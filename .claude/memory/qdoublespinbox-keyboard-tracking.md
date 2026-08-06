---
name: qdoublespinbox-keyboard-tracking
description: 값을 씬에 되쓰는 QDoubleSpinBox/QSpinBox 는 setKeyboardTracking(False) 로 두어야 타이핑이 안 잘린다
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4f6580d4-4bc6-4134-a627-7dc361a23170
  modified: 2026-08-06T05:15:15.988Z
---

`QDoubleSpinBox` 는 기본이 **keyboard tracking ON** — 키를 누를 때마다 값을 확정하고,
확정할 때마다 편집 중인 텍스트를 소수점 자릿수에 맞춰 **다시 쓰며 커서를 옮긴다**
(`interpretText` → `updateEdit`). `decimals(3)` 이면 `0.1` 까지만 쳐도 칸이 `0.100` 이 되어
뒤 자릿수를 이어 칠 수 없고, `0.` 만 쳐도 `0.000` 이 된다.

mayapy 2024 / PySide2 offscreen `QTest.keyClicks("0.123")` 실측:
- tracking **ON** → 텍스트 `'0.100'`, 값 `0.1` (핸들러 쪽 setValue 를 막아도 **그대로** — Qt 자체 재포맷이라)
- tracking **OFF** → `'0.123'`, `0.123`, `valueChanged` 1회(Enter 시). `"0."` 부분 입력은 시그널 없음

**Why:** 사용자가 "숫자를 다 치기도 전에 0 이 자동으로 채워진다" 로 신고한 실제 버그
(A00290_BSTool Shape Editor v01.15). 원인을 `valueChanged` 재진입으로만 보면 못 고친다.

**How to apply:** `valueChanged` 로 값을 씬/파일에 되쓰는 스핀박스는 만들 때
`setKeyboardTracking(False)` (확정은 Enter/포커스 아웃 한 번). 폴링 타이머나 다중 편집이
같은 칸에 `setValue` 하는 구조라면 **포커스를 가진 위젯은 건너뛰는 가드**도 함께 둔다.
관련: [[wip-a00290-shape-editor-tab]], [[mayapy-headless-verify]]
