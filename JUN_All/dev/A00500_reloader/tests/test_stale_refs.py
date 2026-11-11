# -*- coding: utf-8 -*-
"""reload_package 가 패키지 재노출 이름의 옛 클래스를 남기지 않는지 시험 (일반 python, 마야 불필요).

    python dev/A00500_reloader/tests/test_stale_refs.py

재현: pkg.app.ui.main_window 가 `from pkg.app.core import Mgr` 로 쓰는데, 깊이 순서상
main_window 가 pkg.app.core 보다 먼저 리로드돼 옛 Mgr 을 붙잡던 문제
(A00110 v02.55 `copies_rotation` AttributeError, 2026-11-11).
"""
import os
import sys
import shutil
import tempfile
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if JUN_ALL not in sys.path:
    sys.path.insert(0, JUN_ALL)

sys.dont_write_bytecode = True

import config
config.DEV_MODE = True
from dev.A00500_reloader.app.core import reloader

passed = 0
failed = 0


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", label)
    else:
        failed += 1
        print("FAIL", label)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


root = tempfile.mkdtemp()
try:
    pkg = os.path.join(root, "zz_stalepkg")
    for sub in ("", "app", os.path.join("app", "ui")):
        write(os.path.join(pkg, sub, "__init__.py"), "")
    write(os.path.join(pkg, "app", "core", "__init__.py"), "from .mgr import Mgr\n")
    write(os.path.join(pkg, "app", "core", "mgr.py"), "class Mgr:\n    pass\n")
    write(os.path.join(pkg, "app", "ui", "main_window.py"),
          "from zz_stalepkg.app.core import Mgr\n"
          "def has_new():\n    return hasattr(Mgr, 'new_method')\n")
    sys.path.insert(0, root)

    mw = importlib.import_module("zz_stalepkg.app.ui.main_window")
    check("before edit: no new_method", not mw.has_new())

    # 코드 갱신(크기가 달라 pyc 와 무관하게 새로 읽힌다).
    write(os.path.join(pkg, "app", "core", "mgr.py"),
          "class Mgr:\n    def new_method(self):\n        return 1\n")
    importlib.invalidate_caches()

    ok, bad = reloader.reload_package("zz_stalepkg", quiet=True)
    mw = sys.modules["zz_stalepkg.app.ui.main_window"]
    check("one reload: main_window sees new_method", mw.has_new())
    check("one reload: same class object as package",
          mw.Mgr is sys.modules["zz_stalepkg.app.core"].Mgr
          is sys.modules["zz_stalepkg.app.core.mgr"].Mgr)
    check("no failures", not bad)
    check("no stale refs left", not any(
        reloader.stale_refs(sys.modules[n], set(ok)) for n in ok))
finally:
    sys.path.remove(root) if root in sys.path else None
    shutil.rmtree(root, ignore_errors=True)

print("\n{0} passed, {1} failed".format(passed, failed))
sys.exit(1 if failed else 0)
