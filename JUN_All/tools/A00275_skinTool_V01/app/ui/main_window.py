# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
# A00275_skinTool_V01 - Qt UI
#
# 스킨 관련 범용 툴. **상위 탭 = 카테고리, 하위 탭 = 기능** 으로 통일돼 있다(v01.15~).
# 분류는 아래 CATEGORIES 표 하나가 정한다 — 탭을 더할 때 그 표에만 줄을 넣는다.
#
#   Weights : 이미 있는 웨이트를 다른 곳으로 옮긴다
#     - "Classic"        : 레거시 JUN_PY_move_skinWeightTool_v01_04 의 원본 2버튼 UI 이식.
#                          From / To 리스트 + Engine(Kangaroo/Native) + Transfer Mode +
#                          [Joints to Joints in single mesh] / [Meshes to Meshes].
#     - "Transfer"       : 여러 소스 메시 → 현재 선택한 하나의 메시로 웨이트 전이(Kangaroo
#                          무의존). 선택 버텍스에만/소프트 falloff 반영 (weight_transfer_manager).
#     - "Migrate A -> B" : 토폴로지가 다른 두 메시 A,B 사이 Transfer + Move 를 한 번에 처리하는
#                          통합 마이그레이션 (A00270_skinMigrate 기능 이식).
#
#   Bind : 바인드를 새로 만들거나 바인드 상태를 갱신한다
#     - "Bind Pose"      : 조인트를 이동·회전한 현재 상태를 새 바인드 포즈로 만든다.
#                          마야에 대응 기능이 없다(자세한 근거는 core/bind_pose_manager.py).
#     - "Expand Bind"    : 저장한 버텍스 집합을 저장한 조인트들에 바인드. 조인트 사이가
#                          엣지 길이(측지 거리)에 비례해 고르게 분배된다
#                          (Kangaroo ClosestExpand 대체 — core/expand_bind_manager.py).
#
#   Edit : 웨이트를 그대로 둔 채 리그를 고친다 (둘 다 Edit 토글, 웨이트 불변)
#     - "Move Joints"    : 켜면 조인트를 옮겨도 메시가 변형되지 않고, 다시 끄면 그 자리에서
#                          재바인드된다 (core/joint_edit_manager.py).
#     - "Edit Mesh"      : 켜면 rest 셰이프가 보이고 버텍스/엣지/페이스도 메시 자체도 자유롭게
#                          옮길 수 있으며, 끄면 그 형상이 새 rest 가 된다
#                          (core/mesh_edit_manager.py).

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00275_skinTool_V01.app.config.version import VERSION, LAST_UPDATE
from tools.A00275_skinTool_V01.app.core import SkinMigrateManager
from tools.A00275_skinTool_V01.app.core import bind_pose_manager as bp_mgr
from tools.A00275_skinTool_V01.app.core import weight_transfer_manager as wt_mgr
from tools.A00275_skinTool_V01.app.core import joint_edit_manager as je_mgr
from tools.A00275_skinTool_V01.app.core import mesh_edit_manager as me_mgr
from tools.A00275_skinTool_V01.app.core import expand_bind_manager as eb_mgr
from tools.A00275_skinTool_V01.app.core import falloff
from tools.A00275_skinTool_V01.app.ui.falloff_curve_widget import FalloffCurveWidget


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

