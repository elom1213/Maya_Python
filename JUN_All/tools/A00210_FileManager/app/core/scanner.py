# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - directory scanner (UI/DCC 비의존)
#
# 지정한 경로에서 Maya 씬 파일(.mb/.ma)을 수집하고, MetaStore 의 기록과 조인한다.
# UI 파일 목록의 데이터 소스.

import os

from .store import MetaStore, OutsideProjectRootError

MAYA_EXTENSIONS = (".mb", ".ma")


def scan(dir_path, store, recursive=False):
    """dir_path 의 .mb/.ma 를 모아 dict 리스트로 반환.

    store : MetaStore (project_root/store_dir 보유). 키 산출 + 기록 조인에 사용.
    각 항목:
        {
            "abs_path", "file_name", "mtime", "size",
            "key" or None,           # 루트 밖이면 None
            "has_record", "has_thumb", "author",
            "in_root",               # project_root 안인지
        }
    """
    results = []

    if not dir_path or not os.path.isdir(dir_path):
        return results

    if recursive:
        walker = (
            os.path.join(root, name)
            for root, _dirs, files in os.walk(dir_path)
            for name in files
        )
    else:
        walker = (
            os.path.join(dir_path, name)
            for name in os.listdir(dir_path)
        )

    for abs_path in walker:

        if not os.path.isfile(abs_path):
            continue

        if os.path.splitext(abs_path)[1].lower() not in MAYA_EXTENSIONS:
            continue

        try:
            stat = os.stat(abs_path)
            mtime = stat.st_mtime
            size = stat.st_size
        except OSError:
            mtime = 0
            size = 0

        entry = {
            "abs_path": abs_path,
            "file_name": os.path.basename(abs_path),
            "mtime": mtime,
            "size": size,
            "key": None,
            "has_record": False,
            "has_thumb": False,
            "author": "",
            "in_root": True,
        }

        try:
            key = store.make_key(abs_path)
            entry["key"] = key

            record = store.load(key)
            if record is not None:
                entry["has_record"] = True
                entry["author"] = record.author

            entry["has_thumb"] = store.has_thumb(key)

        except OutsideProjectRootError:
            entry["in_root"] = False

        results.append(entry)

    results.sort(key=lambda e: e["file_name"].lower())

    return results
