---
name: getattr-settable-lies-for-constrained
description: getAttr(plug, settable=True) 는 컨스트레인트가 구동하는 트랜스폼에도 True 를 돌려준다 — "쓸 수 있나" 는 connectionInfo(isDestination=True) 로 판정
metadata:
  type: reference
---

**`cmds.getAttr(plug, settable=True)` 로 "이 어트리뷰트에 써도 값이 남는가" 를 판정하면 안 된다.**

Maya 2024 실측 — `pointConstraint` 가 구동하는 ikHandle 의 `translateX` 에 대해:

```
listConnections(d=False)                  -> ['ik_h_pointConstraint1.constraintTranslateX']
connectionInfo(plug, isDestination=True)  -> True
getAttr(plug, settable=True)              -> True      # <-- 거짓말
getAttr(plug, lock=True)                  -> False
```

`settable` 을 믿으면 `xform` 으로 옮기고 **"옮겼다" 고 보고**하는데, 다음 평가에서 컨스트레인트가
도로 끌어가 **편차가 조용히 남는다**(A00060 IK Edit 에서 정확히 편차 1.0 으로 나타났고 테스트가 잡았다).

**판정은 이렇게**

```python
def writable(plug):
    if cmds.getAttr(plug, lock=True):
        return False
    if cmds.connectionInfo(plug, isDestination=True):
        return False
    return True
```

컴파운드(`translate`)를 넘길 땐 `attributeQuery(listChildren=True)` 로 자식 플러그까지 봐야 한다 —
컨스트레인트는 `translateX/Y/Z` 에 개별 연결하므로 부모만 보면 놓친다.

**혼동 주의**: 평범한 `connectAttr` 로 연결된 어트리뷰트(예: FK/IK 스위치에 물린 `ikHandle.ikBlend`)에
대해서는 `settable` 이 제대로 `False` 를 준다. 그래서 "가끔 맞는" 것처럼 보이고, 하필 **트랜스폼 +
컨스트레인트** 조합에서만 틀린다.

관련: [[wip-a00060-ik-edit]] · [[mayapy-headless-verify]] ·
[[constraint-target-plugs-and-offset-spaces]]
