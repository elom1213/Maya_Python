# Changelog — A00210_FileManager

All notable changes to this tool are documented here.

## [01.53] - 2026-11-09

- **[Sync > Status] 트리 이름 순.** 경로 · 파일이 비교 결과 순서(폴더는 처음 나온 파일 때 생긴 순서)로 섞여 보이던 것을 단계마다 정렬한다.
  - 순서: **추적 폴더 → 추적 파일 → 제외 폴더 → 제외 파일**, 각 무리 안은 이름(대소문자 무시) 순.
  - 제외 항목(흐린 색)은 예전처럼 추적 항목 아래 — 그 안에서도 이름 순.
- 시험 UI 108/108(+2), core 65/65. **GUI 확인 아직.**

## [01.52] - 2026-11-06

- **[Sync > Status] `File Types` 확장자 필터.** `Filter` 줄 오른쪽에 File Manager 탭과 같은 `File Types` 버튼 — 비교한 파일들의 확장자를
  `.mb (120)` 처럼 개수와 함께 체크 메뉴로(눌러도 닫히지 않음, `All` 로 한 번에). 버튼 글자 `File Types: mb, ma +2`.
  - 끈 확장자는 이 PC 프로파일(`sync_types_off`)에 기억 — 나중에 생긴 확장자는 켜진 채로 보인다.
  - 고르는 중에는 빈 폴더 줄(파일 없음)을 숨긴다. 폴더 줄 상태는 그대로 **아래 모든 파일**로 센다(`Show` 와 같은 규칙).
  - 메뉴 클래스 `_CheckableMenu` 를 `app/ui/checkable_menu.py`(`CheckableMenu`)로 옮겨 두 탭이 같이 쓴다(main_window 에는 별칭).
- 시험 UI 106/106(+10), File Manager 쪽 시험 그대로 통과.

## [01.51] - 2026-11-06

- **[Sync > Status] 빈 폴더도 트리에.** 파일이 하나도 없는 폴더(예: `scenes/1999_=================================== - 복사본`)는 파일 목록으로는 안 생겨 보이지 않았다.
  - 스캔이 **가장 안쪽 빈 폴더**를 매니페스트 `empty_dirs` 에 적는다(`a/` 와 `a/b/` 가 다 비면 `a/b` 만 — 위 폴더는 경로로 따라 나온다).
    제외 · 무시된 파일만 있는 폴더도 빈 폴더. 실측 JUN_MUE: 폴더 277 중 빈 폴더 181(복사본 구분 폴더 5개 포함).
  - 상태: 모든 PC 에 있으면 `Empty folder`(OK 색), 이 PC 에 없으면 `Missing (empty folder - create it; on …)`, 다른 PC 에 없으면 `Only here (…)`.
    `All PCs` 비교에서는 `Missing: <PC> (empty folder)`. PC 열 = `folder` / `—`. 위 폴더 줄의 상태 개수에도 들어간다.
  - `Show` · `Filter` 는 파일 줄과 같은 규칙. 다른 PC 에 파일이 있는 폴더는 빈 폴더 줄로 만들지 않는다.
  - v01.50 이전에 스캔한 매니페스트(`empty_dirs` 없음)는 '모름' — Missing 으로 치지 않는다. **각 PC 에서 한 번 다시 스캔하면** 들어간다.
- 시험 core 65/65(+8) · UI 96/96(+5).

## [01.50] - 2026-11-06

- **[Sync] PC 표시 이름.** 위쪽 `This PC:` 옆 **`PC Names...`** 창에서 PC 마다 툴 안에서 부를 이름(예: `P4T7MBN` → `Office`)을 붙인다.
  표에는 매니페스트에 나온 모든 PC(이 PC 먼저) · 스캔한 루트가 보이고, 이름 칸을 비우면 컴퓨터 이름으로 돌아간다.
  - 화면 전부 이름으로: `This PC:` 라벨(툴팁 = 컴퓨터 이름) · `PCs:` 줄 · PC 열 머리 · 상태 글자(`get from Home` · `send to Home` · `Missing: Home`) · 요약 열 · 셀 툴팁 · Export List 머리.
  - 이름은 `_sync_settings.json` 의 `pc_names` — **모든 PC 가 공유**(Scan && Push 등으로 푸시하면 다른 PC 에도 같은 이름).
  - 매니페스트 파일 이름 · 판정 키는 **컴퓨터 이름 그대로** — 이름을 바꿔도 이력이 끊기지 않는다.
- 시험 `test_sync_ui.py` 91/91(+13: 저장 · 라벨 · 열 머리 · 상태 글자 · 새로 읽어도 유지 · 창 미리 채움 · 비우기 · 취소), core 57/57. **GUI 확인 아직.**

## [01.49] - 2026-11-05

- **[Sync > Status] `Show` 기본 = 전부 체크(OK · Excluded 포함, 사용자 지정).** 설정 키를 `sync_show` → `sync_show_filters` · `sync_show_excluded` 로 바꿔
  예전 프로파일에 저장된 'OK 꺼짐' 대신 새 기본으로 시작한다(그 뒤 바꾼 체크는 다시 기억).
- **[Sync > Status] 처음엔 전부 접힌 트리.** 다시 그려도(필터 · Show · Compare 를 바꿔도) 사용자가 펼쳐 둔 폴더는 그대로, 필터 글자가 있으면 맞는 곳까지 펼친다.
- **[Sync > Status] 폴더 줄에 아래 파일들의 상태.** `Status` 열을 **경로 바로 옆(2번째 열)** 으로 옮기고, 폴더 줄은 그 아래 **모든** 파일의 상태를
  가장 급한 것부터 `Missing (1) · Ahead (2)` 처럼, 다 같으면 `OK` 로 — 위로 재귀(`00_04_02_ANI_00_PJ_010` → `scenes` → `5040_cleanup_BCM_KANA`).
  `Show` 로 OK 행을 숨겨도 폴더 줄은 실제 상태로 센다. 툴팁에 상태별 개수. `All PCs` 비교에서는 행마다 PC 들 중 가장 급한 상태로 센다.
- **[Sync] 상태 색(사용자 지정).** Missing 연한 빨강 `#ff8a8a` · Outdated 노랑 `#f2d64b` · Conflict 밝은 하늘색 `#7fd8ff` · OK 초록 `#6fcf6f`
  (Ahead / Only here 는 지정이 없어 보라 `#c39bf0`).
