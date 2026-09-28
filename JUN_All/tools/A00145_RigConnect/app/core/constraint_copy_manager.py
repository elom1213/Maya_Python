# -*- coding: utf-8 -*-
"""
constraint_copy_manager - Constrain > Transfer 탭 'Copy' 모드 로직 (v01.57).

왼쪽 목록의 constraint 의 **성질을 읽어**, 오른쪽 목록의 각 오브젝트에 **같은 constraint 를 새로
건다.** Transfer(Default 모드)와 달리 원본은 그대로 둔다 - 복사 · 붙여넣기다.

  before:  [targets] --(parentConstraint)--> objA
  after :  [targets] --(parentConstraint)--> objA        (원본 그대로)
           [targets] --(parentConstraint)--> objB, objC  (같은 성질로 새로)

복사하는 성질
- 종류 (parent / point / orient / scale / aim / poleVector / geometry / normal / tangent /
  pointOnPoly - 종류 무관)
- 타깃(드라이버) 목록과 순서
- **구동 축** - 원본이 x 만 구동하면(skip y, z) 복사본도 x 만. 원본 constraint 출력이 driven 의
  어느 채널에 꽂혀 있는지를 읽어 skip 플래그로 만든다.
- aim 계열(aim / normal / tangent)의 aimVector · upVector · worldUpType · worldUpVector · worldUpObject
- 동적 어트리뷰트 값 - 타깃 **weight**(`<target>W0`), pointOnPoly 의 U / V 등
- interpType · enableRestPosition · restTranslate · restRotate
- 오프셋 (Maintain Offset 을 끈 경우만) - point / orient / aim / scale 의 `offset`,
  parent 의 타깃별 `targetOffsetTranslate` · `targetOffsetRotate`

Maintain Offset
- 켬(기본) : 오프셋은 **각 오브젝트의 지금 자리**로 새로 잡는다 → 복사해도 오브젝트가 튀지 않는다.
- 끔     : 원본의 오프셋 **값을 그대로** 넣는다 → 원본과 똑같은 관계로 붙는다(오브젝트가 움직일 수 있다).

매핑
- MAP_EACH : 왼쪽 constraint **전부**를 오른쪽 오브젝트 **하나하나**에 (point + orient 조합을 통째로)
- MAP_PAIR : 줄끼리 1:1 - 왼쪽 i 번째 줄의 constraint 들 -> 오른쪽 i 번째 오브젝트

건너뛰는 것 (경고)
- 오른쪽 오브젝트가 원본의 driven 자신 / 원본의 타깃 중 하나(순환)
- 오른쪽 오브젝트에 **같은 종류의 constraint 가 이미 있다** - 마야는 새로 만들지 않고 그 constraint 에
  타깃을 더해 버린다(원본 성질과 다른 결과).

UI 비의존: 위젯에서 읽은 이름 리스트만 받는다. UUID 로 잡아 같은 이름이 여럿이어도 안전하다.
"""

import maya.cmds as cmds

from .constraint_transfer_manager import (
    _to_uuid,
    _path,
    _is_constraint,
    _vec3,
    _read_aim,
)


MAP_EACH = "each"
MAP_PAIR = "pair"

#: 종류별 skip 플래그 -> 그 플래그가 다루는 채널 (t / r / s)
_SKIP_FLAGS = {
    "parentConstraint": (("skipTranslate", "t"), ("skipRotate", "r")),
    "pointConstraint": (("skip", "t"),),
    "orientConstraint": (("skip", "r"),),
    "scaleConstraint": (("skip", "s"),),
    "aimConstraint": (("skip", "r"),),
}

_CHANNEL_ATTRS = {
    "t": ("translateX", "translateY", "translateZ"),
    "r": ("rotateX", "rotateY", "rotateZ"),
    "s": ("scaleX", "scaleY", "scaleZ"),
}

_AIM_TYPES = ("aimConstraint", "normalConstraint", "tangentConstraint")

