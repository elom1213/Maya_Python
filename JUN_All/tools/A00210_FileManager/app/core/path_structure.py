# Python Script by Ji Hun Park
# last Update date : 2026-08-03
# A00210_FileManager - path structure templates (UI/DCC 비의존)
#
# 어떤 베이스 폴더의 하위 폴더 구조를 JSON 으로 저장하고, 다른 PC 에서 그 구조를
# 재생성한다. 베이스 경로는 project_root 기준 상대경로로 저장하므로(키 방식과 동일)
# 절대경로가 PC 마다 달라도 동작한다.
#
#   <store_dir>/path_structures/<name>.json
#
# 이 JSON 은 store_dir 안에 있으므로 git_sync 의 push/pull(`git add -A`)로 자동 동기화된다.
#
# v01.29 : 폴더뿐 아니라 **파일 목록도 캡처/재생성**할 수 있다(structure.files).
#          재생성되는 파일은 **0 바이트 빈 파일**이고 이름 끝에 RECREATED_SUFFIX("__")
#          가 붙는다(test.ma -> test.ma__). 원본과 생성물을 이름만 보고 구분하기 위한
#          표식이며, 실제 데이터를 담은 파일을 덮어쓸 일이 없게 해준다.

import os
import json

from dataclasses import dataclass, field, asdict

from .store import MetaStore, OutsideProjectRootError


STRUCTS_DIR = "path_structures"

# Windows 파일명에 못 쓰는 문자.
_ILLEGAL = '\\/:*?"<>|'

# 재생성한 빈 파일에 붙이는 표식. 확장자 뒤에 그대로 덧붙인다(test.ma -> test.ma__).
# 확장자를 바꾸지 않고 덧붙이는 이유: 원래 이름을 눈으로 그대로 읽을 수 있고,
# DCC/탐색기가 이 파일을 진짜 씬 파일로 오해해 열려고 하지 않는다.
RECREATED_SUFFIX = "__"


def marked_name(name, suffix=RECREATED_SUFFIX):
    """재생성 파일 이름. 이미 표식이 붙어 있으면 덧붙이지 않는다(재캡처 후 재생성 시 `____` 방지)."""
    if not suffix or name.endswith(suffix):
        return name
    return name + suffix


@dataclass
class PathStructure:
    """저장된 폴더 구조 템플릿 1개."""

    name: str = ""             # 표시 이름(파일명 생성의 원본)
    base_rel: str = ""         # project_root 기준 베이스 폴더 상대경로 (POSIX)
    recursive: bool = False    # 캡처된 깊이(중첩 트리 여부) — 하위호환용(max_depth 로 대체)
    max_depth: int = 0         # 캡처 깊이(base 기준, top=1). 0 = 무제한(전체 트리)
    folders: list = field(default_factory=list)   # base_rel 기준 하위 폴더 상대경로(POSIX) 목록
    files: list = field(default_factory=list)     # base_rel 기준 파일 상대경로(POSIX) 목록
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
            # files 없는 구버전 JSON → 빈 목록(= 폴더만 재생성, 기존 동작 그대로).
            files=list(data.get("files", []) or []),
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


def _list_files(dir_abs):
    """dir_abs 바로 아래의 파일 이름 목록(정렬). 폴더 무시."""
    try:
        return sorted(
            (e.name for e in os.scandir(dir_abs) if e.is_file()),
            key=str.lower,
        )
    except OSError:
        return []


def _collect_files(base_abs, max_depth, include_top=None):
    """base_abs 아래의 파일 상대경로(POSIX) 목록. 파일만, 폴더 무시.

    깊이 규칙은 폴더와 같다 — base 바로 아래 파일이 depth 1, `top/a.ma` 는 depth 2.
    따라서 max_depth=1 이면 **base 바로 아래 파일만** 기록된다.

    include_top : 기록할 최상위 폴더 이름의 컬렉션(폴더 캡처와 같은 필터). None 이면 전체.
                  **base 바로 아래 파일은 어느 최상위 폴더에도 속하지 않으므로 이 필터와
                  무관하게 항상 포함**된다(base 폴더 자체의 내용물이라서).
    """
    if not os.path.isdir(base_abs):
        return []

    out = list(_list_files(base_abs))                # depth 1 : base 바로 아래

    if max_depth == 1:
        return sorted(out)

    tops = list_top_level(base_abs)
    if include_top is not None:
        allow = set(include_top)
        tops = [t for t in tops if t in allow]

    for top in tops:
        for root, dirs, files in os.walk(os.path.join(base_abs, top)):
            rel_root = os.path.relpath(root, base_abs).replace("\\", "/")
            root_depth = rel_root.count("/") + 1     # "top" → 1
            for name in files:
                if not max_depth or root_depth + 1 <= max_depth:
                    out.append(rel_root + "/" + name)
            if max_depth and root_depth + 1 >= max_depth:
                dirs[:] = []                          # 더 내려가도 깊이 초과
    return sorted(out)


