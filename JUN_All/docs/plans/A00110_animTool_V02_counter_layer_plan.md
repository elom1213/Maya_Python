---
title: A00110_animTool_V02 Bake > Counter Layer (상위 레이어의 월드 변화를 되돌리는 보정 레이어) 계획서
aliases: [animTool Counter Layer, 카운터 레이어, 보정 레이어, world hold layer, CounterLayerManager]
tags: [plan, maya-python, animtool, anim-layer, bake, counter-animation]
updated: 2026-10-29
---

# A00110_animTool_V02 — `Bake > Counter Layer` (보정 레이어) 계획서

> **목적**: `global_ctl > foot_l_ctl, foot_r_ctl` 구조에서 발은 additive 레이어 `lyr_01 … lyr_n` 에 키가 있고, 나중에
> `global_ctl` 만 든 레이어 `lyr_glo` 에 위치·회전 키를 찍었다. 그러면 발의 **월드** 위치·회전이 `lyr_glo` 가 있기 전과
> 달라진다. **`lyr_glo` 는 그대로 두고**, 발의 월드 위치·회전이 **`lyr_glo` 가 있기 전과 같아지도록** 발에 키를 찍은
> **새 레이어 하나**를 만든다.

> [!note] **상태: v02.26 구현 완료 (2026-10-29, 같은 날). 마야 GUI 실기 확인 전.**
> 이 문서의 수치는 전부 **mayapy(Maya 2024) 실측**이다(§4). 핵심 가정 **21 항목 전수 통과** — 발의 worldMatrix 가
> **정수 프레임 전부 1e-14 로 동일**, 레이어 누적 모드 · 조인트 · 가중치 · override · 큰 회전 · 발이 `lyr_glo` 에도 든 경우까지.
> 사전 실험 스크립트(`exp_counter_layer.py`)는 회귀 시험 `tools/A00110_animTool_V02/tests/test_counter_layer.py`
> (**51 / 51**)로 흡수해 삭제했다. 부록 A 는 그 핵심 두 함수의 요지다.
>
> **구현 때 더해진 것 — 메모리 설계(사용자 요청: 1000+ 프레임 구간)**: 스냅샷을 구간 전체로 들지 않고
> `CHUNK_FRAMES = 200` 청크로 "뮤트 → 스냅샷(`array('d')` 16개) → 뮤트 해제 → 키 → 버림" 을 반복한다. 메모리 상한 =
> 청크 × 오브젝트 × 16 double 로 **구간 길이와 무관**. 청크 2 부터는 **보정 레이어 자신도 함께 뮤트**해야 앞 청크 키의
> 외삽이 스냅샷을 오염시키지 않는다(회귀 T7: 청크 7 · 1 프레임에서도 1e-14).
>
> ⚠️ 같은 날 **`Bake > Merge Layers` 계획서**(`A00110_animTool_V02_layer_range_merge_plan.md`)가 다른 세션에서 나왔다.
> 둘 다 `Bake` 카테고리의 새 하위 탭이고 둘 다 `main_window.py` 의 상위 탭 구성표를 건드린다. **구현 시작 전에
> `git log -3 -- tools/A00110_animTool_V02` 로 어느 쪽이 먼저 들어갔는지 보고 버전 번호(02.26 이후)를 정한다.**

---

## 0. 요약 (1분 버전)

1. **마야 레이어 기능으로는 안 된다.** `bakeResults -resolveWithoutLayer` 는 "이 레이어를 뺀 스택에서 **같은 어트리뷰트 값**" 을
   굽는 도구다. 여기서 바뀐 것은 발의 어트리뷰트가 아니라 **부모(`global_ctl`)** 라서, 발의 로컬 값은 `lyr_glo` 전후가 똑같다.
   문제는 **오브젝트 사이(부모→자식)** 에 있고, 그래서 월드 행렬을 직접 재는 기능이 필요하다(§2).
2. **알고리즘은 두 번 훑는다**(§5). ① 되돌릴 레이어(`lyr_glo`)를 **뮤트**하고 발의 `worldMatrix` 를 매 프레임 기록(= 목표).
   ② 뮤트를 풀고 매 프레임 `xform -ws -m <목표>` 로 발을 목표 월드에 놓은 뒤 로컬 T/R 을 읽어 **새 additive 레이어에
   `setKeyframe -animLayer -value`** 로 찍는다. 이 명령이 **"최종 평가값이 그 값이 되도록 레이어 기여를 역산"** 하므로 레이어
   누적 모드(by-layer / by-component) · 가중치 · 아래 override 레이어 · `jointOrient` · 회전 순서를 **우리가 계산하지 않는다**(§4).
