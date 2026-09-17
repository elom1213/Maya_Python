# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00470_MaterialTool - Copy Material : 소스 메시 M 의 **면별** 머티리얼 배정을 M_i 에 그대로.
#
# 전제 : M_i 는 M 과 **같은 메시**(토폴로지 동일, 면 번호가 같은 자리를 가리킨다).
#
# ★ `listConnections(shape, type="shadingEngine")` 로는 **어느 면에 무엇이 붙었는지** 모른다.
#   그 목록의 첫 번째를 통째로 걸면 머티리얼이 하나인 메시에서만 맞는다.
#   면별 배정은 `MFnMesh.getConnectedShaders(instanceNumber)` 가 준다 -
#   셰이딩 엔진 목록 + 면마다 그중 몇 번인지(배정이 없으면 -1).
#   (A00275 Layer > Create 에서 같은 문제를 겪고 확인한 방식이다)
#
# 적용 규칙
#   * 면 개수가 다르면 **건드리지 않고 경고만** - 통째로 하나를 거는 것은 틀린 답이지 폴백이 아니다.
#   * 모든 면이 한 엔진이면 **셰이프째** 건다(면 단위 멤버를 남기지 않는다).
#   * 아니면 엔진마다 면을 연속 구간(`f[0:511]`)으로 묶어 `sets -forceElement` 한 번.
#   * 소스에서 배정이 없는(-1) 면은 대상도 **비운다** - "똑같이" 가 요청이다.
#     면 하나를 `sets -remove` 해서는 안 비워진다(오브젝트째 배정이면 무시, 면별이면
#     initialShadingGroup 으로 되돌아간다 - 실측). 대상 배정을 전부 걷어낸 뒤 다시 건다.
#   * 적용 후 대상의 배정을 **다시 읽어 소스와 비교**한다. 다르면 성공이라 하지 않는다.
#
# 소스 M 은 UUID 로 기억한다 - 기억한 뒤 이름을 바꾸거나 부모를 옮겨도 같은 메시를 찾는다.

import maya.cmds as cmds
import maya.api.OpenMaya as om


# ==========================================================================
# 노드 해석
# ==========================================================================

def _long(name):
    found = cmds.ls(name, long=True) or []
    return found[0] if found else None


def short(path):
    return (path or "").split("|")[-1]


def mesh_shapes(node):
    """트랜스폼/메시 셰이프/컴포넌트 -> non-intermediate **mesh** 셰이프 롱네임 목록."""
    if not node:
        return []
    path = _long(node.split(".")[0])
    if path is None:
        return []
    if cmds.nodeType(path) == "mesh":
        return [] if cmds.getAttr(path + ".intermediateObject") else [path]
    shapes = cmds.listRelatives(path, shapes=True, noIntermediate=True, fullPath=True) or []
    return [s for s in shapes if cmds.nodeType(s) == "mesh"]


def mesh_transform(node):
    """메시를 가진 트랜스폼 롱네임. 셰이프·컴포넌트를 줘도 트랜스폼으로 올린다. 아니면 None."""
    shapes = mesh_shapes(node)
    if not shapes:
        return None
    return cmds.listRelatives(shapes[0], parent=True, fullPath=True)[0]


def uuid_of(node):
    found = cmds.ls(node, uuid=True) or []
    return found[0] if found else None


def node_from_uuid(uuid):
    """UUID -> 현재 롱네임. 씬에서 사라졌으면 None."""
    if not uuid:
        return None
    found = cmds.ls(uuid, long=True) or []
    return found[0] if found else None


def remember_source(selection):
    """선택에서 첫 메시 트랜스폼을 찾아 (uuid, 롱네임). 없으면 (None, None)."""
    for item in selection or []:
        transform = mesh_transform(item)
        if transform:
            return uuid_of(transform), transform
    return None, None


# ==========================================================================
# 면별 배정 읽기
# ==========================================================================

def face_assignment(shape):
    """메시 셰이프의 면별 배정 -> (엔진 이름 목록, 면마다 엔진 인덱스 목록 / 없으면 -1)."""
    selection = om.MSelectionList()
    selection.add(shape)
    dag = selection.getDagPath(0)
    engines, face_index = om.MFnMesh(dag).getConnectedShaders(dag.instanceNumber())
    names = [om.MFnDependencyNode(engine).absoluteName().lstrip(":") for engine in engines]
    return names, list(face_index)


def per_face_engines(shape):
    """면마다 엔진 이름(없으면 None). 비교용."""
    names, face_index = face_assignment(shape)
    return [names[i] if i >= 0 else None for i in face_index]


def _face_engines(shape, face):
    """면 하나가 실제로 속한 셰이딩 엔진(세트 멤버십 기준, 오브젝트째 배정 포함)."""
    sets = cmds.listSets(object="{0}.f[{1}]".format(shape, face), type=1) or []
    return [s for s in sets if cmds.nodeType(s) == "shadingEngine"]


def face_ranges(faces):
    """정렬된 면 번호 -> 연속 구간 [(시작, 끝), ...]."""
    ranges = []
    start = previous = None
    for index in faces:
        if start is None:
            start = previous = index
        elif index == previous + 1:
            previous = index
        else:
            ranges.append((start, previous))
            start = previous = index
    if start is not None:
        ranges.append((start, previous))
    return ranges


def _members(shape, faces):
    return ["{0}.f[{1}:{2}]".format(shape, lo, hi) if lo != hi
            else "{0}.f[{1}]".format(shape, lo)
            for lo, hi in face_ranges(faces)]


def material_of(engine):
    connected = cmds.listConnections(engine + ".surfaceShader",
                                     source=True, destination=False) or []
    return connected[0] if connected else engine


# ==========================================================================
# 적용
# ==========================================================================

