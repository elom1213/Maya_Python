---
title: A00290_BSTool_V02 사용법
aliases: [BS Tool V02, BSToolV2, BS툴 V02]
tags: [maya-python, tool-guide, blendshape, morph-target, ui, tabs]
updated: 2026-09-16
---

# A00290_BSTool_V02 사용법

`A00290_BSTool`(v01.23)을 그대로 복제한 뒤 **탭만 2단으로 재편한 버전**이다.
**기능은 하나도 바뀌지 않았다** — 각 기능의 사용법·원리·한계는 전부
[`A00290_BSTool.md`](A00290_BSTool.md) 에 있고, 이 문서는 **무엇이 어디로 갔는지**와
**V02 에서만 다른 것**만 적는다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (green_dark 테마)
- **버전**: `app/config/version.py` (v02.00)
- **설치**: `__dragDrop_A00290_V02.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **BSToolV2**
  → `tools.A00290_BSTool_V02.run(True)`
- **V01 과 동시에 띄울 수 있다** — 창 · 타겟 확장창 · 로그 확장창의 `objectName` 이 전부 갈렸다.
- 계획서: [`plans/A00290_BSTool_tab_reorg_plan.md`](plans/A00290_BSTool_tab_reorg_plan.md)

---

## 1. 왜 바꿨나

V01 은 상위 탭이 **6개인데 한 줄에 안 들어갔다.** 실측으로 탭 바가 필요로 하는 폭이
**1221 px**, 쓸 수 있는 폭이 **1096 px** 이라 **스크롤 화살표가 떠 있었다.**

그리고 **`Edit BS` 만 2단**이었는데, 그건 분류가 아니라 v01.21 에 `Naming` 을 넣을 자리가
없어서였다. 그래서 **`Naming`(이름 바꾸기)이 `Default`(타겟 꺼내기)와 한 상자에** 있었다 —
하는 일이 전혀 다르다. 규칙 없이 생긴 중첩이라 다음 기능도 같은 식으로 아무 데나 붙는다.

---

## 2. 새 구조 — 상위 = 카테고리 / 하위 = 기능

기준은 **"무엇을 바꾸는가"**(결과물)다. 조작 방식이나 대상 노드가 아니다.

| 상위 탭 | 뜻 | 하위 탭 |
|---|---|---|
| **Shape** | 타겟의 **모양(델타)** 이 바뀐다 — 끝나면 버텍스가 움직여 있다 | `Shape Editor` · `Base Shape` · `Mix Targets` |
| **Target** | **버텍스를 하나도 안 움직인다** — 바뀌는 것은 이름과 인덱스뿐 | `Naming` · `Target Order` |
| **Node** | 타겟 하나를 고르지 않는다 — **노드/리그를 통째로** 다룬다 | `Extract` · `Bake Delete` |

**툴을 켜면 `Shape > Shape Editor` 가 열린다** — V01 에서 처음 보이던 화면과 같다.
가장 흔한 경로에는 클릭이 하나도 늘지 않았다.

실측(테마 적용) — 탭 바가 필요로 하는 폭이 **1221 px → 최대 492 px** 로 내려갔다
(상위 276 · Shape 492 · Target 280 · Node 280). 여섯 개를 한 줄에 늘어놓던 때와 달리 여유가 많다.

---

## 3. 이동 매핑 — V01 의 어디가 V02 의 어디인가

| V01 | V02 | 라벨 |
|---|---|---|
| Shape Editor | **Shape > Shape Editor** | 그대로 |
| Base Shape | **Shape > Base Shape** | 그대로 |
| Mix Targets | **Shape > Mix Targets** | 그대로 |
| Edit BS > Naming | **Target > Naming** | 그대로 |
| Target Order | **Target > Target Order** | 그대로 |
| **Edit BS > Default** | **Node > Extract** | **바뀜 (아래 참고)** |
| Bake Delete | **Node > Bake Delete** | 그대로 |

**빠진 기능 없음. 합쳐진 기능 없음.** 이름이 바뀐 곳은 한 줄뿐이다.

### `Edit BS > Default` 가 `Node > Extract` 가 된 이유

`Naming` 이 `Target` 으로 가면서 `Edit BS` 상자가 없어졌는데, **`Default` 는 부모 탭 없이는
아무 뜻이 없는 이름**이다("기본" 이 무엇의 기본인지가 부모에 있었다). 이 페이지의 버튼 셋 —
`Key every target` · `Copy every target` · `Copy every frame` — 은 **전부 씬에서 무언가를
꺼내 만드는 일**이라 하는 일 그대로 이름을 붙였다.

하위 탭 툴팁에 `Extract (was Edit BS > Default)` 를 남겨 두었으므로, 옛 이름으로 찾아도 보인다.

---

## 4. V02 에서만 다른 것

### 4-1. 각 페이지가 `QScrollArea` 안에 있다

창을 줄여도 위젯이 겹치지 않는다. **기본 창 크기에서 가로 스크롤은 하나도 없다** — 아래 4-2 가
그렇게 정해진 값이다. 세로는 `Shape Editor` · `Naming` · `Mix Targets` 세 곳에서 스크롤이 받는다
(4-2 의 경고 참고).

### 4-2. 기본 창 크기 — 660 x 720(V01) → **620 x 1000**

V01 의 `660 x 720` 은 **실현되지 않는 값**이었다. 실제 최소 크기가 **1118 x 925** 였고,
`Mix Targets` 의 최소 폭 **1092 px** 이 그것을 혼자 정하고 있었다.

V02 는 **가로 620 px** 에서 **일곱 페이지 어디에도 가로 스크롤이 없다.** 두 가지를 했다.

**① 테마를 입히고 쟀다.** 테마 qss 가 `font-size: 12px` 를 주므로 위젯 최소 폭이 확 줄어든다 —
가장 넓은 페이지 기준 **1092 → 809 px**. 처음에 잡았던 1400 폭은 **테마 없이 잰 값**이라 과했다.

**② 한 줄에 나란히 있던 것들을 내렸다.** 그런 줄의 최소 폭은 그대로 창의 최소 폭이 되고,
좌우 스플리터 안에 있으면 **두 배로** 올라온다. **기능·버튼·라벨은 하나도 안 바뀌고 자리만** 바뀌었다.

| 페이지 | 무엇을 내렸나 | 최소 폭 |
|---|---|---:|
| Mix Targets | `Set to Selected` · `Use Scene Weights` · `Uncheck All` 을 **한 줄씩** · `Checked:` / `Number:` 라벨을 제 줄로 · `Base mesh` 라벨을 라디오 위로 | 1092 → **573** |
| Naming | `Set Name` / `Search & Replace` / `Prefix / Suffix` 라디오를 **2줄 그리드**로 | 792 → **498** |

> ⚠️ **세로는 반대로 움직인다.** 좁히면 글이 접혀 **필요한 세로가 늘어난다** —
> `Shape Editor` 918 · `Naming` 894 · `Mix Targets` 756 px. 세로 스크롤까지 없애려면 창이
> 약 **1195 px** 이어야 하는데 그건 1080p 모니터에 안 들어간다. 그래서 **화면에 들어가는 높이**
> (1000)를 택했고, 그 세 페이지는 **세로 스크롤**이 받는다 — 페이지를 `QScrollArea` 에 담아 둔
> 것이 그래서다. 모니터가 충분히 크면 `self.win_height` 를 1195 로 올리면 세로 스크롤도 사라진다.

### 4-3. Shape Editor 의 weight 폴링이 고쳐졌다

V01 은 타이머를 켤지를 **상위 탭 인덱스**로 판단했다(`tabs.currentIndex() == 0`).
2단으로 묶으면 인덱스 0 은 **"Shape 카테고리"** 가 되므로

- `Base Shape` · `Mix Targets` 를 보고 있어도 **타이머가 계속 돈다**(타겟 행마다 `getAttr` 를
  주기적으로 부르는 낭비 — 타겟이 수백 개면 무시할 수 없다),
- 나중에 카테고리 순서를 바꾸면 반대로 조건이 영영 거짓이 되어 **슬라이더가 씬을 안 따라간다.**

**둘 다 에러가 나지 않아** 눈으로 보기 전엔 모른다. V02 는 `_shape_editor_visible()` 이
**위젯 동일성**으로 판단하고, 상위·하위 **두 탭 위젯의 시그널을 모두** 받는다
(하위만 바뀌는 전환에서는 상위 시그널이 오지 않는다).

`Expand` 로 타겟 목록을 별도 창에 띄워 둔 동안에는 **어느 탭에 있든 타이머가 돈다** — V01 과 같다.

---

## 5. 구조

```
A00290_BSTool_V02/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(reload): MainWindow → show
├── __dragDrop_A00290_V02.py    # 셸프 설치 (TOOL_LABEL = "BSToolV2")
├── CHANGELOG.md
├── icon/                       # A00290_BSTool_V02.svg / .png
└── app/
    ├── config/version.py       # VERSION = "02.00"
    ├── core/                   # V01 과 **같은 로직** (복제, 수정 없음)
    └── ui/main_window.py       # 탭 재편이 일어난 유일한 파일
