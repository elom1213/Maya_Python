# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00500_reloader - 셸프 버튼 설치 + 드래그&드롭 진입점
#
# 이 파일을 Maya 뷰포트로 드래그&드롭하면 현재 셸프에 버튼이 설치된다.
# 설치된 버튼은 dev.A00500_reloader.run(True) 를 호출한다 - Framework / tools 모듈 전부 리로드.
# 개발 전용 툴이라 tools/ 가 아니라 dev/ 에 있다 (릴리즈본에는 실리지 않는다).

import maya.cmds as cmds
import maya.mel as mel
import os
import sys


# =========================
# PATH
# =========================

TOOL_ROOT = os.path.dirname(__file__)                       # .../dev/A00500_reloader
JUN_ALL_ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))  # .../JUN_All

# JUN_All 을 sys.path 에 추가 (dev 패키지 import 가능하게)
if JUN_ALL_ROOT not in sys.path:
    sys.path.append(JUN_ALL_ROOT)


# =========================
# TOOL INFO
# =========================

TOOL_LABEL = "Reload"

_ICON_PATH = os.path.join(TOOL_ROOT, "icon", "A00500_reloader.png")
ICON_NAME = _ICON_PATH if os.path.exists(_ICON_PATH) else "pythonFamily.png"

# 셸프 버튼이 실행할 명령.
# ROOT 는 JUN_All 경로여야 `import dev.A00500_reloader` 가 동작한다.
SHELF_COMMAND = r'''
import sys

ROOT = r"{root}"

if ROOT not in sys.path:
    sys.path.append(ROOT)

import dev.A00500_reloader as A00500_reloader

A00500_reloader.run(True)
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

        # childArray 는 버튼 말고 구분선(separator) 등도 준다.
        # shelfButton 이 아닌 것에 shelfButton 질의를 하면 RuntimeError 가 난다.
        try:
            cmd = cmds.shelfButton(btn, q=True, command=True)
        except RuntimeError:
            continue

        if "A00500_reloader.run(True)" in str(cmd):

            cmds.deleteUI(btn)

    # 새 버튼 생성
    cmds.shelfButton(
        parent=current_tab,
        label=TOOL_LABEL,
        annotation="Reload every Framework / tools module (dev only - needs config.DEV_MODE)",
        imageOverlayLabel=TOOL_LABEL,
        image1=ICON_NAME,
        style="iconAndTextVertical",
        command=SHELF_COMMAND,
        sourceType="python"
    )

    cmds.inViewMessage(
        amg="<hl>{0}</hl> shelf button installed.".format(TOOL_LABEL),
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
