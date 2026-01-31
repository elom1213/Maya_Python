import importlib
import sys

from JUN_All import config
from .reload_moduleList import *

def reload_all():
    if not config.DEV_MODE:
        print("[Reload] DEV_MODE is OFF")
        return

    print("[Reload] Reloading ALL modules")

    for group in MODULES.values():
        for mod_name in group:
            _reload_module(mod_name)

def reload_group(group_name):
    if not config.DEV_MODE:
        return

    if group_name not in MODULES:
        raise ValueError(f"Unknown group: {group_name}")

    print(f"[Reload] Reloading group: {group_name}")

    for mod_name in MODULES[group_name]:
        _reload_module(mod_name)

def reload_module(module_name):
    if not config.DEV_MODE:
        return

    _reload_module(module_name)

def _reload_module(module_name):
    if module_name not in sys.modules:
        print(f"[Reload] Skipped (not imported): {module_name}")
        return

    try:
        importlib.reload(sys.modules[module_name])
        print(f"[Reload] OK: {module_name}")
    except Exception as e:
        print(f"[Reload] FAILED: {module_name}")
        print(e)
