# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00290_BSTool - 셸프 버튼 설치 + 드래그&드롭 진입점
#
# 이 파일을 Maya 뷰포트로 드래그&드롭하면 현재 셸프에 버튼이 설치된다.
# 설치된 버튼은 tools.A00290_BSTool.run(True) 를 호출한다.

import maya.cmds as cmds
import maya.mel as mel
import os
import sys


# =========================
# PATH
# =========================

TOOL_ROOT = os.path.dirname(__file__)              # .../tools/A00290_BSTool
JUN_ALL_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))  # .../JUN_All

if JUN_ALL_ROOT not in sys.path:
    sys.path.append(JUN_ALL_ROOT)


# =========================
# TOOL INFO
# =========================

TOOL_LABEL = "BSTool"

_ICON_PATH = os.path.join(TOOL_ROOT, "icon", "A00290_BSTool.png")
ICON_NAME = _ICON_PATH if os.path.exists(_ICON_PATH) else "pythonFamily.png"

# 셸프 버튼이 실행할 명령.
SHELF_COMMAND = r'''
import sys

ROOT = r"{root}"

if ROOT not in sys.path:
    sys.path.append(ROOT)

import tools.A00290_BSTool as A00290_BSTool

A00290_BSTool.run(True)
'''.format(
    root=JUN_ALL_ROOT.replace("\\", "/")
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

        if "A00290_BSTool.run(True)" in str(cmd):

            cmds.deleteUI(btn)

    # 새 버튼 생성
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


# =========================
# DRAG & DROP ENTRY
# =========================

def onMayaDroppedPythonFile(*args):

    try:
        install_shelf_button()
    finally:
        # 이 파일은 베이스네임으로 import 되어 sys.modules 에 캐시된다.
        # 같은 이름이 다시 드롭될 때 캐시된(이전) 모듈이 실행되는 것을 막기 위해
        # 자기 자신을 캐시에서 제거한다.
        import sys
        sys.modules.pop(__name__, None)
