---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-06-19
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-06-19 (오늘)

> [!summary] 신규 툴 A00240 PathTool — 경로 런처(카테고리·우클릭 편집·순서 변경·집/회사 프로파일) + Tree 탭(경로 트리뷰·깊이/파일/확장자 필터·Expand·우클릭 Reveal·폴더/파일 아이콘, v01.02)·버튼 Change Category(v01.03, standalone PySide6) + A00145 RigConnect Match 탭 신설(MEL Match Tool V05.04 이식·리팩토링, v01.03)·Constrain 탭에 Skin Weight to Constraint 추가(v01.02, 접이식) + A00220 BackupTool Settings 접이식화·창 슬림(v01.03)·스핀박스 화살표 PNG 복구·백업 log.txt(v01.02)·상태 표시를 Chrome Dino 애니메이션으로(v01.04)·Auto Backup 저장 즉시 백업(v01.05) + A00110 animTool Follow 탭 강화(Maintain Offset · 1<-n · Get Current) + A00110/A00120 뷰포트 프리즈(refresh suspend 누수) 수정 & Force Refresh 버튼 + A00210 FileManager Lineage 노드 로그 동기화(v01.08)·노드/연결 삭제 & 다중선택(v01.09)·러버밴드 intersect 선택(v01.10)·File Manager Show Recorded Only 필터(v01.11)·Load Image 시작 경로 thumbs 폴더(v01.12)·Settings Branch 편집형 드롭다운(v01.13)·검색/확장자/Recorded 필터 & 우클릭 Show in File Explorer & Log history Expand(v01.14) + Framework dark 테마 Win10 트리 행 가독성
- **A00230_StartupTool 부팅 시 툴 자동 실행 확장**: 기존 "부팅 시 폴더 팝업" 런처를 **폴더 + standalone
  툴 자동 실행**으로 확장. 신규 부팅 코디네이터 `startup.py` 가 `config/startup.json`(기존 `folders.json` 대체,
  `folders` + 신규 `tools` 배열)을 읽어 폴더를 탐색기로 팝업한 뒤 각 툴의 `launch.py` 를 `pythonw` **분리
  프로세스**로 실행(프로세스 분리로 `tools.<tool>.app.*` 패키지 충돌 없음). 기본 등록: A00210 FileManager ·
  A00220 BackupTool · A00240 PathTool. **새 툴 추가는 `tools` 에 `{ "tool": "A002NN_XXX", "enabled": true }`
  한 줄**(표준 위치 밖은 `launch` 경로 override) — 재설치 없이 다음 부팅에 반영. `install.py` 런처(.vbs)가
  `startup.py` 를 가리키도록 변경(기존 설치자는 `install.py` 1회 재실행). `open_folders.py` 는 폴더 로직 모듈로
  재사용·단독 실행 유지. README 갱신. #A00230_StartupTool
- **A00220_BackupTool Auto Backup = 저장 즉시 백업**(v01.04→01.05): Auto Backup 모드가 *주기 타이머*가
  아니라 *저장 시점*에 백업하도록 변경. 대상 파일을 `QFileSystemWatcher` 로 실시간 감시하다가 디스크에서
  바뀌는 즉시(=저장 순간) 그 파일만 백업. 연속 저장·임시파일 교체식 저장을 다루도록 변경을 ~300ms 디바운스
  후 처리하고 감시 경로를 재등록. 기존 `Interval` 주기 타이머는 감시가 놓친 변경을 잡는 **fallback** 으로 유지
  (mtime 비교로 중복 백업 방지). 실행 중 Auto Backup 토글 시 감시 즉시 시작/정지. 복사 루프를 `_backup_targets`
  로 분리해 주기 사이클·저장 감지가 공용. 안내 문서 동기화. #A00220_BackupTool
- **A00220_BackupTool 상태 표시 = Chrome Dino**(v01.03→01.04): Control 의 상태 글자
  (`Deactive`/`Active...`/`Saving`)를 **Chrome-Dino(T-Rex) 픽셀 애니메이션**으로 교체. 신규
  `app/ui/dino_widget.py` 가 코드 내장 비트맵을 **QPainter 로 그림**(이미지 에셋 0개·테마 무관·exe 번들 불필요).
  Active=제자리 달리기(다리 2프레임 교차 + 바닥 점선 스크롤) + 약 2.6초마다 **포물선 점프**, Deactive=가만히
  서 있음, Saving=`hop()` 으로 1회 추가 점프 강조. 자체 33fps QTimer 구동, 기존 점(...) 타이머(`_dot_timer`)·
  관련 메서드 제거. offscreen PNG 렌더로 4포즈(서기/달리기 A·B/점프) 모양 확인 후 통합. #A00220_BackupTool
- **A00240_PathTool 신규**(v01.00): 자주 쓰는 폴더 경로를 버튼으로 만들어 **클릭 시 탐색기로 여는** standalone
  PySide6 런처. **Create** 그룹의 `Category`(카테고리=`QGroupBox` 생성)·`Path` 버튼 — Path 는 **카테고리·버튼
  이름·경로(Browse)를 한 다이얼로그**(`AddPathDialog`)에서 한 번에 입력. 버튼 클릭=경로 열기(폴더는 그 폴더,
  파일이면 폴더+선택; Win `explorer /select,` 우선·mac/linux 폴백, `core/path_opener.py`). **수정/삭제는
  우클릭 메뉴**(카테고리: Rename/Delete, 버튼: Rename/Change Path/Delete) — 항목이 늘어도 화면 유지. 집/회사
  처럼 **JSON 별로 나뉜 Profile**(상단 콤보 + New/Rename/Delete, 최소 1개 유지, 마지막 활성 기억) 추가 —
  프로파일 1개=JSON 1개로 완전 분리. 저장은 `%USERPROFILE%` 가 아니라 **툴 내부 `data/`**(`profiles/<name>.json`
  + `active.json`), **onefile exe 면 exe 옆 `data/`** 로 분기(임시폴더 휘발 회피), `data/` 는 `.gitignore`.
  구버전 `~/.jun_pathtool/shortcuts.json` 은 첫 실행 시 `Default` 로 자동 마이그레이션. 탭은 `QTabWidget`
  (현재 ShortCut 1개, 확장 대비). core(prefs/path_opener)·ui 분리, 툴 고유 import 경로. #A00240_PathTool
