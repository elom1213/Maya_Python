import maya.cmds as cmds
import maya.mel as mel
import os
import sys


# =========================
# USER CONFIG
# =========================

TOOL_ROOT = os.path.dirname(__file__)
TOOL_PATH = "A00050_uvTool"


# tools 폴더 import 가능하게 추가
if TOOL_ROOT not in sys.path:
    sys.path.append(TOOL_ROOT)


# =========================
# TOOL INFO
# =========================

TOOL_LABEL = "uvTool"

ICON_NAME = "pythonFamily.png"

SHELF_COMMAND = r'''
import sys

ROOT = r"{root}"

if ROOT not in sys.path:
    sys.path.append(ROOT)

import tools.{tool_path} as {tool_path}

{tool_path}.run(True)
'''.format(
    root=TOOL_ROOT.replace("\\", "/"),
    tool_path = TOOL_PATH
)


# =========================
# SHELF CREATE
# =========================

def install_shelf_button():

    current_shelf = mel.eval('$temp=$gShelfTopLevel')
    current_tab = cmds.tabLayout(current_shelf, q=True, selectTab=True)

    # 중복 버튼 제거
    shelf_buttons = cmds.shelfLayout(current_tab, q=True, childArray=True) or []

    for btn in shelf_buttons:

        cmd = cmds.shelfButton(btn, q=True, command=True)

        if "A00050_uvTool.run(True)" in str(cmd):

            cmds.deleteUI(btn)

    # 새 버튼 생성
    cmds.shelfButton(
        parent=current_tab,
        label=TOOL_LABEL,
        annotation=TOOL_LABEL,
        image1=ICON_NAME,
        style="iconAndTextVertical",
        command=SHELF_COMMAND,
        sourceType="python"
    )

    cmds.inViewMessage(
        amg=f"<hl>{TOOL_LABEL}</hl> shelf button installed.",
        pos="midCenter",
        fade=True
    )

    print("Shelf Installed")


# =========================
# DRAG & DROP ENTRY
# =========================

def onMayaDroppedPythonFile(*args):

    install_shelf_button()