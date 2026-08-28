---
title: A00130_ControlRig_V02 — 길이 수치(Length) 기능 계획서
aliases: [A00130 Length, 길이 수치, 옵션 컨트롤러 길이]
tags: [plan, A00130, ControlRig, rigging]
updated: 2026-08-28
---

# A00130_ControlRig_V02 — 길이 수치(Length) 기능 계획서

> **한 줄**: **템플릿 조인트 사이의 거리**를 재서 **옵션 컨트롤러의 어트리뷰트에 써 넣는다.**
> 본 계획서: [`A00130_ControlRig_V02_plan.md`](A00130_ControlRig_V02_plan.md) 의 **Phase 6 "길이 수치"** 를 펼친 것.
> 툴 문서: [`../A00130_ControlRig_V02.md`](../A00130_ControlRig_V02.md)

---

## 1. V01 이 하던 것 (근거)

`A00130_ControlRig/app/core/rig_matcher.py` 에 부위별로 같은 모양이 네 번 나온다.

```python
# rig_matcher.py:255  (match_cage_arm_left 안)
dist_arm_l_all = self.get_distance(self.tgt[0], self.tgt[2])
dist_arm_l_up  = self.get_distance(self.tgt[0], self.tgt[1])
dist_arm_l_low = self.get_distance(self.tgt[1], self.tgt[2])

MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".Arm_L",     dist_arm_l_all)
MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".arm_l_up",  dist_arm_l_up)
MayaScene.set_attr(cage_given.rnm_optionCtl[0] + ".arm_l_low", dist_arm_l_low)
```

| 부위 | 위치 | 전체 | 위 | 아래 |
|---|---|---|---|---|
| Arm L | `rig_matcher.py:255` | `.Arm_L` | `.arm_l_up` | `.arm_l_low` |
| Arm R | `rig_matcher.py:293` | **`.Arm_r`** | `.arm_r_up` | `.arm_r_low` |
| Leg L | `rig_matcher.py:306` | `.Leg_L` | `.leg_l_up` | `.leg_l_low` |
| Leg R | `rig_matcher.py:319` | `.Leg_R` | `.leg_r_up` | `.leg_r_low` |

**재는 대상**은 `self.tgt[0..2]` — 사용자가 TSL 에 **손으로 순서대로 담은 아바타 본** 세 개다.
거리는 `MayaScene.distance` (`maya_scene.py:224`) — `xform -ws -t` 두 점의 유클리드 거리.

### 1-1. 써야 하는 어트리뷰트 — **12개 전부**, 하나도 빼지 않는다 ★

부위마다 **세 개씩**이다. `_up` · `_low` 는 `total` 만큼이나 필수다 — **네 개(전체)만 쓰고
나머지 여덟 개를 빠뜨리면 안 된다.**

| # | 어트리뷰트 | 값 | 부위 |
|---|---|---|---|
| 1 | `.Arm_L` | `upperarm → hand` | Arm L 전체 |
| 2 | `.arm_l_up` | `upperarm → lowerarm` | Arm L 위 |
| 3 | `.arm_l_low` | `lowerarm → hand` | Arm L 아래 |
| 4 | `.Arm_r` | `upperarm → hand` | Arm R 전체 |
| 5 | `.arm_r_up` | `upperarm → lowerarm` | Arm R 위 |
| 6 | `.arm_r_low` | `lowerarm → hand` | Arm R 아래 |
| 7 | `.Leg_L` | `thigh → foot` | Leg L 전체 |
| 8 | `.leg_l_up` | `thigh → calf` | Leg L 위 |
| 9 | `.leg_l_low` | `calf → foot` | Leg L 아래 |
| 10 | `.Leg_R` | `thigh → foot` | Leg R 전체 |
| 11 | `.leg_r_up` | `thigh → calf` | Leg R 위 |
| 12 | `.leg_r_low` | `calf → foot` | Leg R 아래 |

