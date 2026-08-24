---
title: A00275_skinTool_V01 탭 재분류 계획서 (상위 탭 → 하위 탭)
aliases: [A00275 탭 정리, skinTool tab reorg, 스킨툴 탭 재분류]
tags: [plan, maya-python, A00275, skintool, ui, tabs]
updated: 2026-08-24
---

# A00275_skinTool_V01 — 탭 · 하위 탭 재분류 계획서

> **목적**: 기능은 **하나도 바꾸지 않고** 평평한 상위 탭 7개를 **카테고리 3 → 기능 7** 의
> 2단 구조로 다시 나눈다. 코드는 "옮기기" 가 아니라 **"묶기"** 만 한다.

- **작성일**: 2026-08-24
- **대상**: `tools/A00275_skinTool_V01/app/ui/main_window.py` (UI 전용 — `app/core/*` 는 손대지 않는다)
- **상태**: **계획 — 미착수**
- **예상 버전**: v01.14 → **v01.15**
- **선례**: [A00110_animTool 탭 재분류 계획서](A00110_animTool_tab_reorg_plan.md) (같은 문제를
  같은 방식으로 푼 툴). 구현 골격은 `A00145_RigConnect` 의 `Constrain` / `Connect` 탭.

---

## 1. 문제

지금 상위 탭은 **7개인데 크기(개념의 넓이)가 서로 다르고, 같은 개념이 흩어져 있다.**

| 상위 탭 | 무엇을 하나 | 성격 |
|---|---|---|
| Classic | 레거시 2버튼 웨이트 이동 | 웨이트를 옮긴다 |
| Transfer | N 소스 메시 → 선택 메시 전이 | 웨이트를 옮긴다 |
| Migrate A -> B | 토폴로지가 다른 두 메시 통합 마이그레이션 | 웨이트를 옮긴다 |
| Bind Pose | 현재 조인트 포즈를 새 바인드 포즈로 | 바인드 상태를 고친다 |
| Move Joints | Edit 토글 — 메시 그대로, 조인트 이동 | 웨이트를 지킨 채 리그를 고친다 |
| Edit Mesh | Edit 토글 — 조인트 그대로, 메시 수정 | 웨이트를 지킨 채 리그를 고친다 |
| Expand Bind | 저장 버텍스 → 저장 조인트에 측지 거리 바인드 | 바인드를 새로 만든다 |

- **웨이트를 옮기는 세 탭**(Classic · Transfer · Migrate)이 서로 남남처럼 나열돼 있다.
  실제로는 "어디서 어디로 옮기나" 만 다른 **같은 종류**다.
- **쌍으로 읽어야 하는 두 탭**이 붙어 있지 않다 —
  `Move Joints`(조인트를 고친다) ↔ `Edit Mesh`(메시를 고친다) 는 조작 방식(Edit 토글)도,
  약속(웨이트 불변)도 같은데 이름만 봐서는 한 쌍인지 알 수 없다.
- `Bind Pose` 와 `Expand Bind` 사이에 편집 탭 2개가 끼어 있다.
- 탭이 7개라 **폭 620 기준 탭 바가 이미 빡빡하다.** 기능이 하나 더 늘면 라벨이 잘리거나
  스크롤 화살표가 뜬다.

> 이 툴은 앞으로도 기능이 붙는다(v01.08 Move Joints, v01.09 Expand Bind, v01.14 Edit Mesh —
> **최근 6개 버전에서 상위 탭이 3개 늘었다**). 평평한 채로 두면 계속 옆으로만 자란다.

---

## 2. 현재 기능 전수 (7개) — 하나도 빠뜨리지 않는다

