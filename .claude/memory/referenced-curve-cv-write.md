---
name: referenced-curve-cv-write
description: 레퍼런스 커브의 CV 를 고칠 때 - curve -replace 는 저장이 안 되고, setAttr controlPoints 는 히스토리에서 델타가 된다. xform 만 셋 다 만족
metadata:
  type: reference
---

레퍼런스로 들어온 커브는 **셰이프 노드를 지울 수 없다**(`Cannot delete ... locked or
read-only children`). 셰이프 교체 대신 **CV 만 옮겨야** 하는데, 쓰는 방법 셋이 전부 다르다
(mayapy 2024 로 확인, A00400 v01.22).

| 방법 | 절대 위치 | 저장(레퍼런스 edit) | undo |
|---|---|---|---|
| `cmds.curve(shape, replace=True, ...)` | O | **X — 그 세션에만. 다시 열면 원래 모양** | O |
| `setAttr .controlPoints[i]` | **X — 히스토리 있으면 델타(트윅), 값이 두 배** | O | O |
| `cmds.xform(cv, objectSpace=True, translation=...)` | O | O | O |

→ **레퍼런스 커브 CV 는 `xform` 으로 하나씩 쓴다.** 레퍼런스가 아닌 커브는
`cmds.curve -replace` 가 한 번에 쓰고 빨라서 그대로 둔다([[shape-pnts-is-post-deformation]] 과
같은 계열의 구분).

**주기(닫힌) 커브는 컴포넌트 `cv[i]` 가 spans 개까지만 유효하다.** MFn 은 `spans + degree`
개로 세는데(뒤 degree 개는 앞의 복사본) 그 인덱스로 `xform` 을 쓰면 **조용히 마지막 CV 로
클램프돼** 엉뚱한 CV 가 망가진다 (원 = 11개인데 `ls cv[*]` 는 8개, cv[8..10] → cv[7] 을 덮어씀).
앞의 spans 개만 쓰면 이음매는 마야가 따라온다. 쓸 수 있는 개수는
`len(cmds.ls(shape + ".cv[*]", flatten=True))`.
