---
title: Framework 공용 위젯 — MOD_log_qt (로그창)
aliases: [JUN_mod_log_qt, 로그창, 로그 위젯, Expand Clear Copy, Shrink]
tags: [framework, qt, widget, maya-python, log]
updated: 2026-09-17
---

# `JUN_mod_log_qt_v01` — Expand / Shrink / Clear / Copy 버튼이 달린 로그창

`JUN_All/Framework/qt/MOD_log_qt_v01.py`

툴마다 `QTextEdit` / `QPlainTextEdit` 를 하나 놓고 **"읽기 전용 + 높이 고정"** 을 반복하던 것을
위젯 하나로 모았다. 여기에 로그창에 늘 아쉬웠던 기능들을 붙였다.

| 버튼 | 동작 |
|------|------|
| **Expand** | 로그를 **별도 창으로 옮겨** 크게 본다. 다시 누르면 그 창을 앞으로 가져온다 |
| **Shrink** (2026-09-17~) | **토글.** 누르면 로그가 사라지고 버튼 줄만 남는다(라벨이 `Show` 로 바뀜). 툴 창도 그만큼 짧아진다. 다시 누르면 로그와 창 높이가 돌아온다 |
| **Clear** | 로그를 비운다 |
| **Copy** | 로그 **전문**을 클립보드로 |

## 사용처 — PySide 툴 **47곳 전부**

`A00470_MaterialTool` 에 먼저 붙였고(v01.02), 2026-09-16 에 나머지 **46곳을 한번에
갈아끼웠다**(계획서: [`Framework_MOD_log_qt_migration_plan.md`](Framework_MOD_log_qt_migration_plan.md)).
이제 `tools/*/app/ui/main_window.py` 의 로그창은 **전부 이 위젯이다.**

| 이전 계열 | 변수 이름 | 개수 |
|-----------|-----------|-----:|
| `QTextEdit` | `te_log` (26) · `log_widget` (6) · `txt_log` (1) | 33 |
| `QPlainTextEdit` | `log_view` | 13 |
| (선행) | `A00470_MaterialTool` | 1 |

`object_name` 은 **툴 폴더명을 그대로** 넣어 유일성을 보장한다 — `JUN_<폴더명>_log_window`.
버전 병존 4쌍(`A00060` · `A00080` · `A00110` · `A00390`)도 폴더명이 다르므로 자동으로 갈린다.
같은 이름이면 Expand 창이 서로를 찾아 닫는다.

**교체 대상이 아닌 텍스트 위젯도 있다** — 미리보기/리포트/편집기는 로그가 아니다:
`A00080_V03` 의 `constraint_preview` · `A00290_BSTool` 의 `te_bd_report` ·
`A00210_FileManager` 의 `txt_log_history` / `txt_new_note` · `A00250_SceneMemo` 의 `editor`.
`A00200_CSV_tool` 은 파일 구조와 import 스타일이 달라 **보류**했다.

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
| `QTextEdit` | `te_log` · `log_widget` · `txt_log` (33곳) | `append` · `setReadOnly` · `setMaximumHeight` / `setMinimumHeight` / `setFixedHeight` · `clear` · `setFont` · `setLineWrapMode` · `moveCursor` |
| `QPlainTextEdit` | `log_view` (13곳) | `appendPlainText` · `setReadOnly` · `setFixedHeight` / `setMinimumHeight` |

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

#### ★ 하지만 **내부 텍스트에만** 걸면 컨테이너가 끝없이 늘어난다 (2026-09-16 수정)

높이를 내부로만 넘기면 이번엔 **컨테이너의 상한이 없어진다.** 툴 창을 세로로
늘리면 레이아웃은 컨테이너를 계속 늘리는데 텍스트는 상한에서 멈추므로, 그 차이가
통째로 **빈 공간**으로 남는다 — 로그는 그대로인데 **로그창이 자리를 다 먹어** 다른 UI 가
밀려 스크롤을 내려야 보인다. `A00275_skinTool_V01` 에서 사용자가 잡았다 — 창 1060px 에서
컨테이너 493px · 텍스트 160px 로 **333px 가 빈 공간**이었다.

교체 전 `QTextEdit` 에 직접 걸 때는 없던 일이다 — 그때는 **위젯 자신이 상한을 가졌다.**
그래서 지금은 내부 텍스트에 걸면서 **컨테이너에도 버튼 줄 높이를 더해** 같은 제약을 건다.

```python
def setMaximumHeight(self, height):
    self.text.setMaximumHeight(height)                         # 보이는 줄 수는 그대로
    super().setMaximumHeight(height + self._chrome_height())   # 창을 늘려도 안 커진다
```

높이를 **아예 지정하지 않은** 툴(로그를 늘어나는 칸으로 쓰는 템플릿 등)은 그대로
늘어난다 — 그쪽은 텍스트도 같이 늘어나 빈 공간이 생기지 않기 때문이다.
상한을 가진 **36곳**(`setMaximumHeight` 23 · `setFixedHeight` 13)이 이 수정으로 고쳐진다.

