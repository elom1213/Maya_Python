# -*- coding: utf-8 -*-
# A00480_FileTool v01.22 - Reference > Default `Import` 시험 (mayapy 오프스크린)
#   합성 씬: top <- mid.ma(<- leaf.ma 중첩) · leaf.ma(로드, 컨스트레인트) · leaf.ma(언로드) · mid.ma(언로드) · leaf.ma 복사본
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_reference_import.py
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


TMP = tempfile.mkdtemp(prefix="jun_a00480_imp_").replace("\\", "/")


def save_as(name):
    path = TMP + "/" + name
    cmds.file(rename=path)
    cmds.file(save=True, type="mayaAscii")
    return path


def refs():
    return sorted(n for n in cmds.ls(type="reference") if n not in ops.SKIP_NODES)


def referenced(node):
    return cmds.objExists(node) and cmds.referenceQuery(node, isNodeReferenced=True)


cmds.file(new=True, force=True)
cmds.polyCube(name="leaf")
LEAF = save_as("leaf.ma")
cmds.file(new=True, force=True)
cmds.file(LEAF, reference=True, namespace="LEAF")
cmds.polySphere(name="mid")
MID = save_as("mid.ma")
cmds.file(new=True, force=True)
cmds.polyCone(name="gone")
GONE = save_as("gone.ma")


def build():
    cmds.file(new=True, force=True)
    cmds.file(MID, reference=True, namespace="MID_A")
    cmds.file(LEAF, reference=True, namespace="TOPL")
    cmds.file(LEAF, reference=True, namespace="UNL")
    cmds.file(unloadReference="UNLRN")
    cmds.file(MID, reference=True, namespace="UNM")
    cmds.file(unloadReference="UNMRN")
    cmds.file(GONE, reference=True, namespace="GONE")
    cmds.polyCube(name="driver")
    cmds.parentConstraint("driver", "TOPL:leaf")
    path = save_as("top.ma")
    return path


TOP = build()
# Missing 파일 : 레퍼런스 뒤 파일을 지우고 다시 연다
os.remove(GONE)
cmds.file(TOP, open=True, force=True)
check("setup", refs() == ["GONERN", "MID_A:LEAFRN", "MID_ARN", "TOPLRN", "UNLRN", "UNMRN"], refs())

# ---------------------------------------------------------------- core : plan
targets, logs = ops.import_plan(["MID_A:LEAFRN"])
check("P1 nested alone -> skipped with a hint", targets == [] and "only be imported after its parent" in logs[0], logs)
targets, logs = ops.import_plan(["MID_A:LEAFRN", "MID_ARN", "TOPLRN"])
check("P2 parent + nested -> parent first", targets == ["MID_ARN", "TOPLRN", "MID_A:LEAFRN"], targets)
targets, logs = ops.import_plan(["GONERN", "driver", "nope"])
check("P3 missing file / non-reference skipped", targets == [] and len(logs) == 3
      and "File is missing" in logs[0], logs)

# ---------------------------------------------------------------- core : import
c, logs = ops.import_references(["TOPLRN"])
check("C1 top-level import : reference node gone, objects are scene objects",
      c == 1 and "TOPLRN" not in refs() and cmds.objExists("TOPL:leaf") and not referenced("TOPL:leaf"), logs)
check("C2 namespace + scene constraint kept", cmds.listConnections("TOPL:leaf.tx", source=True))
c, logs = ops.import_references(["UNLRN"])
check("C3 unloaded -> loaded first, then imported",
      c == 1 and "(loaded first)" in logs[0] and "UNLRN" not in refs() and cmds.objExists("UNL:leaf")
      and not referenced("UNL:leaf"), logs)
c, logs = ops.import_references(["MID_ARN"])
check("C4 parent only -> nested becomes a top-level reference",
      c == 1 and not referenced("MID_A:mid") and "MID_A:LEAFRN" in refs()
      and not cmds.referenceQuery("MID_A:LEAFRN", referenceNode=True, parent=True)
      and any("now top-level" in line for line in logs), logs)
c, logs = ops.import_references(["MID_A:LEAFRN"])
check("C5 that one can be imported now", c == 1 and "MID_A:LEAFRN" not in refs(), logs)
c, logs = ops.import_references(["UNMRN"], include_nested=True)
check("C6 Include nested on an unloaded parent -> parent + its nested, all imported",
      c == 2 and "UNMRN" not in refs() and "UNM:LEAFRN" not in refs()
      and cmds.objExists("UNM:LEAF:leaf") and not referenced("UNM:LEAF:leaf"), (logs, refs()))
check("C7 only the missing one is left", refs() == ["GONERN"], refs())

# 같은 파일 두 번 (복사 번호)
cmds.file(new=True, force=True)
cmds.file(LEAF, reference=True, namespace="A")
cmds.file(LEAF, reference=True, namespace="B")
check("C8 setup : second copy has {1}", cmds.referenceQuery("BRN", filename=True).endswith("{1}"))
c, logs = ops.import_references(["BRN"])
check("C9 copy-numbered reference imports by node (the other stays)",
      c == 1 and refs() == ["ARN"] and not referenced("B:leaf") and referenced("A:leaf"), logs)

# ---------------------------------------------------------------- UI
TOP = build()
LOG = []
page = rt.ReferenceDefaultPage(log=LOG.append)
page.show()
app.processEvents()
page.refresh()
tree = page.tree
asked = {}


def confirm_no(text, title=""):
    asked["text"], asked["title"] = text, title
    return False


def confirm_yes(text, title=""):
    asked["text"], asked["title"] = text, title
    return True


def select(*nodes):
    tree.clearSelection()
    for item in page._all_items():
        if item.data(0, rt.ROLE_NODE) in nodes:
            item.setSelected(True)


check("U1 Import button + Include nested (off)", "Import" in page.buttons and not page.nested_check.isChecked())
page._confirm = confirm_no
select("TOPLRN")
page.on_import()
check("U2 confirm says no undo; No -> nothing changed",
      "cannot be undone" in asked.get("text", "") and asked.get("title") == "Import Reference"
      and "TOPLRN" in refs() and "[Info] Import cancelled." in LOG, asked)
page._confirm = confirm_yes
page.on_import()
check("U3 Yes -> imported + tree refreshed",
      "TOPLRN" not in refs() and all(i.data(0, rt.ROLE_NODE) != "TOPLRN" for i in page._all_items()), LOG[-3:])
LOG[:] = []
select("MID_A:LEAFRN")
asked.clear()
page.on_import()
check("U4 nested row alone -> warning, no confirm", not asked and any("after its parent" in m for m in LOG), LOG)
page.nested_check.setChecked(True)
select("MID_ARN")
page.on_import()
check("U5 Include nested -> parent + nested imported, confirm mentions it",
      "MID_ARN" not in refs() and "MID_A:LEAFRN" not in refs() and "Include nested" in asked.get("text", ""), refs())
menu, handlers = page.build_context_menu()
labels = [a.text() for a in menu.actions()]
check("U6 right-click menu has Import Objects from Reference", "Import Objects from Reference" in labels, labels)
tree.clearSelection()
LOG[:] = []
page.on_import()
check("U7 nothing selected -> warning", LOG == ["[WARN] No reference selected."], LOG)
page.close()

shutil.rmtree(TMP, ignore_errors=True)
ok = sum(R)
print("RESULT {0} {1}/{2}".format("OK" if ok == len(R) else "FAIL", ok, len(R)))
maya.standalone.uninitialize()
os._exit(0 if ok == len(R) else 1)
