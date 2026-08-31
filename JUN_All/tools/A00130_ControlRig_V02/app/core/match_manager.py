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
# (실측) 쓰기 전에 미리 본다.
#
# ── 막힌 채널은 **그룹 단위**로 가른다 (2026-08-28) ─────────────────────────
#
# 처음에는 채널 하나라도 막히면 그 오브젝트를 **통째로** 건너뛰었다. 실제 케이지에서
# 그게 과했다 — `pointConstraint` 가 걸린 컨트롤러는 **위치만** 리그가 갖고 있고
# **회전은 비어 있는데**, 통째로 건너뛰니 **회전이 매칭 안 된 채 방치**됐다.
#
# 실측: 컨스트레인트는 그룹을 통째로 막는다(point=T 3/3, orient/aim=R 3/3, parent=양쪽).
# 반면 축 하나만 잠긴 경우는 `t=[90, 2, 3]` 처럼 진짜 반쪽이 된다.
#
# → **그룹(translate / rotate) 단위로 all-or-nothing.**
#   전부 막혔으면 그 그룹만 깨끗이 건너뛰고 **나머지 그룹은 매칭한다.**
#   일부만 막혔으면 그 그룹은 **건드리지 않고 크게 알린다.**

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import ik_axis_manager
from . import ik_session
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


