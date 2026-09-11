# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-11
# A00290_BSTool - Edit BS > Naming 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# blendShape 타겟의 **이름**을 바꾼다. 여기서 말하는 이름은 타겟 메시의 노드 이름이 아니라
# **weight 어트리뷰트의 별칭(alias)** 이다 — 채널박스와 Shape Editor 가 보여 주는 그 이름.
#
# ## 왜 별칭이 곧 언리얼의 모프 타겟 이름인가
#
# Maya 2024 + FBX 2020.3.4 로 실측한 결과, FBX 에 나가는 이름은 **전부 별칭**이다:
#
#     Geometry: ..., "Geometry::RenamedPose_A", "Shape"
#     Deformer: ..., "SubDeformer::myBS.RenamedPose_A", "BlendShapeChannel"
#
# 타겟 메시 노드 이름(`meshA_ugly_name`)은 **어디에도 안 나간다** — 타겟 메시를 지운
# 구운(baked) 상태든, 라이브로 연결된 상태든 같다. 언리얼은 이 BlendShapeChannel 이름에서
# `<blendShape 노드>.` 접두사를 떼고 모프 타겟 이름으로 쓴다. 그래서 **별칭만 바꾸면**
# 다시 익스포트한 FBX 가 바뀐 이름으로 임포트된다.
#
# ## 마야 기본 기능
#
# 하나씩이면 마야에도 있다 — **Shape Editor 에서 타겟 이름을 더블클릭**하면 그 자리에서
# 고쳐지고, 그게 곧 `cmds.aliasAttr("새이름", "bs.weight[i]")` 다. 이 모듈이 하는 일은
# **여러 개를 규칙으로 한 번에** 바꾸고, 바꾸기 전에 결과를 보여 주고, 마야가 조용히
# 거절하는 경우들을 미리 걸러 내는 것이다.
#
# ## 실측으로 드러난 함정 (mayapy 2024)
#
# - **같은 이름으로 다시 rename 하면 에러다.** `aliasAttr` 은 "이미 그 이름의 어트리뷰트가
#   있다" 며 `RuntimeError` 를 던진다. 안 바뀌는 타겟은 **호출 자체를 건너뛰어야** 한다.
# - **이름 맞바꾸기(A<->B)는 한 번에 안 된다.** 같은 이유로 중간에 임시 이름을 거쳐야 한다.
#   그래서 이 모듈은 바뀌는 타겟 전부를 **임시 이름 -> 최종 이름 2단계**로 넘긴다.
# - **허용 문자가 좁다.** 공백 · `.` · `[` `]` · 숫자로 시작 · 한글(비 ASCII)은 전부 거절되고,
#   마야는 `Warning` 을 찍은 뒤 `RuntimeError` 를 낸다. `-` 는 마야가 받아 주지만 표현식에서
#   뺄셈으로 읽히므로 이 모듈은 막는다.
# - **별칭은 blendShape 노드 안에서만 유일하면 된다.** 다른 노드와 겹쳐도 상관없지만,
#   같은 노드의 **실제 어트리뷰트 이름**(`envelope`, `weight`, `en` …)과는 겹칠 수 없다.
# - 값 · 키/연결 · lock 은 **그대로 살아 있다**(연결은 별칭이 아니라 실제 plug 에 붙어 있다).
#   드라이브하던 애님 커브의 **노드 이름**(`myBS_poseB`)은 안 따라 바뀐다 — 이름일 뿐 문제없다.
# - `aliasAttr` 은 undo 된다. 호출부가 undo_chunk 로 묶으면 **Ctrl+Z 한 번**에 전부 돌아온다.

import re

import maya.cmds as cmds

from . import blendshape_utils as bsu
from . import target_order_manager as tom


# 마야가 별칭으로 받아 주는 것 중 **안전한 것만** 남긴 규칙.
# (마야는 `-` 도 받지만 `bs.a-b` 가 표현식에서 뺄셈으로 읽혀 문제를 만든다)
VALID_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 2단계 rename 의 임시 별칭 접두사. 숫자로 시작하지 않는다.
TEMP_PREFIX = "JUNbsnTmp"

# 이름 짓기 모드
MODE_SET = "set"
MODE_REPLACE = "replace"
MODE_AFFIX = "affix"


# =========================
# 조회
# =========================

def list_targets(bs_node):
    """[(weight 인덱스, 타겟 이름), ...] 를 인덱스 오름차순으로."""
    return tom.list_targets(bs_node)


def target_names(bs_node):
    return tom.target_names(bs_node)


def weight_plug(bs_node, index):
    return "{0}.weight[{1}]".format(bs_node, index)


