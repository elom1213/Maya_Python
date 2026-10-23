---
name: framework-pin-style
description: Framework/qt/pin_style.py — 체크형 Pin(Always on Top) 버튼은 apply_pin_style 로 켜진 동안 연한 빨강 (A00240 · A00220 · A00370, 2026-10-23)
metadata:
  type: project
---

**Pin(Always on Top) 토글 버튼의 "켜짐" 표시는 `Framework/qt/pin_style.py` 의 `apply_pin_style(button)` 한 줄.**
켜진 동안(`:checked`) 연한 빨강 바탕 `#f2a0a0` + 어두운 글자, hover/pressed 도 같은 계열. 사용자 요청(2026-10-23):
"Pinned 모드일 때 버튼이 연한 빨강으로 변해 pin 되었다는 표현". 적용: A00240 v01.26 · A00220 v01.21 · A00370 v01.13.
문서 `JUN_All/docs/Framework_pin_style.md`.

**How to apply:**
- 새 툴에 Pin 버튼을 만들면 `setCheckable(True)` 다음에 `apply_pin_style(self.pin_button)`.
- qss 는 `:checked` 색만 적는다 — padding/border-radius 를 적으면 테마 값을 덮어 버튼 높이가 바뀐다([[wip-a00240-button-colors]]).
- 테마 qss 에는 QPushButton:checked 규칙이 없다(2026-10-23 기준) — 그래서 위젯 qss 로 겹친다. 테마에 넣으면 모든 체크형 버튼이 빨개지므로 넣지 않았다.
- A00210_FileManager v01.37 의 Pin 은 아직 미적용(요청 범위 밖).
- 검증은 offscreen 에서 버튼을 `grab()` 해 가운데 픽셀 색을 읽는다 — 켜짐 `#f2a0a0`, 꺼짐 테마 색.

관련: [[wip-a00220-pin]], [[wip-a00240-button-colors]], [[framework-menubar-widget]]