#### ★ 단, 확장 창에서는 그 제약을 **푼다** (2026-09-16 수정)

같은 제약이 확장 창까지 따라가면 **반대로 어이없다** — Expand 로 띄운 창을 세로로
늘려도 로그는 `max` 에 묶여 그대로고, 남는 자리는 전부 빈 공간이 된다.
**크게 보려고 누른 버튼인데 크게 안 보이는** 상황이다(`A00275` 에서 사용자가 잡았다 —
팝업을 1200px 로 늘려도 로그는 160px 그대로였다).

그 제약은 **"툴 창 안에서 로그가 차지할 몫"** 이지 확장 창에서까지 지킬 값이 아니다.
그래서 `expand()` 가 지금 값을 담아 두고 풀어 준다.

```python
self._text_limits = (self.text.minimumHeight(), self.text.maximumHeight())
self.text.setMinimumHeight(0)
self.text.setMaximumHeight(WIDGET_MAX_HEIGHT)      # 16777215 (QWIDGETSIZE_MAX)
```

`collapse()` 가 담아 둔 값을 되돌리므로 **제자리로 돌아오면 다시 원래 몫만** 차지한다.
확장 중에 툴이 높이를 바꾸면(드물지만) 텍스트에 걸지 않고 **되돌릴 값만** 갱신한다.

실측(오프스크린) — `A00275`(Max 160) · `A00170`(Fixed 120) 둘 다 팝업을 520→800→1200px 로
늘리면 로그가 498→778→1178px 로 **창을 1:1 로 따라간다**(늘어난 680px 를 그대로 가져간다).
닫고 돌아오면 제약이 정확히 복원되고, 툴 창을 1400px 로 늘려도 다시 160 / 120px 만 차지한다.

실측(오프스크린) — `A00275`(Min 90 / Max 160): 창 760→1400px 동안 로그창은 **182px 고정**이고
늘어난 640px 를 **탭이 전부** 가져갔다. `A00170`(Fixed 120): 창 500→1100px 에 로그창 142px 그대로.
`A00004`(상한 없음): 컨테이너·텍스트가 함께 늘어난다(의도대로).

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

## 3-1. Shrink — 로그를 접어 숨기는 토글 (2026-09-17~)

로그를 잠깐 치우고 툴 버튼을 더 넓게 쓰고 싶을 때 누른다. **체크 가능한 버튼**이라 누르면 접히고
라벨이 **`Show`** 로 바뀌며, 다시 누르면 펴지고 **`Shrink`** 로 돌아온다(테마가 `:checked` 를 따로
칠하지 않아서 라벨로 상태를 보인다 — Pin/Pinned 와 같은 방식). **툴 코드는 아무것도 바꿀 필요가 없다.**
접혀 있는 동안에도 로그는 계속 쌓이고, Clear / Copy / Expand 는 그대로 동작한다.

**숨기기만으로는 자리가 안 빈다.** 컨테이너에 `텍스트 높이 + 버튼 줄` 의 min/max 가 걸려 있기 때문이다
(위 2장 ★). 그래서 세 가지를 같이 한다.

1. 텍스트를 숨긴다.
2. 컨테이너의 `(min, max)` 를 담아 두고 **버튼 줄 높이로** 바꾼다 — Expand 의 `_text_limits` 와 같은 방식.
   접혀 있는 동안 툴이 `setMaximumHeight` 등을 부르면 **펼 때 쓸 값만** 갱신한다.
3. **최상위 툴 창 높이를 줄어든 만큼 줄인다.** 최상위 창은 레이아웃이 알아서 줄이지 않으므로,
   안 하면 비운 자리가 스트레치로 넘어갈 뿐 "줄어든" 느낌이 없다.

펼 때는 **실제로 줄였던 만큼만** 되돌린다(창 최소 높이에 걸려 덜 줄었으면 덜 늘린다).
최대화 · 전체 화면 창은 크기를 건드리지 않고, `resize_window_on_shrink=False` 로 창 조절을 끌 수 있다.

| API | 뜻 |
|-----|-----|
| `set_shrunk(bool)` | 접기/펴기. 버튼 체크·라벨도 같이 맞춘다. 이미 그 상태면 아무것도 안 한다 |
| `toggle_shrink()` | 버튼과 같은 동작 |
| `is_shrunk()` | 접혀 있는가 |
| `shrunk_changed(bool)` | 상태가 바뀔 때 한 번 |

**Expand 와 겹쳐도 된다.**

| 상태 | 확장 창 | 툴 창 제자리 |
|------|---------|--------------|
| 펼침 · 확장 안 함 | — | 로그 |
| 접힘 · 확장 안 함 | — | 버튼 줄만 |
| 펼침 · 확장 중 | 로그 | 안내 라벨 |
| 접힘 · 확장 중 | 로그 | 버튼 줄만 |

접힌 채 확장 창을 닫으면 로그는 제자리로 돌아오되 **접힌 상태를 유지**한다.

