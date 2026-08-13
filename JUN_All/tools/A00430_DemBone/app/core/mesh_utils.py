# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 메시 읽기 헬퍼 (maya.cmds / OpenMaya 의존)
#
# 셰이프 확정은 반드시 공용 `Framework.core.maya_shape` 를 쓴다.
# `MDagPath.extendToShape()` 는 트랜스폼 밑에 셰이프가 여럿일 때 **조용히 엉뚱한 셰이프**를
# 고른다(웨이트 API 에 넘기면 kInvalidParameter, 지오메트리는 더 위험하게 조용히 틀림).

import numpy as np

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.core import maya_shape


def shape_of(node, deformer=None):
    """메시 셰이프 롱네임. 못 찾으면 ValueError."""
    shape = maya_shape.shape_path(node, deformer=deformer, type_="mesh")
    if shape is None:
        raise ValueError("'{0}' has no polygon mesh shape.".format(node))
    return shape


def mesh_fn(node, deformer=None):
    """확정된 셰이프의 MFnMesh. 프레임을 옮겨가며 재사용해도 된다."""
    return om.MFnMesh(maya_shape.shape_dag(node, deformer=deformer, type_="mesh"))


def vertex_count(node, deformer=None):
    return maya_shape.vertex_count(node, deformer=deformer)


def get_points(fn, world=True):
    """(nV, 3) 버텍스 위치."""
    space = om.MSpace.kWorld if world else om.MSpace.kObject
    pts = fn.getPoints(space)
    return np.asarray(pts, dtype=float)[:, :3]


def get_faces(node, deformer=None):
    """폴리곤별 버텍스 인덱스 리스트 (DemBones 의 fv). 라플라시안 스무딩용."""
    fn = mesh_fn(node, deformer=deformer)
    counts, indices = fn.getVertices()
    faces = []
    pos = 0
    for c in counts:
        faces.append([int(v) for v in indices[pos:pos + c]])
        pos += c
    return faces


def topo_signature(node, deformer=None):
    """토폴로지 비교용 (버텍스, 엣지, 페이스) 튜플."""
    shape = shape_of(node, deformer=deformer)
    return (int(cmds.polyEvaluate(shape, v=True)),
            int(cmds.polyEvaluate(shape, e=True)),
            int(cmds.polyEvaluate(shape, f=True)))


def frame_list(start, end, stride=1):
    """[start, end] 를 stride 로 훑되 **end 는 반드시 포함**한다."""
    start = int(start)
    end = int(end)
    stride = max(1, int(stride))
    if end < start:
        start, end = end, start
    frames = list(range(start, end + 1, stride))
    if frames[-1] != end:
        frames.append(end)
    return frames
