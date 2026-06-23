# -*- coding: utf-8 -*-
"""
mesh_io - OpenMaya 2.0 기반 벌크 정점 입출력 어댑터.

origin.mel 의 핵심 병목(정점마다 `xform` 명령 1회)을 없앤다.
정점 좌표 전체를 `MFnMesh.getPoints` 로 한 번에 읽고, `setPoints` 로 한 번에 쓴다.
실제 씬 접근은 모두 이 모듈에 모으고, 대칭/미러 수학은 sym_core 가 담당한다.

쓰기(setPoints)는 Undo 가능 커맨드(undo_cmd 플러그인)를 경유한다.
Maya 2023(Python 3.9 / API 2.0)에서 동작하는 API 만 사용한다.
"""

import math
import os

import maya.api.OpenMaya as om
import maya.cmds as cmds

from . import undo_bridge


# undo 커맨드 플러그인 경로(이 파일과 같은 core 폴더의 undo_cmd.py).
_PLUGIN_PATH = os.path.join(os.path.dirname(__file__), "undo_cmd.py")


def ensure_undo_plugin():
    """abSymSetPoints 커맨드가 없으면 플러그인을 로드한다(idempotent).

    런처에서 한 번 로드하지만, DEV reload 로 런처 호출이 누락돼도 커맨드 사용
    직전에 여기서 자가 복구한다. 실패 시 명확한 에러를 던진다.
    """
    if hasattr(cmds, "abSymSetPoints"):
        return
    cmds.loadPlugin(_PLUGIN_PATH, quiet=True)
    if not hasattr(cmds, "abSymSetPoints"):
        raise RuntimeError(
            "Failed to load the undo command plugin: {0}".format(_PLUGIN_PATH))


# ----------------------------------------------------------------------
# DAG / MFnMesh
# ----------------------------------------------------------------------

def get_mfn_mesh(name):
    """transform 또는 mesh shape 이름 -> MFnMesh."""
    sel = om.MSelectionList()
    sel.add(name)
    dag = sel.getDagPath(0)
    # transform 이 넘어오면 첫 shape 로 확장.
    if dag.apiType() == om.MFn.kTransform:
        dag.extendToShape()
    return om.MFnMesh(dag)


def vertex_count(name):
    return get_mfn_mesh(name).numVertices


def _space(world):
    return om.MSpace.kWorld if world else om.MSpace.kObject


# ----------------------------------------------------------------------
# 벌크 정점 좌표 get / set
# ----------------------------------------------------------------------

def get_points(name, world=True):
    """전체 정점 좌표를 [(x, y, z), ...] 로 한 번에 반환(API 호출 1회)."""
    fn = get_mfn_mesh(name)
    pts = fn.getPoints(_space(world))
    return [(p.x, p.y, p.z) for p in pts]


def set_points_undoable(name, points, world=True):
    """전체 정점 좌표를 한 번에 적용한다(Undo 가능 커맨드 경유).

    points: [(x, y, z), ...]  (해당 메시의 정점 수와 길이가 같아야 한다)
    bridge 에 페이로드를 올린 뒤 abSymSetPoints 커맨드를 실행한다.
    커맨드가 old 좌표를 백업하고 setPoints 를 수행하므로 Ctrl+Z 로 복원된다.
    """
    ensure_undo_plugin()
    undo_bridge.PENDING = {
        "mesh": name,
        "points": [(float(p[0]), float(p[1]), float(p[2])) for p in points],
        "world": bool(world),
    }
    cmds.abSymSetPoints()


def set_points_direct(name, points, world=True):
    """Undo 를 거치지 않고 즉시 적용한다(슬라이더 드래그 등 반응성 우선 경로).

    원본도 드래그 중에는 undo 를 끄므로(undoInfo -swf off), 이 경로는 의도적으로
    Undo 큐에 남기지 않는다. 일반 편집은 set_points_undoable 을 쓸 것.
    """
    fn = get_mfn_mesh(name)
    arr = om.MPointArray()
    for p in points:
        arr.append(om.MPoint(float(p[0]), float(p[1]), float(p[2])))
    fn.setPoints(arr, _space(world))


# ----------------------------------------------------------------------
# 표면 최근접점 (closest-point-on-surface) 질의
# ----------------------------------------------------------------------

