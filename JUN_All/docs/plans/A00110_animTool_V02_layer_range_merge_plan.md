---
title: A00110_animTool_V02 Bake > Merge Layers (구간 한정 애니메이션 레이어 병합) 계획서
aliases: [animTool Merge Layers, 레이어 구간 병합, range merge, layer range merge, LayerMergeManager]
tags: [plan, maya-python, animtool, anim-layer, bake]
updated: 2026-10-29
---

# A00110_animTool_V02 — `Bake > Merge Layers` (구간 한정 레이어 병합) 계획서

> **목적**: 마야 애니메이션 레이어 에디터의 **Merge Layers** 를 **프레임 구간 `[Start, End]` 안에서만** 수행한다.
> 레이어 `a`, `b` 가 `[0, 1000]` 에 키를 갖고 있을 때 `[50, 300]` 만 `a + b => b`(기존 레이어로) 또는
> `a + b => c`(새 레이어로) 병합하고, **구간 밖은 손대지 않는다.** 병합 전후 컨트롤러의 **월드 기준 움직임은 같아야**
> 하며, "합친다"는 **마야 Merge Layers 와 같은 의미**다 — 레이어 모드 · 누적 모드 · 가중치 · 다른 레이어와의 관계를
> 그대로 존중한 결과를 **키로 굽는다.**

> [!note] **상태: 계획 (2026-10-29). 구현 전.**
> 이 문서의 수치는 전부 **mayapy(Maya 2024) 실측**이다(§4). 핵심 가정 **13 항목 전수 통과**(월드 매트릭스
> 정수 프레임 전부 동일 · 구간 밖 반 프레임까지 동일). 실측 스크립트는
> `tools/A00110_animTool_V02/tests/exp_layer_range_merge.py` (부록 A) — 구현 때 그대로 회귀 시험의 뼈대가 된다.
>
> ⚠️ 2026-10-29 시점에 **다른 세션이 `A00110_animTool_V02` 를 작업 중일 수 있다**(탭 높이 자동 맞춤 롤아웃이 그래서
> 이 툴만 건너뛰었다). 구현 시작 전에 `git status` · `git log -3 -- tools/A00110_animTool_V02` 로 충돌을 확인한다.

---

## 0. 요약 (1분 버전)

1. **마야 Merge Layers 의 본체는 `bakeResults` 한 줄이다** (§2). `performAnimLayerMerge.mel` 의 `animLayerMerge()` 는
   새 레이어 `Merged_Layer` 를 만들고
   `bakeResults -destinationLayer Merged_Layer -resolveWithoutLayer a -resolveWithoutLayer b -time ":" <attrs>` 로
   "a, b 를 뺀 스택에서 같은 결과가 나오는 값" 을 새 레이어에 굽고, 소스 레이어를 지운다.
2. **구간 한정 = 같은 `bakeResults` 에 `-time "s:e"` + `-preserveOutsideKeys true`** 를 주고(§5.2), 소스 레이어의
   **구간 안 기여를 없애는 것**(§5.5)과 **경계 처리**(§5.6)를 우리가 한다. 마야는 소스를 통째로 지우니 이 두 가지가
   필요 없었다 — 구간 병합의 난제는 전부 여기에 있다.
3. **정확도 계약**(§3): 정수 프레임은 **모든 프레임에서 완전히 같다**(실측 1e-15). 구간 밖은 **반 프레임까지 같다.**
   구간 안의 **프레임 사이**(0.5 등)는 굽기(bake) 보간이라 달라진다 — **마야 Merge Layers 도 똑같이 달라진다**
   (마야 자체 병합 실측: 정수 프레임 9e-16, 반 프레임 7.9e-4).
4. 세 경로: **A** `=> 기존 레이어 b`, **B** `=> 새 레이어 c`, **C** `b = BaseAnimation`. C 는 `-destinationLayer
   BaseAnimation` 이 **소스 레이어 커브를 통째로 지워 버려**(§4 E4) 못 쓰고, 임시 additive 레이어를 base 바로 위에
   굽고 **값을 합산해 base 커브에 접는** 방식으로 간다(§5.4).
5. 소스 중화: **additive 레이어는 구간 키를 지우고 identity(0 / 스케일 Multiply 는 1) 키를 step 으로**, **override
   레이어는 `weight` 를 구간에서 0 으로 계단 키**(§5.5). override 는 값으로 "없음" 을 표현할 수 없기 때문이다.
6. 위치: `Bake > Merge Layers` 하위 탭(§7 · §8). 코어 `app/core/layer_merge_manager.py` (§6).
7. 비용: `bakeResults -resolveWithoutLayer` 는 **키 하나 ≈ 0.22 ms** — 50 컨트롤러 × 300 채널 × 251 프레임 = 16.5 s,
   1001 프레임 = 66 s. **같은 씬의 마야 자체 Merge Layers 는 139 s** 였다(§4 F8). 진행 팝업이 필요하다.

---

## 1. 요청 정리

| # | 요구 | 비고 |
|---|------|------|
| R1 | 레이어 `a`, `b` 를 **구간 `[s, e]` 안에서만** 병합 | `b` 는 BaseAnimation 일 수도 있다 |
| R2 | `a + b => b` — **기존 레이어**로 | §5.2 (경로 A) · base 면 §5.4 (경로 C) |
| R3 | `a + b => c` — **새 레이어**로 | §5.3 (경로 B) |
| R4 | "합침" = **마야 Merge Layers 가 그대로 재현된** 합침 | 모드(additive/override) · 누적 모드 · weight · 다른 레이어 존중 → `bakeResults -rwl` 그대로 사용 (§2) |
| R5 | 병합 전후 **컨트롤러의 월드 기준 움직임 동일** | §3 정확도 계약 · §11 검증 (worldMatrix 전 프레임 비교) |
| R6 | 구간 **밖**은 그대로 | `-preserveOutsideKeys` + 경계 키 (§5.6) |
| R7 | 레이어는 둘 이상일 수 있다 (`a + b + ... => x`) | 마야와 같이 N 개 소스 허용. 본문은 둘로 설명 |

