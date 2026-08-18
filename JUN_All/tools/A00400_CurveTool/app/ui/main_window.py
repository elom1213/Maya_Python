# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-29
# A00400_CurveTool - Qt UI
#
# 1) 선택한 메시 엣지에 부착된 커브를 만든다. 떨어져 있는 엣지 덩어리(연결 성분)마다
#    커브를 따로 만들어, 여러 엣지 구간을 한 번에 고르면 그만큼 여러 커브가 나온다.
# 2) 리스트업한 커브들의 cv[0]/cv[n] 월드 위치를 지정 축으로 비교해 방향을 통일한다
#    (Reverse Direction). 축 비교 방식은 A00360_SortTool 을 참고했다.
#
# 위 두 기능은 "Create / Direction" 탭이고, "Line Width" 탭은 리스트업한 커브의 뷰포트
# 표시 굵기(nurbsCurve.lineWidth)를 슬라이더로 조절한다 — 씬에서 커브를 눈으로 찾고
# 클릭으로 집기 쉽게 하려는 용도다(형상은 건드리지 않는다).

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00400_CurveTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00400_CurveTool.app.core import curve_manager as curve_mgr
from tools.A00400_CurveTool.app.core import wrap_manager as wrap_mgr


WINDOW_OBJECT_NAME = "JUN_A00400_CurveTool_window"

# 방향 비교 축 라디오 (label, mode)
_AXIS_MODES = [
    ("World X", curve_mgr.MODE_X),
    ("World Y", curve_mgr.MODE_Y),
    ("World Z", curve_mgr.MODE_Z),
]

