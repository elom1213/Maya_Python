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
#
# ── 거리를 고정하는 모드 (v03.05) ★★ ───────────────────────────────────────
#
# 위 식에서 타깃과 가운데 오브젝트의 거리는
#
#     |A' - p2| = |A + n*v - (A + v)| = |n - 1| * |v|
#
# 이라 **굽은 정도(|v|)에 딸려 변한다.** 팔을 펴면 타깃이 팔꿈치로 빨려 들어오고
# 접으면 멀어진다 - 폴 벡터 타깃으로 쓰기에는 이 쪽이 오히려 거슬린다.
#
# 거리를 상수 `d` 로 두려면 **방향만 남기고 길이를 정규화**해야 한다:
#
#     A' = p2 + d * v / |v|
#
# 정규화는 가중 평균이 아니므로 `pointConstraint` 하나로는 안 된다. 그런데 위 식은
#
#     A' = A + n*v  에서  n = 1 + d / |v|
#
# 와 **같은 식**이다. 즉 컨스트레인트 구성은 그대로 두고 **`n` 을 노드로 계산해
# 먹이기만 하면 된다.** 공간 변환은 여전히 컨스트레인트가 공짜로 해 준다.
#
#     |v| = distanceBetween( (p1+p3)/2 , p2 )        <- decomposeMatrix 둘 + average
#     n   = 1 + d / clamp(|v|)
#
# ★ **`multiplyDivide` 의 0 나누기는 0 도 NaN 도 아니고 `100000` 이다** (실측, 경고만 낸다).
#   게다가 `|v|` 가 0 이 아니라 아주 작을 때가 더 위험하다 - `n` 이 1e9 쯤으로 뛰면
#   가중 평균이 큰 수끼리의 뺄셈이 되어 **자릿수가 통째로 날아간다.** 그래서 나누기
#   앞에 `clamp` 를 둬서 `|v|` 의 하한을 `STRAIGHT_EPS` 로 잡는다 - 그러면 일직선에
#   가까운 체인에서도 어긋남이 `d` 를 넘지 않는다.

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

#: 거리를 어떻게 보는가 - 배수(굽은 정도에 비례) / 고정(씬 거리)
MODE_MULTIPLE = "multiple"
MODE_FIXED = "fixed"

#: `n` 을 계산하려고 우리가 만드는 유틸리티 노드 타입.
#: bake / 재배선이 **우리 것만** 지우도록 여기서 멈춘다 (조인트 · 타깃에서 걸린다).
_HELPER_TYPES = ("plusMinusAverage", "multiplyDivide", "distanceBetween",
                 "decomposeMatrix", "clamp")

#: clamp 노드의 위 한계 - 어떤 씬 거리보다 커야 한다
_CLAMP_MAX = 1.0e9


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


def solve_position_fixed(p1, p2, p3, distance):
    """`A' = p2 + d * v/|v|` 를 계산한다 - **가운데 점에서 늘 `d` 만큼** 떨어진 자리.

    방향은 `solve_position` 과 같고 길이만 정규화한다. 일직선이면 방향이 없으므로
    가운데 점을 그대로 돌려준다(막지 않는다 - 부르는 쪽이 경고한다).
    """
    a = (p1 + p3) * 0.5
    v = p2 - a
    length = v.length()
    if length < STRAIGHT_EPS:
        return om.MVector(p2)
    return p2 + v * (float(distance) / length)


def fixed_from_multiple(nodes, distance):
    """배수 `n` 이 **지금 포즈에서** 만드는 자리를 가운데 오브젝트로부터의 거리로.

    `A' = A + n*v` 와 `A' = p2 + d*v/|v|` 는

        d = (n - 1) * |v|

    에서 **같은 점**이다(부호까지 - `n < 1` 이면 `d` 가 음수라 반대쪽으로 간다).

    배수로 잡아 두었던 규칙을 **거리 고정 배선으로 옮길 때** 쓴다. 값을 그대로 넘기면
    뜻이 달라져 타깃이 딴 데로 가는데, 이 환산을 거치면 **놓이는 자리가 예전과 같고**
    그 뒤로 거리가 유지된다. 일직선이면 `|v| = 0` 이라 0 - 가운데 오브젝트 자리다.
    """
    if len(nodes) != 3 or any(not cmds.objExists(n) for n in nodes):
        return float(distance)
    p1, p2, p3 = [world_point(n) for n in nodes]
    v = p2 - (p1 + p3) * 0.5
    return (float(distance) - 1.0) * v.length()


def solve(nodes, distance, fixed=False):
    """세 노드의 월드 위치로 `A'` 을 계산한다. `(위치 또는 None, note)`.

    `fixed=True` 면 `distance` 가 **가운데 오브젝트에서의 씬 거리**다(`solve_position_fixed`).
    """
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
        # 관절이 안 굽어 있으면 v 가 0 이라 밀어낼 방향이 없다.
        # T 포즈에서 흔하다 - 막지 않고 알린다.
        note = ("the three points are in a straight line, so there is no direction to "
                "push out to - the target sits {0} - bend the joint first".format(
                    "on the middle object" if fixed
                    else "on the chord no matter what the distance is"))
    if fixed:
        return solve_position_fixed(p1, p2, p3, distance), note
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

def plan(nodes, distance, name=None, kind=KIND_LOCATOR, fixed=False):
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
    position, note = solve(nodes, distance, fixed=fixed)
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


def create(nodes, distance=1.0, name=None, kind=KIND_LOCATOR, parent=None,
           fixed=False):
    """폴 타깃을 만들고 `A'` 에 **늘 붙어 있게** 한다. `(node 또는 None, messages)`.

    전체가 **undo 한 스텝**이다. 만드는 노드는 셋:

        <name>                      타깃 (거리 어트리뷰트를 갖는다)
        <name>_pointConstraint1     타깃 3개
        <name>_oneMinusN            plusMinusAverage : 1 - n
        <name>_side                 multiplyDivide   : (1-n)/2
    """
    messages = []
    row = plan(nodes, distance, name=name, kind=kind, fixed=fixed)
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

        _wire(made, nodes, messages, fixed=fixed)

    messages.append(_wired_line(made, nodes, distance, fixed))
    return made, messages


def _wired_line(target, nodes, distance, fixed):
    """배선을 마쳤을 때 로그에 남기는 한 줄 - 모드마다 거리의 뜻이 다르다."""
    if fixed:
        return ("[OK] '{0}' follows {1}, always {2:g} away from {3} - change '{4}' "
                "to move it.".format(
                    _short(target), " / ".join(_short(n) for n in nodes),
                    float(distance), _short(nodes[1]), DISTANCE_ATTR))
    return ("[OK] '{0}' follows {1} at distance {2:g} - change '{3}' to move "
            "it.".format(
                _short(target), " / ".join(_short(n) for n in nodes),
                float(distance), DISTANCE_ATTR))


def targets_of(target):
    """이 오브젝트를 몰고 있는 pointConstraint 의 타깃 목록 (없으면 빈 목록)."""
    con = constraint_of(target)
    if not con:
        return []
    return cmds.pointConstraint(con, query=True, targetList=True) or []


