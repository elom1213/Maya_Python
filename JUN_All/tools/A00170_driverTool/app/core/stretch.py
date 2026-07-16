# -*- coding: utf-8 -*-
"""
Stretch driven-key builder — ref/ref_01_StretchTool.mel 의 Stretch 기능 이식·리팩토링.

Default Distance 오브젝트의 어트리뷰트 값(a)을 driver 로, Stretch 오브젝트의 어트리뷰트를
driven 으로 하는 set driven key(animCurveUU)를 만든다. 커브는 linear 탄젠트 키 2개로 정의되는
1차 함수이고, pre/post infinity 로 양방향 무한 확장되어 전역에서 직선이 된다.

함수 모드 (a = 빌드 시점의 driver 어트리뷰트 값, original = 빌드 시점의 driven 어트리뷰트 값):
    FUNC_POS "x - a + 1"  : animCurveUU 키 (a, 1), (a+1, 2) → 기울기 +1 (거리 멀수록 값 증가)
    FUNC_NEG "-x + a + 1"  : animCurveUU 키 (a, 1), (a+1, 0) → 기울기 -1 (거리 멀수록 값 감소)
    FUNC_SIGMOID     : 해석적 시그모이드(노드망). x→-∞ 시 tmax, x→+∞ 시 tmin 에 수렴.
    FUNC_SIGMOID_REV : 위와 반대(x→-∞ 시 tmin, x→+∞ 시 tmax).
**모든 모드는 rest(x=a) 에서 driven = original(원래 값 그대로) 이다.**

선형(FUNC_POS/NEG) — animCurveUU + additive 오프셋
---------------------------------------------------
커브를 driven 에 직접 연결하지 않고 사이에 addDoubleLinear 오프셋을 끼워 original 기준 additive 로:

    driven = original + (f(x) - 1) = original + (x - a)     # FUNC_POS
    driven = original + (a - x)                             # FUNC_NEG

    animCurveUU.output ─→ addDoubleLinear.input1
              input2 = (original - 1)  ─────────┘→ output ─→ driven attr

f(x) 의 rest 출력 1 을 빼고 original 을 더하므로 rest 에서 driven = original, driver 가 a 에서
멀어질수록 original 기준으로 늘거나 줄어든다(예: tX 원래 1.5 → 1.5 에서 증감).

시그모이드(FUNC_SIGMOID/REV) — 해석적 노드망
-------------------------------------------
animCurveUU 대신 노드망으로 정확한 시그모이드를 만든다. **plateau(수렴값)는 리터럴 tmax/tmin**
이고, (a, original) 을 정확히 지난다(→ tmin ≤ 0 이하로 안 내려가려면 threshold_min ≥ 0):

    driven(x) = tmin + (tmax - tmin) / (1 + base^( factor*(x-a) + L ))
      factor = +1 (normal) / -1 (reversed)
      L = log_base( (tmax - original) / (original - tmin) )   # ← f(a)=original 을 보장하는 수평이동
    필요조건: base > 1,  tmin < original < tmax.

    base^(exp) 는 multiplyDivide(operation=power)로, 나눗셈/합은 multiplyDivide(divide)·addDoubleLinear
    로 구성. base(= 1/(1+e^-x) 의 e 값에 해당)와 tmax/tmin 은 사용자가 지정한다.

original 은 노드망을 연결하기 **전에** getAttr 로 스냅샷한다(연결 후에는 구동값이라 못 읽는다).

원본 MEL(JUN_stretch_aimCrv / JUN_cmd_makeStretch) 대비 개선점
------------------------------------------------------------
- pre/post infinity 를 둘 다 사용자가 지정한다(원본은 post = Cycle with Offset,
  pre = Constant 로 고정되어 rest 이하 구간이 직선이 아니었다).
- 탄젠트를 linear 로 강제한다(원본은 auto → 두 키 사이가 미세하게 곡선).
- 두 번째 키를 2*a 가 아니라 a+1 에 둔다. 원본은 (a,1),(2a,2) 라 기울기가 1/a 였고
  (실제로는 f(x)=x/a), a=0 이면 두 키의 입력이 겹쳐 커브가 깨졌으며 a<0 이면 두 번째 키가
  왼쪽에 놓여 기울기 부호가 뒤집혔다. a+1 로 두면 항상 기울기 ±1 의 f(x)=±x+(...)+1 이 된다.
- setDrivenKeyframe 을 두 번 호출해 animCurveUU 를 직접 만들어, 원본의
  connectionInfo -sourceFromDestination 재조회를 없앴다.
- 입력 검증(오브젝트/어트리뷰트 존재, self-drive, 스칼라 여부)을 추가하고 실패를 수집해 알린다.

검증(headless mayapy 2024): 위 셋업이 전 구간에서 f(x)=x-a+1 / -x+a+1 과 정확히 일치.
"""