def validate_name(name):
    """별칭으로 쓸 수 있는 이름인지. 문제가 없으면 "" 를, 있으면 그 이유를 반환."""
    if name is None or not name.strip():
        return "empty name"
    if name != name.strip():
        return "leading/trailing space"
    try:
        name.encode("ascii")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return "non-ASCII characters"
    if not VALID_NAME_RE.match(name):
        if name[0].isdigit():
            return "starts with a digit"
        return "only letters, digits and _ are allowed (and not as the first character)"
    return ""


def name_is_taken(bs_node, name):
    """그 이름이 이미 이 blendShape 의 어트리뷰트(별칭 포함)로 있는가."""
    return cmds.objExists("{0}.{1}".format(bs_node, name))


# =========================
# 이름 짓기 (마야 비의존 - 순수 문자열)
# =========================

def _numbered(base, number, pad):
    return "{0}{1:0{2}d}".format(base, number, pad)


def build_names(names, mode, options=None):
    """현재 이름 목록에 규칙을 적용해 **새 이름 목록**을 만든다(길이 동일).

    mode:
      MODE_SET      : name(문자열)로 통째로 교체. `#` 은 번호로 바뀐다(`##` = 2자리).
                      `#` 이 없는데 대상이 둘 이상이면 `_01`, `_02` … 를 뒤에 붙인다
                      (그대로 두면 전부 같은 이름이 되어 어차피 마야가 거절한다).
                      번호는 `#` 이든 자동 접미사든 `start` 부터 리스트 순서대로 센다.
      MODE_REPLACE  : search -> replace 치환. match_case=False 면 대소문자 무시.
      MODE_AFFIX    : prefix + 이름 + suffix.
    """
    options = options or {}
    result = []

    if mode == MODE_SET:
        base = options.get("name", "")
        start = int(options.get("start", 1))
        hashes = re.search(r"#+", base)
        auto = (hashes is None and len(names) > 1)
        for i, _old in enumerate(names):
            number = start + i
            if hashes:
                new = base[:hashes.start()] + _numbered(
                    "", number, len(hashes.group(0))) + base[hashes.end():]
            elif auto:
                new = base + "_" + _numbered("", number, 2)
            else:
                new = base
            result.append(new)
        return result

    if mode == MODE_REPLACE:
        search = options.get("search", "")
        replace = options.get("replace", "")
        match_case = bool(options.get("match_case", True))
        if not search:
            return list(names)
        if match_case:
            return [old.replace(search, replace) for old in names]
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        # 치환 문자열은 **그대로** 넣는다 - 람다를 쓰지 않으면 `\1` 같은 글자가
        # 역참조로 해석되어 사용자가 친 이름과 다른 결과가 나온다.
        return [pattern.sub(lambda _m, r=replace: r, old) for old in names]

    if mode == MODE_AFFIX:
        prefix = options.get("prefix", "")
        suffix = options.get("suffix", "")
        return [prefix + old + suffix for old in names]

    raise ValueError("Unknown naming mode '{0}'.".format(mode))


# =========================
# 계획 (미리보기 + 검사)
# =========================

def plan_renames(bs_node, pairs):
    """[(현재 이름, 새 이름), ...] 을 검사해 미리보기 행 목록으로.

    각 행: {"index", "old", "new", "changed", "error"}
      - changed=False : 이름이 그대로다(마야는 같은 이름 rename 을 거절하므로 건너뛴다).
      - error != ""   : 그대로 적용하면 실패한다. 무엇이 문제인지 한 줄로 담는다.

    검사는 **바뀌는 이름들을 한꺼번에** 본다. A->B 와 B->A 처럼 서로 자리를 바꾸는 것은
    통과시키고(임시 이름을 거쳐 적용된다), 아직 아무도 안 비켜 준 이름과 부딪히는 것만
    잡아낸다.
    """
    if not bsu.is_blendshape(bs_node):
        raise RuntimeError("'{0}' is not a valid blendShape node.".format(bs_node))

    index_map = bsu.target_index_map(bs_node)
    rows = []

    # 이 작업으로 **비워지는** 이름들 - 이 이름과 부딪히는 건 충돌이 아니다.
    freed = set(old for old, new in pairs if old != new and old in index_map)
    seen = {}

    for old, new in pairs:
        row = {"index": index_map.get(old, -1), "old": old, "new": new,
               "changed": old != new, "error": ""}

        if row["index"] == -1:
            row["error"] = "no such target on the node"
        elif not row["changed"]:
            pass
        else:
            reason = validate_name(new)
            if reason:
                row["error"] = reason
            elif new in seen:
                row["error"] = "same new name as '{0}'".format(seen[new])
            elif new not in freed and name_is_taken(bs_node, new):
                row["error"] = "the node already has an attribute named '{0}'".format(new)

        if row["changed"] and not row["error"]:
            seen[new] = old
        rows.append(row)

    return rows


