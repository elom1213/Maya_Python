# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - G0-1 실측용 임시 플러그인 (매니퓰레이터 · 폴오프 계획서 §4 G0-1). 툴 본체와 무관.
# MUIDrawManager.mesh(kPoints / kLineStrip) 에 점마다 색을 주면 VP2 · x-ray 에서 점마다 다른 색으로 보이는지 본다.
# 노드 ID 는 툴(0x0007F630)과 겹치지 않게 0x0007F631. g0_gui_probe.start() 가 읽고 stop() 이 내린다.
import math

import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.api.OpenMayaUI as omui

maya_useNewAPI = True

NODE_NAME = "junMotionPathProbe"
NODE_ID = om.MTypeId(0x0007F631)
CLASSIFICATION = "drawdb/geometry/junMotionPathProbe"
REGISTRANT = "junMotionPathProbeOverride"
N = 60


def falloff_color(w):
    """계획서 §3-2 색표: 1 노랑 → 0.5 주황 → 0 빨강 → 어두운 빨강."""
    stops = ((0.0, (0.35, 0.05, 0.05)), (0.15, (0.85, 0.1, 0.05)), (0.5, (1.0, 0.5, 0.05)), (1.0, (1.0, 0.95, 0.2)))
    for (w0, c0), (w1, c1) in zip(stops, stops[1:]):
        if w <= w1:
            k = (w - w0) / (w1 - w0)
            return om.MColor(tuple(a + (b - a) * k for a, b in zip(c0, c1)) + (1.0,))
    return om.MColor(stops[-1][1] + (1.0,))


def _row(y):
    pts, cols = om.MPointArray(), om.MColorArray()
    for i in range(N):
        x = -6.0 + 12.0 * i / (N - 1)
        pts.append(om.MPoint(x, y + math.sin(i * 0.25) * 0.4, 0.0))
        w = max(0.0, 1.0 - abs(i - N // 2) / 20.0)
        cols.append(falloff_color(w))
    return pts, cols


class ProbeNode(omui.MPxLocatorNode):
    @staticmethod
    def creator():
        return ProbeNode()

    @staticmethod
    def initialize():
        pass

    def isBounded(self):
        return False


class ProbeOverride(omr.MPxDrawOverride):
    @staticmethod
    def creator(obj):
        return ProbeOverride(obj)

    def __init__(self, obj):
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
        return None

    def addUIDrawables(self, obj_path, dm, frame_context, data):
        dm.beginDrawable(omr.MUIDrawManager.kNonSelectable)
        xray = hasattr(dm, "beginDrawInXray")
        if xray:
            dm.beginDrawInXray()
        dm.setDepthPriority(5)
        # 줄 1 (y=0): mesh(kPoints) + 점마다 색
        pts, cols = _row(0.0)
        dm.setPointSize(10.0)
        dm.mesh(omr.MUIDrawManager.kPoints, pts, None, cols)
        # 줄 2 (y=2): mesh(kLineStrip) + 점마다 색
        pts, cols = _row(2.0)
        dm.setLineWidth(4.0)
        dm.mesh(omr.MUIDrawManager.kLineStrip, pts, None, cols)
        # 줄 3 (y=4): 비교용 - 색마다 points() 따로 (안전망 방식)
        pts, cols = _row(4.0)
        for i in range(N):
            dm.setColor(cols[i])
            one = om.MPointArray()
            one.append(pts[i])
            dm.points(one, False)
        dm.text(om.MPoint(-6.5, 0.0, 0.0), "1 mesh kPoints", omr.MUIDrawManager.kRight)
        dm.text(om.MPoint(-6.5, 2.0, 0.0), "2 mesh kLineStrip", omr.MUIDrawManager.kRight)
        dm.text(om.MPoint(-6.5, 4.0, 0.0), "3 points() per color", omr.MUIDrawManager.kRight)
        if xray:
            dm.endDrawInXray()
        dm.endDrawable()


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Ji Hun Park", "0.1", "Any")
    plugin.registerNode(NODE_NAME, NODE_ID, ProbeNode.creator, ProbeNode.initialize, om.MPxNode.kLocatorNode, CLASSIFICATION)
    omr.MDrawRegistry.registerDrawOverrideCreator(CLASSIFICATION, REGISTRANT, ProbeOverride.creator)


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    omr.MDrawRegistry.deregisterDrawOverrideCreator(CLASSIFICATION, REGISTRANT)
    plugin.deregisterNode(NODE_ID)