def limit_depth(folders, max_depth):
    """폴더/파일 상대경로 목록에서 base 기준 깊이가 max_depth 이하인 것만 반환.

    max_depth : 최상위 폴더 = 1. 0(또는 음수)이면 제한 없음(원본 그대로).
    """
    if not max_depth or max_depth < 0:
        return list(folders)
    return [f for f in folders if f.count("/") + 1 <= max_depth]


def capture(base_abs, store, max_depth, include_top=None, include_files=False):
    """베이스 폴더의 하위 구조를 PathStructure 로 캡처.

    store : MetaStore (project_root 보유). base 가 루트 밖이면 OutsideProjectRootError.
    max_depth : 캡처 깊이(최상위=1, 0=무제한).
    include_top : 기록할 최상위 폴더 이름의 컬렉션(체크된 것만). None 이면 전체(하위호환).
    include_files : True 면 파일 목록도 함께 기록한다(내용은 기록하지 않는다 — 이름뿐).
    name / created_* 는 호출자가 채운다.
    """
    base_rel = store.make_key(base_abs)   # project_root 상대 POSIX 키 (밖이면 예외)
    folders = _collect_folders(base_abs, max_depth, include_top)
    files = _collect_files(base_abs, max_depth, include_top) if include_files else []
    return PathStructure(
        base_rel=base_rel,
        recursive=(max_depth != 1),
        max_depth=max_depth,
        folders=folders,
        files=files,
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


def rename(store_dir, old_name, new_name):
    """저장된 구조의 표시 이름(및 JSON 파일명)을 바꾼다.

    JSON 안의 name 필드도 새 이름으로 갱신한다. 두 이름이 서로 다른 파일로
    정규화되는데 새 파일이 이미 있으면 ValueError(덮어쓰기 방지). 표시 이름만 달라
    같은 파일로 정규화되면 name 필드만 갱신한다.
    반환: 새 JSON 파일 경로.
    """
    old_path = struct_path(store_dir, old_name)
    if not os.path.isfile(old_path):
        raise ValueError("Structure not found")

    new_path = struct_path(store_dir, new_name)
    same_file = (os.path.normcase(os.path.abspath(new_path))
                 == os.path.normcase(os.path.abspath(old_path)))
    if not same_file and os.path.isfile(new_path):
        raise ValueError("A structure with that name already exists")

    with open(old_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["name"] = new_name

    MetaStore._ensure_parent(new_path)
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if not same_file:
        os.remove(old_path)

    return new_path


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
    """structure 를 트리 노드(dict)로 변환. Preview 트리뷰의 데이터 소스.

    노드: {"name", "rel"(base 기준 POSIX, 루트=""), "path"(절대경로 또는 ""),
           "is_dir", "recorded", "children"}

    `recorded` — 이 항목이 **구조에 기록되어 Recreate 대상**인지. 폴더는 항상 True,
    파일은 structure.files 에서 온 것만 True 다. 기록된 파일이 없는 구조(구버전 JSON,
    또는 파일 없이 캡처)에서는 디스크의 실제 파일을 **보여주기만** 하므로 False 이고,
    UI 는 이 값으로 체크박스를 줄지(=제외 가능한지) 정한다.

    max_depth : 표시할 깊이(최상위=1, 0=무제한). 파일도 같은 규칙으로 잘린다.
    show_files: 파일을 트리에 넣을지. structure.files 가 있으면 그것을,
                없으면 base_abs 의 실제 파일을(표시 전용) 채운다.
    """
    root_name = os.path.basename(structure.base_rel.rstrip("/")) or (
        structure.base_rel or "(base)")
    root = {"name": root_name, "rel": "", "path": base_abs or "",
            "is_dir": True, "recorded": True, "children": []}

    nodes = {"": root}

    def ensure_dir(rel):
        """rel(POSIX) 폴더 노드를 만들어(필요하면 조상까지) 반환. 깊이 초과면 None."""
        if not rel:
            return root
        node = nodes.get(rel)
        if node is not None:
            return node
        parts = rel.split("/")
        if max_depth and len(parts) > max_depth:
            return None
        parent = ensure_dir("/".join(parts[:-1]))
        if parent is None:
            return None
        node = {
            "name": parts[-1],
            "rel": rel,
            "path": os.path.join(base_abs, *parts) if base_abs else "",
            "is_dir": True,
            "recorded": True,
            "children": [],
        }
        nodes[rel] = node
        parent["children"].append(node)
        return node

    for folder in sorted(structure.folders):
        ensure_dir("/".join(p for p in folder.split("/") if p))

    if show_files:
        if structure.files:
            _add_recorded_files(structure.files, ensure_dir, base_abs, max_depth)
        elif base_abs and os.path.isdir(base_abs):
            _add_disk_files(root)

    return root


def _add_recorded_files(files, ensure_dir, base_abs, max_depth):
    """structure.files 를 해당 폴더 노드의 자식으로 추가(Recreate 대상 = recorded True).

    파일이 든 폴더가 structure.folders 에 없더라도(그럴 일은 드물지만) 폴더 노드를
    만들어 붙인다 — 트리에서 사라져 "왜 안 만들어지지" 가 되지 않도록.
    """
    for rel in sorted(files):
        parts = [p for p in rel.split("/") if p]
        if not parts:
            continue
        if max_depth and len(parts) > max_depth:
            continue
        parent = ensure_dir("/".join(parts[:-1]))
        if parent is None:
            continue
        parent["children"].append({
            "name": parts[-1],
            "rel": rel,
            "path": os.path.join(base_abs, *parts) if base_abs else "",
            "is_dir": False,
            "recorded": True,
            "children": [],
        })


def _add_disk_files(node):
    """node(폴더) 이하의 각 폴더에 **디스크의 실제 파일**을 자식으로 추가(표시 전용).

    기록된 파일이 없는 구조에서 원본 폴더의 내용을 눈으로 확인하는 용도이므로
    recorded=False (Recreate 하지 않는다).
    """
    for child in list(node["children"]):
        if child["is_dir"]:
            _add_disk_files(child)

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
                "is_dir": False, "recorded": False, "children": [],
            })


