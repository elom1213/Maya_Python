# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00470_MaterialTool - 메시 -> 셰이딩 엔진 -> 머티리얼 수집
#
# 씬을 **읽기만** 한다 - 선택(select)은 바꾸지만 노드·어트리뷰트는 건드리지 않는다.
#
# ★ 한 트랜스폼 아래 셰이프가 여럿일 수 있다(blendShape 타겟 정리, 임포트 잔재).
#   "첫 셰이프" 를 고르면 엉뚱한 곳의 머티리얼을 보고하거나 놓친다 - 여기서는
#   **non-intermediate 셰이프를 전부** 본다. 페이스별 할당도 셰이딩 엔진이 결국
#   셰이프에 연결되므로 같은 경로로 잡힌다.

import maya.cmds as cmds


def _long(name):
    found = cmds.ls(name, long=True) or []
    return found[0] if found else None


def geometry_shapes(node):
    """트랜스폼/셰이프 -> non-intermediate 셰이프 롱네임 목록(전부).

    셰이프를 직접 주면 그대로 돌려준다. 컴포넌트('pCube1.f[0]')도 받아들인다.
    """
    if not node:
        return []

    node = _long(node.split(".")[0])
    if node is None:
        return []

    if cmds.objectType(node, isAType="shape"):
        return [] if cmds.getAttr(node + ".intermediateObject") else [node]

    return cmds.listRelatives(node, shapes=True, noIntermediate=True,
                              fullPath=True) or []


def shading_engines(shape):
    """셰이프에 붙은 셰이딩 엔진 목록(순서 유지, 중복 제거).

    오브젝트 전체 할당과 페이스별 할당 양쪽을 잡기 위해 연결과 세트를 함께 본다.

    ★ v01.10 : **멤버가 있는 엔진만** 남긴다. 면을 전부 다른 머티리얼로 다시 배정한 메시는
    `instObjGroups` -> `initialShadingGroup` 연결이 그대로 남아 `listConnections` 에는 보이지만
    `listSets(object=shape)` 에는 없다(실측, mayapy 2024). 그대로 두면 쓰지도 않는
    `standardSurface1` 이 표에 한 줄 올라온다.
    """
    members_of = set(cmds.listSets(object=shape, type=1) or [])

    found = []

    for source in (
            cmds.listConnections(shape, type="shadingEngine") or [],
            sorted(members_of)):
        for engine in source:
            if engine in found or cmds.objectType(engine) != "shadingEngine":
                continue
            if engine not in members_of:
                continue
            found.append(engine)

    return found


def material_of(shading_engine):
    """셰이딩 엔진이 물고 있는 서피스 머티리얼 이름. 없으면 None."""
    connected = cmds.listConnections(
        shading_engine + ".surfaceShader", source=True, destination=False) or []

    if connected:
        return connected[0]

    # surfaceShader 가 비어 있어도 다른 슬롯(volume/displacement)에 물려 있을 수 있다.
    materials = cmds.ls(cmds.listConnections(shading_engine) or [], materials=True) or []

    return materials[0] if materials else None


def scan(nodes):
    """리스트업한 노드들에 붙은 머티리얼을 모은다.

    Returns:
        (assignments, warnings)
        assignments : [(머티리얼 이름, [그 머티리얼을 쓰는 노드, ...]), ...] - 발견 순서
        warnings    : 사람에게 알릴 만한 사정(셰이프 없음, 머티리얼 없음 등)
    """
    nodes = [n for n in (nodes or []) if n]
    if not nodes:
        return [], ["The mesh list is empty. Add the meshes to check."]

    warnings = []
    usage = []          # [(머티리얼, [노드...])] - dict 대신 순서를 지키는 목록
    index = {}

    for node in nodes:
        if not cmds.objExists(node):
            warnings.append("'{0}' is not in the scene anymore - skipped.".format(node))
            continue

        shapes = geometry_shapes(node)
        if not shapes:
            warnings.append("'{0}' has no renderable shape - skipped.".format(node))
            continue

        found_any = False

        for shape in shapes:
            for engine in shading_engines(shape):
                material = material_of(engine)
                if material is None:
                    warnings.append(
                        "'{0}' has no surface material on '{1}' - skipped.".format(
                            engine, node.split("|")[-1]))
                    continue

                found_any = True

                if material not in index:
                    index[material] = len(usage)
                    usage.append((material, []))

                users = usage[index[material]][1]
                if node not in users:
                    users.append(node)

        if not found_any:
            warnings.append(
                "'{0}' has no material assigned.".format(node.split("|")[-1]))

    return usage, warnings


def usage_map(assignments):
    """[(머티리얼, [노드...])] -> {머티리얼: [노드...]} (리포트에 곁들일 용도)."""
    return {material: list(nodes) for material, nodes in (assignments or [])}


def select_nodes(names):
    """씬에서 선택(리스트 행을 눌렀을 때). 없는 것은 조용히 건너뛴다."""
    alive = [n for n in (names or []) if n and cmds.objExists(n)]

    if not alive:
        return []

    cmds.select(alive, replace=True, noExpand=True)

    return alive


