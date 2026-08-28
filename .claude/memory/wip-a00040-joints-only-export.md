---
name: wip-a00040-joints-only-export
description: A00040_file_exporter_V02 Joints only under joints - 조인트 하위 non-joint 를 씬 안 건드리고 FBX 에서 제외 (v02.06)
metadata: 
  node_type: memory
  type: project
  originSessionId: 832a604d-822f-406b-a725-dcd47d36b498
  modified: 2026-08-28T08:21:10.127Z
---

`A00040_file_exporter_V02` v02.06 (2026-08-28): **Joints only under joints** 체크박스(기본 ON).
조인트를 FBX 로 뽑을 때 그 **하위의 조인트 아닌 것**(메시 · 로케이터 · 그룹 · `*_parentConstraint1`)을
FBX 에서 뺀다. 요구 조건이 하나 더 붙어 있었다 — **씬의 조인트 하위 계층은 뽑기 전후로 그대로.**

**Why:** 그 두 번째 조건이 v02.05 의 제외 방식(월드로 unparent 후 복원 · shape `intermediateObject`
토글)을 통째로 무효로 만든다. 되돌리긴 해도 잠긴 채널 · 컨스트레인 · 레퍼런스에서는 **애초에 못 빼서**
`could not exclude` 로 남았고, 메시는 shape 만 숨겨 **빈 트랜스폼이 FBX 에 남았다.**
해법은 씬이 아니라 **익스포터 옵션**을 건드리는 것 → [[fbx-export-selected-scope]].

**How to apply:**
- `core.collect_export_nodes(root, excluded_keys, joints_only)` 가 계층을 펼쳐 (kept, pruned) 를 가른다.
  `under_joint` 플래그를 자식으로 물려주며 판정 — 규칙은 **"조인트 아래"** 에만 적용된다(메시 멤버의
  하위 계층은 그대로 나간다).
- **제외는 그 노드의 자손까지 함께.** 조인트 > 그룹 > 조인트 구조에서 그룹만 빼고 손자 조인트를
  남기면 **FBX 계층이 조용히 재배치된다** — 계층을 바꾸느니 함께 뺀다.
- 타입 필터(Type Filter)도 같은 경로로 통일했다. `_export_fbx` 에서 뺄 게 있을 때만 명시 선택 +
  `core.fbx_options(include_children=False)` 를 쓰고, 없으면 예전 경로 그대로(멤버만 선택).
- 씬을 실제로 건드리는 건 **`Move to scene root` 의 멤버 이동뿐**(UUID 로 잡아 원부모 복원).
- 검증은 **씬 DAG 전체 스냅샷**(경로 · 부모 · 월드 위치 · intermediate)을 export 전후로 비교 +
  뽑은 FBX 를 **다시 임포트**해 내용 확인. 잠긴 채널 메시 · 컨스트레인된 조인트를 씬에 꼭 넣을 것.
