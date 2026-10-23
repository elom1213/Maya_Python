---
name: wip-a00210-shrink-pin
description: "A00210_FileManager v01.37~38 — 탭 위 헤더 행 Shrink · Pin(272x155, Pin 은 Shrunk 아래) + 줄었을 때 아이콘의 폴더 · 기록 카드 · 동기화 뱃지 애니메이션 무한 반복(app/ui/folder_anim.py)"
metadata:
  node_type: memory
  type: project
  originSessionId: 4a5e2d33-dace-406d-882d-78b18f5530db
  modified: 2026-10-23T01:54:40.371Z
---

A00210_FileManager **v01.37** (2026-10-23) — 탭 위에 헤더 행 추가, [[wip-a00240-shrink-anim]] 과
같은 모양: `Pin`(WindowStaysOnTopHint + `show()` 재호출) · `Shrink`(메뉴 바 · `tabs_scroll` · 로그
`hide()` → `invalidate/activate` → **272 x 155**, `button_grid` 에서 Pin 만 (0,1) ↔ (1,0)).
복원은 `_full_size`. `fit_to_content` 는 첫 showEvent 에서만 돌므로 Pin 의 `show()` 와 충돌 없다.

**v01.38 — `anim_area` = `FolderAnimWidget`(`app/ui/folder_anim.py`).** 제안 4안(아이콘 모티프 /
스캔 진행 / Lineage 그래프 / Pull·Push) 중 사용자가 **1번 아이콘 모티프**를 골랐다.
`RocketAnimWidget`([[wip-a00370-shrink-rocket]]) 과 같은 꼴(start / stop / set_elapsed / is_running,
상태가 바뀔 때만 update). 30 x 32 칸 비트맵, 칸 크기 `min(h // 32, w // 30)` → 155px 창에서 4.
- 그리는 순서: 폴더 뒷판 + 탭(`#2f6bd6`) → 기록 카드(몸체 = 테마 글자색, `CARD_PARTS` 썸네일 · 제목 ·
  작업자 · 로그 2줄은 아이콘 파랑, 단계 0/1/2) → 폴더 앞판(`#4c8dff`, 카드를 가린다) → 9x9 뱃지
  (`BADGE_RING` 24칸 시계 방향, 8칸 호 둘이 `ARC_STEP` 2칸씩 12프레임에 한 바퀴).
- 한 바퀴 **3.0초**: 올라옴 0.5(ease-out, 카드 y 24 → 3칸) → 채움 0.6/0.9/1.2 → 동기화 1.4~2.2 →
  내려감 0.5(ease-in) → 쉼 2.7~3.0. 속도를 바꾸려면 클래스 상수 `RISE / FILL_* / SYNC_* / LOWER` 만.

검증: 오프스크린 PySide6 27항목 + 시각별 캡처 6장. **실제 앱 눈 확인 아직.**
