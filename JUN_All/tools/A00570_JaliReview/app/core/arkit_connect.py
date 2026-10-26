# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00570_JaliReview - ARKIT_OUT (52) -> 아바타 블렌드셰이프 연결 (maya.cmds, UI 비의존)
#
# 연결은 **별칭 이름이 같은 타겟만** (평가서 §2-11): CLIP:JALI:ARKIT_OUT.jawOpen -> <bs>.jawOpen. 아바타에 없는 타겟(예: tongueOut)은
# missing 으로 보고, 이미 다른 것이 구동하는 타겟은 Skip 기본(A00550 과 같은 정책). 아바타마다 이름이 다른 타겟은 규칙 json 으로:
#   {"name": "...", "map": {"<ARKIT_OUT attr>": "<blendShape target>", ...}}   (없는 키는 같은 이름)
# 연결은 아바타 레퍼런스 노드의 편집으로 남는다(M0 실측) - 검수 씬을 저장하면 다음에 그대로, 클립을 교체해도 산다.

import json
import os

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


def list_blendshapes():
    return sorted(cmds.ls(type="blendShape") or [])


def blendshape_targets(bs):
    """블렌드셰이프 타겟 별칭 목록 (weight 인덱스 순)."""
    if not bs or not cmds.objExists(bs):
        return []
    names = cmds.listAttr(bs + ".weight", multi=True) or []
    return [n.split(".")[-1] for n in names]


def source_attrs(node):
    """ARKIT_OUT 의 사용자 어트리뷰트(= ARKit 52) - 키 가능한 스칼라만."""
    if not node or not cmds.objExists(node):
        return []
    out = []
    for attr in cmds.listAttr(node, userDefined=True) or []:
        try:
            if cmds.getAttr("{0}.{1}".format(node, attr), type=True) in ("double", "float", "doubleLinear", "long", "bool"):
                out.append(attr)
        except RuntimeError:
            continue
    return out


def load_rules(path):
    """규칙 json -> {src attr: target}. 없거나 비면 {}. 깨졌으면 ValueError."""
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        raise ValueError("Cannot read rules {0}: {1}".format(os.path.basename(path), e))
    table = data.get("map") if isinstance(data, dict) else None
    if not isinstance(table, dict):
        raise ValueError("Rules {0} has no 'map' table".format(os.path.basename(path)))
    return {str(k): str(v) for k, v in table.items()}


def plan(src_node, bs, rules=None, skip_connected=True):
    """연결 계획 {"connect": [(src plug, dst plug)], "skipped": [(dst, 이유)], "missing": [src attr]} - 아무것도 바꾸지 않는다."""
    rules = rules or {}
    targets = set(blendshape_targets(bs))
    out = {"connect": [], "skipped": [], "missing": []}
    claimed = {}          # dst -> src  (규칙으로 두 소스가 같은 타겟을 노리면 먼저 온 쪽만 - 계획 단계에서 잡아야 force 가 덮지 않는다)
    for attr in source_attrs(src_node):
        target = rules.get(attr, attr)
        if target not in targets:
            out["missing"].append(attr)
            continue
        src = "{0}.{1}".format(src_node, attr)
        dst = "{0}.{1}".format(bs, target)
        if dst in claimed:
            out["skipped"].append((dst, "already planned from {0}".format(claimed[dst])))
            continue
        if cmds.isConnected(src, dst):
            out["skipped"].append((dst, "already connected to it"))
            continue
        upstream = cmds.listConnections(dst, s=True, d=False, p=True, scn=True) or []
        if upstream and skip_connected:
            out["skipped"].append((dst, "driven by {0}".format(upstream[0])))
            continue
        if cmds.getAttr(dst, lock=True):
            out["skipped"].append((dst, "locked"))
            continue
        out["connect"].append((src, dst))
        claimed[dst] = src
    return out


def connect(src_node, bs, rules=None, skip_connected=True):
    """계획대로 연결한다 (Undo 한 번). Returns plan dict + "connected": 실제 연결 수, "failed": [(dst, 에러)]."""
    if not src_node or not cmds.objExists(src_node):
        raise ValueError("ARKIT_OUT node not found: {0}".format(src_node))
    if not bs or not cmds.objExists(bs):
        raise ValueError("BlendShape not found: {0}".format(bs))
    result = plan(src_node, bs, rules, skip_connected)
    result["connected"] = 0
    result["failed"] = []
    with undo_chunk():
        for src, dst in result["connect"]:
            try:
                cmds.connectAttr(src, dst, force=True)
                result["connected"] += 1
            except RuntimeError as e:
                result["failed"].append((dst, str(e).strip()))
    return result


def connected_count(src_node, bs):
    """src_node 가 bs 를 구동하는 타겟 수 (상태 표시용)."""
    if not src_node or not bs or not cmds.objExists(src_node) or not cmds.objExists(bs):
        return 0
    n = 0
    for attr in source_attrs(src_node):
        dsts = cmds.listConnections("{0}.{1}".format(src_node, attr), s=False, d=True, p=True, scn=True) or []
        if any(d.split(".")[0] == bs for d in dsts):
            n += 1
    return n


def disconnect(src_node, bs):
    """src_node -> bs 연결을 전부 끊는다. Returns 끊은 수."""
    n = 0
    with undo_chunk():
        for attr in source_attrs(src_node):
            src = "{0}.{1}".format(src_node, attr)
            for dst in cmds.listConnections(src, s=False, d=True, p=True, scn=True) or []:
                if dst.split(".")[0] == bs:
                    cmds.disconnectAttr(src, dst)
                    n += 1
    return n
