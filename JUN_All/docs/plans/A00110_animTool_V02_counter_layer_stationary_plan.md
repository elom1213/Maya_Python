---
title: A00110_animTool_V02 Bake > Counter Layer "Stationary spans only" (글로벌 이동은 살리고 땅 짚은 구간만 고정) 계획서
aliases: [animTool plant hold, 발 고정 레이어, stationary hold, foot plant counter, Counter Layer Stationary]
tags: [plan, maya-python, animtool, anim-layer, bake, counter-animation, foot-plant]
updated: 2026-10-29
---

# A00110_animTool_V02 — `Bake > Counter Layer` **Stationary spans only** 모드 계획서

> **목적**: `CH_n_Global_xx_ctl`(글로벌) 아래 IK 발 컨트롤 `CH_l/r_foot_xx_ctl` 이 additive 레이어에 키가 있고,
> 글로벌만 든 `global_lyr` 가 글로벌을 **이동**시킨다. 글로벌이 없을 때 발은 **땅을 짚는 구간에서 정지**하고 허공에서만
> 움직이는데, 글로벌이 움직이면 그 **정지 구간도 월드에서 미끄러진다.** 원하는 결과는 ① **글로벌 이동으로 발이 결국
> 도달하는 최종 위치는 그대로**, ② **글로벌이 없을 때 정지하던 구간은 월드에서 정지**. `global_lyr` 는 건드리지 않는다.

> [!note] **상태: 계획 (2026-10-29). 실제 씬에서 프로토타입 실측 완료 — 정지 구간 월드 오차 ≤ 2e-6, 구간 끝 최종 위치 오차 0.**
> 모든 수치는 사용자 씬 `00010_cleanup_ZIHAN_00120_tmp.mb` 를 **mayapy(Maya 2024) 로 열어 저장 없이** 잰 값이다(§1-2 · §5).
> 재현 스크립트는 `tools/A00110_animTool_V02/tests/exp_plant_hold_zihan.py`(씬 경로는 상단 상수). 구현 때 회귀 시험으로
> 흡수하고 삭제한다(Counter Layer 때와 같은 절차).
>
> **판단 요약**: 새 탭이 아니라 **v02.26 `Bake > Counter Layer` 탭에 `Hold` 모드를 추가**한다(§3). 같은 입력 · 같은 엔진(뮤트
> 스냅샷 + `xform -m` + `setKeyframe -animLayer` 역산 + 200 프레임 청크)에 "정지 구간 찾기 · 앵커 · 사이 구간 분배" 만 얹는다.

---

## 0. 요약 (1분 버전)

1. **기존 Counter Layer(Everywhere)는 글로벌 이동을 전부 되돌린다** — 발이 처음 자리로 돌아가 버려 "최종 위치 유지" 와 어긋난다.
   이번 요청은 **정지 구간에서만** 되돌리고, 허공 구간이 그 차이를 흡수해 다음 정지 구간(또는 구간 끝)에서 글로벌 위치에 다시 합류하는
   것이다(§2).
2. **방법은 additive 레이어 하나가 맞다**(§2-2). 글로벌 레이어 수정(발이 교대로 땅을 짚어 글로벌이 멈출 틈이 없다) · 로케이터 핀 +
   베이크(레이어 구조 파괴) · override 레이어(아래 편집 상실) · SmartLayer(정지 구간 · 부모 보정 개념 없음) 는 전부 못 쓰거나 비싸다.
3. **알고리즘**(§4): ① `global_lyr` 뮤트 → 발 월드를 프레임마다 스트리밍해 **정지 구간**(연속 프레임 월드 변화 < 톨러런스) 찾기.
   ② 뮤트 해제 → 구간마다 **앵커 프레임**(기본 = 땅에 닿는 첫 프레임)의 월드 포즈를 읽어 **구간 안 목표 = 앵커 포즈**.
   ③ 허공 구간은 앞 구간 끝 델타 → 다음 구간 시작 델타를 **발 자신의 이동량 비례**(기본)로 분배. ④ **구간 양끝(Start · End)은 델타 0**
   → 범위 밖 · 최종 위치가 글로벌 결과와 **정확히** 같다. ⑤ 쓰기는 Counter Layer 와 똑같이 `xform -ws -m` → `setKeyframe -animLayer`.
4. **실측**(§5): 두 발 × 4270–4313 — 정지 구간 월드 오차 **1.7e-6**, 범위 밖 변화 **0**, 4313 최종 위치 차 **0**, `global_lyr` 커브
   불변, 새 레이어 뮤트/삭제 시 원상 복귀, 프레임 간 최대 이동량 보정 전후 **같음**(16.383 — 스파이크 없음). 1000 프레임 × 2 발
   **10.5 s · 파이썬 피크 0.4 MB**.