- **A00240_PathTool 버튼 Change Category(카테고리 이동)**(v01.02→01.03): ShortCut 탭에서 **Path 버튼
  우클릭 메뉴에 Change Category** 추가 — 현재 카테고리를 뺀 목록(`QInputDialog.getItem`)에서 대상을 골라
  버튼을 그쪽 끝으로 이동(`_change_button_category`). 대상에 같은 이름 버튼이 있으면 차단, 다른 카테고리가
  없으면 안내. 버튼 데이터(경로 포함) 그대로 옮기고 프로파일 JSON 저장·재렌더. 안내 문서 동기화.
  #A00240_PathTool
- **A00240_PathTool Tree 탭 신설**(v01.01→01.02): 입력 경로를 **트리뷰**(QTreeWidget)로 보여주는 새 탭
  (A00210 Path Structure 의 트리 표시 취지). 옵션: (1) **Depth** 스핀박스(0=All, 변경 시 자동 재빌드),
  (2) **Show files** 체크박스(끄면 폴더만, File Types 자동 비활성), (3) **File Types** 체크 드롭다운(발견 확장자
  중 표시할 것만, A00210 File Manager 와 동일 `_CheckableMenu`), (4) **Expand** 버튼(800×620 큰 창),
  (5) **우클릭 → Reveal in File Explorer**(`path_opener.open_path` 재사용, 메인/Expand 트리 공용). 폴더/파일은
  **QStyle 표준 아이콘**으로 구분. Build 시 모든 파일을 캐시하고 Show files/File Types 는 재스캔 없이 즉시 필터,
  Depth/Path 만 재스캔. 로직은 새 `core/tree_scanner.py`(UI 비의존, `build_tree`/`collect_extensions`)로 분리.
  안내 문서 동기화. #A00240_PathTool
- **A00240_PathTool 카테고리 순서 변경**(v01.00→01.01): 카테고리가 생성 순서로만 쌓이고 순서를 못 바꾸던
  것을, 카테고리 **우클릭 메뉴에 Move Up / Move Down**(양 끝단 비활성) 추가로 자유롭게 재정렬. 화면 순서=
  `data["categories"]` 리스트 순서라 인접 항목과 swap 후 저장·재렌더(`_move_category`), 바뀐 순서는 프로파일
  JSON 에 저장. #A00240_PathTool
- **A00210_FileManager File Manager 탭 검색·필터·탐색기 연동 강화**(v01.13→01.14): (1) **Scan 이 전
  확장자 리스트업** — `.mb`/`.ma` 만이 아니라 모든 포맷(`scanner.scan(extensions=None)`). (2) **File Types
  체크 드롭다운** — 스캔에서 발견된 확장자 중 표시할 것만 체크(All 포함). 여러 개 연속 토글해도 안 닫히는
  `_CheckableMenu`(mouseReleaseEvent 에서 `action.trigger()` 후 닫기 차단), 버튼 라벨에 선택 요약. (3) **Name
  filter** — 목록 위 입력란+`Filter`(또는 Enter)로 제목에 키워드 포함 파일만(대소문자 무시), 빈 값=전체. 적용
  키워드를 입력란과 분리(`_name_filter`)해 다른 필터 토글 시에도 일관. (4) 세 필터(이름·확장자·Recorded)를
  `_apply_file_filter` 에서 **재스캔 없이 중첩** 적용. (5) **우클릭 → Show in File Explorer** — FileTable 에
  컨텍스트 메뉴+`reveal_requested` 시그널, `abs_path` 를 `explorer /select,`(win)/`open -R`/`xdg-open` 으로
  선택 표시(Lineage 탭 reveal 방식 재사용). (6) **Log history Expand** — 상세 패널이 좁아 긴 로그가 안 보이는
  문제로, 라벨 옆 `Expand` 버튼이 전체 폭 리사이즈 가능한 읽기전용 창에 같은 로그를 띄움(스냅샷). 안내 문서
  동기화. #A00210_FileManager
- **A00210_FileManager Settings Branch 편집형 드롭다운**(v01.12→01.13): Settings 의 **Branch** 입력을
  `QLineEdit` → **editable `QComboBox`**(`_BranchComboBox`)로 변경 — 드롭다운을 펼칠 때마다 Store Repo 의
  **실제 git 브랜치(로컬 + 원격추적, 중복 제거)** 를 채워 올바른 이름을 고르게 한다(목록에 없는 이름은 직접
  타이핑도 가능, 첫 clone/fetch 전 대비). `main`/`master` 혼동 같은 브랜치명 불일치로 나던
  `src refspec ... does not match any` push 오류를 줄임. 네트워크 fetch 없이 로컬 ref 만 읽는 새
  `GitSync.list_branches()`(`git branch` + `git branch -r --format`, `origin/HEAD` 류 제외) 추가. 안내
  문서 동기화. #A00210_FileManager
- **A00210_FileManager Load Image 시작 경로 = Store Repo/thumbs**(v01.11→01.12): File Manager 탭의
  **`Load Image...`** 파일 다이얼로그가 홈(`~`) 대신 **Store Repo 의 `thumbs` 폴더**에서 열리도록 변경 —
  거기 이미 저장된 썸네일을 **여러 파일에 재사용**하기 쉽게. Store Repo 미설정·thumbs 폴더 부재 시 홈으로
  폴백(`_thumbs_start_dir`). #A00210_FileManager
