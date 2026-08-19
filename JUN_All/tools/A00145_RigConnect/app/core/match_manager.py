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

대량 매칭 (_Ctx)
----------------
버텍스 수천 개를 한 번에 매칭하는 일이 흔해서, 항목마다 반복되던 마야 호출을 호출 1회 동안
공유하는 `_Ctx` 로 묶었다:

  - 회전 매칭에 쓰는 **임시 transform** 을 항목마다 createNode/delete 하지 않고 하나만 만들어
    돌려 쓰고 끝에 지운다.
  - 같은 메시의 버텍스가 이어지면 **MFnMesh 를 캐시**한다(항목마다 shape 를 다시 찾지 않는다).
  - `_classify` 의 shape 타입 조회도 노드 이름으로 캐시한다.

셰이프 캐시는 **한 번의 match() 호출 안에서만** 산다 — 그 사이에 씬 토폴로지가 바뀌지 않는다.

타겟↔팔로워 짝짓기 (resolve_pairs)
----------------------------------
기본은 **인덱스 1:1** (`targets[i]` ← `followers[i]`, `n <- n`). 여기에 `one_to_many`(기본 True)
가 붙는다 — 타겟이 **정확히 하나**면 그 하나에 **모든 팔로워**를 맞춘다(`1 <- n`).
타겟이 2개 이상이면 이 값과 무관하게 `n <- n` 이라, 켜 둔 채로도 평소 작업이 달라지지 않는다.
`match()` 와 UI 가 **같은 `resolve_pairs()`** 를 쓰므로 로그에 찍히는 모드와 실제 동작이 어긋나지 않는다.

스냅샷 타겟 (추상 캐시)
-----------------------
`capture()` 로 타겟의 월드 T/R/S 를 값으로 떠서 `SnapshotCache` 에 담아 두면, 그 스냅샷 키를
**타겟처럼** 쓸 수 있다(`snapshot_manager` 참고). "오브젝트를 잠깐 옮겼다 되돌리려고 로케이터를
수천 개 만들던" 흐름을 노드 없이 대신한다.

되돌릴 때는 샘플링이 필요 없다 — 행렬이 이미 메모리에 있으므로 타겟 쪽 마야 호출(`_classify`,
`xform` 질의, `MFnMesh`)이 통째로 빠진다. T/R/S 를 모두 켠 경우에는 임시 노드도 거치지 않고
`cmds.xform(flw, ws=True, matrix=...)` **한 번**으로 끝난다(부모 있는 트랜스폼 · rotateOrder ·
jointOrient 조인트에서 `matchTransform` 과 결과가 같음을 mayapy 로 확인, 오차 ~1e-15).
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_refresh import suspend_refresh
from Framework.core import maya_shape
from tools.A00145_RigConnect.app.core import snapshot_manager as snap

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

class _Ctx(object):
    """한 번의 매칭 호출 동안 공유하는 캐시 + 임시 노드.

    항목 수가 많을 때 같은 질의를 항목마다 반복하지 않기 위한 것이다. 캐시는 이 객체와
    함께 죽으므로 호출 사이에 씬이 바뀌어도 낡은 값이 남지 않는다.
    """

    def __init__(self):
        self._tmp = None            # 회전 매칭용 임시 transform (필요할 때 1개만 생성)
        self._mesh_fns = {}         # 이름 -> MFnMesh
        self._shape_types = {}      # 노드 이름 -> 첫 shape 의 nodeType

    def tmp_transform(self):
        if self._tmp is None:
            self._tmp = cmds.createNode("transform")
        return self._tmp

    def mesh_fn(self, name):
        fn = self._mesh_fns.get(name)
        if fn is None:
            fn = om.MFnMesh(maya_shape.shape_dag(name))
            self._mesh_fns[name] = fn
        return fn

    def shape_type(self, node):
        st = self._shape_types.get(node)
        if st is None:
            shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
            st = cmds.nodeType(shapes[0]) if shapes else cmds.nodeType(node)
            self._shape_types[node] = st
        return st

    def dispose(self):
        """임시 노드를 정리한다(캐시는 객체와 함께 버려진다)."""
        if self._tmp is not None:
            try:
                cmds.delete(self._tmp)
            except Exception:
                pass
            self._tmp = None


