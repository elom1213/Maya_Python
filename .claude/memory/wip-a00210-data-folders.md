---
name: wip-a00210-data-folders
description: A00210 데이터 저장소를 프로파일별 브랜치 → main 하나 + profiles/<data_folder>/ 로, 비공개 저장소도 폐지해 저장소 하나로(공개 노출 결정 대기 · 리허설 검증 · 구현 전)
metadata:
  type: project
---

2026-11-04 계획서 `JUN_All/docs/plans/A00210_FileManager_data_folders_plan.md` (v01.45 예정, **구현 전**).

- 지금: 공개 `elom1213/JUN_FileManager_data` 브랜치 Dnable(프로파일 7개 공유) · SA · src_rig, 비공개 `..._Private` MUE. 클론은 `JUN_FileManager_data` + `JUN_FileManager_data_all/A00x0_*`.
- ★ soundAliance 프로파일은 branch=`Dnable` 인데 store_dir 클론(A0020_SA)은 `SA` 브랜치뿐 — Push 하면 실패할 상태(변환 표로 SA 폴더에 매핑).
- master 의 데이터는 Dnable 에 다 있고 빠진 4개는 일부러 지운 시험 파일 → 폴더 안 만들고 `archive/master` 태그만.
- 리허설(merge -s ours + read-tree --prefix, Dnable 은 git mv): 파일 수 · blob 일치, 기록 보존, 최장 경로 128자 — 계획서 §4 명령 그대로 동작.
- 2026-11-04 Dnable 미반영 82건 푸시(`4690a34`).

- **개정 2026-11-04**: 사용자 요청으로 비공개 저장소 `JUN_FileManager_data_Private` 폐지 → MUE 도 `JUN_FileManager_data/profiles/MUE`(저장소 하나).
  ★ `JUN_FileManager_data` 는 **공개**(API 200) — 옮기면 MUE 공개. 계획서 §0-A: A 저장소 Private 전환 후 기록째(권장) / B 공개 + 스냅숏 / C 공개 + 기록째(비권장). **사용자 결정 대기.**
  리허설: MUE 128=128 blob 0, 기록째면 비공개 커밋 15 개가 들어간다. 비공개 저장소는 삭제 말고 Archive.
- **진행 2026-11-04**: 안 A 확정, 사용자가 저장소 Private 전환(익명 API 404 확인). v01.45 코드 완료(시험 43/43 + 기존 전부),
  `0030_maya_python_JUN/_migrate/`(백업 미러 2 + 리허설 클론 public, push 막힘) 리허설 일치 · 실제 프로파일 10개 읽기 일치.
  **다음 = 계획서 §5 (푸시 요청 턴)** — `_migrate/public` 에서 `git push -u origin main` + archive 태그 + 기본 브랜치. 그 전엔 A00210 을 쓰면 목록이 비고 Wrong branch.
- 함정: 시험 출력에 `—` 가 있으면 cp949 콘솔에서 UnicodeEncodeError → `PYTHONIOENCODING=utf-8`.
- **반영 2026-11-04**: 원격 `main` `8bc1d5b` + `archive/*` 5개, 이 PC 클론 main 전환, 프로파일 3개 store_dir 변경(백업 `profiles_backup_20261104_v0145`), 10개 검증 OK.
  ★ 첫 푸시 시도는 "4가지 작업을 진행해"(푸시 단어 없음)라 자동 권한 확인에서 거부 → "푸시해" 턴에 통과.
  남은 것: 기본 브랜치 main(사용자, gh 미로그인), 1~2주 뒤 §6 Archive · 옛 클론 · 옛 브랜치(사용자 결정). 클론 위치 이동(`JUN_FileManager_data_all/` 아래) 논의 중.
**Why:** 사용자가 브랜치보다 간결한 버전 관리 방식을 요청. GitHub 읽기 권한은 저장소 단위라 비공개 데이터만 저장소로 나눈다.
**How to apply:** 구현은 계획서 §3 부터 순서대로. 원격 변경(§5 · §6 · §7-7)은 푸시 요청 턴에만, 옛 브랜치 삭제는 사용자 결정.
