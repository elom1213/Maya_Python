# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00620_NameDecoder - Qt UI (in-Maya)
#
# 탭: Names(찾은 이름 표) · Blend Shapes(풀린 타겟 이름 + 웨이트) · Rename to ASCII(View 메뉴로 켬, 기본 숨김).
# 마야 UI(아웃라이너 · 채널 박스 · Shape Editor)의 글자는 바꿀 수 없어서 이 창에서 풀어 보여 준다 - Qt 는 유니코드를 그린다.
# 모든 UI 문자열/로그는 영어.

import maya.cmds as cmds

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QPushButton,
    QSlider,
    QFrame,
    QDoubleSpinBox,
    QScrollArea,
    QMenu,
    QMessageBox,
    QFileDialog,
    QApplication,
    QAction,
    QBrush,
    QColor,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_filter_qt_v01 import JUN_mod_filter_qt_v01
from Framework.qt.MOD_viewZoom_qt_v01 import JUN_mod_viewZoom_qt_v01
from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01
from Framework.qt.pin_style import apply_pin_style
from Framework.core import fbx_name
from Framework.core import maya_fbx_names as MFN

from tools.A00620_NameDecoder.app.config.version import VERSION, LAST_UPDATE
from tools.A00620_NameDecoder.app.core import name_table
from tools.A00620_NameDecoder.app.core import bs_weights
from tools.A00620_NameDecoder.app.core import ascii_rename as AR


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00620_NameDecoder_window"

_ENTRY_ROLE = Qt.UserRole

SCOPES = (
    ("Scene", MFN.SCOPE_SCENE),
    ("Selected", MFN.SCOPE_SELECTED),
    ("Selected + Hierarchy", MFN.SCOPE_HIERARCHY),
)

COL_DECODED, COL_RAW, COL_TYPE, COL_OWNER = range(4)

_BROKEN_COLOR = QColor(230, 200, 90)       # 깨진 FBXASC - 노랑
_PLAIN_COLOR = QColor(150, 150, 150)       # FBXASC 없는 이름(Encoded only 끔) - 회색
_STATUS_COLORS = {
    AR.ST_READY: QColor(120, 200, 120),
    AR.ST_RENAMED: QColor(120, 200, 120),
    AR.ST_NO_CHANGE: QColor(150, 150, 150),
}
_STATUS_WARN = QColor(230, 160, 90)

SLIDER_STEPS = 1000

# ------------------------------------------------------------------ Blend Shapes 게이지
# A00290_BSTool_V02 Shape Editor 의 WeightSlider 와 같은 이유로 슬라이더를 직접 그린다:
# 어떤 테마 qss 도 QSlider 를 꾸미지 않아 어두운 배경에선 마야 기본 홈(groove)이 묻혀 핸들만 보인다.
# 다른 점: A00290 은 -1~1 양방향이라 채움(sub-page)을 빼고 중앙 눈금으로 0 을 보였지만,
# 여기는 0~1 한 방향이라 **채운 길이 = 웨이트** 인 게이지로 그린다. 색은 purple_dark 테마(#9582b5)에 맞춘다.
WEIGHT_GAUGE_STYLE = (
    "QSlider:horizontal { min-height: 22px; }"
    # 홈: 빈 부분은 어둡게 + accent 테두리
    "QSlider::groove:horizontal {"
    " height: 10px; margin: 0 6px;"
    " background: #24222b; border: 1px solid #6f6385; border-radius: 5px; }"
    # 채운 부분(0 ~ 핸들) = 웨이트
    "QSlider::sub-page:horizontal {"
    " margin: 0 0 0 6px;"
    " background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6f5f96, stop:1 #b39ddb);"
    " border: 1px solid #9582b5; border-radius: 5px; }"
    "QSlider::add-page:horizontal {"
    " margin: 0 6px 0 0;"
    " background: #24222b; border: 1px solid #6f6385; border-radius: 5px; }"
    # 핸들: 홈 위아래로 튀어나오게
    "QSlider::handle:horizontal {"
    " width: 12px; margin: -5px -6px;"
    " background: #e4dbf2; border: 1px solid #9582b5; border-radius: 4px; }"
    "QSlider::handle:horizontal:hover { background: #ffffff; border: 1px solid #c0addf; }"
    # 비활성(구동 · 잠긴 웨이트): 전체를 회색으로
    "QSlider::groove:horizontal:disabled, QSlider::add-page:horizontal:disabled {"
    " background: #2f2f2f; border: 1px solid #454545; }"
    "QSlider::sub-page:horizontal:disabled { background: #555555; border: 1px solid #454545; }"
    "QSlider::handle:horizontal:disabled { background: #5a5a5a; border: 1px solid #454545; }"
)

