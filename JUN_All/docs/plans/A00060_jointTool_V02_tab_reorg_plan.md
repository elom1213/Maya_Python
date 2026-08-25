---
title: A00060_jointTool_V02 탭 재분류 계획서 (상위 탭 → 하위 탭)
aliases: [A00060 탭 정리, jointTool tab reorg, 조인트툴 탭 재분류]
tags: [plan, maya-python, A00060, jointtool, ui, tabs]
updated: 2026-08-25
---

# A00060_jointTool_V02 — 탭 · 하위 탭 재분류 계획서

> **목적**: 기능을 **하나도 빼거나 더하지 않고**, 평평한 상위 탭 5개(그 안에 접이식 6섹션)를
> **카테고리 5 → 기능 11** 의 2단 구조로 다시 나눈다.
> 특히 `Curve` 탭에 뭉쳐 있는 **성격이 다른 4개 섹션**을 제자리로 보낸다.

- **작성일**: 2026-08-25
- **대상**: `tools/A00060_jointTool_V03/app/ui/main_window.py` (UI 전용 — `app/core/*` 는 손대지 않는다).
  V02 를 복제해 `_V03` 로 갈랐다(6-6 의 결정 번복) — **V02 는 재분류 전 상태로 그대로 둔다.**
- **상태**: **적용 완료 — `A00060_jointTool_V03` v03.00 (2026-08-25).**
  12장 1~12단계 끝, 13단계(사용자 Maya 확인) 대기. 검증 128항목 전부 통과(11장).
  9-3/9-4 대신 10-1·10-2 실측: 상위 탭 바 291px · 가장 넓은 하위 탭 바 241px(`Create`) ·
  가장 긴 페이지 423px(`Create`) → 창 `540 × 820` → **`560 × 720`**.
- **버전**: v01.05 → **v03.00** — 사용자가 `_V03` 폴더를 지시했으므로 6-4 의 `02.00` 이
  아니라 폴더명에 맞춘 `03.xx` 로 센다.
- **선례**:
  [A00110_animTool 탭 재분류 계획서](A00110_animTool_tab_reorg_plan.md) — 상위=카테고리 규칙의 원본,
  [A00275_skinTool_V01 탭 재분류 계획서](A00275_skinTool_V01_tab_reorg_plan.md) — 구현 골격(`_build_sub_tabs` / `_scrolled`).

---

## 1. 문제

### 1-1. 상위 탭 5개의 크기가 서로 다르다

| 상위 탭 | 담긴 기능 수 | 성격 |
|---|---|---|
| `Curve` | **7** (접이식 4섹션) | 조인트 생성 + 조인트 오리엔트 + 클러스터 생성 — **뒤섞임** |
| `Divide` | 1 | 조인트 생성 |
| `Aim` | 1 | 조인트 오리엔트 |
| `Hair` | **5** (접이식 2섹션) | 커브 편집 + 체인 편집 + 선택 — **뒤섞임** |
| `IK Edit` | 1 | 체인 편집 |

기능 하나짜리 탭 3개와, 성격이 다른 기능 5~7개를 담은 탭 2개가 나란히 있다.

### 1-2. `Curve` 탭은 "커브 탭" 이 아니다

이름은 `Curve` 인데 실제로 들어 있는 것은 넷 다 다른 일이다.

| 접이식 섹션 | 실제로 하는 일 | 입력 |
|---|---|---|
| `Tool : joint to Crv` | 커브 위에 **조인트 체인 생성** | nurbsCurve |
| ⤷ 같은 섹션의 `Clusters` 버튼 | 커브 CV 마다 **클러스터 디포머 생성** (조인트와 무관) | nurbsCurve |
| `Tool : joint to obj` | 오브젝트/버텍스 위치에 **조인트 생성** (커브 안 씀) | transform / vertex |
| `Tool : joint orient and rotate` | 기존 조인트의 **jointOrient ↔ rotate 교환** | joint |
| `Tool : Set Orient` | 기존 조인트의 **jointOrient 축·각도 지정** | joint |

**커브를 쓰는 것은 위 둘뿐이고, 아래 둘은 커브와 아무 상관이 없다.**
`Clusters` 는 조인트를 만들지도 않는다. 탭 이름이 안에 있는 어느 기능도 설명하지 못한다.

### 1-3. `Hair` 탭도 같은 문제다

| 접이식 섹션 | 실제로 하는 일 | 입력 |
|---|---|---|
| `Sub Tool : Curve` — Separate / Remove / Rebuild | **커브 자체를 편집** (조인트 생성 전 준비) | nurbsCurve |
| `Tool : Edit` — Reverse joint chain | 조인트 **체인을 역순으로 재생성** | root joint |
| `Tool : Edit` — Select Unused Joints | 안 쓰는 조인트를 **고르기만** (씬 불변) | joint |

`Hair` 는 기능의 이름이 아니라 **쓰임새(헤어 리깅)** 로 붙은 이름이다.
같은 커브 편집 기능을 헤어가 아닌 곳에 쓸 때 이 탭을 열 이유를 짐작하기 어렵다.

### 1-4. 리스트 하나가 세 종류의 노드를 담고 있다 — 뒤섞임의 증거

`Curve` 탭의 `Selections` 리스트(`tsl_curve`) **하나**를 다섯 기능이 나눠 쓴다.

| 기능 | 리스트에 들어 있어야 하는 것 |
|---|---|
| Joints to Crv · Clusters | **커브** |
| Match to Obj | **오브젝트 / 버텍스** |
| joint orient ↔ rotate · Set joints orientation | **조인트** |

