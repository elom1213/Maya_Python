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

from tools.A00145_RigConnect.app.core import blendshape_utils as bsu


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
    - **blendShape 노드면 `weight` 멀티를 타겟 이름(별칭)으로 펼친다.** 일반 멀티 확장은
      인덱스 0 하나만 잡아 첫 타겟만 나오므로, 별칭 목록을 직접 쓴다.

    Args:
        obj: 대상 오브젝트 이름.
        search: 검색 토큰(optional). listAttr 의 부분 이름으로 사용.

    Returns:
        어트리뷰트 이름 문자열 리스트.
    """
    if not obj:
        return []

    # blendShape 면 타겟(별칭) 이름을 맨 앞에 놓는다. 검색어가 있으면 그걸로 거른다.
    bs_targets = bsu.get_blendshape_targets(obj)
    result = [t for t in bs_targets if not search or search in t]

    try:
        if search:
            raw = cmds.listAttr(obj + "." + search) or []
        else:
            raw = cmds.listAttr(obj) or []
    except Exception:
        # search 가 실제 어트리뷰트 이름이 아니면 listAttr 이 실패한다.
        # blendShape 타겟 검색 결과는 그대로 살려서 돌려준다.
        raw = []

    for attr in raw:
        # 중첩 어트리뷰트(이름에 ".") 는 건너뛴다.
        if "." in attr:
            continue

        # blendShape 의 weight 는 위에서 타겟 이름으로 이미 펼쳤다.
        if bs_targets and attr == "weight":
            continue

        # multi 여부를 attributeQuery 로 조용히 판정한다. 예전엔 모든 어트리뷰트에
        # getNextFreeMultiIndex 를 호출했는데, 그 MEL 은 non-multi(스칼라)에서 `attr[0]` 을
        # 찾다 실패해 "No object matches name" 에러를 어트리뷰트 개수만큼 출력했다(catch 해도
        # 출력은 남음). multi 로 확정된 것만 getNextFreeMultiIndex 로 펼치면 결과는 같고 조용하다.
        try:
            is_multi = bool(cmds.attributeQuery(attr, node=obj, multi=True))
        except Exception:
            is_multi = False

        if not is_multi:
            result.append(attr)
        else:
            full = "{0}.{1}".format(obj, attr)
            try:
                idx = mel.eval('getNextFreeMultiIndex("{0}", 0)'.format(full))
                children = cmds.listAttr(
                    "{0}[{1}]".format(full, idx), multi=True) or []
            except Exception:
                children = []
            result.extend(children if children else [attr])

    # 별칭이 raw 에도 섞여 나올 수 있어 순서를 유지한 채 중복을 제거한다.
    seen = set()
    unique = []
    for attr in result:
        if attr not in seen:
            seen.add(attr)
            unique.append(attr)
    return unique


def find_matching(attrs, search):
    """attrs 중 search 토큰을 부분 문자열로 포함하는 항목 (MEL JUN_is_exist 대응)."""
    if not search:
        return []
    return [a for a in attrs if search in a]


def connect_attrs(src_objs, dst_objs, src_attrs, dst_attrs):
    """source -> destination 어트리뷰트 연결 (MEL JUN_cmd_connect_attr 포팅).

    src_attrs / dst_attrs 는 리스트에서 "선택된" 어트리뷰트들이다.
    MEL 의 3가지 패턴을 따른다:
      1) src obj 1개: 한 src 를 **각 dst obj** 의 attr 인덱스별로 (브로드캐스트).
      2) attr 이 양쪽 1개씩: obj 쌍 1:1.
      3) 그 외: obj 쌍 × attr 인덱스 모두.

    **개수가 달라도 중간에 멈추지 않는다.**
      - 어트리뷰트 수가 서로 다르면 **적은 쪽 개수만큼만** 짝지어 연결하고, 남는
        어트리뷰트는 건드리지 않고 그대로 둔다(예: 5개 vs 3개 -> 앞 3쌍만).
      - 오브젝트 수도 같은 규칙(패턴 1의 브로드캐스트는 예외 — 모든 dst obj 를 쓴다).
      - 개별 `connectAttr` 이 실패해도(잠김/타입 불일치/읽기 전용 등) 거기서 중단하지
        않고 나머지를 계속 연결한 뒤, 실패 목록을 함께 돌려준다.
    호출부가 무엇이 남았는지 알려 줄 수 있도록 남은 항목을 report 로 보고한다.

    이 함수는 **양방향**으로 쓰인다(Source->Destination / Destination->Source).
    어느 쪽이 드라이버인지는 인자 순서가 정하므로, report 의 키는 src/dst 가 아니라
    driver/driven 으로 쓴다.

    Returns:
        (count, mode_label, report)
        report = {
            "unused_driver_attrs": [...],   # 짝이 없어 연결하지 않은 드라이버 어트리뷰트
            "unused_driven_attrs": [...],   # 짝이 없어 연결하지 않은 대상 어트리뷰트
            "unused_driver_objs":  [...],   # 짝이 없어 쓰지 않은 드라이버 오브젝트
            "unused_driven_objs":  [...],   # 짝이 없어 쓰지 않은 대상 오브젝트
            "failed": [(src plug, dst plug, 사유), ...],
        }

    Raises:
        ValueError: 오브젝트 목록이 비었거나 어트리뷰트를 하나도 고르지 않았을 때.
    """
    if not src_objs or not dst_objs:
        raise ValueError("Source/Destination object list is empty.")
    if not src_attrs or not dst_attrs:
        raise ValueError("Select source/destination attributes first.")

    # 짝지을 수 있는 만큼만. 남는 쪽은 아래 report 로 알린다.
    pair_count = min(len(src_attrs), len(dst_attrs))
    obj_pairs = min(len(src_objs), len(dst_objs))

    failed = []

    def _connect(src_obj, src_attr, dst_obj, dst_attr):
        """한 쌍을 연결한다. 실패해도 예외를 올리지 않고 기록만 남긴다."""
        src_plug = "{0}.{1}".format(src_obj, src_attr)
        dst_plug = "{0}.{1}".format(dst_obj, dst_attr)
        try:
            cmds.connectAttr(src_plug, dst_plug, force=True)
            return 1
        except Exception as e:
            failed.append((src_plug, dst_plug, str(e).strip()))
            return 0

    count = 0

    # 1) src obj 1개 -> 모든 dst obj 로 브로드캐스트
    if len(src_objs) == 1:
        for dst_obj in dst_objs:
            for i in range(pair_count):
                count += _connect(src_objs[0], src_attrs[i], dst_obj, dst_attrs[i])
        mode = "1 obj -> #objs, attr set matched"
        unused_src_objs, unused_dst_objs = [], []

    # 2) / 3) obj 쌍 1:1 × attr 인덱스
    else:
        for i in range(obj_pairs):
            for j in range(pair_count):
                count += _connect(src_objs[i], src_attrs[j],
                                  dst_objs[i], dst_attrs[j])
        mode = ("#objs -> #objs, 1 attr -> 1 attr" if pair_count == 1
                else "#objs -> #objs, #attr -> #attr")
        unused_src_objs = src_objs[obj_pairs:]
        unused_dst_objs = dst_objs[obj_pairs:]

    report = {
        "unused_driver_attrs": src_attrs[pair_count:],
        "unused_driven_attrs": dst_attrs[pair_count:],
        "unused_driver_objs": unused_src_objs,
        "unused_driven_objs": unused_dst_objs,
        "failed": failed,
    }

    return count, mode, report


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
