# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00390_WindTool_V03 - "Flow" 탭 (Qt)
#
# Waves Gen(블렌더) 식 바람 - 기울기 + 두 축 진행파 + 불규칙성 + 끝 따라가기. 코어는 app/core/flow_manager.
# 체인 목록 · 모드(Bone Chain / Bone Root)는 메인 창 것을 같이 쓴다(get_nodes / is_root_mode 콜러블).
#
# 값은 두 벌: Option 1 (드라이버 *A) / Option 2 (*B). Mix 0 -> 1 로 섞인다 - 셋 다 키 가능, 재생 중에도 라이브.
# 칸을 바꾸면 **대상 드라이버에 바로** 쓴다(Live Edit). 대상 = 선택한 Flow 드라이버(체인 노드 · Tip 선택도 됨), 없으면 씬 전체.
# 빌드할 때는 이 칸 값이 새 드라이버의 시작 값이 된다.
#
# UI 문자열은 영어, 주석은 한국어.

import maya.cmds as cmds

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QSlider,
    QButtonGroup,
)
from Framework.core.maya_undo import undo_chunk

from ..core import flow_manager as fmg
from ..core import flow_presets as fp

_PRESET_QSS = "QPushButton:checked { background-color: #3d6fa8; color: white; font-weight: bold; }"


