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
# 3. `maintainOffset` 이 결과를 가른다 — `False` 면 오브젝트가 **드라이버로 끌려가고**,
#    `True` 면 제자리에 남는다. 기본은 `False`(마야 명령 기본값)이고 json 에서 바꾼다.
#    드라이버와 오브젝트가 **떨어져 있으면 로그에 거리를 적는다** — `mo` 때문에 튀는
#    경우가 바로 그때뿐이라서다.
#
# 4. `Con` 이 `message` 든 일반 어트리뷰트든 `listConnections` 로 노드를 얻는다.

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
        row = {"object": obj, "drivers": [], "status": ST_OK, "note": "", "offset": None}

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

        # 드라이버와 떨어져 있으면 maintainOffset 이 결과를 가른다 - 미리 잰다
        try:
            a = cmds.xform(drivers[0], q=True, ws=True, t=True)
            b = cmds.xform(obj, q=True, ws=True, t=True)
            row["offset"] = max(abs(a[i] - b[i]) for i in range(3))
        except Exception:
            pass

        rows.append(row)

    counts = summarize(rows)
    messages.append("[OK] {0} pose object(s) planned - {1}.".format(
        len(rows), ", ".join("{0} {1}".format(v, k) for k, v in sorted(counts.items()))))
    return rows, messages


def apply(rows, doc):
    """계산된 대로 `parentConstraint` 를 건다. `(results, messages)`. **undo 한 스텝.**"""
    messages = []
    results = {"constrained": 0, "skipped": 0, "targets": 0}
    mo = bool(doc.get("maintain_offset", False))

    with undo_chunk():
        for row in rows:
            if row["status"] != ST_OK:
                results["skipped"] += 1
                messages.append("[Warning] {0}: {1} - {2}.".format(
                    su.short_name(row["object"]), row["status"], row["note"]))
                continue

            if row["offset"] and row["offset"] > 1e-4 and not mo:
                messages.append(
                    "[Info] {0}: the driver is {1:.4g} away - with 'maintain offset' "
                    "off it will snap onto the driver.".format(
                        su.short_name(row["object"]), row["offset"]))

            try:
                made = cmds.parentConstraint(*(row["drivers"] + [row["object"]]),
                                             maintainOffset=mo)
            except Exception as e:
                results["skipped"] += 1
                messages.append("[ERR] {0}: {1}".format(su.short_name(row["object"]), e))
                continue

            results["constrained"] += 1
            results["targets"] += len(row["drivers"])
            messages.append("[OK] {0} is driven by {1} ({2}).".format(
                su.short_name(row["object"]),
                ", ".join(su.short_name(d) for d in row["drivers"]),
                su.short_name(made[0]) if made else "?"))

    messages.append(
        "[OK] Constrain done - {0} object(s) constrained by {1} driver(s), "
        "{2} skipped. Maintain offset {3}.".format(
            results["constrained"], results["targets"], results["skipped"],
            "on" if mo else "off"))
    return results, messages


def summarize(rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts
