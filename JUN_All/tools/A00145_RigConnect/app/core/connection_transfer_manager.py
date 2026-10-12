# -*- coding: utf-8 -*-
"""
connection_transfer_manager - Connect > Transfer Connection 탭 로직 (v01.58).

"연결 전이" : A.attr <-> Tgt.x 로 이어진 연결을 끊고, **같은 이름의 어트리뷰트**를 가진 B 로
옮긴다 (B.attr <-> Tgt.x). 어느 쪽이 드라이버인지(upstream / downstream)에 따라 두 가지다.

    upstream   : Tgt.x -> A.attr   ==>   Tgt.x -> B.attr
    downstream : A.attr -> Tgt.x   ==>   B.attr -> Tgt.x

UI 비의존: 위젯에서 읽은 list/str 값만 받는다.

  - list_rows(objs, ...)         : 소스 오브젝트들의 어트리뷰트 행 (연결 정보 포함)
  - list_nodes(rows, attrs, ...) : 체크한 어트리뷰트에 연결된 노드들
  - missing_on(objs, attrs)      : 목적지에 없는 어트리뷰트
  - transfer(pairs, attrs, nodes, ...) : 전이 실행 (보고서 반환)

플러그 이름 (mayapy 2024 실측)
-----------------------------
`listConnections -connections -plugs` 는 자기 플러그와 상대 플러그를 번갈아 돌려준다.
`-shapes` 를 켜야 쉐입 노드가 트랜스폼 이름으로 바뀌지 않는다. blendShape 타겟(weight 별칭)은
플러그에 **별칭 이름**으로 나오므로 connect_manager.list_attrs 의 타겟 이름과 그대로 맞는다.
"""

import maya.cmds as cmds

from tools.A00145_RigConnect.app.core import connect_manager as cnt_mgr


# ----------------------------------------------------------------------
# 플러그 이름 다루기
# ----------------------------------------------------------------------

def plug_node(plug):
    """'node.attr' -> 'node' (경로 `|` 와 네임스페이스는 그대로)."""
    return plug.split(".", 1)[0]


def plug_attr(plug):
    """'node.attr[0].child' -> 'attr[0].child'."""
    return plug.split(".", 1)[1] if "." in plug else ""


def _short(node):
    """경로 노드 이름의 마지막 토큰 (리스트에서 고른 노드 이름과 비교할 때)."""
    return node.rsplit("|", 1)[-1]


def _same_node(a, b):
    """두 노드 이름이 같은 노드를 가리키는가. 한쪽이 전체 경로여도 맞춘다."""
    if a == b:
        return True
    try:
        la = cmds.ls(a, long=True) or []
        lb = cmds.ls(b, long=True) or []
    except Exception:
        return False
    return bool(la) and la == lb


# ----------------------------------------------------------------------
# 조회
# ----------------------------------------------------------------------

def connections_of(obj):
    """obj 의 모든 연결 - {attr: {"in": [상대 플러그...], "out": [상대 플러그...]}}.

    "in" 은 obj.attr 로 **들어오는** 연결(상대가 드라이버 = upstream),
    "out" 은 obj.attr 에서 **나가는** 연결(obj 가 드라이버 = downstream).
    """
    result = {}
    for upstream in (True, False):
        try:
            pairs = cmds.listConnections(
                obj, connections=True, plugs=True, shapes=True,
                source=upstream, destination=not upstream) or []
        except Exception:
            pairs = []
        key = "in" if upstream else "out"
        for own, other in zip(pairs[0::2], pairs[1::2]):
            attr = plug_attr(own)
            slot = result.setdefault(attr, {"in": [], "out": []})
            if other not in slot[key]:
                slot[key].append(other)
    return result


def list_rows(objs, channel_box_only=True, connected_only=True):
    """소스 오브젝트들의 어트리뷰트 행 (여러 오브젝트면 합집합, 첫 등장 순서).

    Args:
        objs: 소스 오브젝트 이름 리스트.
        channel_box_only: 채널 박스에 보이는 어트리뷰트만 (connect_manager.list_attrs 규칙).
            끄면 모든 어트리뷰트에, 목록에 없던 **연결된 플러그**(멀티 원소 등)도 더한다.
        connected_only: 연결이 하나라도 있는 어트리뷰트만.

    Returns:
        (rows, missing)
        rows : [{"name", "owners": [obj...], "in": {obj: [plug...]}, "out": {obj: [plug...]}}]
        missing : 씬에 없는 오브젝트들.
    """
    rows = {}
    order = []
    missing = []

    for obj in objs:
        if not obj or not cmds.objExists(obj):
            missing.append(obj)
            continue

        conns = connections_of(obj)
        names = list(cnt_mgr.list_attrs(obj, channel_box_only=channel_box_only))
        if not channel_box_only:
            names.extend(a for a in conns if a not in names)

        for name in names:
            conn = conns.get(name)
            if connected_only and not conn:
                continue
            row = rows.get(name)
            if row is None:
                row = rows[name] = {"name": name, "owners": [], "in": {}, "out": {}}
                order.append(name)
            row["owners"].append(obj)
            if conn:
                if conn["in"]:
                    row["in"][obj] = list(conn["in"])
                if conn["out"]:
                    row["out"][obj] = list(conn["out"])

    return [rows[n] for n in order], missing


