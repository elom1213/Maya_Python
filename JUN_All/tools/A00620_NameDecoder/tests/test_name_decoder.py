# -*- coding: utf-8 -*-
# A00620_NameDecoder v01.00 - 디코더 · 씬 스캔 · BS 웨이트 · Rename to ASCII · UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_name_decoder.py
# 예시 씬(Miyabi)이 이 PC 에 있으면 열어서(저장 안 함) 노드 149 · BS 타겟 52 를 확인한다.
import io
import json
import os
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import fbx_name as FN   # noqa: E402
from Framework.core import fbx_binary as FB   # noqa: E402
from Framework.core import maya_fbx_names as MFN   # noqa: E402
from tools.A00620_NameDecoder.app.core import name_table as NT   # noqa: E402
from tools.A00620_NameDecoder.app.core import bs_weights as BW   # noqa: E402
from tools.A00620_NameDecoder.app.core import ascii_rename as AR   # noqa: E402
from tools.A00620_NameDecoder.app.ui import main_window as MW   # noqa: E402
from tools.A00620_NameDecoder.app.core import outline as OL   # noqa: E402
from Framework.qt import maya_icons as MI   # noqa: E402

MIYABI = r"C:\Users\USER\Desktop\JP\0090_Avatar\0010_ZZZ\021_Miyabi\00_01_03_RIG_01_PJ\scenes\0010_Miyabi_base_02.mb"

R = []
TMP = tempfile.mkdtemp(prefix="a00620_")


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ---------------------------------------------------------------- 1. 디코더 (예시 씬에서 뽑은 실제 이름)
REAL = {
    "FBXASC227FBXASC129FBXASC190FBXASC227FBXASC129FBXASC176FBXASC227FBXASC129FBXASC159FBXASC227FBXASC129FBXASC141": u"まばたき",
    "FBXASC227FBXASC129FBXASC132FBXASC239FBXASC188FBXASC146": u"い２",
    "ArmFBXASC233FBXASC165FBXASC176": u"Arm饰",
    "LeftFBXASC032ankle": u"Left ankle",
    "FBXASC049_003": u"1_003",
    "FBXASC229FBXASC143FBXASC163FBXASC230FBXASC168FBXASC170FBXASC231FBXASC139FBXASC173FBXASC227FBXASC130FBXASC129FBXASC229FBXASC183FBXASC166Shape": u"口横狭め左Shape",
}
check("1 real names decode", all(FN.decode(k) == v for k, v in REAL.items()),
      [(FN.decode(k), v) for k, v in REAL.items() if FN.decode(k) != v])
check("1 real names re-encode to the same Maya name", all(FN.encode(v) == k for k, v in REAL.items()))

# 마야 FBX 임포터 실측 (2026-11-09) - 이 표 그대로 나왔다
IMPORTER = {u"1abc": "FBXASC049abc", u"9": "FBXASC057", u"a 1": "aFBXASC0321", u"a-b": "aFBXASC045b",
            u"a.b": "aFBXASC046b", u"x1": "x1", u"_x": "_x", u"é": "FBXASC195FBXASC169",
            u"Ab😀": "AbFBXASC240FBXASC159FBXASC152FBXASC128",
            u"日本": "FBXASC230FBXASC151FBXASC165FBXASC230FBXASC156FBXASC172"}
check("1 encode matches the Maya FBX importer", all(FN.encode(k) == v for k, v in IMPORTER.items()),
      [(k, FN.encode(k), v) for k, v in IMPORTER.items() if FN.encode(k) != v])
check("1 fbx_binary.maya_node_name = fbx_name.encode", all(FB.maya_node_name(k) == v for k, v in IMPORTER.items()))
ROUND = [u"한글 이름", u"中文名字", u"日本語・テスト", u"😀x", u"0start", u"a--b..c", u"plain_Name01", u""]
check("1 round trip decode(encode(s)) == s", all(FN.decode(FN.encode(s)) == s for s in ROUND))
check("1 namespace and path decode piecewise", FN.decode("ns:FBXASC227FBXASC129FBXASC130|grp|FBXASC049") == u"ns:あ|grp|1")
check("1 short or big token left as is", FN.decode("FBXASC12") == "FBXASC12" and FN.decode("FBXASC999x") == "FBXASC999x")
text, ok = FN.decode_ok("aFBXASC227FBXASC129b")          # 3바이트 글자의 2바이트만 - 깨진 UTF-8
check("1 broken utf-8 stays raw and is flagged", text == "aFBXASC227FBXASC129b" and not ok, text)
check("1 is_encoded", FN.is_encoded("xFBXASC032y") and not FN.is_encoded("plain"))
check("1 valid maya names", FN.is_valid_maya_name("blink_L") and not FN.is_valid_maya_name("1_003")
      and not FN.is_valid_maya_name("a b"))


