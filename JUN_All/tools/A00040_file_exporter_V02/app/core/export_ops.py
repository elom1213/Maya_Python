# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-03
# A00040_file_exporter_V02 - core logic (maya.cmds)
#
# 레거시 A00040_file_exporter/utility.py 의 내보내기 로직을 순수 함수로 이식하고,
# "타입 필터"(어떤 노드 타입을 FBX 에서 제외할지) 기능을 추가했다.
# UI 는 이 함수들만 호출한다(thin UI). Maya 밖에서도 import 가능하도록 cmds 는 lazy.

import os


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ================================================================
# 타입 필터 레지스트리
# ================================================================
#
# 내보낼 때 "포함/제외"를 개별 토글할 수 있는 타입 목록.
# - 여기에 등록된 타입만 UI 드롭다운에 체크박스로 노출된다.
# - 등록되지 않은 타입(curve, nurbsSurface 등)은 항상 포함(내보냄)된다.
# - 필터는 오직 "제외"만 한다: 체크 해제된 타입에 해당하는 멤버만 빠지고 나머지는 그대로.
#
# 새 타입을 추가하려면:
#   1) FILTER_TYPES 에 {"key", "label"} 항목 추가
#   2) _TYPE_MATCHERS 에 같은 key 로 판별 함수 추가
# 두 곳만 손대면 UI·로직 모두 자동 반영된다.

FILTER_TYPES = [
    {"key": "mesh",  "label": "Mesh"},
    {"key": "joint", "label": "Joint"},
]


def _shapes_of(node):
    """node(트랜스폼) 아래의 (intermediate 제외) shape 목록. 없으면 빈 리스트."""
    cmds = _cmds()
    if cmds is None:
        return []
    return cmds.listRelatives(
        node, shapes=True, fullPath=True, noIntermediate=True) or []


def _is_type(node, node_type):
    """node 자체가 node_type 이거나, 그 shape 중 하나가 node_type 이면 True.

    (mesh/nurbsCurve 등은 트랜스폼 아래 shape 로 존재하고, joint 는 노드 자체가 타입이다.)
    """
    cmds = _cmds()
    if cmds is None:
        return False
    try:
        if cmds.objectType(node) == node_type:
            return True
    except Exception:
        return False
    for shape in _shapes_of(node):
        if cmds.objectType(shape) == node_type:
            return True
    return False


# key -> 멤버 판별 함수. 새 타입 추가 시 여기에 항목을 더한다.
_TYPE_MATCHERS = {
    "mesh":  lambda node: _is_type(node, "mesh"),
    "joint": lambda node: _is_type(node, "joint"),
}


def member_matches_type(node, key):
    """멤버 node 가 필터 타입 key 에 해당하는지."""
    matcher = _TYPE_MATCHERS.get(key)
    return bool(matcher and matcher(node))


def filter_members(members, excluded_keys):
    """excluded_keys(체크 해제된 필터 타입)에 해당하는 멤버를 제외한다.

    반환: (kept, dropped) — 내보낼 멤버 목록, 제외된 멤버 목록.
    excluded_keys 가 비면 전부 유지한다.
    """
    if not excluded_keys:
        return list(members), []
    kept, dropped = [], []
    excluded = set(excluded_keys)
    for member in members:
        if any(member_matches_type(member, key) for key in excluded):
            dropped.append(member)
        else:
            kept.append(member)
    return kept, dropped


# ================================================================
# 파일명 조립 (Naming)
# ================================================================

def short_name(name):
    """DAG 경로/네임스페이스를 제거하고 leaf 이름만 반환. 'a|b:c' -> 'c'."""
    return name.split("|")[-1].split(":")[-1]


def build_file_names(set_names, token_specs):
    """세트마다 토큰을 조합해 파일명을 만든다.

    token_specs: 토큰별 dict 리스트. 각 dict:
        {"mode": "custom"|"setname", "text": "<custom 일 때 사용할 문자열>"}
      - "custom"  : text 를 그대로 토큰 값으로.
      - "setname" : 해당 세트의 이름(leaf)을 토큰 값으로(세트마다 달라짐).
    빈 토큰은 건너뛰어 '__' 가 생기지 않게 한다.
    반환: set_names 와 같은 길이의 파일명 리스트.
    """
    names = []
    for set_name in set_names:
        parts = []
        for spec in token_specs:
            if spec.get("mode") == "setname":
                value = short_name(set_name)
            else:
                value = spec.get("text", "")
            if value:
                parts.append(value)
        names.append("_".join(parts))
    return names


