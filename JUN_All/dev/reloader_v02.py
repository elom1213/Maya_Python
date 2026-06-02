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