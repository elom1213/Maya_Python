# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-06
# A00290_BSTool - blendShape 타겟 델타 공용 유틸 (maya.cmds, UI 비의존)
#
# Base Shape 탭(델타 스케일)과 Mix Targets 탭(다른 타겟을 섞어 넣기)이 함께 쓰는 저수준 도구.
# 두 탭 모두 "타겟의 델타를 바꾼다" 는 같은 일을 하고, 그 방법은 타겟이 어떻게 저장돼
# 있느냐에 따라 갈린다.
#
#   (A) baked 타겟 — 타겟 메시가 씬에 없고 델타만 노드에 굽혀 있다.
#       inputPointsTarget / inputComponentsTarget 을 직접 쓴다.
#
#   (B) live 타겟 — 타겟 메시가 씬에 남아 inputGeomTarget 에 연결돼 있다.
#       inputPointsTarget 은 **연결된 메시에서 매번 다시 계산되는 값**이라 setAttr 로 써도
#       다음 평가에서 조용히 되돌아간다. 그래서 **타겟 메시의 정점을 직접 옮긴다**.
#
# 델타의 공간 (mayapy 실측) — blendShape 의 **origin** 어트리뷰트가 정한다.
#
#     origin = 1 (local, cmds.blendShape 기본) — 델타 = 타겟 로컬 - 베이스 로컬.
#         두 오브젝트의 transform 이 달라도 순수 오브젝트 공간이다.
#     origin = 0 (world) — 델타 = 타겟로컬 * 타겟worldMatrix * 베이스worldInverse - 베이스로컬.
#         즉 **베이스 오브젝트 공간**이라, transform 이 다르면(회전 · 마이너스 스케일 ·
#         비균등 스케일) 타겟 오브젝트 공간이 아니다.
#
#   정점은 자기 오브젝트 공간으로만 옮길 수 있으므로 world origin 이면 되돌려야 한다.
#       local_offset = delta_offset * (base.worldMatrix * target.worldMatrix^-1)  ← 3x3 부분
#
#   그래도 못 잡는 배치가 있을 수 있어(타겟에 디포머가 낀 경우 등), 옮긴 뒤 **델타가 정말
#   기대값이 됐는지 검증**하고, 아니면 되돌린 뒤 타겟 정점을 x/y/z 로 한 번씩 밀어 응답
#   행렬을 **직접 재서** 다시 시도한다(변환은 선형이라 3번이면 3x3 이 나온다).
#   그래도 아니면 원상복구하고 이유를 돌려준다 — 조용히 틀린 모양을 만들지 않는다.

import re

import maya.cmds as cmds
import maya.api.OpenMaya as om


_COMPONENT_RE = re.compile(r"\[(\d+)(?::(\d+))?\]")

#: weight 1.0 짜리 아이템 인덱스. inputTargetItem 인덱스 = 5000 + 1000 * inbetween weight.
FULL_ITEM = 6000

#: 델타 검증 허용 오차. inputPointsTarget 은 float 로 저장돼 상대 오차가 있으므로
#  값이 클수록 함께 키운다.
_TOL = 1e-4

#: 응답 행렬을 잴 때 정점을 미는 거리(오브젝트 공간). 변환은 선형이라 크기는 무관하고,
#  잰 뒤 곧바로 되돌린다.
_PROBE_STEP = 1.0


# ==================================================
# 컴포넌트 목록
# ==================================================

def expand_components(comps, count):
    """inputComponentsTarget(['vtx[0]', 'vtx[3:7]', ...]) 을 정점 인덱스 목록으로 편다.

    comps 가 비어 있으면(가끔 그렇다) 0..count-1 로 본다 — 마야가 델타를 그 순서로
    담기 때문이다. 편 개수가 델타 개수와 맞지 않으면 None 을 돌려 호출부가 건너뛴다.
    """
    if not comps:
        return list(range(count))

    out = []
    for c in comps:
        match = _COMPONENT_RE.search(c)
        if not match:
            return None
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        out.extend(range(start, end + 1))

    return out if len(out) == count else None