- **[Sync > Status] 창 세로 2.2 배.** 트리 세로 힌트 1075(오프스크린 · `slate_mid` 실측: 창 717 → 1600, 2.23 배). 모니터보다 길면 화면 높이에서 멈춘다.
- **[Sync > Excluded] 왼쪽에 폴더 트리 + 체크박스.** 이 PC 루트 아래 폴더 · 파일을 펼쳐 가며(한 겹씩 읽음) 체크하고 `Exclude Checked (All PCs)` /
  `Exclude Checked (This PC)`. 체크한 폴더 아래의 체크는 폴더 하나로 합친다. 이미 제외 · 무시 패턴에 걸린 항목은 회색 기울임 + 툴팁.
  여러 행을 골라 체크 하나로 전부(공용 `checkTree`), 펼치기 규칙은 공용 `treeExpand`. `Add Folder...` / `Add File...` 도 그대로 있다.
- **[Framework tabFit] 중첩 탭 높이 보정 수정** — 스크롤 칸 안이라도 중첩 탭은 부모 레이아웃의 heightForWidth 경로로 높이가 정해지는데 보정은 아니라고 봐서,
  형제보다 훨씬 긴 Status 페이지를 **두 번** 빼 Roots · Excluded 로 가면 창이 246px 로 쪼그라들었다. 롤아웃 시험 31툴 0 fail.
- 시험 `test_sync_ui.py` 78/78(기본 체크 · 폴더 상태 재귀 · 색 · 처음 접힘 · 펼침 유지 · 2.2 배 · Excluded 트리 체크 → 제외), core 53 · 기존 43 · 32 · 28. **GUI 확인 아직.**

## [01.48] - 2026-11-05

- **[UI] 트리 펼치기 규칙.** 화살표(더블클릭 · `→` 키)로 펼치면 **한 단계만** 보인다 — 접었다 다시 펼쳐도
  예전에 열어 둔 아래 단계가 한꺼번에 열리지 않는다. **Shift + 펼치기 = 아래 전부 펼침, Shift + 접기 = 아래 전부 접음**
  (`*` 키 = 아래 전부). 툴이 처음 펼쳐 보여 주는 동작은 그대로. 적용: Sync > Status · File Manager 파일 목록 · Path Structure 미리보기 · Maya > Reference 트리.
  공용 `JUN_mod_treeExpand_qt_v01` (`docs/Framework_MOD_treeExpand_qt.md`). **GUI 확인 아직.**
- **[Sync] 탭 높이 16px 모자람 수정.** `PCs:` 줄이 줄바꿈 라벨이라 탭 높이 맞춤(tabFit)이 Status 페이지를 368 < 384 로 잘랐다
  (Framework tabFit 롤아웃 시험에서 발견). 한 줄 + 가로 크기 무시(PC 가 많아도 창 폭을 밀지 않음), 전체 내용은 툴팁.

## [01.47] - 2026-11-05

- **[Sync] 새 탭 — PC 간 작업 파일 동기화 추적(Sync Tracker).** 여러 PC 가 같은 경로(예: 정션 `C:\JUN\JUN_MUE`)로 작업할 때
  **어느 PC 의 파일이 최신이고 어느 PC 에 없거나 옛것인지** 를 파일마다 보여 준다. 파일 자체는 옮기지 않는다(전송은 지금처럼 구글 드라이브 등).
  - PC 마다 **매니페스트**(경로 · 크기 · 수정 시각 · SHA-256 · 해시 이력)를 `<데이터 폴더>/manifests/<root>/<PC 이름>.json` 에 쓰고
    기존 Git Sync 로 주고받는다. PC 마다 자기 파일만 써서 git 충돌이 없다. Local(Shared) 모드는 공유 폴더에 바로 쓴다.
  - 상태: `Missing`(다른 PC 에만 있음) · `Outdated`(내 해시가 다른 PC 이력 안에 있음) · `Ahead` / `Only here`(내 것이 최신 — 보내야 함) ·
    `Conflict`(양쪽이 따로 고침) · `OK`. **판정은 해시 + 이력** — 구글 드라이브에서 받은 파일은 수정 시각이 바뀌기 때문.
    처음 보는 파일인데 내용이 다르면 시각으로 '아마' 를 정하고 `?` 를 붙인다.
  - **Status**: `Scan & Push` · `Scan Only` · `Pull & Compare` · `Refresh`, 해시는 백그라운드(진행 막대 · `Cancel`) — 크기 · 시각이 같은 파일은 다시 해시하지 않는다.
    PC 열은 매니페스트 수만큼(이 PC 먼저), **5대 이상이면 요약 열**(Latest on / Missing on / Outdated on). `Compare: This PC / All PCs`,
    `Show` 필터, 경로 필터, 폴더 뱃지(`1 Missing · 2 Ahead`), PC 별 마지막 스캔 시각(24시간 넘으면 `stale`).
    `Copy Paths` · `Export List...` · `Reveal in Explorer`, 우클릭 `Exclude from Sync (All PCs)` / `Exclude on This PC Only` / `Include Again`.
  - **Roots**: 추적 루트 여러 개. 루트 = 이름(id) + 공유 기본 경로, **PC 마다 다른 경로**는 `Set Path on This PC...`(프로파일에 저장).
    겹치는 루트는 안쪽을 바깥 루트의 제외 경로로 넣을지 묻는다. 루트 안의 정션은 기본으로 따라가지 않는다(`Follow junctions` 옵션).
    처음엔 File Manager 의 Project Root 를 첫 루트로 제안한다.
  - **Excluded**: 루트별 제외 경로(폴더 = 그 아래 전부) — `All PCs (shared)` / `This PC only`. 스캔과 비교 둘 다 적용.
    무시 패턴(glob, 기본 `**/backup/**` · `.mayaSwatches` · `Thumbs.db` …).
- 새 `app/core/sync_settings.py` · `sync_manifest.py` · `sync_compare.py`(UI 비의존), `app/ui/sync_tab.py`.
  계획 `JUN_All/docs/plans/A00210_FileManager_sync_tracker_plan.md` 의 1차 범위. 지운 파일 추적 · 시작 시 자동 스캔 · 전송 보조는 다음 단계.
- 시험 `tests/test_sync_core.py` 53/53(제외 경계 · 해시 캐시 · 저장 중 파일 · 되돌림 · 루트 안 정션 · PC 2/3/5대 판정),
  `tests/test_sync_ui.py` 52/52(오프스크린, 가짜 PC · 가짜 git). 기존 43/43 · 28/28 · 50/50 · 32/32.
  실제 `C:/JUN/JUN_MUE`: 320 파일 · 13.9 GB 첫 스캔 10.9 s(디스크 캐시 상태), 재스캔 0.03 s, 매니페스트 106 KB. **GUI 확인 아직.**

