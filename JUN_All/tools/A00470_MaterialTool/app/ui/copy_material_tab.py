# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00470_MaterialTool - Copy Material 탭 (in-Maya)
#
# v01.13 : 왼쪽(Source) · 오른쪽(Target) 리스트 두 개. 담긴 개수로 방식이 정해진다.
#   - Source 1 개 + Target n 개 -> **1 -> n** (예전 Set Source + Target 리스트와 같은 동작)
#   - Source n 개 + Target n 개 -> **n 쌍**, 행 순서로 짝 (Source[i] -> Target[i])
#   - 개수가 다르면(Source 2 개 이상) 실행하지 않는다 - 짝이 모호하다.
# 리스트는 공용 TSL(JUN_mod_tsl_qt_v01) 이라 항목을 UUID 로 기억한다 - 담은 뒤 이름을 바꾸거나 부모를
# 옮겨도 같은 메시를 찾는다(예전 Set Source 의 UUID 기억과 같다).
# ★ 짝은 **행마다** 해석한다. get_all_nodes() 는 씬에서 사라진 행을 빼고 주므로 그대로 짝지으면 한 칸씩
#   밀려 엉뚱한 메시끼리 복사된다 - 사라진 행은 그 쌍만 건너뛴다.
# 면마다 붙은 머티리얼이 대상의 같은 면에 똑같이 붙는다. 로직은 core/material_copy.py.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01
from Framework.core.maya_undo import undo_chunk

from tools.A00470_MaterialTool.app.core import material_copy

MODE_NONE, MODE_ONE_TO_N, MODE_PAIRS, MODE_MISMATCH = "none", "one_to_n", "pairs", "mismatch"

_MODE_OK_QSS = "color: #5fd75f;"
_MODE_BAD_QSS = "color: #ff6b6b;"


