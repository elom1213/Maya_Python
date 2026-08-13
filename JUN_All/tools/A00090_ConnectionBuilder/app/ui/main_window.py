# from Framework.qt.qt import QApplication
from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01

print("QT version  :  " + str(QT_VERSION))

import sys, os
import maya.cmds as cmds
from tools.A00090_ConnectionBuilder.app.config.version import VERSION

from Framework.core.maya_undo import undo_chunk

from tools.A00090_ConnectionBuilder.app.core import RuleLoader
from tools.A00090_ConnectionBuilder.app.core import ConnectionManager
from tools.A00090_ConnectionBuilder.app.core import AttributeManager
from tools.A00090_ConnectionBuilder.app.core import TargetBuilder
from tools.A00090_ConnectionBuilder.app.core import IntermediateManager


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName (창 누적 방지).
WINDOW_OBJECT_NAME = "JUN_A00090_ConnectionBuilder_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width      =  700
        self.win_height     =  500
        self.win_title     =  f"MetaHuman Connection Builder v{VERSION}"
        self.btn_get_label = "Get"
        self.btn_width_01 = 70

        self.connection_manager = ConnectionManager()

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

        row.addWidget(QLabel("Mesh / Node"))

        self.le_mesh = QLineEdit()
        self.le_mesh.setToolTip(
            "mesh -> creates blendShape targets named by the Rule mapping.\n"
            "other node (joint/transform/control) -> creates attributes "
            "named by the Rule mapping."
        )

        row.addWidget(self.le_mesh)

        self.btn_mesh = QPushButton(self.btn_get_label)
        # Create = 선택된 Rule 만, Create All = 모든 Rule.
        self.btn_create = QPushButton("Create")
        self.btn_create_all = QPushButton("Create All")

        self.btn_mesh.setFixedWidth(self.btn_width_01)
        self.btn_create.setFixedWidth(self.btn_width_01)
        self.btn_create_all.setFixedWidth(self.btn_width_01 + 10)

        row.addWidget(self.btn_mesh)
        row.addWidget(self.btn_create)
        row.addWidget(self.btn_create_all)

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
        # 기본 꺼짐 - Source 를 `Source.<attr>` 로 본다. 켜면 `Source.outputs[i]`.
        self.cb_is_solver.setChecked(False)
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

        row.addWidget(QLabel("Version"))

        self.cb_version = QComboBox()
        self.cb_version.setToolTip(
            "Rule set version folder (app/rules/<version>).\n"
            "Add a new folder (v002, v003 ...) with edited json files and pick it here."
        )
        self.cb_version.setFixedWidth(90)

        row.addWidget(self.cb_version)

        row.addWidget(QLabel("Rule"))

        self.cb_rule = QComboBox()

        row.addWidget(self.cb_rule)

        self.btn_refresh_rules = QPushButton("Refresh")
        self.btn_refresh_rules.setToolTip(
            "Rescan app/rules for version folders and json files."
        )
        self.btn_refresh_rules.setFixedWidth(self.btn_width_01)

        row.addWidget(self.btn_refresh_rules)

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
            "for all rules of the selected version "
            "(creates the null node and its attrs if missing)."
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
        self.btn_create.clicked.connect( self.on_create)
        self.btn_create_all.clicked.connect( self.on_create_all)

        self.btn_connect_all.clicked.connect( self.on_connect_all)
        self.btn_connect.clicked.connect( self.on_connect)
        self.btn_disconnect.clicked.connect( self.on_disconnect)
        self.btn_validate.clicked.connect( self.on_validate)

        self.btn_connect_intermediate.clicked.connect( self.on_connect_intermediate)

        self.btn_refresh_rules.clicked.connect( self.on_refresh_rules)
        self.cb_version.currentTextChanged.connect( self.on_version_changed)

        # -------------------------
        # 모든 버튼을 조금 작게 (tsl 위젯 내부 버튼 포함).
        # -------------------------
        for btn in self.findChildren(QPushButton):
            btn.setMaximumHeight(40)

        # 로그 위젯이 준비된 뒤에 버전/룰 콤보를 채운다.
        self.reload_versions()


    def log(self, text):

        self.te_log.append(text)

    # -------------------------------------------------

    # -------------------------------------------------
    # Rule version
    # -------------------------------------------------

    def current_version(self):
        """콤보에서 선택된 rule 버전 폴더 이름."""
        return self.cb_version.currentText() or RuleLoader.get_version()

    def reload_versions(self):
        """app/rules 를 다시 스캔해 Version 콤보를 채운다(선택은 최대한 유지)."""

        keep = self.cb_version.currentText()

        versions = RuleLoader.find_versions()

        self.cb_version.blockSignals(True)
        self.cb_version.clear()
        self.cb_version.addItems(versions)

        if keep in versions:
            self.cb_version.setCurrentText(keep)
        elif versions:
            self.cb_version.setCurrentText(RuleLoader.get_version())

        self.cb_version.blockSignals(False)

        if not versions:
            self.cb_rule.clear()
            self.log(
                f"[ERROR] No rule version folder in : {RuleLoader.RULES_ROOT}"
            )
            return

        RuleLoader.set_version(self.cb_version.currentText())

        self.reload_rules()

    def reload_rules(self):
        """현재 버전의 json 목록으로 Rule 콤보를 채운다(선택은 최대한 유지)."""

        keep = self.cb_rule.currentText()

        version = self.current_version()
        rule_names = RuleLoader.find_all_json(version)

        self.cb_rule.blockSignals(True)
        self.cb_rule.clear()
        self.cb_rule.addItems(rule_names)

        if keep in rule_names:
            self.cb_rule.setCurrentText(keep)

        self.cb_rule.blockSignals(False)

        self.log(
            f"[Rule] {version} : {len(rule_names)} rule(s)"
        )

        if not rule_names:
            self.log(
                f"[Warn] No json in : {RuleLoader.rule_dir(version)}"
            )

    def on_version_changed(self, version):

        if not version:
            return

        try:
            RuleLoader.set_version(version)
        except ValueError as e:
            self.log(f"[ERROR] {e}")
            return

        self.reload_rules()

    def on_refresh_rules(self):
        self.reload_versions()

    # -------------------------------------------------

    def get_rule(self, rule_name=None, solver_node="", driver_node=""):

        if rule_name is None:
            rule_name = self.cb_rule.currentText()

        return RuleLoader.load(
            rule_name=rule_name,
            solver_node=solver_node,
            driver_node=driver_node,
            blendshape_node="",
            version=self.current_version()
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

        version = self.current_version()

        for rule_name in RuleLoader.find_all_json(version):
            for src, tgt in pairs:
                rule = self.get_rule(rule_name, solver_node=src, driver_node=tgt)
                self.connection_manager.connect(rule, is_solver)

        self.log(f"Connect All Finished ({version})")


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
        """선택된 버전의 모든 solver outputs 를 WRK_intermediate null 노드로 연결.

        디렉토리를 동적 스캔하므로 json 이 늘어나면 자동으로 포함된다.
        """
        version = self.current_version()

        rule_names = RuleLoader.find_all_json(version)

        rules = [
            RuleLoader.load_solver_rule(name, version=version)
            for name in rule_names
        ]

        connected, skipped = IntermediateManager.connect(rules)

        self.log(
            f"Connect Intermediate Finished ({version}) : "
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


    def _nodes_from_field(self):
        """Mesh / Node 필드의 텍스트를 콤마로 나눠 노드 리스트로 반환."""
        text = self.le_mesh.text().strip()
        if not text:
            return []
        return [n.strip() for n in text.split(",") if n.strip()]

    def _build_for(self, rules, label):
        """nodes x rules 로 target/attribute 를 생성한다.

        노드가 mesh 면 blendShape target, 그 외면 attribute (TargetBuilder 가 판단).
        """
        nodes = self._nodes_from_field()
        if not nodes:
            self.log(f"[{label}] No node. Enter a mesh/object in the field.")
            return

        with undo_chunk():
            for node in nodes:
                for rule in rules:
                    try:
                        kind, result, report = TargetBuilder.build(rule, node)
                        self._log_build(label, node, kind, result, report,
                                        len(rule.mapping))
                    except Exception as e:
                        self.log(f"[{label}] {node} : {e}")

        self.log(f"{label} Finished")

    def _log_build(self, label, node, kind, result, report, expected):
        """무엇이 실제로 만들어졌는지 보고한다.

        예전에는 성공/실패만 알 수 있어서, 타겟이 일부만 붙어도 정상처럼 보였다.
        """
        if report is None:
            self.log(f"[{label}] {kind} : {node} ({expected} name(s))")
            return

        parts = []
        if report["created"]:
            parts.append(f"{report['created']} created")
        if report["reused"]:
            parts.append(f"{report['reused']} reused")
        if report["skipped"]:
            parts.append(f"{report['skipped']} already there")
        summary = ", ".join(parts) if parts else "nothing to do"

        self.log(f"[{label}] {node} -> {result} : {summary} "
                 f"(of {expected} name(s))")

        for alias, reason in report["failed"]:
            self.log(f"[{label}] {node} -> {alias} FAILED : {reason}")

    def on_create(self):
        """선택된 Rule 하나로만 생성."""
        self._build_for([self.get_rule()], "Create")

    def on_create_all(self):
        """선택된 버전의 모든 Rule 로 생성(메시는 target 누적, 노드는 attr 누적)."""
        version = self.current_version()
        rules = [self.get_rule(name) for name in RuleLoader.find_all_json(version)]
        self._build_for(rules, f"Create All ({version})")
