# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-22
# A00400_CurveTool - Create > Controls 탭 (컨트롤러 커브 만들기 · 색 · 팔레트)
#
# Brandon Schaal 의 `bs_controls` / `bs_controlsUI` 를 옮긴 화면이다. 원본 창의 세 섹션 중
# **만들기와 색** 두 가지를 담는다. 세 번째인 셰이프 교체는 v01.16 에서
# **`Display > Replace` 하위 탭**(`replace_tab.py`)으로 떼어 냈다 - 대상·교체본을 리스트(TSL)에
# 담아 두고 여러 번 돌리는 쪽이 실제 작업 방식이라 자리가 넉넉해야 했다.
# 로직은 전부 `app/core/control_manager.py` 에 있고 여기서는 화면만 만든다.
#
# 원본은 `cmds.frameLayout` 을 접었다 폈다 했는데, 여기서는 `QGroupBox` 다 -
# 이 툴의 다른 탭과 같은 모양을 유지한다.

from Framework.qt.qt import *

from tools.A00400_CurveTool.app.core import control_manager as ctl_mgr


#: 색 버튼 한 칸 크기 (원본 gridLayout 의 30 x 20)
SWATCH_W = 30
SWATCH_H = 20

#: 한 줄에 놓을 색 칸 수. 31칸 + T + R 이 두 줄에 들어간다.
SWATCH_COLUMNS = 11


