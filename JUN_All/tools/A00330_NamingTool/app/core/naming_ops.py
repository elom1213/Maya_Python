# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-02
# A00330_NamingTool - core logic (maya.cmds)
#
# 레거시 두 소스의 네이밍 로직을 순수 함수로 이식한다.
#   - JUN_PY_NamingTool_V03_04.py : Naming Dynamics(계층 토큰), Copy Name
#   - ref/ref_01.mel              : Quick Rename(Front Insert / Change New / Last Add / -1 trim)
# UI 는 이 함수들만 호출한다(thin UI). Maya 밖에서도 import 가능하도록 cmds 는 lazy.

from .set_rename_ops import split_namespace, join_namespace, replace_in_name
from . import token_ops


#: 세트를 대상으로 이름을 복사할 때 기본으로 붙는 접미사.
#: 세트는 DG 노드라 **같은 이름을 그대로 쓸 수 없다**(실측: 마야가 조용히 `name1` 로 바꾼다).
DEFAULT_SET_COPY_SUFFIX = "_copy"

#: Token 미리보기 전용 상태 (나머지는 set_rename_ops 의 ST_* 를 쓴다)
ST_TOKEN = "token error"          # 토큰 칸 문제로 Rename 이 실행되지 않는다
ST_DEFAULT_NODE = "default node"  # 마야 기본 노드 (insert_ops.ST_DEFAULT 와 같은 글자)


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ================================================================
# 공용 헬퍼
# ================================================================

def short_name(name):
    """DAG 경로/네임스페이스를 제거하고 leaf 이름만 반환. 'a|b:c' -> 'c'."""
    return name.split("|")[-1].split(":")[-1]


def _to_uuid(node):
    """노드(짧은 이름/경로/UUID)를 UUID 로 변환. 실패 시 None.

    씬에 같은 이름의 오브젝트가 여러 개면 짧은 이름은 모호해서 rename 이 실패한다.
    UUID 는 rename 중에도 바뀌지 않으므로, 노드를 잡아두는 안정적 핸들로 쓴다.
    """
    cmds = _cmds()
    if cmds is None:
        return None
    uuids = cmds.ls(node, uuid=True) or []
    return uuids[0] if uuids else None


def _rename_by_uuid(uuid, new_name):
    """UUID 로 현재 DAG 경로를 다시 찾아 rename. 성공하면 새 이름(경로) 반환, 없으면 None.

    부모를 rename 하면 자식의 DAG 경로가 바뀌므로, 미리 잡아둔 경로 대신 매번
    UUID → 현재 경로로 해석해서 rename 해야 안전하다.
    """
    cmds = _cmds()
    if cmds is None or not uuid:
        return None
    paths = cmds.ls(uuid, long=True) or []
    if not paths:
        return None
    return cmds.rename(paths[0], new_name)


def is_set_node(node):
    """objectSet / shadingEngine / partition 이면 True.

    `nodeType(inherited=True)` 로 본다 - `shadingEngine` 은 `objectSet` 의 하위 타입이라
    `nodeType()` 문자열 비교로는 놓친다(실측:
    `['containerBase', 'entity', 'objectSet', 'shadingEngine']`).
    """
    cmds = _cmds()
    if cmds is None or not node or not cmds.objExists(node):
        return False
    inherited = cmds.nodeType(node, inherited=True) or []
    return "objectSet" in inherited or "partition" in inherited


def _zeros(length):
    return "0" * length if length > 0 else ""


def _pad(max_pad, index):
    """index 를 max_pad 자리수로 0 패딩. (원본 get_idx_with_pad 이식)"""
    text = str(index)
    return _zeros(max_pad - len(text)) + text


class undo_chunk(object):
    """with undo_chunk(): ... 로 한 번의 Undo 로 묶는다."""

    def __enter__(self):
        cmds = _cmds()
        if cmds:
            cmds.undoInfo(openChunk=True)
        return self

    def __exit__(self, *args):
        cmds = _cmds()
        if cmds:
            cmds.undoInfo(closeChunk=True)
        return False


# ================================================================
# Tab 1 : Naming Dynamics  (JUN_cmd_rename_for_dyn_02 이식)
# ================================================================

