# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 플러그인 로드 · 그리기 노드 만들기 / 지우기 · 그리기 데이터 만들기 (계획서 §4-5)
"""
그리기 노드는 **API(MDagModifier)로** 만들고 지운다 → undo 큐에 들어가지 않는다(Ctrl+Z 는 키만 되돌린다).
노드 · 그 트랜스폼은 `doNotWrite` 라 씬에 저장되지 않고, 아웃라이너에서 숨긴다 - 이 툴 없이도 파일이 그대로 열린다.
"""

import os

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

from . import draw_bridge
from ..plugin import jun_motion_path as plugin_source     # 버전 · 명령 이름만 읽는다 (등록은 loadPlugin 이)

PLUGIN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin",
                           "jun_motion_path.py")
NODE_TYPE = "junMotionPath"
COMMAND = "junMotionPathSetKeys"
TRANSFORM_PREFIX = "JUN_motionPath_"

#: 경로마다 돌려 쓰는 색 (어두운 뷰포트 배경에서 잘 보이는 것)
PALETTE = ((0.30, 0.75, 1.00), (0.55, 1.00, 0.45), (1.00, 0.55, 0.85), (1.00, 0.85, 0.35),
           (0.60, 0.60, 1.00), (0.35, 1.00, 0.85))


#: 옛 플러그인을 바꿨으면 그 버전 (툴 창이 한 번 로그로 알린다) - v01.07
replaced_plugin = None


def command_exists(name):
    """MEL 명령이 등록되어 있나 (Python cmds 에는 exists 가 없다 - hasattr 은 내려놓은 플러그인 명령도 남아 있을 수 있다)."""
    return bool(mel.eval('exists "{0}"'.format(name)))


def plugin_is_current(name):
    """읽혀 있는 플러그인이 이 툴의 것과 같은가 (버전 + 명령이 다 있다)."""
    try:
        have = cmds.pluginInfo(name, q=True, version=True)
    except RuntimeError:
        return False
    return have == plugin_source.PLUGIN_VERSION and all(command_exists(c) for c in plugin_source.COMMANDS)


def ensure_plugin():
    """플러그인을 읽는다. 이미 읽혀 있어도 **옛 버전이면 다시 읽는다** (v01.07). 실패하면 RuntimeError.

    v01.07 이전에는 읽혀 있으면 그대로 두었다 - 툴만 새로 고치고(DEV 리로드 · 새 버전 복사) 마야를 껐다 켜지 않으면
    v01.00~02 의 플러그인이 남아 v01.03 의 `junMotionPathDirty` 가 없었다 → 키를 끌면
    "[FAIL] Drag : module 'maya.cmds' has no attribute 'junMotionPathDirty'".
    다시 읽기 전에 그리기 노드를 지운다(노드가 있으면 마야가 내려놓지 못한다). 툴 창이 다시 그린다.
    """
    name = os.path.splitext(os.path.basename(PLUGIN_FILE))[0]
    if cmds.pluginInfo(name, q=True, loaded=True) and not plugin_is_current(name):
        old = cmds.pluginInfo(name, q=True, version=True)
        delete_all()
        try:
            cmds.unloadPlugin(name)
        except RuntimeError:
            # undo 큐에 옛 플러그인 명령(키 끌기 기록)이 남아 있으면 "still in use" 로 거부된다(실측) → 큐를 비우고 한 번 더.
            # 옛 플러그인을 처음 바꿀 때 한 번뿐이다. 툴 창이 로그로 알린다(replaced_plugin).
            cmds.flushUndo()
            try:
                cmds.unloadPlugin(name)
            except RuntimeError as exc:
                raise RuntimeError("An old Motion Path plugin (v{0}) is loaded and could not be replaced ({1}). "
                                   "Restart Maya.".format(old, exc))
        global replaced_plugin
        replaced_plugin = old
    if not cmds.pluginInfo(name, q=True, loaded=True):
        cmds.loadPlugin(PLUGIN_FILE, quiet=True)
    if not cmds.pluginInfo(name, q=True, loaded=True) or not plugin_is_current(name):
        raise RuntimeError("Could not load the plugin {0}".format(PLUGIN_FILE))
    return name


def create_node(path_key, label):
    """그리기 노드 하나 (트랜스폼 이름, 셰이프 이름). undo 큐 밖."""
    mod = om.MDagModifier()
    xform = mod.createNode(NODE_TYPE)
    mod.renameNode(xform, TRANSFORM_PREFIX + _safe(label))
    mod.doIt()
    fn_x = om.MFnDagNode(xform)
    shape = fn_x.child(0)
    for obj in (xform, shape):
        fn = om.MFnDependencyNode(obj)
        fn.setDoNotWrite(True)
    om.MFnDependencyNode(xform).findPlug("hiddenInOutliner", False).setBool(True)
    om.MFnDependencyNode(shape).findPlug("pathKey", False).setString(path_key)
    return fn_x.fullPathName(), om.MFnDagNode(shape).fullPathName()


def delete_node(transform):
    """그리기 노드를 지운다 (undo 큐 밖). 없으면 조용히."""
    if not transform or not cmds.objExists(transform):
        return
    sel = om.MSelectionList()
    sel.add(transform)
    mod = om.MDagModifier()
    mod.deleteNode(sel.getDependNode(0))
    mod.doIt()


def delete_all():
    """이 툴이 만든 그리기 노드를 모두 지운다(이전 세션이 남긴 것 포함)."""
    for shape in cmds.ls(type=NODE_TYPE, long=True) or []:
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or [shape]
        delete_node(parents[0])
    draw_bridge.clear()


def _safe(label):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in label.split("|")[-1].split(":")[-1])


def _points(rows):
    arr = om.MPointArray()
    for x, y, z in rows:
        arr.append(om.MPoint(float(x), float(y), float(z)))
    return arr


def payload(cache, color, selected_times, current_frame, show_dots=True, show_keys=True, show_numbers=False,
            line_width=2.0, dot_size=4.0, key_size=9.0, points=None, ghost=None):
    """경로 하나의 그리기 데이터 (draw_bridge.DATA 형식).

    points : cache.points 대신 그릴 점 (그래프 Smooth 미리보기, v01.04) · ghost : 함께 회색으로 그릴 원래 선
    """
    pts = cache.points if points is None else points
    sel = {round(t, 3) for t in selected_times}
    keys, chosen, labels = [], [], []
    if show_keys:
        for k in cache.keys:
            p = pts[k.row]
            (chosen if round(k.t, 3) in sel else keys).append(p)
            if show_numbers:
                labels.append((om.MPoint(float(p[0]), float(p[1]), float(p[2])), " {0:g}".format(k.t)))
    current = []
    row = cache.row_of(current_frame)
    if row is not None:
        current.append(pts[row])
    return {
        "line": _points(pts),
        "dots": _points(pts) if show_dots else om.MPointArray(),
        "keys": _points(keys),
        "selected": _points(chosen),
        "current": _points(current),
        "labels": labels,
        "ghost": _points(ghost) if ghost is not None else om.MPointArray(),
        "color": om.MColor((color[0], color[1], color[2], 1.0)),
        "locked": cache.locked,
        "line_width": float(line_width),
        "dot_size": float(dot_size),
        "key_size": float(key_size),
    }
