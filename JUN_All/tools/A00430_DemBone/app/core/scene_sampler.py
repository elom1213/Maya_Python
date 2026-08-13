# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 씬 -> numpy 데이터 취득 (maya.cmds / OpenMaya 의존)
#
# 솔버가 먹는 3가지를 씬에서 뽑아 온다.
#
#   U : (nV, 3)        rest 포즈 (Rest Frame 의 rest 메시, 월드)
#   V : (nF, nV, 3)    프레임별 캐시 메시 위치 (월드)
#   M : (nF, nB, 4, 4) 본 상대 변환 = bindPreMatrix[j] @ joint.worldMatrix(k)
#
# **M 의 곱 순서**가 이 파일의 전부다. 마야는 행벡터 규약이라 "먼저 적용할 것이 왼쪽"이고,
# skinCluster 가 쓰는 스키닝 행렬이 정확히 `bindPreMatrix[j] * matrix[j]` 다.
# 원본 Dem Bones 의 `EvaluateGlobalTransform(t) * bind^-1` (열벡터 규약, FbxReader.cpp:197)
# 과 같은 것을 전치해 쓴 것뿐이다.
#
# 바인드 행렬은 두 곳에서 온다:
#   1. 기존 skinCluster 가 있으면 그 `bindPreMatrix` (인덱스는 반드시
#      `indexForInfluenceObject` 로 얻는다 - 배열 순서를 가정하면 안 된다)
#   2. 없으면 Rest Frame 의 joint.worldMatrix 를 역행렬로
#
# 프레임 루프는 한 번만 돈다(메시 + 조인트를 같은 패스에서 읽는다).
# 실측: 20,100 버텍스 / 조인트 20 개 = 프레임당 약 12ms.

import numpy as np

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from . import mesh_utils
from .solver_common import Progress


def dag_path(node):
    sel = om.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)


def skin_cluster_of(mesh):
    """메시에 걸린 skinCluster 이름. 없으면 None."""
    shape = mesh_utils.shape_of(mesh)
    found = cmds.ls(cmds.listHistory(shape, pdo=True) or [], type="skinCluster") or []
    return found[0] if found else None


def skin_fn(skin_cluster):
    sel = om.MSelectionList()
    sel.add(skin_cluster)
    return oma.MFnSkinCluster(sel.getDependNode(0))


def influence_names(skin_cluster):
    """skinCluster 의 인플루언스 롱네임 목록."""
    fn = skin_fn(skin_cluster)
    return [d.fullPathName() for d in fn.influenceObjects()]


def bind_pre_from_skin(skin_cluster, joints):
    """joints 순서에 맞춘 bindPreMatrix (nB, 4, 4). 없는 조인트는 None 자리.

    logical index 를 `indexForInfluenceObject` 로 얻는다. `matrix[]`/`bindPreMatrix[]` 의
    인덱스는 인플루언스를 붙인 순서라 조밀하지 않을 수 있어서, 배열 위치를 가정하면 틀린다.
    """
    fn = skin_fn(skin_cluster)
    out = []
    for joint in joints:
        try:
            idx = fn.indexForInfluenceObject(dag_path(joint))
        except Exception:
            out.append(None)
            continue
        values = cmds.getAttr("{0}.bindPreMatrix[{1}]".format(skin_cluster, idx))
        out.append(np.asarray(values, dtype=float).reshape(4, 4))
    return out


def joint_world_matrices(joints):
    """현재 시간에서의 joint 월드행렬 (nB, 4, 4)."""
    return np.asarray(
        [np.asarray(dag_path(j).inclusiveMatrix()).reshape(4, 4) for j in joints])


def sample_geometry(cache_mesh, start, end, stride=1, rest_mesh=None,
                    rest_frame=None, need_faces=True, progress=None):
    """조인트 없이 **지오메트리만** 뽑는다 (U / V / faces / frames).

    조인트를 만들어내는 Decompose 모드는 입력에 조인트가 아예 없으므로 이 경로를 쓴다.

    Returns:
        dict: U, V, faces, frames, rest_frame
    """
    prog = progress if isinstance(progress, Progress) else Progress(progress)

    frames = mesh_utils.frame_list(start, end, stride)
    rest_frame = frames[0] if rest_frame is None else int(rest_frame)

    cache_fn = mesh_utils.mesh_fn(cache_mesh)
    n_v = mesh_utils.vertex_count(cache_mesh)

    rest_node = rest_mesh or cache_mesh
    rest_fn = cache_fn if rest_mesh is None else mesh_utils.mesh_fn(rest_mesh)
    if mesh_utils.vertex_count(rest_node) != n_v:
        raise ValueError(
            "Vertex count mismatch: cache {0} has {1}, rest {2} has {3}.".format(
                cache_mesh, n_v, rest_node, mesh_utils.vertex_count(rest_node)))

    current = cmds.currentTime(q=True)
    try:
        prog.tick(0.0, "rest pose")
        cmds.currentTime(rest_frame, edit=True)
        U = mesh_utils.get_points(rest_fn)
        faces = mesh_utils.get_faces(rest_node) if need_faces else None

        n_f = len(frames)
        V = np.empty((n_f, n_v, 3))
        for k, frame in enumerate(frames):
            cmds.currentTime(frame, edit=True)
            try:
                cmds.dgdirty(cache_mesh)
            except Exception:
                pass
            V[k] = mesh_utils.get_points(cache_fn)
            prog.tick((k + 1) / float(n_f), "sampling frame {0}".format(frame))
    finally:
        cmds.currentTime(current, edit=True)

    return {"U": U, "V": V, "faces": faces, "frames": frames,
            "rest_frame": rest_frame}


