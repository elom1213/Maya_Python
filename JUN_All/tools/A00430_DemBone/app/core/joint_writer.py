# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 푼 본 변환을 조인트 키로 굽기 (maya.cmds 의존)
#
# 솔버는 **상대 변환** M 만 안다. 조인트에 넣으려면 월드행렬로 되돌려야 한다.
#
#     M = bindPre @ world      ->      world = bind_world @ M      (행벡터 규약)
#
# 원본은 여기서 DemBonesExt::computeRTB 로 부모 기준 로컬 rot/trans 를 직접 계산하고,
# 오일러 플립을 막으려고 toRot() 에서 ±pi 배수 조합을 전수 탐색한다(DemBonesExt.h:245).
#
# 마야에서는 그 두 가지를 마야에게 맡기는 게 맞다:
#   - 로컬 분해: `cmds.xform(ws=True, matrix=...)` 가 부모 공간 + **jointOrient** 까지
#     감안해 t/r 로 풀어 준다. (직접 하면 joint 는 local = R * JO 라 JO 를 빼야 한다)
#   - 오일러 연속성: 다 구운 뒤 `cmds.filterCurve` (Euler Filter) 한 번.
#
# 주의: 프레임마다 **부모를 먼저** 세팅해야 한다. 자식의 월드행렬을 넣을 때 부모가 이미
# 그 프레임 포즈여야 로컬 값이 맞게 나온다.

import numpy as np

import maya.cmds as cmds

from .solver_common import Progress

ROT_ATTRS = ("rotateX", "rotateY", "rotateZ")
TRANS_ATTRS = ("translateX", "translateY", "translateZ")


def _depth(node):
    return len((cmds.ls(node, l=True) or [node])[0].split("|"))


def hierarchy_order(joints):
    """부모가 먼저 오도록 정렬한 (원래 인덱스, 이름) 목록."""
    return sorted(enumerate(joints), key=lambda pair: _depth(pair[1]))


def world_from_relative(M, bind_world):
    """(nF, nB, 4, 4) 상대 변환 -> 월드행렬."""
    M = np.asarray(M, dtype=float)
    bind_world = np.asarray(bind_world, dtype=float)
    return np.einsum('jab,kjbc->kjac', bind_world, M, optimize=True)


def bake(joints, M, frames, bind_world, translation=True, rotation=True,
         euler_filter=True, skip=None, progress=None):
    """푼 본 변환을 조인트 키프레임으로 굽는다.

    Args:
        joints: 조인트 이름 목록 (M 의 본 순서와 동일).
        M: (nF, nB, 4, 4) 상대 변환.
        frames: 길이 nF 의 프레임 번호 목록.
        bind_world: (nB, 4, 4) 바인드 시점 월드행렬.
        translation / rotation: 키를 걸 채널.
        euler_filter: 다 구운 뒤 회전 커브에 오일러 필터를 적용할지.
        skip: 건드리지 않을 조인트 이름들(= 락 걸린 본). 원래 애니메이션을 그대로 둔다.
            **키를 다시 굽지 않는 것이 중요하다** - 구우면 샘플 프레임 위로만 리샘플되어
            사이 키가 사라진다.

    Returns:
        건 키의 개수.
    """
    prog = progress if isinstance(progress, Progress) else Progress(progress)

    world = world_from_relative(M, bind_world)

    skipped = set()
    for name in (skip or []):
        skipped.update(cmds.ls(name, l=True) or [name])
        skipped.add(name)

    def _is_skipped(node):
        if node in skipped:
            return True
        return bool(skipped.intersection(cmds.ls(node, l=True) or []))

    order = [pair for pair in hierarchy_order(joints) if not _is_skipped(pair[1])]
    if not order:
        return 0

    attrs = []
    if translation:
        attrs.extend(TRANS_ATTRS)
    if rotation:
        attrs.extend(ROT_ATTRS)
    if not attrs:
        return 0

    current = cmds.currentTime(q=True)
    keys = 0
    n_f = len(frames)
    try:
        for k, frame in enumerate(frames):
            cmds.currentTime(frame, edit=True)
            for j, joint in order:
                cmds.xform(joint, worldSpace=True,
                           matrix=[float(v) for v in world[k, j].ravel()])
            for _, joint in order:
                cmds.setKeyframe(joint, attribute=attrs, time=frame)
                keys += len(attrs)
            prog.tick((k + 1) / float(n_f), "baking frame {0}".format(frame))
    finally:
        cmds.currentTime(current, edit=True)

    if euler_filter and rotation:
        curves = []
        for _, joint in order:
            for attr in ROT_ATTRS:
                curves.extend(cmds.listConnections(
                    "{0}.{1}".format(joint, attr), type="animCurve", s=True, d=False) or [])
        if curves:
            try:
                cmds.filterCurve(*curves, filter="euler")
            except Exception:
                pass

    return keys