| # | 탭 | 빌더 메서드 | 상태를 들고 있는 것 | 비고 |
|---|---|---|---|---|
| 1 | Classic | `_build_classic_tab` | `tsl_from` / `tsl_to`, Engine · Transfer Mode 콤보 | 레거시 2버튼 UI |
| 2 | Transfer | `_build_transfer_tab` | 소스 메시 TSL, Engine, falloff 옵션 | |
| 3 | Migrate A -> B | `_build_migrate_tab` | A/B 메시 필드 | |
| 4 | Bind Pose | `_build_bind_pose_tab` | `bp_targets`, 모드 라디오, `btn_bp_update` · `btn_bp_diagnose` | |
| 5 | Move Joints | `_build_move_joints_tab` | `je_targets`, `btn_je_edit`(토글) | **씬에 편집 상태** |
| 6 | Edit Mesh | `_build_edit_mesh_tab` | `me_targets`, `btn_me_edit`(토글) | **씬에 편집 상태** |
| 7 | Expand Bind | `_build_expand_bind_tab` | `eb_mesh` / `eb_vertices` / `eb_loop`, falloff 커브 위젯 | 가장 세로가 길다 |

**공통**: 하단 로그(`te_log`)는 모든 탭이 공유한다 — 재분류 뒤에도 탭 바깥에 그대로 둔다.

---

## 3. 분류 원칙

1. **상위 탭 = 카테고리, 하위 탭 = 기능.** 예외를 두지 않는다(A00110 과 같은 규칙).
   상위 탭에 "기능 하나" 를 직접 올리지 않는다 — 그 예외가 다시 불균형을 만든다.
2. 기준은 **"무엇을 바꾸는가"**. 대상(조인트/메시)이 아니라 **결과물**로 나눈다.
3. **하위가 하나뿐인 카테고리도 하위 탭 바를 둔다.** 지금은 해당 없지만 규칙으로 못박는다.
4. **라벨은 지금 이름 그대로.** 사용자가 문서·메모리·대화에서 부르던 이름을 바꾸지 않는다.

---

## 4. 새 구조 (상위 3 / 하위 7)

```
┌ Skin Tool v01.15 ───────────────────────────────────────┐
│ [ Weights ] [ Bind ] [ Edit ]                           │  ← 상위 = 카테고리
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [ Classic ] [ Transfer ] [ Migrate A -> B ]         │ │  ← 하위 = 기능
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │                                                 │ │ │
│ │ │   (기존 탭 내용 그대로 — 스크롤 영역 안)         │ │ │
│ │ │                                                 │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌ Log ────────────────────────────────────────────────┐ │  ← 탭 바깥, 공유
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│           Copyright (c) Park Ji Hun. ...                │
└─────────────────────────────────────────────────────────┘
```

| 상위 탭 | 뜻 | 하위 탭 |
|---|---|---|
| **Weights** | 이미 있는 웨이트를 **다른 곳으로 옮긴다** | `Classic` · `Transfer` · `Migrate A -> B` |
| **Bind** | 바인드를 **새로 만들거나 바인드 상태를 갱신**한다 | `Bind Pose` · `Expand Bind` |
| **Edit** | **웨이트를 그대로 둔 채** 리그를 고친다 (Edit 토글) | `Move Joints` · `Edit Mesh` |

상위 탭 툴팁(영어, UI 문자열 규칙):

- **Weights** — "Move existing skin weights somewhere else."
- **Bind** — "Create a bind, or update what the current bind pose is."
- **Edit** — "Change the joints or the mesh while every weight value stays the same."

### 왜 이 순서인가

`Weights → Bind → Edit` 는 **지금 탭 순서를 가장 적게 흔든다.** 현재 1·2·3번 탭이 그대로
Weights 로, 4·7번이 Bind 로, 5·6번이 Edit 으로 간다. 왼쪽에 있던 것이 계속 왼쪽에 있으므로
근육기억이 크게 깨지지 않는다.

---

## 5. 이동 매핑 (기존 7개 — 전부 자리 있음)

| 기존 위치 | 새 위치 | 라벨 변경 |
|---|---|---|
| Classic | **Weights > Classic** | 없음 |
| Transfer | **Weights > Transfer** | 없음 |
| Migrate A -> B | **Weights > Migrate A -> B** | 없음 |
| Bind Pose | **Bind > Bind Pose** | 없음 |
| Expand Bind | **Bind > Expand Bind** | 없음 |
| Move Joints | **Edit > Move Joints** | 없음 |
| Edit Mesh | **Edit > Edit Mesh** | 없음 |

