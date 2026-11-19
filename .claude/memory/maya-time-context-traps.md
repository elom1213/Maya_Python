---
name: maya-time-context-traps
description: Maya traps found 2026-11-19 - getAttr -time worldMatrix can return stale values after the node's own curve changes; currentTime(update=False)+plug read is stale; doNotWrite nodes still write the plugin requires line
metadata:
  type: reference
---

Measured in mayapy 2024 while building [[wip-a00630-motion-path]]:

1. **`cmds.getAttr(node + ".worldMatrix[0]", time=t)` can be stale.** Once evaluated at time t, editing the node's *own*
   translate curve (or undoing it) still returns the old matrix; `cmds.dgdirty(allPlugs=True)` does not clear it.
   `getAttr -time` of the translate plug itself was fresh. → For a trustworthy reference value, step time and read
   `xform -q -ws -rp` (turn undo off while stepping so tests' undo order is untouched).
2. **`cmds.currentTime(t, update=False)` + `plug.asMObject()` returns stale upstream values** (off by 20 units in a
   constrained hierarchy) although it is ~20x faster. Use `om.MDGContext(MTime(t)).makeCurrent()` (restore the previous
   context in `finally`); API 2.0 has no `MDGContextGuard`, and `asMObject(ctx)` is deprecated.
3. **Any node of a plugin type in the scene makes the saved file `requires` that plugin**, even with
   `setDoNotWrite(True)` and `pluginInfo -edit -writeRequires false`. Delete such helper nodes in a `kBeforeSave`
   callback and recreate them in `kAfterSave`.
4. Rotate pivot world position = `(rotatePivot + rotatePivotTranslate + translate) · parentMatrix` — not
   `rotatePivot · worldMatrix` (wrong once scale ≠ 1).

5. **Anim layer blend:** each layer adds `animBlendNodeAdditiveDL`; `output = weightA*inputA + weightB*inputB`
   (additive 1 / w, override 1-w / w, mute 1 / 0). `setKeyframe -animLayer` *without* value keeps the final value per key
   (on override layers that bends a curve that should be constant).
6. **Undo of a newly created layer curve leaves stale evaluation** downstream of the blend chain (even when stepping time);
   data is correct. `cmds.dgdirty(target + blend nodes)` fixes it; a marker MPxCommand first in the undo chunk does it on undo.

Related: [[mayapy-headless-verify]] · [[parentmatrix-includes-offsetparentmatrix]]
