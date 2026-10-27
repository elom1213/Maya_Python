# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00275_skinTool_V01 - 스킨 웨이트 공용 헬퍼 (Weights > Smooth · Weights > Move 가 함께 쓴다, UI 비의존)
"""
v01.37 에서 `weight_smooth_manager.py` 에 있던 함수들을 **이름 · 동작 그대로** 옮겼다
(Move 탭이 같은 선택 파싱 · 이웃 · 보더 마스크 · Joint Locks · undo 되는 쓰기를 써야 해서).
`weight_smooth_manager` 는 이 모듈에서 같은 이름으로 import 한다 - 회귀 시험
`tests/test_weight_smooth_regression.py` 로 옮기기 전 결과와 같음을 고정했다.

원본 (읽기 전용 참고, 저장소 밖): kangaroo `kangarooTools/patch.py` - `JointLocks` · `BorderEdges` ·
`getSelectedPatches` · `getNeighbors` · `getBorderMask` · `_applyJointLocks`.
"""

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core import maya_shape
from Framework.core import maya_skin

# 조인트 lock 모드 - 값까지 kangaroo `patch.JointLocks` 와 같게 둔다.
LOCKS_IGNORE = 0            # 잠금을 무시한다
LOCKS_KEEP = 1              # 잠긴 조인트의 값은 그대로 두고 나머지로 맞춘다
LOCKS_ONLY_ADD = 2          # 잠긴 조인트는 늘어나는 것만 허용
LOCKS_ONLY_REMOVE = 3       # 잠긴 조인트는 줄어드는 것만 허용

LOCK_MODES = (LOCKS_IGNORE, LOCKS_KEEP, LOCKS_ONLY_ADD, LOCKS_ONLY_REMOVE)

# 경계(보더) 처리 - kangaroo `patch.BorderEdges`.
BORDER_ALL = 0              # 전부 스무딩
BORDER_IGNORE = 1           # 열린 경계 쪽은 빼고
BORDER_ONLY = 2             # 열린 경계 쪽만

BORDER_MODES = (BORDER_ALL, BORDER_IGNORE, BORDER_ONLY)

# ==================================================================
# 씬 조회 헬퍼
# ==================================================================

def _long(node):
    found = cmds.ls(node, l=True)
    return found[0] if found else node


def _leaf(name):
    return name.split("|")[-1]


def mesh_transform(node):
    """메시 · 셰이프 · 컴포넌트 이름에서 **트랜스폼 풀패스**."""
    node = node.split(".")[0]
    if cmds.objExists(node) and cmds.objectType(node) == "mesh":
        parents = cmds.listRelatives(node, p=True, f=True)
        node = parents[0] if parents else node
    return _long(node)


def skin_clusters(mesh):
    """그 메시를 구동하는 skinCluster 목록(히스토리 순서)."""
    if not mesh or not cmds.objExists(mesh):
        return []
    history = cmds.listHistory(mesh, pdo=True) or []
    return cmds.ls(history, type="skinCluster") or []


def _shape_dag(mesh, skin):
    """웨이트 API 에 넘길 셰이프 MDagPath.

    `extendToShape()` 를 쓰지 않는다 - 셰이프가 여럿이면 조용히 엉뚱한 것을 집는다
    (공용 `Framework.core.maya_shape` 주석 참고).
    """
    return maya_shape.shape_dag(mesh, deformer=skin)


def _vertex_count(dag):
    return om.MFnMesh(dag).numVertices


# ==================================================================
# 선택 읽기 (버텍스 + 소프트 셀렉션)
# ==================================================================

def _component_ids(comp):
    fn = om.MFnSingleIndexedComponent(comp)
    return [fn.element(i) for i in range(fn.elementCount)]


def _soft_of(comp):
    fn = om.MFnSingleIndexedComponent(comp)
    if not fn.hasWeights:
        return None
    return dict((fn.element(i), fn.weight(i).influence)
                for i in range(fn.elementCount))


