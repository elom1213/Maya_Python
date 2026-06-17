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
    recursive: bool = False    # 캡처된 깊이(중첩 트리 여부)
    folders: list = field(default_factory=list)   # base_rel 기준 하위 폴더 상대경로(POSIX) 목록
    created_by: str = ""
    created_at: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return PathStructure(
            name=data.get("name", ""),
            base_rel=data.get("base_rel", ""),
            recursive=bool(data.get("recursive", False)),
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

def _collect_folders(base_abs, recursive):
    """base_abs 아래의 하위 폴더 상대경로(POSIX) 목록. 디렉터리만, 파일 무시."""
    if not os.path.isdir(base_abs):
        return []

    if not recursive:
        return sorted(
            name
            for name in os.listdir(base_abs)
            if os.path.isdir(os.path.join(base_abs, name))
        )

    out = []
    for root, dirs, _files in os.walk(base_abs):
        for d in dirs:
            rel = os.path.relpath(os.path.join(root, d), base_abs)
            out.append(rel.replace("\\", "/"))
    return sorted(out)


def capture(base_abs, store, recursive):
    """베이스 폴더의 하위 구조를 PathStructure 로 캡처.

    store : MetaStore (project_root 보유). base 가 루트 밖이면 OutsideProjectRootError.
    name / created_* 는 호출자가 채운다.
    """
    base_rel = store.make_key(base_abs)   # project_root 상대 POSIX 키 (밖이면 예외)
    folders = _collect_folders(base_abs, recursive)
    return PathStructure(base_rel=base_rel, recursive=recursive, folders=folders)


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


def recreate(structure, project_root):
    """structure 의 폴더들을 로컬 project_root 아래에 생성한다.

    폴더만 생성(os.makedirs, exist_ok). 파일은 만들지 않는다.
    반환: (created, existing) — 둘 다 절대경로 목록.
    """
    if not project_root:
        raise ValueError("Project root is not set")

    base_abs = os.path.join(
        os.path.abspath(project_root),
        *structure.base_rel.split("/"),
    )

    targets = [base_abs] + [
        os.path.join(base_abs, *folder.split("/"))
        for folder in structure.folders
    ]

    created, existing = [], []
    for path in targets:
        if os.path.isdir(path):
            existing.append(path)
        else:
            os.makedirs(path, exist_ok=True)
            created.append(path)

    return created, existing