3. **정확도 계약**(§3): 정수 프레임은 **모든 프레임에서 완전히 같다**(실측 1e-14). 프레임 사이는 보간이라 **1e-3 정도** 다르다
   (베이크와 같은 성질). 드라이버 키 프레임에만 키를 찍는 희소 모드는 **0.95 유닛** 틀려서 기본에서 뺀다(§4 F13).
4. **회전 연속성**은 우리가 책임진다. `xform` 이 돌려준 오일러와 그 **동치해(`alternateSolution`) 중 지금 로컬 회전에 가까운 쪽**을
   `setToClosestCut` 으로 고른다(`closestSolution` 은 짐벌 근처에서 다른 회전이 된다). 270° 회전 드라이버에서 커브 점프 최대 23°(F4).
5. 비용은 **오브젝트·프레임당 0.9 ms**(F10) → 50 컨트롤 × 1000 프레임 ≈ 44 s. 진행 팝업이 필요하다.
6. **어디에**: `Bake > Counter Layer` 하위 탭(§7·§8). 로직은 `app/core/counter_layer_manager.py` 의 `CounterLayerManager` 한 클래스.
7. **SmartLayer 참고 범위**(§2-3): 사용자 노출 설명문(툴팁·Starter Guide)과 UI 동작까지만. 코어는 컴파일 `.pyc` + 라이선스상
   리버스 엔지니어링 금지라 **디컴파일하지 않는다**(2026-08 Curve Filters 이식 때와 같은 결정). 가져온 것은 "레이어 켜고/끄고
   비교해 델타를 얻는다" 는 원리와 World Space 개념이고, SmartLayer 의 본령인 **속도 비례 분배는 이 기능의 목적이 아니라**
   의도적으로 빼고 v2 후보로 둔다(§13).

---

## 1. 요청 정리

> `global_ctl > foot_l_ctl, foot_r_ctl`. 발은 additive 레이어 `lyr_01 … lyr_n` 에 키. `global_ctl` 만 든 `lyr_glo` 를 만들어
> 위치·회전 키를 찍으면 월드 기준 발 위치·회전이 달라진다. `lyr_glo` 는 그대로 두고, **`lyr_glo` 가 있기 전의 월드 기준으로
> 발의 위치·회전이 같도록** 만드는 **추가 레이어**를 만드는 기능. `A00110_animTool_V02` 에 추가. `_SmartLayer` 의 Smart Layer
> 탭 참고 가능.

| 요소 | 해석 | 근거 |
|---|---|---|
| "있기 전" | **`lyr_glo` 를 뮤트한 상태**의 평가 결과 | 레이어를 지우지 않고 재는 유일한 방법. 가중치가 애니메이션돼도 성립(F6) |
| "그대로 놔두되" | `lyr_glo` 의 커브 · 멤버 · 가중치 · 순서 **무변경** | F1·F9 로 모든 기존 커브가 동일함을 확인 |
| "추가 레이어" | **새 additive 레이어 1개**, 스택 **맨 위** | 새 레이어는 마야가 맨 위(`children[-1]`)에 만든다(F1) |
| "위치, 회전값" | translate · rotate 6 채널. **scale 은 v1 제외** | 요청에 없음. `lyr_glo` 가 스케일을 바꾸면 T/R 만으로는 월드 스케일을 못 돌린다(§9) |
| 발이 `lyr_glo` 에도 키가 있다면 | 그 기여도 되돌린다 — 정의가 "뮤트 상태" 이므로 | F5 통과. 로그에 그 사실을 적는다 |

---

## 2. 왜 새 기능이 필요한가

### 2-1. 마야에 있는 것들이 안 맞는 이유

| 후보 | 왜 안 되나 |
|---|---|
| `bakeResults -resolveWithoutLayer lyr_glo` | **어트리뷰트 단위**다. 발의 tx…rz 는 `lyr_glo` 전후 값이 같다(바뀐 건 부모). 월드 차이를 모른다 |
| Merge Layers | 레이어를 합치는 것. 부모의 움직임을 자식에 반영하지 않는다 |
| 컨스트레인트 → 베이크 | 목표 월드를 담은 로케이터를 굽고 발을 parentConstraint 로 붙여 `bakeResults -destinationLayer` — 가능하지만 레이어 멤버 plug 에 컨스트레인트를 물리면 `animBlendNode` 연결이 끊긴다. 이 저장소는 **컨스트레인트 없는 베이크**를 택해 왔다(A00120 `constraint-free bake`) |
| 손으로 키 | 프레임마다 발을 되돌려 놓고 키 — 바로 이것을 자동화하는 것이 이 기능이다 |

### 2-2. 수학

