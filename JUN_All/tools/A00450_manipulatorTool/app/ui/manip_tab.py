# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00450_manipulatorTool - Manipulator 굵기 탭
#
# 마야에는 도구별 매니퓰레이터 굵기가 없다(manipOptions 는 전역 하나뿐).
# 이 탭은 Move/Rotate/Scale 값을 따로 들고 있다가, 도구가 바뀌는 순간(ToolChanged scriptJob)
# 그 도구의 값을 전역에 밀어 넣어 "도구별 굵기"처럼 보이게 한다. core/manip_manager.py 참고.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QFrame,
)

from tools.A00450_manipulatorTool.app.core import manip_manager as mm
from tools.A00450_manipulatorTool.app.ui.slider_row import SliderRow


LABEL_WIDTH = 82


class ManipTab(QWidget):

    def __init__(self, log_view=None, parent=None):

        super(ManipTab, self).__init__(parent)

        self.log_view = log_view

        self.state = mm.ManipState()

        self.tool_rows = {}

        self.build_ui()
        self.pull_from_maya()

        # 도구가 바뀌면 그 도구의 굵기를 전역에 밀어 넣고, 활성 줄을 다시 표시한다.
        job = self.state.start_watch(callback=self.mark_active_tool)

        if job is None:
            self.log("Warning : could not watch tool changes. "
                     "Per-tool thickness applies on slider move only.")

        self.mark_active_tool()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(self.build_thickness_group())
        layout.addWidget(self.build_picking_group())
        layout.addLayout(self.build_button_row())
        layout.addStretch(1)

    # ------------------------------------------------------------------

    def build_thickness_group(self):

        group = QGroupBox("Axis Thickness")

        box = QVBoxLayout(group)
        box.setSpacing(6)

        # ---- 마스터 : 세 도구를 한 번에 ----
        self.row_all = SliderRow(
            "All",
            mm.LINE_SIZE_MIN,
            mm.LINE_SIZE_MAX,
            step=0.1,
            label_width=LABEL_WIDTH,
        )
        self.row_all.setToolTip("Set the axis thickness of Move, Rotate and Scale at once")
        self.row_all.valueChanged.connect(self.on_all_changed)

        box.addWidget(self.row_all)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        box.addWidget(line)

        # ---- 도구별 ----
        for tool in mm.TOOLS:

            row = SliderRow(
                mm.TOOL_LABELS[tool],
                mm.LINE_SIZE_MIN,
                mm.LINE_SIZE_MAX,
                step=0.1,
                label_width=LABEL_WIDTH,
            )
            row.setToolTip(
                "Axis thickness used while the {0} tool is active".format(mm.TOOL_LABELS[tool])
            )
            row.valueChanged.connect(lambda value, t=tool: self.on_tool_size_changed(t, value))

            self.tool_rows[tool] = row

            box.addWidget(row)

        note = QLabel(
            "Maya keeps one global manipulator thickness.\n"
            "Each value above is pushed to Maya when you switch to that tool."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #9a9a9a;")
        box.addWidget(note)

        return group

    # ------------------------------------------------------------------

    def build_picking_group(self):

        # QGroupBox 제목의 & 는 단축키 표시로 먹히므로 && 로 이스케이프한다.
        group = QGroupBox("Picking && Size  (global)")

        box = QVBoxLayout(group)
        box.setSpacing(6)

        self.row_pick = SliderRow(
            "Pick Radius",
            mm.LINE_PICK_MIN,
            mm.LINE_PICK_MAX,
            step=0.5,
            label_width=LABEL_WIDTH,
        )
        self.row_pick.setToolTip(
            "Click tolerance around each axis. "
            "This is what actually makes an axis easier to grab"
        )
        self.row_pick.valueChanged.connect(self.on_pick_changed)
        box.addWidget(self.row_pick)

        self.row_handle = SliderRow(
            "Handle Size",
            mm.HANDLE_SIZE_MIN,
            mm.HANDLE_SIZE_MAX,
            step=1.0,
            label_width=LABEL_WIDTH,
        )
        self.row_handle.setToolTip("Size of the arrow heads and boxes at the end of each axis")
        self.row_handle.valueChanged.connect(self.on_handle_changed)
        box.addWidget(self.row_handle)

        self.row_scale = SliderRow(
            "Manip Scale",
            mm.MANIP_SCALE_MIN,
            mm.MANIP_SCALE_MAX,
            step=0.05,
            label_width=LABEL_WIDTH,
        )
        self.row_scale.setToolTip("Overall size of the whole manipulator")
        self.row_scale.valueChanged.connect(self.on_scale_changed)
        box.addWidget(self.row_scale)

        note = QLabel(
            "Thickness is what you see, Pick Radius is what you hit.\n"
            "Raise Pick Radius too if the manipulator is hard to grab."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #9a9a9a;")
        box.addWidget(note)

        return group

    # ------------------------------------------------------------------

    def build_button_row(self):

        row = QHBoxLayout()
        row.setSpacing(6)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setFixedHeight(30)
        self.btn_reset.setToolTip("Restore the manipulator settings this tool started with")
        self.btn_reset.clicked.connect(self.on_reset)
        row.addWidget(self.btn_reset, stretch=1)

        self.btn_default = QPushButton("Maya Default")
        self.btn_default.setFixedHeight(30)
        self.btn_default.setToolTip(
            "Restore Maya factory values : thickness 2.0, pick 4.0, handle 30.0, scale 1.0"
        )
        self.btn_default.clicked.connect(self.on_maya_default)
        row.addWidget(self.btn_default, stretch=1)

        return row

    # ==================================================================
    # 슬라이더 -> 마야 (라이브)
    # ==================================================================

    def on_all_changed(self, value):

        applied = self.state.set_all_sizes(value)

        for tool in mm.TOOLS:
            self.tool_rows[tool].set_value(applied)

    def on_tool_size_changed(self, tool, value):

        self.state.set_size(tool, value)
        self.sync_master()

    def on_pick_changed(self, value):
        mm.set_pick_radius(value)

    def on_handle_changed(self, value):
        mm.set_handle_size(value)

    def on_scale_changed(self, value):
        mm.set_manip_scale(value)

    def sync_master(self):
        """세 값이 모두 같을 때만 마스터를 그 값으로 맞춘다(다르면 그대로 둔다)."""
        values = [self.state.get_size(tool) for tool in mm.TOOLS]

        if len(set(values)) == 1:
            self.row_all.set_value(values[0])

    # ==================================================================
    # 마야 -> 슬라이더
    # ==================================================================

    def pull_from_maya(self):
        """지금 마야 값을 읽어 모든 슬라이더에 반영한다(신호 없이)."""
        state = mm.snapshot()

        for tool in mm.TOOLS:
            self.tool_rows[tool].set_value(self.state.get_size(tool))

        self.row_all.set_value(state.get("lineSize", mm.DEFAULT_LINE_SIZE))
        self.row_pick.set_value(state.get("linePick", mm.DEFAULT_LINE_PICK))
        self.row_handle.set_value(state.get("handleSize", mm.DEFAULT_HANDLE_SIZE))
        self.row_scale.set_value(state.get("scale", mm.DEFAULT_MANIP_SCALE))

        self.sync_master()

    def mark_active_tool(self):
        """활성 도구의 줄을 강조한다. scriptJob 이 죽은 UI 를 건드리지 않도록 방어한다."""
        try:
            active = mm.current_tool()

            for tool in mm.TOOLS:
                self.tool_rows[tool].set_active(tool == active)

        except RuntimeError:
            # 위젯이 이미 삭제됨 (창을 닫은 뒤 scriptJob 이 늦게 도는 경우)
            self.state.stop_watch()

    # ==================================================================
    # Reset
    # ==================================================================

    def on_reset(self):

        state = self.state.reset()

        self.pull_from_maya()
        self.state.apply_for_current()

        self.log(
            "Reset : thickness {0} / pick {1} / handle {2} / scale {3}".format(
                state.get("lineSize"),
                state.get("linePick"),
                state.get("handleSize"),
                state.get("scale"),
            )
        )

    def on_maya_default(self):

        mm.restore({
            "lineSize": mm.DEFAULT_LINE_SIZE,
            "linePick": mm.DEFAULT_LINE_PICK,
            "handleSize": mm.DEFAULT_HANDLE_SIZE,
            "scale": mm.DEFAULT_MANIP_SCALE,
        })

        for tool in mm.TOOLS:
            self.state.sizes[tool] = mm.DEFAULT_LINE_SIZE

        self.pull_from_maya()

        self.log("Restored Maya default manipulator settings.")

    # ==================================================================
    # 정리 / 로그
    # ==================================================================

    def shutdown(self):
        """창이 닫힐 때 scriptJob 을 끊는다. 안 그러면 죽은 위젯을 가리키는 job 이 남는다."""
        self.state.stop_watch()

    def log(self, text):

        if self.log_view is None:
            print(text)
            return

        self.log_view.appendPlainText(text)
