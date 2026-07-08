# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00360_SortTool - Qt UI
#
# 선택 오브젝트를 TSL 에 리스트업하고 월드 X/Y/Z 위치 · 이름 · 타입 기준으로 정렬해
# 아웃라이너 순서(위->아래)와 TSL 순서를 함께 바꾼다. 아웃라이너 재정렬은 체크박스로
# on/off(기본 on). 위치를 가진 노드면 조인트/메시/커브/클러스터/래티스 핸들 등 무엇이든 동작.
# 정렬 기준(이름/타입)과 순서 방식은 AriSortOutliner.mel 을 참고했다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00360_SortTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00360_SortTool.app.core import sort_manager as sort_mgr


WINDOW_OBJECT_NAME = "JUN_A00360_SortTool_window"

# 정렬 기준 라디오 (label, mode). 2행 x 3열 그리드로 배치.
_SORT_MODES = [
    ("World X", sort_mgr.MODE_X),
    ("World Y", sort_mgr.MODE_Y),
    ("World Z", sort_mgr.MODE_Z),
    ("Name", sort_mgr.MODE_NAME),
    ("Type", sort_mgr.MODE_TYPE),
]

_WARN_COLOR = "#ffb454"


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Sort Tool v{0}".format(VERSION)
        self.resize(340, 560)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        # 메뉴 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # 대상 오브젝트 리스트(TSL). Sort 버튼은 툴이 직접 제공하므로 위젯 내장 Sort 는 끔.
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Objects",
            show_sort=False, list_min_height=200, log_callback=self.log)
        root.addWidget(self.tsl, 1)

        # 정렬 기준 라디오
        box = QGroupBox("Sort By")
        grid = QGridLayout(box)
        self.rb_group = QButtonGroup(self)
        for i, (label, mode) in enumerate(_SORT_MODES):
            rb = QRadioButton(label)
            rb.setProperty("mode", mode)
            if i == 0:
                rb.setChecked(True)
            self.rb_group.addButton(rb, i)
            grid.addWidget(rb, i // 3, i % 3)
        root.addWidget(box)

        # 옵션
        self.chk_reverse = QCheckBox("Reverse (descending)")
        self.chk_reverse.setToolTip("Sort large->small (top of outliner = largest).")
        root.addWidget(self.chk_reverse)

        self.chk_reorder = QCheckBox("Reorder in Outliner")
        self.chk_reorder.setChecked(True)
        self.chk_reorder.setToolTip(
            "On: also change the outliner order (top->bottom).\n"
            "Off: only reorder this list, leave the outliner untouched.")
        root.addWidget(self.chk_reorder)

        # Sort 실행
        self.btn_sort = QPushButton("Sort")
        self.btn_sort.setMinimumHeight(38)
        self.btn_sort.clicked.connect(self.on_sort)
        root.addWidget(self.btn_sort)

        # 로그
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(110)
        root.addWidget(self.te_log)

        self.log("Sort Tool v{0} ({1}) ready. Select objects and click "
                 "'Select Objects'.".format(VERSION, LAST_UPDATE))

    # ==============================================================
    # actions
    # ==============================================================

    def _current_mode(self):
        btn = self.rb_group.checkedButton()
        return btn.property("mode") if btn else sort_mgr.MODE_X

    def _mode_label(self, mode):
        for label, m in _SORT_MODES:
            if m == mode:
                return label
        return mode

    def on_sort(self):
        items = self.tsl.get_all_items()
        if not items:
            self.log("List is empty. Select objects and click 'Select Objects'.", warn=True)
            return

        mode = self._current_mode()
        reverse = self.chk_reverse.isChecked()
        reorder = self.chk_reorder.isChecked()

        try:
            with undo_chunk():
                ordered, missing = sort_mgr.sort_objects(
                    items, mode, reverse=reverse, reorder_outliner=reorder)
        except Exception as e:
            self.log("Sort failed: {0}".format(e), warn=True)
            return

        # TSL 을 정렬 순서로 재구성(위->아래). 해석 못 한 항목은 맨 아래에 남긴다.
        self.tsl.set_items(ordered + missing)

        order_txt = "descending" if reverse else "ascending"
        where = "outliner + list" if reorder else "list only"
        self.log("Sorted {0} object(s) by {1} ({2}, {3}).".format(
            len(ordered), self._mode_label(mode), order_txt, where))
        if missing:
            self.log("Skipped {0} (not found / no position): {1}".format(
                len(missing), ", ".join(missing)), warn=True)

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def log(self, text, warn=False):
        if warn:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(_WARN_COLOR, self._esc(text)))
        else:
            self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Sort Tool\nv{0}  ({1})\n\n"
            "Sort listed objects by world X/Y/Z position, name, or type and\n"
            "reorder them in the outliner (top->bottom).\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
