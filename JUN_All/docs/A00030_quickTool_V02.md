---
title: A00030_quickTool_V02 사용법
aliases: [Quick Tool V02, QuickToolV2, 퀵툴 V02]
tags: [maya-python, tool-guide, quicktool, pyside, qt]
updated: 2026-09-17
---

# A00030_quickTool_V02 — Quick Tool (PySide 재작성)

레거시 **maya.cmds** 툴 [`A00030_quickTool`](A00030_quickTool.md)(V01.16) 을 **PySide(Qt)** 로
다시 쓴 버전이다. **버튼도 동작도 그대로**고 달라진 것은 그릇이다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`slate_dark` 테마)
- **버전**: `app/config/version.py` (v02.03)
- **설치**: `__dragDrop_A00030_V02.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **QuickToolV2**
  → `tools.A00030_quickTool_V02.run(True)`
- **V01 과 동시에 띄울 수 있다** — 창과 로그 확장창의 `objectName` 이 갈렸다.

> `File` · `Import option` 버튼은 [`A00480_FileTool`](A00480_FileTool.md) 의 `Path` · `Import` 탭에도 있다
> (2026-09-17~). 이 툴의 버튼은 그대로 둔다.

---

## 1. V01 에서 무엇이 달라졌나

| | V01 (maya.cmds) | **V02 (PySide)** |
|---|---|---|
| 결과 표시 | `print` / `cmds.warning` → **스크립트 에디터** | **창 안 공용 로그창**(`Expand` / `Clear` / `Copy`) |
| 로직 위치 | UI 파일 하나에 콜백까지 | **`app/core/quick_ops.py`** 로 분리(UI 비의존) |
| Pin (항상 위) | 창을 Qt 위젯으로 **감싸서** 플래그 조작 | 창이 Qt 라 **바로** 토글 |
| 버튼 추가 | 인덱스 상수 + 중첩 리스트를 짝맞춤 | **`MainWindow.SECTIONS` 표에 한 줄** |
| 색 | 코드에 RGB 를 박아 둠 | 공용 **테마 qss** |
| FBX 버튼 | 플러그인이 없으면 **트레이스백** | 플러그인을 올려 보고, 안 되면 **로그로 이유** |

**V01 의 기능은 하나도 빠지지 않았다** — 섹션 6개, 버튼 10개 그대로다.
새로 붙은 것은 레거시에 없던 **`Shelf > Update Shelves`**(v02.01)와 **`File > Open Scene Folder`**(v02.03) 두 개다.

---

## 2. 화면 구성

```
┌ Quick Tool v02.03 ──────────────────┐
│ Help                        [ Pin ] │   ← 메뉴 + 항상 위 토글
│ ┌ Update window ────────────────┐   │
│ │ [ Selected ] [ All Windows ]  │   │
│ ├ Print ────────────────────────┤   │
│ │ [ Print Selected ] [ Print H… ]│  │
│ ├ Import option ────────────────┤   │
│ │ [ Import FBX normal ]         │   │   ← 버튼 하나면 가로를 다 쓴다
│ ├ Create ──────────────────────┤    │
│ │ [ Create texture file ] [ Cl… ]│  │
│ ├ File ────────────────────────┤    │
│ │ [ Copy Scene F… ] [ Open Sce… ]│  │
│ ├ Shelf ──────────────────────┤    │
│ │ [ Update Shelves ]            │   │
│ ├ Display ─────────────────────┤    │
│ │ [ Local Axis ON ] [ Local A… ]│   │
│ └───────────────────────────────┘   │
│ ┌ Log ──────────────[Expand][Clear][Copy]┐
│ └─────────────────────────────────────┘ │
│   Copyright (c) Park Ji Hun. ...        │
└─────────────────────────────────────────┘
```

버튼은 레거시의 `paneLayout(configuration="vertical2")` 와 같이 **두 칸 그리드**로 놓인다.
버튼이 하나뿐인 섹션은 그 칸이 가로를 다 쓴다.

---

## 3. 버튼

### Update window — `Selected` / `All Windows`

재생 중 갱신할 뷰포트를 정한다(`playbackOptions -view`). **`Selected`** 는 활성 뷰만 갱신해
무거운 씬에서 재생이 눈에 띄게 빨라진다. `All Windows` 가 마야 기본이다.

### Print — `Print Selected` / `Print Hierarchy`

- **`Print Selected`** — 현재 선택의 이름을 로그에 적는다.
- **`Print Hierarchy`** — 선택과 그 아래 자식들의 **부모 관계를 트리로** 그린다. 씬은 안 건드린다.

```
qt_j1
└── qt_j2
    └── qt_j3