**섹션을 바꿀 때마다 리스트를 비우고 다시 담아야 한다.** 리스트를 그대로 두고 다른 섹션 버튼을
누르면 — `Joints to Crv` 는 `is not a nurbsCurve` 경고를 내고 건너뛰지만,
**`Clusters` 는 타입 검사가 없어 `.spans` 를 읽다가 그대로 예외로 죽는다**
(`curve_joint_manager.clusters_to_curves`). `Hair` 탭의 `Joint Tool` 리스트(`tsl_hair`) 도
커브 3기능 · 조인트 2기능이 같은 리스트를 나눠 쓴다.

> **리스트가 담아야 할 타입이 섹션마다 다르다는 것이, 그 섹션들이 한 탭에 있으면 안 된다는
> 가장 분명한 신호다.**

### 1-5. 앞으로도 늘어난다

v01.03 월드 좌표 생성 · v01.04 Match to Sel · v01.05 IK Edit — **최근 3개 버전이 모두 기능 추가**였다.
평평한 채로 두면 새 기능은 계속 `Curve` 나 `Hair` 로 들어간다(실제로 `Match to Sel` 이 그렇게 들어갔다).

---

## 2. 현재 기능 전수 (15개) — 하나도 빠뜨리지 않는다

| # | 현재 위치 | 기능 | 위젯 / 옵션 | 코어 | 리스트 |
|---|---|---|---|---|---|
| 1 | Curve > joint to Crv | `Joints to Crv` | point type 라디오 3(CV omit / CV / EP) | `crv_mgr.joints_to_curves` | `tsl_curve` |
| 2 | Curve > joint to Crv | `Clusters` | 없음 | `crv_mgr.clusters_to_curves` | `tsl_curve` |
| 3 | Curve > joint to obj | `Match to Obj` | Connect/Separate, Foward · Secondary · Secondary orient 축 | `obj_mgr.joints_to_objs` | `tsl_curve` |
| 4 | Curve > joint to obj | `Match to Sel` | 위와 같은 옵션 + TSL 의 **Order** 체크박스 | `obj_mgr.joints_to_objs` | 씬 선택 (`tsl_curve.maya_selection()`) |
| 5 | Curve > joint orient and rotate | `joint orient to rotate` | 없음 | `obj_mgr.swap_rotate_orient` | `tsl_curve` |
| 6 | Curve > joint orient and rotate | `rotate to joint orient` | 없음 | `obj_mgr.swap_rotate_orient` | `tsl_curve` |
| 7 | Curve > Set Orient (기본 접힘) | `Set joints orientation` | Orient axis(X/Y/Z), Orient degree | `obj_mgr.set_joint_orient` | `tsl_curve` |
| 8 | Divide | `Make Joint Divided` | Joints Number, `Select Start End` / `Add Start End` | `div_mgr.make_joints_divided` | `tsl_div_start` / `tsl_div_end` |
| 9 | Aim | `Make Joint Aim` | Aim axis(X/Y/Z), `Select Start End` / `Add Start End` | `aim_mgr.make_joint_aim` | `tsl_aim_start` / `_end` / `_pole` |
| 10 | Hair > Sub Tool : Curve | `Separate Curve` | 없음 | `hair_mgr.separate_curves` | `tsl_hair` |
| 11 | Hair > Sub Tool : Curve | `Remove Curve` | Max Length | `hair_mgr.remove_curves_by_length` | `tsl_hair` |
| 12 | Hair > Sub Tool : Curve | `Rebuild Curve` | Interval, Max joints | `hair_mgr.rebuild_curves_by_interval` | `tsl_hair` |
| 13 | Hair > Tool : Edit | `Reverse joint chain` | `Remove origin` 체크박스 | `hair_mgr.reverse_joints` | `tsl_hair` |
| 14 | Hair > Tool : Edit | `Select Unused Joints` | 없음 | `hair_mgr.unused_joints` | `tsl_hair` |
| 15 | IK Edit | IK 편집 토글 일체 | Pole vector · Snap 콤보, preferred angle 체크, `Load Selection` / `Clear` / `Select Handle` / `EDIT IK CHAIN` / `Cancel Edit` / `Update Now` | `ike_mgr.*` | `ike_targets`(TSL 아님) |

**공통**: 하단 로그(`te_log`)와 `Help > About` 메뉴는 모든 탭이 공유한다 — 재분류 뒤에도 탭 바깥에
그대로 둔다. 모든 실행은 `_run()` 이 `undo_chunk` 로 감싼다.

---

## 3. 분류 원칙

1. **상위 탭 = 카테고리, 하위 탭 = 기능.** 예외 없음
   (A00110 · A00275 와 같은 규칙). 상위 탭에 기능 하나를 직접 올리지 않는다.
2. 기준은 **"무엇을 바꾸는가"** — 입력이 아니라 **결과물**로 나눈다.
   (같은 커브를 입력으로 받아도, 조인트가 생기면 `Create`, 커브가 바뀌면 `Curve` 다.)
3. **접이식(`CollapsibleBox`)으로 쌓인 섹션은 전부 하위 탭으로 내린다**
   (`prefer-subtabs-over-stacked-collapsibles` — 섹션이 3~4개를 넘으면 탭).
4. **하위가 하나뿐인 카테고리도 하위 탭 바를 둔다** — 없으면 기능 이름이 화면에서 사라진다.
5. **기능 이름(버튼 라벨)은 그대로 쓴다.** 하위 탭 라벨만 새로 짓는다.

---

## 4. 새 구조 (상위 5 / 하위 11)

