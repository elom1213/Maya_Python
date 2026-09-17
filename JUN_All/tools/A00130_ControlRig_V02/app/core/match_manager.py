# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
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
#
# ── 부모부터 맞추고, 밀려난 것은 다시 맞춘다 (2026-09-17, v02.20) ────────────
#
# 매핑 표 순서대로 맞추면 자식을 먼저 맞춘 뒤 부모가 움직여 **자식이 도로 어긋났다**
# (Match 를 여러 번 눌러야 했다). 이제 **계층이 얕은 것부터** 맞추고, 한 바퀴 뒤 다른 매칭에
# 밀려난 멤버를 **다시 맞춘다**(최대 MAX_PASSES 바퀴). 자세한 것은 `_run_ops`.

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


#: 다시 맞추기를 몇 바퀴까지 돌릴지 (첫 바퀴 포함)
MAX_PASSES = 5

#: 월드 행렬이 "그대로" 라고 볼 허용치 (행렬 원소 차이)
MATRIX_TOLERANCE = 1e-4


class _MatchOp(object):
    """멤버 하나를 조인트 하나에 맞추는 일 한 건."""

    def __init__(self, index, row, member, do_t, do_r, notes):
        self.index = index          # 매핑 표 순서 (같은 깊이 안에서 이 순서를 지킨다)
        self.row = row
        self.member = member
        self.do_t = do_t
        self.do_r = do_r
        self.notes = notes
        self.error = None
        try:
            path = (cmds.ls(member, long=True) or [member])[0]
        except Exception:
            path = member
        self.depth = path.count("|")


def _world_matrix(node):
    return cmds.xform(node, query=True, worldSpace=True, matrix=True)


def _same_matrix(a, b):
    return all(abs(x - y) <= MATRIX_TOLERANCE for x, y in zip(a, b))


def _run_ops(ops):
    """매칭을 실행한다. 로그 목록을 돌려준다.

    ── 왜 순서가 문제인가 (2026-09-17, 사용자 보고) ─────────────────────────
    `obj_01 > obj_02 > obj_03 > obj_04` 에서 **obj_03 을 먼저 맞추고 obj_01 을 나중에**
    맞추면, obj_01 이 움직일 때 **자식인 obj_03 이 딸려 가서 다시 어긋난다.** 매핑 표 순서대로
    맞추면 이런 일이 생기고, 그래서 Match 를 여러 번 눌러야 자리를 잡았다.

    1) **계층이 얕은 것(부모)부터** 맞춘다. 같은 깊이 안에서는 매핑 표 순서 그대로다
       (같은 멤버가 두 세트에 있으면 뒤쪽 행이 이기는 기존 규칙이 유지된다).
    2) 부모-자식이 아닌 연결(컨스트레인트로 따라가는 그룹 · offsetParentMatrix 등)은 깊이로
       순서를 못 정한다. 그래서 한 바퀴 끝나면 **멤버마다 자기가 맞춰진 직후의 월드 행렬과
       지금 행렬을 비교**하고, 다른 매칭에 밀려난 멤버만 **다시 맞춘다.** 사람이 Match 를 다시
       누르던 일을 툴이 한다. 서로가 서로를 미는 순환이면 끝나지 않으므로 MAX_PASSES 에서
       멈추고 이름을 짚어 알린다.
    """
    messages = []
    ordered = sorted(ops, key=lambda op: (op.depth, op.index))

    def run(batch):
        """batch 를 순서대로 맞추고 멤버별 '맞춘 직후' 행렬을 돌려준다."""
        after = {}
        for op in batch:
            try:
                cmds.matchTransform(op.member, op.row["joint"],
                                    position=op.do_t, rotation=op.do_r, scale=False)
            except Exception as e:
                op.error = e
                continue
            after[op.member] = _world_matrix(op.member)
        return after

    after = run(ordered)
    moved = set()
    for pass_number in range(2, MAX_PASSES + 1):
        moved = {member for member, matrix in after.items()
                 if not _same_matrix(_world_matrix(member), matrix)}
        if not moved:
            break
        messages.append(
            "[Info] Match pass {0}: {1} object(s) were moved by another match after they "
            "were placed (not a parent-child link) - matching them again: {2}.".format(
                pass_number, len(moved),
                ", ".join(sorted(su.short_name(m) for m in moved))))
        again = [op for op in ordered if op.member in moved and op.error is None]
        after.update(run(again))
    else:
        moved = {member for member, matrix in after.items()
                 if not _same_matrix(_world_matrix(member), matrix)}
        if moved:
            messages.append(
                "[Warning] {0} object(s) still move each other after {1} passes - they "
                "probably drive each other in a loop: {2}.".format(
                    len(moved), MAX_PASSES,
                    ", ".join(sorted(su.short_name(m) for m in moved))))
    return messages


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
            # ---- 1) 행마다 "무엇을 어떤 채널로 맞출지" 만 정한다 (아직 안 옮긴다) ----
            ops = []            # _MatchOp 목록 - 실행은 아래에서 계층 순서로
            ok_rows = []        # 멤버가 있는 행 - 행별 [OK] 로그용
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
                ok_rows.append(row)

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

                    op = _MatchOp(len(ops), row, member, do_t, do_r, notes)
                    ops.append(op)

            # ---- 2) 부모부터 맞춘다 + 다른 매칭에 밀려난 것은 다시 맞춘다 ----
            messages.extend(_run_ops(ops))

            for op in ops:
                if op.error:
                    results["skipped_members"] += 1
                    messages.append("[ERR] {0} <- {1} : {2}".format(
                        su.short_name(op.member), op.row["joint"], op.error))
                    continue
                results["matched"] += 1
                if op.notes:
                    # 일부만 넣었다 - 무엇을 넣고 무엇을 뺐는지 분명히 적는다
                    results["partial"] += 1
                    did = " + ".join(
                        [x for x in ("position" if op.do_t else "",
                                     "rotation" if op.do_r else "") if x])
                    messages.append("[Info] {0}: '{1}' matched {2} only - {3}.".format(
                        op.row["set"], su.short_name(op.member), did, "; ".join(op.notes)))

            for row in ok_rows:
                seen_joints.add(row["joint"])
                mode = "position only" if "r" not in row["match"] else "position + rotation"
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


