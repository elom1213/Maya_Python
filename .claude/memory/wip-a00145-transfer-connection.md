---
name: wip-a00145-transfer-connection
description: "A00145_RigConnect v01.58 — Connect > Transfer Connection 하위 탭(연결 전이: Source attr 의 연결을 같은 이름 attr 을 가진 Destination 으로, upstream/downstream), 제안해 반영한 UI 단순화, listConnections -shapes 함정"
metadata:
  node_type: memory
  type: project
  originSessionId: 042dc05b-37df-4abd-b775-d917cf9a7c8b
  modified: 2026-10-12T01:16:02.669Z
---

2026-10-12 사용자 요청으로 A00145 에 **Connect > Transfer Connection** 하위 탭을 만들었다 (v01.57 → 01.58).
A.attr_01 ↔ Tgt.attr_tgt_n 을 끊고 **같은 이름의** B.attr_01 ↔ Tgt.attr_tgt_n 으로 잇는다. 사용자가 "연결 전이" 라고 불렀다.

- **코어** `app/core/connection_transfer_manager.py` (UI 비의존): `connections_of(obj)` = `listConnections -connections -plugs -shapes`
  를 in/out 으로 — **`-shapes` 를 안 주면 쉐입 플러그가 트랜스폼 이름으로 바뀐다.** blendShape 타겟은 플러그에 **별칭 이름**으로
  나오므로 `connect_manager.list_attrs` 의 타겟 이름과 그대로 맞는다(mayapy 실측). `list_rows`(여러 Source 는 합집합, 행마다 in/out
  플러그), `list_nodes`(체크한 attr 에 연결된 노드, 노드마다 한 행), `missing_on`, `pair_objects`(Destination 1 = 전부 그리로, 같은 수 =
  행 순서, 그 밖엔 ValueError), `transfer`(먼저 Destination 에 잇고 Source 를 끊는다 — 잇기 실패면 Source 유지 · Destination 이
  **이미 다른 것에 구동**되면 건너뜀 · downstream 은 `connectAttr -force` 한 번으로 교체).
- **사용자가 "불필요·중복 UI 를 제안하라" 고 해서 바꾼 것** (요청 원문과 다른 점, 보고함):
  1. "A·B 공통 어트리뷰트" 목록을 따로 두지 않는다 — Destination TSL 이 바뀌면(model 신호 → QTimer 한 번) 어트리뷰트 목록에서
     **Destination 에 없는 행을 빨갛게** 칠하고 툴팁에 누가 없는지 적는다. 전이는 체크한 행 중 있는 것만.
  2. `List UpStream` / `List DownStream` 두 버튼 대신 **Direction 체크박스(Upstream / Downstream) + `List Nodes` 하나** —
     두 방향이 한 목록에 들어 **한 번의 Transfer 로 양쪽**을 옮긴다. 노드 행은 `Tgt    drives: attr_02    driven by: attr_01`.
- UI 관례: 체크 목록은 공용 `JUN_mod_checkList_qt_v01`([[framework-checklist-behavior]]), 행 값은 `Qt.UserRole`(표시 글에 `[in n  out m]`
  `[k/n]` 이 붙으므로 text 로 비교하지 말 것), 기본 툴팁은 `UserRole+1` 에 보관해 빨강 재칠 때 덧붙인 문구가 누적되지 않게.
  옮긴 뒤 두 목록을 다시 읽고 체크는 이름으로 유지 — `Connected Only` 가 켜져 있으면 다 옮겨진 attr 은 목록에서 사라진다(정상).
- 검증: mayapy 2024 코어 + 오프스크린 UI(teal_dark). 페이지 최소 폭 1189(Pair 1203) 라 창 폭은 안 늘었다. **마야 GUI 확인은 아직.**

관련: [[wip-a00145-connect-both-directions]], [[a00145-attribute-tab-blendshape-alias]], [[undo-chunk-by-default]], [[mayapy-headless-verify]]
