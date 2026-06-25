# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-25
# A00300_meshDoctor - Qt UI
#
# 상단 Diagnose 로 선택 메시를 진단(읽기 전용)하고, 로그뷰에 요약 출력 + 0020_out/ 에
# JSON/TXT 저장. 하단 Fixes 그룹의 버튼은 안전 원클릭 수정(Undo 가능)을 실행한다.

import os

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_collapsible_qt

import maya.cmds as cmds

from tools.A00300_meshDoctor.app.config.version import VERSION, LAST_UPDATE
from tools.A00300_meshDoctor.app.core import MeshScanner, ReportWriter, MeshFixer


WINDOW_OBJECT_NAME = "JUN_A00300_meshDoctor_window"

_SEV_COLOR = {
    "FAIL": "#ff6b6b",
    "WARN": "#ffd166",
    "INFO": "#8ab4f8",
    "PASS": "#6bcf8a",
}


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Mesh Doctor v{0}".format(VERSION)
        self.resize(560, 680)

        self._last_out_dir = None
        self.scanner = MeshScanner()

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        # 메뉴 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # --- Diagnose 행 ---
        diag_row = QHBoxLayout()
        self.btn_diagnose = QPushButton("Diagnose Selected")
        self.btn_diagnose.setMinimumHeight(38)
        self.btn_diagnose.clicked.connect(self.on_diagnose)
        diag_row.addWidget(self.btn_diagnose, 3)

        self.btn_open = QPushButton("Open Log Folder")
        self.btn_open.setMinimumHeight(38)
        self.btn_open.clicked.connect(self.on_open_folder)
        diag_row.addWidget(self.btn_open, 1)
        root.addLayout(diag_row)

        # --- 로그뷰 ---
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setLineWrapMode(QTextEdit.NoWrap)
        self.te_log.setMinimumHeight(280)
        try:
            self.te_log.setFont(QFont("Consolas", 9))
        except Exception:
            pass
        root.addWidget(self.te_log, 1)

        # --- Fixes (접이식) ---
        fixes = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            "Safe One-Click Fixes  (undoable)", expanded=True)
        for label, slot, tip in [
            ("Delete History (deformer-safe)", self._fix(MeshFixer.delete_history),
             "Bake out leftover poly history, keep skinCluster/blendShape."),
            ("Merge Vertices", self._fix(MeshFixer.merge_vertices),
             "Merge coincident/unmerged vertices (tol 1e-4)."),
            ("Conform Normals", self._fix(MeshFixer.conform_normals),
             "Unlock + conform face normals (fixes flipped/locked normals)."),
            ("polyCleanup (fix corruption)", self._fix(MeshFixer.poly_cleanup),
             "Fix non-manifold + lamina + zero-area faces + zero-length edges. "
             "May change topology -> re-skin if needed."),
            ("Snap NaN / Stray Verts", self._fix(MeshFixer.snap_stray_verts),
             "Move NaN/stray verts to mesh centroid (no delete) -> deflates bbox, "
             "fixes empty-space selection."),
        ]:
            b = QPushButton(label)
            b.setMinimumHeight(30)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            fixes.add_widget(b)
        root.addWidget(fixes)

        # --- Select problem components (접이식) ---
        picks = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            "Select Problem Components", expanded=False)
        for label, slot in [
            ("Select Non-Manifold", self._fix(MeshFixer.select_non_manifold)),
            ("Select Zero-Area Faces", self._fix(MeshFixer.select_zero_area_faces)),
            ("Select Stray / NaN Verts", self._fix(MeshFixer.select_stray_verts)),
        ]:
            b = QPushButton(label)
            b.setMinimumHeight(28)
            b.clicked.connect(slot)
            picks.add_widget(b)
        root.addWidget(picks)

        self.log("Mesh Doctor v{0} ({1}) ready. Select a mesh and Diagnose.".format(
            VERSION, LAST_UPDATE))

    # --------------------------------------------------
    # actions
    # --------------------------------------------------

    def on_diagnose(self):
        self.te_log.clear()
        try:
            results = self.scanner.scan_selection()
        except Exception as e:
            self.log("Diagnose failed: {0}".format(e), "FAIL")
            return

        if not results:
            self.log("No polygon mesh selected. Select a mesh and try again.", "WARN")
            return

        for r in results:
            self._print_result(r)

        # 로그 파일 저장
        try:
            json_path, txt_path, out_dir = ReportWriter().write(results)
            self._last_out_dir = out_dir
            self.log("")
            self.log("Log written:", "INFO")
            self.log("  " + json_path, "INFO")
            self.log("  " + txt_path, "INFO")
            self.log("Share the .json with Claude for root-cause analysis.", "INFO")
        except Exception as e:
            self.log("Failed to write log file: {0}".format(e), "FAIL")

    def on_open_folder(self):
        out_dir = self._last_out_dir
        if not out_dir:
            # 아직 진단 전이면 기본 0020_out 경로라도 열어준다.
            try:
                _j, _t, out_dir = None, None, None
                from tools.A00300_meshDoctor.app.core.report import ReportWriter as _RW
                out_dir = str(_RW().pm.path("write"))
            except Exception:
                pass
        if out_dir and os.path.isdir(out_dir):
            try:
                os.startfile(out_dir)
            except Exception as e:
                self.log("Could not open folder: {0}".format(e), "WARN")
        else:
            self.log("No log folder yet. Run Diagnose first.", "WARN")

    def _fix(self, fn):
        def _slot():
            try:
                msg = fn()
            except Exception as e:
                msg = "{0} error: {1}".format(getattr(fn, "__name__", "fix"), e)
                self.log(msg, "FAIL")
                return
            self.log(msg, "INFO")
            self.log("  -> Re-run Diagnose to confirm.", "INFO")
        return _slot

    # --------------------------------------------------
    # log helpers
    # --------------------------------------------------

    def _print_result(self, r):
        c = r.get("counts", {})
        self.log("=" * 60)
        self.log("MESH: {0}  [{1}]  => {2}".format(
            r["transform"], r["shape"], r["worst"]),
            r["worst"])
        self.log("  verts={0} edges={1} faces={2} shells={3}".format(
            c.get("vertices", "?"), c.get("edges", "?"),
            c.get("faces", "?"), c.get("shells", "?")))
        for cause in r.get("suspected_root_causes", []):
            self.log("  >> " + cause, "WARN" if "Symptom" in cause else "PASS")
        self.log("-" * 60)
        for chk in r["checks"]:
            if chk["severity"] == "PASS":
                continue
            line = "  [{0}] {1}".format(chk["severity"], chk["check"])
            if chk["count"]:
                line += " (count={0})".format(chk["count"])
            self.log(line, chk["severity"])
            self.log("      " + chk["message"])
        self.log("")

    def log(self, text, severity=None):
        color = _SEV_COLOR.get(severity)
        if color:
            safe = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            self.te_log.append('<span style="color:{0};">{1}</span>'.format(color, safe))
        else:
            self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Mesh Doctor\nv{0}  ({1})\n\n"
            "Read-only mesh diagnostics + safe one-click fixes.\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
