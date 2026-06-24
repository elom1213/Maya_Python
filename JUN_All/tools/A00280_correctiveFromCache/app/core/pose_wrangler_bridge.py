# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - Epic PoseWrangler(RBF) 래핑 브리지 (UI 비의존)
#
# PoseDriverConnect(epic_pose_wrangler) v2 의 UERBFAPI / RBFNode 를 얇게 감싼다.
# - UERBFAPI(view=False) 로 헤드리스 생성 (PoseWrangler 자체 Qt 창이 우리 PySide 창과 충돌 방지).
# - 솔버/포즈 목록, 포즈->프레임 매핑, go_to_pose, create/edit/delete/mirror blendshape 를 노출.
# 모든 PoseWrangler 호출은 여기로 모은다 (core/ui 분리 + 의존성 격리).

import maya.cmds as cmds


class PoseWranglerBridge:
    """epic_pose_wrangler v2 UERBFAPI 래퍼. PoseWrangler 미설치 시 명확한 에러."""

    def __init__(self):
        self._api = None

    # --------------------------------------------------
    # API lifecycle
    # --------------------------------------------------

    def api(self):
        """UERBFAPI(view=False) 싱글턴. import 실패 시 RuntimeError."""
        if self._api is not None:
            return self._api
        try:
            from epic_pose_wrangler.v2 import main as ue_main
        except Exception:
            raise RuntimeError(
                "PoseWrangler (epic_pose_wrangler) not importable. "
                "Install/enable the PoseDriverConnect module in Maya.")
        self._api = ue_main.UERBFAPI(view=False)
        return self._api

    # --------------------------------------------------
    # Solver / pose queries
    # --------------------------------------------------

    def list_solver_names(self):
        """씬의 RBF 솔버 이름 목록."""
        names = []
        for solver in self.api().rbf_solvers:
            try:
                names.append(solver.name)
            except Exception:
                names.append(str(solver))
        return names

    def get_solver(self, name):
        """이름으로 RBFNode 해석 (없으면 None)."""
        return self.api().get_rbf_solver_by_name(name)

    def pose_names(self, solver):
        """솔버의 포즈 이름 목록 (poses() 순서 = bake 순서)."""
        return list(solver.poses().keys())

    def driver_joints(self, solver):
        try:
            return list(solver.drivers())
        except Exception:
            return []

    def frame_map(self, solver, start_frame, step=1):
        """포즈 -> 프레임 = start + index x step.

        step=1 이면 bake_poses_to_timeline 과 동일. abc 캐시가 포즈당 N 프레임 간격으로
        정착(settle)되도록 시뮬됐다면 step 을 그 간격(예: 60)으로 둬야 미정착 프레임을
        피하고 올바른 형상을 샘플링한다. (알고리즘은 go_to_pose 로 직접 포즈하므로 frame 은
        오직 abc 샘플링 위치로만 쓰임 — 타임라인 베이크와 무관.)
        """
        step = int(step) or 1
        return {name: int(start_frame) + i * step
                for i, name in enumerate(self.pose_names(solver))}

    def has_target(self, solver, pose):
        """해당 포즈에 코렉티브 타겟이 이미 있으면 True."""
        try:
            data = solver.get_blendshape_data_for_pose(pose)
            return bool(data)
        except Exception:
            return False

    # --------------------------------------------------
    # Pose / blendshape ops
    # --------------------------------------------------

    def go_to_pose(self, solver, pose):
        self.api().go_to_pose(pose, solver=solver)

    def create_blendshape(self, solver, pose, base_mesh):
        """default 포즈 복제로 front-of-chain 타겟 생성 + 솔버 출력 와이어."""
        return self.api().create_blendshape(pose, mesh_name=base_mesh, edit=False, solver=solver)

    def create_blendshape_safe(self, solver, pose, base_mesh, target_name=None):
        """RBFNode.create_blendshape 와 동일하되 PoseWrangler 의 엄격한 skin 체크를 건너뛴다.

        PoseWrangler create_blendshape(api.py:1165)은 `listConnections(visibleShape, type='skinCluster')`
        로 skin 여부를 보는데, 이는 **skinCluster 가 노출 셰이프에 직접 연결돼 있어야만** 통과한다.
        skinCluster 가 디포머 체인의 마지막이 아니거나 중간 노드가 끼어 있으면(의상 메시에서 흔함)
        실제로는 스킨돼 있어도 'Target mesh is not skinned' 오탐이 난다.
        invertShape(=edit_blendshape) 는 히스토리로 skin 을 찾으므로 정상 동작하니, 이 시드 생성만
        체크 없이 직접 수행한다. (create_blendshape 본체 1172~1182 와 동일한 절차)

        target_name 을 주면 시드 메시를 그 이름으로 만들어 blendShape 타겟 별칭이
        rules_v01 약속(예: calf_l_default)을 따르게 한다.
        """
        solver.go_to_pose("default")
        try:
            solver.isolate_blendshape(pose_name=pose, isolate=True)
        except Exception:
            pass
        if not target_name:
            short = base_mesh.split("|")[-1].split(":")[-1]
            target_name = "{0}_{1}_seed".format(short, pose)
        dup = cmds.duplicate(base_mesh, name=target_name)[0]
        solver.add_existing_blendshape(pose, dup, base_mesh)
        return dup

    def edit_begin(self, solver, pose):
        """edit 모드 진입: 해당 포즈로 가서 <name>_EDIT 복제를 만든다.
        반환: EDIT 메시 이름 (API 반환값이 없으면 현재 선택에서 추정)."""
        ret = self.api().edit_blendshape(pose, edit=True, solver=solver)
        if ret:
            return ret
        sel = cmds.ls(sl=True, long=False) or []
        return sel[0] if sel else None

    def edit_end(self, solver, pose):
        """edit 모드 종료: invertShape 로 bind 델타 변환 + 솔버 출력 재와이어."""
        return self.api().edit_blendshape(pose, edit=False, solver=solver)

    def delete_blendshape(self, solver, pose):
        try:
            self.api().delete_blendshape(pose, solver=solver)
        except Exception:
            pass

    # --------------------------------------------------
    # Mirror
    # --------------------------------------------------

    def mirror_mapping(self):
        return self.api().mirror_mapping

    def mirror_blendshape(self, solver, pose):
        """해당 포즈의 코렉티브를 반대쪽 솔버로 미러."""
        solver.mirror_blendshape(pose, self.mirror_mapping())
