# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00210_FileManager - version info

# 01.41  Maya > Export sub tab: set rule (json) -> Check Sets (set · playback range · fps · version per file) -> Bake & Export / Export Only
#        (mayapy worker: import references + remove namespaces, bakeResults, top bones to scene root, FBX). Naming Find/Replace + Insert,
#        Overwrite/Cancel popup, report json. mayapy box + file picker shared by the sub tabs. FBX helpers -> Framework/core/maya_fbx.
# 01.40  Maya tab: mayapy_runner / mayapy_process promoted to Framework (Framework/core/mayapy_runner.py,
#        Framework/qt/MOD_mayapyProcess_qt_v01.py) so other standalone tools (A00560_JaliBatch) share the mayapy worker
#        protocol. The two modules here re-export them (no behaviour change).
# 01.42  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식) · 처음 여는 폭은 예전 fit_to_content 그대로

# 01.43  Maya > Reference: Delete Display Layers / Delete Anim Layers 체크박스(기본 ON) - 임포트 뒤 씬의 레이어 · 애니메이션 레이어 삭제.
#        탭 높이: PySide6 에서 tabFit 이 enum int() 로 매번 'fit skipped' 였던 것 수정(Framework) + 스크롤 칸 안 탭의 hfw 경로 보정,
#        리스트 · 트리 sizeHint 축소(picker 트리 110 · Maya File 90 · Reference 100 · Export 표 120 · Log history 100), Settings 줄 합침.

# 01.44  File Manager > Settings: Store Repo / Shared Folder 칸 읽기 전용 - 붙여넣기 · 타이핑으로 경로가 바뀌지 않게,
#        Browse... 로만 바꾼다(실수 방지). 선택 · 복사는 된다.

# 01.45  데이터 저장소: 프로파일마다 브랜치 -> 브랜치 main 하나 + 저장소 안 profiles/<Data Folder>/ (비공개 저장소 폐지, MUE 도 같은 저장소).
#        Settings 에 Data Folder(편집 콤보 = profiles/ 하위 폴더). 데이터 폴더 = <Store Repo>/profiles/<folder> (prefs.data_dir_of, A00211 공유).
#        Push = 내 폴더만 add -> pull --rebase --autostash -> push(거절되면 한 번 더). 클론 브랜치가 설정과 다르면 Pull/Push 거부 + `Switch to main`.
#        옛 프로파일 자동 변환(branch -> data_folder, 저장 폴더 이름으로 soundAliance=SA 교정, 비공개 URL -> 공개 URL). 기본 브랜치 master -> main.

# 01.46  화면 경로 표기 통일 - 같은 경로가 C:\... 와 C:/... 로 섞여 보이던 것을 슬래시(/) 하나로(NAS = //서버/...).
#        새 app/core/paths.py(ui_path · ui_text): 프로파일 읽기(경로 키 8개) · 입력 칸(입력 마침 · Browse) · 로그(모든 탭) · 툴팁 · 안내창,
#        Maya 탭(mayapy · Export Folder 는 예전엔 normpath 로 \ 였다).

# 01.47  Sync 탭 (Sync Tracker) - PC 간 작업 파일 동기화 추적. PC 마다 가진 파일 목록(매니페스트: 경로 · 크기 · 시각 · SHA-256 · 해시 이력)을
#        <데이터 폴더>/manifests/<root>/<PC>.json 으로 주고받아 Missing / Outdated / Ahead / Only here / Conflict 판정.
#        하위 탭 Status · Roots(추적 루트 여러 개, PC 별 경로) · Excluded(루트별 제외 경로 - 공유 / 이 PC 만, 무시 패턴).
#        새 app/core/sync_settings · sync_manifest · sync_compare, app/ui/sync_tab. 계획 docs/plans/A00210_FileManager_sync_tracker_plan.md

# 01.48  트리 펼치기 - 화살표로 펼치면 한 단계만, Shift + 펼치기/접기 = 아래 전부 (Sync > Status · File Manager 파일 목록 · Path Structure 미리보기 · Maya > Reference 트리).
#        공용 Framework/qt/MOD_treeExpand_qt_v01
#        Sync: PCs 줄을 한 줄로 - 줄바꿈 라벨 때문에 탭 높이 맞춤이 Status 페이지를 16px 잘랐다.

# 01.49  Sync > Status: Show 기본 전부 체크(OK · Excluded, 키 sync_show_filters / sync_show_excluded) · 처음엔 전부 접힘(펼친 상태는 다시 그려도 유지) · Status 열을 경로 바로 옆으로 · 폴더 줄 = 아래 모든 파일의 상태
#        (Missing (1) · Ahead (2), 다 같으면 OK) · 색 Missing 연한 빨강 / Outdated 노랑 / Conflict 하늘 / OK 초록 · 창 세로 2.2 배(트리 힌트 1075).
#        Sync > Excluded: 왼쪽에 이 PC 루트 폴더 트리(체크박스, 게으른 읽기) - Exclude Checked (All PCs / This PC).
#        Framework tabFit: 스크롤 칸 안의 중첩 탭도 hfw 경로 - 긴 Status 페이지를 두 번 빼 창이 246px 로 쪼그라들던 것.

# 01.50  Sync: PC 표시 이름 - 위쪽 `PC Names...` 창에서 PC 마다 툴 안 이름(예: Office / Home)을 붙인다. 빈 칸 = 컴퓨터 이름(COMPUTERNAME).
#        _sync_settings.json 의 pc_names 로 모든 PC 공유(푸시하면 다른 PC 에도). This PC 라벨 · PCs 줄 · PC 열 머리 · 상태 글자(get from / send to) ·
#        요약 열 · 툴팁 · Export List 에 이름. 매니페스트 파일 이름은 컴퓨터 이름 그대로(이름을 바꿔도 이력이 끊기지 않는다).

# 01.51  Sync > Status: 빈 폴더도 트리에(예: scenes/1999_=== - 복사본). 스캔이 가장 안쪽 빈 폴더를 매니페스트 empty_dirs 에 적고,
#        PC 마다 있음 / 없음으로 Empty folder(OK) · Missing · Only here. 위 폴더 줄 상태에도 센다. 옛 매니페스트(키 없음)는 판정에서 뺀다 - 다시 스캔하면 들어간다.

VERSION = "01.51"
LAST_UPDATE = "2026-11-06"
