# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-07
# A00460_ControllerTool - FK / IK 컨트롤러 생성 (maya.cmds, UI 비의존)
#
# 조인트(또는 오브젝트) 하나마다 아래 스택을 만든다.
#
#   <joint>_zro          zero-out 널 (조인트 자리 · 방향)
#   └── <joint>_con      오프셋 널
#       └── <joint>_ctl  ★ 애니메이터가 잡는 커브 컨트롤러
#           ├── <joint>_tgt      조인트를 컨스트레인트하는 널 — **잎이다(자식 없음)**
#           └── <child>_zro ...  자식 스택은 **_ctl 밑에** 붙는다 (FK 계층일 때)
#
# 조인트는 자기 스택의 **마지막 노드**(보통 _tgt)를 따라간다.
# _zro / _con / _tgt 는 옵션이라 끄면 스택에서 빠지고, 꺼진 만큼 위/아래가 직접 이어진다.
# _ctl 은 이 툴의 존재 이유이므로 항상 만든다.
#
# ## 자식 스택은 _tgt 가 아니라 _ctl 밑에 (v01.04~)
#
# 예전에는 자식 `_zro` 가 `_tgt` 밑으로 들어가서 `_tgt` 가 "컨스트레인트 드라이버" 와
# "다음 뼈의 부모" 두 역할을 겸했다. 결과는 같지만(둘 다 `_ctl` 에 로컬 0 으로 붙어 있어
# 월드 행렬이 동일) `_tgt` 에 자식이 달려 있으면 그것만 따로 옮기거나 지우기 어렵다.
# 이제 **`_tgt` 는 잎으로 남고** 자식 스택은 `_ctl` 밑에 붙는다.
#
# ## 계층 방식 — FK / IK
#
#   fk : 스택끼리 **계층으로 잇는다.** 부모 컨트롤러를 돌리면 자식이 딸려 온다(FK 감각).
#   ik : 스택을 **하나도 잇지 않는다.** 모든 `_zro` 가 **씬 최상위(월드)** 에 선다.
#        리스트에 자식 계층이 있는 오브젝트가 섞여 있어도 마찬가지다. 컨트롤러끼리
#        서로를 끌지 않으므로 각자 월드에서 독립으로 움직인다(IK 감각).
#
# 이 선택은 **대상 해석 모드(Bone Root / Bone Chain)와 별개**다. 모드는 "누구에게 컨트롤러를
# 만들까", 계층 방식은 "만든 것끼리 어떻게 이을까" 를 정한다. 네 조합이 모두 성립한다.
#
# 좌표: 스택의 **최상단 노드만** matchTransform 으로 조인트 자리(위치+회전)에 맞추고,
# 나머지는 로컬 0 으로 부모 밑에 넣는다(relative parent). 그래서 셋 다 정확히 겹치고,
# 컨트롤러를 움직인 값이 곧 조인트 대비 오프셋이 된다. (A00170_driverTool 과 같은 방식)
# IK 도 최상단을 조인트 자리에 맞추는 것은 같다 — 부모가 없을 뿐이다.

import maya.cmds as cmds


# --------------------------------------------------------------- 상수

# 대상 해석 모드.
#   root  : 리스트업한 각 노드를 **체인의 루트**로 보고, 그 아래 자손까지 따라 내려간다.
#           분기(자식이 여럿)가 있으면 자식마다 스택이 갈라진다.
#   chain : 리스트업한 노드들이 **하나의 체인** — 씬 계층과 무관하게 리스트 순서로 잇는다.
MODE_ROOT = "root"
MODE_CHAIN = "chain"

MODES = (MODE_ROOT, MODE_CHAIN)

# 계층 방식 — 만든 스택끼리 **어떻게 이을지**. 대상 해석 모드와 별개다.
#   fk : 스택을 계층으로 잇는다(자식 _zro 가 부모 _ctl 밑으로).
#   ik : 잇지 않는다 — 모든 _zro 가 씬 최상위(월드)에 선다.
HIER_FK = "fk"
HIER_IK = "ik"

