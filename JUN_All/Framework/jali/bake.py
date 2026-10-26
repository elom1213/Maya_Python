# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali.bake - DUMMY_IN 에 걸린 키를 컨트롤러 채널로 베이크 (maya.cmds, UI 비의존)
#
# 출처: JUN_JALI/examples/build_jali_slider_ctl.py 의 bake_ctl_keys() (2026-10-22, direct 리그용). JUN_JALI 는 별도 공개
# 저장소라 import 할 수 없어 여기로 이식했다(JUN_JALI 쪽은 검증 스크립트가 쓰므로 그대로 둔다).
#
# JALI 슬라이더 컨트롤러 리그(A0020/A0030 direct): DUMMY_IN_*.<attr> → CTL_<tag>.ty (JaLi 는 CNT_JaLi.tx/ty) 직결.
# A00540/A00560 은 키를 DUMMY_IN 에 건다 → 이 모듈이 그 키를 컨트롤러 채널로 옮긴다:
#   copy 모드 : DUMMY_IN 의 animCurve 를 통째로 복사(copyKey/pasteKey) → 키 수 · 탄젠트 그대로. 연결은 끊는다.
#   bake 모드 : bakeResults 로 [start, end] 를 sample_by 간격으로 찍는다 (프레임마다 키).
# 더한 것(A00560 D8): cleanup_dummy_in() - 복사 뒤 DUMMY_IN 에 남은 animCurve 를 지운다(진실은 컨트롤러 한 곳),
#               rename_curves()     - pasteKey 가 만든 커브 이름을 JALI_<ctl>_<attr> 로 (레퍼런스 편집 문장을 사람이 알아보게).
# 레퍼런스된 컨트롤러(A00560 클립: ns "JALI")에서도 그대로 동작한다 - disconnectAttr · connectAttr 가 레퍼런스 편집으로 남는다
# (M0-6 실측 2026-10-26: 재열기 failedEdits 0, DUMMY_IN 커브 0, 키 수 = 프레임 + 1).

import maya.cmds as cmds


CTL_PATTERNS = ("CTL_PH_*", "CTL_CO_*", "CNT_JaLi")
CHANNELS = ("tx", "ty")
CURVE_PREFIX = "JALI"


def controllers(namespace=""):
    """namespace("JALI:" 처럼 콜론까지, "" = 루트) 안의 컨트롤러 트랜스폼 목록."""
    return cmds.ls([namespace + p for p in CTL_PATTERNS], type="transform") or []


def dummy_in_nodes(namespace=""):
    return cmds.ls(namespace + "DUMMY_IN_*", type="transform") or []


def _dummy_in_source(plug):
    """plug 의 상류가 DUMMY_IN_* 어트리뷰트면 (DUMMY_IN 플러그, 그 위 animCurve 또는 None). 아니면 (None, None)."""
    src = cmds.listConnections(plug, s=True, d=False, p=True, scn=True) or []
    if not src or "DUMMY_IN_" not in src[0].split(".")[0].split("|")[-1]:
        return None, None
    curves = cmds.listConnections(src[0], s=True, d=False, type="animCurve", scn=True) or []
    return src[0], (curves[0] if curves else None)


def bake_ctl_keys(nodes=None, start=None, end=None, sample_by=1.0, mode="copy", namespace=""):
    """DUMMY_IN 이 직결된 컨트롤러 채널(ty, JaLi 는 tx/ty)을 베이크한다.

    nodes   : 컨트롤러 목록. None 이면 선택된 것, 선택도 없으면 namespace 안의 CTL_PH_* / CTL_CO_* / CNT_JaLi 전부.
    mode    : "copy" - DUMMY_IN 에 animCurve 가 있으면 그 키를 통째로 복사해 컨트롤러에 붙인다 (키 수 · 탄젠트 그대로).
                       animCurve 가 없는 채널(정적 값 · 다른 노드가 미는 값)은 bakeResults 로 프레임마다 찍는다.
              "bake" - 전부 bakeResults 로 [start, end] 를 sample_by 간격으로 찍는다.
    start/end : bakeResults 범위. None 이면 플레이백 범위.
    Returns 베이크된 플러그 목록. 베이크 뒤 DUMMY_IN → 컨트롤러 연결은 끊기고 DUMMY_OUT 은 컨트롤러를 따라간다.
    """
    if nodes is None:
        nodes = cmds.ls(sl=True, type="transform") or controllers(namespace)
    todo = []                      # (plug, dummy_plug, anim_curve)
    for node in nodes:
        for ch in CHANNELS:
            plug = "{0}.{1}".format(node, ch)
            if not cmds.objExists(plug) or cmds.getAttr(plug, lock=True):
                continue
            dummy_plug, curve = _dummy_in_source(plug)
            if dummy_plug:
                todo.append((plug, dummy_plug, curve))
    if not todo:
        return []

    if start is None:
        start = cmds.playbackOptions(q=True, min=True)
    if end is None:
        end = cmds.playbackOptions(q=True, max=True)

    sampled = []
    for plug, dummy_plug, curve in todo:
        node, attr = plug.split(".", 1)
        if mode == "copy" and curve:
            dummy_node, dummy_attr = dummy_plug.split(".", 1)
            cmds.disconnectAttr(dummy_plug, plug)
            cmds.copyKey(dummy_node, attribute=dummy_attr, option="curve")
            cmds.pasteKey(node, attribute=attr, option="replaceCompletely")
        else:
            sampled.append(plug)
    if sampled:
        cmds.bakeResults(sampled, t=(start, end), sampleBy=sample_by, simulation=False,
                         preserveOutsideKeys=True, disableImplicitControl=True, minimizeRotation=False)
    return [p for p, _, _ in todo]


def cleanup_dummy_in(namespace=""):
    """DUMMY_IN_* 에 남은 animCurve 를 지운다(복사 뒤 진실을 컨트롤러 한 곳에). Returns 지운 커브 수."""
    curves = set()
    for node in dummy_in_nodes(namespace):
        curves.update(cmds.listConnections(node, s=True, d=False, type="animCurve") or [])
    if curves:
        cmds.delete(list(curves))
    return len(curves)


def rename_curves(plugs, prefix=CURVE_PREFIX):
    """plug 마다 상류 animCurve 를 <prefix>_<ctl>_<attr> 로 (네임스페이스는 뗀다). Returns {plug: 새 이름}."""
    out = {}
    for plug in plugs:
        node, attr = plug.split(".", 1)
        curves = cmds.listConnections(plug, s=True, d=False, type="animCurve") or []
        if not curves:
            continue
        wanted = "{0}_{1}_{2}".format(prefix, node.split("|")[-1].split(":")[-1], attr)
        out[plug] = cmds.rename(curves[0], wanted)
    return out


def baked_channels(namespace=""):
    """[(plug, animCurve, 키 수)] - 컨트롤러 채널 중 animCurve 가 붙은 것 (Validate 용)."""
    out = []
    for node in controllers(namespace):
        for ch in CHANNELS:
            plug = "{0}.{1}".format(node, ch)
            if not cmds.objExists(plug):
                continue
            curves = cmds.listConnections(plug, s=True, d=False, type="animCurve") or []
            if curves:
                out.append((plug, curves[0], cmds.keyframe(curves[0], q=True, keyframeCount=True) or 0))
    return out


def dummy_in_curve_count(namespace=""):
    """DUMMY_IN_* 에 붙은 animCurve 수 (0 이어야 정상)."""
    n = 0
    for node in dummy_in_nodes(namespace):
        n += len(cmds.listConnections(node, s=True, d=False, type="animCurve") or [])
    return n
