---
name: framework-shell-integration
description: Framework/core/shell_integration.py — standalone 툴의 File > Add to Start Menu (시작 메뉴 .lnk + AUMID, Windows 10/11). A00240 · A00220 · A00210 에 적용 (2026-10-23)
metadata:
  type: project
---

**standalone PySide 툴의 "시작 메뉴 바로가기" 는 `Framework/core/shell_integration.py` 로.** JUN_Video_Tool(0110)
`app/core/shell_integration.py` 를 공용으로 옮긴 것(2026-10-23). 첫 적용 A00240_PathTool v01.24 · A00220_BackupTool v01.19,
이어 A00210_FileManager v01.39 (`File > Add to Start Menu`, 로그는 창의 `self.log`). 문서 `JUN_All/docs/Framework_shell_integration.md`.

**How to apply (새 standalone 툴에 붙일 때):**
- `app/config/app_meta.py` 에 `APP_NAME`(= .lnk 이름) · `APP_DESCRIPTION` · `start_menu_launch_spec()`(lazy import 로 Framework).
- 메인 창: `self.menu_bar.addMenu("File")`(공용 메뉴 바라 Help 왼쪽에 끼워짐) + `QAction("Add to Start Menu")` →
  `add_to_start_menu(APP_NAME, AUMID, spec, desc)` → `pin_shortcut(lnk, "start")` → 로그 + `QMessageBox.information(start_menu_message(...))`.
- 사용자 요구: **Windows 10 에서도 동작**. 모듈은 PowerShell 5.1 + COM + `%APPDATA%` 만 쓴다. "Pin to Start" 동사는 없을 수 있어
  `"unavailable"` 이 정상 경로 — 안내 창이 수동 고정을 알려 준다. 바로가기(앱 목록 · 검색)는 항상 생긴다.
- 트랩: PowerShell 오류가 콘솔 코드페이지(cp949)로 나와 UTF-8 디코드가 깨진다 → PS 첫 줄 `[Console]::OutputEncoding = UTF8` + `mbcs` 폴백.
  비디오툴 원본엔 이 처리가 없다(거기도 같은 증상일 것).
- 트랩: frozen(PyInstaller) 이면 아이콘을 `_MEIPASS` 의 .ico 로 두지 말 것(실행마다 바뀌는 임시 폴더) — exe 자신을 아이콘으로.
- A00240 은 로그창이 없어 결과 한 줄이 Junction 탭의 공용 로그(`menu_bar.log` 가 `findChildren` 으로 찾는 곳)에 간다.
- 작업표시줄 고정(`Pin to Taskbar` + `set_window_relaunch`)은 옮기지 않았다 — 요청 범위 밖. 필요하면 비디오툴 `main_window.pin_to_taskbar` 를 같은 식으로.
- 검증: 스크래치 폴더에 실제 .lnk 만들어 WScript/AUMID 되읽기 + 두 창 offscreen. **실기 클릭은 A00210 에서 확인(2026-10-23, Win11) · Win10 실기 아직.**

관련: [[standalone-taskbar-icon-method]], [[framework-menubar-widget]], [[release-layout-launch-py]], [[wip-a00220-pin]]
