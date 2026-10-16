---
name: euler-closest-solution-not-equivalent
description: om2 MEulerRotation.setToClosestSolution can return a DIFFERENT rotation near gimbal; use setToClosestCut on euler + alternateSolution and check asMatrix
metadata:
  node_type: memory
  type: feedback
  originSessionId: 65d65d23-f886-438a-972a-303242df429d
  modified: 2026-10-16T02:56:39.341Z
---

`MEulerRotation.setToClosestSolution(target)` is **not** guaranteed to keep the rotation.
Measured (mayapy 2024): decompose(Ry90 x Rx45, XYZ) = (90,45,90) ✓, then closestSolution toward
(45,90,0) → (22.5,45,22.5) — a different orientation. `setToClosestCut` (only 360° shifts) and
`alternateSolution()` stay equivalent.

**Why:** found while fixing A00060 V03 Orient / Rotate (v03.15); random tests passed but the 0/90
combo failed. Also: Euler angles never add per axis — rotate+jointOrient must be composed as
`R x JO` (row vectors, local = [RA][R][JO]).

**How to apply:** to pick "the nicest equivalent Euler", try `{e, e.alternateSolution()}` each with
`setToClosestCut(target)`, keep only those whose `asMatrix().isEquivalent(M)`, take the nearest.
Always include gimbal (0/±90/180) combos in tests, not just random angles. Related: [[wip-a00060-v03-tab-reorg]]
