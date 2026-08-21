# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-27
# A00390_WindTool_V02 - Qt UI
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
from tools.A00390_WindTool_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00390_WindTool_V02.app.core import wind_manager as wind_mgr
from tools.A00390_WindTool_V02.app.core import wave_manager as wave_mgr
from tools.A00390_WindTool_V02.app.core import wave_lite_manager as lite_mgr


WINDOW_OBJECT_NAME = "JUN_A00390_WindTool_V02_window"

_WARN_COLOR = "#ffb454"


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Wind Tool v{0}".format(VERSION)
        self.resize(380, 700)

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

        # 조인트 리스트(TSL). Chain 모드에선 순서가 offset 순번을 정하므로 Up/Down 재정렬.
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints",
            select_label="Select Joints",
            list_min_height=170, log_callback=self.log)
        root.addWidget(self.tsl, 1)

        # 대상 해석 모드: Bone Chain / Bone Root
        mode_box = QGroupBox("Mode")
        mode_row = QHBoxLayout(mode_box)
        self.mode_group = QButtonGroup(self)
        self.rb_chain = QRadioButton("Bone Chain")
        self.rb_chain.setChecked(True)
        self.rb_chain.setToolTip(
            "The listed joints are ONE chain; offset applies by list order\n"
            "(reorder with Up/Down).")
        self.rb_root = QRadioButton("Bone Root")
        self.rb_root.setToolTip(
            "Each listed joint is a chain ROOT: the wave runs down that joint\n"
            "and all its descendant joints, offset by depth from the root.")
        self.mode_group.addButton(self.rb_chain)
        self.mode_group.addButton(self.rb_root)
        mode_row.addWidget(self.rb_chain)
        mode_row.addWidget(self.rb_root)
        mode_row.addStretch(1)
        root.addWidget(mode_box)

        # ---- 탭 : Sine(기존) / Chain Wave(신규)
        self.tabs = QTabWidget()

        sine_page = QWidget()
        sine = QVBoxLayout(sine_page)

        # 출력: Curve(키 굽기) / Node(드라이버 노드망 실시간)
        out_box = QGroupBox("Output")
        out_row = QHBoxLayout(out_box)
        self.out_group = QButtonGroup(self)
        self.rb_curve = QRadioButton("Curve")
        self.rb_curve.setChecked(True)
        self.rb_curve.setToolTip(
            "Bake keyframes onto the joints (scene playback plays it). Default.")
        self.rb_node = QRadioButton("Node")
        self.rb_node.setToolTip(
            "Build a null driver with windPeriod / windAmplitude / windOffset /\n"
            "windSpeed attributes that reproduce the animation LIVE (edit the attrs\n"
            "to change it). windSpeed = playback speed (1 = normal); set OR key it to\n"
            "vary the speed per frame - it updates automatically (integrated, no\n"
            "reversal). Bone Chain -> 1 driver; Bone Root -> one driver per root.\n"
            "The driver also carries windEnvelope [0-1]: 0 = the node does nothing,\n"
            "0.5 = half the effect, 1 = full.")
        self.out_group.addButton(self.rb_curve)
        self.out_group.addButton(self.rb_node)
        out_row.addWidget(self.rb_curve)
        out_row.addWidget(self.rb_node)
        out_row.addStretch(1)
        self.rb_curve.toggled.connect(self._on_output_changed)
        sine.addWidget(out_box)

        self.chk_driver_root = QCheckBox("Place driver at chain root (follow)")
        self.chk_driver_root.setChecked(True)
        self.chk_driver_root.setToolTip(
            "Node output only. On (default): each driver locator is created at the\n"
            "world position of the TOP node of the group it drives (the chain root)\n"
            "instead of at the origin, and KEEPS FOLLOWING that world position.\n\n"
            "Position only - rotation is not followed. No constraint is used: the\n"
            "root's worldMatrix goes through multMatrix + decomposeMatrix straight\n"
            "into the locator's translate, so there is no cycle.\n"
            "Its translate is therefore driven and can no longer be moved by hand;\n"
            "it is still only a holder for the wind attributes.")
        sine.addWidget(self.chk_driver_root)

        # 축(어트리뷰트) 선택
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Axis"))
        self.cmb_axis = QComboBox()
        self.cmb_axis.addItems(wind_mgr.AXES)   # rotateX 기본(첫 항목)
        axis_row.addWidget(self.cmb_axis, 1)
        sine.addLayout(axis_row)

        # 시간 구간 (Start / End) - 공용 위젯. 기본값은 현재 playback 범위.
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))
        self.range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        sine.addWidget(self.range)

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

        # Speed: node 모드 드라이버 windSpeed 초기값(재생 속도 배수).
        self.sb_speed = QDoubleSpinBox()
        self.sb_speed.setDecimals(3)
        self.sb_speed.setRange(-1000.0, 1000.0)
        self.sb_speed.setValue(1.0)
        self.sb_speed.setToolTip(
            "Node output only: initial windSpeed value (playback speed).\n"
            "1 = normal, 2 = double, 0 = frozen. Constant value keeps playing.\n"
            "After building, set OR key windSpeed on the driver to change speed -\n"
            "it updates automatically (integrated over time -> no reversal).")
        self.lbl_speed = QLabel("Speed (Node)")
        form.addRow(self.lbl_speed, self.sb_speed)

        # Node Offset: 드라이버(노드)마다 순번 k*값 만큼 전체 타이밍(windPhaseOffset)을 밀어,
        # Bone Root 모드에서 루트들이 서로 다른 타이밍으로 찰랑이게 한다.
        self.sb_node_offset = QDoubleSpinBox()
        self.sb_node_offset.setDecimals(3)
        self.sb_node_offset.setRange(-100000.0, 100000.0)
        self.sb_node_offset.setValue(0.0)
        self.sb_node_offset.setToolTip(
            "Node output only: per-DRIVER timing offset (frames). Driver k gets\n"
            "windPhaseOffset = k * this, so in Bone Root mode each root sways at a\n"
            "different timing. Edit windPhaseOffset on a driver to retime it later.")
        self.lbl_node_offset = QLabel("Node Offset (Node)")
        form.addRow(self.lbl_node_offset, self.sb_node_offset)

        # Envelope: 드라이버 windEnvelope 초기값. 0 = 노드가 아무 영향도 주지 않음.
        self.sb_envelope = QDoubleSpinBox()
        self.sb_envelope.setDecimals(3)
        self.sb_envelope.setRange(0.0, 1.0)
        self.sb_envelope.setSingleStep(0.1)
        self.sb_envelope.setValue(1.0)
        self.sb_envelope.setKeyboardTracking(False)
        self.sb_envelope.setToolTip(
            "Node output only: initial windEnvelope value - how much of the wind\n"
            "the node applies. 0 = nothing at all, 0.5 = half the swing, 1 = full.\n"
            "Set or key windEnvelope on the driver afterwards to fade the wind in\n"
            "and out without touching the amplitude.")
        self.lbl_envelope = QLabel("Envelope (Node)")
        form.addRow(self.lbl_envelope, self.sb_envelope)

        sine.addLayout(form)

        # 옵션
        self.chk_clear = QCheckBox("Clear existing keys in range")
        self.chk_clear.setChecked(True)
        self.chk_clear.setToolTip(
            "On: remove the axis' keys inside Start~End before writing (clean re-apply).")
        sine.addWidget(self.chk_clear)

        self.chk_keep_zero = QCheckBox("Keep zero-crossing keys")
        self.chk_keep_zero.setChecked(False)
        self.chk_keep_zero.setToolTip(
            "Off (default): drop the interior 0-value keys (peaks only) so the\n"
            "spline curve stays smooth; only Start/End keep anchor keys.\n"
            "On: also key every zero crossing (0, +A, 0, -A ...).")
        sine.addWidget(self.chk_keep_zero)

        # Apply (Curve=키 굽기 / Node=드라이버 빌드)
        self.btn_apply = QPushButton("Apply Wind Keys")
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.clicked.connect(self.on_apply)
        sine.addWidget(self.btn_apply)
        sine.addStretch(1)
        self.tabs.addTab(sine_page, "Sine")
        self.tabs.setTabToolTip(
            0, "Sine - drive ONE attribute per joint with a phase-shifted sine.")
        self.tabs.addTab(self._build_wave_tab(), "Chain Wave")
        index = self.tabs.addTab(self._build_lite_tab(), "Chain Wave Lite")
        self.tabs.setTabToolTip(
            index,
            "Same kind of motion with no curve, no ikHandle and no proxy joints.\n"
            "Use this when there are many chains.")
        self.tabs.setTabToolTip(
            1, "Chain Wave - the chain follows a travelling sine wave using "
               "ROTATION ONLY (bone lengths kept, each joint aims at its child).")
        root.addWidget(self.tabs)


        # 로그
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)
        root.addWidget(self.te_log)

        self._on_output_changed()   # 초기 활성/비활성 + 버튼 라벨 맞추기
        self.log("Wind Tool v{0} ({1}) ready. List a bone chain, pick Output "
                 "(Curve / Node), set params, then Apply.".format(VERSION, LAST_UPDATE))


    # ==============================================================
    # Chain Wave 탭
    # ==============================================================

    def _wave_spin(self, value, mn, mx, step, decimals=2):
        sb = QDoubleSpinBox()
        sb.setRange(mn, mx)
        sb.setSingleStep(step)
        sb.setDecimals(decimals)
        sb.setValue(value)
        sb.setKeyboardTracking(False)
        return sb

    def _build_wave_tab(self):
        """체인이 **회전만으로** 진행하는 싸인 파형을 따라가게 한다.

        Sine 탭은 조인트마다 어트리뷰트 하나에 위상만 밀린 싸인을 넣는다. 그래서
        translate 축을 고르면 월드 위치는 파도처럼 보여도 **뼈가 늘었다 줄고 조인트가
        자식을 향하지 않으며**, rotate 축을 고르면 회전이 자손에 누적돼 체인이 말린다.

        이 탭은 마야 기본 **ikSplineSolver** 로 그 문제를 푼다 - 조인트 rest 위치에 CV 를
        둔 커브를 만들고 CV 를 노드망으로 흔들면, 체인이 **회전만으로** 그 커브를 따라간다
        (뼈 길이 유지 · 각 조인트가 자식을 향함 · 루트 고정).
        """
        page = QWidget()
        wave = QVBoxLayout(page)

        note = QLabel(
            "The chain follows a travelling wave using ROTATION ONLY.\n"
            "Bone lengths are kept, each joint aims at its child, the root stays put.")
        note.setWordWrap(True)
        wave.addWidget(note)

        out_box = QGroupBox("Output")
        out_row = QHBoxLayout(out_box)
        self.wave_out_group = QButtonGroup(self)
        self.rb_wave_node = QRadioButton("Node")
        self.rb_wave_node.setChecked(True)
        self.rb_wave_node.setToolTip(
            "Build the live rig (curve + ikSpline + driver locator).\n"
            "Edit windAmplitude / windWavelength / windPeriod / windSpeed /\n"
            "windRootRamp / windEnvelope on the driver and the wave updates\n"
            "immediately.")
        self.rb_wave_curve = QRadioButton("Curve")
        self.rb_wave_curve.setToolTip(
            "Build the rig, bake the joint ROTATIONS over Start/End, then delete\n"
            "the rig - the scene is left with rotation keys only.")
        self.wave_out_group.addButton(self.rb_wave_node)
        self.wave_out_group.addButton(self.rb_wave_curve)
        out_row.addWidget(self.rb_wave_node)
        out_row.addWidget(self.rb_wave_curve)
        out_row.addStretch(1)
        self.rb_wave_curve.toggled.connect(self._on_wave_output_changed)
        wave.addWidget(out_box)

        self.chk_wave_driver_root = QCheckBox("Place driver at chain root (follow)")
        self.chk_wave_driver_root.setChecked(True)
        self.chk_wave_driver_root.setToolTip(
            "Node output only. On (default): the driver locator is created at the\n"
            "world position of the TOP node of that chain instead of at the origin,\n"
            "and KEEPS FOLLOWING that world position.\n\n"
            "Position only - rotation is not followed. No constraint is used: the\n"
            "root's worldMatrix goes through multMatrix + decomposeMatrix straight\n"
            "into the locator's translate, so there is no cycle.\n"
            "Its translate is therefore driven and can no longer be moved by hand;\n"
            "it is still only a holder for the wind attributes.")
        wave.addWidget(self.chk_wave_driver_root)

        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Sway Axis (world)"))
        self.cmb_wave_axis = QComboBox()
        self.cmb_wave_axis.addItems(wave_mgr.UP_AXES)
        self.cmb_wave_axis.setCurrentText("Y")
        self.cmb_wave_axis.setToolTip(
            "Which WORLD axis the wave pushes the chain along.\n"
            "A chain lying along X with Y up normally sways in Y.")
        axis_row.addWidget(self.cmb_wave_axis, 1)
        wave.addLayout(axis_row)

        self.wave_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=int(cmds.playbackOptions(query=True, minTime=True)),
            end_value=int(cmds.playbackOptions(query=True, maxTime=True)),
            log_callback=self.log)
        wave.addWidget(self.wave_range)

        grid = QGridLayout()
        self.sb_wave_amp = self._wave_spin(1.0, 0.0, 100000.0, 0.1)
        self.sb_wave_amp.setToolTip(
            "How far the wave pushes the curve, in WORLD units.\n"
            "The visible sway is a little smaller - a degree-3 curve does not pass\n"
            "through its control points. Too large for the wavelength and the curve\n"
            "gets longer than the chain, so the tip cannot reach the end.")
        self.sb_wave_len = self._wave_spin(10.0, 0.001, 100000.0, 1.0)
        self.sb_wave_len.setToolTip(
            "Length of ONE wave along the chain, in WORLD units.")
        self.sb_wave_period = self._wave_spin(24.0, 0.001, 100000.0, 1.0)
        self.sb_wave_period.setToolTip("Frames for one cycle to pass.")
        self.sb_wave_speed = self._wave_spin(1.0, -100.0, 100.0, 0.1)
        self.sb_wave_speed.setToolTip(
            "Playback speed (1 = normal). Set or key windSpeed on the driver later;\n"
            "it is integrated over time so the phase never runs backwards.")
        self.sb_wave_ramp = self._wave_spin(1.0, 0.0, 1.0, 0.1)
        self.sb_wave_ramp.setToolTip(
            "0 = the same amplitude all the way from the root.\n"
            "1 = starts at zero on the root and grows toward the tip (default).")
        self.sb_wave_node_offset = self._wave_spin(0.0, -100000.0, 100000.0, 1.0)
        self.sb_wave_node_offset.setToolTip(
            "Per-CHAIN timing offset (frames). Chain k starts with\n"
            "windPhaseOffset = k * this, so in Bone Root mode each chain sways\n"
            "at its own time.")
        self.sb_wave_envelope = self._wave_spin(1.0, 0.0, 1.0, 0.1, decimals=3)
        self.sb_wave_envelope.setToolTip(
            "How much of the wave the driver applies - windEnvelope on the driver.\n"
            "0 = nothing at all (the chain stays at rest), 0.5 = half, 1 = full.\n"
            "Set or key windEnvelope afterwards to fade the wave in and out\n"
            "without touching the amplitude.")
        rows = (("Amplitude", self.sb_wave_amp),
                ("Wavelength", self.sb_wave_len),
                ("Period", self.sb_wave_period),
                ("Speed", self.sb_wave_speed),
                ("Root Ramp", self.sb_wave_ramp),
                ("Envelope", self.sb_wave_envelope),
                ("Chain Offset", self.sb_wave_node_offset))
        for r, (label, widget) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            grid.addWidget(widget, r, 1)
        wave.addLayout(grid)

        self.btn_wave_apply = QPushButton("Build Chain Wave")
        self.btn_wave_apply.setMinimumHeight(38)
        self.btn_wave_apply.clicked.connect(self.on_wave_apply)
        wave.addWidget(self.btn_wave_apply)

        self.btn_wave_remove = QPushButton("Remove Chain Wave")
        self.btn_wave_remove.setToolTip(
            "Delete the rig this tab built (curve, ikSpline, driver, node network)\n"
            "and reset the joint rotations. Baked keys are not touched.")
        self.btn_wave_remove.clicked.connect(self.on_wave_remove)
        wave.addWidget(self.btn_wave_remove)

        wave.addStretch(1)
        self._on_wave_output_changed()
        return page

    def _on_wave_output_changed(self, *args):
        node = self.rb_wave_node.isChecked()
        self.wave_range.setEnabled(not node)
        self.chk_wave_driver_root.setEnabled(node)
        self.btn_wave_apply.setText(
            "Build Chain Wave" if node else "Bake Chain Wave")

    def on_wave_apply(self):
        joints = self.tsl.get_all_nodes()
        if not joints:
            self.log("Joint list is empty. Select joints and click "
                     "'Select Joints'.", warn=True)
            return

        mode = wind_mgr.MODE_ROOT if self.rb_root.isChecked() else wind_mgr.MODE_CHAIN
        node = self.rb_wave_node.isChecked()
        rng = self.wave_range.values()
        if not node and rng is None:
            self.log("Enter Start / End for the bake.", warn=True)
            return
        start, end = rng if rng else (0.0, 0.0)

        with undo_chunk():
            try:
                chains, drivers, msg = wave_mgr.build_wave(
                    joints, mode=mode, axis=self.cmb_wave_axis.currentText(),
                    amplitude=self.sb_wave_amp.value(),
                    wavelength=self.sb_wave_len.value(),
                    period=self.sb_wave_period.value(),
                    speed=self.sb_wave_speed.value(),
                    ramp=self.sb_wave_ramp.value(),
                    node_offset=self.sb_wave_node_offset.value(),
                    envelope=self.sb_wave_envelope.value(),
                    driver_at_root=self.chk_wave_driver_root.isChecked(),
                    output=(wind_mgr.OUTPUT_NODE if node
                            else wind_mgr.OUTPUT_CURVE),
                    start=start, end=end)
            except Exception as exc:                      # noqa: BLE001
                self.log("[Error] {0}".format(exc), warn=True)
                cmds.warning(str(exc))
                return
        self.log(msg, warn=msg.startswith("[Warning]"))

    def on_wave_remove(self):
        with undo_chunk():
            try:
                count, msg = wave_mgr.remove_wave()
            except Exception as exc:                      # noqa: BLE001
                self.log("[Error] {0}".format(exc), warn=True)
                return
        self.log(msg, warn=msg.startswith("[Warning]"))


    # ==============================================================
    # Chain Wave Lite
    # ==============================================================

    def _build_lite_tab(self):
        """커브·ikHandle·프록시 없이 **각도만으로** 같은 종류의 파형을 만든다.

        Chain Wave 탭은 체인마다 커브 + ikSpline + 프록시 조인트를 만든다. 옳은 방법이지만
        실측으로 **체인당 141 노드**(조인트 9개 기준)라 루트가 100 개면 14,000 노드가 된다.

        이 탭은 정의를 바꾼다 — "뼈의 월드 방향각이 싸인파를 그린다". 그래서 진폭이
        **거리가 아니라 각도(도)** 이고, 커브·IK·프록시가 하나도 생기지 않는다.
        같은 체인에서 141 -> 95 노드였고, 커브/ikHandle/프록시는 0 이다.
        """
        page = QWidget()
        lite = QVBoxLayout(page)

        note = QLabel(
            "Same kind of motion as Chain Wave, but with NO ikHandle and NO proxy\n"
            "joints - the bone angle itself is the sine wave.\n"
            "Amplitude is an ANGLE here, so the numbers are not interchangeable\n"
            "with the Chain Wave tab. Match it by eye.\n"
            "Debug Curve draws the result; it drives nothing and can be turned off.")
        note.setWordWrap(True)
        lite.addWidget(note)

        out_box = QGroupBox("Output")
        out_row = QHBoxLayout(out_box)
        self.lite_out_group = QButtonGroup(self)
        self.rb_lite_node = QRadioButton("Node")
        self.rb_lite_node.setChecked(True)
        self.rb_lite_node.setToolTip(
            "Build the live node network (driver locator + per-joint nodes).\n"
            "Edit windSwingAngle / windWavelength / windPeriod / windSpeed /\n"
            "windRootRamp / windEnvelope on the driver and the wave updates\n"
            "immediately.")
        self.rb_lite_curve = QRadioButton("Curve")
        self.rb_lite_curve.setToolTip(
            "Build it, bake the ROTATIONS over Start/End, then delete the setup -\n"
            "the scene is left with rotation keys only (nothing live at all).")
        self.lite_out_group.addButton(self.rb_lite_node)
        self.lite_out_group.addButton(self.rb_lite_curve)
        out_row.addWidget(self.rb_lite_node)
        out_row.addWidget(self.rb_lite_curve)
        out_row.addStretch(1)
        self.rb_lite_curve.toggled.connect(self._on_lite_output_changed)
        lite.addWidget(out_box)

        self.chk_lite_driver_root = QCheckBox("Place driver at chain root (follow)")
        self.chk_lite_driver_root.setChecked(True)
        self.chk_lite_driver_root.setToolTip(
            "Node output only. On (default): the driver locator is created at the\n"
            "world position of the TOP node of that chain, so it sits on the bone /\n"
            "controller it drives instead of at the origin, and KEEPS FOLLOWING\n"
            "that world position - move the root bone / root controller / the whole\n"
            "rig and the locator goes with it.\n\n"
            "Position only - rotation is not followed. No constraint is used: the\n"
            "root's worldMatrix goes through multMatrix + decomposeMatrix straight\n"
            "into the locator's translate, so there is no cycle.\n"
            "Its translate is therefore driven and can no longer be moved by hand;\n"
            "it is still only a holder for the wind attributes.\n\n"
            "Off: the locator is left at the origin and does not follow (the old\n"
            "behaviour).")
        lite.addWidget(self.chk_lite_driver_root)

        axis_row = QHBoxLayout()
        self.lbl_lite_sway = QLabel("Sway Axis (world)")
        axis_row.addWidget(self.lbl_lite_sway)
        self.cmb_lite_axis = QComboBox()
        self.cmb_lite_axis.addItems(wave_mgr.UP_AXES)
        self.cmb_lite_axis.setCurrentText("Y")
        self.cmb_lite_axis.setToolTip(
            "Which WORLD axis the chain sways along.\n"
            "The rotation axis is worked out from the chain direction and this axis,\n"
            "so joint orientation and rotate order do not matter.\n"
            "Ignored while 'Rotate Axis (object)' below is on.")
        axis_row.addWidget(self.cmb_lite_axis, 1)
        lite.addLayout(axis_row)

        # 오브젝트 공간 축으로만 돌리기. 켜면 위의 Sway Axis 는 계산에 전혀 들어가지 않는다.
        local_row = QHBoxLayout()
        self.chk_lite_local = QCheckBox("Rotate Axis (object)")
        self.chk_lite_local.setToolTip(
            "On: every node rotates about ONE of its OWN axes only - the wave is\n"
            "written straight into that rotate channel (rotateX / rotateY / rotateZ)\n"
            "and the other two channels are left untouched.\n"
            "Sway Axis (world) above is IGNORED while this is on.\n\n"
            "Off (default): the rotation axis is derived from the chain direction and\n"
            "the world Sway Axis, so the result is the same in world space whatever\n"
            "the joint orientation is.\n\n"
            "Use this when the rig is meant to bend on one specific local axis.\n"
            "It assumes the chain nodes share an orientation (a normal FK / joint\n"
            "chain does); on a chain whose nodes are oriented every which way the\n"
            "bones swing on their own axes instead of forming one wave.")
        self.chk_lite_local.toggled.connect(self._on_lite_axis_mode_changed)
        local_row.addWidget(self.chk_lite_local)

        self.cmb_lite_local_axis = QComboBox()
        self.cmb_lite_local_axis.addItems(lite_mgr.LOCAL_AXES)
        self.cmb_lite_local_axis.setCurrentText("Z")
        self.cmb_lite_local_axis.setToolTip(
            "Which rotate channel of each node carries the wave (object space).")
        local_row.addWidget(self.cmb_lite_local_axis, 1)
        lite.addLayout(local_row)

        self.lite_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=int(cmds.playbackOptions(query=True, minTime=True)),
            end_value=int(cmds.playbackOptions(query=True, maxTime=True)),
            log_callback=self.log)
        lite.addWidget(self.lite_range)

        grid = QGridLayout()
        self.sb_lite_swing = self._wave_spin(20.0, 0.0, 360.0, 1.0)
        self.sb_lite_swing.setToolTip(
            "How far a bone swings, in DEGREES of world angle.\n"
            "20 means the tip bone leans up to 20 degrees each way.\n"
            "This is NOT the Chain Wave amplitude (which is a distance).")
        self.sb_lite_len = self._wave_spin(10.0, 0.001, 100000.0, 1.0)
        self.sb_lite_len.setToolTip(
            "Length of ONE wave along the chain, in WORLD units.")
        self.sb_lite_period = self._wave_spin(24.0, 0.001, 100000.0, 1.0)
        self.sb_lite_period.setToolTip("Frames for one cycle to pass.")
        self.sb_lite_speed = self._wave_spin(1.0, -100.0, 100.0, 0.1)
        self.sb_lite_speed.setToolTip(
            "Playback speed (1 = normal). Integrated over time, so the phase never\n"
            "runs backwards when you key it.")
        self.sb_lite_ramp = self._wave_spin(1.0, 0.0, 1.0, 0.1)
        self.sb_lite_ramp.setToolTip(
            "0 = every bone swings the same, the root included.\n"
            "1 = the root does not move and the swing grows toward the tip (default).")
        self.sb_lite_node_offset = self._wave_spin(0.0, -100000.0, 100000.0, 1.0)
        self.sb_lite_node_offset.setToolTip(
            "Per-CHAIN timing offset (frames). Chain k starts with\n"
            "windPhaseOffset = k * this, so many chains do not move in lockstep.")
        self.sb_lite_envelope = self._wave_spin(1.0, 0.0, 1.0, 0.1, decimals=3)
        self.sb_lite_envelope.setToolTip(
            "How much of the swing the driver applies - windEnvelope on the driver.\n"
            "0 = nothing at all (the chain stays at rest), 0.5 = half, 1 = full.\n"
            "Set or key windEnvelope afterwards to fade the wind in and out\n"
            "without touching the swing angle.")

        rows = (("Swing Angle", self.sb_lite_swing),
                ("Wavelength", self.sb_lite_len),
                ("Period", self.sb_lite_period),
                ("Speed", self.sb_lite_speed),
                ("Root Ramp", self.sb_lite_ramp),
                ("Envelope", self.sb_lite_envelope),
                ("Chain Offset", self.sb_lite_node_offset))
        for r, (label, widget) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            grid.addWidget(widget, r, 1)
        lite.addLayout(grid)

        # 흔들림을 눈으로 확인하는 커브. Chain Wave 탭이 만드는 커브와 같은 방식이지만
        # 구동 방향이 반대라(체인 -> 커브) 실제 결과를 그린다. 아무것도 구동하지 않는다.
        self.chk_lite_debug = QCheckBox("Debug Curve")
        self.chk_lite_debug.setChecked(True)
        self.chk_lite_debug.setToolTip(
            "On (default): draw one curve per chain showing how it sways.\n"
            "It is built the same way as the Chain Wave tab's curve - a degree 3\n"
            "NURBS with one CV per chain node - but it is DRIVEN BY the chain\n"
            "instead of driving it, so it always sits exactly on the result.\n\n"
            "Display only: it moves nothing, it is set to reference so it cannot be\n"
            "picked in the viewport, and Remove Chain Wave Lite deletes it with the\n"
            "rest of the setup.\n\n"
            "The curves are collected in their own '*_liteCurveGrp' group, separate\n"
            "from the driver locators in '*_liteDriverGrp', so the outliner does not\n"
            "alternate locator / curve / locator / curve.")
        lite.addWidget(self.chk_lite_debug)

        self.btn_lite_apply = QPushButton("Build Chain Wave Lite")
        self.btn_lite_apply.setMinimumHeight(38)
        self.btn_lite_apply.clicked.connect(self.on_lite_apply)
        lite.addWidget(self.btn_lite_apply)

        self.btn_lite_remove = QPushButton("Remove Chain Wave Lite")
        self.btn_lite_remove.setToolTip(
            "Delete what this tab built and put the rotations back to their rest\n"
            "values. Baked keys are not touched, and the Chain Wave tab's rigs\n"
            "are left alone.")
        self.btn_lite_remove.clicked.connect(self.on_lite_remove)
        lite.addWidget(self.btn_lite_remove)

        lite.addStretch(1)
        self._on_lite_output_changed()
        self._on_lite_axis_mode_changed()
        return page

    def _on_lite_output_changed(self, *args):
        node = self.rb_lite_node.isChecked()
        self.lite_range.setEnabled(not node)
        # 드라이버 위치는 node 출력에만 의미가 있다(curve 는 구운 뒤 셋업을 지운다).
        self.chk_lite_driver_root.setEnabled(node)
        self.btn_lite_apply.setText(
            "Build Chain Wave Lite" if node else "Bake Chain Wave Lite")

    def _on_lite_axis_mode_changed(self, *args):
        """오브젝트 축 모드면 Sway Axis 를 통째로 비활성화한다(계산에도 안 들어간다)."""
        local = self.chk_lite_local.isChecked()
        self.lbl_lite_sway.setEnabled(not local)
        self.cmb_lite_axis.setEnabled(not local)
        self.cmb_lite_local_axis.setEnabled(local)

    def on_lite_apply(self):
        joints = self.tsl.get_all_nodes()
        if not joints:
            self.log("Joint list is empty. Select joints and click "
                     "'Select Joints'.", warn=True)
            return

        mode = wind_mgr.MODE_ROOT if self.rb_root.isChecked() else wind_mgr.MODE_CHAIN
        node = self.rb_lite_node.isChecked()
        rng = self.lite_range.values()
        if not node and rng is None:
            self.log("Enter Start / End for the bake.", warn=True)
            return
        start, end = rng if rng else (0.0, 0.0)

        with undo_chunk():
            try:
                chains, drivers, msg = lite_mgr.build_wave_lite(
                    joints, mode=mode, axis=self.cmb_lite_axis.currentText(),
                    swing=self.sb_lite_swing.value(),
                    wavelength=self.sb_lite_len.value(),
                    period=self.sb_lite_period.value(),
                    speed=self.sb_lite_speed.value(),
                    ramp=self.sb_lite_ramp.value(),
                    node_offset=self.sb_lite_node_offset.value(),
                    envelope=self.sb_lite_envelope.value(),
                    local_axis=(self.cmb_lite_local_axis.currentText()
                                if self.chk_lite_local.isChecked() else None),
                    driver_at_root=self.chk_lite_driver_root.isChecked(),
                    debug_curve=self.chk_lite_debug.isChecked(),
                    output=(wind_mgr.OUTPUT_NODE if node
                            else wind_mgr.OUTPUT_CURVE),
                    start=start, end=end)
            except Exception as exc:                      # noqa: BLE001
                self.log("[Error] {0}".format(exc), warn=True)
                cmds.warning(str(exc))
                return
        self.log(msg, warn=msg.startswith("[Warning]"))

    def on_lite_remove(self):
        with undo_chunk():
            try:
                count, msg = lite_mgr.remove_wave_lite()
            except Exception as exc:                      # noqa: BLE001
                self.log("[Error] {0}".format(exc), warn=True)
                return
        self.log(msg, warn=msg.startswith("[Warning]"))

    # ==============================================================
    # output mode toggle
    # ==============================================================

    def _on_output_changed(self, *args):
        """Curve/Node 전환 시 관련 없는 위젯을 비활성화하고 버튼 라벨을 바꾼다."""
        curve = self.rb_curve.isChecked()
        # 구간·clear·keep-zero 는 curve 전용, speed 는 node 전용.
        self.range.setEnabled(curve)
        self.chk_clear.setEnabled(curve)
        self.chk_keep_zero.setEnabled(curve)
        self.sb_speed.setEnabled(not curve)
        self.lbl_speed.setEnabled(not curve)
        self.sb_node_offset.setEnabled(not curve)
        self.lbl_node_offset.setEnabled(not curve)
        self.sb_envelope.setEnabled(not curve)
        self.lbl_envelope.setEnabled(not curve)
        self.chk_driver_root.setEnabled(not curve)
        self.btn_apply.setText("Apply Wind Keys" if curve else "Build Wind Node")

    # ==============================================================
    # actions
    # ==============================================================

    def on_apply(self):
        joints = self.tsl.get_all_nodes()   # UUID 로 해석한 현재 경로(리스트업 항목만)
        if not joints:
            self.log("Joint list is empty. Select joints and click "
                     "'Select Joints'.", warn=True)
            return

        node_mode = self.rb_node.isChecked()

        # 구간은 curve 모드에서만 필요(node 는 전체 타임라인을 실시간 구동).
        if node_mode:
            start, end = 0, 0
        else:
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
        mode = wind_mgr.MODE_ROOT if self.rb_root.isChecked() else wind_mgr.MODE_CHAIN
        output = wind_mgr.OUTPUT_NODE if node_mode else wind_mgr.OUTPUT_CURVE
        speed = self.sb_speed.value()
        node_offset = self.sb_node_offset.value()
        envelope = self.sb_envelope.value()

        try:
            with undo_chunk():
                count, jc, msg = wind_mgr.apply_wind(
                    joints, attr, start, end, period, amp, offset,
                    clear_range=clear_range, skip_zero_crossings=skip_zero,
                    mode=mode, output=output, speed=speed, node_offset=node_offset,
                    envelope=envelope,
                    driver_at_root=self.chk_driver_root.isChecked())
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
            "Drive a bone chain with a sine wave to fake wind sway.\n"
            "value(t) = amplitude * sin(2*pi*(t - i*offset)/period)\n\n"
            "Output = Curve: bake keyframes (fractional-frame keys, spline).\n"
            "Output = Node: a null driver (windPeriod/Amplitude/Offset/Speed)\n"
            "reproduces it live; windSpeed = playback speed (set or key it, auto).\n"
            "Every driver also carries windEnvelope [0-1] - 0 = the node has no\n"
            "effect, 0.5 = half, 1 = full. Set or key it to fade the wind in/out.\n"
            "Bone Chain -> 1 driver; Bone Root -> one driver per root.\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
