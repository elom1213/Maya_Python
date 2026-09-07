# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-07
# A00290_BSTool - Target Order 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# blendShape 노드의 **타겟 나열 순서**(= weight 인덱스 순서)를 바꾼다.
#
# ## 마야에는 이 명령이 없다
#
# `blendShape` 커맨드에는 타겟을 재정렬하는 플래그가 없고, Shape Editor 의 드래그도
# 그룹(디렉터리) 안에서의 표시 순서를 옮길 뿐이다. 그래서 채널박스 · `aliasAttr` ·
# `blendShape -q -target` 이 보여 주는 **진짜 순서인 weight 인덱스**는 한 번 만들어지면
# 그대로 굳는다. 이 모듈은 그 인덱스를 직접 갈아 끼운다.
#
# ## 타겟 하나가 흩어져 있는 곳
#
# "타겟 3번" 은 한 군데 있는 게 아니라 인덱스 3 을 키로 여러 어트리뷰트에 흩어져 있다.
# 순서를 바꾼다는 건 **이 전부를 함께 옮긴다**는 뜻이다. 하나라도 빠뜨리면 이름과 모양이
# 어긋난다(가장 흔한 사고: 별칭만 옮겨서 A 라는 이름이 B 의 델타를 가리키게 되는 것).
#
#   weight[i]                                  값 · 들어오는/나가는 연결 · lock
#   <별칭> -> weight[i]                        aliasAttr 매핑 (타겟 이름)
#   inputTarget[b].inputTargetGroup[i]         델타 본체 (베이스 지오메트리 b 마다 하나씩!)
#     .inputTargetItem[k]                      k = 5000+w*1000 (인비트윈 포함)
#        .inputGeomTarget                        라이브 타겟 메시 연결
#        .inputPointsTarget / .inputComponentsTarget            구운 델타
#        .inputRelativePointsTarget / .inputRelativeComponentsTarget
#     .targetWeights[v]                        타겟별 페인트 웨이트
#     .normalizationId / .postDeformersMode / .targetMatrix / .targetBindMatrix
#   parentDirectory[i]                         Shape Editor 그룹 소속
#   targetVisibility[i] / targetParentVisibility[i] / nextTarget[i]
#   inbetweenInfoGroup[i].inbetweenInfo[k]     인비트윈 이름/타입
#   targetDirectory[d].childIndices            그룹이 담은 타겟 인덱스 목록(표시 순서)
#
# **`inputTarget` 는 베이스 지오메트리마다 하나**다. 한 blendShape 가 메시 여러 개를
# 디폼하면 같은 타겟 인덱스의 델타가 `inputTarget[0]`, `inputTarget[1]` … 에 따로 있다.
# `inputTarget[0]` 만 옮기면 두 번째 메시부터 이름과 모양이 어긋난다.
#
# ## 인덱스 슬롯은 새로 만들지 않는다
#
# 인덱스가 듬성한 blendShape 는 흔하다(타겟을 지우면 그 번호가 빈다 — 예: 0,1,4,7).
# 이 모듈은 **있던 슬롯 집합을 그대로 두고** 그 안에서 타겟만 자리를 바꾼다. 0..n-1 로
# 다시 촘촘하게 매기면 순서와 무관한 인덱스까지 전부 움직여, `weight[4]` 를 이름 대신
# 번호로 참조하던 바깥 노드/스크립트가 조용히 다른 타겟을 가리키게 된다.
#
# ## 편집(sculpt) 중에는 거절한다
#
# `sculptTargetIndex` 가 가리키는 타겟은 디포머가 버텍스 편집을 가로채는 **살아 있는
# 상태**이고, 확정되지 않은 편집이 `sculptTargetTweaks` 에 떠 있다. 그 상태로 인덱스를
# 갈아 끼우면 편집분이 엉뚱한 타겟에 확정된다. 그래서 편집 중이면 아무것도 하지 않고
# 어느 타겟을 끄면 되는지 알린다.

