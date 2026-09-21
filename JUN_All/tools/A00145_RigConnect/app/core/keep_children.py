# -*- coding: utf-8 -*-
"""
keep_children - **부모를 옮겨도 그 아래 오브젝트는 있던 자리에 두는** 공용 로직.

Mirror 탭의 `Apply (Source -> Target)` 와 Match 탭이 함께 쓴다(원래 `mirror_manager` 안에만
있던 것을 v01.53 에서 떼어 냈다 — 두 탭이 **같은 규칙**으로 움직여야 쓰는 사람이 헷갈리지 않는다).

쓰는 순서는 언제나 이렇다.

    kept = keep_children.capture(parent, skip_paths)   # 아무것도 옮기기 전에
    ... 부모를 옮긴다 ...
    keep_children.restore(kept, parent_flipped, warnings, keyed_plugs)

**읽기를 먼저, 그것도 전부 몰아서** 한다 — 앞 줄의 오브젝트가 움직이면 그 아래 자식도 함께
밀리므로, 옮기기 시작한 뒤에 읽으면 이미 늦은 값이다.

## 직계 자식만 본다

자식 하나를 월드에 붙잡아 두면 그 아래 손자들은 **로컬이 그대로**라 저절로 제자리다.
그래서 직계 자식만 읽고 되돌린다(수천 개짜리 계층에서도 비용이 자식 수에 비례한다).

## 못 잡는 자식은 건너뛰고 알린다

`cmds.xform` 은 **잠긴 채널을 에러 없이 건너뛰고 나머지만** 쓴다(이동만 되고 회전은 안 되는
반쪽 결과). 그래서 쓰기 전에 막힌 채널을 먼저 찾고, 하나라도 막혀 있으면 그 자식은 **아예
건드리지 않고**(부모를 따라간 채로 남는다) 이유를 경고로 남긴다.

## 손계(handedness)

부모가 좌우손계를 바꿨으면(Reflect <-> 그 밖) 자식이 월드에서 그대로 있기 위해 자기 로컬의
손계가 바뀌어야 한다 — 즉 `scale` 부호를 써야 하므로 그때만 scale 채널까지 검사한다.
"""

import maya.cmds as cmds


#: 되돌린 결과가 이만큼 어긋나면 "정확히는 못 잡았다" 고 알린다.
APPLY_TOLERANCE = 1e-4


def short(node):
    """DAG 경로를 뗀 짧은 이름(네임스페이스는 남긴다)."""
    return node.split("|")[-1]


def is_constraint(node):
    """*Constraint 노드인가. 타입 상속으로 판정한다(이름 규칙에 기대지 않는다)."""
    return "constraint" in (cmds.nodeType(node, inherited=True) or [])


def determinant3(matrix):
    """월드 행렬 16개 값의 회전/스케일 3x3 부분의 행렬식. 음수면 왼손계."""
    m = matrix
    return (m[0] * (m[5] * m[10] - m[6] * m[9])
            - m[1] * (m[4] * m[10] - m[6] * m[8])
            + m[2] * (m[4] * m[9] - m[5] * m[8]))


def plug_blocker(plug):
    """plug 에 값을 쓸 수 없는 이유. 쓸 수 있으면 None, 키가 걸려 있으면 'keyed'.

    `getAttr(settable=True)` 는 컨스트레인트가 구동해도 True 라 쓸 수 없다 - 연결로 판정한다.
    """
    if cmds.getAttr(plug, lock=True):
        return "locked"
    if not cmds.connectionInfo(plug, isDestination=True):
        return None
    sources = cmds.listConnections(plug, source=True, destination=False,
                                   skipConversionNodes=True) or []
    # 키만 걸린 채널은 값이 들어간다(시간을 바꾸면 커브 값으로 돌아간다).
    # 애님 레이어(animBlendNode*) · pairBlend · 컨스트레인트는 값이 안 남는다.
    if sources and all(cmds.nodeType(src).startswith("animCurve") for src in sources):
        return "keyed"
    return "connected"


def channel_blockers(node, channels):
    """channels(translate/rotate/scale) 중 막힌 plug 와 키 걸린 plug.

    반환: (blocked [(plug, 이유)], keyed [plug])
    """
    blocked, keyed = [], []
    for channel in channels:
        for plug in [node + "." + channel] + [node + "." + channel + a for a in "XYZ"]:
            if not cmds.objExists(plug):
                continue
            reason = plug_blocker(plug)
            if reason == "keyed":
                keyed.append(plug)
            elif reason:
                blocked.append((plug, reason))
    return blocked, keyed


def capture(node, skip_paths=()):
    """node 의 직계 자식 트랜스폼 중 제자리에 둘 것과 **지금** 월드 행렬. [(롱네임, matrix)]

    skip_paths : 여기 들어 있는 자식은 제외한다(롱네임 집합). 그 자신이 이 작업의 대상이라
                 제 차례에 절대 위치로 놓이는 오브젝트를 넣는다 — Mirror 는 Target,
                 Match 는 Follower 다.
    컨스트레인트 노드도 제외한다(driven 밑에 붙어 있을 뿐 위치에 의미가 없다).
    조인트는 트랜스폼이라 포함된다.
    """
    kept = []
    for child in cmds.listRelatives(node, children=True, fullPath=True) or []:
        if child in skip_paths:
            continue
        if "transform" not in (cmds.nodeType(child, inherited=True) or []):
            continue                     # shape
        if is_constraint(child):
            continue
        kept.append((child, cmds.xform(child, query=True, worldSpace=True, matrix=True)))
    return kept


def restore(kept, parent_flipped=False, warnings=None, keyed_plugs=None):
    """부모를 옮긴 뒤 자식들을 읽어 둔 월드 행렬로 되돌린다.

    반환: (되돌린 수, 스케일 부호가 바뀐 수)
    """
    if warnings is None:
        warnings = []
    if keyed_plugs is None:
        keyed_plugs = []

    restored = 0
    flipped = 0
    for child, matrix in kept:
        current = cmds.xform(child, query=True, worldSpace=True, matrix=True)
        if max(abs(a - b) for a, b in zip(current, matrix)) <= APPLY_TOLERANCE:
            restored += 1                 # 부모가 안 움직였다(값이 이미 같다)
            continue

        channels = ["translate", "rotate"] + (["scale"] if parent_flipped else [])
        blocked, keyed = channel_blockers(child, channels)
        if blocked:
            warnings.append("Child '{0}' could not be kept in place and followed its "
                            "parent - {1}.".format(
                                short(child),
                                ", ".join("{0} is {1}".format(plug.split(".", 1)[1], why)
                                          for plug, why in blocked[:3])
                                + (" ..." if len(blocked) > 3 else "")))
            continue

        cmds.xform(child, worldSpace=True, matrix=matrix)
        result = cmds.xform(child, query=True, worldSpace=True, matrix=True)
        if max(abs(a - b) for a, b in zip(result, matrix)) > APPLY_TOLERANCE:
            warnings.append("Child '{0}' could not be kept exactly in place (a pivot, "
                            "limit or non-uniform parent scale got in the way) - check "
                            "it.".format(short(child)))
        restored += 1
        keyed_plugs.extend(keyed)
        if parent_flipped:
            flipped += 1
    return restored, flipped
