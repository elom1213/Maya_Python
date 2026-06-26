# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-26
# A00145_RigConnect - Qt UI
#
# MEL ConnectionTool V04.02 의 3탭(Constrain / Connect / List Connected)을 PySide 로
# 포팅하고, A00140 ConnectClosest 기능을 Connect Closest 탭으로 추가한다(총 4탭).
#
# 로직은 app/core 에 위임하고 이 모듈은 위젯 구성/시그널 연결/로그 출력만 담당한다.
# 모든 UI 문자열(버튼/라벨/로그)은 영어. (한국어는 주석/독스트링만)

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00145_RigConnect.app.config.version import VERSION, LAST_UPDATE
from tools.A00145_RigConnect.app.core import match_manager as mch_mgr
from tools.A00145_RigConnect.app.core import constrain_manager as con_mgr
from tools.A00145_RigConnect.app.core import matrix_constraint_manager as mtx_mgr
from tools.A00145_RigConnect.app.core import connect_manager as cnt_mgr
from tools.A00145_RigConnect.app.core import stream_manager as stm_mgr
from tools.A00145_RigConnect.app.core import skin_constraint_manager as skn_mgr
from tools.A00145_RigConnect.app.core import (
    CONSTRAINT_TYPES, connect_closest, find_closest_for_drivers)
