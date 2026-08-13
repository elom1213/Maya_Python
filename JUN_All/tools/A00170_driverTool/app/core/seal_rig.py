# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00170_driverTool - Seal : 커브에 어태치된 입술 리그를 "끝에서 중앙으로" 다물리는 지퍼 셋업.
#
# 계획서 : docs/plans/A00170_Seal_plan.md
#
# 전제 : AttachCrv > Edge Loop 로 만든 리그.
#   위/아래 입술 라인마다 커브 1개, 그 커브에 널이 어태치(POCI -> fourByFourMatrix ->
#   multMatrix(x parentInverseMatrix) -> decomposeMatrix -> null.translate)되어 있고,
#   조인트가 널(또는 _tgt)을 따라간다.
#
# ## 어떻게 다물리나
#
# 1. 다물린 자리는 **리그를 만든 시점의 포즈(rest)** 다. 널 하나하나의 rest 를 기준 노드
#    (Reference = 머리 조인트, 기본은 널의 부모) 공간에 저장해 두고, 그걸 **통째로**
#    "지금 커브가 말하는 만남점"까지 평행이동시킨 것이 목표다:
#
#        만남점_live = lerp(아래 커브 자리, 위 커브 자리, sealBias)
#        만남점_rest = lerp(아래 rest 자리,  위 rest 자리,  sealBias)
#        목표_i      = rest_i + (만남점_live - 만남점_rest)      # 위/아래 각각
#        목표회전_i  = rest_i 의 회전                            # 그대로
#
#    그래서 **다물려도 위/아래 널이 한 점으로 겹치지 않고**(rest 의 두께·간격 유지),
#    **회전은 다물리기 전(rest)과 완전히 같다**. rest 를 기준 노드 공간에 저장하므로
#    머리가 돌거나 아바타가 움직여도 다물리는 자리는 얼굴을 따라간다.
#    (v01.19 까지는 위/아래 커브 행렬을 `blendMatrix` 로 섞어 **두 널을 같은 행렬**에
#     붙였다 — 위치가 완전히 같아지고, 위/아래 커브 프레임이 서로 반대라 섞인 회전이
#     90° 틀어져 널의 x 축이 월드 z 를 보는 문제가 있었다.)
# 2. 각 조인트의 **입술 위 위치 u**(0~1)에 따라 닫히는 타이밍이 다르다:
#        w_R = ramp( sealR - u*(1-band),  0..band )      # u=0 쪽 끝에서 시작
#        w_L = ramp( sealL - (1-u)*(1-band), 0..band )   # 반대쪽 끝에서 시작
#        w   = clamp01(w_R + w_L)
#    sealR/sealL 이 독립이라 **양 끝에서 중앙으로** 동시에 다물 수 있다.
# 3. 기존 `decomposeMatrix -> null.translate` 사이에 **pairBlend** 를 끼워
#    in1 = 커브 구동, in2 = seal 자리, weight = w 로 섞는다. 커브가 회전까지 구동하면
#    (Edge Loop 의 orient 옵션) 회전도 같은 weight 로 rest 회전을 향해 섞는다.
#
# ## rest 는 "빌드한 순간의 씬 포즈"다
#
# 즉 **입술이 다물린(중립) 포즈에서 빌드**해야 한다. 나중에 다시 잡으려면
# `recapture_rest()`(UI 의 Update Rest Pose) — sealR/sealL 을 잠깐 0 으로 내려
# 커브가 주는 자리를 읽어 rest 행렬만 갈아 끼운다.
#
# ## u 는 생성 순서가 아니라 **커브 파라미터**에서 얻는다
#
# 실측: Edge Loop 로 만든 `up_null_01..09` 의 정규화 파라미터가 1.0 -> 0.0 **역순**이었다.
# 이름/생성 순서로 좌우를 판단하면 지퍼가 뒤집힌다. 그래서 널의 POCI `.parameter` 를
# 커브 minValue/maxValue 로 정규화해 쓰고, 위/아래 커브 방향이 서로 반대면 자동으로 뒤집는다.
#
# ## 커브가 **하나**(입술을 한 바퀴 감는 닫힌 커브)여도 된다
#
# 위/아래가 같은 커브를 나눠 쓰는 게 감지되면, 각 입술이 차지한 **원형 구간**을 찾아
# 그 안에서 u 를 다시 0~1 로 편다(`respan_shared_curve`). 커브의 씸이 입술 한가운데에
# 있어도 상관없다. 자세한 배경은 그 함수 위 주석 참고.
#
# UI 비의존: 위젯에서 읽은 이름/옵션 값만 받는다.

import maya.cmds as cmds


# 컨트롤러에 만드는 어트리뷰트 (이름, min, max, 기본값)
SEAL_ATTRS = (
    ("sealR", 0.0, 1.0, 0.0),
    ("sealL", 0.0, 1.0, 0.0),
    ("sealBias", 0.0, 1.0, 0.5),
    ("sealBand", 0.02, 1.0, 0.35),
    # 0 = 위/아래가 rest 간격(입술 두께)을 지킨 채 만난다(기본).
    # 1 = 위/아래 널이 만남점 **한 점에서 정확히 일치**한다(v01.19 까지의 동작).
    ("sealMerge", 0.0, 1.0, 0.0),
)

# 좌우 판정 축
AXES = ("x", "y", "z")
_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}

# 코너(입 끝)로 보고 건너뛸 u 여유
CORNER_EPS = 0.02

# 짝짓기 척도 : 커브 파라미터 차이 / 월드 거리
METRIC_PARAM = "param"
METRIC_DISTANCE = "distance"
METRICS = (METRIC_PARAM, METRIC_DISTANCE)

DEFAULT_PREFIX = "lipSeal"

# 나중에 rest 를 다시 잡을 수 있도록 남기는 표식(message 어트리뷰트).
REST_NULL_TAG = "sealRestNull"      # rest 행렬 노드 -> 그 널
REST_REF_TAG = "sealRestRef"        # rest 행렬 노드 -> 기준 노드(있을 때만)
SET_CTRL_TAG = "sealController"     # seal SET -> 컨트롤러


