# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-31
# A00130_ControlRig_V02 - IK Axis : 시작 조인트의 **정해진 축**이 폴 타깃을 보게 맞춘다.
#
# Match 버튼을 누르면 매칭이 끝난 **뒤에** 돈다.
#
# ── 무엇을 고치나 ───────────────────────────────────────────────────────────
#
#     jnt_01
#     └── jnt_02          forward = +X, ikHandle + poleVectorConstraint
#
# 이때 `jnt_01` 의 **어느 축이 폴을 보는지는 마야가 정한다.** 실측하면 기본은 `-Y` 다.
# 리그가 `+Z` 를 원하면 맞춰 줘야 한다.
#
# ── 어떻게 고치나 — `twist` 다 (실측으로 갈렸다) ★★ ────────────────────────
#
# **`jointOrient` 로는 안 된다.** 바꿔도 축이 그대로다 — RP 솔버가 월드 방향을 만족시키려
# `rotate` 로 보정해 버려서, 어느 로컬 축이 폴을 보는지가 안 바뀐다(실측).
#
# **`twist` 는 정확히 돈다:**
#
#     twist   0  ->  -Y 가 폴을 본다
#     twist  90  ->  +Z
#     twist 180  ->  +Y
#     twist -90  ->  -Z
#
# ── ★ 레퍼런스에서 유지되는가 (사용자의 조건) ───────────────────────────────
#
# 세팅 후 저장하고 **레퍼런스로 불러와도 같은 축**이어야 한다. `twist` 는 핸들의 평범한
# 어트리뷰트라 파일에 저장된다. 실측:
#
#     원본       twist=90  ->  +Z 가 폴을 본다   jnt_01.rotate = [0, 0, 0]
#     레퍼런스   twist=90  ->  +Z               jnt_01.rotate = [0, 0, 0]
#     임포트     twist=90  ->  +Z
#
# **셋이 같다.** 반대로 `rotate` 에 값을 넣어 고치는 방법은 쓰면 안 된다 — 그 값은
# 솔버가 매 평가마다 덮어쓴다.
#
# ── 기준축을 가정하지 않는다 ────────────────────────────────────────────────
#
# "기본이 `-Y` 이니 `+Z` 로 가려면 90 을 더한다" 로 짜면, 체인 방향이나 마야 버전이
# 조금만 달라도 조용히 틀어진다. 대신 **지금 각도를 재서 그만큼 twist 에 더하고, 다시 재서
# 남은 오차를 보고한다.** 스스로 맞춰 가는 방식이라 기준이 무엇이든 상관없다.

import math

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00060_jointTool_V03.app.core import ik_edit_manager as ike

from . import scene_utils as su


#: 결과 코드
ST_OK = "ok"
ST_NO_SET = "set missing"
ST_NO_POLE = "no pole target"
ST_NO_CHAIN = "chain too short"
ST_BLOCKED = "twist is locked or driven"
ST_ERROR = "error"

#: 이보다 크면 못 맞춘 것으로 본다 (도)
TOLERANCE = 0.01

_AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}


# =========================
# 벡터
# =========================

def parse_axis(text):
    text = (text or "").strip().upper()
    sign = -1.0 if text.startswith("-") else 1.0
    return _AXIS_INDEX.get(text[-1] if text else "X", 0), sign


def axis_world(node, text):
    """노드의 로컬 축이 월드에서 향하는 방향."""
    index, sign = parse_axis(text)
    m = cmds.xform(node, query=True, worldSpace=True, matrix=True)
    return om.MVector(*m[index * 4:index * 4 + 3]) * sign


def world_point(node):
    return om.MVector(*cmds.xform(node, query=True, worldSpace=True, translation=True))


def _flatten(vec, forward):
    """forward 에 수직인 성분만 남긴다."""
    return vec - forward * (vec * forward)


def signed_angle(a, b, axis):
    """`a` 에서 `b` 로, `axis` 를 축으로 한 **부호 있는** 각도(도)."""
    if a.length() < 1e-9 or b.length() < 1e-9:
        return 0.0
    a = a.normal()
    b = b.normal()
    axis = axis.normal()
    return math.degrees(math.atan2((a ^ b) * axis, a * b))


# =========================
# 씬 조회
# =========================

def _settle():
    """솔버가 다시 풀도록 강제한다 — 재서 고치는 방식이라 매번 필요하다."""
    try:
        cmds.dgdirty(allPlugs=True)
    except Exception:
        pass


def pole_position(handle):
    """이 핸들의 폴 타깃 위치. `(MVector 또는 None, note)`."""
    con = ike.pole_vector_constraint(handle)
    if not con:
        return None, "no pole vector constraint on this handle"
    targets = ike.pole_vector_targets(con)
    if not targets:
        return None, "'{0}' has no target".format(su.short_name(con))
    if len(targets) > 1:
        return world_point(targets[0]), "several pole targets - used {0}".format(
            su.short_name(targets[0]))
    return world_point(targets[0]), ""


