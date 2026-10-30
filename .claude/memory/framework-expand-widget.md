---
name: framework-expand-widget
description: Framework 공용 Expand 위젯(MOD_expand_qt_v01) — 패널 본문을 별도 창으로 빼는 기능은 새로 만들지 말고 이걸 쓴다
metadata:
  node_type: memory
  type: project
---

**`Framework/qt/MOD_expand_qt_v01.py` → `JUN_mod_expand_qt_v01`** (2026-08-14 승격).
툴의 한 패널을 **독립 창으로 빼서 보는** 기능. 그래프 에디터·아웃라이너를 크게 띄워 놓고
툴 일부만 옆에 두는 배치용. 문서: `docs/Framework_MOD_expand_qt.md`.

```python
from Framework.qt import JUN_mod_expand_qt
panel = JUN_mod_expand_qt.JUN_mod_expand_qt_v01(
    title="Curve Filters", object_name="JUN_<툴>_<패널>_window", size=(420, 460))
panel.add_widget(w); panel.add_layout(row)          # 접이식 위젯과 같은 API
panel.expanded_changed.connect(lambda *_: self._fit_window_later())
```

**핵심: 복제가 아니라 이동.** 레이아웃에 add 하면 위젯이 이전 부모에서 떨어진다 —
본문을 통째로 옮기므로 **슬라이더·세션·undo 가 한 벌뿐**이고 두 화면 값이 어긋날 수 없다.
툴 코드는 위젯 참조(`self.slider`)를 그대로 쓰면 되고 확장 여부를 신경 쓸 필요가 없다.
복귀 자리는 `layout.indexOf` 로 저장했다가 `insertWidget` (위/아래 순서 유지).

**함정 — 호스트 창이 닫힐 때**: 본문이 확장 창에 가 있는 채로 툴 창이 파괴되면 **본문 위젯까지
함께 사라진다**. 그래서 위젯이 `eventFilter` 로 호스트 창의 `QEvent.Close` 를 감시해 자동으로
접는다. **툴 `closeEvent` 에 정리 코드를 넣지 않아도 된다**(초판에서는 툴마다 수동으로 넣었고,
빠뜨리기 쉬웠다).

- 버튼 재클릭 = 새 창 생성이 아니라 **떠 있는 창을 앞으로**. 닫기는 창의 X 로 한다
  (버튼이 '닫기'로 변하면 창을 찾다 누른 사용자가 창을 잃는다).
- `object_name` 은 **툴마다 유일하게** — 재실행 시 옛 창을 찾아 닫는 데 쓴다.
- **확장 창을 늘 위에 두려면 생성 인자 `stay_on_top=True`**(2026-10-30, A00110_V02 v02.33 Layers · Curve Filters). 확장 창은 툴 창의
  자식 Qt.Window 라 툴 창 위엔 있지만 그래프 에디터 등 다른 창을 클릭하면 뒤로 숨는다. v02.32 에서 Pin 토글을 따라 `set_stay_on_top`
  만 불렀을 때 사용자 보고 "여전히 뒤로 간다" → 창을 만들 때 플래그를 준다. GUI 확인 아직.
- maya 무의존 → 마야 밖에서도 import·검증 가능(단독 28항목).

쓰는 곳: `A00110_animTool_V02` Curve > Filters (v02.04~) · View > Layers (v02.31~).
`A00290_BSTool` Shape Editor 는 **아직 자체 구현**(이 위젯의 원형) — 옮길 수 있다.
관련: [[wip-a00110-tab-taxonomy]], [[prefer-subtabs-over-stacked-collapsibles]]
