# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00110_animTool - 컨트롤러 키프레임을 반대쪽 컨트롤러로 좌우 미러하는 핵심 로직 (maya.cmds + OpenMaya 2.0, UI 비의존)
#
# 언리얼 Mirror Data Table 과 동일하게, 한쪽 컨트롤의 애니메이션을 좌우 대칭으로 반대쪽에 복사한다.
# rotateOrder 무관:  소스는 worldMatrix 로 읽고(오일러 무관), 결과는 타겟 rotateOrder 로 재분해해 기록한다.
#   - 채널 부호 반전 방식은 rotateOrder/축 정렬에 의존하므로 쓰지 않는다.
#   - 월드 매트릭스를 반사축 기준으로 반사(reflection conjugation)한 뒤 타겟 로컬로 변환한다.
#
# 두 가지 미러 모드:
#   - behavior (기본): 소스의 로컬 채널 값(translate/rotate)을 타겟에 그대로 복사한다.
#     Maya mirror joints 의 Behavior 세팅으로 만든 좌우 축 반전 리그는 컨트롤러 자체가 거울상으로
#     정렬돼 있어, 로컬 채널 값을 그대로 복사하면 대칭 포즈가 된다(반사축 무관).
#     예: rotateOrder zxy (-10,-3,-50) -> 타겟도 (-10,-3,-50).
#   - orientation (기존): 순수 월드 반사(반사축 사용). Mt_world = refl * Ms * refl.

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

from .mirror_token_store import MirrorTokenStore


