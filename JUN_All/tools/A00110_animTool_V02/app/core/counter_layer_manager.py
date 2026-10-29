# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00110_animTool_V02 - Bake > Counter Layer : 상위 레이어가 바꾼 자식의 월드 위치·회전을 되돌리는 보정 레이어 (maya.cmds + om2, UI 비의존)
#
# "global_ctl > foot_l_ctl, foot_r_ctl. 발은 additive 레이어 lyr_01..n 에 키. global_ctl 만 든 lyr_glo 에
#  키를 찍으면 발의 **월드**가 바뀐다. lyr_glo 는 그대로 두고, 발의 월드 위치·회전이 lyr_glo 가 있기 전과
#  같아지도록 발에 키를 찍은 **새 레이어 하나**를 만든다."
#
# 계획서 : docs/plans/A00110_animTool_V02_counter_layer_plan.md (mayapy 실측 21/21 이 설계의 근거)
#
# ## 왜 마야 기능으로 안 되나
# `bakeResults -resolveWithoutLayer` 는 **어트리뷰트 단위**다. 발의 tx..rz 는 lyr_glo 전후 값이 같다 -
# 바뀐 것은 **부모**다. 그래서 월드 행렬을 직접 재야 한다.
#
# ## 알고리즘 (두 번 훑기)
#   1) 되돌릴 레이어들을 **뮤트**하고 프레임마다 발의 worldMatrix 를 기록한다 (= 목표 월드, "있기 전").
#   2) 뮤트를 풀고 프레임마다 `xform -ws -m <목표>` 로 발을 목표 월드에 놓은 뒤 로컬 T/R 을 읽어,
#      새 additive 레이어에 `setKeyframe -animLayer L -value V` 로 찍는다. 이 명령은 **"그 plug 의 최종
#      평가값이 V 가 되도록 L 의 커브 값을 역산"** 하므로, 레이어 누적 모드(by-layer / by-component) ·
#      가중치 · 아래 override 레이어 · jointOrient · 회전 순서 · 피벗을 **우리가 계산하지 않는다**
#      (`xform -m` 이 분해를, `setKeyframe -animLayer` 가 레이어 역산을 맡는다).
#   회전의 **동치해 선택만** 우리 일이다 - `alternateSolution` + `setToClosestCut(지금 로컬 회전)`
#   (`closestSolution` 은 짐벌 근처에서 다른 회전이 된다 - euler-closest-solution-not-equivalent).
#
# ## 메모리 - 긴 구간(1000+ 프레임)
# 스냅샷을 구간 전체로 들고 있으면 오브젝트 x 프레임 x 16 double 이 쌓인다(50 ctl x 3000 f 면 수십 MB).
# 그래서 **프레임을 청크(CHUNK_FRAMES)로 나눠 "뮤트 -> 청크 스냅샷 -> 뮤트 해제 -> 청크 쓰기 -> 버림"**
# 을 반복한다. 메모리 상한 = 청크 x 오브젝트 x 16 double (array 'd') 로 구간 길이와 무관하다.
#   * 청크 2 부터는 보정 레이어에 이미 앞 청크의 키가 있어 그 커브가 **끝값을 외삽**한다 - 스냅샷 때
#     보정 레이어도 함께 뮤트해야 "있기 전" 이 오염되지 않는다.
#   * 레이어 mute 토글은 싸다(청크마다 2회). 쓰기 비용(오브젝트·프레임당 ~0.9 ms)이 지배적이다.
#
# ## 실측으로 확인한 함정 (계획서 §4)
#   - 드라이버 키 프레임에만 키를 찍는 희소 모드는 **0.95 유닛** 틀린다 -> 매 프레임이 기본(step=1).
#   - 잠긴 채널은 `animLayer -at` · `xform` · `setKeyframe`(반환 0) 이 **전부 조용히 지나간다** -> 사전 검사.
#   - `xform` 은 setAttr 라 GUI 에서 Auto Keyframe 이 켜져 있으면 활성 레이어에 자체 키가 생긴다 -> 실행 중 끈다.
#   - `getAttr(time=)` 스냅샷은 값은 같지만 currentTime 루프보다 3 배 느리다 -> currentTime 루프.

