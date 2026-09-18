# Mesh Tool
VERSION = "01.09"
LAST_UPDATE = "2026-09-18"

# 01.06  Match 탭 From 리스트의 List From Mesh / Add / Del 버튼 글자가 잘리던 문제.
#        TSL 위젯 전체에 걸려 있던 setMaximumHeight 를 치우고 리스트에만 높이를 제한한다.
# 01.07  로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로 교체 (Expand / Clear / Copy)
# 01.09  Match 탭을 하위 탭 Default / By Weight 로. Default = 기존 Match 그대로. By Weight =
#        스킨 메시(M_w) 조인트 웨이트를 마스크로 메시(M_j)들을 타깃(M_tgt) 쪽으로 웨이트 x 델타 만큼
#        (오브젝트 공간, 인덱스 대응). 짝짓기: 조인트 k -> 메시 k / 합 -> 모든 메시. Ctrl+Z 한 번
