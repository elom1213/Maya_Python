---
title: A00290_BSTool 탭 재분류 계획서 (상위 탭 → 하위 탭)
aliases: [A00290 탭 정리, BSTool tab reorg, BS툴 탭 재분류]
tags: [plan, maya-python, A00290, bstool, blendshape, ui, tabs]
updated: 2026-09-16
---

# A00290_BSTool — 탭 · 하위 탭 재분류 계획서

> **목적**: 기능은 **하나도 바꾸지 않고** 평평한 상위 탭 6개(실제 페이지 7개)를
> **카테고리 3 → 기능 7** 의 2단 구조로 다시 나눈다. 코드는 "옮기기" 가 아니라 **"묶기"** 만 한다.

- **작성일**: 2026-09-16
- **대상**: `tools/A00290_BSTool_V02/app/ui/main_window.py` (UI 전용 — `app/core/*` 는 손대지 않는다)
- **상태**: **적용 완료 — `A00290_BSTool_V02` v02.00 (2026-09-16).** 11장 1~7단계 끝,
  8단계(사용자 Maya 확인) 대기. 사용자가 정한 것 —
  **6-1 은 A(`Extract`)**, **6-5 는 A(감싼다) + "스크롤이 안 생기게 창을 키운다"**,
  그리고 **6-6 과 달리 V02 폴더로 갈랐다**(사용자 지시).
  6-5 실측: 폭만으로는 안 된다 — 폭을 넓히면 `Shape Editor` 가 필요로 하는 세로가
  959 → 839px 로 줄지만 **839 에서 바닥을 친다**. 스크롤이 하나도 없는 최소 크기는
  **1400 x 1158** 이고, 폭을 1500·1700 으로 넓혀도 필요한 세로는 1144 밑으로 안 내려간다.
  ※ 1158 은 1080p 모니터에 안 들어간다 — 그때는 `Shape Editor` · `Naming` 에 세로 스크롤이
  생긴다(스크롤 영역에 담아 둔 이유).
  결과 문서: [`A00290_BSTool_V02.md`](../A00290_BSTool_V02.md)
- **버전**: 계획 시점의 안은 제자리 `v01.23 → v01.24` 였으나, 실제로는 사용자 지시로
  **새 폴더 `A00290_BSTool_V02` 의 v02.00** 이 되었다(6-6 참고). V01 은 그대로 남는다.
- **선례**: [A00275_skinTool_V01 탭 재분류 계획서](A00275_skinTool_V01_tab_reorg_plan.md) ·
  [A00110_animTool 탭 재분류 계획서](A00110_animTool_tab_reorg_plan.md). 구현 골격은
  `A00275_skinTool_V01` 의 `CATEGORIES` / `_build_sub_tabs` / `_scrolled` 를 그대로 따른다.

---

## 1. 문제 — 탭 바가 **이미 넘쳤다** (실측)

`mayapy` + 오프스크린 Qt 로 실제 창을 띄워 재 봤다.

| 잰 것 | 값 |
|---|---:|
| 상위 탭 바가 **필요로 하는 폭** | **1221 px** |
| 그 창에서 탭 바가 **쓸 수 있는 폭** | **1096 px** |
| 차이 | **-125 px** → **스크롤 화살표가 뜬다** |

탭별 폭은 `Shape Editor` 229 · `Edit BS` 144 · `Base Shape` 195 · `Mix Targets` 212 ·
`Target Order` 229 · `Bake Delete` 212 px 다. **여섯 개가 한 줄에 안 들어간다.**
기능이 하나 더 붙으면 더 나빠진다 — 이 툴은 최근 여섯 버전에서 상위 탭이 **네 개 늘었다**
(v01.17 Mix Targets · v01.19 Bake Delete · v01.20 Target Order · v01.21 Naming 하위 탭).

### 그리고 층이 어긋나 있다

지금 구조는 **6개 중 하나만** 2단이다.

