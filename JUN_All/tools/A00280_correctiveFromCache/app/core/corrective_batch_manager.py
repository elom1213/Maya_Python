# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - 캐시에서 코렉티브 블렌드셰이프 배치 추출 (핵심 로직, UI 비의존)
#
# 포즈별로: abc 캐시를 프레임에서 스냅샷 -> 리그를 그 포즈로 -> 캐시 형상을 EDIT 메시에 복사
# -> invertShape 로 bind(스킨 이전) 델타 생성 -> 솔버 출력에 와이어. (계획서 §3 Route A)

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.core.maya_refresh import suspend_refresh

from . import mesh_transfer
from .pose_wrangler_bridge import PoseWranglerBridge


class CorrectiveBatchManager:

    # exists_policy
    SKIP = "skip"
    OVERWRITE = "overwrite"

    # route
    ROUTE_POSEWRANGLER = "posewrangler"   # PoseWrangler edit_blendshape 재사용 (솔버 자동 와이어)
    ROUTE_DIRECT = "direct"               # cmds.invertShape 직접 (이름만 짓고 와이어는 A00090 위임)

    def __init__(self, bridge=None):
        self.bridge = bridge or PoseWranglerBridge()

    # --------------------------------------------------
    # Target naming (A00090 rules_v01 convention)
    # --------------------------------------------------

    @staticmethod
    def solver_prefix(solver_name):
        """솔버 노드 이름 -> rules_v01 매핑 접두사.
        예: 'WRK_calf_l_UERBFSolver' -> 'calf_l',
            'ns:WRK_lowerarm_r_UERBFSolver' -> 'lowerarm_r'."""
        name = solver_name.split(":")[-1].split("|")[-1]
        if name.startswith("WRK_"):
            name = name[4:]
        for suffix in ("_UERBFSolverNode", "_UERBFSolver", "UERBFSolver"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        return name.rstrip("_")

    @classmethod
    def target_name(cls, solver_name, pose):
        """포즈 -> rules_v01 매핑 타겟 이름.

        - 'default' 포즈        -> '<prefix>_default'   (예: calf_l_default)
        - 이미 접두사를 포함한 포즈 -> 그대로            (예: calf_l_back_50)
        - 접두사 없는 포즈        -> '<prefix>_<pose>'   (예: back_50 -> calf_l_back_50)
        """
        prefix = cls.solver_prefix(solver_name)
        if pose == "default":
            return "{0}_default".format(prefix) if prefix else "default"
        if prefix and pose.startswith(prefix + "_"):
            return pose
        if prefix:
            return "{0}_{1}".format(prefix, pose)
        return pose

    # --------------------------------------------------
    # Batch
    # --------------------------------------------------

    def generate_batch(self, jobs, base_mesh, cache, *,
                        route=ROUTE_POSEWRANGLER, wire=True,
                        exists_policy=SKIP, skip_eps=0.0,
                        include_default=False, status_cb=None):
        """jobs: [(solver_node, solver_name, pose, frame), ...]

        반환: (성공 개수, 메시지). 행별 진행은 status_cb(index, text) 로 통지.
        """
        if not jobs:
            return (0, "[Warning] No poses to process.")

        ok, msg = self._validate_common(base_mesh, cache)
        if not ok:
            return (0, msg)

        # invertShape 플러그인 보장 (양 route 공통: Route A 도 내부에서 사용)
        if not cmds.pluginInfo("invertShape", q=True, loaded=True):
            try:
                cmds.loadPlugin("invertShape")
            except Exception:
                return (0, "[Error] invertShape plugin unavailable.")

        original_time = cmds.currentTime(q=True)
        done = 0

        with undo_chunk():
            with suspend_refresh():
                try:
                    for idx, (solver, solver_name, pose, frame) in enumerate(jobs):
                        try:
                            result = self._generate_one(
                                solver, solver_name, pose, frame, base_mesh, cache,
                                route=route, wire=wire,
                                exists_policy=exists_policy, skip_eps=skip_eps,
                                include_default=include_default)
                            if status_cb:
                                status_cb(idx, result)
                            if result.startswith("OK"):
                                done += 1
                        except Exception as exc:
                            if status_cb:
                                status_cb(idx, "ERROR: {0}".format(exc))
                finally:
                    # 처리한 모든 솔버를 default 포즈로 복원 + 타임 복원 (항상)
                    seen = set()
                    for solver, solver_name, _, _ in jobs:
                        if solver_name in seen:
                            continue
                        seen.add(solver_name)
                        try:
                            self.bridge.go_to_pose(solver, "default")
                        except Exception:
                            pass
                    cmds.currentTime(original_time, edit=True)

        return (done, "Generated {0}/{1} corrective(s).".format(done, len(jobs)))

    # --------------------------------------------------
    # One pose
    # --------------------------------------------------

    def _generate_one(self, solver, solver_name, pose, frame, base_mesh, cache, *,
                      route, wire, exists_policy, skip_eps, include_default=False):
        # default 포즈는 보통 무보정(identity)이라 기본 스킵하지만,
        # 사용자가 명시적으로 요청하면(include_default) 캐시 형상으로 타겟을 만든다.
        if pose == "default" and not include_default:
            return "SKIP: default pose"

        # 타겟 이름은 rules_v01 약속을 따른다 (default -> '<prefix>_default').
        tname = self.target_name(solver_name, pose)

        # 1) 캐시를 프레임에서 스냅샷 (abc 평가)
        cache_points = cache.points_at(frame)
        if len(cache_points) != mesh_transfer.topo_signature(base_mesh)[0]:
            return "ERROR: topology mismatch (cache {0} vs mesh {1})".format(
                len(cache_points), mesh_transfer.topo_signature(base_mesh)[0])

        # 2) 리그를 해당 포즈로 (base_mesh 의 skin 이 un-corrected 포즈 형상이 됨)
        self.bridge.go_to_pose(solver, pose)

        # 3) 무주름 스킵 (옵션)
        if skip_eps > 0.0:
            base_points = mesh_transfer.get_points(base_mesh, mesh_transfer.WORLD)
            worst = 0.0
            for i in range(len(cache_points)):
                d = (cache_points[i] - base_points[i]).length()
                if d > worst:
                    worst = d
            if worst < skip_eps:
                return "SKIP: no wrinkle (max delta {0:.4f} < {1})".format(worst, skip_eps)

        if route == self.ROUTE_DIRECT:
            return self._route_direct(solver, pose, tname, base_mesh, cache_points, wire)
        return self._route_posewrangler(solver, pose, tname, base_mesh, cache_points, exists_policy)

    # --------------------------------------------------
    # Route A : PoseWrangler edit_blendshape (솔버 자동 와이어)
    # --------------------------------------------------

    def _route_posewrangler(self, solver, pose, tname, base_mesh, cache_points, exists_policy):
        exists = self.bridge.has_target(solver, pose)
        if exists:
            if exists_policy == self.SKIP:
                return "SKIP: target exists"
            # overwrite: 기존 타겟 제거 후 재생성
            self.bridge.delete_blendshape(solver, pose)

        # 타겟 시드 생성(default 복제) + 솔버 와이어. 시드 메시 이름을 tname 으로 줘서
        # blendShape 타겟 별칭이 rules_v01 약속(예: calf_l_default)을 따르게 한다.
        # PoseWrangler create_blendshape 의 엄격한 skin 직결 체크('Target mesh is not skinned'
        # 오탐)를 피하려 체크 없는 안전 버전 사용. invertShape 는 히스토리로 skin 을 찾아 정상 동작.
        self.bridge.create_blendshape_safe(solver, pose, base_mesh, target_name=tname)

        # edit 진입 -> EDIT 메시에 캐시 형상 복사 -> edit 종료(invertShape + 재와이어)
        edit_mesh = self.bridge.edit_begin(solver, pose)
        if not edit_mesh or not cmds.objExists(edit_mesh):
            return "ERROR: could not enter edit mode (no EDIT mesh)"
        mesh_transfer.set_points(edit_mesh, cache_points, mesh_transfer.WORLD)
        self.bridge.edit_end(solver, pose)
        return "OK: corrective '{0}' wired".format(tname)

    # --------------------------------------------------
    # Route B : 직접 invertShape (이름만, 솔버 와이어는 A00090 위임)
    # --------------------------------------------------

    def _route_direct(self, solver, pose, tname, base_mesh, cache_points, wire):
        # base 복제(현재 포즈) -> 캐시 형상 주입 -> invertShape
        dup = cmds.duplicate(base_mesh, name=base_mesh.split("|")[-1] + "_tmpEdit")[0]
        try:
            mesh_transfer.set_points(dup, cache_points, mesh_transfer.WORLD)
            inv = cmds.invertShape(base_mesh, dup)
        finally:
            if cmds.objExists(dup):
                cmds.delete(dup)

        target = cmds.rename(inv, tname)  # 타겟 이름 = rules_v01 약속 (예: calf_l_default)

        # front-of-chain blendShape 에 타겟 추가 (솔버 연결은 하지 않음 -> A00090 가 와이어)
        bs = self._front_of_chain_blendshape(base_mesh)
        existing = cmds.listAttr(bs, multi=True, string="weight") or []
        next_idx = len(existing)
        cmds.blendShape(bs, edit=True, target=(base_mesh, next_idx, target, 1.0))
        if cmds.objExists(target):
            cmds.delete(target)
        return "OK: target '{0}' added (wire via A00090)".format(tname)

    def _front_of_chain_blendshape(self, base_mesh):
        history = cmds.listHistory(base_mesh, pruneDagObjects=True) or []
        for node in cmds.ls(history, type="blendShape") or []:
            return node
        return cmds.blendShape(base_mesh, frontOfChain=True,
                               name=base_mesh.split("|")[-1] + "_blendShape")[0]

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def _validate_common(self, base_mesh, cache):
        if not base_mesh or not cmds.objExists(base_mesh):
            return (False, "[Warning] Set a valid Garment Base Mesh.")
        # base 가 skin 돼 있어야 invertShape / create_blendshape 가 동작
        history = cmds.listHistory(base_mesh, pruneDagObjects=True) or []
        if not cmds.ls(history, type="skinCluster"):
            return (False, "[Warning] Base mesh has no skinCluster.")
        if cache.topo_signature() != mesh_transfer.topo_signature(base_mesh):
            return (False, "[Warning] Cache and base mesh topology differ "
                           "({0} vs {1}).".format(cache.topo_signature(),
                                                  mesh_transfer.topo_signature(base_mesh)))
        return (True, "")