def plan_errors(rows):
    return [r for r in rows if r["error"]]


def plan_changes(rows):
    return [r for r in rows if r["changed"] and not r["error"]]


# =========================
# 적용
# =========================

def _temp_name(bs_node, index):
    """그 노드에서 비어 있는 임시 별칭."""
    name = "{0}{1}".format(TEMP_PREFIX, index)
    while name_is_taken(bs_node, name):
        name += "_"
    return name


def _assign(bs_node, assignments):
    """[(인덱스, 최종 이름), ...] 를 **임시 이름을 거쳐** 2단계로 준다.

    맞바꾸기(A<->B)와 돌려쓰기(A->B->C->A)를 그대로 지나가게 하는 것이 목적이다.
    `aliasAttr` 은 이미 있는 이름을 거절하므로, 먼저 전부 임시 이름으로 비켜 놓는다.
    """
    for index, _final in assignments:
        cmds.aliasAttr(_temp_name(bs_node, index), weight_plug(bs_node, index))
    for index, final in assignments:
        cmds.aliasAttr(final, weight_plug(bs_node, index))


def live_target_meshes(bs_node, index):
    """그 타겟에 **라이브로 연결된** 타겟 메시 transform 목록(구운 타겟이면 빈 목록)."""
    found = []
    for base in tom.base_indices(bs_node):
        itg = "{0}.inputTarget[{1}].inputTargetGroup[{2}]".format(bs_node, base, index)
        items = cmds.getAttr(itg + ".inputTargetItem", multiIndices=True) or []
        for k in items:
            plug = "{0}.inputTargetItem[{1}].inputGeomTarget".format(itg, k)
            for shape in cmds.listConnections(plug, source=True, destination=False,
                                              shapes=True) or []:
                parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
                node = parents[0] if parents else shape
                if node not in found:
                    found.append(node)
    return found


def apply_renames(bs_node, rows, rename_meshes=False):
    """검사를 통과한 행들을 실제로 적용한다.

    호출부에서 `undo_chunk()` 로 감싸면 **Ctrl+Z 한 번**에 전부 되돌아온다.
    중간에 실패하면 이미 바꾼 것까지 **원래 이름으로 되돌린 뒤** 예외를 올린다.

    반환: {"renamed": n, "meshes": [(old_mesh, new_mesh), ...], "skipped_meshes": [...]}
    """
    errors = plan_errors(rows)
    if errors:
        first = errors[0]
        raise RuntimeError("'{0}' -> '{1}' : {2}".format(
            first["old"], first["new"], first["error"]))

    changes = plan_changes(rows)
    if not changes:
        return {"renamed": 0, "meshes": [], "skipped_meshes": []}

    # 메시 이름은 별칭을 바꾸기 **전에** 찾아 둔다(찾는 길은 인덱스라 순서와 무관하지만,
    # 실패 시 되돌리는 경로를 단순하게 두기 위해 조회와 변경을 분리한다).
    mesh_jobs = []
    skipped = []
    if rename_meshes:
        for row in changes:
            meshes = live_target_meshes(bs_node, row["index"])
            if len(meshes) == 1:
                mesh_jobs.append((meshes[0], row["new"]))
            elif meshes:
                # 베이스 지오메트리가 여럿이면 한 타겟에 메시도 여럿이다. 전부 같은
                # 이름으로 바꿀 수는 없으니 손대지 않고 알린다.
                skipped.append((row["new"], len(meshes)))

    olds = [(row["index"], row["old"]) for row in changes]
    try:
        _assign(bs_node, [(row["index"], row["new"]) for row in changes])
    except Exception:
        # 절반만 바뀐 상태를 남기지 않는다. 되돌리기도 2단계라 맞바꾸기 상태에서도 안전하다.
        try:
            _assign(bs_node, olds)
        except Exception:
            pass
        raise

    renamed_meshes = []
    for mesh, new_name in mesh_jobs:
        if not cmds.objExists(mesh):
            continue
        short = mesh.split("|")[-1]
        if short == new_name:
            continue
        actual = cmds.rename(mesh, new_name)
        renamed_meshes.append((short, actual.split("|")[-1]))

    return {"renamed": len(changes), "meshes": renamed_meshes,
            "skipped_meshes": skipped}
