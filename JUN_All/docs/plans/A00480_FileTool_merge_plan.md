# A00480_FileTool — A00040_file_exporter_V02 + A00030_quickTool_V02(File · Import option) 병합 계획서

> 작성 2026-09-17 · 상태: **v01.00 구현 완료(2026-09-17, mayapy 54항목 통과 · 마야 GUI 확인 전)** · 아키텍처 (B) Maya 내 PySide 툴
>
> **사용자 결정(2026-09-17)** — 이름 `FileTool` · quickTool 버튼 **보존** · `A00040_file_exporter_V02` **보존** · 탭 `Export / Import / Path`.
> 구현 중 바뀐 점: 플러그인 헬퍼는 `import_ops` 가 아니라 별도 `core/fbx_plugin.py`, 탭 파일명은 `*_tab.py`,
> Import · Path 탭의 버튼 표는 공용 `ui/button_section.py`. 창 크기는 v01.01 에서 원본 A00040_V02 와 같은 960 x 853 으로 맞췄다(테마 polish 뒤 최소 크기로 fit).

## 0. 배경 · 목표

파일을 **들여오고(Import) · 내보내고(Export) · 경로를 다루는(Path)** 기능이 두 툴에 흩어져 있다.

| 소스 | 버전 | 가져올 것 |
|------|------|-----------|
| `A00040_file_exporter_V02` | v02.09 | **툴 전체** — 세트 단위 FBX 일괄 익스포트 (Path / Set Up / Naming / Export) |
| `A00030_quickTool_V02` | v02.03 | **`File`** 섹션(`Copy Scene Folder` · `Open Scene Folder`) + **`Import option`** 섹션(`Import FBX normal`) |

두 툴은 이미 짝으로 쓰이고 있다 — quickTool 가이드에 *"`Copy Scene Folder` 는 A00040 의 `Paste` 와 짝"*
이라고 적혀 있다. 한 창에서 복사하고 다른 창에 붙여넣는 흐름을 **한 툴 안의 흐름**으로 만드는 것이 이번 병합의 핵심이다.

**목표**: 새 경로 `JUN_All/tools/A00480_FileTool` 에 탭 구조 툴을 만든다.
- `A00040_file_exporter_V02` 는 **탭 하나(`Export`)** 로 옮긴다 — 기능·동작 동일.
- quickTool 의 버튼은 **`Path` · `Import` 탭**으로 옮긴다.
- 이후 파일 입출력·경로 기능은 **탭/하위 탭을 한 줄씩 더하는 식**으로 늘린다.
- 원본 두 툴은 **무수정 보존**한다(레퍼런스 · 롤백용).

---

## 1. 툴 이름

### 추천: **`A00480_FileTool`** (창 제목 `File Tool v01.00`, 셸프 라벨 `FileTool`)

| 이유 | 설명 |
|------|------|
| 최근 툴 명명 규칙과 같다 | `A00380_MeshTool` · `A00400_CurveTool` · `A00440_SetTool` · `A00470_MaterialTool` — **`<다루는 대상>Tool`**. 대상이 "파일" 이니 `FileTool` |
| 범위가 넓어도 맞는 이름 | Import · Export · Path 설정이 모두 "파일을 다루는 일"이다. 기능이 더 붙어도 이름이 틀려지지 않는다 |
| 기존 툴과 겹치지 않는다 | `A00210_FileManager`(standalone, 씬 파일 버전·기록 추적) · `A00240_PathTool`(standalone, 경로 버튼 런처)와 구분된다. **FileManager · PathTool 은 이미 쓰인 이름**이라 후보에서 뺐다 |
| 번호 | 현재 마지막 툴이 `A00470` → **`A00480`** |

### 다른 후보

| 이름 | 장점 | 단점 |
|------|------|------|
| `A00480_FileIO` | Import/Export 가 이름에 바로 드러난다 | 경로 설정·조작(Path 탭)이 이름에서 빠진다. 규칙(`*Tool`)에서 벗어난다 |
| `A00480_SceneIO` | "마야 씬 안↔밖" 이라는 성격이 정확 | 씬 폴더·외부 경로 조작까지 담기엔 좁다 |
| `A00480_FileHub` | 여러 파일 기능을 모은다는 뉘앙스 | 기존 툴에 없는 어휘라 목록에서 성격이 덜 읽힌다 |

> `A00210_FileManager` 와 이름이 "File" 로 시작해 헷갈릴 수 있다. 가이드 문서 첫 줄에
> **"마야 안에서 도는 입출력 툴 — 씬 파일 버전 추적은 A00210"** 을 적어 구분한다.

---

## 2. 탭 구성

```
┌ File Tool v01.00 ─────────────────────────── [ Pin ] ┐
│ File  Help                                            │
│ ┌ Export ┬ Import ┬ Path ┐                            │
│ │  (A00040_file_exporter_V02 화면 그대로)           │ │
│ │  Export Path [..........] [Browse][Paste][Scene]  │ │  ← Scene: 씬 폴더 채우기 (신규 연결점)
│ │  Set Up / Naming / Export                          │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌ Log ───────────────────────── [Expand][Clear][Copy] ┐ │   ← 탭 공유 로그
│ └──────────────────────────────────────────────────────┘ │
│   Copyright (c) Park Ji Hun. All rights reserved.       │
└─────────────────────────────────────────────────────────┘
```