---

## 2. 마야 Merge Layers 는 실제로 무엇을 하나 — `performAnimLayerMerge.mel` 분석

Maya 2024 `scripts/others/performAnimLayerMerge.mel` 의 `global proc animLayerMerge(string $layers[])`. 우리가 "그대로 재현" 해야
할 대상이므로 단계별로 적는다.

| 단계 | 마야가 하는 일 | 우리 계획에서 |
|------|---------------|---------------|
| 1 | `orderLayers` — 선택 레이어를 **스택 순서**(`animLayer -q -children root`, **첫 원소가 맨 아래**, §4 F1)로 정렬 | 같다 |
| 2 | 첫 레이어가 **BaseAnimation** 이면 임시 override 레이어 `BaseCopy` 를 만들어 base 애니메이션을 `-extractAnimation` 으로 옮기고 그걸 소스로 쓴다 (주석: "does not support BaseAnimation") | **다른 길**로 간다 — 구간 병합에선 extract 가 구간 밖까지 옮겨 버린다 (§5.4) |
| 3 | 소스 레이어들의 **멤버 어트리뷰트 합집합** `animLayer -q -attribute` (키 유무 무관) | additive 소스는 **커브 있는 멤버만**, override 소스는 **모든 멤버**(§4 F4 — 키 없는 override 멤버도 정적 값으로 덮는다) |
| 4 | 새 레이어 `Merged_Layer` 생성. **모드 규칙**: Result=Auto(기본)면 소스 중 override 가 하나라도 있으면 override, 아니면 additive. `scaleAccumulationMode` · `rotationAccumulationMode` 는 소스의 **과반**을 따른다 | 경로 B 에서 같은 규칙 |
| 5 | 위치: 기본(`animLayerMergeUp 1`)은 `moveLayerBefore <가장 아래 소스>` (= 그 자리), 아니면 `moveLayerAfter <가장 위 소스>` | 소스가 **남는** 우리 경우엔 **가장 위 소스 바로 위**(`moveLayerAfter topmost`) — override 결과가 소스를 가리던 것을 그대로 가리도록 (§5.3) |
| 6 | 새 레이어에 어트리뷰트 추가 `animLayer -e -addRelatedKG false -attribute` | 같다 |
| 7 | **새 레이어를 mute** 하고 `bakeResults -simulation false -dic false -removeBakedAttributeFromLayer <delete?> -destinationLayer Merged_Layer [-smart 1 [delta]] -sampleBy 1.0 -oversamplingRate 1 -time ":" -resolveWithoutLayer <각 소스> <attrs>` → unmute | **핵심.** 우리는 `-time "s:e"`, `-preserveOutsideKeys true`, `-removeBakedAttributeFromLayer` 는 쓰지 않는다(소스 키를 우리가 다룬다). 기존 레이어가 대상이면 mute 하지 않는다(§4 E1) |
| 8 | 소스 삭제(`deleteEmptyLayers`) — base 가 있었으면 `Merged_Layer` 를 base 로 extract 하고 삭제. Delete 옵션이 꺼져 있으면 소스를 **mute** | 소스는 남겨야 하므로 **구간 중화**(§5.5) |

옵션 박스(optionVar): `animLayerMergeUp`, `animLayerMergeChilds`(자식 레이어 포함), `animLayerMergeResultType`(Auto/Additive/Override),
`animLayerMergeDeleteLayers`, `animLayerMergeByTime`(Sample by), `animLayerMergeOversamplingRate`, `animLayerMergeSmartBake`,
`animLayerMergeSmartFidelity(+Delta)`.

> [!important] **`bakeResults -resolveWithoutLayer`(rwl) 가 "마야 그대로" 의 전부다.**
> 문서: "when solving for the value to key, it determines the proper value to key on the destination layer to achieve the
> same result as the merged layers." 레이어 모드 · 누적 모드(쿼터니언 by-layer 포함) · weight · 위 레이어의 가림까지
> 마야 C++ 가 푼다. 우리가 수치를 다시 계산하지 않는다 → R4 가 정의상 만족된다. 우리가 보태는 건 **구간**과 **소스 중화**뿐.

---

## 3. 구간 한정이 어려운 이유 — 경계, 그리고 정확도 계약

마야는 소스 레이어를 **지운다.** 구간 병합은 소스가 **구간 밖에 살아 있어야** 하므로 두 문제가 생긴다.

1. **구간 안의 이중 기여.** 대상에 `a+b` 를 구웠는데 `a` 가 구간 안에서 여전히 더해지면 두 배가 된다 → 소스의 구간 안
   기여를 **없애야** 한다. additive 는 값으로(identity), override 는 값으로 안 되고 **weight** 로만 된다(§5.5).
2. **경계의 보간.** `a` 의 키가 0 과 1000 에만 있으면 구간 `[50, 300]` 을 지우고 50 · 300 에 0 을 찍어도, **300 → 1000
   구간의 곡선 모양이 바뀐다**(이웃 키가 300 으로 바뀌었으니). 또 자동 탄젠트는 **이웃 키 위치에 따라** 바뀐다.
   → 구간 바로 밖 `s-1`, `e+1` 에 **모양 보존 키(`setKeyframe -insert`)를 먼저 박고 탄젠트를 `fixed` 로 고정**한다(§5.6).
   그러면 `(…, s-1]` 과 `[e+1, …)` 의 모양은 그대로이고, `(s-1, s)` · `(e, e+1)` 두 **전이 구간**만 새 보간이 된다.

### 정확도 계약 (실측으로 확인, §4)

| 어디서 | 보장 | 실측 |
|--------|------|------|
| **모든 정수 프레임** (구간 안 · 밖 · 경계) | worldMatrix **동일** | max 3.6e-15 |
| 구간 밖 **반 프레임** (`t ≤ s-1`, `t ≥ e+1`) | 동일 | max 3.6e-15 |
| 구간 안 **프레임 사이** (`s ≤ t ≤ e`, 비정수) | 달라진다 — **매 프레임 키의 스플라인 보간** | 수 단위 (키가 듬성한 커브일수록 큼) |
| 전이 구간 `(s-1, s)` · `(e, e+1)` 의 비정수 | 달라진다 | 〃 |

