---
name: wip-a00390-chain-wave
description: A00390_WindTool Chain Wave 탭 — 체인이 회전만으로 싸인 파형을 따라간다(ikSpline + CV 구동). rootOnCurve=False 가 핵심 (v01.09)
metadata:
  node_type: memory
  type: project
---

A00390_WindTool **`Chain Wave` 탭** (v01.08→**01.09**, 2026-08-18).
"커브에 마야 기본 **Nonlinear > Sine** 을 걸고 조인트를 어태치한 결과"를
**조인트 회전값만 바꿔서** 재현한다. 문서: `docs/A00390_WindTool.md`.

**기존 Sine 탭으로는 안 되는 이유**(실측, 조인트 9개·뼈 2.0):
- `translateY` : 월드 위치는 파도지만 **뼈가 2.0→2.02~2.22 로 늘었다 줄고**, rotate 가 전부 0이라
  조인트가 자식을 안 본다. 조인트를 *옮기는* 것이라 당연하다.
- `rotateZ` : 뼈 길이는 지키지만 각 조인트 회전이 **자손에 누적**돼 체인이 말린다.

**해법은 마야에 이미 있다 — `ikSplineSolver`.** 커브를 따라 체인을 눕히되 **회전만** 쓰고
뼈 길이를 유지한다. 구성:
1. 조인트 rest 위치에 CV 를 둔 커브(3차),
2. `ikHandle -sol ikSplineSolver -ccv false -curve <crv>`,
3. CV 를 노드망으로 흔든다 —
   `CV_k = rest + windAmplitude · ramp_k · sin(2π(s_k/windWavelength − phase))`,
   `phase = (windPhaseTime − windPhaseOffset)/windPeriod` (Sine 탭의 적분 표현식 재사용).

**디포머를 쓰지 않은 이유**: `nonLinear sine` 의 amplitude/wavelength 는 **핸들 스케일이 섞인
디포머 로컬 단위**라 월드 단위로 예측이 안 된다(프로토타입에서 진폭 0.2 인데 체인이 반으로
접혔다). CV 를 직접 흔들면 진폭·파장을 **월드 단위 그대로** 준다.

**함정 — `rootOnCurve` 기본값이 True 다.** 커브 시작점이 움직이면 마야가 **루트 조인트의
translate 를 커브로 끌어당긴다.** "회전만" 약속이 깨지고, 셋업을 지운 뒤에도 체인 전체가 통째로
밀린 채 남는다(실측: 전 조인트가 똑같이 Y −1.448 — 회전은 전부 0인데 위치가 어긋나 있어 원인을
찾기 어렵다). **`rootOnCurve=False` + 첫 CV 는 항상 루트에 고정**.

**결과 실측**(뼈 2.0 · 파장 10 · 진폭 1.5): translate 완전 불변 · 세그먼트 2.0 정확 ·
루트 제자리 · 모든 조인트의 x축이 자식을 향함(내적>0.999) · 커브 이탈 최대 0.067(체인 16의 0.4%).

**알아둘 것**
- 진폭은 **CV 를 미는 양**이다. NURBS 3차는 CV 를 통과하지 않아 실제 흔들림은 ~0.85배.
- 파장 대비 진폭이 크면 **커브가 체인보다 길어져** 끝까지 못 간다(그래서 진폭을 2배로 해도
  흔들림은 1.5배쯤).
- ikSpline 은 한 줄 체인만 다룬다 → 갈래는 **첫 자식**을 따라가고 로그로 보고.
- ikSpline 은 커브가 바뀌어도 **평가가 돌아야** 자세가 갱신된다. 배치/스크립트에서는
  `dgdirty` + `currentTime` 재설정으로 한 번 풀어 준다(`_nudge_eval`).

**맨 끝 노드가 회전 0 으로 남는다 — dummy tip 으로 해결** (v01.11): `ikSpline` 은
**엔드 이펙터 조인트를 회전시키지 않는다**(실측: 마지막 두 노드의 월드 회전이 31.6° 로 동일).
프록시 체인 끝에 **마지막 뼈를 같은 방향·길이로 연장한 가상 조인트**를 붙이면 그것이 엔드
이펙터가 되어 진짜 팁도 회전한다. [[wip-a00410-secondarymotion]] 의 `Rotate last node`
(KawaiiPhysics dummy bone)와 같은 해법 — **체인 끝 노드 문제는 이 저장소에서 두 번째다.**

**조인트도 프록시 경로로 통합** (v01.11): 사용자 조인트에 ikSpline 을 직접 걸면 팁을 고치려고
**사용자 체인에 가상 조인트를 심어야** 한다. 프록시를 거치면 사용자 체인엔 ikHandle 도 가상
조인트도 없고 rotate 연결만 남는다. 대신 **조인트는 `jointOrient` 를 벗겨야** 한다
(로컬 = `R × JO`, 안 벗기면 JO 가 두 번). JO 는 빌드 시점 상수라 역행렬을 상수로 접어 넣는다.

**FK 컨트롤러도 된다** (v01.10): ikSpline 이 조인트 전용이라 **프록시 조인트 체인**(숨김)에
파동을 걸고 **월드 회전 변화량**을 컨트롤러 rotate 로 옮긴다 —
`ctrlWorld = restCtrlWorld × restProxyWorld⁻¹ × proxyWorld` → `× ctrl.parentInverseMatrix`.
앞 두 항은 상수로 접는다. 곱의 3×3 블록은 각 3×3 블록의 곱이라 **이동이 섞여도 회전은 정확**
(그래서 outputRotate 만 쓴다). 사이클 없음(조상 행렬 + 프록시에만 의존).
`ctrl > grp > ctrl` 구조는 **셰이프가 달린 트랜스폼**만 골라 체인으로 잡는다(그룹 통과).
Remove 는 빌드 시점 **rest 회전을 세트에 json 으로 적어 뒀다가** 되돌린다(컨트롤러는 0이 아닐 수 있다).

**함정 — rest 행렬은 파동을 걸기 전에 읽어라.** 프록시를 만든 뒤 ikSpline·CV 망을 먼저 걸고
rest 를 읽으면 **휘어진 자세가 rest 로** 잡혀 컨트롤러가 엉뚱한 각도로 간다(실측: 끝에서 1.09
어긋남). [[wip-a00170-lip-seal]] 의 "pairBlend 끼우기 전에 읽어라" 와 같은 순서 함정.

Node(라이브 드라이버) / Curve(회전 키로 굽고 셋업 삭제) 출력 + **Remove Chain Wave**
(`chainWave_waveSET` 로 되돌린다). 기존 Sine 탭은 그대로 두고 탭 2개로 나눴다.
관련: [[mayapy-headless-verify]], [[wip-a00410-secondarymotion]]