| 탭 | 내용 (v01.00) | 출처 | 이후 확장 후보 |
|----|---------------|------|----------------|
| **Export** | Set 단위 FBX 일괄 익스포트 전체 (Export Path · Set Up · Naming · Type Filter · Joints only · Move to scene root) | A00040_V02 | OBJ/Alembic 익스포트, 선택 단위 익스포트, FBX 옵션 프리셋 |
| **Import** | `Import FBX normal` (OverrideNormalsLock) | quickTool `Import option` | FBX 임포트 옵션 프리셋, 폴더 일괄 임포트, 네임스페이스 지정 임포트 |
| **Path** | `Copy Scene Folder` · `Open Scene Folder` | quickTool `File` | 최근 경로 목록, workspace(project) 설정, 경로 변환(`\`↔`/`), 레퍼런스/텍스처 경로 재지정 |

- 탭 순서는 **사용 빈도**(Export 가 주력)로 둔다. `Export` 가 기본 탭.
- 한 탭의 섹션이 3~4개를 넘으면 접이식이 아니라 **하위 탭**으로 나눈다(`<GROUP>_PAGES` + `_build_sub_tabs`, A00145 · A00110 방식).
  Import · Path 탭은 지금 버튼이 적으니 **하위 탭 없이** 시작하고, 기능이 늘면 그때 나눈다.
- **로그는 탭 공유**(`JUN_mod_log_qt_v01` 하나). 탭 생성보다 먼저 만든다 — A00040 의 TSL `log_callback` 이 로그를 참조한다.

### 2-1. 병합으로 새로 생기는 연결점 (v01.00 에 포함)

두 툴이 따로일 때는 못 하던 것 하나만 넣는다. 나머지는 확장 단계로 미룬다.

- **Export Path 옆 `Scene` 버튼** — 현재 씬 폴더를 Export Path 에 바로 채운다.
  지금은 quickTool 에서 `Copy Scene Folder` → A00040 에서 `Paste` 두 창을 오갔다.
  미저장 씬이면 경로를 건드리지 않고 `[WARN]` 만 남긴다(`Paste` 의 빈 클립보드 처리와 같은 규칙).

---

## 3. 폴더 구조

```
A00480_FileTool/
├── __init__.py                     # from .launch import run
├── launch.py                       # run(reload): 기존 창 정리 → MainWindow → 테마 → show
├── __dragDrop_A00480.py            # 셸프 설치 (TOOL_LABEL = "FileTool", 고유 드롭 이름 + sys.modules.pop)
├── icon/A00480_FileTool.svg / .png # 32px, 공통 배경 틀 (신규 툴 아이콘 규칙)
├── CHANGELOG.md
└── app/
    ├── config/version.py           # VERSION = "01.00"
    ├── core/
    │   ├── __init__.py             # export
    │   ├── export_ops.py           # ← A00040_V02 core 이식 (타입 필터 · 파일명 · FBX export)
    │   ├── import_ops.py           # ← quickTool import_fbx_normal (+ FBX 플러그인 로드 헬퍼)
    │   └── path_ops.py             # ← quickTool scene_folder / open_scene_folder
    │                               #   + A00040 UI 의 Paste 경로 정규화 로직을 코어로 내림
    └── ui/
        ├── main_window.py          # 창 · 메뉴 · QTabWidget · 공유 로그 · Pin · 푸터
        ├── tab_export.py           # ← A00040_V02 main_window 의 build_ui 부분
        ├── tab_import.py
        ├── tab_path.py
        └── type_filter_button.py   # ← A00040_V02 그대로
```

탭마다 파일을 나눈다. A00040 화면만 350줄이라 한 파일에 몰면 확장할 때 충돌 지점이 된다.
각 탭은 `QWidget` 서브클래스로 `log` 콜백을 받는다 — 탭이 창을 몰라도 되게.

---

## 4. 이식 시 정리할 것

**동작은 바꾸지 않는다.** 아래는 옮기는 김에 할 구조 정리뿐이다.

| 항목 | 지금 | 새 툴 |
|------|------|-------|
| undo | `export_ops.py` 에 자체 `class undo_chunk` 복제 | 공용 `Framework.core.maya_undo.undo_chunk` 사용 |
| FBX 플러그인 로드 | quickTool 은 로드 후 설정, exporter 는 로드 확인이 약함 | `import_ops` 의 로드 헬퍼를 **Export 도 같이** 쓴다 → 플러그인 없을 때 트레이스백 대신 로그 |
| Paste 경로 정규화 | A00040 **UI**(`on_paste_path`) 안에 따옴표·첫 줄·파일→폴더 처리 | `path_ops.normalize_pasted_path(text)` 로 코어에 → mayapy 로 단위 검증 가능, Path 탭 확장에서 재사용 |
| 클립보드 · 탐색기 | quickTool: 클립보드는 UI, 탐색기는 `Framework.core.file_opener.open_path` | 그대로 유지 (코어는 문자열, Qt 일은 UI) |
| 로그 | 두 툴 모두 `JUN_mod_log_qt_v01` | 하나로 공유 |
| 메뉴 | 두 툴 모두 `JUN_mod_menuBar_qt_v01` | 그대로, `Help > About` 유지 |
| Pin | quickTool 에만 있음 | 새 툴에도 둔다 |
| 테마 | A00040 `blue_dark`(재배정 계획상 `slate_dark`), quickTool `slate_dark` | **`slate_dark`** |
| import 경로 | `tools.A00040_file_exporter_V02.app...` | `tools.A00480_FileTool.app...` 로 전부 교체 (standalone 패키지 충돌 규칙) |
| 창 objectName | 툴별 | `JUN_A00480_FileTool_window` / 로그 `..._log_window` — 원본 툴과 **동시에 띄울 수 있게** |

---

## 5. 작업 순서

| 단계 | 내용 | 완료 기준 |
|------|------|-----------|
| **1. 뼈대** | 폴더 · `launch.py` · `__dragDrop_A00480.py` · `version.py` · 빈 3탭 `main_window.py` · 공유 로그 · Pin · 아이콘 | mayapy 오프스크린에서 창이 뜨고, `run()` 재호출 시 창이 하나 |
| **2. Export 탭** | A00040_V02 core/ui 이식, undo_chunk 공용화, FBX 플러그인 헬퍼 적용 | A00040_V02 의 기존 검증 항목(타입 필터 · Joints only · Move to scene root · 고유 파일명 · 레퍼런스 멤버)이 **같은 결과** |
| **3. Path 탭** | `Copy Scene Folder` · `Open Scene Folder` 이식, Paste 정규화 코어화 | quickTool 검증 항목(미저장 경고, 파일 선택 열기, 폴더 폴백, 탐색기 실패 경고) 통과 + 정규화 표(§A00040 4-1) 5케이스 통과 |
| **4. Import 탭** | `Import FBX normal` 이식 | 플러그인 로드 → 설정, 트레이스백이 로그로 새지 않음 |
| **5. 연결점** | Export Path `Scene` 버튼 | 저장된 씬이면 경로 채움, 미저장이면 경로 유지 + 경고 |
| **6. 문서 · 기록** | `docs/A00480_FileTool.md` 가이드, `CHANGELOG.md`, `WORKLOG.md`, portfolio EN/KR, 원본 두 가이드에 "A00480 으로 옮겨짐" 안내 한 줄 | 문서 목록 표에 등록 |
| **7. 마야 GUI 확인** | 실제 Maya 에서 드롭 설치 · 탭 전환 · Export 1회 | 사용자 육안 확인 |

각 단계를 **개별 커밋**으로 나눈다(단계 2 가 가장 크고 되돌릴 일이 생기면 거기서다).

---

## 6. 정해야 할 것 (사용자 결정)

| # | 질문 | 선택지 | 추천 |
|---|------|--------|------|
| 1 | 툴 이름 | `FileTool` / `FileIO` / `SceneIO` / 기타 | **`FileTool`** |
| 2 | quickTool 의 `File` · `Import option` 섹션은? | (a) 그대로 두고 중복 허용 (b) quickTool 에서 빼고 FileTool 로 안내 | **(a) 당분간 유지** — quickTool 은 자주 쓰는 버튼 모음이라 사용 습관을 깨지 않는다. FileTool 이 안정되면 (b) 를 따로 결정 |
| 3 | `A00040_file_exporter_V02` 는? | (a) 보존(동결) (b) 계속 개선 | **(a) 동결** — 이후 Export 개선은 FileTool 에만. 가이드 상단에 안내 |
| 4 | 탭 이름 | `Export / Import / Path` vs `FBX Export / Import / Scene Path` | **짧은 쪽** — 확장 후 FBX 외 포맷이 들어와도 맞는다 |

---

## 7. 위험 · 주의

- **Export 는 씬을 잠시 바꾼다**(`Move to scene root` 가 멤버를 월드로 뺐다 복원). 이식 중 `undo_chunk` 교체로
  **복원 경로가 undo 청크 밖으로 새지 않는지** 확인한다 — 단계 2 의 핵심 검증.
- `FBXExportIncludeChildren` / `FBXExportInputConnections` 는 **전역 FBX 옵션**이다. Import 탭이 같은 FBX 옵션
  체계를 만지므로, Export 의 `fbx_options` 컨텍스트가 **원래 값으로 되돌리는** 동작을 유지해야 한다.
- 드롭 파일은 반드시 **고유 이름 `__dragDrop_A00480.py`** — 같은 이름이면 캐시된 다른 툴이 설치된다.
- 원본 두 툴과 **objectName 이 겹치면** 한쪽 실행이 다른 쪽 창을 닫는다. 새 이름으로 분리.
- cmds UI 가 아니라 PySide 라 mayapy 오프스크린 검증이 가능하다. 창 크기는 **테마 qss 를 입힌 뒤** 잰다.
