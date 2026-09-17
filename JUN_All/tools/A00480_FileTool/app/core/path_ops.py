# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - Path 탭 로직 (maya.cmds, UI 비의존)
"""
path_ops - 씬 폴더 찾기 · 열기 · 붙여넣은 경로 다듬기.

- `scene_folder` / `open_scene_folder` : A00030_quickTool_V02 `quick_ops` 에서 옮겼다.
- `normalize_pasted_path` : A00040_file_exporter_V02 **UI**(`on_paste_path`) 안에 있던
  정규화를 코어로 내렸다. 클립보드를 읽는 것은 여전히 UI(Qt) 의 일이고, 여기는 문자열만 받는다.
  그래서 마야 없이도 검증할 수 있다.

전부 **로그 문자열 리스트**를 함께 돌려준다.
"""

import os

from Framework.core.file_opener import open_path


def _cmds():
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ==========================================================================
# Scene folder
# ==========================================================================

def scene_folder(native=True):
    """현재 씬이 저장된 **폴더** 경로. 저장 전이면 ("", 경고).

    - native=True  : OS 네이티브 모양(윈도우는 `\\`) - 탐색기·파일 다이얼로그에 붙여넣기용.
    - native=False : `/` 모양 - Export Path 처럼 툴 안에서 쓰는 경로.
    """
    cmds = _cmds()
    scene_path = cmds.file(q=True, sceneName=True) if cmds else ""
    if not scene_path:
        return "", ["[WARN] Current scene has not been saved yet (no scene folder)."]

    folder = os.path.normpath(os.path.dirname(scene_path))
    if not native:
        folder = folder.replace("\\", "/")
    return folder, []


def open_scene_folder():
    """현재 씬이 저장된 폴더를 OS 탐색기로 연다. 로그 리스트를 돌려준다.

    - 씬 파일이 디스크에 있으면 폴더를 열고 **그 파일을 선택(하이라이트)** 한다.
    - 파일이 지워졌거나 이름이 바뀌어 없으면 **폴더만** 연다.
    - 폴더까지 없으면(드라이브 분리 등) 탐색기를 띄우지 않고 경고한다.
    """
    folder, _logs = scene_folder()
    if not folder:
        return ["[WARN] Current scene has not been saved yet (no folder to open)."]

    if not os.path.isdir(folder):
        return ["[WARN] Scene folder does not exist on disk : {0}".format(folder)]

    scene_path = os.path.normpath(_cmds().file(q=True, sceneName=True))
    target = scene_path if os.path.isfile(scene_path) else folder

    try:
        open_path(target)
    except Exception as exc:
        return ["[WARN] Could not open the folder : {0} ({1})".format(folder, exc)]

    return ["Opened scene folder : {0}".format(folder)]


# ==========================================================================
# Pasted path
# ==========================================================================

def normalize_pasted_path(text):
    """클립보드 문자열을 **폴더 경로**로 다듬는다. 반환: (path, logs).

    사람이 복사해 오는 모양을 그대로 받아 준다.
      - 여러 줄이면 **첫 줄**, 앞뒤 공백은 뗀다.
      - 윈도우 `경로로 복사`(Shift+우클릭)가 붙이는 **따옴표**를 벗긴다.
      - 역슬래시는 `/` 로.
      - **파일** 경로면 그 **폴더**를 쓴다.

    비어 있으면 path 는 "" - 호출부는 기존 값을 건드리지 말 것.
    없는 경로여도 path 는 돌려준다(아직 안 만든 폴더 · 끊긴 네트워크 경로일 수 있다). 대신 경고.
    """
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    path = lines[0].strip('"').strip("'").strip() if lines else ""
    if not path:
        return "", ["[WARN] Clipboard has no text to paste."]

    path = path.replace("\\", "/")
    logs = []

    if os.path.isfile(path):
        folder = os.path.dirname(path)
        if folder:
            logs.append("Clipboard held a file - using its folder instead.")
            path = folder

    if os.path.isdir(path):
        logs.append("Export path : {0}".format(path))
    else:
        logs.append("[WARN] Pasted path does not exist yet : {0}".format(path))

    return path, logs
