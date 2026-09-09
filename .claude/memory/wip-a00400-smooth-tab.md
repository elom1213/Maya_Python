---
name: wip-a00400-smooth-tab
description: A00400 Smooth 탭 - smoothCurve 결과에 소프트셀렉션 가중치+Rough+닫힌 커브를 얹는다. smoothCurve 는 음수 무시·주기 실패(감아 넣은 임시 커브로 우회)
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-09-09T00:00:00.000Z
---

`A00400_CurveTool` **Smooth 탭** (v01.04→01.05, 2026-08-18). 고른 CV 를 슬라이더로 실시간
Smooth / Rough. 마야 기본 `Curves > Smooth`(`cmds.smoothCurve`) 결과를 **그대로 쓰되** 확장한다.

```
target[i] = smoothCurve(smoothness=|amount|) 결과
result[i] = origin[i] + sign(amount) * weight[i] * (target[i] - origin[i])
amount = 슬라이더 × Multiplier   (1 이면 마야 기본 Smooth 와 동일 — 검증으로 고정)
```
값을 키울 때 **외삽하지 않고 `smoothness` 를 키운다** → 형태가 안 튄다.
마야 결과는 **임시 복제 커브**에서 뽑는다(드래그당 1개, 틱마다 원본 스냅샷 write → smoothCurve → read).

**`cmds.smoothCurve` 실측**
- **음수 smoothness 를 조용히 무시**한다(s=-1 → 변화 없음) → Rough 는 직접 구현
- **degree 1(직선) 커브에서 실패**한다 → 미리 걸러낸다
- **주기(periodic) 커브에서도 실패**한다(`Cannot smooth CVs on periodic curves`)
  → v01.08 부터 **감아 넣은 임시 열린 커브**로 우회한다(아래)
- **커브 양 끝 CV 를 절대 안 움직인다**(실측 CV12: d2→앞2/뒤1, d3→앞뒤2, d5→앞뒤3 ≈ `(degree+1)//2`).
  끝쪽만 고르면 **성공하는데 아무 것도 안 변한다** → "실제로 움직인 CV 수"를 세어 보고하고 0 이면 경고.
  조용한 무동작이 "툴이 안 된다"의 진짜 정체였다
- 실수 smoothness 를 받는다(0.5≠1). 단 **CV 하나만 보면 단조롭지 않다**
  (s=1→5 에서 전체 최대 변위 1.19→2.48 인데 특정 CV 는 0.89→0.81). 버그 아님
- 히스토리 노드를 만들지 않는다

**소프트 셀렉션**: `om2.MGlobal.getRichSelection()` → `MFnSingleIndexedComponent.weight(i).influence`.
⚠️ **이 호출은 빈 선택에서 예외를 던지고**(`Object does not exist`), **인터랙티브 마야에서는 다른 이유로도
실패할 수 있다** — mayapy 에서는 모든 경우가 정상인데 실제 마야에서 "선택한 게 없다"가 뜬다는 보고를 받았다.
예외를 **조용히 삼키면 안 된다**. 리치가 실패/빈값이면 `cmds.ls(selection=True)` 로 **폴백**하고,
어느 경로였는지와 사유를 로그에 남긴다(`cv_selection()` → (선택, source, note)).
커브 CV 판정은 **컴포넌트 타입 enum 말고 노드가 `nurbsCurve` 인지**로 — 서페이스 `cv[0][0]`·메시 버텍스는 걸러진다.

**undo 함정(이 툴에서 세 번째)**: 임시 복제를 **만드는 capture() 까지 청크 안**이어야 한다.
밖에 두면 Ctrl+Z 가 CV 가 아니라 "임시 커브 삭제"를 되돌려 임시 노드만 되살아난다.
확정 뒤 슬라이더를 0 으로 되돌릴 때는 **신호를 막을 것** — 안 막으면 valueChanged 가 0 으로
재적용해 방금 확정한 결과를 지운다.

