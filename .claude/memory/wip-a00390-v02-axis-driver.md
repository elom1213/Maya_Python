---
name: wip-a00390-v02-axis-driver
description: "A00390_WindTool_V02 v02.02 — Chain Wave Lite object-space Rotate Axis (Sway Axis dropped from the computation, not just greyed out) + driver locator placed at the chain root on all three tabs"
metadata: 
  node_type: memory
  type: project
  originSessionId: 064559b4-a50c-475d-865d-675d82033aad
  modified: 2026-08-19T01:05:45.214Z
---

`tools/A00390_WindTool_V02` **v02.02** — 요청 두 가지.

## 1. Chain Wave Lite `Rotate Axis (object)`

체크박스 + X/Y/Z 콤보. 켜면 각 노드의 **`rotate<축>` 채널 하나에만** 각도를 직결한다
(`_apply_angle(local_index=...)`), 끄면 기존대로 `world_axis = chain_dir × up`.

**비활성은 UI 만이 아니라 계산에서도 해야 한다.** `_build_chain_lite` 가 `local_axis` 를 받으면
월드 축 분기를 **통째로 건너뛴다**(그래서 "체인이 축과 평행" 실패도 안 난다). 검증도 UI 상태가
아니라 **결과 회전값으로** 했다 — `Sway Axis` 를 X/Y/Z 로 돌려도 회전값이 완전히 동일.

- 부수 효과: 축이 기울 때 노드마다 붙던 쿼터니언 3개(`axisAngleToQuat`/`quatProd`/`quatToEuler`)가
  부호 곱셈 1개로 → 비스듬한 조인트 9 체인에서 **102 → 84 노드**. 나머지 두 rotate 채널은 비어 있어
  애니메이터가 계속 쓸 수 있다.
- **⚠️ 전제**: `theta_k − theta_(k-1)` 차분이 월드 각도로 누적되려면 체인 노드들이 **같은 방향으로
  orient** 돼 있어야 한다. 제각각이면 파형이 아니라 각자 흔들린다 → 그때는 Sway Axis.
- 조인트/FK 컨트롤러 모두 같은 경로(Lite 는 프록시가 없다).

## 2. `Place driver at chain root` (기본 ON)

`Node` 출력 드라이버 로케이터를 **체인 최상단 노드의 월드 위치**에 만든다. 예전엔 항상 원점이라
원점에서 먼 체인은 어느 드라이버가 누구 것인지 못 찾았다. **세 탭 전부**(`Sine`/`Chain Wave`/`Lite`),
`Curve` 출력에서는 비활성(셋업이 지워지므로). Bone Root 모드면 루트마다 자기 자리에.

- 각 `_make_*_driver(place_at=...)` → `cmds.xform(drv, ws=True, t=place_at)`.
- 위치는 **셋업이 체인을 건드리기 전** rest 위치로 잡는다(Chain Wave 는 커브·ikHandle·프록시를
  먼저 만드니 순서 주의).
- 로케이터는 어트리뷰트 홀더일 뿐이라 **옮겨도 결과가 안 바뀐다**(실측). 그래서 OFF 여도 결과 동일.

## 곁가지

임의 축 경로가 쓰는 쿼터니언 노드 3종은 **`quatNodes` 플러그인** 소속이라 안 올라와 있으면
`createNode` 뒤 `setAttr` 이 `No object matches name` 으로 죽는다 → 그 경로 앞에서
`loadPlugin("quatNodes", quiet=True)`. (테스트 함정으로만 알고 있던 것을 툴 코드로 옮겼다,
[[wip-a00390-v02-envelope]])

검증: mayapy 2024 헤드리스 **30항목**. 문서 `JUN_All/docs/A00390_WindTool_V02.md` 8·9장.
관련: [[wip-a00390-chain-wave]], [[wip-a00390-windtool]], [[mayapy-headless-verify]].
