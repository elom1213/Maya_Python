# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00610_PmxImporter - Qt UI (in-Maya)
#
# File + Browse + Read(씬을 건드리지 않고 PMX 요약 · 텍스처 상태) -> 옵션 -> Import(진행 팝업) -> 로그.
# 모든 UI 문자열 / 로그는 영어. 옵션 · 최근 파일은 optionVar 로 기억한다.

import os

import maya.cmds as cmds

from Framework.qt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QCheckBox, QDoubleSpinBox, QComboBox, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QBrush, QColor, Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01
from Framework.qt.MOD_treeExpand_qt_v01 import JUN_mod_treeExpand_qt_v01
from Framework.qt.MOD_viewZoom_qt_v01 import JUN_mod_viewZoom_qt_v01
from Framework.qt.pin_style import apply_pin_style

from tools.A00610_PmxImporter.app.config.version import VERSION, LAST_UPDATE
from tools.A00610_PmxImporter.app.core import import_runner as runner
from tools.A00610_PmxImporter.app.core import pmx_reader as pr
from tools.A00610_PmxImporter.app.core import texture_resolver as tr

WINDOW_OBJECT_NAME = "JUN_A00610_PmxImporter_window"
OPT_PREFIX = "JUN_A00610_"

_OK = "#8fd18f"
_WARN = "#f0c060"
_BAD = "#ff8a80"

