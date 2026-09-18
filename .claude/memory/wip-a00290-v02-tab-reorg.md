---
name: wip-a00290-v02-tab-reorg
description: "A00290_BSTool_V02 — V01 을 복제해 탭을 Shape/Target/Node 3카테고리 x 7기능 2단으로 재편(v02.00). Edit BS > Default 는 Node > Extract, 창은 620x1000 (가로 스크롤 없음)"
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
2. **창 폭을 좁히려면 "한 줄에 나란히 둔 것" 을 찾아 내려야 한다.** 버튼·라디오·라벨을 가로로
   늘어놓으면 **그 줄의 최소 폭이 그대로 창의 최소 폭**이 되고, **좌우 스플리터 안에 있으면 두 배**로
   올라온다. 자리만 내려(기능·라벨 그대로) `Mix Targets` 1092 → **573px**, `Naming` 792 → **498px**.
   최종 창은 **620 x 1000** 이고 **가로 스크롤이 전혀 없다**(처음엔 1400 x 1158 로 잡았다 — 그건
   테마 없이 잰 값이라 과했다, [[offscreen-size-needs-theme]]).
   ※ **세로는 반대로 움직인다** — 좁히면 글이 접혀 필요한 세로가 **늘어난다**(Shape Editor 918 ·
   Naming 894 · Mix Targets 756). 세로까지 없애려면 약 1195px 인데 1080p 화면에 안 들어가므로,
   화면에 들어가는 높이를 택하고 그 세 페이지는 세로 스크롤이 받게 뒀다(`QScrollArea` 를 쓴 이유).
   덤으로 V01 의 `win_width = 660` 이 **실현되지 않는 값**이었음이 드러났다(실제 최소 1118x925,
   `Mix Targets` 의 최소 폭 1092px 이 혼자 정하고 있었다).

**V01 과 동시에 뜬다** — 창 · 타겟 확장창 · **로그 확장창**의 `objectName` 이 전부 `_V02` 로
갈렸다(같으면 Expand 창이 서로를 찾아 닫는다 — [[framework-log-widget]]).
셸프 라벨 `BSToolV2`, 드롭 파일 `__dragDrop_A00290_V02.py`.

검증 25항목(mayapy + 오프스크린 Qt, 테마 적용) 통과. **마야 GUI 육안 확인은 아직.**
**v02.03 — `Target > Delete`** (2026-09-18): 체크한 타겟을 노드에서 지운다
(`app/core/delete_target_manager.py`). **직접 `removeMultiInstance` 하지 말고 MEL
`blendShapeDeleteTargetGroup(bs, idx)` 를 부른다** — 마야 Shape Editor 의 Delete 그 자체이고,
잎(`inputTargetItem` · `targetWeights`)부터 지워서 **undo 로 델타 · 인비트윈이 돌아온다**(mayapy 실측).
lock 된 weight 는 그 MEL 이 경고만 하고 0 을 돌려주므로 UI 에서 회색으로 잠갔다.
처음엔 `Target > Edit` 아래 `Naming` / `Delete` 두 겹으로 묶었는데, 사용자가 **3단 탭을 싫어해**
`Target` 바로 밑 한 겹(`Naming` · `Delete` · `Target Order`)으로 되돌렸다 — 탭은 2단까지만.

관련: [[wip-a00290-shape-editor-tab]], [[wip-a00290-naming-tab]], [[wip-a00290-target-order-tab]],
[[wip-a00290-mix-targets-tab]], [[wip-a00290-bake-delete-tab]]