5. **어디에**: `Bake > Counter Layer` 에 `Hold: ( ) Everywhere  (•) Stationary spans only` 라디오 + 옵션 한 줄(톨러런스 · 최소 길이 ·
   앵커 · 분배) + `Preview Spans` 버튼(§8). 코어는 `CounterLayerManager` 확장(§7). 버전 **v02.29**.

---

## 1. 요청 정리와 실제 씬 관찰

### 1-1. 요청

> `test:ZIHAN:zihan_all` 안 `CH_n_Global_xx_ctl` · `CH_l_foot_xx_ctl` · `CH_r_foot_xx_ctl`, 4270–4313. 발은 IK 컨트롤. 글로벌이
> `global_lyr` 에서 이동하지 않으면 발은 땅을 짚을 때 안 움직이고 허공에서만 움직인다. 글로벌이 이동하면 원래 안 움직이던 구간도
> 월드에서 움직인다. **글로벌 이동으로 위치하게 된 발의 최종 위치는 유지**하되, **글로벌이 없을 때 땅을 짚어 이동하지 않던 구간은
> 이동하지 않도록** 하는 기능. A00110_animTool_V02 에 — 새 탭 또는 기존 탭 확장을 판단. additive 레이어 외 좋은 방법이 있으면 제시.
> SmartLayer 로는 편하게 달성하기 어렵다.

### 1-2. 씬 관찰 (mayapy 2024, 저장 없음)

| 항목 | 관찰 |
|---|---|
| 레이어 스택 | `BaseAnimation` > `AnimLayer1`(additive, 발 · 팔 IK 등 8 오브젝트 135 어트리뷰트, **발 T/R 전부 여기**) > `global_lyr`(additive, **`CH_n_Global_xx_ctl` 10 어트리뷰트만**). 글로벌은 Base 에 커브 없음 — `global_lyr` 만이 글로벌의 유일한 애니메이션 |
| 글로벌 이동 | `translateX` 만 **0 → −21.7185**, 키 4271 · 4312(ease in/out). 그 밖 채널은 0(스케일 1). 4312 이후 −21.7185 유지 |
| 계층 | `… CH_n_Global_xx_ctl > CH_n_Hight_xx_zro > CH_MDU_l_LegSet_xx_grp > CH_l_footIK_xx_zro > CH_l_foot_xx_con > CH_l_foot_xx_ctl`. `con` · `zro` 에 컨스트레인트 · 입력 없음. 발 `Global=1 / Root=0` 스페이스 어트리뷰트도 `AnimLayer1` 멤버(정적) |
| 발 로컬 | `global_lyr` 뮤트 전후 **로컬 T/R 완전히 같음** → 바뀐 것은 부모만. Counter Layer 계획서 §2 와 같은 전제 성립. rotateOrder `zxy`(2) |
| 정지 구간 (글로벌 뮤트, 월드 변화 0) | 왼발 **4277–4282**(6f) · **4297–4304**(8f) · 4316~ (범위 밖). 오른발 **4262–4271**(범위 안은 4270–4271) · **4287–4290**(4f) · **4303–4305**(3f) · 4316~ |
| 정지 구간의 미끄럼 (글로벌 켠 상태) | 왼발 4277–4282: 월드 X **−1.26 → −3.85**(2.6 유닛 미끄럼), 4297–4304: **−15.1 → −19.6**(4.4). 오른발 4287–4290: 1.6, 4303–4305: 1.0. **Y · 회전은 불변**(글로벌이 X 만 이동) |
| 땅 높이 | 발바닥 플랫 정지 때 월드 Y **16.526**(로컬 4.400). 오른발 4303–4305 는 Y 19.718 + 회전(42.7°, −67.9°, −18.7°) 인 채로 정지 — "정지" 는 **포즈 전체**로 판단해야 한다 |
| 톨러런스 민감도 | T 0.01 / R 0.1° 와 0.3 / 1° 는 같은 구간. 0.5 / 2° 부터 왼발 4276(변화 0.44) 이 구간에 흡수, 1.0 / 5° 는 오른발 4272(0.74)도 흡수 |
| 평가 비용 | 이 씬은 `currentTime` + 발 2개 `worldMatrix` 읽기 **3.1 ms/프레임**(장난감 씬 Counter Layer 실측의 3배). 프레임마다 레이어 뮤트 토글은 **16 ms/프레임** → 청크 스냅샷 유지 |

> 범위 4270–4313 안에서 **두 발이 동시에 허공인 프레임**은 4283–4286 · 4291–4296 · 4306–4313 뿐이다 — 글로벌을 "발이 다 떠 있을 때만"
> 움직이게 고치는 대안(§2-2 B)이 왜 안 되는지 보여 준다.

---

## 2. 방법 비교

### 2-1. 지금 있는 Counter Layer 가 못 하는 것

