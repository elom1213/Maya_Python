# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00275_skinTool_V01 - Weights > Smooth 코어 (UI 비의존)
"""
Kangaroo 플러그인 `SkinCluster > Smooth` 를 **플러그인 없이** 옮긴 것.

원본 (읽기 전용 참고, 저장소 밖):
  `0020_maya_plugin/0010_kangaroo/scripts/kangarooTabTools/weights.py` : `smoothSkinWeights()`
  `.../kangarooTools/patch.py` : `getNeighborDataForSmoothing()` · `getNeighbors()` ·
                                 `getBorderMask()` · `smoothValues2d()` · `_applyJointLocks()` ·
                                 `setSkinClusterWeights()` (블렌드 · 소프트 · 보더 마스크)

--------------------------------------------------------------------------
알고리즘 (원본과 같다)
--------------------------------------------------------------------------
선택한 버텍스마다 **자기 + 엣지로 이어진 이웃**의 웨이트를 단순 평균해서 자기 웨이트로 삼고,
그것을 `Iterations` 번 되풀이한다.

    new[v] = ( w[v] + sum(w[nb]) ) / (1 + 이웃 수)

- **이웃은 선택 밖에 있어도 읽는다**(원본 `bIncludeNeighborsNotInIds=True`). 선택한 버텍스만
  값이 바뀌고, 선택 경계 밖 이웃은 참고만 된다 - 그래서 선택 덩어리의 가장자리가 튀지 않는다.
- 한 번의 iteration 안에서는 **전부 옛 값으로** 계산한다(Jacobi). 버텍스 순서에 결과가 달라지지
  않게 하려면 이래야 한다.
- 입력 행이 합 1 이면 평균도 합 1 이다 - 그래서 **따로 정규화하지 않는다**(Rigid 만 예외).

옵션 (전부 원본 인자와 1:1)

| 이 툴 | 원본 인자 | 하는 일 |
|-------|-----------|---------|
| Iterations | `iIterations` | 위 평균을 몇 번 |
| Blend | `fBlend` | 결과를 원래 웨이트와 섞는 비율(0 이면 아무 일도 없음) |
| Rigid | `fRigid` | 이웃 몫을 `1 + Rigid*0.25` 제곱한 뒤 다시 정규화 - **약한 몫이 더 깎인다** (약한 인플루언스가 번져 드는 것을 줄여 딱딱하게 유지). 몫이 전부 같으면 제자리다 |
| Keep Value One | `bKeepValueOne` | 웨이트가 1 인 버텍스(완전히 한 조인트) 는 건드리지 않는다 |
| Joint Locks | `iJointLocks` | 잠긴 조인트를 어떻게 다룰지 4 가지 |
| Border Edges | `iBorderEdges` | 열린 경계를 빼고 / 경계만 |
| Border Mask Steps | `iSmoothBorderMask` | 그 경계 마스크를 몇 칸 번지게 할지 |
| Loop Curve | `sLoopCurve` | 커브에 붙은 버텍스는 **루프를 가로지르는 쪽으로만** 평균 (입술 · 눈꺼풀 루프의 결을 지킨다 - 아래 `loop_neighbors` 참고) |
| Use Soft Selection | (원본은 항상 켬) | 소프트 셀렉션 falloff 를 섞는 비율로 |
| SkinCluster | `sChooseSkinCluster` | 메시에 skinCluster 가 여럿일 때 어느 것 |

원본에 있으나 옮기지 않은 것 : `bBarycentricWeighted`(원본 주석이 실험 중이라고 적어 둔 경로 -
이웃 4 개를 면으로 보고 자기 몫을 0.5 로 박아 둔다) · `xDistanceMeshes` · `sSphereMasks` ·
`xClosestToCurve`(SkinCluster 탭 전체가 공유하는 마스크들로, Smooth 만의 것이 아니고
kangaroo 의 `kt_findClosestPoints` 플러그인 명령과 세팅 노드를 필요로 한다).

--------------------------------------------------------------------------
★ 웨이트 쓰기는 API 가 아니라 구간 `setAttr`
--------------------------------------------------------------------------
`MFnSkinCluster.setWeights` 는 **undo 기록에 남지 않는다**(같은 저장소 `weight_layer_manager`
머리말 참고). 스무딩은 "조금 돌려 보고 Ctrl+Z" 를 반복하는 기능이라 undo 가 없으면 쓸 수 없다.
그래서 **바뀌는 버텍스만** `weightList[v].weights[lo:hi]` 구간으로 쓴다. 읽기는 API(bulk) 다.

--------------------------------------------------------------------------
numpy
--------------------------------------------------------------------------
있으면 numpy 로 돌고(원본도 numpy 다), 없으면 **같은 식의 순수 파이썬 경로**로 돈다.
두 경로의 결과가 같은지는 테스트로 고정했다. 순수 파이썬은 큰 메시 전체에서 느리므로
로그에 그 사실을 적는다.
"""

