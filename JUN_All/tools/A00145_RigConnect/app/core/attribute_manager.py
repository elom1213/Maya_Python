# -*- coding: utf-8 -*-
"""
attribute_manager - Attribute 탭 로직.

소스 오브젝트의 어트리뷰트 중 선택한 것들을, 같은 정의(타입/범위/기본값/키어블 등)로
타겟 오브젝트들에 새로 만든다. 이름은 그대로 쓰거나 Prefix / Suffix 를 붙일 수 있다.

  src.stretch (double, min 0 / max 1, default 0.5)
      -> tgt.L_stretch_ctrl  (Prefix "L_", Suffix "_ctrl")

지원 타입: 숫자(double/float/long/short/byte/bool/doubleAngle/doubleLinear/time),
enum, string(typed), message, 컴파운드 벡터/컬러(double3/float3/long3/short3 등), multi.

UI 비의존: 위젯에서 읽은 list/str/bool 값만 받는다. (app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds

from tools.A00145_RigConnect.app.core import attr_display
from tools.A00145_RigConnect.app.core import blendshape_utils as bsu


# addAttr 에 dataType(-dt) 으로 넘겨야 하는 타입들. 그 외는 attributeType(-at).
# attributeQuery 가 "typed" 로 알려주는 어트리뷰트의 실제 데이터 타입은 getAttr 로 확인한다.
_DATA_TYPES = (
    "string", "stringArray", "matrix", "doubleArray", "floatArray",
    "Int32Array", "vectorArray", "nurbsCurve", "nurbsSurface", "mesh",
    "lattice", "pointArray", "componentList",
)

# 값 복사를 하지 않는(할 수 없는) 타입.
_NO_VALUE_TYPES = ("message", "compound")


def list_attributes(obj, user_defined_only=True, search=""):
    """obj 의 어트리뷰트 이름 목록을 반환한다.

    blendShape 노드면 타겟 이름(별칭)을 맨 앞에 나열한다. 타겟은 `weight[i]` 멀티의 별칭이라
    `listAttr(userDefined=True)` 로는 `attributeAliasList` 밖에 안 나오기 때문이다.

    Args:
        obj: 대상 오브젝트 이름.
        user_defined_only: True 면 사용자 정의 어트리뷰트만(기본).
                           False 면 translateX 같은 기본 어트리뷰트까지 전부.
                           blendShape 면 True 일 때 타겟 이름만 보여준다.
        search: 부분 문자열 필터(대소문자 무시). 비어 있으면 필터 없음.

    Returns:
        어트리뷰트 롱네임(=blendShape 면 타겟 이름) 리스트.
    """
    if not obj:
        return []
    if not cmds.objExists(obj):
        raise ValueError("Object not found in scene: {0}".format(obj))

    bs_targets = bsu.get_blendshape_targets(obj)

    if bs_targets and user_defined_only:
        # blendShape 의 "사용자 정의" 어트리뷰트란 사실상 타겟들이다.
        attrs = list(bs_targets)
    elif user_defined_only:
        attrs = cmds.listAttr(obj, userDefined=True) or []
    else:
        attrs = bs_targets + (cmds.listAttr(obj) or [])

    # 컴파운드 자식(tintR / translateX ...)은 목록에서 뺀다. 부모를 복사하면 같이 만들어지고,
    # 자식만 따로는 addAttr 로 만들 수도 없다. listAttr 은 자식을 "parent.child" 로 줄 때도,
    # 평평한 이름으로 줄 때도 있어 둘 다 거른다.
    # (blendShape 타겟 별칭은 weight 로 해석돼 listParent 가 비므로 살아남는다)
    attrs = [a for a in attrs
             if "." not in a and not _query(a, obj, listParent=True)]

    if search:
        low = search.lower()
        attrs = [a for a in attrs if low in a.lower()]

    # 순서를 유지한 채 중복 제거(타겟 별칭이 listAttr 결과에도 섞일 수 있다).
    seen = set()
    unique = []
    for attr in attrs:
        if attr not in seen:
            seen.add(attr)
            unique.append(attr)
    return unique


def _query(attr, node, **kwargs):
    """attributeQuery 래퍼. 조회 실패(해당 속성이 없는 타입 등)면 None."""
    try:
        return cmds.attributeQuery(attr, node=node, **kwargs)
    except Exception:
        return None


def get_attr_spec(obj, attr):
    """obj.attr 의 정의를 addAttr 로 재생성할 수 있는 dict 로 읽는다.

    Returns:
        {long_name, short_name, attr_type, data_type, multi, keyable, channel_box,
         hidden, used_as_color, enum_name, default, min, max, soft_min, soft_max,
         locked, value, children:[spec, ...]}
    """
    full = "{0}.{1}".format(obj, attr)
    if not cmds.objExists(full):
        raise ValueError("Attribute not found: {0}".format(full))

    attr_type = _query(attr, obj, attributeType=True)
    is_multi = bool(_query(attr, obj, multi=True))

    # blendShape 타겟은 `weight[i]` 의 별칭이라, attributeQuery 가 별칭을 부모 멀티(`weight`)로
    # 해석한다. 그대로 두면 타겟 하나를 복사해도 `weight` 라는 multi 어트리뷰트가 생긴다.
    # 타겟 이름을 가진 단일 float(범위/기본값/키어블은 weight 의 정의 그대로)로 바로잡는다.
    is_bs_target = attr in bsu.get_blendshape_targets(obj)

    # "typed" 는 실제 데이터 타입을 getAttr 로 확인해야 한다(string 등).
    data_type = None
    if attr_type == "typed":
        try:
            data_type = cmds.getAttr(full, type=True)
        except Exception:
            data_type = "string"

    spec = {
        "long_name": attr if is_bs_target else (
            _query(attr, obj, longName=True) or attr),
        "short_name": attr if is_bs_target else (
            _query(attr, obj, shortName=True) or attr),
        "attr_type": attr_type,
        "data_type": data_type,
        "multi": False if is_bs_target else is_multi,
        "keyable": bool(_query(attr, obj, keyable=True)),
        # channelBox(=nonKeyable displayed) 는 attributeQuery 에 없어 getAttr 로 본다.
        "channel_box": False,
        "hidden": bool(_query(attr, obj, hidden=True)),
        "used_as_color": bool(_query(attr, obj, usedAsColor=True)),
        "enum_name": None,
        "default": None,
        "min": None, "max": None, "soft_min": None, "soft_max": None,
        "locked": False,
        "value": None,
        "children": [],
    }

    try:
        spec["channel_box"] = bool(cmds.getAttr(full, channelBox=True))
        spec["locked"] = bool(cmds.getAttr(full, lock=True))
    except Exception:
        pass

    if attr_type == "enum":
        enums = _query(attr, obj, listEnum=True)
        spec["enum_name"] = enums[0] if enums else None

    # 범위/기본값은 숫자형에만 존재한다. 없으면 조회가 실패하거나 빈 값이다.
    if _query(attr, obj, minExists=True):
        vals = _query(attr, obj, minimum=True)
        if vals:
            spec["min"] = vals[0]
    if _query(attr, obj, maxExists=True):
        vals = _query(attr, obj, maximum=True)
        if vals:
            spec["max"] = vals[0]
    if _query(attr, obj, softMinExists=True):
        vals = _query(attr, obj, softMin=True)
        if vals:
            spec["soft_min"] = vals[0]
    if _query(attr, obj, softMaxExists=True):
        vals = _query(attr, obj, softMax=True)
        if vals:
            spec["soft_max"] = vals[0]

    defaults = _query(attr, obj, listDefault=True)
    if defaults:
        # 컴파운드면 자식 개수만큼 오지만, 부모 addAttr 엔 default 를 주지 않으므로 첫 값만 쓴다.
        spec["default"] = defaults[0] if len(defaults) == 1 else list(defaults)

    # 현재 값 (multi/message/compound 는 건너뛴다)
    if not spec["multi"] and attr_type not in _NO_VALUE_TYPES:
        try:
            spec["value"] = cmds.getAttr(full)
        except Exception:
            spec["value"] = None

    # 컴파운드(double3/float3 등) 자식 스펙.
    children = _query(attr, obj, listChildren=True) or []
    for child in children:
        spec["children"].append(get_attr_spec(obj, child))

    return spec


def build_new_name(name, prefix="", suffix=""):
    """어트리뷰트 이름에 prefix/suffix 를 붙인다."""
    return "{0}{1}{2}".format(prefix or "", name, suffix or "")


def _child_new_name(child_long, parent_long, parent_new, prefix, suffix):
    """컴파운드 자식의 새 이름.

    자식이 부모 이름으로 시작하면(colorR -> color + R) 부모의 새 이름에 접미부를 잇는다.
    그렇지 않으면 자식 이름에도 prefix/suffix 를 붙인다.
    """
    if child_long.startswith(parent_long):
        return parent_new + child_long[len(parent_long):]
    return build_new_name(child_long, prefix, suffix)


def _add_flags(spec, new_name, keep_short_name):
    """spec -> addAttr 키워드 인자."""
    flags = {"longName": new_name}

    # 이름을 바꾸지 않은 경우에만 원본 short name 을 유지한다.
    # (바꿨는데 short name 을 그대로 쓰면 다른 어트리뷰트와 충돌한다)
    if keep_short_name and spec["short_name"] and spec["short_name"] != new_name:
        flags["shortName"] = spec["short_name"]

    if spec["data_type"]:
        flags["dataType"] = spec["data_type"]
    elif spec["attr_type"]:
        flags["attributeType"] = spec["attr_type"]

    if spec["multi"]:
        flags["multi"] = True

    if spec["attr_type"] == "enum" and spec["enum_name"]:
        flags["enumName"] = spec["enum_name"]

    if spec["used_as_color"]:
        flags["usedAsColor"] = True

    # 숫자형 범위/기본값. string/message/compound 엔 넣지 않는다.
    if spec["min"] is not None:
        flags["minValue"] = spec["min"]
    if spec["max"] is not None:
        flags["maxValue"] = spec["max"]
    if spec["soft_min"] is not None:
        flags["softMinValue"] = spec["soft_min"]
    if spec["soft_max"] is not None:
        flags["softMaxValue"] = spec["soft_max"]
    if spec["default"] is not None and not isinstance(spec["default"], list):
        if not spec["data_type"] and spec["attr_type"] not in _NO_VALUE_TYPES:
            flags["defaultValue"] = spec["default"]

    if spec["keyable"]:
        flags["keyable"] = True
    if spec["hidden"]:
        flags["hidden"] = True

    return flags


def _set_value(target, new_name, spec):
    """새로 만든 어트리뷰트에 소스의 현재 값을 넣는다. 실패해도 조용히 넘어간다."""
    if spec["multi"] or spec["value"] is None:
        return
    if spec["attr_type"] in _NO_VALUE_TYPES:
        return

    full = "{0}.{1}".format(target, new_name)
    value = spec["value"]
    try:
        if spec["data_type"] == "string":
            cmds.setAttr(full, value, type="string")
        elif isinstance(value, (list, tuple)):
            # 컴파운드는 getAttr 이 [(x, y, z)] 로 준다.
            flat = value[0] if len(value) == 1 and isinstance(
                value[0], (list, tuple)) else value
            cmds.setAttr(full, *flat, type=spec["attr_type"])
        else:
            cmds.setAttr(full, value)
    except Exception:
        pass


def _create_one(target, spec, new_name, prefix, suffix, copy_value,
                show_in_channel_box=True):
    """target 에 spec 대로 어트리뷰트 1개(+ 컴파운드면 자식들)를 만든다.

    `show_in_channel_box` 가 True(기본)면 원본이 숨어 있던 것이라도 **채널박스에 보이게**
    만든다 — 만든 뒤에 숨어 있으면 쓸 수가 없고, 레퍼런스로 불러온 다음에는 표시 상태를
    고칠 수도 없기 때문이다(마야가 거부한다). keyable 여부는 원본을 그대로 따른다.
    """
    keep_short_name = (new_name == spec["long_name"])
    cmds.addAttr(target, **_add_flags(spec, new_name, keep_short_name))

    for child in spec["children"]:
        child_new = _child_new_name(
            child["long_name"], spec["long_name"], new_name, prefix, suffix)
        child_flags = _add_flags(child, child_new, keep_short_name)
        child_flags["parent"] = new_name
        cmds.addAttr(target, **child_flags)

    # channelBox(비키어블 표시)는 addAttr 로 못 주고 setAttr 로 켠다.
    if spec["channel_box"] and not spec["keyable"]:
        try:
            cmds.setAttr("{0}.{1}".format(target, new_name), channelBox=True)
        except Exception:
            pass

    # ★ 원본이 숨어 있었으면 사본은 채널박스로 올린다 (v01.52).
    #   keyable 은 원본 그대로 두고, 아무 데도 안 보이는 상태만 없앤다.
    if show_in_channel_box and not attr_display.is_visible(target, new_name):
        attr_display.show_in_channel_box(target, new_name,
                                         keyable=bool(spec["keyable"]))

    if copy_value:
        _set_value(target, new_name, spec)
        for child in spec["children"]:
            child_new = _child_new_name(
                child["long_name"], spec["long_name"], new_name, prefix, suffix)
            _set_value(target, child_new, child)


def copy_attributes(source, attrs, targets, prefix="", suffix="",
                    copy_value=True, skip_existing=True,
                    show_in_channel_box=True):
    """source 의 attrs 를 targets 에 같은 정의로 새로 만든다.

    Args:
        source: 소스 오브젝트 이름.
        attrs: 복사할 어트리뷰트 롱네임 리스트.
        targets: 어트리뷰트를 새로 만들 오브젝트 리스트.
        prefix: 새 이름 앞에 붙일 문자열.
        suffix: 새 이름 뒤에 붙일 문자열.
        copy_value: True 면 소스의 현재 값도 복사한다.
        skip_existing: True 면 같은 이름이 이미 있는 타겟은 건너뛴다(기본).
                       False 면 에러로 보고한다.
        show_in_channel_box: True(기본) 면 원본이 숨어 있던 어트리뷰트도 사본은
                       채널박스에 보이게 만든다. False 면 원본의 표시 상태를 그대로 따른다.

    Returns:
        (created, skipped) — created 는 "target.newAttr" 리스트,
        skipped 는 (target, new_name, reason) 튜플 리스트.
    """
    if not source:
        raise ValueError("No source object. Add an object to the Source list.")
    if not cmds.objExists(source):
        raise ValueError("Source not found in scene: {0}".format(source))
    if not attrs:
        raise ValueError("No attributes selected. Select attributes to copy.")
    if not targets:
        raise ValueError("No target objects. Add objects to the Targets list.")

    # 소스 스펙을 먼저 다 읽어둔다(타겟마다 다시 읽지 않도록).
    specs = [get_attr_spec(source, a) for a in attrs]

    created = []
    skipped = []

    for target in targets:
        if not cmds.objExists(target):
            skipped.append((target, "", "target not found in scene"))
            continue

        for spec in specs:
            new_name = build_new_name(spec["long_name"], prefix, suffix)
            full = "{0}.{1}".format(target, new_name)

            if cmds.objExists(full):
                reason = "attribute already exists"
                if skip_existing:
                    skipped.append((target, new_name, reason))
                    continue
                raise ValueError("{0} : {1}".format(full, reason))

            try:
                _create_one(target, spec, new_name, prefix, suffix, copy_value,
                            show_in_channel_box=show_in_channel_box)
                created.append(full)
            except Exception as e:
                skipped.append((target, new_name, str(e)))

    return created, skipped


def list_attributes_multi(objects, user_defined_only=True):
    """여러 오브젝트의 어트리뷰트를 **합쳐** 한 목록으로 돌려준다.

    ★ 정렬하지 않는다 — **씬에 있는 순서 그대로** 둔다. Attribute > Edit 의 Up / Down 이
    이 목록의 순서를 그대로 바꾸는 것이라, 이름순으로 정렬해 버리면 화면과 실제가 어긋난다.
    첫 오브젝트의 순서를 기준으로 삼고, 뒤 오브젝트에만 있는 것은 뒤에 이어 붙인다.

    Args:
        objects: 오브젝트 이름 리스트.
        user_defined_only: True 면 사용자 정의만(기본). False 면 빌트인까지.

    Returns:
        (rows, missing)
        rows : [{"name", "owners":[obj...], "locked":[obj...], "movable": bool}, ...]
               `movable` 은 **사용자 정의라 순서를 바꿀 수 있는가**다(빌트인은 False).
        missing : 씬에 없는 오브젝트 이름.
    """
    rows = {}
    order = []
    missing = []

    for obj in objects or []:
        if not cmds.objExists(obj):
            missing.append(obj)
            continue

        user_attrs = set(cmds.listAttr(obj, userDefined=True) or [])

        for name in list_attributes(obj, user_defined_only):
            row = rows.get(name)
            if row is None:
                row = {"name": name, "owners": [], "locked": [],
                       "movable": name in user_attrs}
                rows[name] = row
                order.append(name)
            elif name in user_attrs:
                # 한 오브젝트에서라도 사용자 정의면 그쪽에서는 옮길 수 있다.
                row["movable"] = True

            row["owners"].append(obj)

            try:
                if cmds.getAttr("{0}.{1}".format(obj, name), lock=True):
                    row["locked"].append(obj)
            except Exception:
                pass

    return [rows[name] for name in order], missing