```
┌ Joint Tool v03.00 ──────────────────────────────────────┐
│ [ Create ][ Orient ][ Chain ][ Curve ][ Select ]        │  ← 상위 = 카테고리
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [ From Curve ][ From Object ][ Divide ]             │ │  ← 하위 = 기능
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │  Curves   (이 하위 탭 전용 리스트)               │ │ │
│ │ │  ○ Control Vertex (Omit [1], [-2])              │ │ │
│ │ │  ○ Control Vertex    ○ Edit Point               │ │ │
│ │ │  [ Joints to Crv ]                              │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌ Log ────────────────────────────────────────────────┐ │  ← 탭 바깥, 공유
│ └─────────────────────────────────────────────────────┘ │
│           Copyright (c) Park Ji Hun. ...                │
└─────────────────────────────────────────────────────────┘
```

| 상위 탭 | 뜻 (무엇이 바뀌나) | 하위 탭 |
|---|---|---|
| **Create** | 씬에 **조인트가 생긴다** | `From Curve` · `From Object` · `Divide` |
| **Orient** | 있는 조인트의 **방향만** 바뀐다 (위치·개수 불변) | `Aim` · `Set Orient` · `Orient / Rotate` |
| **Chain** | 있는 체인의 **구조·연결**을 고친다 | `Reverse` · `IK Edit` |
| **Curve** | 조인트가 아니라 **커브·디포머**를 다룬다 (조인트를 만들기 전 준비) | `Edit Curve` · `Clusters` |
| **Select** | **씬을 바꾸지 않는다** — 고르기만 한다 | `Unused Joints` |

상위 탭 툴팁(영어 — UI 문자열 규칙):

- **Create** — "Create new joints."
- **Orient** — "Change the orientation of joints that already exist. Nothing is moved and no joint is added."
- **Chain** — "Rebuild or edit a joint chain that already exists."
- **Curve** — "Prepare the curves that joints get built on. No joint is touched."
- **Select** — "Find joints. The scene is not changed."

하위 탭 툴팁:

| 하위 탭 | 툴팁 |
|---|---|
| `From Curve` | "From Curve - build a joint chain on the points of a NURBS curve." |
| `From Object` | "From Object - build a joint at each listed object or vertex, with axis options." |
| `Divide` | "Divide - build evenly spaced joints between a start and an end joint." |
| `Aim` | "Aim - re-orient a chain so that the chosen axis points at a pole target." |
| `Set Orient` | "Set Orient - set jointOrient on a chain by axis and degree." |
| `Orient / Rotate` | "Orient / Rotate - swap values between jointOrient and rotate." |
| `Reverse` | "Reverse - rebuild a joint chain in the opposite order." |
| `IK Edit` | "IK Edit - edit the bone chain while the IK handle and its pole vector stay in place." |
| `Edit Curve` | "Edit Curve - separate, remove by length, and rebuild NURBS curves." |
| `Clusters` | "Clusters - create one cluster deformer per CV of the listed curves." |
| `Unused Joints` | "Unused Joints - select the listed joints that no skinCluster uses." |

### 왜 이 순서인가

`Create → Orient → Chain → Curve → Select` 는 **지금 탭 순서를 가장 적게 흔든다.**
현재 1번 탭(`Curve`)의 가장 큰 내용물(joint to Crv / joint to obj)이 그대로 1번 `Create` 로,
2번(`Divide`)이 `Create` 안으로, 3번(`Aim`)이 2번 `Orient` 로 간다.
왼쪽에 있던 것이 계속 왼쪽에 있다.

> **대안(작업 순서대로)**: `Curve → Create → Orient → Chain → Select` 는 실제 리깅 순서
> (커브 준비 → 조인트 생성 → 오리엔트 → 체인 정리 → 청소)와 맞아 읽기 좋다.
> 다만 지금 1번이던 것이 2번으로 밀린다. **근육기억을 우선해 위 순서를 권장한다.**

---

## 5. 이동 매핑 (기존 15개 — 전부 자리 있음)

| # | 기존 위치 | 새 위치 | 라벨 변경 |
|---|---|---|---|
| 1 | Curve > joint to Crv > `Joints to Crv` | **Create > From Curve** | 버튼 이름 그대로 |
| 2 | Curve > joint to Crv > `Clusters` | **Curve > Clusters** | 버튼 이름 그대로 |
| 3 | Curve > joint to obj > `Match to Obj` | **Create > From Object** | 그대로 |
| 4 | Curve > joint to obj > `Match to Sel` | **Create > From Object** | 그대로 |
| 5 | Curve > joint orient and rotate > `joint orient to rotate` | **Orient > Orient / Rotate** | 그대로 |
| 6 | Curve > joint orient and rotate > `rotate to joint orient` | **Orient > Orient / Rotate** | 그대로 |
| 7 | Curve > Set Orient | **Orient > Set Orient** | 그대로 (**접힘 해제**) |
| 8 | Divide | **Create > Divide** | 그대로 |
| 9 | Aim | **Orient > Aim** | 그대로 |
| 10 | Hair > Sub Tool : Curve > `Separate Curve` | **Curve > Edit Curve** | 그대로 |
| 11 | Hair > Sub Tool : Curve > `Remove Curve` | **Curve > Edit Curve** | 그대로 |
| 12 | Hair > Sub Tool : Curve > `Rebuild Curve` | **Curve > Edit Curve** | 그대로 |
| 13 | Hair > Tool : Edit > `Reverse joint chain` | **Chain > Reverse** | 그대로 |
| 14 | Hair > Tool : Edit > `Select Unused Joints` | **Select > Unused Joints** | 그대로 |
| 15 | IK Edit | **Chain > IK Edit** | 그대로 |

