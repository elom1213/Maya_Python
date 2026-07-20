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


# 버튼 경로 리베이스의 기준 앵커. 모든 JUN 툴은 <JUN_All>/tools/A000XX_name 아래에
# 있으므로, 경로에서 'tools' 세그먼트 뒤쪽(A000XX_name/...)을 붙박이 꼬리로 보고
# 새 루트에 다시 이어붙이면 PC 가 달라도 같은 툴을 가리키게 된다.
_TOOLS_ANCHOR = "tools"


def jun_all_root():
    """이 툴이 실제로 실행되고 있는 PC 의 JUN_All 루트 경로를 반환한다.

    A00370 자신이 <JUN_All>/tools/A00370_ToolLauncher/app/core/tool_launcher.py
    에 있으므로, 이 파일 위치에서 거슬러 올라가면 '현재 PC 의' JUN_All 을 항상
    알 수 있다 — 사용자가 아무것도 지정하지 않아도 되는 기본값이 된다.
    """
    here = os.path.dirname(os.path.abspath(__file__))   # .../app/core
    app_dir = os.path.dirname(here)                      # .../app
    tool_dir = os.path.dirname(app_dir)                  # .../A00370_ToolLauncher
    tools_dir = os.path.dirname(tool_dir)                # .../tools
    return os.path.dirname(tools_dir)                    # .../JUN_All


def _tools_tail(path):
    """path 에서 마지막 'tools' 세그먼트 '뒤' 조각(리스트)을 반환. 없으면 None.

    상대(`tools/A000XX/...`)든 절대(`C:/.../tools/A000XX/...`)든, 어느 PC 의 절대경로든
    동일하게 'tools' 앵커 뒤의 꼬리만 뽑는다. 이 꼬리가 PC 에 무관한 '툴 신원' 이다.
    """
    norm = normalize_path(path)
    if not norm:
        return None
    # normalize_path 는 OS 구분자로 바꾸지만, JSON 에 슬래시로 저장된 상대경로도 함께 받는다.
    parts = [p for p in norm.replace("/", os.sep).split(os.sep) if p not in ("", ".")]
    anchor = -1
    for i, seg in enumerate(parts):
        if seg.lower() == _TOOLS_ANCHOR:
            anchor = i
    if anchor < 0:
        return None
    tail = parts[anchor + 1:]           # ['A000XX_name', ...]
    return tail or None


def to_portable(path):
    """저장용 '이식 가능' 경로를 만든다(프로파일 JSON 에 넣는 형태).

    JUN_All/tools 안을 가리키면 `tools/A000XX_name/...`(슬래시 고정) 상대경로로 —
    이 값은 **PC 가 달라도 동일**하므로 git 에서 프로파일이 흔들리지 않는다.
    'tools' 앵커가 없으면(=JUN_All 밖 외부 절대경로) 정규화한 절대경로 그대로 둔다.
    """
    tail = _tools_tail(path)
    if tail is None:
        return normalize_path(path)
    return "/".join([_TOOLS_ANCHOR] + tail)


def resolve(stored, root):
    """저장된 경로(상대/절대 혼용) → 이 PC(=root) 기준 실제 절대경로.

    'tools' 앵커가 있으면(상대든, 다른 PC 에서 만든 절대든) 그 꼬리를 `root/tools/...` 로
    다시 이어 이 PC 의 실제 경로로 만든다. 앵커가 없으면(외부 절대경로) 그대로 쓴다.
    """
    tail = _tools_tail(stored)
    if tail is None:
        return normalize_path(stored)
    r = normalize_path(root)
    if not r:
        return normalize_path(stored)
    return os.path.normpath(os.path.join(r, _TOOLS_ANCHOR, *tail))


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

    보통 호출측(UI)이 이미 resolve() 로 이 PC 절대경로를 넘기지만, 저장된 값(상대 or
    다른 PC 절대경로)이 그대로 들어와 깨져 있어도, 현재 PC 의 JUN_All 루트로 resolve 한
    경로가 실제로 있으면 그쪽으로 조용히 복구한다.
    """
    ok, msg = validate(path)
    if not ok:
        healed = resolve(path, jun_all_root())
        if healed and validate(healed)[0]:
            path = healed
        else:
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
