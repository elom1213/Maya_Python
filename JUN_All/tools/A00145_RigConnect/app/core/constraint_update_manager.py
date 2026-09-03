# -*- coding: utf-8 -*-
"""
constraint_update_manager - Constrain 탭 'Update' 로직 (maintain offset 재계산).

Attribute Editor 의 parentConstraint 에는 **Update** 버튼이 있다. constraint 가 걸린
오브젝트를 다른 자리로 옮긴 뒤 이 버튼을 누르면 offset 이 **지금 포즈 기준으로 다시
계산**되어, 옮긴 위치/회전 그대로 constraint 가 물린다. MEL 로 찍히는 명령은

    parentConstraint -e -maintainOffset curve2  curve1_parentConstraint1;

버튼은 한 번에 constraint 하나씩만 누를 수 있다. 여기서는 **리스트에 담은 constraint
전부**에 같은 동작을 돌린다. 계산은 우리가 다시 만들지 않고 Maya 명령을 그대로 쓴다 —
AE 버튼과 결과가 어긋날 이유가 없어야 하기 때문이다.

## Maya 2024 실측으로 확인한 것 (mayapy)

- `-e -maintainOffset` 을 받는 타입: **parent / point / orient / scale / aim /
  pointOnPoly**. `geometry` / `normal` / `tangent` / `poleVector` 는
  `Invalid flag 'mo'` 로 거절한다(맞출 offset 이 없는 타입) → 건너뛰고 경고.
- **타깃을 전부 넘겨야 한다.** 타깃 2개 중 하나만 넘기면 넘긴 슬롯의 offset 만 다시
  구워지고 나머지 슬롯은 옛 값 그대로 남는다 → weight 가 섞이는 순간 driven 이 튄다.
- **타깃이 아닌 오브젝트를 넘기면 타깃으로 추가된다**(`-e` 인데도 추가된다). 그래서
  이름을 새로 만들지 않고 지금 연결된 target 슬롯에서 그대로 읽어 넘긴다.
  `<type>Constraint -q -targetList` 는 **짧은 이름**이라 동명 노드에서 어긋나므로
  쓰지 않고, 연결을 역추적하는 `_target_entries()`(롱네임)를 쓴다.
- 타깃이 여럿이고 **weight 가 섞여 있어도 정확**하다(driven 월드 행렬 오차 4e-16).
- 이미 제자리인(= 아무도 움직이지 않은) constraint 에 돌리면 offset 값이 그대로다.
  무해한 no-op 이므로 목록에 섞여 있어도 상관없다. 다만 로그에는 값이 실제로 바뀐
  것만 `updated` 로, 그대로인 것은 `no change` 로 구분해 남긴다.

## driven 을 옮기는 방법 (참고)

constraint 가 살아 있으면 driven 의 채널이 연결되어 있어 그냥은 못 움직인다. 보통은
`blendParent1`(키가 있는 오브젝트에 constraint 를 걸면 Maya 가 만드는 pairBlend
어트리뷰트)을 0 으로 두고 옮긴 뒤 Update → 다시 1 로 되돌린다. 어떤 방법으로 옮겼든
이 명령은 **현재 월드 행렬**을 읽어 offset 을 굽는다.

UI 비의존: 위젯에서 읽은 이름 리스트만 받는다. (app/core <-> app/ui 분리)
"""

import maya.cmds as cmds

# 노드 해석 헬퍼는 Target Edit 과 완전히 같은 규칙이라 재사용한다.
from .constraint_transfer_manager import _path, _collect_constraint_uuids
from .constraint_target_manager import (
    _nice, _constraint_command, _driven, _target_entries, _world_matrix)


# `maintainOffset` 플래그 자체가 없는 타입 (Maya 2024 실측: "Invalid flag 'mo'").
UNSUPPORTED_TYPES = (
    "geometryConstraint",
    "normalConstraint",
    "tangentConstraint",
    "poleVectorConstraint",
)

# offset 값이 실제로 바뀌었는지 판정할 때 쓰는 허용 오차.
CHANGE_TOLERANCE = 1e-6

# 업데이트 뒤 driven 이 제자리인지 볼 때 쓰는 월드 행렬 성분 허용 오차.
MOVE_TOLERANCE = 1e-3


def _flatten(value):
    """getAttr 결과([(x, y, z)] / 스칼라 / 리스트)를 float 리스트로 편다."""
    out = []
    if isinstance(value, (list, tuple)):
        for item in value:
            out.extend(_flatten(item))
    elif isinstance(value, bool):
        out.append(float(value))
    elif isinstance(value, (int, float)):
        out.append(float(value))
    return out