v02.26 `Everywhere` 는 **모든 프레임**에서 발 월드를 `global_lyr` 뮤트 상태로 되돌린다 → 4313 의 발은 글로벌 이동 전 자리(X +21.7)에
남고, 몸만 이동해 다리가 늘어난다. 이번 요청은 **정지 구간 안에서만** 되돌리고 **그 차이를 허공 구간이 흡수**해 최종 위치는 글로벌을 따른다.
수학적으로는 "델타를 어디서 0 으로 두고 어디서 상쇄하느냐" 의 차이이고 쓰기 경로는 같다 — 그래서 **같은 탭의 모드**가 맞다(§3).

### 2-2. 대안 검토

| 방법 | 판정 | 이유 |
|---|---|---|
| **A. additive 보정 레이어 하나** (사용자 제안 = 채택) | **채택** | `global_lyr` · `AnimLayer1` 불변, 뮤트/weight 로 즉시 비교 · 되돌림, undo 한 번, 레이어 편집 가능. 쓰기 경로는 v02.26 그대로 |
| B. `global_lyr` 키를 고쳐 **두 발이 다 떠 있을 때만** 글로벌 이동 | 거부 | 걷기는 발이 교대로 땅을 짚어 틈이 짧다(§1-2 마지막 줄) → 몸이 멈췄다 튀는 이동. 사용자가 `global_lyr` 는 그대로 두기를 원함 |
| C. 로케이터 핀 + 컨스트레인트 + `bakeResults` | 거부 | 월드 로케이터 베이크 → 구간 키 평탄화 → 컨스트레인트 → 되베이크. 노드 생성/삭제 많고 느리며, 베이크 대상 레이어 지정이 없으면 **레이어 스택이 Base 로 접힌다.** 사이 구간 분배도 마야 커브 보간에 맡겨져 제어 불가. 툴 없이 손으로 할 때의 폴백으로만 문서화 |
| D. override 레이어에 월드 포즈 키 | 거부 | 구간 안 아래 레이어 편집이 전부 가려진다. 허공 구간까지 키가 들어가 additive 편집성 상실 |
| E. 리그의 발 "world lock" 어트리뷰트 | 없음 | 이 리그(`Cage`)는 `Global/Root` 스페이스 스위치만 있고 월드 고정이 없다. 둘 다 글로벌 아래라 스위치로는 해결 불가 |
| F. `_SmartLayer` | 참고만 | 레이어 생성 · 오프셋 분배(툴팁의 Linear/Ease 류)는 있으나 **정지 구간 탐지 · 부모 변화 보정** 개념이 없다(사용자 확인). 분배 모드 이름 짓기에만 참고. `.pyc` + 라이선스 → **디컴파일하지 않는다**(v02.26 때와 같은 결정) |

### 2-3. 앵커(정지 구간에서 어느 프레임의 글로벌 위치에 발을 세울까)

구간 안 발 월드는 한 포즈로 고정해야 하므로, 그 포즈를 **글로벌 켠 상태의 어느 프레임에서 읽느냐**가 남는다. 세 가지를 실측했다(§5 B·C).

| 앵커 | 뜻 | 허공이 흡수할 최대 델타(이 씬) | 비고 |
|---|---|---|---|
| **Touchdown**(구간 첫 프레임) — **기본** | 땅에 닿은 자리에 그대로 선다. 들 때 글로벌 기대 위치보다 뒤에 있고 다음 걸음이 따라잡는다 | 4.44 | 모캡 foot-lock 의 "접촉 순간 고정" 과 같은 규칙. 설명이 가장 쉽다 |
| Middle | 구간 가운데 프레임 | **2.33**(절반) | 앞뒤 허공이 반씩 흡수 → 변형 최소. 애니메이터가 고르면 좋은 두 번째 선택 |
| Lift-off(구간 끝 프레임) | 들어 올리는 자리가 글로벌과 같다 | 4.44 | 닿을 때 글로벌보다 앞서 디딘다 |

**구간이 범위 Start/End 에 걸치면 앵커는 그 경계 프레임으로 강제**한다 — 경계에서 델타 0 이어야 범위 밖과 이어진다(§4-4). 범위 전체가
한 구간이면 고정할 것이 없으니 그 오브젝트는 건너뛰고 경고한다(§5 G).

### 2-4. 허공 구간 분배

앞 구간 끝 델타 `D0` → 다음 구간 시작 델타 `D1` 사이를 어떻게 잇나.

| 분배 | 식 | 판정 |
|---|---|---|
| **By travel** — **기본** | `u(f)` = 글로벌 뮤트 상태 발의 **누적 이동 거리 비율**(이동이 0 이면 회전각, 그것도 0 이면 선형) | 발이 원래 안 움직이던 프레임(짧은 공중 멈춤 등)에서는 보정도 안 움직인다 → "정지는 정지" 약속이 허공에서도 유지. 실측 프레임 간 최대 이동량 보정 전후 동일(16.383) |
| Ease | `smoothstep((f−g0)/(g1−g0))` | 매끈하지만 발 속도와 무관하게 분배 |
| Linear | `(f−g0)/(g1−g0)` | 단순, 구간 경계에서 속도 꺾임 |