> **개수를 확인했다.** V01 툴(`A00130_ControlRig`) · 아카이브
> `_archive/legacy_tools/01_Modules/JUN_PY_ControlRigTool_V01_02~07.py` ·
> `_archive/legacy_tools/03_Modules_Test/11_ControlRig_V01_01~07.py` 를 전부 훑었을 때
> 옵션 컨트롤러에 쓰는 `setAttr` 은 **어느 버전에서도 정확히 이 12개**이고 그 밖에는 없다
> (V01_02·03 과 테스트본 01~04 는 아직 0개 — 기능이 V01_05 에서 들어왔다).
>
> **json 은 이 12개를 그대로 담는다**(4-1). 검증 항목 6번이 **12개가 다 써지는지**를 센다(10장).
> **혹시 케이지에 이 12개 말고 더 써야 하는 어트리뷰트가 있다면**(V01 이 쓰지 않던 것)
> 그건 코드에서 알아낼 수 없으니 **이름을 주셔야 한다** — 열린 질문 E.

**옵션 컨트롤러**는 `cage_model.py:364` `set_selected_objs()` 가 찾는다 —
`CH_n_MainGlobal_xx_zro` 를 고른 뒤 그 **계층 전체를 훑어** 이름에 토큰
`OptionAll_xx_ctl` 이 **들어 있는** 노드를 모은다(`constants.py:73-74`).

---

## 2. V02 에서 무엇이 달라지나

| | V01 | **V02** |
|---|---|---|
| 재는 대상 | 아바타 본, **TSL 에 손으로 순서대로** | **템플릿 조인트**, 짝은 **json 이 갖는다** |
| 부위 추가 | `rig_matcher` 에 함수 하나 + 하드코딩 6줄 | **json 한 항목** |
| 옵션 컨트롤러 | 계층을 토큰으로 훑는다 | **json 에 이름**, `su.resolve()` 로 찾는다(네임스페이스) |
| 실행 시점 | Match 안에 **끼어 있다** (부위 매칭 함수가 겸업) | **별도 단계** — 값을 보고 나서 쓴다 |
| 미리보기 | 없다 | **`plan()` 이 값을 표로 보여 준다**(씬 불변) |
| 실패 | `setAttr` 예외가 그대로 올라가 **Match 전체가 중단**된다 | **사전 점검 후 건너뛰고 계속**(1-12) |
| undo | 없다 | **한 스텝** |

> 재는 대상을 아바타 본에서 **템플릿 조인트**로 옮기는 것이 이 기능의 핵심이다.
> 템플릿 조인트는 이미 사람이 아바타에 맞춰 놓은 것이므로 **값은 같고**,
> **아바타의 조인트 이름에 의존하지 않게 된다.**

---

## 3. 실측으로 확인한 것 ★

mayapy headless 로 직접 재 봤다. 아래 다섯 개가 설계를 갈랐다.

### 3-1. `all` 은 `up + low` 가 **아니다** — 직선 거리다

세 조인트가 직렬로 이어져 있으므로 `tgt[0]→tgt[2]` 는 **팔꿈치를 무시한 직선**이다.

| 팔꿈치 각도 | `all` (직선) | `up + low` (합) | 차 |
|---|---|---|---|
| 0° (곧을 때) | 20.0000 | 20.0000 | 0.000000 |
| 5° | 19.9810 | 20.0000 | **−0.10 %** |
| 30° | 19.3185 | 20.0000 | **−3.4 %** |

**아바타는 보통 팔꿈치·무릎이 조금 굽어 있다.** IK 스트레치의 기준 길이로 쓴다면
대개 필요한 값은 **`up + low`(완전히 폈을 때의 길이)** 지 직선 거리가 아니다.
직선 거리를 쓰면 **스트레치가 실제보다 일찍 걸린다.**

→ **열린 질문 A** (8장). 기본값은 **V01 과 같은 직선**으로 두되, **json 에서 고를 수 있게** 하고
**두 값의 차이를 UI 에 보여 준다.** 조용히 바꾸지 않는다.

### 3-2. 없는 어트리뷰트에 `setAttr` → **예외**, 그리고 V01 은 그것을 **안 삼킨다**

```
RuntimeError: setAttr: No object matches name: opt.Arm_r
```