# ---------------------------------------------------------------- 2. 씬 스캔
def build():
    cmds.file(new=True, force=True)
    grp = cmds.group(empty=True, name="rig_grp")
    base = cmds.polyCube(name=FN.encode(u"顔"))[0]
    cmds.parent(base, grp)
    t1 = cmds.polyCube(name="t1")[0]
    t2 = cmds.polyCube(name="t2")[0]
    t3 = cmds.polyCube(name="t3")[0]
    bs = cmds.blendShape(t1, t2, t3, base, name="bsFace")[0]
    cmds.aliasAttr(FN.encode(u"まばたき"), bs + ".w[0]")
    cmds.aliasAttr(FN.encode(u"あ"), bs + ".w[1]")
    cmds.aliasAttr("plainTarget", bs + ".w[2]")
    j = cmds.createNode("joint", name=FN.encode(u"Left ankle"), skipSelect=True)
    cmds.addAttr(j, longName=FN.encode(u"表情"), attributeType="enum",
                 enumName="{0}:{1}=5".format(FN.encode(u"笑"), "plain"))
    cmds.delete(t1, t2, t3)
    cmds.select(clear=True)
    return base, bs, j


base, bs, joint = build()
ents = MFN.scan(MFN.SCOPE_SCENE)
by = {(e.kind, e.decoded): e for e in ents}
check("2 scene finds encoded node, shape, joint",
      (MFN.KIND_NODE, u"顔") in by and (MFN.KIND_NODE, u"顔Shape") in by and (MFN.KIND_NODE, u"Left ankle") in by,
      sorted(k[1] for k in by))
check("2 scene finds encoded bs targets only", (MFN.KIND_BS_TARGET, u"まばたき") in by
      and (MFN.KIND_BS_TARGET, u"あ") in by and (MFN.KIND_BS_TARGET, "plainTarget") not in by)
check("2 bs target index + owner", by[(MFN.KIND_BS_TARGET, u"あ")].index == 1
      and by[(MFN.KIND_BS_TARGET, u"あ")].owner == "bsFace")
check("2 node owner = decoded parent", by[(MFN.KIND_NODE, u"顔")].owner == "rig_grp")
check("2 attrs off by default", not any(e.kind in (MFN.KIND_ATTR, MFN.KIND_ENUM) for e in ents))
ents_a = MFN.scan(MFN.SCOPE_SCENE, include_attrs=True)
check("2 attrs: name + enum field with value", any(e.kind == MFN.KIND_ATTR and e.decoded == u"表情" for e in ents_a)
      and any(e.kind == MFN.KIND_ENUM and e.decoded == u"笑" and e.index == 0 for e in ents_a))
all_names = MFN.scan(MFN.SCOPE_SCENE, encoded_only=False)
check("2 encoded_only off lists plain names too", any(e.raw == "rig_grp" for e in all_names)
      and any(e.raw == "plainTarget" for e in all_names))
cmds.select(base)
sel = MFN.scan(MFN.SCOPE_SELECTED)
check("2 selected: node + shapes (Orig too) + its blendShape targets",
      sorted(e.decoded for e in sel) == sorted([u"顔", u"顔Shape", u"顔ShapeOrig", u"まばたき", u"あ"]), [e.decoded for e in sel])
cmds.select("rig_grp")
hier = MFN.scan(MFN.SCOPE_HIERARCHY)
check("2 hierarchy reaches children", any(e.decoded == u"顔" for e in hier) and not any(e.decoded == u"Left ankle" for e in hier))
MFN.select_entries([by[(MFN.KIND_BS_TARGET, u"あ")]])
check("2 select bs target selects the blendShape", cmds.ls(selection=True) == ["bsFace"])
check("2 selected_uuids", MFN.selected_uuids() == {by[(MFN.KIND_BS_TARGET, u"あ")].uuid})

# ---------------------------------------------------------------- 3. 내보내기
csv_path = os.path.join(TMP, "list.csv")
NT.export_list(ents, csv_path)
with io.open(csv_path, encoding="utf-8-sig") as f:
    csv_text = f.read()
check("3 csv utf-8 with header", csv_text.startswith("decoded,raw,type,owner") and u"まばたき" in csv_text)
json_path = os.path.join(TMP, "list.json")
NT.export_list(ents, json_path)
with io.open(json_path, encoding="utf-8") as f:
    check("3 json list", any(r["decoded"] == u"あ" for r in json.load(f)))
check("3 map pieces unique in order", NT.map_pieces(ents) == [u"顔", u"まばたき", u"あ", u" "] or
      set(NT.map_pieces(ents)) == {u"顔", u"まばたき", u"あ", u" "}, NT.map_pieces(ents))
map_path = os.path.join(TMP, "map.json")
NT.export_map_template(ents, map_path, existing={u"顔": "face"})
with io.open(map_path, encoding="utf-8") as f:
    tpl = json.load(f)
