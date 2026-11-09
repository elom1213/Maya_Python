# -*- coding: utf-8 -*-
# Framework.core.list_rules + TSL `Rules` 버튼 + A00145 Constrain > Constraint (Rules · Swap) 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_list_rules.py
#
# 실제 씬(C:\JUN\JUN_Src_Rig\02_Cage_v02\Cage_v002_0130.mb)이 있으면 그 세트로 개수를 확인한다(없으면 SKIP).
import io
import json
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from Framework.core import list_rules as lr   # noqa: E402
from Framework.qt import JUN_mod_tsl_qt   # noqa: E402

CAGE = r"C:\JUN\JUN_Src_Rig\02_Cage_v02\Cage_v002_0130.mb"
CAGE_COUNTS = {
    "A01_FingersMC_O_tgt_L": 19, "A02_FingersMC_X_tgt_L": 15, "A03_FingersMC_O_tgt_R": 19,
    "A04_FingersMC_X_tgt_R": 15, "B01_arm_drv_L": 4, "B02_arm_drv_R": 4, "B03_leg_drv_L": 5,
    "B04_leg_drv_R": 5, "B05_spineToHead_tgt": 11, "B06_Twist_tgt": 16,
}

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ==========================================================================
print("\n=== R1 shipped rules ===")
rules, errors = lr.load_rules()
cage = [r for r in rules if r.category == "Cage_v02"]
check("R1 no broken files", not errors, errors)
check("R1 ten Cage_v02 rules", sorted(r.name for r in cage) == sorted(CAGE_COUNTS), [r.name for r in cage])
check("R1 each rule = its set, original set order",
      all(r.sets == [r.name] and r.order == lr.ORDER_SET and r.expand_nested for r in cage))

# ==========================================================================
print("\n=== R2 loader: categories, broken json, save ===")
tmp = tempfile.mkdtemp(prefix="list_rules_")
try:
    lr.save_rule(lr.ListRule("top", ["s1"]), tmp)
    lr.save_rule(lr.ListRule("b rule/x", ["s2", "s3"], category="Cat"), tmp)
    io.open(os.path.join(tmp, "Cat", "broken.json"), "w").write(u"{ nope")
    io.open(os.path.join(tmp, "Cat", "nosets.json"), "w").write(u'{"name": "x", "sets": []}')
    got, errs = lr.load_rules(tmp)
    check("R2 two rules, top level first", [(r.category, r.name) for r in got] == [("", "top"), ("Cat", "b rule/x")],
          [(r.category, r.name) for r in got])
    check("R2 two errors reported", len(errs) == 2, errs)
    check("R2 file name sanitized", os.path.exists(os.path.join(tmp, "Cat", "b_rule_x.json")))
    try:
        lr.save_rule(lr.ListRule("top", ["s9"]), tmp)
        check("R2 save refuses overwrite", False)
    except FileExistsError:
        check("R2 save refuses overwrite", True)
    lr.save_rule(lr.ListRule("top", ["s9"]), tmp, overwrite=True)
    check("R2 overwrite", json.load(io.open(os.path.join(tmp, "top.json")))["sets"] == ["s9"])
    check("R2 categories()", [c for c, _ in lr.categories(got)] == ["", "Cat"])
finally:
    shutil.rmtree(tmp)

# ==========================================================================
print("\n=== R3 resolve: namespaces, nesting, order ===")
cmds.file(new=True, force=True)


def raw_array(set_node):
    """세트 멤버 배열(dagSetMembers -> dnSetMembers 인덱스 순)을 직접 읽는다 - 셰이프는 부모 트랜스폼 이름으로."""
    out = []
    for attr in ("dagSetMembers", "dnSetMembers"):
        for i in cmds.getAttr("{0}.{1}".format(set_node, attr), multiIndices=True) or []:
            for n in cmds.listConnections("{0}.{1}[{2}]".format(set_node, attr, i), s=True, d=False,
                                          shapes=True) or []:
                if cmds.objectType(n, isAType="shape"):
                    n = cmds.listRelatives(n, parent=True)[0]
                out.append(n)
    return out


def make(names):
    out = []
    for n in names:
        out.append(cmds.createNode("transform", name=n))
    return out