def closest_surface_points(ref_mesh, query_points, world=True, progress=None):
    """각 query 좌표에 대해 ref_mesh 표면의 최근접점 좌표를 반환한다.

    MFnMesh.getClosestPoint 를 사용(정점이 아니라 표면상의 점이라 토폴로지가
    달라도 매끄럽게 붙는다). query_points 와 같은 공간(world/object)으로 다룬다.

    Args:
        ref_mesh: 레퍼런스 메시명.
        query_points: [(x, y, z), ...].
        world: True 면 월드, False 면 오브젝트 공간.

    Returns:
        [(x, y, z), ...]  (query_points 와 같은 길이/순서)
    """
    fn = get_mfn_mesh(ref_mesh)
    space = _space(world)
    out = []
    total = len(query_points)
    step = max(1, total // 200)
    for k, q in enumerate(query_points):
        if progress is not None and k % step == 0:
            progress(k, total)
        closest, _face = fn.getClosestPoint(
            om.MPoint(float(q[0]), float(q[1]), float(q[2])), space)
        out.append((closest.x, closest.y, closest.z))
    if progress is not None:
        progress(total, total)
    return out


def closest_surface_offsets(base_mesh, query_points, offsets,
                            world=True, power=2.0, progress=None):
    """각 query 좌표에서 base_mesh 표면 최근접점을 찾고, 그 면 정점들의 offsets 를
    역거리가중(IDW)으로 보간한 벡터를 반환한다.

    정점 단위 스냅(nearpoint)과 달리 표면을 따라 부드럽게 보간되어 mesh-flow / wrap
    식 변형 전이가 된다. offsets 는 base_mesh 정점 수와 같은 길이의 (dx,dy,dz) 리스트.

    Args:
        base_mesh: 대응을 찾을 메시(입력0).
        query_points: [(x,y,z), ...] (보통 각 정점의 미러 위치).
        offsets: base 정점별 변형 오프셋 [(dx,dy,dz), ...].
        world: True 면 월드 공간.
        power: IDW 거듭제곱(클수록 최근접 정점에 가깝게).

    Returns:
        query 별 보간 오프셋 [(dx,dy,dz), ...].
    """
    fn = get_mfn_mesh(base_mesh)
    space = _space(world)
    verts = fn.getPoints(space)   # 정점 위치(거리 계산용)
    eps2 = 1e-18
    half_p = power / 2.0
    out = []
    total = len(query_points)
    step = max(1, total // 200)
    for k, q in enumerate(query_points):
        if progress is not None and k % step == 0:
            progress(k, total)
        if not (math.isfinite(q[0]) and math.isfinite(q[1])
                and math.isfinite(q[2])):
            out.append((0.0, 0.0, 0.0))
            continue
        closest, face = fn.getClosestPoint(
            om.MPoint(float(q[0]), float(q[1]), float(q[2])), space)
        face_verts = fn.getPolygonVertices(face)

        # 최근접점이 어느 정점과 일치하면 그 오프셋을 그대로 사용.
        snap = None
        weights = []
        for v in face_verts:
            dv = verts[v] - closest          # MPoint - MPoint -> MVector
            d2 = dv.x * dv.x + dv.y * dv.y + dv.z * dv.z
            if d2 <= eps2:
                snap = v
                break
            weights.append((v, 1.0 / (d2 ** half_p)))

        if snap is not None:
            o = offsets[snap]
            out.append((o[0], o[1], o[2]))
            continue

        total_w = 0.0
        for _v, w in weights:
            total_w += w
        ox = oy = oz = 0.0
        for v, w in weights:
            o = offsets[v]
            f = w / total_w
            ox += o[0] * f
            oy += o[1] * f
            oz += o[2] * f
        out.append((ox, oy, oz))
    if progress is not None:
        progress(total, total)
    return out


# ----------------------------------------------------------------------
# 축 중심(mid) 계산 — origin.mel 과 동일 규칙
# ----------------------------------------------------------------------

def axis_pivot(name, axis_index):
    """오브젝트 월드 pivot(translation)의 해당 축 값."""
    t = cmds.xform(name, q=True, ws=True, t=True)
    return t[axis_index]


def axis_bbox_mid(name, axis_index):
    """월드 bounding box 의 해당 축 중앙값."""
    bb = cmds.xform(name, q=True, ws=True, boundingBox=True)
    # bb = [xmin, ymin, zmin, xmax, ymax, zmax]
    return bb[axis_index] + (bb[axis_index + 3] - bb[axis_index]) / 2.0


# ----------------------------------------------------------------------
# vtx 이름 <-> 인덱스
# ----------------------------------------------------------------------

def vtx_name(mesh, index):
    return "{0}.vtx[{1}]".format(mesh, index)


def vtx_names(mesh, indices):
    return [vtx_name(mesh, i) for i in indices]


def parse_vtx_index(vtx):
    """'obj.vtx[123]' -> 123 (정규식 없이 빠르게)."""
    return int(vtx.rsplit("[", 1)[1].rstrip("]"))


def selected_vertices():
    """현재 선택에서 컴포넌트(정점)를 (mesh, [index,...]) 로 반환.

    정점이 한 메시에만 있다고 가정한다(원본도 동일). 선택이 비었으면 (None, []).
    """
    verts = cmds.filterExpand(sm=31) or []
    if not verts:
        return None, []
    mesh = verts[0].split(".vtx[")[0]
    indices = [parse_vtx_index(v) for v in verts]
    return mesh, indices
