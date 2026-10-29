# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00340_SelectionTool - version info

# 01.07  View > Show Controls : Controls pane 을 통째로 숨기고 보인다(접기와 달리 영역이
#        남지 않는다). 상태는 data/active.json 에 저장.

# 01.08  배치를 좌우로: Controls 왼쪽 | 버튼 모음 오른쪽 (상하 -> 좌우 스플리터).
#        Profile/Create/Color 는 좁은 칸에 맞춰 두 줄, 창 기본 760x600, Log 가 왼쪽 칸의
#        남는 높이를 받는다.

# 01.09  v01.08 의 좌우 배치를 취소하고 상하로 복귀. 위 칸은 처음 보일 때 Controls 내용
#        높이에 맞춰 스크롤 없이 전부 보이고, 로그창은 Controls 밖 창 맨 아래로.

# 01.10  View > Show Profile : Explorer 를 열어 활성 프로파일 json 을 선택해 보여 준다
#        (이 PC 에서 툴이 읽고 쓰는 파일). 파일이 없으면 profiles 폴더를 연다.

# 01.11  최상위 탭 Buttons / Rules. Rules = 규칙 하나가 json 파일 하나(data/rules/<name>.json,
#        name · description · objects). New Rule from Selection 으로 현재 선택을 저장, Select
#        (더블클릭) 로 어느 씬에서든 그 이름 목록을 선택 - 없는 이름은 건너뛰고(빨강), 동명
#        노드는 전부 고르고 경고(주황). Rename 은 파일 이름도 함께, Delete 는 확인 뒤 파일 삭제,
#        여러 규칙을 골라 Select 하면 합집합. View > Show Rules Folder. 마지막 탭 기억.

# 01.12  창 가로 길이를 자유롭게 줄일 수 있게. Rules 탭 상태 줄의 폴더 **전체 경로**(공백 없는 한 단어라 줄이 안 바뀜)가
#        창 최소 폭이 됐었다 - 탭 위젯은 안 보이는 탭까지 가장 넓은 페이지에 맞추므로 Buttons 탭에서도 안 줄었다.
#        상태 줄은 끝 두 폴더 + 툴팁에 전체 경로, Rules 페이지는 스크롤 칸(좁으면 가로 스크롤바), 저작권 줄은 줄바꿈.
#        최소 폭 1494 -> 286 px (오프스크린 측정, 남은 하한은 공용 로그창의 버튼 줄).

# 01.13  Pin 버튼이 켜진(Pinned) 동안 연한 빨강 - 다른 툴과 같은 공용 Framework.qt.pin_style.

# 01.14  로그창이 접힌 채(Shrink 켜짐) 시작한다 - 버튼 줄만 보이고 `Show` 로 편다.

# 01.15  Buttons 탭 선택 버튼을 드래그로 옮긴다(A00240_PathTool v01.28 과 같은 방식) - 같은 카테고리 안 순서,
#        다른 카테고리로 이동(같은 이름이면 막음). 놓일 자리 가로줄 · 가장자리 자동 스크롤 · Esc 취소,
#        살짝 누르고 놓으면 평소 클릭(선택), 색칠 모드에서는 드래그 안 함.

# 01.16  `Add` 체크를 Create 그룹에서 버튼 모음 pane 맨 위로 - Controls 를 접거나 숨겨도 보인다.

# 01.17  공유 프로파일 · 규칙 - 로컬(data/, git 제외) + 공유(shared/, git 추적) 를 함께 보여 준다.
#        프로파일 정체 = (scope, 이름), 콤보에 `[Shared]`, Rules 탭에 Scope 열. Share(로컬 -> 공유 이동) ·
#        Copy to Local(공유 -> 로컬 복사), 공유 것의 이름 변경 · 삭제는 한 번 더 확인. New 는 로컬에.
#        공유 루트는 PC 별로 바꿀 수 있다(View > Shared Folder..., data/active.json 의 shared_dir).
#        계획서 docs/plans/A00340_SelectionTool_shared_profiles_plan.md.

# 01.18  네임스페이스 교체 - Buttons 탭 `Namespace` 콤보(+ Map... · Refresh)로 같은 리그의 다른 아바타를 고른다.
#        프로파일 json 은 그대로, 선택할 때만 {원래 ns: 대상 ns} 로 바꿔 끼운다. 후보 = 씬에서 이 프로파일 컨트롤러가
#        있는 네임스페이스(찾은 수/전체). 프로파일마다 · PC 마다 기억(active.json), 캡처는 원래 ns 로 되돌려 저장.
#        계획서 docs/plans/A00340_SelectionTool_namespace_remap_plan.md.
# 01.19  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식)

VERSION = "01.19"
LAST_UPDATE = "2026-10-29"
