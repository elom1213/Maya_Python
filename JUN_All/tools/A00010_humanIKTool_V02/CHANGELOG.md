# Changelog — A00010_humanIKTool_V02

## v02.01 (2026-08-25)
**[Feature] `Mirror` 탭 신규 — 한쪽을 할당하면 반대쪽은 버튼 하나로.**

왼쪽 팔·다리를 슬롯에 다 붙인 뒤 오른쪽을 똑같이 한 번 더 찍던 작업을 없앤다.
**이미 할당된 슬롯을 읽어서** 반대쪽 슬롯에 대응 노드를 자동으로 붙인다.
조인트(캐릭터 정의)와 컨트롤러(Custom Rig 매핑) **둘 다** 같은 방식으로 동작한다.

| | |
|---|---|
| **Direction** | `Left -> Right` / `Right -> Left` |
| **Scope** | `All Sided Slots`(팔·다리·손가락·발가락·롤 전부) / `Arms & Legs` / `Selected Chain` |
| **Match By** | `Auto`(이름 → 실패분만 위치) / `Name only` / `Position only` |
| **Mirror Axis · Tolerance** | 위치 매칭용. `Name only` 에서는 비활성 |
| **Overwrite existing** | 끄면 이미 차 있는 슬롯은 건드리지 않고 `skip` 으로 보고 |
| **Copy mapping offsets** | Custom Rig 매핑의 offset 을 그대로 복사 |

- **`Preview Joints` / `Preview Controllers` 는 씬을 전혀 바꾸지 않는다.** 결과 표에
  `무엇을 → 어디에 → 어떤 근거로` 가 줄 단위로 나오고, 줄을 고르면 그 대상 노드가
  씬에서 선택된다. 확인한 뒤 `Mirror ...` 를 누른다.

**반대쪽 노드를 무엇으로 찾는가 — 이름을 1순위로 뒀다**

| 근거 | 채택 | 이유 |
|---|---|---|
| **이름의 방향 토큰** | **1순위** | `L_arm_JNT` → `R_arm_JNT`. **포즈에 의존하지 않고**, 좌우 비대칭 리그에서도 맞고, 결과를 사람이 로그만 보고 검수할 수 있다 |
| **월드 위치 미러** | 폴백 | 이름 규칙이 없는 리그를 구제한다. 단 **좌우 대칭 포즈일 때만 옳다** — 그래서 tolerance 안에 든 것만 채택하고 실제 거리를 같이 보고한다 |
| 계층 대칭 | 기각 | 부모가 먼저 풀려야 하는 순환 |
| 조인트 라벨(`.side`/`.type`) | 기각 | 세팅해 둔 리그가 드물고, HumanIK 이 **할당 뒤에** 써 주는 값이라 짝을 찾는 근거로는 늦다 |

이름 매칭은 단순 치환이 아니라 토큰 경계를 본다 — `L_arm` `arm_L` `arm01L` `LeftArm`
`myLeftArm` `arm_lf_ctrl` 은 잡고, `elbow` `clavicle` `Larm` `leftover` 는 잡지 않는다.
대소문자 꼴은 보존한다(`LEFT`→`RIGHT`, `Left`→`Right`). 네임스페이스와 DAG 패스는
건드리지 않고 마지막 이름만 뒤집는다.

**[Feature] Custom Rig(컨트롤러) 미러**

`CustomRigDefaultMappingNode` 의 `bodyPart` / `type`(0=T, 1=R) / `id` / `destinationRig` 를
읽어 반대쪽 이펙터에 `RetargeterAddMapping` 으로 매핑을 만든다.

- 대상 컨트롤러의 `translate` / `rotate` 가 **잠겨 있으면** HumanIK 이 `confirmDialog` 를
  띄워 배치가 모달에서 멈춘다 → 호출 전에 잠금을 직접 확인하고 그 줄만 `skip` 한다.
- 매핑을 추가할 때마다 리타게터를 끊었다 잇는 대신, **배치 전체를 한 번만** 끊고 마지막에
  다시 잇는다.

**[Fix] 할당 성공을 되읽어서 판정한다**

`setCharacterObject` 는 **캐릭터에 Control Rig 이 있으면 경고만 찍고 아무것도 하지 않는다**
(예외도 없다). 기존 `assign_joints` 는 이 경우에도 "assigned" 로 보고했다.

- `Assign` / `Mirror` 모두 실행 전에 `hikGetControlRig` 로 확인하고, 리그가 있으면
  무엇 때문에 막혔는지 밝히고 중단한다.
- 슬롯을 하나 붙일 때마다 `<character>.<슬롯이름>` 연결을 **되읽어** 성공을 판정한다.

**[Change] 상위 탭 2개 — `Assign` / `Mirror`**
HIK 캐릭터 노드 선택은 두 탭이 공유하므로 탭 밖 상단에 그대로 뒀다.
`Assign` 탭의 기능·이름·배치는 하나도 바뀌지 않았다. 창 기본 크기 `360x620` → `620x760`
(결과 표 5열이 들어간다).

**[Internal] 새 모듈 3개**

| 파일 | 역할 |
|---|---|
| `app/core/hik_nodes.py` | HumanIK 슬롯 ID ↔ 이름 테이블, 좌/우 슬롯 짝짓기, 캐릭터 정의 읽기 |
| `app/core/mirror_resolver.py` | "한쪽 노드 → 반대쪽 노드". 조인트와 컨트롤러가 공유 |
| `app/core/custom_rig_manager.py` | Custom Rig 리타게터 읽기 / 매핑 미러 |

슬롯 이름은 `GetHIKNodeName(id)`(mayaHIK 플러그인) 을 런타임 조회하고, 실패할 때 쓰는
Maya 2024 실측 폴백 테이블(0~211)을 함께 둔다. 테스트가 둘의 일치를 검사한다.

**검증** — mayapy(Maya 2024) 헤드리스로 **core 111항목 + UI 스모크 49항목**.
이름 토큰 13종과 오탐 6종, 슬롯 테이블/폴백 일치, Preview 무변경, 이름·위치·Auto 3모드,
재실행 멱등, Overwrite on/off, Scope 3종, 방향 뒤집기, 포즈 틀어진 리그의 실패 보고,
Custom Rig 미러·오프셋 복사·잠긴 컨트롤러 skip.

---

## v02.00 (2026-06-17)
**[Change] 레거시 `A00010_humanIKTool`(maya.cmds UI)을 PySide(아키텍처 B)로 마이그레이션.**
`JUN_get_HIK_node` / `JUN_assign_joints` 를 UI 비의존 정적 메서드(`HIKManager`)로 옮기며
다음을 고쳤다.

- HIK 노드 0개 / 미선택, 조인트 리스트가 비었을 때의 `IndexError` 가드
- 조인트 수와 슬롯 수가 다를 때 조용히 잘리던 `zip` → mismatch 를 명시 경고
- 실패해도 무조건 "succeeded" 를 찍던 문제 → 성공/실패 카운트로 보고
- `cmds.ls(fl=True)` 전체 노드 순회 → `cmds.ls(type="HIKCharacterNode")` 직접 조회