def build_hierarchy_groups(objects, hierarchy=True):
    """각 루트 오브젝트마다 [root, 자손...] 리스트를 만든다.

    원본 규칙 그대로:
      - allDescendents 를 모으되, 루트가 transform 이면 자손 중 transform 만 남긴다
        (shape 노드 제외).
      - [자손...] + [root] 후 reverse → [root, 얕은자손 ... 깊은자손] 순서.

    hierarchy=False (v01.18, Token 탭 Hierarchy 체크 해제) : 자손을 모으지 않는다 - [root] 만.
    """
    cmds = _cmds()
    if cmds is None:
        return []

    groups = []
    for obj in objects:
        # 입력 이름을 고유 DAG 경로로 정규화. 씬에 동일 이름이 여럿이면
        # 짧은 이름은 모호하므로 fullPath 로 다뤄야 rename 이 실패하지 않는다.
        roots = cmds.ls(obj, long=True) or []
        for root in roots:
            if not hierarchy:
                groups.append([root])
                continue
            descendants = cmds.listRelatives(
                root, allDescendents=True, fullPath=True) or []
            if descendants and cmds.objectType(root) == "transform":
                descendants = [d for d in descendants
                               if cmds.objectType(d) == "transform"]
            chain = list(descendants) + [root]
            chain.reverse()
            groups.append(chain)
    return groups


def rename_dynamics(objects, token1, token2, token3,
                    index1, index2, pad1, pad2):
    """계층 토큰 네이밍. 'token1_token2_token3_idx01_idx02' 로 일괄 rename.

    token01 = 루트 그룹마다 증가, token02 = 그룹 내 항목마다 증가(그룹마다 리셋).
    반환: 실제 rename 된 노드 개수.
    """
    cmds = _cmds()
    if cmds is None:
        return 0

    groups = build_hierarchy_groups(objects)

    token01 = int(index1)
    pad1 = int(pad1)
    pad2 = int(pad2)

    # 1) rename 하기 전에 (UUID, 새 이름) 배정을 모두 계산한다.
    #    부모를 rename 하면 자식 DAG 경로가 바뀌므로, 안정적 핸들인 UUID 로 잡아둔다.
    plan = []
    for group in groups:
        string01 = _pad(pad1, token01)
        token02 = int(index2)

        for node in group:
            string02 = _pad(pad2, token02)
            new_name = "_".join([token1, token2, token3, string01, string02])
            uuid = _to_uuid(node)
            if uuid:
                plan.append((uuid, new_name))
            token02 += 1

        token01 += 1

    # 2) UUID 로 현재 경로를 다시 찾아가며 rename → 동일 이름/계층이 있어도 안전.
    count = 0
    for uuid, new_name in plan:
        if _rename_by_uuid(uuid, new_name) is not None:
            count += 1

    return count


def rename_tokens(objects, tokens, hierarchy=True):
    """Rename > Token 탭 (v01.07). 토큰 규칙으로 오브젝트와 transform 자손을 일괄 rename.

    hierarchy=False (v01.18) : 자손은 그대로 두고 리스트의 오브젝트만 바꾼다.

    `rename_dynamics` 의 일반화다 - 토큰 개수와 종류가 자유롭고, 번호를 세는 규칙은
    `token_ops` 에 있다(Numbering 1 개 = 전체 순번, 2 개 = 오브젝트 / 오브젝트 안의 노드).
    레거시 기본 규칙(DEFAULT_TOKENS)이면 `rename_dynamics` 와 같은 이름이 나온다.

    **네임스페이스는 보존한다** - 짧은 이름만 주면 노드가 루트 네임스페이스로 옮겨간다(copy_name 과 같은 규칙).

    반환: `(count, notes)`
        notes : 실행을 막은 이유(`[WARN]`) 또는 마야가 이름을 바꾼 항목(`[Warning]`)
    """
    tokens = token_ops.normalize_tokens(tokens)
    errors = token_ops.validate(tokens)
    if errors:
        return 0, ["[WARN] " + e for e in errors]

    cmds = _cmds()
    if cmds is None:
        return 0, ["[WARN] Maya not available."]

    groups = build_hierarchy_groups(objects, hierarchy)
    names = token_ops.plan_names([len(g) for g in groups], tokens)

    # rename 전에 UUID 로 전부 잡아 둔다 - 부모를 바꾸면 자식 경로가 바뀐다.
    plan = []
    for group, group_names in zip(groups, names):
        for node, leaf in zip(group, group_names):
            namespace, _old = split_namespace(short_name_with_namespace(node))
            plan.append((_to_uuid(node), namespace, leaf, node))

    count = 0
    notes = []
    for uuid, namespace, leaf, original in plan:
        # 잠긴 · 레퍼런스 노드는 cmds.rename 이 RuntimeError 를 낸다 - 그 노드만 건너뛰고 계속한다
        # (v01.15 전에는 예외가 나서 거기서 멈췄다. 미리보기 표에 미리 locked / referenced 로 보인다).
        try:
            new_name = _rename_by_uuid(uuid, join_namespace(namespace, leaf))
        except RuntimeError as e:
            notes.append("[Warning] {0}: not renamed - {1}".format(original, str(e).strip()))
            continue
        if new_name is None:
            notes.append("[Warning] {0}: node no longer exists.".format(original))
            continue
        count += 1
        if short_name(new_name) != leaf:
            notes.append("[Warning] {0} -> {1} (asked for '{2}' - Maya changed it, "
                         "the name is already used).".format(original, new_name, leaf))
    return count, notes


