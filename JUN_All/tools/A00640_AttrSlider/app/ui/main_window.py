# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00640_AttrSlider - Qt UI (in-Maya)
#
# 고른 노드마다 섹션 하나, 그 아래 채널박스 어트리뷰트마다 이름 · 슬라이더 · 숫자 칸 한 줄.
# blendShape 는 envelope + 타겟 웨이트. FBXASC 이름(일본어 등)은 풀어서 보인다(마야 채널박스는 못 그린다).
# 계획서 docs/plans/A00640_AttrSlider_plan.md. 모든 UI 문자열/로그는 영어.

import maya.cmds as cmds

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QPushButton,
    QToolButton,
    QSlider,
    QFrame,
    QDoubleSpinBox,
    QLineEdit,
    QScrollArea,
    QMenu,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QApplication,
    QAction,
    QActionGroup,
    QTimer,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_sliderStyle_qt_v01 import JUN_mod_sliderStyle_qt_v01
from Framework.qt.pin_style import apply_pin_style
from Framework.core.maya_undo import undo_chunk

from tools.A00640_AttrSlider.app.config.version import VERSION, LAST_UPDATE
from tools.A00640_AttrSlider.app.core import attr_rows as AR
from tools.A00640_AttrSlider.app.core import ranges as RG


WINDOW_OBJECT_NAME = "JUN_A00640_AttrSlider_window"

SLIDER_STEPS = 1000
SPIN_LIMIT = 1e6
LABEL_WIDTH = 150

OPTVAR_RANGES = "A00640_userRanges"
OPTVAR_NAMES = "A00640_nameMode"
OPTVAR_SHAPES = "A00640_showShapes"
OPTVAR_BLENDSHAPES = "A00640_showBlendShapes"
OPTVAR_AUTOKEY = "A00640_autoKey"

# 마야 채널박스 색을 따른다
STATE_COLORS = {
    AR.ST_KEYED: "#dd727a",      # 키 - 분홍
    AR.ST_DRIVEN: "#e5d26e",     # 연결 - 노랑
    AR.ST_LOCKED: "#5c6874",     # 잠김 - 회색 파랑
}
STATE_TEXT = {AR.ST_KEYED: "Keyed", AR.ST_DRIVEN: "Driven", AR.ST_LOCKED: "Locked", AR.ST_FREE: ""}
ROW_BG = "#2b2b2b"
ROW_BG_ALT = "#30343a"
ROW_OBJECT = "attrSliderRow"
LABEL_OBJECT = "attrSliderLabel"
SECTION_STYLE = "QToolButton { font-weight: bold; text-align: left; border: none; padding: 3px 2px; }"


# ------------------------------------------------------------------ optionVar

def _opt_get(key, default):
    try:
        if cmds.optionVar(exists=key):
            return cmds.optionVar(query=key)
    except Exception:  # noqa: BLE001
        pass
    return default


def _opt_set(key, value):
    try:
        if isinstance(value, str):
            cmds.optionVar(stringValue=(key, value))
        else:
            cmds.optionVar(intValue=(key, int(value)))
    except Exception:  # noqa: BLE001
        pass


# ------------------------------------------------------------------ Set Range 대화 상자

class RangeDialog(QDialog):
    """사용자 범위 Min / Max. 어트리뷰트 이름 기준으로 저장된다."""

    def __init__(self, attr_label, lo, hi, hard_min=None, hard_max=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Range")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Slider range for '{0}'\n(saved by attribute name - every node with it uses it)"
                                .format(attr_label)))
        grid = QGridLayout()
        self.sb_min = QDoubleSpinBox()
        self.sb_max = QDoubleSpinBox()
        for sb, value in ((self.sb_min, lo), (self.sb_max, hi)):
            sb.setDecimals(3)
            sb.setRange(hard_min if hard_min is not None else -SPIN_LIMIT,
                        hard_max if hard_max is not None else SPIN_LIMIT)
            sb.setValue(value)
        grid.addWidget(QLabel("Min"), 0, 0)
        grid.addWidget(self.sb_min, 0, 1)
        grid.addWidget(QLabel("Max"), 1, 0)
        grid.addWidget(self.sb_max, 1, 1)
        layout.addLayout(grid)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return self.sb_min.value(), self.sb_max.value()


# ------------------------------------------------------------------ 행 위젯

