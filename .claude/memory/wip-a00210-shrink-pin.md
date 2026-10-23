---
name: wip-a00210-shrink-pin
description: "A00210_FileManager v01.37 — 탭 위 헤더 행 Shrink · Pin(272x155, Pin 은 Shrunk 아래), 버튼 왼쪽 anim_area 는 빈 QWidget — 반복 애니메이션은 아직 미정(제안만 함)"
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

**`anim_area` 는 빈 `QWidget`(Expanding, 줄었을 때만 show).** 반복 애니메이션은 사용자가
"어떻게 만들면 좋을지 제시해" 라고만 했고 아직 고르지 않았다. 제안한 안(2026-10-23):
1. 아이콘 모티프 — 폴더에서 기록 카드(썸네일 + 로그 줄)가 올라왔다가 들어가고 동기화 뱃지가 도는 반복
   (추천, A00370 로켓 = 아이콘 과 같은 원칙)
2. 스캔 — 파일 행이 하나씩 채워지고 썸네일이 들어오는 진행 막대
3. Lineage 그래프 — 커밋 점이 선을 따라 올라가며 분기 · 병합
4. Pull/Push — 두 화살표가 서버와 PC 사이를 오가는 동기화
구현은 `RocketAnimWidget`([[wip-a00370-shrink-rocket]]) 꼴(코드 비트맵, start/stop/set_elapsed,
바뀔 때만 update, 테마 글자색 + 아이콘 파랑 `#4c8dff` / `#7fb0ff`)로 바꿔 끼우면 된다.

검증: 오프스크린 PySide6 16항목 + 캡처. **실제 앱 눈 확인 아직.**