```
[Shape Editor] [Edit BS] [Base Shape] [Mix Targets] [Target Order] [Bake Delete]
                   └ [Default] [Naming]          ← 여기만 하위 탭이 있다
```

`Edit BS` 만 하위 탭을 갖는 이유는 분류가 아니라 **v01.21 에 Naming 을 넣을 자리가 없어서**였다.
그래서 `Naming`(타겟 이름 바꾸기)이 `Default`(타겟을 메시로 꺼내기)와 한 상자에 들어가 있다 —
**둘은 하는 일이 전혀 다르다.** 규칙 없이 생긴 중첩이라, 다음 기능도 같은 식으로 아무 데나 붙는다.

### 덤으로 드러난 것 (이 작업의 범위는 아니다)

`win_width = 660` · `win_height = 720` 은 **실현되지 않는 값**이다. 창의 실제 최소 크기는
**1118 x 925** 이고, `resize(660, 720)` 을 불러도 그만큼 줄어들지 않는다.

| 페이지 | 최소 폭 |
|---|---:|
| **Mix Targets** | **1092 px** ← 창 최소 폭을 혼자 정하고 있다 |
| Edit BS | 796 px |
| Shape Editor | 579 px |
| Target Order | 538 px |
| Base Shape | 465 px |
| Bake Delete | 434 px |

이 값은 6-5(스크롤)에서 한 번 더 다룬다.

---

## 2. 현재 기능 전수 (페이지 7개) — 하나도 빠뜨리지 않는다

| # | 위치 | 빌더 메서드 | 무엇을 바꾸나 | 대표 위젯 |
|---|---|---|---|---|
| 1 | Shape Editor | `_build_shape_editor_tab` | 타겟을 **열어 손으로** 고친다(Edit 토글) · weight 조절 | `tsl_se_nodes` · `flt_se` · `lbl_se_number` |
| 2 | Edit BS > Default | `_build_edit_bs_default_tab` | **아무것도 안 바꾼다** — 타겟을 키/메시로 **꺼낸다** | `tsl_bs_nodes` · `le_copy_start` · `le_copy_end` |
| 3 | Edit BS > Naming | `_build_naming_tab` | 타겟 **이름**(weight 별칭) | `le_nm_node` · `le_nm_prefix` · `btn_nm_apply` |
| 4 | Base Shape | `_build_base_shape_tab` | 타겟 **델타를 스케일**(value → 1.0 재정의) | `le_bs_node` · `flt_targets` · `lbl_tgt_number` |
| 5 | Mix Targets | `_build_mix_tab` | 타겟 **델타에 가중합을 더한다** | `le_mix_node` · `flt_mix_src` · `flt_mix_dest` |
| 6 | Target Order | `_build_target_order_tab` | 타겟 **순서**(weight 인덱스) | `le_to_node` · `tsl_to_targets` · `btn_to_apply` |
| 7 | Bake Delete | `_build_bake_delete_tab` | **리그 전체** — deleteComponent 를 체인 앞으로, 히스토리 재구성 | `le_bd_mesh` · `te_bd_report` · `lbl_bd_warn` |

**공통**: 하단 로그(`te_log`, 공용 `JUN_mod_log_qt_v01`)는 모든 탭이 공유한다 — 재분류 뒤에도
탭 바깥에 그대로 둔다.

**탭 인덱스에 의존하는 코드는 딱 한 군데** — 8장에서 따로 다룬다.
`SHAPE_EDITOR_TAB = 0` (85행) 과 `self.tabs.currentIndex() == SHAPE_EDITOR_TAB` (609행).

---

## 3. 분류 원칙

1. **상위 탭 = 카테고리, 하위 탭 = 기능.** 예외를 두지 않는다. 상위 탭에 "기능 하나" 를 직접
   올리지 않는다 — 지금 `Edit BS` 만 2단인 그 예외가 이번 문제를 만들었다.
