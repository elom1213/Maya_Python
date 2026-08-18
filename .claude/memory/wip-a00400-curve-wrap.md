---
name: wip-a00400-curve-wrap
description: A00400 Wrap 탭 - rebuildCurve+blendShape 로 CV 수 다른 커브 라이브 wrap. rebuildCurve 는 트랜스폼을 안 따라간다
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-18T01:02:52.779Z
---

`A00400_CurveTool` **Wrap 탭** (v01.02→01.03, 2026-08-18). CV 개수가 다른 두 커브에서
driven 이 driver 모양을 따르게 한다. 마야 기본 `wrap` 디포머가 불안정해서 만든 대체.

**네트워크** (디포머 없이 스톡 노드만, 그래서 라이브):
```
driverShape.local -> rebuildCurve(driven 의 span/degree) -> transformGeometry -> wrapTarget
wrapTarget -> blendShape(driven) 타깃, weight = driven.wrapEnvelope (0~1)
```
핵심은 **`rebuildCurve`** — "같은 모양을 다른 CV 개수로 다시 표현"하는 노드라, driven 의
span/degree 로 driver 를 재구성하면 CV 개수가 driven 과 **정확히** 같아져 blendShape 타깃이 된다.
12CV←4CV 실측 최대 편차 **0.0013**.

**가장 큰 함정**: `rebuildCurve` 노드는 소스의 **CV 변화만 따라가고 트랜스폼 이동은 무시한다**
(기본 연결이 `worldSpace` 인데도, `dgeval` 해도 안 됨). → 지오메트리는 `.local` 을 먹이고
공간 변환은 `driver.worldMatrix × driven.worldInverseMatrix` 를 `multMatrix`→`transformGeometry`
로 따로 건다. **행렬은 평범한 어트리뷰트라 전파가 확실하다.**

**그 외 실측**
- 노트 벡터 **범위**(0~1 vs 0~9)가 달라도 무관. **간격이 불균등하면** 오차가 커진다(0.264,
  Uniform-rebuild 옵션 켜면 0.088) → 경고 + 옵션
- **form(open/periodic) 이 다르면 편차 10.77 로 망가지는데 blendShape 은 에러를 안 낸다**
  (CV 수만 맞으면 생성됨) → 툴이 미리 거절
- blendShape weight 는 **음수 허용** → Preserve Offset 을 타깃 2개(라이브 +env, 바인드 -env)로
- `undo_chunk` 안에서 `setAttr` 까지 해야 생성이 undo 한 스텝 (밖에 두면 그 setAttr 만 되돌아감)

검증: mayapy 2024 코어 47 + UI 21 = 68항목. 관련: [[mayapy-headless-verify]],
[[qapplication-before-maya-standalone]], [[undo-chunk-by-default]], [[wip-a00420-wrapper]]
