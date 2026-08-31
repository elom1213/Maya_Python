# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-31
# A00130_ControlRig_V02 - Pair : 세트 A 의 하나뿐인 원소로 세트 B 의 하나뿐인 원소를 맞춘다.
#
# Match 가 끝난 **뒤에** 돈다.
#
# ── Match 와 무엇이 다른가 ──────────────────────────────────────────────────
#
# Match 는 **템플릿 조인트**를 기준으로 케이지 세트의 원소들을 옮긴다(1:N).
# Pair 는 **세트 대 세트**다 — `from` 세트의 원소 하나로 `to` 세트의 원소 하나를 맞춘다.
# 조인트가 끼어들지 않는다.
#
# ── 하나임을 검사한다 ───────────────────────────────────────────────────────
#
# 요구가 분명하다: **두 세트의 원소가 모두 하나일 때만** 맞춘다.
# 0개거나 2개 이상이면 **추측하지 않고 건너뛰고 알린다** — 어느 것을 고를지 정할 근거가
# 없는데 하나를 골라 버리면 조용히 틀린 리그가 된다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import scene_utils as su


#: 결과 코드
ST_OK = "ok"
ST_NO_SET = "set missing"
ST_NOT_ONE = "not exactly one"      # 원소가 0개거나 2개 이상
ST_BLOCKED = "blocked"
ST_ERROR = "error"


def _members(set_name, namespace):
    """`(세트 노드 또는 None, 멤버 목록, 하위세트 목록)`."""
    node, _found = su.resolve(set_name, namespace)
    if not node:
        return None, [], []
    if not su.is_set(node):
        return node, [node], []
    members, skipped = su.resolve_members(node)
    return node, members, skipped


def plan(doc, namespace):
    """무엇을 무엇에 맞출지 계산한다. **씬은 안 바꾼다.** `(rows, messages)`.

    각 행: `from` · `to` · `from_node` · `to_node` · `source` · `target` ·
           `match` · `status` · `note`
    """
    messages = []
    rows = []
    match = tuple(doc.get("match") or ("t", "r"))

    for entry in (doc.get("pairs") or []):
        row = {
            "from": entry["from"], "to": entry["to"],
            "from_node": None, "to_node": None,
            "source": None, "target": None,
            "match": match, "status": ST_OK, "note": "",
        }

        a_node, a_members, _a_sub = _members(entry["from"], namespace)
        b_node, b_members, _b_sub = _members(entry["to"], namespace)
        row["from_node"], row["to_node"] = a_node, b_node

        missing = [n for n, node in ((entry["from"], a_node), (entry["to"], b_node))
                   if not node]
        if missing:
            row["status"] = ST_NO_SET
            row["note"] = "looked for " + " and ".join(
                su.candidates(missing[0], namespace))
            rows.append(row)
            continue

        # ★ 두 세트 모두 원소가 정확히 하나여야 한다
        if len(a_members) != 1 or len(b_members) != 1:
            row["status"] = ST_NOT_ONE
            row["note"] = "{0} has {1}, {2} has {3} - both must hold exactly one".format(
                su.short_name(a_node), len(a_members),
                su.short_name(b_node), len(b_members))
            rows.append(row)
            continue

        row["source"], row["target"] = a_members[0], b_members[0]

        want_t, want_r = "t" in match, "r" in match
        blocked = []
        for group, want in (("translate", want_t), ("rotate", want_r)):
            if not want:
                continue
            state, names = su.channel_group_state(row["target"], group)
            if state != su.GROUP_FREE:
                blocked.append("{0} ({1})".format(group, ", ".join(names)))
        if blocked:
            row["status"] = ST_BLOCKED
            row["note"] = "locked or driven: " + "; ".join(blocked)

        rows.append(row)

    counts = summarize(rows)
    messages.append("[OK] {0} pair(s) planned - {1}.".format(
        len(rows), ", ".join("{0} {1}".format(v, k) for k, v in sorted(counts.items()))))
    return rows, messages


def apply(rows):
    """계산된 대로 맞춘다. `(results, messages)`. **undo 한 스텝.**"""
    messages = []
    results = {"matched": 0, "skipped": 0}
    want_t = want_r = True

    with undo_chunk():
        for row in rows:
            if row["status"] != ST_OK:
                results["skipped"] += 1
                messages.append("[Warning] {0} -> {1} : {2} ({3}).".format(
                    row["from"], row["to"], row["status"], row["note"]))
                continue

            want_t = "t" in row["match"]
            want_r = "r" in row["match"]
            try:
                cmds.matchTransform(row["target"], row["source"],
                                    position=want_t, rotation=want_r, scale=False)
            except Exception as e:
                results["skipped"] += 1
                messages.append("[ERR] {0} -> {1} : {2}".format(
                    su.short_name(row["source"]), su.short_name(row["target"]), e))
                continue

            results["matched"] += 1
            messages.append("[OK] {0} <- {1}.".format(
                su.short_name(row["target"]), su.short_name(row["source"])))

    messages.append("[OK] Pair done - {0} matched, {1} skipped.".format(
        results["matched"], results["skipped"]))
    return results, messages


def summarize(rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts
