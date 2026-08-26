# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-26
# A00290_BSTool - Bake Delete 탭 핵심 로직 (maya.cmds + OpenMaya, UI 비의존)
#
# 문제:
#   blendShape -> skinCluster 로 구성된 메시에서 페이스/엣지/버텍스를 지우면 마야는
#   **디포머 뒤에** deleteComponent 를 붙인다.
#
#       blendShape -> skinCluster -> deleteComponent -> <보이는 메시>
#
#   이 상태에서 **보이는 메시와 타겟 메시의 토폴로지가 서로 달라진다**. 리그는 여전히
#   지우기 전 토폴로지로 돌아가고, 지우기는 맨 끝에서 결과만 잘라낸다. 그래서
#   Shape Editor 로 타겟을 편집하거나 타겟 메시를 다시 뽑으면 지우기 전 메시가 나온다.
#
# 이 모듈이 하는 일:
#   지우기를 **체인 맨 앞(중립 셰이프)으로 옮겨** 리그 전체가 처음부터 줄어든 토폴로지로
#   돌게 만든다. 결과 히스토리는
#
#       blendShape -> skinCluster -> <보이는 메시>
#
#   이고 타겟 메시들도 같은 만큼 지워진다. 보이는 모양은 **바뀌지 않는다**(실측: 웨이트
#   조합 · 포즈까지 전부 오차 0).
#
# ==========================================================================
# 어떻게 하는가
# ==========================================================================
#
# 1) 살아남은 정점 찾기 (survivors)
#    deleteComponent 의 **입력 메시**(지우기 전)와 **출력 메시**(지운 뒤)를 플러그 데이터로
#    직접 읽어 위치로 맞춘다. 마야는 컴포넌트를 지울 때 **살아남은 정점의 상대 순서를
#    보존**하므로(실측), 순서를 유지한 채 앞에서부터 훑는 greedy 매칭 하나면 된다.
#    두 메시는 같은 계산 결과라 좌표가 비트 단위로 같다 — 위치 매칭이 흔들릴 여지가 없다.
#
#    그리고 **토폴로지로 검증**한다: 남은 메시의 모든 엣지를 매핑으로 되돌렸을 때 그 두 정점이
#    원본에서 같은 페이스 안에 있어야 한다. 지우기 방식마다 결과가 다르므로 조건을 "같은
#    엣지"가 아니라 "같은 페이스"로 잡는다 — 버텍스를 지우면 페이스가 한 변 줄면서 **없던
#    엣지가 생기고**, 엣지를 지우면 두 페이스가 **병합**된다. 매핑이 한 칸이라도 밀리면
#    여기서 걸린다 — 조용히 틀린 리그를 만들지 않는다.
#
# 2) 줄어든 토폴로지 도너(donor) 만들기
#    **지금 보이는 메시를 복제**한다. 그 자체가 이미 "줄어든 토폴로지 + 올바른 UV/노멀"이다.
#    새로 메시를 조립하면 UV 를 잃는다.
#
# 3) 중립 셰이프(<base>ShapeOrig)와 live 타겟 메시를 도너로 밀어 넣는다
#    도너의 정점만 그 메시의 값으로 바꿔 `donor.outMesh -> dst.inMesh` 로 연결 → 평가 →
#    연결 해제. 해제해도 마지막 데이터가 남는다(실측). 밀어 넣은 뒤에는 그 셰이프의
#    `pnts`(트윅)를 **0 으로 지운다** — `pnts` 인덱스는 지우기 전 번호라 그대로 두면 엉뚱한
#    정점에 옛 오프셋이 얹힌다(실측: live 타겟이 정확히 이 이유로 깨졌다).
#
# 4) 정점 번호를 쓰는 데이터 전부를 다시 매핑
#    - blendShape baked 델타(inputPointsTarget / inputComponentsTarget), 인비트윈 포함
#    - blendShape 페인트 웨이트(baseWeights / targetWeights)
#    - skinCluster 웨이트(weightList) + blendWeights
#    - tweak 노드(vlist[0].vertex)
#    - 디포머 멤버십 — `<orig>.componentTags`(마야 2022+) 와 groupParts 의 컴포넌트 목록
#    - 그 밖의 weightGeometryFilter 의 weightList[g].weights
#
# 5) deleteComponent 를 떼어내고 skinCluster 출력을 셰이프에 바로 잇는다
#
# ==========================================================================
# 함정 (mayapy 2024 실측)
# ==========================================================================
#
# * **skinCluster 웨이트는 DAG 셰이프 정점 수만큼만 읽힌다.** 지우기 뒤 셰이프는 이미 줄어든
#   상태라 `MFnSkinCluster.getWeights` 가 앞쪽 일부만 돌려준다(25개 중 23개). 그래서 읽기
#   전에 **deleteComponent 를 `nodeState = 1`(HasNoEffect)로 잠깐 꺼서** 셰이프를 지우기 전
#   토폴로지로 되돌린 다음 읽는다.
#
# * **밀어 넣은 셰이프의 `pnts` 를 안 지우면 조용히 틀린다** (위 3번).
#
# * **API 쓰기는 undo 에 안 남는다.** 정점 세팅/웨이트 쓰기는 OpenMaya 라 Ctrl+Z 로 완전히
#   되돌아가지 않는다. UI 가 "작업 전에 씬을 저장하라"고 경고한다.

import re

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from Framework.core.maya_undo import undo_chunk
from Framework.core import maya_shape

from . import delta_utils as du


