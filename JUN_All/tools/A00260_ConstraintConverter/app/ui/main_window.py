# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-10
# A00260_ConstraintConverter - Qt UI (Maya constraint -> UE Control Rig)
#
# v01.05 : Constraint Type 드롭다운(Parent / Position / Rotation) + 축(X/Y/Z)별 필터
# v01.07 : 비활성 위젯의 흐린 표현을 Framework/styles/*.qss 의 :disabled 규칙으로 이관

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00260_ConstraintConverter.app.config.version import VERSION, LAST_UPDATE
from tools.A00260_ConstraintConverter.app.core import (
    INTERP_TYPES, NODE_TYPE_ORDER, CHANNELS, AXES, node_spec,
)
from tools.A00260_ConstraintConverter.app.core import constraint_reader

# 주의: ConstraintConverter / ConvertOptions 는 모듈 최상단에서 바인딩하지 않고
# on_convert / _collect_options 안에서 '지역 import' 한다. DEV 리로드 시 같은 깊이의
# 모듈 reload 순서 때문에 이 창이 옛 클래스를 잡는 것을 막아, 코드 변경(노드 배치 등)이
# 항상 즉시 반영되게 한다. (launch.py 의 지역 import 패턴과 동일)


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00260_ConstraintConverter_window"

# 비활성(disabled) 위젯의 흐린 표현은 Framework/styles/*.qss 의 :disabled 규칙이 담당한다.
# (v01.05 에서 이 툴에만 두었던 로컬 DISABLED_QSS 를 v01.07 에서 프레임워크로 옮김)


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 460
        self.win_height = 620
        self.win_title  = "Constraint Converter v{0}".format(VERSION)

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 로그 (탭 빌더가 self.log 를 호출할 수 있으므로 먼저 생성)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(90)
        self.te_log.setMaximumHeight(160)

        # -------------------------
        # Constraint 리스트 (TSL)
        # 기본 Select/Add 는 raw 선택을 담으므로 끄고, 컨스트레인트 수집 버튼을 따로 단다.
        # -------------------------
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Constraints",
            show_select=False,
            show_add=False,
            show_del=True,
            show_up=True,
            show_down=True,
            show_sort=True,
            multi_select=True,
            log_callback=self.log,
        )
        # 편집 버튼 행 앞쪽에 컨스트레인트 수집 버튼 추가
        self.tsl.add_button("List from Sel", self.on_list_constraints, index=0)
        self.tsl.add_button("Add from Sel", self.on_add_constraints, index=1)
        main_layout.addWidget(self.tsl)

        # -------------------------
        # 옵션 영역
        # -------------------------
        main_layout.addWidget(self._build_options_group())

        # -------------------------
        # Convert 버튼
        # -------------------------
        self.btn_convert = QPushButton("Convert  ->  Copy to Clipboard")
        self.btn_convert.setMinimumHeight(36)
        self.btn_convert.clicked.connect(self.on_convert)
        main_layout.addWidget(self.btn_convert)

        main_layout.addWidget(self.te_log)

        self.log("Ready. List constraints, set options, then Convert.")

    def _build_options_group(self):
        group = QGroupBox("Convert Options")
        layout = QVBoxLayout(group)

        # Constraint Type 드롭다운 (생성할 UE 노드 종류)
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Constraint Type:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(list(NODE_TYPE_ORDER))
        self.cmb_type.currentTextChanged.connect(self.on_type_changed)
        type_row.addWidget(self.cmb_type)
        type_row.addStretch(1)
        layout.addLayout(type_row)

        # 채널 x 축 필터 그리드 (기본: Translate 만 X/Y/Z 체크)
        # self.cb_axis[(channel, axis)] = QCheckBox / self.lbl_channel[channel] = QLabel
        self.cb_axis = {}
        self.lbl_channel = {}

        grid = QGridLayout()
        grid.addWidget(QLabel("Filter:"), 0, 0)
        for col, axis in enumerate(AXES):
            grid.addWidget(QLabel(axis.upper()), 0, col + 1, Qt.AlignHCenter)

        for row, (channel, label) in enumerate(CHANNELS, start=1):
            lbl = QLabel(label)
            self.lbl_channel[channel] = lbl
            grid.addWidget(lbl, row, 0)
            for col, axis in enumerate(AXES):
                cb = QCheckBox()
                cb.setChecked(channel == "trans")
                self.cb_axis[(channel, axis)] = cb
                grid.addWidget(cb, row, col + 1, Qt.AlignHCenter)
        grid.setColumnStretch(len(AXES) + 1, 1)
        layout.addLayout(grid)

        # Maintain Offset (기본 체크)
        self.cb_maintain = QCheckBox("Maintain Offset")
        self.cb_maintain.setChecked(True)
        layout.addWidget(self.cb_maintain)

        # InterpolationType 드롭다운 (기본 Shortest)
        interp_row = QHBoxLayout()
        self.lbl_interp = QLabel("Interpolation Type:")
        interp_row.addWidget(self.lbl_interp)
        self.cmb_interp = QComboBox()
        self.cmb_interp.addItems(list(INTERP_TYPES))
        default_idx = list(INTERP_TYPES).index("Shortest")
        self.cmb_interp.setCurrentIndex(default_idx)
        interp_row.addWidget(self.cmb_interp)
        interp_row.addStretch(1)
        layout.addLayout(interp_row)

        # 초기 활성/비활성 상태 반영
        self._sync_option_widgets()

        return group

    def _sync_option_widgets(self):
        """선택된 Constraint Type 이 쓰지 않는 채널/옵션 위젯을 비활성화한다.

        - Position 은 Translate 행만, Rotation 은 Rotate 행만 사용한다.
        - Position 노드에는 AdvancedSettings(InterpolationType) 핀 자체가 없다.
        """
        spec = node_spec(self.cmb_type.currentText())
        active = spec["channels"]

        for channel, _label in CHANNELS:
            enabled = channel in active
            self.lbl_channel[channel].setEnabled(enabled)
            for axis in AXES:
                self.cb_axis[(channel, axis)].setEnabled(enabled)

        self.lbl_interp.setEnabled(spec["interp"])
        self.cmb_interp.setEnabled(spec["interp"])

    # --------------------------------------------------
    # 슬롯
    # --------------------------------------------------

    def on_type_changed(self, type_name):
        """Constraint Type 변경: 안 쓰는 채널을 끄고, 쓰는 채널이 전부 꺼져 있으면 켜 준다."""
        self._sync_option_widgets()

        spec = node_spec(type_name)
        for channel in spec["channels"]:
            boxes = [self.cb_axis[(channel, axis)] for axis in AXES]
            if not any(cb.isChecked() for cb in boxes):
                for cb in boxes:
                    cb.setChecked(True)

        self.log("Constraint type: {0} (filter: {1})".format(
            type_name, ", ".join(spec["channels"])))

    def on_list_constraints(self):
        """선택에서 컨스트레인트를 찾아 리스트를 교체."""
        found = constraint_reader.find_constraints_from_selection()
        self.tsl.set_items(found)
        self.log("Listed {0} constraint(s) from selection.".format(len(found)))

    def on_add_constraints(self):
        """선택에서 찾은 컨스트레인트를 중복 없이 추가."""
        found = constraint_reader.find_constraints_from_selection()
        self.tsl.append_unique(found)
        self.log("Added constraint(s) from selection.")

    def on_convert(self):
        nodes = self.tsl.get_all_items()
        if not nodes:
            self.log("No constraints in the list. List some first.")
            return

        options = self._collect_options()

        # 활성 채널의 축이 모두 꺼져 있으면 필터가 전부 false 라 노드가 아무 일도 하지 않는다.
        spec = node_spec(options.constraint_type)
        if not any(any(options.axes(ch)) for ch in spec["channels"]):
            self.log("No axis checked for {0}. Check at least one of X / Y / Z.".format(
                options.constraint_type))
            return

        try:
            # 지역 import: 리로드 후 최신 클래스를 잡는다 (노드 배치 로직 변경 즉시 반영)
            from tools.A00260_ConstraintConverter.app.core.constraint_converter import (
                ConstraintConverter,
            )
            converter = ConstraintConverter()
            combined, infos, out_path = converter.convert(nodes, options)
        except Exception as e:
            self.log("ERROR during convert: {0}".format(e))
            raise

        if not combined:
            self.log("Nothing converted. (No valid targets on the listed nodes.)")
            return

        # 클립보드로 복사 -> UE 그래프에 바로 붙여넣기 (Ctrl+V)
        QApplication.clipboard().setText(combined)

        self.log("-" * 40)
        for name, child, n in infos:
            self.log("  {0} : {1} <- {2} target(s)".format(name, child, n))
        self.log("Converted {0} constraint(s) -> {1} Constraint node(s).".format(
            len(infos), options.constraint_type))
        self.log("Copied to clipboard. Paste into Control Rig graph (Ctrl+V).")
        self.log("Saved: {0}".format(out_path))

    def _collect_options(self):
        # 지역 import: 리로드 후 최신 모듈을 잡는다 (constraint_converter 와 동일 이유)
        from tools.A00260_ConstraintConverter.app.core.node_builder import ConvertOptions

        axis_flags = {
            "{0}_{1}".format(channel, axis): self.cb_axis[(channel, axis)].isChecked()
            for channel, _label in CHANNELS
            for axis in AXES
        }
        return ConvertOptions(
            constraint_type = self.cmb_type.currentText(),
            maintain_offset = self.cb_maintain.isChecked(),
            interp_type     = self.cmb_interp.currentText(),
            **axis_flags
        )

    # --------------------------------------------------
    # 헬퍼
    # --------------------------------------------------

    def log(self, message):
        self.te_log.append(str(message))

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Constraint Converter\n"
            "Version {0}\n"
            "Last Update {1}\n\n"
            "Maya constraint -> UE Control Rig\n"
            "Parent / Position / Rotation Constraint node.".format(
                VERSION, LAST_UPDATE
            ),
        )