- **A00210_FileManager File Manager 탭 Show Recorded Only 필터**(v01.10→01.11): Scan 옆 **Recursive**
  옆에 **`Show Recorded Only`** 체크박스 추가 — 켜면 **record(Save Record)가 있는 파일만** 목록에 남긴다.
  Recursive 스캔으로 수많은 파일이 잡힐 때 **이 툴로 관리(기록) 중인 파일만** 추리는 용도. 마지막 scan 결과를
  원본으로 캐시(`_scanned_entries`)해 두고 `_apply_file_filter`(`has_record` 필터)로 **재스캔 없이 토글 즉시**
  반영, 상태는 prefs(`show_recorded_only`)에 저장. 용어는 툴 기존 어휘(Save Record·Record 컬럼·
  `records/<key>.json`)와 맞춰 **Recorded** 채택. 안내 문서 동기화. #A00210_FileManager
- **A00145_RigConnect Match 탭 신설**(v01.02→01.03): MEL `Match Tool V05.04` 를 **첫 번째 탭**으로
  이식·리팩토링. `Targets`/`Followers` TSL 로 follower 를 target 의 **위치/회전에 매칭**. 핵심 개선:
  (1) **rotateOrder 가 달라도 안전** — MEL 이 follower 의 rotateOrder 를 타깃 것으로 바꿨다 되돌리던
  방식(+ mesh/cluster 분기에서 복원이 누락되던 버그)을 버리고 `cmds.matchTransform`(임시 transform 경유)
  으로 통일. (2) **버텍스 타겟 노말 매칭** — 타겟이 `mesh.vtx[i]` 면 정점 월드 위치로 이동 + follower 의
  **+Y 축을 정점 노말에 정렬**(`maya.api.OpenMaya` `MFnMesh.getVertexNormal`, `_basis_from_normal`).
  (3) **버텍스 개별 리스트업** — 공용 TSL 위젯의 `cmds.ls(fl=True)` 로 `mesh.vtx[0:13]` 가 하나로 묶이지
  않고 정점별 항목으로 들어감. (4) **Create(Locators/Sphere/Cube)** 버튼은 "생성→목록→수동 Match" 가
  아니라 **타겟 수만큼 생성 후 즉시 매칭**하고 Followers 목록을 채움(곡선 데이터는 MEL 그대로 이식).
  (5) mesh→월드 centroid(getPoints 평균)·cluster→월드 rotatePivot 로 위치 매칭(MEL 의 local-space
  rotatePivot 질의 버그 수정), `Swap` 유지, **Blend Shape 버튼 제거**. 로직은 새
  `core/match_manager.py`(UI 비의존)로 분리. 안내 문서(`docs/A00145_RigConnect.md`) 동기화.
  #A00145_RigConnect
- **A00145_RigConnect Skin Weight to Constraint 추가**(v01.01→01.02): Constrain 탭을 **접이식 2섹션**
  (`CollapsibleBox`)으로 — 기존 **`Constraint`(펼침)** + 신규 **`Skin Weight to Constraint`(접힘)**. 선택한
  버텍스의 **스킨 웨이트 비율**대로 영향 joint 들을 constraint weight 로 follower 에 `parentConstraint`
  (예: `hip:0.2/spine_01:0.5/spine_02:0.3` → 그 비율의 weightAliasList setAttr). `Vertices`/`Followers`
  TSL 2개, `Max Influence`(상위 N joint 만 남기고 합=1 정규화, 0=무제한), `Maintain Offset`, **`Per-vertex`
  체크박스** — 해제 시 모든 버텍스 웨이트 **평균**을 전 follower 에 동일 적용, 체크 시 `vertices[i]→
  followers[i]` **1:1**(개수 일치). 로직은 새 `core/skin_constraint_manager.py`(skinCluster 탐색 →
  `skinPercent` 웨이트 조회 → 정규화 → weighted parentConstraint)로 분리. #A00145_RigConnect
- **A00220_BackupTool Settings 접이식화 + 창 슬림 + 스핀박스 화살표 복구**(v01.01→01.03): **Settings 를
  접이식 섹션**(공용 `JUN_mod_collapsible_qt`, A00110 과 동일)으로 바꾸되, 접을 때 **위쪽 파일 목록
  (textscrollList)이 늘어나던 문제**를 수정 — 토글 시 창을 sizeHint 로 재맞추면 늘어난 공간을 expanding
  목록이 흡수하므로, 대신 **본문 높이(`body_height()`)만큼만 창을 줄이거나 늘려** 목록 크기를 고정.
  `resizeEvent` 로 접힘 상태 높이를 추적해 사용자가 직접 창을 키우면 목록은 그에 맞춰 변함. 창을 세로형
  (~350px)으로 슬림화(Save Mode 라디오·분/초를 세로 적층, 스핀박스 폭 축소, 긴 라벨·버튼 단축). **분/초
  스핀박스 화살표가 직사각형으로 보이던 문제**는 테마 qss 가 `::up-arrow/::down-arrow` 를 CSS
  border-삼각형으로 그려 일부 Qt 에서 안 그려진 게 원인 — **9×9 PNG 화살표 아이콘**(`sb_up/down_dark/
  light.png`) `image:` 로 교체(다크=밝은 화살표/라이트=어두운 화살표), light 테마엔 누락됐던 `::up-button/
  ::down-button` 서브컨트롤 정의 추가, 12개 `*.qss` 일괄. `theme_manager` 는 `@STYLES@` 토큰을 qss 폴더
  절대경로로 치환(`_read_qss`)해 실행 위치와 무관하게 아이콘 경로 해석. 백업 1회마다 **`log.txt`** 에
  시각+원본→백업본 한 줄 누적(v01.02). (Max Versions 는 Version Up 모드 전용이라 Overwrite 모드에서
  비활성 — 의도된 동작.) #A00220_BackupTool #Framework
