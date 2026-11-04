# Python Script by Ji Hun Park
# last Update date : 2026-11-03
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

VERSION = "01.45"
LAST_UPDATE = "2026-11-03"
