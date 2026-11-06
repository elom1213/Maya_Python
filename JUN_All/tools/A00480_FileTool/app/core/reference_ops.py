# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-06
# A00480_FileTool - Reference 탭 로직 (maya.cmds, UI 비의존)
"""
reference_ops - 현재 씬의 레퍼런스(중첩 포함)를 모으고, 파일을 탐색기로 열고, 경로 문자열을 만든다.

mayapy 2024 실측 (2026-10-26):
- 레퍼런스 노드는 `ls(type="reference")` 에 **중첩까지 전부** 나온다(`MID_A:LEAFRN` 처럼 부모 네임스페이스가 붙는다).
  `sharedReferenceNode` · `_UNKNOWN_REF_NODE_` 는 파일이 없는 내부 노드라 뺀다.
- 부모는 `referenceQuery(rn, referenceNode=True, parent=True)` - 최상위면 None. 자식은 `child=True`.
- **부모가 언로드면 그 안의 중첩 레퍼런스 노드는 씬에 없다**(로드돼야 생긴다) → 그 행은 `nested_hidden=True` 로 표시만.
- 같은 파일을 두 번 레퍼런스하면 `filename` 에 `{1}` 같은 복사 번호가 붙는다 → `withoutCopyNumber=True` 로 실제 경로를 읽고
  복사 번호는 따로 둔다. `unresolvedName=True` 는 씬에 적힌 그대로(환경 변수 · 상대 경로).
- 파일이 디스크에 없어도 노드는 있고 `isLoaded` 는 False → `exists` 로 구분한다(Missing).
- 최상위 순서는 Reference Editor 와 같게 `file(q=True, reference=True)` 순, 자식은 이름 순.

전부 **로그 문자열 리스트**를 함께 돌려주고, 클립보드 · 메시지 박스는 UI 몫이다.
"""

import os

from Framework.core.file_opener import open_path

# 파일이 없는 마야 내부 레퍼런스 노드
SKIP_NODES = ("sharedReferenceNode", "_UNKNOWN_REF_NODE_")

STATUS_LOADED = "Loaded"
STATUS_UNLOADED = "Unloaded"
STATUS_MISSING = "Missing"


def _cmds():
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


