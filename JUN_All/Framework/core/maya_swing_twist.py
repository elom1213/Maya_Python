# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-13
# Framework - MetaHuman `SwingTwistEvaluatorNode` 를 마야 quatNodes 노드망으로 재현 (maya.cmds, UI 없음)
#
# 계획서: JUN_All/docs/plans/A00590_SwingTwistNative_plan.md (§1 사양 · §2 수식 · §3 노드망 · §9 Convert · §10 Container)
# 툴:     JUN_All/tools/A00590_SwingTwistNative
#
# 원본(Epic SwingTwistEvaluatorPlugin 1.3.2) 과 수치상 같은 결과를 낸다(골든 시험
# tools/A00590_SwingTwistNative/tests/test_swing_twist_golden.py). 원본 사양을 그대로 따른다:
#   - 트위스트 축은 X 고정, 입력 · 출력 오일러는 **항상 XYZ**(조인트 rotateOrder 무시)
#   - jointOrient 무시 — `.rotate` 만 본다
#   - 블렌드는 출력을 "완전한 역회전(0)" → identity(1) 로 민다 (직관과 반대):
#       twist : 0 = 시작 트위스트 상쇄(fromEnd 면 end 트위스트 복사), 1 = 회전 0
#       swing : 0 = 시작 회전 전체 상쇄, 1 = 시작 트위스트만 상쇄 (0 이 아니다!)
#
# 계산식 (RigLogic TwistSwingJointsEvaluator):
#   q          = euler(start.rotate, XYZ)
#   twist(q)   = normalize(q.x, 0, 0, q.w)
#   invTwist   = inverse(twist(q))
#   swingOut   = invTwist * slerp(inverse(q * invTwist), I, swingBlend)
#   twistOut_i = slerp(base, I, twistBlend_i),  base = invTwist | twist(euler(end.rotate)) (fromEnd)
#
# 망 하나마다 홀더(network 노드 `<name>_SwingTwist`)를 둔다. 블렌드는 홀더 어트리뷰트에서 quatSlerp.inputT 로
# 연결되므로 원본처럼 노드 하나에서 고칠 수 있다. 홀더가 기억하는 것(message):
#   startJoint / endJoint / swingJoint / twistJoints[i]  — 조인트
#   nodes[]                                              — 망의 모든 멤버
#   swingOutput / twistOutputs[i]                        — 출력 quatToEuler (Convert 가 나중에 연결할 때 · Container 공개)
#   sourceType / sourceName (string)                     — Convert 로 만든 망이면 원본 정보(Restore 근거)
#
# Convert (§9): 원본 노드 → 설정 읽기 → 망을 **출력 미연결**로 만든다 → 원본 출력과 수치 대조(무작위 포즈) →
#   원본 삭제(출력 unitConversion 도 함께 사라진다 - 연결만 끊으면 남는다) → 망 출력 연결 → 블렌드 입력 연결 옮기기.
# Restore: 홀더 → 원본 노드를 MetaHuman 방식 그대로 다시 만든다(DNA export 는 원본 노드만 찾는다).
# Container (§10): 망 하나 = container 하나 `<holder>_CTN`. 블렌드 · 입출력을 원본 이름으로 공개, blackBox.
#   container 를 지우면 멤버(홀더 포함)도 함께 지워진다(실측).

import glob
import os
import random

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


PLUGIN = "quatNodes"
ORIGINAL_TYPE = "SwingTwistEvaluatorNode"
ORIGINAL_PLUGIN = "SwingTwistEvaluatorPlugin"
ORIGINAL_SUFFIX = "_SwingTwistEvalNode"

# 홀더를 알아보는 표식 어트리뷰트(값 = 노드망 구조 버전)
MARKER_ATTR = "swingTwistNative"
STRUCTURE_VERSION = 1

HOLDER_SUFFIX = "_SwingTwist"
CONTAINER_SUFFIX = "_CTN"

# Convert 수치 대조 기준(도). 골든 시험 실측 최대 2e-13° — 넉넉히.
VERIFY_TOLERANCE = 1e-6


class SwingTwistError(ValueError):
    """빌드 · 변환 전에 걸러낸 입력 오류(메시지는 UI 로그에 그대로 붙는다 - 영어)."""


def _quiet(_msg):
    pass


# ======================================================================
# 플러그인
# ======================================================================

def ensure_plugin():
    """quatNodes(마야 동봉) 를 로드한다. 이미 로드돼 있으면 아무것도 안 한다."""
    if not cmds.pluginInfo(PLUGIN, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN, quiet=True)


def original_type_known():
    """원본 노드 타입이 지금 마야에 등록돼 있나(플러그인 로드 여부)."""
    return ORIGINAL_TYPE in (cmds.allNodeTypes() or [])