BS_ROW_OBJECT_NAME = "bsWeightRow"
BS_LABEL_OBJECT_NAME = "bsWeightLabel"
BS_ROW_BG = "#2b2b2b"          # 테마 기본 배경
BS_ROW_BG_ALT = "#32303a"      # 번갈아 칠하는 줄 - purple 기운
BS_LABEL_IDLE = "#b8b8b8"      # 웨이트 0 인 타겟 이름
BS_LABEL_ACTIVE = "#e8dcff"    # 웨이트가 0 이 아닌 타겟 이름(굵게)
BS_ACTIVE_EPS = 0.0005         # 숫자 칸(소수 3자리)에 0.000 으로 보이는 값은 꺼진 것으로
BS_ROW_STYLE = (
    "QFrame#{name} {{ background-color: {bg}; border-radius: 3px; }}"
    "QLabel#{label} {{ color: {fg}; font-weight: {weight}; background: transparent; }}"
)


class WeightGauge(QSlider):
    """0 ~ 1 웨이트 게이지 - 채운 길이가 웨이트. 정수 슬라이더라 SLIDER_STEPS 배로 담는다(0.001 해상도).
    범위 밖 웨이트(-10 ~ 10 은 숫자 칸)는 게이지 끝에 붙는다."""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, SLIDER_STEPS)
        self.setSingleStep(SLIDER_STEPS // 100)   # 방향키 0.01
        self.setPageStep(SLIDER_STEPS // 10)      # PageUp/Down 0.1
        self.setMinimumWidth(120)
        self.setStyleSheet(WEIGHT_GAUGE_STYLE)

    def weight(self):
        return self.value() / float(SLIDER_STEPS)

    def set_weight(self, value):
        self.setValue(int(round(min(max(value, 0.0), 1.0) * SLIDER_STEPS)))


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("Name Decoder v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(680, 640)

        # 확인 창 - 테스트에서 끌 수 있게 속성으로
        self.confirm_before_apply = True

        self.entries = []          # Names 탭의 마지막 Scan 결과 [NameEntry]
        self.plans = []            # Rename 탭의 마지막 Preview [RenamePlan]
        self.bs_rows = []          # Blend Shapes 탭의 행 [dict]
        self._syncing = False
        self._sync_job = None

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Pin(우)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        view_menu = self.menu_bar.addMenu("View")
        self.act_rename_tab = QAction("Rename to ASCII Tab", self)
        self.act_rename_tab.setCheckable(True)
        self.act_rename_tab.setToolTip("Show the tab that renames FBXASC names to ASCII names.")
        self.act_rename_tab.toggled.connect(self.set_rename_tab_visible)
        view_menu.addAction(self.act_rename_tab)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)
        apply_pin_style(self.pin_button)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_names_tab(), "Names")
        self.tabs.addTab(self._build_bs_tab(), "Blend Shapes")
        self.rename_page = self._build_rename_tab()
        self.tabs.addTab(self.rename_page, "Rename to ASCII")
        main_layout.addWidget(self.tabs, stretch=3)
        self.set_rename_tab_visible(False)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # 공용 로그 위젯(Expand / Clear / Copy)
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Name Decoder - Log",
            object_name="JUN_A00620_NameDecoder_log_window")
        self.log_view.setMinimumHeight(110)
        main_layout.addWidget(self.log_view, stretch=1)

        self.tab_fit = JUN_mod_tabFit_qt_v01(self, self.tabs)

    # ------------------------------------------------------------------ Names

    def _build_names_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        row = QHBoxLayout()
        row.addWidget(QLabel("Scope"))
        self.cb_scope = QComboBox()
        for label, key in SCOPES:
            self.cb_scope.addItem(label, key)
        self.cb_scope.setToolTip("Scene: every node.\n"
                                 "Selected: the selected nodes, their shapes and their blendShapes.\n"
                                 "Selected + Hierarchy: also everything below the selected transforms.")
        row.addWidget(self.cb_scope)
        self.chk_encoded_only = QCheckBox("Encoded only")
        self.chk_encoded_only.setChecked(True)
        self.chk_encoded_only.setToolTip("On: only names with FBXASC in them.\nOff: every name in the scope.")
        row.addWidget(self.chk_encoded_only)
        self.chk_attrs = QCheckBox("Attributes")
        self.chk_attrs.setToolTip("Also look at user-defined attribute names and enum field names.")
        row.addWidget(self.chk_attrs)
        row.addStretch(1)
        self.btn_scan = QPushButton("Scan")
        self.btn_scan.setMinimumWidth(90)
        self.btn_scan.setToolTip("Find the names in the scope and show them decoded.")
        self.btn_scan.clicked.connect(self.scan)
        row.addWidget(self.btn_scan)
        lay.addLayout(row)

        self.tree_names = QTreeWidget()
        self.tree_names.setHeaderLabels(["Decoded", "Raw (Maya name)", "Type", "Owner"])
        self.tree_names.setRootIsDecorated(False)
        self.tree_names.setUniformRowHeights(True)
        self.tree_names.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_names.setSortingEnabled(True)
        self.tree_names.sortByColumn(-1, Qt.AscendingOrder)
        self.tree_names.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_names.customContextMenuRequested.connect(self._names_menu)
        self.tree_names.itemSelectionChanged.connect(self._on_names_selection)
        header = self.tree_names.header()
        header.setStretchLastSection(True)
        header.resizeSection(COL_DECODED, 170)
        header.resizeSection(COL_RAW, 230)
        header.resizeSection(COL_TYPE, 130)

        self.lbl_names_number = QLabel("Number: 0")
        self.flt_names = JUN_mod_filter_qt_v01(
            tree_widget=self.tree_names, tree_column=COL_DECODED,
            tree_columns=(COL_DECODED, COL_RAW, COL_TYPE, COL_OWNER),
            number_label=self.lbl_names_number,
            placeholder="Type decoded text (e.g. まば) or any part of the Maya name")
        lay.addWidget(self.flt_names)
        lay.addWidget(self.tree_names, stretch=1)
        self.zoom_names = JUN_mod_viewZoom_qt_v01(self.tree_names, key="A00620/names", default=1.0)

        row2 = QHBoxLayout()
        row2.addWidget(self.lbl_names_number)
        self.chk_sync = QCheckBox("Sync with Selection")
        self.chk_sync.setToolTip("Highlight the rows of the nodes selected in Maya.")
        self.chk_sync.toggled.connect(self.set_sync)
        row2.addWidget(self.chk_sync)
        row2.addStretch(1)
        row2.addWidget(self.zoom_names.controls())
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        self.btn_copy = QPushButton("Copy Decoded")
        self.btn_copy.setToolTip("Copy the decoded names of the selected rows (all visible rows if none).")
        self.btn_copy.clicked.connect(lambda: self.copy_rows("decoded"))
        row3.addWidget(self.btn_copy)
        self.btn_export = QPushButton("Export List...")
        self.btn_export.setToolTip("Save Decoded / Raw / Type / Owner of the visible rows as .csv or .json (UTF-8).")
        self.btn_export.clicked.connect(self.export_list)
        row3.addWidget(self.btn_export)
        self.btn_export_map = QPushButton("Export Map Template...")
        self.btn_export_map.setToolTip("Save every decoded piece (e.g. まばたき, 口, ' ') as a JSON map\n"
                                       "{\"piece\": \"\"} to fill in for Rename to ASCII.")
        self.btn_export_map.clicked.connect(self.export_map_template)
        row3.addWidget(self.btn_export_map)
        lay.addLayout(row3)
        return page

    # ------------------------------------------------------------------ Blend Shapes

    def _build_bs_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        row = QHBoxLayout()
        row.addWidget(QLabel("blendShape"))
        self.cb_bs = QComboBox()
        self.cb_bs.setMinimumWidth(200)
        self.cb_bs.currentIndexChanged.connect(self.load_bs_rows)
        row.addWidget(self.cb_bs, stretch=1)
        self.btn_bs_sel = QPushButton("From Selection")
        self.btn_bs_sel.setToolTip("Pick the blendShape of the selected mesh.")
        self.btn_bs_sel.clicked.connect(self.bs_from_selection)
        row.addWidget(self.btn_bs_sel)
        self.btn_bs_refresh = QPushButton("Refresh")
        self.btn_bs_refresh.setToolTip("Reload the blendShape list and the current weights.")
        self.btn_bs_refresh.clicked.connect(self.refresh_bs_list)
        row.addWidget(self.btn_bs_refresh)
        lay.addLayout(row)

        self.lbl_bs_number = QLabel("Number: 0")
        self.flt_bs = JUN_mod_filter_qt_v01(
            rows_provider=lambda: [(r["name"], r["widget"]) for r in self.bs_rows],
            number_label=self.lbl_bs_number,
            placeholder="Type decoded text (e.g. あ) or any part of the Maya name")
        lay.addWidget(self.flt_bs)

        self.bs_container = QWidget()
        self.bs_rows_layout = QVBoxLayout(self.bs_container)
        self.bs_rows_layout.setContentsMargins(2, 2, 2, 2)
        self.bs_rows_layout.setSpacing(1)
        self.bs_rows_layout.addStretch(1)
        self.bs_scroll = QScrollArea()
        self.bs_scroll.setWidgetResizable(True)
        self.bs_scroll.setWidget(self.bs_container)
        self.bs_scroll.setMinimumHeight(220)
        lay.addWidget(self.bs_scroll, stretch=1)

        row2 = QHBoxLayout()
        row2.addWidget(self.lbl_bs_number)
        row2.addStretch(1)
        self.btn_bs_reset = QPushButton("Reset All")
        self.btn_bs_reset.setToolTip("Set every weight to 0 (connected or locked weights are skipped).\n"
                                     "One Ctrl+Z undoes it.")
        self.btn_bs_reset.clicked.connect(self.reset_all_weights)
        row2.addWidget(self.btn_bs_reset)
        lay.addLayout(row2)
        return page

    # ------------------------------------------------------------------ Rename to ASCII

    def _build_rename_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        note = QLabel("Warning: FBX export turns FBXASC names back into the original text (e.g. まばたき).\n"
                      "ASCII names replace that original text. Restore Original Names brings them back.")
        note.setWordWrap(True)
        lay.addWidget(note)

        lay.addWidget(QLabel("Map (decoded piece -> ASCII)"))
        self.tbl_map = QTableWidget(0, 2)
        self.tbl_map.setHorizontalHeaderLabels(["Original", "ASCII"])
        self.tbl_map.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_map.verticalHeader().setVisible(False)
        self.tbl_map.setMinimumHeight(140)
        lay.addWidget(self.tbl_map, stretch=1)

        row = QHBoxLayout()
        for label, tip, slot in (
                ("Fill from Names", "Add every decoded piece of the Names tab that is not in the map yet.",
                 self.fill_map_from_names),
                ("Load Map...", "Load a JSON map {\"original\": \"ascii\"}.", self.load_map),
                ("Save Map...", "Save the map as JSON (UTF-8).", self.save_map),
                ("Clear Map", "Remove every row of the map.", lambda: self.tbl_map.setRowCount(0))):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        lay.addLayout(row)

        self.btn_preview = QPushButton("Preview")
        self.btn_preview.setToolTip("Show the new name of every node / blendShape target in the Names tab.\n"
                                    "Nothing changes until Apply.")
        self.btn_preview.clicked.connect(self.preview_rename)
        lay.addWidget(self.btn_preview)

        self.tree_preview = QTreeWidget()
        self.tree_preview.setHeaderLabels(["Decoded", "New name", "Status", "Raw (Maya name)"])
        self.tree_preview.setRootIsDecorated(False)
        self.tree_preview.setUniformRowHeights(True)
        self.tree_preview.setMinimumHeight(140)
        self.tree_preview.header().resizeSection(0, 150)
        self.tree_preview.header().resizeSection(1, 150)
        self.tree_preview.header().resizeSection(2, 160)
        lay.addWidget(self.tree_preview, stretch=1)

        row2 = QHBoxLayout()
        self.btn_apply = QPushButton("Apply ASCII Names")
        self.btn_apply.setToolTip("Rename the Ready rows. One Ctrl+Z undoes it.\n"
                                  "The original names are kept in the scene for Restore Original Names.")
        self.btn_apply.clicked.connect(self.apply_rename)
        row2.addWidget(self.btn_apply)
        self.btn_restore = QPushButton("Restore Original Names")
        self.btn_restore.setToolTip("Rename everything this tool renamed back to the original FBXASC names.")
        self.btn_restore.clicked.connect(self.restore_names)
        row2.addWidget(self.btn_restore)
        lay.addLayout(row2)
        self.lbl_stored = QLabel("Stored originals: 0")
        lay.addWidget(self.lbl_stored)
        return page

    def set_rename_tab_visible(self, visible):
        index = self.tabs.indexOf(self.rename_page)
        if hasattr(self.tabs, "setTabVisible"):
            self.tabs.setTabVisible(index, bool(visible))
        else:  # Qt 5.15 미만
            self.tabs.setTabEnabled(index, bool(visible))
        if visible:
            self.tabs.setCurrentIndex(index)
            self._update_stored_label()
        if self.act_rename_tab.isChecked() != bool(visible):
            self.act_rename_tab.setChecked(bool(visible))

    def _on_tab_changed(self, index):
        page = self.tabs.widget(index)
        if page is self.rename_page:
            self._update_stored_label()
        elif index == 1 and self.cb_bs.count() == 0:
            self.refresh_bs_list()

    # ==================================================================
    # Names
    # ==================================================================

    def log(self, msg):
        self.log_view.appendPlainText(msg)

    def scan(self):
        scope = self.cb_scope.currentData()
        if scope != MFN.SCOPE_SCENE and not cmds.ls(selection=True):
            self.log("[WARN] Nothing selected - select nodes or use Scope: Scene.")
        self.entries = MFN.scan(scope, encoded_only=self.chk_encoded_only.isChecked(),
                                include_attrs=self.chk_attrs.isChecked())
        self.fill_names()
        encoded = sum(1 for e in self.entries if e.encoded)
        broken = sum(1 for e in self.entries if not e.ok)
        kinds = {}
        for e in self.entries:
            kinds[e.kind] = kinds.get(e.kind, 0) + 1
        self.log("Scan ({0}): {1} name(s), {2} encoded{3}  [{4}]".format(
            self.cb_scope.currentText(), len(self.entries), encoded,
            ", {0} broken".format(broken) if broken else "",
            ", ".join("{0} {1}".format(v, k) for k, v in sorted(kinds.items()))))
        if broken:
            self.log("[WARN] {0} name(s) have FBXASC bytes that are not valid UTF-8 - shown raw (yellow).".format(broken))
        return self.entries

    def fill_names(self):
        self.tree_names.setSortingEnabled(False)
        self.tree_names.clear()
        for i, e in enumerate(self.entries):
            item = QTreeWidgetItem([e.decoded, e.raw, e.type_label(), e.owner])
            item.setData(COL_DECODED, _ENTRY_ROLE, i)
            item.setToolTip(COL_DECODED, e.decoded)
            item.setToolTip(COL_RAW, e.raw)
            if not e.ok:
                item.setForeground(COL_DECODED, QBrush(_BROKEN_COLOR))
            elif not e.encoded:
                item.setForeground(COL_DECODED, QBrush(_PLAIN_COLOR))
            self.tree_names.addTopLevelItem(item)
        self.tree_names.setSortingEnabled(True)
        self.flt_names.refresh()

    def _entry_of(self, item):
        index = item.data(COL_DECODED, _ENTRY_ROLE)
        return self.entries[index] if index is not None and 0 <= index < len(self.entries) else None

    def selected_entries(self):
        return [e for e in (self._entry_of(it) for it in self.tree_names.selectedItems()) if e]

    def visible_entries(self):
        out = []
        for i in range(self.tree_names.topLevelItemCount()):
            item = self.tree_names.topLevelItem(i)
            if not item.isHidden():
                e = self._entry_of(item)
                if e:
                    out.append(e)
        return out

    def _on_names_selection(self):
        if self._syncing:
            return
        entries = self.selected_entries()
        if entries:
            try:
                MFN.select_entries(entries)
            except RuntimeError as exc:
                self.log("[ERROR] Select: {0}".format(str(exc).strip()))

    def _names_menu(self, pos):
        menu = QMenu(self.tree_names)
        menu.addAction("Copy Decoded").triggered.connect(lambda: self.copy_rows("decoded"))
        menu.addAction("Copy Raw").triggered.connect(lambda: self.copy_rows("raw"))
        menu.addAction("Copy Both (tab)").triggered.connect(lambda: self.copy_rows("both"))
        menu.addSeparator()
        menu.addAction("Select in Maya").triggered.connect(lambda: MFN.select_entries(self.selected_entries()))
        menu.exec_(self.tree_names.viewport().mapToGlobal(pos))

    def copy_rows(self, what="decoded"):
        """고른 행(없으면 보이는 행 전부)을 클립보드로. 복사한 글."""
        entries = self.selected_entries() or self.visible_entries()
        if not entries:
            self.log("[WARN] Nothing to copy - Scan first.")
            return ""
        if what == "raw":
            lines = [e.raw for e in entries]
        elif what == "both":
            lines = ["{0}\t{1}".format(e.decoded, e.raw) for e in entries]
        else:
            lines = [e.decoded for e in entries]
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        self.log("Copied {0} name(s) ({1}).".format(len(lines), what))
        return text

    def export_list(self, path=None):
        entries = self.visible_entries()
        if not entries:
            self.log("[WARN] Nothing to export - Scan first.")
            return 0
        if not path:
            path, _flt = QFileDialog.getSaveFileName(self, "Export List", "fbxasc_names.csv",
                                                     "CSV (*.csv);;JSON (*.json)")
        if not path:
            return 0
        count = name_table.export_list(entries, path)
        self.log("Exported {0} row(s): {1}".format(count, path))
        return count

    def export_map_template(self, path=None):
        entries = self.visible_entries()
        if not entries:
            self.log("[WARN] Nothing to export - Scan first.")
            return 0
        if not path:
            path, _flt = QFileDialog.getSaveFileName(self, "Export Map Template", "fbxasc_map.json", "JSON (*.json)")
        if not path:
            return 0
        count = name_table.export_map_template(entries, path, existing=self.map_from_table())
        self.log("Exported map template with {0} piece(s): {1}".format(count, path))
        return count

    # ------------------------------------------------------------------ Sync

    def set_sync(self, on):
        self._kill_sync_job()
        if on:
            try:
                self._sync_job = cmds.scriptJob(event=["SelectionChanged", self.sync_from_maya])
            except RuntimeError as exc:
                self.log("[ERROR] Sync: {0}".format(str(exc).strip()))
                return
            self.sync_from_maya()

    def _kill_sync_job(self):
        if self._sync_job is not None:
            try:
                if cmds.scriptJob(exists=self._sync_job):
                    cmds.scriptJob(kill=self._sync_job, force=True)
            except RuntimeError:
                pass
            self._sync_job = None

    def sync_from_maya(self):
        """마야에서 고른 노드의 행을 표에서 고른다(마야 선택은 다시 바꾸지 않는다)."""
        try:
            uuids = MFN.selected_uuids()
        except Exception:  # noqa: BLE001 - 창이 닫히는 중 등
            return
        self._syncing = True
        try:
            self.tree_names.clearSelection()
            first = None
            for i in range(self.tree_names.topLevelItemCount()):
                item = self.tree_names.topLevelItem(i)
                e = self._entry_of(item)
                if e and e.uuid in uuids and e.kind == MFN.KIND_NODE:
                    item.setSelected(True)
                    first = first or item
            if first is not None:
                self.tree_names.scrollToItem(first)
        finally:
            self._syncing = False

    # ==================================================================
    # Blend Shapes
    # ==================================================================

    def refresh_bs_list(self):
        current = self.cb_bs.currentData()
        self.cb_bs.blockSignals(True)
        self.cb_bs.clear()
        for bs in bs_weights.blendshape_nodes():
            label = fbx_name.decode(bs)
            self.cb_bs.addItem(label if label == bs else "{0}  ({1})".format(label, bs), bs)
        index = self.cb_bs.findData(current) if current else 0
        self.cb_bs.setCurrentIndex(max(index, 0))
        self.cb_bs.blockSignals(False)
        self.load_bs_rows()

    def bs_from_selection(self):
        found = bs_weights.blendshapes_of_selection()
        if not found:
            self.log("[WARN] No blendShape on the selection.")
            return
        if self.cb_bs.findData(found[0]) < 0:
            self.refresh_bs_list()
        self.cb_bs.setCurrentIndex(self.cb_bs.findData(found[0]))
        if len(found) > 1:
            self.log("Selection has {0} blendShapes - showing {1}.".format(len(found), found[0]))

    def _clear_bs_rows(self):
        for r in self.bs_rows:
            r["widget"].setParent(None)
            r["widget"].deleteLater()
        self.bs_rows = []

    def load_bs_rows(self, *_args):
        self._clear_bs_rows()
        bs = self.cb_bs.currentData()
        if not bs or not cmds.objExists(bs):
            self.flt_bs.refresh()
            return
        for t in bs_weights.targets(bs):
            self.bs_rows.append(self._make_bs_row(t))
            self.bs_rows_layout.insertWidget(self.bs_rows_layout.count() - 1, self.bs_rows[-1]["widget"])
        self.flt_bs.refresh()

    def _make_bs_row(self, target):
        # 행 = QFrame(objectName 으로 스타일 대상 한정). 줄마다 배경을 번갈아 칠해 이름 ↔ 게이지 줄을 눈으로 따라가기 쉽게.
        w = QFrame()
        w.setObjectName(BS_ROW_OBJECT_NAME)
        alt = len(self.bs_rows) % 2 == 1
        row = QHBoxLayout(w)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(8)
        lbl = QLabel(target.decoded)
        lbl.setObjectName(BS_LABEL_OBJECT_NAME)
        lbl.setMinimumWidth(170)
        lbl.setToolTip("[{0}] {1}".format(target.index, target.alias))
        row.addWidget(lbl)
        slider = WeightGauge()
        spin = QDoubleSpinBox()
        spin.setRange(-10.0, 10.0)
        spin.setDecimals(3)
        spin.setSingleStep(0.05)
        # 칠 때마다 확정하면 "0.1" 에서 setValue 가 "0.100" 으로 다시 써서 뒷자리를 못 친다 - Enter / 포커스 아웃에서 확정
        spin.setKeyboardTracking(False)
        spin.setFixedWidth(72)
        value = bs_weights.get_weight(target.plug)
        slider.set_weight(value)
        spin.setValue(value)
        row.addWidget(slider, stretch=1)
        row.addWidget(spin)
        info = {"name": "{0}\n{1}".format(target.decoded, target.alias), "widget": w, "label": lbl,
                "plug": target.plug, "slider": slider, "spin": spin, "alt": alt, "editable": target.editable}
        if not target.editable:
            slider.setEnabled(False)
            spin.setEnabled(False)
            w.setToolTip("Driven by {0}".format(target.source) if target.source else "Locked")
        else:
            slider.setToolTip("Drag to set the weight (0 left, 1 right). The filled part is the weight.\n"
                              "Values outside 0-1 are in the number box.")
            slider.sliderPressed.connect(lambda: cmds.undoInfo(openChunk=True, chunkName="A00620_weight"))
            slider.sliderReleased.connect(lambda: cmds.undoInfo(closeChunk=True))
            slider.valueChanged.connect(lambda _v, r=info: self._on_slider(r))
            spin.valueChanged.connect(lambda _v, r=info: self._on_spin(r))
        self._style_bs_row(info, value)
        return info

    @staticmethod
    def _style_bs_row(info, weight):
        """행 배경(번갈아) + 웨이트가 0 이 아니면 이름을 밝게 · 굵게 - 켜진 타겟이 한눈에 보이게."""
        active = abs(weight) > BS_ACTIVE_EPS
        info["widget"].setStyleSheet(BS_ROW_STYLE.format(
            name=BS_ROW_OBJECT_NAME, label=BS_LABEL_OBJECT_NAME,
            bg=BS_ROW_BG_ALT if info["alt"] else BS_ROW_BG,
            fg=BS_LABEL_ACTIVE if active else BS_LABEL_IDLE,
            weight="bold" if active else "normal"))

    def _on_slider(self, info):
        weight = info["slider"].weight()
        bs_weights.set_weight(info["plug"], weight)
        info["spin"].blockSignals(True)
        info["spin"].setValue(weight)
        info["spin"].blockSignals(False)
        self._style_bs_row(info, weight)

    def _on_spin(self, info):
        value = info["spin"].value()
        bs_weights.set_weight(info["plug"], value)
        info["slider"].blockSignals(True)
        info["slider"].set_weight(value)
        info["slider"].blockSignals(False)
        self._style_bs_row(info, value)

    def reset_all_weights(self):
        bs = self.cb_bs.currentData()
        if not bs or not cmds.objExists(bs):
            self.log("[WARN] No blendShape picked.")
            return
        changed, skipped = bs_weights.reset_all(bs)
        self.load_bs_rows()
        self.log("Reset {0} weight(s) to 0{1}.".format(changed, ", skipped {0} connected/locked".format(skipped)
                                                         if skipped else ""))

    # ==================================================================
    # Rename to ASCII
    # ==================================================================

    def map_from_table(self):
        mapping = {}
        for r in range(self.tbl_map.rowCount()):
            k = self.tbl_map.item(r, 0)
            v = self.tbl_map.item(r, 1)
            if k and k.text():
                mapping[k.text()] = v.text().strip() if v else ""
        return mapping

    def set_map(self, mapping):
        self.tbl_map.setRowCount(0)
        for k, v in mapping.items():
            self._add_map_row(k, v)

    def _add_map_row(self, key, value=""):
        r = self.tbl_map.rowCount()
        self.tbl_map.insertRow(r)
        k = QTableWidgetItem(key)
        k.setFlags(k.flags() & ~Qt.ItemIsEditable)
        k.setToolTip(" ".join("U+{0:04X}".format(ord(c)) for c in key))
        self.tbl_map.setItem(r, 0, k)
        self.tbl_map.setItem(r, 1, QTableWidgetItem(value))

    def fill_map_from_names(self):
        if not self.entries:
            self.log("[WARN] Scan in the Names tab first.")
            return 0
        known = self.map_from_table()
        added = 0
        for piece in name_table.map_pieces(self.entries):
            if piece not in known:
                self._add_map_row(piece)
                added += 1
        self.log("Map: added {0} piece(s), {1} in total.".format(added, self.tbl_map.rowCount()))
        return added

    def load_map(self, path=None):
        if not path:
            path, _flt = QFileDialog.getOpenFileName(self, "Load Map", "", "JSON (*.json)")
        if not path:
            return
        try:
            mapping = AR.load_map(path)
        except (IOError, OSError, ValueError) as exc:
            self.log("[ERROR] Load Map: {0}".format(exc))
            return
        self.set_map(mapping)
        self.log("Loaded map with {0} piece(s): {1}".format(len(mapping), path))

    def save_map(self, path=None):
        if not path:
            path, _flt = QFileDialog.getSaveFileName(self, "Save Map", "fbxasc_map.json", "JSON (*.json)")
        if not path:
            return
        mapping = self.map_from_table()
        AR.save_map(mapping, path)
        self.log("Saved map with {0} piece(s): {1}".format(len(mapping), path))

    def preview_rename(self):
        if not self.entries:
            self.log("[WARN] Scan in the Names tab first.")
            return []
        self.plans = AR.preview([e for e in self.entries if e.encoded], self.map_from_table())
        self.tree_preview.clear()
        for p in self.plans:
            item = QTreeWidgetItem([p.entry.decoded, p.new, p.status + (": " + p.note if p.note else ""),
                                    p.entry.raw])
            item.setForeground(2, QBrush(_STATUS_COLORS.get(p.status, _STATUS_WARN)))
            self.tree_preview.addTopLevelItem(item)
        ready = sum(1 for p in self.plans if p.ready)
        self.log("Preview: {0} of {1} name(s) ready.".format(ready, len(self.plans)))
        return self.plans

    def apply_rename(self):
        ready = [p for p in self.plans if p.ready]
        if not ready:
            self.log("[WARN] Nothing ready - fill the map and Preview first.")
            return []
        if self.confirm_before_apply:
            answer = QMessageBox.warning(
                self, "Apply ASCII Names",
                "Rename {0} name(s) to ASCII?\n\n"
                "FBX export writes FBXASC names back as the original text (e.g. まばたき).\n"
                "After this, it writes the ASCII names instead.\n\n"
                "One Ctrl+Z undoes it. Restore Original Names brings the old names back later.".format(len(ready)),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                self.log("Cancelled.")
                return []
        results = AR.apply(ready, log=self.log)
        done = sum(1 for _p, st, _n in results if st == AR.ST_RENAMED)
        self.log("Renamed {0} of {1} name(s).".format(done, len(ready)))
        self._update_stored_label()
        self.scan()
        self.plans = []
        self.tree_preview.clear()
        return results

    def restore_names(self):
        if AR.stored_count() == 0:
            self.log("[WARN] No renamed names are stored in this scene.")
            return 0, 0
        done, failed = AR.restore(log=self.log)
        self.log("Restored {0} name(s){1}.".format(done, ", {0} failed".format(failed) if failed else ""))
        self._update_stored_label()
        self.scan()
        return done, failed

    def _update_stored_label(self):
        try:
            self.lbl_stored.setText("Stored originals: {0}".format(AR.stored_count()))
        except Exception:  # noqa: BLE001
            pass

    # ==================================================================
    # 창 동작
    # ==================================================================

    def closeEvent(self, event):
        self._kill_sync_job()
        super().closeEvent(event)

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Name Decoder v{0}\nLast update : {1}\n\n"
            "Maya's FBX importer turns characters Maya cannot use in names\n"
            "(Japanese, Chinese, spaces, a leading digit ...) into FBXASC + byte code,\n"
            "e.g. FBXASC227FBXASC129FBXASC130 = あ.\n\n"
            "This tool shows those names decoded. Maya itself cannot show them -\n"
            "it rejects such characters in node names.\n\n"
            "Keep the FBXASC names if the file goes back to FBX: the exporter\n"
            "writes them as the original text again.".format(VERSION, LAST_UPDATE),
        )
