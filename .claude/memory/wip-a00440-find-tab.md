---
name: wip-a00440-find-tab
description: A00440_SetTool Find 탭 — 오브젝트가 속한 세트 역조회. listSets 는 트랜스폼/셰이프/컴포넌트가 각각 다르고 중복을 준다, 행 클릭이 세트를 고르도록 공용 TSL 에 select_no_expand 를 뒀다
metadata:
  node_type: memory
  type: project
---

`A00440_SetTool` **`Find` 탭** (v01.04, 2026-09-21). `Create` 가 세트를 만들고 `Edit` 가
세트를 다룬다면 `Find` 는 **거꾸로 묻는다** — "이 오브젝트들은 어느 세트에 들어 있나".
위 `Objects` TSL → `Find Sets` → 아래 `Sets` TSL. **씬은 바뀌지 않는다**(조회 전용).
`app/ui/find_tab.py` + `maya_sets.sets_of / parent_sets / shapes_of / is_default_set /
is_render_set` + `set_manager.run_find_sets`.

**`listSets` 실측 (mayapy 2024)** — 어디에 묻느냐로 답이 갈린다:

| 물어본 것 | 돌아온 것 |
|---|---|
| `listSets(o=<트랜스폼>)` | **트랜스폼이 들어간 세트만** |
| `listSets(o=<셰이프>)` | **컴포넌트 세트 · 셰이딩 그룹** (이쪽에 붙는다) |
| `listSets(o="pCube1.vtx[0]")` | **그 컴포넌트를 담은 세트만** — 같은 메시의 다른 컴포넌트 세트는 제외 |
| 면과 버텍스를 함께 담은 세트 | **두 번 나온다** → 중복 제거 필요 |
| `listSets(o="pCube1.tx")` | `None` |
| 없는 이름 | **TypeError** → 감싸야 한다 |

**★ `listRelatives(<세트>, shapes=True)` 는 세트를 펼쳐 멤버의 셰이프를 준다** — 에러가
아니라서 조용히 섞여 든다. `cmds.select` 가 세트를 펼치는 것과 같은 함정의 다른 얼굴
([[maya-set-rename-traps]]). → `objectType(isAType="dagNode")` 로 **먼저 거른다**.
셰이프는 `extendToShape` 대신 `listRelatives(shapes=True, noIntermediate=True)` 로
**전부** 본다([[extendtoshape-picks-wrong-shape]]).

**★ 공용 TSL 에 `select_no_expand` 를 새로 뒀다** — 세트를 담은 리스트는 행을 눌러도
세트가 아니라 멤버가 선택된다. 켜면 행 클릭이 `noExpand=True` 로 나가 **세트 노드 자체**를
고른다. 기본 OFF, 호출부 133곳이 전부 키워드 인자라 영향 없음. **`Edit` 탭은 켜지 않는다** —
그쪽 Split 은 "씬 선택 == A 의 멤버 전체" 를 사고 감지에 쓰고 있다([[wip-a00440-settool]]).

**필터** — `initialShadingGroup` 은 **렌더링 세트이면서 마야 기본 노드**다. 두 스위치가 서로를
막지 않도록 **렌더링 세트는 `Include shading groups` 하나로만** 판정하고, 기본 세트 스위치는
렌더링 세트가 아닌 것(`defaultLightSet` …)에만 건다. 기본 세트 판정은 이름 목록 +
`ls(defaultNodes=True)`. Maya 2024 는 **디포머가 세트를 만들지 않는다**(component tags) —
skinCluster/blendShape/lattice 를 걸어도 `ls(type="objectSet")` 가 늘지 않는다(실측).

**창 폭** — 긴 체크박스 라벨 하나("Include shading groups and other render sets")가 창 최소 폭을
531 → 615 로 밀어 올렸다. 라벨을 줄여 되돌림(Find 469 < Edit 493). 긴 설명은 툴팁으로
([[offscreen-size-needs-theme]]).

검증: mayapy 2024 헤드리스 41항목(코어 + 오프스크린 Qt UI). 마야 GUI 에서는 아직 안 눌러 봄.
관련: [[wip-a00440-settool]], [[mayapy-headless-verify]], [[framework-tsl-attach-uuids]]