HIERARCHIES = (HIER_FK, HIER_IK)

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

# 컨트롤러 커브 = **정육면체 테두리**(degree 1). A00145_RigConnect 의 Match 탭이 쓰는
# cube 컨트롤(MEL JUN_get_cubeCtl 이식)과 같은 CV 데이터다. 한 붓 그리기로 12개 모서리를
# 모두 지나가며, 좌표는 ±0.5(한 변 1) 단위 큐브다.
_CUBE_POINTS = [
    (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
    (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
    (0.5, -0.5, 0.5),
]

# Control Size 는 **반지름 감각**(큐브 반변길이)이다. 원 컨트롤을 쓰던 때와 같은 숫자로
# 비슷한 크기가 나오도록, ±0.5 인 원본 좌표에 size*2 를 곱한다 → 반변길이 = size.
DEFAULT_SIZE = 1.0


# --------------------------------------------------------------- 헬퍼

def _short(node):
    """풀패스에서 짧은 이름만."""
    return node.split("|")[-1]


def _long(node):
    """풀패스. 같은 노드를 두 이름으로 만나도 하나로 세기 위한 것이다.

    ROOT 모드의 `seen` 이 **입력 그대로의 문자열**을 담으면, 사용자가 루트와 그 자식을
    함께 리스트에 담았을 때 같은 조인트를 두 번 만난다 — 재귀는 `_children_of` 가 준
    풀패스(`|a|b`)로, 바깥 루프는 사용자가 넣은 짧은 이름(`b`)으로. 그러면 **에러 없이**
    `b_zro1` 스택이 하나 더 생긴다. 비교는 언제나 풀패스로 한다.
    """
    found = cmds.ls(node, long=True) or []
    return found[0] if found else node


def _is_constraint(node):
    """컨스트레인트 노드인가.

    마야의 컨스트레인트는 **트랜스폼이고 구동 대상의 자식으로** 생긴다
    (`locator1` 을 걸면 `locator1|locator1_parentConstraint1`). 상속 타입에 `constraint`
    가 들어 있는지로 판별하면 parent/point/orient/scale/aim 등을 전부 잡는다.
    """
    try:
        return "constraint" in (cmds.nodeType(node, inherited=True) or [])
    except Exception:
        return False


def _children_of(node):
    """ROOT 모드에서 따라 내려갈 자식 목록.

    루트가 조인트면 **조인트 자식만** 본다 — 조인트에 붙은 지오메트리나 이미 만들어 둔
    컨트롤러까지 끌려 들어오는 것을 막기 위해서다. 루트가 조인트가 아니면 트랜스폼 자식을
    본다(joint 도 transform 이라 함께 잡힌다).

    ⚠️ **컨스트레인트 노드는 제외한다.** 이 함수는 스택을 만들고 컨스트레인트를 건 *뒤에*
    불리므로, 거르지 않으면 방금 만든 컨스트레인트를 '체인의 다음 뼈'로 착각해
    `locator1_parentConstraint1_zro` 같은 계층을 또 만든다. 대상에 예전 컨스트레인트가
    이미 걸려 있던 경우도 같은 이유로 걸러진다.
    """
    try:
        is_joint = cmds.nodeType(node) == "joint"
    except Exception:
        is_joint = False

    kind = "joint" if is_joint else "transform"
    kids = cmds.listRelatives(node, children=True, type=kind, fullPath=True) or []
    return [k for k in kids if not _is_constraint(k)]


def _cube_control(name, size):
    """FK 컨트롤러 커브 하나(정육면체 테두리). 이름이 겹치면 마야가 뒤에 번호를 붙인다."""
    scale = float(size) * 2.0          # ±0.5 원본 → 반변길이 = size
    points = [(x * scale, y * scale, z * scale) for x, y, z in _CUBE_POINTS]
    crv = cmds.curve(degree=1, point=points, knot=list(range(len(points))))
    return cmds.rename(crv, name)


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


def _create_stack(joint, parent_node, plan, size, result):
    """조인트 하나에 대한 노드 스택을 만들고 (최상단, 최하단, 컨트롤러) 를 돌려준다."""
    base = _short(joint)
    cur_parent = parent_node
    top = None
    ctl = None

    for i, (kind, suffix) in enumerate(plan):
        name = "{0}{1}".format(base, suffix)

        if kind == "curve":
            node = _cube_control(name, size)
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

def _build_one(joint, parent_node, plan, types, size, result):
    """조인트 하나: 스택 생성 + 컨스트레인트. **자식 스택을 붙일 노드**를 돌려준다.

    조인트를 끄는 것은 스택의 **마지막 노드**(보통 `_tgt`)지만, 다음 스택이 붙는 곳은
    **`_ctl`** 이다. 두 역할을 나눠 두어야 `_tgt` 가 잎으로 남는다(모듈 상단 참고).
    """
    top, last, ctl = _create_stack(joint, parent_node, plan, size, result)

    result["controls"].append(ctl)
    if parent_node is None:
        result["roots"].append(top)

    _apply_constraints(last, joint, types, result)
    result["driven"].append(joint)

    return ctl


def _build_root_recursive(joint, parent_node, plan, types, size,
                          result, seen, hierarchy):
    """ROOT 모드 — 조인트와 그 자손을 따라 내려가며 스택을 만든다.

    자손을 **따라가는 것**과 스택을 **잇는 것**은 별개다. IK 계층에서는 자손까지 그대로
    돌지만 부모를 넘기지 않아 모든 스택이 월드에 선다.
    """
    key = _long(joint)
    if key in seen:
        return
    seen.add(key)

    anchor = _build_one(joint, parent_node, plan, types, size, result)
    child_parent = anchor if hierarchy == HIER_FK else None

    for child in _children_of(joint):
        _build_root_recursive(child, child_parent, plan, types, size,
                              result, seen, hierarchy)


def build_controls(nodes, mode=MODE_ROOT, hierarchy=HIER_FK,
                   use_zro=True, use_con=True, use_tgt=True,
                   constraints=DEFAULT_CONSTRAINTS,
                   size=DEFAULT_SIZE):
    """리스트업한 노드들에 컨트롤러 스택을 만든다.

    nodes       : 조인트/오브젝트 이름 목록(리스트 순서 그대로 쓴다).
    mode        : **누구에게 만들까** — MODE_ROOT(각 항목이 체인 루트, 자손까지 따라감) /
                  MODE_CHAIN(리스트에 담긴 것만, 리스트 순서로 본다).
    hierarchy   : **만든 것끼리 어떻게 이을까** — HIER_FK(스택을 계층으로 잇는다) /
                  HIER_IK(잇지 않는다. 모든 _zro 가 씬 최상위에 선다).
                  mode 와 별개라 네 조합이 모두 성립한다.
    use_zro/con/tgt : 만들 널 그룹 종류. _ctl 은 항상 만든다.
    constraints : CON_* 목록. 조인트는 스택의 마지막 노드(보통 _tgt)를 따라간다.
    size        : 컨트롤러 큐브의 반변길이(반지름 감각).

    반환 dict:
        roots       부모가 없는 최상단 노드들 (IK 면 스택마다 하나씩)
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

    if hierarchy not in HIERARCHIES:
        hierarchy = HIER_FK

    if mode == MODE_ROOT:
        seen = set()
        for root in valid:
            _build_root_recursive(root, None, plan, types, size,
                                  result, seen, hierarchy)
    else:
        parent_node = None
        for node in valid:
            anchor = _build_one(node, parent_node, plan, types, size, result)
            # IK 는 다음 스택에 부모를 넘기지 않는다 — 전부 월드에 선다.
            parent_node = anchor if hierarchy == HIER_FK else None

    return result
