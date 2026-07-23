# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-23
# A00275_skinTool_V01 - 단일 메시 웨이트 전이 (Transfer 탭 코어, UI 비의존)
#
# Kangaroo 의 SkinCluster > Transfer 탭을 흉내낸 기능이되, **Kangaroo 없이** 동작한다.
# 여러 소스 메시로부터 "현재 선택한 하나의 타겟 메시"로 스킨 웨이트를 전이한다.
#
# 핵심 요구:
#   - 타겟 메시의 **선택한 버텍스에만** 전이되게 한다(부분 전이).
#   - 소프트 셀렉션이 켜져 있으면 그 **falloff** 를 블렌드 비율로 반영한다.
#
# 방식 (mayapy 로 검증):
#   cmds.copySkinWeights(surfaceAssociation="closestPoint") 가 최근접 점 기반 전이의 무거운
#   계산(면 barycentric 샘플링)을 정확히 해 준다. 소스 메시 여러 개를 함께 선택하면
#   **버텍스별로 가장 가까운 소스**를 알아서 고른다(검증됨). 다만 copySkinWeights 는
#   컴포넌트 제한을 지원하지 않아 **항상 메시 전체**에 적용된다. 그래서 부분 전이/소프트
#   블렌드는 아래처럼 처리한다.
#     1) 전이 전 웨이트를 bulk 로 스냅샷(before).
#     2) copySkinWeights 로 메시 전체 전이 → after.
#     3) 선택 버텍스는 falloff 비율 f 로 before~after 를 lerp, 나머지는 before 로 복원.
#     4) bulk setWeights.
#   버텍스 선택이 없으면(메시 전체 전이) 2)의 copySkinWeights 결과를 그대로 두어 undo 가
#   깔끔하다. 선택/소프트가 있을 때만 setWeights 로 마스킹한다(그 경우 undo 는 setWeights
#   특성상 세밀하지 않다 — 전체가 한 스텝).

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from Framework.core.maya_undo import undo_chunk


# =========================
# 조회 헬퍼
# =========================

def _is_mesh(node):
    if not node or not cmds.objExists(node):
        return False
    if cmds.objectType(node) == "mesh":
        return True
    return bool(cmds.listRelatives(node, s=True, type="mesh", f=True))


def _mesh_transform(node):
    """메시/셰이프/컴포넌트 이름에서 트랜스폼(또는 메시가 달린 트랜스폼)을 돌려준다."""
    node = node.split(".")[0]
    if cmds.objectType(node) == "mesh":
        p = cmds.listRelatives(node, p=True, f=True)
        return p[0] if p else node
    return node


def _skincluster(mesh):
    if not cmds.objExists(mesh):
        return None
    skins = cmds.ls(cmds.listHistory(mesh, pdo=True) or [], type="skinCluster")
    return skins[0] if skins else None


def _leaf(name):
    return name.split("|")[-1].split(":")[-1]


def _influences(sc):
    return cmds.skinCluster(sc, q=True, inf=True) or []


# =========================
# 선택 파싱 (타겟 메시 + 버텍스 + 소프트 가중치)
# =========================

def parse_target_selection():
    """현재 선택에서 (타겟 메시, 선택 버텍스 ids or None, {vtx: soft weight}) 를 뽑는다.

    - 버텍스/컴포넌트를 선택했으면 그 메시가 타겟, 해당 버텍스가 대상.
    - 메시(트랜스폼/셰이프)를 통째 선택했으면 타겟 전체(ids=None).
    - 소프트 셀렉션이 켜져 있으면 falloff 가중치를 함께 돌려준다.
    """
    sel = cmds.ls(sl=True, l=True) or []
    if not sel:
        return None, None, None

    comps = [s for s in sel if "." in s]
    if comps:
        mesh = _mesh_transform(comps[0])
        verts = cmds.ls(cmds.polyListComponentConversion(comps, tv=True), fl=True) or []
        ids = sorted({int(v.split("[")[1].split("]")[0]) for v in verts})
        soft = _soft_weights(mesh)
        return mesh, (ids or None), soft

    # 메시 통째
    for s in sel:
        if _is_mesh(s):
            return _mesh_transform(s), None, None

    return None, None, None


