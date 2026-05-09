import importlib
import sys
import os

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