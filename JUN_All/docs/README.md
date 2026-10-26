# JUN_All 툴 사용법 문서 아카이브

이 폴더는 `JUN_All/tools/` 안의 각 툴에 대한 **사용법 · 폴더 구조 안내 문서**를 모아두는 곳이다.
새 툴을 만들거나 기존 툴을 업데이트하면 여기에 한글 안내 문서를 추가/갱신한다.

> **하위 폴더 `plans/`** — 사용법이 아니라 **기능 개발 계획 · 설계 결정 기록**(개발 문서)을 모은다.
> 파일명은 `<툴 폴더명>_<기능>.md` 규칙(예: `A00150_remapVal_sine_wave_mode.md`).
>
> **학습 노트는 별도 저장소로 이전됨** — 특정 툴 안내가 아닌 **작업 방법론 · 기법 학습 노트**는
> 2026-08-21 부로 [`elom1213/JUN_Study`](https://github.com/elom1213/JUN_Study) 로 옮겼다
> (로컬: `JP/0030_maya_python_JUN/JUN_Study/`). 자세한 사유는 [study/README.md](study/README.md) 참고.

> 정리하면 — `docs/*.md`=툴 안내, `docs/plans/`=개발 계획, 학습 노트=별도 저장소 `JUN_Study`.

---

## 문서 목록

| 툴 | 도메인 | 문서 |
|----|--------|------|
| `A00030_quickTool` | 잡동사니 / 퀵 유틸 | [A00030_quickTool](A00030_quickTool.md) |
| `A00060_jointTool_V03` | 리깅 / 조인트 생성 (Create·Orient·Chain·Curve·Select) | [A00060_jointTool_V03](A00060_jointTool_V03.md) |
| `A00060_jointTool_V02` | 〃 (탭 재분류 전 · 보존) | [A00060_jointTool_V02](A00060_jointTool_V02.md) |
| `A00080_KWI_creator_V03` | 언리얼 / KawaiiPhysics | [A00080_KWI_creator_V03](A00080_KWI_creator_V03.md) |
| `A00110_animTool` | 애니메이션 | [A00110_animTool](A00110_animTool.md) |
| `A00130_ControlRig_V02` | 리깅 / 컨트롤러(cage) 세팅 — 템플릿 조인트 | [A00130_ControlRig_V02](A00130_ControlRig_V02.md) |
| `A00140_ConnectClosest` | 리깅 / 페이셜 | [A00140_ConnectClosest](A00140_ConnectClosest.md) |
| `A00145_RigConnect` | 리깅 / 연결·매칭·컨스트레인트·**미러** 통합 | [A00145_RigConnect](A00145_RigConnect.md) |
| `A00150_remapVal` | 리깅 | [A00150_remapVal](A00150_remapVal.md) |
| `A00160_sphericalEye` | 리깅 / 페이셜 | [A00160_sphericalEye](A00160_sphericalEye.md) |
| `A00180_abSymMesh` | 모델링 / 블렌드셰이프 | [A00180_abSymMesh](A00180_abSymMesh.md) |
| `A00210_FileManager` | 파이프라인 / 파일·버전 기록 (standalone) · **Maya > Reference**(마야 파일들의 레퍼런스를 트리로 보고 체크한 것을 각 파일에 임포트해 제자리 저장, 마야 일은 mayapy 워커) · **Maya > Export**(세트 규칙 `Bake` 가 있는 파일 솎아내기 · 재생 범위 · fps · 버전 표 · `bakeResults` → FBX / FBX 만, 최상위 본은 월드로, 이름 Find/Replace + Insert, Overwrite 팝업) | [A00210_FileManager](A00210_FileManager.md) |
| `A00260_ConstraintConverter` | 리깅 / 언리얼 | [A00260_ConstraintConverter](A00260_ConstraintConverter.md) |
| `A00270_skinMigrate` | 리깅 / 스킨 | [A00270_skinMigrate](A00270_skinMigrate.md) |
| `A00280_correctiveFromCache` | 페이셜·리깅 / RBF 코렉티브 | [A00280_correctiveFromCache](A00280_correctiveFromCache.md) |
| `A00290_BSTool` | 블렌드셰이프 / 페이셜 | [A00290_BSTool](A00290_BSTool.md) |
| `A00320_ARKitCurveTool` | 언리얼 / ARKit·스켈레톤 커브 (참조 코드) | [A00320_ARKitCurveTool](A00320_ARKitCurveTool.md) |
| `A00330_NamingTool` | 네이밍 / 리네임 | [A00330_NamingTool](A00330_NamingTool.md) |
| `A00340_SelectionTool` | 선택 / 리깅·애니 (오브젝트 재선택 버튼) | [A00340_SelectionTool](A00340_SelectionTool.md) |
| `A00410_SecondaryMotion` | 애니메이션 / 2차 모션 (FK 체인 관성·찰랑임) | [A00410_SecondaryMotion](A00410_SecondaryMotion.md) |
| `A00420_Wrapper` | 모델링·페이셜 / 커브 가이드 래핑 (다른 토폴로지 메시 맞추기) | [A00420_Wrapper](A00420_Wrapper.md) |
| `A00480_FileTool` | 파일 입출력 · 경로 (Export / Import / Path / **Reference** — A00040_V02 + quickTool File·Import 통합, 씬 레퍼런스 중첩 트리 · 탐색기 열기 · 경로 복사) | [A00480_FileTool](A00480_FileTool.md) |
| `A00560_JaliBatch` | 페이셜 / 립싱크 **대량** (standalone) — VisemeNet 변환 결과 폴더 → 대사마다 JALI 컨트롤러를 레퍼런스하고 키를 베이크한 **클립 `.mb`**(mayapy 워커 한 프로세스, 도장 + 매니페스트) · Validate / Repath | [A00560_JaliBatch](A00560_JaliBatch.md) |
| `A00570_JaliReview` | 페이셜 / 립싱크 **검수** (in-Maya) — 아바타 + 클립 레퍼런스(ns CLIP), Prev/Next/Swap, 레퍼런스 커브 편집 → Save Clip Edits(`saveReference`), ARKIT_OUT → 블렌드셰이프 연결 | [A00570_JaliReview](A00570_JaliReview.md) |
| `A00580_FacialBoardBuilder` | 페이셜 — ARKit 52 컨트롤 보드(`Ctl_Only_V05`)를 명세 json 에서 생성 · CSV 베이크 · 검증 (헤드리스, UE Control Rig 는 2단계) | [A00580_FacialBoardBuilder](A00580_FacialBoardBuilder.md) |
| `A00380_MeshTool` | 모델링 / 메시 진단 · 편집 (MeshDoctor · Peak · Match) | [A00380_MeshTool](A00380_MeshTool.md) |
| `A00300_meshDoctor` | 〃 (A00380 의 MeshDoctor 탭으로 이식됨 · 보존) | [A00300_meshDoctor](A00300_meshDoctor.md) |

### 공용 위젯 · 헬퍼 (Framework)

특정 툴이 아니라 **여러 툴이 함께 쓰는 위젯/헬퍼**의 동작·옵션 문서. 툴 문서는 "재사용 위젯 …" 이라고만 적고
자세한 동작은 아래를 참조한다.

| 모듈 | 내용 | 문서 |
|------|------|------|
| `Framework/qt/MOD_tsl_qt_v01.py` | 공용 리스트(TSL) 위젯 — Select/Add/Del/Up/Down/Sort, **Order(선택 순서 유지)**, UUID 보관, **요약 모드(`list_limit`)** | [Framework_MOD_tsl_qt](Framework_MOD_tsl_qt.md) |
| `Framework/qt/MOD_filter_qt_v01.py` | 공용 **검색/필터** 위젯 — 입력 즉시 일치 항목만 표시, "보이는 것이 작업 대상" 헬퍼 | [Framework_MOD_filter_qt](Framework_MOD_filter_qt.md) |
| `Framework/qt/MOD_fileTree_qt_v01.py` + `Framework/core/tree_scanner.py` · `prefetcher.py` | 공용 **폴더 트리** 위젯 — A00240 Tree 탭을 그대로 승격(Adaptive · File Types · Omit · Refresh · Expand · Reveal/Copy · 정션). `checkable_files` 로 파일 행 체크박스(Shift 다중 체크, 경로로 기억), `default_types`. A00240 · A00210 Maya 탭이 쓴다 | [Framework_MOD_fileTree_qt](Framework_MOD_fileTree_qt.md) |
| `Framework/qt/MOD_checkTree_qt_v01.py` | 체크박스 `QTreeWidget` 에 붙이는 **다중 선택 + 다중 체크** 동작 — checkList 의 트리 판. 체크박스 유무는 `CheckStateRole` 데이터로 가른다(QTreeWidgetItem 은 기본 플래그가 checkable) | [Framework_MOD_checkTree_qt](Framework_MOD_checkTree_qt.md) |
| `Framework/qt/MOD_checkList_qt_v01.py` | 체크박스 `QListWidget` 에 붙이는 **다중 선택 + 다중 체크** 동작 — Shift/Ctrl 로 고른 행을 체크박스 한 번(또는 Space)으로 함께 켜고 끈다 | [Framework_MOD_checkList_qt](Framework_MOD_checkList_qt.md) |
| `Framework/qt/MOD_tokenName_qt_v01.py` + `Framework/core/token_naming.py` | **토큰 이름 위젯** — Profile(json) + 토큰 칸(Custom / Numbering / Set's Name, Add · Delete Token, 가로 스크롤, 미리보기). 규칙 묶음 · 프로파일 저장은 core. A00330 Token · A00480 Naming 이 공유 | [Framework_MOD_tokenName_qt](Framework_MOD_tokenName_qt.md) |
| `Framework/qt/MOD_expand_qt_v01.py` | 공용 **Expand(별도 창)** 패널 — 본문을 독립 창으로 빼고 되돌린다. **복제가 아니라 이동**이라 값이 어긋날 여지가 없다 | [Framework_MOD_expand_qt](Framework_MOD_expand_qt.md) |
| `Framework/qt/MOD_devMode_qt_v01.py` + `Framework/core/dev_mode.py` | 메뉴 바 **`Dev Mode`** (Developer / Release (shared tool)) — 개발자가 배포 화면을 그대로 미리 본다. 개발자 모드 판정(릴리즈본 = 툴 안에 Framework 동봉 / dev = `config.py` 의 `DEV_MODE`)은 core. A00330 · A00120 이 쓴다 | [Framework_MOD_devMode_qt](Framework_MOD_devMode_qt.md) |
| `Framework/qt/MOD_progress_qt_v01.py` | 공용 **진행률 팝업** — 오래 걸리는 작업의 0~100% 게이지 모달 창. 단계 가중치 자동 재정규화, core 는 `progress(done, total)` 콜백만 안다 | [Framework_MOD_progress_qt](Framework_MOD_progress_qt.md) |
| `Framework/qt/MOD_falloffCurve_qt_v01.py` | 공용 **falloff 커브 편집기** — 캔버스 / +Interpolation·Presets 패널 / 비모달 팝업. 모델은 `Framework/core/falloff_curve.py`(Qt·maya 비의존) | [Framework_MOD_falloffCurve_qt](Framework_MOD_falloffCurve_qt.md) |
| `Framework/core/maya_shape.py` | **트랜스폼 → 셰이프 확정** 헬퍼 — `extendToShape()` 가 엉뚱한 셰이프를 집는 함정을 막는다(`kInvalidParameter` 원인) | [Framework_maya_shape](Framework_maya_shape.md) |
| `Framework/core/maya_skin.py` | skinCluster 웨이트 **인덱스 함정**(물리 vs 논리) — `get/setWeights` 는 물리 인덱스. undo 뒤 재바인드가 죽던 원인 | [Framework_maya_skin](Framework_maya_skin.md) |
| `Framework/core/control_shapes.py` | **컨트롤러 커브 셰이프 34종** 공용 라이브러리(`Framework/rules/control_shapes.json`) — `bs_controls` 의 CV 데이터를 툴 밖으로 올렸다 | [Framework_control_shapes](Framework_control_shapes.md) |
| `Framework/core/log_levels.py` | 로그 줄의 **`[LEVEL]` 표식 -> 색** 공용 규칙 — `[WARN]` 노랑 · `[OK]` 초록. 밝은/어두운 테마용 색 한 쌍을 갖는다 | [Framework_log_levels](Framework_log_levels.md) |
| `Framework/core/mirror_tokens.py` | 좌/우 미러 **토큰 규칙 공용화**(`Framework/rules/mirror_tokens.json`) — 이름 미러링은 **경계 매칭**으로 `arm_lower` 같은 오탐을 막는다 | [Framework_mirror_tokens](Framework_mirror_tokens.md) |
| `Framework/core/shell_integration.py` | Windows **시작 메뉴 바로가기**(.lnk + AppUserModelID, PowerShell `Add-Type` C#) + 시작 화면 고정 시도. standalone 툴의 `File > Add to Start Menu`(A00240 · A00220). Windows 10 · 11 | [Framework_shell_integration](Framework_shell_integration.md) |
| `Framework/jali/` + `Framework/core/mayapy_runner.py` · `Framework/qt/MOD_mayapyProcess_qt_v01.py` | **JALI 립싱크 공용 코어**(A00540 app/core 승격: lipsync_data · mapping · sequence · keyer · scene + bake · clip_stamp · clip_manifest · time_units, 매핑 json) 와 **mayapy 워커 러너**(A00210 승격, `JUNMSG` 프로토콜 · QProcess 진행률 팝업). A00540 · A00560 · A00570 · A00210 | [Framework_jali](Framework_jali.md) |
| `Framework/core/maya_fbx.py` | **FBX 플러그인 · "선택한 것만" FBX 내보내기 헬퍼**(A00480 승격: `ensure_fbx_plugin` · 타입 필터 · `collect_export_nodes` · `fbx_options`(IncludeChildren / InputConnections / BakeComplexAnimation 한시 변경) · `export_selected`). A00480 Export · A00210 Maya > Export | [Framework_maya_fbx](Framework_maya_fbx.md) |
| `Framework/qt/pin_style.py` | 체크형 **`Pin`(Always on Top) 버튼의 켜짐 색** — `apply_pin_style(button)` 한 줄로 켜진 동안 연한 빨강(`:checked` 색만, 크기는 테마 그대로). A00240 · A00220 · A00370 | [Framework_pin_style](Framework_pin_style.md) |

### 배치 · 패키징 (툴 하나가 아니라 전체에 걸친 것)

| 주제 | 내용 | 문서 |
|------|------|------|
| **릴리즈 배치** | dev 트리와 릴리즈본은 **폴더 모양이 다르다** — `Framework` 는 툴 안에 동봉되고 `config.py` · `dev/` 는 실리지 않는다. 진입 파일(`launch.py` · `launcher.py`)이 지켜야 할 규약과 "남의 PC" 검증법 | [Release_Layout](Release_Layout.md) |
| **릴리즈 빌더** | 릴리즈본을 만드는 개발 툴(`JUN_All/dev/A00510_release_builder`, 옛 `release_builder_QT`, `__dragDrop_A00510.py` 로 셸프 설치) | [A00510_release_builder](A00510_release_builder.md) |
| **아이콘 빌더** | `tools/*/icon/*.svg` 와 `dev/*/icon/*.svg` 를 32px png 로(옵션 .ico), 셸프 `Icons` 버튼 또는 mayapy (`dev/A00520_icon_builder`, 옛 `dev/build_icons.py`) | [A00520_icon_builder](A00520_icon_builder.md) |
| **의존성 체크** | Qt 바인딩 · pymel · maya.cmds 가 이 인터프리터에서 import 되는지 표로 (`dev/A00530_dependency_check`, 옛 `dev/check_dependencies.py` 는 재노출) | [A00530_dependency_check](A00530_dependency_check.md) · [DEPENDENCIES](DEPENDENCIES.md) |
| **리로더** | Framework / tools 모듈을 전부 다시 읽는 개발용 셸프 버튼(`JUN_All/dev/A00500_reloader`, `__dragDrop_A00500.py` 로 설치, `__dragDrop_A00500_pycache.py` 는 `__pycache__` 비우기). 각 툴 `launch.py` 의 `dev.reloader_v02` 는 이것의 재노출 | [A00500_reloader](A00500_reloader.md) |

---

## 새 문서 추가 규칙

1. **파일명은 툴 폴더명과 동일**하게 만든다. 예: `tools/A00150_Foo` → `docs/A00150_Foo.md`.
2. 문서 본문은 **한글**로 작성한다. (UI/코드 식별자·로그 예시는 영어 그대로 인용)
3. 아래 **문서 템플릿** 섹션 순서를 따른다.
4. 문서를 추가하면 위 **문서 목록** 표에 한 줄 등록한다.

---

## 문서 템플릿

각 툴 문서는 다음 순서를 표준으로 한다.

1. **개요** — 무엇을 하는 툴인지 한두 문단.
2. **폴더 구조** — 실제 파일 트리와 각 모듈의 역할(특히 core/ui 분리).
3. **설치** — 셸프 버튼 설치 방법(드래그&드롭 등).
4. **실행** — 셸프 버튼 또는 `run()` 호출 방법.
5. **UI 구성** — 화면 요소(버튼/리스트/체크박스/로그)의 의미.
6. **사용 순서** — 실제 작업 단계(①②③…).
7. **동작 규칙** — 내부 매칭/검증 규칙, 주의할 동작.
8. **로그 · 문제 해결** — 로그 메시지 예시와 자주 겪는 문제.
