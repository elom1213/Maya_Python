# -*- coding: utf-8 -*-
# A00275_skinTool_V01 v01.40 - Weights > Flood 시험 (mayapy)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_weight_flood.py
#
# 1) Kangaroo 대조 - 같은 씬을 두 번 만들어 kangaroo `floodSkinCluster` 와 Native `flood_weights` 를 각각 돌리고
#    웨이트 행렬을 비교한다(허용 1e-6). JUN_KANGAROO_DIR (예: ...\0020_maya_plugin\0010_kangaroo) 이 없으면 건너뛴다.
# 2) 같은 이름 조인트 - Kangaroo 는 죽고(있으면 확인), Native 는 풀패스로 맞는 열에 쓴다.
# 3) 합 1 · undo 한 번 · Scale 1 = 변화 없음 · 애매한 이름은 건너뛰기.
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core.maya_undo import undo_chunk   # noqa: E402
from tools.A00275_skinTool_V01.app.core import weight_flood_manager as fl   # noqa: E402

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

NAMES = ("j1", "j2", "j3", "keep", "extra")


# ---------------------------------------------------------------- 씬
def scene(lock=None, extra_influence=True):
    """평면 + 체인 j1 -> j2 -> j3 (x 방향) + keep + extra. 섞인 웨이트가 전부에 깔린다."""
    cmds.file(new=True, force=True)
    mesh = cmds.polyPlane(name="m", w=10, h=2, sx=20, sy=4)[0]
    cmds.select(clear=True)
    cmds.joint(name="j1", position=(-4.1, 0.5, 0))
    cmds.joint(name="j2", position=(0.13, 0.5, 0))
    cmds.joint(name="j3", position=(4.2, 0.5, 0))
    cmds.select(clear=True)
    cmds.joint(name="keep", position=(0, 0, 3))
    cmds.select(clear=True)
    cmds.joint(name="extra", position=(0, 0, -3))
    infl = ["j1", "j2", "j3", "keep"] + (["extra"] if extra_influence else [])
    skin = cmds.skinCluster(infl, mesh, toSelectedBones=True, maximumInfluences=6)[0]
    count = cmds.polyEvaluate(mesh, vertex=True)
    for v in range(count):
        a = ((v * 37) % 11) / 10.0 * 0.6
        b = ((v * 13) % 7) / 10.0 * 0.3          # a + b + k <= 0.98 -> 합 1 을 넘지 않는다
        k = ((v * 7) % 5) / 20.0
        rest = max(0.0, 1.0 - a - b - k)
        values = [("j1", a), ("j3", b), ("keep", k), ("j2", rest)]
        if extra_influence:
            values = [("j1", a * 0.8), ("extra", a * 0.2), ("j3", b), ("keep", k), ("j2", rest)]
        cmds.skinPercent(skin, "m.vtx[{0}]".format(v), transformValue=values)
    if lock:
        cmds.setAttr(lock + ".liw", 1)
    return mesh, skin


def matrix(skin, names=NAMES):
    infl = [cmds.ls(n, long=True)[0] for n in cmds.skinCluster(skin, q=True, influence=True)]
    longs = [cmds.ls(n, long=True)[0] for n in names]
    count = cmds.polyEvaluate("m", vertex=True)
    out = []
    for v in range(count):
        row = dict(zip(infl, cmds.skinPercent(skin, "m.vtx[{0}]".format(v), q=True, v=True)))
        out.append([row.get(n, 0.0) for n in longs])
    return out


def max_diff(a, b):
    return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def prepare(component=None, soft=None):
    cmds.select(component if component else "m", replace=True)
    if soft:
        cmds.softSelect(softSelectEnabled=True, softSelectDistance=soft, softSelectFalloff=0)


def run_native(joints, opts, component=None, soft=None, **scene_kw):
    mesh, skin = scene(**scene_kw)
    prepare(component, soft)
    with undo_chunk():
        done, msgs = fl.flood_weights(joints, island_check=False, **opts)
    cmds.softSelect(softSelectEnabled=False)
    return matrix(skin), msgs


