# CLAUDE.md

Maya / 게임 파이프라인용 Python 툴 모음. 리깅 · 모델링 · 페이셜 작업 자동화 스크립트와
독립 실행(standalone) 툴을 개발한다.

- **Author**: Ji Hun Park (Junny / `Dnable_JunnyPark`)
- **대상 DCC**: Autodesk Maya (Python 3 / `maya.cmds`), 일부 Unreal Engine 텍스트 노드 생성
- **OS**: Windows
- **Branch**: 작업은 `dev`, 배포는 `master`

---

## 1. 저장소 구조 (역사적 레이어)

이 repo는 시간순으로 쌓인 여러 세대의 코드를 함께 담고 있다. **신규 작업은 거의 항상 `JUN_All/` 안에서 한다.**
옛 세대 코드와 학습 메모는 모두 **`_archive/`**(동결, read-only) 아래로 아카이빙되어 있다.

| 경로 | 상태 | 설명 |
|------|------|------|
| `JUN_All/` | **현행 (active)** | 현재 프레임워크 + 모든 신규 툴. 아래 2~4장 참고 |
| `_archive/legacy_tools/01_Modules/` | 레거시(단일 파일) | 버전별 파일명(`JUN_PY_*_V01_02.py`)으로 관리되던 옛 Maya 툴 스크립트 |
| `_archive/legacy_tools/01_Modules_Small/` | 스니펫 | 소형 단일 기능 스크립트 |
| `_archive/legacy_tools/03_Modules_Test/` | 실험 | `01_Modules` 툴들의 개발/테스트 버전 |
| `_archive/legacy_tools/04_KWI_generator/` | 레거시 | `A00080_KWI_creator_V02`의 전신 |
| `_archive/legacy_tools/02_Modules_Old/`, `.../00_Old/` | deprecated | 손대지 말 것 |
| `_archive/study_notes/100_Memo/`, `.../101_*/` | 학습 메모 | Python/Maya 테크닉, 페이셜·셀룰러 오토마타 등 실험 노트. 프로덕션 코드 아님 |
| `_archive/legacy_tools/00_RUN/` | 런처 스니펫 | Maya에서 붙여넣어 실행하던 조각 |

> 새 기능을 추가할 때 `_archive/`의 옛 파일을 수정하지 말 것. 참고용으로만 연다.
> 대응되는 기능은 `JUN_All/tools/A000XX_*`로 옮겨져 있으니 그쪽을 본다. (매핑은 `_archive/README.md` 참고)

---

## 2. `JUN_All/` — 현행 프레임워크

```
JUN_All/
├── config.py              # DEV_MODE 플래그
├── core/launcher.py       # (예약됨)
├── Framework/             # 모든 툴이 공유하는 공용 인프라
│   ├── core/path_manager.py   # PathManager: read(0010)/write(0020) 경로 관리
│   ├── ui/                # maya.cmds 기반 공용 위젯 (MOD_*)
│   │   ├── MOD_button_v01.py   # ButtonSpec / Buttons
│   │   ├── MOD_tsl_01_01.py, MOD_tfg_01.py, MOD_cbg_01.py, MOD_optionMenuGrp_v01.py,
│   │   │   MOD_radioCollection_01_01.py
│   │   └── MOD_colorThem.py    # ColorThemeRegistry (예: "coral_01")
│   ├── qt/qt.py           # Qt(PySide) 바인딩 헬퍼
│   ├── themes/theme_manager.py # ThemeManager.load_theme_to_widget(w, "red") → qss 적용
│   └── styles/*.qss       # dark.qss, red.qss
├── dev/                   # 개발 편의 스크립트 (배포 제외)
│   ├── reloader_v02.py        # DEV_MODE면 패키지 트리 전체 importlib.reload
│   ├── reload_path_list.py    # RELOAD_PACKAGES 목록
│   ├── remove_pycache*.py
│   └── build_release.py       # 툴+Framework를 릴리스 폴더로 복사
└── tools/A000XX_*/        # 개별 툴 (아래)
```

`Framework.ui.__init__`는 위젯들을 `JUN_mod_tsl`, `JUN_button__` 등의 별칭으로 노출한다.
maya.cmds 툴은 이 별칭을 import해서 쓴다.

---

## 3. 두 가지 툴 아키텍처

`JUN_All/tools/` 안의 툴은 **번호 접두사**(`A000XX`)로 정렬되며 두 형태 중 하나다.