```

> 선택이 **이미 다른 선택의 자손**이면 건너뛴다 — 계층을 통째로 고르면 같은 트리가 몇 번이고
> 다시 찍히기 때문이다. 몇 개를 건너뛰었는지 로그에 적는다.

> 트리를 만드는 코드는 **재귀를 쓰지 않는다.** 조인트 체인은 수백 단계로 깊어질 수 있는데
> 재귀로 짜면 파이썬 재귀 한계(기본 1000, 마야 콜백 스택 위라 여유가 더 적다)에 걸린다.
> 명시적 스택으로 훑는다.

### Import option — `Import FBX normal`

FBX 임포트가 **파일에 저장된 노멀을 그대로** 쓰게 한다(`OverrideNormalsLock`).
**다음 임포트부터 적용되는 전역 FBX 설정**이라 지금 씬은 바뀌지 않는다.

> `FBXProperty` 는 MEL 기본 명령이 아니라 **`fbxmaya` 플러그인이 등록하는 프로시저**다.
> 플러그인이 안 올라와 있으면 V01 은 `Cannot find procedure "FBXProperty"` 로 죽었다.
> V02 는 **플러그인을 먼저 올려 보고**, 그래도 안 되면 로그에 이유를 적는다.

### Create — `Create texture file` / `Cluster Each`

- **`Create texture file`** — `file` 노드와 `place2dTexture` 를 만들어 **제대로 연결**한다.
  하이퍼셰이드에서 만들면 딸려 오지만 `shadingNode` 만 부르면 연결이 안 된 채 생긴다.
  UV 관련 어트리뷰트 16개 + `outUV` + `outUvFilterSize` 를 이어 준다.
- **`Cluster Each`** — 선택한 오브젝트마다 클러스터를 **하나씩** 만든다.
  `cmds.cluster` 는 선택 전체에 **하나**를 만들기 때문에 오브젝트마다 따로 선택해 호출한다.
  여러 개여도 **Ctrl+Z 한 번**으로 되돌아간다.

### File — `Copy Scene Folder` / `Open Scene Folder`

**`Copy Scene Folder`** — 현재 씬이 저장된 **폴더** 경로를 클립보드에 넣는다(파일 이름은 뺀다). 경로는 OS 네이티브 모양
(윈도우는 `\`)으로 바꿔 탐색기·파일 다이얼로그에 그대로 붙여넣을 수 있다.
저장하지 않은 씬이면 경고만 남긴다.

> `A00040_file_exporter_V02` 의 **`Paste`** 버튼과 짝이다 — 여기서 복사해 거기에 붙여넣는다.

**`Open Scene Folder`** (v02.03~) — 현재 씬이 저장된 폴더를 **탐색기로 연다.**
씬 파일이 디스크에 있으면 그 파일을 **선택(하이라이트)한 채로** 연다.

- 씬 파일이 지워졌거나 이름이 바뀌어 없으면 **폴더만** 연다.
- 저장하지 않은 씬이거나 폴더 자체가 없으면(드라이브 분리 등) 탐색기를 띄우지 않고 **경고만** 남긴다.
- 여는 일은 공용 `Framework.core.file_opener.open_path` 에 맡긴다(`A00210` · `A00220` 과 같은 구현).

### Shelf — `Update Shelves` (v02.01~, 레거시에 없던 것)

**지금 셸프 상태를 `prefs/shelves` 에 즉시 쓴다.**

> **왜 필요한가** — 마야는 셸프를 **종료할 때** 저장한다. 그래서 셸프를 고쳐 놓고(툴의
> `__dragDrop_*.py` 를 떨어뜨려 버튼이 생긴 것도 포함) **그 마야를 켠 채 다른 마야를 새로 띄우면**,
> 새 마야는 디스크에 남아 있는 **옛 파일**을 읽어 바뀐 것이 하나도 안 보인다. 고친 마야를 껐다
> 켜야 반영됐다. 이 버튼을 누르면 그 저장을 **지금** 해 버리므로, **이후에 뜨는 마야는 바뀐 셸프를
> 그대로 읽는다.**

로그에 **몇 개 중 몇 개가 실제로 쓰였는지**와 폴더 경로가 남는다.

```
Saved 12 of 12 shelf file(s) to C:/Users/USER/Documents/maya/2024/prefs/shelves/
A Maya started from now on will see these shelves (no need to close this one first).
```

**주의 — 이미 떠 있는 다른 마야는 갱신되지 않는다.** 그 마야는 자기 메모리의 셸프를 들고 있고,
**종료할 때 자기 상태로 파일을 덮어쓴다.** 즉 **마지막에 종료하는 마야가 이긴다.** 여러 마야를
띄워 쓸 때는 셸프를 고친 쪽에서 이 버튼을 누르고, **다른 마야는 셸프를 건드리지 않은 채 끄는** 것이
안전하다.

> **구현 메모** — `saveAllShelves($gShelfTopLevel)` 를 부른다. 그런데 **`saveAllShelves("")` 는
> 빈 인자에도 조용히 성공한다**(mayapy 실측). 그대로 부르면 아무것도 안 쓰고 "됐다" 고 말하게 되므로,
> ① UI 가 있는지(`$gShelfTopLevel` + 탭 레이아웃)를 먼저 보고 ② 저장 **전후의 파일 수정 시각을
> 비교해** 실제로 쓰였는지 확인한다. 하나도 안 바뀌었으면 성공이라고 하지 않고 경고한다.

### Display — `Local Axis ON` / `Local Axis OFF`

선택한 오브젝트의 로컬 회전축 표시를 **한 번에** 켜고 끈다. 현재 상태를 먼저 보고 **목표와 다른
것만** 바꾸므로, 선택이 섞여 있어도(일부만 켜져 있어도) 전부 같은 상태로 맞춰진다.

- **컴포넌트를 골라도 된다** — shape 에는 `displayLocalAxis` 가 없으므로 **부모 transform** 으로
  올라간다.
- **`toggle -localAxis` 대신 `setAttr` 을 쓴다.** MEL `toggle` 은 undo 큐에 아무것도 남기지 않아
  (빈 청크) 실행 후 Ctrl+Z 를 누르면 로컬 축이 아니라 **그 이전 작업**이 취소된다.
- 잠기거나 연결된 어트리뷰트는 바꿀 수 없으므로 따로 모아 경고한다.

### Pin (always on top)

창을 다른 마야 창 위에 고정한다. 켜면 라벨이 **`Pinned`** 가 된다.

---

## 4. 구조

```
A00030_quickTool_V02/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(reload): MainWindow → 테마(slate_dark) → show
├── __dragDrop_A00030_V02.py    # 셸프 설치 (TOOL_LABEL = "QuickToolV2")
├── icon/                       # A00030_quickTool_V02.svg / .png
└── app/
    ├── config/version.py       # VERSION = "02.03"
    ├── core/quick_ops.py       # ★ 버튼이 하는 일 전부 (maya.cmds/mel, UI 비의존)
    └── ui/main_window.py       # 창 · 섹션 · 버튼 · 로그
