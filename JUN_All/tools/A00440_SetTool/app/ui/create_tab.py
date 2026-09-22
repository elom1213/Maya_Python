# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-22
# A00440_SetTool - Create 탭 (in-Maya)
#
# 리스트에 담은 오브젝트로 세트를 만든다. 방식이 둘이다 (v01.05~).
#   One set per object : 오브젝트마다 하나 - 세트 개수 = 오브젝트 개수,
#                        이름 = <오브젝트 이름>_Set   (원래 동작, 기본값)
#   One set for all    : 전부를 담은 **세트 하나** - 이름은 칸에 적은 것,
#                        비우면 `objects_Set`
#
# Edit 탭이 다루는 세트를 **만드는 쪽**이다. 컨트롤러 하나마다 세트를 두는 리그에서
# 손으로 만들던 일이라, 이름 규칙만 지키면 그다음은 Edit 탭의 집합 연산으로 이어진다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QRadioButton,
    QButtonGroup,
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

        # ---- 방식 (v01.05~)
        mode_box = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_box)

        self.mode_group = QButtonGroup(self)
        self.rb_per_object = QRadioButton("One set per object  ( N objects -> N sets )")
        self.rb_per_object.setChecked(True)
        self.rb_per_object.setToolTip(
            "The original behaviour - each object gets its own set, named after it.")
        self.rb_one_set = QRadioButton("One set for all  ( N objects -> 1 set )")
        self.rb_one_set.setToolTip(
            "Every object in the list goes into a single new set.")
        self.mode_group.addButton(self.rb_per_object)
        self.mode_group.addButton(self.rb_one_set)
        mode_layout.addWidget(self.rb_per_object)
        mode_layout.addWidget(self.rb_one_set)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Set Name"))
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText(
            "leave empty for '{0}'".format(set_manager.GROUP_SET_NAME))
        self.name_field.setToolTip(
            "Used by 'One set for all'. The path and the namespace are dropped\n"
            "and odd characters are replaced, the same way the per-object names are\n"
            "made - Maya would otherwise change the name silently.")
        name_row.addWidget(self.name_field, stretch=1)
        mode_layout.addLayout(name_row)

        layout.addWidget(mode_box)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

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
        self.btn_create.clicked.connect(self.on_create)
        layout.addWidget(self.btn_create)

        # 방식에 따라 안내문과 버튼 글자가 바뀐다.
        self.mode_group.buttonClicked.connect(lambda *_: self._sync_mode())
        self._sync_mode()

        layout.addStretch(1)

    def _sync_mode(self):
        """방식에 맞춰 안내문 · 버튼 글자 · 이름 칸 활성을 맞춘다."""
        one_set = self.rb_one_set.isChecked()

        self.name_field.setEnabled(one_set)

        if one_set:
            self.hint.setText(
                "Every object in the list goes into ONE new set. The name comes from\n"
                "the Set Name field ('{0}' when it is empty).".format(
                    set_manager.GROUP_SET_NAME))
            self.btn_create.setText("Create One Set")
            self.btn_create.setToolTip(
                "Make a single set holding every object in the list.\n"
                "One undo step for the whole run.")
        else:
            self.hint.setText(
                ("One set per object, named after it : 'pCube1' -> 'pCube1{0}'.\n"
                 "The path and the namespace are dropped from the name, so "
                 "'|grp|rig:pCube1' gives 'pCube1{0}' too.").format(maya_sets.SET_SUFFIX))
            self.btn_create.setText("Create Sets")
            self.btn_create.setToolTip(
                "Make one set for every object in the list, in list order.\n"
                "One undo step for the whole run.")

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

        if self.rb_one_set.isChecked():
            result = set_manager.run_create_one_set(
                objects, name=self.name_field.text().strip())
        else:
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