### (A) Maya in-DCC 툴 — `maya.cmds` UI
예: `A00000_base`(템플릿), `A00010_humanIKTool`, `A00020_move_skineWeightTool`,
`A00030_quickTool`, `A00040_file_exporter`, `A00050_uvTool`, `A00060_jointTool`

```
A000XX_name/
├── __init__.py        # from .launcher import run  →  run()만 외부 노출
├── launcher.py        # run(reload_module=False): DEV면 reload 후 build__() 호출
├── config.py          # DEV_MODE 등 설정 (드롭 파일 아님)
├── <tool>_vNN.py      # 본체. class ...UI__ + build() + build__() (이름 유지 필수)
├── utility.py
└── __dragDrop_<번호>.py / __maya_button.py   # 드롭 설치 파일 (이름은 툴마다 고유, 아래 주의 참고)
```

- UI 본체는 `class` → `build()`로 `cmds.window` 구성, 끝에 진입점 `build__()`.
  **`build__` 함수명은 바꾸지 말 것** (launcher가 호출).
- 버튼은 `JUN_button__.ButtonSpec(...)` 스펙 → `JUN_button__.Buttons(spec).build()` 패턴.
- 색상은 `MOD_colorThem.ColorThemeRegistry.get("coral_01")`에서 가져온다.
- `__dragDrop_<번호>.py`(예: `__dragDrop_A00060.py`)를 Maya 뷰포트로 드래그&드롭하면 셸프 버튼이
  설치되고, 셸프 명령은 `tools.A000XX_name.run(True)`를 호출한다.

> **드래그&드롭 설치 파일 이름 규칙 (중요)**: Maya 는 드롭된 `.py` 를 **파일명(베이스네임)으로 import**
> 한다(`executeDroppedPythonFile` → `importlib.import_module(basename)`). 따라서 모든 툴의 드롭 파일이
> `config.py` / `__dragDrop.py` 처럼 **같은 이름**이면 `sys.modules` 에 첫 번째만 캐시되어, 이후 다른 툴을
> 드롭해도 **이전 툴이 설치되거나(캐시된 모듈 재실행) 설치가 안 된다**(전역 `config` 와도 충돌). 그래서 드롭
> 파일은 **툴마다 고유한 `__dragDrop_<번호>.py`**(예: `__dragDrop_A00190.py`)로 두고,
> `onMayaDroppedPythonFile` 끝에서 `sys.modules.pop(__name__, None)` 로 자기 자신을 캐시에서 제거한다.
> in-Maya 로 동작하는 (B) 툴(A00110+)도 동일한 `__dragDrop_<번호>.py` 드롭 파일을 둔다.

### (B) Standalone / Qt 앱 툴 — PySide
예: `A00004_base_QT`(템플릿), `A00008_base_QT_maya`(Maya 내 PySide 템플릿),
`A00080_KWI_creator_V02`, `A00090_ConnectionBuilder`, `A00100_jsonEditor_MH`

```
A000XX_name/
├── launch.py              # run(): MainWindow 생성 → ThemeManager로 qss → show()
├── app/
│   ├── config/version.py  # VERSION, LAST_UPDATE
│   ├── core/              # 비즈니스 로직 (UI와 분리)
│   └── ui/main_window.py  # QWidget 서브클래스
├── launch.spec / build_exe.bat   # PyInstaller exe 빌드
└── requirements.txt
```

- UI(`app/ui`)와 로직(`app/core`)을 분리한다. core는 가능한 한 DCC 비의존으로 둔다.
- 테마는 `ThemeManager.load_theme_to_widget(window, "red")` (qss).
- PySide 버전이 툴마다 섞여 있다(`A00080`=**PySide6**, `A00090`=**PySide2**). 수정 시 해당 툴의 import를 확인하고 맞출 것.

---

## 4. 주요 툴 도메인

| 툴 | 도메인 | 핵심 동작 |
|----|--------|-----------|
| `A00020_move_skineWeightTool` | 리깅 | 스킨 웨이트 이동 |
| `A00050_uvTool` / `A00060_jointTool` | 모델링/리깅 | UV · 조인트 작업 |
| `A00070/A00080_KWI_creator` | UE 물리 | **KawaiiPhysics(KWI)** AnimGraph 노드 텍스트 생성기 (5장) |
| `A00090_ConnectionBuilder` | **페이셜** | MetaHuman RBF 솔버→드라이버→블렌드셰이프 어트리뷰트 연결 (6장) |
| `A00100_jsonEditor_MH` | 페이셜 | MetaHuman용 json 정렬/편집 |

### 5. KWI Creator (`A00080_KWI_creator_V02`) — 템플릿 기반 텍스트 생성

