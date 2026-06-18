# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00110_animTool - 여러 follower 를 인덱스로 매칭된 target 의 월드 transform 에 맞춰 구간 키 베이크
#                   (maya.cmds + OpenMaya 2.0, UI 비의존)
#
# parentConstraint(maintainOffset=False) 를 컨스트레인트 없이 키로 확정하는 것과 동등하다.
#   - 각 (target, follower) 페어에 대해 [start, end] 정수 프레임마다 follower 가 target 의
#     월드 위치/회전(/스케일)과 "동일"해지도록 follower 로컬 채널에 키를 굽는다.
#   - rotateOrder 무관: target worldMatrix 로 읽고, follower parentInverseMatrix 로 로컬화한 뒤
#     follower 자신의 rotateOrder 로 재분해한다(mirror_key_manager 의 검증된 경로 재사용).
#   - blend(0..1) 는 키 값에 직접 베이크한다(레이어 weight 는 1 유지).
#       0 = 원본 유지, 1 = 매치로 덮어쓰기, 0.5 = 원본과 매치를 반반.
#       회전은 쿼터니언 slerp, 위치/스케일은 선형 lerp 로 섞는다.
#   - 애니메이션 레이어가 선택돼 있으면 그 레이어에 키를 굽는다(override / additive 모두 처리).

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

from .mirror_key_manager import MirrorKeyManager


