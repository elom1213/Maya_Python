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
from tools.A00150_remapVal.app.core import MayaScene, run_build


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
        self.btn_build = QPushButton("Build")
        self.btn_build.setMinimumHeight(34)
        return self.btn_build

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

    def on_build(self):
        prefix = self.le_prefix.text().strip()
        controller = self.le_controller.text().strip()
        joints = self.joints_tsl.get_all_items()
        attrs = self.attr_tsl.selected_items()

        self._log("--- Build Slerp Ramp ---")

        # 입력 검증
        if not prefix:
            self._log("[WARN] Prefix is empty.")
            return
        if not controller:
            self._log("[WARN] Main Controller is empty. Use Get to set it.")
            return
        if not MayaScene.exists(controller):
            self._log("[WARN] Controller not found in scene: {0}".format(controller))
            return
        if not joints:
            self._log("[WARN] Joints list is empty.")
            return
        if not attrs:
            self._log("[WARN] No attribute selected. List Attributes, then select one or more.")
            return

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

    # ================================================================
    # 슬롯 : Help > About
    # ================================================================

    def show_about(self, *args):
        message = (
            "Remap Value (Slerp Ramp) Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Interpolates a collection of objects' attributes along a master\n"
            "remapValue curve (slerp ramp). Based on Chris Lesage's build_slerp_ramp.\n"
            "\n"
            "How to use:\n"
            "1. Set Main Controller (select an object, press Get).\n"
            "2. Add joints to the Joints list.\n"
            "3. Press List Attributes, then select one or more attributes.\n"
            "4. Set a Prefix (default 'twist').\n"
            "5. Press Build. The whole setup is one undo step.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