# ================================================================
# 경로 헬퍼
# ================================================================

def get_unique_filepath(filepath):
    """이미 존재하면 _000, _001 ... 을 붙여 겹치지 않는 경로를 반환."""
    filepath = filepath.replace("\\", "/")
    if not os.path.exists(filepath):
        return filepath

    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    index = 1
    while True:
        new_path = os.path.join(directory, "{0}_{1:03d}{2}".format(name, index, ext))
        new_path = new_path.replace("\\", "/")
        if not os.path.exists(new_path):
            return new_path
        index += 1


# ================================================================
# 내보내기
# ================================================================

class undo_chunk(object):
    """with undo_chunk(): ... 로 한 번의 Undo 로 묶는다."""

    def __enter__(self):
        cmds = _cmds()
        if cmds:
            cmds.undoInfo(openChunk=True)
        return self

    def __exit__(self, *args):
        cmds = _cmds()
        if cmds:
            cmds.undoInfo(closeChunk=True)
        return False


def _uuid(node):
    cmds = _cmds()
    uuids = cmds.ls(node, uuid=True) or []
    return uuids[0] if uuids else None


def _path(uuid):
    cmds = _cmds()
    paths = cmds.ls(uuid, long=True) or []
    return paths[0] if paths else None


def _safe_parent_to_world(node_path):
    """node_path 를 월드(최상위)로 빼낸다. 성공하면 True, 못 빼면 False.

    다음 경우 Maya 가 reparent 를 막는다(모두 예외를 삼키고 False):
      - 레퍼런스 오브젝트가 레퍼런스 부모 밑에 있음
      - transform 어트리뷰트가 잠김(locked)이거나 연결/컨스트레인(connected)되어 있음
        → 월드 위치 보존을 위해 t/r/s 를 세팅할 수 없어 실패
    """
    cmds = _cmds()
    try:
        cmds.parent(node_path, world=True)
        return True
    except Exception:
        return False


def _excluded_shapes_of(node, excluded_keys):
    """node 아래(non-intermediate) shape 중 excluded_keys 타입에 해당하는 것들."""
    return [shape for shape in _shapes_of(node)
            if any(member_matches_type(shape, key) for key in excluded_keys)]


def _set_intermediate(shape_path, state):
    """shape 의 intermediateObject 를 설정. 성공하면 True.

    intermediate shape 는 FBX 가 내보내지 않으므로, 레퍼런스처럼 계층에서 뺄 수 없는
    메시를 export 에서 제외할 때 쓴다(뷰포트에서도 잠시 사라졌다가 복원됨).
    attr 이 잠겨 있거나 실패하면 False.
    """
    cmds = _cmds()
    try:
        cmds.setAttr(shape_path + ".intermediateObject", bool(state))
        return True
    except Exception:
        return False


def _collect_excluded_in_hierarchy(root, excluded_keys):
    """root(포함) 이하 계층에서 excluded 타입에 해당하는 '최상위' 노드들을 반환한다.

    세트 멤버가 그룹이면 그 하위에 있는 mesh/joint 등도 필터의 영향을 받아야 한다.
    여기서 걸린 노드를 export 직전에 잠깐 계층 밖으로 빼내면(아래 _export_fbx),
    그룹은 유지하되 하위의 제외 타입만 FBX 에서 빠진다.

    이미 다른 제외 노드의 자손인 것은 뺀다(조상만 옮기면 자손도 함께 빠지므로 중복 방지).
    """
    cmds = _cmds()
    descendants = cmds.listRelatives(
        root, allDescendents=True, fullPath=True, type="transform") or []
    hierarchy = [root] + descendants

    matched = [n for n in hierarchy
               if any(member_matches_type(n, key) for key in excluded_keys)]

    tops = []
    for node in matched:
        # 조상 중 이미 matched 인 것이 있으면(= node 가 그 자손이면) 건너뛴다.
        if any(other != node and node.startswith(other + "|") for other in matched):
            continue
        tops.append(node)
    return tops


