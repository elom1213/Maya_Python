# -*- coding: utf-8 -*-
# A00380_MeshTool v01.21 - Quad Patch 탭 시험 (mayapy 2024)
#   mayapy.exe test_quad_patch.py [--speed]   (mayapy = C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe)
# 코어(Edge Border / Inset / Faces / Extrude / 스킨 히스토리 / 셰이딩 / 오류) + 탭 UI 스모크(오프스크린 Qt).
# --speed = 9만 버텍스 구에 400면 패치(약 6초). QApplication 은 maya.standalone.initialize() 보다 먼저.
import os
import sys
import traceback

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om   # noqa: E402
from tools.A00380_MeshTool.app.core import quad_patch as qp   # noqa: E402
cmds.undoInfo(state=True, infinity=True)
FAILS = []


def check(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        FAILS.append(msg)


def border_edges(m):
    it = om.MItMeshEdge(qp._dag(m))
    c = 0
    while not it.isDone():
        if it.onBoundary():
            c += 1
        it.next()
    return c


def normals_up(m, faces):
    fn = qp._fn(m)
    return all(fn.getPolygonNormal(f).y > 0.5 for f in faces)


def nonmanifold(m):
    return cmds.polyInfo(m, nonManifoldEdges=True) or cmds.polyInfo(m, nonManifoldVertices=True)


def find_edge(m, pred):
    it = om.MItMeshEdge(qp._dag(m))
    out = []
    while not it.isDone():
        c = it.center(om.MSpace.kObject)
        if it.onBoundary() and pred(c):
            out.append(it.index())
        it.next()
    return out


def run(name, fn):
    try:
        fn()
    except Exception:
        traceback.print_exc()
        FAILS.append(name + ' crashed')


def t_edge():
    cmds.file(new=True, f=True)
    pl = cmds.polyPlane(w=6, h=6, sx=6, sy=6, ch=False)[0]
    cmds.delete(pl + '.f[14:15]', pl + '.f[20:21]')
    shape = cmds.listRelatives(pl, s=True, f=True)[0]
    b0 = border_edges(pl)
    f0 = cmds.polyEvaluate(pl, f=True)
    inner = find_edge(pl, lambda c: abs(c.x) < 1.5 and abs(c.z) < 1.5)[0]
    cmds.select(pl + '.e[%d]' % inner)
    s = qp.QuadPatchSession.from_selection('edge')
    check(s.edge_count == 8, 'edge loop 8 (%d)' % s.edge_count)
    rot, a = s.auto_split()
    print('auto', rot, a)
    s.preview(rot=rot, side=a, rings=0, relax_iter=10)
    check(cmds.objExists(qp.PREVIEW_NAME), 'preview exists')
    res = s.commit(rot=rot, side=a, rings=0, relax_iter=10)
    print(res)
    check(not cmds.objExists(qp.PREVIEW_NAME), 'preview removed after commit')
    check(border_edges(pl) == b0 - 8, 'hole closed (border %d -> %d)' % (b0, border_edges(pl)))
    newf = list(range(f0, cmds.polyEvaluate(pl, f=True)))
    check(len(newf) == res['faces'], 'face count %d' % len(newf))
    check(normals_up(pl, newf), 'new faces face +Y like neighbours')
    check(not nonmanifold(pl), 'manifold')
    check(not cmds.listHistory(shape, pdo=True), 'no history left')
    check(len(cmds.polyListComponentConversion(pl + '.f[%d]' % newf[0], tuv=True) or []) > 0, 'uvs on new face')
    cmds.undo()
    check(cmds.polyEvaluate(pl, f=True) == f0 and border_edges(pl) == b0, 'undo restores')


def t_inset():
    cmds.file(new=True, f=True)
    pl = cmds.polyPlane(w=8, h=8, sx=8, sy=8, ch=False)[0]
    cmds.delete(['%s.f[%d]' % (pl, r * 8 + c) for r in range(2, 6) for c in range(2, 5)])
    b0 = border_edges(pl)
    f0 = cmds.polyEvaluate(pl, f=True)
    inner = find_edge(pl, lambda c: abs(c.x) < 3 and abs(c.z) < 3)[0]
    cmds.select(pl + '.e[%d]' % inner)
    s = qp.QuadPatchSession.from_selection('edge')
    rot, a = s.auto_split()
    print('edges', s.edge_count, 'auto', rot, a)
    s.commit(rot=rot, side=a, rings=1, relax_iter=20, smooth=0.3)
    newf = list(range(f0, cmds.polyEvaluate(pl, f=True)))
    check(border_edges(pl) == b0 - 14, 'inset: hole closed')
    check(normals_up(pl, newf), 'inset: normals')
    check(not nonmanifold(pl), 'inset: manifold')
    fn = qp._fn(pl)
    ys = [fn.getPoint(v).y for v in range(fn.numVertices)]
    check(max(abs(y) for y in ys) < 1e-4, 'inset: flat plane stays flat')


def t_face():
    cmds.file(new=True, f=True)
    sp = cmds.polySphere(r=2, sx=20, sy=20, ch=False)[0]
    f0 = cmds.polyEvaluate(sp, f=True)
    region = ['%s.f[%d]' % (sp, r * 20 + c) for r in range(8, 11) for c in range(3, 7)]
    cmds.select(region)
    s = qp.QuadPatchSession.from_selection('face')
    rot, a = s.auto_split()
    print('face edges', s.edge_count, rot, a)
    shells0 = cmds.polyEvaluate(sp, uvShell=True)
    res = s.commit(rot=rot, side=a, rings=0, relax_iter=10)
    print(res)
    shells1 = cmds.polyEvaluate(sp, uvShell=True)
    check(shells1 == shells0, 'face: uv shells sewn (%s -> %s)' % (shells0, shells1))
    fn = qp._fn(sp)
    r = [om.MVector(fn.getPoint(v)).length() for v in range(fn.numVertices)]
    check(min(r) > 1.9, 'face: new points stay near the sphere (min r %.3f)' % min(r))
    check(border_edges(sp) == 0, 'face: closed')
    check(not nonmanifold(sp), 'face: manifold')
    nf = fn.numPolygons
    newf = range(f0 - len(region), nf)
    ok = all(fn.getPolygonNormal(f) * om.MVector(fn.getPoint(fn.getPolygonVertices(f)[0])) > 0 for f in newf)
    check(ok, 'face: normals point outward')
    uvs = [fn.getPolygonUV(f, 0) for f in newf]
    print('sample uvs', uvs[:4])
    # 원래 영역의 UV 범위 (sphere 20x20: u 0.15~0.35, v 0.4~0.55 근처)
    check(all(0.1 <= u <= 0.4 and 0.35 <= v <= 0.6 for u, v in uvs), 'face: uvs follow the old faces')
    cmds.undo()
    check(cmds.polyEvaluate(sp, f=True) == f0, 'face: undo restores')


def t_extrude():
    cmds.file(new=True, f=True)
    pl = cmds.polyPlane(w=8, h=8, sx=8, sy=8, ch=False)[0]
    cmds.delete(['%s.f[%d]' % (pl, r * 8 + c) for r in range(2, 6) for c in range(2, 6)])
    f0 = cmds.polyEvaluate(pl, f=True)
    b0 = border_edges(pl)
    chain = find_edge(pl, lambda c: abs(c.z - (-2)) < 1e-3 and abs(c.x) < 2)
    sel = ['%s.e[%d]' % (pl, e) for e in chain[:3]]
    cmds.select(sel)
    s = qp.QuadPatchSession.from_selection('extrude')
    print('extrude chain', s.chain_len, 'max rows', s.max_rows())
    s.commit(rows=2, relax_iter=10)
    newf = list(range(f0, cmds.polyEvaluate(pl, f=True)))
    check(len(newf) == 6, 'extrude: 3x2 faces (%d)' % len(newf))
    check(normals_up(pl, newf), 'extrude: normals')
    check(not nonmanifold(pl), 'extrude: manifold')
    check(border_edges(pl) == b0 - 3 - 4 + 3, 'extrude: border %d' % border_edges(pl))
    cmds.undo()
    cmds.select(sel)
    s = qp.QuadPatchSession.from_selection('extrude')
    try:
        s.commit(rows=10)
        check(False, 'extrude: too many rows should fail')
    except qp.PatchError as e:
        check(True, 'extrude too many rows -> %s' % e)


def t_skin():
    cmds.file(new=True, f=True)
    pl = cmds.polyPlane(w=6, h=6, sx=6, sy=6, ch=False)[0]
    cmds.delete(pl + '.f[14:15]', pl + '.f[20:21]')
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='redSG')
    cmds.sets(pl + '.f[0:31]', e=True, forceElement=sg)
    cmds.select(cl=True)
    j = cmds.joint()
    cmds.skinCluster(j, pl)
    shape = cmds.listRelatives(pl, s=True, ni=True, f=True)[0]
    f0 = cmds.polyEvaluate(pl, f=True)
    inner = find_edge(shape, lambda c: abs(c.x) < 1.5 and abs(c.z) < 1.5)[0]
    cmds.select(shape + '.e[%d]' % inner)
    s = qp.QuadPatchSession.from_selection('edge')
    res = s.commit(side=1, rot=0)
    check(res['history_kept'] and bool(cmds.ls(cmds.listHistory(shape), type='skinCluster')), 'skin: history kept')
    newf = list(range(f0, cmds.polyEvaluate(pl, f=True)))
    members = cmds.ls(cmds.sets(sg, q=True), fl=True)
    check(all(any(m.endswith('.f[%d]' % f) for m in members) for f in newf), 'shading: new faces in redSG')