# 값을 그대로 옮길 정적 어트리뷰트 (있고 연결 안 된 것만)
_STATIC_ATTRS = ("interpType", "enableRestPosition", "restTranslate", "restRotate")

# 오프셋 (Maintain Offset 을 끈 경우만 옮긴다)
_OFFSET_TYPES = ("pointConstraint", "orientConstraint", "aimConstraint", "scaleConstraint")


# ------------------------------------------------------------------ 읽기

def _driven_channels(cn, driven):
    """constraint 출력이 꽂힌 driven 의 채널 이름 집합 ('translateX' ...)."""
    pairs = cmds.listConnections(
        cn, source=False, destination=True, plugs=True, connections=True) or []
    driven_short = driven.split("|")[-1]
    channels = set()
    for i in range(1, len(pairs), 2):
        node, _dot, attr = pairs[i].partition(".")
        if node.split("|")[-1] != driven_short:
            continue
        channels.add(attr)
        # translate 통째 연결(드묾) 대비
        if attr in ("translate", "rotate", "scale"):
            for axis in "XYZ":
                channels.add(attr + axis)
    return channels


def _read_skips(ctype, cn, driven):
    """원본이 구동하지 않는 축 -> {flag: ['x', ...]} . 다 구동하면 빈 dict."""
    flags = _SKIP_FLAGS.get(ctype)
    if not flags or not driven:
        return {}
    connected = _driven_channels(cn, driven)
    skips = {}
    for flag, channel in flags:
        attrs = _CHANNEL_ATTRS[channel]
        driven_axes = [a[-1].lower() for a in attrs if a in connected]
        if not driven_axes:
            # 이 채널을 아예 안 구동 - parent 의 skipRotate 전부 등. 전부 skip 은 마야가
            # 받는 경우(parent)만 넣는다.
            if ctype == "parentConstraint":
                skips[flag] = ["x", "y", "z"]
            continue
        missing = [axis for axis in "xyz" if axis not in driven_axes]
        if missing:
            skips[flag] = missing
    return skips


def _target_indices(cn):
    return sorted(cmds.getAttr(cn + ".target", multiIndices=True) or [])


def _read_offsets(ctype, cn):
    """오프셋 값. point/orient/aim/scale -> {'offset': [x,y,z]},
    parent -> {'targets': [(t[3], r[3]), ...]} (타깃 순서)."""
    if ctype in _OFFSET_TYPES and cmds.attributeQuery("offset", node=cn, exists=True):
        return {"offset": _vec3(cmds.getAttr(cn + ".offset"))}
    if ctype == "parentConstraint":
        values = []
        for index in _target_indices(cn):
            base = "{0}.target[{1}]".format(cn, index)
            values.append((_vec3(cmds.getAttr(base + ".targetOffsetTranslate")),
                           _vec3(cmds.getAttr(base + ".targetOffsetRotate"))))
        return {"targets": values}
    return {}


def _read_dynamic(cn):
    """동적(사용자 정의) 스칼라 어트리뷰트 값 - weight(W0..), pointOnPoly U/V 등."""
    values = {}
    for attr in cmds.listAttr(cn, userDefined=True) or []:
        plug = "{0}.{1}".format(cn, attr)
        try:
            value = cmds.getAttr(plug)
        except Exception:
            continue
        if isinstance(value, (int, float, bool)):
            values[attr] = value
    return values


def _read_static(cn):
    values = {}
    for attr in _STATIC_ATTRS:
        if not cmds.attributeQuery(attr, node=cn, exists=True):
            continue
        try:
            values[attr] = cmds.getAttr("{0}.{1}".format(cn, attr))
        except Exception:
            pass
    return values


