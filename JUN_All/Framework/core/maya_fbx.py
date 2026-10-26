# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.core.maya_fbx - FBX 플러그인 · "선택한 것만" FBX 내보내기 헬퍼 (maya.cmds lazy, Maya 밖에서 import 가능)
#
# 2026-10-26 A00480_FileTool `app/core/fbx_plugin.py` + `export_ops.py` 의 FBX 부분(타입 필터 · 계층 펼치기 · FBXExport*
# 옵션 한시 변경 · 고유 경로)을 공용으로 올렸다. A00480 두 모듈은 재노출(동작 동일). A00210_FileManager Maya > Export
# 하위탭(mayapy 워커)이 같은 코드로 FBX 를 쓴다 - 릴리즈본은 툴 간 import 금지라 Framework 에 두어야 두 툴에 다 실린다.
#
# 핵심 (메모리 fbx-export-selected-scope, mayapy 2024 실측):
#   - `cmds.file(typ="FBX export", es=True)` 가 무엇을 담을지는 MEL `FBXExport*` **전역 옵션**이 정한다.
#     FBXExportIncludeChildren false → 선택한 노드만(선택 안 한 조상은 계층 유지용으로 따라 나온다, 자손은 빠진다).
#     FBXExportInputConnections false → 컨스트레인트 드라이버 같은 입력 연결 노드가 FBX 루트에 섞이지 않는다.
#     FBXExportBakeComplexAnimation false → 익스포터가 다시 샘플하지 않는다 (이미 베이크한 커브를 그대로).
#   - 그래서 노드를 옮기거나 숨기지 않고 **내보낼 노드를 전부 명시로 선택**하면 FBX 내용을 정확히 통제한다.
#   - FBX 의 타임스팬(언리얼 "Exported Time")은 내보낼 때의 `playbackOptions min/max` 다 (2026-10-26 실측, ascii FBX Takes).
#   - 레퍼런스 노드를 그대로 내보내면 노드 이름에 네임스페이스(`CHN:root`)가 **남는다** (실측) - 호출부가 임포트 · 네임스페이스
#     제거를 먼저 한다.

import os


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


def _mel():
    try:
        import maya.mel as mel
        return mel
    except Exception:
        return None


# ================================================================
# 플러그인
# ================================================================

FBX_PLUGIN = "fbxmaya"


def ensure_fbx_plugin():
    """`fbxmaya` 를 올린다. 반환: (성공 여부, 로그 리스트). 이미 올라와 있으면 (True, [])."""
    cmds = _cmds()
    if cmds is None:
        return False, ["[FAIL] Maya not available."]
    try:
        loaded = cmds.pluginInfo(FBX_PLUGIN, query=True, loaded=True)
    except RuntimeError:
        loaded = False
    if loaded:
        return True, []
    try:
        cmds.loadPlugin(FBX_PLUGIN, quiet=True)
    except RuntimeError:
        return False, ["[WARN] FBX plugin ('{0}') is not available.".format(FBX_PLUGIN)]
    return True, []


# ================================================================
# 이름 · 타입
# ================================================================

JOINT_TYPE = "joint"


def short_name(name):
    """DAG 경로/네임스페이스를 제거하고 leaf 이름만. 'a|b:c' -> 'c'."""
    return name.split("|")[-1].split(":")[-1]


def _shapes_of(node):
    cmds = _cmds()
    if cmds is None:
        return []
    return cmds.listRelatives(node, shapes=True, fullPath=True, noIntermediate=True) or []


def is_type(node, node_type):
    """node 자체가 node_type 이거나 그 shape 중 하나가 node_type 이면 True (mesh 는 shape, joint 는 노드 자체)."""
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


def is_joint(node):
    cmds = _cmds()
    try:
        return cmds.objectType(node) == JOINT_TYPE
    except Exception:
        return False


def is_constraint(node):
    """parentConstraint · scaleConstraint ... (nodeType 상속에 'constraint')."""
    cmds = _cmds()
    try:
        return "constraint" in (cmds.nodeType(node, inherited=True) or [])
    except Exception:
        return False


# ================================================================
# 타입 필터 레지스트리 (A00480 Export 탭의 드롭다운이 읽는다)
# ================================================================
#
# 등록된 타입만 체크박스로 노출되고, 필터는 "제외" 만 한다. 새 타입 = FILTER_TYPES 한 줄 + _TYPE_MATCHERS 한 줄.

FILTER_TYPES = [
    {"key": "mesh",  "label": "Mesh"},
    {"key": "joint", "label": "Joint"},
]

_TYPE_MATCHERS = {
    "mesh":  lambda node: is_type(node, "mesh"),
    "joint": lambda node: is_type(node, "joint"),
}


def member_matches_type(node, key):
    matcher = _TYPE_MATCHERS.get(key)
    return bool(matcher and matcher(node))


