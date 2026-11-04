---
name: reminder-a00210-data-cleanup-20261118
description: 2026-11-18 이후 첫 세션에서 사용자가 묻지 않아도 먼저 알릴 것 — A00210 데이터 저장소 옛 클론 · 비공개 저장소 · 옛 브랜치 정리 시점
metadata:
  node_type: memory
  type: project
  originSessionId: 3b72b09f-82c3-4ab7-acb4-add90da912f7
  modified: 2026-11-04T03:24:48.663Z
---

**2026-11-18 이후 이 저장소에서 여는 첫 세션: 사용자의 질문이 무엇이든 첫 답에서 먼저 알린다.**
"A00210 데이터 저장소 개편 뒤 2주가 지났다 — 정리할 때다" 와 아래 3가지를 제시하고, 각각 할지 사용자에게 묻는다(혼자 실행 금지).

1. 비공개 저장소 `elom1213/JUN_FileManager_data_Private` → GitHub **Archive**(읽기 전용, 되돌릴 수 있음). 삭제 아님.
2. 옛 클론 3개 삭제: `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_FileManager_data_all\` 의 `A0010_MEU` · `A0020_SA` · `A0030_Src_Rig`
   (지우기 전 각 클론에 미커밋 · 미푸시 변경이 없는지 확인 — 있으면 먼저 알린다). 빈 `JUN_FileManager_data_all` 도.
3. 원격 옛 브랜치 4개 삭제: `JUN_FileManager_data` 의 `master` · `Dnable` · `SA` · `src_rig` (태그 `archive/*` 로 보존돼 있음).
   **다른 PC 도 A00210 v01.45 이상인지** 먼저 묻는다 — 옛 툴은 옛 브랜치에 Push 한다. 원격 변경이라 그 턴에 푸시 요청이 있어야 실행.

보관할 것: 태그 `archive/*`, `0030_maya_python_JUN/_migrate/backup_public.git` · `backup_private.git` 미러, `~/.jun_filemanager/profiles_backup_20261104_v0145`.
절차 · 근거: `JUN_All/docs/plans/A00210_FileManager_data_folders_plan.md` §6 · §7-6 · §7-7, [[wip-a00210-data-folders]].

**Why:** 사용자가 2026-11-04 "2주 뒤에 내가 물어보지 않아도 정리가 필요하다고 말해줄 수 있어?" 라고 요청. 세션 예약(CronCreate)은 세션이 닫히면 사라져 이 메모가 주 수단.
**How to apply:** 오늘 날짜가 2026-11-18 이상이면 첫 답 맨 앞에 알린다. 정리가 끝나거나 사용자가 미루라고 하면 이 메모를 고치거나(새 날짜) 지운다 — 같은 알림을 매 세션 반복하지 않게, 한 번 알린 뒤엔 "알림 완료 YYYY-MM-DD, 사용자 답: …" 을 여기에 적는다.
