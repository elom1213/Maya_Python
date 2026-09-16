# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00310_SearchTool - Qt UI
#
# 이 툴이 하는 일은 하나다 - **Objects 리스트에서 조건에 맞는 것만 골라 선택한다.**
# 다른 것은 "무엇으로 고르는가" 뿐이라, 그 기준을 탭으로 나눈다.
#
#   Type  : 노드 **타입**으로     (구 JUN_PY_SelectionTool_V02_01)
#   Token : 오브젝트 **이름**으로 (구 JUN_PY_SearchTool_V01_02)
#   Rules : 씬에서의 **상태**로   (연결 · 히스토리 · 디포머 …, v01.02~)
#
# ★ v01.03 에서 구조를 바꿨다.
#   - 예전에는 상위 탭 Selection / Search 에 Search 만 하위 탭(Token/Rules)을 갖고 있었다.
#     Selection 도 결국 같은 일(리스트에서 조건에 맞는 것 고르기)이라 **셋을 같은 층으로**
#     올렸다. 그러면 상위 탭이 하나만 남아 중첩이 의미가 없어지므로 **중첩을 걷어냈다.**
#   - **Objects 리스트 · Get · Source · Invert 는 셋이 공유한다.** 탭마다 따로 두면 Token 에서
#     Get 해 놓고 Rules 로 넘어갔을 때 리스트가 비어 있다 - 같은 대상을 다른 기준으로 고르는
#     것이 이 툴의 전부인데 대상을 탭마다 다시 모으는 것은 앞뒤가 안 맞는다.
#
# 리스트 UI 는 공용 위젯 JUN_mod_tsl_qt_v01(Select/Add/Del/Up/Down/Sort), 로직은 app/core.
# 규칙은 app/core/select_rules.py 의 레지스트리에 모이고 UI 는 all_rules() 를 그대로 그리므로
# **규칙을 더해도 이 파일은 안 고친다.**
# 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

from tools.A00310_SearchTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00310_SearchTool.app.core import (
    CONSTRAINT_TYPES,
    collect_from_selection,
    collect_types,
    select_by_types,
    select_by_token,
    all_rules,
    get_rule,
    select_by_rules,
)


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00310_SearchTool_window"


