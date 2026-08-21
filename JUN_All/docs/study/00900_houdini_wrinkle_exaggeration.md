# 후디니 의상 주름 강조 (Wrinkle Exaggeration) — 언샤프 마스크 학습 노트

> **주제**: 이미 시뮬레이션이 끝나 **Alembic(.abc) 캐시로 임포트된 의상 메시**에서,
> 주름 때문에 **튀어나온 부분은 더 튀어나오게, 들어간 부분은 더 들어가게** 후처리로 강조하는
> SOP 네트워크 구성과 그 원리.
>
> 도메인: 시뮬레이션 / 후처리 (Houdini SOP / VEX).

---

## 1. 목적

- 이미 베이크된(시뮬 끝난) 의상 캐시를 다시 시뮬하지 않고, **후처리만으로 주름 디테일을 과장**한다.
- 볼록한 주름(튀어나온 곳)은 더 튀어나오게, 오목한 골(들어간 곳)은 더 들어가게 — **양방향 강조**.
- 평평한 면은 건드리지 않고 **주름 영역만** 골라 적용하며, out/in 강조량을 **따로** 조절한다.

---

## 2. 핵심 원리 — 지오메트리 언샤프 마스크 (하이패스 필터)

이미지 샤프닝의 **unsharp mask** 와 같은 발상을 지오메트리에 적용한다.

메시를 한 번 **스무딩(smooth)** 하면 주름 같은 고주파 디테일이 뭉개진 *기준면* 이 된다.
`원본 − 스무딩` 을 하면 **주름 디테일(고주파 성분)만** 남는다 — 튀어나온 곳은 법선 방향으로 양(+),
들어간 곳은 음(−). 이 디테일을 원본에 다시 더해 **증폭**하면 주름이 강조된다.

```
detail  = P_원본 − P_스무딩          // 주름 고주파 성분
along   = dot(detail, N)            // +면 볼록(out), −면 오목(in)
P_결과  = P_원본 + amt * mask * along * N
```

- **마스킹**: `Measure SOP` 의 곡률(curvature)로 주름 영역(높은 곡률)만 1, 평면은 0 → 평면 보존.
- **분리 컨트롤**: `along` 의 부호로 out/in 을 갈라 `out_amount`, `in_amount` 를 따로 적용.
- **법선 투영**: 디테일을 법선 성분(`along`)만 써서 더하면 접선 방향 드리프트 없이 깔끔하다.
- Alembic 은 토폴로지가 고정된 디포밍 캐시이므로 모든 SOP 가 **매 프레임 자동 적용**된다.

---

## 3. 노드 구성 (위에서 아래로)

작업 대상 Alembic 을 임포트한 SOP 네트워크 안에 아래 순서로 연결한다.

| # | 노드 | 설정 | 역할 |
|---|------|------|------|
| 1 | **File / Alembic** SOP | 의상 `.abc` 캐시 로드 | 입력 (디포밍 메시) |
| 2 | **Normal** SOP | Add Normals to = Points | 원본 법선 `@N` 보장 (매 프레임) |
| 3 | **Measure** SOP | Type = **Curvature** | 원본 곡률 `@curvature` 계산 → 주름 위치 검출 |
| 4 | **Attribute Blur** SOP *(선택)* | Attributes = `curvature`, 약하게(1~3회) | 마스크 경계 부드럽게 (이음새 아티팩트 방지) |
| 5 | **Attribute Wrangle** (Point) "store" | 아래 VEX A | 원본 위치·법선 백업 |
| 6 | **Smooth** SOP | Strength / Iterations = **주름 스케일** | 스무딩된 기준면 생성 (`@P` 가 부드러워짐) |
| 7 | **Attribute Wrangle** (Point) "apply" | 아래 VEX B | 주름 증폭 (마스킹 + out/in 분리) |
| 8 | **Normal** SOP | Add Normals to = Points | 변형 후 법선 **재계산** (필수) |
| 9 | **ROP Alembic Output / File Cache** SOP | | 결과 재캐시 |

> **순서 주의**: 곡률(3)과 원본 백업(5)은 반드시 **Smooth(6) 이전**에 둬서
> *날카로운 원본* 기준으로 주름을 검출/보존해야 한다. Smooth 뒤에 측정하면 주름이 이미 뭉개져 있다.

