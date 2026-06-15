import sys
import importlib
import config 
from .reload_path_list import *


EXCLUDE = {

    "__pycache__",

}

def reload_package(package_name):

    if not config.DEV_MODE:
        print("[Reload] DEV_MODE is OFF")
        return

    modules = []

    for mod_name in sys.modules.keys():
        if (
            mod_name == package_name
            or mod_name.startswith(package_name + ".")
        ):

            modules.append(mod_name)

    # 깊은 모듈부터 리로드
    modules.sort(
        key=lambda x: x.count("."),
        reverse=True
    )

    for mod_name in modules:

        try:

            importlib.reload(
                sys.modules[mod_name]
            )

            print(
                f"[Reload] OK : {mod_name}"
            )

        except Exception as e:

            print(
                f"[Reload] FAILED : {mod_name}"
            )

            print(e)

def reload_all_v02():

    for package in RELOAD_PACKAGES:

        reload_package(package)


def reload_for_tool(tool_package):
    """단일 툴 실행용 reload.

    전체 tools 가 아니라 Framework + 해당 툴만 reload 한다.
    reload_all_v02() 는 sys.modules 의 모든 tools.* 를 reload 하면서
    다른 툴의 launch 모듈 최상단(window_instance = None)을 재실행해
    이미 떠 있던 그 툴 창의 유일한 파이썬 참조를 끊어 창이 닫히는 부작용이 있다.
    툴 실행 시에는 자기 자신과 Framework 만 reload 해 다른 툴 창을 보존한다.
    """

    reload_package("Framework")
    reload_package(tool_package)