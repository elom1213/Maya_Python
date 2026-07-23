---
title: Portfolio — Work Summary (2026-05-06 ~ 2026-07-15)
aliases: [Portfolio EN]
tags: [portfolio, technical-artist, pipeline, unreal, metahuman]
updated: 2026-07-23
---

# Technical Artist / Pipeline TD — Work Summary (EN)

> **Author**: Ji Hun Park (Junny)
> **Period**: 2026-05-06 – 2026-07-15 (~10 weeks)
> **Scope**: Autodesk Maya tool development · Unreal Engine bridging · MetaHuman facial · pipeline infrastructure
> **Volume**: 299 commits · 40+ in-house tools · one shared framework powering all of them
> **Stack**: Python 3, `maya.cmds` / OpenMaya, PySide2 & PySide6 (Qt), PyInstaller, Unreal Engine (Control Rig / KawaiiPhysics / RBF Pose Driver), Houdini Alembic caches

---

## 0. One-liner / Three-liner (for the top of a résumé)

**One line**
> Technical Artist building the rigging & facial pipeline that connects Maya, Unreal Engine and MetaHuman — 40+ in-house tools and the shared framework behind them, built over 10 weeks.

**Three lines**
> - I focus on **removing artist repetition with tooling**: hundreds of manual passes (per-pose corrective matching, per-bone physics setup) collapsed into a single button.
> - I automate the **Maya → Unreal bridge** by generating engine node text: rig data from Maya (joints, constraints, object arrays) becomes Control Rig / KawaiiPhysics nodes you literally **paste into the graph with Ctrl+V**. Chained together, these converters carried a **Maya splineIK rig into Unreal and drove it with runtime physics** (see 2-4).
> - I build tools as a **pipeline, not as one-offs**: shared widgets, theming, path management, undo, drag-&-drop shelf install and a release builder — so a new tool ships in half a day.
> - I **author rig behaviour as tunable math functions**: chain twist and deformation shaped by linear/sigmoid functions (beating the splineIK up-vector limit; art-directable and live-tunable vs. matrix constraints) to build **tentacle and snake** rigs that **import into Unreal and animate exactly as intended**.

---

## 1. MetaHuman rig — Facial · Body RBF · Correctives

### 1-1. Per-joint garment wrinkle correctives via Unreal's Pose Driver (PoseWrangler)
`A00280_correctiveFromCache`

- **Problem**: Authoring cloth-wrinkle correctives for each joint (shoulder, elbow, knee…) meant hand-matching the garment to a Houdini cloth-sim cache in the Shape Editor, once per RBF pose — a **(poses × joints)** grind.
- **What I built**: A tool that reads the **Alembic cloth cache** from Houdini, snapshots the cached shape at each RBF pose frame, drives the rig to that pose, and computes the **pre-skin (bind-space) delta** through PoseWrangler's `invertShape` path — producing the corrective target and **auto-wiring it to the RBF solver output**.
- **Result**: The per-pose manual match became a **one-click batch**. It ships with left/right mirroring, a "skip if max delta < threshold" no-wrinkle filter, skip/overwrite policy for existing targets, and pose→frame step mapping; the whole run is a single undo.
- **Keywords**: MetaHuman, PoseWrangler / RBF Pose Driver, corrective blendshape, `invertShape`, Alembic, Houdini cloth sim

### 1-2. MetaHuman facial RBF connection automation
`A00090_ConnectionBuilder`

- Automates the **RBF solver → driver node → blendshape** attribute wiring of a MetaHuman facial rig, driven by **JSON rule files**.
- Supports **1→n and n→n batch connection** from source/target lists, routing through intermediate nodes (`WRK_intermediate`), plus `validate` and `disconnect` passes.
- Hundreds of hand-made attribute connections became **reproducible and verifiable** data.

### 1-3. MetaHuman facial data utilities
`A00100_jsonEditor_MH`, `A00200_CSV_tool`, `A00320_ARKitCurveTool`

- **jsonEditor_MH** — sorts/edits MetaHuman facial definition JSON; keeps RBF solver settings (interpolation, normalization) as data.
- **CSV_tool** — imports ARKit facial capture CSV into Maya as animation curves.
- **ARKitCurveTool** — reverse-engineered Unreal's `Add ARKit Curves to Skeleton` and reproduced the same result on the Maya side (code + guide).

