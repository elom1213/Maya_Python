---
name: framework-menubar-widget
description: 공용 메뉴 바 JUN_mod_menuBar_qt_v01 + 공통 항목 레지스트리 Framework/core/tool_menu.py (2026-09-17). 모든 툴 공통 메뉴 항목은 여기 한 줄로. PySide2 에서 QAction.menu() 를 부르면 QMenu 가 지워진다
metadata: 
  node_type: memory
  type: project
  originSessionId: 1391a069-f7af-476b-85b5-d9bbf6628251
  modified: 2026-09-17T01:56:48.094Z
---

**툴 창 메뉴의 공통 항목은 `Framework/core/tool_menu.py` 의 `COMMON_MENUS` 에 한 줄 더한다.**
PySide 툴은 `Framework/qt/MOD_menuBar_qt_v01.py` 의 `JUN_mod_menuBar_qt_v01(tool_file=__file__)`(QMenuBar 대체),
maya.cmds 툴은 `JUN_mod_menu.add_common_items('Help', tool_file=__file__)` 가 같은 목록을 읽는다.
첫 항목 `Help > Copy Tool Name`(툴 폴더명을 클립보드로). 문서 `JUN_All/docs/Framework_MOD_menuBar_qt.md`.

- 사용처: PySide 툴 **42곳 전부**(QMenuBar 쓰던 곳) + cmds 툴 7곳(A00000/10/20/30/40/50/60 V01).
  **새 툴이 메뉴 바를 만들면 `QMenuBar()` 대신 이 위젯을 쓸 것.** 메뉴 바 없는 창 15곳은 미적용.
- 드롭인 원리: `addMenu("제목")` 이 **있으면 돌려주고 없으면 만든다** → 툴 코드는 생성 한 줄만 교체.
  공통 항목은 `aboutToShow` 에서 구분선과 함께 **맨 아래로**, 툴이 만든 메뉴는 **공통 메뉴 왼쪽**에 insert.
- 결과 알림은 창 안 [[framework-log-widget]] 을 **누를 때** `findChildren` 으로 찾아 기록(메뉴 바가 로그창보다 먼저 생성됨).

**★ PySide2(mayapy 2024)에서 이 QMenuBar 서브클래스의 메뉴 액션에 `action.menu()` 를 부르면 C++ QMenu 가
지워진다** — 다음 `addAction` 이 `Internal C++ object already deleted`. 순수 QMenuBar 에서는 재현 안 됨.
메뉴는 만들 때 파이썬 목록에 기억하고 `menu()` 로 되찾지 말 것. 제목 순서는 `action.text()`.

**★ mayapy standalone 에서 `cmds.window`/`cmds.menu` 를 만들면 프로세스가 Fatal Error 로 죽는다**
(untitled[Recovered].ma 저장 시도). cmds UI 는 헤드리스 검증 불가 — `cmds.menuItem` 을 가짜로 바꿔 인자만 확인하고
실물은 마야 GUI 에서. (마야 GUI 확인 아직 — cmds 툴 7개 메뉴, 실제 마야 창의 PySide 메뉴 모양.)