def measure(handle, axis):
    """지금 그 축이 폴에서 몇 도 벗어나 있나. `(각도 또는 None, note)`.

    각도는 **부호가 있다** — 그만큼 `twist` 에 더하면 맞는다.
    """
    joints = ike.chain_joints(handle)
    if len(joints) < 2:
        return None, "the chain has fewer than 2 joints"

    root, nxt = joints[0], joints[1]
    forward = world_point(nxt) - world_point(root)
    if forward.length() < 1e-9:
        return None, "the first two joints sit on top of each other"
    forward.normalize()

    pole, note = pole_position(handle)
    if pole is None:
        return None, note

    want = _flatten(pole - world_point(root), forward)
    if want.length() < 1e-6:
        return None, "the pole target is on the chain axis - it cannot say which way is up"

    have = _flatten(axis_world(root, axis), forward)
    if have.length() < 1e-6:
        return None, "the '{0}' axis lies along the chain, so it can never point at "
    return signed_angle(have, want, forward), note


# =========================
# 계획
# =========================

def _handles(set_name, namespace):
    node, _found = su.resolve(set_name, namespace)
    if not node:
        return None, [], []
    if not su.is_set(node):
        return node, [], [node]
    members, _skipped = su.resolve_members(node)
    handles, others = [], []
    for m in members:
        try:
            ok = cmds.objectType(m, isAType="ikHandle")
        except Exception:
            ok = False
        (handles if ok else others).append(m)
    return node, handles, others


def plan(doc, namespace):
    """어느 핸들을 얼마나 돌려야 하나. **씬은 안 바꾼다.** `(rows, messages)`.

    각 행: `handle` · `set` · `axis` · `delta` · `twist` · `status` · `note`
    """
    messages = []
    rows = []

    for entry in (doc.get("sets") or []):
        set_name = entry.get("set")
        axis = entry.get("axis") or "+Z"
        node, handles, others = _handles(set_name, namespace)

        if not node:
            messages.append(
                "[Info] No set called {0} - nothing to align.".format(
                    " or ".join(su.candidates(set_name or "", namespace))))
            continue
        if others:
            messages.append(
                "[Warning] {0}: {1} member(s) are not ikHandles - ignored ({2}).".format(
                    su.short_name(node), len(others),
                    ", ".join(su.short_name(o) for o in others[:5])))

        for handle in handles:
            row = {"handle": handle, "set": set_name, "axis": axis,
                   "delta": None, "twist": None, "status": ST_OK, "note": ""}
            plug = handle + ".twist"
            if cmds.objExists(plug):
                row["twist"] = cmds.getAttr(plug)

            delta, note = measure(handle, axis)
            row["note"] = note
            if delta is None:
                row["status"] = ST_NO_POLE if "pole" in (note or "") else ST_NO_CHAIN
                rows.append(row)
                continue
            row["delta"] = delta

            if not cmds.objExists(plug) or not su.plug_writable(plug):
                row["status"] = ST_BLOCKED
            rows.append(row)

    counts = summarize(rows)
    if rows:
        messages.append("[OK] {0} handle(s) to align - {1}.".format(
            len(rows), ", ".join("{0} {1}".format(v, k)
                                 for k, v in sorted(counts.items()))))
    return rows, messages


def summarize(rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


# =========================
# 적용
# =========================

def apply(rows):
    """`twist` 에 각도를 더해 축을 맞춘다. `(results, messages)`. **undo 한 스텝.**

    한 번 더해 보고 **다시 재서** 남은 오차를 확인한다 — 기준축을 가정하지 않으므로
    부호가 반대여도 두 번째 시도에서 잡힌다.
    """
    messages = []
    results = {"aligned": 0, "skipped": 0, "worst": 0.0}

    with undo_chunk():
        for row in rows:
            handle = row["handle"]
            if row["status"] != ST_OK:
                results["skipped"] += 1
                messages.append("[Warning] {0}: {1}{2}.".format(
                    su.short_name(handle), row["status"],
                    " - " + row["note"] if row["note"] else ""))
                continue

            plug = handle + ".twist"
            base = cmds.getAttr(plug)
            try:
                cmds.setAttr(plug, base + row["delta"])
            except Exception as e:
                results["skipped"] += 1
                messages.append("[ERR] {0}: {1}".format(su.short_name(handle), e))
                continue
            _settle()

            left, _note = measure(handle, row["axis"])
            if left is not None and abs(left) > TOLERANCE:
                # 부호가 반대였던 경우 - 반대로 돌려 본다
                cmds.setAttr(plug, base - row["delta"])
                _settle()
                other, _n = measure(handle, row["axis"])
                if other is None or abs(other) > abs(left):
                    cmds.setAttr(plug, base + row["delta"])
                    _settle()
                else:
                    left = other
                    messages.append(
                        "[Info] {0}: the correction went the other way - used "
                        "-{1:.3f} instead.".format(su.short_name(handle),
                                                   row["delta"]))

            left = abs(left or 0.0)
            results["worst"] = max(results["worst"], left)
            if left > TOLERANCE:
                results["skipped"] += 1
                messages.append(
                    "[Warning] {0}: '{1}' is still {2:.3f} deg off the pole target - "
                    "something else is driving the chain.".format(
                        su.short_name(handle), row["axis"], left))
                continue

            results["aligned"] += 1
            messages.append("[OK] {0}: '{1}' now points at the pole target "
                            "(twist {2:.3f}).".format(
                                su.short_name(handle), row["axis"],
                                cmds.getAttr(plug)))

    if rows:
        messages.append(
            "[OK] IK axis done - {0} aligned, {1} skipped, worst leftover "
            "{2:.4f} deg. The twist value is saved with the file, so a reference "
            "keeps the same axis.".format(
                results["aligned"], results["skipped"], results["worst"]))
    return results, messages
