---
name: qt-exclusive-radio-uncheck-ignored
description: "배타적 QRadioButton 은 setChecked(False) 가 무시된다 — 모드를 코드로 바꾸려면 켜려는 쪽을 직접 켜야 하고, 그러려면 그 위젯을 보관해 두어야 한다"
metadata:
  node_type: memory
  type: reference
---

`QButtonGroup`(또는 `autoExclusive`) 안의 `QRadioButton` 은 **`setChecked(False)` 가 조용히
무시된다.** 배타 그룹에서는 "아무것도 안 켜진 상태" 로 갈 수 없기 때문이다.

그래서 `rb_a.setChecked(False)` 로 "B 모드" 를 만들려 하면 **아무 일도 일어나지 않고 A 모드가
그대로** 남는다. 예외도 경고도 없어서, 테스트에서 "왜 결과가 다르지" 로 한참 헤맨다
(2026-09-16 `A00310_SearchTool` 에서 실제로 밟았다 — Selected 모드로 바꾼 줄 알았는데 계속
Hierarchy 모드라 자손까지 딸려 왔다).

**켜려는 쪽을 직접 켠다** — `rb_b.setChecked(True)`.

그러려면 **두 라디오를 다 보관해야 한다.** 옵션 행을 만드는 헬퍼가 한쪽만
`setattr(self, ...)` 하고 있으면 코드로는 모드를 못 바꾼다(사용자는 클릭으로 바꿀 수 있으니
UI 만 보면 멀쩡하다). 헬퍼를 쓸 때 **양쪽 다 보관**해 두는 편이 낫다.

관련: [[qt-clicked-passes-checked-bool]], [[qtreewidgetitem-checkable-default-flag]]