**빠지는 기능 없음. 합쳐지는 기능 없음. 이름 바뀌는 기능 없음.**

---

## 6. 판단이 갈리는 지점 → 권장안

### 6-1. `Bind Pose` 는 Bind 인가 Edit 인가

`Bind Pose` 도 결과적으로는 "조인트를 옮긴 뒤 다시 바인드" 다. 그러나

- **Edit 카테고리의 정의는 "웨이트를 그대로 둔 채 고친다" 가 아니라 조작 방식이 `Edit 토글`** 인
  것이다. Bind Pose 는 토글이 아니라 **한 방 버튼**(`UPDATE BIND POSE`)이고, 순서도 반대다
  (먼저 옮겨서 메시가 변형된 뒤 → 굳힌다).
- 바꾸는 결과물이 `bindPreMatrix` + `bindPose` 노드, 즉 **바인드 상태 그 자체**다.

→ **`Bind` 로 둔다.** 문서에 이미 있는 "Bind Pose 와 Move Joints 의 차이(순서가 반대)" 설명이
카테고리가 다른 이유를 그대로 설명해 준다.

### 6-2. 다른 분류축 — "대상별"(Weights / Joints / Mesh) 은 왜 안 쓰나

| 대상축 | 배분 |
|---|---|
| Weights | Classic, Transfer, Migrate, **Expand Bind** |
| Joints | Bind Pose, Move Joints |
| Mesh | **Edit Mesh** 하나뿐 |

4 / 2 / 1 로 불균형하고, `Expand Bind`(바인드를 새로 만드는 것)가 전이 기능들과 한 칸에 섞인다.
**채택하지 않는다.**

### 6-3. 라벨을 짧게 바꿀까 (`Edit > Joints` / `Edit > Mesh`)

`Edit > Edit Mesh` 는 "Edit" 이 두 번 나온다. `Edit > Joints` / `Edit > Mesh` 가 더 예쁘다.
그러나 **문서·CHANGELOG·메모리·포트폴리오가 전부 `Move Joints` / `Edit Mesh` 로 부르고 있고,
사용자도 그 이름으로 요청했다.** 이름을 바꾸면 이 재분류의 약속("기능은 하나도 안 바꾼다")이
깨져 보인다.

→ **지금 이름 그대로 둔다.** 중복은 툴팁으로 보완한다.

### 6-4. `V02` 로 폴더를 가를까

A00110 은 재분류판을 `A00110_animTool_V02` 로 갈랐다. 여기는 **가르지 않는다.**

- A00110 은 재분류와 **동시에 Curve Filters 이식**이라는 기능 추가가 예정돼 있었다.
  여기는 **UI 묶기뿐**이라 되돌릴 일이 생겨도 커밋 하나를 되돌리면 된다.
- A00275 자체가 이미 `A00270_skinMigrate` 의 후속 폴더다. 또 가르면 스킨 툴이 3개가 된다.

→ **제자리에서 v01.15 로 올린다.**

---

## 7. 구현 방식 — "묶기만" 한다

**기존 `_build_*_tab()` 7개는 이름도 내용도 건드리지 않는다.** 이것이 회귀를 막는 가장 큰
안전장치다. 새로 쓰는 것은 골격 3개와 분류표뿐이다.

