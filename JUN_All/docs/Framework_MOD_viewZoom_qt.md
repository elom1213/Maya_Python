---
title: Framework 공용 위젯 — MOD_viewZoom_qt (리스트 · 트리 확대 / 축소)
aliases: [JUN_mod_viewZoom_qt, View Zoom, 리스트 확대]
tags: [framework, qt, widget, maya-python]
updated: 2026-11-04
---

# `JUN_mod_viewZoom_qt_v01` — 리스트 · 트리 · 표를 확대 / 축소

`JUN_All/Framework/qt/MOD_viewZoom_qt_v01.py`

아이템 뷰(QTreeWidget · QListWidget · QTableWidget 등) 하나에 붙이면 **배율 하나로 글자 · 행 높이 · 체크박스 ·
트리 들여쓰기가 함께** 커지고 작아진다. 툴마다 행 높이를 따로 박지 않고 이 한 줄로 쓴다.

`A00110_animTool_V02` View > Layers 에서 "행이 낮아 고르기 어렵고 Mute 체크박스가 작다" 는 요청(2026-11-04)으로 만들었다.

---

## 1. 쓰는 법

```python
from Framework.qt import JUN_mod_viewZoom_qt

self.zoom = JUN_mod_viewZoom_qt.JUN_mod_viewZoom_qt_v01(
    self.tree,                       # 아이템 뷰
    key="A00110_animTool_V02/layers",  # 배율 기억(QSettings JUN/viewZoom). None 이면 기억 안 함
    default=1.5,                     # 기본 배율(퍼센트 버튼을 누르면 이 값으로)
    minimum=0.8, maximum=3.0, step=0.1,
    whole_cell_toggle=True)          # 텍스트 없는 체크 칸은 칸 어디를 눌러도 토글

row.addWidget(self.zoom.controls())  # 선택: `Zoom [-] 150% [+]` 한 줄
```

| 조작 | 동작 |
|------|------|
| **Ctrl + 마우스 휠** (뷰 위) | 한 단계 확대 / 축소 |
| `controls()` 의 `-` / `+` | 한 단계 |
| 퍼센트 글자 클릭 | 기본 배율로 |
| 코드 | `set_scale(v)` · `zoom_in()` · `zoom_out()` · `reset()` · `scale()`, 시그널 `scale_changed(float)` |

## 2. 무엇이 커지나

| 항목 | 방법 |
|------|------|
| 글자 · 헤더 | 뷰 **자신의 스타일시트**에 `font-size: Npx` — 테마 qss 의 `QWidget { font-size: 12px }` 가 `setFont` 를 덮기 때문. 뷰 자신의 시트가 창의 시트보다 우선. 뷰가 원래 가진 시트는 앞에 그대로 둔다 |
| 기준 크기(100%) | **부모 위젯의 글자 크기**(테마가 정한 크기). 뷰가 **보일 때(Show)마다 다시 적용**해서, 테마를 창을 만든 뒤에 입혀도 · Expand 창으로 옮겨도 따라간다. 부모가 없는 뷰는 처음 글꼴 |
| 행 높이 | 델리게이트 `sizeHint` = max(원래, 20px × 배율) |
| 체크박스 | **델리게이트가 직접 그린다**(13px × 배율, 팔레트 Highlight 색 채움 + 체크 표시, 부분 체크 = 안쪽 사각형). 아이템 뷰의 체크박스는 스타일이 고정 크기로 그려 qss 로 못 키운다 |
| 굵은 글꼴 칸 | 아이템이 글꼴을 직접 가진 칸(예: 활성 레이어 굵게)도 같은 크기로(굵기 유지) |
| 트리 들여쓰기 | `indentation × 배율` |
| ResizeToContents 열 | 배율이 바뀔 때마다 다시 맞춘다 |

## 3. 체크 칸 누르기

- **텍스트 없는 체크 칸**(예: Mute / Solo / Lock 열)은 `whole_cell_toggle=True` 면 **칸 전체가 누름 영역**. 텍스트가 있는 칸은 체크박스 둘레만.
- 체크 영역 누름은 **행 선택을 바꾸지 않는다**(기본 델리게이트와 같음) — Layers 에서 Mute 를 눌러도 활성 레이어가 안 바뀐다.
- Space 키도 현재 칸 체크를 바꾼다. 바뀌면 평소처럼 `itemChanged` 가 난다.

## 4. 주의

- 뷰의 **델리게이트를 바꾼다**. 커스텀 델리게이트를 쓰는 뷰에는 붙이지 말 것.
- 뷰의 스타일시트에 글자 크기 규칙을 덧붙인다. 붙인 뒤 뷰에 `setStyleSheet` 를 직접 하면 배율 글자 크기가 사라진다(다음 Show · 배율 변경 때 되살아남).

## 5. 시험

`Framework/tests/test_view_zoom.py` — **PySide6(python) · PySide2(mayapy) 둘 다 32/32**: 배율별 행 · 글자 · 헤더 · 체크박스 크기,
min/max, 굵은 칸, 칸 가장자리 클릭 토글 · 행 선택 안 바뀜 · 이름 칸은 선택, 체크 없는 칸, `itemChanged`, `whole_cell_toggle=False`,
Ctrl + 휠 / 휠만, 버튼 줄, QSettings 기억, **창 qss 가 12px 를 박은 경우**(나중에 입혀도), 원래 시트 보존, 렌더, QListWidget.

## 6. 쓰는 곳

| 툴 | 뷰 | 기본 |
|----|----|------|
| `A00110_animTool_V02` v02.38 | View > Layers 레이어 트리 | 150% |
