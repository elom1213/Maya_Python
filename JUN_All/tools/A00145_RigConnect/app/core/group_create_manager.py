# -*- coding: utf-8 -*-
"""
group_create_manager - Constrain 탭 'Group Create' 로직.

리스트업된 각 오브젝트에 대해, 그 오브젝트와 '위치·회전이 동일한' 오프셋 노드를
오브젝트의 계층에 삽입한다(zero-out 용). 부모 쪽/자식 쪽 양방향을 지원한다.

  Parent 쪽 (기본):  부모와 오브젝트 사이에 삽입 (오브젝트가 아래로 밀린다)
    before:  parent -> obj
    after :  parent -> obj_zro_01 -> obj                 (count=1)
             parent -> obj_zro_02 -> obj_zro_01 -> obj   (count=2)

  Child 쪽:  오브젝트와 그 자식들 사이에 삽입 (자식들이 아래로 밀린다)
    before:  obj -> child
    after :  obj -> obj_zro_01 -> child                  (count=1)
             obj -> obj_zro_01 -> obj_zro_02 -> child    (count=2)
    (자식이 없으면 오프셋 노드 체인만 오브젝트 아래에 매달린다.)

- 각 노드는 오브젝트와 같은 월드 위치/회전을 갖는다(스케일은 1 유지).
- 오브젝트/자식의 월드 트랜스폼과 기존 계층은 그대로 유지된다(노드가 사이에만 삽입).
- 노드 이름 = 오브젝트 짧은 이름 + '_' + suffix + '_' + 패딩번호. 예) obj_zro_01.
  Parent 쪽은 _01 이 오브젝트 바로 위, Child 쪽은 _01 이 오브젝트 바로 아래.
- count 로 방향당 만들 (중첩) 노드 수를 정한다.
- suffix / padding(자릿수) / 노드 타입(그룹 또는 오브젝트와 동일 타입)은 호출부가 정한다.

노드 타입:
- match_type=False (기본): 빈 그룹(transform)을 만든다.
- match_type=True: 오브젝트와 '같은 타입'으로 만든다.
    - joint 처럼 shape 이 없는 타입: 같은 nodeType 으로 createNode (joint -> joint).
    - curve/mesh/nurbsSurface/locator 처럼 shape 이 있는 타입: 오브젝트를 복제해 하위
      자식만 지우고 자신의 shape 만 남긴다(curve -> curve, mesh -> mesh). 순수 transform
      (그룹)은 빈 그룹.

UUID 기반: 씬에 같은 이름의 오브젝트가 여럿이면 짧은 이름/경로는 모호하고, 재부모
(reparent)를 하면 DAG 경로가 계속 바뀐다. 그래서 대상 오브젝트·부모·자식·생성한 노드를
모두 UUID 로 잡아두고, 필요할 때마다 UUID -> 현재 경로로 해석해 조작한다.

UI 비의존: 위젯에서 읽은 list/int/str/bool 값만 받는다. (app/core <-> app/ui 분리)
"""

import maya.cmds as cmds


SUFFIX = "zro"


def _short(name):
    """DAG 경로/네임스페이스를 제거한 짧은 노드 이름. 'a|b:c' -> 'c'."""
    return name.split("|")[-1].split(":")[-1]


def _to_uuid(node):
    """노드(짧은 이름/경로)를 UUID 로 변환. 실패 시 None."""
    uuids = cmds.ls(node, uuid=True) or []
    return uuids[0] if uuids else None


def _path(uuid):
    """UUID 로 현재 DAG 롱네임을 다시 찾는다. 없으면 None.
    (부모/자식을 재부모하면 경로가 바뀌므로, 잡아둔 경로 대신 매번 해석한다.)"""
    if not uuid:
        return None
    paths = cmds.ls(uuid, long=True) or []
    return paths[0] if paths else None


