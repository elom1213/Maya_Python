# -*- coding: utf-8 -*-
"""
FKIK General Tool - PySide(Qt) UI.

레거시 maya.cmds UI(JUN_PY_FKIK_General_Tool_V01_02.py: PY_JUN_makeUI_general_FKIKTool)를
PySide 로 리팩토링한 버전. 로직(app/core)은 UI 와 분리하고, 화면만 Qt 로 구성한다.
Framework.qt.qt 가 PySide6 -> PySide2 폴백을 처리하므로 Maya 2023(PySide2)~최신 호환.

UI 문자열/로그는 영어. 핸들러는 위젯에서 list[str] 를 뽑아 core 함수에 넘기고,
결과 list 를 위젯에 되돌린다(위젯<->리스트 변환은 UI 책임).
"""

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

from ..config.version import VERSION, LAST_UPDATE
from ..core import matching
from ..core import driver_setup
from ..core import settings_io

from .limb_list_group import TslListGroup


WINDOW_OBJECT_NAME = "JUN_A00190_FKIK_General_window"

# limb 순서: [arm_left, arm_right, leg_left, leg_right]
_LIMB_LABELS = ["Arm Left", "Arm Right", "Leg Left", "Leg Right"]


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("FKIK General Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(760, 1000)

        # slot_id -> tsl 위젯 (모든 그룹에서 집계)
        self.tsl = {}

        # 드라이버 묶음: 'Set up triangle' 와 'Drivers for FK IK switch' 사이에서 공유.
        self.cage = driver_setup.Cage()

        self._build_ui()

    # ==================================================================
    # UI 구성
    # ==================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.setMenuBar(self._build_menu_bar())

        tabs = QTabWidget()
        tabs.addTab(self._build_source_tab(), "Source")
        tabs.addTab(self._build_match_tab("mfk"), "Match FK")
        tabs.addTab(self._build_match_tab("mik"), "Match IK")
        root.addWidget(tabs, 1)

        root.addWidget(self._build_option_panel())

        # 로그
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(90)
        root.addWidget(self.log_view)

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

    def _build_menu_bar(self):
        bar = QMenuBar()
        help_menu = bar.addMenu("Help")
        help_menu.addAction("About", self.show_about)
        return bar

    def _register(self, group):
        """그룹의 tsl 위젯들을 self.tsl 에 등록하고 그룹을 반환."""
        self.tsl.update(group.all_widgets())
        return group

    def _build_source_tab(self):
        page = QWidget()
        col = QVBoxLayout(page)

        fk_specs = [("src_fk_arm_l", "Arm Left"), ("src_fk_arm_r", "Arm Right"),
                    ("src_fk_leg_l", "Leg Left"), ("src_fk_leg_r", "Leg Right")]
        ik_specs = [("src_ik_arm_l", "Arm Left"), ("src_ik_arm_r", "Arm Right"),
                    ("src_ik_leg_l", "Leg Left"), ("src_ik_leg_r", "Leg Right")]

        col.addWidget(self._register(TslListGroup("Set Source : FK", fk_specs, self._log)))
        col.addWidget(self._register(TslListGroup("Set Source : IK", ik_specs, self._log)))
        col.addStretch(1)
        return page

    def _build_match_tab(self, prefix):
        """prefix 'mfk' 또는 'mik'. limb 별 (pose, ctl) tsl 2개씩, 팔/다리 두 행."""
        page = QWidget()
        col = QVBoxLayout(page)

        arm_specs = [
            ("{0}_arm_l_pose".format(prefix), "Arm L pose"),
            ("{0}_arm_l_ctl".format(prefix), "Arm L ctl"),
            ("{0}_arm_r_pose".format(prefix), "Arm R pose"),
            ("{0}_arm_r_ctl".format(prefix), "Arm R ctl"),
        ]
        leg_specs = [
            ("{0}_leg_l_pose".format(prefix), "Leg L pose"),
            ("{0}_leg_l_ctl".format(prefix), "Leg L ctl"),
            ("{0}_leg_r_pose".format(prefix), "Leg R pose"),
            ("{0}_leg_r_ctl".format(prefix), "Leg R ctl"),
        ]

        col.addWidget(self._register(TslListGroup("Arm", arm_specs, self._log)))
        col.addWidget(self._register(TslListGroup("Leg", leg_specs, self._log)))
        col.addStretch(1)
        return page

    def _build_option_panel(self):
        box = QGroupBox("Option")
        outer = QVBoxLayout(box)

        # --- limb 체크박스 ---
        cb_row = QHBoxLayout()
        self.cb_arm_l = QCheckBox("Arm Left")
        self.cb_arm_r = QCheckBox("Arm Right")
        self.cb_leg_l = QCheckBox("Leg Left")
        self.cb_leg_r = QCheckBox("Leg Right")
        for cb in (self.cb_arm_l, self.cb_arm_r, self.cb_leg_l, self.cb_leg_r):
            cb.setChecked(True)
            cb_row.addWidget(cb)
        cb_row.addStretch(1)
        outer.addLayout(cb_row)

        # --- Start / End frame ---
        frame_row = QHBoxLayout()
        frame_row.addWidget(QLabel("Start Frame"))
        self.spin_start = QSpinBox()
        self.spin_start.setRange(-100000, 100000)
        frame_row.addWidget(self.spin_start)
        frame_row.addWidget(QLabel("End Frame"))
        self.spin_end = QSpinBox()
        self.spin_end.setRange(-100000, 100000)
        frame_row.addWidget(self.spin_end)
        frame_row.addStretch(1)
        outer.addLayout(frame_row)
        self._init_frame_range()

        # --- 셋업 버튼 ---
        setup_row = QHBoxLayout()
        btn_tri = QPushButton("Set up triangle drivers")
        btn_tri.clicked.connect(self.on_setup_triangle)
        setup_row.addWidget(btn_tri)
        btn_switch = QPushButton("Drivers for FK IK switch")
        btn_switch.clicked.connect(self.on_setup_switch)
        setup_row.addWidget(btn_switch)
        btn_load = QPushButton("Load setting")
        btn_load.clicked.connect(self.on_load_setting)
        setup_row.addWidget(btn_load)
        btn_save = QPushButton("Save setting")
        btn_save.clicked.connect(self.on_save_setting)
        setup_row.addWidget(btn_save)
        outer.addLayout(setup_row)

        # --- 매칭 / 베이크 버튼 ---
        action_row = QHBoxLayout()
        btn_match_ik = QPushButton("Match IK")
        btn_match_ik.clicked.connect(lambda: self.on_match(use_ik=True))
        action_row.addWidget(btn_match_ik)
        btn_match_fk = QPushButton("Match FK")
        btn_match_fk.clicked.connect(lambda: self.on_match(use_ik=False))
        action_row.addWidget(btn_match_fk)
        btn_bake_ik = QPushButton("Bake IK")
        btn_bake_ik.clicked.connect(lambda: self.on_bake(use_ik=True))
        action_row.addWidget(btn_bake_ik)
        btn_bake_fk = QPushButton("Bake FK")
        btn_bake_fk.clicked.connect(lambda: self.on_bake(use_ik=False))
        action_row.addWidget(btn_bake_fk)
        outer.addLayout(action_row)

        return box

    def _init_frame_range(self):
        try:
            start = int(cmds.playbackOptions(query=True, minTime=True))
            end = int(cmds.playbackOptions(query=True, maxTime=True))
        except Exception:
            start, end = 0, 100
        self.spin_start.setValue(start)
        self.spin_end.setValue(end)

    # ==================================================================
    # 로그
    # ==================================================================

    def _log(self, message):
        self.log_view.appendPlainText(str(message))

    def _warn(self, message):
        cmds.warning(message)
        self._log("[WARN] " + str(message))

    # ==================================================================
    # 위젯 <-> 리스트 헬퍼
    # ==================================================================

    def _items(self, slot_id):
        return self.tsl[slot_id].get_all_items()

    def _set(self, slot_id, items):
        self.tsl[slot_id].set_items(items)

    def _enabled_limbs(self):
        return [self.cb_arm_l.isChecked(), self.cb_arm_r.isChecked(),
                self.cb_leg_l.isChecked(), self.cb_leg_r.isChecked()]

    def _fk_source_lists(self):
        return [self._items("src_fk_arm_l"), self._items("src_fk_arm_r"),
                self._items("src_fk_leg_l"), self._items("src_fk_leg_r")]

    def _ik_source_lists(self):
        return [self._items("src_ik_arm_l"), self._items("src_ik_arm_r"),
                self._items("src_ik_leg_l"), self._items("src_ik_leg_r")]

    def _ctl_lists(self, prefix):
        return [self._items("{0}_arm_l_ctl".format(prefix)),
                self._items("{0}_arm_r_ctl".format(prefix)),
                self._items("{0}_leg_l_ctl".format(prefix)),
                self._items("{0}_leg_r_ctl".format(prefix))]

    def _pairs(self, prefix):
        """limb 4개의 (pose_objs, ctls) 튜플 리스트."""
        limbs = ["arm_l", "arm_r", "leg_l", "leg_r"]
        return [(self._items("{0}_{1}_pose".format(prefix, lb)),
                 self._items("{0}_{1}_ctl".format(prefix, lb))) for lb in limbs]

    # ==================================================================
    # 슬롯 : 드라이버 셋업
    # ==================================================================

    def on_setup_triangle(self):
        cmds.undoInfo(openChunk=True)
        try:
            driver_setup.setup_triangle_drivers(self._fk_source_lists(), self.cage)
            self._log("Triangle drivers set up.")
        except Exception as exc:
            self._warn("Set up triangle drivers failed: {0}".format(exc))
        finally:
            cmds.undoInfo(closeChunk=True)

    def on_setup_switch(self):
        cmds.undoInfo(openChunk=True)
        try:
            fk_pose, ik_pose = driver_setup.create_switch_drivers(
                self._ik_source_lists(), self._ctl_lists("mfk"), self._ctl_lists("mik"), self.cage)

            limbs = ["arm_l", "arm_r", "leg_l", "leg_r"]
            for i, lb in enumerate(limbs):
                self._set("mfk_{0}_pose".format(lb), fk_pose[i])
                self._set("mik_{0}_pose".format(lb), ik_pose[i])

            self._log("FK/IK switch drivers created.")
        except Exception as exc:
            self._warn("Drivers for FK IK switch failed: {0}".format(exc))
        finally:
            cmds.undoInfo(closeChunk=True)

    # ==================================================================
    # 슬롯 : 매칭 / 베이크
    # ==================================================================

    def on_match(self, use_ik):
        side = "IK" if use_ik else "FK"
        cmds.undoInfo(openChunk=True)
        try:
            n = matching.run_match_bake(
                self._pairs("mfk"), self._pairs("mik"),
                self._enabled_limbs(), use_ik, frame_range=None)
            self._log("Match {0}: {1} control(s) matched at current frame.".format(side, n))
        except Exception as exc:
            self._warn("Match {0} failed: {1}".format(side, exc))
        finally:
            cmds.undoInfo(closeChunk=True)

    def on_bake(self, use_ik):
        side = "IK" if use_ik else "FK"
        start = self.spin_start.value()
        end = self.spin_end.value()
        if end < start:
            self._warn("End frame is before start frame.")
            return
        cmds.undoInfo(openChunk=True)
        try:
            n = matching.run_match_bake(
                self._pairs("mfk"), self._pairs("mik"),
                self._enabled_limbs(), use_ik, frame_range=(start, end))
            self._log("Bake {0}: {1} control(s) baked over {2}-{3}.".format(side, n, start, end))
        except Exception as exc:
            self._warn("Bake {0} failed: {1}".format(side, exc))
        finally:
            cmds.undoInfo(closeChunk=True)

    # ==================================================================
    # 슬롯 : 세팅 저장 / 로드
    # ==================================================================

    def on_save_setting(self):
        path = settings_io.browse_path(save=True)
        if not path:
            return
        data = {slot: widget.get_all_items() for slot, widget in self.tsl.items()}
        try:
            settings_io.save_settings(data, path)
            self._log("Setting saved: {0}".format(path))
        except Exception as exc:
            self._warn("Save setting failed: {0}".format(exc))

    def on_load_setting(self):
        path = settings_io.browse_path(save=False)
        if not path:
            return
        try:
            data = settings_io.load_settings(path)
        except Exception as exc:
            self._warn("Load setting failed: {0}".format(exc))
            return
        applied = 0
        for slot, items in data.items():
            if slot in self.tsl:
                self._set(slot, items)
                applied += 1
        self._log("Setting loaded ({0} list(s) restored): {1}".format(applied, path))

    # ==================================================================
    # Help
    # ==================================================================

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "FKIK General Tool v{0}  (PySide)\n"
            "Update date: {1}\n\n"
            "Match and bake FK/IK poses for character rigs.\n"
            "Collect controls per limb, set up driver pose objects,\n"
            "then Match (current frame) or Bake (frame range).\n\n"
            "Refactor of the legacy maya.cmds tool. Written by Ji Hun Park.".format(
                VERSION, LAST_UPDATE))