> **마야 Merge Layers 도 똑같다.** 전 구간을 `Sample by 1` 로 굽기 때문에 정수 프레임만 보존된다 — 같은 씬에서 마야 자체
> 병합을 돌려 보면 정수 프레임 9e-16, 반 프레임 7.9e-4(§4 F7). "마야 기능이 그대로 재현된 합침" 의 정확도 수준이 이것이고,
> 우리는 **구간 밖에서는 그보다 낫다**(건드리지 않으니 반 프레임도 같다). `Sample by` 를 0.5 로 낮추면 그만큼 촘촘해지고,
> **Smart bake 는 정확도를 버리는 옵션**이다(§4 E7: 정수 프레임 7.9 차이) — 마야처럼 제공하되 기본 OFF, 로그에 경고.

---

## 4. 사전 검증 — mayapy (Maya 2024) 실측

> 계획서를 쓰기 전에 가정을 전부 코드로 때려 봤다. 아래는 추정이 아니라 측정값이다.
> 씬: `ctl` 큐브, base 9축 키(0 · 120 · 260 · 480 · 700 · 1000), 레이어 `b`(tx ty rz sx · 30 60 180 300 900), `a`(tx ry tz sx ·
> 0 100 200 400 1000), 그 위 비병합 레이어 `top`(tx rx · weight 0.7). 구간 `[50, 300]`. 판정은 **worldMatrix 를
> -3..1003 정수 프레임 전부 + 반 프레임**에서 before/after 비교.

### 4.1 통과한 최종 설계 (13 / 13)

| # | 실험 | 결과 |
|---|------|------|
| F1 | `animLayer -q -children root` 의 **첫 원소가 맨 아래**(제일 먼저 평가) — override 를 첫 자리에 두면 위 additive 가 더해지고(87.99), 끝 자리에 두면 그 값으로 덮는다(77.0) | 확정. `moveLayerBefore X` = X 아래, `moveLayerAfter X` = X 위 |
| F2 | **additive `a + b => b`**: b 경계 insert → `bakeResults -t (50,300) -pok -dl b -rwl a -rwl b` → a 중화(identity step) | 정수 3.6e-15 · 밖 반프레임 3.6e-15 · **0.08 s** |
| F3 | **additive `a + b => new c`**(c 는 a 바로 위, 모드 복사, mute 하고 bake, a·b 중화) | 동일 |
| F4 | **override `a` + additive `b => b`**: a 의 **모든 멤버 plug** 포함(10개 — visibility · 키 없는 rx sx sy sz 도), a 는 `weight` 계단 0 | 정수 8.9e-16 · 밖 0 |
| F5 | **override `a` + `b => new override c`**(마야 Auto 규칙), c 는 a 바로 위, c.weight 밖 0 / 안 1 계단, a weight 0, b identity | 정수 0 · 밖 0 |
| F6 | **`a + Base => Base`**: 임시 additive(by-component · additive scale) `c` 를 **base 바로 위**(children[0] 앞)에 굽고 `base'(f) = base(f) + c(f)` 로 접기, c 삭제, a 중화 | 정수 5.3e-15 · 밖 4.4e-15 · **0.10 s** |
| F7 | (참고) 마야 자체 `animLayerMerge({"a","b"})` 전 구간 | 정수 8.9e-16, **반 프레임 7.9e-4** — 마야도 프레임 사이는 다르다 |
| F8 | 성능 50 ctl × 300 plug: bake **0..1000 = 66.5 s**(그 외 단계 합 0.1 s), **50..300 = 16.5 s**, `-simulation true` 64 s(차이 없음). 같은 씬 **마야 Merge Layers = 139 s** | 키 하나 ≈ 0.22 ms. 진행 팝업 필수 |

### 4.2 깨졌던 가정 — 설계가 바뀐 이유 (전부 교정됨)

| # | 가정 | 실측 | 교정 |
|---|------|------|------|
| E1 | 기존 레이어를 `-destinationLayer` 로 줘도 되나 | **된다.** `-rwl` 목록에 대상 자신(b)을 넣어도 되고 `-preserveOutsideKeys true` 로 구간 밖 키가 산다. 대상을 mute 하면 안 된다(원본 평가에서 빠진다) | 경로 A 성립 |
| E2 | `setKeyframe -insert` 만으로 바깥 모양이 보존되나 | insert 자체는 보존한다(diff 0). 하지만 **이웃 키를 bake 가 덮으면 auto 탄젠트가 다시 계산**된다 | insert 직후 `keyTangent -itt fixed -ott fixed` |
| E3 | 대상에 **없던 채널**이 bake 로 생기면 | 새 커브의 키가 `s..e` 뿐 → **pre/post infinity 로 구간 밖에도 끝값이 샌다**(tz · ry 가 0..49, 301.. 에서 4.5 차이) | bake 뒤 그 커브에 `s-1`, `e+1` identity 키 |
| E4 | `-destinationLayer BaseAnimation` 으로 base 에 바로 굽기 | **소스 레이어의 커브가 통째로 사라진다**(bake-to-base 동작) → 구간 밖 a 기여 소실 | 경로 C = 임시 레이어 + 접기 (F6) |
| E5 | 대상 b 의 **weight 가 1 이 아니면**(0.6) | **틀린다**(구간 안 3.9). `bakeResults` 는 대상 weight 를 되돌려 나누지 않는다. 마야는 늘 **새 레이어(weight 1)** 에 굽기 때문에 이 경우가 없다 | 대상 weight ≠ 1 · 애니메이션이면 **거부**, 새 레이어를 권한다 |
| E6 | 스케일 identity | `scaleAccumulationMode` enum 은 **`Additive(0) : Multiply(1)`**, 기본값 Multiply → identity **1.0**. 0 으로 찍으면 sx 가 깨진다 | `identity = 1.0 if scale and mode == 1 else 0.0` |
| E7 | override 소스는 **키 있는 채널만** 다루면 되나 | **아니다.** override 멤버는 **키가 없어도 정적 값으로 덮고 있다** → weight 를 0 으로 내리면 rx · sx · sy · sz 가 바뀜(43.7) | override 소스는 모든 멤버 plug 를 bake 에 포함(마야와 같음) |
| E8 | Smart bake 로도 정확하나 | 정수 프레임 **7.9 차이**, 키 10개 | 기본 OFF + 경고 |
| E9 | lock 된 레이어 커브 편집 | **조용히 무시된다**(예외 없음) | 사전 `animLayer -q -lock` 검사 후 거부 |
| E10 | base 에 **커브가 없는(정적)** plug 를 접을 때 | `setKeyframe(plug, animLayer=root, t)` 는 커브를 만들지만 **값을 역산해 넣는다**(5.0 → 5.03 / 값 5 지정 → 7 저장). **커브 노드에 직접 `setKeyframe(curve, v=)`** 만 정확하다 | 커브는 그 호출로 만들고, 값은 전부 **커브 노드에 직접** 쓴다 |
| E11 | override 소스의 weight 가 **애니메이션**일 때 | `setKeyframe(weight, insert=True)` 로 경계 키가 생긴다(0.8945) | 정적이면 값 키, 애니메이션이면 insert + fixed |