# ============================================================ 조회 / 파라미터

def _long(name):
    found = cmds.ls(name, l=True) or []
    return found[0] if found else None


def _leaf(name):
    return name.split("|")[-1].split(":")[-1]


def poci_of(node):
    """노드를 구동하는 네트워크에서 pointOnCurveInfo 를 찾는다(없으면 None)."""
    if not node or not cmds.objExists(node):
        return None
    hist = cmds.listHistory(node) or []
    found = cmds.ls(hist, type="pointOnCurveInfo") or []
    return found[0] if found else None


def _ancestor_driver(node, depth=6):
    """자신 -> 부모 -> 조부모 … 순으로 커브 구동 노드를 찾는다.

    Edge Loop 가 만드는 계층이 `null > _con > _ctl > _tgt` 라, 사용자가 뷰포트에서 집는
    **컨트롤러(_ctl)** 나 `_tgt` 를 리스트에 담아도 그 위의 널을 찾아내야 한다.
    """
    current = node
    for _ in range(depth + 1):
        if current is None:
            return None
        if poci_of(current):
            return current
        parents = cmds.listRelatives(current, p=True, f=True) or []
        current = parents[0] if parents else None
    return None


def resolve_driver(node):
    """리스트에 무엇을 담아도 커브에 어태치된 **널**을 찾아 준다.

    받아 주는 것: 널 자신 / `_con` · `_ctl` · `_tgt`(부모를 거슬러 올라간다) /
    조인트(그 조인트를 끄는 컨스트레인트의 타깃에서 다시 거슬러 올라간다).
    """
    node = _long(node)
    if node is None:
        return None

    found = _ancestor_driver(node)
    if found:
        return found

    # 조인트처럼 컨스트레인트로 끌려가는 노드 -> 타깃에서 다시 거슬러 올라간다.
    for con in (cmds.listConnections(node, type="constraint") or []):
        con_type = cmds.nodeType(con)
        cmd = getattr(cmds, con_type, None)
        if cmd is None:
            continue
        try:
            targets = cmd(con, q=True, targetList=True) or []
        except Exception:
            targets = []
        for tgt in targets:
            found = _ancestor_driver(_long(tgt))
            if found:
                return found
    return None


def _drivers_under(node):
    """그 노드 **아래(자손)** 에 있는 커브 구동 널들. 그룹을 통째로 담았을 때를 위해."""
    children = cmds.listRelatives(node, allDescendents=True, type="transform",
                                  fullPath=True) or []
    return [c for c in children if poci_of(c)]


def _drivers_on_curve(node):
    """그 노드가 커브면, 그 커브를 쓰는 POCI 가 구동하는 널들.

    위/아래 **입술 커브 2개만** 리스트에 담아도 동작하게 해 준다.
    """
    shapes = []
    if cmds.objectType(node, isType="nurbsCurve"):
        shapes = [node]
    else:
        shapes = cmds.listRelatives(node, shapes=True, type="nurbsCurve",
                                    fullPath=True) or []
    out = []
    for shape in shapes:
        for poci in (cmds.listConnections(shape + ".worldSpace",
                                          type="pointOnCurveInfo") or []):
            # POCI 의 바로 아래는 transform 이 아니라 fourByFourMatrix 다
            # (POCI -> fbf -> multMatrix -> decomposeMatrix -> null). 하류 전체를 훑는다.
            future = cmds.listHistory(poci, future=True, allFuture=True) or []
            for driven in (cmds.ls(future, type="transform", l=True) or []):
                if driven not in out and poci_of(driven) == poci:
                    out.append(driven)
    return out


def curve_of(node):
    """그 널을 어태치하고 있는 **커브 셰이프**(없으면 None)."""
    poci = poci_of(node)
    if not poci:
        return None
    shapes = cmds.listConnections(poci + ".inputCurve", s=True, d=False,
                                  shapes=True) or []
    if not shapes:
        return None
    found = cmds.ls(shapes[0], l=True) or []
    return found[0] if found else shapes[0]


def is_closed_curve(shape):
    """닫힌(한 바퀴 도는) 커브인가. form : 0 open / 1 closed / 2 periodic."""
    if not shape:
        return False
    try:
        return int(cmds.getAttr(shape + ".form")) != 0
    except Exception:
        return False


def normalized_param(node):
    """커브 위 정규화 파라미터 u(0~1). 커브 구동이 아니면 None."""
    poci = poci_of(node)
    shape = curve_of(node)
    if not poci or not shape:
        return None
    lo = cmds.getAttr(shape + ".minValue")
    hi = cmds.getAttr(shape + ".maxValue")
    p = cmds.getAttr(poci + ".parameter")
    return (p - lo) / (hi - lo) if hi > lo else 0.0


def collect_drivers(nodes):
    """이름 목록 -> [{node, poci, u, pos}] (커브에 어태치된 것만, 중복 제거).

    무엇을 담아도 되게 세 단계로 넓혀 가며 찾는다:
      1. 그 노드(또는 그 조상/컨스트레인트 타깃)가 커브 구동인가  -> `resolve_driver`
      2. 그 **아래(자손)** 에 커브 구동 널이 있는가              -> 그룹을 통째로 담은 경우
      3. 그 노드가 **커브**인가                                  -> 그 커브에 붙은 널 전부
    """
    out = []
    seen = set()

    def _add(driver):
        if not driver or driver in seen:
            return
        u = normalized_param(driver)
        if u is None:
            return
        seen.add(driver)
        out.append({
            "node": driver,
            "poci": poci_of(driver),
            "curve": curve_of(driver),
            "u": u,
            "u_raw": u,          # 커브 전체 기준(재정규화 전) — 진단용
            "pos": cmds.xform(driver, q=True, ws=True, t=True),
        })

    for name in nodes or []:
        node = _long(name)
        if node is None:
            continue
        driver = resolve_driver(node)
        if driver:
            _add(driver)
            continue
        for found in _drivers_under(node) or _drivers_on_curve(node):
            _add(found)
    return out


