---
name: ikhandle-creation-traps
description: ikHandle 생성 함정 3종 — SC 핸들에도 poleVector 어트리뷰트가 있다(솔버 이름으로 갈라야 함), ikSpringSolver 는 플러그인 로드만으론 부족, 같은 체인에 두 번째 핸들을 마야가 조용히 만들어 준다
metadata:
  type: reference
---

`cmds.ikHandle` 로 IK 를 만들 때 **실측이 아니면 조용히 틀리는 것들** (Maya 2024).

**① `ikSCsolver` 핸들에도 `poleVector` 어트리뷰트가 있다.**

```python
h = cmds.ikHandle(sj=root, ee=end, solver="ikSCsolver")[0]
cmds.attributeQuery("poleVector", node=h, exists=True)   # True (!)
cmds.poleVectorConstraint(pole, h)
# RuntimeError: Handle must be valid and use rotate plane solver
```

**"폴 벡터를 걸 수 있나" 는 어트리뷰트 존재로 판정하면 안 되고 솔버 이름으로 갈라야 한다.**
폴 벡터를 받는 솔버는 `ikRPsolver` · `ikSpringSolver`. `attributeQuery` 가 거짓말하는
또 하나의 사례다 — [[getattr-settable-lies-for-constrained]] · [[list-attrs-multi-detection]] 과 같은 부류.

**② `ikSpringSolver` 는 플러그인을 로드해도 못 쓴다.**

```python
cmds.loadPlugin("ikSpringSolver", quiet=True)     # loaded == True
cmds.objExists("ikSpringSolver")                  # False  <- 솔버 *노드* 가 없다
cmds.ikHandle(sj=a, ee=b, solver="ikSpringSolver")
# RuntimeError: The ikSolver does not exist.
```

솔버 노드는 **같은 이름의 MEL 프로시저**가 만든다 — `mel.eval("ikSpringSolver;")` 를 한 번
돌린 뒤에야 `ikHandle` 이 통한다. (플러그인 로드 = 노드 타입 등록일 뿐이다.)

**③ 같은 체인에 두 번째 핸들을 마야가 에러도 경고도 없이 만들어 준다.**
`ikHandle(sj=root, ee=end)` 를 두 번 부르면 핸들이 둘 생기고 둘 다 같은 조인트를 구동한다.
막고 싶으면 직접 검사해야 한다 — `cmds.ikHandle(h, q=True, jointList=True)` 로 기존 핸들들의
조인트 집합과 겹치는지 본다(`jointList` 는 **끝 조인트를 뺀다** — [[wip-a00060-ik-edit]]).

**그 밖에**
- `ikHandle(sj, ee)` 반환은 `[handle, effector]`. **이펙터 이름은 `effector1` 로 남는다** —
  `-name` 은 핸들에만 붙는다. 이펙터는 따로 `cmds.rename`(핸들 쿼리는 새 이름을 그대로 따라온다).
- `ikHandle -e -sticky "off"` 는 `The sticky value supplied was invalid.` 경고를 낸다.
  값은 들어가지만 로그가 지저분해진다 — 새 핸들은 어차피 off 이므로 **켤 때만** 건드린다.
  (`sticky=0` 은 경고 없이 통한다.)
- **일직선 체인에 `poleVectorConstraint` 를 걸어도 에러가 안 난다.** 평면이 임의로 정해질 뿐이라
  막을 근거가 없다 — 경고만 내고 진행하는 게 맞다.
- 끝이 시작의 자손이 아니면 `RuntimeError: <a> is not an ancestor of <b>.` — 메시지가 명확하지만,
  여러 쌍을 도는 루프라면 **미리 검사해서 그 쌍만 건너뛰는** 편이 낫다.
- 이름이 겹치면 마야가 조용히 `_ikHandle1` 로 늘린다(에러 아님).

적용: `A00060_jointTool_V03` 의 `Chain > Create IK`
(`app/core/ik_create_manager.py`, v03.01 — [[wip-a00060-v03-tab-reorg]]).
검증은 [[mayapy-headless-verify]].