import maya.cmds as cmds

from . import blendshape_utils as bsu


# 노드 레벨에 있는 **타겟 인덱스로 색인되는** 단순 multi 들. 타겟과 함께 옮겨야 한다.
# (inbetweenInfoGroup 은 자식이 또 multi 라 따로 다룬다)
PER_TARGET_MULTIS = ("parentDirectory", "targetVisibility",
                     "targetParentVisibility", "nextTarget")

# inputTargetGroup 의 단순 자식들 (multi 가 아닌 것).
ITG_SIMPLE = ("normalizationId", "postDeformersMode")

# inputTargetGroup 의 행렬 자식들 (안 쓰는 blendShape 는 None 이 온다).
ITG_MATRIX = ("targetBindMatrix", "targetMatrix")

IDENTITY_MATRIX = (1.0, 0.0, 0.0, 0.0,
                   0.0, 1.0, 0.0, 0.0,
                   0.0, 0.0, 1.0, 0.0,
                   0.0, 0.0, 0.0, 1.0)

# inputTargetItem 의 자식들. inputGeomTarget 은 연결이라 따로 다룬다.
ITI_ARRAYS = (("inputPointsTarget", "pointArray"),
              ("inputComponentsTarget", "componentList"),
              ("inputRelativePointsTarget", "pointArray"),
              ("inputRelativeComponentsTarget", "componentList"))


# =========================
# 조회
# =========================

def list_targets(bs_node):
    """[(weight 인덱스, 타겟 이름), ...] 를 인덱스 오름차순으로 반환.

    UI 가 리스트에 채울 순서가 곧 이 순서다 — 마야가 타겟을 "나열" 하는 순서
    (채널박스 / `blendShape -q -target`)와 같다.
    """
    if not bsu.is_blendshape(bs_node):
        return []
    index_map = bsu.target_index_map(bs_node)
    return sorted(((idx, name) for name, idx in index_map.items()),
                  key=lambda pair: pair[0])


def target_names(bs_node):
    """타겟 이름만 인덱스 순으로."""
    return [name for _idx, name in list_targets(bs_node)]


def base_indices(bs_node):
    """이 blendShape 가 디폼하는 지오메트리(inputTarget) 인덱스 목록."""
    return cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or []


def editing_target(bs_node):
    """sculpt(Edit) 모드인 타겟의 weight 인덱스. 편집 중이 아니면 -1.

    ShapeEditorManager 와 같은 판정이지만, 코어 모듈끼리 서로를 import 하지 않도록
    (순환 참조) 여기서도 어트리뷰트를 직접 읽는다.
    """
    for base in base_indices(bs_node):
        plug = "{0}.inputTarget[{1}].sculptTargetIndex".format(bs_node, base)
        if not cmds.objExists(plug):
            continue
        value = cmds.getAttr(plug)
        if value is not None and value != -1:
            return int(value)
    return -1


# =========================
# 저수준 헬퍼
# =========================

def _itg_plug(bs_node, base, index):
    return "{0}.inputTarget[{1}].inputTargetGroup[{2}]".format(bs_node, base, index)


def _get(plug, default=None):
    """존재하지 않거나 읽을 수 없는 plug 는 default 로. (듬성한 multi 가 흔하다)"""
    try:
        if not cmds.objExists(plug):
            return default
        value = cmds.getAttr(plug)
        return default if value is None else value
    except Exception:
        return default


def _multi_indices(plug):
    try:
        return cmds.getAttr(plug, multiIndices=True) or []
    except Exception:
        return []


def _inputs(plug):
    """plug 로 **들어오는** 소스 plug 하나 (없으면 None)."""
    try:
        found = cmds.listConnections(plug, plugs=True, source=True,
                                     destination=False) or []
    except Exception:
        return None
    return found[0] if found else None


