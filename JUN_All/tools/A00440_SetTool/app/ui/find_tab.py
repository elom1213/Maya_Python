# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
# A00440_SetTool - Find 탭 (in-Maya)
#
# "이 오브젝트들은 **어느 세트에 들어 있나**" 를 되묻는 탭이다.
# 위 리스트에 오브젝트를 담고 `Find Sets` 를 누르면, 그것들이 멤버로 들어 있는 세트가
# 아래 리스트에 올라온다. 아래 리스트의 행을 클릭(Shift/Ctrl 로 여러 개)하면 **그 세트
# 노드 자체**가 씬에서 선택된다.
#
# ── 세트 리스트는 noExpand 로 선택한다 ────────────────────────────────────
# `cmds.select` 는 세트를 만나면 세트를 **펼쳐 멤버를 선택**한다. 그래서 공용 TSL 에
# `select_no_expand` 를 두고 이 탭의 결과 리스트에서 켠다 - 행을 누르면 멤버가 아니라
# 세트가 잡힌다(Edit 탭은 예전 동작 그대로 둔다. 그쪽 Split 은 "씬 선택 == A 의 멤버"
# 를 사고 감지에 쓰고 있다).

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


class FindTab(QWidget):

    def __init__(self, log_view=None, on_found=None, parent=None):
        super(FindTab, self).__init__(parent)

        self.log_view = log_view
        # 찾은 세트를 Edit 탭 리스트로 보낼 때 부르는 콜백 (없으면 버튼을 만들지 않는다)
        self.on_found = on_found

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        # ---- 찾을 오브젝트 --------------------------------------------
        self.obj_tsl = JUN_mod_tsl_qt_v01(
            title="Objects",
            select_label="Select Objects",
            show_reverse=True,
            show_order=True,
            multi_select=True,
            list_min_height=110,
            log_callback=self.log,
        )
        layout.addWidget(self.obj_tsl)

        # ---- 옵션 ------------------------------------------------------
        options_box = QGroupBox("Options")
        options_layout = QVBoxLayout(options_box)

        self.chk_shapes = QCheckBox("Look at the shape as well")
        self.chk_shapes.setChecked(True)
        self.chk_shapes.setToolTip(
            "Component sets and shading groups are attached to the SHAPE, not to the\n"
            "transform. With this off, only the sets holding the transform itself show up.\n"
            "Every non-intermediate shape is queried, not just the first one.")
        options_layout.addWidget(self.chk_shapes)

        self.chk_render = QCheckBox("Include shading groups")
        self.chk_render.setToolTip(
            "A shading group is a set too (nodeType 'shadingEngine'), so every shaded\n"
            "mesh belongs to one. Off by default to keep the list to real object sets.\n"
            "initialShadingGroup comes with them - it is a render set, so this switch\n"
            "decides it, not the default-sets one below.")
        options_layout.addWidget(self.chk_render)

        self.chk_parents = QCheckBox("Include parent sets")
        self.chk_parents.setToolTip(
            "A set can be a member of another set.\n"
            "With this on, the search walks up : object in set B, set B in set C -> C too.")
        options_layout.addWidget(self.chk_parents)

        self.chk_default = QCheckBox("Include Maya's default sets")
        self.chk_default.setToolTip(
            "defaultLightSet, defaultObjectSet, initialShadingGroup ...")
        options_layout.addWidget(self.chk_default)

        self.chk_select_found = QCheckBox("Select the found sets in the scene")
        self.chk_select_found.setToolTip(
            "Select every set found, right after the search.\n"
            "You can also click the rows below to select them one by one.")
        options_layout.addWidget(self.chk_select_found)

        layout.addWidget(options_box)

        self.btn_find = QPushButton("Find Sets")
        self.btn_find.setMinimumHeight(30)
        self.btn_find.setToolTip(
            "List every set the objects above belong to.\n"
            "Nothing in the scene is changed.")
        self.btn_find.clicked.connect(self.on_find)
        layout.addWidget(self.btn_find)

        # ---- 찾은 세트 --------------------------------------------------
        # ★ select_no_expand : 행을 클릭하면 멤버가 아니라 **세트 노드 자체**를 선택한다.
        self.set_tsl = JUN_mod_tsl_qt_v01(
            title="Sets",
            select_label="Select Sets",
            show_reverse=True,
            show_order=False,
            multi_select=True,
            select_no_expand=True,
            list_min_height=110,
            log_callback=self.log,
        )
        layout.addWidget(self.set_tsl)

        self.set_tsl.add_button("Info", self.on_info)
        if self.on_found:
            self.set_tsl.add_button("To Edit", self.on_send_to_edit)

        hint = QLabel(
            "Click a row to select that set in the scene - Shift or Ctrl for several.\n"
            "The sets themselves are selected, not their members.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

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

    def on_find(self):
        # UUID 로 되찾은 **현재** 경로를 쓴다 - 담아 둔 뒤 리네임되어도 맞는 노드를 잡는다.
        objects = self.obj_tsl.get_all_nodes()

        result = set_manager.run_find_sets(
            objects,
            include_shapes=self.chk_shapes.isChecked(),
            include_render=self.chk_render.isChecked(),
            include_parents=self.chk_parents.isChecked(),
            include_default=self.chk_default.isChecked(),
        )

        for warning in result.warnings:
            self.log("[warning] " + warning)

        if not result.ok:
            self.log("[failed] " + result.message)
            return

        self.log(result.message)

        # 몇 개가 걸렸는지 세트마다 한 줄로. 부모 세트는 직접 든 오브젝트가 없을 수 있다.
        total = len(objects)
        for name, members in result.detail.items():
            self.log("  {0} : {1} / {2} object(s)".format(name, len(members), total))

        # 찾은 결과로 리스트를 **교체**한다 - 다시 찾았는데 지난 결과가 남아 있으면
        # 어느 것이 이번 결과인지 알 수 없다.
        self.set_tsl.set_items(result.created_many)

        if self.chk_select_found.isChecked():
            # ★ 그냥 select 하면 세트가 **펼쳐져 멤버**가 선택된다.
            maya_sets.select_sets(result.created_many)

    def on_info(self):
        names = self.set_tsl.get_all_nodes()

        if not names:
            self.log("No set is listed - press Find Sets first.")
            return

        for name in names:
            self.log("{0} : {1}".format(name, set_manager.describe_set(name)))

    def on_send_to_edit(self):
        """고른 세트(없으면 전부)를 Edit 탭 리스트로 보낸다."""
        names = self.set_tsl.selected_nodes() or self.set_tsl.get_all_nodes()

        if not names:
            self.log("No set is listed - press Find Sets first.")
            return

        self.on_found(names)
