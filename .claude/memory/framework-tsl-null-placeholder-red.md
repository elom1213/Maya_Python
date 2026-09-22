---
name: framework-tsl-null-placeholder-red
description: "공용 TSL 은 (Null) 자리표시 행을 빨갛게 칠한다(테마별 공용 빨강). 직접 addItems 로 채운 리스트는 mark_null_items() 를 직접 부른다"
metadata:
  node_type: memory
  type: project
---

공용 TSL(`Framework/qt/MOD_tsl_qt_v01.py`)은 항목 텍스트가 **`(Null)`** 이면 그 행을
**빨간 글씨 + 툴팁**으로 그린다(2026-09-22, 사용자 요청). 채우는 모든 경로
(`set_items` · `append_unique` · 요약 해제)에서 자동이라 **툴은 아무것도 하지 않는다**.

**Why:** 순서로 짝을 맺는 기능은 짝이 없는 자리를 **지우지 않고 표식으로 채운다**
([[wip-a00145-match-null-placeholder]]) — 지우면 뒤가 한 칸씩 밀려 엉뚱한 것끼리 이어지고
**연결은 성공하므로 에러도 안 난다**. 남은 표식은 실제 노드가 아니므로 눈에 띄어야 한다.

**How to apply:**
- 색은 [[framework-log-level-colors]] 의 실패 색(`log_levels.color("ERROR", dark)`)을
  쓴다 — 저장소의 빨강이 한 곳이고 밝은 테마에서도 읽힌다.
- ★ **TSL 을 거치지 않고 `list_widget.addItems(...)` 로 직접 채우면 자동 칠이 안 닿는다.**
  그때는 모듈 함수 `mark_null_items(list_widget, texts=None, tooltip=None)` 를 부른다
  (A00145 `Connect > Match` 가 그렇다 — 그 리스트는 v01.53 까지 회색이었다).
- 다른 표식을 쓰는 툴은 인스턴스의 `null_texts` 를 바꾼다. 기본은 `NULL_ITEM_TEXTS`.
- 리스트를 다시 채우면 칠도 사라진다(항목이 새로 만들어진다).
- 검증 29항목(mayapy 2024 + 오프스크린 Qt).
