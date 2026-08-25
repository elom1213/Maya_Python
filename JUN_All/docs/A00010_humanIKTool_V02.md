---
title: A00010_humanIKTool_V02 사용법
aliases: [HumanIK Tool, HumanIKTool, A00010, Mirror Assign, Custom Rig Mirror]
tags: [maya-python, tool-guide, humanik, hik, characterization, retarget, mirror]
updated: 2026-08-25
---

# A00010_humanIKTool_V02 사용법

HumanIK **캐릭터라이제이션**(어느 조인트가 어느 슬롯인지 정의하는 일)을 리스트 하나로
빠르게 끝내는 in-Maya PySide 툴이다. v02.01 부터 **한쪽을 정의하면 반대쪽은 버튼 하나로**
끝나는 `Mirror` 탭이 있고, 조인트뿐 아니라 **Custom Rig 의 컨트롤러 매핑**도 같은 방식으로
미러한다.

- 버전: `v02.01` (`app/config/version.py`)
- 위치: `JUN_All/tools/A00010_humanIKTool_V02`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00010_V02.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`HumanIKTool`**
버튼 설치. 아이콘은 툴 폴더의 `icon/A00010_humanIKTool_V02.png`(32×32).

### 코드로 실행
```python
import tools.A00010_humanIKTool_V02 as A00010_humanIKTool_V02
A00010_humanIKTool_V02.run(True)     # True 면 DEV_MODE 에서 리로드
```

---

## 2. 화면 구성

```
HumanIK Character Node      <- Assign / Mirror 두 탭이 공유한다
 ├ Get HIK Nodes
 └ (씬의 HIKCharacterNode 목록, 단일 선택)

[ Assign ]  [ Mirror ]
```

**`Get HIK Nodes` 로 캐릭터 노드를 하나 고르는 것이 모든 작업의 전제**다. 고르지 않으면
어느 버튼도 동작하지 않고 그 사실을 로그에 찍는다.

---

## 3. `Assign` 탭 — 체인 단위 수동 할당

1. `Joints (order = slot order)` 리스트에 조인트를 담는다. **리스트 순서가 슬롯 순서**이므로
   `Up` / `Down` 으로 맞춘다.
2. `Bone Chain` 에서 체인을 고른다.
3. `Assign Joints`.

| 체인 | 슬롯 순서 |
|---|---|
| `Spine` | Hips · Spine · Spine1 … Spine6 |
| `Shoulder to hand : Left` / `: Right` | Shoulder · Arm · ForeArm · Hand |
| `Fingers : Left` / `: Right` | Thumb1~3 · Index1~3 · Middle1~3 · Ring1~3 · Pinky1~3 |
| `Neck 1 to head` / `Neck 2 to head` | Neck (· Neck1) · Head |
| `Leg : Left` / `: Right` | UpLeg · Leg · Foot · ToeBase |

조인트 수와 슬롯 수가 다르면 **짧은 쪽까지만** 붙이고 그 사실을 경고로 남긴다.

> [!warning] Control Rig 이 있으면 정의를 못 고친다
> HumanIK 은 캐릭터에 Control Rig 이 붙어 있으면 정의 변경을 **거부한다** — 그런데
> `setCharacterObject` 는 예외를 던지지 않고 조용히 아무것도 안 한다. 툴은 실행 전에
> `hikGetControlRig` 로 확인해 막고, 슬롯을 붙일 때마다 연결을 **되읽어** 성공을 판정한다.
> (v02.00 까지는 이 경우에도 "assigned" 로 보고했다.)

---

## 4. `Mirror` 탭 — 반대쪽 자동 할당

왼쪽 팔·다리를 다 붙였으면 오른쪽은 여기서 한 번에 끝낸다.
**이미 할당된 슬롯을 읽는 것**이 입력이므로, 미리 리스트를 만들 필요가 없다.

### 4-1. 순서

