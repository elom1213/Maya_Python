# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00110_animTool - Qt UI

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00110_animTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00110_animTool.app.core import KeyframeManager
from tools.A00110_animTool.app.core import HotkeyManager
from tools.A00110_animTool.app.core import PoseKeyManager
from tools.A00110_animTool.app.core import CopyKeyManager
from tools.A00110_animTool.app.core import MirrorKeyManager
from tools.A00110_animTool.app.core import MirrorTokenStore
from tools.A00110_animTool.app.core import BakeManager
from tools.A00110_animTool.app.core import FollowMatchManager


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00110_animTool_window"


class MainWindow(QWidget):

    def __init__(self):

        # 마야 메인 윈도우에 parent. 뷰포트 위에는 떠 있되 다른 툴 창과는 정상 Z-order
        # (밑의 창을 클릭하면 위로 올라온다). WindowStaysOnTopHint 의 대체.
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 520
        self.win_height = 600
        self.win_title  = f"Anim Key Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

        # 툴 실행 중 Shift+A 핫키 바인딩 (창 종료 시 closeEvent 에서 복원)
        self.hotkey_mgr = HotkeyManager()
        self._enable_hotkey(self.cb_hotkey.isChecked())

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)

        # parent(마야 메인 윈도우)가 있어도 임베드되지 않고 독립 창으로 유지.
        # (isWindow()==True 이므로 launch.py 의 topLevelWidgets() 정리 로직도 그대로 동작)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # -------------------------
        # 메뉴 바 (Help > About)
        # jointTool 의 cmds.menu('Help') / cmds.menuItem('About') 패턴을 Qt 로 옮김
        # -------------------------

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # -------------------------
        # 로그 (모든 탭 공유)
        # 탭 빌더가 생성 중 self.log() 를 호출할 수 있으므로 탭보다 먼저 생성한다.
        # (레이아웃 추가는 탭 아래에 한다)
        # -------------------------

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)

        # -------------------------
        # 탭: Key Edit / Pose Key
        # (참고로 든 BSTool 의 cmds.tabLayout 을 Qt QTabWidget 으로 대응)
        # -------------------------

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_key_edit_tab(), "Key Edit")
        self.tabs.addTab(self._build_pose_key_tab(), "Pose Key")
        self.tabs.addTab(self._build_copy_key_tab(), "Copy Key")
        self.tabs.addTab(self._build_mirror_key_tab(), "Mirror Key")
        self.tabs.addTab(self._build_bake_tab(), "Bake")
        self.tabs.addTab(self._build_follow_tab(), "Follow")
        main_layout.addWidget(self.tabs)

        # 로그창을 탭 아래에 배치
        main_layout.addWidget(self.te_log)

        # -------------------------
        # 저작권 (공통)
        # -------------------------

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------
    # Tab builders
    # --------------------------------------------------

    def _build_key_edit_tab(self):
        """기존 키 이동/삭제/hold 기능 탭."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Frame range / offset 입력
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)

        row = QHBoxLayout()

        row.addWidget(QLabel("Start"))
        self.le_start = QLineEdit()
        self.le_start.setValidator(validator)
        self.le_start.setPlaceholderText("4")
        row.addWidget(self.le_start)

        row.addWidget(QLabel("End"))
        self.le_end = QLineEdit()
        self.le_end.setValidator(validator)
        self.le_end.setPlaceholderText("10")
        row.addWidget(self.le_end)

        row.addWidget(QLabel("Offset"))
        self.le_offset = QLineEdit()
        self.le_offset.setValidator(QIntValidator(0, 1000000, self))
        self.le_offset.setPlaceholderText("5")
        row.addWidget(self.le_offset)

        tab_layout.addLayout(row)

        # -------------------------
        # 이동 버튼
        # -------------------------

        row = QHBoxLayout()

        self.btn_move_back = QPushButton("◀ Earlier (-)")
        self.btn_move_fwd  = QPushButton("Later (+) ▶")

        row.addWidget(self.btn_move_back)
        row.addWidget(self.btn_move_fwd)

        tab_layout.addLayout(row)

        # -------------------------
        # 삭제 버튼
        # -------------------------

        self.btn_delete = QPushButton("Delete Keys in Range")
        tab_layout.addWidget(self.btn_delete)

        # -------------------------
        # Graph Editor 구간 유지(hold)
        # -------------------------

        grp = QGroupBox("Graph Editor")
        grp_layout = QVBoxLayout(grp)

        self.btn_hold = QPushButton("Hold Selected Range")
        grp_layout.addWidget(self.btn_hold)

        self.cb_hotkey = QCheckBox("Shift+A hotkey")
        self.cb_hotkey.setChecked(True)
        grp_layout.addWidget(self.cb_hotkey)

        self.lbl_hotkey = QLabel("")
        grp_layout.addWidget(self.lbl_hotkey)

        tab_layout.addWidget(grp)

        tab_layout.addStretch(1)

        # -------------------------
        # Signal
        # -------------------------

        self.btn_move_back.clicked.connect(lambda: self.on_move(-1))
        self.btn_move_fwd.clicked.connect(lambda: self.on_move(+1))
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_hold.clicked.connect(self.on_hold)
        self.cb_hotkey.toggled.connect(self.on_toggle_hotkey)

        return tab

    def _build_pose_key_tab(self):
        """선택 오브젝트 현재 프레임에 6축 pose 키를 설정하는 탭.
        축마다 체크박스가 있고, 체크된 축만 입력값으로 키를 설정한다.
        기본 체크: rotate X, rotate Z, translate Y. (A00030 원본 3축)"""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        grp = QGroupBox("Set Pose Key (current frame)")
        grp_layout = QVBoxLayout(grp)

        # 기본 체크 축
        default_on = {"rx", "rz", "ty"}

        # attr -> (checkbox, lineedit)
        self.pose_rows = {}

        for attr, label in PoseKeyManager.AXES:

            row = QHBoxLayout()

            cb = QCheckBox()
            cb.setChecked(attr in default_on)
            row.addWidget(cb)

            lbl = QLabel(label)
            lbl.setMinimumWidth(80)
            row.addWidget(lbl)

            le = QLineEdit("0")
            le.setValidator(QDoubleValidator(-1000000.0, 1000000.0, 4, self))
            row.addWidget(le)

            grp_layout.addLayout(row)

            self.pose_rows[attr] = (cb, le)

        tab_layout.addWidget(grp)

        self.btn_set_pose = QPushButton("Set Pose Key")
        tab_layout.addWidget(self.btn_set_pose)

        tab_layout.addStretch(1)

        self.btn_set_pose.clicked.connect(self.on_set_pose)

        return tab

    def _build_copy_key_tab(self):
        """Base -> Target 으로 시간 범위 애니메이션 키를 복사하고 축별로 값을 반전하는 탭.
        레거시 JUN_PY_CopyPasteKey_V03_01 의 Copy Key Tool 을 Qt 로 포팅.
        Base/Target 리스트는 재사용 위젯 JUN_mod_tsl_qt_v01 2개로 구성한다."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Base / Target 리스트 (재사용 위젯, 가로 2분할)
        # Select / Add / Del / Up / Down / Sort / 카운트 / 씬 선택은 위젯이 내장.
        # -------------------------

        self.base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Base", select_label="Select Base", log_callback=self.log)
        self.tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.base_tsl)
        list_row.addWidget(self.tgt_tsl)
        tab_layout.addLayout(list_row)

        # -------------------------
        # Time range (start / end). 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)

        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_copy_start = QLineEdit(str(time_str))
        self.le_copy_start.setValidator(validator)
        range_row.addWidget(self.le_copy_start)

        range_row.addWidget(QLabel("End"))
        self.le_copy_end = QLineEdit(str(time_end))
        self.le_copy_end.setValidator(validator)
        range_row.addWidget(self.le_copy_end)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Paste Option (cmds.pasteKey option). 기본 "insert".
        # -------------------------

        option_row = QHBoxLayout()
        option_row.addWidget(QLabel("Paste Option"))
        self.cmb_paste_option = QComboBox()
        self.cmb_paste_option.addItems(CopyKeyManager.PASTE_OPTIONS)
        self.cmb_paste_option.setCurrentText("insert")
        option_row.addWidget(self.cmb_paste_option)
        option_row.addStretch(1)
        tab_layout.addLayout(option_row)

        # -------------------------
        # Reverse 체크박스 (Translate X/Y/Z, Rotate X/Y/Z). 기본 모두 off.
        # -------------------------

        rev_grp = QGroupBox("Reverse")
        rev_layout = QHBoxLayout(rev_grp)

        # attr key -> checkbox. CopyKeyManager.AXES 키와 일치.
        self.copy_reverse = {}

        rev_layout.addWidget(QLabel("Translate"))
        for key, label in (("tx", "X"), ("ty", "Y"), ("tz", "Z")):
            cb = QCheckBox(label)
            self.copy_reverse[key] = cb
            rev_layout.addWidget(cb)

        rev_layout.addSpacing(12)

        rev_layout.addWidget(QLabel("Rotate"))
        for key, label in (("rx", "X"), ("ry", "Y"), ("rz", "Z")):
            cb = QCheckBox(label)
            self.copy_reverse[key] = cb
            rev_layout.addWidget(cb)

        rev_layout.addStretch(1)
        tab_layout.addWidget(rev_grp)

        # -------------------------
        # Copy 버튼
        # -------------------------

        self.btn_copy_key = QPushButton("Copy Key")
        tab_layout.addWidget(self.btn_copy_key)

        tab_layout.addStretch(1)

        self.btn_copy_key.clicked.connect(self.on_copy_key)

        return tab

    def _build_mirror_key_tab(self):
        """컨트롤러 키프레임을 반대쪽 컨트롤러로 좌우 미러하는 탭.
        자동 페어링(토큰) + 수동 리스트 폴백. rotateOrder 무관 (worldMatrix 반사)."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Mode : Auto pair / Manual list
        # -------------------------

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode"))
        self.mir_mode_grp = QButtonGroup(self)
        self.rb_mir_auto = QRadioButton("Auto pair from selection")
        self.rb_mir_manual = QRadioButton("Manual list")
        self.rb_mir_auto.setChecked(True)
        self.mir_mode_grp.addButton(self.rb_mir_auto)
        self.mir_mode_grp.addButton(self.rb_mir_manual)
        mode_row.addWidget(self.rb_mir_auto)
        mode_row.addWidget(self.rb_mir_manual)
        mode_row.addStretch(1)
        tab_layout.addLayout(mode_row)

        # -------------------------
        # Base(Source) / Target 리스트 (수동 모드에서 노출). Copy Key 탭과 동일 위젯.
        # Auto 모드에서도 Resolve Pairs 결과 미리보기/수정에 쓸 수 있다.
        # -------------------------

        self.mir_base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Source", select_label="Select Source", log_callback=self.log)
        self.mir_tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)

        self.mir_list_row = QWidget()
        list_row = QHBoxLayout(self.mir_list_row)
        list_row.setContentsMargins(0, 0, 0, 0)
        list_row.addWidget(self.mir_base_tsl)
        list_row.addWidget(self.mir_tgt_tsl)
        tab_layout.addWidget(self.mir_list_row)

        self.btn_mir_resolve = QPushButton("Resolve Pairs from Selection")
        tab_layout.addWidget(self.btn_mir_resolve)

        # -------------------------
        # Mirror Axis (X / Y / Z)
        # -------------------------

        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Mirror Axis"))
        self.mir_axis_grp = QButtonGroup(self)
        self.mir_axis_btns = {}
        for ax in ("X", "Y", "Z"):
            rb = QRadioButton(ax)
            self.mir_axis_grp.addButton(rb)
            self.mir_axis_btns[ax.lower()] = rb
            axis_row.addWidget(rb)
        self.mir_axis_btns["x"].setChecked(True)
        axis_row.addSpacing(12)

        # Channels (Translate / Rotate)
        axis_row.addWidget(QLabel("Channels"))
        self.cb_mir_translate = QCheckBox("Translate")
        self.cb_mir_rotate = QCheckBox("Rotate")
        self.cb_mir_translate.setChecked(True)
        self.cb_mir_rotate.setChecked(True)
        axis_row.addWidget(self.cb_mir_translate)
        axis_row.addWidget(self.cb_mir_rotate)
        axis_row.addStretch(1)
        tab_layout.addLayout(axis_row)

        # Method: Behavior (preserve target local axes) vs world reflection (legacy)
        method_row = QHBoxLayout()
        self.cb_mir_behavior = QCheckBox("Behavior (keep target local axes)")
        self.cb_mir_behavior.setChecked(True)  # 기본값 = 새 방식(behavior)
        self.cb_mir_behavior.setToolTip(
            "On: preserve the target controller's own forward/up axes,\n"
            "like mirror-behavior joints (rest-relative mirror).\n"
            "Off: pure world reflection (legacy).")
        method_row.addWidget(self.cb_mir_behavior)
        method_row.addStretch(1)
        tab_layout.addLayout(method_row)

        # -------------------------
        # Time range + time mode. 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_mir_start = QLineEdit(str(time_str))
        self.le_mir_start.setValidator(validator)
        range_row.addWidget(self.le_mir_start)
        range_row.addWidget(QLabel("End"))
        self.le_mir_end = QLineEdit(str(time_end))
        self.le_mir_end.setValidator(validator)
        range_row.addWidget(self.le_mir_end)

        range_row.addSpacing(12)
        range_row.addWidget(QLabel("Time"))
        self.mir_time_grp = QButtonGroup(self)
        self.rb_mir_srckeys = QRadioButton("Source keys")
        self.rb_mir_bake = QRadioButton("Bake")
        self.rb_mir_srckeys.setChecked(True)
        self.mir_time_grp.addButton(self.rb_mir_srckeys)
        self.mir_time_grp.addButton(self.rb_mir_bake)
        range_row.addWidget(self.rb_mir_srckeys)
        range_row.addWidget(self.rb_mir_bake)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Tokens (접이식) : 좌/우 토큰 쌍 편집 테이블 + Save/Reload -> mirror_tokens.json
        # -------------------------

        self.grp_mir_tokens = QGroupBox("L / R Tokens (mirror_tokens.json)")
        self.grp_mir_tokens.setCheckable(True)
        self.grp_mir_tokens.setChecked(False)
        tok_layout = QVBoxLayout(self.grp_mir_tokens)

        self.tbl_mir_tokens = QTableWidget(0, 2)
        self.tbl_mir_tokens.setHorizontalHeaderLabels(["Left", "Right"])
        self.tbl_mir_tokens.horizontalHeader().setStretchLastSection(True)
        self.tbl_mir_tokens.verticalHeader().setVisible(False)
        self.tbl_mir_tokens.setMaximumHeight(140)
        tok_layout.addWidget(self.tbl_mir_tokens)

        tok_btn_row = QHBoxLayout()
        self.btn_tok_add = QPushButton("Add Row")
        self.btn_tok_del = QPushButton("Remove Row")
        self.btn_tok_save = QPushButton("Save")
        self.btn_tok_reload = QPushButton("Reload")
        for b in (self.btn_tok_add, self.btn_tok_del, self.btn_tok_save, self.btn_tok_reload):
            tok_btn_row.addWidget(b)
        tok_layout.addLayout(tok_btn_row)
        tab_layout.addWidget(self.grp_mir_tokens)

        # -------------------------
        # Mirror 실행 버튼 (구간 미러)
        # -------------------------

        self.btn_mirror = QPushButton("Mirror Selected")
        tab_layout.addWidget(self.btn_mirror)

        # -------------------------
        # Current Frame : 현재 프레임만 미러 (autoKeyframe 재현)
        #   - Start/End/Time 과 무관. 키 있는 채널만 키 갱신, 없으면 포즈만(setAttr).
        # -------------------------

        cf_grp = QGroupBox("Current Frame")
        cf_layout = QVBoxLayout(cf_grp)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Keying"))
        self.mir_cf_key_grp = QButtonGroup(self)
        self.rb_mir_cf_channel = QRadioButton("Per-channel (auto-key)")
        self.rb_mir_cf_object = QRadioButton("Per-object")
        self.rb_mir_cf_channel.setChecked(True)   # 기본 = per-channel (autoKeyframe 동일)
        self.mir_cf_key_grp.addButton(self.rb_mir_cf_channel)
        self.mir_cf_key_grp.addButton(self.rb_mir_cf_object)
        key_row.addWidget(self.rb_mir_cf_channel)
        key_row.addWidget(self.rb_mir_cf_object)
        key_row.addStretch(1)
        cf_layout.addLayout(key_row)

        self.btn_mirror_current = QPushButton("Mirror Current Frame")
        cf_layout.addWidget(self.btn_mirror_current)

        tab_layout.addWidget(cf_grp)

        tab_layout.addStretch(1)

        # -------------------------
        # 상태 초기화 : 토큰 로드, 모드에 따른 리스트 표시
        # -------------------------

        self._mir_load_tokens()
        self._mir_update_mode()

        # -------------------------
        # Signal
        # -------------------------

        self.rb_mir_auto.toggled.connect(self._mir_update_mode)
        self.cb_mir_behavior.toggled.connect(self._mir_update_method)
        self.btn_mir_resolve.clicked.connect(self.on_mir_resolve)
        self.btn_mirror.clicked.connect(self.on_mirror_key)
        self.btn_mirror_current.clicked.connect(self.on_mirror_current_frame)
        self.btn_tok_add.clicked.connect(lambda: self._mir_add_token_row("", ""))
        self.btn_tok_del.clicked.connect(self._mir_del_token_row)
        self.btn_tok_save.clicked.connect(self.on_mir_save_tokens)
        self.btn_tok_reload.clicked.connect(self._mir_load_tokens)

        self._mir_update_method()  # behavior 초기 상태를 Mirror Axis 활성/비활성에 반영

        return tab

    def _build_bake_tab(self):
        """리스트업한 컨트롤러/오브젝트를 구간 dense 키로 굽는 탭.
        A00120_FKIK 의 native bakeResults 베이크를 이식(컨스트레인트 없는 범용 bake).
        대상은 씬 선택이 아니라 Bake List 위젯의 항목이다."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Bake List (재사용 위젯). 리스트업된 항목만 베이크된다.
        # -------------------------

        self.bake_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Bake List", select_label="Select Objects", log_callback=self.log)
        tab_layout.addWidget(self.bake_tsl)

        # -------------------------
        # Range : Current timeline / Custom range
        # -------------------------

        range_mode_row = QHBoxLayout()
        range_mode_row.addWidget(QLabel("Range"))
        self.bake_range_grp = QButtonGroup(self)
        self.rb_bake_timeline = QRadioButton("Current timeline")
        self.rb_bake_custom = QRadioButton("Custom range")
        self.rb_bake_timeline.setChecked(True)   # 기본 = 현재 타임라인 구간
        self.bake_range_grp.addButton(self.rb_bake_timeline)
        self.bake_range_grp.addButton(self.rb_bake_custom)
        range_mode_row.addWidget(self.rb_bake_timeline)
        range_mode_row.addWidget(self.rb_bake_custom)
        range_mode_row.addStretch(1)
        tab_layout.addLayout(range_mode_row)

        # Custom 구간 입력 (Custom 모드에서만 활성). 기본값 = 현재 playback 범위.
        validator = QIntValidator(-1000000, 1000000, self)
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_bake_start = QLineEdit(str(time_str))
        self.le_bake_start.setValidator(validator)
        range_row.addWidget(self.le_bake_start)
        range_row.addWidget(QLabel("End"))
        self.le_bake_end = QLineEdit(str(time_end))
        self.le_bake_end.setValidator(validator)
        range_row.addWidget(self.le_bake_end)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Channels (Translate / Rotate / Scale). 기본 T·R on, S off.
        # -------------------------

        ch_row = QHBoxLayout()
        ch_row.addWidget(QLabel("Channels"))
        self.cb_bake_t = QCheckBox("Translate")
        self.cb_bake_r = QCheckBox("Rotate")
        self.cb_bake_s = QCheckBox("Scale")
        self.cb_bake_t.setChecked(True)
        self.cb_bake_r.setChecked(True)
        ch_row.addWidget(self.cb_bake_t)
        ch_row.addWidget(self.cb_bake_r)
        ch_row.addWidget(self.cb_bake_s)
        ch_row.addStretch(1)
        tab_layout.addLayout(ch_row)

        # -------------------------
        # Options : Keep constraints (기본 ON -> disableImplicitControl=False), Simulation
        # -------------------------

        self.cb_bake_keep_con = QCheckBox("Keep constraints (insert blend)")
        self.cb_bake_keep_con.setChecked(True)   # 기본 유지 -> dic=False
        tab_layout.addWidget(self.cb_bake_keep_con)

        self.cb_bake_sim = QCheckBox("Simulation")
        self.cb_bake_sim.setChecked(True)
        tab_layout.addWidget(self.cb_bake_sim)

        # -------------------------
        # Smart bake : native bakeResults -smart (Maya 2020+). 허용오차 이내 중간 키를
        # C++ 내부에서 제거해 키 수를 줄인다. 끄면 매 프레임 dense.
        # -------------------------

        self.cb_bake_smart = QCheckBox("Smart bake (reduce keys)")
        self.cb_bake_smart.setChecked(False)
        tab_layout.addWidget(self.cb_bake_smart)

        smart_row = QHBoxLayout()
        smart_row.addWidget(QLabel("Tolerance"))
        self.le_bake_smart_tol = QLineEdit("0.5")
        self.le_bake_smart_tol.setValidator(QDoubleValidator(0.0, 1000.0, 3, self))
        smart_row.addWidget(self.le_bake_smart_tol)
        smart_row.addStretch(1)
        tab_layout.addLayout(smart_row)

        # -------------------------
        # Bake 버튼
        # -------------------------

        self.btn_bake = QPushButton("Bake List")
        tab_layout.addWidget(self.btn_bake)

        tab_layout.addStretch(1)

        # 초기 활성 상태 동기화 + 시그널
        self._bake_update_range_mode()
        self._bake_update_smart_mode()
        self.rb_bake_custom.toggled.connect(self._bake_update_range_mode)
        self.cb_bake_smart.toggled.connect(self._bake_update_smart_mode)
        self.btn_bake.clicked.connect(self.on_bake)

        return tab

    def _build_follow_tab(self):
        """좌(Target) / 우(Follower) 리스트로, follower 가 같은 인덱스의 target 의 월드
        위치/회전(/스케일)과 동일해지도록 구간 키를 굽는 탭. rotateOrder 무관.
        blend(0..1) 로 원본 follower 애니메이션과 매치 결과를 섞고, 선택된 애니메이션
        레이어에 키가 들어간다."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Target / Follower 리스트 (재사용 위젯, 가로 2분할). Copy Key 탭과 동일 구성.
        # -------------------------

        self.follow_tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)
        self.follow_flw_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Follower", select_label="Select Followers", log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.follow_tgt_tsl)
        list_row.addWidget(self.follow_flw_tsl)
        tab_layout.addLayout(list_row)

        # -------------------------
        # Time range (start / end). 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_follow_start = QLineEdit(str(time_str))
        self.le_follow_start.setValidator(validator)
        range_row.addWidget(self.le_follow_start)
        range_row.addWidget(QLabel("End"))
        self.le_follow_end = QLineEdit(str(time_end))
        self.le_follow_end.setValidator(validator)
        range_row.addWidget(self.le_follow_end)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Channels (Translate / Rotate / Scale). 기본 T·R on, S off. (Bake 탭과 동일)
        # -------------------------

        ch_row = QHBoxLayout()
        ch_row.addWidget(QLabel("Channels"))
        self.cb_follow_t = QCheckBox("Translate")
        self.cb_follow_r = QCheckBox("Rotate")
        self.cb_follow_s = QCheckBox("Scale")
        self.cb_follow_t.setChecked(True)
        self.cb_follow_r.setChecked(True)
        ch_row.addWidget(self.cb_follow_t)
        ch_row.addWidget(self.cb_follow_r)
        ch_row.addWidget(self.cb_follow_s)
        ch_row.addStretch(1)
        tab_layout.addLayout(ch_row)

        # -------------------------
        # Blend (0..1). LineEdit 와 Slider(0..100) 를 동기화. 기본 1.0(완전 매치).
        # -------------------------

        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Blend (0..1)"))
        self.le_follow_blend = QLineEdit("1.0")
        self.le_follow_blend.setValidator(QDoubleValidator(0.0, 1.0, 3, self))
        self.le_follow_blend.setMaximumWidth(60)
        blend_row.addWidget(self.le_follow_blend)

        self.sld_follow_blend = QSlider(Qt.Horizontal)
        self.sld_follow_blend.setRange(0, 100)
        self.sld_follow_blend.setValue(100)
        blend_row.addWidget(self.sld_follow_blend)
        tab_layout.addLayout(blend_row)

        # -------------------------
        # Match 버튼
        # -------------------------

        self.btn_follow = QPushButton("Match Follow")
        tab_layout.addWidget(self.btn_follow)

        tab_layout.addStretch(1)

        # Slider <-> LineEdit 동기화 + 실행 시그널
        self.sld_follow_blend.valueChanged.connect(self._follow_slider_to_le)
        self.le_follow_blend.editingFinished.connect(self._follow_le_to_slider)
        self.btn_follow.clicked.connect(self.on_follow_bake)

        return tab

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def _read_range(self):
        """start, end 파싱. 실패 시 None."""
        s_txt = self.le_start.text().strip()
        e_txt = self.le_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None

        return (start, end)

    def _read_offset(self):
        """offset(양수) 파싱. 실패 시 None."""
        o_txt = self.le_offset.text().strip()

        if o_txt == "":
            self.log("[Warning] Enter Offset.")
            return None

        return abs(int(o_txt))

    # --------------------------------------------------
    # Handlers
    # --------------------------------------------------

    def on_move(self, sign):

        rng = self._read_range()
        if rng is None:
            return

        offset = self._read_offset()
        if offset is None:
            return

        start, end = rng
        offset = sign * offset   # 앞으로(-) / 뒤로(+)

        count, msg = KeyframeManager.move_keys(start, end, offset)
        self.log(msg)

    def on_delete(self):

        rng = self._read_range()
        if rng is None:
            return

        start, end = rng

        count, msg = KeyframeManager.delete_keys(start, end)
        self.log(msg)

    def on_hold(self):

        count, msg = KeyframeManager.hold_selected_keys()
        self.log(msg)

    def on_set_pose(self):

        # 체크된 축만 모은다. 체크됐는데 값이 비어 있으면 경고 후 중단.
        axis_values = {}
        for attr, (cb, le) in self.pose_rows.items():
            if not cb.isChecked():
                continue
            txt = le.text().strip()
            if txt == "":
                self.log(f"[Warning] {attr} is checked but empty.")
                return
            axis_values[attr] = float(txt)

        if not axis_values:
            self.log("[Warning] No axis checked.")
            return

        count, msg = PoseKeyManager.set_pose_keys(axis_values)
        self.log(msg)

    def on_copy_key(self):

        base = self.base_tsl.get_all_items()
        tgt = self.tgt_tsl.get_all_items()

        if not base or not tgt:
            self.log("[Warning] Fill both Base and Target lists.")
            return

        # Start / End 파싱 (Copy 탭 전용).
        s_txt = self.le_copy_start.text().strip()
        e_txt = self.le_copy_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        reverse_flags = {key: cb.isChecked() for key, cb in self.copy_reverse.items()}
        paste_option = self.cmb_paste_option.currentText()

        count, msg = CopyKeyManager.copy_keys(base, tgt, start, end, reverse_flags, paste_option)
        self.log(msg)

    # --------------------------------------------------
    # Mirror Key
    # --------------------------------------------------

    def _mir_update_mode(self, *args):
        """Auto/Manual 모드에 따라 Source/Target 리스트 표시를 토글."""
        manual = self.rb_mir_manual.isChecked()
        # Auto 모드에서도 Resolve 미리보기를 위해 리스트는 보이게 두되,
        # Manual 일 때만 직접 입력이 주가 된다. 여기서는 항상 표시(미리보기 겸용).
        self.mir_list_row.setVisible(True)
        self.btn_mir_resolve.setVisible(not manual)

    def _mir_update_method(self, *args):
        """Behavior(축 보존) 모드면 Mirror Axis 가 무의미하므로 X/Y/Z 라디오를 비활성화한다.
        (behavior 미러의 좌우 대칭은 레스트 차이에 내장돼 있어 반사축에 무관하다.)"""
        axis_enabled = not self.cb_mir_behavior.isChecked()
        for rb in self.mir_axis_btns.values():
            rb.setEnabled(axis_enabled)

    def _mir_axis(self):
        for ax, rb in self.mir_axis_btns.items():
            if rb.isChecked():
                return ax
        return "x"

    def _mir_read_range(self):
        """Mirror 탭 Start/End 파싱. 실패 시 None."""
        s_txt = self.le_mir_start.text().strip()
        e_txt = self.le_mir_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None
        start = int(s_txt)
        end = int(e_txt)
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None
        return (start, end)

    def _mir_token_pairs(self):
        """현재 토큰 테이블의 (left, right) 쌍 목록(빈 행 제외)."""
        pairs = []
        for r in range(self.tbl_mir_tokens.rowCount()):
            left_item = self.tbl_mir_tokens.item(r, 0)
            right_item = self.tbl_mir_tokens.item(r, 1)
            left = left_item.text().strip() if left_item else ""
            right = right_item.text().strip() if right_item else ""
            if left and right:
                pairs.append((left, right))
        return pairs

    def _mir_add_token_row(self, left="", right=""):
        r = self.tbl_mir_tokens.rowCount()
        self.tbl_mir_tokens.insertRow(r)
        self.tbl_mir_tokens.setItem(r, 0, QTableWidgetItem(left))
        self.tbl_mir_tokens.setItem(r, 1, QTableWidgetItem(right))

    def _mir_del_token_row(self):
        rows = sorted({idx.row() for idx in self.tbl_mir_tokens.selectedIndexes()}, reverse=True)
        if not rows:
            r = self.tbl_mir_tokens.rowCount() - 1
            if r >= 0:
                rows = [r]
        for r in rows:
            self.tbl_mir_tokens.removeRow(r)

    def _mir_load_tokens(self):
        """mirror_tokens.json -> 테이블."""
        pairs, msg = MirrorTokenStore.load()
        self.tbl_mir_tokens.setRowCount(0)
        for left, right in pairs:
            self._mir_add_token_row(left, right)
        self.log(msg)

    def on_mir_save_tokens(self):
        pairs = self._mir_token_pairs()
        if not pairs:
            self.log("[Warning] No valid token pairs to save.")
            return
        count, msg = MirrorTokenStore.save(pairs)
        self.log(msg)

    def on_mir_resolve(self):
        """현재 선택으로 자동 페어링해 Source/Target 리스트를 채운다(미리보기)."""
        sel = cmds.ls(sl=True) or []
        if not sel:
            self.log("[Warning] Select source controllers first.")
            return

        token_pairs = self._mir_token_pairs() or list(MirrorKeyManager.DEFAULT_TOKEN_PAIRS)
        pairs, unpaired, center = MirrorKeyManager.resolve_pairs(sel, token_pairs)

        self.mir_base_tsl.set_items([s for s, _ in pairs])
        self.mir_tgt_tsl.set_items([t for _, t in pairs])

        msg = f"{len(pairs)} pair(s) resolved."
        if center:
            msg += f" {len(center)} center (self-mirror)."
        if unpaired:
            msg += f" {len(unpaired)} unpaired: {', '.join(unpaired)}"
        self.log(msg)

    def _mir_resolve_pairs(self):
        """현재 모드(Auto/Manual)로 (src, tgt) 페어 리스트 반환. 실패 시 None(경고 로그).
        on_mirror_key(구간) / on_mirror_current_frame(현재 프레임) 가 공유한다.
        씬 선택과 무관하게 Source/Target 리스트의 오브젝트만 대상으로 한다."""
        base = self.mir_base_tsl.get_all_items()
        tgt = self.mir_tgt_tsl.get_all_items()

        if self.rb_mir_manual.isChecked():
            # 수동: Source/Target 리스트를 인덱스 매칭.
            if not base or not tgt:
                self.log("[Warning] Fill both Source and Target lists.")
                return None
            if len(base) != len(tgt):
                self.log(f"[Warning] Source({len(base)}) / Target({len(tgt)}) count mismatch.")
                return None
            return list(zip(base, tgt))

        # 자동: 씬 선택을 읽지 않고 Source 리스트를 기준으로 한다.
        if not base:
            self.log("[Warning] Source list is empty. Use 'Select Source' or 'Resolve Pairs'.")
            return None
        if tgt and len(tgt) == len(base):
            # 이미 페어가 채워져 있으면(Resolve 등) 그대로 사용.
            return list(zip(base, tgt))
        # Target 리스트가 비어 있으면 Source 리스트를 토큰으로 자동 페어링.
        token_pairs = self._mir_token_pairs() or list(MirrorKeyManager.DEFAULT_TOKEN_PAIRS)
        pairs, unpaired, center = MirrorKeyManager.resolve_pairs(base, token_pairs)
        if unpaired:
            self.log(f"[Warning] {len(unpaired)} unpaired (skipped): {', '.join(unpaired)}")
        if not pairs:
            self.log("[Warning] No pairs resolved.")
            return None
        return pairs

    def on_mirror_key(self):

        rng = self._mir_read_range()
        if rng is None:
            return
        start, end = rng

        do_t = self.cb_mir_translate.isChecked()
        do_r = self.cb_mir_rotate.isChecked()
        if not do_t and not do_r:
            self.log("[Warning] Enable Translate and/or Rotate.")
            return

        axis = self._mir_axis()
        time_mode = "bake" if self.rb_mir_bake.isChecked() else "source_keys"

        pairs = self._mir_resolve_pairs()
        if pairs is None:
            return

        count, msg = MirrorKeyManager.mirror_keys(
            pairs, start, end, mirror_axis=axis,
            do_translate=do_t, do_rotate=do_r, time_mode=time_mode,
            behavior=self.cb_mir_behavior.isChecked())
        self.log(msg)

    def on_mirror_current_frame(self):
        """현재 프레임의 포즈만 미러(autoKeyframe 재현). Start/End/Time 미사용."""
        do_t = self.cb_mir_translate.isChecked()
        do_r = self.cb_mir_rotate.isChecked()
        if not do_t and not do_r:
            self.log("[Warning] Enable Translate and/or Rotate.")
            return

        pairs = self._mir_resolve_pairs()
        if pairs is None:
            return

        count, msg = MirrorKeyManager.mirror_current_frame(
            pairs, mirror_axis=self._mir_axis(),
            do_translate=do_t, do_rotate=do_r,
            per_object=self.rb_mir_cf_object.isChecked(),
            behavior=self.cb_mir_behavior.isChecked(),
        )
        self.log(msg)

    # --------------------------------------------------
    # Bake
    # --------------------------------------------------

    def _bake_update_range_mode(self, *args):
        """Range 모드에 따라 Custom Start/End 입력 활성/비활성 토글."""
        custom = self.rb_bake_custom.isChecked()
        self.le_bake_start.setEnabled(custom)
        self.le_bake_end.setEnabled(custom)

    def _bake_update_smart_mode(self, *args):
        """Smart bake 체크 상태에 따라 Tolerance 입력 활성/비활성 토글."""
        self.le_bake_smart_tol.setEnabled(self.cb_bake_smart.isChecked())

    def _bake_resolve_range(self):
        """라디오에 따라 (start, end) 결정. 실패 시 None.
        Current timeline = playback min/maxTime, Custom = QLineEdit 입력."""
        if self.rb_bake_timeline.isChecked():
            start = int(cmds.playbackOptions(q=True, minTime=True))
            end = int(cmds.playbackOptions(q=True, maxTime=True))
            return (start, end)

        s_txt = self.le_bake_start.text().strip()
        e_txt = self.le_bake_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None
        start = int(s_txt)
        end = int(e_txt)
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None
        return (start, end)

    def on_bake(self):

        objs = self.bake_tsl.get_all_items()   # 리스트업된 항목만 (씬 선택 아님)
        if not objs:
            self.log("[Warning] Add controllers to the Bake List first.")
            return

        rng = self._bake_resolve_range()
        if rng is None:
            return
        start, end = rng

        channels = []
        if self.cb_bake_t.isChecked():
            channels += ["tx", "ty", "tz"]
        if self.cb_bake_r.isChecked():
            channels += ["rx", "ry", "rz"]
        if self.cb_bake_s.isChecked():
            channels += ["sx", "sy", "sz"]
        if not channels:
            self.log("[Warning] Enable at least one channel group.")
            return

        smart = self.cb_bake_smart.isChecked()
        smart_tol = BakeManager.DEFAULT_SMART_TOLERANCE
        if smart:
            tol_txt = self.le_bake_smart_tol.text().strip()
            try:
                smart_tol = float(tol_txt)
            except ValueError:
                self.log("[Warning] Invalid Tolerance, using {0}.".format(smart_tol))

        count, msg = BakeManager.bake(
            objs, start, end, channels=channels,
            simulation=self.cb_bake_sim.isChecked(),
            disable_implicit=not self.cb_bake_keep_con.isChecked(),  # 체크=유지 -> False
            smart=smart,
            smart_tolerance=smart_tol,
        )
        self.log(msg)

    # --------------------------------------------------
    # Follow (target match bake)
    # --------------------------------------------------

    def _follow_slider_to_le(self, value):
        """Slider(0..100) 변경 -> Blend LineEdit(0..1) 동기화."""
        self.le_follow_blend.setText("{0:.2f}".format(value / 100.0))

    def _follow_le_to_slider(self):
        """Blend LineEdit(0..1) 입력 확정 -> Slider(0..100) 동기화."""
        txt = self.le_follow_blend.text().strip()
        try:
            v = max(0.0, min(1.0, float(txt)))
        except ValueError:
            return
        self.sld_follow_blend.blockSignals(True)
        self.sld_follow_blend.setValue(int(round(v * 100)))
        self.sld_follow_blend.blockSignals(False)

    def on_follow_bake(self):

        targets = self.follow_tgt_tsl.get_all_items()
        followers = self.follow_flw_tsl.get_all_items()

        if not targets or not followers:
            self.log("[Warning] Fill both Target and Follower lists.")
            return
        if len(targets) != len(followers):
            self.log("[Warning] Target ({0}) / Follower ({1}) count mismatch.".format(
                len(targets), len(followers)))
            return

        # Start / End 파싱.
        s_txt = self.le_follow_start.text().strip()
        e_txt = self.le_follow_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return
        start = int(s_txt)
        end = int(e_txt)
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        do_t = self.cb_follow_t.isChecked()
        do_r = self.cb_follow_r.isChecked()
        do_s = self.cb_follow_s.isChecked()
        if not (do_t or do_r or do_s):
            self.log("[Warning] Enable at least one channel group.")
            return

        b_txt = self.le_follow_blend.text().strip()
        try:
            blend = float(b_txt)
        except ValueError:
            self.log("[Warning] Invalid Blend value.")
            return

        count, msg = FollowMatchManager.match_follow(
            targets, followers, start, end, blend,
            do_translate=do_t, do_rotate=do_r, do_scale=do_s)
        self.log(msg)

    def show_about(self, *args):
        # jointTool 의 show_about(confirmDialog) 패턴을 Qt 로 옮김
        QMessageBox.information(
            self,
            "About",
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )

    # --------------------------------------------------
    # Hotkey
    # --------------------------------------------------

    def on_toggle_hotkey(self, checked):
        self._enable_hotkey(checked)

    def _enable_hotkey(self, on):
        """체크 상태에 따라 Shift+A 핫키를 설치/복원하고 상태 라벨을 갱신."""
        if on:
            ok, msg = self.hotkey_mgr.install()
            self.lbl_hotkey.setText("Shift+A : ON" if ok else "Shift+A : unavailable")
        else:
            self.hotkey_mgr.restore()
            msg = "Shift+A hotkey disabled."
            self.lbl_hotkey.setText("Shift+A : OFF")

        self.log(msg)

    # --------------------------------------------------
    # Teardown
    # --------------------------------------------------

    def closeEvent(self, event):
        # 창이 닫힐 때 Shift+A 를 원래 바인딩으로 복원
        try:
            if getattr(self, "hotkey_mgr", None):
                self.hotkey_mgr.restore()
        finally:
            super().closeEvent(event)