def contiguous_runs(indices):
    """정렬된 인덱스를 연속 구간 [(start, end), ...] 으로 묶는다."""
    runs = []
    start = prev = None
    for i in indices:
        if start is None:
            start = prev = i
        elif i == prev + 1:
            prev = i
        else:
            runs.append((start, prev))
            start = prev = i
    if start is not None:
        runs.append((start, prev))
    return runs


def component_strings(indices):
    """정렬된 정점 인덱스를 componentList 문자열로 압축한다."""
    return ["vtx[{0}]".format(a) if a == b else "vtx[{0}:{1}]".format(a, b)
            for a, b in contiguous_runs(indices)]


# ==================================================
# 플러그 경로
# ==================================================

def group_plug(bs_node, geo_idx, grp_idx):
    return "{0}.inputTarget[{1}].inputTargetGroup[{2}]".format(
        bs_node, geo_idx, grp_idx)


def item_plug(group, item_idx):
    return "{0}.inputTargetItem[{1}]".format(group, item_idx)


def item_indices(group):
    return cmds.getAttr(group + ".inputTargetItem", multiIndices=True) or []


def primary_item_index(group):
    """그 타겟의 **완성 모양**(weight 1.0) 아이템 인덱스. 아이템이 없으면 None.

    인비트윈이 있으면 아이템이 여러 개다. 6000(=weight 1.0)이 있으면 그것을, 없으면
    가장 큰 인덱스(= 가장 강한 모양)를 쓴다.
    """
    items = item_indices(group)
    if not items:
        return None
    return FULL_ITEM if FULL_ITEM in items else max(items)


def live_target_shape(plug):
    """inputGeomTarget 에 연결된 타겟 셰이프. 연결이 없으면 None(= baked)."""
    srcs = cmds.listConnections(plug + ".inputGeomTarget",
                                source=True, destination=False,
                                shapes=True) or []
    return srcs[0] if srcs else None


def base_input_shape(bs_node, geo_idx):
    """blendShape 에 **들어오는** 베이스 지오메트리 셰이프 = 중립 모양을 들고 있는 노드.

    보통 '<base>ShapeOrig' 인터미디어트 셰이프다(스킨이 걸린 리깅 메시도 마찬가지 —
    blendShape 이 체인 앞에 있으면 입력은 언제나 바인드 셰이프다).
    상류가 메시가 아니면(다른 디포머 뒤에 blendShape 이 있는 경우) None — 그 중립은
    계산 결과라 정적으로 옮길 수 없다.
    """
    srcs = cmds.listConnections(
        "{0}.input[{1}].inputGeometry".format(bs_node, geo_idx),
        source=True, destination=False, shapes=True) or []
    if srcs and cmds.objectType(srcs[0]) == "mesh":
        return srcs[0]
    return None


def base_shape_for_geo(bs_node, geo_idx):
    """이 inputTarget 인덱스가 디포밍하는 베이스 셰이프 이름."""
    geos = cmds.blendShape(bs_node, query=True, geometry=True) or []
    idxs = cmds.blendShape(bs_node, query=True, geometryIndices=True) or []
    for geo, idx in zip(geos, idxs):
        if idx == geo_idx:
            return geo
    return geos[0] if len(geos) == 1 else None


# ==================================================
# 델타 읽기 / 쓰기
# ==================================================

def read_item_deltas(plug):
    """델타를 {정점: (dx, dy, dz)} 로 읽는다.

    컴포넌트 목록을 델타 개수만큼 펴지 못하면 None(호출부가 건너뛴다).
    """
    pts = cmds.getAttr(plug + ".inputPointsTarget") or []
    if not pts:
        return {}

    comps = cmds.getAttr(plug + ".inputComponentsTarget") or []
    indices = expand_components(comps, len(pts))
    if indices is None:
        return None

    return {vtx: (pts[k][0], pts[k][1], pts[k][2])
            for k, vtx in enumerate(indices)}