**빠지는 기능 없음. 합쳐지는 기능 없음. 버튼 이름 바뀌는 것 없음.**
사라지는 것은 상위 탭 이름 `Hair` 와 접이식 섹션 제목 6개(`Tool : ...` / `Sub Tool : ...`) 뿐이다
— 하위 탭 라벨이 그 자리를 대신한다.

---

## 6. 판단이 갈리는 지점 → 권장안

### 6-1. 공용 리스트를 어떻게 할 것인가 ★ 가장 중요한 결정

`tsl_curve` 를 5기능이, `tsl_hair` 를 5기능이 나눠 쓴다(1-4). 하위 탭으로 흩어지면
**리스트도 흩어져야 한다.** 세 가지 안이 있다.

| 안 | 내용 | 장점 | 단점 |
|---|---|---|---|
| **A. 하위 탭마다 자기 리스트** | 하위 탭 10개(IK Edit 제외)가 각자 TSL 을 갖는다 | 리스트 제목이 **타입을 말해 준다**(`Curves` / `Objects` / `Joints`). 1-4 의 사고가 구조적으로 불가능해진다 | TSL 위젯이 6개 → **10개**. 두 하위 탭에서 같은 커브를 쓰려면 두 번 담아야 한다 |
| **B. 카테고리마다 공용 리스트 하나** | 상위 페이지 위에 TSL 을 두고 하위 탭이 공유 | 위젯 수가 적다. `Curve` 카테고리(둘 다 커브)엔 잘 맞는다 | `Create` 는 커브/오브젝트/조인트쌍이 섞여 **성립하지 않는다.** 섞인 카테고리에서 지금 문제가 그대로 재발한다 |
| **C. 혼합** | 타입이 하나인 카테고리(`Curve`)만 공용, 나머지는 하위 탭별 | 클릭이 준다 | **규칙이 두 개가 된다.** 어느 리스트가 공용인지 화면만 봐선 모른다 |

→ **A 를 권장한다.** 이 재분류의 목적이 "한 화면에 한 가지 일" 인데, 리스트를 공유하는 순간
탭 바가 그 약속을 못 지킨다. TSL 은 **비어 있을 때 비용이 사실상 없다**
(느린 것은 줄 수가 아니라 항목별 UUID 조회 — `framework-tsl-list-limit`).

**A 를 택할 때 리스트 배치 (기존 위젯은 최대한 그대로 재사용)**

| 하위 탭 | 위젯 속성 | TSL `title` | 담는 것 |
|---|---|---|---|
| Create > From Curve | `tsl_create_crv` | `Curves` | nurbsCurve |
| Create > From Object | `tsl_create_obj` | `Objects` | transform / vertex |
| Create > Divide | `tsl_div_start` / `tsl_div_end` *(그대로)* | `Start` / `End` | joint |
| Orient > Aim | `tsl_aim_start` / `_end` / `_pole` *(그대로)* | `Start` / `End` / `pole tgt` | joint |
| Orient > Set Orient | `tsl_orient_set` | `Joints` | joint |
| Orient > Orient / Rotate | `tsl_orient_swap` | `Joints` | joint |
| Chain > Reverse | `tsl_chain_reverse` | `Root Joints` | root joint |
| Chain > IK Edit | *(없음 — `ike_targets`)* | — | ikHandle |
| Curve > Edit Curve | `tsl_curve_edit` | `Curves` | nurbsCurve |
| Curve > Clusters | `tsl_curve_cluster` | `Curves` | nurbsCurve |
| Select > Unused Joints | `tsl_select_unused` | `Joints` | joint |

