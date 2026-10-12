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

VERSION = "01.03"
LAST_UPDATE = "2026-10-12"
