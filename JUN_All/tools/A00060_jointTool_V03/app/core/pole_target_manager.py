# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-31
# A00060_jointTool_V03 - Pole Target : 폴 벡터 타깃을 만들고 늘 제자리에 붙여 둔다.
#
# 계획서: JUN_All/docs/plans/A00060_poleTarget_plan.md
#
# ── 무엇을 만드나 ───────────────────────────────────────────────────────────
#
# 세 오브젝트 `[p1, p2, p3]` 에 대해
#
#     A  = (p1 + p3) / 2          <- 양 끝을 잇는 선분의 중점
#     v  = p2 - A                 <- 중점에서 가운데 관절로 가는 벡터
#     A' = A + n * v              <- 여기에 오브젝트를 둔다
#
# ── 수식을 전개하면 pointConstraint 하나다 ★ ────────────────────────────────
#
#     A' = A + n(p2 - A) = (1-n)A + n*p2
#        = ((1-n)/2)*p1 + n*p2 + ((1-n)/2)*p3
#
# **세 점의 가중 평균이고 가중치 합이 언제나 1이다.** 그래서 벡터 노드망을 짤 필요가
# 없다 - `pointConstraint` 가 그대로 이 식이다.
#
# 직접 짜 보면 왜 안 되는지도 분명하다: `jnt_02.translate` 는 **로컬**이라 체인에서
# 깨진다(실측). 월드로 하려면 `decomposeMatrix` 셋 + 결과를 부모 공간으로 되돌릴
# `multMatrix` 까지 노드가 8개쯤 든다. **컨스트레인트는 그걸 공짜로 해 준다.**
#
# ── 가중치는 setAttr 이 아니라 '연결' 로 넣는다 ★★ ──────────────────────────
#
# `n > 1` 이면 양 끝 가중치가 음수다. 그런데 가중치 어트리뷰트는 `min = 0` 이라
#
#     setAttr(w0, -0.25)  ->  RuntimeError: Cannot set ... below its minimum
#     연결로 -0.25        ->  통과. 결과가 수식과 정확히 일치            (실측)
#
# **모르면 `n>1` 에서 통째로 막힌다.** 어차피 연결해야 하므로 `n` 을 **살아 있는
# 어트리뷰트**로 두는 것은 공짜다.

import math

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


#: 폴 거리 어트리뷰트 이름
DISTANCE_ATTR = "poleDistance"

#: 만들 수 있는 오브젝트 종류
KIND_LOCATOR = "locator"
KIND_JOINT = "joint"
KIND_GROUP = "group"
KINDS = (KIND_LOCATOR, KIND_JOINT, KIND_GROUP)

#: 세 점이 이보다 가까우면 일직선으로 본다 (v 의 길이)
STRAIGHT_EPS = 1e-4


# =========================
# 계산 (씬을 안 바꾼다)
# =========================

def world_point(node):
    return om.MVector(*cmds.xform(node, query=True, worldSpace=True, translation=True))


def solve_position(p1, p2, p3, distance):
    """`A' = A + n*v` 를 계산한다. 세 인자는 `MVector`. 돌려주는 것도 `MVector`.

    **씬을 건드리지 않는다.** `A00130_ControlRig_V02` 처럼 노드를 남기지 않고 위치만
    필요한 곳이 이걸 쓴다.
    """
    a = (p1 + p3) * 0.5
    return a + (p2 - a) * float(distance)


def solve(nodes, distance):
    """세 노드의 월드 위치로 `A'` 을 계산한다. `(위치 또는 None, note)`."""
    if len(nodes) != 3:
        return None, "needs exactly 3 objects"
    missing = [n for n in nodes if not cmds.objExists(n)]
    if missing:
        return None, "missing: " + ", ".join(missing)

    p1, p2, p3 = [world_point(n) for n in nodes]
    a = (p1 + p3) * 0.5
    v = p2 - a
    note = ""
    if v.length() < STRAIGHT_EPS:
        # 관절이 안 굽어 있으면 v 가 0 이라 n 이 얼마든 A 에 머문다.
        # T 포즈에서 흔하다 - 막지 않고 알린다.
        note = ("the three points are in a straight line, so the target sits on the "
                "chord no matter what the distance is - bend the joint first")
    return a + v * float(distance), note