def list_nodes(rows, attrs, upstream=True, downstream=True):
    """체크한 어트리뷰트에 연결된 노드들 (첫 등장 순서, 노드마다 한 행).

    Args:
        rows: list_rows 가 돌려준 행들.
        attrs: 체크한 어트리뷰트 이름들.
        upstream: 소스로 **들어오는** 연결의 노드를 담을지.
        downstream: 소스에서 **나가는** 연결의 노드를 담을지.

    Returns:
        [{"node", "in": [(src_obj, attr, other_plug)...], "out": [(src_obj, attr, other_plug)...]}]
        "in" = 그 노드가 소스를 구동한다(upstream), "out" = 소스가 그 노드를 구동한다(downstream).
    """
    wanted = set(attrs)
    nodes = {}
    order = []

    def _take(key, row):
        for obj, plugs in row[key].items():
            for plug in plugs:
                node = plug_node(plug)
                entry = nodes.get(node)
                if entry is None:
                    entry = nodes[node] = {"node": node, "in": [], "out": []}
                    order.append(node)
                entry[key].append((obj, row["name"], plug))

    for row in rows:
        if row["name"] not in wanted:
            continue
        if upstream:
            _take("in", row)
        if downstream:
            _take("out", row)

    return [nodes[n] for n in order]


def missing_on(objs, attrs):
    """목적지 오브젝트들에 없는 어트리뷰트 - {attr: [없는 obj...]} (전부 있으면 빈 dict)."""
    result = {}
    for attr in attrs:
        for obj in objs:
            if not obj or not cmds.objExists("{0}.{1}".format(obj, attr)):
                result.setdefault(attr, []).append(obj)
    return result


def pair_objects(sources, destinations):
    """소스와 목적지를 짝짓는다.

    목적지가 하나면 모든 소스가 그 하나로, 개수가 같으면 행 순서대로 1:1.
    그 밖에는 ValueError.
    """
    if not sources or not destinations:
        raise ValueError("Source and Destination lists must not be empty")
    if len(destinations) == 1:
        return [(src, destinations[0]) for src in sources]
    if len(sources) == len(destinations):
        return list(zip(sources, destinations))
    raise ValueError(
        "Cannot pair {0} source(s) with {1} destination(s) - use one destination "
        "or the same number of rows".format(len(sources), len(destinations)))


# ----------------------------------------------------------------------
# 전이
# ----------------------------------------------------------------------

def transfer(pairs, attrs, nodes, upstream=True, downstream=True):
    """연결 전이.

    Args:
        pairs: [(src_obj, dst_obj)...] - pair_objects 결과.
        attrs: 옮길 어트리뷰트 이름들 (소스와 목적지에 **같은 이름**).
        nodes: 체크한 상대 노드 이름들. 이 노드들과의 연결만 옮긴다.
        upstream: 소스로 들어오는 연결(노드 -> 소스)을 옮길지.
        downstream: 소스에서 나가는 연결(소스 -> 노드)을 옮길지.

    Returns:
        {"moved": [(direction, other_plug, src_plug, dst_plug)...],
         "skipped": [(src_plug, reason)...],
         "failed": [(src_plug, other_plug, error)...]}

    순서 : 먼저 목적지에 잇고(실패하면 소스는 그대로), 그다음 소스를 끊는다.
    목적지 어트리뷰트에 **다른** 입력이 이미 있으면 건너뛴다(소스도 그대로).
    """
    report = {"moved": [], "skipped": [], "failed": []}
    node_list = list(nodes)

    def _is_wanted(plug):
        node = plug_node(plug)
        return any(_same_node(node, n) for n in node_list)

    for src, dst in pairs:
        if src == dst:
            report["skipped"].append((src, "source and destination are the same object"))
            continue
        conns = connections_of(src)
        for attr in attrs:
            conn = conns.get(attr)
            src_plug = "{0}.{1}".format(src, attr)
            if not conn:
                continue
            dst_plug = "{0}.{1}".format(dst, attr)
            if not cmds.objExists(dst_plug):
                report["skipped"].append((src_plug, "'{0}' has no attribute '{1}'".format(dst, attr)))
                continue

            if upstream:
                for other in conn["in"]:
                    if not _is_wanted(other):
                        continue
                    existing = cmds.listConnections(dst_plug, source=True, destination=False,
                                                    plugs=True, shapes=True) or []
                    if existing and existing[0] != other:
                        report["skipped"].append((
                            src_plug, "'{0}' is already driven by '{1}'".format(dst_plug, existing[0])))
                        continue
                    try:
                        if not existing:
                            cmds.connectAttr(other, dst_plug, force=True)
                        cmds.disconnectAttr(other, src_plug)
                    except Exception as e:
                        report["failed"].append((src_plug, other, str(e)))
                        continue
                    report["moved"].append(("upstream", other, src_plug, dst_plug))

            if downstream:
                for other in conn["out"]:
                    if not _is_wanted(other):
                        continue
                    try:
                        # force 가 src -> other 를 dst -> other 로 바꾼다 (한 번에, 실패하면 그대로).
                        cmds.connectAttr(dst_plug, other, force=True)
                    except Exception as e:
                        report["failed"].append((src_plug, other, str(e)))
                        continue
                    report["moved"].append(("downstream", other, src_plug, dst_plug))

    return report
