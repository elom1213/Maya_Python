# Maya Python Tools — Rigging · Facial · Pipeline Automation

**Autodesk Maya / 게임 파이프라인용 Python 툴 모음** — 리깅 · 모델링 · 페이셜 작업 자동화 스크립트와
독립 실행(standalone) Qt 앱을 직접 설계·개발한 포트폴리오 저장소입니다.

> 작성자: **Ji Hun Park (Junny)** · Technical Artist / Rigging & Pipeline Tools Developer

---

## 🇬🇧 At a glance (English summary)

A portfolio of **production-grade Python tooling for Autodesk Maya and game pipelines**, written and
maintained by **Ji Hun Park (Junny)**, a Technical Artist focused on rigging, facial, and pipeline automation.

It contains **40+ in-house tools** spanning two architectures — **in-Maya `maya.cmds` / PySide UIs** and
**standalone PySide (Qt) desktop apps** — built on a **shared framework** (reusable widgets, theming,
path management, undo handling, drag-&-drop installers). Domains include character **rigging** (FKIK,
control rigs, skin weight transfer, constraint conversion), **facial / MetaHuman** setup (RBF solver →
blendshape auto-connection, PoseWrangler corrective extraction from Houdini cloth caches), **modeling**
(blendshape editing, mesh diagnostics/repair), **Maya → Unreal Engine bridging** (KawaiiPhysics,
Control Rig constraint & item-array node generation), and **standalone pipeline utilities**
(file/version manager, auto-backup, path launcher, startup automation, CSV tools).

👉 **New here? Start in [`JUN_All/`](JUN_All/)** — the active framework and all current tools.
Tool-by-tool documentation lives in [`JUN_All/docs/`](JUN_All/docs/), and a narrative work summary in
[`JUN_All/docs/portfolio/portfolio_EN.md`](JUN_All/docs/portfolio/portfolio_EN.md).

---

## ✨ 주요 툴 (Highlights)

> 스크린샷/데모는 순차적으로 추가할 예정입니다. (이미지 자리: `JUN_All/docs/assets/`)

### 페이셜 / MetaHuman
- **`A00090_ConnectionBuilder`** — MetaHuman 페이셜 리그의 **RBF 솔버 → 드라이버 → 블렌드셰이프**
  어트리뷰트 연결을 규칙(JSON) 기반으로 자동화. PySide 앱, core/ui 분리 설계.
- **`A00280_correctiveFromCache`** — MetaHuman **RBF(PoseWrangler) 의상 주름 코렉티브**를 후디니
  Alembic 캐시에서 **일괄 추출**. (타겟수 × 관절수) 수동 반복을 버튼 하나로 대체.
- **`A00100_jsonEditor_MH`** — MetaHuman용 JSON 정렬·편집 도구.

<!-- ![ConnectionBuilder](JUN_All/docs/assets/A00090_ConnectionBuilder.png) -->

### Unreal Engine 연동 (Maya → UE 브릿지)
> 언리얼 노드는 **텍스트로 붙여넣기가 가능**하다는 점을 이용해, 마야 씬의 리그 데이터를 읽어
> **UE 노드 텍스트를 생성 → 클립보드 복사 → 그래프에 `Ctrl+V`** 하는 변환기 3종.

- **`A00080_KWI_creator_V03`** — Unreal **KawaiiPhysics** AnimGraph 노드(base·세팅·LOD)를 템플릿 치환으로
  대량 생성. 마야에서 선택한 타깃 본 목록을 읽어 노드를 자동 배치하고, **Bone Constraints Data Asset**
  텍스트도 생성(Constraints 탭).
- **`A00260_ConstraintConverter`** — 마야 **컨스트레인트 세팅 → 언리얼 Control Rig Parent/Position/Rotation
  Constraint** 노드로 변환. 축별 필터 · 자동 가로 배치 · 노드 간 ExecutePin(RigVMLink) 연결까지 생성.
- **`A00350_ArrayCreator`** — 마야 오브젝트 리스트 → Control Rig **Item Array 노드**(`TArray<FRigElementKey>`)
  텍스트로 변환. Element Type 지정, 순서 조정(Up/Down/Reverse).
- **`A00320_ARKitCurveTool`** — Unreal `Add ARKit Curves to Skeleton` 동작을 분석해 마야 측에서 재현.