def _soft_weights(mesh):
    """소프트 셀렉션이 켜져 있으면 {vtx id: falloff weight}, 아니면 None."""
    if not cmds.softSelect(q=True, softSelectEnabled=True):
        return None

    try:
        rich = om.MGlobal.getRichSelection()
        sel = rich.getSelection()
    except Exception:
        return None

    short = _leaf(mesh)
    out = {}
    for i in range(sel.length()):
        try:
            dag, comp = sel.getComponent(i)
        except Exception:
            continue
        if dag.fullPathName().split("|")[-1] != short:
            continue
        if comp.isNull() or not comp.hasFn(om.MFn.kMeshVertComponent):
            continue
        fn = om.MFnSingleIndexedComponent(comp)
        for e in range(fn.elementCount):
            out[fn.element(e)] = fn.weight(e).influence if fn.hasWeights else 1.0

    return out or None


# =========================
# bulk weight 읽기/쓰기 (maya.api)
# =========================

def _sc_fn(sc):
    sel = om.MSelectionList()
    sel.add(sc)
    return oma.MFnSkinCluster(sel.getDependNode(0))


def _mesh_dag_comp(mesh):
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    dag.extendToShape()
    n = cmds.polyEvaluate(mesh, v=True)
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(list(range(n)))
    return dag, comp, n


def _get_all_weights(sc, mesh):
    """(flat MDoubleArray, n_verts, influence 논리인덱스 MIntArray, n_inf)."""
    fn = _sc_fn(sc)
    dag, comp, n = _mesh_dag_comp(mesh)
    weights, n_inf = fn.getWeights(dag, comp)
    infl_dags = fn.influenceObjects()
    idxs = om.MIntArray()
    for d in infl_dags:
        idxs.append(int(fn.indexForInfluenceObject(d)))
    return weights, n, idxs, n_inf


def _set_all_weights(sc, mesh, weights, idxs):
    fn = _sc_fn(sc)
    dag, comp, _n = _mesh_dag_comp(mesh)
    fn.setWeights(dag, comp, idxs, weights, False)


# =========================
# 타겟 skinCluster 준비
# =========================

def _prepare_target_skin(target, union_infs):
    """타겟에 skinCluster 를 보장하고, union_infs 를 모두 인플루언스로 갖게 한다."""
    sc = _skincluster(target)
    if not sc:
        sc = cmds.skinCluster(list(union_infs) + [target], tsb=True,
                              n=_leaf(target) + "_skinCluster")[0]
        return sc, True

    have = set(_leaf(n) for n in _influences(sc))
    for inf in union_infs:
        if _leaf(inf) not in have:
            cmds.skinCluster(sc, e=True, addInfluence=inf, weight=0.0)
            have.add(_leaf(inf))
    return sc, False


# =========================
# 메인 동작
# =========================

def _import_kangaroo(extra=""):
    """kangarooTabTools.weights 를 lazy import. 실패 시 RuntimeError."""
    try:
        import kangarooTabTools.weights as ktw
        return ktw
    except Exception:
        raise RuntimeError(
            "Kangaroo plugin not importable (kangarooTabTools). "
            "Load Kangaroo Builder first{0}.".format(extra))


