# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - path structure templates (UI/DCC 비의존)
#
# 어떤 베이스 폴더의 하위 폴더 구조를 JSON 으로 저장하고, 다른 PC 에서 그 구조를
# 재생성한다. 베이스 경로는 project_root 기준 상대경로로 저장하므로(키 방식과 동일)
# 절대경로가 PC 마다 달라도 동작한다. 폴더만 생성하고 파일은 만들지 않는다.
#
#   <store_dir>/path_structures/<name>.json
#
# 이 JSON 은 store_dir 안에 있으므로 git_sync 의 push/pull(`git add -A`)로 자동 동기화된다.

import os
import json

from dataclasses import dataclass, field, asdict

from .store import MetaStore, OutsideProjectRootError


STRUCTS_DIR = "path_structures"

# Windows 파일명에 못 쓰는 문자.
_ILLEGAL = '\\/:*?"<>|'


@dataclass
class PathStructure:
    """저장된 폴더 구조 템플릿 1개."""

    name: str = ""             # 표시 이름(파일명 생성의 원본)
    base_rel: str = ""         # project_root 기준 베이스 폴더 상대경로 (POSIX)
    recursive: bool = False    # 캡처된 깊이(중첩 트리 여부) — 하위호환용(max_depth 로 대체)
    max_depth: int = 0         # 캡처 깊이(base 기준, top=1). 0 = 무제한(전체 트리)
    folders: list = field(default_factory=list)   # base_rel 기준 하위 폴더 상대경로(POSIX) 목록
    created_by: str = ""
    created_at: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        recursive = bool(data.get("recursive", False))
        max_depth = data.get("max_depth")
        if max_depth is None:
            # 구버전 JSON(max_depth 없음): recursive True → 전체(0), False → 최상위만(1).
            max_depth = 0 if recursive else 1
        return PathStructure(
            name=data.get("name", ""),
            base_rel=data.get("base_rel", ""),
            recursive=recursive,
            max_depth=int(max_depth),
            folders=list(data.get("folders", [])),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", ""),
        )


# --------------------------------------------------------------- name / path

def _sanitize_name(name):
    """표시 이름을 파일명으로 안전하게 변환. (JSON 안의 name 은 원문 유지)"""
    cleaned = "".join("_" if c in _ILLEGAL else c for c in (name or "").strip())
    cleaned = "_".join(cleaned.split())          # 공백 런 → 단일 _
    cleaned = cleaned.strip("_.")
    return cleaned or "structure"


def structures_dir(store_dir):
    return os.path.join(store_dir, STRUCTS_DIR)


def struct_path(store_dir, name):
    return os.path.join(structures_dir(store_dir), _sanitize_name(name)) + ".json"


# ------------------------------------------------------------------- capture

def list_top_level(base_abs):
    """base_abs 의 최상위 하위 폴더 이름 목록(정렬). 디렉터리만, 파일 무시.

    UI 의 '기록할 폴더' 체크리스트를 채우는 데 쓴다.
    """
    if not os.path.isdir(base_abs):
        return []
    return sorted(
        name
        for name in os.listdir(base_abs)
        if os.path.isdir(os.path.join(base_abs, name))
    )


def _collect_folders(base_abs, max_depth, include_top=None):
    """base_abs 아래의 하위 폴더 상대경로(POSIX) 목록. 디렉터리만, 파일 무시.

    max_depth : 캡처할 깊이(base 기준, 최상위 폴더 = 1). 0(또는 음수)이면 무제한.
                1 이면 최상위 폴더만.
    include_top : 기록할 최상위 폴더 이름의 컬렉션. None 이면 전체 최상위 폴더를 대상으로
    한다(하위호환). 주어지면 그 최상위 폴더(및 그 하위 트리)만 수집한다.
    """
    if not os.path.isdir(base_abs):
        return []

    tops = list_top_level(base_abs)
    if include_top is not None:
        allow = set(include_top)
        tops = [t for t in tops if t in allow]

    out = []
    for top in tops:
        out.append(top)   # 최상위 폴더 자신 (depth 1)
        if max_depth == 1:
            continue
        top_abs = os.path.join(base_abs, top)
        for root, dirs, _files in os.walk(top_abs):
            rel_root = os.path.relpath(root, base_abs).replace("\\", "/")
            root_depth = rel_root.count("/") + 1   # top_abs → "top" → depth 1
            if max_depth and root_depth >= max_depth:
                dirs[:] = []          # 더 깊이 내려가지 않음
                continue
            for d in dirs:
                out.append(rel_root + "/" + d)
    return sorted(out)


def limit_depth(folders, max_depth):
    """폴더 상대경로 목록에서 base 기준 깊이가 max_depth 이하인 것만 반환.

    max_depth : 최상위 폴더 = 1. 0(또는 음수)이면 제한 없음(원본 그대로).
    """
    if not max_depth or max_depth < 0:
        return list(folders)
    return [f for f in folders if f.count("/") + 1 <= max_depth]


def capture(base_abs, store, max_depth, include_top=None):
    """베이스 폴더의 하위 구조를 PathStructure 로 캡처.

    store : MetaStore (project_root 보유). base 가 루트 밖이면 OutsideProjectRootError.
    max_depth : 캡처 깊이(최상위=1, 0=무제한).
    include_top : 기록할 최상위 폴더 이름의 컬렉션(체크된 것만). None 이면 전체(하위호환).
    name / created_* 는 호출자가 채운다.
    """
    base_rel = store.make_key(base_abs)   # project_root 상대 POSIX 키 (밖이면 예외)
    folders = _collect_folders(base_abs, max_depth, include_top)
    return PathStructure(
        base_rel=base_rel,
        recursive=(max_depth != 1),
        max_depth=max_depth,
        folders=folders,
    )