### 리깅 (Rigging)
- **`A00145_RigConnect`** — 리깅 연결 통합 툴(Match · Matrix Constraint · Connect Closest ·
  스킨 웨이트→컨스트레인트 · 오프셋 그룹 생성 · **Constraint Transfer**).
- **`A00130_ControlRig`** — 컨트롤 리그 생성. · **`A00120_FKIK` / `A00190_FKIK_General_Tool`** — FK/IK 스위칭·베이크.
- **`A00020_move_skineWeightTool` / `A00270_skinMigrate`** — 스킨 웨이트 이동·전이(토폴로지 다른 메시 마이그레이션).
- **`A00060_jointTool_V02`** — 조인트 작업(커브/분할 생성 · 트위스트 Aim). · **`A00010_humanIKTool_V02`** — HumanIK 세팅.
- **`A00170_driverTool`**(Remap·Spherical·AttachCrv 탭), **`A00150_remapVal`**, **`A00160_sphericalEye`** — 드리븐 키/리맵/아이 리그.

### 애니메이션 · 모델링 · 메시
- **`A00110_animTool`** — 키 복사/미러/베이크·Follow·Graph Focus(레거시 알고리즘 이식). · **`A00180_abSymMesh`** — 메쉬 대칭/블렌드셰이프(OpenMaya 재구현).
- **`A00290_BSTool`** — blendShape 편집(**마야 기본 Shape Editor 대체** · Edit BS · Base Shape 탭). · **`A00300_meshDoctor`** — 메시 **읽기전용 진단 + 안전 원클릭 수정**(배치 진단 요약 테이블, JSON/TXT 로그).
- **`A00040_file_exporter_V02`** — 타입 필터 기반 익스포트 자동화. · **`A00050_uvTool`**, **`A00030_quickTool`**, **`A00200_CSV_tool`**.

### 씬 / 선택 · 네이밍 유틸
- **`A00310_SearchTool`** — 오브젝트를 **타입·이름으로 골라 선택**(Selection·Search 탭). · **`A00340_SelectionTool`** — 자주 쓰는 선택 세트를 버튼·프로파일로 재선택(버튼별 색 지정).
- **`A00360_SortTool`** — 월드 X/Y/Z·이름·타입 기준 정렬 + 아웃라이너 재정렬. · **`A00330_NamingTool`** — 리네임/Quick Rename.
- **`A00250_SceneMemo`** — 오브젝트별 메모를 씬에 저장.

### 독립 실행(Standalone) / in-Maya PySide 앱
- **`A00210_FileManager`** — 파일/버전 매니저(파일 참조관계 **Lineage 그래프 시각화**, Remote Git ↔ Local/NAS Source Mode, 폴더 구조 캡처·재생성). · **`A00211_RefLineage`** — 씬 reference → Lineage 내보내기.
- **`A00220_BackupTool`** — 지정 파일 **주기적/저장 시점 자동 백업**(크래시 대비). · **`A00240_PathTool`** — 자주 쓰는 폴더를 버튼/프로파일로 빠르게 열기.
- **`A00370_ToolLauncher`** — 툴 폴더 경로를 버튼에 담아 JUN 툴을 즉시 실행(PC가 바뀌어도 경로 자동 재매핑).
- **`A00230_StartupTool`** — Windows 로그인 시 폴더 팝업 + standalone 툴 자동 실행.
- PySide 앱은 **PyInstaller로 `.exe` 빌드** 가능.

📖 각 툴의 상세 사용법·구조 문서: **[`JUN_All/docs/`](JUN_All/docs/)** (예: [animTool](JUN_All/docs/A00110_animTool.md),
[RigConnect](JUN_All/docs/A00145_RigConnect.md), [meshDoctor](JUN_All/docs/A00300_meshDoctor.md),
[FileManager](JUN_All/docs/A00210_FileManager.md))
📝 작업 내역 요약(포트폴리오 문구): **[국문](JUN_All/docs/portfolio/portfolio_KR.md)** · **[English](JUN_All/docs/portfolio/portfolio_EN.md)**

---

## 🛠 기술 스택 (Tech Stack)

