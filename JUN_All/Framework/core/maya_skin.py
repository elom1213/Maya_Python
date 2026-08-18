# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# Framework - skinCluster 웨이트 API 공용 헬퍼.
#
# `MFnSkinCluster` 의 웨이트 API 에는 **인덱스가 두 종류**라는 함정이 있다.
#
#   물리(physical) 인덱스 : `influenceObjects()` 가 돌려준 배열에서의 자리(0,1,2,...).
#                           `getWeights` 가 돌려주는 웨이트의 **열 순서**가 이것이다.
#   논리(logical) 인덱스  : `.matrix[]` / `.weightList[].weights[]` 의 실제 첨자.
#                           `indexForInfluenceObject()` 가 돌려주는 값.
#
# `getWeights(path, comp, influenceIndices)` 와 `setWeights(path, comp, influenceIndices,
# ...)` 가 받는 것은 **물리 인덱스**다. 그런데 여러 툴이 아래처럼 써 왔다:
#
#     idxs = om.MIntArray()
#     for d in fn.influenceObjects():
#         idxs.append(fn.indexForInfluenceObject(d))   # <- 논리 인덱스
#     fn.setWeights(dag, comp, idxs, weights, False)
#
# skinCluster 를 만든 직후에는 논리 = 물리(0,1,2,...)라 **잘 동작하는 것처럼 보인다**.
# 그래서 이 실수는 오래 살아남는다. 둘이 어긋나는 순간 터진다:
#
#     (kInvalidParameter): Object is incompatible with this method
#
# 어긋나는 대표 상황이 **undo** 다. 인플루언스를 추가한 뒤 Ctrl+Z 로 되돌리면 논리 인덱스는
# 회수되지 않아서, 다시 추가할 때 **새 번호**가 붙는다(실측: `matrix mi` 가 `[0,1,2]` →
# undo → `[0]` → 다시 추가 → **`[0,3,4]`**). 이 상태에서 논리 인덱스를 넘기면 위 에러가 나고,
# 사용자 눈에는 "Ctrl+Z 한 번 하면 그 뒤로 바인드가 안 된다"로 보인다.
# 인플루언스를 지웠다 다시 넣는 툴/스크립트를 쓴 씬도 같은 상태가 된다.
#
# 물리 인덱스로 넘기면 마야가 알아서 올바른 논리 슬롯에 쓴다(듬성한 상태에서 값을 써 넣고
# `skinPercent` 로 되읽어 확인 — `weightList[0].weights` 가 `{0:.., 3:.., 4:..}` 로 정확히 들어간다).
#
# 논리 인덱스가 필요한 곳은 따로 있다 — `.matrix[i]` / `.bindPreMatrix[i]` 같이 **플러그를 직접**
# 다룰 때다. 그때는 `logical_indices()` 를 쓴다.

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds


def skin_fn(skin_cluster):
    """skinCluster 이름 -> MFnSkinCluster."""
    if not skin_cluster or not cmds.objExists(skin_cluster):
        raise ValueError("'{0}' is not a node in the scene.".format(skin_cluster))
    sel = om.MSelectionList()
    sel.add(skin_cluster)
    return oma.MFnSkinCluster(sel.getDependNode(0))


def weight_indices(count):
    """`get/setWeights` 에 넘길 **물리 인덱스** 배열 `[0, 1, ... count-1]`.

    `count` 는 `len(fn.influenceObjects())` — 즉 `getWeights` 가 돌려주는 웨이트의 열 수다.
    (정수 대신 MFnSkinCluster 나 influenceObjects 결과를 줘도 받는다)
    """
    if isinstance(count, oma.MFnSkinCluster):
        count = len(count.influenceObjects())
    elif not isinstance(count, int):
        count = len(count)
    return om.MIntArray(range(int(count)))


def influence_paths(fn):
    """`getWeights` 의 **열 순서**대로인 인플루언스 롱네임 목록.

    웨이트 배열의 `row * n_inf + col` 에서 `col` 이 이 목록의 자리와 같다.
    """
    return [dag.fullPathName() for dag in fn.influenceObjects()]


def logical_indices(fn):
    """`.matrix[i]` / `.weightList[].weights[i]` 용 **논리 인덱스** 목록.

    플러그를 직접 다룰 때만 쓴다. `get/setWeights` 에는 `weight_indices()` 를 쓸 것.
    """
    return [int(fn.indexForInfluenceObject(dag)) for dag in fn.influenceObjects()]
