# -*- coding: utf-8 -*-
# A00480_FileTool v01.17 - Reference > Lineage 페이지 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_reference_lineage.py
# 합성 씬 leaf.ma <- mid.ma(x2) <- top.ma (+ 최상위 leaf, 없는 파일 gone). A00211 스캔 결과가 A00210 NodeItem /
# EdgeItem 으로 그려지는지, Export 가 A00210 이 읽는 lineage JSON 을 쓰는지 본다. A00210 설정(load_store)은 임시 폴더로
# 바꿔 끼워 사용자의 실제 Store Repo 를 건드리지 않는다. QApplication 은 maya.standalone.initialize() 보다 먼저.
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
from Framework.qt.qt import QPointF   # noqa: E402
from tools.A00480_FileTool.app.core import reference_ops as ops   # noqa: E402
from tools.A00480_FileTool.app.ui import reference_lineage_page as rlp   # noqa: E402
from tools.A00480_FileTool.app.ui import reference_tab as rt   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump(n=3):
    for _ in range(n):
        app.processEvents()


check("L0 A00211 + A00210 backends imported", rlp.backends_available(), rlp.BACKEND_ERROR)
rs, lin, lt = rlp.rs, rlp.lin, rlp.lt
MetaStore = rlp.MetaStore

# ---------------------------------------------------------------- scene (test_reference.py 와 같은 합성 씬)
TMP = tempfile.mkdtemp(prefix="jun_a00480_lin_")
STORE = os.path.join(TMP, "store")
os.makedirs(STORE)


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
    cmds.file(GONE, loadReference=rn_gone)
except Exception:
    pass
TOP = save_as("top.ma")

# A00210 설정은 임시 store + 이 폴더를 project root 로 (사용자 설정을 건드리지 않는다)
rs.load_store = lambda: (MetaStore(STORE, TMP), {"author": "test"})

# ---------------------------------------------------------------- page
LOG = []
page = rlp.ReferenceLineagePage(log=LOG.append)
page.resize(700, 600)
page.show()
pump()

nodes = {n.file_name: n for n in page.graph.nodes}
check("L1 four nodes - the scene + three files (same file referenced twice -> one node)",
      sorted(nodes) == ["gone.ma", "leaf.ma", "mid.ma", "top.ma"], sorted(nodes))
check("L2 node items are A00210 NodeItem (same drawing), one per node, NODE_W 150",
      len(page._node_items) == 4 and all(isinstance(it, lt.NodeItem) for it in page._node_items.values())
      and lt.NODE_W == 150)
edges = page._edge_items
links = sorted((page.graph.node_by_id(e.parent_id).file_name, page.graph.node_by_id(e.child_id).file_name) for e in edges)
check("L3 four reference edges: referenced file -> referencing file",
      links == [("gone.ma", "top.ma"), ("leaf.ma", "mid.ma"), ("leaf.ma", "top.ma"), ("mid.ma", "top.ma")], links)
check("L4 edges drawn like A00210 references: kind ref, dashed, grey",
      all(e.kind == "ref" and e.dashed and e.color_hex == lt.REF_EDGE_COLOR for e in edges))
check("L5 labels: scene node 'current scene', missing/unloaded file 'unloaded'",
      nodes["top.ma"].label == "current scene" and nodes["gone.ma"].label == "unloaded" and nodes["mid.ma"].label == "",
      (nodes["top.ma"].label, nodes["gone.ma"].label))
check("L6 keys are project-root relative (A00210 record links)", nodes["mid.ma"].key == "mid.ma" and nodes["top.ma"].key == "top.ma",
      (nodes["mid.ma"].key, nodes["top.ma"].key))
check("L7 layout by depth: scene row 0, referenced files row 150",
      nodes["top.ma"].y == 0.0 and all(nodes[n].y == 150.0 for n in ("mid.ma", "leaf.ma", "gone.ma")),
      [(n, nodes[n].x, nodes[n].y) for n in sorted(nodes)])
check("L8 node colours come from the lane palette", all(it._color.name().upper() in [c.upper() for c in lin.LANE_PALETTE]
                                                        for it in page._node_items.values()))
check("L9 header + log summary", page.count_label.text() == "Reference graph : 4 file(s), 4 reference link(s)"
      and LOG[0] == "Reference graph : 4 file(s), 4 reference link(s) - top.ma", (page.count_label.text(), LOG[:1]))
check("L10 node_abs_path maps every node back to its file",
      page.node_abs_path(nodes["top.ma"]) == TOP and page.node_abs_path(nodes["mid.ma"]) == MID
      and page.node_abs_path(nodes["gone.ma"]) == GONE)
check("L11 store label shows export path + project root",
      "Export : " + os.path.normpath(os.path.join(STORE, "lineage", "top.json")) in page.store_label.text()
      and os.path.normpath(TMP) in page.store_label.text(), page.store_label.text())

# 노드 드래그 -> 모델 위치 + 엣지 재배선
mid_item = page._node_items[nodes["mid.ma"].id]
edge_mid_top = [e for e in edges if page.graph.node_by_id(e.parent_id).file_name == "mid.ma"][0]
start_before = edge_mid_top.path().pointAtPercent(0.0)
mid_item.setPos(mid_item.pos() + QPointF(100.0, 40.0))
pump()
start_after = edge_mid_top.path().pointAtPercent(0.0)
check("L12 dragging a node updates the model and re-routes its edge",
      nodes["mid.ma"].x == 310.0 and nodes["mid.ma"].y == 190.0
      and abs(start_after.x() - start_before.x() - 100.0) < 1e-6 and abs(start_after.y() - start_before.y() - 40.0) < 1e-6,
      (nodes["mid.ma"].x, nodes["mid.ma"].y))

