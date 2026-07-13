# -*- coding: utf-8 -*-

# last Update date : 2026-06-24
# Python Script by Ji Hun Park

# KWI creator V03 - Maya in-DCC (PySide) version
# V02 와 기능 동일. 차이점: 타겟 본 목록을 파일이 아니라 UI 의 TSL(QListWidget)로 입력받는다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QRadioButton,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QLabel,
    QTextEdit,
    QListWidget,
    QAbstractItemView,
    QMessageBox,
    QMenuBar,
    QApplication,
    QTabWidget,
    QScrollArea,
    Qt,
)
from Framework.qt.maya_window import maya_main_window

from tools.A00080_KWI_creator_V03.app.config.version import VERSION
from tools.A00080_KWI_creator_V03.app.core.KWI_creator import KWI_creator
from tools.A00080_KWI_creator_V03.app.core.constraint_creator import ConstraintCreator


WINDOW_OBJECT_NAME = "JUN_KWI_creator_V03_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.win_title = f"Kawaii Creator v{VERSION}"
        self.win_width = 600
        self.win_hight = 600

        self.KWI_creator = KWI_creator()
        self.constraint_creator = ConstraintCreator()

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(self.win_title)
        self.resize(self.win_width, self.win_hight)

        self.build_ui()

    # ------------------------------------------------------------------
    # UI

    def build_ui(self):

        self.layout = QVBoxLayout(self)

        # --- Menu bar (Help) ------------------------------------------
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("How to use").triggered.connect(self.show_help)
        self.layout.setMenuBar(self.menu_bar)

        # --- Target bones (TSL) ---------------------------------------
        # 라벨 헤더에 현재 본 개수를 함께 표시한다 (예: "Target bones (Root bones) : 3").
        self._bones_label_base = "Target bones (Root bones)"
        self.label_bones = QLabel(self._bones_label_base)

        self.tsl_bones = QListWidget()
        self.tsl_bones.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # 리스트가 어떤 경로로 바뀌든(추가/삭제/클리어) 개수 표시가 항상 동기화되도록
        # 모델의 행 변경 시그널에 연결한다.
        self.tsl_bones.model().rowsInserted.connect(self.update_bones_count)
        self.tsl_bones.model().rowsRemoved.connect(self.update_bones_count)

        # bone 입력 줄 : 텍스트 입력 + Add
        self.ipf_bone_name = QLineEdit()
        self.ipf_bone_name.setPlaceholderText("Type a bone name and press Enter / Add")
        self.ipf_bone_name.returnPressed.connect(self.add_bone_from_field)

        self.btn_bone_add = QPushButton("Add")
        self.btn_bone_add.clicked.connect(self.add_bone_from_field)

        row_add = QHBoxLayout()
        row_add.addWidget(self.ipf_bone_name)
        row_add.addWidget(self.btn_bone_add)

        # bone 리스트 조작 버튼들
        self.btn_bone_add_selected = QPushButton("Add Selected")
        self.btn_bone_add_selected.clicked.connect(self.add_bones_from_selection)

        self.btn_bone_remove = QPushButton("Remove")
        self.btn_bone_remove.clicked.connect(self.remove_selected_bones)

        self.btn_bone_clear = QPushButton("Clear")
        self.btn_bone_clear.clicked.connect(self.clear_bones)

        self.btn_bone_load_default = QPushButton("Load Example")
        self.btn_bone_load_default.clicked.connect(self.load_default_bones)

        row_ops = QHBoxLayout()
        row_ops.addWidget(self.btn_bone_add_selected)
        row_ops.addWidget(self.btn_bone_remove)
        row_ops.addWidget(self.btn_bone_clear)
        row_ops.addWidget(self.btn_bone_load_default)

        # --- Create type (radio) --------------------------------------
        self.label_create_type = QLabel("Create type")

        self.radio_create_multiple_nodes = QRadioButton("Multiple Nodes")
        self.radio_create_single_node    = QRadioButton("Single Node")

        self.radio_create_multiple_nodes.toggled.connect(
            lambda checked: checked and self.KWI_creator.set_mode("multiple")
        )
        self.radio_create_single_node.toggled.connect(
            lambda checked: checked and self.KWI_creator.set_mode("single")
        )
        self.radio_create_multiple_nodes.setChecked(True)

        # --- Setting nodes number -------------------------------------
        self.label_setting_nodes_num = QLabel("Setting nodes Number")

        self.ipf_setting_nodes_interval = QLineEdit()
        self.ipf_setting_nodes_interval.setText("1")

        # --- Create buttons -------------------------------------------
        self.btn_create_base_nodes = QPushButton("Create base nodes")
        self.btn_create_base_nodes.clicked.connect(self.create_base_nodes_on_click)

        self.btn_create_setting_nodes = QPushButton("Create setting nodes")
        self.btn_create_setting_nodes.clicked.connect(self.create_setting_nodes_on_click)

        self.btn_create_LD_nodes = QPushButton("Create LD nodes")
        self.btn_create_LD_nodes.clicked.connect(self.create_LD_nodes_on_click)

        self.chk_write_individual = QCheckBox("Also write individual files")
        self.chk_write_individual.setChecked(True)

        self.btn_create_combined = QPushButton("Create combined file")
        self.btn_create_combined.clicked.connect(self.create_combined_on_click)

        # --- Output log -----------------------------------------------
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)

        # --- assemble : tabs + shared log -----------------------------
        self.tabs = QTabWidget()

        # Tab 1 : KWI Nodes (기존 UI 를 그대로 탭 안으로 이동)
        kwi_tab = QWidget()
        kwi_layout = QVBoxLayout(kwi_tab)
        kwi_layout.addWidget(self.label_bones)
        kwi_layout.addWidget(self.tsl_bones)
        kwi_layout.addLayout(row_add)
        kwi_layout.addLayout(row_ops)

        kwi_layout.addWidget(self.label_create_type)
        kwi_layout.addWidget(self.radio_create_multiple_nodes)
        kwi_layout.addWidget(self.radio_create_single_node)

        kwi_layout.addWidget(self.label_setting_nodes_num)
        kwi_layout.addWidget(self.ipf_setting_nodes_interval)

        kwi_layout.addWidget(self.btn_create_base_nodes)
        kwi_layout.addWidget(self.btn_create_setting_nodes)
        kwi_layout.addWidget(self.btn_create_LD_nodes)
        kwi_layout.addWidget(self.chk_write_individual)
        kwi_layout.addWidget(self.btn_create_combined)
        self.tabs.addTab(kwi_tab, "KWI Nodes")

        # Tab 2 : Constraints (신규)
        self.tabs.addTab(self._build_constraint_tab(), "Constraints")

        # 탭 아래에 로그를 공유로 둔다 (두 탭이 같은 로그를 쓴다)
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.log_widget)

        # 초기 개수 표시 (예: "Target bones (Root bones) : 0")
        self.update_bones_count()

    # ------------------------------------------------------------------
    # Constraints tab

    def _build_constraint_tab(self):
        # 언리얼 Kawaii Physics Bone Constraints Data Asset 내용 생성 탭.
        # (Chain A, Chain B) 브래킷 패턴 쌍을 여러 개 입력 -> 인덱스 1:1 zip -> 합본 텍스트.
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Enter bracket patterns, e.g.  dyn_asset_side_0[1-7]_0[1-5]\n"
            "Chain A and Chain B are paired index-by-index (1:1)."
        )
        layout.addWidget(info)

        # --- 동적 패턴 쌍 행들 (스크롤) -------------------------------
        self._pair_rows = []  # [(line_a, line_b, row_widget), ...]

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._rows_container)
        layout.addWidget(scroll)

        # 첫 행은 예시값으로 프리필
        self._add_pair_row(
            "dyn_asset_side_0[1-7]_0[1-5]",
            "dyn_asset_side_0[2-8]_0[1-5]",
        )

        btn_add_pair = QPushButton("+ Add pair")
        btn_add_pair.clicked.connect(lambda: self._add_pair_row())
        layout.addWidget(btn_add_pair)

        btn_generate = QPushButton("Generate & Copy")
        btn_generate.clicked.connect(self.generate_constraints_on_click)
        layout.addWidget(btn_generate)

        layout.addWidget(QLabel("Preview"))
        self.constraint_preview = QTextEdit()
        self.constraint_preview.setReadOnly(True)
        layout.addWidget(self.constraint_preview)

        return tab

    def _add_pair_row(self, chain_a="", chain_b=""):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)

        line_a = QLineEdit()
        line_a.setPlaceholderText("Chain A pattern")
        line_a.setText(chain_a)

        line_b = QLineEdit()
        line_b.setPlaceholderText("Chain B pattern")
        line_b.setText(chain_b)

        btn_remove = QPushButton("-")
        btn_remove.setFixedWidth(28)
        btn_remove.clicked.connect(lambda: self._remove_pair_row(row))

        row_layout.addWidget(line_a)
        row_layout.addWidget(line_b)
        row_layout.addWidget(btn_remove)

        self._rows_layout.addWidget(row)
        self._pair_rows.append((line_a, line_b, row))

    def _remove_pair_row(self, row):
        # 최소 한 행은 남긴다.
        if len(self._pair_rows) <= 1:
            self.log("At least one pair must remain.")
            return
        self._pair_rows = [r for r in self._pair_rows if r[2] is not row]
        self._rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()

    def _get_pattern_rows(self):
        # UI 의 모든 행을 (chain_a, chain_b) 튜플 리스트로 반환.
        return [(a.text(), b.text()) for a, b, _row in self._pair_rows]

    def generate_constraints_on_click(self):
        try:
            out_path, text = self.constraint_creator.create_file(
                self._get_pattern_rows()
            )
        except ValueError as e:
            self.log(f"Constraint error : {e}")
            return

        self.constraint_preview.setPlainText(text)
        QApplication.clipboard().setText(text)

        self.log(f"Constraint data written : {out_path}")
        self.log("Copied constraint data to clipboard. Paste into the Unreal Data Asset.")

    # ------------------------------------------------------------------
    # TSL (target bones) helpers

    def update_bones_count(self, *args):
        # 라벨 헤더에 현재 TSL 의 본 개수를 갱신한다. (*args : 모델 시그널 인자 흡수)
        self.label_bones.setText(
            f"{self._bones_label_base} : {self.tsl_bones.count()}"
        )

    def get_bones(self):
        return [
            self.tsl_bones.item(i).text()
            for i in range(self.tsl_bones.count())
        ]

    def add_bone(self, name):
        name = (name or "").strip()
        if not name:
            return
        # 중복 방지
        if name in self.get_bones():
            return
        self.tsl_bones.addItem(name)

    def add_bone_from_field(self):
        self.add_bone(self.ipf_bone_name.text())
        self.ipf_bone_name.clear()

    def add_bones_from_selection(self):
        # 마야에서 선택된 노드(조인트 등)를 TSL 에 추가한다.
        try:
            import maya.cmds as cmds
        except ImportError:
            self.log("maya.cmds not available (run inside Maya)")
            return

        sel = cmds.ls(selection=True, long=False) or []
        if not sel:
            self.log("Nothing selected")
            return

        added = 0
        for node in sel:
            before = self.tsl_bones.count()
            self.add_bone(node)
            if self.tsl_bones.count() > before:
                added += 1

        self.log(f"Added {added} bone(s) from selection")

    def remove_selected_bones(self):
        for item in self.tsl_bones.selectedItems():
            self.tsl_bones.takeItem(self.tsl_bones.row(item))

    def clear_bones(self):
        self.tsl_bones.clear()

    def load_default_bones(self):
        self.tsl_bones.clear()
        for bone in self.KWI_creator.get_default_tgt_bones():
            self.add_bone(bone)
        self.log(f"Loaded {self.tsl_bones.count()} example bone(s)")

    def _apply_bones_to_creator(self):
        # 생성 직전에 TSL 의 현재 본 목록을 코어에 주입. 비어 있으면 False.
        bones = self.get_bones()
        if not bones:
            self.log("Target bones list is empty. Add bones first.")
            return False
        self.KWI_creator.set_tgt_bones(bones)
        return True

    def _read_interval(self):
        # setting nodes interval 정수 파싱. 실패 시 None.
        try:
            return int(self.ipf_setting_nodes_interval.text())
        except ValueError:
            self.log("Setting nodes Number must be integer")
            return None

    # ------------------------------------------------------------------
    # create handlers

    def is_create_multiple_nodes(self):
        return self.radio_create_multiple_nodes.isChecked()

    def create_base_nodes_on_click(self):
        if not self._apply_bones_to_creator():
            return
        self.KWI_creator.create_base_nodes()
        self.log("Current mode  :  " + str(self.KWI_creator.create_mode))

    def create_setting_nodes_on_click(self):
        if not self._apply_bones_to_creator():
            return
        interval = self._read_interval()
        if interval is None:
            return
        self.KWI_creator.interval_setting_node = interval
        self.KWI_creator.create_setting_nodes()
        self.log("Setting nodes created")

    def create_LD_nodes_on_click(self):
        if not self._apply_bones_to_creator():
            return
        self.KWI_creator.create_LD_nodes()
        self.log("LD nodes created")

    def create_combined_on_click(self):
        if not self._apply_bones_to_creator():
            return
        interval = self._read_interval()
        if interval is None:
            return
        self.KWI_creator.interval_setting_node = interval

        write_individual = self.chk_write_individual.isChecked()
        out_path, combined = self.KWI_creator.create_combined_file(write_individual)

        # 합본 텍스트만 클립보드로 복사 -> UE AnimGraph 에 바로 붙여넣기 (Ctrl+V)
        QApplication.clipboard().setText(combined)

        self.log(f"Combined file created : {out_path}")
        if write_individual:
            self.log("Individual files also written")
        self.log("Copied combined code to clipboard. Paste into Unreal AnimGraph (Ctrl+V).")

    # ------------------------------------------------------------------
    # help

    def show_help(self):
        text = (
            "<h3>Kawaii Creator v{ver}</h3>"
            "<p>Generates Unreal <b>KawaiiPhysics</b> AnimGraph node text "
            "(clipboard-paste format) from a list of target root bones.</p>"
            "<b>How to use</b>"
            "<ol>"
            "<li>Build the <b>Target bones</b> list (TSL):"
            "<ul>"
            "<li><b>Type</b> a bone name and press Enter / <b>Add</b>.</li>"
            "<li><b>Add Selected</b> : add nodes selected in the Maya scene.</li>"
            "<li><b>Remove</b> / <b>Clear</b> : edit the list.</li>"
            "<li><b>Load Example</b> : load the bundled example bone list.</li>"
            "</ul></li>"
            "<li>Pick a <b>Create type</b>:"
            "<ul>"
            "<li><b>Multiple Nodes</b> : one KawaiiPhysics node per bone, chained.</li>"
            "<li><b>Single Node</b> : one node, extra bones become Additional Root Bones.</li>"
            "</ul></li>"
            "<li>Set <b>Setting nodes Number</b> (interval for setting / LD links).</li>"
            "<li>Create the output:"
            "<ul>"
            "<li><b>Create base / setting / LD nodes</b> : write each part separately.</li>"
            "<li><b>Create combined file</b> : write base + setting + LD into one file "
            "(tick <b>Also write individual files</b> to also keep separate files).</li>"
            "</ul></li>"
            "</ol>"
            "<p>Results are written under the tool's <code>0020_out/</code> folder. "
            "Open the generated file and copy its content into the Unreal AnimGraph.</p>"
            "<hr>"
            "<h3>Constraints tab</h3>"
            "<p>Generates the <b>Bone Constraints</b> content for a KawaiiPhysics "
            "<b>Data Asset</b> from bracket patterns, paired index-by-index (1:1).</p>"
            "<ol>"
            "<li>Type two bracket patterns per row, e.g. "
            "<code>dyn_asset_side_0[1-7]_0[1-5]</code> (Chain A) and "
            "<code>dyn_asset_side_0[2-8]_0[1-5]</code> (Chain B).</li>"
            "<li><b>[a-b]</b> expands to integers a..b (left bracket is the outer loop). "
            "If either bound is written with a leading zero, the values are "
            "<b>zero-padded</b> to that width (<code>[01-10]</code> &rarr; "
            "<code>01,02,&hellip;,10</code>); otherwise no padding "
            "(<code>[1-10]</code> &rarr; <code>1,2,&hellip;,10</code>).</li>"
            "<li>Chain A and Chain B must expand to the <b>same count</b> (1:1 pairing).</li>"
            "<li><b>+ Add pair</b> adds more rows; all rows are merged into one output.</li>"
            "<li><b>Generate &amp; Copy</b> builds the text, shows a preview and copies it to "
            "the clipboard. Paste it into the Unreal Data Asset.</li>"
            "</ol>"
        ).format(ver=VERSION)

        box = QMessageBox(self)
        box.setWindowTitle("Help - Kawaii Creator")
        box.setTextFormat(Qt.RichText)
        box.setText(text)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()

    def log(self, message):
        self.log_widget.append(str(message))