**⚠️ 선택을 지우는 마야 명령이 셋** — 이 툴은 슬라이더를 놓을 때마다 선택을 다시 읽으므로
**한 번이라도 풀리면 그 뒤로 아무것도 안 된다.** 증상은 언제나 같은 모양으로 온다:
"한 번은 되는데 그 다음부터 `Select some curve CVs first ...
[RuntimeError: (kFailure): Object does not exist]`" — **뒤의 예외는 원인이 아니라 증거**다
(빈 선택에서 `getRichSelection()` 이 던진다). 셋 다 공용 `keep_selection()` 컨텍스트로 묶었다.
- `cmds.smoothCurve` — **다른 커브에 걸어도** 활성 선택을 지운다(7개→0개). v01.05 에서 잡음.
  사용자가 "슬라이더 움직이면 CV 선택이 풀린다"고 알려줘서 찾았다.
- `cmds.curve`(생성) — **만든 커브를 선택 상태로 만든다.** v01.09 에서 잡음.
  임시 사본 경로가 열린 커브는 `cmds.duplicate`(선택 무해), 닫힌 커브는 `cmds.curve` 라
  **닫힌 커브에서만** 났다 — 아키텍처가 갈라지는 곳이 곧 증상이 갈라지는 곳이다.
- `cmds.delete` — 지운 것이 선택돼 있었으면 선택이 빈다(위와 짝).
- Qt 슬라이더를 **붙잡고 있는 동안 마야가 뷰포트를 다시 그릴 틈을 못 얻는다** → CV 는 바뀌는데
  화면만 그대로. 틱마다 **`cmds.refresh()`** 를 직접 불러야 한다(재진입 플래그로 보호).
- CV 를 하나씩 `cmds.xform` 하면 틱마다 명령 수십~수백 개 → 무거워진다. 읽기는 API `cvPositions`,
  쓰기는 **`cmds.curve(replace=True)`**. ⚠️ API `setCVPositions` 는 빠르지만 **undo 큐에 안 남는다**
  (이 회귀를 실제로 냈고 테스트가 잡음). `cmds.curve -r` 은 0.16ms/call, undo 되고, degree/CV수/
  히스토리 보존, 숨긴 커브 OK, 한 청크 안 여러 번 호출해도 Ctrl+Z 한 번.

**닫힌(주기) 커브** (v01.07→01.08, 2026-09-09). 마야가 거절하는 건 계산이 아니라 **이음매를 넘는
이웃 관계**뿐이다. 그래서 라플라시안을 따로 짜지 않는다 — 그러면 열린 커브와 **감촉이 갈라진다.**
실제 CV(spans 개)를 앞뒤로 **감아 복사한 열린 임시 커브**에 마야 `smoothCurve` 를 돌리고
**가운데 구간만** 읽는다. 마야의 끝 고정은 패딩 안에서만 일어난다.

```
[ 0..7 ]  →  [ 5 6 7 : 0..7 : 0 1 2 ]  →  smoothCurve  →  가운데 [ 0..7 ] 만 읽기
```
- `pad = 2*degree + 4` 면 degree 7 까지 pad 40 과 비트 단위로 같다(실측).
- 결과 = 마야 내부 스텐실을 **순환**으로 건 것과 오차 `8.9e-16`.
  임펄스 응답으로 뽑은 d3 스텐실은 `[-1/18, 2/9, 2/3, 2/9, -1/18]`(합 1).
- ⚠️ **주기 커브는 CV 가 두 가지로 세어진다** — `.cv[i]` 는 `spans` 개, `cvPositions()` 는
  `spans + degree` 개(뒤 degree 개는 앞의 복사본). **쓸 때 복사본까지 갱신**해야 이음매가 안 벌어진다.
- ⚠️ **주기 커브엔 `cmds.curve(replace=True)` 가 그냥 안 통한다**
  (`Must specify knots with the -per option`) → `periodic=True` + `knot=` 까지 넘긴다.
  `setAttr .controlPoints` 는 **히스토리가 있으면 절대 위치가 아니라 트윅(델타)** 이라 값이 두 번 섞인다
  (`makeNurbCircle` 살아 있는 원에서 재현) — 쓰지 않는다. [[shape-pnts-is-post-deformation]] 과 같은 함정.
- 닫힌 커브는 **고정되는 CV 가 없다** → `pinned_indices(periodic=True)` 는 빈 목록,
  `Check Selection` 이 `open`/`closed` 를 적는다.
- 닫힌 커브의 `u=0`/`u=1` 이 같은 점인 것은 [[wip-a00400-curve-joints]] 에도 나온 성질.

검증: mayapy 2024 코어 26 + UI 31 + 폴백 23 + 고정CV 22 + 라이브 13 + 선택유지 15. 툴 전체 회귀 252항목.
v01.08 닫힌 커브 20 + 드래그 9 + UI 9 (열린 커브 결과 회귀 포함).
v01.09 선택 유지 21 (닫힌 · 닫힌+히스토리 · 열린 각각 연속 3회 적용 + 드래그 중/후 + 다음 capture).
같은 툴: [[wip-a00400-points-to-curve]], [[wip-a00400-curve-wrap]], [[wip-a00400-curvetool]]