프레임 `f` 에서 발의 월드는 `W(f) = L(f) · P(f)` (마야 행 벡터 규약, `P` = `parentMatrix[0]`).
`lyr_glo` 는 `P` 만 바꾼다: `P_pre(f) → P_glo(f)`. 목표는 `W_pre(f) = L_pre(f) · P_pre(f)` 를 유지하는 것이므로
필요한 로컬은 `L_need(f) = W_pre(f) · P_glo(f)⁻¹`. 보정 레이어에 들어가야 할 값은 **"다른 모든 레이어가 낸 `L_pre` 위에
더해져 `L_need` 가 되는 값"** — 회전 누적이 by-layer 면 행렬 곱의 역, by-component 면 성분 차, 가중치가 있으면 나눗셈, 아래에
override 가 있으면 또 다르다. **이 역산을 우리가 하지 않고 마야에 맡기는 것**이 설계의 핵심이다 — `setKeyframe -animLayer L -value V`
는 "그 plug 의 최종 평가값이 V 가 되도록 L 의 커브 값을 역산" 한다([[wip-a00110-fill-keys]] 에서 처음 확인, 여기서 F1~F7 로 재확인).
`L_need` 의 분해(피벗 · `rotateAxis` · `jointOrient` · 회전 순서)도 `cmds.xform -ws -m` 에 맡긴다.

### 2-3. `_SmartLayer` 에서 참고한 것 / 하지 않은 것

`C:\Users\USER\Documents\maya\scripts\_SmartLayer`(마야가 지금 쓰는 패키지). 코어·UI 전부 `__hybrid__/*.pyc`(파이썬 버전별
컴파일) 이고 `.py` 는 로더 스텁이다. **디컴파일하지 않는다** — 라이선스 당사자는 벤더이고 이 저장소는 공개 포트폴리오다
(2026-08 Curve Filters 이식과 같은 결정, [[wip-a00110-tab-taxonomy]]). 참고는 **툴팁 · Starter Guide · Troubleshooting 텍스트**
(사용자 노출 문자열)와 UI 구성까지.

| SmartLayer 설명문에서 가져온 원리 | 이 기능에서의 적용 |
|---|---|
| "레이어를 켠 상태와 끈 상태의 트랜스폼을 비교해 델타를 만든다" | §5 의 두 번 훑기(뮤트 스냅샷 → 역산 키) |
| **World Space** — "메인 컨트롤이 애니메이션될 때 IK · 발 · 폴벡터처럼 월드 위치가 중요한 컨트롤" | 정확히 이 요청의 상황. 우리는 월드만 다룬다(로컬 모드 불필요 — 로컬이면 바뀌는 게 없다) |
| "키가 없는 오브젝트는 건드리지 않는다 · 모든 오브젝트에 같은 프레임에 키가 있어야 한다"(함정 3·4) | 우리는 **매 프레임 샘플링**이라 이 함정이 없다. 희소 키 모드는 그래서 기본에서 뺀다(F13) |
| 결과를 **새 레이어**에 담고 원본 레이어는 보존 | 같다 |
| "Run Simulation" 으로 무거운 리그 가속 | 우리는 `currentTime` 루프 자체가 평가 순서를 지키므로 별도 옵션 없음. 비용은 §4 F10 |

**가져오지 않은 것**: SmartLayer 의 본령인 **속도 비례 분배**(Linear Offset · Transformation · Spline, 발 미끄럼 방지 블렌드).
그것은 "레이어의 변경을 원래 애니메이션 흐름에 맞춰 **퍼뜨리는**" 도구이고, 이 요청은 "변경을 **정확히 상쇄**" 하는 것이다.
둘은 반대 방향이다. 분배형은 §13 v2 후보.

---

## 3. 정확도 계약

| 항목 | 계약 | 실측 |
|---|---|---|
| 정수 프레임 `[s, e]` | 발의 `worldMatrix` 가 뮤트 상태와 **동일** | 1e-14 (F1~F7, F12, F15) |
| 프레임 사이 (`f + 0.5`) | 보정 커브와 드라이버 커브의 보간이 서로 달라 **근사**. 베이크와 같은 성질 | 1.15e-3 (유닛) |
| 구간 밖 | 보정 레이어가 영향을 주지 않아야 한다 → `s-1` · `e+1` 에 **identity(0) 키** | 미실측 — 구현 때 회귀 1항목 (§11) |
| 기존 커브 | Base · `lyr_01…n` · `lyr_glo` 의 키 시간·값 **무변경** | F1·F8·F9 동일 |
| undo | 한 번에 보정 레이어 통째로 제거, 다른 커브 복귀 | F8 |

`Step N`(N 프레임마다 키) 옵션을 두되 **기본 1**. N=2 에서 2.5e-3, 드라이버 키(50 프레임)에만 찍으면 **0.95** 틀린다(F13·F13b).

---

## 4. 사전 검증 — mayapy (Maya 2024) 실측

스크립트 `tools/A00110_animTool_V02/tests/exp_counter_layer.py`(15 항목) + 추가 6 항목(부록 A 에 요지). 씬은 §1 의 구조 그대로:
`global_ctl > foot_l_ctl, foot_r_ctl`, 발은 Base(25 프레임 간격) + `lyr_01`(40) + `lyr_02`(30) 에 6 채널 키, `lyr_glo` 는
`global_ctl` 6 채널 50 프레임 간격, 구간 `[0, 200]`.

