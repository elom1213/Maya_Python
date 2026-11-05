---
name: wip-a00210-sync-tracker
description: "PC 간 C:\\JUN\\JUN_MUE 작업 파일 동기화 추적 — PC 별 매니페스트 json 을 A00210 데이터 저장소로 주고받아 Missing/Outdated/Conflict 감지 (계획 확정 · 구현 보류, 2026-11-05)"
metadata:
  node_type: memory
  type: project
  originSessionId: 4c8d14ca-39dd-4d8e-bf56-bc473aa63ef9
  modified: 2026-11-05T00:19:05.766Z
---

2026-11-05 계획서 `JUN_All/docs/plans/A00210_FileManager_sync_tracker_plan.md` (**계획 확정 · 구현 보류 — 사용자가 착수를 따로 요청할 때 1차부터**).

- `C:\JUN\JUN_MUE` = 정션 → 이 PC `Desktop/JP/0001_PJ/0023_MUE_original` (git 아님, 381 파일 · 18.6 GB). 정션은 경로만 맞춘다.
- 현행 전송 = **구글 드라이브 수동 업/다운**(사용자 설명). 웹 다운로드는 수정 시각을 안 지킨다 → 판정은 해시 + history.
- 안: `JUN_FileManager_data/profiles/MUE/manifests/<COMPUTERNAME>.json`(PC 당 파일 하나 → git 충돌 없음), A00210 `Sync` 탭.
- 결정(§7): A00210 `Sync` 탭 · **추적 루트 여러 개**(공유 id + PC 별 경로, 루트별 manifests 폴더) · 루트별 Excluded Paths(하위 전부, 공유 + 이 PC 만) · PC 열 동적(현재 2대, 늘어남).
- `.mb` 를 git/LFS 로 올리는 안은 비권장(용량 · LFS 한도).

**Why:** 사용자가 어느 PC 가 최신이고 어느 PC 가 빠졌는지 형상관리처럼 알고 싶어 함. 서버 · 외부 장치는 후순위.
**How to apply:** 구현은 계획서 §5 1차부터. 구현은 보류 — 요청 전엔 착수 말 것. 관련 [[wip-a00210-data-folders]].