# ------------------------------------------------ 닫힌(한 바퀴) 커브 대응
#
# 널이 위/아래 **각각의 커브**에 붙어 있으면 u 는 그대로 0~1 = 입술 한 줄이다.
# 그런데 입술을 **한 바퀴 휘감는 커브 하나**에 위/아래가 함께 붙어 있으면 얘기가 다르다:
#   - 커브 전체를 0~1 로 재면 윗입술은 그중 절반만 차지한다(지퍼가 절반만 간다).
#   - 커브의 씸(u=0=1)이 입술 **한가운데**에 올 수 있다 — 실측: 윗입술 u 가
#     `0.81 0.87 0.94 | 0.0 0.06 0.12 0.19` 로 갈라졌고, 결과적으로 왼쪽 3쌍이 전부
#     u=0.25, 오른쪽 3쌍이 전부 u=0.75 로 뭉쳐 **동시에 닫혔다**(지퍼가 아니라 스위치).
#   - 씸이 코너로 오인돼 입술 중앙 널이 스킵되고, 정작 입꼬리는 코너로 안 잡혔다.
#
# 그래서 위/아래가 **같은 커브**를 나눠 쓰는 게 감지되면, 각 쪽이 실제로 차지한
# **원형 구간(arc)** 을 찾아 그 안에서 u 를 다시 0~1 로 편다. 구간 찾기는 "가장 큰 빈틈
# 다음이 시작" — 씸을 넘어가도(0.81 → 0.19) 한 덩어리로 인식된다.

def _arc(entries):
    """엔트리들이 차지한 **원형 구간** (start, span). 가장 큰 빈틈 다음이 시작."""
    values = sorted(e["u"] for e in entries)
    n = len(values)
    if n < 2:
        return (values[0] if values else 0.0), 0.0
    gaps = [(values[(i + 1) % n] - values[i]) % 1.0 for i in range(n)]
    biggest = max(range(n), key=lambda i: gaps[i])
    start = values[(biggest + 1) % n]
    span = max((v - start) % 1.0 for v in values)
    return start, span


def _respan(entries, start, span):
    """구간 (start, span) 안의 u 를 0~1 로 다시 편다."""
    if span <= 1e-9:
        return False
    for e in entries:
        e["u"] = min(1.0, max(0.0, ((e["u"] - start) % 1.0) / span))
    return True


def respan_shared_curve(upper, lower):
    """위/아래가 한 커브를 나눠 쓸 때, 각 입술 구간을 0~1 로 다시 편다.

    두 구간 **사이의 빈틈 = 입꼬리**다. 구간을 빈틈의 **절반씩** 늘려 잡아 u=0 / u=1 이
    실제 입꼬리에 오게 한다. 이렇게 하면 코너 널을 리스트에 넣지 않아도 양 끝 널이
    `skip_corners` 에 잘못 걸리지 않고, 넣었으면 그게 정확히 u=0 / 1 이 된다.

    Returns: 다시 폈는가(bool)
    """
    if len(upper) < 2 or len(lower) < 2:
        return False
    up_start, up_span = _arc(upper)
    lo_start, lo_span = _arc(lower)
    if up_span <= 1e-9 or lo_span <= 1e-9:
        return False

    # 윗구간 끝 -> 아랫구간 시작 / 아랫구간 끝 -> 윗구간 시작 사이의 빈틈.
    gap_a = (lo_start - (up_start + up_span)) % 1.0
    gap_b = (up_start - (lo_start + lo_span)) % 1.0
    if up_span + lo_span + gap_a + gap_b <= 1.0 + 1e-6:
        # 두 구간이 겹치지 않을 때만 늘린다(겹치면 어느 쪽 입술인지 알 수 없다).
        up_start -= gap_b * 0.5
        lo_start -= gap_a * 0.5
        up_span += (gap_a + gap_b) * 0.5
        lo_span += (gap_a + gap_b) * 0.5

    done_up = _respan(upper, up_start % 1.0, up_span)
    done_lo = _respan(lower, lo_start % 1.0, lo_span)
    return done_up or done_lo


def prepare_sides(upper, lower, axis="x", start_at_min=True):
    """Upper/Lower 이름 목록 -> 짝짓기에 바로 넣을 수 있는 엔트리 두 벌.

    한 커브에 위/아래가 다 붙어 있는 경우(닫힌 입술 커브)를 여기서 흡수하므로,
    미리보기와 빌드가 **같은 결과**를 본다.

    Returns: (up_entries, lo_entries, info)
        info = {shared_curve, closed, respanned, flipped, dropped}
    """
    up = collect_drivers(upper)
    lo = collect_drivers(lower)

    up_curves = set(e["curve"] for e in up if e["curve"])
    lo_curves = set(e["curve"] for e in lo if e["curve"])
    shared = up_curves & lo_curves

    respanned = False
    if shared and up and lo:
        respanned = respan_shared_curve(up, lo)

    # 같은 널을 양쪽에 다 담았으면(닫힌 커브의 입꼬리에서 흔하다) 코너로 보고 뺀다.
    # 그대로 두면 자기 자신과 짝이 되어 pairBlend 가 두 번 끼워지고 **사이클**이 된다.
    both = set(e["node"] for e in up) & set(e["node"] for e in lo)
    dropped = [(n, "listed in both Upper and Lower (corner)") for n in sorted(both)]
    if both:
        up = [e for e in up if e["node"] not in both]
        lo = [e for e in lo if e["node"] not in both]

    flipped = (orient_u(up, axis, start_at_min),
               orient_u(lo, axis, start_at_min))
    return up, lo, {
        "shared_curve": sorted(shared),
        "closed": any(is_closed_curve(c) for c in shared),
        "respanned": respanned,
        "flipped": flipped,
        "dropped": dropped,
    }


def orient_u(entries, axis="x", start_at_min=True):
    """u 를 '지퍼 시작 끝 = 0' 이 되도록 정렬(필요하면 뒤집는다).

    커브 방향은 리그마다 제각각이라(실측: 위/아래가 반대인 경우도 있다) 월드 좌표로 판정한다.
    `start_at_min=True` 면 지정 축의 **작은 쪽 끝**이 u=0 이 된다.
    반환: (뒤집었는가)
    """
    if len(entries) < 2:
        return False
    index = _AXIS_INDEX.get(axis, 0)
    lo = min(entries, key=lambda e: e["u"])
    hi = max(entries, key=lambda e: e["u"])
    # u=0 쪽이 축의 작은 값이어야 하는데 그 반대면 뒤집는다.
    flip = (lo["pos"][index] > hi["pos"][index]) == bool(start_at_min)
    if flip:
        for e in entries:
            e["u"] = 1.0 - e["u"]
    return flip


