# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# Framework.core.maya_fbx_names - 씬에서 FBXASC 이름(노드 · 블렌드셰이프 타겟 · 어트리뷰트)을 찾아 풀어 준다 (maya.cmds)
#
# 마야는 노드 이름에 일본어 · 띄어쓰기를 받지 않는다 - rename / aliasAttr 는 에러, OpenMaya setName 은 **조용히 무시**
# (2026-11-09 실측). 그래서 이름을 바꾸지 않고, 찾아서 원래 글자(fbx_name.decode)를 함께 돌려준다.
# 계획서: docs/plans/A00620_NameDecoder_plan.md

import re

import maya.cmds as cmds

from Framework.core import fbx_name

# 범위
SCOPE_SCENE = "scene"
SCOPE_SELECTED = "selected"
SCOPE_HIERARCHY = "hierarchy"

# NameEntry.kind
KIND_NODE = "node"
KIND_BS_TARGET = "bs_target"
KIND_ATTR = "attr"
KIND_ENUM = "enum"

_WEIGHT = re.compile(r"^weight\[(\d+)\]$")


class NameEntry(object):
    """찾은 이름 하나.

    kind      : node / bs_target / attr / enum
    raw       : 마야 안의 이름(짧은 이름 · alias · 어트리뷰트 이름 · enum 필드)
    decoded   : 원래 글자
    ok        : 깨진 FBXASC 구간이 없으면 True
    node_type : 노드 타입(bs_target 은 "blendShape")
    uuid      : 노드(또는 타겟 · 어트리뷰트를 가진 노드)의 UUID - 이름이 바뀌어도 찾는다
    owner     : 표에 보일 소유 노드 이름(node 는 부모 경로, 나머지는 노드 이름)
    index     : bs_target = 웨이트 인덱스, enum = 필드 값
    attr      : attr / enum = 어트리뷰트 이름(raw)
    """

    __slots__ = ("kind", "raw", "decoded", "ok", "node_type", "uuid", "owner", "index", "attr")

    def __init__(self, kind, raw, node_type, uuid, owner="", index=None, attr=None):
        self.kind = kind
        self.raw = raw
        self.decoded, self.ok = fbx_name.decode_ok(raw)
        self.node_type = node_type
        self.uuid = uuid
        self.owner = owner
        self.index = index
        self.attr = attr

    @property
    def encoded(self):
        return fbx_name.is_encoded(self.raw)

    def type_label(self):
        if self.kind == KIND_BS_TARGET:
            return "blendShape target [{0}]".format(self.index)
        if self.kind == KIND_ATTR:
            return "attribute"
        if self.kind == KIND_ENUM:
            return "enum field [{0}]".format(self.index)
        return self.node_type

    def __repr__(self):
        return "NameEntry({0}, {1!r} -> {2!r})".format(self.kind, self.raw, self.decoded)


# ================================================================
# 노드 찾기
# ================================================================

def _uuid(node):
    return (cmds.ls(node, uuid=True) or [""])[0]


def _short(node):
    return node.split("|")[-1]


def scope_nodes(scope):
    """범위 안의 노드(긴 이름). Selected = 고른 노드 + 그 셰이프 + 거기 걸린 blendShape.
    Hierarchy = 거기에 고른 트랜스폼 아래 모든 DAG 와 그 blendShape."""
    if scope == SCOPE_SCENE:
        return cmds.ls(long=True) or []

    sel = cmds.ls(selection=True, long=True, objectsOnly=True) or []
    nodes = list(sel)
    dag = [n for n in sel if cmds.objectType(n, isAType="dagNode")]
    if scope == SCOPE_HIERARCHY and dag:
        nodes += cmds.listRelatives(dag, allDescendents=True, fullPath=True) or []
    elif dag:
        nodes += cmds.listRelatives(dag, shapes=True, fullPath=True) or []
    # 메시를 고르면 그 블렌드셰이프 타겟도 보이게 - 히스토리의 blendShape 를 함께
    shapes = [n for n in nodes if cmds.objectType(n, isAType="shape")]
    if shapes:
        nodes += cmds.ls(cmds.listHistory(shapes, pruneDagObjects=True) or [], type="blendShape") or []

    seen = set()
    out = []
    for n in nodes:
        long_name = (cmds.ls(n, long=True) or [n])[0]
        if long_name not in seen:
            seen.add(long_name)
            out.append(long_name)
    return out


