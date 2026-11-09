# -*- coding: utf-8 -*-
# A00610_PmxImporter - 파서 · 변환 · 이름 · 텍스처 시험 (마야 없이, 시스템 파이썬 또는 mayapy)
#   python test_pmx_core.py
# 실제 모델 시험은 A00610_SAMPLE_DIR(기본 Miyabi 폴더)이 있을 때만 - 모델은 저장소에 넣지 않는다.
import os
import sys
import shutil
import tempfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(os.path.dirname(HERE), "app", "core")


def _load(name):
    """app/core 모듈을 패키지(launch.py · Framework) 없이 읽는다."""
    import types
    pkg = sys.modules.get("pmxcore")
    if pkg is None:
        pkg = types.ModuleType("pmxcore")
        pkg.__path__ = [CORE]
        sys.modules["pmxcore"] = pkg
    spec = importlib.util.spec_from_file_location("pmxcore." + name, os.path.join(CORE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pmxcore." + name] = mod
    spec.loader.exec_module(mod)
    return mod


pr = _load("pmx_reader")
cv = _load("pmx_convert")
tr = _load("texture_resolver")
sys.path.insert(0, HERE)
import pmx_writer as pw  # noqa: E402

SAMPLE = os.environ.get("A00610_SAMPLE_DIR", "C:/Users/USER/Desktop/JP/0090_Avatar/0010_ZZZ/021_Miyabi")
R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    line = ("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else "")
    sys.stdout.buffer.write((line + "\n").encode("utf-8"))
    sys.stdout.flush()


def sample_model(enc=0, sizes=(2, 1, 1, 2, 1, 2), version=2.0, add_uv=2, soft=None):
    w = pw.Writer(encoding=enc, add_uv=add_uv, sizes=sizes, version=version)
    verts = [
        {"pos": (0, 0, 0), "uv": (0, 0), "type": 0, "bones": (0,)},
        {"pos": (1, 0, 0), "uv": (1, 0), "type": 1, "bones": (0, 1), "weights": (0.25,)},
        {"pos": (0, 1, 0), "uv": (0, 1), "type": 2, "bones": (0, 1, 1, -1), "weights": (0.2, 0.3, 0.3, 0.0)},
        {"pos": (1, 1, 2), "uv": (1, 1), "type": 3, "bones": (1, 0), "weights": (0.6,), "sdef": tuple(range(9))},
        {"pos": (2, 1, 0), "uv": (0.5, 0.5), "type": 4, "bones": (0, 1, 2, 3), "weights": (0.5, 0.5, 0.5, 0.5)},
    ]
    if add_uv:
        for v in verts:
            v["add_uvs"] = [(0.1, 0.2, 0.0, 0.0)] * add_uv
    data = pw.build(
        w, verts, [(0, 1, 2), (1, 3, 2), (1, 4, 3)], [u"tex\\颜.png", "toon.bmp"],
        [{"name": u"颜", "texture": 0, "faces": 2, "toon": 1},
         {"name": u"刃2", "diffuse": (1, 1, 1, 0.0), "faces": 1, "shared_toon": 3, "sphere": 1, "sphere_mode": 1}],
        [{"name": u"センター", "pos": (0, 8, 0), "parent": 3},
         {"name": u"左足", "name_e": "leg_L", "pos": (1, 10, 0.5), "parent": 0, "flags": 0x11b | 0x800,
          "append": (0, 0.5)},
         {"name": u"左足ＩＫ", "pos": (1, 1, 0), "parent": -1, "flags": 0x3e | 0x2000,
          "ik": {"target": 1, "links": [(1, True), (0, False)]}},
         {"name": u"全ての親", "pos": (0, 0, 0), "parent": -1, "flags": 0x1f, "tail": 0}],
        [{"name": u"まばたき", "type": 1, "panel": 2, "offsets": [(3, (0, 0, 1)), (0, (0, -1, 0))]},
         {"name": u"あ", "name_e": "a", "type": 1, "panel": 3, "offsets": [(4, (1, 0, 0))]},
         {"name": "grp", "type": 0, "offsets": [(0, 0.5), (1, 1.0)]},
         {"name": "bone", "type": 2, "offsets": [(1,)]},
         {"name": "uv", "type": 3, "offsets": [(0,)]},
         {"name": "uv2", "type": 5, "offsets": [(1,)]},
         {"name": "mat", "type": 8, "offsets": [(0,)]},
         {"name": "flip", "type": 9, "offsets": [(0, 1.0)]},
         {"name": "imp", "type": 10, "offsets": [(0,)]}],
        frames=[(u"表情", [(1, 0), (1, 1)]), ("Bones", [(0, 0), (0, 1)])],
        rigids=[u"頭"], joints=[u"j1", u"j2"], soft_bodies=soft)
    return pr.parse_pmx(data)


try:
    # ---------------------------------------------------------- 파서: UTF-16 / UTF-8 · 인덱스 크기 · 2.1
    for enc in (0, 1):
        for sizes in ((1, 1, 1, 1, 1, 1), (2, 1, 1, 2, 1, 2), (4, 4, 4, 4, 4, 4)):
            m = sample_model(enc=enc, sizes=sizes)
            tag = "enc{0} sizes{1}".format(enc, sizes)
            check("parse " + tag, len(m.vertices) == 5 and len(m.faces) == 3 and len(m.materials) == 2
                  and len(m.bones) == 4 and len(m.morphs) == 9 and len(m.rigids) == 1 and len(m.joints) == 2
                  and m.trailing_bytes == 0, (len(m.vertices), len(m.morphs), m.trailing_bytes))
    m = sample_model()
    check("names decoded", m.bones[0].name == u"センター" and m.materials[0].name == u"颜" and m.comment == u"comment ✔")
    check("textures raw", m.textures == [u"tex\\颜.png", "toon.bmp"])
    check("weight types", m.weight_type_counts() == {"BDEF1": 1, "BDEF2": 1, "BDEF4": 1, "SDEF": 1, "QDEF": 1},
          m.weight_type_counts())
    check("BDEF2 second weight = 1 - w", abs(m.vertices[1].weights[1] - 0.75) < 1e-6)
    check("SDEF C/R0/R1", m.vertices[3].sdef_c == (0.0, 1.0, 2.0) and m.vertices[3].sdef_r1 == (6.0, 7.0, 8.0))
    check("additional uvs", len(m.vertices[0].add_uvs) == 2 and abs(m.vertices[0].add_uvs[1][1] - 0.2) < 1e-6)
    check("material toon shared / sphere", m.materials[1].shared_toon and m.materials[1].toon == 3
          and m.materials[1].sphere == 1 and m.materials[0].toon == 1)
    check("material face ranges", m.material_face_ranges() == [(0, 2), (2, 1)])
    b = m.bones
    check("bone IK links + limits", b[2].ik.target == 1 and [l.bone for l in b[2].ik.links] == [1, 0]
          and b[2].ik.links[0].limit_min == (-1.0, 0.0, 0.0) and b[2].ik.links[1].limit_min is None)
    check("bone local axis / external parent / tail bone", b[1].local_x == (1.0, 0.0, 0.0)
          and b[2].external_parent_key == 7 and b[3].tail_bone == 0)
    check("morph types", m.morph_type_counts() == {"vertex": 2, "group": 1, "bone": 1, "uv": 1, "uv2": 1,
                                                    "material": 1, "flip": 1, "impulse": 1}, m.morph_type_counts())
    check("vertex morph offsets", m.morphs[0].offsets[0][0] == 3 and m.morphs[0].offsets[0][1] == (0.0, 0.0, 1.0))
    check("display frames", [f.name for f in m.display_frames] == [u"表情", "Bones"]
          and m.display_frames[1].items == [(0, 0), (0, 1)])
    check("rigid", m.rigids[0].name == u"頭" and m.rigids[0].shape == 2 and m.rigids[0].mode == 1
          and m.rigids[0].no_collision == 0xFFFE)
    m21 = sample_model(version=2.1, soft=0)
    check("PMX 2.1 soft body count, stops before body", m21.header.version == 2.1 and m21.soft_body_count == 0
          and m21.trailing_bytes == 16, (m21.soft_body_count, m21.trailing_bytes))
    # 정점 인덱스 1 바이트 = unsigned (200 > 127)
    w = pw.Writer(sizes=(1, 1, 1, 1, 1, 1), add_uv=0)
    verts = [{"pos": (i, 0, 0)} for i in range(201)]
    m8 = pr.parse_pmx(pw.build(w, verts, [(0, 100, 200)], [], [{"name": "a", "faces": 1}],
                               [{"name": "b", "pos": (0, 0, 0)}], []))
    check("vertex index 1 byte unsigned", m8.faces == [(0, 100, 200)], m8.faces)
    try:
        pr.parse_pmx(b"PMD something")
        check("not PMX raises", False)
    except pr.PmxError:
        check("not PMX raises", True)
    try:
        pr.parse_pmx(b"PMX " + b"\0\0\0\x40" + b"\x08")
        check("truncated raises", False)
    except pr.PmxError:
        check("truncated raises", True)

    # ---------------------------------------------------------- 변환
    check("point (x,y,-z)*8", cv.to_maya_point((1, 2, 3)) == (8, 16, -24))
    check("uv (u,1-v)", cv.to_maya_uv((0.25, 0.25)) == (0.25, 0.75))
    check("triangle reversed (c,b,a)", cv.to_maya_triangle((2, 1, 0)) == (0, 1, 2))
    check("euler mirror", cv.to_maya_euler((0.1, 0.2, 0.3)) == (-0.1, -0.2, 0.3))
    wts, fixed = cv.vertex_weights(m.vertices[2], 4)
    check("weights: same bone summed, -1 dropped, normalized", fixed and abs(wts[0] - 0.25) < 1e-6
          and abs(wts[1] - 0.75) < 1e-6, wts)
    wts, fixed = cv.vertex_weights(m.vertices[4], 4)
    check("weights: QDEF sum 2 normalized", fixed and all(abs(v - 0.25) < 1e-6 for v in wts.values()), wts)
    wts, fixed = cv.vertex_weights(m.vertices[1], 4)
    check("weights: BDEF2 untouched", not fixed and abs(wts[0] - 0.25) < 1e-6 and abs(wts[1] - 0.75) < 1e-6)
    order, parents = cv.bone_creation_order(m.bones)
    check("bone order: parent first (parent index after child)", order.index(3) < order.index(0) < order.index(1),
          order)

    class _B(object):
        def __init__(self, p):
            self.parent = p
    order, parents = cv.bone_creation_order([_B(1), _B(0), _B(5), _B(2)])
    check("bone order: cycle / self / bad parent -> root", sorted(order) == [0, 1, 2, 3] and parents[2] == -1
          and (parents[0] == -1 or parents[1] == -1) and parents[3] == 2, (order, parents))

    # ---------------------------------------------------------- 이름 (FBXASC)
    check("encode JP", cv.encode_name(u"まばたき") ==
          "FBXASC227FBXASC129FBXASC190FBXASC227FBXASC129FBXASC176FBXASC227FBXASC129FBXASC159FBXASC227FBXASC129FBXASC141")
    check("encode leading digit like FBX", cv.encode_name("1") == "FBXASC049" and cv.encode_name("a1") == "a1")
    check("encode space / dot", cv.encode_name("New MMD.x") == "NewFBXASC032MMDFBXASC046x")
    for s in (u"左足ＩＫ", u"刃2", u"体(上)", u"Mouth_↙oo_Unagi", "Chest", u"1.001", u"tex/颜"):
        check("decode(encode) round trip " + s, cv.decode_name(cv.encode_name(s)) == s)
    book = cv.NameBook(taken=lambda n: n == "Taken")
    check("name book: JP first, unique suffix", book.item_name(u"あ", "a", "m0") == "FBXASC227FBXASC129FBXASC130"
          and book.item_name(u"あ", "", "m1") == "FBXASC227FBXASC129FBXASC130_1")
    check("name book: English when JP empty, fallback when both empty",
          book.item_name("", "leg L", "b1") == "legFBXASC032L" and book.item_name("", "", "bone_007") == "bone_007")
    check("name book: avoids scene names, case-insensitive", book.unique("Taken") == "Taken_1"
          and book.unique("BONE_007") == "BONE_007_1")

    # ---------------------------------------------------------- 텍스처
    tmp = tempfile.mkdtemp(prefix="a00610_")
    try:
        os.makedirs(os.path.join(tmp, "Tex"))
        png = os.path.join(tmp, "Tex", u"颜.png")
        with open(png, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\0\0\0\x0dIHDR" + b"\0\0\0\x10\0\0\0\x10" + b"\x08\x06" + b"\0" * 20)
        rgb = os.path.join(tmp, "rgb.png")
        with open(rgb, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\0\0\0\x0dIHDR" + b"\0\0\0\x10\0\0\0\x10" + b"\x08\x02" + b"\0" * 3
                    + b"\0\0\0\0" + b"\0\0\0\x01tRNS" + b"\0" + b"\0\0\0\0" + b"\0\0\0\0IEND")
        rgb2 = os.path.join(tmp, "rgb2.png")
        with open(rgb2, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\0\0\0\x0dIHDR" + b"\0\0\0\x10\0\0\0\x10" + b"\x08\x02" + b"\0" * 3
                    + b"\0\0\0\0" + b"\0\0\0\0IEND" + b"\0" * 8)
        bmp = os.path.join(tmp, "a.bmp")
        with open(bmp, "wb") as f:
            f.write(b"BM" + b"\0" * 26 + b"\x20\x00" + b"\0" * 20)
        os.makedirs(os.path.join(tmp, "deep", "x"))
        lost = os.path.join(tmp, "deep", "x", "lost.png")
        shutil.copy(rgb2, lost)
        p, st = tr.resolve(tmp, u"Tex\\颜.png")
        check("resolve found", st == "found" and os.path.samefile(p, png), (p, st))
        p, st = tr.resolve(tmp, u"tex\\颜.png")
        check("resolve case-insensitive", st in ("found", "case") and os.path.isfile(p), st)
        p, st = tr.resolve(tmp, "elsewhere\\lost.png")
        check("resolve by file name search", st == "search" and os.path.samefile(p, lost), (p, st))
        p, st = tr.resolve(tmp, "nope.png")
        check("resolve missing", st == "missing")
        check("alpha: PNG RGBA", tr.has_alpha(png) is True)
        check("alpha: PNG RGB + tRNS", tr.has_alpha(rgb) is True)
        check("alpha: PNG RGB", tr.has_alpha(rgb2) is False)
        check("alpha: BMP 32bit", tr.has_alpha(bmp) is True)
        check("codepage cp949: 颜 unsafe, 髮 and kana safe", not tr.codepage_safe(u"C:/tex/颜.png", "cp949")
              and tr.codepage_safe(u"C:/tex/髮.png", "cp949") and tr.codepage_safe(u"C:/まばたき.png", "cp949"))
        dst = tr.ascii_copy_path(tmp, u"Tex\\颜.png")
        check("ascii copy path is ASCII + recoverable", all(ord(c) < 128 for c in os.path.basename(dst))
              and cv.decode_name(os.path.splitext(os.path.basename(dst))[0]) == u"Tex/颜", dst)
        check("copy once, then up to date", tr.copy_if_needed(png, dst) and not tr.copy_if_needed(png, dst)
              and os.path.isfile(dst))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---------------------------------------------------------- 실제 모델 (있을 때만)
    real = os.path.join(SAMPLE, "Miyabi.pmx")
    if os.path.isfile(real):
        mm = pr.read_pmx(real)
        check("Miyabi counts", (len(mm.vertices), len(mm.faces), len(mm.textures), len(mm.materials), len(mm.bones),
                                len(mm.morphs), len(mm.display_frames), len(mm.rigids), len(mm.joints), mm.trailing_bytes)
              == (27086, 33528, 9, 23, 436, 52, 14, 318, 442, 0))
        check("Miyabi weights", mm.weight_type_counts() == {"BDEF1": 8946, "BDEF2": 9515, "BDEF4": 8625,
                                                            "SDEF": 0, "QDEF": 0})
        for f, counts in ((u"武器.pmx", (4008, 4353, 3, 17, 12, 10)), (u"幽灵.pmx", (759, 1306, 1, 1, 0, 0))):
            mx = pr.read_pmx(os.path.join(SAMPLE, f))
            check("read " + f, (len(mx.vertices), len(mx.faces), len(mx.materials), len(mx.bones), len(mx.rigids),
                                len(mx.joints)) == counts and mx.trailing_bytes == 0)
    else:
        print("SKIP real model tests (no {0})".format(real))
finally:
    pass

print("\n{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
