# -*- coding: utf-8 -*-
# A00480_FileTool v01.13 - Framework.core.fbx_binary · euler_math 시험 (순수 파이썬, 마야 없이)
#   python test_fbx_core.py
# 작은 바이너리 FBX 를 테스트 안에서 직접 써서(32비트 7400 / 64비트 7700, zlib 배열) 실파일 없이 검증한다.
# 환경 변수 JUN_FBX_TEST_DIR 이 있으면 그 폴더의 실파일도 본다:
#   0010_origin/BCM_01_004.fbx (Vicon 모캡, 7700) · 0020_CHOEUN_0010.fbx (블렌더 출력, 7400)
import math
import os
import random
import struct
import sys
import tempfile
import zlib

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import fbx_binary as fb   # noqa: E402
from Framework.core import euler_math as em   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ---------------------------------------------------------------- 작은 FBX 쓰기

def _prop(v):
    if isinstance(v, bool):
        return b"C" + struct.pack("<?", v)
    if isinstance(v, int):
        return b"L" + struct.pack("<q", v) if abs(v) > 2 ** 31 - 1 else b"I" + struct.pack("<i", v)
    if isinstance(v, float):
        return b"D" + struct.pack("<d", v)
    if isinstance(v, str):
        raw = v.encode("utf-8")
        return b"S" + struct.pack("<I", len(raw)) + raw
    if isinstance(v, tuple) and v[0] in ("l", "f", "d", "i"):     # ('l', [..], zlib?)
        code, values, compress = v
        fmt = {"l": "q", "f": "f", "d": "d", "i": "i"}[code]
        raw = struct.pack("<{0}{1}".format(len(values), fmt), *values)
        data = zlib.compress(raw) if compress else raw
        return code.encode() + struct.pack("<III", len(values), 1 if compress else 0, len(data)) + data
    raise TypeError(v)


def _node(name, props=(), children=(), wide=True, offset=0):
    head_size = 25 if wide else 13
    prop_bytes = b"".join(_prop(p) for p in props)
    body_start = offset + head_size + len(name) + len(prop_bytes)
    child_bytes = b""
    for c in children:
        child_bytes += c(body_start + len(child_bytes))
    if children:
        child_bytes += b"\x00" * head_size
    end = body_start + len(child_bytes)
    fmt = "<QQQB" if wide else "<IIIB"
    return struct.pack(fmt, end, len(props), len(prop_bytes), len(name)) + name.encode() + prop_bytes + child_bytes


def N(name, props=(), children=(), wide=True):
    """오프셋을 나중에 받는 노드 생성자."""
    return lambda offset: _node(name, props, children, wide, offset)


def P(name, kind, *values, wide=True):
    return N("P", (name, kind, "", "A") + tuple(values), wide=wide)


def write_fbx(path, version, wide):
    TPS = 46186158000
    fps = 30.0
    frames = [1, 2, 3, 4]
    rx = [170.0, 179.0, -179.0, -170.0]           # ±180 을 넘는다 (래핑)
    ry = [5.0, 6.0, 7.0, 8.0]
    times = [int(f * TPS / fps) for f in frames]

    def curve(cid, values):
        return N("AnimationCurve", (cid, "AnimCurve::\x00\x01AnimCurve", ""), [
            N("Default", (0.0,), wide=wide),
            N("KeyVer", (4009,), wide=wide),
            N("KeyTime", (("l", times, True),), wide=wide),
            N("KeyValueFloat", (("f", values, False),), wide=wide),
            N("KeyAttrFlags", (("i", [0x2104], False),), wide=wide),
            N("KeyAttrRefCount", (("i", [len(values)], False),), wide=wide),
        ], wide=wide)

    objects = N("Objects", (), [
        N("Model", (10, "Rig\x00\x01Model", "Null"), [N("Properties70", (), [], wide=wide)], wide=wide),
        N("Model", (11, "ns:Hips\x00\x01Model", "LimbNode"), [N("Properties70", (), [
            P("RotationOrder", "enum", 1, wide=wide),
            P("PreRotation", "Vector3D", 10.0, 0.0, 0.0, wide=wide),
            P("Lcl Translation", "Lcl Translation", 0.0, 0.0, 5.0, wide=wide),
        ], wide=wide)], wide=wide),
        N("Model", (12, "ns:Spine-1\x00\x01Model", "LimbNode"), [N("Properties70", (), [], wide=wide)], wide=wide),
        N("Model", (13, "Marker1\x00\x01Model", "Marker"), [N("Properties70", (), [], wide=wide)], wide=wide),
        N("AnimationStack", (20, "Take\x00\x01AnimStack", ""), [N("Properties70", (), [
            P("LocalStart", "KTime", int(1 * TPS / fps), wide=wide),
            P("LocalStop", "KTime", int(4 * TPS / fps), wide=wide),
        ], wide=wide)], wide=wide),
        N("AnimationLayer", (21, "Base\x00\x01AnimLayer", ""), [], wide=wide),
        N("AnimationCurveNode", (30, "R\x00\x01AnimCurveNode", ""), [], wide=wide),
        curve(31, rx), curve(32, ry),
    ], wide=wide)
    conns = N("Connections", (), [
        N("C", ("OO", 10, 0), wide=wide), N("C", ("OO", 11, 10), wide=wide), N("C", ("OO", 12, 11), wide=wide),
        N("C", ("OO", 13, 10), wide=wide),
        N("C", ("OO", 21, 20), wide=wide), N("C", ("OO", 30, 21), wide=wide),
        N("C", ("OP", 30, 11, "Lcl Rotation"), wide=wide),
        N("C", ("OP", 31, 30, "d|X"), wide=wide), N("C", ("OP", 32, 30, "d|Y"), wide=wide),
    ], wide=wide)
    gs = N("GlobalSettings", (), [N("Properties70", (), [
        P("UpAxis", "int", 2, wide=wide), P("UnitScaleFactor", "double", 1.0, wide=wide),
        P("TimeMode", "enum", 6, wide=wide),
    ], wide=wide)], wide=wide)
    data = fb.MAGIC + b"\x1a\x00" + struct.pack("<I", version)
    for node in (gs, objects, conns):
        data += node(len(data))
    data += b"\x00" * (25 if wide else 13)
    with open(path, "wb") as handle:
        handle.write(data)
    return rx, ry