Unreal **KawaiiPhysics** 노드를 클립보드 텍스트로 대량 생성한다. Maya가 아니라 텍스트 처리 툴이다.

- **흐름**: `app/core/0010_src/`의 소스 템플릿(`A0001_Src_KWI_node_v03.py` 등)을 읽어
  `{{KEY}}` 플레이스홀더를 치환 → `0020_out/`에 결과를 쓴다.
- `TemplateEngine.apply(text, replacements)` = `{{KEY}}` → 값 단순 치환.
- `PathManager(__file__, read_dir="0010_src", write_dir="0020_out")`로 경로 관리,
  `tgtBones`(타겟 본 목록)을 읽어 본 개수만큼 노드를 생성(`multiple`/`single` 모드).
- 치환 키 예: `NODE_NAME`, `ROOT_BONE`, `LINKED_TO`, `NODE_POS_X/Y`.

### 6. Connection Builder (`A00090_ConnectionBuilder`) — MetaHuman 페이셜 연결

`app/rules/<version>/*.json`의 규칙대로 어트리뷰트를 연결한다.

- 규칙 JSON: `solver_node`, `driver_node`, `blendshape_node`, `mapping`(어트리뷰트 이름 배열).
- 규칙은 **버전 폴더**(`rules/v001`, `v002` …)로 나눠 두고 UI 의 `Version` 콤보에서 고른다.
  `RuleLoader.find_versions()/set_version()` 이 버전을, `load_all(version)`이 그 폴더의 모든 json을
  `ConnectionRule`로 로드.
- `ConnectionManager`: 솔버 `outputs[idx]` → 드라이버 `.attr` → 블렌드셰이프 `.attr` 순으로
  `cmds.connectAttr`. `connect` / `disconnect` / `validate` 제공.

---

## 7. 컨벤션 · 관례

- **번호 접두사**로 순서를 강제: 툴은 `A000XX_`, 소스 파일은 `A00NN_`, src/out 폴더는 `0010_`/`0020_`.
- **버전은 파일명/폴더명에 박는다**: `*_V01_02.py`, `*_v03.py`, `_creator_V02`. 새 버전은 보통 새 파일을 만들고 기존 파일은 남겨둔다.
- `0010_src`(읽기) → `0020_out`(쓰기) 컨벤션. **`0020_out/`는 `.gitignore` 대상**(생성물).
- `DEV_MODE = True`(`config.py`)일 때 reloader가 동작. 배포 전 의식할 것.
- 주석·문자열에 한국어가 흔하다. 파일은 `# -*- coding: utf-8 -*-` / `encoding="utf-8"`로 처리.
- 파일 헤더 관례: `# Python Script by Ji Hun Park` + `# last Update date :` + 버전 이력.
- Qt 앱은 `CHANGELOG.md` + `app/config/version.py`로 버전 기록.
- `.gitignore`: `**/0020_out/`, `__pycache__/`, `*.pyc`, `**/JUN_memo/`.

## 8. 실행 / 빌드

- **Maya 툴 설치**: 해당 툴의 `__dragDrop_<번호>.py`를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 생성.
  이후 셸프 버튼 또는 `tools.A000XX_name.run(True)`로 실행(`True`면 reload).
- **Qt 앱 실행**: 툴 폴더의 `launch.py`의 `run()` 호출.
- **exe 빌드**: 툴 폴더의 `build_exe.bat`(PyInstaller, `launch.spec`).
- **릴리스 패키징**: `JUN_All/dev/build_release.py` — `TOOL_PATH`를 지정하면 해당 툴 + `Framework`를
  릴리스 디렉터리로 복사(`dev`, `__pycache__`, `.git` 제외). 경로 상수는 로컬 환경에 맞춰 수정 필요.

## 9. 작업 시 주의

- **새 코드는 `JUN_All/`에.** 레거시·학습 코드는 모두 `_archive/`(동결, read-only)로 아카이빙됨 — 참고용으로만 연다.
- Maya/Unreal/페이셜 로직 작업 시 **`app/core`(로직)와 `app/ui`(화면)를 섞지 말 것** — Qt 툴의 기존 분리를 유지.
- 새 maya.cmds 툴은 `A00000_base`를, 새 Qt 툴은 `A00004_base_QT`(또는 Maya 연동은 `A00008_base_QT_maya`)를 복제해서 시작.
- `build__` 등 launcher가 호출하는 진입점 함수명은 변경 금지.
- PySide2/PySide6 혼재 — 수정 대상 툴의 실제 import를 확인하고 맞출 것.
```