#: 체인 꼬리에서 처리할 수 있는 노드 타입. 이것 말고 다른 게 끼어 있으면 거절한다
#  (polySoftEdge 같은 노드까지 중립에 구워 버리면 노멀/토폴로지가 조용히 달라진다).
#
#  `polyTweak` 이 함께 있는 것은 흔하다 — 히스토리가 있는 메시의 정점을 옮기면 값이 셰이프의
#  `pnts` 로 가는데, 그 뒤에 컴포넌트를 지우면 마야가 그 트윅을 **polyTweak 노드로 옮겨**
#  지우기 앞에 끼워 넣는다(실측). 지우기보다 위에 있으면 정점 번호를 다시 매핑해 주고,
#  아래에 있으면(지운 뒤에 옮긴 경우) 이미 새 번호라 그대로 둔다.
TAIL_TYPES = ("deleteComponent", "polyTweak")

#: 지오메트리 입력을 찾을 때 순서대로 시도하는 어트리뷰트 이름.
_GEO_INPUT_ATTRS = ("inputGeometry", "inputPolymesh", "inMesh")

_COMPONENT_RE = re.compile(r"\[(\d+)(?::(\d+))?\]")


# ==================================================
# 작은 헬퍼
# ==================================================

def _long(name):
    found = cmds.ls(name, l=True) or []
    return found[0] if found else None


def _short(name):
    return name.split("|")[-1].split(":")[-1] if name else name


def _source_plug(dest_plug):
    """destination 플러그에 연결된 source 플러그(롱네임). 없으면 None."""
    srcs = cmds.listConnections(dest_plug, s=True, d=False, p=True) or []
    return srcs[0] if srcs else None


def _geo_input_plug(node):
    """그 노드의 **지오메트리 입력 플러그**. 연결이 있는 것을 고른다. 없으면 None."""
    for attr in _GEO_INPUT_ATTRS:
        plug = "{0}.{1}".format(node, attr)
        if cmds.objExists(plug) and _source_plug(plug):
            return plug
    # 디포머(input[N].inputGeometry)
    idxs = cmds.getAttr(node + ".input", mi=True) if cmds.objExists(node + ".input") else None
    for i in (idxs or []):
        plug = "{0}.input[{1}].inputGeometry".format(node, i)
        if cmds.objExists(plug) and _source_plug(plug):
            return plug
    return None


def _is_mesh_shape(node):
    return cmds.objExists(node) and cmds.objectType(node) == "mesh"


def _is_geometry_filter(node):
    return "geometryFilter" in (cmds.nodeType(node, inherited=True) or [])


def mesh_data_from_plug(plug):
    """플러그가 들고 있는 메시 **데이터**를 (points, faceCounts, faceConnects) 로 읽는다.

    상류가 무엇이든(디포머 · deleteComponent · 셰이프) 그 자리의 지오메트리를 그대로 준다.
    """
    sel = om.MSelectionList()
    sel.add(plug)
    fn = om.MFnMesh(sel.getPlug(0).asMObject())
    pts = [(p.x, p.y, p.z) for p in fn.getPoints(om.MSpace.kObject)]
    counts, connects = fn.getVertices()
    return pts, list(counts), list(connects)


def shape_points(shape):
    """셰이프의 **최종** 오브젝트 공간 포인트(`pnts` 트윅까지 반영)."""
    sel = om.MSelectionList()
    sel.add(shape)
    fn = om.MFnMesh(sel.getDagPath(0))
    return [(p.x, p.y, p.z) for p in fn.getPoints(om.MSpace.kObject)]


def _set_shape_points(shape, points):
    sel = om.MSelectionList()
    sel.add(shape)
    fn = om.MFnMesh(sel.getDagPath(0))
    fn.setPoints(om.MPointArray([om.MPoint(p[0], p[1], p[2]) for p in points]),
                 om.MSpace.kObject)


def _existing_indices(plug):
    if not cmds.objExists(plug):
        return []
    return cmds.getAttr(plug, mi=True) or []


def _target_group_indices(bs_node, geo_idx):
    """그 지오메트리의 inputTargetGroup 인덱스 목록."""
    return _existing_indices("{0}.inputTarget[{1}].inputTargetGroup".format(
        bs_node, geo_idx))


def _parse_vertex_components(comps):
    """['vtx[0]', 'vtx[3:7]'] -> [0, 3, 4, 5, 6, 7]"""
    out = []
    for c in comps:
        match = _COMPONENT_RE.search(c)
        if not match:
            continue
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        out.extend(range(start, end + 1))
    return out


def _clear_pnts(shape):
    """셰이프의 `pnts`(트윅) 를 전부 0 으로. 지운 인덱스 목록을 반환.

    정점마다 setAttr 을 돌리면 9만 정점 메시에서 **40 초**가 넘는다(실측 - 이게 이 탭에서
    가장 느린 곳이었다). 연속 구간을 한 번에 쓰는 `delta_utils.write_tweaks` 로 묶는다.
    """
    sel = om.MSelectionList()
    sel.add(shape)
    plug = om.MFnDependencyNode(sel.getDependNode(0)).findPlug("pnts", False)
    idxs = list(plug.getExistingArrayAttributeIndices())
    if idxs:
        try:
            du.write_tweaks(shape, dict.fromkeys(idxs, (0.0, 0.0, 0.0)))
        except Exception:
            pass
    return idxs


# ==================================================
# 토폴로지 비교
# ==================================================

def faces_from_arrays(counts, connects):
    """(faceCounts, faceConnects) -> [(v0, v1, ...), ...]"""
    faces = []
    k = 0
    for c in counts:
        faces.append(tuple(connects[k:k + c]))
        k += c
    return faces


#: 같은 페이스 안 조합을 전부 세지 않고 테두리만 보는 n-gon 크기 한계(O(n^2) 방지).
_COFACIAL_MAX = 32


def _cofacial_pairs(faces):
    """**같은 페이스에 함께 들어 있는** 정점 쌍 집합(엣지를 포함하는 상위 집합)."""
    pairs = set()
    for f in faces:
        n = len(f)
        if n > _COFACIAL_MAX:
            for i in range(n):
                a, b = f[i], f[(i + 1) % n]
                pairs.add((a, b) if a < b else (b, a))
            continue
        for i in range(n):
            for j in range(i + 1, n):
                a, b = f[i], f[j]
                pairs.add((a, b) if a < b else (b, a))
    return pairs


