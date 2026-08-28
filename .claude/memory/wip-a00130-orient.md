---
name: wip-a00130-orient
description: A00130_ControlRig_V02 Orient 단계 — 규칙 A1/A2/A3 가 결국 한 계산(aim+up hint). 부모를 돌리면 후손이 전부 딸려 움직이고, forward 를 맞추면 up 은 직교화만큼 기운다 (v02.04)
metadata:
  type: project
---

**`A00130_ControlRig_V02` 의 `Orient` 단계** (v02.04, 2026-08-28) — 사람이 템플릿 조인트를
놓은 뒤 **방향을 규칙대로 잡는다.** `app/core/orient_manager.py` · `orient_map.json`.
계획서: `JUN_All/docs/plans/A00130_ControlRig_V02_orient_plan.md`.
관련: [[wip-a00130-v02-match]] · [[wip-a00130-ik-session]] · [[wip-a00130-length-values]].

**규칙 셋이 결국 한 계산이다** — "forward 축을 다음 조인트로 aim 하고 up 축을 힌트 쪽으로".
힌트가 **폴 타깃**(A2)이냐 **월드 축**(A1 · 발 tail)이냐만 다르다.
코드가 아는 계산은 셋(aim 기저 · 월드 0 · 미러)이고 **조인트 이름은 전부 json 에** 있다.

**순서가 강제된다**: `미러 → A1 → A2(+tail/preserve) → 위치 전용`.
A2 가 **오른쪽 폴 타깃 위치를 읽으므로** 미러가 먼저다.

**★ 부모를 돌리면 후손이 전부 딸려 움직인다** (가장 크게 물린 것)

척추를 위에서부터 정렬하니 오차가 **조인트마다 90도씩 누적**됐다:
`pelvis` OK → `spine_01` 90도 → `spine_02` 180도. 다음 조인트의 aim 을
**이미 끌려간 위치**로 계산한 탓이다.
**직접 자식만 되돌리게 고쳤다가 또 물렸다** — 손자가 끌려간 채 남는다
(실측: `c` 가 `(0,120,0)` → `(-10,110,0)`).
→ **모든 후손을 부모부터**(위에서 아래로) 되돌린다. 방향 단계 전체 뒤에도 한 번 더.

> **한 단계만 고치면 다음 단계에서 또 물린다.** "자식" 이 아니라 "후손" 이었다.

**★ forward 를 맞추면 up 은 직교화만큼 기운다**

`+Z`→월드`+Y` 와 forward aim 은 **체인이 기울면 동시에 만족될 수 없다**
(실측: `foot→ball` 이 수직에서 36.87도 기울면 `+Z` 도 정확히 36.87도).
→ **forward 우선**(본이 체인을 따라 서는 게 먼저). `+Z` 는 그 조건에서 월드 축에 가장 가까운 값.
**기운 각도를 로그에 적어 감추지 않는다.**
처음엔 테스트가 *정확한 일치*를 기대했다 — **불가능한 것을 기대한 테스트였다.**

**실측 셋**
- **월드 회전 0** 은 `rotate=0`(jointOrient 남음)으로도 `rotate+jointOrient=0`(**부모 회전 남음**)
  으로도 안 된다. `xform -ws -ro 0` 뒤 값을 `jointOrient` 로 옮기고 `rotate=0` 만 된다.
- **Behavior 미러는 축을 `diag(1,-1,-1)`**, 위치는 평면 축만 반전. forward 가 월드에서 같은 쪽을
  보게 되어 **오른팔 forward 가 로컬 `-X`**. 수식으로 구현하고 **`cmds.mirrorJoint` 와 행렬
  단위로 대조**해 검증했다(여러 방향).
- **IK 는 끝 조인트를 안 돌린다** → 다리 `tail` / 팔 `preserve`(로컬 값 기준, 월드는 부모를 따라감).

**`preserved` 와 `no rule` 을 가른다** — 둘 다 씬을 안 바꾸지만 하나는 **결정**, 하나는 **미결**.
같은 칸에 담으면 **확인해야 할 빈칸이 결정된 항목에 묻힌다.**
규칙 없는 40개(`helper_root` · `clavicle_l` · 손가락 38)는 표에 드러내고 안 건드린다.

검증 **Orient 67 + Match 110 + Length 126 + IK 44 = 347항목**.
[[mayapy-headless-verify]] · [[undo-chunk-by-default]]