class MirrorKeyManager:
    """
    소스 컨트롤의 키를 타겟 컨트롤로 미러한다.

    pose_key_manager / copykey_manager 와 동일한 스타일:
    정적 메서드 + undoInfo 청크 + (count, msg) 반환.
    """

    # 미러 대상 채널 (UI 토글 키 -> attr). translate / rotate 그룹.
    T_AXES = [("tx", "translateX"), ("ty", "translateY"), ("tz", "translateZ")]
    R_AXES = [("rx", "rotateX"), ("ry", "rotateY"), ("rz", "rotateZ")]

    # rotateOrder int(0..5) -> MEulerRotation order enum. (값은 0..5 로 동일하지만 명시적으로 매핑)
    RO_ENUM = [
        om.MEulerRotation.kXYZ,  # 0
        om.MEulerRotation.kYZX,  # 1
        om.MEulerRotation.kZXY,  # 2
        om.MEulerRotation.kXZY,  # 3
        om.MEulerRotation.kYXZ,  # 4
        om.MEulerRotation.kZYX,  # 5
    ]

    # 토큰 폴백(JSON 을 못 읽을 때). 권장 진입점은 MirrorTokenStore.load().
    DEFAULT_TOKEN_PAIRS = MirrorTokenStore.DEFAULT_TOKEN_PAIRS

    # --------------------------------------------------
    # 페어링
    # --------------------------------------------------

    @staticmethod
    def resolve_pairs(controls, token_pairs):
        """
        controls 의 각 컨트롤에 대해 반대쪽 컨트롤을 토큰으로 찾는다.

        controls    : 컨트롤 이름 리스트(보통 현재 선택). 선택 순서가 우선순위.
        token_pairs : [(left, right), ...]. 위→아래 순서가 매칭 우선순위.

        반환: (pairs, unpaired, center)
            pairs    : [(src, tgt), ...]  실제 미러 실행 대상(센터는 (ctrl, ctrl))
            unpaired : 토큰은 있으나 반대쪽 노드가 씬에 없는 컨트롤
            center   : 좌/우 토큰이 없어 self-mirror 로 처리한 컨트롤

        양쪽(L,R)을 모두 선택해도 한 방향만 처리한다(먼저 본 쪽이 소스). 이렇게 해야
        L->R 기록이 R->L 읽기를 오염시키는 스왑 문제를 피한다.
        """
        pairs = []
        unpaired = []
        center = []
        claimed = set()

        for ctrl in controls:
            if ctrl in claimed:
                continue

            opp, had_token = MirrorKeyManager._find_opposite(ctrl, token_pairs)

            if opp:
                pairs.append((ctrl, opp))
                claimed.add(ctrl)
                claimed.add(opp)
            elif had_token:
                # 토큰은 매칭됐는데 반대쪽 노드가 없음
                unpaired.append(ctrl)
                claimed.add(ctrl)
            else:
                # 좌/우 토큰 없음 -> 센터 컨트롤. self-mirror.
                center.append(ctrl)
                pairs.append((ctrl, ctrl))
                claimed.add(ctrl)

        return (pairs, unpaired, center)

    @staticmethod
    def _find_opposite(name, token_pairs):
        """
        name 에서 토큰을 치환해 반대쪽 후보 이름을 만들고, 씬에 존재하는 첫 후보를 반환.

        substring 치환이라 '_l' 이 'arm_lower' 같은 이름에 걸릴 수 있으나,
        objExists 로 거르므로 실제로 존재하는 노드만 페어가 된다.
        반환: (opposite_name 또는 None, had_token)
            had_token : 토큰 substring 이 하나라도 매칭됐는지(센터 판별용)
        """
        had_token = False

        for left, right in token_pairs:
            for a, b in ((left, right), (right, left)):
                start = 0
                while True:
                    idx = name.find(a, start)
                    if idx == -1:
                        break
                    had_token = True
                    cand = name[:idx] + b + name[idx + len(a):]
                    if cand != name and cmds.objExists(cand):
                        return (cand, True)
                    start = idx + 1

        return (None, had_token)

    # --------------------------------------------------
    # 미러 실행
    # --------------------------------------------------

    @staticmethod
    def mirror_keys(pairs, start, end, mirror_axis="x",
                    do_translate=True, do_rotate=True, time_mode="source_keys",
                    behavior=True):
        """
        pairs 의 각 (src, tgt) 에 대해 [start, end] 구간 키를 미러한다.

        mirror_axis  : "x" | "y" | "z" (월드 반사축. 기본 x = YZ 평면)
        do_translate : translate 3축 미러 여부
        do_rotate    : rotate 3축 미러 여부
        time_mode    : "source_keys"(소스 키 시점에만 기록) | "bake"(정수 프레임 전수)
        behavior     : True(기본) = 소스 로컬 채널 값을 타겟에 그대로 복사(반사 무관),
                       False = 순수 월드 반사(orientation)
        반환         : (처리한 페어 수, 메시지)
        """
        if not pairs:
            return (0, "[Warning] No pairs to mirror.")

        if not do_translate and not do_rotate:
            return (0, "[Warning] Enable Translate and/or Rotate.")

        refl = MirrorKeyManager._reflection_matrix(mirror_axis)

        done = 0
        skipped = 0

        cmds.undoInfo(openChunk=True)
        try:
            for src, tgt in pairs:
                ok = MirrorKeyManager._mirror_one(
                    src, tgt, start, end, refl, do_translate, do_rotate, time_mode,
                    behavior)
                if ok:
                    done += 1
                else:
                    skipped += 1
        finally:
            cmds.undoInfo(closeChunk=True)

        msg = "{0} pair(s) mirrored (axis: {1}).".format(done, mirror_axis.upper())
        if skipped:
            msg += " {0} skipped (no keys / not settable).".format(skipped)

        return (done, msg)

    @staticmethod
    def _mirrored_values(src, tgt, t, refl, do_t, do_r, behavior=True):
        """시점 t 에서 src 를 미러해 타겟 로컬 TRS(dict: attr -> value)를 반환.

        behavior=True(기본): 소스의 로컬 채널 값을 타겟에 그대로 복사한다(반사·행렬 연산 없음).
            Maya `mirror joints` 의 Behavior 세팅으로 만든 좌우 축 반전 리그는 컨트롤러 자체가
            거울상으로 정렬돼 있어, 로컬 채널 값을 그대로 복사하면 대칭 포즈가 된다.
            (예: rotateOrder zxy (-10,-3,-50) -> 타겟도 (-10,-3,-50)). 반사축에 무관.
        behavior=False: 순수 월드 반사(반사축 사용). 소스는 worldMatrix(rotateOrder 무관)로 읽고,
            refl * Ms * refl 후 타겟 parentInverseMatrix 로 로컬화, 타겟 rotateOrder 로 재분해한다.
        """
        if behavior:
            # 로컬 채널 값 그대로 복사. 좌우 대칭은 리그(컨트롤러 거울상 정렬)에 내장돼 있다.
            values = {}
            if do_t:
                for _, attr in MirrorKeyManager.T_AXES:
                    values[attr] = cmds.getAttr(src + "." + attr, time=t)
            if do_r:
                for _, attr in MirrorKeyManager.R_AXES:
                    values[attr] = cmds.getAttr(src + "." + attr, time=t)
            return values

        ms = om.MMatrix(cmds.getAttr(src + ".worldMatrix[0]", time=t))
        world = refl * ms * refl

        mpi = om.MMatrix(cmds.getAttr(tgt + ".parentInverseMatrix[0]", time=t))

        # 타겟 로컬로: local = world * parentInverse
        tm = om.MTransformationMatrix(world * mpi)

        values = {}
        if do_t:
            tr = tm.translation(om.MSpace.kTransform)
            values["translateX"] = tr.x
            values["translateY"] = tr.y
            values["translateZ"] = tr.z
        if do_r:
            ro = cmds.getAttr(tgt + ".rotateOrder")
            eul = tm.rotation(asQuaternion=True).asEulerRotation()
            eul.reorderIt(MirrorKeyManager.RO_ENUM[ro])  # 타겟 rotateOrder 로 재정렬
            # MEulerRotation 은 라디안 -> rotate attr 은 degree
            values["rotateX"] = math.degrees(eul.x)
            values["rotateY"] = math.degrees(eul.y)
            values["rotateZ"] = math.degrees(eul.z)
        return values

    @staticmethod
    def _settable_attrs(tgt, do_t, do_r):
        """기록 대상 attr(잠긴 채널 제외)."""
        attrs = []
        if do_t:
            attrs += [a for _, a in MirrorKeyManager.T_AXES]
        if do_r:
            attrs += [a for _, a in MirrorKeyManager.R_AXES]
        return [a for a in attrs if MirrorKeyManager._is_settable(tgt, a)]

    @staticmethod
    def _has_time_anim(tgt, attr):
        """attr 에 time 애니메이션 커브(animCurveT*)가 연결돼 있는지. set-driven-key(animCurveU*) 제외."""
        curves = cmds.keyframe(tgt, attribute=attr, query=True, name=True) or []
        return any(cmds.nodeType(c).startswith("animCurveT") for c in curves)

    @staticmethod
    def _mirror_one(src, tgt, start, end, refl, do_t, do_r, time_mode, behavior=True):
        """src -> tgt 단일 페어 미러. 키 하나라도 기록했으면 True."""

        times = MirrorKeyManager._collect_times(src, start, end, time_mode)
        if not times:
            return False

        attrs = MirrorKeyManager._settable_attrs(tgt, do_t, do_r)
        if not attrs:
            return False

        any_set = False

        for t in times:
            values = MirrorKeyManager._mirrored_values(src, tgt, t, refl, do_t, do_r, behavior)
            for attr in attrs:
                try:
                    cmds.setKeyframe(tgt + "." + attr, time=t, value=values[attr])
                    any_set = True
                except Exception:
                    # 연결/잠금 등으로 키 불가한 채널은 건너뜀
                    pass

        return any_set

    # --------------------------------------------------
    # 현재 프레임만 미러 (autoKeyframe 재현)
    # --------------------------------------------------

    @staticmethod
    def mirror_current_frame(pairs, mirror_axis="x", do_translate=True, do_rotate=True,
                             tol=1e-6, per_object=False, behavior=True):
        """
        현재 프레임의 포즈만 각 (src, tgt) 로 미러한다. (구간 베이크 아님)

        키잉은 autoKeyframe 규칙을 재현한다(전역 autoKeyframe 상태는 건드리지 않음):
          - per_object=False (기본, per-channel/auto-key):
              채널에 time 애니메이션 커브가 있고 값이 바뀌면 -> 현재 프레임에 setKeyframe.
              커브가 없던 채널 -> setAttr 로 포즈만(키 생성 안 함).
          - per_object=True (per-object):
              타겟의 대상 채널 중 하나라도 애니메이션이 있으면 -> 대상 채널 전부 현재 프레임에 키.
              전혀 없으면 -> 전부 setAttr(포즈만).

        mirror_axis  : "x" | "y" | "z"
        tol          : 값 변경 판정 임계값(per-channel 모드에서 사용).
        반환         : (처리한 페어 수, 메시지)
        """
        if not pairs:
            return (0, "[Warning] No pairs to mirror.")
        if not do_translate and not do_rotate:
            return (0, "[Warning] Enable Translate and/or Rotate.")

        refl = MirrorKeyManager._reflection_matrix(mirror_axis)
        cur = cmds.currentTime(q=True)

        done = skipped = keyed = posed = 0

        cmds.undoInfo(openChunk=True)
        try:
            for src, tgt in pairs:
                attrs = MirrorKeyManager._settable_attrs(tgt, do_translate, do_rotate)
                if not attrs:
                    skipped += 1
                    continue

                values = MirrorKeyManager._mirrored_values(
                    src, tgt, cur, refl, do_translate, do_rotate, behavior)

                # per-object 모드: 대상 채널 중 하나라도 애니가 있으면 오브젝트를 "keyed" 로 취급.
                obj_anim = False
                if per_object:
                    obj_anim = any(
                        MirrorKeyManager._has_time_anim(tgt, a) for a in attrs)

                touched = False
                for attr in attrs:
                    v = values[attr]
                    full = tgt + "." + attr
                    try:
                        if per_object:
                            key_it = obj_anim
                        else:
                            key_it = (MirrorKeyManager._has_time_anim(tgt, attr)
                                      and abs(cmds.getAttr(full) - v) > tol)

                        if key_it:
                            cmds.setKeyframe(tgt, attribute=attr, time=cur, value=v)
                            keyed += 1
                            touched = True
                        elif not MirrorKeyManager._has_time_anim(tgt, attr):
                            # 키 없던 채널 -> 포즈만(setAttr), 키 생성 안 함
                            cmds.setAttr(full, v)
                            posed += 1
                            touched = True
                        # per-channel 인데 has_anim 이고 값 미변경이면 no-op
                    except Exception:
                        # 잠금/연결 등으로 실패한 채널은 건너뜀
                        pass

                if touched:
                    done += 1
                else:
                    skipped += 1
        finally:
            cmds.undoInfo(closeChunk=True)

        msg = "{0} pair(s) mirrored at frame {1} (axis: {2}; keyed {3}, posed {4}).".format(
            done, int(cur), mirror_axis.upper(), keyed, posed)
        if skipped:
            msg += " {0} skipped.".format(skipped)
        return (done, msg)

    # --------------------------------------------------
    # 헬퍼
    # --------------------------------------------------

    @staticmethod
    def _reflection_matrix(axis):
        """반사축에 따른 4x4 반사 행렬(MMatrix). 기본 x."""
        s = [1.0, 1.0, 1.0]
        idx = {"x": 0, "y": 1, "z": 2}.get((axis or "x").lower(), 0)
        s[idx] = -1.0
        return om.MMatrix([
            s[0], 0.0, 0.0, 0.0,
            0.0, s[1], 0.0, 0.0,
            0.0, 0.0, s[2], 0.0,
            0.0, 0.0, 0.0, 1.0,
        ])

    @staticmethod
    def _collect_times(src, start, end, time_mode):
        """미러 대상 시점 목록. source_keys = 소스 키 시점 union, bake = 정수 프레임 전수."""
        if time_mode == "bake":
            return list(range(int(math.floor(start)), int(math.ceil(end)) + 1))

        times = cmds.keyframe(src, q=True, time=(start, end), timeChange=True) or []
        return sorted(set(times))

    @staticmethod
    def _is_settable(node, attr):
        """채널이 잠겨있지 않은지(키 설정 가능 후보)."""
        try:
            return not cmds.getAttr(node + "." + attr, lock=True)
        except Exception:
            return False