# =========================
# 씬 조회
# =========================

def _short(node):
    return (node or "").split("|")[-1].split(":")[-1]


def _writable(plug):
    """잠기거나 구동되면 못 쓴다. `getAttr(settable=True)` 는 믿지 않는다."""
    if not cmds.objExists(plug):
        return False
    try:
        if cmds.getAttr(plug, lock=True):
            return False
        if cmds.connectionInfo(plug, isDestination=True):
            return False
    except Exception:
        return False
    return True


def blocked_translate(node):
    """지금 `translate` 를 쓸 수 없게 만드는 채널 이름들."""
    return [a for a in ("translateX", "translateY", "translateZ")
            if not _writable("{0}.{1}".format(node, a))]


def constraint_of(node):
    """이 오브젝트를 몰고 있는 pointConstraint (없으면 None)."""
    found = cmds.listRelatives(node, type="pointConstraint", fullPath=False) or []
    return found[0] if found else None


def is_pole_target(node):
    """이 툴이 만든 폴 타깃인가 — 거리 어트리뷰트와 컨스트레인트가 둘 다 있으면."""
    return (cmds.objExists("{0}.{1}".format(node, DISTANCE_ATTR))
            and constraint_of(node) is not None)


def default_name(nodes):
    """가운데 오브젝트 이름에서 딴 기본 이름."""
    mid = _short(nodes[1]) if len(nodes) == 3 else "pole"
    return "{0}_polTgt".format(mid)


# =========================
# 계획
# =========================

def plan(nodes, distance, name=None, kind=KIND_LOCATOR):
    """무엇이 만들어질지. **씬은 안 바꾼다.** `dict`.

    `ok` · `name` · `position` · `note` · `problems`
    """
    row = {"ok": False, "name": name or "", "position": None,
           "note": "", "problems": []}

    if len(nodes) != 3:
        row["problems"].append(
            "pick exactly 3 objects, in the order end - middle - end "
            "(got {0})".format(len(nodes)))
        return row

    missing = [n for n in nodes if not cmds.objExists(n)]
    if missing:
        row["problems"].append("not in the scene: " + ", ".join(missing))
        return row

    if len(set(nodes)) != 3:
        row["problems"].append("the same object was given more than once")
        return row

    row["name"] = name or default_name(nodes)
    position, note = solve(nodes, distance)
    row["position"] = position
    row["note"] = note

    if cmds.objExists(row["name"]):
        if is_pole_target(row["name"]):
            row["problems"].append(
                "'{0}' is already a pole target - use Update to change its distance, "
                "or pick another name".format(row["name"]))
        else:
            row["problems"].append(
                "'{0}' already exists and is not a pole target - pick another "
                "name".format(row["name"]))
        return row

    row["ok"] = True
    return row


# =========================
# 만들기
# =========================

def _make_node(name, kind):
    if kind == KIND_JOINT:
        cmds.select(clear=True)
        return cmds.joint(name=name, position=(0, 0, 0))
    if kind == KIND_GROUP:
        return cmds.group(empty=True, name=name)
    return cmds.spaceLocator(name=name)[0]


