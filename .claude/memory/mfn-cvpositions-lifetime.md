---
name: mfn-cvpositions-lifetime
description: cvPositions() 가 준 MPoint 를 MFnNurbsCurve 밖으로 들고 나오면 값이 되돌아간다 - 읽는 즉시 tuple 로 복사
metadata:
  type: reference
---

```python
def _cv_points(shape):                      # 함정
    return list(om2.MFnNurbsCurve(dag).cvPositions(om2.MSpace.kObject))
```

함수가 끝나 `MFnNurbsCurve` 가 사라지면 그 `MPoint` 들의 값이 **원래 자리로 되돌아가 있다.**
그대로 쓰면 "읽어서 그 값을 다시 쓰는" 꼴이 돼 **한 점도 안 움직이는데 로그는 성공**이라고 찍힌다.

- 재현이 들쭉날쭉하다 — 짧은 스크립트에서는 멀쩡하고, 씬을 저장했다 다시 연 다음에만 터졌다.
  GC 타이밍에 달린 문제라 "가끔 안 먹는다" 로 보인다.
- **읽는 즉시 plain tuple 로 복사한다**: `[(p.x, p.y, p.z) for p in positions]`.
- [[mplug-asmobject-lifetime]] 과 같은 수명 함정이다. `cvPositions` · `getPoints` 처럼
  **API 객체가 소유한 배열**을 돌려주는 것은 전부 의심할 것.

2026-09-22 A00400 v01.22 ([[referenced-curve-cv-write]]) 에서 걸렸다.
