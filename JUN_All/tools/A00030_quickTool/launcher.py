import importlib
import sys

from . import MOD_QuickTool_v01 as tool
from . import config


def run(reload_module=False):
    """
    UI 실행 진입점
    reload_module=True 면 코드 리로드 후 실행
    """

    if reload_module:
        print("[DEV MODE] : reload quickTool")
        quickTool_reload(tool)

    tool.build__()


def quickTool_reload(module):
    if module.__name__ in sys.modules:
        importlib.reload(module)