### 4.1 통과 (21 / 21)

| # | 조건 | 결과 |
|---|---|---|
| F1 | 기본 (transform · xyz · 회전 누적 by-layer) | 글로벌이 발을 27.7 유닛 움직였고, 보정 뒤 월드 오차 **9.8e-15**. 다른 커브 무변경. 새 레이어 = `children[-1]`(맨 위) |
| F2 | 레이어 전부 회전 누적 **by-component** | 9.8e-15 |
| F3 | 보정 대상이 **조인트**(`jointOrient` 10/20/30 · 회전 순서 **zxy**) | 9.8e-15 — `xform -m` 이 JO·순서를 처리 |
| F4 | 드라이버 **ry 0 → 270°** (50 프레임마다 67.5°) | 8.9e-15. 보정 회전 커브 프레임 사이 최대 점프 **23.4°**(연속) |
| F5 | **발 자신도 `lyr_glo` 에 키**(tx · ry) | 9.8e-15 — 뮤트 상태로 돌아간다 |
| F6 | `lyr_01.weight = 0.5` + `lyr_glo.weight` 0→1 애니메이션 | 1.2e-14 |
| F7 | `setAttr` 뒤 `setKeyframe -animLayer` **value 없이** | 9.8e-15 — 두 경로 다 역산. 구현은 `value` 명시(F1 경로)로 간다(의도가 분명) |
| F8 | `undoInfo` 청크 하나 → `undo` | 보정 레이어 사라짐, 다른 커브 동일 |
| F9 | Base · `lyr_01` · `lyr_02` · `lyr_glo` 커브 시간·값 | 보정 전후 동일 (F1 안에서 확인) |
| F10 | 성능 | **0.88 ms / (오브젝트 · 프레임)** → 50 ctl × 1000 f ≈ **44 s**. 진행 팝업 필수 |
| F11 | `getAttr(plug, time=t)` 스냅샷 vs `currentTime` 루프 | 값 동일(0.0) 이지만 getAttr 79 ms vs currentTime **23 ms** → `currentTime` 루프 채택 |
| F12 | 발에 **override 레이어**(`lyr_ov`)가 보정 레이어 아래에 있을 때 | 7.1e-15 — additive 가 위에서 더해지므로 성립 |
| F12b | 보정 레이어를 **override** 로 만들어도 | 9.8e-15 — v1 은 additive 고정, override 는 v2 옵션 후보 |
| F13 | 드라이버 키 프레임(0/50/100/150/200) + 양 끝에만 키 | **0.946 유닛 오차** → 희소 모드는 정확하지 않다. 기본에서 제외 |
| F13b | 2 프레임마다 키 | 2.5e-3 |
| F14 | `foot_l.rz` **lock** | `animLayer -e -at` 는 들어가고, `xform` 은 조용히 건너뛰고, `setKeyframe` 은 **0 을 돌려주며 키 없음** — 조용히 틀린다 → **사전 검사로 걸러 경고**(§9) |
| F15 | 발에 **키가 하나도 없는**(정적) 경우 | 1.1e-14 — 멤버만 추가하면 된다 |

### 4.2 설계에 반영된 사실

- **역산은 마야에 맡길 수 있다**(F1·F2·F6·F12): `setKeyframe(obj, at=a, t=f, v=로컬값, animLayer=L)` 하나가 누적 모드 · 가중치 ·
  아래 override 를 전부 처리한다. 우리는 **로컬 목표값**만 만든다.
- **로컬 목표값은 `xform -ws -m` + `getAttr`** 로 얻는다(F3). 수학으로 분해하면 피벗 · `rotateAxis` · JO · 회전 순서를 전부
  우리가 다뤄야 한다. `xform` 이 `setAttr` 로 쓴 값은 다음 `currentTime` 에서 사라지는 미리보기 값이다([[animated-attr-setkeyframe-plus-setattr]]).
- **회전의 동치해 선택은 우리 일**(F4): `xform` 이 준 오일러 `e` 와 `e.alternateSolution()` 각각에 `setToClosestCut(지금 로컬 회전)`
  을 하고 행렬이 같은지 확인한 뒤 가까운 쪽. `setToClosestSolution` 은 쓰지 않는다([[euler-closest-solution-not-equivalent]]).
  기준은 **같은 프레임의 지금(글로벌 켜진) 로컬 회전** — 그래야 보정 레이어 값이 "작은 델타" 로 남아 연속이 된다.
