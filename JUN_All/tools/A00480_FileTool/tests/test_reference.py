# -*- coding: utf-8 -*-
# A00480_FileTool - Reference 탭 시험 (mayapy 오프스크린, 합성 씬: leaf.ma <- mid.ma <- top, 복사 번호 · 언로드 · 없는 파일)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_reference.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00480_FileTool.app.core import reference_ops as ops   # noqa: E402
from tools.A00480_FileTool.app.ui import reference_tab as rt   # noqa: E402
from tools.A00480_FileTool.app.ui.main_window import MainWindow   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump():
    app.processEvents()
    app.processEvents()


# ---------------------------------------------------------------- scene
TMP = tempfile.mkdtemp(prefix="jun_a00480_ref_")


def save_as(name):
    path = os.path.join(TMP, name).replace("\\", "/")
    cmds.file(rename=path)
    cmds.file(save=True, type="mayaAscii")
    return path


cmds.file(new=True, force=True)
cmds.polyCube(name="leaf")
LEAF = save_as("leaf.ma")

cmds.file(new=True, force=True)
cmds.file(LEAF, reference=True, namespace="LEAF")
cmds.polySphere(name="mid")
MID = save_as("mid.ma")

cmds.file(new=True, force=True)
cmds.file(MID, reference=True, namespace="MID_A")
cmds.file(MID, reference=True, namespace="MID_B")
cmds.file(LEAF, reference=True, namespace="LEAF_TOP")
cmds.file(LEAF, reference=True, namespace="GONE")
GONE = os.path.join(TMP, "gone.ma").replace("\\", "/")
rn_gone = cmds.referenceQuery("GONE:leaf", referenceNode=True)
cmds.file(unloadReference=rn_gone)
try:
    cmds.file(GONE, loadReference=rn_gone)      # 없는 파일로 바꿔 놓는다(Missing)
except Exception:
    pass
TOP = save_as("top.ma")

# ---------------------------------------------------------------- core
rows, logs = ops.scene_references()
by_node = {r["node"]: r for r in rows}
check("C1 six references incl. nested", len(rows) == 6, [r["node"] for r in rows])
check("C2 top-level order = Reference Editor order",
      [r["node"] for r in rows if r["depth"] == 0] == ["MID_ARN", "MID_BRN", "LEAF_TOPRN", "GONERN"],
      [r["node"] for r in rows if r["depth"] == 0])
check("C3 nested rows sit right after their parent (depth 1)",
      [r["node"] for r in rows][:4] == ["MID_ARN", "MID_A:LEAFRN", "MID_BRN", "MID_B:LEAFRN"]
      and by_node["MID_A:LEAFRN"]["depth"] == 1 and by_node["MID_A:LEAFRN"]["parent"] == "MID_ARN")
check("C4 path has no copy number, copy kept apart",
      by_node["MID_BRN"]["path"] == MID and by_node["MID_BRN"]["copy"] == "{1}" and by_node["MID_ARN"]["copy"] == "",
      (by_node["MID_BRN"]["path"], by_node["MID_BRN"]["copy"]))
check("C5 namespaces without leading colon",
      by_node["MID_A:LEAFRN"]["namespace"] == "MID_A:LEAF" and by_node["LEAF_TOPRN"]["namespace"] == "LEAF_TOP")
check("C6 status Loaded / Missing",
      by_node["MID_ARN"]["status"] == "Loaded" and by_node["GONERN"]["status"] == "Missing"
      and by_node["GONERN"]["exists"] is False and by_node["GONERN"]["path"] == GONE)
check("C7 summary log", logs == ["References : 6 (nested 2, missing 1)"], logs)

rn_a = cmds.referenceQuery("MID_A:mid", referenceNode=True)
cmds.file(unloadReference=rn_a)
rows2, logs2 = ops.scene_references()
by2 = {r["node"]: r for r in rows2}
check("C8 unloaded parent: nested gone, nested_hidden flag, status Unloaded",
      len(rows2) == 5 and "MID_A:LEAFRN" not in by2 and by2["MID_ARN"]["status"] == "Unloaded"
      and by2["MID_ARN"]["nested_hidden"] is True and by2["GONERN"]["nested_hidden"] is False)