def _mfn_mesh(name, ctx=None):
    """transform 또는 mesh shape 이름 -> MFnMesh.

    셰이프가 여럿인 트랜스폼에서도 **디포머가 변형하는 셰이프**를 고른다
    (extendToShape 는 첫 non-intermediate 셰이프를 집을 뿐이다 — maya_shape 참고).
    ctx 를 주면 같은 메시를 다시 찾지 않는다(같은 메시의 버텍스가 여럿일 때).
    """
    if ctx is not None:
        return ctx.mesh_fn(name)
    return om.MFnMesh(maya_shape.shape_dag(name))


def _shape_type(node, ctx=None):
    """node 의 첫 shape nodeType. shape 가 없으면 node 자신의 nodeType."""
    if ctx is not None:
        return ctx.shape_type(node)
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
    return cmds.nodeType(shapes[0]) if shapes else cmds.nodeType(node)


def _classify(tgt, ctx=None):
    """target 종류 판별: snapshot/vertex/component/cluster/mesh/transform.

    스냅샷(추상 캐시)은 씬 노드가 아니므로 **가장 먼저** 걸러낸다 — 표시 텍스트에 `.` 이나
    `[` 가 들어 있어도(예: `@cache body.vtx[3]`) 컴포넌트로 오해하지 않도록.
    """
    if snap.is_snapshot(tgt):
        return "snapshot"
    if ".vtx[" in tgt:
        return "vertex"
    if "[" in tgt:                       # edge/face/cv 등 그 외 component
        return "component"
    st = _shape_type(tgt, ctx)
    if st == "clusterHandle":
        return "cluster"
    if st == "mesh":
        return "mesh"
    return "transform"


def _vertex_pos_normal(vtx, ctx=None):
    """버텍스의 (월드 위치 MVector, 월드 노말 MVector) 반환."""
    mesh, rest = vtx.split(".vtx[")
    index = int(rest[:-1])
    fn = _mfn_mesh(mesh, ctx)
    p = fn.getPoint(index, om.MSpace.kWorld)
    n = fn.getVertexNormal(index, True, om.MSpace.kWorld)  # angleWeighted=True
    return om.MVector(p.x, p.y, p.z), n.normal()


def _mesh_centroid(mesh, ctx=None):
    """메시 전체 정점의 월드 평균 좌표 (x, y, z)."""
    pts = _mfn_mesh(mesh, ctx).getPoints(om.MSpace.kWorld)
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


def _component_center(comp):
    """컴포넌트(vtx/cv/edge/face/uv)의 월드 중심 (x, y, z).

    `cmds.pointPosition` 은 **점 컴포넌트만** 받는다 — 엣지·페이스를 주면
    `RuntimeError` 다(예전에는 edge/face 타겟이 여기서 조용히 실패했다).
    `xform -q -ws -t` 는 컴포넌트가 걸친 점들의 좌표를 전부 돌려주므로 그 평균을 쓴다.
    점 컴포넌트(vtx/cv)면 값이 3개뿐이라 pointPosition 과 정확히 같은 결과다.
    """
    pts = cmds.xform(comp, q=True, ws=True, translation=True) or []
    n = len(pts) // 3
    if not n:
        raise ValueError("Cannot read a position from '{0}'.".format(comp))
    return (sum(pts[0::3]) / n, sum(pts[1::3]) / n, sum(pts[2::3]) / n)


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
# world matrix helpers
# ======================================================================

def _matrix_from_basis(x, y, z, pos):
    """기저(x, y, z) + 위치 -> 월드 행렬 16개(row-major)."""
    return [
        x.x, x.y, x.z, 0.0,
        y.x, y.y, y.z, 0.0,
        z.x, z.y, z.z, 0.0,
        pos[0], pos[1], pos[2], 1.0,
    ]


def _matrix_from_pos(pos):
    """위치만 있는 항목(mesh centroid / cluster pivot / component)의 월드 행렬."""
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        pos[0], pos[1], pos[2], 1.0,
    ]


# ======================================================================
# apply
# ======================================================================

