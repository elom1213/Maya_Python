---
title: Framework shell_integration — 시작 메뉴 바로가기 (Windows)
aliases: [shell_integration, Add to Start Menu, 시작 메뉴 바로가기]
tags: [maya-python, framework, windows, standalone]
updated: 2026-10-23
---

# Framework `core/shell_integration.py` — 시작 메뉴 바로가기 (Windows 10 · 11)

standalone PySide 툴이 **자기 바로가기(.lnk)를 시작 메뉴에 만들고 시작 화면 고정을 시도**하는 공용 모듈이다.
`JUN_Video_Tool`(0110) 의 `app/core/shell_integration.py` 를 Framework 로 옮긴 것(타입 힌트 제거, PySide2 툴에서도 import 됨).
Qt · Maya 비의존. 첫 사용처: `A00240_PathTool` v01.24 · `A00220_BackupTool` v01.19 의 `File > Add to Start Menu`.

## 동작

| 단계 | 내용 |
|------|------|
| 실행 명령 | `launch_spec(tool_root, icon)` — dev 면 **`pythonw.exe` + `<tool_root>/launch.py`**(콘솔 창 없음, pythonw 가 없으면 python), PyInstaller exe(frozen) 면 **exe 자신**(아이콘도 exe — `_MEIPASS` 의 .ico 는 실행마다 바뀌는 임시 폴더라 못 쓴다) |
| .lnk 작성 | `create_shortcut(lnk, spec, aumid, description)` — PowerShell 5.1 `Add-Type`(C#) 으로 `IShellLinkW` + `IPropertyStore` 를 직접 호출해 대상 · 인자 · 작업 폴더 · 아이콘 · 설명 · **AppUserModelID** 를 쓴다. 쓰고 나서 AUMID 를 되읽어 확인한다. 같은 경로면 덮어쓴다(툴 폴더 이동 뒤 갱신) |
| 시작 메뉴 | `add_to_start_menu(app_name, aumid, spec, description)` → `%APPDATA%\Microsoft\Windows\Start Menu\Programs\<app_name>.lnk` |
| 고정 | `pin_shortcut(lnk, "start" / "taskbar")` → `"pinned"` · `"already"` · `"unavailable"`. 셸 동사(`Shell.Application` → `Verbs()`)를 영어/한국어 이름으로 찾아 `DoIt()` |
| 안내문 | `start_menu_message(app_name, pinned)` — 툴마다 같은 영어 안내문 |

**왜 AppUserModelID 를 .lnk 에 넣나** — 툴은 `launch.py` 에서 `SetCurrentProcessExplicitAppUserModelID` 로 자기 ID 를 잡는다
([taskbar_icon_guide](taskbar_icon_guide.md)). 바로가기에도 같은 ID 가 있어야 바로가기로 띄운 창이 **같은 작업표시줄 버튼**으로
묶이고, 작업표시줄/시작 화면에 고정했을 때 아이콘이 python 이 아니라 툴 아이콘이 된다. `WScript.Shell` 로는 이 속성을 못 쓴다.

## Windows 10 · 11

쓰는 것이 전부 양쪽에 기본 탑재된 것뿐이다 — PowerShell 5.1(`Add-Type` 이 C# 을 .NET Framework 로 컴파일) · IShellLinkW COM ·
`%APPDATA%` 시작 메뉴 폴더. pywin32 같은 추가 패키지는 없다.

- **바로가기(앱 목록 · 검색)는 늘 만들어진다.** 이것이 기능의 본체다.
- **"Pin to Start" 셸 동사는 OS/빌드에 따라 없다**(Win10 1607+ 부터 프로그램의 자가 고정을 막았고, Win11 은 동사가 있어도
  결과를 알려 주지 않는다). 그래서 `"unavailable"` 이 정상 경로의 하나이고, 호출부는 안내 창에 수동 고정(앱 목록 → 우클릭 →
  시작 화면에 고정)을 적는다. `"pinned"` 는 **요청했다** 는 뜻이다.
- 작업표시줄 고정(`"taskbar"`)은 Win10 1809+ / 11 에서 보통 `"unavailable"` 이다. A00220 · A00240 은 이 메뉴를 두지 않았다
  (필요하면 비디오툴의 `Pin to Taskbar` + `set_window_relaunch` 를 같은 방식으로 옮긴다).
- PowerShell 출력은 스크립트 첫 줄에서 UTF-8 로 맞추고, 그 전에 난 오류(한국어 Windows 는 cp949)는 `mbcs` 로 다시 읽는다 —
  오류 창에 한국어 메시지가 깨지지 않게.

## 툴에서 쓰는 법 (A00240 · A00220 과 같은 모양)

```python
# app/config/app_meta.py
APP_USER_MODEL_ID = "Dnable.JUN.A00240.PathTool"
APP_NAME = "JUN Path Tool"                    # 시작 메뉴 · 검색에 보이는 이름 (= .lnk 이름)
APP_DESCRIPTION = "JUN Path Tool - path shortcuts, folder tree and junctions"

def start_menu_launch_spec():
    from Framework.core import shell_integration        # launch.py 가 sys.path 를 잡은 뒤라 lazy import
    return shell_integration.launch_spec(tool_root(), icon_path())
```

```python
# app/ui/main_window.py
from Framework.core import shell_integration

file_menu = self.menu_bar.addMenu("File")                # 공용 메뉴 바 — Help 의 왼쪽에 끼워진다
act = QAction("Add to Start Menu", self)
act.setEnabled(shell_integration.is_supported())
act.triggered.connect(self.add_to_start_menu)
file_menu.addAction(act)

def add_to_start_menu(self):
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        lnk = shell_integration.add_to_start_menu(APP_NAME, APP_USER_MODEL_ID, start_menu_launch_spec(), APP_DESCRIPTION)
        pinned = shell_integration.pin_shortcut(lnk, "start")
    except shell_integration.ShellIntegrationError as exc:
        error = exc
    finally:
        QApplication.restoreOverrideCursor()
    ...  # 오류면 QMessageBox.warning, 아니면 로그 한 줄 + QMessageBox.information(start_menu_message(APP_NAME, pinned))
```

## 검증 (2026-10-23)

- 시스템 python 3.11 로 **실제 .lnk 생성**(스크래치 폴더, 실제 시작 메뉴는 건드리지 않음): 대상 pythonw · 인자 launch.py ·
  작업 폴더 · 아이콘 `,0` · 설명을 `WScript.Shell` 로 되읽어 일치, AUMID 되읽기 일치, 덮어쓰기, 없는 드라이브 → `ShellIntegrationError`
  (한국어 오류 메시지 정상).
- 두 툴 창 offscreen(PySide6): 메뉴 `File | Help`, 항목 `Add to Start Menu`, 호출 인자(이름 · AUMID · spec · 설명), 성공 시 안내 창 + 로그,
  실패 시 경고 창 + 로그, 커서 복원.
- 실제 시작 메뉴 · 시작 화면 고정은 Windows 11 에서 비디오툴과 같은 코드로 동작 확인된 것. **이 두 툴에서의 실기 클릭과 Windows 10 실기는 아직.**
