---
title: A00460_ControllerTool 사용법
aliases: [Controller Tool, ControllerTool, A00460, FK Control]
tags: [maya-python, tool-guide, controller, fk, rigging, constraint, zro, con, ctl, tgt]
updated: 2026-08-21
---

# A00460_ControllerTool 사용법

Maya 안에서 도는 **애니메이션 컨트롤러 생성** PySide 툴이다(arch B, in-Maya).
키프레임 애니메이션용 컨트롤러를 **제작자 편의에 맞춰** 만들어 주는 것이 목적이고,
v01.00 의 첫 기능은 **FK** 다.

탭은 상위 = 카테고리, 하위 = 기능 두 단계다 (`A00110_animTool_V02` · `A00400_CurveTool` 과 같은 규칙).

| 상위 탭 | 하위 탭 | 내용 |
|---------|---------|------|
| **Create** | **FK** (v01.00~) | 리스트업한 조인트/오브젝트에 `zro > con > ctl > tgt` 계층을 만들고, 조인트가 그 계층을 따라오게 컨스트레인트 |

- **버전**: `app/config/version.py` (v01.02)
- **설치**: `__dragDrop_A00460.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **CtrlTool** → `tools.A00460_ControllerTool.run(True)`
- **참고**: `con/ctl/tgt` 계층 관례는 `A00170_driverTool` 의 Edge Loop 드라이버,
  Bone Chain / Bone Root 모드는 `A00390_WindTool_V02` 를 이식/응용.

---

## 1. 만들어지는 계층

조인트 하나마다 아래 스택이 생기고, 스택끼리 계층으로 이어진다.

```
<joint>_zro          zero-out 널 — 조인트 자리(위치 + 회전)
└── <joint>_con      오프셋 널
    └── <joint>_ctl  ★ 애니메이터가 잡는 커브 컨트롤러
        └── <joint>_tgt   조인트를 컨스트레인트하는 널
            └── <child>_zro ...   자식 조인트의 스택이 여기에 붙는다
```

`joint_A_01 > joint_A_02 > joint_A_03` 체인 하나를 **Bone Root** 로 돌리면 이렇게 나온다.

```
joint_A_01_zro
  joint_A_01_con
    joint_A_01_ctl
      joint_A_01_tgt
        joint_A_02_zro
          joint_A_02_con
            joint_A_02_ctl
              joint_A_02_tgt
                joint_A_03_zro
                  joint_A_03_con
                    joint_A_03_ctl
                      joint_A_03_tgt
