---
name: framework-tsl-list-limit
description: 공용 TSL 위젯의 요약 모드(list_limit) — 대량 선택이 느린 진짜 이유는 줄 수가 아니라 항목별 UUID 조회
metadata: 
  node_type: memory
  type: project
  originSessionId: 5ea9f25d-fd66-4b79-a930-ec982f8f7f17
  modified: 2026-08-18T00:26:24.014Z
---

`Framework/qt/MOD_tsl_qt_v01.py` 에 **`list_limit`** 옵션이 있다(2026-08-18 추가). 항목이 그 수
**이상**이면 리스트를 채우지 않고 요약 라벨 + **`List All (N)`** 버튼만 보여준다. 기본 `0` = 예전처럼
언제나 펼침이라, 옵션을 주지 않은 74곳의 사용처는 영향이 없다.
첫 적용: `A00145_RigConnect` Match 탭의 Targets/Followers (`MATCH_LIST_LIMIT = 500`).

**Why:** "리스트업이 느리다" 의 원인이 QListWidget 의 줄 수라고 짐작하기 쉬운데, 실제 비용은
[[wip-tsl-uuid-selection]] 때문에 **항목마다 부르는 `cmds.ls(name, uuid=True)`** 다. 버텍스 4천 개를
Select 하면 마야 호출이 4천 번 — 정작 하려던 작업보다 오래 걸린다. 요약 모드는 표시 텍스트만
파이썬 리스트로 들고 있어서 그 호출이 **0회**가 된다(스텁 측정 1000개: 1000회 → 0회).

**How to apply:** 리스트가 컴포넌트로 채워질 수 있는 툴이면 `list_limit=500` 을 주는 것으로 끝난다 —
`get_all_items()` / `count()` / `set_items()` 가 요약 상태에서도 그대로 동작해서 **호출부는 바꿀 것이
없다**. 트레이드오프는 **요약 상태에 UUID 가 없다**는 것: `get_all_nodes()` 가 이름으로 해석하므로
담은 뒤 리네임된 항목은 빠진다. 리네임 안전성이 필요하면 `List All` 로 펼치거나 옵션을 주지 않는다.
같은 "펼치지 말고 요약" 발상의 선례는 A00170 AttachCrv > Edge Loop 의 Stored selection.
