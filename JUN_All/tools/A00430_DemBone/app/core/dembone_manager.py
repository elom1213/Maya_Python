# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 작업 오케스트레이션 (maya.cmds 의존, UI 비의존)
#
# UI 는 여기 있는 3개 job 만 부른다. 각 job 은 항상 같은 3단계로 흐른다.
#
#     검증  ->  씬에서 취득(scene_sampler)  ->  numpy 솔브  ->  씬에 적용
#
# 어느 단계에서 실패했는지가 로그로 분명히 남도록, 검증은 **한 번에 모아서** 돌려준다
# (하나 고치면 다음 게 나오는 식으로 반복하지 않게).

import time

import numpy as np

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import joint_builder
from . import joint_writer
from . import mesh_utils
from . import scene_sampler
from . import skin_writer
from . import solver_init
from . import solver_refine
from . import solver_transforms
from . import solver_weights
from .solver_common import Progress, bone_errors, model_size, rmse


class SolveConfig(object):
    """UI 입력 한 벌. 필드가 많아 dict 대신 클래스로 둔다(오타를 빨리 잡으려고)."""

    def __init__(self, **kwargs):
        # --- 입력 ---
        self.cache_mesh = ""
        self.rest_mesh = ""
        self.target_mesh = ""
        self.joints = []
        self.start = 1
        self.end = 24
        self.stride = 1
        self.rest_frame = None

        # --- 웨이트 ---
        self.nnz = 8
        self.weights_smooth = 1e-4
        self.smooth_step = 1.0
        self.smooth_iters = 20
        self.n_weights_iters = 3
        self.prune = 0.0
        self.use_existing_weights = False
        self.lock_amount = 0.0
        self.lock_vertices = None            # None = 전체, list = 그 버텍스만

        # --- 트랜스폼 ---
        self.n_trans_iters = 5
        self.trans_affine = 10.0
        self.trans_affine_norm = 4.0
        self.lock_joints = []
        self.bake_translation = True
        self.bake_rotation = True
        self.euler_filter = True

        # --- 조인트 생성 (Decompose) ---
        self.target_bones = 20
        self.init_iters = 5
        self.init_max_frames = 30
        self.single_root = False
        self.joint_prefix = "demBone"

        # --- 교대 최적화 ---
        self.n_iters = 10
        self.tolerance = 1e-3
        self.patience = 3

        # --- 기타 ---
        self.chunk = 2000
        self.apply_result = True

        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError("Unknown config field: {0}".format(key))
            setattr(self, key, value)

    def target(self):
        return self.target_mesh or self.rest_mesh or self.cache_mesh

    def rest(self):
        return self.rest_mesh or self.cache_mesh


def validate(cfg, need_weights=False, need_joints=True):
    """설정을 검사해 문제 목록(문자열)을 돌려준다. 빈 리스트면 진행 가능."""
    problems = []

    if not cfg.cache_mesh or not cmds.objExists(cfg.cache_mesh):
        problems.append("Cache mesh is not set or does not exist.")
    if cfg.rest_mesh and not cmds.objExists(cfg.rest_mesh):
        problems.append("Rest mesh '{0}' does not exist.".format(cfg.rest_mesh))
    if cfg.target_mesh and not cmds.objExists(cfg.target_mesh):
        problems.append("Target mesh '{0}' does not exist.".format(cfg.target_mesh))

    missing = [j for j in cfg.joints if not cmds.objExists(j)]
    if missing:
        problems.append("Joints not found: {0}".format(", ".join(missing[:5])))
    if need_joints and len(cfg.joints) < 1:
        problems.append("At least one joint is required.")

    if problems:
        return problems

    # 버텍스 수는 셰이프 기준으로 센다(트랜스폼에 걸면 셰이프가 여럿일 때 틀린다).
    try:
        counts = {"cache": mesh_utils.vertex_count(cfg.cache_mesh)}
        if cfg.rest_mesh:
            counts["rest"] = mesh_utils.vertex_count(cfg.rest_mesh)
        if cfg.target_mesh:
            counts["target"] = mesh_utils.vertex_count(cfg.target_mesh)
    except ValueError as exc:
        return [str(exc)]

    unique = set(counts.values())
    if len(unique) > 1:
        problems.append("Vertex counts differ: {0}".format(
            ", ".join("{0}={1}".format(k, v) for k, v in sorted(counts.items()))))

    frames = mesh_utils.frame_list(cfg.start, cfg.end, cfg.stride)
    if len(frames) < 2:
        problems.append("Need at least 2 sample frames (check Start/End/Stride).")

    if need_weights:
        skin = scene_sampler.skin_cluster_of(cfg.target())
        if not skin:
            problems.append(
                "'{0}' has no skinCluster - this mode needs existing weights.".format(
                    cfg.target()))

    return problems


