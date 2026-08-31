# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - Orient & Place : 템플릿 조인트의 **방향**을 규칙대로 잡고,
#                          일부 조인트는 **위치**까지 놓는다 (A1 · A2 · A3 + Place).
#
# 계획서: docs/plans/A00130_ControlRig_V02_orient_plan.md
#
# ── 규칙 셋이 결국 한 가지 계산이다 ────────────────────────────────────────
#
# A1(척추) · A2(팔·다리) · A3(미러) · 손가락의 모든 회전 규칙은
# **"forward 축을 무언가로 aim 하고, up 축을 힌트 쪽으로 둔다"** 하나로 표현된다.
# 다른 것은 **힌트가 무엇이냐** 뿐이다 — 폴 타깃(A2 의 IK 부분)이거나 월드 축(A1 · tail).
#
# ── 실측으로 갈린 것 ───────────────────────────────────────────────────────
#
# 1. **`ikRPsolver` 는 끝 조인트를 회전시키지 않는다** (계획서 2-1)
#    핸들을 옮겨도 `j3.rotate` 는 [0,0,0] 그대로였다. 그래서 A2 는 `A[-1]` 을 못 정한다.
#    -> 다리는 `tail` 이 이어받고, 팔은 `preserve` (그대로 둔다).
#
# 2. **"IK 를 걸었을 때의 회전" 은 그대로는 계산이 안 된다** (계획서 2-2)
#    RP 솔버는 체인을 **강체로** 돌릴 뿐이라 **어느 로컬 축이 폴을 향할지는 시작 방향이
#    정한다.** 그래서 "aim + pole up" 으로 다시 세웠다. up 축은 `+Z` 로 본다(계획서 4-3)
#    — 맞는지는 `up_dev`(월드 축과의 각도)를 재서 표에 띄운다.
#
# 3. **월드 회전 0 은 `rotate=0` 으로도 `jointOrient=0` 으로도 안 된다** (계획서 2-3)
#    `xform -ws -ro 0` 뒤 값을 `jointOrient` 로 옮기고 `rotate` 를 0 으로 두는 방법만 된다.
#
# 4. **Behavior 미러는 축을 `diag(1,-1,-1)` 로 보낸다** (계획서 2-4)
#    위치는 x 만 뒤집고, 세 축 벡터는 y·z 성분만 뒤집힌다. 그래서 오른팔의 forward 가
#    로컬 `-X` 가 된다 — A2 의 `arm_r : -X` 와 맞물린다.
#
# 5. **부모의 방향을 바꾸면 후손이 전부 딸려 움직인다** ★★
#    조인트의 방향은 자식의 월드 위치를 정한다. 척추를 위에서부터 정렬하면 `pelvis` 를
#    돌리는 순간 그 아래가 전부 따라 돌고, **다음 조인트의 aim 이 이미 틀어진 위치로**
#    계산된다. 실측하면 오차가 조인트마다 90도씩 **누적**됐다:
#
#        pelvis   +X=[0,1,0]   OK
#        spine_01 +X=[-1,0,0]  90도 밀림
#        spine_02 +X=[0,-1,0]  180도 밀림
#
#    **직접 자식만 되돌리면 모자란다** — 처음에 그렇게 짰다가 물렸다. 손자가 끌려간 채
#    남는다(실측: `c` 가 (0,120,0) -> (-10,110,0)). 그래서 **모든 후손**을 되돌린다.
#    되돌리는 순서는 **부모부터**(위에서 아래로) — 부모를 나중에 옮기면 자식이 또 움직인다.
#
# 6. **`preserve` 는 로컬 값 기준이다** (계획서 2-6)
#    마야 IK 도 로컬(`rotate`+`jointOrient`)을 지키고 **월드는 부모를 따라 움직인다.**
#    그 변화량을 `world_shift` 로 재서 표에 적는다 — 감추지 않는다.

import math

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from tools.A00060_jointTool_V03.app.core import pole_target_manager as pt

from . import scene_utils as su


#: 결과 코드
ST_OK = "ok"
ST_PRESERVED = "preserved"          # 일부러 안 건드린다 (결정) - 계획서 4-9
ST_NO_RULE = "no rule"              # 아직 규칙이 없다 (미결)  - 계획서 4-9
ST_PLACED = "placed"               # 방향만이 아니라 위치까지 놓았다
ST_POLE = "pole placed"            # 체인에서 계산해 놓았다
ST_MISSING = "joint missing"
ST_BLOCKED = "blocked"
ST_ERROR = "error"

#: 미러 평면 -> 위치에서 뒤집을 축
MIRROR_PLANES = {"YZ": 0, "XZ": 1, "XY": 2}

_AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}


# =========================
# 축 · 벡터
# =========================

def parse_axis(text):
    """`"+X"` · `"-Z"` -> `(인덱스, 부호)`."""
    text = (text or "").strip().upper()
    sign = -1.0 if text.startswith("-") else 1.0
    letter = text[-1] if text else "X"
    return _AXIS_INDEX.get(letter, 0), sign


def axis_vector(text):
    """`"+Z"` -> `MVector(0,0,1)`."""
    index, sign = parse_axis(text)
    v = [0.0, 0.0, 0.0]
    v[index] = sign
    return om.MVector(*v)


