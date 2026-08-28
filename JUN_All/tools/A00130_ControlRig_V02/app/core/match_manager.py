# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - Match : 케이지 세트의 원소를 짝인 템플릿 조인트에 맞춘다.
#
# 계획서 Phase 1 (최소 기능).
#
# ── V01 과 무엇이 다른가 ────────────────────────────────────────────────────
#
# V01 은 매칭할 때마다 **임시 조인트 체인을 만들고 orient 를 다시 잡은 뒤 지웠고**,
# 대상을 사용자가 TSL 에 **손으로 순서대로** 담아야 했다. V02 는 그 자리를 템플릿
# 조인트가 대신한다 — 순서를 사람이 관리하지 않고 **매핑 표가 갖는다**.
#
# 또 V01 의 `MayaScene.match_transforms` 는 팔로워의 `rotateOrder` 를 타깃 것으로
# 잠깐 바꿨다가 되돌리는데, **`xform -rotateOrder` 는 방향을 보존하지 않는다**(실측:
# `rotate 30/40/50` 인 노드의 rotateOrder 만 바꾸면 월드 회전이 달라진다). 그래서
# 여기서는 그 방식을 쓰지 않고 마야 내장 **`matchTransform`** 을 쓴다 —
# rotateOrder · rotateAxis · 피벗을 마야가 알아서 처리한다.
#
# ── 실패를 삼키지 않는다 ────────────────────────────────────────────────────
#
# V01 은 `except Exception: print(...)` 로 실패를 삼켰다. 여기서는 건너뛴 것과 실패한
# 것을 **세어서** 돌려준다. 특히 `matchTransform` 은 **잠긴 채널을 조용히 건너뛰므로**
# (실측) 쓰기 전에 미리 보고, 막혀 있으면 **반쯤 옮기지 않고** 통째로 건너뛴다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import scene_utils as su


#: 결과 코드
ST_OK = "ok"
ST_NO_JOINT = "joint missing"
ST_NO_SET = "set missing"
ST_EMPTY = "no member"
ST_BLOCKED = "blocked"
ST_ERROR = "error"


def plan(joints, namespace):
    """씬을 건드리지 않고 "무엇을 어디에 맞출지" 만 계산한다.

    돌려주는 것: 행 목록. 각 행은
        joint · set · match · members · skipped_sets · status · note
    """
    rows = []

    for entry in joints:
        if not entry["targets"]:
            continue        # 배치·계층용 조인트 - 매칭 대상이 없다

        # 조인트도 세트와 **똑같이** 네임스페이스로 푼다. 케이지 파일 안에 템플릿
        # 조인트가 함께 들어 있으면 레퍼런스에서 `CAGE:helper_*` 로 오기 때문이다
        # (su.resolve 의 주석 참고).
        joint, joint_found = su.resolve(entry["name"], namespace)

        for target in entry["targets"]:
            set_node, set_found = su.resolve(target["set"], namespace)
            row = {
                "joint": joint or entry["name"],
                "joint_wanted": entry["name"],
                "set": set_node or su.qualify(target["set"], namespace),
                "set_wanted": target["set"],
                "match": tuple(target["match"]),
                "members": [],
                "skipped_sets": [],
                "status": ST_OK,
                "note": "",
            }

            if not joint:
                # 계획서 1-12 - 없으면 로그만 남기고 다음 매칭으로 간다
                row["status"] = ST_NO_JOINT
                row["note"] = "looked for " + " and ".join(
                    su.candidates(entry["name"], namespace))
                rows.append(row)
                continue

            if not set_node:
                row["status"] = ST_NO_SET
                row["note"] = "looked for " + " and ".join(
                    su.candidates(target["set"], namespace))
                rows.append(row)
                continue

            if len(joint_found) > 1:
                row["note"] = "ambiguous joint - using {0} (also found {1})".format(
                    joint, ", ".join(joint_found[1:]))
            elif len(set_found) > 1:
                row["note"] = "ambiguous set - using {0} (also found {1})".format(
                    set_node, ", ".join(set_found[1:]))

            members, skipped = su.resolve_members(set_node)
            row["members"] = members
            row["skipped_sets"] = skipped

            if not members:
                row["status"] = ST_EMPTY
                if skipped:
                    row["note"] = "only sub-sets inside, and those are ignored"
            rows.append(row)

    return rows