def parse_selection(use_soft_selection=True):
    """지금 선택에서 `[{"mesh", "ids", "softs"}, ...]`.

    - 버텍스(엣지 · 페이스도 버텍스로 바뀐다)를 고르면 그 버텍스만.
    - 메시 자체를 고르면 `ids=None`(= 메시 전체).
    - 소프트 셀렉션이 켜져 있으면 `softs={id: falloff}`. 끄거나 `use_soft_selection=False`
      면 None.

    kangaroo `patch.getSelectedPatches()` 와 같은 순서로 본다 - 컴포넌트 선택이 먼저이고,
    같은 메시가 오브젝트로도 잡히면 컴포넌트 쪽을 남긴다.
    """
    targets = []
    seen = set()

    # --- 컴포넌트 (소프트 셀렉션 포함)
    rich = None
    if use_soft_selection and cmds.softSelect(q=True, softSelectEnabled=True):
        try:
            rich = om.MGlobal.getRichSelection().getSelection()
        except Exception:                                  # noqa: BLE001
            rich = None

    if rich is None:
        # 소프트 셀렉션이 꺼져 있으면 컴포넌트를 평범하게 읽는다(엣지/페이스는 버텍스로).
        # ★ **컴포넌트만** 넘긴다 - 오브젝트를 그대로 넘기면 `polyListComponentConversion` 이
        #   메시 전체를 버텍스 목록으로 펼쳐서, "메시를 골랐다"(ids=None)와 구별이 사라진다.
        picked = [item for item in (cmds.ls(sl=True, l=True) or []) if "." in item]
        verts = cmds.polyListComponentConversion(picked, tv=True) or [] if picked else []
        verts = cmds.filterExpand(verts, sm=31, fp=True) or []
        grouped = {}
        for item in verts:
            mesh = mesh_transform(item)
            index = int(item.split("[")[-1].split("]")[0])
            grouped.setdefault(mesh, []).append(index)
        for mesh, ids in grouped.items():
            targets.append({"mesh": mesh, "ids": sorted(set(ids)), "softs": None})
            seen.add(mesh)
    else:
        for i in range(rich.length()):
            try:
                dag, comp = rich.getComponent(i)
            except Exception:                              # noqa: BLE001
                continue
            if comp.isNull() or not comp.hasFn(om.MFn.kMeshVertComponent):
                continue
            mesh = mesh_transform(dag.fullPathName())
            ids = _component_ids(comp)
            if not ids:
                continue
            softs = _soft_of(comp)
            targets.append({"mesh": mesh, "ids": sorted(ids), "softs": softs})
            seen.add(mesh)

    # --- 오브젝트로 고른 메시 = 전체
    for node in cmds.ls(sl=True, o=True, l=True) or []:
        if cmds.objectType(node) == "mesh":
            mesh = mesh_transform(node)
        elif cmds.listRelatives(node, s=True, type="mesh", f=True):
            mesh = _long(node)
        else:
            continue
        if mesh in seen:
            continue
        seen.add(mesh)
        targets.append({"mesh": mesh, "ids": None, "softs": None})

    return targets


# ==================================================================
# 토폴로지 (이웃 · 경계)
# ==================================================================

def connected_vertices(dag):
    """버텍스마다 엣지로 이어진 버텍스 목록 (메시 전체)."""
    it = om.MItMeshVertex(dag)
    out = [None] * _vertex_count(dag)
    while not it.isDone():
        out[it.index()] = list(it.getConnectedVertices())
        it.next()
    return [nbs if nbs is not None else [] for nbs in out]


def border_flags(dag):
    """버텍스마다 열린 경계 위인지 (kangaroo `getBorderBoolArray`)."""
    it = om.MItMeshVertex(dag)
    flags = [False] * _vertex_count(dag)
    while not it.isDone():
        flags[it.index()] = bool(it.onBoundary())
        it.next()
    return flags