# (체크박스 속성, ImportOptions 키, 라벨, 기본값, 툴팁)
_CHECKS = [
    ("chk_mesh", "mesh", "Mesh", True, "Vertices, triangles, UVs, normals (one mesh, PMX vertex order)."),
    ("chk_materials", "materials", "Materials", True, "One lambert per PMX material + textures (alpha -> transparency)."),
    ("chk_skeleton", "skeleton", "Skeleton", True, "One joint per PMX bone (including IK bones), world aligned."),
    ("chk_skin", "skin", "Skin", True, "skinCluster with the PMX weights (BDEF1/2/4, SDEF/QDEF)."),
    ("chk_morphs", "morphs", "Morphs", True, "Vertex morphs -> blendShape targets (named after the PMX morphs)."),
    ("chk_normals", "import_normals", "Import normals", True, "Lock the PMX vertex normals on the mesh."),
    ("chk_hide_bones", "hide_invisible_bones", "Hide invisible bones", True,
     "Bones that are hidden in MMD get drawStyle None."),
    ("chk_dq", "dq_for_sdef", "SDEF/QDEF as dual quaternion", True,
     "SDEF/QDEF vertices use dual quaternion skinning (weight blended). Off = linear."),
    ("chk_copy_tex", "copy_unsafe_textures", "Copy unreadable textures", True,
     "Maya cannot read texture paths with characters outside the system code page.\n"
     "Copy those files to <PMX folder>/maya_textures/ with FBXASC names and use the copies."),
]


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("PMX Importer v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 720)
        self.model = None
        self.show_progress = True        # 시험에서 끌 수 있게
        self.build_ui()
        self.load_options()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)
        apply_pin_style(self.pin_button)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 6, 0)
        header.addWidget(self.menu_bar, stretch=1)
        header.addWidget(self.pin_button)
        main.addLayout(header)

        # -- 파일
        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("File"))
        self.le_file = QLineEdit()
        self.le_file.setPlaceholderText("PMX file (.pmx)")
        self.le_file.editingFinished.connect(self.on_read)
        file_row.addWidget(self.le_file, stretch=1)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.on_browse)
        file_row.addWidget(self.btn_browse)
        self.btn_read = QPushButton("Read")
        self.btn_read.setToolTip("Read the PMX and show what is inside (the scene is not changed).")
        self.btn_read.clicked.connect(self.on_read)
        file_row.addWidget(self.btn_read)
        main.addLayout(file_row)

        # -- 정보
        info_box = QGroupBox("Info")
        info = QVBoxLayout(info_box)
        self.lbl_info = QLabel("No file read.")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info.addWidget(self.lbl_info)
        self.tree_tex = QTreeWidget()
        self.tree_tex.setHeaderLabels(["Texture", "Status", "Used by"])
        self.tree_tex.setRootIsDecorated(False)
        self.tree_tex.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_tex.setMinimumHeight(110)
        JUN_mod_treeExpand_qt_v01(self.tree_tex)
        JUN_mod_viewZoom_qt_v01(self.tree_tex, key=OPT_PREFIX + "tex_zoom", default=1.0)
        info.addWidget(self.tree_tex, stretch=1)
        main.addWidget(info_box, stretch=1)

        # -- 옵션
        opt_box = QGroupBox("Import")
        grid = QGridLayout(opt_box)
        for n, (attr, _key, label, default, tip) in enumerate(_CHECKS):
            cb = QCheckBox(label)
            cb.setChecked(default)
            cb.setToolTip(tip)
            setattr(self, attr, cb)
            if n < 5:
                grid.addWidget(cb, 0, n)
            else:
                grid.addWidget(cb, 1 + (n - 5) // 2, (n - 5) % 2 * 2, 1, 2)
        row = 1 + (len(_CHECKS) - 5 + 1) // 2
        grid.addWidget(QLabel("Scale"), row, 0)
        self.sp_scale = QDoubleSpinBox()
        self.sp_scale.setDecimals(3)
        self.sp_scale.setRange(0.001, 1000.0)
        self.sp_scale.setValue(runner.cv.DEFAULT_SCALE)
        self.sp_scale.setToolTip("Maya centimeters per MMD unit (8 = same size as CATS 0.08 m).")
        grid.addWidget(self.sp_scale, row, 1)
        grid.addWidget(QLabel("UV set"), row, 2)
        self.cmb_uv = QComboBox()
        self.cmb_uv.addItems(["map1", "UVMap"])
        self.cmb_uv.setToolTip("Name of the main UV set. Additional UVs become UV1 ~ UV4.")
        grid.addWidget(self.cmb_uv, row, 3)
        grid.addWidget(QLabel("Namespace"), row + 1, 0)
        self.le_ns = QLineEdit()
        self.le_ns.setPlaceholderText("(none)")
        self.le_ns.setToolTip("Import into this namespace (empty = root).")
        grid.addWidget(self.le_ns, row + 1, 1, 1, 3)
        main.addWidget(opt_box)

        self.btn_import = QPushButton("Import")
        self.btn_import.setMinimumHeight(34)
        self.btn_import.setToolTip("Import the PMX into the open scene. One Ctrl+Z removes the whole import.")
        self.btn_import.clicked.connect(self.on_import)
        main.addWidget(self.btn_import)

        self.log_view = JUN_mod_log_qt_v01(window_title="PMX Importer - Log",
                                           object_name="JUN_A00610_PmxImporter_log_window")
        self.log_view.setMinimumHeight(150)
        main.addWidget(self.log_view, stretch=1)

    def log(self, msg):
        self.log_view.appendPlainText(msg)

    # ==================================================================
    # 옵션 기억
    # ==================================================================

    def options(self):
        kw = dict((key, getattr(self, attr).isChecked()) for attr, key, _l, _d, _t in _CHECKS)
        return runner.ImportOptions(scale=self.sp_scale.value(), uv_set_name=self.cmb_uv.currentText(),
                                    namespace=self.le_ns.text().strip(), **kw)

    def save_options(self):
        for attr, key, _l, _d, _t in _CHECKS:
            cmds.optionVar(intValue=(OPT_PREFIX + key, int(getattr(self, attr).isChecked())))
        cmds.optionVar(floatValue=(OPT_PREFIX + "scale", self.sp_scale.value()))
        cmds.optionVar(stringValue=(OPT_PREFIX + "uv_set", self.cmb_uv.currentText()))
        cmds.optionVar(stringValue=(OPT_PREFIX + "file", self.le_file.text().strip()))

    def load_options(self):
        for attr, key, _l, default, _t in _CHECKS:
            if cmds.optionVar(exists=OPT_PREFIX + key):
                getattr(self, attr).setChecked(bool(cmds.optionVar(q=OPT_PREFIX + key)))
        if cmds.optionVar(exists=OPT_PREFIX + "scale"):
            self.sp_scale.setValue(float(cmds.optionVar(q=OPT_PREFIX + "scale")))
        if cmds.optionVar(exists=OPT_PREFIX + "uv_set"):
            i = self.cmb_uv.findText(cmds.optionVar(q=OPT_PREFIX + "uv_set"))
            if i >= 0:
                self.cmb_uv.setCurrentIndex(i)
        if cmds.optionVar(exists=OPT_PREFIX + "file"):
            self.le_file.setText(cmds.optionVar(q=OPT_PREFIX + "file"))

    # ==================================================================
    # 읽기
    # ==================================================================

    def on_browse(self):
        start = os.path.dirname(self.le_file.text().strip()) or cmds.workspace(q=True, rootDirectory=True)
        path, _f = QFileDialog.getOpenFileName(self, "Open PMX", start, "PMX model (*.pmx);;All files (*.*)")
        if path:
            self.le_file.setText(path)
            self.on_read()

    def on_read(self):
        path = self.le_file.text().strip().strip('"')
        self.model = None
        self.tree_tex.clear()
        if not path:
            self.lbl_info.setText("No file read.")
            return None
        if not os.path.isfile(path):
            self.lbl_info.setText("File not found.")
            self.log("[ERROR] File not found: {0}".format(path))
            return None
        try:
            m = pr.read_pmx(path)
        except (pr.PmxError, OSError) as e:
            self.lbl_info.setText("Cannot read this file.")
            self.log("[ERROR] Cannot read PMX: {0}".format(e))
            return None
        self.model = m
        self.lbl_info.setText(summary_text(m))
        self.fill_textures(m, os.path.dirname(os.path.abspath(path)))
        self.save_options()
        return m

    def fill_textures(self, m, pmx_dir):
        codepage = runner.maya_codepage()
        users = {}
        for mat in m.materials:
            for kind, idx in (("color", mat.texture), ("sphere", mat.sphere),
                              ("toon", -1 if mat.shared_toon else mat.toon)):
                if 0 <= idx < len(m.textures):
                    users.setdefault(idx, []).append("{0} ({1})".format(mat.name, kind))
        for i, rel in enumerate(m.textures):
            path, status = tr.resolve(pmx_dir, rel)
            text, color = "Found", _OK
            if status == "missing":
                text, color = "Missing", _BAD
            elif status == "search":
                text, color = "Found elsewhere: " + os.path.relpath(path, pmx_dir).replace("\\", "/"), _WARN
            elif not tr.codepage_safe(path, codepage):
                text, color = "Copy needed ({0})".format(codepage), _WARN
            item = QTreeWidgetItem([tr.normalize_rel(rel), text, ", ".join(users.get(i, [])) or "-"])
            item.setForeground(1, QBrush(QColor(color)))
            item.setToolTip(0, path)
            self.tree_tex.addTopLevelItem(item)
        self.tree_tex.resizeColumnToContents(1)

    # ==================================================================
    # 임포트
    # ==================================================================

    def on_import(self):
        if self.on_read() is None:
            self.log("[WARN] Choose a PMX file first.")
            return None
        path = self.le_file.text().strip().strip('"')
        opts = self.options()
        self.save_options()
        self.log("--- Import {0} ---".format(os.path.basename(path)))
        dlg = None
        if self.show_progress:
            dlg = JUN_mod_progress_qt_v01(self, title="PMX Importer - Import", phases=runner.PHASES)
            dlg.start()
        try:
            result = runner.run_import(
                path, opts, log=self.log,
                progress=dlg.callback() if dlg else None,
                begin=(lambda label: dlg.begin_phase(label)) if dlg else None)
        except Exception as e:      # 사용자에게 보이게 - 예외는 로그로
            self.log("[ERROR] Import failed: {0}".format(e))
            raise
        finally:
            if dlg:
                dlg.finish()
        return result

    # ==================================================================
    # 창
    # ==================================================================

    def toggle_always_on_top(self, checked):
        self.pin_button.setText("Pinned" if checked else "Pin")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "PMX Importer v{0}\nLast update : {1}\n\n"
            "Import an MMD model (PMX 2.0 / 2.1) into Maya: one skinned mesh, joints,\n"
            "blendShape morphs, lambert materials and textures.\n\n"
            "Names are the PMX names. Characters Maya cannot use become FBXASC### (like FBX).\n"
            "Size: x8 (1 MMD unit = 8 cm). Rigid bodies, physics joints, IK and append bones\n"
            "are kept as data (attributes) only.".format(VERSION, LAST_UPDATE))


