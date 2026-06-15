# -*- coding: utf-8 -*-
"""
undo_cmd - Undo 가능 벌크 setPoints 커맨드(OpenMaya 2.0 플러그인).

`MFnMesh.setPoints()` 는 빠르지만 기본적으로 Undo 에 안 잡힌다.
이 커맨드는 doIt 에서 기존 좌표(old)를 백업하고 새 좌표(new)를 적용하며,
undoIt/redoIt 로 Maya 의 Undo 큐에 정상 편입된다(Ctrl+Z / Ctrl+Y).

페이로드는 undo_bridge.PENDING 으로 전달받는다(커맨드 인자로 대형 배열을
넘기지 않기 위함). bridge 는 일반 import 경로로만 접근해 모듈 단일성을 보장한다.

Maya 2023(Python 3.9 / API 2.0)에서 동작한다.
플러그인 로드: cmds.loadPlugin(".../core/undo_cmd.py")
"""

import maya.api.OpenMaya as om


# OpenMaya 2.0 플러그인 선언(필수).
maya_useNewAPI = True


# bridge 는 반드시 canonical 경로(tools.A00180_abSymMesh.core.undo_bridge)로 import 해야
# 툴 코드가 쓰는 모듈과 동일 객체를 공유한다(PENDING 전달).
# 이 플러그인은 항상 실행 중인 툴(mesh_io.ensure_undo_plugin)에서 로드되므로
# 그 시점에 JUN_All 이 이미 sys.path 에 있어 아래 import 가 성립한다.
# (loadPlugin 으로 로드된 .py 에는 __file__ 이 정의되지 않으므로 경로 계산을 쓰지 않는다.)
from tools.A00180_abSymMesh.app.core import undo_bridge


def _mfn_mesh(name):
    sel = om.MSelectionList()
    sel.add(name)
    dag = sel.getDagPath(0)
    if dag.apiType() == om.MFn.kTransform:
        dag.extendToShape()
    return om.MFnMesh(dag)


class AbSymSetPointsCmd(om.MPxCommand):

    kPluginCmdName = "abSymSetPoints"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._mesh = None
        self._space = om.MSpace.kObject
        self._old = None   # MPointArray
        self._new = None   # MPointArray
        self._applied = False

    @staticmethod
    def creator():
        return AbSymSetPointsCmd()

    def doIt(self, args):
        payload = undo_bridge.take()
        if not payload:
            # staging 없이 호출됨 -> 아무 것도 하지 않음(Undo 대상 아님).
            return

        self._mesh = payload["mesh"]
        self._space = om.MSpace.kWorld if payload["world"] else om.MSpace.kObject

        fn = _mfn_mesh(self._mesh)

        # old(현재) 좌표 백업.
        self._old = fn.getPoints(self._space)

        # new 좌표 배열 구성.
        new_arr = om.MPointArray()
        for (x, y, z) in payload["points"]:
            new_arr.append(om.MPoint(x, y, z))
        self._new = new_arr

        self._applied = True
        self.redoIt()

    def redoIt(self):
        if not self._applied:
            return
        fn = _mfn_mesh(self._mesh)
        fn.setPoints(self._new, self._space)

    def undoIt(self):
        if not self._applied:
            return
        fn = _mfn_mesh(self._mesh)
        fn.setPoints(self._old, self._space)

    def isUndoable(self):
        return self._applied


def initializePlugin(plugin):
    fn = om.MFnPlugin(plugin, "Ji Hun Park", "1.0", "Any")
    fn.registerCommand(AbSymSetPointsCmd.kPluginCmdName, AbSymSetPointsCmd.creator)


def uninitializePlugin(plugin):
    fn = om.MFnPlugin(plugin)
    fn.deregisterCommand(AbSymSetPointsCmd.kPluginCmdName)
