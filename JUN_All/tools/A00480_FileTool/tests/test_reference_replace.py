# -*- coding: utf-8 -*-
# A00480_FileTool v01.21 - Reference > Default `Replace...` 시험 (mayapy 오프스크린)
#   합성 씬: top <- mid.ma(<- leaf.ma 중첩) · leaf.ma(로드, 컨스트레인트 걸림) · leaf.ma(언로드)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_reference_replace.py
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

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


TMP = tempfile.mkdtemp(prefix="jun_a00480_rep_").replace("\\", "/")


def save_as(name):
    path = TMP + "/" + name
    cmds.file(rename=path)
    cmds.file(save=True, type="mayaAscii")
    return path


def fname(node):
    return cmds.referenceQuery(node, filename=True, withoutCopyNumber=True)


def build():
    cmds.file(new=True, force=True)
    cmds.file(MID, reference=True, namespace="MID_A")
    cmds.file(LEAF, reference=True, namespace="TOPL")
    cmds.file(LEAF, reference=True, namespace="UNL")
    cmds.file(unloadReference="UNLRN")
    cmds.polyCube(name="driver")
    cmds.parentConstraint("driver", "TOPL:leaf")
    return save_as("top.ma")


cmds.file(new=True, force=True)
cmds.polyCube(name="leaf")
LEAF = save_as("leaf.ma")
cmds.file(new=True, force=True)
cmds.polyCone(name="leaf")
LEAF2 = save_as("leaf2.ma")
cmds.file(new=True, force=True)
cmds.file(LEAF, reference=True, namespace="LEAF")
cmds.polySphere(name="mid")
MID = save_as("mid.ma")
TXT = TMP + "/notes.txt"
with open(TXT, "w") as fh:
    fh.write("x")
TOP = build()

# ---------------------------------------------------------------- core
c, logs = ops.replace_references(["TOPLRN"], LEAF2)
check("C1 top-level replace", c == 1 and fname("TOPLRN") == LEAF2, logs)
check("C2 namespace + scene connection (constraint) kept",
      cmds.objExists("TOPL:leaf") and cmds.listConnections("TOPL:leaf.tx", source=True))
check("C3 loaded stays loaded", cmds.referenceQuery("TOPLRN", isLoaded=True))
c, logs = ops.replace_references(["UNLRN"], LEAF2)
check("C4 unloaded stays unloaded, file changed", c == 1 and fname("UNLRN") == LEAF2
      and not cmds.referenceQuery("UNLRN", isLoaded=True) and "(kept unloaded)" in logs[0], logs)
c, logs = ops.replace_references(["TOPLRN"], LEAF2)
check("C5 same file -> skipped", c == 0 and "Already uses that file" in logs[0], logs)
c, logs = ops.replace_references(["MID_A:LEAFRN"], LEAF2)
check("C6 nested replace works + temporary warning", c == 1 and fname("MID_A:LEAFRN") == LEAF2
      and any("NOT saved" in line for line in logs), logs)
c, logs = ops.replace_references(["TOPLRN"], TMP + "/nope.ma")
check("C7 missing file -> warning, nothing changed", c == 0 and "does not exist" in logs[0] and fname("TOPLRN") == LEAF2)
c, logs = ops.replace_references(["TOPLRN"], TXT)
check("C8 not a Maya file -> warning", c == 0 and "Not a Maya file" in logs[0])
c, logs = ops.replace_references(["nope_RN", "driver"], LEAF)
check("C9 non-reference nodes skipped", c == 0 and sum("skipped" in line for line in logs) == 2, logs)

TOP = build()
targets, logs = ops.replace_plan(["MID_ARN", "MID_A:LEAFRN"])
check("C10 parent + its nested child selected -> parent only", targets == ["MID_ARN"] and "parent only" in logs[0], logs)
check("C11 nested_targets", ops.nested_targets(["MID_ARN", "MID_A:LEAFRN"]) == ["MID_A:LEAFRN"])
c, logs = ops.replace_references(["TOPLRN", "UNLRN"], LEAF2)
check("C12 several rows -> same file", c == 2 and fname("TOPLRN") == LEAF2 and fname("UNLRN") == LEAF2, logs)
cmds.file(save=True)
cmds.file(TOP, open=True, force=True)
check("C13 top-level replace is saved with the scene", fname("TOPLRN") == LEAF2)

# ---------------------------------------------------------------- UI
TOP = build()
LOG = []
page = rt.ReferenceDefaultPage(log=LOG.append)
page.show()
app.processEvents()
page.refresh()
tree = page.tree
asked = {}


def ask_ok(start):
    asked["start"] = start
    return LEAF2


def confirm_no(text):
    asked["text"] = text
    return False


page._ask_file = ask_ok
page._confirm = confirm_no
item = [i for i in page._all_items() if i.data(0, rt.ROLE_NODE) == "TOPLRN"][0]
tree.clearSelection()
item.setSelected(True)
check("U1 selected_nodes", page.selected_nodes() == ["TOPLRN"])
page.on_replace()
check("U2 file dialog starts in the reference's folder",
      os.path.normcase(asked.get("start", "")) == os.path.normcase(os.path.normpath(TMP)), asked.get("start"))
check("U3 confirm says no undo; No -> nothing changed", "cannot be undone" in asked.get("text", "")
      and fname("TOPLRN") == LEAF and "[Info] Replace cancelled." in LOG)
page._confirm = lambda text: True
page.on_replace()
check("U4 Yes -> replaced + tree refreshed with new file", fname("TOPLRN") == LEAF2
      and any(i.data(0, rt.ROLE_PATH) == LEAF2 for i in page._all_items()), LOG[-3:])
nested = [i for i in page._all_items() if i.data(0, rt.ROLE_NODE) == "MID_A:LEAFRN"][0]
asked.clear()
page._confirm = confirm_no
tree.clearSelection()
nested.setSelected(True)
page.on_replace()
check("U5 nested row -> confirm warns it is not saved", "NOT saved" in asked.get("text", ""), asked.get("text"))
page._ask_file = lambda start: ""
LOG[:] = []
page.on_replace()
check("U6 file dialog cancelled -> nothing", LOG == [])
tree.clearSelection()
LOG[:] = []
page.on_replace()
check("U7 nothing selected -> warning", LOG == ["[WARN] No reference selected."])
page.close()

shutil.rmtree(TMP, ignore_errors=True)
ok = sum(R)
print("RESULT {0} {1}/{2}".format("OK" if ok == len(R) else "FAIL", ok, len(R)))
maya.standalone.uninitialize()
os._exit(0 if ok == len(R) else 1)