| 분류 | 내용 |
|------|------|
| 언어 | Python 3 |
| DCC API | Autodesk Maya `maya.cmds` · **OpenMaya**, Unreal Engine 노드 텍스트 생성, Houdini Alembic 캐시 연동 |
| UI | `maya.cmds` 네이티브 위젯, **PySide2 & PySide6** (Qt), qss 컬러 테마 14종 |
| 빌드/배포 | **PyInstaller** (`.exe`), 드래그&드롭 셸프 설치 시스템, 릴리스 빌더(툴+Framework+문서 패키징) |
| 아키텍처 | 공용 **Framework**(재사용 위젯 · 테마 · `PathManager` · 공용 `undo_chunk` · **UUID 기반 오브젝트 리스트**), **core/ui 분리**, 모듈 리로더 |
| 도메인 | 캐릭터 리깅, 페이셜/MetaHuman(RBF·PoseWrangler 코렉티브), 스킨 웨이트 전이, 블렌드셰이프·메시 진단, UE KawaiiPhysics·Control Rig 연동, 파이프라인 유틸 |

---

## 📁 저장소 구조 (Repository map)

| 경로 | 설명 |
|------|------|
| **[`JUN_All/`](JUN_All/)** | **현행 (active)** — 공용 프레임워크 + 모든 신규 툴. **여기부터 보세요.** |
| [`JUN_All/tools/`](JUN_All/tools/) | 개별 툴 (번호 접두사 `A000XX`로 정렬) |
| [`JUN_All/Framework/`](JUN_All/Framework/) | 모든 툴이 공유하는 공용 인프라(위젯·테마·경로 관리) |
| [`JUN_All/docs/`](JUN_All/docs/) | 툴별 상세 사용법·설계 문서 + 작업 로그(`WORKLOG.md`) + 학습 노트(`study/`) |
| [`JUN_All/docs/portfolio/`](JUN_All/docs/portfolio/) | 작업 내역 요약 (국문 · English) |
| [`_archive/`](_archive/) | 동결된 옛 세대 코드와 학습 메모 — **성장 과정·리팩터링 이력** (참고용) |
| `JUN_memo/` | 개인 메모 (저장소 추적 제외) |

> `_archive/`는 초기 단일 파일 스크립트(`01_Modules`)부터 현재의 모듈화된 프레임워크(`JUN_All`)까지의
> **발전 과정**을 보존한 영역입니다. 레거시 → 현행으로의 리팩터링 매핑은 [`_archive/README.md`](_archive/README.md) 참고.

---

## 🧩 아키텍처 개요

툴은 두 가지 형태 중 하나이며, 공통 **Framework**(재사용 위젯 · qss 테마 · `PathManager`)를 공유합니다.

```
(A) in-Maya 툴      — maya.cmds UI. 드래그&드롭으로 셸프 버튼 설치 → run() 실행
(B) PySide(Qt) 앱   — app/core(로직)와 app/ui(화면)를 분리. Maya 내 실행 또는 독립 실행(.exe 빌드) 지원
```

```
JUN_All/
├── Framework/        # 공용 위젯 · 테마 · 경로 관리 (모든 툴이 import)
├── tools/A000XX_*/   # 개별 툴 (위 (A)/(B) 두 아키텍처)
├── dev/              # 리로더 · 릴리스 빌더 (배포 제외)
└── docs/             # 툴별 문서 · WORKLOG
```

---

## 🚀 실행 / 설치 (Quick start)

- **Maya 툴 (A)**: 해당 툴의 `__dragDrop_<번호>.py`를 Maya 뷰포트로 **드래그&드롭** → 셸프 버튼 생성 →
  버튼 클릭 또는 `tools.A000XX_name.run(True)` 실행.
- **Qt 앱 (B)**: 툴 폴더의 `launch.py` → `run()` 호출.
- **exe 빌드**: 툴 폴더의 `build_exe.bat` (PyInstaller).

자세한 설치/실행은 각 툴의 [`JUN_All/docs/`](JUN_All/docs/) 문서를 참고하세요.

---

## 📬 Contact

- **Email**: [junny.park1213@gmail.com](mailto:junny.park1213@gmail.com)
- **GitHub**: [github.com/elom1213](https://github.com/elom1213)
- **Portfolio — 리깅 (Rigging)**: [Notion](https://early-aletopelta-1fe.notion.site/2d8c7945011c805f85f7de708797b440)
- **Portfolio — 애니메이션 (Animation)**: [Notion](https://early-aletopelta-1fe.notion.site/2d8c7945011c808da505d821605f8ed7)
- **Portfolio (Web)**: [junnyparkall.myportfolio.com](https://junnyparkall.myportfolio.com/)

---

<sub>© Ji Hun Park (Junny). 개인 제작 툴 모음입니다. 코드 인용 시 출처를 밝혀 주세요.</sub>
