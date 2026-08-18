---
name: wip-a00145-match-cache
description: "A00145 Match > Cache — 노드 없이 월드 T/R/S 만 기억하는 추상 항목(@cache), 리스트엔 보이지만 씬엔 없다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5ea9f25d-fd66-4b79-a930-ec982f8f7f17
  modified: 2026-08-18T01:00:45.743Z
---

A00145_RigConnect Match 탭의 **Cache**(v01.30, 2026-08-18). 오브젝트를 잠깐 옮겼다 되돌리려고
로케이터를 수천 개 만들던 흐름을 대신한다. `Cache Targets` → Followers 에 `@cache <이름>` 항목
→ Swap → 옮김 → Match 로 복구. 코어는 `app/core/snapshot_manager.py`(**마야 무의존**) +
`match_manager.capture()`.

**Why:** 리스트에 "오브젝트처럼 보이지만 씬에 없는 항목"을 얹는 패턴이 이 툴 밖에서도 쓸 만한데,
그걸 안전하게 만드는 조건이 몇 개 있다.

**How to apply:**
- 키 접두사로 **`@`** 를 쓴다. 마야가 이름에 허용하지 않는 글자라(`rename` 이 `_` 로 바꾼다)
  실제 노드와 절대 겹치지 않는다. 단 `cmds.ls("@cache x")` 는 빈 리스트가 아니라 **RuntimeError** 다
  → 공용 TSL 의 `_looks_like_node` 가드가 그런 텍스트를 마야에 묻지 않는다([[framework-tsl-list-limit]]
  와 같은 위젯).
- **적용은 `cmds.xform(node, ws=True, matrix=...)`**. OM2 `MFnTransform.setTransformation` 이 6배
  빨랐지만 **undo 큐에 안 남는다**([[maya-toggle-cmd-not-undoable]]). xform 은 부모/rotateOrder/
  jointOrient 에서 `matchTransform` 과 결과가 같다(~1e-15).
- **캡처는 오브젝트를 트랜스폼으로 본다** — 라이브 매칭의 메시 centroid 규칙과 일부러 다르다.
  centroid 는 남을 메시 가운데로 보내는 규칙이지 그 메시의 정체가 아니라서, 로케이터 방식은
  메시의 회전을 못 되돌린다. 캐시는 자기 행렬을 기억하므로 된다.
- 컴포넌트 지원은 [[pointposition-points-only]] 를 볼 것.
- 캐시는 **창이 들고 있는 세션 데이터**(창 닫으면 소멸, 씬에 저장 안 됨). 대신 원본이 삭제돼도 살아 있다.