`rig_matcher.py` 의 `try/except` 는 **임시 조인트 삭제 자리(279-282)에만** 있고,
`setAttr` 세 줄과 호출부(`main_window.py:241 on_match`)에는 **없다.**

> **본 계획서 5-1 의 메모를 정정한다.** 거기서는 `Arm_r` 이 오타라면 "오른팔 길이가
> **조용히** 안 써지고 있었다" 고 적었는데, **조용하지 않다** — 예외가 `on_match` 밖으로
> 올라가 **Match 전체가 그 자리에서 멈춘다.**
> 즉 사용자가 V01 로 Match 를 끝까지 돌린 적이 있다면 **`.Arm_r` 은 실제 어트리뷰트 이름**이다
> (리그 쪽 이름이 불규칙한 것). 그래도 **가정하지 않고 툴이 실행 시점에 확인**한다(4-4).

### 3-3. `min`/`max` 는 **자르지 않고 예외를 낸다**

```
RuntimeError: setAttr: Cannot set the attribute 'opt.Arm_L' past its maximum value of 10
```

→ 값은 그대로 `0.0`. **거리는 범위를 쉽게 넘는다**(cm 단위면 팔 길이가 30~70).
범위는 `attributeQuery(node=, maxExists=True/max=True)` 로 **미리 조회할 수 있다.**

### 3-4. 잠김과 연결은 **같은 에러**를 낸다

```
RuntimeError: setAttr: The attribute 'opt.leg_l_up' is locked or connected and cannot be set
```

→ 이미 `scene_utils._plug_writable()` 이 **잠금 + `connectionInfo(isDestination=True)`** 로
판정하고 있다. **그대로 재사용한다** (`getAttr(settable=True)` 는 쓰지 않는다).

### 3-5. 거리는 **씬 선형 단위**를 탄다

같은 두 점(10 cm) 을 재면:

| `currentUnit(linear=)` | 결과 |
|---|---|
| `cm` | 10.0000 |
| `m` | 0.1000 |
| `mm` | 100.0000 |

→ 쓰는 값이 **씬 단위에 따라 100배까지 달라진다.** 툴은 단위를 **바꾸지 않고**,
**어떤 단위로 쟀는지 UI 와 로그에 적는다**(4-5).

---

## 4. 설계 판단

### 4-1. 데이터는 **별도 json** — `length_map.json`

`template_map.json` 은 "조인트 → 세트" 표다. 모양이 다른 데이터를 섞지 않는다.
같은 **버전 폴더**에 파일을 하나 더 둔다 — 케이지 버전이 갈리면 함께 갈린다.

```
app/data/mapping/v001/
├── template_map.json     (기존)
└── length_map.json       (신규)
```

```jsonc
{
  "option_ctl": "OptionAll_xx_ctl",
  "total_mode": "straight",              // 기본값. "sum" 도 가능 (3-1)
  "measures": [
    {
      "part":  "Arm_L",
      "chain": ["helper_upperarm_l", "helper_lowerarm_l", "helper_hand_l"],
      "attrs": { "total": "Arm_L", "upper": "arm_l_up", "lower": "arm_l_low" }
    },
    {
      "part":  "Arm_R",
      "chain": ["helper_upperarm_r", "helper_lowerarm_r", "helper_hand_r"],
      "attrs": { "total": "Arm_r", "upper": "arm_r_up", "lower": "arm_r_low" }
    },
    {
      "part":  "Leg_L",
      "chain": ["helper_thigh_l", "helper_calf_l", "helper_foot_l"],
      "attrs": { "total": "Leg_L", "upper": "leg_l_up", "lower": "leg_l_low" }
    },
    {
      "part":  "Leg_R",
      "chain": ["helper_thigh_r", "helper_calf_r", "helper_foot_r"],
      "attrs": { "total": "Leg_R", "upper": "leg_r_up", "lower": "leg_r_low" }
    }
  ]
}
```

**어트리뷰트 이름을 좌우 대칭으로 유도하지 않는다.** `Arm_L` ↔ `Arm_r` 처럼 **규칙이 깨져 있어서**
(`_L` 대문자 vs `_r` 소문자) 유도하면 한쪽이 조용히 틀린다. **전부 적는다.**

