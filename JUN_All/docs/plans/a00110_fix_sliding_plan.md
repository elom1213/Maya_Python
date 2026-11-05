# A00110_animTool_V02 — Bake > Fix Sliding 계획서

- 작성: 2026-11-04 (현재 V02 = v02.47) → 구현 버전 **v02.48**
- 상태: **v02.48 구현 완료 (2026-11-04)** — 시험 30/30 · UI 11/11, KANA 실측(6830 f · 발 둘 · 191 구간 · 34 s · 구간 안 월드 속도 0). 마야 GUI 확인 아직.
  - 계획과 달라진 점: 디버그 노드는 undo 청크 밖이 아니라 **undo 기록을 끈 채** 만든다 — 밖에서 만들면 Ctrl+Z 한 번이 디버그 노드만 되돌린다.
    D(Lock)는 Pose 축이 아닌 멤버 채널에도 a' 에 키를 하나 더 찍어(값 그대로) [a', b] 를 상수로 만든다.
- 이 문서만 보고 구현할 수 있도록 결정 사항 · 파일 위치 · 알고리즘 · UI · 검증을 모두 적는다.
- 관련 계획서: [a00110_hold_layer_blend_plan.md](a00110_hold_layer_blend_plan.md) (Shift+A Layer Blend Key, v02.39~47)
- 개정: 2026-11-04 — 이웃 구간 블렌드 침범 문제(§9)에 대해 **B → A → D 순서 적용, G 기본 4 프레임** 결정 반영. 대안 A~E 를 §9 에 기록.

---

## 1. 배경 · 요구사항

### 1.1 `_SmartLayer` 의 Fix Sliding (참고만)

마야에서 쓰는 상용 패키지 `C:\Users\USER\Documents\maya\scripts\_SmartLayer`. 코어 · UI 가 전부 `__hybrid__/*.pyc` 이고
`.py` 는 로더 스텁이다. **디컴파일하지 않는다** — 라이선스 당사자는 벤더이고 이 저장소는 공개 포트폴리오다
(Counter Layer 계획서 §2-3, Curve Filters 이식 때와 같은 결정). 참고는 **사용자에게 보이는 문자열(툴팁)과 UI 구성**까지.

툴팁에서 읽은 원리(사용자 관찰과 대체로 같다):

| SmartLayer 툴팁 | 내용 |
|---|---|
| Fix Initial Feet Sliding | 속도 분포로 "스텝" 타이밍을 정한다. 속도 < Threshold 인 부분은 정지, 그 위는 움직임. 그 타이밍으로 미끄러짐을 상쇄하는 포즈를 만들고 속도 분포로 블렌드한다 |
| Speed Threshold | 속도가 이 값보다 작으면 0 으로 친다. **최대 속도의 %**. 좋은 모캡 1~2 %, 나쁜 데이터 15 %+ |
| Speed Smooth Interval | 나쁜 모캡은 프레임마다 속도가 튀어 가짜 스텝이 생긴다 → 스무딩 |
| Speed Components | 속도 벡터에 쓸 축(기본 X Y Z, 세로축을 빼면 수평 속도만) |

사용자 관찰: 버튼을 누르면 `_debug_speed` 노드에 원래 속도 · 스무딩된 속도 · Threshold · 결과 속도 커브가 생기고,
`SmartLayer` 레이어가 생겨 스무딩 값 < Threshold 인 프레임의 결과 속도를 0 으로 만든다.

### 1.2 원하는 결과 (사용자 요구, 2026-11-04)

> Threshold 보다 스무딩된 속도가 작은 구간을 **[a, b]** 라 할 때, **[a, b] 구간의 그 오브젝트의 위치 · 회전 어트리뷰트 키를 선택하고
> Layer Blend Key 가 체크된 상태로 Shift+A 를 누른 결과**가 되게 한다. 사용자가 양의 정수 **M** 을 입력하고,
> **[a, b] 길이가 M 보다 클 때만** 적용한다. 적용할 오브젝트를 리스트업하는 **TSL** 이 있어야 한다.

### 1.3 결정 사항 (2026-11-04 사용자 답)

| # | 질문 | 결정 |
|---|------|------|
| 1 | 구간 길이 조건 방향 ("M 이 길이보다 클 때" 의 글자 뜻은 짧은 구간만) | **길이 > M 일 때만 적용** (짧은 정지는 노이즈로 보고 건너뜀 = Min span) |
| 2 | Hold 할 채널 ("위치, 이동") | **translate + rotate** (UI 에 T / R 체크, 기본 둘 다) |
| 3 | Threshold 단위 | **최대 속도의 %** (오브젝트마다 스무딩된 속도의 최댓값 기준, 기본 2 %) |
| 4 | 이웃 구간의 블렌드 [a−N, a] 가 앞 구간 안으로 들어올 때 (예: [0, 10] · [12, 20], N=5 → f7 키 → f7~f10 이 다시 움직임) | **B → A → D 순서로 적용**, Merge gap **G 기본 4 프레임** (§3.3a, §3.4, 대안 비교는 §9) |

### 1.4 구현자가 정한 해석 (이 문서에서 확정 — 바꾸려면 사용자 확인)