# reveal / copy (탐색기 호출은 가로챈다)
calls = []
real_open = ops.open_path
ops.open_path = calls.append
try:
    LOG[:] = []
    page.reveal_node(nodes["mid.ma"])
    check("L13 reveal_node opens the file in Explorer (via reference_ops)", calls == [os.path.normpath(MID)]
          and LOG and LOG[0].startswith("Opened in File Explorer"), (calls, LOG))
    calls[:] = []
    LOG[:] = []
    page.reveal_node(nodes["gone.ma"])
    check("L14 reveal of a missing file opens its folder + warning", calls == [os.path.normpath(TMP)]
          and LOG[0].startswith("[WARN] File is missing"), LOG)
finally:
    ops.open_path = real_open
LOG[:] = []
page.copy_node_path(nodes["leaf.ma"])
check("L15 copy_node_path -> clipboard native path", QApplication.clipboard().text() == os.path.normpath(LEAF)
      and LOG == ["Copied to clipboard : " + os.path.normpath(LEAF)], LOG)

# fit view
page.buttons["Fit View"].click()
pump()
check("L16 Fit View keeps zoom <= 1 and shows every node", page.view.transform().m11() <= 1.0 + 1e-9
      and all(page.view.mapFromScene(it.sceneBoundingRect()).boundingRect().intersects(page.view.viewport().rect())
              for it in page._node_items.values()), page.view.transform().m11())

# ---------------------------------------------------------------- export
check("L17 default graph name = scene file name", page.graph_name() == "top")
LOG[:] = []
page.buttons["Export to Lineage"].click()
pump()
out = os.path.join(STORE, "lineage", "top.json")
check("L18 Export writes <store>/lineage/top.json + log", os.path.isfile(out)
      and LOG[0] == "Exported lineage graph 'top' : " + os.path.normpath(out), LOG)
loaded = lin.load(STORE, "top")
by_name = {n.file_name: n for n in loaded.nodes}
check("L19 exported graph loads with A00210: 4 nodes, references kept, dragged position kept",
      sorted(by_name) == sorted(nodes) and len(by_name["top.ma"].references) == 3
      and by_name["mid.ma"].references == [by_name["leaf.ma"].id] and by_name["mid.ma"].x == 310.0, by_name["mid.ma"].x)
check("L20 A00210 lists it", lin.list_names(STORE) == ["top"], lin.list_names(STORE))

asked = []
page.confirm = lambda name: asked.append(name) or False
LOG[:] = []
mtime = os.path.getmtime(out)
page.buttons["Export to Lineage"].click()
check("L21 existing graph: asks, decline -> kept", asked == ["top"] and LOG == ["Export cancelled - 'top' was kept as it is."]
      and os.path.getmtime(out) == mtime, LOG)
page.confirm = lambda name: True
page.name_edit.setText("custom_name")
LOG[:] = []
page.buttons["Export to Lineage"].click()
check("L22 custom name -> new file, graph name updated", os.path.isfile(os.path.join(STORE, "lineage", "custom_name.json"))
      and page.graph.name == "custom_name" and LOG[0].startswith("Exported lineage graph 'custom_name'"), LOG[:1])
page.name_edit.setText("")

rs.load_store = lambda: (MetaStore("", ""), {})
page.refresh()
pump()
LOG[:] = []
page.buttons["Export to Lineage"].click()
check("L23 no Store Repo: warning, nothing written", LOG == ["[WARN] Store Repo is not set - set it in A00210_FileManager (File Manager tab) first."]
      and "Store Repo is not set" in page.store_label.text(), LOG)
check("L24 no project root: nodes still drawn, keys empty (A00210 shows '(out of project root)')",
      len(page._node_items) == 4 and all(n.key == "" for n in page.graph.nodes))
rs.load_store = lambda: (MetaStore(STORE, TMP), {"author": "test"})

# ---------------------------------------------------------------- empty / unsaved scene
cmds.file(new=True, force=True)
LOG[:] = []
page.refresh()
pump()
check("L25 new unsaved scene: one node '(untitled scene)', no edges, info log",
      len(page._node_items) == 1 and page.graph.nodes[0].file_name == "(untitled scene)" and not page._edge_items
      and LOG == ["Reference graph : 1 file(s), 0 reference link(s) - (untitled scene)", "[Info] No references in the current scene."], LOG)
LOG[:] = []
page.buttons["Export to Lineage"].click()
check("L26 unsaved scene + empty name: export warns", LOG == ["[WARN] Enter a graph name - the scene is not saved yet, so there is no default."], LOG)
check("L27 node_abs_path of the untitled scene is empty", page.node_abs_path(page.graph.nodes[0]) == "")

# ---------------------------------------------------------------- Reference tab wiring + fallback
tab = rt.ReferenceTab(log=LOG.append)
check("L28 Reference sub tabs: Default + Lineage", [tab.tabs.tabText(i) for i in range(tab.tabs.count())] == ["Default", "Lineage"]
      and isinstance(tab.lineage_page, rlp.ReferenceLineagePage))
saved_rs = rlp.rs
rlp.rs = None
fallback = rlp.ReferenceLineagePage(log=LOG.append)
check("L29 without the backends: notice shown, buttons disabled, no crash", fallback.available is False
      and fallback.notice is not None and fallback.view is None
      and all(not b.isEnabled() for b in fallback.buttons.values()))
fallback.refresh()
fallback.on_export()
check("L30 fallback refresh / export are no-ops", True)
rlp.rs = saved_rs

page.close()
tab.close()
shutil.rmtree(TMP, ignore_errors=True)
ok = sum(R)
print("RESULT {0} {1}/{2}".format("OK" if ok == len(R) else "FAIL", ok, len(R)))
maya.standalone.uninitialize()
os._exit(0 if ok == len(R) else 1)