---

## 5. 알고리즘

### 5.1 공통 전처리

```
입력 : sources = [a, ...], target = 기존 레이어 b | "new", s, e, 옵션(sample_by, smart, listed_only, result_type)
1. 검사 (§9) — 레이어 존재 · 레퍼런스 아님 · lock/mute 아님 · 부모가 root(v1) · 대상 weight == 1 (경로 A) ·
   solo 레이어 없음 · s <= e · Base 가 소스면 target 은 Base 만(v1)
2. plugs = 소스 레이어들의 plug 합집합
      additive 레이어 : 커브가 있는 멤버만        (animLayer -q -attribute  ∩  findCurveForPlug != None)
      override 레이어 : 모든 멤버                  (키 없는 멤버도 정적 override — §4 E7)
   listed_only 면 리스트업한 오브젝트의 plug 로 교집합. 소스 중 override 가 있으면 listed_only 거부(weight 는 레이어 전체).
3. 대상(기존 레이어 b)의 커브마다 경계 키 : setKeyframe -insert s-1, e+1 → keyTangent fixed      (§5.6)
   (대상에 없던 plug 는 bake 뒤 identity 경계 키 — §4 E3)
```

### 5.2 경로 A — `a + b => b` (b 는 BaseAnimation 아님, weight 1)

```
bakeResults(plugs, time=(s, e), sampleBy=sample_by, simulation=False, disableImplicitControl=False,
            preserveOutsideKeys=True, destinationLayer=b, resolveWithoutLayer=[a, ..., b], [smart=True])
for plug in plugs where b had no curve before : b curve 에 (s-1, identity_b), (e+1, identity_b) 키    # additive b 만.
                                                override b 면 없던 멤버가 없다(모든 멤버 포함) / 정적 멤버는 bake 가 키를 만든다
각 소스 a 를 중화 (§5.5)
```

마야와의 차이는 `-time`, `-preserveOutsideKeys`, 대상이 기존 레이어라는 것, 그리고 대상을 **mute 하지 않는** 것 뿐이다.

### 5.3 경로 B — `a + b => c` (새 레이어)

```
c = animLayer("Merged_Layer")                          # 이름은 UI 에서, 중복이면 마야가 번호를 붙인다
모드 (마야 Auto 규칙) : 소스 중 override 가 하나라도 있으면 override, 아니면 additive
누적 모드 : scaleAccumulationMode / rotationAccumulationMode 는 소스의 과반 (동률이면 1)
위치 : animLayer(c, e, parent=root); animLayer(c, e, moveLayerAfter=<스택에서 가장 위인 소스>)   # 가장 위 소스 바로 위
멤버 : animLayer(c, e, attribute=p, addRelatedKG=False) for p in plugs
       (override c 는 멤버가 되는 순간 정적 override 가 생긴다 → bake 가 끝날 때까지 c 를 mute — 마야와 같음)
animLayer(c, e, mute=True); bakeResults(... destinationLayer=c, resolveWithoutLayer=[a, b, ...]); animLayer(c, e, mute=False)
c 의 구간 밖 기여 제거 :
    additive c : 커브마다 (s-1, identity_c), (e+1, identity_c) 키                                  (§4 E3)
    override c : c.weight 를 s-1:0(step) · s:1(step) · e:1(step) · e+1:0 으로 — 밖에서는 통과, 안에서만 덮는다  (§4 F5)
각 소스(a, b 모두)를 중화 (§5.5)
```

### 5.4 경로 C — `a + Base => Base`

`-destinationLayer BaseAnimation` 은 소스 레이어 커브를 지우고(§4 E4), 마야의 `BaseCopy` + `extractAnimation` 은 커브를 **통째로**
옮겨 구간 밖까지 끌고 간다. 그래서 **"임시 레이어에 굽고 base 에 접는다."**

```
c = animLayer("tmpMerge");  scaleAccumulationMode = 0 (Additive);  rotationAccumulationMode = 0 (By Component)
    → base 바로 위에서 c 의 기여는 채널마다 **단순 덧셈**이 된다 (그래야 접을 수 있다)
위치 : animLayer(c, e, parent=root); moveLayerBefore=<children[0]>          # 맨 아래 = base 바로 위
멤버 추가 → mute → bakeResults(plugs, time=(s,e), ..., destinationLayer=c, resolveWithoutLayer=[a, ...])   # Base 는 rwl 에 넣지 않는다
for plug in plugs :
    base_curve = findCurveForPlug(root) 또는 plug 직결 animCurve ([[animlayer-copy-cut-traps]] §4)
    없으면(정적 base) : setKeyframe(plug, animLayer=root, time=s-1) 로 커브만 만들고 그 키 값을 정적 값으로 **직접** 고친다 (§4 E10)
    vals[f] = base_curve.eval(f) + c_curve.eval(f)   for f in s..e        # 자르기 **전에** 떠 둔다
    insert s-1, e+1 (fixed) → cutKey (s, e) → setKeyframe(base_curve, f, vals[f]) 전부
delete c
각 소스 a 를 중화 (§5.5)
```

