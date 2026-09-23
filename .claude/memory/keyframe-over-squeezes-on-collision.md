---
name: keyframe-over-squeezes-on-collision
description: "cmds.keyframe(edit, relative, option=\"over\") does not refuse a move onto an existing key — it squeezes the key to 19.9999f; pre-check collisions"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 137af4e5-6363-471e-8bc9-56275550acc2
  modified: 2026-09-23T01:21:49.535Z
---

`cmds.keyframe(crv, e=True, index=..., relative=True, timeChange=off, option="over")` lets keys
jump over unselected neighbours (default `option="move"` stops at the neighbour, so the offset is
not honoured). But when the destination frame already holds an **unselected** key, Maya does not
raise — it silently lands the key just before it (e.g. `19.999999829931973` next to `20.0`).
Verified with mayapy 2024 (A00110_V02 v02.17 Timing > Move selected-key mode).

**Why:** a fractional key right next to another one is invisible in the Graph Editor and breaks
later integer-frame tools; no error is ever shown.

**How to apply:** before an `over` move, compute `t + offset` for the moving keys and compare to the
unselected key times of the same curve (eps ~1e-3); skip/report that curve instead of moving it.
Related: [[wip-a00110-get-sel-range]]
