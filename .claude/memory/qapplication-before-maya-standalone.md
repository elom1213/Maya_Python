---
name: qapplication-before-maya-standalone
description: mayapy 로 Qt UI 를 테스트할 땐 QApplication 을 maya.standalone.initialize() 이전에 만들어야 한다
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4f6580d4-4bc6-4134-a627-7dc361a23170
  modified: 2026-08-06T08:38:28.516Z
---

mayapy 에서 PySide 위젯을 만들어 테스트할 때, `QApplication` 을
`maya.standalone.initialize()` **뒤에** 만들면 첫 `QWidget()` 에서 **트레이스백 없이
프로세스가 그대로 죽는다**(exit 127). 앞에서 만들면 정상 동작한다.

```python
import os; os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide2.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])   # 반드시 먼저
import maya.standalone; maya.standalone.initialize(name="python")
import maya.cmds as cmds                            # 그 다음
```

출력이 잘려 원인이 안 보이면 `PYTHONUNBUFFERED=1` 로 실행한다(버퍼가 안 비워진 채 죽는다).

**Why:** A00290 Mix Targets 탭 UI 를 헤드리스로 검증하려다 두 번 헤맸다. 순서만 바꾸면
전체 MainWindow(4탭)까지 offscreen 으로 만들어 실제 핸들러를 호출해 볼 수 있다.

**How to apply:** maya.cmds + PySide 를 함께 쓰는 테스트 스크립트는 위 순서를 지킨다.
창 전체가 안 뜨는 툴은 탭 관련 메서드만 `QWidget` 호스트 클래스에 옮겨 붙여 구동해도 된다.
관련: [[mayapy-headless-verify]], [[wip-a00290-mix-targets-tab]]
