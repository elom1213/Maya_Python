---
name: push-target-dnable-dev
description: "Default git push target for this repo — Dnable_repo remote, dev branch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 67ba8ba1-3d8e-4ba5-9cc0-f842b752b6e2
---

When pushing this repo, push to the `Dnable_repo` remote (https://github.com/elom1213/JUN_Dnable.git), `dev` branch. Do NOT push to `origin` (Maya_Python.git) unless explicitly asked.

The `Dnable` branch is the main/master-role branch on `Dnable_repo`. **Do NOT merge into or push to `Dnable` until the user explicitly says so.** All routine work goes through `dev`.

**Why:** The user confirmed Dnable_repo/dev is their working push target across all sessions, not just one task. They reserve `Dnable` (the master-role branch) for deliberate, user-initiated releases.

**How to apply:** Default to `git push Dnable_repo dev` (the local `dev` branch already tracks `Dnable_repo/dev`). Never run `git merge dev` on `Dnable`, `git checkout Dnable` to push, or `git push Dnable_repo Dnable` on your own initiative — only when the user explicitly requests it. Use `origin` only when explicitly asked.
