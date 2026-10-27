# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00275_skinTool_V01 - Weights > Move 코어 (UI 비의존)
"""
조인트 **n 개(From) -> k 개(To)** 웨이트 이동. Kangaroo 플러그인 `SkinCluster > Move` 를 **플러그인 없이** 옮긴 것.
계획서 `docs/plans/A00275_skinTool_V01_move_n_to_k_plan.md`.

원본 (읽기 전용 참고, 저장소 밖):
  `0020_maya_plugin/0010_kangaroo/scripts/kangarooTabTools/weights.py` : `moveSkinClusterWeights()`
  `.../kangarooTools/xforms.py` : `findClosestJoints()`
  `.../kangarooTools/patch.py`  : `smoothValues2d()` · `getNeighborDataForSmoothing()` · `setSkinClusterWeights()`

--------------------------------------------------------------------------
알고리즘 (원본과 같다)
--------------------------------------------------------------------------
1) 버텍스마다 **가장 가까운 To 조인트** (조인트 -> 자식 조인트 선분까지 거리, 0.999 로 줄인 선분, `closest_targets`).
2) From 조인트마다 따로 : 그 웨이트를 최근접 To 에 주고 From 은 0.
3) k >= 2 면 To 사이 경계를 **선택 안 이웃만으로** `smooth_steps` 번 평균, 버텍스마다 옮기는 양의 합은 보존.
4) To 에 더한다.
5) 원래 웨이트와 섞는다 : Blend x 소프트 셀렉션 -> Joint Locks -> Border Edges 마스크 (원본 `setSkinClusterWeights` 순서).

From 마다 따로 도는 것이 중요하다 - 3) 의 합 보존 때문에 From 을 먼저 더해 한 번에 스무딩하면 결과가 다르다.
1) 은 From 과 무관하므로 한 번만 구한다(원본은 매번 다시 구한다 - 결과 같음).

From 이 웨이트를 갖지 않은 버텍스는 3) 의 "합 0" 때문에 그대로다 - **From 이 영향을 미치는 범위만 바뀐다.**

이 툴이 더한 것 (사용자 요청 2026-10-27)
  - `respect_selection` : 켜면(기본) 버텍스를 고른 경우 그 버텍스만, 끄면 컴포넌트를 골랐어도 메시 전체.
  - `use_soft_selection` : 소프트 셀렉션 falloff 를 섞는 비율로 (원본은 늘 켬).

웨이트 쓰기는 Smooth 와 같이 **구간 setAttr**(undo 됨). numpy 가 있으면 numpy, 없으면 같은 식의 순수 파이썬.
"""

import math
import time

import maya.cmds as cmds

from Framework.core import maya_skin

from .skin_weights_common import (  # noqa: F401  (상수는 UI 가 이 모듈에서 읽는다)
    LOCKS_IGNORE,
    LOCKS_KEEP,
    LOCKS_ONLY_ADD,
    LOCKS_ONLY_REMOVE,
    LOCK_MODES,
    BORDER_ALL,
    BORDER_IGNORE,
    BORDER_ONLY,
    BORDER_MODES,
    _leaf,
    skin_clusters,
    _shape_dag,
    _vertex_count,
    parse_selection,
    connected_vertices,
    border_mask,
    _read_weights,
    _write_weights,
    _lock_columns,
    _apply_locks_row,
)

try:
    import numpy as np
except Exception:                                          # noqa: BLE001
    np = None


# 조인트 선분 - 값까지 kangaroo `weights.JointLines` 와 같다.
JOINT_LINES_NO = 0              # 조인트 점까지 거리
JOINT_LINES_YES = 1             # 조인트 -> 자식 조인트 선분 (자식은 To 목록에 든 것만)
JOINT_LINES_ALL_CHILDREN = 2    # 자식이 To 목록 밖이어도

JOINT_LINE_MODES = (JOINT_LINES_NO, JOINT_LINES_YES, JOINT_LINES_ALL_CHILDREN)