def _apply_matrix(flw, mat, translate=True, rotate=True, scale=False, ctx=None):
    """월드 행렬을 임시 transform 에 실어 matchTransform 으로 flw 에 적용한다.

    임시 노드를 거치므로 flw 의 rotateOrder 가 무엇이든 안전하고(매칭은 matchTransform 이 처리),
    끄지 않은 채널은 건드리지 않는다(예: scale=False 면 flw 의 scale 이 그대로 남는다).
    채널을 하나도 켜지 않으면 아무것도 하지 않는다.

    ctx 를 주면 임시 노드를 **한 개만 만들어 돌려 쓴다**(정리는 ctx.dispose()).
    항목마다 createNode/delete 를 부르면 버텍스 수천 개에서 그 비용이 매칭보다 커진다.
    """
    kwargs = {}
    if translate:
        kwargs["position"] = True
    if rotate:
        kwargs["rotation"] = True
    if scale:
        kwargs["scale"] = True
    if not kwargs:
        return

    if ctx is not None:
        tmp = ctx.tmp_transform()
        cmds.xform(tmp, ws=True, matrix=mat)
        cmds.matchTransform(flw, tmp, **kwargs)
        return

    tmp = cmds.createNode("transform")
    try:
        cmds.xform(tmp, ws=True, matrix=mat)
        cmds.matchTransform(flw, tmp, **kwargs)
    finally:
        cmds.delete(tmp)


def _match_via_basis(flw, x, y, z, pos, translate=True, rotate=True, ctx=None):
    """기저(x, y, z) + 위치로 매칭(버텍스 타겟의 노말 정렬 경로)."""
    _apply_matrix(flw, _matrix_from_basis(x, y, z, (pos.x, pos.y, pos.z)),
                  translate=translate, rotate=rotate, ctx=ctx)


def _match_pos(flw, pos):
    """위치만 매칭(월드)."""
    cmds.xform(flw, ws=True, translation=(pos[0], pos[1], pos[2]))


def _apply_snapshot(flw, shot, translate=True, rotate=True, scale=False, ctx=None):
    """캐시해 둔 스냅샷을 flw 에 적용한다. 채널 의미는 원본 타겟 종류를 그대로 따른다.

    - transform : T/R/S. **셋 다 켜져 있으면** 임시 노드도 거치지 않고 `xform -ws -matrix`
      한 번으로 끝낸다(가장 흔한 "원래 자리로 되돌리기" 경로).
    - vertex    : 위치 + 노말 정렬 회전. scale 은 의미가 없어 무시(원본 동작과 동일).
    - 그 외     : 위치만.
    """
    if shot.kind == "transform":
        if translate and rotate and scale:
            cmds.xform(flw, ws=True, matrix=shot.matrix)
            return
        _apply_matrix(flw, shot.matrix, translate=translate, rotate=rotate,
                      scale=scale, ctx=ctx)
    elif shot.kind == "vertex":
        if translate or rotate:
            _apply_matrix(flw, shot.matrix, translate=translate, rotate=rotate,
                          scale=False, ctx=ctx)
    else:                                   # component (위치만 있는 항목)
        if translate:
            _match_pos(flw, shot.position())


def _capture_kind(tgt):
    """캡처할 때의 종류 판별 — 매칭의 `_classify` 와 **일부러 다르다**.

    캡처의 목적은 "이 대상을 원래 자리로 되돌리는 것" 이라, 오브젝트는 종류를 가리지 않고
    **자기 월드 행렬**(T/R/S 전부)을 기억한다. 즉 메시 오브젝트도 centroid 가 아니라 자기
    행렬을 담는다 — 라이브 메시 타겟의 centroid 규칙(`_classify` 의 "mesh")과 다른 점이다.
    centroid/피벗은 "다른 것을 이 메시 가운데로 보내는" 규칙이지 그 메시의 정체가 아니다.

    덤으로 셰이프 조회(`listRelatives` + `nodeType`)가 통째로 빠져서 캡처가 더 빠르다.
    """
    if ".vtx[" in tgt:
        return "vertex"
    if "[" in tgt:                       # cv/edge/face/uv 등 그 외 component
        return "component"
    return "transform"