def _offset_snapshot(cn):
    """constraint 노드의 offset 관련 플러그 값 {plug 이름: [float, ...]}.

    타입마다 offset 이 사는 곳이 다르다 — parent 는 타깃별
    `target[i].targetOffsetTranslate/Rotate`, point/orient/scale/aim 은 공유
    `.offset`, pointOnPoly 는 `.offsetTranslate/.offsetRotate`. 타입별 표를 두는
    대신 이름에 'offset' 이 든 플러그를 전부 훑는다(값 비교에만 쓰므로 넉넉해도 된다).
    constraint 노드도 트랜스폼이라 딸려 오는 `offsetParentMatrix` 는 뺀다.
    """
    try:
        attrs = cmds.listAttr(cn, multi=True) or []
    except Exception:
        attrs = []

    snap = {}
    for attr in attrs:
        leaf = attr.split(".")[-1].split("[")[0]
        if "offset" not in leaf.lower() or leaf == "offsetParentMatrix":
            continue
        try:
            snap[attr] = _flatten(cmds.getAttr("{0}.{1}".format(cn, attr)))
        except Exception:
            continue
    return snap


def _snapshot_differs(before, after):
    """offset 스냅샷 두 개가 (허용 오차 밖에서) 다른가."""
    if set(before) != set(after):
        return True
    for plug, old in before.items():
        new = after[plug]
        if len(old) != len(new):
            return True
        for a, b in zip(old, new):
            if abs(a - b) > CHANGE_TOLERANCE:
                return True
    return False


def _max_matrix_diff(before, after):
    """월드 행렬 두 개의 성분 최대 차이."""
    return max(abs(a - b) for a, b in zip(before, after))


def _constraint_targets(cn):
    """constraint 가 지금 쓰고 있는 타깃 롱네임들. (targets, 해석 실패 수, 중복 수)

    `-q -targetList` 대신 target 슬롯의 입력 연결을 역추적한다(동명 노드 안전).
    """
    targets = []
    missing = 0
    duplicates = 0
    for entry in _target_entries(cn):
        node = entry["node"]
        if not node:
            missing += 1
            continue
        if node in targets:
            duplicates += 1
            continue
        targets.append(node)
    return targets, missing, duplicates


# =========================================================== 공개 API

def update_offsets(constraint_names):
    """리스트의 constraint 들에 AE 의 'Update' (maintain offset 재계산)를 돌린다.

    Args:
        constraint_names: constraint 노드, 또는 constraint 가 걸린 트랜스폼 이름들
            (트랜스폼이면 그 아래 constraint 노드들로 확장된다).

    Returns:
        (results, warnings)
        results: [{"constraint": 표시 이름, "type": 노드 타입,
                   "targets": [타깃 표시 이름], "changed": bool, "note": ...}, ...]
    """
    if not constraint_names:
        raise ValueError("No constraints. Add constraints to the list.")

    con_uuids, warnings = _collect_constraint_uuids(constraint_names)

    # 같은 constraint 를 노드로도, 걸린 트랜스폼으로도 담았을 수 있다.
    unique_uuids = []
    for uuid in con_uuids:
        if uuid not in unique_uuids:
            unique_uuids.append(uuid)

    if not unique_uuids:
        raise ValueError("No valid constraints found in the list.")

    results = []

    for con_uuid in unique_uuids:
        cn = _path(con_uuid)
        if cn is None:
            continue
        name = _nice(cn)
        ctype = cmds.nodeType(cn)

        if ctype in UNSUPPORTED_TYPES:
            warnings.append(
                "Skipped {0} - {1} has no maintain offset to update.".format(
                    name, ctype))
            continue

        cmd = _constraint_command(cn)
        if cmd is None:
            warnings.append(
                "Skipped {0} - no command for node type '{1}'.".format(name, ctype))
            continue

        targets, missing, duplicates = _constraint_targets(cn)
        if missing:
            # 일부만 넘기면 나머지 슬롯의 offset 이 옛 값으로 남아 driven 이 튄다.
            warnings.append(
                "Skipped {0} - {1} target slot(s) could not be resolved; "
                "updating the rest would leave those offsets stale.".format(
                    name, missing))
            continue
        if not targets:
            warnings.append("Skipped {0} - it has no target.".format(name))
            continue
        if duplicates:
            warnings.append(
                "{0} : the same object fills {1} extra target slot(s) - Maya "
                "updates one of them only.".format(name, duplicates))

        driven = _driven(cn)
        before_world = None
        if driven is not None:
            try:
                before_world = list(_world_matrix(driven))
            except Exception:
                before_world = None

        before = _offset_snapshot(cn)
        try:
            cmd(*(targets + [cn]), edit=True, maintainOffset=True)
        except Exception as e:
            warnings.append("{0} : update failed - {1}".format(name, e))
            continue
        after = _offset_snapshot(cn)

        note = ""
        if before_world is not None:
            try:
                moved = _max_matrix_diff(before_world, list(_world_matrix(driven)))
            except Exception:
                moved = 0.0
            if moved > MOVE_TOLERANCE:
                # offset 으로 표현할 수 없는 차이(타깃 스케일 등)가 있었다는 뜻.
                note = "driven moved by {0:.4g}".format(moved)
                warnings.append(
                    "{0} : the driven object '{1}' moved by {2:.4g} after the "
                    "update.".format(name, _nice(driven), moved))

        results.append({
            "constraint": name,
            "type": ctype,
            "targets": [_nice(t) for t in targets],
            "changed": _snapshot_differs(before, after),
            "note": note,
        })

    return results, warnings
