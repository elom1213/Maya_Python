# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-11
# A00620_NameDecoder - Outliner 탭: 범위 안 DAG 계층 + 메시 아래 blendShape 타겟 (maya.cmds)
#
# 계획서: docs/plans/A00620_NameDecoder_outliner_plan.md
# 마야 아웃라이너는 일본어 · 중국어 이름을 표시할 수 없다 → 풀린 이름으로 같은 계층을 보여 준다. 씬은 바꾸지 않는다(선택만).
#
# 실측(mayapy 2024, 2026-11-11):
#   - `ls -dag -long -allPaths` 순서는 깊이 우선(아웃라이너와 같다)이지만 **인스턴스 셰이프 경로는 첫 인스턴스 바로 뒤**에
#     나온다 - 조상(`|A_grp`)보다 먼저. → 부모는 경로 문자열로 찾고, 트리는 두 번(만들기 → 붙이기)에 나눠 만든다.
#   - `ls -invisible` 은 visibility 를 끈 노드만 준다(그 자식은 안 준다) → 숨김은 조상에서 내려받는다.
#   - `ls -showType -allPaths` 는 [경로, 타입, ...] 쌍. `ls <paths> -uuid` 는 인스턴스 경로마다 하나씩(길이가 같다).
#   - `blendShape -q -geometry` 는 부분 경로('cube|cubeShape') → `ls -long` 으로 긴 경로.
# 큰 씬 대비: 마야 질의는 한 번씩 묶는다. 노드마다 getAttr · listRelatives 를 부르지 않는다.

import maya.cmds as cmds

from Framework.core import fbx_name
from Framework.core import maya_fbx_names as MFN

KIND_DAG = "dag"
KIND_BS = "bs"
KIND_BS_TARGET = "bs_target"


class OutlineNode(object):
    """트리 행 하나.

    key       : 행의 고유 키(DAG = 긴 경로, blendShape = 'bs|<붙은 경로>|<bs>', 타겟 = 그 뒤에 '|<index>')
    parent    : 부모 행 key (최상위 = None)
    kind      : dag / bs / bs_target
    raw       : 마야 짧은 이름(타겟 = alias)
    decoded   : 풀린 글자 · ok = 깨진 FBXASC 가 없으면 True
    node_type : 노드 타입(bs · 타겟 = 'blendShape')
    uuid      : 노드 UUID(타겟 = blendShape 노드)
    path      : DAG = 긴 경로, bs · 타겟 = blendShape 노드 이름
    hidden    : 자신이나 조상의 visibility 가 꺼졌거나 중간(intermediate) 셰이프
    index     : 타겟 = 웨이트 인덱스
    """

    __slots__ = ("key", "parent", "kind", "raw", "decoded", "ok", "node_type", "uuid", "path", "hidden", "index")

    def __init__(self, key, parent, kind, raw, node_type, uuid, path="", hidden=False, index=None):
        self.key = key
        self.parent = parent
        self.kind = kind
        self.raw = raw
        self.decoded, self.ok = fbx_name.decode_ok(raw)
        self.node_type = node_type
        self.uuid = uuid
        self.path = path
        self.hidden = hidden
        self.index = index

    @property
    def encoded(self):
        return fbx_name.is_encoded(self.raw)

    def state_key(self):
        """Refresh 뒤에도 같은 행을 찾는 키 - 이름이 바뀌어도(Rename to ASCII) 같도록 UUID 기준.
        인스턴스는 UUID 가 같아 펼침 · 선택을 함께 기억한다(마야 아웃라이너도 둘 다 고른다)."""
        if self.kind == KIND_BS_TARGET:
            return "t:{0}:{1}".format(self.uuid, self.index)
        if self.kind == KIND_BS:
            return "b:{0}".format(self.uuid)
        return "d:{0}".format(self.uuid or self.path)

    def decoded_path(self):
        """풀린 전체 경로(DAG). bs · 타겟은 'blendShape.타겟'."""
        if self.kind == KIND_DAG:
            return fbx_name.decode(self.path)
        if self.kind == KIND_BS_TARGET:
            return "{0}.{1}".format(fbx_name.decode(self.path), self.decoded)
        return fbx_name.decode(self.path)

    def __repr__(self):
        return "OutlineNode({0}, {1!r} -> {2!r})".format(self.kind, self.raw, self.decoded)


