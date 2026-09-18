# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
"""
attr_value_manager - Attribute > Set Value 탭 로직.

`_archive/legacy_tools/01_Modules/JUN_PY_numberTool_V01_01.py` (Number Tool) 이식.
원래 의도: 여러 오브젝트를 담고 → **공통으로 가진** 어트리뷰트를 나열하고 → 고른
어트리뷰트를 **한 번에** 바꾼다. 원본은 모든 값을 실수 하나로 setAttr 해서 enum 도
정수로만 넣을 수 있었다. 여기서는 어트리뷰트 종류마다 입력 방식을 나눈다:

  - float : 실수 시작값 + 간격(Step)
  - int   : 정수 시작값 + 정수 간격
  - bool  : Off / On 두 항목짜리 enum 처럼 다룬다
  - enum  : 항목 **이름**에서 고른다. 간격은 "몇 항목씩 건너뛸지" (끝에서 처음으로 돌아감)

간격(Step)은 **오브젝트 리스트 순서대로** 누적된다: i 번째 오브젝트 = start + i*step.
Repeat 가 N(>0) 이면 N 개마다 시작값으로 되돌아간다 (0,1,2,0,1,2 ...).

UI 비의존: 위젯에서 읽은 값만 받는다.
"""

import maya.cmds as cmds

from tools.A00145_RigConnect.app.core import connect_manager as cnt_mgr
from tools.A00145_RigConnect.app.core import blendshape_utils as bsu


KIND_FLOAT = "float"
KIND_INT = "int"
KIND_BOOL = "bool"
KIND_ENUM = "enum"

# attributeQuery(attributeType) -> 종류. 여기 없는 타입(문자열/행렬/compound 등)은 다루지 않는다.
_TYPE_KIND = {
    "double": KIND_FLOAT, "float": KIND_FLOAT,
    "doubleLinear": KIND_FLOAT, "doubleAngle": KIND_FLOAT,
    "floatLinear": KIND_FLOAT, "floatAngle": KIND_FLOAT, "time": KIND_FLOAT,
    "long": KIND_INT, "short": KIND_INT, "byte": KIND_INT, "char": KIND_INT,
    "bool": KIND_BOOL,
    "enum": KIND_ENUM,
}

BOOL_ITEMS = [("Off", 0), ("On", 1)]


def attr_kind(obj, attr):
    """obj.attr 의 종류(KIND_*) 또는 None(다루지 않는 타입 / 없는 어트리뷰트)."""
    try:
        if not cmds.attributeQuery(attr, node=obj, exists=True):
            return None
        at = cmds.attributeQuery(attr, node=obj, attributeType=True)
    except Exception:
        return None
    # 자식이 있는 compound(double3 등)는 값 하나로 못 넣는다.
    try:
        if cmds.attributeQuery(attr, node=obj, numberOfChildren=True):
            return None
    except Exception:
        pass
    return _TYPE_KIND.get(at)


def enum_items(obj, attr):
    """enum 항목 [(이름, 값), ...]. `A:B=5:C` -> A=0, B=5, C=6 (마야 규칙)."""
    try:
        raw = cmds.attributeQuery(attr, node=obj, listEnum=True) or []
    except Exception:
        return []
    items = []
    value = 0
    for token in (raw[0].split(":") if raw else []):
        if not token:
            continue
        if "=" in token:
            name, num = token.rsplit("=", 1)
            try:
                value = int(num)
            except ValueError:
                name = token
        else:
            name = token
        items.append((name, value))
        value += 1
    return items


def attr_info(obj, attr):
    """UI 편집기를 고르는 데 필요한 정보.

    Returns:
        {"kind", "type", "min", "max", "items"} 또는 None.
        min/max 는 **하드 범위**(없으면 None). items 는 enum/bool 만.
    """
    kind = attr_kind(obj, attr)
    if kind is None:
        return None
    info = {"kind": kind,
            "type": cmds.attributeQuery(attr, node=obj, attributeType=True),
            "min": None, "max": None, "items": []}
    if kind == KIND_ENUM:
        info["items"] = enum_items(obj, attr)
    elif kind == KIND_BOOL:
        info["items"] = list(BOOL_ITEMS)
    else:
        try:
            if cmds.attributeQuery(attr, node=obj, minExists=True):
                info["min"] = cmds.attributeQuery(attr, node=obj, minimum=True)[0]
            if cmds.attributeQuery(attr, node=obj, maxExists=True):
                info["max"] = cmds.attributeQuery(attr, node=obj, maximum=True)[0]
        except Exception:
            pass
    return info


def list_common_attrs(objects, channel_box_only=True):
    """모든 오브젝트가 **공통으로** 가진, 값을 넣을 수 있는 어트리뷰트.

    순서는 첫 오브젝트 기준. 종류가 오브젝트마다 다르면(한쪽은 enum, 한쪽은 float)
    첫 오브젝트의 종류로 보여 주고, 적용할 때 오브젝트별로 다시 판정한다.

    Returns:
        (rows, missing) - rows = [{"name", "kind"}], missing = 씬에 없는 오브젝트.
    """
    present = [o for o in objects if cmds.objExists(o)]
    missing = [o for o in objects if o not in present]
    if not present:
        return [], missing

    def _names(obj):
        if channel_box_only:
            names = set(cnt_mgr.channel_box_attrs(obj))
        else:
            names = set(a for a in (cmds.listAttr(obj, scalar=True) or [])
                        if "." not in a)
        # blendShape 타겟은 weight[i] 별칭이다 - 이름으로 고를 수 있게 넣어 준다.
        names.update(bsu.get_blendshape_targets(obj))
        return names

    first = present[0]
    common = _names(first)
    for obj in present[1:]:
        common &= _names(obj)

    # 첫 오브젝트의 씬 순서로 정렬(listAttr 순서). blendShape 타겟은 앞에.
    order = list(bsu.get_blendshape_targets(first)) + \
        [a for a in (cmds.listAttr(first) or []) if "." not in a]
    rows, seen = [], set()
    for name in order:
        if name not in common or name in seen:
            continue
        seen.add(name)
        kind = attr_kind(first, name)
        if kind:
            rows.append({"name": name, "kind": kind})
    return rows, missing