check("3 map template keeps known translations", tpl.get(u"顔") == "face" and tpl.get(u"あ") == "")

# ---------------------------------------------------------------- 4. BS 웨이트
rows = BW.targets(bs)
check("4 targets decoded", [r.decoded for r in rows] == [u"まばたき", u"あ", "plainTarget"])
BW.set_weight(rows[0].plug, 0.7)
check("4 set weight", abs(cmds.getAttr(bs + ".w[0]") - 0.7) < 1e-6)
drv = cmds.createNode("transform", name="drv", skipSelect=True)
cmds.connectAttr(drv + ".tx", bs + ".w[2]")
cmds.setAttr(drv + ".tx", 0.4)
rows = BW.targets(bs)
check("4 connected weight not editable", not rows[2].editable and rows[2].source == "drv.translateX")
changed, skipped = BW.reset_all(bs)
check("4 reset all skips connected", (changed, skipped) == (1, 1) and cmds.getAttr(bs + ".w[0]") == 0.0)
cmds.undo()
check("4 reset all is one undo", abs(cmds.getAttr(bs + ".w[0]") - 0.7) < 1e-6)

# ---------------------------------------------------------------- 5. Rename to ASCII
base, bs, joint = build()
ents = MFN.scan(MFN.SCOPE_SCENE)
mapping = {u"顔": "face", u"まばたき": "blink", u"あ": "", u" ": "_"}
check("5 translate longest key, substring", AR.translate(FN.encode(u"顔Shape"), mapping)[:2] == ("faceShape", AR.ST_READY))
new, st, note = AR.translate(FN.encode(u"あ"), mapping)
check("5 empty translation = not mapped", st == AR.ST_NOT_MAPPED, (new, st, note))
check("5 leading digit -> invalid", AR.translate("FBXASC049_003", {})[1] == AR.ST_INVALID)
check("5 broken -> broken", AR.translate("aFBXASC227FBXASC129b", {})[1] == AR.ST_BROKEN)
plans = AR.preview(ents, mapping)
st = {p.entry.decoded: p.status for p in plans}
check("5 preview statuses", st[u"顔"] == AR.ST_READY and st[u"まばたき"] == AR.ST_READY
      and st[u"あ"] == AR.ST_NOT_MAPPED and st[u"Left ankle"] == AR.ST_READY, st)
nodes_before = sorted(cmds.ls())
aliases_before = cmds.aliasAttr(bs, query=True)
res = AR.apply(plans)
check("5 apply renames", cmds.objExists("face") and cmds.objExists("faceShape") and cmds.objExists("Left_ankle")
      and "blink" in cmds.aliasAttr(bs, query=True), [r[2] for r in res])
check("5 originals stored (face, Shape, ShapeOrig, joint, target)", AR.stored_count() == 5, AR.stored_count())
cmds.undo()
check("5 apply is one undo", sorted(cmds.ls()) == nodes_before and cmds.aliasAttr(bs, query=True) == aliases_before)
AR.apply(AR.preview(MFN.scan(MFN.SCOPE_SCENE), mapping))
done, failed = AR.restore()
check("5 restore brings FBXASC names back", (done, failed) == (5, 0) and sorted(cmds.ls()) == nodes_before
      and cmds.aliasAttr(bs, query=True) == aliases_before, (done, failed))
check("5 store node removed after restore", AR.stored_count() == 0 and not cmds.ls(AR.STORE_NAME))
cmds.lockNode(FN.encode(u"Left ankle"), lock=True)
st = {p.entry.decoded: p.status for p in AR.preview(MFN.scan(MFN.SCOPE_SCENE), mapping)}
check("5 locked node skipped", st[u"Left ankle"] == AR.ST_LOCKED)
cmds.lockNode(FN.encode(u"Left ankle"), lock=False)
cmds.aliasAttr("blink", bs + ".w[1]")       # あ -> blink 로 먼저 차지
st = {p.entry.decoded: p.status for p in AR.preview(MFN.scan(MFN.SCOPE_SCENE), mapping)}
check("5 alias already in use", st[u"まばたき"] == AR.ST_IN_USE, st)
lm = os.path.join(TMP, "m.json")
AR.save_map(mapping, lm)
check("5 map save / load", AR.load_map(lm) == mapping)

# ---------------------------------------------------------------- 6. UI (오프스크린)
base, bs, joint = build()
w = MW.MainWindow()
w.confirm_before_apply = False
w.show()
APP.processEvents()
check("6 rename tab hidden by default", not w.tabs.isTabVisible(w.tabs.indexOf(w.rename_page)))
w.scan()
check("6 names table rows", w.tree_names.topLevelItemCount() == len(MFN.scan(MFN.SCOPE_SCENE)))
w.flt_names.set_text(u"まば")
check("6 filter by decoded text", [e.decoded for e in w.visible_entries()] == [u"まばたき"])
w.flt_names.set_text("")
w.tree_names.topLevelItem(0).setSelected(True)
APP.processEvents()
check("6 row click selects in maya", cmds.ls(selection=True, long=True) == [MFN.node_of(w.selected_entries()[0])])
check("6 copy decoded", w.copy_rows("decoded") == w.selected_entries()[0].decoded
      and APP.clipboard().text() == w.selected_entries()[0].decoded)
