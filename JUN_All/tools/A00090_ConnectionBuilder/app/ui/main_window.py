# from Framework.qt.qt import QApplication
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

import maya.cmds as cmds
from tools.A00090_ConnectionBuilder.app.config.version import VERSION

from tools.A00090_ConnectionBuilder.app.core import RuleLoader
from tools.A00090_ConnectionBuilder.app.core import ConnectionManager


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_width      =  700
        self.win_height     =  500
        self.win_title     =  f"MetaHuman Connection Builder v{VERSION}"
        self.btn_get_label = "Get"
        self.btn_width_01 = 40

        self.manager = ConnectionManager()

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    def build_ui(self):

        self.setWindowTitle(self.win_title)

        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowStaysOnTopHint
        )

        main_layout = QVBoxLayout(self)

        # -------------------------
        # Solver
        # -------------------------
        row = QHBoxLayout()

        row.addWidget(QLabel("Solver"))

        self.le_solver = QLineEdit()

        row.addWidget(self.le_solver)


        self.btn_solver = QPushButton(self.btn_get_label)

        self.btn_solver.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_solver)


        main_layout.addLayout(row)

        # -------------------------
        # Driver
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("Driver"))

        self.le_driver = QLineEdit()

        row.addWidget(self.le_driver)


        self.btn_driver = QPushButton(self.btn_get_label)

        self.btn_driver.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_driver)


        main_layout.addLayout(row)

        # -------------------------
        # BlendShape
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("BlendShape"))

        self.le_blendshape = QLineEdit()

        row.addWidget(self.le_blendshape)

        
        self.btn_blendShape = QPushButton(self.btn_get_label)

        self.btn_blendShape.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_blendShape)


        main_layout.addLayout(row)

        # -------------------------
        # Rule
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("Rule"))

        self.cb_rule = QComboBox()

        self.cb_rule.addItems([
            "elbow_l",
            "elbow_r",
            "shoulder_l"
        ])

        row.addWidget(self.cb_rule)

        main_layout.addLayout(row)

        # -------------------------
        # Buttons
        # -------------------------

        row = QHBoxLayout()

        self.btn_connect = QPushButton("Connect")

        self.btn_disconnect = QPushButton("Disconnect")

        self.btn_validate = QPushButton("Validate")

        row.addWidget(self.btn_connect)
        row.addWidget(self.btn_disconnect)
        row.addWidget(self.btn_validate)


        main_layout.addLayout(row)

        # -------------------------
        # Log
        # -------------------------

        self.te_log = QTextEdit()

        self.te_log.setReadOnly(True)

        main_layout.addWidget(self.te_log)

        # -------------------------
        # Signal
        # -------------------------

        # -------------------------
        # button connect
        # -------------------------

        self.btn_connect.clicked.connect(
            self.on_connect
        )

        self.btn_disconnect.clicked.connect(
            self.on_disconnect
        )

        self.btn_validate.clicked.connect(
            self.on_validate
        )

        self.btn_solver.clicked.connect(
            lambda: self.set_selected_node(
                self.le_solver
            )
        )

        self.btn_driver.clicked.connect(
            lambda: self.set_selected_node(
                self.le_driver
            )
        )

        self.btn_blendShape.clicked.connect(
            lambda: self.set_selected_node(
                self.le_blendshape
            )
        )

    def log(self, text):

        self.te_log.append(text)
    
    # -------------------------------------------------

    def get_rule(self):

        return RuleLoader.load(

            rule_name=self.cb_rule.currentText(),

            solver_node=self.le_solver.text(),

            driver_node=self.le_driver.text(),

            blendshape_node=self.le_blendshape.text()
        )

    def on_connect(self):

        rule = self.get_rule()

        self.manager.connect(rule)

        self.log("Connect Finished")

    # -------------------------------------------------

    def on_disconnect(self):

        rule = self.get_rule()

        self.manager.disconnect(rule)

        self.log("Disconnect Finished")

    # -------------------------------------------------

    def on_validate(self):

        rule = self.get_rule()

        result = self.manager.validate(rule)

        self.log(
            f"Validate Result : {result}"
        )

    def set_selected_node(self, line_edit):

        selection = cmds.ls(sl=True)

        if not selection:
            return

        line_edit.setText(
            ", ".join(selection)
        )
