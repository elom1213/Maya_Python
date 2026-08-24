# CHANGELOG - A00390_WindTool_V02

## v02.05 (2026-08-24) - Chain Wave Lite: Auto Period (체인 길이로 파장을 잡는다)

### Added
- **`Auto` 체크박스** (Chain Wave Lite 탭, `Wavelength` 줄 오른쪽, **기본 ON**).
  켜면 `Wavelength` 스핀박스 값을 쓰지 않고 **체인마다 그 체인의 길이**를
  `windWavelength` 로 넣는다. 그러면 루트에서 끝까지 파형이 **딱 한 주기** 실린다 —
  체인 위에서 진폭의 최댓값이 한 번, 최솟값이 한 번 나온다.

  ```
  u_k   = s_k / lambda - t        (s_k = 루트에서 노드 k 까지의 누적 거리)
  theta = swing * ramp_k * sin(2pi * u_k)

  lambda = (체인 전체 길이)  ->  s_k/lambda 가 루트 0, 끝 1  ->  정확히 한 주기
  ```

  - 켜면 `Wavelength` 스핀박스는 **비활성**된다(쓰이지 않는 값이라).
  - 파장은 여전히 드라이버의 **라이브 어트리뷰트**다. Auto 는 그 **시작값**만 정한다.
  - 체인 길이가 제각각이어도 각자 자기 길이에 맞는 파장을 받는다(예전에는 길이와
    무관하게 전부 같은 숫자를 썼다).
  - 결과 로그에 실제로 쓴 파장 범위가 찍힌다
    (`Auto Period on: windWavelength = each chain's own path length (8-11) ...`).

### 여기서 "체인의 길이" 는 경로 길이다
루트와 끝의 **직선 거리가 아니다.** 노드를 따라 걸어간 거리
(`wave_manager._arc_positions` 의 누적 거리)를 쓴다. 파형의 위상도 같은 누적 거리 `s_k`
로 매기므로, **굽은 체인이면 굽은 길이 그대로 한 주기**가 된다.

실측(조인트 9개, 앞 3칸은 X 로 2씩 · 뒤 5칸은 Y 로 2씩 꺾인 체인, 경로 길이 16):

| | 루트 -> 끝 sin 값 |
|---|---|
| Auto ON (lambda=16) | `-0.259 +0.499 +0.965 +0.866 +0.259 -0.499 -0.965 -0.866 -0.259` |
| Auto OFF (lambda=10) | `-0.259 +0.838 +0.776 -0.359 -0.999 -0.259 +0.838 +0.776 -0.359` |

Auto ON 은 최댓값(+0.965)과 최솟값(-0.965)이 각각 한 번씩 나오고 양끝 값이 같다 —
정확히 한 주기다. OFF 는 파장이 고정이라 1.6 주기가 실린다.
직선 8 · 굽은 11(=3+4+4) 두 체인을 함께 빌드하면 드라이버가 각각 8.0 / 11.0 을 받는다.

### Changed
- Auto 가 켜져 있으면 `Wavelength <= 0` 검사를 건너뛴다(쓰이지 않는 값이므로).

## v02.04 (2026-08-21) - 아웃라이너 그룹 분리 + 드라이버가 루트를 따라간다

### Changed
- **Chain Wave Lite 의 생성물을 종류별로 그룹에 담는다.** 예전에는 체인마다
  `(드라이버 로케이터, 디버그 커브)` 를 이어서 만들어 아웃라이너에 **번갈아** 쌓였다.
  이제 빌드 하나가 그룹 **둘**을 만든다.

  | 그룹 | 담는 것 |
  |------|---------|
  | `<prefix>_liteDriverGrp` | 드라이버 로케이터 전부 |
  | `<prefix>_liteCurveGrp` | 디버그 커브 전부 |

  - `Debug Curve` 를 끄면 커브 그룹은 **아예 만들지 않는다**.
  - 두 그룹 모두 제거 세트에 들어가 `Remove Chain Wave Lite` 로 함께 지워진다.
  - 그룹은 **원점·단위행렬**이고 `parent -relative` 로 옮긴다. 로컬을 그대로 두므로
    월드 위치가 변하지 않고, **드라이버의 `translate` 가 이미 연결돼 있어**(아래 참고)
    기본 parent 의 "월드 유지" setAttr 이 불가능하다는 실제 이유도 있다.

