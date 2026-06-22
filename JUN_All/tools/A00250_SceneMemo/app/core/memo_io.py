# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00250_SceneMemo - 사이드카 Export / Import
#
# 씬 내부 노드가 정본(source of truth) 이고, 이 모듈은 백업/공유/버전관리용으로
# 마야 파일 옆 "JUN_memo/" 폴더에 <sceneName>_memo.json 을 내보내고/읽어들인다.
# (마야 파일만 복사되면 사이드카가 따라가지 않으므로 정본은 아니다.)

import os
import json

import maya.cmds as cmds


MEMO_DIR = "JUN_memo"   # 마야 파일 옆에 만드는 전용 하위 폴더


def _scene_path():
    return cmds.file(query=True, sceneName=True) or ""


def sidecar_path():
    """현재 씬 기준 사이드카 json 경로. 씬이 미저장이면 None."""
    scene = _scene_path()
    if not scene:
        return None

    folder = os.path.dirname(scene)
    base = os.path.splitext(os.path.basename(scene))[0]
    return os.path.join(folder, MEMO_DIR, base + "_memo.json")


def export_sidecar(store):
    """store 데이터를 JUN_memo/<sceneName>_memo.json 으로 저장. 경로 반환(미저장이면 None)."""
    path = sidecar_path()
    if not path:
        return None

    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = store.get_data()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path


def import_sidecar(store, path=None, overwrite=True):
    """사이드카 json 을 읽어 store 에 병합. (added, updated) 반환(파일 없으면 None)."""
    path = path or sidecar_path()
    if not path or not os.path.isfile(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return store.merge(data, overwrite=overwrite)