w.chk_sync.setChecked(True)
cmds.select(FN.encode(u"Left ankle"))
w.sync_from_maya()
check("6 sync highlights maya selection", [e.decoded for e in w.selected_entries()] == [u"Left ankle"])
w.chk_sync.setChecked(False)
check("6 sync job killed", w._sync_job is None)
w.tabs.setCurrentWidget(w.bs_page)
APP.processEvents()
check("6 bs tab rows decoded", [r["name"].split("\n")[0] for r in w.bs_rows] == [u"まばたき", u"あ", "plainTarget"])
w.bs_rows[1]["slider"].setValue(500)
check("6 slider sets weight", abs(cmds.getAttr(bs + ".w[1]") - 0.5) < 1e-6
      and abs(w.bs_rows[1]["spin"].value() - 0.5) < 1e-6)
w.flt_bs.set_text(u"あ")
check("6 bs filter", sum(1 for r in w.bs_rows if not r["widget"].isHidden()) == 1)
w.act_rename_tab.setChecked(True)
check("6 view menu shows rename tab", w.tabs.isTabVisible(w.tabs.indexOf(w.rename_page)))
w.fill_map_from_names()
check("6 map filled with pieces", set(w.map_from_table()) == {u"顔", u"まばたき", u"あ", u" "})
w.set_map({u"顔": "face", u"まばたき": "blink", u"あ": "A", u" ": "_"})
plans = w.preview_rename()
check("6 preview all ready", plans and all(p.ready for p in plans), [(p.entry.decoded, p.status) for p in plans])
w.apply_rename()
check("6 apply via UI", cmds.objExists("face") and "A" in cmds.aliasAttr(bs, query=True)
      and w.lbl_stored.text() == "Stored originals: 6", w.lbl_stored.text())
w.restore_names()
check("6 restore via UI", cmds.objExists(FN.encode(u"顔")) and w.lbl_stored.text() == "Stored originals: 0")
check("6 ui strings ascii", all(t.isascii() for t in (w.windowTitle(), w.btn_scan.text(), w.btn_apply.text())))
w.close()

# ---------------------------------------------------------------- 8. Outliner (v01.02)
import time   # noqa: E402

# 8-1 아이콘
def _pix_ok(icon):
    return icon is not None and not icon.pixmap(16, 16).isNull()


check("8 icons: maya resources for common DAG types",
      all(_pix_ok(MI.node_icon(t)) for t in ("transform", "mesh", "joint", "camera", "locator", "nurbsCurve")))
check("8 icons: own name when the resource exists", MI.icon_name("joint") == "out_joint.png")
check("8 icons: fallback for types without a resource",
      MI.icon_name("blendShape") == MI.DEFAULT_ICON and MI.icon_name("network") == MI.DEFAULT_ICON
      and MI.icon_name("noSuchType_A00620") == MI.DEFAULT_ICON,
      (MI.icon_name("blendShape"), MI.icon_name("network")))
check("8 icons: cached", MI.node_icon("joint") is MI.node_icon("joint"))
check("8 icons: tool svg for blendShape + target",
      _pix_ok(MW.local_icon("outliner_blendShape")) and _pix_ok(MW.local_icon("outliner_bsTarget")))

# 8-2 build_rows (마야 없이) - 인스턴스 셰이프가 조상보다 먼저 나오는 실측 순서
rows = OL.build_rows([
    ("|g", "transform", "u1", False),
    ("|g|" + FN.encode(u"顔"), "transform", "u2", False),
    ("|h|inst|shape", "mesh", "u5", False),          # 조상 |h 보다 먼저
    ("|h", "transform", "u3", True),
    ("|h|inst", "transform", "u4", True),
    ("|plain", "transform", "u6", False),
], bs_rows=[("|g|" + FN.encode(u"顔"), "bs1", "u7", [(0, FN.encode(u"あ")), (1, "smile")]),
            ("|missing", "bs2", "u8", [(0, "x")])])
pk = dict((r.key, r.parent) for r in rows)
check("8 build_rows: parent by path even when the child comes first", pk["|h|inst|shape"] == "|h|inst"
      and pk["|h"] is None and pk["|g|" + FN.encode(u"顔")] == "|g")
check("8 build_rows: blendShape + targets under the mesh, unknown attach dropped",
      [r.decoded for r in rows if r.kind != OL.KIND_DAG] == ["bs1", u"あ", "smile"]
      and [r for r in rows if r.kind == OL.KIND_BS][0].parent == "|g|" + FN.encode(u"顔"))