def write_baked_deltas(plug, deltas):
    """{정점: (x, y, z)} 를 baked 타겟(델타만 굽힌 타겟)에 그대로 써 넣는다.

    포인트 배열과 컴포넌트 목록은 **같은 순서**여야 하므로 정점 번호 순으로 함께 쓴다.
    거의 0 인 델타는 버려 목록이 불필요하게 커지지 않게 한다.
    """
    verts = sorted(v for v, d in deltas.items()
                   if abs(d[0]) > 1e-9 or abs(d[1]) > 1e-9 or abs(d[2]) > 1e-9)
    if not verts:
        # 남는 델타가 없다 = 타겟이 베이스와 같아졌다. 빈 배열로 비운다.
        cmds.setAttr(plug + ".inputPointsTarget", 0, type="pointArray")
        cmds.setAttr(plug + ".inputComponentsTarget", 0, type="componentList")
        return 0

    pts = []
    for v in verts:
        d = deltas[v]
        pts.append((d[0], d[1], d[2], 1.0))
    comps = component_strings(verts)

    cmds.setAttr(plug + ".inputPointsTarget", len(pts), *pts, type="pointArray")
    cmds.setAttr(plug + ".inputComponentsTarget", len(comps), *comps,
                 type="componentList")
    return len(pts)


def scale_baked_item(plug, factor):
    """baked 아이템의 inputPointsTarget 을 factor 배. 반환: 처리한 포인트 수.

    벡터를 배율하는 것뿐이라 델타가 어느 공간에 있든 결과가 같다.
    """
    pts = cmds.getAttr(plug + ".inputPointsTarget") or []
    if not pts:
        return 0

    new_pts = []
    for p in pts:
        w = p[3] if len(p) > 3 else 1.0
        new_pts.append((p[0] * factor, p[1] * factor, p[2] * factor, w))

    cmds.setAttr(plug + ".inputPointsTarget",
                 len(new_pts), *new_pts, type="pointArray")
    return len(new_pts)


# ==================================================
# 타겟 메시의 tweak(pnts)
# ==================================================

def read_tweaks(shape):
    """shape.pnts 의 **실제로 존재하는 element** 만 {idx: (x, y, z)} 로 읽는다.

    getAttr(".pnts") 통짜 조회는 "compound with mixed type elements" 로 실패하고
    정점마다 getAttr 을 돌리면 느리다(A00380 peak_manager 와 같은 방식).
    """
    tweaks = {}
    try:
        sel = om.MSelectionList()
        sel.add(shape)
        node = sel.getDependNode(0)
        plug = om.MFnDependencyNode(node).findPlug("pnts", False)
        for i in plug.getExistingArrayAttributeIndices():
            ep = plug.elementByLogicalIndex(i)
            tweaks[i] = (ep.child(0).asFloat(),
                         ep.child(1).asFloat(),
                         ep.child(2).asFloat())
    except Exception:
        pass
    return tweaks


def write_tweaks(shape, values):
    """{idx: (x, y, z)} 를 shape.pnts 에 쓴다. 연속 인덱스는 구간 setAttr 로 묶는다.

    정점마다 setAttr/xform 을 돌리면 19k 메시에서 6 초대, 구간으로 묶으면 0.1 초대다.
    메시 데이터(vrts)가 아니라 tweak 에만 쓰므로 undo 도 정확히 맞는다.
    """
    for start, end in contiguous_runs(sorted(values.keys())):
        flat = []
        for i in range(start, end + 1):
            flat.extend(values[i])
        if start == end:
            cmds.setAttr("{0}.pnts[{1}]".format(shape, start),
                         flat[0], flat[1], flat[2], type="double3")
        else:
            cmds.setAttr("{0}.pnts[{1}:{2}]".format(shape, start, end),
                         *flat, type="double3")


# ==================================================
# 델타 공간
# ==================================================