def _lock_array(cfg, n_v):
    """(nV,) 소프트 락 배열. 락이 없으면 None."""
    if cfg.lock_amount <= 0.0:
        return None
    lock = np.zeros(n_v)
    if cfg.lock_vertices is None:
        lock[:] = cfg.lock_amount
    else:
        idx = np.asarray([i for i in cfg.lock_vertices if 0 <= i < n_v], dtype=int)
        if idx.size:
            lock[idx] = cfg.lock_amount
    return lock


def _report(cfg, data, W, M, elapsed, extra=None):
    size = model_size(data["U"])
    err = rmse(data["U"], data["V"], M, W, chunk=cfg.chunk)
    avg_inf, max_inf = skin_writer.influence_stats(W)
    out = {
        "rmse": err,
        "rmse_pct": (100.0 * err / size) if size > 0 else 0.0,
        "model_size": size,
        "vertices": int(data["U"].shape[0]),
        "bones": int(M.shape[1]),
        "frames": len(data["frames"]),
        "avg_influences": avg_inf,
        "max_influences": max_inf,
        "seconds": elapsed,
    }
    if extra:
        out.update(extra)
    return out


def _sample(cfg, prog, need_faces=True):
    skin = scene_sampler.skin_cluster_of(cfg.target())
    return scene_sampler.sample(
        cfg.cache_mesh, cfg.joints, cfg.start, cfg.end, stride=cfg.stride,
        rest_mesh=cfg.rest_mesh or None, rest_frame=cfg.rest_frame,
        skin_cluster=skin, need_faces=need_faces, progress=prog)


# ==========================================================================
# jobs
# ==========================================================================

def solve_weights_job(cfg, progress=None, log=None):
    """캐시 + 조인트 애님 -> 스킨 웨이트. (원본 `--nTransIters=0`)"""
    prog = Progress(progress)
    say = log or (lambda *_a: None)
    t0 = time.time()

    say("Sampling scene...")
    data = _sample(cfg, prog.sub(0.0, 0.3))
    n_v = data["U"].shape[0]

    w_init = None
    lock = None
    if cfg.use_existing_weights or cfg.lock_amount > 0.0:
        skin = scene_sampler.skin_cluster_of(cfg.target())
        if skin:
            w_init = skin_writer.read_weights(cfg.target(), cfg.joints, skin)
            lock = _lock_array(cfg, n_v)
            say("Starting from existing weights of '{0}'.".format(skin))
        else:
            say("No existing skinCluster - starting from scratch.")

    say("Solving weights ({0} verts, {1} joints, {2} frames)...".format(
        n_v, len(cfg.joints), len(data["frames"])))
    W = solver_weights.solve_weights(
        data["U"], data["V"], data["M"], faces=data["faces"], nnz=cfg.nnz,
        weights_smooth=cfg.weights_smooth, smooth_step=cfg.smooth_step,
        smooth_iters=cfg.smooth_iters, n_iters=cfg.n_weights_iters,
        w_init=w_init, lock_weights=lock, chunk=cfg.chunk,
        progress=prog.sub(0.3, 0.65))

    skin_name = None
    if cfg.apply_result:
        say("Applying weights...")
        with undo_chunk():
            skin_name = skin_writer.apply_weights(
                cfg.target(), cfg.joints, W, max_influences=cfg.nnz,
                rest_frame=data["rest_frame"], prune=cfg.prune)
        say("Weights written to '{0}'.".format(skin_name))
    prog.tick(1.0, "done")

    return _report(cfg, data, W, data["M"], time.time() - t0,
                   {"skin_cluster": skin_name, "weights": W, "data": data})