# --------------------------------------------------------------- save / load

def save(store_dir, structure):
    """PathStructure 를 JSON 으로 저장하고 경로 반환."""
    path = struct_path(store_dir, structure.name)
    MetaStore._ensure_parent(path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(structure.to_dict(), f, ensure_ascii=False, indent=2)

    return path


def list_names(store_dir):
    """저장된 구조의 표시 이름 목록(대소문자 무시 정렬). 없으면 []."""
    dir_path = structures_dir(store_dir)
    if not store_dir or not os.path.isdir(dir_path):
        return []

    names = []
    for fname in os.listdir(dir_path):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(dir_path, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            names.append(data.get("name") or fname[:-5])
        except (OSError, ValueError):
            names.append(fname[:-5])

    return sorted(names, key=str.lower)


def load(store_dir, name):
    """이름으로 PathStructure 로드. 없으면 None."""
    path = struct_path(store_dir, name)
    if not os.path.isfile(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PathStructure.from_dict(data)


def exists(store_dir, name):
    return os.path.isfile(struct_path(store_dir, name))


def delete(store_dir, name):
    path = struct_path(store_dir, name)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


# ----------------------------------------------------------------- recreate

def build_tree_lines(folders):
    """폴더 상대경로 목록(POSIX)을 트리뷰 문자열 줄 목록으로 변환.

    예: ["A", "A/b", "A/c", "B"] ->
        A
        ├── b
        └── c
        (빈 줄)
        B
    상위(top-level) 폴더는 빈 줄로 구분하고 커넥터 없이 출력한다.
    """
    tree = {}
    for path in folders:
        node = tree
        for part in path.split("/"):
            if not part:
                continue
            node = node.setdefault(part, {})

    lines = []

    def render(children, prefix):
        keys = list(children.keys())
        for i, key in enumerate(keys):
            last = i == len(keys) - 1
            lines.append(prefix + ("└── " if last else "├── ") + key)
            render(children[key], prefix + ("    " if last else "│   "))

    for idx, key in enumerate(tree.keys()):
        if idx > 0:
            lines.append("")           # 상위 항목 사이 빈 줄
        lines.append(key)
        render(tree[key], "")

    return lines


def build_structure_tree(structure, base_abs=None, show_files=False, max_depth=0):
    """structure.folders 를 트리 노드(dict)로 변환. Preview 트리뷰의 데이터 소스.

    노드: {"name", "rel"(base 기준 POSIX, 루트=""), "path"(절대경로 또는 ""),
           "is_dir", "children"}
    max_depth : 표시할 폴더 깊이(최상위=1, 0=무제한).
    show_files: True 이고 base_abs 가 실재하면 각 폴더의 실제 파일도 자식으로 채운다
                (구조 JSON 은 폴더만 담으므로 파일은 파일시스템에서 읽는다).
    """
    root_name = os.path.basename(structure.base_rel.rstrip("/")) or (
        structure.base_rel or "(base)")
    root = {"name": root_name, "rel": "", "path": base_abs or "",
            "is_dir": True, "children": []}

    nodes = {"": root}
    for folder in sorted(structure.folders):
        parts = [p for p in folder.split("/") if p]
        parent = root
        cur_rel = ""
        for i, part in enumerate(parts):
            if max_depth and (i + 1) > max_depth:
                break
            child_rel = part if not cur_rel else cur_rel + "/" + part
            node = nodes.get(child_rel)
            if node is None:
                node = {
                    "name": part,
                    "rel": child_rel,
                    "path": (os.path.join(base_abs, *child_rel.split("/"))
                             if base_abs else ""),
                    "is_dir": True,
                    "children": [],
                }
                nodes[child_rel] = node
                parent["children"].append(node)
            parent = node
            cur_rel = child_rel

    if show_files and base_abs and os.path.isdir(base_abs):
        _add_files(root)

    return root


def _add_files(node):
    """node(폴더) 이하의 각 폴더에 실제 파일을 자식으로 추가(폴더 먼저 처리 후 파일 append)."""
    for child in list(node["children"]):
        if child["is_dir"]:
            _add_files(child)

    dir_path = node["path"]
    if not dir_path or not os.path.isdir(dir_path):
        return
    try:
        entries = sorted(os.scandir(dir_path), key=lambda e: e.name.lower())
    except OSError:
        return
    for e in entries:
        if e.is_file():
            rel = (node["rel"] + "/" + e.name) if node["rel"] else e.name
            node["children"].append({
                "name": e.name, "rel": rel, "path": e.path,
                "is_dir": False, "children": [],
            })


def recreate(structure, project_root, folders=None):
    """structure 의 폴더들을 로컬 project_root 아래에 생성한다.

    폴더만 생성(os.makedirs, exist_ok). 파일은 만들지 않는다.
    folders : 생성할 폴더 상대경로(POSIX) 목록. None 이면 structure.folders 전체(하위호환).
              지정하면 그 폴더들만 생성한다(깊이/포함 여부는 호출자가 이미 걸러 전달).
    반환: (created, existing) — 둘 다 절대경로 목록.
    """
    if not project_root:
        raise ValueError("Project root is not set")

    selected = structure.folders if folders is None else folders

    base_abs = os.path.join(
        os.path.abspath(project_root),
        *structure.base_rel.split("/"),
    )

    targets = [base_abs] + [
        os.path.join(base_abs, *folder.split("/"))
        for folder in selected
    ]

    created, existing = [], []
    seen = set()
    for path in targets:
        if path in seen:
            continue
        seen.add(path)
        if os.path.isdir(path):
            existing.append(path)
        else:
            os.makedirs(path, exist_ok=True)
            created.append(path)

    return created, existing
