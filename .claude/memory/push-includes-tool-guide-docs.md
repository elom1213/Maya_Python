---
name: push-includes-tool-guide-docs
description: "when pushing, verify the tool's guide doc was updated and include it in the push"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2831d959-6cff-4286-92dd-dcac20de809b
---

When asked to push a tool's changes, first check whether that tool's guide/explanation doc under `JUN_All/docs/<tool>.md` reflects the change; if it's stale, update it, then include it in the commit/push along with CHANGELOG, version, and WORKLOG.

**Why:** The user keeps per-tool guide docs in `JUN_All/docs/` (see [[docs-go-in-jun-all-docs]]) and wants them to stay in sync with the code, not drift behind.

**How to apply:** Before any tool push: (1) update CHANGELOG + version bump, (2) update `JUN_All/docs/WORKLOG.md` (see [[worklog-maintenance]]), (3) check/refresh `JUN_All/docs/<tool>.md` guide doc, (4) stage all of these together with the code. Default push target is [[push-target-dnable-dev]].