> c 가 위의 override 레이어에 가려지는 구간이면 bakeResults 의 해가 임의값일 수 있지만, 그 임의값은 base 에 접혀서도
> 똑같이 가려지므로 최종 결과는 변하지 않는다. (그래도 §9 의 "위에 비병합 override" 경고는 띄운다.)

### 5.5 소스 중화 규칙 — "구간 안에서 이 레이어가 없는 것처럼"

| 소스 레이어 | 방법 | 왜 |
|-------------|------|----|
| **additive** (weight 무관, 애니메이션 weight 포함) | 커브마다: insert `s-1`, `e+1`(fixed) → `cutKey (s, e)` → `s` 에 identity 키 **`-ott step`**, `e` 에 identity 키. identity = 0, 스케일이고 `scaleAccumulationMode == Multiply(1)` 이면 1 | 값으로 "기여 없음" 이 표현된다. weight × identity = identity 라 weight 는 안 봐도 된다 |
| **override** | `weight` 를 `s-1`:현재값(step) · `s`:0(step) · `e`:0(step) · `e+1`:현재값 으로 계단 키. weight 가 이미 애니메이션이면 `s-1`, `e+1` 은 insert+fixed | override 는 어떤 값이든 **덮는다** — "없음" 은 weight 0 뿐. 레이어 전체에 걸리므로 `Listed objects only` 와 양립 불가 |
| **BaseAnimation** (소스일 때) | 중화하지 않는다 — v1 에서 Base 가 소스면 대상도 Base(경로 C) | base → 새 레이어는 v2 (§13) |

step 을 쓰는 이유: `s` 와 `e` 사이에 identity 두 키만 남으면 auto 탄젠트가 **이웃(`s-1`)의 값** 때문에 기울어져 구간 안이
0 이 아니게 될 수 있다. `s` 의 out-tangent 가 step 이면 `[s, e)` 가 정확히 identity 로 고정된다.

### 5.6 경계 규칙

- 구간은 **정수 프레임 `s..e`** 로 받는다(`Sample by` 가 1 보다 작으면 그 간격의 샘플이 더 들어간다).
- 손대는 **모든 기존 커브**(대상 · 소스 · base)는 작업 전에 `s-1`, `e+1` 에 `setKeyframe -insert` + `keyTangent fixed`.
  이미 그 시각에 키가 있으면 insert 는 값만 유지하므로 그대로 fixed 만 건다.
- bake 로 **새로 생긴** 커브(대상에 없던 채널 · 새 레이어 c)는 `s-1`, `e+1` 에 **identity** 키(override 레이어는 weight 로).
- 커브 안의 **비정수 키**(`50.5` 등)는 `cutKey (s, e)` 에 함께 지워진다 — 마야 bake 와 같은 결과.
- `s-1`, `e+1` 이 커브의 키 범위 밖이면 insert 는 상수 외삽값으로 키를 만든다 — 그대로 맞다.

### 5.7 의사 코드 — `LayerMergeManager.merge_range`

```python
@staticmethod
def merge_range(sources, target, start, end, sample_by=1.0, smart=False, listed_objects=None,
                result_type="auto", new_name="Merged_Layer", verify=True):
    """sources : 레이어 이름 목록 / target : 레이어 이름 또는 None(새 레이어). (count, msg) 반환."""
    err = LayerMergeManager.validate(sources, target, start, end, listed_objects)
    if err: return (0, err)
    plugs = LayerMergeManager.merge_plugs(sources, listed_objects)
    if verify: before = LayerMergeManager.sample_plugs(plugs, start - 1, end + 1)   # 정수 프레임 값 (검증용)
    with undo_chunk("Merge Layers (range)"), suspend_refresh():
        if target is None:                       path = _merge_to_new(...)        # §5.3
        elif target == root:                     path = _merge_to_base(...)       # §5.4
        else:                                    path = _merge_to_existing(...)   # §5.2
        for layer in sources:  _neutralize(layer, plugs, start, end)             # §5.5
    if verify: dev = LayerMergeManager.compare(before, LayerMergeManager.sample_plugs(...))   # 최대 편차 · 프레임 · plug
    return (len(plugs), "[Merge Layers] {a} + {b} -> {t} : {n} channels, frames {s}-{e}, {sec:.1f}s, max deviation {dev:.2e} @ f{f}")
```

`verify` 는 **정수 프레임의 채널 값**을 bake 전후로 비교한다(월드 매트릭스가 아니라 채널 — 오브젝트 종류에 무관하고, 채널이
같으면 월드도 같다). 300 plug × 251 프레임 getAttr ≈ 1~2 s. 허용치(1e-4)를 넘으면 로그에 **경고**를 띄우되 되돌리지는
않는다(undo 한 번으로 복귀) — 가려진 override(§9) 같은 경우를 사용자가 바로 알게 하는 안전망.

---

## 6. 모듈 설계

| 파일 | 역할 |
|------|------|
| `app/core/layer_merge_manager.py` (**신규**) | `LayerMergeManager` — 정적 메서드, maya.cmds 전용, UI 비의존. `list_layers_ordered()`(스택 순서 + 모드/weight/lock/mute 태그) · `validate()` · `merge_plugs()` · `merge_range()` · 내부 `_prepare_boundary(curve, s, e)` · `_neutralize_additive` · `_gate_weight` · `_bake(dest, sources, plugs, s, e, mute)` · `_fold_into_base` · `sample_plugs` / `compare` |
| `app/core/layer_key_manager.py` (재사용) | `layer_curve(plug, layer, root)` · `plain_curve(plug)` · `root_layer()` · `list_anim_layers()` — 커브 찾기는 전부 여기 것을 쓴다([[animlayer-copy-cut-traps]] §4 함정이 이미 처리돼 있다) |
| `Framework/core/maya_undo.undo_chunk` · `Framework/core/maya_refresh.suspend_refresh` | 한 undo · 굽는 동안 뷰포트 정지 |
| `Framework/qt/MOD_progress_qt` | 레이어 N 개 × 단계 진행 팝업. bake 한 호출은 쪼갤 수 없으니 **plug 묶음(오브젝트별)** 으로 나눠 호출해 진행률을 낸다 — 호출을 나눠도 결과는 같다(채널 독립) |
| `app/ui/main_window.py` | `BAKE_PAGES` 에 `("Merge Layers", ..., "_build_merge_layers_tab")` 추가, `on_ml_*` 핸들러 |
| `tests/test_layer_range_merge.py` (**신규**) | 부록 A 의 실험을 회귀 시험으로 (§11) |

