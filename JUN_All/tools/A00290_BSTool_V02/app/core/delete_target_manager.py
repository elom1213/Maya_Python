# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00290_BSTool_V02 - Target > Edit > Delete 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# 체크한 타겟들을 blendShape 노드에서 **지운다**(weight 슬롯 · 타겟 데이터 · 별칭째).
#
# ## 직접 removeMultiInstance 하지 않고 마야의 MEL 을 부르는 이유
#
# `inputTargetGroup[i]` 를 통째로 지우면 **undo 로 되살아나지 않는다** — 델타가 빈 채로
# 돌아온다(target_order_manager._remove_element 주석, 실측). 마야 Shape Editor 의 Delete 가
# 부르는 `blendShapeDeleteTargetGroup`(scripts/others) 은 그걸 알고 **잎(inputTargetItem ·
# targetWeights)부터 지운 뒤** 그룹을 지운다. 인비트윈 · combinationShape · 타겟 폴더
# (parentDirectory/nextTarget) · sculptTargetIndex · 별칭까지 같이 정리한다.
# 같은 일을 다시 짜지 않고 그대로 쓴다 — 결과가 Shape Editor 의 Delete 와 똑같다.
#
# - weight 가 **lock** 이면 그 MEL 은 경고만 내고 건너뛴다. 그래서 미리 걸러 알린다.
# - 라이브로 연결돼 있던 **타겟 메시는 씬에 남는다**(마야도 그렇다). 연결만 끊긴다.
# - 남은 타겟의 **인덱스는 그대로**다(빈 자리가 생긴다). 채우려면 Target Order 탭.

import maya.cmds as cmds
import maya.mel as mel

from . import blendshape_utils as bsu
from . import target_order_manager as tom


def list_targets(bs_node):
    """[(weight 인덱스, 타겟 이름), ...] 를 인덱스 오름차순으로."""
    return tom.list_targets(bs_node)


def is_locked(bs_node, index):
    return bool(cmds.getAttr("{0}.weight[{1}]".format(bs_node, index), lock=True))


def delete_targets(bs_node, names):
    """이름으로 고른 타겟들을 지운다.

    호출부가 `undo_chunk()` 로 감싸면 **Ctrl+Z 한 번**에 전부 돌아온다.
    반환: {"deleted": [이름...], "locked": [이름...], "missing": [이름...]}
    """
    if not bsu.is_blendshape(bs_node):
        raise RuntimeError("'{0}' is not a blendShape node.".format(bs_node))

    index_of = {name: index for index, name in list_targets(bs_node)}
    report = {"deleted": [], "locked": [], "missing": []}
    for name in names:
        index = index_of.get(name)
        if index is None:
            report["missing"].append(name)
            continue
        if is_locked(bs_node, index):
            report["locked"].append(name)
            continue
        ok = mel.eval('blendShapeDeleteTargetGroup("{0}", {1})'.format(bs_node, index))
        if ok:
            report["deleted"].append(name)
        else:
            report["locked"].append(name)
    return report
