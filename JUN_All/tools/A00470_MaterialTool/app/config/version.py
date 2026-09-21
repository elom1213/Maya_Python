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
# 01.07  Name Check : `Rename to Suggested` 버튼 - 제안한 이름으로 실제로 바꾼다
#        (자리표시 `{character}` 가 남은 제안 · 기본/참조/잠긴 노드 · 이름 충돌은 건너뛴다).
#        리포트는 **이름 바로 아래에 제안 이름**, 틀린/빠진 토큰 목록은 Detailed 일 때만.
#        로그창은 색으로 - 틀린 이름 빨강 · 제안 이름 초록(클립보드는 그냥 글 그대로)
# 01.08  릴리즈본(다른 PC)에서 열리지 않던 문제 수정 - `launch.py` 가 dev 트리와 릴리즈본
#        배치를 스스로 구분한다(`TOOL_ROOT/Framework` 가 있으면 릴리즈본).
#        자세한 것은 docs/Release_Layout.md - 같은 고침이 전 툴에 함께 들어갔다.
# 01.09  Name Check : Profile 콤보가 처음 열릴 때 기본 규칙 `Set_v001` 을 고른다
#        (`profiles.DEFAULT_PROFILE`). 목록은 그대로 이름순이고, 그 이름이 없으면 첫 번째.

VERSION = "01.09"
LAST_UPDATE = "2026-09-21"
