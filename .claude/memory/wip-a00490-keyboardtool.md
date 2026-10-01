---
name: wip-a00490-keyboardtool
description: "A00490_KeyboardTool (2026-10-01 신규, v01.00) - 키 시퀀스 자동 입력, 고른 창에만. Background(PostMessage)는 조합키가 안 먹고 Foreground(SendInput)는 포커스를 옮긴다"
metadata:
  node_type: memory
  type: project
  originSessionId: 61b22058-2a64-4823-9a3c-e5227d4bb12f
  modified: 2026-10-01T08:35:02.281Z
---

`JUN_All/tools/A00490_KeyboardTool` — standalone PySide6 (A00240 배치, teal_dark). 문서 `docs/A00490_KeyboardTool.md`.
키마다 Count · Interval, Loop(0 = 무한), 대상 창 체크 목록에만 전송. Win10 · 11 둘 다가 요구사항.

- **Background** = `PostMessage(WM_KEYDOWN/UP)` 를 창의 `GetGUIThreadInfo.hwndFocus` 에. 포커스 안 뺏고 여러 창 동시.
  **조합키는 수식키 상태가 안 실린다**(검증에서 Ctrl 과 C 가 따로, mods=0) → 실행 시 `[WARN]`.
- **Foreground** = `AttachThreadInput` + `SetForegroundWindow` 후 `SendInput`. 조합키 OK, 끝나면 원래 창 복귀.
- 정지 = Stop 버튼 + **F9**(`GetAsyncKeyState` 폴링). SendInput 으로 보낸 F9 도 잡히므로 시퀀스에 F9 + SendInput 이면 그 실행만 끈다.
- `+` 가 조합 구분자라 숫자패드 기호는 `NumAdd/NumSub/...`.
- **v01.01 — 크롬 계열(`Chrome_WidgetWin_*`: Chrome/Edge/Whale/Electron)은 활성 창일 때만 키를 처리한다.**
  비활성 창엔 PostMessage 도, 렌더 자식 HWND 로도 무시. 가짜 `WM_ACTIVATE` 는 쓰지 않는다(보낸 직후 테스트 크롬이 정상 종료됐다 — 크래시 기록 없음, 인과는 미확인).
  → Send Method **Auto**(기본): 크롬 계열은 Foreground 로 차례 전환. **크롬 창들은 UI 스레드 하나라** 키를 보내고
  바로 다음 창을 활성화하면 키가 다음 창으로 샌다 → 대상 스레드에 `AttachThreadInput` 후 `GetKeyState` 가
  눌림/떼짐을 보일 때까지 대기(`press_on_window`, 창당 ~10ms). `activate` 안에서 같은 스레드를 다시 붙였다 떼면
  바깥 붙임까지 풀리므로 `keep_thread` 로 건너뛴다. Interval 은 바퀴 시작 간격.
- 크롬 테스트는 **임시 `--user-data-dir` 크롬 + 키를 받으면 탭 제목에 횟수를 적는 html** 로 한다(제목은 GetWindowText 로 읽힘).
  창 목록은 Z 순서라 활성화마다 순서가 바뀐다 — **비교는 hwnd 기준으로**.
- 테스트는 사용자 앱 대신 **별도 프로세스 Qt 수신 창 A/B/C** 로 했다(받은 VK 를 파일에 기록). 크롬 탭은 창이 아니라 분리해야 따로 보낼 수 있다.

**Why:** 사용자 요청(2026-10-01) — 크롬 창 A, B 에만 Down/Up 반복, C 는 그대로.
**How to apply:** 기능 추가 시 core(`keys`/`win32`/`runner`)는 Qt 비의존 유지. 관련 [[standalone-taskbar-icon-method]] · [[new-tool-needs-icon]] · [[framework-checklist-behavior]].
