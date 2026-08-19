---
name: push-only-when-asked
description: Never push to the remote without an explicit user request in the CURRENT turn — committing locally is fine. Violated twice by carrying a previous turn's push approval forward.
metadata:
  node_type: memory
  type: feedback
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
  modified: 2026-08-19T00:59:49.446Z
---

Do NOT push to any remote unless the user explicitly asks **in that turn**. Committing locally is fine and expected, but the push to the remote must wait for an explicit "push" instruction.

**Why:** The user stated this as a standing rule (2026-07-21): "앞으로 내 요청 없이는 원격저장소에 푸시하지 마." They want to control when work becomes visible on the remote. This overrides any habit of pushing right after finishing a tool — finishing work does not imply permission to push.

Reaffirmed **2026-08-10** after a violation: "내가 내 허락없이 푸시하지 말라고 했는데 넌 푸시를 했다.
이건 너의 중대한 실수다. 앞으로 다시는 내 허락없이 푸시하지 마라."

Reaffirmed again **2026-08-19** after the SAME failure mode recurred: "내 요청없이 푸시하지 말라고
했는데 네가 어겼어."

**The failure mode that caused it — twice. Watch for this.** Both violations are the same shape:
an earlier turn said "푸시해", the next turn asked only for a feature, and the push happened anyway.

- 2026-08-10: two turns ended with "문서, 워크로그 갱신하고 푸시해"; the next turn said only
  "기능과 문서를 만들어" and the pattern was carried over.
- 2026-08-19: the turn asking to push A00390 was followed by a turn asking only for the A00110
  Copy Key `1->n` feature. That work was committed **and pushed** unasked (`5bf55d7`). The user
  chose to leave it on the remote, but it should never have gone out.

**A push request in earlier turns never carries into the current one.** Permission is per-turn, and
a run of push turns makes the next silent turn *more* likely to be misread, not less. If the current
turn's text does not contain a push instruction, there is no permission — regardless of what the
last N turns said. Note that both times the reasoning felt like momentum ("we're in a push rhythm"),
not like a decision — so the rhythm itself is the warning sign.

**How to apply:** After completing and committing a change, stop and report; do not run `git push`
on your own initiative.

Hard gate — before typing `git push`, quote the current user message to yourself and point at the
push word in **it** ("푸시해", "push", "올려"). No push word in the current message ⇒ no push, full
stop. Do not accept "the previous turn said push", "the work is finished", "docs are updated", or
"it is the same task as the turn that authorized a push" as substitutes.

When a push IS requested, follow [[push-target-dnable-dev]] for the target,
[[push-includes-tool-guide-docs]] for what to include, and
[[push-only-own-session-work]] for what must be **left out** — a push carries only this
session's work, never another session's changes sitting in the working tree. If work is done and no push was requested,
end by saying it is committed locally and ready to push when they say so — do not push, and do not
undo a past push on your own initiative either (that is also a remote-facing action; offer options
and let the user choose, as on 2026-08-19).
