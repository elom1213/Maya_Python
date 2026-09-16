# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - 메시 -> 셰이딩 엔진 -> 머티리얼 수집
#
# 씬을 **읽기만** 한다(이 툴은 아직 아무것도 바꾸지 않는다).
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
    """
    found = []

    for source in (
            cmds.listConnections(shape, type="shadingEngine") or [],
            cmds.listSets(object=shape, type=1) or []):
        for engine in source:
            if engine not in found and cmds.objectType(engine) == "shadingEngine":
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