> `Match to Sel`(2장 #4)은 리스트 **내용**이 아니라 그 리스트 위젯의 **`Order` 체크박스**를 읽는다
> (`tsl_curve.is_order_tracking()` · `maya_selection()`). 반드시 `From Object` 의 리스트를
> 가리키게 옮긴다 — **빠뜨리면 조용히 다른 탭의 Order 를 읽는다**(8장).

### 6-2. `Select > Unused Joints` 를 독립 카테고리로 둘 것인가

기능 하나짜리 카테고리다. `Chain` 안에 넣자는 안도 성립한다.

- 그러나 **씬을 바꾸지 않는 유일한 기능**이다. 나머지 14개는 전부 "누르면 씬이 변한다".
  A00110 이 같은 이유로 `View` 카테고리를 하나짜리로 남겼다(`wip-a00110-tab-taxonomy`).
- `Chain` 에 넣으면 "고치는 탭 안에 안 고치는 기능" 이 되어 지금 문제의 축소판이 된다.

→ **독립 `Select` 카테고리로 둔다.** 앞으로 붙을 선택·진단 기능(영향 없는 조인트 리포트,
바인드 안 된 메시 찾기 등)의 자리가 된다.

### 6-3. `Clusters` 는 `Create` 인가 `Curve` 인가

"만든다" 는 점에서 `Create` 로 보일 수 있다. 그러나

- `Create` 의 정의는 "만든다" 가 아니라 **"조인트가 생긴다"** 다. `Clusters` 는 조인트를
  하나도 만들지 않는다(cluster 디포머만).
- 실제 쓰임은 **커브 CV 를 손으로 만지기 위한 핸들**을 다는 것 — 커브 준비 작업이다.

→ **`Curve > Clusters`.** `Edit Curve` 와 한 페이지로 합치지 않는 이유는, `Edit Curve` 3버튼이
커브 자체를 바꾸는 반면 `Clusters` 는 커브를 그대로 두고 디포머를 붙이기 때문이다
(같은 사고의 반복을 막는다).

### 6-4. 버전 번호 — `01.05 → 02.00` 인가 `01.06` 인가

**이 툴은 폴더가 `_V02` 인데 버전이 `01.05` 다 — 저장소에서 유일한 예외다.**

| 툴 | 폴더 | VERSION |
|---|---|---|
| `A00010_humanIKTool_V02` | V02 | **02.01** |
| `A00040_file_exporter_V02` | V02 | **02.05** |
| `A00110_animTool_V02` | V02 | **02.12** |
| `A00390_WindTool_V02` | V02 | **02.05** |
| **`A00060_jointTool_V02`** | V02 | **01.05** ← 예외 |

관례는 "폴더가 `_V02` 면 버전도 `02.xx`"(`wip-a00110-tab-taxonomy`)이고,
**A00110 은 정확히 이 탭 재분류 시점에 `01.41 → 02.00` 으로 올렸다.**

→ **`v02.00` 으로 올린다.** 구조가 바뀌는 이번이 번호를 바로잡을 유일하게 자연스러운 지점이다.
CHANGELOG 에 "폴더명(`_V02`)과 버전을 맞춘다" 는 한 줄을 명시한다.
(반대 안: `v01.06` 으로 두면 01.00~01.05 이력과는 이어지지만 **예외는 계속 남는다.**)

### 6-5. 하위 탭 라벨을 버튼 이름과 같게 할까

`Create > From Curve` 안의 버튼은 `Joints to Crv` 다. 라벨이 서로 다르다.

→ **탭 라벨은 짧게(`From Curve`), 버튼은 그대로 둔다.** 창 폭이 540 이라 상위 5 · 하위 3 탭이
들어가려면 라벨이 짧아야 한다. 전체 뜻은 4장의 **탭 툴팁**이 말한다
(A00110 · A00275 와 같은 처리).

### 6-6. `V03` 폴더로 가를 것인가

> **[결정 번복 — 2026-08-25]** 사용자가 **`A00060_jointTool_V03` 경로에 만들라고 지시**했다.
> 아래 권장안(가르지 않는다)은 채택되지 않았다. 대신 `wip-a00110-tab-taxonomy` 의 **복제
> 체크리스트를 전부 적용**했다 — 드롭 파일(`__dragDrop_A00060_V03.py`) · 셸프 `TOOL_LABEL`
> (`JointTool3`) · 아이콘 파일명 · `WINDOW_OBJECT_NAME` · 창 제목(VERSION 경유) ·
> `launch.py` 의 `reload_for_tool` / import 경로. 이 툴은 핫키를 심지 않아 핫키 항목은 해당 없음.
> 폴더를 갈랐으므로 **버전은 `03.00`** 이다(6-4 의 `02.00` 대신).

원래 권장안은 아래와 같았다 — **가르지 않는다.**

- A00110 이 V02 로 가른 이유는 재분류와 **동시에 Curve Filters 이식**이라는 기능 추가가
  예정돼 있었기 때문이다. 여기는 **UI 묶기뿐**이라 되돌릴 일이 생기면 커밋 하나를 되돌리면 된다.
- 이미 `A00060_jointTool`(구) + `A00060_jointTool_V02` 두 폴더가 있다. 또 가르면 조인트 툴이 3개가 된다.
- 드롭 파일 · 셸프 라벨 · 아이콘 · `WINDOW_OBJECT_NAME` · 창 제목 · `launch.py` 임포트까지 전부
  갈아야 한다(`wip-a00110-tab-taxonomy` 의 복제 체크리스트).

→ **제자리에서 버전만 올린다.**

---

## 7. 구현 방식 — 골격은 A00275 와 같다

`_build_curve_tab` 과 `_build_hair_tab` 은 **쪼개진다**(접이식 섹션이 각각 하위 탭 페이지가 된다).
`_build_divide_tab` · `_build_aim_tab` · `_build_ik_edit_tab` 은 **이름도 내용도 그대로** 둔다.

```python
# app/ui/main_window.py

# (하위 탭 라벨, 툴팁, 빌더 메서드 이름)
CREATE_PAGES = (
    ("From Curve",  "From Curve - build a joint chain on the points of a NURBS curve.",
     "_build_create_from_curve_tab"),
    ("From Object", "From Object - build a joint at each listed object or vertex, "
                    "with axis options.", "_build_create_from_object_tab"),
    ("Divide",      "Divide - build evenly spaced joints between a start and an end joint.",
     "_build_divide_tab"),                                   # ← 기존 메서드 그대로
)
ORIENT_PAGES = (
    ("Aim",             "Aim - re-orient a chain so that the chosen axis points at a "
                        "pole target.", "_build_aim_tab"),   # ← 기존 메서드 그대로
    ("Set Orient",      "Set Orient - set jointOrient on a chain by axis and degree.",
     "_build_set_orient_tab"),
    ("Orient / Rotate", "Orient / Rotate - swap values between jointOrient and rotate.",
     "_build_orient_swap_tab"),
)
CHAIN_PAGES = (
    ("Reverse", "Reverse - rebuild a joint chain in the opposite order.",
     "_build_chain_reverse_tab"),
    ("IK Edit", "IK Edit - edit the bone chain while the IK handle and its pole vector "
                "stay in place.", "_build_ik_edit_tab"),     # ← 기존 메서드 그대로
)
CURVE_PAGES = (
    ("Edit Curve", "Edit Curve - separate, remove by length, and rebuild NURBS curves.",
     "_build_curve_edit_tab"),
    ("Clusters",   "Clusters - create one cluster deformer per CV of the listed curves.",
     "_build_curve_cluster_tab"),
)
SELECT_PAGES = (
    ("Unused Joints", "Unused Joints - select the listed joints that no skinCluster uses.",
     "_build_select_unused_tab"),
)

# (상위 탭 라벨, 툴팁, 하위 페이지 표, 하위 QTabWidget 을 담을 속성 이름)
CATEGORIES = (
    ("Create", "Create new joints.", CREATE_PAGES, "create_tabs"),
    ("Orient", "Change the orientation of joints that already exist. Nothing is moved "
               "and no joint is added.", ORIENT_PAGES, "orient_tabs"),
    ("Chain",  "Rebuild or edit a joint chain that already exists.",
     CHAIN_PAGES, "chain_tabs"),
    ("Curve",  "Prepare the curves that joints get built on. No joint is touched.",
     CURVE_PAGES, "curve_tabs"),
    ("Select", "Find joints. The scene is not changed.", SELECT_PAGES, "select_tabs"),
)

def _build_category_tab(self, pages, attr):
    """카테고리 상위 탭 하나 — 기능들을 하위 탭으로 담는다."""
    tabs = self._build_sub_tabs(pages)
    setattr(self, attr, tabs)
    return tabs

def _build_sub_tabs(self, pages):
    tabs = QTabWidget()
    tabs.tabBar().setElideMode(Qt.ElideRight)      # 폭이 모자라면 라벨을 자른다
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

`build_ui()` 의 `addTab` 5줄은 이렇게 바뀐다.

```python
self.tabs = QTabWidget()
for label, tip, pages, attr in self.CATEGORIES:
    index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
    self.tabs.setTabToolTip(index, tip)
    if label == "Chain":
        self.chain_page = self.tabs.widget(index)      # 9장에서 쓴다
self.tabs.currentChanged.connect(self._on_tab_changed)
self.chain_tabs.currentChanged.connect(self._on_tab_changed)
main_layout.addWidget(self.tabs)
```

`QScrollArea` 는 `Framework.qt.qt` 와일드카드 임포트에 이미 들어와 있다(추가 임포트 불필요).

### 쪼개지는 두 빌더 — 새 빌더 8개

| 새 빌더 | 어디서 잘라 오나 | 리스트 |
|---|---|---|
| `_build_create_from_curve_tab` | `_build_curve_tab` 의 `box_crv` (단, `Clusters` 버튼은 뺀다) | `tsl_create_crv` |
| `_build_create_from_object_tab` | `_build_curve_tab` 의 `box_obj` 전체 | `tsl_create_obj` |
| `_build_set_orient_tab` | `_build_curve_tab` 의 `box_set` (접힘 해제) | `tsl_orient_set` |
| `_build_orient_swap_tab` | `_build_curve_tab` 의 `box_swap` | `tsl_orient_swap` |
| `_build_curve_edit_tab` | `_build_hair_tab` 의 `box_crv` 전체 | `tsl_curve_edit` |
| `_build_curve_cluster_tab` | `_build_curve_tab` 의 `Clusters` 버튼 | `tsl_curve_cluster` |
| `_build_chain_reverse_tab` | `_build_hair_tab` 의 `box_edit` 중 `Remove origin` + `Reverse joint chain` | `tsl_chain_reverse` |
| `_build_select_unused_tab` | `_build_hair_tab` 의 `Select Unused Joints` | `tsl_select_unused` |

**`CollapsibleBox` 는 이 작업 뒤 한 번도 쓰이지 않는다.**
→ `app/ui/collapsible.py` 와 그 import 를 지운다. 나중에 필요하면 공용
`Framework.qt.JUN_mod_collapsible_qt` 를 쓴다(툴 로컬 사본을 다시 만들지 않는다).

---

## 8. 리스크 ① — 공용 리스트를 쪼갤 때 참조가 새어 나간다 ★

`tsl_curve` 는 **6곳**, `tsl_hair` 는 **5곳**에서 참조된다. 두 속성이 사라지면 대부분
`AttributeError` 로 즉시 드러난다 — **다만 다음 두 개는 에러 없이 조용히 틀린다.**

| 조용히 틀리는 지점 | 왜 |
|---|---|
| `on_match_to_sel` 의 `self.tsl_curve.is_order_tracking()` / `.maya_selection()` | 다른 하위 탭의 TSL 을 가리켜도 **에러가 나지 않는다.** 사용자가 `From Object` 에서 켠 `Order` 가 무시되고 버텍스가 인덱스 순으로 처리된다(`tsl-selection-order` — pref 가 꺼져 있으면 `ls(os)` 도 에러 없이 인덱스 순서를 준다) |
| `on_hair_select_unused` 의 `self.tsl_hair.select_by_texts(unused)` | 다른 리스트를 하이라이트하면 **화면상 아무 일도 안 일어난 것처럼 보인다**(씬 선택은 되므로 반쯤 동작해 더 헷갈린다) |

**대응**: 재분류 **전에** `grep -n "tsl_curve\|tsl_hair" app/ui/main_window.py` 로 참조 11곳을
전부 뽑아 6-1 표의 새 속성에 **1:1 로 대응시킨 표를 만들고**, 작업 후 두 옛 이름이
**0건**인지 다시 grep 한다. 위 두 항목은 검증 계획(11장)에 개별 항목으로 넣는다.

---

## 9. 리스크 ② — IK Edit 의 씬 상태 동기화 (**적용함** — v03.00)

`IK Edit` 탭은 **편집 상태를 UI 가 아니라 ikHandle 노드에 둔다**(`docs/A00060_jointTool_V02.md` 8-6).
`_adopt_scene_ik_edits()` 가 그 상태를 되찾는데, **지금은 `_build_ik_edit_tab()` 안에서
창을 만들 때 딱 한 번만 호출된다.** 탭을 바꿔도 다시 읽지 않는다.

- **재분류 자체가 이것을 깨지는 않는다.** A00275 를 물어뜯었던 함정(상위 탭 **인덱스**로 갈라
  쓰던 `_on_tab_changed` 가 중첩 뒤 영영 일치하지 않게 되는 것 — `wip-a00275-tab-reorg`)은
  **이 툴엔 해당하지 않는다.** `currentChanged` 연결이 소스에 0건이기 때문이다(grep 확인).
- 다만 **이미 있는 약점**이다. 툴을 열어 둔 채 다른 창에서 편집을 시작/종료하면
  버튼 색과 실제 씬이 어긋난다.

→ **이번에 같이 고치기를 권장한다** (약 10줄, 7장 코드에 배선이 이미 들어 있다).
A00275 와 같이 **인덱스가 아니라 "지금 보이는 페이지"** 로 판단한다.

```python
IKE_SUB_INDEX = 1        # CHAIN_PAGES 안에서 IK Edit 의 자리

def _on_tab_changed(self, *_):
    """IK 편집 상태는 씬에 있다. Chain > IK Edit 이 보일 때 다시 읽어 화면을 맞춘다.

    상위/하위 두 QTabWidget 이 같은 슬롯에 물려 있다. 상위는 **위젯 동일성**으로,
    하위는 CHAIN_PAGES 순서와 묶인 상수로 판단한다(상위 탭 인덱스는 탭이 늘면 뜻이 변한다).
    """
    if self.tabs.currentWidget() is not self.chain_page:
        return
    if self.chain_tabs.currentIndex() != IKE_SUB_INDEX:
        return
    self._adopt_scene_ik_edits()
    self._update_ike_state()
```

`chain_tabs.widget(i)` 가 돌려주는 것은 페이지가 아니라 **`QScrollArea` 래퍼**다 —
위젯 비교로 하위 탭을 찾으려 하면 헷갈린다. 하위는 인덱스 상수를 쓰는 편이 단순하다.

> 범위를 엄격히 지키고 싶으면 이 항목만 빼고 별도 커밋으로 미룰 수 있다. 그때는
> `_on_tab_changed` 배선(7장 `build_ui()`)도 함께 빼서 **죽은 슬롯을 남기지 않는다.**

---

## 10. 그 밖의 리스크와 대응

| # | 리스크 | 대응 |
|---|---|---|
| 10-1 | 상위 5 · 하위 3 탭 바가 창 폭 **540** 에서 잘린다 | `setElideMode(Qt.ElideRight)` + 짧은 라벨(4장). 실측 후 `win_width` 540 → 560~580 검토. 가장 긴 하위 조합은 `Orient` 의 `Aim` / `Set Orient` / `Orient / Rotate` |
| 10-2 | 중첩 탭 바가 세로를 한 줄(약 26~30px) 더 먹는다 | 반대로 **페이지는 짧아진다** — 접이식 4섹션이 한 화면에 쌓이던 `Curve` 탭이 1섹션짜리 하위 탭 4개로 갈라진다. 가장 긴 페이지는 여전히 `Orient > Aim`(TSL 3개 가로 배치). `win_height` 820 → **실측 후 하향** 검토 |
| 10-3 | **이중 스크롤** | 스크롤은 **하위 페이지에만**. 상위 카테고리 페이지는 `QTabWidget` 자체를 그대로 돌려준다 (`prefer-subtabs-over-stacked-collapsibles`) |
| 10-4 | TSL 이 스크롤 안에서 높이를 잃는다 | **TSL 위젯 전체에 `setMaximumHeight` 금지** — 리스트 최소 높이가 안 줄어 버튼에서 높이를 빼앗아 글자가 잘린다(`tsl-widget-max-height-squeezes-buttons`). 지금 코드는 `list_min_height=160` 만 쓴다(안전) — 그대로 유지 |
| 10-5 | 테마 qss(`dark.qss` / `red.qss`)가 중첩 `QTabWidget` 을 예상하지 않았을 수 있다 | 실제 Maya 에서 두 테마로 눈 확인. 필요하면 qss 는 **건드리지 않고** 하위 탭에 `setObjectName` 을 주는 선에서 처리 |
| 10-6 | TSL 이 6개 → 10개로 늘어 창이 무거워진다 | 비용은 **항목 수 × UUID 조회**지 위젯 수가 아니다(`framework-tsl-list-limit`). 빈 리스트 4개 추가는 무시할 수준 — 그래도 기동 시간을 한 번 잰다 |
| 10-7 | 사용자 근육기억이 깨진다 | 4장 순서로 최소화. CHANGELOG 에 5장 이동 매핑 표를 그대로 싣는다. **`Hair` 라는 이름이 사라지는 것**을 CHANGELOG 첫 줄에 명시(헤어 리깅에 쓰던 기능은 `Curve > Edit Curve` + `Chain > Reverse`) |
| 10-8 | 드롭 파일 · 셸프 · 아이콘 | **손대지 않는다.** 폴더를 가르지 않으므로(6-6) 전부 그대로다 |

---

## 11. 검증 계획

**`app/core/*` 를 건드리지 않으므로 코어 회귀는 "그대로 통과" 가 목표다.**

1. **문법 · 임포트** — `mayapy` 로 `import tools.A00060_jointTool_V02.app.ui.main_window`.
2. **재분류 전 스냅샷 → 후 diff** (A00110 에서 검증된 방법, `wip-a00110-tab-taxonomy`):
   `MainWindow` 를 headless 로 띄워 **위젯 속성 이름 집합 + 탭 트리**를 json 으로 남기고,
   재분류 후 다시 떠서 diff. **사라져야 하는 것은 `tsl_curve` · `tsl_hair` 둘뿐**이고,
   새로 생기는 것은 카테고리 5 + 새 TSL 6개여야 한다. 그 밖에 사라진 속성이 있으면
   핸들러 하나가 이미 깨진 것이다.
   - `mayapy` Qt 테스트는 **`QApplication` 을 `standalone.initialize()` 앞에** 만든다
     (`qapplication-before-maya-standalone` — 뒤면 `QWidget` 에서 무단 종료).
3. **UI 스모크** (약 40항목):
   - 상위 탭이 정확히 5개(`Create` / `Orient` / `Chain` / `Curve` / `Select`)이고 순서가 맞는가
   - 하위 탭 11개가 **전부** 존재하고 라벨이 5장 매핑과 일치하는가
   - 탭마다 대표 위젯 접근 — `tsl_create_crv` · `rb_point_group` · `tsl_create_obj` ·
     `cmb_fwd_axis` · `sb_div_num` · `tsl_aim_pole` · `cmb_aim_axis` · `dsb_orient_deg` ·
     `cb_remove_origin` · `btn_ike_edit` · `dsb_max_len` · `sb_max_jnts` ·
     `tsl_curve_cluster` · `tsl_select_unused`
     (스크롤 래핑 뒤에도 `self.*` 참조가 살아 있는지가 핵심)
   - **`tsl_curve` / `tsl_hair` 참조가 소스에 0건**인가 (8장)
4. **8장 전용 회귀 2건 — 이번 작업의 진짜 통과 기준**:
   - `From Object` 의 `Order` 를 켜고 버텍스를 순서대로 골라 `Match to Sel` → **고른 순서대로**
     체인이 생기는가 (다른 탭의 TSL 을 읽고 있으면 인덱스 순으로 나온다)
   - `Unused Joints` 실행 후 **그 탭의 리스트**가 하이라이트되는가
5. **씬 동작 회귀** — 15기능을 각각 최소 1회 실행해 `[OK]` 로그가 뜨는지(코어 무변경 확인).
6. **9장을 포함했다면** — `ike_mgr.begin_edit` 를 코어로 직접 켠 뒤 ① 다른 카테고리로 갔다가
   ② `Chain > IK Edit` 으로 돌아오면 버튼이 켜진 상태로 복원되는가.
7. **실제 Maya 확인**(사용자) — 폭 540 에서 상위·하위 탭 바가 잘리지 않는지, 두 테마에서 중첩 탭이
   정상인지, `Orient > Aim` 의 TSL 3개가 스크롤 안에서 정상인지.

---

## 12. 작업 단계

1. **참조 지도부터.** `grep -n "tsl_curve\|tsl_hair"` 로 11곳을 뽑아 6-1 표에 1:1 대응시킨다(8장).
2. 재분류 **전** 스냅샷 채취(11-2).
3. `_scrolled` / `_build_sub_tabs` / `_build_category_tab` + `*_PAGES` · `CATEGORIES` 표 추가.
4. `_build_curve_tab` · `_build_hair_tab` 을 새 빌더 8개로 쪼갠다(7장 표).
   **`_build_divide_tab` · `_build_aim_tab` · `_build_ik_edit_tab` 은 한 줄도 고치지 않는다.**
5. 핸들러 11곳의 리스트 참조를 새 속성으로 교체.
6. `build_ui()` 의 `addTab` 5줄을 루프로 교체. `app/ui/collapsible.py` 삭제 + import 제거.
7. (결정 시) 9장 `_on_tab_changed` 추가.
8. 창 크기 실측 조정(10-1 · 10-2).
9. 스냅샷 diff + UI 스모크 + 씬 동작 회귀 실행(11장).
10. 파일 헤더 주석의 탭 목록(현재 "3탭 … 총 4탭" 서술)을 새 구조로 고쳐 쓴다.
11. 버전 `01.05 → 03.00`(6-4 + 6-6 번복), `LAST_UPDATE` 갱신.
12. 문서 갱신 —
    `docs/A00060_jointTool_V03.md` **신규**(V02 문서를 바탕으로 3~5장을 새 구조로 재구성),
    `CHANGELOG.md` v03.00(5장 매핑 표 + `Hair` 이름 소멸 안내 + 버전 번호 정정 사유),
    `WORKLOG.md`, `portfolio_EN` / `portfolio_KR` 동시 갱신,
    메모리(`wip-a00060-*` 2건에 "카테고리 하위" 표기 추가 + 새 메모 1건).
13. 사용자 Maya 확인 → 반영.

---

## 13. 이 계획서가 하지 않는 것

- **기능 추가 · 삭제 · 동작 변경 없음.** 버튼과 옵션 위젯은 하나도 바뀌지 않는다.
- **`app/core/*` 수정 없음.** 매니저 6개는 그대로다.
- **버튼 라벨 변경 없음**(6-5). 바뀌는 것은 탭 라벨과, 사라지는 접이식 섹션 제목뿐이다.
- ~~**폴더 분리 없음**(6-6)~~ — **사용자 지시로 `A00060_jointTool_V03` 로 갈랐다.**
  드롭 파일 · 셸프 라벨 · 아이콘 · `WINDOW_OBJECT_NAME` 을 전부 새로 지어 V02 와 공존한다.
- **공용 위젯(`Framework/qt/*`) 수정 없음.** `_scrolled` / `_build_sub_tabs` 는 A00110 · A00145 ·
  A00275 와 같은 코드지만, **공용으로 빼는 것은 이 작업의 범위가 아니다**
  (네 번째 사례가 되므로 공용화 검토는 별건으로 올린다).
- `Clusters` 의 타입 미검사(1-4)는 **고치지 않는다** — 동작 변경이라 별건이다.
  이번 재분류로 리스트가 갈리면 실수 자체가 어려워진다.