check("C9 summary counts unloaded", logs2 == ["References : 5 (nested 1, unloaded 1, missing 1)"], logs2)
cmds.file(loadReference=rn_a)

opened = []
logs3 = ops.open_reference_files([MID, MID, LEAF], opener=opened.append)
check("C10 open: duplicates once, file selected",
      opened == [os.path.normpath(MID), os.path.normpath(LEAF)] and len(logs3) == 2
      and all(l.startswith("Opened in File Explorer") for l in logs3), (opened, logs3))
opened = []
logs4 = ops.open_reference_files([GONE], opener=opened.append)
check("C11 open missing: folder instead + warning",
      opened == [os.path.normpath(TMP)] and logs4[0].startswith("[WARN] File is missing"), logs4)
logs5 = ops.open_reference_files([os.path.join(TMP, "nope", "x.ma")], opener=opened.append)
check("C12 open: no folder either -> warning only", logs5 == ["[WARN] Path does not exist on disk : {0}".format(
    os.path.normpath(os.path.join(TMP, "nope", "x.ma")))], logs5)


def boom(_p):
    raise OSError("explorer failed")


logs6 = ops.open_reference_files([MID], opener=boom)
check("C13 open: opener error -> warning, no traceback", logs6[0].startswith("[WARN] Could not open"), logs6)
check("C14 open: nothing selected", ops.open_reference_files([]) == ["[WARN] No reference selected."])

text, logs7 = ops.clipboard_text([MID, LEAF, MID])
check("C15 clipboard text: one native path per line, unique",
      text == os.path.normpath(MID) + "\n" + os.path.normpath(LEAF) and logs7 == ["Copied to clipboard : 2 paths"], (text, logs7))
text1, logs8 = ops.clipboard_text([LEAF])
check("C16 clipboard single", text1 == os.path.normpath(LEAF) and logs8 == ["Copied to clipboard : " + os.path.normpath(LEAF)])
check("C17 clipboard empty", ops.clipboard_text([]) == ("", ["[WARN] No reference selected."]))

# ---------------------------------------------------------------- UI
LOG = []
page = rt.ReferenceDefaultPage(log=LOG.append)
page.show()
pump()
tree = page.tree
check("U1 showEvent fills the tree: 4 top-level, 2 nested", tree.topLevelItemCount() == 4
      and tree.topLevelItem(0).childCount() == 1 and tree.topLevelItem(1).childCount() == 1
      and tree.topLevelItem(2).childCount() == 0)
check("U2 texts: namespace + copy, native path, status",
      tree.topLevelItem(1).text(0) == "MID_B{1}" and tree.topLevelItem(1).text(1) == os.path.normpath(MID)
      and tree.topLevelItem(1).text(2) == "Loaded" and tree.topLevelItem(3).text(2) == "Missing"
      and tree.topLevelItem(0).child(0).text(0) == "MID_A:LEAF",
      [tree.topLevelItem(i).text(0) for i in range(4)])
check("U3 nested rows are expanded", tree.topLevelItem(0).isExpanded())
check("U4 header label shows the count", page.count_label.text() == "References : 6 (nested 2, missing 1)", page.count_label.text())
check("U5 missing row is red, loaded row is not",
      tree.topLevelItem(3).foreground(0).color().name() != tree.topLevelItem(0).foreground(0).color().name())
check("U6 tooltip names the node", "MID_ARN" in tree.topLevelItem(0).toolTip(0))

