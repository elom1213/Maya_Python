# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00390_WindTool_V03 core - **Flow** 모드 : Waves Gen 식 바람(기울기 + 두 축 진행파 + 불규칙성 + 끝 따라가기)을
#                            마야 노드망으로 라이브 구동한다. (UI 비의존)
#
# 계획서 docs/plans/A00390_WindTool_wavesgen_port_plan.md. 수식은 flow_model(순수 파이썬 기준 모델)과 같고,
# 그 모델은 블렌더 Waves Gen 기준 데이터와 12/12 일치한다(tests/test_flow_golden.py).
#
# ## 무엇을 만드나 (빌드 하나)
#
#   드라이버 로케이터 1개   <prefix>_flowDriver   - 모든 값(옵션 A/B · Mix · 방향 · envelope ...)이 여기 있다, 전부 라이브
#   체인마다 Tip 로케이터   <chain>_flowTip        - 끝 따라가기 목표. 루트의 부모 아래(리그와 같이 움직인다), 움직여서 2차 애니
#   뼈마다 노드망           sin 6 (eulerToQuat) + 산술 + 쿼터니언 -> quatToEuler -> rotate
#   위상 엔진 표현식 1개    flowPhaseEngine        - 씬의 모든 Flow 드라이버의 위상 = ∫ timeScale * speed(Mix) dt
#
# ## 뼈 = 자식이 있는 노드
#
# 체인 [n0 .. nm] 에서 n0..n(m-1) 이 회전하는 뼈다(블렌더 뼈 = 머리 + 꼬리, 꼬리 = 다음 노드). 끝 노드는 rest 그대로.
# 뼈의 진행축 = 다음 노드 방향(로컬), 바람 두 축 p1 · p2 는 그에 수직 - p2 = 기준 월드 축(Wind Axis)을 뼈 평면에 투영,
# p1 = 진행축 x p2 (블렌더 뼈의 Y 진행 · X / Z 와 같은 손 방향).
#
# ## 회전 합성 (Maya 행벡터 규약 - quatProd(a, b) = a 다음 b, mayapy 로 확인)
#
#   q_wind  = qP1(rx) 다음 qP2(rz)                 (블렌더 오일러 XYZ: X 먼저)
#   q_rot   = q_wind 다음 q_rest                    (바람은 rest 로컬 축에서 먼저)
#   끝 따라가기:
#     q_par = q_rot 다음 q_JO                       (부모 공간 방향)
#     a_par = 진행축 x matrix(q_par),  t_par = (Tip 의 부모 공간 위치) - translate
#     q_dt  = angleBetween(a_par, t_par) -> axisAngleToQuat     (블렌더 Damped Track = 최소 회전)
#     q_aim = q_par 다음 q_dt 다음 q_JO^-1
#     q_out = slerp(q_rot, q_aim, w_i)              (블렌더 제약 influence 섞기와 같다)
#   rotate = quatToEuler(q_out, 노드 rotateOrder)
#
# ## sin 은 eulerToQuat 로 (정확)
#
# eulerToQuat(rotateX = 2θ).outputQuatX = sin θ, .outputQuatW = cos θ. V03 의 16샘플 LUT(근사) 대신 이것을 써서
# 노드망 = 순수 모델이 1e-9 로 맞는다. 각도 입력은 도 단위 값을 unitConversion(π/180)으로 직접 넣는다(UI 단위 무관).

import json
import math

import maya.cmds as cmds
from maya.api import OpenMaya as om

from . import flow_model as fm
from . import flow_presets as fp
from .wind_manager import DRIVER_ENVELOPE, MODE_CHAIN, MODE_ROOT, _leaf, _safe, follow_root_position
from .wave_manager import resolve_chains

# ---------------------------------------------------------------- 이름

FLOW_MARK = "flowDriver"
FLOW_MIX = "flowMix"
FLOW_DIR = "flowDirection"
FLOW_TIME_SCALE = "flowTimeScale"
FLOW_CHAIN_OFFSET = "flowChainOffset"
FLOW_VARIATION = "flowVariation"
FLOW_PHASE = "flowPhase"
FLOW_RATE = "flowRate"
FLOW_PRESET = "flowPreset"
FLOW_FPS_SCALE = "flowFpsScale"
FLOW_ENGINE = "flowPhaseEngine"
FLOW_SET_SUFFIX = "_flowSET"
FLOW_REST_ATTR = "flowRestRotate"
FLOW_TIP_SUFFIX = "_flowTip"

PARAMS = fp.PARAMS
WIND_AXES = ("Auto", "X", "Y", "Z")

_DEG2 = 360.0 / math.pi           # 2θ(라디안) -> 도: eulerToQuat 에 2θ 를 도로 넣는다


def eff_attr(p):
    return "flow" + p[0].upper() + p[1:]


def a_attr(p):
    return eff_attr(p) + "A"


def b_attr(p):
    return eff_attr(p) + "B"


# ---------------------------------------------------------------- 노드 도우미

def _plugin():
    if not cmds.pluginInfo("quatNodes", query=True, loaded=True):
        cmds.loadPlugin("quatNodes", quiet=True)