## [01.46] - 2026-11-04

- **[UI] 경로 표기 하나로.** 같은 경로가 `C:\Users\...\JUN_FileManager_data` 와 `C:/Users/.../JUN_FileManager_data` 처럼 섞여 보이던 것을
  **슬래시(`/`)** 로 통일(NAS 는 `//172.30.1.93/...`). Qt 파일 대화상자 · 기존 프로파일 대부분이 쓰던 표기.
  - 프로파일을 읽을 때 경로 칸 8개(Project Root · Store Repo · Shared Folder · Scan Dir · Recreate To · mayapy · Export Rules / Folder)의 표기를 맞추고, 저장도 그 표기로.
  - 직접 입력한 Project Root · Scan Dir 는 입력을 마치면, Browse 결과는 바로 맞춘다. Maya 탭의 mayapy · Export Folder 는 예전엔 일부러 `\` 로 바꿨다 → `/`.
  - **로그**(모든 탭) 안의 Windows 경로, 파일 목록 · Export 표 툴팁, Lineage 경로 안내창도 같은 표기.
  - 끝 구분자 · `..` 정리, 대소문자 · 공백은 그대로. 파일 · git · mayapy 동작은 바뀌지 않는다(Windows 는 `/` 도 받는다).
- 새 `app/core/paths.py`(`ui_path` · `ui_text`). 시험 `tests/test_ui_paths.py` 28/28, 기존 43/43 · 50/50 · 32/32(경로 비교를 표기와 무관하게) · 31/31, A00480 44/44.

## [01.45] - 2026-11-04

- **[데이터 저장소] 프로파일마다 브랜치 → 브랜치 `main` 하나 + 프로파일 폴더.** 데이터는 저장소 안 **`profiles/<Data Folder>/`**
  (records · thumbs · lineage · path_structures)에 있다. 저장소 · 클론은 하나, GitHub 에서 모든 프로파일을 폴더로 한 화면에 본다.
  비공개 저장소 `JUN_FileManager_data_Private` 는 더 쓰지 않고 MUE 도 같은 저장소(`profiles/MUE`) — 저장소는 Private 으로 전환됨.
- **[Settings] `Data Folder`** (Store Repo 아래, 편집 가능한 드롭다운 = `profiles/` 하위 폴더). 여러 프로파일이 같은 폴더를 써도 된다.
  Git Sync 제목에 지금 올리는 폴더(`profiles/<folder>`)가 보인다.
- **[Push] 내 폴더만 커밋** → `pull --rebase --autostash` → push, 그 사이 누가 올려 거절되면 한 번 더. 다른 폴더의 미커밋 변경은 섞이지 않는다.
  커밋 메시지 끝에 `[profiles/<folder>]`. **Pull** 도 `--rebase --autostash`.
- **[안전] 클론 브랜치 확인** — 클론이 옛 프로파일 브랜치(Dnable · SA …)에 있으면 Pull / Push 를 하지 않고 **`Switch to main`** 버튼을 보인다
  (미커밋 변경이 있으면 전환 거부).
- **[변환] 옛 프로파일 자동 변환**: branch 값 → Data Folder(`master` → Dnable), **저장 폴더 이름이 우선**(A0020_SA → SA, A0030_Src_Rig → src_rig,
  A0010_MEU → MUE — branch 값이 클론과 어긋나 있던 soundAliance 교정), 옛 프로파일 브랜치 → `main`, 비공개 저장소 URL → 공용 URL. Store Repo 경로는 바꾸지 않는다.
- **A00211_RefLineage**(+ A00480 Reference > Lineage)도 같은 데이터 폴더 규칙(`prefs.data_dir_of`).
- 시험 `tests/test_data_folders.py` 43/43(변환 · 동시 Push · 내 폴더만 · 거절 재시도 · 브랜치 확인 · Switch · UI). 기존 50/50 · 32/32 · 31/31, A00480 44/44.
- **원격 데이터 옮기기 전에는 이 버전으로 Pull / Push 하지 말 것** — 옛 클론은 `profiles/` 가 없어 목록이 비고 `Wrong branch` 가 뜬다. 절차는 계획서 §5 ~ §7.

## [01.44] - 2026-11-03

- **[File Manager > Settings] `Store Repo` / `Shared Folder` 칸 읽기 전용.** 붙여넣기 · 타이핑으로 데이터 폴더 경로가 실수로 바뀌지 않게,
  경로는 옆의 **`Browse...`** 로만 바꾼다. 칸의 경로를 선택해 복사하는 것은 된다. 모드 전환 · 프로파일 · 기본 경로 채우기는 그대로.

## [01.43] - 2026-11-03

- **[Maya > Reference] `Delete Display Layers` · `Delete Anim Layers` 체크박스 (기본 둘 다 ON).** `Import Reference` 가 임포트 ·
  네임스페이스 정리 **뒤, 저장 전에** 씬의 디스플레이 레이어(`defaultLayer` 제외)와 애니메이션 레이어를 지운다. 임포트된 레퍼런스의 레이어도
  함께 지워지고, 레퍼런스로 남은 것(체크 안 한 레퍼런스)의 레이어는 지울 수 없어 남긴다(로그에 개수). 애니메이션 레이어는 MEL
  `delete BaseAnimation;` 과 같은 결과 — Base 커브만 남고 다른 레이어에만 있던 키는 사라진다. 확인 팝업에 두 옵션 상태 표시.
  mayapy 2024 실측: 레이어 3 + 애니 레이어 4 삭제, 남는 레퍼런스 레이어 유지, 오브젝트 · Base 커브 유지.
- **[UI] 탭 스크롤 제거.** v01.42 의 탭 높이 자동 맞춤이 **PySide6 에서는 한 번도 돌지 않았다** — 공용 tabFit 이
  `int(QSizePolicy.Policy)` 에서 TypeError(PySide6 enum)로 매번 `fit skipped` → 창이 처음 크기에 머물러 긴 탭은 스크롤. Framework 에서 고침.
  또 루트 탭이 `tabs_scroll` 안에 있어 Maya > Export(글줄 바꿈 라벨) 에서 창이 File Manager 높이로 열리던 보정 오차도 고침.
- **[UI] 탭 세로 길이 축소.** 리스트 · 트리의 Qt 기본 sizeHint(192px) 대신 짧게 연다(창을 키우면 늘어난다) — Maya 하위탭 폴더 트리 110 ·
  Maya File 90 · Reference 트리 100 · Export 표 120 · File Manager `Log history` 100. File Manager Settings 는 Scan 옵션을 Scan Dir 줄로 올려 한 줄 절약.
  실화면(2560x1552 작업 영역) 실측 창 높이: File Manager 1480 → 1348 · Maya > Reference 987 · Export 1363, **모든 탭 스크롤바 없음.**

## [01.42] - 2026-10-29

- **[UI] 탭마다 창 높이가 자동으로 맞춰진다.** 탭(중첩 포함)을 바꾸면 창 높이가 지금 보이는 페이지에 맞게 늘거나 줄어
  스크롤 없이 다 보인다. 페이지가 모니터 작업 영역보다 길면 화면 높이에서 멈춘다. 폭은 그대로(처음 여는 크기는 예전 `fit_to_content` 그대로, 그 뒤 높이만 따라간다).
  공용 `JUN_mod_tabFit_qt_v01` — A00275 v01.38 과 같은 방식 (`docs/Framework_MOD_tabFit_qt.md`). **마야 GUI 확인 아직.**

## [01.41] - 2026-10-26
### Added
- **Maya > `Export` sub tab** - pick several Maya files, choose a **set rule** (one json per rule, e.g. set `Bake`,
  exact / contains / regex, ignore namespace, rules folder changeable and shareable), press `Check Sets` and the table
  shows per file whether a matching set exists (top level or inside another set), its playback range, fps and the
  Maya version it was saved with. Files without the set are unchecked and skipped.
- **`Bake & Export`** - for every ready file mayapy opens it, imports loaded references and removes namespaces (option,
  default ON - FBX keeps `CHN:root` otherwise), finds the set, collects its members and all descendants (`Joints Only`
  drops non-joints under joints, constraints always dropped), bakes translate / rotate / scale over Start - End with
  one `bakeResults` call, **moves top bones that sit under a group to the scene root** (world motion baked through a
  temporary locator - exact even when the group is animated), and exports one FBX per file. The Maya file itself is
  never saved. **`Export Only`** does the same without baking.
- Output names: Find / Replace + Insert (`Token` after token k / `Char` at position, default `bake` as the first token
  -> `bake_anim_01.fbx`), live preview in the table, name collisions and invalid characters block the run. Export Folder
  (empty = next to the source). Existing FBX files are listed in a warning popup with `Overwrite` / `Cancel`.
- Range per file (`Timeline` / `Animation range` / `Custom`), editable Start / End cells, `Euler Filter` option,
  progress popup (per file + open / import / bake / export steps; the bake call itself shows no inner progress), cancel at
  a file boundary (grace 30 min), report json next to the FBX files, `Resources` line (CPU / RAM / GPU, read-only).
- `app/maya/core`: `set_rules`, `export_naming`, `export_jobs`, `set_match`, `scene_probe`, `bake_export`, `hw_info`;
  worker jobs `probe` / `export`; `ref_importer.import_loaded_references`. `tests/` : core 50, worker 31 (real mayapy
  worker process, FBX re-import, world matrices), UI 32 (offscreen).

### Changed
- The mayapy box moved from the Reference tab to the bottom of the Maya tab (`mayapy_bar.py`) - one box for all sub tabs.
  File picking (tree + Add Checked / Browse + Maya File list) is now `maya_file_picker.py`, shared by Reference and Export
  (behaviour unchanged).
- FBX helpers that A00480_FileTool had (`fbx_options`, `collect_export_nodes`, `ensure_fbx_plugin`, ...) were promoted to
  `Framework/core/maya_fbx.py`; the worker imports Framework (`launch.spec` datas += `Framework/core`, `Framework/jali`).
- The probe reads the saved playback range from `sceneConfigurationScriptNode` because scenes are opened with
  `executeScriptNodes=False` (`playbackOptions -q` would return the previous scene's values, unit-converted).

## [01.39] - 2026-10-23
### Added
- **`File > Add to Start Menu`** - creates a Start menu shortcut (`JUN File Manager.lnk`) for this tool and
  tries to pin it to Start, the same feature `A00240_PathTool` and `A00220_BackupTool` have (shared
  `Framework/core/shell_integration.py`, Windows 10 / 11). The shortcut runs `pythonw.exe launch.py`
  (or the exe itself when frozen) with this tool's AppUserModelID and icon, so the window groups under the
  same taskbar button. Click again after moving the tool folder to refresh the path. The result is logged
  and shown in a dialog (with the manual pin step when Windows does not expose the pin verb).
- `app/config/app_meta.py`: `APP_NAME`, `APP_DESCRIPTION`, `tool_root()`, `start_menu_launch_spec()`.
- Confirmed in the running tool (2026-10-23): the Start menu shortcut is created.

### Changed
- **`Pin` button turns light red while on** (`Pinned`), the same colour `A00240_PathTool`, `A00220_BackupTool`
  and `A00370_ToolLauncher` use - shared `Framework/qt/pin_style.py` (`apply_pin_style`). Only the `:checked`
  colours are set, so the button keeps its 72 x 28 size and the theme look while off.
- Verified offscreen (PySide6): background pixel of the real window's Pin button = theme colour off, `#f2a0a0` on,
  size unchanged. Confirmed by eye in the running tool (2026-10-23).