def create(nodes, distance=1.0, name=None, kind=KIND_LOCATOR, parent=None):
    """폴 타깃을 만들고 `A'` 에 **늘 붙어 있게** 한다. `(node 또는 None, messages)`.

    전체가 **undo 한 스텝**이다. 만드는 노드는 셋:

        <name>                      타깃 (거리 어트리뷰트를 갖는다)
        <name>_pointConstraint1     타깃 3개
        <name>_oneMinusN            plusMinusAverage : 1 - n
        <name>_side                 multiplyDivide   : (1-n)/2
    """
    messages = []
    row = plan(nodes, distance, name=name, kind=kind)
    for p in row["problems"]:
        messages.append("[Warning] " + p)
    if not row["ok"]:
        return None, messages
    if row["note"]:
        messages.append("[Warning] {0}.".format(row["note"]))

    made = None
    with undo_chunk():
        made = _make_node(row["name"], kind if kind in KINDS else KIND_LOCATOR)
        if parent and cmds.objExists(parent):
            made = cmds.parent(made, parent)[0]

        blocked = blocked_translate(made)
        if blocked:
            messages.append("[ERR] {0}: translate is locked or driven ({1}).".format(
                _short(made), ", ".join(blocked)))
            cmds.delete(made)
            return None, messages

        cmds.addAttr(made, longName=DISTANCE_ATTR, attributeType="double",
                     defaultValue=float(distance), keyable=True)
        cmds.setAttr("{0}.{1}".format(made, DISTANCE_ATTR), float(distance))

        _wire(made, nodes, messages)

    messages.append(
        "[OK] '{0}' follows {1} at distance {2:g} - change '{3}' to move it.".format(
            _short(made), " / ".join(_short(n) for n in nodes),
            float(distance), DISTANCE_ATTR))
    return made, messages


def targets_of(target):
    """이 오브젝트를 몰고 있는 pointConstraint 의 타깃 목록 (없으면 빈 목록)."""
    con = constraint_of(target)
    if not con:
        return []
    return cmds.pointConstraint(con, query=True, targetList=True) or []


def ensure(target, nodes, distance, reset_distance=False):
    """**이미 있는** 오브젝트를 폴 타깃으로 만들거나 갱신한다. `(status, messages)`.

    `status` 는 `"wired"` · `"kept"` · `"rewired"` · `"skipped"`.

    ── 왜 거리를 안 덮어쓰나 ────────────────────────────────────────────────
    이미 배선돼 있으면 **`poleDistance` 값을 그대로 둔다.** 실시간으로 맞추라고 만든
    어트리뷰트인데 실행할 때마다 json 값으로 되돌리면 **맞춰 둔 것이 매번 날아간다.**
    처음 만들 때만 json 의 값을 쓴다. 되돌리고 싶으면 `reset_distance` 를 켠다.
    """
    messages = []
    if not cmds.objExists(target):
        return "skipped", ["[Warning] '{0}' is not in the scene.".format(target)]

    missing = [n for n in nodes if not cmds.objExists(n)]
    if missing:
        return "skipped", ["[Warning] {0}: missing {1}.".format(
            _short(target), ", ".join(missing))]

    plug = "{0}.{1}".format(target, DISTANCE_ATTR)
    mine = cmds.objExists(plug)
    con = constraint_of(target)

    if con and not mine:
        # 우리가 만든 것이 아니다 - 남의 컨스트레인트를 조용히 지우지 않는다
        return "skipped", ["[Warning] {0}: '{1}' already drives it and it has no "
                           "'{2}' - left alone.".format(
                               _short(target), _short(con), DISTANCE_ATTR)]

    if mine and con:
        want = [_long(n) for n in nodes]
        have = [_long(t) for t in targets_of(target)]
        if want == have:
            if reset_distance and _writable(plug):
                cmds.setAttr(plug, float(distance))
                return "wired", messages
            return "kept", messages
        cmds.delete(con)
        con = None
        messages.append("[Info] {0}: the chain changed - rebuilt.".format(
            _short(target)))

    blocked = blocked_translate(target)
    if blocked and not con:
        return "skipped", ["[Warning] {0}: translate is locked or driven ({1}).".format(
            _short(target), ", ".join(blocked))]

    if not mine:
        cmds.addAttr(target, longName=DISTANCE_ATTR, attributeType="double",
                     defaultValue=float(distance), keyable=True)
        cmds.setAttr(plug, float(distance))

    _wire(target, nodes, messages)
    return "wired", messages