회전 델타는 쿼터니언 `slerp`. 델타는 **발 자신의 위치를 기준**으로 적용한다(위치 델타 더하기 · 회전 델타 월드 후곱) — 월드 원점 기준 행렬
보간이면 원점에서 100 유닛 떨어진 발이 10° 회전 보간에 17 유닛 호를 그리기 때문이다(§10).

---

## 3. 새 탭이냐 기존 탭 확장이냐 — **기존 `Bake > Counter Layer` 확장**

| 기준 | 판단 |
|---|---|
| 입력 | 오브젝트 리스트 · 되돌릴 레이어 체크 · Range · Channels · New layer · Zero outside · Skip unchanged · Select new — **전부 동일** |
| 엔진 | 레이어 뮤트 스냅샷 · 200 프레임 청크 · `xform -ws -m` · 회전 동치해 · `setKeyframe -animLayer` 역산 · 검증(lock · 컨스트레인트 · Base · 뮤트/solo) — **전부 재사용**. 새 코드는 "구간 찾기 · 앵커 · 델타 보간" 과 목표 행렬 합성만 |
| 사용자 모델 | "Counter Layer = 체크한 레이어가 바꾼 월드를 되돌리는 레이어. **어디서나**(Everywhere) 또는 **서 있던 구간만**(Stationary spans only)". 한 문장으로 두 모드가 설명된다 |
| 탭 수 | 오늘 `Bake` 는 Bake · Merge Layers · Counter Layer 로 이미 셋. 넷째 탭은 분류([[wip-a00110-tab-taxonomy]])를 흐린다 |
| 비용 | UI 라디오 1줄 + 옵션 1줄 + 버튼 1개. 새 탭이면 위젯 20여 개 · 핸들러 7개가 중복 |

따라서 **`Bake > Counter Layer` 에 `Hold` 모드**를 더한다. `Everywhere` 가 기본(v02.26 동작 그대로)이고 `Stationary spans only` 를 고르면
옵션 줄과 `Preview Spans` 가 활성화된다. 기본 레이어 이름은 모드별 `<layer>_counter` / `<layer>_plant`.

---

## 4. 알고리즘

### 4-1. 입력

Counter Layer 와 같다 + `hold`(`"all"` / `"stationary"`), `tol_t`(기본 0.1 유닛), `tol_r`(0.5°), `min_span`(2 프레임), `anchor`
(`"start"` / `"middle"` / `"end"`), `blend`(`"travel"` / `"ease"` / `"linear"`). `step` 은 Stationary 모드에서 **무시(매 프레임)**.

### 4-2. 1 pass — 정지 구간 찾기 (레이어 뮤트, 스트리밍)

```
layers 뮤트
for f in start-1 .. end+1:              # 양끝 한 프레임 여유 = 이동량 분배용
    currentTime(f)
    for o in objs:
        t, q = worldMatrix(o) → 위치 · 쿼터니언
        if 이전 프레임 있음:
            still[o][f] = |t - t_prev| < tol_t and angle(q, q_prev) < tol_r      # 체크된 채널만 본다 (Rotate 끄면 각도 무시)
            travel[o][f] = (|t - t_prev|, angle)                                 # 분배용 1 쌍 / 프레임
        prev[o] = (t, q)
layers 뮤트 해제
spans[o] = still 이 연속으로 참인 프레임 묶음 [s, e] (길이 e-s+1 >= min_span), start..end 로 잘라서
```

메모리: 오브젝트당 **이전 포즈 1개 + 프레임당 double 2개**. 1000 프레임 × 50 오브젝트 = 0.8 MB.

### 4-3. 2 pass — 앵커 포즈와 경계 델타 (레이어 켠 상태, 새 레이어 생성 전)

```
for o, (s, e) in spans:
    a = 경계 규칙(§4-4) 적용한 앵커 프레임
    currentTime(a);  T_a, Q_a = world(o)                      # 구간 안 목표 포즈
    currentTime(s);  T_s, Q_s = world(o);  D_s = (T_a - T_s, Q_s⁻¹·Q_a)   # 구간 시작의 델타 (허공 → 구간 진입용)
    currentTime(e);  T_e, Q_e = world(o);  D_e = (T_a - T_e, Q_e⁻¹·Q_a)   # 구간 끝의 델타 (구간 → 허공 이탈용)
```

메모리: **구간당 포즈 3개** — 구간 수에만 비례(이 씬 1000 프레임에 발당 20개).

### 4-4. 델타 함수와 경계 규칙

