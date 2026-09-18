# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00400_CurveTool - Create > Controls 탭 (컨트롤러 커브 만들기 · 색 · 셰이프 교체)
#
# Brandon Schaal 의 `bs_controls` / `bs_controlsUI` 를 옮긴 화면이다. 원본 창의 세 섹션
# (Create Controls / Control Colors / Control Shape Replace)을 **그 순서 그대로** 한 탭에 담았다.
# 로직은 전부 `app/core/control_manager.py` 에 있고 여기서는 화면만 만든다.
#
# 원본은 `cmds.frameLayout` 세 개를 접었다 폈다 했는데, 여기서는 `QGroupBox` 세 개다 -
# 이 툴의 다른 탭과 같은 모양을 유지한다.

from Framework.qt.qt import *

import maya.cmds as cmds

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
        # Load 버튼으로 담아 둔 롱네임들 (씬에서 다시 고르기 전까지 유지)
        self._targets = []
        self._replacements = []

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        note = QLabel(
            "Build control curves from a shape library, colour them, and swap the\n"
            "shape of existing controls. Ported from Brandon Schaal's bs_controls.")
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)

        root.addWidget(self._build_create_group(), 1)
        root.addWidget(self._build_color_group())
        root.addWidget(self._build_replace_group())

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

        thick_row = QHBoxLayout()
        thick_row.addWidget(QLabel("Thickness"))
        self.sb_thickness = QDoubleSpinBox()
        self.sb_thickness.setRange(1.0, 8.0)
        self.sb_thickness.setDecimals(1)
        self.sb_thickness.setSingleStep(0.5)
        self.sb_thickness.setValue(1.0)
        self.sb_thickness.setKeyboardTracking(False)
        self.sb_thickness.setToolTip(
            "Viewport line width of the new control (nurbsCurve.lineWidth).\n"
            "1.0 leaves Maya's default - the shape is not changed either way.")
        thick_row.addWidget(self.sb_thickness)
        thick_row.addStretch(1)
        layout.addLayout(thick_row)

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

        self.btn_reset_color = QPushButton("Reset Color")
        self.btn_reset_color.setToolTip(
            "Turn the drawing overrides off again, on both the transform and the\n"
            "shapes, so the control goes back to its layer / default colour.")
        self.btn_reset_color.clicked.connect(self.on_reset_color)
        layout.addWidget(self.btn_reset_color)

        return box

    # ---------------- Shape Replace ----------------

    def _build_replace_group(self):
        box = QGroupBox("Shape Replace")
        layout = QVBoxLayout(box)

        fields = QHBoxLayout()
        self.le_targets = QLineEdit()
        self.le_targets.setPlaceholderText("Shapes to replace...")
        self.le_targets.setReadOnly(True)
        self.le_replacements = QLineEdit()
        self.le_replacements.setPlaceholderText("Replacement(s)...")
        self.le_replacements.setReadOnly(True)
        fields.addWidget(self.le_targets)
        fields.addWidget(self.le_replacements)
        layout.addLayout(fields)

        buttons = QHBoxLayout()
        self.btn_load_targets = QPushButton("Load Shape")
        self.btn_load_targets.setToolTip(
            "Remember the selected control(s) as the ones to change.")
        self.btn_load_targets.clicked.connect(lambda: self.on_load(True))
        self.btn_load_replacements = QPushButton("Load Replacement")
        self.btn_load_replacements.setToolTip(
            "Remember the selected curve(s) as the shape(s) to copy from.\n"
            "One replacement goes on every target; the same number as targets\n"
            "pairs them up in order.")
        self.btn_load_replacements.clicked.connect(lambda: self.on_load(False))
        buttons.addWidget(self.btn_load_targets)
        buttons.addWidget(self.btn_load_replacements)
        layout.addLayout(buttons)

        self.chk_mirror = QCheckBox("Mirror Shapes")
        self.chk_mirror.setToolTip(
            "Flip the replacement across X before it is applied - for the other\n"
            "side of the rig. The target's own position is then not matched.")
        layout.addWidget(self.chk_mirror)

        self.btn_replace = QPushButton("Replace Shapes")
        self.btn_replace.setMinimumHeight(28)
        self.btn_replace.setToolTip(
            "Swap the target's curve shape for the replacement's, keeping the\n"
            "target's transform, name and connections. One undo step.")
        self.btn_replace.clicked.connect(self.on_replace)
        layout.addWidget(self.btn_replace)

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
                shape, mode=mode, name=self.le_name.text(),
                thickness=self.sb_thickness.value())
        except Exception as exc:                            # noqa: BLE001
            self._log("Create control failed: {0}".format(exc))
            return
        self._log_all(messages)

    def on_color(self, index):
        _touched, messages = ctl_mgr.set_color(index)
        self._log_all(messages)

    def on_display(self, display):
        _touched, messages = ctl_mgr.set_display_type(display)
        self._log_all(messages)

    def on_reset_color(self):
        _touched, messages = ctl_mgr.reset_color()
        self._log_all(messages)

    def on_load(self, is_target):
        """지금 선택을 타깃 / 교체용으로 담는다(씬 불변)."""
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            self._log("[WARN] Select the curve(s) to load first.")
            return

        nice = [s.split("|")[-1] for s in selection]
        text = ", ".join(nice) if len(nice) == 1 else "{0} shapes loaded.".format(len(nice))

        if is_target:
            self._targets = selection
            self.le_targets.setText(text)
            self.le_targets.setToolTip(", ".join(nice))
        else:
            self._replacements = selection
            self.le_replacements.setText(text)
            self.le_replacements.setToolTip(", ".join(nice))
        self._log("Loaded {0} {1} shape(s): {2}".format(
            len(nice), "target" if is_target else "replacement", ", ".join(nice)))

    def on_replace(self):
        _replaced, messages = ctl_mgr.replace_shapes(
            self._targets, self._replacements, mirror=self.chk_mirror.isChecked())
        self._log_all(messages)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)
