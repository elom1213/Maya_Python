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
# 1. 조인트 쌍(위 i, 아래 i)의 **커브 위 두 점을 blendColors 로 섞은 점**이 "다물렸을 때의
#    자리"다. blender = sealBias (0 = 아랫입술 자리, 0.5 = 중간, 1 = 윗입술 자리).
#    커브가 움직이면 이 점도 따라 움직인다(라이브).
# 2. 각 조인트의 **입술 위 위치 u**(0~1)에 따라 닫히는 타이밍이 다르다:
#        w_R = ramp( sealR - u*(1-band),  0..band )      # u=0 쪽 끝에서 시작
#        w_L = ramp( sealL - (1-u)*(1-band), 0..band )   # 반대쪽 끝에서 시작
#        w   = clamp01(w_R + w_L)
#    sealR/sealL 이 독립이라 **양 끝에서 중앙으로** 동시에 다물 수 있다.
# 3. 기존 `decomposeMatrix -> null.translate` 사이에 **pairBlend** 를 끼워
#    in1 = 커브 구동, in2 = seal 자리, weight = w 로 섞는다.
#
# ## u 는 생성 순서가 아니라 **커브 파라미터**에서 얻는다
#
# 실측: Edge Loop 로 만든 `up_null_01..09` 의 정규화 파라미터가 1.0 -> 0.0 **역순**이었다.
# 이름/생성 순서로 좌우를 판단하면 지퍼가 뒤집힌다. 그래서 널의 POCI `.parameter` 를
# 커브 minValue/maxValue 로 정규화해 쓰고, 위/아래 커브 방향이 서로 반대면 자동으로 뒤집는다.
#
# UI 비의존: 위젯에서 읽은 이름/옵션 값만 받는다.

import maya.cmds as cmds


# 컨트롤러에 만드는 어트리뷰트 (이름, min, max, 기본값)
SEAL_ATTRS = (
    ("sealR", 0.0, 1.0, 0.0),
    ("sealL", 0.0, 1.0, 0.0),
    ("sealBias", 0.0, 1.0, 0.5),
    ("sealBand", 0.02, 1.0, 0.35),
)

# 좌우 판정 축
AXES = ("x", "y", "z")
_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}

# 코너(입 끝)로 보고 건너뛸 u 여유
CORNER_EPS = 0.02

DEFAULT_PREFIX = "lipSeal"


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


def resolve_driver(node):
    """리스트에 조인트를 넣어도 되도록, 커브에 어태치된 **널**을 찾아 준다.

    - 그 노드 자체가 커브 구동이면 그대로.
    - 아니면 그 노드를 끄는 parentConstraint 의 타깃을 따라 올라가며 찾는다
      (Edge Loop 가 만든 joint <- tgt <- ctl <- con <- null 계층도 이 경로로 잡힌다).
    """
    node = _long(node)
    if node is None:
        return None
    if poci_of(node):
        return node

    for con in (cmds.listConnections(node, type="parentConstraint") or []):
        try:
            targets = cmds.parentConstraint(con, q=True, targetList=True) or []
        except Exception:
            targets = []
        for tgt in targets:
            tgt = _long(tgt)
            if tgt and poci_of(tgt):
                return tgt
            # tgt(_tgt) -> ctl -> con -> null 로 부모를 거슬러 올라가 본다.
            parent = tgt
            for _ in range(4):
                parents = cmds.listRelatives(parent, p=True, f=True) or []
                if not parents:
                    break
                parent = parents[0]
                if poci_of(parent):
                    return parent
    return None


def normalized_param(node):
    """커브 위 정규화 파라미터 u(0~1). 커브 구동이 아니면 None."""
    poci = poci_of(node)
    if not poci:
        return None
    shapes = cmds.listConnections(poci + ".inputCurve", s=True, d=False,
                                  shapes=True) or []
    if not shapes:
        return None
    lo = cmds.getAttr(shapes[0] + ".minValue")
    hi = cmds.getAttr(shapes[0] + ".maxValue")
    p = cmds.getAttr(poci + ".parameter")
    return (p - lo) / (hi - lo) if hi > lo else 0.0