- **A00210_FileManager Lineage 러버밴드 intersect 선택**(v01.09→01.10): 빈 캔버스 드래그 다중선택을
  `ContainsItemShape`(사각형에 **완전히** 든 것만) → **`IntersectsItemShape`**(사각형에 **일부라도 걸친**
  노드·엣지 선택)로 변경 — 큰 노드/긴 화살표도 전체를 감싸지 않고 살짝 걸치면 잡힌다. #A00210_FileManager
- **A00210_FileManager Lineage 노드/연결 삭제 + 다중선택**(v01.09): Lineage 탭에서 **연결선(엣지)도
  클릭 선택**(얇은 곡선용 hit 영역 확대 + 선택 시 흰색·굵게 강조)해 **Delete/Backspace** 로 선택(노드·연결
  혼합)을 **확인 팝업 없이** 삭제 — 연결 삭제는 자식의 해당 부모 링크만 제거, 노드 삭제는 고아 참조까지 정리.
  **빈 캔버스 드래그 = 러버밴드 다중선택**(`ContainsItemShape`), Connect Mode 중엔 러버밴드 off(선 긋기
  집중)·해제 시 복원. **Delete Node** 버튼도 선택 노드를 **일괄(팝업 없이)** 삭제로 변경. #A00210_FileManager
- **A00210_FileManager Lineage 노드 로그 동기화**(v01.08): Lineage 탭 **Node** 패널에 **Log history
  (from record)** 읽기 전용 영역 추가 — File Manager 탭의 Save Record 가 쓰는 `records/<key>.json` 을
  `store.load(node.key)` 로 그대로 읽어 같은 작업 기록을 동일 포맷(`[timestamp] author` + note)으로 표시.
  노드 선택 시·`showEvent`(탭 복귀) 마다 디스크에서 다시 읽어 **File Manager 탭과 동기화**(재클릭 불필요).
  record 매핑 노드에만 표시(planned·루트 밖은 안내문). per-item 회색 foreground 보존 위해 `::item` color 는
  덮지 않음. #A00210_FileManager
- **Framework/styles (dark 테마 트리 행 가독성)**: Windows 10 에서 파일 목록(`QTreeWidget`,
  `alternatingRowColors`)의 **교대 행 배경이 거의 흰색**으로 떠 밝은 글자가 안 보이던 문제 수정. qss 에
  교대행/행 색이 없어 OS 네이티브 팔레트(Win10)가 밝게 칠한 게 원인. `QTreeView/QTreeWidget` 에
  `background #2b2b2b` + **`alternate-background-color #33363c`** + 텍스트/선택(테마 accent)·hover 를
  **명시**해 OS 무관하게 **Win11 처럼** 보이도록 했다. dark.qss + 6개 `*_dark.qss`(blue/brown/coral/green/
  purple/yellow) 일괄 적용(라이트 테마 제외). 이전 탭바·헤더 가독성 수정의 후속(트리 행 누락분). 공용
  Framework 라 dark 테마 전 Qt 툴에 반영. #Framework
- **A00110_animTool / A00120_FKIK 뷰포트 프리즈 수정**(A00110 v01.15→01.16, A00120 v01.03→01.04):
  베이크 시 쓰는 `cmds.refresh(suspend=True)` 는 **씬 전역 토글**이라 복원이 어떤 예외에도 실행돼야
  하는데, A00120 `fkik_matcher.bake()` 의 `finally` 가 임시 컨스트레인트 `cmds.delete()` 를
  `suspend=False` **보다 먼저** 실행 → delete 실패 시 복원이 건너뛰어져 **세션 전체가 프리즈**
  (Graph Editor 커브 편집이 프레임 이동 전까지 반영 안 됨)되는 버그. 전역 상태라 한 번 누수되면 A00110
  도 멈춰 보였다. 공용 컨텍스트 매니저 `Framework/core/maya_refresh.py` 의 **`suspend_refresh()`**
  (복원을 항상 먼저/무조건 보장)로 A00110(`bake_manager`, `follow_match_manager`)·A00120
  (`fkik_matcher`)의 suspend 사용처를 전부 통일하고, `bake_constraint()` 의 임시 컨스트레인트 삭제도
  `finally` 로 이동. A00110·A00120 UI 에 **Force Refresh (Unfreeze Viewport)** 버튼
  (`force_refresh()`) 추가 — 멈춘 세션을 즉시 복구. #A00110_animTool #A00120_FKIK
- **A00110_animTool Follow 탭**(v01.14→01.15): (1) **Maintain Offset** 체크박스 — 타겟↔follower
  의 거리·회전을 유지한 채 추종(`parentConstraint maintainOffset=True` 와 동등)하되, **컨스트레인트
  노드 없이 순수 행렬 연산**으로 구현해 사이클·평가순서 오류를 원천 차단. **Start(구간 시작) 프레임**에서
  페어마다 한 번 `offset = worldMatrix(flw) · worldInverseMatrix(tgt)` 를 측정하고 매 프레임
  `local = offset · worldMatrix(tgt) · parentInverseMatrix(flw)` 로 분해(레거시
  `JUN_PY_MatrixCon_01_01` 의 offsetMat 로직과 동일). 끄면 기존처럼 offset 0(정확히 일치).
  (2) **1<-n** 체크박스 — 켜면 타겟 1개를 모든 follower 가 추종(타겟이 1개가 아니면 경고 후 중단),
  끄면 기존 **n<-n**(인덱스 1:1). (3) **Get Current** 버튼 — Start/End 옆에 각각 두어 현재 Maya
  프레임(`currentTime`)으로 입력란 갱신. 로그에 `mode`(1<-n/n<-n)·`offset`(offset/no-offset) 표기.
  `match_follow(..., maintain_offset, one_to_many)` 로 확장, `_offset_matrix()` 신설,
  `_matched_state(..., offset)` 일반화. 안내 문서(`docs/A00110_animTool.md`) 동기화. #A00110_animTool

