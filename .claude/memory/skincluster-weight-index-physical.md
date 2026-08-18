---
name: skincluster-weight-index-physical
description: MFnSkinCluster get/setWeights 는 물리 인덱스를 받는다 — indexForInfluenceObject(논리)를 넘기면 undo 뒤 kInvalidParameter
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5ea9f25d-fd66-4b79-a930-ec982f8f7f17
  modified: 2026-08-18T01:38:33.914Z
---

`MFnSkinCluster.getWeights` / `setWeights` 의 influence 인덱스는 **물리**다 —
`influenceObjects()` 배열에서의 자리(0,1,2,…), 즉 `getWeights` 웨이트의 열 순서.
`indexForInfluenceObject()` 가 주는 **논리** 인덱스(`.matrix[]` · `.weightList[].weights[]` 첨자)를
넘기면 안 된다. 공용 헬퍼: `Framework.core.maya_skin.weight_indices()` / `logical_indices()`.

**Why:** skinCluster 를 만든 직후에는 **논리 = 물리**라서 잘못 써도 잘 돌아간다. 그래서 이 실수는
오래 살아남고(이 저장소에도 4개 툴 5곳에 복붙돼 있었다), 어긋나는 순간에만 터진다:

```
# Warning: (kInvalidParameter): Object is incompatible with this method
```

**어긋나는 대표 상황은 undo.** 인플루언스를 추가한 뒤 Ctrl+Z 하면 논리 인덱스가 회수되지 않아,
다시 추가할 때 새 번호가 붙는다(실측: `matrix mi` `[0,1,2]` → undo → `[0]` → 재추가 → `[0,3,4]`).
사용자에게는 **"Ctrl+Z 한 번 하면 그 뒤로 바인드가 안 된다"** 로 보인다(A00275 Expand Bind, v01.13).
**이미 스킨이 있는 메시**에서만 재현된다 — 새 메시는 undo 로 skinCluster 자체가 사라진다.

**How to apply:** 웨이트 API 에는 `range(len(fn.influenceObjects()))` 를 넘긴다. 논리 인덱스는
`.matrix[i]` / `.bindPreMatrix[i]` 처럼 **플러그를 직접** 만질 때만 쓴다(A00430
`scene_sampler.bind_pre_from_skin` 이 그 경우). 같은 `kInvalidParameter` 문구가
[[extendtoshape-picks-wrong-shape]] 에서도 나오니, 셰이프를 확정했는데도 계속 나면 인덱스를 의심할 것.
테스트는 **인플루언스를 넣었다 뺐다 해서 인덱스를 듬성하게 만든 뒤** 돌려야 잡힌다.
