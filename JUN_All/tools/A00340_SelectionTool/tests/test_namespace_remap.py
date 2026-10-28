# -*- coding: utf-8 -*-
# A00340_SelectionTool v01.18 - 네임스페이스 교체 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_namespace_remap.py
# prefs 의 경로 상수는 임시 폴더로 - 실제 data/ · shared/ 를 건드리지 않는다.
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication, QDialog   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00340_SelectionTool.app.core import prefs as P   # noqa: E402
from tools.A00340_SelectionTool.app.core import namespace_map as NM   # noqa: E402

TMP = tempfile.mkdtemp(prefix="jun_a00340_ns_")
P.PREFS_DIR = os.path.join(TMP, "data")
P.PROFILES_DIR = os.path.join(P.PREFS_DIR, "profiles")
P.LOCAL_RULES_DIR = os.path.join(P.PREFS_DIR, "rules")
P.ACTIVE_PATH = os.path.join(P.PREFS_DIR, "active.json")
P.DEFAULT_SHARED_ROOT = os.path.join(TMP, "shared")
from tools.A00340_SelectionTool.app.ui import selection_tab as ST   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ================================================================ 1) 순수 로직
check("split_ns", NM.split_ns("a:b:obj") == ("a:b", "obj") and NM.split_ns("obj") == ("", "obj"))
m = {"test:ZIHAN:Cage": "test:IVI:Cage"}
check("remap exact namespace", NM.remap_name("test:ZIHAN:Cage:ctl", m) == "test:IVI:Cage:ctl")
check("remap never a partial namespace", NM.remap_name("test:ZIHAN:CageX:ctl", m) == "test:ZIHAN:CageX:ctl"
      and NM.remap_name("xtest:ZIHAN:Cage:ctl", m) == "xtest:ZIHAN:Cage:ctl")
check("remap '|' paths per segment", NM.remap_name("grp|test:ZIHAN:Cage:a|test:ZIHAN:Cage:b", m)
      == "grp|test:IVI:Cage:a|test:IVI:Cage:b")
check("remap to / from no namespace", NM.remap_name("A:x", {"A": ""}) == "x" and NM.remap_name("x", {"": "B"}) == "B:x")
check("reverse mapping (first wins)", NM.reverse_mapping({"a": "t", "b": "t"}) == {"t": "a"})
check("effective drops identity", NM.effective({"a": "a", "b": "c"}) == {"b": "c"})
data = {"categories": [{"name": "c", "buttons": [{"name": "b", "objects": ["A:x", "A:y", "z", "g|B:w"]}]}]}
check("profile_namespaces", dict(NM.profile_namespaces(data)) == {"A": 2, "": 1, "B": 1})

# ================================================================ 2) 씬 + candidates
def build_scene():
    cmds.file(new=True, force=True)
    for ns in ("A:rig", "B:rig", "C:other", "D:rig"):
        if not cmds.namespace(exists=ns.split(":")[0]):
            cmds.namespace(add=ns.split(":")[0])
        cmds.namespace(add=ns.split(":")[1], parent=ns.split(":")[0])
    for ns in ("A:rig", "B:rig"):
        for n in ("ctl1", "ctl2", "ctl3"):
            cmds.group(empty=True, name=ns + ":" + n)
    cmds.group(empty=True, name="C:other:ctl1")       # 일부만
    for n in ("p1", "p2"):                           # 두 번째 네임스페이스용
        cmds.group(empty=True, name="D:rig:" + n)
    cmds.namespace(add="E")
    for n in ("p1", "p2"):
        cmds.group(empty=True, name="E:" + n)


build_scene()
objs = ["A:rig:ctl1", "A:rig:ctl2", "A:rig:ctl3"]
cands = NM.candidates(objs, "A:rig")
check("candidates : counts and order (found 0 left out)",
      cands == [("A:rig", 3, 3), ("B:rig", 3, 3), ("C:other", 1, 3)], cands)

# ================================================================ 3) UI (한 네임스페이스 프로파일)
P.save_profile("One", {"categories": [{"name": "Body", "buttons": [{"name": "All", "objects": objs}]}]})
P.set_active("One", "local")
logs = []
tab = ST.SelectionTab(log_callback=logs.append)
app.processEvents()
items = [tab.cmb_ns.itemText(i) for i in range(tab.cmb_ns.count())]
check("ui : combo = (as saved) + candidates", items == ["(as saved)", "A:rig  (3/3)", "B:rig  (3/3)", "C:other  (1/3)"], items)
check("ui : enabled for a one-namespace profile", tab.cmb_ns.isEnabled() and tab.btn_ns_map.isEnabled())
tab.cmb_ns.setCurrentIndex(items.index("B:rig  (3/3)"))
app.processEvents()
check("ui : choosing B saves the map", P.get_namespace_map("local", "One") == {"A:rig": "B:rig"})
check("ui : highlighted while mapped", "cfe3ff" in tab.cmb_ns.styleSheet())
btn = tab._cat_boxes[0][2][0]
check("ui : button tooltip shows the remapped names", "B:rig:ctl1" in btn.toolTip() and "A:rig -> B:rig" in btn.toolTip())
cmds.select(clear=True)
del logs[:]
btn.click()
app.processEvents()
check("ui : click selects B", sorted(cmds.ls(sl=True)) == ["B:rig:ctl1", "B:rig:ctl2", "B:rig:ctl3"], cmds.ls(sl=True))
check("ui : log says via", any("via A:rig -> B:rig" in l for l in logs), logs[-1:])