class RowWidget(QFrame):
    """어트리뷰트 한 줄. 값을 쓰는 일은 창(owner)에 맡긴다."""

    def __init__(self, owner, row, alt):
        super().__init__()
        self.owner = owner
        self.row = row
        self.alt = alt
        self.lo = 0.0
        self.hi = 1.0
        self.range_source = ""
        self.slider = None
        self.spin = None
        self.check = None
        self.combo = None
        self.setObjectName(ROW_OBJECT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(6)
        self.label = QLabel()
        self.label.setObjectName(LABEL_OBJECT)
        self.label.setFixedWidth(LABEL_WIDTH)
        layout.addWidget(self.label)

        value = AR.get_value(row)
        if row.kind in (AR.KIND_FLOAT, AR.KIND_INT):
            self.slider = QSlider(Qt.Horizontal)
            self.slider.setRange(0, SLIDER_STEPS)
            self.slider.setMinimumWidth(120)
            self.spin = QDoubleSpinBox()
            self.spin.setDecimals(0 if row.kind == AR.KIND_INT else 3)
            self.spin.setRange(row.hard_min if row.hard_min is not None else -SPIN_LIMIT,
                               row.hard_max if row.hard_max is not None else SPIN_LIMIT)
            self.spin.setSingleStep(1.0 if row.kind == AR.KIND_INT else 0.1)
            # 칠 때마다 확정하면 뒷자리를 못 친다 - Enter / 포커스 아웃에서 확정
            self.spin.setKeyboardTracking(False)
            self.spin.setFixedWidth(84)
            layout.addWidget(self.slider, stretch=1)
            layout.addWidget(self.spin)
            self.slider.sliderPressed.connect(self._on_press)
            self.slider.sliderReleased.connect(self._on_release)
            self.slider.valueChanged.connect(self._on_slider)
            self.spin.valueChanged.connect(self._on_spin)
            self.reset_range(value)
        elif row.kind == AR.KIND_BOOL:
            self.check = QCheckBox()
            layout.addWidget(self.check)
            layout.addStretch(1)
            self.check.toggled.connect(self._on_check)
        else:
            self.combo = QComboBox()
            for (name, num), (raw, _n) in zip(row.items, row.raw_items):
                self.combo.addItem(name, num)
                if name != raw:
                    self.combo.setItemData(self.combo.count() - 1, raw, Qt.ToolTipRole)
            layout.addWidget(self.combo, stretch=1)
            self.combo.activated.connect(self._on_combo)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.update_label()
        self.show_value(value)
        self.update_state()

    # ---------------------------------------------------------- 범위

    def reset_range(self, value=None):
        r = self.row
        if value is None:
            value = AR.get_value(r) or 0.0
        user = self.owner.user_ranges.get(r.range_key())
        self.lo, self.hi, self.range_source = RG.resolve_range(
            value, r.hard_min, r.hard_max, r.soft_min, r.soft_max,
            is_angle=r.is_angle, is_int=r.kind == AR.KIND_INT, user=user)
        self.show_value(value)

    def widen_to(self, value):
        lo, hi = RG.widen(self.lo, self.hi, value, self.row.hard_min, self.row.hard_max)
        if (lo, hi) != (self.lo, self.hi):
            self.lo, self.hi = lo, hi
            self.range_source = RG.SRC_AUTO
            self.update_tooltip()

    def _to_steps(self, value):
        t = (float(value) - self.lo) / (self.hi - self.lo)
        return int(round(min(max(t, 0.0), 1.0) * SLIDER_STEPS))

    def _from_steps(self, steps):
        return self.lo + (self.hi - self.lo) * steps / float(SLIDER_STEPS)

    # ---------------------------------------------------------- 표시

    def update_label(self):
        text = self.row.label(self.owner.name_mode)
        self.label.setText(text)
        self.update_tooltip()

    def update_tooltip(self):
        r = self.row
        lines = ["Maya name: {0}".format(r.raw_name), "Plug: {0}".format(r.plug)]
        if self.slider is not None:
            lines.append("Slider range: {0:g} ~ {1:g} ({2})".format(self.lo, self.hi, self.range_source))
        if r.hard_min is not None or r.hard_max is not None:
            lines.append("Hard limits: {0} ~ {1}".format(
                "-" if r.hard_min is None else "{0:g}".format(r.hard_min),
                "-" if r.hard_max is None else "{0:g}".format(r.hard_max)))
        if r.state != AR.ST_FREE:
            lines.append("{0}{1}".format(STATE_TEXT[r.state], " by " + r.source if r.source else ""))
        if r.state == AR.ST_KEYED:
            lines.append("Changing the time puts the animation value back - turn on Auto Key to keep it.")
        lines.append("Right-click: Set Range / Reset Range / Set Key")
        self.label.setToolTip("\n".join(lines))

    def show_value(self, value):
        """씬 값을 위젯에 (신호 없이)."""
        if value is None:
            return
        if self.slider is not None:
            if not self.slider.isSliderDown():
                self.slider.blockSignals(True)
                self.slider.setValue(self._to_steps(value))
                self.slider.blockSignals(False)
            self.spin.blockSignals(True)
            self.spin.setValue(float(value))
            self.spin.blockSignals(False)
        elif self.check is not None:
            self.check.blockSignals(True)
            self.check.setChecked(bool(value))
            self.check.blockSignals(False)
        elif self.combo is not None:
            index = self.combo.findData(int(value))
            self.combo.blockSignals(True)
            self.combo.setCurrentIndex(index)
            self.combo.blockSignals(False)

    def update_state(self):
        r = self.row
        color = STATE_COLORS.get(r.state)
        style = "QFrame#{0} {{ background-color: {1}; border-radius: 3px; }}".format(
            ROW_OBJECT, ROW_BG_ALT if self.alt else ROW_BG)
        style += "QLabel#{0} {{ background: transparent; {1} }}".format(
            LABEL_OBJECT, "color: {0};".format(color) if color else "")
        self.setStyleSheet(style)
        editable = r.editable
        for w in (self.slider, self.spin, self.check, self.combo):
            if w is not None:
                w.setEnabled(editable)
        self.update_tooltip()

    def refresh(self):
        self.row.refresh_state()
        self.update_state()
        self.show_value(AR.get_value(self.row))

    def matches(self, text):
        if not text:
            return True
        r = self.row
        hay = " ".join((r.nice_name, r.long_name, r.raw_name)).lower()
        return text in hay

    # ---------------------------------------------------------- 입력

    def _on_press(self):
        self.owner.begin_drag(self)

    def _on_release(self):
        self.owner.end_drag(self)

    def _on_slider(self, steps):
        value = self._from_steps(steps)
        if self.row.kind == AR.KIND_INT:
            value = round(value)
        written = self.owner.write(self, value, dragging=self.slider.isSliderDown())
        if written is not None:
            self.spin.blockSignals(True)
            self.spin.setValue(float(written))
            self.spin.blockSignals(False)

    def _on_spin(self, value):
        written = self.owner.write(self, value)
        if written is not None:
            self.widen_to(written)
            self.show_value(written)

    def _on_check(self, checked):
        self.owner.write(self, checked)

    def _on_combo(self, index):
        self.owner.write(self, self.combo.itemData(index))

    def _menu(self, pos):
        menu = QMenu(self)
        if self.slider is not None:
            menu.addAction("Set Range...").triggered.connect(lambda: self.owner.edit_range(self))
            act = menu.addAction("Reset Range")
            act.setEnabled(self.owner.user_ranges.get(self.row.range_key()) is not None)
            act.triggered.connect(lambda: self.owner.clear_range(self))
            menu.addSeparator()
        act = menu.addAction("Set Key")
        act.setEnabled(self.row.editable)
        act.triggered.connect(lambda: self.owner.key_row(self))
        menu.addSeparator()
        menu.addAction("Copy Name").triggered.connect(
            lambda: QApplication.clipboard().setText(self.row.label(self.owner.name_mode)))
        menu.addAction("Copy Maya Name").triggered.connect(
            lambda: QApplication.clipboard().setText(self.row.plug))
        menu.exec_(self.mapToGlobal(pos))


# ------------------------------------------------------------------ 섹션 위젯

class SectionWidget(QWidget):

    def __init__(self, owner, section):
        super().__init__()
        self.owner = owner
        self.section = section
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 4)
        layout.setSpacing(1)

        self.header = QToolButton()
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.DownArrow)
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.setStyleSheet(SECTION_STYLE)
        kind = {AR.SEC_SHAPE: "shape", AR.SEC_BLENDSHAPE: "blendShape"}.get(section.kind, section.node_type)
        self.header.setText("{0}   ({1})".format(section.label, kind))
        self.header.setToolTip("{0}\nClick to fold. Right-click: Select / Copy".format(section.node))
        self.header.toggled.connect(self._fold)
        self.header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header.customContextMenuRequested.connect(self._menu)
        layout.addWidget(self.header)

        self.rows = []
        for i, row in enumerate(section.rows):
            w = RowWidget(owner, row, alt=i % 2 == 1)
            self.rows.append(w)
            layout.addWidget(w)

    def _fold(self, opened):
        self.header.setArrowType(Qt.DownArrow if opened else Qt.RightArrow)
        self.owner.apply_filter()

    def is_open(self):
        return self.header.isChecked()

    def _menu(self, pos):
        menu = QMenu(self)
        menu.addAction("Select Node").triggered.connect(lambda: cmds.select(self.section.node, replace=True))
        menu.addAction("Copy Name").triggered.connect(
            lambda: QApplication.clipboard().setText(self.section.label))
        menu.addAction("Copy Maya Name").triggered.connect(
            lambda: QApplication.clipboard().setText(self.section.raw_label))
        menu.exec_(self.header.mapToGlobal(pos))


