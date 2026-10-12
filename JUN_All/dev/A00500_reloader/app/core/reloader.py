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


def reload_package(package_name, quiet=False):
    """package_name 트리를 리로드한다. 반환 (ok 목록, (이름, 에러) 목록)."""
    ok = []
    failed = []

    if not config.DEV_MODE:
        print("[Reload] DEV_MODE is OFF")
        return ok, failed

    for mod_name in modules_of(package_name):
        module = sys.modules.get(mod_name)
        if module is None:
            continue
        try:
            importlib.reload(module)
            ok.append(mod_name)
            if not quiet:
                print("[Reload] OK : {0}".format(mod_name))
        except Exception as e:
            failed.append((mod_name, str(e)))
            print("[Reload] FAILED : {0}".format(mod_name))
            print(e)

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
