---
title: Framework 공용 위젯 — MOD_menuBar_qt (툴 창 메뉴 바 + 공통 메뉴 항목)
aliases: [JUN_mod_menuBar_qt, 메뉴 바, 공용 메뉴, Copy Tool Name, Copy Tool Name + Tabs, tool_menu]
tags: [framework, qt, widget, maya-python, menu]
updated: 2026-10-29
---

# `JUN_mod_menuBar_qt_v01` — 모든 툴이 같은 공통 항목을 갖는 메뉴 바

| 파일 | 역할 |
|------|------|
| `JUN_All/Framework/core/tool_menu.py` | **공통 항목 레지스트리**(`COMMON_MENUS`) + 툴 이름 판정 + 공통 동작. maya / Qt 비의존 |
| `JUN_All/Framework/qt/MOD_menuBar_qt_v01.py` | PySide 툴용 — `QMenuBar` 대체 위젯 |
| `JUN_All/Framework/ui/MOD_menu_v01.py` | maya.cmds 툴용 — `cmds.menu` 안에 공통 항목을 붙이는 함수 |

툴 창 위의 메뉴(`Help` 등)에 **모든 툴이 똑같이 가져야 하는 항목**을 한 곳에서 관리한다.
두 UI 계열(PySide · maya.cmds)이 **같은 레지스트리**를 읽으므로, 항목을 하나 더하면 양쪽 툴에 다 생긴다.

## 지금 들어 있는 공통 항목

| 메뉴 | 항목 | 동작 |
|------|------|------|
| `Help` | **`Copy Tool Name`** | 툴 코드가 있는 **폴더 이름**을 클립보드로. 예: `A00060_jointTool_V03` |
| `Help` | **`Copy Tool Name + Tabs`** (2026-10-29) | 툴 폴더 이름 뒤에 **지금 보고 있는 탭 라벨**을 바깥 → 안쪽 순으로 ` / ` 로 이어 클립보드로. 예: A00110 의 Transfer 탭 안 Follow 탭을 보고 있으면 `A00110_animTool_V02 / Transfer / Follow`. 탭이 없는 창이면 툴 이름만 |

결과는 창 안의 공용 로그창([`JUN_mod_log_qt_v01`](Framework_MOD_log_qt.md))에 한 줄 남는다 —
`[Copy Tool Name] Copied to clipboard : A00060_jointTool_V03`,
`[Copy Tool Name + Tabs] Copied to clipboard : A00110_animTool_V02 / Transfer / Follow`
(탭이 없으면 뒤에 `(no visible tabs)`). 로그창이 없는 창(maya.cmds 툴 포함)은 Script Editor 에 `print`.

### "지금 보고 있는 탭" 을 세는 법

메뉴 바는 탭보다 먼저 만들어지므로 **누를 때** 센다(`MenuContext.tab_path` 에 함수를 넘겨 두고, 콜백이 읽을 때 호출).

- **PySide** — `MOD_menuBar_qt_v01.visible_tab_path(window)`. 창 안의 모든 `QTabWidget` 중 **보이는 사슬**만 고른다:
  조상 탭 위젯마다 그 `currentWidget()` 안에 들어 있어야 하고(다른 탭 페이지 속 탭 위젯은 제외),
  `isVisibleTo(window)` 가 False 인 것(접힌 그룹 · Shrink 로 숨긴 영역)도 제외. 라벨은 `tabText` 에서 `&` 를 뗀 것.
  `QScrollArea` 안에 든 탭(A00110 처럼)도 조상 사슬로 찾으므로 문제없다. 같은 페이지에 탭 위젯이 둘 보이면
  사슬 단위로 묶어 둘 다 적는다(`바깥 / 안쪽1 / 안쪽1의 안쪽 / 안쪽2`). `menu_bar.tab_path()` 로 툴 코드에서도 읽을 수 있다.
- **maya.cmds** — `MOD_menu_v01.visible_tab_path(window)`. `lsUI -controlLayouts -long` 에서 그 창 아래 `tabLayout` 만 골라,
  바깥 `tabLayout` 의 `selectTab` 자식 안에 든 것만 사슬로 인정하고 `visible` 이 꺼진 것은 뺀다. 라벨은 `tabLabel[selectTabIndex-1]`.
  창 이름은 `add_common_items` 가 만든 `menuItem` 의 전체 경로(`window|menuBarLayout|menu|menuItem`) 첫 마디에서
  알아내므로 **툴 쪽 호출은 그대로**(`add_common_items('Help', tool_file=__file__)`). 다르게 주려면 `window=`.
- 탭 라벨만 적는다 — 버튼으로 페이지를 바꾸는 `QStackedWidget`(A00370 카테고리 같은 것)은 라벨이 없어 세지 않는다.

## 사용처

