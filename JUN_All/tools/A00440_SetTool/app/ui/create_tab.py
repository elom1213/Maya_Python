# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-10
# A00440_SetTool - Create 탭 (in-Maya)
#
# 리스트에 담은 오브젝트를 **하나마다 하나씩** 세트로 만든다.
#   세트 개수 = 오브젝트 개수,  이름 = <오브젝트 이름>_Set
#
# Edit 탭이 다루는 세트를 **만드는 쪽**이다. 컨트롤러 하나마다 세트를 두는 리그에서
# 손으로 만들던 일이라, 이름 규칙만 지키면 그다음은 Edit 탭의 집합 연산으로 이어진다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QCheckBox,
    QPushButton,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01

from tools.A00440_SetTool.app.core import maya_sets, set_manager


class CreateTab(QWidget):

    def __init__(self, log_view=None, on_created=None, parent=None):
        super(CreateTab, self).__init__(parent)

        self.log_view = log_view
        # 만든 세트를 Edit 탭 리스트로 보낼 때 부르는 콜백 (없으면 안 보낸다)
        self.on_created = on_created

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        self.tsl = JUN_mod_tsl_qt_v01(
            title="Objects",
            select_label="Select Objects",
            show_reverse=True,
            show_order=True,
            multi_select=True,
            list_min_height=150,
            log_callback=self.log,
        )
        layout.addWidget(self.tsl)

        hint = QLabel(
            "One set per object, named after it : 'pCube1' -> 'pCube1{0}'.\n"
            "The path and the namespace are dropped from the name, so "
            "'|grp|rig:pCube1' gives 'pCube1{0}' too.".format(maya_sets.SET_SUFFIX))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        options_box = QGroupBox("Options")
        options_layout = QVBoxLayout(options_box)

        self.chk_send_to_edit = QCheckBox("Add the new sets to the Edit tab list")
        self.chk_send_to_edit.setChecked(True)
        self.chk_send_to_edit.setToolTip(
            "The sets you just made are usually the ones you want to combine next.")
        options_layout.addWidget(self.chk_send_to_edit)

        self.chk_select_result = QCheckBox("Select the new sets in the scene")
        options_layout.addWidget(self.chk_select_result)

        layout.addWidget(options_box)

        self.btn_create = QPushButton("Create Sets")
        self.btn_create.setMinimumHeight(30)
        self.btn_create.setToolTip(
            "Make one set for every object in the list, in list order.\n"
            "One undo step for the whole run.")
        self.btn_create.clicked.connect(self.on_create)
        layout.addWidget(self.btn_create)

        layout.addStretch(1)

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        if self.log_view is not None:
            self.log_view.appendPlainText(message)
        else:
            print(message)

    # ==================================================================
    # 실행
    # ==================================================================

    def on_create(self):
        # UUID 로 되찾은 **현재** 경로를 쓴다 - 담아 둔 뒤 리네임되어도 맞는 노드를 잡는다.
        objects = self.tsl.get_all_nodes()
        result = set_manager.run_create_per_object(objects)

        for warning in result.warnings:
            self.log("[warning] " + warning)

        if not result.ok:
            self.log("[failed] " + result.message)
            return

        self.log(result.message)

        if result.created_many:
            if self.chk_send_to_edit.isChecked() and self.on_created:
                self.on_created(result.created_many)
            if self.chk_select_result.isChecked():
                # ★ 세트를 그냥 select 하면 **멤버가 펼쳐져** 선택된다 - 세트 노드 자체를
                #   고르려면 noExpand 가 필요하다.
                maya_sets.select_sets(result.created_many)