# ================================================================
# Rename > Token 미리보기 (v01.15)
# ================================================================

def preview_tokens(objects, tokens, hierarchy=True):
    """Rename 을 누르면 무엇이 어떻게 바뀌는지 - **씬은 바꾸지 않는다** (v01.15).

    hierarchy : rename_tokens 와 같다 (v01.18).

    `rename_tokens` 와 같은 순서로 노드를 모으고(`build_hierarchy_groups`) 같은 이름을 계획한다.
    상태 규칙은 Quick Rename > Insert 와 같다(`set_rename_ops` 의 ST_*).

    반환: `(rows, errors)`
        rows   : 노드마다 dict - path · parent(롱 경로, 월드면 '') · old_name · new_name ·
                 status · note · group(몇 번째 오브젝트) · root(그 오브젝트의 루트인가)
        errors : 토큰 문제(있으면 new_name 은 비고 status 는 ST_TOKEN)

    **name taken 은 이름을 차례로 바꾸는 과정을 흉내 내서** 판정한다. 같은 부모 아래 이름 칸을
    지금 씬 그대로 채워 두고, rename 순서대로 옛 이름을 빼고 새 이름을 넣는다 - 그래서
    "곧 다른 이름으로 바뀔 형제" 의 이름을 받는 경우는 막지 않고, 이미 이 배치에서 쓴 이름이나
    배치 밖 노드의 이름과 겹칠 때만 name taken 이다(마야가 뒤에 번호를 붙인다).
    """
    from .set_rename_ops import (
        invalid_characters, ST_OK, ST_SAME, ST_INVALID, ST_COLLISION,
        ST_LOCKED, ST_REFERENCED, ST_GONE)

    cmds = _cmds()
    if cmds is None:
        return [], ["Maya not available."]

    tokens = token_ops.normalize_tokens(tokens)
    errors = token_ops.validate(tokens)

    groups = build_hierarchy_groups(objects, hierarchy)
    if errors:
        names = [[""] * len(g) for g in groups]
    else:
        names = token_ops.plan_names([len(g) for g in groups], tokens)

    default_nodes = set(cmds.ls(defaultNodes=True) or [])
    occupancy = {}      # 부모 롱 경로('' = 월드) -> 그 아래 지금 쓰이는 짧은 이름(네임스페이스 포함)

    def _names_under(parent):
        if parent not in occupancy:
            if parent:
                children = cmds.listRelatives(parent, children=True, fullPath=True) or []
            else:
                children = cmds.ls(assemblies=True, long=True) or []
            occupancy[parent] = set(c.split("|")[-1] for c in children)
        return occupancy[parent]

    rows = []
    for group_index, (group, group_names) in enumerate(zip(groups, names)):
        for node_index, (path, leaf) in enumerate(zip(group, group_names)):
            parent = path.rpartition("|")[0]
            old_name = short_name_with_namespace(path)
            namespace, _old_leaf = split_namespace(old_name)
            new_name = join_namespace(namespace, leaf) if leaf else ""
            row = {"path": path, "parent": parent, "old_name": old_name, "new_name": new_name,
                   "status": "", "note": "", "group": group_index, "root": node_index == 0}
            rows.append(row)

            if errors:
                row["status"] = ST_TOKEN
                row["note"] = errors[0]
                continue
            if not cmds.objExists(path):
                row["status"] = ST_GONE
                row["note"] = "node no longer exists"
                continue
            short = (cmds.ls(path) or [path])[0]
            if short in default_nodes or path in default_nodes:
                row["status"] = ST_DEFAULT_NODE
                row["note"] = "Maya refuses to rename its default nodes"
                continue
            if cmds.referenceQuery(path, isNodeReferenced=True):
                row["status"] = ST_REFERENCED
                row["note"] = "referenced nodes cannot be renamed"
                continue
            if (cmds.lockNode(path, q=True, lock=True) or [False])[0]:
                row["status"] = ST_LOCKED
                row["note"] = "unlock the node first"
                continue
            problem = invalid_characters(leaf)
            if problem:
                row["status"] = ST_INVALID
                row["note"] = problem
                continue

            # 부모 경로는 아직 옛 이름 기준이다 - 부모 행도 같은 occupancy 키(옛 경로)를 쓰므로 맞물린다.
            taken = _names_under(parent)
            taken.discard(old_name)
            if new_name == old_name:
                row["status"] = ST_SAME
                row["note"] = "already this name"
            elif new_name in taken:
                row["status"] = ST_COLLISION
                row["note"] = "Maya will append a number"
            else:
                row["status"] = ST_OK
            taken.add(new_name)

    return rows, errors