2. 기준은 **"무엇을 바꾸는가"**(결과물). 조작 방식이나 대상 노드가 아니다.
3. **하위가 하나뿐인 카테고리도 하위 탭 바를 둔다**(A00275 와 같은 규칙). 지금은 해당 없다.
4. **라벨은 지금 이름 그대로.** 딱 한 곳만 예외이고, 그 예외는 6-1 에서 따로 결정한다.

---

## 4. 새 구조 (권장안) — 상위 3 / 하위 7

```
┌ BS Tool V02 v02.00 ─────────────────────────────────────┐
│ [ Shape ] [ Target ] [ Node ]                           │  ← 상위 = 카테고리
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [ Shape Editor ] [ Base Shape ] [ Mix Targets ]     │ │  ← 하위 = 기능
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │   (기존 탭 내용 그대로)                          │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌ Log ────────────────────────────────────────────────┐ │  ← 탭 바깥, 공유
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

| 상위 탭 | 뜻 | 하위 탭 |
|---|---|---|
| **Shape** | 타겟의 **모양(델타)** 을 바꾼다 | `Shape Editor` · `Base Shape` · `Mix Targets` |
| **Target** | 모양은 그대로 두고 **타겟의 이름·순서**를 정리한다 | `Naming` · `Target Order` |
| **Node** | 타겟 하나가 아니라 **blendShape 노드/리그를 통째로** 다룬다 | `Extract`(구 Edit BS > Default) · `Bake Delete` |

상위 탭 툴팁(영어, UI 문자열 규칙):

- **Shape** — "Change what a target looks like."
- **Target** — "Rename or reorder targets. No shape changes."
- **Node** — "Work on the whole blendShape node - pull targets out, or bake a topology change into the rig."

### 왜 이 셋인가

- **Shape** 의 셋은 *어떻게* 고치느냐만 다르다 — 손으로(Shape Editor) · 배율로(Base Shape) ·
  다른 타겟을 섞어서(Mix Targets). 셋 다 끝나면 **버텍스가 움직여 있다.**
- **Target** 의 둘은 **버텍스를 하나도 안 움직인다.** 바꾸는 것은 이름과 인덱스, 즉 목록의 메타데이터다.
  `Naming` 이 지금 `Default` 와 한 상자에 있는 것이 이 재분류로 풀리는 가장 큰 오분류다.
- **Node** 의 둘은 **타겟 하나를 고르지 않는다.** `Extract` 는 노드를 **여러 개** 받아 전 타겟을
  한꺼번에 꺼내고, `Bake Delete` 는 보이는 메시를 받아 디포머 체인을 다시 세운다.

### 왜 이 순서인가

`Shape → Target → Node` 는 **왼쪽이 가장 자주 쓰는 것**이다. 그리고 `Shape Editor` 가
**첫 카테고리의 첫 하위 탭**이므로 **툴을 켜면 지금과 똑같이 Shape Editor 가 열린다** —
가장 흔한 경로에는 클릭이 하나도 늘지 않는다.

### 실측 — 폭 문제는 해소된다

| 탭 바 | 필요 폭 |
|---|---:|
| 상위 `Shape` / `Target` / `Node` | **330 px** |
| 하위 Shape (3개) | 636 px |
| 하위 Target (2개) | 356 px |
| 하위 Node (2개) | 356 px |

지금 한 줄이 필요로 하던 **1221 px** 이 **최대 636 px** 로 내려간다. 현재 창 폭(1096 px 가용)에서
**전부 여유 있게 들어간다.**

---

## 5. 이동 매핑 (기존 7개 — 전부 자리 있음)

| 기존 위치 | 새 위치 | 라벨 변경 |
|---|---|---|
| Shape Editor | **Shape > Shape Editor** | 없음 |
| Base Shape | **Shape > Base Shape** | 없음 |
| Mix Targets | **Shape > Mix Targets** | 없음 |
| Edit BS > Naming | **Target > Naming** | 없음 |
| Target Order | **Target > Target Order** | 없음 |
| Edit BS > Default | **Node > Extract** | **있음 → 6-1 에서 결정** |
| Bake Delete | **Node > Bake Delete** | 없음 |

**빠지는 기능 없음. 합쳐지는 기능 없음.** 이름이 바뀌는 곳은 위 한 줄뿐이다.

---

## 6. 판단이 갈리는 지점 → 권장안

### 6-1. ★ `Edit BS > Default` 의 이름 — **결정이 필요하다**

`Naming` 이 `Target` 으로 가면 `Edit BS` 상자에는 `Default` 만 남는다. 그런데
**`Default` 는 홀로 서면 아무 뜻이 없는 이름**이다("기본"이 무엇의 기본인지가 부모 탭에 있었다).
세 가지 중 하나를 골라야 한다.

| 안 | 새 라벨 | 장점 | 단점 |
|---|---|---|---|
| **A (권장)** | `Node > **Extract**` | 하는 일 그대로다 — Key every target · Copy every target · Copy every frame 은 **전부 꺼내기**다 | 문서·메모리의 "Edit BS 탭" 이라는 말이 과거형이 된다 |
| B | `Node > **Edit BS**` | 옛 이름을 지킨다(원칙 4) | `Edit BS` 는 **무엇을 하는지 말해 주지 않는다**. 게다가 이제 이 툴 전체가 "BS 를 Edit" 한다 |
| C | 카테고리를 `Edit BS` 로 | 이름이 완전히 보존된다 | `Bake Delete` 를 `Edit BS` 밑에 넣는 것이 어색하고, 카테고리 이름만 옛 기능 이름이라 층이 다시 어긋난다 |

→ **A 를 권한다.** `Default` 는 원래 "부모 이름 + Default" 로만 읽히던 임시 이름이고, 이 페이지의
버튼 셋은 전부 "씬에서 무언가를 꺼내 만든다". 다만 **옛 이름을 아는 사람이 헤매지 않도록**
- 하위 탭 툴팁에 `"Extract (was Edit BS > Default) - key every target, copy targets or frames to meshes."`
- 문서·CHANGELOG 의 이동 매핑 표(5장)에 한 줄
을 남긴다.

> **B 를 고르면** 5장 매핑에서 라벨 변경이 사라져 "이름 바뀌는 기능 없음" 이 완성된다.
> 보수적으로 가고 싶으면 B 도 충분히 방어된다 — **사용자가 정한다.**

### 6-2. 3분류 대신 4분류(`Extract` 를 독립 카테고리로)는 어떤가

| 안 | 배분 |
|---|---|
| 3분류(권장) | Shape 3 / Target 2 / **Node 2** |
| 4분류 | Shape 3 / Target 2 / **Extract 1** / **Rig 1** |

4분류는 카테고리 둘이 **하위 하나짜리**가 되어, 상위 탭 6개를 4개로 줄이는 데 그친다
(탭 바 330 → 457 px). 줄이려는 문제를 절반만 푼다. **채택하지 않는다.**

### 6-3. 다른 분류축 — "대상별"(Target / Node / Mesh) 은 왜 안 쓰나

| 대상축 | 배분 |
|---|---|
| 타겟 하나 | Shape Editor, Base Shape, Mix Targets, Naming, Target Order |
| 노드 전체 | Extract |
| 메시 | Bake Delete |

**5 / 1 / 1** 로 심하게 기운다. 그리고 "타겟 하나" 칸 안에서 **모양을 바꾸는 것과 이름만 바꾸는
것이 섞인다** — 지금 `Naming` 이 겪고 있는 문제가 그대로 남는다. **채택하지 않는다.**

### 6-4. `Shape Editor` 를 상위에 그대로 두면 안 되나

가장 자주 쓰는 탭이고 가장 크다(페이지 높이 839 px). 그러나 **원칙 1의 예외를 다시 만드는 것**이고,
4장에서 적었듯 **첫 카테고리의 첫 하위 탭**이면 툴을 켤 때 열리는 화면은 지금과 같다.
클릭이 느는 것은 "다른 탭을 보다가 Shape Editor 로 돌아올 때" 뿐이고, 그때도 **한 번**이다.
→ **하위로 내린다.**

### 6-5. ★ 페이지를 `QScrollArea` 로 감쌀 것인가 — **결정이 필요하다**

A00275 는 감쌌다. 여기는 **감싸면 1장에서 드러난 최소 크기 문제까지 같이 풀린다.**

- 지금은 `Mix Targets` 의 최소 폭 **1092 px** 이 창 전체의 최소 폭을 정해, `win_width = 660` 이
  무시되고 창이 **1118 px 밑으로 안 줄어든다.**
- 페이지를 스크롤 영역에 담으면 스크롤 영역 자체의 최소 크기는 작으므로 **창을 의도한 660 까지
  줄일 수 있게 된다.** 대신 `Mix Targets` 에는 **가로 스크롤바가 생긴다.**

| 안 | 결과 |
|---|---|
| **A (권장)** 감싼다 | 창을 작게 쓸 수 있다. 좁힐 때 `Mix Targets` 에 가로 스크롤 |
| B 안 감싼다 | 지금과 같은 최소 크기(1118 x 925) 유지. 중첩 탭 바 한 줄(약 29 px)만큼 세로가 더 필요 |

→ **A 를 권한다.** 다만 이것은 **재분류와 별개의 체감 변화**이므로, 한 커밋에 섞지 말고
**스크롤 적용을 두 번째 커밋**으로 나눈다(문제가 생기면 그것만 되돌린다).
`Mix Targets` 의 1092 px 최소 폭 자체를 줄이는 것은 **이 계획서의 범위가 아니다** — 별도 안건.

### 6-6. `V02` 로 폴더를 가를까

계획 시점의 권장은 **가르지 않는다**였다 — UI 묶기뿐이라 되돌릴 일이 생겨도 커밋 하나를
되돌리면 되기 때문이다.

> **실제로는 사용자가 `A00290_BSTool_V02` 로 가르라고 지시해 그렇게 했다.** V01 이 그대로
> 남으므로 되돌릴 일 자체가 없고, 두 버전을 나란히 띄워 비교할 수 있다. 대신 **동시에 뜰 수
> 있으므로 `objectName` 이 전부 갈려야 한다** — 창 · 타겟 확장창 · **로그 확장창** 셋 다.
> (같으면 Expand 창이 서로를 찾아 닫는다.)

---

## 7. 구현 방식 — "묶기만" 한다

**기존 `_build_*_tab()` 7개는 이름도 내용도 건드리지 않는다.** 이것이 회귀를 막는 가장 큰
안전장치다. 새로 쓰는 것은 골격 셋과 분류표뿐이다 — `A00275_skinTool_V01` 의 코드를 그대로 따른다.

```python
# app/ui/main_window.py