```python
# app/ui/main_window.py

# (하위 탭 라벨, 툴팁 = 전체 이름/설명, 빌더 메서드 이름)
WEIGHTS_PAGES = (
    ("Classic", "Classic - the legacy two-button transfer UI", "_build_classic_tab"),
    ("Transfer", "Transfer - weights from several source meshes onto the selected mesh",
     "_build_transfer_tab"),
    ("Migrate A -> B", "Migrate A -> B - transfer + bone move between two meshes with "
     "different topology", "_build_migrate_tab"),
)
BIND_PAGES = (
    ("Bind Pose", "Bind Pose - make the current joint pose the new bind pose",
     "_build_bind_pose_tab"),
    ("Expand Bind", "Expand Bind - bind a stored vertex set to stored joints by "
     "geodesic edge length", "_build_expand_bind_tab"),
)
EDIT_PAGES = (
    ("Move Joints", "Move Joints - move the joints without deforming the mesh",
     "_build_move_joints_tab"),
    ("Edit Mesh", "Edit Mesh - edit the mesh without changing a single weight",
     "_build_edit_mesh_tab"),
)

# (상위 탭 라벨, 툴팁, 하위 페이지 표, 하위 QTabWidget 을 담을 속성 이름)
CATEGORIES = (
    ("Weights", "Move existing skin weights somewhere else.",
     WEIGHTS_PAGES, "weights_tabs"),
    ("Bind", "Create a bind, or update what the current bind pose is.",
     BIND_PAGES, "bind_tabs"),
    ("Edit", "Change the joints or the mesh while every weight value stays the same.",
     EDIT_PAGES, "edit_tabs"),
)

def _build_category_tab(self, pages, attr):
    """카테고리 상위 탭 하나 — 기능들을 하위 탭으로 담는다."""
    tabs = self._build_sub_tabs(pages)
    setattr(self, attr, tabs)
    return tabs

def _build_sub_tabs(self, pages):
    tabs = QTabWidget()
    tabs.tabBar().setElideMode(Qt.ElideRight)   # 폭이 모자라면 라벨을 자른다
    for label, tip, builder in pages:
        index = tabs.addTab(self._scrolled(getattr(self, builder)()), label)
        tabs.setTabToolTip(index, tip)
    return tabs

def _scrolled(self, widget):
    """페이지를 스크롤 영역에 담는다 (창이 작아도 위젯이 겹치지 않도록)."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll
```

`build_ui()` 의 탭 생성부는 이렇게 줄어든다.

```python
self.tabs = QTabWidget()
for label, tip, pages, attr in self.CATEGORIES:
    index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
    self.tabs.setTabToolTip(index, tip)
    if label == "Edit":
        self.edit_page = self.tabs.widget(index)     # 8장에서 쓴다
self.tabs.currentChanged.connect(self._on_tab_changed)
self.edit_tabs.currentChanged.connect(self._on_tab_changed)
main_layout.addWidget(self.tabs)
```

`QScrollArea` 는 `Framework.qt.qt` 의 와일드카드 임포트로 이미 들어와 있다(추가 임포트 불필요).

---

## 8. 가장 큰 리스크 — 씬 상태 동기화가 조용히 깨진다

**이 항목이 이 작업의 핵심 위험이다.** 지금 코드는 상위 탭 인덱스로 갈라진다.

```python
self.tabs.currentChanged.connect(self._on_tab_changed)

def _on_tab_changed(self, index):
    if index == self.je_tab_index:          # ← 상위 탭 인덱스
        self._adopt_scene_edits(); self._update_je_state()
    elif index == self.me_tab_index:
        self._adopt_scene_mesh_edits(); self._update_me_state()
```

중첩하면 `index` 는 **카테고리 인덱스**가 되어 `je_tab_index`(4) / `me_tab_index`(5) 와 영영
일치하지 않는다. 그러면 **Move Joints · Edit Mesh 탭을 열어도 씬을 다시 읽지 않는다.**

- 툴을 껐다 켰을 때 **편집 중이던 대상을 못 되찾는다**(두 탭 모두의 핵심 약속).
- 다른 창에서 편집을 시작/종료해도 버튼 색과 실제 씬이 어긋난다.
- **에러가 나지 않는다.** 그래서 눈으로 보기 전엔 모른다.

### 권장 수정 — 인덱스 비교를 없애고 "지금 보이는 페이지" 로 판단