## [01.38] - 2026-10-23
### Added
- **Folder animation while shrunk** (`app/ui/folder_anim.py`, `FolderAnimWidget`). The tool icon's
  folder, record card and sync badge are drawn as a code bitmap in the space left of the two buttons
  and **loop forever** (one loop 3.0 s): the record card rises out of the folder (0.5 s, ease-out) ->
  its thumbnail, title and log lines fill in one step at a time (0.3 s apart) -> the sync badge's two
  arrows run one full turn around the ring (0.8 s) -> the card slides back into the folder (0.5 s,
  ease-in) -> a short rest with the closed folder -> again. Card body in the theme text colour,
  everything else in the icon's blues. Restarts from the closed folder every time Shrink is turned
  on, stops when it is turned off, repaints only when the picture changes.
- Verified offscreen (PySide6, 27 checks: phases, card height, fill steps, badge turn, loop wrap, plus
  the v01.37 Shrink / Pin checks) and captures at several times. Not yet checked by eye in the running
  tool.

## [01.37] - 2026-10-23
### Added
- **`Shrink` and `Pin` buttons** in a header row above the tabs (right side, 72 x 28 each) - the same
  pair `A00220_BackupTool`, `A00240_PathTool` and `A00370_ToolLauncher` have.
  - **`Pin`** keeps this window above other windows (`Pinned` while on); press again to release.
  - **`Shrink`** hides the menu bar, the tabs and the log and resizes the window to **272 x 155**,
    with `Pin` moved **under** `Shrunk`. Press again to restore the previous window size (width and
    height). Only the display is hidden: profile, scan results and the log stay as they were.
  - The space left of the two buttons is reserved for a looping animation while shrunk; it is
    still empty in this version.
  - Verified offscreen (PySide6, 15 checks: button place / size, hidden widgets, 272 x 155, Pin under
    Shrunk, restore, repeated toggles, Pin while shrunk). Not yet checked by eye in the running tool.