```

- **`app/core/*` 는 V01 과 한 글자도 다르지 않다**(모듈 헤더 주석의 툴 이름만 바뀌었다).
  탭 재편은 **UI 를 묶기만** 한 작업이고, 기존 `_build_*_tab()` 일곱 개는 건드리지 않았다.
- 분류표는 `MainWindow.CATEGORIES` · `SHAPE_PAGES` · `TARGET_PAGES` · `NODE_PAGES` 에 있다.
  **탭을 더하려면 그 표에 한 줄을 넣으면 된다.**

---

## 6. 검증 (mayapy 2024 + 오프스크린 Qt)

**25항목 통과.**

- 상위 탭이 `Shape` / `Target` / `Node` 이고 하위 7개가 3장 매핑과 일치 · 옛 `tabs_edit_bs` 소멸
- 탭별 대표 위젯 20개가 **스크롤 래핑 뒤에도** 전부 살아 있음
  (`tsl_se_nodes` · `le_bs_node` · `le_mix_node` · `le_nm_node` · `tsl_to_targets` ·
  `tsl_bs_nodes` · `te_bd_report` …)
- 일곱 페이지가 전부 `QScrollArea` 안에 있고, **기본 크기에서 가로 스크롤바가 하나도 안 보임** ·
  폭이 이전(1400)의 절반 이하
- 상위·하위 탭 바가 전부 창 폭 안에 들어감
- **weight 폴링 타이머 7항목** — Shape Editor 에서만 돌고(①⑥), Base Shape · Mix Targets ·
  Target · Node 에서는 멈추며(②③④⑤), **Expand 창이 떠 있으면 어느 탭이든 돈다**(⑦)
- V01 과 `objectName` 이 전부 갈림(창 · 타겟창 · 로그 확장창)

> 실제 Maya GUI 육안 확인은 아직이다.