```

- **코어는 로그 문자열 리스트를 돌려준다.** `print` / `cmds.warning` 을 쓰지 않으므로
  UI 가 그대로 로그창에 쌓고, 마야 없이도 함수 단위로 테스트할 수 있다.
- **버튼 표는 `MainWindow.SECTIONS`** — `(섹션 제목, [(라벨, 핸들러 이름, 툴팁), ...])`.
  버튼을 더하거나 옮기는 일은 이 표 한 줄이다.

---

## 5. 검증 (mayapy 2024 + 오프스크린 Qt)

**22 + 12 + 8항목 통과.**

- 섹션 7개와 버튼 11개(레거시 10 + `Update Shelves`)가 **레거시와 같은 순서**,
  전 버튼에 툴팁, Pin 토글과 로그창 존재
- `Selected` / `All Windows` 가 `playbackOptions -view` 를 실제로 바꾼다
- `Print Selected` — 선택 없으면 경고, 있으면 이름 로그
- `Print Hierarchy` — 조인트 3단 트리를 그리고, 이미 다른 트리 안이면 건너뛴다
- `Import FBX normal` — 플러그인을 올려 설정하고, **트레이스백이 로그로 새지 않는다**
- `Create texture file` — `file` 1개 생성 + `place2dTexture` 가 `uv` · `coverage` 에 연결됨
- `Cluster Each` — 선택 2개면 **클러스터 2개**(하나가 아니라), 선택 없으면 경고
- `Copy Scene Folder` — 미저장 씬이면 경고
- `Open Scene Folder`(8항목, 탐색기 호출은 가로채서 확인) — 미저장 씬은 **경고만, 탐색기 안 띄움** ·
  저장된 씬은 **씬 파일 경로**로 연다(선택 상태) · 파일이 지워지면 **폴더**로 연다 · 폴더가 없으면 경고 ·
  탐색기 호출이 실패해도 트레이스백 없이 경고 · File 섹션 버튼 2개 · 클릭하면 로그에 결과
- `Local Axis ON/OFF` — 실제 `displayLocalAxis` 값이 바뀌고, **컴포넌트를 골라도 부모 transform**
  으로 올라간다. 선택 없으면 경고
- `Pin` — 켜면 `Pinned` + `WindowStaysOnTopHint`, 끄면 원복
- `Update Shelves`(12항목) — UI 가 없으면 **트레이스백 없이 경고만** · 파일이 하나도
  안 바뀌면 **성공이라고 하지 않음** · 쓰인 개수를 정확히 보고 · 일부만 쓰이면 어느 것이
  안 쓰였는지 · MEL 실패는 경고 한 줄로
- `run()` 진입점이 창을 띄우고, 다시 불러도 **보이는 창은 하나**

> 실제 Maya GUI 육안 확인은 아직이다.