| 항목 | 정함 | 이유 |
|---|---|---|
| 속도 | **월드 위치**의 프레임당 이동 거리 (`worldMatrix[0]` 의 translation, 선택 축만) | 미끄러짐은 월드에서 보인다. SmartLayer 기본 driver 도 Position |
| 속도 측정 상태 | **지금 씬의 최종 평가값**(모든 레이어 켠 채) | 사용자가 보는 움직임 그대로 |
| 정지 프레임 판정 | `smoothed[f] < threshold` (**엄격한 작음**) | 요구 "작은 구간" |
| 구간 길이 L | **프레임 수** `b - a + 1`. 적용 조건 `L > M` | |
| "Shift+A 결과" 재현 | Hold 대상 커브 = 각 채널의 **보기 레이어 커브**(Hot Key > Main `Run only when viewing`, 기본 BaseAnimation) 위 [a, b] 안의 키를 "선택" 한 것으로 보고 Hold. Layer Blend = Hot Key > Main 의 레이어 · N · Pose/Current 설정 그대로, 기준 프레임 = 선택 키의 최소 시간(v02.47 규칙) | Shift+A 를 누를 때 사용자는 기본적으로 BaseAnimation 을 보며 그 커브 키를 고른다(v02.43 게이트) |
| Layer Blend 켜짐 여부 | 이 탭의 `Layer Blend Key` 체크(기본 ON)가 정한다. Hot Key > Main 의 `Layer Blend Key` 체크 · 보기 게이트는 **무시**(일괄 처리는 보는 레이어와 무관) | 요구 "Layer Blend Key 가 체크된 상태로" |
| 처리 순서 | 오브젝트마다, 구간을 **시간순**으로 하나씩 "Shift+A" 한다(앞 구간의 레이어 키가 뒤 구간의 Current 값에 반영되게) | 사람이 구간마다 Shift+A 를 차례로 누른 결과와 같게 |
| "Shift+A 결과" 와의 관계 | 결정 #4 의 B · A · D 는 Shift+A 를 **보정**한다. UI 에서 셋을 끄면(G=0, Clamp 끔, Lock 끔) 순수 Shift+A 재현이 된다 — 핵심 대조 시험은 그 상태로 한다(§6-6). **v02.52 개정**: Shift+A 자체가 b 에 레이어 키를 찍게 되어(= D) 순수 Shift+A = G=0 · Clamp 끔 · **Lock 켬** | 요구의 정의를 시험으로 지키면서 보정을 얹기 위해 |
| 디버그 | `_debug_speed` 노드에 4 커브(원래 · 스무딩 · Threshold · 결과) — 옵션, 기본 ON | 사용자가 결과를 눈으로 검증 |

---

## 2. 현재 코드 위치 (v02.47 기준)

경로 기준: `JUN_All/tools/A00110_animTool_V02/app/`

| 무엇 | 위치 |
|------|------|
| Bake 하위 탭 목록 | `ui/main_window.py` `BAKE_PAGES` (Bake · Locator · Counter Layer · Merge Layers) |
| TSL · 구간 위젯 예 | `ui/main_window.py` `_build_locator_bake_tab()` — `JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title=, select_label=, list_min_height=, log_callback=)`, `JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(start_value=, end_value=, log_callback=)` + `Get Timeline` |
| 진행 팝업 예 | `ui/main_window.py` 의 LOC + Anim 실행부 `JUN_mod_progress_qt.JUN_mod_progress_qt_v01(self, title=, phases=)`, 코어는 `progress(done, total, message)` + `progress.phase(name)` (`core/locator_bake_manager.py`) |
| Hold 로직 | `core/keyframe_manager.py` `KeyframeManager.hold_selected_keys()` — 커브마다 start=min, end=max 선택 시간, `(start+EPS, end]` cutKey, end 에 start 값, start out / end in 탄젠트 flat. 키 < 2 개면 skip |
| Shift+A 진입점 | `core/hotkey_manager.py` `HotkeyManager.run_hold()` — `selected_objects()` → `range_start()` → `capture_current(frame=a)` → undo_chunk(Hold + `apply(frame=a)`) |
| Layer Blend 로직 | `core/hold_layer_manager.py` `HoldLayerManager` — `load_settings()`(optionVar 원본), `effective_axes()`(체크 ∪ Current), `view_gate()`, `values_at(plugs, t)`, `capture_current(objects, frame)`, `apply(objects, frame, current_values)` |
| 레이어 커브 찾기 | `core/layer_key_manager.py` `LayerKeyManager.layer_curve(plug, layer, root)` (Base 에 없으면 plug 직결 커브) · `root_layer()` |
| 월드 샘플링 선례 | `core/counter_layer_manager.py` `_snapshot()` — `currentTime` 루프 + `getAttr(o + ".worldMatrix[0]")` |
| 정지 구간 선례 | `core/counter_layer_manager.py` `detect_spans()` (포즈 변화 허용오차 방식 - **이번엔 속도 % 방식이라 재사용하지 않는다**, 구간 자르기 · min_span 처리만 참고) |
| 화면 갱신 멈춤 | `Framework.core.maya_refresh.suspend_refresh` |
| undo 묶기 | `Framework.core.maya_undo.undo_chunk` (중첩 OK) |
| 버전 | `config/version.py` `VERSION = "02.47"` |

---

## 3. 알고리즘

오브젝트 목록 `objs`(TSL), 구간 `[S, E]`(정수 프레임), 옵션:
`axes=(x, y, z)` · `smooth=W` · `threshold_pct=P` · `merge_gap=G`(기본 4) · `min_span=M` · `translate` · `rotate` · `layer_blend` ·
`clamp_blend`(대안 A, 기본 ON) · `lock_end`(대안 D, 기본 ON) · `debug`.

