# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00500_reloader - 패키지 트리 리로드 로직 (dev/reloader_v02.py 에서 옮김, v01.00)
#
# sys.modules 에 올라와 있는 Framework / tools 모듈을 깊은 것부터 importlib.reload 한다.
# config.DEV_MODE 가 꺼져 있으면 아무것도 하지 않는다 (릴리즈본에는 이 파일 자체가 없다).
#
# 쓰는 곳
#   - 셸프 버튼 (A00500_reloader.run)            : reload_all()        - 전부
#   - 각 툴의 launch.py (dev.reloader_v02 재노출)  : reload_for_tool()   - Framework + 그 툴만

import sys
import importlib

import config
from dev.A00500_reloader.app.config.reload_packages import RELOAD_PACKAGES


EXCLUDE = {
    "__pycache__",
}


def modules_of(package_name):
    """sys.modules 에 올라와 있는 package_name 과 그 하위 모듈 이름들 - 깊은 것부터."""
    modules = [
        mod_name for mod_name in list(sys.modules.keys())
        if mod_name == package_name or mod_name.startswith(package_name + ".")
    ]
    # 깊은 모듈부터 리로드해야 부모가 새 자식을 잡는다.
    modules.sort(key=lambda x: x.count("."), reverse=True)
    return modules


def stale_refs(module, reloaded):
    """module 전역 중 **리로드로 바뀌기 전의 옛 클래스/함수**를 가리키는 이름들.

    `from pkg.app.core import Mgr` 처럼 **패키지 __init__ 이 재노출한 이름**을 가져다 쓰는
    모듈은, 깊이 순서상 패키지(`pkg.app.core`)보다 먼저 리로드된다(`pkg.app.ui.main_window` 가
    더 깊다). 그 순간 패키지 속성은 아직 옛 클래스라 main_window 가 옛 것을 붙잡는다.
    마야를 켠 채 코드를 받고 셸프 버튼을 처음 누르면 새로 만든 메서드가
    `AttributeError: type object 'CopyKeyManager' has no attribute 'copies_rotation'` 로 터진
    것이 이것이다(A00110 v02.55, 2026-11-11). 두 번째 누르면 풀린다.

    판정: 전역 값이 리로드한 모듈에서 온 클래스/함수인데, 그 모듈의 지금 같은 이름이
    다른 객체를 가리키면 옛 것이다.
    """
    stale = []
    for name, value in list(vars(module).items()):
        if not isinstance(value, type) and not callable(value):
            continue
        owner = getattr(value, "__module__", None)
        qual = getattr(value, "__qualname__", None)
        if owner not in reloaded or not qual or "." in qual:
            continue
        current = getattr(sys.modules.get(owner), qual, None)
        if current is not None and current is not value:
            stale.append(name)
    return stale


def reload_package(package_name, quiet=False, max_passes=4):
    """package_name 트리를 리로드한다. 반환 (ok 목록, (이름, 에러) 목록).

    첫 패스는 깊은 모듈부터. 그 뒤 옛 클래스/함수를 붙잡은 모듈만 골라 다시 리로드한다
    (`stale_refs`) - 없어질 때까지, 최대 max_passes 번.
    """
    ok = []
    failed = []

    if not config.DEV_MODE:
        print("[Reload] DEV_MODE is OFF")
        return ok, failed

    def _reload(mod_name):
        module = sys.modules.get(mod_name)
        if module is None:
            return False
        try:
            importlib.reload(module)
            if not quiet:
                print("[Reload] OK : {0}".format(mod_name))
            return True
        except Exception as e:
            failed.append((mod_name, str(e)))
            print("[Reload] FAILED : {0}".format(mod_name))
            print(e)
            return False

    order = modules_of(package_name)
    for mod_name in order:
        if _reload(mod_name):
            ok.append(mod_name)

    reloaded = set(ok)
    for _ in range(max_passes):
        again = [n for n in order
                 if n in sys.modules and stale_refs(sys.modules[n], reloaded)]
        if not again:
            break
        for mod_name in again:
            if not quiet:
                print("[Reload] stale refs : {0} ({1})".format(
                    mod_name, ", ".join(stale_refs(sys.modules[mod_name], reloaded))))
            _reload(mod_name)

    return ok, failed


def reload_all(quiet=False):
    """RELOAD_PACKAGES(Framework, tools) 전부. 반환 (ok 목록, failed 목록)."""
    ok = []
    failed = []
    for package in RELOAD_PACKAGES:
        o, f = reload_package(package, quiet=quiet)
        ok.extend(o)
        failed.extend(f)
    return ok, failed


# dev/reloader_v02.py 시절 이름 - 재노출 모듈과 옛 호출부가 쓴다.
def reload_all_v02():
    reload_all()


def reload_for_tool(tool_package):
    """단일 툴 실행용 reload.

    전체 tools 가 아니라 Framework + 해당 툴만 reload 한다.
    reload_all() 은 sys.modules 의 모든 tools.* 를 reload 하면서
    다른 툴의 launch 모듈 최상단(window_instance = None)을 재실행해
    이미 떠 있던 그 툴 창의 유일한 파이썬 참조를 끊어 창이 닫히는 부작용이 있다.
    툴 실행 시에는 자기 자신과 Framework 만 reload 해 다른 툴 창을 보존한다.
    """
    reload_package("Framework")
    reload_package(tool_package)