로그 문자열은 **영어**(전역 규칙). 예:
```
[Merge Layers] a + b -> b : 6 channels, frames 50-300, 0.1s, max deviation 3.6e-15 @ f712
[Merge Layers] a (override) : 4 channels without keys were baked as static override values (same as Maya)
[Merge Layers] Warning : Smart bake is on - the result matches the original only within the fidelity tolerance
[Merge Layers] Skipped : target layer 'b' weight is 0.6 (must be 1.0 and not animated). Merge into a new layer instead.
```

---

## 7. UI 설계 — `Bake > Merge Layers`

```
┌ Bake ─────────────────────────────────────────────────────────────┐
│ [ Bake ] [ Merge Layers ]                                          │
│                                                                    │
│ Layers (stack order, top first)                      [ Refresh ]   │
│  ☐ top                       additive   w 0.70                     │
│  ☑ a                         override   w 1.00                     │
│  ☑ b                         additive   w 1.00                     │
│  ☐ BaseAnimation             base                                  │
│                                                                    │
│ Result   (•) Into existing layer  [ b            v ]               │
│          ( ) New layer            [ Merged_Layer     ]  mode: auto │
│                                                                    │
│ Range    Start [ 50   ] End [ 300  ]  [Get Current] [Get Sel Range]│  ← JUN_mod_timeRange_qt_v01 (Layer 탭과 같은 위젯)
│                                                                    │
│ Options  Sample by [ 1.0 ]   ☐ Smart bake   ☑ Verify result        │
│          ☐ Listed objects only (additive sources only)             │
│                                                                    │
│ [            Merge Range            ]                              │
└────────────────────────────────────────────────────────────────────┘
```

- **Layers** 체크 리스트(`JUN_mod_checkList_qt_v01`): 씬 레이어를 **스택 순서(위가 먼저)** 로 나열, 모드 · weight ·
  `locked` / `muted` 태그. 체크한 것이 소스. `Into existing layer` 콤보는 **체크한 레이어 중**에서 고른다(마야처럼 소스
  중 하나가 결과). Base 를 체크하면 콤보는 Base 로 고정되고 New layer 는 비활성(v1, §13).
- **New layer** 이름 기본 `Merged_Layer`(마야와 같음). `mode: auto` 는 마야 Auto 규칙 결과를 미리 보여 준다(additive / override).
- **Range** 는 이 툴의 다른 탭과 같은 `JUN_mod_timeRange_qt_v01` + `Get Current` / `Get Sel Range`([[wip-a00110-get-sel-range]]).
  비워 두면 소스 커브 전체 키 범위 = **마야 전체 병합과 같은 동작**(소스는 identity 키만 남는다).
- **Sample by**(기본 1.0) · **Smart bake**(기본 OFF, 켜면 툴팁과 로그에 "approximate" 경고) — 마야 옵션 박스 항목 그대로.
- **Verify result**(기본 ON) — §5.7. **Listed objects only** — 창 위쪽 공용 리스트의 오브젝트 plug 로 한정, override 소스가
  있으면 거부(§5.5).
- 버튼 하나 `Merge Range`. 결과는 공유 로그창.
- 모든 UI 문자열 · 툴팁 · 로그는 영어. 툴팁에 정확도 계약(§3)을 한 줄로: *"Integer frames are preserved exactly; between
  frames inside the range the result is baked per sample, exactly like Maya's Merge Layers."*

---

## 8. 탭 분류 정합성 — 왜 `Bake` 인가

V02 의 분류 기준은 **"사용자가 무엇을 바꾸려 하는가"** 다(계획서 `A00110_animTool_tab_reorg_plan.md`).

| 후보 | 근거 | 판정 |
|------|------|------|
| **Bake > Merge Layers** | 병합의 본질이 **합성 결과를 키로 굽는 것**이고 마야도 `bakeResults` 로 구현한다. Bake 카테고리는 지금 하위 탭이 하나(Bake)뿐이라 자리가 있다 | **채택** |
| Transfer > Layer | 이미 레이어 사이 **복사/이동**(값 그대로, 재계산 없음)이 있다. 병합은 값을 다시 푸는 다른 성격이라 같은 탭에 섞으면 "Copy/Cut 은 값 그대로, Merge 는 결과 보존" 이 한 화면에 공존해 헷갈린다 | 보류. 단, Layer 탭 설명에 "병합은 Bake > Merge Layers" 한 줄 교차 참조 |
| Key / Timing / Curve | 키 존재 · 시점 · 모양을 다루지 않는다 | 아님 |

---

## 9. 제한 · 거부 조건 (v1)