import time

import maya.cmds as cmds

from Framework.core import maya_skin

try:
    import numpy as np
except Exception:                                          # noqa: BLE001
    np = None


# v01.37 - 공용 함수는 skin_weights_common 으로 옮겼다(Move 탭과 공유). 이름 그대로 다시 내보낸다.
from .skin_weights_common import (  # noqa: F401
    LOCKS_IGNORE,
    LOCKS_KEEP,
    LOCKS_ONLY_ADD,
    LOCKS_ONLY_REMOVE,
    LOCK_MODES,
    BORDER_ALL,
    BORDER_IGNORE,
    BORDER_ONLY,
    BORDER_MODES,
    _long,
    _leaf,
    mesh_transform,
    skin_clusters,
    _shape_dag,
    _vertex_count,
    _component_ids,
    _soft_of,
    parse_selection,
    connected_vertices,
    border_flags,
    border_mask,
    _read_weights,
    _write_weights,
    _lock_columns,
    _apply_locks_row,
)

#: 이 값을 넘는 웨이트를 "1 인 버텍스" 로 본다(원본과 같은 값).
KEEP_ONE_EPS = 0.9999

#: Rigid 지수. 원본 `fPower = 1.0 + fRigid * 0.25`.
#: 0~1 사이 수를 1 보다 큰 지수로 올리면 **작은 수가 비율상 더 많이 깎인다** -
#: 그래서 약한 이웃 몫이 줄고, 지배적인 인플루언스가 남는다. 몫이 전부 같은
#: 자리(격자 안쪽 등)에서는 정규화로 되돌아와 **값이 그대로다**(테스트로 고정).
RIGID_POWER_SCALE = 0.25


# ==================================================================
# Loop Curve (커브를 따라 한 줄로만)
# ==================================================================

def orig_shape(mesh):
    """디포머 앞의 원본(intermediate) 셰이프. 없으면 보이는 셰이프.

    kangaroo `patch.getOrigShape()` 와 같다 - 버텍스 수가 같은 intermediate 셰이프를 고른다.
    Loop Curve 의 최근접 버텍스를 **rest 자리**에서 찾기 위한 것이다(포즈된 리그에서도 같은
    버텍스가 잡힌다).
    """
    transform = mesh_transform(mesh)
    shapes = cmds.listRelatives(transform, s=True, f=True) or []
    visible = cmds.listRelatives(transform, s=True, ni=True, f=True) or []
    hidden = [s for s in shapes if s not in visible]
    if hidden:
        count = cmds.polyEvaluate(transform, vertex=True)
        for shape in hidden:
            try:
                if cmds.polyEvaluate(shape, vertex=True) == count:
                    return shape
            except Exception:                              # noqa: BLE001
                continue
    return shapes[0] if shapes else transform


def _points_of(shape):
    """셰이프의 월드 좌표 [(x, y, z), ...]."""
    flat = cmds.xform("{0}.vtx[*]".format(shape), q=True, ws=True, t=True) or []
    return [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]


