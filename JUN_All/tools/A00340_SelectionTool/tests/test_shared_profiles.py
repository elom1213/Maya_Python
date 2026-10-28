# -*- coding: utf-8 -*-
# A00340_SelectionTool v01.17 - 공유 프로파일 · 규칙 시험 (+ v01.15 드래그 · v01.16 Add 회귀)  (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_shared_profiles.py
#
# prefs 의 경로 상수를 임시 폴더로 바꿔 **실제 data/ · shared/ 를 건드리지 않는다.**
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
import json
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication, QMessageBox   # noqa: E402
from PySide2.QtCore import Qt, QPoint, QEvent   # noqa: E402
from PySide2.QtGui import QMouseEvent, QKeyEvent   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00340_SelectionTool.app.core import prefs as P   # noqa: E402

TMP = tempfile.mkdtemp(prefix="jun_a00340_shared_")


def use_temp_paths():
    P.PREFS_DIR = os.path.join(TMP, "data")
    P.PROFILES_DIR = os.path.join(P.PREFS_DIR, "profiles")
    P.LOCAL_RULES_DIR = os.path.join(P.PREFS_DIR, "rules")
    P.ACTIVE_PATH = os.path.join(P.PREFS_DIR, "active.json")
    P.DEFAULT_SHARED_ROOT = os.path.join(TMP, "shared")


def reset():
    for name in ("data", "shared", "nas"):
        shutil.rmtree(os.path.join(TMP, name), ignore_errors=True)


use_temp_paths()
from tools.A00340_SelectionTool.app.core import select_rules as SR   # noqa: E402
from tools.A00340_SelectionTool.app.ui import selection_tab as ST   # noqa: E402
from tools.A00340_SelectionTool.app.ui import rules_tab as RT   # noqa: E402
from tools.A00340_SelectionTool.app.ui import main_window as MW   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


ASKED = []
WARNED = []
ST.QMessageBox.question = RT.QMessageBox.question = staticmethod(
    lambda *a, **k: ASKED.append(a[2]) or QMessageBox.Yes)
ST.QMessageBox.warning = staticmethod(lambda *a, **k: WARNED.append(a[2]))
OPENED = []
MW.file_opener.open_path = lambda path: OPENED.append(path)

# ================================================================ 1) prefs
reset()
check("prefs : empty -> local Default", P.get_active_ref() == ("local", "Default"))
P.save_profile("A", {"categories": [1]})
P.save_profile("A", {"categories": [2]}, "shared")
P.save_profile("S", {"categories": []}, "shared")
check("prefs : list_all order (local first)", P.list_all_profiles() ==
      [("local", "A"), ("local", "Default"), ("shared", "A"), ("shared", "S")], P.list_all_profiles())
check("prefs : same name, each scope its own file",
      P.load_profile("A")["categories"] == [1] and P.load_profile("A", "shared")["categories"] == [2])
try:
    P.share_profile("A")
    check("prefs : share blocked when shared has the name", False)
except ValueError:
    check("prefs : share blocked when shared has the name", True)
P.set_active("Default")
P.share_profile("Default")
check("prefs : share moves the file and active follows",
      ("shared", "Default") in P.list_all_profiles() and ("local", "Default") not in P.list_all_profiles()
      and P.get_active_ref() == ("shared", "Default"))
P.copy_profile_to_local("S")
check("prefs : copy to local keeps the shared one",
      ("local", "S") in P.list_all_profiles() and ("shared", "S") in P.list_all_profiles())
json.dump({"active": "A"}, open(P.ACTIVE_PATH, "w"))
check("prefs : old active.json without scope -> local", P.get_active_ref() == ("local", "A"))
P.set_active("Gone", "shared")
check("prefs : missing active corrected to the first", P.get_active_ref() == P.list_all_profiles()[0])
P.rename_profile("A", "A2", "shared")
check("prefs : rename inside shared only",
      ("shared", "A2") in P.list_all_profiles() and ("local", "A") in P.list_all_profiles())
nas = os.path.join(TMP, "nas")
os.makedirs(nas)
P.set_shared_root(nas)
check("prefs : custom shared root", P.profiles_dir("shared") == os.path.join(nas, "profiles"))
P.set_setting(P.SHARED_DIR_KEY, os.path.join(TMP, "nope"))
check("prefs : missing shared root -> default + reported",
      P.shared_root() == P.DEFAULT_SHARED_ROOT and P.shared_root_missing())
P.set_shared_root("")
check("prefs : window settings kept by set_active", P.get_setting(P.SHARED_DIR_KEY) == "")

# ================================================================ 2) rules core
reset()
r = SR.save_rule("r1", ["a"], rules_dir=P.rules_dir("local"))
s = SR.share_rule(r, P.rules_dir("shared"))
check("rules : share_rule moves", os.path.isfile(s.path) and not os.path.exists(r.path))
c = SR.copy_rule_to(s, P.rules_dir("local"))
check("rules : copy_rule_to copies", os.path.isfile(c.path) and os.path.isfile(s.path))
try:
    SR.copy_rule_to(s, P.rules_dir("local"))
    check("rules : copy clash blocked", False)
