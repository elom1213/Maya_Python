---
name: wip-a00210-data-folders
description: A00210 데이터 저장소를 프로파일별 브랜치 → main 하나 + profiles/<data_folder>/ 로 바꾸는 계획(리허설 검증됨, 구현 전) · soundAliance 프로파일 branch 어긋남
metadata:
  type: project
---

2026-11-04 계획서 `JUN_All/docs/plans/A00210_FileManager_data_folders_plan.md` (v01.45 예정, **구현 전**).

- 지금: 공개 `elom1213/JUN_FileManager_data` 브랜치 Dnable(프로파일 7개 공유) · SA · src_rig, 비공개 `..._Private` MUE. 클론은 `JUN_FileManager_data` + `JUN_FileManager_data_all/A00x0_*`.
- ★ soundAliance 프로파일은 branch=`Dnable` 인데 store_dir 클론(A0020_SA)은 `SA` 브랜치뿐 — Push 하면 실패할 상태(변환 표로 SA 폴더에 매핑).
- master 의 데이터는 Dnable 에 다 있고 빠진 4개는 일부러 지운 시험 파일 → 폴더 안 만들고 `archive/master` 태그만.
- 리허설(merge -s ours + read-tree --prefix, Dnable 은 git mv): 파일 수 · blob 일치, 기록 보존, 최장 경로 128자 — 계획서 §4 명령 그대로 동작.
- 2026-11-04 Dnable 미반영 82건 푸시(`4690a34`).

**Why:** 사용자가 브랜치보다 간결한 버전 관리 방식을 요청. GitHub 읽기 권한은 저장소 단위라 비공개 데이터만 저장소로 나눈다.
**How to apply:** 구현은 계획서 §3 부터 순서대로. 원격 변경(§5 · §6 · §7-7)은 푸시 요청 턴에만, 옛 브랜치 삭제는 사용자 결정.
