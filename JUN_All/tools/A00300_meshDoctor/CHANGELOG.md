# A00300_meshDoctor — CHANGELOG

## v01.01 (2026-06-25)
- **`zero_area_faces` 판정을 형상품질(등주지수 q) 기반으로 재작업**: 절대 면적/Maya `zeroArea()` 의존을
  줄여 진짜 슬라이버(케이스 A: 정점 일직선/겹침, Transfer 깨짐)와 작지만 멀쩡한 면(케이스 B: 오탐)을
  구분한다. `q < QUALITY_EPS(1e-2)` 또는 `area < AREA_DEGEN(1e-10)` 이면 `zero_area_faces`(FAIL),
  작지만 형상 정상이면 신규 `tiny_faces`(INFO)로 강등. 임계치 `AREA_TINY(1e-5)`는 polyCleanup zeroGeom 과 정렬.
- 로그(JSON/TXT)에 플래그된 면마다 **실제 면적·품질값**(`f<idx> a=<area> q=<q>`)을 기록 → A/B 육안 구분.
- `Select Zero-Area Faces` 헬퍼도 동일 기준(슬라이버만)으로 정렬.
- **로그창 `Clear Log` 버튼 추가**.

## v01.00 (2026-06-25)
- 최초 버전.
- 선택 메시 읽기 전용 진단: NaN/Inf 정점, 떠돌이(stray) 정점, bounding box 팽창,
  intermediate(orig) shape, 잔여 construction history, non-manifold edge/vertex,
  lamina/holed/concave/zero-area 페이스, zero-length edge, 겹친(미병합) 정점,
  border edge, UV 셋/누락 UV, 음수 스케일, skinCluster 정보.
- 진단 로그를 `0020_out/` 에 JSON + 사람이 읽는 TXT 로 출력.
- 안전 원클릭 수정(Undo 가능): Delete History(deformer-safe), Merge Vertices,
  Conform Normals, polyCleanup(scan→fix), Snap NaN/Stray Verts.
- 문제 컴포넌트 선택 헬퍼: non-manifold edges / zero-area faces / stray·NaN verts.
