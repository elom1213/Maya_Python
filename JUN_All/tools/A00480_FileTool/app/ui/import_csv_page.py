# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-13
# A00480_FileTool - Import > CSV 하위 탭 (in-Maya)
#
# A00200_CSV_tool (ARKit Facial Import) 의 창을 **하위 탭**으로 옮긴 것이다 (v01.10, 원본은 보존).
#
#   CSV File   [...........................] [Browse]
#   Node       [ faceCtrl (52 ARKit)     v ] [Detect] [Selected]
#   Start Frame[ 1 ]   FPS  Recorded [60]  Output [30 v]
#   Audio      [x] Import audio (WAV, or extracted from a video next to the CSV)  [ ] Overwrite WAV
#   [ Import Animation ]
#
# 원본과 다른 점
#   - UI 문자열 · 로그가 전부 영어. 로그는 창의 공용 로그창(log 콜백)으로 간다.
#   - Node 콤보가 블렌드셰이프만이 아니라 **ARKit 이름 어트리뷰트를 가진 아무 노드**를 담는다
#     (core.csv_ops.list_candidate_nodes). `Selected` 로 씬에서 고른 노드를 직접 넣을 수도 있다.
#     항목 글자에 (n ARKit) 점수가 붙는다. 기본 선택은 점수가 가장 높은 노드.
#   - 로직은 core/csv_ops.py (UI 비의존).

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
    QComboBox,
    QSpinBox,
    QCheckBox,
    QFileDialog,
    Qt,
)

import maya.cmds as cmds

from tools.A00480_FileTool.app.core import csv_ops


