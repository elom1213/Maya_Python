# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - 코렉티브 L/R 미러 (옵션, UI 비의존)
#
# 한쪽(예: 왼쪽) 솔버의 코렉티브를 PoseWrangler mirror_blendshape 로 반대쪽 솔버에 복제.
# 작업량을 절반으로 줄이는 선택 단계(기본 off, 수동 선택).

from Framework.core.maya_undo import undo_chunk

from .pose_wrangler_bridge import PoseWranglerBridge


class MirrorManager:

    def __init__(self, bridge=None):
        self.bridge = bridge or PoseWranglerBridge()

    def mirror(self, jobs, status_cb=None):
        """jobs: [(solver_node, solver_name, pose), ...] 선택된 (솔버, 포즈) 를 미러.

        반환: (성공 개수, 메시지).
        """
        if not jobs:
            return (0, "[Warning] No poses selected to mirror.")

        done = 0
        with undo_chunk():
            for idx, (solver, solver_name, pose) in enumerate(jobs):
                try:
                    self.bridge.mirror_blendshape(solver, pose)
                    if status_cb:
                        status_cb(idx, "OK: mirrored")
                    done += 1
                except Exception as exc:
                    if status_cb:
                        status_cb(idx, "ERROR: {0}".format(exc))

        return (done, "Mirrored {0}/{1} corrective(s).".format(done, len(jobs)))
