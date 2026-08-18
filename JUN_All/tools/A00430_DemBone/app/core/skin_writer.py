# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 푼 웨이트를 skinCluster 에 쓰기 (maya.cmds / OpenMaya 의존)
#
# `cmds.skinPercent` 는 버텍스마다 명령을 부르므로 2만 버텍스에서는 못 쓴다.
# `MFnSkinCluster.setWeights` 로 **전체를 한 번에** 쓴다 (실측: 20k x 20 인플루언스 = 0.04초).
#
# 인플루언스 순서 함정: setWeights 에 넘기는 웨이트 배열은
# `[v0_i0, v0_i1, ..., v1_i0, ...]` 순서이고, 여기서 i 는 우리가 넘긴 **인덱스 배열의 순서**다.
# 그 인덱스는 `influenceObjects()` 에서의 자리인 **물리 인덱스**여야 한다 —
# `indexForInfluenceObject` 의 logical index 를 넘기면 undo 등으로 인덱스가 듬성해진
# skinCluster 에서 `kInvalidParameter` 로 죽는다(`Framework.core.maya_skin` 참고).
# 반대로 `matrix[]`/`bindPreMatrix[]` 플러그를 직접 다룰 때는 logical index 가 맞다
# (`scene_sampler.bind_pre_from_skin`).

import numpy as np

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core import maya_shape
from Framework.core import maya_skin

from . import mesh_utils
from . import scene_sampler


def _complete_component(n_v):
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.setCompleteData(int(n_v))
    return comp


def ensure_skin_cluster(mesh, joints, max_influences=8, rest_frame=None,
                        name="A00430_skinCluster"):
    """메시에 skinCluster 를 보장한다. 이미 있으면 빠진 조인트만 인플루언스로 추가.

    새로 만들 때는 Rest Frame 으로 시간을 옮겨 바인드 포즈를 맞춘다 - 바인드는 명령을
    부르는 **그 시점의 조인트 위치**로 잡히기 때문이다.

    Returns:
        (skinCluster 이름, 새로 만들었는지 여부)
    """
    shape = mesh_utils.shape_of(mesh)
    existing = scene_sampler.skin_cluster_of(mesh)

    if existing:
        current = set(scene_sampler.influence_names(existing))
        current_short = set(cmds.ls(list(current)) or [])
        for joint in joints:
            long_name = (cmds.ls(joint, l=True) or [joint])[0]
            if long_name in current or joint in current_short:
                continue
            cmds.skinCluster(existing, edit=True, addInfluence=joint,
                             lockWeights=True, weight=0.0)
            # addInfluence 가 걸어둔 잠금을 풀어 준다(안 풀면 이후 편집이 막힌다).
            try:
                cmds.setAttr("{0}.liw".format(joint), False)
            except Exception:
                pass
        return existing, False

    restore = None
    if rest_frame is not None:
        restore = cmds.currentTime(q=True)
        cmds.currentTime(rest_frame, edit=True)
    try:
        skin = cmds.skinCluster(list(joints), shape, toSelectedBones=True,
                                maximumInfluences=int(max_influences),
                                normalizeWeights=1, name=name)[0]
    finally:
        if restore is not None:
            cmds.currentTime(restore, edit=True)
    return skin, True


def apply_weights(mesh, joints, W, skin_cluster=None, max_influences=8,
                  rest_frame=None, prune=0.0):
    """(nV, nB) 웨이트를 skinCluster 에 쓴다.

    Args:
        mesh: 대상 메시.
        joints: W 의 열 순서와 같은 조인트 목록.
        W: (nV, nB) 웨이트. 행 합 1 을 가정한다.
        skin_cluster: 지정하면 그것을 쓴다. None 이면 찾거나 새로 만든다.
        prune: 이 값 이하 웨이트는 0 으로 만들고 다시 정규화한다.

    Returns:
        skinCluster 이름.
    """
    W = np.asarray(W, dtype=float)

    if skin_cluster is None:
        skin_cluster, _ = ensure_skin_cluster(
            mesh, joints, max_influences=max_influences, rest_frame=rest_frame)

    if prune > 0.0:
        W = np.where(W <= prune, 0.0, W)
        s = W.sum(axis=1)
        s[s <= 1e-12] = 1.0
        W = W / s[:, None]

    # 웨이트를 쓰는 대상 셰이프는 **그 디포머가 실제로 변형하는 셰이프**여야 한다.
    dag = maya_shape.shape_dag(mesh, deformer=skin_cluster, type_="mesh")

    fn = scene_sampler.skin_fn(skin_cluster)
    influences = fn.influenceObjects()
    # get/setWeights 는 **물리** 인덱스를 받는다(Framework.core.maya_skin 참고).
    # logical index 를 넘기면 undo 등으로 인덱스가 듬성해진 skinCluster 에서 죽는다.
    inf_indices = maya_skin.weight_indices(len(influences))

    # 인플루언스 -> W 의 열 매핑. skinCluster 에만 있는 조인트는 0 이 된다.
    wanted = {}
    for col, joint in enumerate(joints):
        long_name = (cmds.ls(joint, l=True) or [joint])[0]
        wanted[long_name] = col

    columns = []
    for d in influences:
        columns.append(wanted.get(d.fullPathName(), -1))

    n_v, n_b = W.shape
    if n_b != len(joints):
        raise ValueError("Weight matrix has {0} columns but {1} joints given.".format(
            n_b, len(joints)))

    flat = np.zeros((n_v, len(influences)))
    for slot, col in enumerate(columns):
        if col >= 0:
            flat[:, slot] = W[:, col]

    comp = _complete_component(n_v)
    fn.setWeights(dag, comp, inf_indices,
                  om.MDoubleArray(flat.ravel().tolist()), False)
    return skin_cluster


def read_weights(mesh, joints, skin_cluster=None):
    """skinCluster 에서 (nV, nB) 웨이트를 읽는다. joints 열 순서를 따른다.

    솔버의 시작값(w_init), 소프트 락 대상, Solve Transforms 의 입력으로 쓴다.
    """
    if skin_cluster is None:
        skin_cluster = scene_sampler.skin_cluster_of(mesh)
    if not skin_cluster:
        raise ValueError("'{0}' has no skinCluster to read weights from.".format(mesh))

    dag = maya_shape.shape_dag(mesh, deformer=skin_cluster, type_="mesh")
    fn = scene_sampler.skin_fn(skin_cluster)
    influences = fn.influenceObjects()
    inf_indices = maya_skin.weight_indices(len(influences))   # 물리 인덱스

    n_v = mesh_utils.vertex_count(mesh, deformer=skin_cluster)
    comp = _complete_component(n_v)
    flat = fn.getWeights(dag, comp, inf_indices)
    table = np.asarray(flat, dtype=float).reshape(n_v, len(influences))

    slot_of = {}
    for slot, d in enumerate(influences):
        slot_of[d.fullPathName()] = slot

    W = np.zeros((n_v, len(joints)))
    for col, joint in enumerate(joints):
        long_name = (cmds.ls(joint, l=True) or [joint])[0]
        slot = slot_of.get(long_name)
        if slot is not None:
            W[:, col] = table[:, slot]
    return W


def influence_stats(W, eps=1e-9):
    """(평균 인플루언스 수, 최대 인플루언스 수) - 리포트용."""
    counts = (np.asarray(W) > eps).sum(axis=1)
    if counts.size == 0:
        return 0.0, 0
    return float(counts.mean()), int(counts.max())