def _curve_points(curve):
    """커브(또는 아무 트랜스폼)의 월드 좌표 목록.

    NURBS 커브면 CV 를, 그 밖의 노드면 피벗 한 점을 쓴다.
    """
    shapes = cmds.listRelatives(curve, s=True, ni=True, f=True) or [curve]
    for shape in shapes:
        if cmds.objExists(shape) and cmds.objectType(shape) == "nurbsCurve":
            flat = cmds.xform("{0}.cv[*]".format(shape), q=True, ws=True, t=True) or []
            return [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
    return [tuple(cmds.xform(curve, q=True, ws=True, t=True))]


def _closest_vertices(mesh, points):
    """점마다 가장 가까운 **rest 자리** 버텍스 id (중복 제거, 순서 유지)."""
    verts = _points_of(orig_shape(mesh))
    if not verts or not points:
        return []

    found = []
    if np is not None:
        aVerts = np.array(verts, dtype="float64")
        aPoints = np.array(points, dtype="float64")
        for point in aPoints:
            diff = aVerts - point
            found.append(int(np.argmin(np.einsum("ij,ij->i", diff, diff))))
    else:
        for px, py, pz in points:
            best = None
            best_d = None
            for index, (vx, vy, vz) in enumerate(verts):
                dist = (vx - px) ** 2 + (vy - py) ** 2 + (vz - pz) ** 2
                if best_d is None or dist < best_d:
                    best, best_d = index, dist
            found.append(best)

    out = []
    for index in found:
        if index is not None and index not in out:
            out.append(index)
    return out


def loop_neighbors(mesh, dag, ids, loop_curve, neighbors):
    """Loop Curve 가 집은 버텍스의 이웃 목록을 **자기 체인 안으로** 제한한다.

    kangaroo `patch.getNeighbors(sLoopCurve=...)` 를 그대로 옮긴 것이다.

      1) 커브의 점(CV)마다 가장 가까운 버텍스를 찾아 **씨앗**으로 삼고, 씨앗마다
         **자기 번호를 라벨**로 붙인다.
      2) 라벨을 이웃으로 번지게 한다. 갈림길(라벨 없는 이웃이 둘 이상)이 나오면 그 자리에서
         멈춘다 - 한 줄로 이어질 때만 계속 간다.
      3) 번진 버텍스의 이웃 목록은 **"라벨이 같거나 아직 라벨 없는"** 이웃들만 남는다.

    ★ **그래서 루프를 "따라" 가 아니라 루프를 "가로질러" 평균된다.** 커브가 루프의 버텍스를
    촘촘히 집으면(보통 그렇다) 루프 위의 이웃들은 **서로 다른 라벨**이라 3) 에서 빠지고,
    남는 것은 루프에서 **벗어나는 쪽 이웃**뿐이다. 입술 · 눈꺼풀 라인에서 라인 방향의 결
    (구석 -> 가운데 그라데이션)은 그대로 두고 **라인을 넘는 쪽만 풀고 싶을 때** 쓰는 옵션이다.
    확인: 5x5 격자의 가운데 행을 커브로 집으면 그 행 버텍스의 이웃이 위/아래 행 둘로 바뀐다.

    커브 대신 **버텍스 id 목록**을 줘도 된다(원본도 받는다). 씨앗을 하나만 주면 갈림길이 없는
    한 줄(스트랜드) 위에서 체인이 자란다 - 격자에서는 첫 걸음에서 갈림길이라 멈춘다.

    돌려주는 것은 `{vertex id: [이웃, ...]}` - 여기 없는 버텍스는 평소 이웃을 그대로 쓴다.
    """
    if isinstance(loop_curve, (list, tuple, set)):
        seeds = [int(i) for i in loop_curve]
    else:
        if not cmds.objExists(loop_curve):
            raise ValueError('Loop Curve "{0}" does not exist.'.format(loop_curve))
        seeds = _closest_vertices(mesh, _curve_points(loop_curve))

    if not seeds:
        return {}

    total = _vertex_count(dag)
    labels = [-1] * total
    for seed in seeds:
        if 0 <= seed < total:
            labels[seed] = seed

    wanted = set(ids)
    restricted = {}
    frontier = [s for s in seeds if 0 <= s < total]

    for step in range(total):
        if not frontier:
            break
        following = []
        for index in frontier:
            label = labels[index]
            connected = neighbors[index]
            valid = [c for c in connected if labels[c] in (label, -1)]
            unused = [c for c in connected if labels[c] == -1]
            if not valid:
                continue
            # 첫 걸음에서는 갈림길을 허용한다(씨앗은 양쪽으로 퍼져야 한다).
            if step == 0 or len(unused) == 1:
                for candidate in valid:
                    if labels[candidate] == -1:
                        labels[candidate] = label
                        following.append(candidate)
                if index in wanted:
                    restricted[index] = valid
        frontier = following

    return restricted


# ==================================================================
# 스무딩 (numpy / 순수 파이썬 두 경로, 같은 식)
# ==================================================================


def _smooth_python(weights, width, nbs, sizes, targets, iterations, power,
                   keep_one, locked, free, lock_mode):
    """순수 파이썬 경로. `weights` 는 flat list, 마지막 행은 패딩(0)."""
    old = list(weights)
    keep_rows = set()
    if keep_one:
        for row in targets:
            base = row * width
            if max(weights[base:base + width]) > KEEP_ONE_EPS:
                keep_rows.add(row)

    for _ in range(max(0, int(iterations))):
        updated = []
        for order, row in enumerate(targets):
            denom = 1.0 / sizes[order]
            acc = [0.0] * width
            for nb in nbs[order]:
                base = nb * width
                for column in range(width):
                    value = weights[base + column] * denom
                    if power:
                        value = value ** power
                    acc[column] += value
            if power:
                total = sum(acc)
                if total < 1e-5:
                    total = 1.0
                acc = [value / total for value in acc]
            updated.append(acc)

        for order, row in enumerate(targets):
            base = row * width
            if row in keep_rows:
                weights[base:base + width] = old[base:base + width]
                continue
            new_row = updated[order]
            if lock_mode != LOCKS_IGNORE and locked:
                new_row = _apply_locks_row(
                    list(new_row), old[base:base + width], locked, free, lock_mode)
            weights[base:base + width] = new_row

    return [list(weights[row * width:(row + 1) * width]) for row in targets]


def _smooth_numpy(weights, width, nbs, sizes, targets, iterations, power,
                  keep_one, locked, free, lock_mode):
    """numpy 경로. 원본 `smoothSkinWeights()` 의 식과 같은 순서로 계산한다."""
    matrix = np.array(weights, dtype="float64").reshape(-1, width)
    old = matrix.copy()
    rows = np.array(targets, dtype=int)

    pad = matrix.shape[0] - 1                  # 패딩 행(0) 의 인덱스
    max_nb = max(len(nb) for nb in nbs) if nbs else 1
    table = np.full((len(nbs), max_nb), pad, dtype=int)
    for order, nb in enumerate(nbs):
        table[order, :len(nb)] = nb
    denom = (1.0 / np.array(sizes, dtype="float64"))[:, np.newaxis, np.newaxis]

    keep_rows = None
    if keep_one:
        keep_rows = rows[np.max(old[rows], axis=1) > KEEP_ONE_EPS]

    lock_cols = np.array(locked, dtype=int)
    free_cols = np.array(free, dtype=int)

    for _ in range(max(0, int(iterations))):
        contrib = matrix[table] * denom
        if power:
            contrib = np.power(contrib, power)
        values = np.sum(contrib, axis=-2)

        if power:
            sums = np.sum(values, axis=-1)
            sums[sums < 1e-5] = 1.0
            values = values / sums[:, np.newaxis]

        matrix[rows] = values

        if keep_rows is not None and keep_rows.size:
            matrix[keep_rows] = old[keep_rows]

        if lock_mode != LOCKS_IGNORE and lock_cols.size:
            block = matrix[rows]
            old_block = old[rows]
            if lock_mode == LOCKS_KEEP:
                block[:, lock_cols] = old_block[:, lock_cols]
            elif lock_mode == LOCKS_ONLY_ADD:
                block[:, lock_cols] = np.maximum(block[:, lock_cols],
                                                 old_block[:, lock_cols])
            elif lock_mode == LOCKS_ONLY_REMOVE:
                block[:, lock_cols] = np.minimum(block[:, lock_cols],
                                                 old_block[:, lock_cols])
            free_sums = np.sum(block[:, free_cols], axis=1) if free_cols.size else None
            if free_sums is not None:
                free_sums[free_sums < 1e-9] = 1.0
                required = 1.0 - np.sum(block[:, lock_cols], axis=1)
                block[:, free_cols] *= (required / free_sums)[:, np.newaxis]
            matrix[rows] = block

    return [list(row) for row in matrix[rows]]


# ==================================================================
# 진입점
# ==================================================================

def smooth(iterations=4, blend=1.0, joint_locks=LOCKS_IGNORE, keep_value_one=False,
           border_edges=BORDER_ALL, border_mask_steps=2, rigid=0.0,
           loop_curve=None, skin_cluster=None, use_soft_selection=True,
           targets=None):
    """선택한 버텍스의 스킨 웨이트를 스무딩한다. `(바뀐 메시 수, 메시지 목록)`.

    targets 를 주면 그것을 쓰고(테스트 · 스크립트용), 안 주면 현재 선택을 읽는다.
    씬을 바꾸는 부분은 호출부(UI)가 `undo_chunk()` 안에서 부른다.
    """
    messages = []

    if joint_locks not in LOCK_MODES:
        raise ValueError("Unknown joint lock mode: {0}".format(joint_locks))
    if border_edges not in BORDER_MODES:
        raise ValueError("Unknown border mode: {0}".format(border_edges))

    iterations = max(0, int(iterations))
    blend = min(1.0, max(0.0, float(blend)))
    rigid = min(1.0, max(0.0, float(rigid)))
    power = (1.0 + rigid * RIGID_POWER_SCALE) if rigid > 0.0 else None

    if targets is None:
        targets = parse_selection(use_soft_selection=use_soft_selection)
    if not targets:
        return 0, ["[WARN] Select some vertices (or a skinned mesh) first."]

    if iterations == 0:
        return 0, ["[WARN] Iterations is 0 - nothing to smooth."]
    if blend <= 0.0:
        return 0, ["[WARN] Blend is 0 - the result would be the current weights."]

    if np is None:
        messages.append("[INFO] numpy was not found - using the slower pure "
                        "Python path.")

    done = 0
    for target in targets:
        mesh = target.get("mesh")
        started = time.time()

        skins = skin_clusters(mesh)
        if not skins:
            messages.append("[SKIP] {0} has no skinCluster.".format(_leaf(mesh)))
            continue
        if skin_cluster:
            if skin_cluster not in skins:
                messages.append("[SKIP] {0} is not driven by {1}.".format(
                    _leaf(mesh), _leaf(skin_cluster)))
                continue
            skin = skin_cluster
        else:
            skin = skins[0]
            if len(skins) > 1:
                messages.append("[INFO] {0} has {1} skinClusters - using {2}.".format(
                    _leaf(mesh), len(skins), _leaf(skin)))

        try:
            dag = _shape_dag(mesh, skin)
        except Exception as exc:                           # noqa: BLE001
            messages.append("[FAIL] {0} : {1}".format(_leaf(mesh), exc))
            continue

        fn = maya_skin.skin_fn(skin)
        total = _vertex_count(dag)
        ids = target.get("ids")
        ids = list(range(total)) if ids is None else [i for i in ids if 0 <= i < total]
        if not ids:
            messages.append("[SKIP] {0} : no vertices to smooth.".format(_leaf(mesh)))
            continue

        neighbors = connected_vertices(dag)

        restricted = {}
        if loop_curve:
            try:
                restricted = loop_neighbors(mesh, dag, ids, loop_curve, neighbors)
            except ValueError as exc:
                return done, messages + ["[FAIL] {0}".format(exc)]
            if not restricted:
                messages.append(
                    "[WARN] {0} : the Loop Curve did not reach any selected "
                    "vertex - smoothing every direction instead.".format(_leaf(mesh)))

        # --- 읽을 버텍스 = 선택 + 그 이웃 (이웃은 값이 바뀌지 않고 참고만 된다)
        union = set(ids)
        for vertex in ids:
            union.update(restricted.get(vertex, neighbors[vertex]))
        union = sorted(union)
        row_of = dict((vertex, order) for order, vertex in enumerate(union))

        weights, width = _read_weights(fn, dag, union)
        if width == 0:
            messages.append("[SKIP] {0} : the skinCluster has no influence.".format(
                _leaf(mesh)))
            continue
        weights.extend([0.0] * width)                      # 패딩 행 (없는 이웃용)

        rows = [row_of[vertex] for vertex in ids]
        nbs = []
        sizes = []
        for vertex in ids:
            own = restricted.get(vertex, neighbors[vertex])
            table = [row_of[vertex]] + [row_of[nb] for nb in own]
            nbs.append(table)
            sizes.append(float(len(table)))

        locked, free = _lock_columns(fn)
        if joint_locks != LOCKS_IGNORE and not locked:
            messages.append("[INFO] {0} : no influence is locked - the Joint Locks "
                            "option changes nothing.".format(_leaf(mesh)))

        engine = _smooth_numpy if np is not None else _smooth_python
        old_rows = [list(weights[row * width:(row + 1) * width]) for row in rows]
        new_rows = engine(list(weights), width, nbs, sizes, rows, iterations, power,
                          keep_value_one, locked, free, joint_locks)

        # --- 마스크 : Blend x 소프트 셀렉션 x 보더
        #     원본은 같은 lerp 를 순서대로 세 번 하는데, 전부 "원래 값 쪽으로" 의 lerp 라
        #     비율을 곱한 한 번과 값이 같다(테스트로 고정).
        factors = [blend] * len(ids)

        softs = target.get("softs") if use_soft_selection else None
        if softs:
            for order, vertex in enumerate(ids):
                factors[order] *= float(softs.get(vertex, 1.0))

        if border_edges != BORDER_ALL:
            mask = border_mask(dag, steps=border_mask_steps,
                               invert=(border_edges == BORDER_ONLY),
                               neighbors=neighbors)
            for order, vertex in enumerate(ids):
                factors[order] *= mask[vertex]

        final_rows = []
        touched = 0
        for order in range(len(ids)):
            factor = factors[order]
            if factor <= 0.0:
                final_rows.append(old_rows[order])
                continue
            touched += 1
            if factor >= 1.0:
                final_rows.append(new_rows[order])
                continue
            old_row = old_rows[order]
            new_row = new_rows[order]
            final_rows.append([old_row[c] + (new_row[c] - old_row[c]) * factor
                               for c in range(width)])

        _write_weights(skin, fn, ids, final_rows)
        done += 1

        note = ""
        if loop_curve and restricted:
            note = " along {0} ({1} vertices on the loop)".format(
                _leaf(loop_curve) if not isinstance(loop_curve, (list, tuple, set))
                else "the given vertices", len(restricted))
        messages.append(
            "[OK] {0} : smoothed {1} of {2} vertices{3}, {4} iteration(s) on {5} "
            "influence(s) in {6:.2f}s.".format(
                _leaf(mesh), touched, len(ids), note, iterations, width,
                time.time() - started))
        if touched < len(ids):
            messages.append(
                "    {0} vertex(es) were left as they are (Blend, soft selection "
                "or the border mask was 0 there).".format(len(ids) - touched))

    if not done and not any(m.startswith("[OK]") for m in messages):
        messages.append("[WARN] Nothing was smoothed.")

    return done, messages
