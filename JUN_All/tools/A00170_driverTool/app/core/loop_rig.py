# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-12
# A00170_driverTool - AttachCrv > Edge Loop : 엣지 루프 -> 커브 -> 널 -> (조인트) 한 번에.
#
# 저장한 **엣지 루프**로 커브를 만들고, 저장한 **버텍스** 자리마다 널(빈 그룹)을 세운 뒤
# 그 널들을 커브에 라이브 어태치한다. 옵션으로 널마다 조인트를 만들어 널을 따라가게 한다.
# 입술/눈꺼풀처럼 "루프를 커브로 뽑아 몇 개의 드라이버로 제어" 하는 셋업을 버튼 하나로 만든다.
#
#   [엣지 루프 저장] --polyToCurve--> 커브(루프마다 1개)
#   [버텍스 저장]    --그 자리에-->  널 --가장 가까운 커브에 어태치--> 커브를 따라 움직임
#                                     └(옵션) 조인트가 널을 따라감
#
# 세 조각의 출처:
#   - 커브 생성   : A00400_CurveTool `curve_manager` 의 방식(엣지를 **연결 성분별로 묶어**
#     그룹마다 `polyToCurve(form=2, ch=True)`). 루프가 여러 개면 커브도 그 수만큼 나온다.
#     (A00400 을 import 하지는 않는다 — 툴 하나를 릴리스할 때 다른 툴이 딸려가면 안 된다.)
#   - 커브 어태치 : 같은 툴의 `attach_curve.build_attach_to_closest` 를 그대로 호출한다.
#   - 조인트      : 널마다 조인트를 만들어 `parentConstraint` 로 따라가게 한다. 조인트를 널
#     밑으로 parent 하지 않는 이유는 스켈레톤 계층을 따로 두고 스킨/익스포트하기 위해서다.
#
# UI 비의존: 위젯에서 읽은 이름 리스트와 옵션 값만 받는다.

import maya.cmds as cmds

from .attach_curve import build_attach_to_closest


# polyToCurve 차수. 1 = 엣지를 그대로 따르는 폴리라인, 3 = 부드러운 곡선.
CURVE_DEGREES = (1, 3)

DEFAULT_PREFIX = "loopDrv"


# ============================================================ 선택 파싱

def parse_selected_edges():
    """현재 선택에서 폴리곤 엣지 이름을 평탄화해 돌려준다."""
    sel = cmds.ls(sl=True, fl=True) or []
    edges = [s for s in sel if ".e[" in s]
    if not edges:
        raise ValueError("No polygon edges selected. Select the edge loop(s) "
                         "first.")
    return edges


def parse_selected_vertices():
    """현재 선택에서 버텍스 이름을 평탄화해 돌려준다(엣지/페이스는 버텍스로 변환)."""
    sel = cmds.ls(sl=True, fl=True) or []
    comps = [s for s in sel if "." in s]
    if not comps:
        raise ValueError("No components selected. Select the vertices where "
                         "the drivers should sit.")
    converted = cmds.polyListComponentConversion(comps, toVertex=True) or []
    verts = cmds.ls(converted, fl=True) or []
    if not verts:
        raise ValueError("The selection has no vertices.")
    return verts


def alive(names):
    """씬에 아직 존재하는 것만 남긴다(컴포넌트는 소유 오브젝트로 판정)."""
    out = []
    for name in names or []:
        node = name.split(".")[0]
        if cmds.objExists(node):
            out.append(name)
    return out


# ============================================================ 커브 생성

def _edge_verts(edge):
    """엣지 하나의 두 정점 이름."""
    conv = cmds.polyListComponentConversion(edge, fromEdge=True,
                                            toVertex=True) or []
    return cmds.ls(conv, fl=True) or []