`chain` 은 **길이 3 고정이 아니라 목록**으로 둔다 — 스파인처럼 마디가 더 많은 부위를 나중에
붙일 때 `attrs` 만 늘리면 되도록. `upper`/`lower` 가 없는 부위(전체 길이만)도 허용한다.

> `chain` 의 조인트 이름은 `template_map.json` 에 **실제로 있는지 로드 시 검증**한다.
> 오타가 나면 조용히 0 이 써지는 게 아니라 **로드 단계에서 잡힌다.**

### 4-2. 옵션 컨트롤러 — 이름으로 자동, 안 되면 **손으로** ★

**2026-08-28 정정 — 처음 설계가 실제 씬에서 실패했다.**

`option_ctl` 을 `OptionAll_xx_ctl` 로 적었는데, 그건 **V01 의 토큰**이지 노드 이름이 아니었다.
V01 은 `"OptionAll_xx_ctl" in obj` 로 **부분 매칭**했고, **실제 이름은
`CH_n_OptionAll_xx_ctl`** 이다. 사용자가 "옵션 컨트롤러를 찾지 못한다" 고 보고했다.

원인을 재 보니 **셋이 겹쳐** 있었다.

| # | 함정 | 실측 |
|---|---|---|
| 1 | json 에 **토큰**을 전체 이름으로 적었다 | `objExists("OptionAll_xx_ctl")` → False |
| 2 | **`ls("*tok*")` 는 네임스페이스를 넘지 않는다** | 노드가 `CAGE:CH_n_...` 면 **빈 목록**. `recursive=True` 라야 찾는다 |
| 3 | **`ls` 가 셰이프까지 잡는다** | 컨트롤러는 nurbsCurve → `...ctlShape` 동반 → 후보 2개 → **"여럿이면 멈춘다" 에 잘못 걸린다** |

2번 때문에 폴백조차 못 갔고, 설령 갔어도 3번에 걸렸을 것이다.

**고친 방식 — 3단계로 찾고, 마지막은 사람이다**

| 순서 | 방법 | `how` |
|---|---|---|
| 1 | **수동 지정**(`Get Selected` / 필드에 직접 입력) — **있으면 이것이 이긴다** | `manual` |
| 2 | `su.resolve(name, ns)` — 네임스페이스 붙인 쪽 먼저, 없으면 이름 그대로 | `exact` |
| 3 | `token_search()` — `ls("*name*", recursive=True, type="transform")` | `token` |

- json 에는 **전체 이름**(`CH_n_OptionAll_xx_ctl`)을 적는다. 3번이 부분 매칭이므로
  **접두사가 붙어도 찾는다.**
- 3번에서 **하나면 쓰되 "이름으로 맞췄다" 고 알린다**(`how = token`) — 조용히 넘어가지 않는다.
- **여럿이면 고르지 않는다.** 후보를 보여 주고 **`Get Selected` 로 지정하라**고 한다.
  V01 은 `rnm_optionCtl[0]` 으로 첫 개를 골랐다 — 남의 노드에 조용히 쓰는 게 최악이다.

**자동이 안 되는 상황을 전제로 만든다.** 리그 이름 규칙은 프로젝트마다 다르므로
**자동 탐지는 편의고, 수동 지정이 보장이다.** UI 에 이름 필드 + `Get Selected` + `Auto` 를 둔다:

- **`Get Selected`** — 선택한 것을 쓴다. **셰이프를 골랐으면 트랜스폼으로 올려 준다**
  (컨트롤러는 커브라 셰이프가 잡히기 쉽다).
- **`Auto`** — 손으로 지정한 것을 버리고 다시 자동으로 찾는다.
- 필드에 **직접 타이핑**해도 된다. 없는 이름이면 거부하고 알린다.
- 지금 어떻게 정해졌는지(`set by hand` / `found by name` / `matched by name - check it is
  the right node` / `not found`) 를 **항상 표시**한다.