1. `Direction` 을 고른다 — 이미 할당해 둔 쪽이 소스다.
2. `Scope` 로 범위를 정한다.
3. **`Preview Joints` 를 먼저 누른다.** 씬은 전혀 바뀌지 않고 결과 표만 채워진다.
4. 표를 확인한다. 줄을 고르면 그 **대상 노드가 씬에서 선택**되므로 눈으로 확인할 수 있다.
5. 문제가 없으면 `Mirror Joints`.

### 4-2. 옵션

| 항목 | 뜻 |
|---|---|
| `Direction` | `Left -> Right` / `Right -> Left` |
| `Scope` → `All Sided Slots` | 방향이 있는 슬롯 **전부** — 팔·다리·손가락·발가락·롤. 기본값 |
| `Scope` → `Arms & Legs` | Shoulder~Hand 와 Leg 체인만 |
| `Scope` → `Selected Chain` | **`Assign` 탭에서 고른 체인**만 |
| `Match By` | 반대쪽 노드를 찾는 근거 (5장) |
| `Mirror Axis` · `Tolerance` | 위치 매칭용. `Name only` 에서는 비활성화된다 |
| `Overwrite existing` | 끄면(기본) 이미 차 있는 슬롯은 건드리지 않고 `skip` 으로 보고 |
| `Copy mapping offsets` | Custom Rig 전용 (6장) |

### 4-3. 결과 표

| 열 | 내용 |
|---|---|
| `HIK Slot` | 소스 슬롯 이름 (컨트롤러는 `LeftHand (Translation)` 처럼 타입까지) |
| `Source` | 그 슬롯에 붙어 있는 노드 |
| `Target` | 찾아낸 반대쪽 노드 |
| `Status` | `ready`(Preview) · `ok` · `skip` · `fail` |
| `Detail` | 무슨 근거로 찾았는지 / 왜 못 찾았는지 |

- `ok` / `ready` 초록·파랑, `skip` 노랑, `fail` 빨강.
- **`Detail` 이 `position (d=...)` 인 줄만 골라 검수하면 된다** — 이름으로 풀린 줄은
  이름만 봐도 맞는지 알 수 있다.

두 번 눌러도 안전하다. 이미 같은 노드가 붙어 있으면 `skip / already assigned` 로 넘어간다.

---

## 5. 반대쪽 노드를 무엇으로 찾는가

이 툴에서 판단이 갈리는 유일한 지점이라 근거를 적어 둔다.

| 근거 | 채택 | 이유 |
|---|---|---|
| **이름의 방향 토큰** | **1순위** | **포즈에 의존하지 않는다.** 애님이 들어가 있든 T 포즈가 아니든 결과가 같다. 좌우 비대칭 리그에서도 맞고, 결과를 이름만 보고 검수할 수 있다 |
| **월드 위치 미러** | 폴백 | 이름 규칙이 전혀 없는 리그를 구제한다. 다만 **좌우 대칭 포즈일 때만 옳다** |
| 계층 대칭 | 기각 | 부모가 먼저 풀려야 짝을 알 수 있는 순환이다 |
| 조인트 라벨 `.side`/`.type` | 기각 | 세팅해 둔 리그가 드물고, HumanIK 이 **할당한 뒤에** 써 주는 값이라 짝을 찾는 근거로는 늦다 |

### 5-1. `Name only` — 이름 토큰 뒤집기

단순 문자열 치환이 아니라 **토큰 경계**를 본다.

| 잡는다 | 안 잡는다 |
|---|---|
| `L_arm_JNT` → `R_arm_JNT` | `elbow` (l 이 단어 안) |
| `arm_L` → `arm_R` | `clavicle` |
| `arm01L` → `arm01R` | `Larm` (뒤에 소문자가 이어짐) |
| `LeftArm` · `myLeftArmCtrl` | `leftover_grp` |
| `arm_lf_ctrl` → `arm_rt_ctrl` | `ARMLeft` |
| `L_arm_L_end` → `R_arm_R_end` (전부) | |

