# -*- coding: utf-8 -*-
# A00470_MaterialTool - version info
#
# 01.00  Name Check 탭 : 메시 -> 머티리얼 수집 + 프로파일(JSON) 규칙 진단
#        (토큰 정렬 · 오타 교정 제안 · 상세 로그 · 클립보드 복사), 프로파일 Set_v001
# 01.01  Set_v001 에 고정 토큰 `CH` 추가 : MT_MANU_CH_{character}_{set}_{part}_{extra...}
# 01.02  로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로 교체 (Expand / Clear / Copy)
# 01.03  머티리얼 표 : 칸 폭을 드래그로 조절 + 씬 선택은 더블클릭으로(한 번 클릭은 선택만)
# 01.04  프로파일 `Basic_v001` 추가 : MT_MANU_CH_{character}_{part}_{extra...}
#        (part = Body / Head / Eye / Tooth / Hair). 코드 수정 없이 JSON 한 장.
# 01.05  Copy Material 탭 : 소스 메시 M 을 UUID 로 기억 -> 대상 메시 M_i 에 면별 머티리얼을 똑같이

VERSION = "01.05"
LAST_UPDATE = "2026-09-17"
