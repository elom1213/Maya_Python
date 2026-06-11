# -*- coding: utf-8 -*-
"""
Control Rig Tool - PySide(Qt) UI.

원본 JUN_PY_ControlRigTool_V01_07.py 의 maya.cmds UI(PY_JUN_makeUI_ContrlRigTool)를
PySide 로 재구성. 로직은 app/core 모듈에 위임하고, 이 모듈은 위젯 구성과 시그널 연결만
담당한다. 모든 UI 문자열(버튼/로그/상태)은 영어.
"""

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from tools.A00130_ControlRig.app.config.version import VERSION
from tools.A00130_ControlRig.app.core import (
    MayaScene,
    CageModel,
    RigMatcher,
    setup_pose_objects,
    constants,
    selection_utils,
)


# checkbox 순서 = cage 의 idx 순서 (spine, shoulder, arm_l, arm_r, leg_l, leg_r, fingers_l, fingers_r)
CHECKBOX_LABELS = [
    "Spine",
    "Shoulders",
    "Arm Left",
    "Arm Right",
    "Leg Left",
    "Leg Right",
    "Fingers Left",
    "Fingers Right",
]


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()

        # 원본의 전역 cage 를 인스턴스 속성으로 캡슐화
        self.cage = CageModel()

        self.setWindowTitle("Control Rig Tool v{0}".format(VERSION))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(480, 800)

        self._build_ui()
        self._connect_signals()

    # ================================================================
    # UI 구성
    # ================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.addWidget(self._build_setup_group())
        root.addWidget(self._build_cage_part_group())
        root.addWidget(self._build_list_group())
        root.addWidget(self._build_match_group())

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

    def _build_setup_group(self):
        group = QGroupBox("Tool : Setup control rig")
        layout = QVBoxLayout(group)

        row = QHBoxLayout()
        self.name_list = QListWidget()
        self.name_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.name_list.setFixedHeight(60)
        row.addWidget(self.name_list)

        self.btn_select_objects = QPushButton("Select Objects")
        row.addWidget(self.btn_select_objects)
        layout.addLayout(row)

        self.lbl_state = QLabel("State : Searching...")
        self._set_status("State : Searching...", "neutral")
        layout.addWidget(self.lbl_state)

        return group

    def _build_cage_part_group(self):
        group = QGroupBox("Cage Part")
        grid = QGridLayout(group)

        self.checkboxes = []
        for i, label in enumerate(CHECKBOX_LABELS):
            cb = QCheckBox(label)
            self.checkboxes.append(cb)
            # 2열 배치: 좌측 0~3, 우측 4~7 (원본의 좌/우 컬럼 구성과 동일)
            col = 0 if i < 4 else 1
            r = i if i < 4 else i - 4
            grid.addWidget(cb, r, col)

        return group

    def _build_list_group(self):
        group = QGroupBox("Set Up")
        layout = QHBoxLayout(group)

        # 기존 UI(Select 버튼 → 헤더 → 리스트 → Add/Del/Up/Down, Sort 없음)를 보존하기 위해
        # 재사용 위젯을 select_label 커스텀 + show_sort=False 로 생성한다.
        self.tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select targets", show_sort=False)
        self.flw_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select followers", show_sort=False)

        layout.addWidget(self.tgt_tsl)
        layout.addWidget(self.flw_tsl)

        return group

    def _build_match_group(self):
        group = QGroupBox("Tool : Match IK and FK")
        layout = QVBoxLayout(group)

        self.btn_setup_followers = QPushButton("Set up Followers")
        self.btn_match = QPushButton("Match")
        self.btn_setup_ik = QPushButton("Set up IK")
        self.btn_setup_pose = QPushButton("Set up pose objects")

        for b in (self.btn_setup_followers, self.btn_match, self.btn_setup_ik, self.btn_setup_pose):
            layout.addWidget(b)

        return group

    def _connect_signals(self):
        self.btn_select_objects.clicked.connect(self.on_select_objects)

        # tgt/flw 리스트(Select/Add/Del/Up/Down, 항목 클릭 시 씬 선택)는 위젯이 자체 처리.
        # name_list(Setup 입력 리스트)만 씬 선택 와이어링을 유지한다.
        self.name_list.itemSelectionChanged.connect(lambda: self._select_in_scene(self.name_list))

        self.btn_setup_followers.clicked.connect(self.on_setup_followers)
        self.btn_match.clicked.connect(self.on_match)
        self.btn_setup_ik.clicked.connect(self.on_setup_ik)
        self.btn_setup_pose.clicked.connect(self.on_setup_pose_objects)

    # ================================================================
    # QListWidget helpers
    # ================================================================

    @staticmethod
    def _list_items(list_widget):
        return [list_widget.item(i).text() for i in range(list_widget.count())]

    @staticmethod
    def _selected_items(list_widget):
        return [item.text() for item in list_widget.selectedItems()]

    def _select_in_scene(self, list_widget):
        items = self._selected_items(list_widget)
        if items:
            MayaScene.select(items)

    def _set_status(self, text, kind="neutral"):
        colors = {
            "success": "background-color: rgb(0, 200, 0); color: black;",
            "fail": "background-color: rgb(220, 0, 0); color: white;",
            "neutral": "background-color: rgb(245, 245, 245); color: black;",
        }
        self.lbl_state.setText(text)
        self.lbl_state.setStyleSheet(colors.get(kind, colors["neutral"]))

    # ================================================================
    # 슬롯 : Select Objects (원본 JUN_cmd_controlRig_setup_btn)
    # ================================================================

    def on_select_objects(self):
        token_option_ctl = constants.TKN_OPTION_CTL

        selection = MayaScene.selection() or []
        objects = []
        sets = []

        self.name_list.clear()
        for item in selection:
            self.name_list.addItem(item)
            if MayaScene.is_set(item):
                sets.append(item)
            else:
                objects.append(item)

        obj_children = selection_utils.make_hierarchy(objects, True, True)

        # option controller 존재 확인
        has_option_ctl = any(token_option_ctl in obj for obj in obj_children)
        if not has_option_ctl:
            self._set_status(
                "State : Fail to find objects for setup ({0})".format(token_option_ctl),
                "fail",
            )
            return

        # cage root set 찾기
        cage_root = ""
        for s in sets:
            if self.cage.MSN_tkn_Cage_root in s:
                cage_root = s
                break

        set_children = MayaScene.sets_query(cage_root)
        for s in set_children:
            if self.cage.MSN_tkn_Cage_01_pos in s:
                self.cage.set_rnm_str_pos_root(s)
            if self.cage.MSN_tkn_Cage_03_Tgt in s:
                self.cage.set_rnm_str_tgt_root(s)
            if self.cage.MSN_tkn_Cage_04_helper in s:
                self.cage.set_rnm_str_helper(s)

        self.cage.set_selected_objs(self._list_items(self.name_list))
        self.cage.set_rnm_lst_all()
        self.cage.set_idx_for_cbg()

        self._set_status("State : Success", "success")

    # ================================================================
    # 슬롯 : Match IK and FK
    # ================================================================

    def _checkbox_states(self):
        return [cb.isChecked() for cb in self.checkboxes]

    def on_setup_followers(self):
        """원본 JUN_CR_setUp_followers."""
        items = []
        for idx, is_checked in enumerate(self._checkbox_states()):
            if is_checked:
                group = self.cage.get_rnm_lst(idx)
                if group:
                    items.extend(group)
        self.flw_tsl.set_items(items)

    def on_match(self):
        """원본 JUN_CR_match."""
        mcr = RigMatcher()
        mcr.set_matcher(self.tgt_tsl.get_all_items(), self.flw_tsl.get_all_items())

        cage = self.cage
        for idx, is_checked in enumerate(self._checkbox_states()):
            if not is_checked:
                continue

            if cage.is_spine(idx):
                mcr.match_cage_spine()
                idx_hid = mcr.num_iter
                obj_hid = mcr.flw[idx_hid]
                MayaScene.set_visibility(obj_hid, False)

            if cage.is_arm_left(idx):
                mcr.match_cage_arm_left(cage, pole_obj=cage.rnm_poleObj_armLeft[0], helper_objs=cage.rnm_helperJnts_arm_l)

            if cage.is_arm_right(idx):
                mcr.match_cage_arm_right(cage.rnm_poleObj_armRight[0], cage_given=cage, helper_objs=cage.rnm_helperJnts_arm_r)

            if cage.is_leg_left(idx):
                mcr.match_cage_leg_l(cage, cage.rnm_poleObj_legLeft[0], cage.rnm_helperJnts_leg_l)

            if cage.is_leg_right(idx):
                mcr.match_cage_leg_r(cage, cage.rnm_poleObj_legRight[0], cage.rnm_helperJnts_leg_r)

            if cage.is_fingers_left(idx):
                mcr.match_cage_fingers_left()

            if cage.is_fingers_right(idx):
                mcr.match_cage_fingers_right()

    def on_setup_ik(self):
        """원본 JUN_CR_setUp_IK : preferred angle 설정."""
        print("set preferred angle")
        for idx, is_checked in enumerate(self._checkbox_states()):
            if is_checked:
                rnm_jnt_to_set_pa = self.cage.get_rnm_PA(idx)
                if rnm_jnt_to_set_pa is not None:
                    print(rnm_jnt_to_set_pa)
                    MayaScene.set_preferred_angles(rnm_jnt_to_set_pa)
        print("set preferred angle End")

    def on_setup_pose_objects(self):
        """원본 JUN_CR_setUp_pose_objects."""
        setup_pose_objects(self.cage)
