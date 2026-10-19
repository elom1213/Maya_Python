# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - blendWeighted 의 input / weight 다루기 (maya.cmds, UI 비의존)
#
# blendWeighted 의 input[] 과 weight[] 는 **따로 존재하는 멀티 어트리뷰트**다 (같은 인덱스끼리 짝).
#   - input[5] 만 연결하면 weight[5] 원소가 없다 -> Node Editor / Attribute Editor 에 안 보인다.
#   - 없는 weight 는 **1.0 으로 계산된다** (실측: 0.5*0.2 + 0.5*없음 = 0.6).
#   - ★ getAttr bw.weight[5] 를 **읽기만 해도 원소가 생긴다** -> 검사는 반드시 getAttr -mi 목록으로만.
# 이 모듈은 input 을 연결할 때 weight 를 항상 같이 만들고, 지울 때 둘 다 지운다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


MISSING_WEIGHT_VALUE = 1.0      # 빠진 weight 가 계산에 쓰이는 값 - 이 값으로 만들면 결과가 그대로다


def list_nodes(pattern="*"):
    """씬의 blendWeighted 이름 (네임스페이스 포함, 정렬)."""
    return sorted(cmds.ls(pattern, type="blendWeighted", recursive=True) or [])


def _indices(plug):
    return list(cmds.getAttr(plug, multiIndices=True) or [])


def input_source(bw, idx):
    """input[idx] 에 연결된 소스 plug (없으면 None)."""
    src = cmds.listConnections("{0}.input[{1}]".format(bw, idx), source=True, destination=False,
                               plugs=True, skipConversionNodes=True)
    return src[0] if src else None


def rows(bw):
    """[(idx, source_plug|None, weight|None, has_weight_element)] - input · weight 인덱스의 합집합, 인덱스 순.

    weight 가 없는 인덱스는 값을 읽지 않는다(읽으면 원소가 생긴다). 그때 weight 는 None.
    """
    in_idx = set(_indices(bw + ".input"))
    w_idx = set(_indices(bw + ".weight"))
    out = []
    for i in sorted(in_idx | w_idx):
        src = input_source(bw, i) if i in in_idx else None
        has_w = i in w_idx
        w = cmds.getAttr("{0}.weight[{1}]".format(bw, i)) if has_w else None
        out.append((i, src, w, has_w))
    return out


def missing_weights(bw):
    """input 은 있는데 weight 원소가 없는 인덱스."""
    w_idx = set(_indices(bw + ".weight"))
    return [i for i in _indices(bw + ".input") if i not in w_idx]


def next_index(bw):
    used = set(_indices(bw + ".input")) | set(_indices(bw + ".weight"))
    return (max(used) + 1) if used else 0


def find_input(bw, source_plug):
    """source_plug 가 연결된 input 인덱스 (없으면 None)."""
    for i in _indices(bw + ".input"):
        src = input_source(bw, i)
        if src and _same_plug(src, source_plug):
            return i
    return None


def _same_plug(a, b):
    """'JALI_IN.AAA' 와 '|grp|JALI_IN.AAA' 처럼 표기가 달라도 같은 plug 인지."""
    if a == b:
        return True
    try:
        na, aa = a.split(".", 1)
        nb, ab = b.split(".", 1)
        return aa == ab and cmds.ls(na, uuid=True) == cmds.ls(nb, uuid=True)
    except ValueError:
        return False


def add_input(bw, source_plug, weight):
    """source_plug 를 다음 빈 인덱스에 연결하고 **같은 인덱스 weight 를 바로 만든다**. Returns 인덱스.

    이미 연결돼 있으면 새로 연결하지 않고 weight 만 바꾼다.
    """
    if not cmds.objExists(source_plug):
        raise ValueError("Source not found: {0}".format(source_plug))
    with undo_chunk():
        idx = find_input(bw, source_plug)
        if idx is None:
            idx = next_index(bw)
            cmds.connectAttr(source_plug, "{0}.input[{1}]".format(bw, idx))
        cmds.setAttr("{0}.weight[{1}]".format(bw, idx), float(weight))
    return idx


def set_weight(bw, idx, value):
    with undo_chunk():
        cmds.setAttr("{0}.weight[{1}]".format(bw, idx), float(value))


def create_missing(bw, value=MISSING_WEIGHT_VALUE):
    """weight 원소가 없는 input 인덱스에 weight 를 만든다. 기본 1.0 = 계산 결과 그대로. Returns 인덱스 목록."""
    idxs = missing_weights(bw)
    if idxs:
        with undo_chunk():
            for i in idxs:
                cmds.setAttr("{0}.weight[{1}]".format(bw, i), float(value))
    return idxs


def remove(bw, idxs):
    """input[i] (연결 포함) 와 weight[i] 를 둘 다 지운다."""
    with undo_chunk():
        for i in idxs:
            for attr in ("input", "weight"):
                plug = "{0}.{1}[{2}]".format(bw, attr, i)
                if i in _indices("{0}.{1}".format(bw, attr)):
                    cmds.removeMultiInstance(plug, b=True)
