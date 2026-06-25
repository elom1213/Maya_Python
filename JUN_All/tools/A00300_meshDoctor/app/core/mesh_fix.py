# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-25
# A00300_meshDoctor - 안전 원클릭 수정 (전부 Undo 가능, 선택 메시 대상)
#
# 주의: polyCleanup / Merge 는 토폴로지를 바꿀 수 있다(정점/엣지 추가·삭제).
# 스킨이 걸린 메시는 복제본에서 수정하거나, 수정 후 재바인딩이 필요할 수 있다.
# 각 작업은 undoInfo chunk 로 묶여 Ctrl+Z 한 번에 되돌아간다.

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

from tools.A00300_meshDoctor.app.core.mesh_scan import (
    shape_of, get_object_points, find_nan_indices, find_stray_indices,
    centroid_of, face_quality, AREA_DEGEN, AREA_TINY, QUALITY_EPS,
)


def _selected_meshes():
    sel = cmds.ls(selection=True, long=True) or []
    out, seen = [], set()
    for node in sel:
        shp = shape_of(node)
        if not shp:
            continue
        if cmds.nodeType(node) == "mesh":
            tr = (cmds.listRelatives(node, parent=True, fullPath=True) or [node])[0]
        else:
            tr = node
        if tr not in seen:
            seen.add(tr)
            out.append((tr, shp))
    return out


def _chunk(name, fn):
    """undo chunk 로 묶어 실행. returns 메시지 문자열."""
    meshes = _selected_meshes()
    if not meshes:
        return "No mesh selected."
    cmds.undoInfo(openChunk=True, chunkName=name)
    try:
        return fn(meshes)
    except Exception as e:
        return "{0} failed: {1}".format(name, e)
    finally:
        cmds.undoInfo(closeChunk=True)


# ----------------------------------------------------------------------
# 개별 수정
# ----------------------------------------------------------------------

