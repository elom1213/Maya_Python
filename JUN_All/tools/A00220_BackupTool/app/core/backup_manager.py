# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00220_BackupTool - 백업 핵심 로직 (UI/DCC 비의존)
#
# 원본 파일을 같은 폴더의 backup 하위 폴더로 복사한다.
#  - overwrite 모드: {base}_{suffix}{ext} 로 항상 덮어씀
#  - version 모드:    {base}_{suffix}_{NN}{ext} 로 증가, 최근 N개만 유지(롤오버)

import os
import re
import shutil

# 버전 인덱스 자릿수 (예: _01, _02 ... 99 초과 시 자릿수 자동 확장).
_PAD = 2


def backup_dir_for(source_path, folder_name):
    """원본 파일이 위치한 폴더 아래의 backup 폴더 경로를 반환한다.

    폴더가 없으면 만들고, 이미 있으면 그대로 둔다(makedirs 는 멱등).
    """
    parent = os.path.dirname(os.path.abspath(source_path))
    backup_dir = os.path.join(parent, folder_name)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def backup_one(source_path, folder_name="backup", suffix="BU",
               versioned=False, max_versions=10):
    """source_path 를 backup 폴더로 1회 복사하고 생성된 백업 절대경로를 반환한다.

    원본이 없으면 FileNotFoundError 를 던진다(호출측에서 잡아 스킵).
    """
    if not os.path.isfile(source_path):
        raise FileNotFoundError(source_path)

    backup_dir = backup_dir_for(source_path, folder_name)
    base, ext = os.path.splitext(os.path.basename(source_path))

    if not versioned:
        # 덮어쓰기: 단일 백업 파일을 매번 갱신.
        dst = os.path.join(backup_dir, f"{base}_{suffix}{ext}")
        shutil.copy2(source_path, dst)
        return dst

    # 버전업: 다음 인덱스로 새 파일 생성 후 오래된 버전 정리.
    existing = list_versions(backup_dir, base, suffix, ext)
    next_index = (existing[-1][0] + 1) if existing else 1
    dst = os.path.join(backup_dir, f"{base}_{suffix}_{next_index:0{_PAD}d}{ext}")
    shutil.copy2(source_path, dst)

    _prune_versions(backup_dir, base, suffix, ext, max_versions)
    return dst


def list_versions(backup_dir, base, suffix, ext):
    """backup 폴더에서 {base}_{suffix}_{NN}{ext} 형태 파일을 찾아

    [(index, filename), ...] 를 인덱스 오름차순으로 반환한다.
    """
    if not os.path.isdir(backup_dir):
        return []

    pattern = re.compile(
        r"^" + re.escape(f"{base}_{suffix}_") + r"(\d+)" + re.escape(ext) + r"$"
    )

    found = []
    for name in os.listdir(backup_dir):
        m = pattern.match(name)
        if m:
            found.append((int(m.group(1)), name))

    found.sort(key=lambda item: item[0])
    return found


def _prune_versions(backup_dir, base, suffix, ext, max_versions):
    """버전 파일이 max_versions 를 넘으면 가장 오래된(인덱스 작은) 것부터 삭제한다."""
    if max_versions is None or max_versions <= 0:
        return

    versions = list_versions(backup_dir, base, suffix, ext)
    excess = len(versions) - max_versions
    for _index, name in versions[:max(0, excess)]:
        try:
            os.remove(os.path.join(backup_dir, name))
        except OSError:
            pass