def _distance(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def pair_cost(up, lo, metric=METRIC_PARAM):
    """짝 후보의 '멀기'. 작을수록 좋은 짝."""
    if metric == METRIC_DISTANCE:
        return _distance(up["pos"], lo["pos"])
    return abs(up["u"] - lo["u"])


def pair_drivers(upper, lower, skip_corners=True, metric=METRIC_PARAM,
                 tolerance=None):
    """위/아래를 **가장 가까운 것끼리 1:1** 로 짝짓는다.

    위치가 정확히 같을 필요는 없다 — "다른 후보보다 가까우면" 짝이 된다. 어떤 척도로
    가까움을 잴지는 `metric` 으로 고른다.

      METRIC_PARAM(기본) : 커브 위 정규화 파라미터 차이 |Δu|.
          입술 위 **같은 진행도**끼리 맺는다. 위/아래 조인트 개수가 달라도, 커브 길이가
          달라도 잘 맞는다.
      METRIC_DISTANCE    : 월드 거리. 파라미터 분포가 서로 많이 다를 때(한쪽만 촘촘하게
          배치했다든가) 쓴다.

    **전역 1:1 배정**이다. 후보를 가까운 순으로 훑어 아직 안 쓰인 것끼리만 맺으므로,
    윗쪽 여럿이 같은 아랫 널을 물고 늘어지지 않는다(예전 구현의 문제). 남는 쪽은 짝 없이
    보고된다.

    `tolerance` 를 주면 그보다 먼 후보는 아예 맺지 않는다(엉뚱한 짝 방지).
    반환: ([(up_entry, lo_entry, u), ...], skipped)  — u 는 두 짝의 평균 위치.
    """
    skipped = []

    def _usable(entries, side):
        out = []
        for e in entries:
            if skip_corners and (e["u"] < CORNER_EPS or e["u"] > 1.0 - CORNER_EPS):
                skipped.append((e["node"], "corner ({0})".format(side)))
                continue
            out.append(e)
        return out

    ups = _usable(upper, "upper")
    los = _usable(lower, "lower")
    if not ups or not los:
        return [], skipped

    candidates = []
    for i, up in enumerate(ups):
        for j, lo in enumerate(los):
            if up["node"] == lo["node"]:
                continue                      # 자기 자신과 짝지으면 사이클이 된다
            cost = pair_cost(up, lo, metric)
            if tolerance is not None and cost > tolerance:
                continue
            candidates.append((cost, i, j))
    candidates.sort(key=lambda c: c[0])

    used_up, used_lo = set(), set()
    pairs = []
    for cost, i, j in candidates:
        if i in used_up or j in used_lo:
            continue
        used_up.add(i)
        used_lo.add(j)
        up, lo = ups[i], los[j]
        pairs.append((up, lo, (up["u"] + lo["u"]) * 0.5))

    for i, up in enumerate(ups):
        if i not in used_up:
            skipped.append((up["node"], "no partner within tolerance"))
    for j, lo in enumerate(los):
        if j not in used_lo:
            skipped.append((lo["node"], "no partner within tolerance"))

    # 입술을 따라가는 순서로 돌려준다(미리보기가 읽기 쉽도록).
    pairs.sort(key=lambda p: p[2])
    return pairs, skipped


# ============================================================ 어트리뷰트

def ensure_attrs(controller, band=None, bias=None, merge=None):
    """컨트롤러에 seal 어트리뷰트를 보장한다. (만든 이름 리스트)"""
    if not controller or not cmds.objExists(controller):
        raise ValueError("Controller '{0}' not found.".format(controller))
    made = []
    for name, lo, hi, default in SEAL_ATTRS:
        if not cmds.attributeQuery(name, node=controller, exists=True):
            cmds.addAttr(controller, longName=name, attributeType="double",
                         minValue=lo, maxValue=hi, defaultValue=default,
                         keyable=True)
            made.append(name)
    for name, value in (("sealBand", None if band is None else max(0.02, float(band))),
                        ("sealBias", None if bias is None else float(bias)),
                        ("sealMerge", None if merge is None else float(merge))):
        if value is None:
            continue
        try:
            cmds.setAttr(controller + "." + name, value)
        except Exception:
            pass
    return made


# ============================================================ 노드 그래프

def _node(kind, name):
    return cmds.createNode(kind, name=name)


def attach_matrix_plug(driver, name=None):
    """그 널을 구동하는 **커브 어태치 월드 행렬** 플러그. (플러그, 새로 만든 노드들)

    attach_curve 네트워크는 `POCI -> fourByFourMatrix -> multMatrix(x parentInverse)`
    이므로 그 **fourByFourMatrix.output** 이 곧 커브가 준 월드 행렬(위치 + orient 옵션이면
    회전까지)이다. 널의 worldMatrix 를 쓰면 우리가 다시 널을 구동하므로 **사이클**이 된다 —
    반드시 널보다 상류에서 가져와야 한다.

    orient 없이 만든 리그 등 fbf 가 없으면 POCI 위치만으로 하나 만들어 준다(위치 전용).
    """
    poci = poci_of(driver)
    found = cmds.listConnections(poci, s=False, d=True,
                                 type="fourByFourMatrix") or []
    if found:
        return found[0] + ".output", []

    fbf = _node("fourByFourMatrix", (name or _leaf(driver)) + "_srcFbf")
    for comp, row in zip("XYZ", ("in30", "in31", "in32")):
        cmds.connectAttr("{0}.position{1}".format(poci, comp),
                         "{0}.{1}".format(fbf, row), f=True)
    return fbf + ".output", [fbf]


def _mat_mul(a, b):
    """4x4 행렬 곱 (마야와 같은 행벡터 규약 : world = local * parent)."""
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r * 4 + c] = sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4))
    return out


