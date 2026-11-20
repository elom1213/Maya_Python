# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00240_PathTool - version info
# 01.31  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식) · 처음 여는 폭은 예전 fit_to_content 그대로

# 01.32  ShortCut 탭의 Profile · Create · Color 를 접이식으로 - 헤더를 누르면 접히고, 접힘 상태는 data/ui_state.json 에 기억.
#        공용 Framework/qt/MOD_collapsible_qt_v01. 접거나 펴면 창 높이를 다시 맞춘다(tab_fit).

# 01.33  Profile · Create · Color 를 따로 접지 않고 접이식 섹션 하나(Profile / Create / Color)에 담아 함께 접는다.
#        세 그룹은 원래 상자(QGroupBox) 모양 그대로. 상태 키 shortcut_settings_expanded (v01.32 의 키 3개는 안 읽음).

VERSION = "01.33"
LAST_UPDATE = "2026-11-20"