def border_mask(dag, steps=2, invert=False, neighbors=None):
    """경계에서 안쪽으로 번지는 0~1 마스크 (kangaroo `getBorderMask`).

    경계 버텍스를 1 로 두고 **경계값을 고정한 채** 메시 전체에서 `steps` 번 평균을 돌려
    안쪽으로 번지게 한다. `invert=False` 면 `1 - mask` 를 돌려준다.

      - Border Edges = Ignore  -> `invert=False` : 경계 근처가 0 (손대지 않는다)
      - Border Edges = Only    -> `invert=True`  : 경계 근처가 1 (거기만 손댄다)
    """
    flags = border_flags(dag)
    if neighbors is None:
        neighbors = connected_vertices(dag)

    values = [1.0 if flag else 0.0 for flag in flags]
    locked = [i for i, flag in enumerate(flags) if flag]

    for _ in range(max(0, int(steps))):
        updated = []
        for index, nbs in enumerate(neighbors):
            total = values[index]
            for nb in nbs:
                total += values[nb]
            updated.append(total / float(1 + len(nbs)))
        for index in locked:
            updated[index] = 1.0
        values = updated

    if invert:
        return values
    return [1.0 - value for value in values]


# ==================================================================
# 웨이트 읽기 / 쓰기
# ==================================================================

def _read_weights(fn, dag, ids):
    """`(flat 웨이트, 인플루언스 수)` — 행 순서는 `ids` 순서."""
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(list(ids))
    count = len(fn.influenceObjects())
    weights = fn.getWeights(dag, comp, maya_skin.weight_indices(count))
    return list(weights), count


def _write_weights(skin, fn, ids, rows):
    """`ids` 의 행만 구간 `setAttr` 로 쓴다(undo 가능).

    구간은 **새 값과 지금 값** 양쪽의 논리 인덱스를 덮어야 한다 - 안 그러면 예전 인플루언스
    값이 남아 합이 1 을 넘는다. 스무딩은 0 을 새로 만들 수 있으므로(평균이 0 인 열)
    지금 0 이 아닌 열도 함께 0 으로 덮는다.
    """
    logical = maya_skin.logical_indices(fn)
    template = "{0}.weightList[{{0}}].weights[{{1}}:{{2}}]".format(skin)

    for vertex, row in zip(ids, rows):
        values = {}
        for column, value in enumerate(row):
            if value != 0.0:
                values[logical[column]] = value
        for column, value in enumerate(row):
            values.setdefault(logical[column], 0.0)
        low = min(values)
        high = max(values)
        dense = [0.0] * (high - low + 1)
        for index, value in values.items():
            dense[index - low] = value
        cmds.setAttr(template.format(vertex, low, high), *dense)


def _lock_columns(fn):
    """`(잠긴 열, 안 잠긴 열)` — `getWeights` 의 열 순서 기준."""
    locked = []
    free = []
    for column, dag in enumerate(fn.influenceObjects()):
        attr = "{0}.liw".format(dag.fullPathName())
        is_locked = False
        try:
            is_locked = bool(cmds.getAttr(attr))
        except Exception:                                  # noqa: BLE001
            is_locked = False
        (locked if is_locked else free).append(column)
    return locked, free


def _apply_locks_row(row, old_row, locked, free, mode):
    """kangaroo `patch._applyJointLocks` 한 행 분량."""
    if mode == LOCKS_KEEP:
        for column in locked:
            row[column] = old_row[column]
    elif mode == LOCKS_ONLY_ADD:
        for column in locked:
            row[column] = max(row[column], old_row[column])
    elif mode == LOCKS_ONLY_REMOVE:
        for column in locked:
            row[column] = min(row[column], old_row[column])

    free_sum = sum(row[c] for c in free)
    if free_sum < 1e-9:
        free_sum = 1.0
    required = 1.0 - sum(row[c] for c in locked)
    factor = required / free_sum
    for column in free:
        row[column] *= factor
    return row