def summary_text(m):
    wt = m.weight_type_counts()
    mt = m.morph_type_counts()
    lines = [
        "Model: {0}  ({1})   PMX {2}  {3}".format(m.name, m.name_e or "-", m.header.version,
                                               "UTF-16" if m.header.encoding == 0 else "UTF-8"),
        "Vertices {0:,}   Triangles {1:,}   Additional UVs {2}   Materials {3}   Textures {4}".format(
            len(m.vertices), len(m.faces), m.header.additional_uvs, len(m.materials), len(m.textures)),
        "Weights: " + "  ".join("{0} {1:,}".format(k, v) for k, v in wt.items() if v),
        "Bones {0}  (IK {1}, append {2})   Morphs {3}  ({4})".format(
            len(m.bones), sum(1 for b in m.bones if b.ik), sum(1 for b in m.bones if b.append_parent >= 0),
            len(m.morphs), ", ".join("{0} {1}".format(k, v) for k, v in sorted(mt.items())) or "-"),
        "Display frames {0}   Rigid bodies {1}   Joints {2}{3}   (physics is kept as data only)".format(
            len(m.display_frames), len(m.rigids), len(m.joints),
            "   Soft bodies {0}".format(m.soft_body_count) if m.soft_body_count else ""),
    ]
    return "\n".join(lines)
