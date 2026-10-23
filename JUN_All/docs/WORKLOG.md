---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-10-23
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

## 2026-10-23 (오늘)

> [!summary] JALI 대량 파이프라인 — **계획 평가 + A00560_JaliBatch · A00570_JaliReview 제작 계획서** (코드 전, 문서만) `#A00560_JaliBatch` `#A00570_JaliReview` `#JALI`
- 요청: wav · 대본 N 개 → JALI 툴(JUN_JALI 변환기) → JALI 컨트롤러(`A0030_jali_slider_ctl_direct_arkit.ma`) 레퍼런스 + DUMMY_IN 키 → 컨트롤러 베이크한 클립 `.mb` N 개를 만드는 standalone 툴, 검수는 빈 씬에 클립 + 아바타를 레퍼런스하고 ARKIT_OUT → 블렌드셰이프 연결, 레퍼런스 교체로 다른 클립 — 이 계획을 평가하고 개선안과 제작 계획서를 문서로.
- `docs/plans/A00560_JaliBatch_pipeline_review.md`: 뼈대(클립 = 컨트롤러 레퍼런스 + 자기 animCurve, 레퍼런스 교체 검수, 변환 · 마야 프로세스 분리)는 유지. **틀어진 곳 둘** — ① 레퍼런스된 animCurve 편집은 검수 씬의 레퍼런스 편집으로 쌓여 클립 `.mb` 가 Ctrl+S 로 안 바뀐다 → `file -saveReference`(Save Reference Edits) 를 명시 버튼으로 ② 편집은 노드 이름으로 기록되고 모든 클립이 같은 이름이라 저장 안 한 채 교체하면 다음 클립에 묻어 간다 → Swap 앞 편집 0건 검사. 더한 것: Validate(failedEdits · 도장) · 네임스페이스 고정(`CLIP:JALI:`) · 시작 프레임 = 파일 이름 `_f0105_0429`(30fps 원본 구간, wav 길이와 일치) · fps 명시 · 매니페스트 json · 베이크 뒤 DUMMY_IN 커브 삭제 · 덮어쓰기 정책 · 변환은 2단계 · Open Clip 대안.
- `docs/plans/A00560_JaliBatch_plan.md`: P0 공용 승격(`Framework/jali/` ← A00540 코어 · `mayapy_runner`/`MOD_mayapyProcess` ← A00210 · `bake.py` ← JUN_JALI `bake_ctl_keys`) → P1 `A00560_JaliBatch` standalone(Batch · Validate, mayapy 워커 한 프로세스) → P3 `A00570_JaliReview` in-Maya(Swap · Save Clip Edits · Connect) → P4 변환기 CLI. 결정 D1~D14, **M0 실측 8항목**(optionVar 이름 · 편집 문장 · saveReference 되읽기 · 교체 시 편집 전파 · 레퍼런스 사운드 · 클립 왕복 · 컨트롤러 갱신 · 시간) 을 코드 전에 확정, 단계 M0~M7, 검증 T1~T9, 질문 Q1~Q8(권장안 포함). 사용자 요청으로 A00540 코어를 그대로 쓰는 쪽으로 설계.

> [!summary] A00240_PathTool — **Path 버튼 드래그로 자리 옮기기 + 창 크기 자유롭게 + 버튼이 창 폭을 따라 말줄임** (v01.27->01.28->01.29->01.30) `#A00240_PathTool`
- 요청: (1) 생성된 버튼의 위치를 마우스 클릭 · 홀드 · 이동 · 해제로 바꾸고 싶다 → 진단 후 "버튼 서브클래스에서 마우스 이벤트만으로" 로 확정. (2) 일정 가로 아래로 창이 줄지 않는다 → 진단: `QTabWidget` 최소 = 숨은 탭 포함 최댓값, Junction 탭(TSL 둘 나란히 978) 이 바닥 → 탭을 QScrollArea 에.
- v01.28 `shortcut_tab.py`: `_PathButton(QPushButton)` — press 에 전역 좌표 기억, move 가 `startDragDistance` 넘으면 `begin_drag`, 이후 `update_drag`(가로줄 `_drop_line` + 가장자리 자동 스크롤 40ms 틱), release 는 `end_drag`(super 안 불러 clicked 안 나감), Esc 는 `cancel_drag` + 다음 release 삼킴. 자리 계산 `_drop_target_at` = 커서 y 를 품는 카테고리 박스(없으면 가장 가까운) + 가운데 y 가 위인 버튼 수. `_drop_button` 은 같은 카테고리면 pop/insert(인덱스 보정), 다른 카테고리면 Change Category 와 같은 이름 충돌 규칙. 버튼은 `(cat_index, btn_index)` 키 — 같은 이름 둘이어도 안전. 색칠 모드는 `drag_enabled=False`.
- v01.29 `main_window.py`: `tabs_scroll`(NoFrame) + `showEvent` 1회 `fit_to_content`(A00210 v01.36 과 동일 — 탭 최소 + 헤더, 모니터 작업 영역까지), Shrink 는 `tabs_scroll` 을 감춘다.
- 검증(오프스크린 PySide6 42항목, 스크래치 프로파일로 실데이터 안 건드림): 창 최소 가로 1004 → 172, `resize(300,400)`·`(250,300)` 먹음, 여는 크기 화면 안, Shrink 272x155 · 복원 / 클릭 vs 드래그, 아래 · 위 이동, 제자리 놓기 무변화, 카테고리 간 이동, 이름 충돌 경고, Esc 취소 + 놓음 삼킴 + 다음 클릭 정상, 색칠 모드 드래그 없음, 자동 스크롤, JSON 저장. **실기 눈 확인 아직.**
- 문서 `docs/A00240_PathTool.md` "창 크기" · "5-2 드래그" 절, CHANGELOG 01.28 · 01.29, version, 메모리 `wip-a00240-drag-reorder` 신규 + `qtabwidget-min-size-hidden-pages` 사용처.
- **v01.30 (같은 날, 후속 요청)** — "창을 줄이면 버튼도 함께 줄고 글자가 안 잘리게". 원인 둘: (1) v01.29 의 바깥 스크롤 칸 하나가 탭 위젯을 가장 넓은 페이지 폭(Junction 982)으로 유지해 ShortCut 페이지가 좁아지지 않았다 → **페이지마다** `QScrollArea`(`_wrap_page`, `fit_to_content` 는 `_pages_min_size` 로 페이지 최소의 축별 최댓값). (2) QPushButton 최소 폭 = 글자 폭 → `_ElideButton`: `setMinimumWidth(40)`(Qt 는 명시 최소가 있으면 minimumSizeHint 를 안 쓴다) + `resizeEvent` 에서 `elidedText`, 전체 이름은 `full_text` · 툴팁 첫 줄. 함정 둘: 말줄임된 글자로 힌트를 재면 되먹임으로 한 행이 고르지 않게 줄어 **전체 라벨 기준 힌트를 캐시**(`_refresh_hints`, 생성 · setText · StyleChange/FontChange 때만 — sizeHint 안에서 setText 금지), 라벨 여백은 상수(24) 대신 **힌트 폭 − 글자 폭**으로 잰다(Category 는 18 이라 상수로는 힌트 폭 그대로인 버튼도 말줄임됐다). `_PathButton` 은 `_ElideButton` 상속, Profile · Create · Color 행 버튼 7개도 교체, 콤보 `AdjustToMinimumContentsLengthWithIcon(4)`. ShortCut 페이지 바닥 410 → 296(offscreen, Color 행).
- 검증(오프스크린 21항목 + 42항목 회귀): 넓을 때 전체 라벨 · 좁을 때 말줄임 + 툴팁 · 글자가 버튼 안에 · 페이지 폭이 창을 따름 · 눌린 행은 고르게 줄고 stretch 있는 행은 전체 라벨 · 힌트 안정 · 드래그 정렬 유지. **실기 눈 확인 아직.**

> [!summary] A00210_FileManager — **Pinned 동안 Pin 버튼 연한 빨강 + File > Add to Start Menu** (v01.38->01.39) `#A00210_FileManager`
- 요청(두 턴): A00240 처럼 A00210 도 (1) Pin 이 켜져 있을 때 버튼을 빨강으로, (2) 시작 메뉴 바로가기 추가 기능.
- Pin 색: `main_window.py` Pin 생성 직후 공용 `Framework/qt/pin_style.apply_pin_style` 한 줄. 색 · 크기 규칙은 세 툴과 같다(`:checked` 색만, padding 없음).
- Start Menu: `app_meta.py` 에 `APP_NAME`(JUN File Manager) · `APP_DESCRIPTION` · `tool_root()` · `start_menu_launch_spec()`, `main_window.py` 에 `File` 메뉴(공용 메뉴 바라 Help 왼쪽) + `Add to Start Menu` → 공용 `shell_integration.add_to_start_menu` · `pin_shortcut` → 하단 로그 한 줄 + 안내/경고 창. A00240 의 핸들러와 같은 꼴(로그만 이 창의 `self.log`).
- 검증(15항목): offscreen PySide6 실제 창 — Pin 바탕 픽셀 꺼짐 = 테마 색 · 켜짐 = `#f2a0a0` · 72 x 28 유지, File 메뉴가 Help 왼쪽에 있고 액션 enabled, `start_menu_launch_spec()` 이 pythonw + launch.py + .ico 를 가리킴. **실기 확인(사용자, 같은 날)**: Pin 색이 바뀌고 시작 메뉴 바로가기도 생긴다.
- 문서 `docs/A00210_FileManager.md` Pin 줄 + "File > Add to Start Menu" 소절, `docs/Framework_pin_style.md` · `docs/Framework_shell_integration.md` 사용처, CHANGELOG, version.

> [!summary] A00240_PathTool · A00220_BackupTool · A00370_ToolLauncher — **Pinned 동안 Pin 버튼 연한 빨강** (A00240 v01.25->01.26 · A00220 v01.20->01.21 · A00370 v01.12->01.13) + 공용 `Framework/qt/pin_style.py` `#A00240_PathTool` `#A00220_BackupTool` `#A00370_ToolLauncher` `#Framework`
- 요청: 세 툴의 `Pin` 이 켜져(`Pinned`) 있을 때 버튼을 연한 빨강으로 바꿔 핀 상태가 보이게.
- 공용 `Framework/qt/pin_style.py` — `apply_pin_style(button)` 이 `QPushButton:checked`(+hover/pressed) 색만 적은 qss 를 버튼에 붙인다(바탕 `#f2a0a0` · 글자 `#4a1414`). padding 을 안 적어 버튼 크기 · 테마 모양은 그대로. 세 툴은 Pin 생성 직후 한 줄.
- 검증: offscreen 에서 A00240(yellow_mid) · A00220(green_mid) 실제 창과 A00370 과 같은 테마의 버튼을 그려 가운데 픽셀 — 꺼짐 = 테마 색, 켜짐 = 연한 빨강. 마야 · 실기 확인 아직. A00210_FileManager 의 Pin(v01.37)은 요청에 없어 그대로.
- 문서 `docs/Framework_pin_style.md` 신규, 세 툴 가이드 · CHANGELOG · docs/README 색인.

> [!summary] A00370_ToolLauncher · A00240_PathTool — **줄어든 채 Pin 을 누르면 애니메이션이 멈추던 것 수정** (A00370 v01.13->01.14 · A00240 v01.26->01.27) `#A00370_ToolLauncher` `#A00240_PathTool`
- A00210 애니메이션 테스트에서 발견: Pin 토글은 창 플래그를 바꾸며 창을 숨겼다 다시 보이는데, 애니메이션 위젯의 `hideEvent` 가 타이머를 세워 버려 그 뒤로 멈춰 있었다. 세 위젯(`rocket_anim` · `file_tree_anim` · `folder_anim`) 모두 `hideEvent` 에서 돌던 중이었는지 `_resume` 에 기억하고 `showEvent` 에서 잇는다. 명시 `stop()`(Shrink 끔)은 `_resume=False`.
- 검증: 세 툴 오프스크린 테스트에 "Pin 중 애니메이션 계속" 항목 추가(A00370 32 · A00240/A00220 35 · A00210 25 전부 통과).

> [!summary] A00210_FileManager — **줄었을 때 폴더 · 기록 카드 애니메이션** (v01.37->01.38) `#A00210_FileManager`
- 확정(사용자): 제안 4안 중 **1번(아이콘 모티프)**.
- `app/ui/folder_anim.py` `FolderAnimWidget`(신규, A00370 `RocketAnimWidget` 과 같은 꼴): 30x32 칸 비트맵 — 폴더 뒷판 · 탭 / 기록 카드(테마 글자색, 썸네일 · 제목 · 작업자 · 로그 2줄은 아이콘 파랑) / 폴더 앞판 / 9x9 동기화 뱃지(링 24칸 위를 8칸짜리 호 둘이 2칸씩 12프레임에 한 바퀴). 한 바퀴 3.0초 — 올라옴 0.5(ease-out) → 채움 3단계(0.3초 간격) → 동기화 0.8 → 내려감 0.5(ease-in) → 쉼 0.3. 켤 때마다 처음부터, 끄면 정지, 상태(카드 높이 · 채움 수 · 뱃지 프레임)가 바뀔 때만 update.
- `main_window.py`: 빈 `QWidget` 자리를 `FolderAnimWidget` 으로, Shrink 켤 때 `start()` · 끌 때 `stop()`.
- 검증(오프스크린 PySide6, 27항목): 단계 · 카드 높이 단조 · 채움 단계 · 뱃지 한 바퀴(12프레임) · 루프 되감기 + v01.37 Shrink/Pin 회귀 + 시각별 캡처 6장 눈 확인. 실제 앱 눈 확인은 아직.

> [!summary] A00210_FileManager — **Shrink · Pin 추가** (v01.36->01.37) `#A00210_FileManager`
- 요청: A00210 에도 Shrink · Pin 기능 추가 + 줄었을 때 반복 애니메이션 아이디어 제시(제시만, 구현은 아직).
- `main_window.py`: 탭 위 헤더 행(A00240 과 같은 모양) — `Pin`(WindowStaysOnTopHint, show() 재호출) · `Shrink`(메뉴 바 · `tabs_scroll` · 로그 `hide()` → `invalidate/activate` → **272 x 155**, Pin 은 `button_grid` (0,1) ↔ (1,0)). 복원은 `_full_size`. 버튼 왼쪽 `anim_area` 는 빈 `QWidget`(Expanding) — 애니메이션 정하면 바꿔 끼운다. `fit_to_content` 는 첫 show 에만 돌아 Pin 의 show() 와 충돌 없음.
- 검증(오프스크린 PySide6, 15항목): 버튼 자리 · 크기, 감춘 위젯, 272x155, Pin 이 Shrunk 아래, 복원 크기 · 자리, 반복 토글, Shrink 중 Pin + 캡처. 실제 앱 눈 확인은 아직.
- 문서 `docs/A00210_FileManager.md` "Shrink · Pin" 절, CHANGELOG, version.

> [!summary] A00240_PathTool · A00220_BackupTool — **줄었을 때 Pin 을 Shrunk 아래로, 창 272 x 155** (A00240 v01.24->01.25 · A00220 v01.19->01.20) `#A00240_PathTool` `#A00220_BackupTool`
- 요청: A00370 v01.12 와 똑같이 두 툴도 줄었을 때 가로를 줄일 것.
- 둘 다 버튼 둘을 `QGridLayout`(`button_grid`)에 두고 Shrink 토글에서 `Pin` 만 (0,1) ↔ (1,0) 으로 옮긴다. `SHRINK_WIDTH` 350 → **272**. A00220 은 공룡을 헤더 행 아래(root index 1)가 아니라 **헤더 행 왼쪽(index 0)** 으로 옮겨 세로 155 를 유지, `_full_height` → `_full_size`(가로도 복원). 세 툴(A00220 · A00240 · A00370)이 줄었을 때 같은 모양 · 같은 크기.
- 검증(오프스크린 PySide6, 34항목 + A00370 회귀 32항목): 두 툴 모두 272x155, Pin 이 Shrunk 아래, 빈 열 없음, 복원 크기 · 자리, 공룡 행 이동 · 복귀, 파일 트리 애니메이션 유지, 반복 토글 + 캡처. 실제 앱 눈 확인은 아직.
- 문서 `docs/A00240_PathTool.md` · `docs/A00220_BackupTool.md` Shrink 절, 두 CHANGELOG · version.

