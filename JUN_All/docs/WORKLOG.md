---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-10-13
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

## 2026-10-13 (오늘)

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
