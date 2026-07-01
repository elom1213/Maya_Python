# -*- coding: utf-8 -*-
"""
match_manager - Match 탭 로직.

MEL `JUN_MEL_MATCH_V05_04.mel`(Match Tool V05.04)의 PySide 포팅 + 리팩토링.
follower 를 target 의 위치/회전에 맞춘다. target 종류에 따라:

  - transform/joint/curve : 위치+회전 매칭(rotateOrder 가 달라도 안전).
  - mesh(오브젝트 전체)     : 월드 정점 평균(centroid)으로 위치만.
  - clusterHandle          : 월드 rotatePivot 으로 위치만.
  - 그 외 component(edge/face/cv) : pointPosition 으로 위치만.
  - vertex(.vtx[i])        : 정점 월드 위치로 이동 + follower 의 +Y 축을 정점 노말에 정렬.

UI 비의존: 위젯에서 읽은 list/str 값만 받는다. (app/core ↔ app/ui 분리)

MEL 대비 개선/버그 수정:
  - rotateOrder 를 임시로 바꿨다 되돌리는 방식(+ mesh/cluster 분기에서 복원 누락 버그)을 제거하고
    `cmds.matchTransform`(rotateOrder 안전)으로 통일.
  - mesh/cluster 의 local-space rotatePivot 질의 버그를 월드 centroid/월드 rotatePivot 으로 수정.
  - `catch(nodeType ...)` 의 취약한 shape 판별을 listRelatives(shapes=True)+nodeType 으로 교체.
  - Blend Shape 기능 제거.
  - Locators/Sphere/Cube 는 "생성 후 즉시 매칭"으로 동작(create_and_match).
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_refresh import suspend_refresh

_EPS = 1e-6


# ======================================================================
# control shapes (MEL JUN_get_sphereCtl / JUN_get_cubeCtl 의 곡선 데이터 이식)
# ======================================================================

# degree 1 sphere(원 3개를 잇는 와이어프레임) 컨트롤의 CV 좌표.
_SPHERE_POINTS = [
    (0, 0, 0), (0, 0.505239, 0), (0, 0.488023, 0.130765), (0, 0.437549, 0.252619),
    (0, 0.357258, 0.357258), (0, 0.252619, 0.437549), (0, 0.130765, 0.488023),
    (0, 0, 0.505239), (0, -0.130765, 0.488023), (0, -0.252619, 0.437549),
    (0, -0.357258, 0.357258), (0, -0.437549, 0.252619), (0, -0.488023, 0.130765),
    (0, -0.505239, 0), (0, -0.488023, -0.130765), (0, -0.437549, -0.252619),
    (0, -0.357258, -0.357258), (0, -0.252619, -0.437549), (0, -0.130765, -0.488023),
    (0, 0, -0.505239), (0, 0.130765, -0.488023), (0, 0.252619, -0.437549),
    (0, 0.357258, -0.357258), (0, 0.437549, -0.252619), (0, 0.488023, -0.130765),
    (0, 0.505239, 0), (0.130765, 0.488023, 0), (0.252619, 0.437549, 0),
    (0.357258, 0.357258, 0), (0.437549, 0.252619, 0), (0.488023, 0.130765, 0),
    (0.505239, 0, 0), (0.488023, -0.130765, 0), (0.437549, -0.252619, 0),
    (0.357258, -0.357258, 0), (0.252619, -0.437549, 0), (0.130765, -0.488023, 0),
    (0, -0.505239, 0), (-0.130765, -0.488023, 0), (-0.252619, -0.437549, 0),
    (-0.357258, -0.357258, 0), (-0.437549, -0.252619, 0), (-0.488023, -0.130765, 0),
    (-0.505239, 0, 0), (-0.488023, 0.130765, 0), (-0.437549, 0.252619, 0),
    (-0.357258, 0.357258, 0), (-0.252619, 0.437549, 0), (-0.130765, 0.488023, 0),
    (0, 0.505239, 0), (0, 0, 0), (0, -0.505239, 0), (0, 0, 0),
    (0.505239, 0, 0), (0.488023, 0, -0.130765), (0.437549, 0, -0.252619),
    (0.357258, 0, -0.357258), (0.252619, 0, -0.437549), (0.130765, 0, -0.488023),
    (0, 0, -0.505239), (-0.130765, 0, -0.488023), (-0.252619, 0, -0.437549),
    (-0.357258, 0, -0.357258), (-0.437549, 0, -0.252619), (-0.488023, 0, -0.130765),
    (-0.505239, 0, 0), (-0.488023, 0, 0.130765), (-0.437549, 0, 0.252619),
    (-0.357258, 0, 0.357258), (-0.252619, 0, 0.437549), (-0.130765, 0, 0.488023),
    (0, 0, 0.505239), (0.130765, 0, 0.488023), (0.252619, 0, 0.437549),
    (0.357258, 0, 0.357258), (0.437549, 0, 0.252619), (0.488023, 0, 0.130765),
    (0.505239, 0, 0), (0, 0, 0), (0, 0, -0.505239), (0, 0, 0.505239),
    (0, 0, 0), (-0.505239, 0, 0),
]

# degree 1 cube 컨트롤의 CV 좌표.
_CUBE_POINTS = [
    (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
    (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
    (0.5, -0.5, 0.5),
]


def _make_curve(points):
    """degree 1 곡선 컨트롤을 만들어 transform 이름을 반환(Maya 기본 이름)."""
    knots = list(range(len(points)))
    return cmds.curve(degree=1, point=points, knot=knots)


def _make_control(ctl_type):
    """ctl_type('locator'/'sphere'/'cube') 컨트롤 1개 생성 → transform 이름 반환."""
    if ctl_type == "locator":
        return cmds.spaceLocator()[0]
    if ctl_type == "sphere":
        return _make_curve(_SPHERE_POINTS)
    if ctl_type == "cube":
        return _make_curve(_CUBE_POINTS)
    raise ValueError("Unknown control type: {0}".format(ctl_type))


# ======================================================================
# target classification / sampling
# ======================================================================

def _mfn_mesh(name):
    """transform 또는 mesh shape 이름 -> MFnMesh (mesh_io 패턴과 동일)."""
    sel = om.MSelectionList()
    sel.add(name)
    dag = sel.getDagPath(0)
    if dag.apiType() == om.MFn.kTransform:
        dag.extendToShape()
    return om.MFnMesh(dag)


def _shape_type(node):
    """node 의 첫 shape nodeType. shape 가 없으면 node 자신의 nodeType."""
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
    return cmds.nodeType(shapes[0]) if shapes else cmds.nodeType(node)


def _classify(tgt):
    """target 종류 판별: vertex/component/cluster/mesh/transform."""
    if ".vtx[" in tgt:
        return "vertex"
    if "[" in tgt:                       # edge/face/cv 등 그 외 component
        return "component"
    st = _shape_type(tgt)
    if st == "clusterHandle":
        return "cluster"
    if st == "mesh":
        return "mesh"
    return "transform"


def _vertex_pos_normal(vtx):
    """버텍스의 (월드 위치 MVector, 월드 노말 MVector) 반환."""
    mesh, rest = vtx.split(".vtx[")
    index = int(rest[:-1])
    fn = _mfn_mesh(mesh)
    p = fn.getPoint(index, om.MSpace.kWorld)
    n = fn.getVertexNormal(index, True, om.MSpace.kWorld)  # angleWeighted=True
    return om.MVector(p.x, p.y, p.z), n.normal()


def _mesh_centroid(mesh):
    """메시 전체 정점의 월드 평균 좌표 (x, y, z)."""
    pts = _mfn_mesh(mesh).getPoints(om.MSpace.kWorld)
    n = len(pts)
    if not n:
        raise ValueError("Mesh has no vertices: {0}".format(mesh))
    sx = sum(p.x for p in pts)
    sy = sum(p.y for p in pts)
    sz = sum(p.z for p in pts)
    return (sx / n, sy / n, sz / n)


def _cluster_pivot(handle):
    """clusterHandle 의 월드 rotatePivot (x, y, z)."""
    return cmds.xform(handle, q=True, ws=True, rotatePivot=True)


# ======================================================================
# orientation from normal
# ======================================================================

def _basis_from_normal(normal, axis="y"):
    """주어진 노말을 axis 축으로 삼는 직교 정규기저 (x, y, z) 반환.

    axis="y" 면 +Y 가 노말을 향한다(기본). reference up 은 world Z(노말과 평행하면 world X).
    """
    n = normal.normal()
    ref = om.MVector(0, 0, 1)
    if abs(ref * n) > 0.9999:
        ref = om.MVector(1, 0, 0)

    if axis == "x":
        x = n
        y = (ref ^ x).normal()
        z = (x ^ y).normal()
    elif axis == "z":
        z = n
        x = (ref ^ z).normal()
        y = (z ^ x).normal()
    else:  # "y" (기본)
        y = n
        x = (y ^ ref).normal()
        z = (x ^ y).normal()
    return x, y, z


# ======================================================================
# apply
# ======================================================================

def _match_via_matrix(flw, x, y, z, pos, translate=True, rotate=True):
    """기저(x,y,z)+위치를 임시 transform 에 실어 matchTransform 으로 flw 에 적용한다.

    임시 노드를 거치므로 flw 의 rotateOrder 가 무엇이든 안전하고(매칭은 matchTransform 이 처리),
    flw 의 scale 도 보존된다(matchTransform pos+rot 은 scale 을 건드리지 않음).
    translate/rotate 로 위치/회전 중 적용할 채널을 고른다(둘 다 False 면 아무것도 안 함).
    """
    kwargs = {}
    if translate:
        kwargs["position"] = True
    if rotate:
        kwargs["rotation"] = True
    if not kwargs:
        return

    mat = [
        x.x, x.y, x.z, 0.0,
        y.x, y.y, y.z, 0.0,
        z.x, z.y, z.z, 0.0,
        pos.x, pos.y, pos.z, 1.0,
    ]
    tmp = cmds.createNode("transform")
    try:
        cmds.xform(tmp, ws=True, matrix=mat)
        cmds.matchTransform(flw, tmp, **kwargs)
    finally:
        cmds.delete(tmp)


def _match_pos(flw, pos):
    """위치만 매칭(월드)."""
    cmds.xform(flw, ws=True, translation=(pos[0], pos[1], pos[2]))


def _parent_one(flw, tgt):
    """flw 를 tgt(컴포넌트면 그 소유 transform) 아래로 parent 한다.

    DOOTOOL 'Parent Followers to Targets' 이식. cmds.parent 는 기본적으로 월드 위치를
    보존하므로 매칭된 위치/회전을 유지한다. 자기 자신이거나 이미 그 자식이면 스킵한다.
    """
    node = tgt.split(".")[0] if "." in tgt else tgt   # 컴포넌트 -> 소유 오브젝트
    if node == flw:
        return
    parents = cmds.listRelatives(flw, parent=True, fullPath=True) or []
    node_full = (cmds.ls(node, long=True) or [node])[0]
    if parents and parents[0] == node_full:
        return
    cmds.parent(flw, node)


def _match_one(tgt, flw, normal_axis, translate=True, rotate=True, scale=False):
    """target 종류에 따라 flw 를 tgt 에 매칭한다(채널: translate/rotate/scale).

    - transform/joint/curve : matchTransform 으로 켜진 채널(pos/rot/scale)만 월드 매칭.
    - vertex : 위치(translate) + 노말 정렬 회전(rotate). scale 은 의미 없어 무시.
    - mesh(centroid)/cluster(pivot)/component : 위치만(translate). rotate/scale 무시.
    scale 은 DOOTOOL 'Scale (Only in The World Space)' 이식 — matchTransform scale 은
    flw 의 월드 스케일이 tgt 의 월드 스케일과 같아지도록 맞춘다(월드 기준).
    """
    kind = _classify(tgt)
    if kind == "vertex":
        if translate or rotate:      # 둘 다 꺼졌으면 정점 샘플링 자체를 건너뛴다.
            pos, normal = _vertex_pos_normal(tgt)
            x, y, z = _basis_from_normal(normal, normal_axis)
            _match_via_matrix(flw, x, y, z, pos,
                              translate=translate, rotate=rotate)
    elif kind == "mesh":
        if translate:
            _match_pos(flw, _mesh_centroid(tgt))
    elif kind == "cluster":
        if translate:
            _match_pos(flw, _cluster_pivot(tgt))
    elif kind == "component":
        if translate:
            _match_pos(flw, cmds.pointPosition(tgt, world=True))
    else:  # transform/joint/curve : rotateOrder 안전한 월드 매칭
        kwargs = {}
        if translate:
            kwargs["position"] = True
        if rotate:
            kwargs["rotation"] = True
        if scale:
            kwargs["scale"] = True
        if kwargs:
            cmds.matchTransform(flw, tgt, **kwargs)
    return kind


# ======================================================================
# public API
# ======================================================================

def match(targets, followers, normal_axis="y",
          translate=True, rotate=True, scale=False, parent=False):
    """targets[i] 에 followers[i] 를 매칭한다(인덱스 1:1).

    Args:
        targets:   타겟 오브젝트/컴포넌트 리스트.
        followers: 따라갈 오브젝트 리스트.
        normal_axis: 버텍스 타겟일 때 노말에 정렬할 follower 축("x"/"y"/"z"). 기본 "y".
        translate: 위치 매칭(기본 True). DOOTOOL 'Translation'.
        rotate:    회전 매칭(기본 True). DOOTOOL 'Rotation'.
        scale:     월드 스케일 매칭(기본 False). DOOTOOL 'Scale (Only in The World Space)'.
        parent:    매칭 후 follower 를 target 아래로 parent(기본 False).
                   DOOTOOL 'Parent Followers to Targets'.

    Returns:
        (matched_count, skipped_count). 개수가 다르면 min 만큼만 매칭하고 차이를 skipped 로 보고.
    """
    if not targets:
        raise ValueError("No targets. Add objects to the Targets list.")
    if not followers:
        raise ValueError("No followers. Add objects to the Followers list.")

    n = min(len(targets), len(followers))
    skipped = abs(len(targets) - len(followers))

    with suspend_refresh():
        for i in range(n):
            _match_one(targets[i], followers[i], normal_axis,
                       translate=translate, rotate=rotate, scale=scale)
        # DOOTOOL 과 동일하게 매칭을 모두 마친 뒤 별도 패스로 parent 한다.
        if parent:
            for i in range(n):
                _parent_one(followers[i], targets[i])

    return n, skipped


def create_and_match(targets, ctl_type, normal_axis="y"):
    """targets 수만큼 컨트롤(ctl_type)을 만들어 각 타겟 위치/방향에 즉시 매칭한다.

    Args:
        targets:   타겟 오브젝트/컴포넌트 리스트.
        ctl_type:  "locator" / "sphere" / "cube".
        normal_axis: 버텍스 타겟일 때 노말 정렬 축. 기본 "y".

    Returns:
        생성된 컨트롤 transform 이름 리스트(타겟과 인덱스 1:1).
    """
    if not targets:
        raise ValueError("No targets. Add objects to the Targets list.")

    created = []
    with suspend_refresh():
        for _ in targets:
            created.append(_make_control(ctl_type))
        for tgt, flw in zip(targets, created):
            _match_one(tgt, flw, normal_axis)

    return created