class ControlsTab(QWidget):
    """컨트롤러 커브 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    def __init__(self, log_callback=None, parent=None):
        super(ControlsTab, self).__init__(parent)

        self._log = log_callback or (lambda text: None)
        # 팔레트에서 마지막으로 고른 색 (0~1 세 값). 아직 안 골랐으면 None.
        self._last_rgb = None

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        note = QLabel(
            "Build control curves from a shape library and colour them.\n"
            "Ported from Brandon Schaal's bs_controls - its shape replace now\n"
            "lives in Display > Replace, the drawn line width in\n"
            "Display > Shape Edit.")
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)

        root.addWidget(self._build_create_group(), 1)
        root.addWidget(self._build_color_group())

    # ---------------- Create ----------------

    def _build_create_group(self):
        box = QGroupBox("Create Controls")
        layout = QVBoxLayout(box)

        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("Controller name or suffix replace...")
        self.le_name.setToolTip(
            "Empty      : <object>_ANIM\n"
            "One word   : the object's common suffix (_jnt, _loc, ...) is swapped\n"
            "             for it - spine_jnt + ctl -> spine_ctl\n"
            "With a '_' : used as the name exactly as typed (spaces become '_')")
        layout.addWidget(self.le_name)

        self.lw_shapes = QListWidget()
        self.lw_shapes.setMinimumHeight(150)
        self.lw_shapes.setToolTip("The shape to build. Double-click to build it at the origin.")
        names = ctl_mgr.shape_names()
        self.lw_shapes.addItems(names)
        if names:
            self.lw_shapes.setCurrentRow(0)
        self.lw_shapes.itemDoubleClicked.connect(lambda *_: self.on_create(ctl_mgr.MODE_ORIGIN))
        layout.addWidget(self.lw_shapes, 1)

        grid = QGridLayout()
        specs = (
            ("Parent", ctl_mgr.MODE_PARENT, 0, 0,
             "Build the control at each selected object and make it the object's\n"
             "PARENT (the control takes the object's place in the hierarchy)."),
            ("Child", ctl_mgr.MODE_CHILD, 0, 1,
             "Build the control at each selected object and park it UNDER the object.\n"
             "The object's own children are moved under the control."),
            ("World", ctl_mgr.MODE_WORLD, 1, 0,
             "Build the control at each selected object but leave it in the world\n"
             "(no parenting)."),
            ("Origin", ctl_mgr.MODE_ORIGIN, 1, 1,
             "Build one control at the origin. The selection is ignored.\n"
             "With no name typed the shape name is used (circle_pin, ...)."),
        )
        self.buttons = {}
        for label, mode, row, col, tip in specs:
            button = QPushButton(label)
            button.setMinimumHeight(28)
            button.setToolTip(tip + "\nOne undo step.")
            button.clicked.connect(lambda _checked=False, m=mode: self.on_create(m))
            grid.addWidget(button, row, col)
            self.buttons[mode] = button
        layout.addLayout(grid)

        return box

    # ---------------- Color ----------------

    def _build_color_group(self):
        box = QGroupBox("Control Color")
        layout = QVBoxLayout(box)

        note = QLabel("Sets the colour on the SHAPE, so children do not inherit it.")
        note.setWordWrap(True)
        layout.addWidget(note)

        grid = QGridLayout()
        grid.setSpacing(2)
        for i, (index, rgb) in enumerate(ctl_mgr.COLOR_SWATCHES):
            button = QPushButton()
            button.setFixedSize(SWATCH_W, SWATCH_H)
            # 테마 qss 의 버튼 색을 이 버튼만 덮어쓴다(색 견본이라 색 자체가 내용이다).
            button.setStyleSheet(
                "background-color: rgb({0}, {1}, {2}); border: 1px solid #202020;".format(
                    int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)))
            button.setToolTip("Maya colour index {0}".format(index))
            button.clicked.connect(lambda _checked=False, c=index: self.on_color(c))
            grid.addWidget(button, i // SWATCH_COLUMNS, i % SWATCH_COLUMNS)

        count = len(ctl_mgr.COLOR_SWATCHES)
        self.btn_template = QPushButton("T")
        self.btn_template.setFixedSize(SWATCH_W, SWATCH_H)
        self.btn_template.setToolTip(
            "Template - the control is drawn grey and cannot be selected in the viewport.")
        self.btn_template.clicked.connect(
            lambda: self.on_display(ctl_mgr.DISPLAY_TEMPLATE))
        grid.addWidget(self.btn_template, count // SWATCH_COLUMNS, count % SWATCH_COLUMNS)

        self.btn_reference = QPushButton("R")
        self.btn_reference.setFixedSize(SWATCH_W, SWATCH_H)
        self.btn_reference.setToolTip(
            "Reference - the control is drawn normally but cannot be selected.")
        self.btn_reference.clicked.connect(
            lambda: self.on_display(ctl_mgr.DISPLAY_REFERENCE))
        grid.addWidget(self.btn_reference, (count + 1) // SWATCH_COLUMNS,
                       (count + 1) % SWATCH_COLUMNS)

        grid_row = QHBoxLayout()
        grid_row.addLayout(grid)
        grid_row.addStretch(1)
        layout.addLayout(grid_row)

        # v01.17 - 인덱스 32색 밖의 색. ref_01.mel 의 `Color Palettes` 와 같은 방식
        # (`overrideRGBColors` + `overrideColorRGB`)이고, 팔레트는 별도 팝업이다.
        palette_row = QHBoxLayout()
        self.btn_palette = QPushButton("Color Palette...")
        self.btn_palette.setToolTip(
            "Pick any colour from a palette window (not just the 32 index colours).\n"
            "The shape is switched to RGB override (overrideRGBColors) and gets\n"
            "exactly the colour you picked. Reset Color undoes both kinds.")
        self.btn_palette.clicked.connect(self.on_palette)
        palette_row.addWidget(self.btn_palette, 1)

        # 마지막으로 고른 색을 보여 주는 견본 + 다시 적용 버튼
        self.btn_last_color = QPushButton()
        self.btn_last_color.setFixedSize(SWATCH_W, SWATCH_H)
        self.btn_last_color.setToolTip("Apply the colour you picked last.")
        self.btn_last_color.clicked.connect(
            lambda: self.on_rgb(self._last_rgb) if self._last_rgb else self.on_palette())
        palette_row.addWidget(self.btn_last_color)
        layout.addLayout(palette_row)
        self._show_last_color()

        self.btn_reset_color = QPushButton("Reset Color")
        self.btn_reset_color.setToolTip(
            "Turn the drawing overrides off again, on both the transform and the\n"
            "shapes, so the control goes back to its layer / default colour.")
        self.btn_reset_color.clicked.connect(self.on_reset_color)
        layout.addWidget(self.btn_reset_color)

        return box

    # ==================================================================
    # 동작
    # ==================================================================

    def _shape(self):
        item = self.lw_shapes.currentItem()
        return item.text() if item else ""

    def on_create(self, mode):
        shape = self._shape()
        if not shape:
            self._log("[WARN] Pick a control shape from the list first.")
            return
        try:
            _result, messages = ctl_mgr.create_controls(
                shape, mode=mode, name=self.le_name.text())
        except Exception as exc:                            # noqa: BLE001
            self._log("Create control failed: {0}".format(exc))
            return
        self._log_all(messages)

    def on_color(self, index):
        _touched, messages = ctl_mgr.set_color(index)
        self._log_all(messages)

    def on_palette(self):
        """팔레트 팝업을 띄워 임의 색을 고르고, 고른 색을 선택한 컨트롤에 입힌다.

        ★ 마야의 `cmds.colorEditor`(ref_01.mel 이 쓰는 것) 대신 **Qt 팔레트**를 쓴다 -
        이 툴은 PySide 창이라 팝업도 같은 위젯 계열이어야 부모·테마·항상 위 설정이 맞물린다.
        고르는 값은 같은 0~1 RGB 이고, 들어가는 어트리뷰트도 ref 와 같다.
        """
        start = QColor.fromRgbF(*self._last_rgb) if self._last_rgb else QColor(255, 255, 0)
        picked = QColorDialog.getColor(start, self, "Control Color")
        if not picked.isValid():        # 취소
            return
        self._last_rgb = (picked.redF(), picked.greenF(), picked.blueF())
        self._show_last_color()
        self.on_rgb(self._last_rgb)

    def on_rgb(self, rgb):
        _touched, messages = ctl_mgr.set_color_rgb(rgb)
        self._log_all(messages)

    def _show_last_color(self):
        """견본 버튼에 마지막으로 고른 색을 칠한다(아직 없으면 빈 칸)."""
        if not self._last_rgb:
            self.btn_last_color.setStyleSheet("border: 1px dashed #808080;")
            self.btn_last_color.setText("")
            return
        r, g, b = (int(round(v * 255)) for v in self._last_rgb)
        self.btn_last_color.setStyleSheet(
            "background-color: rgb({0}, {1}, {2}); border: 1px solid #202020;".format(r, g, b))

    def on_display(self, display):
        _touched, messages = ctl_mgr.set_display_type(display)
        self._log_all(messages)

    def on_reset_color(self):
        _touched, messages = ctl_mgr.reset_color()
        self._log_all(messages)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)
