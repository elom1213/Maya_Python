# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00480_FileTool - Import > FBX 의 `Mocap FBX Import (Exact Rotation)` 섹션 (v01.13, in-Maya)
#
#   FBX File   [.....................................] [Browse]
#   Info       FBX 7700, Z-up, cm, 60 fps, frames 1-6285, 5 skeletons, ...
#   Skeletons  [x] CHOEUN (73)  [x] SUA (73)  [x] ZHAN (73)
#              [x] IVI (73)     [x] KANA (73)              [All] [None]
#   Options    [x] Skeletons only   [x] Normalize joints   [x] Unwrap rotations   [x] Verify against file
#   [ Import FBX (Exact) ]                                  [ Fix Scene From FBX ]
#
# 마야 FBX 임포터가 비 XYZ 회전 순서 조인트(모캡 Hips 등)의 회전 키를 뒤집는 문제를, FBX 파일의 원본 키로 커브를 다시 써서
# 고친다. 로직은 Framework.core.maya_fbx_exact (core.import_ops 가 얇게 감싼다). 기본값은 사용자 결정(2026-10-27) -
# Normalize ON(0020 처럼 jointOrient 0 · rotateOrder xyz) · Skeletons only ON · 타임라인 파일 그대로 · undo 기록 안 함.

import os

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QApplication,
    Qt,
)

from tools.A00480_FileTool.app import core

#: 스켈레톤 체크박스 한 줄의 개수
SKELETON_COLUMNS = 3