| 조건 | 처리 | 이유 |
|------|------|------|
| 소스/대상 레이어가 **lock** | 거부 | 커브 편집이 조용히 무시된다(§4 E9) |
| 소스/대상이 **mute** | 거부 | mute 레이어는 지금 결과에 없다 — 합칠 게 없다 |
| 씬에 **solo** 레이어가 있음 | 거부 | 지금 보이는 결과가 solo 결과라 굽는 값이 뒤틀린다 |
| 대상 기존 레이어의 **weight ≠ 1 또는 애니메이션** | 거부 + "merge into a new layer instead" | §4 E5 |
| 레이어가 **레퍼런스 노드** | 거부 | 마야 `autoAnimLayerMerge` 도 거부한다 |
| 소스/대상의 **부모가 root 가 아님**(자식 레이어) | 거부 | 계층 병합(`animLayerMergeChilds`)은 v2 |
| **Base 가 소스**인데 대상이 Base 가 아님 | 거부 | v2 (§13) |
| `Listed objects only` + **override 소스** | 거부 | weight 는 레이어 전체에 걸린다 |
| 대상(또는 새 레이어 위치) **위에 비병합 override 레이어**가 같은 plug 를 덮음 | **경고**(진행은 함) + Verify 가 편차를 보고 | bakeResults 의 해가 가려진다. 마야도 같은 빈틈(MEL 주석 "Workarround, manually mute overriding layers") |
| Smart bake ON | 경고 | 근사 |
| 구간 안에 키가 전혀 없는 소스 | 그냥 진행 | 커브 보간값도 기여다 — bake 가 그대로 담는다 |

---

## 10. 함정 · 리스크

1. **`setKeyframe(plug, animLayer=L, value=V)` 는 역산한다** — 커브에 쓸 값은 전부 **커브 노드**에 쓴다(§4 E10,
   [[wip-a00110-fill-keys]] · [[animlayer-copy-cut-traps]]). 시험 씬도 레이어마다 따로 키한다(번갈아 키하면 값이 엉킨다).
2. **auto 탄젠트는 이웃 키에 반응한다** — insert 뒤 반드시 `fixed`(§4 E2). 사용자가 커브를 `auto` 로 되돌리면 전이 구간
   근처 모양이 조금 바뀔 수 있다 — 문서에 적는다.
3. **override 멤버는 키 없이도 덮는다**(§4 E7) — plug 집합 규칙을 additive/override 로 나눈다. `visibility` 같은 비 transform
   멤버도 들어간다(마야와 같음; 로그에 개수 표시).
4. **`cutKey` 에 `animLayer` 플래그가 없다** — 커브 노드에서 지운다([[animlayer-copy-cut-traps]] §3). 키를 다 지우면 커브 노드가
   사라지므로 `s`, `e` identity 키는 **cut 뒤 바로** 찍는다(그 사이 평가 없음). 안전하게는 identity 키를 먼저 찍고 `(s, e)` 개구간을 지우는 순서.
5. **회전 플립** — bake 결과는 오일러라 180° 근처에서 뒤집힐 수 있다(마야 병합도 같다). 로그에 `Curve > Euler` 안내 한 줄.
6. **성능** — 0.22 ms/키. 100 컨트롤러 × 9축 × 1000 프레임이면 3분대. 진행 팝업 + 로그에 소요 시간. `suspend_refresh` 필수.
   bake 를 오브젝트별로 나눠 호출해 진행률을 내되, **호출 횟수가 늘어도 총 시간은 같은지** 구현 때 한 번 잰다.
7. **undo** — 한 청크. 하지만 `animLayer` 생성/삭제 + bake + 수백 커브 편집이 한 청크라 undo 가 느릴 수 있다. 실측해 보고 로그에 적는다.
8. **Qt 창은 헤드리스에서 잰 값과 다르다** — 새 하위 탭 높이는 마야 GUI 에서 확인([[offscreen-size-needs-theme]]). 이 툴은 tabFit 이
   아직 없고(`_fit_window` grow-only) 다른 세션이 작업 중일 수 있으니 **tabFit 적용은 이 작업에 끼우지 않는다.**

---

## 11. 검증 계획

### 11-1. `tests/test_layer_range_merge.py` (mayapy, 헤드리스) — 부록 A 실험을 회귀로

| 케이스 | 기대 |
|--------|------|
| additive `a + b => b` / `=> new c` | worldMatrix 정수 프레임 전부 동일(1e-9), 밖 반 프레임 동일, 구간 밖 소스 키 보존, 소스 구간 안 identity |
| override `a + b => b` / `=> new c (override)` | 동일. c.weight 게이트가 밖 0 / 안 1. 키 없는 멤버도 bake 됨 |
| `a + Base => Base` | 동일. 임시 레이어 삭제됨. **base 에 커브 없던 정적 plug** 포함 |
| `rotationAccumulationMode = By Layer`(쿼터니언) 소스 · `scaleAccumulationMode = Additive` | 동일 |
| 소스 weight 0.7 / 애니메이션 weight (additive · override) | 동일 |
| 비병합 레이어 `top`(위) · 아래 레이어 | 건드리지 않음(커브 해시 비교) |
| 구간이 커브 키 범위 밖으로 걸침(`[-10, 20]`, `[900, 1100]`) · 구간 안 키 없음 · 비정수 키 | 동일 |
| 소스 3개 | 동일 |
| 거부 조건 §9 전부 | `(0, "[Merge Layers] Skipped : ...")`, 씬 변경 없음 |
| Smart bake | 편차 > 0 이고 로그에 경고 |
| 두 번 연속 병합(`[50,300]` 뒤 `[300, 600]`, 경계 공유) | 동일 — 경계 키가 겹쳐도 깨지지 않는지 |
| 마야 전체 병합과 비교 — 구간 비움 | 우리 결과의 정수 프레임 == 마야 `animLayerMerge` 결과(F7) |
| 성능 | 50 ctl × 300 plug × 251 프레임 로그에 초 단위 기록(절대값 단정 금지) |
| 창 | `MainWindow` 를 오프스크린으로 만들어 `Merge Layers` 탭 위젯 존재 · 기본값 · 영어 문자열 확인([[qapplication-before-maya-standalone]]) |

### 11-2. 마야 GUI (사용자)

1. 요청 그대로의 씬(`a`, `b` 에 0~1000 키, `[50, 300]` 병합)에서 재생 — 눈으로 차이 없음, 그래프 에디터에서 구간 밖 키가 그대로.
2. 레이어 에디터에 결과 레이어 위치(가장 위 소스 바로 위) · 모드 표시.
3. override 소스의 weight 커브(계단)가 레이어 에디터 weight 필드에 어떻게 보이는지.
4. Ctrl+Z 한 번에 복귀, 걸리는 시간.
5. 진행 팝업이 뜨고 닫히는지, 로그 한 줄.

