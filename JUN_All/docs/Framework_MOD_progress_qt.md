---
title: Framework 공용 위젯 — MOD_progress_qt (진행률 팝업)
aliases: [JUN_mod_progress_qt, 진행률 팝업, 프로그레스 바, 게이지 창]
tags: [framework, qt, widget, maya-python]
updated: 2026-09-09
---

# `JUN_mod_progress_qt_v01` — 0~100% 게이지 모달 팝업

`JUN_All/Framework/qt/MOD_progress_qt_v01.py`

오래 걸리는 작업(Apply / Bake / 씬 샘플링)이 도는 동안 **아무 안내 없이 창이 멎어 있는 것**을 막는다.
게이지 + 현재 단계 이름 + 세부 메시지 + 경과 시간을 모달 팝업으로 띄운다.

`A00410_SecondaryMotion` 의 Apply 에 붙이면서 공용으로 올렸다. 그전까지는 툴마다 방식이 달랐다 —
`A00430_DemBone` 은 메인 창에 붙은 `QProgressBar`, `A00420_Wrapper` 는 로그 줄.
**"작업 도는 동안 뜨는 팝업"** 은 어느 툴에서나 같은 모양이므로 위젯 하나로 모았다.

---

## 1. 쓰는 법

```python
from Framework.qt import JUN_mod_progress_qt

dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01(
    self,                                    # 부모 창
    title="Secondary Motion - Apply",
    phases=[("Sampling scene", 30),          # (단계 이름, 가중치)
            ("Solving chains", 5),
            ("Baking keys", 65)])
dlg.start()

try:
    dlg.begin_phase()                        # 1단계로
    core.sample(..., progress=dlg.callback())
    dlg.begin_phase()                        # 2단계로
    core.solve(..., progress=dlg.callback())
    dlg.begin_phase()                        # 3단계로
    core.write(..., progress=dlg.callback())
finally:
    dlg.finish()                             # 성공/실패 무관하게 닫는다
```

`finally` 에 `finish()` 를 두는 것이 중요하다 — 예외로 빠져나가도 팝업은 닫혀야 한다.

---

## 2. 핵심 — **core 는 이 위젯을 모른다**

로직(`app/core`)이 위젯을 import 하면 UI 와 다시 얽힌다. 그래서 core 가 아는 것은 콜백 하나뿐이다.

```python
progress(done, total, message=None)      # 현재 단계 안에서의 상대 진행
```

- `progress` 가 `None` 이면 **아무 일도 하지 않는다** → 진행률 없이도 같은 코드가 그대로 돈다.
  빠른 경로(예: A00410 의 13ms 프리뷰)에는 아예 안 넘기면 된다.
- `total` 이 0 이면 그 단계를 끝난 것으로 본다.
- `dlg.callback()` 이 그 규약에 맞는 함수를 돌려준다.

core 함수는 선택 인자 하나만 받으면 된다.

```python
def bake_keys(self, writes, progress=None):
    total = len(items) * frames
    ...
    if progress:
        progress(done, total, node_name)
```

---

## 3. 단계 가중치 — 실제로 도는 것만 넣는다

한 작업은 보통 비용이 크게 다른 단계로 나뉜다(샘플링 30 / 솔브 5 / 키 굽기 65).
가중치는 **합이 얼마든 비율로만** 쓰이고, 단계마다 `[base, base+span]` 구간이 배정된다.

> **돌지 않는 단계는 목록에서 빼라.** 그러면 나머지 가중치가 **자동으로 재정규화**되어
> 0~100% 를 채운다. 자리를 남겨 두면 게이지가 중간에서 멈추거나 건너뛰는 것처럼 보인다.

```python
phases = []
if need_sample:                              # 캐시가 살아 있으면 이 단계는 없다
    phases.append(("Sampling scene", 30))
phases.append(("Solving chains", 5))
phases.append(("Baking keys", 65))
```

이미 만든 팝업에서 한 단계를 건너뛰어야 하면 `skip_phase()` (그 단계 끝까지 게이지를 채운다).

---

## 4. 갱신 비용 — 값은 늘, 화면은 가끔

`setKeyframe` 을 수천 번 도는 루프에서 매번 `processEvents()` 를 부르면 **그리는 쪽이 더 비싸다.**

- 게이지 값(`setValue`)은 **항상** 반영한다. 다시 그리기를 예약만 하므로 싸다.
- 실제로 화면을 갱신하는 `processEvents()` 만 `_MIN_INTERVAL`(30ms) 간격으로 묶는다.

> **함정**: 값 갱신까지 같이 스로틀하면, **갱신이 뚝 끊긴 순간의 퍼센트가 화면에 영영 안 올라간다**
> (마지막 보고가 스로틀 창 안에 들어오면 그대로 묻힌다). 묶어야 할 것은 `processEvents` 쪽뿐이다.

---

## 5. 취소 · 창 닫기

- 기본은 **닫기 버튼 없음 · Esc 무시**다. 창만 닫히고 작업은 계속 도는 상태를 만들지 않기 위해서다.
- 모달(`ApplicationModal`)이라 도는 동안 툴 버튼을 다시 누를 수 없다.
- `cancellable=True` 면 Cancel 버튼이 생기고 `was_cancelled()` 가 True 가 된다.
  **중단 지점이 안전한 작업에만** 켤 것 — 씬을 반쯤 고쳐 놓고 멈추면 안 되는 작업(A00410 의 Apply 등)은
  기본값 그대로 둔다.

---

## 6. API

| 메서드 | 하는 일 |
|--------|---------|
| `set_phases(phases)` | `[(label, weight), ...]` 또는 `[label, ...]`(균등). 가중치 재정규화 |
| `begin_phase(label=None, index=None)` | 다음(또는 지정) 단계로. 게이지는 단계 시작점으로 |
| `skip_phase()` | 현재 단계를 돌지 않고 끝까지 채운다 |
| `step(done, total, message=None)` | 현재 단계 안에서의 진행 |
| `set_fraction(f, message=None)` | 전체 진행(0.0~1.0)을 직접 지정 |
| `set_message(text)` | 세부 메시지만 갱신 |
| `callback()` | core 에 넘길 `progress(done, total, message=None)` |
| `start()` / `finish()` | 팝업 띄우기 / 닫기 |
| `elapsed()` | 시작 후 경과 초 (로그에 "(3.4s)" 로 붙이기 좋다) |
| `was_cancelled()` | Cancel 눌렸는가 (`cancellable=True` 일 때만) |

---

## 7. 쓰고 있는 툴

| 툴 | 어디에 |
|----|--------|
| `A00410_SecondaryMotion` | Apply — 샘플링 / 솔브 / 키·레이어 기록 |

> 무거운 작업이 있는데 아직 진행 표시가 없는 툴(`A00420_Wrapper` 의 로그 줄,
> `A00430_DemBone` 의 창 내장 게이지)은 이 위젯으로 옮길 수 있다.