- **PySide 툴 42곳 전부** — `tools/*/app/ui/main_window.py` 에서 `QMenuBar()` 를 쓰던 곳.
  `A00180_abSymMesh` 는 `Operations | Help` 두 메뉴.
- **메뉴 바를 새로 단 창** (2026-09-18) — `A00220_BackupTool` v01.16 · `A00240_PathTool` v01.10.
- **maya.cmds 툴 7곳** — `A00000_base` · `A00010_humanIKTool` · `A00020_move_skineWeightTool` ·
  `A00030_quickTool` · `A00040_file_exporter` · `A00050_uvTool` · `A00060_jointTool`.
- **메뉴 바가 없는 창은 대상이 아니다** — 템플릿 `A00004_base_QT` · `A00008_base_QT_maya`,
  `A00070` · `A00080_V02` · `A00090` · `A00100` · `A00130_ControlRig`(V01) · `A00200` · `A00210` ·
  `A00211` · `A00230` · `A00250` · `A00320`. 붙이려면 아래 사용법 그대로 메뉴 바를 만든다.

## 사용법

### PySide 툴

```python
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01

self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
help_menu = self.menu_bar.addMenu("Help")            # 이미 있는 공통 Help 를 돌려받는다
help_menu.addAction("About").triggered.connect(self.show_about)
```

기존 툴은 **`QMenuBar()` 한 줄만** 바꿨다. 나머지 코드는 그대로다.

### maya.cmds 툴

```python
from Framework.ui import JUN_mod_menu

cmds.menuBarLayout()
cmds.menu(label='Help')
cmds.menuItem(label='About', command=self.show_about)
JUN_mod_menu.add_common_items('Help', tool_file=__file__)   # 그 메뉴의 항목들 맨 끝에서
```

## 공통 항목 추가하기 — 앞으로 늘릴 때

`Framework/core/tool_menu.py` 의 `COMMON_MENUS` 에 `MenuItemSpec` 을 한 줄 더한다.
콜백은 `ctx`(`MenuContext`) 하나를 받는다.

```python
def open_tool_folder(ctx):
    # ctx.tool_name / ctx.tool_dir / ctx.window(PySide 창, cmds 는 None) / ctx.log(message)
    # ctx.tab_path = 지금 보이는 탭 라벨 리스트(바깥 → 안쪽, 없으면 [])
    ...

COMMON_MENUS = [
    ("Help", [
        MenuItemSpec("Copy Tool Name", copy_tool_name, "Copy this tool's folder name ..."),
        MenuItemSpec("Open Tool Folder", open_tool_folder, "Open this tool's folder"),
    ]),
    ("Tools", [                                  # 새 메뉴 제목이면 모든 툴에 그 메뉴가 생긴다
        MenuItemSpec("Reload Tool", reload_tool),
    ]),
]
```

- 리스트 순서가 곧 **메뉴 바의 순서 · 메뉴 안의 순서**다.
- 코드에서 더하려면 `register_common_item("Help", MenuItemSpec(...))` — 같은 label 이면 교체(리로드에 안전).
  **이미 열려 있는 창에는 반영되지 않는다**(창을 다시 열면 생긴다).
- UI 문자열(label · tooltip · 로그)은 **영어**.
- 콜백이 예외를 던져도 메뉴가 툴을 죽이지 않는다 — `[<label>] Failed : ...` 로 로그에 남긴다.

## 동작 규칙

### `addMenu("제목")` 은 "있으면 돌려주고 없으면 만든다"

드롭인 교체가 되는 이유다. 공통 `Help` 는 생성자에서 이미 만들어져 있으므로, 툴의 `addMenu("Help")` 가
**두 번째 Help 를 만들지 않고 그 메뉴를 받는다.** `&Help` 같은 니모닉 표시는 떼고 비교한다.
`addMenu(QMenu)` · `addMenu(icon, "제목")` 은 Qt 원래 동작이다.

### 공통 항목은 늘 메뉴 **맨 아래**

공통 항목은 생성자에서 먼저 들어가므로 그냥 두면 툴의 `About` 가 그 **아래**에 붙는다.
메뉴가 열릴 때(`aboutToShow`) **구분선 + 공통 항목을 맨 뒤로 옮긴다** — 툴이 항목을 언제 더하든
`About … | ─── | Copy Tool Name` 순서다. 툴 항목이 하나도 없으면 구분선은 숨긴다.

### 툴이 만든 메뉴는 공통 메뉴의 **왼쪽**

`addMenu("Operations")` 처럼 새 메뉴는 뒤에 붙이지 않고 **첫 공통 메뉴 앞에 끼운다** — `Operations | Help`.

### 툴 이름 찾기