def t_errors():
    cmds.file(new=True, f=True)
    pl = cmds.polyPlane(w=6, h=6, sx=6, sy=6, ch=False)[0]
    cmds.select(pl + '.f[0]')
    try:
        qp.QuadPatchSession.from_selection('face')
        check(False, 'face at border should fail')
    except qp.PatchError as e:
        check(True, 'face at border -> %s' % e)
    cmds.delete(pl + '.f[14:15]')
    cmds.select(cl=True)
    inner = find_edge(pl, lambda c: abs(c.x) < 1.5 and abs(c.z) < 1.5)[0]
    cmds.select(pl + '.e[%d]' % inner)
    s = qp.QuadPatchSession.from_selection('edge')
    check(s.edge_count == 6, 'six-edge hole ok')
    cmds.select(pl + '.e[0]')
    s = qp.QuadPatchSession.from_selection('edge')
    check(s.edge_count == 24, 'outer border loop 24 edges')


def t_speed():
    import time
    cmds.file(new=True, f=True)
    sp = cmds.polySphere(r=10, sx=300, sy=300, ch=False)[0]
    region = ['%s.f[%d]' % (sp, r * 300 + c) for r in range(140, 160) for c in range(10, 30)]
    cmds.select(region)
    t = time.time()
    s = qp.QuadPatchSession.from_selection('face')
    t1 = time.time() - t
    t = time.time()
    for i in range(5):
        s.preview(side=s.auto_split()[1] if i == 0 else 20, rot=0, relax_iter=10)
    t2 = (time.time() - t) / 5
    rot, a = s.auto_split()
    res = s.commit(rot=rot, side=a, relax_iter=10)
    print('speed: start %.2fs, preview %.2fs, commit %s' % (t1, t2, res))
    check(not nonmanifold(sp), 'speed: manifold')


