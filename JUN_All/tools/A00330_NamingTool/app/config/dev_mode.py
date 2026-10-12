# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00330_NamingTool - 개발자 모드 판정 (v01.14, v01.27 공용화)
#
# v01.27 : 판정 규칙을 Framework.core.dev_mode 로 올렸다 (다른 툴도 같은 규칙을 쓴다 - A00120 등).
#          이 모듈은 그 공용 함수를 이 툴의 경로로 부르는 얇은 껍데기다. 이름(`is_dev_mode()`,
#          `IS_RELEASE`, `TOOL_ROOT`)은 token_tab / main_window 가 쓰므로 그대로 둔다.
#
# 규칙 (docs/Release_Layout.md):
#   릴리즈본 : 툴 폴더 안에 Framework 가 동봉돼 있다 -> 항상 False (config.py 가 실리지 않는다)
#   dev 트리 : JUN_All/config.py 의 DEV_MODE
#
# 쓰는 곳: Token 탭 Enum 칸의 `Values...` - 개발자 모드에서만 보인다. 공유받은 사람은 팀 이름 규칙
# (Dnable_Set_v001 의 값 목록)을 바꾸지 못한다.

import os

from Framework.core import dev_mode as _dev_mode

# app/config/dev_mode.py -> app/config -> app -> <tool>
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IS_RELEASE = _dev_mode.is_release(__file__)


def is_dev_mode():
    """개발자 모드면 True. 부를 때마다 config.py 를 다시 읽는다(DEV_MODE 를 바꾸고 툴만 다시 열면 된다)."""
    return _dev_mode.is_dev_mode(__file__)
