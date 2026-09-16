---
name: framework-log-widget
description: "공용 로그창 JUN_mod_log_qt_v01 (Expand/Clear/Copy) — 내부는 QTextEdit 이어야 하고(색깔 로그), 높이는 컨테이너가 아니라 내부 텍스트에 걸어야 한다"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ab0fb3dc-63c8-41e1-86da-70abc7b8ab38
  modified: 2026-09-16T01:12:12.248Z
---

`Framework/qt/MOD_log_qt_v01.py` 의 `JUN_mod_log_qt_v01` (2026-09-16 신설, 첫 사용처
[[wip-a00470-materialtool]]). 읽기 전용 로그 + **작은 버튼 3개** — `Expand`(별도 창) ·
`Clear` · `Copy`(전문 클립보드). 문서 `JUN_All/docs/Framework_MOD_log_qt.md`.

**저장소 로그창은 두 계열이고 합쳐서 39곳이다** — `te_log`/`log_widget`/`txt_log`(QTextEdit) 25,
`log_view`(QPlainTextEdit) 14. 실제로 부르는 메서드는 `append` · `appendPlainText` · `setReadOnly` ·
높이 3종 · `clear` · `setFont` · `setLineWrapMode` · `moveCursor` 뿐이라, 위젯이 **그 이름을 전부
받게** 만들어 두면 교체는 **생성 두 줄**로 끝난다(나머지는 `__getattr__` 로 내부 텍스트에 위임).

**★ 내부는 반드시 `QTextEdit`.** `A00300_meshDoctor` · `A00430_DemBone` · `A00410_SecondaryMotion`
이 `append('<span style="color:…">…')` 로 **색깔 로그**를 쓴다 — `QPlainTextEdit` 로 만들면 그
세 툴에서 태그가 글자 그대로 보인다. 대신 `appendPlainText` 는 **커서로 평문 삽입**해 직접 구현해야
한다(`append` 로 대신하면 로그 속 `<` 가 HTML 로 먹힌다).

**★ 높이 계열(`setFixedHeight`/`setMinimumHeight`/`setMaximumHeight`)과 `setFont` 는 컨테이너가
아니라 내부 텍스트에 건다.** 컨테이너에 걸면 버튼 줄이 그 높이를 나눠 먹어 **로그가 보이던 것보다
줄어든다** ([[tsl-widget-max-height-squeezes-buttons]] 와 같은 함정). 이렇게 하면 보이는 줄 수는
교체 전과 같고 창만 버튼 줄(~22px)만큼 커진다.

**Expand 는 복제가 아니라 이동** — [[framework-expand-widget]] 과 같은 기법(텍스트 위젯을 새 창으로
옮기고 `layout.indexOf` 로 되돌린다). 확장 중 들어온 로그도 같은 위젯에 쌓여 **동기화 문제 자체가
없다.** 버튼 줄은 원래 자리에 남아 확장 중에도 Clear/Copy 가 된다. 툴 창 Close 를 `eventFilter` 로
감시해 자동으로 접는다(미아 방지). 공용 Expand 패널을 그대로 쓰지 않은 이유는 그쪽이 **버튼 하나
전용 줄** 구조라 버튼 3개 한 줄 요구와 맞지 않아서다.

**★ 테마 qss 의 `QPushButton { padding: 8px; }` 이 낮은 버튼을 먹는다.** `setFixedHeight(20)` 과
만나면 위아래 16px + 테두리 2px 로 **글자 자리가 2px** 만 남아 **글자가 아예 안 보인다**(글꼴 12px).
버튼은 멀쩡히 보이고 클릭도 되므로 크기만 봐서는 모른다 — 2026-09-16 에 실제로 이 상태로 내보냈고
사용자가 "글자가 안 보인다" 고 알려 줬다. 해결은 그 버튼에만 `setStyleSheet("padding: 0px 6px;")`
(Qt 스타일시트는 지정한 속성만 덮어써서 색·테두리·호버는 테마 그대로). 내용 영역 `72x2` → `72x18`.
**폭도 고정하지 말 것** — `setFixedWidth` 는 폰트가 큰 테마에서 같은 일을 가로로 만든다.
`setMinimumWidth` 만 준다. **높이 24px 미만 버튼을 만드는 모든 위젯이 같은 함정을 밟는다.**

**★ 버튼 글자가 보이는지를 픽셀로 검증하려 하지 말 것.** 오프스크린 Qt 에서는 `QLabel` 조차
`grab()` 하면 고유 색이 1개다 — **글자가 래스터화되지 않는다.** 멀쩡한 버튼도 "글자 0px" 로 나와
아무것도 가리지 못한다(실제로 한 번 틀린 결론을 낼 뻔했다). **`QStyle.SE_PushButtonContents`**
내용 영역을 재서 `fontMetrics().height()` 와 비교하는 것이 맞다 — qss padding 이 반영된 값이다.

**함정 하나**: `copy()` 는 `QTextEdit` 의 **선택 영역 복사**로 위임된다. 전문 복사는
`copy_to_clipboard()`(= Copy 버튼). 빈 로그면 **클립보드를 건드리지 않는다.**

`object_name` 은 **툴마다 유일하게** 준다(확장 창이 서로를 닫지 않도록).
검증: mayapy + 오프스크린 Qt **56 + 55항목**(버튼 여백은 8개 테마 × 3버튼, 버그 재현 포함).
마야 GUI 확인은 아직.