def _original_plugin_candidates():
    ver = cmds.about(version=True)[:4]
    pattern = os.path.expanduser(
        "~/Documents/maya/modules/MetaHumanForMaya/lib/SwingTwistEvaluatorPlugin/*/platform-windows/"
        "maya-{0}/lib/SwingTwistEvaluatorPlugin.mll".format(ver))
    return sorted(glob.glob(pattern), reverse=True)


def load_original_plugin():
    """원본 플러그인을 로드한다. 모듈 경로로 이름 로드 → 안 되면 MetaHumanForMaya 기본 설치 위치. 성공하면 True."""
    if original_type_known():
        return True
    try:
        cmds.loadPlugin(ORIGINAL_PLUGIN, quiet=True)
    except RuntimeError:
        for path in _original_plugin_candidates():
            try:
                cmds.loadPlugin(path, quiet=True)
                break
            except RuntimeError:
                continue
    return original_type_known()


def unload_original_plugin(flush_undo=False):
    """씬에 원본 노드가 하나도 없을 때만 플러그인을 내린다. 내렸으면 True.

    변환으로 지운 원본 노드는 **undo 큐에 남아 있어** 마야가 "still in use" 로 거부한다(실측).
    flush_undo=True 면 undo 큐를 비우고 내린다 - 호출부(UI)가 사용자에게 먼저 알린다.
    """
    if not original_type_known() or list_original_nodes():
        return False
    if flush_undo:
        cmds.flushUndo()
    for name in (cmds.pluginInfo(query=True, listPlugins=True) or []):
        if name.startswith(ORIGINAL_PLUGIN):
            try:
                cmds.unloadPlugin(name)
            except RuntimeError:
                return False
    return not original_type_known()


# ======================================================================
# 검사
# ======================================================================

def _incoming(plug):
    """plug 와 그 자식 plug 에 들어오는 연결 소스(중복 없이)."""
    node, attr = plug.split(".", 1)
    plugs = [plug]
    children = cmds.attributeQuery(attr, node=node, listChildren=True) or []
    plugs += ["{0}.{1}".format(node, c) for c in children]
    found = []
    for p in plugs:
        for src in cmds.listConnections(p, source=True, destination=False, plugs=True,
                                        skipConversionNodes=True) or []:
            if src not in found:
                found.append(src)
    return found


def _locked_rotate(node):
    return [a for a in ("rotate", "rotateX", "rotateY", "rotateZ")
            if cmds.getAttr("{0}.{1}".format(node, a), lock=True)]


def validate(start_joint, end_joint, swing_joint, twist_joints, twist_blends, from_end, check_outputs=True):
    """빌드 전에 입력을 검사한다. 문제가 있으면 SwingTwistError, 없으면 경고 문자열 목록.

    check_outputs=False 는 Convert 용 — 출력 조인트가 아직 원본에 구동되고 있어도 통과시킨다.
    """
    warnings = []
    twist_joints = list(twist_joints or [])
    twist_blends = list(twist_blends or [])

    if not start_joint:
        raise SwingTwistError("Start joint is required.")
    if not swing_joint and not any(twist_joints):
        raise SwingTwistError("Nothing to drive - set a swing joint or at least one twist joint.")
    if len(twist_blends) != len(twist_joints):
        raise SwingTwistError("Twist blend count ({0}) does not match twist joint count ({1}).".format(
            len(twist_blends), len(twist_joints)))

    inputs = [("Start", start_joint)]
    if end_joint:
        inputs.append(("End", end_joint))
    outputs = []
    if swing_joint:
        outputs.append(("Swing", swing_joint))
    outputs += [("Twist {0}".format(i), j) for i, j in enumerate(twist_joints) if j]

    for label, node in inputs + outputs:
        if not cmds.objExists(node):
            raise SwingTwistError("{0} '{1}' does not exist.".format(label, node))
        if not cmds.attributeQuery("rotate", node=node, exists=True):
            raise SwingTwistError("{0} '{1}' has no rotate attribute.".format(label, node))

    out_nodes = [cmds.ls(n, long=True)[0] for _, n in outputs]
    if len(set(out_nodes)) != len(out_nodes):
        raise SwingTwistError("The same joint is used for more than one output.")
    in_nodes = {cmds.ls(n, long=True)[0] for _, n in inputs}
    for label, node in outputs:
        if cmds.ls(node, long=True)[0] in in_nodes:
            raise SwingTwistError("{0} '{1}' is also an input joint - that would make a cycle.".format(label, node))

    for label, node in outputs:
        if check_outputs:
            src = _incoming(node + ".rotate")
            if src:
                raise SwingTwistError("{0} '{1}' rotate is already driven by {2} - disconnect it first.".format(
                    label, node, ", ".join(src)))
        locked = _locked_rotate(node)
        if locked:
            raise SwingTwistError("{0} '{1}' has locked channels: {2}.".format(label, node, ", ".join(locked)))

    if from_end and not end_joint:
        warnings.append("From End is on without an end joint - twist outputs stay at zero (same as the original node).")
    if end_joint and not from_end:
        warnings.append("End joint is ignored because From End is off (same as the original node).")
    # 원본은 rotateOrder 를 보지 않고 XYZ 로 해석한다 - 그대로 재현하되 알린다.
    for label, node in inputs + outputs:
        if cmds.attributeQuery("rotateOrder", node=node, exists=True) and cmds.getAttr(node + ".rotateOrder") != 0:
            warnings.append("{0} '{1}' rotate order is not XYZ - the network reads/writes XYZ like the original node.".format(
                label, node))
    return warnings


