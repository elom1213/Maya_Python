# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - Qt UI

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.core.maya_refresh import force_refresh

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00280_correctiveFromCache.app.config.version import VERSION, LAST_UPDATE
from tools.A00280_correctiveFromCache.app.core import (
    PoseWranglerBridge, AlembicCache, CorrectiveBatchManager,
    SolverSource, MirrorManager,
)


WINDOW_OBJECT_NAME = "JUN_A00280_correctiveFromCache_window"

# Per-pose 테이블 컬럼
COL_SOLVER = 0
COL_POSE = 1
COL_FRAME = 2
COL_PROCESS = 3
COL_STATUS = 4


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 720
        self.win_height = 700
        self.win_title = f"Corrective From Cache v{VERSION}"

        self.resize(self.win_width, self.win_height)

        # PoseWrangler 래퍼 (생성만; UERBFAPI 는 실제 사용 시 lazy import)
        self.bridge = PoseWranglerBridge()
        self._solver_cache = {}   # name -> RBFNode

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        main_layout.addWidget(self._build_source_group())
        main_layout.addWidget(self._build_mesh_group())
        main_layout.addWidget(self._build_pose_table_group())
        main_layout.addWidget(self._build_options_group())

        # 실행 버튼
        run_row = QHBoxLayout()
        self.btn_generate = QPushButton("Generate Correctives From Cache")
        self.btn_generate.setMinimumHeight(40)
        self.btn_generate.clicked.connect(self.on_generate)
        self.btn_mirror = QPushButton("Mirror Selected Poses")
        self.btn_mirror.clicked.connect(self.on_mirror)
        run_row.addWidget(self.btn_generate, 3)
        run_row.addWidget(self.btn_mirror, 1)
        main_layout.addLayout(run_row)

        # 로그
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(90)
        self.te_log.setMaximumHeight(150)
        main_layout.addWidget(self.te_log)

        self.btn_force_refresh = QPushButton("Force Refresh (Unfreeze Viewport)")
        self.btn_force_refresh.clicked.connect(self.on_force_refresh)
        main_layout.addWidget(self.btn_force_refresh)

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    def _build_source_group(self):
        grp = QGroupBox("Solver Source")
        layout = QVBoxLayout(grp)

        mode_row = QHBoxLayout()
        self.src_grp = QButtonGroup(self)
        self.rb_src_scene = QRadioButton("Scene solvers")
        self.rb_src_json = QRadioButton("From JSON")
        self.rb_src_scene.setChecked(True)
        self.src_grp.addButton(self.rb_src_scene)
        self.src_grp.addButton(self.rb_src_json)
        mode_row.addWidget(self.rb_src_scene)
        mode_row.addWidget(self.rb_src_json)
        self.le_json = QLineEdit()
        self.le_json.setPlaceholderText("sample_04.json path (for 'From JSON')")
        btn_json = QPushButton("Browse")
        btn_json.clicked.connect(self._browse_json)
        mode_row.addWidget(self.le_json)
        mode_row.addWidget(btn_json)
        layout.addLayout(mode_row)

        load_row = QHBoxLayout()
        self.btn_load_solvers = QPushButton("Load Solvers")
        self.btn_load_solvers.clicked.connect(self.on_load_solvers)
        load_row.addWidget(self.btn_load_solvers)
        load_row.addWidget(QLabel("(multi-select solvers, then Refresh Poses)"))
        load_row.addStretch(1)
        layout.addLayout(load_row)

        self.lst_solvers = QListWidget()
        self.lst_solvers.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lst_solvers.setMaximumHeight(110)
        layout.addWidget(self.lst_solvers)

        return grp

    def _build_mesh_group(self):
        grp = QGroupBox("Meshes")
        layout = QVBoxLayout(grp)

        # Garment base mesh
        m_row = QHBoxLayout()
        m_row.addWidget(QLabel("Garment Base Mesh"))
        self.le_base = QLineEdit()
        self.le_base.setPlaceholderText("skinned garment (blendShape goes front-of-chain)")
        m_row.addWidget(self.le_base)
        btn_pick_base = QPushButton("Pick Selected")
        btn_pick_base.clicked.connect(lambda: self._pick_mesh(self.le_base))
        m_row.addWidget(btn_pick_base)
        layout.addLayout(m_row)

        # Alembic cache
        a_row = QHBoxLayout()
        self.abc_grp = QButtonGroup(self)
        self.rb_abc_node = QRadioButton("Scene node")
        self.rb_abc_file = QRadioButton(".abc file")
        self.rb_abc_node.setChecked(True)
        self.abc_grp.addButton(self.rb_abc_node)
        self.abc_grp.addButton(self.rb_abc_file)
        a_row.addWidget(QLabel("Alembic Cache"))
        a_row.addWidget(self.rb_abc_node)
        a_row.addWidget(self.rb_abc_file)
        self.le_abc = QLineEdit()
        self.le_abc.setPlaceholderText("cache mesh node, or .abc file path")
        a_row.addWidget(self.le_abc)
        btn_pick_abc = QPushButton("Pick / Browse")
        btn_pick_abc.clicked.connect(self._pick_abc)
        a_row.addWidget(btn_pick_abc)
        layout.addLayout(a_row)

        return grp

    def _build_pose_table_group(self):
        grp = QGroupBox("Poses")
        layout = QVBoxLayout(grp)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Start Frame"))
        self.le_start = QLineEdit("0")
        self.le_start.setValidator(QIntValidator(-1000000, 1000000, self))
        self.le_start.setMaximumWidth(80)
        top_row.addWidget(self.le_start)

        top_row.addSpacing(12)
        top_row.addWidget(QLabel("Frame Step"))
        self.le_step = QLineEdit("1")
        self.le_step.setValidator(QIntValidator(1, 1000000, self))
        self.le_step.setMaximumWidth(70)
        self.le_step.setToolTip("frame = start + poseIndex x step. "
                                "Set this to the cache's per-pose interval (e.g. 60).")
        top_row.addWidget(self.le_step)

        self.btn_refresh_poses = QPushButton("Refresh Poses")
        self.btn_refresh_poses.clicked.connect(self.on_refresh_poses)
        top_row.addWidget(self.btn_refresh_poses)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(["Solver", "Pose", "Frame", "Process", "Status"])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setMinimumHeight(180)
        layout.addWidget(self.tbl)

        return grp

    def _build_options_group(self):
        grp = QGroupBox("Options")
        layout = QVBoxLayout(grp)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Route"))
        self.route_grp = QButtonGroup(self)
        self.rb_route_pw = QRadioButton("PoseWrangler (auto-wire)")
        self.rb_route_direct = QRadioButton("Direct invertShape (A00090 wires)")
        self.rb_route_pw.setChecked(True)
        self.route_grp.addButton(self.rb_route_pw)
        self.route_grp.addButton(self.rb_route_direct)
        r1.addWidget(self.rb_route_pw)
        r1.addWidget(self.rb_route_direct)
        r1.addStretch(1)
        layout.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("If target exists"))
        self.exist_grp = QButtonGroup(self)
        self.rb_skip = QRadioButton("Skip")
        self.rb_overwrite = QRadioButton("Overwrite")
        self.rb_skip.setChecked(True)
        self.exist_grp.addButton(self.rb_skip)
        self.exist_grp.addButton(self.rb_overwrite)
        r2.addWidget(self.rb_skip)
        r2.addWidget(self.rb_overwrite)
        r2.addSpacing(16)
        r2.addWidget(QLabel("Skip if max delta <"))
        self.le_eps = QLineEdit("0.0")
        self.le_eps.setValidator(QDoubleValidator(0.0, 1000.0, 4, self))
        self.le_eps.setMaximumWidth(70)
        r2.addWidget(self.le_eps)
        r2.addStretch(1)
        layout.addLayout(r2)

        r3 = QHBoxLayout()
        self.cb_include_default = QCheckBox("Include 'default' pose (build a target for it too)")
        self.cb_include_default.setChecked(False)
        self.cb_include_default.toggled.connect(self._on_include_default_toggled)
        r3.addWidget(self.cb_include_default)
        r3.addStretch(1)
        layout.addLayout(r3)

        return grp

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def on_force_refresh(self):
        force_refresh()
        self.log("Viewport refresh restored.")

    def _browse_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select solver JSON", "", "JSON (*.json)")
        if path:
            self.le_json.setText(path)
            self.rb_src_json.setChecked(True)

    def _pick_mesh(self, line_edit):
        sel = cmds.ls(sl=True, long=False) or []
        if not sel:
            self.log("[Warning] Select a mesh first.")
            return
        node = sel[0]
        if cmds.objectType(node) == "mesh":
            parents = cmds.listRelatives(node, parent=True) or []
            node = parents[0] if parents else node
        line_edit.setText(node)

    def _pick_abc(self):
        if self.rb_abc_file.isChecked():
            path, _ = QFileDialog.getOpenFileName(self, "Select .abc", "", "Alembic (*.abc)")
            if path:
                self.le_abc.setText(path)
        else:
            self._pick_mesh(self.le_abc)

    def _resolve_solver(self, name):
        """이름 -> RBFNode (캐시). 실패 시 None."""
        if name in self._solver_cache:
            return self._solver_cache[name]
        node = self.bridge.get_solver(name)
        self._solver_cache[name] = node
        return node

    def _build_cache(self):
        """현재 Alembic 입력으로 AlembicCache 생성. 실패 시 None(+로그)."""
        abc = self.le_abc.text().strip()
        if not abc:
            self.log("[Warning] Set an Alembic cache node or .abc file.")
            return None
        try:
            if self.rb_abc_file.isChecked():
                return AlembicCache.from_file(abc)
            return AlembicCache(abc)
        except Exception as exc:
            self.log("[Error] Alembic: {0}".format(exc))
            return None

    # --------------------------------------------------
    # Handlers
    # --------------------------------------------------

    def on_load_solvers(self):
        self.lst_solvers.clear()
        self._solver_cache.clear()
        try:
            if self.rb_src_json.isChecked():
                path = self.le_json.text().strip()
                if not path:
                    self.log("[Warning] Set a JSON path.")
                    return
                names = SolverSource.from_json(path)
            else:
                names = SolverSource.from_scene(self.bridge)
        except Exception as exc:
            self.log("[Error] Load solvers: {0}".format(exc))
            return

        if not names:
            self.log("[Warning] No solvers found.")
            return
        self.lst_solvers.addItems(names)
        self.log("Loaded {0} solver(s). Select some, then Refresh Poses.".format(len(names)))

    def on_refresh_poses(self):
        names = [i.text() for i in self.lst_solvers.selectedItems()]
        if not names:
            self.log("[Warning] Select solver(s) in the list first.")
            return

        start = int(self.le_start.text() or "0")
        step = int(self.le_step.text() or "1")
        if step < 1:
            step = 1
        self.tbl.setRowCount(0)

        for name in names:
            solver = self._resolve_solver(name)
            if solver is None:
                self.log("[Warning] Solver '{0}' not found in scene.".format(name))
                continue
            try:
                frame_map = self.bridge.frame_map(solver, start, step)
            except Exception as exc:
                self.log("[Error] poses({0}): {1}".format(name, exc))
                continue
            include_default = self.cb_include_default.isChecked()
            for pose, frame in frame_map.items():
                self._add_row(name, pose, frame,
                              process=(pose != "default") or include_default)

        self.log("Pose table refreshed ({0} row(s)).".format(self.tbl.rowCount()))

    def _add_row(self, solver_name, pose, frame, process=True):
        r = self.tbl.rowCount()
        self.tbl.insertRow(r)

        it_solver = QTableWidgetItem(solver_name)
        it_solver.setFlags(it_solver.flags() & ~Qt.ItemIsEditable)
        self.tbl.setItem(r, COL_SOLVER, it_solver)

        it_pose = QTableWidgetItem(pose)
        it_pose.setFlags(it_pose.flags() & ~Qt.ItemIsEditable)
        self.tbl.setItem(r, COL_POSE, it_pose)

        self.tbl.setItem(r, COL_FRAME, QTableWidgetItem(str(frame)))   # 편집 가능

        it_proc = QTableWidgetItem()
        it_proc.setFlags((it_proc.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable)
        it_proc.setCheckState(Qt.Checked if process else Qt.Unchecked)
        self.tbl.setItem(r, COL_PROCESS, it_proc)

        self.tbl.setItem(r, COL_STATUS, QTableWidgetItem(""))

    def _on_include_default_toggled(self, checked):
        """옵션 토글 시 이미 만들어진 테이블의 default 행 체크 상태를 갱신."""
        for r in range(self.tbl.rowCount()):
            pose_item = self.tbl.item(r, COL_POSE)
            if pose_item is None or pose_item.text() != "default":
                continue
            proc = self.tbl.item(r, COL_PROCESS)
            if proc is not None:
                proc.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def _collect_jobs(self, require_checked=True):
        """체크된 행 -> [(solver_node, name, pose, frame, row), ...]."""
        jobs = []
        for r in range(self.tbl.rowCount()):
            proc = self.tbl.item(r, COL_PROCESS)
            if require_checked and (proc is None or proc.checkState() != Qt.Checked):
                continue
            name = self.tbl.item(r, COL_SOLVER).text()
            pose = self.tbl.item(r, COL_POSE).text()
            try:
                frame = int(self.tbl.item(r, COL_FRAME).text())
            except (TypeError, ValueError):
                self.log("[Warning] Row {0}: invalid frame, skipped.".format(r))
                continue
            solver = self._resolve_solver(name)
            if solver is None:
                self.log("[Warning] Solver '{0}' missing, row skipped.".format(name))
                continue
            jobs.append((solver, name, pose, frame, r))
        return jobs

    def on_generate(self):
        base = self.le_base.text().strip()
        if not base or not cmds.objExists(base):
            self.log("[Warning] Set a valid Garment Base Mesh.")
            return

        cache = self._build_cache()
        if cache is None:
            return

        rows = self._collect_jobs(require_checked=True)
        if not rows:
            self.log("[Warning] No checked poses to process.")
            return

        # 테이블 행 매핑 보존하며 jobs 구성
        jobs = [(s, n, p, f) for (s, n, p, f, _r) in rows]
        job_rows = [r for (_s, _n, _p, _f, r) in rows]

        def status_cb(idx, text):
            self.tbl.item(job_rows[idx], COL_STATUS).setText(text)

        route = (CorrectiveBatchManager.ROUTE_POSEWRANGLER
                 if self.rb_route_pw.isChecked()
                 else CorrectiveBatchManager.ROUTE_DIRECT)
        exists_policy = (CorrectiveBatchManager.SKIP
                         if self.rb_skip.isChecked()
                         else CorrectiveBatchManager.OVERWRITE)
        try:
            skip_eps = float(self.le_eps.text() or "0.0")
        except ValueError:
            skip_eps = 0.0

        mgr = CorrectiveBatchManager(self.bridge)
        count, msg = mgr.generate_batch(
            jobs, base, cache,
            route=route, wire=self.rb_route_pw.isChecked(),
            exists_policy=exists_policy, skip_eps=skip_eps,
            include_default=self.cb_include_default.isChecked(),
            status_cb=status_cb)
        self.log(msg)

    def on_mirror(self):
        rows = self._collect_jobs(require_checked=True)
        if not rows:
            self.log("[Warning] Check the poses you want to mirror.")
            return
        jobs = [(s, n, p) for (s, n, p, _f, _r) in rows]
        job_rows = [r for (_s, _n, _p, _f, r) in rows]

        def status_cb(idx, text):
            self.tbl.item(job_rows[idx], COL_STATUS).setText(text)

        mgr = MirrorManager(self.bridge)
        count, msg = mgr.mirror(jobs, status_cb=status_cb)
        self.log(msg)

    def show_about(self, *args):
        QMessageBox.information(
            self, "About",
            f"Corrective From Cache v{VERSION}\n"
            f"Batch-extract MetaHuman RBF cloth-wrinkle correctives from an Alembic cache.\n"
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}")