def _outputs(plug):
    """plug 에서 **나가는** 목적지 plug 목록."""
    try:
        return cmds.listConnections(plug, plugs=True, source=False,
                                    destination=True) or []
    except Exception:
        return []


def _disconnect(src, dst):
    try:
        cmds.disconnectAttr(src, dst)
    except Exception:
        pass


def _set_array(plug, values, attr_type):
    """배열 어트리뷰트 쓰기. **타입마다 인자 모양이 다르다** (실측으로 확인).

        pointArray    : setAttr(plug, 개수, (x,y,z,w), (x,y,z,w), ...)
                        4개짜리 **튜플 그대로** 넘긴다. 풀어서 float 로 넘기면
                        "Error reading data element number 2" 로 죽는다.
        componentList : setAttr(plug, 개수, "vtx[0]", "vtx[3:5]", ...)
        Int32Array    : setAttr(plug, [0, -1, 3])
                        **개수를 붙이면 안 된다.** 붙이면 마야가 개수를 첫 값으로
                        읽고 나머지를 버린다 — `[0,-1,3]` 을 개수와 함께 주면
                        "Too much data was provided" 로 죽고, 값이 하나뿐이면
                        에러 없이 **개수가 값으로 저장된다**(조용한 오작동).
    """
    if values is None:
        return
    if attr_type == "Int32Array":
        cmds.setAttr(plug, list(values), type="Int32Array")
    else:
        cmds.setAttr(plug, len(values), *values, type=attr_type)


# =========================
# 스냅샷 / 되쓰기
# =========================

def _snapshot_item(bs_node, base, index, item):
    """inputTargetItem[item] 하나의 내용."""
    plug = "{0}.inputTargetItem[{1}]".format(_itg_plug(bs_node, base, index), item)
    data = {"geom_input": _inputs(plug + ".inputGeomTarget")}
    for name, _type in ITI_ARRAYS:
        data[name] = _get("{0}.{1}".format(plug, name))
    return data


def _snapshot_group(bs_node, base, index):
    """한 베이스 지오메트리에서의 inputTargetGroup[index] 내용 전체."""
    plug = _itg_plug(bs_node, base, index)
    items = {}
    for item in _multi_indices(plug + ".inputTargetItem"):
        items[item] = _snapshot_item(bs_node, base, index, item)

    weights = {}
    for vtx in _multi_indices(plug + ".targetWeights"):
        value = _get("{0}.targetWeights[{1}]".format(plug, vtx))
        if value is not None:
            weights[vtx] = value

    data = {"items": items, "target_weights": weights}
    for name in ITG_SIMPLE:
        data[name] = _get("{0}.{1}".format(plug, name))
    for name in ITG_MATRIX:
        data[name] = _get("{0}.{1}".format(plug, name))
    return data


def _snapshot_target(bs_node, index, name, bases):
    """타겟 하나를 이루는 모든 것을 딕셔너리로."""
    weight = "{0}.weight[{1}]".format(bs_node, index)

    inbetween = {}
    iig = "{0}.inbetweenInfoGroup[{1}].inbetweenInfo".format(bs_node, index)
    for item in _multi_indices(iig):
        inbetween[item] = {
            "inbetweenTargetType": _get("{0}[{1}].inbetweenTargetType".format(iig, item)),
            "inbetweenTargetName": _get("{0}[{1}].inbetweenTargetName".format(iig, item)),
        }

    data = {
        "index": index,
        "name": name,
        "value": _get(weight, 0.0),
        "locked": bool(cmds.getAttr(weight, lock=True)),
        "keyable": bool(cmds.getAttr(weight, keyable=True)),
        "weight_input": _inputs(weight),
        "weight_outputs": _outputs(weight),
        "groups": {base: _snapshot_group(bs_node, base, index) for base in bases},
        "inbetween": inbetween,
    }
    for attr in PER_TARGET_MULTIS:
        data[attr] = _get("{0}.{1}[{2}]".format(bs_node, attr, index))
    return data