def collect_drivers(nodes):
    """이름 목록 -> [{node, poci, u, pos}] (커브에 어태치된 것만). u 순서로 정렬하지 않는다."""
    out = []
    for name in nodes or []:
        driver = resolve_driver(name)
        if not driver:
            continue
        u = normalized_param(driver)
        if u is None:
            continue
        out.append({
            "node": driver,
            "poci": poci_of(driver),
            "u": u,
            "pos": cmds.xform(driver, q=True, ws=True, t=True),
        })
    return out


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


def pair_drivers(upper, lower, skip_corners=True):
    """위/아래를 **정규화 파라미터 최근접**으로 짝짓는다.

    이름/생성 순서로 짝지으면 커브 방향이 다를 때 어긋난다(위 모듈 주석 참고).
    반환: ([(up_entry, lo_entry, u), ...], skipped)
    """
    pairs = []
    skipped = []
    for up in upper:
        if skip_corners and (up["u"] < CORNER_EPS or up["u"] > 1.0 - CORNER_EPS):
            skipped.append((up["node"], "corner"))
            continue
        best = min(lower, key=lambda lo: abs(lo["u"] - up["u"])) if lower else None
        if best is None:
            skipped.append((up["node"], "no lower driver"))
            continue
        if skip_corners and (best["u"] < CORNER_EPS or best["u"] > 1.0 - CORNER_EPS):
            skipped.append((up["node"], "paired with a corner"))
            continue
        pairs.append((up, best, (up["u"] + best["u"]) * 0.5))
    return pairs, skipped


# ============================================================ 어트리뷰트

def ensure_attrs(controller, band=None, bias=None):
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
    if band is not None:
        try:
            cmds.setAttr(controller + ".sealBand", max(0.02, float(band)))
        except Exception:
            pass
    if bias is not None:
        try:
            cmds.setAttr(controller + ".sealBias", float(bias))
        except Exception:
            pass
    return made


# ============================================================ 노드 그래프

def _node(kind, name):
    return cmds.createNode(kind, name=name)


def _seal_point(up_poci, lo_poci, ctrl, name):
    """다물리는 목표 지점(월드) — 위/아래 커브 점을 sealBias 로 섞는다.

    blendColors: blender=1 -> color1(위), 0 -> color2(아래).
    """
    bc = _node("blendColors", name + "_bias")
    cmds.connectAttr(up_poci + ".position", bc + ".color1", f=True)
    cmds.connectAttr(lo_poci + ".position", bc + ".color2", f=True)
    cmds.connectAttr(ctrl + ".sealBias", bc + ".blender", f=True)
    # blendColors 의 출력 성분은 R/G/B 다(X/Y/Z 가 아니다) -> 성분 플러그를 그대로 돌려준다.
    return bc, (bc + ".outputR", bc + ".outputG", bc + ".outputB")


def _to_local(point_components, null, name):
    """월드 점(성분 플러그 3개) -> null 부모 공간 로컬 translate(attach_curve 와 같은 패턴)."""
    fbf = _node("fourByFourMatrix", name + "_fbf")
    for src, row in zip(point_components, ("in30", "in31", "in32")):
        cmds.connectAttr(src, "{0}.{1}".format(fbf, row), f=True)
    mmx = _node("multMatrix", name + "_mmx")
    cmds.connectAttr(fbf + ".output", mmx + ".matrixIn[0]", f=True)
    cmds.connectAttr(null + ".parentInverseMatrix[0]", mmx + ".matrixIn[1]", f=True)
    dcm = _node("decomposeMatrix", name + "_dcm")
    cmds.connectAttr(mmx + ".matrixSum", dcm + ".inputMatrix", f=True)
    return dcm + ".outputTranslate", [fbf, mmx, dcm]


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