KT_KEYS = {"value": "fValue", "operation": "iOperation", "smooth_steps": "iSmoothSteps", "blend": "fBlend",
           "joint_lines": "iJointLines", "joint_locks": "iJointLocks", "border_edges": "iBorderEdges",
           "border_mask_steps": "iSmoothBorderMask", "project_squash": "bProjectSquashToMainJoints"}


def run_kangaroo(joints, opts, component=None, soft=None, **scene_kw):
    mesh, skin = scene(**scene_kw)
    prepare(component, soft)
    kw = dict((KT_KEYS[k], v) for k, v in opts.items())
    KT.floodSkinCluster(sJoints=list(joints), bDisableIslandCheck=True, xDistanceMeshes=None,
                        iCheckMissingInfluences=KTP.MissingInfluencesOptions.onlyAddMissingInfluencesInSkinCluster,
                        **kw)
    cmds.softSelect(softSelectEnabled=False)
    return matrix(skin)


RC, AC, RA, AA, SA, DI = (fl.OP_REPLACE_CLOSEST, fl.OP_ADD_CLOSEST, fl.OP_REPLACE_ALL, fl.OP_ADD_ALL,
                          fl.OP_SCALE_ALL, fl.OP_DISTRIBUTE)
CHAIN = ["j1", "j2", "j3"]

CASES = [
    ("1 replace closest, one joint, value 1", ["j2"], dict(), {}),
    ("2 replace closest, one joint, value 0.4", ["j2"], dict(value=0.4), {}),
    ("3 replace closest, chain of 3 (default)", CHAIN, dict(), {}),
    ("4 replace closest, chain, smooth 0", CHAIN, dict(smooth_steps=0), {}),
    ("5 replace closest, chain, joint lines = points", CHAIN, dict(joint_lines=0), {}),
    ("6 replace closest, chain, joint lines = children in list", ["j1", "j3"], dict(joint_lines=1), {}),
    ("7 replace closest, j1 + j3, all children", ["j1", "j3"], dict(joint_lines=2), {}),
    ("8 add closest, chain, value 0.5", CHAIN, dict(operation=AC, value=0.5), {}),
    ("9 add closest, chain, value 1", CHAIN, dict(operation=AC), {}),
    ("10 replace all, j1 + keep, value 0.6", ["j1", "keep"], dict(operation=RA, value=0.6), {}),
    ("11 add all, j1 + keep, value 0.4", ["j1", "keep"], dict(operation=AA, value=0.4), {}),
    ("13 scale all, j2, value 2.5", ["j2"], dict(operation=SA, value=2.5), {}),
    ("14 distribute, chain", CHAIN, dict(operation=DI), {}),
    ("15 component selection", CHAIN, dict(), dict(_component="m.vtx[20:70]")),
    ("16 soft selection", ["keep"], dict(value=0.7), dict(_component="m.vtx[40:44]", _soft=3.0)),
    ("17 blend 0.5", CHAIN, dict(blend=0.5), {}),
    ("18 locks keep (keep locked)", CHAIN, dict(value=0.6, joint_locks=1), dict(lock="keep")),
    ("19 locks only add (j1 locked)", ["j2"], dict(value=0.3, joint_locks=2), dict(lock="j1")),
    ("20 joint is not an influence yet", ["extra", "j2"], dict(value=0.8), dict(extra_influence=False)),
]

