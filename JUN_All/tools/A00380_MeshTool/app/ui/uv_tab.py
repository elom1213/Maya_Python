# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
# A00380_MeshTool - UV Sets 탭 (v01.17)
#
# A00050_uvTool_V02(v02.03) 의 창을 **탭 하나로** 옮긴 것이다. 하는 일은 같다 —
# 메시는 `UV set name`(기본 `map1`) 이라는 UV 세트 **하나만** 가져야 한다는 규칙으로
#   * Catch Objects  : 어긋난 메시를 **사유와 함께** 로그에 적고 리스트 · 씬 선택에 담는다
#   * Delete UV Sets : 규칙 이름이 아닌 세트를 지운다(첫/기본 세트는 마야가 못 지운다)
#   * Rename UV Set  : 첫 세트의 이름을 규칙 이름으로
# 리스트 옆 UV Sets 표(Object / UV Sets / Rule)가 오브젝트마다 세트와 판정을 보여 준다.
#
# 옮기면서 바꾼 것은 **창에 딸린 것뿐**이다 — 메뉴 · Pin · 로그창은 A00380 창의 것을 쓴다
# (`log` / `log_html` 콜백). 규칙 설명은 Help > UV Sets Rule. 로직(`app/core/uv_set_manager.py`)과
# 표(`app/ui/uv_set_table.py`)는 A00050 의 파일을 그대로 가져왔다.
#
# 원본 A00050_uvTool_V02 는 지우지 않고 남긴다(A00300 → MeshDoctor 이식 때와 같은 관례).

import maya.cmds as cmds

from Framework.qt.qt import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    Qt,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01

from tools.A00380_MeshTool.app.core import uv_set_manager as uv_mgr
from tools.A00380_MeshTool.app.ui.uv_set_table import UvSetTable, colored_log_line


#: Help > UV Sets Rule 에 보여 줄 규칙 설명.
RULE_TEXT = (
    "A mesh should have exactly ONE UV set, named after the\n"
    "'UV set name' field (default '{0}').\n\n"
    "Caught as broken :\n"
    "  multiple    two or more UV sets\n"
    "  wrong_name  a single set with another name\n"
    "  no_uv       no UV set at all\n\n"
    "Delete UV Sets deletes every set with another name - except the\n"
    "default (first) one, which Maya never deletes.\n"
    "Rename UV Set renames the FIRST set to that name.\n"
    "It cannot rename when the mesh already has a set with that name -\n"
    "Maya refuses.".format(uv_mgr.DEFAULT_UV_SET))


