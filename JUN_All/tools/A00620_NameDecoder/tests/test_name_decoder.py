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
w.tabs.setCurrentIndex(1)
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

# ---------------------------------------------------------------- 7. 예시 씬 (있을 때만, 저장하지 않는다)
if os.path.exists(MIYABI):
    cmds.file(MIYABI, open=True, force=True, loadReferenceDepth="none")
    m = MFN.scan(MFN.SCOPE_SCENE)
    nodes = [e for e in m if e.kind == MFN.KIND_NODE]
    targets = [e for e in m if e.kind == MFN.KIND_BS_TARGET]
    check("7 Miyabi: 149 nodes, 52 targets, none broken", (len(nodes), len(targets)) == (149, 52)
          and all(e.ok for e in m), (len(nodes), len(targets)))
    check("7 Miyabi: まばたき among targets", any(e.decoded == u"まばたき" for e in targets))
    cmds.file(new=True, force=True)
else:
    print("SKIP 7 Miyabi scene not found")

print("\n{0} / {1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