root_objs = make(["c_obj", "a_obj", "b_obj"])
cmds.sets(root_objs, name="RIG_set")
rule = lr.ListRule("RIG_set", ["RIG_set"])
check("R3 default order = set", rule.order == lr.ORDER_SET)
res = lr.resolve_rule(rule)
check("R3 original order (as made)", res.ok and res.items == ["c_obj", "a_obj", "b_obj"], res.items)
res = lr.resolve_rule(lr.ListRule("RIG_set", ["RIG_set"], order=lr.ORDER_NAME))
check("R3 order=name sorts", res.items == ["a_obj", "b_obj", "c_obj"], res.items)
# 빼고 더하기 - 뺀 자리는 비고, 더한 것은 끝에
extra = make(["d_obj", "e_obj"])
cmds.sets("d_obj", add="RIG_set")
cmds.sets("e_obj", add="RIG_set")
cmds.sets("a_obj", remove="RIG_set")
cmds.sets("a_obj", add="RIG_set")
res = lr.resolve_rule(rule)
check("R3 one-by-one add / remove keeps array order", res.items == ["c_obj", "b_obj", "d_obj", "e_obj", "a_obj"],
      res.items)
many = make(["m1", "m2", "m3", "m4"])
cmds.sets(many, name="MANY_set")
cmds.sets(make(["m5", "m6"]), add="MANY_set")
res = lr.resolve_rule(lr.ListRule("many", ["MANY_set"]))
check("R3 several added at once = whatever array Maya made", res.items == raw_array("MANY_set"),
      (res.items, raw_array("MANY_set")))
first = lr.resolve_rule(rule).items
check("R3 stable over repeated calls", all(lr.resolve_rule(rule).items == first for _ in range(5)))
cmds.sets("a_obj", remove="RIG_set")
cmds.sets(extra, remove="RIG_set")
cmds.sets("a_obj", add="RIG_set")      # 다시 c, b, a

# 네임스페이스에만 있는 세트
cmds.namespace(add="chr")
cmds.namespace(set="chr")
ns_objs = make(["z_jnt", "y_jnt"])
inner = cmds.sets(ns_objs[:1], name="INNER_set")
cmds.sets([ns_objs[1], inner], name="NS_set")
cmds.namespace(set=":")
r_ns = lr.ListRule("NS_set", ["NS_set"])
res = lr.resolve_rule(r_ns)
check("R3 set found inside a namespace", res.ok and res.used_sets == ["chr:NS_set"], res.used_sets)
check("R3 nested set expanded (DAG members, then nested set)", res.items == ["chr:y_jnt", "chr:z_jnt"], res.items)
res = lr.resolve_rule(lr.ListRule("NS_set", ["NS_set"], expand_nested=False))
check("R3 expand_nested off keeps the set", "chr:INNER_set" in res.items, res.items)

# 깊은 네임스페이스 + 같은 이름이 두 군데
cmds.namespace(add="a")
cmds.namespace(add="b", parent="a")
cmds.namespace(set="a:b")
deep = make(["q_obj"])
cmds.sets(deep, name="NS_set")
cmds.namespace(set=":")
res = lr.resolve_rule(r_ns)
check("R3 two namespaces -> ambiguous, nothing listed", not res.ok and not res.items and
      sorted(res.ambiguous["NS_set"]) == ["a:b:NS_set", "chr:NS_set"], res.ambiguous)