> [!summary] A00240_PathTool · A00220_BackupTool — **File > Add to Start Menu: 시작 메뉴 바로가기** (A00240 v01.23->01.24 · A00220 v01.18->01.19) + 공용 `Framework/core/shell_integration.py` `#A00240_PathTool` `#A00220_BackupTool` `#Framework`
- 요청: 두 standalone 툴에 JUN Video Tool(0110) 과 같은 "시작화면 바로가기 추가" 기능. **Windows 10 에서도 동작할 것.**
- 공용 모듈 `Framework/core/shell_integration.py`(Qt · Maya 비의존): 비디오툴 `app/core/shell_integration.py` 이식(타입 힌트 제거). `launch_spec`(dev = pythonw + launch.py / frozen = exe) · `create_shortcut`(PowerShell `Add-Type` C# → IShellLinkW + IPropertyStore 로 .lnk + **AppUserModelID**) · `add_to_start_menu` · `pin_shortcut("start")` · `start_menu_message`. Win10/11 공통 재료만 쓴다(PowerShell 5.1 · COM · `%APPDATA%`). PS 출력 UTF-8 지정 + cp949 폴백(비디오툴엔 없던 것 — 한국어 오류가 깨졌다).
- 툴: `app_meta.py` 에 `APP_NAME` · `APP_DESCRIPTION` · `tool_root()` · `start_menu_launch_spec()`. 메인 창에 `File` 메뉴(공용 메뉴 바라 Help 왼쪽) + `Add to Start Menu` → 만들고 고정 시도 → 로그 한 줄(A00240 은 Junction 탭 Log) + 안내 창(수동 고정 방법, 폴더 옮기면 다시 누르기).
- 검증: 실제 .lnk 생성(스크래치, WScript 되읽기 · AUMID 되읽기 · 덮어쓰기 · 오류) + 두 창 offscreen 배선 테스트 24항목. **두 툴에서의 실기 클릭 · Win10 실기는 아직.** 문서 `docs/Framework_shell_integration.md` 신규, 두 툴 가이드 · CHANGELOG · docs/README 색인.

> [!summary] A00370_ToolLauncher — **줄었을 때 Pin 을 Shrunk 아래로, 창 272 x 155** (v01.11->01.12) `#A00370_ToolLauncher`
- 요청: 줄어든 뒤 `Shrunk` 버튼 밑에 `Pin` 이 오게 하고, 원래 `Pin` 이 차지하던 가로 칸을 없애 줄었을 때 가로를 줄일 것.
- `main_window.py`: 버튼 둘을 `QGridLayout`(`button_grid`)에 두고 Shrink 토글에서 `Pin` 만 (0,1) ↔ (1,0) 으로 옮긴다(removeWidget → addWidget). `SHRINK_WIDTH` 350 → **272**(Pin 칸 72 + 간격 6). 로켓 영역(166 x 133) · 세로는 그대로.
- 검증(오프스크린 PySide6, 32항목): 줄었을 때 Pin 이 Shrunk 와 같은 x · 아래, Shrunk 가 오른쪽 끝(빈 열 없음), 복원 시 한 줄로 복귀 + 캡처. 마야 GUI 미확인.

> [!summary] A00370_ToolLauncher — **Shrink + 줄었을 때 로켓 발사 애니메이션** (v01.10->01.11) `#A00370_ToolLauncher`
- 요청: A00220_BackupTool 처럼 Shrink 를 만들고, 줄었을 때 이 툴 아이콘의 로켓이 위로 발사되는 애니메이션을 무한 반복.
- `main_window.py`: `Pin` 왼쪽 체크형 `Shrink`(72x28). 메뉴 바 · 런처 영역 · 저작권 줄을 `hide()` → `invalidate/activate` → **350 x 155**(A00220 · A00240 과 같은 크기). 끄면 줄이기 전 크기로. 화면만 감추므로 프로파일 · 로그 유지.
- `app/ui/rocket_anim.py` `RocketAnimWidget`(신규): 코드 비트맵 로켓 11x14(몸체 = 테마 글자색, 창문 · 날개 · 불꽃 = 아이콘 코랄). 한 바퀴 2.4초 — 점화 0.6초(불꽃 깜빡임 + 떨림) → 상승 1.2초(ease-in, 연기 점 꼬리) → 빈 하늘 0.6초 → 반복. 켤 때마다 처음부터, 끄면 정지, 모습이 바뀔 때만 다시 그린다. A00240 `FileTreeAnimWidget` 과 같은 꼴(start/stop/set_elapsed).
- 검증(오프스크린 PySide6, 29항목): 버튼 자리 · 크기, 감춘 위젯, 350x155, 왕복 복원, 반복 토글, shrink 중 Pin, 단계 · 루프 되감기 · 연기 + 시각별 캡처로 눈 확인. 마야 GUI 미확인.
- 문서: `docs/A00370_ToolLauncher.md` 11) 절, CHANGELOG, version.

> [!summary] A00360_SortTool — **Sort By > Selection: 선택한 순서대로 아웃라이너 정렬** (v01.02->01.03) `#A00360_SortTool`
- 요청: 오브젝트를 **선택한 순서대로** 아웃라이너 정렬 순서를 바꾸는 기능. `AriSortOutlinerOptions` 의 **Selects** 라디오와 같은 동작.
- 코어 `sort_manager.py`: `MODE_SELECTION` 추가 — 정렬 키를 새로 계산하지 않고 `items` 의 **인덱스**(= 들어온 리스트 순서)를 키로 쓴다. 리스트는 Select Objects 시점의 선택 순서이므로 결국 선택 순서. 아웃라이너 적용은 기존 슬롯 스왑(부모별 그룹) 그대로, Reverse · Reorder in Outliner 옵션도 그대로 먹는다. 위치 없는 DG 노드도 이 모드에선 건너뛰지 않는다(아웃라이너는 DAG 만).
- UI: Sort By 그리드에 **Selection** 라디오(2행 3열 꽉 참) + 라디오 6개 툴팁. About 문구.
- 검증(mayapy 2024, 20항목): 최상위 선택 순서 → `A D C B E`, Reverse, 부모 다른 섞인 선택(로케이터·조인트), blendShape 포함, 없는 이름 missing, 아웃라이너 off, Name 모드 회귀. 마야 GUI 미확인.
- 문서 `docs/A00360_SortTool.md` 갱신(버전 이력 표 추가).

## 2026-10-22