- **희소 키는 안 된다**(F13): 드라이버가 50 프레임마다 키라도 사이 보간은 비선형이라 발이 0.95 유닛 미끄러진다. 매 프레임이 기본.
- **잠긴 채널은 조용히 틀린다**(F14): 세 명령이 전부 예외 없이 지나간다. 실행 전 `getAttr -lock` 으로 걸러 **채널은 건너뛰고 경고**.
- **스냅샷은 `currentTime` 루프**(F11). 두 번 훑기(뮤트 스냅샷 + 쓰기)라 프레임마다 `currentTime` 2회 — 그래도 쓰기 비용(0.9 ms)이 지배적.

---

## 5. 알고리즘

### 5.1 입력

| 입력 | 뜻 | 기본 |
|---|---|---|
| `objects` | 월드를 유지시킬 오브젝트(발) — TSL 목록 | 사용자 리스트업 |
| `layers` | 되돌릴 레이어들(`lyr_glo`). 1개 이상 | 애니메이션 레이어 에디터에서 **선택된 레이어** |
| `start, end` | 정수 구간 | 현재 타임라인 |
| `channels` | `translate` / `rotate` | 둘 다 ON |
| `step` | N 프레임마다 키 | 1 |
| `layer_name` | 새 레이어 이름 | `<layers[0]>_counter`(여러 개면 `counter`), 겹치면 마야 자동 번호 |
| `zero_outside` | `s-1` · `e+1` identity 키 | ON (구간이 애니메이션 전체가 아니면) |
| `skip_unchanged` | 글로벌이 월드를 안 바꾼 오브젝트는 키 없이 통과 | ON (tolerance 1e-6) |
| `select_new` | 끝나면 새 레이어를 에디터에서 선택(마야 관례) | ON |

### 5.2 절차

```
0. 검사(§9): 오브젝트 존재 · 레이어 존재/뮤트 아님/Base 아님 · solo 레이어 없음 · 잠긴 채널 · 비 애니 소스(컨스트레인트 등)
   autoKeyframe 끄기(GUI 함정 §10) · undo 청크 열기 · suspend_refresh
1. 스냅샷(pre):   layers 전부 mute=True
                  for f in range(s, e+1, step): currentTime(f); W_pre[o, f] = getAttr(o.worldMatrix[0])
                  layers mute 복원
   (skip_unchanged) 뮤트 풀고 같은 루프로 W_glo 를 재서 |W_pre - W_glo| < tol 인 오브젝트는 대상에서 뺀다(로그)
2. 새 레이어:     L = animLayer(layer_name)  (additive, 기본 누적 모드)  — 맨 위에 생긴다
                  for o, a in 대상×채널: animLayer(L, e=True, attribute=o.a)
3. 쓰기:          for f in frames: currentTime(f)
                      for o in 대상:
                          ref = getAttr(o.rotate)                       # 연속성 기준(글로벌 켜진 지금 로컬 회전)
                          xform(o, ws=True, m=W_pre[o, f])              # 일반 분해(JO·피벗·순서)
                          t   = xform(o, q=True, t=True)
                          r   = pick_rotation(o, getAttr(o.rotate), ref) # alternateSolution + closestCut
                          for a, v in zip(channels, t + r):
                              setKeyframe(o, at=a, t=f, v=v, animLayer=L)   # 마야가 레이어 기여 역산
   (zero_outside) 각 커브에 setKeyframe t=s-1, e+1, v=0 (step 탄젠트는 불필요 — 값이 0 이면 사이 보간만 남는다)
4. 마무리:        select_new 면 L 만 selected/preferred · autoKeyframe 복원 · 청크 닫기 · 로그 (개수 · 구간 · 초)
```

### 5.3 의사 코드 — `CounterLayerManager.create`

```python
@staticmethod
def create(objects, layers, start, end, channels=("translate", "rotate"), step=1,
           layer_name=None, zero_outside=True, skip_unchanged=True, select_new=True,
           progress=None):
    """-> (keyed_object_count, msg). 실패/거부는 (0, "[Warning] ...")."""
    problems = CounterLayerManager.validate(objects, layers)        # §9. 거부면 (0, msg)
    attrs = resolve_channels(channels)                               # ["tx".."rz"]
    frames = list(range(start, end + 1, step)); if frames[-1] != end: frames.append(end)
    with undo_chunk(), suspend_refresh(), autokey_off():
        pre = sample_world(objects, frames, mute=layers)             # 1
        if skip_unchanged: objects = changed_only(objects, pre, frames)
        lyr = make_layer(layer_name or default_name(layers), objects, attrs)   # 2
        write_counter(lyr, objects, attrs, pre, frames, progress)    # 3 (프레임 루프)
        if zero_outside: zero_keys(lyr, objects, attrs, start - 1, end + 1)
        if select_new: select_only(lyr)
    return (len(objects), msg)
```

`pick_rotation` 은 부록 A 의 코드 그대로(API `MEulerRotation`, 회전 순서는 `getAttr rotateOrder`).

