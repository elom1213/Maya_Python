# -*- coding: utf-8 -*-
# A00275_skinTool_V01 v01.37 - Weights > Move (n -> k) 시험 (mayapy)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_weight_move.py
#
# 핵심은 **Kangaroo 대조** - 같은 씬을 두 번 만들어 kangaroo `moveSkinClusterWeights` 와 Native `move_weights` 를
# 각각 돌리고 웨이트 행렬을 비교한다(허용 1e-6). Kangaroo 경로는 환경 변수 JUN_KANGAROO_DIR
# (예: ...\0020_maya_plugin\0010_kangaroo) 가 없으면 건너뛰고, 나머지(합 보존 · 범위 밖 불변 · undo · numpy=순수 파이썬)는 늘 돈다.
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core.maya_undo import undo_chunk   # noqa: E402
from tools.A00275_skinTool_V01.app.core import weight_move_manager as mv   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ---------------------------------------------------------------- Kangaroo
KT = None
KDIR = os.environ.get("JUN_KANGAROO_DIR")
if KDIR and os.path.isdir(KDIR):
    sys.path.insert(0, os.path.join(KDIR, "scripts"))
    version = cmds.about(version=True)[:4]
    cmds.loadPlugin(os.path.join(KDIR, "plug-ins", "win64", version, "kt_cmdUndo.py"), quiet=True)
    import kangarooTabTools.weights as KT   # noqa: E402
    import kangarooTools.patch as KTP   # noqa: E402
    import kangarooTools.report as KTR   # noqa: E402

    class _Silent(object):                       # UI 진행률 객체 - 헤드리스에서는 None
        def __getattr__(self, name):
            return lambda *a, **k: None
    KTR.report = _Silent()


# ---------------------------------------------------------------- 씬
def scene(kind="plane", lock=None, skin_parent=False, to_influence=True):
    """From 2 (fA, fB) 가 바인드된 메시 + To 체인 3 (t1 -> t2 -> t3)."""
    cmds.file(new=True, force=True)
    if kind == "plane":
        mesh = cmds.polyPlane(name="m", w=10, h=2, sx=20, sy=4)[0]
    else:                                        # 원통 (닫힌 면 없음 -> 경계 있음), 위로 서 있다
        mesh = cmds.polyCylinder(name="m", r=1, h=10, sx=12, sy=20, sc=0)[0]
        cmds.delete("m.f[240:241]")             # 위아래 캡 제거 -> 열린 경계
    cmds.select(clear=True)
    if kind == "plane":
        fa = cmds.joint(name="fA", position=(-5, 0, 0))
        fb = cmds.joint(name="fB", position=(5, 0, 0))
        cmds.select(clear=True)
        t1 = cmds.joint(name="t1", position=(-5, 0.5, 0))
        t2 = cmds.joint(name="t2", position=(0, 0.5, 0))
        t3 = cmds.joint(name="t3", position=(5, 0.5, 0))
    else:
        fa = cmds.joint(name="fA", position=(0, -5, 0))
        fb = cmds.joint(name="fB", position=(0, 5, 0))
        cmds.select(clear=True)
        t1 = cmds.joint(name="t1", position=(0.3, -5, 0))
        # y=0 이면 y=-2.5 행이 t1 · t2 와 거리가 **정확히 같다**. Kangaroo 는 To 목록을 list(set(...)) 로 만들어
        # 동률일 때 고르는 조인트가 실행마다(문자열 해시) 달라진다 - 이 툴은 목록 순서로 정한다. 대조는 동률 없는 씬으로.
        t2 = cmds.joint(name="t2", position=(0.3, 0.013, 0))
        t3 = cmds.joint(name="t3", position=(0.3, 5, 0))
    cmds.select(clear=True)
    keep = cmds.joint(name="keep", position=(0, 0, 3))
    infl = ["fA", "fB", "keep"] + (["t1", "t2", "t3"] if to_influence else [])
    skin = cmds.skinCluster(infl, mesh, toSelectedBones=True, maximumInfluences=6)[0]
    if to_influence:
        for t in ("t1", "t2", "t3"):
            cmds.skinPercent(skin, mesh, transformValue=[(t, 0.0)])
    count = cmds.polyEvaluate(mesh, vertex=True)
    for v in range(count):                       # 결정적인 섞인 웨이트
        a = ((v * 37) % 11) / 10.0 * 0.8
        k = ((v * 13) % 5) / 20.0
        cmds.skinPercent(skin, "m.vtx[{0}]".format(v), transformValue=[("fA", a), ("keep", k),
                                                                     ("fB", max(0.0, 1.0 - a - k))])
    if lock:
        cmds.setAttr(lock + ".liw", 1)
    if skin_parent:
        cmds.addAttr("t2", ln="skinParent", dt="string")
        cmds.setAttr("t2.skinParent", "keep", type="string")
    return mesh, skin


