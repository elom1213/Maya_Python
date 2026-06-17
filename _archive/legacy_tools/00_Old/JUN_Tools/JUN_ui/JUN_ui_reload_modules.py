import importlib
from JUN_Tools import config
from . import JUN_module_tsl, JUN_module_radCol

def reload_all():
    if not config.DEV_MODE:
        return
    
    importlib.reload(JUN_module_tsl)
    importlib.reload(JUN_module_radCol)
    print("[DEV MODE] : Reload JUN_ui modules...")