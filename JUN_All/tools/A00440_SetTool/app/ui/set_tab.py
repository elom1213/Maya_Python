# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00440_SetTool - Qt UI 본문 (in-Maya)
#
# 컴포넌트를 원소로 갖는 세트들끼리 집합 연산을 한다.
#
# ── 리스트 클릭이 씬 선택을 바꾼다 ─────────────────────────────────────────
# 공용 TSL 위젯은 항목을 클릭하면 그 노드를 씬에서 선택한다. 그런데 대상이 세트일 때
# `cmds.select` 는 세트를 **펼쳐서 멤버 전체를 선택**한다(mayapy 로 확인).
# Split 은 "지금 고른 컴포넌트"가 S 인데, 리스트에서 A 를 고르는 순간 S 가 A 의 멤버
# 전체로 바뀌어 버린다 → 그대로 실행하면 A 를 통째로 빼내는 사고가 난다.
# 그래서 Split 쪽에는 **Capture Selection** 을 둬서 S 를 미리 붙잡아 두고,
# 붙잡은 게 없을 때는 씬 선택을 쓰되 그것이 A 의 멤버와 정확히 같으면 거부한다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    Qt,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01

from tools.A00440_SetTool.app.core import maya_sets, set_manager, set_ops


class SetTab(QWidget):

    def __init__(self, log_view=None, parent=None):
        super(SetTab, self).__init__(parent)

        self.log_view = log_view

        # Capture Selection 으로 붙잡아 둔 S. 비어 있으면 실행 시점의 씬 선택을 쓴다.
        self.captured = []

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        # ---- 세트 목록 ------------------------------------------------
        self.tsl = JUN_mod_tsl_qt_v01(
            title="Sets",
            select_label="Select Sets",
            show_reverse=True,
            show_order=True,
            multi_select=True,
            list_min_height=150,
            log_callback=self.log,
        )
        layout.addWidget(self.tsl)

        # 세트 구성 확인용. 리스트에 담은 것들의 원소 수/종류를 로그로 뿌린다.
        self.tsl.add_button("Info", self.on_info)

        hint = QLabel(
            "Operations use every item in the list, in list order.\n"
            "Difference subtracts the rest from the FIRST item.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ---- 결과 -----------------------------------------------------
        result_box = QGroupBox("Result")
        result_layout = QVBoxLayout(result_box)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("New Set Name"))
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("leave empty for an automatic name")
        name_row.addWidget(self.name_field, stretch=1)
        result_layout.addLayout(name_row)

        self.chk_select_result = QCheckBox("Select the result in the scene")
        result_layout.addWidget(self.chk_select_result)

        layout.addWidget(result_box)

        # ---- 집합 연산 -------------------------------------------------
        ops_box = QGroupBox("Set Operations")
        ops_layout = QVBoxLayout(ops_box)

        self.btn_union = QPushButton("Union ( ∪ )")
        self.btn_union.setToolTip("A ∪ B ∪ ...  -  every element of any set")
        self.btn_union.clicked.connect(self.on_union)

        self.btn_intersection = QPushButton("Intersection ( ∩ )")
        self.btn_intersection.setToolTip("A ∩ B ∩ ...  -  elements present in every set")
        self.btn_intersection.clicked.connect(self.on_intersection)

        self.btn_difference = QPushButton("Difference ( ∖ )")
        self.btn_difference.setToolTip(
            "A ∖ B ∖ ...  -  the first set minus every other set")
        self.btn_difference.clicked.connect(self.on_difference)

        for button in (self.btn_union, self.btn_intersection, self.btn_difference):
            button.setMinimumHeight(30)
            ops_layout.addWidget(button)

        layout.addWidget(ops_box)

        # ---- 분할(Split) -----------------------------------------------
        split_box = QGroupBox("Split by Scene Selection")
        split_layout = QVBoxLayout(split_box)

        split_hint = QLabel(
            "A = the selected row (or the first row).  S = the scene selection.\n"
            "Moves A ∩ S out of A into a new set.")
        split_hint.setWordWrap(True)
        split_layout.addWidget(split_hint)

        capture_row = QHBoxLayout()
        self.btn_capture = QPushButton("Capture Selection ( S )")
        self.btn_capture.setToolTip(
            "Remember the current scene selection.\n"
            "Do this BEFORE clicking a set in the list - clicking a row makes Maya select\n"
            "that set's members, which replaces your component selection.")
        self.btn_capture.clicked.connect(self.on_capture)
        capture_row.addWidget(self.btn_capture, stretch=1)

        self.btn_clear_capture = QPushButton("Clear")
        self.btn_clear_capture.setFixedWidth(60)
        self.btn_clear_capture.clicked.connect(self.on_clear_capture)
        capture_row.addWidget(self.btn_clear_capture)
        split_layout.addLayout(capture_row)

        self.capture_label = QLabel("S : not captured - the live scene selection will be used")
        self.capture_label.setWordWrap(True)
        split_layout.addWidget(self.capture_label)

        self.chk_remove_source = QCheckBox("Remove the extracted elements from A")
        self.chk_remove_source.setChecked(True)
        self.chk_remove_source.setToolTip(
            "On  : A is split in two - A keeps A ∖ S, the new set takes A ∩ S\n"
            "Off : A is left untouched, the new set is a copy of A ∩ S")
        split_layout.addWidget(self.chk_remove_source)

        self.btn_split = QPushButton("Split ( A ∖ S , A ∩ S )")
        self.btn_split.setMinimumHeight(30)
        self.btn_split.clicked.connect(self.on_split)
        split_layout.addWidget(self.btn_split)

        layout.addWidget(split_box)

        layout.addStretch(1)

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        if self.log_view is not None:
            self.log_view.appendPlainText(message)
        else:
            print(message)

    def _report(self, result):
        """OpResult 를 로그에 뿌리고, 옵션에 따라 결과를 씬에서 선택한다."""
        for warning in result.warnings:
            self.log("[warning] " + warning)

        if not result.ok:
            self.log("[failed] " + result.message)
            return

        self.log(result.message)

        if result.created:
            self.tsl.append_unique([result.created])

        if self.chk_select_result.isChecked():
            maya_sets.select(result.members)

    # ==================================================================
    # 입력 수집
    # ==================================================================

    def _set_names(self):
        """리스트에 담긴 세트들의 **현재** 이름(UUID 로 해석)."""
        return self.tsl.get_all_nodes()

    def _target_set(self):
        """Split 의 A. 정확히 한 행을 골랐으면 그것, 아니면 첫 행."""
        selected = self.tsl.selected_nodes()

        if len(selected) == 1:
            return selected[0]

        names = self._set_names()

        return names[0] if names else None

    def _result_name(self, fallback):
        text = self.name_field.text().strip()

        return text if text else fallback

    def _selection(self):
        """Split 에 쓸 S. (원소들, 어디서 왔는지) 를 돌려준다."""
        if self.captured:
            return self.captured, "captured selection"

        return maya_sets.current_selection(), "live scene selection"

    # ==================================================================
    # 동작
    # ==================================================================

    def on_info(self):
        names = self._set_names()

        if not names:
            self.log("The list is empty.")
            return

        for name in names:
            self.log("{0} : {1}".format(name, set_manager.describe_set(name)))

    def on_capture(self):
        self.captured = maya_sets.current_selection()

        if not self.captured:
            self.capture_label.setText("S : nothing was selected - capture cleared")
            self.log("Capture Selection : nothing is selected in the scene.")
            return

        summary = set_ops.type_summary(self.captured)
        self.capture_label.setText("S : {0} elements ({1})".format(len(self.captured), summary))
        self.log("Captured {0} elements ({1}).".format(len(self.captured), summary))

    def on_clear_capture(self):
        self.captured = []
        self.capture_label.setText("S : not captured - the live scene selection will be used")
        self.log("Capture cleared.")

    def on_union(self):
        self._report(set_manager.run_union(self._set_names(), self._result_name("union_set")))

    def on_intersection(self):
        self._report(set_manager.run_intersection(
            self._set_names(), self._result_name("intersection_set")))

    def on_difference(self):
        self._report(set_manager.run_difference(
            self._set_names(), self._result_name("difference_set")))

    def on_split(self):
        target = self._target_set()

        if not target:
            self.log("[failed] The list is empty - add the set to split first.")
            return

        picked, source = self._selection()

        if not picked:
            self.log("[failed] Nothing is selected in the scene and nothing was captured.")
            return

        # 리스트의 행을 클릭하면 마야가 **그 세트의 멤버 전체**를 선택한다
        # (cmds.select 는 세트를 펼친다). 그 상태로 Split 을 누르면 S = A 가 되어
        # A 를 통째로 빼내 버린다. 사고를 막고 원인을 알려준다.
        if source == "live scene selection" and set(picked) == set(maya_sets.set_members(target)):
            self.log(
                "[failed] The scene selection is exactly the contents of '{0}'. "
                "Clicking a row in the list selects that set's members, which would extract "
                "everything. Select the components you want, press Capture Selection ( S ), "
                "then Split.".format(target))
            return

        self.log("Split using {0} ({1} elements).".format(source, len(picked)))

        result = set_manager.run_split(
            target,
            self._result_name("{0}_split".format(target.split("|")[-1].split(":")[-1])),
            remove_from_source=self.chk_remove_source.isChecked(),
            picked=picked,
        )

        self._report(result)