def _tolerance(points):
    """바운딩 박스 크기에 맞춘 위치 비교 허용 오차 (메시 데이터는 float 저장)."""
    if not points:
        return 1e-5
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    return max(1e-5, span * 1e-5)


def survivors(pre_points, post_points, tol=None):
    """지운 뒤 정점 -> 지우기 전 정점 번호 목록. 못 맞추면 None.

    마야가 **살아남은 정점의 상대 순서를 보존**한다는 성질을 쓴다. 앞에서부터 한 번만
    훑으므로 큰 메시에서도 O(N) 이다.
    """
    if tol is None:
        tol = _tolerance(pre_points)
    out = []
    i = 0
    n = len(pre_points)
    for q in post_points:
        found = -1
        while i < n:
            p = pre_points[i]
            i += 1
            if (abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol
                    and abs(p[2] - q[2]) <= tol):
                found = i - 1
                break
        if found < 0:
            return None
        out.append(found)
    return out


def validate_mapping(surv, pre_faces, post_faces):
    """매핑이 원본 토폴로지와 앞뒤가 맞는지 확인한다. (ok, 첫 실패 설명)

    남은 메시의 모든 엣지를 매핑으로 되돌렸을 때, 그 두 정점이 원본에서 **같은 페이스에
    들어 있어야** 한다. 지우기 방식마다 결과가 다르므로 조건을 "같은 엣지"가 아니라
    "같은 페이스"로 잡는다:

        페이스 삭제 — 남은 페이스가 원본 페이스 그대로다.                 (엣지도 그대로)
        버텍스 삭제 — 그 정점만 빠지고 페이스는 한 변이 줄어든다.        (**새 엣지가 생긴다**)
        엣지 삭제   — 두 페이스가 하나로 합쳐진다.                        (테두리는 원래 엣지)

    세 경우 모두 새로 생기는 엣지의 양 끝은 **원래 한 페이스 안에 있던 정점들**이다.
    매핑이 한 칸이라도 밀리면 이 조건이 곧바로 깨진다.
    """
    pairs = _cofacial_pairs(pre_faces)
    for fi, f in enumerate(post_faces):
        n = len(f)
        for i in range(n):
            a, b = surv[f[i]], surv[f[(i + 1) % n]]
            key = (a, b) if a < b else (b, a)
            if key not in pairs:
                return False, ("face {0}: vertices {1} and {2} never shared a face in "
                               "the original mesh".format(fi, a, b))
    return True, ""


# ==================================================
# 히스토리 분석
# ==================================================

def _tail_chain(shape):
    """셰이프에서 상류로 올라가며 **디포머를 만나기 전까지의 노드들**을 모은다.

    반환: (tail 노드 목록[셰이프에 가까운 순], 첫 tail 의 지오메트리 입력 플러그, 에러 메시지)
    """
    plug = shape + ".inMesh"
    tail = []
    for _ in range(64):
        src = _source_plug(plug)
        if src is None:
            return tail, plug, ""
        node = src.split(".")[0]
        if _is_geometry_filter(node) or _is_mesh_shape(node):
            return tail, plug, ""
        tail.append(node)
        nxt = _geo_input_plug(node)
        if nxt is None:
            # 더 못 올라간다. 노드 타입 검사가 곧 더 나은 메시지를 준다.
            return tail, plug, ""
        plug = nxt
    return tail, plug, "history is deeper than 64 nodes - giving up."


def _deformer_geo_index(deformer, shape):
    """그 디포머에서 우리 셰이프에 해당하는 input 인덱스. 못 찾으면 None."""
    try:
        geos = cmds.deformer(deformer, q=True, g=True) or []
        idxs = cmds.deformer(deformer, q=True, gi=True) or []
    except Exception:
        return None
    for geo, idx in zip(geos, idxs):
        if _long(geo) == shape:
            return int(idx)
    return int(idxs[0]) if len(idxs) == 1 else None


def _walk_to_orig(plug):
    """디포머 입력에서 상류로 올라가 **중립 메시 셰이프**를 찾는다.

    반환: (셰이프 또는 None, 지나온 노드 목록)
    """
    between = []
    for _ in range(64):
        src = _source_plug(plug)
        if src is None:
            return None, between
        node = src.split(".")[0]
        if _is_mesh_shape(node):
            return node, between
        between.append(node)
        nxt = _geo_input_plug(node)
        if nxt is None:
            return None, between
        plug = nxt
    return None, between


# ==================================================
# 분석 리포트
# ==================================================

