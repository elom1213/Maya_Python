# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00210_FileManager - "Lineage" tab (Qt)
#
# 파일들(.mb/.ma 뿐 아니라 .fbx/.obj 등 포맷 무관) 사이의 브랜치/병합 관계(DAG)를
# 인터랙티브 캔버스에서 직접 그리고,
# git-graph 스타일의 색상 레인 트리로 본다. 그래프는 store_dir 에 JSON 으로 저장되어
# (path_structure 와 동일) git 으로 동기화된다.
#
#  - 노드: 드래그로 이동(위치 저장). 색상은 토폴로지 레인에서 자동 계산.
#  - Connect Mode: 노드 → 노드 로 선을 그어 부모 관계 지정(사이클/중복 거부).
#  - Auto Layout: 레인/토폴로지로 자동 정렬.
#
# project_root / store_dir / 로그는 MainWindow 에서 콜러블로 주입받는다(단일 소스 유지).

import os
import sys
import time
import subprocess

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QMenu,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsItem,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPixmap,
    Qt,
    QRectF,
    QPointF,
)

from ..core import lineage as lin
from ..core import scanner
from ..core.store import OutsideProjectRootError


NODE_W = 150
NODE_H = 48


# ============================================================== graphics items

class NodeItem(QGraphicsObject):
    """드래그 가능한 노드 1개. 모델(LineageNode)을 직접 참조해 위치를 되돌려 쓴다."""

    def __init__(self, node, color_hex, tab):
        super().__init__()
        self.node = node
        self.tab = tab
        self._color = QColor(color_hex)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)   # 필수: 위치 저장
        self.setZValue(1.0)
        self.setPos(node.x, node.y)

    # --- geometry
    def boundingRect(self):
        return QRectF(-3, -3, NODE_W + 6, NODE_H + 6)

    def top_center_scene(self):
        return self.scenePos() + QPointF(NODE_W / 2.0, 0.0)

    def bottom_center_scene(self):
        return self.scenePos() + QPointF(NODE_W / 2.0, NODE_H)

    # --- paint
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(0, 0, NODE_W, NODE_H)

        fill = QColor(self._color)
        if self.node.planned:
            fill.setAlpha(70)            # planned 는 반투명
        else:
            fill.setAlpha(235)
        painter.setBrush(QBrush(fill))

        if self.isSelected():
            painter.setPen(QPen(QColor("#FFFFFF"), 2.5))
        elif self.node.planned:
            pen = QPen(QColor(self._color).lighter(130), 1.6)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
        else:
            painter.setPen(QPen(QColor(self._color).darker(160), 1.4))
        painter.drawRoundedRect(rect, 7, 7)

        # 텍스트(파일명 + 보조 라벨)
        painter.setPen(QColor("#15181C"))
        fm = QFontMetrics(painter.font())
        name = fm.elidedText(self.node.file_name or "(node)", Qt.ElideMiddle, NODE_W - 16)
        painter.drawText(QRectF(8, 6, NODE_W - 16, 20), Qt.AlignVCenter | Qt.AlignLeft, name)

        sub = self.node.label or ("planned" if self.node.planned else "")
        if not self.node.key and not self.node.planned:
            sub = sub or "(out of project root)"
        if sub:
            f = QFont(painter.font())
            f.setPointSizeF(max(7.0, f.pointSizeF() - 1.5))
            painter.setFont(f)
            painter.setPen(QColor("#2A2F36"))
            sub = fm.elidedText(sub, Qt.ElideRight, NODE_W - 16)
            painter.drawText(QRectF(8, NODE_H - 22, NODE_W - 16, 18),
                             Qt.AlignVCenter | Qt.AlignLeft, sub)

    # --- model sync
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.node.x = float(self.pos().x())
            self.node.y = float(self.pos().y())
            if self.tab is not None:
                self.tab._reroute_edges()
        return super().itemChange(change, value)

    # --- context menu (우클릭)
    def contextMenuEvent(self, event):
        if self.tab is None:
            return
        menu = QMenu()
        act_reveal = menu.addAction("Reveal in File Explorer")
        # 실제 파일 경로를 해석할 수 있을 때만 활성(planned/루트 밖/없는 파일은 비활성).
        act_reveal.setEnabled(bool(self.tab.node_abs_path(self.node)))
        chosen = menu.exec(event.screenPos())
        if chosen is act_reveal:
            self.tab.reveal_node(self.node)
        event.accept()