---

## 6. 모듈 설계

```
tools/A00110_animTool_V02/app/core/counter_layer_manager.py     # 신규. maya.cmds + om2, UI 비의존
    class CounterLayerManager:
        list_anim_layers()        -> LayerKeyManager.list_anim_layers() 재사용 (목록 + 선택)
        validate(objects, layers) -> [(level, msg)]  # 거부·경고 분리 (§9)
        create(...)               -> (count, msg)    # §5.3
        _sample_world / _pick_rotation / _write_counter / _zero_keys / _select_only
app/core/__init__.py                                             # export 추가
app/ui/main_window.py
    Bake 카테고리 튜플에 ("Counter Layer", 툴팁, "_build_counter_layer_tab") 추가
    _build_counter_layer_tab()  / on_counter_layer()  / _cl_refresh_layers() (Transfer > Layer 의 레이어 갱신 패턴 재사용)
app/config/version.py                                            # 02.2x + 이력 한 줄
tests/test_counter_layer.py                                      # exp_counter_layer.py 를 회귀로 (§11)
docs/A00110_animTool_V02.md §5.7 Bake 에 "#### Counter Layer", §6 사용 순서                       # 문서
```

- **core 는 위젯을 모른다** — `progress(done, total, message)` 콜백만([[framework-progress-widget]]).
- `undo_chunk` · `suspend_refresh` 는 기존 `Framework/core/maya_undo`, `maya_refresh`.
- 레이어 목록 조회는 `LayerKeyManager.list_anim_layers()` 와 같은 함수를 쓴다 — "선택된 레이어" 전역 질의 함정은
  [[animlayer-no-global-selected-query]].
- `autokey_off()` 컨텍스트는 신규 소형 헬퍼(`autoKeyframe -q -state` 저장 → False → 복원). 다른 탭(Follow · Fill Keys)에도 쓸 수
  있으면 `Framework/core` 로 올리되, v1 은 매니저 안에 둔다.

---

## 7. UI 설계 — `Bake > Counter Layer`

```
┌──────────────────────────────────────────────────────────┐
│ [Counter List]                                           │  ← JUN_mod_tsl_qt_v01 (Bake 탭과 같은 위젯)
│ Select Objects                                           │     월드를 유지시킬 오브젝트(발)
│ ┌ QListWidget ┐                                          │
│ └─────────────┘                                          │
│ ┌ Counter These Layers ──────────────── [Refresh] ┐      │  ← QListWidget + JUN_mod_checkList_qt_v01 (다중 체크)
│ │ [ ] lyr_01    [ ] lyr_02    [v] lyr_glo          │      │     기본 체크 = 에디터에서 선택된 레이어. BaseAnimation 은 목록에서 제외
│ └──────────────────────────────────────────────────┘      │
│ Range (•) Current timeline  ( ) Custom range             │  ← Bake 탭과 동일 라디오
│ Start [ 0 ]   End [ 200 ]                                 │  ← JUN_mod_timeRange_qt_v01 (Custom 일 때 활성)
│ Channels [v] Translate [v] Rotate        Step [ 1 ]      │
│ New layer [ lyr_glo_counter        ]                     │  ← 비우면 기본 이름
│ [v] Zero outside range   [v] Skip unchanged objects      │
│ [v] Select new layer                                     │
│ [ Create Counter Layer ]                                 │
└──────────────────────────────────────────────────────────┘
```

- **문자열은 전부 영어**(전역 규칙 6장). 탭 라벨 `Counter Layer`, 툴팁 "Counter Layer - add a layer that keeps the listed
  objects' world position / rotation as they were without the checked layers (e.g. feet under an animated global control)".
- **진행 팝업**: 오브젝트 × 프레임 > 2,000 이면 `JUN_mod_progress_qt_v01`(단계 "Sampling" 30 · "Keying" 70; F10 비용 기준).
  미만이면 로그 한 줄만.
- **로그 예**: `Counter Layer: lyr_glo_counter - 2 object(s), 12 channel(s), 0-200f (201 keys/ch), without [lyr_glo]  (0.4s)`.
  경고 줄: `Skipped (locked): foot_l_ctl.rz` · `Unchanged (no keys): hand_ctl` · `Note: foot_r_ctl is also keyed in lyr_glo - that
  contribution is countered too`.
- 페이지는 `JUN_mod_fit_tab_page_v01` 을 반환해 탭 높이 자동 맞춤([[framework-tabfit-widget]])에 그대로 얹힌다.

---

## 8. 탭 분류 정합성 — 왜 `Bake` 인가