# ================================================================
# 행 만들기 (마야 없이 시험 가능한 순수 함수)
# ================================================================

def _parent_path(path):
    head = path.rsplit("|", 1)[0]
    return head if head else None


def build_rows(dag_rows, bs_rows=(), encoded_branches_only=False):
    """[OutlineNode] - 입력 순서 그대로(형제 순서 = 씬 순서).

    dag_rows : [(긴 경로, 타입, uuid, hidden)]
    bs_rows  : [(붙일 행의 긴 경로, blendShape 이름, bs uuid, [(index, alias)])] - 붙일 행이 없으면 버린다
    encoded_branches_only : FBXASC(또는 깨진) 이름이 하나라도 든 가지만. 조상은 FBXASC 가 없어도 남긴다.
    """
    present = set(row[0] for row in dag_rows)
    out = []
    for path, node_type, uuid, hidden in dag_rows:
        parent = _parent_path(path)
        out.append(OutlineNode(path, parent if parent in present else None, KIND_DAG,
                               path.rsplit("|", 1)[-1], node_type, uuid, path=path, hidden=bool(hidden)))
    for attach, bs, bs_uuid, targets in bs_rows:
        if attach not in present:
            continue
        key = "bs|{0}|{1}".format(attach, bs)
        out.append(OutlineNode(key, attach, KIND_BS, bs.rsplit("|", 1)[-1], "blendShape", bs_uuid, path=bs))
        for index, alias in targets:
            out.append(OutlineNode("{0}|{1}".format(key, index), key, KIND_BS_TARGET, alias, "blendShape",
                                   bs_uuid, path=bs, index=index))
    if encoded_branches_only:
        out = prune_to_encoded(out)
    return out


def prune_to_encoded(nodes):
    """FBXASC 이름이 든 행과 그 조상만 남긴다(순서 유지). 부모는 key 로 거슬러 오른다 - 순서에 기대지 않는다."""
    parent_of = dict((n.key, n.parent) for n in nodes)
    keep = set()
    for n in nodes:
        if not (n.encoded or not n.ok):
            continue
        key = n.key
        while key is not None and key not in keep:
            keep.add(key)
            key = parent_of.get(key)
    return [n for n in nodes if n.key in keep]


# ================================================================
# 마야에서 모으기
# ================================================================

def _scene_dag():
    """[(긴 경로, 타입)] 씬 순서, 인스턴스는 경로마다."""
    flat = cmds.ls(dag=True, long=True, showType=True, allPaths=True) or []
    return list(zip(flat[0::2], flat[1::2]))


def _hidden_paths(paths):
    """숨은 경로 집합 - visibility 끈 노드 · 중간 셰이프 + 그 아래 전부."""
    direct = set(cmds.ls(dag=True, long=True, invisible=True, allPaths=True) or [])
    direct.update(cmds.ls(dag=True, long=True, intermediateObjects=True, allPaths=True) or [])
    if not direct:
        return set()
    memo = {}

    def hidden(path):
        if path in memo:
            return memo[path]
        result = path in direct
        if not result:
            parent = _parent_path(path)
            result = hidden(parent) if parent else False
        memo[path] = result
        return result

    return set(p for p in paths if hidden(p))


def _scope_paths(scope, all_paths, shape_set):
    """범위 안 경로 집합(조상 포함). Scene = None(전부)."""
    if scope == MFN.SCOPE_SCENE:
        return None
    path_set = set(all_paths)
    sel = cmds.ls(selection=True, long=True, objectsOnly=True) or []
    picked = [p for p in sel if p in path_set]
    # blendShape 노드를 골랐으면 그 메시를 고른 것으로
    for bs in cmds.ls(sel, type="blendShape") or []:
        picked += cmds.ls(cmds.blendShape(bs, query=True, geometry=True) or [], long=True) or []
    wanted = set(picked)
    if not picked:
        return wanted
    prefixes = tuple(p + "|" for p in picked)
    for p in all_paths:
        if not p.startswith(prefixes):
            continue
        if scope == MFN.SCOPE_HIERARCHY:
            wanted.add(p)
        elif p in shape_set and _parent_path(p) in wanted:   # Selected = 그 셰이프까지
            wanted.add(p)
    # 조상 - 위치가 보이게
    for p in list(wanted):
        parent = _parent_path(p)
        while parent and parent not in wanted:
            wanted.add(parent)
            parent = _parent_path(parent)
    return wanted


def _uuids(paths):
    if not paths:
        return []
    found = cmds.ls(paths, uuid=True) or []
    if len(found) == len(paths):
        return found
    return [(cmds.ls(p, uuid=True) or [""])[0] for p in paths]   # 길이가 어긋나면 하나씩(드묾)


def _bs_rows(shapes):
    """[(붙일 경로, bs, uuid, [(index, alias)])] - 메시 트랜스폼(셰이프 표시 중이면 셰이프) 아래."""
    out = []
    for bs in cmds.ls(type="blendShape") or []:
        try:
            geo = cmds.blendShape(bs, query=True, geometry=True) or []
        except RuntimeError:
            continue
        uuid = (cmds.ls(bs, uuid=True) or [""])[0]
        targets = MFN.blendshape_targets(bs)
        for shape in cmds.ls(geo, long=True) or []:
            attach = shape if shapes else _parent_path(shape)
            if attach:
                out.append((attach, bs, uuid, targets))
    return out


def collect(scope=MFN.SCOPE_SCENE, shapes=False, blend_shapes=True, encoded_branches_only=False):
    """범위의 아웃라이너 행 [OutlineNode]."""
    dag = _scene_dag()
    all_paths = [p for p, _t in dag]
    shape_set = set(cmds.ls(dag=True, long=True, shapes=True, allPaths=True) or [])
    wanted = _scope_paths(scope, all_paths, shape_set)
    kept = [(p, t) for p, t in dag
            if (wanted is None or p in wanted) and (shapes or p not in shape_set)]
    paths = [p for p, _t in kept]
    uuids = _uuids(paths)
    hidden = _hidden_paths(paths)
    dag_rows = [(p, t, u, p in hidden) for (p, t), u in zip(kept, uuids)]
    bs_rows = _bs_rows(shapes) if blend_shapes else ()
    return build_rows(dag_rows, bs_rows, encoded_branches_only=encoded_branches_only)


# ================================================================
# 선택
# ================================================================

def maya_name(node):
    """행의 마야 노드 이름. DAG 는 경로(인스턴스를 구분), 없어졌으면 UUID 로 찾는다."""
    if node.path and cmds.objExists(node.path):
        return node.path
    found = cmds.ls(node.uuid, long=True) if node.uuid else None
    return found[0] if found else None


def select_nodes(nodes, add=False):
    """행들의 노드를 마야에서 선택(타겟 = blendShape 노드). 선택한 이름 목록."""
    names = []
    for n in nodes:
        name = maya_name(n)
        if name and name not in names:
            names.append(name)
    if names:
        cmds.select(names, add=add, noExpand=True)
    elif not add:
        cmds.select(clear=True)
    return names


def select_hierarchy(nodes):
    """DAG 행과 그 아래 전부를 선택."""
    names = [maya_name(n) for n in nodes if n.kind == KIND_DAG]
    names = [n for n in names if n]
    if names:
        cmds.select(names, hierarchy=True)
    return names


def selected_paths():
    """지금 마야 선택의 (긴 경로 집합, uuid 집합) - Sync 용."""
    return (set(cmds.ls(selection=True, long=True, objectsOnly=True) or []),
            set(cmds.ls(selection=True, uuid=True, objectsOnly=True) or []))