> **교훈**: **V01 의 상수가 전체 이름이라고 가정한 것**이 시작이었다. 상수 이름
> (`TKN_OPTION_CTL` — **TKN** = token)이 이미 말해 주고 있었는데 쓰는 쪽 코드
> (`if self.tkn_optionCtl in obj`)를 안 봤다. **상수를 옮길 때는 그 상수가 어떻게 쓰이는지
> 함께 옮겨야 한다.**

### 4-3. `plan()` / `apply()` 를 가른다 — Match 와 같은 구조

- `plan(measures, option_ctl, namespace, total_mode)` → **씬을 안 바꾸고** 행 목록을 만든다.
  각 행: `part · chain · total · upper · lower · attrs · status · note`
- `apply(rows)` → `undo_chunk()` 안에서 `setAttr`.

**값을 먼저 보고 쓴다.** 길이는 눈으로 검산할 수 있는 수치라 미리보기의 값어치가 크다
(팔 길이가 `0.35` 로 나오면 씬 단위가 m 인 것을 바로 안다).

### 4-4. 쓰기 전 **사전 점검** — 3-2 · 3-3 · 3-4 를 전부 미리 본다

`setAttr` 을 그냥 던지고 예외를 받는 대신, 행마다 먼저 판정한다.

| 점검 | 방법 | 실패 시 |
|---|---|---|
| 조인트가 있나 | `su.resolve()` | `joint missing` — 건너뛰고 계속 |
| 옵션 컨트롤러가 있나 | `su.resolve()` (4-2) | 전체 중단 (쓸 곳이 없다) |
| 어트리뷰트가 있나 | `cmds.objExists("ctl.Arm_r")` | `attr missing` — **그 행만** 건너뛴다 |
| 쓸 수 있나 | `su.plug_writable()` (3-4) | `locked or connected` |
| 범위 안인가 | `attributeQuery(minExists/maxExists)` (3-3) | `out of range (max 10)` — **쓰지 않는다** |

> **자르지 않는다.** 범위를 넘으면 잘라서 쓰는 게 아니라 **거부하고 알린다** —
> 잘린 길이는 틀린 리그를 조용히 만든다.

`_plug_writable` 은 지금 밑줄 이름이다. **공개 이름(`plug_writable`)으로 올리고** 기존 호출부를
따라 고친다 — 두 번째 소비자가 생겼으니 내부 헬퍼가 아니다.

### 4-5. 씬 단위는 **바꾸지 않고 표시한다**

`cmds.currentUnit(query=True, linear=True)` 를 읽어 UI 라벨과 로그에 붙인다 —
`Measured in cm`. 툴이 단위를 바꾸면 **씬의 다른 것들이 다 틀어지므로** 절대 바꾸지 않는다.

### 4-6. 실행 시점 — **템플릿 조인트를 놓은 뒤**

이 단계는 **템플릿 조인트가 이미 아바타에 맞춰져 있다는 것**에 의존한다.
Match 를 돌리기 **전에도 후에도** 값은 같다(Match 는 케이지를 움직이지, 조인트를 움직이지 않는다).
→ **Match 와 순서 의존이 없다.** 다만 조인트가 전부 원점에 있으면 길이가 전부 0 이므로,
**모든 값이 0 이면 "조인트를 아직 안 놓은 것 같다" 고 경고**한다.

---

## 5. 파일 구조

```
A00130_ControlRig_V02/
├── app/core/
│   ├── scene_utils.py        (수정) _plug_writable -> plug_writable 공개
│   ├── mapping_data.py       (수정) load_length(version) 추가 + 검증
│   └── length_manager.py     ★ 신규 — distance / plan / apply
├── app/data/mapping/v001/
│   └── length_map.json       ★ 신규
└── app/ui/main_window.py     (수정) STEPS 에 "Length" 한 줄
```

`length_manager.py` 공개 함수:

| 함수 | 하는 일 |
|---|---|
| `distance(a, b)` | `xform -ws -t` 두 점의 유클리드 거리 |
| `chain_lengths(chain)` | 마디별 거리 목록 + 직선 거리 |
| `plan(measures, option_ctl, namespace, total_mode)` | 씬 불변. 행 목록 |
| `apply(rows)` | `undo_chunk()` 안에서 `setAttr`. `(results, messages)` |
| `summarize(rows)` | 상태별 개수 |

