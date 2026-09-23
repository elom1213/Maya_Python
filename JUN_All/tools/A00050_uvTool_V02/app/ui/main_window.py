# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
# A00050_uvTool_V02 - Qt UI (in-Maya)
#
# V01(`A00050_uvTool`, maya.cmds UI)을 **PySide 로 옮긴 버전**이다. 하는 일은 같다 —
# UV 세트가 규칙(`map1` 하나)에 어긋난 메시를 찾고, 첫 UV 세트의 이름을 `map1` 로 고친다.
#
# 옮기면서 달라진 것은 **무슨 일이 일어났는지 말해 준다**는 점이다.
#   * `Catch Objects` : 어떤 메시가 **왜** 규칙에 어긋나는지 한 줄씩 로그로 적고,
#                       그 메시들을 **씬에서 선택**한다(V01 은 리스트만 채웠다).
#   * `Rename UV Set` : 이름이 **어떻게 바뀌었는지**(before -> after) 한 줄씩 적고,
#                       못 바꾼 것은 **사유**를 적는다(V01 은 조용히 넘어갔다).
#
# ── 이름 칸 (v02.01) ──────────────────────────────────────────────────────
# 바꿀 이름을 **화면에서 입력**한다(기본 `map1`). 칸 하나가 **두 버튼을 함께** 정한다 —
# `Rename` 이 붙일 이름이자 `Catch` 가 규칙으로 삼는 이름이다. 둘을 따로 두면
# "잡아서 고쳤는데 여전히 위반" 이 되어 버린다. 규칙 문장도 입력에 따라 같이 바뀐다.
#
# ── UV Sets 표 (v02.02) ───────────────────────────────────────────────────
# 리스트 옆에 **오브젝트 · UV 세트 이름들 · 규칙 판정** 세 칸짜리 표를 둔다
# (A00330_NamingTool Quick Rename > Insert 의 Preview 와 같은 형식). 리스트 · 이름 칸이
# 바뀔 때, Catch · Rename 뒤에 다시 그린다. 로그의 `[wrong_name]` 줄은 빨간색.
# 표는 `app/ui/uv_set_table.py`, 행 데이터는 코어 `inspect()` - A00380_MeshTool 로
# 옮길 때 두 파일을 그대로 가져가면 된다.
#
# 로직은 `app/core/uv_set_manager.py` 에 있고 여기서는 화면과 로그만 다룬다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QCheckBox,
    QMessageBox,
    QPushButton,
    QSplitter,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt import JUN_mod_tsl_qt