[[wip-a00110-tab-taxonomy]] 의 기준 "사용자가 무엇을 바꾸려 하는가": 이 기능은 **마야의 평가 결과(월드)를 프레임마다 재서 키로
확정**한다 — 베이크의 정의다. `Transfer`(오브젝트 간 이동) · `Key`(키의 존재) 가 아니다. Merge Layers 계획서가 같은 이유로
`Bake` 에 들어갔으므로 `Bake` 는 **Bake · Merge Layers · Counter Layer** 세 하위 탭이 된다. 첫 하위 탭(대표)은 `Bake` 유지.

---

## 9. 제한 · 거부 조건 (v1)

| 조건 | 처리 |
|---|---|
| 오브젝트 목록 비었음 / 레이어 체크 없음 | 거부 |
| 체크한 레이어가 **뮤트** 상태 | 거부 — 뮤트면 "있기 전" 과 지금이 같아 되돌릴 게 없다 |
| `BaseAnimation` 체크 | 목록에서 제외(뮤트 불가·의미 없음) |
| **solo** 레이어 존재 | 거부 — solo 가 평가를 바꿔 "지금" 이 보이는 결과와 다르다 |
| 오브젝트 채널 **lock** | 그 채널 건너뛰고 경고(F14: 조용히 틀리므로 반드시 사전 검사) |
| 채널 소스가 `animCurve`/`animBlendNode` 가 아님(컨스트레인트 · 익스프레션 · 직접 연결) | 그 오브젝트 건너뛰고 경고 — 키가 결과에 안 나타난다 |
| 레퍼런스 노드 | 허용(레이어·커브는 로컬에 생긴다). 레퍼런스 **커브 편집**이 아니라 새 커브라 [[maya-reference-fcurve-edit-traps]] 와 무관 |
| 오브젝트가 체크한 레이어의 멤버 | 허용 + 로그 노트(F5) |
| 스케일 | v1 미지원. 체크 레이어가 스케일을 바꾸면 "T/R 만 복원됐다" 경고(스냅샷 행렬의 스케일 성분 비교로 감지) |
| 구간 밖 | `zero_outside` 로 identity 키. 끄면 보정 커브가 끝값을 유지해 구간 밖 발이 어긋난다 — 툴팁에 명시 |
| 새 레이어 이후 **순서 변경** | 사용자가 보정 레이어를 다른 레이어 아래로 옮기면 by-layer 회전 누적에서는 결과가 달라질 수 있다 — 문서에 명시 |

---

## 10. 함정 · 리스크

1. **Auto Keyframe(GUI)**: `xform` 은 `setAttr` 이라 autokey 가 켜져 있으면 마야가 **활성 레이어에 자체 키**를 찍는다
   ([[animated-attr-setkeyframe-plus-setattr]] 3항). 실행 중 `autoKeyframe -state false` → 복원. mayapy 엔 autokey 가 없어
   **GUI 에서만 확인 가능**(§11-2 1순위).
2. **`setKeyframe` 반환 0** = 키 안 찍힘(lock · 비 설정 가능). 채널마다 반환값을 세어 로그에 "N keys skipped".
3. **회전 동치해**: `closestSolution` 금지. 기준이 "지금 로컬 회전" 이라 드라이버가 프레임 사이 180° 를 넘으면 점프가 남을 수
   있다 — 그 경우 `Curve > Euler` 로 후처리하라고 로그에 적는다(드라이버 쪽 키가 그만큼 거친 것이 원인).
4. **두 세션 충돌**: Merge Layers 와 같은 파일(`main_window.py` Bake 튜플, `version.py`, `core/__init__.py`, 문서 §5.7)을 건드린다.
   먼저 들어간 쪽 위에 얹고, 버전 이력 줄은 **한 줄만** 추가.
5. **성능**: 0.9 ms / (오브젝트·프레임). 100 컨트롤 × 3000 프레임이면 4.5 분 — 진행 팝업 + `suspend_refresh` 필수. `Step` 은
   정확도를 깨므로(§3) 가속 수단이 아니라 "의도적으로 거친 키" 옵션으로만 설명.
6. **뮤트 토글이 undo 스택에 남는다** — 청크 안이라 한 번에 되돌아간다(F8). 예외가 나도 `finally` 에서 뮤트 복원.
7. **`skip_unchanged` 의 tolerance**: 1e-6 유닛. 글로벌이 미세하게만 움직인 프레임이 있는 오브젝트는 포함된다(옳다).

---

## 11. 검증 계획

### 11-1. `tests/test_counter_layer.py` (mayapy, 헤드리스)

`exp_counter_layer.py` 의 씬 빌더와 F1~F15 를 **매니저 호출**로 바꿔 회귀로 둔다. 추가:
- `zero_outside`: `[50, 150]` 만 보정 → 구간 밖 `[0, 49]` · `[151, 200]` 의 월드가 **보정 전(글로벌 켜진)** 과 같고 안은 뮤트 상태와 같다.
- `skip_unchanged`: 글로벌 밖의 오브젝트를 섞어 넣으면 키가 안 생긴다.
- lock · 컨스트레인트 소스 → 경고 문자열 + 나머지 채널은 정확.
- `step=2` → 오차 보고 ≤ 3e-3, 정수 짝수 프레임은 1e-12.
- 레이어 두 개 동시 되돌리기(`lyr_glo` + `lyr_glo2`).

