# -*- coding: utf-8 -*-
# A00610_PmxImporter - 마야 임포트 시험 (mayapy, 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_import_maya.py
#
# 1) 합성 PMX(저장소 안에서 만든다)로 임포트 · undo · 이름 · 재질 · 스킨 · 모프를 시험
# 2) 실제 모델이 있으면(A00610_SAMPLE_DIR) 기준 mb(CATS -> FBX 결과)와 숫자로 대조 - 계획서 §11-2 G1 ~ G12
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    from PySide2.QtWidgets import QApplication
except ImportError:
    from PySide6.QtWidgets import QApplication
APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402
import maya.api.OpenMaya as om  # noqa: E402
import maya.api.OpenMayaAnim as oma  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, JUN_ALL)
sys.path.insert(0, HERE)
from tools.A00610_PmxImporter.app.core import import_runner as IR  # noqa: E402
from tools.A00610_PmxImporter.app.core import pmx_reader as pr  # noqa: E402
from tools.A00610_PmxImporter.app.core import pmx_convert as cv  # noqa: E402
import pmx_writer as pw  # noqa: E402

SAMPLE = os.environ.get("A00610_SAMPLE_DIR", "C:/Users/USER/Desktop/JP/0090_Avatar/0010_ZZZ/021_Miyabi")
BASE_MB = os.path.join(SAMPLE, "00_01_03_RIG_01_PJ", "scenes", "0010_Miyabi_base_02.mb")
OUT = io.open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
R = []
TMP = tempfile.mkdtemp(prefix="a00610_maya_")


def check(name, cond, extra=""):
    R.append(bool(cond))
    OUT.write(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else "") + "\n")
    OUT.flush()


def log_sink():
    lines = []
    return lines, lines.append


def mesh_fn(name):
    sel = om.MSelectionList()
    sel.add(name)
    return om.MFnMesh(sel.getDagPath(0))


def orig_shape(transform):
    shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
    inter = [s for s in shapes if cmds.getAttr(s + ".intermediateObject")]
    return inter[0] if inter else shapes[0]


def world_points(shape):
    sel = om.MSelectionList()
    sel.add(shape)
    dag = sel.getDagPath(0)
    return om.MFnMesh(dag).getPoints(om.MSpace.kWorld)


def write_synthetic(folder):
    """텍스처 2장(하나는 RGBA, 하나는 cp949 밖 글자) + 본 3 + 모프 2 + SDEF 정점."""
    os.makedirs(os.path.join(folder, "tex"))
    import struct
    import zlib

    def png(path, rgba):
        w = h = 4
        ct = 6 if rgba else 2
        bpp = 4 if rgba else 3
        raw = b"".join(b"\0" + b"\x80" * (w * bpp) for _ in range(h))

        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    png(os.path.join(folder, "tex", u"颜.png"), True)
    png(os.path.join(folder, "tex", "body.png"), False)
    w = pw.Writer(add_uv=1)
    verts = []
    for y in range(3):
        for x in range(2):
            v = {"pos": (x, y * 2, 0.5 * x), "normal": (0, 0, -1), "uv": (x, y / 2.0), "add_uvs": [(x, y, 0, 0)]}
            if y == 0:
                v.update(type=0, bones=(1,))
            elif y == 1:
                v.update(type=3, bones=(1, 2), weights=(0.5,), sdef=(0.0,) * 9)
            else:
                v.update(type=2, bones=(2, 2, 1, -1), weights=(0.3, 0.3, 0.2, 0.0))
            verts.append(v)
    faces = [(0, 2, 1), (1, 2, 3), (2, 4, 3), (3, 4, 5)]
    data = pw.build(
        w, verts, faces, [u"tex\\颜.png", "TEX\\BODY.PNG", "missing.png"],
        [{"name": u"颜", "texture": 0, "faces": 2},
         {"name": "body", "texture": 1, "faces": 1, "diffuse": (1, 1, 1, 0.5)},
         {"name": u"刃2", "texture": 2, "faces": 1, "diffuse": (0.2, 0.4, 0.6, 0.0)}],
        [{"name": u"全ての親", "pos": (0, 0, 0)},
         {"name": u"左足", "pos": (0, 0, 0), "parent": 0, "flags": 0x11b, "append": (0, 0.5)},
         {"name": u"1", "pos": (0, 2, 0), "parent": 1, "flags": 0x11b & ~0x8, "append": (1, 0.3)},
         {"name": u"左足ＩＫ", "pos": (0, 4, 0), "parent": 0, "flags": 0x3e,
          "ik": {"target": 2, "links": [(1, True)]}}],
        [{"name": u"まばたき", "type": 1, "panel": 2, "offsets": [(5, (0, 0, 1)), (4, (0, -1, 0)), (5, (0, 0, 1))]},
         {"name": u"あ", "type": 1, "panel": 3, "offsets": [(0, (1, 0, 0))]},
         {"name": "grp", "type": 0, "offsets": [(0, 1.0)]}],
        rigids=[u"頭"], joints=[u"j"], name=u"テスト", name_e="test")
    path = os.path.join(folder, u"テスト.pmx")
    with open(path, "wb") as f:
        f.write(data)
    return path