def _long(node):
    names = cmds.ls(node, long=True) or []
    return names[0] if names else node


def _wire(target, nodes, messages):
    """컨스트레인트와 노드 둘을 만들고 가중치를 **연결**한다.

    가중치를 `setAttr` 로 넣으면 `n > 1` 에서 죽는다(모듈 주석). 반드시 연결이다.
    """
    con = cmds.pointConstraint(nodes[0], nodes[1], nodes[2], target,
                               maintainOffset=False)[0]
    aliases = cmds.pointConstraint(con, query=True, weightAliasList=True) or []
    if len(aliases) != 3:
        messages.append("[ERR] {0}: expected 3 weights, got {1}.".format(
            _short(target), len(aliases)))
        return con

    base = _short(target)
    sub = cmds.createNode("plusMinusAverage", name=base + "_oneMinusN")
    cmds.setAttr(sub + ".operation", 2)                  # subtract
    cmds.setAttr(sub + ".input1D[0]", 1.0)
    cmds.connectAttr("{0}.{1}".format(target, DISTANCE_ATTR), sub + ".input1D[1]")

    half = cmds.createNode("multiplyDivide", name=base + "_side")
    cmds.setAttr(half + ".operation", 2)                 # divide
    cmds.setAttr(half + ".input2X", 2.0)
    cmds.connectAttr(sub + ".output1D", half + ".input1X")

    # ★ setAttr 이 아니라 연결. 음수 가중치가 필요하고 setAttr 은 min 0 에 막힌다.
    cmds.connectAttr(half + ".outputX", "{0}.{1}".format(con, aliases[0]))
    cmds.connectAttr("{0}.{1}".format(target, DISTANCE_ATTR),
                     "{0}.{1}".format(con, aliases[1]))
    cmds.connectAttr(half + ".outputX", "{0}.{1}".format(con, aliases[2]))
    return con


# =========================
# 고치기 / 굳히기
# =========================

def update(target, distance):
    """이미 있는 폴 타깃의 거리만 바꾼다. 노드는 다시 만들지 않는다."""
    messages = []
    plug = "{0}.{1}".format(target, DISTANCE_ATTR)
    if not cmds.objExists(plug):
        messages.append("[Warning] {0} has no '{1}' - it was not made by this tool.".format(
            _short(target), DISTANCE_ATTR))
        return False, messages
    if not _writable(plug):
        messages.append("[Warning] {0}.{1} is locked or driven.".format(
            _short(target), DISTANCE_ATTR))
        return False, messages

    with undo_chunk():
        cmds.setAttr(plug, float(distance))
    messages.append("[OK] {0} distance -> {1:g}.".format(_short(target), float(distance)))
    return True, messages


def bake(target):
    """컨스트레인트와 보조 노드를 지우고 **그 자리에 굳힌다**. 되돌리려면 undo."""
    messages = []
    if not cmds.objExists(target):
        messages.append("[Warning] '{0}' is gone.".format(target))
        return False, messages

    con = constraint_of(target)
    if not con:
        messages.append("[Info] {0} has no constraint - nothing to bake.".format(
            _short(target)))
        return False, messages

    keep = cmds.xform(target, query=True, worldSpace=True, translation=True)

    with undo_chunk():
        # 컨스트레인트가 물고 있던 보조 노드를 함께 지운다
        extra = []
        for alias in (cmds.pointConstraint(con, query=True, weightAliasList=True) or []):
            for src in (cmds.listConnections("{0}.{1}".format(con, alias),
                                             source=True, destination=False) or []):
                if src != target:
                    extra.append(src)
        cmds.delete(con)
        for node in sorted(set(extra)):
            if cmds.objExists(node) and not (cmds.listConnections(
                    node, source=False, destination=True) or []):
                cmds.delete(node)
        cmds.xform(target, worldSpace=True, translation=keep)

    messages.append("[OK] {0} baked in place - the constraint and its helper nodes "
                    "are gone.".format(_short(target)))
    return True, messages
