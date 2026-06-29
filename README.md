# Maya Python Tools — Rigging · Facial · Pipeline Automation

**Autodesk Maya / 게임 파이프라인용 Python 툴 모음** — 리깅 · 모델링 · 페이셜 작업 자동화 스크립트와
독립 실행(standalone) Qt 앱을 직접 설계·개발한 포트폴리오 저장소입니다.

> 작성자: **Ji Hun Park (Junny)** · Technical Artist / Rigging & Pipeline Tools Developer

---

## 🇬🇧 At a glance (English summary)

A portfolio of **production-grade Python tooling for Autodesk Maya and game pipelines**, written and
maintained by **Ji Hun Park (Junny)**, a Technical Artist focused on rigging, facial, and pipeline automation.

It contains **35+ in-house tools** spanning two architectures — **in-Maya `maya.cmds` / PySide UIs** and
**standalone PySide (Qt) desktop apps** — built on a **shared framework** (reusable widgets, theming,
path management, drag-&-drop installers). Domains include character **rigging** (FKIK, control rigs, skin
weight transfer, constraint conversion), **facial / MetaHuman** setup (RBF solver → blendshape
auto-connection, corrective extraction), **modeling** (blendshape editing, mesh diagnostics/repair),
**Unreal Engine physics** (KawaiiPhysics node generation), and **standalone pipeline utilities**
(file/version manager, auto-backup, path launcher, startup automation, CSV tools).

👉 **New here? Start in [`JUN_All/`](JUN_All/)** — the active framework and all current tools.
Tool-by-tool documentation lives in [`JUN_All/docs/`](JUN_All/docs/).

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

### Unreal Engine 연동
- **`A00080_KWI_creator_V02/V03`** — Unreal **KawaiiPhysics** AnimGraph 노드를 템플릿 치환으로
  대량 생성하는 텍스트 제너레이터. 타깃 본 목록을 읽어 노드를 자동 배치.
- **`A00260_ConstraintConverter`** — 마야 **컨스트레인트 세팅 → 언리얼 Control Rig Parent Constraint**
  노드 텍스트로 변환·클립보드 복사(`Ctrl+V` 로 그래프에 생성).

### 리깅 (Rigging)
- **`A00130_ControlRig`** — 컨트롤 리그 생성. · **`A00120_FKIK` / `A00190_FKIK_General_Tool`** — FK/IK 스위칭·베이크.
- **`A00020_move_skineWeightTool` / `A00270_skinMigrate`** — 스킨 웨이트 이동·전이(토폴로지 다른 메시 마이그레이션).
- **`A00060_jointTool_V02`** — 조인트 작업. · **`A00145_RigConnect`** — 매칭/컨스트레인트/연결 통합.
- **`A00170_driverTool`**(Remap·Spherical·AttachCrv 탭), **`A00150_remapVal`**, **`A00160_sphericalEye`** — 드리븐 키/리맵/아이 리그.

### 애니메이션 · 모델링 · 메시
- **`A00110_animTool`** — 키 복사/붙여넣기·미러·베이크(레거시 알고리즘 이식). · **`A00180_abSymMesh`** — 메쉬 대칭/블렌드셰이프.
- **`A00290_BSTool`** — blendShape 편집(Edit BS · Base Shape 탭). · **`A00300_meshDoctor`** — 메시 **읽기전용 진단 + 안전 원클릭 수정**(JSON/TXT 로그).
- **`A00050_uvTool`**, **`A00040_file_exporter`**, **`A00200_CSV_tool`**.

### 씬 / 선택 유틸
- **`A00310_SearchTool`** — 오브젝트를 **타입·이름으로 골라 선택**(Selection·Search 탭). · **`A00250_SceneMemo`** — 오브젝트별 메모를 씬에 저장.

### 독립 실행(Standalone) / in-Maya PySide 앱
- **`A00210_FileManager`** — 파일/버전 매니저(Remote Git ↔ Local/NAS Source Mode). · **`A00211_RefLineage`** — 씬 reference → Lineage 내보내기.
- **`A00220_BackupTool`** — 지정 파일 **주기적 자동 백업**(크래시 대비). · **`A00240_PathTool`** — 자주 쓰는 폴더를 버튼/프로파일로 빠르게 열기.
- **`A00230_StartupTool`** — Windows 로그인 시 폴더 팝업 + standalone 툴 자동 실행.
- PySide 앱은 **PyInstaller로 `.exe` 빌드** 가능.

📖 각 툴의 상세 사용법·구조 문서: **[`JUN_All/docs/`](JUN_All/docs/)** (예: [animTool](JUN_All/docs/A00110_animTool.md),
[RigConnect](JUN_All/docs/A00145_RigConnect.md), [meshDoctor](JUN_All/docs/A00300_meshDoctor.md),
[FileManager](JUN_All/docs/A00210_FileManager.md))

---

## 🛠 기술 스택 (Tech Stack)

| 분류 | 내용 |
|------|------|
| 언어 | Python 3 |
| DCC API | Autodesk Maya `maya.cmds`, Unreal Engine 텍스트 노드 생성 |
| UI | `maya.cmds` 네이티브 위젯, **PySide2 & PySide6** (Qt) |
| 빌드/배포 | **PyInstaller** (`.exe`), 드래그&드롭 셸프 설치 시스템 |
| 아키텍처 | 공용 **Framework**(재사용 위젯·테마·경로 관리), **core/ui 분리**, 모듈 리로더 |
| 도메인 | 캐릭터 리깅, 페이셜/MetaHuman, 스킨 웨이트 전이, 블렌드셰이프·메시 진단, UE KawaiiPhysics·Control Rig 연동, 파이프라인 유틸 |

---

## 📁 저장소 구조 (Repository map)

| 경로 | 설명 |
|------|------|
| **[`JUN_All/`](JUN_All/)** | **현행 (active)** — 공용 프레임워크 + 모든 신규 툴. **여기부터 보세요.** |
| [`JUN_All/tools/`](JUN_All/tools/) | 개별 툴 (번호 접두사 `A000XX`로 정렬) |
| [`JUN_All/Framework/`](JUN_All/Framework/) | 모든 툴이 공유하는 공용 인프라(위젯·테마·경로 관리) |
| [`JUN_All/docs/`](JUN_All/docs/) | 툴별 상세 사용법·설계 문서 + 작업 로그(`WORKLOG.md`) |
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
