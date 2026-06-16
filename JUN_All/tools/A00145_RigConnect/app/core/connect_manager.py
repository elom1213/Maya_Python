# -*- coding: utf-8 -*-
"""
connect_manager - Connect 탭 로직.

MEL ConnectionTool V04.02 의 attribute 연결 proc 포팅:
  - JUN_cmd_upd_tsl_attr      -> list_attrs (compound/multi 펼치기)
  - JUN_cmd_upd_tsl_search    -> find_matching / list_attrs(search)
  - JUN_cmd_connect_attr      -> connect_attrs (3가지 브로드캐스트 패턴)
  - JUN_cmd_connect_52Facial  -> connect_52_facial

UI 비의존: 위젯에서 읽은 list/str 값만 받는다.
"""

import maya.cmds as cmds
import maya.mel as mel


# MEL JUN_cmd_connect_52Facial 의 하드코딩 52 ARKit 페이셜 어트리뷰트(순서/철자 보존).
# source / target 동일 이름으로 연결한다.
FACIAL_52 = [
    "browInnerUp", "browDownLeft", "browDownRight", "browOuterUpLeft",
    "browOuterUpRight", "eyeLookUpLeft", "eyeLookUpRight", "eyeLookDownLeft",
    "eyeLookDownRight", "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft",
    "eyeLookOutRight", "eyeBlinkLeft", "eyeBlinkRight", "eyeSquintLeft",
    "eyeSquintRight", "eyeWideLeft", "eyeWideRight", "cheekPuff",
    "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft", "noseSneerRight",
    "jawOpen", "jawForward", "jawLeft", "jawRight", "mouthFunnel",
    "mouthPucker", "mouthLeft", "mouthRight", "mouthRollUpper",
    "mouthRollLower", "mouthShrugUpper", "mouthShrugLower", "mouthClose",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft",
    "mouthUpperUpRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthPressLeft", "mouthPressRight", "mouthStretchLeft",
    "mouthStretchRight", "tongueOut",
]


def list_attrs(obj, search=""):
    """obj 의 어트리뷰트 목록을 반환 (MEL JUN_cmd_upd_tsl_attr 포팅).

    - search 가 있으면 listAttr(obj.search) 로 필터한 목록을 기준으로 한다.
    - 이름에 "." 가 들어간(중첩) 항목은 제외한다.
    - multi/compound 어트리뷰트는 getNextFreeMultiIndex 로 판정해
      listAttr -multi 로 자식 어트리뷰트까지 펼친다.

    Args:
        obj: 대상 오브젝트 이름.
        search: 검색 토큰(optional). listAttr 의 부분 이름으로 사용.

    Returns:
        어트리뷰트 이름 문자열 리스트.
    """
    if not obj:
        return []

    if search:
        raw = cmds.listAttr(obj + "." + search) or []
    else:
        raw = cmds.listAttr(obj) or []

    result = []
    for attr in raw:
        # 중첩 어트리뷰트(이름에 ".") 는 건너뛴다.
        if "." in attr:
            continue

        full = "{0}.{1}".format(obj, attr)

        # getNextFreeMultiIndex 는 multi 어트리뷰트에서만 성공한다.
        # 성공하면 multi 로 보고 자식까지 펼치고, 실패(예외)하면 일반 어트리뷰트로 추가.
        try:
            idx = mel.eval('getNextFreeMultiIndex("{0}", 0)'.format(full))
            is_multi = True
        except Exception:
            is_multi = False

        if not is_multi:
            result.append(attr)
        else:
            children = cmds.listAttr(
                "{0}.{1}[{2}]".format(obj, attr, idx), multi=True) or []
            result.extend(children)

    return result


def find_matching(attrs, search):
    """attrs 중 search 토큰을 부분 문자열로 포함하는 항목 (MEL JUN_is_exist 대응)."""
    if not search:
        return []
    return [a for a in attrs if search in a]


