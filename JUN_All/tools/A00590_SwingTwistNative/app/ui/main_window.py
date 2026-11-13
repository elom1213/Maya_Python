# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-13
# A00590_SwingTwistNative - Qt UI (in-Maya)
#
# Build 탭: MetaHuman `create_swing_twist_evaluator` 와 같은 입력(Start / End / Swing 조인트, Twist 조인트 + 블렌드,
#           From End) 을 받아 quatNodes 노드망을 만든다 - 코어 Framework/core/maya_swing_twist.build().
# Rigs 탭:  씬에 만든 노드망(홀더 network 노드) 목록 · 선택 · Build 탭으로 불러오기 · 삭제.
# 블렌드는 홀더의 swingBlend / twistBlend[i] 어트리뷰트 - 홀더를 고르면 Channel Box 에서 바로 고친다.
# 모든 UI 문자열/로그는 영어.

import maya.cmds as cmds

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QPushButton,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01
from Framework.qt.pin_style import apply_pin_style
from Framework.core import maya_swing_twist as ST

from tools.A00590_SwingTwistNative.app.config.version import VERSION, LAST_UPDATE


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00590_SwingTwistNative_window"

DEFAULT_TWIST_BLEND = 0.5

BLEND_TIP = ("Each blend slides its output from the full counter rotation (0) to identity (1):\n"
             "  Twist: 0 = cancel the start twist (From End: copy the end twist), 1 = zero rotation.\n"
             "  Swing: 0 = cancel the whole start rotation, 1 = cancel the start twist only.\n"
             "Same as the original SwingTwistEvaluatorNode. Values outside 0-1 extrapolate.")

RIG_COLUMNS = ["Holder", "Start", "Swing", "Twists", "From End", "Nodes"]


def _short(node):
    return node.split("|")[-1] if node else ""


