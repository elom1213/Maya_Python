# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00120_FKIK - Qt UI (레거시 PY_JUN_makeUI_FKIKTool 대체)
#
# v01.12 (2026-10-12)
#   - Setup 칸을 v01.10 높이로 되돌렸다. 리스트 · Manual/Auto 라디오 · 버튼을 한 줄에 두고,
#     Auto 리스트는 TSL 위젯 대신 50px 고정 QListWidget. 모드에 맞는 버튼 하나만 보인다.
# v01.11 (2026-10-12)
#   - Setup 에 Manual / Auto 모드. Manual 은 예전처럼 Select Objects, Auto 는 Refresh 로 씬을
#     네임스페이스 단위로 조사해 FK/IK 스위칭이 되는 리그를 리스트에 올린다 (core/fkik_scan.py).
#   - Targets / Followers 두 리스트는 접이식(기본 접힘). Search 는 코드만 남기고 화면에서 숨겼다.
#   - 메뉴 바 `Dev Mode` (공용 JUN_mod_devMode_qt_v01) 로 Developer / Release 화면을 번갈아 본다.
#     Release 화면 = Auto 기본 · 두 리스트 없음 · Bake (Constraint) 없음 · 로그 접힘 · Force Refresh 없음.
#   - Bake IK / Bake FK 는 공용 진행률 팝업(JUN_mod_progress_qt_v01)으로 프레임 진행을 보인다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_timeRange_qt
from Framework.qt import JUN_mod_collapsible_qt
from Framework.qt import JUN_mod_progress_qt
from Framework.core.maya_refresh import force_refresh
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_devMode_qt_v01 import JUN_mod_devMode_qt_v01

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00120_FKIK.app.config.version import VERSION, LAST_UPDATE
from tools.A00120_FKIK.app.core import (
    FKIKSetup,
    FKIKScanner,
    FKIKMatcher,
    search_by_token,
)


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.win_width  = 480
        self.win_height = 760
        self.win_title  = f"FKIK Tool v{VERSION}"

        # Auto 모드가 찾은 단위들 - 리스트 표시 라벨 -> unit dict (core/fkik_scan.py)
        self._units = {}
        self._fitted_once = False

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # ==================================================
    # UI 구성
    # ==================================================

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        # 맨 위 메뉴 바 (Help > About)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        self._build_setup_section(root)
        self._build_limb_section(root)
        self._build_lists_section(root)
        self._build_search_section(root)
        self._build_match_bake_section(root)
        self._build_log_section(root)
        root.addStretch(1)

        # Help 오른쪽의 `Dev Mode` 메뉴 (공용 위젯, 개발자 모드에서만 생긴다).
        # 배포본은 메뉴가 없고 is_developer() 가 늘 False 라 Release 화면으로 고정된다.
        self.dev_mode = JUN_mod_devMode_qt_v01(
            self.menu_bar, tool_file=__file__,
            developer_tooltip=(
                "Developer view - Manual / Auto setup, Targets / Followers lists,\n"
                "Bake (Constraint), full log, Force Refresh."),
            release_tooltip=(
                "The view people get in the shared tool - Auto setup only,\n"
                "no lists, no Bake (Constraint), log collapsed."))
        self.dev_mode.modeChanged.connect(self.apply_view)
        self.apply_view(self.dev_mode.is_developer())

    # --------------------------------------------------
    # Setup
    # --------------------------------------------------

    def _build_setup_section(self, root):

        box = QGroupBox("Setup")
        layout = QVBoxLayout(box)

        # v01.12 : 한 줄 - [리스트(50px)] (Manual)(Auto) [Select Objects | Refresh].
        # 라디오 행을 따로 두고 Auto 리스트를 TSL 위젯(헤더 포함)으로 만들었더니 칸이 v01.10 보다
        # 58px 길어졌다. 리스트 50px 이 줄 높이를 정하고 나머지는 그 안에 들어가므로 세로는 v01.10 과 같다.
        row = QHBoxLayout()

        # 리스트 자리 : Manual = 선택한 오브젝트 / Auto = 네임스페이스 단위 리그
        self.setup_stack = QStackedWidget()
        self.setup_stack.setFixedHeight(50)

        self.lw_rig = QListWidget()
        self.lw_rig.setFixedHeight(50)
        self.lw_rig.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setup_stack.addWidget(self.lw_rig)

        # 항목은 네임스페이스 라벨이라 씬 노드가 아니다 - 일반 QListWidget (편집 버튼 · UUID 없음).
        self.lw_units = QListWidget()
        self.lw_units.setFixedHeight(50)
        self.lw_units.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lw_units.setToolTip(
            "Rigs found in the scene, by namespace.\n"
            "Pick one to load its Targets / Followers.")
        self.lw_units.itemSelectionChanged.connect(self.on_unit_selected)
        self.setup_stack.addWidget(self.lw_units)

        row.addWidget(self.setup_stack, 1)

        # 모드 : Manual (선택한 오브젝트) / Auto (씬 조사)
        self.rb_manual = QRadioButton("Manual")
        self.rb_manual.setToolTip(
            "Select the rig (top node or any controls) in the scene,\n"
            "then press Select Objects to resolve Targets / Followers.")
        self.rb_auto = QRadioButton("Auto")
        self.rb_auto.setToolTip(
            "Scan the scene by namespace and list every rig that can switch FK / IK.\n"
            "Press Refresh to scan again. Pick a rig in the list to load it.")
        self.rb_manual.setChecked(True)
        row.addWidget(self.rb_manual)
        row.addWidget(self.rb_auto)

        # 버튼 : 모드에 맞는 하나만 보인다
        self.btn_setup = QPushButton("Select Objects")
        self.btn_setup.clicked.connect(self.on_setup)
        row.addWidget(self.btn_setup)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip("Scan the scene again (by namespace).")
        self.btn_refresh.clicked.connect(self.on_refresh)
        self.btn_refresh.setVisible(False)
        row.addWidget(self.btn_refresh)

        layout.addLayout(row)

        self.lbl_state = QLabel("State : Waiting...")
        self.lbl_state.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._set_state("State : Waiting...", ok=None)
        layout.addWidget(self.lbl_state)

        self.rb_auto.toggled.connect(self._on_mode_toggled)

        root.addWidget(box)

    # --------------------------------------------------
    # Limb checkboxes
    # --------------------------------------------------

    def _build_limb_section(self, root):

        row = QHBoxLayout()

        arm_box = QGroupBox("Arm")
        arm_layout = QVBoxLayout(arm_box)
        self.cb_arm_l = QCheckBox("Arm Left")
        self.cb_arm_r = QCheckBox("Arm Right")
        self.cb_arm_l.setChecked(True)
        self.cb_arm_r.setChecked(True)
        arm_layout.addWidget(self.cb_arm_l)
        arm_layout.addWidget(self.cb_arm_r)
        row.addWidget(arm_box)

        leg_box = QGroupBox("Leg")
        leg_layout = QVBoxLayout(leg_box)
        self.cb_leg_l = QCheckBox("Leg Left")
        self.cb_leg_r = QCheckBox("Leg Right")
        self.cb_leg_l.setChecked(True)
        self.cb_leg_r.setChecked(True)
        leg_layout.addWidget(self.cb_leg_l)
        leg_layout.addWidget(self.cb_leg_r)
        row.addWidget(leg_box)

        root.addLayout(row)

    # --------------------------------------------------
    # Targets / Followers lists (접이식, 기본 접힘)
    # --------------------------------------------------

    def _build_lists_section(self, root):

        # 재사용 PySide tsl 위젯(Framework.qt.MOD_tsl_qt_v01) 사용.
        # A00140_ConnectClosest 와 동일한 형식. Select/Add/Del/Up/Down/Sort/씬 선택은 위젯이 자체 처리한다.
        self.tsl_targets = self._make_edit_list("Targets")
        self.tsl_followers = self._make_edit_list("Followers")

        row = QHBoxLayout()
        row.addWidget(self.tsl_targets)
        row.addWidget(self.tsl_followers)

        # v01.11 : 두 리스트는 펼쳐야 보인다. 평소에는 Setup 결과를 확인할 일이 드물다.
        self.lists_box = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            "Targets / Followers", expanded=False)
        self.lists_box.header.setToolTip(
            "Show the Targets / Followers that Setup resolved.\n"
            "Edit them here only when the automatic result needs a fix.")
        self.lists_box.add_layout(row)
        self.lists_box.toggled.connect(lambda _e: self._fit_height_later())

        root.addWidget(self.lists_box)

    def _make_edit_list(self, title):
        """A00140_ConnectClosest 와 동일한 형식의 재사용 tsl 위젯(Select/Add/Del/Up/Down/Sort)."""

        return JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title=title)

    # --------------------------------------------------
    # Search (v01.11 : 화면에서 숨김 - 코드는 남긴다)
    # --------------------------------------------------

    def _build_search_section(self, root):

        box = QGroupBox("Search")
        row = QHBoxLayout(box)

        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("token")
        row.addWidget(self.le_search)

        self.cb_invert = QCheckBox("Invert")
        row.addWidget(self.cb_invert)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.on_search)
        row.addWidget(self.btn_search)

        # 사용자 요청(v01.11) : Search 는 쓰지 않는다. 지우지 않고 숨긴다 - on_search 는 그대로 동작한다.
        box.setVisible(False)
        self.search_box = box

        root.addWidget(box)

    # --------------------------------------------------
    # Match / Bake
    # --------------------------------------------------

    def _build_match_bake_section(self, root):

        box = QGroupBox("Match / Bake")
        layout = QVBoxLayout(box)

        # frame range - 공용 위젯(JUN_mod_timeRange_qt).
        # Start/End 입력 + 칸별 Get Current + 선택 키에서 구간을 읽는 Get Sel Range 를
        # 모두 제공한다. 기본값은 현재 playback 범위.
        start, end = self._playback_range()
        self.bake_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=start, end_value=end, log_callback=self.log)
        layout.addWidget(self.bake_range)

        # match
        match_row = QHBoxLayout()
        self.btn_match_ik = QPushButton("Match IK")
        self.btn_match_fk = QPushButton("Match FK")
        self.btn_match_ik.clicked.connect(lambda: self.on_match(ik_to_fk=True))
        self.btn_match_fk.clicked.connect(lambda: self.on_match(ik_to_fk=False))
        match_row.addWidget(self.btn_match_ik)
        match_row.addWidget(self.btn_match_fk)
        layout.addLayout(match_row)

        # bake
        bake_row = QHBoxLayout()
        self.btn_bake_ik = QPushButton("Bake IK")
        self.btn_bake_fk = QPushButton("Bake FK")
        self.btn_bake_ik.clicked.connect(lambda: self.on_bake(ik_to_fk=True))
        self.btn_bake_fk.clicked.connect(lambda: self.on_bake(ik_to_fk=False))
        bake_row.addWidget(self.btn_bake_ik)
        bake_row.addWidget(self.btn_bake_fk)
        layout.addLayout(bake_row)

        self.btn_bake_constraint = QPushButton("Bake (Constraint)")
        self.btn_bake_constraint.clicked.connect(self.on_bake_constraint)
        layout.addWidget(self.btn_bake_constraint)

        root.addWidget(box)

    # --------------------------------------------------
    # Log
    # --------------------------------------------------

    def _build_log_section(self, root):

        self.te_log = JUN_mod_log_qt_v01(
            window_title="FKIK Tool - Log",
            object_name="JUN_A00120_FKIK_log_window")
        self.te_log.setFixedHeight(90)
        root.addWidget(self.te_log)

        # Force Refresh : 어떤 이유로든 뷰포트가 멈춰(커브 편집이 프레임 이동 전까지
        # 반영 안 됨) 있을 때, 막힌 전역 refresh suspend 를 풀고 한 번 다시 그린다.
        self.btn_force_refresh = QPushButton("Force Refresh (Unfreeze Viewport)")
        self.btn_force_refresh.setToolTip(
            "Clear a stuck viewport refresh-suspend and redraw once.\n"
            "Use if Graph Editor edits don't show until you scrub frames.")
        self.btn_force_refresh.clicked.connect(self.on_force_refresh)
        root.addWidget(self.btn_force_refresh)

    def on_force_refresh(self):
        force_refresh()
        self.log("Viewport refresh restored.")

    def show_about(self, *args):
        message = (
            "FKIK Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Match and bake FK/IK controls on a rig.\n"
            "\n"
            "- Setup > Manual : select the rig and press Select Objects to\n"
            "  resolve Targets / Followers from the selection.\n"
            "- Setup > Auto : Refresh scans the scene by namespace and lists\n"
            "  every rig that can switch FK / IK. Pick one to load it.\n"
            "- Match IK / Match FK : snap the pose once at the current frame.\n"
            "- Bake IK / Bake FK : bake the Start-End range constraint-free,\n"
            "  per frame via matchTransform (rotateOrder-safe, keeps keys on\n"
            "  other ranges and animation layers untouched). A progress popup\n"
            "  shows the frames as they go.\n"
            "- Get Current : fill that Start / End field with the current frame.\n"
            "- Get Sel Range : fill Start and End from the first / last\n"
            "  selected keyframe.\n"
            "- Bake (Constraint) : optional parentConstraint + bakeSimulation\n"
            "  path for selected pairs over the playback range.\n"
            "- Dev Mode (developers only) : switch between the Developer view\n"
            "  and the Release view people get in the shared tool.\n"
            "\n"
            "All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)

    # ==================================================
    # Developer / Release 화면 (v01.11)
    # ==================================================

    def apply_view(self, developer):
        """Developer(True) / Release(False) 화면.

        Release 화면 = 배포본을 받은 사람이 보는 것:
          - Setup 은 Auto 가 기본 (Manual 라디오는 남는다)
          - Targets / Followers 접이식 자체가 없다
          - Bake (Constraint) 없음
          - 로그는 접힌 상태(Show 로 펼 수 있다)
          - Force Refresh 없음
        Developer 로 돌아오면 전부 되살린다 (Setup 모드는 건드리지 않는다).
        """
        developer = bool(developer)

        self.lists_box.setVisible(developer)
        self.btn_bake_constraint.setVisible(developer)
        self.btn_force_refresh.setVisible(developer)
        self.te_log.set_shrunk(not developer)

        if not developer and not self.rb_auto.isChecked():
            self.rb_auto.setChecked(True)      # -> _on_mode_toggled -> Auto 조사

        self._fit_height_later()

    # ==================================================
    # 창 높이
    # ==================================================

    def _fit_height(self):
        """창 높이를 지금 보이는 내용에 맞춘다 (접이식 토글 · 화면 전환 뒤)."""
        layout = QWidget.layout(self)
        if layout is None:
            return
        layout.activate()
        target = max(layout.sizeHint().height(), self.minimumSizeHint().height())
        # 화면보다 큰 창은 아래가 잘려 로그창 잔상이 남는다 - 작업 영역 높이 안으로.
        screen = QApplication.primaryScreen() if QApplication.instance() else None
        if screen is not None:
            target = min(target, screen.availableGeometry().height() - 80)
        self.resize(self.width(), target)

    def _fit_height_later(self):
        if self.isVisible():
            QTimer.singleShot(0, self._fit_height)

    def showEvent(self, event):
        super().showEvent(event)
        # 테마(qss)가 입혀진 뒤 처음 보일 때 한 번 - 접힌 리스트 · 숨긴 Search 만큼 창을 줄인다.
        if not self._fitted_once:
            self._fitted_once = True
            self._fit_height()

    # ==================================================
    # Helpers
    # ==================================================

    def log(self, text):
        self.te_log.append(text)

    def _playback_range(self):
        """Bake 구간 위젯의 초기값으로 쓸 현재 playback 범위(start, end)."""
        try:
            return (int(cmds.playbackOptions(q=True, minTime=True)),
                    int(cmds.playbackOptions(q=True, maxTime=True)))
        except Exception:
            return (None, None)

    def _set_state(self, text, ok=None):
        self.lbl_state.setText(text)
        if ok is True:
            color = "background-color: rgb(60, 170, 60); color: black;"
        elif ok is False:
            color = "background-color: rgb(200, 60, 60); color: black;"
        else:
            color = "background-color: rgb(220, 220, 220); color: black;"
        self.lbl_state.setStyleSheet(color)

    def _set_list_items(self, lw, items):
        # Setup 의 lw_rig / lw_units(일반 QListWidget) 채우기용. (Targets/Followers 는 tsl 위젯 사용)
        lw.blockSignals(True)
        lw.clear()
        for it in items:
            lw.addItem(it)
        lw.blockSignals(False)

    @staticmethod
    def _selected_texts(lw):
        return [it.text() for it in lw.selectedItems()]

    @staticmethod
    def _select_list_text(lw, text):
        """시그널 없이 글이 같은 행 하나를 고른다 (없으면 아무것도 안 한다)."""
        lw.blockSignals(True)
        lw.clearSelection()
        for i in range(lw.count()):
            if lw.item(i).text() == text:
                lw.setCurrentRow(i)
                lw.item(i).setSelected(True)
                break
        lw.blockSignals(False)

    def _load_unit(self, unit):
        """Auto 모드가 찾은 단위 하나를 Targets / Followers 에 올린다."""
        self.tsl_targets.set_items(unit["targets"])
        self.tsl_followers.set_items(unit["followers"])
        self._set_state("State : Success (%s)" % unit["label"], ok=True)
        self.log(
            "Loaded '%s' : %d targets / %d followers"
            % (unit["label"], len(unit["targets"]), len(unit["followers"])))

    # ==================================================
    # Handlers
    # ==================================================

    def _on_mode_toggled(self, auto):
        """Manual <-> Auto. Auto 로 들어올 때마다 씬을 새로 조사한다."""
        self.setup_stack.setCurrentIndex(1 if auto else 0)
        self.btn_setup.setVisible(not auto)
        self.btn_refresh.setVisible(auto)
        if auto:
            self.on_refresh()

    def on_setup(self):
        selection = cmds.ls(sl=True, fl=True)

        self._set_list_items(self.lw_rig, selection or [])

        result = FKIKSetup.resolve(selection)

        if not result["ok"]:
            self._set_state("State : " + result["message"], ok=False)
            self.log(result["message"])
            return

        self.tsl_targets.set_items(result["targets"])
        self.tsl_followers.set_items(result["followers"])

        self._set_state("State : Success", ok=True)
        self.log(
            f"Setup success : {len(result['targets'])} targets / "
            f"{len(result['followers'])} followers"
        )

    def on_refresh(self):
        """Auto : 씬을 네임스페이스 단위로 조사해 리그 리스트를 다시 채운다.

        전에 골라 둔 단위가 여전히 있으면 그것을, 없으면 첫 단위를 고른다(고르면 바로 로드된다).
        """
        previous = self._selected_texts(self.lw_units)
        previous = previous[0] if previous else None

        result = FKIKScanner.scan()
        units = result["units"]
        self._units = {u["label"]: u for u in units}

        self._set_list_items(self.lw_units, [u["label"] for u in units])

        for unit in result["skipped"]:
            self.log("[WARN] Skipped '%s' : %s" % (unit["label"], unit["message"]))

        if not units:
            self.tsl_targets.set_items([])
            self.tsl_followers.set_items([])
            self._set_state("State : No FK / IK rig found in the scene", ok=False)
            self.log("Refresh : no FK / IK rig found (0 units).")
            return

        self.log("Refresh : %d rig(s) found." % len(units))

        pick = previous if previous in self._units else units[0]["label"]
        # _select_list_text 는 시그널을 막으므로 로드는 직접 부른다.
        self._select_list_text(self.lw_units, pick)
        self._load_unit(self._units[pick])

    def on_unit_selected(self):
        """Auto 리스트에서 리그를 고르면 그 단위를 로드한다."""
        selected = self._selected_texts(self.lw_units)
        if not selected:
            return
        unit = self._units.get(selected[0])
        if unit is None:
            return
        self._load_unit(unit)

    def on_search(self):
        token = self.le_search.text().strip()
        if not token:
            self.log("[Warning] Enter a search token.")
            return

        invert = self.cb_invert.isChecked()
        matched_all = []

        for tsl in (self.tsl_targets, self.tsl_followers):
            matched = search_by_token(tsl.get_all_items(), token, invert)
            tsl.select_by_texts(matched)
            matched_all.extend(matched)

        if matched_all:
            cmds.select(matched_all)

        self.log(f"Search '{token}' (invert={invert}) : {len(matched_all)} matched")

    def on_match(self, ik_to_fk):
        all_t = self.tsl_targets.get_all_items()
        all_f = self.tsl_followers.get_all_items()

        tgt, flw = FKIKMatcher.build_pairs(
            all_t, all_f,
            self.cb_arm_l.isChecked(), self.cb_arm_r.isChecked(),
            self.cb_leg_l.isChecked(), self.cb_leg_r.isChecked(),
            ik_to_fk,
        )

        if not tgt or not flw:
            self.log("[Warning] No pairs to match. Run Setup and check limb options.")
            return

        self.tsl_targets.select_by_texts(tgt)
        self.tsl_followers.select_by_texts(flw)

        count = FKIKMatcher.match(tgt, flw)

        mode = "IK" if ik_to_fk else "FK"
        self.log(f"Match {mode} : {count} pairs matched")

    def on_bake(self, ik_to_fk):
        all_t = self.tsl_targets.get_all_items()
        all_f = self.tsl_followers.get_all_items()

        tgt, flw = FKIKMatcher.build_pairs(
            all_t, all_f,
            self.cb_arm_l.isChecked(), self.cb_arm_r.isChecked(),
            self.cb_leg_l.isChecked(), self.cb_leg_r.isChecked(),
            ik_to_fk,
        )

        if not tgt or not flw:
            self.log("[Warning] No pairs to bake. Run Setup and check limb options.")
            return

        # 공용 위젯은 칸이 비었거나 숫자가 아니면 None 을 준다(스핀박스와 달리 빈 값 가능).
        rng = self.bake_range.values()
        if rng is None:
            self.log("[Warning] Enter a valid Start / End frame.")
            return
        start, end = rng

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        self.tsl_targets.select_by_texts(tgt)
        self.tsl_followers.select_by_texts(flw)

        mode = "IK" if ik_to_fk else "FK"

        # v01.11 : 공용 진행률 팝업 - core 의 bake 가 프레임마다 콜백을 부른다.
        dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01(
            self, title="FKIK Tool - Bake %s" % mode,
            message="Starting...", phases=[("Baking frames", 1)])
        dlg.start()
        try:
            dlg.begin_phase()
            frames = FKIKMatcher.bake(tgt, flw, start, end, progress=dlg.callback())
        finally:
            dlg.finish()

        self.log(f"Bake {mode} : {frames} frames baked [{start}-{end}]")

    def on_bake_constraint(self):
        tgt = self.tsl_targets.selected_items()
        flw = self.tsl_followers.selected_items()

        if not tgt or not flw:
            self.log("[Warning] Select matching items in both Targets and Followers.")
            return

        if len(tgt) != len(flw):
            self.log(
                f"[Warning] Count mismatch : {len(tgt)} targets vs {len(flw)} followers."
            )
            return

        count = FKIKMatcher.bake_constraint(tgt, flw)
        self.log(f"Bake (Constraint) : {count} pairs baked")