def sample(cache_mesh, joints, start, end, stride=1, rest_mesh=None,
           rest_frame=None, skin_cluster=None, need_faces=True,
           progress=None):
    """씬에서 U / V / M 을 뽑는다.

    Args:
        cache_mesh: 애니메이션되는 메시(알렘빅 캐시 등).
        joints: 조인트 이름 목록. **순서가 곧 본 인덱스**다.
        start, end, stride: 샘플할 프레임 구간.
        rest_mesh: rest 포즈로 쓸 메시. None 이면 Rest Frame 의 cache_mesh.
        rest_frame: 바인드 포즈로 볼 프레임. None 이면 start.
        skin_cluster: 바인드 행렬을 가져올 기존 skinCluster (선택).
        need_faces: 라플라시안 스무딩용 토폴로지를 함께 읽을지.

    Returns:
        dict: U, V, M, faces, frames, rest_frame, bind_world
    """
    prog = progress if isinstance(progress, Progress) else Progress(progress)

    if not joints:
        raise ValueError("No joints given.")

    frames = mesh_utils.frame_list(start, end, stride)
    rest_frame = frames[0] if rest_frame is None else int(rest_frame)

    cache_fn = mesh_utils.mesh_fn(cache_mesh)
    n_v = mesh_utils.vertex_count(cache_mesh)

    rest_node = rest_mesh or cache_mesh
    rest_fn = cache_fn if rest_mesh is None else mesh_utils.mesh_fn(rest_mesh)
    if mesh_utils.vertex_count(rest_node) != n_v:
        raise ValueError(
            "Vertex count mismatch: cache {0} has {1}, rest {2} has {3}.".format(
                cache_mesh, n_v, rest_node, mesh_utils.vertex_count(rest_node)))

    current = cmds.currentTime(q=True)
    try:
        # ---- rest 포즈 + 바인드 행렬 ----
        prog.tick(0.0, "rest pose")
        cmds.currentTime(rest_frame, edit=True)
        U = mesh_utils.get_points(rest_fn)

        bind_world = joint_world_matrices(joints)
        if skin_cluster:
            from_skin = bind_pre_from_skin(skin_cluster, joints)
            bind_pre = []
            for j, mat in enumerate(from_skin):
                # skinCluster 에 없는 조인트는 Rest Frame 기준으로 채운다.
                bind_pre.append(mat if mat is not None
                                else np.linalg.inv(bind_world[j]))
            bind_pre = np.asarray(bind_pre)
        else:
            bind_pre = np.asarray([np.linalg.inv(m) for m in bind_world])

        faces = mesh_utils.get_faces(rest_node) if need_faces else None

        # ---- 시퀀스 ----
        n_f = len(frames)
        n_b = len(joints)
        V = np.empty((n_f, n_v, 3))
        M = np.empty((n_f, n_b, 4, 4))

        joint_dags = [dag_path(j) for j in joints]

        for k, frame in enumerate(frames):
            cmds.currentTime(frame, edit=True)
            # 알렘빅 노드가 lazy 할 수 있어 확실히 dirty 시킨 뒤 읽는다(A00280 과 같은 이유).
            try:
                cmds.dgdirty(cache_mesh)
            except Exception:
                pass

            V[k] = mesh_utils.get_points(cache_fn)
            for j, d in enumerate(joint_dags):
                world = np.asarray(d.inclusiveMatrix()).reshape(4, 4)
                # 행벡터 규약: 바인드를 먼저 되돌리고 현재 포즈로 간다.
                M[k, j] = bind_pre[j] @ world

            prog.tick((k + 1) / float(n_f), "sampling frame {0}".format(frame))
    finally:
        cmds.currentTime(current, edit=True)

    return {
        "U": U,
        "V": V,
        "M": M,
        "faces": faces,
        "frames": frames,
        "rest_frame": rest_frame,
        "bind_world": bind_world,
    }