def short_name_with_namespace(path):
    """DAG 경로만 떼고 네임스페이스는 남긴다. 'a|ns:b' -> 'ns:b'."""
    return path.split("|")[-1]


# ================================================================
# Tab 2 : Copy Name  (JUN_cmd_copyName 이식)
# ================================================================

def copy_name(base_items, target_items, prefix,
              set_suffix=DEFAULT_SET_COPY_SUFFIX,
              search="", replace="", case_sensitive=True):
    """base 리스트의 이름(prefix 부착)을 target 리스트에 순서대로 적용(rename).

    v01.05 : `search` 가 있으면 **Base 의 leaf 이름** 안의 `search` 를 `replace` 로 바꾼 뒤
    복사한다(예: Base `L_arm_jnt`, Search `jnt`, Replace `ctrl` -> Target `L_arm_ctrl`).
    치환은 Base 이름에만 걸리고 prefix / set suffix 는 그 뒤에 붙는다. 규칙은 Set Rename 탭과
    같은 `replace_in_name`(글자 그대로, 전부 치환, 대소문자 옵션)이다.

    **세트도 대상이 된다.** 다만 세트는 DG 노드라 **같은 이름을 그대로 못 쓴다** — 트랜스폼과
    같은 이름을 주면 마야가 **조용히 `name1` 로 바꾼다**(실측). 그래서 대상이 세트면
    `set_suffix`(기본 `_copy`)를 뒤에 붙인다. 빈 문자열을 주면 안 붙이고, 그때 충돌이 나면
    실제로 붙은 이름을 notes 로 알린다.

    (DAG 노드는 부모가 다르면 같은 이름을 가질 수 있어 이 문제가 없다 — 실측:
    `|g1|c` 와 `|g2|c` 가 공존한다.)

    반환: `(new_names, warning, notes)`
        warning : 개수 불일치 안내(없으면 None)
        notes   : 항목별 경고 목록(충돌로 이름이 바뀌었다 / 노드가 사라졌다 등)
    """
    cmds = _cmds()
    if cmds is None:
        return [], "Maya not available.", []

    warning = None
    notes = []
    count = min(len(base_items), len(target_items))
    if len(base_items) != len(target_items):
        warning = ("Base({0}) and Targets({1}) counts differ; "
                   "renaming first {2} item(s).").format(
            len(base_items), len(target_items), count)

    suffix = set_suffix or ""

    # 동일 이름 대비: target 을 먼저 UUID 로 잡아두고 rename 한다.
    plan = []
    for i in range(count):
        target = target_items[i]
        base_leaf = replace_in_name(
            short_name(base_items[i]), search, replace, case_sensitive)
        new_leaf = prefix + base_leaf
        if is_set_node(target):
            new_leaf += suffix
        # **네임스페이스를 보존한다** - 짧은 이름만 주면 노드가 루트 네임스페이스로
        # 옮겨간다(실측: 세트도 트랜스폼도 마찬가지다).
        namespace, _leaf = split_namespace(target)
        plan.append((_to_uuid(target), namespace, new_leaf, target))

    new_names = []
    for uuid, namespace, new_leaf, original in plan:
        if not new_leaf:
            # Search 가 Base 이름 전체를 지웠다 - 빈 이름으로는 rename 할 수 없다
            notes.append("[Warning] {0}: skipped - the new name would be empty.".format(
                original))
            continue
        want = join_namespace(namespace, new_leaf)
        new_name = _rename_by_uuid(uuid, want)
        if new_name is None:
            notes.append("[Warning] {0}: node no longer exists.".format(original))
            continue
        new_names.append(new_name)
        if short_name(new_name) != new_leaf:
            # 이름이 겹쳐 마야가 번호를 붙였거나, 잘못된 문자를 고쳤다
            notes.append(
                "[Warning] {0} -> {1} (asked for '{2}' - Maya changed it).".format(
                    original, new_name, new_leaf))

    return new_names, warning, notes


