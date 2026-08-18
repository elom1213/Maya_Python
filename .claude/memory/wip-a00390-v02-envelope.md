---
name: wip-a00390-v02-envelope
description: "A00390_WindTool_V02 v02.01 — windEnvelope [0,1] on every Node driver (Sine/Chain Wave/Lite); one multiply node per driver, and Chain Wave's rotation is NOT linear in amplitude"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5daa567a-aa4a-4115-99c6-ec8bdb8c00eb
  modified: 2026-08-18T08:48:31.657Z
---

`tools/A00390_WindTool_V02` **v02.01** — 세 탭(`Sine` · `Chain Wave` · `Chain Wave Lite`)의
`Node` 출력이 만드는 드라이버 전부에 **`windEnvelope` [0, 1]** 영향력 어트리뷰트.
0 = 영향 없음 · 0.5 = 절반 · 1 = 완전 적용(기본). UI 는 탭마다 `Envelope` 스핀박스
(Sine 것은 Node 전용이라 Curve 출력에서 비활성).

**드라이버당 곱셈 노드 1개면 끝난다.** 파형 값이 **진폭에 정비례**하므로 envelope 를 진폭에
한 번만 곱하면 그 아래 조인트·CV 가 전부 같은 비율로 줄어든다. 조인트/CV 마다 노드를 만들지 말 것.

| 탭 | 실효값 | 노드 | env=0 |
|----|--------|------|-------|
| Sine (`wind_manager`) | `windAmplitude × windEnvelope` | `<drv>_ampEnvelope` | 값 전부 0 |
| Chain Wave (`wave_manager`) | `windAmplitude × windEnvelope` | `<drv>_ampEnvelope` | CV rest → 체인 rest |
| Lite (`wave_lite_manager`) | `windSwingAngle × windEnvelope` | `<chain>_liteSwingEnv` | theta 0 → rest |

상수는 `wind_manager.DRIVER_ENVELOPE`, 나머지 두 매니저가 import 한다.
Chain Wave / Lite 는 이 노드도 제거 세트(`_waveSET` / `_waveLiteSET`)에 들어가 Remove 로 함께 지워진다.

**⚠️ Chain Wave 는 CV 변위가 정확히 절반이지, 조인트 회전각이 절반은 아니다.**
`0.5` 에서 CV 변위는 `1.0` 의 정확히 절반이지만(실측 일치), ikSpline 이 커브를 푸는 과정이
비선형이라 **회전 비율이 0.47~1.08 로 흩어진다**(변위가 0 근처인 조인트에서 특히 크게).
"절반의 영향력" 은 **파동의 세기**가 절반이라는 뜻. 각도를 직접 다루는 **Lite 는 회전각까지
정확히 절반**이다. → 테스트는 Chain Wave 를 회전 비율이 아니라 **CV 변위**로 재야 한다.

**mayapy 검증 함정 둘**:
- 임의 축 경로가 쓰는 `axisAngleToQuat`/`quatProd`/`quatToEuler` 는 **`quatNodes` 플러그인**이라
  standalone 에서는 `cmds.loadPlugin("quatNodes")` 를 먼저 해야 한다(안 하면 노드는 만들어지지만
  `setAttr ...inputAxisX` 가 `No object matches name`).
- `cmds.curve(name=...)` 는 **트랜스폼에만** 이름을 준다 — 셰이프는 `curveShape1`. 커브를 이름으로
  찾을 땐 `ls(type="nurbsCurve")` 말고 트랜스폼을 찾을 것.

검증: mayapy 2024 헤드리스 35항목(코어 21 + UI 14) 통과 — 존재/기본값/빌드 초기값, 범위 밖 거부,
0.5 절반, 0.0 rest 복귀(Lite `1e-8` 미만, Chain Wave `0.000000`), 대각 체인 쿼터니언 경로, Remove 잔여 0.

관련: [[addattr-min-max-raises-not-clamps]], [[wip-a00390-windtool]], [[wip-a00390-chain-wave]],
[[mayapy-headless-verify]], [[qapplication-before-maya-standalone]].
