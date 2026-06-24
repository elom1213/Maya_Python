# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00270_skinMigrate - Qt UI

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00270_skinMigrate.app.config.version import VERSION, LAST_UPDATE
from tools.A00270_skinMigrate.app.core import SkinMigrateManager


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00270_skinMigrate_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 560
        self.win_height = 620
        self.win_title = f"Skin Migrate v{VERSION}"

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
        # Engine / Transfer Mode
        # -------------------------

        opt_grp = QGroupBox("Engine")
        opt_layout = QVBoxLayout(opt_grp)

        eng_row = QHBoxLayout()
        eng_row.addWidget(QLabel("Engine"))
        self.eng_grp = QButtonGroup(self)
        self.rb_eng_kangaroo = QRadioButton("Kangaroo")
        self.rb_eng_native = QRadioButton("Native")
        self.rb_eng_kangaroo.setChecked(True)
        self.rb_eng_kangaroo.setToolTip(
            "Chain Kangaroo Builder's Transfer + Move (same as the manual workflow).\n"
            "Requires the Kangaroo plugin to be loaded.")
        self.rb_eng_native.setToolTip(
            "cmds.copySkinWeights + maya.api setWeights. No plugin dependency.\n"
            "Move is a simple 1:1 joint-column move (no closest-joint / smoothing).")
        self.eng_grp.addButton(self.rb_eng_kangaroo)
        self.eng_grp.addButton(self.rb_eng_native)
        eng_row.addWidget(self.rb_eng_kangaroo)
        eng_row.addWidget(self.rb_eng_native)
        eng_row.addStretch(1)

        eng_row.addWidget(QLabel("Transfer Mode"))
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(SkinMigrateManager.TRANSFER_MODES)
        self.cmb_mode.setCurrentIndex(SkinMigrateManager.DEFAULT_TRANSFER_MODE)
        eng_row.addWidget(self.cmb_mode)
        opt_layout.addLayout(eng_row)

        main_layout.addWidget(opt_grp)

        # -------------------------
        # Source / Target Mesh
        # -------------------------

        mesh_grp = QGroupBox("Meshes")
        mesh_layout = QVBoxLayout(mesh_grp)

        self.le_mesh_a = QLineEdit()
        self.le_mesh_a.setPlaceholderText("Source Mesh A (weights come FROM here)")
        self.le_mesh_b = QLineEdit()
        self.le_mesh_b.setPlaceholderText("Target Mesh B (weights go TO here)")

        mesh_layout.addLayout(
            self._mesh_row("Source Mesh A", self.le_mesh_a))
        mesh_layout.addLayout(
            self._mesh_row("Target Mesh B", self.le_mesh_b))

        main_layout.addWidget(mesh_grp)

        # -------------------------
        # Joints A (From) / Joints B (To) — index 로 쌍을 이룬다
        # -------------------------

        self.tsl_joints_a = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints A (From)", select_label="Select From-Joints",
            log_callback=self.log)
        self.tsl_joints_b = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints B (To)", select_label="Select To-Joints",
            log_callback=self.log)

        joints_row = QHBoxLayout()
        joints_row.addWidget(self.tsl_joints_a)
        joints_row.addWidget(self.tsl_joints_b)
        main_layout.addLayout(joints_row)

        self.lbl_pair_hint = QLabel(
            "A[i] -> B[i] are paired by row order. Keep both lists in the same order.")
        self.lbl_pair_hint.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_pair_hint)

        # -------------------------
        # Options
        # -------------------------

        chk_row = QHBoxLayout()
        self.cb_remove_unused = QCheckBox("Remove unused influences")
        self.cb_remove_unused.setChecked(True)
        self.cb_remove_unused.setToolTip(
            "After the move, delete the now-zero A-joints from B so B keeps only B-joints.")

        self.cb_strict = QCheckBox("Strict joint check")
        self.cb_strict.setChecked(True)
        self.cb_strict.setToolTip(
            "Error out if a From-joint is not actually bound to Mesh A.\n"
            "Catches wrong order / typos. Turn off to warn-and-continue.")

        self.cb_select_result = QCheckBox("Select result mesh")
        self.cb_select_result.setChecked(False)

        chk_row.addWidget(self.cb_remove_unused)
        chk_row.addWidget(self.cb_strict)
        chk_row.addWidget(self.cb_select_result)
        chk_row.addStretch(1)
        main_layout.addLayout(chk_row)

        # -------------------------
        # Run
        # -------------------------

        self.btn_transfer = QPushButton("TRANSFER")
        self.btn_transfer.setMinimumHeight(40)
        self.btn_transfer.clicked.connect(self.on_transfer)
        main_layout.addWidget(self.btn_transfer)

        # -------------------------
        # Log
        # -------------------------

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(90)
        self.te_log.setMaximumHeight(160)
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    def _mesh_row(self, label, line_edit):
        """라벨 + QLineEdit + 'Set from selection' 버튼 행."""
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setMinimumWidth(100)
        row.addWidget(lbl)
        row.addWidget(line_edit)
        btn = QPushButton("<- Set")
        btn.setToolTip("Set from the first selected mesh.")
        btn.clicked.connect(lambda: self._set_mesh_from_selection(line_edit))
        row.addWidget(btn)
        return row

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def _set_mesh_from_selection(self, line_edit):
        sel = cmds.ls(sl=True, long=False) or []
        if not sel:
            self.log("[Warning] Select a mesh first.")
            return
        # 트랜스폼 우선. 메시 셰이프가 선택됐으면 트랜스폼으로 올린다.
        node = sel[0]
        if cmds.objectType(node) == "mesh":
            parents = cmds.listRelatives(node, parent=True) or []
            node = parents[0] if parents else node
        line_edit.setText(node)

    # --------------------------------------------------
    # Handlers
    # --------------------------------------------------

    def on_transfer(self):

        mesh_a = self.le_mesh_a.text().strip()
        mesh_b = self.le_mesh_b.text().strip()
        joints_a = self.tsl_joints_a.get_all_items()
        joints_b = self.tsl_joints_b.get_all_items()

        engine = "kangaroo" if self.rb_eng_kangaroo.isChecked() else "native"
        transfer_mode = self.cmb_mode.currentIndex()

        count, msg = SkinMigrateManager.migrate(
            mesh_a, mesh_b, joints_a, joints_b,
            engine=engine,
            transfer_mode=transfer_mode,
            remove_unused=self.cb_remove_unused.isChecked(),
            select_result=self.cb_select_result.isChecked(),
            strict_joints=self.cb_strict.isChecked(),
        )
        self.log(msg)

    def show_about(self, *args):
        QMessageBox.information(
            self,
            "About",
            f"Skin Migrate v{VERSION}\n"
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )
