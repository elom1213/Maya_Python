# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-31
# A00130_ControlRig_V02 - Constrain : 포즈 오브젝트를 `Con` 이 가리키는 노드에 물린다.
#
# Pair 가 끝난 **뒤에** 돈다.
#
# ── 규칙 ────────────────────────────────────────────────────────────────────
#
#   1. `C04_pose_objects` 세트의 원소를 전부 본다
#   2. 각 오브젝트에 `Con` 어트리뷰트가 있는지 검사
#   3. 있으면 거기 **연결된 노드**를 찾는다
#   4. 그 노드가 오브젝트를 **drive** 하도록 `parentConstraint` 를 건다
#
# ── 실측으로 갈린 것 ────────────────────────────────────────────────────────
#
# 1. **같은 드라이버로 다시 걸면 멱등**이다 — 같은 컨스트레인트 노드가 돌아오고 타깃도
#    1개 그대로다. 그런데 **드라이버가 다르면 조용히 타깃이 2개로 늘어난다.**
#    `Con` 이 바뀐 뒤 다시 돌리면 **두 노드가 반씩 끌어당기는** 리그가 된다.
#    -> 이미 `parentConstraint` 가 걸린 오브젝트는 **건드리지 않고 알린다.**
#
# 2. **잠긴 채널이 있으면 `RuntimeError`** 다 (`Connection not made: ...`).
#    조용하진 않지만, 예외를 던지고 멈추는 대신 **미리 보고 건너뛴다.**
#
# 3. `maintainOffset` 이 결과를 가른다 — `False` 면 오브젝트가 **드라이버로 끌려가고**
#    (위치뿐 아니라 **회전까지**), `True` 면 제자리에 남는다.
#
#    ★ **기본은 `True` 다** (v02.17). 마야 명령 기본값이 `False` 라 그걸 따랐는데, 그러면
#      `Pair` 단계에서 맞춰 둔 포즈 오브젝트의 **회전이 걸자마자 드라이버 값으로 덮인다.**
#      앞 단계가 세워 둔 것을 다음 단계가 지우는 셈이라 이 파이프라인의 기본값이 될 수 없다.
#      json 의 `maintain_offset` 로 여전히 끌 수 있다.
#
#    ★ **켰다고 믿지 않고 잰다** — 걸기 **전후의 월드 행렬**을 비교해 위치·회전이 얼마나
#      움직였는지 확인하고, 움직였으면 그 수치를 로그에 적는다. `mo` 를 켜도 잠긴 채널이나
#      이상한 부모 밑에서는 어긋날 수 있고, **조용히 틀리는 것이 가장 나쁘다.**
#
# 4. `Con` 이 `message` 든 일반 어트리뷰트든 `listConnections` 로 노드를 얻는다.

import math

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import scene_utils as su


#: 결과 코드
ST_OK = "ok"
ST_NO_SET = "set missing"
ST_NO_ATTR = "no Con attribute"
ST_NO_DRIVER = "Con is not connected"
ST_ALREADY = "already constrained"
ST_BLOCKED = "blocked"
ST_ERROR = "error"


#: 걸기 전후가 '그대로' 라고 볼 한계 (씬 단위 / 도)
KEEP_POS_EPS = 1.0e-4
KEEP_ROT_EPS = 1.0e-3


def maintain_offset(doc):
    """`maintainOffset` 을 쓸지 - **없으면 켬**(v02.17, 모듈 주석 3번)."""
    return bool((doc or {}).get("maintain_offset", True))


def world_matrix(node):
    """월드 행렬 16개 값. 못 읽으면 `None`."""
    try:
        return cmds.xform(node, query=True, worldSpace=True, matrix=True)
    except Exception:
        return None


def drift(before, after):
    """두 월드 행렬 사이의 `(위치 차, 회전 차(도))`.

    회전은 **세 축 사이의 각** 중 최대다 - 오일러로 빼면 `180` 과 `-180` 이 다르게 나와
    가만히 있는 것도 움직인 것처럼 보인다.
    """
    if not before or not after:
        return 0.0, 0.0
    pos = math.sqrt(sum((after[12 + i] - before[12 + i]) ** 2 for i in range(3)))
    rot = 0.0
    for i in range(3):
        u = om.MVector(before[i * 4], before[i * 4 + 1], before[i * 4 + 2])
        v = om.MVector(after[i * 4], after[i * 4 + 1], after[i * 4 + 2])
        if u.length() < 1e-9 or v.length() < 1e-9:
            continue
        dot = max(-1.0, min(1.0, u.normal() * v.normal()))
        rot = max(rot, math.degrees(math.acos(dot)))
    return pos, rot


def existing_constraint(node):
    """이 오브젝트에 이미 걸린 parentConstraint (없으면 None)."""
    found = cmds.listRelatives(node, type="parentConstraint", fullPath=False) or []
    return found[0] if found else None


def drivers_of(node, attribute):
    """`Con` 에 연결된 노드들. `(drivers, note)`.

    소스 쪽을 먼저 본다 — `message` 로 노드를 담아 두면 그쪽이다(실측).
    없으면 반대 방향도 본다. 어느 타입이든 `listConnections` 로 노드가 나온다.
    """
    plug = "{0}.{1}".format(node, attribute)
    if not cmds.objExists(plug):
        return [], ""

    src = cmds.listConnections(plug, source=True, destination=False) or []
    if src:
        return sorted(set(src)), ""

    dst = cmds.listConnections(plug, source=False, destination=True) or []
    if dst:
        return sorted(set(dst)), "found on the output side of '{0}'".format(attribute)

    return [], ""


def plan(doc, namespace):
    """무엇을 무엇에 물릴지 계산한다. **씬은 안 바꾼다.** `(rows, messages)`.

    각 행: `object` · `drivers` · `status` · `note` · `offset`
    """
    messages = []
    rows = []
    attribute = doc.get("attribute") or "Con"

    set_node, _found = su.resolve(doc.get("set"), namespace)
    if not set_node:
        messages.append("[ERR] Pose object set not found. Looked for {0}.".format(
            " and ".join(su.candidates(doc.get("set") or "", namespace))))
        return rows, messages
    if not su.is_set(set_node):
        messages.append("[Warning] '{0}' is not a set.".format(set_node))
        return rows, messages

    members, skipped = su.resolve_members(set_node)
    if skipped:
        messages.append("[Info] {0}: {1} sub-set(s) ignored.".format(
            su.short_name(set_node), len(skipped)))

    for obj in members:
        row = {"object": obj, "drivers": [], "status": ST_OK, "note": "",
               "offset": None, "offset_rot": None}

        plug = "{0}.{1}".format(obj, attribute)
        if not cmds.objExists(plug):
            row["status"] = ST_NO_ATTR
            row["note"] = "no '{0}' attribute".format(attribute)
            rows.append(row)
            continue

        drivers, note = drivers_of(obj, attribute)
        row["drivers"] = drivers
        row["note"] = note
        if not drivers:
            row["status"] = ST_NO_DRIVER
            row["note"] = "'{0}' exists but nothing is connected to it".format(attribute)
            rows.append(row)
            continue

        already = existing_constraint(obj)
        if already:
            row["status"] = ST_ALREADY
            row["note"] = ("'{0}' is already there - left alone. Delete it first if the "
                           "driver changed, otherwise a second target gets added "
                           "silently.".format(su.short_name(already)))
            rows.append(row)
            continue

        blocked = []
        for group in ("translate", "rotate"):
            state, names = su.channel_group_state(obj, group)
            if state != su.GROUP_FREE:
                blocked.append("{0} ({1})".format(group, ", ".join(names)))
        if blocked:
            row["status"] = ST_BLOCKED
            row["note"] = "locked or driven: " + "; ".join(blocked)
            rows.append(row)
            continue

        # 드라이버와 어긋나 있으면 maintainOffset 이 결과를 가른다 - 미리 잰다.
        # **회전도 잰다** - 위치가 같아도 회전이 다르면 mo off 에서 덮인다.
        pos, rot = drift(world_matrix(drivers[0]), world_matrix(obj))
        row["offset"] = pos
        row["offset_rot"] = rot

        rows.append(row)

    counts = summarize(rows)
    messages.append("[OK] {0} pose object(s) planned - {1}.".format(
        len(rows), ", ".join("{0} {1}".format(v, k) for k, v in sorted(counts.items()))))
    return rows, messages


def apply(rows, doc):
    """계산된 대로 `parentConstraint` 를 건다. `(results, messages)`. **undo 한 스텝.**"""
    messages = []
    results = {"constrained": 0, "skipped": 0, "targets": 0}
    mo = maintain_offset(doc)
    results["moved"] = 0
    results["kept"] = 0

    with undo_chunk():
        for row in rows:
            if row["status"] != ST_OK:
                results["skipped"] += 1
                messages.append("[Warning] {0}: {1} - {2}.".format(
                    su.short_name(row["object"]), row["status"], row["note"]))
                continue

            if not mo and ((row["offset"] or 0.0) > KEEP_POS_EPS
                           or (row["offset_rot"] or 0.0) > KEEP_ROT_EPS):
                messages.append(
                    "[Info] {0}: the driver is {1:.4g} away and {2:.3f} deg apart - "
                    "with 'maintain offset' off it will snap onto the driver.".format(
                        su.short_name(row["object"]), row["offset"] or 0.0,
                        row["offset_rot"] or 0.0))

            # ★ 걸기 전 자리를 적어 둔다 - 뒤에서 정말 그대로인지 잰다
            was = world_matrix(row["object"])

            try:
                made = cmds.parentConstraint(*(row["drivers"] + [row["object"]]),
                                             maintainOffset=mo)
            except Exception as e:
                results["skipped"] += 1
                messages.append("[ERR] {0}: {1}".format(su.short_name(row["object"]), e))
                continue

            moved_pos, moved_rot = drift(was, world_matrix(row["object"]))
            if moved_pos > KEEP_POS_EPS or moved_rot > KEEP_ROT_EPS:
                results["moved"] += 1
                if mo:
                    # mo 를 켰는데도 움직였다 - 조용히 넘기면 안 되는 종류다
                    messages.append(
                        "[Warning] {0}: 'maintain offset' is on but it still moved "
                        "{1:.4g} and turned {2:.3f} deg. Check for locked or driven "
                        "channels on it or on its parents.".format(
                            su.short_name(row["object"]), moved_pos, moved_rot))
            else:
                results["kept"] += 1

            results["constrained"] += 1
            results["targets"] += len(row["drivers"])
            messages.append("[OK] {0} is driven by {1} ({2}).".format(
                su.short_name(row["object"]),
                ", ".join(su.short_name(d) for d in row["drivers"]),
                su.short_name(made[0]) if made else "?"))

    messages.append(
        "[OK] Constrain done - {0} object(s) constrained by {1} driver(s), "
        "{2} skipped. Maintain offset {3} - {4} stayed exactly where they were, "
        "{5} moved.".format(
            results["constrained"], results["targets"], results["skipped"],
            "on" if mo else "off", results["kept"], results["moved"]))
    if mo and results["moved"]:
        messages.append(
            "[Warning] {0} object(s) moved even though 'maintain offset' is on - "
            "they are listed above.".format(results["moved"]))
    return results, messages


def summarize(rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts
