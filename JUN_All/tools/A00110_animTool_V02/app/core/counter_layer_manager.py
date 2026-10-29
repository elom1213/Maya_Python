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
    def default_layer_name(layers):
        """새 레이어 기본 이름: 레이어 하나면 `<layer>_counter`, 여럿이면 `counter`."""
        layers = [l for l in (layers or []) if l]
        if len(layers) == 1:
            return "{0}_counter".format(layers[0])
        return "counter"

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
               select_new=True, chunk_frames=None, progress=None):
        """`layers` 를 뮤트한 상태의 월드 위치·회전이 유지되도록 `objects` 에 키를 찍은 새 레이어를 만든다.

        Args:
            objects       : 월드를 유지시킬 오브젝트(발) 이름들.
            layers        : 되돌릴 레이어 이름들(예: ["lyr_glo"]). 1 개 이상.
            start, end    : 정수 구간(양 끝 포함).
            translate     : tx ty tz 를 보정.
            rotate        : rx ry rz 를 보정.
            step          : N 프레임마다 키. **1 이 아니면 정확하지 않다**(계획서 §3) - 끝 프레임은 항상 포함.
            layer_name    : 새 레이어 이름. None/빈 문자열이면 default_layer_name().
            zero_outside  : start-1 / end+1 에 identity(0) 키를 둬 구간 밖 영향을 끊는다.
            skip_unchanged: 구간 안 어느 프레임에서도 월드가 안 바뀐 오브젝트는 키를 남기지 않는다.
            select_new    : 끝나면 새 레이어만 에디터에서 선택(preferred).
            chunk_frames  : 스냅샷 청크 크기(기본 CHUNK_FRAMES). 메모리 상한을 정한다.
            progress      : progress(done, total, message=None) 콜백. None 이면 조용히.

        Returns:
            (keyed_object_count, msg)
        """
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
        step = max(1, int(step or 1))
        frames = list(range(start, end + 1, step))
        if frames[-1] != end:
            frames.append(end)
        chunk = max(1, int(chunk_frames or CounterLayerManager.CHUNK_FRAMES))

        objs = list(usable.keys())
        name = (layer_name or "").strip() or CounterLayerManager.default_layer_name(layers)

        total_units = len(frames) * 2          # 스냅샷 1 + 쓰기 1 (프레임 단위)
        done_units = [0]

        def report(message=None):
            if progress:
                progress(done_units[0], total_units, message)

        changed = dict((o, False) for o in objs)
        scale_changed = False
        skipped_keys = 0
        keyed = 0
        ref_cache = {}

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
                # ---- 새 레이어 (additive, 맨 위). 멤버로 넣기만 하면 기여는 0 이다.
                lyr = cmds.animLayer(name)
                for o in objs:
                    for a in usable[o]:
                        cmds.animLayer(lyr, edit=True, attribute="{0}.{1}".format(o, a))

                # ---- 청크 루프 : 뮤트 스냅샷 -> 뮤트 해제 -> 쓰기
                for c0 in range(0, len(frames), chunk):
                    chunk_frames_list = frames[c0:c0 + chunk]

                    pre = CounterLayerManager._snapshot(
                        objs, chunk_frames_list, list(layers) + [lyr])
                    done_units[0] += len(chunk_frames_list)
                    report("Sampling {0}-{1}".format(chunk_frames_list[0],
                                                     chunk_frames_list[-1]))

                    for i, f in enumerate(chunk_frames_list):
                        cmds.currentTime(f)
                        for o in objs:
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
        msg = ("Counter Layer: {0} - {1} object(s), {2} channel(s), {3} ({4} keys/ch), "
               "without [{5}]".format(lyr, len(objs), channels, rng, len(frames),
                                      ", ".join(layers)))
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
