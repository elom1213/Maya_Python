# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00400_CurveTool core - 커브 -> 커브 Wrap (CV 개수가 달라도 모양을 맞춘다). UI 비의존.
#
# 마야 기본 `wrap` 디포머로도 커브끼리 묶을 수는 있지만 결과가 불안정해 실무에 못 쓴다.
# 여기서는 디포머 대신 **마야가 이미 정확히 계산해 주는 것**을 쓴다.
#
#   driverShape.worldSpace ─▶ rebuildCurve ─▶ transformGeometry ─▶ target 커브
#                              (driven 의 span/degree 로 재구성)   (driven 로컬 공간으로)
#   target 커브 ─▶ blendShape(driven) 의 타깃,  weight = envelope
#
# `rebuildCurve` 는 "같은 모양을 다른 CV 개수로 다시 표현"하는 노드다. driven 커브의
# span/degree 로 driver 를 재구성하면 CV 개수가 driven 과 정확히 같아지고, 그러면
# blendShape 의 타깃으로 그대로 쓸 수 있다. 노드로 남으므로 **라이브**다.
#
# envelope 은 driven 트랜스폼에 붙는 [0, 1] 실수 어트리뷰트이고 blendShape weight 에
# 연결된다. 0 이면 원래 모양, 1 이면 driver 모양 — blendShape 의 envelope 과 같은 감각.
#
# ── mayapy 로 확인한 사실 ──────────────────────────────────────────────────
#  * rebuildCurve 노드는 driver CV 를 움직이면 그대로 따라온다(라이브).
#  * 12CV driven ← 4CV driver 는 편차 최대 0.0013 — 사실상 정확히 일치.
#  * 노트 벡터의 **범위(0~1 vs 0~9)가 달라도 결과는 같다**. 균등 간격이면 무관하다.
#    반대로 **간격이 불균등하면 오차가 커진다**(같은 조건에서 0.169 → 0.442).
#  * **form(open/periodic)이 다르면 결과가 망가진다**(편차 10.77). CV 개수가 우연히
#    같으면 blendShape 이 에러도 없이 만들어지므로 미리 막아야 한다.
#  * CV 개수가 다르면 blendShape 이 "Target ... does not match with base" 로 거절한다.
#  * blendShape weight 는 **음수를 받는다** → Preserve Offset 을 타깃 두 개로 만들 수 있다.

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from Framework.core.maya_shape import shape_path
from Framework.core.maya_undo import undo_chunk

# 이 툴이 만든 blendShape 임을 표시하는 태그. 제거할 때 이걸로 찾는다.
WRAP_TAG = "junCurveWrap"

DEFAULT_ENVELOPE_ATTR = "wrapEnvelope"

# 편차 측정 샘플 수
SAMPLES = 60


# ==========================================================================
# 커브 조회
# ==========================================================================

def curve_shape(node):
    """트랜스폼이든 셰이프든 nurbsCurve 셰이프의 롱네임. 없으면 None.

    셰이프 해석은 공용 헬퍼를 쓴다(extendToShape 로 직접 뒤지면 인터미디어트를 집는다).
    """
    if not node or not cmds.objExists(node):
        return None

    shape = shape_path(node, type_="nurbsCurve")

    # shape_path 는 이미 셰이프인 노드를 타입을 가리지 않고 그대로 돌려준다
    # (메시 셰이프를 넣으면 메시가 나온다) → 여기서 한 번 더 확인한다.
    if shape and cmds.nodeType(shape) == "nurbsCurve":
        return shape

    return None


def _fn(shape):
    sel = om2.MSelectionList()
    sel.add(shape)
    return om2.MFnNurbsCurve(sel.getDagPath(0))


def curve_info(shape):
    """CV 수 / span / degree / form / 노트."""
    fn = _fn(shape)

    return {
        "shape": shape,
        "cvs": fn.numCVs,
        "spans": fn.numSpans,
        "degree": fn.degree,
        "form": int(fn.form),          # 1 = open, 2 = closed, 3 = periodic
        "knots": list(fn.knots()),
        "length": fn.length(),
    }


def form_name(form):
    return {1: "open", 2: "closed", 3: "periodic"}.get(form, "unknown({0})".format(form))