```
delta(o, f):
    f 가 어느 구간 안         → 목표 = (T_a, Q_a) 그대로
    앞 구간 끝 g0 / 다음 구간 시작 g1 사이:
        D0 = D_e(앞 구간)   (앞 구간 없으면 g0 = start, D0 = 0)
        D1 = D_s(다음 구간) (다음 구간 없으면 g1 = end,   D1 = 0)      # zero_outside=False 면 D0 유지
        u  = blend(o, g0, g1, f)   (g1 == g0 이면 1)
        D  = (lerp(D0.t, D1.t, u), slerp(D0.q, D1.q, u))
    목표 = (T_on(f) + D.t,  Q_on(f) · D.q)                                # 발 자신의 위치 기준으로 적용
```

- **Start · End 에서 델타 = 0** 이 핵심 계약이다. 구간이 Start/End 에 걸치면 앵커를 그 경계 프레임으로 강제해 같은 효과를 낸다. 그래서
  **범위 밖과 최종 위치가 글로벌 결과와 정확히 같다**(§5 A: 4313 차 0, 범위 밖 변화 0).
- 프로토타입 첫 판은 `end+1` 에서 0 으로 두었더니 4313 에 0.44 가 남고 4314 로 한 프레임 계단이 생겼다 → `end` 로 바꿈. 이 함정은 §10.

### 4-5. 3 pass — 쓰기 (Counter Layer 청크 루프 재사용)

```
lyr = animLayer(name); 멤버 추가
for 청크:
    on = _snapshot(objs, chunk, mute_layers=[lyr])         # Everywhere 는 layers + [lyr] 를 뮤트하던 자리 — 여기선 보정 레이어만
    lyr 뮤트 해제
    for f in chunk: for o: 
        target = compose(on[o][f], delta(o, f))             # MTransformationMatrix: 위치·회전만 바꾸고 스케일/시어는 유지
        ref = getAttr rotate; xform(o, ws, m=target); 로컬 T + _pick_rotation → setKeyframe(... animLayer=lyr)
zero_outside: 커브 노드에 start-1 / end+1 에 0 키 (기존과 동일)
skip_unchanged: 목표 == 글로벌 켠 월드인 오브젝트(구간 없음 · 글로벌이 범위 안에서 안 움직임) → 커브 삭제 + removeAttribute
```

청크 2 이후 보정 레이어 자신을 뮤트하고 스냅샷해야 하는 이유(앞 청크 키 외삽)는 v02.26 과 같다.

---

## 5. 실측 — 실제 씬 프로토타입 (mayapy 2024, 두 발, 저장 없음)

| # | 실행 | 결과 |
|---|---|---|
| A | 4270–4313, anchor **start**, blend **travel** | 구간 탐지 L `[4277-4282] [4297-4304]` · R `[4270-4271] [4287-4290] [4303-4305]`(앵커 4270 강제). **정지 구간 월드 오차 1.71e-6** · **범위 밖 변화 0** · **4313 최종 위치 차 0** · 안쪽 최대 이동 4.436 · 프레임 간 최대 이동량 보정 전 16.383 = 보정 후 16.383 · `global_lyr` 커브 불변 · 새 레이어가 맨 위 · **뮤트하면 글로벌 결과와 동일, 삭제해도 동일** · 커브 12개 × 46 키(4269–4314) · 반 프레임 4279.5 의 앵커 대비 오차 2.8e-14 |
| B | anchor **end** | 구간 오차 1.71e-6 · 안쪽 최대 이동 4.436 · 최대 프레임 간 이동 16.325 |
| C | anchor **middle** | 구간 오차 1.71e-6 · 안쪽 최대 이동 **2.334**(절반) · 16.364 |
| D | blend **ease** | 구간 오차 동일 · 16.383 |
| E | blend **linear** | 구간 오차 동일 · 16.383 |
| F | 범위 **4280–4300**(왼발 4277–4282 가 Start 에 걸침, 4297–4304 가 End 에 걸침) | 구간이 `[4280-4282] [4297-4300]` 로 잘리고 앵커 **4280 · 4300 강제**. 4279→4280 프레임 간 이동 보정 전후 0.5222 동일, 4280 · 4300 · 4301 변화 **0** |
| G | 범위 전체가 정지인 오브젝트(`CH_n_MainGlobal_xx_ctl`)를 섞음 | 구간 `[4270-4313]` 하나 → **건너뛰고 레이어 멤버에서 제외**, 왼발만 키 |
| H | **1000 프레임**(3800–4800) 두 발 | 구간 L 21개 · R 20개, 키 12,012, **탐지 2.0 s + 쓰기 8.1 s = 10.5 s**, 파이썬 피크 메모리 **0.4 MB** |
| I | 비용 | `currentTime` + 발 2개 읽기 3.1 ms/프레임, 프레임마다 뮤트 토글 2회 16 ms/프레임(5배) → 청크 스냅샷 유지 |
| 톨러런스 | 0.01/0.1° · 0.3/1° 동일 구간, 0.5/2° 부터 정착 프레임 흡수 | 기본 **0.1 유닛 / 0.5°**, `Preview Spans` 로 확인 후 조정 |

