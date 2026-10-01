---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-10-01
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

**이 파일은 현재 월을 담는다.** 지난 달은 [`worklog/`](worklog/) 로 내려간다 —
파일 자체는 늘 이 경로에 있으므로 이 문서를 가리키는 링크는 깨지지 않는다.
트리거와 절차는 [`worklog/README.md`](worklog/README.md).

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 지난 달 보관

| 월 | 파일 | 작업일 |
|----|------|--------|
| 2026-09 | [`worklog/2026-09.md`](worklog/2026-09.md) | 16일 |
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-10-01 (오늘)

> [!summary] A00490 KeyboardTool — **체크한 크롬 창 전부에 키가 가게** (v01.00->01.01)
- 문제(사용자 확인): 크롬 창 2개를 체크하면 **클릭한 창만** 동작. 재현: 비활성 크롬은 PostMessage 를 무시 — 안쪽 `Chrome_RenderWidgetHostHWND` 로 보내도 무시. 가짜 `WM_ACTIVATE` 는 테스트 크롬이 꺼진 적이 있어 기각.
- 수정: Send Method **Auto**(기본) = 크롬 계열(`Chrome_WidgetWin_*`)은 Foreground, 나머지 Background. Foreground 는 창을 차례로 앞으로 가져오고 **그 창이 키를 읽을 때까지 대기** — 대상 스레드에 AttachThreadInput 후 `GetKeyState` 가 눌림/떼짐을 보일 때까지(크롬 창들은 UI 스레드 하나라 바로 넘어가면 키가 다음 창으로 샌다).
- 실측(크롬 3창 × 20): 대기 0 = 25ms/바퀴 · 1/1/25(샘) · 고정 30ms = 106ms · **읽기 대기 = 32ms · 20/20/20**. Interval 은 바퀴 시작 간격으로.
- 검증(UI, Auto, 크롬 3 + Qt 1, Loop 2): 크롬 각 30 · Qt 30 · 6.47초 · 포커스 복귀. 문서 4장 · 8장 갱신.

> [!summary] A00490 KeyboardTool — **신규: 키 시퀀스 자동 입력 + 대상 창 지정** (v01.00)
- 요청: 키 여러 개를 키마다 횟수 · 간격으로 누르기(예 Down 10 · Up 10, 1초) + 루프 + **고른 창에만**(크롬 A, B 만, C 는 그대로). Windows 10 · 11 둘 다. 아이콘 포함.
- 구조: standalone PySide6(A00240 배치). core = `keys`(이름 <-> VK, `Ctrl+C` 파싱) · `win32`(ctypes 창 열거 / PostMessage / SendInput / activate) · `runner`(스레드, Stop 이벤트 + F9 감시) · `presets`(data/presets). UI = 시퀀스 표(키 캡처 칸) · 대상 창 체크 목록(공용 checkList) · Run · 공용 로그.
- 전송 방식 2개: **Background**(PostMessage, 포커스 유지, 여러 창 동시 · 조합키는 안 먹음) / **Foreground**(AttachThreadInput 으로 앞으로 + SendInput, 끝나면 원래 창 복귀).
- Win10/11: Vista~ 고정 user32 API 만, DWM cloaked 로 숨은 UWP 창 제외, 64bit `INPUT` 40바이트 맞춤.
- 검증(별도 프로세스 수신 창 A/B/C): Background · Foreground 둘 다 A · B 만 받고 C 0건, Foreground 는 Ctrl 수식키 포함 + 포커스 복귀, Stop · F9 · 대상 창 닫힘 처리. **실제 크롬은 미확인.**
- 문서: [A00490_KeyboardTool.md](A00490_KeyboardTool.md).

> [!summary] A00210 FileManager Path Structure — **Preview 트리 맨 위를 `.` 로** (v01.33->01.34)
- 요청: Base Folder `A`(아래 `B/B_01` · `B/B_02` · `C`)를 Capture · Save 하면 트리 맨 위에 `A` 가 보인다. 재생성 때 `A` 가 새로 생긴다고 오해하므로 `.` 아래에 `B` · `C` 가 보이게.
- 사실관계: 저장 내용(`folders = B, B/B_01, B/B_02, C`)과 재생성(Recreate To 바로 안)은 이미 `A` 를 만들지 않았다 — **표시만** 원본 이름이었다(`build_structure_tree` 의 루트 이름).
- 수정: 루트 이름 = `ROOT_LABEL "."`, 루트 툴팁 = `'.' = the Recreate To folder itself ...` + `Captured from: <원본>`. Expand 창 제목은 원본 경로 대신 구조 이름(`(not saved)`).
- 검증(오프스크린, 임시 A/B/C): Capture 직후 · Save 후 목록 선택 둘 다 `. > B > B_01, B_02 / C` · JSON folders 그대로 · Recreate To 에 `B, B/B_01, B/B_02, C` 만 생성(`A` 없음).