# ======================================================================
# 빌드
# ======================================================================

def _prefix_of(name):
    for suffix in (HOLDER_SUFFIX, ORIGINAL_SUFFIX):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[:-len(suffix)]
    return name


def _create_holder(prefix):
    holder = cmds.createNode("network", name=prefix + HOLDER_SUFFIX)
    cmds.addAttr(holder, longName=MARKER_ATTR, attributeType="long", defaultValue=STRUCTURE_VERSION)
    cmds.setAttr(holder + "." + MARKER_ATTR, lock=True)
    for attr in ("startJoint", "endJoint", "swingJoint", "swingOutput"):
        cmds.addAttr(holder, longName=attr, attributeType="message")
    cmds.addAttr(holder, longName="twistJoints", attributeType="message", multi=True, indexMatters=True)
    cmds.addAttr(holder, longName="twistOutputs", attributeType="message", multi=True, indexMatters=True)
    cmds.addAttr(holder, longName="nodes", attributeType="message", multi=True, indexMatters=False)
    cmds.addAttr(holder, longName="swingBlend", attributeType="double", defaultValue=0.0, keyable=True)
    cmds.addAttr(holder, longName="twistBlend", attributeType="double", multi=True, keyable=True)
    cmds.addAttr(holder, longName="fromEnd", attributeType="bool", defaultValue=False)
    cmds.addAttr(holder, longName="sourceType", dataType="string")
    cmds.addAttr(holder, longName="sourceName", dataType="string")
    return holder


def _node(holder, node_type, name):
    node = cmds.createNode(node_type, name=name)
    cmds.connectAttr(node + ".message", holder + ".nodes", nextAvailable=True)
    return node


def _set_identity(plug):
    """quat 입력을 identity(0,0,0,1) 로. quatSlerp.input2Quat 기본값은 (0,0,0,0) 이다."""
    node, attr = plug.split(".", 1)
    for axis, value in (("X", 0.0), ("Y", 0.0), ("Z", 0.0), ("W", 1.0)):
        cmds.setAttr("{0}.{1}{2}".format(node, attr, axis), value)


def _twist_of(holder, prefix, euler_node, tag):
    """euler_node.outputQuat 의 X 축 트위스트 = normalize(x, 0, 0, w)."""
    tw = _node(holder, "quatNormalize", "{0}_{1}_twist".format(prefix, tag))
    cmds.connectAttr(euler_node + ".outputQuatX", tw + ".inputQuatX")
    cmds.connectAttr(euler_node + ".outputQuatW", tw + ".inputQuatW")
    return tw


