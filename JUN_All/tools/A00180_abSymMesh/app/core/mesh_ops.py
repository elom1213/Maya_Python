# -*- coding: utf-8 -*-
"""
mesh_ops - 지오메트리 편집(반 잘라 미러) 연산.

Make Symmetric Reference 의 'Mirror geometry' 모드 구현.
한쪽 반을 잘라내고 남은 반을 반사 복제·병합해 **토폴로지까지 완전 대칭**인 메시를 만든다.
(snap_core 의 정점 위치 기반 모드와 달리, 실제 지오메트리를 재생성한다.)

cmds 기반(씬 편집). 정점 좌표 IO 는 mesh_io, 반사 계산은 snap_core 를 재사용한다.
"""

import maya.cmds as cmds

from . import mesh_io
from . import snap_core


def mirror_geometry(mesh, axis, mid, positive_source,
                    seam_tol=0.001, merge_tol=0.001):
    """mesh 의 한쪽 반을 잘라내고 미러해 완전 대칭 지오메트리로 만든다.

    절차(원본 레시피):
      1) 시임(평면 근처) 정점을 평면으로 스냅.
      2) 반대쪽 반 정점의 '내부 면'을 삭제.
      3) 남은 반을 반사 복제(노멀 뒤집기).
      4) 합쳐서 시임을 병합.

    Args:
        mesh: 대상 메시(보통 복제본). polyUnite 로 소비되고 결과는 새 transform.
        axis: 0/1/2 = X/Y/Z.
        mid: 대칭 평면의 축 성분값.
        positive_source: True 면 +쪽을 남기고 -쪽 삭제, False 면 반대.
        seam_tol: 평면 위(시임) 정점 판정/스냅 허용 오차.
        merge_tol: 미러 후 시임 병합 거리.

    Returns:
        결과 transform 명.
    """
    pts = mesh_io.get_points(mesh, world=True)

    # 1) 시임(평면 근처) 정점을 평면(mid)으로 스냅.
    snapped = [list(p) for p in pts]
    for q in snapped:
        if abs(q[axis] - mid) <= seam_tol:
            q[axis] = mid
    mesh_io.set_points_undoable(mesh, [tuple(q) for q in snapped], world=True)

    # 2) 삭제할 쪽(시임 제외) 정점의 '내부 면'을 삭제.
    del_idx = []
    keep = 0
    for i, q in enumerate(snapped):
        d = q[axis] - mid
        if (d < -seam_tol) if positive_source else (d > seam_tol):
            del_idx.append(i)
        elif abs(d) > seam_tol:
            keep += 1
    if keep == 0:
        raise RuntimeError(
            "No geometry on the source side. Check Origin / Source side.")
    if del_idx:
        verts = mesh_io.vtx_names(mesh, del_idx)
        faces = cmds.polyListComponentConversion(
            verts, fromVertex=True, toFace=True, internal=True) or []
        if faces:
            cmds.delete(faces)

    # 3) 남은 반을 반사 복제 + 노멀 뒤집기(반사로 winding 이 뒤집혀 면이 안쪽을 향함).
    short = mesh.split("|")[-1]
    dup = cmds.duplicate(mesh, name=short + "_mirHalf")[0]
    dpts = mesh_io.get_points(dup, world=True)
    refl = [snap_core.reflect(p, axis, mid) for p in dpts]
    mesh_io.set_points_undoable(dup, refl, world=True)
    cmds.polyNormal(dup, normalMode=0, ch=False)

    # 4) 합치고 시임 병합.
    result = cmds.polyUnite(mesh, dup, ch=False, mergeUVSets=True)[0]
    cmds.polyMergeVertex(result, distance=merge_tol, ch=False)
    cmds.delete(result, constructionHistory=True)
    return result
