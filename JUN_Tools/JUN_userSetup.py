# C:\Users\user\Documents\maya\modules\scripts

import sys

TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun"
# TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun/JUN_Tools"

if TOOLS_ROOT not in sys.path:
    sys.path.append(TOOLS_ROOT)

'''
After run above code, runinng below

import JUN_Tools.JUN_ui

it well run __init__.py in JUN_Tools, JUN_ui

'''