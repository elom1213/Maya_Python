# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00030_quickTool_V02 - Qt UI (in-Maya)
#
# 레거시 maya.cmds 툴 `A00030_quickTool`(V01.16) 을 PySide 로 재작성했다.
# **버튼과 동작은 그대로**고, 달라진 것은 그릇이다.
#   - 로직은 `app/core/quick_ops.py` 로 분리(UI 비의존). UI 는 버튼을 그리고 로그를 받는다.
#   - 결과를 `print` / `cmds.warning` 대신 **공용 로그창**(Expand / Clear / Copy)에 쌓는다.
#     스크립트 에디터를 안 열어도 결과가 보인다.
#   - Pin(항상 위)은 레거시가 창을 Qt 위젯으로 감싸서 하던 것을, 이제 창이 Qt 라 바로 한다.
#
# 버튼 구성(레거시 그대로) — 섹션 6 / 버튼 10:
#   Update window : Selected · All Windows
#   Print         : Print Selected · Print Hierarchy
#   Import option : Import FBX normal
#   Create        : Create texture file · Cluster Each
#   File          : Copy Scene Folder
#   Shelf         : Update Shelves  (v02.01~ 신규 - 레거시에 없던 것)
#   Display       : Local Axis ON · Local Axis OFF
#
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QApplication,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

from tools.A00030_quickTool_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00030_quickTool_V02.app import core


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00030_quickTool_V02_window"


