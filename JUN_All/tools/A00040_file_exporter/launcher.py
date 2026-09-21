import importlib
import sys
import os

# dev 트리와 릴리즈본은 배치가 다르다 - 경로는 "있는 것"을 보고 정한다.
#   dev 트리 : Framework 가 JUN_All 에 있고 모든 툴이 공유한다
#   릴리즈본 : Framework 는 툴 폴더 안에 동봉된다
# 본체 모듈이 `from Framework...` 를 하므로 **아래 `from . import` 보다 먼저** 잡아야 한다.
# 자세한 것은 docs/Release_Layout.md
TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))

ROOT = os.path.abspath(os.path.join(TOOL_ROOT, "..", ".."))

IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))

for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)


from . import file_exporter_v01 as tool
from . import config


def run(reload_module=False):
    """
    UI 실행 진입점
    reload_module=True 면 코드 리로드 후 실행
    """

    ROOT = os.path.dirname(__file__)

    if ROOT not in sys.path:
        sys.path.append(ROOT)

    if reload_module:
        print("[DEV MODE] : reload file_exporter_v01")
        base__reload(tool)

    tool.build__()


def base__reload(module):
    if module.__name__ in sys.modules:
        importlib.reload(module)