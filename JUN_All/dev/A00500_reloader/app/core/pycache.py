# -*- coding: utf-8 -*-
# A00500_reloader - __pycache__ 비우기 (옛 dev/remove_pycache.py + remove_pycache_for_dev.py)
#
# 고정 경로(G:/...)로 부르던 _for_dev 는 지웠다. 기본 루트는 이 파일 기준으로 계산한 JUN_All.

import os
import shutil

# core -> app -> A00500_reloader -> dev -> JUN_All
JUN_ALL_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))


def find_pycache(root=None):
    """root 아래 __pycache__ 폴더 경로들 (깊은 것 포함)."""
    root = root or JUN_ALL_ROOT
    found = []
    for dirpath, dirnames, _files in os.walk(root):
        for dirname in list(dirnames):
            if dirname == "__pycache__":
                found.append(os.path.join(dirpath, dirname))
                dirnames.remove(dirname)        # 그 안은 더 내려가지 않는다
    return found


def remove_pycache(root=None):
    """root(기본 JUN_All) 아래 __pycache__ 전부 삭제. 반환 (지운 경로들, (경로, 에러) 들)."""
    removed = []
    failed = []
    for path in find_pycache(root):
        try:
            shutil.rmtree(path)
            removed.append(path)
        except Exception as e:
            failed.append((path, str(e)))
    return removed, failed