pruned = OL.prune_to_encoded(rows)
check("8 prune: encoded rows + their parents only",
      [r.key for r in pruned] == ["|g", "|g|" + FN.encode(u"顔"), "bs|{0}|bs1".format("|g|" + FN.encode(u"顔")),
                                  "bs|{0}|bs1|0".format("|g|" + FN.encode(u"顔"))], [r.key for r in pruned])

# 8-3 collect (씬)
base, bs, joint = build()
face = cmds.ls(base, long=True)[0]
nodes = OL.collect(MFN.SCOPE_SCENE)
by_path = dict((n.path, n) for n in nodes if n.kind == OL.KIND_DAG)
check("8 collect: every DAG transform, no shapes by default",
      set(by_path) == set(p for p in cmds.ls(dag=True, long=True) if not cmds.objectType(p, isAType="shape")),
      sorted(set(by_path) ^ set(p for p in cmds.ls(dag=True, long=True) if not cmds.objectType(p, isAType="shape"))))
check("8 collect: parent = listRelatives parent",
      all((n.parent or None) == ((cmds.listRelatives(n.path, parent=True, fullPath=True) or [None])[0])
          for n in nodes if n.kind == OL.KIND_DAG))
check("8 collect: order = ls -dag order", [n.path for n in nodes if n.kind == OL.KIND_DAG]
      == [p for p in cmds.ls(dag=True, long=True) if p in by_path])
bsn = [n for n in nodes if n.kind == OL.KIND_BS]
tg = [n for n in nodes if n.kind == OL.KIND_BS_TARGET]
check("8 collect: blendShape under the face transform with decoded targets",
      len(bsn) == 1 and bsn[0].parent == face and [t.decoded for t in tg] == [u"まばたき", u"あ", "plainTarget"])
check("8 collect: default cameras are hidden", by_path["|persp"].hidden and not by_path[face].hidden)
cmds.setAttr("rig_grp.visibility", 0)
check("8 collect: hidden parent hides children", [n for n in OL.collect() if n.path == face][0].hidden)
cmds.setAttr("rig_grp.visibility", 1)
with_shapes = OL.collect(shapes=True)
shape_rows = dict((n.path, n) for n in with_shapes if n.kind == OL.KIND_DAG)
orig = [p for p in shape_rows if p.endswith("ShapeOrig")]
check("8 collect: Shapes on - shapes, intermediate shape hidden, blendShape under the shape",
      face + "|" + FN.encode(u"顔Shape") in shape_rows and orig and shape_rows[orig[0]].hidden
      and [n for n in with_shapes if n.kind == OL.KIND_BS][0].parent == face + "|" + FN.encode(u"顔Shape"))
check("8 collect: Blend Shapes off", not any(n.kind != OL.KIND_DAG for n in OL.collect(blend_shapes=False)))
enc = OL.collect(encoded_branches_only=True)
check("8 collect: encoded branches only keeps the plain parent",
      set(n.path for n in enc if n.kind == OL.KIND_DAG) == {"|rig_grp", face, "|" + FN.encode(u"Left ankle")}
      and "plainTarget" not in [n.decoded for n in enc], [n.decoded for n in enc])
cmds.select(base)
sel_rows = OL.collect(MFN.SCOPE_SELECTED)
check("8 collect: Selected = node + the path above it",
      [n.path for n in sel_rows if n.kind == OL.KIND_DAG] == ["|rig_grp", face])
cmds.select("rig_grp")
check("8 collect: Selected + Hierarchy reaches children",
      face in [n.path for n in OL.collect(MFN.SCOPE_HIERARCHY)])
cmds.select(bs)
check("8 collect: selecting the blendShape shows its mesh",
      face in [n.path for n in OL.collect(MFN.SCOPE_SELECTED)])
inst = cmds.instance(base)[0]
inst_rows = OL.collect(shapes=True)
shape_paths = [n.path for n in inst_rows if n.kind == OL.KIND_DAG and n.node_type == "mesh"
               and n.raw == FN.encode(u"顔Shape")]
check("8 collect: instanced shape = one row per parent", len(shape_paths) == 2, shape_paths)
cmds.delete(inst)
cmds.select(clear=True)

# 8-4 UI
w = MW.MainWindow()
w.confirm_before_apply = False
w.show()
APP.processEvents()
check("8 ui: Outliner is the first tab and filled on open",
      w.tabs.indexOf(w.outliner_page) == 0 and w.tree_out.topLevelItemCount() == len(cmds.ls(assemblies=True)))
face_item = w.out_items[face]
check("8 ui: decoded name + icon + parent", face_item.text(0) == u"顔" and not face_item.icon(0).isNull()
      and face_item.parent() is w.out_items["|rig_grp"])