#: 원본 상수들
LINE_LENGTH_FACTOR = 0.999      # 선분 끝을 줄인다 - 자식 조인트 자리에서는 자식 쪽이 이기게
MIN_CHILD_DISTANCE = 0.00001    # 자식과 이보다 가까우면 선분을 만들지 않는다
ZERO_WEIGHT = 0.00000001        # 이 아래 웨이트는 0 으로 본다(_removeZeroInfluencesNumpy)
SQUASH_ATTR = "skinParent"      # bProjectSquashToMainJoints - Kangaroo 리그의 squash 조인트


# ==================================================================
# 1) 최근접 To 조인트 (kangaroo xforms.findClosestJoints)
# ==================================================================

def _project_joints(joints, project_squash):
    """`skinParent` 문자열 어트리뷰트가 가리키는 조인트로 바꾼다(원본 sProjectAttrs)."""
    out = list(joints)
    if not project_squash:
        return out
    for index, joint in enumerate(out):
        plug = "{0}.{1}".format(joint, SQUASH_ATTR)
        if cmds.objExists(plug):
            parent = cmds.getAttr(plug)
            if parent and parent not in out and cmds.objExists(parent):
                out[index] = parent
    return out


def _joint_lines(joints, joint_lines):
    """(조인트 위치들, 조인트마다 [(A, 자식 위치), ...]). 선분이 없으면 []. 0.999 단축은 계산하는 쪽에서 원본 식대로."""
    positions = [tuple(cmds.xform(j, q=True, ws=True, t=True)) for j in joints]
    if joint_lines == JOINT_LINES_NO:
        return positions, [[] for _ in joints]
    in_list = set(cmds.ls(joints, long=True) or [])
    lines = []
    for index, joint in enumerate(joints):
        children = cmds.listRelatives(joint, children=True, type="joint", fullPath=True) or []
        if children and joint_lines != JOINT_LINES_ALL_CHILDREN:
            children = [c for c in children if c in in_list]
        own = []
        ax, ay, az = positions[index]
        for child in children:
            bx, by, bz = cmds.xform(child, q=True, ws=True, t=True)
            if math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2) <= MIN_CHILD_DISTANCE:
                continue
            own.append(((ax, ay, az), (bx, by, bz)))
        lines.append(own)
    return positions, lines


def closest_targets(points, joints, joint_lines=JOINT_LINES_YES, project_squash=True):
    """점마다 가장 가까운 조인트 인덱스 (k = 1 이면 전부 0)."""
    if len(joints) <= 1:
        return [0] * len(points)
    projected = _project_joints(joints, project_squash)
    positions, lines = _joint_lines(projected, joint_lines)
    if np is not None:
        return _closest_numpy(points, positions, lines)
    return _closest_python(points, positions, lines)


def _closest_python(points, positions, lines):
    out = []
    for px, py, pz in points:
        best, best_d = 0, None
        for j, (jx, jy, jz) in enumerate(positions):
            if lines[j]:
                dist = None
                for (ax, ay, az), (cx0, cy0, cz0) in lines[j]:
                    vx, vy, vz = cx0 - ax, cy0 - ay, cz0 - az
                    full = math.sqrt(vx * vx + vy * vy + vz * vz)
                    dx, dy, dz = vx / full, vy / full, vz / full
                    length = full * LINE_LENGTH_FACTOR
                    bx = ax + vx * LINE_LENGTH_FACTOR
                    by = ay + vy * LINE_LENGTH_FACTOR
                    bz = az + vz * LINE_LENGTH_FACTOR
                    t = ((px - ax) * dx + (py - ay) * dy + (pz - az) * dz) / length
                    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                    cx = ax * (1 - t) + bx * t
                    cy = ay * (1 - t) + by * t
                    cz = az * (1 - t) + bz * t
                    d = math.sqrt((cx - px) ** 2 + (cy - py) ** 2 + (cz - pz) ** 2)
                    if dist is None or d < dist:
                        dist = d
            else:
                dist = math.sqrt((jx - px) ** 2 + (jy - py) ** 2 + (jz - pz) ** 2)
            if best_d is None or dist < best_d:
                best, best_d = j, dist
        out.append(best)
    return out