class _Net(object):
    """만든 노드를 모으며 이름을 붙이는 작은 도우미."""

    def __init__(self, tag):
        self.tag = tag
        self.made = []

    def node(self, ntype, suffix):
        n = cmds.createNode(ntype, name="{0}_{1}".format(self.tag, suffix))
        self.made.append(n)
        return n

    def mdl(self, a, b, suffix):
        """a * b (plug 또는 상수)."""
        n = self.node("multDoubleLinear", suffix)
        _feed(a, n + ".input1")
        _feed(b, n + ".input2")
        return n + ".output"

    def adl(self, a, b, suffix):
        n = self.node("addDoubleLinear", suffix)
        _feed(a, n + ".input1")
        _feed(b, n + ".input2")
        return n + ".output"

    def pma(self, items, suffix, op=1):
        """합(op 1) / 차(op 2). items = plug 또는 상수."""
        n = self.node("plusMinusAverage", suffix)
        cmds.setAttr(n + ".operation", op)
        for k, it in enumerate(items):
            _feed(it, "{0}.input1D[{1}]".format(n, k))
        return n + ".output1D"

    def div(self, a, b, suffix):
        n = self.node("multiplyDivide", suffix)
        cmds.setAttr(n + ".operation", 2)
        _feed(a, n + ".input1X")
        _feed(b, n + ".input2X")
        return n + ".outputX"

    def pow(self, a, b, suffix):
        n = self.node("multiplyDivide", suffix)
        cmds.setAttr(n + ".operation", 3)
        _feed(a, n + ".input1X")
        _feed(b, n + ".input2X")
        return n + ".outputX"

    def deg_in(self, src, dst, suffix):
        """도 단위 double -> 각도 어트리뷰트 (unitConversion π/180 을 직접)."""
        uc = self.node("unitConversion", suffix)
        cmds.setAttr(uc + ".conversionFactor", math.pi / 180.0)
        _feed(src, uc + ".input")
        cmds.connectAttr(uc + ".output", dst, force=True)

    def sin2(self, arg_deg2, suffix):
        """sin θ  (arg_deg2 = 2θ 를 도로 표현한 plug). eulerToQuat 하나."""
        e = self.node("eulerToQuat", suffix)
        self.deg_in(arg_deg2, e + ".inputRotateX", suffix + "Uc")
        return e


def _feed(value, dst):
    if isinstance(value, str):
        cmds.connectAttr(value, dst, force=True)
    else:
        cmds.setAttr(dst, float(value))


def _set_quat(plug_prefix, q):
    for c, v in zip("XYZW", (q.x, q.y, q.z, q.w)):
        cmds.setAttr(plug_prefix + c, v)


def _quat_prod(net, a, b, suffix):
    """a 다음 b. a, b = 노드 이름(outputQuat 를 가진) 또는 MQuaternion 상수."""
    n = net.node("quatProd", suffix)
    for slot, q in ((1, a), (2, b)):
        if isinstance(q, om.MQuaternion):
            _set_quat("{0}.input{1}Quat".format(n, slot), q)
        else:
            cmds.connectAttr(q + ".outputQuat", "{0}.input{1}Quat".format(n, slot), force=True)
    return n


# ---------------------------------------------------------------- 드라이버

def _add_double(node, attr, value, keyable=True, mn=None, mx=None, channel_box=None):
    kw = {"longName": attr, "attributeType": "double", "defaultValue": float(value), "keyable": keyable}
    if mn is not None:
        kw["minValue"] = mn
    if mx is not None:
        kw["maxValue"] = mx
    cmds.addAttr(node, **kw)
    if not keyable and channel_box is not None:
        cmds.setAttr(node + "." + attr, channelBox=channel_box)
    cmds.setAttr(node + "." + attr, float(value))


def _make_driver(name, opt_a, opt_b, mix, direction, envelope, chain_offset, variation,
                 time_scale, preset_name, place_at=None):
    drv = cmds.spaceLocator(name=name)[0]
    if place_at is not None:
        cmds.xform(drv, worldSpace=True, translation=place_at)
    cmds.addAttr(drv, longName=FLOW_MARK, attributeType="bool", defaultValue=True)
    cmds.setAttr(drv + "." + FLOW_MARK, True)
    cmds.addAttr(drv, longName=FLOW_PRESET, dataType="string")
    cmds.setAttr(drv + "." + FLOW_PRESET, preset_name or "", type="string")

    _add_double(drv, FLOW_MIX, mix, mn=0.0, mx=1.0)
    for p in PARAMS:
        lo, hi = fp.LIMITS[p]
        _add_double(drv, a_attr(p), opt_a[p], mn=lo, mx=hi)
        _add_double(drv, b_attr(p), opt_b[p], mn=lo, mx=hi)
    _add_double(drv, FLOW_DIR, direction)
    _add_double(drv, DRIVER_ENVELOPE, envelope, mn=0.0, mx=1.0)
    _add_double(drv, FLOW_TIME_SCALE, time_scale, mn=0.0)
    _add_double(drv, FLOW_CHAIN_OFFSET, chain_offset)
    _add_double(drv, FLOW_VARIATION, variation, mn=0.0, mx=1.0)
    # 실효 값(Mix 로 섞인 것) - 표시만, 키 불가
    for p in PARAMS:
        _add_double(drv, eff_attr(p), opt_a[p], keyable=False, channel_box=True)
    _add_double(drv, FLOW_PHASE, 0.0, keyable=False, channel_box=False)
    _add_double(drv, FLOW_RATE, 0.0, keyable=False, channel_box=False)
    _add_double(drv, FLOW_FPS_SCALE, 24.0 / _scene_fps(), keyable=False, channel_box=False)

    made = []
    tag = _safe(_leaf(drv))
    for p in PARAMS:
        bl = cmds.createNode("blendTwoAttr", name="{0}_{1}Mix".format(tag, p))
        cmds.connectAttr(drv + "." + a_attr(p), bl + ".input[0]")
        cmds.connectAttr(drv + "." + b_attr(p), bl + ".input[1]")
        cmds.connectAttr(drv + "." + FLOW_MIX, bl + ".attributesBlender")
        cmds.connectAttr(bl + ".output", drv + "." + eff_attr(p), force=True)
        made.append(bl)
    return drv, made


