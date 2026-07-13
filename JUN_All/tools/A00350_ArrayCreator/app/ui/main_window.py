# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00350_ArrayCreator - Qt UI (Maya objects -> UE Control Rig Item Array node)
#
# TSL 에 오브젝트를 리스트업하고, 그 순서대로 UE Control Rig 의 Item Array 노드
# 텍스트를 생성해 클립보드에 복사(UE 그래프에 Ctrl+V) + 0020_out 에 파일 저장한다.
# 요소 Type 은 콤보에서 선택(모든 요소 공통, 기본 Bone). 참고: A00080/A00260.

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00350_ArrayCreator.app.config.version import VERSION, LAST_UPDATE
from tools.A00350_ArrayCreator.app.core import ELEMENT_TYPES, DEFAULT_TYPE, DEFAULT_NODE_TITLE

# 주의: ArrayCreator / ArrayOptions 는 최상단에서 바인딩하지 않고 슬롯 안에서 '지역 import'
# 한다(DEV 리로드 시 이 창이 옛 클래스를 잡는 것을 막아 코드 변경이 즉시 반영되게 함).


WINDOW_OBJECT_NAME = "JUN_A00350_ArrayCreator_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 420
        self.win_height = 600
        self.win_title  = "Array Creator v{0}".format(VERSION)

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
        help_menu.addAction("About").triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 로그 (탭 빌더가 self.log 를 호출할 수 있으므로 먼저 생성)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(90)
        self.te_log.setMaximumHeight(150)

        # 오브젝트 리스트 (TSL). Select/Add 는 현재 선택으로 채운다. 순서는 Up/Down 으로.
        # Reverse 로 배열 순서를 한 번에 뒤집을 수 있다.
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects",
            select_label="Select Objects",
            show_sort=False,
            show_reverse=True,
            list_min_height=200,
            log_callback=self.log,
        )
        main_layout.addWidget(self.tsl, 1)

        # 옵션 영역
        main_layout.addWidget(self._build_options_group())

        # 생성 버튼
        self.btn_create = QPushButton("Create Array Node  ->  Copy to Clipboard")
        self.btn_create.setMinimumHeight(36)
        self.btn_create.clicked.connect(self.on_create)
        main_layout.addWidget(self.btn_create)

        main_layout.addWidget(self.te_log)

        self.log("Array Creator v{0} ({1}) ready. Select objects and 'Select Objects'.".format(
            VERSION, LAST_UPDATE))

    def _build_options_group(self):
        group = QGroupBox("Array Options")
        layout = QVBoxLayout(group)

        # 요소 Type (모든 요소 공통, 기본 Bone)
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Element Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(list(ELEMENT_TYPES))
        self.cmb_type.setCurrentIndex(list(ELEMENT_TYPES).index(DEFAULT_TYPE))
        self.cmb_type.setToolTip("ERigElementType applied to every array element.")
        type_row.addWidget(self.cmb_type)
        type_row.addStretch(1)
        layout.addLayout(type_row)

        # Node Title (UE 그래프에 보이는 노드 이름)
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Node Title:"))
        self.le_title = QLineEdit(DEFAULT_NODE_TITLE)
        self.le_title.setToolTip("NodeTitle shown on the pasted node in the Control Rig graph.")
        title_row.addWidget(self.le_title)
        layout.addLayout(title_row)

        return group

    # --------------------------------------------------
    # 슬롯
    # --------------------------------------------------

    def on_create(self):
        names = self.tsl.get_all_items()
        if not names:
            self.log("No objects in the list. Select objects and 'Select Objects' first.")
            return

        options = self._collect_options()

        try:
            # 지역 import: 리로드 후 최신 클래스를 잡는다.
            from tools.A00350_ArrayCreator.app.core.array_creator import ArrayCreator
            creator = ArrayCreator()
            text, elements, out_path = creator.create(names, options)
        except Exception as e:
            self.log("ERROR during create: {0}".format(e))
            raise

        if not text:
            self.log("Nothing generated. (No valid object names.)")
            return

        # 클립보드로 복사 -> UE Control Rig 그래프에 바로 붙여넣기 (Ctrl+V)
        QApplication.clipboard().setText(text)

        self.log("-" * 40)
        self.log("Array '{0}' ({1}): {2} element(s) [{3}]".format(
            options.node_title, options.node_name, len(elements), options.elem_type))
        for i, name in enumerate(elements):
            self.log("  [{0}] {1}".format(i, name))
        self.log("Copied to clipboard. Paste into Control Rig graph (Ctrl+V).")
        self.log("Saved: {0}".format(out_path))

    def _collect_options(self):
        # 지역 import: 리로드 후 최신 모듈을 잡는다.
        from tools.A00350_ArrayCreator.app.core.node_builder import ArrayOptions
        return ArrayOptions(
            elem_type  = self.cmb_type.currentText(),
            node_title = self.le_title.text().strip() or DEFAULT_NODE_TITLE,
        )

    # --------------------------------------------------
    # 헬퍼
    # --------------------------------------------------

    def log(self, message):
        self.te_log.append(str(message))

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Array Creator\n"
            "Version {0}\n"
            "Last Update {1}\n\n"
            "Maya objects -> UE Control Rig Item Array node (clipboard).".format(
                VERSION, LAST_UPDATE
            ),
        )