def _sample(tgt, normal_axis="y", ctx=None):
    """타겟 하나에서 (종류, 월드 행렬) 을 뽑는다 — 캡처가 쓰는 경로.

    - transform : 월드 행렬 그대로(스케일·shear 포함).
    - vertex    : 노말 정렬 기저 + 위치(라이브 버텍스 타겟과 같은 해석).
    - component : 컴포넌트 중심 위치(회전은 단위행렬).
    """
    kind = _capture_kind(tgt)
    if kind == "vertex":
        pos, normal = _vertex_pos_normal(tgt, ctx)
        x, y, z = _basis_from_normal(normal, normal_axis)
        return kind, _matrix_from_basis(x, y, z, (pos.x, pos.y, pos.z))
    if kind == "component":
        return kind, _matrix_from_pos(_component_center(tgt))
    return kind, cmds.xform(tgt, q=True, ws=True, matrix=True)


def _parent_one(flw, tgt):
    """flw 를 tgt(컴포넌트면 그 소유 transform) 아래로 parent 한다.

    DOOTOOL 'Parent Followers to Targets' 이식. cmds.parent 는 기본적으로 월드 위치를
    보존하므로 매칭된 위치/회전을 유지한다. 자기 자신이거나 이미 그 자식이면 스킵한다.
    스냅샷(추상 캐시)은 씬에 없으니 부모가 될 수 없다 — 조용히 건너뛴다(호출부가 보고한다).
    """
    if snap.is_snapshot(tgt):
        return False
    node = tgt.split(".")[0] if "." in tgt else tgt   # 컴포넌트 -> 소유 오브젝트
    if node == flw:
        return True
    parents = cmds.listRelatives(flw, parent=True, fullPath=True) or []
    node_full = (cmds.ls(node, long=True) or [node])[0]
    if parents and parents[0] == node_full:
        return True
    cmds.parent(flw, node)
    return True


def _match_one(tgt, flw, normal_axis, translate=True, rotate=True, scale=False,
               ctx=None, cache=None):
    """target 종류에 따라 flw 를 tgt 에 매칭한다(채널: translate/rotate/scale).

    - transform/joint/curve : matchTransform 으로 켜진 채널(pos/rot/scale)만 월드 매칭.
    - vertex : 위치(translate) + 노말 정렬 회전(rotate). scale 은 의미 없어 무시.
    - mesh(centroid)/cluster(pivot)/component : 위치만(translate). rotate/scale 무시.
    scale 은 DOOTOOL 'Scale (Only in The World Space)' 이식 — matchTransform scale 은
    flw 의 월드 스케일이 tgt 의 월드 스케일과 같아지도록 맞춘다(월드 기준).
    """
    kind = _classify(tgt, ctx)
    if kind == "snapshot":
        shot = cache.get(tgt) if cache is not None else None
        if shot is None:
            raise ValueError(
                "No cached transform for '{0}' - it was cleared or the tool "
                "was reloaded.".format(tgt))
        _apply_snapshot(flw, shot, translate=translate, rotate=rotate,
                        scale=scale, ctx=ctx)
    elif kind == "vertex":
        if translate or rotate:      # 둘 다 꺼졌으면 정점 샘플링 자체를 건너뛴다.
            pos, normal = _vertex_pos_normal(tgt, ctx)
            x, y, z = _basis_from_normal(normal, normal_axis)
            _match_via_basis(flw, x, y, z, pos,
                             translate=translate, rotate=rotate, ctx=ctx)
    elif kind == "mesh":
        if translate:
            _match_pos(flw, _mesh_centroid(tgt, ctx))
    elif kind == "cluster":
        if translate:
            _match_pos(flw, _cluster_pivot(tgt))
    elif kind == "component":
        if translate:
            _match_pos(flw, _component_center(tgt))
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

def _note(notes, message, limit=5):
    """진행을 멈추지 않고 남기는 메모. 같은 이야기가 길어지지 않도록 앞의 몇 줄만 남긴다."""
    if notes is None:
        return
    if len(notes) < limit:
        notes.append(message)
    elif len(notes) == limit:
        notes.append("... (more of the same, only the first {0} are shown)".format(limit))


