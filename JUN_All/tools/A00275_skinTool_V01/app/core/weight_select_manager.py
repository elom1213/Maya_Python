# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00275_skinTool_V01 core - Select > By Weight
"""
체크한 조인트의 스킨 웨이트가 기준값 이상 / 이하인 버텍스를 고른다. UI 비의존.

범위(scope)는 두 가지다.
  * 메시 통째로 불러오면  -> 그 메시의 **모든** 버텍스 (vertices=None 으로 보관 - 불러온 뒤
    버텍스 수가 바뀌어도 실행 시점의 전체를 본다)
  * 버텍스(엣지/페이스도 버텍스로 변환)를 골라 불러오면 -> **그 버텍스들만**
범위를 **불러올 때 저장**하는 이유: 결과를 고르는 순간 마야 선택이 결과로 바뀌고, 조인트
리스트 행을 눌러도 조인트가 선택된다. 실행 시점의 선택을 범위로 쓰면 기준값만 바꿔 다시
고르는 흐름이 깨진다.

여러 조인트를 체크했을 때의 판정(combine)
  * COMBINE_ANY  - 체크한 조인트 중 **하나라도** 조건을 만족
  * COMBINE_ALL  - 체크한 조인트 **모두** 조건을 만족
  * COMBINE_SUM  - 체크한 조인트 웨이트의 **합**이 조건을 만족
`<=` 는 웨이트가 0 인(그 조인트에 전혀 안 묶인) 버텍스도 포함한다 - 값 그대로의 뜻이다.

웨이트는 `MFnSkinCluster.getWeights` 한 번으로 읽는다. 인덱스는 **물리 인덱스** 열 순서
(Framework.core.maya_skin 주석 참고).
"""

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core import maya_shape
from Framework.core import maya_skin
from tools.A00275_skinTool_V01.app.core import expand_bind_manager as eb


MODE_AT_LEAST = "at_least"      # weight >= value
MODE_AT_MOST = "at_most"        # weight <= value
MODES = (MODE_AT_LEAST, MODE_AT_MOST)

COMBINE_ANY = "any"
COMBINE_ALL = "all"
COMBINE_SUM = "sum"
COMBINES = (COMBINE_ANY, COMBINE_ALL, COMBINE_SUM)

# 웨이트는 float 로 저장돼서 1.0 이 0.99999994 로 읽히기도 한다. 경계값은 포함으로 본다.
EPSILON = 1e-6


def _leaf(name):
    return name.split("|")[-1]


def _long(name):
    found = cmds.ls(name, long=True) or []
    return found[0] if found else None


# ==================================================================
# 판정 (마야 없는 순수 계산)
# ==================================================================

def match_rows(rows, columns, threshold, mode=MODE_AT_LEAST, combine=COMBINE_ANY):
    """rows[i] = 인플루언스 열 순서의 웨이트 행. 조건을 만족하는 행 번호 목록."""
    if mode not in MODES:
        raise ValueError("Unknown mode: {0}".format(mode))
    if combine not in COMBINES:
        raise ValueError("Unknown combine: {0}".format(combine))
    if not columns:
        raise ValueError("No joint to test.")
    threshold = float(threshold)
    if mode == MODE_AT_LEAST:
        test = lambda w: w >= threshold - EPSILON
    else:
        test = lambda w: w <= threshold + EPSILON

    out = []
    for i, row in enumerate(rows):
        values = [row[c] for c in columns]
        if combine == COMBINE_ANY:
            ok = any(test(v) for v in values)
        elif combine == COMBINE_ALL:
            ok = all(test(v) for v in values)
        else:
            ok = test(sum(values))
        if ok:
            out.append(i)
    return out


def compress_ranges(ids):
    """정렬된 id -> [(시작, 끝)] 연속 구간."""
    ranges = []
    for vid in sorted(set(ids)):
        if ranges and vid == ranges[-1][1] + 1:
            ranges[-1][1] = vid
        else:
            ranges.append([vid, vid])
    return [tuple(r) for r in ranges]


# ==================================================================
# 범위 불러오기
# ==================================================================

def _skin_and_shape(mesh):
    """메시(트랜스폼 또는 셰이프) -> (skinCluster, 스킨이 실제로 변형하는 셰이프 롱네임)."""
    skin = eb.skincluster_of(mesh)
    if not skin:
        raise ValueError("'{0}' has no skinCluster.".format(_leaf(mesh)))
    shape, drives = maya_shape.drives_shape(skin, mesh)
    if not drives:
        raise ValueError(
            "'{0}' is not deformed by {1}. Check the mesh history - the bound shape "
            "may be a different one under the same transform.".format(
                _leaf(shape or mesh), skin))
    return skin, shape