# ------------------------------------------------------------------ 창

class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("Attr Slider v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(460, 560)

        self.user_ranges = RG.UserRanges(load=lambda: _opt_get(OPTVAR_RANGES, ""),
                                         save=lambda text: _opt_set(OPTVAR_RANGES, text))
        self.name_mode = _opt_get(OPTVAR_NAMES, AR.NAMES_NICE)
        if self.name_mode not in (AR.NAMES_NICE, AR.NAMES_LONG):
            self.name_mode = AR.NAMES_NICE
        self.sections = []           # [SectionWidget]
        self.nodes = []              # 지금 목록의 노드(고른 순서)
        self._jobs = []
        self._drag_row = None
        self._rebuild_timer = QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(30)
        self._rebuild_timer.timeout.connect(self.rebuild_from_selection)

        self.build_ui()
        self.slider_style = JUN_mod_sliderStyle_qt_v01(self)
        self.rebuild_from_selection()
        self._start_jobs()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        view = self.menu_bar.addMenu("View")
        group = QActionGroup(self)
        self.act_nice = QAction("Nice Names", self, checkable=True)
        self.act_long = QAction("Long Names", self, checkable=True)
        for act, mode in ((self.act_nice, AR.NAMES_NICE), (self.act_long, AR.NAMES_LONG)):
            group.addAction(act)
            view.addAction(act)
            act.setChecked(self.name_mode == mode)
            act.triggered.connect(lambda _c=False, m=mode: self.set_name_mode(m))
        view.addSeparator()
        self.act_shapes = QAction("Shapes", self, checkable=True)
        self.act_shapes.setChecked(bool(_opt_get(OPTVAR_SHAPES, 1)))
        self.act_shapes.setToolTip("Also list the shape node attributes (like SHAPES in the Channel Box).")
        self.act_shapes.toggled.connect(lambda on: self._toggle_opt(OPTVAR_SHAPES, on))
        view.addAction(self.act_shapes)
        self.act_bs = QAction("Blend Shapes of Selection", self, checkable=True)
        self.act_bs.setChecked(bool(_opt_get(OPTVAR_BLENDSHAPES, 1)))
        self.act_bs.setToolTip("Also list the blendShape nodes in the history of the selected meshes\n"
                               "(like INPUTS in the Channel Box).")
        self.act_bs.toggled.connect(lambda on: self._toggle_opt(OPTVAR_BLENDSHAPES, on))
        view.addAction(self.act_bs)
        view.addSeparator()
        view.addAction("Expand All").triggered.connect(lambda: self.fold_all(True))
        view.addAction("Collapse All").triggered.connect(lambda: self.fold_all(False))
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

        bar = QHBoxLayout()
        self.btn_lock = QPushButton("Lock List")
        self.btn_lock.setCheckable(True)
        self.btn_lock.setToolTip("Stop following the Maya selection - keep the current list.")
        self.btn_lock.toggled.connect(self.set_locked)
        apply_pin_style(self.btn_lock)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip("Rebuild the list (from the selection, or the locked nodes).")
        self.btn_refresh.clicked.connect(self.refresh_list)
        self.chk_autokey = QCheckBox("Auto Key")
        self.chk_autokey.setToolTip("Set a key on the attribute after each change\n"
                                    "(a slider drag keys once, when released).")
        self.chk_autokey.setChecked(bool(_opt_get(OPTVAR_AUTOKEY, 0)))
        self.chk_autokey.toggled.connect(lambda on: _opt_set(OPTVAR_AUTOKEY, on))
        bar.addWidget(self.btn_lock)
        bar.addWidget(self.btn_refresh)
        bar.addStretch(1)
        bar.addWidget(self.chk_autokey)
        main.addLayout(bar)

        self.ed_filter = QLineEdit()
        self.ed_filter.setPlaceholderText("Filter attributes / nodes (decoded or Maya name)")
        self.ed_filter.setClearButtonEnabled(True)
        self.ed_filter.textChanged.connect(self.apply_filter)
        main.addWidget(self.ed_filter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(2)
        self.empty_label = QLabel("Select nodes in Maya.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.list_layout.addWidget(self.empty_label)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.container)
        main.addWidget(self.scroll, stretch=1)

        self.log_view = JUN_mod_log_qt_v01(window_title="Attr Slider - Log",
                                           object_name="JUN_A00640_AttrSlider_log_window")
        self.log_view.setMinimumHeight(90)
        main.addWidget(self.log_view)
        self.log_view.set_shrunk(True)

    def log(self, msg):
        self.log_view.log(msg)

    # ==================================================================
    # 목록
    # ==================================================================

    def rebuild_from_selection(self):
        if self.btn_lock.isChecked():
            return
        self.rebuild(AR.selected_nodes())

    def refresh_list(self):
        if self.btn_lock.isChecked():
            self.rebuild([n for n in self.nodes if cmds.objExists(n)])
        else:
            self.rebuild(AR.selected_nodes())

    def rebuild(self, nodes):
        """노드 목록으로 섹션 · 행을 다시 만든다. 접힘 상태와 스크롤 위치는 노드 이름으로 유지."""
        self._end_open_drag()
        folded = {s.section.node for s in self.sections if not s.is_open()}
        scroll = self.scroll.verticalScrollBar().value()
        for s in self.sections:
            s.setParent(None)
            s.deleteLater()
        self.sections = []
        self.nodes = list(nodes)
        try:
            sections, dropped = AR.build_sections(nodes, include_shapes=self.act_shapes.isChecked(),
                                                  include_blendshapes=self.act_bs.isChecked())
        except Exception as exc:  # noqa: BLE001
            self.log("[ERROR] List: {0}".format(exc))
            sections, dropped = [], 0
        if dropped:
            self.log("[WARN] {0} node(s) selected - showing the first {1}.".format(
                len(nodes), AR.MAX_NODES))
        for sec in sections:
            w = SectionWidget(self, sec)
            if sec.node in folded:
                w.header.setChecked(False)
            self.sections.append(w)
            self.list_layout.insertWidget(self.list_layout.count() - 1, w)
        self.empty_label.setVisible(not self.sections)
        self.empty_label.setText("Select nodes in Maya." if not nodes else "No attributes to show.")
        self.apply_filter()
        self.slider_style.apply()
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(scroll))

    def row_widgets(self):
        return [r for s in self.sections for r in s.rows]

    def apply_filter(self, *_args):
        text = self.ed_filter.text().strip().lower()
        for s in self.sections:
            sec_hit = bool(text) and (text in s.section.label.lower() or text in s.section.raw_label.lower())
            any_row = False
            for r in s.rows:
                hit = sec_hit or r.matches(text)
                any_row = any_row or hit
                r.setVisible(hit and s.is_open())
            s.setVisible(any_row)

    def fold_all(self, opened):
        for s in self.sections:
            s.header.setChecked(opened)

    def refresh_values(self):
        """시간 · undo 뒤 - 위젯은 그대로, 값과 상태만 다시 읽는다."""
        for r in self.row_widgets():
            if cmds.objExists(r.row.node):
                r.refresh()

    def set_name_mode(self, mode):
        self.name_mode = mode
        _opt_set(OPTVAR_NAMES, mode)
        for r in self.row_widgets():
            r.update_label()
        self.apply_filter()

    def _toggle_opt(self, key, on):
        _opt_set(key, on)
        self.refresh_list()

    def set_locked(self, locked):
        self.btn_lock.setText("List Locked" if locked else "Lock List")
        if not locked:
            self.rebuild_from_selection()

    # ==================================================================
    # 쓰기
    # ==================================================================

    def begin_drag(self, row_widget):
        """슬라이더를 누름 - 놓을 때까지 하나의 undo."""
        self._end_open_drag()
        cmds.undoInfo(openChunk=True, chunkName="A00640_drag")
        self._drag_row = row_widget

    def end_drag(self, row_widget):
        if self._drag_row is None:
            return
        try:
            if self.chk_autokey.isChecked() and row_widget.row.editable:
                AR.set_key(row_widget.row)
                row_widget.update_state()
        except Exception as exc:  # noqa: BLE001
            self.log("[ERROR] Key: {0}".format(exc))
        finally:
            cmds.undoInfo(closeChunk=True)
            self._drag_row = None

    def _end_open_drag(self):
        if self._drag_row is not None:
            cmds.undoInfo(closeChunk=True)
            self._drag_row = None

    def write(self, row_widget, value, dragging=False):
        """값 쓰기. 드래그 중이면 키를 미루고(놓을 때 한 번), 아니면 쓰기 + 키를 undo 하나로."""
        row = row_widget.row
        try:
            if dragging:
                written = AR.set_value(row, value, key=False)
            else:
                with undo_chunk():
                    written = AR.set_value(row, value, key=self.chk_autokey.isChecked())
                row_widget.update_state()
        except Exception as exc:  # noqa: BLE001
            self.log("[WARN] {0}".format(exc))
            row_widget.refresh()
            return None
        return written

    def key_row(self, row_widget):
        try:
            AR.set_key(row_widget.row)
            row_widget.update_state()
            self.log("Key set: {0}".format(row_widget.row.plug))
        except Exception as exc:  # noqa: BLE001
            self.log("[WARN] {0}".format(exc))

    # ---------------------------------------------------------- 범위

    def edit_range(self, row_widget):
        r = row_widget.row
        dlg = RangeDialog(r.label(self.name_mode), row_widget.lo, row_widget.hi, r.hard_min, r.hard_max, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        self.set_user_range(row_widget, *dlg.values())

    def set_user_range(self, row_widget, lo, hi):
        try:
            self.user_ranges.set(row_widget.row.range_key(), lo, hi)
        except ValueError as exc:
            self.log("[WARN] {0}".format(exc))
            return False
        self._reset_ranges_named(row_widget.row.range_key())
        self.log("Range of '{0}' = {1:g} ~ {2:g} (saved).".format(row_widget.row.range_key(), lo, hi))
        return True

    def clear_range(self, row_widget):
        if self.user_ranges.remove(row_widget.row.range_key()):
            self._reset_ranges_named(row_widget.row.range_key())
            self.log("Range of '{0}' reset.".format(row_widget.row.range_key()))

    def _reset_ranges_named(self, key):
        for r in self.row_widgets():
            if r.slider is not None and r.row.range_key() == key:
                r.reset_range()
                r.update_tooltip()

    # ==================================================================
    # scriptJob
    # ==================================================================

    def _start_jobs(self):
        self._kill_jobs()
        for event, fn in (("SelectionChanged", self._on_selection),
                          ("timeChanged", self._on_time),
                          ("Undo", self.refresh_values),
                          ("Redo", self.refresh_values),
                          ("SceneOpened", self.refresh_list),
                          ("NewSceneOpened", self.refresh_list)):
            try:
                self._jobs.append(cmds.scriptJob(event=[event, fn]))
            except Exception:  # noqa: BLE001
                pass

    def _kill_jobs(self):
        for job in self._jobs:
            try:
                if cmds.scriptJob(exists=job):
                    cmds.scriptJob(kill=job, force=True)
            except Exception:  # noqa: BLE001
                pass
        self._jobs = []

    def _on_selection(self):
        if not self.btn_lock.isChecked():
            # 한 번의 선택 동작에 이벤트가 여러 번 올 수 있다 - 모아서 한 번
            self._rebuild_timer.start()

    def _on_time(self):
        if self.isVisible():
            self.refresh_values()

    # ==================================================================
    # 창 동작
    # ==================================================================

    def closeEvent(self, event):
        self._end_open_drag()
        self._kill_jobs()
        super().closeEvent(event)

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Attr Slider v{0}\nLast update : {1}\n\n"
            "Lists the Channel Box attributes of the selected nodes as sliders.\n"
            "A blendShape node shows its envelope and target weights.\n\n"
            "Names Maya cannot show (Japanese, Chinese ... imported from FBX as\n"
            "FBXASC codes) are shown decoded - the Maya name is in the tooltip.\n\n"
            "Slider range: your saved range > hard limits > soft limits > automatic.\n"
            "Right-click a row to set the range (saved by attribute name).\n"
            "Colors: pink = keyed, yellow = driven, gray = locked.".format(VERSION, LAST_UPDATE))