class FbxExactImportSection(QGroupBox):
    """Import > FBX 의 모캡 FBX 정확 임포트 섹션."""

    def __init__(self, log=None, parent=None):
        super(FbxExactImportSection, self).__init__("Mocap FBX Import (Exact Rotation)", parent)
        self._log_callback = log
        self._info = None
        self.skeleton_checks = []        # [(이름, QCheckBox)]
        self.build_ui()
        self._update_buttons()

    # ------------------------------------------------------------------ UI

    def build_ui(self):
        self.setToolTip(
            "The Maya FBX importer can flip the rotation keys of joints whose rotate order is not XYZ\n"
            "(e.g. mocap Hips), so the pose is wrong. This imports the FBX and then rebuilds the joint\n"
            "rotation (and translation) curves from the keys stored in the file.")
        grid = QGridLayout(self)

        grid.addWidget(QLabel("FBX File"), 0, 0)
        self.le_path = QLineEdit()
        self.le_path.setPlaceholderText("Binary FBX with a skeleton (mocap)")
        self.le_path.editingFinished.connect(self.on_scan)
        grid.addWidget(self.le_path, 0, 1)
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.on_browse)
        grid.addWidget(btn_browse, 0, 2)

        grid.addWidget(QLabel("Info"), 1, 0)
        self.lbl_info = QLabel("-")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        grid.addWidget(self.lbl_info, 1, 1, 1, 2)

        grid.addWidget(QLabel("Skeletons"), 2, 0, Qt.AlignTop)
        skel_row = QHBoxLayout()
        self.skeleton_box = QWidget()
        self.skeleton_grid = QGridLayout(self.skeleton_box)
        self.skeleton_grid.setContentsMargins(0, 0, 0, 0)
        skel_row.addWidget(self.skeleton_box, 1)
        skel_btns = QVBoxLayout()
        self.btn_all = QPushButton("All")
        self.btn_all.clicked.connect(lambda: self._check_all(True))
        self.btn_none = QPushButton("None")
        self.btn_none.clicked.connect(lambda: self._check_all(False))
        skel_btns.addWidget(self.btn_all)
        skel_btns.addWidget(self.btn_none)
        skel_btns.addStretch(1)
        skel_row.addLayout(skel_btns)
        grid.addLayout(skel_row, 2, 1, 1, 2)

        grid.addWidget(QLabel("Options"), 3, 0, Qt.AlignTop)
        opts = QGridLayout()
        self.chk_skeletons_only = QCheckBox("Skeletons only")
        self.chk_skeletons_only.setChecked(True)
        self.chk_skeletons_only.setToolTip(
            "Import: delete what is not a skeleton - markers under the skeleton roots,\n"
            "cameras and other top nodes. Unchecked skeletons are always deleted.")
        self.chk_normalize = QCheckBox("Normalize joints (jointOrient 0, rotateOrder xyz)")
        self.chk_normalize.setChecked(True)
        self.chk_normalize.setToolTip(
            "Bake jointOrient (FBX PreRotation) and the rotate order into the rotation, so every joint\n"
            "has jointOrient 0 and rotateOrder xyz - the same layout as a Blender round trip.\n"
            "The pose is the same either way. Unchecked = keep the file layout.")
        self.chk_normalize.toggled.connect(self._update_buttons)
        self.chk_unwrap = QCheckBox("Unwrap rotations (rotate order aware)")
        self.chk_unwrap.setChecked(True)
        self.chk_unwrap.setToolTip(
            "Remove 360 deg jumps between keys using the solutions that keep the pose for the joint's\n"
            "rotate order. Normalize joints always does this, so it applies only when Normalize is off.")
        self.chk_verify = QCheckBox("Verify against file")
        self.chk_verify.setChecked(True)
        self.chk_verify.setToolTip("Compare the result with the file at sample frames and log the largest error.")
        opts.addWidget(self.chk_skeletons_only, 0, 0)
        opts.addWidget(self.chk_verify, 0, 1)
        opts.addWidget(self.chk_normalize, 1, 0, 1, 2)
        opts.addWidget(self.chk_unwrap, 2, 0, 1, 2)
        grid.addLayout(opts, 3, 1, 1, 2)

        btn_row = QHBoxLayout()
        self.btn_import = QPushButton("Import FBX (Exact)")
        self.btn_import.setMinimumHeight(32)
        self.btn_import.setToolTip(
            "Import the checked skeletons with the Maya FBX importer, then rebuild their rotation curves\n"
            "from the file. Stops if the scene already has a node with the same root name.\n"
            "Undo is not recorded (millions of keys).")
        self.btn_import.clicked.connect(self.on_import)
        btn_row.addWidget(self.btn_import, 1)
        self.btn_fix = QPushButton("Fix Scene From FBX")
        self.btn_fix.setMinimumHeight(32)
        self.btn_fix.setToolTip(
            "For a scene that was already imported straight from this FBX: rebuild the rotation curves\n"
            "of the selected roots (or every top node named like a skeleton in the file) from the file.\n"
            "Joints whose rotate order / jointOrient no longer match the file are skipped.")
        self.btn_fix.clicked.connect(self.on_fix)
        btn_row.addWidget(self.btn_fix, 1)
        grid.addLayout(btn_row, 4, 0, 1, 3)

        grid.setColumnStretch(1, 1)

    # ------------------------------------------------------------- 상태

    def _update_buttons(self, *_args):
        has_file = self._info is not None
        self.btn_import.setEnabled(has_file and bool(self.checked_skeletons()))
        self.btn_fix.setEnabled(has_file)
        self.btn_all.setEnabled(bool(self.skeleton_checks))
        self.btn_none.setEnabled(bool(self.skeleton_checks))
        self.chk_unwrap.setEnabled(not self.chk_normalize.isChecked())

    def _set_skeletons(self, skeletons):
        for _name, chk in self.skeleton_checks:
            self.skeleton_grid.removeWidget(chk)
            chk.deleteLater()
        self.skeleton_checks = []
        for index, (name, count) in enumerate(skeletons):
            chk = QCheckBox("{0} ({1})".format(name, count))
            chk.setChecked(True)
            chk.toggled.connect(self._update_buttons)
            self.skeleton_grid.addWidget(chk, index // SKELETON_COLUMNS, index % SKELETON_COLUMNS)
            self.skeleton_checks.append((name, chk))

    def _check_all(self, state):
        for _name, chk in self.skeleton_checks:
            chk.setChecked(state)

    def checked_skeletons(self):
        return [name for name, chk in self.skeleton_checks if chk.isChecked()]

    # ------------------------------------------------------------ 핸들러

    def on_browse(self):
        start = os.path.dirname(self.le_path.text().strip()) if self.le_path.text().strip() else ""
        path, _filter = QFileDialog.getOpenFileName(self, "Select FBX", start, "FBX (*.fbx);;All Files (*)")
        if path:
            self.le_path.setText(path)
            self.on_scan()

    def on_scan(self):
        path = self.le_path.text().strip()
        if not path:
            self._info = None
            self.lbl_info.setText("-")
            self._set_skeletons([])
            self._update_buttons()
            return
        if self._info is not None and self._info.get("path") == path:
            return
        info, logs = core.scan_fbx_exact(path)
        self._info = info
        self.lbl_info.setText(logs[0][len("[Info] "):] if info else "-")
        self._set_skeletons(info["skeletons"] if info else [])
        self._log_all(logs)
        self._update_buttons()

    def on_import(self):
        path = self.le_path.text().strip()
        if not self._ensure_scanned(path):
            return
        self._run(core.import_fbx_exact, path, skeletons=self.checked_skeletons(),
                  skeletons_only=self.chk_skeletons_only.isChecked(), unwrap=self.chk_unwrap.isChecked(),
                  normalize=self.chk_normalize.isChecked(), verify=self.chk_verify.isChecked())

    def on_fix(self):
        path = self.le_path.text().strip()
        if not self._ensure_scanned(path):
            return
        import maya.cmds as cmds
        selection = cmds.ls(selection=True, long=True) or []
        roots = sorted({"|" + node.split("|")[1] for node in selection if node.startswith("|")}) or None
        self._run(core.fix_scene_from_fbx, path, roots=roots, unwrap=self.chk_unwrap.isChecked(),
                  normalize=self.chk_normalize.isChecked(), verify=self.chk_verify.isChecked())

    # ------------------------------------------------------------ 보조

    def _ensure_scanned(self, path):
        if self._info is None or self._info.get("path") != path:
            self._info = None
            self.on_scan()
        return self._info is not None

    def _run(self, func, path, **kwargs):
        self._log("[Info] {0} : {1}".format(
            "Import FBX (Exact)" if func is core.import_fbx_exact else "Fix Scene From FBX", path))
        self.btn_import.setEnabled(False)
        self.btn_fix.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            _ok, logs = func(path, progress=self._progress, **kwargs)
        finally:
            QApplication.restoreOverrideCursor()
            self._update_buttons()
        self._log_all(logs)

    def _progress(self, message):
        self._log(message)
        QApplication.processEvents()

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)