### Added
- **드라이버 로케이터가 루트 본/컨트롤러의 월드 위치를 계속 따라간다** (Node 출력).
  **Sine / Chain Wave / Chain Wave Lite 세 탭 전부**. 기존 체크박스를
  `Place driver at chain root (follow)` 로 바꿔 그대로 켜고 끈다(기본 ON).

  ```
  multMatrix(root.worldMatrix[0], driver.parentInverseMatrix[0])
      -> decomposeMatrix.outputTranslate -> driver.translate
  ```

  - **constraint 를 쓰지 않는다** — 월드 행렬 직결이다(요청대로).
  - **위치만.** 회전은 연결하지 않는다 — `driver.rotate` 는 그대로 비어 있다.
  - 루트 조인트를 옮기든, 루트 컨트롤러를 움직이든, **리그 그룹째 옮기든** 따라온다.
  - 대신 드라이버의 `translate` 가 구동되므로 **손으로 옮길 수 없게 된다**
    (원래도 위치는 의미가 없는 "어트리뷰트 홀더" 였다).
  - `Curve` 출력에서는 걸지 않는다 — 구운 뒤 셋업을 통째로 지우기 때문.

### 왜 사이클이 안 나는가 (`parentInverseMatrix` 를 쓴 이유)
`worldInverseMatrix` 를 쓰면 드라이버 **자신의** translate 를 읽어 진짜 사이클이 된다.
`parentInverseMatrix` 는 **부모**의 월드 역행렬이라 자기 translate 에 의존하지 않는다.
드라이버 `wind*` → … → `root.rotate` → `root.worldMatrix` → `driver.translate` 경로도
`driver.translate` 로 되돌아오지 않으므로 닫히지 않는다.

사이클이 되는 배치는 **하나뿐**이다 — 드라이버가 root 의 **조상**인 경우
(그때는 `root.worldMatrix` 가 드라이버의 translate 에 의존한다).
그 경우는 **연결하지 않고** 로그에 사유를 남긴다:
`Root-follow skipped (would cycle): <root> (driver is an ancestor of the root)`.

### 검증
`mayapy` (Maya 2024) 헤드리스 — **코어 43 + UI 22 항목 전부 통과** + 이중 빌드 스모크 테스트.

- 로케이터 그룹 1개 / 커브 그룹 1개, 각 그룹에 **자기 종류만** 3개씩,
  아웃라이너 최상위에 흩어진 로케이터·커브 **0개**
- 리그 그룹 이동 · 루트 조인트 이동 둘 다에서 드라이버 위치 오차 `< 1e-6`
- 루트를 **회전**시켜도 `driver.rotate` 는 연결 없음(위치만 따라감)
- 씬에 `constraint` 노드 **0개**, `cycleCheck` **비어 있음**(빌드 직후·이동 후·컨트롤러 체인)
- 드라이버가 조상인 배치는 **연결 거부** + 노드도 만들지 않음
- 리그를 옮긴 뒤에도 디버그 커브 CV 가 체인 위에 **오차 `0.0000000000`**
- `Debug Curve` OFF → 커브 그룹 없음 / `nurbsCurve` 0개, 드라이버 그룹은 그대로
- 체크박스 OFF → 원점에 그대로, `translate` 연결 없음, 그룹 분리는 유지
- Sine · Chain Wave 탭에서도 추종 동작, Remove 후 `*rootFollow*` 잔여 0
- `Curve` 출력은 예전대로 구운 뒤 잔여물 0

---

## v02.03 (2026-08-19) - Chain Wave Lite 디버그 커브

