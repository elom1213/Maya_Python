---
title: Framework 공용 위젯 — MOD_log_qt (로그창)
aliases: [JUN_mod_log_qt, 로그창, 로그 위젯, Expand Clear Copy]
tags: [framework, qt, widget, maya-python, log]
updated: 2026-09-16
---

# `JUN_mod_log_qt_v01` — Expand / Clear / Copy 버튼이 달린 로그창

`JUN_All/Framework/qt/MOD_log_qt_v01.py`

툴마다 `QTextEdit` / `QPlainTextEdit` 를 하나 놓고 **"읽기 전용 + 높이 고정"** 을 반복하던 것을
위젯 하나로 모았다. 여기에 로그창에 늘 아쉬웠던 세 가지를 붙였다.

| 버튼 | 동작 |
|------|------|
| **Expand** | 로그를 **별도 창으로 옮겨** 크게 본다. 다시 누르면 그 창을 앞으로 가져온다 |
| **Clear** | 로그를 비운다 |
| **Copy** | 로그 **전문**을 클립보드로 |

`A00470_MaterialTool` 에 먼저 붙였다. 저장소에는 로그창이 **39군데**(`log_view` 계열 14 ·
`te_log` 계열 25) 있고, 하나씩 이 위젯으로 갈아끼우는 것이 목표다.

---

## 1. 쓰는 법

```python
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

self.log_view = JUN_mod_log_qt_v01(
    window_title="Material Tool - Log",                      # Expand 창 제목
    object_name="JUN_A00470_MaterialTool_log_window")        # 툴마다 유일하게
self.log_view.setMinimumHeight(180)
layout.addWidget(self.log_view)

self.log_view.appendPlainText("plain message")               # 기존 호출 그대로
self.log_view.append('<span style="color:#ff5555;">red</span>')   # 색깔 로그도 그대로
self.log_view.log("새 코드에서는 이 이름을 써도 된다")
```

| 인자 | 기본 | 뜻 |
|------|------|-----|
| `window_title` | `"Log"` | Expand 로 띄우는 창의 제목 |
| `object_name` | 제목에서 생성 | 그 창의 objectName. **툴마다 유일해야** 재실행 시 옛 창을 찾아 닫을 수 있다 |
| `title` | `None` | 버튼 줄 왼쪽 라벨. 기본은 라벨 없음 — 기존 로그창을 갈아끼워도 화면이 달라지지 않게 |
| `expand_size` | `(620, 520)` | 확장 창 초기 크기 |
| `buttons_on_top` | `True` | 버튼 줄을 로그 위/아래 어디에 둘지 |
| `read_only` | `True` | 로그는 읽는 것이다 |

시그널 — `expanded_changed(bool)` · `cleared()` · `copied(int)`.

---

## 2. ★ 기존 로그창을 그대로 갈아끼울 수 있는 이유

저장소의 로그창은 두 계열이고, 실제로 호출하는 메서드는 조사해 보면 몇 개뿐이다.

| 계열 | 변수 이름 | 호출하는 것 |
|------|-----------|-------------|
| `QTextEdit` | `te_log` · `log_widget` · `txt_log` (25곳) | `append` · `setReadOnly` · `setMaximumHeight` / `setMinimumHeight` / `setFixedHeight` · `clear` · `setFont` · `setLineWrapMode` · `moveCursor` |
| `QPlainTextEdit` | `log_view` (14곳) | `appendPlainText` · `setReadOnly` · `setFixedHeight` / `setMinimumHeight` |

이 위젯은 **그 이름을 전부 그대로 받는다.** 그래서 교체는 보통 **생성 두 줄만** 바뀐다.

- **내부는 `QTextEdit` 이다.** `A00300_meshDoctor` · `A00430_DemBone` ·
  `A00410_SecondaryMotion` 이 `append('<span style="color:…">…')` 로 **색깔 로그**를 쓴다 —
  내부를 `QPlainTextEdit` 로 두면 그 세 툴에서 태그가 글자 그대로 보인다.