def delta_to_local_matrix(bs_node, geo_idx, shape):
    """델타 공간의 변위를 **타겟 오브젝트 공간** 변위로 바꾸는 행렬(없으면 None).

    origin=local 이면 델타가 이미 타겟 오브젝트 공간이라 변환이 필요 없다.
    origin=world 면 델타가 베이스 오브젝트 공간이므로 base.world * target.world^-1 로
    되돌린다. 두 transform 이 같으면(대개 그렇다) 항등이라 None 을 준다.
    """
    try:
        if cmds.getAttr(bs_node + ".origin") != 0:      # 0 = world, 1 = local
            return None
    except Exception:
        return None

    base_shape = base_shape_for_geo(bs_node, geo_idx)
    if not base_shape:
        return None

    try:
        base_m = om.MMatrix(cmds.getAttr(base_shape + ".worldMatrix[0]"))
        tgt_m = om.MMatrix(cmds.getAttr(shape + ".worldMatrix[0]"))
    except Exception:
        return None

    mat = base_m * tgt_m.inverse()
    return None if mat.isEquivalent(om.MMatrix.kIdentity, 1e-6) else mat


def measure_local_matrix(plug, shape, probe, probe_tweak):
    """타겟 정점을 실제로 흔들어 '로컬 변위 -> 델타 변위' 응답을 재고, 그 역행렬을 준다.

    계산으로 못 맞추는 배치를 위한 폴백. 변환은 선형이라 정점 하나를 x/y/z 로 한 번씩
    밀어 보면 3x3 이 그대로 나온다. 잰 뒤에는 원래 tweak 으로 되돌린다.
    """
    before = read_item_deltas(plug)
    if before is None:
        return None
    d0 = before.get(probe, (0.0, 0.0, 0.0))

    rows = []
    try:
        for axis in range(3):
            moved = list(probe_tweak)
            moved[axis] += _PROBE_STEP
            write_tweaks(shape, {probe: tuple(moved)})

            after = read_item_deltas(plug)
            if after is None:
                return None
            d1 = after.get(probe, (0.0, 0.0, 0.0))
            rows.append([(d1[i] - d0[i]) / _PROBE_STEP for i in range(3)])
    finally:
        write_tweaks(shape, {probe: tuple(probe_tweak)})

    mat = om.MMatrix([rows[0][0], rows[0][1], rows[0][2], 0.0,
                      rows[1][0], rows[1][1], rows[1][2], 0.0,
                      rows[2][0], rows[2][1], rows[2][2], 0.0,
                      0.0, 0.0, 0.0, 1.0])
    if abs(mat.det3x3()) < 1e-9:
        return None
    return mat.inverse()


def offset_target_mesh(shape, offsets, saved, mat):
    """타겟 정점을 offsets(델타 공간)만큼, 필요하면 mat 로 공간을 되돌려 옮긴다."""
    values = {}
    for vtx, off in offsets.items():
        vec = om.MVector(off[0], off[1], off[2])
        if mat is not None:
            vec = vec * mat
        bx, by, bz = saved.get(vtx, (0.0, 0.0, 0.0))
        values[vtx] = (bx + vec.x, by + vec.y, bz + vec.z)
    write_tweaks(shape, values)


def deltas_match(plug, expected):
    """델타가 정말 expected 가 됐는지 확인한다(정점 번호로 대조).

    스케일 뒤 아주 작아진 델타는 마야가 목록에서 걷어낼 수 있으므로 위치가 아니라
    **정점 번호로** 대조하고, 없는 정점은 0 으로 본다. 기대하지 않은 정점이 움직인
    경우도 잡도록 양쪽 정점의 합집합을 본다.
    """
    after = read_item_deltas(plug)
    if after is None:
        return False

    for vtx in set(expected) | set(after):
        exp = expected.get(vtx, (0.0, 0.0, 0.0))
        got = after.get(vtx, (0.0, 0.0, 0.0))
        for i in range(3):
            if abs(got[i] - exp[i]) > _TOL * max(1.0, abs(exp[i])):
                return False
    return True


