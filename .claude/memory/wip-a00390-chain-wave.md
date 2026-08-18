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

Node(라이브 드라이버) / Curve(회전 키로 굽고 셋업 삭제) 출력 + **Remove Chain Wave**
(`chainWave_waveSET` 로 되돌린다). 기존 Sine 탭은 그대로 두고 탭 2개로 나눴다.
관련: [[mayapy-headless-verify]], [[wip-a00410-secondarymotion]]
