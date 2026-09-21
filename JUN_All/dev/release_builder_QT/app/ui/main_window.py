# -*- coding: utf-8 -*-
# main_window.py - Release Builder UI (QWidget)
#
# 툴이 50개를 넘어가면서 목록에서 눈으로 찾는 것이 일이 됐다. 그래서 공용 검색 위젯
# `JUN_mod_filter_qt_v01` 을 붙였다(v01.02) — 다른 툴들과 **같은 규칙**이다.
#   * 부분 일치 · 대소문자 무시 · 공백으로 나눈 여러 단어는 AND
#   * 항목을 지우는 게 아니라 `setHidden` 으로 가리므로 필터를 비우면 돌아온다
#   * `Number: 보이는수 / 전체수` 가 헤더에 붙는다
#
# ★ 체크는 필터와 **따로 논다** — Qt 는 숨긴 항목의 체크를 유지한다. 그래서
#   `Select All` / `Clear` 는 **보이는 것에만** 걸고(그게 필터를 쓰는 이유다),
#   릴리즈할 때 **가려진 채 체크된 것이 몇 개인지 로그로 알린다** — 체크는 명시적인
#   의사표시라 없던 일로 하지 않되, 모르고 나가는 일도 없게.
#
# 로그창도 공용 위젯 `JUN_mod_log_qt_v01` 로 바꿨다(v01.02) — Expand / Shrink /
# Clear / Copy 가 딸려 오고, 다른 툴과 조작이 같다.

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QCheckBox,
)

from Framework.qt import JUN_mod_filter_qt
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

from ..config.version import VERSION
from ..core.release_builder import ReleaseBuilder
from ..config.app_meta import window_icon