def _make_offset_node(source_node, match_type, name):
    """월드에 오프셋 노드를 하나 만들어 그 이름을 반환한다.

    match_type=False: 빈 그룹(transform).
    match_type=True : source 오브젝트와 '같은 타입'으로 만든다.
      - shape 이 있는 타입(curve/mesh/nurbsSurface/locator ...): source 를 복제해
        그 자식(하위 트랜스폼)만 지우고 자신의 shape 만 남긴다 -> 커브면 커브가,
        메시면 메시가 만들어진다. 월드로 빼고 스케일은 1 로 초기화(그룹 경로와 동일).
      - shape 이 없는 타입(joint/ikHandle ...): 같은 nodeType 으로 createNode.
        (joint 등이 현재 선택에 자동 부착되지 않도록 select clear 후 생성.)
      - 순수 transform(그룹): 빈 그룹.
    """
    if not match_type:
        return cmds.group(empty=True, world=True, name=name)

    obj_type = cmds.nodeType(source_node)
    shapes = cmds.listRelatives(source_node, shapes=True, fullPath=True) or []

    if shapes:
        # source 를 복제(하위 자식 포함) -> 복제본의 하위 트랜스폼만 삭제 -> shape 만 남김.
        dup = cmds.duplicate(
            source_node, name=name, returnRootsOnly=True, renameChildren=True)[0]
        dup_kids = cmds.listRelatives(
            dup, children=True, type="transform", fullPath=True) or []
        if dup_kids:
            cmds.delete(dup_kids)
        # 복제본은 source 와 같은 부모 아래 생긴다 -> 그룹 경로처럼 월드로 뺀다.
        if cmds.listRelatives(dup, parent=True):
            dup = cmds.parent(dup, world=True)[0]
        # 스케일은 1 로(그룹 경로와 동일하게; 위치/회전만 이후 matchTransform 로 맞춘다).
        for attr in ("scaleX", "scaleY", "scaleZ"):
            try:
                cmds.setAttr("{0}.{1}".format(dup, attr), 1)
            except Exception:
                pass
        return dup

    # shape 없는 DAG 타입.
    if obj_type == "transform":
        return cmds.group(empty=True, world=True, name=name)
    cmds.select(clear=True)
    try:
        return cmds.createNode(obj_type, name=name)
    except Exception:
        return cmds.group(empty=True, world=True, name=name)


def _node_name(base, suffix, index, padding):
    """오프셋 노드 이름 = '<base>_<suffix>_<번호(패딩)>'. 예) obj_zro_01."""
    return "{0}_{1}_{2:0{3}d}".format(base, suffix, index, padding)


def _create_parent_chain(obj_uuid, base, count, suffix, match_type, padding):
    """부모와 오브젝트 사이에 count 개의 중첩 오프셋 노드를 삽입한다.

    _01 이 오브젝트 바로 위, 번호가 커질수록 더 바깥(위쪽)이다. 노드 타입은 항상
    원본 오브젝트를 기준으로 정한다(match_type 이면 모든 노드가 오브젝트와 같은 타입).
    반환: 생성한 노드 UUID 리스트.
    """
    node = _path(obj_uuid)

    # 원래 부모도 UUID 로(월드면 None).
    parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
    parent_uuid = _to_uuid(parents[0]) if parents else None

    created = []
    # prev_uuid : 다음 노드가 감쌀 대상(처음엔 오브젝트, 이후엔 직전 노드).
    prev_uuid = obj_uuid
    for i in range(1, count + 1):
        node_obj = _make_offset_node(
            _path(obj_uuid), match_type, _node_name(base, suffix, i, padding))
        node_uuid = _to_uuid(node_obj)

        # prev(오브젝트/직전 노드)와 같은 월드 위치·회전(스케일 제외).
        cmds.matchTransform(
            _path(node_uuid), _path(prev_uuid),
            position=True, rotation=True, scale=False)

        # 원래 부모 아래로(월드 트랜스폼 보존). 부모가 월드면 그대로 둔다.
        if parent_uuid is not None:
            parent_path = _path(parent_uuid)
            if parent_path is not None:
                cmds.parent(_path(node_uuid), parent_path)

        # 감쌀 노드(prev)를 이 노드 아래로(월드 보존).
        cmds.parent(_path(prev_uuid), _path(node_uuid))

        created.append(node_uuid)
        prev_uuid = node_uuid   # 다음 노드는 이 노드를 감싼다(더 바깥).

    return created


