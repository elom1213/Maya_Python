---
name: maya-attr-reorder-deleteattr-undo
description: Maya has no attribute reorder command — deleteAttr + undo sends an attr to the END of the list; three dangers (undo eats other work / undo off loses the attr / not Ctrl+Z undoable)
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1391a069-f7af-476b-85b5-d9bbf6628251
  modified: 2026-09-17T02:30:58.440Z
---

마야에는 **어트리뷰트를 재정렬하는 명령이 없다**. `addAttr` 에도 `attributeQuery` 에도 순서 플래그가
없다. 유일한 방법은 **`deleteAttr` → `cmds.undo()`** — 지웠다 되돌리면 그 어트리뷰트가 **목록 맨 뒤로**
간다. 원하는 순서대로 전부 한 바퀴 돌리면 결과가 정확히 그 순서다.

**Why:** 2026-09-17 A00145 `Attribute > Edit` 의 `Up`/`Down` 을 만들며 mayapy 로 실측했다.
200개 전체 재정렬이 **0.004초**, **값 · 커넥션 · 키가 전부 유지된다**(undo 가 원래 상태를 되돌리는
것이므로 다시 이어 줄 필요가 없다). 사용자 정의 어트리뷰트에만 통한다 — 빌트인은 `deleteAttr` 대상이
아니라 순서를 못 바꾼다.

**How to apply:** 위험 셋을 전부 막고 써야 한다(셋 다 실측 확인).
1. **`deleteAttr` 이 실패한 자리에서 `undo()` 를 부르면 남의 작업이 되돌아간다.** 실측에서 사용자가
   만든 노드가 사라졌다. → **성공했을 때만** undo. 잠긴 어트리뷰트는 잠금을 풀고 옮긴 뒤 다시 잠근다.
2. **undo 가 꺼져 있으면 어트리뷰트를 그대로 잃는다.** 시작 전에 `cmds.undoInfo(query=True, state=True)`
   를 보고 꺼져 있으면 **아무것도 하지 않는다.**
3. **이 작업 자체는 `Ctrl+Z` 로 안 돌아간다.** delete 와 undo 가 짝이라 큐에 아무것도 안 남고, 오히려
   그 뒤 `Ctrl+Z` 는 **그 전에 하던 작업**을 취소한다. → 실행할 때마다 로그로 알린다.
- undo 뒤 `attributeQuery(exists=True)` 로 **정말 돌아왔는지 확인**하고, 아니면 거기서 멈춘다.

**2026-09-17 사용자 보고: 순서를 바꾸자 연결이 자리 기준으로 엇갈렸다**(`a->b`). mayapy 17가지 변형 +
**별도 마야 GUI(2024, 병렬 평가) 실제 핸들러**로도 재현 안 됨(이름·API·값 흐름 전부 유지). 원인 미확인 —
사용자 씬 조건을 모른다. 대응: v01.46 `Maintain connections`(기본 ON) = 옮기기 전 연결을 플러그 이름으로
적고 옮긴 뒤 **어긋난 것만** 복구. `skipConversionNodes=True` 로 비교해야 undo 가 unitConversion 을 다른
이름으로 살렸을 때 멀쩡한 연결을 끊지 않는다. 다시 보고되면 **씬 조건(노드 타입·레퍼런스·어떻게 확인했는지)**부터 물을 것.
Node Editor 는 재정렬 후에도 행을 옛 순서로 그린다(표시만 다름).
**미해결 기존 결함**: 컴파운드는 자식 `deleteAttr` 실패로 **순서가 반쯤 바뀐 채** 멈춘다 · alias 붙은 어트리뷰트는 못 옮긴다.

**GUI 마야로 재현하는 법**: 사용자 세션은 건드리지 말고 `maya.exe -noAutoloadPlugins -command "python(\"exec(open(r'x.py').read())\")"`
로 **새 인스턴스**를 띄우고, 스크립트는 `maya.utils.executeDeferred` 로 실행 → 결과를 파일로 쓰고 `cmds.quit(force=True)`.
mayapy standalone 에서 `cmds.window` 를 만들면 프로세스가 죽는 것과 달리 여기선 실제 UI · Qt 캡처(`QWidget.grab`)까지 된다.
- 구현: `tools/A00145_RigConnect/app/core/attr_order_manager.py` (`plan_order` 는 maya 비의존 순수 함수).

관련: [[a00145-attribute-tab-blendshape-alias]], [[undo-chunk-by-default]], [[mayapy-headless-verify]]