_FPS = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0, "show": 48.0, "palf": 50.0, "ntscf": 60.0}


def _scene_fps():
    unit = cmds.currentUnit(query=True, time=True)
    if unit in _FPS:
        return _FPS[unit]
    try:
        return float(unit.replace("fps", ""))
    except ValueError:
        return 24.0


# ---------------------------------------------------------------- 위상 엔진

def flow_drivers():
    out = []
    for node in (cmds.ls(type="transform", long=True) or []):
        if cmds.objExists(node + "." + FLOW_MARK):
            out.append(node)
    return out


_CONTRIB = (("W", FLOW_TIME_SCALE), ("SA", a_attr("speed")), ("SB", b_attr("speed")), ("M", FLOW_MIX))


def _mel_eval_f(i, x, out):
    """$x 에서 피적분 f = W * (SA + (SB - SA) * M) 을 계산해 $out 에 넣는 MEL.

    곡선마다 키 사이를 **직선**으로 본다(V03 엔진과 같은 가정). 키가 없으면 어트리뷰트 값(상수)."""
    lines = []
    for key, _attr in _CONTRIB:
        v = "${0}{1}x".format(key, i)
        t, val, n, s = "$t{0}{1}".format(key, i), "$v{0}{1}".format(key, i), "$n{0}{1}".format(key, i), \
            "$s{0}{1}".format(key, i)
        lines.append(
            "{v} = {s};\n"
            "if ({n} > 0) {{\n"
            "  if ({x} <= {t}[0]) {v} = {val}[0];\n"
            "  else if ({x} >= {t}[{n} - 1]) {v} = {val}[{n} - 1];\n"
            "  else {{ for ($j{key}{i} = 0; $j{key}{i} < {n} - 1; $j{key}{i}++) {{\n"
            "    if ({x} <= {t}[$j{key}{i} + 1]) {{\n"
            "      {v} = {val}[$j{key}{i}] + ({val}[$j{key}{i} + 1] - {val}[$j{key}{i}]) * ({x} - {t}[$j{key}{i}])"
            " / ({t}[$j{key}{i} + 1] - {t}[$j{key}{i}]);\n"
            "      break; }} }} }}\n"
            "}}\n".format(v=v, s=s, n=n, x=x, t=t, val=val, key=key, i=i))
    lines.append("{out} = $W{i}x * ($SA{i}x + ($SB{i}x - $SA{i}x) * $M{i}x);\n".format(out=out, i=i))
    return "".join(lines)


