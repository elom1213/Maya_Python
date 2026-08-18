---
name: wip-a00400-smooth-tab
description: A00400 Smooth 탭 - smoothCurve 결과에 소프트셀렉션 가중치+Rough 를 얹는다. smoothCurve 는 음수 무시·주기 실패
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-18T01:57:03.406Z
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
- **주기(periodic) 커브**와 **degree 1(직선) 커브에서 실패**한다 → 미리 걸러낸다
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

**라이브 드래그 함정 3개** (사용자 보고: "처음 한 번은 되는데 잡고 드래그하면 반응이 없다")
- **`cmds.smoothCurve` 가 활성 선택을 지운다**(임시 커브에 걸어도 7개→0개). 첫 틱 뒤 CV 선택이
  풀려 **그 다음부터 적용 대상이 사라진다** = "드래그해도 반응 없음"의 진짜 원인.
  → 명령 앞뒤로 `MGlobal.getActiveSelectionList/setActiveSelectionList` 로 보관·복원(소프트 폴오프도 유지).
  사용자가 "슬라이더 움직이면 CV 선택이 풀린다"고 알려줘서 잡혔다.
- Qt 슬라이더를 **붙잡고 있는 동안 마야가 뷰포트를 다시 그릴 틈을 못 얻는다** → CV 는 바뀌는데
  화면만 그대로. 틱마다 **`cmds.refresh()`** 를 직접 불러야 한다(재진입 플래그로 보호).
- CV 를 하나씩 `cmds.xform` 하면 틱마다 명령 수십~수백 개 → 무거워진다. 읽기는 API `cvPositions`,
  쓰기는 **`cmds.curve(replace=True)`**. ⚠️ API `setCVPositions` 는 빠르지만 **undo 큐에 안 남는다**
  (이 회귀를 실제로 냈고 테스트가 잡음). `cmds.curve -r` 은 0.16ms/call, undo 되고, degree/CV수/
  히스토리 보존, 숨긴 커브 OK, 한 청크 안 여러 번 호출해도 Ctrl+Z 한 번.

검증: mayapy 2024 코어 26 + UI 31 + 폴백 23 + 고정CV 22 + 라이브 13 + 선택유지 15. 툴 전체 회귀 252항목.
같은 툴: [[wip-a00400-points-to-curve]], [[wip-a00400-curve-wrap]], [[wip-a00400-curvetool]]
