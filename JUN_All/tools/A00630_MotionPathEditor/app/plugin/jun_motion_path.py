# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
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

import numpy as np

import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.cmds as cmds
import maya.api.OpenMayaUI as omui

from tools.A00630_MotionPathEditor.app.core import draw_bridge
from tools.A00630_MotionPathEditor.app.core import gizmo as gz

maya_useNewAPI = True

NODE_NAME = "junMotionPath"
NODE_ID = om.MTypeId(0x0007F630)            # 마야가 로컬용으로 비워 둔 범위 (0x0007F000 ~ 0x0007FFFF)
CLASSIFICATION = "drawdb/geometry/junMotionPath"
REGISTRANT = "junMotionPathDrawOverride"
COMMAND_NAME = "junMotionPathSetKeys"
DIRTY_COMMAND_NAME = "junMotionPathDirty"
VERSION_COMMAND_NAME = "junMotionPathVersion"
COMMANDS = (COMMAND_NAME, DIRTY_COMMAND_NAME, VERSION_COMMAND_NAME)

#: 플러그인 버전 (v01.07). **이 파일을 고치면 올린다** - 마야는 이미 읽힌 플러그인을 다시 읽지 않으므로, 툴(draw_nodes.ensure_plugin)이
#: 읽힌 코드의 버전과 이 값을 비교해 다르면 다시 읽는다. v01.00~02 의 플러그인은 "1.0" 이었다(junMotionPathDirty · ghost 그리기 없음).
#: 읽힌 버전은 **명령 junMotionPathVersion 으로 묻는다** - `pluginInfo -q -version` 은 같은 경로에서 다시 읽어도 처음 읽은 값을 계속
#: 돌려준다(실측: 새 코드인데 "1.0") → v01.07 첫 판이 교체 뒤에도 "옛것" 으로 보고 툴 창을 못 열었다.
PLUGIN_VERSION = "2.0"          # 1.6 = v01.09 폴오프 색 · 고른 프레임 점 · HUD 글자 / 1.7 = v01.10 선을 화면 2D 로(메시에 안 가린다)
                                # 1.8 = v01.11 매니퓰레이터 (draw_bridge.GIZMO, core/gizmo) / 1.9 = v01.12 기즈모 굵기 1.5 배
                                # 2.0 = v01.14 기즈모 호버 = 굵게


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
_FALL_TEXT_COLOR = om.MColor((1.0, 0.85, 0.3, 1.0))


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