def _closest_numpy(points, positions, lines):
    """원본 numpy 식 그대로 (같은 연산 순서 - 동률일 때도 같은 조인트가 나오게)."""
    aPoints = np.array(points, dtype="float64").reshape(-1, 3)
    aJoints = np.array(positions, dtype="float64")
    n_points, n_joints = len(aPoints), len(aJoints)
    aClosest = np.repeat(aJoints[np.newaxis, :], n_points, axis=0).reshape(n_points, n_joints, 3)

    starts, ends, mapper = [], [], []
    for j, own in enumerate(lines):
        mapper.append(len(starts) if own else -1)
        for a, b in own:
            starts.append(a)
            ends.append(b)
    if starts:
        A = np.array(starts, dtype="float64")
        B_full = np.array(ends, dtype="float64")
        # 원본: 방향 = (자식 - A) / 길이, 길이 *= 0.999, B = A + 벡터 * 0.999
        vectors = B_full - A
        lengths = np.linalg.norm(vectors, axis=-1)
        directions = vectors / lengths[:, np.newaxis]
        lengths = lengths * LINE_LENGTH_FACTOR
        B = A + vectors * LINE_LENGTH_FACTOR
        n_lines = len(A)
        rep = np.repeat(aPoints, n_lines, axis=0).reshape(n_points, n_lines, 3)
        ts = np.sum((rep - A) * directions.reshape(1, n_lines, 3), axis=-1) / lengths
        ts = np.clip(ts, 0, 1).reshape(n_points, n_lines, 1)
        closest_lines = A[np.newaxis] * (1 - ts) + B[np.newaxis] * ts
        for j in range(n_joints):
            start = mapper[j]
            if start == -1:
                continue
            stop = n_lines
            for k in range(j + 1, n_joints):
                if mapper[k] != -1:
                    stop = mapper[k]
                    break
            block = closest_lines[:, start:stop]
            dists = np.linalg.norm(block - rep[:, start:stop], axis=-1)
            pick = np.argmin(dists, axis=-1)
            aClosest[:, j] = block[np.arange(n_points), pick]
    per_joint = np.repeat(aPoints, n_joints, axis=0).reshape(n_points, n_joints, 3)
    distances = np.linalg.norm(aClosest - per_joint, axis=-1)
    return [int(i) for i in np.argmin(distances, axis=1)]


# ==================================================================
# 2) ~ 4) 분배 + 스무딩 (kangaroo smoothValues2d, 선택 안 이웃만)
# ==================================================================

def smooth_columns(columns, neighbor_rows, iterations):
    """columns : k 개 리스트(행 = 선택 버텍스 순서). neighbor_rows : 행마다 [자기, 이웃 행...].

    `new[r] = Σ old[nbr] / len(nbr)` 를 iterations 번 (Jacobi). 새 리스트를 돌려준다.
    """
    if np is not None:
        if not columns or not columns[0]:
            return [list(c) for c in columns]
        values = np.array(columns, dtype="float64").T                     # 행 x k
        values = np.concatenate([values, np.zeros((1, values.shape[1]))])  # 패딩 행
        pad = len(columns[0])
        width = max(len(n) for n in neighbor_rows)
        table = np.full((len(neighbor_rows), width), pad, dtype=int)
        for r, nbr in enumerate(neighbor_rows):
            table[r, :len(nbr)] = nbr
        denom = (1.0 / np.array([len(n) for n in neighbor_rows], dtype="float64"))[:, np.newaxis]
        rows = np.arange(len(neighbor_rows))
        for _ in range(iterations):
            values[rows] = np.sum(values[table], axis=1) * denom
        return [list(col) for col in values[:-1].T]
    out = [list(c) for c in columns]
    for _ in range(iterations):
        new = []
        for col in out:
            new.append([sum(col[n] for n in nbr) / float(len(nbr)) for nbr in neighbor_rows])
        out = new
    return out


def distribute(rows, col_from, cols_to, closest, smooth_steps, neighbor_rows, before):
    """From 열 하나를 To 열들로 (원본 루프 한 바퀴). rows 를 제자리에서 바꾼다.

    before : 이동 전 웨이트 행(원본 aWeightsSwappedBefore) - From 들이 서로의 결과를 보지 않게.
    """
    k = len(cols_to)
    n = len(rows)
    sets = [[0.0] * n for _ in range(k)]
    for r in range(n):
        value = before[r][col_from]
        sets[closest[r]][r] += value
        rows[r][col_from] -= value
    if k > 1 and smooth_steps > 0:
        sums_before = [sum(sets[i][r] for i in range(k)) for r in range(n)]
        sets = smooth_columns(sets, neighbor_rows, smooth_steps)
        for r in range(n):
            after = sum(sets[i][r] for i in range(k))
            scale = sums_before[r] * (1.0 / (after if after != 0 else 1.0))
            for i in range(k):
                sets[i][r] *= scale
    for i, col in enumerate(cols_to):
        for r in range(n):
            rows[r][col] += sets[i][r]


