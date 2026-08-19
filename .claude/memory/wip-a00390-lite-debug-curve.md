---
name: wip-a00390-lite-debug-curve
description: "A00390_WindTool_V02 v02.03 — Chain Wave Lite debug curve (default ON); same build as the Chain Wave curve but driven BY the chain, and it has one CV fewer because Chain Wave adds an ikSpline dummy tip"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5daa567a-aa4a-4115-99c6-ec8bdb8c00eb
  modified: 2026-08-19T01:46:19.228Z
---

`A00390_WindTool_V02` **v02.03** — Chain Wave Lite 탭에 **`Debug Curve`** 체크박스(**기본 ON**).
체인마다 "어떻게 흔들리는지" 보여 주는 커브를 하나 만든다. 조인트 체인·FK 컨트롤러 체인 동일.

**구성은 Chain Wave 의 커브와 같고, 구동 방향만 반대다.**
체인 노드 위치를 CV 로 하는 **degree 3 NURBS**, CV k ↔ 노드 k.

```
CV k  <-  multMatrix(node_k.worldMatrix, curve.worldInverseMatrix)
          -> decomposeMatrix.outputTranslate -> shape.controlPoints[k]
```

- `outputTranslate`(double3) 를 `controlPoints[k]`(double3) 에 **컴파운드째 연결**된다.
- `worldInverseMatrix` 로 커브 오브젝트 공간으로 되돌리므로 **커브나 그 부모를 옮겨도** CV 가
  조인트에 붙어 있다. `worldInverseMatrix` 는 CV 에 의존하지 않아 **사이클이 없다**(실측).
- 표시 전용 — 셰이프를 `overrideDisplayType = 2`(**reference**) 로 둬 뷰포트에서 안 잡힌다.
  제거 세트에 들어가 `Remove Chain Wave Lite` 로 함께 지워진다.

**⚠️ Chain Wave 의 커브보다 CV 가 정확히 하나 적다** (조인트 9 → Lite 9 / Chain Wave 10).
Chain Wave 는 커브를 **프록시 체인**에서 만드는데, ikSpline 이 엔드 이펙터를 필요로 해 끝에
**가상 조인트(dummy tip)** 를 붙이기 때문이다([[wip-a00390-chain-wave]]). 두 커브의 CV 수가
같을 거라 가정하지 말 것 — 테스트에서 이걸로 한 번 헛짚었다.

**"Chain Wave 가 만들었을 커브" 를 계산해 그리는 방식은 일부러 안 썼다.** 두 모드는 값이 같지
않고(진폭의 뜻이 거리↔각도, 실측 비율이 파장에 따라 0.41~0.75 로 변해 상수 보정 불가 —
[[wip-a00390-chain-wave]] 참고), 그렇게 그리면 **실제 흔들림과 다른 그림**이 나와 디버그용으로
해롭다. 지금 방식은 실제 결과를 그리면서도 커브의 생김새·구성은 요청대로 같다.

검증: mayapy 2024 코어 26 + UI 7. 5개 프레임에서 **모든 CV 가 노드 위에 오차 `0.00000000`**,
`windEnvelope` 0 이면 커브도 rest 로, 체크 OFF 면 `nurbsCurve` 0개, Bone Root 3개 → 커브 3개,
FK 컨트롤러 체인 동일, Bake 뒤 잔여 0.

관련: [[wip-a00390-v02-envelope]], [[wip-a00390-v02-axis-driver]], [[mayapy-headless-verify]].
