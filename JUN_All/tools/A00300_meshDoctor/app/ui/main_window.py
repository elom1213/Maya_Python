# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-07
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
from tools.A00300_meshDoctor.app.core.mesh_scan import shape_of


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
        self.resize(600, 820)

        self._last_out_dir = None
        self._results = []                 # 마지막 진단 결과(요약 테이블 행과 1:1 대응)
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

        # --- Target Meshes (진단 대상 리스트) ---
        # 여러 메시를 리스트업해 한 번에 진단한다. 비어 있으면 현재 선택을 진단(하위호환).
        # 항목은 UUID 로 보관(중복 이름/리페어런트에도 안전), 표시는 짧은 이름.
        targets_group = QGroupBox("Target Meshes")
        tg_layout = QHBoxLayout(targets_group)

        self.lst_targets = QListWidget()
        self.lst_targets.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lst_targets.setToolTip(
            "Meshes to diagnose. Empty = diagnose the current Maya selection.")
        self.lst_targets.setMaximumHeight(110)
        tg_layout.addWidget(self.lst_targets, 1)

        tg_btns = QVBoxLayout()
        b_add = QPushButton("Add Selected")
        b_add.setToolTip("Add currently selected polygon meshes to the list.")
        b_add.clicked.connect(self.on_add_selected)
        b_remove = QPushButton("Remove")
        b_remove.setToolTip("Remove the selected rows from the list.")
        b_remove.clicked.connect(self.on_remove_targets)
        b_clear = QPushButton("Clear")
        b_clear.clicked.connect(self.on_clear_targets)
        for b in (b_add, b_remove, b_clear):
            b.setMinimumHeight(28)
            tg_btns.addWidget(b)
        tg_btns.addStretch(1)
        tg_layout.addLayout(tg_btns)
        root.addWidget(targets_group)

        # --- Diagnose 행 ---
        diag_row = QHBoxLayout()
        self.btn_diagnose = QPushButton("Diagnose Listed")
        self.btn_diagnose.setMinimumHeight(38)
        self.btn_diagnose.setToolTip(
            "Diagnose every mesh in the list above (or the current selection if the list is empty).")
        self.btn_diagnose.clicked.connect(self.on_diagnose)
        diag_row.addWidget(self.btn_diagnose, 3)

        self.btn_open = QPushButton("Open Log Folder")
        self.btn_open.setMinimumHeight(38)
        self.btn_open.clicked.connect(self.on_open_folder)
        diag_row.addWidget(self.btn_open, 1)
        root.addLayout(diag_row)

        # --- Summary 테이블 (메시당 한 줄, 행 클릭 -> 아래 로그에 상세) ---
        self.tbl_summary = QTableWidget(0, 3)
        self.tbl_summary.setHorizontalHeaderLabels(["Mesh", "Status", "Issues"])
        self.tbl_summary.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_summary.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_summary.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_summary.verticalHeader().setVisible(False)
        self.tbl_summary.setMinimumHeight(150)
        self.tbl_summary.setToolTip("Click a row to show that mesh's full report below.")
        hdr = self.tbl_summary.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_summary.itemSelectionChanged.connect(self._on_summary_row)
        root.addWidget(self.tbl_summary, 1)

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

        # --- 로그 Clear ---
        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.setToolTip("Clear the log view above.")
        self.btn_clear_log.clicked.connect(lambda: self.te_log.clear())
        root.addWidget(self.btn_clear_log)

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

        self.log("Mesh Doctor v{0} ({1}) ready. Add meshes to the list (or select) "
                 "and Diagnose Listed.".format(VERSION, LAST_UPDATE))

    # --------------------------------------------------
    # actions
    # --------------------------------------------------

    def on_diagnose(self):
        # 대상: 리스트업된 메시 우선, 비어 있으면 현재 선택(하위호환).
        nodes = self._listed_nodes()
        source = "listed"
        if not nodes:
            nodes = cmds.ls(selection=True, long=True) or []
            source = "selection"

        self.te_log.clear()
        try:
            results = self.scanner.scan_nodes(nodes)
        except Exception as e:
            self.log("Diagnose failed: {0}".format(e), "FAIL")
            return

        self._results = results
        self._fill_summary(results)

        if not results:
            where = "in the list" if source == "listed" else "selected"
            self.log("No polygon mesh {0}. Add meshes to the list (or select) and "
                     "try again.".format(where), "WARN")
            return

        # 로그에 배치 요약을 한 번 남긴다(상세는 요약 테이블 행 클릭으로).
        self.log("Diagnosed {0} mesh(es)  [{1}]".format(len(results), source), "INFO")
        for r in results:
            self.log("  [{0}] {1}   {2}".format(
                r["worst"], r["transform"], self._issue_summary(r)), r["worst"])
        self.log("")
        self.log("Click a row in the Summary table above for that mesh's full report.", "INFO")

        # 로그 파일 저장(배치 전체)
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

    # --------------------------------------------------
    # target list (TSL)
    # --------------------------------------------------

    def on_add_selected(self):
        sel = cmds.ls(selection=True, long=True) or []
        existing = set(self._listed_uuids())
        added = 0
        for node in sel:
            shp = shape_of(node)
            if not shp:
                continue
            if cmds.nodeType(node) == "mesh":
                tr = (cmds.listRelatives(node, parent=True, fullPath=True) or [node])[0]
            else:
                tr = node
            uuid = self._to_uuid(tr)
            if not uuid or uuid in existing:
                continue
            existing.add(uuid)
            item = QListWidgetItem(tr.split("|")[-1])
            item.setData(Qt.UserRole, uuid)
            item.setToolTip(tr)
            self.lst_targets.addItem(item)
            added += 1
        if added:
            self.log("Added {0} mesh(es) to the list.".format(added), "INFO")
        else:
            self.log("No new polygon mesh in the selection to add.", "WARN")

    def on_remove_targets(self):
        for item in self.lst_targets.selectedItems():
            self.lst_targets.takeItem(self.lst_targets.row(item))

    def on_clear_targets(self):
        self.lst_targets.clear()

    @staticmethod
    def _to_uuid(node):
        u = cmds.ls(node, uuid=True) or []
        return u[0] if u else None

    def _listed_uuids(self):
        return [self.lst_targets.item(i).data(Qt.UserRole)
                for i in range(self.lst_targets.count())]

    def _listed_nodes(self):
        """리스트의 UUID 를 현재 DAG 경로로 해석. 사라진 항목은 경고하고 건너뛴다."""
        nodes, stale = [], []
        for i in range(self.lst_targets.count()):
            item = self.lst_targets.item(i)
            found = cmds.ls(item.data(Qt.UserRole), long=True) or []
            if found:
                nodes.append(found[0])
            else:
                stale.append(item.text())
        if stale:
            self.log("Skipped {0} missing mesh(es): {1}".format(
                len(stale), ", ".join(stale)), "WARN")
        return nodes

    # --------------------------------------------------
    # summary table
    # --------------------------------------------------

    @staticmethod
    def _issue_summary(r):
        """WARN/FAIL 체크만 'name(count)' 로 요약(FAIL 먼저). 없으면 'clean'."""
        parts = []
        for sev in ("FAIL", "WARN"):
            for chk in r["checks"]:
                if chk["severity"] != sev:
                    continue
                parts.append("{0}({1})".format(chk["check"], chk["count"])
                             if chk["count"] else chk["check"])
        return ", ".join(parts) if parts else "clean"

    def _fill_summary(self, results):
        self.tbl_summary.blockSignals(True)
        self.tbl_summary.setRowCount(0)
        for r in results:
            row = self.tbl_summary.rowCount()
            self.tbl_summary.insertRow(row)

            mesh_item = QTableWidgetItem(r["transform"])
            mesh_item.setToolTip(r.get("transform_full", r["transform"]))

            status_item = QTableWidgetItem("● " + r["worst"])
            color = _SEV_COLOR.get(r["worst"])
            if color:
                status_item.setForeground(QColor(color))

            issues_item = QTableWidgetItem(self._issue_summary(r))
            issues_item.setToolTip(issues_item.text())

            self.tbl_summary.setItem(row, 0, mesh_item)
            self.tbl_summary.setItem(row, 1, status_item)
            self.tbl_summary.setItem(row, 2, issues_item)
        self.tbl_summary.blockSignals(False)

    def _on_summary_row(self):
        row = self.tbl_summary.currentRow()
        if row < 0 or row >= len(self._results):
            return
        self.te_log.clear()
        self._print_result(self._results[row])

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