### 1-4. Facial control authoring — blendShape targets → controller attributes
`A00145_RigConnect` (Attribute tab)

- A blendShape's targets are not plain attributes — they live as **aliases on a `weight[]` multi**, so the usual attribute listing only surfaces the first one. I read them straight from `aliasAttr`, so **selecting a blendShape lists every target by name** in both the Attribute and Connect tabs.
- Chosen targets are **copied onto a controller as named, keyable float attributes** (optional prefix/suffix, type/range/default preserved); the Connect tab then wires **controller → blendShape target**.
- Turns "expose these dozens of face shapes as rig controls" into a pick-and-copy step instead of hand-adding attributes and connections one at a time — the everyday grind of building a facial control rig.

### 1-5. Generalizing the MetaHuman skeleton + Unreal RBF setup to non-MetaHuman avatars
`A00270_skinMigrate`, `A00130_ControlRig`, `A00060_jointTool_V02`, `A00145_RigConnect`, `A00090_ConnectionBuilder`

- **Goal**: take the rig approach proven on MetaHuman — its **bone structure** and the **Unreal RBF (PoseWrangler) pose-driver** setup — and stand it up on **other avatars, both realistic and cartoon-style**, all the way into Unreal.
- Because these scripts are **selection- and JSON-rule-driven rather than hardcoded to MetaHuman**, the same pipeline retargets to an arbitrary character:
  - **Skeleton onto the custom mesh** — build and orient the joint structure (`A00060_jointTool_V02`, region-matched with `A00130_ControlRig`) and transfer skin across differing topology with **bone remapping** (`A00270_skinMigrate`).
  - **Rig plumbing** — match / constrain / attribute-copy / connect-closest to align the new rig to the reference (`A00145_RigConnect`).
  - **Body / joint RBF** — wire the **RBF solver → driver → corrective** attributes from source/target lists through JSON rules (`A00090_ConnectionBuilder`); its shipped rules are **body-limb** correctives (`WRK_thigh / calf / lowerarm_l/r`), i.e. the same RBF wiring **reused well beyond MetaHuman faces**.
  - **Into Unreal** — author the RBF pose-driver in engine with **PoseWrangler**, so the pose-driven deformation runs live on the target skeleton in-engine.
- **Result**: MetaHuman-grade **pose-driven deformation (RBF)** became **repeatable on non-MetaHuman realistic and cartoon avatars**, without writing an engine plugin or hand-rebuilding each RBF setup per character.
- **Keywords**: RBF Pose Driver, PoseWrangler, skeleton retarget, cross-topology skin transfer, Control Rig, avatar-agnostic rig pipeline, Maya → Unreal

---

## 2. Unreal Engine node generators (Maya → UE bridge)

> Shared idea: Unreal graph nodes can be **copied and pasted as text**.
> So I read the rig data out of the Maya scene, **generate the Unreal node text, copy it to the clipboard, and Ctrl+V it into the UE graph** — dozens or hundreds of nodes appear at once, with correct values and layout. Three converters were built on this principle.

### 2-1. Maya joints → Unreal KawaiiPhysics converter
`A00080_KWI_creator` (V01 → V02 standalone → **V03 in-Maya**)

- Takes a list of **target root bones** selected in Maya and generates one **KawaiiPhysics AnimGraph node set** (base / settings / LOD) per bone via template substitution, including automatic node placement in the graph.
- **Constraints tab**: generates the contents of a KawaiiPhysics **Bone Constraints Data Asset** — filtering to bone pairs that actually exist in the scene, with zero-padded indices so it drops straight into the asset.
- **Evolution**: the generation core stayed untouched while the UI moved from a standalone Qt app to an in-Maya PySide tool, and the bone list moved from a source file to **live Maya selection**. A concrete payoff of the core/ui separation.
- **Result**: per-bone secondary-motion setup for hair, cloth and accessories became "hand it the bone list".

### 2-2. Maya constraints → Unreal Control Rig constraints converter
`A00260_ConstraintConverter`

