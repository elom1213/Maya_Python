# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00040_file_exporter_V02 - core logic (maya.cmds)
#
# 레거시 A00040_file_exporter/utility.py 의 내보내기 로직을 순수 함수로 이식하고,
# "타입 필터"(어떤 노드 타입을 FBX 에서 제외할지) 기능을 추가했다.
# v02.06: joint 하위의 non-joint 노드를 FBX 에서 빼는 "Joints only" 옵션 추가.
#   제외는 노드를 옮기거나 고치지 않고, 내보낼 노드를 명시로 선택한 뒤
#   FBXExportIncludeChildren 을 꺼서 처리한다 → 씬 계층은 export 전후로 동일하다.
# UI 는 이 함수들만 호출한다(thin UI). Maya 밖에서도 import 가능하도록 cmds 는 lazy.

import os


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


def _mel():
    """maya.mel 을 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.mel as mel
        return mel
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


JOINT_TYPE = "joint"


def _is_joint(node):
    """node 가 joint 타입인지. (joint 는 shape 이 아니라 노드 자체가 타입이다.)"""
    cmds = _cmds()
    try:
        return cmds.objectType(node) == JOINT_TYPE
    except Exception:
        return False


def collect_export_nodes(root, excluded_keys, joints_only=True):
    """root 계층을 펼쳐 FBX 에 담을 노드와 뺄 노드를 가른다. **씬은 건드리지 않는다.**

    - joints_only=True : joint 아래(자손)에 있는 non-joint 노드를 통째로(그 자손까지) 뺀다.
      조인트를 뽑을 때 그 밑에 매달린 메시 · 로케이터 · 컨스트레인트 노드 · 그룹이 FBX 에
      섞이지 않게 한다. joint 밑의 그룹 안에 다시 joint 가 있어도, 그 그룹이 빠지면 부모를
      잃으므로 하위 joint 까지 함께 뺀다(계층을 임의로 재배치하지 않는다).
    - excluded_keys : 타입 필터에서 체크 해제된 타입도 같은 방식으로 뺀다(자손 포함).
    - root(세트 멤버) 자신은 여기서 거르지 않는다 — filter_members 가 이미 걸렀다.

    반환: (kept, pruned) — 둘 다 fullPath 리스트.
    """
    cmds = _cmds()
    if cmds is None:
        return [root], []

    kept, pruned = [], []
    stack = [(root, False)]  # (fullPath, 조상 중에 joint 가 있는가)
    while stack:
        node, under_joint = stack.pop()

        if node != root:
            if excluded_keys and any(member_matches_type(node, key)
                                     for key in excluded_keys):
                pruned.append(node)
                continue
            if joints_only and under_joint and not _is_joint(node):
                pruned.append(node)
                continue

        kept.append(node)

        try:
            children = cmds.listRelatives(
                node, children=True, fullPath=True, type="transform") or []
        except Exception:
            children = []
        child_under_joint = under_joint or _is_joint(node)
        for child in children:
            stack.append((child, child_under_joint))

    return kept, pruned


# ================================================================
# FBX 익스포터 옵션 (MEL FBXExport*)
# ================================================================
#
# cmds.file(typ="FBX export") 는 FBX 플러그인의 현재 옵션을 그대로 따른다.
# 아래 옵션을 잠깐 바꿨다가 export 후 원래 값으로 되돌린다.
#   FBXExportIncludeChildren  : False 면 "선택한 노드만" 내보낸다(자손 자동 포함 안 함).
#                               → 선택 목록으로 FBX 내용을 정확히 통제할 수 있고, 씬 계층을
#                                 전혀 건드리지 않아도 된다. 선택 안 한 조상(부모 그룹)은
#                                 계층 유지용으로 그대로 따라 나온다.
#   FBXExportInputConnections : False 면 선택 노드에 입력으로 연결된 노드(컨스트레인트
#                               드라이버 등)를 딸려 보내지 않는다. joint 만 뽑을 때 컨트롤러
#                               로케이터가 FBX 루트에 섞여 들어오는 것을 막는다.

_FBX_OPTIONS = {
    "include_children": "FBXExportIncludeChildren",
    "input_connections": "FBXExportInputConnections",
}


class fbx_options(object):
    """with fbx_options(include_children=False): ... 로 FBX 옵션을 한시적으로 바꾼다.

    None 인 항목은 손대지 않는다. 플러그인이 없거나 명령이 실패하면 조용히 넘어간다
    (그 경우 기존 동작 그대로 export 된다).
    """

    def __init__(self, include_children=None, input_connections=None):
        self._wanted = {
            "include_children": include_children,
            "input_connections": input_connections,
        }
        self._previous = {}

    def _eval(self, command):
        mel = _mel()
        if mel is None:
            return None
        try:
            return mel.eval(command)
        except Exception:
            return None

    def __enter__(self):
        cmds = _cmds()
        if cmds is not None and not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
            try:
                cmds.loadPlugin("fbxmaya", quiet=True)
            except Exception:
                pass
        for key, value in self._wanted.items():
            if value is None:
                continue
            command = _FBX_OPTIONS[key]
            current = self._eval("{0} -q".format(command))
            if current is None:
                continue
            self._previous[key] = bool(current)
            self._eval("{0} -v {1}".format(command, "true" if value else "false"))
        return self

    def __exit__(self, *args):
        for key, value in self._previous.items():
            self._eval("{0} -v {1}".format(
                _FBX_OPTIONS[key], "true" if value else "false"))
        self._previous = {}
        return False


def _export_fbx(members, filepath, excluded_keys, keep_hierarchy=False,
                joints_only=True):
    """members 를 FBX 로 내보낸다.

    - keep_hierarchy=False(기본): 각 멤버를 월드(최상위)로 빼냈다가 내보낸 뒤 원부모로 복원한다.
      FBX 에는 멤버가 부모 없이 루트로 들어간다(예: 'grp>joint_01' -> 'joint_01').
    - keep_hierarchy=True: 멤버를 옮기지 않고 제자리에서 내보낸다. 조상(부모) 체인은 유지되고
      형제 가지는 빠지므로 씬 계층이 보존된다(예: 'grp>joint_01' -> 'grp>joint_01').
    - joints_only=True: joint 하위의 non-joint 노드를 FBX 에서 뺀다.
    - excluded_keys: 타입 필터에서 체크 해제된 타입을 FBX 에서 뺀다.

    뺄 노드가 있으면 **노드를 옮기거나 고치는 대신** 내보낼 노드를 전부 명시로 선택하고
    FBXExportIncludeChildren 을 끈 채 export 한다. 그래서 필터 · joints_only 는 씬 계층을
    전혀 바꾸지 않는다(레퍼런스 · 잠긴 채널 · 컨스트레인된 노드도 그대로 처리된다).
    씬을 실제로 건드리는 것은 keep_hierarchy=False 의 멤버 이동뿐이며, export 후 원부모로
    되돌린다. 씬에 동일 이름이 있어도 안전하도록 노드/부모는 UUID 로 잡는다.

    반환: excluded_names — FBX 에서 빠진 하위 노드의 leaf 이름 리스트.
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

    # 2) 멤버 이동 뒤의 경로로 계층을 펼쳐, 내보낼 노드와 뺄 노드를 가른다.
    member_paths = [p for p in (_path(m) for m, _ in member_infos) if p]
    export_nodes, pruned = [], []
    for root in member_paths:
        kept, dropped = collect_export_nodes(root, excluded_keys, joints_only)
        export_nodes.extend(kept)
        pruned.extend(dropped)

    # 3) 선택 후 export selected.
    #    - 뺄 게 있으면 펼친 목록을 그대로 선택하고 IncludeChildren 을 끈다.
    #    - 뺄 게 없으면 기존과 동일하게 멤버만 선택하고 옵션도 건드리지 않는다.
    has_joint = any(_is_joint(node) for node in export_nodes)
    include_children = False if pruned else None
    # joint 를 내보낼 때는 컨스트레인트 드라이버 등 입력 연결 노드가 딸려오지 않게 한다.
    input_connections = False if (joints_only and has_joint) else None

    cmds.select(export_nodes if pruned else member_paths)
    with fbx_options(include_children=include_children,
                     input_connections=input_connections):
        cmds.file(filepath, force=True, options="v=0;",
                  typ="FBX export", pr=True, es=True)

    # 4) 복원: 월드로 빼낸 멤버를 원부모로. (필터/joints_only 는 씬을 건드리지 않았다.)
    for member_uuid, parent_uuid in member_infos:
        if parent_uuid is None or member_uuid not in moved_members:
            continue
        member_path = _path(member_uuid)
        parent_path = _path(parent_uuid)
        if member_path and parent_path:
            cmds.parent(member_path, parent_path)

    cmds.select(clear=True)
    return [short_name(node) for node in pruned]


