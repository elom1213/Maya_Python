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

## 2026-10-02 (오늘)

> [!summary] A00330 NamingTool — **Quick Rename > Insert Position 슬라이더** (v01.23->01.24)
- 요청: Position 에 가로 슬라이더, A00110_animTool_V02 Stagger `Offset per Item` 과 같은 UI.
- [슬라이더(늘어남)] [숫자 칸 78px] + A00110 `STAGGER_SLIDER_STYLE` 같은 값. 슬라이더 <-> 숫자 칸 동기(blockSignals), 범위 = 가장 긴 이름 n -> -(n+1)..n, 범위 밖 숫자는 슬라이더를 끝에.
- 검증(mayapy 2024, arm_jnt / hand + `X`): 범위 -8..7, 슬라이더 3 / -1 / -4 / -8 -> 숫자 · 미리보기 일치, 숫자 99 -> 슬라이더 7 · `arm_jntX`, Apply = 미리보기. 창 최소 820x916 전후 같음.

> [!summary] A00330 NamingTool — **`Dnable_Set_v001` 업데이트를 배포용에 반영** (프로파일 데이터, 버전 변경 없음)
- 사용자가 개발 PC 에서 고친 프로파일: 넘버링 칸 Numbering(1, 2) -> **Custom `xx`**(나머지는 키 순서만 다름). 처음 이름 `CHN_n_SetXXX_Top_xx_geo`.
- 팀 문서 5-1 · 5-2 반대로 고침: 하나뿐이면 그대로 `xx`, 여러 개면 Numbering 으로 바꾸고 **Start 1 · Pad 0 2** (바꾼 직후는 0 · 0).
- 릴리즈에는 빌더 대신 이 두 파일만 복사 — 빌더는 개발 PC 의 다른 data(활성 · Basic)와 ref 까지 가져온다.

> [!summary] A00330 NamingTool — **`Custom` 프로파일: 배포본에서도 칸 추가 · 삭제** (v01.22->01.23)
- 요청: 특수 프로파일 Custom — 배포받은 사람도 Add / Delete Token 이 보여 토큰을 추가 · 제거.
- 프로파일 json `"free_tokens": true` 로 켠다(이름 하드코딩 대신 데이터). `TokenProfileStore.profile_flag` + `save_profile` 이 다른 키를 지키게(개발자 Save 로 표시가 사라지지 않게).
- 위젯 `tokens_addable()` = 개발 화면 or free_tokens → Add / Delete Token · 칸 머리 보임. Save / New / Rename / Delete 는 개발 화면에서만 그대로.
- 검증: 오프스크린(배포 화면 Set ↔ Custom 전환 · Add / Delete · 파일 불변 · 개발 Save 후 free_tokens 유지), mayapy 2024 임시 배포본 전체 창.

> [!summary] A00330 NamingTool — **배포 화면에서 칸 머리 Token 1~N 숨김** (v01.21->01.22)
- 요청: 배포 모드에서 Token 버튼도 없애기(칸 머리 Token 1~6 으로 확인). `TokenColumn._apply_rule_lock` 에서 header 숨김.
- 칸 줄 183 -> 145px(brown_dark), 입력칸은 여전히 y · 높이 하나. 팀 문서의 "Token 5" 안내를 화면에 보이는 칸 이름(왼쪽부터 순서 · `Start` 등)으로 바꿈.

> [!summary] A00330 NamingTool — **배포 화면에서 프로파일 Rename / Delete 도 숨김** (v01.20->01.21)
- 요청: 배포모드에서 Rename · Delete 버튼 없애기. `_apply_mode_buttons` 숨김 목록에 추가 → 배포본 Profile 줄은 콤보만.
- 검증(mayapy 2024): dev 토글 · 임시 배포본 둘 다 6버튼(Save · New · Rename · Delete · Add / Delete Token) 숨김, A00480 형태는 보임.

> [!summary] A00330 NamingTool — **배포 화면에서 Save / New 숨김** (v01.19->01.20)
- 요청: 배포모드에서 Save · New 를 없애 사용자가 규칙을 임의로 수정하지 못하게.
- 공용 위젯 `_apply_mode_buttons` 가 Add / Delete Token 과 함께 Save / New 도 숨긴다(`btn_new_profile` 보관). Rename / Delete(프로파일)는 그대로.
- 팀 문서 5-1: "Save 를 눌러야 저장" 안내 → "칸 값은 이번 Rename 에만, 공유 툴엔 Save / New 없음".
- 검증(mayapy 2024): dev 토글 끄면 4버튼 숨김 · 켜면 복원, 임시 배포본 처음부터 숨김, A00480 형태(기본값)는 보임.

> [!summary] A00330 NamingTool — **배포 화면 다른 탭 숨김 + Hierarchy 기본 꺼짐** (v01.18->01.19)
- 요청: 배포모드에선 Token 말고 다른 탭이 UI 상 존재하는 것도 안 보이게 / Hierarchy 체크 기본 해제.
- `apply_release_tabs`: 회색 잠금 → `setTabVisible`(Qt 5.15+), 없으면 removeTab / insertTab(처음 부를 때 페이지 · 제목 · 툴팁 · 자리 기억).
- 검증(mayapy 2024): setTabVisible 경로 · `hasattr` 를 막아 흉내 낸 옛 Qt 경로 둘 다 — 배포 화면 Rename / Token 만, 개발 화면 원래 순서 · 툴팁 복원, 토글 반복 OK. Hierarchy 기본 False.

> [!summary] A00330 NamingTool — **Token 탭 `Hierarchy` 체크** (v01.17->01.18)
- 요청: 체크하면 Objects 리스트 오브젝트의 자식까지, 해제하면 그 오브젝트만 rename.
- `build_hierarchy_groups(objects, hierarchy)` — False 면 [root] 만. `rename_tokens` · `preview_tokens` 가 넘겨받는다. UI 는 Rename 왼쪽 체크(기본 켜짐 = 예전 동작), 토글하면 Preview 갱신.
- 검증(mayapy 2024, 그룹 2개 · 한쪽에 자식 2개): 켜짐 → 4개 rename, 꺼짐 → 그룹 2개만 · 자식 kid0/kid1 그대로, 둘 다 미리보기 = 실제.

> [!summary] A00330 NamingTool — **배포 화면: Add/Delete Token 없음 · Token 탭만, 개발자 모드엔 `Dev Mode` 토글** (v01.16->01.17)
- 요청: 배포모드에선 Add / Delete Token 빼기, 개발자 모드엔 Dev Mode 토글로 개발 / 배포 화면을 번갈아 보기. 이어서 배포모드에선 Rename > Token 말고 다른 탭 못 쓰게.
- 공용 위젯: `mode_toggle` · `set_rules_editable()`(칸을 다시 만들되 지금 칸 · 저장 기준 유지) · 신호 `rulesEditableChanged`. 배포 화면은 Add / Delete Token 숨김.
- 메인 창 `apply_release_tabs`: Set Rename · Copy Name · Quick Rename 을 `setTabEnabled(False)` + 툴팁 안내 + Token 탭으로 이동. 테마에 잠긴 탭 모양이 없어 `QTabBar::tab:disabled` 글자만 흐리게.
- 팀 문서: 그룹 이름을 Quick Rename 으로 안내하던 5-3 절 → 배포본에선 Quick Rename 이 잠기므로 **마야에서 직접**으로 바꿈.
- 검증(mayapy 2024 전체 창): dev — 토글 끄면 탭 3개 잠김 · Token 으로 이동 · Add 숨김, 켜면 원복 / **임시 배포본**(동봉 Framework) — 토글 없음 · 탭 잠김 · Add 숨김. 칸 편집 · 미저장 상태가 토글 전후 유지.

> [!summary] A00330 NamingTool — **Preview 표 세 칸 색 구분** (v01.15->01.16)
- 요청: Current / New name / Status 칸 색을 서로 다르게.
- 칸 배경 파랑 · 보라 · 회색(반투명, 어두운 테마 alpha 70 / 밝은 50 - 같은 값이면 brown_dark 에서 거의 안 보였다), Status 글자색과 안 겹치는 계열.
- 머리글: `headerItem().setBackground` 는 테마 qss 의 section 배경에 덮여 brown_dark 에서 안 보임 → 테마가 그린 위에 덧칠하는 `TintedHeader(QHeaderView)`. 새 QHeaderView 는 stretchLastSection 이 False 라 True 로.
- 확인: brown_dark · green_light 캡처.

