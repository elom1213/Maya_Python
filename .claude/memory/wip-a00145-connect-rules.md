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

**v01.61 (2026-10-13, 사용자 요청) — Connect by Rule `Manage...`**: 규칙 표 + 체크한 규칙 json 삭제(`ui/rule_manage_dialog.RuleManageDialog`).
`connect_rules.delete_rules(rules, rules_dir)` 는 **규칙 폴더 안의 .json 만** 지운다(밖/다른 확장자는 failed). 깨진 json 은 빨간 줄로만
알리고 안 건드린다(load_rules 가 ConnectRule 을 못 만들어 표에 못 올린다). 창 닫힌 뒤 `deleted_count()` 보고 콤보 재로드. 테스트는 `on_delete(confirm=False)`.

관련: [[wip-a00145-transfer-connection]], [[wip-a00145-connect-both-directions]], [[wip-a00090-rule-versions]], [[qapplication-before-maya-standalone]]

**v01.63 (2026-10-22)** — 두 번째 규칙 `jali_22_viseme.json` = **`JALI 22 Viseme`**: `Jaw` `Lip` + 비즘 20
(`Ah Aa Eh Ee Ih Oh Uh U Eu Schwa R S ShChZh Th JY LNTD GK MBP FV W`), 사용자가 준 순서 그대로. 이 22개 이름은
JUN_JALI 의 angela 리그(`AHH AAA IEE …`)와 **다른 철자 체계**다 — 리그마다 json 을 따로 두는 A00540 과 같은 사정.
규칙 이름은 "<체계> <개수> <대상>" 꼴(ARKit 52 와 맞춤). 데이터만, mayapy 22/22 확인.

**2026-10-22 실측 — 부분 연결은 안전하다**: `connect_by_rule` 은 짝마다 try/except 라 없는 attr · 잠긴 dst · 타입 불일치 ·
없는 오브젝트 행 · 자기 연결 모두 그 짝만 skipped 로 세고 나머지는 전부 연결(mayapy 16항목). 단 **skipped 는 사유를
구분하지 않고 로그에 attr 이름이 안 나온다** — 사용자가 "뭐가 안 붙었나" 를 물으면 그게 후속 작업.

**v01.64 (2026-10-22)** — 겹치는 이름 보호 + 스킵 사유: `resolve_node(name)` → (긴 이름, 사유). 행의 src/dst 가 하나로 안 잡히면
(없음 · `ambiguous name, N objects match`) **행 통째 스킵**, 아니면 긴 이름으로 `connectAttr -force`. `connect_by_rule(..., on_skip=cb)`
콜백 `(src, dst, attr|None, reason)`; attr 사유는 `no such attribute on Source/Destination` 또는 마야 메시지 마지막 줄(잠김 · 타입).
UI 는 행 단위 한 줄, attr 단위는 (행, 사유) 로 묶어 한 줄. **레퍼런스 ↔ 레퍼런스 · 중첩 레퍼런스 연결 OK, 저장 후 레퍼런스 편집으로 유지**
(mayapy 실측). 관련: [[connectattr-ambiguous-short-name-silent]]