```python
def _on_tab_changed(self, *_):
    """편집 상태는 씬에 있다. Edit 카테고리가 보일 때 씬을 다시 읽어 화면을 맞춘다.

    상위/하위 두 QTabWidget 이 같은 슬롯에 연결돼 있고, 인덱스가 아니라 **위젯 동일성**으로
    판단한다(인덱스는 탭이 늘고 줄면 의미가 변한다).
    """
    if self.tabs.currentWidget() is not self.edit_page:
        return

    page = self.edit_tabs.currentWidget()
    if page is self.je_page:
        self._adopt_scene_edits()
        self._update_je_state()
    elif page is self.me_page:
        self._adopt_scene_mesh_edits()
        self._update_me_state()
```

`self.je_page` / `self.me_page` 는 `_build_sub_tabs` 가 만든 **스크롤 래퍼**를 가리켜야 한다
(`tabs.widget(i)` 가 돌려주는 것이 `QScrollArea` 지 페이지 위젯이 아니다). 헷갈리기 쉬운
지점이라 `_build_sub_tabs` 가 `(tabs, [래퍼...])` 를 돌려주게 하거나, `EDIT_PAGES` 순서에
맞춘 인덱스 상수(`JE_SUB = 0`, `ME_SUB = 1`)를 쓰는 편이 단순하다 — **구현 시 후자를 권장**한다.

> 대안으로 "Edit 카테고리가 보이면 두 상태를 **모두** 갱신" 도 가능하다(분기 없음). 비용은
> `find_editing_in_scene()` 이 `cmds.ls(type="mesh")` 를 훑는 것뿐인데, 이미 대상이 잡혀 있으면
> `_adopt_*` 가 즉시 반환하므로 실질 비용은 작다. 다만 **메시가 수천 개인 씬에서 탭을 누를
> 때마다** 전수 조회가 도는 것은 확인 후 결정한다(9-4 측정 항목).

---

## 9. 그 밖의 리스크와 대응

| # | 리스크 | 대응 |
|---|---|---|
| 9-1 | `_scrolled()` 로 감싸면 `tabs.widget(i)` 가 페이지가 아니라 `QScrollArea` 다 | 인덱스/위젯으로 페이지를 찾는 코드가 있는지 먼저 확인 — **현재는 8장의 `_on_tab_changed` 하나뿐**(grep 완료). 새로 만들지 않는다 |
| 9-2 | **이중 스크롤** — 상위 페이지에도 스크롤을 씌우면 스크롤바가 두 겹으로 보인다 | 스크롤은 **하위 페이지에만**. 상위 카테고리 페이지는 `QTabWidget` 자체를 그대로 돌려준다 ([[prefer-subtabs-over-stacked-collapsibles]]) |
| 9-3 | 중첩 탭 바가 세로를 한 줄(약 26~30px) 더 먹어 `Expand Bind` 아래가 잘린다 | 실측 후 `win_height` 680 → 700~720. 스크롤이 있으니 잘려도 못 쓰게 되지는 않는다 |
| 9-4 | 탭 전환마다 씬 조회가 도는 비용 | 8장 권장안은 Edit 카테고리에서만 돈다. 메시 5,000개 씬에서 `find_editing_in_scene()` 시간을 mayapy 로 한 번 잰다 |
| 9-5 | 테마 qss(`dark.qss` / `red.qss`)가 중첩 `QTabWidget` 을 예상하지 않았을 수 있다 | 실제 Maya 에서 두 테마로 눈 확인. 필요하면 qss 는 **건드리지 않고** 하위 탭에만 `setObjectName` 을 주는 선에서 처리 |
| 9-6 | TSL 위젯이 스크롤 안에서 높이를 잃는다 | **TSL 위젯 전체에 `setMaximumHeight` 를 걸지 않는다** — 리스트 최소 높이가 안 줄어 버튼에서 높이를 빼앗아 글자가 잘린다 ([[tsl-widget-max-height-squeezes-buttons]]). 높이 제한이 필요하면 `list_widget` 에만 |
| 9-7 | 사용자 근육기억이 깨진다 | 4장의 순서(Weights → Bind → Edit)로 최소화. CHANGELOG 에 이동 매핑 표(5장)를 그대로 싣는다 |