def apply(rows, ik_handles=None, auto_ik=True, axis_doc=None, namespace=None):
    """계산된 행대로 실제로 맞춘다. `(results, messages)`.

    전체가 **undo 한 스텝**이다.

    `ik_handles` 를 주면 **매칭 앞뒤로 IK 편집 세션을 연다** (계획서 Phase 4):

        IK 끄기 -> 매칭 -> 핸들 스냅 + 폴 벡터 역산 -> IK 켜기

    이게 없으면 IK 가 걸린 조인트는 `matchTransform` 이 **성공해도 다음 평가에서 IK 가
    도로 가져간다**(실측). 그러면 툴은 `[OK] matched` 라고 보고하는데 아무것도 안 바뀐다.
    자세한 근거는 `ik_session` 의 모듈 주석.

    `auto_ik` 면 **세트에 없더라도 매칭 대상을 건드리는 핸들을 씬에서 찾아 함께 끈다.**
    중첩 IK(팔 체인 안의 Drv 체인 등)가 세트에서 빠져 있으면, 그 솔버가 매칭과 싸워
    **조인트가 부모와 어긋난 채 남는다**(실측 7.643도). 자세한 것은
    `ik_session.related_handles` 의 주석.

    `axis_doc` 을 주면 **IK 세션이 끝난 뒤에** 정해진 축이 폴 타깃을 보도록 `twist` 를
    맞춘다(`ik_axis_manager`). 세션이 끝난 **뒤**여야 하는 이유는, 그때라야 핸들과 폴
    벡터가 새 체인에 맞춰져 있어 잰 각도가 뜻을 갖기 때문이다.

    매칭 도중 예외가 나면 **편집을 취소해 체인을 원래대로 돌리고** IK 를 되켠 뒤 예외를
    다시 올린다 — 반쯤 매칭된 체인에 IK 가 다시 붙는 것이 제일 나쁘다.
    """
    messages = []
    results = {
        "matched": 0,            # 한 그룹이라도 적용된 멤버 수
        "joints": 0,
        "skipped_members": 0,    # 아무것도 적용 못 한 멤버 수
        "partial": 0,            # 일부 그룹만 적용된 멤버 수
        "driven_t": 0,           # 위치를 리그가 갖고 있어 건너뛴 수
        "driven_r": 0,
        "half": 0,               # 축이 일부만 막혀 손대지 않은 그룹 수
    }
    seen_joints = set()

    with undo_chunk():
        # ---- IK 편집 모드 진입 ----
        handles = list(ik_handles or [])

        if auto_ik:
            # 세트를 믿되 그것만 믿지 않는다 - 빠진 핸들을 찾아 함께 끈다
            members = [m for row in rows for m in (row["members"] or [])]
            extra, extra_msgs = ik_session.related_handles(members, handles)
            messages.extend(extra_msgs)
            handles.extend(extra)

        session = None
        if handles:
            session, ik_msgs = ik_session.begin(handles)
            messages.extend(ik_msgs)

        try:
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

                    # 그룹 단위로 "지금 쓸 수 있나" 를 본다 (위 주석 참고)
                    do_t, do_r = want_t, want_r
                    notes = []

                    if want_t:
                        state, blocked = su.channel_group_state(member, "translate")
                        if state == su.GROUP_DRIVEN:
                            do_t = False
                            results["driven_t"] += 1
                            notes.append("position is driven by the rig")
                        elif state == su.GROUP_PARTIAL:
                            do_t = False
                            results["half"] += 1
                            notes.append(
                                "position left alone - only {0} blocked, moving the rest "
                                "would half-move it".format(", ".join(blocked)))

                    if want_r:
                        state, blocked = su.channel_group_state(member, "rotate")
                        if state == su.GROUP_DRIVEN:
                            do_r = False
                            results["driven_r"] += 1
                            notes.append("rotation is driven by the rig")
                        elif state == su.GROUP_PARTIAL:
                            do_r = False
                            results["half"] += 1
                            notes.append(
                                "rotation left alone - only {0} blocked, rotating the rest "
                                "would half-move it".format(", ".join(blocked)))

                    if not do_t and not do_r:
                        results["skipped_members"] += 1
                        messages.append("[Warning] {0}: '{1}' skipped - {2}.".format(
                            row["set"], su.short_name(member), "; ".join(notes)))
                        continue

                    try:
                        cmds.matchTransform(member, row["joint"],
                                            position=do_t, rotation=do_r, scale=False)
                    except Exception as e:
                        results["skipped_members"] += 1
                        messages.append("[ERR] {0} <- {1} : {2}".format(
                            su.short_name(member), row["joint"], e))
                        continue

                    results["matched"] += 1
                    if notes:
                        # 일부만 넣었다 - 무엇을 넣고 무엇을 뺐는지 분명히 적는다
                        results["partial"] += 1
                        did = " + ".join(
                            [x for x in ("position" if do_t else "",
                                         "rotation" if do_r else "") if x])
                        messages.append("[Info] {0}: '{1}' matched {2} only - {3}.".format(
                            row["set"], su.short_name(member), did, "; ".join(notes)))

                seen_joints.add(row["joint"])
                mode = "position only" if not want_r else "position + rotation"
                messages.append("[OK] {0} <- {1} : {2} member(s), {3}.".format(
                    row["joint"], su.short_name(row["set"]), len(row["members"]), mode))
        except Exception:
            # 반쯤 매칭된 체인에 IK 를 도로 붙이지 않는다 - 시작 상태로 되돌린다
            if session:
                messages.extend(ik_session.cancel(session))
            raise

        # ---- IK 편집 모드 종료 (핸들 스냅 + 폴 벡터 역산) ----
        if session:
            _ik_results, ik_msgs = ik_session.end(session)
            messages.extend(ik_msgs)

        # ---- IK 축 맞추기 (세션이 끝난 뒤라야 잰 각도가 뜻을 갖는다) ----
        if axis_doc and (axis_doc.get("sets") or []):
            axis_rows, axis_msgs = ik_axis_manager.plan(
                axis_doc, namespace if namespace is not None else su.NO_NAMESPACE)
            messages.extend(axis_msgs)
            if axis_rows:
                _axis_results, axis_msgs = ik_axis_manager.apply(axis_rows)
                messages.extend(axis_msgs)

    results["joints"] = len(seen_joints)
    messages.append("[OK] Match done - {0} object(s) on {1} joint(s), {2} skipped.".format(
        results["matched"], results["joints"], results["skipped_members"]))
    if results["partial"]:
        messages.append(
            "[Info] {0} object(s) matched only part of the channels - the rig already "
            "drives the rest ({1} position, {2} rotation).".format(
                results["partial"], results["driven_t"], results["driven_r"]))
    if results["half"]:
        messages.append(
            "[Warning] {0} channel group(s) were left alone because only some axes are "
            "locked - moving the rest would half-move the object. Unlock them or "
            "lock the whole group.".format(results["half"]))
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