- Reads the **constraints in the Maya scene** (type, targets, weights) and emits **Control Rig Parent / Position / Rotation Constraint node** text.
- Supports per-axis filtering (translate/rotate channels), collapsed node output, **automatic horizontal layout** (wrapping every 4 nodes) and **ExecutePin wiring between nodes (RigVMLink)** — so the pasted graph is runnable immediately.
- **Result**: constraint relationships validated in Maya no longer have to be rebuilt by hand in Unreal.

### 2-3. Maya objects → Unreal Control Rig Item Array converter
`A00350_ArrayCreator`

- Turns a list of Maya objects, in order, into an Unreal Control Rig **Item Array node (`TArray<FRigElementKey>`)** and copies it to the clipboard.
- Element type is selectable (Bone / Control / Null / Curve / Socket …) and the order is editable (Up / Down / **Reverse**). The Reverse action — for when you picked a chain tip-to-root — was implemented **in the shared list widget**, so every other tool inherits it.

### 2-4. 【Case study】 Porting a Maya splineIK setup into Unreal, driven by runtime physics
`A00350_ArrayCreator` + `A00260_ConstraintConverter` + `A00145_RigConnect`

> A real production case where the converters above were **chained into one pipeline** rather than used individually.
> The goal: take a splineIK rig authored in Maya and make it **come alive under physics in Unreal**.

- **Problem**: a joint chain **whose two end points must stay pinned at all times** had to swing in Unreal. Putting physics (KawaiiPhysics / Physics Asset) directly on the chain bones **releases those end points**, so the motion is wrong. On top of that, rebuilding the Maya splineIK behaviour by hand in-engine is expensive.
- **Approach — move what physics simulates from the chain onto the curve's control points**
  1. **In Maya**: built the joint chain and the **splineIK curve** that drives it, then created **one joint at each of the curve's control vertex positions** (**CV joints**). Physics then acts on **a handful of CV joints instead of the whole chain**, so **pinning the two end CVs structurally guarantees the pinned end points**.
  2. **Attaching the CV joints**: rather than eyeballing what each CV should follow, I constrained them using **`A00145_RigConnect`'s Skin Weight to Constraint** — **deriving the attachment targets and weights straight from the skin weights**, so each CV rides the bones the mesh actually follows.
  3. **Into Unreal — data transfer**: **`A00350_ArrayCreator`** emitted the joint chain and the CV joint list as **Control Rig Item Array node text** (the ordered bone arrays the splineIK node needs), and **`A00260_ConstraintConverter`** converted the **constraints on the CV joints into Control Rig constraint nodes**. Nothing validated in Maya had to be re-wired by hand in-engine.
  4. **In Unreal — driving it**: **KawaiiPhysics / a Physics Asset** makes the CV joints swing, and a **splineIK setup in Control Rig** makes the **joint chain bend to follow those CV joints**.
- **Result**: the splineIK behaviour authored in Maya **runs as live physics in Unreal while both ends stay pinned**. It is **in-engine simulation, not baked animation**, so it reacts to any motion.
- **Why it matters**: three self-built tools (**item array generation · constraint conversion · skin-weight-to-constraint**) combined to complete the path from **Maya rig data → Unreal Control Rig + physics** with **no manual rebuild**.

```
[Maya]                                       [Unreal]
 joint chain ─┐                               joint chain (same skeleton)
              │ splineIK                          ▲  splineIK (Control Rig)
 splineIK crv ┘                                   │
      │ control vertex positions                 CV joints
      ▼                                           ▲  KawaiiPhysics / Physics Asset
  CV joints ── A00145 Skin Weight to Constraint ──┤   (end CVs pinned → ends stay fixed)
      │                                           │
      └── A00350 Item Array ──────────────────────┤  ← chain / CV bone array text
      └── A00260 Constraint Converter ────────────┘  ← constraint-relationship node text
```

- **Keywords**: splineIK, Control Rig, KawaiiPhysics, Physics Asset, runtime secondary motion, both-ends-pinned chain, skin-weight-driven attachment, Maya → Unreal rig data conversion

---

## 3. Rigging automation (character rig · skinning · shapes)

### 3-1. Function-driven twist & deform rig asset — built with `A00170_driverTool`

Not just the tool — I stood up real rig assets with it, such as **tentacle and snake** rigs.

- **Idea — shaping a driver like signal processing**: a hierarchy of **driver nulls whose Translate / Rotate / Scale attributes are shaped by a chosen math function, as if processing a signal**. The drivers feed a joint chain, so the chain's deformation is expressed **per-function and additively (layered)**. The Stretch tab builds the linear/sigmoid function as a driven network and lays its output **additively on top of the original value**, so several functions can be **stacked on one chain** to compose complex behaviour.
- **Chain twist — beating the splineIK limit**: the function specifies **how much twist is distributed from the root to the tip** of the chain. This overcomes the classic **splineIK limitation** — a single up-vector can't cleanly deliver progressive/large twist along the whole span — by distributing twist through the function instead. Especially effective for **long, coiling, twisting** rigs like tentacles and snakes.
- **Edge over matrix constraints**: unlike a matrix (offsetParentMatrix) setup that rigidly copies/constrains a transform, here the **shape of how the value propagates along the chain is authored as a function**. The sigmoid carries convergence thresholds (upper/lower plateaus, never dropping below 0) and a sharpness, and those parameters are **exposed as scene attributes on the driver object**, so the falloff can be **tuned and animated live in the scene without rebuilding the rig**. The result is deformation that is **art-directable, layerable and live-tunable** rather than a rigid constraint.
- **Unreal-import ready — plays as intended**: the setup drives a **real joint chain**, not Maya-only constructs, so the resulting skeletal animation **imports into Unreal and plays exactly as intended**. (It isn't ported to a live Control Rig, but the driver function network **bakes down to joint/skeleton animation**, so it stays alive in-engine.) An **engine-ready** rig from a game-pipeline standpoint.

```
Default Distance attribute (driver signal x)
        │  A00170 Stretch:  f(x) = linear / sigmoid (threshold & sharpness = scene attrs)
        ▼
  driver null hierarchy  (T / R / S,  additive over the original value)
   null_0 -> null_1 -> null_2 -> ... -> null_n   <- functions stack (layered)
        │  drives
        ▼
  joint chain  jnt_0 -> jnt_1 -> ... -> jnt_n     -> progressive root->tip twist (beats splineIK up-vector)
        │  bake to FBX skeletal animation
        ▼
  Unreal:  import -> animates as intended (engine-ready)
```

- **Keywords**: driven-function rig, additive function layering, chain twist distribution, beating the splineIK up-vector limit, sigmoid falloff, live attribute control, vs. matrix constraints, tentacle/snake rig, Unreal-import ready

### 3-2. Rigging tool list

| Tool | What it does |
|------|--------------|
| `A00145_RigConnect` | **Unified rig-connection tool**: absorbed two legacy MEL tools (ConnectionTool, Match Tool) into Qt. Match (T/R/S/Parent options), matrix constraints, connect-to-closest, **skin weight → constraint conversion** (Parent / Scale / Point / Orient), batch offset/zero-out group creation, **Constraint Transfer** (move an existing constraint onto another object, preserving world pose), and an **Attribute tab** that copies chosen attributes onto other objects with a prefix/suffix (type/range/default/keyable preserved) — including a blendShape's targets (see 1-4) |
| `A00270_skinMigrate` | One-click **skin weight transfer between meshes of different topology, with bone remapping**; the legacy two-button UI is preserved as a Classic tab |
| `A00275_skinTool_V01` | The above plus **Update Bind Pose** (a capability Maya lacks, see 3-3) and a **Transfer tab** (weights from many source meshes → the selected mesh, **restricted to selected vertices with soft-selection falloff**, no third-party plugin) |
| `A00060_jointTool_V02` | Legacy MEL JointTool folded into Qt: curve-based / divided joint creation in **world space**, twist-only Aim redesign, unused-joint selector |
| `A00120_FKIK`, `A00190_FKIK_General_Tool` | FK/IK switching and baking. Moved to native `bakeResults` for speed, then fixed to a constraint-free per-frame match bake so that **keys outside the range and anim-layer poses are no longer corrupted** |
| `A00130_ControlRig` | Control rig generation |
| `A00180_abSymMesh` | Legacy abSymMesh **re-implemented on OpenMaya** for speed: snap-to-symmetry, mirror deform, selected-vertices-only mode |
| `A00290_BSTool` | blendShape editing suite — a tab that **replaces Maya's native Shape Editor** (all targets listed, per-target edit toggle, live weight sync, **range/multi-select to drive many weights at once**, **editing keyed targets** so Auto Keyframe records keys, gesture-level undo), Base Shape editing, per-frame shape copy |
| `A00170_driverTool`, `A00150_remapVal`, `A00160_sphericalEye` | **Function-driven stretch** (linear/sigmoid functions as a driven network, laid additively over the original value; sigmoid thresholds & sharpness exposed as **live scene attributes on the driver object** — see 3-1), driven keys / remapValue (master node driving child remaps, sine-wave and slerp-ramp build modes), closest-point curve attach with even distribution, spherical eye rig (pupil dilation, converge-to-center) |

### 3-3. Update Bind Pose — implementing a missing Maya capability by working the deformer graph directly
`A00275_skinTool_V01`

- **Problem**: once a mesh is bound, moving or rotating joints deforms it — but **Maya has no way to
  freeze that state as the new bind pose**. `Go to Bind Pose` always returns to the original one.
- **Confirmed there is no native route**, by measurement: `skinCluster -e -recacheBindMatrices` does not
  touch `bindPreMatrix` at all, and `dagPose -reset` does not update the bind pose.
  `Move Skinned Joints Tool` solves a different problem ("move joints without deforming the mesh").
- **What I built**: a three-step operation on the skin deformer graph — ① set each influence's
  `bindPreMatrix` to its current `worldInverseMatrix`, ② bake the `skinCluster output − input` delta into
  the **input shape at the head of the deformer chain**, and ③ rebuild the `bindPose` (dagPose) node and
  reconnect it. Because a blendShape adds static deltas — a **linear** operation where
  `f(orig+d) = f(orig)+d` — this works **with the blendShape either before or after the skin, preserving
  the existing history**.
- **Made failures diagnosable on real rigs**: on a 22,644-vertex facial mesh the input-shape search stopped
  at a **chain of 13 `groupParts` nodes**; deformers expose `input[i].inputGeometry` while `groupParts`
  exposes a scalar `inputGeometry`. Alongside the fix I added a **read-only Diagnose report** that prints
  the deformer chain exactly as connected, so a user can see where it stops.
- **Where correctness had to be exact**: `bindPreMatrix` indices must be read from the `matrix[]`
  connections, **not** from the order of `skinCluster -q -inf` — on a rig whose influences were removed and
  re-added the indices are sparse, so enumerating them **writes matrices into the wrong joint slots and
  looks like a double transform**. And baking with `MFnMesh.setPoints` leaves the scene inconsistent after
  Ctrl+Z because it never enters the undo queue, so the bake goes through a ranged `setAttr` on `pnts`.
  I also measured that a still-live blendShape target **cancels the baked offset in proportion to its
  weight**, and surfaced that as a warning with the actual values.
- **Keywords**: skinCluster, `bindPreMatrix`, dagPose, deformer graph traversal, OpenMaya, undo safety

---

## 4. Animation tooling

`A00110_animTool`

- One window for the animator's repetitive work: key copy/paste (with axis reversal), **L/R controller key mirroring**, 6-axis pose keys, Offset & Hold, baking (including Smart bake), **Follow (target-match bake)**, and automatic Graph Editor framing (frames to current ± margin on selection).
- I analysed and documented the bake algorithms of the legacy MEL / SmartLayer tools, then **ported them onto native Maya APIs**, verifying result parity while gaining speed.
- **Stagger Offset — authoring follow-through / wave motion with a slider**: shifts the listed controllers' keys inside a chosen frame range by **list order × N frames**, producing the delayed, trailing motion of tails, hair and cloth. The value is **adjusted live with a slider** and is **never cumulative** (always recomputed from the original positions).
  - **Live editing and Undo made to coexist**: nothing is written to the undo queue while dragging (so it doesn't fill with hundreds of entries); the moment the input **settles**, the result is committed as **a single entry**. Because undo *applies a command's inverse to the current state*, the tool always rewinds to the last committed state before recording — so **one Ctrl+Z lands exactly where the user started**.
  - Keys are moved with **relative moves only**, never by rebuilding the curve, so **tangents, infinity and anim-layer membership survive**. It even detects the case where the user hits Undo in the scene and the session's assumptions go stale, via a **probe key**, rather than corrupting the timing.
  - The behaviour is covered by **59 headless (mayapy) scenarios** — non-cumulative edits, keys outside the range, tangent preservation, undo restoration.

---

## 5. Modeling / asset QC · export

- **`A00300_meshDoctor`** — **read-only mesh diagnosis with safe one-click repair**. Detects non-manifold geometry, lamina faces, zero-area faces (judged by shape quality, not just area), n-gons, etc.; **batch-diagnoses many meshes into a colour-coded summary table**, and logs results to JSON/TXT.
- **`A00380_MeshTool`** — **inflates / shrinks a mesh along its vertex normals** (the equivalent of Houdini's `peak` node), with a live slider preview, Range/Step controls for fine adjustment, and **soft-selection falloff** support. Maya's native route (Move tool with `axis = normal`) issues one command per vertex and is slow; writing **`shape.pnts` in one ranged `setAttr`** instead cut **19,462 vertices from ~7.2 s to 0.10 s (~70x)**. The real behaviour of Maya's tweak and undo stack was verified headlessly with `mayapy`, so the **slider adjustment is itself the committed result** (no separate Apply button) and each stroke **reverts precisely with a single Ctrl+Z**.
- **`A00040_file_exporter_V02`** — export automation: type filters (applied through group hierarchies), referenced-mesh handling, and a choice of flattening to scene root or preserving hierarchy.
- **`A00050_uvTool`**, **`A00030_quickTool`**, **`A00330_NamingTool`** (legacy naming tool port + Quick Rename), **`A00310_SearchTool`** (select by type/name), **`A00360_SortTool`** (sort by world X/Y/Z, name or type and reorder the Outliner).

---

## 6. Pipeline infrastructure & shared framework (the tool that makes tools)

I designed the common foundation alongside the tools, not as an afterthought.

- **Shared Framework**
  - Reusable widgets (lists, buttons, combos) and **14 colour themes (qss)** unified across 21 Qt tools.
  - **UUID-backed object lists** — list↔scene selection survives duplicate names, renames and reparenting; rolled into the shared widget and inherited by 18 tools at once.
  - A shared `undo_chunk` convention so repeated scene edits collapse into **a single Ctrl+Z**.
  - `PathManager` (read/write path separation), Maya main-window parenting, module reloader.
- **Deployment / install system**
  - **Drag-&-drop shelf install** — drop a `.py` onto the Maya viewport and an icon shelf button appears. Solved the `sys.modules` cache collision between tools with a per-tool unique install-file convention.
  - **PyInstaller `.exe` builds**, a release builder (tool + framework + docs packaged automatically), and Windows taskbar icon handling.
- **Standalone pipeline utilities**
  - `A00210_FileManager` — file/version manager that **visualises file reference relationships as a node graph (Lineage)**, switches between Remote (Git) and Local (NAS) source modes, captures and recreates folder structures, and records thumbnails and logs. (`A00211_RefLineage` exports a Maya scene's reference graph straight into it.)
  - `A00220_BackupTool` — periodic and on-save **automatic backup** of watched files (crash insurance).
  - `A00240_PathTool` · `A00370_ToolLauncher` · `A00230_StartupTool` — launch frequently used folders/tools from buttons and profiles, auto-start them on Windows login, and **re-map paths automatically when the workstation changes**.
- **Documentation** — every tool carries a usage guide, a CHANGELOG and a version file, backed by a daily WORKLOG.

---

## 7. What I want this work to say

1. **Cross-DCC problem solving.** Maya, Unreal and Houdini caches are stitched into one flow. Generating Unreal node text in particular proved to be a pragmatic way to automate large graph setups **without writing an engine plugin**.
2. **Modernising legacy assets.** Scattered MEL and single-file scripts were analysed, consolidated into Qt tools, verified for behavioural parity, and documented.
3. **Artist-first design.** A tool lives or dies at its UI: always-on-top pins, collapsible sections, sorting/search, colour customisation and undo safety were iterated on repeatedly because that is where artists' hands actually land.
4. **Reusable structure.** Because logic (core) and UI are kept apart, moving the KWI Creator from a standalone app into Maya reused the generation core untouched.

---

## 8. Docs · repository

- Per-tool guides: `JUN_All/docs/`
- Work journal: `JUN_All/docs/WORKLOG.md`
- Repository map and architecture overview: root `README.md`