def _insert_pair_blend(null, seal_plug, weight_plug, name):
    """decomposeMatrix -> null.translate 사이에 pairBlend 를 끼운다."""
    src = cmds.listConnections(null + ".translate", s=True, d=False,
                               plugs=True) or []
    if not src:
        raise RuntimeError(
            "'{0}' translate is not driven by a curve network.".format(_leaf(null)))
    pb = _node("pairBlend", name + "_pb")
    cmds.connectAttr(src[0], pb + ".inTranslate1", f=True)
    cmds.connectAttr(seal_plug, pb + ".inTranslate2", f=True)
    cmds.connectAttr(weight_plug, pb + ".weight", f=True)
    cmds.connectAttr(pb + ".outTranslate", null + ".translate", f=True)
    return pb


# ============================================================ 빌드 / 제거

def seal_set_name(prefix):
    return "{0}_seal_SET".format(prefix or DEFAULT_PREFIX)


def build_seal(upper, lower, controller, prefix=DEFAULT_PREFIX, axis="x",
               start_at_min=True, skip_corners=True, bias=0.5, band=0.35):
    """입술 지퍼 셋업을 만든다.

    Args:
        upper, lower: 위/아래 입술의 널(또는 그 조인트) 이름들.
        controller: sealR / sealL / sealBias / sealBand 를 올릴 컨트롤러.
        prefix: 생성 노드 이름 접두사.
        axis / start_at_min: 지퍼 시작 끝을 정하는 월드 축과 방향.
        skip_corners: 입 끝(u≈0, 1) 조인트는 건드리지 않는다.
        bias / band: 어트리뷰트 초기값.

    Returns:
        report dict — pairs / nodes / set / attrs / skipped / flipped.
    """
    prefix = (prefix or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX

    up_entries = collect_drivers(upper)
    lo_entries = collect_drivers(lower)
    if not up_entries or not lo_entries:
        raise ValueError("Both Upper and Lower need curve-attached drivers "
                         "(got {0} / {1}).".format(len(up_entries), len(lo_entries)))

    flipped_up = orient_u(up_entries, axis, start_at_min)
    flipped_lo = orient_u(lo_entries, axis, start_at_min)

    pairs, skipped = pair_drivers(up_entries, lo_entries, skip_corners)
    if not pairs:
        raise ValueError("No pair could be matched (all corners / no lower "
                         "drivers).")

    existing = seal_set_name(prefix)
    if cmds.objExists(existing):
        remove_seal(prefix)

    made_attrs = ensure_attrs(controller, band=band, bias=bias)

    created = []
    # band 는 여러 쌍이 공유한다 : 1 - band 를 한 번만 만든다.
    omb = _node("plusMinusAverage", "{0}_seal_oneMinusBand".format(prefix))
    cmds.setAttr(omb + ".operation", 2)
    cmds.setAttr(omb + ".input1D[0]", 1.0)
    cmds.connectAttr(controller + ".sealBand", omb + ".input1D[1]", f=True)
    created.append(omb)
    one_minus_band = omb + ".output1D"

    for i, (up, lo, u) in enumerate(pairs):
        name = "{0}_seal_{1:02d}".format(prefix, i + 1)

        bias_node, point_components = _seal_point(up["poci"], lo["poci"],
                                                  controller, name)
        created.append(bias_node)

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
            local_plug, nodes = _to_local(point_components, entry["node"],
                                          name + "_" + side)
            pb = _insert_pair_blend(entry["node"], local_plug, weight_plug,
                                    name + "_" + side)
            created += nodes + [pb]

    node_set = cmds.sets(created, name=seal_set_name(prefix))

    return {
        "pairs": [(_leaf(u["node"]), _leaf(l["node"]), u_val)
                  for u, l, u_val in pairs],
        "nodes": created,
        "set": node_set,
        "attrs": made_attrs,
        "skipped": skipped,
        "flipped": (flipped_up, flipped_lo),
        "controller": controller,
    }


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
        src = cmds.listConnections(pb + ".inTranslate1", s=True, d=False,
                                   plugs=True) or []
        dst = cmds.listConnections(pb + ".outTranslate", s=False, d=True,
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