# (하위 탭 라벨, 툴팁, 빌더 메서드 이름)
SHAPE_PAGES = (
    ("Shape Editor", "Shape Editor - list every target of a blendShape node and "
     "toggle Edit on any of them", "_build_shape_editor_tab"),
    ("Base Shape", "Base Shape - redefine the shape seen at a given weight as the "
     "new weight=1.0 shape", "_build_base_shape_tab"),
    ("Mix Targets", "Mix Targets - add a weighted mix of source targets onto other "
     "targets", "_build_mix_tab"),
)
TARGET_PAGES = (
    ("Naming", "Naming - rename target aliases in bulk (these become the morph "
     "target names in Unreal)", "_build_naming_tab"),
    ("Target Order", "Target Order - change the real target order (weight index) of "
     "the node", "_build_target_order_tab"),
)
NODE_PAGES = (
    ("Extract", "Extract (was Edit BS > Default) - key every target, copy targets or "
     "frames to meshes", "_build_edit_bs_default_tab"),
    ("Bake Delete", "Bake Delete - move a deleteComponent to the front of the chain "
     "so the whole rig shrinks with it", "_build_bake_delete_tab"),
)

# (상위 탭 라벨, 툴팁, 하위 페이지 표, 하위 QTabWidget 을 담을 속성 이름)
CATEGORIES = (
    ("Shape", "Change what a target looks like.", SHAPE_PAGES, "shape_tabs"),
    ("Target", "Rename or reorder targets. No shape changes.",
     TARGET_PAGES, "target_tabs"),
    ("Node", "Work on the whole blendShape node - pull targets out, or bake a "
     "topology change into the rig.", NODE_PAGES, "node_tabs"),
)
```

`build_ui()` 의 `addTab` 6줄이 루프로 바뀐다.

```python
self.tabs = QTabWidget()
for label, tip, pages, attr in self.CATEGORIES:
    index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
    self.tabs.setTabToolTip(index, tip)
