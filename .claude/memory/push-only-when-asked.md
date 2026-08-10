---
name: push-only-when-asked
description: Never push to the remote without an explicit user request — committing locally is fine
metadata: 
  node_type: memory
  type: feedback
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
  modified: 2026-08-10T02:15:16.771Z
---

Do NOT push to any remote unless the user explicitly asks in that turn. Committing locally is fine and expected, but the push to the remote must wait for an explicit "push" instruction.

**Why:** The user stated this as a standing rule (2026-07-21): "앞으로 내 요청 없이는 원격저장소에 푸시하지 마." They want to control when work becomes visible on the remote. This overrides any habit of pushing right after finishing a tool — finishing work does not imply permission to push.

Reaffirmed **2026-08-10** after a violation: "내가 내 허락없이 푸시하지 말라고 했는데 넌 푸시를 했다.
이건 너의 중대한 실수다. 앞으로 다시는 내 허락없이 푸시하지 마라."

**The failure mode that caused it — watch for this.** Two turns in a row had ended with
"문서, 워크로그 갱신하고 푸시해". The next turn said only "기능과 문서를 만들어" (no push), and the
prior pattern was carried over anyway. **A push request in earlier turns never carries into the
current one.** Permission is per-turn, and a run of push turns makes the next silent turn *more*
likely to be misread, not less. If the current turn's text does not contain a push instruction,
there is no permission — regardless of what the last N turns said.

**How to apply:** After completing and committing a change, stop and report; do not run `git push`
on your own initiative. Before any `git push`, re-read **the current user message** and confirm the
push word is in *it* (e.g. "푸시해", "push"). When it is, follow [[push-target-dnable-dev]] for the
target and [[push-includes-tool-guide-docs]] for what to include. If work is done and no push was
requested, end by saying it is committed locally and ready to push when they say so — do not push,
and do not undo a past push on your own initiative either (that is also a remote-facing action).