def screen_strips(points, view_proj, width, height):
    """(N,3) 월드 점 → 화면 픽셀 선 조각들 [(k,2) 배열] (v01.10).

    선은 **2D 로** 그린다: 마야 2024 VP2 는 beginDrawInXray 안에서도 3D 선(lineStrip · mesh 선)을 메시 뒤로 가린다
    (GUI 실측 2회 - 점만 x-ray 가 된다). 화면 좌표 선(line2d · mesh2d)은 박스 선택 사각형처럼 늘 위에 보인다.
    카메라 뒤(w <= 0)로 가는 점에서 선을 끊는다. view_proj = 행 벡터 4x4 (picking.project 와 같은 규약).
    """
    P = np.asarray(points, dtype="float64").reshape(-1, 3)
    if len(P) < 2:
        return []
    clip = np.hstack([P, np.ones((len(P), 1))]) @ np.asarray(view_proj, dtype="float64")
    w = clip[:, 3]
    front = w > 1e-6
    safe = np.where(front, w, 1.0)
    px = np.empty((len(P), 2))
    px[:, 0] = (clip[:, 0] / safe * 0.5 + 0.5) * width
    px[:, 1] = (clip[:, 1] / safe * 0.5 + 0.5) * height
    out = []
    i, n = 0, len(P)
    while i < n:
        if not front[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and front[j + 1]:
            j += 1
        if j > i:
            out.append(px[i:j + 1])
        i = j + 1
    return out


def _view_of(frame_context):
    """(view_proj 4x4 numpy, 너비, 높이) - 지금 그리는 뷰."""
    m = frame_context.getMatrix(omr.MFrameContext.kViewProjMtx)
    vp = np.array([[m.getElement(r, c) for c in range(4)] for r in range(4)])
    _x, _y, width, height = frame_context.getViewportDimensions()
    return vp, width, height


def _line2d(dm, strip):
    """화면 선 조각 하나. mesh2d 한 번(빠름), 안 되면 line2d 로."""
    arr = om.MPointArray([om.MPoint(x, y) for x, y in strip.tolist()])     # 7,000 점 약 6 ms (append 루프 9 ms)
    try:
        dm.mesh2d(omr.MUIDrawManager.kLineStrip, arr)
    except Exception:                                      # noqa: BLE001
        for a, b in zip(list(arr)[:-1], list(arr)[1:]):
            dm.line2d(a, b)


class _Data(om.MUserData):
    def __init__(self):
        om.MUserData.__init__(self, False)
        self.payload = None
        self.hud = None
        self.text = None
        self.gizmo = None


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
        mine = draw_bridge.HUD.get("owner") == key
        data.hud = draw_bridge.HUD.get("box") if mine else None
        data.text = draw_bridge.HUD.get("text") if mine else None
        data.gizmo = dict(draw_bridge.GIZMO) if draw_bridge.GIZMO.get("owner") == key else None
        return data

    def addUIDrawables(self, obj_path, dm, frame_context, data):
        p = getattr(data, "payload", None)
        if p:
            self._draw_path(dm, p)
            try:
                self._draw_lines(dm, p, *_view_of(frame_context))
            except Exception:                              # noqa: BLE001 - 선이 실패해도 점은 그린다
                pass
        giz = getattr(data, "gizmo", None)
        if giz:
            try:
                self._draw_gizmo(dm, giz, *_view_of(frame_context))
            except Exception:                              # noqa: BLE001
                pass
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
        text = getattr(data, "text", None)
        if text:                                            # v01.09 폴오프 반경 (커서 옆)
            x, y, label = text
            dm.beginDrawable(omr.MUIDrawManager.kNonSelectable)
            dm.setColor(_FALL_TEXT_COLOR)
            dm.setFontSize(omr.MUIDrawManager.kDefaultFontSize)
            dm.text2d(om.MPoint(x + 14, y + 10), label, omr.MUIDrawManager.kLeft)
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
        # 선(경로 · 폴오프 · 미리보기 원래 경로)은 _draw_lines 가 화면 2D 로 그린다 (v01.10)
        if len(p.get("dots", ())):
            dm.setColor(line_color)
            dm.setPointSize(float(p.get("dot_size", 4.0)))
            dm.points(p["dots"], False)
        fall = p.get("fall_dots")
        if fall is not None and len(fall):                  # v01.09 폴오프 점 - 점마다 가중치 색 (mesh kPoints 는 x-ray 됨)
            dm.setPointSize(float(p.get("dot_size", 4.0)) + 3.0)
            dm.mesh(omr.MUIDrawManager.kPoints, fall, None, p["fall_colors"])
        key_size = float(p.get("key_size", 9.0))
        if len(p.get("keys", ())):
            dm.setColor(_LOCK_COLOR if locked else _KEY_COLOR)
            dm.setPointSize(key_size)
            dm.points(p["keys"], False)
        if len(p.get("selected", ())):
            dm.setColor(_SEL_COLOR)
            dm.setPointSize(key_size + 2.0)
            dm.points(p["selected"], False)
        if len(p.get("selected_dots", ())):                # v01.09 고른 프레임 점
            dm.setColor(_SEL_COLOR)
            dm.setPointSize(float(p.get("dot_size", 4.0)) + 5.0)
            dm.points(p["selected_dots"], False)
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


    @staticmethod
    def _draw_lines(dm, p, view_proj, width, height):
        """선 세 가지를 화면 2D 로 (v01.10 - 3D 선은 x-ray 안에서도 메시에 가려진다)."""
        locked = p.get("locked", False)
        line_color = _LOCK_COLOR if locked else p.get("color", _KEY_COLOR)
        lw = float(p.get("line_width", 2.0))
        dm.beginDrawable(omr.MUIDrawManager.kNonSelectable)
        ghost = p.get("ghost")
        if ghost is not None and len(ghost) > 1:            # 그래프 Smooth 미리보기 · 끄는 동안: 원래 경로 (v01.04)
            dm.setColor(_GHOST_COLOR)
            dm.setLineWidth(1.0)
            dm.setLineStyle(omr.MUIDrawManager.kDashed)
            for strip in screen_strips(ghost, view_proj, width, height):
                _line2d(dm, strip)
            dm.setLineStyle(omr.MUIDrawManager.kSolid)
        line = p.get("line")
        if line is not None and len(line) > 1:
            dm.setColor(line_color)
            dm.setLineWidth(lw)
            for strip in screen_strips(line, view_proj, width, height):
                _line2d(dm, strip)
        for color, pts in p.get("fall_lines") or ():         # v01.09 폴오프 범위 - 색 단계마다
            dm.setColor(color)
            dm.setLineWidth(lw + 2.0)
            for strip in screen_strips(pts, view_proj, width, height):
                _line2d(dm, strip)
        dm.endDrawable()


    @staticmethod
    def _draw_gizmo(dm, g, view_proj, width, height):
        """매니퓰레이터 (v01.11) - 화면 2D 로(경로 선과 같은 이유), 크기는 화면 픽셀 고정. 잡은 부분은 노랑."""
        pivot = np.asarray(g["pivot"], dtype="float64")
        axes = np.asarray(g["axes"], dtype="float64")
        vdir = gz.view_dir(view_proj)
        length = gz.SIZE_PX * gz.world_per_px(pivot, view_proj, width, height, vdir)
        active = g.get("active")
        hover = g.get("hover")
        dm.beginDrawable(omr.MUIDrawManager.kNonSelectable)
        dm.setLineStyle(omr.MUIDrawManager.kSolid)
        for name, line in gz.geometry(pivot, axes, g.get("mode", gz.MODE_MOVE), length, vdir):
            rgb = gz.ACTIVE_COLOR if name == active else gz.COLORS.get(name, (1.0, 1.0, 1.0))
            dm.setColor(om.MColor(tuple(rgb) + (1.0,)))
            dm.setLineWidth(gz.ACTIVE_WIDTH if name == active else gz.HOVER_WIDTH if name == hover else gz.LINE_WIDTH)
            for strip in screen_strips(line, view_proj, width, height):
                _line2d(dm, strip)
            if name in ("x", "y", "z"):                     # 화살표 머리 (화면에서)
                px, front = gz.project(line[-2:], view_proj, width, height)
                if front.all():
                    d = px[1] - px[0]
                    n = np.linalg.norm(d)
                    if n > 1e-6:
                        d /= n
                        side = np.array([-d[1], d[0]])
                        tip = px[1]
                        for s in (1.0, -1.0):
                            q = tip - d * gz.HEAD_LEN + side * gz.HEAD_HALF * s
                            dm.line2d(om.MPoint(float(tip[0]), float(tip[1])), om.MPoint(float(q[0]), float(q[1])))
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


class JunMotionPathVersionCmd(om.MPxCommand):
    """읽혀 있는 플러그인 코드의 버전 (v01.07) - 툴이 옛 플러그인인지 판단한다. undo 큐에 남지 않는다."""

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def creator():
        return JunMotionPathVersionCmd()

    def doIt(self, args):
        self.setResult(PLUGIN_VERSION)

    def isUndoable(self):
        return False


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Ji Hun Park", PLUGIN_VERSION, "Any")
    plugin.registerNode(NODE_NAME, NODE_ID, JunMotionPathNode.creator, JunMotionPathNode.initialize,
                        om.MPxNode.kLocatorNode, CLASSIFICATION)
    omr.MDrawRegistry.registerDrawOverrideCreator(CLASSIFICATION, REGISTRANT, JunMotionPathDrawOverride.creator)
    plugin.registerCommand(COMMAND_NAME, JunMotionPathSetKeysCmd.creator)
    plugin.registerCommand(DIRTY_COMMAND_NAME, JunMotionPathDirtyCmd.creator)
    plugin.registerCommand(VERSION_COMMAND_NAME, JunMotionPathVersionCmd.creator)


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    plugin.deregisterCommand(VERSION_COMMAND_NAME)
    plugin.deregisterCommand(DIRTY_COMMAND_NAME)
    plugin.deregisterCommand(COMMAND_NAME)
    omr.MDrawRegistry.deregisterDrawOverrideCreator(CLASSIFICATION, REGISTRANT)
    plugin.deregisterNode(NODE_ID)
