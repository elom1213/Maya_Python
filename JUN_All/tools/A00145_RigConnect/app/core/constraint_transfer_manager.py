# -*- coding: utf-8 -*-
"""
constraint_transfer_manager - Constrain 탭 'Constraint Transfer' 로직.

이미 걸려 있는 constraint 를 '다른 오브젝트에 걸리도록' 옮긴다. 어떤 종류의
constraint(parent/point/orient/scale/aim/poleVector/geometry/pointOnPoly/normal/
tangent) 든, 원본을 지우고 '세팅이 같은' constraint 를 오른쪽(대상) 오브젝트에 새로
만든다.

  before:  [targets] --(parentConstraint, MO)--> objA        (objA 가 driven)
  after :  [targets] --(parentConstraint, MO)--> objB        (원본 삭제, objB 로 이관)

핵심 보장:
- **Maintain Offset**: 새 constraint 는 항상 maintainOffset=True 로 만들어, 대상
  오브젝트가 현재 위치에서 튀지 않는다. 원본 driven 오브젝트도 삭제 후 월드 트랜스폼을
  복원해 그대로 둔다. => 명령 전후 두 오브젝트 모두 위치/회전 불변.
- **세팅 복제**: constraint 타입, 타깃(드라이버) 목록, 타깃별 weight, aim 계열의
  aim/up/worldUp 설정, parent/orient 의 interpType 을 그대로 옮긴다.
- **UUID 기반**: constraint 노드·타깃·driven·대상 오브젝트를 모두 UUID 로 잡아, 같은
  이름의 오브젝트가 여럿이어도 안전하게 동작한다.

매핑(왼쪽 constraint 목록 <-> 오른쪽 오브젝트 목록):
- 오른쪽이 1개면: 모든 constraint 를 그 오브젝트 하나로 옮긴다.
- 개수가 같으면: 인덱스 1:1.
- 그 외: 적은 쪽 개수만큼 1:1, 경고.
왼쪽 항목이 constraint 가 아니라 일반 트랜스폼이면, 그 트랜스폼에 걸린 constraint
(자식 constraint 노드)들로 자동 확장한다.

UI 비의존: 위젯에서 읽은 이름 리스트만 받는다. (app/core <-> app/ui 분리)
"""

import maya.cmds as cmds


def _to_uuid(node):
    """노드(짧은 이름/경로)를 UUID 로 변환. 실패 시 None."""
    uuids = cmds.ls(node, uuid=True) or []
    return uuids[0] if uuids else None


def _path(uuid):
    """UUID 로 현재 롱네임을 다시 찾는다. 없으면 None."""
    if not uuid:
        return None
    paths = cmds.ls(uuid, long=True) or []
    return paths[0] if paths else None


def _is_constraint(node):
    """node 가 constraint 노드인가(추상 타입 'constraint' 상속 여부)."""
    inherited = cmds.nodeType(node, inherited=True) or []
    return "constraint" in inherited


def _vec3(val):
    """cmds 쿼리 결과를 [x, y, z] 3-float 로 평탄화."""
    if val and isinstance(val[0], (list, tuple)):
        val = val[0]
    return [float(v) for v in val]


# ------------------------------------------------------------- 왼쪽 목록 해석

def _collect_constraint_uuids(names):
    """이름 리스트를 constraint UUID 리스트로 해석한다.

    - constraint 노드면 그대로.
    - 일반 트랜스폼이면 그 자식 constraint 노드들로 확장.
    반환: (constraint UUID 리스트, 경고 리스트)
    """
    uuids = []
    warnings = []
    for name in names:
        matches = cmds.ls(name, long=True) or []
        if not matches:
            warnings.append("Skipped (not found): {0}".format(name))
            continue
        if len(matches) > 1:
            warnings.append(
                "Ambiguous name '{0}' ({1} matches) - using first.".format(
                    name, len(matches)))
        node = matches[0]

        if _is_constraint(node):
            u = _to_uuid(node)
            if u:
                uuids.append(u)
            continue

        # 트랜스폼이면 걸린 constraint 로 확장.
        cons = cmds.listRelatives(
            node, children=True, type="constraint", fullPath=True) or []
        if not cons:
            warnings.append("Skipped (not a constraint / no constraint): {0}".format(name))
            continue
        for c in cons:
            u = _to_uuid(c)
            if u:
                uuids.append(u)
    return uuids, warnings


# --------------------------------------------------------- constraint 세팅 읽기