def _build_network(prefix, start_joint, end_joint, swing_joint, swing_blend, twist_joints, twist_blends, from_end):
    """홀더 + 망을 만든다. 출력 조인트에는 **연결하지 않는다**(connect_outputs 가 한다)."""
    holder = _create_holder(prefix)
    cmds.setAttr(holder + ".swingBlend", float(swing_blend))
    cmds.setAttr(holder + ".fromEnd", from_end)
    for i, b in enumerate(twist_blends):
        cmds.setAttr("{0}.twistBlend[{1}]".format(holder, i), b)

    cmds.connectAttr(start_joint + ".message", holder + ".startJoint")
    if end_joint:
        cmds.connectAttr(end_joint + ".message", holder + ".endJoint")
    if swing_joint:
        cmds.connectAttr(swing_joint + ".message", holder + ".swingJoint")
    for i, j in enumerate(twist_joints):
        if j:
            cmds.connectAttr(j + ".message", "{0}.twistJoints[{1}]".format(holder, i))

    has_twist = any(twist_joints)
    need_start = bool(swing_joint) or (has_twist and not from_end)

    eq = inv_twist = None
    if need_start:
        eq = _node(holder, "eulerToQuat", prefix + "_ST_startQuat")
        cmds.connectAttr(start_joint + ".rotate", eq + ".inputRotate")
        tw = _twist_of(holder, prefix, eq, "ST_start")
        inv_twist = _node(holder, "quatInvert", prefix + "_ST_invTwist")
        cmds.connectAttr(tw + ".outputQuat", inv_twist + ".inputQuat")

    if swing_joint:
        sw = _node(holder, "quatProd", prefix + "_ST_swing")
        cmds.connectAttr(eq + ".outputQuat", sw + ".input1Quat")
        cmds.connectAttr(inv_twist + ".outputQuat", sw + ".input2Quat")
        inv_sw = _node(holder, "quatInvert", prefix + "_ST_invSwing")
        cmds.connectAttr(sw + ".outputQuat", inv_sw + ".inputQuat")
        sl = _node(holder, "quatSlerp", prefix + "_ST_swingSlerp")
        cmds.connectAttr(inv_sw + ".outputQuat", sl + ".input1Quat")
        _set_identity(sl + ".input2Quat")
        cmds.connectAttr(holder + ".swingBlend", sl + ".inputT")
        out = _node(holder, "quatProd", prefix + "_ST_swingOut")
        cmds.connectAttr(inv_twist + ".outputQuat", out + ".input1Quat")
        cmds.connectAttr(sl + ".outputQuat", out + ".input2Quat")
        eu = _node(holder, "quatToEuler", prefix + "_ST_swingEuler")
        cmds.connectAttr(out + ".outputQuat", eu + ".inputQuat")
        cmds.connectAttr(eu + ".message", holder + ".swingOutput")

    if has_twist:
        base = None                       # None = identity (fromEnd 인데 end 조인트가 없을 때)
        if not from_end:
            base = inv_twist + ".outputQuat"
        elif end_joint:
            eqe = _node(holder, "eulerToQuat", prefix + "_ST_endQuat")
            cmds.connectAttr(end_joint + ".rotate", eqe + ".inputRotate")
            # 원본 그대로 - fromEnd 의 base 는 end 트위스트 **자체**(역회전 아님)
            base = _twist_of(holder, prefix, eqe, "ST_end") + ".outputQuat"
        for i, j in enumerate(twist_joints):
            if not j:
                continue
            sl = _node(holder, "quatSlerp", "{0}_ST_twistSlerp{1}".format(prefix, i))
            if base:
                cmds.connectAttr(base, sl + ".input1Quat")
            else:
                _set_identity(sl + ".input1Quat")
            _set_identity(sl + ".input2Quat")
            cmds.connectAttr("{0}.twistBlend[{1}]".format(holder, i), sl + ".inputT")
            eu = _node(holder, "quatToEuler", "{0}_ST_twistEuler{1}".format(prefix, i))
            cmds.connectAttr(sl + ".outputQuat", eu + ".inputQuat")
            cmds.connectAttr(eu + ".message", "{0}.twistOutputs[{1}]".format(holder, i))
    return holder


def outputs(holder):
    """[(출력 quatToEuler, 출력 조인트)] - swing 먼저, 그다음 twist 인덱스 순."""
    pairs = []
    eu, joint = _src(holder + ".swingOutput"), _src(holder + ".swingJoint")
    if eu and joint:
        pairs.append((eu, joint))
    for i in cmds.getAttr(holder + ".twistOutputs", multiIndices=True) or []:
        eu = _src("{0}.twistOutputs[{1}]".format(holder, i))
        joint = _src("{0}.twistJoints[{1}]".format(holder, i))
        if eu and joint:
            pairs.append((eu, joint))
    return pairs


def connect_outputs(holder):
    """망 출력 quatToEuler.outputRotate → 출력 조인트 .rotate."""
    for eu, joint in outputs(holder):
        cmds.connectAttr(eu + ".outputRotate", joint + ".rotate", force=True)


def build(name, start_joint, end_joint=None, swing_joint=None, swing_blend=0.0,
          twist_joints=(), twist_blends=(), from_end=False, log=None, wrap=False):
    """§3 노드망을 만들고 홀더 이름을 돌려준다.

    인자는 MetaHuman `create_swing_twist_evaluator` 와 같다 — 그 함수 자리에 바로 쓸 수 있다.
    twist_joints 안의 None/"" 는 그 인덱스를 비워 둔다(블렌드 인덱스는 유지). wrap=True 면 container 로 묶는다.
    undo 한 번.
    """
    log = log or _quiet
    twist_joints = list(twist_joints or [])
    twist_blends = [float(b) for b in (twist_blends or [])]
    end_joint = end_joint or None
    swing_joint = swing_joint or None
    from_end = bool(from_end)

    for w in validate(start_joint, end_joint, swing_joint, twist_joints, twist_blends, from_end):
        log("[WARN] " + w)

    ensure_plugin()
    with undo_chunk():
        holder = _build_network(_prefix_of(name), start_joint, end_joint, swing_joint, swing_blend,
                                twist_joints, twist_blends, from_end)
        connect_outputs(holder)
        if wrap:
            wrap_container(holder)

    log("Built {0} ({1} nodes){2}.".format(holder, len(members(holder)), " in a container" if wrap else ""))
    return holder