def _create_child_chain(obj_uuid, base, count, suffix, match_type, padding):
    """오브젝트와 그 자식들 사이에 count 개의 중첩 오프셋 노드를 삽입한다.

    _01 이 오브젝트 바로 아래, 번호가 커질수록 더 깊다(아래쪽). 오브젝트의 기존
    (트랜스폼) 자식들은 가장 깊은 노드 아래로 옮겨진다(shape 는 오브젝트에 남는다).
    노드 타입은 항상 원본 오브젝트를 기준으로 정한다(match_type 이면 오브젝트와 같은 타입).
    반환: 생성한 노드 UUID 리스트.
    """
    obj_path = _path(obj_uuid)

    # 오브젝트의 기존 자식(트랜스폼/joint 만, shape 제외)을 UUID 로 잡아둔다.
    kids = cmds.listRelatives(
        obj_path, children=True, type="transform", fullPath=True) or []
    kid_uuids = [u for u in (_to_uuid(k) for k in kids) if u]

    created = []
    # prev_uuid : 새 노드를 붙일 부모(처음엔 오브젝트, 이후엔 직전 노드).
    prev_uuid = obj_uuid
    for i in range(1, count + 1):
        node_obj = _make_offset_node(
            _path(obj_uuid), match_type, _node_name(base, suffix, i, padding))
        node_uuid = _to_uuid(node_obj)

        # 모든 오프셋 노드는 오브젝트와 같은 월드 위치·회전(스케일 제외).
        cmds.matchTransform(
            _path(node_uuid), _path(obj_uuid),
            position=True, rotation=True, scale=False)

        # 직전 노드(또는 오브젝트) 아래로(월드 보존 -> 로컬은 zero).
        cmds.parent(_path(node_uuid), _path(prev_uuid))

        created.append(node_uuid)
        prev_uuid = node_uuid   # 다음 노드는 이 노드 아래로(더 깊게).

    # 기존 자식들을 가장 깊은 오프셋 노드 아래로(월드 보존).
    for kid_uuid in kid_uuids:
        kid_path = _path(kid_uuid)
        if kid_path is not None:
            cmds.parent(kid_path, _path(prev_uuid))

    return created


def create_offset_nodes(objects, count=1, suffix=SUFFIX, match_type=False,
                        create_parent=True, create_child=False, padding=2):
    """objects 각각에 오프셋(zero) 노드를 삽입한다(부모 쪽/자식 쪽 선택).

    Args:
        objects: 대상 오브젝트 이름 리스트.
        count: 방향당 만들 (중첩) 노드 수. 1 이상.
        suffix: 노드 이름 접미사(<obj>_<suffix>_01). 비우면 기본값 사용.
        match_type: True 면 오브젝트와 같은 노드 타입(예: joint), False 면 빈 그룹.
        create_parent: 부모 쪽(오브젝트 위) 삽입 여부.
        create_child: 자식 쪽(오브젝트 아래) 삽입 여부.
        padding: 번호 자릿수(2 -> 01, 02). 1 이상.

    Returns:
        (생성된 노드명 리스트, 경고 메시지 리스트)
    """
    if not objects:
        raise ValueError("No objects. Add objects to the list first.")
    if count < 1:
        raise ValueError("Count must be >= 1.")
    if padding < 1:
        raise ValueError("Padding must be >= 1.")
    if not (create_parent or create_child):
        raise ValueError("Enable Parent and/or Child side.")

    suffix = (suffix or "").strip() or SUFFIX

    warnings = []

    # 1. 입력 오브젝트를 UUID 로 잡아둔다(중복 이름/재부모에도 안정적인 핸들).
    obj_uuids = []
    for obj in objects:
        matches = cmds.ls(obj, uuid=True) or []
        if not matches:
            warnings.append("Skipped (not found): {0}".format(obj))
            continue
        if len(matches) > 1:
            warnings.append(
                "Ambiguous name '{0}' ({1} matches) - using first.".format(
                    obj, len(matches)))
        obj_uuids.append(matches[0])

    created_uuids = []

    for obj_uuid in obj_uuids:
        node = _path(obj_uuid)
        if node is None:
            warnings.append("Skipped (no longer in scene): {0}".format(obj_uuid))
            continue

        base = _short(node)

        try:
            if create_parent:
                created_uuids += _create_parent_chain(
                    obj_uuid, base, count, suffix, match_type, padding)
            if create_child:
                created_uuids += _create_child_chain(
                    obj_uuid, base, count, suffix, match_type, padding)
        except RuntimeError as e:
            warnings.append("Failed on '{0}': {1}".format(base, e))
            continue

    # 생성한 노드의 현재 경로로 해석(재부모로 경로가 바뀌었을 수 있음).
    created = [p for p in (_path(u) for u in created_uuids) if p]
    return created, warnings


# 구버전 호환: create_groups(objects, count) -> 그룹만, 부모 쪽. (외부 호출부 대비)
def create_groups(objects, count=1):
    """(deprecated) create_offset_nodes 로 위임하는 구버전 시그니처."""
    return create_offset_nodes(objects, count=count)