def _remove_element(plug):
    """multi **요소 하나**를 지운다. 실패는 조용히 넘긴다.

    반드시 **잎(leaf) 요소**에만 쓴다 — `inputTargetItem[6000]`, `targetWeights[4]`,
    `parentDirectory[2]` 같은 것들. `inputTargetGroup[i]` 처럼 **자식이 또 multi 인
    요소를 통째로 지우면 undo 로 되살아나지 않는다**(실측: 지운 뒤 Ctrl+Z 를 해도
    inputPointsTarget 이 빈 채로 남는다 — 델타가 영영 사라진다). 그래서 이 모듈은
    그룹을 통째로 지우지 않고, **슬롯 위에 덮어쓰고 남는 잎만** 지운다.
    """
    try:
        cmds.removeMultiInstance(plug, b=True)
    except Exception:
        pass


def _detach_target(bs_node, data, bases):
    """스냅샷을 뜬 타겟의 **연결과 별칭만** 떼어 낸다 (데이터는 그대로 둔다).

    데이터를 지우지 않는 이유는 `_remove_element` 주석 참고 — 지운 그룹은 undo 로
    돌아오지 않는다. 대신 되쓰기 단계에서 슬롯을 통째로 덮어쓴다.
    """
    index = data["index"]
    weight = "{0}.weight[{1}]".format(bs_node, index)

    if data["locked"]:
        cmds.setAttr(weight, lock=False)
    if data["weight_input"]:
        _disconnect(data["weight_input"], weight)
    for dst in data["weight_outputs"]:
        _disconnect(weight, dst)

    # 별칭은 **전부 떼고 나서** 다시 붙인다. 이름이 다른 인덱스에 걸린 채로
    # 같은 이름을 또 붙이면 마야가 거절하거나 앞의 것을 조용히 버린다.
    if data["name"] in (cmds.aliasAttr(bs_node, query=True) or []):
        try:
            cmds.aliasAttr("{0}.{1}".format(bs_node, data["name"]), remove=True)
        except Exception:
            pass

    for base in bases:
        plug = _itg_plug(bs_node, base, index)
        for item, item_data in data["groups"][base]["items"].items():
            if item_data["geom_input"]:
                _disconnect(item_data["geom_input"],
                            "{0}.inputTargetItem[{1}].inputGeomTarget".format(plug, item))