check("R3 rule_namespaces", lr.rule_namespaces(r_ns) == ["a:b", "chr"], lr.rule_namespaces(r_ns))
res = lr.resolve_rule(r_ns, namespace="a:b")
check("R3 pick namespace a:b", res.ok and res.items == ["a:b:q_obj"], res.items)
res = lr.resolve_rule(lr.ListRule("nope", ["NO_SUCH_set"]))
check("R3 missing set reported", res.missing == ["NO_SUCH_set"] and not res.items)
cmds.sets(name="EMPTY_set", empty=True)
res = lr.resolve_rule(lr.ListRule("e", ["EMPTY_set"]))
check("R3 empty set reported", res.empty_sets == ["EMPTY_set"] and not res.items)
res = lr.resolve_rule(lr.ListRule("two", ["RIG_set", "EMPTY_set"]))
check("R3 several sets = union", res.items == ["c_obj", "b_obj", "a_obj"], res.items)
# 짧은 이름이 겹치는 다른 세트(RIG_set2)는 잡지 않는다
cmds.sets(make(["w_obj"]), name="RIG_set2")
check("R3 exact leaf match only", lr.find_sets("RIG_set") == ["RIG_set"], lr.find_sets("RIG_set"))
# 컴포넌트 멤버
cube = cmds.polyCube(name="cmp_cube")[0]
cmds.sets(cube + ".vtx[0:1]", name="VTX_set")
res = lr.resolve_rule(lr.ListRule("v", ["VTX_set"]))
check("R3 component members kept", res.items and all(".vtx[" in i for i in res.items), res.items)
other = make(["k_obj"])
cmds.sets(other, name="MIX_set")
cmds.sets(cube + ".vtx[3]", add="MIX_set")
res = lr.resolve_rule(lr.ListRule("m", ["MIX_set"]))
check("R3 object then component", res.items == ["k_obj", "cmp_cube.vtx[3]"], res.items)
cmds.sets(cube + ".vtx[4]", name="MIX2_set")
cmds.sets(other, add="MIX2_set")
res = lr.resolve_rule(lr.ListRule("m2", ["MIX2_set"]))
check("R3 component then object", res.items == ["cmp_cube.vtx[4]", "k_obj"], res.items)

# ==========================================================================
print("\n=== R4 TSL Rules button ===")
logs = []
plain = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Plain")
check("R4 off by default (no button)", plain.btn_rules is None)
tmp = tempfile.mkdtemp(prefix="list_rules_ui_")
try:
    lr.save_rule(lr.ListRule("RIG_set", ["RIG_set"], category="Test"), tmp)
    lr.save_rule(lr.ListRule("NS_set", ["NS_set"], category="Test"), tmp)
    lr.save_rule(lr.ListRule("Missing", ["NO_SUCH_set"]), tmp)
    tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="T", show_rules=True, rules_dir=tmp,
                                            log_callback=logs.append)
    check("R4 button made", tsl.btn_rules is not None and tsl.btn_rules.text() == "Rules")
    tsl._fill_rules_menu()
    acts = tsl._rules_menu.actions()
    labels = [a.text() for a in acts]
    sub = [a for a in acts if a.menu()]
    check("R4 menu: top-level rule, category sub-menu, tools", labels[0] == "Missing" and
          "Test" in labels and "New Rules from Selected Sets..." in labels and "Open Rules Folder" in labels,
          labels)
    check("R4 sub-menu lists its rules", [a.text() for a in sub[0].menu().actions()] == ["NS_set", "RIG_set"])
    rule_rig = [r for r in tsl.load_rules() if r.name == "RIG_set"][0]
    rule_ns = [r for r in tsl.load_rules() if r.name == "NS_set"][0]
    # 메뉴 항목 클릭 = 교체
    [a for a in sub[0].menu().actions() if a.text() == "RIG_set"][0].trigger()
    check("R4 menu click lists the set (set order)", tsl.get_all_items() == ["c_obj", "b_obj", "a_obj"],
          tsl.get_all_items())
    check("R4 UUIDs attached", len(tsl.get_all_nodes()) == 3)
    # 여러 네임스페이스 -> 묻는다
    asked = []
    tsl.choose_namespace = lambda rule, spaces: (asked.append(spaces), "chr")[1]
    tsl.apply_rule(rule_ns, append=True)
    check("R4 asks namespace, appends", asked == [["a:b", "chr"]] and
          tsl.get_all_items() == ["c_obj", "b_obj", "a_obj", "chr:y_jnt", "chr:z_jnt"], tsl.get_all_items())
    tsl.choose_namespace = lambda rule, spaces: None
    before = tsl.get_all_items()
    check("R4 cancel keeps list", tsl.apply_rule(rule_ns) is None and tsl.get_all_items() == before)
    tsl.apply_rule([r for r in tsl.load_rules() if r.name == "Missing"][0])
    check("R4 missing set warns, list unchanged", tsl.get_all_items() == before and
          any("no set named 'NO_SUCH_set'" in l for l in logs), logs[-2:])
    # New Rules from Selected Sets
    cmds.select(["RIG_set", "chr:NS_set"], noExpand=True, replace=True)
    tsl.ask_category = lambda default="": "New Cat"
    saved = tsl.new_rules_from_selected_sets()
    check("R4 new rules saved (namespace stripped)", sorted(os.path.basename(p) for p in saved) ==
          ["NS_set.json", "RIG_set.json"] and all(os.sep + "New_Cat" + os.sep in p for p in saved), saved)
    tsl.confirm_overwrite = lambda names: False
    saved = tsl.new_rules_from_selected_sets()
    check("R4 existing rules kept when not confirmed", saved == [])
    cmds.select(clear=True)
    check("R4 nothing selected warns", tsl.new_rules_from_selected_sets() == [] and
          "Select one or more sets" in logs[-1])