> [!summary] A00210 FileManager Path Structure — **Capture 가 Project Root 와 무관하게 어느 경로에서든** (v01.32->01.33)
- 요청: Base Folder 를 채우고 Capture 하면 File Manager 탭 Project Root 하위 경로만 되고 그 위 경로는 안 된다. 제약을 없애 원하는 어느 경로든 캡처되게.
- 원인: `capture()` 가 베이스를 `store.make_key()`(루트 기준 키)로만 저장해서, 루트 밖이면 `OutsideProjectRootError` → `Base folder is outside the project root`, 루트가 비면 탭이 `Set Project Root first` 로 막았다. 다른 드라이브면 `relpath` 가 `ValueError` 를 던져 잡히지도 않았다.
- 수정: JSON 에 캡처한 절대경로 `base_path` 를 늘 기록하고, `base_rel` 은 루트 안일 때만 채운다(`base_rel_in_root` — 루트 없음 · 밖 · 다른 드라이브 모두 "", 루트 자신은 예전처럼 "."). 탭의 두 경고 삭제. Preview 의 실제 폴더는 `project_root/base_rel` 우선, 없으면 `base_path`. 트리 루트 이름 · Expand 창 제목은 `base_label()`. 재생성은 v01.32 부터 `Recreate To` 만 쓰므로 그대로.
- 검증(오프스크린, 임시 폴더): 루트 안 / 루트 자신 / 루트 밖 / 루트 비움 / store 없음 / 다른 드라이브 캡처 · 실제 탭에서 루트 비움 · 루트 밖 Base 로 Capture → Save 경고 0, `base_path` 저장, 트리 루트 = `Asset` · 그 구조를 Recreate To 로 재생성 · 구버전 JSON 로드.

> [!summary] A00480 FileTool · A00330 NamingTool — **토큰 칸을 고쳐도 프로파일에 저장 안 함, `Save` 버튼으로만** (A00480 v01.07->01.08 · A00330 v01.10->01.11)
- 요청: A00480 Naming 에서 프로파일을 골라 칸에 글자를 넣고 툴을 닫았다 열면 고친 칸이 그 프로파일의 기본이 돼 있다(알림 없이). 버튼을 눌렀을 때만 기본이 되게, 누르지 않으면 어떤 프로파일도 바뀌지 않게.
- 원인: 공용 위젯 `Framework/qt/MOD_tokenName_qt_v01.py` 의 `_after_edit()` 가 칸이 바뀔 때마다 `store.save_profile()` 을 불렀다.
- 수정(공용 위젯 — **A00330 Token 탭도 같이 바뀐다**): 자동 저장 제거, Profile 줄 콤보 오른쪽에 **`Save`** (`save_profile()`). 로드 직후 `tokens()` 를 기준으로 잡아 `is_dirty()` — 저장 안 한 변경이 있을 때만 Save 가 켜지고, 고쳤다 되돌리면 꺼진다. 저장 안 한 칸은 프로파일 전환(`[WARN] ... unsaved edits ... were dropped.`) · 창 닫기 때 버려진다. `New` 는 지금 칸을 새 프로파일에 저장(떠나온 프로파일은 그대로).
- 검증(오프스크린 PySide6, 임시 data): 편집 → 위젯 다시 만들기 = 원래 6칸(SK_MANU_CH_Name_Basic_Version) · Save 후 다시 만들기 = 고친 칸 · 되돌리면 dirty False · New 후 편집 → 전환 시 WARN.
- 창 폭: Save 버튼만큼 A00480 창 최소 폭 882 → 954px (mayapy 2024 오프스크린 slate_dark). 원래 맞춘 960 안. 마야 GUI 확인 전.

> [!summary] A00240 PathTool — **Change Profile: 카테고리를 버튼째 다른 프로파일로 이동** (v01.13->01.14)
- 요청: Category 버튼으로 만든 카테고리를 좌클릭하면 `Change Profile` 이 나오고, 고른 프로파일로 그 카테고리와 안의 버튼 전부가 옮겨지게.
- 구현: 카테고리 박스를 좌클릭 콜백을 받는 `_CategoryBox(QGroupBox)` 로 바꿨다(Framework Qt 바인딩에 `Signal` 이 없어 콜백). Path 버튼은 자기 클릭을 소비하므로 **헤더 · 버튼 사이 빈 곳**을 누를 때만 메뉴가 뜨고, 버튼 클릭은 그대로 경로 열기. 같은 항목을 우클릭 메뉴에도 넣었다.
- 이동 로직은 core `prefs.move_category(src, dst, name)` (UI 비의존). 대상에 같은 이름 카테고리가 있으면 **끝에 합치고**, 버튼 이름이 겹치면 **아무것도 안 옮기고** 겹친 이름을 알린다. 저장은 **대상 → 현재** 순(중간 실패 시 사라지지 않고 양쪽에 남게).
- 검증(오프스크린 PySide6, 임시 data 폴더): 좌클릭 메뉴 = `['Change Profile']` · 버튼 클릭은 경로 열기만 · 새 카테고리 이동 · 이름 충돌 시 무변경 + 경고 · 같은 이름 카테고리에 합치기 · 활성 프로파일 유지.
