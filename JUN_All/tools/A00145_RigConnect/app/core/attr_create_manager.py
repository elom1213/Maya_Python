# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00145_RigConnect - Attribute > Create 탭 로직 (프로파일 스펙 -> addAttr)
#
# Copy 탭은 **씬에 있는 원본 어트리뷰트를 그대로 복제**하지만, Create 탭은 원본 없이
# **프로파일에 적어 둔 정의**로 새로 만든다. 그래서 소스 오브젝트가 필요 없다.
#
# 이미 같은 이름이 있으면 만들지 않는다(덮어쓰지 않는다). 타입이나 범위가 달라도
# 손대지 않고 건너뛴다 - 기존 어트리뷰트를 바꾸면 거기 걸린 연결·키가 깨지기 때문이다.

import maya.cmds as cmds

from tools.A00145_RigConnect.app.core import attr_profile_prefs as prefs


def _add_flags(spec):
    """정규화된 스펙 -> addAttr 키워드 인자.

    `defaultValue` 는 이미 `normalize_spec` 이 범위 안으로 잘라 두었다. addAttr 은 범위
    밖 기본값을 에러가 아니라 **경고 후 무시**하므로(실측), 자르지 않으면 사용자가 적은
    값이 조용히 사라진다.
    """
    if spec["type"] == "string":
        # string 은 `dataType` 이고 `defaultValue` 를 받지 못한다(실측:
        # `Expected float, got str`). 값과 채널박스 표시는 만든 뒤 `_finish_string` 이 넣는다.
        # `keyable` 도 켜 봐야 채널박스에 안 나오므로 여기서 켜지 않는다.
        return {"longName": spec["name"], "dataType": "string"}

    flags = {
        "longName": spec["name"],
        "attributeType": prefs.TYPE_TO_MAYA[spec["type"]],
        "defaultValue": spec["default"],
        "keyable": bool(spec["keyable"]),
    }
    if spec["type"] == "enum":
        # 항목 이름은 `a:b:c` 한 문자열로 준다. defaultValue 는 **항목 번호**이고,
        # 범위를 벗어나면 마야가 조용히 0 으로 만든다(실측) - normalize_spec 이 이미 잘랐다.
        flags["enumName"] = prefs.enum_name(spec.get("enum") or [])
    if spec["type"] in prefs.RANGED_TYPES:
        if spec["min"] is not None:
            flags["minValue"] = spec["min"]
        if spec["max"] is not None:
            flags["maxValue"] = spec["max"]
    return flags


def _finish_string(plug, spec):
    """string 어트리뷰트를 만든 뒤 값과 채널박스 표시를 넣는다 (v01.48).

    - 기본값은 `setAttr ... type="string"` 으로 넣는다(addAttr 이 못 받는다).
      빈 문자열이면 넣지 않는다 - 마야가 주는 값이 `None` 인 상태 그대로 둔다.
    - `Keyable` 체크는 string 에선 **"채널박스에 보이게"** 로 읽는다. string 은 키를 못 걸고,
      `addAttr -keyable` 을 켜도 채널박스에 나오지 않는다(실측) - `setAttr -channelBox` 가 필요하다.
    """
    if spec["default"]:
        cmds.setAttr(plug, spec["default"], type="string")
    if spec["keyable"]:
        cmds.setAttr(plug, channelBox=True)


def create_attributes(objects, specs):
    """objects 전부에 specs 대로 어트리뷰트를 만든다.

    Args:
        objects: 오브젝트 이름 리스트.
        specs: `attr_profile_prefs.normalize_spec` 을 통과한 dict 리스트.

    Returns:
        (created, skipped) — created 는 "obj.attr" 리스트,
        skipped 는 (obj, attr_name, reason) 튜플 리스트.

    Raises:
        ValueError: 오브젝트나 스펙이 비었을 때.
    """
    if not objects:
        raise ValueError("No objects. Add objects to the list on the left.")
    if not specs:
        raise ValueError(
            "No attributes checked. Check the attributes to create on the right.")

    # 스펙은 여기서 한 번 더 정규화한다 - UI 를 거치지 않고 불려도 안전하도록.
    specs = [prefs.normalize_spec(s) for s in specs]

    created, skipped = [], []

    for obj in objects:
        if not cmds.objExists(obj):
            skipped.append((obj, "", "object not found in scene"))
            continue

        for spec in specs:
            full = "{0}.{1}".format(obj, spec["name"])
            if cmds.objExists(full):
                skipped.append((obj, spec["name"], "attribute already exists"))
                continue
            try:
                cmds.addAttr(obj, **_add_flags(spec))
                if spec["type"] == "string":
                    _finish_string(full, spec)
                created.append(full)
            except Exception as e:
                skipped.append((obj, spec["name"], str(e)))

    return created, skipped