---

## 12. 작업 순서

1. **코어** `app/core/layer_merge_manager.py` — §5 그대로. 부록 A 스크립트의 함수를 정리해 옮기는 수준이다.
2. **시험** `tests/test_layer_range_merge.py` — §11-1. 코어만으로 전부 돌린다(UI 없이).
3. **UI** `Bake > Merge Layers` 탭(§7) + 핸들러 + 공용 리스트 연동(`Listed objects only`).
4. **버전** `app/config/version.py` 02.25 → **02.26**(이력 주석), `CHANGELOG.md`.
5. **문서** `docs/A00110_animTool_V02.md` — §1 개요 6번(Bake)에 한 줄, §5.7 Bake 탭에 하위 탭 설명(정확도 계약 · 거부 조건),
   §6 사용 순서, §7 동작 규칙(`layer_merge_manager.LayerMergeManager.merge_range`), §8 로그 예시. Transfer > Layer 설명에 교차 참조.
   이 계획서 상단 상태 → `[!done]` + "구현하며 달라진 것".
6. **WORKLOG** · 포트폴리오 EN/KR 한 줄 · 메모리 `wip-a00110-layer-range-merge`(+ `MEMORY.md` 한 줄).
7. 사용자 GUI 확인(§11-2) → 푸시는 **그 턴에 요청이 있을 때만**.

---

## 13. 범위 밖 (v2 후보)

- **Base → 새 레이어**(마야 "Down" + base 삭제에 해당): base 커브를 구간에서 identity 로 중화하면 된다(새 레이어가 base 바로 위 additive 일 때).
- **자식 레이어 포함**(`animLayerMergeChilds`) · 계층 어디든.
- **Result type 강제**(Additive / Override) — 마야 옵션 박스의 Result 라디오. v1 은 Auto 만.
- `Oversampling rate` · `Smart bake fidelity delta` — 마야 옵션 박스의 나머지.
- 구간이 소스 전체를 덮어 identity 키만 남은 소스 레이어를 **지우는 옵션**(마야 Delete baked layers 에 해당).
- 비병합 override 가 위를 덮을 때 **그 레이어를 임시 mute 하고 굽는** 보정(마야 MEL 의 TODO).

---

## 부록 A. 실측 스크립트 (재현용)

`tools/A00110_animTool_V02/tests/exp_layer_range_merge.py` — 이 계획서 §4.1 의 F1~F8 을 그대로 돌린다.
`"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" exp_layer_range_merge.py` (약 3분, F8 성능 측정 포함). 결과 13 / 13.
구현 뒤 `test_layer_range_merge.py` 가 이 파일의 역할을 이어받으면 이 파일은 지운다(계획서에서만 참조).

핵심 호출 원형:

```python
# 대상이 기존 레이어 b (경로 A)
for curve in curves_of(b, plugs):                       # 대상에 있던 커브만
    cmds.setKeyframe(curve, insert=True, time=(s-1, s-1)); cmds.keyTangent(curve, e=True, time=(s-1, s-1), itt="fixed", ott="fixed")
    cmds.setKeyframe(curve, insert=True, time=(e+1, e+1)); cmds.keyTangent(curve, e=True, time=(e+1, e+1), itt="fixed", ott="fixed")
cmds.bakeResults(plugs, time=(s, e), sampleBy=1, simulation=False, disableImplicitControl=False,
                 preserveOutsideKeys=True, destinationLayer=b, resolveWithoutLayer=[a, b])
for plug in plugs_that_had_no_curve_on_b:                # §4 E3
    c = curve_of(b, plug); cmds.setKeyframe(c, time=(s-1, s-1), value=identity(plug, b)); cmds.setKeyframe(c, time=(e+1, e+1), value=identity(plug, b))

# additive 소스 중화
for plug, curve in curves_of(a, plugs).items():
    insert_fixed(curve, s-1); insert_fixed(curve, e+1)
    cmds.cutKey(curve, time=(s, e), clear=True)
    idv = 1.0 if plug.split(".")[-1].startswith("scale") and cmds.getAttr(a + ".scaleAccumulationMode") == 1 else 0.0
    cmds.setKeyframe(curve, time=(s, s), value=idv, outTangentType="step"); cmds.setKeyframe(curve, time=(e, e), value=idv)

# override 소스 중화 (weight 게이트)
w = a + ".weight"; cur = cmds.getAttr(w)
cmds.setKeyframe(w, time=(s-1, s-1), value=cur, outTangentType="step"); cmds.setKeyframe(w, time=(s, s), value=0.0, outTangentType="step")
cmds.setKeyframe(w, time=(e, e), value=0.0, outTangentType="step");     cmds.setKeyframe(w, time=(e+1, e+1), value=cur)
```

## 부록 B. 마야 `animLayerMerge` 가 실제로 실행한 명령 (F7 의 evalEcho)

```
bakeResults -simulation false -dic false -removeBakedAttributeFromLayer 1 -destinationLayer Merged_Layer
            -sampleBy 1 -oversamplingRate 1 -time ":" -resolveWithoutLayer b -resolveWithoutLayer a
            ctl.rotateX ctl.rotateY ctl.rotateZ ctl.scaleX ctl.scaleY ctl.scaleZ ctl.translateX ctl.translateY ctl.translateZ ctl.visibility;
```
`-time ":"` 가 "전체 구간" 이고, 우리는 여기에 `"s:e"` 를 넣는 것이 구간 병합의 출발점이다. `-removeBakedAttributeFromLayer 1`
은 소스에서 어트리뷰트를 **통째로** 떼는 옵션이라 구간 병합에는 쓰지 않는다.

관련 메모: [[animlayer-copy-cut-traps]] · [[animlayer-no-global-selected-query]] · [[wip-a00110-layer-key-copy]] ·
[[wip-a00110-graph-focus]](`keyframe -q -name` 은 활성 레이어 커브만) · [[mayapy-headless-verify]] · [[undo-chunk-by-default]]
