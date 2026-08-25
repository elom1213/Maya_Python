---
name: wip-a00010-hik-mirror
description: A00010_humanIKTool_V02 Mirror 탭 — 한쪽 슬롯을 읽어 반대쪽 자동 할당(조인트 + Custom Rig 컨트롤러), 근거는 이름 1순위·위치 폴백
metadata:
  type: project
---

`A00010_humanIKTool_V02` **v02.01 `Mirror` 탭** (2026-08-25). 왼쪽 팔·다리를 Assign 한 뒤
오른쪽을 버튼 하나로. **조인트(캐릭터 정의)와 컨트롤러(Custom Rig 매핑) 둘 다.**

**입력은 리스트가 아니라 "이미 할당된 슬롯"** — 캐릭터 노드의 슬롯 플러그
(`<char>.LeftArm`)에 조인트 `.Character` 메시지가 연결되므로 `listConnections` 로 읽는다.
플러그는 할당 여부와 무관하게 **항상 존재**한다.

**슬롯 ID ↔ 이름** — mayaHIK 플러그인의 MEL `GetHIKNodeName(id)` 가 권위,
`hikGetNodeCount()` = **212** (Maya 2024). `0~171` 정의 슬롯, `172~211` Leaf roll(커스텀 리그 전용).
좌우 짝은 **체인 정의에 적지 않고** 이름 접두사 `Left`/`Right` 를 뒤집어 역인덱스로 찾는다
→ `BONE_CHAINS` 에 없는 슬롯(손가락 4마디·InHand·Roll·Leaf)까지 자동으로 따라온다.
`app/core/hik_nodes.py` 에 실측 폴백 테이블이 있고 **테스트가 런타임 조회와의 일치를 검사**한다.

**반대쪽 노드를 무엇으로 찾는가 — 이름이 1순위** (`app/core/mirror_resolver.py`, 조인트/컨트롤러 공용)
- 이름 방향 토큰: **포즈 비의존**(애님 들어간 리그에서도 맞음), 좌우 비대칭 리그에서도 성립,
  결과를 이름만 보고 검수 가능.
- 위치 미러는 폴백 — **대칭 포즈일 때만 옳다.** tolerance 밖이면 추측하지 않고 **거리를 적어 fail**.
- 계층 대칭은 순환이라 기각. 조인트 라벨 `.side`/`.type` 은 HumanIK 이 **할당 뒤에** 써 주는 값이라 기각.
- 토큰 매칭은 치환이 아니라 **경계 판정** + **blocker**(그 자리에서 더 긴 토큰이 시작하면 무시).
  blocker 없으면 `LEFT_arm` 이 `l/r` 쌍에도 걸려 `REFT_arm` 헛 후보가 나온다.

**실측으로 확인한 HumanIK 거동 (추측하면 틀린다)**
- `setCharacterObject` 는 캐릭터에 **Control Rig 이 있으면 경고만 찍고 아무것도 안 하며 예외도
  안 던진다** → 성공 판정은 **연결 되읽기**로. `hikGetControlRig(char)` 로 미리 막는다.
- `InputCharacterizationLock` 은 **API 레벨에서 할당을 막지 않는다**(UI 전용 가드) → 가드 불필요.
- `setCharacterObject` 는 undo 된다. **Custom Rig 매핑 생성은 파이썬 경로(`maya.app.hik.retargeter`)
  라 undo 가 깔끔하지 않을 수 있다** → Preview 가 안전망.
- `RetargeterAddMapping` 은 대상 컨트롤러의 translate/rotate 가 **잠겨 있으면 confirmDialog** 를
  띄워 배치가 모달에서 멈춘다 → 호출 전에 잠금을 직접 검사해 그 줄만 skip.
- 매핑 노드 `CustomRigDefaultMappingNode`: `.bodyPart`(슬롯 이름) `.type`(0=T,1=R) `.id`(슬롯 ID)
  `.destinationRig`(message→컨트롤러) `.offsetX/Y/Z`. T/R 은 **별개의 매핑 노드** 다.
- Custom Rig 자체는 이 툴이 만들지 않는다 — HIK 창에서 만들어 둔 리타게터를 읽어 쓴다.

관련: [[mayapy-headless-verify]] · [[undo-chunk-by-default]] · [[push-includes-tool-guide-docs]]