def analyze(mesh):
    """씬을 건드리지 않고 상황을 조사한다.

    반환: dict. `ok` 가 False 면 `error` 에 이유가 들어 있다(영어 — UI 로그에 그대로 나간다).
    """
    report = {"ok": False, "error": "", "warnings": [], "notes": [],
              "shape": None, "transform": None, "tail": [], "deformers": [],
              "orig_shape": None, "blendshapes": [], "skins": [], "others": [],
              "live_targets": [], "live_with_history": [],
              "deletes": [], "upstream_tail": [], "downstream_tail": [],
              "orig_between": [],
              "pre_count": 0, "post_count": 0, "pre_faces": 0, "post_faces": 0,
              "survivors": None}

    if not mesh or not cmds.objExists(mesh):
        report["error"] = "Pick a mesh first."
        return report

    shape = maya_shape.shape_path(mesh, type_="mesh")
    if not shape:
        report["error"] = "'{0}' has no polygon mesh shape.".format(_short(mesh))
        return report
    report["shape"] = shape
    parents = cmds.listRelatives(shape, p=True, f=True) or []
    report["transform"] = parents[0] if parents else shape

    # ---- 꼬리(지우기) ----
    tail, _plug, err = _tail_chain(shape)
    if err:
        report["error"] = err
        return report
    if not tail:
        report["error"] = ("no deleteComponent found after the deformers - "
                           "this mesh has nothing to bake.")
        return report

    bad = [n for n in tail if cmds.nodeType(n) not in TAIL_TYPES]
    if bad:
        report["error"] = ("unsupported node(s) between the deformers and the mesh: "
                           "{0}. Only deleteComponent (and the polyTweak that carries "
                           "vertex tweaks) is handled.".format(
                               ", ".join("{0} ({1})".format(_short(n), cmds.nodeType(n))
                                         for n in bad)))
        return report

    deletes = [i for i, n in enumerate(tail)
               if cmds.nodeType(n) == "deleteComponent"]
    if not deletes:
        report["error"] = ("no deleteComponent after the deformers - this mesh has "
                           "nothing to bake.")
        return report
    first_del, last_del = min(deletes), max(deletes)

    # tail 은 셰이프에 가까운 쪽부터다. 지우기보다 **위**(상류)에 있는 노드는 지우기 전
    # 번호를 쓰므로 다시 매핑해야 하고, **아래**(하류)면 이미 지운 뒤 번호라 손댈 게 없다.
    # 지우기 사이에 낀 노드는 부분적으로 줄어든 번호라 어느 쪽도 아니다 - 거절한다.
    between = [tail[i] for i in range(first_del + 1, last_del)
               if cmds.nodeType(tail[i]) != "deleteComponent"]
    if between:
        report["error"] = ("{0} sits between two deleteComponent nodes - its vertex "
                           "numbers are only half reduced. Delete the history on this "
                           "mesh's tweaks first.".format(
                               ", ".join(_short(n) for n in between)))
        return report

    report["tail"] = tail
    report["deletes"] = [tail[i] for i in deletes]
    report["upstream_tail"] = tail[last_del + 1:]
    report["downstream_tail"] = tail[:first_del]

    head_plug = _geo_input_plug(tail[last_del])
    report["head_plug"] = head_plug

    src = _source_plug(head_plug) if head_plug else None
    if src is None:
        report["error"] = "could not reach the geometry feeding '{0}'.".format(
            _short(tail[last_del]))
        return report
    report["head_source"] = src

    # ---- 지우기 전 / 뒤 메시 ----
    try:
        pre_pts, pre_counts, pre_conn = mesh_data_from_plug(head_plug)
        post_pts, post_counts, post_conn = mesh_data_from_plug(
            "{0}.outputGeometry".format(tail[first_del]))
    except Exception as exc:
        report["error"] = "could not read the meshes around the delete: {0}".format(exc)
        return report

    report["pre_count"] = len(pre_pts)
    report["post_count"] = len(post_pts)
    report["pre_faces"] = len(pre_counts)
    report["post_faces"] = len(post_counts)

    surv = survivors(pre_pts, post_pts)
    if surv is None:
        report["error"] = ("could not match the vertices before/after the delete "
                           "(the delete may have changed the vertex order).")
        return report

    ok, why = validate_mapping(surv, faces_from_arrays(pre_counts, pre_conn),
                               faces_from_arrays(post_counts, post_conn))
    if not ok:
        report["error"] = "vertex mapping failed validation - {0}".format(why)
        return report
    report["survivors"] = surv

    # ---- 디포머 체인 ----
    deformers = []
    plug = head_plug
    for _ in range(64):
        s = _source_plug(plug)
        if s is None:
            break
        node = s.split(".")[0]
        if _is_mesh_shape(node):
            break
        if _is_geometry_filter(node):
            deformers.append(node)
        nxt = _geo_input_plug(node)
        if nxt is None:
            break
        plug = nxt
    report["deformers"] = deformers
    if not deformers:
        report["error"] = ("no deformer in front of the delete - just use "
                           "Edit > Delete by Type > History instead.")
        return report

    orig, between = _walk_to_orig(plug)
    if orig is None:
        report["error"] = ("could not reach the neutral (orig) mesh at the top of "
                           "the deformer chain.")
        return report
    report["orig_shape"] = orig
    report["orig_between"] = between

    # ---- 디포머별 조사 ----
    seen_live = set()
    for node in deformers:
        ntype = cmds.nodeType(node)
        gi = _deformer_geo_index(node, shape)
        if gi is None:
            report["error"] = ("'{0}' does not report which input drives this mesh."
                               .format(_short(node)))
            return report

        if ntype == "blendShape":
            info = {"node": node, "geo_idx": gi, "live": [], "baked": 0, "targets": 0}
            grp_idxs = _target_group_indices(node, gi)
            info["targets"] = len(grp_idxs)
            for g in grp_idxs:
                group = du.group_plug(node, gi, g)
                for it in du.item_indices(group):
                    item = du.item_plug(group, it)
                    live = du.live_target_shape(item)
                    if live:
                        live = _long(live) or live
                        info["live"].append(live)
                        if live not in seen_live:
                            seen_live.add(live)
                            report["live_targets"].append(live)
                            if _source_plug(live + ".inMesh"):
                                report["live_with_history"].append(live)
                    else:
                        info["baked"] += 1
            report["blendshapes"].append(info)

        elif ntype == "skinCluster":
            geos = cmds.deformer(node, q=True, g=True) or []
            if len(geos) > 1:
                report["error"] = ("skinCluster '{0}' drives {1} meshes - this tab "
                                   "only handles single-mesh skinClusters."
                                   .format(_short(node), len(geos)))
                return report
            infs = cmds.skinCluster(node, q=True, inf=True) or []
            report["skins"].append({"node": node, "geo_idx": gi,
                                    "influences": len(infs)})

        elif ntype == "tweak":
            report["others"].append({"node": node, "type": ntype, "geo_idx": gi})

        else:
            report["others"].append({"node": node, "type": ntype, "geo_idx": gi})
            if "weightGeometryFilter" not in (cmds.nodeType(node, inherited=True) or []):
                report["warnings"].append(
                    "'{0}' ({1}) is not a weighted deformer - if it stores anything "
                    "per vertex it will NOT be remapped.".format(_short(node), ntype))
            else:
                report["notes"].append(
                    "'{0}' ({1}): painted weights will be remapped."
                    .format(_short(node), ntype))

    if report["live_with_history"]:
        report["warnings"].append(
            "{0} live target mesh(es) still have construction history - it will be "
            "deleted so the reduced shape sticks.".format(len(report["live_with_history"])))

    if not report["blendshapes"]:
        report["notes"].append("no blendShape in front of the delete - "
                               "only the neutral mesh and the deformer weights change.")

    report["ok"] = True
    return report


