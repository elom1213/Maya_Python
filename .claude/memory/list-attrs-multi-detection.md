---
name: list-attrs-multi-detection
description: "detect multi attributes with attributeQuery(multi=True), never getNextFreeMultiIndex on every attr (spams \"No object matches name\")"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c3545ac1-18bb-4331-aaa2-bfc6fc5af398
---

To test whether an attribute is a multi/array attribute, use `cmds.attributeQuery(attr, node=obj, multi=True)` (silent). Do NOT call `mel.eval('getNextFreeMultiIndex("obj.attr", 0)')` on every attribute to probe multi-ness: for non-multi (scalar) attrs that MEL proc tries `attr[0]`, fails, and prints `getNextFreeMultiIndex.mel line 41: No object matches name: obj.attr[0]` — one error PER attribute (a locator alone → ~215 errors). Catching the Python exception does NOT suppress the printed Maya error.

**Pattern**: `attributeQuery(multi=True)` first; only when it's a confirmed multi call `getNextFreeMultiIndex` to expand children (`listAttr("obj.attr[idx]", multi=True)`, fall back to `[attr]` if empty). Result set is identical, error spam gone.

**Why**: this `list_attrs` helper is shared/duplicated across tools' "List Attributes" buttons — fixed in `A00170_driverTool/app/core/maya_scene.py` (v01.12) and `A00145_RigConnect/app/core/connect_manager.py` (v01.18, keeps its blendShape-weight alias handling). If another tool copies this list_attrs pattern, apply the same fix. Verify with [[mayapy-headless-verify]]. Related: [[a00145-attribute-tab-blendshape-alias]].
