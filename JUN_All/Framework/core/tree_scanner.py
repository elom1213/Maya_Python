# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# Framework - directory tree scanner (UI/DCC 비의존)
#
# A00240_PathTool 의 core/tree_scanner.py 를 Framework 로 승격 (2026-10-12, A00240 v01.20).
# A00480_FileTool 의 Maya 탭도 같은 트리를 쓰므로 한 벌만 둔다. A00240 쪽 파일은 re-export 만 남았다.
# 아래 v01.NN 표기는 A00240_PathTool 버전 이력이다.
#
# 입력 경로 아래의 폴더/파일을 깊이 제한을 두고 훑어 트리 노드(dict) 구조로 돌려준다.
# Tree 탭의 데이터 소스. UI 는 이 구조를 받아 QTreeWidget 으로 그린다.
#
# 노드 구조:
#   {"name": <표시 이름>, "path": <절대경로>, "is_dir": bool,
#    "ext": <파일 확장자(점 없음, 소문자) / 폴더는 "">, "children": [<노드>...],
#    "loaded": <폴더만 - 그 폴더 안을 디스크에서 읽었는가>,
#    "junction": <폴더만 - 디렉터리 정션인가 (v01.19)>, "target": <정션이 가리키는 경로>}
#
# v01.19 : 정션은 scandir 의 stat(follow_symlinks=False) 리파스 태그로 판별한다(추가 디스크 접근 없음).
#          Depth 탐색(_walk)은 **자기 조상을 가리키는 정션 안으로는 내려가지 않는다** - 안 그러면
#          A/link->A 같은 순환을 경로 길이 한계까지 끝없이 내려간다.
#
# v01.16 : **Adaptive(지연) 탐색** - build_tree_lazy() 는 루트 바로 아래 한 겹만 읽고,
#          나머지 폴더는 loaded=False 로 둔다. UI 가 폴더를 펼칠 때 scan_children() 으로
#          그 폴더 한 겹만 읽는다(펼친 곳만 디스크를 읽는다).

import os
import stat


def build_tree(root_path, max_depth=0, include_files=True, extensions=None):
    """root_path 아래를 트리 노드(dict)로 만들어 root 노드를 반환한다.

    max_depth   : 표시할 깊이. 0(또는 음수)이면 무제한. 3이면 root 아래 3단계까지.
    include_files: False 면 폴더만 담는다.
    extensions  : None 이면 모든 파일. 아니면 점 없는 소문자 확장자 모음만 포함.
    """
    root = _root_node(root_path)
    if os.path.isdir(root["path"]):
        _walk(root["path"], root, 1, max_depth, include_files, _norm_exts(extensions),
              os.path.realpath(root["path"]))
    return root


def build_tree_lazy(root_path):
    """Adaptive(지연) 탐색의 시작 - 루트 **바로 아래 한 겹만** 읽는다 (v01.16).

    하위 폴더는 children=[] · loaded=False 로 남는다. 펼칠 때 scan_children() 으로 채운다.
    """
    root = _root_node(root_path)
    root["children"] = scan_children(root["path"])
    root["loaded"] = True
    return root


def scan_children(dir_path):
    """dir_path **바로 아래 한 겹**의 노드 목록(폴더 먼저, 그다음 파일; 이름순) (v01.16).

    하위 폴더는 읽지 않는다(loaded=False). 읽을 수 없는 폴더(권한 등)는 빈 목록.
    os.scandir 의 DirEntry.is_dir / is_file 은 Windows 에서 추가 stat 없이 답한다.
    """
    try:
        entries = list(os.scandir(dir_path))
    except OSError:
        return []

    dirs = sorted((e for e in entries if _safe_is_dir(e)), key=lambda e: e.name.lower())
    files = sorted((e for e in entries if _safe_is_file(e)), key=lambda e: e.name.lower())

    out = [_dir_node(d) for d in dirs]
    for f in files:
        out.append({"name": f.name, "path": f.path, "is_dir": False,
                    "ext": os.path.splitext(f.name)[1].lower().lstrip("."), "children": []})
    return out