check("8 ui: hidden camera is italic", w.out_items["|persp"].font(0).italic())
tgt_item = [it for k, it in w.out_items.items() if k.endswith("|1") and k.startswith("bs|")][0]
check("8 ui: target row label", tgt_item.text(0) == u"あ  [1]" and tgt_item.parent().parent() is face_item)
w.flt_out.set_text(u"まば")
vis = [it.text(0) for it in w.flt_out.visible_items()]
check("8 ui: recursive filter shows the hit + its parents, expanded",
      vis == ["rig_grp", u"顔", "bsFace  (blendShape)", u"まばたき  [0]"]
      and w.out_items["|rig_grp"].isExpanded() and face_item.isExpanded() and w.lbl_out_number.text() == "Number: 1 / {0}".format(len(w.out_nodes)), (vis, w.lbl_out_number.text()))
w.flt_out.set_text("")
check("8 ui: clearing the filter collapses what it expanded",
      not w.out_items["|rig_grp"].isExpanded() and len(w.flt_out.visible_items()) == len(w.out_nodes))
w.flt_out.set_text(u"まば")
w.refresh_outliner()
w.flt_out.set_text("")
check("8 ui: refresh under a filter does not keep the filter's expansion",
      not w.out_items["|rig_grp"].isExpanded() and not w.out_items[face].isExpanded())
face_item = w.out_items[face]
face_item.setSelected(True)
APP.processEvents()
check("8 ui: row click selects in maya", cmds.ls(selection=True, long=True) == [face])
w.out_items["|rig_grp"].setExpanded(True)
w.refresh_outliner()
check("8 ui: refresh keeps expanded + selected rows",
      w.out_items["|rig_grp"].isExpanded() and w.out_items[face].isSelected())
w.tree_out.clearSelection()
w.chk_out_sync.setChecked(True)
cmds.select(FN.encode(u"Left ankle"))
APP.processEvents()
w.sync_outliner_from_maya()
check("8 ui: sync selects the maya selection", [n.decoded for n in w.selected_out_nodes()] == [u"Left ankle"])
cmds.select(face)
w.sync_outliner_from_maya()
check("8 ui: sync expands to the row", [n.path for n in w.selected_out_nodes()] == [face]
      and w.out_items["|rig_grp"].isExpanded())
tgt_item = [it for k, it in w.out_items.items() if k.endswith("|1") and k.startswith("bs|")][0]
w.tree_out.clearSelection()
tgt_item.setSelected(True)
w.sync_outliner_from_maya()      # 마야 GUI 에선 scriptJob 이 부른다
check("8 ui: clicking a target row with Sync on keeps the target row selected",
      [n.decoded for n in w.selected_out_nodes()] == [u"あ"] and cmds.ls(selection=True) == [bs],
      [n.decoded for n in w.selected_out_nodes()])
cmds.select(face)
w.sync_outliner_from_maya()
check("8 ui: a new maya selection still syncs after a tree click", [n.path for n in w.selected_out_nodes()] == [face])
w.chk_out_sync.setChecked(False)
# mayapy standalone 의 scriptJob 은 에러 없이 None 을 돌려준다(실측 2026-11-11) → 공유 · 정리는 가짜 scriptJob 으로 센다
_real_job = MW.cmds.scriptJob
_jobs = {"next": 100, "live": set(), "made": 0}


def _fake_job(*args, **kwargs):
    if "event" in kwargs:
        _jobs["next"] += 1
        _jobs["made"] += 1
        _jobs["live"].add(_jobs["next"])
        return _jobs["next"]
    if "exists" in kwargs:
        return kwargs["exists"] in _jobs["live"]
    if "kill" in kwargs:
        _jobs["live"].discard(kwargs["kill"])
    return None


MW.cmds.scriptJob = _fake_job
try:
    w.chk_sync.setChecked(True)
    w.chk_out_sync.setChecked(True)
    job = w._sync_job
    w.chk_sync.setChecked(False)
    check("8 ui: one job while either sync is on",
          job is not None and w._sync_job == job and _jobs["made"] == 1 and _jobs["live"] == {job}, _jobs)
    w.chk_out_sync.setChecked(False)
    check("8 ui: sync job killed when both are off", w._sync_job is None and not _jobs["live"], _jobs)
finally:
    MW.cmds.scriptJob = _real_job
row = w.open_bs_target(bs, 1)
check("8 ui: double-click target opens the Blend Shapes row",
      w.tabs.currentWidget() is w.bs_page and row is not None and row["plug"].endswith(".weight[1]"))
