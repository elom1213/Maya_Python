# Changelog — A00270_skinMigrate

## v01.02 (2026-08-12)
- **[Fix] 한 트랜스폼에 메시 셰이프가 여럿일 때 엉뚱한 셰이프를 잡던 문제** — `MDagPath.extendToShape()`
  는 **첫 번째 non-intermediate 셰이프**를 고를 뿐이라, blendShape 타겟 셰이프를 같은 트랜스폼에 정리해
  둔 리그·머지/임포트 잔재 씬에서 원하는 셰이프가 아닌 것이 나왔다. 웨이트 API 에 넘기면
  `(kInvalidParameter): Object is incompatible with this method` 로 죽고, 지오메트리 읽기/쓰기는
  **조용히 다른 셰이프**를 만졌다.
- 공용 헬퍼 **`Framework.core.maya_shape`** 로 통일했다 — 셰이프를 추측하지 않고 **디포머가 실제로
  변형하는 셰이프**(`cmds.deformer -q -g`)로 확정한다.
- 네이티브 조인트 이동(`_native_move_columns`)의 dagPath / 버텍스 수를 셰이프 기준으로 잡는다.

## v01.01 (2026-06-29)
- **두 개 탭 구조로 개편** — 레거시 `JUN_PY_move_skinWeightTool_v01_04` 의 원본 UI 를 이식.
  - **Tab 1 "Classic"** — 레거시 원본 2버튼 충실 이식:
    - `Joints to Joints (single mesh)` — 현재 선택한 메시 위에서 From-joint[i] → To-joint[i] 로
      스킨 웨이트 이동 (Kangaroo `moveSkinClusterWeights`, selection 기반).
    - `Meshes to Meshes` — From-mesh[i] → To-mesh[i] 로 skinCluster 전이
      (Kangaroo `transferSkinCluster`, Transfer Mode 적용, 인덱스 쌍 루프).
    - From / To 리스트(TSL) + Transfer Mode 콤보.
  - **Tab 2 "Migrate A -> B"** — 기존 v01.00 통합 마이그레이션(Transfer + Move) 기능 그대로.
  - 로그창을 두 탭이 공유하도록 창 하단으로 이동.
- core(`SkinMigrateManager`)에 `move_joints_in_mesh` / `transfer_meshes` 추가, Kangaroo lazy
  import 를 `_import_kangaroo()` 헬퍼로 공통화 (플러그인 미존재 시 안내 메시지).

## v01.00 (2026-06-24)
- 최초 버전.
- 토폴로지가 다른 두 리깅 메시 A, B 사이의 **스킨 웨이트 전이 + 본 재매핑**을 버튼 한 번으로 처리하는
  in-Maya PySide 툴 (`A00110_animTool` 클론, coral_dark 테마).
- 동작: ① Transfer (A 의 웨이트/본을 B 로) → ② Move (A_joint_i → B_joint_i) → ③ (옵션) 0 가중치 A 본 제거.
  전체가 단일 undo 청크.
- **엔진 2종 (UI 선택)**:
  - `Kangaroo` (기본) — `kangarooTabTools.weights` 의 `transferSkinCluster` + `moveSkinClusterWeights`
    체이닝. 수동 워크플로우와 동일 결과. Kangaroo Builder 플러그인 필요.
  - `Native` — `cmds.copySkinWeights` + `maya.api setWeights`. 플러그인 무의존. Move 는 본 1:1 컬럼 이동.
- 입력: Source Mesh A / Target Mesh B + Joints A(From) / Joints B(To) 리스트(행 순서 zip 매핑).
- 옵션: Transfer Mode(기본 Closest Point), Remove unused influences(ON), Strict joint check(ON),
  Select result mesh.
- 아이콘: `icon/A00270_skinMigrate.png` — 파랑 메시 A → 초록 메시 B 마이그레이션 모티프.
