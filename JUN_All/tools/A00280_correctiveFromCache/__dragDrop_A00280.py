# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - 셸프 버튼 설치 + 드래그&드롭 진입점

import maya.cmds as cmds
import maya.mel as mel
import os
import sys


TOOL_ROOT = os.path.dirname(__file__)              # .../tools/A00280_correctiveFromCache
JUN_ALL_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))  # .../JUN_All

if JUN_ALL_ROOT not in sys.path:
    sys.path.append(JUN_ALL_ROOT)


TOOL_LABEL = "CacheCorrective"

_ICON_PATH = os.path.join(TOOL_ROOT, "icon", "A00280_correctiveFromCache.png")
ICON_NAME = _ICON_PATH if os.path.exists(_ICON_PATH) else "pythonFamily.png"

SHELF_COMMAND = r'''
import sys

ROOT = r"{root}"

if ROOT not in sys.path:
    sys.path.append(ROOT)

import tools.A00280_correctiveFromCache as A00280_correctiveFromCache

A00280_correctiveFromCache.run(True)
'''.format(
    root=JUN_ALL_ROOT.replace("\\", "/")
)


def install_shelf_button():

    current_shelf = mel.eval('$temp=$gShelfTopLevel')
    current_tab = cmds.tabLayout(current_shelf, q=True, selectTab=True)

    shelf_buttons = cmds.shelfLayout(current_tab, q=True, childArray=True) or []

    for btn in shelf_buttons:

        cmd = cmds.shelfButton(btn, q=True, command=True)

        if "A00280_correctiveFromCache.run(True)" in str(cmd):

            cmds.deleteUI(btn)

    cmds.shelfButton(
        parent=current_tab,
        label=TOOL_LABEL,
        annotation=TOOL_LABEL,
        imageOverlayLabel=TOOL_LABEL,
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


def onMayaDroppedPythonFile(*args):

    try:
        install_shelf_button()
    finally:
        # 베이스네임 import 캐시 충돌 방지 (CLAUDE.md 규칙)
        import sys
        sys.modules.pop(__name__, None)
