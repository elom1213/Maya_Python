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


def _export_fbx(members, filepath):
    """members 를 FBX 로 내보낸다.

    깔끔한 계층으로 내보내기 위해 각 멤버를 월드(최상위)로 빼냈다가 내보낸 뒤 원래
    부모로 복원한다. 씬에 동일 이름이 있어도 안전하도록 노드/부모를 UUID 로 잡는다.
    """
    cmds = _cmds()

    # 원래 부모를 UUID 로 기록 (월드 최상위면 None).
    infos = []  # [(member_uuid, parent_uuid|None), ...]
    for member in members:
        parents = cmds.listRelatives(member, parent=True, fullPath=True) or []
        parent_uuid = _uuid(parents[0]) if parents else None
        member_uuid = _uuid(member)
        if member_uuid:
            infos.append((member_uuid, parent_uuid))

    # 월드로 빼내기 (이미 최상위면 그대로). UUID 는 reparent 후에도 유지된다.
    for member_uuid, parent_uuid in infos:
        if parent_uuid is None:
            continue
        cmds.parent(_path(member_uuid), world=True)

    # 선택 후 export selected.
    cmds.select([_path(m) for m, _ in infos])
    cmds.file(filepath, force=True, options="v=0;",
              typ="FBX export", pr=True, es=True)

    # 원래 부모로 복원 (월드 최상위였던 것은 그대로 둔다).
    for member_uuid, parent_uuid in infos:
        if parent_uuid is None:
            continue
        member_path = _path(member_uuid)
        parent_path = _path(parent_uuid)
        if member_path and parent_path:
            cmds.parent(member_path, parent_path)

    cmds.select(clear=True)


def export_sets(set_names, file_names, excluded_keys, export_path):
    """Set's Name TSL 의 각 objectSet 을 하나의 FBX 로 내보낸다.

    - set_names[i] 의 멤버를 모아 타입 필터(excluded_keys) 적용 후 남은 것만 내보낸다.
    - 파일명은 file_names[i] (없으면 세트 leaf 이름), ':' 는 '_' 로 치환, 겹치면 고유화.
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

        _export_fbx(kept, mainpath)

        logs.append("[OK] {0}  ->  {1}".format(set_name, mainpath))
        logs.append("     exported {0} object(s): {1}".format(
            len(kept), ", ".join(short_name(k) for k in kept)))
        if dropped:
            logs.append("     excluded {0} object(s): {1}".format(
                len(dropped), ", ".join(short_name(d) for d in dropped)))

    if not logs:
        logs.append("[WARN] No sets to export. Add objectSets first.")
    return logs