### 3.1 샘플링 (한 번의 시간 루프로 모든 오브젝트)

```
with suspend_refresh():
    now = currentTime(q)
    for f in S..E:
        currentTime(f)
        for o in objs: pos[o].append(getAttr(o.worldMatrix[0])[12:15])
    currentTime(now)          # finally 에서 반드시 복원
```

- **`getAttr -time` · API `MDGContext` 금지** — 레이어가 있으면 Base 값만 준다(v02.47 실측). `currentTime -update false` 도 옛 값.
- 진행: 단계 `Sampling`, 프레임마다 `progress(i, n)`(스로틀 금지 — [[framework-progress-widget]]).
- 시간 이동이 undo 큐를 채우지 않도록 `undoInfo(stateWithoutFlush=False)` 로 감싸고 끝에 되돌린다(`HoldLayerManager.values_at` 과 같은 방식).

### 3.2 속도 · 스무딩 · Threshold (순수 함수 — 마야 없이 시험)

```python
def speeds(points, axes):          # points: [(x,y,z)] 길이 n
    d(i) = sqrt(sum(((p[i][k] - p[i-1][k]) ** 2) for k in 0..2 if axes[k]))
    v = [d(1)] + [d(i) for i in 1..n-1]    # 첫 프레임은 다음 프레임과의 차 (길이 n 유지)

def smooth(values, window):        # 중심 이동 평균, window = W (1 이면 그대로)
    h = W // 2;  out[i] = mean(values[max(0, i-h) : min(n, i+h+1)])   # 가장자리는 창이 줄어든다

threshold = P / 100 * max(smoothed)
```