def blendshape_targets(bs):
    """[(index, alias)] - 웨이트 alias 가 있는 타겟만, 인덱스 순."""
    pairs = cmds.aliasAttr(bs, query=True) or []
    out = []
    for alias, plug in zip(pairs[0::2], pairs[1::2]):
        m = _WEIGHT.match(plug)
        if m:
            out.append((int(m.group(1)), alias))
    return sorted(out)


def scan(scope=SCOPE_SCENE, encoded_only=True, include_attrs=False):
    """범위 안의 이름을 찾아 [NameEntry]. encoded_only 면 FBXASC 가 든 것만."""
    entries = []
    for node in scope_nodes(scope):
        if not cmds.objExists(node):
            continue
        node_type = cmds.nodeType(node)
        uuid = _uuid(node)
        short = _short(node)
        owner = node.rsplit("|", 1)[0].split("|")[-1] if "|" in node.strip("|") else ""
        owner = fbx_name.decode(owner)
        if not encoded_only or fbx_name.is_encoded(short):
            entries.append(NameEntry(KIND_NODE, short, node_type, uuid, owner=owner))

        if node_type == "blendShape":
            for index, alias in blendshape_targets(node):
                if not encoded_only or fbx_name.is_encoded(alias):
                    entries.append(NameEntry(KIND_BS_TARGET, alias, node_type, uuid,
                                             owner=fbx_name.decode(short), index=index))

        if include_attrs:
            entries.extend(_attr_entries(node, node_type, uuid, short, encoded_only))
    return entries


def _attr_entries(node, node_type, uuid, short, encoded_only):
    out = []
    owner = fbx_name.decode(short)
    for attr in cmds.listAttr(node, userDefined=True) or []:
        if not encoded_only or fbx_name.is_encoded(attr):
            out.append(NameEntry(KIND_ATTR, attr, node_type, uuid, owner=owner, attr=attr))
        try:
            is_enum = cmds.attributeQuery(attr, node=node, attributeType=True) == "enum"
        except RuntimeError:
            continue
        if not is_enum:
            continue
        spec = (cmds.attributeQuery(attr, node=node, listEnum=True) or [""])[0]
        value = 0
        for field in spec.split(":"):
            if "=" in field:
                field, _sep, num = field.rpartition("=")
                try:
                    value = int(num)
                except ValueError:
                    pass
            if field and (not encoded_only or fbx_name.is_encoded(field)):
                out.append(NameEntry(KIND_ENUM, field, node_type, uuid, owner=owner, index=value, attr=attr))
            value += 1
    return out


# ================================================================
# 선택
# ================================================================

def node_of(entry):
    """항목의 노드 긴 이름(UUID 로 찾는다). 없으면 None."""
    found = cmds.ls(entry.uuid, long=True) if entry.uuid else None
    return found[0] if found else None


def select_entries(entries, add=False):
    """항목들의 노드를 마야에서 선택. 선택한 노드 목록."""
    nodes = []
    for e in entries:
        n = node_of(e)
        if n and n not in nodes:
            nodes.append(n)
    if nodes:
        cmds.select(nodes, add=add, noExpand=True)
    elif not add:
        cmds.select(clear=True)
    return nodes


def selected_uuids():
    """마야에서 지금 고른 노드의 UUID 집합 - Sync with Selection 용."""
    return set(cmds.ls(selection=True, uuid=True, objectsOnly=True) or [])