# ==================================================================
# 섬 검사
# ==================================================================

def count_islands(ids, neighbors):
    """선택 버텍스가 몇 덩어리로 나뉘는지 (선택 안 엣지로만 잇는다)."""
    wanted = set(ids)
    seen = set()
    islands = 0
    for start in ids:
        if start in seen:
            continue
        islands += 1
        stack = [start]
        seen.add(start)
        while stack:
            v = stack.pop()
            for nb in neighbors[v]:
                if nb in wanted and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return islands


# ==================================================================
# 진입점
# ==================================================================

def _resolve_joints(names, label, messages):
    """존재하는 조인트만 풀패스로, 순서 유지 · 중복 제거."""
    out = []
    for name in names:
        found = cmds.ls(name, long=True, type="joint") or []
        if not found:
            messages.append("[WARN] {0} : '{1}' is not a joint in the scene - ignored.".format(label, name))
            continue
        if found[0] not in out:
            out.append(found[0])
    return out


def move_weights(joints_from, joints_to, smooth_steps=5, blend=1.0, joint_lines=JOINT_LINES_YES,
                 joint_locks=LOCKS_IGNORE, border_edges=BORDER_ALL, border_mask_steps=2,
                 respect_selection=True, use_soft_selection=True, project_squash=True,
                 island_check=True, confirm=None, targets=None):
    """선택 메시(들)에서 joints_from(n) 의 웨이트를 joints_to(k) 로 옮긴다. `(바뀐 메시 수, 메시지 목록)`.

    confirm : 섬이 여럿일 때 부를 콜백(질문 문자열 -> bool). None 이면 묻지 않고 진행한다.
    targets : 주면 선택 대신 그것을 쓴다(`[{"mesh", "ids", "softs"}]`, 테스트 · 스크립트용).
    씬을 바꾸는 부분은 호출부(UI)가 `undo_chunk()` 안에서 부른다.
    """
    messages = []
    if joint_locks not in LOCK_MODES:
        raise ValueError("Unknown joint lock mode: {0}".format(joint_locks))
    if border_edges not in BORDER_MODES:
        raise ValueError("Unknown border mode: {0}".format(border_edges))
    if joint_lines not in JOINT_LINE_MODES:
        raise ValueError("Unknown joint line mode: {0}".format(joint_lines))
    smooth_steps = max(0, int(smooth_steps))
    blend = min(1.0, max(0.0, float(blend)))

    froms = _resolve_joints(joints_from, "From", messages)
    tos = _resolve_joints(joints_to, "To", messages)
    if not froms or not tos:
        return 0, messages + ["[WARN] Fill both the From and the To joint lists."]
    overlap = [j for j in froms if j in tos]
    if overlap:
        messages.append("[Info] {0} joint(s) are in both lists ({1}) - their own weights are shared out among "
                        "the To joints as well (same as Kangaroo).".format(
                            len(overlap), ", ".join(_leaf(j) for j in overlap)))

    if targets is None:
        targets = parse_selection(use_soft_selection=use_soft_selection)
    if not targets:
        return 0, messages + ["[WARN] Select a skinned mesh (or some of its vertices) first."]
    if not respect_selection:
        targets = [{"mesh": t["mesh"], "ids": None, "softs": None} for t in targets]
    if blend <= 0.0:
        return 0, messages + ["[WARN] Blend is 0 - the result would be the current weights."]
    if np is None:
        messages.append("[Info] numpy was not found - using the slower pure Python path.")

    done = 0
    for target in targets:
        mesh = target["mesh"]
        started = time.time()
        skins = skin_clusters(mesh)
        if not skins:
            messages.append("[SKIP] {0} has no skinCluster.".format(_leaf(mesh)))
            continue
        skin = skins[0]
        try:
            dag = _shape_dag(mesh, skin)
        except Exception as exc:                           # noqa: BLE001
            messages.append("[FAIL] {0} : {1}".format(_leaf(mesh), exc))
            continue
        total = _vertex_count(dag)
        ids = target.get("ids")
        ids = list(range(total)) if ids is None else sorted(i for i in set(ids) if 0 <= i < total)
        if not ids:
            messages.append("[SKIP] {0} : no vertices.".format(_leaf(mesh)))
            continue
        neighbors = connected_vertices(dag)

        # 1) 섬 검사 (원본: 컴포넌트 선택이 섬 2 개 이상이면 묻는다)
        if island_check and len(ids) != total:
            islands = count_islands(ids, neighbors)
            if islands > 1 and confirm is not None:
                if not confirm("The selection on {0} is split into {1} islands. Continue?".format(
                        _leaf(mesh), islands)):
                    messages.append("[SKIP] {0} : stopped at the island check.".format(_leaf(mesh)))
                    continue

        # 2) From 거르기 - 인플루언스이고 선택 범위에 웨이트가 있는 것만
        fn = maya_skin.skin_fn(skin)
        influences = [d.fullPathName() for d in fn.influenceObjects()]
        weights, width = _read_weights(fn, dag, ids)
        col_of = dict((name, c) for c, name in enumerate(influences))
        live_from = []
        for joint in froms:
            col = col_of.get(joint)
            if col is None:
                messages.append("[SKIP] {0} : From '{1}' is not an influence.".format(_leaf(mesh), _leaf(joint)))
                continue
            if not any(weights[r * width + col] >= ZERO_WEIGHT for r in range(len(ids))):
                messages.append("[SKIP] {0} : From '{1}' has no weight here.".format(_leaf(mesh), _leaf(joint)))
                continue
            live_from.append(joint)
        if not live_from:
            messages.append("[SKIP] {0} : no From joint has weight in the selection.".format(_leaf(mesh)))
            continue

        # 3) To 가 인플루언스가 아니면 weight 0 으로 더한다
        added = []
        for joint in tos:
            if joint not in col_of:
                cmds.skinCluster(skin, edit=True, addInfluence=joint, weight=0.0)
                added.append(_leaf(joint))
        if added:
            messages.append("[Info] {0} : added {1} as influence(s) (weight 0).".format(
                _leaf(mesh), ", ".join(added)))
            fn = maya_skin.skin_fn(skin)
            influences = [d.fullPathName() for d in fn.influenceObjects()]
            weights, width = _read_weights(fn, dag, ids)
            col_of = dict((name, c) for c, name in enumerate(influences))

        # 4) 웨이트 행 (원본은 1e-8 미만을 0 으로 본다 - 쓰는 값에는 영향 없음)
        rows = [weights[r * width:(r + 1) * width] for r in range(len(ids))]
        old = [list(row) for row in rows]
        before = [list(row) for row in rows]

        # 5) 최근접 To - 지금 변형된 메시의 월드 좌표. 원본과 **같은 명령**(xform vtx[*] ws)으로 읽는다 -
        #    MFnMesh.getPoints 와는 마지막 자리가 달라서, 두 To 와 거리가 정확히 같은 버텍스(대칭 메시)에서
        #    고르는 조인트가 갈렸다(원통 Joint Lines = points 에서 0.30 차이, 2026-10-27).
        flat = cmds.xform("{0}.vtx[*]".format(dag.fullPathName()), q=True, ws=True, t=True)
        points = [(flat[3 * v], flat[3 * v + 1], flat[3 * v + 2]) for v in ids]
        closest = closest_targets(points, tos, joint_lines, project_squash)

        # 6) 선택 안 이웃 표 (원본 bIncludeNeighborsNotInIds=False, 자기 포함)
        row_of = dict((v, r) for r, v in enumerate(ids))
        neighbor_rows = [[r] + [row_of[nb] for nb in neighbors[v] if nb in row_of] for r, v in enumerate(ids)]

        cols_to = [col_of[j] for j in tos]
        for joint in live_from:
            distribute(rows, col_of[joint], cols_to, closest, smooth_steps, neighbor_rows, before)

        # 7) 섞기 - Blend x 소프트 -> Joint Locks -> Border (원본 setSkinClusterWeights 순서)
        softs = target.get("softs") if use_soft_selection else None
        locked, free = _lock_columns(fn)
        if joint_locks != LOCKS_IGNORE and not locked:
            messages.append("[Info] {0} : no influence is locked - the Joint Locks option changes nothing.".format(
                _leaf(mesh)))
        mask = None
        if border_edges != BORDER_ALL:
            mask = border_mask(dag, steps=border_mask_steps, invert=(border_edges == BORDER_ONLY),
                               neighbors=neighbors)
        final = []
        for r, vertex in enumerate(ids):
            factor = blend * (float(softs.get(vertex, 1.0)) if softs else 1.0)
            row = rows[r]
            base = old[r]
            if factor != 1.0:
                row = [base[c] + (row[c] - base[c]) * factor for c in range(width)]
            if joint_locks != LOCKS_IGNORE and locked:
                row = _apply_locks_row(list(row), base, locked, free, joint_locks)
            if mask is not None:
                m = mask[vertex]
                row = [base[c] * (1.0 - m) + row[c] * m for c in range(width)]
            final.append(row)

        changed = [r for r in range(len(ids)) if any(abs(final[r][c] - old[r][c]) > 1e-12 for c in range(width))]
        _write_weights(skin, fn, [ids[r] for r in changed], [final[r] for r in changed])
        done += 1
        messages.append("[OK] {0} : moved {1} -> {2} joint(s), {3} of {4} vertices changed{5} ({6:.2f}s).".format(
            _leaf(mesh), len(live_from), len(tos), len(changed), len(ids),
            " (soft)" if softs else "", time.time() - started))

    if not done and not any(m.startswith("[OK]") for m in messages):
        messages.append("[WARN] Nothing was moved.")
    return done, messages


