# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
# A00330_NamingTool - Qt UI
#
# 레거시 maya.cmds 네이밍 툴(JUN_PY_NamingTool_V03_04)을 PySide + QTabWidget 으로 이식.
#   - Rename > Token 탭 : 계층 토큰 네이밍 (legacy Naming Dynamics, v01.07 규칙·프로파일 - token_tab.py)
#   - Copy Name    탭 : base 이름을 target 에 prefix 부착 복사 (legacy Copy name)
#   - Quick Rename 탭 : Front Insert / Change New / Last Add / -1 trim (ref/ref_01.mel 이식)
#   - Set Rename   탭 : 세트 이름의 부분 문자열 찾아 바꾸기 (v01.02, NEW)
#       마야 `Modify > Search and Replace Names` 는 세트를 못 고른다 - `select(set)` 이
#       멤버를 펼쳐 선택하기 때문이다. 이 탭은 세트를 직접 열거해 고르고 미리보기를 준다.
#   v01.03 : Set Rename 에 Add / Del (다른 탭의 TSL 과 같은 조작),
#            Copy Name 이 세트도 대상으로 (세트는 같은 이름을 못 써서 `_copy` 접미사).
#   v01.05 : Copy Name 에 Search / Replace - Base 이름 속 단어를 바꿔서 Targets 에 복사.
#   v01.07 : 상위 탭 Rename 을 만들고 Naming Dyn(-> Token) · Set Rename 을 하위 탭으로.
#            Token 탭은 칸 수가 자유인 토큰(Custom / Numbering) + Profile(json) - app/ui/token_tab.py.
#   v01.09 : Quick Rename 을 하위 탭 Selection(기존) / Insert(신규) 로.
#            Insert 는 리스트의 오브젝트 이름 n 번째 자리에 글자를 넣는다(음수는 끝에서부터).
#            미리보기 표를 보고 Apply 를 눌러야 바뀐다 - app/core/insert_ops.py.
# 리스트 UI 는 공용 위젯 JUN_mod_tsl_qt_v01, 로직은 app/core. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_filter_qt
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.core import log_levels
from Framework.themes.theme_manager import ThemeManager