def export_sets(set_names, file_names, excluded_keys, export_path,
                keep_hierarchy=False, joints_only=True):
    """Set's Name TSL 의 각 objectSet 을 하나의 FBX 로 내보낸다.

    - set_names[i] 의 멤버를 모아 타입 필터(excluded_keys) 적용 후 남은 것만 내보낸다.
    - 파일명은 file_names[i] (없으면 세트 leaf 이름), ':' 는 '_' 로 치환, 겹치면 고유화.
    - keep_hierarchy=False(기본): 멤버를 씬 최상위로 빼서 내보낸다.
      True: 씬 계층(부모)을 유지한 채 내보낸다. (자세한 동작은 _export_fbx 참고)
    - joints_only=True(기본): joint 하위의 non-joint 노드를 FBX 에서 뺀다(씬은 그대로).
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

        excluded_desc = _export_fbx(
            kept, mainpath, excluded_keys, keep_hierarchy, joints_only)

        logs.append("[OK] {0}  ->  {1}".format(set_name, mainpath))
        logs.append("     exported {0} member(s): {1}".format(
            len(kept), ", ".join(short_name(k) for k in kept)))
        # 필터/joints_only 로 빠진 것: 세트에 직접 든 멤버(dropped) + 하위 노드(excluded_desc)
        excluded_all = [short_name(d) for d in dropped] + excluded_desc
        if excluded_all:
            logs.append("     excluded {0} object(s): {1}".format(
                len(excluded_all), ", ".join(excluded_all)))

    if not logs:
        logs.append("[WARN] No sets to export. Add objectSets first.")
    return logs