# ==================================================================
# Kangaroo 엔진 (플러그인이 로드돼 있을 때)
# ==================================================================

def move_weights_kangaroo(joints_from, joints_to, smooth_steps=5, blend=1.0, joint_lines=JOINT_LINES_YES,
                          joint_locks=LOCKS_IGNORE, border_edges=BORDER_ALL, border_mask_steps=2,
                          respect_selection=True, use_soft_selection=True, project_squash=True,
                          island_check=True):
    """같은 옵션으로 kangaroo `moveSkinClusterWeights` 를 부른다. `(성공 여부, 메시지 목록)`."""
    try:
        import kangarooTabTools.weights as ktw
        import kangarooTools.patch as ktpatch
    except Exception:                                      # noqa: BLE001
        return 0, ["[FAIL] Kangaroo plugin not importable (kangarooTabTools) - load it or switch the "
                   "engine to 'Native'."]
    froms = [_leaf(j) for j in joints_from]
    tos = [_leaf(j) for j in joints_to]
    if not froms or not tos:
        return 0, ["[WARN] Fill both the From and the To joint lists."]
    x_joints = {repr(froms): repr(tos)}

    selection = cmds.ls(sl=True, long=True) or []
    soft_before = cmds.softSelect(q=True, softSelectEnabled=True)
    try:
        if not respect_selection:
            meshes = sorted({item.split(".")[0] for item in selection})
            cmds.select(meshes, replace=True)
        if not use_soft_selection and soft_before:
            cmds.softSelect(softSelectEnabled=False)
        ktw.moveSkinClusterWeights(
            xJoints=x_joints, iSmoothSteps=smooth_steps, fBlend=blend, iJointLines=joint_lines,
            iJointLocks=joint_locks, iBorderEdges=border_edges, iSmoothBorderMask=border_mask_steps,
            bDisableIslandCheck=not island_check, bProjectSquashToMainJoints=project_squash,
            iCheckMissingInfluences=ktpatch.MissingInfluencesOptions.onlyAddMissingInfluencesInSkinCluster)
    except Exception as exc:                               # noqa: BLE001
        return 0, ["[FAIL] Kangaroo move failed : {0}".format(exc)]
    finally:
        if not use_soft_selection and soft_before:
            cmds.softSelect(softSelectEnabled=True)
        if not respect_selection and selection:
            cmds.select(selection, replace=True)
    return 1, ["[OK] [kangaroo] moved {0} -> {1} joint(s) on the selection.".format(len(froms), len(tos))]