# ================================================================
# Tab 3 : Quick Rename  (ref_01.mel 이식, 현재 선택 기준)
# ================================================================

def _selection_uuids():
    """현재 선택을 UUID 목록으로. 계층을 rename 해도 핸들이 유지되도록."""
    cmds = _cmds()
    if cmds is None:
        return []
    return cmds.ls(sl=True, uuid=True) or []


def insert_front(text):
    """선택 오브젝트 이름 앞에 text 를 붙인다. (insertapply 이식) 반환: 처리 개수."""
    cmds = _cmds()
    if cmds is None:
        return 0
    count = 0
    for uuid in _selection_uuids():
        paths = cmds.ls(uuid, long=True) or []
        if not paths:
            continue
        cmds.rename(paths[0], text + short_name(paths[0]))
        count += 1
    return count


def add_rear(text):
    """선택 오브젝트 이름 뒤에 text 를 붙인다. (addapply 이식) 반환: 처리 개수."""
    cmds = _cmds()
    if cmds is None:
        return 0
    count = 0
    for uuid in _selection_uuids():
        paths = cmds.ls(uuid, long=True) or []
        if not paths:
            continue
        cmds.rename(paths[0], short_name(paths[0]) + text)
        count += 1
    return count


def change_new(new_name, start_index_text):
    """선택 오브젝트를 new_name(+증가 인덱스)으로 rename. (newapply 이식)

    - start_index_text 가 빈 문자열:
        선택 2개 이상 → new_name + 01,02,...  / 1개 → new_name (번호 없음)
    - start_index_text 가 숫자:
        new_name + index, index+1, ...  (10 미만은 0 패딩)
    반환: (count, error) — new_name 이 비면 error 문자열 반환.
    """
    cmds = _cmds()
    if cmds is None:
        return 0, "Maya not available."
    if not new_name.strip():
        return 0, "Enter a new name. (Change New is empty)"

    selection = _selection_uuids()
    count = 0

    def _suffix(counter):
        return ("0" + str(counter)) if counter < 10 else str(counter)

    def _rename(uuid, name):
        return _rename_by_uuid(uuid, name) is not None

    if start_index_text.strip() == "":
        if len(selection) > 1:
            counter = 1
            for uuid in selection:
                if _rename(uuid, new_name + _suffix(counter)):
                    count += 1
                counter += 1
        else:
            for uuid in selection:
                if _rename(uuid, new_name):
                    count += 1
    else:
        counter = int(start_index_text)
        for uuid in selection:
            if _rename(uuid, new_name + _suffix(counter)):
                count += 1
            counter += 1

    return count, None


def trim_front():
    """선택 오브젝트 이름의 첫 글자를 제거. (Front_m 이식) 반환: 처리 개수."""
    cmds = _cmds()
    if cmds is None:
        return 0
    count = 0
    for uuid in _selection_uuids():
        paths = cmds.ls(uuid, long=True) or []
        if not paths:
            continue
        leaf = short_name(paths[0])
        if len(leaf) <= 1:
            continue
        cmds.rename(paths[0], leaf[1:])
        count += 1
    return count


def trim_rear():
    """선택 오브젝트 이름의 마지막 글자를 제거. (Rear_m 이식) 반환: 처리 개수."""
    cmds = _cmds()
    if cmds is None:
        return 0
    count = 0
    for uuid in _selection_uuids():
        paths = cmds.ls(uuid, long=True) or []
        if not paths:
            continue
        leaf = short_name(paths[0])
        if len(leaf) <= 1:
            continue
        cmds.rename(paths[0], leaf[:-1])
        count += 1
    return count


def all_apply(new_name, start_index_text, insert_text, add_text):
    """allaplly 이식: Change New → Front Insert → Last Add 순서로 적용."""
    messages = []
    count, error = change_new(new_name, start_index_text)
    if error:
        messages.append("[New] " + error)
    else:
        messages.append("[New] {0} renamed.".format(count))
    messages.append("[Insert] {0} renamed.".format(insert_front(insert_text)))
    messages.append("[Add] {0} renamed.".format(add_rear(add_text)))
    return messages
