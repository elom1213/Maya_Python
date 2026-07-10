# A00300_meshDoctor — CHANGELOG

## v01.03 (2026-07-10)
- **`Target Meshes` 리스트 선택 → 씬 선택 연동**: 리스트에서 항목을 고르면 씬의 해당 메시도
  선택된다(공용 `Framework/qt/MOD_tsl_qt_v01.py` 의 `_on_selection_changed` 와 같은 동작).
  표시 이름이 아니라 **항목에 보관된 UUID** 로 노드를 되찾으므로 이름이 겹쳐도 정확히 그 메시가 잡힌다.
  선택이 비면(Remove/Clear 직후) 씬 선택은 건드리지 않고, 씬에서 사라진 항목은 로그로 안내한다.

## v01.02 (2026-07-07)
- **`Target Meshes` 리스트 신규**(Add Selected / Remove / Clear, 항목을 UUID 로 보관) +
  `Diagnose Listed` 가 리스트 전체를 진단. 리스트가 비면 현재 선택을 진단(하위호환).
- 결과를 **Summary 테이블**(`Mesh` / `Status` / `Issues`, 상태별 색)로 요약하고,
  행을 클릭하면 그 메시의 전체 리포트를 아래 로그창에 표시.

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
