# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00275_skinTool_V01 - Weights > Flood 코어 (UI 비의존, v01.40)
"""
고른 조인트(들)에 웨이트를 **채운다**(flood). Kangaroo 플러그인 `SkinCluster > Flood` 를 **플러그인 없이** 옮긴 것.
마야 Paint Skin Weights 의 Flood 와 같지만, 소프트 셀렉션을 반영하고 조인트 여러 개를 한 번에 채울 수 있다.

원본 (읽기 전용 참고, 저장소 밖):
  `0020_maya_plugin/0010_kangaroo/scripts/kangarooTabTools/weights.py` : `floodSkinCluster()`
  `.../kangarooTools/xforms.py` : `findClosestJoints()`
  `.../kangarooTools/patch.py`  : `smoothValues2d()` · `setSkinClusterWeights()` · `checkInfluences()`

--------------------------------------------------------------------------
동작 (원본과 같다)
--------------------------------------------------------------------------
Operation (값까지 원본 `FloodSkinClusterOperation` 과 같다)
  - Replace Closest : 버텍스마다 가장 가까운 조인트(뼈 선분) 하나에 Value. 조인트가 하나면 전부 그것.
  - Add Closest     : 가장 가까운 조인트에 Value 를 **남은 몫(1 - 고른 조인트 합)** 비율로 더한다.
  - Replace All     : 고른 조인트 전부에 Value / 조인트 수.
  - Add All         : 위 값을 남은 몫 비율로 더한다.
  - Scale All       : 고른 조인트 값에 Value 를 곱한다(조인트마다 같은 Value - 아래 "원본과 다른 점").
  - Distribute      : 고른 조인트들끼리 웨이트를 나눠 갖는다 = Move(From = To = 고른 조인트).
조인트가 2 개 이상이면 조인트 사이 경계를 **선택 안 이웃만으로** Smooth Steps 번 평균(합 보존).
그 다음 나머지 인플루언스를 줄인다 - Value = 1 이면 0, 아니면 남은 몫에 비례해서.
마지막 섞기는 Move 와 같다 : Blend x 소프트 셀렉션 -> Joint Locks -> Border Edges.

--------------------------------------------------------------------------
원본과 다른 점 (사용자 요청 2026-11-19 : "같은 조인트 이름이 있어도 에러 없이")
--------------------------------------------------------------------------
원본은 인플루언스를 `fullPathName().split('|')[-1]` (짧은 이름) 으로 다룬다. 씬에 같은 이름 조인트가
둘이면 (1) 인플루언스 dict 가 겹쳐 엉뚱한 열에 쓰고, (2) `cmds.xform(짧은 이름)` 이
"More than one object matches name" 으로 죽고, (3) 없는 인플루언스 검사 · 추가도 짧은 이름이라 실패한다.
여기서는 **조인트와 인플루언스를 전부 풀패스(DAG 경로)로** 맞춘다 :
  - 조인트 목록은 UI 리스트의 UUID 로 푼 풀패스. 이름으로 넘어와도 하나로 안 풀리면 건너뛰고 알린다.
  - 인플루언스 열 = `MFnSkinCluster.influenceObjects()` 의 fullPathName.
  - 최근접 조인트 계산(`weight_move_manager.closest_targets`)도 풀패스로 xform, `skinParent` 도 풀패스로 푼다.
  - 없는 인플루언스는 풀패스로 weight 0 추가(원본의 "추가할까요" 대화 대신 로그).

그 밖에 원본 버그 (mayapy 에서 원본과 나란히 돌려 확인, tests/test_weight_flood.py)
  - Blend : 원본 floodSkinCluster 는 fBlend 를 setSkinClusterWeights 에 넘기지 않아 **Blend 가 무시된다**
    (Distribute 만 먹는다). 여기서는 모든 연산에 Blend 를 반영한다.
  - Scale All : 원본은 "All" 연산 값을 `Value / 조인트 수` 로 만들어 Scale 에도 그대로 쓴다 - 조인트 2 개에
    Scale 1 이면 둘 다 반이 되고, 거기에 "Value = 1 이면 나머지 0" 이 겹쳐 합이 1 보다 작아진다.
    여기서는 조인트마다 Value 를 그대로 곱하고 나머지는 늘 "남은 몫에 비례" 로 맞춘다 - Scale 1 = 변화 없음.
    조인트가 하나면 원본과 같다.
  - 고른 조인트 말고 다른 인플루언스가 없는 버텍스(예: 한 조인트 100%)에 Value < 1 을 주면 남은 몫을 받을 곳이
    없어 합이 1 보다 작게 남는다 - **원본과 같게 두고** 개수를 [WARN] 으로 알린다.
  - 원본 목록의 Subtract All 은 처리 분기가 주석 처리돼 동작하지 않아서 넣지 않았다.
  - Distance Meshes · Sphere Masks · Closest To Curve 는 Move 탭처럼 넣지 않았다.

웨이트 쓰기는 Smooth · Move 와 같이 **구간 setAttr**(undo 됨). 호출부(UI)가 `undo_chunk()` 안에서 부른다.
"""

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
from . import weight_move_manager as mv_mgr
from .weight_move_manager import (  # noqa: F401
    JOINT_LINES_NO,
    JOINT_LINES_YES,
    JOINT_LINES_ALL_CHILDREN,
    JOINT_LINE_MODES,
)