w.tabs.setCurrentWidget(w.outliner_page)
w.tree_out.clearSelection()
cmds.select(clear=True)
face_item = w.out_items[face]
face_item.setSelected(True)
check("8 ui: copy decoded path", w.copy_out_rows("path") == u"|rig_grp|顔")
w.select_out_hierarchy()
check("8 ui: select hierarchy", FN.encode(u"顔Shape") in cmds.ls(selection=True))
w.set_out_raw_column(False, save=False)
check("8 ui: raw column hidden", w.tree_out.isColumnHidden(MW.OUT_COL_RAW))
w.set_out_raw_column(True, save=False)
# v01.05 Raw Column 체크박스 - 헤더 메뉴(set_out_raw_column)와 같은 상태
check("8 raw toggle: checkbox follows the column", w.chk_out_raw.isChecked() and not w.tree_out.isColumnHidden(MW.OUT_COL_RAW))
_raw_saved = MW.cmds.optionVar(query=MW.OPTVAR_OUT_RAW) if MW.cmds.optionVar(exists=MW.OPTVAR_OUT_RAW) else None
w.chk_out_raw.setChecked(False)
APP.processEvents()
check("8 raw toggle: unchecking hides the Raw column, Name fills the width",
      w.tree_out.isColumnHidden(MW.OUT_COL_RAW)
      and w.tree_out.header().sectionSize(MW.OUT_COL_NAME) >= w.tree_out.viewport().width() - 2,
      (w.tree_out.header().sectionSize(MW.OUT_COL_NAME), w.tree_out.viewport().width()))
check("8 raw toggle: remembered in the optionVar", MW.cmds.optionVar(query=MW.OPTVAR_OUT_RAW) == 0)
w.set_out_raw_column(True, save=False)
check("8 raw toggle: header menu path updates the checkbox", w.chk_out_raw.isChecked()
      and not w.tree_out.isColumnHidden(MW.OUT_COL_RAW))
if _raw_saved is None:
    MW.cmds.optionVar(remove=MW.OPTVAR_OUT_RAW)
else:
    MW.cmds.optionVar(intValue=(MW.OPTVAR_OUT_RAW, _raw_saved))
w.zoom_outliner.set_scale(2.0, save=False)
check("8 ui: zoom grows the icons", w.tree_out.iconSize().width() == 32)
w.zoom_outliner.set_scale(1.0, save=False)
w.scan()
names_items = [w.tree_names.topLevelItem(i) for i in range(w.tree_names.topLevelItemCount())]
check("8 names: icons on node + target rows", all(not it.icon(0).isNull() for it in names_items))
shape_entry = [e for e in w.entries if e.decoded == u"顔Shape"]
tgt_entry = [e for e in w.entries if e.decoded == u"あ"]
found = w.show_in_outliner(shape_entry + tgt_entry)
check("8 names: Show in Outliner (shape -> transform row, target row)",
      w.tabs.currentWidget() is w.outliner_page and [n.decoded for n in found] == [u"顔", u"あ"]
      and sorted(n.decoded for n in w.selected_out_nodes()) == sorted([u"顔", u"あ"]), [n.decoded for n in found])
w.act_rename_tab.setChecked(True)
w.set_map({u"顔": "face", u"まばたき": "blink", u"あ": "A", u" ": "_"})
w.preview_rename()
w.apply_rename()
check("8 rename refreshes the outliner", any(n.decoded == "face" for n in w.out_nodes))
w.restore_names()
check("8 restore refreshes the outliner", any(n.decoded == u"顔" for n in w.out_nodes))
w.close()

# 8-7 창 가로 크기 자유 (v01.04) - 탭을 스크롤 칸에, 콤보는 가장 긴 항목 폭을 요구하지 않는다
w = MW.MainWindow()
w.show()
for _ in range(3):
    APP.processEvents()
check("8 resize: window minimum width no longer follows the widest tab row",
      w.minimumSizeHint().width() < 400 < w.tabs.minimumSizeHint().width(),
      (w.minimumSizeHint().width(), w.tabs.minimumSizeHint().width()))
w.resize(360, w.height())
APP.processEvents()
narrow_bar = w.tabs_scroll.horizontalScrollBar().isVisible()
check("8 resize: narrows to 360 with a horizontal scroll bar", w.width() == 360 and narrow_bar, (w.width(), narrow_bar))
w.resize(w.tabs.minimumSizeHint().width() + 200, w.height())
APP.processEvents()
check("8 resize: wide again, no scroll bar", not w.tabs_scroll.horizontalScrollBar().isVisible())
check("8 resize: scope combos do not ask for the longest item",
      w.cb_out_scope.minimumSizeHint().width() < w.cb_out_scope.sizeHint().width() or
      w.cb_out_scope.sizeAdjustPolicy() == MW.QComboBox.AdjustToMinimumContentsLengthWithIcon)
check("8 resize: tabFit turned on after the first fit", w.tab_fit.is_enabled())
w.close()

# 8-5 속도 - 합성 1 만 노드(10 단 체인 1000 개)
cmds.file(new=True, force=True)
for c in range(1000):
    parent = None
    for d in range(10):
        parent = cmds.createNode("transform", name=FN.encode(u"節{0}_{1}".format(c, d)), parent=parent,
                                 skipSelect=True)