TMP = tempfile.mkdtemp(prefix="jun_fbx_core_")
for version, wide in ((7700, True), (7400, False)):
    path = os.path.join(TMP, "mini_{0}.fbx".format(version))
    rx, ry = write_fbx(path, version, wide)
    doc = fb.read(path)
    tag = "[{0}] ".format(version)
    check(tag + "version", doc.version == version, doc.version)
    check(tag + "settings", doc.settings == {"up_axis": "Z", "unit_cm": 1.0, "fps": 30.0, "start": 1.0, "stop": 4.0},
          doc.settings)
    check(tag + "counts", doc.counts == {"Null": 1, "LimbNode": 2, "Marker": 1}, doc.counts)
    check(tag + "skeleton roots", [(n, c) for _m, n, c in doc.skeleton_roots()] == [("Rig", 2)], doc.skeleton_roots())
    check(tag + "short name strips namespace", doc.models[11].short == "Hips")
    check(tag + "path_from", doc.path_from(10, 12) == ["Hips", "Spine-1"], doc.path_from(10, 12))
    check(tag + "rotation order / pre", doc.rotation_order(11) == "XZY" and doc.pre_rotation(11) == (10.0, 0.0, 0.0))
    ch = doc.channel(11, "Lcl Rotation")
    check(tag + "channel axes", sorted(ch) == ["X", "Y"], sorted(ch))
    check(tag + "frames from ticks", ch["X"].frames == [1.0, 2.0, 3.0, 4.0], ch["X"].frames)
    check(tag + "values (zlib times, raw values)", [round(v, 3) for v in ch["X"].values] == rx)
    check(tag + "interp linear", ch["X"].interp_kind() == "linear")
    check(tag + "value_at linear", abs(ch["Y"].value_at(2.5) - 6.5) < 1e-9 and ch["Y"].value_at(99) == 8.0)
    check(tag + "value_at static axis", doc.value_at(11, "Lcl Rotation", 2.0)[2] == 0.0)
    check(tag + "static translation", doc.static(11, "Lcl Translation") == (0.0, 0.0, 5.0))
    check(tag + "no channel -> {}", doc.channel(12, "Lcl Rotation") == {})

check("maya_node_name keeps [A-Za-z0-9_]", fb.maya_node_name("Hips_01") == "Hips_01")
check("maya_node_name encodes others", fb.maya_node_name("Spine-1") == "SpineFBXASC0451", fb.maya_node_name("Spine-1"))
bad_path = os.path.join(TMP, "ascii.fbx")
with open(bad_path, "wb") as handle:
    handle.write(b"; FBX 7.4.0 project file\nFBXHeaderExtension:  {\n}\n")
try:
    fb.read(bad_path)
    check("ASCII FBX refused", False)
except fb.FbxError as exc:
    check("ASCII FBX refused", "ASCII" in str(exc), exc)

# ---------------------------------------------------------------- euler_math

