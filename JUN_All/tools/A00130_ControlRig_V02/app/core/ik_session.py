# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - IK 편집 세션 : Match 앞뒤로 IK 를 껐다 켠다.
#
# 계획서 Phase 4 · 7-4.
#
# ── 왜 필요한가 (실측) ──────────────────────────────────────────────────────
#
# IK 가 걸린 조인트는 **막힌 것처럼 보이지 않는다.** IK 는 어트리뷰트 연결이 아니라
# 솔버로 값을 쓰기 때문이다:
#
#     connectionInfo("ik_mid.rotateZ", isDestination=True)  ->  False
#     channel_group_state("ik_mid", "rotate")               ->  free
#
# 그래서 `matchTransform` 은 **성공하고**, 다음 평가에서 IK 가 **도로 가져간다**:
#
#     전     ik_mid r = [0, 0, 0]
#     직후   ik_mid r = [15, 25, 35]     <- 들어갔다
#     평가후 ik_mid r = [0, 0, 0]        <- IK 가 되돌렸다
#
# 툴은 `[OK] ... matched` 라고 보고하는데 **아무것도 안 바뀐다** — 조용한 거짓 성공이다.
#
# ── 끄고 켜는 것만으로는 부족하다 ───────────────────────────────────────────
#
#     ikBlend=0 -> 매칭 -> r = [15, 25, 35]   OK
#     ikBlend=1 복원   -> r = [0, 0, 0]       원위치
#
# **핸들을 새 체인에 스냅하고 폴 벡터를 역산**해야 편집이 남는다. 그 계산은
# `A00060_jointTool_V03` 의 IK Edit 이 이미 갖고 있다(핸들 스냅만으론 편차 1.615,
# 폴 벡터 역산까지 해야 0). **다시 만들지 않고 그것을 부른다.**
#
# ── ikBlend 는 이 리그에서 쓰이지 않는다 ────────────────────────────────────
#
# 사용자 확인(2026-08-28): 이 케이지의 ikHandle 은 **`ikBlend` 를 FK/IK 스위치로 쓰지
# 않는다.** 그래서 계획서 7-4 가 "최대 기술 리스크" 로 꼽았던 **씬 전역 IK 정지**
# (`ikSystem -e -solve 0`) 로 물러설 일이 없다 — 핸들별로 끄면 된다.
#
# 다만 **가정하지 않고 확인한다.** `preflight()` 가 핸들마다 `ikBlend` 를 쓸 수 있는지
# 미리 보고, 하나라도 구동되고 있으면 **크게 알린다** — 그건 전제가 깨졌다는 뜻이고,
# 그대로 두면 씬 전체 IK 가 꺼진 채 매칭이 돈다.

import maya.cmds as cmds

from tools.A00060_jointTool_V03.app.core import ik_edit_manager as ike

from . import scene_utils as su


#: 케이지에서 ikHandle 을 모아 둔 세트의 기본 이름
DEFAULT_IK_SET = "D01_IK_handle"


# =========================
# 세트 -> 핸들
# =========================

def resolve_set(name, namespace):
    """ikHandle 세트를 찾는다. `(세트 노드 또는 None, messages)`.

    조인트·케이지 세트·옵션 컨트롤러와 **같은 이름 해석**을 쓴다 — 네임스페이스를 붙인
    쪽 먼저, 없으면 이름 그대로. 레퍼런스한 케이지면 `CAGE:D01_IK_handle` 이 된다.
    """
    messages = []
    if not name:
        return None, messages

    node, found = su.resolve(name, namespace)
    if not node:
        messages.append(
            "[Info] No ikHandle set called {0} - matching without an IK session.".format(
                " or ".join(su.candidates(name, namespace))))
        return None, messages

    if len(found) > 1:
        messages.append("[Warning] Ambiguous ikHandle set - using {0} (also found {1}).".format(
            node, ", ".join(found[1:])))

    if not su.is_set(node):
        messages.append("[Warning] '{0}' is not a set - ignoring it.".format(node))
        return None, messages

    return node, messages


def handles_in_set(set_node):
    """세트 안의 ikHandle 목록. `(handles, messages)`.

    세트에 핸들이 아닌 것이 섞여 있어도 **조용히 버리지 않고 알린다.**
    하위 세트는 Match 와 같은 이유로 펴지 않는다(계획서 1-11).
    """
    messages = []
    if not set_node:
        return [], messages

    members, skipped_sets = su.resolve_members(set_node)
    if skipped_sets:
        messages.append("[Info] {0}: {1} sub-set(s) ignored.".format(
            su.short_name(set_node), len(skipped_sets)))

    handles, others = [], []
    for m in members:
        try:
            is_handle = cmds.objectType(m, isAType="ikHandle")
        except Exception:
            is_handle = False
        (handles if is_handle else others).append(m)

    if others:
        messages.append("[Warning] {0}: {1} member(s) are not ikHandles - ignored ({2}).".format(
            su.short_name(set_node), len(others),
            ", ".join(su.short_name(o) for o in others[:5])))

    return handles, messages


