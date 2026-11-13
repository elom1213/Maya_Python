# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-13
# Framework - MetaHuman `SwingTwistEvaluatorNode` 를 마야 quatNodes 노드망으로 재현 (maya.cmds, UI 없음)
#
# 계획서: JUN_All/docs/plans/A00590_SwingTwistNative_plan.md (§1 사양 · §2 수식 · §3 노드망)
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
# 연결되므로 원본처럼 노드 하나에서 고칠 수 있다. 홀더는 조인트(message) 와 **멤버 노드 목록**(`nodes[]`)을 갖는다 —
# 다음 단계의 Convert/Restore(§9) · Container(§10) 가 이 목록으로 망 전체를 찾는다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


PLUGIN = "quatNodes"
ORIGINAL_TYPE = "SwingTwistEvaluatorNode"

# 홀더를 알아보는 표식 어트리뷰트(값 = 노드망 구조 버전)
MARKER_ATTR = "swingTwistNative"
STRUCTURE_VERSION = 1

HOLDER_SUFFIX = "_SwingTwist"


class SwingTwistError(ValueError):
    """빌드 전에 걸러낸 입력 오류(메시지는 UI 로그에 그대로 붙는다 - 영어)."""


# ======================================================================
# 플러그인
# ======================================================================

def ensure_plugin():
    """quatNodes(마야 동봉) 를 로드한다. 이미 로드돼 있으면 아무것도 안 한다."""
    if not cmds.pluginInfo(PLUGIN, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN, quiet=True)


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


def validate(start_joint, end_joint, swing_joint, twist_joints, twist_blends, from_end):
    """빌드 전에 입력을 검사한다. 문제가 있으면 SwingTwistError, 없으면 경고 문자열 목록."""
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

def _holder_name(name):
    return name if name.endswith(HOLDER_SUFFIX) else name + HOLDER_SUFFIX


def _create_holder(name):
    holder = cmds.createNode("network", name=_holder_name(name))
    cmds.addAttr(holder, longName=MARKER_ATTR, attributeType="long", defaultValue=STRUCTURE_VERSION)
    cmds.setAttr(holder + "." + MARKER_ATTR, lock=True)
    for attr in ("startJoint", "endJoint", "swingJoint"):
        cmds.addAttr(holder, longName=attr, attributeType="message")
    cmds.addAttr(holder, longName="twistJoints", attributeType="message", multi=True, indexMatters=True)
    cmds.addAttr(holder, longName="nodes", attributeType="message", multi=True, indexMatters=False)
    cmds.addAttr(holder, longName="swingBlend", attributeType="double", defaultValue=0.0, keyable=True)
    cmds.addAttr(holder, longName="twistBlend", attributeType="double", multi=True, keyable=True)
    cmds.addAttr(holder, longName="fromEnd", attributeType="bool", defaultValue=False)
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


def build(name, start_joint, end_joint=None, swing_joint=None, swing_blend=0.0,
          twist_joints=(), twist_blends=(), from_end=False, log=None):
    """§3 노드망을 만들고 홀더 이름을 돌려준다.

    인자는 MetaHuman `create_swing_twist_evaluator` 와 같다 — 그 함수 자리에 바로 쓸 수 있다.
    twist_joints 안의 None/"" 는 그 인덱스를 비워 둔다(블렌드 인덱스는 유지). undo 한 번.
    """
    log = log or (lambda _m: None)
    twist_joints = list(twist_joints or [])
    twist_blends = [float(b) for b in (twist_blends or [])]
    end_joint = end_joint or None
    swing_joint = swing_joint or None
    from_end = bool(from_end)

    for w in validate(start_joint, end_joint, swing_joint, twist_joints, twist_blends, from_end):
        log("[WARN] " + w)

    ensure_plugin()
    prefix = name[:-len(HOLDER_SUFFIX)] if name.endswith(HOLDER_SUFFIX) else name

    with undo_chunk():
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

        inv_twist = None
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
            cmds.connectAttr(eu + ".outputRotate", swing_joint + ".rotate")

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
                cmds.connectAttr(eu + ".outputRotate", j + ".rotate")

    log("Built {0} ({1} nodes).".format(holder, len(members(holder))))
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


def read_holder(holder):
    """홀더의 설정을 build() 인자 모양 dict 로 읽는다."""
    twist_idx = cmds.getAttr(holder + ".twistBlend", multiIndices=True) or []
    joint_idx = cmds.getAttr(holder + ".twistJoints", multiIndices=True) or []
    count = max(list(twist_idx) + list(joint_idx) + [-1]) + 1
    twist_joints, twist_blends = [], []
    for i in range(count):
        twist_joints.append(_src("{0}.twistJoints[{1}]".format(holder, i)))
        twist_blends.append(cmds.getAttr("{0}.twistBlend[{1}]".format(holder, i)) if i in twist_idx else 0.0)
    return {
        "name": holder[:-len(HOLDER_SUFFIX)] if holder.endswith(HOLDER_SUFFIX) else holder,
        "start_joint": _src(holder + ".startJoint"),
        "end_joint": _src(holder + ".endJoint"),
        "swing_joint": _src(holder + ".swingJoint"),
        "swing_blend": cmds.getAttr(holder + ".swingBlend"),
        "twist_joints": twist_joints,
        "twist_blends": twist_blends,
        "from_end": bool(cmds.getAttr(holder + ".fromEnd")),
    }


def set_swing_blend(holder, value):
    cmds.setAttr(holder + ".swingBlend", float(value))


def set_twist_blend(holder, index, value):
    cmds.setAttr("{0}.twistBlend[{1}]".format(holder, int(index)), float(value))


def delete_rig(holder):
    """노드망 + 홀더를 지운다. 출력 조인트의 rotate 는 마지막 평가값에 남는다. undo 한 번."""
    with undo_chunk():
        nodes = [n for n in members(holder) if cmds.objExists(n)]
        if nodes:
            cmds.delete(nodes)
        if cmds.objExists(holder):
            cmds.delete(holder)
    return len(nodes)
