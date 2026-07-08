# -*- coding: utf-8 -*-
# A00360_SortTool core - 선택 오브젝트 정렬 로직 (maya.cmds, UI 비의존)
#
# 월드 X/Y/Z 위치 · 이름 · 타입 기준으로 오브젝트를 정렬하고, 아웃라이너의 형제
# 순서(위->아래)를 그 순서로 바꾼다.
#
# 아웃라이너 재정렬은 AriSortOutliner.mel 의 '슬롯 스왑' 방식을 이식했다: 선택
# 오브젝트가 '원래 차지하던 슬롯'들을 정렬 순서로 다시 채운다. Maya 의 reorder 는
# 같은 부모의 형제끼리만 순서를 바꿀 수 있으므로, 대상을 부모별로 그룹지어 처리한다.

import maya.cmds as cmds


# 정렬 기준 모드
MODE_X = "x"
MODE_Y = "y"
MODE_Z = "z"
MODE_NAME = "name"
MODE_TYPE = "type"

_AXIS_INDEX = {MODE_X: 0, MODE_Y: 1, MODE_Z: 2}


# --------------------------------------------------------------- 정렬 키

def _short(full):
    return full.split("|")[-1]


def _type_name(full):
    """타입 키: shape 가 있으면 shape 의 nodeType, 없으면 자신의 nodeType."""
    shapes = cmds.listRelatives(full, shapes=True, fullPath=True) or []
    return cmds.nodeType(shapes[0]) if shapes else cmds.nodeType(full)


def _world_pos(full):
    """오브젝트의 월드 위치 [x, y, z]. 위치를 알 수 없는 노드면 None.

    조인트·메시·커브·로케이터·클러스터/래티스 핸들 등 위치를 가진 DAG 노드는 모두
    xform 으로 월드 위치를 얻는다. 위치 개념이 없는 순수 DG 노드(blendShape 등)는 None.
    """
    try:
        return cmds.xform(full, q=True, ws=True, translation=True)
    except Exception:
        return None


def _compute_key(full, mode):
    """정렬 키. 위치=float, 이름=소문자 str, 타입=(타입, 이름) 튜플.

    위치 모드에서 위치를 못 구하는 노드는 None 을 돌려주어 정렬에서 제외(스킵)한다.
    이름/타입 모드는 어떤 노드든 이름/타입이 있으므로 항상 키가 나온다.
    """
    if mode in _AXIS_INDEX:
        pos = _world_pos(full)
        return None if pos is None else pos[_AXIS_INDEX[mode]]
    if mode == MODE_TYPE:
        return (_type_name(full).lower(), _short(full).lower())
    # MODE_NAME
    return _short(full).lower()


# ------------------------------------------------ 아웃라이너 재정렬 (Ari 이식)

def _siblings(full):
    """full 의 형제 목록(fullPath). 최상위면 assemblies(top-level transform)."""
    parent = cmds.listRelatives(full, parent=True, fullPath=True)
    if parent:
        return cmds.listRelatives(parent[0], children=True, fullPath=True) or []
    return cmds.ls(assemblies=True, long=True) or []


def _list_num(full):
    """형제 중 full 의 인덱스(= 아웃라이너 순서). 없으면 -1."""
    for i, sib in enumerate(_siblings(full)):
        if sib == full:
            return i
    return -1


def _obj_at(parent_full, num):
    """parent_full 의 자식(또는 최상위) 중 num 번째 오브젝트. 범위 밖이면 None."""
    if parent_full:
        children = cmds.listRelatives(parent_full, children=True, fullPath=True) or []
    else:
        children = cmds.ls(assemblies=True, long=True) or []
    if 0 <= num < len(children):
        return children[num]
    return None


def _num_sort(full, num):
    """full 을 형제 슬롯 num 으로 이동(그 자리 오브젝트와 스왑). Ari NumSort 이식.

    reorder 는 형제 순서만 바꾸고 이름/DAG 경로는 그대로라, 스왑 뒤에도 full 경로는 유효하다.
    """
    parent = cmds.listRelatives(full, parent=True, fullPath=True)
    parent_full = parent[0] if parent else ""
    this_obj = _obj_at(parent_full, num)
    move = num - _list_num(full)
    if move == 0:
        return
    try:
        cmds.reorder(full, relative=move)
        if this_obj and this_obj != full:
            cmds.reorder(this_obj, relative=(move * (-1) - 1))
    except RuntimeError:
        pass


def _reorder_outliner(ordered_fulls):
    """정렬된 fullPath 순서대로 아웃라이너 형제 순서를 바꾼다(부모별 그룹 처리).

    아웃라이너/reorder 는 DAG 노드에만 의미가 있으므로, 위치 정렬에 낀 순수 DG 노드는
    (있다면) 재정렬에서 제외한다. 전역 정렬 순서는 유지된다.
    """
    dag_fulls = [f for f in ordered_fulls if cmds.ls(f, dag=True, long=True)]
    groups = {}
    order = []
    for full in dag_fulls:
        parent = cmds.listRelatives(full, parent=True, fullPath=True)
        key = parent[0] if parent else ""
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(full)

    for key in order:
        objs = groups[key]                        # 이미 전역 정렬 순서(부모 그룹 부분집합)
        slots = sorted(_list_num(o) for o in objs)  # 대상 오브젝트가 차지하던 슬롯들
        for obj, slot in zip(objs, slots):
            _num_sort(obj, slot)


# ------------------------------------------------------------------- 공개 API

def sort_objects(items, mode, reverse=False, reorder_outliner=True):
    """items(표시 이름) 를 mode 기준으로 정렬한다.

    mode  : MODE_X/Y/Z(월드 위치) · MODE_NAME · MODE_TYPE
    반환   : (ordered_texts, missing_texts)
      ordered_texts : 정렬된(해석 성공) 표시 이름 리스트 — TSL 재구성용(위->아래)
      missing_texts : 씬에서 못 찾은(삭제/이름변경/중복 모호) 표시 이름 리스트
    reorder_outliner=True 면 아웃라이너 형제 순서도 같은 순서로 바꾼다.
    """
    keyed = []      # (text, full, key)
    missing = []
    for text in items:
        found = cmds.ls(text, long=True) or []
        if len(found) != 1:
            missing.append(text)     # 0개(없음) 또는 2개+(이름 모호) -> 건너뜀
            continue
        full = found[0]
        key = _compute_key(full, mode)
        if key is None:
            missing.append(text)     # 위치를 알 수 없는 노드(위치 정렬 대상 아님)
            continue
        keyed.append((text, full, key))

    keyed.sort(key=lambda t: t[2])
    if reverse:
        keyed.reverse()

    ordered_texts = [t for t, _f, _k in keyed]
    ordered_fulls = [f for _t, f, _k in keyed]

    if reorder_outliner and ordered_fulls:
        _reorder_outliner(ordered_fulls)

    if ordered_fulls:
        try:
            cmds.select(ordered_fulls)
        except Exception:
            pass

    return ordered_texts, missing