# Operation - 값까지 kangaroo `FloodSkinClusterOperation` 과 같다.
OP_REPLACE_CLOSEST = 0
OP_ADD_CLOSEST = 1
OP_REPLACE_ALL = 2
OP_ADD_ALL = 3
OP_SCALE_ALL = 6
OP_DISTRIBUTE = 12

OPERATIONS = (OP_REPLACE_CLOSEST, OP_ADD_CLOSEST, OP_REPLACE_ALL, OP_ADD_ALL, OP_SCALE_ALL, OP_DISTRIBUTE)
CLOSEST_OPS = (OP_REPLACE_CLOSEST, OP_ADD_CLOSEST)
#: Smooth Steps 가 의미 있는 연산 (원본 UI 의 setControlEnabled 와 같다)
SMOOTH_OPS = (OP_REPLACE_CLOSEST, OP_ADD_CLOSEST, OP_DISTRIBUTE)

OP_LABELS = {
    OP_REPLACE_CLOSEST: "replace closest",
    OP_ADD_CLOSEST: "add closest",
    OP_REPLACE_ALL: "replace all",
    OP_ADD_ALL: "add all",
    OP_SCALE_ALL: "scale all",
    OP_DISTRIBUTE: "distribute",
}

FULL_EPS = 0.999999         # 고른 조인트 합이 이보다 크면 나머지는 0 (원본 상수)
OTHERS_EPS = 0.00001        # 나머지 합이 이보다 작으면 1 로 (0 나누기 방지, 원본 상수)
SCALE_EPS = 0.000001        # Scale 의 분모 하한 (원본 상수)


# ==================================================================
# 한 행 계산 (원본 floodSkinCluster 의 numpy 식을 행 단위로)
# ==================================================================

def set_weights_for_rows(n_rows, n_joints, value, operation, closest=None):
    """고른 조인트에 줄 값 표 `[행][조인트]` (스무딩 전). closest : Closest 연산일 때 행마다 조인트 인덱스."""
    if n_joints == 1:
        return [[value] for _ in range(n_rows)]
    if operation in CLOSEST_OPS:
        out = []
        for r in range(n_rows):
            row = [0.0] * n_joints
            row[closest[r]] = value
            out.append(row)
        return out
    # Scale 은 조인트마다 Value 를 곱한다(원본은 Value / n 이라 조인트가 많을수록 더 줄었다).
    share = value if operation == OP_SCALE_ALL else value / float(n_joints)
    return [[share] * n_joints for _ in range(n_rows)]


def smooth_set_weights(sets, neighbor_rows, steps):
    """조인트 사이 경계 스무딩 + 행마다 합 되돌리기 (원본 smoothValues2d + 재정규화)."""
    if steps <= 0 or not sets or len(sets[0]) < 2:
        return sets
    n_joints = len(sets[0])
    sums_before = [sum(row) for row in sets]
    columns = [[row[i] for row in sets] for i in range(n_joints)]
    columns = mv_mgr.smooth_columns(columns, neighbor_rows, steps)
    out = []
    for r in range(len(sets)):
        row = [columns[i][r] for i in range(n_joints)]
        after = sum(row)
        scale = sums_before[r] / (after if after != 0 else 1.0)
        out.append([v * scale for v in row])
    return out