```

- **`_ctl` 만 커브**(정육면체 테두리 nurbsCurve)이고 나머지 셋은 **셰이프 없는 널 그룹**이다.
- 조인트는 **스택의 마지막 노드**를 따라간다. 기본 구성에서는 `_tgt` 다.
- **스택 최상단만** `matchTransform` 으로 조인트 자리(위치 + 회전)에 맞추고
  나머지는 **로컬 0** 으로 부모 밑에 넣는다. 그래서 넷이 정확히 겹치고,
  **컨트롤러를 움직인 값이 곧 조인트 대비 오프셋**이 된다.
- 스케일은 맞추지 않는다 — 컨트롤러 크기는 `Control Size` 가 정한다.

---

## 2. 화면 구성

```
┌ Controller Tool ────────────────────┐
│ Help                                │
│ [ Create ]                          │  ← 상위 탭 (카테고리)
│ [ FK ]                              │  ← 하위 탭 (기능)
│ [ List Selected ]                   │
│ Joints / Objects      Number: N     │
│ ┌─────────────────────────────────┐ │
│ │ joint_A_01                      │ │   TSL: Add / Del / Up / Down / Reverse
│ │ joint_B_01                      │ │
│ └─────────────────────────────────┘ │
│ ┌ Mode ───────────────────────────┐ │
│ │ (o) Bone Root  ( ) Bone Chain   │ │
│ └─────────────────────────────────┘ │
│ ┌ Nodes to Build ─────────────────┐ │
│ │ [v] zro  [v] con  [v] tgt       │ │
│ │ ctl (cube control curve) is a.. │ │
│ │ Control Size [1.000]            │ │
│ └─────────────────────────────────┘ │
│ ┌ Constraint ─────────────────────┐ │
│ │ [v]Parent [ ]Point [ ]Orient    │ │
│ │ [ ]Scale                        │ │
│ └─────────────────────────────────┘ │
│ [      Create FK Controls        ]  │
│ [ log ... ]                         │
└─────────────────────────────────────┘
```

---

## 3. 옵션

### Mode — 리스트를 어떻게 읽을 것인가

| 모드 | 뜻 |
|------|-----|
| **Bone Root** (기본) | 리스트의 **각 항목이 체인의 루트**. 그 노드와 **씬 계층상 모든 자손**까지 따라 내려가며 스택을 만든다 |
| **Bone Chain** | 리스트업한 노드들이 **하나의 체인**. 씬 계층과 무관하게 **리스트 순서**로 잇는다(Up/Down 으로 순서 조정) |

`joint_A_01`, `joint_B_01` 두 루트를 담고 **Bone Root** 로 돌리면 **독립된 계층 2개**가 나온다.
같은 리스트를 **Bone Chain** 으로 돌리면 `joint_A_01_tgt` 밑에 `joint_B_01_zro` 가 붙는 **하나의 계층**이 나온다.

> **분기 처리**: Bone Root 에서 자식이 여럿이면 갈래마다 스택이 갈라진다.
> `root_jnt_tgt` 밑에 `armL_jnt_zro` 와 `armR_jnt_zro` 가 나란히 붙는 식이다.

> **어디까지 내려가나**: 루트가 **조인트면 조인트 자식만** 따라간다 —
> 조인트에 붙은 지오메트리나 이미 만들어 둔 컨트롤러가 끌려 들어오는 것을 막기 위해서다.
> 루트가 조인트가 아니면 트랜스폼 자식을 따라간다.

### Nodes to Build — 만들 널 그룹

`zro` / `con` / `tgt` 체크박스. **기본은 셋 다 켜짐.**
끄면 스택에서 빠지고 위아래가 **직접 이어진다.**

- **`_ctl` 은 체크박스가 없다** — 이 툴의 존재 이유라 항상 만든다.
- ⭐ **`tgt` 를 끄면 `_ctl` 이 대신 조인트를 컨스트레인트한다.**
  컨스트레인트 드라이버는 언제나 **스택의 마지막 노드**이기 때문이다.

`zro` 만 켠 결과:

```
joint_A_01_zro
  joint_A_01_ctl          ← 이 노드가 joint_A_01 을 컨스트레인트
    joint_A_02_zro
      joint_A_02_ctl