@dataclass
class RecreateResult:
    """recreate() 결과. 폴더/파일을 따로 센다.

    예전 호출부가 `created, existing = recreate(...)` 로 쓰던 것을 깨지 않도록
    2-튜플로도 언패킹된다(폴더 목록). 항목이 늘어도 호출부가 안 깨진다.
    """

    created: list = field(default_factory=list)         # 새로 만든 폴더
    existing: list = field(default_factory=list)        # 이미 있던 폴더
    created_files: list = field(default_factory=list)   # 새로 만든 빈 파일
    existing_files: list = field(default_factory=list)  # 이미 있던(건드리지 않은) 파일

    def __iter__(self):
        return iter((self.created, self.existing))


def recreate(structure, project_root, folders=None, base_abs=None,
             files=None, file_suffix=RECREATED_SUFFIX):
    """structure 의 폴더(및 선택 시 파일)를 목적지 베이스 폴더 아래에 생성한다.

    base_abs : 목적지 베이스 폴더 절대경로. 주어지면 그 폴더 '바로 안'에 생성한다
               (UI 의 'Recreate To' 칸). None 이면 하위호환으로
               project_root + structure.base_rel 을 베이스로 계산한다.
    folders : 생성할 폴더 상대경로(POSIX) 목록. None 이면 structure.folders 전체(하위호환).
              지정하면 그 폴더들만 생성한다(깊이/포함 여부는 호출자가 이미 걸러 전달).
    files   : 생성할 파일 상대경로(POSIX) 목록. None 이면 **파일을 만들지 않는다**
              (기존 동작 유지 — 파일 생성은 호출자가 명시적으로 켜야 한다).
    file_suffix : 생성 파일 이름 끝에 붙일 표식. 기본 "__" (test.ma -> test.ma__).

    파일은 **0 바이트 빈 파일**로 만든다. 같은 이름이 이미 있으면 **손대지 않는다**
    (내용을 지우지 않는다). 파일의 부모 폴더는 folders 에 없더라도 함께 만든다.
    반환: RecreateResult.
    """
    selected = structure.folders if folders is None else folders

    if base_abs is None:
        if not project_root:
            raise ValueError("Project root is not set")
        base_abs = os.path.join(
            os.path.abspath(project_root),
            *structure.base_rel.split("/"),
        )
    else:
        base_abs = os.path.abspath(base_abs)

    targets = [base_abs] + [
        os.path.join(base_abs, *folder.split("/"))
        for folder in selected
    ]

    result = RecreateResult()
    seen = set()
    for path in targets:
        if path in seen:
            continue
        seen.add(path)
        if os.path.isdir(path):
            result.existing.append(path)
        else:
            os.makedirs(path, exist_ok=True)
            result.created.append(path)

    for rel in (files or []):
        parts = [p for p in rel.split("/") if p]
        if not parts:
            continue
        parent = os.path.join(base_abs, *parts[:-1])
        path = os.path.join(parent, marked_name(parts[-1], file_suffix))

        if os.path.exists(path):
            result.existing_files.append(path)
            continue

        # 파일이 든 폴더가 folders 에서 빠져 있어도(깊이 제한/체크 해제) 파일을 만들려면
        # 부모 폴더는 있어야 한다. 여기서 만든 폴더도 created 에 집계한다.
        if not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
            if parent not in seen:
                seen.add(parent)
                result.created.append(parent)

        # "x" = 배타적 생성. 위 exists 검사와 생성 사이의 경쟁 상태에서도 기존 파일을
        # 덮어쓰지 않는다(빈 파일로 날려버리는 사고 방지).
        try:
            with open(path, "x", encoding="utf-8"):
                pass
            result.created_files.append(path)
        except FileExistsError:
            result.existing_files.append(path)

    return result
