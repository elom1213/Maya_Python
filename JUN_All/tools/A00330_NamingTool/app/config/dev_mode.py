# Python Script by Ji Hun Park
# last Update date : 2026-10-02
# A00330_NamingTool - 개발자 모드 판정 (v01.14)
#
# launch.py 와 같은 규칙이다 (docs/Release_Layout.md):
#   릴리즈본 : 툴 폴더 안에 Framework 가 동봉돼 있다 -> 항상 False (config.py 가 실리지 않는다)
#   dev 트리 : JUN_All/config.py 의 DEV_MODE
#
# 쓰는 곳: Token 탭 Enum 칸의 `Values...` - 개발자 모드에서만 보인다. 공유받은 사람은 팀 이름 규칙
# (Dnable_Set_v001 의 값 목록)을 바꾸지 못한다.

import os
import importlib.util

# app/config/dev_mode.py -> app/config -> app -> <tool>
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))


def _read_dev_mode():
    if IS_RELEASE:
        return False
    # JUN_All/config.py 를 **경로로** 읽는다 - `import config` 는 흔한 이름이라 다른 툴 폴더의
    # config.py 를 집을 수 있다(Release_Layout.md). 못 읽으면 개발자 모드가 아닌 것으로 본다.
    path = os.path.join(os.path.dirname(os.path.dirname(TOOL_ROOT)), "config.py")
    if not os.path.isfile(path):
        return False
    try:
        spec = importlib.util.spec_from_file_location("_jun_all_config_for_A00330", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception:
        return False
    return bool(getattr(module, "DEV_MODE", False))


def is_dev_mode():
    """개발자 모드면 True. 부를 때마다 config.py 를 다시 읽는다(DEV_MODE 를 바꾸고 툴만 다시 열면 된다)."""
    return _read_dev_mode()