```

| 항목 | 뜻 |
|------|-----|
| **Control Size** | 큐브 **반변길이**(반지름 감각). `1.0` 이면 조인트에서 사방 1유닛까지 뻗는 큐브 |

> **컨트롤러 모양은 정육면체 테두리 고정**이다(v01.02~). `A00145_RigConnect` 의 Match 탭이 쓰는
> cube 컨트롤과 **같은 CV 데이터**(degree 1, CV 17개로 12모서리를 한 붓에 그린다).
> 큐브는 90° 회전 대칭이라 축을 골라도 결과가 같으므로 **Shape Axis 옵션은 없다.**

### Constraint — 조인트가 무엇을 따라가나

| 체크박스 | 명령 | 잡는 채널 |
|---|---|---|
| **Parent** (기본) | `parentConstraint` | translate + rotate |
| **Point** | `pointConstraint` | translate |
| **Orient** | `orientConstraint` | rotate |
| **Scale** | `scaleConstraint` | scale |

여러 개를 동시에 켤 수 있고, 전부 `maintainOffset=True` 로 건다.

> ⚠️ **Parent 와 Point/Orient 를 같이 켜지 말 것.** 같은 채널을 두 컨스트레인트가 다투게 된다.
> 툴이 막지는 않지만 로그에 경고를 남기고, 마야도 두 번째 컨스트레인트를
> `Object is already connected` 로 거부한다.
> **Parent 하나**, 또는 **Point + Orient** 중 하나를 고르는 게 정석이다.
>
> 쓸모 있는 조합은 **Parent + Scale** 이다. `parentConstraint` 는 스케일을 잡지 않는다.

> 체크박스를 하나도 안 켜면 컨트롤러만 만들고 조인트는 따라오지 않는다(로그에 경고).

---

## 4. 사용법

1. 씬에서 체인의 **루트 조인트**들을 고르고 **List Selected**
2. **Mode** 선택 — 보통 **Bone Root**
3. **Nodes to Build** 에서 필요한 널만 남기고, **Control Size** 를 조인트 크기에 맞춘다
4. **Constraint** 선택 — 보통 **Parent**(필요하면 + Scale)
5. **Create FK Controls**

결과로 만들어진 **루트 계층들이 선택된 상태**로 남는다. 그대로 리그 그룹으로 옮기면 된다.
전체가 **undo 한 스텝**이라 마음에 안 들면 `Ctrl+Z` 한 번으로 되돌아간다.

> 마지막 `select` 까지 **undo chunk 안에서** 한다. 밖에서 하면 select 가 별도 undo 스텝이 되어
> `Ctrl+Z` 를 한 번 눌렀을 때 **선택만 되돌아가고 컨트롤러는 남는다**(v01.01 에서 고침).

---

## 5. 알아둘 것 (mayapy 로 확인)

- **컨트롤러를 회전하면 그 아래 조인트가 전부 따라온다.** 스택이 조인트 계층을 그대로 복제하므로
  FK 답게 부모 회전이 자식으로 전파된다.
- **이름이 겹치면 마야가 뒤에 번호를 붙인다.** 조용히 넘어가면 어떤 노드가 어떤 조인트 것인지
  헷갈리므로, 툴이 `Name 'x_zro' was taken - Maya used 'x_zro1'.` 로 로그에 알려 준다.
- **같은 조인트를 두 번 처리하지 않는다.** Bone Root 에서 루트 여러 개가 겹쳐 잡혀도
  이미 처리한 조인트는 건너뛴다.
- 씬에 없는 이름은 `missing` 으로 보고하고 건너뛴다.

---

## 6. 구조

```
tools/A00460_ControllerTool/
├── launch.py / __init__.py / __dragDrop_A00460.py
├── icon/A00460_ControllerTool.svg (+ .png)   # 셸프 아이콘(본 체인 + FK 컨트롤 링)
└── app/
    ├── config/version.py
    ├── core/fk_manager.py   # 계층 생성 + 컨스트레인트 (maya.cmds, UI 비의존)
    └── ui/main_window.py    # PySide UI (카테고리 상위 탭 + 기능 하위 탭 + 로그)
```

**핵심 API** — `fk_manager`

```python
build_fk_controls(nodes, mode=MODE_ROOT,
                  use_zro=True, use_con=True, use_tgt=True,
                  constraints=(CON_PARENT,),
                  size=1.0)
```

반환 dict:

| 키 | 내용 |
|---|---|
| `roots` | 계층 최상단 노드들 |
| `controls` | 만들어진 `_ctl` 목록 |
| `constraints` | 만들어진 컨스트레인트 노드 |
| `driven` | 컨스트레인트가 걸린 조인트 |
| `missing` | 씬에 없던 입력 |
| `renamed` | 이름이 겹쳐 번호가 붙은 `(원한 이름, 실제 이름)` |
| `warnings` | 경고 문자열 |

내부 흐름:

- `_stack_plan(use_zro, use_con, use_tgt)` — 만들 노드의 `(종류, 접미사)` 순서 목록. `_ctl` 은 항상 포함
- `_create_stack(...)` — 스택을 만들고 `(최상단, 최하단, ctl)` 반환. **최상단만 matchTransform**
- `_build_root_recursive(...)` — Bone Root 모드의 재귀 하강(분기 대응)
- `_apply_constraints(driver, driven, types, result)` — `driver` = **스택의 최하단 노드**

**탭 구조** — `MainWindow.CATEGORIES` / `CREATE_PAGES` 표 한 곳이 분류를 정한다.
하위가 `FK` 하나뿐이지만 하위 탭 바를 그대로 둔다 — 기능 이름이 화면에 남고,
IK / Space Switch 같은 기능이 늘어도 구조가 그대로다.

---

## 7. 앞으로

이 툴의 목적은 "컨트롤러를 제작자 편의에 맞춰 생성"하는 것이라, FK 는 시작점이다.
`Create` 카테고리에 하위 탭을 추가하는 형태로 늘린다 — 표만 고치면 된다.
