---
name: wip-a00220-dino-save-pulse
description: "A00220_BackupTool v01.09 IMPLEMENTED (visual check + push pending) — dino shows accent-color hop at user-save moment, distinct from the 360° backup spin"
metadata: 
  node_type: memory
  type: project
  originSessionId: f512cf79-ecd4-4c35-bd99-27839d408de1
---

WIP (2026-07-01): A00220_BackupTool 상태 공룡에 **저장 감지 순간** 표현 추가. v01.08→01.09.

**요청**: 공룡이 '툴 작동중'·'백업 실시' 두 상태만 표현했음. Save Delay(v01.08)로 저장 순간과
백업 순간이 벌어졌으니 **사용자가 파일을 저장한 순간**을 눈으로 구분할 애니메이션 추가.
사용자 확정 스타일: **강조색 톡 점프**(AskUserQuestion 으로 선택).

**구현**:
- `app/ui/dino_widget.py`: 스핀(`_spin_t`) 패턴 미러링한 `_save_t` + `notify_save()`. 상수
  `_SAVE_TICKS=12`(~0.4s)·`_SAVE_PEAK_CELLS=5`(자동 점프 7칸보다 낮음). `_tick` 우선순위
  `스핀 > 저장 > 점프 > 자동점프`. `_save_offset_px()` 포물선. `_current_legs()` 에 `_save_t` 시
  `_LEGS_JUMP`. paintEvent 비-스핀 경로에서 `_save_t` 활성 시 스프라이트를 `palette().highlight()`
  색(폴백 `#4CAF50`)으로 그림. `set_running(False)` 에서 `_save_t` 초기화. 죽은 `hop()` 제거.
- `app/ui/main_window.py`: `_on_fs_changed`(저장 감지 핸들러)에서 백업 예약 직후
  `self.dino.notify_save()`. 감시 중=Auto Backup 모드에서만 나타남(주기 모드는 저장 순간 모름).
- 버전 01.09, docstring/헤더/CHANGELOG/docs(5장 Dino 상태표)/WORKLOG 갱신.

**검증**: `ast.parse` + 오프스크린 PySide6 실제 인스턴스화 6/6 PASS(펄스 시작·종료, 스핀 우선 양보,
저장 점프 높이<자동 점프, 정지 초기화, `_on_fs_changed`→notify_save+예약).

**계획서**: C:\Users\USER\.claude\plans\zazzy-spinning-leaf.md

**남은 일**: 육안 확인(python launch.py → Start → 파일 저장 시 강조색 톡 점프 → Delay 후 스핀) +
푸시([[push-target-dnable-dev]], CHANGELOG/docs/WORKLOG 포함=[[push-includes-tool-guide-docs]]).
끝나면 이 메모 삭제. 규약: [[ui-text-english-only]], [[worklog-maintenance]].