def transfer_to_mesh(source_meshes, respect_soft=True, engine="native"):
    """소스 메시들 → 현재 선택한 타겟 메시(또는 그 선택 버텍스)로 웨이트를 전이한다.

    engine="native"   : cmds.copySkinWeights + maya.api (플러그인 무의존, 소프트 falloff 지원).
    engine="kangaroo" : Kangaroo transferSkinCluster (플러그인 필요).

    반환: (성공 여부 int, 메시지 str)
    """
    sources = [s for s in (source_meshes or []) if _is_mesh(s)]
    if not sources:
        return 0, "[Warning] Add one or more source meshes (with skinCluster) to the list."

    if engine == "kangaroo":
        return _transfer_to_mesh_kangaroo(sources)

    src_scs = []
    for s in sources:
        sc = _skincluster(s)
        if not sc:
            return 0, "[Warning] Source '{0}' has no skinCluster.".format(_leaf(s))
        src_scs.append(sc)

    target, vtx_ids, soft = parse_target_selection()
    if not target:
        return 0, ("[Warning] Select the target mesh (or its vertices) in the scene "
                   "before transferring.")
    if not _is_mesh(target):
        return 0, "[Warning] Target '{0}' is not a polygon mesh.".format(_leaf(target))
    if _mesh_transform(target) in [_mesh_transform(s) for s in sources]:
        return 0, "[Warning] Target mesh is also in the source list."

    if not respect_soft:
        soft = None

    # 소스 인플루언스 합집합
    union = []
    seen = set()
    for sc in src_scs:
        for inf in _influences(sc):
            if inf not in seen:
                seen.add(inf)
                union.append(inf)

    msgs = []
    try:
        with undo_chunk():
            sc_t, created = _prepare_target_skin(target, union)
            if created:
                msgs.append("created skinCluster on target")

            partial = bool(vtx_ids)   # 버텍스 선택이 있으면 부분 전이

            before = None
            if partial:
                before, n_v, idxs, n_inf = _get_all_weights(sc_t, target)

            # 메시 전체 전이 (버텍스별 최근접 소스)
            cmds.select(sources + [target], r=True)
            cmds.copySkinWeights(
                noMirror=True, surfaceAssociation="closestPoint",
                influenceAssociation=["name", "closestJoint", "oneToOne"])

            if not partial:
                cmds.select(target, r=True)
                return 1, "[Transfer] {0} source(s) -> {1} (whole mesh, closestPoint). {2}".format(
                    len(sources), _leaf(target),
                    "; ".join(msgs) if msgs else "").strip()

            # 부분 전이: 선택 버텍스만 남기고 나머지는 원복 + 소프트 블렌드
            after, _n, idxs2, n_inf2 = _get_all_weights(sc_t, target)

            # copySkinWeights 가 예상 밖으로 인플루언스를 추가하면 before/after 컬럼이
            # 어긋난다. 그 경우 마스킹을 포기하고 전체 전이 결과를 그대로 둔다(정합성 우선).
            if n_inf2 != n_inf or len(after) != len(before):
                cmds.select(target, r=True)
                return 1, ("[Transfer] {0} source(s) -> {1} (whole mesh; influence set "
                           "changed so per-vertex masking was skipped).".format(
                               len(sources), _leaf(target)))

            final = om.MDoubleArray(before)   # 기본은 원본(before) = 미선택 복원

            sel_set = set(vtx_ids)
            for v in vtx_ids:
                f = 1.0
                if soft is not None:
                    f = soft.get(v, 0.0)
                base = v * n_inf
                for i in range(n_inf):
                    b = before[base + i]
                    a = after[base + i]
                    final[base + i] = b + (a - b) * f

            _set_all_weights(sc_t, target, final, idxs)

            cmds.select(target, r=True)
            where = "{0} vert(s)".format(len(sel_set))
            if soft is not None:
                where += ", soft falloff"
            msgs.insert(0, "{0}".format(where))
    except Exception as exc:
        return 0, "[Error] {0}".format(exc)

    return 1, "[Transfer/native] {0} source(s) -> {1} ({2}). {3}".format(
        len(sources), _leaf(target), "; ".join(msgs),
        "(partial uses setWeights; undo is one step)").strip()


# =========================
# Kangaroo 엔진
# =========================

def _transfer_to_mesh_kangaroo(sources):
    """Kangaroo transferSkinCluster 로 소스들 → 현재 선택(타겟)에 전이한다.

    타겟(메시 또는 버텍스)은 씬의 현재 선택을 그대로 쓴다(_pSelection=None). 소스가
    여럿이면 sFrom 에 함께 넘겨 Kangaroo 가 버텍스별 최근접 소스를 처리한다.
    버텍스 선택/컴포넌트 처리·부분 전이는 Kangaroo 쪽 로직을 따른다.
    """
    for s in sources:
        if not _skincluster(s):
            return 0, "[Warning] Source '{0}' has no skinCluster.".format(_leaf(s))

    target, vtx_ids, _soft = parse_target_selection()
    if not target:
        return 0, ("[Warning] Select the target mesh (or its vertices) in the scene "
                   "before transferring.")
    if not _is_mesh(target):
        return 0, "[Warning] Target '{0}' is not a polygon mesh.".format(_leaf(target))
    if _mesh_transform(target) in [_mesh_transform(s) for s in sources]:
        return 0, "[Warning] Target mesh is also in the source list."

    try:
        ktw = _import_kangaroo(extra=" or switch the engine to 'Native'")
    except RuntimeError as exc:
        return 0, "[Error] {0}".format(exc)

    # 타겟에 skinCluster 가 이미 있으면 그걸 쓰고, 없으면 새로 만들게 한다.
    auto_create = _skincluster(target) is None

    try:
        with undo_chunk():
            ktw.transferSkinCluster(
                _pSelection=None,        # 현재 선택 = 타겟(메시/버텍스)
                sFrom=list(sources),
                iMode=2,                 # Closest Point
                iSmoothBorderMask=1,
                bAutoCreateNewSkinCluster=auto_create,
            )
    except Exception as exc:
        return 0, "[Error] {0}".format(exc)

    where = "{0} vert(s)".format(len(vtx_ids)) if vtx_ids else "whole mesh"
    return 1, "[Transfer/kangaroo] {0} source(s) -> {1} ({2}, closestPoint).".format(
        len(sources), _leaf(target), where)