def _export_fbx(members, filepath, excluded_keys, keep_hierarchy=False):
    """members 를 FBX 로 내보낸다.

    - keep_hierarchy=False(기본): 각 멤버를 월드(최상위)로 빼냈다가 내보낸 뒤 원부모로 복원한다.
      FBX 에는 멤버가 부모 없이 루트로 들어간다(예: 'grp>joint_01' -> 'joint_01').
    - keep_hierarchy=True: 멤버를 옮기지 않고 제자리에서 내보낸다. FBX export selected 는
      조상(부모) 체인은 유지하되 형제 가지는 제외하므로, 씬 계층이 보존된다
      (예: 'grp>joint_01' -> 'grp>joint_01').
    - excluded_keys 가 있으면 (모드와 무관하게) 각 멤버 '계층 내부'의 제외 타입 노드(그룹 하위
      mesh/joint 등)를 export 직전에 월드로 빼냈다가 export 후 원부모로 복원한다.
    - 씬에 동일 이름이 있어도 안전하도록 노드/부모를 UUID 로 잡는다.
    - 멤버가 (잠김/연결/레퍼런스 등으로) 월드로 뺄 수 없으면 제자리에서 내보낸다(복원 생략).
    - 제외 타입 노드 처리: shape 기반(mesh 등)은 shape 의 intermediateObject 를 켜서 제외하고
      (reparent 불필요 → 잠금/연결/레퍼런스와 무관하게 동작), shape 없는 타입(joint)만 월드로
      빼낸다. 둘 다 안 되는 것만 제외 불가로 남는다. export 후 모두 원복.
    반환: (excluded_names, excluded_failed)
      excluded_names  : FBX 에서 실제로 제외된 하위 노드의 leaf 이름 리스트.
      excluded_failed : shape 도 없고 뺄 수도 없어 FBX 에 남은 제외 대상 이름.
    """
    cmds = _cmds()

    # 1) 멤버 원부모를 UUID 로 기록 (월드 최상위면 None) 후 (기본 모드면) 월드로 빼내기.
    #    빼내기에 성공한 멤버만 moved 에 담아, 복원 대상을 그것으로 한정한다.
    member_infos = []  # [(member_uuid, parent_uuid|None), ...]
    for member in members:
        parents = cmds.listRelatives(member, parent=True, fullPath=True) or []
        parent_uuid = _uuid(parents[0]) if parents else None
        member_uuid = _uuid(member)
        if member_uuid:
            member_infos.append((member_uuid, parent_uuid))

    moved_members = set()
    for member_uuid, parent_uuid in ([] if keep_hierarchy else member_infos):
        if parent_uuid is None:
            continue
        node_path = _path(member_uuid)
        if node_path and _safe_parent_to_world(node_path):
            moved_members.add(member_uuid)

    # 2) 각 멤버 계층 내부의 제외 타입 노드를 FBX 에서 뺀다.
    #    a) shape 기반 타입(mesh 등): 해당 shape 의 intermediateObject 를 켜서 제외한다.
    #       노드를 옮기지 않으므로(reparent 불필요) 잠금/연결/컨스트레인/레퍼런스/네임스페이스와
    #       무관하게 항상 동작한다. FBX 는 intermediate shape 를 내보내지 않는다.
    #    b) shape 가 없는 타입(joint 등): 통째로 월드로 빼낸다(안 되면 제외 불가로 남긴다).
    excluded_infos = []   # 월드로 빼낸 [(node_uuid, parent_uuid), ...]
    hidden_shapes = []    # intermediate 로 숨긴 shape uuid (복원용)
    excluded_names = []
    excluded_failed = []  # shape 도 없고 뺄 수도 없어 FBX 에 남은 제외 대상
    if excluded_keys:
        for member_uuid, _ in member_infos:
            root = _path(member_uuid)
            if not root:
                continue
            for node in _collect_excluded_in_hierarchy(root, excluded_keys):
                node_uuid = _uuid(node)
                if not node_uuid:
                    continue

                # a) shape 기반: shape 를 intermediate 로 숨김 (가장 안전, reparent 없음)
                hidden_any = False
                for shape in _excluded_shapes_of(node, excluded_keys):
                    shape_uuid = _uuid(shape)
                    if shape_uuid and _set_intermediate(shape, True):
                        hidden_shapes.append(shape_uuid)
                        hidden_any = True
                if hidden_any:
                    excluded_names.append(short_name(node))
                    continue

                # b) shape 없는 타입(joint 등): 통째로 월드로 빼내기
                parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
                parent_uuid = _uuid(parents[0]) if parents else None
                node_path = _path(node_uuid)
                if parent_uuid is not None and node_path and _safe_parent_to_world(node_path):
                    excluded_infos.append((node_uuid, parent_uuid))
                    excluded_names.append(short_name(node))
                else:
                    # 옮길 수도 숨길 수도 없음(shape 없고 잠김/연결/레퍼런스 등) → 제외 불가
                    excluded_failed.append(short_name(node))

    # 3) 선택 후 export selected.
    cmds.select([_path(m) for m, _ in member_infos])
    cmds.file(filepath, force=True, options="v=0;",
              typ="FBX export", pr=True, es=True)

    # 4) 복원: intermediate 로 숨긴 shape 해제 → 빼낸 제외 노드 원부모 → 멤버 원부모.
    for shape_uuid in hidden_shapes:
        shape_path = _path(shape_uuid)
        if shape_path:
            _set_intermediate(shape_path, False)

    for node_uuid, parent_uuid in excluded_infos:
        node_path = _path(node_uuid)
        parent_path = _path(parent_uuid)
        if node_path and parent_path:
            cmds.parent(node_path, parent_path)

    for member_uuid, parent_uuid in member_infos:
        if parent_uuid is None or member_uuid not in moved_members:
            continue
        member_path = _path(member_uuid)
        parent_path = _path(parent_uuid)
        if member_path and parent_path:
            cmds.parent(member_path, parent_path)

    cmds.select(clear=True)
    return excluded_names, excluded_failed


