# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - directory tree scanner (UI/DCC 비의존)
#
# 입력 경로 아래의 폴더/파일을 깊이 제한을 두고 훑어 트리 노드(dict) 구조로 돌려준다.
# Tree 탭의 데이터 소스. UI 는 이 구조를 받아 QTreeWidget 으로 그린다.
#
# 노드 구조:
#   {"name": <표시 이름>, "path": <절대경로>, "is_dir": bool,
#    "ext": <파일 확장자(점 없음, 소문자) / 폴더는 "">, "children": [<노드>...]}

import os


def build_tree(root_path, max_depth=0, include_files=True, extensions=None):
    """root_path 아래를 트리 노드(dict)로 만들어 root 노드를 반환한다.

    max_depth   : 표시할 깊이. 0(또는 음수)이면 무제한. 3이면 root 아래 3단계까지.
    include_files: False 면 폴더만 담는다.
    extensions  : None 이면 모든 파일. 아니면 점 없는 소문자 확장자 모음만 포함.
    """
    root_path = os.path.abspath(root_path)
    base = os.path.basename(root_path.rstrip("\\/")) or root_path
    root = {"name": base, "path": root_path, "is_dir": True, "ext": "", "children": []}

    if os.path.isdir(root_path):
        _walk(root_path, root, 1, max_depth, include_files, _norm_exts(extensions))

    return root


def _norm_exts(extensions):
    if extensions is None:
        return None
    return {e.lower().lstrip(".") for e in extensions}


def _walk(dir_path, parent, depth, max_depth, include_files, exts):
    """dir_path 내용을 parent["children"] 에 채운다(폴더 먼저, 그다음 파일; 이름순)."""
    if max_depth and depth > max_depth:
        return
    try:
        entries = list(os.scandir(dir_path))
    except OSError:
        return

    dirs = sorted((e for e in entries if e.is_dir()), key=lambda e: e.name.lower())
    files = sorted((e for e in entries if e.is_file()), key=lambda e: e.name.lower())

    for d in dirs:
        child = {"name": d.name, "path": d.path, "is_dir": True, "ext": "",
                 "children": []}
        parent["children"].append(child)
        _walk(d.path, child, depth + 1, max_depth, include_files, exts)

    if include_files:
        for f in files:
            ext = os.path.splitext(f.name)[1].lower().lstrip(".")
            if exts is not None and ext not in exts:
                continue
            parent["children"].append(
                {"name": f.name, "path": f.path, "is_dir": False, "ext": ext,
                 "children": []})


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
