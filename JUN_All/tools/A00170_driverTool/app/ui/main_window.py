# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00170_driverTool - Qt UI
#
# A00150_remapVal (Remap Value) + A00160_sphericalEye (Spherical Eye) 를
# 하나의 창 + QTabWidget 으로 통합한다(A00110_animTool 패턴).
# 두 탭의 위젯/핸들러는 접두사(rmp_ / sph_)로 분리하고, 로그/메뉴/푸터는 공유한다.
# 핵심 로직은 app/core 에 그대로 위임한다. 모든 UI 문자열/로그는 영어.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

from tools.A00170_driverTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00170_driverTool.app.core import (
    MayaScene,
    run_build_slerp, run_build_wave,
    run_build_spherical, run_build_nodes,
    run_attach_to_closest, run_attach_uniform, AIM_AXES, DRIVER_TYPES,
)


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00170_driverTool_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Driver Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(580, 780)

        self.build_ui()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # -------------------------
        # 메뉴 바 (Help > About)
        # -------------------------
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # -------------------------
        # 공용 로그 (모든 탭 공유)
        # 탭 빌더가 생성 중(_sync_*) self._log() 를 호출할 수 있으므로 탭보다 먼저 생성한다.
        # (레이아웃 추가는 탭 아래에 한다)
        # -------------------------
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(120)

        # -------------------------
        # 탭: Remap Value / Spherical Eye
        # -------------------------
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_remap_tab(), "Remap Value")
        self.tabs.addTab(self._build_spherical_tab(), "Spherical Eye")
        self.tabs.addTab(self._build_attach_tab(), "AttachCrv")
        main_layout.addWidget(self.tabs)

        # 로그창을 탭 아래에 배치
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # -------------------------
        # 저작권 (공통)
        # -------------------------
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ================================================================
    # Tab : Remap Value  (A00150_remapVal 이식)
    # ================================================================

    def _build_remap_tab(self):
        """Slerp Ramp / Sine Wave 두 빌드 모드. Main Controller + Joints + Attributes."""

        tab = QWidget()
        root = QVBoxLayout(tab)

        # Main Controller
        row = QHBoxLayout()
        row.addWidget(QLabel("Main Controller"))
        self.rmp_le_controller = QLineEdit()
        row.addWidget(self.rmp_le_controller)
        self.rmp_btn_get_controller = QPushButton("Get")
        self.rmp_btn_get_controller.setFixedWidth(70)
        row.addWidget(self.rmp_btn_get_controller)
        root.addLayout(row)

        # Prefix
        row = QHBoxLayout()
        row.addWidget(QLabel("Prefix"))
        self.rmp_le_prefix = QLineEdit()
        self.rmp_le_prefix.setText("twist")
        row.addWidget(self.rmp_le_prefix)
        root.addLayout(row)

        # Driver Attr (Sine Wave 전용)
        row = QHBoxLayout()
        row.addWidget(QLabel("Driver Attr"))
        self.rmp_le_driver_attr = QLineEdit()
        self.rmp_le_driver_attr.setText("wave")
        self.rmp_le_driver_attr.setToolTip(
            "Sine Wave mode: name of the keyable attribute added to the "
            "Main Controller. Its value drives the phase of all objects.")
        row.addWidget(self.rmp_le_driver_attr)
        root.addLayout(row)

        # Range : In Min/Max(Sine Wave), Out Min/Max(공용)
        row = QHBoxLayout()
        row.addWidget(QLabel("Range"))

        row.addWidget(QLabel("In Min"))
        self.rmp_dsb_input_min = self._rmp_make_range_spinbox(
            0.0, "Sine Wave only. Default of the controller's {prefix}_input_min attr (remapValue Input Min).")
        row.addWidget(self.rmp_dsb_input_min)

        row.addWidget(QLabel("In Max"))
        self.rmp_dsb_input_max = self._rmp_make_range_spinbox(
            0.0, "Sine Wave only. Auto = Joints count - 1 (master remapValue Input Max). "
                 "Read-only: updates live as the Joints list changes.")
        # In Max 는 항상 (오브젝트 수 - 1) 로 자동 세팅되므로 사용자 편집을 막는다.
        self.rmp_dsb_input_max.setReadOnly(True)
        self.rmp_dsb_input_max.setButtonSymbols(QAbstractSpinBox.NoButtons)
        row.addWidget(self.rmp_dsb_input_max)

        row.addWidget(QLabel("Out Min"))
        self.rmp_dsb_output_min = self._rmp_make_range_spinbox(
            0.0, "Both modes. Default of the controller's {prefix}_output_min attr (master remapValue Output Min).")
        row.addWidget(self.rmp_dsb_output_min)

        row.addWidget(QLabel("Out Max"))
        self.rmp_dsb_output_max = self._rmp_make_range_spinbox(
            1.0, "Both modes. Default of the controller's {prefix}_output_max attr "
                 "(master remapValue Output Max / amplitude).")
        row.addWidget(self.rmp_dsb_output_max)
        root.addLayout(row)

        # Interpolation : Slerp Ramp 전용. {prefix}_interpolation enum attr 기본값.
        row = QHBoxLayout()
        row.addWidget(QLabel("Interpolation"))
        self.rmp_cb_interp = QComboBox()
        self.rmp_cb_interp.addItems(["Linear", "Smooth", "Spline"])
        self.rmp_cb_interp.setCurrentIndex(0)
        self.rmp_cb_interp.setToolTip(
            "Slerp Ramp only. Interpolation of the master remapValue / the "
            "controller's {prefix}_interpolation enum attr. Default Linear.")
        row.addWidget(self.rmp_cb_interp)
        row.addStretch(1)
        root.addLayout(row)

        # Set Up : Joints(oColl) + Attributes(twistAttrs)
        group = QGroupBox("Set Up")
        group_layout = QHBoxLayout(group)
        self.rmp_joints_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Joints")
        self.rmp_attr_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Attributes", show_select=False)
        # numberTool 의 'List attributes' 버튼을 편집 버튼 행 맨 앞에 추가.
        self.rmp_attr_tsl.add_button("List Attributes", self.on_rmp_list_attributes, index=0)
        group_layout.addWidget(self.rmp_joints_tsl)
        group_layout.addWidget(self.rmp_attr_tsl)
        root.addWidget(group, stretch=1)

        # Attr Search
        row = QHBoxLayout()
        row.addWidget(QLabel("Attr Search"))
        self.rmp_le_attr_search = QLineEdit()
        self.rmp_le_attr_search.setPlaceholderText("token (e.g. rotate)")
        self.rmp_le_attr_search.setToolTip(
            "Select listed attributes containing this token. If none match, "
            "re-query the first joint by this token to reveal attributes that "
            "are not currently listed (e.g. 'worldMatrix').")
        row.addWidget(self.rmp_le_attr_search)
        self.rmp_btn_attr_search = QPushButton("Search")
        self.rmp_btn_attr_search.setFixedWidth(70)
        row.addWidget(self.rmp_btn_attr_search)
        root.addLayout(row)

        # Build buttons : Slerp Ramp / Sine Wave
        btn_box = QWidget()
        btn_row = QHBoxLayout(btn_box)
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.rmp_btn_build = QPushButton("Build (Slerp Ramp)")
        self.rmp_btn_build.setMinimumHeight(34)
        self.rmp_btn_build.setToolTip("Master remapValue slerp ramp setup (original).")
        btn_row.addWidget(self.rmp_btn_build)
        self.rmp_btn_build_wave = QPushButton("Build (Sine Wave)")
        self.rmp_btn_build_wave.setMinimumHeight(34)
        self.rmp_btn_build_wave.setToolTip(
            "Phase-offset sine wave: plusMinusAverage -> animCurve -> remapValue per object.")
        btn_row.addWidget(self.rmp_btn_build_wave)
        root.addWidget(btn_box)

        # Signals
        self.rmp_btn_get_controller.clicked.connect(self.on_rmp_get_controller)
        self.rmp_btn_attr_search.clicked.connect(self.on_rmp_search_attrs)
        self.rmp_le_attr_search.returnPressed.connect(self.on_rmp_search_attrs)
        self.rmp_btn_build.clicked.connect(self.on_rmp_build)
        self.rmp_btn_build_wave.clicked.connect(self.on_rmp_build_wave)

        # Joints 리스트 항목 수가 바뀔 때마다 In Max 를 (오브젝트 수 - 1) 로 라이브 반영.
        joints_model = self.rmp_joints_tsl.list_widget.model()
        joints_model.rowsInserted.connect(self._rmp_sync_input_max)
        joints_model.rowsRemoved.connect(self._rmp_sync_input_max)
        joints_model.modelReset.connect(self._rmp_sync_input_max)
        self._rmp_sync_input_max()  # 초기값 반영

        return tab

    def _rmp_make_range_spinbox(self, value, tooltip):
        sb = QDoubleSpinBox()
        sb.setRange(-1000000.0, 1000000.0)
        sb.setDecimals(3)
        sb.setValue(value)
        sb.setFixedWidth(80)
        sb.setToolTip(tooltip)
        return sb

    def _rmp_sync_input_max(self, *args):
        """Joints 리스트 항목 수가 바뀌면 In Max 를 (오브젝트 수 - 1) 로 자동 반영."""
        n = self.rmp_joints_tsl.count()
        self.rmp_dsb_input_max.setValue(float(max(n - 1, 1)))

    def on_rmp_get_controller(self):
        """현재 선택의 첫 오브젝트를 Main Controller 로 설정."""
        selection = MayaScene.selection()
        if not selection:
            self._log("[WARN] Nothing selected. Select a controller first.")
            return
        self.rmp_le_controller.setText(selection[0])

    def on_rmp_list_attributes(self):
        """joints 리스트 첫 오브젝트의 어트리뷰트(전체)를 Attributes 리스트에 채운다.

        keyable 만이 아니라 listAttr(obj) 전체 + multi/compound 자식까지 펼쳐 보여준다
        (A00145_RigConnect Connect 탭 List Attributes 와 동일).
        """
        joints = self.rmp_joints_tsl.get_all_items()
        if not joints:
            self._log("[WARN] Joints list is empty. Add joints first.")
            return
        first = joints[0]
        if not MayaScene.exists(first):
            self._log("[WARN] Object not found in scene: {0}".format(first))
            return
        attrs = MayaScene.list_attrs(first)
        self.rmp_attr_tsl.set_items(attrs)
        self._log("Listed {0} attribute(s) from {1}.".format(len(attrs), first))

    def on_rmp_search_attrs(self):
        """토큰으로 어트리뷰트를 검색한다.

        현재 리스트에 토큰을 포함하는 항목이 있으면 그것들을 선택하고, 없으면
        토큰으로 다시 질의해 (리스트업되지 않았던) 어트리뷰트를 찾아 채운다
        (A00145_RigConnect Connect 탭 Search 와 동일).
        """
        token = self.rmp_le_attr_search.text().strip()
        if not token:
            self._log("[WARN] Enter a search token.")
            return

        matches = [a for a in self.rmp_attr_tsl.get_all_items() if token in a]
        if matches:
            self.rmp_attr_tsl.select_by_texts(matches)
            self._log("Search '{0}' : {1} attribute(s) selected.".format(
                token, len(matches)))
            return

        # 현재 목록에 없으면 토큰으로 재질의해 발견되는 어트리뷰트를 채운다.
        joints = self.rmp_joints_tsl.get_all_items()
        if not joints:
            self._log("[WARN] Joints list is empty. Add joints first.")
            return
        first = joints[0]
        if not MayaScene.exists(first):
            self._log("[WARN] Object not found in scene: {0}".format(first))
            return
        try:
            attrs = MayaScene.list_attrs(first, token)
        except Exception as exc:
            self._log("[WARN] No attribute matches '{0}': {1}".format(token, exc))
            return
        if not attrs:
            self._log("Search '{0}' : no attribute found.".format(token))
            return
        self.rmp_attr_tsl.set_items(attrs)
        self._log("Search '{0}' : re-listed {1} attribute(s) from {2}.".format(
            token, len(attrs), first))

    def _rmp_collect_inputs(self):
        """공통 입력 수집 + 검증. 유효하면 (prefix, controller, joints, attrs), 아니면 None."""
        prefix = self.rmp_le_prefix.text().strip()
        controller = self.rmp_le_controller.text().strip()
        joints = self.rmp_joints_tsl.get_all_items()
        attrs = self.rmp_attr_tsl.selected_items()

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

    def on_rmp_build(self):
        self._log("--- Build Slerp Ramp ---")
        collected = self._rmp_collect_inputs()
        if collected is None:
            return
        prefix, controller, joints, attrs = collected

        # Out Min/Out Max 스핀박스를 Slerp output 제어 attr 기본값으로 재사용.
        output_min = self.rmp_dsb_output_min.value()
        output_max = self.rmp_dsb_output_max.value()
        # 콤보 index 0/1/2 -> enum value 1/2/3 (Linear/Smooth/Spline).
        interp_index = self.rmp_cb_interp.currentIndex()
        interp = interp_index + 1
        interp_name = ["Linear", "Smooth", "Spline"][interp_index]

        with undo_chunk():
            try:
                master = run_build_slerp(prefix, controller, joints, attrs, output_min, output_max, interp)
                self._log(
                    "Built: {master} | {n} joint(s) | interp: {interp} | attrs: {attrs}".format(
                        master=master, n=len(joints), interp=interp_name, attrs=", ".join(attrs)
                    )
                )
            except Exception as exc:
                self._log("[ERROR] Build failed: {0}".format(exc))

    def on_rmp_build_wave(self):
        """Sine Wave 모드 빌드: 오브젝트마다 plusMinusAverage->animCurve->remapValue 체인 생성."""
        self._log("--- Build Sine Wave ---")
        collected = self._rmp_collect_inputs()
        if collected is None:
            return
        prefix, controller, joints, attrs = collected

        driver_attr = self.rmp_le_driver_attr.text().strip()
        if not driver_attr:
            self._log("[WARN] Driver Attr name is empty.")
            return
        input_min = self.rmp_dsb_input_min.value()
        input_max = self.rmp_dsb_input_max.value()
        output_min = self.rmp_dsb_output_min.value()
        output_max = self.rmp_dsb_output_max.value()

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
    # Tab : Spherical Eye  (A00160_sphericalEye 이식)
    # ================================================================

    def _build_spherical_tab(self):
        """Baked / Converge 두 빌드 모드. Z축 일렬 조인트(front -> center)를 driver 하나로 구동."""

        tab = QWidget()
        root = QVBoxLayout(tab)

        # Main Controller
        row = QHBoxLayout()
        row.addWidget(QLabel("Main Controller"))
        self.sph_le_controller = QLineEdit()
        row.addWidget(self.sph_le_controller)
        self.sph_btn_get_controller = QPushButton("Get")
        self.sph_btn_get_controller.setFixedWidth(70)
        row.addWidget(self.sph_btn_get_controller)
        root.addLayout(row)

        # Prefix
        row = QHBoxLayout()
        row.addWidget(QLabel("Prefix"))
        self.sph_le_prefix = QLineEdit()
        self.sph_le_prefix.setText("eye")
        row.addWidget(self.sph_le_prefix)
        root.addLayout(row)

        # Driver Attr
        row = QHBoxLayout()
        row.addWidget(QLabel("Driver Attr"))
        self.sph_le_driver_attr = QLineEdit()
        self.sph_le_driver_attr.setText("dilate")
        self.sph_le_driver_attr.setToolTip(
            "Name of the keyable attribute added to the Main Controller. "
            "Its value drives the spherical dilation of all joints.")
        row.addWidget(self.sph_le_driver_attr)
        root.addLayout(row)

        # Radius (R)
        row = QHBoxLayout()
        row.addWidget(QLabel("Radius (R)"))
        self.sph_dsb_radius = QDoubleSpinBox()
        self.sph_dsb_radius.setRange(-1000000.0, 1000000.0)
        self.sph_dsb_radius.setDecimals(3)
        self.sph_dsb_radius.setValue(1.0)
        self.sph_dsb_radius.setFixedWidth(100)
        self.sph_dsb_radius.setToolTip(
            "Sphere radius R. Baked: default of the controller's {prefix}_radius attr "
            "(dilation strength). Converge: radius of the sphere the bound curves are "
            "kept on. Auto-updates to the first->last (front->center) joint distance "
            "whenever the Joints list changes (Select/Add/Del); you can still override "
            "it manually before building.")
        row.addWidget(self.sph_dsb_radius)
        row.addStretch(1)
        root.addLayout(row)

        # Joints (front -> center order)
        group = QGroupBox("Joints (front -> center order)")
        group_layout = QVBoxLayout(group)
        self.sph_joints_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Joints")
        group_layout.addWidget(self.sph_joints_tsl)
        root.addWidget(group, stretch=1)

        # Build buttons : Baked / Converge
        btn_box = QWidget()
        btn_row = QHBoxLayout(btn_box)
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.sph_btn_build = QPushButton("Build (Spherical Eye)")
        self.sph_btn_build.setMinimumHeight(34)
        self.sph_btn_build.setToolTip(
            "Baked mode. Drive scaleX/Y (= 1 + driver*R*sin) and translateZ "
            "(= Zinit + driver*R*cos) for the listed joints. sin/cos are baked as "
            "constants at build time. translateX/Y are left untouched.")
        btn_row.addWidget(self.sph_btn_build)
        self.sph_btn_build_nodes = QPushButton("Build (Converge to Center)")
        self.sph_btn_build_nodes.setMinimumHeight(34)
        self.sph_btn_build_nodes.setToolTip(
            "Converge mode (Maya 2023+ compatible). dilate (-90..90) gathers every joint to "
            "the LAST (center) joint when positive, or the FIRST (front) joint when negative, "
            "and drives scaleX/Y so each bound curve stays on a sphere of radius R: "
            "scale = sqrt(R^2 - dist^2) / sqrt(R^2 - dist_rest^2).")
        btn_row.addWidget(self.sph_btn_build_nodes)
        root.addWidget(btn_box)

        # Signals
        self.sph_btn_get_controller.clicked.connect(self.on_sph_get_controller)
        self.sph_btn_build.clicked.connect(self.on_sph_build)
        self.sph_btn_build_nodes.clicked.connect(self.on_sph_build_nodes)

        # Joints 리스트 항목이 바뀔 때마다 Radius 를 first->last 조인트 거리로 자동 갱신.
        joints_model = self.sph_joints_tsl.list_widget.model()
        joints_model.rowsInserted.connect(self._sph_sync_radius)
        joints_model.rowsRemoved.connect(self._sph_sync_radius)
        joints_model.modelReset.connect(self._sph_sync_radius)
        self._sph_sync_radius()  # 초기 반영

        return tab

    def _sph_sync_radius(self, *args):
        """Joints 리스트가 바뀔 때마다 Radius 를 first->last 조인트(=front->center) 거리로 자동 갱신.

        조인트가 2개 미만이거나 씬에 없으면 값을 건드리지 않는다(사용자 수동 override 유지).
        """
        joints = self.sph_joints_tsl.get_all_items()
        if len(joints) < 2:
            return
        dist = MayaScene.distance(joints[0], joints[-1])
        if dist is None:
            return
        self.sph_dsb_radius.setValue(dist)

    def on_sph_get_controller(self):
        """현재 선택의 첫 오브젝트를 Main Controller 로 설정."""
        selection = MayaScene.selection()
        if not selection:
            self._log("[WARN] Nothing selected. Select a controller first.")
            return
        self.sph_le_controller.setText(selection[0])

    def _sph_collect_inputs(self):
        """공통 입력 수집 + 검증. 유효하면 (prefix, controller, joints), 아니면 None."""
        prefix = self.sph_le_prefix.text().strip()
        controller = self.sph_le_controller.text().strip()
        joints = self.sph_joints_tsl.get_all_items()

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
        return prefix, controller, joints

    def _sph_collect_build_inputs(self):
        """공통 입력 + driver_attr/radius 수집·검증. 유효하면 튜플, 아니면 None."""
        collected = self._sph_collect_inputs()
        if collected is None:
            return None
        prefix, controller, joints = collected

        driver_attr = self.sph_le_driver_attr.text().strip()
        if not driver_attr:
            self._log("[WARN] Driver Attr name is empty.")
            return None
        radius = self.sph_dsb_radius.value()
        return prefix, controller, joints, driver_attr, radius

    def on_sph_build(self):
        """Baked 모드: 조인트마다 scale/translateZ 구동 노드 생성(sin/cos 는 빌드 시 상수)."""
        self._log("--- Build Spherical Eye (Baked) ---")
        collected = self._sph_collect_build_inputs()
        if collected is None:
            return
        prefix, controller, joints, driver_attr, radius = collected

        with undo_chunk():
            try:
                driver = run_build_spherical(prefix, controller, joints, driver_attr, radius)
                self._log(
                    "Built (baked): driver {driver} | {n} joint(s) | radius {r}".format(
                        driver=driver, n=len(joints), r=radius
                    )
                )
            except Exception as exc:
                self._log("[ERROR] Build failed: {0}".format(exc))

    def on_sph_build_nodes(self):
        """Converge 모드: dilate 0->90 동안 전 조인트를 center(마지막) 조인트 위치로 수렴."""
        self._log("--- Build Converge to Center ---")
        collected = self._sph_collect_build_inputs()
        if collected is None:
            return
        prefix, controller, joints, driver_attr, radius = collected
        if len(joints) < 2:
            self._log("[WARN] Need at least 2 joints (front .. center) to converge.")
            return

        with undo_chunk():
            try:
                driver, skipped = run_build_nodes(prefix, controller, joints, driver_attr, radius)
                self._log(
                    "Built (converge): driver {driver} | {n} joint(s) | +center '{c}' / "
                    "-front '{f}' | sphere radius {r}".format(
                        driver=driver, n=len(joints), c=joints[-1], f=joints[0], r=radius
                    )
                )
                if skipped:
                    self._log(
                        "[WARN] scale NOT driven for {n} joint(s) (radius {r} <= rest distance "
                        "from center): {names}".format(
                            n=len(skipped), r=radius, names=", ".join(skipped)
                        )
                    )
            except Exception as exc:
                self._log("[ERROR] Build failed: {0}".format(exc))

    # ================================================================
    # Tab : AttachCrv  (ref/ref_01.mel attachDriverOnCurve 이식 + 동작 변경)
    # ================================================================

    def _build_attach_tab(self):
        """TSL 에 나열된 오브젝트들을 커브에서 '가장 가까운 지점'에 라이브 어태치한다.

        ref 는 커브에 일정 간격으로 새 로케이터를 어태치했지만, 여기서는 기존
        오브젝트들을 각자 최근접 파라미터 지점에 붙인다(커브 변형을 따라감).
        """
        tab = QWidget()
        root = QVBoxLayout(tab)

        # Attachment Curve
        row = QHBoxLayout()
        row.addWidget(QLabel("Attachment Curve"))
        self.atc_le_curve = QLineEdit()
        row.addWidget(self.atc_le_curve)
        self.atc_btn_get_curve = QPushButton("Get")
        self.atc_btn_get_curve.setFixedWidth(70)
        row.addWidget(self.atc_btn_get_curve)
        root.addLayout(row)

        # Objects (커브에 붙일 기존 오브젝트들)
        group = QGroupBox("Objects (attach to closest point)")
        group_layout = QVBoxLayout(group)
        self.atc_objs_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Objects")
        group_layout.addWidget(self.atc_objs_tsl)
        root.addWidget(group, stretch=1)

        # Options : Orient to tangent + Aim Axis
        row = QHBoxLayout()
        self.atc_cb_orient = QCheckBox("Orient to curve tangent")
        self.atc_cb_orient.setChecked(True)
        self.atc_cb_orient.setToolTip(
            "On: aim the chosen local axis along the curve tangent and drive "
            "the object's rotate as well as translate. Off: drive translate "
            "only (keeps each object's current rotation). Turn off for vertical "
            "curves where the tangent is parallel to world up.")
        row.addWidget(self.atc_cb_orient)
        row.addWidget(QLabel("Aim Axis"))
        self.atc_cb_aim = QComboBox()
        self.atc_cb_aim.addItems(list(AIM_AXES))
        self.atc_cb_aim.setToolTip(
            "Which local axis of each object aims along the curve tangent.")
        row.addWidget(self.atc_cb_aim)
        row.addStretch(1)
        root.addLayout(row)

        # Normal curve (norCrv) : ref-faithful up-vector source.
        row = QHBoxLayout()
        self.atc_cb_norcrv = QCheckBox("Create Normal Curve (norCrv)")
        self.atc_cb_norcrv.setChecked(True)
        self.atc_cb_norcrv.setToolTip(
            "On (default, like the original ref tool): create one straight "
            "'norCrv' curve parented under the attachment curve and drive each "
            "object's up (Y) / side (Z) from it. Rotate or reshape the norCrv "
            "to control the up direction and twist of the whole chain.\n"
            "Off: use the self-contained world-up frame computed from the curve "
            "tangent (no extra curve created).")
        row.addWidget(self.atc_cb_norcrv)
        row.addWidget(QLabel("norCrv Length"))
        self.atc_dsb_norcrv_len = QDoubleSpinBox()
        self.atc_dsb_norcrv_len.setRange(0.001, 100000.0)
        self.atc_dsb_norcrv_len.setDecimals(3)
        self.atc_dsb_norcrv_len.setSingleStep(0.1)
        self.atc_dsb_norcrv_len.setValue(1.0)
        self.atc_dsb_norcrv_len.setFixedWidth(90)
        self.atc_dsb_norcrv_len.setToolTip(
            "Length of the generated norCrv (visual size of the up reference).")
        row.addWidget(self.atc_dsb_norcrv_len)
        row.addStretch(1)
        root.addLayout(row)

        # Collect the created pointOnCurveInfo nodes into one objectSet.
        self.atc_cb_make_set = QCheckBox(
            "Group pointOnCurveInfo nodes into a set")
        self.atc_cb_make_set.setChecked(True)
        self.atc_cb_make_set.setToolTip(
            "Create one objectSet ('<curve>_atcPOCI_SET') containing every "
            "pointOnCurveInfo node made by this build, for easy selection later.")
        root.addWidget(self.atc_cb_make_set)

        # Build : Attach the listed objects to their closest point.
        self.atc_btn_build = QPushButton("Attach to Closest Point")
        self.atc_btn_build.setMinimumHeight(34)
        self.atc_btn_build.setToolTip(
            "For each listed object: find the closest parameter on the curve, "
            "then drive it there with a pointOnCurveInfo -> matrix network "
            "(parent-safe, live as the curve deforms).")
        root.addWidget(self.atc_btn_build)

        # Distribute : create N new drivers uniformly along the curve
        # (ref attachDriverOnCurve original behaviour). Shares the orient / Aim
        # Axis / norCrv / set options above.
        dist_group = QGroupBox("Distribute new drivers uniformly")
        dist_layout = QVBoxLayout(dist_group)

        dist_row = QHBoxLayout()
        dist_row.addWidget(QLabel("Count"))
        self.atc_sb_count = QSpinBox()
        self.atc_sb_count.setRange(1, 1000)
        self.atc_sb_count.setValue(5)
        self.atc_sb_count.setFixedWidth(70)
        self.atc_sb_count.setToolTip(
            "How many new drivers to create and spread evenly along the curve.")
        dist_row.addWidget(self.atc_sb_count)
        dist_row.addWidget(QLabel("Driver Type"))
        self.atc_cb_drvtype = QComboBox()
        self.atc_cb_drvtype.addItems(["Locator", "Null"])
        self.atc_cb_drvtype.setToolTip(
            "Locator: spaceLocator drivers (visible). Null: empty groups.")
        dist_row.addWidget(self.atc_cb_drvtype)
        dist_row.addStretch(1)
        dist_layout.addLayout(dist_row)

        self.atc_cb_fullrange = QCheckBox("Distribute across full range (open curve)")
        self.atc_cb_fullrange.setChecked(True)
        self.atc_cb_fullrange.setToolTip(
            "On (open curves): the first and last drivers land exactly on the "
            "curve ends (parameter min and max).\n"
            "Off (periodic/closed curves): the last driver stops just before the "
            "end so it does not overlap the first at the seam.")
        dist_layout.addWidget(self.atc_cb_fullrange)

        self.atc_btn_distribute = QPushButton("Distribute Drivers on Curve")
        self.atc_btn_distribute.setMinimumHeight(34)
        self.atc_btn_distribute.setToolTip(
            "Create Count new drivers and attach them at evenly spaced "
            "parameters from the curve start to its end (pointOnCurveInfo -> "
            "matrix network, live as the curve deforms).")
        dist_layout.addWidget(self.atc_btn_distribute)
        root.addWidget(dist_group)

        # Signals
        self.atc_btn_get_curve.clicked.connect(self.on_atc_get_curve)
        self.atc_btn_build.clicked.connect(self.on_atc_build)
        self.atc_btn_distribute.clicked.connect(self.on_atc_distribute)
        self.atc_cb_orient.toggled.connect(self._atc_sync_orient_enabled)
        self.atc_cb_norcrv.toggled.connect(self._atc_sync_orient_enabled)
        self._atc_sync_orient_enabled()

        return tab

    def _atc_sync_orient_enabled(self, *args):
        """Orient/norCrv 토글에 따라 종속 위젯의 활성 상태를 동기화한다."""
        orient = self.atc_cb_orient.isChecked()
        self.atc_cb_aim.setEnabled(orient)
        self.atc_cb_norcrv.setEnabled(orient)
        self.atc_dsb_norcrv_len.setEnabled(orient and self.atc_cb_norcrv.isChecked())

    def on_atc_get_curve(self):
        """현재 선택의 첫 오브젝트를 Attachment Curve 로 설정."""
        selection = MayaScene.selection()
        if not selection:
            self._log("[WARN] Nothing selected. Select a curve first.")
            return
        self.atc_le_curve.setText(selection[0])

    def on_atc_build(self):
        self._log("--- Attach to Closest Point ---")
        curve = self.atc_le_curve.text().strip()
        objects = self.atc_objs_tsl.get_all_items()

        if not curve:
            self._log("[WARN] Attachment Curve is empty. Use Get to set it.")
            return
        if not MayaScene.exists(curve):
            self._log("[WARN] Curve not found in scene: {0}".format(curve))
            return
        if not objects:
            self._log("[WARN] Objects list is empty. Add objects first.")
            return

        orient = self.atc_cb_orient.isChecked()
        aim_axis = self.atc_cb_aim.currentText()
        use_norcrv = self.atc_cb_norcrv.isChecked()
        norcrv_len = self.atc_dsb_norcrv_len.value()
        create_set = self.atc_cb_make_set.isChecked()

        with undo_chunk():
            try:
                attached, failed, set_node, norcrv = run_attach_to_closest(
                    curve, objects, orient=orient, aim_axis=aim_axis,
                    use_normal_curve=use_norcrv,
                    normal_curve_length=norcrv_len,
                    create_set=create_set)
            except Exception as exc:
                self._log("[ERROR] Attach failed: {0}".format(exc))
                return

        self._log(
            "Attached {n} object(s) to '{c}' | orient: {o}{axis}{nc}".format(
                n=len(attached), c=curve,
                o="on" if orient else "off",
                axis=" ({0})".format(aim_axis) if orient else "",
                nc=" | norCrv" if (orient and use_norcrv) else ""))
        if norcrv:
            self._log(
                "Normal curve created: {0} "
                "(rotate/reshape it to control up & twist)".format(norcrv))
        for obj, param in attached:
            self._log("  {0} -> param {1:.4f}".format(obj, param))
        for obj, reason in failed:
            self._log("[WARN] Skipped {0}: {1}".format(obj, reason))
        if set_node:
            self._log("pointOnCurveInfo nodes grouped into set: {0}".format(
                set_node))

    def on_atc_distribute(self):
        """커브에 새 드라이버 N 개를 균일 파라미터 간격으로 생성·어태치(ref 원래 동작)."""
        self._log("--- Distribute Drivers on Curve ---")
        curve = self.atc_le_curve.text().strip()

        if not curve:
            self._log("[WARN] Attachment Curve is empty. Use Get to set it.")
            return
        if not MayaScene.exists(curve):
            self._log("[WARN] Curve not found in scene: {0}".format(curve))
            return

        count = self.atc_sb_count.value()
        driver_type = self.atc_cb_drvtype.currentText().lower()
        full_range = self.atc_cb_fullrange.isChecked()
        orient = self.atc_cb_orient.isChecked()
        aim_axis = self.atc_cb_aim.currentText()
        use_norcrv = self.atc_cb_norcrv.isChecked()
        norcrv_len = self.atc_dsb_norcrv_len.value()
        create_set = self.atc_cb_make_set.isChecked()

        with undo_chunk():
            try:
                created, set_node, norcrv = run_attach_uniform(
                    curve, count, driver_type=driver_type, full_range=full_range,
                    orient=orient, aim_axis=aim_axis,
                    use_normal_curve=use_norcrv,
                    normal_curve_length=norcrv_len,
                    create_set=create_set)
            except Exception as exc:
                self._log("[ERROR] Distribute failed: {0}".format(exc))
                return

        self._log(
            "Distributed {n} {t} driver(s) on '{c}' | range: {rng} | "
            "orient: {o}{axis}{nc}".format(
                n=len(created), t=driver_type, c=curve,
                rng="full" if full_range else "open-ended",
                o="on" if orient else "off",
                axis=" ({0})".format(aim_axis) if orient else "",
                nc=" | norCrv" if (orient and use_norcrv) else ""))
        if norcrv:
            self._log(
                "Normal curve created: {0} "
                "(rotate/reshape it to control up & twist)".format(norcrv))
        for drv, param in created:
            self._log("  {0} -> param {1:.4f}".format(drv, param))
        if set_node:
            self._log("pointOnCurveInfo nodes grouped into set: {0}".format(
                set_node))

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def show_about(self, *args):
        message = (
            "Driver Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Merge of two rigging driver setup tools into tabs:\n"
            "\n"
            "[Remap Value]\n"
            "- Build (Slerp Ramp): interpolates attributes along a master remapValue\n"
            "  curve. Based on Chris Lesage's build_slerp_ramp.\n"
            "- Build (Sine Wave): per object a plusMinusAverage -> animCurve ->\n"
            "  remapValue chain propagates a phase-offset sine wave.\n"
            "\n"
            "[Spherical Eye] (Z-axis aligned joints, front -> center)\n"
            "- Build (Spherical Eye): baked spherical dilation (sin/cos baked).\n"
            "- Build (Converge to Center): Maya 2023+ node network. dilate (-90..90)\n"
            "  gathers joints to the center (+) or front (-) and keeps bound curves\n"
            "  on a sphere of radius R.\n"
            "\n"
            "[AttachCrv] (ported from ref attachDriverOnCurve)\n"
            "- Attach to Closest Point: drives each listed object onto its closest\n"
            "  parameter on the curve via a pointOnCurveInfo -> matrix network\n"
            "  (parent-safe, live as the curve deforms). Optional orient to tangent.\n"
            "- Distribute Drivers on Curve (ref original): create N new Locator/Null\n"
            "  drivers spread evenly from the curve start to its end (Count, full /\n"
            "  open-ended range), attached with the same matrix network.\n"
            "- Create Normal Curve (norCrv, default, ref-faithful): adds one straight\n"
            "  norCrv under the curve; rotate/reshape it to control up & twist. Off:\n"
            "  self-contained world-up frame.\n"
            "\n"
            "Each build is one undo step. All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