> [!summary] A00540_JaliLipSync — **클립 여러 개를 순서대로 한 씬에: 클립 표 · Hold · 합친 wav** (v01.01->01.02) `#A00540_JaliLipSync`
- 요청: txt · wav 여러 개를 한꺼번에 넣고, 원하는 순서로 나열해 그 순서로 키가 한 씬에 들어가게. 음성도 여럿을 순서대로 재생. 파일 사이 `Hold` 프레임을 사용자가 정하게.
- 코어 `sequence.py`(Maya 비의존): `Clip` · `load_clip`(wav 자동) · `layout(clips, start, hold, fps)` — 클립 길이는 **wav 길이**(모델 출력은 끝 0.32 s 가 빠져 txt 길이로 이으면 다음 음성이 일찍 시작된다), 다음 시작 = 끝 + 1 + hold · `write_sequence_wav()` — 클립 wav 를 각자 프레임 자리에 놓은 wav 하나(마야 타임슬라이더는 사운드 노드 하나만 보여 준다). `keyer.apply_sequence()` — 전체 구간 cutKey 한 번, 클립별 키, hold 는 **끝 값을 end + hold 에 한 번 더 키**로 붙들어 정지 구간(안 붙들면 마야가 사이를 보간), 전체 Undo 한 번. `apply()` 는 단일 클립 래퍼.
- UI: TXT/WAV 한 줄 → 클립 표(# · Start · TXT · WAV · Length) + Add TXT(다중, 이름순) / Set WAV / No WAV / Remove / Up / Down / Clear, `Hold (frames)`, `Sequence WAV` 경로. Apply 로그에 클립별 구간. Remove Keys 는 표의 전체 구간.
- 함정: `int(2.3 s × 30 fps)` = 68 (68.99999…) — `key_frames` · `layout` 에 1e-6 을 더했다.
- 검증(mayapy 2024, `tests/run_all.py` 132항목 — 매핑 21 · sequence 17 · 코어 33 · UI 36 · 실제 파일 25): 합성 리그 + `out_en_002` 실제 5 클립(A0020, hold 12, 합친 wav 31.10 s). 마야 GUI 미확인.

> [!summary] A00145_RigConnect — **Connect by Rule 겹치는 이름 보호 + 스킵 사유 로그 · 레퍼런스 간 연결 실측** (v01.63->01.64) `#A00145_RigConnect`
- 요청: 중복 이름 케이스 문제 해결 + 레퍼런스로 불러온 노드끼리 규칙 연결이 되는지 조사.
- 문제: `connectAttr` 는 짧은 이름이 겹쳐도(`grp1|A:dup` · `grp2|A:dup` 를 `A:dup`) 에러 없이 첫 노드에 붙어 성공으로 셌다. 수정: 행마다 `resolve_node`(`ls -long`) 로 하나로 확정, 없음 · 겹침이면 **행 통째 스킵**, 확정된 긴 이름으로 연결. `on_skip(src, dst, attr, reason)` 콜백으로 사유 전달, UI 는 행 단위 한 줄 + attr 단위는 같은 행 · 사유를 묶어 한 줄(`no such attribute on Source (19) : Oh, Uh, ...`). 반환값은 그대로.
- 레퍼런스 조사(mayapy 2024): 레퍼런스 → 레퍼런스(다른 파일 · 같은 파일 두 번) · 중첩 레퍼런스(`OUT:SUB:node`) → 레퍼런스 전부 22/22, **저장 후 재오픈 유지**(`referenceQuery -editStrings` 에 connectAttr 편집), 언로드된 레퍼런스는 행 스킵 — 된다.
- 검증: 코어 10항목(겹침 행 스킵 · 긴 경로 행 연결 · 행/attr 사유 · 레퍼런스 6) + 이전 16항목 회귀 + UI 1(오프스크린 mayapy, 로그 줄). 마야 GUI 미확인.

> [!summary] A00145_RigConnect — **Connect by Rule: 어트리뷰트가 일부 없어도 끝까지 연결되는지 확인** (코드 변경 없음) `#A00145_RigConnect`
- 요청: 규칙 연결 도중 어트리뷰트가 일부 없어도 있는 것은 전부 연결되고 코드가 중단되지 않는지 확인, 중단되면 고칠 것.
- `connect_by_rule` 은 짝마다 `connectAttr -force` 를 try/except 로 감싸 실패를 skipped 로 세고 계속 간다 → **중단 없음, 고칠 것 없음**.
- 검증(mayapy 2024, JALI 22 · ARKit 52 두 규칙 × 8 = 16항목): Source 에 처음 · 가운데 · 끝 attr 없음 / Destination 에 절반 없음 / 양쪽에 서로 다른 것 없음 / Destination 잠김 / 타입 불일치(string) / 이미 연결됨(force 교체) / 여러 행 중 없는 오브젝트 행(그 행만 스킵, 다음 행 계속) / 자기 자신 연결 — 모두 나머지는 전부 연결.
- 알아 둘 것: skipped 수는 "없는 attr" 과 "잠김 · 타입 불일치 · 없는 오브젝트" 를 구분하지 않고, 로그에 어느 attr 이 스킵됐는지는 안 나온다(원하면 후속).
- 네임스페이스 질문(사용자): 1중 `A:` · 2중 `A:B:` · 3중 `A:B:C:` · 레퍼런스 `REF:A:B:`(소스 · 데스티네이션 양쪽) · 같은 잎 이름이 네임스페이스만 다른 경우 전부 연결 OK(mayapy 7항목). **함정**: 잎 이름이 겹치는 DAG 노드(`grp1|A:dup` · `grp2|A:dup`)를 짧은 이름 `A:dup` 로 주면 `connectAttr` 가 에러 없이 첫 노드에 붙는다 — 목록은 `ls` 의 최단 유일 이름이라 보통 안전, 담은 뒤 리네임 · 복제하면 애매해질 수 있음(메모리 `connectattr-ambiguous-short-name-silent`).

> [!summary] A00145_RigConnect — **Connect by Rule 규칙 `JALI 22 Viseme`** (v01.62->01.63, 데이터만) `#A00145_RigConnect`
- 요청: Jaw · Lip + 비즘 20(Ah Aa Eh Ee Ih Oh Uh U Eu Schwa R S ShChZh Th JY LNTD GK MBP FV W)을 가진 두 노드를 같은 이름끼리 잇는 규칙, 이름은 JALI 또는 더 좋은 것.
- `app/rules/connect/jali_22_viseme.json` — 이름 `JALI 22 Viseme`(개수를 이름에 넣어 ARKit 52 규칙과 같은 꼴). 코드 변경 없음, 콤보 `Reload` 로 뜬다.
- 검증(mayapy 2024): 로더 errors 0 · 규칙 2개 · 22개 attr 노드 두 개 사이 22/22 연결 · 한쪽에 attr 하나 없는 노드는 21 + skipped 1. 마야 GUI 미확인.

> [!summary] A00370_ToolLauncher — **프로파일 정리 반영** (v01.09->01.10, 데이터만) `#A00370_ToolLauncher`
- 확정(사용자): 계획서 제안대로 · humanIK · CurveTool 은 RIG 만, SetTool 은 UTIL, MaterialTool 은 MESH · FACIAL/UTIL 신설 동의 · standalone 제외 · 색 입힘 · **기존 버튼 순서 유지, 추가만** · `Mesh` → `MESH`.
- `data/profiles`: `Mesh.json` → `MESH.json`(git mv), `FACIAL.json` · `UTIL.json` 신설. 기존 버튼은 `Main` 에 그대로, 새 툴 22종은 뒤에 붙인 카테고리(RIG Control · Skin & Motion, ANIM Motion, MESH Edit, FACIAL Shape · Lip Sync, UTIL Select & Name · Scene · File). 버튼 13 → 38. 프로파일별 색(RIG 파랑 · ANIM 주황 · MESH 초록 · FACIAL 분홍 · UTIL 회색 · UE 보라). `A00430_DemBone` 아이콘 없어 svg/png 신규(icon builder, mayapy).
- 검증(헤드리스): 38개 전부 validate OK · 아이콘 · 중복 없음 · 경로 portable · 기존 13개 순서 HEAD 와 동일. 오프스크린 캡처로 색 · 아이콘 · 카테고리 확인. 마야 GUI 미확인. `active.json` 은 안 건드림.

> [!summary] A00370_ToolLauncher — **프로파일 분류 · 미등록 툴 등록 계획서** (착수 전) `#A00370_ToolLauncher`
- 요청: `data/profiles` 의 기존 분류(ANIM · Mesh · RIG · UE)를 참고해, 자주 쓰는 툴 중 버튼이 없는 툴을 등록하는 작업의 계획서.
- `docs/plans/A00370_ToolLauncher_profile_classification_plan.md` — 현황(등록 13, 카테고리는 전부 Main), 분류 축(D1 `FACIAL` · `UTIL` 신설 · D2 카테고리 2~3개 · D3 중복 등록 허용), 후보 25종을 프로파일별 표로(활동량 = 커밋 수, 사용 빈도 아님), 제외(구버전 · 템플릿 · **standalone 은 `__init__.py` 가 없어 등록 불가** · dev 툴은 `tools` 앵커 없어 절대경로로 저장됨), 절차 S1~S5(json 만, 코드 변경 없음), 확인 질문 Q1~Q5.
- 선검사: 후보 25종 전부 `validate` OK, 아이콘은 `A00430_DemBone` 만 없음.

> [!summary] A00370_ToolLauncher — **메뉴 `Profile > Show Profiles Folder`** (v01.08->01.09) `#A00370_ToolLauncher`
- 요청: 프로파일 json 저장 경로를 탐색기로 팝업하는 메뉴 문구.
- 메뉴 바에 `Profile` 메뉴(Help 왼쪽) → `data/profiles/` 를 공용 `file_opener.open_path` 로 연다(없으면 만든다), 로그에 경로. A00550 `Library > Show Libraries Folder` 와 같은 모양, `main_window.py` 만.
- 검증(오프스크린 PySide6, open_path 가짜로 바꿔): 메뉴 순서 Profile · Help · 항목 문구 · 넘어간 경로 = `PROFILES_DIR` · 로그 · 실패 시 `[ERROR]`. 실제 탐색기 팝업은 마야 GUI 미확인.

> [!summary] A00370_ToolLauncher — **검색(Filter) 추가** (v01.07->01.08) `#A00370_ToolLauncher`
- 요청: 필터로 툴 버튼을 검색할 수 있게.
- 버튼 영역 바로 위(Controls 박스 밖, 접어도 보임)에 공용 `JUN_mod_filter_qt_v01` 을 **rows_provider** 모드로 — 버튼 영역이 QListWidget 이 아니라 행 위젯 더미라서. 찾는 글자는 버튼 이름 + 카테고리 이름 + 툴 폴더명(`A00080` 으로도 찾힘), 부분 일치 · 대소문자 무시 · 여러 단어 AND. **남은 버튼이 없는 카테고리는 통째로 숨김**(`filtered` 시그널), `Number: n / N`.
- 재렌더(이름 변경 · 이동 · Color Select · 프로파일 전환) 뒤 `refresh()` 로 필터 유지. 자체 검색 코드 없음 — 공용 위젯 문서 적용 현황에 등록.
- 검증(오프스크린 PySide6, 사용자 프로파일은 가짜 데이터로 막고): 15항목 — 이름 · 카테고리 · 폴더명 · AND · 무일치 전부 숨김 · Clear 복원 · 재렌더 · Color 모드 · 카테고리 0개 · 위치. 마야 GUI 미확인.

> [!summary] A00220_BackupTool — **탐색기 드래그&드롭으로 대상 파일 추가** (v01.17->01.18) `#A00220_BackupTool`
- 요청: `Add...` 대화상자 말고 탐색기에서 파일을 끌어다 놓아도 Target Files 에 담기게.
- `Target Files` 그룹 어디에든(목록 · 빈 자리 · 버튼 줄) 놓으면 담긴다. 폴더는 **바로 안의 파일만**(하위 폴더 X). 이미 있는 경로는 건너뛰고(대소문자 무시) 로그 한 줄 `Dropped: N file(s), ...`. `Add...` 와 드롭이 `add_paths()` 하나를 쓴다.
- 드롭 이벤트는 `QListWidget` 뷰포트로 오므로 뷰포트 + 그룹 박스에 이벤트 필터(A00240 Junction 방식). 그룹에도 거는 이유: 실행 중엔 목록이 비활성이라 드롭을 못 받는데 `Add...` 는 실행 중에도 되므로 맞췄다. Auto Backup 중 추가한 파일은 바로 감시에 올린다(폴링은 처음 본 파일을 기준선만 잡아 저장으로 오인하지 않음).
- 검증(오프스크린 PySide6): 16항목 — 파일 2개 · 대소문자 다른 중복 · 폴더 1단계 · 없는 경로 · 텍스트 드래그 무시 · 목록 비활성 상태에서 그룹 드롭 · Active 때 watcher 등록 · 툴팁. 실제 탐색기 드롭은 GUI 미확인.

> [!summary] A00540_JaliLipSync — **규칙 json 역할표 · Target Auto / Manual · JaLi scale** (v01.00->01.01) `#A00540_JaliLipSync`
- 배경: JUN_JALI 쪽에서 만든 슬라이더 리그 `A0020_jali_slider_ctl.ma`(angela 어트리뷰트 1:1 슬라이더 22 + JaLi 박스, `DUMMY_IN_*` 입력 허브 0~1, `DUMMY_OUT_*` 출력 허브 — 계획 `JUN_JALI/docs/0090`, 어트리뷰트 안내 `0120`)에 VisemeNet 키를 걸려면 툴이 `CNT_PHONEMES` 이름과 angela 단위(scale 10 · Jaw/Lip 0~15)에 묶여 있는 것을 풀어야 했다. 계획서 `docs/plans/A00540_JaliLipSync_v0101_rules_manual_plan.md`.
- 매핑 json v2: `nodes`(역할 → 노드 이름) · `viseme_scale` · `jali{scale, range, fixed_default}`. 리그 표식은 코드가 아니라 json 의 phonemes 노드. 새 규칙 `jali_slider_dummy_in.json`(scale 1 · JaLi 0~1 · Fixed 0.6), angela json 보강. 타겟 해석은 `keyer.resolve_targets()` 한 곳(Auto 네임스페이스 / Manual node_map).
- UI: Target **Auto**(규칙의 phonemes 노드로 찾기) / **Manual**(Phonemes · Coartic · JaLi 칸 `<< Sel`, 빈 역할은 건너뛰고 로그에 `skipped:`). `JaLi scale` 스핀박스. 규칙을 바꾸면 배율 · Fixed 범위가 json 기본값으로 리셋. 적용 배율 > 어트리뷰트 max 면 `[WARN] exceeds`. 출력 세기(`output_max` · `global_scale`)는 리그에서 조절 — 규칙에 두지 않음(사용자 결정).
- 리그: A0020 의 `CNT_JaLi` 휴식 위치 0, 기본 9 는 `DUMMY_IN_JALI.Jaw/Lip` 기본값 0.6 이 민다 — 데이터 키가 그 자리를 덮어 더해지지 않는다(JUN_JALI `build_jali_slider_ctl.py`, 검증 305).
- 검증(mayapy 2024): `tests/run_all.py` — 매핑 21 · 코어 22 · UI 18(오프스크린) · 실제 파일 18(A0020 Auto/Manual, angela 키값 v01.00 과 동일). 마야 GUI 미확인.

---

## 2026-10-20

> [!summary] A00550_PoseMapper — **Connect To... 창이 마야를 막지 않게** (v01.05->01.06) `#A00550_PoseMapper`
- 보고: `Connect To...` 를 열면 아래 마야 창이 막혀 씬에서 오브젝트를 골라 Source / Target 을 채울 수 없다.
- 원인: 대화상자를 `exec_()`(모달)로 열었다.
- 수정: `show()` 모델리스 + `WA_DeleteOnClose`, 탭이 참조를 들고 있고 다시 열면 이전 창을 닫는다. `<< Sel` 은 그대로 `cmds.ls(sl=True)` 첫 노드.
- 검증(mayapy 2024 오프스크린): isModal False · 보이는 채로 `<< Sel` 이 Source / Target 을 채움 · 재오픈 시 새 창. 마야 GUI 미확인.

## 2026-10-19

> [!summary] A00550_PoseMapper — **Pose Map 에 JaLi 조절** (v01.04->01.05) `#A00550_PoseMapper`
- 배경: 테스트 씬에서 Pose Map 노드망(`pm_NET1`)이 BS 를 구동하는 동안 `CNT_JaLi` 를 2~15 로 바꿔도 얼굴이 그대로(실측) — 노드망이 음소 값만 더했다. 원래 JALI 노드망은 타겟마다 축만 있고 세기 조절이 없다.
- 추가: 타겟마다 `Axis`(- / Jaw / Lip) · `Strength`(0~1), factor = 1 + Strength × (축값 / Neutral − 1). JaLi 칸(노드 · Jaw / Lip 어트리뷰트 — translateX / Y 자동 · Neutral 9), `JALI Defaults` / `Clear Axes`, Connect 에 JaLi 노드. 씬 노드 = 노드망당 `pm_ratio_Jaw/Lip` + 축 있는 체인마다 `pm_jb_`(blendTwoAttr) · `pm_jm_`(mult). json `"jali"`, 옛 json · 노드망 호환.
- 검증(mayapy 2024 + 테스트 씬): `tests/test_jali.py` 24 · `test_ui_jali.py` 14 — **CNT_JaLi (2,9) (9,4) (12,6) 에서 원래 JALI 노드망과 같은 값**(Jaw 2 → jawOpen 0.222), 기존 시험 9종 회귀 통과. 계획서 §11 단계별 커밋. 마야 GUI 미확인.

> [!summary] A00550_PoseMapper — **창 크기를 언제든 자유롭게 · Save 등이 크기를 바꾸지 않게** (v01.03->01.04) `#A00550_PoseMapper`
- 보고: Save 뒤 창 크기를 드래그로 못 바꾼다, Save 를 누르면 크기가 저절로 바뀐다.
- 원인: ① `QTabWidget` 최소 크기(안 보이는 탭 포함 최댓값)가 창 최소로 강제 — 처음부터 그 이하로 못 줄였다(메모리 qtabwidget-min-size) ② Save 가 라이브러리 콤보에 긴 이름을, 상태 줄에 경로를 넣어 그 최소를 키움 → 창이 저절로 넓어지고 못 줄임.
- 수정: 탭을 `QScrollArea` 에 담음(**최소 폭을 걸지 않음** — A00480 방식과 달리 가로도 자유롭게, 작으면 스크롤바), 콤보는 `AdjustToMinimumContentsLengthWithIcon`, 상태 줄은 가로 `Ignored` + 툴팁. 처음 열 때만 내용에 맞춤.
- 덤: 테스트 씬 16:20 저장본에 노드망이 두 개(`pm_NET` 이 `pm_NET1` 의 Replace 에 밀려 BS 를 구동하지 않음) — 밀린 노드망을 고르면 상태 줄 `[!]` + 로그 경고. 시험은 `tests/scene_fixture.py` 로 원래 배선에서 시작.
- 검증(mayapy 오프스크린): `tests/test_ui_size.py` 8/8 + 나머지 7종 통과. 마야 GUI 미확인. 사용자 라이브러리 json 변경분은 커밋하지 않음.

> [!summary] A00550_PoseMapper — **Solo preview 가 저절로 꺼지던 문제** (v01.02->01.03) `#A00550_PoseMapper`
- 보고: Solo 를 켜고 음소를 고른 뒤 Target 값을 0 에서 올렸다 다시 0 으로 하면 Solo 가 꺼진다 → 체크박스를 눌러 끌 때만 꺼지게.
- 원인: 타겟 값을 바꾸면 음소 줄 글자가 `AHH` → `AHH (1)` 로 바뀌는데, **`QListWidget` 은 글자만 바뀌어도 `itemChanged` 를 쏜다** → 체크 변경으로 읽혀 Solo 를 껐다(v01.01 에서 넣은 동작). 같은 식으로 탭 이동 · 노드 칸 포커스 아웃(`editingFinished` 는 글자 그대로여도 온다) · Capture · Remove Network 도 껐다.
- 수정: 라벨 갱신은 신호를 막고, 체크는 **실제로 바뀐 경우만** 처리. 끄는 것은 체크박스 클릭과 창 닫기뿐 — 나머지는 유지하며 다시 건다(Source 변경 = 이전 원복 + 새로 / 체크 변경 = 새 체크 목록으로 / Capture = 잠시 원복 후 다시).
- 검증(mayapy 오프스크린): `tests/test_ui_solo.py` 15/15 + 기존 6종 회귀 통과(테스트 씬 포함). 마야 GUI 미확인.

> [!summary] A00550_PoseMapper — **메뉴 `Library > Show Libraries Folder`** (v01.01->01.02) `#A00550_PoseMapper`
- 요청: libraries 경로를 탐색기에서 팝업하는 메뉴.
- 메뉴 바에 `Library` 메뉴(Help 왼쪽) → `app/libraries` 를 공용 `file_opener.open_path` 로 연다(폴더가 없으면 만든다), 로그에 경로.
- 검증(mayapy 오프스크린, open_path 가짜로 바꿔): 메뉴 항목 · 넘어간 경로 = `LIB_DIR` · 로그. 실제 탐색기 팝업은 마야 GUI 미확인.

> [!summary] A00550_PoseMapper — **Source 목록 다중 선택 · 체크 / 해제 · 전체 토글** (v01.00->01.01) `#A00550_PoseMapper`
- 요청: Source tsl 에서 여러 어트리뷰트를 골라 한 번에 체크 / 해제, 전체 체크 / 해제 토글.
- 공용 `JUN_mod_checkList_qt_v01` 을 붙임(Shift / Ctrl 선택, 고른 줄의 체크박스 하나 · Space = 고른 줄 전부) + `Check Sel` / `Uncheck Sel` + `Check All` ⇄ `Uncheck All` 토글. 여러 줄이 한 번에 바뀌면 `checksChanged` 로 받아 상태를 전부 기억, 체크가 바뀌면 Solo preview 원복.
- 검증(mayapy 2024 오프스크린): `tests/test_ui_checks.py` 12/12(실제 체크박스 클릭 포함) + 테스트 씬 Pose Map 시험 회귀 통과. 마야 GUI 미확인.

> [!summary] A00550_PoseMapper **신규** — 음소 어트리뷰트 → 블렌드셰이프 포즈 (Pose Map) + blendWeighted weight 편집 (Blend Weights) `#A00550_PoseMapper`
- 요청: `JALI_IN` 같은 음소 노드 · 음소 · 블렌드셰이프(`BS_arkit`)를 골라 음소별 타겟 값을 조정 → 관계 저장 → 임의의 노드 쌍에 연결. 그리고 blendWeighted 에 UI 에서 보이는 weight 를 추가하는 탭. 기준값 기본 10 + 임의 실수, 이미 연결된 타겟은 Skip.
- 원인 실측: Node Editor 에서 `input[5]` 만 연결하면 `weight[5]` 원소가 없어 안 보이지만 **1.0 으로 계산**된다. `getAttr weight[5]` 는 **읽기만 해도 원소를 만든다** → 검사는 `-mi` 로만. 테스트 씬 `JALI1:bw_mouthFunnel [5] OHH` 가 정확히 이 상태였다.
- Pose Map: 타겟마다 blendWeighted(+clamp), weight = 포즈 / Ref, `pm_NET` network 가 message 로 묶음. 슬라이더 = 그 타겟 체인만 sync, Solo preview(연결된 음소는 값을 넣을 수 있는 위쪽 plug 로 · 원복), Capture(어떤 노드망이든 결과를 포즈로), json 저장, Connect To(Skip / Replace / Add). 음소 목록 체크 — `Jaw` · `Lip` 기본 해제.
- Blend Weights: input · weight 표, weight 없는 input 빨강, Add = 연결 + weight 같이, Create Missing(1.0, 결과 그대로), Remove = 둘 다.
- 검증(mayapy 2024 + 테스트 씬 `JP__CHN_Basic_1070_JALI_test.mb`, 열기만): 74항목. 계획서 `docs/plans/A00550_PoseMapper_plan.md` §10 에 단계별 진행 기록(중단 복구용). **마야 GUI 미확인**.

> [!summary] A00110_animTool_V02 — **Key > Key Attrs: 체크한 어트리뷰트만 Key every target** (v02.20->02.21) `#A00110_animTool_V02`
- 요청: 선택 오브젝트를 리스트업하고 키 가능한 어트리뷰트를 체크박스 목록으로 — 필터 검색, 채널박스에 보이는 것만 볼지 토글, 체크된 어트리뷰트를 차례대로 0 → 1 키 (A00290_BSTool_V02 Key every target 의 일반화).
- 새 `attr_key_manager.AttrKeyManager` — 목록은 오브젝트들의 합집합(`Channel Box only` 기본 켬 = keyable + channelBox, 끄면 잠기지 않은 수치형 전부). multi 는 원소로 펴고 별칭을 붙여 blendShape 타겟이 이름으로 보인다.
- 키 규칙은 BSTool 과 같다: n 번째 플러그가 `Start+n` 에서 1, 앞뒤 0. 순서 = 오브젝트 → 어트리뷰트. 없음 · 잠김 · 구동(컨스트레인트 / 드리븐 키 / 익스프레션 — 키를 걸면 pairBlend 가 끼어 리그가 바뀐다) 플러그는 건너뛰고 프레임도 쓰지 않는다. 필터에 가려진 체크는 제외 + 로그. Undo 한 번.
- UI: 공용 TSL · `JUN_mod_checkList_qt`(Shift/Ctrl 다중 체크) · `JUN_mod_filter_qt`, Check All(보이는 것만) / Clear Checks(전부), Start Frame, 행 툴팁에 그 어트리뷰트를 가진 오브젝트.
- 발견: mayapy 에서 `maya.standalone.initialize()` 가 `QGuiApplication` 을 먼저 만들어 위젯 생성이 조용히 죽는다(exit 127) → 오프스크린 UI 테스트는 `QApplication` 을 initialize **전에** 만들어야 한다.
- 검증(mayapy 2024, offscreen UI): 코어 13 (채널박스 / 전체 목록, blendShape 별칭, 순차 프레임, 잠김 · 구동 · 없음 건너뜀, pairBlend 미생성, Undo 한 번) · UI 6 (탭 존재, 리스트업, Check All 보이는 것만, 필터 제외, 버튼 경로, 토글 재나열 + 체크 유지) — 19/19. 마야 GUI 는 미확인.

> [!summary] A00540_JaliLipSync **신규** + JUN_JALI(VisemeNet 포크) 툴 3종 — **음성 → JALI 리그 립싱크** `#A00540_JaliLipSync`
- 요청: JUN_JALI 계획서(`docs/0030_tool_plan.md`)대로 — 더블클릭 추론 환경 설치, wav → txt 스탠드얼론 변환기(TSL + 저장 경로, 오류 시 중단 + 로그), 마야 키 툴(드래그&드롭 셸프), JALI ↔ ARKit 매칭.
- JUN_JALI: `setup_env.bat`(64bit Python 3.9~3.11 탐색 · winget 제안 · `.venv` · 자가 검사) · `Run_VisemeNet_Converter.bat` + `tools/VisemeNet_Converter`(검사 규칙 E01~E11 · 사전 검사 실패면 변환 0 · 변환 중 오류 즉시 중단 · QThread) · `vendor/Framework`(이 저장소 Framework 복사본).
- 발견: 원본 그래프가 `net2` dropout 0.5 를 **상수로** 박아 추론이 무작위(같은 wav 최대 차 0.64) → 불러올 때 상수만 1.0 으로 바꾸는 결정적 모드 기본. 출력은 음성 끝 **0.32초 짧다**(64줄 창 · 32줄 패딩, 시작은 맞음) → 줄 수 공식으로 E23 검사.
- 마야: `A00540_JaliLipSync` — txt 고르면 json / 같은 이름으로 wav 자동, 리그 네임스페이스 콤보, 매핑 json, 시작 프레임 · 비짐 배율 · JaLi 데이터/고정, 씬 fps 샘플, 구간 지우고 키, Undo 한 번, 사운드 노드.
- 검증: 변환기 검사 13 · 코어 17 · 오프스크린 UI 12, `setup_env.bat` 새 설치 84초 · 재실행 8초 · 파이썬 없을 때 안내 / mayapy 2024 코어 19 · UI 15. **미확인**: 변환기 창 실제 표시, winget 설치, Win10, 마야 GUI 드롭 · 소리 재생.

> [!summary] A00340_SelectionTool — **View > Show Profile: 활성 프로파일 json 을 탐색기에서 선택해 연다** (v01.09->01.10) `#A00340_SelectionTool`
- 요청: 메뉴바에 `Show Profile` — 누르면 이 PC 에서 툴이 참조하는 profile 경로가 탐색기에 표시된 채 팝업.
- `View` 메뉴에 항목 추가, `prefs.profile_path(get_active())` 를 공용 `file_opener.open_path` 로(파일 선택). 파일이 없으면 profiles → data 폴더 폴백 + `[WARN]`.
- 검증(mayapy 2024, offscreen UI): 메뉴 항목 존재, `open_path` 에 넘어가는 경로 = 활성 json, 파일 없을 때 폴백. 실제 `explorer /select` 호출은 에러 없이 실행됨, 마야 GUI 메뉴에서 눌러 보는 것은 미확인.

> [!summary] A00145_RigConnect — **Constrain > Constraint 에 `All Targets -> Each Follower` 옵션** (v01.61->01.62) `#A00145_RigConnect`
- 요청: Targets 에 `tgt_i` 여러 개, Followers 에 하나를 담고 Constrain 하면 타깃이 하나만 생긴다 → 모든 `tgt_i` 를 타깃으로 갖는 constraint 를 만드는 옵션.
- 원인: 짝짓기가 인덱스 1:1(타깃 1개면 브로드캐스트)이라 follower 하나엔 `tgt_0` 만 걸렸다.
- 수정: 체크박스(기본 OFF) — 켜면 follower 마다 종류별 constraint 하나에 Targets 전부. 짝짓기를 `constrain_manager.resolve_pairs()` 로 뽑아 두 모드가 공유. Matrix 모드에선 비활성.
- 검증(mayapy 2024, offscreen UI): Parent+Scale 타깃 3개, 2 follower × Point+Orient, mo off 평균 위치, OFF 시 예전 1:1, UI `on_constrain()` 경로 · Undo 한 번 · Matrix 비활성 — 12/12. 마야 GUI 는 미확인.

## 2026-10-16

> [!summary] A00110_animTool_V02 — **Tab 이 매니퓰레이터 공간 토글 대신 페인트 선택을 하던 것 수정** (v02.19->02.20) `#A00110_animTool_V02`
- 보고: `Tab : ON` 상태로 Tab 을 누르면 스크립트 에디터에 `dR_paintPress; selectPref -paintSelect 1 ...` 만 찍히고 토글이 안 된다.
- 원인: 뷰포트 Tab 은 핫키가 아니라 Modeling Toolkit 이 가로채 `nexOpt mayaTabPressCmd / mayaTabReleaseCmd` 를 실행한다(`modelingToolkit.mll` 문자열에서 확인) → `hotkey -keyShortcut Tab` 은 한 번도 불리지 않았다.
- 수정: `TabKeyManager` — 그 nexOpt 넷(use 플래그 + 명령)을 툴 명령(`run_tab_press` / `run_tab_release`)으로 바꿔 끼우고 끄거나 닫을 때 복원. 키 자동 반복은 한 번만 토글, 크래시로 남은 값은 MTK 기본으로 복원, MTK 미로드면 예전 핫키.
- 검증(mayapy 2024): `nexOpt` 는 GUI 전용 명령이라 가짜 저장소로 — 설치 · 실제 MEL 로 press/repeat/release 실행(토글 2회) · 복원 · 잔존값 복구 · 폴백. **마야 GUI 에서 Tab 실제 동작은 미확인**.

> [!summary] A00110_animTool_V02 — **최상위 Hot Key 탭 신설: Main = Hold 이식 + Tab 으로 매니퓰레이터 공간 Object/World 토글** (v02.18->02.19) `#A00110_animTool_V02`
- 요청: Hold 탭을 없애고 최상위 `Hot Key` > 하위 `Main` 으로 이식, Tap(Tab) 으로 매니퓰레이터 공간 Object / World 토글.
- `Timing > Hold` 삭제 → `Hot Key > Main` 에 Hold 그룹(버튼 + Shift+A) + Manipulator Space 그룹(토글 버튼 + `Tab hotkey`, 기본 켬).
- `HotkeyManager` 를 키마다 인스턴스로 일반화(`hold()` / `manip_space()`), 창 닫을 때 둘 다 원래 바인딩 복원. 새 `manip_space_manager.ManipSpaceManager.toggle()` —
  현재 툴 공간이 World 면 Object, 아니면 World 로 Move / Rotate / Scale 세 컨텍스트를 함께 맞춘다(Rotate 의 World 는 mode 1, Move / Scale 은 2).
- 검증(mayapy 2024, offscreen UI): 탭 구성(Timing = Move / Offset / Stagger, Hot Key = Main), 가짜 컨텍스트로 토글 4경우, 가짜 `cmds.hotkey` 로 Tab / Shift+A 설치 · 복원.
  standalone 에는 툴 컨텍스트 · 핫키 세트가 없어 **실제 공간 전환과 Tab 바인딩은 마야 GUI 미확인**.

> [!summary] A00400_CurveTool — **Create > Controls 셰이프 목록에 Filter** (v01.26->01.27) `#A00400_CurveTool`
- 요청: Controls 에서 필터로 원하는 컨트롤러를 검색.
- 공용 `JUN_mod_filter_qt_v01` 을 셰이프 목록(QListWidget)에 붙임 + `Number: N / 34`. 현재 셰이프가 가려지면 보이는 첫 셰이프로 옮기고,
  `_shape()` 는 숨은 항목을 돌려주지 않는다(보이는 것이 작업 대상).
- 검증(mayapy 2024, offscreen UI): `arrow` → 15 / 34 · current 이동, 불일치 → 만들기 경고, Origin 으로 필터된 셰이프 생성. 마야 GUI 는 미확인.

> [!summary] A00060_jointTool_V03 — **Orient / Rotate 가 둘 다 값이 있는 조인트의 회전을 바꾸지 않음** (v03.14->03.15) `#A00060_jointTool_V03`
- 요청: `rotate to joint orient` 를 누르면 rotate 와 jointOrient 가 둘 다 값이 있는 조인트가 보이는 회전이 달라진다 → 전후 변화 없게.
- 원인: 오일러 각을 축별로 더함(옛 MEL 포팅). 수정: `R x JO` 행렬 합성 → 남는 쪽 순서로 분해, 옛 합에 가장 가까운 등가 해
  (`setToClosestSolution` 은 짐벌 근처에서 다른 회전을 줘서 `setToClosestCut` 두 후보로). 반대 버튼도 같이, 잠김 · 연결은 건너뜀.
- 검증(mayapy 2024): 무작위 240 + 짐벌 조합 371건 월드 행렬 불변, 한쪽만 값 → 예전 숫자, undo 복귀. 마야 GUI 는 미확인.

> [!summary] A00480_FileTool — **Import > CSV 에 Value Scale (CSV 값 x 배율)** (v01.10->01.11) `#A00480_FileTool`
- 요청: CSV 는 [0, 1] 값뿐인데 AdvancedSkeleton 페이셜 컨트롤은 [0, 10] 키를 요구 → 임포트 때 사용자가 넣은 수를 곱하는 UI.
- UI `Value Scale` 줄(QDoubleSpinBox, 기본 1, 빠른 버튼 `x1` / `x10`) → `csv_ops.import_facial(value_scale=)` 가 `float(raw) * value_scale` 로 키. 1 이 아니면 로그 · 요약에 배율.
- 검증(mayapy 2024, offscreen UI): `x10` 클릭 → jawOpen 0~1 이 0~10 으로 키, 한 번 undo 로 키 전부 제거. 마야 GUI 는 미확인.

> [!summary] A00275_skinTool_V01 — **Weights > Classic 의 Native 엔진이 선택 버텍스만 처리** (v01.35->01.36) `#A00275_skinTool_V01`
- 요청: Classic 탭 Native 모드에서 선택한 버텍스만 웨이트 전이 — Joints to Joints 먼저, Meshes to Meshes 도 오래 걸리지 않으면.
- `Joints to Joints`: 선택 파싱을 Transfer 탭의 `parse_target_selections` 로 바꿔 버텍스 · 엣지 · 페이스 선택이면 그 버텍스만
  `_native_move_columns(vtx_ids, soft)` 로 읽고 써서 본 컬럼 이동(소프트 셀렉션 = falloff 비율). 메시 통째 선택은 예전 그대로 전체.
- `Meshes to Meshes`: To 메시에 버텍스를 고르면 `_transfer_one_native` 재사용(전체 copySkinWeights 후 미선택 복원, `surface_association` 인자 추가로
  Transfer Mode 반영) - To 의 skinCluster 는 유지. 통째 선택한 To = 전체, 선택 안 한 To = Skipped, 컴포넌트 선택이 아예 없으면 예전 동작. 끝나면 선택 복원.
- 검증(mayapy 2024) 20 항목 통과. 마야 GUI · 소프트 셀렉션은 미확인.

> [!summary] A00400_CurveTool — **Display > Replace 가 교체본의 선 굵기도 복사** (v01.25->01.26) `#A00400_CurveTool`
- 요청: Shape Edit 으로 굵게 한 커브의 셰이프로 Replace 하면 결과가 얇게 나온다 → 교체본 굵기를 그대로 복사.
  (처음엔 "대상의 교체 전 굵기 유지" 로 읽고 고쳤다가, 같은 날 사용자 확인으로 **교체본 굵기 복사**로 바꿨다.)
- 원인: 레퍼런스 대상은 셰이프를 못 지워 CV 만 옮기므로 굵기가 옛 값으로 남는다. 로컬 대상은 복제본에 굵기가 딸려 왔지만 명시적으로 쓰지 않았다.
- 수정: `control_manager._line_widths` / `_restore_line_widths` — 교체본 굵기를 로컬 경로(복제 전에 읽어 새 셰이프에)와 레퍼런스 경로(CV 매칭 뒤 setAttr) 모두에 쓴다.
- 검증(mayapy 2024): 굵기 6.0 교체본 → 기본 굵기(-1) 대상. 로컬 Mirror 끔/켬 · 레퍼런스 Mirror 끔/켬 전부 6.0, 레퍼런스는 저장 후 다시 열어도 6.0, 로컬 undo 시 -1 복귀.

## 2026-10-13

> [!summary] A00480_FileTool — **Import 탭을 하위 탭 CSV / FBX 로, CSV = A00200_CSV_tool(ARKit Facial Import) 이식** (v01.09->01.10) `#A00480_FileTool`
- 요청: A00200 을 A00480 으로 전부 이식, UI 전부 영어, 블렌드셰이프뿐 아니라 ARKit 52 어트리뷰트를 가진 노드에도 키 임포트, Import 하위 탭 CSV · FBX.
  **원본 A00200 은 보존**(다른 이식들과 같은 방침).
- 코어 `core/csv_ops.py` — `node_targets(node)`(블렌드셰이프 = weight 별칭 · 그 밖 = 스칼라 어트리뷰트, 소문자 키) · `list_candidate_nodes()`
  (`ls(type=blendShape)` + `ls("*.jawOpen", recursive=True)` 류 대표 5개로 ARKit 노드 탐색, 네임스페이스 포함) · `detect_best_node` · `import_facial`
  (다운샘플 step · 씬 FPS · 키 · 타임라인 확장 · 오디오) · `resolve_audio`(같은 stem WAV, `_raw` 뗀 stem, 동영상에서 ffmpeg 추출) · `summary_lines`.
  **키 · 타임라인 · 사운드를 한 undo 청크로** — `playbackOptions` 도 undo 항목이라 원본처럼 키만 묶으면 첫 undo 가 타임라인만 되돌린다(mayapy 실측).
- UI `ui/import_csv_page.py`(`CsvImportPage`: CSV File · Node 콤보 `(n ARKit, 타입)` + Detect / Selected · Start Frame · FPS Recorded/Output · Audio ·
  Import Animation) · `ui/import_tab.py` = `QTabWidget(CSV, FBX)`, FBX 는 예전 SECTIONS 표(`FbxImportPage`), `ImportTab.buttons` · 핸들러 이름 호환 유지.
- 검증: mayapy 2024 47항목 — 52 이름 · 컨트롤/블렌드셰이프/네임스페이스 후보 · 헤더 매칭 · 60→30 다운샘플 값/프레임 · HeadYaw 같은 이름도 키 ·
  씬 FPS · 타임라인 · undo 한 번 · 60→60 블렌드셰이프 · 오류 3종 · 오디오 stem/WAV · ImportTab 하위 탭 · Detect/Selected · 페이지 임포트/오류 로그 영어.
  ffmpeg 추출 · 마야 GUI 는 미확인. standalone 은 `undoInfo(state=True)` 를 켜야 undo 검사가 된다.
- 문서 `A00480_FileTool.md` §3-1 · 표 · 구조 · 기능 더하기, CHANGELOG v01.10, About.

> [!summary] A00240_PathTool — **Junction > Create `Tree...`: Tree 탭과 같은 트리 팝업에서 폴더를 체크해 Sources / Create In 에 담기** (v01.22->01.23) `#A00240_PathTool` `#Framework`
- 요청: Create 탭의 TSL 에 경로를 넣을 때 Tree 탭 UI 를 그대로 쓰는 팝업, 차이는 경로마다 체크박스.
- Framework `JUN_mod_fileTree_qt_v01` 에 **`checkable_folders=True`** 추가 — 폴더 행(루트 포함)에 체크박스, 기억·신호·다중 체크는 `checkable_files` 와
  같은 규칙, `...` 생략 행은 체크 없음. 기본값 꺼짐이라 A00240 Tree 탭 · A00210 · A00480 은 그대로.
- A00240 `junction_tab._TreePickDialog` — 두 리스트가 팝업 하나를 공유(트리가 남는다), 처음 열 때 Tree 탭 경로로 시작, `Add Checked to <list>` 가 담고 체크를
  비운 뒤 닫는다. 파일은 체크박스 없음 · 기본 감춤(정션은 폴더만). `_PathList(on_tree=...)` 로 `Tree...` 버튼.
- 검증: 오프스크린 PySide6 — 두 버튼 · 시작 경로 · 폴더/루트 체크박스 · 파일 체크박스 없음 · 체크(공용 checkTree `set_checked`) → 라벨/버튼 → Add → TSL
  → 체크 비움/닫힘 · 재사용 · Create In · 빈 Add 유지 · 중복 건너뜀 · Tree 탭 영향 없음. 테스트에서 모달 창은 `QTimer` 드라이버 + 워치독으로 돈다.
- 문서 `A00240_PathTool.md` 11-1 · `Framework_MOD_fileTree_qt.md` 옵션 표 · CHANGELOG.

> [!summary] A00145_RigConnect — **Connect by Rule `Manage...`: 규칙을 체크해 json 파일 삭제** (v01.60->01.61) `#A00145_RigConnect`
- 요청: 규칙 중 일부를 골라 지우는 기능. `Rule` 콤보 옆 `Manage...` → 규칙 표(체크 | Name | Pairs | File, 툴팁에 설명·경로·짝) →
  `Delete Checked` 가 이름을 나열해 한 번 묻고 파일을 지운다. 창을 닫으면 콤보 재로드.
- 코어 `connect_rules.delete_rules(rules)` — **규칙 폴더 안의 .json 만** 지운다(밖의 경로 · 다른 확장자는 failed 로 돌려주고 안 건드림),
  이미 없는 파일은 지운 것으로. 깨진 json 은 표 아래 빨간 줄로만 알리고 건드리지 않는다.
- 검증: mayapy 2024 — delete_rules(선택 삭제 · txt/폴더 밖/빈 경로 거절 · 없는 파일) + 다이얼로그 오프스크린(표 · 체크 · 삭제 후 갱신 · 비면 버튼 비활성)
  + MainWindow 콤보 재로드. 마야 GUI 확인 아직.

> [!summary] A00145_RigConnect — **Connect > Transfer Connection `Save as Rule...`: 체크한 연결을 Connect by Rule 규칙 json 으로 저장** (v01.59->01.60) `#A00145_RigConnect`
- 요청: Transfer Connection 탭의 Source Objects + Attributes · Connected Nodes 체크 관계만으로 규칙을 만들고 싶다 (더 좋은 방법이 있으면 제안).
  이 방식을 그대로 채택하고 두 가지를 더했다 — **방향 선택**(규칙은 `Source.a -> Destination.b` 한 방향이라 downstream / upstream 중 하나) 과
  **저장 전 미리보기 창**(이름 · 파일 · 설명 · 짝 체크).
- 코어: `connection_transfer_manager.rule_pairs(rows, attrs, nodes, upstream, downstream)` — cmds 없이 list_rows 결과만 읽어
  `(driver_attr, driven_attr)` 짝을 모은다(오브젝트가 여럿이면 같은 짝은 한 행 + 개수 + 플러그 목록). `connect_rules.save_rule` /
  `rule_file_name` / `rule_path` — 같은 이름 짝은 `attributes`, 다른 이름은 `pairs`, 파일명은 이름 슬러그, 덮어쓰기는 플래그로만.
- UI: `ui/rule_save_dialog.py` (`RuleSaveDialog`) — Direction 라디오(짝 없는 쪽은 비활성), 짝 표, 적용 안내 문구, 파일 이름은 이름을 따라가되
  손대면 고정, 파일 존재 / 같은 이름 규칙은 확인·경고. 저장 뒤 Connect 페이지 `Rule` 콤보 재로드 + 새 규칙 선택.
- 검증: mayapy 2024 — rows/nodes → rule_pairs(down · up · 노드 필터) → save_rule(attributes/pairs 분리 · 중복 · 덮어쓰기 거절 · ValueError) →
  load_rules → connect_by_rule 로 다른 오브젝트에 재연결 확인, 다이얼로그 오프스크린(방향 전환 · 파일명 추종 · 체크 해제 · result). 마야 GUI 확인 아직.
- 문서 `A00145_RigConnect.md` Connect by Rule 절 · Transfer Connection 5번 · 구조 갱신.

> [!summary] A00240_PathTool — **Junction > Create: 끝 폴더 이름이 같은 소스들이 서로를 막던 문제 수정** (v01.21->01.22) `#A00240_PathTool`
- 증상: n -> 1 로 서로 다른 소스를 여러 개 담았는데 두 번째부터 `same junction path as an earlier row`.
- 원인: 정션 이름 = 소스의 **끝 폴더 이름**(`basename`)이라 `ProjA/Content` 와 `ProjB/Content` 가 같은 폴더 안에서
  둘 다 `Content` 로 겹쳤다. 상태 문구는 맞았지만 하나만 만들어지는 결과가 문제.
- 수정: `core/junction.unique_names()` — 같은 폴더에 만들 소스들 중 **겹치는 것만** 상위 폴더 이름을 앞에 붙여
  `ProjA_Content` · `ProjB_Content`(그래도 같으면 한 단계 더, 다 써도 같으면 `_2`). 겹치지 않는 소스는 그대로.
  같은 소스를 두 번 담으면 `same source as an earlier row` 로 거른다(이름 계산에서는 빼서 이름이 길어지지 않게).
  n -> n 에서 두 행이 같은 Create In 폴더를 쓸 때도 같은 규칙. `Target row is the junction path` 는 그대로.
- 검증: 임시 폴더에 plan 시나리오 6종 + 실제 `mklink /J` 왕복(만든 뒤 재계획 = already a junction, rmdir) +
  오프스크린 PySide6 로 Create 탭 미리보기 표 확인(3 ready / 3 rows). 문서 11-1 · CHANGELOG · 툴팁 갱신.

> [!summary] A00030 quickTool_V02 — **File 섹션(Copy Scene Folder · Open Scene Folder)을 UI 에서 숨김, 코드는 그대로** (v02.06->02.07)
- 요청: File 관련 버튼 UI 를 없애되 내부 기능 코드는 남긴다.
- `MainWindow.HIDDEN_SECTIONS = ("File",)` — `build_ui` 가 이 제목의 섹션을 건너뛴다. `SECTIONS` 표의 `File` 줄 ·
  핸들러 `on_copy_scene_folder` / `on_open_scene_folder` · `quick_ops.scene_folder` / `open_scene_folder` 는 그대로(튜플에서 빼면 바로 복귀).
  About 의 `[File]` 두 줄 삭제, 창 기본 높이 700→640. A00480_FileTool 의 Path 탭과 겹치는 기능이라 숨겼다.
- 문서 `A00030_quickTool_V02.md` 안내 · 화면 · File 절 · 구조 · 검증 갱신.
- 검증: mayapy 2024 오프스크린 6항목 — 그룹박스에 `File` 없음 · `buttons` 에 두 버튼 없음 · 보이는 섹션 8개 순서 · 표에 줄 남음 ·
  핸들러 직접 호출 동작 · `HIDDEN_SECTIONS` 비우면 복귀. GUI 확인 아직.

> [!summary] A00340 SelectionTool — **좌우 배치 취소 → 상하 복귀 · Controls 가 스크롤 없이 전부 보이게 · 로그는 창 맨 아래** (v01.08->01.09)
- 요청: 어제의 좌우 배치 요청을 취소하고 원래(상하)대로. Controls 가 보일 땐 스크롤 없이 전체가 보이게. 로그창은 툴 맨 밑에.
- UI 두 파일을 v01.07(`fa9f38b`) 로 되돌린 뒤 다시 작업: 로그 그룹을 Controls 에서 빼 `main_window` 의 스플리터 아래 `Log` 그룹으로
  (고정 90px, Controls 를 접거나 숨겨도 보인다). `SelectionTab(log_callback)` 만 받는다. 창 360x620.
- **위 칸 높이 맞춤** `_fit_controls_height`: 처음 보일 때(`showEvent`) Controls 내용의 최소 높이 + 프레임 + 가로 스크롤바 두께를
  위 칸으로 잡아 스크롤 없이 전부 보인다. 접었다 펴면 그 높이로, 숨긴 채 열었다 보여도 맞춘다.
- CHANGELOG v01.09 · 문서 8항 · About · 주석.
- 검증: mayapy 2024 오프스크린 — 세로 스플리터, 위 칸 높이 ≥ 내용 높이 · 세로 스크롤바 없음, 로그가 스플리터 아래 ·
  Show Controls 꺼도 로그 보임, 접기/펴기 복원, 숨긴 채 열었다 보일 때 맞춤, v01.07 테스트 19항목 통과. GUI 확인 아직.

## 2026-10-12

> [!summary] A00340 SelectionTool — **배치를 좌우로: Controls 왼쪽 | 버튼 모음 오른쪽** (v01.07->01.08)
- 요청: Controls 가 위, 나머지가 아래인 구성을 Controls 왼쪽 · 나머지 오른쪽으로.
- `QSplitter(Qt.Vertical)` → `Horizontal`, 기본 너비 `CONTROLS_WIDTH = 300` | 480, 창 360x620 → **760x600**.
  한 줄짜리 Profile / Create / Color 는 좁은 칸에 안 맞아(오프스크린 최소 547px) **두 줄**(위젯 행 + 버튼 행)로.
  폰트에 따라 버튼 폭이 달라 상수로 못 박으므로 **처음 보일 때(`showEvent`) 내용의 최소 너비를 재서** 왼쪽 칸을 그 이상으로
  연다(세로 스크롤바 폭을 여유로 더함 - 세로 바가 뷰포트를 좁혀 가로 바를 부르던 것).
  왼쪽 칸의 남는 높이는 Log 그룹이 받는다(`setFixedHeight(90)` → 최소 90 + stretch). 접기는 헤더 **너비**로 줄이고
  펴면 직전 너비 복원(`_controls_expanded_w`). View > Show Controls 는 그대로(숨기면 오른쪽이 전체).
- CHANGELOG v01.08 · 문서 8항 · About · 주석의 위/아래 표현을 왼쪽/오른쪽으로.
- 검증: mayapy 2024 오프스크린 — 스플리터 가로, 왼쪽 x < 오른쪽 x · 두 pane 높이 같음, 접으면 왼쪽 너비가 헤더 폭 근처,
  펴면 복원, Show Controls 끄면 오른쪽 너비 = 스플리터 전체, Log 가 왼쪽 칸 남는 높이를 받음. GUI 확인 아직.

> [!summary] A00030 quickTool_V02 — **Attribute > Attribute Lock: 채널박스에서 고른 어트리뷰트를 선택 오브젝트 전부에 lock/unlock 토글** (v02.05->02.06)
- 요청: 토글 버튼 하나로, 선택한 오브젝트들의 선택한 어트리뷰트를 lock · unlock.
- `quick_ops.channel_box_plugs()` — 채널박스 네 구역(main · shape · history · output)의 선택 어트리뷰트 × 그 구역의
  오브젝트 목록을 `node.attr` 플러그로. 없는 어트리뷰트는 건너뛰고 개수만. 채널박스가 없으면(헤드리스) 경고 한 줄.
- `quick_ops.toggle_attribute_lock(plugs=None)` — 지금 상태를 보고 **전부 잠겨 있으면 풀고, 아니면 전부 잠근다**(섞여 있으면
  안내 한 줄). `undo_chunk` 하나. 레퍼런스 노드 · 연결된 어트리뷰트도 잠긴다.
- ★ mayapy 실측: **부모 복합(`translate`)이 잠겨 있으면 자식 `tx` 의 `setAttr -lock 0` 은 조용히 성공하지만 그대로 잠겨 있다.**
  `_unlock_plug` 가 풀고 나서도 잠겨 있으면 부모를 풀고 요청에 없는 형제는 다시 잠근다(위로 반복). 메모 `maya-attr-lock-parent-compound`.
- UI: `Attribute` 섹션을 `Select` 다음에(버튼 하나라 가로를 다 씀), About 한 줄, 창 기본 높이 660→700.
- 문서 `A00030_quickTool_V02.md` 섹션 · 화면 · 검증 갱신.
- 검증: mayapy 2024 오프스크린 27항목 — lock / unlock / mixed / undo 한 번 / 부모 잠금 자식 unlock / 연결 / 레퍼런스 / 없는 플러그 /
  채널박스 없음 경고 / 섹션 순서 · 버튼 클릭 로그. **채널박스에서 실제로 읽는 경로와 GUI 는 아직.**

> [!summary] A00340 SelectionTool — **View > Show Controls: Controls pane 을 통째로 숨기기** (v01.06->01.07)
- 요청: Controls 를 접어도 차지하는 영역이 너무 크다. Help 옆 메뉴에서 토글하고, 안 보일 때는 영역이 아예 없어야 한다.
- 원인: 접기는 `CollapsibleBox` 헤더 줄 + 위 pane 인 `QScrollArea` 의 최소 높이가 남는다(스플리터 `setCollapsible(0, False)`).
- `View` 메뉴(공용 메뉴 바가 Help 왼쪽에 놓음) 에 체크형 `Show Controls`. 끄면 `SelectionTab.set_controls_visible(False)` 가
  위 pane 을 `setVisible(False)` — 스플리터가 그 위젯과 핸들을 없는 것으로 쳐 버튼 모음이 창 전체를 쓴다. 켜면 직전 비율 복원.
- 상태는 `prefs.set_setting("show_controls")` 로 `data/active.json` 에(다른 키 보존하도록 `set_active` 도 merge 로). 다음 실행 때
  숨긴 채 열고 메뉴 체크를 실제 상태에 맞춘다(시그널 막고).
- CHANGELOG · 문서 8항 · About 갱신.
- 검증: mayapy 2024 오프스크린 — 메뉴 순서 View | Help, 끄면 pane 숨김 · 핸들 숨김 · 버튼 pane 높이 = 스플리터 전체,
  켜면 비율 복원, active.json 에 키 저장 + `active` 보존, 새 창이 저장값대로 숨긴 채 열리고 체크도 꺼짐. GUI 확인 아직.

> [!summary] A00030 quickTool_V02 — **Select > Select Shapes: 선택한 오브젝트 대신 그 셰이프를 선택** (v02.04->02.05)
- 요청: 커브를 고르고 있으면 커브 셰이프를, 메시면 메시 셰이프를 선택하는 버튼.
- `quick_ops.select_shapes()` — `ls -objectsOnly` 로 받은 선택마다 `listRelatives -s -ni` 로 셰이프를 모아 `select -r`.
  타입을 가리지 않고(nurbsCurve · mesh · locator …) **한 트랜스폼의 셰이프 전부**, **Orig 는 제외**, 컴포넌트는 그 셰이프,
  이미 셰이프면 그대로. 셰이프 없는 것(조인트 · 빈 그룹)은 빠지고 이름을 경고로. 로그는 타입별 개수 요약 한 줄.
- UI: `Select` 섹션을 `Print` 다음에(버튼 하나라 가로를 다 씀), About 한 줄, 창 기본 높이 620→660.
- 문서 `A00030_quickTool_V02.md` 섹션 · 화면 · 검증 갱신.
- 검증: mayapy 2024 오프스크린 17항목 — 셰이프 둘인 컨트롤러 커브 2개 · 스킨 메시 Orig 제외 · 컴포넌트 · 섞인 선택의 경고 ·
  undo 로 선택 복원 · 섹션 순서와 버튼 클릭 로그. 실제 마야 GUI 확인은 아직.

> [!summary] dev 정리 — **낱개 스크립트 9개를 A 번호 툴로: A00520_icon_builder · A00530_dependency_check 신규, pycache 는 A00500 에, build_release 는 A00510 legacy, 메모는 _archive** 
- 요청: dev 의 코드를 조사해 `AXXXXX_{툴이름}` 단위로 분류할 수 있는 것을 정리 → 제안대로 진행.
- **A00520_icon_builder** (v01.00, 옛 `build_icons.py`): `tools/*/icon` 에 더해 **`dev/*/icon` 도** 훑는다(옛 것은 tools 만), `--only <툴>` 필터, `--ico`(16~256 다중 크기, Pillow 있을 때만 · mayapy 엔 없어 건너뛰고 알림), 셸프 `Icons` 버튼. `app/core/icon_builder.build_all` 이 (ok, failed, ico) 보고서.
- **A00530_dependency_check** (v01.00, 옛 `check_dependencies.py`): 검사 표는 그대로, 셸프 `DepCheck` 버튼 + 뷰포트 요약. **`dev/check_dependencies.py` 는 재노출**(DEPENDENCIES.md · 계획서가 그 경로를 적어 둠).
- **A00500_reloader**: `remove_pycache.py` → `app/core/pycache.py`(find/remove, 루트는 파일 기준 JUN_All), `clean_pycache()` + 두 번째 드롭 파일 `__dragDrop_A00500_pycache.py`(`Clear pyc`). `remove_pycache_for_dev.py`(G: 고정 경로)는 삭제.
- **A00510_release_builder**: 전신 `build_release.py` 를 `legacy/` 로(README). 문서·주석의 "`dev/build_release.py` 가 툴 하나 + Framework 만 복사" 는 A00510 으로 바꿈(A00400 · Framework_control_shapes · control_shapes.py · joint_curve_manager.py).
- `__userSetup.py` · `__memo.py`(2026-01 스니펫, G: 경로) → `_archive/study_notes/100_Memo/05_·06_Memo_dev_*_2026-01.py`. dev/ 에는 `__init__` · `reloader_v02`(재노출) · `check_dependencies`(재노출) · 툴 폴더 4개만 남는다.
- 아이콘 3개 신규(이미지 틀 · 체크 링 · 빗자루 선), A00520 자신으로 `--only A005` 렌더. 문서 `A00520_icon_builder.md` · `A00530_dependency_check.md` 신설, README 배치 표 2줄, 옛 스크립트를 가리키던 문서 7곳 갱신.
- 검증: mayapy 2024 — A00520 `only=A005` 로 dev 아이콘 5개 png, tools+dev 둘 다 탐색, A00530 in-Maya 표 + 재노출 동일 모듈, clean_pycache 임시 폴더(중첩 포함) 삭제, 드롭 파일 3개 명령 문자열 · 아이콘, A00530 셸프 명령 실행. 마야 GUI 드롭은 아직.

> [!summary] A00510_release_builder — **`dev/release_builder_QT` 이름을 A 번호 규칙으로 + 셸프 설치** (v01.02->01.03)
- 요청: release_builder_QT 도 `AXXXXX_release_builder` 로. dev 의 코드를 tools 와 같은 방식으로 관리하는 것이 좋은지, 더 나은 방법이 있는지도.
- git mv `dev/release_builder_QT` → `dev/A00510_release_builder`, 아이콘 3개 · `docs/release_builder_QT.md` → `docs/A00510_release_builder.md` 도 git mv. 코드(`launch` import 경로 · `ICON_STEM` · 로그창 objectName) · 문서(README · Release_Layout · A00500 · A00210 주석) · 메모 5개의 옛 이름 34곳 치환 — 지난 WORKLOG 본문은 그대로.
- 추가: `__dragDrop_A00510.py`(라벨 Release) + 패키지 `__init__.run()` — launch 최상단이 AppUserModelID 를 지정하므로 **늦게 import** 해 마야에서 패키지 import 만으로 작업 표시줄 묶음이 바뀌지 않게.
- 검증: mayapy 2024 오프스크린 — 패키지 import 시 launch 미로드, 아이콘 ico/png 탐색, 창 생성, 릴리즈 대상 목록에 dev 툴 없음, 드롭 파일의 셸프 명령 실행.

> [!summary] A00500_reloader — **dev 의 리로더를 셸프 버튼 툴로 정리** (신규 v01.00)
- 요청: `dev/reloader_mayaScript_v02.py` 를 복사해 마야 툴로 쓰고 있다 — 다른 툴처럼 `__dragDrop_AXXXXX.py` 로 셸프에 설치하고 `AXXXXX_reloader` 폴더로 관리. tools 가 더 맞으면 tools 로, 아니면 dev 에 정리.
- 판단: `config.DEV_MODE` 에 의존하고 릴리즈본(dev 제외)에 실리지 않는 개발 전용이라 **`dev/A00500_reloader`** (release_builder_QT 와 같은 자리). 40여 개 launch.py 가 `from dev.reloader_v02 import reload_for_tool` 을 쓰므로 **`dev/reloader_v02.py` 는 얇은 재노출**로 남겨 호출부는 손대지 않았다.
- 이동(git mv): `reloader_v02.py` → `app/core/reloader.py`(`reload_package` 가 (ok, failed) 를 돌려주게), `reload_path_list.py` → `app/config/reload_packages.py`, 붙여넣기 스크립트 v01/v02 · v01 리로더 · 모듈 목록 → `legacy/`(README, import 안 됨). 신규: `__init__` · `launch.run(True)`(config → 리로더 자신 → Framework/tools 순, 뷰포트에 개수 보고, DEV_MODE 꺼짐이면 건너뜀) · `__dragDrop_A00500.py`(라벨 Reload) · 아이콘 svg+png(원형 화살표).
- 문서: `docs/A00500_reloader.md` 신설, README 배치 표 한 줄, Release_Layout 표 한 줄.
- 검증: mayapy 2024 — run(True) 로 Framework·tools 모듈 리로드와 개수, 재노출 import 와 reload_for_tool, DEV_MODE 꺼짐 경로, 드롭 파일의 셸프 명령 실행. 마야 GUI 드롭 설치는 아직.

> [!summary] A00240 PathTool — **Tree 탭: 정션 우클릭에 Reveal (Junction) / (Origin)** (v01.20->01.21, Framework `path_context`)
- 요청: Tree 에서 정션 항목(`main\tgt_0010`)을 더블클릭하면 정션을 거친 경로가 열린다. 우클릭에 `Reveal in File Explorer (Junction)` / `(Origin)` 두 항목을 두어 후자가 원본(`...\tgt_0010`)을 열게 — 좋은 생각이면 그대로.
- 판단: 그대로 구현. 더블클릭은 **보이는 경로 그대로**(= Junction) 유지 — 트리에 적힌 것이 열려야 놀랍지 않고 원본은 메뉴에서 고른다.
- `Framework/qt/path_context.py`(공용): `origin_of(path)` = `realpath` 가 정규화 경로와 다르면 실제 경로(정션 · 심볼릭 링크, **정션을 거친 하위 경로도**), `build_path_menu(view, path)` 가 origin 있으면 Junction/Origin 두 Reveal + Copy, 없으면 기존 Reveal + Copy. `show_path_menu` 는 그걸 띄우기만. Tree 탭 · Expand 창 · A00210 Maya 탭 리스트가 같은 헬퍼라 모두 적용.
- 검증: 오프스크린 PySide6 + 임시 폴더 실제 `mklink /J` 18 항목 — origin_of 6 경우, 메뉴 문구 · 각 항목이 여는 경로(open_path 가로채기) · 툴팁 · 일반 폴더 메뉴 불변 · Copy · 정션을 거친 파일 · 트리 위젯에서 정션 항목 툴팁과 더블클릭. 마야/실기 탐색기 팝업 확인은 아직.
- 문서: `docs/A00240_PathTool.md` 더블클릭 · 우클릭 절, `docs/Framework_MOD_fileTree_qt.md`, CHANGELOG 01.21.

> [!summary] 메모 — **MEMORY.md 색인 압축: 항목마다 훅 한 줄, 상세는 각 메모 파일** (b1f4fba)
- `.claude/memory/MEMORY.md` 31.9KB -> 17.0KB. 메모 파일 링크 225개는 그대로, 긴 설명은 각 파일로. 코드 변경 없음.

> [!summary] A00210 FileManager — **창 크기를 가장자리로 자유롭게 조절** (v01.35->01.36)
- 문제(사용자): 가장자리를 끌어도 창 크기가 안 바뀐다. 원인: `QTabWidget` 최소 크기 = **숨은 페이지까지** 모든 페이지 최소의 최댓값(오프스크린 1752 x 1206 — File Manager 탭 세로 1032, Lineage 탭 가로 1726, Maya 탭은 842 x 660 으로 무관). 창이 최소에 붙어 못 줄이고, 화면만큼 크면 못 늘린다.
- 수정: 탭을 `QScrollArea` 에 담고(최소 266 x 213), 첫 showEvent 다음 루프의 `fit_to_content()` 가 예전 자연 크기를 모니터 작업 영역까지로 잘라 연다(A00480 v01.07 과 같은 길). 여는 크기는 그대로, 그 뒤 자유.
- 검증(오프스크린): 최소 작음 · 여는 높이 = 예전(화면 캡) · 600x400 축소 · 1400x900 확대 · Maya 탭 UI 14 항목 재통과. 실제 화면 확인은 사용자.

> [!summary] A00010 humanIKTool_V02 — **Mirror 탭: 컨트롤러를 할당한 캐릭터도 반대쪽 컨트롤러로 · 토큰은 공용 mirror_tokens.json** (v02.05->02.06)
- 요청: HIK 슬롯에 조인트가 아니라 +X 컨트롤러를 assign 하면 Mirror Joints 가 -X 컨트롤러가 아닌 조인트를 집는다 — `rules/mirror_tokens.json` 규칙대로 반대편 컨트롤러가 미러되게.
- 원인: `mirror_joints` 가 후보 풀을 `node_type="joint"` 로 못 박고 `Mirror in same root` 의 루트도 `top_joint`(조인트만)라 컨트롤러 캐릭터는 루트가 없고 조인트만 후보였다.
- `mirror_resolver`: `NODE_TYPE_SOURCE` = 소스와 같은 노드 타입(`ls -exactType` — transform 이면 조인트 제외) · `top_node` = 조인트면 최상위 조인트, 아니면 DAG 최상위 · 이름 토큰은 자체 표 대신 **`MirrorTokenStore.opposite_name`**(가는 방향의 출발 토큰이어야 후보). `hik_manager.mirror_definition` / `hik_roots`(옛 이름 별칭 유지), `custom_rig_manager` 도 NODE_TYPE_SOURCE. 버튼 `Preview / Mirror Definition`.
- 검증: mayapy 2024 + mayaHIK — 컨트롤러 캐릭터(ctrl_grp 아래, 같은 자리에 조인트 스켈레톤 + 동명 미끼) 4 슬롯 전부 반대쪽 **컨트롤러**(이름 3 · 위치 1, 같은 자리 조인트 미끼 안 집음) · undo · 조인트 캐릭터는 그대로 조인트 · same root 끄면 동명 ambiguous · 공용 토큰(`_l` `_L` `_lf` `Left`, `leftover` 는 없음, 반대쪽 토큰은 후보 없음) · UI 버튼 이름. 마야 GUI 확인은 아직.

> [!summary] A00170 driverTool — **AttachCrv Default: Distribute 모드 빈 공간 정리** (v01.32->01.33)
- 요청: Distribute New Drivers Evenly 모드에서 `Distribute new drivers uniformly` 그룹에 빈 공간이 너무 많다. 정렬·정돈.
- 원인: Objects 그룹(stretch 1)이 숨으면 남는 세로 공간이 늘어날 수 있는 QGroupBox 로 흘러들어 Distribute 그룹이 키만 커졌다.
- 고침: Distribute · Follower 그룹은 세로 size policy `Maximum`(sizeHint 높이만), root 끝에 trailing stretch 를 두고 `_atc_sync_mode` 가 Objects 가 보이면 0 / 숨으면 1 로 토글(Closest · Follower 는 Objects 리스트가 공간을 다 받고, Distribute 는 빈 칸이 아래로). 그룹 안은 HBox 한 줄 → 라벨 오른쪽 정렬 QGridLayout(한 줄에 하나, 값 위젯 폭 110 통일). Follower 그룹도 같은 모양.
- 검증: 오프스크린 PySide2(테마 입힘) 12 항목 — Distribute 그룹 높이 == sizeHint(190, 페이지 888) · 위젯 x/폭 정렬 · Closest/Follower 는 Objects 가 공간을 받고 마지막 위젯이 바닥 근처 · 모드 왕복. 마야 GUI 확인은 아직.

> [!summary] A00210 FileManager — **Maya 탭 > Reference: 마야 파일들의 레퍼런스를 트리로 보고 체크한 것을 각 파일에 임포트해 제자리 저장, 마야 일은 mayapy 워커** (v01.34->01.35) · A00240 Tree 탭을 Framework 로 승격 (v01.19->01.20) · A00480 은 원상복구
- 요청: 계획서 먼저(`docs/plans/A00210_FileManager_maya_reference_plan.md`, §12 사용자 결정 11개 · §13 재개용 진행표 · §14 이식). **처음 A00480_FileTool 에 만들었는데 사용자가 "실수, A00210 으로" 라고 바꿔** A00480 은 v01.09 로 되돌리고(커밋으로) `app/maya` 를 A00210 으로 옮겼다. 나중에 독립 툴로 뗄 수 있게 → `app/maya/{core,ui}` 한 폴더, 밖은 Framework · prefs 만.
- **A00210 은 standalone** → maya.cmds 가 필요한 일(.mb 읽기 · 임포트)은 `core/maya_worker.py` 를 mayapy.exe 로 띄워(`ui/mayapy_process.py` QProcess) 한다. stdout `JUNMSG {json}` 프로토콜(log/progress/result/error), 결과 json, Cancel = 플래그 파일(파일 경계) → 120초 뒤 kill. `.ma` 만이면 머리글 파싱으로 즉시(`scan(allow_open=False)` → `.mb` 를 만나면 `needs_maya`). mayapy 칸(Browse/Detect, 프로파일 `mayapy_path`). 워커는 에러 경로에서도 `uninitialize` 해야 종료 코드가 안 깨진다(0xC000000D). exe 는 `launch.spec` datas 로 `app/maya/core` 동봉.
- Framework: A00240 Tree 탭 + tree_scanner + prefetcher 를 `MOD_fileTree_qt_v01` 로 승격(A00240 은 re-export, 동작 동일) + `checkable_files`(파일 행 체크박스, 경로로 기억 · Expand 창 공유) · `default_types`. 트리용 다중 체크 동작 `MOD_checkTree_qt_v01`(checkList 의 트리 판 — **QTreeWidgetItem 은 기본 플래그가 checkable 이라 `CheckStateRole` 데이터로 판정**). Reveal / Copy file path 공용 `path_context.py`.
- core: `.ma` 는 머리글 `file -r` 문장(여러 줄) 파싱, `.mb` 는 `loadReferenceDepth none` 으로 열어 읽기, 중첩은 재귀(한 파일 한 번, 순환 가드). 임포트는 파일마다 백업(`backup/<이름>_REF_NN`, A00220 과 같은 폴더) → **기본 열기** → 체크된 레퍼런스 load/import → 올라온 중첩도 import → 모든 네임스페이스 병합(남는 레퍼런스 것은 건너뜀) → 원래 타입으로 저장. 실패 파일은 저장 안 함.
- 실측 함정: 언로드 레퍼런스는 import 에러(먼저 load) · 부모 import 시 중첩이 최상위로 올라온다 · **none 으로 열어 저장하면 체크 안 한 레퍼런스가 언로드로 굳는다**(처음 구현에서 File_03 의 fbx 가 사라졌다 → 임포트는 기본 열기로).
- UI: 공용 폴더 트리(ma/mb/fbx 기본) → Add Checked / Browse... → Maya File(공용 TSL) | Reference 트리(Reference | Used by, 중첩 접힘 · 체크 없음, 끊김 빨강) → Get Reference / Import Reference(확인 팝업 · 진행률 팝업). 옵션 Remove All Namespace · Backup 기본 ON.
- 검증: mayapy 2024 코어 샘플 41 + 실제 컨트롤 파일 2개 복사본(스캔 10s · 임포트 17s · 재열기 refs 0 · ns 0 · 원본 무수정) · 실제 mayapy 워커 왕복 17(스캔 · 임포트 · 재스캔 · 취소 · 에러) · 오프스크린 QTest 21(트리 체크) + 14(A00210 UI, 가짜 워커). A00210 GUI 에서 실제 mayapy 로 돌려 본 것은 아직.
- 문서: `docs/A00210_FileManager.md` §4-D 신설, `Framework_MOD_fileTree_qt.md` · `Framework_MOD_checkTree_qt.md` 신설, README · CHANGELOG(A00210 · A00240) · 포트폴리오 EN/KR · 메모 2개. A00480 문서 · CHANGELOG · 버전은 원래대로.

> [!summary] A00170 driverTool — **Seal Free 모드: 다물면 회전도 빌드 포즈로** (v01.31->01.32)
- 요청: Free 모드로 빌드한 뒤 Seal R/L 로 다물면 translate 는 기대대로인데, 입술 오브젝트의 회전을 바꾼 뒤 다물면 바뀐 회전이 그대로 남는다. 회전도 바꾸기 전 값으로 돌아가게.
- 원인: `build_seal` 이 `rotation_driven(null)`(rotate 에 연결이 있을 때)만 회전 pairBlend 를 끼웠고, `input_feed` 의 static 경로는 translate 만 `sealBase` 를 심었다. Free 모드의 정적 오브젝트는 rotate 가 그대로 자유 채널.
- 고침: `FREE_BASE_ROTATE_ATTR = "sealBaseRotate"`(doubleAngle3 — double 이면 unitConversion 이 끼어든다), `_ensure_base_attr(node, attr)` 일반화, `input_feed` 가 rotate 도 static 허용, `rotation_sealable(null, allow_static)` 로 Free 면 모든 드라이버에 `_rest_local_rotate` + pairBlend 회전. `_insert_pair_blend` 가 회전 feed 종류를 돌려줘 리포트 `static_rotated` 추가, UI 로그 한 줄. `_restore_input` 이 `sealBase`/`sealBaseRotate` 둘 다 값을 되쓰고 plug 단위로 삭제. Attached 모드는 불변.
- 검증: mayapy 2024 28 항목 — 정적 로케이터 10개(sealBaseRotate 고친 뒤 다물면 rest, 열면 바뀐 값, 절반 가중치는 사이, 머리 회전 불변, Update Rest Pose, Remove 되쓰기+attr 삭제) · JO 조인트(채널·월드 모두 rest) · pointConstraint translate + 정적 rotate 혼합 · `blend_rotation=False` · Attached 회귀. 마야 GUI 확인은 아직.
- 문서: `docs/A00170_driverTool.md` Free 모드 절 불릿 + 표, UI 툴팁/About. 포트폴리오는 손대지 않음.

> [!summary] A00060 jointTool_V03 — **Create > From Object `Match Rotation`** (v03.13->03.14)
- 요청: Separate 일 때 조인트가 오브젝트의 회전값과 일치하게 생기는 체크박스, 기본 꺼짐.
- `obj_joint_manager.joints_to_objs(..., match_rotation=False)` — separate 에서만, 조인트마다 `xform -ws -rotation` 으로 월드 회전을 주고 `makeIdentity -apply -rotate` 로 jointOrient 에 굳힌다(rotate 0). 컴포넌트(`.`)는 건너뜀. Connect 는 무시.
- UI: Connect/Separate 라디오 줄에 `Match Rotation` 체크박스, Separate 일 때만 활성(`buttonToggled`).
- 검증: mayapy 2024 — 회전·이동 그룹 아래 로케이터의 월드 회전 행렬 일치(jointOrient 65.3/-9.4/116.5, rotate 0), 월드 로케이터 (0,-30,0), 버텍스 0, 꺼짐 0, Connect 무시, UI 활성 전환 · 실행 · undo.

> [!summary] A00170 driverTool — **AttachCrv Default 탭 Mode 콤보 3개 + Create Followers at Live Closest Point** (v01.30->01.31)
- 요청: Default 탭에 모드 3개를 콤보로 — 기존 Attach to Closest Point · Distribute Drivers 를 두 모드로, 세 번째는 Objects 의 `obj_i` 마다 `sfc` 표면의 최근접 위치·회전에 새 `obj_attach_i` 를 만들고 `obj_i` 가 움직여도 최근접 지점을 따라가게. 제안대로 `closestPointOnSurface` 의 U/V 를 POSI 에 연결하는 구조.
- 모드 이름: `Attach Objects to Closest Point` / `Distribute New Drivers Evenly` / `Create Followers at Live Closest Point` (`attach_curve.ATTACH_MODES`). 모드별 위젯만 보이게(`_atc_sync_mode`) — Objects 는 Closest·Follower, Maintain offset 은 Closest 만, Distribute 그룹 · Follower 그룹(Follower Type · Name Suffix · 버튼)은 각자 모드만. Orient/Aim/norCrv/set 은 공유.
- 코어 `build_attach_followers`: `obj.worldMatrix -> decomposeMatrix -> closestPointOnSurface.inPosition`, `parameterU/V -> POSI.parameterU/V`(커브는 `nearestPointOnCurve.parameter -> POCI`), 나머지는 기존 `_attach_one` 네트워크 — `_attach_one(param_plugs=)` 로 파라미터를 상수 대신 플러그로 받게 확장. 팔로워 이름 `<obj 짧은 이름>_attach`, Locator/Null, 오브젝트는 안 건드림, 실패한 오브젝트의 노드만 치움.
- 검증: mayapy 2024 + 오프스크린 PySide2 48 항목 — 팔로워 위치 = 따로 구한 최근접 · X = tangentU · 오브젝트/부모/서피스/팔로워 부모를 바꿔도 유지 · Null·접미사·`-X`·커브+norCrv · undo 한 덩어리 · 회귀 · 콤보 가시성 · 핸들러. 마야 GUI 확인은 아직.
- 문서: `docs/A00170_driverTool.md` Default 절 Mode 표 + Followers 절, 포트폴리오 EN/KR 한 구절.

> [!summary] A00470 MaterialTool — **Check Names · Rename 한 줄 + Report Options 접이식(기본 접힘)** (v01.11->01.12)
- 요청: Check Names / Rename to Suggested 를 가로 한 줄로, Report 체크박스 셋을 접이식에 넣고 기본 접힘.
- Report `QGroupBox` → 공용 `JUN_mod_collapsible_qt_v01("Report Options", expanded=False)`, 체크박스는 `body` 에 그대로. 접혀 있어도 `isChecked()` 는 살아 있어 Check Names 가 기본값(클립보드 복사 켬)으로 동작. 두 실행 버튼은 `QHBoxLayout`.
- 오프스크린 teal_dark 실측: 탭 최소 높이 750 → **641px**(접힘) / 709px(펼침), 버튼 30px 유지, 두 버튼 같은 y. 46항목 회귀 통과. 마야 GUI 확인은 아직.

> [!summary] A00145 RigConnect — **Connect 52 Facial Target 버튼 → 규칙 json `Connect by Rule`** (v01.58->01.59)
- 요청: 버튼을 없애고 정해진 연결을 규칙 json 으로 관리. 첫 규칙 `Apple ARKit 52 Facial Target` 이 예전 버튼과 같은 연결을 하도록, 규칙이 늘어날 것을 염두.
- `app/rules/connect/<rule>.json` 파일 하나 = 규칙 하나(`name` / `description` / `attributes` 같은 이름 / `pairs` 다른 이름). 코드의 `FACIAL_52` 목록을 json 으로 뽑아 `apple_arkit_52_facial.json` 으로, `connect_manager.connect_52_facial` 은 지움.
- `app/core/connect_rules.py`: `load_rules()`(이름순, 깨진 파일은 errors 로) · `find_rule` · `connect_by_rule`(행 순서 1:1, 없는 attr 스킵 — MEL 동작 그대로). UI 는 Connect 페이지 `Connect by Rule` 그룹(Rule 콤보 + Reload + Connect by Rule), 콤보 툴팁에 설명 · 짝 수 · 경로.
- 검증: mayapy 2024 — 규칙 52 짝 로드, 깨진/모양 틀린 json 은 errors · attributes+pairs 혼합 정규화, 오브젝트 2:1 에서 51 연결 1 스킵, 오프스크린 UI 콤보 · Reload · 연결 · undo.

> [!summary] A00470 MaterialTool — **Name Check 버튼 글자 잘림 수정 · Sort / Reverse / List Materials 한 줄** (v01.10->01.11)
- 요청: Select Materials / Select Faces 세로가 작아 글자가 안 보임. Sort · Reverse · List Materials 를 가로 한 줄로, 바꾼 뒤 세로가 줄었는지 확인.
- 원인(오프스크린 teal_dark 실측): 테마 버튼 sizeHint 30px 인데 `setMinimumHeight(26/28)` 이 바닥을 낮춰, 창(520x820)이 탭 내용(최소 816)보다 작을 때 레이아웃이 그 버튼들만 26/28 로 눌렀다. 탭 버튼의 명시 최소 높이를 전부 제거 → 8개 모두 30px.
- 한 줄: TSL 레이아웃에서 `btn_sort`/`btn_reverse` 를 `removeWidget` 으로 빼내 `List Materials` 와 QHBoxLayout 에 담고 TSL 안 맨 아래에 붙임(그룹 안 유지). Sort/Reverse/List 클릭 동작 확인.
- 결과: 탭 최소 높이 **816 → 750px**(−66), 창 minimumSizeHint 1109 → 1043. 46항목 회귀 통과. 마야 GUI 확인은 아직.

> [!summary] A00400 CurveTool — **Shape Edit: 레퍼런스 커브의 셰이프 수정이 저장 후에도 유지** (v01.24->01.25)
- 요청: Display > Shape Edit 으로 레퍼런스 커브의 셰이프를 고치고 저장 → 다시 열면 반영이 안 됨. 레퍼런스 커브도 고쳐지고 저장 후에도 유지되게.
- 원인: `shape_xform_manager._write_points` 가 `cmds.curve -replace` 로만 썼다. 이 명령은 레퍼런스 셰이프에서 그 세션에만 먹고 레퍼런스 edit 로 기록되지 않는다([[referenced-curve-cv-write]] — Replace 탭은 v01.22 에 이미 우회).
- 고침: 셰이프마다 `referenceQuery -isNodeReferenced` 로 보고 레퍼런스면 `xform(cv, objectSpace, translation)` 으로 CV 하나씩(절대 위치 · 레퍼런스 edit · undo 한 스텝), `ls(shape.cv[*])` 개수까지만(주기 커브 클램프 함정). 로컬 커브는 `curve -replace` 그대로. Apply 와 라이브 세션(preview/settle/restore) 모두 같은 `_write_points` 를 지나므로 둘 다 고쳐짐.
- 검증: mayapy 2024 — 열린 3차 · 히스토리 있는 원 · 1차 사각 · 셰이프 2개 컨트롤을 레퍼런스로, Apply + 라이브 세션 → 저장 → 재열기 → 재편집 → 저장 → 재열기, 25 항목 통과(수정 전 코드는 재열기 5 항목 실패). 마야 GUI 확인은 아직.
- 문서: `docs/A00400_CurveTool.md` Shape Edit 알아둘 것 + Replace 절 문구. 포트폴리오는 손대지 않음(버그 수정).

> [!summary] A00470 MaterialTool — **Name Check: Select Materials / Select Faces + Listed meshes only** (v01.09->01.10)
- 요청: 레거시 `JUN_PY_ShaderTool_V01_04.py` 의 Select Shader / Select Faces 를 Name Check 탭에 이식. UI 안 셋(표 아래 한 줄 · Selection 그룹박스 · 표 오른쪽 세로 버튼 열) 중 **표 아래 한 줄**, 페이스 범위는 **체크박스 토글 기본 ON** 으로 사용자가 골랐다.
- 표 아래 `[Select Materials] [Select Faces] ☑ Listed meshes only`. 고른 행이 대상, 아무 행도 안 골랐으면 표 전부(로그로 알림). 더블클릭 동작은 그대로(같은 `select_materials`).
- `core/maya_materials.py`: `faces_of(materials, meshes|None)` = 머티리얼 → 셰이딩 엔진 → `sets -q` 멤버(마야가 `f[0:199]` 구간으로 압축해 준다) → 범위 안 메시 셰이프만, 오브젝트째는 `shape.f[*]`. `select_faces` 는 **API `MGlobal.setActiveSelectionList`**(인덱스 → `MFnSingleIndexedComponent`) — 4만 면 체커보드에서 `cmds.select(문자열 2만)` 1.4초 → 0.001초, 실패 시 `cmds.select` 폴백. 레거시 `select(SG)` 는 씬 전체 + 오브젝트째 배정은 오브젝트가 선택되던 것을 둘 다 고쳤다.
- 실측 함정: **`sets -q` 면별 멤버는 트랜스폼 기준**(`sphere.f[0:199]`) → 셰이프로 풀어 비교(노드별 캐시 없으면 2만 멤버에 2.3초). 셰이프 둘인 트랜스폼의 `t.f[0:2]` 배정은 두 셰이프 모두. **면을 전부 재배정한 메시는 `initialShadingGroup` 연결이 남아** `listConnections` 에 보이고 `listSets` 엔 없다 → `shading_engines()` 가 멤버 있는 엔진만 남기도록 고침(쓰지 않는 `standardSurface1` 가짜 행 제거).
- 검증: mayapy 2024 + 오프스크린 Qt 46항목 — 통째/면별/NURBS 제외/네임스페이스/빈 리스트/SG 없는 머티리얼/A+B/체커보드 2만/API == cmds 결과/셰이프 2개/UI(버튼·기본값·행 없음=전부·범위 토글·더블클릭). 마야 GUI 확인은 아직. 문서 `docs/A00470_MaterialTool.md` §1.2.

> [!summary] A00145 RigConnect — **Connect > Transfer Connection 하위 탭 (연결 전이)** (v01.57->01.58)
- 요청: A.attr_01 ↔ Tgt.attr_tgt_n 연결을 끊고 같은 이름 attr 을 가진 B.attr_01 ↔ Tgt.attr_tgt_n 으로 옮기는 기능. Source 어트리뷰트 목록(Channel Box Only / Connected Only, 체크박스, 전체 체크/해제) → 연결된 노드 목록(체크박스) → Destination → Transfer. upstream/downstream 둘 다. 불필요·중복 UI 는 제안하라고 했다.
- 제안해 반영한 것: ① "A·B 공통 어트리뷰트" 목록을 따로 두지 않고 Destination 을 담는 순간 어트리뷰트 목록에서 **없는 행을 빨갛게**(툴팁에 누가 없는지) — 같은 집합을 두 번 체크할 일이 없다. ② List UpStream / DownStream 두 버튼 대신 **Direction 체크박스 둘 + List Nodes 하나** — 두 방향이 한 목록에 들어 한 번의 Transfer 로 양쪽을 옮긴다(노드 행 `drives: attr_02    driven by: attr_01`).
- `app/core/connection_transfer_manager.py`(UI 비의존): `connections_of` = `listConnections -c -p -shapes`(-shapes 없으면 쉐입이 트랜스폼 이름으로 바뀜, blendShape 타겟은 별칭 이름으로 나와 list_attrs 와 맞음), `list_rows`(합집합 · 연결 수), `list_nodes`, `missing_on`, `pair_objects`(목적지 1 = 전부, 같은 수 = 행 순서), `transfer`(먼저 목적지에 잇고 Source 를 끊는다 · 목적지가 이미 다른 것에 구동되면 건너뜀 · downstream 은 `connectAttr -force` 한 번).
- UI: 체크 목록은 공용 `JUN_mod_checkList_qt_v01`, 행 값은 UserRole(표시 글과 분리), Destination TSL 의 model 신호로 빨강 재칠(QTimer 로 한 번), 옮긴 뒤 두 목록 재조회(체크는 이름으로 유지), `undo_chunk` 하나.
- 검증: mayapy 2024 — 코어(down 2 + up 1 전이, 체크 안 한 노드 유지, 목적지 충돌 건너뜀, undo, blendShape 별칭 행) · 오프스크린 UI(teal_dark) 탭 4개, 목록/옵션 토글/노드 행/빨강 표시/전이/재조회/빨강 해제/undo/행 클릭 씬 선택, 페이지 최소 폭 1189(Pair 1203 보다 좁음). 마야 GUI 확인은 아직.

> [!summary] A00170 driverTool — **AttachCrv: jointOrient 가 있는 조인트도 로케이터와 같게 회전** (v01.29->01.30)
- 요청: Default 탭에서 로케이터와 조인트를 같은 자리에 Orient + Attach to Closest Point 로 서피스에 붙이고 서피스를 변형하면 둘이 다르게 돈다(조인트 JO ≠ 0). 조인트도 로케이터와 같은 값으로 돌게.
- 원인: 네트워크가 `decomposeMatrix.outputRotate` 를 조인트 `rotate` 에 그대로 넣었다. 조인트 로컬 회전은 `R × JO` 라 프레임 뒤에 JO 가 다시 얹힌다(JO = 0 이면 같아서 안 보였다).
- `attach_curve._attach_one`: 조인트면 `rotate = rot(M) × JO⁻¹` — translate 는 기존 dcm 그대로 두고 rotate 만 `_atc_rotMMX(× JO⁻¹) → _atc_rotDCM` 에서 뽑는다(JO⁻¹ 를 오른쪽에 곱하면 translate 가 돌아가므로 분리). JO⁻¹ 는 seal v01.29 와 같이 **각 음수 + zyx composeMatrix**(라이브 — JO 를 나중에 고쳐도 따라감). `_local_matrix_from_channels` 도 조인트면 `R0 × JO` 를 넣어 Maintain offset 빌드 순간 제자리.
- 검증: mayapy 2024 — 같은 자리의 로케이터/조인트(JO (23,−41,67), rotate (10,20,30)) 서피스·커브 × `±X` × Maintain ON/OFF × rotateOrder zxy/yzx × 회전한 부모, 어태치 직후·변형 뒤·JO 를 바꾼 뒤 **월드 회전/위치 동일**, JO=0 회귀, orient OFF, Distribute — 85 항목 통과. 수정 전 코드에서는 같은 테스트 30 항목 실패(테스트가 버그를 잡는다). 마야 GUI 확인은 아직.
- 문서: `docs/A00170_driverTool.md` Maintain offset 절의 "조인트는 널에 붙이는 편이 안전하다" 문장을 v01.30 동작으로 교체. 포트폴리오는 손대지 않음(버그 수정).

> [!summary] A00120 FKIK — **Setup 칸 높이를 v01.10 으로 되돌림** (v01.11->01.12)
- 요청: v01.11 뒤 Setup 칸 세로가 길어졌다 — 기존과 같게.
- 원인(오프스크린 실측 108 → 166): Manual/Auto 라디오 행(36) + Auto 리스트를 헤더 있는 공용 TSL 로 만든 것(22). 테마의 라디오는 패딩·테두리가 있는 버튼 모양이라 라디오와 버튼을 세로로 겹쳐도 50px 안에 못 든다.
- 한 줄 `[리스트(50 고정)] (Manual) (Auto) [Select Objects | Refresh]` — Auto 리스트는 일반 `QListWidget`(툴팁으로 설명), 버튼은 모드에 맞는 하나만 `setVisible`. `_selected_texts` / `_select_list_text` 헬퍼로 TSL 호출을 대체.
- 검증: mayapy 2024 오프스크린(blue_dark) — 옛/새 Setup 둘 다 108, Auto 전환 시 Refresh 버튼·빈 씬 상태 메시지, Manual 복귀, 리스트 행 선택으로 단위 로드. 마야 GUI 확인은 아직.

> [!summary] README — **Portfolio (Web) 링크를 Notion 포트폴리오 페이지로 교체** (f48db0b)
- 루트 `README.md` 의 Portfolio (Web) 링크 한 줄만. 코드 변경 없음.

> [!summary] A00240 PathTool — **Junction 탭(Create / Remove) + Tree 정션 연한 빨강** (v01.18->01.19)
- 요청: `cmd /c mklink /J` 를 UI 로. 소스/타깃 선택 UI, 두 리스트로 n->1 · n->n, 원본은 두고 정션만 안전 삭제, Tree 에서 정션은 연한 빨강. 요청 번호 배치는 1·2·3(생성) = Create, 4(삭제) = Remove 로 읽었다.
- `core/junction.py`(UI 비의존): `is_junction` = lstat 리파스 태그(`islink` 는 정션에 False, `isjunction` 은 3.12+), `plan()` 이 행마다 ready/사유(파일 · 없음 · 이미 있음 · 자기 안 순환 · 중복), `create_junction` = subprocess mklink(CREATE_NO_WINDOW, oem 디코드) 뒤 되읽기, `remove_junction` = 정션 확인 후 `os.rmdir`(빈 실제 폴더도 지우는 명령이라 확인이 전부), `find_junctions`.
- `ui/junction_tab.py`: 공용 TSL 에 Add.../Paste/드롭을 얹은 `_PathList` 둘 + 미리보기 표 + Create → 만든 정션은 Remove 탭에 자동 담김. Remove 는 Junction|Target 표(정션 아니면 빨강·건너뜀) + Scan + 확인 다이얼로그.
- Tree: `tree_scanner` 가 scandir stat(follow_symlinks=False) 로 `junction`/`target` 을 노드에 적고(추가 디스크 접근 없음), `_walk` 는 실제 위치를 따라가며 자기 조상을 가리키는 정션은 안 내려간다(Depth All 이 끝난다). `tree_tab` 은 아이콘을 SourceAtop 으로 물들이고 글자색 `#f08a8a`, 툴팁 `Junction -> 타깃`.
- 검증: 오프스크린 PySide6 — plan 사유 7종, 생성/삭제(원본 파일 유지), n->1 · n->n(타깃=정션 경로), 실제 폴더 섞어 Remove 해도 안 지움, Scan, Tree 색/툴팁/Omit 과 조합/순환 정션. 창 최소 폭(오프스크린) 887 → 940.

> [!summary] A00170 driverTool — **Seal 탭 Free 모드**: 어태치 없는 트랜스폼도 지퍼로 다문다 (v01.28->01.29)
- 요청: Build Seal 이 커브/서피스 어태치 드라이버에만 동작(`found 0 / 0`). 기존 동작은 그대로 두고 **다른 모드**로 어태치 없는 오브젝트도 되게.
- 판단: 어태치는 ① 입술 위 u ② 다물리기 전 라이브 위치 ③ pairBlend 끼울 연결 세 가지만 공급 — 셋을 대체하면 지퍼 계산은 그대로 쓸 수 있다.
- `Mode` 콤보 `Attached (curve / surface)` / `Free (any transform)`. Free = 담은 트랜스폼이 곧 드라이버. u = Corner Axis 위치를 **Reference 공간**에서 양쪽 합집합 양 끝으로 0~1(월드로 재면 머리가 기운 포즈에서 짝이 한 칸 밀렸다 — 실측).
- 연결 있는 노드(컨스트레인트 · 키)는 **축별** 플러그로 받는다 — 컴파운드 `listConnections(node.translate)` 는 자식 연결을 안 돌려주고, 컴파운드를 force 로 이어도 자식 연결이 남아 두 소스가 다툰다(실측, 먼저 끊는다). 연결 없는 정적 노드는 `sealBase` double3 를 심어 소스로(자기 어트리뷰트 → 자기 translate 는 사이클 아님).
- 조인트 직접 다물기: rest 회전 `R = local × JO⁻¹` — `inverseMatrix` 는 matrixNodes 플러그인 노드라 **각 음수 + zyx 순서 composeMatrix** 로 대체.
- Remove 는 축별/sealBase 까지 되돌림. 검증 mayapy 52(정적 · JO 컨스트레인트 조인트 · X 키 · Attached 는 HEAD 와 월드 행렬 동일) + UI 오프스크린 19, 전부 통과.
- 문서: `docs/A00170_driverTool.md` Free 모드 절, 포트폴리오 EN/KR 3-4 한 단락.

> [!summary] A00120 FKIK — **Setup Manual / Auto · 접이식 리스트 · Dev Mode · Bake 진행률 팝업** (v01.10->01.11)
- 요청: Setup 을 Manual(Select Objects) / Auto(Refresh 로 씬을 네임스페이스 단위 조사) 로, Targets/Followers 는 접이식(기본 접힘) · Search 는 코드만 두고 숨김, A00330 의 Dev Mode 메뉴를 공용 위젯으로 올려 FKIK 도 쓰기, 배포 화면(Auto 기본 · 리스트 없음 · Bake (Constraint) 없음 · 로그 접힘 · Force Refresh 없음), Bake IK/FK 진행률 팝업.
- Auto : `app/core/fkik_scan.py` `FKIKScanner.scan` — `ls("*BlendFKIKPos_grp*", recursive=True)` 로 모든 네임스페이스에서 찾아 네임스페이스마다 `FKIKSetup.resolve(톱 노드들)`. 한 네임스페이스에 리그가 여럿이면 톱 노드마다 `(root) | rigB_grp` 로 나눈다. 검증에 걸린 리그는 `[WARN] Skipped`. Auto 로 바꾸는 순간에도 조사하고, Refresh 는 전에 고른 단위를 유지한다. 리스트는 공용 TSL(버튼 없음 · `attach_uuids=False`).
- 화면 : `apply_view(developer)` 하나가 다섯 가지를 숨기고 보인다. 창 높이는 `showEvent`(테마 입힌 뒤) 와 토글 · 전환 뒤 `sizeHint` 로 다시 잡고 화면 작업 영역 높이로 자른다(창이 화면을 넘으면 로그창 잔상이 남는 함정 대비).
- Bake : `FKIKMatcher.bake(..., progress=None)` — 프레임마다 콜백, UI 는 `JUN_mod_progress_qt_v01` 단계 하나.
- 검증: mayapy 2024 오프스크린 — 합성 리그 3개(네임스페이스 1 + 루트 2) 조사 → 단위 3개 · 각 24/24, Release 전환 시 Auto 라디오 · 숨김 다섯 가지 · 창 660→520, 접이식 펼침 902, bake 5 프레임 콜백 6회 · 팝업 경로로 120 프레임. 마야 GUI 확인은 아직.

> [!summary] Framework — **`Dev Mode` 메뉴 공용 위젯 `JUN_mod_devMode_qt_v01` + 판정 `Framework/core/dev_mode.py`** (신규)
- A00330 v01.26 `_build_dev_mode_menu` 를 `Framework/qt/MOD_devMode_qt_v01.py` 로. 개발자 모드에서만 메뉴(Help 오른쪽, QMenu 직접 addMenu), `modeChanged(bool)` · `set_developer()` · `is_developer()`. 화면 전환은 툴의 일.
- 판정은 A00330 `app/config/dev_mode.py` 규칙 그대로를 `Framework/core/dev_mode.py` 로 — `is_dev_mode(tool_file)` (릴리즈본 = 툴 안에 Framework 동봉 → False, dev = `JUN_All/config.py` 의 `DEV_MODE` 를 경로로 읽음). 툴 폴더는 `tool_menu.tool_dir_from_path`.
- 문서 [`Framework_MOD_devMode_qt.md`](Framework_MOD_devMode_qt.md), README 표 한 줄. `Framework/qt/__init__` 별칭 `JUN_mod_devMode_qt`.

> [!summary] A00330 NamingTool — **Dev Mode 메뉴를 공용 위젯으로 교체** (v01.26->01.27)
- `_build_dev_mode_menu` 가 `JUN_mod_devMode_qt_v01` 을 만들고 메뉴 <-> Token 위젯 `rules_editable` 을 양방향으로 잇는다. `app/config/dev_mode.py` 는 공용 판정을 부르는 껍데기(이름 유지).
- 검증: mayapy 오프스크린 — 메뉴 → 탭 숨김 · 규칙 잠금, 위젯 → 메뉴 체크, `act_release.trigger()`. 모양 · 동작은 v01.26 과 같다.

> [!summary] A00410 SecondaryMotion — **자식 없는 컨트롤러/조인트도 혼자 찰랑이게: Virtual Child** (v01.10->01.11)
- 요청: 자식이 없는 컨트롤러 하나를 TSL 에 올리고 Apply 하면 키가 전혀 안 찍히고, 자식 컨트롤러를 붙여야 회전함 -> 자식이 없어도 있는 것처럼 찰랑이게. 가상 자식의 축·거리는 사용자 UI 로. 조인트도 같으면 같이.
- 원인: `resolve_chains` 가 노드 2개 미만이면 체인을 안 만들고, 가상 팁(`Rotate last node`)은 마지막 뼈를 **연장**하는 방식이라 뼈가 없는 단일 노드엔 방향이 없었다. 조인트도 같은 경로.
- `Virtual Child` 박스(Axis `+X..-Z` 콤보 + Length 스핀, 기본 +X 10). 단일 노드 체인(Bone Chain 홀로 / Bone Root 자손 없음)에 노드 로컬 `offset * worldMatrix` 점을 프레임마다 붙여 2점 체인으로 푼다 — 그 노드 회전만 기록. 자식이 있는 노드는 무영향, Length 0 = 끔(예전 동작). 바꾸면 재샘플링.
- 검증(mayapy 2024, 33 항목): 단일 컨트롤러(부모 회전 + RA + rotateOrder) · 단일 조인트(JO 20/-35/50 + RA + yzx) 왕복 오차 5e-14 / 9e-15, 이동만으로도 흔들림(Length 길수록 각도 감소), 2노드 체인 무회귀 1e-12, Layer 승격 · Bake Keys · UI 콤보/스핀/캐시 무효화/로그. 마야 GUI 실기는 아직.

> [!summary] A00240 PathTool — **Tree 탭 Omit: 루트 아래 N 단계를 `...` 한 줄로 생략** (v01.17->01.18)
- 요청: `A/B/C/D/E` 에서 Omit 2 면 `A / ... / D / E`, 3 이면 `A / ... / E` 로 — 늘 같은 고정 경로를 건너뛰고 본다. 2 이상의 정수 입력 UI.
- Refresh 행 오른쪽에 `Omit` 체크 + 스핀(2~99). 루트 항목 아래 `...` 하나(경로 없음, `ROLE_OMIT`)를 달고 N+1 단계의 폴더·파일을 전부 그 밑에 모은다 — 가지가 여럿이어도 `...` 은 하나, 툴팁에 루트 기준 상대 경로.
- Adaptive 면 생략 단계는 펼칠 수 없으니 `_ensure_omit_loaded()` 가 0~N 단계를 항목 만들기 전에 읽는다(새 확장자를 File Types 에 먼저). `...` 아래 폴더는 평소처럼 선읽기. 펼침·선택 상태는 `_item_key()` 로 `...` 도 적어 Refresh 뒤에도 열린 채. 생략 단계 안 폴더를 Refresh 하면 루트 자식을 통째로 다시 만든다.
- 검증: 오프스크린 PySide6 — Omit 2/3 결과, 가지 여럿 모으기, Filter(`...` 는 글자로 안 맞음), Refresh(루트 · `...` 밑 파일 Selected), Show files, Adaptive 끈 Depth All, Expand 창. 처음엔 0~N-1 단계만 읽어 `...` 밑이 비었다 — N 단계까지 읽어야 그 자식이 보인다.

## 2026-10-02

> [!summary] A00010 humanIKTool_V02 — **Assign Joints 직후 HumanIK 창 즉시 갱신** (v02.04->02.05)
- 요청: Assign Joints 뒤 HumanIK 창이 Definition 탭을 보고 있어도 갱신이 안 돼 Controls 로 갔다가 돌아와야 보임 -> 버튼 누르면 바로 보이게.
- 원인: `assign_joints` 에 HIK 창 갱신 호출이 없었고, Mirror 의 `hikUpdateDefinitionUI` 단독 호출은 현재 캐릭터를 씬에서 다시 읽지 않는다. 탭 전환은 `hikUpdateCharacterControlsUI(false)` 를 탄다(Maya 2024 `hikCharacterControlsUI.mel` 확인).
- `refresh_hik_ui()` = `hikUpdateCharacterControlsUI(false)` 즉시 + `hikUpdateCharacterControlsUIEvalDeferred()`, 둘 다 `exists` 확인 후. Assign · Mirror 공통.
- 검증: 컴파일만. 마야 GUI 에서 HIK 창을 띄운 확인은 아직.

> [!summary] A00240 PathTool — **Tree 탭 백그라운드 선읽기 + 빈 폴더 화살표 미리 제거** (v01.16->01.17)
- 요청: v01.16 보고의 개선안 1(선읽기) · 2(빈 폴더 미리 확인) 추가.
- `core/prefetcher.py` 신설 - 작업 스레드 4 개, LIFO(최근 요청 먼저), 세대(`reset`)로 이전 빌드 결과 폐기. Qt 비의존.
- UI: Build · 펼치기 · Refresh 때 보이는 안 읽은 하위 폴더를 요청(한 단계 앞만, 폴더당 2000 개 상한), 50ms 타이머가 틱마다 결과를 모아 캐시 · 항목에 반영. 자식을 미리 달아 두므로 빈 폴더 · 다 걸러지는 폴더는 화살표가 사라진다(2번은 1번의 부산물).
- 검증(PySide6 offscreen): 빈 폴더 화살표 선읽기 전 있음 -> 후 없음, 한 단계 앞만, 펼치면 다음 단계 선읽기, Show files 끄면 파일만 있는 폴더 화살표 없음, 연속 Build 이전 결과 폐기, 폴더 300 개(각 20 하위) 선읽기 0.14 초 · 그 뒤 펼치기 0.0001 초. v01.16 테스트 전부 재통과, MainWindow 생성 OK.

> [!summary] A00240 PathTool — **Tree 탭 Adaptive(펼칠 때만 읽기) + 더블클릭 탐색기 열기** (v01.15->01.16)
- 요청 1: Depth 를 크게 두면 Build 가 오래 걸림 -> `Adaptive` 체크(기본 켬) 시 Build 는 루트 한 겹만, 폴더를 펼칠 때 그 폴더 한 겹만 읽고 재귀적으로 반복. 끄면 예전처럼 Depth 까지 미리. Shift + 펼치기는 아래 전부 읽기.
- `tree_scanner.build_tree_lazy()` / `scan_children()` + 폴더 노드 `loaded` 플래그, UI 는 경로->노드 색인(`_reindex`) - 매번 캐시 훑기는 Shift 펼치기에서 제곱(폴더 6천 개 16 초). Refresh 는 읽은 폴더만(`_rescan_lazy`), Filter 는 읽은 범위 안에서만.
- 새 확장자는 항목을 만들기 **전에** File Types 에 넣는다 - 일부만 체크한 상태에서 펼친 폴더의 새 확장자 파일이 숨던 문제.
- 요청 2: 더블클릭 = 탐색기에서 열기(Reveal 과 같음), 더블클릭 펼치기는 끔.
- 검증(PySide6 offscreen, 8^4 폴더 · 약 1만 노드): Adaptive Build 0.001 초 vs Depth All 0.23~0.35 초, 펼치기 = 한 겹, 손자 미로드, 부분 확장자 필터 + 새 `.fbx` 표시, Shift 전체 펼치기 9947 노드 0.6 초, Refresh Recursive 로 새 폴더 반영 · 펼침 유지, 더블클릭 -> reveal 호출 · 안 펼쳐짐.

> [!summary] A00010 humanIKTool_V02 — **Bone Chain 콤보 순서 정리** (버전 변경 없음)
- `BONE_CHAINS` 키 순서만: Spine, Neck to head, 왼쪽(팔 / 손가락 / 다리), 오른쪽. 슬롯 ID 는 그대로 - 순서는 Assign 탭 Bone Chain 콤보 표시에만 쓰인다.
- 검증(mayapy 2024): 8 체인 모두 할당 슬롯 일치, Selected Chain 미러 정상.

> [!summary] A00010 humanIKTool_V02 — **Neck to head 하나로 + Mirror in same root** (v02.03->02.04)
- 요청 1: Neck 1 / Neck 2 to head 를 없애고 Neck to head - 리스트 앞 n-1 개 = 목 체인, 마지막 = 머리. `chain_slots(label, n)` 이 Neck(20) · Neck1~9(32~40) 중 앞 n-1 개 + Head(15), 목 10 개 초과는 경고.
- 요청 2: Mirror `Mirror in same root` 체크 - 켜면 HIK 할당 조인트의 최상위 조인트(부모가 조인트인 동안 올라감) 아래만, 끄면 씬 전체 조인트(동명 여럿이면 ambiguous). `MirrorResolver(search=ROOTS|SCENE, roots)`, 컨트롤러 미러는 예전 그대로(HIERARCHY).
- **덤으로 찾은 버그**: 찾은 조인트를 짧은 이름으로 setCharacterObject → 동명 조인트가 있으면 `No object matches name` 으로 할당 실패. 풀 패스로 할당 · 비교(`_same_node`).
- 검증(mayapy 2024 + mayaHIK, 같은 이름 스켈레톤 두 벌): Neck 4 개 -> Neck · Neck1 · Neck2 · Head, 1 개 -> Head, 12 개 -> 경고 / same_root 켬 -> charA 의 R_* 3 개 이름 매칭 · 적용 성공 · 재실행 skip, 끔 + Name -> ambiguous, 끔 + Auto -> 위치. 체크박스는 Options 둘째 줄(한 줄이면 최소 폭 1008 -> 1362).

> [!summary] A00480 FileTool — **Naming 토큰에 Enum + 토큰 규칙 공용화(`COMMON_RULES`)** (v01.08->01.09)
- 요청: A00480 Token 에도 Enum, A00330 과 같은 규칙을 다른 툴도 함께 쓰는 공용 규칙으로.
- `Framework/core/token_naming.py`: `COMMON_RULES = (Custom, Enum, Numbering)` 신설, `TokenRuleSet` 기본값. `MAYA_NODE_RULES = COMMON_RULES`, `FILE_NAME_RULES = COMMON_RULES + Set's Name`.
- 검증: A00330 규칙 그대로, A00480 콤보 Custom / Enum / Numbering / Set's Name, `names_for` -> `SK_SIN_Set008_grp_001`, Enum 값에 파일명 금지 문자 검사(`a:b` 막음, `a-b` 통과), 위젯 Enum 칸 · Values... 표시.
- A00330 릴리즈의 Framework 사본도 같은 파일로(동작 차이 없음). A00480 은 릴리즈 저장소에 없다.

> [!summary] A00330 NamingTool — **Dev Mode 를 메뉴 바로 (Help 오른쪽)** (v01.25->01.26)
- 요청: Dev Mode 버튼을 툴 맨 위 Help 메뉴 오른쪽의 별도 메뉴로, 메뉴에서 모드를 고르게.
- `Dev Mode` 메뉴 = 배타 QActionGroup `Developer` / `Release (shared tool)`, 개발자 모드에서만 생성. 공용 메뉴 바 `addMenu("제목")` 은 Help **왼쪽**에 끼우므로 QMenu 를 직접 넘겨 오른쪽에. Tokens 줄 토글 버튼은 제거(mode_toggle=False).
- 검증(mayapy 2024): dev 메뉴 순서 Help, Dev Mode · Release/Developer 전환 시 탭 · 버튼 따라감 · 코드 전환 시 체크 동기, 임시 배포본은 Help 만. 메뉴 캡처.

> [!summary] A00330 NamingTool — **Position 슬라이더 색을 brown_dark 테마로** (v01.24->01.25)
- A00110 의 파란 슬라이더 색 -> brown_dark.qss 값: 홈 #38352f + 테두리 #ad9276(입력칸), 손잡이 #9c8266 / hover #ad9276 / 누름 #856e55(버튼). 캡처 확인.

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
