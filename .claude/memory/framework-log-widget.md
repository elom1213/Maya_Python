---
name: framework-log-widget
description: "공용 로그창 JUN_mod_log_qt_v01 (Expand/Clear/Copy) — 2026-09-16 에 PySide 툴 47곳 전부 교체 완료. 내부는 QTextEdit 이어야 하고(색깔 로그), 높이는 컨테이너가 아니라 내부 텍스트에 걸어야 한다"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ab0fb3dc-63c8-41e1-86da-70abc7b8ab38
  modified: 2026-09-16T01:12:12.248Z
---

`Framework/qt/MOD_log_qt_v01.py` 의 `JUN_mod_log_qt_v01` (2026-09-16 신설, 첫 사용처
[[wip-a00470-materialtool]]). 읽기 전용 로그 + **작은 버튼 3개** — `Expand`(별도 창) ·
`Clear` · `Copy`(전문 클립보드). 문서 `JUN_All/docs/Framework_MOD_log_qt.md`.

**★ 2026-09-16 에 전면 교체를 마쳤다 — `tools/*/app/ui/main_window.py` 의 로그창은 이제
47/47 전부 이 위젯이다.** 이전은 두 계열 — `te_log`/`log_widget`/`txt_log`(QTextEdit) 33,
`log_view`(QPlainTextEdit) 13. 실제로 부르는 메서드는 `append` · `appendPlainText` · `setReadOnly` ·
높이 3종 · `clear` · `setFont` · `setLineWrapMode` · `moveCursor` 뿐이라, 위젯이 **그 이름을 전부
받게** 만들어 두면 교체는 **생성 두 줄**로 끝난다(나머지는 `__getattr__` 로 내부 텍스트에 위임).

**★ 내부는 반드시 `QTextEdit`.** `A00300_meshDoctor` · `A00430_DemBone` · `A00410_SecondaryMotion`
이 `append('<span style="color:…">…')` 로 **색깔 로그**를 쓴다 — `QPlainTextEdit` 로 만들면 그
세 툴에서 태그가 글자 그대로 보인다. 대신 `appendPlainText` 는 **커서로 평문 삽입**해 직접 구현해야
한다(`append` 로 대신하면 로그 속 `<` 가 HTML 로 먹힌다).

**★ 높이 계열(`setFixedHeight`/`setMinimumHeight`/`setMaximumHeight`)은 내부 텍스트와
컨테이너 **둘 다**에 건다** — 텍스트에는 받은 값 그대로, 컨테이너에는 **버튼 줄 높이를 더해서.**
(`setFont` 는 텍스트에만.) 둘 다 이유가 있고, **한쪽만 하면 반대 방향으로 깨진다.**

- 컨테이너에만 걸면 → 버튼 줄이 그 높이를 나눠 먹어 **로그가 교체 전보다 줄어든다**
  ([[tsl-widget-max-height-squeezes-buttons]] 와 같은 함정).
- **텍스트에만 걸면 → 컨테이너의 상한이 없어진다.** 툴 창을 세로로 늘리면 레이아웃은
  컨테이너를 계속 늘리는데 텍스트는 상한에서 멈추므로 그 차이가 **빈 공간**으로 남아,
  로그는 그대로인데 **로그창이 자리를 다 먹고 다른 UI 가 스크롤 밖으로 밀린다.**
  2026-09-16 전면 교체 직후 이 모양으로 나갔고 사용자가 `A00275` 에서 잡았다 — 실측 창 1060px 에서
  컨테이너 493px · 텍스트 160px, **333px 가 버려진 자리**였다. 교체 전 `QTextEdit` 에 직접 걸 때는
  **위젯 자신이 상한을 가졌기 때문에** 없던 일이다.

결과: 보이는 줄 수는 교체 전과 같고, 창은 버튼 줄(~22px)만큼 커지되 **더 늘리지는 않는다.**
높이를 아예 안 준 툴(로그를 늘어나는 칸으로 쓰는 템플릿 등)은 그대로 늘어난다 — 그쪽은 텍스트도
같이 늘어나 빈 공간이 생기지 않으므로 증상이 아니다.

**★ 그리고 그 제약은 확장 창에서는 풀어야 한다.** 그 값은 **"툴 창 안에서 로그가 차지할 몫"** 이지
Expand 로 띄운 창에서까지 지킬 값이 아니다. 그대로 두면 **팝업을 아무리 늘려도 로그는 상한에 묶여**
남는 자리가 빈 공간이 된다 — 크게 보려고 누른 버튼인데 크게 안 보인다(2026-09-16 사용자 지적,
`A00275` 에서 팝업 1200px 에 로그 160px). `expand()` 가 `(min, max)` 를 `_text_limits` 에 담아 두고
`min=0` / `max=16777215`(`QWIDGETSIZE_MAX`, 바인딩에 이름이 없어 상수로 적어 둠)로 풀고,
`collapse()` 가 되돌린다. 확장 중에 툴이 높이를 바꾸면 텍스트에 걸지 않고 **되돌릴 값만** 갱신한다.

> 세 자리를 한 세트로 기억할 것 — **텍스트에 걸고**(보이는 줄 수 유지) · **컨테이너에도 걸고**
> (창을 늘려도 안 커짐) · **확장 창에서는 푼다**(팝업은 창을 따라감). 하나라도 빠지면 셋 중 하나가
> 깨진다.

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

**`object_name` 은 툴 폴더명을 그대로 넣는다** — `JUN_<폴더명>_log_window`. 폴더명이 이미
유일하므로 버전 병존 4쌍(`A00060` · `A00080` · `A00110` · `A00390`, V01/V02/V03 가 동시에 뜨는
상황)도 자동으로 갈린다. 같으면 Expand 창이 서로를 찾아 닫는다.
`window_title` 은 `"<툴 이름> - Log"`, 버전 병존 툴만 제목에도 버전을 넣는다.

**교체 대상이 아닌 텍스트 위젯이 있다** — 미리보기/리포트/편집기는 로그가 아니다:
`constraint_preview`(A00080_V03) · `te_bd_report`(A00290) · `txt_log_history` / `txt_new_note`
(A00210) · `editor`(A00250). **`A00200_CSV_tool` 은 보류** — 단일 파일 구조에 `QtWidgets.`
접두사 import 스타일이라 일괄 처리에 섞지 않았다.

계획서 · 결과: `JUN_All/docs/Framework_MOD_log_qt_migration_plan.md` (배치 5개로 커밋).
검증: 위젯 자체 **56 + 55항목** + 전면 교체 후 **47툴 전수 스모크 46/47**(mayapy + 오프스크린 Qt).
실패 1건 `A00008_base_QT_maya` 는 로그창과 무관한 **기존 결함** — 존재하지 않는
`tools.A00001_base_maya` 를 import 한다(2026-06-02 `86a8a45` 부터). 미해결 안건.
**마야 GUI 육안 확인은 아직** — 색깔 로그 3툴의 색 · Pin 툴과 Expand 창의 항상-위 관계 ·
창 높이를 스스로 계산하는 툴(`A00110` · `A00220`)의 섹션 접기/펼치기 · `setFixedHeight` 13곳의 +22px.
