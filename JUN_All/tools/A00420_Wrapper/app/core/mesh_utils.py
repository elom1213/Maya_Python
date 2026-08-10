# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-10
# A00420_Wrapper core - 메시/커브 읽기·쓰기 + 최근접점 가속기 (numpy). UI 비의존.
#
# 검증해 둔 마야 API 함정 (mayapy headless 로 확인):
#   * `MMeshIntersector.create(node, matrix)` 에 월드 행렬을 넘겨도 `getClosestPoint()` 가
#     돌려주는 point/normal 은 **오브젝트 공간**이다. 그래서 여기서는 아예 intersector 를
#     항등(=오브젝트 공간)으로 만들고, 질의 좌표를 numpy 로 한 번에 오브젝트 공간으로
#     옮겨 넣는다(행렬 변환을 파이썬 루프 밖으로 뺀다).
#   * 속도: MMeshIntersector 20k 질의 0.6s vs `MFnMesh.getClosestPoint(kWorld)` 4.9s.
#     → 반복 투영에는 반드시 MMeshIntersector 를 쓴다.
#   * `MFnMesh.getPoints()` 를 np.array 로 감싸면 (N, 4) 동차좌표다. `[:, :3]` 로 자른다.
#   * 마야는 행벡터 규약(p' = p * M)이라 numpy 에서도 `p @ M[:3,:3] + M[3,:3]` 가 맞다.

import maya.cmds as cmds
import maya.api.OpenMaya as om

import numpy as np


# ============================================================ 노드 / 행렬

def dag_path(node):
    """노드 이름 -> MDagPath."""
    sel = om.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)


def mesh_shape_of(node):
    """transform 또는 shape 이름을 받아 mesh shape 의 full path 를 돌려준다. 없으면 None."""
    if not node or not cmds.objExists(node):
        return None

    if cmds.nodeType(node) == "mesh":
        return cmds.ls(node, long=True)[0]

    shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True,
                                type="mesh", fullPath=True) or []
    return shapes[0] if shapes else None


def curve_shape_of(node):
    """transform 또는 shape 이름을 받아 nurbsCurve shape 의 full path 를 돌려준다."""
    if not node or not cmds.objExists(node):
        return None

    if cmds.nodeType(node) == "nurbsCurve":
        return cmds.ls(node, long=True)[0]

    shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True,
                                type="nurbsCurve", fullPath=True) or []
    return shapes[0] if shapes else None


def matrix_to_np(m):
    """MMatrix -> (4, 4) numpy 배열 (마야와 같은 row-major)."""
    try:
        return np.array(m, dtype=np.float64).reshape(4, 4)
    except Exception:
        return np.array([[m.getElement(r, c) for c in range(4)]
                         for r in range(4)], dtype=np.float64)


def xform_points(points, m):
    """(N, 3) 점들을 4x4 행렬로 변환 (마야 행벡터 규약)."""
    return np.asarray(points, dtype=np.float64) @ m[:3, :3] + m[3, :3]


def xform_normals(normals, m):
    """(N, 3) 노멀을 4x4 행렬로 변환. 노멀은 역전치를 쓴다 (n' = n * (M^-1)^T)."""
    inv3 = np.linalg.inv(m[:3, :3])
    return np.asarray(normals, dtype=np.float64) @ inv3.T


def world_position(name):
    """오브젝트/컴포넌트(vtx, cv, 로케이터, transform)의 월드 위치를 (3,) 로."""
    if "." in name and "[" in name:
        return np.array(cmds.pointPosition(name, world=True), dtype=np.float64)

    return np.array(cmds.xform(name, q=True, ws=True, t=True), dtype=np.float64)


# ============================================================ 메시 래퍼