# ## v02.29 - Hold 모드 "Stationary spans only" (계획서 docs/plans/A00110_animTool_V02_counter_layer_stationary_plan.md)
# Everywhere(기존)는 모든 프레임에서 월드를 "있기 전" 으로 되돌린다 - 발이 처음 자리로 돌아가 버린다.
# Stationary 는 **되돌릴 레이어를 뮤트했을 때 오브젝트가 정지하던 구간(땅을 짚은 발)** 에서만 월드를 한 포즈로
# 고정하고, 움직이는 구간이 그 차이를 흡수해 다음 정지 구간 · 구간 끝에서 레이어 결과에 다시 합류한다.
#   1) 레이어 뮤트 + 스트리밍 : 프레임마다 월드 위치/쿼터니언을 이전 프레임과 비교 -> 정지 구간 [s, e] 들
#      (포즈 변화 < tol). 메모리 = 이전 포즈 1개 + 프레임당 누적 이동량 double 2개.
#   2) 레이어 켠 상태 : 구간마다 앵커 프레임(기본 = 땅에 닿은 첫 프레임)의 월드 포즈 = 구간 안 목표,
#      구간 시작/끝 프레임의 델타(앵커 포즈 - 그 프레임 포즈). 메모리 = 구간당 포즈 3개.
#   3) 움직이는 구간 : 앞 구간 끝 델타 -> 다음 구간 시작 델타를 **오브젝트 자신의 이동량 비례**(기본) /
#      ease / linear 로 보간. 델타는 오브젝트 위치 기준(위치 더하기 · 회전 월드 후곱 slerp) - 원점 기준 행렬
#      보간은 회전 델타가 큰 호를 그린다. **Start · End 에서 델타 0** (경계에 걸친 구간은 앵커를 경계로 강제,
#      범위 전체가 정지면 제외) -> 범위 밖과 최종 위치는 레이어 결과와 정확히 같다.
#   4) 쓰기는 같은 청크 루프. 스냅샷은 **보정 레이어만** 뮤트(되돌릴 레이어는 켠 채) -> 목표 = 스냅샷 + 델타.
#   실측(ZIHAN 씬 두 발): 구간 안 오차 1.7e-6(쿼터니언 왕복), 범위 밖 0, 1000 f x 2 발 10.5 s / 0.4 MB.
#   프레임마다 뮤트 토글은 16 ms/f (5배) 라 청크를 유지한다.

import math
from array import array

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_undo import undo_chunk
from Framework.core.maya_refresh import suspend_refresh

from .fill_key_manager import FillKeyManager