def norm_key(path):
    """대소문자 · 슬래시 차이를 무시한 경로 키(중복 제거용)."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path))) if path else ""


# ==========================================================================
# Scene references
# ==========================================================================

def _query(cmds, node, **kwargs):
    try:
        return cmds.referenceQuery(node, **kwargs)
    except Exception:
        return None


def _row(cmds, node, parent, depth):
    path = _query(cmds, node, filename=True, withoutCopyNumber=True) or ""
    full = _query(cmds, node, filename=True) or path
    stored = _query(cmds, node, filename=True, unresolvedName=True, withoutCopyNumber=True) or path
    namespace = (_query(cmds, node, namespace=True) or "").lstrip(":")
    loaded = bool(_query(cmds, node, isLoaded=True))
    copy = full[len(path):] if full.startswith(path) and len(full) > len(path) else ""
    exists = bool(path) and os.path.isfile(path)
    if not exists:
        status = STATUS_MISSING
    elif loaded:
        status = STATUS_LOADED
    else:
        status = STATUS_UNLOADED
    return {
        "node": node,
        "parent": parent,
        "depth": depth,
        "namespace": namespace or node,
        "path": path.replace("\\", "/"),
        "stored": stored.replace("\\", "/"),
        "copy": copy,
        "loaded": loaded,
        "exists": exists,
        "status": status,
        # 언로드 상태라 그 안의 중첩 레퍼런스를 씬이 모른다
        "nested_hidden": (not loaded) and exists,
    }


def scene_references():
    """현재 씬의 레퍼런스 전부를 **트리 순서(깊이 우선)** 의 평평한 행 목록으로. 반환 (rows, logs).

    row = {node, parent(부모 레퍼런스 노드 또는 None), depth(0 = 최상위), namespace, path(실제 경로, `/`),
           stored(씬에 적힌 경로), copy(`{1}` 같은 복사 번호 또는 ""), loaded, exists, status, nested_hidden}
    """
    cmds = _cmds()
    if cmds is None:
        return [], ["[WARN] maya.cmds is not available - no scene to read."]

    nodes = [n for n in (cmds.ls(type="reference") or []) if n not in SKIP_NODES]
    # 파일이 없는 노드(깨진 내부 노드)는 뺀다
    nodes = [n for n in nodes if _query(cmds, n, filename=True)]

    parents = {n: _query(cmds, n, referenceNode=True, parent=True) for n in nodes}
    children = {}
    for node in nodes:
        children.setdefault(parents.get(node), []).append(node)

    # 최상위 순서 = Reference Editor 순(file -q -reference). 거기 없는 것은 이름 순으로 뒤에.
    top = []
    for ref_file in (cmds.file(q=True, reference=True) or []):
        node = _query(cmds, ref_file, referenceNode=True)
        if node in nodes and node not in top:
            top.append(node)
    for node in sorted(children.get(None, [])):
        if node not in top:
            top.append(node)

    rows = []

    def walk(node, parent, depth):
        rows.append(_row(cmds, node, parent, depth))
        for child in sorted(children.get(node, [])):
            walk(child, node, depth + 1)

    for node in top:
        walk(node, None, 0)

    return rows, [summary(rows)]


def summary(rows):
    """로그 한 줄: `References : 6 (nested 2, unloaded 1, missing 1)` / 없으면 안내."""
    if not rows:
        return "[Info] No references in the current scene."
    nested = sum(1 for r in rows if r["depth"] > 0)
    unloaded = sum(1 for r in rows if r["status"] == STATUS_UNLOADED)
    missing = sum(1 for r in rows if r["status"] == STATUS_MISSING)
    parts = ["nested {0}".format(nested)]
    if unloaded:
        parts.append("unloaded {0}".format(unloaded))
    if missing:
        parts.append("missing {0}".format(missing))
    return "References : {0} ({1})".format(len(rows), ", ".join(parts))


# ==========================================================================
# Open / copy
# ==========================================================================

# File 열 / Lineage 노드 보기 모드 (v01.16, v01.18 기본 = 파일 이름) - 전체 경로 / 파일 이름만.
# Default 와 Lineage 두 하위 탭이 **같은** 마야 optionVar 를 쓴다 - 한쪽에서 바꾸면 다른 쪽도 다음에 열 때 따라간다.
FILE_VIEW_PATH = "path"
FILE_VIEW_NAME = "name"
FILE_VIEWS = (FILE_VIEW_PATH, FILE_VIEW_NAME)
FILE_VIEW_DEFAULT = FILE_VIEW_NAME
FILE_VIEW_CHOICES = (("Full Path", FILE_VIEW_PATH), ("File Name", FILE_VIEW_NAME))   # `Show` 콤보 항목 (라벨, 모드)
FILE_VIEW_OPTION = "JUN_A00480_FileTool_reference_file_view"


def file_text(path, view=FILE_VIEW_PATH):
    """File 열에 보일 글자. `path` 모드는 윈도우 모양 전체 경로, `name` 모드는 파일 이름만."""
    if not path:
        return ""
    if view == FILE_VIEW_NAME:
        return os.path.basename(os.path.normpath(path))
    return os.path.normpath(path)


def load_file_view():
    """기억해 둔 보기 모드. 없거나 마야 밖이면 기본(파일 이름)."""
    cmds = _cmds()
    if cmds is None:
        return FILE_VIEW_DEFAULT
    try:
        if cmds.optionVar(exists=FILE_VIEW_OPTION):
            value = cmds.optionVar(q=FILE_VIEW_OPTION)
            if value in FILE_VIEWS:
                return value
    except Exception:                                      # noqa: BLE001
        pass
    return FILE_VIEW_DEFAULT


def save_file_view(view):
    """보기 모드를 마야 optionVar 에 기억한다(마야 밖이면 아무것도 안 한다)."""
    cmds = _cmds()
    if cmds is None or view not in FILE_VIEWS:
        return False
    try:
        cmds.optionVar(sv=(FILE_VIEW_OPTION, view))
        return True
    except Exception:                                      # noqa: BLE001
        return False


def unique_paths(paths):
    """순서를 지키며 같은 파일(대소문자 · 슬래시 무시)을 하나로."""
    seen = set()
    out = []
    for path in paths or []:
        key = norm_key(path)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def open_reference_files(paths, opener=None):
    """레퍼런스 파일들을 탐색기로 연다(파일마다 폴더를 열고 그 파일을 선택). 반환: 로그 리스트.

    같은 파일은 한 번만 연다. 디스크에 없는 파일은 그 **폴더**가 있으면 폴더를 열고, 없으면 경고만.
    """
    logs = []
    targets = unique_paths(paths)
    if not targets:
        return ["[WARN] No reference selected."]
    if opener is None:
        opener = open_path          # 호출 시점에 잡는다(시험에서 바꿔 끼울 수 있게)

    for path in targets:
        native = os.path.normpath(path)
        if os.path.isfile(native):
            target = native
        elif os.path.isdir(os.path.dirname(native)):
            target = os.path.dirname(native)
            logs.append("[WARN] File is missing - opening its folder instead : {0}".format(native))
        else:
            logs.append("[WARN] Path does not exist on disk : {0}".format(native))
            continue
        try:
            opener(target)
            logs.append("Opened in File Explorer : {0}".format(native))
        except Exception as exc:
            logs.append("[WARN] Could not open : {0} ({1})".format(native, exc))
    return logs


def clipboard_text(paths):
    """복사할 문자열 - 파일마다 한 줄, OS 네이티브 모양(윈도우는 `\\`). 반환 (text, logs). 비었으면 ("", 경고)."""
    targets = unique_paths(paths)
    if not targets:
        return "", ["[WARN] No reference selected."]
    lines = [os.path.normpath(p) for p in targets]
    return "\n".join(lines), ["Copied to clipboard : {0}".format(
        lines[0] if len(lines) == 1 else "{0} paths".format(len(lines)))]


# ==========================================================================
# Replace (v01.21)
# ==========================================================================
# mayapy 2024 실측 (2026-11-06):
# - `file(new, loadReference=rn)` = Reference Editor 의 Replace Reference. 네임스페이스 · 노드 이름 · 씬 쪽 연결
#   (컨스트레인트 · 애니 커브)은 그대로 남는다(같은 이름의 노드가 새 파일에 있으면 다시 붙는다).
# - 언로드 레퍼런스도 그냥 부르면 **로드돼 버린다** → `loadReferenceDepth="none"` 이면 파일만 바뀌고 언로드 그대로.
# - **중첩 레퍼런스**(다른 레퍼런스 안의 것)도 바뀌지만 마야 경고대로 **임시**다 - 씬을 저장해도 남지 않는다
#   (다시 열면 원래 파일). 영구히 바꾸려면 부모 파일을 열고 거기서 바꿔야 한다 → 막지 않고 로그로 알린다.
# - 같은 파일을 이미 다른 레퍼런스가 쓰면 마야가 `{1}` 복사 번호를 붙인다(정상).
# - **undo 안 된다**(undoInfo 에 남지 않는다) → UI 가 실행 전에 확인을 받는다.

REPLACE_EXTENSIONS = (".ma", ".mb")
REPLACE_FILTER = "Maya Files (*.ma *.mb);;All Files (*)"


def _is_nested(cmds, node):
    return bool(_query(cmds, node, referenceNode=True, parent=True))


def replace_plan(nodes):
    """교체할 노드를 정리한다. 반환 (targets, skipped_logs).

    - 씬에 없는 노드 · 레퍼런스가 아닌 노드는 뺀다.
    - 부모와 그 안의 중첩 레퍼런스를 같이 고르면 **부모만** 바꾼다(부모를 바꾸면 중첩 노드는 새 파일 것으로 다시 생긴다).
    """
    cmds = _cmds()
    if cmds is None:
        return [], ["[WARN] maya.cmds is not available - no scene to change."]
    picked = []
    for node in nodes or []:
        if node and node not in picked:
            picked.append(node)
    logs = []
    valid = []
    for node in picked:
        if not cmds.objExists(node) or cmds.nodeType(node) != "reference":
            logs.append("[WARN] Not a reference node in the scene - skipped : {0}".format(node))
            continue
        valid.append(node)
    targets = []
    for node in valid:
        parent = _query(cmds, node, referenceNode=True, parent=True)
        covered = False
        while parent:
            if parent in valid:
                covered = True
                break
            parent = _query(cmds, parent, referenceNode=True, parent=True)
        if covered:
            logs.append("[Info] {0} is inside another selected reference - replacing the parent only.".format(node))
        else:
            targets.append(node)
    return targets, logs


def nested_targets(nodes):
    """그중 중첩 레퍼런스(바꿔도 저장되지 않는 것) 노드 목록 - 확인 창 문구용."""
    cmds = _cmds()
    if cmds is None:
        return []
    return [n for n in nodes or [] if cmds.objExists(n) and _is_nested(cmds, n)]


def replace_references(nodes, new_path):
    """고른 레퍼런스 노드들을 `new_path` 파일로 바꾼다(Reference Editor 의 Replace Reference). 반환 (count, logs).

    로드 상태는 지킨다 - 로드돼 있던 것은 로드, 언로드였던 것은 언로드 그대로(Missing 이던 것은 로드해 본다).
    중첩 레퍼런스는 바뀌지만 저장되지 않는다는 경고를 남긴다. undo 는 안 된다(호출 전에 확인 받을 것).
    """
    cmds = _cmds()
    if cmds is None:
        return 0, ["[WARN] maya.cmds is not available - no scene to change."]
    path = (new_path or "").replace("\\", "/")
    if not path:
        return 0, ["[WARN] No replacement file chosen."]
    if not os.path.isfile(path):
        return 0, ["[WARN] File does not exist : {0}".format(os.path.normpath(path))]
    if os.path.splitext(path)[1].lower() not in REPLACE_EXTENSIONS:
        return 0, ["[WARN] Not a Maya file (.ma / .mb) : {0}".format(os.path.normpath(path))]

    targets, logs = replace_plan(nodes)
    if not targets:
        return 0, logs or ["[WARN] No reference selected."]

    count = 0
    nested = 0
    for node in targets:
        old = _query(cmds, node, filename=True, withoutCopyNumber=True) or ""
        if old and norm_key(old) == norm_key(path):
            logs.append("[Info] Already uses that file - skipped : {0}".format(node))
            continue
        was_nested = _is_nested(cmds, node)
        loaded = bool(_query(cmds, node, isLoaded=True))
        keep_unloaded = (not loaded) and bool(old) and os.path.isfile(old)
        try:
            if keep_unloaded:
                cmds.file(path, loadReference=node, loadReferenceDepth="none")
            else:
                cmds.file(path, loadReference=node)
        except Exception as exc:                            # noqa: BLE001
            logs.append("[ERROR] Could not replace {0} : {1}".format(node, exc))
            continue
        count += 1
        line = "Replaced {0} : {1} -> {2}".format(
            node, os.path.basename(old) or "(none)", os.path.basename(path))
        if keep_unloaded:
            line += " (kept unloaded)"
        logs.append(line)
        if was_nested:
            nested += 1
    if nested:
        logs.append("[WARN] {0} nested reference(s) replaced - this is temporary and is NOT saved with the scene. "
                    "Open the parent file and replace it there to make it permanent.".format(nested))
    logs.append("Replace done : {0} reference(s) -> {1}".format(count, os.path.normpath(path)))
    return count, logs
