---
name: framework-progress-widget
description: Framework 공용 진행률 팝업(MOD_progress_qt_v01) — 오래 걸리는 작업에 게이지 창이 필요하면 새로 만들지 말고 이걸 쓴다
metadata: 
  node_type: memory
  type: project
  originSessionId: fb4a8dc4-f323-4f72-8ea8-9bbb59d15251
  modified: 2026-09-09T00:45:54.985Z
---

**`Framework/qt/MOD_progress_qt_v01.py` → `JUN_mod_progress_qt_v01`** (2026-09-09 승격,
`A00410_SecondaryMotion` Apply 에 처음 적용). 0~100% 게이지 + 단계 이름 + 세부 메시지 + 경과 시간을
띄우는 **모달 팝업**. 문서: `docs/Framework_MOD_progress_qt.md`.

```python
from Framework.qt import JUN_mod_progress_qt
dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01(
    self, title="... - Apply",
    phases=[("Sampling scene", 30), ("Solving chains", 5), ("Baking keys", 65)])
dlg.start()
try:
    dlg.begin_phase(); core.sample(..., progress=dlg.callback())
    dlg.begin_phase(); core.write(...,  progress=dlg.callback())
finally:
    dlg.finish()                     # 예외로 빠져나가도 닫히게 finally 에
```

**Why:** 툴마다 진행 표시가 제각각이었다(A00430 은 창 내장 `QProgressBar`, A00420 은 로그 줄).
"작업 도는 동안 뜨는 팝업" 은 어느 툴에서나 같은 모양이라 위젯 하나로 모았다.

**How to apply:**
- **core 는 위젯을 모른다** — `progress(done, total, message=None)` **콜백만** 받는다.
  `None` 이면 아무 일도 안 하므로 **빠른 경로(프리뷰 등)에는 그냥 안 넘기면** 예전 코드 그대로다.
  core 함수 시그니처에 `progress=None` 하나만 추가하는 식으로 붙인다.
- **돌지 않는 단계는 목록에서 빼라.** 가중치가 자동 재정규화되어 0~100% 를 채운다.
  자리를 남겨 두면 게이지가 중간에서 멈추거나 건너뛰는 것처럼 보인다(`skip_phase()` 도 있다).
  가중치는 **실측 비용**으로 정한다 — 노드×프레임 `setKeyframe` 같은 기록 단계가 압도적으로 무겁다.
- **★ 값 갱신과 화면 갱신을 같이 스로틀하면 안 된다.** 비싼 건 `setValue` 가 아니라
  `QApplication.processEvents()` 다. 둘 다 30ms 로 묶었더니 **갱신이 뚝 끊긴 순간의 퍼센트가 화면에
  영영 안 올라갔다**(마지막 보고가 스로틀 창에 묻힌다 — 헤드리스 테스트가 잡았다).
  → 값은 늘 반영, `processEvents` 만 간격으로 묶는다.
- **닫기 버튼 없음 · Esc 무시 · ApplicationModal** 이 기본이다. 창만 닫히고 작업은 계속 도는 상태를
  만들지 않고, 도는 중에 버튼을 다시 못 누르게 한다. `cancellable=True` 는 **중단해도 안전한 작업에만**.
- 끝나면 `dlg.elapsed()` 로 로그에 `(3.4s)` 를 붙여 주면 다음번 대기 감각이 생긴다.
- 아직 안 옮긴 후보: `A00420_Wrapper`(로그 줄), `A00430_DemBone`(창 내장 게이지).

관련: [[wip-a00410-secondarymotion]], [[framework-timerange-widget]], [[framework-expand-widget]],
[[prefer-pyside-for-new-tools]], [[mayapy-headless-verify]]
