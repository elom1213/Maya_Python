# -*- coding: utf-8 -*-
"""
Control Rig Tool - PySide(Qt) UI.

원본 JUN_PY_ControlRigTool_V01_07.py 의 maya.cmds UI(PY_JUN_makeUI_ContrlRigTool)를
PySide 로 재구성. 로직은 app/core 모듈에 위임하고, 이 모듈은 위젯 구성과 시그널 연결만
담당한다. 모든 UI 문자열(버튼/로그/상태)은 영어.
"""

from Framework.qt.qt import *

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

        layout.addLayout(self._build_target_column())
        layout.addLayout(self._build_follower_column())

        return group

    def _build_target_column(self):
        col = QVBoxLayout()

        self.btn_select_targets = QPushButton("Select targets")
        col.addWidget(self.btn_select_targets)

        header = QHBoxLayout()
        header.addWidget(QLabel("Targets"))
        self.lbl_tgt_num = QLabel("Number: ")
        header.addWidget(self.lbl_tgt_num)
        col.addLayout(header)

        self.tgt_list = QListWidget()
        self.tgt_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        col.addWidget(self.tgt_list)

        btns = QHBoxLayout()
        self.btn_tgt_add = QPushButton("Add")
        self.btn_tgt_del = QPushButton("Del")
        self.btn_tgt_up = QPushButton("Up")
        self.btn_tgt_down = QPushButton("Down")
        for b in (self.btn_tgt_add, self.btn_tgt_del, self.btn_tgt_up, self.btn_tgt_down):
            btns.addWidget(b)
        col.addLayout(btns)

        return col

    def _build_follower_column(self):
        col = QVBoxLayout()

        self.btn_select_followers = QPushButton("Select followers")
        col.addWidget(self.btn_select_followers)

        header = QHBoxLayout()
        header.addWidget(QLabel("Followers"))
        self.lbl_flw_num = QLabel("Number: ")
        header.addWidget(self.lbl_flw_num)
        col.addLayout(header)

        self.flw_list = QListWidget()
        self.flw_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        col.addWidget(self.flw_list)

        btns = QHBoxLayout()
        self.btn_flw_add = QPushButton("Add")
        self.btn_flw_del = QPushButton("Del")
        self.btn_flw_up = QPushButton("Up")
        self.btn_flw_down = QPushButton("Down")
        for b in (self.btn_flw_add, self.btn_flw_del, self.btn_flw_up, self.btn_flw_down):
            btns.addWidget(b)
        col.addLayout(btns)

        return col

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

        self.btn_select_targets.clicked.connect(lambda: self.on_select(self.tgt_list, self.lbl_tgt_num))
        self.btn_select_followers.clicked.connect(lambda: self.on_select(self.flw_list, self.lbl_flw_num))

        self.btn_tgt_add.clicked.connect(lambda: self.on_list_add(self.tgt_list, self.lbl_tgt_num))
        self.btn_tgt_del.clicked.connect(lambda: self.on_list_del(self.tgt_list, self.lbl_tgt_num))
        self.btn_tgt_up.clicked.connect(lambda: self.on_list_up(self.tgt_list))
        self.btn_tgt_down.clicked.connect(lambda: self.on_list_down(self.tgt_list))

        self.btn_flw_add.clicked.connect(lambda: self.on_list_add(self.flw_list, self.lbl_flw_num))
        self.btn_flw_del.clicked.connect(lambda: self.on_list_del(self.flw_list, self.lbl_flw_num))
        self.btn_flw_up.clicked.connect(lambda: self.on_list_up(self.flw_list))
        self.btn_flw_down.clicked.connect(lambda: self.on_list_down(self.flw_list))

        # 리스트 항목 클릭 시 Maya 에서 선택
        self.name_list.itemSelectionChanged.connect(lambda: self._select_in_scene(self.name_list))
        self.tgt_list.itemSelectionChanged.connect(lambda: self._select_in_scene(self.tgt_list))
        self.flw_list.itemSelectionChanged.connect(lambda: self._select_in_scene(self.flw_list))

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

    @staticmethod
    def _selected_rows(list_widget):
        return sorted(idx.row() for idx in list_widget.selectedIndexes())

    @staticmethod
    def _set_items(list_widget, items):
        list_widget.clear()
        if items:
            list_widget.addItems(items)

    @staticmethod
    def _append_items(list_widget, items):
        if not items:
            return
        list_widget.addItems(items)

    def _update_number(self, label, list_widget):
        label.setText("Number: {0}".format(list_widget.count()))

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
    # 슬롯 : target / follower 리스트 편집
    # ================================================================

    def on_select(self, list_widget, number_label):
        """원본 JUN_cmd_toolSel_btn : 선택을 리스트로 대체."""
        selection = MayaScene.selection() or []
        self._set_items(list_widget, selection)
        self._update_number(number_label, list_widget)

    def on_list_add(self, list_widget, number_label):
        """원본 CMD_ToolSel_b_add : 중복 없이 선택을 추가."""
        existing = self._list_items(list_widget)
        for item in MayaScene.selection() or []:
            if item in existing:
                print("{0} is already in the list.".format(item))
            else:
                list_widget.addItem(item)
                existing.append(item)
        self._update_number(number_label, list_widget)

    def on_list_del(self, list_widget, number_label):
        """원본 CMD_ToolSel_b_del : 선택된 항목 삭제."""
        for row in reversed(self._selected_rows(list_widget)):
            list_widget.takeItem(row)
        self._update_number(number_label, list_widget)

    def on_list_up(self, list_widget):
        """원본 CMD_ToolSel_b_up."""
        items = self._list_items(list_widget)
        sel_index_1based = [r + 1 for r in self._selected_rows(list_widget)]
        if not sel_index_1based:
            return
        moved_items, result_index = selection_utils.move_up_index(items, sel_index_1based)
        self._set_items(list_widget, moved_items)
        for ri in result_index:
            self._select_row(list_widget, ri - 1)

    def on_list_down(self, list_widget):
        """원본 CMD_ToolSel_b_down."""
        items = self._list_items(list_widget)
        sel_index_1based = [r + 1 for r in self._selected_rows(list_widget)]
        if not sel_index_1based:
            return
        moved_items, result_index = selection_utils.move_down_index(items, sel_index_1based)
        self._set_items(list_widget, moved_items)
        for ri in result_index:
            self._select_row(list_widget, ri)

    @staticmethod
    def _select_row(list_widget, row):
        if 0 <= row < list_widget.count():
            list_widget.item(row).setSelected(True)

    # ================================================================
    # 슬롯 : Match IK and FK
    # ================================================================

    def _checkbox_states(self):
        return [cb.isChecked() for cb in self.checkboxes]

    def on_setup_followers(self):
        """원본 JUN_CR_setUp_followers."""
        self.flw_list.clear()
        for idx, is_checked in enumerate(self._checkbox_states()):
            if is_checked:
                self._append_items(self.flw_list, self.cage.get_rnm_lst(idx))
        self._update_number(self.lbl_flw_num, self.flw_list)

    def on_match(self):
        """원본 JUN_CR_match."""
        mcr = RigMatcher()
        mcr.set_matcher(self._list_items(self.tgt_list), self._list_items(self.flw_list))

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
