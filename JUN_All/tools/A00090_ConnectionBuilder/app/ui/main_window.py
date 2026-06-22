# from Framework.qt.qt import QApplication
from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01

print("QT version  :  " + str(QT_VERSION))

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

        super().__init__(maya_main_window())

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

        self.setWindowFlags(Qt.Window)

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
        # Source(좌) / Target(우) 를 좌우로 배치.
        # Source 컬럼 상단에 Is Solver 체크박스.
        # -------------------------

        src_target_row = QHBoxLayout()

        # --- Source 컬럼 (구 Base / solver) ---
        src_col = QVBoxLayout()

        is_solver_row = QHBoxLayout()
        self.cb_is_solver = QCheckBox('Is Solver')
        self.cb_is_solver.setChecked(True)
        is_solver_row.addWidget(self.cb_is_solver)
        is_solver_row.addStretch(1)
        src_col.addLayout(is_solver_row)

        self.tsl_source = JUN_mod_tsl_qt_v01(title="Source", log_callback=self.log)
        self.tsl_source.add_button(
            "Set Attr", lambda: self.create_attributes_for(self.tsl_source))
        self.tsl_source.add_button(
            "Del Attr", lambda: self.delete_attributes_for(self.tsl_source))
        src_col.addWidget(self.tsl_source)

        src_target_row.addLayout(src_col)

        # --- Target 컬럼 (구 Driver) ---
        tgt_col = QVBoxLayout()

        # Source 의 Is Solver 행과 높이를 맞추기 위한 빈 행.
        tgt_col.addWidget(QLabel(""))

        self.tsl_target = JUN_mod_tsl_qt_v01(title="Target", log_callback=self.log)
        self.tsl_target.add_button(
            "Set Attr", lambda: self.create_attributes_for(self.tsl_target))
        self.tsl_target.add_button(
            "Del Attr", lambda: self.delete_attributes_for(self.tsl_target))
        tgt_col.addWidget(self.tsl_target)

        src_target_row.addLayout(tgt_col)

        main_layout.addLayout(src_target_row)

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

        # 체크 해제 = 1->n (broadcast), 체크 = n->n (index pair)
        self.cb_pair_mode = QCheckBox("n->n (index pair)")
        self.cb_pair_mode.setToolTip(
            "Unchecked = 1->n broadcast (first Source to every Target).\n"
            "Checked = n->n index pair (Source[i] -> Target[i], equal count required)."
        )

        self.btn_connect_all = QPushButton("Connect All")
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_validate = QPushButton("Validate")

        row.addWidget(self.cb_pair_mode)
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

        self.btn_connect_all.clicked.connect( self.on_connect_all)
        self.btn_connect.clicked.connect( self.on_connect)
        self.btn_disconnect.clicked.connect( self.on_disconnect)
        self.btn_validate.clicked.connect( self.on_validate)

        self.btn_connect_intermediate.clicked.connect( self.on_connect_intermediate)

        # -------------------------
        # 모든 버튼을 조금 작게 (tsl 위젯 내부 버튼 포함).
        # -------------------------
        for btn in self.findChildren(QPushButton):
            btn.setMaximumHeight(40)


    def log(self, text):

        self.te_log.append(text)

    # -------------------------------------------------

    def get_rules_file_name(self):
        # return [f.name for f in self.pm.path("read").iterdir() if f.is_file()]
        directory = self.pm.path("read")
        return [os.path.splitext(f)[0] for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    def get_rule(self, rule_name=None, solver_node="", driver_node=""):

        if rule_name is None:
            rule_name = self.cb_rule.currentText()

        return RuleLoader.load(
            rule_name=rule_name,
            solver_node=solver_node,
            driver_node=driver_node,
            blendshape_node=""
        )

    # -------------------------------------------------
    # Source / Target pairing
    # -------------------------------------------------

    def _build_pairs(self, sources, targets):
        """모드에 따라 (source, target) 쌍 리스트 생성. 오류 시 [] 반환하고 로그."""
        if self.cb_pair_mode.isChecked():          # n->n index pair
            if len(sources) != len(targets):
                self.log(
                    "[ERROR] n->n requires equal Source/Target count "
                    f"(Source {len(sources)}, Target {len(targets)})"
                )
                return []
            return list(zip(sources, targets))

        # 1->n broadcast : 첫 Source 를 모든 Target 으로
        if not sources:
            return []
        if len(sources) > 1:
            self.log(f"[Warn] 1->n uses first Source only : {sources[0]}")
        return [(sources[0], t) for t in targets]

    # -------------------------------------------------

    def on_connect_all(self):

        pairs = self._build_pairs(
            self.tsl_source.get_all_items(),
            self.tsl_target.get_all_items()
        )

        if not pairs:
            return

        is_solver = self.cb_is_solver.isChecked()

        for rule_name in RuleLoader.find_all_json():
            for src, tgt in pairs:
                rule = self.get_rule(rule_name, solver_node=src, driver_node=tgt)
                self.connection_manager.connect(rule, is_solver)

        self.log("Connect All Finished")


    def on_connect(self):

        pairs = self._build_pairs(
            self.tsl_source.get_all_items(),
            self.tsl_target.get_all_items()
        )

        if not pairs:
            return

        is_solver = self.cb_is_solver.isChecked()

        for src, tgt in pairs:
            rule = self.get_rule(solver_node=src, driver_node=tgt)
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

        pairs = self._build_pairs(
            self.tsl_source.get_all_items(),
            self.tsl_target.get_all_items()
        )

        if not pairs:
            return

        for src, tgt in pairs:
            rule = self.get_rule(solver_node=src, driver_node=tgt)
            self.connection_manager.disconnect(rule)

        self.log("Disconnect Finished")

    # -------------------------------------------------

    def on_validate(self):

        pairs = self._build_pairs(
            self.tsl_source.get_all_items(),
            self.tsl_target.get_all_items()
        )

        if not pairs:
            return

        for src, tgt in pairs:
            rule = self.get_rule(solver_node=src, driver_node=tgt)
            result = self.connection_manager.validate(rule)
            self.log(
                f"Validate Result ({src} -> {tgt}) : {result}"
            )

    def set_selected_node(self, line_edit):

        selection = cmds.ls(sl=True)

        if not selection:
            return

        line_edit.setText(
            ", ".join(selection)
        )

    def create_attributes_for(self, tsl):
        """리스트 위젯의 모든 노드에 선택 rule mapping attr 생성."""
        rule = self.get_rule()

        for node in tsl.get_all_items():
            try:
                AttributeManager.create(rule, node)
            except Exception as e:
                self.log(f"[Set Attr] {node} : {e}")

    def delete_attributes_for(self, tsl):
        """리스트 위젯의 모든 노드에서 선택 rule mapping attr 삭제."""
        rule = self.get_rule()

        for node in tsl.get_all_items():
            try:
                AttributeManager.delete(rule, node)
            except Exception as e:
                self.log(f"[Del Attr] {node} : {e}")


    def on_create_target(self, le_mesh):
        mesh = self.le_mesh.text().strip()

        if not mesh:
            return

        rule = self.get_rule()

        BlendShapeManager.create_blendshape(
            rule,
            mesh
        )
