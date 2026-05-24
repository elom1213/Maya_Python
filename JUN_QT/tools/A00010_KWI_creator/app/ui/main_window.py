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

from app.core.file_processor import process_file
from app.core.KWI_creator import KWI_creator


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_title = "Kawaii Creator v01.00"
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

        self.ipf_setting_nodes_num = QLineEdit()    
        self.ipf_setting_nodes_num.setPlaceholderText("1")

        # radio button
        self.radio_create_multiple_nodes = QRadioButton("Multiple Nodes")
        self.radio_create_single_node    = QRadioButton("Single Node")

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
        self.layout.addWidget(self.ipf_setting_nodes_num)

        self.layout.addWidget(self.btn_create_base_nodes)
        self.layout.addWidget(self.btn_create_setting_nodes)
        self.layout.addWidget(self.btn_create_LD_nodes)
        self.layout.addWidget(self.log_widget)

    def is_create_multiple_nodes(self):
        return self.radio_create_multiple_nodes.isChecked()

    def log_create_create_mult_nodes(self):

        create_mult_nodes = self.is_create_multiple_nodes()
        log = None

        if create_mult_nodes:
            log = "Create multiple nodees"
        else :
            log = "Create single nodee"


        self.log_main.append(log)

    def create_base_nodes_on_click(self):

        create_mult_nodes = self.is_create_multiple_nodes()


        self.KWI_creator.reset_create_type()
        self.KWI_creator.create_multiple_nodes = create_mult_nodes
        self.KWI_creator.create_single_node = not create_mult_nodes

        self.KWI_creator.create_base_nodes()

        self.log_create_create_mult_nodes()
        self.log(self.log_main)


    def create_setting_nodes_on_click(self):

        num_setting_node__ = self.ipf_setting_nodes_num.text()

        try:
            num_setting_node__ = int(num_setting_node__)

        except ValueError:

            self.log("Must be integer")
            return
        
        print(num_setting_node__)
        print(type(num_setting_node__))

        self.KWI_creator.num_setting_node = num_setting_node__
        self.KWI_creator.create_setting_nodes()

    def create_LD_nodes_on_click(self):
        self.KWI_creator.create_LD_nodes()

    def log(self, message):

        self.log_widget.append(str(message))