def world_axis_of(node, text):
    """노드의 로컬 축이 월드에서 향하는 방향."""
    index, sign = parse_axis(text)
    m = cmds.xform(node, q=True, ws=True, m=True)
    row = m[index * 4:index * 4 + 3]
    return om.MVector(*row) * sign


def angle_between(a, b):
    """두 벡터 사이 각도(도)."""
    if a.length() < 1e-9 or b.length() < 1e-9:
        return 0.0
    d = max(-1.0, min(1.0, a.normal() * b.normal()))
    return math.degrees(math.acos(d))


def world_point(node):
    return om.MVector(*cmds.xform(node, q=True, ws=True, t=True))


# =========================
# 방향 만들기 (모든 규칙이 이 하나를 쓴다)
# =========================

def basis_matrix(origin, forward_dir, up_hint, forward_axis, up_axis):
    """원하는 두 축으로 정규직교 기저를 만들어 월드 행렬로 돌려준다.

    - `forward_dir` : forward 축이 향해야 할 월드 방향
    - `up_hint`     : up 축이 향해야 할 **힌트**(폴 타깃 방향이거나 월드 축).
                      forward 에 수직인 성분만 쓴다.

    세 번째 축은 오른손 좌표계가 되도록 부호를 맞춘다 — 안 그러면 스케일이 −1 인
    행렬이 나와 조인트가 뒤집힌다.
    """
    f = om.MVector(forward_dir)
    if f.length() < 1e-9:
        return None
    f.normalize()

    u = om.MVector(up_hint)
    u = u - f * (u * f)                 # forward 에 수직인 성분만
    if u.length() < 1e-6:
        # 힌트가 forward 와 거의 같은 방향이면 쓸 수 없다 - 다른 축으로 피한다
        fallback = om.MVector(0, 0, 1) if abs(f.z) < 0.9 else om.MVector(0, 1, 0)
        u = fallback - f * (fallback * f)
    u.normalize()

    f_idx, f_sign = parse_axis(forward_axis)
    u_idx, u_sign = parse_axis(up_axis)
    if f_idx == u_idx:
        return None
    t_idx = 3 - f_idx - u_idx           # 남은 축

    rows = [None, None, None]
    rows[f_idx] = f * f_sign
    rows[u_idx] = u * u_sign
    third = rows[f_idx] ^ rows[u_idx]
    third.normalize()
    rows[t_idx] = third

    # 오른손 좌표계로 (det > 0)
    det = rows[0] * (rows[1] ^ rows[2])
    if det < 0:
        rows[t_idx] = -rows[t_idx]

    return om.MMatrix([
        rows[0].x, rows[0].y, rows[0].z, 0.0,
        rows[1].x, rows[1].y, rows[1].z, 0.0,
        rows[2].x, rows[2].y, rows[2].z, 0.0,
        origin.x, origin.y, origin.z, 1.0,
    ])


def descendants(joint):
    """이 조인트의 **모든 후손** (부모가 먼저 오는 순서).

    `listRelatives(allDescendents=True)` 는 **아래에서 위로** 준다. 위치를 되돌릴 때는
    **부모부터** 맞춰야 하므로 뒤집어서 쓴다.
    """
    kids = cmds.listRelatives(joint, allDescendents=True, type="joint",
                              fullPath=False) or []
    return list(reversed(kids))


def _hold_descendants(joint):
    return [(c, cmds.xform(c, q=True, ws=True, t=True)) for c in descendants(joint)]


def _release_descendants(held):
    for child, pos in held:
        if cmds.objExists(child):
            cmds.xform(child, ws=True, t=pos)


def set_world_orientation(joint, matrix, keep_children=True):
    """조인트를 이 월드 행렬의 방향으로. **위치는 안 건드린다.**

    방향은 `jointOrient` 가 갖고 `rotate` 는 0 으로 남긴다 (계획서 2-3 (d)).

    `keep_children` 이면 **모든 후손의 월드 위치를 원래대로 되돌린다.** 직접 자식만으로는
    모자란다 — 손자가 끌려간 채 남아 다음 조인트의 aim 이 틀어진다(모듈 주석 5).
    """
    kids = _hold_descendants(joint) if keep_children else []

    keep = cmds.xform(joint, q=True, ws=True, t=True)

    cmds.setAttr(joint + ".rotate", 0, 0, 0)
    if cmds.attributeQuery("jointOrient", node=joint, exists=True):
        cmds.setAttr(joint + ".jointOrient", 0, 0, 0)

    m = list(matrix)
    m[12], m[13], m[14] = keep[0], keep[1], keep[2]
    cmds.xform(joint, ws=True, m=m)

    _rotate_into_orient(joint)
    _release_descendants(kids)


def _rotate_into_orient(joint, keep_world=False):
    """`rotate` 에 들어간 값을 `jointOrient` 로 옮기고 `rotate` 를 0 으로.

    `keep_world` 면 자식의 월드 위치까지 지킨다(미러처럼 위치도 함께 정한 경우).
    """
    if not cmds.attributeQuery("jointOrient", node=joint, exists=True):
        return
    r = cmds.getAttr(joint + ".rotate")[0]
    if abs(r[0]) < 1e-9 and abs(r[1]) < 1e-9 and abs(r[2]) < 1e-9:
        return
    kids = []
    if keep_world:
        for c in (cmds.listRelatives(joint, children=True, type="joint") or []):
            kids.append((c, cmds.xform(c, q=True, ws=True, m=True)))

    world = cmds.xform(joint, q=True, ws=True, m=True)
    cmds.setAttr(joint + ".rotate", 0, 0, 0)
    cmds.setAttr(joint + ".jointOrient", 0, 0, 0)
    cmds.xform(joint, ws=True, m=world)
    r = cmds.getAttr(joint + ".rotate")[0]
    cmds.setAttr(joint + ".jointOrient", r[0], r[1], r[2])
    cmds.setAttr(joint + ".rotate", 0, 0, 0)

    for child, m in kids:
        if cmds.objExists(child):
            cmds.xform(child, ws=True, m=m)


