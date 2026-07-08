# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00370_ToolLauncher - launch a JUN tool from its folder path (UI 비의존)
#
# 이 툴의 버튼은 '실행할 툴 폴더 경로' 하나를 담는다. 클릭하면 그 폴더의 파이썬
# 패키지를 import 해 run() 진입점을 호출한다 — 즉 셸프 버튼이 하던 일을 대신한다.
#
# JUN_All 의 모든 툴은 다음 규칙을 따른다(A00000_base 이후 공통):
#   <JUN_All>/tools/A000XX_name/
#     ├── __init__.py   →  from .launch import run     # run() 만 외부 노출
#     └── launch.py     →  run(reload_module=True)     # 셸프 버튼이 run(True) 호출
#
# 그래서 폴더 경로 하나만 있으면:
#   1) 부모 폴더( .../tools )의 부모( .../JUN_All )를 sys.path 에 추가하고
#   2) '<부모폴더명>.<툴폴더명>'  (예: tools.A00080_KWI_creator_V03) 을 import 한 뒤
#   3) 그 모듈의 run(True) 를 호출한다.
# 이는 각 툴의 __dragDrop 셸프 명령이 하는 동작과 정확히 동일하다.

import os
import sys
import importlib


def normalize_path(path):
    """따옴표/공백을 정리하고 OS 표준 경로로 정규화한다(빈 값이면 '')."""
    if not path:
        return ""
    cleaned = path.strip().strip('"').strip("'")
    if not cleaned:
        return ""
    return os.path.normpath(cleaned)


def resolve_module(path):
    """툴 폴더 경로 → (jun_all_root, module_name).

    module_name 은 '<부모폴더명>.<툴폴더명>' (JUN 규칙이면 'tools.A000XX_name').
    부모의 부모(root)를 sys.path 에 넣으면 그 이름으로 import 된다.
    """
    tool_dir = normalize_path(path).rstrip(os.sep)
    parent = os.path.dirname(tool_dir)          # .../tools
    root = os.path.dirname(parent)              # .../JUN_All
    module_name = "{0}.{1}".format(
        os.path.basename(parent), os.path.basename(tool_dir)
    )
    return root, module_name


def validate(path):
    """실행 가능한 툴 폴더인지 검사. (ok, message) 반환."""
    norm = normalize_path(path)
    if not norm:
        return False, "Path is empty."
    if not os.path.isdir(norm):
        return False, "Folder not found: {0}".format(norm)
    if not os.path.isfile(os.path.join(norm, "__init__.py")):
        return False, "No __init__.py in folder (not an importable tool)."
    return True, "OK"


def display_name(path):
    """경로에서 보기 좋은 기본 버튼 이름(툴 폴더명)을 뽑는다."""
    return os.path.basename(normalize_path(path).rstrip(os.sep))


def find_icon(path):
    """툴 폴더의 아이콘 파일 경로를 찾아 반환한다(없으면 '').

    JUN 규칙: <tool>/icon/<폴더명>.png. 그게 없으면 icon/ 안의 아무 png,
    그것도 없으면 png/svg 순으로 폭넓게 찾는다. 버튼에 곁들일 아이콘용.
    """
    tool_dir = normalize_path(path).rstrip(os.sep)
    icon_dir = os.path.join(tool_dir, "icon")
    if not os.path.isdir(icon_dir):
        return ""

    base = os.path.basename(tool_dir)
    # 1) 표준 이름( <폴더명>.png )
    preferred = os.path.join(icon_dir, base + ".png")
    if os.path.isfile(preferred):
        return preferred

    # 2) icon/ 안의 png → svg 순으로 첫 파일.
    for ext in (".png", ".svg"):
        try:
            hits = sorted(
                fn for fn in os.listdir(icon_dir)
                if fn.lower().endswith(ext)
            )
        except OSError:
            hits = []
        if hits:
            return os.path.join(icon_dir, hits[0])

    return ""


def launch(path, reload_module=True):
    """path 의 툴 패키지를 import 해 run() 을 호출한다. (ok, message) 반환.

    reload_module 은 run() 에 그대로 전달된다(DEV_MODE 면 그 툴이 자기 자신을 리로드).
    셸프 버튼과 동일하게 기본값 True.
    """
    ok, msg = validate(path)
    if not ok:
        return False, msg

    root, module_name = resolve_module(path)
    if root not in sys.path:
        sys.path.append(root)

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # import 단계 실패(문법 오류/의존성 등)
        return False, "Import failed ({0}): {1}".format(module_name, exc)

    run_fn = getattr(module, "run", None)
    if not callable(run_fn):
        return False, "Tool '{0}' has no run() entry point.".format(module_name)

    try:
        # 대부분의 툴 run(reload_module=True) — 인자를 못 받는 예외적 툴은 무인자로.
        try:
            run_fn(reload_module)
        except TypeError:
            run_fn()
    except Exception as exc:
        return False, "Launch failed ({0}): {1}".format(module_name, exc)

    return True, "Launched {0}".format(module_name)


def reveal_in_explorer(path):
    """탐색기에서 툴 폴더를 연다(Windows). (ok, message) 반환."""
    norm = normalize_path(path)
    if not os.path.isdir(norm):
        return False, "Folder not found: {0}".format(norm)
    try:
        os.startfile(norm)  # noqa: only available on Windows
    except Exception as exc:
        return False, "Could not open folder: {0}".format(exc)
    return True, "Opened {0}".format(norm)
