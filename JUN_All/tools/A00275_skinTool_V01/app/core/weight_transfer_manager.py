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
    """메시/셰이프/컴포넌트 이름에서 트랜스폼을 **풀 패스로** 돌려준다.

    풀 패스로 정규화하는 이유: 소스 제외 필터가 TSL 이름(숏네임일 수 있음)과 선택 파싱
    결과(ls -l 풀 패스)를 비교하는데, 표기가 다르면 소스를 대상에서 못 걸러내 자기 자신에
    전이하려다 실패한다.
    """
    node = node.split(".")[0]
    if cmds.objectType(node) == "mesh":
        p = cmds.listRelatives(node, p=True, f=True)
        node = p[0] if p else node
    ls = cmds.ls(node, l=True)
    return ls[0] if ls else node


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

    (단일 대상용. 여러 대상은 parse_target_selections 를 쓴다.)
    """
    targets = parse_target_selections()
    return targets[0] if targets else (None, None, None)


def parse_target_selections():
    """현재 선택을 **대상 메시별로 그룹핑**해 [(mesh, vtx_ids or None, soft), ...] 를 돌려준다.

    - 여러 메시를 통째로 선택하면 각 메시가 전이 대상(각각 ids=None).
    - 어떤 메시의 버텍스/컴포넌트를 선택하면 그 메시는 부분 전이(선택 버텍스만).
    - 소프트 셀렉션이 켜져 있으면 메시별 falloff 가중치를 함께 담는다.
    """
    sel = cmds.ls(sl=True, l=True) or []
    if not sel:
        return []

    comps = [s for s in sel if "." in s]
    wholes = [s for s in sel if "." not in s and _is_mesh(s)]

    result = []
    seen = set()

    # 컴포넌트(버텍스) 선택 → 메시별 부분 전이
    comp_by_mesh = {}
    for c in comps:
        comp_by_mesh.setdefault(_mesh_transform(c), []).append(c)

    for mesh, cs in comp_by_mesh.items():
        verts = cmds.ls(cmds.polyListComponentConversion(cs, tv=True), fl=True) or []
        ids = sorted({int(v.split("[")[1].split("]")[0]) for v in verts})
        result.append((mesh, ids or None, _soft_weights(mesh)))
        seen.add(mesh)

    # 통째 선택된 메시 → 전체 전이 (이미 부분으로 잡힌 메시는 건너뜀)
    for w in wholes:
        mesh = _mesh_transform(w)
        if mesh in seen:
            continue
        result.append((mesh, None, None))
        seen.add(mesh)

    return result


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

    targets = parse_target_selections()
    if not targets:
        return 0, ("[Warning] Select the target mesh(es) (or their vertices) in the "
                   "scene before transferring.")

    # 소스로 쓰인 메시는 대상에서 제외한다.
    src_transforms = {_mesh_transform(s) for s in sources}
    targets = [t for t in targets if _mesh_transform(t[0]) not in src_transforms]
    if not targets:
        return 0, "[Warning] The selected target(s) are all in the source list."

    # 소스 인플루언스 합집합
    union = []
    seen = set()
    for sc in src_scs:
        for inf in _influences(sc):
            if inf not in seen:
                seen.add(inf)
                union.append(inf)

    done = 0
    warns = []
    detail = []
    try:
        # 선택한 모든 대상 메시를 한 번의 undo 로 묶어 전이한다.
        with undo_chunk():
            for mesh, vtx_ids, soft in targets:
                if not respect_soft:
                    soft = None
                note = _transfer_one_native(sources, union, mesh, vtx_ids, soft)
                done += 1
                detail.append("{0}({1})".format(_leaf(mesh), note))
    except Exception as exc:
        return 0, "[Error] {0} (after {1} mesh(es))".format(exc, done)

    return 1, "[Transfer/native] {0} source(s) -> {1} target(s): {2}".format(
        len(sources), done, ", ".join(detail))


def _transfer_one_native(sources, union, target, vtx_ids, soft):
    """소스들 → 대상 메시 하나에 전이한다(부분/소프트 마스킹 포함). 짧은 설명 문자열 반환."""

    sc_t, created = _prepare_target_skin(target, union)
    partial = bool(vtx_ids)   # 버텍스 선택이 있으면 부분 전이

    before = idxs = None
    n_inf = 0
    if partial:
        before, _n_v, idxs, n_inf = _get_all_weights(sc_t, target)

    # 메시 전체 전이 (소스가 여럿이면 버텍스별 최근접 소스)
    cmds.select(list(sources) + [target], r=True)
    cmds.copySkinWeights(
        noMirror=True, surfaceAssociation="closestPoint",
        influenceAssociation=["name", "closestJoint", "oneToOne"])

    if not partial:
        return "whole" + (", new sc" if created else "")

    # 부분 전이: 선택 버텍스만 남기고 나머지는 원복 + 소프트 블렌드
    after, _n, _idxs2, n_inf2 = _get_all_weights(sc_t, target)

    # copySkinWeights 가 예상 밖으로 인플루언스를 추가하면 before/after 컬럼이 어긋난다.
    # 그 경우 마스킹을 포기하고 전체 전이 결과를 그대로 둔다(정합성 우선).
    if n_inf2 != n_inf or len(after) != len(before):
        return "whole (masking skipped: influence set changed)"

    final = om.MDoubleArray(before)   # 기본은 원본(before) = 미선택 복원
    for v in vtx_ids:
        f = soft.get(v, 0.0) if soft is not None else 1.0
        base = v * n_inf
        for i in range(n_inf):
            b = before[base + i]
            a = after[base + i]
            final[base + i] = b + (a - b) * f

    _set_all_weights(sc_t, target, final, idxs)

    where = "{0}v".format(len(vtx_ids))
    if soft is not None:
        where += "+soft"
    return where


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

    # Kangaroo transferSkinCluster 는 _pSelection=None 이면 현재 선택 전체(여러 메시/버텍스)를
    # 대상으로 처리한다. 여기서는 검증/메시지용으로만 대상 목록을 확인한다.
    src_transforms = {_mesh_transform(s) for s in sources}
    targets = [t for t in parse_target_selections()
               if _mesh_transform(t[0]) not in src_transforms]
    if not targets:
        return 0, ("[Warning] Select the target mesh(es) (or their vertices) in the "
                   "scene before transferring.")

    try:
        ktw = _import_kangaroo(extra=" or switch the engine to 'Native'")
    except RuntimeError as exc:
        return 0, "[Error] {0}".format(exc)

    # 대상 중 하나라도 skinCluster 가 없으면 Kangaroo 가 새로 만들게 한다.
    auto_create = any(_skincluster(m) is None for m, _ids, _s in targets)

    try:
        with undo_chunk():
            ktw.transferSkinCluster(
                _pSelection=None,        # 현재 선택 = 타겟(들)
                sFrom=list(sources),
                iMode=2,                 # Closest Point
                iSmoothBorderMask=1,
                bAutoCreateNewSkinCluster=auto_create,
            )
    except Exception as exc:
        return 0, "[Error] {0}".format(exc)

    return 1, "[Transfer/kangaroo] {0} source(s) -> {1} target(s) (closestPoint).".format(
        len(sources), len(targets))
