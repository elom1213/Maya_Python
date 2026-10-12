---
name: wip-a00240-tree-omit
description: "A00240 Tree 탭 Omit(v01.18) — 루트 아래 N 단계를 `...` 한 줄로 생략, 가지 여럿이어도 `...` 은 하나, Adaptive 면 N 단계까지 즉시 읽기"
metadata:
  node_type: memory
  type: project
  originSessionId: f332ff00-a691-4c0f-97a1-ab3bba2197bb
  modified: 2026-10-12T00:14:04.191Z
---

A00240_PathTool v01.18 (2026-10-12) Tree 탭 **Omit** — Refresh 행 오른쪽 `Omit` 체크 + 스핀(2~99).
`A/B/C/D/E` 에서 Omit 2 = `A / ... / D / E`, 3 = `A / ... / E`.

**설계 결정 (사용자 예시는 일자 경로였고, 가지가 여럿일 때는 내가 정했다):**
- `...` 은 루트 아래 **하나**다. N+1 단계의 폴더·파일을 모든 가지에서 모아 그 밑에 단다. 출처는 항목
  툴팁(루트 기준 상대 경로 `B/C/D`). 생략 단계 안에서 끝나는 가지·그 단계의 파일은 **안 보인다**.
- `...` 항목은 경로 역할이 비어 있고 `ROLE_OMIT` 표식만 있다 → 더블클릭/우클릭 열기·복사 자동 차단.
  Filter 는 `...` 을 글자로 맞추지 않는다. 펼침·선택 보존은 `_item_key()` 가 `"..."` 열쇠를 준다.
- `...` 은 늘 펼쳐 둔다(접히면 루트+`...` 만 남는다).

**Why:**
- Adaptive 에선 생략 단계를 펼칠 수 없으니 `_ensure_omit_loaded()` 가 **항목을 만들기 전에**
  0~N 단계를 동기로 읽는다(새 확장자를 File Types 에 먼저 넣어야 걸러지지 않는다 — `_load_item` 과
  같은 순서). **N 단계까지 읽어야** 그 자식(N+1)이 보인다 — 처음에 `range(omit)` 로 한 단계 모자라
  `...` 밑이 비었다.
- 생략 단계 안의 폴더를 Refresh 하면(`...` 밑 파일 Selected) 그 항목이 화면에 없으므로
  **루트 자식을 통째로** 다시 만든다. 파일의 폴더는 부모 항목이 아니라 `dirname` 으로 찾는다.

**How to apply:** Omit 을 손댈 땐 `tree_tab.py` 의 `_add_omitted_children` · `_ensure_omit_loaded` ·
`_nodes_at_depth` · `_prefetch_children`(루트면 `...` 밑 노드) 네 곳이 한 세트. 검증은 오프스크린
PySide6 로 Omit 2/3 · 가지 여럿 · Refresh · Filter 를 돌리면 된다([[offscreen-size-needs-theme]]).
관련: [[wip-a00240-shrink-anim]] · [[wip-a00240-button-colors]].