`tool_file=__file__` 경로를 위로 올라가며
1. **부모가 `tools` 인 폴더** — `…/tools/A00060_jointTool_V03/app/ui/main_window.py` → `A00060_jointTool_V03`
2. 없으면 **`app` 폴더를 담은 폴더** — 릴리스처럼 `tools` 밖으로 복사된 PySide 툴 대비
3. 그래도 없으면 `None` — 클립보드를 건드리지 않고 `Could not find the tool folder name.` 를 남긴다.

직접 지정하려면 `JUN_mod_menuBar_qt_v01(tool_name="...")`.

## ★ 함정 — PySide2 에서 `QAction.menu()` 가 메뉴를 지운다

처음 구현은 이미 있는 메뉴를 `for action in self.actions(): action.menu()` 로 찾았다. mayapy 2024(PySide2)
에서 **이 서브클래스의 메뉴 액션에 `menu()` 를 한 번 부르면 C++ `QMenu` 가 지워져**, 바로 다음
`help_menu.addAction("About")` 이 `Internal C++ object (PySide2.QtWidgets.QMenu) already deleted` 로 죽었다.
(순수 `QMenuBar` 에서는 재현되지 않았다.) 그래서 메뉴는 **만들 때 파이썬 쪽 목록(`_menus`)에 기억**하고,
찾을 때 `menu()` 를 쓰지 않는다. 메뉴 제목 순서는 `menu_titles()`(액션 `text()`)로 본다.

## 검증 (2026-10-29, `Copy Tool Name + Tabs`, mayapy 2024 + 오프스크린 Qt) — 27/27

- **합성 창 17** — 3단 중첩(`Transfer / Follow / Options`) · 안쪽 탭 전환 · 다른 탭 페이지 속 탭 위젯 제외 ·
  `&Fill` 니모닉 제거 · 숨긴 그룹 속 탭 제외/보이면 포함(사슬 단위 순서) · Help 항목 순서(`Copy Tool Name` → `+ Tabs`) ·
  클립보드 · 로그 줄 · 툴팁 · `About` 위, 공통 항목 아래 · 탭 없는 창은 이름만 + `(no visible tabs)` ·
  툴 이름 없으면 클립보드 유지 · 수집 함수 예외 → `[]`.
- **실제 `A00110_animTool_V02` 창** — Transfer > Follow 로 바꾸고 누르면 클립보드 `A00110_animTool_V02 / Transfer / Follow`, 로그 기록.
- **메뉴 바 쓰는 PySide 툴 52곳 전수 스모크 52/52** — 창 생성 → 항목 존재 → 누르면 클립보드가 툴 폴더명으로 시작, 예외 없음.
- **maya.cmds 쪽** — 가짜 `cmds` 로 menuItem 2개 + 구분선, menuItem 경로에서 창 이름, 중첩 `tabLayout` 사슬(`Transfer / Follow / Options`) ·
  바깥 탭 전환 · 숨긴 tabLayout 제외 · 없는 창 → `[]` · command 호출 → 클립보드 6항목.
  **실제 마야 GUI 에서 cmds 메뉴 · 탭 확인은 아직.**

## 검증 (2026-09-17, mayapy 2024 + 오프스크린 Qt)

- **위젯 28항목** — 툴 이름 판정 6(tools 하위 · cmds 파일 · 폴더 자체 · 릴리스 복사본 · 못 찾음 · None) ·
  `addMenu("Help")` 가 같은 메뉴 · Help 하나뿐 · 공통 항목 맨 아래 · 구분선 표시/숨김 · 재정렬 멱등 ·
  `aboutToShow` 로 늦게 넣은 항목 뒤로 · 새 메뉴가 Help 왼쪽 · 같은 제목 재호출 · `&Help` ·
  하위 메뉴 · 클립보드 · 툴팁 · 로그창 기록 · 명시 `tool_name` · 못 찾으면 클립보드 유지 ·
  레지스트리 추가/교체/새 메뉴 순서 · 콜백 예외 · gc 뒤에도 메뉴 생존.
- **PySide 툴 42곳 전수 스모크 42/42** — 실제 `MainWindow` 생성 → 메뉴 바 1개 · `tool_name` 이 폴더명 ·
  Help 가 맨 오른쪽에 하나 · 툴의 기존 항목 유지 · 맨 아래 `Copy Tool Name` · 누르면 클립보드 = 폴더명 ·
  로그창에 기록.
- **maya.cmds 쪽** — `add_common_items` 를 가짜 `menuItem` 으로 호출해 구분선 · 항목 · annotation ·
  command(체크 bool 인자) → 클립보드 확인 5항목, 7개 툴 파일 컴파일 통과.
  **mayapy standalone 에는 cmds UI 가 없어**(창을 만들면 프로세스가 죽는다) 실제 cmds 메뉴는
  **마야 GUI 에서 확인해야 한다.**
