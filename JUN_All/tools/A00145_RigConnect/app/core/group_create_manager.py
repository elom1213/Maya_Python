# -*- coding: utf-8 -*-
"""
group_create_manager - Constrain 탭 'Group Create' 로직.

리스트업된 각 오브젝트에 대해, 그 오브젝트와 '위치·회전이 동일한' 빈 그룹을
오브젝트의 (원래) 부모와 오브젝트 사이 계층에 삽입한다.

  before:  parent -> obj
  after :  parent -> obj_con_01 -> obj            (count=1)
           parent -> obj_con_02 -> obj_con_01 -> obj   (count=2)

- 각 그룹은 오브젝트와 같은 월드 위치/회전을 갖는다(스케일은 1 유지).
- 오브젝트의 월드 트랜스폼과 기존 계층(부모)은 그대로 유지된다.
- 그룹 이름은 오브젝트 짧은 이름 + '_con_01'(중첩이면 _con_02, ...). 가장 안쪽
  (오브젝트 바로 위) 그룹이 _con_01 이다.
- count 로 오브젝트당 만들 그룹 수를 정한다.

UUID 기반: 씬에 같은 이름의 오브젝트가 여럿이면 짧은 이름/경로는 모호하고, 재부모
(reparent)를 하면 DAG 경로가 계속 바뀐다. 그래서 대상 오브젝트·부모·생성한 그룹을
모두 UUID 로 잡아두고, 필요할 때마다 UUID -> 현재 경로로 해석해 조작한다.

UI 비의존: 위젯에서 읽은 list/int 값만 받는다. (app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds


SUFFIX = "con"


def _short(name):
    """DAG 경로/네임스페이스를 제거한 짧은 노드 이름. 'a|b:c' -> 'c'."""
    return name.split("|")[-1].split(":")[-1]


def _to_uuid(node):
    """노드(짧은 이름/경로)를 UUID 로 변환. 실패 시 None."""
    uuids = cmds.ls(node, uuid=True) or []
    return uuids[0] if uuids else None


def _path(uuid):
    """UUID 로 현재 DAG 롱네임을 다시 찾는다. 없으면 None.
    (부모를 재부모하면 자식 경로가 바뀌므로, 잡아둔 경로 대신 매번 해석한다.)"""
    if not uuid:
        return None
    paths = cmds.ls(uuid, long=True) or []
    return paths[0] if paths else None


def create_groups(objects, count=1):
    """objects 각각에 count 개의 중첩 오프셋 그룹을 삽입한다.

    Args:
        objects: 대상 오브젝트 이름 리스트.
        count: 오브젝트당 만들 그룹 수(중첩). 1 이상.

    Returns:
        (생성된 그룹명 리스트, 경고 메시지 리스트)
    """
    if not objects:
        raise ValueError("No objects. Add objects to the list first.")
    if count < 1:
        raise ValueError("Group count must be >= 1.")

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

        # 원래 부모도 UUID 로(월드면 None).
        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
        parent_uuid = _to_uuid(parents[0]) if parents else None

        try:
            # prev_uuid : 다음 그룹이 감쌀 노드(처음엔 오브젝트, 이후엔 직전 그룹).
            #             모든 그룹이 오브젝트와 같은 월드에 놓이므로 prev 기준으로 맞춘다.
            prev_uuid = obj_uuid
            for i in range(1, count + 1):
                grp_name = "{0}_{1}_{2:02d}".format(base, SUFFIX, i)

                # 빈 그룹 생성(월드). 이름 충돌 시 Maya 가 유니크화 -> UUID 로 잡는다.
                grp = cmds.group(empty=True, world=True, name=grp_name)
                grp_uuid = _to_uuid(grp)

                # prev(오브젝트/직전 그룹)와 같은 월드 위치·회전(스케일 제외).
                cmds.matchTransform(
                    _path(grp_uuid), _path(prev_uuid),
                    position=True, rotation=True, scale=False)

                # 그룹을 원래 부모 아래로(월드 트랜스폼 보존). 부모가 월드면 그대로 둔다.
                if parent_uuid is not None:
                    parent_path = _path(parent_uuid)
                    if parent_path is not None:
                        cmds.parent(_path(grp_uuid), parent_path)

                # 감쌀 노드(prev)를 그룹 아래로(월드 보존).
                cmds.parent(_path(prev_uuid), _path(grp_uuid))

                created_uuids.append(grp_uuid)
                prev_uuid = grp_uuid   # 다음 그룹은 이 그룹을 감싼다(더 바깥).

        except RuntimeError as e:
            warnings.append("Failed on '{0}': {1}".format(base, e))
            continue

    # 생성한 그룹의 현재 경로로 해석(재부모로 경로가 바뀌었을 수 있음).
    created = [p for p in (_path(u) for u in created_uuids) if p]
    return created, warnings
