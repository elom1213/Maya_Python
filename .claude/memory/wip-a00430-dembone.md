---
name: wip-a00430-dembone
description: "A00430_DemBone — EA Dem Bones(스키닝 분해) 마야 이식 툴, v01.03 구현 완료(4모드)"
metadata: 
  node_type: memory
  type: project
  originSessionId: cbf34923-4abc-4c62-9078-e552b18afd5c
  modified: 2026-08-13T02:06:39.028Z
---

**A00430_DemBone** — EA SEED **Dem Bones**(BSD-3, SIGGRAPH Asia 2012 논문 구현)의 마야 이식.
**v01.03 완료**(2026-08-13): Solve Weights / Solve Transforms / Refine / **Decompose** 4탭, PySide(arch B).
문서: `JUN_All/docs/A00430_DemBone.md`(가이드) · `docs/plans/A00430_DemBone_plan.md` ·
`docs/plans/A00430_DemBone_v0103_ref_requirements.md`(§9 에 원본 대비 변경점).

- **`ref/` 는 git 추적 제외**(`.gitignore`, 47MB). 툴은 런타임에 `ref/` 를 읽거나 import 하지 않는다 —
  알고리즘만 읽고 파이썬으로 새로 작성. 사용자 방침: **ref 의 코드가 필요하면 ref 밖에 새로 만들거나 복사**.
- 4모드 = 원본 CLI: `--nTransIters=0` / `--nWeightsIters=0` / `compute()` / `-b N`.
- 상대 변환 `M = bindPreMatrix[j] @ joint.worldMatrix(t)` — 마야 skinCluster 와 같은 식.
  코어 전체가 **마야 행벡터 규약**(원본 Eigen 은 열벡터).
- mayapy: **numpy 있음 / scipy 없음** → ConvexLS(NNLS+합=1)와 라플라시안 스무딩(자코비 반복)을 직접 구현.

**실측으로 잡은 함정 4개** (전부 가이드 §9 에 기록):
1. 본 솔브 공분산은 **4×4**. 무게중심을 나눌 질량은 `qpT(3,3)`(공분산 자신)이지 `uuT[j,j]` 가 아니다.
   웨이트 합 1 + affinity 0 이면 우연히 같아 안 드러나고, Translation Affinity 를 켜면 무너진다(460%→1.4%).
2. **락 조인트는 다시 굽지도 말 것**(샘플 프레임으로만 리샘플되어 사이 키 소실).
3. (v01.03) 원본의 **분할 씨앗 1링(4~5개)은 너무 작다** — 새 본이 다음 라벨 확산에서 먹히고 솎여 사라져
   20k 버텍스에 본 20개를 요청해도 2개에서 멈춘다 → 클러스터 크기의 1/8 로 키움.
4. (v01.03) **라벨 확산 우선순위를 절대 오차로 두면 한 본만 편든다** — 힙이 하나라 오차 작은 본이 먼저
   다 훑고, 나중 본은 이웃이 점령돼 못 자란다(`[1,1,431,359]`) → **`E - E.min(axis=1)`(최선 대비 열위)** 로 변경.

성능(20,100 버텍스): 웨이트 16.5s(오차 0.19%) / 트랜스폼 3.0s / Decompose 본 20개 32.6s(1.02%).
씬 취득 12ms/frame. 초기화는 **프레임만 솎는다**(`Init Frames`) — 버텍스를 솎으면 인접 그래프가 끊겨
라벨 확산이 깨진다.

미완: `ref/data/Decomposition_*.fbx`(원본 exe 결과) 대조 검증은 아직 안 했다.

관련: [[mayapy-headless-verify]], [[extendtoshape-picks-wrong-shape]], [[prefer-pyside-for-new-tools]],
[[undo-chunk-by-default]], [[qdoublespinbox-keyboard-tracking]]