def _root_node(root_path):
    root_path = os.path.abspath(root_path)
    base = os.path.basename(root_path.rstrip(os.sep + "/")) or root_path
    node = {"name": base, "path": root_path, "is_dir": True, "ext": "", "children": [],
            "loaded": False}
    _mark_junction(node, _lstat(root_path))
    return node


def _dir_node(entry):
    """scandir 의 폴더 엔트리 -> 폴더 노드(loaded=False). 정션이면 표시와 타깃을 붙인다 (v01.19)."""
    node = {"name": entry.name, "path": entry.path, "is_dir": True, "ext": "", "children": [],
            "loaded": False}
    try:
        st = entry.stat(follow_symlinks=False)    # Windows 는 목록 데이터로 답한다(추가 stat 없음)
    except OSError:
        st = None
    _mark_junction(node, st)
    return node


def _lstat(path):
    try:
        return os.lstat(path)
    except OSError:
        return None


def _mark_junction(node, st):
    """리파스 태그가 IO_REPARSE_TAG_MOUNT_POINT 면 정션 - node 에 junction/target 을 적는다."""
    if st is None:
        return
    attrs = getattr(st, "st_file_attributes", 0)
    if not attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return
    if getattr(st, "st_reparse_tag", 0) != stat.IO_REPARSE_TAG_MOUNT_POINT:
        return
    node["junction"] = True
    try:
        target = os.readlink(node["path"])
    except OSError:
        target = ""
    if target.startswith("\\\\?\\"):
        target = target[4:]
    node["target"] = target


def _safe_is_dir(entry):
    try:
        return entry.is_dir()
    except OSError:
        return False


def _safe_is_file(entry):
    try:
        return entry.is_file()
    except OSError:
        return False


def _norm_exts(extensions):
    if extensions is None:
        return None
    return {e.lower().lstrip(".") for e in extensions}


def _walk(dir_path, parent, depth, max_depth, include_files, exts, real_dir):
    """dir_path 내용을 parent["children"] 에 채운다(폴더 먼저, 그다음 파일; 이름순).

    real_dir : dir_path 의 **실제** 위치 - 정션을 타고 내려왔으면 그 타깃 기준의 경로다
               (realpath 호출 없이 이름을 이어 붙여 만든다). 정션의 타깃이 real_dir 자신이거나
               그 조상이면 순환이므로 그 안으로는 내려가지 않는다(노드는 남긴다 - 화면에는 보인다).
    """
    if max_depth and depth > max_depth:
        return
    parent["loaded"] = True
    try:
        entries = list(os.scandir(dir_path))
    except OSError:
        return

    dirs = sorted((e for e in entries if e.is_dir()), key=lambda e: e.name.lower())
    files = sorted((e for e in entries if e.is_file()), key=lambda e: e.name.lower())

    for d in dirs:
        child = _dir_node(d)
        parent["children"].append(child)
        child_real = os.path.join(real_dir, d.name)
        if child.get("junction") and child.get("target"):
            if _same_or_inside(real_dir, child["target"]):
                child["loaded"] = True          # 순환 - 비어 있는 것으로 둔다
                continue
            child_real = child["target"]
        _walk(d.path, child, depth + 1, max_depth, include_files, exts, child_real)

    if include_files:
        for f in files:
            ext = os.path.splitext(f.name)[1].lower().lstrip(".")
            if exts is not None and ext not in exts:
                continue
            parent["children"].append(
                {"name": f.name, "path": f.path, "is_dir": False, "ext": ext,
                 "children": []})


def _same_or_inside(path, folder):
    """path 가 folder 자신이거나 그 안인가(대소문자 무시)."""
    p = os.path.normcase(os.path.normpath(path))
    f = os.path.normcase(os.path.normpath(folder))
    return p == f or p.startswith(f + os.sep)


def collect_extensions(node):
    """트리(node 이하)에서 발견된 파일 확장자(점 없음) 집합을 반환한다."""
    found = set()

    def rec(n):
        for c in n["children"]:
            if c["is_dir"]:
                rec(c)
            else:
                found.add(c.get("ext", ""))

    rec(node)
    return found