class CsvImportPage(QWidget):
    """Import > CSV : ARKit 페이셜 CSV 를 노드의 키프레임으로."""

    def __init__(self, log=None, parent=None):
        super(CsvImportPage, self).__init__(parent)
        self._log_callback = log
        self._nodes = []          # 콤보 항목 순서의 노드 이름
        self.build_ui()

    # ------------------------------------------------------------------ UI

    def build_ui(self):
        layout = QVBoxLayout(self)

        box = QGroupBox("ARKit Facial CSV")
        grid = QGridLayout(box)

        # CSV 파일
        grid.addWidget(QLabel("CSV File"), 0, 0)
        self.le_csv = QLineEdit()
        self.le_csv.setPlaceholderText("CSV exported by Live Link Face (ARKit blend shapes)")
        self.le_csv.setToolTip(
            "A CSV whose header holds the ARKit blend shape names (one column each).\n"
            "Columns are matched to the node's attributes by name, case-insensitive;\n"
            "Timecode / BlendShapeCount and unmatched columns are skipped.")
        grid.addWidget(self.le_csv, 0, 1)
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.on_browse)
        grid.addWidget(btn_browse, 0, 2)

        # 노드
        grid.addWidget(QLabel("Node"), 1, 0)
        self.cmb_node = QComboBox()
        self.cmb_node.setToolTip(
            "The node that receives the keys : a blendShape (weight aliases) or ANY node\n"
            "with attributes named like the CSV columns (e.g. a facial control with the\n"
            "52 ARKit attributes). '(n ARKit)' = how many of the 52 names the node has.\n"
            "Detect lists every blendShape and every node with ARKit attributes;\n"
            "Selected adds the node selected in the scene.")
        grid.addWidget(self.cmb_node, 1, 1)
        node_btns = QHBoxLayout()
        btn_detect = QPushButton("Detect")
        btn_detect.setToolTip("Scan the scene for blendShapes and nodes with ARKit attributes,\n"
                              "and pick the one with the most ARKit names.")
        btn_detect.clicked.connect(self.on_detect)
        node_btns.addWidget(btn_detect)
        btn_selected = QPushButton("Selected")
        btn_selected.setToolTip("Use the node selected in the scene (added to the list).")
        btn_selected.clicked.connect(self.on_use_selected)
        node_btns.addWidget(btn_selected)
        grid.addLayout(node_btns, 1, 2)

        # 시작 프레임 · FPS
        grid.addWidget(QLabel("Start Frame"), 2, 0)
        fps_row = QHBoxLayout()
        self.spn_start = QSpinBox()
        self.spn_start.setRange(-100000, 100000)
        self.spn_start.setValue(1)
        self.spn_start.setToolTip("Frame of the first CSV row. The audio starts here too.")
        fps_row.addWidget(self.spn_start)
        fps_row.addSpacing(16)
        fps_row.addWidget(QLabel("FPS   Recorded"))
        self.spn_source_fps = QSpinBox()
        self.spn_source_fps.setRange(1, 240)
        self.spn_source_fps.setValue(60)
        self.spn_source_fps.setToolTip("FPS the CSV was recorded at (Live Link Face : 60).")
        fps_row.addWidget(self.spn_source_fps)
        fps_row.addWidget(QLabel("Output"))
        self.cmb_target_fps = QComboBox()
        for fps in csv_ops.TARGET_FPS_CHOICES:
            self.cmb_target_fps.addItem(str(fps))
        self.cmb_target_fps.setToolTip(
            "FPS of the keys. The scene FPS is set to this value, and rows are\n"
            "downsampled by round(Recorded / Output) - 60 -> 30 keeps every 2nd row.")
        fps_row.addWidget(self.cmb_target_fps)
        fps_row.addStretch(1)
        grid.addLayout(fps_row, 2, 1, 1, 2)

        # 오디오
        grid.addWidget(QLabel("Audio"), 3, 0)
        audio_row = QHBoxLayout()
        self.chk_audio = QCheckBox("Import audio")
        self.chk_audio.setChecked(True)
        self.chk_audio.setToolTip(
            "Import the WAV with the same name as the CSV ('_raw' is ignored) as a scene\n"
            "sound. Without a WAV, extract it from a video with the same name (MOV / MP4 ...)\n"
            "using ffmpeg from PATH.")
        audio_row.addWidget(self.chk_audio)
        self.chk_overwrite_wav = QCheckBox("Overwrite WAV")
        self.chk_overwrite_wav.setToolTip("Extract again even if the WAV already exists.")
        audio_row.addWidget(self.chk_overwrite_wav)
        audio_row.addStretch(1)
        grid.addLayout(audio_row, 3, 1, 1, 2)

        grid.setColumnStretch(1, 1)
        layout.addWidget(box)

        self.btn_import = QPushButton("Import Animation")
        self.btn_import.setMinimumHeight(32)
        self.btn_import.setToolTip(
            "Key every matched attribute of the node from the CSV rows, extend the\n"
            "timeline to the imported range and import the audio. One undo step.")
        self.btn_import.clicked.connect(self.on_import)
        layout.addWidget(self.btn_import)
        layout.addStretch(1)

    # ------------------------------------------------------------- nodes

    def _set_nodes(self, nodes, current=None):
        """콤보를 채운다. current 가 없으면 점수가 가장 높은 노드를 고른다."""
        self._nodes = list(nodes)
        self.cmb_node.blockSignals(True)
        self.cmb_node.clear()
        for node in self._nodes:
            score = csv_ops.score_node(node)
            kind = "blendShape" if csv_ops.is_blendshape(node) else cmds.nodeType(node)
            self.cmb_node.addItem("{0}   ({1} ARKit, {2})".format(node, score, kind))
        self.cmb_node.blockSignals(False)
        if not self._nodes:
            return
        if current is None:
            current = csv_ops.detect_best_node(self._nodes) or self._nodes[0]
        if current in self._nodes:
            self.cmb_node.setCurrentIndex(self._nodes.index(current))

    def current_node(self):
        index = self.cmb_node.currentIndex()
        if 0 <= index < len(self._nodes):
            return self._nodes[index]
        return ""

    def on_detect(self):
        nodes = csv_ops.list_candidate_nodes()
        self._set_nodes(nodes)
        if not nodes:
            self._log("[WARN] CSV : no blendShape and no node with ARKit attributes in the scene.")
            return
        best = self.current_node()
        self._log("CSV : {0} candidate node(s), picked '{1}' ({2} ARKit)".format(
            len(nodes), best, csv_ops.score_node(best)))

    def on_use_selected(self):
        selected = cmds.ls(selection=True) or []
        if not selected:
            self._log("[WARN] CSV : select a node in the scene first.")
            return
        node = selected[0]
        nodes = list(self._nodes)
        if node not in nodes:
            nodes.append(node)
        self._set_nodes(nodes, current=node)
        self._log("CSV : node '{0}' ({1} ARKit, {2} attribute(s))".format(
            node, csv_ops.score_node(node), len(csv_ops.node_targets(node))))

    # ------------------------------------------------------------ actions

    def on_browse(self):
        start_dir = os.path.dirname(self.le_csv.text().strip()) or ""
        path, _filter = QFileDialog.getOpenFileName(
            self, "Select ARKit CSV", start_dir, "CSV Files (*.csv)")
        if path:
            self.le_csv.setText(path)

    def on_import(self):
        csv_path = self.le_csv.text().strip()
        node = self.current_node()
        if not csv_path:
            self._log("[ERR] CSV : choose a CSV file.")
            return
        if not node:
            self._log("[ERR] CSV : choose a node (Detect or Selected).")
            return

        self._log("--- CSV Import : {0} ---".format(os.path.basename(csv_path)))
        try:
            summary = csv_ops.import_facial(
                csv_path, node,
                start_frame=self.spn_start.value(),
                source_fps=self.spn_source_fps.value(),
                target_fps=int(self.cmb_target_fps.currentText()),
                do_audio=self.chk_audio.isChecked(),
                overwrite_wav=self.chk_overwrite_wav.isChecked(),
                log=self._log)
        except Exception as e:
            self._log("[ERR] CSV import failed : {0}".format(e))
            cmds.warning(str(e))
            return
        for line in csv_ops.summary_lines(summary):
            self._log(line)

    # ------------------------------------------------------------- helper

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
