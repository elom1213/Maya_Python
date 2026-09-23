# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
# A00330_NamingTool - Quick Rename > Insert : 이름의 n 번째 자리에 글자를 끼워 넣는다 (v01.09).
#
# ── 위치(Position) 규칙 ──────────────────────────────────────────────────────
#
#   양수·0 은 **앞에서 센 글자 수** 뒤에 넣는다.  음수는 **맨 끝에서부터** 센다.
#
#       name = "arm_jnt",  text = "X"
#        0 -> "Xarm_jnt"      (맨 앞)
#        3 -> "armX_jnt"      (앞 3 글자 뒤)
#       -1 -> "arm_jntX"      (맨 끝)
#       -4 -> "arm_Xjnt"      (뒤 3 글자 앞)
#
#   즉 0 과 -1 이 서로 짝(맨 앞 / 맨 끝)이다. `-0` 이 없으니 음수는 -1 부터 끝을 가리킨다.
#   이름보다 먼 자리(길이 3 인 이름에 5)는 **끝(앞)에 붙이고** 미리보기에 그렇게 적는다 -
#   이름 길이가 제각각인 여러 오브젝트에 한 번에 쓰기 때문에 에러로 막지 않는다.
#
# ── 무엇을 바꾸나 ───────────────────────────────────────────────────────────
#
#   **짧은 이름(leaf)만** 센다. DAG 경로(`|grp|`)와 네임스페이스(`NS:`)는 떼어 두고
#   다시 붙인다 - 네임스페이스를 빼고 rename 하면 노드가 루트 네임스페이스로 옮겨간다
#   (set_rename_ops 함정 1 과 같다).
#
# ── 미리보기와 적용 ─────────────────────────────────────────────────────────
#
#   preview() 는 씬을 건드리지 않고 행마다 새 이름과 상태를 준다. apply_rows() 는
#   적용 가능한 행만 **깊은 노드부터** rename 한다 - 부모를 먼저 바꾸면 미리 잡아 둔
#   자식의 경로가 틀어진다. 상태 규칙은 Set Rename 탭(set_rename_ops)과 같다.

from .set_rename_ops import (
    split_namespace, join_namespace, invalid_characters,
    ST_OK, ST_SAME, ST_INVALID, ST_COLLISION, ST_LOCKED, ST_REFERENCED, ST_GONE,
    APPLICABLE,
)

ST_DEFAULT = "default node"
ST_NOT_NODE = "not a node"     # 컴포넌트(.vtx[0]) 등


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ================================================================
# 순수 문자열 규칙 (Maya 없이 테스트된다)
# ================================================================

def insert_index(length, position):
    """이름 길이와 Position 으로 실제 삽입 인덱스를 준다. -> (index, clamped)

    clamped 는 Position 이 이름 밖을 가리켜 앞/끝으로 당겨졌는지.
    """
    position = int(position)
    index = position if position >= 0 else length + 1 + position
    clamped = index < 0 or index > length
    return max(0, min(length, index)), clamped


def insert_text(leaf, text, position):
    """leaf 의 Position 자리에 text 를 넣은 새 이름. -> (new_leaf, clamped)"""
    leaf = leaf or ""
    index, clamped = insert_index(len(leaf), position)
    return leaf[:index] + (text or "") + leaf[index:], clamped


def split_path(path):
    """'|grp|NS:leaf' -> ('|grp', 'NS', 'leaf'). DG 노드는 ('', ns, leaf)."""
    parent, _sep, node = (path or "").rpartition("|")
    namespace, leaf = split_namespace(node)
    return parent, namespace, leaf


# ================================================================
# 미리보기
# ================================================================

def _row(path, parent, namespace, leaf):
    return {"path": path, "parent": parent, "namespace": namespace, "leaf": leaf,
            "new_leaf": "", "new_name": "", "status": "", "note": ""}