class FollowMatchManager:
    """
    follower 리스트를 같은 인덱스의 target 리스트에 월드 transform 으로 추종시켜 키를 굽는다.

    다른 manager 와 동일 스타일: 정적 메서드 + undoInfo 청크 + (count, msg) 반환.
    """

    # rotateOrder int(0..5) -> MEulerRotation order enum. mirror_key_manager 의 테이블 재사용.
    RO_ENUM = MirrorKeyManager.RO_ENUM

    # 채널 -> 로컬 attr(긴 이름). scale 은 호출부에서 do_scale 로 켤 때만 포함.
    T_ATTRS = ["translateX", "translateY", "translateZ"]
    R_ATTRS = ["rotateX", "rotateY", "rotateZ"]
    S_ATTRS = ["scaleX", "scaleY", "scaleZ"]

    # --------------------------------------------------
    # 공개 진입점
    # --------------------------------------------------

    @staticmethod
    def match_follow(targets, followers, start, end, blend,
                     do_translate=True, do_rotate=True, do_scale=False):
        """
        targets[i] 의 월드 transform 에 followers[i] 를 맞춰 [start, end] 구간 키를 굽는다.

        targets, followers : 같은 길이의 노드 이름 리스트(인덱스로 1:1 매칭).
        start, end         : 정수 프레임 구간(포함).
        blend              : 0..1. 0=원본 유지, 1=매치 덮어쓰기, 0.5=반반.
        do_translate / do_rotate / do_scale : 매칭/블렌드 채널 그룹.
        반환               : (matched_count, msg)
        """
        if not targets or not followers:
            return (0, "[Warning] Fill both Target and Follower lists.")
        if len(targets) != len(followers):
            return (0, "[Warning] Target ({0}) / Follower ({1}) count mismatch.".format(
                len(targets), len(followers)))
        if start > end:
            return (0, "[Warning] Start ({0}) is greater than End ({1}).".format(start, end))
        if not (do_translate or do_rotate or do_scale):
            return (0, "[Warning] Enable at least one channel group.")

        try:
            blend = float(blend)
        except (TypeError, ValueError):
            return (0, "[Warning] Invalid blend value.")
        blend = max(0.0, min(1.0, blend))
        if blend == 0.0:
            return (0, "[Info] Blend is 0; follower animation unchanged.")

        layer, is_override, layer_msg = FollowMatchManager._resolve_layer()

        times = list(range(int(math.floor(start)), int(math.ceil(end)) + 1))

        done = 0
        skipped = 0

        cur = cmds.currentTime(q=True)
        cmds.undoInfo(openChunk=True)
        cmds.refresh(suspend=True)
        try:
            for tgt, flw in zip(targets, followers):
                ok = FollowMatchManager._match_one(
                    tgt, flw, times, blend, do_translate, do_rotate, do_scale,
                    layer, is_override)
                if ok:
                    done += 1
                else:
                    skipped += 1
        finally:
            # 예외가 나도 뷰포트 억제 해제 / 프레임 복원 / undo 청크 닫기를 반드시 수행
            cmds.refresh(suspend=False)
            cmds.currentTime(cur, edit=True)
            cmds.undoInfo(closeChunk=True)

        frames = len(times)
        msg = "{0} follower(s) matched over [{1}-{2}] ({3} frames, blend {4}). {5}".format(
            done, start, end, frames, blend, layer_msg)
        if skipped:
            msg += " {0} skipped (no settable channels / no node).".format(skipped)
        return (done, msg)

    # --------------------------------------------------
    # 페어 1개 처리 (2-pass: 원본 읽기 -> 매치 쓰기)
    # --------------------------------------------------

    @staticmethod
    def _match_one(tgt, flw, times, blend, do_t, do_r, do_s, layer, is_override):
        """단일 (tgt, flw) 페어를 굽는다. 키를 하나라도 기록했으면 True."""
        if not cmds.objExists(tgt) or not cmds.objExists(flw):
            return False

        ro = cmds.getAttr(flw + ".rotateOrder")
        order = FollowMatchManager.RO_ENUM[ro]

        attrs = FollowMatchManager._settable_attrs(flw, do_t, do_r, do_s)
        if not attrs:
            return False

        additive = (layer is not None) and (not is_override)

        # 레이어 멤버십 보장 (override/additive 모두 멤버여야 키가 레이어로 들어간다)
        if layer is not None:
            for a in attrs:
                try:
                    cmds.animLayer(layer, edit=True, attribute=flw + "." + a)
                except Exception:
                    pass

        # blend==1 이고 override(=base 포함)면 원본 O 가 필요 없다 -> 단일 쓰기 패스.
        full = (blend >= 1.0) and is_override

        # ---- Pass 1: 원본 평가값 O (+ additive 면 base B) 읽기 ----
        orig = {}
        if not full:
            for t in times:
                orig[t] = FollowMatchManager._read_state(flw, t, do_t, do_r, do_s, order)

        base = {}
        if additive and not full:
            # 레이어를 뮤트해 base(레이어 기여 제외) 를 읽는다. 끝나면 원상 복구.
            prev_mute = bool(cmds.animLayer(layer, q=True, mute=True))
            try:
                cmds.animLayer(layer, edit=True, mute=True)
                for t in times:
                    base[t] = FollowMatchManager._read_state(flw, t, do_t, do_r, do_s, order)
            finally:
                cmds.animLayer(layer, edit=True, mute=prev_mute)

        # ---- Pass 2: 매치 M 계산 -> blend -> 레이어 모드별 값 V 기록 ----
        any_set = False
        for t in times:
            m_state = FollowMatchManager._matched_state(tgt, flw, t, do_t, do_r, do_s)

            if full:
                values = FollowMatchManager._values_from_state(m_state, do_t, do_r, do_s, order)
            else:
                f_state = FollowMatchManager._blend_state(
                    orig[t], m_state, blend, do_t, do_r, do_s)
                if additive:
                    values = FollowMatchManager._additive_values(
                        base[t], f_state, do_t, do_r, do_s, order)
                else:
                    values = FollowMatchManager._values_from_state(
                        f_state, do_t, do_r, do_s, order)

            for a in attrs:
                if a not in values:
                    continue
                try:
                    if layer is not None:
                        cmds.setKeyframe(flw, attribute=a, time=t, value=values[a],
                                         animLayer=layer)
                    else:
                        cmds.setKeyframe(flw, attribute=a, time=t, value=values[a])
                    any_set = True
                except Exception:
                    # 잠금/연결 등으로 키 불가한 채널은 건너뜀
                    pass

        return any_set

    # --------------------------------------------------
    # 상태(state) 읽기 / 계산
    #   state = {"t": (x,y,z), "q": MQuaternion, "s": (x,y,z)} (켜진 채널만 존재)
    # --------------------------------------------------

    @staticmethod
    def _read_state(node, t, do_t, do_r, do_s, order):
        """node 의 시점 t 로컬 채널 값을 state 로 읽는다(현재 씬/레이어 평가)."""
        st = {}
        if do_t:
            st["t"] = (
                cmds.getAttr(node + ".translateX", time=t),
                cmds.getAttr(node + ".translateY", time=t),
                cmds.getAttr(node + ".translateZ", time=t),
            )
        if do_r:
            rx = cmds.getAttr(node + ".rotateX", time=t)
            ry = cmds.getAttr(node + ".rotateY", time=t)
            rz = cmds.getAttr(node + ".rotateZ", time=t)
            eul = om.MEulerRotation(
                math.radians(rx), math.radians(ry), math.radians(rz), order)
            st["q"] = eul.asQuaternion()
        if do_s:
            st["s"] = (
                cmds.getAttr(node + ".scaleX", time=t),
                cmds.getAttr(node + ".scaleY", time=t),
                cmds.getAttr(node + ".scaleZ", time=t),
            )
        return st

    @staticmethod
    def _matched_state(tgt, flw, t, do_t, do_r, do_s):
        """target 의 월드 transform 을 follower 로컬로 변환한 state. rotateOrder 무관.

        local = worldMatrix(tgt) * parentInverseMatrix(flw). offset 0(정확히 일치).
        """
        ms = om.MMatrix(cmds.getAttr(tgt + ".worldMatrix[0]", time=t))
        mpi = om.MMatrix(cmds.getAttr(flw + ".parentInverseMatrix[0]", time=t))
        tm = om.MTransformationMatrix(ms * mpi)

        st = {}
        if do_t:
            tr = tm.translation(om.MSpace.kTransform)
            st["t"] = (tr.x, tr.y, tr.z)
        if do_r:
            st["q"] = tm.rotation(asQuaternion=True)
        if do_s:
            sc = tm.scale(om.MSpace.kTransform)
            st["s"] = (sc[0], sc[1], sc[2])
        return st

    @staticmethod
    def _blend_state(o_state, m_state, blend, do_t, do_r, do_s):
        """원본 O 와 매치 M 을 blend 로 섞은 최종 state F.
        위치/스케일은 선형 lerp, 회전은 쿼터니언 slerp(최단호)."""
        st = {}
        if do_t:
            ot, mt = o_state["t"], m_state["t"]
            st["t"] = tuple(o + (m - o) * blend for o, m in zip(ot, mt))
        if do_r:
            st["q"] = FollowMatchManager._slerp(o_state["q"], m_state["q"], blend)
        if do_s:
            os_, ms_ = o_state["s"], m_state["s"]
            st["s"] = tuple(o + (m - o) * blend for o, m in zip(os_, ms_))
        return st

    @staticmethod
    def _values_from_state(st, do_t, do_r, do_s, order):
        """state -> {attr: value}. 회전 쿼터니언은 follower rotateOrder 로 분해."""
        values = {}
        if do_t and "t" in st:
            values["translateX"], values["translateY"], values["translateZ"] = st["t"]
        if do_r and "q" in st:
            eul = st["q"].asEulerRotation()
            eul.reorderIt(order)
            values["rotateX"] = math.degrees(eul.x)
            values["rotateY"] = math.degrees(eul.y)
            values["rotateZ"] = math.degrees(eul.z)
        if do_s and "s" in st:
            values["scaleX"], values["scaleY"], values["scaleZ"] = st["s"]
        return values

    @staticmethod
    def _additive_values(b_state, f_state, do_t, do_r, do_s, order):
        """additive 레이어용 레이어-로컬 값. 평가값 = base(B) + layer(V) 가 최종 F 가 되도록.
        translate = F - B, rotate = B^-1 * F(회전 합성), scale = F / B(스케일은 곱).
        """
        values = {}
        if do_t:
            bt, ft = b_state["t"], f_state["t"]
            values["translateX"] = ft[0] - bt[0]
            values["translateY"] = ft[1] - bt[1]
            values["translateZ"] = ft[2] - bt[2]
        if do_r:
            q_layer = b_state["q"].inverse() * f_state["q"]
            eul = q_layer.asEulerRotation()
            eul.reorderIt(order)
            values["rotateX"] = math.degrees(eul.x)
            values["rotateY"] = math.degrees(eul.y)
            values["rotateZ"] = math.degrees(eul.z)
        if do_s:
            bs, fs = b_state["s"], f_state["s"]
            values["scaleX"] = fs[0] / bs[0] if bs[0] else fs[0]
            values["scaleY"] = fs[1] / bs[1] if bs[1] else fs[1]
            values["scaleZ"] = fs[2] / bs[2] if bs[2] else fs[2]
        return values

    # --------------------------------------------------
    # 헬퍼
    # --------------------------------------------------

    @staticmethod
    def _resolve_layer():
        """키를 구울 애니메이션 레이어 결정.
        반환: (layer 또는 None, is_override, msg)
            layer=None  -> 레이어 인자 없이 베이스 커브에 키.
            is_override -> True 면 override(또는 base) 공식, False 면 additive 공식.

        주의: animLayer 에는 "선택된 레이어 목록"을 주는 전역 쿼리가 없다. -selected 는
        레이어 이름을 인자로 줘야 그 레이어의 선택 여부(bool)를 돌려주는 per-layer 쿼리다.
        그래서 전체 레이어를 나열한 뒤 각각 selected 를 검사한다.
        """
        layers = cmds.ls(type="animLayer") or []
        if not layers:
            return (None, True, "No anim layers; keys on base curves.")

        root = cmds.animLayer(q=True, root=True)

        selected = []
        for lyr in layers:
            try:
                if cmds.animLayer(lyr, q=True, selected=True):
                    selected.append(lyr)
            except Exception:
                pass

        if not selected:
            return (None, True, "No anim layer selected; keys on base curves.")

        # BaseAnimation(root) 은 override/additive 개념 밖 -> 베이스 커브로 처리.
        non_base = [lyr for lyr in selected if lyr != root]
        if not non_base:
            return (None, True, "BaseAnimation selected; keys on base curves.")

        layer = non_base[0]
        override = bool(cmds.animLayer(layer, q=True, override=True))
        msg = "Layer '{0}' ({1}).".format(layer, "override" if override else "additive")
        if len(non_base) > 1:
            msg += " ({0} layers selected, using first).".format(len(non_base))
        return (layer, override, msg)

    @staticmethod
    def _settable_attrs(node, do_t, do_r, do_s):
        """기록 대상 attr(잠긴 채널 제외). mirror_key_manager._is_settable 재사용."""
        attrs = []
        if do_t:
            attrs += FollowMatchManager.T_ATTRS
        if do_r:
            attrs += FollowMatchManager.R_ATTRS
        if do_s:
            attrs += FollowMatchManager.S_ATTRS
        return [a for a in attrs if MirrorKeyManager._is_settable(node, a)]

    @staticmethod
    def _slerp(q0, q1, blend):
        """쿼터니언 최단호 보간(version-independent). blend 0..1."""
        dot = q0.x * q1.x + q0.y * q1.y + q0.z * q1.z + q0.w * q1.w
        # 최단 경로 보장(부호 뒤집기)
        if dot < 0.0:
            q1 = om.MQuaternion(-q1.x, -q1.y, -q1.z, -q1.w)
            dot = -dot
        # 거의 동일하면 선형 보간 후 정규화(수치 안정)
        if dot > 0.9995:
            r = om.MQuaternion(
                q0.x + (q1.x - q0.x) * blend,
                q0.y + (q1.y - q0.y) * blend,
                q0.z + (q1.z - q0.z) * blend,
                q0.w + (q1.w - q0.w) * blend,
            )
            return r.normal()
        theta_0 = math.acos(max(-1.0, min(1.0, dot)))
        theta = theta_0 * blend
        sin_0 = math.sin(theta_0)
        s0 = math.sin(theta_0 - theta) / sin_0
        s1 = math.sin(theta) / sin_0
        return om.MQuaternion(
            s0 * q0.x + s1 * q1.x,
            s0 * q0.y + s1 * q1.y,
            s0 * q0.z + s1 * q1.z,
            s0 * q0.w + s1 * q1.w,
        )