# =========================
# 세트에 없는데 관련된 핸들 찾기
# =========================

def _long(node):
    names = cmds.ls(node, long=True) or []
    return names[0] if names else node


def _self_and_descendants(node):
    out = {_long(node)}
    for c in (cmds.listRelatives(node, allDescendents=True, type="joint",
                                 fullPath=True) or []):
        out.add(c)
    return out


def related_handles(members, known=()):
    """매칭 대상을 건드리는데 **세트에 없는** ikHandle 을 찾는다. `(handles, messages)`.

    ── 왜 필요한가 (2026-08-28 실측) ─────────────────────────────────────────
    `D01_IK_handle` 은 리거가 손으로 채우는 목록이라 **빠진 핸들이 있을 수 있다.**
    특히 **중첩 IK** — 메인 팔 체인 안에 Drv 체인이 또 들어 있는 구조:

        CH_r_UpperArm_xx_ikjnt
        └── CH_r_UpperArmDrv_xx_ikjnt      <- 이 체인에도 제 ikHandle 이 있다
            └── CH_r_LowerArmDrv_xx_ikjnt

    Drv 핸들이 세트에 없으면 **매칭 중에도 계속 풀린다.** 부모 체인이 움직이는 동안
    솔버가 Drv 조인트를 다시 잡아, 회전이 부모와 어긋난 채 남는다:

        Drv 핸들이 세트에 있을 때  -> 부모 대비 0.000 도   OK
        Drv 핸들이 세트에 없을 때  -> 부모 대비 7.643 도   X

    (`LowerArmDrv` 는 **끝 조인트**라 솔버가 안 돌린다 - 그래서 겉보기엔 한 조인트만
    틀어진 것처럼 보인다.)

    그래서 **세트를 믿되 그것만 믿지 않는다.** 매칭 대상(그리고 그 하위)을 체인에
    포함하는 핸들을 씬에서 찾아 **함께 끄고, 무엇을 더 껐는지 알린다** — 리거가
    세트를 고칠 수 있도록.
    """
    messages = []
    if not members:
        return [], messages

    touched = set()
    for m in members:
        if cmds.objExists(m):
            touched |= _self_and_descendants(m)

    known_long = {_long(h) for h in (known or [])}
    found = []

    for handle in (cmds.ls(type="ikHandle", long=True) or []):
        if handle in known_long:
            continue
        try:
            chain = ike.chain_joints(handle)
        except Exception:
            chain = []
        if not chain:
            continue
        if any(_long(j) in touched for j in chain):
            found.append(handle)

    if found:
        messages.append(
            "[Warning] {0} ikHandle(s) drive joints being matched but are NOT in the "
            "handle set - turning them off too, otherwise their solver would fight the "
            "match and leave the joints rotated: {1}. Consider adding them to the "
            "set.".format(len(found), ", ".join(su.short_name(h) for h in found[:6])))

    return found, messages


# =========================
# 사전 점검
# =========================

def preflight(handles):
    """편집을 시작하기 전에 볼 수 있는 것을 본다. `(ok_handles, messages)`.

    `ikBlend` 가 **구동되고 있으면** A00060 은 씬 전역 IK 정지로 물러선다. 이 리그는
    `ikBlend` 를 쓰지 않기로 돼 있으므로, 그런 핸들이 있다면 **전제가 깨진 것**이다.
    조용히 전역으로 끄지 않고 **분명히 알린다.**
    """
    messages = []
    ok, driven = [], []

    for h in handles:
        if not cmds.objExists(h):
            messages.append("[Warning] '{0}' no longer exists.".format(su.short_name(h)))
            continue

        plug = h + ".ikBlend"
        if cmds.objExists(plug) and not su.plug_writable(plug):
            driven.append(h)
        ok.append(h)

    if driven:
        messages.append(
            "[Warning] {0} handle(s) have a driven ikBlend ({1}). This rig is not "
            "supposed to use ikBlend as an FK/IK switch - IK solving would be turned "
            "off SCENE-WIDE for the edit instead of per handle. Check the rig.".format(
                len(driven), ", ".join(su.short_name(h) for h in driven[:5])))

    return ok, messages


def describe(set_node, handles):
    """UI 한 줄 요약."""
    if not set_node:
        return "no ikHandle set found - matching without an IK session"
    if not handles:
        return "{0} : no ikHandle inside".format(su.short_name(set_node))
    return "{0} : {1} ikHandle(s)".format(su.short_name(set_node), len(handles))