def _driver_snippet(i, drv, fps_scale):
    """드라이버 하나의 위상: flowPhase = K * ∫_0^frame f dt,  flowRate = K * f(frame).

    키 시각 전부를 경계로 나누면 구간 안에서 W · SA · SB · M 이 모두 직선 -> f 는 3차 이하 -> Simpson 이 **정확**하다.
    상수만이면 f 가 상수라 flowPhase = K * f * frame (블렌더 Waves Gen 의 '프레임 x 속도' 와 같다)."""
    head = []
    for key, attr in _CONTRIB:
        head.append("float $s{k}{i} = {d}.{a};\n"
                    "float $t{k}{i}[] = `keyframe -q -timeChange {d}.{a}`;\n"
                    "float $v{k}{i}[] = `keyframe -q -valueChange {d}.{a}`;\n"
                    "int $n{k}{i} = size($t{k}{i});\n"
                    "int $j{k}{i};\n"
                    "float ${k}{i}x;\n".format(k=key, i=i, d=drv, a=attr))
    body = (
        "float $cf{i} = frame;\n"
        "float $lo{i} = ($cf{i} < 0) ? $cf{i} : 0.0;\n"
        "float $hi{i} = ($cf{i} < 0) ? 0.0 : $cf{i};\n"
        "float $bp{i}[] = {{$lo{i}, $hi{i}}};\n"
    ).format(i=i)
    for key, _attr in _CONTRIB:
        body += ("int $q{k}{i}; for ($q{k}{i} = 0; $q{k}{i} < $n{k}{i}; $q{k}{i}++) {{\n"
                 "  if ($t{k}{i}[$q{k}{i}] > $lo{i} && $t{k}{i}[$q{k}{i}] < $hi{i}) $bp{i}[size($bp{i})] = $t{k}{i}[$q{k}{i}];\n"
                 "}}\n").format(k=key, i=i)
    body += (
        "$bp{i} = sort($bp{i});\n"
        "float $acc{i} = 0.0;\n"
        "float $x{i}; float $fa{i}; float $fm{i}; float $fb{i};\n"
        "int $g{i}; for ($g{i} = 0; $g{i} < size($bp{i}) - 1; $g{i}++) {{\n"
        "  float $a{i} = $bp{i}[$g{i}]; float $b{i} = $bp{i}[$g{i} + 1];\n"
        "  if ($b{i} - $a{i} <= 0) continue;\n"
        "  $x{i} = $a{i};\n"
    ).format(i=i)
    body += _mel_eval_f(i, "$x{0}".format(i), "$fa{0}".format(i))
    body += "  $x{i} = 0.5 * ($a{i} + $b{i});\n".format(i=i)
    body += _mel_eval_f(i, "$x{0}".format(i), "$fm{0}".format(i))
    body += "  $x{i} = $b{i};\n".format(i=i)
    body += _mel_eval_f(i, "$x{0}".format(i), "$fb{0}".format(i))
    body += ("  $acc{i} += ($b{i} - $a{i}) / 6.0 * ($fa{i} + 4.0 * $fm{i} + $fb{i});\n"
             "}}\n"
             "if ($cf{i} < 0) $acc{i} = -$acc{i};\n"
             "$x{i} = $cf{i};\n").format(i=i)
    body += _mel_eval_f(i, "$x{0}".format(i), "$fb{0}".format(i))
    body += ("{d}.{ph} = {K!r} * $acc{i};\n"
             "{d}.{rate} = {K!r} * $fb{i};\n").format(d=drv, ph=FLOW_PHASE, rate=FLOW_RATE, K=float(fps_scale), i=i)
    return "".join(head) + body


def wire_flow_phase():
    """씬의 모든 Flow 드라이버의 위상 엔진(표현식 하나)을 다시 만든다. 드라이버 수를 돌려준다.

    표현식은 어트리뷰트를 **직접 읽어** 입력 연결이 생긴다 - Mix · speed 를 바꾸면 멈춘 상태에서도 다시 계산된다.
    키는 keyframe -q 로 데이터만 읽어(DG 평가 없음) 비용이 프레임 번호와 무관하다(V03 엔진과 같은 원리)."""
    if cmds.objExists(FLOW_ENGINE):
        cmds.delete(FLOW_ENGINE)
    drivers = flow_drivers()
    if not drivers:
        return 0
    body = "".join(_driver_snippet(i, d, cmds.getAttr(d + "." + FLOW_FPS_SCALE)) for i, d in enumerate(drivers))
    cmds.expression(string=body, alwaysEvaluate=True, unitConversion="none", name=FLOW_ENGINE)
    return len(drivers)


# ---------------------------------------------------------------- 체인

def _world_rot(node):
    m = om.MMatrix(cmds.xform(node, query=True, worldSpace=True, matrix=True))
    return om.MTransformationMatrix(m).rotation(asQuaternion=True)


def _local_vec(node, world_vec):
    """월드 방향 -> 노드 로컬 방향(행벡터: local = world * R^-1)."""
    q = _world_rot(node)
    return om.MVector(world_vec).rotateBy(q.inverse())


def _ref_axis(chain, wind_axis):
    p0 = om.MVector(*cmds.xform(chain[0], q=True, ws=True, t=True))
    p1 = om.MVector(*cmds.xform(chain[-1], q=True, ws=True, t=True))
    d = (p1 - p0).normal()
    if wind_axis in ("X", "Y", "Z"):
        v = om.MVector(0, 0, 0)
        v["XYZ".index(wind_axis)] = 1.0
        return v
    # Auto: Waves Gen 과 같다 - 체인이 X 쪽이 아니면 월드 X, X 쪽이면 월드 Y
    return om.MVector(1, 0, 0) if abs(d.x) < 0.9 else om.MVector(0, 1, 0)


def _rotate_inputs(node):
    plugs = [node + "." + a for a in ("rotate", "rotateX", "rotateY", "rotateZ")]
    return [p for p in plugs if cmds.listConnections(p, source=True, destination=False)]


