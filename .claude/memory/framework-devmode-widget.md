---
name: framework-devmode-widget
description: "메뉴 바 `Dev Mode`(Developer / Release) 는 공용 위젯 JUN_mod_devMode_qt_v01 + 판정 Framework/core/dev_mode.py — 툴마다 다시 짜지 말 것, 화면 전환은 툴의 apply_view(bool) 가 한다"
metadata:
  node_type: memory
  type: project
  originSessionId: 1b679bc1-ca09-4af4-b1a4-09415405fb3c
  modified: 2026-10-12T00:22:06.207Z
---

2026-10-12 에 A00330 v01.26 의 `_build_dev_mode_menu` 를 `Framework/qt/MOD_devMode_qt_v01.py`
(`JUN_mod_devMode_qt_v01`) 로 올렸고, 개발자 모드 판정은 `Framework/core/dev_mode.py` 의
`is_dev_mode(tool_file)` 로 올렸다. A00330 (v01.27) · A00120 (v01.11) 이 쓴다.

- 개발자 모드에서만 메뉴가 생긴다(Help **오른쪽**, QMenu 를 직접 `addMenu` — 문자열 `addMenu` 는 Help 왼쪽에 끼운다).
  배포본(툴 폴더 안에 Framework 동봉)은 메뉴가 없고 `is_developer()` 가 늘 False.
- 위젯은 **화면을 바꾸지 않는다** — 툴이 `modeChanged(bool)` 을 `apply_view(developer)` 에 잇고 처음에 한 번 직접 부른다.
  모든 위젯을 만든 **뒤**에 생성할 것(apply_view 가 그것들을 숨긴다).
- 툴의 "화면" 이 다른 위젯 상태(A00330 Token 의 `rules_editable`)면 두 방향을 다 잇는다(`set_developer` 는 같은 값이면 시그널 없음).
- 판정만 필요하면 `Framework.core.dev_mode.is_dev_mode(__file__)` — maya/Qt 비의존.

**Why:** 배포 화면을 개발자가 미리 볼 수 있어야 하는 툴이 늘고 있다(A00330 → A00120). 메뉴와 판정이 툴마다 복제되면
규칙(릴리즈본 판정 · config.py 경로 읽기)이 어긋난다.

**How to apply:** 새 툴에 Developer / Release 화면이 필요하면 이 위젯을 쓰고 `apply_view` 하나에 숨김 목록을 모은다.
문서 `JUN_All/docs/Framework_MOD_devMode_qt.md`. 관련: [[release-layout-launch-py]], [[framework-menubar-widget]], [[wip-a00120-fkik-auto-devmode]].