def is_uniform(info):
    """노트 간격이 균등한가.

    간격이 불균등하면 driver 를 아무리 잘 재구성해도 driven 의 노트로 다시 해석될 때
    모양이 어긋난다(실측). 그래서 미리 알려 준다.
    """
    knots = info["knots"]
    degree = info["degree"]

    lo = degree - 1
    hi = len(knots) - (degree - 1)

    breaks = knots[lo:hi]

    if len(breaks) < 3:
        return True

    gaps = [breaks[i + 1] - breaks[i] for i in range(len(breaks) - 1)]
    span = max(gaps)

    if span <= 0.0:
        return True

    return (max(gaps) - min(gaps)) / span < 1e-4


def deviation(shape_a, shape_b, samples=SAMPLES):
    """두 커브를 호 길이 등간격으로 샘플해 대응점 거리의 (최대, 평균). 월드 기준."""
    fa, fb = _fn(shape_a), _fn(shape_b)

    la, lb = fa.length(), fb.length()

    distances = []

    for i in range(samples):
        t = i / float(samples - 1)
        pa = fa.getPointAtParam(fa.findParamFromLength(la * t), om2.MSpace.kWorld)
        pb = fb.getPointAtParam(fb.findParamFromLength(lb * t), om2.MSpace.kWorld)
        distances.append((pa - pb).length())

    return max(distances), sum(distances) / len(distances)


# ==========================================================================
# 검사
# ==========================================================================

def check(driver, driven):
    """wrap 을 걸 수 있는지 본다. (에러, 경고목록, 정보) 를 돌려준다."""
    warnings = []

    driver_shape = curve_shape(driver)
    driven_shape = curve_shape(driven)

    if not driver_shape:
        return "Driver is not a NURBS curve: {0}".format(driver), warnings, None

    if not driven_shape:
        return "Driven is not a NURBS curve: {0}".format(driven), warnings, None

    if driver_shape == driven_shape:
        return "Driver and driven are the same curve.", warnings, None

    driver_info = curve_info(driver_shape)
    driven_info = curve_info(driven_shape)

    # form 이 다르면 CV 개수가 우연히 맞아도 결과가 망가진다(실측 편차 10.77).
    if driver_info["form"] != driven_info["form"]:
        return ("Curve forms differ - driver is {0}, driven is {1}. "
                "Wrapping across forms produces a broken shape.".format(
                    form_name(driver_info["form"]), form_name(driven_info["form"])),
                warnings, None)

    if find_wrap(driven_shape):
        return "'{0}' already has a curve wrap. Remove it first.".format(driven), warnings, None

    if not is_uniform(driven_info):
        warnings.append(
            "The driven curve has non-uniform knots. The wrap still works but cannot be exact "
            "- turn on 'Uniform-rebuild driven' for a precise match (it slightly changes the "
            "driven curve's own shape).")

    if driven_info["cvs"] < driver_info["cvs"]:
        warnings.append(
            "The driven curve has fewer CVs ({0}) than the driver ({1}); it can only "
            "approximate the driver's shape.".format(driven_info["cvs"], driver_info["cvs"]))

    return None, warnings, {"driver": driver_info, "driven": driven_info}


# ==========================================================================
# 조회 / 제거
# ==========================================================================

def find_wrap(driven):
    """driven 에 걸린 이 툴의 blendShape. 없으면 None."""
    shape = curve_shape(driven)

    if not shape:
        return None

    for node in (cmds.listHistory(shape, pruneDagObjects=True) or []):
        if cmds.nodeType(node) == "blendShape" and cmds.objExists(node + "." + WRAP_TAG):
            return node

    return None


def wrap_nodes(blend_node):
    """blendShape 에 딸린 셋업 노드들(중간 커브 그룹, rebuild, transformGeometry 등)."""
    nodes = set([blend_node])

    for node in (cmds.listHistory(blend_node, pruneDagObjects=False) or []):
        if cmds.nodeType(node) in ("rebuildCurve", "transformGeometry", "multMatrix",
                                   "multDoubleLinear"):
            nodes.add(node)

    group = None

    if cmds.objExists(blend_node + ".junWrapGroup"):
        linked = cmds.listConnections(blend_node + ".junWrapGroup") or []
        group = linked[0] if linked else None

    return sorted(nodes), group


def envelope_attr(blend_node):
    """이 wrap 을 구동하는 envelope 어트리뷰트 이름(`curve.wrapEnvelope`). 없으면 None."""
    sources = cmds.listConnections(blend_node + ".weight[0]", plugs=True, source=True,
                                   destination=False) or []

    return sources[0] if sources else None