### 11-2. 마야 GUI (사용자)

1. **Auto Keyframe ON** 상태로 실행 → 활성 레이어에 쓰레기 키가 없고 undo 한 번에 돌아오는지.
2. 실제 리그(발 IK 컨트롤 + 메인 컨트롤) — 뷰포트에서 발이 제자리에 서는지, 보정 레이어 선택 상태.
3. 진행 팝업이 뜨고 끝나는지(50 컨트롤 × 1000 프레임 급).
4. 탭 높이 자동 맞춤에 새 하위 탭이 얹히는지.

---

## 12. 작업 순서

| 단계 | 내용 | 산출물 |
|---|---|---|
| 1 | `git log -3 -- tools/A00110_animTool_V02` 로 Merge Layers 선행 여부 확인, 버전 번호 확정 | — |
| 2 | `counter_layer_manager.py` + `__init__` export | core |
| 3 | `test_counter_layer.py` (exp 를 회귀로 전환, exp 삭제) | tests 통과 |
| 4 | `main_window.py` Bake 튜플 + 빌더 + 핸들러 + 진행 팝업 | UI |
| 5 | `version.py`, 문서 §5.7 · §6, WORKLOG, 포트폴리오([[update-portfolio-on-tool-work]]) | 문서 |
| 6 | 사용자 GUI 확인(§11-2) → 메모리 갱신 | — |

---

## 13. 범위 밖 (v2 후보)

- **Scale 채널**(F12b 가 보여 준 override 보정 레이어 옵션과 함께).
- **분배형(SmartLayer 식)**: 월드 델타를 0 으로 만들지 않고 **속도 비례로 일부만** 상쇄하는 "Blend %" — 발 미끄럼을 허용하되
  자연스럽게. 설계가 전혀 다르다(델타 분배 커브 필요).
- **대상 자동 수집**: 체크한 레이어의 멤버 오브젝트 **자손 중 레이어에 든 것**을 자동으로 리스트에 채우는 버튼.
- **구간 자동**: 체크한 레이어 커브의 첫/끝 키로 Start/End 채우기(Get Sel Range 와 같은 자리).
- 보정 레이어를 Base 로 접기(Merge Layers 와 결합).

---

## 부록 A. 실측 스크립트 요지 (재현용)

전체는 `tools/A00110_animTool_V02/tests/exp_counter_layer.py`. 핵심 두 함수:

```python
def pick_rotation(obj, target_deg, ref_deg):
    """xform 이 돌려준 오일러와 같은 회전 중 ref(지금 로컬 회전)에 가장 가까운 것."""
    order = API_ORDER[cmds.getAttr(obj + ".rotateOrder")]
    e   = om.MEulerRotation(*[math.radians(v) for v in target_deg], order=order)
    ref = om.MEulerRotation(*[math.radians(v) for v in ref_deg],    order=order)
    M = e.asMatrix(); best = None
    for cand in (om.MEulerRotation(e), e.alternateSolution()):
        cand.setToClosestCut(ref)                       # 360 단위 이동만 - 회전 보존
        if not cand.asMatrix().isEquivalent(M, 1e-9):   # 안전망
            continue
        d = sum((cand[i] - ref[i]) ** 2 for i in range(3))
        if best is None or d < best[0]: best = (d, cand)
    return [math.degrees(best[1][i]) for i in range(3)]

def counter_layer(objs, target_world, times, name="lyr_glo_counter"):
    lyr = cmds.animLayer(name)                                   # additive, 맨 위
    for o in objs:
        for a in TR: cmds.animLayer(lyr, e=True, at=o + "." + a)
    for t in times:
        cmds.currentTime(t)
        for o in objs:
            ref_rot = cmds.getAttr(o + ".rotate")[0]
            cmds.xform(o, ws=True, m=target_world[(o, t)])       # 일반 분해(JO, 회전 순서, 피벗)
            tr  = cmds.xform(o, q=True, t=True)
            rot = pick_rotation(o, cmds.getAttr(o + ".rotate")[0], ref_rot)
            for a, v in zip(TR, list(tr) + rot):
                cmds.setKeyframe(o, at=a, t=t, v=v, animLayer=lyr)   # 마야가 레이어 기여를 역산
    return lyr
```

추가 6 항목(F12 · F12b · F13 · F13b · F14 · F15)은 같은 헬퍼로 스크래치에서 돌렸고 §4.1 에 결과만 옮겼다.
스냅샷은 `animLayer -e -mute true` → `currentTime` 루프 → `getAttr worldMatrix[0]` → 뮤트 복원.