def world_zero(joint, keep_children=True):
    """월드 회전을 `0,0,0` 으로. `rotate` 도 0 으로 남는다 (계획서 2-3 (d))."""
    kids = _hold_descendants(joint) if keep_children else []

    cmds.xform(joint, ws=True, ro=(0, 0, 0))
    _rotate_into_orient(joint)
    _release_descendants(kids)


# =========================
# 미러
# =========================

def mirror_point(point, plane):
    """평면 기준으로 위치를 뒤집는다."""
    axis = MIRROR_PLANES.get(plane, 0)
    p = [point.x, point.y, point.z]
    p[axis] = -p[axis]
    return om.MVector(*p)


def mirror_behavior_matrix(matrix, plane):
    """마야의 `mirrorJoint -mirrorBehavior` 와 같은 행렬을 만든다.

    실측(계획서 2-4)으로 확인한 규칙:

      위치 : 평면 축의 성분만 부호 반전          (YZ 면 x)
      방향 : **세 축 벡터 전부** 나머지 두 축 성분만 부호 반전

    즉 YZ 미러면 축 벡터는 `diag(1,-1,-1)` 을 지난다. `-R * axis` 와 같은 말이고
    (`R = diag(-1,1,1)`), 그래서 forward 축이 **월드에서 같은 쪽을 보게 되어**
    오른쪽 조인트의 forward 가 로컬 `-X` 가 된다.
    """
    axis = MIRROR_PLANES.get(plane, 0)
    m = list(matrix)

    for row in range(3):
        for col in range(3):
            if col != axis:
                m[row * 4 + col] = -m[row * 4 + col]

    m[12 + axis] = -m[12 + axis]
    return om.MMatrix(m)


def _det3(m):
    a = om.MVector(m[0], m[1], m[2])
    b = om.MVector(m[4], m[5], m[6])
    c = om.MVector(m[8], m[9], m[10])
    return a * (b ^ c)


# =========================
# 데이터 -> 씬 이름
# =========================

def _resolve(name, namespace):
    node, _found = su.resolve(name, namespace)
    return node


def _subtree(root):
    """조인트와 그 하위 전부 (깊이 우선)."""
    out = [root]
    for child in (cmds.listRelatives(root, children=True, type="joint",
                                     fullPath=False) or []):
        out.extend(_subtree(child))
    return out


def _pair_subtrees(source, target):
    """두 계층을 같은 순서로 짝짓는다. `(pairs, messages)`."""
    messages = []
    src = _subtree(source)
    dst = _subtree(target)
    if len(src) != len(dst):
        messages.append(
            "[Warning] {0} has {1} joint(s) but {2} has {3} - mirroring the first "
            "{4}.".format(su.short_name(source), len(src), su.short_name(target),
                          len(dst), min(len(src), len(dst))))
    return list(zip(src, dst)), messages


# =========================
# 위치 보존
# =========================

def _depth(node):
    n, d = node, 0
    while True:
        parents = cmds.listRelatives(n, parent=True, fullPath=False) or []
        if not parents:
            return d
        n, d = parents[0], d + 1


def template_nodes(doc, namespace):
    """씬에 있는 템플릿 조인트 전부 (부모가 먼저 오도록 정렬)."""
    out = []
    for name in (doc.get("_all_joints") or []):
        node = _resolve(name, namespace)
        if node:
            out.append(node)
    return sorted(out, key=_depth)


def snapshot_positions(nodes):
    """월드 위치를 적어 둔다."""
    snap = []
    for n in nodes:
        try:
            snap.append((n, cmds.xform(n, q=True, ws=True, t=True)))
        except Exception:
            pass
    return snap


def restore_positions(snap):
    """적어 둔 월드 위치로 되돌린다.

    **부모부터 되돌려야 한다** — 자식을 먼저 맞춰도 부모를 나중에 옮기면 또 끌려간다.
    `snapshot_positions` 에 넘긴 목록이 이미 깊이순이므로 그대로 돈다.
    """
    moved = 0
    for node, pos in snap:
        if not cmds.objExists(node):
            continue
        # 폴 타깃처럼 translate 가 구동되는 것은 되돌릴 수 없고 되돌릴 필요도 없다
        if su.blocked_channels(node, translate=True, rotate=False):
            continue
        now = cmds.xform(node, q=True, ws=True, t=True)
        if max(abs(now[i] - pos[i]) for i in range(3)) < 1e-7:
            continue
        try:
            cmds.xform(node, ws=True, t=pos)
            moved += 1
        except Exception:
            pass
    return moved


# =========================
# 계획 (씬을 바꾸지 않는다)
# =========================

