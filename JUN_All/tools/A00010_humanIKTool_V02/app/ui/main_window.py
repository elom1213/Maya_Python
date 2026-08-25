# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-25
# A00010_humanIKTool_V02 - Qt UI (PySide)
# 레거시 A00010_humanIKTool 의 maya.cmds UI 를 PySide(arch B)로 마이그레이션.
#
# v02.01 : 상위 탭 2개(Assign / Mirror). HIK 캐릭터 노드 선택은 두 탭이 공유하므로
#          탭 밖 상단에 그대로 둔다.

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

from tools.A00010_humanIKTool_V02.app.config.version import VERSION
from tools.A00010_humanIKTool_V02.app.core import (
    HIKManager, CustomRigManager, MODE_NAME, MODE_POSITION, MODE_AUTO,
)


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00010_humanIKTool_V02_window"


# 결과 표의 상태별 색. 다크 테마 위에서 읽히는 채도로 고른다.
STATUS_COLORS = {
    "ok":    QColor(120, 200, 130),
    "ready": QColor(120, 175, 230),
    "skip":  QColor(220, 185, 110),
    "fail":  QColor(225, 110, 110),
}

MATCH_MODES = [
    ("Auto (name, then position)", MODE_AUTO),
    ("Name only", MODE_NAME),
    ("Position only", MODE_POSITION),
]