def remove_wrap(driven):
    """wrap 셋업을 걷어낸다. driven 커브는 원래 모양으로 돌아간다."""
    blend_node = find_wrap(driven)

    if not blend_node:
        return "No curve wrap found on '{0}'.".format(driven)

    attr = envelope_attr(blend_node)
    nodes, group = wrap_nodes(blend_node)

    with undo_chunk():
        # 어트리뷰트 먼저 끊고 지운다(연결이 남은 채 노드를 지우면 경고가 난다).
        if attr and cmds.objExists(attr):
            cmds.deleteAttr(attr)

        for node in nodes:
            if cmds.objExists(node):
                cmds.delete(node)

        if group and cmds.objExists(group):
            cmds.delete(group)

    return None


def get_envelope(driven):
    blend_node = find_wrap(driven)

    if not blend_node:
        return None

    attr = envelope_attr(blend_node)

    return cmds.getAttr(attr) if attr and cmds.objExists(attr) else None


def set_envelope(driven, value):
    blend_node = find_wrap(driven)

    if not blend_node:
        return False

    attr = envelope_attr(blend_node)

    if not attr or not cmds.objExists(attr):
        return False

    cmds.setAttr(attr, max(0.0, min(1.0, float(value))))

    return True


# ==========================================================================
# 생성
# ==========================================================================

def _transform_of(shape):
    return (cmds.listRelatives(shape, parent=True, fullPath=True) or [None])[0]


