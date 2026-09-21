# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
# A00470_MaterialTool - 진단이 제안한 이름으로 머티리얼을 **실제로 바꾼다**.
#
# `maya_materials` 는 씬을 읽기만 하는 모듈이라, 씬을 바꾸는 일은 여기에 둔다.
#
# ── 제안 이름을 그대로 쓸 수 없는 경우가 있다 ★ ──────────────────────────
# `NameProfile._suggest()` 는 **고칠 값을 모르는 자리**를 `{character}` 처럼 남긴다.
# 예: `MT_MANU_CH_Set002_Top` 은 캐릭터 토큰이 통째로 빠진 이름이라 제안이
# `MT_MANU_CH_{character}_Set002_Top` 이 된다. 이걸 그대로 노드 이름으로 쓰면
# **중괄호가 박힌 이름**이 씬에 남는다(마야는 `{}` 를 지우고 붙여 버려 더 나쁘다).
# 그래서 자리표시가 하나라도 있으면 **건너뛰고 무엇을 채워야 하는지 알린다.**
#
# ── 이름을 바꾸기 전에 보는 것들 ─────────────────────────────────────────
#   - 참조(reference)된 노드      : 마야가 못 바꾼다
#   - 기본 노드 · 잠긴 노드        : `lambert1` 같은 기본 머티리얼이다. ★ 기본 노드는
#                                   `ls -readOnly` 로는 **안 잡힌다**(실측) —
#                                   `ls -defaultNodes` 로 본다
#   - 그 이름을 **이미 쓰는 노드** : 마야는 조용히 `name1` 로 바꿔 버리므로, 그렇게
#                                   두지 않고 건너뛰고 알린다
#
# ── 네임스페이스 ★ ──────────────────────────────────────────────────────
# `CHAR:MT_...` 를 `cmds.rename(node, "MT_...")` 처럼 **짧은 이름**으로 바꾸면 노드가
# 네임스페이스 밖으로 빠진다(실측). 원래 네임스페이스를 새 이름에 다시 붙여 준다.

import re

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


#: 제안 이름에 남은 "값을 모르는 자리" — `{character}` 꼴.
PLACEHOLDER_RE = re.compile(r"\{[^}]*\}")


def placeholders(name):
    """제안 이름에 남은 자리표시들. 없으면 빈 목록."""
    return PLACEHOLDER_RE.findall(name or "")


def _namespace_of(node):
    """`CHAR:MT_x` -> `CHAR:` / 네임스페이스가 없으면 빈 문자열."""
    short = (node or "").split("|")[-1]
    return short.rsplit(":", 1)[0] + ":" if ":" in short else ""


def _short(node):
    return (node or "").split("|")[-1].split(":")[-1]


def plan(materials, reports):
    """무엇을 무엇으로 바꿀지 정한다. **씬은 건드리지 않는다.**

    `materials` : 진단한 머티리얼 이름들(리스트업된 순서 그대로)
    `reports`   : {이름: NameReport}

    반환 `(renames, skipped)`
      renames : [(현재 이름, 새 이름)]
      skipped : [(현재 이름, 사유)]
    """
    renames = []
    skipped = []
    taken = {}              # 새 이름 -> 그 이름을 먼저 차지한 머티리얼

    for material in materials or []:
        report = reports.get(material)

        if report is None:
            skipped.append((material, "not checked yet"))
            continue

        if report.ok:
            skipped.append((material, "already follows the rule"))
            continue

        suggestion = (report.suggested_name or "").strip()
        if not suggestion:
            skipped.append((material, "no suggested name"))
            continue

        holes = placeholders(suggestion)
        if holes:
            # 무엇을 채워야 하는지 그대로 보여 준다 - 사람이 정해야 하는 값이다.
            skipped.append((material, "the suggestion still needs {0} : {1}".format(
                ", ".join(holes), suggestion)))
            continue

        if suggestion == _short(material):
            skipped.append((material, "already the suggested name"))
            continue

        if suggestion in taken:
            skipped.append((material, "'{0}' is already taken by {1}".format(
                suggestion, _short(taken[suggestion]))))
            continue

        taken[suggestion] = material
        renames.append((material, suggestion))

    return renames, skipped


def _blocked(node):
    """이름을 못 바꾸는 이유. 바꿀 수 있으면 None."""
    if not cmds.objExists(node):
        return "not in the scene anymore"

    try:
        if cmds.referenceQuery(node, isNodeReferenced=True):
            return "referenced"
    except Exception:
        pass

    # 기본 머티리얼(`lambert1` · `standardSurface1` …)은 마야가 이름을 못 바꾸게 한다.
    # ★ `cmds.ls(node, readOnly=True)` 로는 **안 잡힌다**(실측 - 빈 목록이 온다).
    #   `ls -defaultNodes` 에 들어 있는지로 본다.
    try:
        if node in (cmds.ls(defaultNodes=True) or []):
            return "a Maya default node"
    except Exception:
        pass

    try:
        if cmds.lockNode(node, query=True, lock=True)[0]:
            return "locked"
    except Exception:
        pass

    return None


def apply(renames):
    """`plan()` 이 돌려준 목록대로 이름을 바꾼다. **undo 한 스텝.**

    반환 `(done, failed)`
      done   : [(옛 이름, 새 이름)] — 되읽어 확인한 실제 이름이다
      failed : [(이름, 사유)]
    """
    done = []
    failed = []

    if not renames:
        return done, failed

    with undo_chunk():
        for node, wanted in renames:

            reason = _blocked(node)
            if reason:
                failed.append((node, reason))
                continue

            # 네임스페이스는 지킨다 (짧은 이름으로 바꾸면 밖으로 빠진다).
            target = _namespace_of(node) + wanted

            if cmds.objExists(target):
                failed.append((node, "'{0}' already exists in the scene".format(target)))
                continue

            try:
                result = cmds.rename(node, target)
            except Exception as e:
                # 마야 에러 문자열은 끝에 줄바꿈이 붙어 로그가 벌어진다.
                failed.append((node, "rename failed : {0}".format(
                    " ".join(str(e).split()))))
                continue

            # 되읽어 확인한다 - 마야는 이름이 겹치거나 못 쓰는 글자가 있으면 **조용히**
            # 다른 이름을 붙인다.
            if _short(result) != wanted:
                failed.append((node, "Maya named it '{0}' instead of '{1}'".format(
                    _short(result), wanted)))
                continue

            done.append((node, result))

    return done, failed