def format_report(report):
    """analyze() 결과를 UI 에 보여 줄 여러 줄 문자열로."""
    if not report.get("ok"):
        return "Not ready: {0}".format(report.get("error") or "unknown problem.")

    lines = []
    lines.append("Mesh        : {0}  ({1})".format(_short(report["transform"]),
                                                   _short(report["shape"])))
    chain = [_short(n) for n in report["tail"]]
    chain += [_short(n) for n in report["deformers"]]
    chain += [_short(report["orig_shape"])]
    lines.append("History     : {0}".format("  <-  ".join(chain)))
    lines.append("Delete nodes: {0}".format(
        ", ".join(_short(n) for n in report["deletes"])))
    kept = [n for n in report["tail"] if n not in report["deletes"]]
    if kept:
        lines.append("Kept in tail: {0}".format(
            ", ".join("{0} ({1})".format(_short(n), cmds.nodeType(n)) for n in kept)))
    lines.append("Vertices    : {0} -> {1}   ({2} removed)".format(
        report["pre_count"], report["post_count"],
        report["pre_count"] - report["post_count"]))
    lines.append("Faces       : {0} -> {1}   ({2} removed)".format(
        report["pre_faces"], report["post_faces"],
        report["pre_faces"] - report["post_faces"]))

    for bs in report["blendshapes"]:
        lines.append("blendShape  : {0}  -  {1} target(s), {2} live mesh(es), "
                     "{3} baked item(s)".format(_short(bs["node"]), bs["targets"],
                                                len(set(bs["live"])), bs["baked"]))
    for sk in report["skins"]:
        lines.append("skinCluster : {0}  -  {1} influence(s)".format(
            _short(sk["node"]), sk["influences"]))
    for other in report["others"]:
        lines.append("deformer    : {0}  ({1})".format(_short(other["node"]),
                                                       other["type"]))
    if report["live_targets"]:
        names = ", ".join(_short(s) for s in report["live_targets"][:8])
        more = "" if len(report["live_targets"]) <= 8 else \
            "  (+{0} more)".format(len(report["live_targets"]) - 8)
        lines.append("Live targets: {0}{1}".format(names, more))

    lines.append("Result      : {0}".format(
        "  <-  ".join([_short(n) for n in report["deformers"]] +
                      [_short(report["orig_shape"])]) or "history removed"))

    for note in report["notes"]:
        lines.append("Note        : {0}".format(note))
    for warn in report["warnings"]:
        lines.append("Warning     : {0}".format(warn))
    return "\n".join(lines)


# ==================================================
# 정점 번호를 쓰는 데이터 다시 매핑
# ==================================================

def _remap_baked_deltas(bs_node, geo_idx, old2new, log):
    """baked 타겟(인비트윈 포함)의 델타 인덱스를 새 번호로. 지워진 정점의 델타는 버린다."""
    changed = 0
    dropped = 0
    for g in _target_group_indices(bs_node, geo_idx):
        group = du.group_plug(bs_node, geo_idx, g)
        for it in du.item_indices(group):
            item = du.item_plug(group, it)
            if du.live_target_shape(item):
                continue
            deltas = du.read_item_deltas(item)
            if deltas is None:
                log("  ! could not read deltas on {0} - left alone".format(item))
                continue
            if not deltas:
                continue
            kept = {}
            for vtx, d in deltas.items():
                new = old2new.get(vtx)
                if new is None:
                    dropped += 1
                else:
                    kept[new] = d
            du.write_baked_deltas(item, kept)
            changed += 1
    return changed, dropped


def _remap_double_multi(plug, old2new, log):
    """정점으로 인덱싱된 double multi(baseWeights / targetWeights / blendWeights) 재매핑.

    쓰기는 연속 구간으로 묶고, 지우기는 **새 값이 덮어쓰지 않는 옛 인덱스만** 한다
    (페인트가 전 정점에 깔린 맵이면 지울 것이 꼬리 몇 개뿐이다).
    """
    idxs = _existing_indices(plug)
    if not idxs:
        return 0

    values = {}
    for i in idxs:
        try:
            values[i] = cmds.getAttr("{0}[{1}]".format(plug, i))
        except Exception:
            pass

    new_values = {}
    for old, val in values.items():
        new = old2new.get(old)
        if new is not None:
            new_values[new] = val

    for start, end in du.contiguous_runs(sorted(new_values)):
        flat = [new_values[i] for i in range(start, end + 1)]
        try:
            if start == end:
                cmds.setAttr("{0}[{1}]".format(plug, start), flat[0])
            else:
                cmds.setAttr("{0}[{1}:{2}]".format(plug, start, end), *flat)
        except Exception as exc:
            log("  ! {0}[{1}:{2}] : {3}".format(plug, start, end, exc))

    for i in set(idxs) - set(new_values):
        try:
            cmds.removeMultiInstance("{0}[{1}]".format(plug, i), b=True)
        except Exception:
            pass
    return len(new_values)


