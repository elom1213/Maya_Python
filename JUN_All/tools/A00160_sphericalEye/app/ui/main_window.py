# -*- coding: utf-8 -*-
"""
Spherical Eye Tool - PySide(Qt) UI.

Z축 일렬 조인트(앞 -> 중심)를 컨트롤러 driver 하나로 구면 dilation 구동하는 셋업을 만든다.
로직은 app/core/spherical_drive.py 에 위임한다. UI 보조는 maya.cmds(MayaScene),
노드 생성 본체는 pymel(core). 모든 UI 문자열/로그는 영어.
"""

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from tools.A00160_sphericalEye.app.config.version import VERSION, LAST_UPDATE
from tools.A00160_sphericalEye.app.core import MayaScene, run_build, run_build_nodes


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Spherical Eye Tool v{0}".format(VERSION))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(480, 560)

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
        root.addLayout(self._build_radius_row())
        root.addWidget(self._build_list_group(), stretch=1)
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
        self.le_prefix.setText("eye")
        row.addWidget(self.le_prefix)
        return row

    def _build_driver_attr_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Driver Attr"))
        self.le_driver_attr = QLineEdit()
        self.le_driver_attr.setText("dilate")
        self.le_driver_attr.setToolTip(
            "Name of the keyable attribute added to the Main Controller. "
            "Its value drives the spherical dilation of all joints.")
        row.addWidget(self.le_driver_attr)
        return row

    def _build_radius_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Radius (R)"))
        self.dsb_radius = QDoubleSpinBox()
        self.dsb_radius.setRange(-1000000.0, 1000000.0)
        self.dsb_radius.setDecimals(3)
        self.dsb_radius.setValue(1.0)
        self.dsb_radius.setFixedWidth(100)
        self.dsb_radius.setToolTip(
            "Sphere radius R. Baked: default of the controller's {prefix}_radius attr "
            "(dilation strength). Converge: radius of the sphere the bound curves are "
            "kept on. Auto-updates to the first->last (front->center) joint distance "
            "whenever the Joints list changes (Select/Add/Del); you can still override "
            "it manually before building.")
        row.addWidget(self.dsb_radius)
        row.addStretch(1)
        return row

    def _build_list_group(self):
        group = QGroupBox("Joints (front -> center order)")
        layout = QVBoxLayout(group)
        # 조인트 리스트(oColl). 리스트 순서가 앞(Z+) -> 중심 순서여야 한다.
        self.joints_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Joints")
        layout.addWidget(self.joints_tsl)
        return group

    def _build_build_button(self):
        # 두 가지 빌드 모드: Baked(구면 dilation, sin/cos 상수) / Converge(center 조인트로 수렴).
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        self.btn_build = QPushButton("Build (Spherical Eye)")
        self.btn_build.setMinimumHeight(34)
        self.btn_build.setToolTip(
            "Baked mode. Drive scaleX/Y (= 1 + driver*R*sin) and translateZ "
            "(= Zinit + driver*R*cos) for the listed joints. sin/cos are baked as "
            "constants at build time. translateX/Y are left untouched.")
        row.addWidget(self.btn_build)

        self.btn_build_nodes = QPushButton("Build (Converge to Center)")
        self.btn_build_nodes.setMinimumHeight(34)
        self.btn_build_nodes.setToolTip(
            "Converge mode (Maya 2023+ compatible). dilate (-90..90) gathers every joint to "
            "the LAST (center) joint when positive, or the FIRST (front) joint when negative, "
            "and drives scaleX/Y so each bound curve stays on a sphere of radius R: "
            "scale = sqrt(R^2 - dist^2) / sqrt(R^2 - dist_rest^2).")
        row.addWidget(self.btn_build_nodes)
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
        self.btn_build.clicked.connect(self.on_build)
        self.btn_build_nodes.clicked.connect(self.on_build_nodes)

        # Joints 리스트 항목이 바뀔 때마다 Radius 를 first->last 조인트 거리로 자동 갱신.
        # Select/Add/Del 등 모든 변경은 내부 QListWidget 의 model 시그널로 잡는다
        # (위젯 blockSignals 는 위젯 시그널만 막고 model 시그널은 막지 않는다).
        joints_model = self.joints_tsl.list_widget.model()
        joints_model.rowsInserted.connect(self._sync_radius)
        joints_model.rowsRemoved.connect(self._sync_radius)
        joints_model.modelReset.connect(self._sync_radius)
        self._sync_radius()  # 초기 반영

    # ================================================================
    # helpers
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _sync_radius(self, *args):
        """Joints 리스트가 바뀔 때마다 Radius 를 first->last 조인트(=front->center) 거리로 자동 갱신.

        Converge 모드의 sphere 반지름 = front 조인트에서 center 조인트까지 거리. 조인트가 2개 미만이거나
        씬에 없으면 값을 건드리지 않는다(사용자가 수동 입력/override 가능하도록 유지).
        """
        joints = self.joints_tsl.get_all_items()
        if len(joints) < 2:
            return
        dist = MayaScene.distance(joints[0], joints[-1])
        if dist is None:
            return
        self.dsb_radius.setValue(dist)

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

    def _collect_inputs(self):
        """공통 입력 수집 + 검증. 유효하면 (prefix, controller, joints), 아니면 None."""
        prefix = self.le_prefix.text().strip()
        controller = self.le_controller.text().strip()
        joints = self.joints_tsl.get_all_items()

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

    def _collect_build_inputs(self):
        """공통 입력 + driver_attr/radius 수집·검증. 유효하면 튜플, 아니면 None."""
        collected = self._collect_inputs()
        if collected is None:
            return None
        prefix, controller, joints = collected

        driver_attr = self.le_driver_attr.text().strip()
        if not driver_attr:
            self._log("[WARN] Driver Attr name is empty.")
            return None
        radius = self.dsb_radius.value()
        return prefix, controller, joints, driver_attr, radius

    def on_build(self):
        """Baked 모드: 조인트마다 scale/translateZ 구동 노드 생성(sin/cos 는 빌드 시 상수)."""
        self._log("--- Build Spherical Eye (Baked) ---")
        collected = self._collect_build_inputs()
        if collected is None:
            return
        prefix, controller, joints, driver_attr, radius = collected

        # Undo 청크: 전체 빌드를 한 번에 취소 가능하게.
        cmds.undoInfo(openChunk=True)
        try:
            driver = run_build(prefix, controller, joints, driver_attr, radius)
            self._log(
                "Built (baked): driver {driver} | {n} joint(s) | radius {r}".format(
                    driver=driver, n=len(joints), r=radius
                )
            )
        except Exception as exc:
            self._log("[ERROR] Build failed: {0}".format(exc))
        finally:
            cmds.undoInfo(closeChunk=True)

    def on_build_nodes(self):
        """Converge 모드: dilate 0->90 동안 전 조인트를 center(마지막) 조인트 위치로 수렴."""
        self._log("--- Build Converge to Center ---")
        collected = self._collect_build_inputs()
        if collected is None:
            return
        prefix, controller, joints, driver_attr, radius = collected
        if len(joints) < 2:
            self._log("[WARN] Need at least 2 joints (front .. center) to converge.")
            return

        # Undo 청크: 전체 빌드를 한 번에 취소 가능하게.
        cmds.undoInfo(openChunk=True)
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
        finally:
            cmds.undoInfo(closeChunk=True)

    # ================================================================
    # 슬롯 : Help > About
    # ================================================================

    def show_about(self, *args):
        message = (
            "Spherical Eye Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Drives Z-axis aligned joints (front -> center) from a single\n"
            "controller attribute. Two build modes:\n"
            "\n"
            "- Build (Spherical Eye) - Baked spherical dilation. sin/cos baked:\n"
            "    scaleX/Y   = 1      + driver * R * sin(offset)\n"
            "    translateZ = Zinit + driver * R * cos(offset)\n"
            "- Build (Converge to Center) - Maya 2023+ node network. dilate\n"
            "  (-90..90) gathers every joint to the LAST (center) joint when\n"
            "  positive, or the FIRST (front) joint when negative, and scales\n"
            "  each bound curve to stay on a sphere of radius R:\n"
            "    translate_i = init + t_c*(center-init) + t_f*(front-init)\n"
            "    scaleX/Y_i  = sqrt(R^2 - dist^2) / sqrt(R^2 - dist_rest^2)\n"
            "\n"
            "At driver=0 every joint stays at its rest pose. Converge mode needs\n"
            "at least 2 joints (first = front target, last = center target) and a\n"
            "Radius R >= each joint's rest distance to the center joint.\n"
            "\n"
            "How to use:\n"
            "1. Set Main Controller (select an object, press Get).\n"
            "2. Add joints to the Joints list in FRONT -> CENTER order.\n"
            "3. Set Prefix, Driver Attr name, and Radius (sphere radius R).\n"
            "4. Press a Build button. The whole build is one undo step.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
