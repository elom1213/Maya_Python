# -*- coding: utf-8 -*-
# A00440_SetTool - version info
#
# 01.00  Union / Intersection / Difference + Split (A∖S , A∩S)
# 01.01  탭 2개 : Edit(기존) / Create(오브젝트마다 <이름>_Set 세트를 만든다)
# 01.02  로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로 교체 (Expand / Clear / Copy)
# 01.04  탭 3개 : Find 추가 - 오브젝트들이 속한 세트를 찾아 리스트업, 행 클릭이
#                 (멤버가 아니라) 세트 노드 자체를 씬에서 선택

# 01.05  Create 에 Mode - 오브젝트마다 하나(원래) / **전부를 담은 세트 하나**.
#        Edit 탭에 Objects 리스트(Sets 우측) + `Add Objects to Sets` - 세트가
#        하나면 전부 그 하나에, 여럿이면 행 순서로 1:1(적은 쪽만큼)

# 01.06  Pin 켜짐(Pinned) = 연한 빨강 - 공용 Framework/qt/pin_style (A00240_PathTool 과 같은 색).
# 01.07  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식)

VERSION = "01.07"
LAST_UPDATE = "2026-10-29"