def _build_chain(drv, chain, chain_index, tip_follow, wind_axis, net_tag):
    """체인 하나. (만든 노드, rest dict, tip, 사유 or None)."""
    bones = chain[:-1]
    n = len(bones)
    if n < 1:
        return [], {}, None, "needs 2+ nodes"
    busy = [_leaf(b) for b in bones if _rotate_inputs(b)]
    if busy:
        return [], {}, None, "rotate already driven / keyed on {0}".format(", ".join(busy[:3]))

    net = _Net(net_tag)
    rest = {}
    ref_w = _ref_axis(chain, wind_axis)
    k0 = fm.k0_of(n)
    pos = [om.MVector(*cmds.xform(c, q=True, ws=True, t=True)) for c in chain]

    # ★ 축은 **연결하기 전에 전부** 구한다. 루프 안에서 구하면 앞 뼈가 이미 바람으로 돌아간 월드 회전을 읽어
    #   뒤 뼈의 로컬 진행축이 기운다(실측: 두 번째 뼈 (0, 0.9985, -0.0548) - 블렌더 대조에서 잡힘).
    axes = []
    for i, node in enumerate(bones):
        aim = _local_vec(node, pos[i + 1] - pos[i]).normal()
        p2 = _local_vec(node, ref_w)
        p2 = p2 - aim * (p2 * aim)
        if p2.length() < 1e-6:
            alt = om.MVector(0, 1, 0) if abs(ref_w.y) < 0.9 else om.MVector(0, 0, 1)
            p2 = _local_vec(node, alt)
            p2 = p2 - aim * (p2 * aim)
        p2 = p2.normal()
        axes.append((aim, (aim ^ p2).normal(), p2))

    # ---- Tip (끝 따라가기 목표): 끝 노드에서 마지막 뼈 방향으로 반 뼈 더. 루트의 부모 아래.
    tip = None
    if tip_follow:
        last = pos[-1] - pos[-2]
        tip_pos = pos[-1] + last * 0.5
        tip = cmds.spaceLocator(name=_safe(_leaf(chain[0])) + FLOW_TIP_SUFFIX + "#")[0]
        cmds.xform(tip, worldSpace=True, translation=list(tip_pos))
        size = max(last.length() * 0.6, 1e-3)
        for c in "XYZ":
            cmds.setAttr(tip + ".localScale" + c, size)
        parent = cmds.listRelatives(chain[0], parent=True, fullPath=True)
        if parent:
            tip = cmds.parent(tip, parent[0])[0]
        net.made.append(tip)

    # ---- 체인 공유: 위상 · 변주 · 이득 · 방향
    sf, lf, ff = [None] * 3
    if chain_index > 0:
        consts = []
        for phase, size in (fm.VARY_SPEED, fm.VARY_LENGTH, fm.VARY_FLUTTER):
            consts.append(math.sin(chain_index * fm.VARY_STEP + phase) * size)
        sf = net.adl(net.mdl(drv + "." + FLOW_VARIATION, consts[0], "varSpd"), 1.0, "varSpd1")
        lf = net.adl(net.mdl(drv + "." + FLOW_VARIATION, consts[1], "varLen"), 1.0, "varLen1")
        ff = net.adl(net.mdl(drv + "." + FLOW_VARIATION, consts[2], "varFlt"), 1.0, "varFlt1")
        lag = net.mdl(net.mdl(drv + "." + FLOW_CHAIN_OFFSET, float(chain_index), "lagFrames"),
                      drv + "." + FLOW_RATE, "lag")
        phi = net.mdl(net.adl(drv + "." + FLOW_PHASE, lag, "phiLag"), sf, "phi")
        length = net.mdl(drv + "." + eff_attr("wavelength"), lf, "len")
        flutter = net.mdl(drv + "." + eff_attr("flutter"), ff, "flt")
    else:
        phi = drv + "." + FLOW_PHASE
        length = drv + "." + eff_attr("wavelength")
        flutter = drv + "." + eff_attr("flutter")
    inv_len = net.div(1.0, length, "invLen")
    cross_flt = net.mdl(drv + "." + eff_attr("cross"), flutter, "crossFlt")
    rnd = drv + "." + eff_attr("random")
    r_a16 = net.mdl(rnd, fm.A_WANDER_GAIN * _DEG2, "rA16")
    r_b13 = net.mdl(rnd, fm.B_WANDER_GAIN * _DEG2, "rB13")
    r_04 = net.mdl(rnd, fm.A_RIPPLE_GAIN, "r04")
    t_terms = {}
    for key, coef in (("am", fm.A_MAIN), ("aw", fm.A_WANDER), ("ar", fm.A_RIPPLE),
                      ("bm", fm.B_MAIN), ("bw", fm.B_WANDER), ("br", fm.B_RIPPLE)):
        t_terms[key] = net.mdl(phi, coef * _DEG2, "t_" + key)
    # 이득 = k0 * envelope / (1 - 0.7 * follow * F)
    env_k0 = net.mdl(drv + "." + DRIVER_ENVELOPE, k0, "envK0")
    if tip_follow:
        den = net.pma([1.0, net.mdl(drv + "." + eff_attr("follow"), fm.FOLLOW_GAIN, "folGain")], "gainDen", op=2)
        gain = net.div(env_k0, den, "gain")
    else:
        gain = env_k0
    dir_q = net.sin2(net.mdl(drv + "." + FLOW_DIR, 2.0, "dir2"), "dirSin")    # X = sin d, W = cos d
    sin_d, cos_d = dir_q + ".outputQuatX", dir_q + ".outputQuatW"

    for i, node in enumerate(bones):
        b = net_tag + "_b{0:02d}".format(i)
        net.tag = b
        u = fm.u_of(i, n)
        s = i * k0
        # ---- 공간 항 (도, 2θ): -720 * m * s / L
        md = net.node("multiplyDivide", "space")
        for c, m in (("X", 1.0), ("Y", fm.A_RIPPLE_SPACE), ("Z", fm.B_SPACE)):
            cmds.connectAttr(inv_len, md + ".input1" + c)
            cmds.setAttr(md + ".input2" + c, -720.0 * m * s)
        sp_br = net.mdl(inv_len, -720.0 * fm.B_RIPPLE_SPACE * s, "spaceBr")
        # ---- 파 a
        aw = net.sin2(net.pma([t_terms["aw"], _DEG2 * fm.A_WANDER_STEP * s], "awArg"), "awSin")
        am = net.sin2(net.pma([t_terms["am"], md + ".outputX", net.mdl(aw + ".outputQuatX", r_a16, "awGain")], "amArg"),
                      "amSin")
        ar = net.sin2(net.pma([t_terms["ar"], md + ".outputY",
                               _DEG2 * (fm.A_RIPPLE_PHASE + fm.A_RIPPLE_STEP * s)], "arArg"), "arSin")
        wave_a = net.adl(am + ".outputQuatX", net.mdl(ar + ".outputQuatX", r_04, "arGain"), "waveA")
        # ---- 파 b
        bw = net.sin2(net.pma([t_terms["bw"], _DEG2 * (fm.B_WANDER_PHASE + fm.B_WANDER_STEP * s)], "bwArg"), "bwSin")
        bm = net.sin2(net.pma([t_terms["bm"], md + ".outputZ", _DEG2 * fm.B_PHASE,
                               net.mdl(bw + ".outputQuatX", r_b13, "bwGain")], "bmArg"), "bmSin")
        br = net.sin2(net.pma([t_terms["br"], sp_br, _DEG2 * (fm.B_RIPPLE_PHASE + fm.B_RIPPLE_STEP * s)], "brArg"),
                      "brSin")
        wave_b = net.adl(bm + ".outputQuatX", net.mdl(br + ".outputQuatX", r_04, "brGain"), "waveB")
        # ---- 크기
        env = net.pow(u, drv + "." + eff_attr("stiffness"), "env")
        lean = net.mdl(drv + "." + eff_attr("lean"), fm.LEAN_BASE + fm.LEAN_GROW * u, "lean")
        along = net.mdl(net.adl(lean, net.mdl(net.mdl(flutter, env, "fltEnv"), wave_a, "fltA"), "alongSum"),
                        gain, "along")
        across = net.mdl(net.mdl(net.mdl(cross_flt, env, "crsEnv"), wave_b, "crsB"), gain, "across")
        # ---- 방향 분배: rx = along cos + across sin,  rz = along sin - across cos
        rx = net.pma([net.mdl(along, cos_d, "aCos"), net.mdl(across, sin_d, "cSin")], "rx")
        rz = net.pma([net.mdl(along, sin_d, "aSin"), net.mdl(across, cos_d, "cCos")], "rz", op=2)

        # ---- 축 (rest 로컬, 위에서 미리 구한 것)
        aim, p1, p2 = axes[i]

        q1 = net.node("axisAngleToQuat", "qP1")
        cmds.setAttr(q1 + ".inputAxis", p1.x, p1.y, p1.z)
        net.deg_in(rx, q1 + ".inputAngle", "qP1Uc")
        q2 = net.node("axisAngleToQuat", "qP2")
        cmds.setAttr(q2 + ".inputAxis", p2.x, p2.y, p2.z)
        net.deg_in(rz, q2 + ".inputAngle", "qP2Uc")
        q_wind = _quat_prod(net, q1, q2, "qWind")

        order = cmds.getAttr(node + ".rotateOrder")
        rest_rot = list(cmds.getAttr(node + ".rotate")[0])
        rest[node] = rest_rot
        q_rest = om.MEulerRotation([math.radians(v) for v in rest_rot], order).asQuaternion()
        q_rot = _quat_prod(net, q_wind, q_rest, "qRot")

        if tip_follow:
            jo = (cmds.getAttr(node + ".jointOrient")[0] if cmds.objExists(node + ".jointOrient") else (0, 0, 0))
            q_jo = om.MEulerRotation([math.radians(v) for v in jo]).asQuaternion()
            q_par = _quat_prod(net, q_rot, q_jo, "qPar")
            cm = net.node("composeMatrix", "parMtx")
            cmds.setAttr(cm + ".useEulerRotation", 0)
            cmds.connectAttr(q_par + ".outputQuat", cm + ".inputQuat")
            vp = net.node("vectorProduct", "aimPar")
            cmds.setAttr(vp + ".operation", 3)
            cmds.setAttr(vp + ".input1", aim.x, aim.y, aim.z)
            cmds.connectAttr(cm + ".outputMatrix", vp + ".matrix")
            mm = net.node("multMatrix", "tipMmx")
            cmds.connectAttr(tip + ".worldMatrix[0]", mm + ".matrixIn[0]")
            cmds.connectAttr(node + ".parentInverseMatrix[0]", mm + ".matrixIn[1]")
            dm = net.node("decomposeMatrix", "tipDcm")
            cmds.connectAttr(mm + ".matrixSum", dm + ".inputMatrix")
            tv = net.node("plusMinusAverage", "tipVec")
            cmds.setAttr(tv + ".operation", 2)
            cmds.connectAttr(dm + ".outputTranslate", tv + ".input3D[0]")
            cmds.connectAttr(node + ".translate", tv + ".input3D[1]")
            ab = net.node("angleBetween", "track")
            cmds.connectAttr(vp + ".output", ab + ".vector1")
            cmds.connectAttr(tv + ".output3D", ab + ".vector2")
            qdt = net.node("axisAngleToQuat", "qTrack")
            cmds.connectAttr(ab + ".axis", qdt + ".inputAxis")
            cmds.connectAttr(ab + ".angle", qdt + ".inputAngle")
            q_aim = _quat_prod(net, _quat_prod(net, q_par, qdt, "qParTrack"), q_jo.inverse(), "qAim")
            # 영향력 w = 1 - (1 - min(0.999, follow * k))^(12/n)
            k = 1.0 - fm.FOLLOW_TIP_DROP * (i / float(max(1, n - 1)))
            cl = net.node("clamp", "folClamp")
            cmds.setAttr(cl + ".maxR", fm.FOLLOW_CAP)
            cmds.setAttr(cl + ".minR", -1e9)
            cmds.connectAttr(net.mdl(drv + "." + eff_attr("follow"), k, "folK"), cl + ".inputR")
            w = net.pma([1.0, net.pow(net.pma([1.0, cl + ".outputR"], "folInv", op=2), fm.REF_BONES / n, "folPow")],
                        "folW", op=2)
            sl = net.node("quatSlerp", "qBlend")
            cmds.connectAttr(q_rot + ".outputQuat", sl + ".input1Quat")
            cmds.connectAttr(q_aim + ".outputQuat", sl + ".input2Quat")
            cmds.connectAttr(w, sl + ".inputT")
            q_out = sl
        else:
            q_out = q_rot

        qe = net.node("quatToEuler", "euler")
        cmds.setAttr(qe + ".inputRotateOrder", order)
        cmds.connectAttr(q_out + ".outputQuat", qe + ".inputQuat")
        cmds.connectAttr(qe + ".outputRotate", node + ".rotate", force=True)
    return net.made, rest, tip, None


