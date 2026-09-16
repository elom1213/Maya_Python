---
name: wip-a00290-v02-tab-reorg
description: "A00290_BSTool_V02 — V01 을 복제해 탭을 Shape/Target/Node 3카테고리 x 7기능 2단으로 재편(v02.00). Edit BS > Default 는 Node > Extract 가 됐고, 창 기본 크기는 스크롤이 안 뜨는 1400x1158"
metadata:
  node_type: memory
  type: project
---

`A00290_BSTool_V02` 는 **V01(v01.23)을 통째로 복제해 탭만 재편한** 툴이다(v02.00, 2026-09-16).
**기능은 하나도 다르지 않다** — `app/core/*` 는 모듈 헤더의 툴 이름만 바뀌었고, 기존
`_build_*_tab()` 일곱 개도 손대지 않았다. **묶기만** 했다.
계획서 `docs/plans/A00290_BSTool_tab_reorg_plan.md`, 문서 `docs/A00290_BSTool_V02.md`.

**★ 어디가 어디로 갔나** — 기존 `wip-a00290-*` 메모들이 말하는 탭 경로는 **V01 기준**이다.
V02 에서는 이 표로 옮겨 읽는다.

| V01 | V02 |
|---|---|
| Shape Editor | **Shape > Shape Editor** |
| Base Shape | **Shape > Base Shape** |
| Mix Targets | **Shape > Mix Targets** |
| Edit BS > Naming | **Target > Naming** |
| Target Order | **Target > Target Order** |
| **Edit BS > Default** | **Node > Extract** ← 이름이 바뀐 유일한 곳 |
| Bake Delete | **Node > Bake Delete** |

분류 기준은 **"무엇을 바꾸는가"** — `Shape`(모양/델타가 바뀐다) · `Target`(버텍스는 안 움직이고
이름·인덱스만) · `Node`(타겟 하나를 안 고르고 노드/리그를 통째로). 분류표는
`MainWindow.CATEGORIES` · `SHAPE/TARGET/NODE_PAGES` 에 있고 **탭 추가는 표에 한 줄**이다.
`Default` 를 `Extract` 로 바꾼 것은 `Edit BS` 상자가 없어지면 **"Default" 가 부모 없이는 뜻이
없는 이름**이기 때문이다(툴팁에 `was Edit BS > Default` 를 남겼다).

**★ 이 재편에서 실제로 밟은 것 두 가지**

1. **탭 인덱스로 타이머를 켜던 코드가 조용히 깨진다.** V01 은 Shape Editor 의 weight 폴링을
   `tabs.currentIndex() == SHAPE_EDITOR_TAB(0)` 으로 켰다. 2단으로 묶으면 인덱스 0 은
   **"Shape 카테고리"** 가 되어 Base Shape/Mix Targets 에서도 계속 돌고, 카테고리 순서를 바꾸면
   반대로 영영 안 돈다. **둘 다 에러가 안 난다.** → 위젯 동일성(`_shape_editor_visible()`)으로
   판단하고 **상위·하위 두 탭 위젯의 시그널을 모두** 받는다(하위만 바뀌는 전환은 상위 시그널이
   안 온다). [[prefer-subtabs-over-stacked-collapsibles]] 작업에서 반복되는 함정이다.
2. **스크롤이 안 뜨는 창 크기는 폭만으로 못 만든다.** 폭을 넓히면 `Shape Editor` 가 필요로 하는
   세로가 959 → **839px 에서 바닥을 친다**(1400 을 넘겨도 안 줄어든다). 그래서 세로도 키워
   **1400 x 1158** 이 되었고, 폭을 1500·1700 으로 해도 필요한 세로는 1144 밑으로 안 내려간다.
   ※ **1158 은 1080p 모니터에 안 들어간다** — 그때는 `Shape Editor` · `Naming` 에 세로 스크롤이
   생긴다(페이지를 `QScrollArea` 에 담아 둔 이유). 줄이려면 `win_width`/`win_height` 두 줄만.
   덤으로 V01 의 `win_width = 660` 이 **실현되지 않는 값**이었음이 드러났다(실제 최소 1118x925,
   `Mix Targets` 의 최소 폭 1092px 이 혼자 정하고 있었다).

**V01 과 동시에 뜬다** — 창 · 타겟 확장창 · **로그 확장창**의 `objectName` 이 전부 `_V02` 로
갈렸다(같으면 Expand 창이 서로를 찾아 닫는다 — [[framework-log-widget]]).
셸프 라벨 `BSToolV2`, 드롭 파일 `__dragDrop_A00290_V02.py`.

검증 24항목(mayapy + 오프스크린 Qt) 통과. **마야 GUI 육안 확인은 아직.**
관련: [[wip-a00290-shape-editor-tab]], [[wip-a00290-naming-tab]], [[wip-a00290-target-order-tab]],
[[wip-a00290-mix-targets-tab]], [[wip-a00290-bake-delete-tab]]
