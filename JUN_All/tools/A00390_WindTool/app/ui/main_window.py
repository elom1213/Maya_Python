# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-27
# A00390_WindTool - Qt UI
#
# TSL 에 본 체인을 리스트업하고, 회전(또는 이동) 축에 싸인 주기함수 키프레임을 찍어
# '바람에 일렁이는' 애니메이션을 만든다. 구간은 JUN_mod_timeRange_qt(Start/End) 로,
# 주기·진폭·조인트별 offset(실수 프레임) 은 스핀박스로 지정한다.
#   value(t) = amplitude * sin(2*pi*(t - i*offset)/period)  (i = 조인트 순번)
# 키는 1/4 주기마다(0, +A, 0, -A ...) 찍혀 spline 보간으로 싸인 파형이 된다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_timeRange_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00390_WindTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00390_WindTool.app.core import wind_manager as wind_mgr


WINDOW_OBJECT_NAME = "JUN_A00390_WindTool_window"

_WARN_COLOR = "#ffb454"


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Wind Tool v{0}".format(VERSION)
        self.resize(360, 620)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        # 메뉴 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # 본 체인 리스트(TSL). 순서가 offset 순번을 정하므로 Up/Down 으로 재정렬 가능.
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Bone Chain (order = offset step)",
            select_label="Select Joints",
            list_min_height=170, log_callback=self.log)
        root.addWidget(self.tsl, 1)

        # 축(어트리뷰트) 선택
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Axis"))
        self.cmb_axis = QComboBox()
        self.cmb_axis.addItems(wind_mgr.AXES)   # rotateX 기본(첫 항목)
        axis_row.addWidget(self.cmb_axis, 1)
        root.addLayout(axis_row)

        # 시간 구간 (Start / End) - 공용 위젯. 기본값은 현재 playback 범위.
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))
        self.range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        root.addWidget(self.range)

        # 파라미터: 주기 / 진폭 / offset
        form = QFormLayout()

        self.sb_period = QDoubleSpinBox()
        self.sb_period.setDecimals(3)
        self.sb_period.setRange(0.001, 100000.0)
        self.sb_period.setValue(12.0)
        self.sb_period.setToolTip("Frames per full sine cycle (can be fractional).")
        form.addRow("Period (frames)", self.sb_period)

        self.sb_amp = QDoubleSpinBox()
        self.sb_amp.setDecimals(3)
        self.sb_amp.setRange(-100000.0, 100000.0)
        self.sb_amp.setValue(40.0)
        self.sb_amp.setToolTip("Peak value of the sine wave.")
        form.addRow("Amplitude", self.sb_amp)

        self.sb_offset = QDoubleSpinBox()
        self.sb_offset.setDecimals(3)
        self.sb_offset.setRange(-100000.0, 100000.0)
        self.sb_offset.setValue(10.0)
        self.sb_offset.setToolTip(
            "Per-joint phase delay in frames (joint order i -> i*offset).\n"
            "Fractional frames allowed (unlike Stagger's integer offset).")
        form.addRow("Offset / joint (frames)", self.sb_offset)

        root.addLayout(form)

        # 옵션
        self.chk_clear = QCheckBox("Clear existing keys in range")
        self.chk_clear.setChecked(True)
        self.chk_clear.setToolTip(
            "On: remove the axis' keys inside Start~End before writing (clean re-apply).")
        root.addWidget(self.chk_clear)

        self.chk_keep_zero = QCheckBox("Keep zero-crossing keys")
        self.chk_keep_zero.setChecked(False)
        self.chk_keep_zero.setToolTip(
            "Off (default): drop the interior 0-value keys (peaks only) so the\n"
            "spline curve stays smooth; only Start/End keep anchor keys.\n"
            "On: also key every zero crossing (0, +A, 0, -A ...).")
        root.addWidget(self.chk_keep_zero)

        # Apply
        self.btn_apply = QPushButton("Apply Wind Keys")
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.clicked.connect(self.on_apply)
        root.addWidget(self.btn_apply)

        # 로그
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)
        root.addWidget(self.te_log)

        self.log("Wind Tool v{0} ({1}) ready. List a bone chain, set range / "
                 "period / amplitude / offset, then Apply.".format(VERSION, LAST_UPDATE))

    # ==============================================================
    # actions
    # ==============================================================

    def on_apply(self):
        joints = self.tsl.get_all_nodes()   # UUID 로 해석한 현재 경로(리스트업 항목만)
        if not joints:
            self.log("Bone chain list is empty. Select joints and click "
                     "'Select Joints'.", warn=True)
            return

        rng = self.range.values()
        if rng is None:
            self.log("Enter valid Start / End frames.", warn=True)
            return
        start, end = rng

        attr = self.cmb_axis.currentText()
        period = self.sb_period.value()
        amp = self.sb_amp.value()
        offset = self.sb_offset.value()
        clear_range = self.chk_clear.isChecked()
        skip_zero = not self.chk_keep_zero.isChecked()

        try:
            with undo_chunk():
                count, jc, msg = wind_mgr.apply_wind(
                    joints, attr, start, end, period, amp, offset,
                    clear_range=clear_range, skip_zero_crossings=skip_zero)
        except Exception as e:
            self.log("Apply failed: {0}".format(e), warn=True)
            return

        self.log(msg, warn=(count == 0))

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def log(self, text, warn=False):
        if warn:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(_WARN_COLOR, self._esc(text)))
        else:
            self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Wind Tool\nv{0}  ({1})\n\n"
            "Key a bone chain with a sine wave to fake wind sway.\n"
            "value(t) = amplitude * sin(2*pi*(t - i*offset)/period)\n"
            "Keys land every quarter period (fractional frames supported);\n"
            "spline tangents give the sine-like shape. Per-joint offset\n"
            "staggers the chain (fractional frames allowed).\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