def _write_target(bs_node, data, index, bases, previous):
    """스냅샷 `data` 를 슬롯 `index` 에 되쓴다.

    `previous` 는 그 슬롯에 **원래 있던** 타겟의 스냅샷이다. 슬롯을 비우지 않고
    덮어쓰므로, 새 주인이 안 쓰는 잎 요소(예: 없어진 인비트윈, 페인트 웨이트)는
    여기서 하나씩 지워야 한다. 안 그러면 남의 인비트윈이 그대로 붙어 있다.
    """
    weight = "{0}.weight[{1}]".format(bs_node, index)

    cmds.setAttr(weight, data["value"])
    cmds.aliasAttr(data["name"], weight)
    cmds.setAttr(weight, keyable=data["keyable"])

    for base in bases:
        group = data["groups"][base]
        old_group = previous["groups"][base]
        plug = _itg_plug(bs_node, base, index)

        # 전 주인만 갖고 있던 인비트윈 아이템 / 페인트 웨이트를 먼저 걷어낸다.
        for item in set(old_group["items"]) - set(group["items"]):
            _remove_element("{0}.inputTargetItem[{1}]".format(plug, item))
        for vtx in set(old_group["target_weights"]) - set(group["target_weights"]):
            _remove_element("{0}.targetWeights[{1}]".format(plug, vtx))

        for item, item_data in group["items"].items():
            item_plug = "{0}.inputTargetItem[{1}]".format(plug, item)
            old_item = old_group["items"].get(item) or {}
            for name, attr_type in ITI_ARRAYS:
                value = item_data[name]
                # 새 주인이 그 배열을 안 쓰는데 전 주인은 썼다면 **빈 배열로 지운다**.
                # 값이 없다고 건너뛰면 전 주인의 델타가 남아, 이름만 바뀐 채 남의 모양이
                # 딸려 온다(같은 인덱스에 빈 인비트윈 아이템이 있는 씬에서 실제로 났다).
                if not value and old_item.get(name):
                    value = []
                _set_array("{0}.{1}".format(item_plug, name), value, attr_type)
            if item_data["geom_input"]:
                cmds.connectAttr(item_data["geom_input"],
                                 item_plug + ".inputGeomTarget", force=True)

        for vtx, value in group["target_weights"].items():
            cmds.setAttr("{0}.targetWeights[{1}]".format(plug, vtx), value)
        for name in ITG_SIMPLE:
            if group[name] is not None:
                cmds.setAttr("{0}.{1}".format(plug, name), group[name])
        for name in ITG_MATRIX:
            value = group[name]
            if not value and old_group[name]:
                value = IDENTITY_MATRIX      # 전 주인의 행렬을 지운다(기본값으로)
            if value:
                cmds.setAttr("{0}.{1}".format(plug, name), value, type="matrix")

    for attr in PER_TARGET_MULTIS:
        plug = "{0}.{1}[{2}]".format(bs_node, attr, index)
        if data[attr] is not None:
            cmds.setAttr(plug, data[attr])
        elif previous[attr] is not None:
            _remove_element(plug)

    iig = "{0}.inbetweenInfoGroup[{1}].inbetweenInfo".format(bs_node, index)
    for item in set(previous["inbetween"]) - set(data["inbetween"]):
        _remove_element("{0}[{1}]".format(iig, item))
    for item, info in data["inbetween"].items():
        item_plug = "{0}[{1}]".format(iig, item)
        if info["inbetweenTargetType"] is not None:
            cmds.setAttr(item_plug + ".inbetweenTargetType",
                         info["inbetweenTargetType"])
        if info["inbetweenTargetName"] is not None:
            cmds.setAttr(item_plug + ".inbetweenTargetName",
                         info["inbetweenTargetName"], type="string")

    # 연결은 값을 다 쓴 뒤에 건다(연결된 plug 는 setAttr 이 막힌다).
    if data["weight_input"]:
        cmds.connectAttr(data["weight_input"], weight, force=True)
    for dst in data["weight_outputs"]:
        try:
            cmds.connectAttr(weight, dst, force=True)
        except Exception:
            pass
    if data["locked"]:
        cmds.setAttr(weight, lock=True)


def _remap_directories(bs_node, remap):
    """Shape Editor 그룹이 들고 있는 타겟 인덱스 목록을 새 번호로 옮긴다.

    `targetDirectory[d].childIndices` 는 그 그룹이 담은 것들의 **표시 순서**이기도 하다.
    음수 `-d` 는 하위 그룹을 가리키므로 손대지 않고 자리만 지킨다. 양수(타겟)끼리는
    새 인덱스 오름차순으로 다시 세워, Shape Editor 도 바뀐 순서로 보이게 한다.
    """
    changed = 0
    for directory in _multi_indices(bs_node + ".targetDirectory"):
        plug = "{0}.targetDirectory[{1}].childIndices".format(bs_node, directory)
        children = _get(plug)
        if not children:
            continue
        children = [int(c) for c in children]

        moved = [remap.get(c, c) for c in children if c >= 0]
        moved.sort()
        result = []
        cursor = 0
        for child in children:
            if child < 0:
                result.append(child)
            else:
                result.append(moved[cursor])
                cursor += 1

        if result != children:
            _set_array(plug, result, "Int32Array")
            changed += 1
    return changed


