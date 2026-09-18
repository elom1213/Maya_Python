# -*- coding: utf-8 -*-
# A00480_FileTool - version info
#
# 01.00  신규. 파일 입출력 · 경로 툴.
#        Export : A00040_file_exporter_V02(v02.09) 화면과 동작을 그대로 옮겼다.
#        Import : A00030_quickTool_V02 의 Import FBX normal.
#        Path   : A00030_quickTool_V02 의 Copy Scene Folder · Open Scene Folder.
#        합치면서 생긴 것 — Export Path 의 `Scene` 버튼(씬 폴더를 바로 채운다),
#        FBX 플러그인이 없을 때 Export 도 트레이스백 대신 로그로 알린다.
#        원본 두 툴은 무수정 보존.

# 01.01  창 크기를 A00040_file_exporter_V02 와 같게(slate_dark 960 x 853).
#        테마가 자식에 입혀진 뒤 레이아웃 최소 크기로 맞추고(show 다음 이벤트 루프),
#        Export 탭 페이지 여백 0 · 창 좌우 여백 -2(탭 테두리만큼) · Pin 높이 22.
#        v01.00 은 테마 전 글자 크기로 재서 약 1290 x 890 으로 떴다.

# 01.02  Pin 버튼 글자가 안 보이던 것 수정. 크기(72 x 22)는 그대로, 테마의 padding 8px 을
#        이 버튼만 위아래 0 으로(글자 영역 4px -> 20px).

# 01.03  Export 규칙 - 내보내기 전에 모든 세트를 검사, 하나라도 걸리면 파일을 하나도 안 쓴다.
#        첫 규칙 Check Hide Mesh (세트 안 메시 중 씬에서 안 보이는 것). 규칙은 export_rules.EXPORT_RULES 한 줄로 는다.

# 01.04  Check Hide Mesh 는 메시 자신(트랜스폼 + 쉐입)만 본다 - 숨겨진 그룹 · 조인트 등 메시가 아닌 오브젝트는 괜찮다.

# 01.05  규칙이 짚은 노드를 마야에서 선택 - Check 와 규칙에 막힌 Export 둘 다(숨긴 메시 트랜스폼).

VERSION = "01.05"
LAST_UPDATE = "2026-09-18"
