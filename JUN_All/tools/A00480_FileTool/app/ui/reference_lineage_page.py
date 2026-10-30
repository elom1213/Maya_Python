# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-30
# A00480_FileTool - Reference > Lineage 페이지 (in-Maya, v01.17)
#
# 현재 씬의 레퍼런스 관계를 **노드 그래프**로 보여 준다.
#   - 데이터 : A00211_RefLineage 의 `ref_scanner` (씬 스캔 → A00210 `LineageGraph`). 노드 1개 = 파일 1개
#              (씬 자신도 루트 노드), 엣지 = "참조 대상 → 참조하는 파일" reference 관계, 깊이별 자동 배치.
#   - 그림   : A00210_FileManager Lineage 탭의 `NodeItem` / `EdgeItem` / `LineageView` 를 **그대로** 쓴다.
#              그래서 A00210 에서 보는 노드와 같은 모양이다 — 둥근 노드(레인 자동색, 파일명 + 보조 라벨),
#              회색 점선 + 채운 삼각 화살촉, 휠 줌 · 중간 버튼 팬 · 드래그 이동 · 러버밴드 선택.
#   - Export : 같은 그래프를 A00211 과 똑같은 lineage JSON 으로 A00210 의 Store Repo 에 쓴다
#              (`<store_dir>/lineage/<name>.json`) → A00210 Lineage 탭에서 Refresh 로 열린다.
#
# ★ 다른 두 툴을 import 한다 — 이 저장소의 "툴 간 import 금지"(릴리즈본은 툴 하나 + Framework 만 동봉) 관례의
#   예외다(사용자 지시 2026-10-30: A00211 로 데이터, A00210 과 같은 노드). 둘이 없으면(릴리즈본) 이 페이지는
#   안내문만 보이고 Reference > Default 와 나머지 탭은 그대로 동작한다. A00211 자체도 같은 식으로 A00210 을 쓴다.
#
# 노드 우클릭은 A00210 의 메뉴(`QMenu.exec` — PySide2 에는 없다, key 없으면 비활성) 대신 여기서 다시 만든다 :
# 이 페이지는 절대 경로를 알고 있으므로 project root 없이도 Reveal in File Explorer / Copy Path 가 된다.
#
# `Show` 콤보(v01.18) : 노드 글자를 **File Name**(기본) / **Full Path** 로. Default 탭과 같은 optionVar 를 쓴다.
# 선택(v01.19) : 빈 곳 드래그 = 러버밴드 다중 선택(A00210 과 같은 IntersectsItemShape), Shift/Ctrl 클릭도 된다.
# 고른 노드의 **전체 경로**는 캔버스 아래 `Selected` 칸(읽기 전용, 복사 가능)에 보인다 - 여러 개면 수와 이름.
# 노드 글자는 A00210 NodeItem 이 `node.file_name` 을 그리므로 그 값을 보기 모드에 맞춰 바꾼다 - Export 때는
# A00210 규약(파일 이름)으로 되돌려 쓴다. 이름 없는 씬은 "(untitled scene)" 그대로.

import os

from Framework.qt.qt import (
    Qt,
    QTimer,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QGraphicsScene,
    QGraphicsView,
    QPainter,
    QMenu,
    QMessageBox,
    QApplication,
    QPointF,
    QRectF,
)

from tools.A00480_FileTool.app.core import reference_ops as ops

try:
    from tools.A00211_RefLineage.app.core import ref_scanner as rs
    from tools.A00210_FileManager.app.core import lineage as lin
    from tools.A00210_FileManager.app.core.store import MetaStore
    from tools.A00210_FileManager.app.ui import lineage_tab as lt
    BACKEND_ERROR = ""
except Exception as _exc:                                  # noqa: BLE001 - ImportError 포함(릴리즈본에 두 툴이 없을 때)
    rs = lin = lt = MetaStore = None
    BACKEND_ERROR = str(_exc)

# 같은 두 노드 사이에 엣지가 여럿이면 가로로 벌리는 간격(A00210 과 같은 값).
EDGE_FAN_SPACING = 18.0


def backends_available():
    """A00211(스캔) + A00210(모델 · 그림) 을 다 import 했는가."""
    return rs is not None and lin is not None and lt is not None and MetaStore is not None


