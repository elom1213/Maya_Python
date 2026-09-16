---
name: utility-nodes-inherit-shadingdependnode
description: "multiplyDivide · vectorProduct · plusMinusAverage 는 shadingDependNode 를 상속한다 — 셰이딩 판정은 getClassification 으로"
metadata:
  node_type: memory
  type: reference
---

**`nodeType(inherited=True)` 로 셰이딩 노드를 걸러내면 리깅 유틸리티가 같이 걸린다.** (Maya 2024 실측)

```
multiplyDivide    -> ['shadingDependNode', 'multiplyDivide']
vectorProduct     -> ['shadingDependNode', 'vectorProduct']
plusMinusAverage  -> ['shadingDependNode', 'plusMinusAverage']
condition / blendColors / reverse / setRange / clamp / remapValue -> 상속 안 함 (헷갈린다)
```

리그 노드망을 훑는 코드가 `"shadingDependNode" in inherited` 로 셰이딩을 제외하면, **리깅에서 제일
흔한 세 노드가 통째로 빠진다.** A00145 Mirror 가 이 때문에 노드망을 반만 복제했다
([[wip-a00145-mirror-network-offsets]]).

**대신 노드 분류(`cmds.getClassification(<타입>)`)의 뒤쪽(기능) 분류를 본다.**

```
multiplyDivide -> 'drawdb/shader/operation/multiplyDivide:math/operation'
file           -> 'drawdb/shader/texture/2d/file:texture/2d'
lambert        -> 'drawdb/shader/surface/lambert:shader/surface'
condition      -> 'drawdb/shader/operation/condition:utility/general'
```

앞의 `drawdb/...` 는 **하이퍼셰이드 그리기 분류**라 유틸리티 노드에도 `shader` 가 들어 있다 —
버리고, `:` 뒤 분류의 첫 토큰이 `shader` / `texture` 일 때만 셰이딩으로 본다.
(`decomposeMatrix` 는 `'animation'`, `pointOnCurveInfo` 는 `''` 로 분류가 비어 있을 수 있다.)
플러그인 타입은 `getClassification` 이 던질 수 있으니 감싼다.
