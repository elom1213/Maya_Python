# from Framework.qt.qt import QApplication 
from Framework.qt.qt import * 
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

print("QT version  :  " + str(QT_VERSION))

from tools.A00090_ConnectionBuilder.app.config.version import VERSION

from tools.A00001_base_maya.app.core.file_processor import process_file
from tools.A00090_ConnectionBuilder.app.core import RuleLoader
from tools.A00090_ConnectionBuilder.app.core import ConnectionManager


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.win_width      =  600
        self.win_height     =  400
        self.win_title     =  f"MetaHuman Connection Builder v{VERSION}"

        self.setWindowTitle("My Qt Tool")

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    def build_ui(self):

        self.layout = QVBoxLayout(self)

        self.setWindowTitle(self.win_title)

        self.setWindowFlags(Qt.Window)

        # 버튼
        self.btn_open = QPushButton("Open File")

        self.btn_open.clicked.connect(self.on_open_file)

        self.layout.addWidget(self.btn_open)

        # 로그창 - 공용 위젯(Expand / Clear / Copy).
        # ★ 이 템플릿을 복제해 새 툴을 만들 때 object_name 을 그 툴의 것으로
        #    바꾼다. 같은 이름이면 Expand 창이 서로를 찾아 닫는다.
        self.log_widget = JUN_mod_log_qt_v01(
            window_title="Qt Tool - Log",
            object_name="JUN_A00008_base_QT_maya_log_window")

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