def t_ui():
    from tools.A00380_MeshTool.app.ui.quad_patch_tab import QuadPatchTab
    logs = []
    tab = QuadPatchTab(log=lambda text, warn=False, ok=False: logs.append((warn, text)))
    tab.show()
    cmds.file(new=True, f=True)
    cmds.select(cl=True)
    tab.on_start(qp.MODE_EDGE)
    check(logs and logs[-1][0] and not tab.btn_apply.isEnabled(), 'ui: empty selection warns')
    pl = cmds.polyPlane(w=8, h=8, sx=8, sy=8, ch=False)[0]
    cmds.delete(['%s.f[%d]' % (pl, r * 8 + c) for r in range(2, 6) for c in range(2, 6)])
    e = find_edge(pl, lambda c: abs(c.x) < 3 and abs(c.z) < 3)[0]
    f0 = cmds.polyEvaluate(pl, f=True)
    cmds.select('%s.e[%d]' % (pl, e))
    tab.on_start(qp.MODE_EDGE)
    check(tab.row_rot.slider.maximum() == 15 and tab.row_side.slider.maximum() == 7, 'ui: ranges from 16 edges')
    check(not tab.row_rows.spin.isEnabled(), 'ui: rows off in Edge Border')
    tab.row_side.slider.setValue(3)
    tab.row_rings.spin.setValue(1)
    tab._refresh()
    check('31 faces' in tab.lbl_status.text(), 'ui: status ' + tab.lbl_status.text())
    tab.on_apply()
    check(cmds.polyEvaluate(pl, f=True) - f0 == 31 and not cmds.objExists(qp.PREVIEW_NAME), 'ui: patched 31 faces')
    cmds.undo()
    check(cmds.polyEvaluate(pl, f=True) == f0, 'ui: one Ctrl+Z undoes the patch')
    cmds.select('%s.e[%d]' % (pl, e))
    tab.on_start(qp.MODE_EDGE)
    tab.on_cancel()
    check(not cmds.objExists(qp.PREVIEW_NAME) and cmds.polyEvaluate(pl, f=True) == f0, 'ui: cancel leaves the mesh')
    chain = find_edge(pl, lambda c: abs(c.z + 2) < 1e-3 and abs(c.x) < 2)
    cmds.select(['%s.e[%d]' % (pl, x) for x in chain])
    tab.on_start(qp.MODE_EXTRUDE)
    check(tab.row_rows.slider.maximum() == 5 and not tab.row_rot.spin.isEnabled(), 'ui: extrude rows 1..5')
    tab.row_rows.spin.setValue(2)
    tab.on_apply()
    check(cmds.polyEvaluate(pl, f=True) - f0 == 8, 'ui: extrude 4 x 2')


TESTS = [('edge', t_edge), ('inset', t_inset), ('face', t_face), ('extrude', t_extrude),
             ('skin', t_skin), ('errors', t_errors), ('ui', t_ui)]
if '--speed' in sys.argv:
    TESTS.insert(0, ('speed', t_speed))
for n, f in TESTS:
    print('---', n)
    run(n, f)
print('FAILS', FAILS)
print('ALL PASS' if not FAILS else 'FAILED %d' % len(FAILS))