# ======================================================================
# 홀더 조회 · 편집
# ======================================================================

def is_holder(node):
    return bool(node) and cmds.objExists(node) and cmds.attributeQuery(MARKER_ATTR, node=node, exists=True)


def list_holders():
    """씬의 홀더(network 노드) 목록 - 이름순."""
    return sorted(n for n in (cmds.ls(type="network") or []) if is_holder(n))


def members(holder):
    """홀더가 기억하는 노드망 멤버(홀더 자신 제외)."""
    return cmds.listConnections(holder + ".nodes", source=True, destination=False) or []


def _src(plug):
    found = cmds.listConnections(plug, source=True, destination=False) or []
    return found[0] if found else None


def _src_plug(plug):
    found = cmds.listConnections(plug, source=True, destination=False, plugs=True, skipConversionNodes=True) or []
    return found[0] if found else None


def _has_attr(node, attr):
    return cmds.attributeQuery(attr, node=node, exists=True)


def read_holder(holder):
    """홀더의 설정을 build() 인자 모양 dict 로 읽는다(+ 원본 정보)."""
    twist_idx = cmds.getAttr(holder + ".twistBlend", multiIndices=True) or []
    joint_idx = cmds.getAttr(holder + ".twistJoints", multiIndices=True) or []
    count = max(list(twist_idx) + list(joint_idx) + [-1]) + 1
    twist_joints, twist_blends = [], []
    for i in range(count):
        twist_joints.append(_src("{0}.twistJoints[{1}]".format(holder, i)))
        twist_blends.append(cmds.getAttr("{0}.twistBlend[{1}]".format(holder, i)) if i in twist_idx else 0.0)
    source_type = cmds.getAttr(holder + ".sourceType") if _has_attr(holder, "sourceType") else None
    source_name = cmds.getAttr(holder + ".sourceName") if _has_attr(holder, "sourceName") else None
    return {
        "name": _prefix_of(holder),
        "start_joint": _src(holder + ".startJoint"),
        "end_joint": _src(holder + ".endJoint"),
        "swing_joint": _src(holder + ".swingJoint"),
        "swing_blend": cmds.getAttr(holder + ".swingBlend"),
        "twist_joints": twist_joints,
        "twist_blends": twist_blends,
        "from_end": bool(cmds.getAttr(holder + ".fromEnd")),
        "source_type": source_type or None,
        "source_name": source_name or None,
    }


def set_swing_blend(holder, value):
    cmds.setAttr(holder + ".swingBlend", float(value))


def set_twist_blend(holder, index, value):
    cmds.setAttr("{0}.twistBlend[{1}]".format(holder, int(index)), float(value))


def delete_rig(holder):
    """노드망 + 홀더(+ container)를 지운다. 출력 조인트의 rotate 는 마지막 평가값에 남는다. undo 한 번.

    돌려주는 값 = 지운 멤버 수(홀더 · container 제외).
    """
    with undo_chunk():
        nodes = [n for n in members(holder) if cmds.objExists(n)]
        container = container_of(holder)
        if container:
            cmds.delete(container)            # 멤버 · 홀더까지 함께 지워진다(실측)
        else:
            if nodes:
                cmds.delete(nodes)
            if cmds.objExists(holder):
                cmds.delete(holder)
    return len(nodes)


# ======================================================================
# Convert (§9) — 원본 SwingTwistEvaluatorNode → 노드망
# ======================================================================

def list_original_nodes():
    """씬의 원본 SwingTwistEvaluatorNode (플러그인이 안 로드돼 있으면 빈 목록)."""
    if not original_type_known():
        return []
    return sorted(cmds.ls(type=ORIGINAL_TYPE) or [])


def _dest_rotate_node(plug, label):
    """출력 plug 의 목적지 조인트(unitConversion 건너뜀). 없으면 None, 여러 곳이거나 rotate 가 아니면 오류."""
    dests = cmds.listConnections(plug, source=False, destination=True, plugs=True, skipConversionNodes=True) or []
    if not dests:
        return None
    if len(dests) > 1:
        raise SwingTwistError("{0} drives more than one plug ({1}) - convert it by hand.".format(label, ", ".join(dests)))
    node, attr = dests[0].split(".", 1)
    if attr not in ("rotate", "r"):
        raise SwingTwistError("{0} drives {1}, not a rotate - convert it by hand.".format(label, dests[0]))
    return node


