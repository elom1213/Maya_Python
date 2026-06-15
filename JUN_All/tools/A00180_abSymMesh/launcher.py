import importlib
import sys, os

from . import config
from .core import undo_bridge
from .core import mesh_io
from .core import sym_core
from . import abSymMesh_v01 as tool


def run(reload_module=False):
    """UI 실행 진입점. reload_module=True 면 코드 리로드 후 실행."""

    ROOT = os.path.dirname(__file__)

    if ROOT not in sys.path:
        sys.path.append(ROOT)

    if reload_module:
        print("[DEV MODE] : reload abSymMesh")
        # 깊은(core) 모듈부터 reload 후 UI 모듈 reload.
        for module in (undo_bridge, mesh_io, sym_core, tool):
            _reload(module)

    # undo 커맨드 플러그인 로드(없으면). 실제 사용 직전에도 자가 복구된다.
    mesh_io.ensure_undo_plugin()

    tool.build__()


def _reload(module):
    if module.__name__ in sys.modules:
        importlib.reload(module)