> [!summary] A00330 NamingTool — **Token 탭 Preview 표** (v01.14->01.15)
- 요청: Quick Rename > Insert 의 Preview 창처럼 Rename > Token 탭에서도 이름을 바꾼 결과를 미리 보게.
- core `preview_tokens`: `rename_tokens` 와 같은 순서 · 같은 이름, 행마다 Current / New name / Status(Insert 와 같은 규칙 + `token error`). `name taken` 은 부모별 이름 칸을 씬대로 채우고 rename 순서대로 바꾸는 흉내로 판정.
- UI: Objects | Preview(QSplitter, 계층 트리), 리스트 · 토큰 변경 시 150ms 모아 갱신. 창 최소 크기 전후 820x916.
- 덤으로 고친 것: 잠긴 노드에서 Rename 이 `RuntimeError` 로 멈추던 것 → 건너뛰고 [Warning] / Rename 뒤 리스트를 새 이름으로.
- 검증(mayapy 2024): 큐브 3 + 단독 → 01~04 OK / 그룹 → 트리 + 월드 동명 `name taken` / `Set-8` → token error / 잠긴 노드 locked, Rename 후 미리보기 = 실제 이름, 잠긴 노드만 건너뜀.

> [!summary] A00330 NamingTool — **배포본에선 Enum 규칙 잠금, `Values...` 는 개발자 모드만** (v01.13->01.14)
- 요청: Enum 칸의 `Values...`(칸 이름 · 값 목록 편집)는 개발자 모드에서만, 배포용 툴에서는 없애서 공유받은 사람이 규칙을 못 바꾸게.
- 판정 `app/config/dev_mode.py` — launch.py 와 같은 규칙(툴 폴더에 Framework 동봉 = 배포본 → False, 아니면 `JUN_All/config.py` DEV_MODE 를 **경로로** 읽음).
- 공용 위젯 `rules_editable`(기본 True): False 면 `Values...` 숨김 · Enum 칸 규칙 콤보 잠금(Custom 으로 바꿔 우회 차단) · Enum 칸 Delete Token 막음 · 다른 칸 콤보에서 Enum 제외. 값 고르기 · Save 등은 그대로. A00480 은 기본값이라 불변.
- 검증: dev 트리 `dev True`, **릴리즈 빌더로 임시 폴더에 만든 배포본**(dev 경로 sys.path 제거, 동봉 Framework 로딩 확인) `IS_RELEASE True dev False` → Values 4칸 숨김 · 콤보 잠김 · Enum 삭제 [WARN] · 값 고르기 정상. 팀 문서 5장 갱신(규칙은 관리자만).

> [!summary] A00330 NamingTool — **Token 칸 입력칸 높이 · 위치 통일** (v01.12->01.13)
- 요청(`ref/ref_02.png`): CHN · n 과 SetXXX, Top 과 Numbering `1` 의 입력칸 높이가 다르다 — 같게.
- 원인 둘: Enum 값 콤보는 80px 에 글자를 넣으려 padding 을 줄여 낮았다 / Custom 페이지엔 이름 줄이 없어 입력칸이 한 줄 위에 붙었다. 고치는 중 하나 더 — Numbering 페이지엔 stretch 가 없어 남는 높이가 이름 줄로 나뉘어 입력칸이 6px 내려갔다.
- 수정(공용 `MOD_tokenName_qt_v01`): 모든 페이지 = 이름 줄(`Text` / role / `Start` / `Set`) -> 입력칸 -> stretch. `_match_input_heights` 가 입력칸 5종을 테마 입힌 QLineEdit / QSpinBox 중 큰 높이로 고정(Polish · StyleChange · Show).
- 실측: brown_dark · green_light 6칸 y 83 · 높이 32 전부 같음, dark 높이 26 같음(페이지 안 y 17 동일). A00480 칸 줄 높이 전후 163px.

> [!summary] A00030 QuickTool V02 — **`Print Hierarchy` -> `Copy Hierarchy`** (v02.03->02.04)
- 요청: 버튼 이름을 Copy Hierarchy 로, 로그 출력은 그대로 두고 계층 트리를 클립보드에도 복사.
- 수정: 버튼 표 라벨 · 핸들러 `on_copy_hierarchy` — 트리를 로그에 찍은 뒤 같은 텍스트를 `QApplication.clipboard()` 로(Copy Scene Folder 와 같은 방식), 코어 로그 문구 `Copy Hierarchy : n node(s).`, About · 가이드 문서 갱신.
- 검증(mayapy 2024 + 오프스크린): 라벨 교체 · 조인트 3단 트리 로그 그대로 · 클립보드 = 로그 트리 · 선택 없으면 경고만.

