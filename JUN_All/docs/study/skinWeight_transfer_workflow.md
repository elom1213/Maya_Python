# 스킨 웨이트 전이 워크플로우 — Shrink Wrap + Blendshape 공간 정렬 학습 노트

> **주제**: 잘 웨이트된 메시 A 의 스킨 웨이트를, 토폴로지가 다른 무(無)웨이트 메시 B 로
> 정확히 옮기기 위한 작업 방식과 그 원리·개선점 정리.
>
> 관련 문서: [A00270_skinMigrate_plan.md](../plans/A00270_skinMigrate_plan.md) (Kangaroo Transfer/Move 1-click 툴 계획)
> 관련 코드: `JUN_All/tools/A00020_move_skineWeightTool/MOD_move_skinWeightTool_v01.py`,
> Kangaroo `...\0020_maya_plugin\0010_kangaroo\scripts\kangarooTabTools\weights.py`

---

## 1. 목적

- **잘 웨이트된 메시 A** 가 있다. 그 웨이트를 **외형은 비슷하나 토폴로지가 다른 메시 B** 로 옮긴다.
- 핵심 동기: B 를 처음부터 손으로 웨이트하지 않고, **검증된 A 의 웨이트를 출발점으로 재사용**해 작업 시간을 줄인다.

---

## 2. 현재 워크플로우 (단계별)

| 단계 | 동작 | 의도 |
|------|------|------|
| 1 | A 에 **Shrink Wrap** 을 걸어 A 표면을 B 표면에 최대한 밀착시킨다 | A 와 B 를 **공간적으로 겹치게** 만든다 |
| 2 | 줄어든(밀착된) 형태를 A 의 **Blendshape 타겟**으로 만든다 | 변형 결과를 재사용 가능한 타겟으로 고정 |
| 3 | 타겟 값을 **1** 로 → 바인드된 A 가 B 표면과 거의 같은 형태가 됨 | A 의 표면 ≈ B 의 표면 |
| 4 | Kangaroo **Transfer** 로 A → B 웨이트 전이 | 공간이 겹친 상태에서 전이 정확도 ↑ |
| 5 | 전이된 B 웨이트를 **섬세하게 다듬기** | 전이 오차 보정 |

---

## 3. 왜 이 방식이 통하는가 (핵심 원리)

### 3-1. "전이 정확도 = 공간 오버랩"
대부분의 웨이트 전이는 **closest point / closest vertex** 대응으로 동작한다(`copySkinWeights` 의
`surfaceAssociation='closestPoint'`, Kangaroo `TransferMode.closestPoint` 동일).
이 방식은 **두 메시의 표면이 같은 위치에 있을수록 정확하고, 어긋날수록 엉뚱한 곳의 웨이트를 끌어온다.**

→ Shrink Wrap 으로 A 를 B 표면에 밀착시킨 것은 곧 **전이 대응 오차를 사전에 최소화**하는 행위다.
이 사전 정렬은 전이 엔진(Kangaroo든 네이티브 `copySkinWeights`든)과 무관하게 항상 이득이다.

### 3-2. Blendshape 를 쓰는 이유 = 비파괴(non-destructive)
바인드된 A 메시를 직접 편집하지 않고 **Blendshape 타겟(값 1)** 으로 형태만 B 에 맞춘다.
- A 의 원본 리그/웨이트가 **그대로 보존**된다 (값 0 으로 즉시 복귀 가능).
- 정렬 형태를 타겟으로 **재사용·미세조정** 가능.
이 비파괴 설계가 이 워크플로우의 가장 잘 된 부분이다.

---

## 4. 우려되는 지점 (여기서 품질이 갈린다)

1. **Shrink Wrap 투영 실패 구역**
   closest-point 투영은 **오목한 곳·얇은 곳·겹치는 부위**(겨드랑이, 손가락 사이, 입 안쪽, 사타구니)에서
   면이 뒤집히거나 핀칭(pinching)된다. 문제는 *그 구역의 웨이트가 가장 부정확하게 전이*된다는 점 —
   즉 **손으로 다듬는 영역 = Shrink Wrap 이 실패한 영역**으로 겹친다.
   → 전이 전에 밀착된 A 의 **법선·뒤집힌 면·자기교차(self-intersection)** 를 점검하면 다듬는 양이 줄어든다.