# ---------------------------------------------------------------- 공개 API

def build_flow(joints, mode=MODE_ROOT, preset=None, opt_a=None, opt_b=None, mix=0.0, direction=0.0,
               envelope=1.0, chain_offset=14.0, variation=1.0, time_scale=1.0, tip_follow=True,
               wind_axis="Auto", prefix=None, follow_root=True):
    """Flow 셋업. (체인 수, 드라이버 이름 or None, 메시지)

    preset : 이름을 주면 그 프리셋의 옵션 1 / 2 를 A / B 로. 아니면 opt_a / opt_b(dict, 없으면 기본값)."""
    _plugin()
    if not joints:
        return 0, None, "[Warning] Nothing selected."
    if preset:
        opt_a, opt_b = fp.option(preset, 0), fp.option(preset, 1)
    opt_a = dict(fp.DEFAULTS, **(opt_a or {}))
    opt_b = dict(opt_a, **(opt_b or {})) if opt_b is not None else dict(opt_a)

    chains, missing, branched = resolve_chains(joints, mode)
    if not chains:
        return 0, None, "[Warning] No chain (2+ nodes) found." + (" Skipped: " + ", ".join(missing[:5]) if missing else "")

    base = prefix or _safe(_leaf(chains[0][0]))
    drv, made = _make_driver(base + "_flowDriver#", opt_a, opt_b, mix, direction, envelope, chain_offset,
                             variation, time_scale, preset,
                             place_at=cmds.xform(chains[0][0], q=True, ws=True, t=True))
    made = [drv] + made
    if follow_root:
        f_made, _skip = follow_root_position(drv, chains[0][0])
        made += f_made

    rest_all, failed, built, tips = {}, [], 0, []
    for ci, chain in enumerate(chains):
        c_made, rest, tip, why = _build_chain(drv, chain, built, tip_follow, wind_axis,
                                              _safe(_leaf(chain[0])) + "_flow")
        if why:
            failed.append("{0} ({1})".format(_leaf(chain[0]), why))
            continue
        made += c_made
        rest_all.update(rest)
        if tip:
            tips.append(tip)
        built += 1

    if not built:
        cmds.delete([m for m in made if cmds.objExists(m)])
        return 0, None, "[Warning] Nothing built. " + "; ".join(failed[:5])

    set_name = base + FLOW_SET_SUFFIX
    node_set = cmds.sets([m for m in made if cmds.objExists(m)], name=set_name)
    cmds.addAttr(node_set, longName=FLOW_REST_ATTR, dataType="string")
    cmds.setAttr(node_set + "." + FLOW_REST_ATTR, json.dumps(rest_all), type="string")
    n_drv = wire_flow_phase()

    msg = ("Flow: {0} chain(s), {1} bone(s), {2} maya node(s). Driver '{3}' holds Option A / B and flowMix "
           "(all keyable, live){4}. {5}Phase engine '{6}' drives {7} Flow driver(s). Remove with the '{8}' set.").format(
        built, len(rest_all), len(made), _leaf(drv),
        ", preset '{0}'".format(preset) if preset else "",
        "Tip Follow on: move the '{0}' locator(s) for secondary motion. ".format(FLOW_TIP_SUFFIX) if tip_follow else "",
        FLOW_ENGINE, n_drv, cmds.ls(node_set)[0])
    if failed:
        msg += " Failed: {0}.".format("; ".join(failed[:5]))
    if branched:
        msg += " Branching chain(s) followed the first child: {0}.".format(", ".join(branched[:5]))
    if missing:
        msg += " Skipped: {0}.".format(", ".join(missing[:5]))
    return built, drv, msg