def ensure(target, nodes, distance, reset_distance=False, fixed=False):
    """**이미 있는** 오브젝트를 폴 타깃으로 만들거나 갱신한다. `(status, messages)`.

    `status` 는 `"wired"` · `"kept"` · `"rewired"` · `"skipped"`.

    ── 왜 거리를 안 덮어쓰나 ────────────────────────────────────────────────
    이미 배선돼 있으면 **`poleDistance` 값을 그대로 둔다.** 실시간으로 맞추라고 만든
    어트리뷰트인데 실행할 때마다 json 값으로 되돌리면 **맞춰 둔 것이 매번 날아간다.**
    처음 만들 때만 json 의 값을 쓴다. 되돌리고 싶으면 `reset_distance` 를 켠다.

    ── 모드가 다르면 다시 짓는다 ────────────────────────────────────────────
    체인이 같아도 **배선 모드**(배수 / 거리 고정)가 요청과 다르면 `kept` 가 아니라
    다시 짓는다. 안 그러면 체크박스를 켜고 눌러도 아무 일도 안 일어난 것처럼 보인다.
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
        want_mode = MODE_FIXED if fixed else MODE_MULTIPLE
        if want == have and mode_of(target) == want_mode:
            if reset_distance and _writable(plug):
                cmds.setAttr(plug, float(distance))
                return "wired", messages
            return "kept", messages
        if want == have:
            messages.append("[Info] {0}: rewired to '{1}' distance.".format(
                _short(target), want_mode))
        else:
            messages.append("[Info] {0}: the chain changed - rebuilt.".format(
                _short(target)))
        # 보조 노드도 함께 지운다 - 컨스트레인트만 지우면 계산 노드가 떠돌이로 남는다
        _drop_helpers(con)
        con = None

    blocked = blocked_translate(target)
    if blocked and not con:
        return "skipped", ["[Warning] {0}: translate is locked or driven ({1}).".format(
            _short(target), ", ".join(blocked))]

    if not mine:
        cmds.addAttr(target, longName=DISTANCE_ATTR, attributeType="double",
                     defaultValue=float(distance), keyable=True)
        cmds.setAttr(plug, float(distance))

    _wire(target, nodes, messages, fixed=fixed)
    return "wired", messages


def _long(node):
    names = cmds.ls(node, long=True) or []
    return names[0] if names else node


def _wire_n_fixed(target, nodes, base):
    """`n = 1 + d / |v|` 를 노드로 계산하고 **그 결과 plug** 를 돌려준다.

    이 한 줄이 '거리 고정' 모드의 전부다 - 컨스트레인트 구성은 배수 모드와 똑같고,
    거기에 먹이는 `n` 만 상수에서 **계산된 값**으로 바뀐다(모듈 주석).

        <base>_endA / _endB    decomposeMatrix  : 양 끝의 월드 위치
        <base>_mid             plusMinusAverage : (p1+p3)/2   (operation = average)
        <base>_bendLen         distanceBetween  : |v| = |mid - p2|
        <base>_bendClamp       clamp            : |v| 의 하한 (0 나누기 · 자릿수 손실)
        <base>_nRatio          multiplyDivide   : d / |v|
        <base>_n               plusMinusAverage : 1 + d/|v|
    """
    end_a = cmds.createNode("decomposeMatrix", name=base + "_endA")
    end_b = cmds.createNode("decomposeMatrix", name=base + "_endB")
    cmds.connectAttr(_long(nodes[0]) + ".worldMatrix[0]", end_a + ".inputMatrix")
    cmds.connectAttr(_long(nodes[2]) + ".worldMatrix[0]", end_b + ".inputMatrix")

    mid = cmds.createNode("plusMinusAverage", name=base + "_mid")
    cmds.setAttr(mid + ".operation", 3)                  # average
    cmds.connectAttr(end_a + ".outputTranslate", mid + ".input3D[0]")
    cmds.connectAttr(end_b + ".outputTranslate", mid + ".input3D[1]")

    # distanceBetween 은 (inMatrix1 * point1) 과 (inMatrix2 * point2) 사이를 잰다.
    # inMatrix1 을 비워 두면 항등이라 point1 이 그대로 월드 좌표로 쓰인다.
    length = cmds.createNode("distanceBetween", name=base + "_bendLen")
    cmds.connectAttr(mid + ".output3D", length + ".point1")
    cmds.connectAttr(_long(nodes[1]) + ".worldMatrix[0]", length + ".inMatrix2")

    # ★ 0 나누기는 100000 을 돌려주고(실측), 0 에 가까운 |v| 는 n 을 폭발시켜
    #   가중 평균의 자릿수를 먹는다. 나누기 전에 하한을 건다.
    guard = cmds.createNode("clamp", name=base + "_bendClamp")
    cmds.setAttr(guard + ".minR", STRAIGHT_EPS)
    cmds.setAttr(guard + ".maxR", _CLAMP_MAX)
    cmds.connectAttr(length + ".distance", guard + ".inputR")

    ratio = cmds.createNode("multiplyDivide", name=base + "_nRatio")
    cmds.setAttr(ratio + ".operation", 2)                # divide
    cmds.connectAttr("{0}.{1}".format(target, DISTANCE_ATTR), ratio + ".input1X")
    cmds.connectAttr(guard + ".outputR", ratio + ".input2X")

    plus = cmds.createNode("plusMinusAverage", name=base + "_n")
    cmds.setAttr(plus + ".input1D[0]", 1.0)
    cmds.connectAttr(ratio + ".outputX", plus + ".input1D[1]")
    return plus + ".output1D"


def _wire(target, nodes, messages, fixed=False):
    """컨스트레인트와 보조 노드를 만들고 가중치를 **연결**한다.

    가중치를 `setAttr` 로 넣으면 `n > 1` 에서 죽는다(모듈 주석). 반드시 연결이다.

    `fixed=True` 면 `n` 이 `poleDistance` 자신이 아니라 `1 + d/|v|` 다. **그 차이가
    전부다** - 아래 `1-n` · `(1-n)/2` · 가중치 연결은 두 모드가 똑같이 쓴다.
    """
    con = cmds.pointConstraint(nodes[0], nodes[1], nodes[2], target,
                               maintainOffset=False)[0]
    aliases = cmds.pointConstraint(con, query=True, weightAliasList=True) or []
    if len(aliases) != 3:
        messages.append("[ERR] {0}: expected 3 weights, got {1}.".format(
            _short(target), len(aliases)))
        return con

    base = _short(target)
    if fixed:
        n_plug = _wire_n_fixed(target, nodes, base)
    else:
        n_plug = "{0}.{1}".format(target, DISTANCE_ATTR)

    sub = cmds.createNode("plusMinusAverage", name=base + "_oneMinusN")
    cmds.setAttr(sub + ".operation", 2)                  # subtract
    cmds.setAttr(sub + ".input1D[0]", 1.0)
    cmds.connectAttr(n_plug, sub + ".input1D[1]")

    half = cmds.createNode("multiplyDivide", name=base + "_side")
    cmds.setAttr(half + ".operation", 2)                 # divide
    cmds.setAttr(half + ".input2X", 2.0)
    cmds.connectAttr(sub + ".output1D", half + ".input1X")

    # ★ setAttr 이 아니라 연결. 음수 가중치가 필요하고 setAttr 은 min 0 에 막힌다.
    cmds.connectAttr(half + ".outputX", "{0}.{1}".format(con, aliases[0]))
    cmds.connectAttr(n_plug, "{0}.{1}".format(con, aliases[1]))
    cmds.connectAttr(half + ".outputX", "{0}.{1}".format(con, aliases[2]))
    return con


def helper_nodes(con):
    """컨스트레인트 가중치 위에 매달린 **우리가 만든 유틸리티 노드** 목록.

    이름으로 찾지 않는다(리네임에 깨진다). 가중치에서 거슬러 올라가되 `_HELPER_TYPES`
    가 아닌 노드에서 **멈춘다** - 타깃 트랜스폼과 체인 조인트가 거기서 걸린다.
    """
    if not con or not cmds.objExists(con):
        return []
    stack = []
    for alias in (cmds.pointConstraint(con, query=True, weightAliasList=True) or []):
        stack.extend(cmds.listConnections("{0}.{1}".format(con, alias),
                                          source=True, destination=False) or [])
    found, seen = [], set()
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        if cmds.nodeType(node) not in _HELPER_TYPES:
            continue
        found.append(node)
        stack.extend(cmds.listConnections(node, source=True, destination=False) or [])
    return found


def mode_of(target):
    """이 폴 타깃이 어느 모드로 배선됐나 - `MODE_FIXED` · `MODE_MULTIPLE` · `None`.

    거리 고정 모드에서만 `distanceBetween` 이 `n` 을 계산한다.
    """
    con = constraint_of(target)
    if not con:
        return None
    for node in helper_nodes(con):
        if cmds.nodeType(node) == "distanceBetween":
            return MODE_FIXED
    return MODE_MULTIPLE


def _drop_helpers(con):
    """컨스트레인트와 그 위의 보조 노드를 함께 지운다 (다른 데 안 쓰이는 것만)."""
    extra = helper_nodes(con)
    if con and cmds.objExists(con):
        cmds.delete(con)
    for node in sorted(set(extra)):
        if cmds.objExists(node) and not (cmds.listConnections(
                node, source=False, destination=True) or []):
            cmds.delete(node)


# =========================
# 이미 있는 오브젝트에 걸기
# =========================

def create_on(targets, nodes, distance=1.0, reset_distance=False, fixed=False):
    """**이미 씬에 있는** 오브젝트들에 `create()` 와 같은 배선을 건다.

    `(rows, messages)` — `rows` 는 `[{"target", "status"}]`,
    `status` 는 `ensure()` 의 것(`wired` · `kept` · `skipped`).

    `create()` 는 노드를 새로 만들어 거기에 배선하지만, 이미 만들어 둔 컨트롤러나
    로케이터를 그대로 폴 타깃으로 쓰고 싶은 경우가 더 흔하다. 그때 노드를 다시 만들고
    옛것을 지우는 대신 **가진 오브젝트를 고친다** — 이름 · 부모 · 셰이프 · 이미 걸린
    다른 연결이 전부 그대로 남는다.

    ★ **리스트의 세 오브젝트 자신은 건너뛴다.** 체인 멤버에 이 배선을 걸면 자기 자신을
      타깃으로 삼는 컨스트레인트가 되어 순환이 된다. 마야는 사이클 경고만 내고 씬은
      망가진 채로 남으므로, 걸기 전에 막는다.

    ★ **거리는 기본적으로 덮어쓰지 않는다.** 이미 배선된 타깃의 `poleDistance` 는
      실시간으로 맞춰 둔 값이다 - 바꾸려면 `Update Selected`(= `update()`) 를 쓴다.
      [[ensure]] 와 같은 규칙.

    전체가 **undo 한 스텝**이다.
    """
    messages = []
    rows = []

    targets = [t for t in (targets or [])]
    if not targets:
        messages.append("[Warning] Select the object(s) to turn into pole targets.")
        return rows, messages

    if len(nodes) != 3:
        messages.append(
            "[Warning] pick exactly 3 objects, in the order end - middle - end "
            "(got {0})".format(len(nodes)))
        return rows, messages

    missing = [n for n in nodes if not cmds.objExists(n)]
    if missing:
        messages.append("[Warning] not in the scene: " + ", ".join(missing))
        return rows, messages

    if len(set(_long(n) for n in nodes)) != 3:
        messages.append("[Warning] the same object was given more than once")
        return rows, messages

    _position, note = solve(nodes, distance, fixed=fixed)
    if note:
        messages.append("[Warning] {0}.".format(note))

    chain = set(_long(n) for n in nodes)
    with undo_chunk():
        for target in targets:
            if not cmds.objExists(target):
                rows.append({"target": target, "status": "skipped"})
                messages.append("[Warning] '{0}' is not in the scene.".format(target))
                continue
            if _long(target) in chain:
                # 체인 멤버를 자기 자신으로 몰면 사이클이다 (위 주석)
                rows.append({"target": target, "status": "skipped"})
                messages.append(
                    "[Warning] {0}: it is one of the three objects in the list - "
                    "a pole target cannot be driven by itself.".format(_short(target)))
                continue

            status, notes = ensure(target, nodes, distance,
                                   reset_distance=reset_distance, fixed=fixed)
            rows.append({"target": target, "status": status})
            messages.extend(notes)
            if status == "wired":
                messages.append(_wired_line(
                    target, nodes,
                    cmds.getAttr("{0}.{1}".format(target, DISTANCE_ATTR)), fixed))
            elif status == "kept":
                messages.append(
                    "[Info] {0}: already follows the same three objects - left as "
                    "it is (use Update Selected to change the distance).".format(
                        _short(target)))

    return rows, messages


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
        # 컨스트레인트가 물고 있던 보조 노드를 함께 지운다.
        # 거리 고정 모드는 계산 노드가 여러 단이라 **한 단만 지우면 떠돌이가 남는다**.
        _drop_helpers(con)
        cmds.xform(target, worldSpace=True, translation=keep)

    messages.append("[OK] {0} baked in place - the constraint and its helper nodes "
                    "are gone.".format(_short(target)))
    return True, messages