def reference_plug(null, ref=None):
    """rest 를 실어 나를 **기준 공간**의 월드 행렬 플러그.

    ref 를 주면 그 노드(보통 머리 조인트), 없으면 널의 **부모**를 기준으로 쓴다.
    널의 부모 그룹이 이미 머리를 따라간다면 기본값으로 충분하다.
    """
    if ref:
        return ref + ".worldMatrix[0]"
    return null + ".parentMatrix[0]"


def rest_local_matrix(null, ref=None):
    """지금 씬 포즈에서의 널 행렬을 **기준 공간**으로 옮긴 값(리스트 16).

    이 값이 "다물렸을 때의 자리"다. 기준 공간에 담아 두므로 머리가 회전하거나
    아바타가 이동해도 다물리는 자리가 얼굴을 따라간다.
    """
    world = cmds.getAttr(null + ".worldMatrix[0]")
    if ref:
        inverse = cmds.getAttr(ref + ".worldInverseMatrix[0]")
    else:
        inverse = cmds.getAttr(null + ".parentInverseMatrix[0]")
    return _mat_mul(world, inverse)


def _self_and_ancestors(node):
    """자신 + 모든 조상의 롱네임 집합."""
    long_name = _long(node)
    if not long_name:
        return set()
    parts = long_name.split("|")
    return set("|".join(parts[:i]) for i in range(2, len(parts) + 1))


def curve_movers(shape):
    """그 커브를 **무엇이 움직이나** — 스킨 인플루언스 / 커브를 끄는 컨스트레인트 타깃.

    입술 커브는 보통 머리에 스킨돼 있다. 그 인플루언스가 곧 "머리 공간"이다.
    """
    movers = []
    for skin in (cmds.ls(cmds.listHistory(shape) or [], type="skinCluster") or []):
        movers += cmds.skinCluster(skin, q=True, inf=True) or []
    transforms = cmds.listRelatives(shape, p=True, f=True) or []
    for transform in transforms:
        for con in (cmds.listConnections(transform, type="constraint") or []):
            cmd = getattr(cmds, cmds.nodeType(con), None)
            if cmd is None:
                continue
            try:
                movers += cmd(con, q=True, targetList=True) or []
            except Exception:
                pass
    out = []
    for mover in movers:
        long_name = _long(mover)
        if long_name and long_name not in out:
            out.append(long_name)
    return out


def rest_space_warnings(entries, reference=None):
    """rest 를 저장할 공간이 **얼굴을 따라가지 않을 것 같으면** 경고 문자열들.

    `Reference` 를 채웠으면 사용자가 공간을 직접 정한 것이므로 아무 말도 하지 않는다.
    비어 있으면 널의 부모가 기준인데, 그 부모가 커브를 움직이는 것(머리)을 따라가지
    않으면 머리를 돌렸을 때 다물리는 자리가 얼굴을 벗어난다 — 그 경우만 짚어 준다.
    """
    if reference:
        return []

    warnings = []
    orphans = [e["node"] for e in entries
               if not (cmds.listRelatives(e["node"], p=True) or [])]
    if orphans:
        warnings.append(
            "{0} driver(s) sit at the world root ('{1}'...), so their closed "
            "pose would be stored in world space. Set Reference to the head."
            .format(len(orphans), _leaf(orphans[0])))

    by_curve = {}
    for entry in entries:
        if entry.get("curve"):
            by_curve.setdefault(entry["curve"], []).append(entry["node"])
    for shape, nulls in sorted(by_curve.items()):
        movers = curve_movers(shape)
        if not movers:
            continue
        covered = any(mover in _self_and_ancestors(null)
                      for null in nulls for mover in movers)
        if not covered:
            warnings.append(
                "'{0}' moves with '{1}' but the drivers are not parented under "
                "it - set Reference to '{1}' (or whatever defines the head "
                "space), otherwise the sealed lips stay behind when the head "
                "turns.".format(_leaf(shape), _leaf(movers[0])))
    return warnings


def _rest_frame(null, ref, name):
    """rest 포즈를 기준 노드에 실어 라이브로 재생한다.

    Returns (월드행렬 플러그, 월드 위치 플러그, 만든 노드들)
    """
    mmx = _node("multMatrix", name + "_restMx")
    cmds.setAttr(mmx + ".matrixIn[0]", rest_local_matrix(null, ref), type="matrix")
    cmds.connectAttr(reference_plug(null, ref), mmx + ".matrixIn[1]", f=True)

    # Update Rest Pose 가 나중에 이 노드와 널을 다시 찾을 수 있게 표식을 남긴다.
    cmds.addAttr(mmx, longName=REST_NULL_TAG, attributeType="message")
    cmds.connectAttr(null + ".message", mmx + "." + REST_NULL_TAG, f=True)
    if ref:
        cmds.addAttr(mmx, longName=REST_REF_TAG, attributeType="message")
        cmds.connectAttr(ref + ".message", mmx + "." + REST_REF_TAG, f=True)

    dcm = _node("decomposeMatrix", name + "_restDcm")
    cmds.connectAttr(mmx + ".matrixSum", dcm + ".inputMatrix", f=True)
    return mmx + ".matrixSum", dcm + ".outputTranslate", [mmx, dcm]


def _rest_local_rotate(rest_world_plug, null, name):
    """rest 회전을 널의 **부모 공간**으로 (pairBlend.inRotate2 용)."""
    mmx = _node("multMatrix", name + "_restLocMx")
    cmds.connectAttr(rest_world_plug, mmx + ".matrixIn[0]", f=True)
    cmds.connectAttr(null + ".parentInverseMatrix[0]", mmx + ".matrixIn[1]", f=True)
    dcm = _node("decomposeMatrix", name + "_restLocDcm")
    cmds.connectAttr(mmx + ".matrixSum", dcm + ".inputMatrix", f=True)
    # 널의 회전 순서를 그대로 따라간다(기본 xyz 가 아닐 수도 있다).
    cmds.connectAttr(null + ".rotateOrder", dcm + ".inputRotateOrder", f=True)
    return dcm + ".outputRotate", [mmx, dcm]


