# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - metadata store (UI/DCC 비의존)
#
# 중앙 데이터 리포(JUN_FileManager_data) 안의 record JSON / 썸네일 PNG 를 읽고 쓴다.
# 키(key)는 "프로젝트 루트 기준 상대경로" 로 PC 가 달라도 같은 파일이 같은 기록에 매핑된다.
#
#   <store_dir>/records/<key>.json
#   <store_dir>/thumbs/<key>.png

import os
import json
import shutil

from .models import FileRecord


class OutsideProjectRootError(Exception):
    """대상 파일이 project_root 밖에 있어 키를 만들 수 없을 때."""


class MetaStore:

    RECORDS_DIR = "records"
    THUMBS_DIR = "thumbs"

    def __init__(self, store_dir, project_root):
        self.store_dir = os.path.abspath(store_dir) if store_dir else ""
        self.project_root = os.path.abspath(project_root) if project_root else ""

    # ------------------------------------------------------------------ key

    def make_key(self, abs_file_path):
        """project_root 기준 상대경로(POSIX 슬래시)를 키로 반환.

        파일이 루트 밖이면 OutsideProjectRootError.
        """
        if not self.project_root:
            raise OutsideProjectRootError("Project root is not set")

        abs_file_path = os.path.abspath(abs_file_path)
        rel = os.path.relpath(abs_file_path, self.project_root)

        # 루트 밖이면 relpath 가 ".." 로 시작한다.
        if rel.startswith("..") or os.path.isabs(rel):
            raise OutsideProjectRootError(
                f"File is outside project root: {abs_file_path}"
            )

        return rel.replace("\\", "/")

    # --------------------------------------------------------------- paths

    def record_path(self, key):
        return os.path.join(
            self.store_dir,
            self.RECORDS_DIR,
            *key.split("/"),
        ) + ".json"

    def thumb_path(self, key):
        return os.path.join(
            self.store_dir,
            self.THUMBS_DIR,
            *key.split("/"),
        ) + ".png"

    @staticmethod
    def _ensure_parent(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # ------------------------------------------------------------- records

    def load(self, key):
        """record JSON 을 읽어 FileRecord 반환. 없으면 None."""
        path = self.record_path(key)

        if not os.path.isfile(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return FileRecord.from_dict(data)

    def save(self, record):
        """FileRecord 를 record JSON 으로 저장."""
        path = self.record_path(record.key)
        self._ensure_parent(path)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

        return path

    # -------------------------------------------------------------- thumbs

    def save_thumb(self, key, src_png):
        """임시 캡쳐 PNG 를 thumbs/<key>.png 로 복사하고 상대경로를 반환."""
        dst = self.thumb_path(key)
        self._ensure_parent(dst)
        shutil.copyfile(src_png, dst)

        return os.path.relpath(dst, self.store_dir).replace("\\", "/")

    def thumb_abs(self, key):
        """썸네일 절대경로(존재 여부와 무관)."""
        return self.thumb_path(key)

    def has_thumb(self, key):
        return os.path.isfile(self.thumb_path(key))
