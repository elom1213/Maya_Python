---
name: wip-a00290-bake-delete-tab
description: A00290 Bake Delete 탭 — 디포머 뒤 deleteComponent 를 리그 전체에 반영(중립·타겟·델타·웨이트 재매핑)
metadata: 
  node_type: memory
  type: project
  originSessionId: 3a0c2f78-6b11-4467-ab38-c6a4ffe45922
  modified: 2026-08-26T08:36:53.327Z
---

`A00290_BSTool` **Bake Delete 탭** (v01.19, 2026-08-26) — `blendShape -> skinCluster -> deleteComponent`
로 남은 지우기를 **체인 맨 앞(중립 셰이프)으로 옮겨** 히스토리를 `blendShape -> skinCluster` 로
되돌린다. 중립 · 모든 live 타겟 메시가 같이 줄고, 정점 번호를 쓰는 데이터가 전부 재매핑된다.
코어는 `app/core/bake_delete_manager.py`(`analyze` / `apply` / `format_report`).

**Why:** 리깅된 메시에서 컴포넌트를 지우면 마야가 지우기를 디포머 **뒤**에 붙여 **보이는 메시와
타겟 메시의 토폴로지가 갈라진다**. Shape Editor 로 타겟을 열면 지우기 전 모양이 나온다.

**How to apply:**
- **정점 매핑은 위치 greedy 한 번**이면 된다 — 마야는 컴포넌트를 지울 때 **살아남은 정점의 상대
  순서를 보존**하고, deleteComponent 의 입력/출력 메시는 같은 계산 결과라 좌표가 비트 단위로 같다.
- **검증은 "같은 엣지"가 아니라 "같은 페이스"** — 버텍스를 지우면 페이스가 한 변 줄며 **없던 엣지가
  생기고**, 엣지를 지우면 두 페이스가 **병합**된다. 엣지 기준으로 짜면 버텍스 삭제가 곧바로 거절된다.
- **줄어든 토폴로지는 보이는 메시를 복제해 얻는다.** 메시를 새로 조립하면 **UV 를 잃는다.**
  `donor.outMesh -> dst.inMesh` 연결 → 평가 → 해제하면 데이터가 그대로 남는다.
- 함정 (Maya 2024 실측):
  - **밀어 넣은 셰이프의 `pnts` 를 안 지우면 조용히 틀린다** — 인덱스가 지우기 전 번호라 엉뚱한
    정점에 옛 오프셋이 얹힌다 (live 타겟이 정확히 이것 때문에 깨졌다).
  - **skinCluster 웨이트는 DAG 셰이프 정점 수만큼만 읽힌다** — `getWeights` 가 **에러 없이** 앞쪽
    일부만 준다. 읽기 전에 deleteComponent 를 `nodeState = 1` 로 꺼 지우기 전 토폴로지로 되돌린다.
  - **디포머 멤버십은 groupParts 가 아니라 `<orig>.componentTags`** (마야 2022+. `cmds.cluster` 가
    groupParts 를 아예 안 만든다). 중립 셰이프에 그대로 남으니 같이 고쳐야 한다.
  - **`baseWeights`/`targetWeights` 는 `setAttr` 로 써도 blendShape 가 안 더러워진다** → `dgdirty`.
  - **`pnts` 를 정점마다 `setAttr` 하면 9만 정점에서 40s** → 연속 구간 쓰기로 apply 전체 46s → 2.5s.
- 정점/웨이트 쓰기가 OpenMaya API 라 **Ctrl+Z 로 완전히 안 돌아온다** — UI 가 경고한다.

관련: [[shape-pnts-is-post-deformation]] [[skincluster-weight-index-physical]]
[[blendshape-live-target-inputpointstarget]] [[extendtoshape-picks-wrong-shape]]
[[mayapy-headless-verify]] [[wip-a00290-mix-targets-tab]]