def group_edges(edges):
    """엣지를 '붙어 있는 덩어리'(연결 성분)별로 묶는다 — A00400_CurveTool 과 같은 방식.

    두 엣지가 정점을 공유하면 같은 그룹. 서로 다른 메시의 엣지는 정점을 공유할 수 없어
    자연히 갈린다. 반환: [[edge, ...], ...] (발견 순서)
    """
    edge_verts = {e: _edge_verts(e) for e in edges}

    vert_to_edges = {}
    for edge, verts in edge_verts.items():
        for vert in verts:
            vert_to_edges.setdefault(vert, []).append(edge)

    seen = set()
    groups = []
    for start in edges:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        comp = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for vert in edge_verts[cur]:
                for nb in vert_to_edges.get(vert, []):
                    if nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
        groups.append(comp)
    return groups


def curves_from_edges(edges, prefix=DEFAULT_PREFIX, degree=1):
    """엣지를 연결 성분별로 묶어 그룹마다 커브 1개를 만든다.

    `polyToCurve(form=2, ch=True)` — form=2 는 열림/닫힘을 자동 판단하므로 닫힌 엣지
    루프면 주기적 커브가 나오고, ch=True 라 커브가 메시에 **부착**되어 메시가 변형되면
    커브도 따라 변한다.
    Returns (curves, group_count)
    """
    if degree not in CURVE_DEGREES:
        degree = 1

    groups = group_edges(edges)
    created = []
    for i, group in enumerate(groups):
        cmds.select(group, replace=True)
        res = cmds.polyToCurve(form=2, degree=degree, constructionHistory=True,
                               conformToSmoothMeshPreview=0)
        crv = cmds.rename(res[0], "{0}_crv_{1:02d}".format(prefix, i + 1))
        created.append(crv)
    return created, len(groups)


# ============================================================ 널 / 최근접 커브

def _curve_shape(curve):
    if cmds.objExists(curve) and cmds.objectType(curve, isType="nurbsCurve"):
        return curve
    shapes = cmds.listRelatives(curve, shapes=True, type="nurbsCurve",
                                fullPath=True) or []
    return shapes[0] if shapes else None


def _closest_distance(curve_shape, position):
    """world position 에서 그 커브까지의 최단 거리(제곱 아님)."""
    npoc = cmds.createNode("nearestPointOnCurve")
    try:
        cmds.connectAttr(curve_shape + ".worldSpace[0]", npoc + ".inputCurve",
                         force=True)
        cmds.setAttr(npoc + ".inPositionX", position[0])
        cmds.setAttr(npoc + ".inPositionY", position[1])
        cmds.setAttr(npoc + ".inPositionZ", position[2])
        near = cmds.getAttr(npoc + ".position")[0]
    finally:
        cmds.delete(npoc)
    return ((near[0] - position[0]) ** 2 + (near[1] - position[1]) ** 2 +
            (near[2] - position[2]) ** 2) ** 0.5


def nearest_curve(curves, position):
    """position 에 가장 가까운 커브 이름. 커브가 하나면 그것(질의 생략)."""
    if len(curves) == 1:
        return curves[0]
    best, best_d = None, float("inf")
    for curve in curves:
        shape = _curve_shape(curve)
        if shape is None:
            continue
        d = _closest_distance(shape, position)
        if d < best_d:
            best, best_d = curve, d
    return best


def _create_null(name, position):
    """빈 그룹(널)을 만들어 world position 에 놓는다."""
    null = cmds.group(empty=True, name=name)
    cmds.xform(null, worldSpace=True, translation=position)
    return null


# ============================================================ 메인 동작