# =========================
# Check Position (v02.21)
# =========================
#
# "Cage set 안의 오브젝트들이 **월드 기준으로 전부 같은 위치 · 같은 회전**에 있나" 를 본다.
# 씬은 바꾸지 않는다. Match 가 한 세트의 멤버를 같은 조인트에 맞추므로, 멤버끼리 어긋나 있으면
# 매칭이 덜 됐거나(막힌 채널 · 리그가 구동) 누군가 손으로 옮긴 것이다.
#
# - **위치는 월드 rotate pivot** 으로 비교한다. `matchTransform -position` 이 맞추는 기준이
#   피벗이라(translate 값이 아니라) 같은 기준으로 봐야 Match 결과와 판정이 어긋나지 않는다.
# - **회전은 월드 행렬의 방향(쿼터니언) 사이 각도**로 비교한다. 오일러 값끼리 비교하면
#   rotateOrder · jointOrient · 360도 차이 · 짐벌에서 같은 방향이 다른 숫자로 나와 틀린 판정을 낸다.
#   스케일은 MTransformationMatrix 가 떼어 낸다.
# - 기준은 **첫 멤버**다. 가장 멀리 벗어난 멤버의 이름과 차이를 적는다.

#: Check Position 허용치
POSITION_TOLERANCE = 1e-3       # 월드 단위
ROTATION_TOLERANCE = 1e-2       # 도

#: Check Position 결과 코드
CHECK_OK = "OK"
CHECK_DIFFERENT = "different"
CHECK_SKIPPED = "not checked"


def _world_pose(node):
    """(월드 rotate pivot MVector, 월드 방향 MQuaternion). 트랜스폼이 아니면 예외."""
    import maya.api.OpenMaya as om

    pivot = cmds.xform(node, query=True, worldSpace=True, rotatePivot=True)
    matrix = om.MMatrix(cmds.xform(node, query=True, worldSpace=True, matrix=True))
    quat = om.MTransformationMatrix(matrix).rotation(asQuaternion=True)
    return om.MVector(pivot[0], pivot[1], pivot[2]), quat


def _angle_between(q1, q2):
    """두 방향 사이 각도(도). q 와 -q 는 같은 방향이라 절댓값을 쓴다."""
    import math
    dot = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w)
    return math.degrees(2.0 * math.acos(min(1.0, dot)))


