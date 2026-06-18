---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-06-18
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-06-18 (오늘)

> [!summary] 신규 툴 A00230 StartupTool — 부팅 시 지정 폴더 자동 팝업(JSON 관리) + A00220 BackupTool — 주기적 자동 백업(standalone PySide) + A00110 animTool Follow 탭(target 추종 베이크) + A00210 FileManager Lineage 탭(파일 브랜치/병합 그래프)
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