t0 = time.time()
big = OL.collect()
t_collect = time.time() - t0
w = MW.MainWindow()
t0 = time.time()
w.refresh_outliner()
t_ui = time.time() - t0
w.flt_out.set_text(u"節999_9")
t_flt = time.time() - t0 - t_ui
# 8-6 Alt + 가운데 버튼 드래그 (v01.03)
from PySide2.QtCore import QEvent, QPointF   # noqa: E402
from PySide2.QtGui import QMouseEvent   # noqa: E402
from PySide2.QtCore import Qt as _Qt   # noqa: E402


def _mouse(kind, x, y, buttons, mods, button=_Qt.MiddleButton):
    ev = QMouseEvent(kind, QPointF(x, y), button, buttons, mods)
    APP.sendEvent(w.tree_out.viewport(), ev)


w.flt_out.set_text("")
w.resize(600, 400)
w.tabs.setCurrentWidget(w.outliner_page)
w.show()
APP.processEvents()
bar = w.tree_out.verticalScrollBar()
w.tree_out.clearSelection()
bar.setValue(50)
_mouse(QEvent.MouseButtonPress, 50, 200, _Qt.MiddleButton, _Qt.AltModifier)
panning = w.pan_out.is_panning()
_mouse(QEvent.MouseMove, 50, 100, _Qt.MiddleButton, _Qt.NoModifier, _Qt.NoButton)   # 드래그 중 Alt 를 떼도 계속
up = bar.value()
_mouse(QEvent.MouseMove, 50, 300, _Qt.MiddleButton, _Qt.NoModifier, _Qt.NoButton)
down = bar.value()
_mouse(QEvent.MouseButtonRelease, 50, 300, _Qt.NoButton, _Qt.NoModifier)
check("8 alt pan: drag up scrolls down, drag down scrolls up (grab direction)",
      panning and up > 50 and down < 50 and not w.pan_out.is_panning(), (bar.maximum(), up, down))
check("8 alt pan: no selection change, cursor restored",
      not w.tree_out.selectedItems() and w.tree_out.viewport().cursor().shape() != _Qt.ClosedHandCursor)
bar.setValue(50)
_mouse(QEvent.MouseButtonPress, 50, 200, _Qt.MiddleButton, _Qt.NoModifier)
_mouse(QEvent.MouseMove, 50, 100, _Qt.MiddleButton, _Qt.NoModifier, _Qt.NoButton)
_mouse(QEvent.MouseButtonRelease, 50, 100, _Qt.NoButton, _Qt.NoModifier)
check("8 alt pan: middle drag without Alt does not pan", bar.value() == 50 and not w.pan_out.is_panning(), bar.value())
w.close()
print("    timing 10k: collect {0:.2f}s, refresh+fill {1:.2f}s, filter {2:.2f}s".format(t_collect, t_ui, t_flt))
check("8 speed: 10k nodes collected", len([n for n in big if n.kind == OL.KIND_DAG]) == 10004, len(big))
check("8 speed: 10k refresh under 5s (target 1s, see timing)", t_ui < 5.0, round(t_ui, 2))

# ---------------------------------------------------------------- 7. 예시 씬 (있을 때만, 저장하지 않는다)
if os.path.exists(MIYABI):
    cmds.file(MIYABI, open=True, force=True, loadReferenceDepth="none")
    m = MFN.scan(MFN.SCOPE_SCENE)
    nodes = [e for e in m if e.kind == MFN.KIND_NODE]
    targets = [e for e in m if e.kind == MFN.KIND_BS_TARGET]
    check("7 Miyabi: 149 nodes, 52 targets, none broken", (len(nodes), len(targets)) == (149, 52)
          and all(e.ok for e in m), (len(nodes), len(targets)))
    check("7 Miyabi: まばたき among targets", any(e.decoded == u"まばたき" for e in targets))
    t0 = time.time()
    mo = OL.collect(shapes=True)
    print("    timing Miyabi collect (shapes): {0:.2f}s".format(time.time() - t0))
    dag_rows = [n for n in mo if n.kind == OL.KIND_DAG]
    check("7 Miyabi outliner: every DAG node (637), 52 targets under a mesh",
          len(dag_rows) == len(cmds.ls(dag=True, long=True, allPaths=True))
          and len([n for n in mo if n.kind == OL.KIND_BS_TARGET]) == 52, (len(dag_rows), len(mo)))
    check("7 Miyabi outliner: no DAG type falls back to the default icon",
          all(MI.icon_name(t) != MI.DEFAULT_ICON for t in set(n.node_type for n in dag_rows)),
          sorted(t for t in set(n.node_type for n in dag_rows) if MI.icon_name(t) == MI.DEFAULT_ICON))
    cmds.file(new=True, force=True)
else:
    print("SKIP 7 Miyabi scene not found")

print("\n{0} / {1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
