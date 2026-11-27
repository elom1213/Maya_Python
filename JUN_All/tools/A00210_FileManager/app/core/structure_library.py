# Python Script by Ji Hun Park
# last Update date : 2026-11-27
# A00210_FileManager - Path Structure library (UI/DCC 비의존)
#
# v01.60 : Saved Structures 를 File Manager 프로파일에서 독립시킨다.
#   저장 위치 = 데이터 저장소 **루트**의 path_structures/ (프로파일 데이터 폴더 profiles/<folder>/ 밖).
#   모든 PC · 모든 프로파일이 같은 목록을 본다.
#
#   <repo>/path_structures/
#     ├── _categories/<id>.json     카테고리 하나 = 파일 하나 {"id", "name", "created_by", "created_at"}
#     └── <name>.json               구조 (PathStructure). "category" = 카테고리 id ("" = Uncategorized)
#
#   카테고리를 파일 하나씩 + id 참조로 두는 이유: 이름 바꾸기 = 그 파일 하나만 바뀌고, 두 PC 가 동시에
#   카테고리를 만들어도 새 파일 두 개라 git 충돌이 원리상 안 난다(목록 파일 하나면 충돌).
#   구조 파일은 카테고리와 무관하게 평평하게 둔다 - 이동 = JSON 의 category 만 수정.
#   계획 docs/plans/A00210_FileManager_structure_library_plan.md

import os
import json
import time
import uuid
import glob

from dataclasses import dataclass, asdict

from . import path_structure as ps_mod
from .store import MetaStore


LIB_DIR = ps_mod.STRUCTS_DIR          # "path_structures" - 저장소 루트 기준
CAT_DIR = "_categories"
UNCATEGORIZED = ""                    # category id 가 비었거나 모르는 id
UNCATEGORIZED_LABEL = "Uncategorized"
PROFILES_DIR = "profiles"             # 옛(v01.59 까지) 위치 profiles/<folder>/path_structures


def _now_iso():
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Category:
    id: str
    name: str
    created_by: str = ""
    created_at: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data, fallback_id=""):
        return Category(
            id=str(data.get("id") or fallback_id),
            name=str(data.get("name") or fallback_id),
            created_by=data.get("created_by", "") or "",
            created_at=data.get("created_at", "") or "",
        )


