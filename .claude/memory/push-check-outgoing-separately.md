---
name: push-check-outgoing-separately
description: git push 전에 나가는 커밋 목록을 **별도 명령**으로 보고 판단한 뒤 다음 명령에서 push — 한 줄로 묶지 말 것 (2026-11-05 다른 세션 커밋 동반 푸시)
metadata:
  type: feedback
---

`git log <remote>/<branch>..HEAD` 와 `git push` 를 **한 명령에 묶지 않는다.** 먼저 나가는 커밋 목록만 출력하고,
전부 이 세션 커밋인지 확인한 다음 **다음 도구 호출**에서 push 한다. 다른 세션 커밋이 끼어 있으면 멈추고 사용자에게 묻는다.

**Why:** 2026-11-05 "푸시하고 작업 진행해" 턴에서 `git fetch && git log ..HEAD && git push` 를 한 줄로 실행 →
다른 세션이 그 사이 만든 `6aa97fb5`(A00600_SceneCleanup v01.00)가 함께 원격으로 나갔다. 전역 규칙 3장 위반. 이전 턴들에서는
세션 시작 이후 커밋이 내 것뿐이라 묶어도 괜찮았던 관성이 원인이다.

**How to apply:** 매 push 마다 — ① `git log --oneline <remote>/<branch>..HEAD` 단독 실행 ② 목록 검토(작성 세션 판단) ③ 그 다음 호출에서 push.
다른 세션 커밋이 위에 쌓여 있으면 그것까지 나가므로 사용자 결정. 관련 [[push-target-dnable-dev]].
