# Python Script by Ji Hun Park
# last Update date : 2026-10-26
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

VERSION = "01.14"
LAST_UPDATE = "2026-10-27"
