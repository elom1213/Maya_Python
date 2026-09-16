---
name: wip-a00145-mirror-network-offsets
description: "A00145 Mirror > Create — 네트워크에 값으로 박힌 maintain offset 은 미러 쪽 기준으로 다시 풀어야 한다 (v01.42)"
metadata:
  node_type: memory
  type: project
---

A00145_RigConnect **Mirror > Create 의 노드 네트워크 재구성** (v01.41→**01.42**, 2026-09-16).

`A00170_driverTool` 의 `AttachCrv > Default + Maintain offset` 으로 붙인 오브젝트
(`CRV -> vectorProduct -> POCI -> fourByFourMatrix -> multMatrix -> joint`)를 커브와 함께
미러하면 **커브만 미러되고 오브젝트는 원본 자리에 남았다.** 원인이 둘이었다.

1. **유틸리티 노드가 네트워크 수집에서 빠졌다** — `vectorProduct` 가 `shadingDependNode` 를
   상속하기 때문. 자세한 건 [[utility-nodes-inherit-shadingdependnode]].
2. **`multMatrix.matrixIn[0]` 의 maintain offset 은 연결이 아니라 값**이라 복제하면 그대로
   따라오는데, 그 값은 `OPM0 · frame0⁻¹` 로 **원본 쪽 프레임 기준**이다. 미러된 커브의 프레임과
   곱해지는 순간 오브젝트를 원본 쪽으로 끌어당긴다(YZ 실측: `x=-4` 로 가야 할 조인트가 `x=-10.1`).

**오프셋의 미러는 "같은 상수" 가 아니라 "미러된 프레임 기준으로 같은 관계"다.** 네트워크를 다시
세운 뒤(`_restore_network_placement`) 미러가 놓아 준 월드 `T` 로 돌아오도록 상수를 다시 푼다.

```
W = L · OPM · P                                   (로컬 · offsetParentMatrix · 부모 월드)
OPM_need    = OPM_now · P · W_now⁻¹ · T · P⁻¹
matrixIn[k] = 앞쪽곱⁻¹ · OPM_need · 뒤쪽곱⁻¹        (matrixSum = matrixIn[0]·[1]·…)
```

로컬 `L` 을 직접 읽지 않고 **현재 상태에서 역산**해 피벗 · `jointOrient` · `rotateAxis` 와 무관하게
한다. 같은 방식은 `offsetParentMatrix` 를 구동하는 어떤 multMatrix 리그에도 쓸 수 있다
([[parentmatrix-includes-offsetparentmatrix]] 도 같이 본다).

**Maintain offset 을 끄고 붙인 조인트**는 `rotate` 를 네트워크가 직접 구동한다. 미러가 회전을
`jointOrient` 로 옮겨 두면([[wip-a00145-mirror-tab]] 의 조인트 규칙) 두 회전이 겹쳐 엉뚱한 방향을
보므로, 그 경우 `jointOrient` 는 **원본 값 그대로** 둔다(= 커브 프레임에 대한 같은 로컬 오프셋).