A 의 프레임별 월드 X(왼발): 4277–4282 **80.165 고정**(보정 전 80.165 → 77.573 미끄럼), 4283–4296 델타 2.50 → 0.02 로 이동량 비례 소멸,
4297–4304 **95.396 고정**(보정 전 95.396 → 90.960), 4305–4312 델타 4.24 → 0.79, **4313 = 94.592 = 보정 전**. 오른발도 같은 모양.

---

## 6. 정확도 계약

| 항목 | 약속 | 근거 |
|---|---|---|
| 정지 구간 안 (정수 프레임) | 앵커 포즈와 **≤ 2e-6**(위치 유닛 · 도) | §5 A–F. 쿼터니언 왕복 오차. v02.26 의 1e-14 보다 크지만 뷰포트 · 익스포트에서 구별 불가 |
| 범위 Start · End · 밖 | **글로벌 결과와 완전히 같다(0)** | 경계 델타 0 규칙 + 커브 0 키 |
| 허공 구간 | 글로벌 결과에서 **최대 \|D\|** 만큼 벗어난다(앵커 start/end 4.44 · middle 2.33). 프레임 간 이동량 분포는 보정 전과 같다 | §5 A–E |
| 프레임 사이(반 프레임) | 보간. 실측 2.8e-14(글로벌 커브가 한 베지어 구간이라 사실상 일치) — 일반적으로는 v02.26 과 같은 ~1e-3 급으로 본다 | §5 A |
| `global_lyr` · 다른 레이어 | 불변 | 커브 키 시각·값 비교 |
| 되돌림 | 보정 레이어 뮤트/삭제/undo 한 번 → 원상 | §5 A |

---

## 7. 모듈 설계

`app/core/counter_layer_manager.py` — `CounterLayerManager` 확장(새 파일 없음).

```python
class CounterLayerManager:
    HOLD_ALL, HOLD_STATIONARY = "all", "stationary"
    ANCHORS = ("start", "middle", "end")          # UI: Touchdown / Middle / Lift-off
    BLENDS  = ("travel", "ease", "linear")        # UI: By travel / Ease / Linear
    STILL_TOL_T, STILL_TOL_R, MIN_SPAN = 0.1, 0.5, 2

    @staticmethod
    def detect_spans(objects, layers, start, end, translate=True, rotate=True,
                     tol_t=None, tol_r=None, min_span=None):
        """layers 뮤트 상태로 정지 구간을 찾는다. → (spans {obj: [[s, e], ...]}, travel {obj: {f: (dist, angle)}})"""

    @staticmethod
    def preview_spans(objects, layers, start, end, **kw):
        """detect_spans 결과를 로그 문장으로. 'CH_l_foot_xx_ctl: 4277-4282 (6f), 4297-4304 (8f)' / 'no stationary span'."""

    @staticmethod
    def create(objects, layers, start, end, translate=True, rotate=True, step=1,
               layer_name=None, zero_outside=True, skip_unchanged=True, select_new=True,
               chunk_frames=None, progress=None,
               hold=HOLD_ALL, tol_t=None, tol_r=None, min_span=None, anchor="start", blend="travel"):
        # hold == "all": 기존 경로 그대로 (스냅샷 뮤트 = layers + [lyr], 목표 = 스냅샷)
        # hold == "stationary": detect_spans → 앵커/경계 델타 → 스냅샷 뮤트 = [lyr], 목표 = compose(스냅샷, delta)
```

- 청크 루프를 `target_for(o, i, f, on_matrix)` 콜러블로 뽑아 두 모드가 같은 쓰기 코드를 쓴다.
- `default_layer_name(layers, hold)` → `<layer>_counter` / `<layer>_plant`(여러 레이어면 `counter` / `plant`).
- 로그(영어): `Counter Layer (stationary): global_lyr_plant - 2 object(s), 12 channel(s), 4270-4313f, spans L 2 / R 3, anchor touchdown,
  blend by travel, without [global_lyr]` + 경고 `No stationary span: hand_ctl (tolerance 0.1 / 0.5 deg) - no keys.` ·
  `Stationary for the whole range: MainGlobal_ctl - nothing to hold.` · 기존 lock/컨스트레인트/스케일 노트.
- **진행 팝업**: 기존 임계(오브젝트 × 프레임 > 2000) 그대로. 단계는 `Detecting`(1 pass) · `Sampling + keying`(3 pass) 둘.

**메모리(1000+ 프레임 요구 유지)**: 1 pass 스트리밍(프레임당 double 2개) · 2 pass 구간당 포즈 3개 · 3 pass 200 프레임 청크 = 구간 길이와
무관한 상한. 실측 2 발 × 1001 프레임 파이썬 피크 0.4 MB. 50 컨트롤 × 1000 프레임 추정 ≈ 2 MB(이동량 0.8 MB + 청크 1.3 MB).

