---
name: wip-a00210-sync-tracker
description: "PC 간 C:\\JUN\\JUN_MUE 작업 파일 동기화 추적 — PC 별 매니페스트 json 을 A00210 데이터 저장소로 주고받아 Missing/Outdated/Conflict 감지 (v01.47 1차 구현 · GUI 확인 아직, 2026-11-05)"
metadata:
  node_type: memory
  type: project
  originSessionId: 4c8d14ca-39dd-4d8e-bf56-bc473aa63ef9
  modified: 2026-11-05T00:19:05.766Z
---

2026-11-05 계획서 `JUN_All/docs/plans/A00210_FileManager_sync_tracker_plan.md` (**v01.47 1차 구현 완료 2026-11-05 — 2차 이후는 요청 시**).

- `C:\JUN\JUN_MUE` = 정션 → 이 PC `Desktop/JP/0001_PJ/0023_MUE_original` (git 아님, 381 파일 · 18.6 GB). 정션은 경로만 맞춘다.
- 현행 전송 = **구글 드라이브 수동 업/다운**(사용자 설명). 웹 다운로드는 수정 시각을 안 지킨다 → 판정은 해시 + history.
- 안: `JUN_FileManager_data/profiles/MUE/manifests/<루트>/<COMPUTERNAME>.json`(PC 당 루트당 파일 하나 → git 충돌 없음), A00210 `Sync` 탭.
- 결정(§7): A00210 `Sync` 탭 · **추적 루트 여러 개**(공유 id + PC 별 경로, 루트별 manifests 폴더) · 루트별 Excluded Paths(하위 전부, 공유 + 이 PC 만) · PC 열 동적(현재 2대, 늘어남).
- `.mb` 를 git/LFS 로 올리는 안은 비권장(용량 · LFS 한도).

**Why:** 사용자가 어느 PC 가 최신이고 어느 PC 가 빠졌는지 형상관리처럼 알고 싶어 함. 서버 · 외부 장치는 후순위.
- v01.47: `app/core/sync_settings · sync_manifest · sync_compare`, `app/ui/sync_tab`. 시험 core 53 · ui 52. 실측 320 파일 13.9 GB 첫 스캔 10.9 s, 재스캔 0.03 s.
- 함정: Windows `os.path.normcase` 는 `/` 를 `\` 로 바꾼다 → glob 패턴 비교 전에 다시 `/` 로. 2대에서 한쪽만 가진 파일 = `Only here`(Ahead 아님).
- 오프스크린 시험에서 MainWindow 를 만들되 close 하지 않는다(closeEvent 가 실제 프로파일을 저장).
**How to apply:** 2차(지운 파일 · 자동 스캔 · 별명) · 3차는 사용자가 요청할 때. GUI 실사용(두 PC) 확인 전. 관련 [[wip-a00210-data-folders]].
- v01.48~49 (2026-11-05): Status 열 = 경로 옆, 폴더 줄 = 아래 **모든** 파일 상태(`Missing (1) · Ahead (2)` / `OK`), 처음 접힘(펼침 유지),
  색 Missing #ff8a8a · Outdated #f2d64b · Conflict #7fd8ff · OK #6fcf6f(사용자 지정), Show 기본 전부 체크(키 `sync_show_filters` — 예전 `sync_show` 무시),
  Status 트리 힌트 1075 = 창 2.2 배(717 → 1600), Excluded 왼쪽 게으른 체크 트리 → Exclude Checked. GUI 확인 아직.