---

## 2026-06-18

> [!summary] 신규 툴 A00230 StartupTool — 부팅 시 지정 폴더 자동 팝업(JSON 관리) + A00220 BackupTool — 주기적 자동 백업(standalone PySide) + A00110 animTool Follow 탭(target 추종 베이크) & Offset/Hold 신설→Key Edit 접이식 섹션 재구성 + A00210 FileManager Lineage 탭(파일 브랜치/병합 그래프) & Path Structure 선택 기록(체크한 최상위 폴더만)
- **A00230_StartupTool**: Windows 부팅(로그인) 시 자주 쓰는 작업 폴더들을 **탐색기 창으로 자동 팝업**하는
  순수 Python 유틸리티 신규. 열 폴더는 `config/folders.json` 으로 관리·확장(`path`/`enabled`,
  `open_missing`). 경로는 **환경변수(`%USERPROFILE%` 등)·`~` 확장**을 지원해 **PC 가 바뀌어도 동일**하게
  동작하고, 존재하지 않는 경로는 조용히 skip + 중복 경로 dedupe. `install.py` 가 Startup 폴더에 고유명
  런처(`A00230_StartupTool.vbs`)를 1회 생성 — 로그인 시 **pythonw 로 콘솔창 없이** `open_folders.py`
  실행(런처엔 그 PC 의 절대경로가 박힘). `uninstall.py` 로 제거. JSON 로더는 **전체 줄 `//` 주석**을
  허용해 항목을 삭제 없이 토글 가능. Framework·PathManager 비의존(표준 라이브러리만). #A00230_StartupTool
- **A00210_FileManager**: **Lineage 탭 신설**(v01.02) — 여러 리비전 폴더에 흩어진 파일들
  (.mb/.ma 뿐 아니라 .fbx/.obj 등 **포맷 무관**)의 **브랜치/병합 관계(DAG)** 를 직접 기록하고
  `git log --graph` 스타일 **색상 레인 트리**로 본다.
  **인터랙티브 캔버스**(`QGraphicsView`): 노드 드래그 이동 + **Connect Mode** 로 노드→노드 선 긋기로
  부모 연결(자기연결·중복·**순환 자동 거부**). **레인 색상은 DAG 토폴로지에서 자동 계산**(`compute_lanes`,
  git-graph 컬럼 배정 — 브랜치=다른 색, 병합=레인 수렴), **Auto Layout**(컬럼=레인·행=위상순서, 이후
  드래그 위치 저장). **Planned**("제작 예정") placeholder 노드(점선·반투명). 노드 추가는 폴더
  **스캔(모든 포맷·확장자 필터)**·단일 **Add File**·**Add Planned** 3가지 — 루트 안이면
  project-relative key 로 기존 record/썸네일 자동 링크. 에셋별 이름 그래프 `<store_dir>/lineage/<name>.json`
  저장·기존 Push/Pull 로 git 동기화. core(`lineage.py`, Qt 비의존)/ui(`lineage_tab.py`) 분리,
  `path_structure` 패턴 미러. #A00210_FileManager
- **A00210_FileManager Lineage 보강**(v01.03): (1) **버전업/브랜치 수동 지정** — 노드별
  `relation`(`""`auto/`version`/`branch`) 추가. **Node** 패널 `Relation to parent` 콤보로 같은 부모의
  어느 자식을 **Version-up(부모와 같은 색=메인 라인 상속)** 으로, 어느 자식을 **Branch(강제로 새 레인=다른
  색)** 로 볼지 추가 순서와 무관하게 선택. `compute_lanes` 트렁크 선택을 `version` 최우선·`branch` 제외로
  바꾸되 미지정은 기존 기본(첫 자식) 유지(하위호환), 트렁크 레인을 먼저 예약해 다른 자식이 가로채던 케이스도
  정리. 색은 항상 관계에서 파생(의미↔색 불일치 방지), JSON `relation` 키로 저장·Push 동기화. (2) **캔버스
  탐색** — `LineageView(QGraphicsView)` 서브클래스로 **휠 줌**(`AnchorUnderMouse`, 0.15x~4.0x, 현재
  배율은 `transform().m11()`로 읽어 `fitInView` 후에도 정확)과 **중간 버튼 드래그 팬** 추가(좌클릭·노드
  드래그·Connect Mode 와 비충돌, PySide6/2 좌표 모두 대응). #A00210_FileManager
- **A00210_FileManager Lineage 노드 우클릭 메뉴**(v01.04): `NodeItem.contextMenuEvent` 로 노드 우클릭
  시 **Reveal in File Explorer** 제공 — `key`(project-relative)를 `store.project_root`와 합쳐 절대경로
  복원 후 탐색기로 폴더를 열고 **파일 선택**(Windows `explorer /select,`, macOS `open -R`/Linux
  `xdg-open` 폴백). 경로 해석 가능할 때만 활성(키 있음+루트 설정+파일 존재), planned·루트 밖·사라진 파일은
  비활성+안내. 이후 우클릭 액션을 계속 확장할 수 있는 구조. #A00210_FileManager
