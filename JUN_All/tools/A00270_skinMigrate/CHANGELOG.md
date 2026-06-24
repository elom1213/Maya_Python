# Changelog — A00270_skinMigrate

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