def check_positions(rows, namespace=None,
                    pos_tol=POSITION_TOLERANCE, rot_tol=ROTATION_TOLERANCE):
    """행(= Cage set)마다 멤버들이 같은 월드 위치 · 회전인지 본다. 씬 불변.

    템플릿 조인트가 없는 행은 plan() 이 멤버를 안 펴 두므로, 그때는 namespace 로 세트를
    직접 찾아 본다 - 이 검사는 조인트가 없어도 뜻이 있다(멤버끼리 비교).

    돌려주는 것: `(results, messages)`. results 는 rows 와 같은 순서의 dict 목록 -
        state      CHECK_OK / CHECK_DIFFERENT / CHECK_SKIPPED
        text       Status 칸에 쓸 한 줄 (영어)
        max_pos    멤버 사이 최대 위치 차 (없으면 None)
        max_rot    멤버 사이 최대 회전 차, 도 (없으면 None)
    """
    results = []
    counts = {CHECK_OK: 0, CHECK_DIFFERENT: 0, CHECK_SKIPPED: 0}
    messages = []

    for row in rows:
        result = {"state": CHECK_SKIPPED, "text": "", "max_pos": None, "max_rot": None}
        results.append(result)
        name = su.short_name(row["set"])

        members = row["members"] or []
        if row["status"] == ST_NO_JOINT:
            set_node, _found = su.resolve(row["set_wanted"], namespace)
            if set_node:
                members, _skipped = su.resolve_members(set_node)
            else:
                result["text"] = "Not checked - set missing"
                counts[CHECK_SKIPPED] += 1
                continue

        if row["status"] == ST_NO_SET:
            result["text"] = "Not checked - set missing"
            counts[CHECK_SKIPPED] += 1
            continue

        members = [m for m in members if cmds.objExists(m)]
        if not members:
            result["text"] = "Not checked - no member"
            counts[CHECK_SKIPPED] += 1
            continue

        poses, unreadable = [], []
        for member in members:
            # ★ 컴포넌트(`cube.vtx[0]`)는 xform 이 **에러 없이 오브젝트의 행렬을 돌려준다**(실측) -
            #   그대로 두면 오브젝트와 "같다" 고 OK 가 나온다. 이름으로 먼저 거른다.
            if "." in member:
                unreadable.append(member)
                continue
            try:
                poses.append((member,) + _world_pose(member))
            except Exception:
                unreadable.append(member)

        if unreadable:
            # 트랜스폼이 아닌 멤버(컴포넌트 등)는 위치·회전을 비교할 수 없다 - 괜찮다고 말하지 않는다.
            result["state"] = CHECK_DIFFERENT
            result["text"] = "Cannot read the transform of: {0}".format(
                ", ".join(su.short_name(m) for m in unreadable))
            counts[CHECK_DIFFERENT] += 1
            messages.append("[Warning] Check Position {0}: {1}".format(name, result["text"]))
            continue

        base_name, base_pos, base_rot = poses[0]
        worst_pos, worst_rot = (0.0, None), (0.0, None)
        for member, pos, rot in poses[1:]:
            d_pos = (pos - base_pos).length()
            d_rot = _angle_between(rot, base_rot)
            if d_pos > worst_pos[0]:
                worst_pos = (d_pos, member)
            if d_rot > worst_rot[0]:
                worst_rot = (d_rot, member)

        result["max_pos"], result["max_rot"] = worst_pos[0], worst_rot[0]
        problems = []
        if worst_pos[0] > pos_tol:
            problems.append("position differs by {0:.4g} ({1})".format(
                worst_pos[0], su.short_name(worst_pos[1])))
        if worst_rot[0] > rot_tol:
            problems.append("rotation differs by {0:.4g} deg ({1})".format(
                worst_rot[0], su.short_name(worst_rot[1])))

        if problems:
            result["state"] = CHECK_DIFFERENT
            text = "; ".join(problems)
            result["text"] = text[0].upper() + text[1:] + " vs {0}".format(su.short_name(base_name))
            counts[CHECK_DIFFERENT] += 1
            messages.append("[Warning] Check Position {0}: {1}".format(name, result["text"]))
        else:
            result["state"] = CHECK_OK
            result["text"] = ("OK - 1 member" if len(poses) == 1 else
                              "OK - {0} members share position and rotation".format(len(poses)))
            counts[CHECK_OK] += 1

    summary = "Check Position : {0} OK, {1} different, {2} not checked.".format(
        counts[CHECK_OK], counts[CHECK_DIFFERENT], counts[CHECK_SKIPPED])
    if counts[CHECK_DIFFERENT] == 0 and counts[CHECK_OK]:
        summary = "[OK] " + summary
    messages.insert(0, summary)
    return results, messages