def solve_transforms_job(cfg, progress=None, log=None):
    """캐시 + 기존 웨이트 -> 본 애니메이션. (원본 `--nWeightsIters=0`)"""
    prog = Progress(progress)
    say = log or (lambda *_a: None)
    t0 = time.time()

    say("Sampling scene...")
    data = _sample(cfg, prog.sub(0.0, 0.25), need_faces=False)

    skin = scene_sampler.skin_cluster_of(cfg.target())
    W = skin_writer.read_weights(cfg.target(), cfg.joints, skin)
    say("Read weights from '{0}'.".format(skin))

    lock_bones = np.asarray(
        [j in set(cfg.lock_joints) for j in cfg.joints], dtype=bool)
    if lock_bones.any():
        say("{0} bone(s) locked.".format(int(lock_bones.sum())))

    say("Solving bone transformations...")
    M = solver_transforms.solve_transforms(
        data["U"], data["V"], W, M_init=data["M"], n_iters=cfg.n_trans_iters,
        trans_affine=cfg.trans_affine, trans_affine_norm=cfg.trans_affine_norm,
        lock_bones=lock_bones, progress=prog.sub(0.25, 0.6))

    keys = 0
    if cfg.apply_result:
        say("Baking keys...")
        with undo_chunk():
            keys = joint_writer.bake(
                cfg.joints, M, data["frames"], data["bind_world"],
                translation=cfg.bake_translation, rotation=cfg.bake_rotation,
                euler_filter=cfg.euler_filter, skip=cfg.lock_joints,
                progress=prog.sub(0.85, 0.15))
        say("{0} keys set.".format(keys))
    prog.tick(1.0, "done")

    return _report(cfg, data, W, M, time.time() - t0,
                   {"keys": keys, "transforms": M, "data": data})


def refine_job(cfg, progress=None, log=None):
    """웨이트와 본 변환을 번갈아 최적화. (원본 `compute()`)"""
    prog = Progress(progress)
    say = log or (lambda *_a: None)
    t0 = time.time()

    say("Sampling scene...")
    data = _sample(cfg, prog.sub(0.0, 0.2))
    n_v = data["U"].shape[0]

    skin = scene_sampler.skin_cluster_of(cfg.target())
    W = None
    if skin:
        W = skin_writer.read_weights(cfg.target(), cfg.joints, skin)
        say("Starting from existing weights of '{0}'.".format(skin))
    else:
        say("No skinCluster found - weights start from the rigid fit.")

    lock = _lock_array(cfg, n_v) if W is not None else None
    lock_bones = np.asarray(
        [j in set(cfg.lock_joints) for j in cfg.joints], dtype=bool)

    start_err = None
    if W is not None:
        start_err = rmse(data["U"], data["V"], data["M"], W, chunk=cfg.chunk)
        say("Start RMSE = {0:.6f}".format(start_err))

    M, W, history = solver_refine.refine(
        data["U"], data["V"], data["M"], W, faces=data["faces"],
        n_iters=cfg.n_iters, tolerance=cfg.tolerance, patience=cfg.patience,
        n_trans_iters=cfg.n_trans_iters, n_weights_iters=cfg.n_weights_iters,
        nnz=cfg.nnz, weights_smooth=cfg.weights_smooth,
        smooth_step=cfg.smooth_step, smooth_iters=cfg.smooth_iters,
        trans_affine=cfg.trans_affine, trans_affine_norm=cfg.trans_affine_norm,
        lock_bones=lock_bones, lock_weights=lock, chunk=cfg.chunk,
        progress=prog.sub(0.2, 0.65), log=say)

    skin_name = None
    keys = 0
    if cfg.apply_result:
        say("Applying weights and baking keys...")
        with undo_chunk():
            skin_name = skin_writer.apply_weights(
                cfg.target(), cfg.joints, W, max_influences=cfg.nnz,
                rest_frame=data["rest_frame"], prune=cfg.prune)
            keys = joint_writer.bake(
                cfg.joints, M, data["frames"], data["bind_world"],
                translation=cfg.bake_translation, rotation=cfg.bake_rotation,
                euler_filter=cfg.euler_filter, skip=cfg.lock_joints,
                progress=prog.sub(0.9, 0.1))
        say("Weights written to '{0}', {1} keys set.".format(skin_name, keys))
    prog.tick(1.0, "done")

    return _report(cfg, data, W, M, time.time() - t0,
                   {"skin_cluster": skin_name, "keys": keys,
                    "history": history, "start_rmse": start_err,
                    "weights": W, "transforms": M, "data": data})