def _remap_paint_index(bs_node, remap):
    """페인트 대상 타겟 인덱스도 같이 옮긴다(안 옮기면 남의 타겟을 칠하게 된다)."""
    for base in base_indices(bs_node):
        plug = "{0}.inputTarget[{1}].paintTargetIndex".format(bs_node, base)
        value = _get(plug)
        if value is None or value < 0:
            continue
        new_value = remap.get(int(value))
        if new_value is not None and new_value != value:
            try:
                cmds.setAttr(plug, new_value)
            except Exception:
                pass


# =========================
# 메인 동작
# =========================

def reorder_targets(bs_node, order):
    """`order` 에 적힌 타겟 이름 순서대로 blendShape 의 타겟 순서를 바꾼다.

    Args:
        bs_node: blendShape 노드 이름.
        order: 타겟 이름 목록. 지금 있는 타겟 전체의 **순열**이어야 한다.

    Returns:
        report dict — node / count / moved / directories / order(새 순서) 등.

    Raises:
        ValueError: 노드가 blendShape 가 아니거나, 목록이 순열이 아니거나,
            타겟이 편집(Edit/sculpt) 중일 때.
    """
    if not bsu.is_blendshape(bs_node):
        raise ValueError("'{0}' is not a blendShape node.".format(bs_node))

    current = list_targets(bs_node)
    if not current:
        raise ValueError("'{0}' has no targets.".format(bs_node))

    wanted = [str(name) for name in (order or [])]
    have = [name for _idx, name in current]
    if sorted(wanted) != sorted(have):
        missing = [n for n in have if n not in wanted]
        unknown = [n for n in wanted if n not in have]
        detail = []
        if len(wanted) != len(have):
            detail.append("{0} name(s) given for {1} target(s)".format(
                len(wanted), len(have)))
        if missing:
            detail.append("missing: " + ", ".join(missing[:5]))
        if unknown:
            detail.append("not a target: " + ", ".join(unknown[:5]))
        raise ValueError(
            "The new order must list every target of '{0}' exactly once ({1}). "
            "Press 'List Targets' again.".format(bs_node, "; ".join(detail)))

    editing = editing_target(bs_node)
    if editing != -1:
        name = dict(current).get(editing, "weight[{0}]".format(editing))
        raise ValueError(
            "'{0}' is in Edit (sculpt) mode on target '{1}'. Turn Edit off "
            "first - the Shape Editor tab's 'Exit All Edits' does it.".format(
                bs_node, name))

    # 있던 인덱스 슬롯을 그대로 쓴다 (듬성해도 그 모양 그대로).
    slots = [idx for idx, _name in current]
    index_of = {name: idx for idx, name in current}
    remap = {index_of[name]: slot for slot, name in zip(slots, wanted)}

    if all(old == new for old, new in remap.items()):
        return {"node": bs_node, "count": len(current), "moved": 0,
                "directories": 0, "order": wanted, "slots": slots}

    bases = base_indices(bs_node)
    snapshots = {idx: _snapshot_target(bs_node, idx, name, bases)
                 for idx, name in current}

    # 전부 떼어 낸 **뒤에** 전부 되쓴다. 하나씩 옮기면 아직 안 옮긴 타겟의 별칭/연결과
    # 부딪힌다(같은 이름이 두 인덱스에 걸리거나, 옮기려던 연결이 먼저 끊긴다).
    for data in snapshots.values():
        _detach_target(bs_node, data, bases)
    for old_index, data in snapshots.items():
        slot = remap[old_index]
        _write_target(bs_node, data, slot, bases, snapshots[slot])

    directories = _remap_directories(bs_node, remap)
    _remap_paint_index(bs_node, remap)

    return {
        "node": bs_node,
        "count": len(current),
        "moved": sum(1 for old, new in remap.items() if old != new),
        "directories": directories,
        "order": wanted,
        "slots": slots,
    }