from tools.A00330_NamingTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00330_NamingTool.app import core
from tools.A00330_NamingTool.app.ui.token_tab import TokenTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00330_NamingTool_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Naming Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 720)

        self.build_ui()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 공용 로그창 (탭 빌더가 self._log / TSL log_callback 을 쓰므로 탭보다 먼저 생성)
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Naming Tool - Log",
            object_name="JUN_A00330_NamingTool_log_window")
        self.log_view.setFixedHeight(110)

        # 탭: Rename(하위 탭 Token / Set Rename) / Copy Name / Quick Rename
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_rename_tab(), "Rename")
        self.tabs.addTab(self._build_copy_name_tab(), "Copy Name")
        self.tabs.addTab(self._build_quick_rename_tab(), "Quick Rename")
        self.tabs.setTabToolTip(
            0,
            "Token - name objects from token rules.\n"
            "Set Rename - search and replace inside set names.")
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

    # ================================================================
    # Tab : Rename  (v01.07) - 하위 탭 Token / Set Rename
    # ================================================================

    def _build_rename_tab(self):
        self.rename_tabs = QTabWidget()
        self.token_tab = TokenTab(log=self._log)
        self.rename_tabs.addTab(self.token_tab, "Token")
        self.rename_tabs.addTab(self._build_set_rename_tab(), "Set Rename")
        self.rename_tabs.setTabToolTip(
            0,
            "Rename objects and their descendants with token rules (Custom / Numbering).\n"
            "The rules are kept in profiles.")
        self.rename_tabs.setTabToolTip(
            1,
            "Search and replace inside set names.\n"
            "Maya's own Search and Replace Names cannot reach sets from a selection.")
        return self.rename_tabs

    # ================================================================
    # Tab : Copy Name  (legacy Copy name)
    # ================================================================

    def _build_copy_name_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # Base | Targets (좌우)
        self.copy_base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Base", select_label="Select Base",
            log_callback=self._log)
        self.copy_tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select Targets",
            log_callback=self._log)

        # 세트는 `cmds.select(set)` 이 멤버를 펼쳐 버려서 Select/Add 로는 담기 어렵다.
        # 전용 버튼으로 담는다 - 지금 선택에 든 세트 + 선택한 오브젝트가 **속한** 세트.
        self.copy_base_tsl.add_button(
            "Add Sets", lambda: self._copy_add_sets(self.copy_base_tsl))
        self.copy_tgt_tsl.add_button(
            "Add Sets", lambda: self._copy_add_sets(self.copy_tgt_tsl))

        list_row = QHBoxLayout()
        list_row.addWidget(self.copy_base_tsl)
        list_row.addWidget(self.copy_tgt_tsl)
        root.addLayout(list_row, stretch=1)

        # Prefix / Set suffix
        form = QGridLayout()
        form.addWidget(QLabel("Prefix :"), 0, 0)
        self.copy_le_prefix = QLineEdit()
        self.copy_le_prefix.setPlaceholderText("optional prefix for new names")
        form.addWidget(self.copy_le_prefix, 0, 1)

        form.addWidget(QLabel("Set suffix :"), 1, 0)
        self.copy_le_set_suffix = QLineEdit(core.DEFAULT_SET_COPY_SUFFIX)
        self.copy_le_set_suffix.setToolTip(
            "Added when the Targets item is a SET.\n"
            "A set cannot take a name that is already used - Maya would silently make\n"
            "it 'name1'. Clear this field to copy the name as-is and let Maya decide\n"
            "(the log then reports the name it actually gave).")
        form.addWidget(self.copy_le_set_suffix, 1, 1)

        # Search / Replace (v01.05) - Base 이름 속 단어를 바꿔서 Targets 에 복사.
        # 규칙은 Set Rename 탭과 같다(글자 그대로, 전부 치환, 대소문자 옵션).
        search_tip = (
            "Every Search found in the Base name is replaced with Replace,\n"
            "and the result is given to the Target.\n"
            "e.g. Base 'L_arm_jnt', Search 'jnt', Replace 'ctrl' -> Target 'L_arm_ctrl'\n"
            "Only the Base name is searched - Prefix and Set suffix are added after.")

        form.addWidget(QLabel("Search :"), 2, 0)
        self.copy_le_search = QLineEdit()
        self.copy_le_search.setPlaceholderText(
            "text to find inside each Base name (empty = copy as-is)")
        self.copy_le_search.setToolTip(search_tip)
        form.addWidget(self.copy_le_search, 2, 1)

        form.addWidget(QLabel("Replace :"), 3, 0)
        self.copy_le_replace = QLineEdit()
        self.copy_le_replace.setPlaceholderText("text to put in its place (may be empty)")
        self.copy_le_replace.setToolTip(search_tip)
        form.addWidget(self.copy_le_replace, 3, 1)

        self.copy_cb_case = QCheckBox("Case sensitive")
        self.copy_cb_case.setChecked(True)
        self.copy_cb_case.setToolTip("Match Search with the same upper / lower case.")
        form.addWidget(self.copy_cb_case, 4, 1)
        root.addLayout(form)

        # 실행 버튼
        btn = QPushButton("Copy Name")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Rename each Targets item to (Prefix + the matching Base item's "
            "leaf name), in list order.\n"
            "If Search is filled, it is replaced with Replace inside the Base name first.\n"
            "Sets also get the Set suffix. Namespaces are kept.")
        btn.clicked.connect(self.on_copy_name)
        root.addWidget(btn)

        return tab

    def _copy_add_sets(self, tsl):
        """지금 선택과 관련된 세트를 리스트에 더한다 (Copy Name 탭).

        `cmds.select(set)` 은 세트가 아니라 멤버를 펼쳐 선택하므로, 평범한 Select/Add 로는
        세트를 담기 어렵다. 여기서는 **선택에 들어 있는 세트**와 **선택한 오브젝트가 속한
        세트**를 함께 모은다(메시를 고르고 그것이 든 세트를 담는 것이 흔한 흐름이다).
        """
        names = core.set_rename_ops.sets_from_selection()
        if not names:
            self._log("[WARN] Add Sets : no set in the selection, and the selected "
                      "objects do not belong to any set.")
            return
        tsl.append_unique(names)
        self._log("Add Sets : {0} set(s) added to {1}.".format(
            len(names), tsl.title))

    def on_copy_name(self):
        base_items = self.copy_base_tsl.get_all_items()
        target_items = self.copy_tgt_tsl.get_all_items()
        if not base_items or not target_items:
            self._log("[WARN] Both Base and Targets lists must be filled.")
            return

        with core.undo_chunk():
            new_names, warning, notes = core.copy_name(
                base_items, target_items, self.copy_le_prefix.text(),
                set_suffix=self.copy_le_set_suffix.text(),
                search=self.copy_le_search.text(),
                replace=self.copy_le_replace.text(),
                case_sensitive=self.copy_cb_case.isChecked())
        if warning:
            self._log("[WARN] " + warning)
        for note in notes:
            self._log(note)

        # Targets 리스트를 새 이름으로 갱신
        if new_names:
            self.copy_tgt_tsl.set_items(new_names)
        search = self.copy_le_search.text()
        if search:
            self._log("Copy Name : {0} target(s) renamed (Search '{1}' -> Replace '{2}').".format(
                len(new_names), search, self.copy_le_replace.text()))
        else:
            self._log("Copy Name : {0} target(s) renamed.".format(len(new_names)))

    # ================================================================
    # Tab : Quick Rename  (v01.09) - 하위 탭 Selection / Insert
    # ================================================================

    def _build_quick_rename_tab(self):
        self.quick_tabs = QTabWidget()
        self.quick_tabs.addTab(self._build_quick_selection_page(), "Selection")
        self.quick_tabs.addTab(self._build_quick_insert_page(), "Insert")
        self.quick_tabs.setTabToolTip(
            0,
            "Front Insert / Change New / Last Add / -1 trim on the current selection.")
        self.quick_tabs.setTabToolTip(
            1,
            "Insert text at the n-th position of every listed name.\n"
            "Preview first, then Apply.")
        return self.quick_tabs

    # ================================================================
    # Quick Rename > Selection  (ref/ref_01.mel 이식, 현재 선택 기준)
    # ================================================================

    def _build_quick_selection_page(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        note = QLabel("Operates on the current Maya selection.")
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)

        # 상단: -1 Front / All Apply
        top_row = QHBoxLayout()
        btn_trim_front = QPushButton("-1 Front")
        btn_trim_front.setToolTip("Remove the first character of each name.")
        btn_trim_front.clicked.connect(self.on_trim_front)
        top_row.addWidget(btn_trim_front)
        btn_all = QPushButton("All Apply")
        btn_all.setToolTip("Apply Change New, then Front Insert, then Last Add.")
        btn_all.clicked.connect(self.on_all_apply)
        top_row.addWidget(btn_all)
        root.addLayout(top_row)

        # 입력 + 개별 적용 버튼
        form = QGridLayout()

        form.addWidget(QLabel("Front Insert"), 0, 0)
        self.qr_le_insert = QLineEdit()
        form.addWidget(self.qr_le_insert, 0, 1)
        btn_insert = QPushButton("Insert Apply")
        btn_insert.setToolTip("Prepend the text to each selected name.")
        btn_insert.clicked.connect(self.on_insert_apply)
        form.addWidget(btn_insert, 0, 2)

        form.addWidget(QLabel("Change New"), 1, 0)
        self.qr_le_new = QLineEdit()
        form.addWidget(self.qr_le_new, 1, 1)
        btn_new = QPushButton("New Apply")
        btn_new.setToolTip(
            "Rename to the new name + incrementing index. With Start empty: "
            "multiple selection appends 01, 02, ...; single selection has no "
            "number.")
        btn_new.clicked.connect(self.on_new_apply)
        form.addWidget(btn_new, 1, 2)

        form.addWidget(QLabel("Start (Index)"), 2, 0)
        self.qr_le_index = QLineEdit()
        self.qr_le_index.setPlaceholderText("empty = auto from 1")
        self.qr_le_index.setFixedWidth(120)
        form.addWidget(self.qr_le_index, 2, 1)

        form.addWidget(QLabel("Last Add"), 3, 0)
        self.qr_le_add = QLineEdit()
        form.addWidget(self.qr_le_add, 3, 1)
        btn_add = QPushButton("Add Apply")
        btn_add.setToolTip("Append the text to each selected name.")
        btn_add.clicked.connect(self.on_add_apply)
        form.addWidget(btn_add, 3, 2)

        root.addLayout(form)

        # 하단: -1 Rear
        btn_trim_rear = QPushButton("-1 Rear")
        btn_trim_rear.setToolTip("Remove the last character of each name.")
        btn_trim_rear.clicked.connect(self.on_trim_rear)
        root.addWidget(btn_trim_rear)

        root.addStretch(1)
        return tab

    def on_insert_apply(self):
        with core.undo_chunk():
            count = core.insert_front(self.qr_le_insert.text())
        self._log("Front Insert : {0} renamed.".format(count))

    def on_add_apply(self):
        with core.undo_chunk():
            count = core.add_rear(self.qr_le_add.text())
        self._log("Last Add : {0} renamed.".format(count))

    def on_new_apply(self):
        with core.undo_chunk():
            count, error = core.change_new(
                self.qr_le_new.text(), self.qr_le_index.text())
        if error:
            self._log("[WARN] " + error)
        else:
            self._log("Change New : {0} renamed.".format(count))

    def on_trim_front(self):
        with core.undo_chunk():
            count = core.trim_front()
        self._log("-1 Front : {0} renamed.".format(count))

    def on_trim_rear(self):
        with core.undo_chunk():
            count = core.trim_rear()
        self._log("-1 Rear : {0} renamed.".format(count))

    def on_all_apply(self):
        with core.undo_chunk():
            messages = core.all_apply(
                self.qr_le_new.text(), self.qr_le_index.text(),
                self.qr_le_insert.text(), self.qr_le_add.text())
        for message in messages:
            self._log("All Apply " + message)

    # ================================================================
    # Quick Rename > Insert  (v01.09)
    # ================================================================

    #: 미리보기 표 컬럼
    _INS_COL_NAME, _INS_COL_NEW, _INS_COL_STATUS = range(3)

    def _build_quick_insert_page(self):
        """리스트의 오브젝트 이름 n 번째 자리에 글자를 넣는다.

        Text / Position 을 바꾸거나 리스트가 바뀌면 오른쪽 미리보기가 바로 갱신되고,
        씬은 **Apply 를 눌러야** 바뀐다. 규칙은 app/core/insert_ops.py 머리말.
        """
        tab = QWidget()
        root = QVBoxLayout(tab)

        # ---- 좌: 오브젝트 리스트 / 우: 미리보기 ----
        self.ins_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Objects",
            log_callback=self._log)

        self.ins_tree = QTreeWidget()
        self.ins_tree.setColumnCount(3)
        self.ins_tree.setHeaderLabels(["Current", "New name", "Status"])
        self.ins_tree.setRootIsDecorated(False)
        self.ins_tree.setAlternatingRowColors(True)
        self.ins_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.ins_tree.setToolTip("What each listed name will become. Nothing is renamed "
                                 "until you press Apply.")

        preview_box = QWidget()
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(2, 2, 2, 2)
        lbl_preview = QLabel("Preview")
        font = lbl_preview.font()
        font.setBold(True)
        lbl_preview.setFont(font)
        preview_layout.addWidget(lbl_preview)
        preview_layout.addWidget(self.ins_tree, 1)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.ins_tsl)
        split.addWidget(preview_box)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        root.addWidget(split, stretch=1)

        # 리스트가 바뀌면(Select / Add / Del / Up / Down / Sort) 미리보기를 다시 그린다
        model = self.ins_tsl.list_widget.model()
        for signal in (model.rowsInserted, model.rowsRemoved,
                       model.rowsMoved, model.modelReset):
            signal.connect(self._ins_update_preview)

        # ---- Text / Position ----
        position_tip = (
            "Where the text goes, counted in characters of the short name\n"
            "(DAG path and namespace are not counted and are kept).\n"
            "  0 = front, 3 = after the 3rd character\n"
            " -1 = end,  -4 = before the last 3 characters\n"
            "e.g. 'arm_jnt' + 'X' :  0 -> Xarm_jnt,  3 -> armX_jnt,  -1 -> arm_jntX\n"
            "A position past the name puts the text at the end (or the front).")

        form = QGridLayout()
        form.addWidget(QLabel("Text"), 0, 0)
        self.ins_le_text = QLineEdit()
        self.ins_le_text.setPlaceholderText("text to insert")
        self.ins_le_text.textChanged.connect(self._ins_update_preview)
        form.addWidget(self.ins_le_text, 0, 1, 1, 2)

        form.addWidget(QLabel("Position"), 1, 0)
        self.ins_sb_position = QSpinBox()
        self.ins_sb_position.setRange(-999, 999)
        self.ins_sb_position.setValue(0)
        self.ins_sb_position.setToolTip(position_tip)
        self.ins_sb_position.valueChanged.connect(self._ins_update_preview)
        form.addWidget(self.ins_sb_position, 1, 1)
        self.ins_lbl_position = QLabel("")
        self.ins_lbl_position.setToolTip(position_tip)
        form.addWidget(self.ins_lbl_position, 1, 2)
        form.setColumnStretch(2, 1)
        root.addLayout(form)

        self.ins_btn_apply = QPushButton("Apply")
        self.ins_btn_apply.setMinimumHeight(32)
        self.ins_btn_apply.setToolTip(
            "Rename the listed objects as shown in the preview.\n"
            "Rows marked no change / invalid name / locked / referenced are skipped.\n"
            "Everything is one undo step.")
        self.ins_btn_apply.clicked.connect(self.on_ins_apply)
        root.addWidget(self.ins_btn_apply)

        self._ins_update_preview()
        return tab

    def _ins_position_hint(self, position):
        """Position 칸 옆의 한 줄 설명."""
        if position == 0:
            return "front"
        if position == -1:
            return "end"
        if position > 0:
            return "after the first {0} character(s)".format(position)
        return "before the last {0} character(s)".format(-position - 1)

    def _ins_rows(self):
        return core.insert_ops.preview(
            self.ins_tsl.get_all_nodes(),
            self.ins_le_text.text(),
            self.ins_sb_position.value())

    def _ins_update_preview(self, *args):
        """미리보기 표를 다시 채운다. 씬은 건드리지 않는다."""
        if not hasattr(self, "ins_btn_apply"):
            return      # 빌드 중 (위젯이 아직 다 안 만들어짐)

        position = self.ins_sb_position.value()
        self.ins_lbl_position.setText(self._ins_position_hint(position))

        rows = self._ins_rows()
        dark = ThemeManager.is_dark_theme()
        colors = {
            core.insert_ops.ST_OK: log_levels.color("OK", dark),
            core.insert_ops.ST_COLLISION: log_levels.color("WARN", dark),
            core.insert_ops.ST_SAME: log_levels.color("SKIP", dark),
        }
        error_color = log_levels.color("ERROR", dark)

        self.ins_tree.clear()
        for row in rows:
            status = row["status"]
            shows_new = status in core.insert_ops.APPLICABLE
            item = QTreeWidgetItem([
                row["path"].split("|")[-1],
                row["new_name"] if shows_new else "",
                status if not row["note"] else "{0} - {1}".format(status, row["note"])])
            item.setToolTip(self._INS_COL_NAME, row["path"])
            color = colors.get(status, error_color)
            if color:
                item.setForeground(self._INS_COL_STATUS, QBrush(QColor(color)))
            self.ins_tree.addTopLevelItem(item)
        for col in range(3):
            self.ins_tree.resizeColumnToContents(col)

    def on_ins_apply(self):
        # 미리보기 때와 씬이 달라졌을 수 있으니 누르는 순간 다시 계산한다
        rows = self._ins_rows()
        if not rows:
            self._log("[WARN] Insert : the Objects list is empty.")
            return
        if not self.ins_le_text.text():
            self._log("[WARN] Insert : the Text field is empty.")
            return

        counts = core.insert_ops.summarize(rows)
        if not any(r["status"] in core.insert_ops.APPLICABLE for r in rows):
            self._log("[WARN] Insert : nothing to rename ({0}).".format(
                ", ".join("{0} {1}".format(v, k) for k, v in sorted(counts.items()))))
            return

        with core.undo_chunk():
            paths, messages = core.insert_ops.apply_rows(rows)
        for message in messages:
            self._log(message)

        skipped = {k: v for k, v in counts.items()
                   if k not in core.insert_ops.APPLICABLE}
        if skipped:
            self._log("[SKIP] {0}".format(
                ", ".join("{0} {1}".format(v, k) for k, v in sorted(skipped.items()))))

        # 리스트를 새 이름으로 다시 채운다 (짧은 고유 이름으로 보여 준다)
        self.ins_tsl.set_items(core.insert_ops.display_names(paths))
        self._ins_update_preview()

    # ================================================================
    # Rename > Set Rename  (v01.02)
    # ================================================================

    #: 트리 컬럼
    _SR_COL_NAME, _SR_COL_TYPE, _SR_COL_MEMBERS, _SR_COL_NEW, _SR_COL_STATUS = range(5)

    def _build_set_rename_tab(self):
        """세트 이름의 부분 문자열을 찾아 바꾼다.

        마야 기본 `Search and Replace Names` 가 세트에 안 먹히는 이유는 명령이 아니라
        **세트를 선택할 수 없다는 것**이다(`select(set)` 은 멤버를 펼친다).
        그래서 이 탭은 세트를 직접 열거해 고르게 하고, 바꾸기 전에 미리보기를 준다.
        """
        tab = QWidget()
        root = QVBoxLayout(tab)

        note = QLabel(
            "Maya's Search and Replace Names cannot pick sets - clicking a set selects "
            "its members instead. Pick the sets here.")
        note.setWordWrap(True)
        root.addWidget(note)

        # ---- 목록 채우기 ----
        src_row = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setToolTip("List every set in the scene.")
        btn_refresh.clicked.connect(self.on_sr_refresh)
        src_row.addWidget(btn_refresh)

        btn_from_sel = QPushButton("From Selection")
        btn_from_sel.setToolTip(
            "Replace the list with the sets the selected objects belong to.\n"
            "Selecting a set itself works too (Maya expands it, so this looks at\n"
            "membership as well).")
        btn_from_sel.clicked.connect(self.on_sr_from_selection)
        src_row.addWidget(btn_from_sel)

        btn_add = QPushButton("Add")
        btn_add.setToolTip(
            "Add the sets related to the current selection to the list,\n"
            "keeping what is already there.")
        btn_add.clicked.connect(self.on_sr_add)
        src_row.addWidget(btn_add)

        btn_del = QPushButton("Del")
        btn_del.setToolTip(
            "Remove the highlighted rows FROM THIS LIST.\n"
            "The sets themselves are not deleted from the scene.")
        btn_del.clicked.connect(self.on_sr_del)
        src_row.addWidget(btn_del)

        self.sr_cb_shading = QCheckBox("Shading Engines")
        self.sr_cb_shading.setToolTip(
            "Include shadingEngine nodes. Off by default - renaming them touches the "
            "render setup.")
        self.sr_cb_shading.stateChanged.connect(lambda *_: self.on_sr_refresh())
        src_row.addWidget(self.sr_cb_shading)

        self.sr_cb_partitions = QCheckBox("Partitions")
        self.sr_cb_partitions.setToolTip(
            "Include partition nodes. They are a different node type, so Maya's own "
            "set listings miss them.")
        self.sr_cb_partitions.stateChanged.connect(lambda *_: self.on_sr_refresh())
        src_row.addWidget(self.sr_cb_partitions)

        src_row.addStretch(1)
        root.addLayout(src_row)

        # ---- 필터 ----
        self.sr_lbl_number = QLabel("Number: 0")
        self.sr_tree = QTreeWidget()
        self.sr_tree.setColumnCount(5)
        self.sr_tree.setHeaderLabels(["Set", "Type", "Members", "New name", "Status"])
        self.sr_tree.setRootIsDecorated(False)
        self.sr_tree.setAlternatingRowColors(True)
        self.sr_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sr_tree.setSortingEnabled(True)
        self.sr_tree.itemSelectionChanged.connect(self.on_sr_selection_changed)

        self.sr_filter = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            tree_widget=self.sr_tree, number_label=self.sr_lbl_number,
            placeholder="Type any part of a set name")

        filter_row = QHBoxLayout()
        filter_row.addWidget(self.sr_filter, 1)
        filter_row.addWidget(self.sr_lbl_number)
        root.addLayout(filter_row)

        root.addWidget(self.sr_tree, stretch=1)

        # ---- 검색 / 치환 ----
        form = QGridLayout()
        form.addWidget(QLabel("Search"), 0, 0)
        self.sr_le_search = QLineEdit()
        self.sr_le_search.setPlaceholderText("text to find inside the set name")
        self.sr_le_search.textChanged.connect(self._sr_update_preview)
        form.addWidget(self.sr_le_search, 0, 1)

        form.addWidget(QLabel("Replace"), 1, 0)
        self.sr_le_replace = QLineEdit()
        self.sr_le_replace.setPlaceholderText("text to put in its place (may be empty)")
        self.sr_le_replace.textChanged.connect(self._sr_update_preview)
        form.addWidget(self.sr_le_replace, 1, 1)
        root.addLayout(form)

        opt_row = QHBoxLayout()
        self.sr_cb_case = QCheckBox("Case sensitive")
        self.sr_cb_case.setChecked(True)
        self.sr_cb_case.setToolTip("Same as Maya's own Search and Replace Names.")
        self.sr_cb_case.stateChanged.connect(lambda *_: self._sr_update_preview())
        opt_row.addWidget(self.sr_cb_case)

        btn_select_scene = QPushButton("Select Sets in Scene")
        btn_select_scene.setToolTip(
            "Select the highlighted sets themselves (not their members).")
        btn_select_scene.clicked.connect(self.on_sr_select_in_scene)
        opt_row.addWidget(btn_select_scene)
        opt_row.addStretch(1)
        root.addLayout(opt_row)

        self.sr_btn_apply = QPushButton("Rename Selected Sets")
        self.sr_btn_apply.setMinimumHeight(32)
        self.sr_btn_apply.setToolTip(
            "Rename the highlighted sets. Rows marked no change / invalid name /\n"
            "locked / referenced / default set are skipped.\n"
            "Everything is one undo step.")
        self.sr_btn_apply.clicked.connect(self.on_sr_apply)
        root.addWidget(self.sr_btn_apply)

        return tab

    # ---- Set Rename : 목록 ----

    def _sr_fill(self, infos):
        """트리를 세트 정보로 다시 채운다."""
        self.sr_tree.setSortingEnabled(False)
        self.sr_tree.clear()
        for info in infos:
            item = QTreeWidgetItem([
                info["name"], info["type"], str(info["members"]), "", ""])
            item.setData(0, Qt.UserRole, info["name"])
            self.sr_tree.addTopLevelItem(item)
        self.sr_tree.setSortingEnabled(True)
        for col in range(5):
            self.sr_tree.resizeColumnToContents(col)
        # 새 항목은 숨김이 초기화되므로 필터를 다시 먹인다
        self.sr_filter.refresh()
        self._sr_update_preview()

    def on_sr_refresh(self):
        infos = core.set_rename_ops.list_sets(
            include_shading_engines=self.sr_cb_shading.isChecked(),
            include_partitions=self.sr_cb_partitions.isChecked())
        self._sr_fill(infos)
        self._log("Set Rename : listed {0} set(s).".format(len(infos)))

    def _sr_listed_names(self):
        """지금 목록에 올라와 있는 세트 이름 전부 (숨김 여부와 무관)."""
        return [self.sr_tree.topLevelItem(i).data(0, Qt.UserRole)
                for i in range(self.sr_tree.topLevelItemCount())]

    def on_sr_add(self):
        """선택과 관련된 세트를 **기존 목록에 더한다**(교체하지 않는다)."""
        names = core.set_rename_ops.sets_from_selection()
        if not names:
            self._log("[WARN] Set Rename : no set in the selection, and the selected "
                      "objects do not belong to any set.")
            return

        listed = self._sr_listed_names()
        fresh = [n for n in names if n not in listed]
        if not fresh:
            self._log("Set Rename : already listed ({0} set(s)).".format(len(names)))
            return

        infos = [i for i in (core.set_rename_ops.set_info(n) for n in listed + fresh) if i]
        self._sr_fill(infos)
        self._log("Set Rename : added {0} set(s) ({1} already listed).".format(
            len(fresh), len(names) - len(fresh)))

    def on_sr_del(self):
        """하이라이트한 행을 **목록에서만** 뺀다. 씬의 세트는 그대로 둔다."""
        drop, hidden = self.sr_filter.visible_selected()
        if not drop:
            self._log("[WARN] Set Rename : highlight the rows to remove from the list.")
            return

        keep = [n for n in self._sr_listed_names() if n not in drop]
        infos = [i for i in (core.set_rename_ops.set_info(n) for n in keep) if i]
        self._sr_fill(infos)
        self._log("Set Rename : removed {0} row(s) from the list "
                  "(the sets are still in the scene).".format(len(drop)))
        if hidden:
            self._log("[Info] {0} highlighted row(s) are hidden by the filter and "
                      "were kept.".format(hidden))

    def on_sr_from_selection(self):
        names = core.set_rename_ops.sets_from_selection()
        if not names:
            self._log("[WARN] Set Rename : the selection does not belong to any set.")
            self._sr_fill([])
            return
        infos = [i for i in (core.set_rename_ops.set_info(n) for n in names) if i]
        self._sr_fill(infos)
        self._log("Set Rename : {0} set(s) from the selection.".format(len(infos)))

    def _sr_selected_names(self):
        """지금 보이면서 선택된 세트 이름 + 필터에 가려진 선택 수."""
        return self.sr_filter.visible_selected()

    def on_sr_selection_changed(self):
        self._sr_update_preview()

    def on_sr_select_in_scene(self):
        names, hidden = self._sr_selected_names()
        if not names:
            self._log("[WARN] Set Rename : highlight one or more sets first.")
            return
        count = core.set_rename_ops.select_sets_in_scene(names)
        self._log("Set Rename : selected {0} set(s) in the scene "
                  "(the sets themselves, not their members).".format(count))
        if hidden:
            self._log("[Info] {0} highlighted row(s) are hidden by the filter and "
                      "were skipped.".format(hidden))

    # ---- Set Rename : 미리보기 ----

    def _sr_rows_for_selection(self):
        names, hidden = self._sr_selected_names()
        rows = core.set_rename_ops.preview(
            names,
            self.sr_le_search.text(),
            self.sr_le_replace.text(),
            case_sensitive=self.sr_cb_case.isChecked())
        return rows, hidden

    def _sr_update_preview(self):
        """선택된 행에만 새 이름/상태를 적는다. 씬은 건드리지 않는다."""
        if not hasattr(self, "sr_tree"):
            return

        rows, _hidden = self._sr_rows_for_selection()
        by_name = {r["name"]: r for r in rows}

        for i in range(self.sr_tree.topLevelItemCount()):
            item = self.sr_tree.topLevelItem(i)
            name = item.data(0, Qt.UserRole)
            row = by_name.get(name)
            if row is None:
                item.setText(self._SR_COL_NEW, "")
                item.setText(self._SR_COL_STATUS, "")
                continue
            status = row["status"]
            # no change / invalid 는 새 이름 칸을 비워 둔다 - 바뀔 것이 없다는 뜻
            show_new = status not in (core.set_rename_ops.ST_SAME,
                                      core.set_rename_ops.ST_INVALID)
            item.setText(self._SR_COL_NEW, row["new_name"] if show_new else "")
            item.setText(self._SR_COL_STATUS,
                         status if not row["note"]
                         else "{0} - {1}".format(status, row["note"]))

    # ---- Set Rename : 적용 ----

    def on_sr_apply(self):
        rows, hidden = self._sr_rows_for_selection()
        if not rows:
            self._log("[WARN] Set Rename : highlight one or more sets first.")
            return
        if not self.sr_le_search.text():
            self._log("[WARN] Set Rename : the Search field is empty.")
            return

        counts = core.set_rename_ops.summarize(rows)
        applicable = [r for r in rows
                      if r["status"] in core.set_rename_ops.APPLICABLE]
        if not applicable:
            self._log("Set Rename : nothing to do ({0}).".format(
                ", ".join("{0} {1}".format(v, k) for k, v in sorted(counts.items()))))
            return

        with core.undo_chunk():
            _results, messages = core.set_rename_ops.apply_rename(applicable)

        for message in messages:
            self._log(message)

        skipped = {k: v for k, v in counts.items()
                   if k not in core.set_rename_ops.APPLICABLE}
        if skipped:
            self._log("[Info] skipped - {0}".format(
                ", ".join("{0} {1}".format(v, k) for k, v in sorted(skipped.items()))))
        if hidden:
            self._log("[Info] {0} highlighted row(s) are hidden by the filter and "
                      "were skipped.".format(hidden))

        # 이름이 바뀌었으니 목록을 다시 읽는다
        self.on_sr_refresh()

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def show_about(self, *args):
        message = (
            "Naming Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Qt port of legacy JUN_PY_NamingTool_V03_04, plus a new tab.\n"
            "\n"
            "[Rename > Token] name each object and its transform descendants\n"
            "  from tokens joined by '_'. Each token is Custom (text) or\n"
            "  Numbering (Start + Pad 0). Add / Delete Token; rules are kept in profiles.\n"
            "[Rename > Set Rename] search and replace inside set names.\n"
            "\n"
            "[Copy Name] copy Base leaf names onto Targets with a prefix.\n"
            "  Search / Replace swaps a word inside the Base name first.\n"
            "\n"
            "[Quick Rename > Selection] (ported from ref/ref_01.mel, current selection):\n"
            "  Front Insert / Change New (+index) / Last Add / -1 trim / All Apply.\n"
            "[Quick Rename > Insert] insert text at the n-th position of every listed\n"
            "  name (negative = counted from the end). Preview first, then Apply.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
