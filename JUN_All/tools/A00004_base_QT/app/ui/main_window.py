from Framework.qt.qt import (
    QWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QFileDialog
)
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

from JUN_All.tools.A00004_base_QT.app.core.file_processor import process_file


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

        # 로그창 - 공용 위젯(Expand / Clear / Copy).
        # ★ 이 템플릿을 복제해 새 툴을 만들 때 object_name 을 그 툴의 것으로
        #    바꾼다. 같은 이름이면 Expand 창이 서로를 찾아 닫는다.
        self.log_widget = JUN_mod_log_qt_v01(
            window_title="Qt Tool - Log",
            object_name="JUN_A00004_base_QT_log_window")

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