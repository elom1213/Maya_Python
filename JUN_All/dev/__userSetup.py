# C:\Users\user\Documents\maya\modules\scripts

import sys

TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun"
# TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun/JUN_All"

if TOOLS_ROOT not in sys.path:
    sys.path.append(TOOLS_ROOT)

'''
After run above code, runinng below

import JUN_All.JUN_ui

it well run __init__.py in JUN_Tools, JUN_ui

'''

from JUN_All import config 
from JUN_All.tools.A0020_move_skineWeightTool import *

import importlib

if config.DEV_MODE:
    importlib.reload(skinTool)
else :
    print("DEV mode pass");

skinTool.JUN_PY_move_skinWeightTool_v01_04(); 
