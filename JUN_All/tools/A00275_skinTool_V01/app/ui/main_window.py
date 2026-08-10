# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-29
# A00275_skinTool_V01 - Qt UI
#
# 스킨 관련 범용 툴. 네 개의 탭:
#   Tab 1 "Classic"      : 레거시 JUN_PY_move_skinWeightTool_v01_04 의 원본 2버튼 UI 이식.
#                          From / To 리스트 + Engine(Kangaroo/Native) + Transfer Mode +
#                          [Joints to Joints in single mesh] / [Meshes to Meshes].
#   Tab 2 "Transfer"     : 여러 소스 메시 → 현재 선택한 하나의 메시로 웨이트 전이(Kangaroo
#                          무의존). 선택 버텍스에만/소프트 falloff 반영 (weight_transfer_manager).
#   Tab 3 "Migrate A->B" : 토폴로지가 다른 두 메시 A,B 사이 Transfer + Move 를 한 번에 처리하는
#                          통합 마이그레이션 (A00270_skinMigrate 기능 이식).
#   Tab 4 "Bind Pose"    : 조인트를 이동·회전한 현재 상태를 새 바인드 포즈로 만든다.
#                          마야에 대응 기능이 없다(자세한 근거는 core/bind_pose_manager.py).
#   Tab 5 "Move Joints"  : Edit 토글 방식. 켜면 조인트를 옮겨도 메시가 변형되지 않고,
#                          다시 끄면 그 자리에서 재바인드된다(웨이트 불변).

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00275_skinTool_V01.app.config.version import VERSION, LAST_UPDATE
from tools.A00275_skinTool_V01.app.core import SkinMigrateManager
from tools.A00275_skinTool_V01.app.core import bind_pose_manager as bp_mgr
from tools.A00275_skinTool_V01.app.core import weight_transfer_manager as wt_mgr
from tools.A00275_skinTool_V01.app.core import joint_edit_manager as je_mgr


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00275_skinTool_V01_window"