def decompose_job(cfg, progress=None, log=None):
    """캐시만으로 **조인트까지 만들어 낸다**. (원본 `-b N` / Full Decomposition)

    흐름: 지오메트리 취득 -> LBG-VQ 클러스터링 -> 본 변환 -> 교대 최적화 ->
          조인트 생성 -> 바인드 -> 키 베이크.
    """
    prog = Progress(progress)
    say = log or (lambda *_a: None)
    t0 = time.time()

    say("Sampling geometry...")
    data = scene_sampler.sample_geometry(
        cfg.cache_mesh, cfg.start, cfg.end, stride=cfg.stride,
        rest_mesh=cfg.rest_mesh or None, rest_frame=cfg.rest_frame,
        need_faces=True, progress=prog.sub(0.0, 0.15))

    U = data["U"]
    V = data["V"]
    n_v = U.shape[0]
    n_f = V.shape[0]

    # 클러스터링은 프레임 하나하나가 아니라 "포즈가 얼마나 다양한가"로 결정된다.
    # 오차표 비용이 O(nV*nB*nF) 라 초기화에서는 프레임을 고르게 솎아 쓴다.
    limit = max(2, int(cfg.init_max_frames))
    picked = np.unique(np.linspace(0, n_f - 1, min(n_f, limit)).astype(int))
    V_init = V[picked]
    if picked.size < n_f:
        say("Clustering on {0} of {1} frames.".format(picked.size, n_f))

    neighbors = None
    if data["faces"]:
        from . import laplacian as _lap
        neighbors = _lap.neighborhood_from_faces(n_v, data["faces"])

    say("Creating bone clusters (target {0})...".format(cfg.target_bones))
    W, _label, n_b = solver_init.initialize(
        U, V_init, data["faces"], cfg.target_bones, n_init_iters=cfg.init_iters,
        neighbors=neighbors, progress=prog.sub(0.15, 0.35), log=say)
    say("{0} bone(s) created.".format(n_b))

    say("Solving bone transformations...")
    M = solver_transforms.solve_transforms(
        U, V, W, M_init=None, n_iters=max(1, cfg.n_trans_iters),
        trans_affine=cfg.trans_affine, trans_affine_norm=cfg.trans_affine_norm,
        progress=prog.sub(0.5, 0.1))

    history = []
    if cfg.n_iters > 0:
        say("Refining...")
        M, W, history = solver_refine.refine(
            U, V, M, W, faces=data["faces"], n_iters=cfg.n_iters,
            tolerance=cfg.tolerance, patience=cfg.patience,
            n_trans_iters=cfg.n_trans_iters, n_weights_iters=cfg.n_weights_iters,
            nnz=cfg.nnz, weights_smooth=cfg.weights_smooth,
            smooth_step=cfg.smooth_step, smooth_iters=cfg.smooth_iters,
            trans_affine=cfg.trans_affine, trans_affine_norm=cfg.trans_affine_norm,
            chunk=cfg.chunk, progress=prog.sub(0.6, 0.3), log=say)

    positions = joint_builder.bind_positions(U, W, cfg.trans_affine_norm)
    root = None
    if cfg.single_root:
        root = joint_builder.pick_root(bone_errors(U, V_init, M[picked]))
        say("Root bone: index {0}.".format(root))

    joints = []
    skin_name = None
    keys = 0
    if cfg.apply_result:
        if scene_sampler.skin_cluster_of(cfg.target()):
            say("The target already has a skinCluster - the new joints are added to "
                "it and the old influences end up with zero weight.")
        say("Creating {0} joint(s)...".format(n_b))
        with undo_chunk():
            joints, bind_world = joint_builder.create_joints(
                positions, root=root, prefix=cfg.joint_prefix,
                radius=joint_builder.suggest_radius(U, n_b))
            skin_name = skin_writer.apply_weights(
                cfg.target(), joints, W, max_influences=cfg.nnz,
                rest_frame=data["rest_frame"], prune=cfg.prune)
            keys = joint_writer.bake(
                joints, M, data["frames"], bind_world,
                translation=cfg.bake_translation, rotation=cfg.bake_rotation,
                euler_filter=cfg.euler_filter, progress=prog.sub(0.92, 0.08))
        say("Weights written to '{0}', {1} keys set.".format(skin_name, keys))
    prog.tick(1.0, "done")

    return _report(cfg, data, W, M, time.time() - t0,
                   {"skin_cluster": skin_name, "keys": keys, "joints": joints,
                    "history": history, "weights": W, "transforms": M,
                    "positions": positions, "data": data})
