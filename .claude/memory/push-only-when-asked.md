---
name: push-only-when-asked
description: Never push to the remote without an explicit user request — committing locally is fine
metadata: 
  node_type: memory
  type: feedback
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

Do NOT push to any remote unless the user explicitly asks in that turn. Committing locally is fine and expected, but the push to the remote must wait for an explicit "push" instruction.

**Why:** The user stated this as a standing rule (2026-07-21): "앞으로 내 요청 없이는 원격저장소에 푸시하지 마." They want to control when work becomes visible on the remote. This overrides any habit of pushing right after finishing a tool — finishing work does not imply permission to push.

**How to apply:** After completing and committing a change, stop and report; do not run `git push` on your own initiative. Wait for the user to say push (e.g. "푸시해", "push"). When they do, follow [[push-target-dnable-dev]] for the target and [[push-includes-tool-guide-docs]] for what to include.
