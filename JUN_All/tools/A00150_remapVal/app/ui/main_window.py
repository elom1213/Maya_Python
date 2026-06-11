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

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from tools.A00150_remapVal.app.config.version import VERSION, LAST_UPDATE
from tools.A00150_remapVal.app.core import MayaScene, run_build, run_build_wave


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Remap Value Tool v{0}".format(VERSION))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
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
        # Sine Wave 모드 전용: remapValue range 4개. 컨트롤러 제어 attr 의 기본값이 된다.
        row = QHBoxLayout()
        row.addWidget(QLabel("Range"))

        row.addWidget(QLabel("In Min"))
        self.dsb_input_min = self._make_range_spinbox(
            0.0, "Default of the controller's {prefix}_input_min attr (remapValue Input Min).")
        row.addWidget(self.dsb_input_min)

        row.addWidget(QLabel("In Max"))
        self.dsb_input_max = self._make_range_spinbox(
            0.0, "Default of the controller's {prefix}_input_max attr (remapValue Input Max). "
                 "0 = auto (object count - 1).")
        row.addWidget(self.dsb_input_max)

        row.addWidget(QLabel("Out Min"))
        self.dsb_output_min = self._make_range_spinbox(
            0.0, "Default of the controller's {prefix}_output_min attr (remapValue Output Min).")
        row.addWidget(self.dsb_output_min)

        row.addWidget(QLabel("Out Max"))
        self.dsb_output_max = self._make_range_spinbox(
            1.0, "Default of the controller's {prefix}_output_max attr (remapValue Output Max / amplitude).")
        row.addWidget(self.dsb_output_max)
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

    # ================================================================
    # helpers
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

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

        # Undo 청크: 전체 빌드를 한 번에 취소 가능하게.
        cmds.undoInfo(openChunk=True)
        try:
            master = run_build(prefix, controller, joints, attrs)
            self._log(
                "Built: {master} | {n} joint(s) | attrs: {attrs}".format(
                    master=master, n=len(joints), attrs=", ".join(attrs)
                )
            )
        except Exception as exc:
            self._log("[ERROR] Build failed: {0}".format(exc))
        finally:
            cmds.undoInfo(closeChunk=True)

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
        cmds.undoInfo(openChunk=True)
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
        finally:
            cmds.undoInfo(closeChunk=True)

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