**시간**: 이 프로덕션 씬에서 2 발 × 1000 프레임 10.5 s(탐지 2 s). 리그 평가가 지배하므로 오브젝트가 늘어도 선형보다 완만하게 는다.

---

## 8. UI 설계 — `Bake > Counter Layer` 추가분

```
│ Channels [v] Translate [v] Rotate        Step [ 1 ]                 │  ← Stationary 모드에서는 Step 비활성(매 프레임)
│ Hold  (•) Everywhere   ( ) Stationary spans only                    │  ← 새 라디오 (QButtonGroup)
│   Still tol [ 0.100 ] units  [ 0.50 ] deg   Min span [ 2 ] f       │  ← Stationary 일 때만 활성
│   Anchor [ Touchdown ▾ ]   Blend [ By travel ▾ ]   [ Preview Spans ] │     콤보 2 + 버튼 (로그에 구간 목록)
│ New layer [ global_lyr_plant        ]                               │  ← 플레이스홀더가 모드에 따라 _counter / _plant
```

- 위젯 이름(접두 `cl_` 유지): `cl_hold_grp` · `rb_cl_hold_all` · `rb_cl_hold_still` · `dsb_cl_tol_t` · `dsb_cl_tol_r` · `sb_cl_min_span` ·
  `cb_cl_anchor` · `cb_cl_blend` · `btn_cl_preview`. 모드 토글 핸들러 `_cl_update_hold_mode` 가 옵션 줄 · Step · 이름 플레이스홀더를 바꾼다.
- 툴팁(영어): Hold — "Everywhere: restore the world pose on every frame (undo the checked layers completely). Stationary spans only: keep the
  objects where they stood while they were not moving without the checked layers, and let the moving frames absorb the difference - the final
  position still follows the checked layers." Anchor — "Which frame of a stationary span the object stays at: Touchdown = first frame,
  Lift-off = last, Middle = halfway (smallest detour)." Blend — "How the offset fades between spans: By travel = proportional to the object's own
  motion (still frames stay still), Ease, Linear." Preview Spans — "List the detected stationary spans in the log without creating a layer."
- 라디오 두 개는 `QButtonGroup` 으로 상호 배제([[qt-exclusive-radio-uncheck-ignored]]). `QDoubleSpinBox` 는 `keyboardTracking` 끄기
  ([[qdoublespinbox-keyboard-tracking]]).
- `JUN_mod_fit_tab_page_v01` 반환은 그대로 — 두 줄 늘어난 높이가 탭 맞춤에 반영된다.

---

## 9. 제한 · 거부 · 경고 (v1)

| 상황 | 처리 |
|---|---|
| 레이어 미체크 · Base 체크 · 뮤트/solo · 리스트 비움 · T/R 둘 다 끔 | 기존 Counter Layer 거부 그대로 |
| 오브젝트에 정지 구간 없음 | 경고 + 키 없음(멤버 제외). 톨러런스 안내 |
| 범위 전체가 한 정지 구간 | 경고 + 제외(§5 G) |
| 구간이 Start/End 에 걸침 | 앵커 경계 강제(조용히, 로그 노트) |
| 글로벌이 범위 안에서 안 움직임(목표 == 현재) | `skip_unchanged` → 제외 |
| 잠긴 · 컨스트레인트 채널 | 기존 경고 + 건너뜀. 감지는 월드 행렬이라 영향 없음 |
| 발이 체크한 레이어의 멤버이기도 함 | 기존 노트("그 기여도 함께 보정") |
| Step > 1 | Stationary 모드에선 무시(UI 비활성) |
| 서브프레임 키 · 스케일 | v1 제외(기존과 같음) |

---

## 10. 함정 · 리스크

1. **경계 델타는 `end` 에서 0 이어야 한다.** `end+1` 에서 0 으로 두면 마지막 프레임에 잔여 델타가 남고 한 프레임 계단이 생긴다(프로토타입 첫
   판 0.44). 같은 이유로 Start 쪽도 `start` 에서 0.
