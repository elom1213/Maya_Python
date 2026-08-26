# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-26
# A00060_jointTool_V03 - 시작/끝 조인트 쌍마다 ikHandle 을 만든다 (+ 폴 벡터 컨스트레인트).
#
# MEL JointTool V05.03 의 `JUN_cmd_make_jntAim` 이 원래 하던 일이다. V02 로 포팅하면서
# Aim 탭은 **회전만 바꾸는**(IK 를 안 쓰는) 방식으로 다시 설계됐고, 그 과정에서 ikHandle 을
# 만드는 경로가 사라졌다. 이 모듈이 그 자리를 채운다.
#
# ── MEL 원본에서 고친 것 ────────────────────────────────────────────────────
#
#   원본:  for(i) { $ik = `ikHandle -sj $str[i] -ee $end[i]`;
#                   poleVectorConstraint $pole[i] $ik[0]; }
#
#   1. **폴 타깃이 없으면 컨스트레인트를 만들지 않는다.** 원본은 리스트가 짧으면 빈 문자열을
#      그대로 넘겨 에러를 냈다. 이제 그 체인은 IK 만 만들고 넘어간다(로그로 알린다).
#   2. **개수가 안 맞으면 알린다.** 원본은 min() 으로 조용히 잘랐다.
#   3. **솔버를 고를 수 있다.** 원본은 기본값(ikRPsolver) 고정.
#      `ikSCsolver` 는 폴 벡터가 없어서 컨스트레인트를 건너뛴다 - 실측상 그냥 걸면
#      `RuntimeError: Handle must be valid and use rotate plane solver` 다.
#      **`attributeQuery("poleVector")` 로 판정하면 안 된다 - SC 핸들에도 그 어트리뷰트는
#      있다(True 를 돌려준다).** 솔버 이름으로 갈라야 한다.
#   4. **이름을 지어 준다.** 원본은 `ikHandle1`, `effector1` 로 남겼다. 이제 시작 조인트
#      이름에서 핸들·이펙터 이름을 만든다(이펙터 리네임은 옵션).
#   5. **미리 검증한다.** 조인트인가 / 끝이 시작의 자손인가 / 이미 핸들이 걸려 있지 않은가.
#      특히 **같은 체인에 두 번째 핸들을 만드는 것은 마야가 에러도 경고도 없이 해 준다**
#      (실측) - 그래서 여기서 경고한다.
#   6. **한 번의 undo 로 묶는다.**
#
# ── 알아 둘 것 ──────────────────────────────────────────────────────────────
#
# - 일직선 체인은 팔꿈치 방향이 없어 폴 벡터가 정할 평면이 임의가 된다. 실측상
#   `poleVectorConstraint` 는 **에러 없이 성공**하므로 여기서 경고만 내고 진행한다.
# - **`ikSpringSolver` 는 플러그인을 로드하는 것만으로는 부족하다.** 로드해도 솔버 *노드*가
#   없어서 `ikHandle -sol ikSpringSolver` 가 `The ikSolver does not exist.` 로 죽는다(실측).
#   노드는 MEL 프로시저 `ikSpringSolver;` 가 만든다 - 그래서 로드 뒤 한 번 호출한다.
# - **`ikHandle -e -sticky "off"` 는 `The sticky value supplied was invalid.` 경고를 낸다**
#   (값 자체는 들어간다). 새로 만든 핸들은 어차피 off 이므로 켤 때만 건드린다.
# - 이름이 겹치면 마야가 조용히 `_ikHandle1` 로 늘린다(에러 아님).

import maya.cmds as cmds
import maya.mel as mel

from Framework.core.maya_undo import undo_chunk


SOLVER_RP = "ikRPsolver"
SOLVER_SC = "ikSCsolver"
SOLVER_SPRING = "ikSpringSolver"

# UI 콤보 순서. 기본은 ikRPsolver (마야 기본값과 같다).
SOLVERS = (SOLVER_RP, SOLVER_SC, SOLVER_SPRING)