class MeshFixer:

    # 1) deformer-safe history 삭제 (skinCluster/blendShape 보존, poly history 제거)
    @staticmethod
    def delete_history():
        def _do(meshes):
            done = []
            for tr, _shp in meshes:
                cmds.bakePartialHistory(tr, prePostDeformers=True)
                done.append(tr.split("|")[-1])
            return "Delete History (deformer-safe): {0}".format(", ".join(done))
        return _chunk("MeshDoctor_DeleteHistory", _do)

    # 2) 정점 병합
    @staticmethod
    def merge_vertices(tol=1.0e-4):
        def _do(meshes):
            done = []
            for tr, shp in meshes:
                before = cmds.polyEvaluate(shp, vertex=True)
                cmds.polyMergeVertex("{0}.vtx[*]".format(tr), distance=tol, ch=False)
                after = cmds.polyEvaluate(shp, vertex=True)
                done.append("{0}: {1}->{2}".format(tr.split("|")[-1], before, after))
            return "Merge Vertices (tol={0:g}): {1}".format(tol, "  ".join(done))
        return _chunk("MeshDoctor_MergeVertices", _do)

    # 3) 노멀 정리 (잠금 해제 + conform)
    @staticmethod
    def conform_normals():
        def _do(meshes):
            done = []
            for tr, _shp in meshes:
                cmds.polyNormalPerVertex("{0}.vtx[*]".format(tr), ufn=True)
                cmds.polyNormal(tr, normalMode=2, userNormalMode=0, ch=False)
                done.append(tr.split("|")[-1])
            return "Conform Normals: {0}".format(", ".join(done))
        return _chunk("MeshDoctor_ConformNormals", _do)

    # 4) polyCleanup: non-manifold + lamina + zero-area face + zero-length edge 수정.
    #    (n-gon/concave 는 건드리지 않아 토폴로지 변화를 최소화한다.)
    @staticmethod
    def poly_cleanup():
        def _do(meshes):
            cmds.select([tr for tr, _ in meshes], replace=True)
            # polyCleanupArgList 4 인자 순서(Maya cleanupPolygonOptions 표준):
            # 0 allMeshes, 1 selectOnly(0=fix), 2 historyOn, 3 quads, 4 nsided,
            # 5 concave, 6 holed, 7 nonplanar, 8 zeroGeom, 9 zeroGeomTol,
            # 10 zeroEdge, 11 zeroEdgeTol, 12 zeroMap, 13 zeroMapTol,
            # 14 sharedUVs, 15 nonmanifold, 16 lamina, 17 invalidComponents
            # [1]="1" = perform cleanup (not select-only). quads/nsided=0 이라
            # n-gon 테셀레이션 같은 파괴적 토폴로지 변경은 하지 않는다.
            arg = ('polyCleanupArgList 4 { '
                   '"0","1","1","0","0","0","0","0",'
                   '"1","1e-05","1","1e-05","0","1e-05",'
                   '"0","1","1","0" }')
            mel.eval(arg)
            return "polyCleanup (non-manifold + lamina + zero-area + zero-edge) on " \
                   "{0} mesh(es). Re-Diagnose to confirm.".format(len(meshes))
        return _chunk("MeshDoctor_PolyCleanup", _do)

    # 5) NaN/떠돌이 정점을 centroid 로 스냅 (정점 삭제 없이 위치만 이동 -> bbox 수축).
    @staticmethod
    def snap_stray_verts():
        def _do(meshes):
            done = []
            for tr, shp in meshes:
                points = get_object_points(shp)
                bad = sorted(set(find_nan_indices(points)) |
                             set(find_stray_indices(points)))
                if not bad:
                    done.append("{0}: none".format(tr.split("|")[-1]))
                    continue
                cx, cy, cz = centroid_of(points)
                for i in bad:
                    cmds.xform("{0}.vtx[{1}]".format(tr, i),
                               objectSpace=True, absolute=True, translation=(cx, cy, cz))
                done.append("{0}: {1} snapped".format(tr.split("|")[-1], len(bad)))
            return "Snap NaN/Stray Verts -> centroid: {0}".format("  ".join(done))
        return _chunk("MeshDoctor_SnapStray", _do)

    # ------------------------------------------------------------------
    # 문제 컴포넌트 선택 헬퍼 (셀렉션만 변경, 지오메트리 불변)
    # ------------------------------------------------------------------

    @staticmethod
    def select_non_manifold():
        meshes = _selected_meshes()
        comps = []
        for _tr, shp in meshes:
            comps += (cmds.polyInfo(shp, nonManifoldEdges=True) or [])
            comps += (cmds.polyInfo(shp, nonManifoldVertices=True) or [])
        if not comps:
            return "No non-manifold components."
        # polyInfo 결과 문자열에서 컴포넌트만 추려 선택
        cmds.select(clear=True)
        for _tr, shp in meshes:
            nme = cmds.polyInfo(shp, nonManifoldEdges=True) or []
            for s in nme:
                idx = s.split(":")[0].split()[-1]
                cmds.select("{0}.e[{1}]".format(shp, idx), add=True)
        return "Selected {0} non-manifold component line(s).".format(len(comps))

    @staticmethod
    def select_zero_area_faces():
        # mesh_scan 의 zero_area(슬라이버) 판정과 동일 기준: 형상품질 q 로 거른다.
        meshes = _selected_meshes()
        sel = []
        for tr, shp in meshes:
            try:
                it = om.MItMeshPolygon(_dag(shp))
                while not it.isDone():
                    try:
                        area = it.getArea(om.MSpace.kObject)
                        candidate = area < AREA_TINY
                        try:
                            candidate = candidate or it.zeroArea()
                        except Exception:
                            pass
                        if candidate:
                            q = face_quality(it.getPoints(om.MSpace.kObject), area)
                            if area < AREA_DEGEN or q < QUALITY_EPS:
                                sel.append("{0}.f[{1}]".format(tr, it.index()))
                    except Exception:
                        pass
                    it.next()
            except Exception:
                pass
        if not sel:
            return "No degenerate/sliver faces."
        cmds.select(sel, replace=True)
        return "Selected {0} degenerate/sliver face(s).".format(len(sel))

    @staticmethod
    def select_stray_verts():
        meshes = _selected_meshes()
        sel = []
        for tr, shp in meshes:
            points = get_object_points(shp)
            bad = sorted(set(find_nan_indices(points)) | set(find_stray_indices(points)))
            sel += ["{0}.vtx[{1}]".format(tr, i) for i in bad]
        if not sel:
            return "No stray/NaN vertices."
        cmds.select(sel, replace=True)
        return "Selected {0} stray/NaN vertex(es).".format(len(sel))


def _dag(node):
    sel = om.MSelectionList()
    sel.add(node)
    dag = sel.getDagPath(0)
    if dag.apiType() == om.MFn.kTransform:
        dag.extendToShape()
    return dag