- **`appendPlainText` 는 직접 구현했다.** `QTextEdit` 에는 없는 이름이고, `append()` 로 대신하면
  로그에 들어 있는 `<` 가 HTML 로 먹힌다. 커서로 **평문**을 넣어 글자를 그대로 남긴다.
  → `a < b and <not a tag>` 가 그대로 보인다(테스트로 고정).
- 그 밖에 `QWidget` 에 없는 이름은 `__getattr__` 로 **내부 텍스트에 위임**한다 —
  `toPlainText` · `moveCursor` · `verticalScrollBar` · `document` · `setLineWrapMode` 등.

> ⚠️ `copy()` 는 `QTextEdit` 의 **선택 영역 복사**로 위임된다. 전문 복사는 **`copy_to_clipboard()`**
> (= Copy 버튼)다. 이름이 겹치는 유일한 자리다.

### 높이는 컨테이너가 아니라 **내부 텍스트**에 건다 ★

`setFixedHeight(110)` 을 이 위젯(컨테이너)에 그대로 걸면 **버튼 줄이 그 110 을 나눠 먹어**
로그가 보이던 것보다 줄어든다. 공용 TSL 에서 `max-height` 가 버튼을 찌그러뜨렸던 것과 같은 함정이다.
그래서 `setFixedHeight` / `setMinimumHeight` / `setMaximumHeight` / `setFont` 는 **전부 내부
텍스트로 넘긴다.**

> 결과: **로그가 보이는 줄 수는 교체 전과 같고**, 창이 버튼 줄(약 22px)만큼 세로로 커진다.
> 창 높이를 유지해야 하는 툴이라면 기존 높이에서 그만큼 빼서 주면 된다.

### ★ 테마 qss 의 `padding: 8px` 이 낮은 버튼을 통째로 먹는다

처음 만들었을 때 **버튼 글자가 아예 보이지 않았다.** 원인은 폰트도, 버튼 크기 계산도 아니었다.

```
QPushButton { padding: 8px; }      <- 모든 테마 qss 의 공통 규칙
setFixedHeight(20)                 <- 작은 버튼을 만들려고 준 높이
```

위아래 패딩 16px + 테두리 2px = **18px**. 20px 높이에서 글자가 그려질 자리는 **2px** 만 남고,
글꼴은 12px 이라 아무것도 그려지지 않는다. 버튼은 멀쩡히 있고 클릭도 되므로 **크기만 보면
정상으로 보이는** 종류의 버그다.

그래서 이 세 버튼에만 패딩을 덮어쓴다.

```python
BUTTON_STYLE = "padding: 0px 6px; margin: 0px;"
button.setStyleSheet(BUTTON_STYLE)     # 색·테두리·호버는 테마 규칙 그대로 남는다
```

Qt 스타일시트는 **지정한 속성만** 덮어쓰므로 테마의 색이 깨지지 않는다.
내용 영역은 `72x2` → `72x18` 이 되어 12px 글꼴이 3px 여유를 두고 들어간다(측정값).

**폭은 고정하지 않는다.** `setFixedWidth` 로 잘라 두면 폰트가 큰 테마에서 같은 일이 **가로로**
되풀이된다. `setMinimumWidth(58)` 만 주고 나머지는 스타일에 맡긴다 — 8개 테마에서 글자 폭보다
넓은 것을 확인했다.

> 낮은 버튼(높이 24px 미만)을 새로 만드는 다른 위젯도 같은 함정을 밟는다. 높이를 고정했다면
> 패딩도 같이 손봐야 한다.

---

## 3. Expand 는 복제가 아니라 이동이다

`MOD_expand_qt_v01` 과 같은 방식이다. 텍스트 위젯을 **그대로 새 창으로 옮긴다.**

- 두 벌을 동기화할 일이 없다 — **확장 중에 들어온 로그도 당연히 같은 위젯에 쌓인다.**
- 툴 코드는 `self.log_view` 참조를 그대로 쓰면 된다.
- 버튼 줄은 **원래 자리에 남으므로** 확장 중에도 Clear / Copy 가 동작한다.
- 확장 중 원래 자리에는 안내 라벨이 자리를 지킨다.