tree.clearSelection()
tree.topLevelItem(0).setSelected(True)           # MID_A  (mid.ma)
tree.topLevelItem(1).setSelected(True)           # MID_B  (mid.ma{1}) - same file
tree.topLevelItem(0).child(0).setSelected(True)  # MID_A:LEAF (leaf.ma)
check("U7 selected_paths in tree order", page.selected_paths() == [MID, LEAF, MID], page.selected_paths())
LOG[:] = []
page.buttons["Copy Path"].click()
pump()
check("U8 Copy Path -> clipboard two lines (same file once)",
      QApplication.clipboard().text() == os.path.normpath(MID) + "\n" + os.path.normpath(LEAF)
      and LOG == ["Copied to clipboard : 2 paths"], (QApplication.clipboard().text(), LOG))

calls = []
real_open = ops.open_path
ops.open_path = calls.append
try:
    LOG[:] = []
    page.buttons["Open in Explorer"].click()
    check("U9 Open in Explorer -> opener per unique file", calls == [os.path.normpath(MID), os.path.normpath(LEAF)]
          and len(LOG) == 2, (calls, LOG))
    calls[:] = []
    LOG[:] = []
    page._on_double_click(tree.topLevelItem(2))
    check("U10 double-click opens that one file", calls == [os.path.normpath(LEAF)] and len(LOG) == 1, calls)
    calls[:] = []
    LOG[:] = []
    tree.clearSelection()
    page.buttons["Open in Explorer"].click()
    check("U11 nothing selected -> warning only", calls == [] and LOG == ["[WARN] No reference selected."], LOG)
finally:
    ops.open_path = real_open

cmds.file(unloadReference=rn_a)
LOG[:] = []
page.buttons["Refresh"].click()
pump()
check("U12 Refresh after unload: nested row gone, grey Unloaded",
      tree.topLevelItem(0).childCount() == 0 and tree.topLevelItem(0).text(2) == "Unloaded"
      and tree.topLevelItem(0).foreground(0).color().name() == rt.UNLOADED_COLOR
      and LOG == ["References : 5 (nested 1, unloaded 1, missing 1)"], LOG)
cmds.file(loadReference=rn_a)

page.refresh()
tree.clearSelection()
tree.topLevelItem(0).setSelected(True)             # mid.ma
tree.topLevelItem(0).child(0).setSelected(True)    # leaf.ma
menu, handlers = page.build_context_menu()
names = [a.text() for a in menu.actions() if not a.isSeparator()]
check("U13 context menu: Reveal / Copy (2 files) / Refresh, handlers wired",
      names == ["Reveal in File Explorer (2 files)", "Copy file path (2 files)", "Refresh"]
      and [handlers[a] for a in menu.actions() if not a.isSeparator()] == [page.on_open, page.on_copy, page.refresh],
      names)
tree.clearSelection()
menu, handlers = page.build_context_menu()
acts = [a for a in menu.actions() if not a.isSeparator()]
check("U13b context menu with nothing selected: Reveal / Copy disabled, Refresh enabled",
      [a.text() for a in acts] == ["Reveal in File Explorer", "Copy file path", "Refresh"]
      and [a.isEnabled() for a in acts] == [False, False, True])

cmds.file(new=True, force=True)
LOG[:] = []
page.refresh()
check("U14 empty scene: no rows + info log", tree.topLevelItemCount() == 0
      and LOG == ["[Info] No references in the current scene."] and page.count_label.text() == "No references in the current scene.", LOG)

win = MainWindow()
win.show()
pump()
labels = [win.tabs.tabText(i) for i in range(win.tabs.count())]
check("U15 main window tabs", labels == ["Export", "Import", "Path", "Reference"], labels)
check("U16 Reference sub tab Default", win.reference_tab.tabs.tabText(0) == "Default"
      and set(win.reference_tab.buttons) == {"Open in Explorer", "Copy Path", "Refresh"})
import inspect   # noqa: E402
check("U17 About mentions the tab", "[Reference > Default]" in inspect.getsource(type(win).show_about))
win.close()

# ---------------------------------------------------------------- done
shutil.rmtree(TMP, ignore_errors=True)
ok = sum(R)
print("RESULT {0} {1}/{2}".format("OK" if ok == len(R) else "FAIL", ok, len(R)))
maya.standalone.uninitialize()
os._exit(0 if ok == len(R) else 1)