- `max(smoothed) == 0`(전혀 안 움직임) → 그 오브젝트는 **건너뛰고 경고**: `"[Warning] Fix Sliding: <obj> does not move in <S>-<E>. Skipped."`
- W 는 짝수여도 된다(h = W//2 로 창은 홀수 2h+1).

### 3.3 정지 구간

```python
def still_spans(smoothed, start, threshold):
    # smoothed[i] < threshold 인 연속 구간 -> [(a, b)] (프레임 번호, a = start + i0, b = start + i1)

spans = merge_gaps(spans, G)                                   # §3.3a 대안 B — 반드시 M 판정 **전에**
apply_spans = [(a, b) for (a, b) in spans if (b - a + 1) > M]
short_spans = 나머지 (로그에만)
```

- 구간이 `S` 나 `E` 에 닿아도 그대로 쓴다(잘림은 [S, E] 로 자연히).

### 3.3a 짧은 틈 합치기 — 대안 B (Merge gap G, 기본 4)

```python
def merge_gaps(spans, G):
    # spans 는 시간순. 이웃 (a1, b1), (a2, b2) 사이의 '움직인 프레임 수' gap = a2 - b1 - 1.
    # gap <= G 면 하나로 합친다 -> (a1, b2). 합친 결과에 대해 다시 다음 이웃과 비교(연쇄 합치기).
    # G = 0 이면 합치지 않는다(이웃 구간은 정의상 gap >= 1).
```

- 예: [0, 10] · [12, 20] → gap 1 ≤ 4 → **[0, 20] 한 구간**. [0, 10] · [16, 25] → gap 5 > 4 → 그대로 둘.
- 합친 구간의 길이로 M 을 판정한다(짧은 두 조각이 합쳐져 M 을 넘으면 적용).
- 로그: `"<o>: merged [0-10] + [12-20] -> [0-20] (gap 1 <= G 4)"`.
- 디버그 `n_result` 예측(Preview)은 합친 구간 기준으로 0.

### 3.4 구간마다 "Shift+A" 재현 (시간순)

오브젝트 `o`, 구간 `(a, b)`:

1. **채널** = `translate` 면 `translateX/Y/Z`, `rotate` 면 `rotateX/Y/Z`. 잠긴 채널 · 커브 없는 채널은 건너뜀.
2. **Hold 대상 커브** = 채널마다 `LayerKeyManager.layer_curve(o.ch, hold_layer, root)`. `hold_layer` = Hot Key > Main 의
   `view_layer` 설정(`HoldLayerManager.load_settings()["view_layer"]`, "" = 루트). 없으면 그 채널 skip.
3. **"선택된 키" 시간** = 그 커브의 `[a, b]` 안 키 시간들(`keyframe(crv, q, time=(a, b), timeChange)`). 2 개 미만이면 그 커브는 Hold skip
   (Shift+A 와 같다 — 모캡처럼 매 프레임 키면 항상 2 개 이상).
4. **기준 프레임** `a'` = 모든 대상 커브의 "선택된 키" 최소 시간(`range_start` 와 같은 규칙). 키가 하나도 없으면 `a' = a`.
5. **Current 값** — `layer_blend` 면 `HoldLayerManager.capture_current([o], frame=a', force=True)` 를 **Hold 전에**.
6. **블렌드 시작 t0** — 대안 A (`clamp_blend`, 기본 ON):
   `t0 = max(a' - N, b_prev)` — `b_prev` = **같은 오브젝트에서 바로 앞에 적용한 구간의 끝**(없으면 클램프 없음).
   §3.3a 뒤에는 이웃 구간 gap ≥ G+1 ≥ 1 이므로 항상 `b_prev < a'` → `t0 < a'` 가 보장된다.
   예: [0, 10] · [16, 25], N=8 → 두 번째 구간 t0 = max(8, 10) = **f10** (f8 이면 f8~f10 이 다시 움직였다).
   `clamp_blend` 끔이면 `t0 = a' - N`(Shift+A 그대로).
7. undo 청크 안에서:
   - `KeyframeManager.hold_range(curves, a, b)` (§4.1 — `hold_selected_keys` 의 커브 처리를 그대로)
   - `layer_blend` 면 `HoldLayerManager.apply(objects=[o], frame=a', current_values=cur, force=True,
     ramp_start=t0, hold_end=(b if lock_end else None))` (§4.2)
   - **대안 D** (`lock_end`, 기본 ON) — `apply` 안에서: 이번에 키를 찍은 모든 레이어 채널(t0 의 멤버 채널 + a' 의 Pose 축)에
     **b 에도 키**를 찍는다. 값 = **a' 에서의 레이어 값**(a' 키를 찍은 뒤 레이어 커브를 a' 에서 평가한 raw 값, `_key_raw`).
     그리고 그 커브의 `a'` out 탄젠트 · `b` in 탄젠트를 **flat** 으로 — 값이 같아도 auto/spline 탄젠트는 이웃 키 때문에 부풀 수 있다.
     결과: [a', b] 안에서 레이어 값이 상수 → 다음 구간의 키가 들어와도 고정 구간 내부는 안 움직인다.
     `b == a'` 면 생략. b 에 이미 키가 있으면 덮어쓴다(결정 1 과 같은 규칙).
   - A 와 D 를 같이 쓰면: 다음 구간의 t0 ≥ 이 구간의 b → 다음 블렌드는 이동 프레임 (b, a₂') 에서만 일어난다.
8. 결과 줄 수집: `"<o>: [a-b] (L f) held <k> curve(s), layer keys f<t0> / f<a'>[ / f<b>]"` (+ `"(blend start clamped from f<a'-N>)"`)
   또는 Layer Blend 메시지(경고 포함) 그대로.

> 전체 실행은 **바깥 undo_chunk 하나** — Ctrl+Z 한 번에 모든 오브젝트 · 구간이 되돌아간다.

### 3.5 디버그 노드 `_debug_speed` (옵션, 기본 ON)

- 실행마다 기존 `_debug_speed` 를 지우고 새로 만든다(`cmds.createNode("transform", name="_debug_speed")`, 월드 루트).
- 오브젝트마다 접두사 `n` = 짧은 이름(네임스페이스 `:` · `|` → `_`, 겹치면 `_2` …). 어트리뷰트(double, keyable):
  `n_speed`(원래) · `n_smooth`(스무딩) · `n_threshold`(상수) · `n_result`(결과).
- `n_result` = **적용 뒤 다시 샘플링한 실제 속도**(§3.1 한 번 더, 스무딩 없이). Preview 에서는 예측값
  (`speed` 를 적용될 구간에서 0).
- 키 쓰기는 프레임 수가 많으므로 **API `MFnAnimCurve.create` + `addKeys(times, values)`**(animCurveTU, 시간은 `MTime(f, uiUnit)`).
  `setKeyframe` 반복은 쓰지 않는다.
- 노드에 문자열 어트리뷰트 `info` = `"S-E, W, P%, M, axes"`(나중에 무슨 설정이었는지).
- 이 노드는 **undo 청크 밖**에서 만든다(Ctrl+Z 로 키를 되돌려도 디버그는 남아 비교할 수 있게). 단 Preview 는 키를 안 바꾸므로 상관없음.

### 3.6 Preview Spans (키 변경 없음)

§3.1 ~ §3.3 만 하고 로그에 오브젝트마다:
`"<o>: max <v> /f, threshold <t> (<P>%) - apply [a-b] (L f), ... ; skip (<= M f) [c-d] ..."`. `debug` 면 디버그 노드(결과 = 예측).

---

## 4. 코드 변경

### 4.1 `core/keyframe_manager.py` — Hold 를 커브 단위로 쪼갠다

```python
@staticmethod
def _hold_curve(crv, times):
    """hold_selected_keys 의 커브 하나 처리. times = 그 커브에서 '선택된' 키 시간. 반환 True(처리) / False(skip)."""
    # 기존 본문 그대로: len < 2 -> False, start/end, start 값, cutKey (start+EPS, end], setKeyframe end, flat 탄젠트

@staticmethod
def hold_selected_keys():           # 동작 불변 - 내부만 _hold_curve 사용

@staticmethod
def hold_range(curves, a, b):
    """커브들에서 [a, b] 안의 키를 선택한 것처럼 Hold. 반환 (done, skipped, start_time or None)."""
```

- **회귀**: `tests/test_hold_layer_blend.py` 의 RH · VG2 · RA 가 그대로 통과해야 한다(Shift+A 동작 불변).

### 4.2 `core/hold_layer_manager.py` — `force` · `ramp_start` · `hold_end` 인자

- `capture_current(objects=None, frame=None, force=False)` · `apply(objects=None, frame=None, current_values=None, force=False)`.
- `force=True` 면 `enabled` 검사와 `view_gate` 를 건너뛴다. 나머지(레이어 존재 · 잠김 · 멤버 · 축 · 메시지)는 그대로.
- `run_hold` 는 바꾸지 않는다(force=False).
- `apply(..., ramp_start=None, hold_end=None)` 추가 (Fix Sliding 전용, Shift+A 는 안 씀):
  - `ramp_start` 가 있으면 `t0 = ramp_start` (없으면 예전처럼 `t1 - N`). `ramp_start >= t1` 이면 경고하고 레이어 키 생략.
  - `hold_end` 가 있고 `> t1` 이면 대안 D(§3.4-7): 이번에 키를 찍은 채널마다 b 에 a' 레이어 값 키 + a' out / b in 탄젠트 flat.
  - 메시지 프레임 표기: `(f<t0> -> f<t1>[ -> f<b>])`.

### 4.3 새 파일 `core/fix_sliding_manager.py` (maya.cmds, UI 비의존)

```python
class FixSlidingManager:
    DEFAULT_SMOOTH = 5
    DEFAULT_THRESHOLD_PCT = 2.0
    DEFAULT_MIN_SPAN = 3
    DEFAULT_MERGE_GAP = 4          # 대안 B, 0 = 합치지 않음
    DEBUG_NODE = "_debug_speed"
    PHASES = ("Sampling", "Applying", "Debug")

    # ---- 순수 함수 (마야 없이 시험) ----
    @staticmethod
    def speeds(points, axes=(True, True, True)) -> list
    @staticmethod
    def smooth(values, window) -> list
    @staticmethod
    def still_spans(smoothed, start, threshold) -> list[(a, b)]
    @staticmethod
    def merge_gaps(spans, gap) -> (merged, merges)           # 대안 B, merges = [((a1,b1),(a2,b2))] 로그용
    @staticmethod
    def split_spans(spans, min_span) -> (apply, short)       # L = b - a + 1 > M
    @staticmethod
    def blend_starts(spans, n, clamp=True) -> [t0, ...]       # 대안 A 의 t0 계산 (순수 함수, a' 는 호출부가 넘김)

    # ---- 마야 ----
    @staticmethod
    def sample_positions(objs, start, end, progress=None) -> {obj: [(x, y, z), ...]}
    @classmethod
    def analyze(cls, objs, start, end, axes, smooth, threshold_pct, min_span, progress=None) -> {obj: result}
        # result = {"speed", "smooth", "threshold", "max", "apply", "short", "still": bool}
    @classmethod
    def preview(cls, objs, start, end, ..., debug=True, progress=None) -> (results, lines)
    @classmethod
    def run(cls, objs, start, end, axes, smooth, threshold_pct, min_span, merge_gap=4,
            translate=True, rotate=True, layer_blend=True, clamp_blend=True, lock_end=True,
            debug=True, progress=None) -> (count, lines)
    @staticmethod
    def write_debug(results, start, end, info) -> node
```

- 검증 먼저(아무것도 안 바꾸고 반환): 오브젝트 없음 · 씬에 없음 · `end <= start` · T/R 둘 다 꺼짐 · 축 셋 다 꺼짐 ·
  `layer_blend` 인데 Hot Key > Main 레이어 미선택 / 없음 / 잠김 → 그 이유 한 줄(영어, `[Warning]`).
- `run` 순서: 검증 → 분석(Sampling) → undo_chunk { 오브젝트마다 · 구간 시간순 §3.4 } (Applying) → 디버그(재샘플 포함, Debug).
- 반환 `lines` 마지막에 요약: `"Fix Sliding: <k> object(s), <s> span(s) fixed, <m> merge(s) (G=<G>), <t> short span(s) skipped (M=<M>)."`

### 4.4 `core/__init__.py`

`from .fix_sliding_manager import FixSlidingManager` + `__all__`.

### 4.5 UI — `ui/main_window.py`

`BAKE_PAGES` 에 Counter Layer 다음으로 추가:

```python
("Fix Sliding", "Fix Sliding - find the frames where each listed object stands still (smoothed world "
 "speed below a % of its max speed) and, for every still span longer than Min span, do what Shift+A "
 "does on that span: Hold its translate / rotate keys and Layer Blend Key", "_build_fix_sliding_tab"),
```

`_build_fix_sliding_tab()` (문자열 전부 영어):

```
[Fix Sliding List  (TSL)            ]   self.fs_tsl  (title="Fix Sliding List", select_label="Select Objects")
Frame Range  [Start][End] Get Current · Get Sel Range · [Get Timeline]   self.fs_range
Speed
  Components  [x] X  [x] Y  [x] Z                       self.cb_fs_x / _y / _z
  Smooth interval  [ 5 ] frames                         self.sp_fs_smooth   (QSpinBox 1~200)
  Threshold        [ 2.00 ] % of max speed              self.sp_fs_threshold (QDoubleSpinBox 0.01~100, 2 자리)
Spans
  Merge gap (G)    [ 4 ] frames  - join spans whose gap is this short   self.sp_fs_merge_gap (0~1000, 0 = off)
  Min span (M)     [ 3 ] frames  - fix only spans longer than this   self.sp_fs_min_span (1~10000)
Keys
  [x] Translate  [x] Rotate                             self.cb_fs_t / _r
  [x] Layer Blend Key  (Hot Key > Main: <layer>, N=<N>)  self.cb_fs_layer_blend + self.lbl_fs_layer_blend
      [x] Clamp blend start to the previous span        self.cb_fs_clamp   (대안 A, Layer Blend 끄면 비활성)
      [x] Lock the layer through each span (key at b)   self.cb_fs_lock    (대안 D, Layer Blend 끄면 비활성)
  [x] Debug speed curves (_debug_speed)                 self.cb_fs_debug
[ Preview Spans ]  [ Fix Sliding ]                      self.btn_fs_preview / self.btn_fs_run
```

- 툴팁(요지):
  - Threshold: `"A frame is 'still' when the smoothed speed is below this % of the object's max smoothed speed.\nGood mocap: 1-2 %, noisy data: 15 % or more."`
  - Min span: `"Only still spans longer than this many frames are fixed. Shorter ones are treated as noise and left alone."`
  - Merge gap: `"Two still spans with at most this many moving frames between them are treated as one span\n(checked before Min span). 0 = never merge."`
  - Clamp: `"Start each blend (a - N) no earlier than the end of the previous fixed span, so the layer never\nstarts moving inside a span that is already fixed."`
  - Lock: `"Also key the layer at the span end b with the same value as at a (flat tangents), so the layer\nstays constant through the whole span."`
  - Layer Blend Key: `"For each fixed span [a, b] also key the layer chosen in Hot Key > Main at a and a - N\n(Pose Key axes / Current), exactly like Shift+A with Layer Blend Key on."`
  - Fix Sliding: `"For each still span longer than Min span: Hold the translate / rotate keys inside it\n(the curves of the Hot Key > Main 'Run only when viewing' layer) and Layer Blend Key. One undo."`
- `lbl_fs_layer_blend` 는 탭이 보일 때 · 버튼 누를 때 `HoldLayerManager.load_settings()` 로 갱신(`<layer>` 없으면 `(no layer chosen)` 빨강 대신 `[Warning]` 문구).
- 실행 = 진행 팝업(`phases=FixSlidingManager.PHASES`), 결과 `lines` 를 로그에 그대로. 끝나면 View > Layers 갱신(`on_al_refresh(quiet=True)`, 있을 때).
- 설정 기억: optionVar `JUN_A00110_fixSliding_<key>`(smooth · threshold · merge_gap · min_span · x/y/z · t/r · layer_blend · clamp · lock · debug). 창을 열 때 복원.
- 창 높이: 공용 tabFit 이 이미 걸려 있다(새 하위 탭도 자동). 확인만.

---

## 5. 함정 · 위험 (구현 시 mayapy 로 실측)

1. **레이어가 있으면 `getAttr -time` / `MDGContext` 는 Base 값만** — 샘플링 · 재샘플은 반드시 `currentTime` 루프([[wip-a00110-hold-layer-blend]] v02.47).
2. **로컬 채널 Hold ≠ 월드 정지** — 부모(글로벌 컨트롤 등)가 그 구간에 움직이면 로컬 T/R 을 고정해도 월드는 움직인다.
   대상은 월드에 있는 IK 발 · 컨트롤러 전제. 부모가 움직이는 경우는 Counter Layer(Stationary) 쪽 기능이다 → 툴팁 · 가이드에 적는다.
3. **Layer Blend 레이어 키가 a', a'−N 두 개뿐이면** 구간 안 (a', b] 에서 레이어 커브가 다음 레이어 키 쪽으로 보간되고,
   다음 구간의 블렌드 [a₂'−N, a₂'] 가 앞 구간 안으로 들어올 수 있다(사용자 확인: [0, 10] · [12, 20], N=5 → f7 키).
   → **결정 #4: B → A → D** 로 해결(§3.3a · §3.4-6/7). 남는 경우: 레이어에 원래 있던 키가 구간 안에 있으면 D 의 a'~b 사이에서
   그 키가 지워지지는 않는다 — 덮어쓰지 않고 로그 `"(layer already has keys inside [a-b] - not locked flat)"` 로 알린다.
4. **Hold 대상 레이어 = 보기 레이어**: 기본 BaseAnimation. 사용자가 `Run only when viewing` 을 다른 레이어로 바꿔 두면 그 레이어 커브를 Hold 한다
   (Shift+A 와 같은 정신). Layer Blend 레이어와 같으면 같은 커브에 Hold + 레이어 키가 겹친다 → 경고 한 줄만.
5. **키가 듬성한 커브**: [a, b] 안 키가 2 개 미만이면 Hold skip(Shift+A 와 같음). 로그 `"(k curve(s) skipped: <2 keys in span)"`.
6. **회전 Hold** 는 오일러 값 그대로 평평하게(Shift+A 와 같음). 구간 끝에서 튀면 Curve > Euler 로.
7. **성능**: 샘플링 = 프레임 수 × 오브젝트 수 `getAttr`. 무거운 리그 1000 f 는 수 초~십수 초(Counter Layer 실측 1000 f 10.5 s). 디버그 켜면 재샘플 한 번 더 → 2 배.
8. **Current 값 읽기**: 구간마다 `capture_current(frame=a')` 가 시간을 a' 로 옮겼다 돌아온다(undo 기록 끔). 구간 수 × 2 번 이동.
9. **undo**: 바깥 청크 하나. `currentTime` 이동은 undo 를 끈 채로(§3.1) — 안 그러면 Ctrl+Z 한 번이 시간 이동만 되돌린다(v02.41 시험 함정).
10. **네임스페이스 · 레퍼런스**: 레퍼런스 컨트롤의 Base 커브도 편집 가능(일반 키 편집과 같음). 디버그 어트리뷰트 이름은 `:` 를 `_` 로.

---

## 6. 검증 (mayapy, `tests/test_fix_sliding.py`)

`maya.standalone` + 오프스크린 PySide2(UI 부분). optionVar(`JUN_A00110_holdLayer_*`, `JUN_A00110_fixSliding_*`)는 시작 · 끝에 지운다.

**순수 함수**
1. `speeds` — 축 끄기(Y 끔이면 세로 이동 무시), 길이 n 유지, 첫 프레임 = 다음 차.
2. `smooth` — W=1 그대로, W=3 중심 평균, 가장자리 창 축소, 짝수 W.
3. `still_spans` — 경계 포함(a, b), 구간 시작 · 끝이 S / E 에 닿는 경우, 엄격한 `<`.
4. `split_spans` — `L == M` 은 short, `L == M+1` 은 apply.

**장면** (로케이터 `foot`, Base 에 매 프레임 키, 1~60 f):
- f1–10 이동 0→10, f11–30 정지(±0.01 지터), f31–40 이동 10→20, f41–60 정지(지터), 세로(ty)는 f31–40 에 살짝 들썩.
- `AnimLayer1`(additive) 생성 · foot T/R 멤버. Hot Key > Main 설정: `layer=AnimLayer1, offset=5, axis_values={tx:0, ...}, current_axes=[...]`.

5. Preview: 정지 구간 두 개 ≈ [11, 30](L=20) · [41, 60](L=20) — 정확한 경계는 스무딩 창 때문에 1~2 f 밀릴 수 있으니
   순수 함수로 같은 데이터에서 계산한 값과 비교한다. M=5 면 둘 다 apply, M=20 이면 둘 다 short(L == M), M=19 면 둘 다 apply. 키 변경 없음.
6. Run(M=5, P=5 %, W=3, **G=0 · Clamp 끔 · Lock 끔**): **같은 장면을 복제해 손으로 `selectKey`(구간 안 T/R Base 커브) +
   `HotkeyManager.run_hold()`(보기 = Base) 를 구간마다 한 결과와 Base 커브 · 레이어 커브의 키 시간 · 값이 1e-9 까지 같다**
   — "Shift+A 결과" 의 정의 그대로 대조(핵심 시험). 보정(B · A · D)을 끈 상태가 순수 Shift+A 다.
7. 짧은 구간(L ≤ M) 의 커브는 그대로.
8. 레이어 멤버가 아닌 오브젝트: Hold 는 되고 Layer Blend 는 `Skipped` 메시지.
9. 안 움직이는 오브젝트: 건너뜀 + 경고, 키 변경 없음.
10. `layer_blend=False`: Hold 만, 레이어 커브 그대로.
11. `translate=False`: 회전 커브만 Hold.
12. 디버그: `_debug_speed` 존재, 오브젝트당 어트리뷰트 4 개, 키 수 = 프레임 수, threshold 상수, 적용 구간에서 `n_result` 평균 < `n_speed` 평균. 두 번 실행해도 노드 하나.
13. undo 한 번에 Base · 레이어 커브 원상복구(디버그 노드는 남음), `currentTime` 원래대로.
14. Hot Key > Main 의 `Layer Blend Key` 가 꺼져 있고 보기 레이어가 AnimLayer1 이어도 이 탭 실행은 동작(force).
14a. **대안 B** `merge_gaps` 순수: gap = G 는 합침, G+1 은 안 합침, 연쇄 합치기, G=0 은 그대로. 장면: 정지 [0, 10] · [12, 20](gap 1) → G=4 로 한 구간
     [0, 20], 레이어 키는 f(0−N) · f0 (· f20) 뿐이고 **f7 같은 중간 키가 없다**(사용자 예시 그대로).
14b. **대안 A** 장면: 정지 [0, 10] · [16, 25](gap 5 > G 4), N=8 → 두 번째 구간 레이어 키 t0 = **f10**(f8 아님), 로그에 `clamped`. Clamp 끔이면 f8.
14c. **대안 D**: 각 구간 b 에 레이어 키, 값 = a' 의 레이어 값(1e-9), a' out / b in 탄젠트 flat, [a', b] 의 정수 · 반 프레임에서 레이어 값 상수.
14d. B · A · D 를 다 켠 Run 뒤 재샘플 월드 속도: 적용 구간 내부(양 끝 제외) 프레임 속도 < 1e-6 (레이어에 원래 키가 없을 때).
15. 회귀: `test_hold_layer_blend.py` 81/81 · `test_hold_layer_blend_ui.py` 21/21 (Shift+A 불변).

**UI** (`tests/test_fix_sliding_ui.py`)
16. Bake 하위 탭 `Fix Sliding` 존재, 기본값(W 5 · 2 % · **G 4** · M 3 · XYZ · T R · Layer Blend ON · **Clamp ON · Lock ON** · Debug ON),
    Layer Blend 를 끄면 Clamp · Lock 비활성.
17. 버튼 → 코어에 옵션이 그대로 넘어간다(코어를 가짜로 바꿔 인자 기록).
18. optionVar 저장 → 창 다시 열면 복원.
19. `lbl_fs_layer_blend` 가 Hot Key > Main 레이어 · N 을 보인다, 레이어 미선택이면 경고 문구.

GUI 확인(사용자): 실제 모캡(ZIHAN 등)에서 발 IK 두 개 — Preview 구간이 눈으로 본 접지와 맞는지, Run 후 `_debug_speed` 결과 커브, 레이어 키 위치.

---

## 7. 작업 순서 (권장)

1. §4.1 Hold 리팩터 → `test_hold_layer_blend.py` 통과 확인(동작 불변).
2. §4.2 `force` → 같은 회귀.
3. §4.3 순수 함수(speeds · smooth · still_spans · merge_gaps · split_spans · blend_starts) + 시험 1~4 · 14a 순수 부분.
4. 샘플링 · analyze · preview + 시험 5.
5. run(§3.4, 먼저 B · A · D 끈 상태) + 대조 시험 6 → 7~11, 13~14.
5a. `apply(ramp_start, hold_end)`(§4.2) + B · A · D 켜기 → 시험 14a~14d.
6. 디버그 노드(§3.5) + 시험 12.
7. UI(§4.5) + UI 시험 16~19.
8. 마무리 체크리스트.

## 8. 마무리 체크리스트

- [ ] `config/version.py` → `02.48`, 이력에 한 줄
- [ ] 새 파일 헤더 관례(`# Python Script by Ji Hun Park` / `# last Update date :`)
- [ ] 툴 가이드 `JUN_All/docs/A00110_animTool_V02.md` — Bake > Fix Sliding 절(화면 · 옵션 · 함정 §5-2,3), 탭 표 · 파일 트리에 `fix_sliding_manager.py`
- [ ] `JUN_All/docs/WORKLOG.md`
- [ ] 메모리 `wip-a00110-fix-sliding.md` 새로 + `MEMORY.md` A00110 줄
- [ ] 이 계획서 상태 → 구현 완료 + 바뀐 점
- [ ] 로컬 커밋(경로 명시 스테이징). **푸시는 그 턴에 요청이 있을 때만.**

---

## 9. 이웃 구간 블렌드 침범 — 대안 A~E 기록 (2026-11-04)

### 9.1 문제

Shift+A(= Fix Sliding 의 기본 재현)를 구간마다 차례로 하면 블렌드 구간 **[a−N, a]** 가 앞 구간 안으로 들어올 수 있다.

| 순서 | 구간 | 레이어 키 |
|---|---|---|
| 1 | [0, 10] | f-5 (레이어 값), f0 (Pose / Current) |
| 2 | [12, 20] | **f7** (레이어 값), f12 (Pose / Current) |

f7 키 자체는 그 시점 값을 보존하지만, **f7 → f12 사이에서 레이어가 두 번째 포즈 쪽으로 보간**되므로 고정돼야 할 첫 구간의 f7~f10 이
다시 움직인다(사용자 확인: "7 프레임에 원하지 않는 키가 찍힌다"). 첫 구간 안 (0, 10] 도 레이어가 다음 키 쪽으로 보간될 수 있다.

### 9.2 대안

| | 방법 | 장점 | 단점 |
|---|---|---|---|
| **A** | **블렌드 시작을 앞 구간 끝에서 자른다** — `t0 = max(a − N, b_prev)`. 예: max(7, 10) = f10, 블렌드는 이동 프레임 [10, 12] 에서만 | 고정 구간 안은 절대 안 움직인다. 구현 몇 줄 | 틈이 짧으면 블렌드가 1~2 프레임 → 툭 튈 수 있다 |
| **B** | **틈이 짧은 구간을 하나로 합친다**(Merge gap G) — 이동 프레임 수 ≤ G 면 한 구간. 예: 틈 f11 한 프레임 → [0, 20] | 모캡 노이즈로 접지가 잠깐 끊긴 경우를 깔끔히 처리, 키도 준다 | 진짜 짧은 스텝까지 합칠 수 있어 G 를 사용자가 정해야 한다 |
| **C** | **겹치면 그 구간의 블렌드를 생략하고 경고** | 가장 보수적 | 그 구간은 레이어 보정이 빠진다 |
| **D** | **구간 끝 b 에도 레이어 키** — a 와 같은 값 + flat 탄젠트로 구간 내부를 잠근다 | A 와 함께면 고정 구간을 완전히 보장 | 단독으로는 다음 블렌드가 안으로 들어오는 걸 못 막는다 |
| **E** | **이동 거리 비례 블렌드**(SmartLayer 방식) — 틈 안에서 실제 이동 거리 비율로 레이어 값을 매 프레임 분배. 정지 프레임은 이동량 0 이라 자동으로 안 움직인다. Counter Layer v02.29 "By travel" 과 같은 원리 | 품질이 가장 좋다 | 틈 구간에 매 프레임 키, 작업량 큼, "Shift+A 결과" 와 달라진다 |

### 9.3 결정

- **Fix Sliding: B → A → D 순서로 적용, G 기본 4 프레임**(사용자, 2026-11-04). 셋 다 UI 에서 끌 수 있고(G=0 · Clamp 끔 · Lock 끔) 끄면 순수 Shift+A 재현.
  - B 먼저: 노이즈로 끊긴 접지를 하나로 → 그 뒤 M 판정.
  - A: 남은 이웃 구간 사이에서 블렌드가 이동 프레임에서만 일어나게.
  - D: 각 고정 구간 내부의 레이어 값을 상수로 잠금.
- **C**: 채택 안 함(A 가 같은 상황을 보정까지 해서 처리).
- **E**: 이번 범위 밖 — Fix Sliding 결과(`_debug_speed` 의 `n_result`)를 본 뒤 다음 버전 옵션 후보.
- **손으로 누르는 Shift+A** 는 앞 구간을 모르므로 이번 범위에서 바꾸지 않는다. 후보(미정): 세션 동안 오브젝트마다 Shift+A 로 Hold 한 구간을 기억해
  다음 Shift+A 의 t0 를 직전 구간 끝으로 자르기 — 시간순으로 누르면 정확, 거꾸로 누르면 못 막아 경고만 가능.