def read_constraint_spec(con_uuid):
    """constraint 의 성질을 dict 로. 읽을 수 없으면 None."""
    cn = _path(con_uuid)
    if cn is None:
        return None
    ctype = cmds.nodeType(cn)
    cmd = getattr(cmds, ctype, None)
    if cmd is None:
        return None

    try:
        targets = cmd(cn, q=True, targetList=True) or []
    except Exception:
        targets = []
    target_uuids = [u for u in (_to_uuid(t) for t in targets) if u]

    parents = cmds.listRelatives(cn, parent=True, fullPath=True) or []
    driven = parents[0] if parents else None

    return {
        "name": cn.split("|")[-1],
        "type": ctype,
        "target_uuids": target_uuids,
        "target_names": [t.split("|")[-1] for t in targets],
        "driven_uuid": _to_uuid(driven) if driven else None,
        "aim": _read_aim(cmd, cn) if ctype in _AIM_TYPES else {},
        "skips": _read_skips(ctype, cn, driven),
        "offsets": _read_offsets(ctype, cn),
        "dynamic": _read_dynamic(cn),
        "static": _read_static(cn),
    }


# ------------------------------------------------------------------ 쓰기

def _set_plug(plug, value):
    """연결 안 된 plug 에 값을 넣는다. double3 는 [[x,y,z]] 모양도 받는다."""
    if cmds.listConnections(plug, source=True, destination=False):
        return False
    if isinstance(value, (list, tuple)):
        flat = _vec3(value)
        cmds.setAttr(plug, *flat, type="double3")
    else:
        cmds.setAttr(plug, value)
    return True


def _has_same_type(obj, ctype):
    return bool(cmds.listRelatives(obj, children=True, type=ctype, fullPath=True))


def apply_spec(spec, obj, maintain_offset=True):
    """spec 의 constraint 를 obj 에 새로 건다. 새 constraint 이름 반환."""
    ctype = spec["type"]
    cmd = getattr(cmds, ctype)

    target_paths = [p for p in (_path(u) for u in spec["target_uuids"]) if p]
    if not target_paths:
        raise RuntimeError("no resolvable targets")

    kw = {}
    aim = spec["aim"]
    for flag in ("aimVector", "upVector", "worldUpVector"):
        if flag in aim:
            kw[flag] = aim[flag]
    if "worldUpType" in aim:
        kw["worldUpType"] = aim["worldUpType"]
    wuo = _path(aim.get("worldUpObject_uuid"))
    if wuo:
        kw["worldUpObject"] = wuo
    for flag, axes in spec["skips"].items():
        kw[flag] = axes

    args = target_paths + [obj]
    # maintainOffset 을 받지 않는 종류(geometry 등)는 플래그 없이 다시 시도한다.
    try:
        res = cmd(*args, maintainOffset=maintain_offset, **kw)
    except TypeError:
        res = cmd(*args, **kw)
    new_cn = res[0] if isinstance(res, (list, tuple)) else res

    # 동적(weight, U/V) · 정적 값
    for attr, value in spec["dynamic"].items():
        if cmds.attributeQuery(attr, node=new_cn, exists=True):
            try:
                _set_plug("{0}.{1}".format(new_cn, attr), value)
            except Exception:
                pass
    for attr, value in spec["static"].items():
        if cmds.attributeQuery(attr, node=new_cn, exists=True):
            try:
                _set_plug("{0}.{1}".format(new_cn, attr), value)
            except Exception:
                pass

    # 오프셋 값 그대로 (Maintain Offset 끔)
    if not maintain_offset:
        offsets = spec["offsets"]
        if "offset" in offsets:
            _set_plug(new_cn + ".offset", offsets["offset"])
        if "targets" in offsets:
            for index, (t, r) in zip(_target_indices(new_cn), offsets["targets"]):
                base = "{0}.target[{1}]".format(new_cn, index)
                _set_plug(base + ".targetOffsetTranslate", t)
                _set_plug(base + ".targetOffsetRotate", r)

    return new_cn


# ------------------------------------------------------------------ 왼쪽 목록