def _remap_double3_multi(plug, old2new, log):
    """정점으로 인덱싱된 double3 multi(tweak.vlist[0].vertex / polyTweak.tweak) 재매핑."""
    idxs = _existing_indices(plug)
    if not idxs:
        return 0

    values = {}
    for i in idxs:
        try:
            values[i] = cmds.getAttr("{0}[{1}]".format(plug, i))[0]
        except Exception:
            pass

    new_values = {}
    for old, val in values.items():
        new = old2new.get(old)
        if new is not None:
            new_values[new] = val

    for start, end in du.contiguous_runs(sorted(new_values)):
        flat = []
        for i in range(start, end + 1):
            flat.extend(new_values[i])
        try:
            if start == end:
                cmds.setAttr("{0}[{1}]".format(plug, start),
                             flat[0], flat[1], flat[2], type="double3")
            else:
                cmds.setAttr("{0}[{1}:{2}]".format(plug, start, end),
                             *flat, type="double3")
        except Exception as exc:
            log("  ! {0}[{1}:{2}] : {3}".format(plug, start, end, exc))

    for i in set(idxs) - set(new_values):
        try:
            cmds.removeMultiInstance("{0}[{1}]".format(plug, i), b=True)
        except Exception:
            pass
    return len(new_values)


def _remap_tweak(node, old2new, log):
    """tweak 노드의 `vlist[0].vertex[i]` 오프셋을 재매핑."""
    return _remap_double3_multi("{0}.vlist[0].vertex".format(node), old2new, log)


def _used_tag_names(deformers, shape):
    """체인의 디포머들이 멤버십으로 **실제 참조하는** 컴포넌트 태그 이름들.

    폴리 프리미티브는 'front' / 'rim' 같은 태그를 기본으로 달고 나오므로, 아무도 안 쓰는
    태그까지 경고하면 로그만 시끄러워진다.
    """
    names = set()
    for node in deformers:
        for i in _existing_indices(node + ".input"):
            plug = "{0}.input[{1}].componentTagExpression".format(node, i)
            if not cmds.objExists(plug):
                continue
            try:
                expr = cmds.getAttr(plug)
            except Exception:
                expr = None
            if expr:
                names.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr))
    return names


def _remap_component_tags(shape, old2new, new_count, log, used_tags=None):
    """셰이프의 **컴포넌트 태그**(Maya 2022+ 디포머 멤버십) 인덱스를 재매핑.

    마야 2022 부터 디포머 멤버십은 groupParts 가 아니라 `<orig>.componentTags[i]` 에
    이름 + 컴포넌트 목록으로 들어간다(실측: `cmds.cluster` 가 groupParts 를 아예 안 만든다).
    태그는 우리가 지오메트리를 밀어 넣는 **중립 셰이프에 그대로 남으므로** 여기서 같이
    고쳐 주지 않으면 디포머가 엉뚱한 정점에 걸린다.
    """
    done = 0
    for i in _existing_indices(shape + ".componentTags"):
        plug = "{0}.componentTags[{1}]".format(shape, i)
        comps = cmds.getAttr(plug + ".componentTagContents") or []
        if not comps or any("*" in c for c in comps):
            continue
        name = cmds.getAttr(plug + ".componentTagName")
        if not all(c.startswith("vtx[") for c in comps):
            if used_tags is None or name in used_tags:
                log("  ! component tag '{0}' on {1} is not vertex based - left alone; "
                    "check the deformer that uses it".format(name, _short(shape)))
            continue
        new = sorted(old2new[v] for v in _parse_vertex_components(comps)
                     if v in old2new)
        if len(new) == new_count:
            cmds.setAttr(plug + ".componentTagContents", 1, "vtx[*]",
                         type="componentList")
        elif new:
            strings = du.component_strings(new)
            cmds.setAttr(plug + ".componentTagContents", len(strings), *strings,
                         type="componentList")
        else:
            cmds.setAttr(plug + ".componentTagContents", 0, type="componentList")
            log("  ! component tag '{0}' on {1} is now empty (all its vertices were "
                "deleted)".format(name, _short(shape)))
        done += 1
    return done


def _remap_group_parts(nodes, old2new, new_count, log):
    """groupParts 의 컴포넌트 목록을 재매핑. `vtx[*]` 는 그대로 둔다."""
    done = 0
    for node in nodes:
        if cmds.nodeType(node) != "groupParts":
            continue
        comps = cmds.getAttr(node + ".inputComponents") or []
        if not comps or any("*" in c for c in comps):
            continue
        if not all(c.startswith("vtx[") for c in comps):
            log("  ! {0}: component list is not vertex based - left alone".format(
                _short(node)))
            continue
        old = _parse_vertex_components(comps)
        new = sorted(old2new[v] for v in old if v in old2new)
        if len(new) == new_count:
            cmds.setAttr(node + ".inputComponents", 1, "vtx[*]", type="componentList")
        else:
            strings = du.component_strings(new)
            cmds.setAttr(node + ".inputComponents", len(strings), *strings,
                         type="componentList")
        done += 1
    return done


# ==================================================
# skinCluster 웨이트
# ==================================================

def _read_skin_weights(skin, shape, vtx_count):
    """(가중치 평면 배열, 인플루언스 수). 호출 전에 셰이프가 **지우기 전** 토폴로지여야 한다."""
    sel = om.MSelectionList()
    sel.add(skin)
    fn = oma.MFnSkinCluster(sel.getDependNode(0))
    n_inf = len(fn.influenceObjects())

    dag = om.MSelectionList().add(shape).getDagPath(0)
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.setCompleteData(vtx_count)
    weights = list(fn.getWeights(dag, comp, om.MIntArray(range(n_inf))))
    return weights, n_inf


def _write_skin_weights(skin, shape, weights, n_inf, vtx_count):
    sel = om.MSelectionList()
    sel.add(skin)
    fn = oma.MFnSkinCluster(sel.getDependNode(0))

    dag = om.MSelectionList().add(shape).getDagPath(0)
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.setCompleteData(vtx_count)
    fn.setWeights(dag, comp, om.MIntArray(range(n_inf)),
                  om.MDoubleArray(weights), False)