상태 코드는 Match 와 같은 결을 쓴다 —
`ST_OK` · `ST_NO_JOINT` · `ST_NO_ATTR` · `ST_BLOCKED` · `ST_RANGE` · `ST_ERROR`.

---

## 6. UI — `Length` 단계 탭

`STEPS` 표에 줄 하나를 넣는다(그러라고 만든 자리다).

```
┌ Source ────────────────────────────────────┐   (기존 공용)
│ Mapping [v001 ▾]  Cage namespace [CAGE ▾]  │
└────────────────────────────────────────────┘
┌ Match │ Length ─────────────────────────────┐
│ Option controller : CAGE:OptionAll_xx_ctl   │  ← 찾은 결과를 그대로 보여 준다
│ Measured in cm      Total = straight ▾      │  ← 단위(4-5) · 방식(3-1)
│ ┌────────┬───────┬───────┬───────┬────────┐ │
│ │ Part   │ Total │ Upper │ Lower │ Status │ │
│ │ Arm_L  │ 62.31 │ 31.10 │ 31.24 │ ok     │ │
│ │ Arm_R  │ 62.28 │ 31.09 │ 31.22 │ ok     │ │
│ │ Leg_L  │ 88.04 │ 44.50 │ 43.60 │ ok  ⚠  │ │  ← 굽음 0.06 (3-1)
│ │ Leg_R  │ 88.02 │ 44.49 │ 43.59 │ ok     │ │
│ └────────┴───────┴───────┴───────┴────────┘ │
│ [ Measure ]                 [ Write Values ]│
└─────────────────────────────────────────────┘
```

- **`Measure`** — 재기만 한다. **씬 불변.** (Match 탭의 `Check` 와 같은 역할)
- **`Write Values`** — 옵션 컨트롤러에 쓴다. **undo 한 스텝.**
- `Total` 콤보는 **json 의 `total_mode` 를 초기값으로** 하고, 바꾸면 표가 즉시 다시 계산된다.
- `up + low` 와 직선 거리가 **0.5 % 넘게 벌어지면** 그 행에 표식과 함께
  `bent - straight 88.04 vs sum 88.10` 을 적는다.

UI 문자열은 전부 영어(전역 규칙 6장).

---

## 7. 리스크

| # | 리스크 | 대응 |
|---|---|---|
| 7-1 | **`Arm_r` 이 실제 이름이 아니면** 오른팔만 안 써진다 | 3-2 로 "실제 이름일 가능성이 높다" 까지는 좁혔다. 그래도 **실행 시점에 `objExists` 로 확인**하고, 없으면 그 행만 `attr missing` 으로 표시(4-4). **툴이 이름을 고쳐 주지는 않는다** |
| 7-2 | **직선 vs 합** 을 잘못 고르면 스트레치 기준이 틀어진다 | 기본값은 V01 과 동일(직선). **차이를 표에 드러내고** 사용자가 고른다(3-1 · 6장) |
| 7-3 | 씬 단위가 다르면 값이 100배 틀어진다 | 바꾸지 않고 **표시**한다(4-5). 값이 눈에 보이므로 미리보기에서 걸린다 |
| 7-4 | 옵션 컨트롤러를 **잘못 찾아** 남의 노드에 쓴다 | 여럿이면 **고르지 않고 멈춘다**(4-2) |
| 7-5 | 조인트를 안 놓고 눌러 **길이 0** 이 써진다 | 전부 0 이면 경고(4-6). 0 을 쓰는 것 자체는 막지 않는다(의도일 수 있다) |
| 7-6 | 레퍼런스 케이지에서 `setAttr` 이 reference edit 으로 남는다 | 정상 동작이고 A00060 v03.02 에서 이미 확인했다. **문서에 적어 둔다** |
| 7-7 | 스파인·손가락에는 측정이 없다 | V01 도 없다. json 에 항목을 더하면 붙는다(4-1) — **코드 수정 불필요** |

---

## 8. 열린 질문

