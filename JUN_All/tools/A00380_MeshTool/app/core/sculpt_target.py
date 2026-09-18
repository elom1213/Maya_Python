# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00380_MeshTool - blendShape 타겟 Edit(sculpt) 모드인 메시에 버텍스 이동을 써 넣는다
#
# 마야 Shape Editor(또는 A00290 Shape Editor 탭)에서 타겟 Edit 를 켜면 `sculptTarget` 이
# 셰이프의 `tweakLocation` 을 `<bs>.inputTarget[g].vertex[0]` 에 연결한다. 이때부터
# 셰이프의 `.pnts` 는 평범한 tweak 가 아니다 (Maya 2024 mayapy 실측):
#
#   - `setAttr shape.pnts[..]` : 값이 타겟 델타에 **더해지고**(절대값 아님) 명령은
#     `RuntimeError: Maya command error` 를 낸다. 구간 쓰기는 일부 원소가 빠지기도 한다.
#   - `move -r -os vtx` : 정상. 이동량 d 가 그대로 편집 중인 아이템의 inputPointsTarget 에
#     더해진다. 하지만 버텍스 1만 개에 11초, undo 14초라 일괄 적용에는 못 쓴다.
#   - `xform -os -t vtx` : 타겟에 안 들어가고 다른 곳으로 빠진다.
#
# 그래서 마야가 `move` 로 하는 일을 **한 번에** 한다 — 편집 중인 아이템의 델타에 d 를 더해
# inputPointsTarget / inputComponentsTarget 을 setAttr 두 번으로 쓴다(undo 가능).
#
# 마야 `move` 의 규칙을 그대로 따른다 (실측):
#   - 아이템 = 5000 + 1000 * inputTarget[g].sculptInbetweenWeight (인비트윈 편집이면 5500 등)
#   - d 는 셰이프 **오브젝트 공간** 그대로 더한다. 타겟 weight 로 나누지 않고, origin 이
#     world 여도 그대로다(베이스 공간 델타이므로).
#   - 라이브 타겟(inputGeomTarget 에 메시가 연결)이면 그 메시 버텍스도 d 만큼 옮긴다 —
#     inputPointsTarget 은 연결된 메시에서 다시 계산되기 때문이다. origin world 면
#     d 를 타겟 공간으로 되돌린다: d * (base.worldMatrix * target.worldInverseMatrix) 의 3x3.
#
# 델타는 블렌드셰이프 입력(스킨 앞)에 들어가므로, 스킨이 바인드 포즈가 아니면 마야에서 손으로
# 편집할 때와 똑같이 화면 이동량과 어긋난다.

import re

import maya.cmds as cmds
import maya.api.OpenMaya as om


_COMPONENT_RE = re.compile(r"\[(\d+)(?::(\d+))?\]")
_EPS = 1e-9


# =========================
# 찾기
# =========================

class SculptTarget(object):
    """셰이프 하나에 걸린, Edit 가 켜진 blendShape 타겟 아이템."""

    def __init__(self, bs, geo_idx, target_idx, item_idx):
        self.bs = bs
        self.geo_idx = geo_idx
        self.target_idx = target_idx
        self.item_idx = item_idx
        self.plug = "{0}.inputTarget[{1}].inputTargetGroup[{2}].inputTargetItem[{3}]".format(
            bs, geo_idx, target_idx, item_idx)

    @property
    def label(self):
        alias = cmds.aliasAttr("{0}.w[{1}]".format(self.bs, self.target_idx), q=True)
        name = alias or "w[{0}]".format(self.target_idx)
        if self.item_idx != 6000:
            name += " (inbetween {0:.3f})".format((self.item_idx - 5000) / 1000.0)
        return "{0}.{1}".format(self.bs, name)

    def live_mesh(self):
        """inputGeomTarget 에 연결된 타겟 메시(셰이프 풀 패스). 없으면 None."""
        src = cmds.listConnections(self.plug + ".inputGeomTarget",
                                   source=True, destination=False, shapes=True) or []
        for node in src:
            shapes = ([node] if cmds.nodeType(node) == "mesh" else
                      cmds.listRelatives(node, s=True, f=True, type="mesh", ni=True) or [])
            if shapes:
                return cmds.ls(shapes[0], l=True)[0]
        return None