def offset_base_mesh(shape, offsets):
    """중립(베이스) 셰이프의 정점을 offsets 만큼 옮긴다. 반환: 옮긴 정점 수.

    **공간 변환이 필요 없다** — blendShape 은 output = base_point + Σ(weight * delta) 로
    델타를 베이스 포인트에 그대로 더한다. 즉 델타와 베이스 포인트는 정의상 같은 공간이다.
    (mayapy 실측: 스킨 유무 · origin local/world · 베이스 회전 8조합에서, 중립을 V 만큼
    옮기면 안 움직인 live 타겟의 델타가 정확히 -V 만큼 변한다 = 같은 공간.)

    타겟 메시 쪽(apply_live_offsets)과 달리 여기서는 검증이 필요 없다. 저장된 포인트를
    직접 옮기는 것이라 재계산되지 않기 때문이다.
    """
    tweaks = read_tweaks(shape)
    values = {}
    for vtx, off in offsets.items():
        bx, by, bz = tweaks.get(vtx, (0.0, 0.0, 0.0))
        values[vtx] = (bx + off[0], by + off[1], bz + off[2])
    if values:
        write_tweaks(shape, values)
    return len(values)


def duplicate_with_offsets(shape, offsets, name):
    """중립 셰이프를 복제해 offsets 를 적용한 **새 메시**를 만든다(리그는 건드리지 않는다).

    복제본의 포인트를 하나하나 명시적으로 세팅하므로, duplicate 가 무엇을 가져왔든
    결과는 '중립 + offsets' 로 확정된다. 반환: 새 transform 이름(실패하면 None).
    """
    sel = om.MSelectionList()
    sel.add(shape)
    src_fn = om.MFnMesh(sel.getDagPath(0))
    points = src_fn.getPoints(om.MSpace.kObject)

    for vtx, off in offsets.items():
        if 0 <= vtx < len(points):
            p = points[vtx]
            points[vtx] = om.MPoint(p.x + off[0], p.y + off[1], p.z + off[2])

    parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
    if not parents:
        return None

    dup = cmds.duplicate(parents[0], name=name, upstreamNodes=False,
                         returnRootsOnly=True)[0]
    # 히스토리와 인터미디어트 셰이프를 걷어내 순수한 메시 하나만 남긴다.
    try:
        cmds.delete(dup, constructionHistory=True)
    except Exception:
        pass
    shapes = cmds.listRelatives(dup, shapes=True, fullPath=True) or []
    for s in shapes:
        if cmds.getAttr(s + ".intermediateObject"):
            cmds.delete(s)
    shapes = cmds.listRelatives(dup, shapes=True, fullPath=True) or []
    if not shapes:
        return None

    dst = om.MSelectionList()
    dst.add(shapes[0])
    om.MFnMesh(dst.getDagPath(0)).setPoints(points, om.MSpace.kObject)
    return dup


def apply_live_offsets(bs_node, geo_idx, plug, shape, offsets, expected):
    """live 타겟 메시를 offsets(델타 공간)만큼 옮겨 델타가 expected 가 되게 한다.

    공간을 계산으로 되돌려 옮기고 검증한다. 어긋나면 되돌린 뒤 응답 행렬을 직접 재서
    한 번 더 시도하고, 그래도 아니면 원상복구한다.

    반환: (성공 여부, 실패 사유 또는 None)
    """
    if not offsets:
        return True, None

    tweaks = read_tweaks(shape)
    saved = {vtx: tweaks.get(vtx, (0.0, 0.0, 0.0)) for vtx in offsets}

    try:
        mat = delta_to_local_matrix(bs_node, geo_idx, shape)
        offset_target_mesh(shape, offsets, saved, mat)
        if deltas_match(plug, expected):
            return True, None

        # 공간 가정이 틀렸다. 되돌리고 응답을 직접 재서 다시.
        write_tweaks(shape, saved)
        probe = max(offsets, key=lambda v: sum(c * c for c in offsets[v]))
        measured = measure_local_matrix(plug, shape, probe, saved[probe])
        if measured is not None:
            offset_target_mesh(shape, offsets, saved, measured)
            if deltas_match(plug, expected):
                return True, None

        write_tweaks(shape, saved)
    except Exception as exc:
        return False, "could not move target mesh '{0}' ({1})".format(shape, exc)

    return False, ("'{0}' left unchanged - moving its vertices does not change the"
                   " deltas as expected (target mesh may be deformed or"
                   " constrained)".format(shape))