from tools.A00145_RigConnect.app.ui.collapsible import CollapsibleBox


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00145_RigConnect_window"


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 560
        self.win_height = 860
        self.win_title = "RigConnect v{0}".format(VERSION)

        # Connect 탭 src/dst 위젯 보관용. List Connected 의 stream 방향 상태.
        self._connect_widgets = {}
        self._stream_upstream = True

        self.resize(self.win_width, self.win_height)
        # 창이 의도치 않게 너무 작게 줄어들지 않도록 최소 크기를 보장한다.
        # (리스트/로그가 쓸만한 높이를 유지하도록 콘텐츠보다 약간 낮은 바닥값)
        self.setMinimumSize(480, 560)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

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

        # 공유 로그창 (탭 빌더가 self.log 를 호출할 수 있어 탭보다 먼저 생성)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_match_tab(), "Match")
        self.tabs.addTab(self._build_constrain_tab(), "Constrain")
        self.tabs.addTab(self._build_connect_tab(), "Connect")
        self.tabs.addTab(self._build_list_connected_tab(), "List Connected")
        self.tabs.addTab(self._build_connect_closest_tab(), "Connect Closest")
        main_layout.addWidget(self.tabs)

        main_layout.addWidget(self.te_log)

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------------------
    # Tab : Match  (MEL Match Tool V05.04 이식)
    # --------------------------------------------------------------

    def _build_match_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Targets / Followers (TSL 위젯이 cmds.ls(fl=True) 로 버텍스를 개별 항목으로 펼친다)
        self.tsl_match_tgt = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select",
            list_min_height=200, log_callback=self.log)
        self.tsl_match_flw = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=200, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_match_tgt)
        list_row.addWidget(self.tsl_match_flw)
        layout.addLayout(list_row)

        # Create : 타겟 수만큼 컨트롤을 만들어 타겟 위치/방향에 즉시 매칭(+ Followers 목록 채움).
        create_box = QGroupBox("Create (at target positions)")
        create_row = QHBoxLayout(create_box)
        for label, ctl_type in (("Locators", "locator"),
                                ("Sphere", "sphere"),
                                ("Cube", "cube")):
            btn = QPushButton(label)
            btn.clicked.connect(
                lambda _checked=False, t=ctl_type: self.on_match_create(t))
            create_row.addWidget(btn)
        layout.addWidget(create_box)

        # Match / Swap
        btn_row = QHBoxLayout()
        btn_match = QPushButton("Match")
        btn_match.setMinimumHeight(32)
        btn_match.clicked.connect(self.on_match)
        btn_swap = QPushButton("Swap")
        btn_swap.clicked.connect(self.on_match_swap)
        btn_row.addWidget(btn_match)
        btn_row.addWidget(btn_swap)
        layout.addLayout(btn_row)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Tab : Constrain
    # --------------------------------------------------------------

    def _build_constrain_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 기존 Constraint 기능은 펼쳐두고(collapsed=False),
        # 새 Skin Weight to Constraint 기능은 접어둔다(collapsed=True).
        layout.addWidget(self._build_constrain_basic_box())
        layout.addWidget(self._build_skin_constraint_box())

        layout.addStretch(1)
        return tab

    def _build_constrain_basic_box(self):
        """기존 multi target -> follower constraint UI (접이식, 기본 펼침)."""
        box = CollapsibleBox("Constraint", collapsed=False)

        self.tsl_targets = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select",
            list_min_height=200, log_callback=self.log)
        self.tsl_followers = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=200, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_targets)
        list_row.addWidget(self.tsl_followers)
        box.addLayout(list_row)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # MEL checkBox 는 기본 unchecked.
        self.cb_con_maintain = QCheckBox("Maintain Offset")
        self.cb_con_maintain.setChecked(False)
        opt_layout.addWidget(self.cb_con_maintain)

        self.rb_con_group = QButtonGroup(self)
        rb_row = QHBoxLayout()
        for i, (key, label) in enumerate(con_mgr.CONSTRAIN_TYPES):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_con_group.addButton(rb, i)
            rb_row.addWidget(rb)
        opt_layout.addLayout(rb_row)

        # --- Matrix Constraint 모드 ---
        # 체크 시 *Constraint 노드 대신 multMatrix/decomposeMatrix 네트워크로 구속한다.
        self.cb_con_matrix = QCheckBox("Matrix Constraint")
        self.cb_con_matrix.setChecked(False)
        opt_layout.addWidget(self.cb_con_matrix)

        # Matrix 모드 전용 채널 토글(기본 전부 on). 일반 모드에선 비활성.
        mtx_row = QHBoxLayout()
        self.cb_mtx_t = QCheckBox("Translate")
        self.cb_mtx_r = QCheckBox("Rotate")
        self.cb_mtx_s = QCheckBox("Scale")
        for cb in (self.cb_mtx_t, self.cb_mtx_r, self.cb_mtx_s):
            cb.setChecked(True)
            mtx_row.addWidget(cb)
        opt_layout.addLayout(mtx_row)

        self.cb_con_matrix.toggled.connect(self._on_matrix_mode_toggled)
        self._on_matrix_mode_toggled(False)

        box.addWidget(opt_box)

        btn = QPushButton("Constrain")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self.on_constrain)
        box.addWidget(btn)

        return box

    def _on_matrix_mode_toggled(self, enabled):
        """Matrix Constraint 모드 토글.

        Matrix on  : 채널(T/R/S) 체크박스 활성, 컨스트레인트 타입 라디오 비활성.
        Matrix off : 반대.
        """
        for cb in (self.cb_mtx_t, self.cb_mtx_r, self.cb_mtx_s):
            cb.setEnabled(enabled)
        for rb in self.rb_con_group.buttons():
            rb.setEnabled(not enabled)

    def _build_skin_constraint_box(self):
        """Skin Weight to Constraint UI (접이식, 기본 접힘).

        선택 버텍스의 스킨 웨이트로 영향 joint 들을 그 비율의 weight 로
        follower 에 parentConstraint 한다.
        """
        box = CollapsibleBox("Skin Weight to Constraint", collapsed=True)

        # 어떤 버텍스를 선택했는지 리스트업하는 TSL + follower 리스트.
        self.tsl_skin_verts = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Vertices", select_label="Select",
            list_min_height=180, log_callback=self.log)
        self.tsl_skin_followers = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=180, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_skin_verts)
        list_row.addWidget(self.tsl_skin_followers)
        box.addLayout(list_row)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # Max Influence : 사용할 최대 joint 개수 (0 = 제한 없음).
        mi_row = QHBoxLayout()
        mi_row.addWidget(QLabel("Max Influence"))
        self.sb_skin_max_inf = QSpinBox()
        self.sb_skin_max_inf.setRange(0, 100)
        self.sb_skin_max_inf.setValue(4)
        self.sb_skin_max_inf.setToolTip("Max number of influences to use (0 = no limit)")
        mi_row.addWidget(self.sb_skin_max_inf)
        mi_row.addStretch(1)
        opt_layout.addLayout(mi_row)

        self.cb_skin_maintain = QCheckBox("Maintain Offset")
        self.cb_skin_maintain.setChecked(True)
        opt_layout.addWidget(self.cb_skin_maintain)

        # 체크 시: vertices[i] 웨이트 -> followers[i] 1:1.
        # 해제 시: 모든 버텍스 웨이트 평균 -> 모든 follower 에 동일 적용.
        self.cb_skin_per_vertex = QCheckBox(
            "Per-vertex (vertex[i] -> follower[i], 1:1)")
        self.cb_skin_per_vertex.setChecked(False)
        opt_layout.addWidget(self.cb_skin_per_vertex)

        box.addWidget(opt_box)

        btn_row = QHBoxLayout()

        btn = QPushButton("Skin Weight to Constraint")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Constrain the objects in the Followers list with the skin "
            "weights of the selected vertices.")
        btn.clicked.connect(self.on_skin_weight_to_constraint)
        btn_row.addWidget(btn)

        # Locators : follower 를 직접 만들 필요 없이, 로케이터를 자동 생성하고
        # 동일한 스킨 웨이트 constraint 를 그 로케이터에 건다.
        btn_loc = QPushButton("Locators")
        btn_loc.setMinimumHeight(32)
        btn_loc.setToolTip(
            "Auto-create locators and run Skin Weight to Constraint on them "
            "(no Followers needed).\n"
            "Per-vertex: one locator per vertex at its position.\n"
            "Average: one locator at the centroid of selected vertices.")
        btn_loc.clicked.connect(self.on_skin_weight_to_locators)
        btn_row.addWidget(btn_loc)

        box.addLayout(btn_row)

        return box

    # --------------------------------------------------------------
    # Tab : Connect
    # --------------------------------------------------------------

    def _build_connect_tab(self):
        # Source/Destination 두 섹션 + 큰 버튼들이 세로로 쌓여 창 높이를 넘기면
        # 각 TSL 의 버튼이 창 경계를 침범한다. 내용을 스크롤 영역에 담아, 공간이
        # 모자라면 위젯이 겹치는 대신 스크롤바가 생기도록 한다.
        content = QWidget()
        layout = QVBoxLayout(content)

        layout.addWidget(self._build_connect_io("src", "Source Objects"))
        layout.addWidget(self._build_connect_io("dst", "Destination Objects"))

        btn_connect = QPushButton("Connect Source to Destination")
        btn_connect.setMinimumHeight(32)
        btn_connect.clicked.connect(self.on_connect_attrs)
        layout.addWidget(btn_connect)

        btn_facial = QPushButton("Connect 52 Facial Target")
        btn_facial.clicked.connect(self.on_connect_52_facial)
        layout.addWidget(btn_facial)

        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _build_connect_io(self, role, title):
        """Connect 탭의 Source/Destination 한 섹션을 만든다 (접이식)."""
        box = CollapsibleBox(title)

        tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=120, log_callback=self.log)

        attr_list = QListWidget()
        attr_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        attr_list.setMinimumHeight(120)

        search = QLineEdit()
        search.setPlaceholderText("search attribute")

        btn_list = QPushButton("List Attributes")
        btn_search = QPushButton("Search")

        body = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(tsl)
        left.addWidget(btn_list)

        right = QVBoxLayout()
        right.addWidget(QLabel("Attributes"))
        right.addWidget(attr_list)
        search_row = QHBoxLayout()
        search_row.addWidget(search)
        search_row.addWidget(btn_search)
        right.addLayout(search_row)

        body.addLayout(left)
        body.addLayout(right)
        box.addLayout(body)

        self._connect_widgets[role] = {
            "tsl": tsl,
            "attrs": attr_list,
            "search": search,
        }

        btn_list.clicked.connect(lambda: self.on_list_attrs(role))
        btn_search.clicked.connect(lambda: self.on_search_attrs(role))
        search.returnPressed.connect(lambda: self.on_search_attrs(role))

        return box

    # --------------------------------------------------------------
    # Tab : List Connected
    # --------------------------------------------------------------

    def _build_list_connected_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        row = QHBoxLayout()

        # Objects
        self.tsl_stream_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=220, log_callback=self.log)
        row.addWidget(self.tsl_stream_objs)

        # Types
        types_box = QVBoxLayout()
        types_box.addWidget(QLabel("Types"))
        self.list_types = QListWidget()
        self.list_types.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_types.setMinimumHeight(180)
        types_box.addWidget(self.list_types)
        btn_up = QPushButton("List UpStream")
        btn_dn = QPushButton("List DownStream")
        btn_up.clicked.connect(lambda: self.on_list_stream(True))
        btn_dn.clicked.connect(lambda: self.on_list_stream(False))
        types_box.addWidget(btn_up)
        types_box.addWidget(btn_dn)
        row.addLayout(types_box)

        # Nodes
        nodes_box = QVBoxLayout()
        nodes_box.addWidget(QLabel("Nodes"))
        self.list_nodes = QListWidget()
        self.list_nodes.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_nodes.setMinimumHeight(180)
        self.list_nodes.itemSelectionChanged.connect(self.on_nodes_selection_changed)
        nodes_box.addWidget(self.list_nodes)
        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.on_search_nodes)
        nodes_box.addWidget(btn_search)
        row.addLayout(nodes_box)

        layout.addLayout(row)
        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Tab : Connect Closest  (A00140 ConnectClosest 이식)
    # --------------------------------------------------------------

    def _build_connect_closest_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        set_box = QGroupBox("Set Up")
        set_layout = QHBoxLayout(set_box)
        self.cc_driven = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Driven",
            list_min_height=200, log_callback=self.log)
        self.cc_driver = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Driver",
            list_min_height=200, log_callback=self.log)
        # 각 Driver 에 가장 가까운 오브젝트를 찾아 Driven 을 driver 순서대로 채운다.
        # 후보 풀: Driven 에 항목이 있으면 그걸, 없으면 현재 씬 선택.
        self.cc_driver.add_button("Get Closest", self.on_get_closest)
        set_layout.addWidget(self.cc_driven)
        set_layout.addWidget(self.cc_driver)
        layout.addWidget(set_box)

        opt_box = QGroupBox("Constraint Type")
        opt_layout = QVBoxLayout(opt_box)
        cb_row = QHBoxLayout()
        self.cc_checkboxes = {}
        for key, label, _method in CONSTRAINT_TYPES:
            cb = QCheckBox(label)
            self.cc_checkboxes[key] = cb
            cb_row.addWidget(cb)
        self.cc_checkboxes["parent"].setChecked(True)
        opt_layout.addLayout(cb_row)
        self.cc_maintain = QCheckBox("Maintain Offset")
        self.cc_maintain.setChecked(True)
        opt_layout.addWidget(self.cc_maintain)
        layout.addWidget(opt_box)

        btn = QPushButton("Connect")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self.on_connect_closest)
        layout.addWidget(btn)

        layout.addStretch(1)
        return tab

    # ==============================================================
    # UI helpers
    # ==============================================================

    def _selected_texts(self, list_widget):
        return [it.text() for it in list_widget.selectedItems()]

    def _all_texts(self, list_widget):
        return [list_widget.item(i).text() for i in range(list_widget.count())]

    def log(self, text):
        self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "RigConnect v{0}\n"
            "Written by Ji Hun Park\n"
            "Update date : {1}\n"
            "\n"
            "Match       : match followers to targets (pos/rot, rotateOrder safe)\n"
            "              + create locators/sphere/cube at targets + vertex normal (+Y)\n"
            "Constrain   : multi target -> follower constraints\n"
            "              + Skin Weight to Constraint (weighted parentConstraint)\n"
            "              + Locators (auto-create locators and constrain them)\n"
            "Connect     : connect attributes (3 broadcast patterns) + 52 facial\n"
            "List Conn.  : explore up/down stream nodes by type\n"
            "Connect Closest : 1:1 closest matching constraints\n"
            "              + Get Closest (fill Driven with each driver's "
            "nearest object)".format(
                VERSION, LAST_UPDATE))

    def _run(self, label, func):
        """undo chunk 로 감싸 실행하고 결과를 로그에 남긴다."""
        with undo_chunk():
            try:
                func()
                self.log("[OK] {0}".format(label))
            except Exception as e:
                self.log("[ERR] {0} : {1}".format(label, e))
                cmds.warning(str(e))

    # ==============================================================
    # Handlers : Match
    # ==============================================================

    def on_match(self):
        targets = self.tsl_match_tgt.get_all_items()
        followers = self.tsl_match_flw.get_all_items()
        if len(targets) != len(followers):
            self.log("[WARN] Match : target/follower counts differ "
                     "({0} vs {1}) - matching {2} pair(s)".format(
                         len(targets), len(followers),
                         min(len(targets), len(followers))))

        def _do():
            matched, skipped = mch_mgr.match(targets, followers)
            self.log("       {0} matched, {1} skipped".format(matched, skipped))

        self._run("Match", _do)

    def on_match_create(self, ctl_type):
        targets = self.tsl_match_tgt.get_all_items()

        def _do():
            created = mch_mgr.create_and_match(targets, ctl_type)
            # 생성한 컨트롤을 Followers 목록에 채우고 씬에서 선택.
            self.tsl_match_flw.set_items(created)
            if created:
                cmds.select(created)
            self.log("       created and matched {0} {1}(s)".format(
                len(created), ctl_type))

        self._run("Create {0}".format(ctl_type), _do)

    def on_match_swap(self):
        targets = self.tsl_match_tgt.get_all_items()
        followers = self.tsl_match_flw.get_all_items()
        self.tsl_match_tgt.set_items(followers)
        self.tsl_match_flw.set_items(targets)
        self.log("[OK] Swap : targets <-> followers")

    # ==============================================================
    # Handlers : Constrain
    # ==============================================================

    def on_constrain(self):
        targets = self.tsl_targets.get_all_items()
        followers = self.tsl_followers.get_all_items()
        maintain_offset = self.cb_con_maintain.isChecked()

        if self.cb_con_matrix.isChecked():
            translate = self.cb_mtx_t.isChecked()
            rotate = self.cb_mtx_r.isChecked()
            scale = self.cb_mtx_s.isChecked()

            def _do():
                made, errors = mtx_mgr.matrix_constraint(
                    targets, followers, maintain_offset,
                    translate, rotate, scale)
                for err in errors:
                    self.log("[WARN] {0}".format(err))
                self.log("       {0} matrix constraint(s) created".format(
                    len(made)))

            self._run("Matrix Constraint", _do)
            return

        con_type = con_mgr.CONSTRAIN_TYPES[self.rb_con_group.checkedId()][0]
        self._run("Constrain",
                  lambda: con_mgr.constrain(
                      targets, followers, con_type, maintain_offset))

    def on_skin_weight_to_constraint(self):
        vertices = self.tsl_skin_verts.get_all_items()
        followers = self.tsl_skin_followers.get_all_items()
        max_influence = self.sb_skin_max_inf.value()
        maintain_offset = self.cb_skin_maintain.isChecked()
        per_vertex = self.cb_skin_per_vertex.isChecked()

        def _do():
            made = skn_mgr.skin_weight_to_constraint(
                vertices, followers, max_influence, maintain_offset, per_vertex)
            self.log("       {0} constraint(s) created".format(len(made)))

        self._run("Skin Weight to Constraint", _do)

    def on_skin_weight_to_locators(self):
        vertices = self.tsl_skin_verts.get_all_items()
        max_influence = self.sb_skin_max_inf.value()
        maintain_offset = self.cb_skin_maintain.isChecked()
        per_vertex = self.cb_skin_per_vertex.isChecked()

        def _do():
            created, made = skn_mgr.create_locators_and_constrain(
                vertices, max_influence, maintain_offset, per_vertex)
            # 생성한 로케이터를 Followers 목록에 채우고 씬에서 선택.
            self.tsl_skin_followers.set_items(created)
            if created:
                cmds.select(created)
            self.log("       {0} locator(s) created, "
                     "{1} constraint(s) applied".format(len(created), len(made)))

        self._run("Skin Weight to Locators", _do)

    # ==============================================================
    # Handlers : Connect
    # ==============================================================

    def on_list_attrs(self, role):
        w = self._connect_widgets[role]
        objs = w["tsl"].get_all_items()
        if not objs:
            self.log("[ERR] List Attributes : object list is empty")
            return
        try:
            attrs = cnt_mgr.list_attrs(objs[0])
        except Exception as e:
            self.log("[ERR] List Attributes : {0}".format(e))
            cmds.warning(str(e))
            return
        w["attrs"].clear()
        w["attrs"].addItems(attrs)
        self.log("[OK] List Attributes : {0} ({1} attrs)".format(objs[0], len(attrs)))

    def on_search_attrs(self, role):
        w = self._connect_widgets[role]
        search = w["search"].text().strip()
        attr_widget = w["attrs"]

        all_items = self._all_texts(attr_widget)
        matches = cnt_mgr.find_matching(all_items, search) if search else []

        if matches:
            # 현재 목록에서 매칭 항목을 선택 상태로 만든다.
            attr_widget.clearSelection()
            for i in range(attr_widget.count()):
                if attr_widget.item(i).text() in matches:
                    attr_widget.item(i).setSelected(True)
            self.log("[OK] Search : {0} match(es) selected".format(len(matches)))
        else:
            # 매칭이 없으면 검색어로 다시 attr 목록을 질의해 채운다 (MEL 동작).
            objs = w["tsl"].get_all_items()
            if not objs:
                self.log("[ERR] Search : object list is empty")
                return
            try:
                attrs = cnt_mgr.list_attrs(objs[0], search)
            except Exception as e:
                self.log("[ERR] Search : {0}".format(e))
                return
            attr_widget.clear()
            attr_widget.addItems(attrs)
            self.log("[OK] Search : re-listed {0} attrs for '{1}'".format(
                len(attrs), search))

    def on_connect_attrs(self):
        src = self._connect_widgets["src"]
        dst = self._connect_widgets["dst"]
        src_objs = src["tsl"].get_all_items()
        dst_objs = dst["tsl"].get_all_items()
        src_attrs = self._selected_texts(src["attrs"])
        dst_attrs = self._selected_texts(dst["attrs"])

        def _do():
            count, mode = cnt_mgr.connect_attrs(
                src_objs, dst_objs, src_attrs, dst_attrs)
            self.log("       {0} connection(s) [{1}]".format(count, mode))

        self._run("Connect Source to Destination", _do)

    def on_connect_52_facial(self):
        src = self._connect_widgets["src"]
        dst = self._connect_widgets["dst"]
        src_objs = src["tsl"].get_all_items()
        dst_objs = dst["tsl"].get_all_items()

        def _do():
            connected, skipped = cnt_mgr.connect_52_facial(src_objs, dst_objs)
            self.log("       {0} connected, {1} skipped".format(connected, skipped))

        self._run("Connect 52 Facial Target", _do)

    # ==============================================================
    # Handlers : List Connected
    # ==============================================================

    def on_list_stream(self, upstream):
        objs = self.tsl_stream_objs.get_all_items()
        if not objs:
            self.log("[ERR] List Stream : object list is empty")
            return
        self._stream_upstream = upstream
        try:
            types = stm_mgr.list_stream_types(objs, upstream)
        except Exception as e:
            self.log("[ERR] List Stream : {0}".format(e))
            cmds.warning(str(e))
            return
        self.list_types.clear()
        self.list_types.addItems(types)
        self.list_nodes.clear()
        self.log("[OK] List {0}Stream : {1} type(s)".format(
            "Up" if upstream else "Down", len(types)))

    def on_search_nodes(self):
        objs = self.tsl_stream_objs.get_all_items()
        types = self._selected_texts(self.list_types)
        if not objs:
            self.log("[ERR] Search Nodes : object list is empty")
            return
        if not types:
            self.log("[ERR] Search Nodes : select one or more types")
            return
        try:
            nodes = stm_mgr.nodes_by_types(objs, types, self._stream_upstream)
        except Exception as e:
            self.log("[ERR] Search Nodes : {0}".format(e))
            cmds.warning(str(e))
            return
        self.list_nodes.clear()
        self.list_nodes.addItems(nodes)
        self.log("[OK] Search Nodes : {0} node(s)".format(len(nodes)))

    def on_nodes_selection_changed(self):
        sel = self._selected_texts(self.list_nodes)
        try:
            if sel:
                cmds.select(sel)
            else:
                cmds.select(clear=True)
        except Exception as e:
            cmds.warning(str(e))

    # ==============================================================
    # Handlers : Connect Closest
    # ==============================================================

    def on_get_closest(self):
        """각 Driver 의 가장 가까운 오브젝트를 찾아 Driven 을 driver 순서대로 채운다.

        후보 풀은 Driven 리스트에 항목이 있으면 그것을, 없으면 현재 씬 선택을 쓴다.
        결과(찾은 오브젝트)는 뷰포트에서도 선택해 눈으로 확인할 수 있게 한다.
        매칭 로직은 connect_closest 와 동일(greedy 1:1)이라 Connect 결과의 미리보기다.
        """
        drivers = self.cc_driver.get_all_items()
        self.log("--- Get Closest ---")

        if not drivers:
            self.log("[WARN] Driver list is empty. Add objects to the Driver list.")
            return

        candidates = self.cc_driven.get_all_items()
        source = "Driven list"
        if not candidates:
            candidates = cmds.ls(sl=True, fl=True) or []
            source = "current selection"
        if not candidates:
            self.log("[WARN] No candidates. Fill the Driven list or "
                     "select objects in the scene.")
            return
        self.log("Candidate pool: {0} ({1} object(s))".format(
            source, len(candidates)))

        pairs, errors = find_closest_for_drivers(drivers, candidates)

        for err in errors:
            self.log("[WARN] {0}".format(err))

        if not pairs:
            self.log("No closest match found.")
            return

        drivens = [driven for _driver, driven, _dist in pairs]
        self.cc_driven.set_items(drivens)

        for driver, driven, dist in pairs:
            self.log("Closest: {0} -> {1} (dist {2:.3f})".format(
                driver, driven, dist))

        # 발견 검증용: 찾은 오브젝트를 뷰포트에서 선택.
        try:
            cmds.select(drivens, replace=True)
        except Exception:
            pass

        self.log("Done. {0} closest object(s) listed in Driven.".format(
            len(pairs)))

    def on_connect_closest(self):
        drivers = self.cc_driver.get_all_items()
        drivens = self.cc_driven.get_all_items()
        keys = [key for key, cb in self.cc_checkboxes.items() if cb.isChecked()]
        maintain_offset = self.cc_maintain.isChecked()

        self.log("--- Connect Closest ---")

        results, errors = connect_closest(
            drivers, drivens, keys, maintain_offset)

        for err in errors:
            self.log("[WARN] {0}".format(err))

        for r in results:
            self.log(
                "Connected: {driver} -> {driven} "
                "(dist {dist:.3f}, {cons})".format(
                    driver=r["driver"],
                    driven=r["driven"],
                    dist=r["distance"],
                    cons=", ".join(r["constraints"]),
                )
            )

        self.log("Done. {0} connection(s) made.".format(len(results)))