import math

import maya.cmds as cmds


# 함수 모드 라벨(= UI 표시 문자열)
FUNC_POS = "f(x) = x - a + 1"
FUNC_NEG = "f(x) = -x + a + 1"
FUNC_SIGMOID = "Sigmoid (x-:max, x+:min)"
FUNC_SIGMOID_REV = "Sigmoid rev (x-:min, x+:max)"
FUNCTIONS = (FUNC_POS, FUNC_NEG, FUNC_SIGMOID, FUNC_SIGMOID_REV)
# 시그모이드 계열(노드망으로 빌드, threshold/base 파라미터 사용)
SIGMOID_FUNCTIONS = (FUNC_SIGMOID, FUNC_SIGMOID_REV)

# infinity: UI 표시 라벨 -> setInfinity 문자열 타입 (선형 모드 전용)
INFINITY_TYPES = ("Constant", "Linear", "Cycle", "Cycle with Offset", "Oscillate")
_INFINITY_ARG = {
    "Constant": "constant",
    "Linear": "linear",
    "Cycle": "cycle",
    "Cycle with Offset": "cycleRelative",
    "Oscillate": "oscillate",
}
DEFAULT_INFINITY = "Cycle with Offset"

# 시그모이드 파라미터 기본값
# base = 1/(1+e^-x) 의 e 값에 해당하는 거듭제곱 밑. 클수록 전이가 급격하다(> 1 필수).
DEFAULT_BASE = math.e
# threshold_min ≥ 0 이면 driven 이 0 밑으로 내려가지 않는다. original 은 (min, max) 사이여야 한다.
DEFAULT_THRESHOLD_MIN = 0.0
DEFAULT_THRESHOLD_MAX = 2.0


def _second_key_value(func):
    """모드에 맞는 두 번째 키의 value(첫 키는 (a, 1) 고정, 둘째 키 입력은 a+1 고정)."""
    # FUNC_NEG → (a+1, 0): 기울기 -1 / 그 외(FUNC_POS 기본) → (a+1, 2): 기울기 +1
    return 0.0 if func == FUNC_NEG else 2.0


def _driven_curve(plug):
    """driven plug 을 구동하는 animCurveUU 를 찾는다.

    보통 driven key 는 plug 에 animCurveUU 가 직접 연결되지만, plug 에 이미 다른 입력이
    있어 blendWeighted 가 끼면 그 입력 쪽 animCurve 를 되짚는다.
    """
    for node in cmds.listConnections(plug, s=True, d=False) or []:
        if cmds.nodeType(node).startswith("animCurve"):
            return node
        for inp in cmds.listConnections(node, s=True, d=False) or []:
            if cmds.nodeType(inp).startswith("animCurve"):
                return inp
    return None