except ValueError:
    check("rules : copy clash blocked", True)

# ================================================================ 3) Buttons tab
reset()
P.save_profile("A", {"categories": [{"name": "L", "buttons": []}]})
P.save_profile("A", {"categories": [{"name": "S", "buttons": []}]}, "shared")
P.set_active("A", "local")
tab = ST.SelectionTab(log_callback=lambda m: None)
app.processEvents()
items = [tab.cmb_profile.itemText(i) for i in range(tab.cmb_profile.count())]
check("buttons : combo shows local and [Shared]", items == ["A", "A  [Shared]"], items)
check("buttons : local -> Share on, Copy off", tab.btn_share.isEnabled() and not tab.btn_copy_local.isEnabled())
tab.cmb_profile.setCurrentIndex(1)
app.processEvents()
check("buttons : picking the shared one of the same name opens it",
      [c["name"] for c in tab._data["categories"]] == ["S"] and P.get_active_ref() == ("shared", "A"))
check("buttons : shared -> title + Copy on", tab._profile_group.title() == "Profile (shared)"
      and tab.btn_copy_local.isEnabled() and not tab.btn_share.isEnabled())
tab._data["categories"].append({"name": "New", "buttons": []})
tab._save_and_render()
check("buttons : edits go to the shared file, local untouched",
      [c["name"] for c in P.load_profile("A", "shared")["categories"]] == ["S", "New"]
      and [c["name"] for c in P.load_profile("A")["categories"]] == ["L"])
del WARNED[:]
tab.on_copy_profile_to_local()
check("buttons : Copy to Local blocked when local has the name", WARNED, WARNED)
P.save_profile("B", {"categories": []})
tab._refresh_profiles()
tab.cmb_profile.setCurrentIndex([tab.cmb_profile.itemText(i) for i in range(tab.cmb_profile.count())].index("B"))
app.processEvents()
tab.on_share_profile()
check("buttons : Share moves B and stays on it", P.get_active_ref() == ("shared", "B")
      and tab.cmb_profile.currentText() == "B  [Shared]")
n = len(ASKED)
tab.on_delete_profile()
check("buttons : deleting a shared profile asks twice", len(ASKED) - n == 2 and ("shared", "B") not in P.list_all_profiles())
ST.QInputDialog.getText = staticmethod(lambda *a, **k: ("Fresh", True))
tab.on_new_profile()
check("buttons : New creates a local profile", P.get_active_ref() == ("local", "Fresh"))

# ================================================================ 4) Rules tab
reset()
L, S = os.path.join(TMP, "data", "rules"), os.path.join(TMP, "shared", "rules")
SR.save_rule("r1", ["a"], rules_dir=L)
SR.save_rule("r1", ["b"], rules_dir=S)
SR.save_rule("r2", ["c"], rules_dir=L)
rt = RT.RulesTab(log_callback=lambda m: None)          # 둘 다 None -> prefs 의 (임시) 로컬 · 공유
app.processEvents()
rows = [(rt.tree.topLevelItem(i).text(0), rt.tree.topLevelItem(i).text(1)) for i in range(rt.tree.topLevelItemCount())]
check("rules tab : Scope column, both folders", rows == [("r1", "Local"), ("r2", "Local"), ("r1", "Shared")], rows)
rt.select_rule_by_name("r1", "shared")
check("rules tab : same name picks the shared file",
      [x.objects for x in rt.selected_rules()] == [["b"]] and rt.btn_copy_local.isEnabled() and not rt.btn_share.isEnabled())
rt._ask_name = lambda *a: "r1x"
n = len(ASKED)
rt.on_rename()
check("rules tab : renaming a shared rule asks, stays in shared",
      len(ASKED) - n == 1 and sorted(os.listdir(S)) == ["r1x.json"] and "r1.json" in os.listdir(L))
rt.select_rule_by_name("r2", "local")
rt.on_share()
check("rules tab : Share moves", "r2.json" in os.listdir(S) and "r2.json" not in os.listdir(L))
rt.select_rule_by_name("r1x", "shared")
rt.on_copy_to_local()
check("rules tab : Copy to Local copies", "r1x.json" in os.listdir(L) and "r1x.json" in os.listdir(S))
n = len(ASKED)
rt.select_rule_by_name("r2", "shared")
rt.on_delete()
check("rules tab : deleting a shared rule asks twice", len(ASKED) - n == 2 and "r2.json" not in os.listdir(S))
rt2 = RT.RulesTab(log_callback=lambda m: None, rules_dir=L)
check("rules tab : rules_dir only (test mode) -> no shared", rt2.shared_dir() is None)

