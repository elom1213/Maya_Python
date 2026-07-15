---
title: Portfolio — Work Summary (2026-05-06 ~ 2026-07-15)
aliases: [Portfolio EN]
tags: [portfolio, technical-artist, pipeline, unreal, metahuman]
updated: 2026-07-15
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
> - I automate the **Maya → Unreal bridge** by generating engine node text: rig data from Maya (joints, constraints, object arrays) becomes Control Rig / KawaiiPhysics nodes you literally **paste into the graph with Ctrl+V**.
> - I build tools as a **pipeline, not as one-offs**: shared widgets, theming, path management, undo, drag-&-drop shelf install and a release builder — so a new tool ships in half a day.

---

## 1. MetaHuman · Facial / Correctives

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

---

## 3. Rigging automation (character rig · skinning · shapes)

| Tool | What it does |
|------|--------------|
| `A00145_RigConnect` | **Unified rig-connection tool**: absorbed two legacy MEL tools (ConnectionTool, Match Tool) into Qt. Match (T/R/S/Parent options), matrix constraints, connect-to-closest, **skin weight → constraint conversion** (Parent / Scale / Point / Orient), batch offset/zero-out group creation, **Constraint Transfer** (move an existing constraint onto another object, preserving world pose), and an **Attribute tab** that copies chosen attributes onto other objects with a prefix/suffix (type/range/default/keyable preserved) — including a blendShape's targets (see 1-4) |
| `A00270_skinMigrate` | One-click **skin weight transfer between meshes of different topology, with bone remapping**; the legacy two-button UI is preserved as a Classic tab |
| `A00060_jointTool_V02` | Legacy MEL JointTool folded into Qt: curve-based / divided joint creation in **world space**, twist-only Aim redesign, unused-joint selector |
| `A00120_FKIK`, `A00190_FKIK_General_Tool` | FK/IK switching and baking. Moved to native `bakeResults` for speed, then fixed to a constraint-free per-frame match bake so that **keys outside the range and anim-layer poses are no longer corrupted** |
| `A00130_ControlRig` | Control rig generation |
| `A00180_abSymMesh` | Legacy abSymMesh **re-implemented on OpenMaya** for speed: snap-to-symmetry, mirror deform, selected-vertices-only mode |
| `A00290_BSTool` | blendShape editing suite — a tab that **replaces Maya's native Shape Editor** (all targets listed, per-target edit toggle, live weight sync), Base Shape editing, per-frame shape copy |
| `A00170_driverTool`, `A00150_remapVal`, `A00160_sphericalEye` | Driven keys / remapValue (master node driving child remaps, sine-wave and slerp-ramp build modes), closest-point curve attach with even distribution, spherical eye rig (pupil dilation, converge-to-center) |

---

## 4. Animation tooling

`A00110_animTool`

- One window for the animator's repetitive work: key copy/paste (with axis reversal), **L/R controller key mirroring**, 6-axis pose keys, Offset & Hold, baking (including Smart bake), **Follow (target-match bake)**, and automatic Graph Editor framing (frames to current ± margin on selection).
- I analysed and documented the bake algorithms of the legacy MEL / SmartLayer tools, then **ported them onto native Maya APIs**, verifying result parity while gaining speed.

---

## 5. Modeling / asset QC · export

- **`A00300_meshDoctor`** — **read-only mesh diagnosis with safe one-click repair**. Detects non-manifold geometry, lamina faces, zero-area faces (judged by shape quality, not just area), n-gons, etc.; **batch-diagnoses many meshes into a colour-coded summary table**, and logs results to JSON/TXT.
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