def create_wrap(driver, driven, attr_name=DEFAULT_ENVELOPE_ATTR,
                preserve_offset=False, uniform_rebuild=False):
    """driven 커브가 driver 커브의 모양을 따르도록 라이브 네트워크를 만든다.

    preserve_offset=False (기본)
        envelope 1 에서 driven 이 **driver 의 모양 그대로** 된다.
    preserve_offset=True
        driven 의 원래 모양을 유지한 채 driver 의 **변화량만** 따라간다.
        (타깃 두 개 - 라이브 +env, 바인드 스냅샷 -env)

    uniform_rebuild=True 면 driven 커브를 균등 노트로 먼저 재구성한다.
    노트가 불균등한 커브에서 정확도를 얻는 대신 driven 의 모양이 아주 조금 바뀐다.
    """
    error, warnings, info = check(driver, driven)

    if error:
        return {"ok": False, "message": error, "warnings": warnings}

    driver_shape = info["driver"]["shape"]
    driven_shape = info["driven"]["shape"]
    driver_xform = _transform_of(driver_shape)
    driven_xform = _transform_of(driven_shape)

    base = driven_xform.split("|")[-1].split(":")[-1]

    with undo_chunk():
        if uniform_rebuild and not is_uniform(info["driven"]):
            cmds.rebuildCurve(driven_shape, constructionHistory=False, replaceOriginal=True,
                              rebuildType=0, degree=info["driven"]["degree"],
                              spans=info["driven"]["spans"], keepRange=1,
                              keepEndPoints=True, endKnots=1)
            info["driven"] = curve_info(driven_shape)

        spans = info["driven"]["spans"]
        degree = info["driven"]["degree"]

        # 1) driver 를 driven 의 span/degree 로 재구성 → CV 개수가 driven 과 같아진다.
        rebuilt = cmds.rebuildCurve(
            driver_shape, constructionHistory=True, replaceOriginal=False,
            rebuildType=0, degree=degree, spans=spans, keepRange=1,
            keepEndPoints=True, keepTangents=False, keepControlPoints=False, endKnots=1)

        target_xform = cmds.rename(rebuilt[0], "{0}_wrapTarget".format(base))
        rebuild_node = cmds.rename(rebuilt[1], "{0}_wrapRebuild".format(base))
        target_shape = curve_shape(target_xform)

        # 2) 공간 변환.
        #    rebuildCurve 는 기본으로 driver 의 worldSpace 에 연결되지만, **소스 트랜스폼이
        #    움직여도 다시 계산하지 않는다**(mayapy 실측 - CV 변화만 따라온다).
        #    그래서 지오메트리는 driver 의 `local` 을 먹이고, 공간 변환은 행렬 연결로 따로
        #    처리한다. 행렬은 평범한 어트리뷰트라 트랜스폼 변화가 확실히 전파된다.
        #
        #        driver local ──(driver.worldMatrix × driven.worldInverseMatrix)──▶ driven local
        cmds.connectAttr(driver_shape + ".local", rebuild_node + ".inputCurve", force=True)

        space_node = cmds.createNode("multMatrix", name="{0}_wrapSpace".format(base))
        cmds.connectAttr(driver_xform + ".worldMatrix[0]", space_node + ".matrixIn[0]",
                         force=True)
        cmds.connectAttr(driven_xform + ".worldInverseMatrix[0]", space_node + ".matrixIn[1]",
                         force=True)

        xform_node = cmds.createNode("transformGeometry",
                                     name="{0}_wrapToLocal".format(base))
        cmds.connectAttr(rebuild_node + ".outputCurve", xform_node + ".inputGeometry",
                         force=True)
        cmds.connectAttr(space_node + ".matrixSum", xform_node + ".transform", force=True)
        cmds.connectAttr(xform_node + ".outputGeometry", target_shape + ".create", force=True)

        targets = [target_xform]
        snapshot_xform = None

        # 3) Preserve Offset 이면 바인드 시점 스냅샷을 하나 더 만든다.
        if preserve_offset:
            snapshot_xform = cmds.duplicate(target_xform,
                                            name="{0}_wrapBind".format(base))[0]
            # 스냅샷은 정지해 있어야 한다 - 히스토리를 끊는다.
            snapshot_shape = curve_shape(snapshot_xform)
            for plug in (cmds.listConnections(snapshot_shape + ".create", plugs=True,
                                              source=True, destination=False) or []):
                cmds.disconnectAttr(plug, snapshot_shape + ".create")
            targets.append(snapshot_xform)

        # 4) blendShape
        blend_node = cmds.blendShape(targets + [driven_xform],
                                     name="{0}_wrapBS".format(base))[0]

        cmds.addAttr(blend_node, longName=WRAP_TAG, attributeType="bool",
                     defaultValue=True)

        # 5) envelope 어트리뷰트
        if cmds.objExists("{0}.{1}".format(driven_xform, attr_name)):
            attr_name = "{0}1".format(attr_name)

        cmds.addAttr(driven_xform, longName=attr_name, attributeType="double",
                     minValue=0.0, maxValue=1.0, defaultValue=1.0, keyable=True)

        envelope_plug = "{0}.{1}".format(driven_xform, attr_name)

        cmds.connectAttr(envelope_plug, blend_node + ".weight[0]", force=True)

        if preserve_offset:
            # 바인드 스냅샷은 -envelope 로 빼서 "변화량만" 남긴다.
            negate = cmds.createNode("multDoubleLinear", name="{0}_wrapNegate".format(base))
            cmds.setAttr(negate + ".input2", -1.0)
            cmds.connectAttr(envelope_plug, negate + ".input1", force=True)
            cmds.connectAttr(negate + ".output", blend_node + ".weight[1]", force=True)

        # 6) 중간 커브들은 그룹에 담아 숨긴다.
        group = cmds.group(empty=True, name="{0}_wrapGrp".format(base))
        for node in targets:
            cmds.parent(node, group)
        cmds.setAttr(group + ".visibility", False)

        cmds.addAttr(blend_node, longName="junWrapGroup", attributeType="message")
        cmds.addAttr(group, longName="junWrapOwner", attributeType="message")
        cmds.connectAttr(group + ".junWrapOwner", blend_node + ".junWrapGroup", force=True)

        # setAttr 도 chunk 안에서 해야 한다. 밖에 두면 그것만 별도 undo 항목이 되어
        # Ctrl+Z 한 번이 셋업 전체가 아니라 이 값 하나만 되돌린다.
        cmds.setAttr(envelope_plug, 1.0)

    # 7) 얼마나 잘 맞았는지 재서 알려 준다.
    max_dev, avg_dev = deviation(driven_shape, driver_shape)
    length = max(info["driver"]["length"], 1e-9)

    return {
        "ok": True,
        "message": ("Wrapped '{0}' to '{1}' - {2} CV driven / {3} CV driver, "
                    "max deviation {4:.4f} ({5:.3f}% of driver length), avg {6:.4f}").format(
            base, driver_shape.split("|")[-1],
            info["driven"]["cvs"], info["driver"]["cvs"],
            max_dev, max_dev / length * 100.0, avg_dev),
        "warnings": warnings,
        "blend_node": blend_node,
        "envelope": envelope_plug,
        "max_deviation": max_dev,
        "avg_deviation": avg_dev,
    }
