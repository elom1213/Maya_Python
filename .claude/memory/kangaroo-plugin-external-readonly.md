---
name: kangaroo-plugin-external-readonly
description: "kangaroo Maya plugin is an external read-only reference, not part of this repo — never modify it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 67f36f12-b669-4c14-94ed-e1c1529c6b41
---

The "kangaroo" Maya plugin lives OUTSIDE this repo at `C:\Users\USER\Desktop\JP\0020_maya_plugin\0010_kangaroo`. It is a third-party/external rigging plugin the user uses (SkinCluster › Transfer, etc.). Treat it as **read-only reference only** — read its source to understand behavior, but **never modify kangaroo files**. When a problem could be solved by changing kangaroo, instead guide the user (UI options/workflow) or solve it in our own JUN_All tools.

**Why:** User explicitly said "kangaroo 툴을 직접 수정하지는 말고 안내만 해줘" while diagnosing a mesh that broke kangaroo's weight Transfer.

**How to apply:** For kangaroo-related issues, output guidance + document it in our tool docs (e.g. [[metahuman-cloth-corrective-A00280]] style docs under JUN_All/docs). Verified fact found in source: kangaroo Transfer `closestVertex`/`closestUV` modes (weights.py:2073) do direct vertex-weight assignment with NO barycentric face math, so they bypass zero-area/non-manifold/lamina corruption without modifying the mesh.