def connect_attrs(src_objs, dst_objs, src_attrs, dst_attrs):
    """source -> destination 어트리뷰트 연결 (MEL JUN_cmd_connect_attr 포팅).

    src_attrs / dst_attrs 는 리스트에서 "선택된" 어트리뷰트들이다.
    MEL 의 3가지 패턴을 그대로 따른다:
      1) src obj 1개 & len(srcAttr)==len(dstAttr): 한 src 를 각 dst obj 의 attr 인덱스별로.
      2) srcAttr 1개 & dstAttr 1개: obj 쌍 1:1 (min 길이).
      3) len(srcAttr)==len(dstAttr): obj 쌍 × attr 인덱스 모두.
    그 외에는 연결 실패.

    Returns:
        (count, mode_label) — 연결 개수와 적용된 패턴 설명.

    Raises:
        ValueError: 입력이 비었거나 어떤 패턴에도 맞지 않을 때.
    """
    if not src_objs or not dst_objs:
        raise ValueError("Source/Destination object list is empty.")
    if not src_attrs or not dst_attrs:
        raise ValueError("Select source/destination attributes first.")

    smaller = min(len(src_objs), len(dst_objs))
    count = 0

    # 1) 1 obj 1 attr-set -> #obj #attr
    if len(src_objs) == 1 and len(src_attrs) == len(dst_attrs):
        for dst_obj in dst_objs:
            for i in range(len(dst_attrs)):
                cmds.connectAttr(
                    "{0}.{1}".format(src_objs[0], src_attrs[i]),
                    "{0}.{1}".format(dst_obj, dst_attrs[i]),
                    force=True)
                count += 1
        mode = "1 obj -> #objs, attr set matched"

    # 2) #obj 1 attr -> #obj 1 attr
    elif len(src_attrs) == 1 and len(dst_attrs) == 1:
        for i in range(smaller):
            cmds.connectAttr(
                "{0}.{1}".format(src_objs[i], src_attrs[0]),
                "{0}.{1}".format(dst_objs[i], dst_attrs[0]),
                force=True)
            count += 1
        mode = "#objs -> #objs, 1 attr -> 1 attr"

    # 3) #obj #attr -> #obj #attr
    elif len(src_attrs) == len(dst_attrs):
        for i in range(smaller):
            for j in range(len(dst_attrs)):
                cmds.connectAttr(
                    "{0}.{1}".format(src_objs[i], src_attrs[j]),
                    "{0}.{1}".format(dst_objs[i], dst_attrs[j]),
                    force=True)
                count += 1
        mode = "#objs -> #objs, #attr -> #attr"

    else:
        raise ValueError(
            "Connection fail: attribute counts do not match "
            "(src {0}, dst {1}).".format(len(src_attrs), len(dst_attrs)))

    return count, mode


def connect_52_facial(src_objs, dst_objs):
    """52 ARKit 페이셜 어트리뷰트를 src -> dst 로 일괄 연결 (MEL JUN_cmd_connect_52Facial 포팅).

    obj 쌍을 min 길이만큼 1:1 로 묶고, 각 쌍에서 52개 어트리뷰트를 같은 이름으로 연결한다.
    없는 어트리뷰트는 건너뛴다.

    Returns:
        (connected_count, skipped_count).
    """
    if not src_objs or not dst_objs:
        raise ValueError("Source/Destination object list is empty.")

    smaller = min(len(src_objs), len(dst_objs))
    connected = 0
    skipped = 0

    for i in range(smaller):
        bs_src = src_objs[i]
        bs_dst = dst_objs[i]
        for name in FACIAL_52:
            try:
                cmds.connectAttr(
                    "{0}.{1}".format(bs_src, name),
                    "{0}.{1}".format(bs_dst, name),
                    force=True)
                connected += 1
            except Exception:
                # 소스/타겟에 해당 어트리뷰트가 없으면 스킵 (MEL catch 동작).
                skipped += 1

    return connected, skipped
