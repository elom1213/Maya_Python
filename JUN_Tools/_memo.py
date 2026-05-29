# C:\Users\user\Documents\maya\modules\scripts
# 위 경로의 userSetup.py 에 아래 코드 복사하니 기대대로 기능이 됐음

import sys

# TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun"
TOOLS_ROOT = r"C:\Users/USER/Desktop/JP/0030_maya_python_JUN/Maya_Python"
# TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun/JUN_Tools"

if TOOLS_ROOT not in sys.path:
    sys.path.append(TOOLS_ROOT)

'''
After run above code, runinng below

import JUN_Tools.JUN_ui

it well run __init__.py in JUN_Tools, JUN_ui


의도한 경로가 sys.path 에 있는지 확인방법

import sys
    
ROOT = r"G:\D_link_dir/02_Maya_python_Jun"
print(ROOT in sys.path)

sys.path 경로 다 출력

for p in sys.path:
    print(p)

'''