from tools.A00050_uvTool_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00050_uvTool_V02.app.core import uv_set_manager as uv_mgr
from tools.A00050_uvTool_V02.app.ui.uv_set_table import UvSetTable, colored_log_line


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00050_uvTool_V02_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("UV Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        # 최소 크기(533 x 772)보다 넉넉하게 — 로그가 몇 줄 보이도록.
        # 가로는 리스트 옆 UV Sets 표(세 칸)가 보이도록 넓혔다(v02.02, 560 -> 720).
        # 최소 폭은 그대로라 줄이면 표가 가로 스크롤된다.
        self.resize(720, 820)

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        help_menu.addAction("The Rule").triggered.connect(self.show_rule)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 규칙 한 줄. 아래 이름 칸을 고치면 이 문장도 따라 바뀐다(v02.01).
        self.lbl_rule = QLabel()
        self.lbl_rule.setAlignment(Qt.AlignCenter)
        self.lbl_rule.setWordWrap(True)
        main_layout.addWidget(self.lbl_rule)

        # ---- 오브젝트 목록 | UV Sets 표 (v02.02) -------------------------
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Objects",
            show_reverse=True, list_min_height=150, log_callback=self.log)

        self.uv_table = UvSetTable()

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.tsl)
        split.addWidget(self.uv_table)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        main_layout.addWidget(split, 1)

        # 리스트가 바뀌면(Select / Add / Del / Up / Down / Sort / Catch) 표를 다시 그린다
        model = self.tsl.list_widget.model()
        for signal in (model.rowsInserted, model.rowsRemoved,
                       model.rowsMoved, model.modelReset):
            signal.connect(self._refresh_table)

        # ---- 동작 -----------------------------------------------------
        tool_box = QGroupBox("Tool")
        tool_layout = QVBoxLayout(tool_box)

        # ---- 원하는 UV 세트 이름 (v02.01) -----------------------------
        # 하나의 칸이 **두 버튼을 함께** 정한다 — Rename 이 붙일 이름이자, Catch 가
        # 규칙으로 삼는 이름이다. 둘이 다르면 "잡은 것을 고쳤는데 여전히 위반" 이 된다.
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("UV set name"))

        self.le_uv_name = QLineEdit(uv_mgr.DEFAULT_UV_SET)
        self.le_uv_name.setPlaceholderText(uv_mgr.DEFAULT_UV_SET)
        self.le_uv_name.setToolTip(
            "The name a mesh should have - used by BOTH buttons :\n"
            "  Catch Objects : a mesh that does not have exactly this one set is caught\n"
            "  Rename UV Set : the first UV set is renamed to this\n\n"
            "Default is '{0}'. Maya accepts almost anything here (even spaces),\n"
            "but it refuses an empty name.".format(uv_mgr.DEFAULT_UV_SET))
        self.le_uv_name.textChanged.connect(self._sync_rule_label)
        self.le_uv_name.textChanged.connect(self._refresh_table)
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
            "On (default) : every mesh in the scene is checked (what V01 did).\n"
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

        self.btn_rename = QPushButton("Rename UV Set")
        self.btn_rename.setMinimumHeight(32)
        self.btn_rename.setToolTip(
            "Rename the FIRST UV set of every listed object to the name typed above.\n"
            "The log shows the name before and after, one line per mesh.\n"
            "A mesh that already has a set with that name cannot be renamed -\n"
            "Maya refuses - and the log says so. One undo step.")
        self.btn_rename.clicked.connect(self.on_rename)

        # Delete UV Sets (v02.03) - Rename 의 왼쪽
        self.btn_delete = QPushButton("Delete UV Sets")
        self.btn_delete.setMinimumHeight(32)
        self.btn_delete.setToolTip(
            "Delete every UV set whose name is NOT the name typed above,\n"
            "on every listed object. One undo step.\n"
            "Maya cannot delete the default (first) UV set, so a mesh without\n"
            "that name is left alone - rename it first.")
        self.btn_delete.clicked.connect(self.on_delete)

        edit_row = QHBoxLayout()
        edit_row.addWidget(self.btn_delete)
        edit_row.addWidget(self.btn_rename)
        tool_layout.addLayout(edit_row)

        main_layout.addWidget(tool_box)

        # ---- 로그 -----------------------------------------------------
        self.log_view = JUN_mod_log_qt_v01(
            window_title="UV Tool - Log",
            object_name="JUN_A00050_uvTool_V02_log_window")
        self.log_view.setFixedHeight(140)
        main_layout.addWidget(self.log_view)

        # 규칙 문장을 처음 한 번 채운다(이름 칸이 만들어진 뒤라야 한다).
        self._sync_rule_label()

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        self.log_view.appendPlainText(message)

    def _refresh_table(self, *_args):
        """UV Sets 표를 리스트 항목 기준으로 다시 그린다. 씬은 바꾸지 않는다."""
        if not hasattr(self, "le_uv_name"):
            return      # 빌드 중
        wanted = self.le_uv_name.text().strip() or uv_mgr.DEFAULT_UV_SET
        nodes = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        self.uv_table.set_rows(uv_mgr.inspect(nodes, wanted), wanted)

    # ==================================================================
    # 동작
    # ==================================================================

    def _sync_rule_label(self, *_args):
        """규칙 문장을 지금 입력한 이름으로 갱신한다(빈 칸이면 기본값을 보여 준다)."""
        name = self.le_uv_name.text().strip() or uv_mgr.DEFAULT_UV_SET

        self.lbl_rule.setText(
            "One UV set per mesh, named '{0}'.\n"
            "Catch finds the meshes that break it, Delete / Rename fix them.".format(name))

    def _wanted_name(self):
        """두 버튼이 함께 쓰는 **원하는 UV 세트 이름**. 못 쓰는 이름이면 None.

        마야가 거절하는 것은 빈 이름뿐이라, 다듬기도 그 선에서 멈춘다.
        """
        ok, cleaned, message = uv_mgr.clean_name(self.le_uv_name.text())

        if not ok:
            self.log("[WARN] " + message)
            return None

        if message:
            self.log(message)
            # 다듬은 값을 칸에도 되돌려 준다 - 화면과 동작이 어긋나지 않게.
            self.le_uv_name.setText(cleaned)

        return cleaned

    def _targets(self):
        """실행 대상 — **리스트가 먼저**, 비어 있으면 씬 선택(그 사실을 로그에 남긴다).

        V01 은 씬 선택을 먼저 봤는데, 리스트를 채워 두고 눌렀을 때 **무엇이 대상인지
        화면으로 알 수 없었다.** 지금은 보이는 것(리스트)이 대상이다.
        """
        nodes = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        if nodes:
            return nodes

        import maya.cmds as cmds
        selected = cmds.ls(selection=True, long=True) or []
        if selected:
            self.log("The list is empty - using the {0} selected object(s) "
                     "instead.".format(len(selected)))

        return selected

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
                # 로그창은 `<` 가 든 줄을 툴이 쓴 HTML 로 보고 그대로 받는다
                self.log_view.append(html)
            else:
                self.log(line)

        transforms = list(dict.fromkeys(item["transform"] for item in offenders))

        self.log("       {0} mesh(es) break the rule, {1} object(s) listed.".format(
            len(offenders), len(transforms)))

        self.tsl.set_items(transforms)
        # 같은 목록이면 rows 신호가 안 올 수도 있다 - 확실히 다시 그린다
        self._refresh_table()

        if self.chk_select_result.isChecked():
            import maya.cmds as cmds
            cmds.select(transforms, replace=True)
            self.log("       Selected them in the scene.")

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

        renamed = 0
        untouched = 0

        for record in records:
            name = (record["shape"] or record["node"] or "").split("|")[-1]
            before = ", ".join(record["before"]) or "-"
            after = ", ".join(record["after"]) or "-"
            status = record["status"]

            if status == uv_mgr.RENAMED:
                renamed += 1
                self.log("  {0} : {1}  ->  {2}".format(name, before, after))
            elif status == uv_mgr.ALREADY:
                untouched += 1
                self.log("  {0} : {1}  (already '{2}', left alone)".format(
                    name, before, wanted))
            else:
                untouched += 1
                detail = record["detail"] or uv_mgr.REASONS.get(status, status).format(
                    count=len(record["before"]),
                    sets=", ".join(record["before"]) or "-",
                    first=record["before"][0] if record["before"] else "-",
                    default=wanted)
                self.log("  [WARN] {0} : {1}  (not renamed - {2})".format(
                    name, before, detail))

        self.log("       {0} renamed, {1} left as they were.".format(
            renamed, untouched))

        if renamed:
            self.log("       Ctrl+Z undoes the whole run.")

        # 이름이 바뀌었으니 표도 다시 (리스트는 그대로라 신호가 오지 않는다)
        self._refresh_table()

    def on_delete(self):
        """입력한 이름이 **아닌** UV 세트를 지우고 before -> after 를 한 줄씩 적는다 (v02.03)."""
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

        changed = 0
        untouched = 0

        for record in records:
            name = (record["shape"] or record["node"] or "").split("|")[-1]
            before = ", ".join(record["before"]) or "-"
            after = ", ".join(record["after"]) or "-"
            status = record["status"]

            if status == uv_mgr.DELETED:
                changed += 1
                self.log("  {0} : {1}  ->  {2}".format(name, before, after))
            elif status == uv_mgr.PARTIAL:
                changed += 1
                self.log("  [WARN] {0} : {1}  ->  {2}  ({3})".format(
                    name, before, after, record["detail"]))
            elif status == uv_mgr.ALREADY:
                untouched += 1
                self.log("  {0} : {1}  (only '{2}', nothing to delete)".format(
                    name, before, wanted))
            else:
                untouched += 1
                detail = record["detail"] or uv_mgr.REASONS.get(status, status).format(
                    count=len(record["before"]),
                    sets=", ".join(record["before"]) or "-",
                    first=record["before"][0] if record["before"] else "-",
                    default=wanted)
                self.log("  [WARN] {0} : {1}  (nothing deleted - {2})".format(
                    name, before, detail))

        self.log("       {0} changed, {1} left as they were.".format(changed, untouched))

        if changed:
            self.log("       Ctrl+Z undoes the whole run.")

        self._refresh_table()

    # ==================================================================
    # 창 동작
    # ==================================================================

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")

        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "UV Tool v{0}\nLast update : {1}\n\n"
            "Written by Ji Hun Park.\n"
            "PySide port of A00050_uvTool (V01).".format(VERSION, LAST_UPDATE),
        )

    def show_rule(self):
        QMessageBox.information(
            self,
            "The Rule",
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
            "Maya refuses - and it never deletes a UV set (Maya does not allow\n"
            "deleting the default one).".format(uv_mgr.DEFAULT_UV_SET),
        )
