---
name: reload-stale-instance-super
description: "Framework 위젯은 zero-arg super() 만 — run(True) 가 Framework 를 reload 하면 super(Class, self) 는 옛 인스턴스에서 TypeError"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f0dafff4-39d2-4341-8b56-4bc9271dd7f4
  modified: 2026-09-18T08:47:07.811Z
---

Framework(`JUN_All/Framework/**`) 클래스에서는 `super(ClassName, self)` 대신 **`super()`** 를 쓴다.

**Why:** 툴 `run(True)` 는 DEV_MODE 에서 `reload_for_tool` 로 `Framework` 전체를 `importlib.reload` 한다.
이미 떠 있는 다른 툴 창의 위젯은 옛 클래스 인스턴스로 남는데, 모듈 전역 이름은 새 클래스를 가리켜
`super(type, obj): obj must be an instance or subtype of type` 가 난다. 2026-09-18 A00380 Apply By Weight
중 `MOD_log_qt_v01.eventFilter`(툴 창에 걸린 필터라 이벤트마다 호출)에서 터졌다. `super()` 는 `__class__` 셀로
정의 클래스에 묶여 리로드와 무관하다. 32곳 일괄 치환, mayapy 로 재현·검증.

**How to apply:** 새 Framework 위젯을 만들거나 옛 코드를 옮길 때 `super()` 로. 툴 자신의 클래스는 run 이 옛 창을 닫으므로
덜 급하지만, 다른 툴 창에 필터/시그널로 오래 붙는 객체라면 같은 함정이다. 관련 [[framework-log-widget]]