> ★ **개발 중 잡은 함정 두 개**
> - **창 높이는 제약을 되돌리기 전에 잰다.** 컨테이너 min 을 되돌리는 순간 Qt 가 창을 새 최소 높이까지
>   **먼저 키운다.** 그 뒤에 잰 높이에 줄였던 만큼을 더하면 두 번 커진다(실측 600 → 692).
> - **`owner.layout()` 을 부르지 않는다.** 툴 창이 `self.layout = QVBoxLayout(self)` 처럼 같은 이름의
>   **속성**을 두면 메서드가 가려져 `'QVBoxLayout' object is not callable` 이 난다 — `A00004_base_QT`
>   템플릿이 그렇다. `QWidget.layout(owner)` 로 클래스 메서드를 직접 부른다.

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

### Shrink (2026-09-17) — 위젯 28항목 + 툴 50곳 스모크

**위젯 28항목**(mayapy 2024 + 오프스크린 Qt): 버튼 4개 순서 · 체크 가능 · 누르면 텍스트 숨김 + `Show` ·
컨테이너가 버튼 줄 높이로 · 창이 짧아짐 · 다시 누르면 로그/창 높이 **정확히 복원** · 숨긴 동안 쌓인 로그 보존 ·
**10번 왕복해도 크기가 새지 않음** · `set_shrunk` 중복 호출에 시그널 한 번 · 접힌 동안 `setMaximumHeight` 가
로그를 다시 열지 않고 펼 때 적용 · Expand 와 네 조합(위 표) · 확장 창에서는 높이 제약이 계속 풀려 있음 ·
높이를 안 준(늘어나는) 로그 · `resize_window_on_shrink=False` · 최대화 창은 크기 불변 · **창 최소 높이에 걸려
덜 줄어든 경우 정확히 복원** · 로그 자체가 최상위 창 · **9개 테마 × `Shrink`/`Show` 포함 라벨 전부 버튼 안에 들어감**.

**툴 50곳 스모크** — 이 위젯을 쓰는 모든 `MainWindow` 를 각 툴의 테마로 띄워 Shrink 를 두 번 눌렀다:
로그가 숨었다가 돌아오는지 · 창 높이와 로그 높이가 원래대로인지 · 버튼 줄이 로그 폭 안에 들어가는지 ·
**4번째 버튼 때문에 창 최소 폭이 늘어난 툴이 있는지**(없음). **48/50 통과**, 나머지 둘은 이번 변경과 무관한 import 문제다:
`A00004_base_QT` 는 `JUN_All.tools...` 절대 import 라 저장소 루트를 경로에 넣어야 뜬다 — 넣고 따로 돌려 통과(400 → 73 → 400).
이 확인에서 위 `owner.layout()` 함정을 잡았다. `A00008_base_QT_maya` 는 기존 결함(없는 `tools.A00001_base_maya` import).

툴 대부분은 창이 버튼 줄만 남기고 로그 높이만큼 짧아진다(예: `A00300_meshDoctor` 931 → 649).
`A00040_file_exporter_V02` · `A00080_KWI_creator_V02/V03` · `A00310_SearchTool` 은 창이 이미 최소 높이라
**로그만 사라지고 창 높이는 그대로**다 — 비운 자리는 그 툴의 스트레치가 가져간다.

> 마야 GUI 육안 확인은 아직이다 — 특히 창 높이를 스스로 계산하는 `A00110` · `A00220` 에서 섹션 접기와 섞었을 때.

### 전면 교체 후 — 47툴 전수 스모크 테스트

교체를 마치고 `mayapy` + 오프스크린 Qt 로 **툴 47개의 `MainWindow` 를 실제로 생성**해
다섯 가지를 한꺼번에 확인했다 — 생성 중 예외 없음 · 로그 위젯이 `JUN_mod_log_qt_v01` 인스턴스 ·
**`object_name` 이 47개 전부 유일** · `append`(HTML 색 살아있음) · `appendPlainText`(`<tag>` 글자 그대로) ·
**파일에 적힌 높이 제약이 내부 텍스트에 걸렸는지**(컨테이너가 아니라) · `expand()` → `collapse()` 왕복 후
텍스트가 제자리로 돌아오고 내용이 보존되는지.

**46/47 통과.** 유일한 실패는 `A00008_base_QT_maya` 이고, 이번 교체와 무관한 **기존 결함**이다 —
존재하지 않는 `tools.A00001_base_maya` 를 import 한다(2026-06-02 `86a8a45` 부터).

> 실제 Maya GUI 육안 확인은 아직이다(헤드리스 검증만 마쳤다). 특히 다음 세가지를 눈으로 본다 —
> 색깔 로그 3툴(`A00300` · `A00410` · `A00430`)의 색 · Pin 툴과 Expand 창의 항상-위 관계
> (`A00110` · `A00220` · `A00340` · `A00370`) · 창 높이를 스스로 계산하는 툴(`A00110` · `A00220`)의
> 섹션 접기/펼치기.
