# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - Blend Weights 탭 (계획서 §4)
#
# blendWeighted 하나를 골라 input / weight 를 표로 본다. weight 원소가 없는 input(계산은 1.0, UI 에는 안 보임)을
# 빨갛게 표시하고, input 을 추가할 때 weight 를 같이 만든다. 로직은 app/core/blend_weights.py.

import maya.cmds as cmds

from Framework.qt.qt import *

from ..core import blend_weights as bwm


COLS = ["Idx", "Input (source)", "Weight", "Input x Weight", "State"]
RED = QColor("#ff6b6b")
GREY = QColor("#9a9a9a")


class BlendWeightsTab(QWidget):

    def __init__(self, log, parent=None):
        super().__init__(parent)
        self._log = log
        self._updating = False
        self._build()
        self.refresh_nodes()

    # ------------------------------------------------------------------ UI

    def _build(self):
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Node"))
        self.cmb_node = QComboBox()
        self.cmb_node.setMinimumWidth(220)
        self.cmb_node.currentTextChanged.connect(lambda *_: self.refresh_table())
        row.addWidget(self.cmb_node, 1)
        btn_sel = QPushButton("<< Sel")
        btn_sel.setToolTip("Use the selected blendWeighted node")
        btn_sel.clicked.connect(self.on_pick_selected)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.on_refresh)
        row.addWidget(btn_sel)
        row.addWidget(btn_refresh)
        layout.addLayout(row)

        frow = QHBoxLayout()
        frow.addWidget(QLabel("Filter"))
        self.le_filter = QLineEdit()
        self.le_filter.setPlaceholderText("part of the node name, e.g. bw_mouth")
        self.le_filter.textChanged.connect(lambda *_: self.refresh_nodes())
        frow.addWidget(self.le_filter, 1)
        self.cb_missing_only = QCheckBox("Missing weights only")
        self.cb_missing_only.setToolTip("List only blendWeighted nodes that have inputs without a weight element")
        self.cb_missing_only.toggled.connect(lambda *_: self.refresh_nodes())
        frow.addWidget(self.cb_missing_only)
        layout.addLayout(frow)

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in (0, 2, 3, 4):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(180)
        layout.addWidget(self.table, 1)

        self.lb_output = QLabel("output -")
        layout.addWidget(self.lb_output)

        add_box = QGroupBox("Add Input (connects and creates its weight together)")
        arow = QHBoxLayout(add_box)
        arow.addWidget(QLabel("Source"))
        self.le_source = QLineEdit()
        self.le_source.setPlaceholderText("node.attribute  (e.g. JALI1:JALI_IN.OHH)")
        arow.addWidget(self.le_source, 1)
        btn_src = QPushButton("<< Sel Attr")
        btn_src.setToolTip("Selected node + the attribute highlighted in the Channel Box")
        btn_src.clicked.connect(self.on_pick_source)
        arow.addWidget(btn_src)
        arow.addWidget(QLabel("Weight"))
        self.ds_weight = QDoubleSpinBox()
        self.ds_weight.setDecimals(4)
        self.ds_weight.setRange(-1000.0, 1000.0)
        self.ds_weight.setSingleStep(0.01)
        self.ds_weight.setValue(0.1)
        arow.addWidget(self.ds_weight)
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self.on_add)
        arow.addWidget(btn_add)
        layout.addWidget(add_box)

        brow = QHBoxLayout()
        btn_missing = QPushButton("Create Missing Weights (1.0)")
        btn_missing.setToolTip("Inputs without a weight element are already computed as 1.0.\n"
                               "This creates those elements with 1.0 - the result does not change,\n"
                               "they just become visible and editable.")
        btn_missing.clicked.connect(self.on_create_missing)
        btn_remove = QPushButton("Remove Selected")
        btn_remove.setToolTip("Remove input[i] (and its connection) and weight[i] of the selected rows")
        btn_remove.clicked.connect(self.on_remove)
        btn_select = QPushButton("Select Source")
        btn_select.clicked.connect(self.on_select_source)
        brow.addWidget(btn_missing)
        brow.addWidget(btn_remove)
        brow.addWidget(btn_select)
        layout.addLayout(brow)

    # ------------------------------------------------------------------ 목록

    def current_node(self):
        name = self.cmb_node.currentText()
        return name if name and cmds.objExists(name) else None

    def refresh_nodes(self, keep=None):
        keep = keep or self.cmb_node.currentText()
        text = self.le_filter.text().strip().lower()
        nodes = [n for n in bwm.list_nodes() if text in n.lower()]
        if self.cb_missing_only.isChecked():
            nodes = [n for n in nodes if bwm.missing_weights(n)]
        self.cmb_node.blockSignals(True)
        self.cmb_node.clear()
        self.cmb_node.addItems(nodes)
        if keep and keep in nodes:
            self.cmb_node.setCurrentText(keep)
        self.cmb_node.blockSignals(False)
        self.refresh_table()

    def on_refresh(self, *args):
        self.refresh_nodes()
        total = [n for n in bwm.list_nodes() if bwm.missing_weights(n)]
        if total:
            self._log("[WARN] {0} blendWeighted node(s) have inputs without a weight element: {1}".format(
                len(total), ", ".join(total[:8]) + (" ..." if len(total) > 8 else "")))

    def on_pick_selected(self, *args):
        sel = cmds.ls(sl=True, type="blendWeighted") or []
        if not sel:
            self._log("[WARN] Select a blendWeighted node first.")
            return
        self.le_filter.blockSignals(True)
        self.le_filter.clear()
        self.le_filter.blockSignals(False)
        self.cb_missing_only.setChecked(False)
        self.refresh_nodes(keep=sel[0])

    def refresh_table(self):
        bw = self.current_node()
        self._updating = True
        self.table.setRowCount(0)
        if not bw:
            self.lb_output.setText("output -")
            self._updating = False
            return
        for r, (idx, src, w, has_w) in enumerate(bwm.rows(bw)):
            self.table.insertRow(r)
            self.table.setItem(r, 0, self._item(str(idx), idx))
            self.table.setItem(r, 1, self._item(src or "(not connected)"))
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(-1000.0, 1000.0)
            spin.setSingleStep(0.01)
            spin.setValue(w if has_w else bwm.MISSING_WEIGHT_VALUE)
            if not has_w:
                spin.setToolTip("No weight element - computed as 1.0. Editing creates it.")
            spin.valueChanged.connect(lambda v, i=idx: self._on_weight_changed(i, v))
            self.table.setCellWidget(r, 2, spin)
            value = cmds.getAttr("{0}.input[{1}]".format(bw, idx)) if src else 0.0
            eff = value * (w if has_w else bwm.MISSING_WEIGHT_VALUE)
            self.table.setItem(r, 3, self._item("{0:.4f}".format(eff)))
            if not has_w:
                state, color = "no weight element (= 1.0)", RED
            elif not src:
                state, color = "no input", GREY
            else:
                state, color = "OK", None
            item = self._item(state)
            if color is not None:
                item.setForeground(color)
            self.table.setItem(r, 4, item)
        self.lb_output.setText("output {0:.4f}".format(cmds.getAttr(bw + ".output")))
        self._updating = False

    @staticmethod
    def _item(text, data=None):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        if data is not None:
            item.setData(Qt.UserRole, data)
        return item

    def _selected_indices(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        return [self.table.item(r, 0).data(Qt.UserRole) for r in rows]

    # ------------------------------------------------------------------ 편집

    def _on_weight_changed(self, idx, value):
        if self._updating:
            return
        bw = self.current_node()
        if bw:
            bwm.set_weight(bw, idx, value)
            self.lb_output.setText("output {0:.4f}".format(cmds.getAttr(bw + ".output")))

    def on_pick_source(self, *args):
        sel = cmds.ls(sl=True) or []
        if not sel:
            self._log("[WARN] Select the source node first (and highlight an attribute in the Channel Box).")
            return
        attrs = []
        try:
            attrs = cmds.channelBox("mainChannelBox", q=True, selectedMainAttributes=True) or []
        except RuntimeError:
            pass
        if attrs:
            long_name = cmds.attributeQuery(attrs[0], node=sel[0], longName=True)
            self.le_source.setText("{0}.{1}".format(sel[0], long_name))
        else:
            self.le_source.setText(sel[0] + ".")
            self._log("[INFO] No Channel Box attribute highlighted - type the attribute after the dot.")

    def on_add(self, *args):
        bw = self.current_node()
        src = self.le_source.text().strip()
        if not bw:
            self._log("[ERROR] Pick a blendWeighted node first.")
            return
        if "." not in src or src.endswith("."):
            self._log("[ERROR] Source must be node.attribute")
            return
        try:
            idx = bwm.add_input(bw, src, self.ds_weight.value())
        except (ValueError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        self._log("[OK] {0}.input[{1}] <- {2}, weight[{1}] = {3:g}".format(bw, idx, src, self.ds_weight.value()))
        self.refresh_table()

    def on_create_missing(self, *args):
        bw = self.current_node()
        if not bw:
            return
        idxs = bwm.create_missing(bw)
        if idxs:
            self._log("[OK] {0}: created weight {1} = 1.0 (result unchanged, now visible)".format(
                bw, ", ".join("[{0}]".format(i) for i in idxs)))
        else:
            self._log("[INFO] {0}: no missing weights".format(bw))
        self.refresh_table()

    def on_remove(self, *args):
        bw = self.current_node()
        idxs = self._selected_indices()
        if not bw or not idxs:
            self._log("[WARN] Select rows to remove.")
            return
        bwm.remove(bw, idxs)
        self._log("[OK] {0}: removed input + weight {1}".format(bw, ", ".join("[{0}]".format(i) for i in idxs)))
        self.refresh_table()

    def on_select_source(self, *args):
        bw = self.current_node()
        nodes = []
        for i in self._selected_indices():
            src = bwm.input_source(bw, i) if bw else None
            if src:
                nodes.append(src.split(".", 1)[0])
        if nodes:
            cmds.select(nodes)
        else:
            self._log("[WARN] No connected source in the selected rows.")
