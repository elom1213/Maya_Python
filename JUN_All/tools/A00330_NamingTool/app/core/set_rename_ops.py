# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-27
# A00330_NamingTool - Set Rename : 세트 이름의 부분 문자열 찾아 바꾸기.
#
# ── 마야 기본 기능이 왜 세트에 안 먹히나 (Maya 2024 실측) ──────────────────────
#
# `Modify > Search and Replace Names` 의 실체는 MEL `searchReplaceNames` 다.
# **이 명령 자체는 세트도 잘 바꾼다** — `"all"` 모드로 돌리면 세트 이름이 같이 바뀐다
# (실측: 세트 5개를 포함해 8개 이름이 바뀌었다).
#
# 문제는 `"selected"` 모드다. 세트를 고르려고 해도 **`cmds.select(set)` 은 세트가 아니라
# 그 멤버를 펼쳐서 선택한다**(실측: `ls(sl)` 이 `['pCube1']`). 그래서 선택 기반 모드는
# 세트를 영영 못 본다. `noExpand=True` 로 넘기면 세트 자신이 선택되고, 그때는
# `searchReplaceNames ... "selected"` 도 세트를 바꾼다 — **즉 막힌 것은 명령이 아니라
# "세트를 선택하는 방법"이었다.**
#
# `"all"` 모드는 대안이 못 된다. 씬의 메시·조인트·카메라까지 전부 바꾼다.
#
# → 그래서 이 탭은 **세트를 직접 열거해서 고르게 하고**, 바꾸기 전에 **미리보기**를 준다.
#
# ── 실측으로 알아낸 함정들 ────────────────────────────────────────────────────
#
# 1. **네임스페이스가 벗겨진다.** `rename("NS:in_ns", "plain")` 하면 세트가 **루트
#    네임스페이스로 옮겨간다**(NS 는 비게 된다). 짧은 이름만 바꿔 넘기면 레퍼런스에서
#    온 세트가 전부 네임스페이스를 잃는다. → **네임스페이스는 떼어 두고 짧은 이름만
#    치환한 뒤 다시 붙여서** rename 한다.
# 2. **마야가 이름을 조용히 고친다.** `1bad` -> `bad`(맨 앞 숫자가 **사라진다**),
#    `has space` -> `has_space`, `has-dash` -> `has_dash`, `a|b` -> `a_b`.
#    경고만 뜨고 넘어가므로 **의도와 다른 이름이 조용히 생긴다.**
#    → 여기서는 **미리 걸러 내고 건너뛴다**(마야의 조용한 변환을 흉내 내지 않는다).
# 3. **이름이 겹치면 번호를 붙인다.** `rename(b, "dup_set")` -> `dup_set1`. 에러가 아니다.
#    → 미리보기에서 **충돌로 표시**하고, 실행 후 **실제로 붙은 이름**을 보고한다.
# 4. **기본 세트는 못 바꾼다** — `initialShadingGroup` 은 `Cannot rename a read only node`.
#    `ls(readOnly=True)` 는 **빈 리스트를 준다**(판정에 쓰면 안 된다) —
#    `ls(defaultNodes=True)` 로 골라야 한다.
# 5. **잠긴 노드는 못 바꾼다** — `Cannot rename a locked node`.
# 6. **`partition` 은 `objectSet` 이 아니다.** `ls(type="objectSet")` 에 안 잡힌다.
#    따로 열거해야 한다(`shadingEngine` 은 `objectSet` 의 하위 타입이라 같이 잡힌다).
# 7. `rename` 은 **undo 된다**(실측).

import re


# 상태 코드 (UI 가 그대로 표시한다)
ST_OK = "OK"
ST_SAME = "no change"          # 검색어가 없어 이름이 그대로
ST_INVALID = "invalid name"    # 마야가 허용하지 않는 문자 -> 건너뛴다
ST_COLLISION = "name taken"    # 같은 이름이 이미 있다 -> 마야가 번호를 붙인다
ST_LOCKED = "locked"
ST_REFERENCED = "referenced"
ST_DEFAULT = "default set"
ST_GONE = "gone"               # 실행 시점에 사라진 노드

#: 이 상태들만 실제로 rename 을 시도한다
APPLICABLE = (ST_OK, ST_COLLISION)

#: 마야 노드 이름 규칙 - 영문/밑줄로 시작, 이후 영문·숫자·밑줄
_VALID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ================================================================
# 이름 헬퍼
# ================================================================