def apply_row(row, cols, others, sets, value, operation):
    """웨이트 한 행에 연산을 적용한다(제자리). cols : 고른 조인트 열, others : 나머지 열."""
    if operation in (OP_REPLACE_CLOSEST, OP_REPLACE_ALL):
        for i, c in enumerate(cols):
            row[c] = sets[i]
    elif operation in (OP_ADD_CLOSEST, OP_ADD_ALL):
        total = sum(sets)
        denom = 1.0 / (total if total > 1.0 else 1.0)
        scaled = [v * denom for v in sets]
        free = 1.0 - sum(row[c] for c in cols)
        for i, c in enumerate(cols):
            row[c] += scaled[i] * free
    elif operation == OP_SCALE_ALL:
        for i, c in enumerate(cols):
            row[c] = row[c] * sets[i]
        new_sum = sum(row[c] for c in cols)
        denom = new_sum if new_sum > 1.0 else 1.0
        if denom < SCALE_EPS:
            denom = 1.0
        for c in cols:
            row[c] /= denom

    # 나머지 인플루언스 줄이기
    if value == 1.0 and operation != OP_SCALE_ALL:
        for c in others:
            row[c] = 0.0
        return row
    sum_joints = sum(row[c] for c in cols)
    full = sum_joints > FULL_EPS
    if full:
        sum_joints = 0.0
    sum_others = sum(row[c] for c in others)
    if sum_others < OTHERS_EPS:
        sum_others = 1.0
    factor = (1.0 - sum_joints) / sum_others
    for c in others:
        row[c] = 0.0 if full else row[c] * factor
    return row


# ==================================================================
# 진입점
# ==================================================================

