---
name: wip-a00130-v02-match
description: A00130_ControlRig_V02 — 템플릿 조인트 패러다임 재작성. Phase 1(Match) 완료. 매핑은 json, 이름은 네임스페이스 붙인 쪽과 안 붙인 쪽을 둘 다 찾아본다, matchTransform 은 잠긴 채널을 조용히 건너뛴다 (v02.00)
metadata:
  type: project
---

**`A00130_ControlRig_V02`** = `A00130_ControlRig`(V01)의 **템플릿 조인트 패러다임 재작성판**
(v02.00, 2026-08-28). **V01 은 그대로 둔다** — 케이지 구조가 달라 호환되지 않는다.
계획서: `JUN_All/docs/plans/A00130_ControlRig_V02_plan.md`(5차 개정),
문서: `docs/A00130_ControlRig_V02.md`.

**패러다임**: 사람이 판단하는 자리를 **템플릿 조인트**가 독점한다 — 눈으로 놓고, 나머지는 버튼.
V01 은 `Targets` 리스트에 **손으로 순서대로** 담아야 했고 그게 이 툴이 어려웠던 진짜 이유였다.

**Phase 1 (완료)** — `Create Template Joints`(계층대로, 원점, 멱등) · `Check`(씬 불변) ·
`Match`(undo 한 스텝) · `Cage namespace` 콤보.
**Phase 2~6 대기**: 저장/로드 · 미러 · IK 세션(`D01_IK_handle`) · Orient · Validate · 길이 수치.

> 계획서상 템플릿 **생성**은 Phase 2 였지만 Phase 1 에 넣었다 — Match 만 있으면
> **넣을 조인트가 없어** 최소 기능이 성립하지 않는다.

**데이터는 json** (`app/data/mapping/<version>/template_map.json`) — 조인트 80 · 짝 74 ·
구조용(매칭 대상 없음) 10 · 위치 전용 세트 6.
**값은 언제나 목록이다** — 원본 표에서 한 조인트가 세트 둘을 갖는 모양이 **두 가지**였다
(`helper_foot_l` 은 한 줄에 둘, **`helper_ball_l` 은 줄이 둘로 나뉘어**).
`{조인트: 세트}` 로 만들면 **한쪽이 조용히 사라진다.** 로드할 때 같은 이름이 또 나오면 합친다.

**실측으로 갈린 설계 두 가지** ★

- **V01 의 `MayaScene.match_transforms` 를 안 가져왔다.** 그 함수는 팔로워의 `rotateOrder` 를
  타깃 것으로 잠깐 바꿨다가 되돌리는데, **`xform -rotateOrder` 는 방향을 보존하지 않는다**
  (실측: `rotate 30/40/50` 인 노드의 rotateOrder 만 바꾸면 월드 회전이 달라진다).
  → 마야 내장 **`matchTransform`** 을 쓴다. rotateOrder·rotateAxis·피벗을 마야가 처리한다.
- **`matchTransform` 은 잠긴 채널을 조용히 건너뛴다** — `translateX` 만 잠근 오브젝트가
  **X 만 안 움직이고 에러도 없었다**(실측). 반쯤 옮겨진 상태가 제일 나쁘므로, 쓰기 전에
  **잠금 + 입력 연결**을 직접 보고 막혀 있으면 **그 오브젝트를 통째로 건너뛴다.**
  판정에 `getAttr(settable=True)` 는 쓰지 않는다([[getattr-settable-lies-for-constrained]]).

**이름은 "어디에 산다" 고 정하지 말고 찾아본다** ★ — `scene_utils.resolve()` 가 후보 두 개를
순서대로 본다: `CAGE:helper_pelvis` → `helper_pelvis`. **조인트와 세트에 똑같이** 적용한다.

> **처음에 틀렸던 것**: "템플릿 조인트는 작업 씬에 로컬, 케이지 세트만 레퍼런스" 라고 보고
> **세트에만** 네임스페이스를 붙였다. 그런데 **실제 케이지 파일에는 템플릿 조인트도 함께
> 들어 있다.** 그래서 케이지를 **임포트**하면 다 찾아지는데 **레퍼런스**하면 조인트가
> `CAGE:helper_*` 가 되어 `Check` 가 **전부 `joint missing`** 이 됐다 — 네임스페이스를
> 제대로 골라도. 사용자가 그 증상을 보고했다(2026-08-28).
> **교훈: 무엇이 로컬이고 무엇이 레퍼런스인지 정해 두면, 파일 구성이 조금만 달라도
> 조용히 전부 실패한다.**

- 둘 다 있으면 네임스페이스 쪽을 쓰고 `ambiguous joint - using ... (also found ...)` 로 알린다.
- 못 찾으면 `looked for CAGE:x and x` 로 무엇을 찾아봤는지 적는다.
- `create_template` 도 같은 `resolve` 를 쓴다 — 안 그러면 **레퍼런스 케이지가 이미 준 조인트를
  로컬에 하나 더 만든다.**
- json 에는 양쪽 다 네임스페이스 없이 적고 실행할 때 붙인다. 목록은 규칙 없이
  `namespaceInfo` 로 뽑아 **사용자가 콤보에서 고른다**(`(none)` 포함).
- **회귀 테스트는 실제 케이지 파일을 저장해 두 방식으로 불러 본다** — 임포트만으로 테스트하면
  이 버그를 못 잡는다.

**하위 세트는 통째로 무시**하고 **재귀하지 않는다** — 하위 세트 안의 오브젝트도 안 건드린다.
판정은 `nodeType(inherited=True)` ([[maya-set-rename-traps]] ⑧ 과 같은 방법).
`cmds.sets(<세트 아닌 노드>, q=True)` 는 **None + 경고**라 먼저 `is_set()` 으로 갈라야 한다.

**미러는 조인트 이름으로 한다** — 조인트는 `_l`↔`_r` 로 **31/31** 맞는데 세트 이름은 33개 중
**17개가 실패**한다(좌우에서 접두 번호까지 바뀐다: `A01_Arm_L_*`↔`A02_Arm_R_*`,
`B01_Leg_L_*`↔`B02_Leg_R_*`). 계획서 7-3.

**orient 규칙은 아직 없다** — json 의 `orient` 필드는 자리만 잡아 두고 아무도 읽지 않으며,
**`Match` 는 orient 가 돌았는지에 의존하지 않는다.** 탭은 `main_window.py` 의 `STEPS` 표에
줄 하나면 붙는다.

**의존**: 지금은 없다(Phase 4 에서 `A00060_jointTool_V03` 의 IK Edit 을 부른다 —
[[referenced-node-name-comparisons]] 로 레퍼런스 케이지에서도 되는 것을 확인해 뒀다).

검증 **88항목** — `plan()`/`apply()` 를 갈라 둬서 `Check` 와 미리보기가 **씬을 안 바꾸고**
같은 계산을 쓴다. [[mayapy-headless-verify]] · [[qapplication-before-maya-standalone]].
