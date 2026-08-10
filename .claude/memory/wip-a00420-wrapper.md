---
name: wip-a00420-wrapper
description: A00420_Wrapper - 커브 가이드로 다른 토폴로지 메시를 래핑 (Wrap3D 대응). TPS 워프 + 표면 투영 2단계
metadata: 
  node_type: memory
  type: project
  originSessionId: f046a986-cc50-4648-8721-90b85713abbb
  modified: 2026-08-10T02:33:54.620Z
---

**신규 툴 (2026-08-10, v01.00)**: `A00420_Wrapper` — 토폴로지가 다른 두 메시에서 소스의 토폴로지는
유지한 채 형태만 타깃과 같아지도록 정점을 옮긴다. Wrap3D 의 `SelectPointPairs` + `Wrapping` 대응이되,
가이드가 낱개 포인트가 아니라 **커브 쌍**이다(얼굴 특징이 선으로 잡히므로).

**Why:** 사용자가 Wrap3D 의 wrap 기능을 커브 가이드 방식으로 원했다. 커브 1개 = 대응 포인트 수십 개라
포인트를 하나씩 찍는 것보다 손질이 크게 준다.

**How to apply:**
- 파이프라인은 **2 단계가 한 짝**이다. ① 커브 대응 → **TPS 워프**(3D 커널 `phi(r)=r`)로 특징을 맞추고,
  ② 타깃 표면 최근접점으로 **반복 투영**(비강체 ICP)해 세부를 붙인다. 투영만 하면 윗입술 정점이 아랫입술로
  끌리고, 워프만 하면 가이드 없는 볼·이마가 안 붙는다. 투영 **변위**(위치가 아님)를 라플라시안 스무딩.
- **`MMeshIntersector.create(node, matrix)` 에 월드 행렬을 넘겨도 `getClosestPoint()` 결과는 오브젝트
  공간**이다(headless 확인). intersector 는 항등으로 만들고 좌표 변환은 numpy 로 통째 처리 →
  행렬 변환이 파이썬 루프 밖으로. 최근접점 20,000 회 **0.6s vs `MFnMesh.getClosestPoint(kWorld)` 4.9s**.
- 커브 쌍의 사고 2 종(진행 **방향** 반대 / 닫힌 커브 **시작점 seam** 불일치)은 두 샘플열을 각자 중심·크기로
  **정규화**한 뒤 정/역 × 시작점 N 후보 중 오차 최소로 자동 해결. `Show Guide Links` 로 눈 확인.
- 컨트롤 포인트가 겹치면 TPS 행렬이 특이해져 폭발 → 격자 반올림으로 미리 병합(`merge_duplicates`).
- 정점 쓰기는 `shape.pnts` 구간 setAttr ([[wip-a00380-meshtool-peak]] 방식), 가이드 커브 생성은
  [[wip-a00400-curvetool]] 재사용. numpy 는 Maya 2022+ 내장(2024=2.2.6), 없으면 UI 가 기능을 막는다.
- 성능: 소스 32,222 / 타깃 39,802 정점, 투영 8 회 → 총 0.98 초.
- **Maya 실사용 확인 완료** (2026-08-10, 사용자 확인). 기본값 Samples 24 / Projection 5 / Relax 0.3 유지.
