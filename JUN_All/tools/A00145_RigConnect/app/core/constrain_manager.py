# -*- coding: utf-8 -*-
"""
constrain_manager - Constrain 탭 로직.

MEL ConnectionTool V04.02 의 JUN_cmd_constrain_tgt_to_flw 포팅.
targets(드라이버 역할) 가 followers 를 따라가도록 constraint 를 건다.

UI 비의존: 위젯에서 읽은 list/str/bool 값만 받는다. (app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds


# 라디오 버튼 순서/라벨 = MEL radioCollection 순서.
# (key, label) — key 로 cmds 함수를 디스패치한다.
CONSTRAIN_TYPES = [
    ("parent", "Parent"),
    ("scale", "Scale"),
    ("point", "Point"),
    ("orient", "Orient"),
    ("pointOnPoly", "Point On Poly"),
]

# key -> cmds.*Constraint 함수명.
_CON_CMD = {
    "parent": "parentConstraint",
    "scale": "scaleConstraint",
    "point": "pointConstraint",
    "orient": "orientConstraint",
    "pointOnPoly": "pointOnPolyConstraint",
}


def constrain(targets, followers, con_type, maintain_offset=True):
    """targets -> followers 로 constraint 연결.

    MEL 동작 그대로:
      - followers 가 targets 보다 많고 target 이 1개면 단일 target 을 모든 follower 에 브로드캐스트.
      - 그 외에는 인덱스 1:1.
    Maya constraint 는 (target, follower) 순으로 호출해 target 이 follower 를 드라이브한다.

    Args:
        targets: 타겟(드라이버) 오브젝트 리스트.
        followers: 팔로워(구속될) 오브젝트 리스트.
        con_type: CONSTRAIN_TYPES 의 key ("parent"/"scale"/"point"/"orient"/"pointOnPoly").
        maintain_offset: constraint 의 maintain offset 옵션.

    Returns:
        생성된 constraint 노드명 리스트.
    """
    if not targets:
        raise ValueError("No target objects. Add objects to the Targets list.")
    if not followers:
        raise ValueError("No follower objects. Add objects to the Followers list.")
    if con_type not in _CON_CMD:
        raise ValueError("Unknown constraint type: {0}".format(con_type))

    con_func = getattr(cmds, _CON_CMD[con_type])

    made = []
    all_size = max(len(followers), len(targets))
    for i in range(all_size):
        # follower 인덱스가 범위를 벗어나면 중단 (MEL 의 빈 문자열 동작 방지).
        if i >= len(followers):
            break
        # target 이 1개면 항상 0번을 사용(브로드캐스트), 아니면 i.
        idx_tgt = 0 if len(targets) == 1 else i
        if idx_tgt >= len(targets):
            break

        result = con_func(targets[idx_tgt], followers[i], mo=maintain_offset)
        if result:
            made.append(result[0])

    return made