self.tabs.currentChanged.connect(lambda *_a: self._update_se_timer())
self.shape_tabs.currentChanged.connect(lambda *_a: self._update_se_timer())   # ★ 8장
main_layout.addWidget(self.tabs)
```

**지워지는 것**: `_build_edit_bs_tab()`(하위 탭 두 개를 담기만 하던 껍데기)과 `self.tabs_edit_bs`.
`tabs_edit_bs` 를 참조하는 다른 코드는 **없다**(생성부 4줄이 전부 — grep 확인).

---

## 8. ★ 가장 큰 리스크 — Shape Editor 의 **폴링 타이머가 조용히 어긋난다**

**이 항목이 이 작업의 핵심 위험이다.** Shape Editor 는 씬의 weight 를 슬라이더에 되비추려고
타이머로 폴링하는데, **그 타이머를 켤지 말지를 상위 탭 인덱스로 판단한다.**

```python
SHAPE_EDITOR_TAB = 0                                     # 85행

def _update_se_timer(self):                              # 605행~
    expanded = self._se_window is not None and self._se_window.isVisible()
    active = bool(self._se_rows) and (
        expanded
        or (self.isVisible() and self.tabs.currentIndex() == SHAPE_EDITOR_TAB))   # 609행
```

중첩하면 `currentIndex() == 0` 은 **"Shape 카테고리가 열려 있다"** 가 된다. 그래서

- `Base Shape` · `Mix Targets` 를 보고 있어도 **타이머가 계속 돈다** — 타겟 행마다
  `cmds.getAttr` 을 주기적으로 부르는 낭비다(타겟이 수백 개면 무시할 수 없다).
- 반대로 나중에 **카테고리 순서를 바꾸면** 조건이 영영 거짓이 되어 **슬라이더가 씬을 안 따라간다.**
- **어느 쪽도 에러가 나지 않는다.** 눈으로 보기 전엔 모른다.

### 권장 수정 — 인덱스 비교를 없애고 "지금 보이는 페이지" 로 판단

```python
def _shape_editor_visible(self):
    """Shape Editor 페이지가 실제로 화면에 있는가.

    인덱스가 아니라 **위젯 동일성**으로 본다 - 인덱스는 탭이 늘고 줄면 의미가 변한다.
    """
    return (self.tabs.currentWidget() is self.shape_page
            and self.shape_tabs.currentWidget() is self.se_page)

