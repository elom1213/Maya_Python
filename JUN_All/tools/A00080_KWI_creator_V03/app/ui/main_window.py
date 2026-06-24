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
    Qt,
)
from Framework.qt.maya_window import maya_main_window

from tools.A00080_KWI_creator_V03.app.config.version import VERSION
from tools.A00080_KWI_creator_V03.app.core.KWI_creator import KWI_creator


WINDOW_OBJECT_NAME = "JUN_KWI_creator_V03_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.win_title = f"Kawaii Creator v{VERSION}"
        self.win_width = 600
        self.win_hight = 560

        self.KWI_creator = KWI_creator()

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

        # --- assemble -------------------------------------------------
        self.layout.addWidget(self.label_bones)
        self.layout.addWidget(self.tsl_bones)
        self.layout.addLayout(row_add)
        self.layout.addLayout(row_ops)

        self.layout.addWidget(self.label_create_type)
        self.layout.addWidget(self.radio_create_multiple_nodes)
        self.layout.addWidget(self.radio_create_single_node)

        self.layout.addWidget(self.label_setting_nodes_num)
        self.layout.addWidget(self.ipf_setting_nodes_interval)

        self.layout.addWidget(self.btn_create_base_nodes)
        self.layout.addWidget(self.btn_create_setting_nodes)
        self.layout.addWidget(self.btn_create_LD_nodes)
        self.layout.addWidget(self.chk_write_individual)
        self.layout.addWidget(self.btn_create_combined)
        self.layout.addWidget(self.log_widget)

        # 초기 개수 표시 (예: "Target bones (Root bones) : 0")
        self.update_bones_count()

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
        ).format(ver=VERSION)

        box = QMessageBox(self)
        box.setWindowTitle("Help - Kawaii Creator")
        box.setTextFormat(Qt.RichText)
        box.setText(text)
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()

    def log(self, message):
        self.log_widget.append(str(message))