# 기존 dev/build_release.py 의 RELEASE_ROOT_PARENT 를 기본값으로 사용
DEFAULT_DEST = r"G:/D_link_dir/02_Maya_python_Jun_Release/Maya_Tool_Release/tools"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.builder = ReleaseBuilder()

        self.setWindowTitle(f"Release Builder v{VERSION}")
        self.resize(600, 560)

        # 창(그리고 작업 표시줄) 아이콘. 파일이 없으면 조용히 넘어간다.
        icon = window_icon()
        if icon is not None:
            self.setWindowIcon(icon)

        self.build_ui()
        self.refresh_tools()

    def build_ui(self):

        self.layout = QVBoxLayout(self)

        # --- Tool list ---
        head = QHBoxLayout()
        head.addWidget(QLabel("Tools to release"))
        head.addStretch(1)
        self.lbl_number = QLabel("Number: 0")
        head.addWidget(self.lbl_number)
        self.layout.addLayout(head)

        self.list_tools = QListWidget()
        self.layout.addWidget(self.list_tools)

        # --- Filter (v01.02) : 공용 검색 위젯. 목록을 다시 채운 뒤엔 refresh() 를 부른다.
        self.flt_tools = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.list_tools,
            placeholder="Type any part of a tool name (e.g. skin, A004)",
            number_label=self.lbl_number)
        self.layout.addWidget(self.flt_tools)

        # Select All / Clear / Refresh
        row_select = QHBoxLayout()

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setToolTip(
            "Check every tool the filter is showing.\n"
            "Entries hidden by the filter keep whatever they had.")
        self.btn_select_all.clicked.connect(self.on_select_all)
        row_select.addWidget(self.btn_select_all)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setToolTip(
            "Uncheck every tool the filter is showing.\n"
            "Entries hidden by the filter keep whatever they had.")
        self.btn_clear.clicked.connect(self.on_clear)
        row_select.addWidget(self.btn_clear)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip(
            "Read the tools folder again. The filter text stays as it is.")
        self.btn_refresh.clicked.connect(self.refresh_tools)
        row_select.addWidget(self.btn_refresh)

        self.layout.addLayout(row_select)

        # --- Destination ---
        self.layout.addWidget(QLabel("Release destination"))

        row_dest = QHBoxLayout()

        self.ipf_dest = QLineEdit()
        self.ipf_dest.setText(DEFAULT_DEST)
        row_dest.addWidget(self.ipf_dest)

        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.on_browse)
        row_dest.addWidget(self.btn_browse)

        self.layout.addLayout(row_dest)

        # --- Options ---
        self.chk_docs = QCheckBox("Include docs")
        self.chk_docs.setChecked(True)
        self.layout.addWidget(self.chk_docs)

        # --- Release ---
        self.btn_release = QPushButton("Release")
        self.btn_release.setMinimumHeight(36)
        self.btn_release.clicked.connect(self.on_release)
        self.layout.addWidget(self.btn_release)

        # --- Log ---
        # 공용 로그창(v01.02) : Expand / Shrink / Clear / Copy 가 딸려 온다.
        # 다른 툴들과 같은 물건이라 조작이 같고, 긴 릴리즈 로그를 별도 창으로 띄워
        # 크게 볼 수 있다.
        self.log_widget = JUN_mod_log_qt_v01(
            window_title="Release Builder - Log",
            object_name="JUN_release_builder_QT_log_window")
        self.layout.addWidget(self.log_widget, 1)

    # ---------------------------------------------------------------- helpers

    def log(self, text):
        # 공용 위젯의 `append()` 는 HTML 을 해석한다. 이 로그에는 경로와 `=` 구분선이
        # 들어가므로 **글자 그대로** 넣는 쪽을 쓴다.
        self.log_widget.appendPlainText(str(text))

    def refresh_tools(self):

        self.list_tools.clear()

        for name in self.builder.list_tools():

            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_tools.addItem(item)

        # 목록을 다시 채웠으므로 필터를 다시 먹인다(필터 글자는 그대로 남는다).
        self.flt_tools.refresh()

        self.log(f"Found {self.list_tools.count()} tools in {self.builder.tools_root}")

        if self.flt_tools.text().strip():
            self.log(f"Filter '{self.flt_tools.text().strip()}' is on - "
                     f"showing {len(self.flt_tools.visible_items())} of them.")

    def checked_tools(self):
        """체크된 툴 이름들 + 그 중 **필터에 가려진** 개수.

        Qt 는 숨긴 항목의 체크를 유지한다. 체크는 명시적인 의사표시라 가려졌다고 빼지
        않되, 모르고 나가는 일이 없도록 **몇 개가 가려져 있었는지** 함께 돌려준다.
        """
        names = []
        hidden = 0

        for i in range(self.list_tools.count()):
            item = self.list_tools.item(i)
            if item.checkState() != Qt.Checked:
                continue

            names.append(item.text())
            if item.isHidden():
                hidden += 1

        return names, hidden

    def _set_all_check(self, state):
        """**보이는 항목만** 체크/해제한다 - 필터를 거는 이유가 그것이다."""
        for item in self.flt_tools.visible_items():
            item.setCheckState(state)

    # ----------------------------------------------------------------- slots

    def on_select_all(self):
        self._set_all_check(Qt.Checked)

    def on_clear(self):
        self._set_all_check(Qt.Unchecked)

    def on_browse(self):

        path = QFileDialog.getExistingDirectory(
            self,
            "Select release destination",
            self.ipf_dest.text(),
        )

        if path:
            self.ipf_dest.setText(path)

    def on_release(self):

        names, hidden = self.checked_tools()

        if not names:
            self.log("No tools selected")
            return

        if hidden:
            self.log(f"[NOTE] {hidden} checked tool(s) are hidden by the filter "
                     f"- they are released too.")

        dest = self.ipf_dest.text().strip()

        if not dest:
            self.log("Release destination is empty")
            return

        self.log("=" * 50)
        self.log(f"Releasing {len(names)} tool(s) -> {dest}")

        results = self.builder.release(
            names,
            dest,
            include_framework=True,
            include_docs=self.chk_docs.isChecked(),
            log=self.log,
        )

        self.log(f"Done. {len(results)} tool(s) released.")
        self.log("=" * 50)