class MainWindow(QWidget):

    # ==================================================================
    # 버튼 표 — (섹션 제목, [(라벨, 핸들러 이름, 툴팁), ...])
    # ==================================================================
    # ★ 버튼을 더하거나 옮기는 일은 **이 표 한 줄**이다. 레거시는 인덱스 상수
    #   (idx_updateWin ... idx_display)와 중첩 리스트로 짝을 맞춰야 했다.
    SECTIONS = (
        ("Update window", (
            ("Selected", "on_view_selected",
             "Refresh only the active viewport while playing - faster on heavy scenes."),
            ("All Windows", "on_view_all",
             "Refresh every viewport while playing (Maya default)."),
        )),
        ("Print", (
            ("Print Selected", "on_print_selected",
             "Log the names of the current selection."),
            ("Print Hierarchy", "on_print_hierarchy",
             "Log the parent/child tree of the selection.\n"
             "Objects already inside another printed tree are skipped."),
        )),
        ("Import option", (
            ("Import FBX normal", "on_import_fbx_normal",
             "Make FBX import use the normals stored in the file.\n"
             "This is a global FBX setting - it applies to the next import."),
        )),
        ("Create", (
            ("Create texture file", "on_create_texture_file",
             "Create a file node wired to a place2dTexture, the way Hypershade does it."),
            ("Cluster Each", "on_create_cluster_each",
             "One cluster per selected object (cmds.cluster would make a single "
             "cluster for the whole selection)."),
        )),
        ("File", (
            ("Copy Scene Folder", "on_copy_scene_folder",
             "Copy the folder of the current scene to the clipboard."),
        )),
        ("Shelf", (
            ("Update Shelves", "on_update_shelves",
             "Write the current shelves to disk right now.\n"
             "Maya only saves shelves when it quits, so a Maya started while this "
             "one is open\nwould read the old files. Press this and the next Maya "
             "sees your shelves."),
        )),
        ("Display", (
            ("Local Axis ON", "on_local_axis_on",
             "Show the local rotation axes of every selected object."),
            ("Local Axis OFF", "on_local_axis_off",
             "Hide them. Objects already in that state are left alone."),
        )),
    )

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Quick Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(360, 620)

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Pin 토글(우)
        # 코너 위젯 대신 QHBoxLayout 으로 배치해 토글 시 위치/크기가 고정되도록 한다.
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        # 고정 크기 - "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록(넓은 라벨 기준).
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 공용 로그창 (섹션 빌더가 self._log 를 참조하므로 먼저 만든다)
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Quick Tool - Log",
            object_name="JUN_A00030_quickTool_V02_log_window")
        self.log_view.setMinimumHeight(90)
        self.log_view.setMaximumHeight(160)

        # 섹션들
        self.buttons = {}
        for title, specs in self.SECTIONS:
            main_layout.addWidget(self._build_section(title, specs))

        main_layout.addStretch(1)
        main_layout.addWidget(self.log_view)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    def _build_section(self, title, specs):
        """섹션 하나 - 버튼을 **두 칸 그리드**로 담는다.

        레거시가 `paneLayout(configuration="vertical2")` 로 두 칸씩 놓던 모양 그대로다.
        버튼이 하나뿐인 섹션은 그 칸이 **가로를 다 쓴다**(레거시와 같다).
        """
        box = QGroupBox(title)
        grid = QGridLayout(box)

        for index, (label, handler, tip) in enumerate(specs):
            button = QPushButton(label)
            button.setToolTip(tip)
            button.clicked.connect(getattr(self, handler))
            self.buttons[label] = button

            row, column = divmod(index, 2)
            if len(specs) == 1:
                grid.addWidget(button, row, 0, 1, 2)
            else:
                grid.addWidget(button, row, column)

        return box

    # ==================================================================
    # Handlers - 코어를 부르고 돌려받은 로그를 창에 쌓는다
    # ==================================================================

    def on_view_selected(self):
        self._log_all(core.set_playback_view(True))

    def on_view_all(self):
        self._log_all(core.set_playback_view(False))

    def on_print_selected(self):
        _names, logs = core.selected_names()
        self._log_all(logs)

    def on_print_hierarchy(self):
        text, logs = core.print_hierarchy()
        if text:
            # 트리는 여러 줄이라 로그에 그대로 붙인다(Expand 로 크게 볼 수 있다).
            self._log_all(text.splitlines())
        self._log_all(logs)

    def on_import_fbx_normal(self):
        self._log_all(core.import_fbx_normal())

    def on_create_texture_file(self):
        _file_node, _place, logs = core.create_texture_file()
        self._log_all(logs)

    def on_create_cluster_each(self):
        _handles, logs = core.create_cluster_each()
        self._log_all(logs)

    def on_copy_scene_folder(self):
        """씬 폴더를 클립보드로. 경로를 찾는 것은 코어, 복사는 여기(Qt)."""
        folder, logs = core.scene_folder()
        self._log_all(logs)
        if not folder:
            return

        clipboard = QApplication.clipboard()
        if clipboard is None:
            self._log("[WARN] Could not access the system clipboard.")
            return

        clipboard.setText(folder)
        self._log("Copied to clipboard : {0}".format(folder))

    def on_update_shelves(self):
        self._log_all(core.save_all_shelves())

    def on_local_axis_on(self):
        self._log_all(core.set_local_axis(True))

    def on_local_axis_off(self):
        self._log_all(core.set_local_axis(False))

    # ==================================================================
    # Helper / About
    # ==================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)

    def toggle_always_on_top(self, enabled):
        # WindowStaysOnTopHint 를 켜고/끄고, 플래그 변경 후 다시 show() (안 하면 창이 사라짐)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self._log("Always on Top : {0}".format("ON" if enabled else "OFF"))

    def show_about(self, *args):
        message = (
            "Quick Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "PySide rewrite of the legacy A00030_quickTool (V01.16).\n"
            "Same buttons, same behaviour - the results now go to the log\n"
            "instead of the script editor.\n"
            "\n"
            "[Update window] Selected / All Windows - which viewports refresh\n"
            "  while playing.\n"
            "[Print] Print Selected / Print Hierarchy - names and the parent tree.\n"
            "[Import option] Import FBX normal - use the normals in the file.\n"
            "[Create] Create texture file / Cluster Each.\n"
            "[File] Copy Scene Folder - the scene's folder to the clipboard.\n"
            "[Shelf] Update Shelves - write the shelves to disk now, so a Maya\n"
            "  started later sees them (Maya only saves them on exit).\n"
            "[Display] Local Axis ON / OFF - batch show or hide local axes.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