def find_sculpt_target(shape):
    """shape 를 변형하는 blendShape 중 Edit 가 켜진 타겟. 없으면 None."""
    shape_long = cmds.ls(shape, l=True)[0]
    hist = cmds.listHistory(shape, pruneDagObjects=True) or []
    for bs in cmds.ls(hist, type="blendShape") or []:
        geos = cmds.blendShape(bs, q=True, geometry=True) or []
        idxs = cmds.blendShape(bs, q=True, geometryIndices=True) or []
        for geo, g in zip(geos, idxs):
            if cmds.ls(geo, l=True)[0] != shape_long:
                continue
            ti = cmds.getAttr("{0}.inputTarget[{1}].sculptTargetIndex".format(bs, g))
            if ti is None or ti < 0:
                continue
            ibw = cmds.getAttr("{0}.inputTarget[{1}].sculptInbetweenWeight".format(bs, g))
            item = int(round(5000 + 1000 * (1.0 if ibw is None else ibw)))
            return SculptTarget(bs, g, int(ti), item)
    return None


# =========================
# 델타 읽기 / 쓰기
# =========================

def _expand_components(comps, count):
    """['vtx[0]', 'vtx[3:7]'] -> 인덱스 목록. 비어 있으면 0..count-1, 개수가 안 맞으면 None."""
    if not comps:
        return list(range(count))
    out = []
    for c in comps:
        m = _COMPONENT_RE.search(c)
        if not m:
            return None
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        out.extend(range(start, end + 1))
    return out if len(out) == count else None


def _component_strings(indices):
    out = []
    start = prev = None
    for i in indices:
        if start is None:
            start = prev = i
        elif i == prev + 1:
            prev = i
        else:
            out.append((start, prev))
            start = prev = i
    if start is not None:
        out.append((start, prev))
    return ["vtx[{0}]".format(a) if a == b else "vtx[{0}:{1}]".format(a, b) for a, b in out]


def _read_deltas(plug):
    pts = cmds.getAttr(plug + ".inputPointsTarget") or []
    if not pts:
        return {}
    comps = cmds.getAttr(plug + ".inputComponentsTarget") or []
    indices = _expand_components(comps, len(pts))
    if indices is None:
        raise ValueError("can't read the deltas of {0}".format(plug))
    return {v: (pts[k][0], pts[k][1], pts[k][2]) for k, v in enumerate(indices)}


def _write_deltas(plug, deltas):
    verts = sorted(v for v, d in deltas.items()
                   if abs(d[0]) > _EPS or abs(d[1]) > _EPS or abs(d[2]) > _EPS)
    if not verts:
        cmds.setAttr(plug + ".inputPointsTarget", 0, type="pointArray")
        cmds.setAttr(plug + ".inputComponentsTarget", 0, type="componentList")
        return
    pts = [(deltas[v][0], deltas[v][1], deltas[v][2], 1.0) for v in verts]
    comps = _component_strings(verts)
    cmds.setAttr(plug + ".inputPointsTarget", len(pts), *pts, type="pointArray")
    cmds.setAttr(plug + ".inputComponentsTarget", len(comps), *comps, type="componentList")


def _dag(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


def _move_live_mesh(live, base_shape, st, offsets):
    """라이브 타겟 메시의 버텍스를 offsets 만큼 옮긴다 (그 메시의 pnts, undo 가능)."""
    conv = None
    if cmds.getAttr(st.bs + ".origin") == 0:      # world: 베이스 공간 -> 타겟 공간
        conv = _dag(base_shape).inclusiveMatrix() * _dag(live).inclusiveMatrixInverse()
    if conv is not None:
        offsets = {v: tuple(om.MVector(*d) * conv) for v, d in offsets.items()}
    # 연속 구간마다 읽고 더해서 한 번에 쓴다.
    for comp in _component_strings(sorted(offsets)):
        m = _COMPONENT_RE.search(comp)
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        plug = "{0}.pnts[{1}:{2}]".format(live, start, end)
        cur = cmds.getAttr(plug)
        flat = []
        for k, v in enumerate(range(start, end + 1)):
            d = offsets[v]
            flat.extend((cur[k][0] + d[0], cur[k][1] + d[1], cur[k][2] + d[2]))
        cmds.setAttr(plug, *flat, type="double3")


def add_offsets(shape, st, offsets):
    """{vtx: (dx, dy, dz)} (shape 오브젝트 공간) 를 편집 중인 타겟에 더한다. 옮긴 수를 돌려준다.

    호출부가 undo_chunk 로 감싼다.
    """
    offsets = {v: d for v, d in offsets.items()
               if abs(d[0]) > _EPS or abs(d[1]) > _EPS or abs(d[2]) > _EPS}
    if not offsets:
        return 0

    live = st.live_mesh()
    if live:
        _move_live_mesh(live, shape, st, offsets)
        return len(offsets)

    deltas = _read_deltas(st.plug)
    for v, d in offsets.items():
        b = deltas.get(v, (0.0, 0.0, 0.0))
        deltas[v] = (b[0] + d[0], b[1] + d[1], b[2] + d[2])
    _write_deltas(st.plug, deltas)
    return len(offsets)