MESH_EDIT_ON_TEXT = "EDIT ON  -  edit the mesh, then press again"
MESH_EDIT_OFF_TEXT = "EDIT MESH"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 620
        # 하위 탭 바가 한 줄 더 생긴 만큼(v01.15) 높였다. 페이지가 이보다 길면
        # 잘리지 않고 스크롤된다(_scrolled) — 가장 긴 Expand Bind 가 약 850px 다.
        self.win_height = 710
        self.win_title = f"Skin Tool v{VERSION}"

        # Bind Pose 탭이 잡아둔 대상 skinCluster 목록
        self.bp_targets = []

        # Move Joints 탭이 잡아둔 대상 skinCluster 목록
        self.je_targets = []

        # Edit Mesh 탭이 잡아둔 대상 메시 셰이프 목록
        self.me_targets = []

        # Expand Bind 탭이 저장해 둔 버텍스 집합 (메시 롱네임, 버텍스 id 리스트).
        # 리스트 위젯으로 펼치지 않는다 — 수천 개가 예사라 UI 가 바로 느려진다.
        # 대신 요약 라벨 + Select 버튼으로 확인한다.
        self.eb_mesh = None
        self.eb_vertices = []
        # 조인트가 앉아 있는 엣지 루프(선택 입력). 순서대로 정렬된 id + 닫힘 여부.
        self.eb_loop = []
        self.eb_loop_closed = False

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

        # 탭 : 카테고리 3개 (Weights / Bind / Edit) → 각 카테고리 안에 기능 하위 탭
        self.tabs = QTabWidget()

        for label, tip, pages, attr in self.CATEGORIES:
            index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
            self.tabs.setTabToolTip(index, tip)
            if attr == "edit_tabs":
                # 씬 상태를 다시 읽어야 하는 카테고리. 인덱스가 아니라 **위젯**을 기억한다
                # (인덱스는 탭이 늘고 줄면 의미가 변한다 — 아래 _on_tab_changed 주석 참고).
                self.edit_page = self.tabs.widget(index)

        # 편집 상태는 UI 가 아니라 씬(노드)에 있다. 상위/하위 어느 쪽을 눌러도 다시 읽는다.
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.edit_tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs)

        # 공유 로그
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # ==================================================================
    # 탭 분류 (v01.15~) — **상위 탭 = 카테고리 / 하위 탭 = 기능** 하나로 통일.
    #
    # 기준은 "무엇을 바꾸는가"(결과물)다. 대상(조인트/메시)으로 나누지 않는다 —
    # 그러면 Expand Bind 가 전이 기능들과 한 칸에 섞이고 배분이 4/2/1 로 기운다.
    #
    # 하위 페이지가 하나뿐인 카테고리가 생겨도 하위 탭 바를 그대로 둔다. 그래야 기능
    # 이름이 화면에 남고, 기능이 늘어도 구조가 그대로다.
    #
    # 기존 _build_*_tab() 은 이름도 내용도 바뀌지 않았다. 이 표는 그것들을 **묶기만** 한다.
    # ==================================================================

    # (하위 탭 라벨, 툴팁 = 전체 이름/설명, 빌더 메서드 이름)
    WEIGHTS_PAGES = (
        ("Classic", "Classic - the legacy two-button transfer UI "
         "(joints to joints in one mesh / meshes to meshes)", "_build_classic_tab"),
        ("Transfer", "Transfer - weights from several source meshes onto the "
         "selected mesh (selected vertices and soft-selection falloff supported)",
         "_build_transfer_tab"),
        ("Migrate A -> B", "Migrate A -> B - transfer + bone move in one step "
         "between two meshes with different topology", "_build_migrate_tab"),
    )

    BIND_PAGES = (
        ("Bind Pose", "Bind Pose - make the current joint pose the new bind pose",
         "_build_bind_pose_tab"),
        ("Expand Bind", "Expand Bind - bind a stored vertex set to stored joints, "
         "spreading the weights evenly by edge length "
         "(replaces Kangaroo's ClosestExpand)", "_build_expand_bind_tab"),
    )

    EDIT_PAGES = (
        ("Move Joints", "Move Joints - move the joints without deforming the mesh, "
         "then re-bind where they are", "_build_move_joints_tab"),
        ("Edit Mesh", "Edit Mesh - edit the shape or the position of a bound mesh "
         "without changing a single skin weight", "_build_edit_mesh_tab"),
    )

    # Edit 카테고리 하위 탭의 인덱스 (EDIT_PAGES 의 순서와 같아야 한다).
    # _on_tab_changed 가 어느 편집 탭이 보이는지 가리는 데 쓴다.
    JE_SUB_INDEX = 0        # Move Joints
    ME_SUB_INDEX = 1        # Edit Mesh

    # (상위 탭 라벨, 툴팁, 하위 페이지 표, 하위 QTabWidget 을 담을 속성 이름)
    CATEGORIES = (
        ("Weights", "Move existing skin weights somewhere else.",
         WEIGHTS_PAGES, "weights_tabs"),
        ("Bind", "Create a bind, or update what the current bind pose is.",
         BIND_PAGES, "bind_tabs"),
        ("Edit", "Change the joints or the mesh while every weight value stays "
         "the same.", EDIT_PAGES, "edit_tabs"),
    )

    def _build_category_tab(self, pages, attr):
        """카테고리 상위 탭 하나 — 기능들을 하위 탭으로 담는다."""

        tabs = self._build_sub_tabs(pages)
        setattr(self, attr, tabs)

        return tabs

    def _build_sub_tabs(self, pages):
        """(라벨, 툴팁, 빌더 메서드 이름) 목록을 중첩 탭 위젯으로 만든다.

        A00145_RigConnect 의 Constrain / Connect 탭과 같은 골격이다.
        """

        tabs = QTabWidget()
        # 폭이 모자라면 라벨을 자른다(스크롤 화살표만 뜨는 것보다 읽기 쉽다).
        tabs.tabBar().setElideMode(Qt.ElideRight)

        for label, tip, builder in pages:
            index = tabs.addTab(self._scrolled(getattr(self, builder)()), label)
            tabs.setTabToolTip(index, tip)

        return tabs

    def _scrolled(self, widget):
        """페이지를 스크롤 영역에 담아 돌려준다 (창이 작아도 위젯이 겹치지 않도록).

        스크롤은 **하위 페이지에만** 씌운다. 상위 카테고리 페이지에도 씌우면 스크롤바가
        두 겹으로 보인다. (이 툴은 A00110 처럼 창을 콘텐츠에 맞춰 자동으로 늘리지 않으므로
        fit page 가 아니라 스크롤이 맞다.)
        """

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        return scroll

    # --------------------------------------------------
    # Weights > Classic (레거시 원본 2버튼 이식)
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
    # Weights > Transfer (여러 소스 -> 선택한 하나의 메시, Kangaroo 무의존)
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
    # Weights > Migrate A -> B (기존 통합 마이그레이션)
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
    # Bind > Bind Pose (현재 포즈를 새 바인드 포즈로)
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
    # Edit > Move Joints (Edit 토글 - 메시를 건드리지 않고 조인트 이동)
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

    def _on_tab_changed(self, *_):
        """편집 상태는 씬에 있다. 편집 탭이 보일 때 다시 읽어 화면을 맞춘다.

        상위(`tabs`)와 하위(`edit_tabs`) 두 QTabWidget 이 같은 슬롯에 연결돼 있으므로
        **넘어온 인덱스를 쓰지 않는다** — 어느 위젯이 보낸 신호인지에 따라 뜻이 다르다.
        상위는 위젯 동일성으로, 하위는 EDIT_PAGES 순서와 묶인 상수로 가린다.

        (중첩 전에는 상위 탭 인덱스 하나로 갈랐는데, 그대로 두면 그 인덱스가 카테고리
        인덱스가 되어 **에러 없이** 편집 탭의 씬 재조회가 죽는다. 그러면 툴을 껐다 켰을 때
        편집 중이던 대상을 못 되찾는다 — 두 편집 탭의 핵심 약속이 조용히 깨지는 자리다.)
        """

        if self.tabs.currentWidget() is not self.edit_page:
            return

        index = self.edit_tabs.currentIndex()

        if index == self.JE_SUB_INDEX:
            self._adopt_scene_edits()
            self._update_je_state()
        elif index == self.ME_SUB_INDEX:
            self._adopt_scene_mesh_edits()
            self._update_me_state()

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

    # --------------------------------------------------
    # Edit > Edit Mesh (Edit 토글 - 웨이트를 건드리지 않고 메시 수정)
    # --------------------------------------------------

    def _build_edit_mesh_tab(self):

        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Edit a bound mesh without changing a single skin weight.\n"
            "Press EDIT MESH, move vertices / edges / faces or the mesh itself, then\n"
            "press the button again to make that the new rest shape.\n"
            "While editing, the mesh shows its rest shape and its transform is unlocked.")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ---- 대상 ----
        tgt_grp = QGroupBox("Target")
        tgt_layout = QVBoxLayout(tgt_grp)

        self.lbl_me_target = QLabel("Nothing loaded.")
        self.lbl_me_target.setWordWrap(True)
        tgt_layout.addWidget(self.lbl_me_target)

        row = QHBoxLayout()
        self.btn_me_load = QPushButton("Load Selection")
        self.btn_me_load.setMinimumHeight(30)
        self.btn_me_load.setToolTip(
            "Pick up the bound mesh from the current selection.\n"
            "Select the mesh you want to edit (a mesh without a skinCluster is "
            "ignored).")
        self.btn_me_load.clicked.connect(self.on_me_load)
        row.addWidget(self.btn_me_load, 2)

        self.btn_me_clear = QPushButton("Clear")
        self.btn_me_clear.clicked.connect(self.on_me_clear)
        row.addWidget(self.btn_me_clear, 1)
        tgt_layout.addLayout(row)

        self.btn_me_select = QPushButton("Select Mesh")
        self.btn_me_select.setToolTip(
            "Select the loaded mesh in the viewport so you can start editing it "
            "right away.")
        self.btn_me_select.clicked.connect(self.on_me_select)
        tgt_layout.addWidget(self.btn_me_select)

        layout.addWidget(tgt_grp)

        # ---- Edit 토글 ----
        self.btn_me_edit = QPushButton(MESH_EDIT_OFF_TEXT)
        self.btn_me_edit.setCheckable(True)
        self.btn_me_edit.setMinimumHeight(44)
        self.btn_me_edit.setToolTip(
            "ON  : the skin is held at envelope 0 so the mesh shows its rest shape,\n"
            "      and the transform is unlocked - edit anything you like.\n"
            "OFF : the mesh you see becomes the new rest shape. Weights are never\n"
            "      touched, so every vertex keeps exactly the same weight values.\n"
            "Each press is a single undo step.")
        self.btn_me_edit.clicked.connect(self.on_me_edit_clicked)
        layout.addWidget(self.btn_me_edit)

        self.btn_me_cancel = QPushButton("Cancel Edit (restore mesh)")
        self.btn_me_cancel.setToolTip(
            "Leave edit mode and put the mesh back the way it was when you pressed\n"
            "EDIT MESH - vertex tweaks, transform, envelope and locks.")
        self.btn_me_cancel.clicked.connect(self.on_me_cancel)
        layout.addWidget(self.btn_me_cancel)

        self.lbl_me_state = QLabel("")
        self.lbl_me_state.setAlignment(Qt.AlignCenter)
        self.lbl_me_state.setWordWrap(True)
        layout.addWidget(self.lbl_me_state)

        layout.addStretch(1)

        self._update_me_state()

        return tab

    def _update_me_state(self):
        """씬의 실제 편집 상태를 읽어 버튼/라벨을 맞춘다 (Move Joints 와 같은 규칙)."""

        editing = me_mgr.editing_of(self.me_targets)
        on = bool(editing)

        self.btn_me_edit.setChecked(on)
        self.btn_me_edit.setText(MESH_EDIT_ON_TEXT if on else MESH_EDIT_OFF_TEXT)
        self.btn_me_edit.setStyleSheet(EDIT_ON_STYLE if on else "")
        self.btn_me_edit.setEnabled(bool(self.me_targets))

        self.btn_me_cancel.setEnabled(on)
        self.btn_me_select.setEnabled(bool(self.me_targets))
        # 편집 중에 대상을 바꾸면 envelope 를 내려놓은 메시가 씬에 남는다. 끝낼 때까지 잠근다.
        self.btn_me_load.setEnabled(not on)
        self.btn_me_clear.setEnabled(not on)

        self.lbl_me_target.setText(me_mgr.describe(self.me_targets))

        if on:
            self.lbl_me_state.setText(
                "Edit mode is ON - the mesh shows its rest shape. Edit it, then press "
                "the button again to keep it.")
        elif self.me_targets:
            self.lbl_me_state.setText("Ready.")
        else:
            self.lbl_me_state.setText(
                "Select a bound mesh and press Load Selection.")

    def _adopt_scene_mesh_edits(self):
        """툴 밖(다른 세션/재실행)에서 시작된 편집을 되찾는다."""

        if self.me_targets:
            return

        editing = me_mgr.find_editing_in_scene()
        if editing:
            self.me_targets = editing
            self.log(f"[Info] Found {len(editing)} mesh(es) still in mesh edit mode: "
                     f"{', '.join(s.split('|')[-1] for s in editing)}")

    # --------------------------------------------------
    # Handlers : Edit Mesh
    # --------------------------------------------------

    def on_me_load(self):

        try:
            self.me_targets = me_mgr.resolve_targets()
        except Exception as e:
            self.me_targets = []
            self.log(f"[Error] {e}")

        self._update_me_state()

        if not self.me_targets:
            self.log("[Warning] No skinned mesh found. Select a bound mesh.")
        else:
            self.log(f"[OK] Loaded {len(self.me_targets)} mesh(es): "
                     f"{', '.join(s.split('|')[-1] for s in self.me_targets)}")

    def on_me_clear(self):
        self.me_targets = []
        self._update_me_state()
        self.log("Edit Mesh target cleared.")

    def on_me_select(self):

        if not self.me_targets:
            self.log("[Warning] Nothing loaded. Press 'Load Selection' first.")
            return

        try:
            cmds.select(self.me_targets, replace=True)
        except Exception as e:
            self.log(f"[Error] {e}")
            return

        self.log(f"[OK] Selected {len(self.me_targets)} mesh(es).")

    def on_me_edit_clicked(self):

        if not self.me_targets:
            self.log("[Warning] Nothing loaded. Press 'Load Selection' first.")
            self._update_me_state()
            return

        # 버튼의 체크 상태가 아니라 **씬의 실제 상태**로 방향을 정한다.
        if me_mgr.editing_of(self.me_targets):
            count, messages = me_mgr.end_edit(self.me_targets)
            done = f"[Done] {count} mesh(es) kept as the new rest shape."
        else:
            count, messages = me_mgr.begin_edit(self.me_targets)
            done = (f"[Done] {count} mesh(es) opened for editing - edit them now, "
                    f"then press the button again.")

        for m in messages:
            self.log(m)
        self.log(done)

        self._update_me_state()

    def on_me_cancel(self):

        if not me_mgr.editing_of(self.me_targets):
            self.log("[Warning] Not in edit mode.")
            self._update_me_state()
            return

        count, messages = me_mgr.cancel_edit(self.me_targets)
        for m in messages:
            self.log(m)
        self.log(f"[Done] {count} mesh(es) restored.")

        self._update_me_state()

    # --------------------------------------------------
    # Bind > Expand Bind (Kangaroo ClosestExpand 대체)
    # --------------------------------------------------

    # 콤보 표시 이름 -> core 의 Falloff mode.
    EB_MODES = (
        ("Surface (edge length)", eb_mgr.MODE_SURFACE),
        ("Topology (edge count)", eb_mgr.MODE_TOPOLOGY),
        ("Volume (straight line)", eb_mgr.MODE_VOLUME),
    )

    def _build_expand_bind_tab(self):

        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Store the vertices to bind and the joints to bind them to, then "
            "press BIND.\nBetween two joints the weights are spread by the real "
            "edge lengths, so\nevenly spaced loops stay even (Kangaroo "
            "ClosestExpand does not).")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ---------------- 버텍스 집합 (리스트로 펼치지 않는다)
        vtx_grp = QGroupBox("Vertices to bind")
        vtx_layout = QVBoxLayout(vtx_grp)

        self.lbl_eb_verts = QLabel("Stored: none")
        self.lbl_eb_verts.setToolTip(
            "The stored vertex set is kept as ids, not as a list widget - a "
            "lip/eye region is easily thousands of vertices and a list that "
            "long makes the window crawl.")
        vtx_layout.addWidget(self.lbl_eb_verts)

        vtx_row = QHBoxLayout()
        btn_store_v = QPushButton("Store Vertices from Selection")
        btn_store_v.setToolTip(
            "Store the selected vertices (edges/faces are converted).\n"
            "Selecting a whole mesh stores all of its vertices.")
        btn_store_v.clicked.connect(self.on_eb_store_vertices)
        vtx_row.addWidget(btn_store_v)
        btn_sel_v = QPushButton("Select")
        btn_sel_v.setToolTip("Re-select the stored vertices in the scene.")
        btn_sel_v.clicked.connect(self.on_eb_select_vertices)
        vtx_row.addWidget(btn_sel_v)
        btn_clr_v = QPushButton("Clear")
        btn_clr_v.clicked.connect(self.on_eb_clear_vertices)
        vtx_row.addWidget(btn_clr_v)
        vtx_layout.addLayout(vtx_row)

        # ---------------- 조인트가 앉아 있는 엣지 루프 (선택 입력이지만 권장)
        self.lbl_eb_loop = QLabel("Edge loop: none (optional)")
        self.lbl_eb_loop.setToolTip(
            "The edge loop the joints sit on - a loop inside the stored vertex "
            "set.\n"
            "With it, the joint split is measured ALONG the loop and the "
            "distance away from\n"
            "the loop only fades the amount, so every row keeps the loop's "
            "ratio.\n"
            "Without it the ratio smears toward the nearest joint as you move "
            "off the loop.")
        vtx_layout.addWidget(self.lbl_eb_loop)

        loop_row = QHBoxLayout()
        btn_store_l = QPushButton("Store Edge Loop from Selection")
        btn_store_l.setToolTip(
            "Store the selected edge loop (pick the edges, or the vertices "
            "along it).\n"
            "It must be one unbroken loop - open or closed, no branches.")
        btn_store_l.clicked.connect(self.on_eb_store_loop)
        loop_row.addWidget(btn_store_l)
        btn_sel_l = QPushButton("Select")
        btn_sel_l.setToolTip("Re-select the stored edge loop in the scene.")
        btn_sel_l.clicked.connect(self.on_eb_select_loop)
        loop_row.addWidget(btn_sel_l)
        btn_clr_l = QPushButton("Clear")
        btn_clr_l.clicked.connect(self.on_eb_clear_loop)
        loop_row.addWidget(btn_clr_l)
        vtx_layout.addLayout(loop_row)

        layout.addWidget(vtx_grp)

        # ---------------- 조인트 집합 (개수가 적어 리스트로 보여도 가볍다)
        self.tsl_eb_joints = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints to bind to", select_label="Store Joints from Selection",
            list_min_height=90, log_callback=self.log)
        self.tsl_eb_joints.setToolTip(
            "Influences for the bind, in any order. Usually the joints sitting "
            "on the loop.")
        layout.addWidget(self.tsl_eb_joints)

        # ---------------- Falloff (ref/ref_01.png 구성을 따른다)
        fall_grp = QGroupBox("Falloff")
        fall_layout = QVBoxLayout(fall_grp)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Falloff mode"))
        self.cmb_eb_mode = QComboBox()
        for label, _mode in self.EB_MODES:
            self.cmb_eb_mode.addItem(label)
        self.cmb_eb_mode.setToolTip(
            "Surface  : distance along the mesh edges (edge lengths) - use this "
            "for loops.\n"
            "Topology : number of edge steps, ignoring how long they are.\n"
            "Volume   : straight world distance, ignoring the topology (can "
            "bleed across a gap).")
        self.cmb_eb_mode.currentIndexChanged.connect(self._on_eb_mode_changed)
        mode_row.addWidget(self.cmb_eb_mode)
        mode_row.addStretch(1)
        fall_layout.addLayout(mode_row)

        radius_row = QHBoxLayout()
        radius_row.addWidget(QLabel("Soft Select"))
        self.sb_eb_radius = QDoubleSpinBox()
        self.sb_eb_radius.setDecimals(4)
        self.sb_eb_radius.setRange(0.0001, 1000000.0)
        self.sb_eb_radius.setSingleStep(0.1)
        self.sb_eb_radius.setValue(1.0)
        self.sb_eb_radius.setKeyboardTracking(False)
        self.sb_eb_radius.setToolTip(
            "How far the bind reaches, measured from the vertex closest to each "
            "joint.\nScene units for Surface / Volume, edge steps for Topology.")
        radius_row.addWidget(self.sb_eb_radius)
        btn_fit = QPushButton("Fit to Joints")
        btn_fit.setToolTip(
            "Set the radius so each joint's falloff just reaches its nearest "
            "neighbouring joint\n(measured with the current falloff mode, along "
            "the edge loop when one is stored).")
        btn_fit.clicked.connect(self.on_eb_fit_radius)
        radius_row.addWidget(btn_fit)
        radius_row.addStretch(1)
        fall_layout.addLayout(radius_row)

        across_row = QHBoxLayout()
        across_row.addWidget(QLabel("Across width"))
        self.sb_eb_across = QDoubleSpinBox()
        self.sb_eb_across.setDecimals(4)
        self.sb_eb_across.setRange(0.0, 1000000.0)
        self.sb_eb_across.setSingleStep(0.1)
        self.sb_eb_across.setValue(0.0)
        self.sb_eb_across.setSpecialValueText("same as Soft Select")
        self.sb_eb_across.setKeyboardTracking(False)
        self.sb_eb_across.setToolTip(
            "Edge loop only: how far the bind reaches AWAY from the loop.\n"
            "The joint split never changes here - this only fades how much the "
            "stored joints take.\n"
            "0 = use the Soft Select value (which is the reach ALONG the loop).")
        across_row.addWidget(self.sb_eb_across)
        across_row.addStretch(1)
        fall_layout.addLayout(across_row)

        curve_row = QHBoxLayout()
        lbl_curve = QLabel("Falloff curve")
        lbl_curve.setAlignment(Qt.AlignTop)
        curve_row.addWidget(lbl_curve)
        self.eb_curve = FalloffCurveWidget()
        curve_row.addWidget(self.eb_curve, 1)
        fall_layout.addLayout(curve_row)

        interp_row = QHBoxLayout()
        interp_row.addWidget(QLabel("Interpolation"))
        self.cmb_eb_interp = QComboBox()
        for name in falloff.INTERPOLATIONS:
            self.cmb_eb_interp.addItem(name.capitalize())
        self.cmb_eb_interp.setCurrentIndex(
            list(falloff.INTERPOLATIONS).index(self.eb_curve.interpolation()))
        self.cmb_eb_interp.currentIndexChanged.connect(
            lambda i: self.eb_curve.set_interpolation(falloff.INTERPOLATIONS[i]))
        # 프리셋은 보간 방식까지 바꾼다. 커브가 바뀔 때마다 콤보를 맞춰 두어야
        # 화면 표기와 실제 계산이 어긋나지 않는다(어느 경로로 바뀌든).
        self.eb_curve.changed.connect(self._sync_eb_interp_combo)
        interp_row.addWidget(self.cmb_eb_interp)
        interp_row.addStretch(1)
        fall_layout.addLayout(interp_row)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Curve presets"))
        for label, _points, _interp in falloff.PRESETS:
            btn = QPushButton(label)
            btn.setToolTip("Load the '{0}' falloff curve.".format(label))
            btn.clicked.connect(
                lambda _checked=False, name=label: self._eb_apply_preset(name))
            preset_row.addWidget(btn)
        preset_row.addStretch(1)
        fall_layout.addLayout(preset_row)

        layout.addWidget(fall_grp)

        # ---------------- Blend
        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Blend"))
        self.sb_eb_blend = QDoubleSpinBox()
        self.sb_eb_blend.setDecimals(3)
        self.sb_eb_blend.setRange(0.0, 1.0)
        self.sb_eb_blend.setSingleStep(0.05)
        self.sb_eb_blend.setValue(1.0)
        self.sb_eb_blend.setKeyboardTracking(False)
        self.sb_eb_blend.setToolTip(
            "How much of a vertex the stored joints may take when that vertex "
            "is already\nbound to OTHER influences: 0.6 leaves 0.4 to them.\n"
            "A vertex with no other influence always ends up at 1.0, whatever "
            "Blend says.")
        blend_row.addWidget(self.sb_eb_blend)
        blend_row.addStretch(1)
        layout.addLayout(blend_row)

        self.btn_eb_bind = QPushButton("BIND stored vertices to stored joints")
        self.btn_eb_bind.setMinimumHeight(40)
        self.btn_eb_bind.clicked.connect(self.on_eb_bind)
        layout.addWidget(self.btn_eb_bind)

        layout.addStretch(1)
        self._on_eb_mode_changed(0)
        return tab

    # ---------------- Expand Bind : 상태/헬퍼

    def _eb_mode(self):
        return self.EB_MODES[self.cmb_eb_mode.currentIndex()][1]

    def _on_eb_mode_changed(self, _index):
        """Topology 모드는 반경 단위가 '엣지 개수' 라 스핀박스 표기를 바꾼다."""
        if self._eb_mode() == eb_mgr.MODE_TOPOLOGY:
            self.sb_eb_radius.setSuffix("  edges")
            self.sb_eb_radius.setSingleStep(1.0)
        else:
            self.sb_eb_radius.setSuffix("")
            self.sb_eb_radius.setSingleStep(0.1)

    def _eb_apply_preset(self, name):
        self.eb_curve.set_preset(name)

    def _sync_eb_interp_combo(self):
        """커브 위젯의 보간 방식을 콤보에 반영(시그널 루프는 blockSignals 로 차단)."""
        index = list(falloff.INTERPOLATIONS).index(self.eb_curve.interpolation())
        if self.cmb_eb_interp.currentIndex() == index:
            return
        self.cmb_eb_interp.blockSignals(True)
        self.cmb_eb_interp.setCurrentIndex(index)
        self.cmb_eb_interp.blockSignals(False)

    def _eb_update_label(self):
        if not self.eb_vertices:
            self.lbl_eb_verts.setText("Stored: none")
        else:
            self.lbl_eb_verts.setText("Stored: {0} vertices  ({1})".format(
                len(self.eb_vertices), self.eb_mesh.split("|")[-1]))

        if not self.eb_loop:
            self.lbl_eb_loop.setText("Edge loop: none (optional)")
        else:
            self.lbl_eb_loop.setText("Edge loop: {0} vertices, {1}".format(
                len(self.eb_loop), "closed" if self.eb_loop_closed else "open"))

    def _eb_vertex_names(self, ids=None):
        """저장된 id 를 연속 구간으로 묶어 컴포넌트 이름으로 만든다(선택이 빨라진다)."""
        names = []
        ids = sorted(self.eb_vertices if ids is None else ids)
        start = 0
        while start < len(ids):
            end = start
            while end + 1 < len(ids) and ids[end + 1] == ids[end] + 1:
                end += 1
            if end == start:
                names.append("{0}.vtx[{1}]".format(self.eb_mesh, ids[start]))
            else:
                names.append("{0}.vtx[{1}:{2}]".format(
                    self.eb_mesh, ids[start], ids[end]))
            start = end + 1
        return names

    # ---------------- Expand Bind : 핸들러

    def on_eb_store_vertices(self):
        try:
            mesh, ids = eb_mgr.parse_selected_vertices()
        except Exception as e:
            self.log("[Error] Store Vertices : {0}".format(e))
            return
        self.eb_mesh = mesh
        self.eb_vertices = ids
        self._eb_update_label()
        self.log("[OK] Stored {0} vertices on {1}.".format(
            len(ids), mesh.split("|")[-1]))

    def on_eb_select_vertices(self):
        if not self.eb_vertices:
            self.log("[Warning] No vertices stored yet.")
            return
        if not cmds.objExists(self.eb_mesh or ""):
            self.log("[Error] Stored mesh is gone. Store the vertices again.")
            return
        try:
            cmds.select(self._eb_vertex_names(), r=True)
        except Exception as e:
            self.log("[Error] Select : {0}".format(e))
            return
        self.log("[OK] Selected {0} stored vertices.".format(len(self.eb_vertices)))

    def on_eb_clear_vertices(self):
        self.eb_mesh = None
        self.eb_vertices = []
        self.eb_loop = []
        self.eb_loop_closed = False
        self._eb_update_label()
        self.log("[OK] Cleared the stored vertices (and the edge loop).")

    def on_eb_store_loop(self):
        try:
            mesh, order, closed = eb_mgr.parse_selected_loop()
        except Exception as e:
            self.log("[Error] Store Edge Loop : {0}".format(e))
            return

        if self.eb_vertices and mesh != self.eb_mesh:
            self.log("[Error] Store Edge Loop : that loop is on '{0}', but the "
                     "stored vertices are on '{1}'.".format(
                         mesh.split("|")[-1], (self.eb_mesh or "").split("|")[-1]))
            return

        outside = [v for v in order if v not in set(self.eb_vertices)]
        self.eb_mesh = mesh
        self.eb_loop = order
        self.eb_loop_closed = closed
        self._eb_update_label()
        self.log("[OK] Stored {0} edge loop of {1} vertices.".format(
            "a closed" if closed else "an open", len(order)))
        if self.eb_vertices and outside:
            self.log("[Warning] {0} loop vertices are not in the stored vertex "
                     "set - they will be bound too.".format(len(outside)))

    def on_eb_select_loop(self):
        if not self.eb_loop:
            self.log("[Warning] No edge loop stored yet.")
            return
        if not cmds.objExists(self.eb_mesh or ""):
            self.log("[Error] Stored mesh is gone. Store the loop again.")
            return
        try:
            cmds.select(self._eb_vertex_names(self.eb_loop), r=True)
        except Exception as e:
            self.log("[Error] Select : {0}".format(e))
            return
        self.log("[OK] Selected the stored edge loop ({0} vertices).".format(
            len(self.eb_loop)))

    def on_eb_clear_loop(self):
        self.eb_loop = []
        self.eb_loop_closed = False
        self._eb_update_label()
        self.log("[OK] Cleared the stored edge loop.")

    def on_eb_fit_radius(self):
        try:
            radius = eb_mgr.suggest_radius(
                self.eb_mesh, self.eb_vertices,
                self.tsl_eb_joints.get_all_items(), mode=self._eb_mode(),
                loop_ids=self.eb_loop, loop_closed=self.eb_loop_closed)
        except Exception as e:
            self.log("[Error] Fit to Joints : {0}".format(e))
            return
        self.sb_eb_radius.setValue(radius)
        self.log("[OK] Radius set to {0:.4f} (widest gap between neighbouring "
                 "joints).".format(radius))

    def on_eb_bind(self):
        joints = self.tsl_eb_joints.get_all_items()
        try:
            with undo_chunk():
                report = eb_mgr.expand_bind(
                    self.eb_mesh, self.eb_vertices, joints,
                    radius=self.sb_eb_radius.value(),
                    blend=self.sb_eb_blend.value(),
                    mode=self._eb_mode(),
                    curve_points=self.eb_curve.points(),
                    curve_interp=self.eb_curve.interpolation(),
                    loop_ids=self.eb_loop,
                    loop_closed=self.eb_loop_closed,
                    across_radius=self.sb_eb_across.value())
        except Exception as e:
            self.log("[Error] Bind : {0}".format(e))
            cmds.warning(str(e))
            return

        if report["loop_added"]:
            self.log("[Warning] {0} loop vertices were not in the stored set - "
                     "they were bound as well.".format(report["loop_added"]))
        if report["created_skin"]:
            self.log("[Warning] {0} had no skinCluster - a new one was created, "
                     "so the vertices outside the stored set carry Maya's "
                     "default bind.".format(report["mesh"].split("|")[-1]))
        if report["skipped"]:
            self.log("[Warning] {0} stored vertices were out of range and left "
                     "untouched (raise Soft Select to reach them).".format(
                         report["skipped"]))
        loop_note = ""
        if report["loop"]:
            loop_note = ", loop {0} verts / across {1:.4f}".format(
                report["loop"], report["across_radius"])
        self.log("[OK] Bound {0} vertices to {1} joints  (mode {2}, radius "
                 "{3:.4f}{4}, blend {5:.3f}, max weight {6:.3f}).".format(
                     report["affected"], len(report["joints"]), report["mode"],
                     report["radius"], loop_note, report["blend"],
                     report["max_weight"]))

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
            "              then re-bind at the new positions (weights unchanged).\n"
            "Expand Bind : bind a stored vertex set to stored joints with a\n"
            "              falloff curve; weights spread by real edge length.\n\n"
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )
