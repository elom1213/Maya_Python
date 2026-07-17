---
name: wip-a00170-stretch-tab
description: A00170 Stretch tab — additive stretch driver (linear + sigmoid w/ live scene-attr control, multi-attr) from ref_01_StretchTool.mel (DONE, Maya-verified + pushed v01.11)
metadata: 
  node_type: memory
  type: project
  originSessionId: c3545ac1-18bb-4331-aaa2-bfc6fc5af398
---

A00170_driverTool v01.09 — new **Stretch** tab (4th tab; `stc_*` prefix), core `app/core/stretch.py` `run_build_stretch`. Ported + refactored from `ref/ref_01_StretchTool.mel` (Stretch feature only; the MEL's Distance tab / distanceDimension was NOT ported).

**What it does**: Default Distance object's attr (value `a`, snapshot at build) drives a Stretch object's attr via a **set driven key** (animCurveUU) with 2 linear-tangent keys + user pre/post infinity. Default 1 → 1:n, else n:n. Functions: `f(x)=x-a+1` (slope +1) or `f(x)=-x+a+1` (slope -1), both through `(a,1)`.

**Additive offset (v01.09)**: the curve is NOT wired straight to the attr (that overwrote it). An `addDoubleLinear` node is inserted between — `curve.output → input1`, `input2 = original - 1` → `driven = original + (x-a)`. So the attr keeps its **original value at rest** and grows/shrinks from there (e.g. translateX originally 1.5 stays 1.5 at rest). `original` is getAttr-snapshotted BEFORE keying (after connection it's driven). setInfinity runs while the curve is still directly on the plug (setInfinity needs a plug target, not the curve node), THEN the disconnect/insert surgery runs — infinity persists on the curve. Compound driven attrs (translate) skipped (non-scalar) before any partial keying. `run_build_stretch` returns `(driver_plug, driven_plug, a, original, offset_node)` per pair.

**Sigmoid functions (v01.10)**: Function combo gains `Sigmoid`/`Sigmoid rev`. Built as an **analytic node network** (NOT animCurveUU) — user said any nodes are fine. `driven = tmin + (tmax-tmin)/(1 + base^(±(x-a)+L))` via `multiplyDivide` op=3 (power, base^exp) + op=2 (divide) + addDoubleLinear/multDoubleLinear. Requested spec: x→-∞ converges to threshold_max, x→+∞ to threshold_min (≥0 so driven never <0), a reversed variant, user-set base (the "e" in 1/(1+e^-x)) + thresholds, AND (added mid-task) **sigmoid(a) = the Stretch attr's original value**. That last condition is met by the horizontal shift `L = log_base((tmax-original)/(original-tmin))` → plateaus are the LITERAL thresholds and the curve passes through `(a, original)`. Requires `threshold_min < original < threshold_max` (else that pair is skipped + WARN); base>1 and tmax>tmin raise ValueError. UI: Sharpness(base, default e)/Thresh Min/Max spinboxes, sigmoid-only (infinity combos are linear-only; `_stc_sync_func_enabled` toggles). `multiplyDivide` power is overflow-safe in Maya (base^huge → inf → span/inf → 0 plateau). Defaults tmin=0, tmax=2 (so scale~1 / small translate fits).

**v01.11 — multi-attr + live sigmoid control + search-select-all**: ① Stretch **Attributes TSL is multi-select** (`multi_attr=True`); pairing (1:n / n:n object pairing × selected attrs) is expanded in the UI and `build_stretch` just does an index-aligned `zip` (dropped its internal 1:n logic). ② Sigmoid `base`/`tmin`/`tmax` become **live keyable attrs on the driver (Default Distance) object** (`stretchSharpness`/`stretchThreshMin`/`stretchThreshMax`, default=UI value, one set per driver object, shared+cached), wired into the network → tweak the sigmoid live in the scene. Made possible by rewriting the sigmoid to `driven = tmin + (tmax-tmin)/(1 + ratio·base^(±(x-a)))` with `ratio = (tmax-original)/(original-tmin) = base^L` — **no log node**, so base/tmin/tmax can be live and `driven(a)=original` still holds exactly (only `a`, `original`, `factor` stay baked). ③ Attr Search re-query now `select_by_texts(all found)` (multi TSL selects all; single selects first). Verified headless: multi-attr sigmoid+linear, live tmax change retargets all networks while each keeps its own original at rest.

**Refactor/bugfixes over the MEL**: ① pre/post infinity both user-settable (MEL fixed post=Cycle-w/-Offset, pre=Constant). ② tangents auto→linear. ③ 2nd key `2a`→`a+1` so it's actually `f(x)=x-a+1` (MEL slope was `1/a`), killing `a=0` (coincident key inputs) / `a<0` (slope sign flip) breakage. ④ two `setDrivenKeyframe` calls build the curve directly (dropped `connectionInfo` re-lookup). ⑤ existence/self-drive/scalar input validation.

**Verified facts (headless mayapy 2024)** — see [[mayapy-headless-verify]]:
- `setInfinity` applies only when the target is the **driven plug (obj.attr)**, NOT the animCurve node; string `cycleRelative` = "Cycle with offset".
- setAttr enum for `.preInfinity`/`.postInfinity`: `{Constant:0, Linear:1, Cycle:3, Cycle with offset:4}` (2 is a gap → Constant). MEL's `4` was correct.
- animCurveUU driver axis is queried with `keyframe -q -fc` (floatChange), not `-tc`.
- linear tangents + cycleRelative both sides → `f(x)=x-a+1`/`-x+a+1` exact across full range. 1:n / n:n / validation all pass.

**Status**: DONE — v01.09 additive, v01.10 sigmoid, v01.11 (multi-attr + live scene-attr sigmoid control + search-select-all + per-function param UI toggle w/ container boxes so labels gray too) all **Maya-confirmed by user + pushed** ([[push-target-dnable-dev]], [[push-includes-tool-guide-docs]] — guide `docs/A00170_driverTool.md`, version.py 01.11, WORKLOG updated). See [[wip-a00170-attachcrv-tab]] for the sibling tab pattern.