## [01.36] - 2026-10-12
### Fixed
- **The window can be resized again by dragging its edges.** It opens at the same size as before, but that
  size is no longer its minimum. Cause: a `QTabWidget`'s minimum size is the largest minimum of **all** its
  pages, hidden ones included (the File Manager page sets the height, the Lineage page the width), so the
  window sat on its minimum and could not shrink - and could not grow either when it was already as tall
  as the screen. The tabs now sit in a scroll area; `fit_to_content()` opens the window at the old natural
  size, capped to the monitor's work area, and a scrollbar appears only if you make it smaller than the content.

## [01.35] - 2026-10-12
### Added
- **New `Maya` tab** for working on Maya scene files on disk, with a first sub-tab **`Reference`**.
  - Pick Maya files in a folder tree (the shared tree from A00240 PathTool, now with **check boxes on file rows** -
    select several rows with Shift / Ctrl and one click checks them all; File Types defaults to `.ma .mb .fbx`),
    then `Add Checked` (or `Browse...`) puts them in the **Maya File** list.
  - **`Get Reference`** lists the references the selected files use. Nested references (a reference's own references)
    fold under their parent; the `Used by` column names the Maya files. Missing files are red and cannot be checked.
  - **`Import Reference`** opens every scanned file, imports the **checked** references it uses (nested ones come
    along, unloaded ones are loaded first), merges namespaces and **saves the file in place** in its original type.
    A confirmation lists what will change; a progress popup follows the files; a file that fails is not saved.
  - Options, on by default: **Remove All Namespace** (every namespace in the scene; those of references that stay
    referenced are kept) and **Backup** (`<folder>/backup/<name>_REF_NN.<ext>` - the same `backup/` folder as
    A00220_BackupTool, which uses `_BU`).
  - Right-click `Reveal in File Explorer` / `Copy file path` and double-click on all three lists, like the tree tab.
- **This app runs outside Maya, so Maya work runs in `mayapy`**: `.ma` files are read from their header right here;
  anything that needs Maya (`.mb` files, importing) is handed to a small worker script started with `mayapy.exe`
  in the background. The progress popup follows it; Cancel stops after the current file. The **mayapy** box
  (Browse... / Detect) is saved with the profile; empty means the newest Maya under Program Files.
- The Maya tab lives in its own package `app/maya/` (core + ui) so it can become a separate tool later. Shared pieces
  went to the Framework: `MOD_fileTree_qt_v01`, `MOD_checkTree_qt_v01`, `path_context`.
  (It was first built into A00480_FileTool the same day and moved here; A00480 is unchanged.)

## [01.34] - 2026-10-01
### Changed
- **Path Structure: the Preview tree's top item is now `.` instead of the Base Folder's name.**
  Capturing `A` (with `B/B_01`, `B/B_02`, `C` under it) used to show `A` at the top, which read as if
  Recreate would make a new `A` folder. The saved items were always relative to the base, and
  Recreate creates them directly inside `Recreate To`, so the top is now `.` = the Recreate To folder.
  Its tooltip says so and shows the folder it was captured from.
- The Expand window title shows the structure name (or `(not saved)`) instead of the base path.
- What is saved and what Recreate creates are unchanged.

## [01.33] - 2026-10-01
### Changed
- **Path Structure: Capture works from any folder.** It no longer needs a Project Root (File Manager tab)
  and the Base Folder no longer has to be inside it - before, an empty root gave
  "Set Project Root first" and a folder above or outside the root gave "Base folder is outside the project root".
- A saved structure now also records the absolute path it was captured from (`base_path`).
  `base_rel` (path under the Project Root) is still filled when the folder is inside the root, so
  structures captured there keep working on other PCs as before; it is empty for folders outside the root.
- Recreate is unchanged - it has used only the `Recreate To` field since v01.32, so structures captured
  outside the root recreate the same way.
- Older JSON files without `base_path` load as before.

## [01.32] - 2026-09-28
### Added
- **Help menu bar** - the shared Framework menu bar (`JUN_mod_menuBar_qt_v01`), so the window gets
  the same common `Help` items as every other tool (`Copy Tool Name`, ...).
### Fixed
- **Path Structure - Recreate always builds in `Recreate To`.** Selecting a structure (or any list
  refresh, e.g. after a profile switch) used to overwrite the field with `<Project Root>/<base_rel>`,
  so a typed destination was silently replaced and the structure landed under the Project Root.
  The field is now independent of the File Manager tab: nothing auto-fills or clears it, and its
  value is saved per profile (`recreate_to`) and restored on the next launch.

## [01.31] - 2026-09-18
### Added
- **Shift / Ctrl multi-select + multi-check** on the two check lists - Lineage `Add Node from Scan...`
  and Path Structure `Folders to record`. Clicking the check box of a selected row (or Space) sets
  every selected row. Framework shared behaviour `JUN_mod_checkList_qt`.

## [01.29] - 2026-08-03
### Added
- **Path Structure — capture and recreate files, not just folders.** Two checkboxes,
  **both on by default**:
  - **Include files** (Save Structure) — Capture also records the file names it finds,
    into a new `files` list in the structure JSON. Only *names* are stored, never file
    contents. Depth and the "Folders to record" checklist apply to files exactly as they
    do to folders, so `Capture Depth = 1` records only the files sitting directly in the
    base folder. Files directly in the base are always included regardless of the
    top-level checklist, because they belong to the base folder itself.
  - **Create files** (Preview row, replaces the old *Show files*) — recorded files appear
    in the Preview tree with checkboxes and are created by **Recreate**. What you see in
    the tree is what gets created, which is the same rule Depth already followed; turning
    it off hides *and* skips the files. Uncheck a single file to skip just that one.
- Recreated files are **empty 0-byte files marked with `__`** appended to the full name —
  `test.ma` → `test.ma__` — so a generated placeholder can never be mistaken for, or
  opened as, a real scene. The suffix is not re-applied if the name already ends with it,
  so capture-then-recreate round trips do not grow `____`.
### Changed
- `recreate()` now returns a **`RecreateResult`** (created/existing folders **and** files)
  instead of a bare tuple. It still unpacks as `created, existing = recreate(...)`, so
  existing callers keep working. The result message and log now report folder and file
  counts separately.
- Preview: when a structure has **no recorded files** (saved before this version, or with
  *Include files* off), the tree falls back to listing the base folder's files from disk
  as before — now **greyed out and without checkboxes**, making it obvious they are
  reference only and are never created.
### Fixed
- An existing file at the target path is **never overwritten or truncated**. It is counted
  as "already existed" and left untouched (exclusive `open(..., "x")`, so even a race
  between the check and the write cannot clobber it).
- Structures saved before this version load unchanged (`files` defaults to an empty list),
  and recreate exactly as they did — folders only.

## [01.27] - 2026-07-03
### Added
- **App / taskbar icon.** Added a blue folder + record-card + sync-badge icon
  (`icon/A00210_FileManager.svg` → `.png` + multi-size `.ico` 16–256px) matching the
  blue_dark theme. `launch.py` now sets it as the application/window icon and — on
  Windows — sets an explicit **AppUserModelID** (`Dnable.JUN.A00210.FileManager`) so
  the taskbar shows this icon instead of the generic `python.exe` icon when the tool
  is run from a terminal. Icon path resolves in both dev and PyInstaller builds
  (`app/config/app_meta.py`); `build_exe.bat` embeds the `.ico` and bundles it.
### Changed
- **Settings** — merged the separate **Store Repo** and **Shared Folder** rows into
  a **single data-folder input** that adapts to the Source Mode. The label and hints
  switch between *Store Repo* (Remote/Git) and *Shared Folder* (Local) as you change
  the mode. Each mode still remembers its own path independently (kept in the profile
  as `store_dir` / `local_dir`), so switching modes never clears the other path. No
  profile migration needed — existing profiles load unchanged.

## [01.25] - 2026-07-02
### Fixed
- **Path Structure** tab — multi-select checkbox toggle now **keeps the selection
  across repeated clicks**. Previously the selected rows stayed selected only for
  the first checkbox click and collapsed to a single row afterwards. The pre-click
  selection is now captured on mouse-press (before Qt collapses it), so you can keep
  toggling the same multi-selection over and over.

## [01.24] - 2026-07-02
### Changed
- **Path Structure** tab — **Preview** is now an interactive **tree view**
  (QTreeWidget) instead of plain text, like the A00240 PathTool *Tree* tab:
  - **Show files** checkbox (default **off**) — folders only by default; when on,
    files found on disk (under the local base folder) are shown too. Files are for
    inspection only and are never recreated.
  - **Expand** button — opens the same tree in a large window. Check-state changes
    made there are reflected back into the tab.
### Added
- **Path Structure** tab — **depth + selective recreate** control:
  - **Capture Depth** spinbox on the *Save Structure* group (1 = top-level only,
    0 = All) replaces the old **Recursive** checkbox — capture the folder tree only
    as deep as you want.
  - **Depth** spinbox on the *Saved Structures* group limits how deep the preview
    shows **and** how deep **Recreate** creates (0 = All).
  - Each folder in the preview tree has a **checkbox**; unchecking excludes it from
    **Recreate**. So you can recreate only the depth and paths you want. (Ancestor
    folders needed by a checked child are still created.)
  - **Multi-select** the tree rows with **Shift/Ctrl**, then toggle one of the
    selected checkboxes to check/uncheck **all selected folders at once**.
  - Older structures saved before this version load fine — `recursive: true` maps
    to depth *All*, `recursive: false` to depth *top-level*.

## [01.23] - 2026-06-26
### Added
- **File Manager** tab — **Source Mode** selector (Settings group). Choose where
  records/thumbnails are read from and written to:
  - **Remote (Git)** — the existing behavior: a central git data-repo synced with
    **Pull / Push** (uses the **Store Repo** clone path).
  - **Local (Shared / NAS)** — a new **Shared Folder** path is read and written
    **directly, with no git**. Intended for teams sharing a NAS, where the file
    server keeps the data in sync instead of pushing/pulling a git remote each
    time. In this mode the git inputs (Store Repo, Remote, Branch, Remote URL) and
    the **Pull / Push** buttons are disabled; use **Scan** to refresh.
  - The mode is saved **per profile** (alongside the new `local_dir`), so e.g. a
    `Work (NAS)` profile can use Local mode while a `Home` profile stays on Git.
    All tabs (File Manager / Path Structure / Lineage) follow the active mode's
    folder automatically.

## [01.21] - 2026-06-22
### Added
- **File Manager** tab — **Edit** button on the **Log history** header. Opens an
  *Edit Log History* dialog where each past entry's **author** and **note** can be
  edited and individual entries **deleted** (timestamps are kept). OK replaces the
  record's logs in order; press **Save Record** to persist (same flow as Add Log
  Entry). Editing is structured per-entry, so timestamps/entry boundaries can't be
  corrupted by free-text edits.