2. **갭(gap)을 가로지르는 웨이트 누출(bleed)**
   closest-point 는 손가락↔손가락, 팔↔몸통처럼 *가깝지만 분리된* 부위 사이로 웨이트가 새어 든다.
   Shrink Wrap 이 거리를 줄여 완화하지만 완전히 없애지는 못한다.
   → **geodesic(측지) 거리 기반 전이**는 표면을 따라 거리를 재므로 갭을 넘지 않는다.

3. **전이 시점의 포즈**
   전이는 반드시 **바인드 포즈(기본 자세)** 에서 한다. 포즈가 들어간 상태에서 공간 대응을 잡으면 오차가 누적된다.

4. **인플루언스 매핑**
   B 의 skinCluster 는 A 와 **동일한 조인트 집합**을 가져야 하고, 전이는 인덱스가 아니라
   **이름 기준 매핑**(`influenceAssociation`)으로 하는 것이 안전하다.
   토폴로지뿐 아니라 본 이름까지 다르면, 전이 후 **본 A[] → 본 B[] Move** 단계가 추가로 필요하다
   (→ [A00270_skinMigrate_plan.md](../plans/A00270_skinMigrate_plan.md) 가 이 Transfer+Move 를 한 버튼으로 묶는 계획).

---

## 5. 개선 방법

### 5-1. 게임 파이프라인 후처리 (필수)
이 repo 는 게임용이다. 전이 직후 반드시:
- **maxInfluences 제한**(보통 4) → **prune small weights** → **재 normalize**.
- 안 하면 엔진에서 조인트당 영향 초과로 깨지거나 결과가 달라진다.

### 5-2. Geodesic Voxel Bind 를 보조 시작점으로
A 없이 B 에 `bindSkin`(Geodesic Voxel)만 걸어도 의외로 쓸 만한 초기 웨이트가 나온다.
→ "A 에서 전이 → 안 되는 부위만 voxel 결과로 보강" 식으로 두 소스를 섞으면 손작업이 준다.

### 5-3. 전이 직후 스냅샷 저장
`deformerWeights` export 또는 ngSkinTools 레이어로 전이 직후 상태를 저장 →
다듬다 망쳐도 되돌리며 반복 실험할 수 있다.

### 5-4. 노이즈 정리 후 베이크
closest-point 전이는 미세한 웨이트 노이즈를 남긴다. 약한 **Delta Mush / smooth** 후 베이크하면 깔끔하다.

### 5-5. 구역별 분할 전이
전체를 한 번에 전이하지 말고, 문제 구역(손·얼굴)은 버텍스를 미리 선택해 **국소적으로 따로 전이**하면
갭 누출을 원천 차단할 수 있다.

---

## 6. 전이 방식 비교 (참고)

| 방식 | 대응 기준 | 강점 | 약점 |
|------|-----------|------|------|
| **closest point on surface** | 표면 최근접점 | 토폴로지 달라도 동작, 빠름 | 갭 누출, 정렬 어긋나면 부정확 → **본 워크플로우가 정렬로 보완** |
| **closest vertex** | 최근접 버텍스 | 동일/유사 토폴로지에 정확 | 밀도 다르면 앨리어싱 |
| **UV 기반** | UV 좌표 일치 | 토폴로지 무관, 정밀 | 두 메시 UV 가 호환돼야 함 |
| **geodesic** | 표면 따라 측지거리 | **갭 누출 차단** | 비용 큼, 비매니폴드 취약 |

본 워크플로우는 **closest point 의 약점(정렬 의존)을 Shrink Wrap 정렬로 메우는** 전략이다 — 합리적이다.

---

## 7. 코드/툴 연계

- **A00020_move_skineWeightTool** — Kangaroo `transferSkinCluster`(전이) / `moveSkinClusterWeights`(본 이동)를
  이미 코드로 호출 중. 본 워크플로우의 4단계를 자동화할 때 재사용 가능한 검증된 호출부.
- **A00270_skinMigrate (계획)** — Transfer + Move 를 한 버튼으로. 본 문서의 정렬(1~3단계)은 그 툴의
  **Transfer 직전 수동 전처리**에 해당한다. 향후 정렬까지 툴로 흡수할지 검토 여지.

---

## 8. 한 줄 요약

> **"공간 정렬 → 전이 → 정리" 큰 틀은 프로의 방식이 맞다.**
> 개선 여지는 ① Shrink Wrap 실패 구역 사전 점검, ② geodesic 기반 전이로 갭 누출 차단,
> ③ 게임용 후처리(maxInf / prune / normalize) 강제 — 이 셋에 집중하면 다듬는 시간이 눈에 띄게 준다.