class MainWindow(QWidget):

    # 규칙 탈락 사유를 로그에 몇 줄까지 적을지. 전부 적으면 큰 리스트에서 로그가 묻힌다.
    REJECT_LOG_LIMIT = 20

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
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Search Tool - Log",
            object_name="JUN_A00310_SearchTool_log_window")
        self.log_view.setFixedHeight(110)

        # ---- 공유 영역 : 세 탭이 모두 이 리스트를 대상으로 삼는다
        main_layout.addLayout(self._build_option_row())
        main_layout.addWidget(self._build_objects_list(), stretch=1)

        # ---- 기준별 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_type_tab(), "Type")
        self.tabs.setTabToolTip(0, "Pick by node type.")
        self.tabs.addTab(self._build_token_tab(), "Token")
        self.tabs.setTabToolTip(1, "Pick by name - objects whose name contains "
                                   "the token.")
        self.tabs.addTab(self._build_rules_tab(), "Rules")
        self.tabs.setTabToolTip(2, "Pick by state in the scene - connections, "
                                   "history, deformers.")
        main_layout.addWidget(self.tabs, stretch=1)

        # 로그창
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ---- 공유 : 옵션 행 + Objects 리스트

    def _build_option_row(self):
        """Hierarchy/Selected 라디오 + Invert 체크박스 한 줄 (세 탭 공용)."""
        row = QHBoxLayout()
        row.addWidget(QLabel("Source"))

        self.rb_hierarchy = QRadioButton("Hierarchy")
        self.rb_selected = QRadioButton("Selected")
        self.rb_hierarchy.setChecked(True)
        self.rb_hierarchy.setToolTip(
            "Hierarchy: expand each selected object to its descendant "
            "transforms. Selected: use the raw selection only.")
        # ★ 두 라디오를 다 보관한다 - 배타적 라디오는 `setChecked(False)` 가 **무시되므로**
        #   모드를 코드로 바꾸려면 켜려는 쪽을 직접 켜야 한다.
        group = QButtonGroup(self)
        group.addButton(self.rb_hierarchy)
        group.addButton(self.rb_selected)
        row.addWidget(self.rb_hierarchy)
        row.addWidget(self.rb_selected)

        row.addStretch(1)

        self.cb_invert = QCheckBox("Invert")
        self.cb_invert.setToolTip(
            "Select the complement: everything in the Objects list that does "
            "NOT match.")
        row.addWidget(self.cb_invert)
        return row

    def _build_objects_list(self):
        """세 탭이 함께 쓰는 Objects 리스트. 한 번 Get 하면 어느 탭에서나 쓴다."""
        self.objs_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", show_select=False, log_callback=self._log)
        self.objs_tsl.add_button("Get", self.on_get_objects, index=0)
        return self.objs_tsl

    def _objects_or_warn(self):
        objects = self.objs_tsl.get_all_items()
        if not objects:
            self._log("[WARN] Objects list is empty. Use Get first.")
        return objects

    def on_get_objects(self):
        """선택/계층의 오브젝트로 공유 Objects 리스트를 채운다."""
        hierarchy = self.rb_hierarchy.isChecked()
        objects = collect_from_selection(hierarchy)
        if not objects:
            self._log("[WARN] Nothing selected.")
            return
        self.objs_tsl.set_items(objects)
        self._log("Got {0} object(s) ({1}).".format(
            len(objects), "hierarchy" if hierarchy else "selected"))

    # ================================================================
    # Tab : Type  (구 Selection 탭, JUN_PY_SelectionTool_V02_01 이식)
    # ================================================================

    def _build_type_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # Types 리스트 - 이 탭에서만 쓰므로 탭 안에 둔다.
        self.type_types_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Types", show_select=False, show_add=False,
            log_callback=self._log)
        self.type_types_tsl.add_button(
            "List Types", self.on_list_types, index=0)
        root.addWidget(self.type_types_tsl, stretch=1)

        # Select By Shape (고정 타입 버튼)
        shape_box = QGroupBox("Select By Shape (from the Objects list)")
        shape_layout = QVBoxLayout(shape_box)
        r1 = QHBoxLayout()
        for label, type_name in (("Mesh", "mesh"),
                                 ("nurbsCurve", "nurbsCurve")):
            btn = QPushButton(label)
            btn.clicked.connect(
                lambda _checked=False, t=type_name: self.on_select_by_shape(t))
            r1.addWidget(btn)
        shape_layout.addLayout(r1)
        r2 = QHBoxLayout()
        btn_joint = QPushButton("Joint")
        btn_joint.clicked.connect(
            lambda _checked=False: self.on_select_by_shape("joint"))
        r2.addWidget(btn_joint)
        btn_con = QPushButton("Constraint")
        btn_con.clicked.connect(
            lambda _checked=False: self.on_select_by_shape(CONSTRAINT_TYPES))
        r2.addWidget(btn_con)
        shape_layout.addLayout(r2)
        root.addWidget(shape_box)

        # Select By Type (Types 리스트에서 선택된 타입들로 매칭)
        btn_by_type = QPushButton("Select By Type (use selected types)")
        btn_by_type.setMinimumHeight(32)
        btn_by_type.setToolTip(
            "Select objects whose node type is among the types you have "
            "selected in the Types list.")
        btn_by_type.clicked.connect(self.on_select_by_type)
        root.addWidget(btn_by_type)

        return tab

    def on_list_types(self):
        """Objects 리스트에 있는 오브젝트들의 노드 타입을 모아 Types 에 채운다.

        v01.02 까지는 씬 선택에서 직접 모았다. Objects 리스트가 공유가 된 v01.03 부터는
        **다른 버튼들과 같은 대상**(= Objects 리스트)을 본다 - 화면에 보이는 목록과 타입
        목록이 어긋나지 않는다.
        """
        objects = self._objects_or_warn()
        if not objects:
            return
        types = collect_types(objects)
        self.type_types_tsl.set_items(types)
        self._log("Listed {0} node type(s) from {1} object(s).".format(
            len(types), len(objects)))

    def on_select_by_shape(self, type_names):
        """Objects 리스트 중 주어진 타입(들)인 것을 선택한다."""
        objects = self._objects_or_warn()
        if not objects:
            return
        invert = self.cb_invert.isChecked()
        selected = select_by_types(objects, type_names, invert)
        self.objs_tsl.select_by_texts(selected)
        label = type_names if isinstance(type_names, str) else "constraint"
        self._log("Select By Shape '{0}'{1} : {2} object(s).".format(
            label, " (inverted)" if invert else "", len(selected)))

    def on_select_by_type(self):
        """Types 리스트에서 선택된 타입들에 매칭되는 Objects 를 선택한다."""
        types = self.type_types_tsl.selected_items()
        if not types:
            self._log("[WARN] Select one or more types in the Types list.")
            return
        objects = self._objects_or_warn()
        if not objects:
            return
        invert = self.cb_invert.isChecked()
        selected = select_by_types(objects, types, invert)
        self.objs_tsl.select_by_texts(selected)
        self._log("Select By Type {0}{1} : {2} object(s).".format(
            types, " (inverted)" if invert else "", len(selected)))

    # ================================================================
    # Tab : Token  (JUN_PY_SearchTool_V01_02 이식)
    # ================================================================

    def _build_token_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        row = QHBoxLayout()
        row.addWidget(QLabel("Search Token"))
        self.token_le = QLineEdit()
        self.token_le.setPlaceholderText("substring of the object name")
        self.token_le.returnPressed.connect(self.on_search_token)
        row.addWidget(self.token_le)
        root.addLayout(row)

        root.addStretch(1)

        btn_search = QPushButton("Search By Token")
        btn_search.setMinimumHeight(32)
        btn_search.setToolTip(
            "Select objects in the list whose name contains the token.")
        btn_search.clicked.connect(self.on_search_token)
        root.addWidget(btn_search)

        return tab

    def on_search_token(self):
        """Objects 리스트 중 이름에 토큰을 포함하는 것을 선택한다."""
        token = self.token_le.text().strip()
        if not token:
            self._log("[WARN] Enter a search token.")
            return
        objects = self._objects_or_warn()
        if not objects:
            return
        invert = self.cb_invert.isChecked()
        selected = select_by_token(objects, token, invert)
        self.objs_tsl.select_by_texts(selected)
        self._log("Search '{0}'{1} : {2} object(s).".format(
            token, " (inverted)" if invert else "", len(selected)))

    # ================================================================
    # Tab : Rules  (v01.02~)
    # ================================================================

    def _build_rules_tab(self):
        """규칙 목록은 `app/core/select_rules.all_rules()` 를 그대로 그린다.

        ★ 규칙이 늘어나도 **이 함수는 손대지 않는다** - core 에 `register()` 한 줄을
        더하면 리스트에 저절로 나타난다.
        """
        tab = QWidget()
        root = QVBoxLayout(tab)

        rules_box = QGroupBox("Rules (pick one or more - all of them must match)")
        rules_layout = QVBoxLayout(rules_box)

        self.rules_list = QListWidget()
        self.rules_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for rule in all_rules():
            item = QListWidgetItem(rule.label)
            item.setData(Qt.UserRole, rule.key)
            item.setToolTip(rule.description)
            self.rules_list.addItem(item)
        if self.rules_list.count():
            self.rules_list.setCurrentRow(0)
        self.rules_list.itemSelectionChanged.connect(
            self._on_rule_selection_changed)
        rules_layout.addWidget(self.rules_list)

        # 고른 규칙이 무엇을 뜻하는지 한 줄로 (툴팁을 못 보는 사람도 알도록)
        self.rules_lbl_desc = QLabel()
        self.rules_lbl_desc.setWordWrap(True)
        rules_layout.addWidget(self.rules_lbl_desc)

        root.addWidget(rules_box, stretch=1)

        btn_rules = QPushButton("Select By Rules")
        btn_rules.setMinimumHeight(32)
        btn_rules.setToolTip(
            "Select objects in the list that satisfy every rule you picked.\n"
            "Objects that do not are listed in the log with the reason.")
        btn_rules.clicked.connect(self.on_select_by_rules)
        root.addWidget(btn_rules)

        self._on_rule_selection_changed()
        return tab

    def _selected_rule_keys(self):
        return [item.data(Qt.UserRole) for item in self.rules_list.selectedItems()]

    def _on_rule_selection_changed(self):
        keys = self._selected_rule_keys()
        if not keys:
            self.rules_lbl_desc.setText("Pick a rule above.")
            return
        self.rules_lbl_desc.setText(
            "\n".join("{0} - {1}".format(get_rule(key).label,
                                         get_rule(key).description)
                      for key in keys))

    def on_select_by_rules(self):
        """Objects 리스트 중 고른 규칙을 전부 만족하는 것을 선택한다."""
        keys = self._selected_rule_keys()
        if not keys:
            self._log("[WARN] Pick one or more rules.")
            return
        objects = self._objects_or_warn()
        if not objects:
            return

        invert = self.cb_invert.isChecked()
        selected, rejected = select_by_rules(objects, keys, invert)
        self.objs_tsl.select_by_texts(selected)

        labels = ", ".join(get_rule(key).label for key in keys)
        self._log("Select By Rules [{0}]{1} : {2} of {3} object(s).".format(
            labels, " (inverted)" if invert else "", len(selected), len(objects)))

        # 왜 빠졌는지 - "몇 개 맞았다" 보다 이쪽이 쓸모 있다.
        for obj, reason in rejected[:self.REJECT_LOG_LIMIT]:
            self._log("    - {0} : {1}".format(obj.split("|")[-1], reason))
        if len(rejected) > self.REJECT_LOG_LIMIT:
            self._log("    ... and {0} more.".format(
                len(rejected) - self.REJECT_LOG_LIMIT))

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
            "Pick objects from the shared Objects list by one of three\n"
            "criteria. Get fills the list once - every tab works on it.\n"
            "\n"
            "[Type] (from JUN_PY_SelectionTool)\n"
            "- List Types: collect the node types of the listed objects.\n"
            "- Select By Shape: Mesh / nurbsCurve / Joint / Constraint.\n"
            "- Select By Type: match the types you picked in the Types list.\n"
            "\n"
            "[Token] (from JUN_PY_SearchTool)\n"
            "- Search By Token: select objects whose name contains the token.\n"
            "\n"
            "[Rules]\n"
            "- Select By Rules: keep only the objects that satisfy every rule\n"
            "  you picked. Rejected objects are logged with the reason.\n"
            "- Standalone: no connections and no history - nothing drives it\n"
            "  and it drives nothing.\n"
            "\n"
            "Invert flips the result to the complement. All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
