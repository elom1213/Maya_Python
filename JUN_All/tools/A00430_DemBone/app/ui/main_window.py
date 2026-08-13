# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone - Qt UI
#
# EA Dem Bones(Smooth Skinning Decomposition with Rigid Bones)의 마야 이식.
# 애니메이션 메시 시퀀스(알렘빅 캐시 등)와 조인트를 비교해, 그 움직임을 가장 잘 재현하는
# **스킨 웨이트**(또는 **본 애니메이션**)를 풀어 준다.
#
# 화면 흐름: Input(캐시/rest/타깃 메시 + 조인트 + 프레임) -> 모드 탭 -> Run -> 로그/리포트.
# 입력은 세 모드가 **공유**한다(같은 데이터로 모드만 바꿔 돌리는 일이 잦아서).
#
# 모든 UI 문자열은 영어, 한국어는 주석/독스트링만.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_timeRange_qt

import maya.cmds as cmds

from tools.A00430_DemBone.app.config.version import VERSION, LAST_UPDATE

# core 는 numpy 를 쓴다(Maya 2022+ 내장). 없으면 창은 뜨되 기능을 막고 이유를 알린다.
try:
    from tools.A00430_DemBone.app.core import alembic_cache as abc_mod
    from tools.A00430_DemBone.app.core import dembone_manager as mgr
    from tools.A00430_DemBone.app.core import scene_sampler as sampler
    from tools.A00430_DemBone.app.core.solver_common import SolveCancelled
    CORE_ERROR = ""
except Exception as _e:                                   # pragma: no cover
    abc_mod = None
    mgr = None
    sampler = None
    SolveCancelled = Exception
    CORE_ERROR = str(_e)


WINDOW_OBJECT_NAME = "JUN_A00430_DemBone_window"

_WARN_COLOR = "#ffb454"
_OK_COLOR = "#8bd450"