def export_sets(set_names, file_names, excluded_keys, export_path,
                keep_hierarchy=False):
    """Set's Name TSL 의 각 objectSet 을 하나의 FBX 로 내보낸다.

    - set_names[i] 의 멤버를 모아 타입 필터(excluded_keys) 적용 후 남은 것만 내보낸다.
    - 파일명은 file_names[i] (없으면 세트 leaf 이름), ':' 는 '_' 로 치환, 겹치면 고유화.
    - keep_hierarchy=False(기본): 멤버를 씬 최상위로 빼서 내보낸다.
      True: 씬 계층(부모)을 유지한 채 내보낸다. (자세한 동작은 _export_fbx 참고)
    반환: 로그 문자열 리스트.
    """
    cmds = _cmds()
    if cmds is None:
        return ["[FAIL] Maya not available."]

    if not export_path:
        return ["[FAIL] Check export path."]

    logs = []
    cmds.select(clear=True)

    for i, set_name in enumerate(set_names):
        file_name = file_names[i] if i < len(file_names) and file_names[i] else short_name(set_name)

        if not cmds.objExists(set_name):
            logs.append("[SKIP] {0} does not exist.".format(set_name))
            continue
        if cmds.objectType(set_name) != "objectSet":
            logs.append("[SKIP] {0} is not an objectSet.".format(set_name))
            continue

        members = cmds.sets(set_name, q=True) or []
        if not members:
            logs.append("[SKIP] {0} has no members.".format(set_name))
            continue

        kept, dropped = filter_members(members, excluded_keys)
        if not kept:
            logs.append(
                "[FAIL] {0}: nothing left to export after type filter.".format(set_name))
            continue

        file_name = file_name.replace(":", "_")
        mainpath = "{0}/{1}.fbx".format(export_path, file_name).replace("\\", "/")
        mainpath = get_unique_filepath(mainpath)

        excluded_desc, excluded_failed = _export_fbx(
            kept, mainpath, excluded_keys, keep_hierarchy)

        logs.append("[OK] {0}  ->  {1}".format(set_name, mainpath))
        logs.append("     exported {0} member(s): {1}".format(
            len(kept), ", ".join(short_name(k) for k in kept)))
        # 필터로 빠진 것: 세트에 직접 든 멤버(dropped) + 그룹 하위 노드(excluded_desc)
        excluded_all = [short_name(d) for d in dropped] + excluded_desc
        if excluded_all:
            logs.append("     excluded {0} object(s): {1}".format(
                len(excluded_all), ", ".join(excluded_all)))
        # shape 도 없고(joint 등) 계층에서도 뺄 수 없어 부득이 FBX 에 남은 제외 대상
        if excluded_failed:
            logs.append("     [WARN] could not exclude {0} object(s) "
                        "(no shape to hide and cannot be unparented), "
                        "still in FBX: {1}".format(
                            len(excluded_failed), ", ".join(excluded_failed)))

    if not logs:
        logs.append("[WARN] No sets to export. Add objectSets first.")
    return logs