_WARN_COLOR = "#ffb454"


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Curve Tool v{0}".format(VERSION)
        self.resize(360, 620)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        # 메뉴 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # 로그창은 탭 빌더가 self.log 를 부를 수 있어 탭보다 먼저 만든다(둘이 공유).
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(110)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_create_tab(), "Create / Direction")
        index = self.tabs.addTab(self._build_width_tab(), "Line Width")
        self.tabs.setTabToolTip(
            index,
            "Make the listed curves thicker in the viewport so they are easier "
            "to see and to click on.")
        index = self.tabs.addTab(self._build_wrap_tab(), "Wrap")
        self.tabs.setTabToolTip(
            index,
            "Make one curve take the shape of another, even when the two have "
            "different CV counts.")
        root.addWidget(self.tabs, 1)

        root.addWidget(self.te_log)

        self.log("Curve Tool v{0} ({1}) ready. Select mesh edges and click "
                 "'Create Curves from Selected Edges'.".format(VERSION, LAST_UPDATE))

    # --------------------------------------------------------------
    # Tab 1 : Create / Direction  (기존 기능 그대로)
    # --------------------------------------------------------------

    def _build_create_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # ---------------- 1) 엣지 -> 커브 생성 ----------------
        gen_box = QGroupBox("Create Curves from Mesh Edges")
        gen_lay = QVBoxLayout(gen_box)

        # 이름 접두사
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name Prefix"))
        self.le_prefix = QLineEdit("edgeCurve")
        name_row.addWidget(self.le_prefix, 1)
        gen_lay.addLayout(name_row)

        # 부드러운 커브 옵션 (degree 3)
        self.chk_smooth = QCheckBox("Smooth curve (degree 3)")
        self.chk_smooth.setToolTip(
            "Off: linear curve that follows the edges exactly (degree 1).\n"
            "On: smooth degree-3 curve through the edge points.")
        gen_lay.addWidget(self.chk_smooth)

        self.btn_create = QPushButton("Create Curves from Selected Edges")
        self.btn_create.setMinimumHeight(34)
        self.btn_create.clicked.connect(self.on_create)
        gen_lay.addWidget(self.btn_create)

        root.addWidget(gen_box)

        # ---------------- 커브 리스트(TSL) ----------------
        # 생성된 커브가 여기 담기며, Reverse Direction 은 이 리스트를 대상으로 동작한다.
        # 손으로 씬에서 커브를 골라 'List Selected Curves' 로 담을 수도 있다.
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Curves", select_label="List Selected Curves",
            show_sort=False, list_min_height=170, log_callback=self.log)
        root.addWidget(self.tsl, 1)

        # ---------------- 2) 방향 정렬 ----------------
        dir_box = QGroupBox("Reverse Direction")
        dir_lay = QVBoxLayout(dir_box)

        # 비교 축
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Compare Axis"))
        self.axis_group = QButtonGroup(self)
        for i, (label, mode) in enumerate(_AXIS_MODES):
            rb = QRadioButton(label)
            rb.setProperty("mode", mode)
            if mode == curve_mgr.MODE_Y:   # 기본 Y (위 -> 아래)
                rb.setChecked(True)
            self.axis_group.addButton(rb, i)
            axis_row.addWidget(rb)
        dir_lay.addLayout(axis_row)

        # cv[0] 가 와야 할 끝(최대/최소)
        end_row = QHBoxLayout()
        end_row.addWidget(QLabel("cv[0] at"))
        self.end_group = QButtonGroup(self)
        self.rb_max = QRadioButton("Max end (e.g. top)")
        self.rb_max.setChecked(True)
        self.rb_min = QRadioButton("Min end (e.g. bottom)")
        self.end_group.addButton(self.rb_max, 0)
        self.end_group.addButton(self.rb_min, 1)
        end_row.addWidget(self.rb_max)
        end_row.addWidget(self.rb_min)
        dir_lay.addLayout(end_row)

        self.btn_reverse = QPushButton("Reverse Direction")
        self.btn_reverse.setMinimumHeight(34)
        self.btn_reverse.setToolTip(
            "For each listed curve, compare cv[0] vs cv[n] on the chosen axis and\n"
            "flip the curve direction so cv[0] ends up on the chosen end.")
        self.btn_reverse.clicked.connect(self.on_reverse)
        dir_lay.addWidget(self.btn_reverse)

        root.addWidget(dir_box)
        return tab

    # --------------------------------------------------------------
    # Tab 2 : Line Width  (뷰포트에서 잘 보이고 잘 집히도록)
    # --------------------------------------------------------------

    def _build_width_tab(self):
        """리스트업한 커브의 **표시 굵기**(`nurbsCurve.lineWidth`)를 슬라이더로 조절한다.

        형상이 아니라 그려지는 두께만 바꾸는 표시 전용 어트리뷰트라, 굵게 해 두면 씬에서
        커브가 눈에 잘 띄고 클릭으로 집기도 쉬워진다.
        """
        tab = QWidget()
        root = QVBoxLayout(tab)

        desc = QLabel(
            "Thicker curves are easier to see and to click in the viewport.\n"
            "Drag the slider - it is applied as soon as you let go.\n"
            "This only changes how the curve is drawn - shape and history are "
            "untouched.")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        self.tsl_width = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Curves", select_label="List Selected Curves",
            show_sort=False, list_min_height=170, log_callback=self.log)
        root.addWidget(self.tsl_width, 1)

        width_box = QGroupBox("Line Width")
        width_lay = QVBoxLayout(width_box)

        row = QHBoxLayout()
        self.sld_width = QSlider(Qt.Horizontal)
        # 슬라이더는 정수라 0.1 단위로 쓰려고 10 배로 잡는다.
        self.sld_width.setRange(int(curve_mgr.LINE_WIDTH_MIN * 10),
                                int(curve_mgr.LINE_WIDTH_MAX * 10))
        self.sld_width.setValue(20)
        self.sld_width.setToolTip(
            "Drag to set the drawn thickness of every listed curve.\n"
            "It updates live while you drag and is applied for good the moment "
            "you let go\n(no Apply button needed). The whole drag is one undo "
            "step.")
        row.addWidget(self.sld_width, 1)

        self.dsb_width = QDoubleSpinBox()
        self.dsb_width.setDecimals(1)
        self.dsb_width.setSingleStep(0.1)
        self.dsb_width.setRange(curve_mgr.LINE_WIDTH_MIN, curve_mgr.LINE_WIDTH_MAX)
        self.dsb_width.setValue(2.0)
        self.dsb_width.setFixedWidth(70)
        self.dsb_width.setKeyboardTracking(False)
        row.addWidget(self.dsb_width)
        width_lay.addLayout(row)

        btn_row = QHBoxLayout()
        self.btn_width_get = QPushButton("Get")
        self.btn_width_get.setToolTip(
            "Read the line width of the first listed curve into the slider.")
        self.btn_width_get.clicked.connect(self.on_width_get)
        btn_row.addWidget(self.btn_width_get)

        self.btn_width_reset = QPushButton("Use Maya Default (-1)")
        self.btn_width_reset.setToolTip(
            "Set the listed curves back to -1, which means 'follow Maya's "
            "global line width'.")
        self.btn_width_reset.clicked.connect(self.on_width_reset)
        btn_row.addWidget(self.btn_width_reset)
        width_lay.addLayout(btn_row)

        root.addWidget(width_box)

        # 슬라이더 <-> 스핀박스 동기화 + 라이브 적용.
        self.sld_width.valueChanged.connect(self._on_width_slider)
        self.dsb_width.valueChanged.connect(self._on_width_spin)
        # 드래그 전체를 undo 한 스텝으로 묶는다(값이 바뀔 때마다 쌓이지 않게).
        self.sld_width.sliderPressed.connect(self._width_drag_start)
        self.sld_width.sliderReleased.connect(self._width_drag_end)
        self._width_dragging = False

        return tab

    # ==============================================================
    # actions
    # ==============================================================

    def _axis_mode(self):
        btn = self.axis_group.checkedButton()
        return btn.property("mode") if btn else curve_mgr.MODE_Y

    def on_create(self):
        """선택한 엣지 덩어리마다 커브를 만들어 TSL 에 담는다."""
        prefix = (self.le_prefix.text() or "edgeCurve").strip()
        degree = 3 if self.chk_smooth.isChecked() else 1

        try:
            with undo_chunk():
                created, groups = curve_mgr.curves_from_selected_edges(
                    prefix=prefix, degree=degree)
        except ValueError as e:
            self.log(str(e), warn=True)
            return
        except Exception as e:
            self.log("Create failed: {0}".format(e), warn=True)
            return

        # 생성된 커브를 리스트에 담는다(기존 리스트 교체).
        self.tsl.set_items(created)
        self.log("Created {0} curve(s) from {1} edge group(s): {2}".format(
            len(created), groups, ", ".join(created)))

    def on_reverse(self):
        """리스트업된 커브의 방향을 지정 축 기준으로 통일한다."""
        # UUID 로 현재 경로를 되찾아(리네임/리페어런트 안전) 대상 커브를 얻는다.
        curves = self.tsl.get_all_nodes()
        if not curves:
            curves = self.tsl.get_all_items()   # UUID 없는 항목 폴백
        if not curves:
            self.log("Curve list is empty. Create curves or list some first.", warn=True)
            return

        mode = self._axis_mode()
        cv0_at_max = self.rb_max.isChecked()

        try:
            with undo_chunk():
                reversed_names, skipped = curve_mgr.reverse_curves_by_axis(
                    curves, mode, cv0_at_max=cv0_at_max)
        except Exception as e:
            self.log("Reverse failed: {0}".format(e), warn=True)
            return

        end_txt = "Max" if cv0_at_max else "Min"
        self.log("Reversed {0} curve(s) so cv[0] is at the {1} {2} end.{3}".format(
            len(reversed_names), mode.upper(), end_txt,
            (" [" + ", ".join(reversed_names) + "]") if reversed_names else ""))
        if skipped:
            details = ", ".join("{0} ({1})".format(n, why) for n, why in skipped)
            self.log("Skipped {0}: {1}".format(len(skipped), details))

    # --------------------------------------------------------------
    # Tab 3 : Wrap
    # --------------------------------------------------------------

    def _build_wrap_tab(self):
        """CV 개수가 다른 두 커브에서, 한쪽이 다른 쪽의 모양을 그대로 따르게 한다.

        마야 기본 `wrap` 디포머로도 커브끼리 묶을 수는 있지만 결과가 불안정하다.
        여기서는 디포머 대신 `rebuildCurve` + `blendShape` 노드 네트워크를 만든다
        (자세한 이유와 실측은 core/wrap_manager.py 참고).
        """
        tab = QWidget()
        root = QVBoxLayout(tab)

        desc = QLabel(
            "Make the driven curve take the driver's shape, even with a different "
            "CV count.\nThe driven curve gets a 0-1 attribute that blends between "
            "its own shape and\nthe wrapped one, like a blendShape envelope.")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        pick_box = QGroupBox("Curves")
        pick_lay = QVBoxLayout(pick_box)

        self.le_wrap_driver = QLineEdit()
        self.le_wrap_driver.setPlaceholderText("driver - the shape to copy")
        self.le_wrap_driven = QLineEdit()
        self.le_wrap_driven.setPlaceholderText("driven - the curve that gets deformed")

        for label, field, tip in (
                ("Driver", self.le_wrap_driver, "The curve whose shape is copied."),
                ("Driven", self.le_wrap_driven,
                 "The curve that is deformed. It keeps its own CVs and history.")):
            row = QHBoxLayout()
            caption = QLabel(label)
            caption.setFixedWidth(46)
            row.addWidget(caption)
            field.setToolTip(tip)
            row.addWidget(field, 1)
            button = QPushButton("<<")
            button.setFixedWidth(34)
            button.setToolTip("Put the first selected curve here.")
            button.clicked.connect(lambda _checked=False, f=field: self._wrap_pick(f))
            row.addWidget(button)
            pick_lay.addLayout(row)

        root.addWidget(pick_box)

        opt_box = QGroupBox("Options")
        opt_lay = QVBoxLayout(opt_box)

        self.chk_wrap_offset = QCheckBox("Preserve offset (follow the driver's change only)")
        self.chk_wrap_offset.setToolTip(
            "Off : at envelope 1 the driven curve becomes the driver's shape.\n"
            "On  : the driven curve keeps its own shape and only follows how the "
            "driver changes\n      from the moment the wrap was made.")
        opt_lay.addWidget(self.chk_wrap_offset)

        self.chk_wrap_uniform = QCheckBox("Uniform-rebuild the driven curve")
        self.chk_wrap_uniform.setToolTip(
            "Only matters when the driven curve has non-uniform knots - then an exact "
            "match is\nimpossible. Turning this on rebuilds it evenly first, which "
            "changes the driven\ncurve's own shape a little but makes the wrap far "
            "more accurate.")
        opt_lay.addWidget(self.chk_wrap_uniform)

        attr_row = QHBoxLayout()
        attr_row.addWidget(QLabel("Envelope attr"))
        self.le_wrap_attr = QLineEdit(wrap_mgr.DEFAULT_ENVELOPE_ATTR)
        self.le_wrap_attr.setToolTip(
            "Name of the 0-1 attribute added to the driven curve.")
        attr_row.addWidget(self.le_wrap_attr, 1)
        opt_lay.addLayout(attr_row)

        root.addWidget(opt_box)

        btn_row = QHBoxLayout()
        self.btn_wrap_check = QPushButton("Check")
        self.btn_wrap_check.setToolTip(
            "Report what the two curves look like and whether they can be wrapped, "
            "without changing anything.")
        self.btn_wrap_check.clicked.connect(self.on_wrap_check)
        btn_row.addWidget(self.btn_wrap_check)

        self.btn_wrap_create = QPushButton("Create Wrap")
        self.btn_wrap_create.clicked.connect(self.on_wrap_create)
        btn_row.addWidget(self.btn_wrap_create, 1)

        self.btn_wrap_remove = QPushButton("Remove Wrap")
        self.btn_wrap_remove.setToolTip(
            "Delete the wrap setup from the driven curve and give it its own shape back.")
        self.btn_wrap_remove.clicked.connect(self.on_wrap_remove)
        btn_row.addWidget(self.btn_wrap_remove)
        root.addLayout(btn_row)

        env_box = QGroupBox("Envelope")
        env_lay = QVBoxLayout(env_box)

        env_row = QHBoxLayout()
        self.sld_wrap_env = QSlider(Qt.Horizontal)
        # 슬라이더는 정수라 0.01 단위로 쓰려고 100 배로 잡는다.
        self.sld_wrap_env.setRange(0, 100)
        self.sld_wrap_env.setValue(100)
        self.sld_wrap_env.setToolTip(
            "0 = the driven curve's own shape, 1 = wrapped.\n"
            "This writes the attribute on the driven curve - the same value you can "
            "key or\nconnect anywhere else.")
        env_row.addWidget(self.sld_wrap_env, 1)

        self.dsb_wrap_env = QDoubleSpinBox()
        self.dsb_wrap_env.setDecimals(2)
        self.dsb_wrap_env.setSingleStep(0.05)
        self.dsb_wrap_env.setRange(0.0, 1.0)
        self.dsb_wrap_env.setValue(1.0)
        self.dsb_wrap_env.setFixedWidth(70)
        self.dsb_wrap_env.setKeyboardTracking(False)
        env_row.addWidget(self.dsb_wrap_env)
        env_lay.addLayout(env_row)

        root.addWidget(env_box)
        root.addStretch(1)

        self._wrap_env_dragging = False
        self.sld_wrap_env.valueChanged.connect(self._on_wrap_env_slider)
        self.dsb_wrap_env.valueChanged.connect(self._on_wrap_env_spin)
        self.sld_wrap_env.sliderPressed.connect(self._wrap_env_drag_start)
        self.sld_wrap_env.sliderReleased.connect(self._wrap_env_drag_end)

        return tab

    # ==============================================================
    # actions : Wrap
    # ==============================================================

    def _wrap_pick(self, field):
        """씬에서 고른 첫 커브를 필드에 넣는다."""
        selection = cmds.ls(selection=True, long=True) or []

        for node in selection:
            if wrap_mgr.curve_shape(node):
                field.setText(node)
                return

        self.log("Select a NURBS curve first.", warn=True)

    def _wrap_pair(self):
        driver = self.le_wrap_driver.text().strip()
        driven = self.le_wrap_driven.text().strip()

        if not driver or not driven:
            self.log("Set both Driver and Driven first (use the << buttons).", warn=True)
            return None, None

        return driver, driven

    def _wrap_report(self, warnings):
        for warning in warnings:
            self.log(warning, warn=True)

    def on_wrap_check(self):
        driver, driven = self._wrap_pair()

        if not driver:
            return

        error, warnings, info = wrap_mgr.check(driver, driven)

        if info:
            for role in ("driver", "driven"):
                data = info[role]
                self.log("{0} : {1} CVs, {2} spans, degree {3}, {4}{5}".format(
                    role, data["cvs"], data["spans"], data["degree"],
                    wrap_mgr.form_name(data["form"]),
                    "" if wrap_mgr.is_uniform(data) else ", non-uniform knots"))

        self._wrap_report(warnings)

        if error:
            self.log(error, warn=True)
        else:
            self.log("These two curves can be wrapped.")

    def on_wrap_create(self):
        driver, driven = self._wrap_pair()

        if not driver:
            return

        result = wrap_mgr.create_wrap(
            driver, driven,
            attr_name=self.le_wrap_attr.text().strip() or wrap_mgr.DEFAULT_ENVELOPE_ATTR,
            preserve_offset=self.chk_wrap_offset.isChecked(),
            uniform_rebuild=self.chk_wrap_uniform.isChecked())

        self._wrap_report(result.get("warnings") or [])

        if not result["ok"]:
            self.log(result["message"], warn=True)
            return

        self.log(result["message"])
        self._set_wrap_env_widgets(1.0)

    def on_wrap_remove(self):
        driven = self.le_wrap_driven.text().strip()

        if not driven:
            self.log("Set the Driven curve first.", warn=True)
            return

        error = wrap_mgr.remove_wrap(driven)

        if error:
            self.log(error, warn=True)
            return

        self.log("Removed the curve wrap from {0}.".format(driven.split("|")[-1]))

    def _set_wrap_env_widgets(self, value):
        """슬라이더/스핀박스를 값에 맞춘다(서로 신호를 되쏘지 않게 막고)."""
        for widget, scaled in ((self.sld_wrap_env, int(round(value * 100))),
                               (self.dsb_wrap_env, value)):
            widget.blockSignals(True)
            widget.setValue(scaled)
            widget.blockSignals(False)

    def _apply_wrap_env(self, value, log=True):
        driven = self.le_wrap_driven.text().strip()

        if not driven:
            if log:
                self.log("Set the Driven curve first.", warn=True)
            return False

        if not wrap_mgr.set_envelope(driven, value):
            if log:
                self.log("{0} has no curve wrap.".format(driven.split("|")[-1]), warn=True)
            return False

        if log:
            self.log("Envelope {0:.2f} -> {1}".format(value, driven.split("|")[-1]))

        return True

    def _on_wrap_env_slider(self, value):
        env = value / 100.0
        self._set_wrap_env_widgets(env)

        if self._wrap_env_dragging:
            # 드래그 중 — undo 청크가 열려 있고, 로그는 손을 뗄 때 한 번만.
            self._apply_wrap_env(env, log=False)
        else:
            with undo_chunk():
                self._apply_wrap_env(env)

    def _on_wrap_env_spin(self, value):
        self._set_wrap_env_widgets(value)
        with undo_chunk():
            self._apply_wrap_env(value)

    def _wrap_env_drag_start(self):
        self._wrap_env_dragging = True
        cmds.undoInfo(openChunk=True)

    def _wrap_env_drag_end(self):
        """손을 떼는 순간이 커밋. 청크를 닫기 전에 마지막 값을 확정한다."""
        self._wrap_env_dragging = False
        try:
            self._apply_wrap_env(self.dsb_wrap_env.value())
        finally:
            cmds.undoInfo(closeChunk=True)

    # ==============================================================
    # actions : Line Width
    # ==============================================================

    def _width_curves(self):
        """굵기를 바꿀 대상 커브(UUID 로 현재 경로를 되찾아 리네임에 안전)."""
        curves = self.tsl_width.get_all_nodes()
        return curves or self.tsl_width.get_all_items()

    def _apply_width(self, width, log=True):
        """대상 커브에 굵기를 쓴다. (변경 수, 스킵 리스트)"""
        curves = self._width_curves()
        if not curves:
            if log:
                self.log("Curve list is empty. List some curves first.", warn=True)
            return 0, []

        changed, skipped = curve_mgr.set_line_width(curves, width)
        if log:
            self.log("Line width {0} -> {1} curve shape(s).".format(
                "default (-1)" if width < 0 else "{0:.1f}".format(width),
                len(changed)))
            if skipped:
                details = ", ".join("{0} ({1})".format(n.split("|")[-1], why)
                                    for n, why in skipped)
                self.log("Skipped {0}: {1}".format(len(skipped), details),
                         warn=True)
        return len(changed), skipped

    def _set_width_widgets(self, value):
        """슬라이더/스핀박스를 값에 맞춘다(서로 신호를 되쏘지 않게 막고)."""
        for widget, scaled in ((self.sld_width, int(round(value * 10))),
                               (self.dsb_width, value)):
            widget.blockSignals(True)
            widget.setValue(scaled)
            widget.blockSignals(False)

    def _on_width_slider(self, value):
        width = value / 10.0
        self._set_width_widgets(width)
        if self._width_dragging:
            # 드래그 중 — undo 청크가 열려 있고, 커밋/로그는 손을 뗄 때 한 번만 한다.
            self._apply_width(width, log=False)
        else:
            # 화살표 키·홈그루브 클릭처럼 한 번에 끝나는 변경은 그 자리에서 적용.
            with undo_chunk():
                self._apply_width(width)

    def _on_width_spin(self, value):
        # keyboardTracking=False 라 Enter/포커스 아웃에서 한 번 들어온다 = 그 자체로 settle.
        self._set_width_widgets(value)
        with undo_chunk():
            self._apply_width(value)

    def _width_drag_start(self):
        """드래그 시작 — 여기서 연 undo 청크를 놓을 때 닫는다."""
        self._width_dragging = True
        cmds.undoInfo(openChunk=True)

    def _width_drag_end(self):
        """슬라이더에서 손을 떼는 순간이 곧 **자동 적용(commit)** 이다.

        드래그 중에도 라이브로 반영하지만, 마지막 값을 한 번 더 확실히 써서 놓친 이벤트가
        없게 하고 그때만 로그를 남긴다(드래그 내내 로그가 도배되지 않도록). 별도의 Apply
        버튼은 두지 않는다.
        """
        self._width_dragging = False
        # 마지막 값 확정은 **청크를 닫기 전에** 해야 드래그 전체가 undo 한 스텝으로 남는다
        # (닫은 뒤에 쓰면 커밋이 별도 스텝이 되어 Ctrl+Z 를 두 번 눌러야 한다).
        try:
            self._apply_width(self.dsb_width.value())
        finally:
            cmds.undoInfo(closeChunk=True)

    def on_width_get(self):
        curves = self._width_curves()
        if not curves:
            self.log("Curve list is empty. List some curves first.", warn=True)
            return
        width = curve_mgr.get_line_width(curves[0])
        if width is None:
            self.log("Could not read the line width of {0}.".format(
                curves[0].split("|")[-1]), warn=True)
            return
        # -1(마야 기본)은 슬라이더 범위 밖이라 최솟값으로 보여 준다.
        self._set_width_widgets(max(width, curve_mgr.LINE_WIDTH_MIN))
        self.log("{0} line width = {1}{2}".format(
            curves[0].split("|")[-1], width,
            "  (-1 = Maya's global default)" if width < 0 else ""))

    def on_width_reset(self):
        with undo_chunk():
            self._apply_width(curve_mgr.LINE_WIDTH_DEFAULT)

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def log(self, text, warn=False):
        if warn:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(_WARN_COLOR, self._esc(text)))
        else:
            self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Curve Tool\nv{0}  ({1})\n\n"
            "Create one attached curve per connected group of selected mesh edges,\n"
            "then align curve direction by comparing cv[0]/cv[n] on a world axis.\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