**툴 창이 닫히면 자동으로 접는다.** 로그가 확장 창에 가 있는 채로 툴 창이 파괴되면 텍스트까지
함께 사라지므로, 툴 창의 Close 를 `eventFilter` 로 감시한다 — 각 툴이 `closeEvent` 에 정리 코드를
넣지 않아도 된다.

공용 Expand 패널(`MOD_expand_qt_v01`)을 쓰지 않고 여기에 다시 구현한 것은, 그 패널이 **버튼
하나를 위한 전용 줄**을 갖는 구조라 **버튼 3개를 한 줄에** 두려는 이 위젯의 요구와 맞지 않기
때문이다. 이동/복귀/미아 방지 기법은 그대로 따랐다.

---

## 4. 교체 절차 (기존 툴에 적용할 때)

1. import 를 바꾸고 생성부를 교체한다.
   ```python
   # 전
   self.te_log = QTextEdit()
   self.te_log.setReadOnly(True)
   self.te_log.setMaximumHeight(120)

   # 후
   self.te_log = JUN_mod_log_qt_v01(
       window_title="Curve Tool - Log",
       object_name="JUN_A00400_CurveTool_log_window")
   self.te_log.setMaximumHeight(120)          # 내부 텍스트에 걸린다
   ```
2. **나머지 호출부는 건드리지 않는다.** `append` / `appendPlainText` 가 그대로 동작한다.
3. `object_name` 을 **툴마다 다르게** 준다(확장 창이 서로를 닫지 않도록).
4. 창을 띄워 로그 높이가 예전과 같은지, 색깔 로그가 있으면 색이 살아 있는지 본다.

---

## 5. 검증

`mayapy` (Maya 2024) + 오프스크린 Qt 헤드리스 **56 + 55항목 통과**.

버튼 3개의 존재와 크기 · 두 계열 쓰기(`append` / `appendPlainText` / `log`)가 한 상자에 쌓이는지 ·
**HTML 이 렌더되는지와 평문이 태그를 지키는지** · Clear(버튼 · `clear()` · 시그널) ·
Copy(전문 · 클립보드 내용 · 빈 로그는 클립보드를 건드리지 않는지) ·
**Expand 가 복제가 아니라 이동인지**(확장 중 append 가 같은 위젯에 쌓이는지 · 두 번 눌러도 창이
하나인지 · 닫으면 제자리로 · 내용 보존) · **툴 창을 닫으면 자동으로 접히는지(미아 방지)** ·
드롭인 호환 11항목(높이 3종이 **내부 텍스트**에 걸리는지 · `setFont` · `setLineWrapMode` ·
`moveCursor` · `verticalScrollBar` · `document` · 없는 속성은 `AttributeError`) ·
`A00470_MaterialTool` 이 실제로 이 위젯을 쓰는지(탭의 `log()` 경로 · 진단 리포트 · Expand 동작).

**버튼 여백 55항목** — 8개 테마(`teal_dark` `brown_dark` `coral_dark` `yellow_light` `slate_mid`
`purple_dark` `green_mid` `dark`) × 버튼 3개의 **세로·가로 여백**, 버튼이 여전히 작은지,
셋이 한 줄에 들어가는지, 로그가 받은 높이를 그대로 지키는지. 맨 앞에 **버그 재현**을 둔다 —
패딩을 덮어쓰지 않은 20px 버튼의 내용 영역이 글꼴보다 작다는 것을 먼저 확인하고, 그다음 수정본이
크다는 것을 확인한다.

> ★ **픽셀을 세지 않는다.** 처음에는 버튼을 `grab()` 해서 글자 픽셀을 세려 했는데, 오프스크린
> 플랫폼에서는 `QLabel` 조차 고유 색이 1개로 나온다 — **글자가 래스터화되지 않는다.** 멀쩡한
> 버튼도 "글자 0px" 로 보여서 아무것도 가리지 못했다. 대신 스타일이 계산하는 내용 영역
> (`QStyle.SE_PushButtonContents`)을 재고 글꼴 높이와 비교한다 — qss 의 padding 이 그대로
> 반영되는 값이라 이 버그를 정확히 집는다.

> 실제 Maya GUI 확인은 아직이다(헤드리스 검증만 마쳤다).
