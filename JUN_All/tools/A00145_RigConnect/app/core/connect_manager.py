# -*- coding: utf-8 -*-
"""
connect_manager - Connect 탭 로직.

MEL ConnectionTool V04.02 의 attribute 연결 proc 포팅:
  - JUN_cmd_upd_tsl_attr      -> list_attrs (compound/multi 펼치기)
  - JUN_cmd_upd_tsl_search    -> find_matching / list_attrs(search)
  - JUN_cmd_connect_attr      -> connect_attrs (3가지 브로드캐스트 패턴)
  - JUN_cmd_connect_52Facial  -> (v01.59) 규칙 JSON app/rules/connect/*.json + connect_rules.connect_by_rule

UI 비의존: 위젯에서 읽은 list/str 값만 받는다.
"""

import maya.cmds as cmds
import maya.mel as mel

from tools.A00145_RigConnect.app.core import blendshape_utils as bsu


def channel_box_attrs(obj):
    """obj 의 채널박스에 보이는 어트리뷰트 이름 집합.

    채널박스 = keyable + channelBox(비키어블 표시). 둘 다 listAttr 로 따로 받는다.
    mayapy 실측으로 확인한 함정:
      - `listAttr -k` 는 **hidden 키어블도 돌려준다** -> attributeQuery(hidden) 로 뺀다.
      - 키어블 compound(double3 등)는 부모도 나오지만 채널박스엔 자식(X/Y/Z)만 보인다
        -> 자식이 있는 부모는 뺀다.
    blendShape 타겟(weight 별칭)은 여기 들지 않는다 - list_attrs 가 따로 살린다.
    """
    if not obj:
        return set()
    raw = (cmds.listAttr(obj, keyable=True) or []) + \
          (cmds.listAttr(obj, channelBox=True) or [])
    visible = set()
    for attr in raw:
        if "." in attr or attr in visible:
            continue
        try:
            if cmds.attributeQuery(attr, node=obj, hidden=True):
                continue
            if cmds.attributeQuery(attr, node=obj, numberOfChildren=True):
                continue
        except Exception:
            pass
        visible.add(attr)
    return visible


def list_attrs(obj, search="", channel_box_only=False):
    """obj 의 어트리뷰트 목록을 반환 (MEL JUN_cmd_upd_tsl_attr 포팅).

    - search 가 있으면 listAttr(obj.search) 로 필터한 목록을 기준으로 한다.
    - 이름에 "." 가 들어간(중첩) 항목은 제외한다.
    - multi/compound 어트리뷰트는 getNextFreeMultiIndex 로 판정해
      listAttr -multi 로 자식 어트리뷰트까지 펼친다.
    - **blendShape 노드면 `weight` 멀티를 타겟 이름(별칭)으로 펼친다.** 일반 멀티 확장은
      인덱스 0 하나만 잡아 첫 타겟만 나오므로, 별칭 목록을 직접 쓴다.
    - channel_box_only 면 채널박스에 보이는 것(channel_box_attrs)만 남긴다.
      blendShape 타겟은 채널박스에 늘 보이므로 그대로 둔다.

    Args:
        obj: 대상 오브젝트 이름.
        search: 검색 토큰(optional). listAttr 의 부분 이름으로 사용.
        channel_box_only: True 면 채널박스에 보이는 어트리뷰트만.

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

    visible = None
    if channel_box_only:
        visible = channel_box_attrs(obj) | set(bs_targets)

    # 별칭이 raw 에도 섞여 나올 수 있어 순서를 유지한 채 중복을 제거한다.
    seen = set()
    unique = []
    for attr in result:
        if visible is not None and attr not in visible:
            continue
        if attr not in seen:
            seen.add(attr)
            unique.append(attr)
    return unique


def find_matching(attrs, search):
    """attrs 중 search 토큰을 부분 문자열로 포함하는 항목 (MEL JUN_is_exist 대응)."""
    if not search:
        return []
    return [a for a in attrs if search in a]


def incoming_plug(plug):
    """plug 로 들어오는 연결의 소스 plug 이름. 없으면 "".

    ``connectionInfo -isDestination`` 은 plug 자신뿐 아니라 **부모 compound 가 연결돼
    간접으로 구동되는 자식**(예: ``.t`` 가 연결된 노드의 ``.tx``)에도 True 를 준다 —
    그 자식에 connectAttr 을 걸면 어차피 실패하므로 "이미 연결됨" 으로 함께 다룬다.
    그 경우 소스는 부모 plug 로 돌아온다(``sourceFromDestination``).
    plug 가 없는 등 질의가 실패하면 "" 를 돌려주고, 판단은 뒤의 connectAttr 에 맡긴다.
    """
    try:
        if not cmds.connectionInfo(plug, isDestination=True):
            return ""
        return cmds.connectionInfo(plug, sourceFromDestination=True) or ""
    except Exception:
        return ""


def connect_attrs(src_objs, dst_objs, src_attrs, dst_attrs, force=False):
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

    **이미 연결된 대상 어트리뷰트** (v01.67):
      - ``force=False`` (기본): 대상 플러그에 들어오는 연결이 이미 있으면 **끊지 않고 그대로 둔다.**
        건너뛴 짝은 ``report["kept"]`` 에 (드라이버 plug, 대상 plug, 지금 들어오는 plug) 로 담아
        호출부가 로그로 알릴 수 있게 한다. 이미 같은 드라이버가 걸려 있어도(바꿀 게 없음)
        여기 든다. 부모 compound 가 연결돼 자식이 구동되는 경우도 "연결됨" 으로 본다
        (``connectionInfo -isDestination`` 이 그렇게 답한다, mayapy 실측).
      - ``force=True``: 예전 동작. ``connectAttr -force`` 로 기존 연결을 끊고 새로 건다.
      - 판정은 **드라이버 쪽이 아니라 대상 쪽**만 본다. 드라이버 어트리뷰트가 다른 곳으로
        이미 나가고 있는 것은 팬아웃이라 막을 이유가 없다.

    Args:
        force: 이미 연결된 대상 어트리뷰트를 끊고 다시 걸지(True) 그대로 둘지(False).

    Returns:
        (count, mode_label, report)
        report = {
            "unused_driver_attrs": [...],   # 짝이 없어 연결하지 않은 드라이버 어트리뷰트
            "unused_driven_attrs": [...],   # 짝이 없어 연결하지 않은 대상 어트리뷰트
            "unused_driver_objs":  [...],   # 짝이 없어 쓰지 않은 드라이버 오브젝트
            "unused_driven_objs":  [...],   # 짝이 없어 쓰지 않은 대상 오브젝트
            "failed": [(src plug, dst plug, 사유), ...],
            "kept":   [(src plug, dst plug, 기존 입력 plug), ...],  # force=False 로 둔 것
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
    kept = []

    def _connect(src_obj, src_attr, dst_obj, dst_attr):
        """한 쌍을 연결한다. 실패해도 예외를 올리지 않고 기록만 남긴다.

        force 가 꺼져 있고 대상에 이미 입력 연결이 있으면 건드리지 않고 kept 에 적는다.
        """
        src_plug = "{0}.{1}".format(src_obj, src_attr)
        dst_plug = "{0}.{1}".format(dst_obj, dst_attr)
        if not force:
            existing = incoming_plug(dst_plug)
            if existing:
                kept.append((src_plug, dst_plug, existing))
                return 0
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
        "kept": kept,
    }

    return count, mode, report
