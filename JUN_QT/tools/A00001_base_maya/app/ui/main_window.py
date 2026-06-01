from PySide2.QtWidgets import (
    QWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QFileDialog
)

from tools.A00001_base_maya.app.core.file_processor import process_file


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("My Qt Tool")

        self.resize(600, 400)

        self.build_ui()

    def build_ui(self):

        self.layout = QVBoxLayout(self)

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