def _blend_spin(value):
    spin = QDoubleSpinBox()
    spin.setRange(-10.0, 10.0)
    spin.setDecimals(3)
    spin.setSingleStep(0.05)
    spin.setKeyboardTracking(False)
    spin.setValue(float(value))
    spin.setToolTip(BLEND_TIP)
    return spin


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("Swing Twist Native v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(460, 640)

        # 확인 창 - 테스트에서 끌 수 있게 속성으로
        self.confirm_delete = True

        self.build_ui()
        self.refresh_rigs()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Pin(우)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)
        apply_pin_style(self.pin_button)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab(), "Build")
        self.tabs.addTab(self._rigs_tab(), "Rigs")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs, stretch=1)

        # 공용 로그 위젯(Expand / Clear / Copy)
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Swing Twist Native - Log",
            object_name="JUN_A00590_SwingTwistNative_log_window")
        self.log_view.setMinimumHeight(110)
        self.log_view.setMaximumHeight(220)
        main_layout.addWidget(self.log_view)

        self.tab_fit = JUN_mod_tabFit_qt_v01(self, self.tabs)

    # ---------------------------------------------------------------- Build
    def _joint_row(self, grid, row, label, tip):
        grid.addWidget(QLabel(label), row, 0)
        field = QLineEdit()
        field.setPlaceholderText("(none)")
        field.setToolTip(tip)
        grid.addWidget(field, row, 1)
        btn = QPushButton("Set")
        btn.setToolTip("Set from the first selected object")
        btn.setFixedWidth(52)
        btn.clicked.connect(lambda: self._set_from_selection(field))
        grid.addWidget(btn, row, 2)
        return field

    def _build_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        grid = QGridLayout()
        grid.addWidget(QLabel("Name"), 0, 0)
        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("(start joint name)")
        self.le_name.setToolTip("Prefix of the created nodes. The holder is <Name>_SwingTwist.")
        grid.addWidget(self.le_name, 0, 1, 1, 2)

        self.le_start = self._joint_row(grid, 1, "Start", "Input joint. Its rotate is read as XYZ (rotate order and joint orient are ignored, same as the original).")
        self.le_end = self._joint_row(grid, 2, "End", "Optional input joint - used only when From End is on.")
        self.le_swing = self._joint_row(grid, 3, "Swing", "Optional output joint for the swing part.")

        grid.addWidget(QLabel("Swing Blend"), 4, 0)
        self.sp_swing_blend = _blend_spin(0.0)
        grid.addWidget(self.sp_swing_blend, 4, 1, 1, 2)

        self.chk_from_end = QCheckBox("From End")
        self.chk_from_end.setToolTip("Twist outputs follow the END joint's X twist instead of cancelling the start twist.\n"
                                     "Same as the original fromEnd attribute.")
        grid.addWidget(self.chk_from_end, 5, 1, 1, 2)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)

        lay.addWidget(QLabel("Twist Joints"))
        self.tbl_twist = QTableWidget(0, 2)
        self.tbl_twist.setHorizontalHeaderLabels(["Joint", "Blend"])
        self.tbl_twist.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_twist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_twist.verticalHeader().setVisible(True)
        self.tbl_twist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_twist.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_twist.setMinimumHeight(110)
        self.tbl_twist.setToolTip("Output joints for the twist part, in index order (twists[0], twists[1], ...).")
        lay.addWidget(self.tbl_twist, stretch=1)

        row = QHBoxLayout()
        for label, slot, tip in (
                ("Add Selected", self.add_twist_selected, "Add the selected objects as twist joints"),
                ("Remove", self.remove_twist_rows, "Remove the selected rows"),
                ("Up", lambda: self.move_twist_row(-1), "Move the selected row up"),
                ("Down", lambda: self.move_twist_row(1), "Move the selected row down"),
                ("Clear", self.clear_twists, "Remove every row")):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        lay.addLayout(row)

        note = QLabel("Twist blend: 0 = cancel start twist, 1 = zero.  "
                      "Swing blend: 0 = cancel whole start rotation, 1 = cancel twist only.")
        note.setWordWrap(True)
        note.setToolTip(BLEND_TIP)
        lay.addWidget(note)

        self.btn_build = QPushButton("Build")
        self.btn_build.setMinimumHeight(34)
        self.btn_build.setToolTip("Create the quatNodes network that replaces SwingTwistEvaluatorNode.\n"
                                  "One Ctrl+Z undoes it.")
        self.btn_build.clicked.connect(self.build_rig)
        lay.addWidget(self.btn_build)
        return page

    # ---------------------------------------------------------------- Rigs
    def _rigs_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        self.tbl_rigs = QTableWidget(0, len(RIG_COLUMNS))
        self.tbl_rigs.setHorizontalHeaderLabels(RIG_COLUMNS)
        self.tbl_rigs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tbl_rigs.horizontalHeader().setStretchLastSection(True)
        self.tbl_rigs.verticalHeader().setVisible(False)
        self.tbl_rigs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_rigs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_rigs.setMinimumHeight(140)
        self.tbl_rigs.itemSelectionChanged.connect(self._on_rig_selection)
        lay.addWidget(self.tbl_rigs, stretch=1)

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for target, label, slot, tip in (
                (row1, "Refresh", self.refresh_rigs, "Re-read the networks in the scene"),
                (row1, "Select Holder", self.select_holders,
                 "Select the holder node - edit swingBlend / twistBlend in the Channel Box"),
                (row1, "Select Nodes", self.select_nodes, "Select every node of the network"),
                (row2, "Select Joints", self.select_joints, "Select the input and output joints"),
                (row2, "Load to Build", self.load_to_build, "Copy this network's settings into the Build tab"),
                (row2, "Delete", self.delete_rigs,
                 "Delete the network. Output joints keep their last rotate values.")):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            target.addWidget(btn)
        lay.addLayout(row1)
        lay.addLayout(row2)
        return page

    # ==================================================================
    # 로그 · 공통
    # ==================================================================

    def log(self, msg):
        self.log_view.appendPlainText(msg)

    @staticmethod
    def _selection():
        return cmds.ls(selection=True) or []

    def _set_from_selection(self, field):
        sel = self._selection()
        if not sel:
            self.log("[WARN] Nothing selected.")
            return
        field.setText(sel[0])
        if field is self.le_start and not self.le_name.text().strip():
            self.le_name.setText(_short(sel[0]))

    def _on_tab_changed(self, index):
        if self.tabs.widget(index) is self.tbl_rigs.parent():
            self.refresh_rigs()

    # ==================================================================
    # Twist 표
    # ==================================================================

    def _twist_rows(self):
        rows = []
        for r in range(self.tbl_twist.rowCount()):
            item = self.tbl_twist.item(r, 0)
            spin = self.tbl_twist.cellWidget(r, 1)
            rows.append((item.text() if item else "", spin.value() if spin else DEFAULT_TWIST_BLEND))
        return rows

    def _set_twist_rows(self, rows):
        self.tbl_twist.setRowCount(0)
        for joint, blend in rows:
            r = self.tbl_twist.rowCount()
            self.tbl_twist.insertRow(r)
            item = QTableWidgetItem(joint or "")
            item.setToolTip(joint or "(empty index)")
            self.tbl_twist.setItem(r, 0, item)
            self.tbl_twist.setCellWidget(r, 1, _blend_spin(blend))

    def add_twist_selected(self):
        sel = self._selection()
        if not sel:
            self.log("[WARN] Nothing selected.")
            return
        rows = self._twist_rows()
        have = {j for j, _ in rows}
        added = [s for s in sel if s not in have]
        self._set_twist_rows(rows + [(s, DEFAULT_TWIST_BLEND) for s in added])
        if len(added) < len(sel):
            self.log("[WARN] Skipped {0} joint(s) already in the list.".format(len(sel) - len(added)))

    def _selected_twist_rows(self):
        return sorted({i.row() for i in self.tbl_twist.selectedIndexes()})

    def remove_twist_rows(self):
        drop = set(self._selected_twist_rows())
        self._set_twist_rows([r for i, r in enumerate(self._twist_rows()) if i not in drop])

    def move_twist_row(self, step):
        sel = self._selected_twist_rows()
        if len(sel) != 1:
            return
        i, rows = sel[0], self._twist_rows()
        j = i + step
        if not 0 <= j < len(rows):
            return
        rows[i], rows[j] = rows[j], rows[i]
        self._set_twist_rows(rows)
        self.tbl_twist.selectRow(j)

    def clear_twists(self):
        self._set_twist_rows([])

    # ==================================================================
    # Build
    # ==================================================================

    def build_args(self):
        rows = self._twist_rows()
        start = self.le_start.text().strip()
        return {
            "name": self.le_name.text().strip() or _short(start) or "swingTwist",
            "start_joint": start,
            "end_joint": self.le_end.text().strip() or None,
            "swing_joint": self.le_swing.text().strip() or None,
            "swing_blend": self.sp_swing_blend.value(),
            "twist_joints": [j.strip() or None for j, _ in rows],
            "twist_blends": [b for _, b in rows],
            "from_end": self.chk_from_end.isChecked(),
        }

    def build_rig(self):
        args = self.build_args()
        self.log("--- Build {0} ---".format(args["name"]))
        try:
            holder = ST.build(log=self.log, **args)
        except ST.SwingTwistError as exc:
            self.log("[ERROR] " + str(exc))
            return None
        except RuntimeError as exc:
            self.log("[ERROR] Maya: {0}".format(str(exc).strip()))
            return None
        self.refresh_rigs(select=holder)
        return holder

    # ==================================================================
    # Rigs
    # ==================================================================

    def refresh_rigs(self, select=None):
        holders = ST.list_holders()
        self.tbl_rigs.setRowCount(0)
        for h in holders:
            spec = ST.read_holder(h)
            twists = [j for j in spec["twist_joints"] if j]
            values = [h, _short(spec["start_joint"]), _short(spec["swing_joint"]) or "-",
                      str(len(twists)), "Yes" if spec["from_end"] else "-", str(len(ST.members(h)))]
            r = self.tbl_rigs.rowCount()
            self.tbl_rigs.insertRow(r)
            for c, v in enumerate(values):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setData(Qt.UserRole, h)
                    item.setToolTip("Swing blend {0:.3f}\nTwists: {1}".format(
                        spec["swing_blend"],
                        ", ".join("{0} ({1:.3f})".format(_short(j), b)
                                  for j, b in zip(spec["twist_joints"], spec["twist_blends"]) if j) or "-"))
                self.tbl_rigs.setItem(r, c, item)
            if h == select:
                self.tbl_rigs.selectRow(r)
        return holders

    def selected_holders(self):
        rows = sorted({i.row() for i in self.tbl_rigs.selectedIndexes()})
        out = []
        for r in rows:
            h = self.tbl_rigs.item(r, 0).data(Qt.UserRole)
            if cmds.objExists(h):
                out.append(h)
        return out

    def _need_holders(self):
        holders = self.selected_holders()
        if not holders:
            self.log("[WARN] Select a network in the list first.")
        return holders

    def _on_rig_selection(self):
        holders = self.selected_holders()
        if holders:
            cmds.select(holders, replace=True)

    def select_holders(self):
        holders = self._need_holders()
        if holders:
            cmds.select(holders, replace=True)
            self.log("Selected {0} holder(s) - edit blends in the Channel Box.".format(len(holders)))

    def select_nodes(self):
        holders = self._need_holders()
        nodes = [n for h in holders for n in ST.members(h)]
        if nodes:
            cmds.select(nodes, replace=True)
            self.log("Selected {0} node(s).".format(len(nodes)))

    def select_joints(self):
        joints = []
        for h in self._need_holders():
            spec = ST.read_holder(h)
            for j in [spec["start_joint"], spec["end_joint"], spec["swing_joint"]] + spec["twist_joints"]:
                if j and j not in joints:
                    joints.append(j)
        if joints:
            cmds.select(joints, replace=True)
            self.log("Selected {0} joint(s).".format(len(joints)))

    def load_to_build(self):
        holders = self._need_holders()
        if not holders:
            return
        spec = ST.read_holder(holders[0])
        self.le_name.setText(spec["name"])
        self.le_start.setText(spec["start_joint"] or "")
        self.le_end.setText(spec["end_joint"] or "")
        self.le_swing.setText(spec["swing_joint"] or "")
        self.sp_swing_blend.setValue(spec["swing_blend"])
        self.chk_from_end.setChecked(spec["from_end"])
        self._set_twist_rows(list(zip(spec["twist_joints"], spec["twist_blends"])))
        self.tabs.setCurrentIndex(0)
        self.log("Loaded {0} into the Build tab. Delete the old network before building again "
                 "(its outputs are still connected).".format(holders[0]))

    def delete_rigs(self):
        holders = self._need_holders()
        if not holders:
            return
        if self.confirm_delete:
            answer = QMessageBox.question(
                self, "Delete",
                "Delete these networks?\n\n  - {0}\n\nOutput joints keep their last rotate values.\n"
                "One Ctrl+Z undoes it.".format("\n  - ".join(holders)),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                self.log("Cancelled.")
                return
        for h in holders:
            n = ST.delete_rig(h)
            self.log("Deleted {0} ({1} nodes).".format(h, n))
        self.refresh_rigs()

    # ==================================================================
    # 창 동작
    # ==================================================================

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Swing Twist Native v{0}\nLast update : {1}\n\n"
            "Builds a network of Maya quatNodes that gives the same result as\n"
            "MetaHuman's SwingTwistEvaluatorNode - no Epic plugin needed.\n\n"
            "- X is the twist axis, rotations are read and written as XYZ\n"
            "  (rotate order and joint orient are ignored, like the original).\n"
            "- Twist blend: 0 = cancel the start twist, 1 = zero rotation.\n"
            "- Swing blend: 0 = cancel the whole start rotation, 1 = cancel the twist only.\n"
            "- Blends live on the holder node (<name>_SwingTwist).".format(VERSION, LAST_UPDATE),
        )
