# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00460_ControllerTool - FK 컨트롤러 생성 (maya.cmds, UI 비의존)
#
# 조인트(또는 오브젝트) 하나마다 아래 스택을 만들고, 스택끼리 계층으로 잇는다.
#
#   <joint>_zro          zero-out 널 (조인트 자리 · 방향)
#   └── <joint>_con      오프셋 널
#       └── <joint>_ctl  ★ 애니메이터가 잡는 커브 컨트롤러
#           └── <joint>_tgt  조인트를 컨스트레인트하는 널
#               └── <child>_zro ...   (자식 조인트의 스택이 여기에 붙는다)
#
# 조인트는 자기 스택의 **마지막 노드**(보통 _tgt)를 따라간다.
# _zro / _con / _tgt 는 옵션이라 꺼면 스택에서 빠지고, 꺼진 만큼 위/아래가 직접 이어진다.
# _ctl 은 이 툴의 존재 이유이므로 항상 만든다.
#
# 좌표: 스택의 **최상단 노드만** matchTransform 으로 조인트 자리(위치+회전)에 맞추고,
# 나머지는 로컬 0 으로 부모 밑에 넣는다(relative parent). 그래서 셋 다 정확히 겹치고,
# 컨트롤러를 움직인 값이 곧 조인트 대비 오프셋이 된다. (A00170_driverTool 과 같은 방식)

import maya.cmds as cmds


# --------------------------------------------------------------- 상수

# 대상 해석 모드.
#   root  : 리스트업한 각 노드를 **체인의 루트**로 보고, 그 아래 자손까지 따라 내려간다.
#           분기(자식이 여럿)가 있으면 자식마다 스택이 갈라진다.
#   chain : 리스트업한 노드들이 **하나의 체인** — 씬 계층과 무관하게 리스트 순서로 잇는다.
MODE_ROOT = "root"
MODE_CHAIN = "chain"

CON_PARENT = "parent"
CON_POINT = "point"
CON_ORIENT = "orient"
CON_SCALE = "scale"

# 컨스트레인트 체크박스 순서(UI 와 공유). 기본은 parent 하나.
CONSTRAINT_TYPES = (CON_PARENT, CON_POINT, CON_ORIENT, CON_SCALE)
DEFAULT_CONSTRAINTS = (CON_PARENT,)

SUFFIX_ZRO = "_zro"
SUFFIX_CON = "_con"
SUFFIX_CTL = "_ctl"
SUFFIX_TGT = "_tgt"

# 컨트롤러 커브(원)의 법선 축. 조인트가 X 로 뻗는 마야 기본을 따라 X 가 기본이다.
AXIS_VECTORS = {
    "X": (1.0, 0.0, 0.0),
    "Y": (0.0, 1.0, 0.0),
    "Z": (0.0, 0.0, 1.0),
}
DEFAULT_AXIS = "X"
DEFAULT_SIZE = 1.0


# --------------------------------------------------------------- 헬퍼

def _short(node):
    """풀패스에서 짧은 이름만."""
    return node.split("|")[-1]


def _children_of(node):
    """ROOT 모드에서 따라 내려갈 자식 목록.

    루트가 조인트면 **조인트 자식만** 본다 — 조인트에 붙은 지오메트리나 이미 만들어 둔
    컨트롤러까지 끌려 들어오는 것을 막기 위해서다. 루트가 조인트가 아니면 트랜스폼 자식을
    본다(joint 도 transform 이라 함께 잡힌다).
    """
    try:
        is_joint = cmds.nodeType(node) == "joint"
    except Exception:
        is_joint = False

    kind = "joint" if is_joint else "transform"
    return cmds.listRelatives(node, children=True, type=kind, fullPath=True) or []


def _circle_control(name, size, axis):
    """FK 컨트롤러 커브 하나(원). 이름이 겹치면 마야가 뒤에 번호를 붙인다."""
    normal = AXIS_VECTORS.get(axis, AXIS_VECTORS[DEFAULT_AXIS])
    crv = cmds.circle(name=name, normal=normal, radius=float(size),
                      constructionHistory=False)[0]
    return crv


def _reparent(node, parent):
    """node 를 parent 밑으로 **로컬 트랜스폼 0 을 유지한 채** 넣는다.

    relative=True 라 월드 위치를 보존하지 않는다. 원점에서 만든 노드는 로컬 0 을 그대로
    유지하므로 결과적으로 부모 자리에 정확히 겹친다.
    """
    if not parent:
        return node
    result = cmds.parent(node, parent, relative=True)
    return result[0] if result else node


def _stack_plan(use_zro, use_con, use_tgt):
    """만들 노드의 (종류, 접미사) 순서 목록. _ctl 은 언제나 들어간다."""
    plan = []
    if use_zro:
        plan.append(("group", SUFFIX_ZRO))
    if use_con:
        plan.append(("group", SUFFIX_CON))
    plan.append(("curve", SUFFIX_CTL))
    if use_tgt:
        plan.append(("group", SUFFIX_TGT))
    return plan