- **A00210_FileManager 썸네일 캡쳐 오버레이 검정화면 수정**(v01.05): Capture Region 시 화면이 전부
  검게 덮여 캡쳐 범위가 안 보이던 문제 해결. 원인은 오버레이 위젯에 `WA_TranslucentBackground` 가 없어
  반투명 dim 이 불투명(검정) 배경 위에 칠해진 것. (1) 투명 배경 속성 활성 → 실제 화면이 비쳐 보임,
  (2) 풀스크린 '상태'(`WindowFullScreen`) 제거하고 **가상 데스크탑 geometry** 로 전체 모니터를 덮음
  (풀스크린+반투명이 단일모니터 스냅/합성 깨짐을 유발 — **Windows 10/11 공통** 동작 위해), (3) 선택영역
  표시를 `CompositionMode_Clear`(드라이버 편차) 대신 **선택영역 제외 둘레 4개 영역만 dim** 으로 변경해
  선택영역이 확실히 투명. 결과적으로 Win+Shift+S 처럼 전체는 살짝 어둡고 드래그 영역만 또렷. #A00210_FileManager
- **A00210_FileManager 배포 사용자 데이터 리포 원클릭 동기화**(v01.06): 릴리즈본을 git 으로 받은 사용자가
  데이터(records/thumbs/lineage/path_structures)를 동기화 못 하던 문제 해결. 근본원인 3가지 — (1) `on_pull/
  on_push` 가 읽던 `remote_url` 이 prefs/UI 어디에도 없어 항상 빈 값 → `ensure_repo` 가 clone 못 하고 로컬
  init 만 함, (2) 기본 브랜치 `main` vs 데이터 리포 `master` 불일치, (3) 배포 PC 에 clone 할 기본 store_dir
  없음. 해결: **중앙 데이터 리포 URL/브랜치/기본 clone 경로(`~/.jun_filemanager/JUN_FileManager_data`)를 툴에
  번들**(`app/config/data_repo.py`, release_builder 가 `app/` 통째 복사하므로 자동 포함). prefs 기본값을 번들에서
  채우고 구버전 prefs 는 load 시 브랜치 마이그레이션(main→master), UI 에 **Remote URL** 필드 추가, **Pull
  한 번**에 repo 없으면 기본 경로로 자동 clone→pull. clone 실패 시 **로컬 init 폴백 제거**(인증/권한 오류
  표면화, 끊긴 빈 repo 방지). core(prefs/git_sync)·config(data_repo)·ui(main_window) 분리 유지. #A00210_FileManager
- **A00210_FileManager Path Structure 선택 기록**(v01.07): Path Structure 탭에서 베이스 폴더의 **모든**
  하위 경로를 기록하던 것을, **선택한 최상위 폴더만** 기록하도록 변경. **"Folders to record" 체크리스트**
  (`QListWidget`)에 최상위 하위 폴더를 체크박스와 함께 리스트업하고(Base 변경·Browse·**Scan** 시 채움,
  재스캔 시 기존 체크 이름 기준 보존), **"All" 체크박스**로 전체 선택/해제(전체 기록). **Capture** 는 체크된
  최상위 폴더만 모으고(폴더가 있는데 미체크면 경고), **Recursive** 면 그 하위 트리까지 포함. core 는
  `list_top_level()` 추가 + `_collect_folders()`/`capture()` 에 `include_top` 필터(None=전체, 하위호환).
  로직 `app/core/path_structure.py`, UI `app/ui/path_structure_tab.py`. #A00210_FileManager
- **A00220_BackupTool**: 컴퓨터 비정상 종료 대비 **주기적 자동 백업** standalone PySide6 앱 신규.
  대상 **파일 목록**을 분·초 주기로 각 원본 폴더의 `backup` 하위 폴더에 복사(`{base}_{suffix}{ext}`,
  예 `scene_BU.mb`). 폴더명·접미사(BU) UI 지정, **Overwrite(기본)** / **Version Up**(`_NN`,
  최근 N개만 유지·롤오버) 모드 선택. 상태 표시 `Stat : Deactive` / `Active...`(점 애니메이션) /
  `Saving`. **다음 저장까지 남은 시간 카운트다운**(`Next save in MM:SS`, 1초 갱신, v01.01) 추가.
  설정은 로컬 prefs(`~/.jun_backuptool/prefs.json`)에 영속. core(Qt 비의존)/ui 분리,
  A00210 standalone 구조 준수. #A00220_BackupTool
- **A00110_animTool**: **Follow 탭 신설**(v01.11) — 좌(Target)/우(Follower) 리스트로, 각 follower 가
  같은 인덱스 target 의 **월드 위치·회전(·스케일)과 동일**해지도록 구간 키를 베이크(컨스트레인트 없이
  `parentConstraint(maintainOffset=False)` 와 동등). **rotateOrder 무관** — target `worldMatrix` 를
  follower `parentInverseMatrix` 로 로컬화한 뒤 **follower rotateOrder 로 재분해**(Mirror Key 경로
  재사용). **blend(0~1)** 로 원본↔매치 혼합(위치/스케일 lerp·회전 쿼터니언 slerp)을 **키 값에
  베이크**(레이어 weight=1 유지), 선택된 애니 레이어(override `V=F` / additive `V=F−B`)에 기록.
  로직 `app/core/follow_match_manager.py`, UI 는 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개. 더불어
  선택 레이어 판별을 `cmds.ls(type=animLayer)` 나열 후 레이어별 `selected` 검사로 구현(animLayer 에
  선택 레이어 목록 전역 쿼리가 없음). #A00110_animTool