def plan(doc, namespace, world_zero_spine=None, mirror_enabled=True):
    """어느 조인트에 어떤 규칙이 걸리는지 계산한다. `(rows, messages)`.

    **씬은 바꾸지 않는다.** 각 행:
        joint · wanted · rule · status · note · up_dev · world_shift

    `up_dev` 는 지금 씬 상태로 잰 값이다. **Orient 를 돌리기 전에는 아직 옛 값**이므로,
    `Orient` 뒤에 표가 다시 그려질 때의 숫자가 진짜다(계획서 4-3 검산).
    """
    messages = []
    rows = []
    claimed = {}

    if world_zero_spine is None:
        world_zero_spine = bool(doc.get("world_zero_default", True))

    def add(name, rule, status=ST_OK, note="", up_expect=None):
        node = _resolve(name, namespace)
        row = {"joint": node or name, "wanted": name, "rule": rule,
               "status": status, "note": note, "up_dev": None, "world_shift": None}
        if not node:
            row["status"] = ST_MISSING
            row["note"] = "looked for " + " and ".join(su.candidates(name, namespace))
        elif up_expect:
            try:
                row["up_dev"] = angle_between(world_axis_of(node, up_expect[0]),
                                              axis_vector(up_expect[1]))
            except Exception:
                pass
        if name in claimed:
            row["note"] = (row["note"] + " | " if row["note"] else "") + \
                "also claimed by {0} - {1} wins".format(claimed[name], rule)
        claimed[name] = rule
        rows.append(row)
        return row

    mirror = doc.get("mirror") or {}

    # ---- 1. 미러 ----
    if mirror_enabled:
        for entry in (mirror.get("behavior") or []):
            if entry.get("stage", "early") != "early":
                continue                       # 늦은 미러는 아래 3c 에서
            src = _resolve(entry["source"], namespace)
            dst = _resolve(entry["target"], namespace)
            if not src or not dst:
                add(entry["target"], "A3 mirror", ST_MISSING)
                continue
            pairs = ([(src, dst)] if not entry.get("children")
                     else _pair_subtrees(src, dst)[0])
            for _s, d in pairs:
                add(su.short_name(d), "A3 behavior", note="mirrored from the left")
        for entry in (mirror.get("position_pairs") or []):
            add(entry["target"], "A3 position", note="position mirrored, aimed by A2")

    # ---- 2. A1 ----
    for group in (doc.get("aim_groups") or []):
        use_zero = world_zero_spine and group.get("world_zero_option")
        rule = "A1 world zero" if use_zero else "A1 aim"
        expect = None if use_zero else (group.get("up"), group.get("up_world"))
        for name in group["joints"]:
            add(name, rule, up_expect=expect)

    # ---- 3. A2 ----
    for chain in (doc.get("pole_chains") or []):
        joints = chain["joints"]
        expect = (chain.get("up"), chain.get("expect_up_world"))
        for name in joints[:-1]:
            add(name, "A2 " + chain["name"], up_expect=expect)

        tail = chain.get("tail")
        if tail == "preserve":
            row = add(joints[-1], "A2 keep", ST_PRESERVED,
                      "left exactly as it is - the IK solver never rotates the end joint")
            row["status"] = ST_PRESERVED
        elif isinstance(tail, dict):
            for name in tail["joints"]:
                add(name, "A2 tail", up_expect=(tail.get("up"), tail.get("up_world")))

    # ---- 4. 위치 전용 (마지막에 이긴다) ----
    if mirror_enabled:
        for entry in (mirror.get("position_only") or []):
            add(entry["target"], "A3 position + world zero")
            add(entry["source"], "A3 world zero")

    # ---- 1b. 폴 타깃 ----
    for entry in ((doc.get("pole_targets") or {}).get("targets") or []):
        row = add(entry["name"], "Pole from {0}".format(
            su.short_name(entry["chain"][1])))
        if row["status"] == ST_OK:
            row["status"] = ST_POLE
            row["note"] = "computed from {0}".format(
                " / ".join(su.short_name(n) for n in entry["chain"]))

    # ---- 3b. 하위 계층 정렬 ----
    for group in (doc.get("aim_subtrees") or []):
        root = _resolve(group["root"], namespace)
        if not root:
            add(group["root"], "aim subtree", ST_MISSING)
        else:
            for node in descendants(root):
                add(su.short_name(node), "Aim " + group.get("name", "subtree"),
                    up_expect=(group.get("up"), group.get("up_world")))

    # ---- 3c. 늦은 미러 ----
    if mirror_enabled:
        for entry in (mirror.get("behavior") or []):
            if entry.get("stage", "early") != "late":
                continue
            src = _resolve(entry["source"], namespace)
            dst = _resolve(entry["target"], namespace)
            if not src or not dst:
                add(entry["target"], "A3 behavior (late)", ST_MISSING)
                continue
            pairs = ([(src, dst)] if not entry.get("children")
                     else _pair_subtrees(src, dst)[0])
            for _s, d in pairs:
                add(su.short_name(d), "A3 behavior (late)",
                    note="mirrored from the left after it was aimed")

    # ---- 5. 배치 (마지막) ----
    for group in (doc.get("place") or []):
        for name in group["joints"]:
            row = add(name, "Place {0} {1:g}".format(
                group.get("axis", "+Z"), group.get("distance", 0.0)))
            if row["status"] == ST_OK:
                row["status"] = ST_PLACED
                row["note"] = "moved along its own {0} by {1:g} from the parent".format(
                    group.get("axis", "+Z"), group.get("distance", 0.0))

    # ---- 규칙이 없는 조인트 ----
    known = set(claimed)
    for name in (doc.get("_all_joints") or []):
        if name not in known:
            node = _resolve(name, namespace)
            rows.append({"joint": node or name, "wanted": name, "rule": "(none)",
                         "status": ST_NO_RULE, "note": "untouched - no rule yet",
                         "up_dev": None, "world_shift": None})

    counts = summarize(rows)
    messages.append("[OK] {0} joint(s) planned - {1}.".format(
        len(rows), ", ".join("{0} {1}".format(v, k) for k, v in sorted(counts.items()))))
    return rows, messages