def _position_plug(matrix_plug, name):
    """월드 행렬 -> 월드 위치 플러그."""
    dcm = _node("decomposeMatrix", name + "_dcm")
    cmds.connectAttr(matrix_plug, dcm + ".inputMatrix", f=True)
    return dcm + ".outputTranslate", [dcm]


def _meeting_point(up_plug, lo_plug, ctrl, name):
    """위/아래 위치를 sealBias 로 섞은 **만남점**. (1 = 위, 0 = 아래)"""
    bc = _node("blendColors", name)
    cmds.connectAttr(up_plug, bc + ".color1", f=True)
    cmds.connectAttr(lo_plug, bc + ".color2", f=True)
    cmds.connectAttr(ctrl + ".sealBias", bc + ".blender", f=True)
    return bc + ".output", [bc]


def _offset(live_point, rest_point, name):
    """만남점이 rest 에서 얼마나 옮겨 갔나(월드 벡터)."""
    pma = _node("plusMinusAverage", name)
    cmds.setAttr(pma + ".operation", 2)                    # 2 = subtract
    cmds.connectAttr(live_point, pma + ".input3D[0]", f=True)
    cmds.connectAttr(rest_point, pma + ".input3D[1]", f=True)
    return pma + ".output3D", [pma]


def _seal_translate(rest_point, offset_plug, live_point, ctrl, null, name):
    """목표 위치 -> 널의 부모 공간 translate.

        keep  = rest 자리 + 만남점 이동량        (sealMerge = 0, 기본)
        merge = 만남점 그 자체                   (sealMerge = 1)
        목표  = lerp(keep, merge, sealMerge)

    `keep` 은 위/아래가 **같은 이동량**을 받으므로 rest 의 간격(입술 두께)이 그대로
    유지된다. `merge` 는 v01.19 까지의 동작으로, 위/아래 널이 **한 점에서 정확히 만난다**.
    """
    pma = _node("plusMinusAverage", name + "_add")
    cmds.connectAttr(rest_point, pma + ".input3D[0]", f=True)
    cmds.connectAttr(offset_plug, pma + ".input3D[1]", f=True)

    bc = _node("blendColors", name + "_merge")
    cmds.connectAttr(live_point, bc + ".color1", f=True)          # blender = 1
    cmds.connectAttr(pma + ".output3D", bc + ".color2", f=True)   # blender = 0
    cmds.connectAttr(ctrl + ".sealMerge", bc + ".blender", f=True)

    pmm = _node("pointMatrixMult", name + "_local")
    cmds.connectAttr(bc + ".output", pmm + ".inPoint", f=True)
    cmds.connectAttr(null + ".parentInverseMatrix[0]", pmm + ".inMatrix", f=True)
    return pmm + ".output", [pma, bc, pmm]


def _zip_weight(ctrl, seal_attr, u, one_minus_band, name):
    """지퍼 가중치 한 방향 : ramp(seal - u*(1-band), 0..band).

    band 를 라이브로 쓰기 위해 `u*(1-band)` 를 노드로 계산한다. 마지막 remapValue 는
    0..band 를 0..1 로 매핑하며(=클램프) 값 램프로 이징까지 줄 수 있다.
    """
    mul = _node("multiplyDivide", name + "_off")
    cmds.setAttr(mul + ".input1X", u)
    cmds.connectAttr(one_minus_band, mul + ".input2X", f=True)

    sub = _node("plusMinusAverage", name + "_sub")
    cmds.setAttr(sub + ".operation", 2)                    # 2 = subtract
    cmds.connectAttr(ctrl + "." + seal_attr, sub + ".input1D[0]", f=True)
    cmds.connectAttr(mul + ".outputX", sub + ".input1D[1]", f=True)

    rv = _node("remapValue", name + "_rv")
    cmds.connectAttr(sub + ".output1D", rv + ".inputValue", f=True)
    cmds.setAttr(rv + ".inputMin", 0.0)
    cmds.connectAttr(ctrl + ".sealBand", rv + ".inputMax", f=True)
    return rv + ".outValue", [mul, sub, rv]


def rotation_driven(null):
    """그 널의 rotate 를 커브(또는 무엇이든)가 구동하고 있나."""
    return bool(cmds.listConnections(null + ".rotate", s=True, d=False,
                                     plugs=True))


def _insert_pair_blend(null, seal_t, seal_r, weight_plug, name):
    """커브 구동과 seal 자리 사이에 pairBlend 를 끼운다. (pairBlend, 회전도 섞었나)

    회전은 **커브가 회전까지 구동하고 있을 때만** 끼운다(`seal_r` 이 있을 때).
    Edge Loop 를 `orient` 없이 만들었으면 널의 rotate 는 연결 없는 정적 값 —
    그게 이미 rest 회전이라 건드릴 이유가 없다.
    """
    src_t = cmds.listConnections(null + ".translate", s=True, d=False,
                                 plugs=True) or []
    if not src_t:
        raise RuntimeError(
            "'{0}' translate is not driven by a curve network.".format(_leaf(null)))

    pb = _node("pairBlend", name + "_pb")
    cmds.connectAttr(src_t[0], pb + ".inTranslate1", f=True)
    cmds.connectAttr(seal_t, pb + ".inTranslate2", f=True)
    cmds.connectAttr(weight_plug, pb + ".weight", f=True)
    cmds.connectAttr(pb + ".outTranslate", null + ".translate", f=True)

    rotated = False
    if seal_r:
        src_r = cmds.listConnections(null + ".rotate", s=True, d=False,
                                     plugs=True) or []
        if src_r:
            cmds.connectAttr(src_r[0], pb + ".inRotate1", f=True)
            cmds.connectAttr(seal_r, pb + ".inRotate2", f=True)
            # 0 = Euler, 1 = Quaternion. 회전 블렌드는 쿼터니언이 안정적이다.
            cmds.setAttr(pb + ".rotInterpolation", 1)
            cmds.connectAttr(pb + ".outRotate", null + ".rotate", f=True)
            rotated = True
    return pb, rotated


# ============================================================ 빌드 / 제거