finally:
    shutil.rmtree(tmp)

# ==========================================================================
print("\n=== R5 real scene: Cage_v002_0130.mb ===")
if not os.path.exists(CAGE):
    print("SKIP (scene not found)")
else:
    cmds.file(new=True, force=True)
    cmds.file(CAGE, reference=True, namespace="cage", loadReferenceDepth="topOnly")
    ok = True
    for rule in cage:
        res = lr.resolve_rule(rule)
        good = res.ok and len(res.items) == CAGE_COUNTS[rule.name] and \
            res.used_sets == ["cage:" + rule.name] and all(i.startswith("cage:") for i in res.items)
        ok = ok and good
        if not good:
            print("   ", rule.name, len(res.items), res.used_sets, res.missing)
    check("R5 all 10 rules through namespace 'cage:' with the right counts", ok)
    by = dict((r.name, r) for r in cage)
    res = lr.resolve_rule(by["B03_leg_drv_L"])
    check("R5 B03_leg_drv_L in original order", res.items == [
        "cage:CH_l_leg_drvjnt", "cage:CH_l_knee_drvjnt", "cage:CH_l_ankle_drvjnt",
        "cage:CH_l_foot_drvjnt", "cage:CH_l_toe_drvjnt"], res.items)
    res = lr.resolve_rule(by["A01_FingersMC_O_tgt_L"])
    check("R5 A01 in original order", res.items[:8] == [
        "cage:CH_Thumb_proxinal_l_xx_tgt", "cage:CH_Thumb_intermediate_l_xx_tgt", "cage:CH_Thumb_distal_l_xx_tgt",
        "cage:CH_Index_metacarpal_l_xx_tgt", "cage:CH_Index_proxinal_l_xx_tgt",
        "cage:CH_Index_intermediate_l_xx_tgt", "cage:CH_Index_distal_l_xx_tgt",
        "cage:CH_Middle_metacarpal_l_xx_tgt"] and res.items[-1] == "cage:CH_Lttle_distal_l_xx_tgt", res.items)
    same = True
    for rule in cage:
        node = "cage:" + rule.name
        want = []
        for i in cmds.getAttr(node + ".dagSetMembers", multiIndices=True) or []:
            want += cmds.listConnections("{0}.dagSetMembers[{1}]".format(node, i), s=True, d=False) or []
        items = lr.resolve_rule(rule).items
        same = same and items == want and all(lr.resolve_rule(rule).items == items for _ in range(3))
        if items != want:
            print("   ", rule.name, items[:3], want[:3])
    check("R5 all 10 = dagSetMembers index order, stable", same)

# ==========================================================================
print("\n=== R6 A00145 Constrain > Constraint : Rules + Swap ===")
from tools.A00145_RigConnect.app.ui.main_window import MainWindow   # noqa: E402
cmds.file(new=True, force=True)
objs = make(["t1", "t2", "f1", "f2"])
cmds.sets(objs[:2], name="TGT_set")
win = MainWindow()
check("R6 Targets / Followers have Rules", win.tsl_targets.btn_rules is not None and
      win.tsl_followers.btn_rules is not None)
win.tsl_targets.apply_rule(lr.ListRule("TGT_set", ["TGT_set"]))
win.tsl_followers.set_items(["f1", "f2"])
win.on_constraint_swap()
check("R6 Swap", win.tsl_targets.get_all_items() == ["f1", "f2"] and
      win.tsl_followers.get_all_items() == ["t1", "t2"])
check("R6 Swap button on the page", any(b.text() == "Swap" for b in win.findChildren(type(win.tsl_targets.btn_rules))
                                        if b.toolTip().startswith("Swap the two lists: Targets")))
win.close()

# ==========================================================================
print("\n=== RESULT: {0}/{1} passed ===".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
