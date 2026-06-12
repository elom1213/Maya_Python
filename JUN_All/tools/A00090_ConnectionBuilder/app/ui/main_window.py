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

import sys, os
import maya.cmds as cmds
from tools.A00090_ConnectionBuilder.app.config.version import VERSION
from Framework.core.path_manager import PathManager

from tools.A00090_ConnectionBuilder.app.core import RuleLoader
from tools.A00090_ConnectionBuilder.app.core import ConnectionManager
from tools.A00090_ConnectionBuilder.app.core import AttributeManager
from tools.A00090_ConnectionBuilder.app.core import BlendShapeManager
from tools.A00090_ConnectionBuilder.app.core import IntermediateManager


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_width      =  700
        self.win_height     =  500
        self.win_title     =  f"MetaHuman Connection Builder v{VERSION}"
        self.btn_get_label = "Get"
        self.btn_width_01 = 70
        
        self.connection_manager = ConnectionManager()

        APP_DIR = os.path.join(os.path.dirname(__file__),"." )
        self.pm = PathManager(  APP_DIR, 
                                read_dir  = "rules_v01")

        self.rules_file_name =  self.get_rules_file_name()

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
        # mesh to create blend shape
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("Mesh for blendShape"))

        self.le_mesh = QLineEdit()

        row.addWidget(self.le_mesh)

        self.btn_mesh = QPushButton(self.btn_get_label)
        self.btn_create_targets = QPushButton("Create targets")

        self.btn_mesh.setFixedWidth(self.btn_width_01)
        self.btn_create_targets.setFixedWidth(self.btn_width_01*2 + 10)

        row.addWidget(self.btn_mesh)
        row.addWidget(self.btn_create_targets)

        main_layout.addLayout(row)

        # -------------------------
        # Solver
        # -------------------------

        row = QHBoxLayout()

        self.cb_is_solver = QCheckBox('Is Solver')
        self.cb_is_solver.setChecked(True)

        row.addWidget(self.cb_is_solver)
        
        row.addWidget(QLabel("Base"))

        self.le_solver = QLineEdit()

        row.addWidget(self.le_solver)


        self.btn_solver = QPushButton(self.btn_get_label)
        self.btn_set_attr_solver = QPushButton("Set Attr")
        self.btn_del_attr_solver = QPushButton("Del Attr")

        self.btn_solver.setFixedWidth(self.btn_width_01)
        self.btn_set_attr_solver.setFixedWidth(self.btn_width_01)
        self.btn_del_attr_solver.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_solver)
        row.addWidget(self.btn_set_attr_solver)
        row.addWidget(self.btn_del_attr_solver)


        main_layout.addLayout(row)

        # -------------------------
        # Driver
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("Driver"))

        self.le_driver = QLineEdit()

        row.addWidget(self.le_driver)


        self.btn_driver = QPushButton(self.btn_get_label)
        self.btn_set_attr_driver = QPushButton("Set Attr")
        self.btn_del_attr_driver = QPushButton("Del Attr")

        self.btn_driver.setFixedWidth(self.btn_width_01)
        self.btn_set_attr_driver.setFixedWidth(self.btn_width_01)
        self.btn_del_attr_driver.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_driver)
        row.addWidget(self.btn_set_attr_driver)
        row.addWidget(self.btn_del_attr_driver)


        main_layout.addLayout(row)

        # -------------------------
        # BlendShape
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("BlendShape"))

        self.le_blendshape = QLineEdit()

        row.addWidget(self.le_blendshape)

        
        self.btn_blendShape = QPushButton(self.btn_get_label)
        self.btn_set_attr_blendShape = QPushButton("Set Attr")
        self.btn_del_attr_blendShape = QPushButton("Del Attr")

        self.btn_blendShape.setFixedWidth(self.btn_width_01)
        self.btn_set_attr_blendShape.setFixedWidth(self.btn_width_01)
        self.btn_del_attr_blendShape.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_blendShape)
        row.addWidget(self.btn_set_attr_blendShape)
        row.addWidget(self.btn_del_attr_blendShape)


        main_layout.addLayout(row)

        # -------------------------
        # Rule
        # -------------------------

        row = QHBoxLayout()

        row.addWidget(QLabel("Rule"))

        self.cb_rule = QComboBox()

        self.cb_rule.addItems(self.rules_file_name)

        row.addWidget(self.cb_rule)

        main_layout.addLayout(row)

        # -------------------------
        # Buttons
        # -------------------------

        row = QHBoxLayout()

        self.btn_connect_all = QPushButton("Connect All")
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_validate = QPushButton("Validate")

        row.addWidget(self.btn_connect_all)
        row.addWidget(self.btn_connect)
        row.addWidget(self.btn_disconnect)
        row.addWidget(self.btn_validate)


        main_layout.addLayout(row)

        # -------------------------
        # Intermediate (solver outputs -> WRK_intermediate null)
        # -------------------------

        row = QHBoxLayout()

        self.btn_connect_intermediate = QPushButton("Connect Intermediate")
        self.btn_connect_intermediate.setToolTip(
            "Connect every solver's outputs[i] to WRK_intermediate.<mapping[i]> "
            "for all rules in rules_v01 (creates the null node and its attrs if missing)."
        )

        row.addWidget(self.btn_connect_intermediate)

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

        self.btn_mesh.clicked.connect( lambda: self.set_selected_node(self.le_mesh ))
        self.btn_create_targets.clicked.connect(lambda: self.on_create_target(self.le_mesh))

        self.btn_solver.clicked.connect( lambda: self.set_selected_node(self.le_solver ))
        self.btn_set_attr_solver.clicked.connect(lambda: self.create_attributes(self.le_solver))
        self.btn_del_attr_solver.clicked.connect(lambda: self.create_attributes(self.le_solver))

        self.btn_driver.clicked.connect( lambda: self.set_selected_node(self.le_driver ))
        self.btn_set_attr_driver.clicked.connect( lambda:self.create_attributes(self.le_driver))
        self.btn_del_attr_driver.clicked.connect( lambda:self.delete_attributes(self.le_driver))

        self.btn_blendShape.clicked.connect( lambda: self.set_selected_node(self.le_blendshape ))
        self.btn_set_attr_blendShape.clicked.connect( lambda:self.create_attributes(self.le_blendshape))
        self.btn_del_attr_blendShape.clicked.connect( lambda:self.delete_attributes(self.le_blendshape))



        self.btn_connect_all.clicked.connect( self.on_connect_all)
        self.btn_connect.clicked.connect( self.on_connect)
        self.btn_disconnect.clicked.connect( self.on_disconnect)
        self.btn_validate.clicked.connect( self.on_validate)

        self.btn_connect_intermediate.clicked.connect( self.on_connect_intermediate)


    def log(self, text):

        self.te_log.append(text)
    
    # -------------------------------------------------

    def get_rules_file_name(self):
        # return [f.name for f in self.pm.path("read").iterdir() if f.is_file()]
        directory = self.pm.path("read")
        return [os.path.splitext(f)[0] for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    def get_rule(self, rule_name=None):

        if rule_name is None:
            rule_name = self.cb_rule.currentText()

        return RuleLoader.load(
            rule_name=rule_name,
            solver_node=self.le_solver.text(),
            driver_node=self.le_driver.text(),
            blendshape_node=self.le_blendshape.text()
        )
        
    def get_rule_all(self):
        json_all = RuleLoader.find_all_json()
        rules = []
        for json_current in json_all:
            rule = self.get_rule(json_current)
            rules.append(rule)
        return rules


    def on_connect_all(self):
        rules = self.get_rule_all()

        is_solver = self.cb_is_solver.isChecked()

        for rule in rules:
            self.connection_manager.connect(rule, is_solver)

        self.log("Connect All Finished")


    def on_connect(self):

        rule = self.get_rule()

        is_solver = self.cb_is_solver.isChecked()

        self.connection_manager.connect(rule, is_solver)

        self.log("Connect Finished")

    # -------------------------------------------------

    def on_connect_intermediate(self):
        """rules_v01 의 모든 solver outputs 를 WRK_intermediate null 노드로 연결.

        디렉토리를 동적 스캔하므로 json 이 늘어나면 자동으로 포함된다.
        """
        rule_names = RuleLoader.find_all_json()

        rules = [
            RuleLoader.load_solver_rule(name)
            for name in rule_names
        ]

        connected, skipped = IntermediateManager.connect(rules)

        self.log(
            f"Connect Intermediate Finished : "
            f"{connected} connection(s) from {len(rules)} solver(s) -> WRK_intermediate"
        )

        if skipped:
            self.log(f"  Skipped (solver not in scene) : {', '.join(skipped)}")

    # -------------------------------------------------

    def on_disconnect(self):

        rule = self.get_rule()

        self.connection_manager.disconnect(rule)

        self.log("Disconnect Finished")

    # -------------------------------------------------

    def on_validate(self):

        rule = self.get_rule()

        result = self.connection_manager.validate(rule)

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

    def create_attributes(self, le_target):

        rule = self.get_rule()

        target = le_target.text()

        AttributeManager.create(
            rule,
            target
        )
    def delete_attributes(self, le_target):

        rule = self.get_rule()

        target = le_target.text()

        AttributeManager.delete(
            rule,
            target
        )


    def on_create_target(self, le_mesh):
        mesh = self.le_mesh.text().strip()

        if not mesh:
            return

        rule = self.get_rule()

        BlendShapeManager.create_blendshape(
            rule,
            mesh
        )