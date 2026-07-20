# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-20
# A00380_MeshTool - Qt UI
#
# Peak 탭: 선택한 메시/버텍스를 자기 노말 방향으로 팽창(+)·수축(-) 시킨다.
# 후디니 peak 노드와 같은 개념이고, 마야 기본(Move 툴 axis=normal)보다 훨씬 빠르다.
#
# 흐름: Load Selection 으로 스냅샷 → 슬라이더를 끌면 실시간 미리보기(API 직접 쓰기)
#       → Apply 로 확정(tweak 구간 setAttr, Ctrl+Z 한 번에 되돌아감).

import time

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00380_MeshTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00380_MeshTool.app.core import peak_manager as peak_mgr


WINDOW_OBJECT_NAME = "JUN_A00380_MeshTool_window"

# 슬라이더는 정수만 다루므로 -SLIDER_TICKS ~ +SLIDER_TICKS 를 -range ~ +range 로 매핑한다.
SLIDER_TICKS = 1000

_WARN_COLOR = "#ffb454"
_OK_COLOR = "#7ddc7d"

# 미리보기 한 번이 이 시간을 넘으면 "무거운 메시"로 보고 드래그 중 갱신을 솎아낸다.
_HEAVY_SEC = 0.08


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Mesh Tool v{0}".format(VERSION)
        self.resize(380, 520)

        self.session = None      # peak_mgr.PeakSession
        self._syncing = False    # 슬라이더 <-> 스핀박스 상호 갱신 재귀 방지
        self._script_job = None
        self._last_preview_sec = 0.0   # 직전 미리보기 소요 시간 (스로틀 판단용)
        self._last_preview_at = 0.0

        self.build_ui()
        self.update_state()

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

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_peak_tab(), "Peak")
        root.addWidget(self.tabs, 1)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(110)
        root.addWidget(self.te_log)

        self.log("Mesh Tool v{0} ({1}) ready. Select a mesh or vertices, then "
                 "click 'Load Selection'.".format(VERSION, LAST_UPDATE))

    def build_peak_tab(self):

        page = QWidget()
        lay = QVBoxLayout(page)

        # ---- 대상 -------------------------------------------------
        box_target = QGroupBox("Target")
        v = QVBoxLayout(box_target)

        self.lb_target = QLabel("Nothing loaded.")
        self.lb_target.setWordWrap(True)
        v.addWidget(self.lb_target)

        row = QHBoxLayout()
        self.btn_load = QPushButton("Load Selection")
        self.btn_load.setMinimumHeight(30)
        # clicked 는 checked(bool) 를 넘기므로 silent 인자로 새지 않게 감싼다.
        self.btn_load.clicked.connect(lambda: self.on_load())
        row.addWidget(self.btn_load, 2)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.on_clear)
        row.addWidget(self.btn_clear, 1)
        v.addLayout(row)

        self.chk_auto = QCheckBox("Auto load on selection change")
        self.chk_auto.setChecked(True)
        self.chk_auto.setToolTip(
            "Re-snapshot automatically whenever the scene selection changes.")
        self.chk_auto.toggled.connect(self.on_auto_toggled)
        v.addWidget(self.chk_auto)

        lay.addWidget(box_target)

        # ---- 옵션 -------------------------------------------------
        box_opt = QGroupBox("Options")
        vo = QVBoxLayout(box_opt)

        self.chk_angle = QCheckBox("Angle weighted normals")
        self.chk_angle.setChecked(True)
        self.chk_angle.setToolTip(
            "On: average face normals weighted by corner angle (smoother peak).\n"
            "Off: plain average.")
        vo.addWidget(self.chk_angle)

        self.chk_soft = QCheckBox("Respect soft selection")
        self.chk_soft.setChecked(True)
        self.chk_soft.setToolTip(
            "Use Maya's soft selection falloff as a per-vertex multiplier\n"
            "(only when soft select is enabled).")
        vo.addWidget(self.chk_soft)

        lay.addWidget(box_opt)

        # ---- 양(amount) -------------------------------------------
        box_amt = QGroupBox("Amount")
        va = QVBoxLayout(box_amt)

        row_r = QHBoxLayout()
        row_r.addWidget(QLabel("Range"))
        self.sp_range = QDoubleSpinBox()
        self.sp_range.setDecimals(3)
        self.sp_range.setRange(0.001, 10000.0)
        self.sp_range.setValue(1.0)
        self.sp_range.setToolTip(
            "Slider limit. Lower it for finer control (e.g. 0.05).")
        self.sp_range.valueChanged.connect(self.on_range_changed)
        row_r.addWidget(self.sp_range, 1)
        va.addLayout(row_r)

        self.sl_amount = QSlider(Qt.Horizontal)
        self.sl_amount.setRange(-SLIDER_TICKS, SLIDER_TICKS)
        self.sl_amount.setValue(0)
        self.sl_amount.valueChanged.connect(self.on_slider_changed)
        # 드래그 중 갱신을 솎아냈을 수 있으므로, 손을 떼면 마지막 값으로 확실히 맞춘다.
        self.sl_amount.sliderReleased.connect(self.apply_preview)
        va.addWidget(self.sl_amount)

        row_a = QHBoxLayout()
        row_a.addWidget(QLabel("Value"))
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setDecimals(4)
        self.sp_amount.setRange(-10000.0, 10000.0)
        self.sp_amount.setSingleStep(0.01)
        self.sp_amount.setValue(0.0)
        self.sp_amount.valueChanged.connect(self.on_spin_changed)
        row_a.addWidget(self.sp_amount, 1)

        btn_zero = QPushButton("0")
        btn_zero.setMaximumWidth(30)
        btn_zero.setToolTip("Set amount back to zero.")
        btn_zero.clicked.connect(lambda: self.set_amount(0.0))
        row_a.addWidget(btn_zero)
        va.addLayout(row_a)

        # 미세 조정 nudge
        row_n = QHBoxLayout()
        row_n.addWidget(QLabel("Step"))
        self.sp_step = QDoubleSpinBox()
        self.sp_step.setDecimals(4)
        self.sp_step.setRange(0.0001, 1000.0)
        self.sp_step.setSingleStep(0.001)
        self.sp_step.setValue(0.01)
        self.sp_step.setToolTip("Amount added/removed by the - / + buttons.")
        row_n.addWidget(self.sp_step, 1)

        self.btn_minus = QPushButton("-")
        self.btn_minus.setMaximumWidth(34)
        self.btn_minus.setToolTip("Shrink by one step (preview).")
        self.btn_minus.clicked.connect(lambda: self.nudge(-1))
        row_n.addWidget(self.btn_minus)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setMaximumWidth(34)
        self.btn_plus.setToolTip("Inflate by one step (preview).")
        self.btn_plus.clicked.connect(lambda: self.nudge(1))
        row_n.addWidget(self.btn_plus)
        va.addLayout(row_n)

        lay.addWidget(box_amt)

        # ---- 확정 -------------------------------------------------
        row_apply = QHBoxLayout()

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.setToolTip("Commit the preview (undoable with one Ctrl+Z).")
        self.btn_apply.clicked.connect(self.on_apply)
        row_apply.addWidget(self.btn_apply, 2)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setMinimumHeight(38)
        self.btn_reset.setToolTip("Discard the preview and go back to the snapshot.")
        self.btn_reset.clicked.connect(self.on_reset)
        row_apply.addWidget(self.btn_reset, 1)

        lay.addLayout(row_apply)
        lay.addStretch(1)

        return page

    # ==============================================================
    # 상태
    # ==============================================================

    def has_session(self):
        return self.session is not None

    def update_state(self):

        on = self.has_session()

        for w in (self.sl_amount, self.sp_amount, self.sp_step, self.sp_range,
                  self.btn_minus, self.btn_plus, self.btn_apply, self.btn_reset):
            w.setEnabled(on)

        if not on:
            self.lb_target.setText("Nothing loaded.")
            return

        names = self.session.mesh_names()
        head = names[0] if len(names) == 1 else "{0} meshes".format(len(names))

        text = "{0}  |  {1} vertice(s)".format(head, self.session.vertex_count)
        if self.session.is_soft:
            text += "  |  soft selection"

        self.lb_target.setText(text)

    def amount(self):
        return self.sp_amount.value()

    def set_amount(self, value):
        """슬라이더/스핀박스를 함께 맞추고 미리보기를 갱신한다."""

        rng = self.sp_range.value()
        value = max(-rng, min(rng, value))

        self._syncing = True
        self.sp_amount.setValue(value)
        self.sl_amount.setValue(int(round(value / rng * SLIDER_TICKS)))
        self._syncing = False

        self.apply_preview()

    def apply_preview(self, throttle=False):
        """미리보기 갱신.

        throttle=True 는 슬라이더를 잡고 끄는 중이라는 뜻이다. 아주 무거운 메시에서
        모든 슬라이더 눈금마다 갱신하면 UI 가 밀리므로, 직전 미리보기가 오래
        걸렸다면 그 시간만큼 지나기 전엔 건너뛴다. 손을 떼면 항상 마지막 값으로
        한 번 더 갱신하므로 결과가 어긋나지는 않는다.
        """

        if not self.has_session():
            return

        if throttle and self._last_preview_sec > _HEAVY_SEC:
            if (time.time() - self._last_preview_at) < self._last_preview_sec:
                return

        start = time.time()

        try:
            self.session.preview(self.amount())
        except Exception as e:
            self.log("Preview failed: {0}".format(e), warn=True)
            return

        self._last_preview_sec = time.time() - start
        self._last_preview_at = time.time()

    # ==============================================================
    # 이벤트
    # ==============================================================

    def on_slider_changed(self, tick):

        if self._syncing:
            return

        value = tick / float(SLIDER_TICKS) * self.sp_range.value()

        self._syncing = True
        self.sp_amount.setValue(value)
        self._syncing = False

        # 슬라이더를 잡고 있는 동안만 솎아낸다 (손을 떼면 sliderReleased 가 마무리).
        self.apply_preview(throttle=self.sl_amount.isSliderDown())

    def on_spin_changed(self, value):

        if self._syncing:
            return

        rng = self.sp_range.value()

        # 스핀박스로 슬라이더 범위를 넘겨 입력하면 범위를 늘려 준다.
        if abs(value) > rng:
            self._syncing = True
            self.sp_range.setValue(abs(value))
            self._syncing = False
            rng = abs(value)

        self._syncing = True
        self.sl_amount.setValue(int(round(value / rng * SLIDER_TICKS)))
        self._syncing = False

        self.apply_preview()

    def on_range_changed(self, rng):

        if self._syncing:
            return

        # 범위가 바뀌어도 현재 값은 유지되도록 슬라이더 위치만 다시 계산한다.
        self.set_amount(self.amount())

    def nudge(self, sign):
        self.set_amount(self.amount() + sign * self.sp_step.value())

    # ---- 로드 / 클리어 --------------------------------------------

    def on_load(self, silent=False):

        # 확정하지 않은 미리보기가 있으면 먼저 되돌린다.
        self.discard_preview()

        try:
            session = peak_mgr.PeakSession.from_selection(
                angle_weighted=self.chk_angle.isChecked(),
                soft_select=self.chk_soft.isChecked())
        except Exception as e:
            self.session = None
            self.update_state()
            self.log("Load failed: {0}".format(e), warn=True)
            return

        self.session = session

        self._syncing = True
        self.sp_amount.setValue(0.0)
        self.sl_amount.setValue(0)
        self._syncing = False

        self.update_state()

        if session is None:
            if not silent:
                self.log("Nothing to load. Select a mesh or its vertices.", warn=True)
            return

        msg = "Loaded {0} vertice(s) on {1}.".format(
            session.vertex_count, ", ".join(session.mesh_names()))
        if session.is_soft:
            msg += " (soft selection falloff active)"

        if not silent:
            self.log(msg)

    def on_clear(self):
        self.discard_preview()
        self.session = None
        self.update_state()
        self.log("Cleared.")

    def discard_preview(self):
        """미리보기를 스냅샷 상태로 되돌린다 (확정 안 함)."""

        if not self.has_session():
            return

        try:
            self.session.restore()
        except Exception:
            pass

    # ---- 확정 / 리셋 ----------------------------------------------

    def on_apply(self):

        if not self.has_session():
            self.log("Nothing loaded.", warn=True)
            return

        value = self.amount()

        if abs(value) < 1e-9:
            self.log("Amount is 0 - nothing to apply.", warn=True)
            return

        try:
            with undo_chunk():
                moved = self.session.commit(value)
        except Exception as e:
            self.log("Apply failed: {0}".format(e), warn=True)
            return

        self._syncing = True
        self.sp_amount.setValue(0.0)
        self.sl_amount.setValue(0)
        self._syncing = False

        verb = "Inflated" if value > 0 else "Shrunk"
        self.log("{0} {1} vertice(s) by {2:.4f}.".format(verb, moved, abs(value)),
                 ok=True)

    def on_reset(self):

        if not self.has_session():
            return

        self.set_amount(0.0)
        self.log("Preview reset.")

    # ---- 자동 로드 -------------------------------------------------

    def on_auto_toggled(self, on):
        if on:
            self.start_script_job()
        else:
            self.kill_script_job()

    def start_script_job(self):

        if self._script_job is not None:
            return

        try:
            self._script_job = cmds.scriptJob(
                event=["SelectionChanged", self.on_selection_changed],
                protected=False)
        except Exception as e:
            self.log("Auto load unavailable: {0}".format(e), warn=True)

    def kill_script_job(self):

        if self._script_job is None:
            return

        try:
            if cmds.scriptJob(exists=self._script_job):
                cmds.scriptJob(kill=self._script_job, force=True)
        except Exception:
            pass

        self._script_job = None

    def on_selection_changed(self):

        if not self.chk_auto.isChecked():
            return

        try:
            self.on_load(silent=True)
        except Exception:
            pass

    # ==============================================================
    # show / close
    # ==============================================================

    def showEvent(self, event):
        super(MainWindow, self).showEvent(event)
        if self.chk_auto.isChecked():
            self.start_script_job()

    def closeEvent(self, event):
        # 확정하지 않은 미리보기를 남긴 채 닫으면 씬이 어긋난 상태로 보인다.
        self.discard_preview()
        self.kill_script_job()
        super(MainWindow, self).closeEvent(event)

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def log(self, text, warn=False, ok=False):

        if warn:
            color = _WARN_COLOR
        elif ok:
            color = _OK_COLOR
        else:
            color = None

        if color:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(color, self._esc(text)))
        else:
            self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Mesh Tool\nv{0}  ({1})\n\n"
            "Peak: inflate / shrink a mesh along its vertex normals,\n"
            "like Houdini's peak node. Drag the slider for a live preview,\n"
            "then Apply to commit it as a single undo step.\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