random.seed(7)
ORDERS = ["XYZ", "XZY", "YZX", "YXZ", "ZXY", "ZYX"]
worst = 0.0
for order in ORDERS:
    for _ in range(200):
        v = [random.uniform(-400, 400) for _ in range(3)]
        worst = max(worst, em.angle_between(em.matrix(v, order), em.matrix(em.alternate(v, order), order)))
check("alternate keeps the pose for all 6 orders", worst < 1e-9, worst)

# XYZ 꼴 동치를 XZY 에 쓰면 자세가 바뀐다 (마야 임포터 버그의 재현) - RightArm f3707 실측값
truth = (3.472, 34.422, 88.554)
maya = (543.472, -574.422, -91.446)
check("XYZ formula on XZY joint changes the pose (Maya bug)",
      em.angle_between(em.matrix(truth, "XZY"), em.matrix(maya, "XZY")) > 170)
check("Maya value == XYZ alternate of truth", em.same_angles(maya, em.alternate(truth, "XYZ")))

xs = [((i * 7.3) % 360.0) - 180.0 for i in range(500)]
ys = [10.0 * math.sin(i / 40.0) for i in range(500)]
zs = [3.0] * 500
ux, uy, uz = em.unwrap_triples(xs, ys, zs, "XZY")
check("unwrap_triples removes jumps", em.count_jumps(xs) > 0 and em.count_jumps(ux) == 0,
      (em.count_jumps(xs), em.count_jumps(ux)))
check("unwrap_triples keeps the pose", max(em.angle_between(em.matrix(a, "XZY"), em.matrix(b, "XZY"))
                                            for a, b in zip(zip(xs, ys, zs), zip(ux, uy, uz))) < 1e-9)
check("unwrap_single", em.count_jumps(em.unwrap_single(xs)) == 0)

worst = 0.0
for order in ORDERS:
    jo = [random.uniform(-90, 90) for _ in range(3)]
    ra = [random.uniform(-30, 30) for _ in range(3)]
    for gimbal in (False, True):
        a = [random.uniform(-300, 300) for _ in range(100)]
        b = [random.uniform(-0.05, 0.05) if gimbal else random.uniform(-300, 300) for _ in range(100)]
        c = [random.uniform(-0.05, 0.05) if gimbal else random.uniform(-300, 300) for _ in range(100)]
        j = [0.0, 90.0, 0.0] if gimbal else jo
        nx, ny, nz = em.normalize_xyz(a, b, c, order, j, ra)
        for i in range(100):
            want = em.mat_mul(em.mat_mul(em.matrix(j, "XYZ"), em.matrix((a[i], b[i], c[i]), order)), em.matrix(ra, "XYZ"))
            worst = max(worst, em.angle_between(want, em.matrix((nx[i], ny[i], nz[i]), "XYZ")))
check("normalize_xyz keeps the pose (incl. near gimbal)", worst < 1e-8, worst)

# ---------------------------------------------------------------- 실파일 (있으면)

real = os.environ.get("JUN_FBX_TEST_DIR")
if real and os.path.isdir(real):
    bcm = os.path.join(real, "0010_origin", "BCM_01_004.fbx")
    if os.path.isfile(bcm):
        doc = fb.read(bcm)
        check("[BCM] 7700 Z-up 60fps 1-6285", doc.version == 7700 and doc.settings["up_axis"] == "Z"
              and doc.settings["fps"] == 60.0 and (doc.settings["start"], doc.settings["stop"]) == (1.0, 6285.0),
              doc.settings)
        check("[BCM] 5 skeletons x 73", [(n, c) for _m, n, c in doc.skeleton_roots()] ==
              [(n, 73) for n in ("CHOEUN", "SUA", "ZHAN", "IVI", "KANA")])
        check("[BCM] counts", doc.counts == {"Null": 11, "Camera": 67, "Marker": 390, "LimbNode": 365}, doc.counts)
        orders = {}
        for mid, m in doc.models.items():
            if m.kind == "LimbNode":
                orders[doc.rotation_order(mid)] = orders.get(doc.rotation_order(mid), 0) + 1
        check("[BCM] rotation orders", orders == {"XYZ": 175, "XZY": 130, "ZXY": 40, "YZX": 10, "ZYX": 10}, orders)
    blender = os.path.join(real, "0020_CHOEUN_0010.fbx")
    if os.path.isfile(blender):
        doc = fb.read(blender)
        check("[Blender] 7400 Y-up, 1 skeleton x 86", doc.version == 7400 and doc.settings["up_axis"] == "Y"
              and [(n, c) for _m, n, c in doc.skeleton_roots()] == [("CHOEUN", 86)])
else:
    print("SKIP real files (set JUN_FBX_TEST_DIR)")

print("\n{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