def apply(rows):
    """계산된 행대로 실제로 맞춘다. `(results, messages)`.

    전체가 **undo 한 스텝**이다.
    """
    messages = []
    results = {"matched": 0, "joints": 0, "skipped_members": 0}
    seen_joints = set()

    with undo_chunk():
        for row in rows:
            if row["status"] in (ST_NO_JOINT, ST_NO_SET):
                messages.append("[Warning] {0} <- {1} : {2} ({3}).".format(
                    row["joint"], row["set"], row["status"], row["note"]))
                continue

            if row["skipped_sets"]:
                messages.append("[Info] {0}: {1} sub-set(s) ignored - {2}.".format(
                    row["set"], len(row["skipped_sets"]),
                    ", ".join(su.short_name(s) for s in row["skipped_sets"])))

            if not row["members"]:
                messages.append("[Warning] {0} <- {1} : no member to match{2}.".format(
                    row["joint"], row["set"],
                    " ({0})".format(row["note"]) if row["note"] else ""))
                continue

            want_t = "t" in row["match"]
            want_r = "r" in row["match"]

            for member in row["members"]:
                if not cmds.objExists(member):
                    results["skipped_members"] += 1
                    messages.append("[Warning] {0}: member '{1}' is gone.".format(
                        row["set"], member))
                    continue

                blocked = su.blocked_channels(member, translate=want_t, rotate=want_r)
                if blocked:
                    # 반쯤 옮겨진 상태가 제일 나쁘다 - 통째로 건너뛴다
                    results["skipped_members"] += 1
                    messages.append(
                        "[Warning] {0}: '{1}' skipped - locked or driven ({2}).".format(
                            row["set"], su.short_name(member), ", ".join(blocked)))
                    continue

                try:
                    cmds.matchTransform(member, row["joint"],
                                        position=want_t, rotation=want_r, scale=False)
                except Exception as e:
                    results["skipped_members"] += 1
                    messages.append("[ERR] {0} <- {1} : {2}".format(
                        su.short_name(member), row["joint"], e))
                    continue

                results["matched"] += 1

            seen_joints.add(row["joint"])
            mode = "position only" if not want_r else "position + rotation"
            messages.append("[OK] {0} <- {1} : {2} member(s), {3}.".format(
                row["joint"], su.short_name(row["set"]), len(row["members"]), mode))

    results["joints"] = len(seen_joints)
    messages.append("[OK] Match done - {0} object(s) on {1} joint(s), {2} skipped.".format(
        results["matched"], results["joints"], results["skipped_members"]))
    return results, messages


def summarize(rows):
    """상태별 개수 (UI 요약용)."""
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


# =========================
# 템플릿 조인트 생성 (매핑 표의 계층 그대로)
# =========================

def create_template(joints, namespace=None):
    """매핑 표의 계층대로 템플릿 조인트를 만든다. `(created, messages)`.

    **위치는 잡아 주지 않는다** — 계획서 1-3 대로 배치는 사람이 손으로 한다.
    여기서 만드는 것은 **이름과 부모 관계**뿐이다(원점에 쌓인다).

    **이미 있으면 안 만든다** — 네임스페이스를 붙인 쪽도 함께 본다. 케이지 파일에
    템플릿 조인트가 들어 있는 경우(레퍼런스면 `CAGE:helper_*`) **똑같은 조인트를
    로컬에 하나 더 만들어 버리는 것**을 막는다.
    """
    messages = []
    created = []

    with undo_chunk():
        for entry in joints:
            name = entry["name"]
            existing, _ = su.resolve(name, namespace)
            if existing:
                continue
            cmds.select(clear=True)
            made = cmds.joint(name=name, position=(0, 0, 0))
            created.append(made)

        # 부모는 전부 만든 뒤에 건다 (표의 순서와 무관하게 안전하도록)
        for entry in joints:
            node, _ = su.resolve(entry["name"], namespace)
            if entry["parent"]:
                parent_node, _ = su.resolve(entry["parent"], namespace)
            else:
                parent_node = None
            if not node or not parent_node:
                continue
            current = cmds.listRelatives(node, parent=True) or []
            if current and current[0] == parent_node:
                continue
            try:
                cmds.parent(node, parent_node)
            except Exception as e:
                messages.append("[Warning] {0}: could not parent under {1} ({2}).".format(
                    node, parent_node, e))

    messages.append("[OK] Created {0} template joint(s) ({1} already existed).".format(
        len(created), len(joints) - len(created)))
    if created:
        messages.append("[Info] They are all at the origin - place them by hand, "
                        "then press Match.")
    return created, messages