class MeshData(object):
    """메시 하나의 dag/함수셋/좌표 캐시. 월드 <-> 오브젝트 변환 행렬을 들고 있다."""

    def __init__(self, node):

        shape = mesh_shape_of(node)
        if not shape:
            raise ValueError("Not a mesh: {0}".format(node))

        self.node = node
        self.shape = shape
        self.name = shape.split("|")[-1]
        self.dag = dag_path(shape)
        self.fn = om.MFnMesh(self.dag)
        self.count = self.fn.numVertices

        self.o2w = matrix_to_np(self.dag.inclusiveMatrix())
        self.w2o = matrix_to_np(self.dag.inclusiveMatrixInverse())

        self._adjacency = None

    # ---- 좌표 ------------------------------------------------------

    def world_points(self):
        return np.array(self.fn.getPoints(om.MSpace.kWorld),
                        dtype=np.float64)[:, :3]

    def object_points(self):
        return np.array(self.fn.getPoints(om.MSpace.kObject),
                        dtype=np.float64)[:, :3]

    def world_normals(self):
        return np.array(self.fn.getVertexNormals(False, om.MSpace.kWorld),
                        dtype=np.float64)[:, :3]

    # ---- 인접 정보 -------------------------------------------------

    def adjacency(self):
        """라플라시안 스무딩용 이웃 정보 (i, j, count) 를 돌려준다.

        i[k] 의 이웃이 j[k]. 삼각형에서 만들어 numpy 로만 다룬다(엣지 순회 루프 없음).
        count 는 정점별 이웃 수(0 이면 1 로 클램프).
        """
        if self._adjacency is not None:
            return self._adjacency

        _, tri_verts = self.fn.getTriangles()
        tv = np.array(tri_verts, dtype=np.int64).reshape(-1, 3)

        e = np.vstack([tv[:, [0, 1]], tv[:, [1, 2]], tv[:, [2, 0]]])
        i = np.concatenate([e[:, 0], e[:, 1]])
        j = np.concatenate([e[:, 1], e[:, 0]])

        # 삼각형이 공유하는 엣지 때문에 중복이 생긴다 -> (i, j) 쌍으로 유일화.
        key = np.unique(i * np.int64(self.count) + j)
        i = key // self.count
        j = key % self.count

        count = np.bincount(i, minlength=self.count).astype(np.float64)
        count[count == 0.0] = 1.0

        self._adjacency = (i.astype(np.int64), j.astype(np.int64), count)
        return self._adjacency

    # ---- 쓰기 ------------------------------------------------------

    def _read_tweaks(self):
        """shape.pnts 에 이미 들어 있는 tweak 값 {idx: (x, y, z)}."""
        tweaks = {}
        try:
            plug = om.MFnDependencyNode(self.dag.node()).findPlug("pnts", False)
            for i in plug.getExistingArrayAttributeIndices():
                ep = plug.elementByLogicalIndex(i)
                tweaks[i] = (ep.child(0).asFloat(),
                             ep.child(1).asFloat(),
                             ep.child(2).asFloat())
        except Exception:
            pass
        return tweaks

    def set_world_points(self, world_pts, chunk=4000):
        """월드 좌표 (N, 3) 을 이 메시에 쓴다. undo 가능하도록 shape.pnts 에 구간 setAttr.

        A00380_MeshTool 과 같은 방식이다. `pnts`(tweak)는 기존 지오/디포머 출력 **위에**
        더해지는 값이라, 이미 들어 있던 tweak 을 읽어 (원하는 위치 - 현재 위치)만큼만
        더한다. 그래서 히스토리/스킨이 걸린 메시에서도 결과가 맞고 Ctrl+Z 도 정확하다.
        """
        world_pts = np.asarray(world_pts, dtype=np.float64)
        if len(world_pts) != self.count:
            raise ValueError(
                "Point count mismatch: mesh {0}, given {1}".format(
                    self.count, len(world_pts)))

        want_obj = xform_points(world_pts, self.w2o)
        delta = want_obj - self.object_points()

        base = self._read_tweaks()

        for start in range(0, self.count, chunk):
            end = min(start + chunk, self.count) - 1

            flat = []
            for i in range(start, end + 1):
                bx, by, bz = base.get(i, (0.0, 0.0, 0.0))
                dx, dy, dz = delta[i]
                flat.extend((bx + dx, by + dy, bz + dz))

            if start == end:
                cmds.setAttr("{0}.pnts[{1}]".format(self.shape, start),
                             flat[0], flat[1], flat[2], type="double3")
            else:
                cmds.setAttr("{0}.pnts[{1}:{2}]".format(self.shape, start, end),
                             *flat, type="double3")

        return self.count


# ============================================================ 최근접점

class ClosestPointFinder(object):
    """대상 메시 위의 최근접점을 빠르게 찾는다 (MMeshIntersector).

    intersector 는 오브젝트 공간(항등 행렬)으로 만들고, 질의/결과 좌표 변환은
    numpy 로 통째 처리한다. 파이썬 루프 안에서는 MPoint 생성 + 질의만 한다.
    """

    def __init__(self, mesh):

        self.mesh = mesh
        self._inter = om.MMeshIntersector()
        self._inter.create(mesh.dag.node())

    def query(self, world_pts):
        """(N, 3) 월드 점들의 최근접점을 찾는다.

        반환: (points_world, normals_world, distance)
          points_world  : (N, 3) 대상 표면 위의 최근접 월드 좌표
          normals_world : (N, 3) 그 지점의 월드 노멀
          distance      : (N,)   원래 점에서의 거리
        """
        world_pts = np.asarray(world_pts, dtype=np.float64)
        n = len(world_pts)

        obj = xform_points(world_pts, self.mesh.w2o)

        out = np.array(obj, copy=True)
        nrm = np.zeros((n, 3), dtype=np.float64)
        nrm[:, 1] = 1.0

        get_closest = self._inter.getClosestPoint
        MPoint = om.MPoint

        for k in range(n):
            try:
                r = get_closest(MPoint(obj[k, 0], obj[k, 1], obj[k, 2]))
            except Exception:
                continue

            p = r.point
            v = r.normal
            out[k, 0] = p.x
            out[k, 1] = p.y
            out[k, 2] = p.z
            nrm[k, 0] = v.x
            nrm[k, 1] = v.y
            nrm[k, 2] = v.z

        pts_w = xform_points(out, self.mesh.o2w)
        nrm_w = xform_normals(nrm, self.mesh.o2w)

        length = np.linalg.norm(nrm_w, axis=1)
        length[length == 0.0] = 1.0
        nrm_w = nrm_w / length[:, None]

        dist = np.linalg.norm(pts_w - world_pts, axis=1)

        return pts_w, nrm_w, dist


# ============================================================ 라플라시안

def smooth_field(values, adjacency, amount, iterations):
    """정점별 벡터장 (N, 3) 을 메시 인접으로 라플라시안 스무딩한다.

    위치가 아니라 **변위(displacement)** 를 스무딩하는 데 쓴다. 그래야 원본 메시의
    디테일을 유지하면서 투영으로 생긴 스파이크만 눌린다.
    """
    if amount <= 0.0 or iterations <= 0:
        return values

    i, j, count = adjacency
    out = np.array(values, dtype=np.float64, copy=True)
    n = len(out)

    for _ in range(int(iterations)):
        avg = np.empty_like(out)
        for c in range(3):
            avg[:, c] = np.bincount(i, weights=out[j, c], minlength=n)
        avg /= count[:, None]
        out += amount * (avg - out)

    return out