def _source_rotate_node(plug, label):
    src = _src_plug(plug)
    if not src:
        return None
    node, attr = src.split(".", 1)
    if attr not in ("rotate", "r"):
        raise SwingTwistError("{0} comes from {1}, not a rotate - convert it by hand.".format(label, src))
    return node


def read_original(node):
    """원본 노드 설정을 build() 인자 모양 dict 로 + 블렌드 입력 연결 소스(plug).

    twist 는 twists[] 와 twistBlend[] 의 논리 인덱스를 그대로 둔다(빈 인덱스는 None).
    """
    if not cmds.objExists(node) or cmds.nodeType(node) != ORIGINAL_TYPE:
        raise SwingTwistError("'{0}' is not a {1}.".format(node, ORIGINAL_TYPE))
    start = _source_rotate_node(node + ".startJoint", "startJoint")
    if not start:
        raise SwingTwistError("'{0}' has no start joint connected.".format(node))
    end = _source_rotate_node(node + ".endJoint", "endJoint")
    swing = _dest_rotate_node(node + ".swing", "swing")

    tw_idx = cmds.getAttr(node + ".twists", multiIndices=True) or []
    tb_idx = cmds.getAttr(node + ".twistBlend", multiIndices=True) or []
    count = max(list(tw_idx) + list(tb_idx) + [-1]) + 1
    twist_joints, twist_blends, twist_blend_srcs = [], [], {}
    for i in range(count):
        joint = _dest_rotate_node("{0}.twists[{1}]".format(node, i), "twists[{0}]".format(i)) if i in tw_idx else None
        twist_joints.append(joint)
        plug = "{0}.twistBlend[{1}].values".format(node, i)
        twist_blends.append(cmds.getAttr(plug) if i in tb_idx else 0.0)
        src = _src_plug(plug) or _src_plug("{0}.twistBlend[{1}]".format(node, i))
        if src:
            twist_blend_srcs[i] = src
    # 끝의 빈 인덱스(출력 없는 블렌드만 있는 자리)는 잘라낸다
    while twist_joints and not twist_joints[-1]:
        twist_joints.pop()
        twist_blends.pop()

    return {
        "name": _prefix_of(node),
        "start_joint": start,
        "end_joint": end,
        "swing_joint": swing,
        "swing_blend": cmds.getAttr(node + ".swingBlend"),
        "twist_joints": twist_joints,
        "twist_blends": twist_blends,
        "from_end": bool(cmds.getAttr(node + ".fromEnd")),
        "swing_blend_src": _src_plug(node + ".swingBlend"),
        "twist_blend_srcs": twist_blend_srcs,
        "from_end_src": _src_plug(node + ".fromEnd"),
    }


def _move_input(from_plug, to_plug):
    """from_plug 로 들어오는 연결을 끊고 같은 소스를 to_plug 에 꽂는다. 옮겼으면 True.

    삭제할 노드의 입력(키 animCurve 등)은 **지우기 전에** 옮겨야 한다 - 그 노드에만 연결된 animCurve 는
    노드와 함께 지워진다(실측).
    """
    src = cmds.listConnections(from_plug, source=True, destination=False, plugs=True) or []
    if not src:
        return False
    cmds.disconnectAttr(src[0], from_plug)
    cmds.connectAttr(src[0], to_plug, force=True)
    return True


def _settable_rotate(node):
    return node and not _locked_rotate(node) and not _incoming(node + ".rotate")


def _compare_outputs(original, holder, spec, samples, seed=590):
    """원본 출력 plug 와 망 출력 quatToEuler 를 지금 포즈 + 무작위 포즈에서 비교한다. 최대 오차(도)와 포즈 수.

    무작위 포즈는 입력 조인트 rotate 를 잠깐 바꿨다가 되돌린다(잠겼거나 구동 중이면 지금 포즈만).
    """
    pairs = []
    if spec["swing_joint"]:
        pairs.append((original + ".swing", _src(holder + ".swingOutput")))
    for i, j in enumerate(spec["twist_joints"]):
        if j:
            pairs.append(("{0}.twists[{1}]".format(original, i), _src("{0}.twistOutputs[{1}]".format(holder, i))))

    def err_now():
        worst = 0.0
        for o_plug, eu in pairs:
            a = cmds.getAttr(o_plug)[0]
            b = cmds.getAttr(eu + ".outputRotate")[0]
            worst = max(worst, max(abs(x - y) for x, y in zip(a, b)))
        return worst

    worst, poses = err_now(), 1
    drivers = [j for j in (spec["start_joint"], spec["end_joint"]) if j]
    if samples and all(_settable_rotate(j) for j in drivers):
        saved = {j: cmds.getAttr(j + ".rotate")[0] for j in drivers}
        rng = random.Random(seed)
        try:
            for k in range(samples):
                span = 180.0 if k % 2 else 60.0
                for j in drivers:
                    cmds.setAttr(j + ".rotate", *[rng.uniform(-span, span) for _ in range(3)])
                worst = max(worst, err_now())
                poses += 1
        finally:
            for j, v in saved.items():
                cmds.setAttr(j + ".rotate", *v)
    return worst, poses


