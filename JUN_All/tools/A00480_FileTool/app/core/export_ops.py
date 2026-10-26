# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00480_FileTool - Export 탭 로직 (maya.cmds)
#
# 2026-10-26 : 타입 필터 레지스트리 · 계층 펼치기(collect_export_nodes) · FBXExport* 옵션 한시 변경(fbx_options) · 고유 경로 ·
#   short_name 을 **`Framework.core.maya_fbx` 로 올렸다** (A00210_FileManager Maya > Export 하위탭이 같은 코드를 쓴다 -
#   릴리즈본은 툴 간 import 금지). 이 모듈은 그 이름들을 재노출하고, 세트 단위 내보내기(export_sets · _export_fbx)만 갖는다.
#   **동작은 같다** (collect_export_nodes 의 새 인자 prune_constraints 는 기본 False = 옛 동작).
#
# A00040_file_exporter_V02(v02.09) export_ops 를 옮겼다. 바뀐 것:
#   - 자체 undo_chunk 복제를 지웠다 → UI 가 공용 Framework.core.maya_undo.undo_chunk 를 쓴다.
#   - FBX 플러그인 로드를 공용 ensure_fbx_plugin 으로. 플러그인이 없으면 export_sets 가 트레이스백 대신 [FAIL] 로그를 돌려준다.
#
# --- 원본 헤더 ---
# 레거시 A00040_file_exporter/utility.py 의 내보내기 로직을 순수 함수로 이식하고,
# "타입 필터"(어떤 노드 타입을 FBX 에서 제외할지) 기능을 추가했다.
# v02.06: joint 하위의 non-joint 노드를 FBX 에서 빼는 "Joints only" 옵션 추가.
#   제외는 노드를 옮기거나 고치지 않고, 내보낼 노드를 명시로 선택한 뒤
#   FBXExportIncludeChildren 을 꺼서 처리한다 → 씬 계층은 export 전후로 동일하다.
# UI 는 이 함수들만 호출한다(thin UI). Maya 밖에서도 import 가능하도록 cmds 는 lazy.

from Framework.core.maya_fbx import (  # noqa: F401 - 재노출 (UI · 다른 모듈이 export_ops.X 로 부른다)
    ensure_fbx_plugin,
    FILTER_TYPES, _TYPE_MATCHERS, member_matches_type, filter_members,
    short_name, is_type as _is_type, is_joint as _is_joint, JOINT_TYPE,
    collect_export_nodes, get_unique_filepath,
    fbx_options, _FBX_OPTIONS,
)


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ================================================================
# 내보내기
# ================================================================

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
    has_joint = any(_is_joint(node) for node in export_nodes)
    include_children = False if pruned else None
    input_connections = False if (joints_only and has_joint) else None

    cmds.select(export_nodes if pruned else member_paths)
    with fbx_options(include_children=include_children,
                     input_connections=input_connections):
        cmds.file(filepath, force=True, options="v=0;",
                  typ="FBX export", pr=True, es=True)

    # 4) 복원: 월드로 빼낸 멤버를 원부모로.
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

    plugin_ok, plugin_logs = ensure_fbx_plugin()
    if not plugin_ok:
        return plugin_logs + ["[FAIL] Cannot export FBX without the plugin."]

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
        excluded_all = [short_name(d) for d in dropped] + excluded_desc
        if excluded_all:
            logs.append("     excluded {0} object(s): {1}".format(
                len(excluded_all), ", ".join(excluded_all)))

    if not logs:
        logs.append("[WARN] No sets to export. Add objectSets first.")
    return logs