### VEX A — 원본 백업 (노드 5)
```vex
v@origP = @P;
v@origN = normalize(@N);
```

### VEX B — 주름 증폭 (노드 7)
```vex
// 이 시점의 @P 는 Smooth 로 부드러워진 위치, v@origP 는 원본
vector detail = v@origP - @P;                  // 주름 고주파 성분
float  along  = dot(detail, v@origN);          // +볼록(out) / -오목(in)

// 곡률 기반 마스크: 주름 영역(높은 곡률)만 1, 평면은 0
float mask = fit(abs(@curvature), ch("mask_min"), ch("mask_max"), 0, 1);

// out/in 분리 증폭량
float amt = (along >= 0) ? ch("out_amount") : ch("in_amount");

// 원본 기준으로, 법선 방향 디테일만 증폭해서 더함 (접선 드리프트 방지)
@P = v@origP + amt * mask * along * v@origN;
```

**노출 파라미터** (노드 7 Wrangle, 추후 HDA 화 시 그대로 promote):
- `out_amount` — 튀어나온 곳 강조량 (예: 0.5 ~ 1.5)
- `in_amount`  — 들어간 곳 강조량 (예: 0.5 ~ 1.5)
- `mask_min` / `mask_max` — 곡률 마스크 범위 (어느 곡률부터 주름으로 볼지)
- `Smooth` SOP 의 Iterations / Strength — **주름 스케일**(작게 = 미세 주름만, 크게 = 굵은 주름까지)

> **변형**: 법선 투영(`along * N`) 대신 **`@P = v@origP + amt * mask * detail`**(전체 벡터)을
> 쓰면 더 자연스러운 주름이 나올 수 있으나, 접선 방향으로 살짝 밀릴 수 있다.

---

## 4. 검증

1. **마스크 확인** — 노드 4 뒤에 임시 `Color` SOP 로 `curvature`(또는 `mask`)를 색으로 시각화,
   주름선에만 마스크가 잡히는지 확인.
2. **Before / After 비교** — 노드 7(apply Wrangle)을 Bypass 토글하며 뷰포트 비교.
3. **타임라인 스크럽** — 디포밍 전 구간에서 깨짐 / 플리커 없는지 확인. 과하면 `*_amount` 를 낮추거나
   `Smooth` Iterations 조정.
4. **법선 시각화** — 노드 8 이후 노멀이 새 표면을 따라 올바르게 재계산됐는지 확인.
5. **셀프 인터섹션 체크** — `in_amount` 가 크면 깊은 골에서 면이 겹칠 수 있음. 깊은 주름 위주로 점검.

---

## 5. 주의점 (Gotchas)

- 변형 후 **반드시 Normal 재계산**(노드 8). 안 하면 렌더에서 음영이 원본 법선을 따라 어긋난다.
- 마스크 경계가 거칠면 **Attribute Blur(노드 4)** 반복수를 늘려 falloff 를 부드럽게.
- 토폴로지가 프레임마다 바뀌는 캐시라면 `@curvature` / `origP` 가 점 번호에 의존하므로 주의
  (일반적인 의상 디포밍 abc 는 고정 토폴로지라 문제없음).
- 강조량이 과하면 시뮬에 없던 형태가 생겨 **부자연스럽고 시간축 플리커**가 보일 수 있다 — 보수적으로.

---

## 6. 폴백 / 확장

- **Peak SOP + 곡률 가중** *(더 간단)*: `Measure` 로 `@curvature` 를 만든 뒤 `Peak` SOP 의 Distance 를
  곡률 어트리뷰트로 곱해 법선 방향으로 밀기. 셋업은 가장 단순하나 out/in 분리·정밀도가 낮다.
- **멀티 스케일** *(더 정교)*: VEX B 를 블러 반경이 다른 `Smooth` 두 단계(굵은 주름 / 미세 주름)로
  복제해 각각 다른 amount 로 더한다 → 굵은 실루엣 주름과 잔주름을 따로 제어.

---

## 7. 한 줄 요약

> **"스무딩한 기준면과의 차이(= 주름 디테일)를 곡률 마스크로 골라, 법선 방향으로 out/in 따로 증폭한다."**
> 시뮬을 다시 돌리지 않고 `Measure(curvature) → Smooth → Wrangle(언샤프) → Normal 재계산` 만으로,
> Alembic 캐시 전 구간에 주름 강조가 매 프레임 적용된다.
