# BS Tool V02 (Qt)
# 02.04  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식)

# 02.05  트리 펼치기 - 화살표로 펼치면 한 단계만, Shift + 펼치기/접기 = 아래 전부 (Naming 미리보기 트리).
#        공용 Framework/qt/MOD_treeExpand_qt_v01

# 02.06  Shape Editor 타겟 이름 표시 모드 - Names: Decoded(기본) / Raw (FBXASC).
#        FBX 로 들어온 일본어 · 중국어 · 띄어쓰기 타겟(FBXASC227FBXASC129FBXASC130)을 원래 글자(あ)로 보여 준다.
#        표시만 바꾼다 - 행 동작은 웨이트 인덱스 기준. 필터는 두 이름 다 찾는다. 공용 Framework/core/fbx_name (A00620 과 같은 디코더)

VERSION = "02.06"
LAST_UPDATE = "2026-11-09"
