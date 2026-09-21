# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
# A00145_RigConnect - 어트리뷰트를 채널박스에 보이게 한다 (Attribute > Edit / Create 공용)
#
# 마야에서 유저 어트리뷰트가 채널박스에 나오는 길은 **둘뿐**이다.
#
#   keyable  = on            → 키를 걸 수 있는 채널로 보인다
#   keyable  = off + cb = on → "non-keyable displayed" 로 보인다(키는 못 건다)
#
# 둘 다 아니면 **아무 데도 안 보인다.** `addAttr` 은 `keyable` 을 주지 않으면 그 상태로
# 만들므로, 만들자마자 숨어 있는 어트리뷰트가 된다. 이 모듈이 만든 직후 그 상태를 정리한다.
#
# ── ★ 레퍼런스로 들어온 어트리뷰트는 고칠 수 없다 (Maya 2024 실측) ──────────────
#
#     setAttr: The attribute 'R:ctl.plain' is from a referenced file,
#              thus the channelBox state cannot be changed.
#
# `keyable` 도 같은 문구로 거부된다. **레퍼런스 쪽에서는 손쓸 방법이 없다** — 그래서
# 어트리뷰트를 만드는 **그 순간에** 보이게 해 두는 것이 유일한 해법이다. 다행히 한 번
# 제대로 만들어 두면 그 상태는 파일에 저장되고(`setAttr -cb on` / `-k on`),
# **.ma · .mb 어느 쪽으로 저장해도 레퍼런스로 불러왔을 때 그대로 보인다**(실측).
# 레퍼런스된 노드에 **새로 더한** 어트리뷰트는 레퍼런스 에디트로 남아, 씬을 다시 열어도
# 채널박스 표시가 유지된다(실측).
#
# ── 그 밖에 실측으로 확인한 것 ────────────────────────────────────────────
# - `addAttr -h true` 로 숨겨 만든 것도 `setAttr -k/-cb` 로 **되살아난다**
#   (`attributeQuery -hidden` 은 계속 True 라고 답한다 - 표시 여부와 별개다).
# - `keyable = on` 이면 `getAttr -cb` 는 False 다. 둘은 배타적인 상태다.
# - **컴파운드는 부모만 켜도 자식이 안 나온다** → 자식까지 같이 켠다.
# - 잠긴(locked) 어트리뷰트도 표시 상태는 바뀐다. 잠금은 그대로 둔다.
# - string 은 `keyable` 을 켜도 채널박스에 나오지 않는다 → **항상 `channelBox`** 로 켠다.
# - message 는 채널박스에 값이 없다 → 건드리지 않는다.

import maya.cmds as cmds


#: 채널박스에 값이 없는 타입 — 표시를 켜 봐야 의미가 없다.
_NO_CHANNEL_TYPES = ("message",)

#: keyable 로는 채널박스에 나오지 않는 데이터 타입 — channelBox 로 켠다.
_CB_ONLY_DATA_TYPES = ("string",)


def _plug(obj, attr):
    return "{0}.{1}".format(obj, attr)


def _attr_type(obj, attr):
    """(attributeType, dataType). 못 읽으면 (None, None)."""
    try:
        attr_type = cmds.attributeQuery(attr, node=obj, attributeType=True)
    except Exception:
        return None, None

    data_type = None
    if attr_type == "typed":
        try:
            data_type = cmds.getAttr(_plug(obj, attr), type=True)
        except Exception:
            data_type = None

    return attr_type, data_type


def _children(obj, attr):
    """컴파운드 자식 이름들(없으면 빈 리스트)."""
    try:
        return cmds.attributeQuery(attr, node=obj, listChildren=True) or []
    except Exception:
        return []


def is_visible(obj, attr):
    """지금 채널박스에 보이는가 (keyable 이거나 non-keyable displayed)."""
    plug = _plug(obj, attr)

    if not cmds.objExists(plug):
        return False

    try:
        if cmds.getAttr(plug, keyable=True):
            return True
        return bool(cmds.getAttr(plug, channelBox=True))
    except Exception:
        return False


def show_in_channel_box(obj, attr, keyable=None):
    """`obj.attr` 을 채널박스에 보이게 한다. 컴파운드면 자식까지.

    Args:
        obj: 오브젝트 이름.
        attr: 어트리뷰트 롱네임.
        keyable: True 면 keyable 채널로, False 면 non-keyable displayed 로 켠다.
            None 이면 **지금 상태를 존중한다** — keyable 이면 그대로 두고,
            숨어 있으면 non-keyable displayed 로 올린다.

    Returns:
        (ok, reason) — ok 가 False 면 reason 에 이유가 담긴다.
    """
    plug = _plug(obj, attr)

    if not cmds.objExists(plug):
        return False, "attribute not found"

    attr_type, data_type = _attr_type(obj, attr)

    if attr_type in _NO_CHANNEL_TYPES:
        return False, "{0} attributes are not shown in the channel box".format(attr_type)

    # string 은 keyable 로 켜도 채널박스에 나오지 않는다 → channelBox 로 고정.
    if data_type in _CB_ONLY_DATA_TYPES:
        keyable = False

    if keyable is None:
        keyable = bool(cmds.getAttr(plug, keyable=True))

    targets = [attr] + _children(obj, attr)

    try:
        for name in targets:
            child_plug = _plug(obj, name)
            if keyable:
                cmds.setAttr(child_plug, keyable=True)
            else:
                # 순서가 중요하다 — keyable 을 끄면 마야가 표시도 같이 끄므로
                # **끈 다음에** channelBox 를 켠다.
                cmds.setAttr(child_plug, keyable=False)
                cmds.setAttr(child_plug, channelBox=True)
    except Exception as e:
        message = str(e)
        if "referenced file" in message:
            # ★ 레퍼런스에서 온 어트리뷰트는 표시 상태를 바꿀 수 없다.
            return False, ("from a referenced file - fix it in the rig scene and save, "
                           "the channel box state cannot be changed here")
        return False, message

    return True, ""


def show_attributes(objects, attrs, keyable=None):
    """여러 오브젝트의 여러 어트리뷰트를 한 번에 채널박스로 올린다.

    Returns:
        (shown, skipped) — shown 은 "obj.attr" 리스트,
        skipped 는 (obj, attr, reason) 튜플 리스트.
    """
    shown, skipped = [], []

    for obj in objects or []:
        if not cmds.objExists(obj):
            skipped.append((obj, "", "object not found in scene"))
            continue

        for attr in attrs or []:
            if not cmds.objExists(_plug(obj, attr)):
                skipped.append((obj, attr, "attribute not found"))
                continue

            ok, reason = show_in_channel_box(obj, attr, keyable=keyable)
            if ok:
                shown.append(_plug(obj, attr))
            else:
                skipped.append((obj, attr, reason))

    return shown, skipped