def _create_stack(joint, parent_node, plan, size, axis, result):
    """조인트 하나에 대한 노드 스택을 만들고 (최상단, 최하단, 컨트롤러) 를 돌려준다."""
    base = _short(joint)
    cur_parent = parent_node
    top = None
    ctl = None

    for i, (kind, suffix) in enumerate(plan):
        name = "{0}{1}".format(base, suffix)

        if kind == "curve":
            node = _circle_control(name, size, axis)
        else:
            node = cmds.group(empty=True, name=name)

        # 이름이 이미 쓰이고 있으면 마야가 번호를 붙인다. 조용히 넘어가면 나중에
        # 어떤 노드가 어떤 조인트 것인지 헷갈리므로 알려 준다.
        if _short(node) != name:
            result["renamed"].append((name, _short(node)))

        node = _reparent(node, cur_parent)

        if i == 0:
            # 스택 최상단만 조인트 자리로. 아래는 로컬 0 이라 그대로 따라온다.
            # 스케일은 건드리지 않는다(컨트롤러 크기는 Size 로 정한다).
            cmds.matchTransform(node, joint, position=True, rotation=True)
            top = node

        if suffix == SUFFIX_CTL:
            ctl = node

        cur_parent = node

    return top, cur_parent, ctl


def _apply_constraints(driver, driven, types, result):
    """driver 가 driven 을 끌게 컨스트레인트를 건다."""
    for con_type in types:
        try:
            if con_type == CON_PARENT:
                made = cmds.parentConstraint(driver, driven, maintainOffset=True)
            elif con_type == CON_POINT:
                made = cmds.pointConstraint(driver, driven, maintainOffset=True)
            elif con_type == CON_ORIENT:
                made = cmds.orientConstraint(driver, driven, maintainOffset=True)
            elif con_type == CON_SCALE:
                made = cmds.scaleConstraint(driver, driven, maintainOffset=True)
            else:
                continue
            result["constraints"].extend(made or [])
        except Exception as exc:
            result["warnings"].append(
                "{0}Constraint failed on {1}: {2}".format(
                    con_type, _short(driven), exc))


# --------------------------------------------------------------- 빌드

def _build_one(joint, parent_node, plan, types, size, axis, result):
    """조인트 하나: 스택 생성 + 컨스트레인트. 스택의 **최하단**을 돌려준다."""
    top, last, ctl = _create_stack(joint, parent_node, plan, size, axis, result)

    result["controls"].append(ctl)
    if parent_node is None:
        result["roots"].append(top)

    _apply_constraints(last, joint, types, result)
    result["driven"].append(joint)

    return last


def _build_root_recursive(joint, parent_node, plan, types, size, axis,
                          result, seen):
    """ROOT 모드 — 조인트와 그 자손을 계층 그대로 따라 내려가며 스택을 잇는다."""
    if joint in seen:
        return
    seen.add(joint)

    last = _build_one(joint, parent_node, plan, types, size, axis, result)

    for child in _children_of(joint):
        _build_root_recursive(child, last, plan, types, size, axis, result, seen)


def build_fk_controls(nodes, mode=MODE_ROOT,
                      use_zro=True, use_con=True, use_tgt=True,
                      constraints=DEFAULT_CONSTRAINTS,
                      size=DEFAULT_SIZE, axis=DEFAULT_AXIS):
    """리스트업한 노드들에 FK 컨트롤러 계층을 만든다.

    nodes       : 조인트/오브젝트 이름 목록(리스트 순서 그대로 쓴다).
    mode        : MODE_ROOT(각 항목이 체인 루트, 자손까지 따라감) /
                  MODE_CHAIN(리스트 전체가 한 체인, 리스트 순서로 이음).
    use_zro/con/tgt : 만들 널 그룹 종류. _ctl 은 항상 만든다.
    constraints : CON_* 목록. 조인트는 스택의 마지막 노드(보통 _tgt)를 따라간다.
    size, axis  : 컨트롤러 원의 반지름과 법선 축.

    반환 dict:
        roots       계층 최상단 노드들
        controls    만들어진 _ctl 목록
        constraints 만들어진 컨스트레인트 노드
        driven      컨스트레인트가 걸린 조인트
        missing     씬에 없던 입력
        renamed     이름이 겹쳐 마야가 번호를 붙인 (원한 이름, 실제 이름)
        warnings    경고 문자열
    """
    result = {
        "roots": [], "controls": [], "constraints": [], "driven": [],
        "missing": [], "renamed": [], "warnings": [],
    }

    types = [t for t in CONSTRAINT_TYPES if t in (constraints or ())]
    if not types:
        result["warnings"].append(
            "No constraint type is checked - controls are built but the "
            "joints will not follow them.")

    # parent 는 T+R 을 함께 잡는다. point/orient 를 같이 걸면 같은 채널을 두 컨스트레인트가
    # 다투게 되어 결과가 예측하기 어려워진다. 막지는 않고 알려만 준다.
    if CON_PARENT in types and (CON_POINT in types or CON_ORIENT in types):
        result["warnings"].append(
            "Parent is checked together with Point/Orient - they drive the "
            "same channels and will fight. Use Parent alone, or Point+Orient.")

    plan = _stack_plan(use_zro, use_con, use_tgt)

    valid = []
    for node in (nodes or []):
        if not node or not cmds.objExists(node):
            result["missing"].append(node)
            continue
        valid.append(node)

    if not valid:
        return result

    if mode == MODE_ROOT:
        seen = set()
        for root in valid:
            _build_root_recursive(root, None, plan, types, size, axis,
                                  result, seen)
    else:
        parent_node = None
        for node in valid:
            parent_node = _build_one(node, parent_node, plan, types,
                                     size, axis, result)

    return result