try:
    # ================================================================= 합성 모델
    cmds.file(new=True, force=True)
    syn = write_synthetic(os.path.join(TMP, "syn"))
    lines, log = log_sink()
    res = IR.run_import(syn, IR.ImportOptions(), log=log)
    grp_name = cv.encode_name(u"テスト") + "_grp"
    check("syn: group named after PMX model name (FBXASC)", res.group == "|" + grp_name, res.group)
    check("syn: decode group name", cv.decode_name(grp_name[:-4]) == u"テスト")
    shp = cmds.listRelatives(res.mesh, shapes=True, fullPath=True)[0]
    fn = mesh_fn(shp)
    check("syn: mesh counts", (fn.numVertices, fn.numPolygons) == (6, 4))
    check("syn: winding reversed (c,b,a)", list(fn.getPolygonVertices(0)) == [1, 2, 0])
    check("syn: position (x,y,-z)*8", fn.getPoint(5, om.MSpace.kObject).isEquivalent(om.MPoint(8, 32, -4), 1e-5))
    u, v = fn.getUV(fn.getPolygonUVid(0, 0, "map1"), "map1")
    check("syn: uv (u,1-v)", abs(u - 1) < 1e-6 and abs(v - 1) < 1e-6, (u, v))
    check("syn: uv sets", list(fn.getUVSetNames()) == ["map1", "UV1"], fn.getUVSetNames())
    # getVertexNormal 은 사용자(잠긴) 노멀을 무시하고 기하 평균을 준다 - face-vertex 노멀로 읽는다
    n = om.MVector(fn.getFaceVertexNormal(0, 1, om.MSpace.kObject))
    check("syn: normal locked and converted (0,0,-1) -> (0,0,1)", n.isEquivalent(om.MVector(0, 0, 1), 1e-5)
          and fn.isNormalLocked(fn.getFaceNormalIds(0)[0]), n)
    joints = cmds.ls(res.joints)
    names = [j.split("|")[-1] for j in res.joints]
    check("syn: joint names = PMX names in FBXASC", names[2] == "FBXASC049" and names[1] == cv.encode_name(u"左足")
          and cv.decode_name(names[3]) == u"左足ＩＫ", names)
    check("syn: IK bone created by default", len(res.joints) == 4)
    check("syn: hierarchy", cmds.listRelatives(res.joints[2], parent=True, fullPath=True)[0] == res.joints[1])
    check("syn: world positions", cmds.xform(res.joints[3], q=True, ws=True, t=True) == [0.0, 32.0, 0.0])
    check("syn: invisible bone hidden", cmds.getAttr(res.joints[2] + ".drawStyle") == 2
          and cmds.getAttr(res.joints[1] + ".drawStyle") == 0)
    data = json.loads(cmds.getAttr(res.joints[3] + ".mmdData"))
    check("syn: IK data kept", data["ik"]["target"] == 2 and data["ik"]["links"][0]["bone"] == 1
          and data["ik"]["links"][0]["min"] == [-1.0, 0.0, 0.0])
    check("syn: append data kept", json.loads(cmds.getAttr(res.joints[1] + ".mmdData"))["appendRatio"] == 0.5)
    check("syn: original name attr (FBXASC)", cv.decode_name(cmds.getAttr(res.joints[3] + ".mmdName")) == u"左足ＩＫ")
    # 재질
    mats = res.materials
    sgs = cmds.ls(mats, type="shadingEngine")
    check("syn: 3 lambert + 3 SG", len(cmds.ls(mats, type="lambert")) == 3 and len(sgs) == 3)
    face_sg = cmds.ls(cmds.sets(sgs[0], q=True), flatten=True)
    check("syn: face range of material 0", sorted(face_sg) == sorted([shp.split("|")[-1] + ".f[0]",
                                                                      shp.split("|")[-1] + ".f[1]"])
          or len(face_sg) == 2, face_sg)
    files = cmds.ls(mats, type="file")
    paths = [cmds.getAttr(f + ".fileTextureName") for f in files]
    check("syn: 颜 copied to maya_textures (cp949), body found case-insensitive, missing kept",
          any("maya_textures" in p for p in paths) and any(p.lower().endswith("tex/body.png") for p in paths)
          and len(files) == 3, paths)
    m0 = cmds.ls(mats, type="lambert")[0]
    check("syn: RGBA texture -> transparency", cmds.listConnections(m0 + ".transparency", plugs=True) is not None)
    m1 = cmds.ls(mats, type="lambert")[1]
    rv = cmds.listConnections(m1 + ".transparencyR", source=True) or []
    check("syn: diffuse alpha 0.5 without texture alpha -> constant 0.5",
          not rv and abs(cmds.getAttr(m1 + ".transparencyR") - 0.5) < 1e-6)
    check("syn: hidden material warned", any("diffuse alpha 0" in l for l in lines))
    check("syn: missing texture warned", any("Missing texture: missing.png" in l for l in lines), lines)
    md = json.loads(cmds.getAttr(m0 + ".mmdData"))
    check("syn: material data kept", md["texture"] == u"tex\\颜.png" and md["edge"] is True)
    # 모프
    bs = res.blendshape
    aliases = cmds.aliasAttr(bs, q=True)[0::2]
    check("syn: morph aliases = PMX names", [cv.decode_name(a) for a in aliases] == [u"まばたき", u"あ"], aliases)
    cmds.setAttr(bs + "." + aliases[0], 1.0)
    out_pt = mesh_fn(shp).getPoint(5, om.MSpace.kObject)
    check("syn: morph duplicate offsets summed, z flipped", out_pt.isEquivalent(om.MPoint(8, 32, -4 - 16), 1e-4),
          out_pt)
    cmds.setAttr(bs + "." + aliases[0], 0.0)
    check("syn: non-vertex morph reported", any("group 1" in l for l in lines))
    hist = cmds.listHistory(shp, pruneDagObjects=True) or []
    check("syn: deformer order blendShape before skin",
          hist.index(res.skin) < hist.index(bs), [h for h in hist if h in (res.skin, bs)])
    # 스킨
    sk = oma.MFnSkinCluster(om.MSelectionList().add(res.skin).getDependNode(0))
    infl = [d.partialPathName() for d in sk.influenceObjects()]
    sel = om.MSelectionList()
    sel.add(shp)
    w, nin = sk.getWeights(sel.getDagPath(0), om.MObject())
    row2 = dict((infl[c].split("|")[-1], w[2 * nin + c]) for c in range(nin) if w[2 * nin + c] > 1e-9)
    row4 = dict((infl[c].split("|")[-1], w[4 * nin + c]) for c in range(nin) if w[4 * nin + c] > 1e-9)
    check("syn: SDEF weights", abs(row2.get(names[1], 0) - 0.5) < 1e-6 and abs(row2.get("FBXASC049", 0) - 0.5) < 1e-6,
          row2)
    check("syn: BDEF4 same bone summed + normalized", abs(row4.get("FBXASC049", 0) - 0.75) < 1e-6
          and abs(row4.get(names[1], 0) - 0.25) < 1e-6, row4)
    check("syn: only weighted bones are influences", sorted(i.split("|")[-1] for i in infl)
          == sorted([names[1], "FBXASC049"]), infl)
    check("syn: SDEF -> dual quaternion blend", cmds.getAttr(res.skin + ".skinningMethod") == 2
          and abs(cmds.getAttr(res.skin + ".blendWeights[2]") - 1.0) < 1e-6)
    rep = json.loads(cmds.getAttr(res.group + ".mmdImportReport"))
    check("syn: report", rep["not_imported"]["rigid_bodies"] == 1 and rep["skin"]["sdef"] == 2
          and rep["counts"]["morphs"] == 3, rep.get("not_imported"))
    # 문자열 어트리뷰트 = ASCII 만 (.ma 는 cp949 로 저장되어 '颜' 이 '?' 가 된다)
    strings = []
    for node in [res.group] + res.joints + res.materials + [res.blendshape]:
        for a in cmds.listAttr(node, userDefined=True) or []:
            if a.startswith("mmd") and cmds.getAttr(node + "." + a, type=True) == "string":
                strings.append(cmds.getAttr(node + "." + a) or "")
    check("syn: all mmd string attrs are ASCII (.ma safe)",
          strings and all(all(ord(c) < 128 for c in s) for s in strings),
          [s for s in strings if any(ord(c) >= 128 for c in s)][:3])
    check("syn: comment / source file decode",
          json.loads('"' + cmds.getAttr(res.group + ".mmdComment") + '"') == u"comment ✔"
          and json.loads('"' + cmds.getAttr(res.group + ".mmdSourceFile") + '"').endswith(u"テスト.pmx"))
    fa = os.path.join(TMP, "syn_roundtrip.ma")
    cmds.file(rename=fa)
    cmds.file(save=True, type="mayaAscii", force=True)
    cmds.file(fa, open=True, force=True)
    check("syn: .ma round trip keeps names + data",
          cv.decode_name(cmds.getAttr(res.joints[3] + ".mmdName")) == u"左足ＩＫ"
          and json.loads(cmds.getAttr(res.blendshape + ".mmdMorphs"))[cv.encode_name(u"あ")]["name"] == u"あ"
          and json.loads(cmds.getAttr(res.materials[0] + ".mmdData"))["texture"] == u"tex\\颜.png"
          and cmds.getAttr(res.blendshape + ".weight", size=True) == 2)

    # 다시 넣기: 이름 충돌 없이
    res2 = IR.run_import(syn, IR.ImportOptions(), log=log)
    check("syn: second import gets unique names", res2.group != res.group and res2.joints[0] != res.joints[0]
          and cmds.objExists(res2.skin), (res2.group, res2.joints[0]))
    # undo 한 번 = 임포트 통째로
    before = set(cmds.ls())
    cmds.undoInfo(state=True, infinity=True)
    cmds.flushUndo()
    res3 = IR.run_import(syn, IR.ImportOptions(), log=log)
    check("syn: import adds nodes", len(set(cmds.ls()) - before) > 20)
    cmds.undo()
    check("syn: one undo removes the whole import", set(cmds.ls()) == before, sorted(set(cmds.ls()) ^ before)[:10])
    # 네임스페이스
    res4 = IR.run_import(syn, IR.ImportOptions(namespace="mmd"), log=log)
    check("syn: namespace", res4.group.startswith("|mmd:") and all(":" in j.split("|")[-1] for j in res4.joints)
          and cmds.namespaceInfo(currentNamespace=True) == ":", res4.group)
    # 일부만
    cmds.file(new=True, force=True)
    res5 = IR.run_import(syn, IR.ImportOptions(skin=False, morphs=False, materials=False), log=log)
    check("syn: options off -> no skin/bs, initial shading", res5.skin is None and res5.blendshape is None
          and "initialShadingGroup" in (cmds.listConnections(cmds.listRelatives(res5.mesh, shapes=True)[0],
                                                             type="shadingEngine") or []))

    # ================================================================= UI
    from tools.A00610_PmxImporter.app.ui import main_window as MW
    cmds.file(new=True, force=True)
    win = MW.MainWindow()
    win.show_progress = False
    win.le_file.setText(syn)
    m = win.on_read()
    check("ui: read fills info + textures", m is not None and u"テスト" in win.lbl_info.text()
          and win.tree_tex.topLevelItemCount() == 3)
    st = [win.tree_tex.topLevelItem(i).text(1) for i in range(3)]
    check("ui: texture status (copy needed / found / missing)", st[0].startswith("Copy needed") and st[1] == "Found"
          and st[2] == "Missing", st)
    win.chk_morphs.setChecked(False)
    r = win.on_import()
    check("ui: import with options from UI", r is not None and r.blendshape is None and r.skin is not None)
    win.close()
    win2 = MW.MainWindow()
    check("ui: options remembered (optionVar)", not win2.chk_morphs.isChecked() and win2.le_file.text() == syn)
    win2.chk_morphs.setChecked(True)
    win2.save_options()
    win2.close()

    # ================================================================= 실제 모델 + 기준 mb (있을 때만)
    real = os.path.join(SAMPLE, "Miyabi.pmx")
    if os.path.isfile(real) and os.path.isfile(BASE_MB):
        cmds.file(BASE_MB, open=True, force=True, ignoreVersion=True, loadNoReferences=True)
        lines, log = log_sink()
        t0 = time.time()
        res = IR.run_import(real, IR.ImportOptions(namespace="imp"), log=log)
        dt = time.time() - t0
        check("G11 Miyabi import time < 15 s", dt < 15, "{0:.1f}s".format(dt))
        model = pr.read_pmx(real)
        shp = cmds.listRelatives(res.mesh, shapes=True, fullPath=True)
        shp = [s for s in shp if not cmds.getAttr(s + ".intermediateObject")][0]
        ours_orig = orig_shape(res.mesh)
        mine = world_points(ours_orig)
        ref = world_points("|Body|BodyShapeOrig")
        d = max(mine[i].distanceTo(ref[i]) for i in range(len(ref)))
        check("G1 positions vs base mb (CATS)", d < 1e-4, d)
        fo = mesh_fn(ours_orig)
        fr = mesh_fn("|Body|BodyShapeOrig")
        dmax = 0.0
        for setm, setr in (("map1", "UVMap"), ("UV1", "UV1"), ("UV2", "UV2")):
            u1, v1 = fo.getUVs(setm)
            u2, v2 = fr.getUVs(setr)
            # UV id 가 달라도 face-vertex 로 비교
            for f in range(0, fo.numPolygons, 3):
                for k in range(3):
                    a = fo.getPolygonUV(f, k, setm)
                    b = fr.getPolygonUV(f, k, setr)
                    dmax = max(dmax, abs(a[0] - b[0]), abs(a[1] - b[1]))
        check("G2 UVs (map1/UV1/UV2) vs base mb", dmax < 1e-6, dmax)
        same = sum(1 for f in range(fo.numPolygons)
                   if list(fo.getPolygonVertices(f)) == list(fr.getPolygonVertices(f)))
        check("G3 face vertex lists identical", same == fo.numPolygons, (same, fo.numPolygons))

        # G4 모프 델타 vs tgt_grp (이름: mb 는 FBX 가 인코딩한 PMX 이름 -> decode 로 비교)
        def dec(s):
            return cv.decode_name(s)
        ref_targets = dict((dec(t.split("|")[-1]), t) for t in (cmds.listRelatives("tgt_grp", fullPath=True) or []))
        bsn = res.blendshape
        base_pts = fr.getPoints()
        Mref = om.MMatrix(cmds.xform("Body", q=True, ws=True, m=True))
        matched = 0
        worst = 0.0
        for alias in cmds.aliasAttr(bsn, q=True)[0::2]:
            name = dec(alias.split(":")[-1])
            if name not in ref_targets:
                continue
            tp = mesh_fn(ref_targets[name]).getPoints()
            cmds.setAttr(bsn + "." + alias, 1.0)
            ours_def = world_points(shp)
            cmds.setAttr(bsn + "." + alias, 0.0)
            ours_base = world_points(shp)
            for i in range(0, len(tp)):
                exp = (tp[i] - base_pts[i]) * Mref
                got = ours_def[i] - ours_base[i]
                worst = max(worst, (exp - got).length())
            matched += 1
        check("G4 morph deltas vs base mb targets", matched >= 40 and worst < 1e-3, (matched, worst))

        # G5 스킨 웨이트 = PMX 정리 결과
        sk = oma.MFnSkinCluster(om.MSelectionList().add(res.skin).getDependNode(0))
        paths = [dg.fullPathName() for dg in sk.influenceObjects()]
        col_bone = [res.joints.index(p) for p in paths]
        sel = om.MSelectionList()
        sel.add(shp)
        w, nin = sk.getWeights(sel.getDagPath(0), om.MObject())
        worst = 0.0
        for vi, vx in enumerate(model.vertices):
            exp, _ = cv.vertex_weights(vx, len(model.bones))
            row = vi * nin
            for c in range(nin):
                worst = max(worst, abs(w[row + c] - exp.get(col_bone[c], 0.0)))
        check("G5 skin weights == PMX", worst < 1e-6, worst)
        # G6 조인트 위치
        worst = max(om.MVector(*[a - b for a, b in zip(cmds.xform(j, q=True, ws=True, t=True),
                                                     cv.to_maya_point(model.bones[i].position))]).length()
                    for i, j in enumerate(res.joints))
        check("G6 joint world positions", worst < 1e-4, worst)
        # G7 재질
        sgs = cmds.ls(res.materials, type="shadingEngine")
        counts = [len(cmds.ls(cmds.sets(sg, q=True) or [], flatten=True)) for sg in sgs]
        check("G7 23 SG, face counts = PMX", counts == [c for _s, c in model.material_face_ranges()], counts[:5])
        files = cmds.ls(res.materials, type="file")
        check("G7 all texture files load (outSize > 0)",
              all(cmds.getAttr(f + ".outSize")[0][0] > 0 for f in files) and len(files) == 5,
              [(f, cmds.getAttr(f + ".outSize")) for f in files])
        alpha_mats = [m for m in cmds.ls(res.materials, type="lambert")
                      if cmds.listConnections(m + ".transparency") or cmds.listConnections(m + ".transparencyR")]
        check("G7 transparency only on RGBA-textured materials", all(
            json.loads(cmds.getAttr(m + ".mmdData"))["texture"].split("\\")[-1] in (u"颜.png", u"髮.png", u"内.png")
            for m in alpha_mats) and len(alpha_mats) > 10, len(alpha_mats))
        # G8 바인드 포즈 = 입력
        d = max(a.distanceTo(b) for a, b in zip(world_points(shp), mine))
        check("G8 bind pose deformation == input", d < 1e-4, d)
        # G9 포즈: 왼팔꿈치 회전 -> 직접 계산한 LBS
        elbow = [j for j, b in zip(res.joints, model.bones) if b.name == u"左ひじ"][0]
        cmds.setAttr(elbow + ".rotate", 30, 60, 90, type="double3")
        bind_inv = [om.MMatrix([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0] + [-c for c in cv.to_maya_point(b.position)] + [1])
                    for b in model.bones]
        cur = [om.MMatrix(cmds.xform(j, q=True, ws=True, m=True)) for j in res.joints]
        skinned = world_points(shp)
        worst = 0.0
        moved = 0
        for vi, vx in enumerate(model.vertices):
            exp_w, _ = cv.vertex_weights(vx, len(model.bones))
            p = om.MPoint(*cv.to_maya_point(vx.position))
            acc = om.MVector()
            for b, wt in exp_w.items():
                acc += om.MVector(p * bind_inv[b] * cur[b]) * wt
            if om.MVector(p).isEquivalent(acc, 1e-3) is False:
                moved += 1
            worst = max(worst, (om.MVector(skinned[vi]) - acc).length())
        cmds.setAttr(elbow + ".rotate", 0, 0, 0, type="double3")
        check("G9 posed skin == linear blend skinning from PMX weights", worst < 1e-3 and moved > 100,
              (worst, moved))
        # G10 다른 모델
        for f, n_files in ((u"武器.pmx", 1), (u"幽灵.pmx", 0)):
            r = IR.run_import(os.path.join(SAMPLE, f), IR.ImportOptions(namespace="imp2"), log=log)
            check("G10 " + f, r.skin is not None and len(cmds.ls(r.materials, type="file")) == n_files)
        # G12 저장 -> 다시 열기
        fp = os.path.join(TMP, "roundtrip.mb")
        cmds.file(rename=fp)
        cmds.file(save=True, type="mayaBinary", force=True)
        cmds.file(fp, open=True, force=True)
        shp2 = [s for s in cmds.ls("imp:*", type="mesh", long=True) if not cmds.getAttr(s + ".intermediateObject")]
        bs2 = cmds.ls("imp:*", type="blendShape")
        ok_alias = bs2 and len(cmds.aliasAttr(bs2[0], q=True)) == 2 * 52
        a0 = cmds.aliasAttr(bs2[0], q=True)[0]
        cmds.setAttr(bs2[0] + "." + a0, 1.0)
        moved_after = cmds.getAttr(bs2[0] + "." + a0) == 1.0
        check("G12 save/reopen: 52 aliases, attrs, skin", ok_alias and moved_after
              and cmds.getAttr("imp:" + res.group.split(":")[-1] + ".mmdModelName") == "Unagi"
              and len(cmds.ls("imp:*", type="skinCluster")) == 1, (len(shp2), bs2))
    else:
        OUT.write("SKIP real model tests (no {0} or {1})\n".format(real, BASE_MB))
finally:
    shutil.rmtree(TMP, ignore_errors=True)

OUT.write("\n{0}/{1} passed\n".format(sum(R), len(R)))
OUT.flush()
os._exit(0 if all(R) else 1)
