# -*- coding: utf-8 -*-
# A00510_release_builder - version info
#
# 01.00  툴을 골라 릴리즈 폴더로 복사하는 Qt 창 (dev/build_release.py 의 후신)
# 01.01  Include docs 옵션
# 01.02  목록 **검색(Filter)** — 공용 위젯 `JUN_mod_filter_qt_v01`. 체크는 보이는 것에만
#        걸고, 가려진 채 체크된 것은 릴리즈 때 개수를 알린다.
#        로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로(Expand / Shrink / Clear / Copy).
#        아이콘 추가(svg / png / 다중 크기 ico) + 작업 표시줄 AppUserModelID

# 01.03  폴더 이름 release_builder_QT -> A00510_release_builder (dev 툴도 tools 와 같은 번호 규칙).
#        아이콘 파일 이름 · ICON_STEM · 로그창 objectName 도 같이. __dragDrop_A00510.py 로 셸프 설치,
#        패키지 __init__ 의 run() 은 launch 를 늦게 import (import 만으로 AUMID 가 바뀌지 않게).

# 01.04  ★ 마야 셸프로 띄우면 **마야 UI 전체가 이 툴 테마로 바뀌던 것** 수정 - qss 를 QApplication(=마야)
#        이 아니라 이 창에만 입힌다. AppUserModelID · 앱 아이콘도 이 프로세스가 앱을 만들 때만
#        (예전엔 launch import 만으로 마야 프로세스의 작업 표시줄 ID 가 바뀌었다). 다시 누르면 이전 창을 닫는다.
#        Run_ReleaseBuilder.bat (더블클릭 실행) + make_shortcut.py - 툴 아이콘이 박힌 `Release Builder.lnk`.

VERSION = "01.04"
LAST_UPDATE = "2026-11-03"
