# -*- coding: utf-8 -*-
# A00030_quickTool_V02 - version info
#
# 02.00  레거시 maya.cmds 툴 A00030_quickTool(V01.16) 을 PySide(Qt) 로 재작성.
#        기능은 그대로 10개 버튼 6섹션. 로직을 app/core 로 분리하고, 결과는
#        print/warning 대신 공용 로그창(JUN_mod_log_qt_v01)에 쌓는다.
# 02.01  Shelf > Update Shelves 추가 : 지금 셸프 상태를 prefs/shelves 에 즉시 쓴다.
#        마야는 종료할 때만 저장해서, 켜 둔 채 새 마야를 띄우면 옛 셸프가 보였다.
# 02.02  공용 메뉴 바(JUN_mod_menuBar_qt_v01) 적용 — Help 에 Copy Tool Name.
# 02.03  File > Open Scene Folder 추가 : 씬이 저장된 폴더를 탐색기로 연다
#        (씬 파일이 있으면 그 파일을 선택한 채로).

VERSION = "02.03"
LAST_UPDATE = "2026-09-17"