# 캡처 되돌리기 : B 를 고르고 Update -> A 로 저장, 밖의 것은 그대로 + 경고
cmds.select(["B:rig:ctl1", "B:rig:ctl2", "C:other:ctl1"])
del logs[:]
tab._update_button_objects("Body", "All", append=False)
saved = P.load_profile("One")["categories"][0]["buttons"][0]["objects"]
check("capture : mapped names go back to the saved namespace", saved == ["A:rig:ctl1", "A:rig:ctl2", "C:other:ctl1"], saved)
check("capture : warns about names outside the map", any("outside the mapped" in l for l in logs), logs)
P.save_profile("One", {"categories": [{"name": "Body", "buttons": [{"name": "All", "objects": objs}]}]})

# 다시 열면 기억 / 씬에 없으면 (as saved)
tab2 = ST.SelectionTab(log_callback=logs.append)
check("ui : remembered when reopened", tab2.cmb_ns.currentData() == "B:rig")
cmds.namespace(removeNamespace="B:rig", deleteNamespaceContent=True)
del logs[:]
tab3 = ST.SelectionTab(log_callback=logs.append)
check("ui : target gone from the scene -> as saved + info",
      tab3.cmb_ns.currentIndex() == 0 and P.get_namespace_map("local", "One") == {}
      and any("not in this scene" in l for l in logs), logs)
check("ui : not highlighted when as saved", tab3.cmb_ns.styleSheet() == "")

# ================================================================ 4) 여러 네임스페이스 프로파일 + Map...
build_scene()
P.save_profile("Two", {"categories": [{"name": "c", "buttons": [
    {"name": "b", "objects": ["A:rig:ctl1", "A:rig:ctl2", "D:rig:p1", "D:rig:p2"]}]}]})
P.set_active("Two", "local")
tab4 = ST.SelectionTab(log_callback=logs.append)
check("multi : combo disabled, Map enabled", not tab4.cmb_ns.isEnabled() and tab4.btn_ns_map.isEnabled())


class _FakeDialog(object):
    def __init__(self, rows, current, parent=None):
        _FakeDialog.rows = rows

    def exec_(self):
        return QDialog.Accepted

    def mapping(self):
        return {"A:rig": "B:rig", "D:rig": "E"}


real_dialog = ST.NamespaceMapDialog
ST.NamespaceMapDialog = _FakeDialog
tab4.on_namespace_map_dialog()
ST.NamespaceMapDialog = real_dialog
check("multi : dialog gets one row per namespace with candidates",
      [r[0] for r in _FakeDialog.rows] == ["A:rig", "D:rig"] and ("E", 2, 2) in _FakeDialog.rows[1][2], _FakeDialog.rows)
check("multi : combo shows (mapped: 2) and is highlighted",
      tab4.cmb_ns.currentText() == "(mapped: 2)" and "cfe3ff" in tab4.cmb_ns.styleSheet())
cmds.select(clear=True)
tab4._cat_boxes[0][2][0].click()
app.processEvents()
check("multi : click selects both remapped namespaces",
      sorted(cmds.ls(sl=True)) == ["B:rig:ctl1", "B:rig:ctl2", "E:p1", "E:p2"], cmds.ls(sl=True))

# 실제 대화상자 : 후보 콤보 · mapping()
dlg = real_dialog([("A:rig", 2, NM.candidates(["A:rig:ctl1", "A:rig:ctl2"], "A:rig"))], {"A:rig": "B:rig"})
combo = dlg._combos[0][1]
check("dialog : keep + other candidates, current preselected",
      [combo.itemText(i) for i in range(combo.count())] == ["(keep - as saved)", "B:rig  (2/2)", "C:other  (1/2)"]
      and dlg.mapping() == {"A:rig": "B:rig"}, [combo.itemText(i) for i in range(combo.count())])

# 네임스페이스 없는 프로파일
P.save_profile("Plain", {"categories": [{"name": "c", "buttons": [{"name": "b", "objects": ["x", "y"]}]}]})
P.set_active("Plain", "local")
tab5 = ST.SelectionTab(log_callback=logs.append)
check("plain : no namespace -> combo and Map disabled", not tab5.cmb_ns.isEnabled() and not tab5.btn_ns_map.isEnabled())

# ================================================================ 5) 프로파일 Rename / Share / Delete 때 매핑 키
P.set_namespace_map("local", "Two", {"A:rig": "B:rig"})
P.rename_profile("Two", "Two2")
check("prefs : rename moves the map", P.get_namespace_map("local", "Two2") == {"A:rig": "B:rig"}
      and P.get_namespace_map("local", "Two") == {})
P.share_profile("Two2")
check("prefs : share moves the map", P.get_namespace_map("shared", "Two2") == {"A:rig": "B:rig"})
P.delete_profile("Two2", "shared")
check("prefs : delete drops the map", P.get_namespace_map("shared", "Two2") == {})

shutil.rmtree(TMP, ignore_errors=True)
print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
