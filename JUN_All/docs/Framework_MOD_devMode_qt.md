---
title: Framework 공용 위젯 — MOD_devMode_qt (Dev Mode 메뉴)
aliases: [JUN_mod_devMode_qt, Dev Mode, Developer / Release, 배포 화면 미리보기, dev_mode]
tags: [framework, qt, widget, release, maya-python]
updated: 2026-10-12
---

# `JUN_mod_devMode_qt_v01` — 메뉴 바의 `Dev Mode` 메뉴

`JUN_All/Framework/qt/MOD_devMode_qt_v01.py` + 판정 `JUN_All/Framework/core/dev_mode.py`

툴마다 **개발자가 보는 화면**과 **배포본을 받은 사람이 보는 화면**이 다를 때, 개발자가 배포 화면을
그대로 미리 볼 수 있게 창 맨 위 메뉴 바에 `Dev Mode` 메뉴를 둔다.

```
Help | Dev Mode
       (o) Developer
       ( ) Release (shared tool)
```

`A00330_NamingTool` v01.26 의 `_build_dev_mode_menu` 를 공용으로 올렸다(2026-10-12). 같은 날
`A00120_FKIK` v01.11 이 두 번째 사용자가 됐다 — A00330 은 "규칙을 못 바꾸는 화면", A00120 은
"Auto 만 보이고 리스트 · 디버그 버튼이 없는 화면" 이 Release 다.

---

## 1. 규칙

- **개발자 모드에서만 메뉴를 만든다.** 배포본에는 메뉴 자체가 없고 `is_developer()` 는 늘 `False` —
  배포 화면이 고정된다. 판정은 `Framework.core.dev_mode.is_dev_mode(tool_file)`:

  | | 판정 |
  |---|---|
  | 릴리즈본 | 툴 폴더 안에 `Framework` 가 동봉돼 있다 → **항상 False** ([`Release_Layout`](Release_Layout.md)) |
  | dev 트리 | `JUN_All/config.py` 의 `DEV_MODE` — **경로로** 읽는다(`import config` 는 다른 툴 폴더의 config.py 를 집을 수 있다) |

  툴 폴더는 `tool_menu.tool_dir_from_path` 와 같은 규칙으로 찾는다(부모가 `tools` 인 폴더, 없으면 `app` 을 담은 폴더).
- 메뉴는 공통 메뉴(`Help`)의 **오른쪽**이다. 공용 메뉴 바의 `addMenu("제목")` 은 새 메뉴를 `Help` 왼쪽에
  끼우므로, QMenu 를 직접 넘겨 Qt 기본 동작(맨 오른쪽)을 쓴다.
- **화면 전환은 위젯이 하지 않는다.** 툴이 `modeChanged(bool)` 을 받아 자기 위젯을 숨기고 보인다
  (`True` = Developer). 코드에서 모드가 바뀌면 `set_developer()` 로 체크를 맞춘다(같은 값이면 시그널 없음).

---

## 2. 쓰는 법

```python
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_devMode_qt_v01 import JUN_mod_devMode_qt_v01

self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
help_menu = self.menu_bar.addMenu("Help")
...
# 모든 위젯을 만든 뒤 (apply_view 가 그것들을 숨기므로)
self.dev_mode = JUN_mod_devMode_qt_v01(
    self.menu_bar, tool_file=__file__,
    developer_tooltip="Developer view - ...",            # 선택
    release_tooltip="The view people get in the shared tool - ...")
self.dev_mode.modeChanged.connect(self.apply_view)       # apply_view(developer: bool)
self.apply_view(self.dev_mode.is_developer())            # 처음 화면

def apply_view(self, developer):
    self.lists_box.setVisible(developer)
    self.btn_debug.setVisible(developer)
    self.te_log.set_shrunk(not developer)
```

| API | 뜻 |
|---|---|
| `is_available()` | 메뉴가 있는지 (= 개발자 모드) |
| `is_developer()` / `is_release()` | 지금 화면. 배포본은 늘 Release |
| `set_developer(bool)` / `set_release()` | 화면을 바꾼다. 배포본에서는 Release 로 고정돼 아무 일도 안 한다 |
| `modeChanged(bool)` | 화면이 바뀔 때. `True` = Developer |
| `menu` / `act_developer` / `act_release` | QMenu · QAction (배포본은 `None`) |
| `developer=` (생성자) | 개발자 모드일 때의 처음 화면. 기본 `True` |

**양방향 동기** (A00330) — 툴의 "화면" 이 다른 위젯 상태(예: Token 위젯의 `rules_editable`)라면 두 방향을 다 잇는다:

```python
self.dev_mode.modeChanged.connect(widget.set_rules_editable)       # 메뉴 -> 위젯
widget.rulesEditableChanged.connect(self.dev_mode.set_developer)   # 위젯 -> 메뉴
```

---

## 3. 판정만 쓰기

메뉴 없이 "개발자에게만 보이는 버튼" 을 둘 때는 core 만 부른다.

```python
from Framework.core import dev_mode
if dev_mode.is_dev_mode(__file__):
    row.addWidget(self.btn_values)
```

`is_release(tool_file)` · `read_dev_mode_flag(tool_file)` · `tool_root(tool_file)` 도 있다.
maya / Qt 를 import 하지 않으므로 standalone 툴 · mayapy 에서도 import 만으로 깨지지 않는다.

---

## 4. 검증 (2026-10-12, mayapy 2024 오프스크린)

- dev 트리(`DEV_MODE = True`) : 메뉴 `['Help', 'Dev Mode']`, 처음 Developer. `set_developer(False)` → 툴의 `apply_view(False)` 호출 ·
  `act_release` 체크. 가짜 릴리즈 배치(`<tmp>/tools/X/Framework`)의 파일 경로 → `is_release True` · `is_dev_mode False`.
- A00330 : 메뉴 → `rules_editable False` · 탭 숨김, 위젯 → 메뉴 체크 따라감, `act_release.trigger()` 도 같음.
- A00120 : Release 로 바꾸면 Auto 라디오 · 리스트 접이식 숨김 · Bake (Constraint) · Force Refresh 숨김 · 로그 접힘, 창 높이 660 → 520.

사용처 : `A00330_NamingTool` (v01.27) · `A00120_FKIK` (v01.11).
