# -*- coding: utf-8 -*-
# main_window.py - Release Builder UI (QWidget)

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
    QTextEdit,
    QFileDialog,
    QCheckBox,
)

from ..config.version import VERSION
from ..core.release_builder import ReleaseBuilder

# 기존 dev/build_release.py 의 RELEASE_ROOT_PARENT 를 기본값으로 사용
DEFAULT_DEST = r"G:/D_link_dir/02_Maya_python_Jun_Release/Maya_Tool_Release/tools"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.builder = ReleaseBuilder()

        self.setWindowTitle(f"Release Builder v{VERSION}")
        self.resize(600, 480)

        self.build_ui()
        self.refresh_tools()

    def build_ui(self):

        self.layout = QVBoxLayout(self)

        # --- Tool list ---
        self.layout.addWidget(QLabel("Tools to release"))

        self.list_tools = QListWidget()
        self.layout.addWidget(self.list_tools)

        # Select All / Clear / Refresh
        row_select = QHBoxLayout()

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self.on_select_all)
        row_select.addWidget(self.btn_select_all)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.on_clear)
        row_select.addWidget(self.btn_clear)

        self.btn_refresh = QPushButton("Refresh")
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
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.layout.addWidget(self.log_widget)

    # ---------------------------------------------------------------- helpers

    def log(self, text):
        self.log_widget.append(str(text))

    def refresh_tools(self):

        self.list_tools.clear()

        for name in self.builder.list_tools():

            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_tools.addItem(item)

        self.log(f"Found {self.list_tools.count()} tools in {self.builder.tools_root}")

    def checked_tools(self):

        names = []

        for i in range(self.list_tools.count()):
            item = self.list_tools.item(i)
            if item.checkState() == Qt.Checked:
                names.append(item.text())

        return names

    def _set_all_check(self, state):
        for i in range(self.list_tools.count()):
            self.list_tools.item(i).setCheckState(state)

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

        names = self.checked_tools()

        if not names:
            self.log("No tools selected")
            return

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
