# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00210_FileManager - directory scanner (UI/DCC 비의존)
#
# 지정한 경로에서 파일을 수집하고, MetaStore 의 기록과 조인한다. UI 파일 목록의 데이터 소스.
# 기본은 Maya 씬 파일(.mb/.ma)만 수집하지만, extensions 인자로 다른 포맷(또는 모든 포맷)을
# 받을 수 있다(Lineage 탭에서 포맷 무관 노드 추가에 사용).

import os

from .store import MetaStore, OutsideProjectRootError

MAYA_EXTENSIONS = (".mb", ".ma")


def scan(dir_path, store, recursive=False, extensions=MAYA_EXTENSIONS):
    """dir_path 의 파일을 모아 dict 리스트로 반환.

    store : MetaStore (project_root/store_dir 보유). 키 산출 + 기록 조인에 사용.
    extensions : 허용 확장자 튜플(점 포함, 대소문자 무관). None 이면 **모든 파일**.
    각 항목:
        {
            "abs_path", "file_name", "ext", "mtime", "size",
            "key" or None,           # 루트 밖이면 None
            "has_record", "has_thumb", "author",
            "in_root",               # project_root 안인지
        }
    """
    results = []

    if not dir_path or not os.path.isdir(dir_path):
        return results

    allowed = None if extensions is None else tuple(e.lower() for e in extensions)

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

        ext = os.path.splitext(abs_path)[1].lower()
        if allowed is not None and ext not in allowed:
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
            "ext": ext.lstrip("."),
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
