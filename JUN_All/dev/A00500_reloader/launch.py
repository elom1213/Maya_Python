# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00500_reloader - launch entry point (dev tool, in-Maya)
#
# 예전에는 dev/reloader_mayaScript_v02.py 의 네 줄을 마야 스크립트 에디터에 붙여 넣어 썼다.
# 이제 __dragDrop_A00500.py 로 설치한 셸프 버튼이 run(True) 를 부른다.
#
# run() 이 하는 일 (순서가 중요하다)
#   1. config 리로드          - DEV_MODE 를 바꾼 것이 바로 먹는다
#   2. 리로더 자신 리로드      - 패키지 목록 · 리로드 로직을 고친 것이 바로 먹는다
#   3. Framework / tools 리로드 - sys.modules 에 올라와 있는 것 전부, 깊은 것부터
#   4. 결과를 스크립트 에디터와 뷰포트(inViewMessage)에 보고
#
# 창이 없는 툴이다. 개발 전용이라 릴리즈본(dev/ 제외)에는 실리지 않는다 - docs/Release_Layout.md

import os
import sys
import importlib

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))          # .../dev/A00500_reloader
ROOT = os.path.abspath(os.path.join(TOOL_ROOT, "..", ".."))      # .../JUN_All

if ROOT not in sys.path:
    sys.path.append(ROOT)


def _in_view(message):
    """마야 뷰포트 메시지. 마야가 아니면(mayapy · 테스트) 조용히 건너뛴다."""
    try:
        import maya.cmds as cmds
        cmds.inViewMessage(amg=message, pos="midCenter", fade=True)
    except Exception:
        pass


def run(reload_module=True):
    """셸프 버튼 진입점. 반환 (ok 목록, failed 목록).

    reload_module : True 면 config 와 리로더 자신을 먼저 리로드한다 (셸프 버튼은 늘 True).
    """
    import config
    from dev.A00500_reloader.app.config import reload_packages
    from dev.A00500_reloader.app.core import reloader

    if reload_module:
        importlib.reload(config)
        importlib.reload(reload_packages)
        importlib.reload(reloader)

    if not config.DEV_MODE:
        print("[Reload] DEV_MODE is OFF - nothing reloaded (JUN_All/config.py)")
        _in_view("<hl>Reload</hl> skipped - DEV_MODE is OFF")
        return [], []

    ok, failed = reloader.reload_all()

    print("[Reload] {0} module(s) reloaded, {1} failed  ({2})".format(
        len(ok), len(failed), ", ".join(reload_packages.RELOAD_PACKAGES)))
    for name, error in failed:
        print("[Reload]   FAILED {0} : {1}".format(name, error))

    if failed:
        _in_view("<hl>Reload</hl> {0} reloaded, <hl>{1} failed</hl> - see Script Editor".format(
            len(ok), len(failed)))
    else:
        _in_view("<hl>Reload</hl> {0} module(s) reloaded".format(len(ok)))

    return ok, failed


def clean_pycache(root=None):
    """두 번째 셸프 버튼(__dragDrop_A00500_pycache.py) : JUN_All 아래 __pycache__ 전부 삭제.

    옛 dev/remove_pycache.py. 리로드가 .pyc 를 다시 쓰므로 보통은 필요 없고, 옛 .pyc 가 섞여
    이상할 때(파일을 옮긴 뒤 등)만 누른다. 반환 (지운 경로들, 실패들).
    """
    from dev.A00500_reloader.app.core import pycache

    removed, failed = pycache.remove_pycache(root)
    print("[Reload] __pycache__ : {0} removed, {1} failed (under {2})".format(
        len(removed), len(failed), root or pycache.JUN_ALL_ROOT))
    for path, error in failed:
        print("[Reload]   FAILED {0} : {1}".format(path, error))
    _in_view("<hl>__pycache__</hl> {0} folder(s) removed{1}".format(
        len(removed), ", <hl>{0} failed</hl>".format(len(failed)) if failed else ""))
    return removed, failed
