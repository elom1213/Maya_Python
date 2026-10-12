---
name: compound-connect-leaves-child-connections
description: "Maya 컴파운드(double3) 연결 함정 — listConnections(node.translate) 는 자식(translateX) 연결을 안 돌려주고, 컴파운드를 force 로 이어도 기존 자식 연결이 남아 두 소스가 다툰다. 축별로 조회·끊기"
metadata:
  node_type: memory
  type: reference
  originSessionId: 13b1c87d-a7c0-4b67-8313-56faa8672f5e
  modified: 2026-10-12T00:26:28.296Z
---

mayapy 2024 실측 (2026-10-12, A00170 Seal Free 모드 작업 중):

- `cmds.listConnections("n.translate", s=True, plugs=True)` 는 **컴파운드에 직접 들어온 연결만** 준다.
  컨스트레인트(`constraintTranslateX -> translateX`) 와 키(animCurve) 는 **자식 플러그에만** 연결되므로 `None`.
  반대로 컴파운드가 연결돼 있으면 자식 조회(`n.translateX`) 가 `None` 이다 — "구동되는가" 는 둘 다 봐야 안다.
- `cmds.connectAttr(src, "n.translate", f=True)` 는 자식에 걸린 기존 연결을 **끊지 않는다**. 연결은 성공하고
  `translateX` 에는 컨스트레인트가, `translate` 에는 새 소스가 **동시에** 남는다. 컴파운드로 덮기 전에 자식을
  `disconnectAttr` 로 먼저 끊어야 한다.
- pairBlend 자식 이름은 `inTranslateX1` / `inRotateX1` (`inTranslate1X` 아님).
- `inverseMatrix` 는 matrixNodes **플러그인** 노드라 standalone 에서 `unknown` 이 된다. `decomposeMatrix` /
  `composeMatrix` / `multMatrix` 는 코어. 회전 역행렬은 **각을 음수로 + 회전 순서를 뒤집은(xyz→zyx=5) composeMatrix** 로.
- 노드의 커스텀 어트리뷰트(`n.sealBase`) 가 노드 자신의 `translate` 를 구동하는 것은 **사이클이 아니다**
  (`cycleCheck(all=True)` False).

**How to apply:** translate/rotate 에 끼어들 때는 `_source_plugs(node, attr)` 처럼 컴파운드 + 자식 셋을 함께 조회하고,
축별 소스는 축별로 잇고, 출력 컴파운드를 연결하기 전에 자식 연결을 끊는다. 되돌릴 때도 축별로.
구현 예: `A00170_driverTool/app/core/seal_rig.py` 의 `input_feed` / `_connect_feed` / `_disconnect_children` / `_restore_input`.

관련: [[wip-a00170-lip-seal]], [[mayapy-headless-verify]], [[getattr-settable-lies-for-constrained]]