def remove_flow(prefix=None):
    sets = [s for s in (cmds.ls(type="objectSet") or []) if s.endswith(FLOW_SET_SUFFIX)
            and (prefix is None or s.startswith(prefix))]
    if not sets:
        return 0, "[Warning] No Flow setup found."
    for node_set in sets:
        rest = {}
        if cmds.objExists(node_set + "." + FLOW_REST_ATTR):
            try:
                rest = json.loads(cmds.getAttr(node_set + "." + FLOW_REST_ATTR) or "{}")
            except ValueError:
                rest = {}
        members = cmds.sets(node_set, q=True) or []
        cmds.delete([m for m in members if cmds.objExists(m)])
        if cmds.objExists(node_set):
            cmds.delete(node_set)
        for node, value in rest.items():
            if not cmds.objExists(node):
                continue
            for i, c in enumerate("XYZ"):
                plug = "{0}.rotate{1}".format(node, c)
                if cmds.listConnections(plug, source=True, destination=False):
                    continue
                try:
                    cmds.setAttr(plug, value[i])
                except RuntimeError:
                    pass
    wire_flow_phase()
    return len(sets), "Flow removed: {0} setup(s).".format(len(sets))


# ---------------------------------------------------------------- 프리셋 · 값 (UI 가 부른다)