def matrix(skin):
    infl = cmds.skinCluster(skin, q=True, influence=True)
    count = cmds.polyEvaluate("m", vertex=True)
    out = []
    for v in range(count):
        row = dict(zip(infl, cmds.skinPercent(skin, "m.vtx[{0}]".format(v), q=True, v=True)))
        out.append([row.get(n, 0.0) for n in ("fA", "fB", "keep", "t1", "t2", "t3")])
    return out


def max_diff(a, b):
    return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def select(component):
    cmds.select(component if component else "m", replace=True)


def run_native(opts, component=None, soft=None, **scene_kw):
    mesh, skin = scene(**scene_kw)
    select(component)
    if soft:
        cmds.softSelect(softSelectEnabled=True, softSelectDistance=soft, softSelectFalloff=0)
    with undo_chunk():
        done, msgs = mv.move_weights(["fA", "fB"], opts.pop("_to", ["t1", "t2", "t3"]), island_check=False, **opts)
    cmds.softSelect(softSelectEnabled=False)
    return matrix(skin), msgs


KT_KEYS = {"smooth_steps": "iSmoothSteps", "blend": "fBlend", "joint_lines": "iJointLines",
           "joint_locks": "iJointLocks", "border_edges": "iBorderEdges", "border_mask_steps": "iSmoothBorderMask",
           "project_squash": "bProjectSquashToMainJoints"}


def run_kangaroo(opts, component=None, soft=None, **scene_kw):
    mesh, skin = scene(**scene_kw)
    select(component)
    if soft:
        cmds.softSelect(softSelectEnabled=True, softSelectDistance=soft, softSelectFalloff=0)
    to = opts.pop("_to", ["t1", "t2", "t3"])
    kw = dict((KT_KEYS[k], v) for k, v in opts.items())
    KT.moveSkinClusterWeights(xJoints={"['fA','fB']": repr(to)}, bDisableIslandCheck=True,
                              iCheckMissingInfluences=KTP.MissingInfluencesOptions.onlyAddMissingInfluencesInSkinCluster,
                              **kw)
    cmds.softSelect(softSelectEnabled=False)
    return matrix(skin)


CASES = [
    ("1 plane n=2 k=3 default", dict(), {}),
    ("2 k=1 (merge)", dict(_to=["t2"]), {}),
    ("3a cylinder joint lines = points", dict(joint_lines=0), dict(kind="cyl")),
    ("3b cylinder joint lines = children in To", dict(joint_lines=1), dict(kind="cyl")),
    ("3c cylinder joint lines = all children", dict(joint_lines=2), dict(kind="cyl")),
    ("4 component selection", dict(), dict(_component="m.vtx[20:70]")),
    ("5 soft selection", dict(), dict(_component="m.vtx[40:44]", _soft=3.0)),
    ("6a smooth steps 0", dict(smooth_steps=0), {}),
    ("6b smooth steps 20", dict(smooth_steps=20), {}),
    ("7 blend 0.5", dict(blend=0.5), {}),
    ("8a locks keep (keep locked)", dict(joint_locks=1), dict(lock="keep")),
    ("8b locks only add (t2 locked)", dict(joint_locks=2), dict(lock="t2")),
    ("8c locks only remove (fA locked)", dict(joint_locks=3), dict(lock="fA")),
    ("9a border ignore, mask 2", dict(border_edges=1, border_mask_steps=2), dict(kind="cyl")),
    ("9b border only, mask 0", dict(border_edges=2, border_mask_steps=0), dict(kind="cyl")),
    ("10 To not influences", dict(), dict(to_influence=False)),
    ("11 skinParent on t2", dict(), dict(skin_parent=True)),
]

for name, opts, scene_kw in CASES:
    scene_kw = dict(scene_kw)
    component = scene_kw.pop("_component", None)
    soft = scene_kw.pop("_soft", None)
    native, msgs = run_native(dict(opts), component, soft, **scene_kw)
    sums_ok = all(abs(sum(r) - 1.0) < 1e-6 for r in native)
    check("[{0}] rows sum to 1".format(name), sums_ok)
    if KT is not None and opts.get("border_edges", 0) == 0:
        golden = run_kangaroo(dict(opts), component, soft, **scene_kw)
        diff = max_diff(native, golden)
        check("[{0}] == Kangaroo".format(name), diff < 1e-6, "max diff {0:.2e}".format(diff))
        if diff >= 1e-6 and os.environ.get("JUN_DEBUG_MOVE"):
            bad = [v for v in range(len(native)) if max(abs(a - b) for a, b in zip(native[v], golden[v])) > 1e-6]
            print("DEBUG bad vertices", len(bad), bad[:20])
            for v in bad[:4]:
                print("DEBUG", v, [round(x, 4) for x in native[v]], [round(x, 4) for x in golden[v]])
    elif opts.get("border_edges", 0):
        # Kangaroo 의 Border Edges 는 numpy 2.x 에서 자기 버그로 죽는다(getBorderMask -> smoothValues2d 의
        # 불리언 인덱스 길이가 패딩 행 하나만큼 어긋난다, 예전 numpy 는 허용). 그래서 성질로 본다:
        #   Ignore borders -> 경계 버텍스는 그대로 / Only borders(mask 0) -> 경계 아닌 버텍스는 그대로.
        border = set()
        it_mesh = cmds.ls("m", long=True)[0]
        from maya.api import OpenMaya as om2
        sel = om2.MSelectionList(); sel.add(it_mesh)
        it = om2.MItMeshVertex(sel.getDagPath(0))
        while not it.isDone():
            if it.onBoundary():
                border.add(it.index())
            it.next()
        original_mesh, original_skin = scene(**scene_kw)
        original = matrix(original_skin)
        if opts["border_edges"] == 1:
            same = all(native[v] == original[v] for v in border)
            check("[{0}] border vertices unchanged".format(name), border and same, len(border))
        else:
            same = all(native[v] == original[v] for v in range(len(native)) if v not in border)
            changed = any(native[v] != original[v] for v in border)
            check("[{0}] only border vertices changed".format(name), same and changed, len(border))

