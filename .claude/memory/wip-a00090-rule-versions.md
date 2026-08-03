---
name: wip-a00090-rule-versions
description: A00090_ConnectionBuilder 규칙 json 을 rules/<version> 폴더로 나누고 UI Version 콤보로 선택 (v01.05)
metadata: 
  node_type: memory
  type: project
  originSessionId: d70da490-70ce-45b8-ac44-b1338adf1b02
  modified: 2026-08-03T06:35:57.266Z
---

A00090_ConnectionBuilder 의 규칙 json 경로가 `app/rules_v01/*.json` → **`app/rules/<version>/*.json`**
으로 바뀌었다(2026-08-03, v01.05). 기존 8개는 `rules/v001`. 새 버전은 폴더(`v002` …)를 만들어 넣고
UI 의 `Version` 콤보에서 고른다. `Refresh` 로 재스캔.

**Why:** 포즈 구성이 바뀌면 `mapping` 이 달라지는데, 옛 규칙을 덮어쓰지 않고 프로젝트별로 병행해야 했다.
`rules_v01` 안에 `v001` 을 넣는 안은 이름이 중복(v01 안의 v001)이라 `rules/` 를 루트로 잡았다.

**How to apply:** 코어는 `RuleLoader.find_versions()/get_version()/set_version()/rule_dir()`,
`load`·`load_solver_rule`·`find_all_json`·`load_all` 은 `version` 인자를 받고 생략 시 현재 선택 버전을 쓴다.
UI 에서 새 코드를 붙일 땐 `self.current_version()` 을 넘길 것. 콤보를 채우는 코드는 `self.log()` 를
부르므로 로그 위젯 생성 뒤(`build_ui` 끝)에 호출하고, 채우는 동안 `blockSignals` 로 재진입을 막는다.
A00280 의 타겟 이름 규칙 문서가 아직 `rules_v01` 로 적혀 있을 수 있다 → [[metahuman-cloth-corrective-A00280]].