## [01.20] - 2026-06-22
### Added
- **File Manager** tab — **settings Profiles**. A new **Profile** group (combo +
  **New / Rename / Delete**) saves every user setting — Project Root, Store Repo,
  Scan Dir, Remote, Branch, Remote URL, Author, Recursive, Show Recorded Only — as
  a named profile (one JSON each, under `~/.jun_filemanager/profiles/`). Switch
  profiles to instantly load that environment's settings (e.g. Home / Work).
  - Switching a profile **auto-saves the current fields** to the outgoing profile
    first (no lost edits), then loads the new one and **refreshes the Lineage /
    Path Structure** saved-lists against the new Store Repo. The window also saves
    the active profile on close, and remembers it across launches (`active.json`).
  - **Save Settings** now writes to the active profile. The old single
    `prefs.json` is **migrated once** into a `Default` profile (original kept as
    `prefs.json.bak`); `prefs.load()/save()` stay back-compatible (they target the
    active profile), so A00211_RefLineage keeps working unchanged.

## [01.19] - 2026-06-22
### Changed
- **Lineage** tab — node right-click **Reveal in File Explorer**: if the file
  exists on this machine it is revealed in File Explorer as before (no popup). If
  it doesn't (e.g. a graph generated on another machine by **A00211_RefLineage**),
  the file's **path is popped up** in a dialog (selectable/copyable) instead of
  silently failing. The menu item is enabled whenever the node has a `key` (no
  longer greyed out just because the file is missing locally).