def _spin(minimum, maximum, value, decimals=0, step=1.0, tip=""):
    """숫자 입력. 값을 되쓸 수 있으므로 keyboardTracking 은 끈다
    (켜두면 타이핑 중간값이 그대로 반영돼 `0.1` 이 `0.100` 으로 잘리는 일이 생긴다)."""
    box = QDoubleSpinBox() if decimals else QSpinBox()
    # setDecimals 를 먼저 해야 한다. 기본 자릿수는 2 라서, 뒤에 하면 setValue(1e-4) 가
    # 0.00 으로 반올림되어 **기본값이 조용히 사라진다**.
    if decimals:
        box.setDecimals(decimals)
        box.setSingleStep(step)
    box.setRange(minimum, maximum)
    box.setValue(value)
    box.setKeyboardTracking(False)
    if tip:
        box.setToolTip(tip)
    box.setMinimumWidth(80)
    return box


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "DemBone v{0}".format(VERSION)
        self.resize(520, 900)

        self._cancel = False
        self._running = False
        self._lock_vertices = None            # 소프트 락 대상 버텍스 인덱스

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        root.addWidget(self._build_input_box())
        root.addWidget(self._build_joint_box(), 1)
        root.addWidget(self._build_tabs())
        root.addLayout(self._build_run_row())

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(130)
        root.addWidget(self.te_log)

        if CORE_ERROR:
            self.btn_run.setEnabled(False)
            self.log("Core modules failed to load: {0}".format(CORE_ERROR), warn=True)
            self.log("This tool needs numpy (bundled with Maya 2022+).", warn=True)
        else:
            self.log("DemBone v{0} ({1}) ready.".format(VERSION, LAST_UPDATE))
            self.log("Load the animated cache mesh and the joints, set the frame "
                     "range, then Run.")

    # ---------------- input ----------------

    def _build_input_box(self):
        box = QGroupBox("Input")
        lay = QVBoxLayout(box)

        self.le_cache = QLineEdit()
        self.le_cache.setPlaceholderText("animated mesh (alembic cache)")
        lay.addLayout(self._mesh_row("Cache", self.le_cache, abc=True))

        self.le_rest = QLineEdit()
        self.le_rest.setPlaceholderText("rest pose mesh (empty = cache at rest frame)")
        lay.addLayout(self._mesh_row("Rest", self.le_rest))

        self.le_target = QLineEdit()
        self.le_target.setPlaceholderText("mesh to skin (empty = rest mesh)")
        lay.addLayout(self._mesh_row("Target", self.le_target))

        self.time_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=int(cmds.playbackOptions(q=True, min=True)),
            end_value=int(cmds.playbackOptions(q=True, max=True)),
            show_sel_range=False, log_callback=self.log)
        lay.addWidget(self.time_range)

        row = QHBoxLayout()
        row.addWidget(QLabel("Rest Frame"))
        self.sp_rest_frame = _spin(-100000, 100000, int(
            cmds.playbackOptions(q=True, min=True)),
            tip="Frame where the joints sit at their bind pose.\n"
                "The rest mesh is read at this frame too.")
        row.addWidget(self.sp_rest_frame)
        row.addWidget(QLabel("Stride"))
        self.sp_stride = _spin(1, 100, 1,
                               tip="Sample every Nth frame. Raise it to trade a bit of\n"
                                   "accuracy for speed on long caches.")
        row.addWidget(self.sp_stride)
        row.addStretch(1)
        lay.addLayout(row)

        return box

    def _mesh_row(self, label, line_edit, abc=False):
        row = QHBoxLayout()

        tag = QLabel(label)
        tag.setMinimumWidth(44)
        row.addWidget(tag)
        row.addWidget(line_edit, 1)

        btn = QPushButton("<<")
        btn.setFixedWidth(32)
        btn.setToolTip("Load the selected mesh.")
        btn.clicked.connect(lambda *_a, e=line_edit: self.on_load_mesh(e))
        row.addWidget(btn)

        sel = QPushButton("Sel")
        sel.setFixedWidth(36)
        sel.setToolTip("Select this mesh in the scene.")
        sel.clicked.connect(lambda *_a, e=line_edit: self.on_select_field(e))
        row.addWidget(sel)

        if abc:
            imp = QPushButton("Import .abc")
            imp.setToolTip("Import an alembic file and use its mesh as the cache.")
            imp.clicked.connect(lambda *_a: self.on_import_abc())
            row.addWidget(imp)

        return row

    def _build_joint_box(self):
        self.tsl_joints = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints", select_label="Select Joints",
            list_min_height=140, log_callback=self.log)
        self.tsl_joints.add_button("Hierarchy", self.on_add_hierarchy)
        return self.tsl_joints

    # ---------------- tabs ----------------

    def _build_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_weights(), "Solve Weights")
        self.tabs.setTabToolTip(0, "Cache + joint animation -> skinning weights")
        self.tabs.addTab(self._tab_transforms(), "Solve Transforms")
        self.tabs.setTabToolTip(1, "Cache + existing weights -> bone animation")
        self.tabs.addTab(self._tab_refine(), "Refine")
        self.tabs.setTabToolTip(2, "Optimize weights and bone animation together")
        self.tabs.addTab(self._tab_decompose(), "Decompose")
        self.tabs.setTabToolTip(3, "Cache only -> build the joints, weights and animation")
        self.tabs.addTab(self._tab_options(), "Options")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        return self.tabs

    def _tab_weights(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        info = QLabel("Solves the skinning weights that best reproduce the cache "
                      "when the joints play their animation.")
        info.setWordWrap(True)
        lay.addWidget(info)

        self.cb_use_existing = QCheckBox("Start from existing weights")
        self.cb_use_existing.setToolTip(
            "Use the target's current skinCluster weights as the starting point\n"
            "instead of a fresh rigid fit.")
        lay.addWidget(self.cb_use_existing)

        row = QHBoxLayout()
        row.addWidget(QLabel("Preserve"))
        self.sp_lock_amount = _spin(0.0, 1.0, 0.0, decimals=2, step=0.1,
                                    tip="How much of the existing weights to keep.\n"
                                        "0 = solve freely, 1 = do not change them.")
        row.addWidget(self.sp_lock_amount)
        self.btn_lock_verts = QPushButton("From Selected Verts")
        self.btn_lock_verts.setToolTip(
            "Limit the preserve amount to the selected vertices.\n"
            "With nothing captured it applies to the whole mesh.")
        self.btn_lock_verts.clicked.connect(self.on_capture_lock_verts)
        row.addWidget(self.btn_lock_verts)
        self.btn_lock_clear = QPushButton("Clear")
        self.btn_lock_clear.clicked.connect(self.on_clear_lock_verts)
        row.addWidget(self.btn_lock_clear)
        lay.addLayout(row)

        self.lbl_lock = QLabel("Preserve applies to: whole mesh")
        lay.addWidget(self.lbl_lock)

        lay.addStretch(1)
        return page

    def _tab_transforms(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        info = QLabel("Solves the bone animation that best reproduces the cache "
                      "with the target's current skinning weights, then bakes keys.")
        info.setWordWrap(True)
        lay.addWidget(info)

        row = QHBoxLayout()
        self.cb_bake_t = QCheckBox("Translate")
        self.cb_bake_t.setChecked(True)
        row.addWidget(self.cb_bake_t)
        self.cb_bake_r = QCheckBox("Rotate")
        self.cb_bake_r.setChecked(True)
        row.addWidget(self.cb_bake_r)
        self.cb_euler = QCheckBox("Euler Filter")
        self.cb_euler.setChecked(True)
        self.cb_euler.setToolTip("Run an euler filter on the baked rotation curves\n"
                                 "so they do not flip between frames.")
        row.addWidget(self.cb_euler)
        row.addStretch(1)
        lay.addLayout(row)

        lock_row = QHBoxLayout()
        self.btn_lock_joints = QPushButton("Lock Selected Joints")
        self.btn_lock_joints.setToolTip(
            "Locked joints keep their current animation and are not solved\n"
            "(the reference tool calls this demLock).")
        self.btn_lock_joints.clicked.connect(self.on_capture_lock_joints)
        lock_row.addWidget(self.btn_lock_joints)
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.on_clear_lock_joints)
        lock_row.addWidget(btn_clear)
        lay.addLayout(lock_row)

        self._lock_joints = []
        self.lbl_lock_joints = QLabel("Locked joints: none")
        lay.addWidget(self.lbl_lock_joints)

        lay.addStretch(1)
        return page

    def _tab_refine(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        info = QLabel("Alternates transform and weight updates until the error stops "
                      "improving. Needs a skinned target to start from.")
        info.setWordWrap(True)
        lay.addWidget(info)

        form = QFormLayout()
        self.sp_iters = _spin(1, 500, 10,
                              tip="Maximum number of global iterations.")
        form.addRow("Global Iterations", self.sp_iters)
        self.sp_tolerance = _spin(0.0, 1.0, 0.001, decimals=5, step=0.001,
                                  tip="Stop when the error improves by less than this\n"
                                      "fraction for [Patience] iterations in a row.")
        form.addRow("Tolerance", self.sp_tolerance)
        self.sp_patience = _spin(1, 50, 3)
        form.addRow("Patience", self.sp_patience)
        lay.addLayout(form)

        note = QLabel("Weight locks from the Solve Weights tab and joint locks from "
                      "the Solve Transforms tab are respected here.")
        note.setWordWrap(True)
        lay.addWidget(note)

        lay.addStretch(1)
        return page

    def _tab_decompose(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        info = QLabel("Builds a whole skeleton from the cache alone: clusters the mesh "
                      "into bones, creates the joints, binds and bakes. No joints are "
                      "needed as input - the Joints list is ignored here.")
        info.setWordWrap(True)
        lay.addWidget(info)

        form = QFormLayout()
        self.sp_target_bones = _spin(1, 512, 20,
                                     tip="How many bones to aim for. The result can differ\n"
                                         "slightly - splitting and pruning decide the final\n"
                                         "count (the reference behaves the same way).")
        form.addRow("Target Bones", self.sp_target_bones)
        self.sp_init_iters = _spin(1, 50, 5,
                                   tip="Clustering passes after each split. Higher is tidier\n"
                                       "and slower.")
        form.addRow("Init Iterations", self.sp_init_iters)
        self.sp_init_frames = _spin(2, 1000, 30,
                                    tip="Frames used for clustering, spread over the range.\n"
                                        "Clustering only needs pose variety, and this stage\n"
                                        "costs vertices x bones x frames - so it is capped\n"
                                        "here and the full range is used afterwards.")
        form.addRow("Init Frames", self.sp_init_frames)
        self.le_prefix = QLineEdit("demBone")
        self.le_prefix.setToolTip("Joint names become <prefix>_00, <prefix>_01, ...")
        form.addRow("Joint Prefix", self.le_prefix)
        lay.addLayout(form)

        self.cb_single_root = QCheckBox("Parent every joint under one root")
        self.cb_single_root.setToolTip(
            "Off: the joints are created as siblings.\n"
            "On: the bone that best explains the whole mesh on its own becomes the\n"
            "root and the rest are parented under it (the reference calls this\n"
            "bindUpdate=2).")
        lay.addWidget(self.cb_single_root)

        note = QLabel("Refine settings (Global Iterations / Tolerance / Patience) and the "
                      "Options tab apply here too. Set Global Iterations to 0 to skip "
                      "refinement.")
        note.setWordWrap(True)
        lay.addWidget(note)

        lay.addStretch(1)
        return page

    def _tab_options(self):
        page = QWidget()
        outer = QVBoxLayout(page)

        weights_box = QGroupBox("Weights")
        form = QFormLayout(weights_box)
        self.sp_nnz = _spin(1, 64, 8,
                            tip="Maximum number of joints influencing one vertex.")
        form.addRow("Max Influences", self.sp_nnz)
        self.sp_smooth = _spin(0.0, 10.0, 1e-4, decimals=6, step=0.0001,
                               tip="Smoothness regularizer. Raise it when the solved\n"
                                   "weights look noisy, lower it for a tighter fit.")
        form.addRow("Smoothness", self.sp_smooth)
        self.sp_smooth_step = _spin(0.0, 100.0, 1.0, decimals=2, step=0.5,
                                    tip="Strength of the laplacian smoothing step.")
        form.addRow("Smooth Step", self.sp_smooth_step)
        self.sp_smooth_iters = _spin(0, 200, 20,
                                     tip="Jacobi iterations used to apply the smoothing\n"
                                         "(the reference uses a direct sparse solve).")
        form.addRow("Smooth Iterations", self.sp_smooth_iters)
        self.sp_w_iters = _spin(0, 50, 3,
                                tip="Weight update iterations per pass.")
        form.addRow("Weight Iterations", self.sp_w_iters)
        self.sp_prune = _spin(0.0, 1.0, 0.0, decimals=5, step=0.001,
                              tip="Drop weights at or below this value before writing.")
        form.addRow("Prune Below", self.sp_prune)
        outer.addWidget(weights_box)

        trans_box = QGroupBox("Transformations")
        form2 = QFormLayout(trans_box)
        self.sp_t_iters = _spin(0, 50, 5,
                                tip="Bone update iterations per pass.")
        form2.addRow("Transform Iterations", self.sp_t_iters)
        self.sp_affine = _spin(0.0, 1000.0, 10.0, decimals=2, step=1.0,
                               tip="Translation affinity: lets the strongly weighted core\n"
                                   "of each bone dominate its solved transform.\n"
                                   "Keeps lightly weighted bones from flying off, at a\n"
                                   "small cost in accuracy. Set 0 for the tightest fit.")
        form2.addRow("Translation Affinity", self.sp_affine)
        self.sp_affine_norm = _spin(0.1, 32.0, 4.0, decimals=2, step=0.5,
                                    tip="p-norm used by the translation affinity.")
        form2.addRow("Affinity p-Norm", self.sp_affine_norm)
        outer.addWidget(trans_box)

        misc_box = QGroupBox("Misc")
        form3 = QFormLayout(misc_box)
        self.sp_chunk = _spin(100, 100000, 2000,
                              tip="Vertices processed per batch. Lower it if memory\n"
                                  "is tight on very heavy meshes.")
        form3.addRow("Vertex Chunk", self.sp_chunk)
        self.cb_apply = QCheckBox("Apply result to the scene")
        self.cb_apply.setChecked(True)
        self.cb_apply.setToolTip("Uncheck to only report the error without touching\n"
                                 "the scene (dry run).")
        form3.addRow("", self.cb_apply)
        outer.addWidget(misc_box)

        outer.addStretch(1)
        return page

    # ---------------- run row ----------------

    def _build_run_row(self):
        row = QVBoxLayout()

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        row.addWidget(self.progress)

        buttons = QHBoxLayout()
        self.btn_run = QPushButton("Solve Weights")
        self.btn_run.setMinimumHeight(38)
        self.btn_run.clicked.connect(lambda *_a: self.on_run())
        buttons.addWidget(self.btn_run, 1)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setMinimumHeight(38)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(lambda *_a: self.on_cancel())
        buttons.addWidget(self.btn_cancel)

        row.addLayout(buttons)
        return row

    # ==============================================================
    # helpers
    # ==============================================================

    def log(self, message, warn=False, ok=False):
        color = _WARN_COLOR if warn else (_OK_COLOR if ok else None)
        if color:
            self.te_log.append('<span style="color:{0};">{1}</span>'.format(
                color, message))
        else:
            self.te_log.append(message)
        self.te_log.moveCursor(QTextCursor.End)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "DemBone v{0} ({1})\n\n"
            "Skinning decomposition for Maya - solves skinning weights and/or bone\n"
            "animation from an animated mesh sequence.\n\n"
            "Port of Dem Bones (c) 2019 Electronic Arts, BSD 3-Clause.\n"
            "Le & Deng, Smooth Skinning Decomposition with Rigid Bones,\n"
            "ACM TOG 31(6), SIGGRAPH Asia 2012.".format(VERSION, LAST_UPDATE))

    def _on_tab_changed(self, index):
        labels = ["Solve Weights", "Solve Transforms", "Refine", "Decompose",
                  "Solve Weights"]
        self.btn_run.setText(labels[min(index, len(labels) - 1)])

    def on_load_mesh(self, line_edit, *_a):
        selected = cmds.ls(sl=True, l=True, type="transform") or []
        if not selected:
            shapes = cmds.ls(sl=True, l=True, type="mesh") or []
            selected = shapes[:1]
        if not selected:
            self.log("Select a mesh first.", warn=True)
            return
        line_edit.setText(selected[0])

    def on_select_field(self, line_edit, *_a):
        name = line_edit.text().strip()
        if name and cmds.objExists(name):
            cmds.select(name, replace=True)
        else:
            self.log("Nothing to select.", warn=True)

    def on_import_abc(self, *_a):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Alembic", "", "Alembic (*.abc)")
        if not path:
            return
        try:
            meshes = abc_mod.import_file(path)
        except Exception as exc:
            self.log("Import failed: {0}".format(exc), warn=True)
            return
        self.le_cache.setText(meshes[0])
        self.log("Imported {0} mesh(es); using '{1}'.".format(len(meshes), meshes[0]))

        found = abc_mod.frame_range()
        if found:
            self.time_range.set_range(found[0], found[1])
            self.sp_rest_frame.setValue(found[0])
            self.log("Frame range set to {0} - {1} from the alembic node.".format(*found))

    def on_add_hierarchy(self, *_a):
        """선택한 조인트의 하위 조인트까지 한 번에 담는다."""
        roots = cmds.ls(sl=True, l=True, type="joint") or []
        if not roots:
            self.log("Select at least one joint.", warn=True)
            return
        joints = []
        for root in roots:
            joints.append(root)
            joints.extend(cmds.listRelatives(root, ad=True, type="joint", f=True) or [])
        ordered = []
        for j in joints:
            if j not in ordered:
                ordered.append(j)
        self.tsl_joints.set_items(ordered)
        self.log("{0} joint(s) listed.".format(len(ordered)))

    def on_capture_lock_verts(self, *_a):
        verts = cmds.ls(sl=True, fl=True, type="float3") or []
        indices = []
        for name in verts:
            if ".vtx[" not in name:
                continue
            indices.append(int(name.split(".vtx[")[1].split("]")[0]))
        if not indices:
            self.log("Select vertices on the target mesh first.", warn=True)
            return
        self._lock_vertices = sorted(set(indices))
        self.lbl_lock.setText("Preserve applies to: {0} vertices".format(
            len(self._lock_vertices)))

    def on_clear_lock_verts(self, *_a):
        self._lock_vertices = None
        self.lbl_lock.setText("Preserve applies to: whole mesh")

    def on_capture_lock_joints(self, *_a):
        joints = cmds.ls(sl=True, l=True, type="joint") or []
        if not joints:
            self.log("Select the joints to lock.", warn=True)
            return
        self._lock_joints = joints
        self.lbl_lock_joints.setText("Locked joints: {0}".format(len(joints)))

    def on_clear_lock_joints(self, *_a):
        self._lock_joints = []
        self.lbl_lock_joints.setText("Locked joints: none")

    # ==============================================================
    # run
    # ==============================================================

    def _config(self):
        joints = self.tsl_joints.get_all_nodes()
        cfg = mgr.SolveConfig(
            cache_mesh=self.le_cache.text().strip(),
            rest_mesh=self.le_rest.text().strip(),
            target_mesh=self.le_target.text().strip(),
            joints=joints,
            start=self.time_range.start() or 0,
            end=self.time_range.end() or 0,
            stride=self.sp_stride.value(),
            rest_frame=self.sp_rest_frame.value(),
            nnz=self.sp_nnz.value(),
            weights_smooth=self.sp_smooth.value(),
            smooth_step=self.sp_smooth_step.value(),
            smooth_iters=self.sp_smooth_iters.value(),
            n_weights_iters=self.sp_w_iters.value(),
            prune=self.sp_prune.value(),
            use_existing_weights=self.cb_use_existing.isChecked(),
            lock_amount=self.sp_lock_amount.value(),
            lock_vertices=self._lock_vertices,
            n_trans_iters=self.sp_t_iters.value(),
            trans_affine=self.sp_affine.value(),
            trans_affine_norm=self.sp_affine_norm.value(),
            lock_joints=list(self._lock_joints),
            bake_translation=self.cb_bake_t.isChecked(),
            bake_rotation=self.cb_bake_r.isChecked(),
            euler_filter=self.cb_euler.isChecked(),
            target_bones=self.sp_target_bones.value(),
            init_iters=self.sp_init_iters.value(),
            init_max_frames=self.sp_init_frames.value(),
            single_root=self.cb_single_root.isChecked(),
            joint_prefix=self.le_prefix.text().strip() or "demBone",
            n_iters=self.sp_iters.value(),
            tolerance=self.sp_tolerance.value(),
            patience=self.sp_patience.value(),
            chunk=self.sp_chunk.value(),
            apply_result=self.cb_apply.isChecked(),
        )
        return cfg

    def _progress(self, fraction, message):
        """솔버가 부르는 진행률 콜백. False 를 돌려주면 솔버가 취소로 본다."""
        self.progress.setValue(int(round(100 * fraction)))
        if message:
            self.progress.setFormat("%p%  -  {0}".format(message))
        QApplication.processEvents()
        return not self._cancel

    def on_cancel(self):
        if self._running:
            self._cancel = True
            self.log("Cancelling...", warn=True)

    def on_run(self):
        if self._running or CORE_ERROR:
            return

        index = self.tabs.currentIndex()
        mode = {0: "weights", 1: "transforms", 2: "refine",
                3: "decompose"}.get(index, "weights")

        cfg = self._config()
        problems = mgr.validate(cfg, need_weights=(mode == "transforms"),
                                need_joints=(mode != "decompose"))
        if problems:
            for problem in problems:
                self.log(problem, warn=True)
            return

        self._cancel = False
        self._running = True
        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setValue(0)

        job = {"weights": mgr.solve_weights_job,
               "transforms": mgr.solve_transforms_job,
               "refine": mgr.refine_job,
               "decompose": mgr.decompose_job}[mode]

        try:
            report = job(cfg, progress=self._progress, log=self.log)
            self._log_report(mode, report)
        except SolveCancelled:
            self.log("Cancelled - the scene was not changed.", warn=True)
        except Exception as exc:
            self.log("Failed: {0}".format(exc), warn=True)
            import traceback
            print(traceback.format_exc())
        finally:
            self._running = False
            self.btn_run.setEnabled(True)
            self.btn_cancel.setEnabled(False)
            self.progress.setFormat("%p%")

    def _log_report(self, mode, report):
        self.log("-" * 52)
        self.log("{0} verts | {1} joints | {2} frames".format(
            report["vertices"], report["bones"], report["frames"]))
        if report.get("start_rmse") is not None:
            self.log("RMSE {0:.6f} -> {1:.6f}".format(
                report["start_rmse"], report["rmse"]))
        self.log("RMSE {0:.6f}  ({1:.4f}% of model size)".format(
            report["rmse"], report["rmse_pct"]), ok=True)
        if mode != "transforms":
            self.log("influences per vertex: avg {0:.2f}, max {1}".format(
                report["avg_influences"], report["max_influences"]))
        if report.get("joints"):
            self.log("{0} joint(s) created: {1} ...".format(
                len(report["joints"]),
                ", ".join(n.split("|")[-1] for n in report["joints"][:4])), ok=True)
        if report.get("keys"):
            self.log("{0} keys baked.".format(report["keys"]))
        self.log("done in {0:.1f}s".format(report["seconds"]), ok=True)
        if report["rmse_pct"] > 1.0:
            self.log("The error is high - the cache may not be reproducible with "
                     "linear blend skinning (cloth, muscle or volume effects), or the "
                     "joints/frame range may not match the cache.", warn=True)