def seal_set_name(prefix):
    return "{0}_seal_SET".format(prefix or DEFAULT_PREFIX)


def build_seal(upper, lower, controller, prefix=DEFAULT_PREFIX, axis="x",
               start_at_min=True, skip_corners=True, bias=0.5, band=0.35,
               metric=METRIC_PARAM, tolerance=None, blend_rotation=True,
               reference=None, merge=0.0):
    """입술 지퍼 셋업을 만든다.

    **씬은 입술이 다물린(중립) 포즈여야 한다** — 지금 포즈가 곧 다물렸을 때의 자리(rest)다.

    Args:
        upper, lower: 위/아래 입술의 널(또는 그 조인트) 이름들.
        controller: sealR / sealL / sealBias / sealBand / sealMerge 를 올릴 컨트롤러.
        prefix: 생성 노드 이름 접두사.
        axis / start_at_min: 지퍼 시작 끝을 정하는 월드 축과 방향.
        skip_corners: 입 끝(u≈0, 1) 조인트는 건드리지 않는다.
        bias / band / merge: 어트리뷰트 초기값.
        metric / tolerance: 짝짓기 척도와 최대 허용치(`pair_drivers` 참고).
        blend_rotation: True 면 다물릴 때 회전을 **rest(다물리기 전) 회전**으로 되돌린다.
            커브가 회전까지 구동하고 있는 널에만 노드가 붙는다(Edge Loop 의 orient 옵션).
        reference: rest 를 저장할 기준 노드(보통 머리 조인트). None 이면 각 널의 **부모**.
            널 그룹이 이미 머리를 따라간다면 None 으로 충분하다.
        merge: `sealMerge` 초기값. 0 = 위/아래가 rest 간격을 지킨 채 만난다(기본),
            1 = 위/아래 널이 만남점 한 점에서 정확히 일치한다(v01.19 까지의 동작).

    Returns:
        report dict — pairs / nodes / set / attrs / skipped / flipped.
    """
    prefix = (prefix or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX
    if reference:
        reference = _long(reference)
        if reference is None:
            raise ValueError("Reference node not found in the scene.")

    up_entries, lo_entries, info = prepare_sides(upper, lower, axis, start_at_min)
    if not up_entries or not lo_entries:
        if info["dropped"]:
            # 닫힌 커브를 양쪽 리스트에 통째로 담으면 두 쪽이 같은 널 집합이 된다.
            raise ValueError(
                "Upper and Lower resolve to the same {0} driver(s). With one "
                "curve around both lips, list each lip's nulls separately "
                "instead of the whole curve in both.".format(len(info["dropped"])))
        raise ValueError("Both Upper and Lower need curve-attached drivers "
                         "(got {0} / {1}).".format(len(up_entries), len(lo_entries)))

    flipped_up, flipped_lo = info["flipped"]

    pairs, skipped = pair_drivers(up_entries, lo_entries, skip_corners,
                                  metric=metric, tolerance=tolerance)
    skipped = list(info["dropped"]) + skipped
    if not pairs:
        raise ValueError("No pair could be matched (all corners / no lower "
                         "drivers).")

    existing = seal_set_name(prefix)
    if cmds.objExists(existing):
        remove_seal(prefix)

    made_attrs = ensure_attrs(controller, band=band, bias=bias, merge=merge)

    created = []
    rotated_count = 0
    # band 는 여러 쌍이 공유한다 : 1 - band 를 한 번만 만든다.
    omb = _node("plusMinusAverage", "{0}_seal_oneMinusBand".format(prefix))
    cmds.setAttr(omb + ".operation", 2)
    cmds.setAttr(omb + ".input1D[0]", 1.0)
    cmds.connectAttr(controller + ".sealBand", omb + ".input1D[1]", f=True)
    created.append(omb)
    one_minus_band = omb + ".output1D"

    for i, (up, lo, u) in enumerate(pairs):
        name = "{0}_seal_{1:02d}".format(prefix, i + 1)

        # (1) 커브가 지금 말하는 위/아래 자리 -> sealBias 로 섞은 **만남점**.
        up_plug, up_nodes = attach_matrix_plug(up["node"], name + "_up")
        lo_plug, lo_nodes = attach_matrix_plug(lo["node"], name + "_lo")
        up_live, n_up = _position_plug(up_plug, name + "_upLive")
        lo_live, n_lo = _position_plug(lo_plug, name + "_loLive")
        live_point, n_live = _meeting_point(up_live, lo_live, controller,
                                            name + "_liveMid")
        created += up_nodes + lo_nodes + n_up + n_lo + n_live

        # (2) rest(= 지금 씬 포즈)를 기준 공간에 담아 라이브로 재생 + 그 만남점.
        #     pairBlend 를 끼우기 **전에** 읽어야 커브가 주는 자리를 그대로 잡는다.
        rest = {}
        for side, entry in (("Up", up), ("Lo", lo)):
            world_mx, rest_point, nodes = _rest_frame(
                entry["node"], reference, name + "_" + side)
            rest[side] = (world_mx, rest_point)
            created += nodes
        rest_mid, n_rest = _meeting_point(rest["Up"][1], rest["Lo"][1],
                                          controller, name + "_restMid")
        offset_plug, n_off = _offset(live_point, rest_mid, name + "_delta")
        created += n_rest + n_off

        w_r, nodes_r = _zip_weight(controller, "sealR", u, one_minus_band,
                                   name + "_R")
        w_l, nodes_l = _zip_weight(controller, "sealL", 1.0 - u, one_minus_band,
                                   name + "_L")
        created += nodes_r + nodes_l

        # 두 방향 합성 : 더한 뒤 0~1 로 자른다.
        add = _node("plusMinusAverage", name + "_sum")
        cmds.connectAttr(w_r, add + ".input1D[0]", f=True)
        cmds.connectAttr(w_l, add + ".input1D[1]", f=True)
        clamp = _node("clamp", name + "_clamp")
        cmds.setAttr(clamp + ".minR", 0.0)
        cmds.setAttr(clamp + ".maxR", 1.0)
        cmds.connectAttr(add + ".output1D", clamp + ".inputR", f=True)
        created += [add, clamp]
        weight_plug = clamp + ".outputR"

        for side, entry in (("Up", up), ("Lo", lo)):
            null = entry["node"]
            side_name = name + "_" + side
            world_mx, rest_point = rest[side]

            seal_t, nodes = _seal_translate(rest_point, offset_plug, live_point,
                                            controller, null, side_name)
            created += nodes

            seal_r = None
            if blend_rotation and rotation_driven(null):
                seal_r, rot_nodes = _rest_local_rotate(world_mx, null, side_name)
                created += rot_nodes

            pb, rotated = _insert_pair_blend(null, seal_t, seal_r, weight_plug,
                                             side_name)
            created += [pb]
            if rotated:
                rotated_count += 1

    node_set = cmds.sets(created, name=seal_set_name(prefix))
    # Update Rest Pose 가 컨트롤러를 다시 찾을 수 있도록.
    cmds.addAttr(node_set, longName=SET_CTRL_TAG, attributeType="message")
    cmds.connectAttr(controller + ".message", node_set + "." + SET_CTRL_TAG,
                     f=True)

    return {
        "pairs": [(_leaf(u["node"]), _leaf(l["node"]), u_val)
                  for u, l, u_val in pairs],
        "nodes": created,
        "set": node_set,
        "attrs": made_attrs,
        "skipped": skipped,
        "flipped": (flipped_up, flipped_lo),
        "controller": controller,
        "rotated": rotated_count,
        "reference": reference,
        "space_warnings": rest_space_warnings(
            [e for pair in pairs for e in pair[:2]], reference),
        "shared_curve": info["shared_curve"],
        "closed": info["closed"],
        "respanned": info["respanned"],
    }


def seal_controller(prefix=DEFAULT_PREFIX):
    """그 prefix 로 빌드한 seal 이 쓰는 컨트롤러(없으면 None)."""
    node_set = seal_set_name(prefix)
    if not cmds.objExists(node_set):
        return None
    if not cmds.attributeQuery(SET_CTRL_TAG, node=node_set, exists=True):
        return None
    found = cmds.listConnections(node_set + "." + SET_CTRL_TAG, s=True,
                                 d=False) or []
    return found[0] if found else None


def recapture_rest(prefix=DEFAULT_PREFIX):
    """**지금 씬 포즈**를 새 rest(다물렸을 때의 자리)로 다시 잡는다.

    리그를 다시 만들지 않고 rest 행렬만 갈아 끼운다. 읽는 동안 `sealR` / `sealL` 을
    잠깐 0 으로 내려 **커브가 주는 자리**(다물리기 전)를 읽고, 전부 읽은 뒤에 쓴다.

    Returns (갱신한 널 개수, 컨트롤러)
    """
    node_set = seal_set_name(prefix)
    if not cmds.objExists(node_set):
        raise ValueError("No seal to update for prefix '{0}' ({1})."
                         .format(prefix, node_set))

    members = [n for n in (cmds.sets(node_set, q=True) or []) if cmds.objExists(n)]
    marks = [n for n in members
             if cmds.attributeQuery(REST_NULL_TAG, node=n, exists=True)]
    if not marks:
        raise ValueError("This seal was built by an older version - rebuild it "
                         "once to enable Update Rest Pose.")

    controller = seal_controller(prefix)
    saved = {}
    if controller:
        for attr in ("sealR", "sealL"):
            plug = controller + "." + attr
            if not cmds.objExists(plug):
                continue
            if not cmds.getAttr(plug, settable=True):
                raise RuntimeError(
                    "'{0}' is locked or connected - set it to 0 yourself, then "
                    "run Update Rest Pose.".format(plug))
            saved[plug] = cmds.getAttr(plug)
            cmds.setAttr(plug, 0.0)

    try:
        updates = []
        for mmx in marks:
            null = (cmds.listConnections(mmx + "." + REST_NULL_TAG, s=True,
                                         d=False) or [None])[0]
            if not null:
                continue
            ref = None
            if cmds.attributeQuery(REST_REF_TAG, node=mmx, exists=True):
                ref = (cmds.listConnections(mmx + "." + REST_REF_TAG, s=True,
                                            d=False) or [None])[0]
            # 쓰기 전에 전부 읽는다 — 하나를 쓰면 그 널이 곧바로 움직인다.
            updates.append((mmx, rest_local_matrix(null, ref)))
    finally:
        for plug, value in saved.items():
            try:
                cmds.setAttr(plug, value)
            except Exception:
                pass

    for mmx, matrix in updates:
        cmds.setAttr(mmx + ".matrixIn[0]", matrix, type="matrix")
    return len(updates), controller


def remove_seal(prefix=DEFAULT_PREFIX):
    """빌드한 seal 네트워크를 걷어내고 **원래 커브 연결로 되돌린다**.

    pairBlend 의 in1(원래 커브 구동)을 다시 널 translate 로 이어 준 뒤 노드를 지운다.
    컨트롤러의 어트리뷰트는 **지우지 않는다**(키가 걸려 있을 수 있다).
    Returns (restored_count, deleted_count)
    """
    node_set = seal_set_name(prefix)
    if not cmds.objExists(node_set):
        return (0, 0)

    members = cmds.sets(node_set, q=True) or []
    restored = 0
    for pb in cmds.ls(members, type="pairBlend") or []:
        # translate 와 rotate 를 모두 원래 소스로 되돌린다(회전을 섞은 경우 대비).
        for in_attr, out_attr in (("inTranslate1", "outTranslate"),
                                  ("inRotate1", "outRotate")):
            src = cmds.listConnections(pb + "." + in_attr, s=True, d=False,
                                       plugs=True) or []
            dst = cmds.listConnections(pb + "." + out_attr, s=False, d=True,
                                       plugs=True) or []
            if not src or not dst:
                continue
            for plug in dst:
                try:
                    cmds.connectAttr(src[0], plug, force=True)
                    restored += 1
                except Exception:
                    pass

    alive = [n for n in members if cmds.objExists(n)]
    if alive:
        cmds.delete(alive)
    if cmds.objExists(node_set):
        cmds.delete(node_set)
    return (restored, len(alive))