def _apply_to_shape(names, source_faces, target):
    """source 의 면별 배정(names, source_faces)을 target 셰이프에 건다. 경고 목록."""
    warnings = []
    used = set(source_faces)

    if len(used) == 1 and -1 not in used:
        cmds.sets(target, edit=True, forceElement=names[source_faces[0]])
        return warnings

    by_engine = {}
    unassigned = []
    for face, index in enumerate(source_faces):
        if index < 0:
            unassigned.append(face)
        else:
            by_engine.setdefault(index, []).append(face)

    if unassigned:
        # ★ 면 하나만 `sets -remove` 해서는 비워지지 않는다(mayapy 실측): 오브젝트째 걸린
        #   배정이면 조용히 무시되고, 면별 배정이면 마야가 그 면을 initialShadingGroup 으로
        #   되돌린다. 소스와 똑같이 **대상의 배정을 전부 걷어낸 뒤** 필요한 면만 건다.
        _clear_assignment(target)

    for index, faces in sorted(by_engine.items()):
        cmds.sets(_members(target, faces), edit=True, forceElement=names[index])

    if unassigned:
        warnings.append("{0} face(s) have no material on the source - left empty "
                        "on the target too.".format(len(unassigned)))
    return warnings


def _clear_assignment(shape):
    """셰이프의 셰이딩 엔진 멤버십을 오브젝트째 · 면별 모두 걷어낸다."""
    transform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
    owners = set(cmds.ls([shape, transform], long=True) or [])
    for engine in cmds.listSets(object=shape, type=1) or []:
        if cmds.nodeType(engine) != "shadingEngine":
            continue
        members = cmds.sets(engine, query=True) or []
        mine = [m for m in members if _long(m.split(".")[0]) in owners]
        if mine:
            cmds.sets(mine, edit=True, remove=engine)


def copy_material(source_uuid, targets):
    """UUID 로 기억한 소스 메시의 면별 머티리얼 배정을 targets 에 똑같이 건다.

    호출하는 쪽이 undo 청크로 감싼다.
    반환: dict(ok, message, copied=[target], skipped=[(target, why)], warnings=[str],
               materials=[머티리얼 이름])
    """
    result = {"ok": False, "message": "", "copied": [], "skipped": [],
              "warnings": [], "materials": []}

    source = node_from_uuid(source_uuid)
    if not source:
        result["message"] = ("The source mesh is not in the scene anymore. "
                             "Set the source again.")
        return result

    source_shapes = mesh_shapes(source)
    if not source_shapes:
        result["message"] = "'{0}' has no mesh shape.".format(short(source))
        return result

    # 셰이프마다 (엔진 이름, 면 인덱스)를 **적용 전에** 전부 읽어 둔다.
    source_data = [face_assignment(s) for s in source_shapes]
    if not any(names for names, _faces in source_data):
        result["message"] = "'{0}' has no material assigned.".format(short(source))
        return result

    for names, _faces in source_data:
        for engine in names:
            material = material_of(engine)
            if material not in result["materials"]:
                result["materials"].append(material)

    if not targets:
        result["message"] = "The target list is empty."
        return result

    seen = set()
    for item in targets:
        target = mesh_transform(item)
        if not target:
            result["skipped"].append((item, "not a mesh"))
            continue
        if target == source:
            result["skipped"].append((target, "this is the source mesh"))
            continue
        if target in seen:
            continue
        seen.add(target)

        target_shapes = mesh_shapes(target)
        if len(target_shapes) != len(source_shapes):
            result["skipped"].append((target, "{0} mesh shape(s), the source has {1}".format(
                len(target_shapes), len(source_shapes))))
            continue

        # 전부 검사한 뒤에 건다 - 셰이프 둘 중 하나만 바뀐 채로 남지 않게.
        mismatch = None
        for (names, faces), shape in zip(source_data, target_shapes):
            count = cmds.polyEvaluate(shape, face=True) or 0
            if count != len(faces):
                mismatch = "{0} faces, the source has {1}".format(count, len(faces))
                break
        if mismatch:
            result["skipped"].append((target, mismatch))
            continue

        try:
            for (names, faces), shape in zip(source_data, target_shapes):
                if not names:
                    continue
                for warning in _apply_to_shape(names, faces, shape):
                    result["warnings"].append("{0}: {1}".format(short(target), warning))
        except Exception as e:                              # noqa: BLE001
            result["skipped"].append((target, "assignment failed - {0}".format(e)))
            continue

        # 되읽어 확인한다 - 마야가 조용히 다른 결과를 냈다면 성공이라 하지 않는다.
        wrong = 0
        for (names, faces), shape in zip(source_data, target_shapes):
            expected = [names[i] if i >= 0 else None for i in faces]
            actual = per_face_engines(shape)
            for face, (want, got) in enumerate(zip(expected, actual)):
                if want == got:
                    continue
                # ★ 면별 배정을 걷어낸 메시에서 getConnectedShaders 는 **어느 세트에도 없는 면을
                #   initialShadingGroup 으로 보고한다**(mayapy 실측: sets -q 로는 멤버가 아닌데도).
                #   비어 있어야 할 면은 실제 세트 멤버십으로 다시 본다.
                if want is None and not _face_engines(shape, face):
                    continue
                wrong += 1
        if wrong:
            result["skipped"].append((target, "applied, but {0} face(s) still differ "
                                              "from the source".format(wrong)))
            continue

        result["copied"].append(target)

    if not result["copied"]:
        result["message"] = "Nothing was copied."
        return result

    result["ok"] = True
    result["message"] = ("Copy Material : {0} -> {1} mesh(es), {2} material(s).".format(
        short(source), len(result["copied"]), len(result["materials"])))
    return result