### Added
- **`Debug Curve` 체크박스**(Chain Wave Lite 탭, **기본 ON**) — 체인이 어떻게 흔들리는지
  보여 주는 커브를 체인마다 하나 만든다. 조인트 체인·FK 컨트롤러 체인 둘 다.
  - **Chain Wave 탭이 만드는 커브와 같은 방식**이다 — 체인 노드 위치를 CV 로 하는
    **degree 3 NURBS**(노드가 적으면 차수를 낮춘다), CV k ↔ 체인 노드 k.
  - 다른 것은 **구동 방향뿐**이다:
    `Chain Wave` = 커브가 ikSpline 으로 체인을 **구동**(커브 → 체인),
    `Lite` = 체인이 각도로 움직이고 커브가 **따라간다**(체인 → 커브).
  - CV k = `multMatrix(node_k.worldMatrix, curve.worldInverseMatrix)` →
    `decomposeMatrix.outputTranslate` → `controlPoints[k]`.
    커브나 그 부모를 옮겨도 CV 는 조인트에 붙어 있고, `worldInverseMatrix` 는 CV 에
    의존하지 않아 **사이클이 없다**(실측).
  - **표시 전용**이다 — 아무것도 구동하지 않고, 셰이프를 `reference` 로 둬 뷰포트에서
    **선택되지 않는다**. `Remove Chain Wave Lite` 로 셋업과 함께 지워진다.

### 왜 "Chain Wave 가 만들었을 커브" 를 계산해 그리지 않았나
두 모드는 **값이 같지 않다**(v02.00 참고 — 진폭의 뜻이 거리 ↔ 각도이고, 실측 비율이
파장에 따라 0.41~0.75 로 변해 상수 보정이 불가능하다). 그런 커브를 그리면 **실제 흔들림과
다른 그림**을 보여 주게 되어 디버그용으로 오히려 해롭다. 지금 방식은 **실제 결과**를 그린다.

### 알아둘 것
- Chain Wave 의 커브보다 **CV 가 정확히 하나 적다**(조인트 9 → Lite 9 / Chain Wave 10).
  Chain Wave 는 커브를 **프록시 체인**에서 만드는데, ikSpline 이 엔드 이펙터를 필요로 해
  끝에 **가상 조인트(dummy tip)** 를 하나 더 붙이기 때문이다. 디버그 커브는 실제 노드만 그린다.
- 체크를 끄면 예전 그대로 **커브가 하나도 생기지 않는다**(로그 문구도 예전 문장으로 돌아간다).

### 검증
`mayapy` (Maya 2024) 헤드리스 — 코어 26 + UI 7 항목 **전부 통과**.

- 기본 ON 으로 커브 1개 생성, CV 수 = 노드 수, degree 3, 셰이프가 reference
- **5개 프레임에서 모든 CV 가 체인 노드 위에 정확히**(최대 오차 `0.00000000`)
- `windEnvelope` 를 0 으로 내리면 커브도 rest 선으로 돌아감
- **사이클 없음**, 커브의 하류 연결 없음(구동하지 않음)
- Remove 후 커브·헬퍼 노드 잔여 0, 회전 rest 복귀
- 체크 OFF 면 `nurbsCurve` 가 **0개**이고 파형은 그대로 동작
- Bone Root 3개 → 커브 3개, **FK 컨트롤러 체인**에서도 CV 가 컨트롤러 위에
- Bake(Curve) 출력 뒤에는 커브도 함께 사라짐

## v02.01 (2026-08-18) - windEnvelope

### Added
- **`windEnvelope` 어트리뷰트 [0, 1]** — Node 출력이 만드는 **모든** 드라이버
  (Sine `*_windDriver`, Chain Wave `*_waveDriver`, Chain Wave Lite `*_liteDriver`)에 붙는다.
  - `0` = 노드가 **아무 영향도 주지 않는다**, `0.5` = **절반**, `1` = **완전 적용**(기본값).
  - `addAttr` 의 `minValue`/`maxValue` 로 구간을 강제한다 — 마야가 범위 밖 `setAttr` 을
    **거부한다**(잘라 내는 게 아니라 `RuntimeError`). 툴에서 넘기는 초기값은 파이썬에서 먼저 클램프.
  - 키를 걸 수 있으므로 바람을 **페이드 인/아웃** 시킬 수 있다 — 진폭을 건드리지 않고.
- 세 탭 모두 UI 에 `Envelope` 스핀박스(0~1, 기본 1.0). Sine 탭은 Node 전용이라
  Curve 출력에서는 `Speed`/`Node Offset` 처럼 **비활성**된다.

### 구현
파형 값이 **진폭에 정비례**하므로 envelope 를 **진폭에 한 번만** 곱하면 아래 전부가 같은
비율로 줄어든다. 그래서 드라이버당 `multDoubleLinear` **1개**면 끝이다(조인트/CV 마다
노드를 더 만들지 않는다).