class UvSetsTab(QWidget):
    """UV Sets 탭. `log(text)` 는 평문 한 줄, `log_html(html)` 은 색을 입힌 한 줄."""

    def __init__(self, log, log_html, parent=None):
        super().__init__(parent)
        self.log = log
        self.log_html = log_html
        self._build()

    # ==================================================================
    # UI
    # ==================================================================

    def _build(self):
        layout = QVBoxLayout(self)

        # 규칙 한 줄. 아래 이름 칸을 고치면 이 문장도 따라 바뀐다.
        self.lbl_rule = QLabel()
        self.lbl_rule.setAlignment(Qt.AlignCenter)
        self.lbl_rule.setWordWrap(True)
        layout.addWidget(self.lbl_rule)

        # ---- 오브젝트 목록 | UV Sets 표 --------------------------------
        self.tsl = JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Objects",
            show_reverse=True, list_min_height=150, log_callback=self.log)
        self.uv_table = UvSetTable()

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.tsl)
        split.addWidget(self.uv_table)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        layout.addWidget(split, 1)

        # 리스트가 바뀌면(Select / Add / Del / Up / Down / Sort / Catch) 표를 다시 그린다
        model = self.tsl.list_widget.model()
        for signal in (model.rowsInserted, model.rowsRemoved,
                       model.rowsMoved, model.modelReset):
            signal.connect(self.refresh_table)

        # ---- 동작 -----------------------------------------------------
        tool_box = QGroupBox("Tool")
        tool_layout = QVBoxLayout(tool_box)

        # 칸 하나가 세 버튼을 함께 정한다 — Catch 의 규칙 이름, Delete 가 남길 이름,
        # Rename 이 붙일 이름. 따로 두면 "잡아서 고쳤는데 여전히 위반" 이 된다.
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("UV set name"))
        self.le_uv_name = QLineEdit(uv_mgr.DEFAULT_UV_SET)
        self.le_uv_name.setPlaceholderText(uv_mgr.DEFAULT_UV_SET)
        self.le_uv_name.setToolTip(
            "The name a mesh should have - used by ALL buttons :\n"
            "  Catch Objects  : a mesh that does not have exactly this one set is caught\n"
            "  Delete UV Sets : every set with another name is deleted\n"
            "  Rename UV Set  : the first UV set is renamed to this\n\n"
            "Default is '{0}'. Maya accepts almost anything here (even spaces),\n"
            "but it refuses an empty name.".format(uv_mgr.DEFAULT_UV_SET))
        self.le_uv_name.textChanged.connect(self._sync_rule_label)
        self.le_uv_name.textChanged.connect(self.refresh_table)
        name_row.addWidget(self.le_uv_name, 1)

        self.btn_name_default = QPushButton("map1")
        self.btn_name_default.setFixedWidth(64)
        self.btn_name_default.setToolTip("Put the default name back.")
        self.btn_name_default.clicked.connect(
            lambda: self.le_uv_name.setText(uv_mgr.DEFAULT_UV_SET))
        name_row.addWidget(self.btn_name_default)
        tool_layout.addLayout(name_row)

        self.chk_scene_wide = QCheckBox("Catch : look at every mesh in the scene")
        self.chk_scene_wide.setChecked(True)
        self.chk_scene_wide.setToolTip(
            "On (default) : every mesh in the scene is checked.\n"
            "Off          : only the objects in the list above are checked.")
        tool_layout.addWidget(self.chk_scene_wide)

        self.chk_select_result = QCheckBox("Catch : select the offending meshes")
        self.chk_select_result.setChecked(True)
        self.chk_select_result.setToolTip(
            "Select what was caught in the scene, so you can look at it right away.")
        tool_layout.addWidget(self.chk_select_result)

        self.btn_catch = QPushButton("Catch Objects")
        self.btn_catch.setMinimumHeight(32)
        self.btn_catch.setToolTip(
            "List every mesh that breaks the rule and say WHY in the log.\n"
            "Nothing in the scene is changed.")
        self.btn_catch.clicked.connect(self.on_catch)
        tool_layout.addWidget(self.btn_catch)

        self.btn_delete = QPushButton("Delete UV Sets")
        self.btn_delete.setMinimumHeight(32)
        self.btn_delete.setToolTip(
            "Delete every UV set whose name is NOT the name typed above,\n"
            "on every listed object. One undo step.\n"
            "Maya cannot delete the default (first) UV set, so a mesh without\n"
            "that name is left alone - rename it first.")
        self.btn_delete.clicked.connect(self.on_delete)

        self.btn_rename = QPushButton("Rename UV Set")
        self.btn_rename.setMinimumHeight(32)
        self.btn_rename.setToolTip(
            "Rename the FIRST UV set of every listed object to the name typed above.\n"
            "The log shows the name before and after, one line per mesh.\n"
            "A mesh that already has a set with that name cannot be renamed -\n"
            "Maya refuses - and the log says so. One undo step.")
        self.btn_rename.clicked.connect(self.on_rename)

        edit_row = QHBoxLayout()
        edit_row.addWidget(self.btn_delete)
        edit_row.addWidget(self.btn_rename)
        tool_layout.addLayout(edit_row)

        layout.addWidget(tool_box)

        self._sync_rule_label()

    # ==================================================================
    # 표 · 규칙 문장
    # ==================================================================

    def refresh_table(self, *_args):
        """UV Sets 표를 리스트 항목 기준으로 다시 그린다. 씬은 바꾸지 않는다."""
        if not hasattr(self, "le_uv_name"):
            return      # 빌드 중
        wanted = self.le_uv_name.text().strip() or uv_mgr.DEFAULT_UV_SET
        nodes = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        self.uv_table.set_rows(uv_mgr.inspect(nodes, wanted), wanted)

    def _sync_rule_label(self, *_args):
        name = self.le_uv_name.text().strip() or uv_mgr.DEFAULT_UV_SET
        self.lbl_rule.setText(
            "One UV set per mesh, named '{0}'.\n"
            "Catch finds the meshes that break it, Delete / Rename fix them.".format(name))

    def _wanted_name(self):
        """세 버튼이 함께 쓰는 **원하는 UV 세트 이름**. 못 쓰는 이름이면 None."""
        ok, cleaned, message = uv_mgr.clean_name(self.le_uv_name.text())
        if not ok:
            self.log("[WARN] " + message)
            return None
        if message:
            self.log(message)
            self.le_uv_name.setText(cleaned)     # 화면과 동작이 어긋나지 않게
        return cleaned

    def _targets(self):
        """실행 대상 — **리스트가 먼저**, 비어 있으면 씬 선택(그 사실을 로그에 남긴다)."""
        nodes = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        if nodes:
            return nodes
        selected = cmds.ls(selection=True, long=True) or []
        if selected:
            self.log("The list is empty - using the {0} selected object(s) "
                     "instead.".format(len(selected)))
        return selected

    # ==================================================================
    # 동작
    # ==================================================================

    def on_catch(self):
        """규칙에 맞지 않는 메시를 찾아 **사유와 함께** 로그에 적고 리스트·씬에 담는다."""
        wanted = self._wanted_name()
        if wanted is None:
            return

        nodes = None
        if not self.chk_scene_wide.isChecked():
            nodes = self._targets()
            if not nodes:
                self.log("[WARN] Nothing to check - add objects to the list, or "
                         "tick 'look at every mesh in the scene'.")
                return

        offenders, checked = uv_mgr.find_offenders(nodes, wanted=wanted)

        where = "the scene" if nodes is None else "the list"
        self.log("Catch : checked {0} mesh(es) in {1}, wanting one '{2}'.".format(
            checked, where, wanted))

        if not checked:
            self.log("       No mesh found.")
            return
        if not offenders:
            self.log("       Every mesh follows the rule (one '{0}').".format(wanted))
            return

        for item in offenders:
            line = "  [{0}] {1} : {2}".format(
                item["status"], item["transform"].split("|")[-1], item["reason"])
            html = colored_log_line(line, item["status"])
            if html:
                self.log_html(html)      # [wrong_name] 은 빨간 줄
            else:
                self.log(line)

        transforms = list(dict.fromkeys(item["transform"] for item in offenders))
        self.log("       {0} mesh(es) break the rule, {1} object(s) listed.".format(
            len(offenders), len(transforms)))

        self.tsl.set_items(transforms)
        self.refresh_table()

        if self.chk_select_result.isChecked():
            cmds.select(transforms, replace=True)
            self.log("       Selected them in the scene.")

    def _log_records(self, records, wanted, changed_statuses, verb):
        """Delete / Rename 결과를 한 줄씩. 반환: (changed, untouched)."""
        changed = 0
        untouched = 0
        for record in records:
            name = (record["shape"] or record["node"] or "").split("|")[-1]
            before = ", ".join(record["before"]) or "-"
            after = ", ".join(record["after"]) or "-"
            status = record["status"]

            if status in changed_statuses:
                changed += 1
                if record["detail"]:
                    self.log("  [WARN] {0} : {1}  ->  {2}  ({3})".format(
                        name, before, after, record["detail"]))
                else:
                    self.log("  {0} : {1}  ->  {2}".format(name, before, after))
            elif status == uv_mgr.ALREADY:
                untouched += 1
                self.log("  {0} : {1}  (already fine for '{2}', left alone)".format(
                    name, before, wanted))
            else:
                untouched += 1
                detail = record["detail"] or uv_mgr.REASONS.get(status, status).format(
                    count=len(record["before"]),
                    sets=", ".join(record["before"]) or "-",
                    first=record["before"][0] if record["before"] else "-",
                    default=wanted)
                self.log("  [WARN] {0} : {1}  (not {2} - {3})".format(
                    name, before, verb, detail))
        return changed, untouched

    def on_delete(self):
        """입력한 이름이 **아닌** UV 세트를 지우고 before -> after 를 한 줄씩 적는다."""
        wanted = self._wanted_name()
        if wanted is None:
            return
        nodes = self._targets()
        if not nodes:
            self.log("[WARN] Nothing to delete from - list the objects first "
                     "(Catch Objects, or Select Objects).")
            return

        self.log("Delete : every UV set except '{0}' on {1} object(s).".format(
            wanted, len(nodes)))
        records = uv_mgr.delete_other_uv_sets(nodes, keep=wanted)
        changed, untouched = self._log_records(
            records, wanted, (uv_mgr.DELETED, uv_mgr.PARTIAL), "deleted")

        self.log("       {0} changed, {1} left as they were.".format(changed, untouched))
        if changed:
            self.log("       Ctrl+Z undoes the whole run.")
        self.refresh_table()

    def on_rename(self):
        """첫 UV 세트를 **입력한 이름**으로 바꾸고 어떻게 바뀌었는지 한 줄씩 적는다."""
        wanted = self._wanted_name()
        if wanted is None:
            return
        nodes = self._targets()
        if not nodes:
            self.log("[WARN] Nothing to rename - list the objects first "
                     "(Catch Objects, or Select Objects).")
            return

        self.log("Rename : first UV set -> '{0}' on {1} object(s).".format(
            wanted, len(nodes)))
        records = uv_mgr.rename_first_uv_set(nodes, new_name=wanted)
        changed, untouched = self._log_records(
            records, wanted, (uv_mgr.RENAMED,), "renamed")

        self.log("       {0} renamed, {1} left as they were.".format(changed, untouched))
        if changed:
            self.log("       Ctrl+Z undoes the whole run.")
        self.refresh_table()
