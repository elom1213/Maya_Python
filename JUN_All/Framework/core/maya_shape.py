# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-12
# Framework - "트랜스폼 -> 셰이프" 해석 공용 헬퍼.
#
# 여러 툴이 아래 패턴을 각자 복붙해 왔다:
#
#     sel = om.MSelectionList(); sel.add(mesh)
#     dag = sel.getDagPath(0)
#     dag.extendToShape()          # <- 문제
#
# `MDagPath.extendToShape()` 는 **첫 번째 non-intermediate 셰이프**를 고를 뿐이다
# (Orig/intermediate 는 건너뛴다 — Maya 2024 실측). 한 트랜스폼 아래에 셰이프가
# 여럿이면 — blendShape 타겟 셰이프를 같은 트랜스폼에 정리해 둔 리그, 머지/임포트
# 잔재, 셰이프를 부모로 끌어다 붙인 씬 — **원하는 셰이프가 아닌 것**이 나온다.
# 그 결과:
#
#   - 디포머 웨이트 API 에 넘기면 죽는다
#     `(kInvalidParameter): Object is incompatible with this method`
#   - 지오메트리를 읽고 쓰는 코드는 **조용히 엉뚱한 셰이프**를 만진다(더 위험)
#   - 덤: `cmds.polyEvaluate(<셰이프 여럿인 트랜스폼>, v=True)` 는 정수가 아니라
#     요약 **문자열**을 돌려줘 호출부가 TypeError 로 터진다
#
# 그래서 이 모듈은 셰이프를 **추측하지 않고 확정**한다.
#
#   1. 이미 셰이프면 그대로 쓴다.
#   2. `deformer` 를 주면 **그 디포머가 실제로 변형하는 셰이프**를 고른다
#      (`cmds.deformer -q -g` — skinCluster/blendShape/lattice 등 전부 동작).
#   3. 안 주면 트랜스폼의 히스토리에서 디포머를 찾아 같은 방식으로 고른다.
#   4. 그래도 못 정하면 non-intermediate 셰이프의 첫 번째.
#
# 웨이트를 읽고 쓰는 코드는 **deformer 를 넘겨** 쓰는 것을 권장한다.

import maya.api.OpenMaya as om
import maya.cmds as cmds


def _long(name):
    found = cmds.ls(name, l=True) or []
    return found[0] if found else None


def deformed_shapes(deformer):
    """디포머가 변형하는 셰이프 롱네임 집합."""
    if not deformer or not cmds.objExists(deformer):
        return set()
    try:
        geos = cmds.deformer(deformer, q=True, geometry=True) or []
    except Exception:
        geos = []

    shapes = set()
    for geo in geos:
        # 셰이프 이름으로 오는 게 보통이지만, 트랜스폼으로 오는 경우도 대비한다.
        shapes.update(cmds.ls(geo, l=True, shapes=True) or [])
        shapes.update(cmds.listRelatives(geo, s=True, f=True, ni=True) or [])
    return shapes


def _history_deformers(transform):
    return cmds.ls(cmds.listHistory(transform, pdo=True) or [],
                   type="geometryFilter") or []


def shape_path(node, deformer=None, type_="mesh"):
    """`node` 가 가리키는 **셰이프 롱네임**. 못 찾으면 None.

    Args:
        node: 트랜스폼 / 셰이프 / 컴포넌트('mesh.vtx[0]') 이름.
        deformer: 알고 있으면 넘긴다. 그 디포머가 변형하는 셰이프를 우선한다
            (웨이트를 읽고 쓸 때는 반드시 넘길 것).
        type_: 원하는 셰이프 타입. None 이면 타입을 가리지 않는다.
    """
    if not node:
        return None
    node = node.split(".")[0]
    node = _long(node)
    if node is None:
        return None

    if cmds.objectType(node, isAType="shape"):
        return node

    kwargs = {"s": True, "f": True, "ni": True}
    if type_:
        kwargs["type"] = type_
    shapes = cmds.listRelatives(node, **kwargs) or []
    if not shapes:
        return None
    if len(shapes) == 1:
        return shapes[0]

    # 셰이프가 여럿일 때만 디포머로 가린다(한 개면 질의 비용을 아낀다).
    candidates = [deformer] if deformer else _history_deformers(node)
    for candidate in candidates:
        driven = deformed_shapes(candidate)
        for shape in shapes:
            if shape in driven:
                return shape
    return shapes[0]


def shape_dag(node, deformer=None, type_="mesh"):
    """`shape_path` 로 확정한 셰이프의 MDagPath. 없으면 ValueError."""
    shape = shape_path(node, deformer=deformer, type_=type_)
    if shape is None:
        raise ValueError("'{0}' has no {1} shape.".format(
            node, type_ or "geometry"))
    sel = om.MSelectionList()
    sel.add(shape)
    return sel.getDagPath(0)


def vertex_count(node, deformer=None):
    """메시 버텍스 수. **셰이프 기준**으로 센다.

    트랜스폼에 `polyEvaluate` 를 걸면 셰이프가 여럿일 때 정수가 아닌 문자열이 온다.
    """
    shape = shape_path(node, deformer=deformer, type_="mesh")
    if shape is None:
        raise ValueError("'{0}' has no polygon mesh shape.".format(node))
    return int(cmds.polyEvaluate(shape, v=True))


def drives_shape(deformer, node):
    """그 디포머가 `node` 의 셰이프를 실제로 변형하는가. (셰이프 롱네임, 여부)"""
    shape = shape_path(node, deformer=deformer, type_=None)
    return shape, bool(shape) and shape in deformed_shapes(deformer)