# ======================================================================
# 머티리얼 -> 페이스 (v01.10, 레거시 JUN_PY_ShaderTool_V01_04 의 Select Faces 이식)
# ======================================================================
#
# 레거시는 `cmds.select(셰이딩엔진)` 한 줄이었다 — 세트 멤버가 통째로 선택되므로
# ① 씬 전체가 잡혀 리스트에 담은 메시로 범위를 못 좁히고 ② 오브젝트째 배정된 메시는
# 페이스가 아니라 오브젝트가 선택됐다.
#
# 여기서는 `sets -q` 로 멤버를 받는다. 마야가 연속한 면을 `sphere.f[0:199]` 처럼 **구간으로
# 압축해서** 돌려주므로(체커보드처럼 안 이어지는 면은 하나씩) 페이스 문자열을 새로 만들 일이
# 없고, 엔진 하나에 질의 하나다. 범위 안의 메시만 남기고 오브젝트째 멤버는 `shape.f[*]` 로 바꿔
# 선택은 **한 번**이다.
#
# ★ 선택은 `cmds.select` 가 아니라 **API `MGlobal.setActiveSelectionList`** 로 한다(`select_faces`).
#   4만 면 체커보드(멤버 2만 개)에서 `cmds.select(문자열 2만 개)` 는 1.4초, 인덱스를
#   `MFnSingleIndexedComponent` 에 담아 API 로 넘기면 0.001초다(실측, mayapy 2024). 수집(`faces_of`)은
#   0.1초. API 가 실패하면 `cmds.select` 로 폴백한다.
#
# ★ `sets -q` 의 면별 멤버는 **트랜스폼** 기준이다(`sphere.f[0:199]`, 셰이프 아님). 범위를
#   셰이프로 갖고 있으니 멤버의 노드를 `geometry_shapes()` 로 셰이프에 풀어 비교한다.


def shading_engines_of_material(material):
    """머티리얼이 물린 셰이딩 엔진 목록(순서 유지 · 중복 제거).

    `surfaceShader` 뿐 아니라 어느 슬롯에 물렸든 잡는다 — `material_of()` 의 역방향.
    """
    if not material or not cmds.objExists(material):
        return []

    found = []
    for engine in cmds.listConnections(
            material, type="shadingEngine", source=False, destination=True) or []:
        if engine not in found:
            found.append(engine)
    return found


def _scope_shapes(meshes):
    """리스트에 담은 메시들 -> 롱네임 셰이프 집합. None 이면 '씬 전체'(= None 그대로)."""
    if meshes is None:
        return None

    shapes = set()
    for mesh in meshes:
        if mesh and cmds.objExists(mesh):
            shapes.update(geometry_shapes(mesh))
    return shapes


def _mesh_shapes_in_scope(node, scope, cache):
    """세트 멤버의 노드(트랜스폼 또는 셰이프) -> 범위 안의 **메시** 셰이프들.

    ★ 체커보드처럼 안 이어지는 면은 멤버가 면 하나씩 2만 개가 된다. 멤버마다 셰이프를 다시
    조회하면 2.3초, 노드별로 한 번만 조회하면 훨씬 빠르다(실측) - 그래서 `cache` 를 받는다.
    """
    if node not in cache:
        shapes = [sh for sh in geometry_shapes(node) if cmds.nodeType(sh) == "mesh"]
        if scope is not None:
            shapes = [sh for sh in shapes if sh in scope]
        cache[node] = shapes
    return cache[node]


def faces_of(materials, meshes=None):
    """머티리얼들이 붙은 **페이스 컴포넌트** 목록을 모은다.

    Args:
        materials : 머티리얼 이름들
        meshes    : 이 메시들(의 셰이프)로 범위를 좁힌다. **None 이면 씬 전체.**
                    빈 목록은 "아무 메시도 아님" 이라 결과가 비고 경고가 남는다.

    Returns:
        (faces, warnings)
        faces    : ['|a|aShape.f[*]', '|b.f[0:199]', ...] - 그대로 `cmds.select` 에 넘긴다.
                   오브젝트째 배정은 셰이프의 `f[*]`, 면별 배정은 세트가 준 구간 그대로.
        warnings : 사람에게 알릴 사정(엔진 없음 · 빈 범위 등)
    """
    materials = [m for m in (materials or []) if m]
    warnings = []

    if not materials:
        return [], ["No material given."]

    scope = _scope_shapes(meshes)
    if scope is not None and not scope:
        return [], ["The mesh list is empty - nothing to select faces on. "
                    "Add meshes, or turn off 'Listed meshes only'."]

    faces = []
    seen = set()
    cache = {}      # 멤버 노드 -> 범위 안 메시 셰이프들 (노드마다 한 번만 조회)

    def take(face):
        if face not in seen:
            seen.add(face)
            faces.append(face)

    for material in materials:
        engines = shading_engines_of_material(material)
        if not engines:
            warnings.append("'{0}' is not connected to any shading engine - skipped.".format(
                material.split("|")[-1]))
            continue

        for engine in engines:
            members = cmds.sets(engine, query=True) or []
            if not members:
                continue

            # 한 번에 롱네임으로 - 컴포넌트('sphere.f[0:3]')도 그대로 롱네임이 붙어 나온다.
            for member in cmds.ls(members, long=True) or []:
                node, _dot, component = member.partition(".")

                if component:
                    # 면별 배정 : 세트가 준 구간 그대로. 메시의 세트 멤버는 늘 f[...] 다.
                    if component.startswith("f[") and _mesh_shapes_in_scope(node, scope, cache):
                        take(member)
                else:
                    # 오브젝트째 배정 : 셰이프(또는 트랜스폼) -> 전체 면
                    for shape in _mesh_shapes_in_scope(node, scope, cache):
                        take(shape + ".f[*]")

    return faces, warnings