def summarize(rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


# =========================
# 적용
# =========================

def apply(doc, namespace, world_zero_spine=None, mirror_enabled=True):
    """규칙대로 실제로 방향을 잡는다. `(results, messages)`. **undo 한 스텝.**

    순서가 강제된다 (계획서 4-6):
        미러 -> A1 -> A2(+tail/preserve) -> 위치 전용
    """
    messages = []
    results = {"mirrored": 0, "aimed": 0, "preserved": 0, "zeroed": 0,
               # 폴 타깃과 Place 는 둘 다 "위치를 놓는" 일이지만 성격이 다르다.
               # 한 칸에 담으면 요약에서 어느 쪽이 몇 개인지 알 수 없다.
               "poles": 0, "placed": 0, "skipped": 0}

    if world_zero_spine is None:
        world_zero_spine = bool(doc.get("world_zero_default", True))

    mirror = doc.get("mirror") or {}
    plane = mirror.get("plane", "YZ")

    with undo_chunk():
        # ---- 1. 미러 (A2 가 폴 타깃 위치를 읽으므로 반드시 먼저) ----
        if mirror_enabled:
            results["mirrored"] += _do_behavior(mirror, plane, namespace, messages,
                                                stage="early")
            results["mirrored"] += _do_position_pairs(mirror, plane, namespace, messages)
        else:
            messages.append(
                "[Warning] Mirroring is off. A2 reads the pole targets on the right "
                "side, so if they were never mirrored the right arm and leg will be "
                "aimed at the wrong place.")

        # ---- 1b. 폴 타깃을 체인에서 계산해 놓는다 ----
        # A2 가 이 위치를 읽어 롤을 정하므로 **A2 보다 먼저**여야 하고,
        # 오른쪽은 미러가 체인을 놓은 **뒤**여야 한다.
        results["poles"] += _do_pole_targets(doc, namespace, results, messages)

        # ---- 방향을 잡기 전에 위치를 적어 둔다 ----
        # 조인트를 돌리면 자식이 딸려 움직인다(모듈 주석 5). 미러가 끝난 **뒤**에
        # 찍어야 미러로 옮긴 자리가 기준이 된다.
        snap = snapshot_positions(template_nodes(doc, namespace))

        # ---- 2. A1 ----
        results["aimed"] += _do_aim_groups(doc, world_zero_spine, namespace,
                                           results, messages)

        # ---- 3. A2 ----
        results["aimed"] += _do_pole_chains(doc, namespace, results, messages)

        # ---- 끌려간 위치를 되돌린다 (부모부터) ----
        moved = restore_positions(snap)
        if moved:
            messages.append(
                "[Info] {0} joint(s) were dragged along while their parents were "
                "rotated - put back where they were.".format(moved))

        # ---- 3b. 하위 계층 정렬 (손가락) ----
        results["aimed"] += _do_aim_subtrees(doc, namespace, results, messages)

        # ---- 3c. 늦은 미러 (오른손가락 - 왼쪽이 정렬된 뒤라야 한다) ----
        if mirror_enabled:
            results["mirrored"] += _do_behavior(mirror, plane, namespace, messages,
                                                stage="late")

        # ---- 4. 위치 전용 ----
        if mirror_enabled:
            results["zeroed"] += _do_position_only(mirror, plane, namespace,
                                                   results, messages)

        # ---- 4b. 폴 타깃 회전 0 (방향 단계가 끝난 뒤라야 뜻이 있다) ----
        results["zeroed"] += _zero_pole_targets(doc, namespace, results, messages)

        # ---- 5. 배치 (마지막 - 방향이 다 정해진 뒤라야 자기 축이 확정된다) ----
        results["placed"] += _do_place(doc, namespace, results, messages)

    messages.append(
        "[OK] Orient & Place done - {0} mirrored, {1} aimed, {2} preserved, {3} zeroed, "
        "{4} pole target(s) computed, {5} placed, {6} skipped.".format(
            results["mirrored"], results["aimed"], results["preserved"],
            results["zeroed"], results["poles"], results["placed"],
            results["skipped"]))
    return results, messages


def _writable(joint):
    return not su.blocked_channels(joint, translate=False, rotate=True)


def _do_behavior(mirror, plane, namespace, messages, stage="early"):
    """`stage` 가 맞는 behavior 미러만 돈다.

    `late` 가 왜 필요한가 — 오른손가락은 **왼손가락을 정렬한 뒤에** 미러해야 한다.
    이른 미러는 아직 손대지 않은 왼손가락을 복사하므로, 사용자가 놓아 둔 방향이
    그대로 오른쪽에 박힌다.
    """
    done = 0
    for entry in (mirror.get("behavior") or []):
        if entry.get("stage", "early") != stage:
            continue
        src = _resolve(entry["source"], namespace)
        dst = _resolve(entry["target"], namespace)
        if not src or not dst:
            messages.append("[Warning] behavior mirror {0} -> {1}: missing.".format(
                entry["source"], entry["target"]))
            continue

        if entry.get("children"):
            pairs, msgs = _pair_subtrees(src, dst)
            messages.extend(msgs)
        else:
            pairs = [(src, dst)]

        # 부모부터 내려가며 넣는다. 부모를 돌리면 자식이 끌려가지만, 바로 다음에
        # 그 자식의 월드 행렬을 통째로 덮으므로 최종 결과는 정확하다.
        for s, d in pairs:
            try:
                m = om.MMatrix(cmds.xform(s, q=True, ws=True, m=True))
                cmds.xform(d, ws=True, m=list(mirror_behavior_matrix(m, plane)))
                _rotate_into_orient(d, keep_world=True)
                done += 1
            except Exception as e:
                messages.append("[ERR] behavior mirror {0}: {1}".format(
                    su.short_name(d), e))
        messages.append("[OK] behavior mirror {0} -> {1} : {2} joint(s).".format(
            su.short_name(src), su.short_name(dst), len(pairs)))
    return done


def _do_position_pairs(mirror, plane, namespace, messages):
    done = 0
    for entry in (mirror.get("position_pairs") or []):
        src = _resolve(entry["source"], namespace)
        dst = _resolve(entry["target"], namespace)
        if not src or not dst:
            messages.append("[Warning] position mirror {0} -> {1}: missing.".format(
                entry["source"], entry["target"]))
            continue
        want = mirror_point(world_point(src), plane)
        try:
            cmds.xform(dst, ws=True, t=(want.x, want.y, want.z))
            done += 1
        except Exception as e:
            messages.append("[ERR] position mirror {0}: {1}".format(
                su.short_name(dst), e))
    if done:
        messages.append("[OK] position mirror : {0} joint(s).".format(done))
    return done


def _do_aim_groups(doc, world_zero_spine, namespace, results, messages):
    done = 0
    for group in (doc.get("aim_groups") or []):
        use_zero = world_zero_spine and group.get("world_zero_option")
        names = group["joints"]
        nodes = [_resolve(n, namespace) for n in names]

        for i, node in enumerate(nodes):
            if not node:
                results["skipped"] += 1
                messages.append("[Warning] {0}: not in the scene.".format(names[i]))
                continue
            if not _writable(node):
                results["skipped"] += 1
                messages.append("[Warning] {0}: rotation is locked or driven.".format(
                    su.short_name(node)))
                continue

            if use_zero:
                world_zero(node)
                results["zeroed"] += 1
                continue

            child = nodes[i + 1] if i + 1 < len(nodes) else None
            if not child:
                # 마지막 조인트는 앞 조인트의 방향을 물려받는다 (계획서 5-4)
                prev = nodes[i - 1] if i > 0 else None
                if prev:
                    m = cmds.xform(prev, q=True, ws=True, m=True)
                    set_world_orientation(node, om.MMatrix(m))
                    done += 1
                continue

            fwd = world_point(child) - world_point(node)
            mat = basis_matrix(world_point(node), fwd, axis_vector(group["up_world"]),
                               group["forward"], group["up"])
            if mat is None:
                results["skipped"] += 1
                messages.append("[Warning] {0}: could not build an orientation.".format(
                    su.short_name(node)))
                continue
            set_world_orientation(node, mat)
            done += 1

        messages.append("[OK] {0} : {1}.".format(
            group.get("name", "aim group"),
            "world zero" if use_zero else "aimed along the chain"))
    return done


def _do_aim_subtrees(doc, namespace, results, messages):
    """어느 조인트 아래 **전부**를, 각자 제 자식을 보도록 정렬한다.

    손가락처럼 **마디 수가 제각각이고 갈래가 많은** 계층에 쓴다 — 조인트 이름을 하나하나
    적는 대신 뿌리 하나만 적는다. 손가락이 늘거나 줄어도 json 은 그대로다.

    잎(자식 없는 끝마디)은 **부모의 방향을 물려받는다** — aim 할 대상이 없다.
    부모부터 내려가므로 그때 부모는 이미 정렬돼 있다.
    """
    done = 0
    for group in (doc.get("aim_subtrees") or []):
        root = _resolve(group["root"], namespace)
        if not root:
            messages.append("[Warning] {0}: not in the scene - subtree skipped.".format(
                group["root"]))
            continue

        hint = axis_vector(group["up_world"])
        nodes = descendants(root)          # 부모가 먼저 오는 순서
        if not nodes:
            messages.append("[Info] {0}: nothing under it.".format(
                su.short_name(root)))
            continue

        for node in nodes:
            if not _writable(node):
                results["skipped"] += 1
                messages.append("[Warning] {0}: rotation is locked or driven.".format(
                    su.short_name(node)))
                continue

            kids = cmds.listRelatives(node, children=True, type="joint") or []
            if kids:
                here = world_point(node)
                mat = basis_matrix(here, world_point(kids[0]) - here, hint,
                                   group["forward"], group["up"])
                if mat is None:
                    results["skipped"] += 1
                    continue
                set_world_orientation(node, mat)
            else:
                # 끝마디 - 부모 방향을 그대로
                parent = (cmds.listRelatives(node, parent=True, type="joint")
                          or [None])[0]
                if not parent:
                    continue
                set_world_orientation(node, om.MMatrix(
                    cmds.xform(parent, q=True, ws=True, m=True)))
            done += 1

        messages.append("[OK] {0} : {1} joint(s) under {2} aimed ({3} forward, "
                        "{4} -> world {5}).".format(
                            group.get("name", "subtree"), len(nodes),
                            su.short_name(root), group["forward"],
                            group["up"], group["up_world"]))
    return done


def _do_pole_chains(doc, namespace, results, messages):
    done = 0
    for chain in (doc.get("pole_chains") or []):
        names = chain["joints"]
        nodes = [_resolve(n, namespace) for n in names]
        pole = _resolve(chain.get("pole"), namespace) if chain.get("pole") else None

        if None in nodes or not pole:
            results["skipped"] += len(names)
            messages.append("[Warning] {0}: chain or pole target missing - skipped.".format(
                chain["name"]))
            continue

        pole_pos = world_point(pole)

        # IK 부분 : 끝 조인트는 건드리지 않는다 (계획서 2-1)
        for i in range(len(nodes) - 1):
            node = nodes[i]
            if not _writable(node):
                results["skipped"] += 1
                messages.append("[Warning] {0}: rotation is locked or driven.".format(
                    su.short_name(node)))
                continue
            here = world_point(node)
            fwd = world_point(nodes[i + 1]) - here
            mat = basis_matrix(here, fwd, pole_pos - here,
                               chain["forward"], chain["up"])
            if mat is None:
                results["skipped"] += 1
                continue
            set_world_orientation(node, mat)
            done += 1

        # 끝 조인트부터
        tail = chain.get("tail")
        end = nodes[-1]

        if tail == "preserve":
            results["preserved"] += 1
            messages.append(
                "[Info] {0}: '{1}' left exactly as it is (rotate/jointOrient "
                "untouched). Its world orientation follows the parent.".format(
                    chain["name"], su.short_name(end)))
        elif isinstance(tail, dict):
            done += _do_tail(tail, namespace, results, messages, chain["name"])

        dev = angle_between(world_axis_of(nodes[0], chain["up"]),
                            axis_vector(chain.get("expect_up_world") or "+Z"))
        messages.append("[OK] {0} : aimed at the pole - {1} deviates {2:.2f} deg from "
                        "world {3}.".format(chain["name"], chain["up"], dev,
                                            chain.get("expect_up_world") or "+Z"))
    return done


def _do_tail(tail, namespace, results, messages, label):
    done = 0
    names = tail["joints"]
    nodes = [_resolve(n, namespace) for n in names]
    hint = axis_vector(tail["up_world"])

    for i, node in enumerate(nodes):
        if not node:
            results["skipped"] += 1
            continue
        if not _writable(node):
            results["skipped"] += 1
            messages.append("[Warning] {0}: rotation is locked or driven.".format(
                su.short_name(node)))
            continue

        child = nodes[i + 1] if i + 1 < len(nodes) else None
        if not child:
            prev = nodes[i - 1] if i > 0 else None
            if prev:
                set_world_orientation(node, om.MMatrix(
                    cmds.xform(prev, q=True, ws=True, m=True)))
                done += 1
            continue

        here = world_point(node)
        mat = basis_matrix(here, world_point(child) - here, hint,
                           tail["forward"], tail["up"])
        if mat is None:
            results["skipped"] += 1
            continue
        set_world_orientation(node, mat)
        done += 1

    # forward 를 정확히 맞추면 up 은 그만큼 기운다 - 직교화의 결과다(계획서 2-7).
    # 체인이 수직에서 기운 만큼 그대로 남으므로, **감추지 않고 적는다.**
    first = next((n for n in nodes if n), None)
    if first:
        dev = angle_between(world_axis_of(first, tail["up"]),
                            axis_vector(tail["up_world"]))
        messages.append(
            "[OK] {0} tail : {1} is {2:.2f} deg off world {3} - that is how far the "
            "chain itself leans; aiming down the chain wins.".format(
                label, tail["up"], dev, tail["up_world"]))
    return done


def _do_pole_targets(doc, namespace, results, messages):
    """폴 타깃을 제 팔·다리에 **살아 있게 물린다**. 회전은 뒤에서 월드 0.

    배선은 `A00060_jointTool_V03` 의 `pole_target_manager.ensure()` 를 그대로 쓴다 —
    그 툴의 `Chain > Pole Target` 으로 만든 것과 **같은 구성**이어야 하기 때문이다.

    각 조인트에 **`poleDistance` 어트리뷰트**가 붙어 뷰포트에서 실시간으로 거리를
    맞출 수 있다.

    **이미 배선돼 있으면 거리 값을 안 건드린다** — 맞춰 둔 값이 실행할 때마다 json 값으로
    되돌아가면 실시간 조절이 무의미해진다. json 의 `distance` 는 **처음 만들 때만** 쓰고,
    되돌리려면 `reset_distance` 를 켠다.
    """
    group = doc.get("pole_targets") or {}
    entries = group.get("targets") or []
    if not entries:
        return 0

    distance = float(group.get("distance", 1.0))
    reset = bool(group.get("reset_distance", False))
    done = 0
    kept = []

    for entry in entries:
        node = _resolve(entry["name"], namespace)
        if not node:
            results["skipped"] += 1
            messages.append("[Warning] {0}: not in the scene - not placed.".format(
                entry["name"]))
            continue

        chain = [_resolve(n, namespace) for n in entry["chain"]]
        if None in chain:
            results["skipped"] += 1
            messages.append("[Warning] {0}: chain incomplete ({1}) - not placed.".format(
                su.short_name(node),
                ", ".join(n for n, r in zip(entry["chain"], chain) if not r)))
            continue

        # translate 가 구동되는지 여기서 미리 보지 않는다 — 두 번째 실행부터는
        # **우리가 건 컨스트레인트**가 몰고 있어서 전부 걸러져 버린다(실제로 물렸다).
        # 남의 컨스트레인트인지 우리 것인지는 `ensure()` 가 가른다.
        _pos, note = pt.solve(chain, distance)
        if note:
            messages.append("[Warning] {0}: {1}.".format(su.short_name(node), note))

        status, msgs = pt.ensure(node, chain, distance, reset_distance=reset)
        messages.extend(msgs)
        if status == "skipped":
            results["skipped"] += 1
            continue
        done += 1
        if status == "kept":
            kept.append(su.short_name(node))

    if kept:
        messages.append(
            "[Info] {0} pole target(s) kept the distance you dialled in ({1}). "
            "Set 'reset_distance' in the mapping file to force them back.".format(
                len(kept), ", ".join(kept)))
    messages.append(
        "[OK] {0} pole target(s) wired to their limb - each has a '{1}' attribute you "
        "can change in the viewport.".format(done, pt.DISTANCE_ATTR))
    return done


def _zero_pole_targets(doc, namespace, results, messages):
    """폴 타깃의 회전을 월드 0 으로. **방향 단계가 전부 끝난 뒤에** 돈다.

    위치는 일찍(A2 가 읽어야 하므로) 놓지만, 회전을 그때 0 으로 만들면 **소용이 없다** —
    폴 타깃은 `upperarm` · `thigh` 의 **자식**이라, 뒤이어 A2 가 부모를 돌리면 월드 회전이
    따라 움직인다(실측: `[170.27, 13.49, -2.29]`). 그래서 두 단계로 갈랐다.
    """
    done = 0
    for entry in ((doc.get("pole_targets") or {}).get("targets") or []):
        node = _resolve(entry["name"], namespace)
        if not node:
            continue
        if not _writable(node):
            results["skipped"] += 1
            messages.append("[Warning] {0}: rotation is locked or driven.".format(
                su.short_name(node)))
            continue
        world_zero(node)
        done += 1
    if done:
        messages.append("[OK] {0} pole target(s) set to world zero rotation.".format(done))
    return done


def _do_place(doc, namespace, results, messages):
    """조인트를 **자기 축 방향으로** 놓는다. 방향 단계가 전부 끝난 뒤에 돈다.

    `translate` 를 직접 쓴다 — 실측하면 `setAttr .translate`, `xform -os -t`,
    `move -r -os` 가 **모두 같은 결과**다(오브젝트 공간 이동 = translate 어트리뷰트).

    **이 단계 때문에 이 탭이 방향만이 아니라 위치까지 건드린다** — 그래서 이름이
    `Orient` 가 아니라 `Orient & Place` 다.
    """
    done = 0
    for group in (doc.get("place") or []):
        axis = group.get("axis", "+Z")
        dist = float(group.get("distance", 0.0))
        index, sign = parse_axis(axis)

        offset = [0.0, 0.0, 0.0]
        offset[index] = sign * dist

        for name in group["joints"]:
            node = _resolve(name, namespace)
            if not node:
                results["skipped"] += 1
                messages.append("[Warning] {0}: not in the scene - not placed.".format(
                    name))
                continue
            if su.blocked_channels(node, translate=True, rotate=False):
                results["skipped"] += 1
                messages.append(
                    "[Warning] {0}: translation is locked or driven - not placed.".format(
                        su.short_name(node)))
                continue
            try:
                if group.get("reset", True):
                    cmds.setAttr(node + ".translate", 0, 0, 0)
                cmds.xform(node, objectSpace=True, translation=offset)
                done += 1
            except Exception as e:
                results["skipped"] += 1
                messages.append("[ERR] {0}: {1}".format(su.short_name(node), e))

        messages.append("[OK] placed {0} joint(s) at {1} {2:g} in object space.".format(
            len(group["joints"]), axis, dist))
    return done


def _do_position_only(mirror, plane, namespace, results, messages):
    done = 0
    for entry in (mirror.get("position_only") or []):
        src = _resolve(entry["source"], namespace)
        dst = _resolve(entry["target"], namespace)

        if src and dst:
            want = mirror_point(world_point(src), plane)
            try:
                cmds.xform(dst, ws=True, t=(want.x, want.y, want.z))
            except Exception as e:
                messages.append("[ERR] {0}: {1}".format(su.short_name(dst), e))

        for node in (src, dst):
            if not node:
                results["skipped"] += 1
                continue
            if not _writable(node):
                results["skipped"] += 1
                messages.append("[Warning] {0}: rotation is locked or driven.".format(
                    su.short_name(node)))
                continue
            world_zero(node)
            done += 1

    if done:
        messages.append(
            "[OK] position-only joints : {0} mirrored and set to world zero.".format(done))
    return done
