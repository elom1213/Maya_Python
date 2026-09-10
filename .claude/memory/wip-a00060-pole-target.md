---
name: wip-a00060-pole-target
description: A00060 Chain>Pole Target — A'=A+n*v 는 pointConstraint 하나로 환원된다. 가중치는 setAttr 이 음수를 거부하고 연결은 통과한다. 거리 고정은 n 만 계산해 먹인다 (v03.05)
metadata:
  type: project
---

**`A00060_jointTool_V03` 의 `Chain > Pole Target`** (v03.03, 2026-08-31) —
세 오브젝트에 대해 `A=(p1+p3)/2`, `v=p2-A` 일 때 **`A'=A+n·v` 에 늘 붙어 있는 오브젝트**.
`app/core/pole_target_manager.py`. 계획서 `docs/plans/A00060_poleTarget_plan.md`.

**★ 노드망을 짜기 전에 수식을 전개하라**

```
A' = (1-n)A + n·p2 = ((1-n)/2)·p1 + n·p2 + ((1-n)/2)·p3
```

**세 점의 가중 평균이고 가중치 합이 언제나 1** — 그냥 `pointConstraint` 다.
직접 벡터 노드망을 짜면 `translate` 가 **로컬**이라 체인에서 깨지고, 월드로 하려면
`decomposeMatrix` 셋 + `multMatrix` 로 노드가 8개쯤 든다.
**컨스트레인트가 월드 공간과 타깃의 부모 공간을 공짜로 처리한다** → 노드 **3개**.

**★ 컨스트레인트 가중치는 `setAttr` 이 음수를 거부하고 연결은 통과한다** (실측)

```
attributeQuery(minExists)=True, min=0
setAttr(w0, -0.25)  ->  RuntimeError: below its minimum
연결로 -0.25        ->  통과, 결과가 수식과 정확히 일치
```

`n>1` 이면 양 끝 가중치가 음수라 **모르면 통째로 막힌다.**
[[addattr-min-max-raises-not-clamps]] 의 뒷면 — **min/max 는 `setAttr` 만 막는다.**
어차피 연결이니 `n` 을 살아 있는 어트리뷰트(`poleDistance`)로 두는 것은 공짜다.

**세 점이 일직선이면** `v=0` 이라 n 이 얼마든 A 에 머문다 — T 포즈에서 흔하다.
막지 않고 경고한다.

**`A00130` 이 `ensure()` 로 쓴다** — 템플릿 폴 타깃 4개를 **살아 있게** 물려 `poleDistance` 로
실시간 조절한다(v02.15). 폴 타깃은 `upperarm`·`thigh` 의 **자식**이라 **위치는 일찍(A2 가
읽는다), 회전 0 은 늦게** 해야 한다([[wip-a00130-orient]]).

**★ 이미 배선돼 있으면 거리 값을 덮어쓰지 않는다.** 실행할 때마다 json 값으로 되돌리면
**실시간 조절이 무의미**해진다. json 의 값은 **처음 만들 때만** 쓰고 `reset_distance` 로만 강제 복원.

**★ 자기가 만든 상태를 "남이 손댄 것"으로 오해하지 마라.** `ensure()` 앞에 "translate 가
구동되나" 사전 검사를 뒀더니, 두 번째 실행에서 **우리가 건 컨스트레인트**에 걸려 4개가 전부
걸러졌다(`0 pole target(s) wired`). **두 번째 실행에서만 드러나는 종류의 버그다.**

**`Create Selected` (v03.04)** — `create_on()` 은 `ensure()` 를 선택 목록에 돌리는 얇은 층이다.
새 노드를 만드는 `create()` 와 배선(`_wire`)이 같다.

**★ 체인 멤버를 고른 채 누르면 순환이 된다.** 리스트의 세 오브젝트 자신에게 걸면 **자기 자신을
타깃으로 삼는 pointConstraint** 다. 마야는 **사이클 경고만 내고 씬은 망가진 채 남는다** —
막지 않으면 조용히 깨진다. 긴 이름으로 비교해 건너뛴다.

**`Fixed distance` (v03.05)** — 거리를 상수로 두려면 `A' = p2 + d*v/|v|` 인데, 이것은
`A' = A + n*v` 에서 **`n = 1 + d/|v|`** 와 **같은 식**이다. **정규화가 필요해도 컨스트레인트를
버릴 이유가 없다** — 구성은 그대로 두고 **먹이는 `n` 만 계산된 값으로** 바꾼다(노드 6개).

**★ `multiplyDivide` 의 0 나누기는 0 도 NaN 도 아니고 `100000`** (실측, 경고만).
더 위험한 건 `|v|` 가 **아주 작을 때** — `n` 이 1e9 로 뛰면 가중 평균이 큰 수끼리의 뺄셈이라
자릿수가 날아간다. 나누기 앞에 `clamp` 로 하한.

**★ 모드가 다르면 `kept` 가 아니라 재배선.** 체인이 같으면 `kept` 라는 규칙 때문에 옵션을
켜고 눌러도 **아무 일도 안 일어난 것처럼** 보인다. 재배선·bake 는 가중치에서 거슬러 올라가
**우리 유틸리티 타입만** 골라 지운다(`helper_nodes()`) — 계산 노드가 여러 단이라 한 단만
지우면 떠돌이가 남는다.

**A00130 은 `ensure(fixed=False)` 기본값이라 영향 없다.**

검증 **54 + 22 + 25항목**. [[mayapy-headless-verify]] · [[wip-a00060-ik-edit]]