def split_namespace(name):
    """'NS:sub:leaf' -> ('NS:sub', 'leaf'). 네임스페이스가 없으면 ('', name).

    세트는 DAG 노드가 아니라 `|` 경로가 없다. `:` 만 갈라 주면 된다.
    """
    name = name or ""
    if ":" not in name:
        return "", name
    ns, leaf = name.rsplit(":", 1)
    return ns, leaf


def join_namespace(namespace, leaf):
    return "{0}:{1}".format(namespace, leaf) if namespace else leaf


def replace_in_name(leaf, search, replace, case_sensitive=True):
    """짧은 이름 안의 search 를 replace 로 모두 바꾼다.

    `replace` 는 **글자 그대로** 들어간다 - 정규식 치환 기호(`\\1` 등)로 해석하지 않는다.
    """
    if not search:
        return leaf
    if case_sensitive:
        return leaf.replace(search, replace)
    return re.sub(re.escape(search), lambda _m: replace, leaf, flags=re.IGNORECASE)


def invalid_characters(leaf):
    """마야 이름으로 쓸 수 없는 이유. 문제가 없으면 None."""
    if not leaf:
        return "the new name would be empty"
    if leaf[0].isdigit():
        return "a name cannot start with a digit (Maya drops the leading digit)"
    bad = sorted(set(ch for ch in leaf if not (ch.isalnum() or ch == "_")))
    if bad:
        return "illegal character(s): {0}".format(" ".join(repr(c) for c in bad))
    if not _VALID_NAME.match(leaf):
        return "not a legal Maya name"
    return None


# ================================================================
# 세트 열거
# ================================================================

def _is_default(cmds, node):
    return node in (cmds.ls(defaultNodes=True) or [])


def set_info(node, default_nodes=None):
    """세트 하나의 정보. 없으면 None."""
    cmds = _cmds()
    if cmds is None or not node or not cmds.objExists(node):
        return None

    if default_nodes is None:
        default_nodes = set(cmds.ls(defaultNodes=True) or [])

    node_type = cmds.nodeType(node)
    namespace, leaf = split_namespace(node)

    try:
        referenced = bool(cmds.referenceQuery(node, isNodeReferenced=True))
    except Exception:
        referenced = False
    try:
        locked = bool(cmds.lockNode(node, q=True, lock=True)[0])
    except Exception:
        locked = False
    try:
        members = len(cmds.sets(node, q=True) or [])
    except Exception:
        members = 0

    uuids = cmds.ls(node, uuid=True) or []

    return {
        "name": node,
        "leaf": leaf,
        "namespace": namespace,
        "type": node_type,
        "members": members,
        "uuid": uuids[0] if uuids else None,
        "default": node in default_nodes,
        "referenced": referenced,
        "locked": locked,
    }


def list_sets(include_shading_engines=False, include_partitions=False,
              include_default=False, include_referenced=True):
    """씬의 세트 목록(dict).

    `partition` 은 `objectSet` 이 아니므로(실측) 따로 열거한다.
    `shadingEngine` 은 `objectSet` 의 하위 타입이라 기본 목록에 섞여 들어온다 —
    렌더 셋업을 실수로 건드리지 않도록 **기본은 뺀다.**
    """
    cmds = _cmds()
    if cmds is None:
        return []

    default_nodes = set(cmds.ls(defaultNodes=True) or [])

    nodes = list(cmds.ls(type="objectSet") or [])
    if include_partitions:
        nodes += list(cmds.ls(type="partition") or [])

    out = []
    for node in nodes:
        info = set_info(node, default_nodes)
        if info is None:
            continue
        if info["type"] == "shadingEngine" and not include_shading_engines:
            continue
        if info["default"] and not include_default:
            continue
        if info["referenced"] and not include_referenced:
            continue
        out.append(info)

    out.sort(key=lambda d: d["name"])
    return out


def sets_from_selection():
    """지금 씬 선택과 관련된 세트 이름들.

    두 경로를 합친다 —
      1) **선택된 오브젝트가 속한 세트** (`listSets`). 메시 하나를 고르고 그것이 든
         세트를 찾는 것이 실제 작업에서 가장 흔한 흐름이다.
      2) **세트 자신이 선택된 경우** (`ls(sl, type="objectSet")`).
         `cmds.select(set)` 은 멤버를 펼치므로 보통 여기엔 안 잡히지만,
         `noExpand=True` 로 고른 경우엔 잡힌다.
    """
    cmds = _cmds()
    if cmds is None:
        return []

    found = []

    for node in (cmds.ls(sl=True, type="objectSet") or []):
        if node not in found:
            found.append(node)

    for obj in (cmds.ls(sl=True) or []):
        for s in (cmds.listSets(object=obj) or []):
            if s not in found:
                found.append(s)

    return sorted(found)