for name, joints, opts, scene_kw in CASES:
    scene_kw = dict(scene_kw)
    component = scene_kw.pop("_component", None)
    soft = scene_kw.pop("_soft", None)
    native, msgs = run_native(joints, dict(opts), component, soft, **scene_kw)
    ok_msg = any(m.startswith("[OK]") for m in msgs)
    # 다른 인플루언스가 없던 버텍스(vtx[0] = j2 100%)는 Value < 1 이면 합이 모자란다 - 원본과 같고 [WARN] 으로 알린다
    warned = any("less than 1" in m for m in msgs)
    sums_ok = all(abs(sum(r) - 1.0) < 1e-6 for r in native) or warned
    check("[{0}] ran, rows sum to 1 (or warned)".format(name), ok_msg and sums_ok,
          [m for m in msgs if not m.startswith("[OK]")])
    if KT is not None:
        golden = run_kangaroo(joints, dict(opts), component, soft, **scene_kw)
        if "blend" in opts and opts.get("operation", RC) != DI:
            # 원본 floodSkinCluster 는 fBlend 를 setSkinClusterWeights 에 넘기지 않는다(원본 버그 - Blend 무시).
            # 이 툴은 Blend 를 반영하므로 기대값 = 원래 웨이트와 원본 결과를 Blend 로 섞은 것.
            _m, _s = scene(**scene_kw)
            original = matrix(_s)
            b = opts["blend"]
            golden = [[o + (g - o) * b for o, g in zip(ro, rg)] for ro, rg in zip(original, golden)]
        diff = max_diff(native, golden)
        check("[{0}] == Kangaroo{1}".format(name, " (blended)" if "blend" in opts else ""), diff < 1e-6, "max diff {0:.2e}".format(diff))
        if diff >= 1e-6 and os.environ.get("JUN_DEBUG_FLOOD"):
            bad = [v for v in range(len(native)) if max(abs(a - b) for a, b in zip(native[v], golden[v])) > 1e-6]
            print("DEBUG bad vertices", len(bad), bad[:20])
            for v in bad[:4]:
                print("DEBUG", v, [round(x, 4) for x in native[v]], [round(x, 4) for x in golden[v]])

# ---------------------------------------------------------------- 범위 · 속성
mesh, skin = scene()
before = matrix(skin)
cmds.select("m.vtx[0:10]")
with undo_chunk():
    fl.flood_weights(["j2"], island_check=False)
after = matrix(skin)
check("only the selected vertices change", all(after[v] == before[v] for v in range(11, len(after)))
      and all(abs(after[v][1] - 1.0) < 1e-9 for v in range(11)))
cmds.undo()
check("one undo restores", max_diff(matrix(skin), before) < 1e-9)

mesh, skin = scene()
before = matrix(skin)
cmds.select("m")
fl.flood_weights(["j1", "j3"], operation=SA, value=1.0, island_check=False)
check("scale all with value 1 changes nothing (Kangaroo halves both and zeroes the others)",
      max_diff(matrix(skin), before) < 1e-9)

# Scale All 여러 조인트 = 조인트마다 Value 를 곱하고 나머지가 남은 몫을 비례로 (원본은 Value / n)
mesh, skin = scene()
before = matrix(skin)
cmds.select("m")
fl.flood_weights(["j1", "j3"], operation=SA, value=0.5, island_check=False)
after = matrix(skin)
ok = True
for rb, ra in zip(before, after):
    ok = ok and abs(ra[0] - rb[0] * 0.5) < 1e-9 and abs(ra[2] - rb[2] * 0.5) < 1e-9 and abs(sum(ra) - 1.0) < 1e-6
check("scale all on two joints multiplies each by Value, others take the rest", ok)

mesh, skin = scene()
cmds.select("m")
done, msgs = fl.flood_weights(["nope"], island_check=False)
check("unknown joint -> warning, nothing done", done == 0 and any("not a joint" in m for m in msgs), msgs)
done, msgs = fl.flood_weights(["j2"], operation=DI, island_check=False)
check("distribute with one joint -> warning", done == 0 and any("two joints" in m for m in msgs), msgs)


