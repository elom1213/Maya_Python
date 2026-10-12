---
name: wip-a00145-connect-rules
description: "A00145_RigConnect v01.59 — Connect 52 Facial Target 버튼을 없애고 규칙 json(app/rules/connect/*.json) + Connect by Rule 로; 파일 하나 = 규칙 하나, 새 규칙은 json 만 더한다"
metadata:
  node_type: memory
  type: project
  originSessionId: 042dc05b-37df-4abd-b775-d917cf9a7c8b
  modified: 2026-10-12T01:48:04.583Z
---

2026-10-12 사용자 요청: "Connect 52 Facial Target 버튼을 없애고 정해진 연결을 규칙 json 으로 관리, 첫 규칙
`Apple ARKit 52 Facial Target` 이 버튼과 같은 연결을 하도록, 규칙이 계속 늘어날 것을 염두" (v01.58 → 01.59).

- **규칙 파일** `tools/A00145_RigConnect/app/rules/connect/<rule>.json` — `data/` 는 git 제외(사용자 데이터)라 쓰지 않고
  `app/rules/` 에 둔다(A00090 의 `app/rules/<version>` 과 같은 자리). 모양: `name` / `description` /
  `attributes`(같은 이름끼리) / `pairs`(`[[src, dst], ...]` 이름이 다를 때, attributes 와 함께 가능).
- **코어** `app/core/connect_rules.py`: `load_rules()` → (이름순 규칙, 깨진 파일 errors), `find_rule(name)`,
  `connect_by_rule(src, dst, rule)` → (connected, skipped, pair 수). 연결 규칙은 MEL `JUN_cmd_connect_52Facial` 그대로
  (오브젝트 행 순서 1:1 짧은 쪽만큼, `connectAttr -force`, 없는 attr 스킵). `connect_manager` 의 `FACIAL_52` /
  `connect_52_facial` 은 **지웠다**(목록은 json 으로 뽑음, 52개 순서·철자 보존).
- **UI** Connect 페이지 `Connect by Rule` 그룹 = `Rule` 콤보 + `Reload` + `Connect by Rule`. 콤보 툴팁에 설명 · 짝 수 · 파일
  경로. Reload 는 고르던 규칙을 이름으로 유지. 규칙 0개 / 깨진 파일은 `[WARN]` 로그.
- 새 규칙을 더할 땐 json 만 폴더에 넣는다 — 코드 변경 없음. 릴리즈 빌드는 툴 폴더째 복사하므로 rules 도 따라간다.
- 검증: mayapy 2024(로더 · 깨진 json · 2:1 오브젝트 51/1 · UI 콤보 · undo). 마야 GUI 확인은 아직.

관련: [[wip-a00145-transfer-connection]], [[wip-a00145-connect-both-directions]], [[wip-a00090-rule-versions]]