- **A00110_animTool**: **Offset & Hold 기능 신설 → Key Edit 탭 접이식 재구성**(v01.12→01.14).
  리스트업한 컨트롤러의 키를 **포즈 유지(hold) + 보간(offset)** 구조로 재배치 — 오브젝트 커브들의
  **키 시점 합집합**을 포즈로 삼아 포즈마다 `[start+i·P, start+i·P+hold]`(P=hold+offset) plateau 를
  만들고 사이를 offset 길이로 보간한다. 값은 `getAttr(time=)` 로 샘플링(키 없던 커브도 보간값),
  plateau 안쪽 탄젠트 flat·보간 구간 spline(유지→가속→감속→유지), Start 비우면 오브젝트별 첫 키 앵커.
  로직 `app/core/offset_hold_manager.py`. 처음 별도 탭으로 추가(v01.12)했다가 **Key Edit 탭으로 통합**
  (v01.13), 다시 Key Edit 탭을 **Move Keys / Graph Editor / Offset & Hold 접이식 섹션 3개**로 분리
  (v01.14, Offset & Hold 기본 접힘). 접이식 위젯은 재사용 모듈 `Framework/qt/MOD_collapsible_qt_v01.py`
  (`JUN_mod_collapsible_qt_v01` + 숨김 시 sizeHint 0 인 `JUN_mod_fit_tab_page_v01`)로 분리, 레거시
  `JUN_PY_SelectionTool` 의 `frameLayout(collapsable=True)` 패턴 이식. 섹션 토글·탭 전환 시
  `_fit_window` 가 **창 크기를 현재 탭 콘텐츠에 맞춰 자동 조정**. #A00110_animTool
- **standalone Qt 패키지 충돌 수정**: A00080·A00210·A00220·release_builder_QT 가 모두 최상위
  `app` 으로 import 해, 한 인터프리터(Maya·공용 런처)에서 두 툴을 동시에 띄우면 `sys.modules['app']`
  가 첫 툴로 점유돼 두 번째 툴이 `ModuleNotFoundError`(또는 엉뚱한 창)로 실패하던 문제 해결. launch.py 는
  **툴 고유 경로**(`tools.<tool>.app...` / `dev.release_builder_QT.app...`)로, 내부 모듈은 **상대 import**
  (`from ..core import …`)로 전환 — in-Maya 툴(A00110)·템플릿(A00004/A00008)이 이미 쓰던 규약과 일치.
  4개 툴 동시 로드 검증 완료. A00080·A00210 의 launch/내부 import 경로 전환은 **전용 커밋으로 분리**
  푸시(A00220·release_builder 분은 각 기능 커밋에 포함). #Framework
- **Framework/styles (dark 테마 가독성)**: Windows 10 에서 **탭바·테이블 헤더** 글자가 배경과
  대비가 낮아 안 보이던 문제 수정. qss 에 `QTabBar::tab`/`QTabWidget::pane`/`QHeaderView::section`
  (+hover·corner)을 **명시**(어두운 배경·밝은 글자·테마 accent 테두리)해, OS 네이티브 렌더(Win10/11
  차이)와 무관하게 **Win11 처럼** 보이도록 했다. `dark.qss` + 6개 `*_dark.qss`(blue/brown/coral/
  green/purple/yellow) 일괄 적용, 라이트 테마 제외. 공용 Framework 라 dark 테마 전 Qt 툴에 반영.
  #Framework

## 2026-06-17

> [!summary] 신규 툴 2종(A00210 FileManager·A00010 HumanIK V02) + 윈도우 최상단 정책 개선 + 신규 툴 2종(A00200·Release Builder) + Mirror Key Behavior + 저장소 정리(레거시 아카이빙·포트폴리오 README·FileManager 데이터 분리·브랜치 정리) + A00210 Path Structure 탭
- **Framework/qt**: 모든 Qt 툴 창을 **마야 메인 윈도우에 parent** — 뷰포트 위에는 떠 있되 다른 툴
  창과는 정상 Z-order(밑에 있는 창을 클릭하면 위로 올라옴). `Qt.WindowStaysOnTopHint`(항상 최상단)
  폐기. 공용 헬퍼 `Framework/qt/maya_window.py` 의 `maya_main_window()` 추가, A00110+12개 Qt 툴 및
  A00008 템플릿에 일괄 적용(A00200 은 기존부터 동일 패턴) (`d2b5ad4`) #Framework
- **dev/release_builder_QT**: 릴리스 패키징용 **PySide Release Builder QT** 신규 (`7640a92`) #dev
- **A00200_CSV_tool**: **ARKit 페이셜 CSV import** 신규 툴 + 드래그&드롭 설치(`__dragDrop_A00200`)
  (`3d9ec1e`) #A00200_CSV_tool
- **A00110_animTool**: Mirror Key 탭에 **Behavior 모드**(기본 ON) 추가 — 반대쪽 컨트롤러의 고유
  forward/up 축 방향을 보존하며 미러. 소스의 **로컬 채널 값(translate/rotate)을 타겟에 그대로
  복사**한다(반사·행렬 연산 없음, 반사축 무관). Maya `mirror joints` 의 Behavior 세팅으로 만든
  좌우 축 반전 리그용. 체크박스로 기존 월드 반사(orientation)와 선택, 구간/현재프레임 둘 다 적용.
- **A00110_animTool**: Behavior 가 ON 이면 반사축이 무의미하므로 **Mirror Axis 라디오 비활성**.
- **A00110_animTool**: Mirror 실행(Mirror Selected·Mirror Current Frame)이 **씬 선택과 무관하게
  Source/Target 리스트의 오브젝트만** 대상으로 처리(선택 → `Resolve Pairs`/`Select Source` 로
  리스트 채우기 → 실행으로 단계 분리). (v01.08~01.09) #A00110_animTool
- **A00210_FileManager**: Maya 씬(`.mb`/`.ma`) **버전·작업기록 추적** standalone PySide6 앱 신규 —
  경로 스캔·파일별 작업자/타임스탬프 로그·**화면 영역 캡쳐 썸네일**·기록(records/thumbs) **git
  push/pull**(원본 미푸시). 키는 프로젝트 상대경로(cross-PC), 절대경로 설정은 로컬 prefs. core(Qt/Maya
  비의존)/ui 분리, 사용법 [A00210 가이드](A00210_FileManager.md) (`fd74913`) #A00210_FileManager
