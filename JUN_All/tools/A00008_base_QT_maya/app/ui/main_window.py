# from Framework.qt.qt import QApplication 
from Framework.qt.qt import * 

print("QT version  :  " + str(QT_VERSION))
'''
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QFileDialog
)
'''

from tools.A00090_ConnectionBuilder.app.config.version import VERSION

from tools.A00001_base_maya.app.core.file_processor import process_file
from tools.A00090_ConnectionBuilder.app.core import RuleLoader
from tools.A00090_ConnectionBuilder.app.core import ConnectionManager


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_width      =  600
        self.win_height     =  400
        self.win_title     =  f"MetaHuman Connection Builder v{VERSION}"

        self.setWindowTitle("My Qt Tool")

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    def build_ui(self):

        self.layout = QVBoxLayout(self)

        self.setWindowTitle(self.win_title)

        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowStaysOnTopHint
        )

        # 버튼
        self.btn_open = QPushButton("Open File")

        self.btn_open.clicked.connect(self.on_open_file)

        self.layout.addWidget(self.btn_open)

        # 로그창
        self.log_widget = QTextEdit()

        self.log_widget.setReadOnly(True)

        self.layout.addWidget(self.log_widget)

    def log(self, text):

        self.log_widget.append(text)

    def on_open_file(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File"
        )

        if not file_path:
            return

        self.log(f"Selected File : {file_path}")

        result = process_file(file_path)

        self.log(result)