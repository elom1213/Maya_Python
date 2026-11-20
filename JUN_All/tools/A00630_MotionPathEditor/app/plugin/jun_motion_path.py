# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 플러그인 (OpenMaya 2.0): 그리기 노드 + VP2 draw override + undo 명령
"""
cmds.loadPlugin(<이 파일>) 로 읽는다 (툴의 plugin_loader 가 한다).

- 노드 `junMotionPath` (MPxLocatorNode) : 경로 하나에 하나. 속성 `pathKey`(string) 로 draw_bridge.DATA 의 어느 경로를 그릴지 고른다.
  선택되지 않는다(그릴 때 kNonSelectable) · 경계 상자 없음(늘 그린다) · 툴이 doNotWrite 로 만들어 씬에 저장되지 않는다.
- `junMotionPathDrawOverride` : 그리기 데이터는 툴이 **바뀔 때만** MPointArray 로 만들어 draw_bridge 에 둔다 - 여기서는 읽어서 그리기만.
  x-ray 로 그려 메시에 가려지지 않는다.
- 명령 `junMotionPathSetKeys` : 드래그 동안 MAnimCurveChange 에 쌓인 키 변경을 **undo 한 번**으로 마야 큐에 넣는다.
  변경은 이미 적용돼 있으므로 doIt 은 기록만 받고, undoIt / redoIt 이 그 기록을 되돌리고 다시 한다(A00180 abSymSetPoints 와 같은 구조).

`__file__` 이 없으므로(메모 maya-loadplugin-no-file) 경로 계산을 하지 않고, draw_bridge 는 정식 경로로 import 한다.
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.cmds as cmds
import maya.api.OpenMayaUI as omui

from tools.A00630_MotionPathEditor.app.core import draw_bridge

maya_useNewAPI = True

NODE_NAME = "junMotionPath"
NODE_ID = om.MTypeId(0x0007F630)            # 마야가 로컬용으로 비워 둔 범위 (0x0007F000 ~ 0x0007FFFF)
CLASSIFICATION = "drawdb/geometry/junMotionPath"
REGISTRANT = "junMotionPathDrawOverride"
COMMAND_NAME = "junMotionPathSetKeys"
DIRTY_COMMAND_NAME = "junMotionPathDirty"


def _dirty(nodes):
    """다시 계산하라고 표시 (v01.03). 레이어에 새로 만든 커브가 undo 로 지워진 뒤 마야가 블렌드 체인 아래쪽을
    다시 계산하지 않아 오브젝트가 낡은 위치에 남았다(시간을 옮겨도) - 대상 노드 + 블렌드 노드를 dgdirty 한다."""
    alive = [n for n in nodes if cmds.objExists(n)]
    if alive:
        cmds.dgdirty(alive)

_KEY_COLOR = om.MColor((0.95, 0.95, 0.95, 1.0))
_SEL_COLOR = om.MColor((1.0, 0.75, 0.1, 1.0))
_CUR_COLOR = om.MColor((1.0, 0.25, 0.25, 1.0))
_LOCK_COLOR = om.MColor((0.45, 0.45, 0.45, 1.0))
_HUD_COLOR = om.MColor((1.0, 1.0, 1.0, 0.8))
_GHOST_COLOR = om.MColor((0.55, 0.55, 0.55, 0.9))


class JunMotionPathNode(omui.MPxLocatorNode):
    aPathKey = None

    def __init__(self):
        omui.MPxLocatorNode.__init__(self)

    @staticmethod
    def creator():
        return JunMotionPathNode()

    @staticmethod
    def initialize():
        typed = om.MFnTypedAttribute()
        JunMotionPathNode.aPathKey = typed.create("pathKey", "pk", om.MFnData.kString)
        typed.storable = False
        JunMotionPathNode.addAttribute(JunMotionPathNode.aPathKey)

    def isBounded(self):
        return False


class _Data(om.MUserData):
    def __init__(self):
        om.MUserData.__init__(self, False)
        self.payload = None
        self.hud = None


class JunMotionPathDrawOverride(omr.MPxDrawOverride):

    @staticmethod
    def creator(obj):
        return JunMotionPathDrawOverride(obj)

    def __init__(self, obj):
        # isAlwaysDirty=True : 다시 그릴 때마다 prepareForDraw - 툴은 데이터를 바꾸고 뷰를 refresh 만 하면 된다
        omr.MPxDrawOverride.__init__(self, obj, None, True)

    def supportedDrawAPIs(self):
        return omr.MRenderer.kAllDevices

    def isBounded(self, obj_path, camera_path):
        return False

    def boundingBox(self, obj_path, camera_path):
        return om.MBoundingBox()

    def hasUIDrawables(self):
        return True

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        data = old_data if isinstance(old_data, _Data) else _Data()
        key = om.MFnDependencyNode(obj_path.node()).findPlug("pathKey", False).asString()
        data.payload = draw_bridge.DATA.get(key)
        data.hud = draw_bridge.HUD.get("box") if draw_bridge.HUD.get("owner") == key else None
        return data

    def addUIDrawables(self, obj_path, dm, frame_context, data):
        p = getattr(data, "payload", None)
        if p:
            self._draw_path(dm, p)
        box = getattr(data, "hud", None)
        if box:
            x0, y0, x1, y1 = box
            dm.beginDrawable(omr.MUIDrawManager.kNonSelectable)
            dm.setColor(_HUD_COLOR)
            dm.setLineWidth(1.0)
            dm.setLineStyle(omr.MUIDrawManager.kDashed)
            corners = [om.MPoint(x0, y0), om.MPoint(x1, y0), om.MPoint(x1, y1), om.MPoint(x0, y1)]
            for a, b in zip(corners, corners[1:] + corners[:1]):
                dm.line2d(a, b)
            dm.endDrawable()

    @staticmethod
    def _draw_path(dm, p):
        xray = hasattr(dm, "beginDrawInXray")
        dm.beginDrawable(omr.MUIDrawManager.kNonSelectable)
        if xray:
            dm.beginDrawInXray()
        dm.setDepthPriority(5)
        locked = p.get("locked", False)
        line_color = _LOCK_COLOR if locked else p.get("color", _KEY_COLOR)
        ghost = p.get("ghost")
        if ghost is not None and len(ghost) > 1:            # 그래프 Smooth 미리보기: 원래 경로 (v01.04)
            dm.setColor(_GHOST_COLOR)
            dm.setLineWidth(1.0)
            dm.setLineStyle(omr.MUIDrawManager.kDashed)
            dm.lineStrip(ghost, False)
            dm.setLineStyle(omr.MUIDrawManager.kSolid)
        if len(p.get("line", ())) > 1:
            dm.setColor(line_color)
            dm.setLineWidth(float(p.get("line_width", 2.0)))
            dm.lineStrip(p["line"], False)
        if len(p.get("dots", ())):
            dm.setColor(line_color)
            dm.setPointSize(float(p.get("dot_size", 4.0)))
            dm.points(p["dots"], False)
        key_size = float(p.get("key_size", 9.0))
        if len(p.get("keys", ())):
            dm.setColor(_LOCK_COLOR if locked else _KEY_COLOR)
            dm.setPointSize(key_size)
            dm.points(p["keys"], False)
        if len(p.get("selected", ())):
            dm.setColor(_SEL_COLOR)
            dm.setPointSize(key_size + 2.0)
            dm.points(p["selected"], False)
        if len(p.get("current", ())):
            dm.setColor(_CUR_COLOR)
            dm.setPointSize(key_size * 0.8)
            dm.points(p["current"], False)
        labels = p.get("labels") or ()
        if labels:
            dm.setColor(_KEY_COLOR)
            for point, text in labels:
                dm.text(point, text, omr.MUIDrawManager.kLeft)
        if xray:
            dm.endDrawInXray()
        dm.endDrawable()


class JunMotionPathSetKeysCmd(om.MPxCommand):
    """드래그 동안 쌓인 MAnimCurveChange 를 undo 한 번으로."""

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._change = None
        self._nodes = []

    @staticmethod
    def creator():
        return JunMotionPathSetKeysCmd()

    def doIt(self, args):
        # 변경은 드래그 동안 이미 적용됐다 - 기록만 받는다
        self._change, self._nodes = draw_bridge.take()

    def redoIt(self):
        if self._change is not None:
            self._change.redoIt()
            _dirty(self._nodes)

    def undoIt(self):
        if self._change is not None:
            self._change.undoIt()
            _dirty(self._nodes)

    def isUndoable(self):
        return self._change is not None


class JunMotionPathDirtyCmd(om.MPxCommand):
    """드래그 undo 묶음의 **맨 앞**에 넣는 표시 명령 - undo 때 가장 마지막에 되돌려지며 대상 · 블렌드 노드를 다시 계산하게 한다."""

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._nodes = []

    @staticmethod
    def creator():
        return JunMotionPathDirtyCmd()

    def doIt(self, args):
        self._nodes = draw_bridge.take_dirty()

    def redoIt(self):
        _dirty(self._nodes)

    def undoIt(self):
        _dirty(self._nodes)

    def isUndoable(self):
        return bool(self._nodes)


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Ji Hun Park", "1.0", "Any")
    plugin.registerNode(NODE_NAME, NODE_ID, JunMotionPathNode.creator, JunMotionPathNode.initialize,
                        om.MPxNode.kLocatorNode, CLASSIFICATION)
    omr.MDrawRegistry.registerDrawOverrideCreator(CLASSIFICATION, REGISTRANT, JunMotionPathDrawOverride.creator)
    plugin.registerCommand(COMMAND_NAME, JunMotionPathSetKeysCmd.creator)
    plugin.registerCommand(DIRTY_COMMAND_NAME, JunMotionPathDirtyCmd.creator)


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    plugin.deregisterCommand(DIRTY_COMMAND_NAME)
    plugin.deregisterCommand(COMMAND_NAME)
    omr.MDrawRegistry.deregisterDrawOverrideCreator(CLASSIFICATION, REGISTRANT)
    plugin.deregisterNode(NODE_ID)