| 탭 | 실효값 | 노드 | envelope=0 일 때 |
|----|--------|------|------------------|
| Sine | `windAmplitude × windEnvelope` | `*_ampEnvelope` | 값이 전부 0 (진폭 0 과 같음) |
| Chain Wave | `windAmplitude × windEnvelope` | `*_ampEnvelope` | CV 가 rest → 체인이 rest 자세 |
| Chain Wave Lite | `windSwingAngle × windEnvelope` | `*_liteSwingEnv` | theta 전부 0 → rest 자세 |

Chain Wave / Lite 는 이 노드도 제거용 세트에 들어가므로 Remove 로 같이 지워진다.

### 검증
`mayapy` (Maya 2024) 헤드리스 — 코어 21항목 + UI 14항목 **전부 통과**.

- 세 드라이버 모두 `windEnvelope` 존재 · 기본값 1.0 · 빌드 시 초기값 유지
- 범위 밖 `setAttr`(5.0 / −3.0) 이 거부되는지
- Sine: `0.5` 가 `1.0` 결과의 **정확히 절반**(5프레임 표본), `0.0` 이 전부 0
- Chain Wave: `0.5` 가 CV 변위의 **정확히 절반**, `0.0` 이면 CV 변위 0 · 회전 0 ·
  조인트 월드 위치가 rest 와 `0.000000` 차이
- Chain Wave Lite: `0.5` 가 로컬 회전의 **정확히 절반**, `0.0` 이면 rest 와 `1e-8` 미만 차이
- 임의 축(쿼터니언 경로, 대각 체인)에서도 `0.0` = rest · `0.5` 가 rest 와 full 사이
- Remove 후 envelope 노드 잔여 0

> ⚠️ Chain Wave 에서 **CV 변위는 envelope 에 정확히 비례하지만 조인트 회전각은 아니다.**
> ikSpline 이 커브를 푸는 과정이 비선형이라 `0.5` 에서 회전 비율이 0.47~1.08 로 흩어진다
> (변위가 0 근처인 조인트에서 특히). "절반의 영향력" 은 **파동의 세기**가 절반이라는 뜻이고,
> Lite 탭은 각도를 직접 다루므로 회전각까지 정확히 절반이다.

## v02.00 (2026-08-18) - Chain Wave Lite

`A00390_WindTool` v01.11 을 그대로 복제해 시작한다(Sine / Chain Wave 탭은 동일).

### Added
- **Chain Wave Lite 탭** - 커브·ikHandle·프록시 조인트 **없이** 각도만으로 같은 종류의
  파형을 만든다. 루트가 100개를 넘는 상황(털·풀·촉수 다발)을 위한 것.
  - `theta_k = swing * ramp_k * sin(2pi(s_k/lambda - phase))`, 조인트 로컬 회전은
    `theta_k - theta_(k-1)` — FK 누적을 상쇄해 체인이 말리지 않는다.
  - **진폭의 뜻이 바뀌었다**: 거리(월드 단위)가 아니라 **뼈가 흔들리는 각도(도)**.
    기존 탭과 같은 숫자가 같은 그림을 주지 않는다.
  - 회전축은 체인 방향 x 진동축으로 구하고 rotate 채널 공간으로 옮긴다. 기본축과
    맞으면 채널 직결, 아니면 `axisAngleToQuat -> quatProd -> quatToEuler`.
  - 조인트든 FK 컨트롤러든 **같은 경로** — 프록시 체인이 필요 없다.
- `core/wave_lite_manager.py` (신규). 기존 `wave_manager` 는 손대지 않았다.

### 측정
- 같은 체인(조인트 9, 뼈 2.0)에서 **141 -> 95 노드 (33% 감소)**,
  커브 0 · ikHandle 0 · ikEffector 0 · 프록시 조인트 0.
- 뼈 각도가 정의식과 최대 **0.015도** 차이(16샘플 싸인 LUT 보간 오차).
- 뼈 길이 유지 · 루트 고정 · translate 불변.

### 알아둘 것
- 기존 Chain Wave 와 **값이 같지 않다.** 접선각을 그대로 쓰면 ikSpline 대비 과대해지고
  (파장 10에서 -25.5도 vs -39.7도), 그 비율이 파장에 따라 0.41~0.75로 변해 상수 보정이
  불가능하다. 그래서 재현 대신 **정의를 각도로 바꿨다**.