def load_scope():
    """현재 선택에서 범위를 만든다.

    반환 dict:
      mesh        - 메시 롱네임 (컴포넌트가 셰이프 이름으로 왔으면 셰이프)
      skin        - skinCluster
      vertices    - None(메시 전체) 또는 정렬된 버텍스 id 목록
      total       - 메시 버텍스 수
      influences  - 바인드된 조인트 롱네임 (getWeights 열 순서)
    """
    sel = cmds.ls(sl=True, long=True) or []
    has_components = any("." in s for s in sel)
    try:
        mesh, ids = eb.parse_selected_vertices()
    except ValueError:
        raise ValueError("Select a skinned mesh, or some of its vertices.")

    skin, shape = _skin_and_shape(mesh)
    fn = maya_skin.skin_fn(skin)
    return {
        "mesh": mesh,
        "skin": skin,
        "vertices": list(ids) if has_components else None,
        "total": maya_shape.vertex_count(shape, deformer=skin),
        "influences": maya_skin.influence_paths(fn),
    }


def read_influences(mesh):
    skin, _shape = _skin_and_shape(mesh)
    return maya_skin.influence_paths(maya_skin.skin_fn(skin))


# ==================================================================
# 고르기
# ==================================================================

def _component(ids=None, count=0):
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    if ids is None:
        comp_fn.setCompleteData(count)
    else:
        comp_fn.addElements(list(ids))
    return comp


def find_vertices(mesh, joints, threshold, mode=MODE_AT_LEAST, combine=COMBINE_ANY,
                  vertices=None):
    """조건을 만족하는 버텍스 id 목록(정렬). vertices=None 이면 메시 전체에서 찾는다."""
    if not mesh or not cmds.objExists(mesh):
        raise ValueError("The loaded mesh no longer exists. Load it again.")
    if not joints:
        raise ValueError("Check at least one joint.")
    threshold = float(threshold)
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("The value must be between 0 and 1 (got {0}).".format(threshold))

    skin, shape = _skin_and_shape(mesh)
    fn = maya_skin.skin_fn(skin)
    influences = maya_skin.influence_paths(fn)
    column_of = {path: i for i, path in enumerate(influences)}

    columns, missing = [], []
    for joint in joints:
        path = _long(joint) if cmds.objExists(joint) else None
        if path in column_of:
            columns.append(column_of[path])
        else:
            missing.append(_leaf(joint))
    if missing:
        raise ValueError("Not bound to {0}: {1}. Load the mesh again.".format(
            _leaf(mesh), ", ".join(missing)))

    total = maya_shape.vertex_count(shape, deformer=skin)
    if vertices is None:
        comp = _component(count=total)
    else:
        ids = sorted(set(int(v) for v in vertices))
        if not ids:
            return []
        if ids[-1] >= total:
            raise ValueError(
                "The loaded vertices do not fit {0} anymore ({1} vertices now). "
                "Load them again.".format(_leaf(mesh), total))
        comp = _component(ids)

    dag = maya_shape.shape_dag(shape, deformer=skin, type_="mesh")
    flat, n_inf = fn.getWeights(dag, comp)
    flat = list(flat)
    # 행 순서는 컴포넌트의 원소 순서다 - 넣은 순서를 믿지 않고 되읽는다.
    order = list(om.MFnSingleIndexedComponent(comp).getElements()) \
        if vertices is not None else list(range(total))
    rows = [flat[i * n_inf:(i + 1) * n_inf] for i in range(len(order))]
    hits = match_rows(rows, columns, threshold, mode, combine)
    return sorted(order[i] for i in hits)


def select_vertices(mesh, ids):
    """ids 를 마야에서 선택한다(교체). 빈 목록이면 선택을 건드리지 않는다."""
    if not ids:
        return
    names = ["{0}.vtx[{1}:{2}]".format(mesh, a, b) for a, b in compress_ranges(ids)]
    cmds.select(names, replace=True)
    # 오브젝트 모드에서도 고른 버텍스가 보이게 메시를 하이라이트한다.
    transform = eb.mesh_transform(mesh) or mesh
    try:
        cmds.hilite(transform, replace=True)
    except RuntimeError:
        pass
