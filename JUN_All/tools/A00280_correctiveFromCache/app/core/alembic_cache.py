# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - Alembic 캐시 메시 프레임 평가 / 스냅샷 (UI 비의존)
#
# 후디니 클로스 시뮬 .abc 캐시 메시를 받아, 특정 프레임의 버텍스 위치를 읽는다.
# - 이미 임포트된 캐시 메시 노드(권장) 또는 .abc 파일 경로(AbcImport)를 받는다.
# - gpuCache 가 아니라 실제 polyMesh(AlembicNode.time 구동) 여야 버텍스를 읽을 수 있다.

import maya.cmds as cmds

from . import mesh_transfer


class AlembicCache:
    """캐시 메시 1개를 프레임별로 평가해 포인트 배열을 돌려준다."""

    def __init__(self, mesh):
        if not cmds.objExists(mesh):
            raise ValueError("Cache mesh '{0}' does not exist.".format(mesh))
        self.mesh = mesh

    # --------------------------------------------------
    # Construction
    # --------------------------------------------------

    @classmethod
    def from_file(cls, abc_path, namespace="A00280_abc"):
        """.abc 파일을 임포트하고 첫 메시를 캐시 대상으로 사용.
        여러 메시가 있으면 첫 번째를 쓰므로, 가능하면 메시 노드를 직접 지정할 것."""
        if not cmds.pluginInfo("AbcImport", q=True, loaded=True):
            cmds.loadPlugin("AbcImport")

        before = set(cmds.ls(type="mesh", long=True))
        cmds.AbcImport(abc_path, mode="import")
        after = set(cmds.ls(type="mesh", long=True))
        new_shapes = sorted(after - before)
        if not new_shapes:
            raise RuntimeError("No mesh imported from '{0}'.".format(abc_path))

        transforms = cmds.listRelatives(new_shapes[0], parent=True, fullPath=True) or new_shapes[:1]
        return cls(transforms[0])

    # --------------------------------------------------
    # Eval
    # --------------------------------------------------

    def points_at(self, frame, space=None):
        """주어진 프레임에서 캐시 메시의 버텍스 위치 배열(MPointArray, 기본 월드 공간).
        currentTime 변경이 시간 의존 노드를 dirty -> getPoints 풀에서 재평가된다."""
        cmds.currentTime(frame, edit=True)
        # abc 디포머가 lazy 할 수 있어 확실히 dirty 시킨 뒤 읽는다.
        try:
            cmds.dgdirty(self.mesh)
        except Exception:
            pass
        sp = mesh_transfer.WORLD if space is None else space
        return mesh_transfer.get_points(self.mesh, sp)

    def topo_signature(self):
        return mesh_transfer.topo_signature(self.mesh)
