# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00370_ToolLauncher - version info

# 01.13  Pinned 동안 Pin 버튼이 연한 빨강 - 공용 Framework/qt/pin_style (A00240 · A00220 과 같은 색).
# 01.12  Shrink 때 Pin 을 Shrunk 아래로 내리고 빈 칸만큼 창을 좁힌다 - 350 -> 272 x 155.
# 01.11  Shrink 토글(Pin 왼쪽) - 메뉴 바 · 탭 · 저작권 줄을 감추고 창을 350 x 155 로
#        (A00220 · A00240 이 줄었을 때와 같은 크기). 줄어든 동안 버튼 왼쪽 자리에서 툴
#        아이콘의 로켓이 발사되기를 무한 반복(app/ui/rocket_anim.py, 한 바퀴 2.4초).
# 01.10  프로파일 정리(데이터만, 코드 변경 없음): Mesh -> MESH 이름 변경, FACIAL · UTIL 신설,
#        기존 버튼 순서 그대로 두고 새 카테고리에 툴 22종 추가(버튼 13 -> 38), 프로파일별 버튼 색.
#        계획서 docs/plans/A00370_ToolLauncher_profile_classification_plan.md
# 01.09  메뉴 Profile > Show Profiles Folder - 프로파일 json 폴더(data/profiles)를 탐색기로.
# 01.08  버튼 영역 위에 검색(Filter) 줄 - 공용 JUN_mod_filter_qt_v01(rows_provider).
#        버튼 이름 · 카테고리 이름 · 툴 폴더명으로 걸러 맞는 버튼만 남기고, 남은 버튼이
#        없는 카테고리는 통째로 숨긴다. 재렌더(편집 · Color Select) 뒤에도 필터 유지.

# 01.07  기본 프로파일의 버튼을 현행 툴로 정리. 옛 툴을 가리키던 버튼 5개 -
#        meshDoctor(A00380 의 MeshDoctor 탭으로 이식됨)는 삭제, uvTool / BSTool /
#        AnimTool / jointTool 은 현행 버전 폴더로 교체. 코드 변경은 없다(data/profiles).

VERSION = "01.13"
LAST_UPDATE = "2026-10-23"