2. **델타는 발 위치 기준으로 적용**(위치 더하기 · 회전 월드 후곱). 월드 원점 기준 행렬 보간은 회전 델타가 큰 호를 만든다(§2-4).
3. **감지는 반드시 레이어 뮤트 상태**에서 — 글로벌이 켜진 채로는 어떤 프레임도 정지가 아니다.
4. **정지 판단은 포즈 전체**(위치 + 회전, 체크된 채널 기준). 오른발 4303–4305 처럼 기울어진 채 정지하는 구간이 있다.
5. **프레임마다 뮤트 토글 금지**(16 ms/프레임) — 청크 스냅샷 유지. 청크 2 이후 보정 레이어 자신 뮤트(v02.26 함정) 동일.
6. 쿼터니언 → `setRotation` 왕복으로 구간 오차가 2e-6 — 정수 프레임 1e-14 를 약속하던 Everywhere 와 계약이 다르다. 문서에 그대로 적는다.
7. 커브 찾기는 **긴 어트리뷰트 이름**(`translateX`)으로 대조 — 프로토타입에서 `tx` 로 비교해 0 키가 안 들어간 적이 있다(기존 `_layer_curve` 는 OK).
8. GUI 에서 `xform` 은 setAttr → autoKeyframe 끄고 복원(기존). 실기 확인은 여전히 1순위.
9. 톨러런스 기본 0.1 / 0.5° 는 이 씬 기준. 모캡 정리본은 더 클 수 있다 → `Preview Spans` 로 보고 조정.

---

## 11. 검증 계획

### 11-1. `tests/test_counter_layer.py` 확장 (mayapy, 헤드리스) — T23 ~

합성 씬(`global_ctl > foot_l/r_ctl`, 발 additive 레이어에 "정지 6f – 이동 10f – 정지 8f – 이동" 키, `lyr_glo` 가 글로벌을 X 이동 + 한 케이스는 Y 회전):
- 구간 탐지가 설계한 구간과 일치 · `min_span` 으로 짧은 구간 제외 · 톨러런스 크면 정착 프레임 흡수.
- Stationary 모드: 구간 안 월드 = 앵커 포즈(≤ 1e-5), Start/End/밖 = 글로벌 결과(1e-9), 앵커 3종, 분배 3종(프레임 간 이동량 스파이크 없음),
  글로벌 **회전**(쿼터니언 델타 경로) 케이스, Translate-only / Rotate-only 채널, 구간이 Start/End 에 걸침(앵커 강제), 범위 전체 정지 → 제외 경고,
  구간 없음 → 경고, `zero_outside=False` 끝값 유지, 청크 7 프레임 동일 결과, undo 한 번, Everywhere 결과가 v02.26 과 동일(회귀).
- `preview_spans` 문장 포맷.
- 실제 씬 수치(§5)는 저장소 밖 파일이라 회귀에 넣지 않는다 — `exp_plant_hold_zihan.py` 로 재현.

### 11-2. 오프스크린 UI 스모크

라디오 토글 → 옵션 줄 · Step · 플레이스홀더 전환, `Preview Spans` 가 레이어를 만들지 않음, Create 가 모드별 이름으로 레이어 생성.

### 11-3. 마야 GUI (사용자)

1. 이 씬 4270–4313 두 발, `global_lyr` 체크, Stationary — 뷰포트에서 발이 미끄러지지 않고 4313 이후 글로벌 결과와 같은지.
2. Auto Keyframe ON 상태 · undo 한 번 · 진행 팝업(1000 프레임) · 탭 높이.

---

## 12. 작업 순서

| 단계 | 내용 | 산출물 |
|---|---|---|
| 1 | `git status` 깨끗함 확인, 버전 **02.29** 확정 | — |
| 2 | `CounterLayerManager.detect_spans / preview_spans` + `create(hold=...)` 리팩터(target 콜러블) | core |
| 3 | `test_counter_layer.py` T23~ 추가, `exp_plant_hold_zihan.py` 삭제(흡수) | tests 통과 |
| 4 | `main_window.py` Counter Layer 탭 라디오 · 옵션 줄 · Preview 버튼 · 핸들러 | UI |
| 5 | `version.py`, 가이드 §5.7 Counter Layer(모드 설명 · ASCII 갱신) · §6 · §7, WORKLOG, 포트폴리오 KR/EN, 메모리 | 문서 |
| 6 | 사용자 GUI 확인(§11-3) → 메모리 갱신 | — |

---

## 13. 범위 밖 (v2 후보)

- **사용자가 구간을 직접 지정**(타임라인 선택 범위 · 키 마커) — 탐지가 애매한 모캡용.
- **부분 상쇄 %**(Blend 강도) — 미끄럼을 일부만 남기는 SmartLayer 식 분배.
- **발 자동 수집** — 체크한 레이어 멤버의 자손 중 다른 레이어에 키가 있는 컨트롤을 리스트에 채우기.
- **ON 이동량 기준 분배** 선택지, 회전만/위치만으로 정지 판단하는 별도 스위치.
- 스케일 채널 · 서브프레임.

---

## 부록 A. 재현 스크립트

`tools/A00110_animTool_V02/tests/exp_plant_hold_zihan.py` — 씬 경로 상수 `SCENE` 를 바꿔 mayapy 로 실행하면 §5 A·F·G·H·톨러런스·비용을
`exp_plant_hold.txt` 로 쓴다. 저장은 하지 않는다. 핵심 함수: `detect_spans`(§4-2) · `plant_hold`(§4-3~4-5) · `verify`.