def _constraints_of_row(name, warnings):
    """왼쪽 한 줄 -> constraint UUID 목록. 트랜스폼이면 걸린 constraint 전부(종류 무관)."""
    matches = cmds.ls(name, long=True) or []
    if not matches:
        warnings.append("Skipped (not found): {0}".format(name))
        return []
    if len(matches) > 1:
        warnings.append("Ambiguous name '{0}' ({1} matches) - using first.".format(
            name, len(matches)))
    node = matches[0]
    if _is_constraint(node):
        return [_to_uuid(node)]
    cons = cmds.listRelatives(node, children=True, type="constraint", fullPath=True) or []
    if not cons:
        warnings.append("Skipped (not a constraint / no constraint): {0}".format(name))
        return []
    return [_to_uuid(c) for c in cons]


def _object_uuid(name, warnings):
    matches = cmds.ls(name, uuid=True) or []
    if not matches:
        warnings.append("Skipped object (not found): {0}".format(name))
        return None
    if len(matches) > 1:
        warnings.append("Ambiguous object '{0}' ({1} matches) - using first.".format(
            name, len(matches)))
    return matches[0]


# ------------------------------------------------------------------ 공개 API

def copy_constraints(constraint_names, object_names, maintain_offset=True, mapping=MAP_EACH):
    """왼쪽 constraint 의 성질을 오른쪽 오브젝트에 복사한다 (원본 유지).

    반환: (생성된 constraint 이름 리스트, 경고 리스트, 로그 줄 리스트)
    """
    if not constraint_names:
        raise ValueError("No constraints. Add constraints to the left list.")
    if not object_names:
        raise ValueError("No objects. Add objects to the right list.")

    warnings = []
    rows = [(name, _constraints_of_row(name, warnings)) for name in constraint_names]
    objects = [(name, _object_uuid(name, warnings)) for name in object_names]

    # (constraint uuid, object uuid) 목록
    jobs = []
    if mapping == MAP_PAIR:
        if len(rows) != len(objects):
            warnings.append(
                "Row count differs (constraints {0} vs objects {1}) - copying "
                "{2} row(s).".format(len(rows), len(objects), min(len(rows), len(objects))))
        for (_row, con_uuids), (_obj, obj_uuid) in zip(rows, objects):
            jobs.extend((cu, obj_uuid) for cu in con_uuids)
    else:
        all_cons = [cu for _row, con_uuids in rows for cu in con_uuids]
        for _obj, obj_uuid in objects:
            jobs.extend((cu, obj_uuid) for cu in all_cons)

    specs = {}
    created_uuids = []
    lines = []
    for con_uuid, obj_uuid in jobs:
        if not con_uuid or not obj_uuid:
            continue
        if con_uuid not in specs:
            specs[con_uuid] = read_constraint_spec(con_uuid)
        spec = specs[con_uuid]
        if spec is None:
            warnings.append("Skipped (unreadable constraint): {0}".format(con_uuid))
            continue

        obj = _path(obj_uuid)
        if obj is None:
            continue
        short = obj.split("|")[-1]
        if obj_uuid == spec["driven_uuid"]:
            warnings.append("{0}: already driven by {1} - skipped.".format(short, spec["name"]))
            continue
        if obj_uuid in spec["target_uuids"]:
            warnings.append("{0}: it is a target of {1} (would drive itself) - skipped.".format(
                short, spec["name"]))
            continue
        if _has_same_type(obj, spec["type"]):
            warnings.append(
                "{0}: already has a {1} - skipped (Maya would add the targets to it "
                "instead of making a new one).".format(short, spec["type"]))
            continue

        try:
            new_cn = apply_spec(spec, obj, maintain_offset)
        except Exception as e:
            warnings.append("{0}: {1} failed - {2}".format(short, spec["type"], e))
            continue
        created_uuids.append(_to_uuid(new_cn))
        skip_text = ", ".join("{0}={1}".format(k, "".join(v)) for k, v in spec["skips"].items())
        lines.append("{0} -> {1} : {2} [{3}]{4}".format(
            spec["name"], short, new_cn.split("|")[-1], ", ".join(spec["target_names"]),
            " ({0})".format(skip_text) if skip_text else ""))

    created = [p for p in (_path(u) for u in created_uuids) if p]
    return created, warnings, lines