def _read_weights(cmd, cn, targets):
    """타깃 순서에 맞춘 weight 값 리스트(weightAliasList 순서 = targetList 순서)."""
    try:
        aliases = cmd(cn, q=True, weightAliasList=True) or []
    except Exception:
        aliases = []
    weights = []
    for alias in aliases:
        try:
            weights.append(cmds.getAttr("{0}.{1}".format(cn, alias)))
        except Exception:
            weights.append(1.0)
    return weights


def _read_aim(cmd, cn):
    """aimConstraint 전용 설정(aim/up/worldUp)을 읽는다."""
    extra = {}
    for flag in ("aimVector", "upVector", "worldUpVector"):
        try:
            extra[flag] = _vec3(cmd(cn, q=True, **{flag: True}))
        except Exception:
            pass
    try:
        extra["worldUpType"] = cmd(cn, q=True, worldUpType=True)
    except Exception:
        pass
    try:
        wuo = cmd(cn, q=True, worldUpObject=True)
        if wuo:
            wuo = wuo[0] if isinstance(wuo, (list, tuple)) else wuo
            extra["worldUpObject_uuid"] = _to_uuid(wuo)
    except Exception:
        pass
    return extra


def _read_constraint(con_uuid):
    """constraint 의 타입/타깃/weight/driven/부가설정을 읽어 스펙 dict 로 반환.

    타깃과 driven 은 UUID 로 잡는다. 해석 불가면 None.
    """
    cn = _path(con_uuid)
    if cn is None:
        return None
    ctype = cmds.nodeType(cn)
    cmd = getattr(cmds, ctype, None)
    if cmd is None:
        return None

    try:
        targets = cmd(cn, q=True, targetList=True) or []
    except Exception:
        targets = []
    target_uuids = [u for u in (_to_uuid(t) for t in targets) if u]

    parents = cmds.listRelatives(cn, parent=True, fullPath=True) or []
    driven_uuid = _to_uuid(parents[0]) if parents else None

    weights = _read_weights(cmd, cn, targets)

    extra = {}
    if ctype == "aimConstraint":
        extra = _read_aim(cmd, cn)
    if ctype in ("parentConstraint", "orientConstraint"):
        if cmds.attributeQuery("interpType", node=cn, exists=True):
            try:
                extra["interpType"] = cmds.getAttr("{0}.interpType".format(cn))
            except Exception:
                pass

    return {
        "type": ctype,
        "target_uuids": target_uuids,
        "weights": weights,
        "driven_uuid": driven_uuid,
        "extra": extra,
    }


# ------------------------------------------------------------ constraint 재생성

def _apply_weights(cmd, new_cn, weights):
    """새 constraint 에 원본 weight 값을 순서대로 적용."""
    if not weights:
        return
    try:
        aliases = cmd(new_cn, q=True, weightAliasList=True) or []
    except Exception:
        aliases = []
    for alias, w in zip(aliases, weights):
        try:
            cmds.setAttr("{0}.{1}".format(new_cn, alias), w)
        except Exception:
            pass


def _recreate(spec, new_driven_path):
    """spec 대로 new_driven_path 에 constraint 를 새로 만든다. 새 constraint 명 반환.

    maintainOffset=True 로 만들어 대상 오브젝트가 튀지 않게 한다(지원 안 하는 타입이면
    자동으로 MO 없이 재시도). 타깃 weight / aim 설정 / interpType 도 복원한다.
    """
    ctype = spec["type"]
    cmd = getattr(cmds, ctype)

    target_paths = [p for p in (_path(u) for u in spec["target_uuids"]) if p]
    if not target_paths:
        raise RuntimeError("no resolvable targets")

    args = target_paths + [new_driven_path]

    extra = spec["extra"]
    kw = {}
    if ctype == "aimConstraint":
        for flag in ("aimVector", "upVector", "worldUpVector"):
            if flag in extra:
                kw[flag] = extra[flag]
        if "worldUpType" in extra:
            kw["worldUpType"] = extra["worldUpType"]
        wuo_path = _path(extra.get("worldUpObject_uuid"))
        if wuo_path:
            kw["worldUpObject"] = wuo_path

    # maintainOffset 지원 여부가 타입마다 달라, 붙여서 시도하고 실패하면 없이 재시도.
    try:
        res = cmd(*args, maintainOffset=True, **kw)
    except (RuntimeError, TypeError):
        res = cmd(*args, **kw)

    new_cn = res[0] if isinstance(res, (list, tuple)) else res

    _apply_weights(cmd, new_cn, spec["weights"])

    if "interpType" in extra:
        try:
            cmds.setAttr("{0}.interpType".format(new_cn), extra["interpType"])
        except Exception:
            pass

    return new_cn