class MainWindow(QWidget):

    def __init__(self):

        # 마야 메인 윈도우에 parent (뷰포트 위에는 떠 있되 다른 툴 창과 정상 Z-order)
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 620
        self.win_height = 760
        self.win_title  = f"HumanIK Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # -------------------------
        # HIK character node 섹션 (Assign / Mirror 두 탭이 공유하므로 탭 밖에 둔다)
        # -------------------------
        grp_hik = QGroupBox("HumanIK Character Node")
        hik_layout = QVBoxLayout(grp_hik)

        self.btn_get_hik = QPushButton("Get HIK Nodes")
        self.btn_get_hik.clicked.connect(self.on_get_hik_nodes)
        hik_layout.addWidget(self.btn_get_hik)

        # HIK 노드는 하나만 대상으로 하므로 단일 선택.
        self.list_hik = QListWidget()
        self.list_hik.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_hik.setMaximumHeight(90)
        hik_layout.addWidget(self.list_hik)

        main_layout.addWidget(grp_hik)

        # -------------------------
        # 탭
        # -------------------------
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_assign_tab(), "Assign")
        self.tabs.addTab(self._build_mirror_tab(), "Mirror")
        main_layout.addWidget(self.tabs, 1)

        # -------------------------
        # 로그
        # -------------------------
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # -------------------------------------------------- Assign 탭

    def _build_assign_tab(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        # 조인트 리스트 (재사용 위젯)
        # 순서가 슬롯 매칭 순서이므로 Up/Down 으로 정렬 가능하게 둔다.
        grp_jnt = QGroupBox("Joints to Assign")
        jnt_layout = QVBoxLayout(grp_jnt)

        self.tsl_joints = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints (order = slot order)",
            show_select=True, show_add=True, show_del=True,
            show_up=True, show_down=True, show_sort=True,
            multi_select=True, list_min_height=160,
            select_label="Select Joints",
            log_callback=self.log,
        )
        jnt_layout.addWidget(self.tsl_joints)

        layout.addWidget(grp_jnt, 1)

        # 본 체인 선택 + Assign
        grp_chain = QGroupBox("Bone Chain")
        chain_layout = QVBoxLayout(grp_chain)

        self.cmb_chain = QComboBox()
        self.cmb_chain.addItems(HIKManager.chain_labels())
        chain_layout.addWidget(self.cmb_chain)

        self.btn_assign = QPushButton("Assign Joints")
        self.btn_assign.clicked.connect(self.on_assign_joints)
        chain_layout.addWidget(self.btn_assign)

        layout.addWidget(grp_chain)

        return page

    # -------------------------------------------------- Mirror 탭

    def _build_mirror_tab(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        # --- 어떤 슬롯을 미러할지 ---
        grp_what = QGroupBox("What to Mirror")
        form_what = QGridLayout(grp_what)

        self.cmb_direction = QComboBox()
        self.cmb_direction.addItems(HIKManager.DIRECTIONS)
        self.cmb_direction.setToolTip(
            "Which side is already assigned. Its slots are read and copied to the other side.")
        form_what.addWidget(QLabel("Direction"), 0, 0)
        form_what.addWidget(self.cmb_direction, 0, 1)

        self.cmb_scope = QComboBox()
        self.cmb_scope.addItems(HIKManager.MIRROR_SCOPES)
        self.cmb_scope.setToolTip(
            "All Sided Slots : every assigned slot that has a left/right counterpart "
            "(arms, legs, fingers, toes, rolls).\n"
            "Arms & Legs : shoulder-to-hand and leg chains only.\n"
            "Selected Chain : the chain picked in the Assign tab.")
        form_what.addWidget(QLabel("Scope"), 1, 0)
        form_what.addWidget(self.cmb_scope, 1, 1)

        form_what.setColumnStretch(1, 1)
        layout.addWidget(grp_what)

        # --- 반대쪽 노드를 무엇으로 찾을지 ---
        grp_how = QGroupBox("How to Find the Opposite Node")
        form_how = QGridLayout(grp_how)

        self.cmb_mode = QComboBox()
        for label, _ in MATCH_MODES:
            self.cmb_mode.addItem(label)
        self.cmb_mode.setToolTip(
            "Name : flip the side token in the name (L_arm_JNT -> R_arm_JNT). Pose independent.\n"
            "Position : mirror the world position and take the nearest node. "
            "Only correct while the rig is in a symmetric pose.\n"
            "Auto : name first, position for whatever the name could not resolve.")
        self.cmb_mode.currentIndexChanged.connect(self._sync_position_controls)
        form_how.addWidget(QLabel("Match By"), 0, 0)
        form_how.addWidget(self.cmb_mode, 0, 1, 1, 3)

        self.cmb_axis = QComboBox()
        self.cmb_axis.addItems(["X", "Y", "Z"])
        self.cmb_axis.setToolTip("Mirror plane normal for position matching. X = the usual YZ plane.")
        self.lbl_axis = QLabel("Mirror Axis")
        form_how.addWidget(self.lbl_axis, 1, 0)
        form_how.addWidget(self.cmb_axis, 1, 1)

        self.spn_tolerance = QDoubleSpinBox()
        self.spn_tolerance.setDecimals(3)
        self.spn_tolerance.setRange(0.0, 10000.0)
        self.spn_tolerance.setValue(1.0)
        self.spn_tolerance.setSingleStep(0.1)
        # 타이핑 도중 값이 되쓰이지 않도록 (0.1 -> 0.100 으로 잘리는 문제)
        self.spn_tolerance.setKeyboardTracking(False)
        self.spn_tolerance.setToolTip(
            "Maximum distance (scene units) between the mirrored position and the candidate. "
            "Anything farther is reported as unresolved instead of being guessed.")
        self.lbl_tolerance = QLabel("Tolerance")
        form_how.addWidget(self.lbl_tolerance, 1, 2)
        form_how.addWidget(self.spn_tolerance, 1, 3)

        form_how.setColumnStretch(1, 1)
        form_how.setColumnStretch(3, 1)
        layout.addWidget(grp_how)

        # --- 옵션 ---
        grp_opt = QGroupBox("Options")
        opt_layout = QHBoxLayout(grp_opt)

        self.chk_overwrite = QCheckBox("Overwrite existing")
        self.chk_overwrite.setToolTip(
            "Off : a target slot that already holds something is left alone and reported as skipped.")
        opt_layout.addWidget(self.chk_overwrite)

        self.chk_copy_offset = QCheckBox("Copy mapping offsets (controllers)")
        self.chk_copy_offset.setChecked(True)
        self.chk_copy_offset.setToolTip(
            "Custom Rig only. Offsets are copied verbatim, not negated - check them if your "
            "right-side controllers are built with a different orientation convention.")
        opt_layout.addWidget(self.chk_copy_offset)

        opt_layout.addStretch(1)
        layout.addWidget(grp_opt)

        # --- 실행 ---
        grp_run = QGroupBox("Run")
        run_layout = QGridLayout(grp_run)

        self.btn_preview_joints = QPushButton("Preview Joints")
        self.btn_preview_joints.setToolTip("Show what would be assigned. Changes nothing.")
        self.btn_preview_joints.clicked.connect(lambda: self.on_mirror_joints(True))
        run_layout.addWidget(self.btn_preview_joints, 0, 0)

        self.btn_mirror_joints = QPushButton("Mirror Joints")
        self.btn_mirror_joints.clicked.connect(lambda: self.on_mirror_joints(False))
        run_layout.addWidget(self.btn_mirror_joints, 0, 1)

        self.btn_preview_ctrl = QPushButton("Preview Controllers")
        self.btn_preview_ctrl.setToolTip(
            "Custom Rig mapping preview. Requires a Custom Rig created in the HumanIK window.")
        self.btn_preview_ctrl.clicked.connect(lambda: self.on_mirror_controllers(True))
        run_layout.addWidget(self.btn_preview_ctrl, 1, 0)

        self.btn_mirror_ctrl = QPushButton("Mirror Controllers")
        self.btn_mirror_ctrl.clicked.connect(lambda: self.on_mirror_controllers(False))
        run_layout.addWidget(self.btn_mirror_ctrl, 1, 1)

        run_layout.setColumnStretch(0, 1)
        run_layout.setColumnStretch(1, 1)
        layout.addWidget(grp_run)

        # --- 결과 ---
        grp_res = QGroupBox("Result")
        res_layout = QVBoxLayout(grp_res)

        self.tree_result = QTreeWidget()
        self.tree_result.setHeaderLabels(["HIK Slot", "Source", "Target", "Status", "Detail"])
        self.tree_result.setRootIsDecorated(False)
        self.tree_result.setAlternatingRowColors(True)
        self.tree_result.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_result.itemSelectionChanged.connect(self.on_result_selection_changed)
        header = self.tree_result.header()
        header.setStretchLastSection(True)
        for col, width in ((0, 130), (1, 130), (2, 130), (3, 60)):
            self.tree_result.setColumnWidth(col, width)
        res_layout.addWidget(self.tree_result)

        hint = QLabel("Selecting a row selects its target node in the scene.")
        hint.setAlignment(Qt.AlignRight)
        res_layout.addWidget(hint)

        layout.addWidget(grp_res, 1)

        self._sync_position_controls()

        return page

    def _sync_position_controls(self):
        """Name only 모드에서는 위치 관련 입력이 아무 영향도 주지 않으므로 비활성화한다."""
        uses_position = self.match_mode() != MODE_NAME
        for w in (self.lbl_axis, self.cmb_axis, self.lbl_tolerance, self.spn_tolerance):
            w.setEnabled(uses_position)

    # --------------------------------------------------
    # 입력 값
    # --------------------------------------------------

    def match_mode(self):
        return MATCH_MODES[self.cmb_mode.currentIndex()][1]

    def selected_hik_node(self):
        items = self.list_hik.selectedItems()
        return items[0].text() if items else None

    # --------------------------------------------------
    # Slots
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def on_get_hik_nodes(self):
        nodes = HIKManager.get_hik_nodes()
        self.list_hik.clear()
        if not nodes:
            self.log("[Warning] No HIKCharacterNode found in the scene.")
            return
        self.list_hik.addItems(nodes)
        self.list_hik.setCurrentRow(0)
        self.log("Found {0} HIK node(s).".format(len(nodes)))

    def on_assign_joints(self):
        joints = self.tsl_joints.get_all_items()
        hik_node = self.selected_hik_node()
        chain_label = self.cmb_chain.currentText()

        done, msg = HIKManager.assign_joints(joints, hik_node, chain_label)
        self.log(msg)

    # -------------------------------------------------- Mirror

    def on_mirror_joints(self, dry_run):
        hik_node = self.selected_hik_node()

        records, msg = HIKManager.mirror_joints(
            hik_node,
            direction=self.cmb_direction.currentText(),
            scope=self.cmb_scope.currentText(),
            chain_label=self.cmb_chain.currentText(),
            mode=self.match_mode(),
            axis=self.cmb_axis.currentText(),
            tolerance=self.spn_tolerance.value(),
            overwrite=self.chk_overwrite.isChecked(),
            dry_run=dry_run,
        )

        self._fill_result([
            (r["slot_name"], r["src"], r["dst"], r["status"], r["reason"], r["dst"])
            for r in records
        ])
        self.log(msg)

    def on_mirror_controllers(self, dry_run):
        hik_node = self.selected_hik_node()

        scope_ids = HIKManager.scope_slots(self.cmb_scope.currentText(),
                                           self.cmb_chain.currentText())

        records, msg = CustomRigManager.mirror_mappings(
            hik_node,
            direction=self.cmb_direction.currentText(),
            scope_slot_ids=scope_ids,
            mode=self.match_mode(),
            axis=self.cmb_axis.currentText(),
            tolerance=self.spn_tolerance.value(),
            overwrite=self.chk_overwrite.isChecked(),
            copy_offset=self.chk_copy_offset.isChecked(),
            dry_run=dry_run,
        )

        self._fill_result([
            ("{0} ({1})".format(r["body"], CustomRigManager.TYPE_LABEL.get(r["type"], r["type"])),
             r["src"], r["dst"], r["status"], r["reason"], r["dst"])
            for r in records
        ])
        self.log(msg)

    def _fill_result(self, rows):
        """rows = [(slot, src, dst, status, detail, node_to_select), ...]"""
        self.tree_result.blockSignals(True)
        self.tree_result.clear()
        for slot, src, dst, status, detail, node in rows:
            item = QTreeWidgetItem([slot or "", src or "", dst or "-", status, detail or ""])
            color = STATUS_COLORS.get(status)
            if color:
                item.setForeground(3, QBrush(color))
            item.setData(0, Qt.UserRole, node)
            self.tree_result.addTopLevelItem(item)
        self.tree_result.blockSignals(False)

    def on_result_selection_changed(self):
        """결과 행을 고르면 그 대상 노드를 씬에서 선택해 눈으로 확인할 수 있게 한다."""
        import maya.cmds as cmds

        nodes = []
        for item in self.tree_result.selectedItems():
            node = item.data(0, Qt.UserRole)
            if node and cmds.objExists(node):
                nodes.append(node)
        if nodes:
            cmds.select(nodes, replace=True)

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "HumanIK Tool v{0}\nWritten by Ji Hun Park.".format(VERSION),
        )
