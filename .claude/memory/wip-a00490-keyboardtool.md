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
- 테스트는 사용자 앱 대신 **별도 프로세스 Qt 수신 창 A/B/C** 로 했다(받은 VK 를 파일에 기록). **실제 크롬은 미확인** — 크롬 탭은 창이 아니라 분리해야 따로 보낼 수 있다.

**Why:** 사용자 요청(2026-10-01) — 크롬 창 A, B 에만 Down/Up 반복, C 는 그대로.
**How to apply:** 기능 추가 시 core(`keys`/`win32`/`runner`)는 Qt 비의존 유지. 관련 [[standalone-taskbar-icon-method]] · [[new-tool-needs-icon]] · [[framework-checklist-behavior]].