| # | 질문 | 왜 물어야 하나 | 기본값 |
|---|---|---|---|
| **A** | **`Total` 은 직선인가 합인가?** | 굽은 팔에서 3.4 %까지 벌어진다. IK 스트레치 기준이면 보통 **합**이 맞다 | **직선**(V01 과 동일) |
| **B** | **`.Arm_r` 이 케이지의 실제 어트리뷰트 이름이 맞나?** | 맞다면 그대로 두고, 아니라면 json 한 글자만 고치면 된다 | 있는 그대로 `Arm_r` |
| ~~**C**~~ | ~~옵션 컨트롤러가 **하나뿐**인가?~~ | **해소(2026-08-28)** — 이름은 `CH_n_OptionAll_xx_ctl` 하나이고, 자동으로 못 정하는 경우를 위해 **`Get Selected` 수동 지정**을 넣었다(4-2) | 자동 3단계 + 수동 |
| **D** | 스파인·손가락 길이도 필요한가? | 필요하면 어트리뷰트 이름만 주시면 json 에 줄을 더한다 | 넣지 않는다 |
| **E** | **12개(1-1) 말고 더 써야 하는 어트리뷰트가 있나?** | 코드에는 12개뿐이다(모든 버전 확인). 케이지에 더 있다면 **코드에서 알아낼 수 없다** — 이름과 재는 구간을 주시면 json 에 줄을 더한다 | 12개 |

> **A · B 는 답을 몰라도 만들 수 있다.** A 는 UI 에서 바꿀 수 있게, B 는 실행 시점 확인으로
> 설계했다. **답을 기다리지 않고 진행하고, 답이 오면 json 만 고친다.**

---

## 9. 작업 순서

> **2026-08-28 — 1~6 단계 전부 완료 (v02.01).** 검증 **Length 92 + Match 88 = 180항목** 통과.

| 단계 | 내용 | 확인 | 상태 |
|---|---|---|---|
| 1 | `length_map.json` 작성 (4-1) + `mapping_data.load_length()` 와 **조인트 이름 검증** | **12개(1-1)가 하나도 안 빠지고 실리는가** — 로드 시 개수를 센다 · 없는 조인트 이름을 잡는가 | ✅ |
| 2 | `scene_utils.plug_writable` 공개화 + 기존 호출부 정리 | 88항목 회귀가 그대로 통과하는가 | ✅ |
| 3 | `length_manager.distance` / `chain_lengths` / `plan` | **씬 불변** · 굽은 체인에서 직선≠합이 표에 드러나는가 | ✅ |
| 4 | `length_manager.apply` + 사전 점검 5종 (4-4) | 없는 어트리뷰트·잠김·연결·범위 밖에서 **예외 없이 건너뛰고 계속** · undo 한 스텝 | ✅ |
| 5 | `Length` 탭 (6장) | 값 미리보기 → 쓰기 · 단위 표시 · Total 콤보 | ✅ |
| 6 | 문서 · CHANGELOG · WORKLOG · 메모리 | | ✅ |

---

## 10. 검증 계획 (mayapy headless)

> **2026-08-28 — 13항목 전부 구현했고 통과한다 (Length 92 · Match 88).**
> 더해서 `length_map.json` 에서 `_up`/`_low` 8개를 일부러 빼는 **변이 테스트**로
> **27항목이 실패하는 것**을 확인했다 — 검증이 누락을 실제로 잡는다.

Match 와 같은 방식으로 **케이지 `.ma` 를 만들어 임포트/레퍼런스 두 경로를 나란히** 돌린다.