class FlowTab(QWidget):

    def __init__(self, get_nodes, is_root_mode, log, on_built=None):
        super().__init__()
        self._get_nodes = get_nodes
        self._is_root_mode = is_root_mode
        self._log = log
        self._on_built = on_built
        self._loading = True            # 만드는 동안 칸 초기값 설정이 드라이버에 쓰지 않게
        self._build_ui()
        self._loading = False
        self._apply_values_to_ui(fp.option("Breeze", 0), fp.option("Breeze", 1), 0.0)

    # ============================================================== build

    def _spin(self, lo, hi, step, decimals=3, tip=""):
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setSingleStep(step)
        sb.setDecimals(decimals)
        sb.setKeyboardTracking(False)
        if tip:
            sb.setToolTip(tip)
        return sb

    def _build_ui(self):
        lay = QVBoxLayout(self)
        note = QLabel(
            "Wind with a steady lean, a wave travelling down the chain, sideways sway,\n"
            "gusts and Tip Follow (same motion as the Blender add-on Waves Gen).\n"
            "Every value lives on the driver and can be keyed - Mix blends Option 1 -> 2.")
        lay.addWidget(note)

        # ---- 프리셋
        pre_box = QGroupBox("Preset")
        pre = QVBoxLayout(pre_box)
        row = QHBoxLayout()
        self.preset_buttons = {}
        self.preset_group = QButtonGroup(self)
        self.preset_group.setExclusive(False)       # 어느 것도 안 맞을 때 전부 꺼야 한다
        for name in fp.PRESET_ORDER:
            b = QPushButton(name)
            b.setCheckable(True)
            b.setStyleSheet(_PRESET_QSS)
            b.setToolTip("Load '{0}' into Option 1 / Option 2 (and into the target drivers).\n"
                         "Blue = the values match this preset.".format(name))
            b.clicked.connect(lambda _c=False, n=name: self.on_preset(n))
            self.preset_group.addButton(b)
            self.preset_buttons[name] = b
            row.addWidget(b)
        pre.addLayout(row)

        mix_row = QHBoxLayout()
        self.btn_opt1 = QPushButton("Option 1")
        self.btn_opt1.setToolTip("Mix = 0 (Option 1 values).")
        self.btn_opt1.clicked.connect(lambda: self.on_mix_set(0.0))
        self.btn_opt2 = QPushButton("Option 2")
        self.btn_opt2.setToolTip("Mix = 1 (Option 2 values).")
        self.btn_opt2.clicked.connect(lambda: self.on_mix_set(1.0))
        mix_row.addWidget(self.btn_opt1)
        mix_row.addWidget(self.btn_opt2)
        mix_row.addWidget(QLabel("Mix"))
        self.sl_mix = QSlider(Qt.Horizontal)
        self.sl_mix.setRange(0, 100)
        self.sl_mix.setToolTip("Blend Option 1 -> Option 2 live (flowMix on the driver, keyable).")
        self.sl_mix.valueChanged.connect(self._on_mix_slider)
        mix_row.addWidget(self.sl_mix, 1)
        self.sb_mix = self._spin(0.0, 1.0, 0.05, 3, "flowMix: 0 = Option 1, 1 = Option 2.")
        self.sb_mix.valueChanged.connect(self._on_mix_spin)
        mix_row.addWidget(self.sb_mix)
        self.btn_key_mix = QPushButton("Key Mix")
        self.btn_key_mix.setToolTip("Set a key on flowMix at the current frame (animate calm -> gusty).")
        self.btn_key_mix.clicked.connect(self.on_key_mix)
        mix_row.addWidget(self.btn_key_mix)
        pre.addLayout(mix_row)
        lay.addWidget(pre_box)

        # ---- 값 (옵션 1 / 2)
        val_box = QGroupBox("Wind (Option 1 | Option 2)")
        grid = QGridLayout(val_box)
        grid.addWidget(QLabel(""), 0, 0)
        grid.addWidget(QLabel("Option 1"), 0, 1)
        grid.addWidget(QLabel("Option 2"), 0, 2)
        self.sb_a, self.sb_b = {}, {}
        for r, p in enumerate(fp.PARAMS, start=1):
            lo, hi = fp.LIMITS[p]
            lbl = QLabel(fp.LABELS[p])
            lbl.setToolTip(fp.TOOLTIPS[p])
            grid.addWidget(lbl, r, 0)
            step = 0.05 if hi <= 1.0 else 0.5
            for col, store, attr_fn in ((1, self.sb_a, fmg.a_attr), (2, self.sb_b, fmg.b_attr)):
                sb = self._spin(lo, hi, step, 3, fp.TOOLTIPS[p])
                sb.valueChanged.connect(lambda v, pp=p, fn=attr_fn: self._on_value(fn(pp), v))
                store[p] = sb
                grid.addWidget(sb, r, col)
        btn_same = QPushButton("Option 2 = Option 1")
        btn_same.setToolTip("Copy every Option 1 value into Option 2 (Mix then changes nothing).")
        btn_same.clicked.connect(self.on_copy_a_to_b)
        grid.addWidget(btn_same, len(fp.PARAMS) + 1, 1, 1, 2)
        lay.addWidget(val_box)

        # ---- 공통 값
        com_box = QGroupBox("Shared")
        cg = QGridLayout(com_box)
        self.sb_dir = self._spin(-360.0, 360.0, 5.0, 2, "Direction the wind blows around the chain (degrees, live).")
        self.sb_env = self._spin(0.0, 1.0, 0.05, 3, "windEnvelope: 0 = no wind (rest pose), 1 = full (live).")
        self.sb_time = self._spin(0.0, 10.0, 0.1, 3, "flowTimeScale: playback speed of the wind (1 = normal, key it "
                                                     "to slow down / speed up - integrated, never runs backward).")
        self.sb_offset = self._spin(-500.0, 500.0, 1.0, 2, "flowChainOffset: frames of delay between chains "
                                                           "(Bone Root mode) so they do not move in step.")
        self.sb_vary = self._spin(0.0, 1.0, 0.05, 3, "flowVariation: rhythm / wavelength / size differences between "
                                                     "chains (0 = all the same).")
        for k, (lbl, sb, attr) in enumerate((("Direction", self.sb_dir, fmg.FLOW_DIR),
                                             ("Envelope", self.sb_env, "windEnvelope"),
                                             ("Time Scale", self.sb_time, fmg.FLOW_TIME_SCALE),
                                             ("Chain Offset", self.sb_offset, fmg.FLOW_CHAIN_OFFSET),
                                             ("Variation", self.sb_vary, fmg.FLOW_VARIATION))):
            cg.addWidget(QLabel(lbl), k // 2, (k % 2) * 2)
            cg.addWidget(sb, k // 2, (k % 2) * 2 + 1)
            sb.valueChanged.connect(lambda v, a=attr: self._on_value(a, v, plain=True))
        self.sb_env.setValue(1.0)
        self.sb_time.setValue(1.0)
        self.sb_offset.setValue(14.0)
        self.sb_vary.setValue(1.0)
        lay.addWidget(com_box)

        # ---- 빌드
        bld_box = QGroupBox("Build")
        bg = QGridLayout(bld_box)
        bg.addWidget(QLabel("Wind Axis"), 0, 0)
        self.cmb_axis = QComboBox()
        self.cmb_axis.addItems(fmg.WIND_AXES)
        self.cmb_axis.setToolTip("World axis that sets 'Direction 0'.\n"
                                 "Auto = world X, or world Y when the chain itself runs along X.")
        bg.addWidget(self.cmb_axis, 0, 1)
        self.chk_tip = QCheckBox("Tip Follow")
        self.chk_tip.setChecked(True)
        self.chk_tip.setToolTip("Every bone turns toward a Tip locator past the chain end ('Tip Follow' value).\n"
                                "Needed for the presets to look like Waves Gen. Move the Tip for secondary motion.\n"
                                "Off = wind only (lighter).")
        bg.addWidget(self.chk_tip, 0, 2)
        self.chk_live = QCheckBox("Live Edit")
        self.chk_live.setChecked(True)
        self.chk_live.setToolTip("On: editing a value writes it to the target drivers at once\n"
                                 "(selected Flow driver / its chain / Tip, else every Flow driver in the scene).\n"
                                 "A keyed attribute gets a key at the current frame instead.")
        bg.addWidget(self.chk_live, 0, 3)
        self.btn_build = QPushButton("Build Flow")
        self.btn_build.setMinimumHeight(34)
        self.btn_build.clicked.connect(self.on_build)
        self.btn_remove = QPushButton("Remove Flow")
        self.btn_remove.clicked.connect(self.on_remove)
        self.btn_load = QPushButton("Load From Driver")
        self.btn_load.setToolTip("Read the values of the selected (or first) Flow driver into this tab.")
        self.btn_load.clicked.connect(self.on_load)
        self.btn_sel = QPushButton("Select Driver")
        self.btn_sel.clicked.connect(lambda: self._select(tips=False))
        self.btn_tips = QPushButton("Select Tips")
        self.btn_tips.clicked.connect(lambda: self._select(tips=True))
        bg.addWidget(self.btn_build, 1, 0, 1, 2)
        bg.addWidget(self.btn_remove, 1, 2, 1, 2)
        bg.addWidget(self.btn_load, 2, 0, 1, 2)
        bg.addWidget(self.btn_sel, 2, 2)
        bg.addWidget(self.btn_tips, 2, 3)
        lay.addWidget(bld_box)
        lay.addStretch(1)

    # ============================================================== 값 <-> UI

    def ui_values(self):
        a = {p: self.sb_a[p].value() for p in fp.PARAMS}
        b = {p: self.sb_b[p].value() for p in fp.PARAMS}
        return a, b, self.sb_mix.value()

    def _apply_values_to_ui(self, a, b, mix, other=None):
        self._loading = True
        try:
            for p in fp.PARAMS:
                self.sb_a[p].setValue(a[p])
                self.sb_b[p].setValue(b[p])
            self.sb_mix.setValue(mix)
            self.sl_mix.setValue(int(round(mix * 100)))
            if other:
                self.sb_dir.setValue(other.get(fmg.FLOW_DIR, 0.0))
                self.sb_env.setValue(other.get("windEnvelope", 1.0))
                self.sb_time.setValue(other.get(fmg.FLOW_TIME_SCALE, 1.0))
                self.sb_offset.setValue(other.get(fmg.FLOW_CHAIN_OFFSET, 0.0))
                self.sb_vary.setValue(other.get(fmg.FLOW_VARIATION, 0.0))
        finally:
            self._loading = False
        self._refresh_preset_buttons()

    def _refresh_preset_buttons(self):
        a, b, _m = self.ui_values()
        match = fp.matching_preset(a, b)
        for name, btn in self.preset_buttons.items():
            btn.setChecked(name == match)

    def _targets(self):
        try:
            return fmg.selected_flow_drivers()
        except Exception:  # noqa: BLE001
            return []

    # ============================================================== 핸들러

    def _on_value(self, attr, value, plain=False):
        if self._loading:
            return
        self._refresh_preset_buttons()
        if not self.chk_live.isChecked():
            return
        drivers = self._targets()
        if drivers:
            fmg.set_plain(drivers, attr, value)
            if attr.endswith("A") or attr.endswith("B"):
                for d in drivers:
                    cmds.setAttr(d + "." + fmg.FLOW_PRESET, "", type="string")

    def _on_mix_slider(self, v):
        if self._loading:
            return
        self._loading = True
        self.sb_mix.setValue(v / 100.0)
        self._loading = False
        self._write_mix(v / 100.0)

    def _on_mix_spin(self, v):
        if self._loading:
            return
        self._loading = True
        self.sl_mix.setValue(int(round(v * 100)))
        self._loading = False
        self._write_mix(v)

    def _write_mix(self, v):
        if self.chk_live.isChecked():
            drivers = self._targets()
            if drivers:
                fmg.set_plain(drivers, fmg.FLOW_MIX, v)

    def on_mix_set(self, v):
        self.sb_mix.setValue(v)

    def on_key_mix(self):
        drivers = self._targets()
        if not drivers:
            self._log("No Flow driver in the scene.", warn=True)
            return
        with undo_chunk():
            t = cmds.currentTime(q=True)
            for d in drivers:
                cmds.setKeyframe(d, attribute=fmg.FLOW_MIX, value=self.sb_mix.value(),
                                 inTangentType="linear", outTangentType="linear")
                # 이미 있던 키 위에 찍으면 탄젠트가 안 바뀐다 - 직접 linear 로(위상 엔진은 키 사이를 직선으로 적분)
                cmds.keyTangent(d, attribute=fmg.FLOW_MIX, time=(t, t), inTangentType="linear",
                                outTangentType="linear")
        self._log("flowMix keyed at frame {0:g} = {1:.3f} on {2} driver(s). Keys use linear tangents "
                  "(the phase engine integrates between keys as straight lines).".format(
                      cmds.currentTime(q=True), self.sb_mix.value(), len(drivers)))

    def on_preset(self, name):
        o1, o2 = fp.option(name, 0), fp.option(name, 1)
        self._apply_values_to_ui(o1, o2, self.sb_mix.value())
        if self.chk_live.isChecked():
            drivers = self._targets()
            if drivers:
                with undo_chunk():
                    fmg.apply_preset(drivers, name)
                self._log("Preset '{0}' -> Option 1 / 2 on {1} driver(s). Mix stays {2:.2f}.".format(
                    name, len(drivers), self.sb_mix.value()))
                return
        self._log("Preset '{0}' loaded - Build Flow to use it.".format(name))

    def on_copy_a_to_b(self):
        for p in fp.PARAMS:
            self.sb_b[p].setValue(self.sb_a[p].value())

    def on_build(self):
        nodes = self._get_nodes()
        if not nodes:
            self._log("Joint list is empty. Select joints and click 'Select Joints'.", warn=True)
            return
        a, b, mix = self.ui_values()
        match = fp.matching_preset(a, b)
        with undo_chunk():
            try:
                built, drv, msg = fmg.build_flow(
                    nodes, mode=fmg.MODE_ROOT if self._is_root_mode() else fmg.MODE_CHAIN,
                    preset=None, opt_a=a, opt_b=b, mix=mix, direction=self.sb_dir.value(),
                    envelope=self.sb_env.value(), chain_offset=self.sb_offset.value(),
                    variation=self.sb_vary.value(), time_scale=self.sb_time.value(),
                    tip_follow=self.chk_tip.isChecked(), wind_axis=self.cmb_axis.currentText())
                if drv and match:
                    cmds.setAttr(drv + "." + fmg.FLOW_PRESET, match, type="string")
            except Exception as exc:  # noqa: BLE001
                self._log("[Error] {0}".format(exc), warn=True)
                cmds.warning(str(exc))
                return
        self._log(msg, warn=msg.startswith("[Warning]"))
        if drv:
            cmds.select(drv)
        if self._on_built:
            self._on_built()

    def on_remove(self):
        with undo_chunk():
            try:
                _n, msg = fmg.remove_flow()
            except Exception as exc:  # noqa: BLE001
                self._log("[Error] {0}".format(exc), warn=True)
                return
        self._log(msg, warn=msg.startswith("[Warning]"))

    def on_load(self):
        drivers = self._targets()
        if not drivers:
            self._log("No Flow driver in the scene.", warn=True)
            return
        a, b, mix, _e, other = fmg.driver_values(drivers[0])
        self._apply_values_to_ui(a, b, mix, other)
        self._log("Loaded values from '{0}'.".format(drivers[0].split("|")[-1]))

    def _select(self, tips):
        drivers = self._targets()
        if not drivers:
            self._log("No Flow driver in the scene.", warn=True)
            return
        if not tips:
            cmds.select(drivers)
            return
        out = []
        for st in cmds.ls("*" + fmg.FLOW_SET_SUFFIX) or []:
            for m in cmds.sets(st, q=True) or []:
                if fmg.FLOW_TIP_SUFFIX in m:
                    out.append(m)
        if out:
            cmds.select(out)
        else:
            self._log("No Tip locator (built without Tip Follow?).", warn=True)