# ================================================================ 5) window menu
reset()
P.save_profile("Loc", {"categories": []})
P.set_setting(P.SHARED_DIR_KEY, os.path.join(TMP, "elsewhere"))
win = MW.MainWindow()
app.processEvents()
check("menu : missing shared folder warned at start", "Shared folder not found" in win.log_view.toPlainText())
nas = os.path.join(TMP, "nas")
os.makedirs(os.path.join(nas, "profiles"))
nas_json = os.path.join(nas, "profiles", "NasProf.json")
open(nas_json, "w").write('{"categories": []}')
win._apply_shared_folder(nas)
items = [win.selection_tab.cmb_profile.itemText(i) for i in range(win.selection_tab.cmb_profile.count())]
check("menu : Shared Folder... -> its profiles appear", "NasProf  [Shared]" in items, items)
win.selection_tab.cmb_profile.setCurrentIndex(items.index("NasProf  [Shared]"))
win.on_show_profile()
check("menu : Show Profile opens the shared json", OPENED and OPENED[-1] == nas_json, OPENED[-1:])
win.on_show_shared_folder()
check("menu : Show Shared Folder opens the root", OPENED[-1] == nas)
win._apply_shared_folder("")
check("menu : Use Default Shared Folder", P.shared_root() == P.DEFAULT_SHARED_ROOT
      and P.get_active_ref() == ("local", "Loc"))
pages = [win.tabs.tabText(i) for i in range(win.tabs.count())]
check("menu : tabs unchanged", pages == ["Buttons", "Rules"], pages)

# ================================================================ 6) 회귀 - 드래그 (v01.15) · Add (v01.16)
reset()
P.save_profile("D", {"categories": [
    {"name": "Body", "buttons": [{"name": n, "objects": [n]} for n in ("A", "B", "C", "D")]},
    {"name": "Face", "buttons": [{"name": n, "objects": [n]} for n in ("E", "B")]},
]}, "shared")
P.set_active("D", "shared")
tab = ST.SelectionTab(log_callback=lambda m: None)
tab.resize(320, 700)
tab.show()
for _ in range(3):
    app.processEvents()
clicked = []
tab._on_button_clicked = lambda c, n: clicked.append((c, n))
tab._render_categories()
app.processEvents()


def names():
    return [[b["name"] for b in c["buttons"]] for c in tab._data["categories"]]


def btn(cat, idx):
    return tab._cat_boxes[cat][2][idx]


def gpos(w, y_frac=0.5):
    return w.mapToGlobal(QPoint(w.width() // 2, int(w.height() * y_frac)))


def send(w, etype, g, button=Qt.LeftButton, buttons=Qt.LeftButton):
    QApplication.sendEvent(w, QMouseEvent(etype, w.mapFromGlobal(g), g, button, buttons, Qt.NoModifier))
    app.processEvents()


def drag(src, dst, cancel=False):
    start = gpos(src)
    send(src, QEvent.MouseButtonPress, start)
    send(src, QEvent.MouseMove, QPoint(start.x(), start.y() + (30 if dst.y() > start.y() else -30)), Qt.NoButton)
    send(src, QEvent.MouseMove, dst, Qt.NoButton)
    line = tab._drop_line.isVisible()
    if cancel:
        QApplication.sendEvent(src, QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
        app.processEvents()
    send(src, QEvent.MouseButtonRelease, dst, Qt.LeftButton, Qt.NoButton)
    return line


check("drag : drop line while dragging", drag(btn(0, 0), gpos(btn(0, 3), 0.1)))
check("drag : reorder inside a category", names()[0] == ["B", "C", "A", "D"], names())
check("drag : saved to the (shared) profile file",
      [b["name"] for b in P.load_profile("D", "shared")["categories"][0]["buttons"]] == ["B", "C", "A", "D"])
drag(btn(0, 3), gpos(btn(1, 0), 0.1))
check("drag : move to another category", names() == [["B", "C", "A"], ["D", "E", "B"]], names())
before = names()
del WARNED[:]
drag(btn(0, 0), gpos(btn(1, 1), 0.9))
check("drag : same name blocked", names() == before and WARNED)
before = names()
drag(btn(0, 2), gpos(btn(0, 0), 0.1), cancel=True)
check("drag : Esc cancels", names() == before and not tab._drop_line.isVisible())
b = btn(0, 1)
send(b, QEvent.MouseButtonPress, gpos(b))
send(b, QEvent.MouseButtonRelease, gpos(b), Qt.LeftButton, Qt.NoButton)
check("drag : plain click selects, drags never did", clicked == [("Body", "C")], clicked)
check("add : not inside Controls, visible when collapsed",
      not tab._controls_box.isAncestorOf(tab.chk_add) and tab.chk_add.isVisible())
tab._controls_box._header.click()
app.processEvents()
check("add : still visible after collapsing Controls", tab.chk_add.isVisible())

shutil.rmtree(TMP, ignore_errors=True)
print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
