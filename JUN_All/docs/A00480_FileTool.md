---
title: A00480_FileTool 사용법
aliases: [File Tool, FileTool, A00480]
tags: [maya-python, tool-guide, file, fbx, export, import, path, pyside]
updated: 2026-09-17
---

# A00480_FileTool 사용법

Maya 안에서 도는 **파일 입출력 · 경로** PySide 툴이다(arch B, in-Maya).
흩어져 있던 두 툴의 기능을 한 창의 탭으로 모았다.

| 탭 | 내용 | 출처 |
|----|------|------|
| **Export** | objectSet 마다 FBX 한 파일로 일괄 익스포트 (Export Path · Set Up · Naming · Type Filter · Joints only) | [`A00040_file_exporter_V02`](A00040_file_exporter_V02.md) 화면 전체 |
| **Import** | `Import FBX normal` — FBX 임포트가 파일의 노멀을 그대로 쓰게 | [`A00030_quickTool_V02`](A00030_quickTool_V02.md) `Import option` |
| **Path** | `Copy Scene Folder` · `Open Scene Folder` | [`A00030_quickTool_V02`](A00030_quickTool_V02.md) `File` |

- **버전**: `app/config/version.py` (v01.02 — Pin 글자 잘림 수정)
- **설치**: `__dragDrop_A00480.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **FileTool** → `tools.A00480_FileTool.run(True)`
- **테마**: `slate_dark`
- **원본 두 툴은 그대로 남아 있다.** quickTool 의 File · Import option 버튼도 지워지지 않았다.
  창 이름(objectName)이 달라 **셋을 동시에 띄워도 서로 닫지 않는다.**

> 이름이 비슷한 [`A00210_FileManager`](A00210_FileManager.md) 는 **마야 밖**에서 도는 씬 파일 버전·작업 기록 추적 앱이고,
> [`A00240_PathTool`](A00240_PathTool.md) 은 자주 쓰는 폴더를 버튼으로 여는 standalone 런처다. 이 툴은 **마야 안의 입출력**이다.

---

## 1. 화면

```
┌ File Tool v01.02 ───────────────────────────── [ Pin ] ┐
│ Help                                                    │
│ ┌ Export ┬ Import ┬ Path ┐                              │
│ │ Export Path [.................] [Browse][Paste][Scene]│
│ │ Set Up      [Set's Name]   [File name]                │
│ │ Naming      SK MANU CH Name Type Version  [Set Name]  │
│ │ Export      □ Move to scene root □ Joints only ...    │
│ │             Type Filter : [Include Types ▾] [Export]  │
│ └───────────────────────────────────────────────────────┘
│ Log ─────────────────────────────── [Expand][Clear][Copy]
│   Copyright (c) Park Ji Hun. All rights reserved.        │
└──────────────────────────────────────────────────────────┘
```

- **로그창은 세 탭이 함께 쓴다.** 어느 탭에서 누른 결과든 같은 곳에 쌓인다.
- **창 크기는 원본 `A00040_file_exporter_V02` 와 같다**(slate_dark 기준 960 x 853, v01.01~). 폭은 Naming 토큰 6칸 줄이 정한다.
  - 테마 qss 는 `show()` 뒤에야 자식 위젯에 입혀지므로, 그 전에 재면 글자가 큰 상태의 최소 크기(약 1290 폭)로 창이 커진다.
    `launch.py` 가 show 다음 이벤트 루프에서 `fit_to_content()` 로 레이아웃 최소 크기에 맞춘다.
  - 탭 테두리만큼 늘어나는 것은 Export 페이지 여백 0 · 창 좌우 여백 -2 · Pin 높이 22 로 상쇄했다.
  - Pin 버튼은 22px 높이라 테마의 `padding: 8px` 이면 글자 자리가 4px 뿐이다 → 이 버튼만 위아래 padding 0(v01.02).

---

## 2. Export 탭

**원본 `A00040_file_exporter_V02` v02.09 와 동작이 같다** — 같은 씬 · 같은 옵션이면 같은 FBX 가 나온다
(§6 검증). 사용법 전체는 원본 문서를 그대로 따른다:

- 흐름 · Naming 토큰 → [A00040 §5](A00040_file_exporter_V02.md#5-사용-흐름)
- Type Filter · Joints only under joints → [A00040 §6](A00040_file_exporter_V02.md#6-내보낼-대상-고르기-type-filter--joints-only)
- Move to scene root → [A00040 §7](A00040_file_exporter_V02.md#7-내보내기-동작-move-to-scene-root--keep-hierarchy)
- Paste 가 받아 주는 경로 모양 → [A00040 §4-1](A00040_file_exporter_V02.md#4-1-paste--클립보드의-경로-꽂기-v0208)

### 2-1. `Scene` 버튼 (신규)

**현재 씬이 저장된 폴더를 Export Path 에 바로 채운다.**

따로일 때는 quickTool 의 `Copy Scene Folder` 로 복사하고, 창을 바꿔 A00040 의 `Paste` 로 붙여야 했다.
씬 옆에 FBX 를 뽑는 일이 잦아 한 번에 되게 했다.

| 상황 | 결과 |
|------|------|
| 저장된 씬 | 폴더를 `/` 모양으로 채우고 `Export path : ...` 로그 |
| 저장 안 한 씬 | **기존 경로를 건드리지 않고** `[WARN] Current scene has not been saved yet (no scene folder).` |

### 2-2. 원본과 달라진 것 (동작 아님)

| | A00040_V02 | FileTool |
|---|---|---|
| FBX 플러그인이 없을 때 | `cmds.file(typ="FBX export")` 가 트레이스백 | **익스포트 전에** 플러그인을 올려 보고, 안 되면 `[FAIL] Cannot export FBX without the plugin.` |
| undo | 파일 안의 자체 `undo_chunk` 복제 | 공용 `Framework.core.maya_undo.undo_chunk` |
| Paste 경로 정규화 | UI 핸들러 안 | `core.normalize_pasted_path` (마야 없이 검증 가능, 결과 동일) |

---

## 3. Import 탭

### `Import FBX normal`

FBX 임포트가 **파일에 저장된 노멀을 그대로** 쓰게 한다(`OverrideNormalsLock` = 1).
**다음 임포트부터 적용되는 전역 FBX 설정**이라 지금 씬은 바뀌지 않는다.

- `FBXProperty` 는 `fbxmaya` 플러그인이 등록하는 프로시저라, **플러그인을 먼저 올려 보고** 안 되면 로그에 이유를 남긴다.
- 로그: `FBX import : OverrideNormalsLock ON (applies to the next import).`

---

## 4. Path 탭

### `Copy Scene Folder`

현재 씬 폴더를 클립보드에 넣는다. 경로는 **OS 네이티브 모양**(윈도우는 `\`)이라 탐색기 주소창 ·
파일 다이얼로그에 그대로 붙여넣을 수 있다. 저장 안 한 씬이면 경고만 남기고 클립보드를 건드리지 않는다.

### `Open Scene Folder`

현재 씬 폴더를 **탐색기로 연다.** 씬 파일이 디스크에 있으면 **그 파일을 선택한 채로** 연다.

| 상황 | 결과 |
|------|------|
| 저장된 씬 · 파일 있음 | 폴더를 열고 씬 파일 선택 |
| 파일이 지워졌거나 이름이 바뀜 | 폴더만 연다 |
| 폴더가 없음(드라이브 분리 등) | 탐색기를 안 띄우고 `[WARN] Scene folder does not exist on disk` |
| 저장 안 한 씬 | 경고만 |
| 탐색기 호출 실패 | 트레이스백 없이 `[WARN] Could not open the folder` |

---

## 5. 구조

```
A00480_FileTool/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(reload): MainWindow → 테마(slate_dark) → show → (다음 루프) fit_to_content()
├── __dragDrop_A00480.py        # 셸프 설치 (TOOL_LABEL = "FileTool")
├── icon/                       # A00480_FileTool.svg / .png (폴더 + 들어오고 나가는 화살표)
├── CHANGELOG.md
└── app/
    ├── config/version.py       # VERSION = "01.02"
    ├── core/                   # UI 비의존 (결과는 로그 문자열 리스트)
    │   ├── fbx_plugin.py       # ensure_fbx_plugin() — Export · Import 공용
    │   ├── export_ops.py       # A00040_V02 export_ops 이식 (타입 필터 · 파일명 · FBX export)
    │   ├── import_ops.py       # import_fbx_normal
    │   └── path_ops.py         # scene_folder · open_scene_folder · normalize_pasted_path
    └── ui/
        ├── main_window.py      # 메뉴 · Pin · QTabWidget · 공용 로그 · 푸터
        ├── export_tab.py       # A00040_V02 화면 + Scene 버튼
        ├── import_tab.py       # SECTIONS 표
        ├── path_tab.py         # SECTIONS 표
        ├── button_section.py   # SECTIONS 표 → 두 칸 버튼 그리드 (quickTool 방식)
        └── type_filter_button.py
```

### 기능 더하기

- **Import · Path 탭에 버튼** — 탭 클래스의 `SECTIONS` 에 `(라벨, 핸들러 이름, 툴팁)` 한 줄 + 핸들러 메서드.
  로직은 `app/core/*_ops.py` 에 두고 **로그 문자열 리스트**를 돌려준다.
- **섹션이 3~4개를 넘으면** 접이식으로 쌓지 말고 하위 탭으로 나눈다.
- **새 탭** — `app/ui/<name>_tab.py` 에 `QWidget(log=...)` 를 만들고 `main_window.build_ui` 에서 `addTab`.
- **Export 의 타입 필터 타입** — `export_ops.FILTER_TYPES` + `_TYPE_MATCHERS` 두 곳(원본과 같다).

---

## 6. 검증 (mayapy 2024 + 오프스크린 Qt)

**54항목 통과.** 창 크기는 원본과 나란히 띄워 **둘 다 960 x 853** 인 것을 확인(v01.01).

- **창** — `run()` 을 두 번 불러도 보이는 창은 하나 · 제목 · 탭 `Export / Import / Path` 순서, Export 가 기본 ·
  원본 두 툴과 objectName 이 다름 · 버튼 라벨과 툴팁 · Pin 켜기/끄기
- **Paste 정규화** — 역슬래시 → `/` · 따옴표 벗기기 · 파일이면 폴더 · 여러 줄이면 첫 줄 · 비었으면 경고 ·
  없는 경로는 넣되 경고 · **빈 클립보드면 기존 값 유지**
- **Scene 버튼** — 미저장이면 경로 유지 + 경고 · 저장된 씬이면 `/` 모양 폴더
- **Path 탭** — Copy 미저장 시 클립보드 그대로 · 저장된 씬이면 네이티브 경로 · Open 은 (탐색기 호출을 가로채서)
  파일 선택 / 파일 없으면 폴더 / 폴더 없으면 경고 / 호출 실패 시 경고 · 미저장이면 탐색기 안 띄움
- **Import 탭** — `OverrideNormalsLock` 이 실제로 1 · 플러그인이 없으면 `[WARN]` 만
- **Export = 원본** — 조인트 체인 밑에 메시·로케이터, 그룹 안 메시·커브, **같은 이름 노드**가 있는 씬에서
  옵션 4조합(Move to root / Keep hierarchy × Type Filter × Joints only)마다 원본 `A00040_V02` core 와 FileTool
  **탭 핸들러**로 각각 익스포트해서
  - 파일 이름 목록이 같다
  - **FBX 를 다시 임포트한 계층이 같다**
  - 결과 로그(`[OK]` · exported · excluded)가 같다
  - 익스포트 후 씬 계층이 전과 같고, **Ctrl+Z 한 번** 뒤에도 씬이 깨지지 않는다
- **플러그인 없는 Export** — `[FAIL]` 로그, 파일 안 생김, 트레이스백 없음

> 실제 Maya GUI 육안 확인은 아직이다.