# 폴 벡터를 받는 솔버. ikSCsolver 는 여기 없다.
PV_SOLVERS = (SOLVER_RP, SOLVER_SPRING)

# 플러그인이 필요한 솔버 -> 플러그인 이름
_PLUGIN_SOLVERS = {SOLVER_SPRING: "ikSpringSolver"}

DEFAULT_HANDLE_SUFFIX = "_ikHandle"
DEFAULT_EFFECTOR_SUFFIX = "_effector"

# 일직선 판정 - 체인 축에 수직인 성분이 축 길이의 이 비율보다 작으면 "곧다" 로 본다.
_STRAIGHT_RATIO = 1e-4


# =========================
# 헬퍼
# =========================

def _long(node):
    if not node:
        return None
    found = cmds.ls(node, l=True) or []
    return found[0] if found else None


def _short(node):
    return (node or "").split("|")[-1]


def _is_joint(node):
    return bool(node and cmds.objExists(node) and cmds.nodeType(node) == "joint")


def _world_pos(node):
    return cmds.xform(node, q=True, ws=True, t=True)


def chain_between(start, end):
    """start..end 를 root->leaf 순으로 반환. end 가 start 의 자손이 아니면 None.

    `ikHandle` 도 같은 검사를 하지만(`... is not an ancestor of ...`), 미리 확인해야
    **어느 쌍이 왜 안 되는지**를 다른 쌍을 만들기 전에 로그로 말해 줄 수 있다.
    """
    s_long = _long(start)
    e_long = _long(end)
    if not s_long or not e_long:
        return None
    if s_long == e_long:
        return None

    walk = [e_long]
    parent = cmds.listRelatives(e_long, parent=True, f=True)
    while parent:
        walk.append(parent[0])
        if parent[0] == s_long:
            walk.reverse()
            return walk
        parent = cmds.listRelatives(parent[0], parent=True, f=True)
    return None


def handles_on_chain(joints):
    """주어진 조인트들을 이미 구동하고 있는 ikHandle 목록.

    핸들에서 조인트로 가는 연결을 직접 훑는 것보다 `ikHandle -q -jointList` 가 확실하다.
    (jointList 는 끝 조인트를 빼고 주지만, 겹침 판정에는 그것으로 충분하다.)
    """
    want = set(j for j in (_long(x) for x in joints) if j)
    out = []
    for h in (cmds.ls(type="ikHandle", l=True) or []):
        try:
            jl = cmds.ikHandle(h, q=True, jointList=True) or []
        except Exception:
            continue
        if want.intersection(j for j in (_long(x) for x in jl) if j):
            out.append(h)
    return out


def is_straight(joints):
    """체인이 (거의) 일직선인가 - 팔꿈치 방향이 없어 폴 벡터 평면이 임의가 된다."""
    if len(joints) < 3:
        return True
    root = _world_pos(joints[0])
    end = _world_pos(joints[-1])
    axis = [end[i] - root[i] for i in range(3)]
    aa = sum(v * v for v in axis)
    if aa < 1e-12:
        return True

    axis_len = aa ** 0.5
    for mid in joints[1:-1]:
        to_mid = [x - y for x, y in zip(_world_pos(mid), root)]
        scale = sum(a * b for a, b in zip(to_mid, axis)) / aa
        perp = [to_mid[i] - axis[i] * scale for i in range(3)]
        if (sum(v * v for v in perp) ** 0.5) > axis_len * _STRAIGHT_RATIO:
            return False
    return True


