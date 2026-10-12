# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00530_dependency_check - launch entry point (dev tool, in-Maya or any python)
#
# Qt 바인딩 · pymel · maya.cmds · (선택) pyinstaller 가 이 인터프리터에서 실제로 import 되는지
# 표로 보고한다 (옛 dev/check_dependencies.py). 창이 없다 - 셸프 버튼은 run() 을 부르고
# 결과는 스크립트 에디터와 뷰포트 메시지로 간다. 터미널은 이 파일을 그대로 실행한다.

import os
import sys

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))          # .../dev/A00530_dependency_check
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


def run(check_standalone=False):
    """의존성 점검. 표를 print 하고 누락이 없으면 True.

    check_standalone : True 면 pyinstaller 같은 standalone 전용 항목도 검사한다.
    """
    from dev.A00530_dependency_check.app.core import dependency_check

    ok = dependency_check.run(check_standalone=check_standalone)
    if ok:
        _in_view("<hl>Dependencies</hl> all OK")
    else:
        _in_view("<hl>Dependencies</hl> something is MISSING - see Script Editor")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run(check_standalone=True) else 1)