def resolve_pairs(targets, followers, one_to_many=True):
    """(pairs, fan_out, unpaired) — 타겟↔팔로워 짝을 정한다.

    pairs    : [(target, follower), ...] 실제로 매칭할 짝.
    fan_out  : True 면 `1 <- n` (타겟 하나에 팔로워 전부), False 면 `n <- n` (인덱스 1:1).
    unpaired : `n <- n` 에서 짝을 못 찾고 남은 항목 수(개수 차이). `1 <- n` 이면 0 —
               타겟 1 / 팔로워 4 는 **정상**이라 경고할 일이 아니다.

    `one_to_many=True` 여도 타겟이 2개 이상이면 `n <- n` 으로 **조용히 폴백**한다.
    (A00110 Follow 탭의 `1<-n` 은 개수가 안 맞으면 에러를 내지만, 여기는 폴백이 요구 사항이다.)

    match() 와 UI 가 이 함수를 함께 쓴다 — 모드 판정이 두 군데로 갈라지면 로그에 찍히는
    모드와 실제 동작이 어긋난다.
    """
    if not targets or not followers:
        return [], False, 0

    if one_to_many and len(targets) == 1:
        return [(targets[0], flw) for flw in followers], True, 0

    n = min(len(targets), len(followers))
    return (list(zip(targets[:n], followers[:n])), False,
            abs(len(targets) - len(followers)))


def capture(targets, cache, normal_axis="y", notes=None):
    """targets 의 **월드 T/R/S 를 값으로** 떠서 cache 에 담고 스냅샷 키 목록을 돌려준다.

    로케이터를 만들어 위치를 기억하던 자리를 대신한다 — 씬에 노드를 만들지 않고,
    되돌릴 때 타겟 쪽 마야 호출이 통째로 빠진다.

    Args:
        targets:   오브젝트 / 컴포넌트(버텍스·CV·엣지·페이스) 이름 리스트.
                   이미 스냅샷인 항목은 그대로 통과시킨다(다시 캡처해도 안전).
        cache:     `snapshot_manager.SnapshotCache`.
        normal_axis: 버텍스 타겟의 노말을 실을 축. 매칭 때와 같은 값을 준다(기본 "y").
        notes:     실패 사유를 담을 리스트(선택). 하나가 실패해도 나머지는 계속 캡처한다.

    Returns:
        입력과 **길이·순서가 같은** 리스트. 캡처한 항목은 스냅샷 키로, 실패한 항목은 원래
        이름 그대로 들어간다 — Match 는 인덱스로 짝을 짓기 때문에 여기서 항목이 빠지면
        그 뒤의 짝이 통째로 어긋난다(실패해도 라이브 타겟으로는 계속 쓸 수 있다).

    오브젝트는 종류를 가리지 않고 **자기 월드 행렬**을 기억한다(`_capture_kind` 참고).
    """
    if not targets:
        raise ValueError("No targets. Add objects to the Targets list.")

    keys = []
    ctx = _Ctx()
    try:
        for tgt in targets:
            if snap.is_snapshot(tgt):
                # 이미 캐시된 항목 — 데이터가 남아 있으면 그대로 통과.
                if cache.get(tgt) is None:
                    _note(notes, "no cached transform for {0}".format(tgt))
                keys.append(tgt)
                continue
            try:
                kind, matrix = _sample(tgt, normal_axis, ctx)
            except Exception as exc:
                _note(notes, "{0} : {1}".format(tgt, exc))
                keys.append(tgt)          # 자리를 비우지 않는다(짝이 밀리지 않도록)
                continue
            keys.append(cache.add(tgt, kind, matrix))
    finally:
        ctx.dispose()

    return keys