if KT is None:
    print("SKIP Kangaroo comparison (set JUN_KANGAROO_DIR)")

# ---------------------------------------------------------------- 성질 (Kangaroo 없이)
mesh, skin = scene()
before = matrix(skin)
select("m.vtx[0:30]")
with undo_chunk():
    mv.move_weights(["fA", "fB"], ["t1", "t2", "t3"], island_check=False)
after = matrix(skin)
outside_same = all(before[v] == after[v] for v in range(31, len(before)))
check("respect selection : vertices outside the selection unchanged", outside_same)
check("respect selection : selection changed", before[:31] != after[:31])
moved_ok = all(abs((b[0] + b[1]) - (a[3] + a[4] + a[5])) < 1e-6 and a[0] < 1e-9 and a[1] < 1e-9
               for b, a in zip(before[:31], after[:31]))
check("From weight fully moved to To (sum kept per vertex)", moved_ok)
cmds.undo()
check("undo brings everything back in one step", max_diff(matrix(skin), before) < 1e-9)

mesh, skin = scene()
select("m.vtx[0:30]")
with undo_chunk():
    mv.move_weights(["fA", "fB"], ["t1", "t2", "t3"], island_check=False, respect_selection=False)
after = matrix(skin)
check("respect selection off : the whole mesh changes", all(r[0] < 1e-9 and r[1] < 1e-9 for r in after))

# From 웨이트가 없는 버텍스는 그대로 (범위 밖 불변)
mesh, skin = scene()
for v in range(0, 21):
    cmds.skinPercent(skin, "m.vtx[{0}]".format(v), transformValue=[("keep", 1.0)])
before = matrix(skin)
select(None)
with undo_chunk():
    mv.move_weights(["fA", "fB"], ["t1", "t2", "t3"], island_check=False)
after = matrix(skin)
check("vertices without From weight are untouched", all(before[v] == after[v] for v in range(21)))

# numpy = 순수 파이썬
if mv.np is not None:
    results = []
    for use_np in (True, False):
        saved = mv.np
        if not use_np:
            mv.np = None
        try:
            mesh, skin = scene(kind="cyl")
            select(None)
            mv.move_weights(["fA", "fB"], ["t1", "t2", "t3"], island_check=False, joint_lines=1)
            results.append(matrix(skin))
        finally:
            mv.np = saved
    check("numpy path == pure Python path", max_diff(results[0], results[1]) < 1e-9,
          "{0:.2e}".format(max_diff(results[0], results[1])))

# 섬 검사 - confirm 콜백
mesh, skin = scene()
select(["m.vtx[0:2]", "m.vtx[60:62]"])
asked = []
done, msgs = mv.move_weights(["fA"], ["t1", "t2"], confirm=lambda q: asked.append(q) or False)
check("island check asks and can stop", asked and done == 0 and any("island check" in m for m in msgs), asked)

# Kangaroo 엔진 래퍼 (UI 의 Engine = Kangaroo) == Native
if KT is not None:
    mesh, skin = scene(kind="cyl")
    select("m.vtx[30:150]")
    ok, msgs = mv.move_weights_kangaroo(["fA", "fB"], ["t1", "t2", "t3"], island_check=False)
    via_wrapper = matrix(skin)
    mesh, skin = scene(kind="cyl")
    select("m.vtx[30:150]")
    mv.move_weights(["fA", "fB"], ["t1", "t2", "t3"], island_check=False)
    check("Kangaroo engine wrapper == Native", ok and max_diff(via_wrapper, matrix(skin)) < 1e-6,
          "{0:.2e} {1}".format(max_diff(via_wrapper, matrix(skin)), msgs))

# 방어
done, msgs = mv.move_weights([], ["t1"])
check("empty From -> warning", done == 0 and any("Fill both" in m for m in msgs))
done, msgs = mv.move_weights(["nope"], ["t1"])
check("unknown joint -> warning", done == 0 and any("not a joint" in m for m in msgs))

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
