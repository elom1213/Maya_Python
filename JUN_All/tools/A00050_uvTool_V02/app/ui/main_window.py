# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
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
# 로직은 `app/core/uv_set_manager.py` 에 있고 여기서는 화면과 로그만 다룬다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QCheckBox,
    QMessageBox,
    QPushButton,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt import JUN_mod_tsl_qt

from tools.A00050_uvTool_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00050_uvTool_V02.app.core import uv_set_manager as uv_mgr


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00050_uvTool_V02_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("UV Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        # 최소 크기(533 x 736)보다 조금 넉넉하게 — 로그가 몇 줄 보이도록.
        self.resize(560, 780)

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

        rule = QLabel(
            "One UV set per mesh, named '{0}'.\n"
            "Catch finds the meshes that break it, Rename fixes the name.".format(
                uv_mgr.DEFAULT_UV_SET))
        rule.setAlignment(Qt.AlignCenter)
        rule.setWordWrap(True)
        main_layout.addWidget(rule)

        # ---- 오브젝트 목록 --------------------------------------------
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Objects",
            show_reverse=True, list_min_height=150, log_callback=self.log)
        main_layout.addWidget(self.tsl, 1)

        # ---- 동작 -----------------------------------------------------
        tool_box = QGroupBox("Tool")
        tool_layout = QVBoxLayout(tool_box)

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
            "Rename the FIRST UV set of every listed object to '{0}'.\n"
            "The log shows the name before and after, one line per mesh.\n"
            "A mesh that already has a '{0}' cannot be renamed - Maya refuses -\n"
            "and the log says so. One undo step.".format(uv_mgr.DEFAULT_UV_SET))
        self.btn_rename.clicked.connect(self.on_rename)
        tool_layout.addWidget(self.btn_rename)

        main_layout.addWidget(tool_box)

        # ---- 로그 -----------------------------------------------------
        self.log_view = JUN_mod_log_qt_v01(
            window_title="UV Tool - Log",
            object_name="JUN_A00050_uvTool_V02_log_window")
        self.log_view.setFixedHeight(140)
        main_layout.addWidget(self.log_view)

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        self.log_view.appendPlainText(message)

    # ==================================================================
    # 동작
    # ==================================================================

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
        nodes = None

        if not self.chk_scene_wide.isChecked():
            nodes = self._targets()
            if not nodes:
                self.log("[WARN] Nothing to check - add objects to the list, or "
                         "tick 'look at every mesh in the scene'.")
                return

        offenders, checked = uv_mgr.find_offenders(nodes)

        where = "the scene" if nodes is None else "the list"
        self.log("Catch : checked {0} mesh(es) in {1}.".format(checked, where))

        if not checked:
            self.log("       No mesh found.")
            return

        if not offenders:
            self.log("       Every mesh follows the rule (one '{0}').".format(
                uv_mgr.DEFAULT_UV_SET))
            return

        for item in offenders:
            self.log("  [{0}] {1} : {2}".format(
                item["status"], item["transform"].split("|")[-1], item["reason"]))

        transforms = list(dict.fromkeys(item["transform"] for item in offenders))

        self.log("       {0} mesh(es) break the rule, {1} object(s) listed.".format(
            len(offenders), len(transforms)))

        self.tsl.set_items(transforms)

        if self.chk_select_result.isChecked():
            import maya.cmds as cmds
            cmds.select(transforms, replace=True)
            self.log("       Selected them in the scene.")

    def on_rename(self):
        """첫 UV 세트를 map1 으로 바꾸고 **이름이 어떻게 바뀌었는지** 한 줄씩 적는다."""
        nodes = self._targets()

        if not nodes:
            self.log("[WARN] Nothing to rename - list the objects first "
                     "(Catch Objects, or Select Objects).")
            return

        records = uv_mgr.rename_first_uv_set(nodes)

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
                    name, before, uv_mgr.DEFAULT_UV_SET))
            else:
                untouched += 1
                detail = record["detail"] or uv_mgr.REASONS.get(status, status).format(
                    count=len(record["before"]),
                    sets=", ".join(record["before"]) or "-",
                    first=record["before"][0] if record["before"] else "-",
                    default=uv_mgr.DEFAULT_UV_SET)
                self.log("  [WARN] {0} : {1}  (not renamed - {2})".format(
                    name, before, detail))

        self.log("Rename : {0} renamed, {1} left as they were.".format(
            renamed, untouched))

        if renamed:
            self.log("       Ctrl+Z undoes the whole run.")

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
            "A mesh should have exactly ONE UV set, named '{0}'.\n\n"
            "Caught as broken :\n"
            "  multiple    two or more UV sets\n"
            "  wrong_name  a single set with another name\n"
            "  no_uv       no UV set at all\n\n"
            "Rename UV Set renames the FIRST set to '{0}'.\n"
            "It cannot rename when the mesh already has a '{0}' - Maya refuses -\n"
            "and it never deletes a UV set (Maya does not allow deleting the "
            "default one).".format(uv_mgr.DEFAULT_UV_SET),
        )