# ------------------------------------------------------------------- 공개 API

def transfer_constraints(constraint_names, object_names):
    """constraint 를 오른쪽 오브젝트로 옮긴다(원본 삭제 + 동일 세팅 재생성).

    Args:
        constraint_names: 왼쪽 목록. constraint 노드 또는 걸린 트랜스폼.
        object_names: 오른쪽 목록. 새로 constraint 를 받을(driven) 오브젝트.

    Returns:
        (생성된 constraint 명 리스트, 경고 메시지 리스트)
    """
    if not constraint_names:
        raise ValueError("No constraints. Add constraints to the left list.")
    if not object_names:
        raise ValueError("No target objects. Add objects to the right list.")

    con_uuids, warnings = _collect_constraint_uuids(constraint_names)
    if not con_uuids:
        raise ValueError("No valid constraints found in the left list.")

    obj_uuids = []
    for name in object_names:
        matches = cmds.ls(name, uuid=True) or []
        if not matches:
            warnings.append("Skipped target (not found): {0}".format(name))
            continue
        if len(matches) > 1:
            warnings.append(
                "Ambiguous target '{0}' ({1} matches) - using first.".format(
                    name, len(matches)))
        obj_uuids.append(matches[0])
    if not obj_uuids:
        raise ValueError("No valid target objects found in the right list.")

    # 매핑: (con_uuid, [대상 obj_uuid, ...]) 페어 구성.
    pairs = []
    if len(obj_uuids) == 1:
        # 모든 constraint 를 오브젝트 하나로.
        for cu in con_uuids:
            pairs.append((cu, [obj_uuids[0]]))
    elif len(con_uuids) == len(obj_uuids):
        for cu, ou in zip(con_uuids, obj_uuids):
            pairs.append((cu, [ou]))
    else:
        n = min(len(con_uuids), len(obj_uuids))
        warnings.append(
            "Count mismatch (constraints {0} vs objects {1}) - transferring "
            "{2} pair(s).".format(len(con_uuids), len(obj_uuids), n))
        for cu, ou in zip(con_uuids[:n], obj_uuids[:n]):
            pairs.append((cu, [ou]))

    created_uuids = []

    for con_uuid, target_obj_uuids in pairs:
        spec = _read_constraint(con_uuid)
        if spec is None:
            warnings.append("Skipped (unreadable constraint): {0}".format(con_uuid))
            continue

        driven_uuid = spec["driven_uuid"]
        driven_path = _path(driven_uuid)
        # 삭제 후 복원할 원본 driven 의 월드 트랜스폼(대상 목록에 자기 자신이 없을 때만).
        old_matrix = None
        if driven_path and driven_uuid not in target_obj_uuids:
            try:
                old_matrix = cmds.xform(
                    driven_path, q=True, ws=True, matrix=True)
            except Exception:
                old_matrix = None

        # 1) 새 constraint 를 먼저 만든다(원본이 살아 있는 동안 -> 타깃/오프셋 안정).
        for obj_uuid in target_obj_uuids:
            new_driven = _path(obj_uuid)
            if new_driven is None:
                warnings.append("Skipped target (no longer in scene): {0}".format(obj_uuid))
                continue
            try:
                new_cn = _recreate(spec, new_driven)
                # 이름은 이후 원본 삭제/재부모로 흔들릴 수 있으니 곧바로 UUID 로 잡는다.
                created_uuids.append(_to_uuid(new_cn))
            except Exception as e:
                warnings.append("Failed to apply on '{0}': {1}".format(new_driven, e))

        # 2) 원본 constraint 삭제.
        cn = _path(con_uuid)
        if cn is not None:
            try:
                cmds.delete(cn)
            except Exception as e:
                warnings.append("Failed to delete original: {0}".format(e))

        # 3) 원본 driven 을 원래 월드 트랜스폼으로 복원(튐 방지).
        if old_matrix is not None:
            dp = _path(driven_uuid)
            if dp is not None:
                try:
                    cmds.xform(dp, ws=True, matrix=old_matrix)
                except Exception:
                    pass

    created = [p for p in (_path(u) for u in created_uuids) if p]
    if created:
        try:
            cmds.select(created)
        except Exception:
            pass

    return created, warnings