| # | 무엇을 | 왜 |
|---|---|---|
| 1 | 곧은 체인에서 `all == up + low` | 기준선 |
| 2 | **30° 굽힌 체인에서 `all < up + low`** 이고 표에 표식이 뜨는가 | 3-1 이 실제로 드러나는가 |
| 3 | `total_mode="sum"` 이면 합이 써지는가 | 열린 질문 A 의 두 갈래 |
| 4 | **레퍼런스 케이지**에서 옵션 컨트롤러를 찾고 쓰는가(`CAGE:`) | 4-2 — Match 에서 물렸던 그 문제 |
| 5 | 임포트 케이지에서도 되는가 | 〃 |
| 6 | **12개가 전부 써지는가** — 그리고 그중 하나가 없어도 **나머지 11개**가 써지는가 | 1-1 · 3-2 · 4-4 (V01 은 여기서 멈췄다). `_up`/`_low` 8개가 빠지지 않았는지 **개수로** 센다 |
| 7 | **잠긴** / **연결된** 어트리뷰트를 건너뛰고 알리는가 | 3-4 |
| 8 | **`max` 가 걸린** 어트리뷰트에 범위 밖 값을 **안 쓰고** 알리는가 | 3-3 |
| 9 | 옵션 컨트롤러: 정확한 이름 · **네임스페이스를 넘는 토큰 검색** · **셰이프가 후보를 부풀리지 않는가** · 후보 둘이면 멈추는가 · **수동 지정이 이기는가** · `Get Selected` 가 셰이프를 트랜스폼으로 올리는가 | 4-2 · 7-4 |
| 10 | 조인트가 전부 원점이면 **경고**가 뜨는가 | 4-6 |
| 11 | 단위를 `m` 로 바꾸면 값이 1/100 이 되고 **라벨이 `m` 로 바뀌는가** | 3-5 · 4-5 |
| 12 | `Measure` 가 **씬을 안 바꾸는가** | 4-3 |
| 13 | 전체가 **undo 한 스텝**인가 | 4-3 |

---

## 11. 결정 로그

| 날짜 | 결정 | 이유 |
|---|---|---|
| 2026-08-28 | **재는 대상을 아바타 본 → 템플릿 조인트로** | 사용자 요청. 아바타 조인트 이름 의존이 사라지고 순서를 사람이 관리하지 않는다 |
| 2026-08-28 | **`length_map.json` 을 따로 둔다** | `template_map.json` 은 조인트→세트 표다. 모양이 다른 데이터를 섞지 않는다 |
| 2026-08-28 | **어트리뷰트 이름을 좌우 대칭으로 유도하지 않는다** | `Arm_L` ↔ **`Arm_r`** 로 규칙이 깨져 있다. 유도하면 한쪽이 조용히 틀린다 |
| 2026-08-28 | **`Total` 기본값은 V01 과 같은 직선 거리** | 30° 굽으면 합과 3.4 % 벌어진다(실측). 조용히 바꾸지 않고 **차이를 보여 주고 고르게** 한다 |
| 2026-08-28 | **범위를 넘으면 자르지 않고 거부** | 잘린 길이는 틀린 리그를 조용히 만든다. `min/max` 는 자르지 않고 예외를 낸다(실측) |
| 2026-08-28 | **옵션 컨트롤러 후보가 여럿이면 멈춘다** | 남의 노드에 조용히 쓰는 것이 최악. V01 은 `[0]` 을 골랐다 |
| 2026-08-28 | **본 계획서 5-1 의 "조용히 안 써진다" 를 정정** | 실측: `setAttr` 이 `RuntimeError` 를 내고 V01 은 그 자리를 **안 감쌌다** → Match 가 멈춘다. 따라서 `.Arm_r` 은 **실제 이름일 가능성이 높다** |
| 2026-08-28 | **어트리뷰트 12개를 1-1 에 낱개로 못박는다** | `_up`/`_low` 8개가 `total` 4개만큼 필수인데, 요약 표에서 줄여 적으면 **빠진 것처럼 읽힌다**(실제로 그렇게 읽혔다). 낱개 목록 + 개수 검증으로 못 빠지게 한다 |
| 2026-08-28 | **옵션 컨트롤러에 수동 지정(`Get Selected`)을 넣는다** | json 이름이 V01 의 **토큰**이었고(`OptionAll_xx_ctl` vs 실제 `CH_n_OptionAll_xx_ctl`), 게다가 `ls` 가 **네임스페이스를 안 넘고 셰이프까지 잡아** 자동 탐지가 두 겹으로 실패했다. 리그 이름 규칙은 프로젝트마다 다르므로 **자동은 편의, 수동이 보장**이다 |