class CounterLayerManager:
    """상위(부모) 레이어가 바꾼 월드 위치·회전을 되돌리는 보정 additive 레이어를 만든다."""

    T_ATTRS = ["tx", "ty", "tz"]
    R_ATTRS = ["rx", "ry", "rz"]

    # 한 번에 스냅샷해 두는 프레임 수. 메모리 상한 = CHUNK_FRAMES x 오브젝트 x 16 double.
    CHUNK_FRAMES = 200

    # 글로벌이 월드를 바꾸지 않은 오브젝트 판정 허용오차(worldMatrix 성분).
    UNCHANGED_TOL = 1e-6

    # 월드 스케일이 바뀌었는지(T/R 만으로는 못 돌린다) 판정 허용오차.
    SCALE_TOL = 1e-4

    # UI 가 진행 팝업을 띄울 기준 (오브젝트 x 프레임). 실측 0.9 ms 단위 -> 약 2 초.
    PROGRESS_THRESHOLD = 2000

    # Hold 모드. Everywhere = 모든 프레임에서 되돌림, Stationary = 정지 구간만 고정(사이는 분배).
    HOLD_ALL = "all"
    HOLD_STATIONARY = "stationary"
    # 정지 구간 안에서 오브젝트가 서 있을 프레임 : 구간 첫(touchdown) · 가운데 · 끝(lift-off).
    ANCHORS = ("start", "middle", "end")
    # 움직이는 구간의 델타 분배 : 오브젝트 이동량 비례 · smoothstep · 선형.
    BLENDS = ("travel", "ease", "linear")
    # 정지 판정 허용오차(월드 위치 유닛 · 도) 와 최소 구간 길이(프레임).
    STILL_TOL_T = 0.1
    STILL_TOL_R = 0.5
    MIN_SPAN = 2

    _API_ORDER = [om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX, om.MEulerRotation.kZXY,
                  om.MEulerRotation.kXZY, om.MEulerRotation.kYXZ, om.MEulerRotation.kZYX]

    # ==================================================
    # 조회 (UI 목록 채우기)
    # ==================================================

    @staticmethod
    def root_layer():
        try:
            return cmds.animLayer(q=True, root=True)
        except Exception:
            return None

    @staticmethod
    def list_counter_candidates():
        """(BaseAnimation 을 뺀 레이어 이름 목록, 그중 에디터에서 선택된 것들).

        Base 는 뮤트할 수 없고 "있기 전" 의 의미도 없어 후보에서 뺀다. 선택 여부는 전역 질의가
        없으므로 레이어마다 묻는다(animlayer-no-global-selected-query).
        """
        layers, _ = FillKeyManager.list_anim_layers()
        root = CounterLayerManager.root_layer()
        out = [l for l in (layers or []) if l != root]
        selected = []
        for l in out:
            try:
                if cmds.animLayer(l, q=True, selected=True):
                    selected.append(l)
            except Exception:
                pass
        return out, selected

    @staticmethod
    def default_layer_name(layers, hold=None):
        """새 레이어 기본 이름: 레이어 하나면 `<layer>_counter`, 여럿이면 `counter`.

        Stationary 모드는 `_plant` / `plant` (발을 땅에 심는다는 뜻).
        """
        suffix = "plant" if hold == CounterLayerManager.HOLD_STATIONARY else "counter"
        layers = [l for l in (layers or []) if l]
        if len(layers) == 1:
            return "{0}_{1}".format(layers[0], suffix)
        return suffix

    @staticmethod
    def resolve_channels(translate=True, rotate=True):
        attrs = []
        if translate:
            attrs += CounterLayerManager.T_ATTRS
        if rotate:
            attrs += CounterLayerManager.R_ATTRS
        return attrs

    # ==================================================
    # 검사
    # ==================================================

    @staticmethod
    def _source_is_anim(plug):
        """plug(또는 그 부모 compound)의 입력이 없거나 애님 커브 / 레이어 블렌드 노드면 True.

        컨스트레인트 · 익스프레션 · 직접 연결이 들어와 있으면 키가 결과에 나타나지 않는다.
        """
        obj, attr = plug.split(".", 1)
        parents = {"tx": "translate", "ty": "translate", "tz": "translate",
                   "rx": "rotate", "ry": "rotate", "rz": "rotate"}
        for p in (plug, "{0}.{1}".format(obj, parents.get(attr, attr))):
            try:
                srcs = cmds.listConnections(p, source=True, destination=False,
                                            plugs=False, skipConversionNodes=True) or []
            except Exception:
                srcs = []
            for s in srcs:
                t = cmds.nodeType(s)
                if not (t.startswith("animCurve") or t.startswith("animBlendNode")):
                    return False
        return True

    @staticmethod
    def validate(objects, layers, attrs):
        """실행 가능 여부와 대상 채널을 정한다.

        Returns:
            (error, usable, warnings)
            error    : 거부 사유 문자열(없으면 None)
            usable   : {obj: [attr, ...]}  실제로 키를 찍을 채널
            warnings : 로그에 붙일 경고 줄들
        """
        warnings = []
        if not objects:
            return ("[Warning] Add objects to the Counter List first.", {}, warnings)
        if not layers:
            return ("[Warning] Check at least one layer to counter.", {}, warnings)
        if not attrs:
            return ("[Warning] Enable Translate and/or Rotate.", {}, warnings)

        root = CounterLayerManager.root_layer()
        if not root:
            return ("[Warning] No animation layer in the scene.", {}, warnings)

        for l in layers:
            if not cmds.objExists(l):
                return ("[Warning] Anim layer '{0}' is gone.".format(l), {}, warnings)
            if l == root:
                return ("[Warning] BaseAnimation cannot be countered (it cannot be "
                        "muted).", {}, warnings)
            if cmds.getAttr(l + ".mute"):
                return ("[Warning] '{0}' is muted - with it muted, 'before' and 'now' "
                        "are the same, so there is nothing to counter. Unmute it "
                        "first.".format(l), {}, warnings)

        # solo 는 평가를 바꿔 "지금 보이는 결과" 가 스택 전체가 아니다.
        soloed = [l for l in (cmds.ls(type="animLayer") or [])
                  if l != root and cmds.getAttr(l + ".solo")]
        if soloed:
            return ("[Warning] Solo is on ({0}). Turn solo off first - it changes "
                    "what the stack evaluates to.".format(", ".join(soloed)), {}, warnings)

        usable = {}
        missing, locked, driven = [], [], []
        for obj in objects:
            if not cmds.objExists(obj):
                missing.append(obj)
                continue
            if "transform" not in (cmds.nodeType(obj, inherited=True) or []):
                driven.append(obj)
                continue
            ok = []
            for a in attrs:
                plug = "{0}.{1}".format(obj, a)
                if not cmds.objExists(plug):
                    continue
                if cmds.getAttr(plug, lock=True):
                    locked.append(plug)
                    continue
                if not CounterLayerManager._source_is_anim(plug):
                    driven.append(plug)
                    continue
                ok.append(a)
            if ok:
                usable[obj] = ok

        if missing:
            warnings.append("Not found: {0}.".format(CounterLayerManager._brief(missing)))
        if locked:
            warnings.append("Skipped (locked - the world will not match on these): {0}."
                            .format(CounterLayerManager._brief(locked)))
        if driven:
            warnings.append("Skipped (driven by a constraint / expression / connection, "
                            "or not a transform): {0}.".format(
                                CounterLayerManager._brief(driven)))
        if not usable:
            return ("[Warning] Nothing to key - every channel was missing, locked or "
                    "driven.", {}, warnings)
        return (None, usable, warnings)

    # ==================================================
    # 메인 동작
    # ==================================================

    @staticmethod
    def create(objects, layers, start, end, translate=True, rotate=True, step=1,
               layer_name=None, zero_outside=True, skip_unchanged=True,
               select_new=True, chunk_frames=None, progress=None,
               hold=None, tol_t=None, tol_r=None, min_span=None,
               anchor="start", blend="travel"):
        """`layers` 가 바꾼 월드를 되돌리는 키를 `objects` 에 찍은 새 레이어를 만든다.

        Args:
            objects       : 월드를 유지시킬 오브젝트(발) 이름들.
            layers        : 되돌릴 레이어 이름들(예: ["lyr_glo"]). 1 개 이상.
            start, end    : 정수 구간(양 끝 포함).
            translate     : tx ty tz 를 보정.
            rotate        : rx ry rz 를 보정.
            step          : N 프레임마다 키. **1 이 아니면 정확하지 않다**(계획서 §3) - 끝 프레임은 항상 포함.
                            Stationary 모드에서는 무시(매 프레임).
            layer_name    : 새 레이어 이름. None/빈 문자열이면 default_layer_name().
            zero_outside  : start-1 / end+1 에 identity(0) 키를 둬 구간 밖 영향을 끊는다.
                            Stationary 모드에서는 Start · End 에서 델타가 0 이 되게 분배하는 것까지 포함.
            skip_unchanged: 구간 안 어느 프레임에서도 월드가 안 바뀐 오브젝트는 키를 남기지 않는다.
            select_new    : 끝나면 새 레이어만 에디터에서 선택(preferred).
            chunk_frames  : 스냅샷 청크 크기(기본 CHUNK_FRAMES). 메모리 상한을 정한다.
            progress      : progress(done, total, message=None) 콜백. None 이면 조용히.
            hold          : HOLD_ALL(기본, 모든 프레임) / HOLD_STATIONARY(정지 구간만 고정, 사이는 분배).
            tol_t, tol_r  : 정지 판정 허용오차(월드 위치 유닛 · 도). None = STILL_TOL_T / STILL_TOL_R.
            min_span      : 정지 구간 최소 길이(프레임). None = MIN_SPAN.
            anchor        : "start"(touchdown) / "middle" / "end"(lift-off) - 구간 안에서 서 있을 프레임.
            blend         : "travel"(이동량 비례) / "ease" / "linear" - 움직이는 구간의 델타 분배.

        Returns:
            (keyed_object_count, msg)
        """
        hold = hold or CounterLayerManager.HOLD_ALL
        stationary = (hold == CounterLayerManager.HOLD_STATIONARY)
        if stationary and anchor not in CounterLayerManager.ANCHORS:
            return (0, "[Warning] Unknown anchor '{0}'.".format(anchor))
        if stationary and blend not in CounterLayerManager.BLENDS:
            return (0, "[Warning] Unknown blend '{0}'.".format(blend))

        attrs = CounterLayerManager.resolve_channels(translate, rotate)
        error, usable, warnings = CounterLayerManager.validate(objects, layers, attrs)
        if error:
            return (0, " ".join([error] + warnings))

        try:
            start, end = int(start), int(end)
        except (TypeError, ValueError):
            return (0, "[Warning] Start / End must be integers.")
        if start > end:
            start, end = end, start
        step = 1 if stationary else max(1, int(step or 1))
        frames = list(range(start, end + 1, step))
        if frames[-1] != end:
            frames.append(end)
        chunk = max(1, int(chunk_frames or CounterLayerManager.CHUNK_FRAMES))

        objs = list(usable.keys())
        name = (layer_name or "").strip() or CounterLayerManager.default_layer_name(layers, hold)

        # 진행 단위 : (정지 구간 탐지) + 스냅샷 1 + 쓰기 1 (프레임 단위)
        total_units = len(frames) * 2 + ((end - start + 2) if stationary else 0)
        done_units = [0]

        def report(message=None):
            if progress:
                progress(done_units[0], total_units, message)

        changed = dict((o, False) for o in objs)
        scale_changed = False
        skipped_keys = 0
        keyed = 0
        ref_cache = {}
        plan = {}
        dropped = []
        unchanged = []

        saved_time = cmds.currentTime(q=True)
        autokey = False
        try:
            autokey = bool(cmds.autoKeyframe(q=True, state=True))
        except Exception:
            pass

        with undo_chunk(), suspend_refresh():
            if autokey:
                cmds.autoKeyframe(state=False)
            try:
                # ---- Stationary : 정지 구간(레이어 뮤트) -> 앵커 포즈 · 경계 델타(레이어 켠 채)
                if stationary:
                    def tick(f):
                        done_units[0] += 1
                        if progress and f % 10 == 0:
                            report("Detecting still spans {0}".format(f))

                    spans, cum_d, cum_a = CounterLayerManager.detect_spans(
                        objs, layers, start, end, translate, rotate, tol_t, tol_r,
                        min_span, tick=tick)
                    plan, dropped = CounterLayerManager._stationary_plan(
                        objs, spans, start, end, anchor, zero_outside)
                    for o, why in dropped:
                        if why == "none":
                            warnings.append(
                                "No stationary span: {0} (tolerance {1} / {2} deg, min "
                                "{3}f) - no keys.".format(
                                    o, CounterLayerManager._tol(tol_t, True),
                                    CounterLayerManager._tol(tol_r, False),
                                    int(min_span or CounterLayerManager.MIN_SPAN)))
                        else:
                            warnings.append("Stationary for the whole range: {0} - "
                                            "nothing to hold.".format(o))
                    objs = [o for o in objs if o in plan]
                    if not objs:
                        return (0, "[Warning] Nothing to hold - no object has a "
                                   "stationary span inside the range. " + " ".join(warnings))

                # ---- 새 레이어 (additive, 맨 위). 멤버로 넣기만 하면 기여는 0 이다.
                lyr = cmds.animLayer(name)
                for o in objs:
                    for a in usable[o]:
                        cmds.animLayer(lyr, edit=True, attribute="{0}.{1}".format(o, a))

                # 스냅샷 때 뮤트할 레이어 : Everywhere = 되돌릴 레이어 + 보정 레이어("있기 전"),
                # Stationary = 보정 레이어만(레이어 켠 결과에 델타를 얹는다).
                mute_list = [lyr] if stationary else list(layers) + [lyr]
                # 채널 일부만 키를 찍는 오브젝트는 xform 이 건드린 나머지 채널을 되돌린다 (키 없는 정적
                # 채널이면 xform 의 setAttr 가 그대로 남는다).
                partial = dict((o, len(usable[o]) < 6) for o in objs)

                # ---- 청크 루프 : 뮤트 스냅샷 -> 뮤트 해제 -> 쓰기
                for c0 in range(0, len(frames), chunk):
                    chunk_frames_list = frames[c0:c0 + chunk]

                    pre = CounterLayerManager._snapshot(objs, chunk_frames_list, mute_list)
                    done_units[0] += len(chunk_frames_list)
                    report("Sampling {0}-{1}".format(chunk_frames_list[0],
                                                     chunk_frames_list[-1]))

                    for i, f in enumerate(chunk_frames_list):
                        cmds.currentTime(f)
                        for o in objs:
                            if stationary:
                                target = CounterLayerManager._stationary_target(
                                    plan[o], f, pre[o][i], cum_d[o], cum_a[o], start,
                                    blend, translate)
                            else:
                                target = pre[o][i]
                            now = cmds.getAttr(o + ".worldMatrix[0]")
                            if not changed[o] and CounterLayerManager._differs(
                                    now, target, CounterLayerManager.UNCHANGED_TOL):
                                changed[o] = True
                            if not scale_changed and CounterLayerManager._scale_differs(
                                    now, target):
                                scale_changed = True

                            ref_rot = cmds.getAttr(o + ".rotate")[0]
                            cmds.xform(o, worldSpace=True, matrix=list(target))
                            tr = cmds.xform(o, q=True, translation=True)
                            rot = CounterLayerManager._pick_rotation(
                                o, cmds.getAttr(o + ".rotate")[0], ref_rot, ref_cache)
                            if partial[o]:
                                cmds.xform(o, worldSpace=True, matrix=list(now))
                            vals = dict(zip(CounterLayerManager.T_ATTRS, tr))
                            vals.update(zip(CounterLayerManager.R_ATTRS, rot))
                            for a in usable[o]:
                                n = cmds.setKeyframe(o, attribute=a, time=f,
                                                     value=vals[a], animLayer=lyr)
                                if n:
                                    keyed += 1
                                else:
                                    skipped_keys += 1
                        done_units[0] += 1
                        if progress and (i % 10 == 0 or i == len(chunk_frames_list) - 1):
                            report("Keying frame {0}".format(f))
                    del pre

                # ---- 바뀌지 않은 오브젝트는 레이어에서 뺀다 (키·커브 제거)
                unchanged = [o for o in objs if not changed[o]]
                if skip_unchanged and unchanged:
                    for o in unchanged:
                        for a in usable[o]:
                            plug = "{0}.{1}".format(o, a)
                            curve = CounterLayerManager._layer_curve(lyr, plug)
                            if curve:
                                cmds.cutKey(curve, clear=True)
                            try:
                                cmds.animLayer(lyr, edit=True, removeAttribute=plug)
                            except Exception:
                                pass
                    objs = [o for o in objs if changed[o]]

                # ---- 구간 밖 : identity(0) 키. 커브 노드에 직접 쓴다 (animLayer 경로는 역산한다).
                if zero_outside:
                    for o in objs:
                        for a in usable[o]:
                            curve = CounterLayerManager._layer_curve(
                                lyr, "{0}.{1}".format(o, a))
                            if not curve:
                                continue
                            for t in (start - 1, end + 1):
                                cmds.setKeyframe(curve, time=t, value=0.0)

                if select_new:
                    CounterLayerManager._select_only(lyr)
            finally:
                if autokey:
                    cmds.autoKeyframe(state=True)
                try:
                    cmds.currentTime(saved_time)
                except Exception:
                    pass

        # ---- 로그
        channels = len(set(a for o in objs for a in usable[o]))
        rng = "{0}-{1}f".format(start, end)
        if step > 1:
            rng += " (every {0}f - NOT exact between keys)".format(step)
        head = "Counter Layer (stationary): " if stationary else "Counter Layer: "
        msg = ("{0}{1} - {2} object(s), {3} channel(s), {4} ({5} keys/ch), "
               "without [{6}]".format(head, lyr, len(objs), channels, rng, len(frames),
                                      ", ".join(layers)))
        if stationary:
            labels = {"start": "touchdown", "middle": "middle", "end": "lift-off"}
            blends = {"travel": "by travel", "ease": "ease", "linear": "linear"}
            counts = ", ".join("{0} {1}".format(o.split("|")[-1], len(plan[o]["spans"]))
                               for o in objs)
            msg += ", spans [{0}], anchor {1}, blend {2}".format(
                counts, labels[anchor], blends[blend])
        if unchanged:
            msg += " Unchanged (no keys): {0}.".format(
                CounterLayerManager._brief(unchanged)) if skip_unchanged else \
                " Unchanged (keyed anyway): {0}.".format(
                    CounterLayerManager._brief(unchanged))
        if skipped_keys:
            msg += " {0} key(s) could not be set.".format(skipped_keys)
        if scale_changed:
            msg += (" Note: the world SCALE also changed - only translate / rotate "
                    "are restored.")
        members = [o for o in objs if CounterLayerManager._is_member_of_any(o, layers)]
        if members:
            msg += (" Note: {0} also keyed in the countered layer(s) - that "
                    "contribution is countered too.".format(
                        CounterLayerManager._brief(members)))
        if warnings:
            msg += " " + " ".join(warnings)
        if not objs:
            return (0, "[Warning] " + msg)
        return (len(objs), msg)

    # ==================================================
    # Stationary : 정지 구간 탐지 · 미리보기
    # ==================================================

    @staticmethod
    def _tol(value, is_translate):
        if value is None or value <= 0:
            return CounterLayerManager.STILL_TOL_T if is_translate else CounterLayerManager.STILL_TOL_R
        return float(value)

    @staticmethod
    def detect_spans(objects, layers, start, end, translate=True, rotate=True,
                     tol_t=None, tol_r=None, min_span=None, tick=None):
        """`layers` 를 뮤트한 상태에서 오브젝트가 정지하는 프레임 구간을 찾는다 (스트리밍).

        정지 = 이전 프레임 대비 월드 위치 변화 < tol_t (translate 가 켜졌을 때) **그리고**
        월드 회전 변화 < tol_r 도 (rotate 가 켜졌을 때). 구간은 start..end 로 잘리고 길이 < min_span 은 버린다.

        Returns:
            (spans, cum_d, cum_a)
            spans : {obj: [[s, e], ...]}
            cum_d : {obj: array('d')}  cum_d[f - start] = start..f 까지 누적 월드 이동 거리 (분배용)
            cum_a : {obj: array('d')}  같은 것, 회전각(도)
        """
        tol_t = CounterLayerManager._tol(tol_t, True)
        tol_r = CounterLayerManager._tol(tol_r, False)
        min_span = max(2, int(min_span or CounterLayerManager.MIN_SPAN))
        start, end = int(start), int(end)
        n = end - start + 1
        objs = list(objects)
        still = dict((o, bytearray(n)) for o in objs)         # still[o][f - start]
        cum_d = dict((o, array("d", [0.0] * n)) for o in objs)
        cum_a = dict((o, array("d", [0.0] * n)) for o in objs)
        prev = {}

        saved_time = cmds.currentTime(q=True)
        was_muted = {}
        for l in layers:
            was_muted[l] = bool(cmds.getAttr(l + ".mute"))
            cmds.animLayer(l, edit=True, mute=True)
        try:
            for f in range(start - 1, end + 1):
                cmds.currentTime(f)
                for o in objs:
                    t, q = CounterLayerManager._pose(cmds.getAttr(o + ".worldMatrix[0]"))
                    if o in prev and f >= start:
                        pt, pq = prev[o]
                        dist = (t - pt).length()
                        ang = CounterLayerManager._angle(q, pq)
                        ok = True
                        if translate:
                            ok = ok and dist < tol_t
                        if rotate:
                            ok = ok and ang < tol_r
                        i = f - start
                        still[o][i] = 1 if ok else 0
                        cum_d[o][i] = (cum_d[o][i - 1] if i else 0.0) + dist
                        cum_a[o][i] = (cum_a[o][i - 1] if i else 0.0) + ang
                    prev[o] = (t, q)
                if tick:
                    tick(f)
        finally:
            for l in layers:
                cmds.animLayer(l, edit=True, mute=was_muted[l])
            try:
                cmds.currentTime(saved_time)
            except Exception:
                pass

        spans = {}
        for o in objs:
            runs = []
            f = start
            while f <= end:
                if f + 1 <= end and still[o][f + 1 - start]:
                    g = f
                    while g + 1 <= end and still[o][g + 1 - start]:
                        g += 1
                    if g - f + 1 >= min_span:
                        runs.append([f, g])
                    f = g + 1
                else:
                    f += 1
            spans[o] = runs
        return spans, cum_d, cum_a

    @staticmethod
    def preview_spans(objects, layers, start, end, translate=True, rotate=True,
                      tol_t=None, tol_r=None, min_span=None):
        """레이어를 만들지 않고 정지 구간만 로그 문장으로. → (구간이 있는 오브젝트 수, msg)."""
        attrs = CounterLayerManager.resolve_channels(translate, rotate)
        error, usable, warnings = CounterLayerManager.validate(objects, layers, attrs)
        if error:
            return (0, " ".join([error] + warnings))
        try:
            start, end = int(start), int(end)
        except (TypeError, ValueError):
            return (0, "[Warning] Start / End must be integers.")
        if start > end:
            start, end = end, start
        objs = list(usable.keys())
        spans, _, _ = CounterLayerManager.detect_spans(
            objs, layers, start, end, translate, rotate, tol_t, tol_r, min_span)
        parts = []
        found = 0
        for o in objs:
            runs = spans[o]
            if runs:
                found += 1
                parts.append("{0}: {1}".format(o.split("|")[-1], ", ".join(
                    "{0}-{1} ({2}f)".format(s, e, e - s + 1) for s, e in runs)))
            else:
                parts.append("{0}: none".format(o.split("|")[-1]))
        msg = ("Stationary spans {0}-{1}f without [{2}] (tolerance {3} / {4} deg, min {5}f): "
               "{6}".format(start, end, ", ".join(layers),
                            CounterLayerManager._tol(tol_t, True),
                            CounterLayerManager._tol(tol_r, False),
                            max(2, int(min_span or CounterLayerManager.MIN_SPAN)),
                            "; ".join(parts)))
        if warnings:
            msg += " " + " ".join(warnings)
        return (found, msg)

    @staticmethod
    def _stationary_plan(objs, spans, start, end, anchor, zero_outside):
        """구간마다 앵커 포즈 · 경계 델타, 사이 구간의 (g0, g1, D0, D1) 표를 만든다 (레이어 켠 상태에서 읽음).

        Returns:
            (plan, dropped)
            plan[o] = dict(spans=[(s, e)], poses=[(MVector, MQuaternion)], span_idx=array('i'),
                           segs=[(g0, g1, (dT0, dQ0), (dT1, dQ1))], seg_idx=array('i'))
            dropped = [(obj, "none" | "whole")]
        """
        plan, dropped = {}, []
        n = end - start + 1
        zero = (om.MVector(0.0, 0.0, 0.0), om.MQuaternion())
        for o in objs:
            runs = [(int(s), int(e)) for s, e in spans.get(o, [])]
            if not runs:
                dropped.append((o, "none"))
                continue
            if any(s <= start and e >= end for s, e in runs):
                dropped.append((o, "whole"))
                continue
            anchors = []
            for s, e in runs:
                if s <= start:
                    anchors.append(start)
                elif e >= end:
                    anchors.append(end)
                elif anchor == "start":
                    anchors.append(s)
                elif anchor == "end":
                    anchors.append(e)
                else:
                    anchors.append((s + e) // 2)
            poses, edges = [], []
            for (s, e), af in zip(runs, anchors):
                cmds.currentTime(af)
                ta, qa = CounterLayerManager._pose(cmds.getAttr(o + ".worldMatrix[0]"))
                poses.append((ta, qa))
                ed = []
                for f in (s, e):
                    cmds.currentTime(f)
                    t, q = CounterLayerManager._pose(cmds.getAttr(o + ".worldMatrix[0]"))
                    ed.append((ta - t, q.inverse() * qa))
                edges.append(ed)
            # 사이 구간 표
            segs = []
            span_idx = array("i", [-1] * n)
            seg_idx = array("i", [-1] * n)
            for k, (s, e) in enumerate(runs):
                for f in range(s, e + 1):
                    span_idx[f - start] = k
            # 첫 구간 앞
            first_s, first_d = runs[0][0], edges[0][0]
            segs.append((start, first_s, zero if zero_outside else first_d, first_d))
            for k in range(len(runs) - 1):
                segs.append((runs[k][1], runs[k + 1][0], edges[k][1], edges[k + 1][0]))
            last_e, last_d = runs[-1][1], edges[-1][1]
            segs.append((last_e, end, last_d, zero if zero_outside else last_d))
            for k, (g0, g1, _d0, _d1) in enumerate(segs):
                for f in range(g0, g1 + 1):
                    if span_idx[f - start] < 0:
                        seg_idx[f - start] = k
            plan[o] = dict(spans=runs, poses=poses, span_idx=span_idx, segs=segs,
                           seg_idx=seg_idx)
        return plan, dropped

    @staticmethod
    def _stationary_target(p, f, on_matrix, cum_d, cum_a, start, blend, use_dist):
        """프레임 f 의 목표 월드 행렬(list 16). 구간 안 = 앵커 포즈, 사이 = 레이어 결과 + 보간 델타."""
        tm = om.MTransformationMatrix(om.MMatrix(on_matrix))
        i = f - start
        k = p["span_idx"][i]
        if k >= 0:
            ta, qa = p["poses"][k]
            tm.setTranslation(ta, om.MSpace.kWorld)
            tm.setRotation(qa)
            return list(tm.asMatrix())
        g0, g1, d0, d1 = p["segs"][p["seg_idx"][i]]
        u = CounterLayerManager._frac(blend, cum_d, cum_a, start, g0, g1, f, use_dist)
        dt = d0[0] * (1.0 - u) + d1[0] * u
        dq = om.MQuaternion.slerp(d0[1], d1[1], u)
        t = tm.translation(om.MSpace.kWorld)
        q = tm.rotation(asQuaternion=True)
        tm.setTranslation(t + dt, om.MSpace.kWorld)
        tm.setRotation(q * dq)
        return list(tm.asMatrix())

    @staticmethod
    def _frac(blend, cum_d, cum_a, start, g0, g1, f, use_dist=True):
        """g0(델타 D0) -> g1(델타 D1) 사이 프레임 f 의 보간 비율 0..1."""
        if g1 <= g0:
            return 1.0
        u = (f - g0) / float(g1 - g0)
        if blend == "linear":
            return u
        if blend == "ease":
            return u * u * (3.0 - 2.0 * u)
        for cum in ((cum_d, cum_a) if use_dist else (cum_a,)):
            tot = cum[g1 - start] - cum[g0 - start]
            if tot > 1e-9:
                return (cum[f - start] - cum[g0 - start]) / tot
        return u

    @staticmethod
    def _pose(matrix):
        tm = om.MTransformationMatrix(om.MMatrix(matrix))
        return tm.translation(om.MSpace.kWorld), tm.rotation(asQuaternion=True)

    @staticmethod
    def _angle(q1, q2):
        """두 쿼터니언 사이 회전각(도)."""
        w = abs((q1 * q2.inverse()).w)
        return math.degrees(2.0 * math.acos(min(1.0, w)))

    # ==================================================
    # 내부 헬퍼
    # ==================================================

    @staticmethod
    def _snapshot(objs, frames, mute_layers):
        """`mute_layers` 를 뮤트한 채 프레임마다 worldMatrix 를 찍는다. {obj: [array('d')x16, ...]}.

        currentTime 루프가 getAttr(time=) 보다 3 배 빠르다(계획서 F11). 뮤트는 finally 로 복원.
        """
        out = dict((o, []) for o in objs)
        for l in mute_layers:
            cmds.animLayer(l, edit=True, mute=True)
        try:
            for f in frames:
                cmds.currentTime(f)
                for o in objs:
                    out[o].append(array("d", cmds.getAttr(o + ".worldMatrix[0]")))
        finally:
            for l in mute_layers:
                cmds.animLayer(l, edit=True, mute=False)
        return out

    @staticmethod
    def _differs(a, b, tol):
        for x, y in zip(a, b):
            if abs(x - y) > tol:
                return True
        return False

    @staticmethod
    def _scale_differs(a, b):
        """두 행렬의 축 길이(스케일)가 다른가."""
        for r in (0, 4, 8):
            la = math.sqrt(a[r] ** 2 + a[r + 1] ** 2 + a[r + 2] ** 2)
            lb = math.sqrt(b[r] ** 2 + b[r + 1] ** 2 + b[r + 2] ** 2)
            if abs(la - lb) > CounterLayerManager.SCALE_TOL:
                return True
        return False

    @staticmethod
    def _pick_rotation(obj, target_deg, ref_deg, cache=None):
        """`target_deg`(xform 이 돌려준 오일러)와 같은 회전 중 `ref_deg` 에 가장 가까운 것(도).

        `alternateSolution` + `setToClosestCut` 만 쓴다 - 둘 다 회전을 보존한다. `setToClosestSolution`
        은 짐벌 근처에서 **다른 회전**을 돌려줘 금지(euler-closest-solution-not-equivalent).
        """
        if cache is not None and obj in cache:
            order = cache[obj]
        else:
            order = CounterLayerManager._API_ORDER[cmds.getAttr(obj + ".rotateOrder")]
            if cache is not None:
                cache[obj] = order
        e = om.MEulerRotation(*[math.radians(v) for v in target_deg], order=order)
        ref = om.MEulerRotation(*[math.radians(v) for v in ref_deg], order=order)
        matrix = e.asMatrix()
        best = None
        for cand in (om.MEulerRotation(e), e.alternateSolution()):
            cand.setToClosestCut(ref)
            if not cand.asMatrix().isEquivalent(matrix, 1e-9):
                continue
            d = sum((cand[i] - ref[i]) ** 2 for i in range(3))
            if best is None or d < best[0]:
                best = (d, cand)
        if best is None:          # 이론상 없지만, 있으면 xform 값을 그대로 쓴다.
            return list(target_deg)
        c = best[1]
        return [math.degrees(c[0]), math.degrees(c[1]), math.degrees(c[2])]

    @staticmethod
    def _layer_curve(layer, plug):
        try:
            c = cmds.animLayer(layer, q=True, findCurveForPlug=plug) or []
        except Exception:
            c = []
        return c[0] if c else None

    @staticmethod
    def _is_member_of_any(obj, layers):
        for l in layers:
            try:
                members = cmds.animLayer(l, q=True, attribute=True) or []
            except Exception:
                members = []
            if any(m.split(".", 1)[0] == obj for m in members):
                return True
        return False

    @staticmethod
    def _select_only(layer):
        """새 레이어만 선택 + preferred (마야가 Merge 뒤에 하는 것과 같은 관례)."""
        for l in cmds.ls(type="animLayer") or []:
            try:
                cmds.animLayer(l, edit=True, selected=(l == layer))
            except Exception:
                pass
        try:
            cmds.animLayer(layer, edit=True, preferred=True)
        except Exception:
            pass

    @staticmethod
    def _brief(names, limit=8):
        uniq = sorted(set(names))
        if len(uniq) <= limit:
            return ", ".join(uniq)
        return "{0} (+{1} more)".format(", ".join(uniq[:limit]), len(uniq) - limit)