def _is_scalar(value):
    """getAttr 결과가 스트레치 driver 로 쓸 수 있는 단일 숫자인지."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def build_stretch(default_pairs, stretch_pairs, func=FUNC_POS,
                  pre_infinity=DEFAULT_INFINITY, post_infinity=DEFAULT_INFINITY,
                  base=DEFAULT_BASE, threshold_min=DEFAULT_THRESHOLD_MIN,
                  threshold_max=DEFAULT_THRESHOLD_MAX):
    """Default Distance driver 로 Stretch Object 어트리뷰트를 구동하는 네트워크 생성.

    Parameters
    ----------
    default_pairs : list[(obj, attr)]  driver. a = getAttr(obj.attr) (빌드 시점 값).
    stretch_pairs : list[(obj, attr)]  driven.
        default 가 1개면 그 하나로 모든 stretch 를 구동(1:n), 아니면 순서쌍 n:n(min 길이).
    func : FUNCTIONS 중 하나(FUNC_POS/NEG = 선형, FUNC_SIGMOID/REV = 시그모이드).
    pre_infinity, post_infinity : INFINITY_TYPES 중 하나(라벨). 선형 모드에만 적용.
    base, threshold_min, threshold_max : 시그모이드 파라미터. base > 1,
        threshold_min < original < threshold_max 여야 한다(시그모이드 모드에만 적용).

    Returns
    -------
    (built, skipped)
        built   : list[(driver_plug, driven_plug, a, original, node)]
                  node = 선형이면 오프셋 addDoubleLinear, 시그모이드면 최종 출력 노드.
        skipped : list[(driven_plug, reason)]

    Raises
    ------
    ValueError : 시그모이드 모드에서 base ≤ 1 또는 threshold_max ≤ threshold_min 일 때.
    """
    is_sigmoid = func in SIGMOID_FUNCTIONS
    if is_sigmoid:
        if base <= 1.0:
            raise ValueError("Sigmoid base must be > 1 (got {0}).".format(base))
        if threshold_max <= threshold_min:
            raise ValueError(
                "Sigmoid threshold_max must be > threshold_min "
                "(got min={0}, max={1}).".format(threshold_min, threshold_max))

    pre_arg = _INFINITY_ARG.get(pre_infinity, "cycleRelative")
    post_arg = _INFINITY_ARG.get(post_infinity, "cycleRelative")
    second_val = _second_key_value(func)

    # 페어링: 1:n 이면 driver 를 stretch 개수만큼 복제, 아니면 min 길이로 zip.
    if len(default_pairs) == 1:
        pairs = [(default_pairs[0], sp) for sp in stretch_pairs]
    else:
        pairs = list(zip(default_pairs, stretch_pairs))

    built = []
    skipped = []

    for (d_obj, d_attr), (s_obj, s_attr) in pairs:
        driver_plug = "{0}.{1}".format(d_obj, d_attr)
        driven_plug = "{0}.{1}".format(s_obj, s_attr)

        if not cmds.objExists(driver_plug):
            skipped.append((driven_plug, "driver attr not found: {0}".format(driver_plug)))
            continue
        if not cmds.objExists(driven_plug):
            skipped.append((driven_plug, "driven attr not found: {0}".format(driven_plug)))
            continue
        if driver_plug == driven_plug:
            skipped.append((driven_plug, "driver and driven are the same plug"))
            continue

        a = cmds.getAttr(driver_plug)
        if not _is_scalar(a):
            skipped.append((driven_plug,
                            "driver attr is not a single numeric value: {0}".format(driver_plug)))
            continue

        # driven 의 원래 값. 네트워크를 연결하기 전에 스냅샷한다(모든 모드가 rest=original 을 보존).
        # 컴파운드(translate 등) 는 스칼라가 아니므로 여기서 걸러 부분 빌드를 막는다.
        original = cmds.getAttr(driven_plug)
        if not _is_scalar(original):
            skipped.append((driven_plug,
                            "driven attr is not a single numeric value: {0}".format(driven_plug)))
            continue

        if is_sigmoid:
            # 시그모이드는 (min, max) 사이에 original 이 있어야 (a, original)을 지날 수 있다.
            if not (threshold_min < original < threshold_max):
                skipped.append((driven_plug,
                    "sigmoid needs threshold_min < original({0}) < threshold_max; "
                    "got [{1}, {2}]".format(original, threshold_min, threshold_max)))
                continue
            try:
                node = _build_sigmoid(
                    driver_plug, driven_plug, a, original, base,
                    threshold_min, threshold_max,
                    func == FUNC_SIGMOID_REV, s_obj, s_attr)
            except Exception as exc:  # locked/이미 연결됨 등
                skipped.append((driven_plug, "sigmoid build failed: {0}".format(exc)))
                continue
            built.append((driver_plug, driven_plug, a, original, node))
            continue

        # --- 선형(FUNC_POS/NEG): animCurveUU 2키 + additive 오프셋 ---
        try:
            # (a, 1) 과 (a+1, second_val) — animCurveUU 하나에 키 2개.
            cmds.setDrivenKeyframe(driven_plug, currentDriver=driver_plug,
                                   driverValue=a, value=1.0)
            cmds.setDrivenKeyframe(driven_plug, currentDriver=driver_plug,
                                   driverValue=a + 1.0, value=second_val)
        except Exception as exc:  # keyable/locked 아님 등
            skipped.append((driven_plug, "setDrivenKeyframe failed: {0}".format(exc)))
            continue

        crv = _driven_curve(driven_plug)
        if not crv:
            skipped.append((driven_plug, "driven curve not found after keying"))
            continue

        # 탄젠트 linear + pre/post infinity.
        cmds.keyTangent(crv, e=True, itt="linear", ott="linear")
        # setInfinity 는 커브 노드가 아니라 plug(오브젝트.어트리뷰트) 대상일 때만 적용된다.
        # 커브가 아직 driven 에 직접 연결된 이 시점에 걸어야 하며, 이후 배선을 바꿔도 유지된다.
        cmds.setInfinity(driven_plug, pri=pre_arg, poi=post_arg)

        # additive 오프셋 노드 삽입: driven = curve.output + (original - 1).
        # 커브 → driven 직결을 끊고 addDoubleLinear 를 사이에 끼운다.
        offset = _insert_offset(crv, driven_plug, original, s_obj, s_attr)

        built.append((driver_plug, driven_plug, a, original, offset))

    return built, skipped


def _build_sigmoid(driver_plug, driven_plug, a, original, base, tmin, tmax,
                   reversed_, s_obj, s_attr):
    """해석적 시그모이드 노드망을 만들고 driven 에 연결. 반환: 최종 출력 노드 이름.

    driven(x) = tmin + (tmax-tmin) / (1 + base^( factor*(x-a) + L ))
        factor = -1(reversed) / +1(normal),  L = log_base((tmax-original)/(original-tmin))
    L 수평이동으로 driven(a) = original 을 정확히 보장하고, plateau 는 리터럴 tmax/tmin.
    """
    span = tmax - tmin
    factor = -1.0 if reversed_ else 1.0
    # (tmax-original)>0, (original-tmin)>0 는 호출부에서 보장(threshold_min<original<threshold_max).
    L = math.log((tmax - original) / (original - tmin)) / math.log(base)

    prefix = "{0}_{1}".format(s_obj.replace("|", "_").replace(":", "_"), s_attr)

    def _node(kind, suffix):
        return cmds.createNode(kind, name="{0}_stretchSig{1}".format(prefix, suffix))

    diff = _node("addDoubleLinear", "Diff")        # x - a
    cmds.connectAttr(driver_plug, diff + ".input1")
    cmds.setAttr(diff + ".input2", -a)

    fdiff = _node("multDoubleLinear", "Fac")       # factor * (x - a)
    cmds.connectAttr(diff + ".output", fdiff + ".input1")
    cmds.setAttr(fdiff + ".input2", factor)

    expn = _node("addDoubleLinear", "Exp")         # factor*(x-a) + L
    cmds.connectAttr(fdiff + ".output", expn + ".input1")
    cmds.setAttr(expn + ".input2", L)

    powr = _node("multiplyDivide", "Pow")          # base ^ exponent
    cmds.setAttr(powr + ".operation", 3)           # power
    cmds.setAttr(powr + ".input1X", base)
    cmds.connectAttr(expn + ".output", powr + ".input2X")

    denom = _node("addDoubleLinear", "Denom")      # 1 + base^exp
    cmds.connectAttr(powr + ".outputX", denom + ".input1")
    cmds.setAttr(denom + ".input2", 1.0)

    frac = _node("multiplyDivide", "Div")          # span / denom
    cmds.setAttr(frac + ".operation", 2)           # divide
    cmds.setAttr(frac + ".input1X", span)
    cmds.connectAttr(denom + ".output", frac + ".input2X")

    out = _node("addDoubleLinear", "Out")          # tmin + span/denom
    cmds.connectAttr(frac + ".outputX", out + ".input1")
    cmds.setAttr(out + ".input2", tmin)

    cmds.connectAttr(out + ".output", driven_plug)
    return out


def _insert_offset(curve, driven_plug, original, s_obj, s_attr):
    """curve.output 를 driven 에 직접 연결하는 대신 addDoubleLinear(+original-1)를 끼운다.

    driven = curve.output + (original - 1) → rest 에서 original, driver 이동 시 additive 증감.
    반환: 생성한 addDoubleLinear 노드 이름.
    """
    name = "{0}_{1}_stretchAdd".format(
        s_obj.replace("|", "_").replace(":", "_"), s_attr)
    add = cmds.createNode("addDoubleLinear", name=name)
    cmds.disconnectAttr(curve + ".output", driven_plug)
    cmds.connectAttr(curve + ".output", add + ".input1")
    cmds.setAttr(add + ".input2", original - 1.0)
    cmds.connectAttr(add + ".output", driven_plug)
    return add
