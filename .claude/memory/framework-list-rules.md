---
name: framework-list-rules
description: 공용 TSL `Rules` 버튼(show_rules=True) — 규칙 json(Framework/rules/list_rules/<Category>/)대로 리스트업, 지금은 세트 멤버(네임스페이스 무관), 기본 이름순. A00145 Constraint 첫 적용 + Swap
metadata:
  type: project
---

2026-11-09 사용자 요청: A00145 Constrain > Constraint 에 Match 의 Swap + Targets/Followers 를 **정해진 규칙대로 리스트업**,
"TSL 있는 모든 툴이 쓸 수 있게 공용으로". 첫 규칙 = `C:\JUN\JUN_Src_Rig\02_Cage_v02\Cage_v002_0130.mb` 의 세트 10개
(A01_FingersMC_O_tgt_L … B06_Twist_tgt), 세트에 네임스페이스가 붙어도 대응.

- **TSL `show_rules=True`(기본 꺼짐)** → Select 옆 `Rules` 메뉴. 규칙 클릭 = 교체, **Shift = 추가**. `New Rules from Selected Sets...`
  (세트 하나 = 규칙 하나, 네임스페이스 뺀 이름, 카테고리 묻기) · `Open Rules Folder`. 메뉴는 열 때마다 폴더 재로드.
- 코어 `Framework/core/list_rules.py`(json 부분 DCC 비의존): `load_rules` → (rules, errors), `save_rule`, `resolve_rule(rule, namespace)`.
  규칙 = `Framework/rules/list_rules/<Category>/<name>.json` {name, description, sets[], order, expand_nested}. git 추적(릴리즈에 동봉).
- **세트 찾기 = `cmds.ls(name, recursive=True, type="objectSet")` + 잎 이름 정확히 같은 것만.** 여러 네임스페이스면 `ambiguous` →
  TSL 이 `choose_namespace` 팝업으로 묻는다(시험은 메서드 바꿔 끼움 — 오프스크린 QMenu.exec_ 는 멈춘다).
- **`cmds.sets -q` 멤버 순서는 임의**(Cage 실측) → 기본 `order: "name"`(네임스페이스 뺀 이름순). Constraint 는 자리로 짝짓기 때문.
- 모은 게 0 이면 리스트를 안 건드린다(교체로 비우지 않게). 멤버 세트는 펼침(순환 안전), 컴포넌트 멤버 그대로.
- A00145 v01.70: Constraint 페이지 `tsl_targets/tsl_followers` 에 show_rules, `on_constraint_swap`.
- 시험 `Framework/tests/test_list_rules.py` 39/39 (Cage 를 `cage:` 로 레퍼런스: **loadReferenceDepth="none" 으로 걸면 언로드라 노드 없음**
  — 시험에서 실제로 걸림, `topOnly` 로). GUI 확인 아직.

관련: [[wip-a00145-connect-rules]], [[wip-a00340-selectiontool]], [[maya-reference-import-traps]]