def preview(nodes, text, position):
    """노드(롱 경로)마다 새 이름과 상태를 계산한다. 씬은 바꾸지 않는다.

    각 행: path · parent · namespace · leaf · new_leaf · new_name · status · note
    """
    cmds = _cmds()
    rows = []
    if cmds is None:
        return rows

    default_nodes = set(cmds.ls(defaultNodes=True) or [])
    # 이 배치 안에서 만들어질 이름 - 같은 부모 아래에서 서로 부딪히는 것도 잡는다.
    # DAG 노드는 부모가 다르면 같은 이름을 쓸 수 있고, DG 노드는 씬 전체에서 하나뿐이다.
    produced = set()

    for path in (nodes or []):
        parent, namespace, leaf = split_path(path)
        row = _row(path, parent, namespace, leaf)
        rows.append(row)

        if "." in leaf:
            row["status"] = ST_NOT_NODE
            row["note"] = "components cannot be renamed"
            continue
        if not cmds.objExists(path):
            row["status"] = ST_GONE
            row["note"] = "node no longer exists"
            continue

        new_leaf, clamped = insert_text(leaf, text, position)
        row["new_leaf"] = new_leaf
        row["new_name"] = join_namespace(namespace, new_leaf)
        if clamped:
            row["note"] = "position is outside the name - put at the {0}".format(
                "end" if int(position) >= 0 else "start")

        short = cmds.ls(path)[0] if cmds.ls(path) else path
        if short in default_nodes or path in default_nodes:
            row["status"] = ST_DEFAULT
            row["note"] = "Maya refuses to rename its default nodes"
        elif cmds.referenceQuery(path, isNodeReferenced=True):
            row["status"] = ST_REFERENCED
            row["note"] = "referenced nodes cannot be renamed"
        elif (cmds.lockNode(path, q=True, lock=True) or [False])[0]:
            row["status"] = ST_LOCKED
            row["note"] = "unlock the node first"
        elif not text:
            row["status"] = ST_SAME
            row["note"] = "the Text field is empty"
        else:
            problem = invalid_characters(new_leaf)
            if problem:
                row["status"] = ST_INVALID
                row["note"] = problem
            else:
                is_dag = path.startswith("|")
                target = (parent + "|" + row["new_name"]) if is_dag else row["new_name"]
                key = (parent if is_dag else None, row["new_name"])
                if cmds.objExists(target) or key in produced:
                    row["status"] = ST_COLLISION
                    row["note"] = "name taken - Maya will append a number"
                else:
                    row["status"] = ST_OK
                produced.add(key)

    return rows


def summarize(rows):
    """상태별 개수. UI 로그용."""
    counts = {}
    for row in (rows or []):
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


# ================================================================
# 적용
# ================================================================

def apply_rows(rows):
    """적용 가능한 행만 rename 한다. -> (final_paths, messages)

    **깊은 노드부터** 바꾼다. 부모를 먼저 바꾸면 자식의 롱 경로가 달라지므로, 자식을 먼저
    바꾸고 부모를 바꾼 뒤에는 그 아래 행들의 경로 앞부분을 새 경로로 고쳐 쓴다.
    final_paths 는 rows 와 같은 순서로 **지금 씬의 경로**다(리스트 갱신용).
    """
    cmds = _cmds()
    if cmds is None:
        return [], ["[ERROR] maya.cmds is not available."]

    current = [row["path"] for row in rows]
    messages = []
    renamed = 0

    order = sorted(range(len(rows)), key=lambda i: current[i].count("|"), reverse=True)
    for i in order:
        row = rows[i]
        if row["status"] not in APPLICABLE:
            continue
        old = current[i]
        if not cmds.objExists(old):
            messages.append("[ERROR] {0}: node no longer exists.".format(old))
            continue
        try:
            actual = cmds.rename(old, row["new_name"])
        except Exception as e:
            messages.append("[ERROR] {0}: {1}".format(old, e))
            continue

        renamed += 1
        actual_node = actual.split("|")[-1]
        new_path = (row["parent"] + "|" + actual_node) if old.startswith("|") else actual_node
        # 이 노드 아래에 있던 행들의 경로를 새 경로로 옮긴다
        for j, path in enumerate(current):
            if path == old:
                current[j] = new_path
            elif path.startswith(old + "|"):
                current[j] = new_path + path[len(old):]

        old_short = old.split("|")[-1]
        if actual_node != row["new_name"]:
            messages.append("[WARN] {0} -> {1} (asked for '{2}' - Maya changed it).".format(
                old_short, actual_node, row["new_name"]))
        else:
            messages.append("[OK] {0} -> {1}".format(old_short, actual_node))

    messages.append("[OK] Insert : {0} object(s) renamed.".format(renamed))
    return current, messages


def display_names(paths):
    """롱 경로를 리스트에 보일 짧은 고유 이름으로. 사라진 노드는 경로 그대로."""
    cmds = _cmds()
    if cmds is None:
        return list(paths or [])
    return [(cmds.ls(p) or [p])[0] if cmds.objExists(p) else p for p in (paths or [])]
