# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00440_SetTool - 집합 연산 (순수 파이썬, Maya 무의존)
#
# 원소는 "정규화된 멤버 문자열"(예: `|grp1|pCube1.vtx[3]`)이다. 정규화는 maya_sets 가
# 담당하고, 여기서는 이미 정규화된 리스트만 다룬다. 그래서 이 모듈은 mayapy 없이도
# 그대로 테스트할 수 있다.
#
# ── 왜 파이썬 set 을 그대로 쓰지 않는가 ────────────────────────────────────
# `set` 은 순서를 잃는다. 컴포넌트는 인덱스 순으로 보이는 편이 사람이 읽기 좋고,
# Difference 는 애초에 순서(무엇에서 무엇을 빼는지)가 의미를 갖는다.
# 그래서 판정에만 set 을 쓰고 결과는 dict(삽입 순서 유지) 로 만든다.
#
# ── 컴포넌트 종류 ──────────────────────────────────────────────────────────
# 지금은 "모든 세트가 같은 종류" 를 가정해도 되지만, 훗날 버텍스 세트와 엣지 세트를
# 섞는 상황을 상정해 **연산 자체는 종류를 가리지 않게** 만들었다.
# 서로 다른 종류의 원소는 그냥 서로 다른 원소이므로 ∪ / ∩ / ∖ 는 그대로 성립한다.
# 종류는 `group_by_type()` / `type_summary()` 로 따로 조회해 경고에만 쓴다.

from collections import OrderedDict

# 오브젝트(컴포넌트가 아닌 노드) 를 가리키는 종류 이름
OBJECT_TYPE = "object"

# 컴포넌트 종류 토큰 -> 사람이 읽는 이름. 없는 토큰은 토큰 그대로 쓴다.
TYPE_LABELS = {
    "vtx": "vertex",
    "e": "edge",
    "f": "face",
    "map": "uv",
    "vtxFace": "vertex face",
    "cv": "cv",
    "ep": "edit point",
    "pt": "lattice point",
    "u": "u iso",
    "v": "v iso",
    OBJECT_TYPE: "object",
}


# ==========================================================================
# 종류 판별
# ==========================================================================

def component_type(member):
    """멤버 문자열의 컴포넌트 종류 토큰. 컴포넌트가 아니면 OBJECT_TYPE.

        "|grp1|pCube1.vtx[3]"  -> "vtx"
        "|grp1|pCube1.map[12]" -> "map"
        "|nrb1.cv[0][1]"       -> "cv"
        "|grp1|pCube1"         -> "object"

    DAG 경로에는 `|` 가 들어가므로, **마지막 `|` 뒤**에서만 `.` 를 찾는다.
    (경로 중간의 노드 이름에 `.` 가 있을 일은 없지만 규칙을 명확히 해 둔다.)
    """
    if not member:
        return OBJECT_TYPE

    tail = member.rsplit("|", 1)[-1]

    if "." not in tail:
        return OBJECT_TYPE

    attribute = tail.split(".", 1)[1]

    # "vtx[3]" -> "vtx", "cv[0][1]" -> "cv"
    return attribute.split("[", 1)[0] or OBJECT_TYPE


def type_label(token):
    """종류 토큰의 표시용 이름."""
    return TYPE_LABELS.get(token, token)


def group_by_type(members):
    """종류별로 나눈 OrderedDict. 등장 순서를 유지한다."""
    grouped = OrderedDict()

    for member in members:
        grouped.setdefault(component_type(member), []).append(member)

    return grouped


def type_summary(members):
    """'vertex x120' / 'vertex x120, edge x8' 같은 한 줄 요약."""
    grouped = group_by_type(members)

    if not grouped:
        return "empty"

    return ", ".join(
        "{0} x{1}".format(type_label(token), len(items))
        for token, items in grouped.items()
    )


def is_mixed(members):
    """한 묶음 안에 서로 다른 종류가 섞여 있는가."""
    return len(group_by_type(members)) > 1


def common_type(groups):
    """여러 묶음이 모두 같은 한 종류인지. 같으면 그 토큰, 아니면 None."""
    tokens = set()

    for members in groups:
        tokens.update(group_by_type(members).keys())

    if len(tokens) == 1:
        return tokens.pop()

    return None


# ==========================================================================
# 집합 연산
# ==========================================================================

def ordered_unique(members):
    """순서를 유지하면서 중복 제거."""
    return list(OrderedDict.fromkeys(members))


def union(*groups):
    """A ∪ B ∪ ... — 등장 순서대로 이어붙이고 중복 제거."""
    merged = []

    for members in groups:
        merged.extend(members)

    return ordered_unique(merged)


def intersection(*groups):
    """A ∩ B ∩ ... — 모든 묶음에 들어 있는 원소만. 순서는 첫 묶음 기준."""
    if not groups:
        return []

    first = ordered_unique(groups[0])

    if len(groups) == 1:
        return first

    rest = [set(members) for members in groups[1:]]

    return [m for m in first if all(m in other for other in rest)]


def difference(first, *rest):
    """A ∖ B ∖ ... — 첫 묶음에서 나머지에 들어 있는 원소를 뺀다.

    **순서가 의미를 갖는 유일한 연산**이다. 첫 인자가 감수(minuend).
    """
    kept = ordered_unique(first)

    if not rest:
        return kept

    removed = set()

    for members in rest:
        removed.update(members)

    return [m for m in kept if m not in removed]


def split(members, picked):
    """A 와 선택 S 로부터 (A∖S, A∩S) 를 만든다.

    집합론에서 이 두 조각 {A∖S, A∩S} 는 **S 가 A 에 유도하는 분할(partition)** 이고,
    A = (A∖S) ⊔ (A∩S) 로 서로소 합집합이 된다.
    - A∩S 는 A 위에서의 S 의 **자취(trace)**
    - A∖S 는 A 에 대한 S 의 **상대여집합(relative complement)**
    단일한 표준 연산자 이름은 없어서 구현체들은 보통 split / partition / extract 라 부른다.

    반환: (남는 것, 빼낸 것)
    """
    picked_set = set(picked)

    kept = []
    extracted = []

    for member in ordered_unique(members):
        if member in picked_set:
            extracted.append(member)
        else:
            kept.append(member)

    return kept, extracted