def convert(node, verify_samples=20, wrap=False, log=None):
    """원본 노드 하나를 노드망으로 바꾸고 홀더를 돌려준다. undo 한 번.

    대조 오차가 VERIFY_TOLERANCE 를 넘으면 만든 망을 지우고 SwingTwistError(원본은 그대로).
    """
    log = log or _quiet
    if cmds.referenceQuery(node, isNodeReferenced=True):
        raise SwingTwistError("'{0}' is from a reference - convert it in the referenced file.".format(node))
    spec = read_original(node)
    for w in validate(spec["start_joint"], spec["end_joint"], spec["swing_joint"], spec["twist_joints"],
                      spec["twist_blends"], spec["from_end"], check_outputs=False):
        log("[WARN] " + w)
    if spec["from_end_src"]:
        log("[WARN] {0}.fromEnd is connected ({1}) - the network keeps the current value ({2}).".format(
            node, spec["from_end_src"], spec["from_end"]))

    ensure_plugin()
    with undo_chunk():
        holder = _build_network(spec["name"], spec["start_joint"], spec["end_joint"], spec["swing_joint"],
                                spec["swing_blend"], spec["twist_joints"], spec["twist_blends"], spec["from_end"])
        err, poses = _compare_outputs(node, holder, spec, verify_samples)
        if err > VERIFY_TOLERANCE:
            delete_rig(holder)
            raise SwingTwistError("{0}: network differs from the original by {1:.3g} deg - left unchanged.".format(
                node, err))

        cmds.setAttr(holder + ".sourceType", ORIGINAL_TYPE, type="string")
        cmds.setAttr(holder + ".sourceName", node, type="string")
        # 블렌드 입력을 **원본을 지우기 전에** 홀더로 옮긴다 - 원본에만 연결된 animCurve(키)는
        # 원본과 함께 지워진다(실측). connectAttr force 가 원본 쪽 연결을 끊는다.
        _move_input(node + ".swingBlend", holder + ".swingBlend")
        for i in spec["twist_blend_srcs"]:
            dst = "{0}.twistBlend[{1}]".format(holder, i)
            _move_input("{0}.twistBlend[{1}].values".format(node, i), dst)
            _move_input("{0}.twistBlend[{1}]".format(node, i), dst)
        # 원본을 지우면 출력 unitConversion 도 함께 사라진다(연결만 끊으면 남는다 - 실측)
        cmds.delete(node)
        connect_outputs(holder)
        if wrap:
            wrap_container(holder)

    log("Converted {0} -> {1} ({2} nodes, max diff {3:.3g} deg over {4} pose(s)){5}.".format(
        node, holder, len(members(holder)), err, poses, " in a container" if wrap else ""))
    return holder