def build_values(count, start, step=0.0, repeat=0):
    """리스트 순서대로 넣을 값 count 개. i 번째 = start + (i % repeat 또는 i) * step."""
    values = []
    for i in range(count):
        k = i % repeat if repeat and repeat > 0 else i
        values.append(start + k * step)
    return values


def build_enum_values(count, items, start_index, step=1, repeat=0):
    """enum/bool 용: 항목 **인덱스**를 step 씩 옮겨 가며 (이름, 값) count 개. 끝에서 처음으로 돈다."""
    if not items:
        return []
    out = []
    for i in range(count):
        k = i % repeat if repeat and repeat > 0 else i
        out.append(items[(start_index + k * step) % len(items)])
    return out


def _clamp(value, info):
    lo, hi = info.get("min"), info.get("max")
    clamped = value
    if lo is not None and clamped < lo:
        clamped = lo
    if hi is not None and clamped > hi:
        clamped = hi
    return clamped, clamped != value


def _is_animated(plug):
    """키(animCurve) 또는 애니메이션 레이어(animBlendNode)로 구동되는지."""
    src = cmds.listConnections(plug, source=True, destination=False,
                               skipConversionNodes=True) or []
    for node in src:
        t = cmds.nodeType(node)
        if t.startswith("animCurve") or t.startswith("animBlendNode"):
            return True
    return False


def plan(objects, attr, kind, values, clamp=True):
    """적용 전 미리보기 겸 실제 적용 계획.

    Args:
        values: kind 가 float/int 면 숫자 리스트, enum/bool 이면 (이름, 값) 리스트.
                enum 은 **이름**으로 각 오브젝트의 항목을 다시 찾는다 (오브젝트마다 값이
                다를 수 있다).

    Returns:
        [{"obj", "plug", "current", "new", "shown", "status", "note"}]
        status: "ok" / "skip". shown = 로그/표에 보일 새 값 문자열.
    """
    rows = []
    for obj, value in zip(objects, values):
        plug = "{0}.{1}".format(obj, attr)
        row = {"obj": obj, "plug": plug, "current": "", "new": None,
               "shown": "", "status": "skip", "note": ""}
        rows.append(row)

        if not cmds.objExists(obj):
            row["note"] = "object not found"
            continue
        info = attr_info(obj, attr)
        if info is None:
            row["note"] = "no settable attribute '{0}'".format(attr)
            continue

        try:
            cur = cmds.getAttr(plug)
        except Exception as e:
            row["note"] = str(e)
            continue

        obj_kind = info["kind"]
        if obj_kind in (KIND_ENUM, KIND_BOOL):
            items = info["items"]
            cur_name = next((n for n, v in items if v == int(cur)), str(cur))
            row["current"] = cur_name
            if kind not in (KIND_ENUM, KIND_BOOL):
                row["note"] = "is {0}, not {1}".format(obj_kind, kind)
                continue
            name = value[0]
            match = next((v for n, v in items if n == name), None)
            if match is None:
                row["note"] = "no enum item '{0}'".format(name)
                continue
            row["new"], row["shown"] = match, name
        else:
            row["current"] = _fmt(cur, obj_kind)
            if kind in (KIND_ENUM, KIND_BOOL):
                row["note"] = "is {0}, not {1}".format(obj_kind, kind)
                continue
            new = int(round(value)) if obj_kind == KIND_INT else float(value)
            if clamp:
                new, was = _clamp(new, info)
                if was:
                    row["note"] = "clamped to range"
            row["new"], row["shown"] = new, _fmt(new, obj_kind)

        if cmds.getAttr(plug, lock=True):
            row["note"] = "locked"
            continue
        # 키/레이어 말고 다른 노드가 구동하면 setAttr 이 실패한다.
        if cmds.listConnections(plug, source=True, destination=False) and \
                not _is_animated(plug):
            row["note"] = "driven by a connection"
            continue
        row["status"] = "ok"
    return rows


def apply(rows):
    """plan() 결과 중 status == "ok" 를 적용한다. 키 걸린 plug 는 키를 찍고 setAttr.

    Returns:
        (set_count, keyed_count, failed[(plug, reason)])
    """
    done, keyed, failed = 0, 0, []
    for row in rows:
        if row["status"] != "ok":
            continue
        plug = row["plug"]
        try:
            # 키 걸린 plug 는 setAttr 만 하면 다음 프레임에 커브 값으로 돌아간다.
            # 키를 먼저 찍고 setAttr 로 즉시 반영한다 (undo 도 한 덩어리).
            if _is_animated(plug):
                cmds.setKeyframe(plug, value=row["new"])
                keyed += 1
            cmds.setAttr(plug, row["new"])
            done += 1
        except Exception as e:
            failed.append((plug, str(e).strip()))
    return done, keyed, failed


def _fmt(value, kind):
    if kind in (KIND_INT, KIND_BOOL):
        return str(int(round(value)))
    return "{0:.4f}".format(value).rstrip("0").rstrip(".") or "0"