def build_loop_drivers(edges, vertices, prefix=DEFAULT_PREFIX, degree=1,
                       orient=True, aim_axis="+X", use_normal_curve=True,
                       normal_curve_length=1.0, create_set=True,
                       create_joints=True, joint_radius=1.0):
    """저장한 엣지 루프 -> 커브, 저장한 버텍스 자리 -> 널, 널 -> 커브 어태치 (+조인트).

    Args:
        edges: 저장해 둔 엣지 이름들(루프 여러 개를 한 번에 줘도 된다).
        vertices: 널을 세울 버텍스 이름들.
        prefix: 생성물 이름 접두사(`<prefix>_crv_01` / `_null_01` / `_jnt_01`).
        degree: 커브 차수(1=폴리라인, 3=부드러운 곡선).
        orient, aim_axis, use_normal_curve, normal_curve_length, create_set:
            어태치 옵션 — `attach_curve.build_attach_to_closest` 와 같은 의미.
        create_joints: True 면 널마다 조인트를 만들어 `parentConstraint` 로 따라가게 한다.
        joint_radius: 만들 조인트의 표시 반경.

    Returns:
        report dict — curves / nulls / joints / attached / failed / sets /
        norcrvs / null_group / joint_group.

    널은 **버텍스 위치에 만든 뒤** 커브에 어태치하므로, 커브 위 최근접 지점으로 끌려간다
    (버텍스가 커브 위에 있으면 그 자리 그대로). 커브가 여러 개면 널마다 **가장 가까운
    커브**에 붙는다.
    """
    edges = alive(edges)
    vertices = alive(vertices)
    if not edges:
        raise ValueError("No edge loop stored. Press 'Store Edge Loops' first.")
    if not vertices:
        raise ValueError("No vertices stored. Press 'Store Vertices' first.")

    prefix = (prefix or DEFAULT_PREFIX).strip() or DEFAULT_PREFIX

    # 1) 엣지 루프 -> 커브
    curves, group_count = curves_from_edges(edges, prefix=prefix, degree=degree)
    if not curves:
        raise ValueError("Could not build any curve from the stored edges.")

    # 2) 버텍스 자리마다 널
    null_group = cmds.group(empty=True, name="{0}_null_grp".format(prefix))
    nulls = []
    for i, vtx in enumerate(vertices):
        position = cmds.pointPosition(vtx, world=True)
        null = _create_null("{0}_null_{1:02d}".format(prefix, i + 1), position)
        null = cmds.parent(null, null_group)[0]
        nulls.append(null)

    # 3) 널 -> 가장 가까운 커브에 어태치 (커브별로 묶어 한 번씩 호출한다 —
    #    norCrv/세트가 커브마다 하나씩만 생기게 하려면 이렇게 모아 불러야 한다)
    by_curve = {}
    for null in nulls:
        position = cmds.xform(null, query=True, worldSpace=True,
                              rotatePivot=True)
        target = nearest_curve(curves, position)
        by_curve.setdefault(target, []).append(null)

    attached = []
    failed = []
    sets = []
    norcrvs = []
    for curve in curves:
        members = by_curve.get(curve)
        if not members:
            continue
        got, bad, set_node, norcrv = build_attach_to_closest(
            curve, members, orient=orient, aim_axis=aim_axis,
            use_normal_curve=use_normal_curve,
            normal_curve_length=normal_curve_length, create_set=create_set)
        attached.extend([(obj, curve, param) for obj, param in got])
        failed.extend(bad)
        if set_node:
            sets.append(set_node)
        if norcrv:
            norcrvs.append(norcrv)

    # 4) (옵션) 조인트 — 어태치가 끝난 **널의 현재 자리**에 만들어 따라가게 한다.
    joints = []
    joint_group = None
    if create_joints and attached:
        joint_group = cmds.group(empty=True, name="{0}_jnt_grp".format(prefix))
        for i, (null, _curve, _param) in enumerate(attached):
            position = cmds.xform(null, query=True, worldSpace=True,
                                  rotatePivot=True)
            cmds.select(clear=True)
            jnt = cmds.joint(position=position, radius=joint_radius,
                             name="{0}_jnt_{1:02d}".format(prefix, i + 1))
            jnt = cmds.parent(jnt, joint_group)[0]
            # 널이 커브를 따라 움직이면 조인트도 그대로 따라간다.
            cmds.parentConstraint(null, jnt, maintainOffset=False)
            joints.append(jnt)

    return {
        "curves": curves,
        "loops": group_count,
        "nulls": nulls,
        "joints": joints,
        "attached": attached,
        "failed": failed,
        "sets": sets,
        "norcrvs": norcrvs,
        "null_group": null_group,
        "joint_group": joint_group,
    }
