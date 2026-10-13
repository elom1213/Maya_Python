---
name: wip-a00145-connect-rules
description: "A00145_RigConnect v01.59~60 — Connect 52 Facial Target 버튼을 없애고 규칙 json(app/rules/connect/*.json) + Connect by Rule 로; 파일 하나 = 규칙 하나, 새 규칙은 json 만 더한다 · Transfer Connection 의 Save as Rule 로 씬에서 규칙을 뽑는다(방향 하나)"
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

**v01.60 (2026-10-13, 사용자 요청) — Transfer Connection `Save as Rule...`**: 사용자가 "Source Objects + Attributes · Connected Nodes
의 체크된 관계만 규칙으로" 를 제안했고 그대로 채택, **방향 선택 + 미리보기 창**을 더했다(규칙은 `Source.a -> Destination.b` 한 방향이라
downstream `[Source attr, node attr]` / upstream `[node attr, Source attr]` 중 하나만 — 섞으면 적용할 때 누가 Source 인지 갈린다).
- `connection_transfer_manager.rule_pairs(rows, attrs, nodes, upstream, downstream)` — cmds 없이 list_rows 결과만 읽음, 같은 짝은 한 행(count · plugs).
- `connect_rules.save_rule(name, pairs, description, file_name, rules_dir, overwrite)` / `rule_file_name`(슬러그) / `rule_path`. 같은 이름 짝 → `attributes`.
- `ui/rule_save_dialog.RuleSaveDialog(down_pairs, up_pairs, existing_rules)` — 파일명은 이름을 따라가되 `textEdited` 뒤 고정, 존재 파일은 덮어쓰기 확인,
  같은 이름 규칙은 경고. 저장 뒤 `_load_connect_rules()` + 새 규칙 선택.
- 검증: mayapy 2024 core + 오프스크린 다이얼로그(QApplication 을 standalone 전에!). 마야 GUI 확인 아직.

관련: [[wip-a00145-transfer-connection]], [[wip-a00145-connect-both-directions]], [[wip-a00090-rule-versions]], [[qapplication-before-maya-standalone]]