class CopyMaterialTab(QWidget):

    def __init__(self, log_view=None, parent=None):
        super(CopyMaterialTab, self).__init__(parent)

        self.log_view = log_view
        self.build_ui()
        self.update_mode()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        desc = QLabel(
            "Give the target meshes the same per-face materials as the source meshes.\n"
            "1 source + n targets : the source to every target.\n"
            "n sources + n targets : row by row (source 1 -> target 1, source 2 -> target 2 ...).\n"
            "Each pair is assumed to be the same mesh (same face order).")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        lists = QHBoxLayout()
        self.tsl_source = JUN_mod_tsl_qt_v01(
            title="Source Meshes",
            select_label="Select Sources",
            multi_select=True,
            list_min_height=160,
            log_callback=self.log,
        )
        self.tsl_source.setToolTip(
            "One mesh : its materials go to every target.\n"
            "Several meshes : paired with the targets row by row.\n"
            "Items are remembered by UUID - renaming or reparenting later still finds them.")
        self.tsl_target = JUN_mod_tsl_qt_v01(
            title="Target Meshes",
            select_label="Select Targets",
            multi_select=True,
            list_min_height=160,
            log_callback=self.log,
        )
        for tsl in (self.tsl_source, self.tsl_target):
            model = tsl.list_widget.model()
            model.rowsInserted.connect(self.update_mode)
            model.rowsRemoved.connect(self.update_mode)
            model.modelReset.connect(self.update_mode)
            lists.addWidget(tsl, stretch=1)
        layout.addLayout(lists, stretch=1)

        # 예전 이름(대상 리스트) - tab.tsl 로 접근하던 코드를 살린다.
        self.tsl = self.tsl_target

        self.lbl_mode = QLabel()
        self.lbl_mode.setWordWrap(True)
        layout.addWidget(self.lbl_mode)

        self.btn_copy = QPushButton("Copy Material")
        self.btn_copy.setMinimumHeight(32)
        self.btn_copy.setToolTip(
            "Assign each source's per-face materials to its target(s).\n"
            "A target with a different face count is skipped, not guessed.\n"
            "One undo step.")
        self.btn_copy.clicked.connect(self.on_copy_material)
        layout.addWidget(self.btn_copy)

    # ==================================================================
    # 로그
    # ==================================================================

    def log(self, message):
        if self.log_view is not None:
            self.log_view.appendPlainText(message)
        else:
            print(message)

    # ==================================================================
    # 방식
    # ==================================================================

    def mode(self):
        """(방식, 소스 수, 대상 수)."""
        n_src = self.tsl_source.list_widget.count()
        n_tgt = self.tsl_target.list_widget.count()
        if not n_src or not n_tgt:
            return MODE_NONE, n_src, n_tgt
        if n_src == 1:
            return MODE_ONE_TO_N, n_src, n_tgt
        if n_src == n_tgt:
            return MODE_PAIRS, n_src, n_tgt
        return MODE_MISMATCH, n_src, n_tgt

    def update_mode(self, *args):
        mode, n_src, n_tgt = self.mode()
        if mode == MODE_NONE:
            text, qss = "Fill both lists : one source for 1 -> n, or as many sources as targets.", ""
        elif mode == MODE_ONE_TO_N:
            text, qss = "Mode : 1 -> {0}  (the source to every target)".format(n_tgt), _MODE_OK_QSS
        elif mode == MODE_PAIRS:
            text, qss = "Mode : {0} pairs, row by row".format(n_src), _MODE_OK_QSS
        else:
            text, qss = ("Counts differ : {0} sources, {1} targets. Use one source, or as many "
                         "sources as targets.".format(n_src, n_tgt)), _MODE_BAD_QSS
        self.lbl_mode.setText(text)
        self.lbl_mode.setStyleSheet(qss)
        self.btn_copy.setEnabled(mode in (MODE_ONE_TO_N, MODE_PAIRS))

    @staticmethod
    def _rows(tsl):
        """행마다 (표시 이름, 지금 노드 | None). 사라진 행도 자리를 지킨다."""
        out = []
        for i in range(tsl.list_widget.count()):
            item = tsl.list_widget.item(i)
            out.append((item.text(), tsl._node_of(item)))
        return out

    # ==================================================================
    # 복사
    # ==================================================================

    def on_copy_material(self):
        mode, n_src, n_tgt = self.mode()
        if mode == MODE_NONE:
            self.log("[warning] Fill both the Source and the Target lists.")
            return
        if mode == MODE_MISMATCH:
            self.log("[warning] {0} sources and {1} targets - use one source, or as many sources "
                     "as targets.".format(n_src, n_tgt))
            return

        sources = self._rows(self.tsl_source)
        targets = self._rows(self.tsl_target)

        if mode == MODE_ONE_TO_N:
            name, source = sources[0]
            if not source:
                self.log("[warning] The source mesh '{0}' is not in the scene anymore.".format(name))
                return
            live = []
            for text, node in targets:
                if node:
                    live.append(node)
                else:
                    self.log("[skipped] {0} : not in the scene anymore".format(text))
            if not live:
                self.log("[failed] None of the target meshes are in the scene.")
                return
            with undo_chunk():
                result = material_copy.copy_material_from(source, live)
            for target, why in result["skipped"]:
                self.log("[skipped] {0} : {1}".format(material_copy.short(target), why))
            self._finish(result)
            return

        # n 쌍 : 사라진 행은 그 쌍만 빼고(이름은 리스트에 보이는 그대로 로그), 나머지는 순서 유지.
        pairs = []
        for (s_text, s_node), (t_text, t_node) in zip(sources, targets):
            if s_node and t_node:
                pairs.append((s_node, t_node))
            else:
                self.log("[skipped] {0} -> {1} : not in the scene anymore".format(s_text, t_text))
        if not pairs:
            self.log("[failed] No pair has both meshes in the scene.")
            return
        with undo_chunk():
            result = material_copy.copy_material_pairs(pairs)
        for source, target, why in result["skipped"]:
            self.log("[skipped] {0} -> {1} : {2}".format(
                material_copy.short(source), material_copy.short(target), why))
        if result["ok"]:
            for source, target in result["copied"]:
                self.log("  {0} -> {1}".format(material_copy.short(source), material_copy.short(target)))
        self._finish(result)

    def _finish(self, result):
        for warning in result["warnings"]:
            self.log("[warning] " + warning)
        if not result["ok"]:
            self.log("[failed] " + result["message"])
            return
        self.log(result["message"])
        self.log("  materials : " + ", ".join(result["materials"]))