## [01.18] - 2026-06-22
### Added
- **Lineage** tab — **convert an edge's type by selecting it and switching the
  edge-type dropdown**. Select one or more edges, then change the
  `Lineage (parent)` / `Reference (dashed)` dropdown beside *Connect Mode* — the
  selected arrows switch type in place (solid open-V ↔ dashed filled-triangle),
  keeping their direction. The underlying relationship moves between the lineage
  DAG (`parents`) and the `references` list, any custom edge color carries over,
  and a conversion that would create a cycle is rejected. (Previously the dropdown
  only chose what a *new* node→node drag created.)

## [01.17] - 2026-06-22
### Added
- **Lineage** tab — **edge colors are now editable too**. Select one or more edges
  (lineage and/or reference) and use **Set Color...** to recolor them, or **Reset
  Color** to revert to the default (lineage = child lane color, reference = gray).
  `Set Color... / Reset Color` now act on the combined node + edge selection. The
  per-edge override is stored in the graph JSON (`edge_colors`, keyed by
  `kind:src>dst`; back-compatible) and cleaned up when an endpoint node is deleted.

### Fixed
- **Lineage** tab — **overlapping arrows between the same two nodes are fanned
  apart**. When a node pair had both a lineage and a reference edge (or otherwise
  shared endpoints), the arrows were drawn on top of each other. Edges sharing the
  same node pair are now spread horizontally by a fixed spacing so each arrow (and
  its arrowhead) is distinct.

## [01.16] - 2026-06-22
### Added
- **Lineage** tab — **Reference edges (dashed)**: a node can now point a **gray
  dashed arrow** at another node to show a Maya **reference** relationship
  (referenced file → the file that loads it), separate from the solid
  version/branch lineage. Drawn in **Connect Mode** via the new **edge-type
  dropdown** (`Lineage (parent)` / `Reference (dashed)`) beside the *Connect Mode*
  button — pick *Reference*, then drag from the referenced node to the referencing
  node. Reference edges are independent of the lineage DAG, so they **do not affect
  lane/color/auto-layout**; they have their own cycle guard and a filled-triangle
  arrowhead to tell them apart from lineage's open V. Stored as a new per-node
  `references` list in the graph JSON (back-compatible: older graphs load fine).
- **Lineage** tab — **Set Color... / Reset Color**: rubber-band select one or more
  nodes and set a **custom fill color** on all of them at once (`Set Color...`,
  color picker), or **Reset Color** to revert the selection to the automatic lane
  color. The manual color is stored per node (`color`); lineage edges keep their
  lane color, so the git-graph lane reading is preserved.

## [01.15] - 2026-06-22
### Fixed
- **Lineage** tab — **middle-mouse pan no longer hits a wall**. Panning moves the
  scrollbars, whose travel was bounded by the scene rect (content bounds + a small
  200 px margin), so dragging stopped once you reached just past the nodes. The
  pannable area is now a full viewport-worth of margin around the content, and the
  scene rect grows on demand while you keep dragging toward an edge — so you can
  pan freely well beyond the nodes (effectively unlimited). The margin resets to
  the content on the next render, so it never bloats permanently.

