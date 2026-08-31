---
name: wip-a00130-pair-constrain
description: A00130_ControlRig_V02 Pair/Constrain 탭 — 세트 1:1 매칭과 Con->parentConstraint. parentConstraint 는 드라이버가 다르면 조용히 타깃을 늘린다 (v02.10)
metadata:
  type: project
---

**`A00130_ControlRig_V02` 의 `Pair` · `Constrain` 단계** (v02.10, 2026-08-31).
`app/core/pair_manager.py` · `constrain_manager.py` · `pair_map.json` · `constrain_map.json`.
탭 순서: `Orient & Place · Length · Match · Pair · Constrain`.
관련: [[wip-a00130-v02-match]] · [[wip-a00130-orient]] · [[wip-a00130-ik-session]].

**Pair** — Match 와 다르다. Match 는 **템플릿 조인트** 기준 1:N, Pair 는 **세트 대 세트**로
원소 하나씩. **두 세트가 모두 원소를 정확히 하나 가질 때만** 실행하고, 아니면 **몇 개인지
적어서 건너뛴다** — 고를 근거가 없는데 하나를 고르면 조용히 틀린 리그가 된다.

**★ `parentConstraint` 는 드라이버가 다르면 조용히 타깃을 늘린다** (실측)

```
같은 드라이버로 재실행  -> 같은 노드, 타깃 1개      (멱등)
다른 드라이버로 재실행  -> 타깃 2개                 (조용히 늘어난다)
```

`Con` 을 바꾼 뒤 다시 돌리면 **두 노드가 반씩 끌어당기는** 리그가 된다.
→ **이미 컨스트레인트가 있으면 건드리지 않고**, "드라이버가 바뀌었으면 먼저 지우라" 고 적는다.
회귀에 **`Con` 을 바꾸고 다시 돌려도 안 늘어난다**를 박아 뒀다.

**그 밖의 실측**
- 잠긴 채널이 있으면 `parentConstraint` 는 **`RuntimeError`**(조용하진 않다). 미리 보고 건너뛴다.
- `maintainOffset` off 면 오브젝트가 **드라이버로 끌려가고**, on 이면 제자리.
  기본 off(명령 기본값)이고 **떨어져 있으면 거리를 로그에 적는다** — 그때만 결과가 갈린다.
- `Con` 이 `message` 든 일반 어트리뷰트든 `listConnections` 로 노드가 나온다.

**받은 이름을 임의로 고치지 않고 짚는다** — `C04_match_10_l_ArmPol`(끝 `e` 없음) ·
`C04_pose_obects`(`j` 없음)를 그대로 넣고 로그·문서에 표시했더니, 사용자가 **둘 다 오타로
확인**해 v02.11 에서 고쳤다(`...ArmPole` · `C04_pose_objects`).

> **짚어 두는 편이 맞았다.** 같은 데이터에 `B01_Leg_R_ik_08/09` 처럼 **다른 오른쪽 다리 세트
> 13개와 접두가 어긋나 보여도 진짜인** 이름이 함께 있다. 임의로 "고쳤다면" 그쪽을 망쳤을 것이다.
> 씬에 없으면 **찾아본 이름을 적어** 알리므로 어느 쪽이든 조용히 틀리지 않는다.

> **테스트가 순서에 기대면 안 된다.** `cmds.sets(q=True)` 는 **멤버 순서를 보장하지 않는다** —
> 리스트로 비교하다 실패했고 매핑 비교로 고쳤다. 같은 회차에 **같은 라벨을 두 곳에 쓴 것**과
> **0부터 세는 인덱스를 1부터로 착각한 것**도 함께 잡았다. 셋 다 코드가 아니라 테스트 문제였다.

검증 **Pair/Constrain 69 + Orient 96 + Match 115 + Length 127 + IK 57 = 464항목**.
[[mayapy-headless-verify]] · [[undo-chunk-by-default]] · [[constraint-target-plugs-and-offset-spaces]]