def meshes_of(faces):
    """페이스 컴포넌트 목록 -> 그 면들이 속한 메시 **트랜스폼** 롱네임(중복 제거, 순서 유지).

    `f[*]` 는 셰이프에, 면별 구간은 트랜스폼에 붙어 나오므로 둘을 트랜스폼으로 합친다.
    """
    out = []
    transform_of = {}       # 노드 -> 트랜스폼 (멤버 2만 개여도 노드마다 한 번만 조회)
    for face in faces or []:
        node = face.partition(".")[0]
        if node not in transform_of:
            transform = node
            if cmds.objExists(node) and cmds.objectType(node, isAType="shape"):
                parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
                transform = parents[0] if parents else node
            transform_of[node] = transform
        transform = transform_of[node]
        if transform not in out:
            out.append(transform)
    return out


def count_faces(faces):
    """페이스 컴포넌트 목록이 가리키는 면 개수(로그용). 구간은 산술로, `f[*]` 는 polyEvaluate."""
    total = 0
    for face in faces or []:
        node, _dot, component = face.partition(".")
        inner = component[2:-1] if component.startswith("f[") else ""
        if inner == "*":
            try:
                total += int(cmds.polyEvaluate(node, face=True))
            except Exception:
                pass
        elif ":" in inner:
            lo, hi = inner.split(":")
            total += int(hi) - int(lo) + 1
        elif inner:
            total += 1
    return total


def _face_indices_by_shape(faces):
    """페이스 컴포넌트 문자열들 -> {메시 셰이프 롱네임: [면 인덱스...] 또는 None(= 전부)}.

    `sets -q` 의 면별 멤버는 트랜스폼에 붙어 나오므로(`|sphere.f[0:199]`) 셰이프로 푼다 -
    마야가 `transform.f[i]` 를 해석할 때와 같이 **첫 non-intermediate 메시 셰이프**다.
    """
    shape_of = {}
    by_shape = {}

    for face in faces:
        node, _dot, component = face.partition(".")
        inner = component[2:-1] if component.startswith("f[") else ""
        if not inner:
            continue

        if node not in shape_of:
            meshes = [sh for sh in geometry_shapes(node) if cmds.nodeType(sh) == "mesh"]
            shape_of[node] = meshes[0] if meshes else None
        shape = shape_of[node]
        if shape is None:
            continue

        indices = by_shape.setdefault(shape, [])
        if indices is None:
            continue                       # 이미 '전부'
        if inner == "*":
            by_shape[shape] = None
        elif ":" in inner:
            lo, hi = inner.split(":")
            indices.extend(range(int(lo), int(hi) + 1))
        else:
            indices.append(int(inner))

    return by_shape


def _select_faces_api(faces):
    """인덱스를 `MFnSingleIndexedComponent` 에 담아 **한 번에** 활성 선택으로. 문자열 파싱이 없다."""
    import maya.api.OpenMaya as om

    by_shape = _face_indices_by_shape(faces)
    if not by_shape:
        raise RuntimeError("no mesh face to select")

    selection = om.MSelectionList()

    for shape, indices in by_shape.items():
        finder = om.MSelectionList()
        finder.add(shape)
        dag = finder.getDagPath(0)

        if indices is None:
            indices = range(om.MFnMesh(dag).numPolygons)

        component = om.MFnSingleIndexedComponent()
        handle = component.create(om.MFn.kMeshPolygonComponent)
        component.addElements(list(indices))

        selection.add((dag, handle), True)

    om.MGlobal.setActiveSelectionList(selection, om.MGlobal.kReplaceList)


def select_faces(faces):
    """페이스 컴포넌트들을 **한 번에** 고른다. 비어 있으면 선택을 건드리지 않고 [] 를 돌려준다.

    API 경로(`_select_faces_api`)가 기본이다 - `cmds.select` 는 컴포넌트 문자열 개수에 비례해
    느려진다(2만 개에 1.4초, API 는 0.001초). API 가 실패하면 `cmds.select` 로 돌아간다.
    """
    faces = [f for f in (faces or []) if f]
    if not faces:
        return []

    try:
        _select_faces_api(faces)
    except Exception:
        cmds.select(faces, replace=True)
    return faces
