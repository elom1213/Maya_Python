# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-30
# A00330_NamingTool - core logic (maya.cmds)
#
# 레거시 두 소스의 네이밍 로직을 순수 함수로 이식한다.
#   - JUN_PY_NamingTool_V03_04.py : Naming Dynamics(계층 토큰), Copy Name
#   - ref/ref_01.mel              : Quick Rename(Front Insert / Change New / Last Add / -1 trim)
# UI 는 이 함수들만 호출한다(thin UI). Maya 밖에서도 import 가능하도록 cmds 는 lazy.

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

def build_hierarchy_groups(objects):
    """각 루트 오브젝트마다 [root, 자손...] 리스트를 만든다.

    원본 규칙 그대로:
      - allDescendents 를 모으되, 루트가 transform 이면 자손 중 transform 만 남긴다
        (shape 노드 제외).
      - [자손...] + [root] 후 reverse → [root, 얕은자손 ... 깊은자손] 순서.
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


# ================================================================
# Tab 2 : Copy Name  (JUN_cmd_copyName 이식)
# ================================================================

def copy_name(base_items, target_items, prefix):
    """base 리스트의 이름(prefix 부착)을 target 리스트에 순서대로 적용(rename).

    반환: (new_names, warning) — warning 은 개수 불일치 시 안내 문자열(없으면 None).
    """
    cmds = _cmds()
    if cmds is None:
        return [], "Maya not available."

    warning = None
    count = min(len(base_items), len(target_items))
    if len(base_items) != len(target_items):
        warning = ("Base({0}) and Targets({1}) counts differ; "
                   "renaming first {2} item(s).").format(
            len(base_items), len(target_items), count)

    # 동일 이름 대비: target 을 먼저 UUID 로 잡아두고 rename 한다.
    plan = [(_to_uuid(target_items[i]), prefix + short_name(base_items[i]))
            for i in range(count)]

    new_names = []
    for uuid, new_base in plan:
        new_name = _rename_by_uuid(uuid, new_base)
        if new_name is not None:
            new_names.append(new_name)

    return new_names, warning


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