def _make_node_item_class():
    """A00210 NodeItem 의 서브클래스 - 그림은 그대로, 우클릭 메뉴만 이 페이지 것으로."""
    if lt is None:
        return None

    class RefNodeItem(lt.NodeItem):

        def contextMenuEvent(self, event):
            page = self.tab
            if page is None:
                return
            path = page.node_abs_path(self.node)
            menu = QMenu()
            act_reveal = menu.addAction("Reveal in File Explorer")
            act_reveal.setEnabled(bool(path))
            act_copy = menu.addAction("Copy Path")
            act_copy.setEnabled(bool(path))
            run = getattr(menu, "exec_", None) or menu.exec
            chosen = run(event.screenPos())
            if chosen is act_reveal:
                page.reveal_node(self.node)
            elif chosen is act_copy:
                page.copy_node_path(self.node)
            event.accept()

    return RefNodeItem


RefNodeItem = _make_node_item_class()


class ReferenceLineagePage(QWidget):
    """Reference > Lineage : 현재 씬의 레퍼런스 관계 노드 그래프 (+ A00210 lineage JSON 으로 Export)."""

    def __init__(self, log=None, parent=None):
        super(ReferenceLineagePage, self).__init__(parent)
        self._log_callback = log
        self.available = backends_available()
        self.file_view = ops.load_file_view()
        self.collected = None
        self.graph = None
        self.store = None
        self.prefs = {}
        self._path_by_id = {}
        self._node_items = {}
        self._edge_items = []
        self.buttons = {}
        self.scene = None
        self.view = None
        self.notice = None
        # 덮어쓰기 확인. 시험에서는 바꿔 끼운다.
        self.confirm = self._ask_overwrite
        self.build_ui()

    # ------------------------------------------------------------------ UI

    def build_ui(self):
        layout = QVBoxLayout(self)

        head = QHBoxLayout()
        self.count_label = QLabel("Reference graph of the current scene")
        head.addWidget(self.count_label, stretch=1)
        head.addWidget(QLabel("Show"))
        self.view_combo = QComboBox()
        for label, _view in ops.FILE_VIEW_CHOICES:
            self.view_combo.addItem(label)
        self.view_combo.setCurrentIndex(self._view_index(self.file_view))
        self.view_combo.setToolTip(
            "What each node shows.\n"
            "File Name : only the file name (default).\n"
            "Full Path : the whole path of the file (middle-elided to fit the node).\n"
            "Reveal / Copy Path / Export always use the full path. Shared with the Default tab and remembered.")
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        head.addWidget(self.view_combo)
        for label, handler, tip in (
                ("Refresh", self.refresh, "Read the references of the current scene again and redraw the graph."),
                ("Fit View", self.fit_view, "Zoom the canvas so every node is visible.")):
            button = QPushButton(label)
            button.setToolTip(tip)
            button.clicked.connect(handler)
            self.buttons[label] = button
            head.addWidget(button)
        layout.addLayout(head)

        if not self.available:
            self.notice = QLabel(
                "This page needs A00211_RefLineage (scene scan) and A00210_FileManager (graph "
                "drawing) in the same tools folder. They were not found, so the reference graph "
                "cannot be shown here.\n" + (BACKEND_ERROR or ""))
            self.notice.setWordWrap(True)
            self.notice.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            layout.addWidget(self.notice, stretch=1)
            for button in self.buttons.values():
                button.setEnabled(False)
            return

        self.scene = QGraphicsScene()
        self.scene.selectionChanged.connect(self._on_selection_changed)
        self.view = lt.LineageView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        # 빈 곳 드래그 = 러버밴드 다중 선택(범위에 일부라도 걸친 노드 · 엣지). 중간 버튼 팬 · 휠 줌은 view 가 처리. (v01.19)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        self.view.setMinimumHeight(360)
        self.view.setToolTip(
            "Every file the current scene references, as a graph. Node = one file (the scene\n"
            "itself is the root). Dashed grey arrow = 'referenced file -> file that references it'\n"
            "(same drawing as A00210_FileManager > Lineage).\n"
            "Mouse wheel: zoom. Middle drag: pan. Drag a node to move it. Drag on empty space:\n"
            "rubber-band select several nodes (Shift / Ctrl click also work). Right-click a node:\n"
            "Reveal in File Explorer / Copy Path. The full path of the selection shows below.")
        layout.addWidget(self.view, stretch=1)

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Selected"))
        self.selected_edit = QLineEdit()
        self.selected_edit.setReadOnly(True)
        self.selected_edit.setPlaceholderText("Click a node to see its full file path here")
        self.selected_edit.setToolTip(
            "Full path of the selected node (select the text to copy it).\n"
            "With several nodes selected: how many, and their file names - the tooltip of this box lists every path.")
        sel_row.addWidget(self.selected_edit, stretch=1)
        layout.addLayout(sel_row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Graph name"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("defaults to the scene file name")
        self.name_edit.setToolTip("Name of the lineage graph written by Export (defaults to the scene file name).")
        row.addWidget(self.name_edit, stretch=1)
        self.export_button = QPushButton("Export to Lineage")
        self.export_button.setToolTip(
            "Save this graph as an A00210 lineage JSON (<Store Repo>/lineage/<name>.json) - the\n"
            "same file A00211_RefLineage writes. Open A00210_FileManager > Lineage and press\n"
            "Refresh to see it. Node positions you dragged here are kept.")
        self.export_button.clicked.connect(self.on_export)
        self.buttons["Export to Lineage"] = self.export_button
        row.addWidget(self.export_button)
        layout.addLayout(row)

        self.store_label = QLabel("")
        self.store_label.setWordWrap(True)
        layout.addWidget(self.store_label)

    # ------------------------------------------------------------------ data

    def showEvent(self, event):
        # 탭을 열 때마다 현재 씬 기준으로(Default 페이지와 같은 규칙). 보기 모드도 optionVar 에서 따라간다.
        super(ReferenceLineagePage, self).showEvent(event)
        view = ops.load_file_view()
        if view != self.file_view:
            self.set_file_view(view)
        if self.available:
            self.refresh()

    # ------------------------------------------------------------------ node text view (Default 탭과 같은 모드)

    @staticmethod
    def _view_index(view):
        for i, (_label, v) in enumerate(ops.FILE_VIEW_CHOICES):
            if v == view:
                return i
        return 0

    def node_text(self, node, view=None):
        """노드에 보일 글자 - 보기 모드(기본 = 지금 모드)에 따라 파일 이름 / 전체 경로. 저장 전 씬은 그대로."""
        path = self.node_abs_path(node)
        if not path:
            return node.file_name
        return ops.file_text(path, self.file_view if view is None else view)

    def _apply_file_view(self):
        """그래프의 모든 노드 글자를 지금 보기 모드로. 아이템은 다시 그린다."""
        if self.graph is None:
            return
        for node in self.graph.nodes:
            node.file_name = self.node_text(node)
            item = self._node_items.get(node.id)
            if item is not None:
                item.update()

    def set_file_view(self, view):
        """노드 글자를 `path`(전체 경로) / `name`(파일 이름) 으로. 씬은 다시 읽지 않는다."""
        if view not in ops.FILE_VIEWS:
            return
        self.file_view = view
        if self.view_combo.currentIndex() != self._view_index(view):
            self.view_combo.setCurrentIndex(self._view_index(view))      # -> _on_view_changed 가 다시 들어온다
            return
        self._apply_file_view()
        ops.save_file_view(view)

    def _on_view_changed(self, index):
        choices = ops.FILE_VIEW_CHOICES
        self.set_file_view(choices[index][1] if 0 <= index < len(choices) else ops.FILE_VIEW_DEFAULT)

    def graph_name(self):
        """Export 이름 - 칸이 비면 씬 파일 이름(확장자 없이). 저장 전 씬이면 ""."""
        text = self.name_edit.text().strip() if self.view is not None else ""
        if text:
            return text
        scene = (self.collected or {}).get("scene", "")
        return os.path.splitext(os.path.basename(scene))[0] if scene else ""

    def refresh(self, *_args):
        """씬을 다시 읽어 그래프를 만들고 그린다."""
        if not self.available:
            return
        try:
            self.collected = rs.collect_scene_references()
        except Exception as exc:                            # noqa: BLE001 - 마야 밖 · 쿼리 실패
            self._log("[WARN] Could not read the scene references : {0}".format(exc))
            return
        try:
            self.store, self.prefs = rs.load_store()
        except Exception as exc:                            # noqa: BLE001 - prefs 깨짐 등
            self.store, self.prefs = MetaStore("", ""), {}
            self._log("[WARN] Could not read the A00210 settings ({0}) - nodes have no project keys.".format(exc))

        self.graph = rs.build_graph(self.collected, self.store, self.graph_name() or "scene_references",
                                    (self.prefs or {}).get("author", ""))
        self._path_by_id = self._map_paths(self.collected, self.graph)
        self._apply_file_view()
        self._render_graph()
        QTimer.singleShot(0, self.fit_view)

        paths = self.collected["paths"]
        edges = self.collected["edges"]
        scene = self.collected["scene"]
        summary = "Reference graph : {0} file(s), {1} reference link(s)".format(len(paths), len(edges))
        self.count_label.setText(summary)
        self._log(summary + " - " + (os.path.basename(scene) if scene else "(untitled scene)"))
        if not edges:
            self._log("[Info] No references in the current scene.")
        self._refresh_store_label()

    @staticmethod
    def _map_paths(collected, graph):
        """노드 id -> 절대 경로. build_graph 는 [씬] + 정렬된 나머지 순으로 seq 를 매긴다."""
        scene_norm = collected["scene_norm"]
        paths = collected["paths"]
        ordered = [scene_norm] + sorted(n for n in paths if n != scene_norm)
        out = {}
        for node in graph.nodes:
            if 0 <= node.seq < len(ordered):
                out[node.id] = paths.get(ordered[node.seq], "")
        return out

    def _refresh_store_label(self):
        store = self.store
        if store is None or not store.store_dir:
            text = "Export : Store Repo is not set - set it in A00210_FileManager (File Manager tab)."
        else:
            text = "Export : {0}".format(os.path.normpath(os.path.join(store.store_dir, lin.LINEAGE_DIR,
                                                                        (self.graph_name() or "<name>") + ".json")))
        root = getattr(store, "project_root", "") if store is not None else ""
        text += "\nProject root : {0}".format(os.path.normpath(root) if root else "(not set - nodes have no record links)")
        self.store_label.setText(text)

    def node_abs_path(self, node):
        """노드의 절대 경로(저장 전 씬이면 "")."""
        return self._path_by_id.get(node.id, "") if node is not None else ""

    # ------------------------------------------------------------------ drawing (A00210 과 같은 규칙)

    def _render_graph(self):
        self.scene.clear()
        self._node_items = {}
        self._edge_items = []
        if self.graph is None:
            return

        lane_of, _order = lin.compute_lanes(self.graph)
        for node in self.graph.nodes:
            lane_col = lin.lane_color(lane_of.get(node.id, 0))
            item = RefNodeItem(node, node.color or lane_col, self)
            self.scene.addItem(item)
            self._node_items[node.id] = item

        ids = {n.id for n in self.graph.nodes}
        overrides = self.graph.edge_colors
        # 계보(parents) 실선 - 씬 스캔 그래프에는 없지만 A00210 과 같은 규칙으로 그린다.
        for node in self.graph.nodes:
            child_color = lin.lane_color(lane_of.get(node.id, 0))
            for pid in node.parents:
                if pid not in ids:
                    continue
                edge = lt.EdgeItem(pid, node.id)
                parent = self.graph.node_by_id(pid)
                dashed = node.planned or (parent is not None and parent.planned)
                edge.set_style(overrides.get(lin.edge_color_key("lineage", pid, node.id)) or child_color, dashed)
                self.scene.addItem(edge)
                self._edge_items.append(edge)
        # reference 점선 - 참조 대상 -> 참조하는 노드, 회색 + 채운 삼각 화살촉.
        for node in self.graph.nodes:
            for tid in node.references:
                if tid not in ids:
                    continue
                edge = lt.EdgeItem(tid, node.id, kind="ref")
                edge.set_style(overrides.get(lin.edge_color_key("ref", tid, node.id)) or lt.REF_EDGE_COLOR, True)
                self.scene.addItem(edge)
                self._edge_items.append(edge)

        self._reroute_edges()
        self._update_scene_rect()
        self._on_selection_changed()

    # ------------------------------------------------------------------ selection -> full path (v01.19)

    def selected_nodes(self):
        """지금 선택된 노드(모델)들 - 씬 아이템 순서."""
        if self.scene is None:
            return []
        return [item.node for item in self.scene.selectedItems() if isinstance(item, lt.NodeItem)]

    def selection_text(self):
        """`Selected` 칸 글자. 하나면 전체 경로, 여럿이면 수 + 파일 이름들, 없으면 ""."""
        nodes = self.selected_nodes()
        if not nodes:
            return ""
        if len(nodes) == 1:
            path = self.node_abs_path(nodes[0])
            return os.path.normpath(path) if path else "(untitled scene - not saved yet)"
        names = []
        for node in nodes:
            path = self.node_abs_path(node)
            names.append(os.path.basename(os.path.normpath(path)) if path else "(untitled scene)")
        return "{0} nodes selected : {1}".format(len(nodes), ", ".join(names))

    def _on_selection_changed(self, *_args):
        if self.view is None:
            return
        self.selected_edit.setText(self.selection_text())
        self.selected_edit.setCursorPosition(0)
        paths = [os.path.normpath(p) for p in (self.node_abs_path(n) for n in self.selected_nodes()) if p]
        self.selected_edit.setToolTip(
            "\n".join(paths) if paths else
            "Full path of the selected node (select the text to copy it).\n"
            "With several nodes selected: how many, and their file names - this tooltip lists every path.")

    def _reroute_edges(self):
        """노드가 움직이면 엣지를 다시 긋는다(NodeItem.itemChange 가 부른다). 같은 노드쌍 엣지는 가로로 벌린다."""
        groups = {}
        for edge in self._edge_items:
            groups.setdefault((edge.parent_id, edge.child_id), []).append(edge)
        for (pid, cid), edges in groups.items():
            p = self._node_items.get(pid)
            c = self._node_items.get(cid)
            if p is None or c is None:
                continue
            n = len(edges)
            for i, edge in enumerate(edges):
                shift = QPointF((i - (n - 1) / 2.0) * EDGE_FAN_SPACING, 0.0)
                edge.route(p.bottom_center_scene() + shift, c.top_center_scene() + shift)

    def _update_scene_rect(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isNull():
            self.scene.setSceneRect(QRectF(0, 0, 400, 300))
            return
        scale = self.view.transform().m11() or 1.0
        vp = self.view.viewport().rect()
        mx = max(800.0, vp.width() / scale)
        my = max(800.0, vp.height() / scale)
        self.scene.setSceneRect(rect.adjusted(-mx, -my, mx, my))

    def fit_view(self, *_args):
        if self.scene is None:
            return
        rect = self.scene.itemsBoundingRect()
        if not rect.isNull():
            self.view.fitInView(rect.adjusted(-40, -40, 40, 40), Qt.KeepAspectRatio)
            # 노드가 하나뿐이면 fitInView 가 과하게 확대한다 - 최대 배율을 1 로 둔다.
            if self.view.transform().m11() > 1.0:
                self.view.resetTransform()
                self.view.centerOn(rect.center())

    # ------------------------------------------------------------------ node actions

    def reveal_node(self, node):
        path = self.node_abs_path(node)
        if not path:
            self._log("[WARN] This node has no file path (the scene is not saved).")
            return
        self._log_all(ops.open_reference_files([path]))

    def copy_node_path(self, node):
        path = self.node_abs_path(node)
        if not path:
            self._log("[WARN] This node has no file path (the scene is not saved).")
            return
        text, logs = ops.clipboard_text([path])
        if text:
            clipboard = QApplication.clipboard()
            if clipboard is None:
                logs = ["[WARN] Could not access the system clipboard."]
            else:
                clipboard.setText(text)
        self._log_all(logs)

    # ------------------------------------------------------------------ export

    def _ask_overwrite(self, name):
        answer = QMessageBox.question(
            self, "Export to Lineage",
            "A lineage graph named '{0}' already exists.\nOverwrite it?".format(name))
        return answer == QMessageBox.Yes

    def on_export(self, *_args):
        """그래프를 A00210 lineage JSON 으로 저장한다(A00211 Export 와 같은 파일)."""
        if not self.available:
            return
        if self.graph is None:
            self.refresh()
            if self.graph is None:
                return
        store = self.store
        if store is None or not store.store_dir:
            self._log("[WARN] Store Repo is not set - set it in A00210_FileManager (File Manager tab) first.")
            return
        name = self.graph_name()
        if not name:
            self._log("[WARN] Enter a graph name - the scene is not saved yet, so there is no default.")
            return
        if lin.exists(store.store_dir, name) and not self.confirm(name):
            self._log("Export cancelled - '{0}' was kept as it is.".format(name))
            return
        self.graph.name = name
        # A00210 규약대로 노드 글자는 파일 이름으로 저장한다(Full Path 모드여도).
        for node in self.graph.nodes:
            node.file_name = self.node_text(node, ops.FILE_VIEW_NAME)
        try:
            path = lin.save(store.store_dir, self.graph)
        except Exception as exc:                            # noqa: BLE001
            self._log("[WARN] Export failed : {0}".format(exc))
            return
        finally:
            self._apply_file_view()
        self._log("Exported lineage graph '{0}' : {1}".format(name, os.path.normpath(path)))
        self._log("Open A00210_FileManager > Lineage and press Refresh to see it (Push there to sync).")
        self._refresh_store_label()

    # ------------------------------------------------------------------ helper

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)