def select_sets_in_scene(names):
    """세트 자신을 씬에서 선택한다.

    **`noExpand=True` 가 핵심이다** - 빼면 마야가 멤버를 펼쳐 선택해 버린다(실측).
    """
    cmds = _cmds()
    if cmds is None:
        return 0
    alive = [n for n in (names or []) if cmds.objExists(n)]
    if not alive:
        cmds.select(clear=True)
        return 0
    cmds.select(alive, noExpand=True)
    return len(alive)


# ================================================================
# 미리보기
# ================================================================

def preview(names, search, replace, case_sensitive=True):
    """세트마다 (옛 이름 -> 새 이름 + 상태) 를 계산한다. 씬은 건드리지 않는다.

    돌려주는 각 항목:
        name · leaf · namespace · type · uuid · new_leaf · new_name · status · note
    """
    cmds = _cmds()
    rows = []
    if cmds is None:
        return rows

    default_nodes = set(cmds.ls(defaultNodes=True) or [])

    # 이 배치 안에서 새로 만들어질 이름 - 서로 부딪히는 것도 잡아야 한다
    produced = {}

    for name in (names or []):
        info = set_info(name, default_nodes)
        if info is None:
            rows.append({"name": name, "leaf": split_namespace(name)[1],
                         "namespace": split_namespace(name)[0], "type": "",
                         "uuid": None, "new_leaf": "", "new_name": "",
                         "status": ST_GONE, "note": "node no longer exists"})
            continue

        row = dict(info)
        new_leaf = replace_in_name(info["leaf"], search, replace, case_sensitive)
        # 네임스페이스는 그대로 다시 붙인다 - 안 붙이면 세트가 루트로 옮겨간다(실측)
        row["new_leaf"] = new_leaf
        row["new_name"] = join_namespace(info["namespace"], new_leaf)
        row["note"] = ""

        if info["default"]:
            row["status"] = ST_DEFAULT
            row["note"] = "Maya refuses to rename its default sets"
        elif info["referenced"]:
            row["status"] = ST_REFERENCED
            row["note"] = "referenced nodes cannot be renamed"
        elif info["locked"]:
            row["status"] = ST_LOCKED
            row["note"] = "unlock the node first"
        elif new_leaf == info["leaf"]:
            row["status"] = ST_SAME
        else:
            problem = invalid_characters(new_leaf)
            if problem:
                row["status"] = ST_INVALID
                row["note"] = problem
            elif cmds.objExists(row["new_name"]) or row["new_name"] in produced:
                row["status"] = ST_COLLISION
                row["note"] = "Maya will append a number"
            else:
                row["status"] = ST_OK

        if row["status"] in APPLICABLE:
            produced[row["new_name"]] = name

        rows.append(row)

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

def apply_rename(rows):
    """미리보기 행 중 적용 가능한 것만 rename 한다.

    **UUID 로 다시 찾아서** rename 한다 - 앞의 rename 이 이름을 바꿔 놓았을 수 있다.
    마야가 이름을 조용히 바꿀 수 있으므로(충돌 시 번호, 잘못된 문자 변환)
    **실제로 붙은 이름**을 `actual` 로 돌려준다.

    돌려주는 것: `(results, messages)`
    """
    cmds = _cmds()
    results, messages = [], []
    if cmds is None:
        return results, ["[ERR] maya.cmds is not available."]

    for row in (rows or []):
        if row.get("status") not in APPLICABLE:
            continue

        uuid = row.get("uuid")
        paths = cmds.ls(uuid) if uuid else []
        if not paths:
            results.append({"old": row["name"], "actual": None,
                            "ok": False, "error": "node no longer exists"})
            messages.append("[ERR] {0}: node no longer exists.".format(row["name"]))
            continue

        current = paths[0]
        try:
            actual = cmds.rename(current, row["new_name"])
        except Exception as e:
            results.append({"old": current, "actual": None,
                            "ok": False, "error": str(e)})
            messages.append("[ERR] {0}: {1}".format(current, e))
            continue

        results.append({"old": current, "actual": actual, "ok": True, "error": None})

        if actual != row["new_name"]:
            # 충돌로 번호가 붙었거나 마야가 문자를 바꿨다 - 조용히 넘기지 않는다
            messages.append(
                "[Warning] {0} -> {1} (asked for '{2}' - Maya changed it).".format(
                    current, actual, row["new_name"]))
        else:
            messages.append("[OK] {0} -> {1}".format(current, actual))

    messages.append("[OK] {0} set(s) renamed.".format(
        len([r for r in results if r["ok"]])))
    return results, messages