def ensure_solver(solver, messages):
    """플러그인이 필요한 솔버면 로드하고 **솔버 노드까지** 만든다. 못 쓰면 False.

    플러그인만 로드하면 안 된다 - 실측상 그 상태에서 `ikHandle -sol ikSpringSolver` 는
    `The ikSolver does not exist.` 로 죽는다. 솔버 노드는 같은 이름의 MEL 프로시저가 만든다.
    """
    plugin = _PLUGIN_SOLVERS.get(solver)
    if not plugin:
        return True
    try:
        if not cmds.pluginInfo(plugin, q=True, loaded=True):
            cmds.loadPlugin(plugin, quiet=True)
        if not cmds.objExists(solver):
            mel.eval("{0};".format(solver))
        return True
    except Exception as e:
        messages.append(
            "[ERR] Could not set up the '{0}' solver ({1}).".format(solver, e))
        return False


def resolve_pairs(starts, ends, poles):
    """(start, end, pole) 튜플 목록 + 잘라낸 개수 안내 메시지.

    start/end 는 짝이 맞아야 하고, pole 은 **없어도 된다** - 짧으면 그 뒤 체인은
    폴 벡터 컨스트레인트 없이 IK 만 만든다.
    """
    starts = list(starts or [])
    ends = list(ends or [])
    poles = list(poles or [])

    count = min(len(starts), len(ends))
    notes = []
    if len(starts) != len(ends):
        notes.append(
            "[Warning] Start has {0} item(s) and End has {1} - only the first {2} "
            "pair(s) are used.".format(len(starts), len(ends), count))
    if len(poles) > count:
        notes.append(
            "[Warning] pole tgt has {0} item(s) but there are only {1} chain(s) - "
            "the extra target(s) are ignored.".format(len(poles), count))
    elif poles and len(poles) < count:
        notes.append(
            "[Info] pole tgt has {0} item(s) for {1} chain(s) - the remaining chain(s) "
            "get an IK handle with no pole vector constraint.".format(len(poles), count))

    pairs = []
    for i in range(count):
        pole = poles[i] if i < len(poles) else None
        pairs.append((starts[i], ends[i], pole))
    return pairs, notes


# =========================
# 본체
# =========================

def create_ik_handles(starts, ends, poles,
                      solver=SOLVER_RP,
                      handle_suffix=DEFAULT_HANDLE_SUFFIX,
                      rename_effector=True,
                      effector_suffix=DEFAULT_EFFECTOR_SUFFIX,
                      sticky=False):
    """시작/끝 쌍마다 ikHandle 을 만들고, 폴 타깃이 있으면 컨스트레인트도 건다.

    돌려주는 것은 `(results, messages)`.
    `results` 는 쌍마다 dict — 실패한 쌍은 `handle` 이 None 이고 `error` 가 채워진다.
    **한 쌍이 실패해도 나머지는 계속 만든다** (원본 MEL 은 첫 에러에서 멈췄다).
    """
    messages = []

    if solver not in SOLVERS:
        messages.append("[ERR] Unknown solver '{0}'.".format(solver))
        return [], messages

    pairs, notes = resolve_pairs(starts, ends, poles)
    messages.extend(notes)

    if not pairs:
        messages.append("[ERR] Fill both the Start and the End list first.")
        return [], messages

    if not ensure_solver(solver, messages):
        return [], messages

    handle_suffix = handle_suffix if handle_suffix is not None else ""
    effector_suffix = effector_suffix if effector_suffix is not None else ""

    results = []

    with undo_chunk():
        for start, end, pole in pairs:
            entry = {"start": start, "end": end, "pole": pole,
                     "handle": None, "effector": None, "constraint": None,
                     "error": None}
            results.append(entry)

            # ---- 검증 ----
            problem = _validate(start, end, pole)
            if problem:
                entry["error"] = problem
                messages.append("[ERR] {0}".format(problem))
                continue

            joints = chain_between(start, end)
            existing = handles_on_chain(joints)
            if existing:
                messages.append(
                    "[Warning] {0}: the chain already has {1} ({2}). Maya lets you stack "
                    "a second handle on it without complaining - remove the old one if "
                    "that is not what you want.".format(
                        _short(start), "an IK handle" if len(existing) == 1
                        else "{0} IK handles".format(len(existing)),
                        ", ".join(_short(h) for h in existing)))

            # ---- 생성 ----
            try:
                created = cmds.ikHandle(sj=start, ee=end, solver=solver,
                                        name=_short(start) + handle_suffix)
            except Exception as e:
                entry["error"] = "{0}: {1}".format(_short(start), e)
                messages.append("[ERR] {0}".format(entry["error"]))
                continue

            handle, effector = created[0], created[1]
            entry["handle"] = handle
            entry["effector"] = effector

            if rename_effector:
                try:
                    entry["effector"] = cmds.rename(
                        effector, _short(start) + effector_suffix)
                except Exception as e:
                    messages.append("[Warning] {0}: could not rename the effector "
                                    "({1}).".format(_short(handle), e))

            # 새 핸들은 이미 off 다. 켤 때만 건드린다 - "off" 를 넘기면 마야가
            # `The sticky value supplied was invalid.` 경고를 낸다(값은 들어가지만 로그가 지저분해진다).
            if sticky:
                try:
                    cmds.ikHandle(handle, e=True, sticky="sticky")
                except Exception as e:
                    messages.append("[Warning] {0}: could not set sticky ({1}).".format(
                        _short(handle), e))

            messages.append("[OK] {0}: IK handle '{1}' created with {2}.".format(
                _short(start), _short(handle), solver))

            # ---- 폴 벡터 ----
            _apply_pole_vector(entry, joints, solver, messages)

    made = len([r for r in results if r["handle"]])
    constrained = len([r for r in results if r["constraint"]])
    messages.append(
        "[OK] {0} of {1} chain(s) done - {2} pole vector constraint(s).".format(
            made, len(results), constrained))

    return results, messages