class StructureLibrary:
    """저장소 루트(repo_dir) 하나를 받아 path_structures/ 를 다룬다."""

    def __init__(self, repo_dir):
        self.repo_dir = os.path.abspath(repo_dir) if repo_dir else ""

    # -------------------------------------------------------------- paths

    def lib_dir(self):
        return os.path.join(self.repo_dir, LIB_DIR) if self.repo_dir else ""

    def cat_dir(self):
        return os.path.join(self.lib_dir(), CAT_DIR) if self.repo_dir else ""

    def _cat_path(self, cat_id):
        return os.path.join(self.cat_dir(), cat_id + ".json")

    # --------------------------------------------------------- categories

    def list_categories(self):
        """카테고리 목록(이름 대소문자 무시 정렬). 깨진 json 은 건너뛴다."""
        d = self.cat_dir()
        if not d or not os.path.isdir(d):
            return []
        out = []
        for fname in os.listdir(d):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(d, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                continue
            if isinstance(data, dict):
                out.append(Category.from_dict(data, fallback_id=fname[:-5]))
        return sorted(out, key=lambda c: (c.name.lower(), c.id))

    def _category_ids(self):
        return {c.id for c in self.list_categories()}

    def get_category(self, cat_id):
        for c in self.list_categories():
            if c.id == cat_id:
                return c
        return None

    def category_name(self, cat_id):
        c = self.get_category(cat_id) if cat_id else None
        return c.name if c is not None else UNCATEGORIZED_LABEL

    def find_category(self, name):
        """이름(대소문자 무시)으로 카테고리 찾기. 없으면 None."""
        key = (name or "").strip().lower()
        for c in self.list_categories():
            if c.name.lower() == key:
                return c
        return None

    def _check_name(self, name, ignore_id=""):
        name = (name or "").strip()
        if not name:
            raise ValueError("Category name is empty")
        if name.lower() == UNCATEGORIZED_LABEL.lower():
            raise ValueError("'{0}' is reserved".format(UNCATEGORIZED_LABEL))
        other = self.find_category(name)
        if other is not None and other.id != ignore_id:
            raise ValueError("A category named '{0}' already exists".format(other.name))
        return name

    def _write_category(self, cat):
        path = self._cat_path(cat.id)
        MetaStore._ensure_parent(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cat.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    def create_category(self, name, author=""):
        if not self.repo_dir:
            raise ValueError("Library folder is not set")
        name = self._check_name(name)
        ids = self._category_ids()
        cat_id = uuid.uuid4().hex[:8]
        while cat_id in ids:
            cat_id = uuid.uuid4().hex[:8]
        cat = Category(id=cat_id, name=name, created_by=author or "", created_at=_now_iso())
        self._write_category(cat)
        return cat

    def rename_category(self, cat_id, new_name):
        cat = self.get_category(cat_id)
        if cat is None:
            raise ValueError("Category not found")
        cat.name = self._check_name(new_name, ignore_id=cat_id)
        self._write_category(cat)
        return cat

    def delete_category(self, cat_id, mode="move"):
        """카테고리 삭제. mode "move" = 안의 구조를 Uncategorized 로, "delete" = 구조도 삭제.

        반환: 영향받은 구조 이름 목록.
        """
        if mode not in ("move", "delete"):
            raise ValueError("mode must be 'move' or 'delete'")
        path = self._cat_path(cat_id)
        if not os.path.isfile(path):
            raise ValueError("Category not found")
        names = [n for n, c in ps_mod.list_entries(self.repo_dir) if c == cat_id]
        if mode == "delete":
            for n in names:
                ps_mod.delete(self.repo_dir, n)
        else:
            self.set_category(names, UNCATEGORIZED)
        os.remove(path)
        return names

    # --------------------------------------------------------- structures

    def list_structures(self):
        """[(이름, category id)] - 모르는 id 는 UNCATEGORIZED 로 정규화."""
        ids = self._category_ids()
        return [(n, c if c in ids else UNCATEGORIZED) for n, c in ps_mod.list_entries(self.repo_dir)]

    def grouped(self):
        """트리 채우기용 [(Category | None, [이름...])]. 카테고리는 전부(빈 것 포함, 이름 순),
        None = Uncategorized 는 해당 구조가 있을 때만 맨 뒤."""
        entries = self.list_structures()
        out = []
        for cat in self.list_categories():
            out.append((cat, [n for n, c in entries if c == cat.id]))
        loose = [n for n, c in entries if c == UNCATEGORIZED]
        if loose:
            out.append((None, loose))
        return out

    def category_of(self, name):
        for n, c in self.list_structures():
            if n == name:
                return c
        return UNCATEGORIZED

    def load(self, name):
        return ps_mod.load(self.repo_dir, name)

    def save(self, structure):
        if not self.repo_dir:
            raise ValueError("Library folder is not set")
        return ps_mod.save(self.repo_dir, structure)

    def exists(self, name):
        return bool(self.repo_dir) and ps_mod.exists(self.repo_dir, name)

    def delete(self, name):
        return ps_mod.delete(self.repo_dir, name)

    def rename(self, old, new):
        return ps_mod.rename(self.repo_dir, old, new)

    def set_category(self, names, cat_id):
        """여러 구조를 한 카테고리로 옮긴다(JSON 의 category 만 바꿔 다시 쓴다). 반환: 옮긴 이름 목록."""
        cat_id = cat_id or UNCATEGORIZED
        if cat_id and cat_id not in self._category_ids():
            raise ValueError("Category not found")
        moved = []
        for name in names:
            path = ps_mod.struct_path(self.repo_dir, name)
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if (data.get("category", "") or "") == cat_id:
                continue
            data["category"] = cat_id
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            moved.append(name)
        return moved

    # ------------------------------------------------------------- legacy

    def legacy_files(self):
        """옛 위치(v01.59 까지)에 남은 구조 [(데이터 폴더, 절대경로)] - 이전 스크립트 대상."""
        if not self.repo_dir:
            return []
        pattern = os.path.join(self.repo_dir, PROFILES_DIR, "*", LIB_DIR, "*.json")
        out = []
        for path in sorted(glob.glob(pattern)):
            folder = os.path.basename(os.path.dirname(os.path.dirname(path)))
            out.append((folder, path))
        return out
