# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00010_humanIKTool_V02 - Qt UI (PySide)
# 레거시 A00010_humanIKTool 의 maya.cmds UI 를 PySide(arch B)로 마이그레이션.

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

from tools.A00010_humanIKTool_V02.app.config.version import VERSION
from tools.A00010_humanIKTool_V02.app.core import HIKManager


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00010_humanIKTool_V02_window"


class MainWindow(QWidget):

    def __init__(self):

        # 마야 메인 윈도우에 parent (뷰포트 위에는 떠 있되 다른 툴 창과 정상 Z-order)
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 360
        self.win_height = 620
        self.win_title  = f"HumanIK Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # -------------------------
        # HIK character node 섹션
        # -------------------------
        grp_hik = QGroupBox("HumanIK Character Node")
        hik_layout = QVBoxLayout(grp_hik)

        self.btn_get_hik = QPushButton("Get HIK Nodes")
        self.btn_get_hik.clicked.connect(self.on_get_hik_nodes)
        hik_layout.addWidget(self.btn_get_hik)

        # HIK 노드는 하나만 대상으로 하므로 단일 선택.
        self.list_hik = QListWidget()
        self.list_hik.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_hik.setMaximumHeight(90)
        hik_layout.addWidget(self.list_hik)

        main_layout.addWidget(grp_hik)

        # -------------------------
        # 조인트 리스트 (재사용 위젯)
        # 순서가 슬롯 매칭 순서이므로 Up/Down 으로 정렬 가능하게 둔다.
        # -------------------------
        grp_jnt = QGroupBox("Joints to Assign")
        jnt_layout = QVBoxLayout(grp_jnt)

        self.tsl_joints = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints (order = slot order)",
            show_select=True, show_add=True, show_del=True,
            show_up=True, show_down=True, show_sort=True,
            multi_select=True, list_min_height=160,
            select_label="Select Joints",
            log_callback=self.log,
        )
        jnt_layout.addWidget(self.tsl_joints)

        main_layout.addWidget(grp_jnt)

        # -------------------------
        # 본 체인 선택 + Assign
        # -------------------------
        grp_chain = QGroupBox("Bone Chain")
        chain_layout = QVBoxLayout(grp_chain)

        self.cmb_chain = QComboBox()
        self.cmb_chain.addItems(HIKManager.chain_labels())
        chain_layout.addWidget(self.cmb_chain)

        self.btn_assign = QPushButton("Assign Joints")
        self.btn_assign.clicked.connect(self.on_assign_joints)
        chain_layout.addWidget(self.btn_assign)

        main_layout.addWidget(grp_chain)

        # -------------------------
        # 로그
        # -------------------------
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------
    # Slots
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def selected_hik_node(self):
        items = self.list_hik.selectedItems()
        return items[0].text() if items else None

    def on_get_hik_nodes(self):
        nodes = HIKManager.get_hik_nodes()
        self.list_hik.clear()
        if not nodes:
            self.log("[Warning] No HIKCharacterNode found in the scene.")
            return
        self.list_hik.addItems(nodes)
        self.list_hik.setCurrentRow(0)
        self.log("Found {0} HIK node(s).".format(len(nodes)))

    def on_assign_joints(self):
        joints = self.tsl_joints.get_all_items()
        hik_node = self.selected_hik_node()
        chain_label = self.cmb_chain.currentText()

        done, msg = HIKManager.assign_joints(joints, hik_node, chain_label)
        self.log(msg)

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "HumanIK Tool v{0}\nWritten by Ji Hun Park.".format(VERSION),
        )