---

## 10. 검증 계획

**코어는 건드리지 않으므로 코어 회귀는 "그대로 통과" 가 목표다.**

1. **기존 회귀 재실행** — `mesh_edit_manager` 코어 51항목이 100% 그대로 통과.
2. **UI 스모크 확장** (현재 25항목 → 약 40항목):
   - 상위 탭이 정확히 3개(`Weights` / `Bind` / `Edit`)이고 순서가 맞는가
   - 하위 탭 7개가 **전부** 존재하고 라벨이 5장 매핑과 일치하는가
   - 각 페이지의 대표 위젯이 살아 있는가 — `tsl_classic_from` · `tsl_classic_to` ·
     `tsl_transfer_src` · `btn_transfer_run` · `tsl_joints_a` · `btn_bp_update` ·
     `btn_bp_diagnose` · `btn_je_edit` · `btn_me_edit` · `btn_eb_bind` 로
     **탭마다 최소 1개씩** 속성 접근을 확인(스크롤 래핑 후에도 `self.*` 참조가 유지되는지가 핵심)
   - **씬 상태 동기화 회귀 테스트**(8장) — `begin_edit` 를 코어로 직접 켠 뒤
     ① 다른 카테고리로 갔다가 ② `Edit > Move Joints` 로 돌아오면 버튼이 켜진 상태로 복원되는가.
     `Edit > Edit Mesh` 도 같은 방식으로. **이 두 항목이 이번 작업의 진짜 통과 기준이다.**
   - 편집 중 `Load Selection` 잠금이 그대로인가
3. **실제 Maya 확인**(사용자) — 폭 620 에서 세 하위 탭 바가 잘리지 않는지, 두 테마에서
   중첩 탭이 정상으로 보이는지, `Expand Bind` 의 falloff 커브 위젯이 스크롤 안에서 정상인지.

---

## 11. 작업 단계

1. `_scrolled` / `_build_sub_tabs` / `_build_category_tab` + `WEIGHTS/BIND/EDIT_PAGES` ·
   `CATEGORIES` 표 추가. `build_ui()` 의 `addTab` 7줄을 루프로 교체.
   **기존 `_build_*_tab` 7개는 한 줄도 수정하지 않는다.**
2. `_on_tab_changed` 재작업(8장) + `je_tab_index` / `me_tab_index` 제거 또는 **하위 탭 인덱스로
   의미 변경**(이름을 `je_sub_index` / `me_sub_index` 로 바꿔 혼동을 없앤다).
3. 창 높이 실측 조정(9-3), 하위 탭 바 폭 확인.
4. UI 스모크 확장 & 실행, 코어 회귀 재실행.
5. 파일 헤더 주석의 탭 목록(현재 `Tab 1~7` 나열)을 새 구조로 고쳐 쓴다.
6. 문서 갱신 —
   `docs/A00275_skinTool_V01.md` 의 **탭 표**와 절 제목(`1-B` · `1-B2` · `1-C` …)을 새 구조로,
   `CHANGELOG.md` v01.15(5장 매핑 표 포함), `WORKLOG.md`, `portfolio_EN/KR`,
   메모리(`wip-a00275-*` 들에 "Edit 카테고리 하위" 표기 추가 + 새 메모 1건).
7. 사용자 Maya 확인 → 반영.

---

## 12. 이 계획서가 하지 않는 것

- **기능 추가·삭제·동작 변경 없음.** 버튼 하나도 옮기지 않는다(탭 내부 레이아웃은 그대로).
- **`app/core/*` 수정 없음.**
- 탭 라벨 변경 없음(6-3).
- `V02` 폴더 분리 없음(6-4).
- 공용 위젯(`Framework/qt/*`) 수정 없음 — 골격 3개는 A00145 와 같은 코드지만, **공용으로 빼는
  것은 이 작업의 범위가 아니다**(A00110 · A00145 · A00275 세 곳에서 같은 모양이 확인되면 그때
  공용화를 따로 검토한다).