- 인식하는 쌍: `left/right`, `lft/rgt`, `lt/rt`, `lf/rt`, `l/r`.
  `rt` 처럼 두 쌍에 걸치는 토큰은 후보를 여러 개 만들어 **실제로 존재하는 첫 후보**를 쓴다.
- 대소문자 꼴을 보존한다 — `LEFT`→`RIGHT`, `Left`→`Right`, `l`→`r`.
- **네임스페이스와 DAG 패스는 건드리지 않는다.** `ns:L_hand_CTRL` → `ns:R_hand_CTRL`.
- 같은 이름의 노드가 여럿이면 **먼저 같은 부모 아래**를 보고, 그다음 소스와 같은 계층
  루트 아래를 본다. 그래도 못 좁히면 `ambiguous name` 으로 보고하고 건드리지 않는다.

### 5-2. `Position only` — 위치 미러

`Mirror Axis`(기본 `X`) 기준으로 월드 좌표를 뒤집고 가장 가까운 후보를 고른다.

- 후보는 **소스와 같은 계층 루트 아래**로 좁힌다 — 레퍼런스가 여러 개 걸린 씬에서 옆
  캐릭터의 조인트를 집는 사고를 막는다. 조인트 미러는 `joint` 타입만, 컨트롤러 미러는
  모든 트랜스폼을 후보로 본다.
- **`Tolerance` 밖이면 채택하지 않고 실제 거리를 적어 `fail` 로 보고한다.**
  포즈가 들어간 리그에서 조용히 엉뚱한 조인트를 집는 것이 이 방식의 유일한 위험이라,
  추측하는 대신 실패시키는 쪽을 골랐다.

> [!tip] 위치로 미러할 거면 먼저 스탠스 포즈로
> `Skeleton > HumanIK > (Stance Pose)` 로 돌려놓고 하면 tolerance 를 아주 작게(예: `0.001`)
> 줄 수 있다. 값이 클수록 잘못 집을 여지가 커진다.

### 5-3. `Auto` (기본값)

이름을 먼저 시도하고, **이름으로 못 푼 항목만** 위치로 넘긴다. 섞인 리그(대부분 이름은
있는데 몇 개만 규칙에서 벗어난 경우)에 맞다. 각 줄의 `Detail` 이 어느 쪽으로 풀렸는지
말해 준다.

---

## 6. 컨트롤러 미러 (Custom Rig)

`Preview Controllers` / `Mirror Controllers` 는 **HumanIK Custom Rig 의 컨트롤러 매핑**을
같은 방식으로 미러한다. 조인트 정의가 "조인트 → 슬롯" 이라면 Custom Rig 은
"내 리그의 컨트롤러 → 이펙터" 다.

### 6-1. 전제

**Custom Rig 자체는 이 툴이 만들지 않는다.** HumanIK 창에서
`Custom Rig` 탭 → `Create Custom Rig` 로 만들고, **한쪽 컨트롤러를 먼저 매핑해 둔 상태**여야
한다. 없으면 그 사실을 로그로 알린다.

### 6-2. 동작

`CustomRigDefaultMappingNode` 를 읽어 반대쪽 이펙터에 매핑을 만든다.

| 어트리뷰트 | 뜻 |
|---|---|
| `.bodyPart` | `LeftHand` — HumanIK 슬롯 이름과 같다 |
| `.type` | `0` = Translation, `1` = Rotation (한 이펙터가 둘을 따로 갖는다) |
| `.id` | 슬롯 ID |
| `.destinationRig` | 매핑된 컨트롤러 |
| `.offsetX/Y/Z` | HIK UI 에서 잡은 오프셋 |

- **T 와 R 매핑은 각각 한 줄**로 처리된다. 표에 `LeftHand (Translation)` / `(Rotation)` 이
  따로 나온다.
- `Copy mapping offsets` 를 켜면 소스 매핑의 offset 을 **그대로** 복사한다.
  **부호를 뒤집지는 않는다** — 좌우 컨트롤러의 방향 규약이 다른 리그라면 복사를 끄고
  HIK 창에서 직접 잡는 편이 낫다.