- **A00010_humanIKTool_V02**: HumanIK 툴 in-Maya PySide 재작성 신규 (`6ef7f76`) #A00010_humanIKTool
- **.gitignore**: PyInstaller 빌드 산출물(`build/`·`dist/`) 무시 추가 (`fd74913`)
- **저장소 아카이빙**: 레거시·학습 폴더 10개를 `_archive/` 로 이동(`git mv`, 히스토리 보존) —
  `legacy_tools/`(00_Old·00_RUN·01_Modules·01_Modules_Small·02_Modules_Old·03_Modules_Test·
  04_KWI_generator) + `study_notes/`(100_Memo·101_cellular_automata·101_maya_python_technic).
  추적되던 `.pyc` 12개 정리, 레거시→현행 매핑표 `_archive/README.md` 추가 (`5248196`) #archive
- **루트 README**: 채용·상사 대상 **포트폴리오형 루트 `README.md`** 신규 — 한국어 본문 + 영어 요약,
  도메인별 툴 하이라이트·기술 스택·저장소 구조·연락처(이메일/GitHub/Notion·웹 포트폴리오). 스크린샷
  자리 `JUN_All/docs/assets/` (`d73c8c7`) #docs
- **A00210_FileManager 데이터 분리**: 별도 원격(`JUN_FileManager_data`)으로 동기화되는 데이터 폴더가
  부모 트리 안에 **중첩(nested repo)** 돼 있던 임베디드-repo 위험 해소 — 부모 트리 밖으로 이동 +
  `store_dir` prefs 갱신, 부모 `.gitignore` 에 추가해 우발적 gitlink 커밋 방지 (`91949fd`) #A00210_FileManager
- **브랜치 정리**: `Dnable` 을 master 역할 기본 브랜치로 확정. `dev_archive`(로컬+원격)·`master`(로컬)
  삭제, 서버에 없던 `Dnable_bch` 추적 잔상 prune. 이후 일상 작업/푸시는 `dev` 로 일원화 #git
- **A00210_FileManager**: **Path Structure 탭** 신규(v01.01) — 베이스 폴더의 하위 폴더 구조를 JSON 으로
  저장해 다른 PC 와 git 동기화하고 **버튼 하나로 폴더만 재생성**(파일 미생성). 베이스는 project_root
  상대경로로 저장→PC 마다 자기 루트 아래 재생성. **Recursive** 토글(중첩 트리 전체 vs 최상위만),
  이름별 다중 저장, **Capture(미리보기)/Save 분리**, 트리뷰 preview(`build_tree_lines`). 기존 창을
  QTabWidget(File Manager/Path Structure)로 재구성, 로그 공유. 코어(`app/core/path_structure.py`,
  Qt 비의존)/ui 분리 (`4dfa979`) #A00210_FileManager

## 2026-06-16

> [!summary] 신규 병합 툴 2종 + Qt 인프라 정리 + JointTool Aim 재설계
- **A00145_RigConnect**: MEL ConnectionTool V04.02 + A00140 병합(4탭 PySide) 신규 툴, 사용법 [A00145 가이드](A00145_RigConnect.md) (`5592490`, `d1750df`) #A00145_RigConnect
- **A00060_jointTool_V02**: MEL JointTool V05.03 + A00060 병합(4탭) 신규 툴, 사용법 [A00060 V02 가이드](A00060_jointTool_V02.md) (`ec42af1`, `bbb78bd`) #A00060_jointTool_V02
- **A00060_jointTool_V02**: Aim 탭 재설계 — Aim axis 드롭박스(X/Y/Z) + twist-only IK식 정렬(joint 월드 위치 보존·constraint/cycle 제거·레퍼런스 안전, v01.01) (`4c67ac8`) #A00060_jointTool_V02
- **Framework/qt**: 모든 Qt 툴을 `Framework.qt.qt` 래퍼 경유로 일원화 (`f3c8d58`) #Framework
- **deps**: 외부 의존성 관리 중앙화 (`a13792c`)
- **A00110_animTool**: Smart bake 옵션(native `bakeResults -smart`, v01.07) + 비교 문서 (`859299d`, `c0d7db8`) #A00110_animTool
- **dragDrop**: 드롭 설치 파일명 고유화로 셸프 버튼 충돌 해결 (`30f0f09`)
- **A00190_FKIK_General_Tool**: 레거시 FK/IK 툴 PySide 리팩터 (`cab90a6`) #A00190_FKIK

## 2026-06-15

> [!summary] animTool/abSymMesh PySide 강화 + bake 성능
- **A00110_animTool**: Copy Key 탭(v01.03)·Mirror Key 탭(v01.04) 추가 + 문서화 (`f6139ac`, `147fa7f`, `be41423`, `8917cbf`) #A00110_animTool
- **A00180_abSymMesh**: Python/OpenMaya 재구현(속도)·app/ 레이아웃 + PySide UI·동작 문서 (`f01ced1`, `f6f5053`, `4719e56`) #A00180_abSymMesh
- **A00170_driverTool**: RemapVal + SphericalEye 를 탭 툴로 병합 (`96acac4`) #A00170_driverTool
- **A00150_remapVal**: 보간을 enum(Linear/Smooth/Spline)으로 (`2cb49aa`) #A00150_remapVal
- **A00120_FKIK**: per-frame 루프 대신 native `bakeResults` 로 bake (`b83c591`) #A00120_FKIK
- **A00080_KWI_creator**: 결합 파일 출력(base+setting+LD) (`61c459e`) #A00080_KWI_creator
- **dev/reload**: per-tool `reload_for_tool` 추가 + 전 Qt 런처 전환 (`1660c63`)
- **Framework/styles**: 체크박스·라디오 인디케이터 전 테마 가시성 수정 (`acf285e`, `730f8b4`) #Framework

---