# ---------------------------------------------------------------- 같은 이름 조인트
def dup_scene():
    """그룹 A, B 아래에 같은 이름 `dup` 조인트, 그 자식도 같은 이름 `tip`. keep 과 함께 바인드."""
    cmds.file(new=True, force=True)
    mesh = cmds.polyPlane(name="m", w=10, h=2, sx=20, sy=4)[0]
    paths = []
    for grp, x in (("A", -3.0), ("B", 3.0)):
        cmds.select(clear=True)
        cmds.group(empty=True, name=grp)
        cmds.select(clear=True)
        j = cmds.joint(name="dup", position=(x, 0.5, 0))
        cmds.joint(name="tip", position=(x + 1.5, 0.5, 0))
        cmds.parent(j, grp)
        paths.append(cmds.ls("{0}|dup".format(grp), long=True)[0])
    cmds.select(clear=True)
    cmds.joint(name="keep", position=(0, 0, 3))
    infl = paths + ["keep"]
    skin = cmds.skinCluster(infl, mesh, toSelectedBones=True, maximumInfluences=4)[0]
    for v in range(cmds.polyEvaluate(mesh, vertex=True)):
        cmds.skinPercent(skin, "m.vtx[{0}]".format(v), transformValue=[("keep", 1.0)])
    return mesh, skin, paths


mesh, skin, paths = dup_scene()
if KT is not None:
    cmds.select("m")
    try:
        KT.floodSkinCluster(sJoints=["dup", "dup"], bDisableIslandCheck=True, xDistanceMeshes=None,
                            iCheckMissingInfluences=KTP.MissingInfluencesOptions.onlyAddMissingInfluencesInSkinCluster)
        kt_error = None
    except Exception as exc:                       # noqa: BLE001
        kt_error = exc
    check("Kangaroo flood fails with same-name joints (the bug being fixed)", kt_error is not None, kt_error)
    mesh, skin, paths = dup_scene()

cmds.select("m")
with undo_chunk():
    done, msgs = fl.flood_weights(paths, island_check=False)
check("Native flood with same-name joints runs", done == 1, msgs)
names = ["|A|dup", "|B|dup", "|keep"]
mat = matrix(skin, names)
xs = cmds.xform("m.vtx[*]", q=True, ws=True, t=True)[0::3]
left = [v for v, x in enumerate(xs) if x < -2.5]      # 경계(x = 0) 스무딩 폭 밖
right = [v for v, x in enumerate(xs) if x > 2.5]
check("left side goes to A|dup, right side to B|dup, keep is 0",
      all(mat[v][0] > 0.99 for v in left) and all(mat[v][1] > 0.99 for v in right)
      and all(abs(r[2]) < 1e-9 for r in mat) and all(abs(sum(r) - 1.0) < 1e-6 for r in mat))

# skinParent 가 같은 이름(애매)을 가리켜도 죽지 않는다
mesh, skin, paths = dup_scene()
cmds.addAttr(paths[0], ln="skinParent", dt="string")
cmds.setAttr(paths[0] + ".skinParent", "tip", type="string")
cmds.select("m")
done, msgs = fl.flood_weights(paths, island_check=False)
check("skinParent pointing at an ambiguous name does not crash", done == 1, msgs)

# 이름으로 넘어와 애매하면 건너뛴다
mesh, skin, paths = dup_scene()
cmds.select("m")
done, msgs = fl.flood_weights(["dup"], island_check=False)
check("ambiguous short name is skipped with a warning", done == 0 and any("matches 2 joints" in m for m in msgs), msgs)
done, msgs = fl.flood_weights(["A|dup"], value=0.5, island_check=False)
check("unique partial path works", done == 1, msgs)

# 같은 이름 조인트가 인플루언스가 아니면 풀패스로 추가된다
mesh, skin, paths = dup_scene()
cmds.skinCluster(skin, e=True, removeInfluence=paths[1])
cmds.select("m")
done, msgs = fl.flood_weights([paths[1]], value=0.5, island_check=False)
infl = [cmds.ls(n, long=True)[0] for n in cmds.skinCluster(skin, q=True, influence=True)]
check("missing same-name influence is added by full path", done == 1 and paths[1] in infl, msgs)

if KT is None:
    print("SKIP Kangaroo comparison (set JUN_KANGAROO_DIR)")
print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