def flood_weights(joints, value=1.0, operation=OP_REPLACE_CLOSEST, smooth_steps=4, blend=1.0,
                  joint_lines=JOINT_LINES_ALL_CHILDREN, joint_locks=LOCKS_IGNORE, border_edges=BORDER_ALL,
                  border_mask_steps=1, respect_selection=True, use_soft_selection=True, project_squash=True,
                  island_check=True, confirm=None, targets=None):
    """선택 메시(들)에서 joints 에 웨이트를 채운다. `(바뀐 메시 수, 메시지 목록)`.

    joints : 풀패스 권장(UI 는 UUID 로 푼 풀패스를 넘긴다). 이름이 여러 조인트에 맞으면 건너뛴다.
    confirm : 섬이 여럿일 때 부를 콜백(질문 문자열 -> bool). None 이면 묻지 않고 진행한다.
    targets : 주면 선택 대신 그것을 쓴다(`[{"mesh", "ids", "softs"}]`, 테스트 · 스크립트용).
    """
    messages = []
    if operation not in OPERATIONS:
        raise ValueError("Unknown flood operation: {0}".format(operation))
    if joint_locks not in LOCK_MODES:
        raise ValueError("Unknown joint lock mode: {0}".format(joint_locks))
    if border_edges not in BORDER_MODES:
        raise ValueError("Unknown border mode: {0}".format(border_edges))
    if joint_lines not in JOINT_LINE_MODES:
        raise ValueError("Unknown joint line mode: {0}".format(joint_lines))
    smooth_steps = max(0, int(smooth_steps))
    blend = min(1.0, max(0.0, float(blend)))
    value = float(value)

    resolved = mv_mgr._resolve_joints(joints, "Joints", messages)
    if not resolved:
        return 0, messages + ["[WARN] Add the joints to flood to the list first."]

    if operation == OP_DISTRIBUTE:
        # 원본 : moveSkinClusterWeights(xJoints={j: '고른 조인트 전부'}) - From = To = 고른 조인트.
        if len(resolved) < 2:
            return 0, messages + ["[WARN] Distribute needs at least two joints."]
        done, more = mv_mgr.move_weights(
            resolved, resolved, smooth_steps=smooth_steps, blend=blend, joint_lines=joint_lines,
            joint_locks=joint_locks, border_edges=border_edges, border_mask_steps=border_mask_steps,
            respect_selection=respect_selection, use_soft_selection=use_soft_selection,
            project_squash=project_squash, island_check=island_check, confirm=confirm, targets=targets,
            report_overlap=False)
        return done, messages + more

    if targets is None:
        targets = parse_selection(use_soft_selection=use_soft_selection)
    if not targets:
        return 0, messages + ["[WARN] Select a skinned mesh (or some of its vertices) first."]
    if not respect_selection:
        targets = [{"mesh": t["mesh"], "ids": None, "softs": None} for t in targets]
    if blend <= 0.0:
        return 0, messages + ["[WARN] Blend is 0 - the result would be the current weights."]

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
            islands = mv_mgr.count_islands(ids, neighbors)
            if islands > 1 and confirm is not None:
                if not confirm("The selection on {0} is split into {1} islands. Continue?".format(
                        _leaf(mesh), islands)):
                    messages.append("[SKIP] {0} : stopped at the island check.".format(_leaf(mesh)))
                    continue

        # 2) 인플루언스가 아닌 조인트는 weight 0 으로 더한다 - 풀패스로 (원본은 짧은 이름이라 동명에서 실패)
        fn = maya_skin.skin_fn(skin)
        influences = [d.fullPathName() for d in fn.influenceObjects()]
        added = []
        for joint in resolved:
            if joint not in influences:
                cmds.skinCluster(skin, edit=True, addInfluence=joint, weight=0.0)
                added.append(joint)
        if added:
            messages.append("[Info] {0} : added {1} as influence(s) (weight 0).".format(
                _leaf(mesh), ", ".join(_leaf(j) for j in added)))
            fn = maya_skin.skin_fn(skin)
            influences = [d.fullPathName() for d in fn.influenceObjects()]

        col_of = dict((name, c) for c, name in enumerate(influences))
        weights, width = _read_weights(fn, dag, ids)
        rows = [weights[r * width:(r + 1) * width] for r in range(len(ids))]
        old = [list(row) for row in rows]
        cols = [col_of[j] for j in resolved]
        col_set = set(cols)
        others = [c for c in range(width) if c not in col_set]

        # 3) 고른 조인트에 줄 값 - Closest 는 지금 변형된 메시의 월드 좌표 (Move 와 같은 명령으로 읽는다)
        closest = None
        if operation in CLOSEST_OPS and len(resolved) > 1:
            flat = cmds.xform("{0}.vtx[*]".format(dag.fullPathName()), q=True, ws=True, t=True)
            points = [(flat[3 * v], flat[3 * v + 1], flat[3 * v + 2]) for v in ids]
            closest = mv_mgr.closest_targets(points, resolved, joint_lines, project_squash)
        sets = set_weights_for_rows(len(ids), len(resolved), value, operation, closest)
        if len(resolved) > 1 and smooth_steps > 0:
            row_of = dict((v, r) for r, v in enumerate(ids))
            neighbor_rows = [[r] + [row_of[nb] for nb in neighbors[v] if nb in row_of]
                             for r, v in enumerate(ids)]
            sets = smooth_set_weights(sets, neighbor_rows, smooth_steps)

        for r in range(len(ids)):
            apply_row(rows[r], cols, others, sets[r], value, operation)

        # 4) 섞기 - Blend x 소프트 -> Joint Locks -> Border (원본 setSkinClusterWeights 순서, Move 와 같다)
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
        short = [r for r in changed if abs(sum(final[r]) - 1.0) > 1e-6 and abs(sum(old[r]) - 1.0) <= 1e-6]
        if short:
            messages.append("[WARN] {0} : {1} vertex(es) had no other influence to take the rest - their weights now "
                            "add up to less than 1 (e.g. vtx[{2}] = {3:.3f}). Same as Kangaroo.".format(
                                _leaf(mesh), len(short), ids[short[0]], sum(final[short[0]])))
        messages.append("[OK] {0} : {1} {2:g} on {3} joint(s), {4} of {5} vertices changed{6} ({7:.2f}s).".format(
            _leaf(mesh), OP_LABELS[operation], value, len(resolved), len(changed), len(ids),
            " (soft)" if softs else "", time.time() - started))

    if not done and not any(m.startswith("[OK]") for m in messages):
        messages.append("[WARN] Nothing was flooded.")
    return done, messages
