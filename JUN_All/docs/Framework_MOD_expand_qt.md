---
title: Framework 공용 위젯 — MOD_expand_qt (Expand / 별도 창)
aliases: [JUN_mod_expand_qt, Expand 패널, 별도 창]
tags: [framework, qt, widget, maya-python]
updated: 2026-08-14
---

# `JUN_mod_expand_qt_v01` — 본문을 별도 창으로 빼서 보는 패널

`JUN_All/Framework/qt/MOD_expand_qt_v01.py`

패널 안의 내용을 **독립 창으로 띄웠다가 제자리로 되돌린다.** 그래프 에디터나 아웃라이너를
크게 띄워 놓고 툴의 한 부분만 옆에 두고 쓰는 배치에 쓴다.

`A00290_BSTool` 의 Shape Editor `Expand` 와 `A00110_animTool_V02` 의 Curve Filters `Expand`
에서 검증한 방식을 공용으로 올린 것이다.

---

## 1. 쓰는 법

```python
from Framework.qt import JUN_mod_expand_qt

self.panel = JUN_mod_expand_qt.JUN_mod_expand_qt_v01(
    title="Curve Filters",                                  # 창 제목
    object_name="JUN_A00110_animTool_V02_curveFilters_window",  # 툴마다 유일하게
    size=(420, 460))

self.panel.add_widget(some_widget)     # 본문 구성 (접이식 위젯과 같은 API)
self.panel.add_layout(some_row)

tab_layout.addWidget(self.panel)

# 창 크기를 콘텐츠에 맞추는 툴이면 연결해 둔다
self.panel.expanded_changed.connect(lambda *_: self._fit_window_later())
```

`self.panel.body` 를 직접 써도 된다(위젯 안의 `QVBoxLayout`).

---

## 2. 핵심 — 복제가 아니라 **이동**이다

본문 위젯을 새 창으로 **그대로 옮긴다**(Qt 는 레이아웃에 add 하면 이전 부모에서 자동으로
떼어 온다). 두 벌을 만들어 동기화하는 방식이 아니라서:

- 슬라이더 · 세션 · undo 규칙이 **완전히 같게** 동작한다(코드가 한 벌이니 당연히).
- 두 화면의 값이 **어긋날 여지 자체가 없다**.
- 툴 코드는 위젯 참조(`self.slider` 등)를 **그대로** 쓰면 된다. 확장 여부를 신경 쓸 필요가 없다.

되돌릴 자리는 `layout.indexOf` 로 미리 저장해 두었다가 `insertWidget` 으로 복귀하므로,
위/아래 다른 위젯 사이의 **원래 순서**를 지킨다.

---

## 3. 창이 미아로 남지 않게

확장 창은 툴 창의 자식(`QWidget(owner, Qt.Window)`)이다. 툴 창이 닫힐 때 본문이 확장 창에
들어가 있으면 **본문까지 함께 파괴**된다. 그래서 이 위젯은 **툴 창의 Close 이벤트를 감시해
자동으로 접는다**(`eventFilter`). 툴은 `closeEvent` 에 정리 코드를 넣지 않아도 된다.

> `A00290_BSTool` · `A00110_animTool_V02` 초판에서는 각 툴의 `closeEvent` 에 수동으로
> 정리 코드를 넣었다. 공용화하면서 위젯이 알아서 하도록 바꿨다.

---

## 4. API

| 멤버 | 설명 |
|------|------|
| `add_widget(w)` / `add_layout(l)` | 본문 구성 (`JUN_mod_collapsible_qt_v01` 과 같은 API) |
| `body` | 본문 `QVBoxLayout` |
| `content()` | 본문 위젯(옮겨 다니는 그것) |
| `button` | Expand 버튼(다른 자리에 옮겨 붙이고 싶을 때) |
| `placeholder` | 본문이 나가 있는 동안 자리를 지키는 `QLabel` |
| `expand()` / `collapse()` / `toggle()` | 프로그램에서 직접 제어 |
| `is_expanded()` | 지금 별도 창에 나가 있나 |
| `expanded_changed(bool)` | 상태가 바뀔 때 방출(창 크기 재조정 등에 연결) |

### 생성 인자

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `title` | `"Panel"` | 확장 창 제목. 버튼 툴팁·기본 안내 문구에도 쓰인다 |
| `button_label` | `"Expand"` | 버튼 글자 |
| `placeholder` | 자동 | 본문이 나가 있는 동안의 안내 문구 |
| `object_name` | 자동 | 확장 창의 `objectName`. **툴마다 유일하게 줄 것** — 재실행 시 옛 창을 찾아 닫는 데 쓴다 |
| `size` | `(420, 460)` | 확장 창 초기 크기. `None` 이면 Qt 기본값 |
| `button_on_top` | `True` | 버튼 줄을 본문 위/아래 중 어디에 둘지 |

---

## 5. 동작 규칙

- **버튼을 다시 누르면** 새 창을 만들지 않고 **떠 있는 창을 앞으로** 가져온다.
  (버튼이 '닫기' 로 바뀌지 않는 이유: 창을 찾다가 버튼을 누른 사용자가 창을 잃어버린다.)
- **닫기는 창의 X** 로 한다 → 자동으로 제자리 복귀.
- 패널 여러 개를 한 툴에 둬도 **서로 간섭하지 않는다**(각자 창을 가진다).
- `maya` 의존이 없다 — 마야 밖에서도 import·생성된다.

---

## 6. 검증

`mayapy` 헤드리스 28항목: 마야 없이 import, 이동(복제 아님) 확인, 안내 라벨, 재클릭 시 앞으로,
닫으면 원래 순서 자리로 복귀, `expanded_changed` 방출, **호스트 창 닫힘 시 자동 접힘**,
생성 인자(라벨·문구·objectName·크기), 패널 2개 독립 동작.

## 7. 쓰고 있는 툴

| 툴 | 어디에 |
|----|--------|
| `A00110_animTool_V02` | `Curve > Filters` (v02.04~) |
| `A00290_BSTool` | Shape Editor 타겟 목록 — 자체 구현(공용화 이전). 옮길 수 있다 |
