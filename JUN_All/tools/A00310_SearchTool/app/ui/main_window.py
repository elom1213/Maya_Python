# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-26
# A00310_SearchTool - Qt UI
#
# 레거시 maya.cmds 툴 두 개를 하나의 창 + QTabWidget 으로 통합한다.
#   - Selection 탭 : JUN_PY_SelectionTool_V02_01 이식 (타입/오브젝트 리스트업 + 타입별 선택)
#   - Search    탭 : JUN_PY_SearchTool_V01_02 이식 (이름 토큰으로 검색 선택)
# 두 탭의 위젯/핸들러는 접두사(sel_ / sch_)로 분리하고, 로그/메뉴/푸터는 공유한다.
# 리스트 UI 는 공용 위젯 JUN_mod_tsl_qt_v01(Select/Add/Del/Up/Down/Sort), 로직은 app/core.
# 모든 UI 문자열/로그는 영어.

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

from tools.A00310_SearchTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00310_SearchTool.app.core import (
    MayaScene,
    CONSTRAINT_TYPES,
    collect_from_selection,
    collect_types,
    select_by_types,
    select_by_token,
)


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00310_SearchTool_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Search Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 720)

        self.build_ui()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 공용 로그창 (탭 빌더가 self._log / TSL log_callback 을 쓰므로 탭보다 먼저 생성)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(110)

        # 탭: Selection / Search
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_selection_tab(), "Selection")
        self.tabs.addTab(self._build_search_tab(), "Search")
        main_layout.addWidget(self.tabs)

        # 로그창
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    def _build_option_row(self, prefix):
        """Hierarchy/Selected 라디오 + Invert 체크박스 한 줄. (radio, invert) 를 반환."""
        row = QHBoxLayout()
        row.addWidget(QLabel("Source"))

        rb_hierarchy = QRadioButton("Hierarchy")
        rb_selected = QRadioButton("Selected")
        rb_hierarchy.setChecked(True)
        rb_hierarchy.setToolTip(
            "Hierarchy: expand each selected object to its descendant "
            "transforms. Selected: use the raw selection only.")
        group = QButtonGroup(self)
        group.addButton(rb_hierarchy)
        group.addButton(rb_selected)
        row.addWidget(rb_hierarchy)
        row.addWidget(rb_selected)

        row.addStretch(1)

        cb_invert = QCheckBox("Invert")
        cb_invert.setToolTip(
            "Select the complement: everything in the Objects list that does "
            "NOT match.")
        row.addWidget(cb_invert)

        # 핸들러에서 참조하도록 보관
        setattr(self, prefix + "_rb_hierarchy", rb_hierarchy)
        setattr(self, prefix + "_cb_invert", cb_invert)
        return row

    # ================================================================
    # Tab : Selection  (JUN_PY_SelectionTool_V02_01 이식)
    # ================================================================

    def _build_selection_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # 옵션 (Hierarchy/Selected + Invert)
        root.addLayout(self._build_option_row("sel"))

        # Types | Objects (좌우)
        self.sel_types_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Types", show_select=False, show_add=False,
            log_callback=self._log)
        # 'List Types' : 선택/계층에서 노드 타입을 모아 채운다(편집 행 맨 앞).
        self.sel_types_tsl.add_button(
            "List Types", self.on_sel_list_types, index=0)

        self.sel_objs_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", show_select=False, log_callback=self._log)
        # 'Get' : 선택/계층의 오브젝트로 리스트를 채운다(편집 행 맨 앞).
        self.sel_objs_tsl.add_button("Get", self.on_sel_get_objects, index=0)

        list_row = QHBoxLayout()
        list_row.addWidget(self.sel_types_tsl)
        list_row.addWidget(self.sel_objs_tsl)
        root.addLayout(list_row, stretch=1)

        # Select By Shape (고정 타입 버튼)
        shape_box = QGroupBox("Select By Shape (from the Objects list)")
        shape_layout = QVBoxLayout(shape_box)
        r1 = QHBoxLayout()
        for label, type_name in (("Mesh", "mesh"),
                                 ("nurbsCurve", "nurbsCurve")):
            btn = QPushButton(label)
            btn.clicked.connect(
                lambda _checked=False, t=type_name: self.on_sel_by_shape(t))
            r1.addWidget(btn)
        shape_layout.addLayout(r1)
        r2 = QHBoxLayout()
        btn_joint = QPushButton("Joint")
        btn_joint.clicked.connect(
            lambda _checked=False: self.on_sel_by_shape("joint"))
        r2.addWidget(btn_joint)
        btn_con = QPushButton("Constraint")
        btn_con.clicked.connect(
            lambda _checked=False: self.on_sel_by_shape(CONSTRAINT_TYPES))
        r2.addWidget(btn_con)
        shape_layout.addLayout(r2)
        root.addWidget(shape_box)

        # Select By Type (Types 리스트에서 선택된 타입들로 매칭)
        btn_by_type = QPushButton("Select By Type (use selected types)")
        btn_by_type.setMinimumHeight(32)
        btn_by_type.setToolTip(
            "Select objects whose node type is among the types you have "
            "selected in the Types list.")
        btn_by_type.clicked.connect(self.on_sel_by_type)
        root.addWidget(btn_by_type)

        return tab

    def _selection_objects_or_warn(self, tsl):
        objects = tsl.get_all_items()
        if not objects:
            self._log("[WARN] Objects list is empty. Use Get first.")
        return objects

    def on_sel_get_objects(self):
        """선택/계층의 오브젝트로 Objects 리스트를 채운다."""
        hierarchy = self.sel_rb_hierarchy.isChecked()
        objects = collect_from_selection(hierarchy)
        if not objects:
            self._log("[WARN] Nothing selected.")
            return
        self.sel_objs_tsl.set_items(objects)
        self._log("Got {0} object(s) ({1}).".format(
            len(objects), "hierarchy" if hierarchy else "selected"))

    def on_sel_list_types(self):
        """선택/계층의 노드 타입을 모아 Types 리스트에 채운다."""
        hierarchy = self.sel_rb_hierarchy.isChecked()
        objects = collect_from_selection(hierarchy)
        if not objects:
            self._log("[WARN] Nothing selected.")
            return
        types = collect_types(objects)
        self.sel_types_tsl.set_items(types)
        self._log("Listed {0} node type(s).".format(len(types)))

    def on_sel_by_shape(self, type_names):
        """Objects 리스트 중 주어진 타입(들)인 것을 선택한다."""
        objects = self._selection_objects_or_warn(self.sel_objs_tsl)
        if not objects:
            return
        invert = self.sel_cb_invert.isChecked()
        selected = select_by_types(objects, type_names, invert)
        self.sel_objs_tsl.select_by_texts(selected)
        label = type_names if isinstance(type_names, str) else "constraint"
        self._log("Select By Shape '{0}'{1} : {2} object(s).".format(
            label, " (inverted)" if invert else "", len(selected)))

    def on_sel_by_type(self):
        """Types 리스트에서 선택된 타입들에 매칭되는 Objects 를 선택한다."""
        types = self.sel_types_tsl.selected_items()
        if not types:
            self._log("[WARN] Select one or more types in the Types list.")
            return
        objects = self._selection_objects_or_warn(self.sel_objs_tsl)
        if not objects:
            return
        invert = self.sel_cb_invert.isChecked()
        selected = select_by_types(objects, types, invert)
        self.sel_objs_tsl.select_by_texts(selected)
        self._log("Select By Type {0}{1} : {2} object(s).".format(
            types, " (inverted)" if invert else "", len(selected)))

    # ================================================================
    # Tab : Search  (JUN_PY_SearchTool_V01_02 이식)
    # ================================================================

    def _build_search_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # Search Token
        row = QHBoxLayout()
        row.addWidget(QLabel("Search Token"))
        self.sch_le_token = QLineEdit()
        self.sch_le_token.setPlaceholderText("substring of the object name")
        self.sch_le_token.returnPressed.connect(self.on_sch_search)
        row.addWidget(self.sch_le_token)
        root.addLayout(row)

        # 옵션 (Hierarchy/Selected + Invert)
        root.addLayout(self._build_option_row("sch"))

        # Objects 리스트
        self.sch_objs_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", show_select=False, log_callback=self._log)
        self.sch_objs_tsl.add_button("Get", self.on_sch_get_objects, index=0)
        root.addWidget(self.sch_objs_tsl, stretch=1)

        # Search By Token
        btn_search = QPushButton("Search By Token")
        btn_search.setMinimumHeight(32)
        btn_search.setToolTip(
            "Select objects in the list whose name contains the token.")
        btn_search.clicked.connect(self.on_sch_search)
        root.addWidget(btn_search)

        return tab

    def on_sch_get_objects(self):
        """선택/계층의 오브젝트로 Search 탭 Objects 리스트를 채운다."""
        hierarchy = self.sch_rb_hierarchy.isChecked()
        objects = collect_from_selection(hierarchy)
        if not objects:
            self._log("[WARN] Nothing selected.")
            return
        self.sch_objs_tsl.set_items(objects)
        self._log("Got {0} object(s) ({1}).".format(
            len(objects), "hierarchy" if hierarchy else "selected"))

    def on_sch_search(self):
        """Objects 리스트 중 이름에 토큰을 포함하는 것을 선택한다."""
        token = self.sch_le_token.text().strip()
        if not token:
            self._log("[WARN] Enter a search token.")
            return
        objects = self.sch_objs_tsl.get_all_items()
        if not objects:
            self._log("[WARN] Objects list is empty. Use Get first.")
            return
        invert = self.sch_cb_invert.isChecked()
        selected = select_by_token(objects, token, invert)
        self.sch_objs_tsl.select_by_texts(selected)
        self._log("Search '{0}'{1} : {2} object(s).".format(
            token, " (inverted)" if invert else "", len(selected)))

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def show_about(self, *args):
        message = (
            "Search Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Merge of two legacy selection helpers into tabs:\n"
            "\n"
            "[Selection] (from JUN_PY_SelectionTool)\n"
            "- Get / List Types from the selection (or its hierarchy).\n"
            "- Select By Shape: Mesh / nurbsCurve / Joint / Constraint.\n"
            "- Select By Type: match the types you picked in the Types list.\n"
            "\n"
            "[Search] (from JUN_PY_SearchTool)\n"
            "- Search By Token: select objects whose name contains the token.\n"
            "\n"
            "Invert flips the result to the complement. All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