def restore(holder, log=None):
    """홀더 → 원본 SwingTwistEvaluatorNode 를 MetaHuman 방식 그대로 다시 만들고 망을 지운다. undo 한 번.

    원본 플러그인이 필요하다(load_original_plugin). 블렌드 입력 연결도 원본으로 옮긴다. 원본 노드 이름을 돌려준다.
    """
    log = log or _quiet
    if not load_original_plugin():
        raise SwingTwistError("{0} plugin is not available - cannot restore.".format(ORIGINAL_PLUGIN))
    spec = read_holder(holder)
    name = spec["source_name"] or (spec["name"] + ORIGINAL_SUFFIX)
    if cmds.objExists(name):
        name = spec["name"] + ORIGINAL_SUFFIX + "#"

    with undo_chunk():
        # MetaHuman mh_pose_editor/model/swing_twist.py 의 create_swing_twist_evaluator 와 같은 설정.
        # 출력 연결은 망을 지운 뒤에(조인트 rotate 가 아직 망에 구동되고 있다).
        node = cmds.createNode(ORIGINAL_TYPE, name=name)
        if spec["from_end"]:
            cmds.setAttr(node + ".fromEnd", True)
        if spec["swing_joint"]:
            cmds.setAttr(node + ".swingBlend", spec["swing_blend"])
        cmds.connectAttr(spec["start_joint"] + ".rotate", node + ".startJoint")
        if spec["end_joint"]:
            cmds.connectAttr(spec["end_joint"] + ".rotate", node + ".endJoint")
        for i, (joint, blend) in enumerate(zip(spec["twist_joints"], spec["twist_blends"])):
            cmds.setAttr("{0}.twistBlend[{1}].values".format(node, i), blend)
            if joint:
                cmds.setAttr("{0}.twists[{1}]".format(node, i), 0, 0, 0)
        # 블렌드 입력(키 등)은 홀더를 지우기 전에 옮긴다
        _move_input(holder + ".swingBlend", node + ".swingBlend")
        for i in cmds.getAttr(holder + ".twistBlend", multiIndices=True) or []:
            _move_input("{0}.twistBlend[{1}]".format(holder, i), "{0}.twistBlend[{1}].values".format(node, i))
        delete_rig(holder)
        if spec["swing_joint"]:
            cmds.connectAttr(node + ".swing", spec["swing_joint"] + ".rotate")
        for i, joint in enumerate(spec["twist_joints"]):
            if joint:
                cmds.connectAttr("{0}.twists[{1}]".format(node, i), joint + ".rotate")
        # 원본 노드는 attributeAffects 가 비어 있어, MetaHuman 처럼 twists[i] 를 0 으로 setAttr 하면 입력이 바뀔 때까지
        # 출력이 "깨끗한 0" 으로 남는다(실측 - MetaHuman 원래 함수도 같다). 바로 다시 계산되게 더럽힌다.
        cmds.dgdirty(node)

    log("Restored {0} from {1}.".format(node, holder))
    return node


# ======================================================================
# Container (§10) — 망 하나를 한 노드처럼
# ======================================================================

def container_of(holder):
    """홀더가 든 container (없으면 None)."""
    if not cmds.objExists(holder):
        return None
    found = cmds.container(query=True, findContainer=[holder])
    return found if found else None


def _input_quat(holder, joint):
    """joint.rotate 를 받는 멤버 eulerToQuat."""
    if not joint:
        return None
    for n in members(holder):
        if cmds.nodeType(n) == "eulerToQuat" and _src(n + ".inputRotate") == joint:
            return n
    return None


def wrap_container(holder, black_box=True):
    """망 + 홀더를 container 하나로 묶는다. 이미 묶였으면 그 container. undo 한 번.

    공개(원본 노드와 같은 이름): swingBlend · twistBlend<i> (홀더 바인드 — container 에서 바로 고친다),
    startJoint · endJoint (입력), swing · twists<i> (출력).
    """
    existing = container_of(holder)
    if existing:
        return existing
    spec = read_holder(holder)
    with undo_chunk():
        container = cmds.container(name=holder + CONTAINER_SUFFIX, addNode=members(holder) + [holder],
                                   includeNetwork=False, includeHierarchyBelow=False,
                                   includeShapes=False, includeTransform=False)
        publish = [(holder + ".swingBlend", "swingBlend")]
        for i in cmds.getAttr(holder + ".twistBlend", multiIndices=True) or []:
            publish.append(("{0}.twistBlend[{1}]".format(holder, i), "twistBlend{0}".format(i)))
        start_q = _input_quat(holder, spec["start_joint"])
        if start_q:
            publish.append((start_q + ".inputRotate", "startJoint"))
        end_q = _input_quat(holder, spec["end_joint"])
        if end_q:
            publish.append((end_q + ".inputRotate", "endJoint"))
        sw = _src(holder + ".swingOutput")
        if sw:
            publish.append((sw + ".outputRotate", "swing"))
        for i in cmds.getAttr(holder + ".twistOutputs", multiIndices=True) or []:
            eu = _src("{0}.twistOutputs[{1}]".format(holder, i))
            if eu:
                publish.append((eu + ".outputRotate", "twists{0}".format(i)))
        for plug, name in publish:
            cmds.container(container, edit=True, publishAndBind=[plug, name])
        cmds.setAttr(container + ".blackBox", bool(black_box))
    return container


def unwrap_container(holder):
    """container 를 풀어 망을 그대로 두고 container 만 지운다. 풀었으면 True. undo 한 번."""
    container = container_of(holder)
    if not container:
        return False
    with undo_chunk():
        nodes = cmds.container(container, query=True, nodeList=True) or []
        if nodes:
            cmds.container(container, edit=True, removeNode=nodes)
        cmds.delete(container)
    return True


def set_black_box(holder, on):
    """container 의 blackBox(안 숨기기)를 켜고 끈다. container 가 없으면 False."""
    container = container_of(holder)
    if not container:
        return False
    cmds.setAttr(container + ".blackBox", bool(on))
    return True