## [01.14] - 2026-06-19
### Added
- **File Manager** tab — **right-click a file → Show in File Explorer**: opens the
  file's folder with the file selected (Windows `explorer /select,`, macOS `open
  -R`, Linux `xdg-open`).
- **File Manager** tab — **Name filter** bar above the file list: a text field +
  **Filter** button (or Enter). Empty shows all; a keyword shows only files whose
  name contains it (case-insensitive). Stacks with the other filters.
- **File Manager** tab — **File Types** checkable dropdown next to *Show Recorded
  Only*: lists the extensions found in the last scan, each toggleable (plus
  **All**), so you can show only chosen types. Re-filters instantly; the menu
  stays open while toggling multiple types.
- **File Manager** tab — **Expand** button by *Log history* opens the log in a
  large, resizable read-only window (the side panel is narrow for long logs).

### Changed
- **File Manager** tab — **Scan now lists all file types**, not just `.mb`/`.ma`
  (`.fbx`/`.obj`/`.png` etc. are included); narrow the result with the new
  **File Types** / **Name filter** controls.

## [01.13] - 2026-06-19
### Changed
- **Settings** — the **Branch** field is now an editable dropdown. Opening it lists
  the Store Repo's actual git branches (local + remote-tracking, deduped) so you can
  pick a valid one instead of typing it. You can still type a branch name manually
  (e.g. before the first clone/fetch). This avoids the common `src refspec <branch>
  does not match any` push error caused by a branch-name mismatch (e.g. `main` vs
  `master`). Backed by new `GitSync.list_branches()` (reads local refs, no network).

## [01.12] - 2026-06-19
### Changed
- **File Manager** tab — *Load Image...* now opens in the Store Repo's `thumbs`
  folder instead of the home directory, so a thumbnail already saved there can be
  reused for several files. Falls back to home if the Store Repo is unset or its
  `thumbs` folder does not exist yet.

## [01.11] - 2026-06-19
### Added
- **File Manager** tab — **Show Recorded Only** checkbox next to *Recursive*. When
  checked, the file list keeps only files that have a saved record (created via
  *Save Record*), so a recursive scan that lists every file can be narrowed to the
  ones tracked through this tool. Re-filters instantly on toggle (no re-scan
  needed) and the state is remembered in prefs.

## [01.10] - 2026-06-19
### Changed
- **Lineage** tab — rubber-band selection is now **intersect** mode: dragging a box
  selects any node or connection the rectangle **touches**, instead of only the
  ones fully enclosed by it (was `ContainsItemShape`, now `IntersectsItemShape`).

## [01.09] - 2026-06-19
### Added
- **Lineage** tab — delete nodes **and connections**, with multi-select:
  - **Click a connection (edge)** to select it (hit area widened so thin curves are
    easy to hit; the selected edge is highlighted white/thick).
  - **Delete / Backspace** removes the current selection — any mix of nodes and
    connections — with no confirmation popup. Deleting a connection drops only that
    parent link from the child; deleting a node also cleans up orphaned references.
  - **Rubber-band multi-select**: drag on empty canvas to box-select nodes fully
    inside the rectangle. Disabled while **Connect Mode** is on (so line-drawing is
    unaffected); restored when Connect Mode turns off.
### Changed
- **Delete Node** button now deletes **all selected nodes at once** and no longer
  shows a confirmation dialog (was: single node + Yes/No popup).

## [01.08] - 2026-06-19
### Added
- **Lineage** tab — the **Node** panel now shows the selected node's **log history**
  (read-only), loaded from the same record the File Manager tab's *Save Record*
  writes (`records/<key>.json`). It is re-read from disk on node select and when
  the Lineage tab regains focus, so entries stay in sync with the File Manager tab.
  Shown only for nodes that map to a record (not for planned / out-of-root nodes).

## [01.06] - 2026-06-18
### Added
- **One-click data-repo sync for distributed users.** The tool now ships a bundled
  default data-repo config (`app/config/data_repo.py`: central repo URL, branch,
  and a default local clone path `~/.jun_filemanager/JUN_FileManager_data`). When a
  user who received the released tool clicks **Pull** and no store repo exists yet,
  it auto-clones the central data repo to the default location and pulls — no
  manual clone or path setup needed.
- New **Remote URL** field in Settings, pre-filled from the bundled config
  (editable for forks/relocated repos), persisted in prefs.
### Fixed
- Data sync never worked for distributed installs: the Pull/Push handlers read a
  `remote_url` pref that was never set (missing from defaults and UI), so the store
  was only ever `git init`-ed locally with no remote. The remote URL is now wired
  end-to-end.
- Default sync branch mismatch (`main`) vs the actual data repo (`master`); defaults
  now come from the bundled config, and legacy prefs are migrated to the correct
  branch on load.
- Clone failures no longer silently fall back to a local `git init` (which created a
  disconnected empty repo); the error is surfaced so auth/network/access issues are
  visible.

## [01.05] - 2026-06-18
### Fixed
- **Region capture** overlay showed a fully black screen, hiding what was being
  selected. The overlay widget was missing `WA_TranslucentBackground`, so the dim
  layer was painted over an opaque (black) background instead of the live desktop.
  Now the screen is only dimmed and the drag region stays clear (like Win+Shift+S).
  - Enabled `WA_TranslucentBackground` so the actual screen shows through.
  - Replaced fullscreen window **state** with explicit virtual-desktop **geometry**
    (frameless / stay-on-top / tool) — fullscreen + translucency could snap to a
    single monitor or break compositing. Works on Windows 10 and 11.
  - Painted the dim as four rects around the selection instead of
    `CompositionMode_Clear` (driver-dependent), so the selected region is reliably
    transparent.

## [01.04] - 2026-06-18
### Added
- **Lineage** tab — node **right-click context menu**: **Reveal in File Explorer**
  opens the folder containing that node's file with the file selected
  (Windows `explorer /select,`; macOS/Linux fallbacks). Enabled only when the path
  resolves (node has a project-relative key, project root is set, and the file
  still exists); disabled for planned / out-of-root / missing files. Built to be
  extended with more per-node actions later.

## [01.03] - 2026-06-18
### Added
- **Lineage** tab — manual relationship control: each node has a **Relation to
  parent** (`Auto` / `Version-up (main line)` / `Branch (variation)`). A
  `Version-up` child inherits the parent's lane color (same color = version line);
  a `Branch` child is forced onto a new lane (different color). `Auto` keeps the
  previous topology default (first child by creation order is the main line). Lets
  you flip which child is the version-up vs the branch instead of relying on add
  order.
- **Lineage** canvas navigation: mouse-**wheel zoom** (anchored under the cursor,
  0.15x–4.0x) and **pan via middle-mouse drag**. Left-click (select / node drag)
  and Connect Mode are unaffected.

## [01.02] - 2026-06-18
### Added
- **Lineage** tab: manually record branch / merge relationships between files
  (any format — `.mb`/`.ma`, `.fbx`, `.obj`, ZBrush, textures, …) and view them as
  a git-graph-style colored tree.
  - Interactive canvas (`QGraphicsView`): drag nodes to reposition; turn on
    **Connect Mode** and drag node → node to set a parent link (self-links,
    duplicates, and cycles are rejected).
  - **Auto lane coloring** — lanes (columns) are computed from the DAG topology
    like `git log --graph`; each lane cycles a color palette. Branches read as
    distinct colors; merges (multi-parent) collapse lanes.
  - **Auto Layout** arranges nodes into lanes (column = lane, row = topological
    order); positions stay user-draggable afterward and are saved.
  - **Planned** nodes ("제작 예정") for files not yet created (dashed, translucent).
  - Add nodes from a folder **scan** (any format; filter the result list by
    extension) or a single **Add File...**; both link to an existing
    record/thumbnail by project-relative key when inside the project root.
    Also add empty **planned** nodes. Node inspector to rename, mark planned,
    annotate, and preview the linked thumbnail.
  - Multiple named graphs per asset (`<store_dir>/lineage/<name>.json`); list,
    load, save, delete. Auto-synced by the existing Git Pull / Push.

## [01.01] - 2026-06-17
### Added
- **Path Structure** tab: save a folder-structure template (subfolders of a base
  folder) to JSON in the synced store, and recreate those folders on another PC.
  - Base path is stored **relative to the project root**, so recreation rebuilds
    under each PC's own project root (absolute paths may differ).
  - **Recursive** checkbox: capture the full nested subfolder tree, or only the
    immediate child folders.
  - Multiple named structures (`<store_dir>/path_structures/<name>.json`); list,
    preview, recreate, delete. Folders only — no files are created.
  - Auto-synced by the existing Git Pull / Push (records / thumbnails / structures).
### Changed
- Main window reorganized into tabs (**File Manager**, **Path Structure**); the log
  panel is shared below both tabs.

## [01.00] - 2026-06-17
### Added
- Initial release. Standalone (Maya-independent) PySide6 Windows app.
- Scan a directory for Maya scene files (`.mb` / `.ma`) and list them.
- Per-file metadata record: author + timestamped work log entries.
- Thumbnail per file via on-screen region capture (or load an image file).
- Metadata store keyed by **project-relative path** so the same file maps to the
  same record on any PC.
- Git sync (Pull / Push) of records and thumbnails only — original `.mb`/`.ma`
  files are never pushed (kept out of the data repo + `.gitignore` safety net).
- Per-PC local preferences (`%USERPROFILE%/.jun_filemanager/prefs.json`).
- PyInstaller build (`build_exe.bat`, `launch.spec`).