# =========================
# 세션
# =========================

def _snap_off(handles):
    """세션 동안 `snapEnable` 을 꺼 두고 원래 값을 돌려준다. `{handle: 값}`.

    ── 왜 끄나 (2026-08-28 실측) ─────────────────────────────────────────────
    `snapEnable` 이 켜져 있으면 **마야가 평가 중에 ikHandle 의 translate 를 직접 쓴다**
    (핸들을 이펙터에 붙인다). 그 쓰기는 우리 편집 사이사이에 끼어들고 undo 큐가 그것을
    그대로 재구성하지 못해서, **undo 한 번에 핸들이 중간값에 착지한다**:

        snapEnable 그대로   before=[20,0,0] after=[18,0,3] undo=[19.063, 4.226, 0]  X
        snapEnable 껐다 켜기 before=[20,0,0] after=[18,0,3] undo=[20,0,0]           O

    끄고 있어도 `end_edit` 은 `xform` 으로 **명시적으로** 스냅하므로 결과는 같다.
    되켜는 것은 스냅이 끝난 **뒤**다 — 그때는 이미 핸들이 이펙터에 있어 아무 일도 안 난다.
    """
    saved = {}
    for h in handles:
        plug = h + ".snapEnable"
        if not cmds.objExists(plug) or not su.plug_writable(plug):
            continue
        try:
            saved[h] = cmds.getAttr(plug)
            cmds.setAttr(plug, 0)
        except Exception:
            saved.pop(h, None)
    return saved


def _snap_restore(saved):
    for h, value in (saved or {}).items():
        plug = h + ".snapEnable"
        if cmds.objExists(plug) and su.plug_writable(plug):
            try:
                cmds.setAttr(plug, value)
            except Exception:
                pass


def begin(handles):
    """IK 를 끄고 스냅샷을 남긴다. `(session, messages)`.

    `session` 은 `end()` / `cancel()` 에 그대로 넘긴다. 비어 있으면 세션이 안 열린 것이다.

    A00060 의 `begin_edit` 을 그대로 쓴다 — 핸들에 상태를 써 두므로 세션이 끊겨도
    나중에 되찾을 수 있다.
    """
    messages = []
    session = {"handles": [], "snap": {}}
    if not handles:
        return session, messages

    ok, pre = preflight(handles)
    messages.extend(pre)
    if not ok:
        return session, messages

    session["snap"] = _snap_off(ok)
    messages.extend("[IK] " + m for m in ike.begin_edit(ok))
    session["handles"] = [h for h in ok if ike.is_editing(h)]

    if session["handles"]:
        messages.append("[OK] IK edit mode ON for {0} handle(s) - the chain joints can "
                        "be moved now.".format(len(session["handles"])))
    else:
        _snap_restore(session["snap"])
        session["snap"] = {}
        messages.append("[Warning] No handle entered edit mode - the chains will not "
                        "move. See the messages above.")
    return session, messages


def end(session):
    """핸들과 폴 벡터를 편집된 체인에 맞추고 IK 를 되켠다. `(results, messages)`."""
    messages = []
    handles = (session or {}).get("handles") or []
    if not handles:
        return [], messages

    results, msgs = ike.end_edit(handles)
    messages.extend("[IK] " + m for m in msgs)

    # 스냅이 끝난 뒤에 되켠다 (위 _snap_off 주석)
    _snap_restore(session.get("snap"))

    worst_t = max([r[1] for r in results] or [0.0])
    worst_r = max([r[2] for r in results] or [0.0])
    messages.append(
        "[OK] IK edit mode OFF for {0} handle(s) - handles and pole vectors follow the "
        "chain (worst deviation {1:.4f} / {2:.4f} deg).".format(
            len(results), worst_t, worst_r))
    return results, messages


def cancel(session):
    """편집 시작 시점으로 되돌리고 IK 를 되켠다. 매칭 중 예외가 났을 때 쓴다."""
    messages = []
    handles = (session or {}).get("handles") or []
    if not handles:
        return messages
    messages.extend("[IK] " + m for m in ike.cancel_edit(handles))
    _snap_restore(session.get("snap"))
    messages.append(
        "[Warning] The match was aborted, so the IK chains were put back the way they "
        "were and IK was turned on again.")
    return messages


def stranded_handles(handles):
    """아직 편집 모드에 남아 있는 핸들 (지난 실행이 끊겼을 때).

    A00060 은 편집 상태를 **핸들의 어트리뷰트에** 남기므로, 세션이 비정상 종료돼도
    씬에 흔적이 남는다. 다음 Match 에서 그걸 발견하면 알린다.
    """
    return [h for h in handles if cmds.objExists(h) and ike.is_editing(h)]
