---
name: referenced-node-name-comparisons
description: 레퍼런스에서 오는 것은 노드 이름에 네임스페이스가 붙는다 — ikHandle -q -solver 가 'CAGE:ikRPsolver' 를 주는 바람에 이름 비교가 조용히 어긋났다. 타입/UUID 로 판정할 것
metadata:
  type: reference
---

**마야가 "이름" 을 돌려주는 쿼리는 레퍼런스에서 전부 네임스페이스가 붙어 온다.**
그 이름을 상수와 비교하면 **에러 없이** 어긋난다.

**실제로 물린 사례** (`A00060_jointTool_V03` v03.02, 2026-08-27)

```python
cmds.ikHandle(h, q=True, solver=True)                    # 'CAGE:ikRPsolver'
'CAGE:ikRPsolver' in ("ikRPsolver", "ikSpringSolver")    # False (!)
```

**솔버 노드까지 함께 레퍼런스된다**는 걸 놓친 것이다. `IK Edit` 이
`if solver not in RP_LIKE_SOLVERS: return` 로 빠져나가 **폴 벡터 갱신을 통째로 건너뛰었고**,
조인트를 옮겨 확정하면 **위치 2.036 / 회전 45.77도** 가 조용히 남았다(로컬 씬은 0.000000).
`inspect()` 도 같은 비교를 써서 **blockers 가 비어 있었다** — 경고조차 없었다.

**고치는 법**: 이름이 아니라 **노드 타입**으로 판정한다.

```python
node = cmds.ikHandle(h, q=True, solver=True)
solver = cmds.nodeType(node) if node and cmds.objExists(node) else ""
```

네임스페이스에도, **솔버 노드를 리네임한 씬**에도 흔들리지 않는다.

**같은 부류를 의심할 곳**
- `*(q=True, ...)` 가 **노드 이름**을 주는 모든 쿼리(solver · deformer · constraint 이름 등)
- 이름 상수/토큰과 `==` · `in` 으로 비교하는 코드 전부
- **타입 필터(`ls(type=...)` · `listConnections(type=...)` · `nodeType(x) == ...`)는 안전하다** —
  타입은 네임스페이스를 안 탄다

**레퍼런스 노드에서 되는 것 / 안 되는 것** (Maya 2024 실측)

| | |
|---|---|
| `setAttr` (트랜스폼 · `preferredAngle` · 컨스트레인트 offset) | O — **reference edit 으로 저장돼 씬을 다시 열어도 남는다** |
| `addAttr` / `deleteAttr` (동적 어트리뷰트) | O — 지우면 **원본 파일에 흔적이 안 남는다** |
| `rename` | X — `Cannot rename a read only node` ([[maya-set-rename-traps]] ⑤ 와 같은 메시지) |
| 이름으로 노드를 잡아 두기 | 위험 — 네임스페이스가 붙는다. **UUID 로**([[uuid-safe-rename-duplicate-names]]) |

관련: [[wip-a00060-ik-edit]] · [[ikhandle-creation-traps]] · [[mayapy-headless-verify]]
