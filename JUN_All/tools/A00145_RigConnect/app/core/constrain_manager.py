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


# key -> 그 constraint 가 구동하는 채널 그룹 (t=translate, r=rotate, s=scale). (v01.47)
# 여러 종류를 한 번에 걸 때 **채널이 겹치면 안 된다** — 마야가 두 번째를
# `Object is already connected.` 로 거절한다(실측: parent+point, parent+orient).
# parent+scale, point+orient+scale 은 겹치지 않아 함께 걸린다(실측).
# pointOnPoly 는 translate + rotate 를 구동하고(실측), 타깃이 버텍스라 scale 과도 못 섞는다
# → 모든 채널을 차지하는 것으로 두어 **혼자만** 쓰이게 한다.
CONSTRAIN_CHANNELS = {
    "parent": "tr",
    "scale": "s",
    "point": "t",
    "orient": "r",
    "pointOnPoly": "trs",
}


def types_conflict(type_a, type_b):
    """두 종류가 같은 채널을 구동해 함께 걸 수 없으면 True."""
    return bool(set(CONSTRAIN_CHANNELS[type_a]) & set(CONSTRAIN_CHANNELS[type_b]))


def validate_types(con_types):
    """함께 걸 종류 목록을 검사한다. 문제가 없으면 None, 있으면 이유 문자열."""
    if not con_types:
        return "No constraint type is checked."
    unknown = [t for t in con_types if t not in _CON_CMD]
    if unknown:
        return "Unknown constraint type: {0}".format(", ".join(unknown))
    labels = dict(CONSTRAIN_TYPES)
    for i, a in enumerate(con_types):
        for b in con_types[i + 1:]:
            if types_conflict(a, b):
                return "{0} and {1} drive the same channels - Maya cannot put both on " \
                       "one object.".format(labels[a], labels[b])
    return None


def get_constraint_func(con_type):
    """CONSTRAIN_TYPES 의 key 에 대응하는 cmds.*Constraint 함수를 반환한다.

    Args:
        con_type: CONSTRAIN_TYPES 의 key ("parent"/"scale"/"point"/"orient"/"pointOnPoly").

    Returns:
        cmds 의 constraint 함수.
    """
    if con_type not in _CON_CMD:
        raise ValueError("Unknown constraint type: {0}".format(con_type))
    return getattr(cmds, _CON_CMD[con_type])


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
    con_func = get_constraint_func(con_type)

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


def constrain_types(targets, followers, con_types, maintain_offset=True):
    """targets -> followers 로 **여러 종류**의 constraint 를 함께 건다 (v01.47).

    예) ["parent", "scale"] / ["point", "orient"] / ["point", "orient", "scale"].
    target/follower 짝을 맞추는 규칙은 `constrain()` 과 같다(target 1개면 브로드캐스트, 아니면 1:1).
    종류 목록은 먼저 `validate_types` 로 검사한다 - 채널이 겹치면 **아무것도 걸지 않고** 예외.

    한 follower 에서 한 종류가 실패해도(이미 연결된 채널 등) **나머지는 계속 건다** —
    실패는 `errors` 로 돌려준다.

    Returns:
        (made, errors)
          made   : [(con_type, constraint 노드명), ...]
          errors : ["<follower> <- <target> (<label>): <이유>", ...]
    """
    problem = validate_types(list(con_types))
    if problem:
        raise ValueError(problem)
    if not targets:
        raise ValueError("No target objects. Add objects to the Targets list.")
    if not followers:
        raise ValueError("No follower objects. Add objects to the Followers list.")

    labels = dict(CONSTRAIN_TYPES)
    ordered = [key for key, _label in CONSTRAIN_TYPES if key in con_types]

    made = []
    errors = []
    for i, follower in enumerate(followers):
        idx_tgt = 0 if len(targets) == 1 else i
        if idx_tgt >= len(targets):
            break
        target = targets[idx_tgt]
        for con_type in ordered:
            try:
                result = get_constraint_func(con_type)(target, follower, mo=maintain_offset)
            except Exception as e:
                errors.append("{0} <- {1} ({2}): {3}".format(
                    follower, target, labels[con_type], str(e).strip()))
                continue
            if result:
                made.append((con_type, result[0]))

    return made, errors