# Edit 토글이 켜졌을 때의 버튼 색 (A00290_BSTool 의 Shape Editor Edit 버튼과 같은 의미).
# 테마 qss 의 :hover / :pressed 는 pseudo-state 규칙이라 배경색만 바꾸면 마우스를 올리는
# 순간 테마 색으로 되돌아가 보인다. 그래서 그 두 상태까지 함께 덮는다.
EDIT_ON_STYLE = (
    "QPushButton { background-color: #c85a28; color: #ffffff;"
    " border: 1px solid #f09050; font-weight: bold; }"
    "QPushButton:hover { background-color: #d96a34; }"
    "QPushButton:pressed { background-color: #a8441c; }"
)
EDIT_ON_TEXT = "EDIT ON  -  move the joints, then press again"
EDIT_OFF_TEXT = "EDIT JOINTS"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 620
        self.win_height = 680
        self.win_title = f"Skin Tool v{VERSION}"

        # Bind Pose 탭이 잡아둔 대상 skinCluster 목록
        self.bp_targets = []

        # Move Joints 탭이 잡아둔 대상 skinCluster 목록
        self.je_targets = []

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

        # 공유 로그 위젯을 먼저 만든다 (탭의 TSL 위젯이 log_callback=self.log 로 참조).
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(90)
        self.te_log.setMaximumHeight(160)

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_classic_tab(), "Classic")
        self.tabs.addTab(self._build_transfer_tab(), "Transfer")
        self.tabs.addTab(self._build_migrate_tab(), "Migrate A -> B")
        self.tabs.addTab(self._build_bind_pose_tab(), "Bind Pose")
        self.je_tab_index = self.tabs.addTab(
            self._build_move_joints_tab(), "Move Joints")
        # 편집 상태는 UI 가 아니라 씬(노드)에 있다. 탭을 열 때마다 씬을 다시 읽어 맞춘다.
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)

        # 공유 로그
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------
    # Tab 1 : Classic (레거시 원본 2버튼 이식)
    # --------------------------------------------------

    def _build_classic_tab(self):

        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Classic move tool. From[i] / To[i] are paired by row order.\n"
            "Pick the engine: Kangaroo (plugin) or Native (no plugin).")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Engine (Kangaroo / Native) + Transfer Mode
        eng_grp = QGroupBox("Engine")
        eng_layout = QHBoxLayout(eng_grp)
        self.classic_eng_grp = QButtonGroup(self)
        self.rb_classic_kangaroo = QRadioButton("Kangaroo")
        self.rb_classic_native = QRadioButton("Native")
        self.rb_classic_kangaroo.setChecked(True)
        self.rb_classic_kangaroo.setToolTip(
            "Kangaroo Builder plugin (must be loaded).")
        self.rb_classic_native.setToolTip(
            "cmds.copySkinWeights + maya.api. No plugin dependency.\n"
            "Move is a 1:1 joint-column move; native setWeights undo is one step.")
        self.classic_eng_grp.addButton(self.rb_classic_kangaroo)
        self.classic_eng_grp.addButton(self.rb_classic_native)
        eng_layout.addWidget(self.rb_classic_kangaroo)
        eng_layout.addWidget(self.rb_classic_native)
        eng_layout.addStretch(1)

        eng_layout.addWidget(QLabel("Transfer Mode"))
        self.cmb_classic_mode = QComboBox()
        self.cmb_classic_mode.addItems(SkinMigrateManager.TRANSFER_MODES)
        self.cmb_classic_mode.setCurrentIndex(SkinMigrateManager.DEFAULT_TRANSFER_MODE)
        self.cmb_classic_mode.setToolTip("Used by 'Meshes to Meshes' only.")
        eng_layout.addWidget(self.cmb_classic_mode)
        layout.addWidget(eng_grp)

        # From / To 리스트 (joints 또는 meshes, 동작 버튼에 따라 의미가 달라진다)
        self.tsl_classic_from = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="From", select_label="Select From", log_callback=self.log)
        self.tsl_classic_to = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="To", select_label="Select To", log_callback=self.log)

        lists_row = QHBoxLayout()
        lists_row.addWidget(self.tsl_classic_from)
        lists_row.addWidget(self.tsl_classic_to)
        layout.addLayout(lists_row)

        # 버튼: joints to joints (단일 메시) / meshes to meshes
        self.btn_joints_to_joints = QPushButton("Joints to Joints (single mesh)")
        self.btn_joints_to_joints.setMinimumHeight(34)
        self.btn_joints_to_joints.setToolTip(
            "Move skin weights From-joint[i] -> To-joint[i] on the currently\n"
            "selected mesh. Select the bound mesh in the scene first.")
        self.btn_joints_to_joints.clicked.connect(self.on_move_joints)
        layout.addWidget(self.btn_joints_to_joints)

        self.btn_meshes_to_meshes = QPushButton("Meshes to Meshes")
        self.btn_meshes_to_meshes.setMinimumHeight(34)
        self.btn_meshes_to_meshes.setToolTip(
            "Transfer skinCluster From-mesh[i] -> To-mesh[i] using Transfer Mode.")
        self.btn_meshes_to_meshes.clicked.connect(self.on_transfer_meshes)
        layout.addWidget(self.btn_meshes_to_meshes)

        return tab

    # --------------------------------------------------
    # Tab 2 : Transfer (여러 소스 -> 선택한 하나의 메시, Kangaroo 무의존)
    # --------------------------------------------------

    def _build_transfer_tab(self):

        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Transfer skin weights from the SOURCE meshes (list below) to ALL meshes\n"
            "you currently have selected in the scene (closest point).\n"
            "Select vertices on a target to transfer only there; soft selection\n"
            "falloff is respected (Native engine).")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # 소스 메시 리스트
        self.tsl_transfer_src = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Source Meshes", select_label="Select Source Meshes",
            log_callback=self.log)
        layout.addWidget(self.tsl_transfer_src)

        # 옵션 (Engine + Mode + soft selection)
        opt_grp = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_grp)

        eng_row = QHBoxLayout()
        eng_row.addWidget(QLabel("Engine"))
        self.transfer_eng_grp = QButtonGroup(self)
        self.rb_transfer_native = QRadioButton("Native")
        self.rb_transfer_kangaroo = QRadioButton("Kangaroo")
        self.rb_transfer_native.setChecked(True)
        self.rb_transfer_native.setToolTip(
            "cmds.copySkinWeights + maya.api. No plugin.\n"
            "Supports transfer to selected vertices with soft-selection falloff.")
        self.rb_transfer_kangaroo.setToolTip(
            "Kangaroo transferSkinCluster (plugin must be loaded).\n"
            "Component/partial handling follows Kangaroo; soft falloff is Native-only.")
        self.transfer_eng_grp.addButton(self.rb_transfer_native)
        self.transfer_eng_grp.addButton(self.rb_transfer_kangaroo)
        eng_row.addWidget(self.rb_transfer_native)
        eng_row.addWidget(self.rb_transfer_kangaroo)
        eng_row.addStretch(1)

        eng_row.addWidget(QLabel("Mode"))
        cmb = QComboBox()
        cmb.addItem("Closest Point")
        cmb.setEnabled(False)
        cmb.setToolTip("Closest point (like Kangaroo's Closest Point).")
        eng_row.addWidget(cmb)
        opt_layout.addLayout(eng_row)

        self.cb_transfer_soft = QCheckBox("Respect soft selection falloff")
        self.cb_transfer_soft.setChecked(True)
        self.cb_transfer_soft.setToolTip(
            "When soft selection is on, blend the transferred weights by its falloff.\n"
            "Native engine only.")
        opt_layout.addWidget(self.cb_transfer_soft)

        # Kangaroo 를 고르면 soft falloff 옵션은 Native 전용이라 비활성.
        self.rb_transfer_kangaroo.toggled.connect(
            lambda on: self.cb_transfer_soft.setEnabled(not on))

        layout.addWidget(opt_grp)

        hint = QLabel(
            "Targets = your current scene selection (one or more meshes, or "
            "vertices on them).")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        self.btn_transfer_run = QPushButton("TRANSFER to selected mesh(es)")
        self.btn_transfer_run.setMinimumHeight(40)
        self.btn_transfer_run.clicked.connect(self.on_transfer_to_mesh)
        layout.addWidget(self.btn_transfer_run)

        layout.addStretch(1)
        return tab

    def on_transfer_to_mesh(self):
        sources = self.tsl_transfer_src.get_all_items()
        engine = "kangaroo" if self.rb_transfer_kangaroo.isChecked() else "native"
        count, msg = wt_mgr.transfer_to_mesh(
            sources, respect_soft=self.cb_transfer_soft.isChecked(), engine=engine)
        self.log(msg)

    # --------------------------------------------------
    # Tab 3 : Migrate A -> B (기존 통합 마이그레이션)
    # --------------------------------------------------

    def _build_migrate_tab(self):

        tab = QWidget()
        main_layout = QVBoxLayout(tab)

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

        return tab

    # --------------------------------------------------
    # Tab 4 : Bind Pose (현재 포즈를 새 바인드 포즈로)
    # --------------------------------------------------

    def _build_bind_pose_tab(self):

        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Make the current joint pose the new bind pose.\n"
            "Move / rotate joints first, then press Update Bind Pose.\n"
            "Maya's Go to Bind Pose will return to this state afterwards.")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ---- 대상 ----
        tgt_grp = QGroupBox("Target")
        tgt_layout = QVBoxLayout(tgt_grp)

        self.lbl_bp_target = QLabel("Nothing loaded.")
        self.lbl_bp_target.setWordWrap(True)
        tgt_layout.addWidget(self.lbl_bp_target)

        row = QHBoxLayout()
        self.btn_bp_load = QPushButton("Load Selection")
        self.btn_bp_load.setMinimumHeight(30)
        self.btn_bp_load.setToolTip(
            "Pick up skinClusters from the current selection.\n"
            "Select the bound mesh, or just its joints.")
        self.btn_bp_load.clicked.connect(lambda: self.on_bp_load())
        row.addWidget(self.btn_bp_load, 2)

        self.btn_bp_clear = QPushButton("Clear")
        self.btn_bp_clear.clicked.connect(self.on_bp_clear)
        row.addWidget(self.btn_bp_clear, 1)
        tgt_layout.addLayout(row)

        self.btn_bp_diagnose = QPushButton("Diagnose")
        self.btn_bp_diagnose.setToolTip(
            "Read-only report of the deformer chain.\n"
            "Use this when a mesh reports 'shape NOT kept' to see where it stops.")
        self.btn_bp_diagnose.clicked.connect(self.on_bp_diagnose)
        tgt_layout.addWidget(self.btn_bp_diagnose)

        layout.addWidget(tgt_grp)

        # ---- 모드 ----
        mode_grp = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_grp)

        self.bp_mode_grp = QButtonGroup(self)

        self.rb_bp_keep = QRadioButton("Keep current shape")
        self.rb_bp_keep.setChecked(True)
        self.rb_bp_keep.setToolTip(
            "The deformed shape you see right now becomes the new rest shape.\n"
            "The mesh does not visibly move. This is usually what you want.")

        self.rb_bp_snap = QRadioButton("Snap mesh to rest shape")
        self.rb_bp_snap.setToolTip(
            "Only the bind matrices are updated, so the deformation is undone and\n"
            "the mesh returns to its original shape at the new joint positions.\n"
            "Same result as having moved the joints with Move Skinned Joints Tool.")

        self.bp_mode_grp.addButton(self.rb_bp_keep)
        self.bp_mode_grp.addButton(self.rb_bp_snap)
        mode_layout.addWidget(self.rb_bp_keep)
        mode_layout.addWidget(self.rb_bp_snap)

        self.cb_bp_rebuild = QCheckBox("Rebuild bindPose node (Go to Bind Pose)")
        self.cb_bp_rebuild.setChecked(True)
        self.cb_bp_rebuild.setToolTip(
            "Recreate the dagPose node so Maya's Go to Bind Pose returns here.\n"
            "Turn off to leave the existing bindPose node untouched.")
        mode_layout.addWidget(self.cb_bp_rebuild)

        layout.addWidget(mode_grp)

        # ---- 실행 ----
        self.btn_bp_update = QPushButton("UPDATE BIND POSE")
        self.btn_bp_update.setMinimumHeight(40)
        self.btn_bp_update.setToolTip("Runs as a single undo step.")
        self.btn_bp_update.clicked.connect(self.on_bp_update)
        layout.addWidget(self.btn_bp_update)

        layout.addStretch(1)

        self._update_bp_state()

        return tab

    def _update_bp_state(self):

        on = bool(self.bp_targets)
        self.btn_bp_update.setEnabled(on)
        self.lbl_bp_target.setText(bp_mgr.describe(self.bp_targets))

    # --------------------------------------------------
    # Handlers : Bind Pose
    # --------------------------------------------------

    def on_bp_load(self):

        try:
            self.bp_targets = bp_mgr.resolve_targets()
        except Exception as e:
            self.bp_targets = []
            self.log(f"[Error] {e}")

        self._update_bp_state()

        if not self.bp_targets:
            self.log("[Warning] No skinCluster found. "
                     "Select a bound mesh or its joints.")
        else:
            self.log(f"[OK] Loaded {len(self.bp_targets)} skinCluster(s): "
                     f"{', '.join(self.bp_targets)}")

    def on_bp_diagnose(self):

        if not self.bp_targets:
            self.log("[Warning] Nothing loaded. Press 'Load Selection' first.")
            return

        for line in bp_mgr.diagnose(self.bp_targets):
            self.log(line)

    def on_bp_clear(self):
        self.bp_targets = []
        self._update_bp_state()
        self.log("Bind Pose target cleared.")

    def on_bp_update(self):

        if not self.bp_targets:
            self.log("[Warning] Nothing loaded. Press 'Load Selection' first.")
            return

        keep = self.rb_bp_keep.isChecked()

        count, messages = bp_mgr.update_bind_pose(
            self.bp_targets,
            keep_shape=keep,
            rebuild_dag_pose=self.cb_bp_rebuild.isChecked())

        for m in messages:
            self.log(m)

        self.log(f"[Done] {count} skinCluster(s) updated "
                 f"({'shape kept' if keep else 'snapped to rest'}).")

    # --------------------------------------------------
    # Tab 5 : Move Joints (Edit 토글 - 메시를 건드리지 않고 조인트 이동)
    # --------------------------------------------------

    def _build_move_joints_tab(self):

        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Move or rotate the bound joints without deforming the mesh.\n"
            "Press EDIT JOINTS, move / rotate the joints in the viewport, then press\n"
            "the button again to re-bind at the new joint positions.\n"
            "Per-vertex weights are never touched - they stay exactly the same.")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ---- 대상 ----
        tgt_grp = QGroupBox("Target")
        tgt_layout = QVBoxLayout(tgt_grp)

        self.lbl_je_target = QLabel("Nothing loaded.")
        self.lbl_je_target.setWordWrap(True)
        tgt_layout.addWidget(self.lbl_je_target)

        row = QHBoxLayout()
        self.btn_je_load = QPushButton("Load Selection")
        self.btn_je_load.setMinimumHeight(30)
        self.btn_je_load.setToolTip(
            "Pick up skinClusters from the current selection.\n"
            "Select the bound mesh, or just its joints.")
        self.btn_je_load.clicked.connect(self.on_je_load)
        row.addWidget(self.btn_je_load, 2)

        self.btn_je_clear = QPushButton("Clear")
        self.btn_je_clear.clicked.connect(self.on_je_clear)
        row.addWidget(self.btn_je_clear, 1)
        tgt_layout.addLayout(row)

        self.btn_je_select_inf = QPushButton("Select Influences")
        self.btn_je_select_inf.setToolTip(
            "Select every influence joint of the loaded skinClusters,\n"
            "so you can grab them in the viewport right away.")
        self.btn_je_select_inf.clicked.connect(self.on_je_select_influences)
        tgt_layout.addWidget(self.btn_je_select_inf)

        layout.addWidget(tgt_grp)

        # ---- 옵션 ----
        opt_grp = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_grp)

        self.cb_je_rebuild = QCheckBox("Rebuild bindPose node (Go to Bind Pose)")
        self.cb_je_rebuild.setChecked(True)
        self.cb_je_rebuild.setToolTip(
            "Recreate the dagPose node when you finish, so Maya's Go to Bind Pose\n"
            "returns to the new joint positions.")
        opt_layout.addWidget(self.cb_je_rebuild)

        layout.addWidget(opt_grp)

        # ---- Edit 토글 ----
        self.btn_je_edit = QPushButton(EDIT_OFF_TEXT)
        self.btn_je_edit.setCheckable(True)
        self.btn_je_edit.setMinimumHeight(44)
        self.btn_je_edit.setToolTip(
            "ON  : the mesh is held in place - moving the joints does not deform it.\n"
            "OFF : the current joint positions become the new bind state.\n"
            "Each press is a single undo step.")
        self.btn_je_edit.clicked.connect(self.on_je_edit_clicked)
        layout.addWidget(self.btn_je_edit)

        self.btn_je_cancel = QPushButton("Cancel Edit (restore joints)")
        self.btn_je_cancel.setToolTip(
            "Leave edit mode and put the joints and bind matrices back where they\n"
            "were when you pressed EDIT JOINTS.")
        self.btn_je_cancel.clicked.connect(self.on_je_cancel)
        layout.addWidget(self.btn_je_cancel)

        self.lbl_je_state = QLabel("")
        self.lbl_je_state.setAlignment(Qt.AlignCenter)
        self.lbl_je_state.setWordWrap(True)
        layout.addWidget(self.lbl_je_state)

        layout.addStretch(1)

        self._update_je_state()

        return tab

    def _update_je_state(self):
        """씬의 실제 편집 상태를 읽어 버튼/라벨을 맞춘다.

        편집 상태는 씬(노드)에 있으므로, 툴을 닫았다 열거나 다른 곳에서 바꿔도
        화면이 씬을 따라가야 한다.
        """

        editing = je_mgr.editing_of(self.je_targets)
        on = bool(editing)

        self.btn_je_edit.setChecked(on)
        self.btn_je_edit.setText(EDIT_ON_TEXT if on else EDIT_OFF_TEXT)
        self.btn_je_edit.setStyleSheet(EDIT_ON_STYLE if on else "")
        self.btn_je_edit.setEnabled(bool(self.je_targets))

        self.btn_je_cancel.setEnabled(on)
        # 편집 중에 대상을 바꾸면 임시 노드가 씬에 남는다. 끝낼 때까지 잠근다.
        self.btn_je_load.setEnabled(not on)
        self.btn_je_clear.setEnabled(not on)

        self.lbl_je_target.setText(je_mgr.describe(self.je_targets))

        if on:
            self.lbl_je_state.setText(
                "Edit mode is ON - move / rotate the joints, then press the button "
                "again to re-bind.")
        elif self.je_targets:
            self.lbl_je_state.setText("Ready.")
        else:
            self.lbl_je_state.setText(
                "Select a bound mesh (or its joints) and press Load Selection.")

    def _adopt_scene_edits(self):
        """툴 밖(다른 세션/재실행)에서 시작된 편집을 되찾는다."""

        if self.je_targets:
            return

        editing = je_mgr.find_editing_in_scene()
        if editing:
            self.je_targets = editing
            self.log(f"[Info] Found {len(editing)} skinCluster(s) still in joint edit "
                     f"mode: {', '.join(editing)}")

    def _on_tab_changed(self, index):
        # Move Joints 탭이 보일 때만 씬 상태를 다시 읽는다.
        if index == self.je_tab_index:
            self._adopt_scene_edits()
            self._update_je_state()

    # --------------------------------------------------
    # Handlers : Move Joints
    # --------------------------------------------------

    def on_je_load(self):

        try:
            self.je_targets = je_mgr.resolve_targets()
        except Exception as e:
            self.je_targets = []
            self.log(f"[Error] {e}")

        self._update_je_state()

        if not self.je_targets:
            self.log("[Warning] No skinCluster found. "
                     "Select a bound mesh or its joints.")
        else:
            self.log(f"[OK] Loaded {len(self.je_targets)} skinCluster(s): "
                     f"{', '.join(self.je_targets)}")

    def on_je_clear(self):
        self.je_targets = []
        self._update_je_state()
        self.log("Move Joints target cleared.")

    def on_je_select_influences(self):

        if not self.je_targets:
            self.log("[Warning] Nothing loaded. Press 'Load Selection' first.")
            return

        influences = je_mgr.influences_of(self.je_targets)
        if not influences:
            self.log("[Warning] No influence found on the loaded skinCluster(s).")
            return

        try:
            cmds.select(influences, replace=True)
        except Exception as e:
            self.log(f"[Error] {e}")
            return

        self.log(f"[OK] Selected {len(influences)} influence(s).")

    def on_je_edit_clicked(self):

        if not self.je_targets:
            self.log("[Warning] Nothing loaded. Press 'Load Selection' first.")
            self._update_je_state()
            return

        # 버튼의 체크 상태가 아니라 **씬의 실제 상태**로 방향을 정한다.
        if je_mgr.editing_of(self.je_targets):
            count, messages = je_mgr.end_edit(
                self.je_targets, rebuild_dag_pose=self.cb_je_rebuild.isChecked())
            done = f"[Done] {count} skinCluster(s) re-bound at the new joint positions."
        else:
            count, messages = je_mgr.begin_edit(self.je_targets)
            done = (f"[Done] {count} skinCluster(s) held - move the joints now, "
                    f"then press the button again.")

        for m in messages:
            self.log(m)
        self.log(done)

        self._update_je_state()

    def on_je_cancel(self):

        if not je_mgr.editing_of(self.je_targets):
            self.log("[Warning] Not in edit mode.")
            self._update_je_state()
            return

        count, messages = je_mgr.cancel_edit(self.je_targets)
        for m in messages:
            self.log(m)
        self.log(f"[Done] {count} skinCluster(s) restored.")

        self._update_je_state()

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
    # Handlers : Classic
    # --------------------------------------------------

    def _classic_engine(self):
        return "kangaroo" if self.rb_classic_kangaroo.isChecked() else "native"

    def on_move_joints(self):
        joints_from = self.tsl_classic_from.get_all_items()
        joints_to = self.tsl_classic_to.get_all_items()
        count, msg = SkinMigrateManager.move_joints_in_mesh(
            joints_from, joints_to, engine=self._classic_engine())
        self.log(msg)

    def on_transfer_meshes(self):
        meshes_from = self.tsl_classic_from.get_all_items()
        meshes_to = self.tsl_classic_to.get_all_items()
        count, msg = SkinMigrateManager.transfer_meshes(
            meshes_from, meshes_to,
            transfer_mode=self.cmb_classic_mode.currentIndex(),
            engine=self._classic_engine())
        self.log(msg)

    # --------------------------------------------------
    # Handlers : Migrate A -> B
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
            f"Skin Tool v{VERSION}\n\n"
            "Classic : joint/mesh weight move (Kangaroo or Native engine).\n"
            "Transfer : many source meshes -> selected mesh/vertices (no plugin).\n"
            "Migrate A->B : cross-topology transfer + bone remap.\n"
            "Bind Pose : make the current joint pose the new bind pose.\n"
            "Move Joints : Edit toggle - move joints without deforming the mesh,\n"
            "              then re-bind at the new positions (weights unchanged).\n\n"
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )
