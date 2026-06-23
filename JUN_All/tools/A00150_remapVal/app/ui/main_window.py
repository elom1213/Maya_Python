# -*- coding: utf-8 -*-
"""
Remap Value (slerp ramp) Tool - PySide(Qt) UI.

sample_01.py 의 build_slerp_ramp(prefix, controlObj, oColl, twistAttrs) 를 GUI 로 감싼다.
  - Main Controller : controlObj  (QLineEdit + Get, A00090 패턴)
  - Joints          : oColl        (재사용 위젯 JUN_mod_tsl_qt_v01)
  - Attributes      : twistAttrs   (재사용 위젯 + List Attributes + Search, numberTool 패턴)
  - Prefix          : 첫 인자 문자열 (QLineEdit)

로직은 app/core 에 위임한다. UI 보조는 maya.cmds(MayaScene), 노드 생성 본체는 pymel(core).
모든 UI 문자열/로그는 영어.
"""

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

from tools.A00150_remapVal.app.config.version import VERSION, LAST_UPDATE
from tools.A00150_remapVal.app.core import MayaScene, run_build, run_build_wave


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setWindowTitle("Remap Value Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 720)

        self._build_ui()
        self._connect_signals()

    # ================================================================
    # UI 구성
    # ================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        root.addLayout(self._build_controller_row())
        root.addLayout(self._build_prefix_row())
        root.addLayout(self._build_driver_attr_row())
        root.addLayout(self._build_range_row())
        root.addLayout(self._build_interp_row())
        root.addWidget(self._build_list_group(), stretch=1)
        root.addLayout(self._build_attr_search_row())
        root.addWidget(self._build_build_button())
        root.addWidget(self._build_log_group())

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

    def _build_controller_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Main Controller"))
        self.le_controller = QLineEdit()
        row.addWidget(self.le_controller)
        self.btn_get_controller = QPushButton("Get")
        self.btn_get_controller.setFixedWidth(70)
        row.addWidget(self.btn_get_controller)
        return row

    def _build_prefix_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Prefix"))
        self.le_prefix = QLineEdit()
        self.le_prefix.setText("twist")
        row.addWidget(self.le_prefix)
        return row

    def _build_driver_attr_row(self):
        # Sine Wave 모드 전용: 컨트롤러에 추가할 공통 driver attr 이름.
        row = QHBoxLayout()
        row.addWidget(QLabel("Driver Attr"))
        self.le_driver_attr = QLineEdit()
        self.le_driver_attr.setText("wave")
        self.le_driver_attr.setToolTip(
            "Sine Wave mode: name of the keyable attribute added to the "
            "Main Controller. Its value drives the phase of all objects.")
        row.addWidget(self.le_driver_attr)
        return row

    def _make_range_spinbox(self, value, tooltip):
        sb = QDoubleSpinBox()
        sb.setRange(-1000000.0, 1000000.0)
        sb.setDecimals(3)
        sb.setValue(value)
        sb.setFixedWidth(80)
        sb.setToolTip(tooltip)
        return sb

    def _build_range_row(self):
        # remapValue range 4개. 컨트롤러 제어 attr 의 기본값이 된다.
        # In Min/Max 는 Sine Wave 전용, Out Min/Max 는 두 모드 공용.
        row = QHBoxLayout()
        row.addWidget(QLabel("Range"))

        row.addWidget(QLabel("In Min"))
        self.dsb_input_min = self._make_range_spinbox(
            0.0, "Sine Wave only. Default of the controller's {prefix}_input_min attr (remapValue Input Min).")
        row.addWidget(self.dsb_input_min)

        row.addWidget(QLabel("In Max"))
        self.dsb_input_max = self._make_range_spinbox(
            0.0, "Sine Wave only. Auto = Joints count - 1 (master remapValue Input Max). "
                 "Read-only: updates live as the Joints list changes.")
        # In Max 는 항상 (오브젝트 수 - 1) 로 자동 세팅되므로 사용자 편집을 막는다.
        self.dsb_input_max.setReadOnly(True)
        self.dsb_input_max.setButtonSymbols(QAbstractSpinBox.NoButtons)
        row.addWidget(self.dsb_input_max)

        row.addWidget(QLabel("Out Min"))
        self.dsb_output_min = self._make_range_spinbox(
            0.0, "Both modes. Default of the controller's {prefix}_output_min attr (master remapValue Output Min).")
        row.addWidget(self.dsb_output_min)

        row.addWidget(QLabel("Out Max"))
        self.dsb_output_max = self._make_range_spinbox(
            1.0, "Both modes. Default of the controller's {prefix}_output_max attr "
                 "(master remapValue Output Max / amplitude).")
        row.addWidget(self.dsb_output_max)
        return row

    def _build_interp_row(self):
        # Slerp Ramp 전용: master remapValue 의 보간 방식. enum 으로 빌드되는
        # 컨트롤러 {prefix}_interpolation attr 의 기본값이 된다. 기본 Linear.
        row = QHBoxLayout()
        row.addWidget(QLabel("Interpolation"))
        self.cb_interp = QComboBox()
        self.cb_interp.addItems(["Linear", "Smooth", "Spline"])
        self.cb_interp.setCurrentIndex(0)
        self.cb_interp.setToolTip(
            "Slerp Ramp only. Interpolation of the master remapValue / the "
            "controller's {prefix}_interpolation enum attr. Default Linear.")
        row.addWidget(self.cb_interp)
        row.addStretch(1)
        return row

    def _build_list_group(self):
        group = QGroupBox("Set Up")
        layout = QHBoxLayout(group)

        # 좌: joints(oColl) — 기본형 위젯. 우: attributes(twistAttrs) — Select 대신 List Attributes.
        self.joints_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Joints")
        self.attr_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Attributes", show_select=False)
        # numberTool 의 'List attributes' 버튼을 편집 버튼 행 맨 앞에 추가.
        self.attr_tsl.add_button("List Attributes", self.on_list_attributes, index=0)

        layout.addWidget(self.joints_tsl)
        layout.addWidget(self.attr_tsl)
        return group

    def _build_attr_search_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Attr Search"))
        self.le_attr_search = QLineEdit()
        self.le_attr_search.setPlaceholderText("token (e.g. rotate)")
        row.addWidget(self.le_attr_search)
        self.btn_attr_search = QPushButton("Search")
        self.btn_attr_search.setFixedWidth(70)
        row.addWidget(self.btn_attr_search)
        return row

    def _build_build_button(self):
        # 두 가지 빌드 모드: Slerp Ramp(기존) / Sine Wave(신규).
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        self.btn_build = QPushButton("Build (Slerp Ramp)")
        self.btn_build.setMinimumHeight(34)
        self.btn_build.setToolTip("Master remapValue slerp ramp setup (original).")
        row.addWidget(self.btn_build)

        self.btn_build_wave = QPushButton("Build (Sine Wave)")
        self.btn_build_wave.setMinimumHeight(34)
        self.btn_build_wave.setToolTip(
            "Phase-offset sine wave: plusMinusAverage -> animCurve -> remapValue per object.")
        row.addWidget(self.btn_build_wave)
        return container

    def _build_log_group(self):
        group = QGroupBox("Log")
        layout = QVBoxLayout(group)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(120)
        layout.addWidget(self.log_view)
        return group

    def _connect_signals(self):
        self.btn_get_controller.clicked.connect(self.on_get_controller)
        self.btn_attr_search.clicked.connect(self.on_search_attrs)
        self.le_attr_search.returnPressed.connect(self.on_search_attrs)
        self.btn_build.clicked.connect(self.on_build)
        self.btn_build_wave.clicked.connect(self.on_build_wave)

        # Joints 리스트 항목 수가 바뀔 때마다 In Max 를 (오브젝트 수 - 1) 로 라이브 반영.
        # Select/Add/Del/Sort 등 모든 변경은 내부 QListWidget 의 model 시그널로 잡는다
        # (위젯의 blockSignals 는 위젯 시그널만 막고 model 시그널은 막지 않는다).
        joints_model = self.joints_tsl.list_widget.model()
        joints_model.rowsInserted.connect(self._sync_input_max)
        joints_model.rowsRemoved.connect(self._sync_input_max)
        joints_model.modelReset.connect(self._sync_input_max)
        self._sync_input_max()  # 초기값 반영

    # ================================================================
    # helpers
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _sync_input_max(self, *args):
        """Joints 리스트 항목 수가 바뀌면 In Max 를 (오브젝트 수 - 1) 로 자동 반영.

        Sine Wave 마스터 remapValue 의 Input Max 는 항상 오브젝트 수 - 1 이어야
        animCurve 출력(0..N-1)과 input 범위가 정렬된다. max(...,1) 은 N<=1 보호용.
        """
        n = self.joints_tsl.count()
        self.dsb_input_max.setValue(float(max(n - 1, 1)))

    # ================================================================
    # 슬롯
    # ================================================================

    def on_get_controller(self):
        """현재 선택의 첫 오브젝트를 Main Controller 로 설정."""
        selection = MayaScene.selection()
        if not selection:
            self._log("[WARN] Nothing selected. Select a controller first.")
            return
        self.le_controller.setText(selection[0])

    def on_list_attributes(self):
        """joints 리스트 첫 오브젝트의 keyable 어트리뷰트를 Attributes 리스트에 채운다."""
        joints = self.joints_tsl.get_all_items()
        if not joints:
            self._log("[WARN] Joints list is empty. Add joints first.")
            return
        first = joints[0]
        if not MayaScene.exists(first):
            self._log("[WARN] Object not found in scene: {0}".format(first))
            return
        attrs = MayaScene.list_keyable_attrs(first)
        self.attr_tsl.set_items(attrs)
        self._log("Listed {0} keyable attribute(s) from {1}.".format(len(attrs), first))

    def on_search_attrs(self):
        """토큰을 포함하는 어트리뷰트를 Attributes 리스트에서 선택."""
        token = self.le_attr_search.text().strip()
        if not token:
            self._log("[WARN] Enter a search token.")
            return
        matches = [a for a in self.attr_tsl.get_all_items() if token in a]
        self.attr_tsl.select_by_texts(matches)
        self._log("Search '{0}' : {1} attribute(s) selected.".format(token, len(matches)))

    def _collect_inputs(self):
        """공통 입력 수집 + 검증. 유효하면 (prefix, controller, joints, attrs), 아니면 None."""
        prefix = self.le_prefix.text().strip()
        controller = self.le_controller.text().strip()
        joints = self.joints_tsl.get_all_items()
        attrs = self.attr_tsl.selected_items()

        if not prefix:
            self._log("[WARN] Prefix is empty.")
            return None
        if not controller:
            self._log("[WARN] Main Controller is empty. Use Get to set it.")
            return None
        if not MayaScene.exists(controller):
            self._log("[WARN] Controller not found in scene: {0}".format(controller))
            return None
        if not joints:
            self._log("[WARN] Joints list is empty.")
            return None
        if not attrs:
            self._log("[WARN] No attribute selected. List Attributes, then select one or more.")
            return None
        return prefix, controller, joints, attrs

    def on_build(self):
        self._log("--- Build Slerp Ramp ---")
        collected = self._collect_inputs()
        if collected is None:
            return
        prefix, controller, joints, attrs = collected

        # Out Min/Out Max 스핀박스를 Slerp output 제어 attr 기본값으로 재사용.
        output_min = self.dsb_output_min.value()
        output_max = self.dsb_output_max.value()
        # 콤보 index 0/1/2 -> enum value 1/2/3 (Linear/Smooth/Spline).
        interp_index = self.cb_interp.currentIndex()
        interp = interp_index + 1
        interp_name = ["Linear", "Smooth", "Spline"][interp_index]

        # Undo 청크: 전체 빌드를 한 번에 취소 가능하게.
        with undo_chunk():
            try:
                master = run_build(prefix, controller, joints, attrs, output_min, output_max, interp)
                self._log(
                    "Built: {master} | {n} joint(s) | interp: {interp} | attrs: {attrs}".format(
                        master=master, n=len(joints), interp=interp_name, attrs=", ".join(attrs)
                    )
                )
            except Exception as exc:
                self._log("[ERROR] Build failed: {0}".format(exc))

    def on_build_wave(self):
        """Sine Wave 모드 빌드: 오브젝트마다 plusMinusAverage->animCurve->remapValue 체인 생성."""
        self._log("--- Build Sine Wave ---")
        collected = self._collect_inputs()
        if collected is None:
            return
        prefix, controller, joints, attrs = collected

        driver_attr = self.le_driver_attr.text().strip()
        if not driver_attr:
            self._log("[WARN] Driver Attr name is empty.")
            return
        input_min = self.dsb_input_min.value()
        input_max = self.dsb_input_max.value()
        output_min = self.dsb_output_min.value()
        output_max = self.dsb_output_max.value()

        # Undo 청크: 전체 빌드를 한 번에 취소 가능하게.
        with undo_chunk():
            try:
                driver = run_build_wave(
                    prefix, controller, joints, driver_attr, attrs,
                    input_min, input_max, output_min, output_max)
                self._log(
                    "Built sine wave: driver {driver} | {n} object(s) | "
                    "range in[{imin},{imax}] out[{omin},{omax}] | attrs: {attrs}".format(
                        driver=driver, n=len(joints),
                        imin=input_min, imax=input_max, omin=output_min, omax=output_max,
                        attrs=", ".join(attrs)
                    )
                )
            except Exception as exc:
                self._log("[ERROR] Build failed: {0}".format(exc))

    # ================================================================
    # 슬롯 : Help > About
    # ================================================================

    def show_about(self, *args):
        message = (
            "Remap Value (Slerp Ramp) Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Two build modes:\n"
            "- Build (Slerp Ramp): interpolates attributes along a master remapValue\n"
            "  curve. Based on Chris Lesage's build_slerp_ramp.\n"
            "- Build (Sine Wave): per object a plusMinusAverage -> animCurve ->\n"
            "  remapValue chain propagates a phase-offset sine wave. The Driver Attr\n"
            "  added to the Main Controller drives the phase of all objects.\n"
            "\n"
            "How to use:\n"
            "1. Set Main Controller (select an object, press Get).\n"
            "2. Add joints to the Joints list.\n"
            "3. Press List Attributes, then select one or more attributes.\n"
            "4. Set a Prefix (default 'twist'). For Sine Wave, set a Driver Attr name.\n"
            "5. Press Build (Slerp Ramp) or Build (Sine Wave). Each build is one undo step.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