class EdgeItem(QGraphicsPathItem):
    """부모 -> 자식 연결선. 색은 자식 레인 색."""

    def __init__(self, parent_id, child_id):
        super().__init__()
        self.parent_id = parent_id
        self.child_id = child_id
        self.color_hex = "#888888"
        self.dashed = False
        self.setZValue(-1.0)

    def set_style(self, color_hex, dashed):
        self.color_hex = color_hex
        self.dashed = dashed
        pen = QPen(QColor(color_hex), 2.0)
        pen.setCosmetic(False)
        if dashed:
            pen.setStyle(Qt.DashLine)
        self.setPen(pen)

    def route(self, p_anchor, c_anchor):
        path = QPainterPath(p_anchor)
        mid_y = (p_anchor.y() + c_anchor.y()) / 2.0
        path.cubicTo(
            QPointF(p_anchor.x(), mid_y),
            QPointF(c_anchor.x(), mid_y),
            c_anchor,
        )
        # 자식쪽 화살촉(아래로 향하는 V).
        a = 7.0
        path.moveTo(c_anchor.x() - a, c_anchor.y() - a)
        path.lineTo(c_anchor.x(), c_anchor.y())
        path.lineTo(c_anchor.x() + a, c_anchor.y() - a)
        self.setPath(path)


class LineageScene(QGraphicsScene):
    """Connect Mode 에서 노드 -> 노드 선을 그어 부모를 연결한다."""

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        self._connect_mode = False
        self._pending = None        # 시작(부모) NodeItem
        self._temp = None           # 임시 rubber-band path

    def set_connect_mode(self, on):
        self._connect_mode = bool(on)
        self._clear_temp()

    def _clear_temp(self):
        if self._temp is not None:
            self.removeItem(self._temp)
            self._temp = None
        self._pending = None

    def _node_at(self, scene_pos):
        for it in self.items(scene_pos):
            if isinstance(it, NodeItem):
                return it
        return None

    def mousePressEvent(self, event):
        if self._connect_mode and event.button() == Qt.LeftButton:
            node = self._node_at(event.scenePos())
            if node is not None:
                self._pending = node
                self._temp = QGraphicsPathItem()
                pen = QPen(QColor("#BBBBBB"), 1.6)
                pen.setStyle(Qt.DashLine)
                self._temp.setPen(pen)
                self._temp.setZValue(2.0)
                self.addItem(self._temp)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._connect_mode and self._pending is not None and self._temp is not None:
            p = self._pending.bottom_center_scene()
            c = event.scenePos()
            path = QPainterPath(p)
            path.lineTo(c)
            self._temp.setPath(path)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._connect_mode and self._pending is not None:
            target = self._node_at(event.scenePos())
            parent = self._pending
            self._clear_temp()
            if target is not None and target is not parent:
                self.tab.try_add_edge(parent.node.id, target.node.id)
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ==================================================================== view

class LineageView(QGraphicsView):
    """줌(마우스 휠, 커서 기준) + 팬(중간 버튼 드래그)을 지원하는 캔버스 뷰."""

    MIN_ZOOM = 0.15
    MAX_ZOOM = 4.0
    _STEP = 1.15

    def __init__(self, scene):
        super().__init__(scene)
        self._panning = False
        self._pan_last = None
        # 휠 줌이 마우스 커서 아래 지점을 기준으로 확대/축소되게.
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

    @staticmethod
    def _evt_pos(event):
        # PySide6=position()(QPointF) / PySide2=pos()(QPoint) 모두 대응.
        if hasattr(event, "position"):
            return event.position().toPoint()
        return event.pos()

    def wheelEvent(self, event):
        factor = self._STEP if event.angleDelta().y() > 0 else 1.0 / self._STEP
        cur = self.transform().m11()            # 현재 배율(fitInView 후에도 정확)
        target = cur * factor
        if target < self.MIN_ZOOM:
            factor = self.MIN_ZOOM / cur
        elif target > self.MAX_ZOOM:
            factor = self.MAX_ZOOM / cur
        if abs(factor - 1.0) > 1e-6:
            self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_last = self._evt_pos(event)
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_last is not None:
            pos = self._evt_pos(event)
            delta = pos - self._pan_last
            self._pan_last = pos
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self._pan_last = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ============================================================ add-from-scan dialog