def _trim_weight_list(skin, new_count):
    """줄어든 뒤 범위를 벗어난 `weightList[]` 항목을 지운다(파일만 불리는 찌꺼기)."""
    idxs = _existing_indices(skin + ".weightList")
    removed = 0
    for i in idxs:
        if i >= new_count:
            try:
                cmds.removeMultiInstance("{0}.weightList[{1}]".format(skin, i), b=True)
                removed += 1
            except Exception:
                pass
    return removed


# ==================================================
# 실행
# ==================================================

def apply(mesh, log=None):
    """지우기를 리그 전체에 반영하고 deleteComponent 를 떼어낸다.

    Args:
        mesh: 대상 메시(트랜스폼 또는 셰이프).
        log: 진행 상황을 받을 콜백(문자열 하나씩). None 이면 버린다.

    Returns:
        (성공 여부, 리포트 dict)
    """
    log = log or (lambda _m: None)

    report = analyze(mesh)
    if not report["ok"]:
        log(report["error"])
        return False, report

    shape = report["shape"]
    orig = report["orig_shape"]
    deletes = report["deletes"]
    surv = report["survivors"]
    old2new = {old: new for new, old in enumerate(surv)}
    pre_count = report["pre_count"]
    post_count = report["post_count"]

    log("Bake Delete : {0}   {1} -> {2} verts".format(
        _short(report["transform"]), pre_count, post_count))

    # 끝나고 "정말 모양이 그대로인가"를 확인할 기준. 지금 화면에 보이는 그대로를 찍어 둔다.
    try:
        before_pts = shape_points(shape)
    except Exception:
        before_pts = None

    donor = None
    bypassed = []
    with undo_chunk():
        try:
            # ---- 1) 지우기 전 토폴로지로 되돌린 상태에서 웨이트를 읽는다 ----
            #  DAG 셰이프가 이미 줄어 있으면 getWeights 가 앞쪽 일부만 준다.
            for node in deletes:
                cmds.setAttr(node + ".nodeState", 1)
                bypassed.append(node)
            cmds.polyEvaluate(shape, v=True)

            skin_data = []
            for sk in report["skins"]:
                weights, n_inf = _read_skin_weights(sk["node"], shape, pre_count)
                skin_data.append((sk["node"], weights, n_inf))
                log("  read {0} weights x {1} influence(s) from {2}".format(
                    pre_count, n_inf, _short(sk["node"])))

            for node in bypassed:
                cmds.setAttr(node + ".nodeState", 0)
            bypassed = []
            cmds.polyEvaluate(shape, v=True)

            # ---- 2) 줄어든 토폴로지 도너 ----
            donor = cmds.duplicate(report["transform"], name="__JUN_bakeDelete_donor",
                                   returnRootsOnly=True)[0]
            if cmds.listRelatives(donor, p=True):
                donor = cmds.parent(donor, world=True)[0]
            donor = _long(donor)
            donor_shape = (cmds.listRelatives(donor, s=True, ni=True, f=True) or [None])[0]
            if donor_shape is None:
                raise RuntimeError("could not duplicate the mesh to get the reduced "
                                   "topology.")
            # 도너에도 지우기가 딸려 왔으면(히스토리를 물고 온 경우) 굳혀 둔다.
            cmds.delete(donor, ch=True)
            _clear_pnts(donor_shape)
            if int(cmds.polyEvaluate(donor_shape, v=True)) != post_count:
                raise RuntimeError("the duplicated mesh does not match the reduced "
                                   "topology - aborting.")

            used_tags = _used_tag_names(report["deformers"], shape)

            def push(points, dst_shape):
                _set_shape_points(donor_shape, points)
                cmds.connectAttr(donor_shape + ".outMesh", dst_shape + ".inMesh", f=True)
                cmds.polyEvaluate(dst_shape, v=True)
                cmds.disconnectAttr(donor_shape + ".outMesh", dst_shape + ".inMesh")
                _clear_pnts(dst_shape)

            # ---- 3) 중립 셰이프 ----
            orig_pts = shape_points(orig)
            if len(orig_pts) != pre_count:
                raise RuntimeError(
                    "neutral mesh '{0}' has {1} verts but the deformers run on {2} - "
                    "aborting.".format(_short(orig), len(orig_pts), pre_count))
            orig_src = _source_plug(orig + ".inMesh")
            push([orig_pts[o] for o in surv], orig)
            log("  neutral mesh {0} reduced to {1} verts".format(
                _short(orig), post_count))
            tags = _remap_component_tags(orig, old2new, post_count, log,
                                         used_tags=used_tags)
            if tags:
                log("  {0} component tag(s) on {1} remapped".format(tags, _short(orig)))
            if orig_src:
                dead = orig_src.split(".")[0]
                if not (cmds.listConnections(dead, s=False, d=True) or []):
                    cmds.delete(dead)
                    log("  removed leftover history node {0}".format(_short(dead)))

            # ---- 4) live 타겟 메시 ----
            for tshape in report["live_targets"]:
                if _source_plug(tshape + ".inMesh"):
                    parent = (cmds.listRelatives(tshape, p=True, f=True) or [tshape])[0]
                    cmds.delete(parent, ch=True)
                    log("  deleted history on live target {0}".format(_short(tshape)))
                tpts = shape_points(tshape)
                if len(tpts) != pre_count:
                    log("  ! live target {0} has {1} verts (expected {2}) - skipped"
                        .format(_short(tshape), len(tpts), pre_count))
                    continue
                push([tpts[o] for o in surv], tshape)
                _remap_component_tags(tshape, old2new, post_count, log,
                                      used_tags=used_tags)
                log("  live target {0} reduced".format(_short(tshape)))

            # ---- 5) blendShape 데이터 ----
            for bs in report["blendshapes"]:
                node, gi = bs["node"], bs["geo_idx"]
                changed, dropped = _remap_baked_deltas(node, gi, old2new, log)
                log("  {0}: {1} baked item(s) remapped{2}".format(
                    _short(node), changed,
                    ", {0} delta(s) on deleted verts dropped".format(dropped)
                    if dropped else ""))
                base_w = _remap_double_multi(
                    "{0}.inputTarget[{1}].baseWeights".format(node, gi), old2new, log)
                tgt_w = 0
                for g in _target_group_indices(node, gi):
                    tgt_w += _remap_double_multi(
                        "{0}.targetWeights".format(du.group_plug(node, gi, g)),
                        old2new, log)
                if base_w or tgt_w:
                    log("  {0}: painted weights remapped (base {1}, target {2})".format(
                        _short(node), base_w, tgt_w))

            # ---- 6) tweak / 그 밖의 디포머 ----
            for other in report["others"]:
                node, ntype = other["node"], other["type"]
                if ntype == "tweak":
                    n = _remap_tweak(node, old2new, log)
                    if n:
                        log("  tweak {0}: {1} offset(s) remapped".format(_short(node), n))
                elif "weightGeometryFilter" in (cmds.nodeType(node, inherited=True) or []):
                    n = _remap_double_multi(
                        "{0}.weightList[{1}].weights".format(node, other["geo_idx"]),
                        old2new, log)
                    if n:
                        log("  {0}: {1} painted weight(s) remapped".format(
                            _short(node), n))

            # ---- 7) groupParts ----
            group_nodes = set()
            for node in report["deformers"]:
                for plug in (cmds.listConnections(node, s=True, d=False, p=False,
                                                  type="groupParts") or []):
                    group_nodes.add(plug)
            group_nodes.update(n for n in report.get("orig_between", [])
                               if cmds.nodeType(n) == "groupParts")
            n = _remap_group_parts(sorted(group_nodes), old2new, post_count, log)
            if n:
                log("  {0} groupParts component list(s) remapped".format(n))

            # ---- 8) skinCluster 웨이트 ----
            for node, weights, n_inf in skin_data:
                new_w = []
                for o in surv:
                    base = o * n_inf
                    new_w.extend(weights[base:base + n_inf])
                _write_skin_weights(node, shape, new_w, n_inf, post_count)
                _remap_double_multi(node + ".blendWeights", old2new, log)
                trimmed = _trim_weight_list(node, post_count)
                log("  {0}: weights rewritten for {1} verts{2}".format(
                    _short(node), post_count,
                    " ({0} stale entries removed)".format(trimmed) if trimmed else ""))

            # ---- 9) 지우기 위쪽에 있던 polyTweak ----
            #  그 노드의 정점 번호는 아직 지우기 전 번호다. 아래쪽(지운 뒤에 옮긴 것)은
            #  이미 새 번호라 건드리지 않는다.
            for node in report["upstream_tail"]:
                if cmds.nodeType(node) != "polyTweak":
                    continue
                n = _remap_double3_multi(node + ".tweak", old2new, log)
                log("  polyTweak {0}: {1} offset(s) remapped".format(_short(node), n))

            # ---- 10) deleteComponent 떼어내기 ----
            #  입력을 출력이 가던 곳에 바로 이어 준 다음 노드를 지운다. 지우기가 여러 개거나
            #  사이에 polyTweak 이 있어도 배선이 그대로 유지된다.
            for node in deletes:
                src = _source_plug(node + ".inputGeometry")
                dests = cmds.listConnections(node + ".outputGeometry",
                                             s=False, d=True, p=True) or []
                if src:
                    for dst in dests:
                        cmds.connectAttr(src, dst, f=True)
            cmds.delete(deletes)
            log("  removed {0}".format(", ".join(_short(n) for n in deletes)))

            # ---- 11) 다시 평가시키기 ----
            #  `baseWeights` / `targetWeights` 는 setAttr 로 써도 blendShape 가 더러워지지
            #  않는다(실측: 값은 바뀌었는데 화면은 그대로). 명시적으로 흔들어 준다.
            for bs in report["blendshapes"]:
                cmds.dgdirty(bs["node"])
            cmds.dgdirty(shape)

        except Exception as exc:
            for node in bypassed:
                try:
                    cmds.setAttr(node + ".nodeState", 0)
                except Exception:
                    pass
            log("FAILED: {0}".format(exc))
            report["ok"] = False
            report["error"] = str(exc)
            return False, report
        finally:
            # 도너 정리도 같은 undo 스텝 안에서 - Ctrl+Z 로 빈 메시가 되살아나지 않게.
            if donor and cmds.objExists(donor):
                cmds.delete(donor)

    final = int(cmds.polyEvaluate(shape, v=True))
    log("Done. '{0}' now runs on {1} verts with no deleteComponent left.".format(
        _short(report["transform"]), final))

    # 주장과 실제가 어긋나지 않게 - 화면에 보이는 모양이 정말 그대로인지 재 본다.
    if before_pts is not None:
        try:
            after_pts = shape_points(shape)
        except Exception:
            after_pts = None
        if after_pts is None or len(after_pts) != len(before_pts):
            report["warnings"].append("could not re-check the visible shape.")
        else:
            worst = 0.0
            for a, b in zip(after_pts, before_pts):
                worst = max(worst, abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))
            report["deviation"] = worst
            if worst > _tolerance(before_pts):
                log("WARNING: the visible shape moved by {0:.6g} - undo / reload the "
                    "scene and check.".format(worst))
                report["warnings"].append(
                    "the visible shape moved by {0:.6g}.".format(worst))
            else:
                log("  verified: the visible shape is unchanged "
                    "(max deviation {0:.3g}).".format(worst))
    return True, report


class BakeDeleteManager:
    """UI 가 쓰는 얇은 파사드."""

    analyze = staticmethod(analyze)
    apply = staticmethod(apply)
    format_report = staticmethod(format_report)
