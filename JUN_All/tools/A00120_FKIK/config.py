# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - 셸프 버튼 설치 + 드래그&드롭 진입점
#
# 이 파일을 Maya 뷰포트로 드래그&드롭하면 현재 셸프에 버튼이 설치된다.
# 설치된 버튼은 tools.A00120_FKIK.run(True) 를 호출한다.

import maya.cmds as cmds
import maya.mel as mel
import os
import sys


# =========================
# DEV
# =========================

DEV_MODE = True


# =========================
# PATH
# =========================

TOOL_ROOT = os.path.dirname(__file__)              # .../tools/A00120_FKIK
JUN_ALL_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))  # .../JUN_All

# JUN_All 을 sys.path 에 추가 (tools 패키지 import 가능하게)
if JUN_ALL_ROOT not in sys.path:
    sys.path.append(JUN_ALL_ROOT)


# =========================
# TOOL INFO
# =========================

TOOL_LABEL = "FKIKTool"

ICON_NAME = "pythonFamily.png"

# 셸프 버튼이 실행할 명령.
# ROOT 는 JUN_All 경로여야 `import tools.A00120_FKIK` 가 동작한다.
SHELF_COMMAND = r'''
import sys

ROOT = r"{root}"

if ROOT not in sys.path:
    sys.path.append(ROOT)

import tools.A00120_FKIK as A00120_FKIK

A00120_FKIK.run(True)
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

        if "A00120_FKIK.run(True)" in str(cmd):

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