def _update_se_timer(self):
    expanded = self._se_window is not None and self._se_window.isVisible()
    active = bool(self._se_rows) and (
        expanded or (self.isVisible() and self._shape_editor_visible()))
    ...
```

- `SHAPE_EDITOR_TAB` 상수는 **지운다**(남겨 두면 다음 사람이 또 쓴다).
- **상위·하위 두 `QTabWidget` 의 `currentChanged` 를 모두** `_update_se_timer` 에 연결해야 한다.
  하위만 바뀌는 전환(예: Shape Editor → Base Shape)은 상위 시그널이 **안 온다.**
- 6-5 에서 스크롤을 채택하면 `self.se_page` 는 `QScrollArea` **래퍼**를 가리켜야 한다
  (`tabs.widget(i)` 가 돌려주는 것이 래퍼다). 헷갈리기 쉬우므로 `_build_sub_tabs` 가 만든 래퍼를
  그대로 보관하거나, `SHAPE_PAGES` 순서에 맞춘 상수(`SE_SUB = 0`)로 `shape_tabs.widget(SE_SUB)` 를
  쓰는 편이 단순하다 — **구현 시 후자를 권장**한다.

---

## 9. 그 밖의 리스크와 대응

| # | 리스크 | 대응 |
|---|---|---|
| 9-1 | 스크롤로 감싸면 `tabs.widget(i)` 가 페이지가 아니라 `QScrollArea` 다 | 페이지를 위젯으로 찾는 코드는 **8장 하나뿐**(grep 완료). 새로 만들지 않는다 |
| 9-2 | **이중 스크롤** — 상위 페이지에도 스크롤을 씌우면 스크롤바가 두 겹 | 스크롤은 **하위 페이지에만**. 상위 카테고리 페이지는 `QTabWidget` 자체를 그대로 돌려준다 ([[prefer-subtabs-over-stacked-collapsibles]]) |
| 9-3 | 중첩 탭 바가 세로를 한 줄(**29 px** 실측) 더 먹는다 | 페이지 최대 높이가 866 px 이고 창 최소 높이가 925 px 라 **지금도 여유가 있다**. 6-5 A 를 택하면 스크롤이 받는다 |
| 9-4 | `Shape Editor` 의 **Expand 창**(별도 창으로 타겟 목록) 이 중첩과 엮인다 | Expand 창이 떠 있으면 타이머는 탭과 무관하게 돌아야 한다 — 8장 수정안이 `expanded` 를 그대로 앞에 두므로 **동작이 같다.** 검증 항목에 넣는다 |
| 9-5 | 테마 qss(`green_dark` 등)가 중첩 `QTabWidget` 을 예상하지 않았을 수 있다 | 실제 Maya 에서 눈 확인. 필요하면 qss 는 **건드리지 않고** 하위 탭에 `setObjectName` 을 주는 선에서 |
| 9-6 | TSL·Filter 위젯이 스크롤 안에서 높이를 잃는다 | **TSL 위젯 전체에 `setMaximumHeight` 를 걸지 않는다** — 리스트 최소 높이가 안 줄어 버튼에서 높이를 빼앗아 글자가 잘린다 ([[tsl-widget-max-height-squeezes-buttons]]). 필요하면 `list_widget` 에만 |
| 9-7 | `Bake Delete` 의 `te_bd_report` 는 고정폭 폰트 · `NoWrap` 독립 뷰다 | 로그가 아니므로 **공용 로그 위젯으로 바꾸지 않는다**(로그창 교체 때도 제외했다). 스크롤 안에서 폭이 줄면 가로 스크롤이 생기는지만 확인 |
| 9-8 | 사용자 근육기억이 깨진다 | 4장 순서로 최소화(켤 때 열리는 화면은 그대로). CHANGELOG 에 5장 매핑 표를 그대로 싣는다 |

---

## 10. 검증 계획

**코어는 건드리지 않으므로 코어 회귀는 "그대로 통과" 가 목표다.**

1. **UI 스모크** (mayapy + 오프스크린 Qt)
   - 상위 탭이 정확히 3개(`Shape` / `Target` / `Node`)이고 순서가 맞는가
   - 하위 탭 7개가 **전부** 있고 라벨이 5장 매핑과 일치하는가
   - 각 페이지의 대표 위젯이 살아 있는가 — 2장 표의 이름으로 **탭마다 최소 2개씩**
     `self.*` 접근(스크롤 래핑 뒤에도 참조가 유지되는지가 핵심)
   - `tabs_edit_bs` 가 **없어졌는가**, `_build_edit_bs_tab` 잔재가 없는가
   - **타이머 회귀(8장) — 이번 작업의 진짜 통과 기준**
     ① `Shape > Shape Editor` 에서 행을 만들면 타이머가 **돈다**
     ② `Shape > Base Shape` 로 옮기면 **멈춘다** (지금 코드라면 계속 돌던 자리)
     ③ `Target` / `Node` 카테고리에서도 **멈춰 있다**
     ④ 다시 `Shape > Shape Editor` 로 오면 **다시 돈다**
     ⑤ **Expand 창이 떠 있으면** 어느 탭이든 **돈다**(9-4)
   - 탭 바 폭 실측 — 상위/하위 모두 창 폭 안에 들어가는가(4장 예상치와 대조)
2. **기존 회귀 재실행** — `target_order` · `bake_delete` · `mix` · `naming` 코어 테스트를 그대로
   돌려 **전부 그대로 통과**하는지.
3. **실제 Maya 확인**(사용자) — 중첩 탭이 테마에서 정상으로 보이는지, `Shape Editor` 의 Expand 창과
   weight 슬라이더가 그대로인지, 6-5 를 채택했다면 `Mix Targets` 의 가로 스크롤이 견딜 만한지.

---

## 11. 작업 단계

1. `_scrolled` / `_build_sub_tabs` / `_build_category_tab` + `SHAPE/TARGET/NODE_PAGES` ·
   `CATEGORIES` 표 추가. `build_ui()` 의 `addTab` 6줄을 루프로 교체.
   `_build_edit_bs_tab` 과 `tabs_edit_bs` 제거.
   **기존 `_build_*_tab` 7개는 한 줄도 수정하지 않는다.**
2. **8장 타이머 수정** — `_shape_editor_visible()` 도입, `SHAPE_EDITOR_TAB` 제거,
   상위·하위 두 시그널 연결.
3. 6-1 결정 반영(라벨 `Extract` 또는 `Edit BS`).
4. UI 스모크 작성·실행, 코어 회귀 재실행.
5. 6-5 를 채택하면 **스크롤 적용을 별도 커밋**으로. 창 최소 크기를 다시 재고 `win_width/height`
   가 이제 실현되는지 확인.
6. 파일 헤더 주석의 탭 목록(현재 `1) ~ 6)` 나열)을 새 구조로 고쳐 쓴다.
7. 문서 갱신 — `docs/A00290_BSTool.md` 의 절 제목(`탭 1` ~ `탭 6`)을 새 구조로,
   `CHANGELOG.md` v02.00(5장 매핑 표 포함), `WORKLOG.md`,
   메모리 5건(`wip-a00290-*`)에 새 위치 표기.
8. 사용자 Maya 확인 → 반영.

---

## 12. 이 계획서가 하지 않는 것

- **기능 추가·삭제·동작 변경 없음.** 버튼 하나도 옮기지 않는다(탭 내부 레이아웃은 그대로).
- **`app/core/*` 수정 없음.**
- `Mix Targets` 의 최소 폭 1092 px 을 줄이는 작업 — 1장·6-5 에서 드러났지만 **별도 안건**이다.
- `te_bd_report` 를 공용 로그 위젯으로 바꾸는 것(9-7) — 로그가 아니다.
- `V02` 폴더 분리 없음(6-6).
- 공용 위젯(`Framework/qt/*`) 수정 없음 — 골격 셋은 A00145 · A00275 와 같은 모양이지만,
  **공용으로 빼는 것은 이 작업의 범위가 아니다**(세 번째 같은 모양이 확인됐으므로, 공용화는
  이 작업이 끝난 뒤 별도로 검토할 만하다).