class AddFromScanDialog(QDialog):
    """스캔된 파일을 체크해서 노드로 추가한다(포맷 무관). 확장자로 필터 가능."""

    def __init__(self, entries, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Nodes from Scan")
        self.resize(460, 460)
        self._entries = entries

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{len(entries)} file(s) found. Check the ones to add:"))

        filt_row = QHBoxLayout()
        self.ipf_filter = QLineEdit()
        self.ipf_filter.setPlaceholderText("filter by extension (e.g. mb ma fbx obj) - empty = all")
        self.ipf_filter.textChanged.connect(self._apply_filter)
        filt_row.addWidget(QLabel("Filter"))
        filt_row.addWidget(self.ipf_filter)
        layout.addLayout(filt_row)

        self.list = QListWidget()
        for entry in entries:
            label = entry["file_name"]
            if not entry.get("in_root", True):
                label += "   (out of project root)"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, entry)
            self.list.addItem(item)
        layout.addWidget(self.list, stretch=1)

        sel_row = QHBoxLayout()
        btn_check = QPushButton("Check Visible")
        btn_check.clicked.connect(lambda: self._set_visible_checked(True))
        btn_uncheck = QPushButton("Uncheck Visible")
        btn_uncheck.clicked.connect(lambda: self._set_visible_checked(False))
        sel_row.addWidget(btn_check)
        sel_row.addWidget(btn_uncheck)
        sel_row.addStretch(1)
        layout.addLayout(sel_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _wanted_exts(self):
        raw = self.ipf_filter.text().replace(",", " ").split()
        return {e.lower().lstrip(".") for e in raw if e.strip()}

    def _apply_filter(self):
        wanted = self._wanted_exts()
        for i in range(self.list.count()):
            item = self.list.item(i)
            entry = item.data(Qt.UserRole)
            ext = (entry.get("ext") or "").lower()
            item.setHidden(bool(wanted) and ext not in wanted)

    def _set_visible_checked(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.list.count()):
            item = self.list.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def checked_entries(self):
        out = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.checkState() == Qt.Checked:
                out.append(item.data(Qt.UserRole))
        return out


# ================================================================== the tab

class LineageTab(QWidget):

    def __init__(self, get_store, get_project_root, get_store_dir, log):
        super().__init__()

        self._get_store = get_store
        self._get_project_root = get_project_root
        self._get_store_dir = get_store_dir
        self._log = log

        self._graph = lin.LineageGraph()
        self._node_items = {}      # id -> NodeItem
        self._edge_items = []      # list[EdgeItem]
        self._selected_id = None

        self._build_ui()
        self.on_refresh()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self._build_saved_group())
        root.addWidget(self._build_toolbar())

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self._build_canvas())
        split.addWidget(self._build_inspector())
        # 좌(캔버스):우(Node 패널) = 3:1 → 캔버스가 가로의 약 3/4 를 차지.
        # stretch 는 리사이즈 분배, setSizes 는 초기 비율(큰 비례값이면 가용폭에 맞춰 스케일).
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        split.setSizes([3000, 1000])
        root.addWidget(split, stretch=1)

    def _build_saved_group(self):
        group = QGroupBox("Lineage Graphs")
        layout = QVBoxLayout(group)

        name_row = QHBoxLayout()
        self.ipf_name = QLineEdit()
        self.ipf_name.setPlaceholderText("graph name (e.g. LUN_rig)")
        name_row.addWidget(QLabel("Name"))
        name_row.addWidget(self.ipf_name)
        layout.addLayout(name_row)

        self.list_graphs = QListWidget()
        self.list_graphs.setMaximumHeight(90)
        self.list_graphs.currentItemChanged.connect(self.on_select_graph)
        layout.addWidget(self.list_graphs)

        btn_row = QHBoxLayout()
        for text, slot in (
            ("New", self.on_new),
            ("Save", self.on_save),
            ("Refresh", self.on_refresh),
            ("Delete", self.on_delete_graph),
        ):
            b = QPushButton(text)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        return group

    def _build_toolbar(self):
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)

        btn_layout = QPushButton("Auto Layout")
        btn_layout.clicked.connect(self.on_auto_layout)

        self.btn_connect = QPushButton("Connect Mode")
        self.btn_connect.setCheckable(True)
        self.btn_connect.toggled.connect(self.on_toggle_connect)

        btn_scan = QPushButton("Add Node from Scan...")
        btn_scan.clicked.connect(self.on_add_from_scan)
        btn_file = QPushButton("Add File...")
        btn_file.clicked.connect(self.on_add_file)
        btn_planned = QPushButton("Add Planned Node")
        btn_planned.clicked.connect(self.on_add_planned)
        btn_del_node = QPushButton("Delete Node")
        btn_del_node.clicked.connect(self.on_delete_node)

        row.addWidget(btn_layout)
        row.addWidget(self.btn_connect)
        row.addStretch(1)
        row.addWidget(btn_scan)
        row.addWidget(btn_file)
        row.addWidget(btn_planned)
        row.addWidget(btn_del_node)

        return bar

    def _build_canvas(self):
        self.scene = LineageScene(self)
        self.scene.selectionChanged.connect(self._on_selection_changed)

        self.view = LineageView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setDragMode(QGraphicsView.NoDrag)
        return self.view

    def _build_inspector(self):
        group = QGroupBox("Node")
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel("File name"))
        self.ipf_node_name = QLineEdit()
        self.ipf_node_name.editingFinished.connect(self._apply_node_name)
        layout.addWidget(self.ipf_node_name)

        self.chk_planned = QCheckBox("Planned (file not created yet)")
        self.chk_planned.toggled.connect(self._apply_node_planned)
        layout.addWidget(self.chk_planned)

        # 부모에 대한 관계: version-up(부모와 같은 색=메인 라인) vs branch(다른 색=베리에이션).
        layout.addWidget(QLabel("Relation to parent"))
        self.cmb_relation = QComboBox()
        self.cmb_relation.addItem("Auto", "")              # 토폴로지 기본(첫 자식이 메인)
        self.cmb_relation.addItem("Version-up (main line)", "version")
        self.cmb_relation.addItem("Branch (variation)", "branch")
        self.cmb_relation.currentIndexChanged.connect(self._apply_node_relation)
        layout.addWidget(self.cmb_relation)
        self.lbl_relation_hint = QLabel("same color = version line, other color = branch")
        self.lbl_relation_hint.setWordWrap(True)
        self.lbl_relation_hint.setStyleSheet("color: #9aa; font-size: 11px;")
        layout.addWidget(self.lbl_relation_hint)

        layout.addWidget(QLabel("Label / note"))
        self.ipf_node_label = QLineEdit()
        self.ipf_node_label.editingFinished.connect(self._apply_node_label)
        layout.addWidget(self.ipf_node_label)

        layout.addWidget(QLabel("Key (project-relative)"))
        self.lbl_node_key = QLabel("-")
        self.lbl_node_key.setWordWrap(True)
        self.lbl_node_key.setStyleSheet("color: #9aa;")
        layout.addWidget(self.lbl_node_key)

        self.lbl_node_thumb = QLabel()
        self.lbl_node_thumb.setFixedSize(180, 102)
        self.lbl_node_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_node_thumb.setStyleSheet("border: 1px solid #555;")
        self.lbl_node_thumb.setText("No thumbnail")
        layout.addWidget(self.lbl_node_thumb, alignment=Qt.AlignHCenter)

        layout.addStretch(1)
        self._set_inspector_enabled(False)
        return group

    # ============================================================ helpers

    @staticmethod
    def _now_iso():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _selected_graph_name(self):
        item = self.list_graphs.currentItem()
        return item.text() if item is not None else ""

    def _set_inspector_enabled(self, enabled):
        for w in (self.ipf_node_name, self.chk_planned, self.ipf_node_label):
            w.setEnabled(enabled)
        # 관계 콤보는 부모가 있는 노드에서만 의미가 있다(루트는 비활성).
        node = self._selected_node()
        self.cmb_relation.setEnabled(enabled and bool(node and node.parents))

    def _selected_node(self):
        if self._selected_id is None:
            return None
        return self._graph.node_by_id(self._selected_id)

    # ============================================================ saved list

    def on_refresh(self, select=None):
        names = lin.list_names(self._get_store_dir())
        keep = select if select is not None else self._selected_graph_name()

        self.list_graphs.blockSignals(True)
        self.list_graphs.clear()
        self.list_graphs.addItems(names)
        self.list_graphs.blockSignals(False)

        if keep and keep in names:
            self.list_graphs.setCurrentRow(names.index(keep))

    def on_new(self):
        self._graph = lin.LineageGraph()
        self.ipf_name.clear()
        self.list_graphs.blockSignals(True)
        self.list_graphs.setCurrentRow(-1)
        self.list_graphs.blockSignals(False)
        self._render_graph()
        self._log("New lineage graph (empty).")

    def on_select_graph(self, *_):
        name = self._selected_graph_name()
        if not name:
            return
        graph = lin.load(self._get_store_dir(), name)
        if graph is None:
            return
        self._graph = graph
        self.ipf_name.setText(graph.name)
        self._render_graph()
        self._fit_view()

    def on_save(self):
        name = self.ipf_name.text().strip()
        store_dir = self._get_store_dir()

        if not name:
            QMessageBox.warning(self, "Lineage", "Enter a graph name.")
            return
        if not store_dir:
            QMessageBox.warning(self, "Lineage", "Set Store Repo first (File Manager tab).")
            return

        if lin.exists(store_dir, name) and name != self._graph.name:
            ok = QMessageBox.question(
                self, "Lineage", f"A graph named '{name}' already exists. Overwrite?"
            )
            if ok != QMessageBox.Yes:
                return

        self._graph.name = name
        if not self._graph.created_at:
            self._graph.created_at = self._now_iso()

        path = lin.save(store_dir, self._graph)
        self._log(f"Lineage graph saved: {path}")
        self._log("Saved locally - use Push on the File Manager tab to sync.")
        self.on_refresh(select=name)

    def on_delete_graph(self):
        name = self._selected_graph_name()
        if not name:
            QMessageBox.warning(self, "Lineage", "Select a graph first.")
            return
        ok = QMessageBox.question(self, "Lineage", f"Delete graph '{name}'?")
        if ok != QMessageBox.Yes:
            return
        lin.delete(self._get_store_dir(), name)
        self._log(f"Lineage graph deleted: {name}")
        self.on_refresh()

    # ============================================================ node ops

    def on_add_from_scan(self):
        start = self._get_project_root() or os.path.expanduser("~")
        scan_dir = QFileDialog.getExistingDirectory(self, "Select Folder to Scan", start)
        if not scan_dir:
            return

        store = self._get_store()
        # 포맷 무관: 모든 파일을 스캔하고 다이얼로그에서 확장자로 필터한다.
        entries = scanner.scan(scan_dir, store, recursive=True, extensions=None)
        if not entries:
            QMessageBox.information(self, "Lineage", "No files found in that folder.")
            return

        dialog = AddFromScanDialog(entries, self)
        if dialog.exec() != QDialog.Accepted:
            return

        chosen = dialog.checked_entries()
        if not chosen:
            return

        existing_keys = {n.key for n in self._graph.nodes if n.key}
        base = len(self._graph.nodes)
        added = 0
        for k, entry in enumerate(chosen):
            key = entry.get("key") or ""
            if key and key in existing_keys:
                self._log(f"Skipped (already in graph): {entry['file_name']}")
                continue
            node = lin.node_from_entry(entry, lin.next_seq(self._graph))
            node.x = float(60 * ((base + added) % 6))
            node.y = float(40 * (base + added))
            self._graph.nodes.append(node)
            if key:
                existing_keys.add(key)
            added += 1

        self._render_graph()
        self._log(f"Added {added} node(s). Use Connect Mode to link, then Auto Layout.")

    def on_add_file(self):
        start = self._get_project_root() or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(self, "Select File", start, "All Files (*.*)")
        if not path:
            return

        store = self._get_store()
        node = lin.node_from_path(path, store, lin.next_seq(self._graph))

        if node.key and node.key in {n.key for n in self._graph.nodes if n.key}:
            QMessageBox.information(self, "Lineage", "That file is already in the graph.")
            return

        count = len(self._graph.nodes)
        node.x = float(60 * (count % 6))
        node.y = float(40 * count)
        self._graph.nodes.append(node)
        self._render_graph()
        self._log(f"Added node: {node.file_name}")

    def on_add_planned(self):
        node = lin.LineageNode(
            id=lin.new_node_id(),
            file_name="NEW (planned)",
            planned=True,
            label="제작 예정",
            seq=lin.next_seq(self._graph),
        )
        count = len(self._graph.nodes)
        node.x = float(60 * (count % 6))
        node.y = float(40 * count)
        self._graph.nodes.append(node)
        self._render_graph()
        self._log("Added planned node. Rename it in the Node panel.")

    def on_delete_node(self):
        node = self._selected_node()
        if node is None:
            QMessageBox.warning(self, "Lineage", "Select a node first.")
            return
        ok = QMessageBox.question(self, "Lineage", f"Delete node '{node.file_name}'?")
        if ok != QMessageBox.Yes:
            return
        lin.remove_node(self._graph, node.id)
        self._selected_id = None
        self._render_graph()
        self._populate_inspector(None)
        self._log(f"Deleted node: {node.file_name}")

    def try_add_edge(self, parent_id, child_id):
        child = self._graph.node_by_id(child_id)
        if child is None:
            return
        if parent_id in child.parents:
            self._log("Edge already exists.")
            return
        if lin.would_create_cycle(self._graph, parent_id, child_id):
            QMessageBox.warning(self, "Lineage", "That connection would create a cycle.")
            return
        child.parents.append(parent_id)
        self._render_graph()
        parent = self._graph.node_by_id(parent_id)
        self._log(f"Linked: {parent.file_name if parent else '?'} -> {child.file_name}")

    # ============================================================ reveal in explorer

    def node_abs_path(self, node):
        """노드가 가리키는 실제 파일의 절대경로(존재할 때만). 없으면 "".

        key 는 project_root 기준 상대경로이므로 root + key 로 복원한다. planned/루트 밖
        (key="")/파일 없음/루트 미설정이면 경로가 없다.
        """
        if node is None or not node.key:
            return ""
        store = self._get_store()
        root = getattr(store, "project_root", "") if store is not None else ""
        if not root:
            return ""
        path = os.path.join(root, *node.key.split("/"))
        return path if os.path.exists(path) else ""

    def reveal_node(self, node):
        """노드 파일을 탐색기에서 (폴더를 열고 파일을 선택해) 보여준다."""
        path = self.node_abs_path(node)
        if not path:
            QMessageBox.information(
                self, "Lineage",
                "No file to reveal — this node is planned, out of the project root, "
                "or the file no longer exists at its recorded path.",
            )
            self._log(f"Reveal skipped (no path): {node.file_name if node else '?'}")
            return
        if self._reveal_in_explorer(path):
            self._log(f"Revealed in File Explorer: {path}")
        else:
            self._log(f"Failed to open File Explorer for: {path}")

    @staticmethod
    def _reveal_in_explorer(path):
        """OS 파일 탐색기에서 파일을 선택 상태로 연다(Windows 우선)."""
        path = os.path.normpath(path)
        try:
            if sys.platform.startswith("win"):
                # explorer /select, 는 성공해도 비0 종료코드를 내므로 반환값을 보지 않는다.
                subprocess.Popen(["explorer", "/select,", path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
            return True
        except OSError:
            return False

    # ============================================================ layout / connect

    def on_auto_layout(self):
        if not self._graph.nodes:
            return
        lin.auto_layout(self._graph)
        self._render_graph()
        self._fit_view()
        self._log("Auto layout applied.")

    def on_toggle_connect(self, checked):
        self.scene.set_connect_mode(checked)
        self.btn_connect.setText("Connect Mode (ON)" if checked else "Connect Mode")
        # connect 중에는 노드 드래그/선택을 막아 선 긋기에 집중.
        for item in self._node_items.values():
            item.setFlag(QGraphicsItem.ItemIsMovable, not checked)

    # ============================================================ render

    def _render_graph(self):
        self.scene.clear()
        self._node_items = {}
        self._edge_items = []

        lane_of, _order = lin.compute_lanes(self._graph)

        for node in self._graph.nodes:
            color = lin.lane_color(lane_of.get(node.id, 0))
            item = NodeItem(node, color, self)
            if self.btn_connect.isChecked():
                item.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.scene.addItem(item)
            self._node_items[node.id] = item

        ids = {n.id for n in self._graph.nodes}
        for node in self._graph.nodes:
            child_color = lin.lane_color(lane_of.get(node.id, 0))
            for pid in node.parents:
                if pid not in ids:
                    continue            # 고아 참조는 무시
                edge = EdgeItem(pid, node.id)
                dashed = node.planned or self._graph.node_by_id(pid).planned
                edge.set_style(child_color, dashed)
                self.scene.addItem(edge)
                self._edge_items.append(edge)

        self._reroute_edges()
        self._update_scene_rect()

        # 선택 복원
        if self._selected_id and self._selected_id in self._node_items:
            self._node_items[self._selected_id].setSelected(True)

    def _reroute_edges(self):
        for edge in self._edge_items:
            p = self._node_items.get(edge.parent_id)
            c = self._node_items.get(edge.child_id)
            if p is None or c is None:
                continue
            edge.route(p.bottom_center_scene(), c.top_center_scene())

    def _update_scene_rect(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isNull():
            self.scene.setSceneRect(QRectF(0, 0, 400, 300))
        else:
            self.scene.setSceneRect(rect.adjusted(-200, -200, 200, 200))

    def _fit_view(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isNull():
            self.view.fitInView(rect.adjusted(-40, -40, 40, 40), Qt.KeepAspectRatio)

    # ============================================================ inspector

    def _on_selection_changed(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, NodeItem)]
        if items:
            self._selected_id = items[0].node.id
            self._populate_inspector(items[0].node)
        else:
            self._selected_id = None
            self._populate_inspector(None)

    def _populate_inspector(self, node):
        block = (self.ipf_node_name, self.chk_planned,
                 self.ipf_node_label, self.cmb_relation)
        for w in block:
            w.blockSignals(True)

        if node is None:
            self.ipf_node_name.clear()
            self.chk_planned.setChecked(False)
            self.ipf_node_label.clear()
            self.cmb_relation.setCurrentIndex(0)
            self.lbl_node_key.setText("-")
            self.lbl_node_thumb.clear()
            self.lbl_node_thumb.setText("No thumbnail")
            self._set_inspector_enabled(False)
        else:
            self.ipf_node_name.setText(node.file_name)
            self.chk_planned.setChecked(node.planned)
            self.ipf_node_label.setText(node.label)
            idx = self.cmb_relation.findData(node.relation or "")
            self.cmb_relation.setCurrentIndex(idx if idx >= 0 else 0)
            self.lbl_node_key.setText(node.key or "(planned / out of root)")
            self._refresh_node_thumb(node)
            self._set_inspector_enabled(True)

        for w in block:
            w.blockSignals(False)

    def _refresh_node_thumb(self, node):
        self.lbl_node_thumb.clear()
        if node.key:
            store = self._get_store()
            thumb = store.thumb_abs(node.key)
            if os.path.isfile(thumb):
                pix = QPixmap(thumb).scaled(
                    180, 102, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.lbl_node_thumb.setPixmap(pix)
                return
        self.lbl_node_thumb.setText("No thumbnail")

    def _apply_node_name(self):
        node = self._selected_node()
        if node is None:
            return
        node.file_name = self.ipf_node_name.text().strip()
        item = self._node_items.get(node.id)
        if item is not None:
            item.update()

    def _apply_node_planned(self, checked):
        node = self._selected_node()
        if node is None:
            return
        node.planned = bool(checked)
        # planned 는 엣지 점선 스타일에 영향 → 재렌더.
        self._render_graph()

    def _apply_node_label(self):
        node = self._selected_node()
        if node is None:
            return
        node.label = self.ipf_node_label.text().strip()
        item = self._node_items.get(node.id)
        if item is not None:
            item.update()

    def _apply_node_relation(self, *_):
        node = self._selected_node()
        if node is None:
            return
        node.relation = self.cmb_relation.currentData() or ""
        # 관계는 레인/색 계산에 영향 → 재렌더(자동 트렁크 선택이 바뀜).
        self._render_graph()
