from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QPushButton,
    QLineEdit,
    QLabel,
    QTextEdit,
)

from tools.A00080_KWI_creator_V02.app.config.version import VERSION
from tools.A00080_KWI_creator_V02.app.core.file_processor import process_file
from tools.A00080_KWI_creator_V02.app.core.KWI_creator import KWI_creator


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_title = f"Kawaii Creator v{VERSION}"
        self.win_width = 600
        self.win_hight = 400

        self.log_main = []

        self.KWI_creator = KWI_creator()

        self.setWindowTitle(self.win_title)

        self.resize(self.win_width, self.win_hight)

        self.build_ui()

    def build_ui(self):

        self.layout = QVBoxLayout(self)

        self.label_create_type = QLabel("Create type")
        self.label_setting_nodes_num = QLabel("Setting nodes Number")

        self.ipf_setting_nodes_interval = QLineEdit()    
        self.ipf_setting_nodes_interval.setText ("1")

        # radio button
        self.radio_create_multiple_nodes = QRadioButton("Multiple Nodes")
        self.radio_create_single_node    = QRadioButton("Single Node")

        self.radio_create_multiple_nodes.toggled.connect(
                                                            lambda checked:
                                                            checked and self.KWI_creator.set_mode("multiple")
                                                            )
        self.radio_create_single_node.toggled.connect(      lambda checked:
                                                            checked and self.KWI_creator.set_mode("single")
                                                            )
        self.radio_create_multiple_nodes.setChecked(True)

        # btn : create nodes
        self.btn_create_base_nodes = QPushButton("Create base nodes")
        self.btn_create_base_nodes.clicked.connect(self.create_base_nodes_on_click)

        self.btn_create_setting_nodes = QPushButton("Create setting nodes")
        self.btn_create_setting_nodes.clicked.connect(self.create_setting_nodes_on_click)

        self.btn_create_LD_nodes = QPushButton("Create LD nodes")
        self.btn_create_LD_nodes.clicked.connect(self.create_LD_nodes_on_click)

        # out put log
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)

        # set layout

        self.layout.addWidget(self.label_create_type)
        
        self.layout.addWidget(self.radio_create_multiple_nodes)
        self.layout.addWidget(self.radio_create_single_node)

        self.layout.addWidget(self.label_setting_nodes_num)
        self.layout.addWidget(self.ipf_setting_nodes_interval)

        self.layout.addWidget(self.btn_create_base_nodes)
        self.layout.addWidget(self.btn_create_setting_nodes)
        self.layout.addWidget(self.btn_create_LD_nodes)
        self.layout.addWidget(self.log_widget)

    def is_create_multiple_nodes(self):
        return self.radio_create_multiple_nodes.isChecked()

    def create_base_nodes_on_click(self):

        self.KWI_creator.create_base_nodes()
        mode_current = self.KWI_creator.create_mode
        mode_current = "Current mode  :  " + str(mode_current)
        self.log(mode_current)


    def create_setting_nodes_on_click(self):

        interval_setting_node__ = self.ipf_setting_nodes_interval.text()

        try:
            interval_setting_node__ = int(interval_setting_node__)

        except ValueError:

            self.log("Must be integer")
            return

        self.KWI_creator.interval_setting_node = interval_setting_node__
        self.KWI_creator.create_setting_nodes()

    def create_LD_nodes_on_click(self):
        self.KWI_creator.create_LD_nodes()

    def log(self, message):

        self.log_widget.append(str(message))