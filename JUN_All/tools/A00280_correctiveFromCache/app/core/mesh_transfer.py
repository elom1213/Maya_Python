# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - maya.api 메시 포인트 읽기/쓰기 + 토폴로지 검사 (UI 비의존)
#
# 토폴로지가 동일한 두 메시(캐시 == 의상) 사이에서 버텍스 위치를 1:1 복사한다.
# viewport 비의존(MFnMesh) 이라 refresh suspend / 배치 상황에서도 안전.

from maya.api import OpenMaya as om

# 캐시와 의상의 트랜스폼이 다를 수 있으므로 코렉티브 추출은 월드 공간으로 복사한다
# (PoseWrangler EDIT 메시가 포즈된 월드 위치의 복제라는 가정과 일치).
WORLD = om.MSpace.kWorld
OBJECT = om.MSpace.kObject


def _shape_dag(mesh):
    """transform/shape 이름 -> shape MDagPath."""
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    dag.extendToShape()
    return dag


def topo_signature(mesh):
    """(vertex 수, polygon 수). 두 메시 비교용."""
    fn = om.MFnMesh(_shape_dag(mesh))
    return (fn.numVertices, fn.numPolygons)


def same_topology(mesh_a, mesh_b):
    return topo_signature(mesh_a) == topo_signature(mesh_b)


def get_points(mesh, space=om.MSpace.kObject):
    """메시의 포인트 배열(MPointArray)."""
    return om.MFnMesh(_shape_dag(mesh)).getPoints(space)


def set_points(mesh, points, space=om.MSpace.kObject):
    """메시 포인트를 주어진 배열로 덮어쓴다. 길이가 다르면 ValueError."""
    fn = om.MFnMesh(_shape_dag(mesh))
    if len(points) != fn.numVertices:
        raise ValueError(
            "point count mismatch: target={0} vs source={1}".format(
                fn.numVertices, len(points)))
    fn.setPoints(points, space)


def copy_points(source_mesh, target_mesh, space=om.MSpace.kObject):
    """source -> target 으로 버텍스 위치 복사 (토폴로지 동일 전제)."""
    set_points(target_mesh, get_points(source_mesh, space), space)


def max_delta(mesh_a, mesh_b, space=om.MSpace.kObject):
    """두 메시의 최대 버텍스 거리 (무주름 판정용). 토폴로지 다르면 None."""
    pa = get_points(mesh_a, space)
    pb = get_points(mesh_b, space)
    if len(pa) != len(pb):
        return None
    worst = 0.0
    for i in range(len(pa)):
        d = (pa[i] - pb[i]).length()
        if d > worst:
            worst = d
    return worst
