# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
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
