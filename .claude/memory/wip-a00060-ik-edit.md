---
name: wip-a00060-ik-edit
description: A00060_jointTool_V02 IK Edit 탭 — ikHandle/폴 벡터 컨스트레인트를 둔 채 본 체인 수정. 핸들 스냅만으론 부족하고 폴 벡터 역산이 핵심
metadata:
  type: project
---

`A00060_jointTool_V02` **v01.05 `IK Edit` 탭** (2026-08-25).
**V03 에서는 `Chain > IK Edit` 하위 탭이다** ([[wip-a00060-v03-tab-reorg]]) — V03 은 탭을 열
때마다 씬을 다시 읽어 버튼 상태를 맞춘다(V02 는 창을 만들 때 한 번만 읽었다). 본 체인에 걸린 ikHandle 과
poleVectorConstraint 를 **지우지 않고** 체인을 수정한다. UI 는 A00275 `Edit Mesh` 와 같은
토글(`EDIT IK CHAIN`) + 상태를 씬 노드에(`JUN_ikEdit` / `JUN_ikEditData` on the ikHandle).

**마야에는 대응 기능이 없다** — 2024 컨스트레인트의 `Update Offset` 은
`parentConstraint -e -maintainOffset`(`AETemplates/AEparentConstraintTemplate.mel:90`)이지만
`AEikHandleTemplate.mel` 에는 없고 `ikHandle` 명령에도 플래그가 없다(`-enable` 은 아예 없음).

**핵심: 핸들 스냅만으론 부족하다** (Maya 2024 실측)
- IK 켜진 채 중간 조인트를 `(2,5,1)` 로 → 솔버가 `(0.00068, 5.2, 1.72)` 로 되돌린다.
- IK 끄고 고친 뒤 **핸들만** 이펙터로 스냅 → **편차 1.615** (폴 벡터가 옛 평면을 가리켜 체인이 비틀림).
- 핸들 스냅 **+ 폴 벡터 역산** → **편차 0.00000000** (위치·회전 모두, 저장/재열기 후에도).

**poleVectorConstraint 의 식** (실측 확정)
```
pv = (target_world − ikRoot_world) × handle.parentInverseMatrix(3x3) + offset
```
`poleVector` 는 **핸들 부모 공간**에 산다(월드 아님). `offset` 은 그 출력 공간에서 선형으로
더해지므로 역산이 한 줄이다 — `new_offset = desired_pv − (current_pv − current_offset)`.
컨스트레인트도 타깃도 안 건드리고 **offset 만** 갱신 = 마야 `Update Offset` 과 같은 발상.
`desired_pv` = 루트→중간에서 체인 축 성분을 뺀 **수직 성분**.

**twist 보정** — `twist≠0` 이면 솔버가 평면 위에 그 각을 **더** 얹는다(편차 1.06).
원하는 벡터를 체인 축 기준 **−twist** 만큼 미리 돌려 상쇄하고 **twist 값은 안 건드린다**
(애니 채널). `ikRPsolver` 는 `roll` 을 쓰지 않는다.

**실측이 아니면 조용히 틀리는 것들**
- **`getAttr(plug, settable=True)` 는 컨스트레인트가 구동하는 트랜스폼에도 `True`** →
  "옮겼다" 고 보고해 놓고 편차 1.0 이 남는다. `connectionInfo(isDestination=True)` + `lock` 으로 판정.
  참고: 평범한 `connectAttr` 로 연결된 `ikBlend` 에 대해서는 `settable` 이 제대로 False 다.
- **`ikHandle.snapEnable`(기본 ON) 은 IK 가 꺼진 동안 핸들을 이펙터에 자동으로 붙인다** →
  자유로운 핸들에선 스냅이 사실상 무동작. 구속된 핸들의 델타를 핸들 트랜스폼에서 내면 0 이 나오므로
  컨스트레인트의 **출력 플러그 `constraintTranslate`** 를 봐야 한다.
- `ikHandle -q -jointList` 는 **끝 조인트를 뺀다**. 끝 조인트는 `effector.translateX` 의 입력.
- `ikBlend` 가 FK/IK 스위치에 연결되면 `setAttr` 이 `RuntimeError`. 그때만
  `cmds.ikSystem(e=True, solve=False)`(마야 "Enable IK Solvers")로 물러선다 — **씬 전역**이고
  **세션 상태**라 마야 재시작 뒤 살아난다(툴이 편집 중이면 다시 꺼 준다).
- `ikSplineSolver` 는 커브가 체인을 구동 → 거부. 일직선 체인은 팔꿈치 방향을 못 읽음 → 경고.
  `ikSCsolver` 는 폴 벡터가 없어 스냅만으로 편차 0.

**v03.02 (2026-08-27) — 레퍼런스에서 온 핸들은 폴 벡터를 갱신하지 않고 있었다.**
`ikHandle -q -solver` 가 **솔버 노드 이름**을 주는데 레퍼런스면 `CAGE:ikRPsolver` 로 온다 →
`RP_LIKE_SOLVERS` 비교가 어긋나 `_apply_pole_vector` 가 맨 앞에서 빠져나갔다.
**핸들만 스냅되고 폴 벡터는 옛 평면** → 편차 **2.036 / 45.77도**(로컬은 0.000000), 경고 없음.
`handle_solver()` 가 `cmds.nodeType` 을 돌려주게 고쳤다 — 자세한 건
[[referenced-node-name-comparisons]]. **레퍼런스 자체는 이 툴을 막지 않는다** —
`setAttr`/`addAttr`/`deleteAttr` 다 되고 편집은 reference edit 으로 저장된다.

관련: [[mayapy-headless-verify]] · [[wip-a00275-edit-mesh]] ·
[[constraint-target-plugs-and-offset-spaces]] · [[undo-chunk-by-default]]
