---
name: wip-a00440-settool
description: A00440_SetTool - 컴포넌트 세트 집합연산. 이름 정규화가 전부이고 세트 클릭은 멤버를 선택한다
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-18T00:25:32.717Z
---

`A00440_SetTool` (v01.00, 2026-08-18). 컴포넌트를 원소로 갖는 오브젝트 세트끼리
∪ / ∩ / ∖ 와 Split(A∖S, A∩S). 아키텍처 (B) PySide.

**핵심은 이름 정규화다.** 마야는 같은 컴포넌트를 `pCube1.vtx[0:2]` / `pCube1Shape.vtx[1]` /
`|grp1|pCube1.vtx[1]` 로 다르게 부른다 → 읽는 모든 경로에서 `cmds.ls(..., flatten=True, long=True)`.
mayapy 실측:
- **셰이프로 선택해도 트랜스폼 롱네임으로 정규화**된다 → 세트 멤버와 씬 선택을 직접 비교해도 된다
- 동명 노드가 있으면 `cmds.sets(q=True)` 가 구분되는 **부분 경로**를 준다(뭉개지지 않음).
  반대로 **모호한 짧은 이름을 `cmds.sets()` 에 넘기면 에러** → 항상 정규화해서 넘길 것
- 빈 세트는 `None` (→ `or []`), 없는 멤버 remove 는 무시(에러 아님), 비운 세트 노드는 남는다
- `cmds.duplicate` 는 **원본이 속한 세트에 복제본도 넣는다**

**가장 큰 함정**: `cmds.select(<세트>)` 는 세트 노드가 아니라 **멤버를 펼쳐서 선택**한다.
공용 TSL 은 행 클릭 시 `cmds.select` 를 하므로, 리스트에서 A 를 고르면 씬 선택이 A 의 멤버
전체가 된다 → Split 이 A 를 통째로 빼내는 사고. 그래서 **Capture Selection** 으로 S 를 미리
붙잡고, 씬 선택 == A 의 멤버 전체면 실행을 **거부**한다.

**설계**: `set_ops.py` 는 Maya 무의존(단독 테스트 가능). 순서 보존을 위해 판정에만 `set`,
결과는 `dict`. 컴포넌트 종류는 **연산에서 가리지 않고**(섞여도 ∪/∩/∖ 는 성립) 경고만 —
훗날 버텍스/엣지 세트를 섞는 요구에 대비. 중첩 세트는 원소 하나로 센다.

**Split 의 수학 용어**: 표준 연산자 이름은 없다. `A∩S` = **자취(trace of S on A)`,
`A∖S` = **상대여집합**, 둘을 합친 `{A∖S, A∩S}` = **S 가 A 에 유도하는 분할(partition)**.
`A = (A∖S) ⊔ (A∩S)`. 구현 세계에서는 partition/split.

검증: mayapy 2024 헤드리스 71항목. 관련: [[mayapy-headless-verify]], [[undo-chunk-by-default]],
[[wip-tsl-uuid-selection]], [[qapplication-before-maya-standalone]]