def match(targets, followers, normal_axis="y",
          translate=True, rotate=True, scale=False, parent=False,
          cache=None, notes=None, one_to_many=True):
    """타겟에 팔로워를 매칭한다. 기본은 인덱스 1:1, 타겟이 하나면 전부 그 하나에.

    Args:
        targets:   타겟 오브젝트/컴포넌트/**스냅샷 키** 리스트.
        followers: 따라갈 오브젝트 리스트.
        normal_axis: 버텍스 타겟일 때 노말에 정렬할 follower 축("x"/"y"/"z"). 기본 "y".
        translate: 위치 매칭(기본 True). DOOTOOL 'Translation'.
        rotate:    회전 매칭(기본 True). DOOTOOL 'Rotation'.
        scale:     월드 스케일 매칭(기본 False). DOOTOOL 'Scale (Only in The World Space)'.
        parent:    매칭 후 follower 를 target 아래로 parent(기본 False).
                   DOOTOOL 'Parent Followers to Targets'.
        cache:     스냅샷 타겟을 해석할 `SnapshotCache`(선택).
        notes:     건너뛴 사유를 담을 리스트(선택).
        one_to_many: True(기본)이고 **타겟이 정확히 하나**면 그 하나에 **모든 팔로워**를
                   매칭한다(`1 <- n`). 타겟이 2개 이상이면 이 값과 무관하게 `n <- n`.
                   짝짓기는 `resolve_pairs()` 가 정한다.

    Returns:
        (matched_count, skipped_count). `n <- n` 에서 개수가 다르면 min 만큼만 매칭하고 차이를
        skipped 에 더한다(`1 <- n` 은 개수가 달라도 정상이라 더하지 않는다).
        한 쌍이 실패해도 **멈추지 않고** 나머지를 계속 매칭한다(사유는 notes 로).
    """
    if not targets:
        raise ValueError("No targets. Add objects to the Targets list.")
    if not followers:
        raise ValueError("No followers. Add objects to the Followers list.")

    pairs, _fan_out, unpaired = resolve_pairs(targets, followers, one_to_many)
    skipped = unpaired                             # 개수 차이는 호출부가 안내한다

    matched = 0
    ctx = _Ctx()
    try:
        with suspend_refresh():
            for tgt, flw in pairs:
                if snap.is_snapshot(flw):
                    # 추상 캐시는 씬에 없으니 움직일 수 없다(타겟으로만 쓴다).
                    _note(notes, "follower {0} is a cached item - nothing to move".format(flw))
                    skipped += 1
                    continue
                try:
                    _match_one(tgt, flw, normal_axis,
                               translate=translate, rotate=rotate, scale=scale,
                               ctx=ctx, cache=cache)
                except Exception as exc:
                    _note(notes, "{0} -> {1} : {2}".format(tgt, flw, exc))
                    skipped += 1
                    continue
                matched += 1
            # DOOTOOL 과 동일하게 매칭을 모두 마친 뒤 별도 패스로 parent 한다.
            # 같은 짝(pairs)을 쓴다 — 1 <- n 이면 팔로워 전부가 그 하나의 타겟 아래로 간다.
            if parent:
                unparented = 0
                for tgt, flw in pairs:
                    if snap.is_snapshot(flw):
                        continue
                    try:
                        if not _parent_one(flw, tgt):
                            unparented += 1
                    except Exception as exc:
                        _note(notes, "parent {0} : {1}".format(flw, exc))
                if unparented:
                    _note(notes, "{0} follower(s) not parented - a cached item "
                                 "cannot be a parent".format(unparented))
    finally:
        ctx.dispose()

    return matched, skipped


def create_and_match(targets, ctl_type, normal_axis="y", cache=None):
    """targets 수만큼 컨트롤(ctl_type)을 만들어 각 타겟 위치/방향에 즉시 매칭한다.

    Args:
        targets:   타겟 오브젝트/컴포넌트/스냅샷 키 리스트.
        ctl_type:  "locator" / "sphere" / "cube".
        normal_axis: 버텍스 타겟일 때 노말 정렬 축. 기본 "y".
        cache:     스냅샷 타겟을 해석할 `SnapshotCache`(선택) — 캐시해 둔 자리에
                   실제 컨트롤을 세우고 싶을 때 쓴다.

    Returns:
        생성된 컨트롤 transform 이름 리스트(타겟과 인덱스 1:1).
    """
    if not targets:
        raise ValueError("No targets. Add objects to the Targets list.")

    created = []
    ctx = _Ctx()
    try:
        with suspend_refresh():
            for _ in targets:
                created.append(_make_control(ctl_type))
            for tgt, flw in zip(targets, created):
                _match_one(tgt, flw, normal_axis, ctx=ctx, cache=cache)
    finally:
        ctx.dispose()

    return created