def _validate(start, end, pole):
    """만들기 전에 걸러 낼 것. 문제가 없으면 None."""
    if not start or not cmds.objExists(start):
        return "Start '{0}' does not exist.".format(_short(start))
    if not end or not cmds.objExists(end):
        return "End '{0}' does not exist.".format(_short(end))
    if not _is_joint(start):
        return "Start '{0}' is not a joint ({1}).".format(
            _short(start), cmds.nodeType(start))
    if not _is_joint(end):
        return "End '{0}' is not a joint ({1}).".format(
            _short(end), cmds.nodeType(end))
    if _long(start) == _long(end):
        return "'{0}': Start and End are the same joint.".format(_short(start))
    if chain_between(start, end) is None:
        return "'{0}' is not an ancestor of '{1}' - they are not one chain.".format(
            _short(start), _short(end))
    if pole and not cmds.objExists(pole):
        return "Pole target '{0}' does not exist.".format(_short(pole))
    return None


def _apply_pole_vector(entry, joints, solver, messages):
    """폴 타깃이 주어졌을 때만 컨스트레인트를 건다."""
    pole = entry.get("pole")
    handle = entry.get("handle")
    if not handle:
        return

    if not pole:
        # 요청받은 동작: 타깃이 없으면 컨스트레인트를 만들지 않는다.
        messages.append("[Info] {0}: no pole target given - IK handle only.".format(
            _short(handle)))
        return

    if solver not in PV_SOLVERS:
        messages.append(
            "[Warning] {0}: {1} has no pole vector, so '{2}' was ignored. Use "
            "{3} if you need one.".format(
                _short(handle), solver, _short(pole), SOLVER_RP))
        return

    if is_straight(joints):
        messages.append(
            "[Warning] {0}: the chain is straight, so there is no elbow direction and "
            "the pole vector plane is arbitrary. Bend the chain a little before "
            "creating the IK if the flip matters.".format(_short(handle)))

    try:
        con = cmds.poleVectorConstraint(pole, handle)
        entry["constraint"] = con[0] if con else None
        messages.append("[OK] {0}: pole vector constraint to '{1}'.".format(
            _short(handle), _short(pole)))
    except Exception as e:
        messages.append("[ERR] {0}: pole vector constraint to '{1}' failed ({2}).".format(
            _short(handle), _short(pole), e))