### 6-3. 잠긴 컨트롤러

HumanIK 은 대상 컨트롤러의 `translate` / `rotate` 가 잠겨 있으면 **`confirmDialog` 를 띄운다**
— 배치 처리 한가운데서 모달이 뜨면 작업이 멈춘다. 그래서 호출 전에 잠금을 직접 확인하고,
잠긴 채널은 그 줄만 `skip / has locked ... channels` 로 넘긴다.

> [!warning] undo
> 조인트 미러는 한 번의 `Ctrl+Z` 로 되돌아간다(검증함). **Custom Rig 매핑은 HumanIK 이
> 자체 파이썬 경로로 노드를 만들기 때문에 undo 가 깔끔하지 않을 수 있다** — 그래서
> `Preview Controllers` 가 있다. 먼저 보고 나서 실행할 것.

---

## 7. 코드 구조

```
app/
├── config/version.py
├── core/
│   ├── hik_nodes.py           # 슬롯 ID <-> 이름 테이블, 좌/우 짝짓기, 정의 읽기
│   ├── mirror_resolver.py     # "한쪽 노드 -> 반대쪽 노드" (조인트/컨트롤러 공용)
│   ├── hik_manager.py         # 체인 할당 + 조인트 미러
│   └── custom_rig_manager.py  # 리타게터 읽기 + 컨트롤러 매핑 미러
└── ui/main_window.py          # 탭 2개 (Assign / Mirror)
```

### 7-1. 슬롯 테이블

슬롯 이름은 mayaHIK 플러그인의 MEL 전역 프로시저 **`GetHIKNodeName(id)`** 가 권위다.
`HIKNodes` 가 최초 접근 때 `hikGetNodeCount()` 만큼 한 번 조회해 캐시한다.
Maya 2024 기준 **212개**(`0~171` 정의 슬롯, `172~211` Leaf roll).

플러그인 조회가 실패할 때를 대비해 실측값 폴백 테이블을 같은 파일에 둔다.
**테스트가 폴백과 런타임 조회의 일치를 검사하므로**, 마야 버전을 올린 뒤 테이블이 낡으면
테스트가 먼저 잡는다.

슬롯 ID 는 캐릭터 노드의 어트리뷰트 이름이기도 하다 — `TestChar.LeftArm` 에 조인트의
`.Character` 메시지가 연결된다. 지금 무엇이 붙어 있는지는 이 플러그를 `listConnections`
하면 된다.

### 7-2. 좌/우 슬롯 짝

체인 정의(`BONE_CHAINS`)에 좌우 쌍을 따로 적지 않는다. **슬롯 이름의 `Left`/`Right`
접두사를 뒤집고 역인덱스로 ID 를 찾는다.** 그래서 `BONE_CHAINS` 에 없는 슬롯(손가락 4번째
마디, InHand, Roll, Leaf roll 등)까지 자동으로 따라온다.

---

## 8. 참고 — HumanIK MEL 인터페이스

이 툴이 기대는 외부 프로시저. Maya 2024 `scripts/others/` 에서 확인.

| 호출 | 파일 | 용도 |
|---|---|---|
| `setCharacterObject(node, char, slotId, 0)` | `hikDefinitionUtils.mel` | 슬롯 할당 |
| `GetHIKNodeName(id)` · `hikGetNodeCount()` | mayaHIK 플러그인 | 슬롯 테이블 |
| `hikGetControlRig(char)` | mayaHIK 플러그인 | Control Rig 존재 확인 |
| `RetargeterAddMapping / DeleteMapping / Connect / Disconnect` | `retargeter.mel` | Custom Rig 매핑 |
| `hikUpdateDefinitionUI` · `hikUpdateCustomRigUI` | `hik*UI.mel` | HIK 창 갱신(`catchQuiet` 로 감쌈) |