def filter_members(members, excluded_keys):
    """excluded_keys 에 해당하는 멤버를 뺀다. 반환 (kept, dropped)."""
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
# 계층 펼치기
# ================================================================

def collect_export_nodes(root, excluded_keys, joints_only=True, prune_constraints=False):
    """root 계층을 펼쳐 FBX 에 담을 노드와 뺄 노드를 가른다. **씬은 건드리지 않는다.**

    - joints_only : joint 아래(자손)의 non-joint 노드를 통째로(그 자손까지) 뺀다. joint 밑 그룹 안의 joint 도
      그룹과 함께 빠진다(계층을 임의로 재배치하지 않는다).
    - excluded_keys : 타입 필터에서 체크 해제된 타입도 같은 방식으로(자손 포함).
    - prune_constraints : 컨스트레인트 노드(조인트의 자식으로 생긴다)를 어디서든 뺀다. A00210 Export 가 켠다
      (베이크 뒤 끊긴 컨스트레인트가 FBX 에 빈 노드로 남지 않게). A00480 은 기존 동작 유지(False).
    - root 자신은 거르지 않는다.
    반환 (kept, pruned) - 둘 다 fullPath.
    """
    cmds = _cmds()
    if cmds is None:
        return [root], []
    kept, pruned = [], []
    stack = [(root, False)]
    while stack:
        node, under_joint = stack.pop()
        if node != root:
            if prune_constraints and is_constraint(node):
                pruned.append(node)
                continue
            if excluded_keys and any(member_matches_type(node, key) for key in excluded_keys):
                pruned.append(node)
                continue
            if joints_only and under_joint and not is_joint(node):
                pruned.append(node)
                continue
        kept.append(node)
        try:
            children = cmds.listRelatives(node, children=True, fullPath=True, type="transform") or []
        except Exception:
            children = []
        child_under_joint = under_joint or is_joint(node)
        for child in children:
            stack.append((child, child_under_joint))
    return kept, pruned


# ================================================================
# 경로
# ================================================================

def get_unique_filepath(filepath):
    """이미 있으면 _001, _002 ... 을 붙여 겹치지 않는 경로(슬래시 /)."""
    filepath = filepath.replace("\\", "/")
    if not os.path.exists(filepath):
        return filepath
    directory = os.path.dirname(filepath)
    name, ext = os.path.splitext(os.path.basename(filepath))
    index = 1
    while True:
        new_path = os.path.join(directory, "{0}_{1:03d}{2}".format(name, index, ext)).replace("\\", "/")
        if not os.path.exists(new_path):
            return new_path
        index += 1


# ================================================================
# FBXExport* 옵션 한시 변경
# ================================================================

_FBX_OPTIONS = {
    "include_children": "FBXExportIncludeChildren",
    "input_connections": "FBXExportInputConnections",
    "bake_complex_animation": "FBXExportBakeComplexAnimation",
    "in_ascii": "FBXExportInAscii",
}


class fbx_options(object):
    """with fbx_options(include_children=False): ... - None 인 항목은 손대지 않고, 나갈 때 원래 값으로 되돌린다.

    플러그인이 없거나 명령이 실패하면 조용히 넘어간다(그 경우 기존 동작 그대로 export 된다).
    """

    def __init__(self, include_children=None, input_connections=None, bake_complex_animation=None, in_ascii=None):
        self._wanted = {
            "include_children": include_children,
            "input_connections": input_connections,
            "bake_complex_animation": bake_complex_animation,
            "in_ascii": in_ascii,
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

    @staticmethod
    def _to_bool(value):
        """`-q` 결과 - IncludeChildren 은 int(1/0), BakeComplexAnimation 은 **문자열** 'true'/'false' 로 온다(2026-10-26 실측)."""
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "on", "yes")
        return bool(value)

    def __enter__(self):
        ensure_fbx_plugin()
        for key, value in self._wanted.items():
            if value is None:
                continue
            command = _FBX_OPTIONS[key]
            current = self._eval("{0} -q".format(command))
            if current is None:
                continue
            self._previous[key] = self._to_bool(current)
            self._eval("{0} -v {1}".format(command, "true" if value else "false"))
        return self

    def __exit__(self, *args):
        for key, value in self._previous.items():
            self._eval("{0} -v {1}".format(_FBX_OPTIONS[key], "true" if value else "false"))
        self._previous = {}
        return False


def export_selected(nodes, filepath, include_children=None, input_connections=None, bake_complex_animation=None):
    """nodes 를 선택해 FBX 로 내보낸다(export selected). 폴더가 없으면 만든다. 옵션은 fbx_options 로 한시 변경."""
    cmds = _cmds()
    folder = os.path.dirname(filepath)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    cmds.select(nodes)
    with fbx_options(include_children=include_children, input_connections=input_connections,
                     bake_complex_animation=bake_complex_animation):
        cmds.file(filepath.replace("\\", "/"), force=True, options="v=0;", typ="FBX export", pr=True, es=True)
    cmds.select(clear=True)
    return filepath