> [!summary] A00330 NamingTool — **Token `Enum` 규칙 + 팀 이름 규칙 문서** (v01.11->01.12)
- 요청: SetXXX 오브젝트 이름 규칙(`{캐릭터}_{좌우}_{세트}_{파츠}_{넘버링}_{오브젝트종류}`)을 팀에 공유할 문서 + `Dnable_Set_v001` 의 캐릭터 · 좌우 · 파츠 · 오브젝트종류를 타이핑 대신 정해진 값에서 고르게. A00470 이름 규칙 json 참고.
- 공용 `token_naming` 에 `RULE_ENUM` — `{"rule": "enum", "role", "values", "value"}`(키는 A00470 `{"type": "enum", "role", "values"}` 와 같게). 목록 밖 value 는 첫 값, 빈 목록은 검사에서 막음, 값도 마야 글자 검사. `MAYA_NODE_RULES` 에만 추가 → A00480 규칙 목록 불변.
- 위젯: Enum 칸 = 칸 이름(role) · 값 콤보 · `Values...`(칸 이름 + 쉼표 값 목록). 칸 높이 불변(Numbering 4줄이 정함), 80px 에 `Accessory` 들어감.
- 프로파일 `Dnable_Set_v001`: CHN/DHA/LUN/SIN/TBM · n/l/r · Top/Pants/Shoes/Accessory · geo/grp. **이 파일은 개발 저장소에선 `.gitignore`(data/) — 이 PC 와 릴리즈 저장소에만 있다.**
- 문서 `docs/A00330_NamingRule_Set.md`(팀 공유): 규칙 표 · 그룹은 파츠 생략 · 예시 1~3 · 자주 틀리는 것 · 툴 사용법. Token 탭은 transform 자손까지 바꾸므로 **그룹은 Quick Rename Change New(선택 1개 + Start 비움 = 이름 그대로)** 로 안내(코드 확인).
- 검증: 오프스크린(검사 · 미리보기 · Values... · Save 왕복), **mayapy 2024 rename** — `SIN_n_Set008_Accessory_01~03_geo`, `SIN_l_Set008_Shoes_xx_geo`.
- 릴리즈: release_builder 로직으로 A00330 만 다시 복사 → 릴리즈 저장소 변경 8개 파일(문서 2 포함), 로컬 커밋.

> [!summary] A00240 PathTool — **버튼 색 지정** (A00340 색 기능 이식, v01.14->01.15)
- 요청: A00340_SelectionTool 처럼 경로 버튼마다 색을 정할 수 있게 — A00340 기능을 그대로 옮겨도 된다.
- 이식: 버튼 우클릭 `Set Color...`(QColorDialog = 팔레트 + Pick Screen Color 스포이드) / `Reset Color`, `Color` 그룹 `Color Select` 모드(체크형 버튼으로 카테고리를 넘나들며 체크 → `Apply...` / `Clear`, 켜진 동안 클릭은 경로를 안 연다), 글자색 흑/백 자동, 버튼 dict 에 `"color"` 저장. 체크 상태는 위젯의 실제 `isChecked()` 로 다시 맞춘 뒤 적용(A00340 v01.03 안전장치 그대로).
- 다른 점: 색 버튼 여백을 테마 값 `padding 8px · radius 4px` 로 — A00340 값(4px · 3px)이면 색 버튼이 기본 버튼보다 낮다(실측 후 34px 로 같음). 라벨 `Apply Color...`/`Clear Color` -> `Apply...`/`Clear` — 그대로면 Color 그룹(오프스크린 534px)이 Profile 그룹(468px)보다 넓어 창 최소 폭이 는다(줄인 뒤 390px).
- 검증(오프스크린, 임시 프로파일 폴더 — 실제 data/ 불변): 개별 지정 · 평소 클릭 = 경로 열기 · 모드 중 클릭 = 체크만(열기 0) · C1/C2 걸친 체크 → Apply 한 색 · 체크 유지 · Clear · 모드 끄면 다시 열기 · Reset.

## 2026-10-01

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