def selected_flow_drivers():
    """선택(드라이버 · Tip · 체인 노드)에서 Flow 드라이버들. 없으면 씬 전체."""
    sel = cmds.ls(selection=True, long=True) or []
    out = []
    all_drv = flow_drivers()
    for s in sel:
        if s in all_drv and s not in out:
            out.append(s)
            continue
        for st in (cmds.listSets(object=s) or []):
            if st.endswith(FLOW_SET_SUFFIX):
                for m in cmds.sets(st, q=True) or []:
                    full = (cmds.ls(m, long=True) or [m])[0]
                    if full in all_drv and full not in out:
                        out.append(full)
    if not out:
        # 선택한 체인 노드의 rotate 를 거슬러 올라가 드라이버 찾기
        for s in sel:
            hist = cmds.listHistory(s + ".rotate", pruneDagObjects=False) or [] if cmds.objExists(s + ".rotate") else []
            for h in hist:
                full = (cmds.ls(h, long=True) or [h])[0]
                if full in all_drv and full not in out:
                    out.append(full)
    return out or all_drv


def apply_preset(drivers, name):
    """프리셋 옵션 1 / 2 를 A / B 에 쓴다(Mix 는 그대로). 키가 있으면 그 시각에 값만 바꾼다(키는 지우지 않는다)."""
    o1, o2 = fp.option(name, 0), fp.option(name, 1)
    for d in drivers:
        for p in PARAMS:
            _set_value(d + "." + a_attr(p), o1[p])
            _set_value(d + "." + b_attr(p), o2[p])
        cmds.setAttr(d + "." + FLOW_PRESET, name, type="string")
    return len(drivers)


def set_param(drivers, p, value):
    """값 하나를 A 와 B 둘 다에 - Mix 와 무관하게 그 값(프리셋에서 벗어나 사용자 값)."""
    for d in drivers:
        _set_value(d + "." + a_attr(p), value)
        _set_value(d + "." + b_attr(p), value)
        cmds.setAttr(d + "." + FLOW_PRESET, "", type="string")


def set_plain(drivers, attr, value):
    for d in drivers:
        _set_value(d + "." + attr, value)


def _set_value(plug, value):
    if cmds.getAttr(plug, lock=True):
        return
    if cmds.listConnections(plug, source=True, destination=False, type="animCurve"):
        # 키가 있으면 지금 시각에 키 - linear 탄젠트(위상 엔진이 키 사이를 직선으로 적분하므로 그림과 맞게)
        t = cmds.currentTime(q=True)
        cmds.setKeyframe(plug, value=float(value), inTangentType="linear", outTangentType="linear")
        cmds.keyTangent(plug, time=(t, t), inTangentType="linear", outTangentType="linear")
    else:
        cmds.setAttr(plug, float(value))


def driver_values(drv):
    """UI 표시용: (A dict, B dict, mix, 실효 dict, 기타 dict)."""
    a = {p: cmds.getAttr(drv + "." + a_attr(p)) for p in PARAMS}
    b = {p: cmds.getAttr(drv + "." + b_attr(p)) for p in PARAMS}
    e = {p: cmds.getAttr(drv + "." + eff_attr(p)) for p in PARAMS}
    other = {k: cmds.getAttr(drv + "." + k) for k in (FLOW_DIR, DRIVER_ENVELOPE, FLOW_TIME_SCALE,
                                                      FLOW_CHAIN_OFFSET, FLOW_VARIATION)}
    return a, b, cmds.getAttr(drv + "." + FLOW_MIX), e, other
