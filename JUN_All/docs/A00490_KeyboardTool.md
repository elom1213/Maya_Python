# A00490_KeyboardTool — 사용 안내

**키 여러 개를 순서대로, 키마다 정한 횟수 · 간격으로 자동으로 누르는** 툴.
루프 모드로 끝없이(또는 정한 횟수만큼) 반복할 수 있고, **고른 창에만** 키를 보낼 수 있다.

예) `Down` 을 1초 간격으로 10번 → `Up` 을 1초 간격으로 10번 → (Loop) 다시 `Down` 10번 …
크롬 창 A, B, C 가 떠 있을 때 A, B 만 체크하면 A, B 에만 들어가고 C 는 그대로다.

> Maya 안에서 도는 툴이 아니라 `A00240_PathTool` 처럼 **Windows 에서 독립 실행되는 PySide6 앱** 이다.
> **Windows 10 · 11 둘 다** 동작한다 — 키 전송은 두 OS 에 똑같이 있는 user32 API 만 쓴다(5장).

---

## 1. 실행

- **개발 실행**: `python JUN_All/tools/A00490_KeyboardTool/launch.py`
- **exe 빌드**: 툴 폴더의 `build_exe.bat` → `dist/A00490_KeyboardTool.exe`
- 필요 패키지: `PySide6`(+ 빌드용 `pyinstaller`). 키 전송은 표준 라이브러리 `ctypes` 만 쓴다.
- 작업표시줄 아이콘: `icon/A00490_KeyboardTool.ico`(16~256px) + AppUserModelID
  `Dnable.JUN.A00490.KeyboardTool` ([taskbar_icon_guide.md](taskbar_icon_guide.md)).

---

## 2. 화면

| 영역 | 내용 |
|------|------|
| **Key Sequence** | 표 한 줄 = 키 하나. `Key` · `Count`(누를 횟수) · `Interval (s)`(한 번 누른 뒤 기다릴 시간). 위에서 아래로 실행된다. |
| | `Add` / `Remove` / `Up` / `Down` / `Clear` 로 줄 편집. |
| | `Preset` — 시퀀스 + Loop + Start Delay + Send Method 를 이름 붙여 저장/불러오기. |
| **Target Windows** | `Checked windows only` — 아래 목록에서 체크한 창에만 보낸다. |
| | `Whatever window is active` — 실제 키보드처럼, 누르는 순간 포커스를 가진 창에 보낸다. |
| | 목록은 `[프로세스]  창 제목`. `Filter` 로 거르기(예: `chrome`), `Refresh` 로 다시 읽기. 이 툴 자신은 목록에 안 나온다. |
| | `Send Method` — Background / Foreground (4장). |
| **Run** | `Loop` + `Times`(0 = Infinite), `Start Delay`, `Start`, `Stop (F9)`, 진행 상태, `Pin`(항상 위). |
| **Log** | 공용 로그창. 시작 · 단계 · 경고(창이 닫힘 등) · 종료 사유. |

### Key 입력

- 칸을 클릭하고 **키를 누르면** 그 키 이름이 들어간다 — `Ctrl` / `Shift` / `Alt` 조합도 (`Ctrl+C`).
  키보드 배열(한/영)과 무관하게 가상 키 코드로 받는다.
- 오른쪽 `...` 버튼 메뉴에서 골라도 된다 (Arrows / Navigation / Common / Function / Numpad / Letters / Digits).
- 숫자패드 기호는 `NumAdd` `NumSub` `NumMul` `NumDiv` `NumDec` 로 적는다 (`+` 는 조합 구분자라서).
- 이름이 없는 키는 `VK_xx`(16진 가상 키 코드) 로 들어간다.

### 실행 순서

```
for loop (Loop 꺼짐 = 1번, Times 0 = Stop 까지):
    for step in 표:
        step.Count 번:
            체크한 모든 창에 step.Key 누르기   (누르고 떼기 30ms)
            step.Interval 초 기다리기
```

- **Stop** 버튼 또는 **F9** (어느 창에서든) 로 멈춘다. 기다리는 도중에도 20ms 안에 멈춘다.
- 실행 중 대상 창이 닫히면 `[WARN]` 을 남기고 대상에서 뺀다. 전부 닫히면 끝난다.
- 창을 닫으면 실행도 멈춘다.

---

## 3. 프리셋

`<툴>/data/presets/<이름>.json` (exe 로 실행하면 exe 옆 `data/presets/`).
기본으로 `Down_Up_Loop`(Down 10 · Up 10, 1초, Loop) 이 들어 있다.
**대상 창은 저장하지 않는다** — 창 핸들은 창을 열 때마다 바뀐다.

```json
{"steps": [{"key": "Down", "count": 10, "interval": 1.0}, ...],
 "loop": true, "loop_count": 0, "start_delay": 0.0, "method": "background"}
```

---

## 4. Send Method — Background vs Foreground

| | Background (기본) | Foreground |
|---|---|---|
| 방식 | 대상 창에 `WM_KEYDOWN`/`WM_KEYUP` 를 `PostMessage` | 대상 창을 앞으로 가져와 `SendInput` |
| 포커스 | **안 뺏는다** — 다른 일을 하면서 돌려도 된다 | 누를 때마다 그 창으로 옮겨간다. 끝나면 원래 창으로 돌아온다 |
| 여러 창 | 같은 순간에 전부 | 창마다 차례로 (앞으로 → 누르기) |
| 조합키(`Ctrl+C`) | **대부분 안 먹는다** — 메시지로는 Ctrl 눌림 상태를 못 바꾼다 (실행 시 `[WARN]`) | 먹는다 |
| 안 먹는 곳 | 키 상태를 직접 읽는 앱(게임 · 일부 DirectInput 앱) | 거의 없음 |

