---
name: wip-a00060-pole-target
description: A00060 Chain>Pole Target — A'=A+n*v 는 pointConstraint 하나로 환원된다. 가중치는 setAttr 이 음수를 거부하고 연결은 통과한다 (v03.03)
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

검증 **54항목**. [[mayapy-headless-verify]] · [[wip-a00060-ik-edit]]
