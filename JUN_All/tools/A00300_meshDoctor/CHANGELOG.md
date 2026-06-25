# A00300_meshDoctor — CHANGELOG

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