- Background 는 대상 창 안에서 **마지막으로 포커스를 가졌던 칸**(`GetGUIThreadInfo` 의 `hwndFocus`)에 보낸다
  — 메모장이면 편집 칸. 그래서 창을 한 번 클릭해 원하는 칸에 포커스를 둔 뒤 다른 창으로 가도 된다.
- 방향키 · PageUp 등은 **확장 키 플래그**를 붙여 보낸다. 안 붙이면 숫자패드 2/4/6/8 로 받는 앱이 있다.
- `Whatever window is active` 는 대상이 없으므로 항상 SendInput (= 실제 키보드) 이다.

---

## 5. Windows 10 / 11 호환

쓰는 API 는 전부 Vista~ 고정 API 라 Win10 · 11 이 같다:
`EnumWindows` `PostMessageW` `SendInput` `GetGUIThreadInfo` `AttachThreadInput` `SetForegroundWindow`
`QueryFullProcessImageNameW` `GetAsyncKeyState`, 그리고 `DwmGetWindowAttribute(DWMWA_CLOAKED)`(Win8~).

- **cloaked 창 제외** — Win10/11 은 숨은 UWP 껍데기(설정 · 계산기 대기 창 등)가 "보이는 창" 으로 열거된다.
  DWM cloaked 속성으로 걸러 목록에 안 나오게 한다.
- **포커스 가져오기** — Windows 는 포그라운드가 아닌 프로세스의 `SetForegroundWindow` 를 막는다(작업표시줄만 깜빡).
  현재 포그라운드 스레드에 `AttachThreadInput` 으로 잠깐 붙어 허용받는다. 최소화된 창은 먼저 복원한다.
- **`SendInput` 구조체** — 64bit 에서 `INPUT` 이 40바이트여야 받는다. 공용체에 `MOUSEINPUT` 을 같이 둬서 크기를 맞춘다.

---

## 6. 주의 · 한계

- **크롬 탭은 창이 아니다.** 한 창 안의 탭 A, B, C 는 창 하나다 — 키는 그 창의 **보이는 탭**에만 간다.
  탭마다 따로 보내려면 탭을 끌어내 **창으로 분리**한다.
- **관리자 권한 창**에는 둘 다 안 들어간다(UIPI). 이 툴도 관리자로 실행해야 한다.
- 최소화된 창은 Background 로 보내도 앱에 따라 처리를 미룬다. Foreground 는 복원해서 보낸다.
- 시퀀스에 **F9** 가 있고 SendInput 을 쓰면(Foreground · active window) 우리가 보낸 F9 가 정지로 읽히므로
  그 실행만 F9 정지가 꺼진다(`[WARN]`). Stop 버튼은 그대로 된다.
- 반복 입력을 막는 웹사이트 · 게임의 이용 약관은 사용자가 확인할 것.

---

## 7. 구조

```
A00490_KeyboardTool/
├── launch.py                 # AppUserModelID → QApplication → teal_dark 테마 → MainWindow
├── app/
│   ├── config/version.py · app_meta.py
│   ├── core/                 # Qt 비의존
│   │   ├── keys.py           # 키 이름 <-> 가상 키 코드, 'Ctrl+C' 파싱
│   │   ├── win32.py          # 창 열거 + PostMessage / SendInput / activate (ctypes)
│   │   ├── runner.py         # Step, SequenceRunner (스레드, Stop 이벤트 + F9 감시)
│   │   └── presets.py        # data/presets/*.json
│   └── ui/
│       ├── main_window.py    # 세 구역 + 로그, 러너 콜백은 Qt 신호로 메인 스레드에
│       └── key_capture.py    # 키를 눌러 입력하는 칸 + ... 메뉴
├── data/presets/Down_Up_Loop.json
├── icon/A00490_KeyboardTool.svg · .png(32) · .ico(16~256)
├── build_exe.bat · launch.spec · requirements.txt · CHANGELOG.md
```

---

## 8. 검증 (2026-10-01, Windows 11)

별도 프로세스의 수신 창 3개(A, B, C)를 띄우고 받은 키를 파일에 적게 했다.

- **Background**, 대상 A · B, `Down x3 → Up x2 → Ctrl+C x1`, Loop 2회 → A · B 에 같은 순서로 2바퀴, **C 는 0건**.
  `Ctrl+C` 는 Ctrl 과 C 가 따로 들어가고 수식키 상태는 없음(4장 표대로).
- **Foreground**, 대상 A · B → A · B 에 들어가고 `Ctrl+C` 는 Ctrl 수식키와 함께 들어감, C 0건, 끝난 뒤 원래 창으로 포커스 복귀.
- UI 경로: Start → 진행 표시 `Loop 1/inf | Step 1/1 | Down 8/100` → Stop → `Idle - Stopped.`
- 실행 중 대상 창을 닫음 → `[WARN] Window closed ...` → `All target windows are closed.` 로 끝남.
- F9 (SendInput 으로 시스템에 주입) → `Stopped by F9.`
- 실제 크롬 창으로는 아직 확인하지 않았다 (테스트 시점에 크롬이 떠 있지 않았음).
