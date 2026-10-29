# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00110_animTool_V02 - 애니메이션 레이어 사이 키 복사 / 잘라내기 (maya.cmds, UI 비의존)
#
# "리스트업한 오브젝트들의 키를 **레이어 A 에서 레이어 B 로** 한 번에 옮긴다."
#
# 마야에서 Ctrl+C / Ctrl+V 로는 레이어를 건너뛰는 복사가 온전히 안 된다 - 붙여넣기가
# **지금 선택된 레이어**로 가 버리고, 오브젝트가 여러 개면 어떤 채널이 어디로 갔는지도
# 알 수 없다. 그래서 소스/대상 레이어를 **명시**하고 채널을 골라서 옮기는 경로를 따로 둔다.
#
# ## mayapy(2024) 로 확인한 사실 - 구현이 여기에 기대고 있다
#
# 1. `copyKey(plug, animLayer=L)` / `pasteKey(plug, animLayer=L, option=...)` 는 **레이어를
#    지정한 복사·붙여넣기가 된다.** 붙여넣기는 클립보드의 **원래 시간**에 들어간다(현재
#    프레임이 아니다). 대상 레이어에 그 채널의 커브가 없으면 **커브를 새로 만들어 준다.**
# 2. 단, 대상 레이어가 **BaseAnimation 이 아닌데** 그 plug 가 레이어 멤버가 아니면
#    `pasteKey` 는 `RuntimeError: Nothing to paste to` 로 실패한다. 먼저
#    `animLayer(L, e=True, attribute=plug)` 로 넣어 줘야 한다.
#    BaseAnimation 은 멤버가 아니어도 그냥 붙는다(커브까지 만들어 준다).
# 3. **`cutKey` 에는 `animLayer` 플래그가 없다**(`TypeError: Invalid flag 'animLayer'`).
#    그래서 잘라내기는 소스 **커브 노드**를 찾아 거기서 지운다.
# 4. `animLayer(L, q=True, findCurveForPlug=plug)` 는 **어느 레이어에도 안 든 오브젝트**에
#    대해서는 BaseAnimation 을 물어도 `None` 을 준다(평범한 애님 커브가 있어도). 그 경우엔
#    plug 에 직접 연결된 animCurve 가 곧 base 커브다.
# 5. `copyKey` 는 시간 플래그가 없으면 **그 커브의 모든 키**를 복사한다.
#
# ## 값 의미(중요)
#
# **Copy** 는 **커브 값을 그대로** 옮긴다 - 레이어 기여분을 다시 계산하지 않는다(마야의
# 복사/붙여넣기와 같은 규칙). Base(절대값) -> additive 레이어로 복사하면 두 번 더해진다.
#
# **Cut(Move) 는 기본으로 최종 결과를 보존한다(keep_result=True, v02.28).** 커브를 그대로 옮기고
# 잘라내기만 하면 월드 위치·회전이 달라지는데, 원인은 두 가지다(mayapy 2024 실측, 2026-10-29):
#
# 6. **커브를 다 지우면 blend 노드 입력에 마지막 값이 정적으로 남는다.** Base 커브를 지우면
#    맨 아래 `animBlendNode*.inputA` 에, 레이어 커브를 지우면 그 레이어 노드의 `inputB` 에
#    지우던 순간의 값이 그대로 남아 계속 더해진다(마야 자체 `animLayer -extractAnimation` 도
#    같은 상태를 만든다). `setAttr` 로 plug 에 직접 쓰면 활성 레이어 쪽에 들어가 소용없고,
#    **그 입력 plug 에 identity(0 · multiply 스케일은 1)를 써야** 정확히 원래 결과로 돌아간다.
#    override 레이어에는 identity 가 없으므로 `animLayer -e -removeAttribute` 로 멤버에서 뺀다.
# 7. **대상이 커브 없이 정적 값을 갖고 있었으면 붙여넣기가 그 값을 덮는다.** Base 로 옮길 때 base
#    정적값 c, additive 로 옮길 때 그 레이어 멤버의 정적값 d 가 사라지므로 붙여넣은 키에
#    합성한다(`keyframe -r -vc` / multiply 스케일은 `scaleKey -vs`). by-component 는 정확,
#    **by-layer 회전에 0 아닌 회전을 합성하는 경우만 근사**(회전 합성은 축별 덧셈이 아니다)
#    -> 로그에 경고.
#
# 구간(Limit to Time Range) 이동은 Merge Layers 와 같은 경계 규칙을 쓴다 - 소스에 `s-1`·`s`·`e`·`e+1`
# 키를 `setKeyframe -insert` + `keyTangent fixed` 로 박아 모양을 고정하고, 잘라낸 자리는 identity
# 키(`s` step · `e`), 대상에는 바깥 값 키(`s-1` · `e+1`). 정수 프레임은 전부 같고 `(s-1, s)` ·
# `(e, e+1)` 사이만 보간이 다르다.
#
# 보존이 안 되는 경우(그대로 옮기고 로그에 적는다): 대상에 이미 키가 있는 채널(`replace` 로
# 덮인다 - 합치려면 Bake > Merge Layers), 레이어 weight ≠ 1, override 소스를 구간으로 자르기,
# visibility 같은 비수치(Boolean/Enum) 채널, 아래 레이어가 애니메이션된 override 소스.

import maya.cmds as cmds

from .copykey_manager import CopyKeyManager
from .fill_key_manager import FillKeyManager

from Framework.core.maya_undo import undo_chunk


class LayerKeyManager:
    """애니메이션 레이어 사이로 키를 복사(copy) / 옮긴다(cut)."""

    # 붙여넣기 모드는 Copy Key 탭과 같은 목록을 쓴다(단일 소스).
    PASTE_OPTIONS = CopyKeyManager.PASTE_OPTIONS

    # 9축 체크박스 정의도 Copy Key 탭과 공유한다(UI 체크박스 순서와 일치).
    COPY_ATTRS = CopyKeyManager.COPY_ATTRS
    TRS_ATTRS = CopyKeyManager.TRS_ATTRS

    # 레이어 사이 이동의 기본 붙여넣기 모드. Copy Key 탭의 기본값("insert", 마야 기본)과
    # 다르다 - 레이어를 옮길 때 원하는 것은 "그 구간을 이 커브로 바꿔라" 이지, 대상 레이어에
    # 이미 있던 키를 시간축으로 밀어내는 게 아니다.
    DEFAULT_PASTE_OPTION = "replace"

    # ==================================================
    # 조회 (UI 목록 채우기)
    # ==================================================

    @staticmethod
    def list_anim_layers():
        """(레이어 이름 목록, 지금 선택된 레이어 or None). Fill Keys 탭과 같은 조회."""
        return FillKeyManager.list_anim_layers()

    @staticmethod
    def root_layer():
        """BaseAnimation 레이어 이름(레이어가 없으면 None)."""
        try:
            return cmds.animLayer(q=True, root=True)
        except Exception:
            return None

    @staticmethod
    def plain_curve(plug):
        """plug 에 **직접** 연결된 애님 커브(레이어에 안 든 오브젝트의 base 커브).

        레이어에 든 plug 는 앞단이 animBlendNode* 라 여기서 걸리지 않는다 - 그래서
        "레이어 없는 평범한 커브" 만 골라내는 판정으로 쓸 수 있다.
        """
        try:
            found = cmds.listConnections(plug, source=True, destination=False,
                                         type="animCurve",
                                         skipConversionNodes=True) or []
        except Exception:
            found = []
        return found[0] if found else None

    @staticmethod
    def layer_curve(plug, layer, root=None):
        """이 plug 를 이 레이어에서 구동하는 애님 커브. 없으면 None.

        BaseAnimation 을 물었는데 못 찾으면, 그 오브젝트가 **어느 레이어에도 안 든**
        경우일 수 있으므로 plug 직결 커브로 한 번 더 본다(맨 위 §4).
        """
        if not layer:
            return None
        try:
            curves = cmds.animLayer(layer, q=True, findCurveForPlug=plug) or []
        except Exception:
            curves = []
        if curves:
            return curves[0]
        if root is None:
            root = LayerKeyManager.root_layer()
        if layer == root:
            return LayerKeyManager.plain_curve(plug)
        return None

    @staticmethod
    def list_layer_attrs(objects, layer, skip_trs=True):
        """오브젝트들의 채널 중 **그 레이어에 커브가 있는** 것들의 합집합.

        후보는 `listAttr(keyable=True, visible=True, unlocked=True)` - 다른 탭들
        (`FillKeyManager.list_keyable_attrs`, `CopyKeyManager.list_custom_attrs`)과 같은
        기준이다(= 채널박스에 뜨는 키 가능 채널).

        여기서 한 번 더 **소스 레이어에 실제로 커브가 있는지** 로 거른다. 옮길 게 없는
        채널을 목록에 올려 봐야 고를 이유가 없기 때문이다.

        skip_trs=True(기본)면 9축 체크박스가 담당하는 translate/rotate/scale 은 뺀다.
        """
        root = LayerKeyManager.root_layer()

        found = []
        seen = set()

        for obj in (objects or []):
            if not cmds.objExists(obj):
                continue
            try:
                attrs = cmds.listAttr(obj, keyable=True, visible=True,
                                      unlocked=True) or []
            except Exception:
                attrs = []
            for attr in attrs:
                # 중첩 이름(compound 자식 경로)은 plug 로 바로 못 쓰므로 제외.
                if "." in attr or attr in seen:
                    continue
                if skip_trs and attr in LayerKeyManager.TRS_ATTRS:
                    continue
                plug = "{0}.{1}".format(obj, attr)
                if not LayerKeyManager.layer_curve(plug, layer, root):
                    continue
                seen.add(attr)
                found.append(attr)

        return found

    # ==================================================
    # 대상 채널 정하기
    # ==================================================

    @staticmethod
    def resolve_attrs(attr_flags, custom_attrs=None):
        """9축 체크박스 + 커스텀 채널 목록 -> 옮길 채널 이름 리스트.

        Copy Key 탭과 달리 **"필터 없음(None)" 경로가 없다.** 레이어 이동은 채널(plug)
        하나씩 copy/paste 해야 하므로(노드 단위 pasteKey 는 클립보드 커브를 이름이 아니라
        순서로 맞춘다) 언제나 명시 목록이 필요하다. 채널을 다 옮기고 싶으면
        `all_keyed=True` 경로(소스 레이어에 커브가 있는 채널 전부)를 쓴다.
        """
        attrs = []
        if attr_flags:
            attrs = [attr for key, attr in LayerKeyManager.COPY_ATTRS
                     if attr_flags.get(key)]

        for attr in (custom_attrs or []):
            attr = (attr or "").strip()
            if attr and attr not in attrs:
                attrs.append(attr)

        return attrs

    # ==================================================
    # 메인 동작
    # ==================================================

    @staticmethod
    def transfer_keys(objects, src_layer, dst_layer, attr_flags=None,
                      custom_attrs=None, all_keyed=False, start=None, end=None,
                      paste_option=None, cut=False, keep_result=True):
        """`src_layer` 의 키를 `dst_layer` 로 복사(cut=False) 하거나 옮긴다(cut=True).

        Args:
            objects      : 대상 오브젝트 이름들.
            src_layer    : 가져올 레이어 이름.
            dst_layer    : 넣을 레이어 이름.
            attr_flags   : {"tx": bool, ... "sz": bool} 9축 선택.
            custom_attrs : 추가로 옮길 채널 이름들(예: ["ikBlend"]).
            all_keyed    : True 면 위 둘을 무시하고 **소스 레이어에 커브가 있는 채널 전부**를
                           오브젝트마다 따로 구해 옮긴다.
            start, end   : 시간 구간(양 끝 포함). None 이면 **그 커브의 모든 키**.
            paste_option : cmds.pasteKey option (기본 "replace").
            cut          : True 면 붙여넣기에 성공한 뒤 **소스 레이어의 그 키들을 지운다**.
            keep_result  : cut 일 때 **최종 평가값(월드 위치·회전)을 보존**한다(맨 위 §6·§7).
                           False 면 예전처럼 커브 값만 그대로 옮긴다. Copy 에는 영향 없다.

        Returns:
            (옮긴 채널 수, 메시지)
        """
        if not objects:
            return (0, "[Warning] Object list is empty.")
        if not src_layer or not dst_layer:
            return (0, "[Warning] Pick both a source and a destination layer.")
        if src_layer == dst_layer:
            return (0, "[Warning] Source and destination layer are the same "
                       "({0}).".format(src_layer))
        for layer in (src_layer, dst_layer):
            if not cmds.objExists(layer):
                return (0, "[Warning] Anim layer '{0}' is gone.".format(layer))

        if paste_option not in LayerKeyManager.PASTE_OPTIONS:
            paste_option = LayerKeyManager.DEFAULT_PASTE_OPTION

        attrs = LayerKeyManager.resolve_attrs(attr_flags, custom_attrs)
        if not all_keyed and not attrs:
            return (0, "[Warning] No channel checked (Translate / Rotate / Scale / "
                       "Custom Channels), and 'All Keyed Channels' is off.")

        if start is not None and end is not None:
            start, end = (min(start, end), max(start, end))
            time_kwargs = {"time": (start, end)}
        else:
            start = end = None
            time_kwargs = {}

        root = LayerKeyManager.root_layer()
        keep = bool(cut and keep_result)

        moved = 0          # 실제로 붙여넣은 채널 수
        cut_count = 0      # 소스에서 지운 채널 수
        kept = 0           # 최종값을 보존한(정확한) 채널 수
        objs_done = set()
        missing_obj = []   # 씬에 없는 오브젝트
        missing = []       # plug 가 없는 채널
        no_key = []        # 소스 레이어에 (구간 안) 키가 없는 채널
        failed = []        # 붙여넣기 실패
        notes = []         # keep_result 가 정확히 안 되는 이유 [text, set(attr)] (중복 제거, 순서 유지)

        def note(text, attr=None):
            """같은 이유는 한 번만, 채널은 뒤에 묶어 적는다(9축이면 이름 아홉 개가 아홉 줄이 된다)."""
            for item in notes:
                if item[0] == text:
                    if attr:
                        item[1].add(attr)
                    return
            notes.append([text, set([attr]) if attr else set()])

        if keep:
            for layer in (src_layer, dst_layer):
                w = LayerKeyManager._layer_weight(layer, root)
                if w is None:
                    note("'{0}' weight is animated - result not exact".format(layer))
                elif abs(w - 1.0) > 1e-9:
                    note("'{0}' weight is {1:g} (not 1) - result not exact".format(
                        layer, w))

        with undo_chunk():
            for obj in objects:
                if not cmds.objExists(obj):
                    missing_obj.append(obj)
                    continue

                if all_keyed:
                    obj_attrs = LayerKeyManager.list_layer_attrs(
                        [obj], src_layer, skip_trs=False)
                else:
                    obj_attrs = attrs

                for attr in obj_attrs:
                    plug = "{0}.{1}".format(obj, attr)
                    if not cmds.objExists(plug):
                        missing.append(attr)
                        continue

                    # ---- 0) (Move + keep) 구간 이동이면 소스 커브의 경계 모양을 먼저 고정한다
                    src_curve = None
                    edges = (False, False)
                    dst_member = True
                    if keep:
                        src_curve = LayerKeyManager.layer_curve(plug, src_layer, root)
                        if src_curve and start is not None:
                            edges = LayerKeyManager._prep_source_range(
                                src_curve, start, end)
                        if src_curve and dst_layer != root:
                            dst_nodes = LayerKeyManager._layer_nodes(dst_layer)
                            dst_member = any(n in dst_nodes for n, _ in
                                             LayerKeyManager._blend_chain(plug))

                    # ---- 1) 소스 레이어에서 복사
                    try:
                        copied = cmds.copyKey(plug, animLayer=src_layer,
                                              **time_kwargs)
                    except Exception:
                        copied = 0
                    if not copied:
                        no_key.append(attr)
                        continue

                    # ---- 2) 대상 레이어가 그 채널을 갖고 있게 한다
                    # BaseAnimation 은 멤버가 아니어도 붙으므로 건드리지 않는다.
                    if dst_layer != root:
                        try:
                            if not cmds.animLayer(dst_layer, q=True,
                                                  findCurveForPlug=plug):
                                cmds.animLayer(dst_layer, edit=True, attribute=plug)
                        except Exception:
                            pass

                    # ---- 2.5) (Move + keep) 붙여넣기 전에 대상의 정적값 · blend 노드를 읽어 둔다
                    info = None
                    if keep and src_curve:
                        info = LayerKeyManager._move_info(
                            plug, attr, src_layer, dst_layer, root, src_curve,
                            start, end, edges, dst_member, note)

                    # ---- 3) 붙여넣기
                    try:
                        cmds.pasteKey(plug, animLayer=dst_layer,
                                      option=paste_option)
                    except Exception:
                        # 잠긴 채널 / 대상 레이어에 넣을 수 없는 채널 등.
                        failed.append(attr)
                        continue

                    moved += 1
                    objs_done.add(obj)

                    # ---- 3.5) (Move + keep) 대상이 들고 있던 정적값을 붙여넣은 키에 합성
                    if info:
                        LayerKeyManager._compose_destination(info)

                    # ---- 4) 잘라내기 : 붙여넣기가 성공한 뒤에만 소스를 지운다
                    if cut and LayerKeyManager._cut_source(plug, src_layer, root,
                                                           start, end):
                        cut_count += 1
                        # ---- 5) (Move + keep) 소스에 남은 정적값 · 구간 기여를 중화
                        if info and LayerKeyManager._neutralize_source(info):
                            kept += 1

        mode = "Cut" if cut else "Copy"
        scope = ("all keyed channels" if all_keyed
                 else LayerKeyManager._scope_text(attrs))
        rng = "all keys" if start is None else "{0}-{1}f".format(start, end)
        msg = ("{0}: {1} channel(s) on {2} object(s), {3} -> {4}  "
               "[{5}, option: {6}, channels: {7}]".format(
                   mode, moved, len(objs_done), src_layer, dst_layer, rng,
                   paste_option, scope))
        if cut:
            msg += " Removed from {0}: {1} channel(s).".format(src_layer, cut_count)
        if keep:
            msg += " Result kept on {0} channel(s).".format(kept)
            if notes:
                parts = []
                for text, attrs_ in notes:
                    if attrs_:
                        text = "{0} ({1})".format(text, LayerKeyManager._brief(attrs_))
                    parts.append(text)
                msg += " Not exact: " + "; ".join(parts) + "."
        if missing_obj:
            msg += " Not found: {0}.".format(LayerKeyManager._brief(missing_obj))
        # 키가 없던 채널 보고는 두 갈래다. 9축은 **기본이 전부 켜짐**이라, 회전만 키가 있는
        # 컨트롤러 하나에도 이름이 예닐곱 개씩 따라 붙어 로그가 안 읽힌다 - 개수로만 적는다.
        # 사용자가 직접 고른 커스텀 채널은 왜 안 갔는지 알아야 하므로 이름을 남긴다.
        no_key_axis = sorted(set(a for a in no_key if a in LayerKeyManager.TRS_ATTRS))
        no_key_other = sorted(set(a for a in no_key
                                  if a not in LayerKeyManager.TRS_ATTRS))
        if no_key_axis:
            msg += " {0} axis channel(s) not keyed in {1}.".format(
                len(no_key_axis), src_layer)
        if no_key_other:
            msg += " No key in {0}: {1}.".format(
                src_layer, LayerKeyManager._brief(no_key_other))
        if missing:
            msg += " Channel missing: {0}.".format(LayerKeyManager._brief(missing))
        if failed:
            msg += " Paste failed (locked?): {0}.".format(
                LayerKeyManager._brief(failed))

        return (moved, msg)

    # ==================================================
    # 내부 헬퍼
    # ==================================================

    @staticmethod
    def _cut_source(plug, src_layer, root, start, end):
        """소스 레이어 커브에서 옮긴 키를 지운다. 지웠으면 True.

        `cutKey` 에는 animLayer 플래그가 없으므로(맨 위 §3) 커브 노드를 직접 찾아 지운다.
        구간의 키를 다 지우면 마야가 **커브 노드까지 지운다** - 뒤에서 그 이름을 다시
        쓰지 않도록 여기서 마무리한다.
        """
        curve = LayerKeyManager.layer_curve(plug, src_layer, root)
        if not curve:
            return False
        try:
            if start is None:
                cmds.cutKey(curve, clear=True)
            else:
                cmds.cutKey(curve, time=(start, end), clear=True)
        except Exception:
            return False
        return True

    # --------------------------------------------------
    # Move + keep_result : 최종값 보존 (맨 위 §6 · §7)
    # --------------------------------------------------

    # enum (실측) : scaleAccumulationMode Additive(0):Multiply(1), rotationAccumulationMode By Component(0):By Layer(1)
    SCALE_MULTIPLY = 1
    ROT_BY_LAYER = 1

    @staticmethod
    def _blend_chain(plug):
        """plug 앞단의 animBlendNode 사슬 [(node, suffix), ...] - **맨 위 레이어부터 맨 아래로**.

        plug <- bnTop.output[X] <- bnTop.inputA[X] <- bnNext.output[X] ... 를 따라 내려간다.
        레이어에 안 든 plug 는 빈 리스트. suffix 는 회전(`outputX`)처럼 compound 자식일 때의 꼬리.
        """
        chain = []
        cur = plug
        for _ in range(128):
            srcs = cmds.listConnections(cur, source=True, destination=False, plugs=True,
                                        skipConversionNodes=True) or []
            if not srcs:
                break
            node, attr = srcs[0].split(".", 1)
            if (not cmds.nodeType(node).startswith("animBlendNode")
                    or not attr.startswith("output")):
                break
            suffix = attr[len("output"):]
            chain.append((node, suffix))
            cur = node + ".inputA" + suffix
        return chain

    @staticmethod
    def _layer_nodes(layer):
        try:
            return set(cmds.animLayer(layer, q=True, blendNodes=True) or [])
        except Exception:
            return set()

    @staticmethod
    def _layer_kind(layer, root):
        if layer == root:
            return "base"
        try:
            return "override" if cmds.getAttr(layer + ".override") else "additive"
        except Exception:
            return "additive"

    @staticmethod
    def _layer_weight(layer, root):
        """레이어 weight. Base 는 1. 애니메이션돼 있으면 None."""
        if layer == root:
            return 1.0
        try:
            if cmds.listConnections(layer + ".weight", source=True, destination=False):
                return None
            return float(cmds.getAttr(layer + ".weight"))
        except Exception:
            return 1.0

    @staticmethod
    def _static(input_plug):
        """blend 노드 입력이 커브 없이 들고 있는 정적 값. 연결돼 있으면(= 애니메이션) None."""
        try:
            if cmds.listConnections(input_plug, source=True, destination=False):
                return None
            return float(cmds.getAttr(input_plug))
        except Exception:
            return None

    @staticmethod
    def _insert_fixed(curve, t):
        """모양 보존 키(`setKeyframe -insert`) + 탄젠트 고정. 이미 키가 있으면 값은 그대로, 탄젠트만 고정된다."""
        cmds.setKeyframe(curve, insert=True, time=(t, t))
        cmds.keyTangent(curve, e=True, time=(t, t), itt="fixed", ott="fixed")

    @staticmethod
    def _prep_source_range(curve, start, end):
        """구간 이동 전에 소스 커브의 경계 모양을 고정한다. (구간 앞에 키가 있나, 뒤에 키가 있나) 를 돌려준다.

        앞에 키가 있으면 `s-1`(남는 쪽) · `s`(옮겨지는 쪽) 에, 뒤에 키가 있으면 `e` · `e+1` 에 모양 보존 키를
        박고 탄젠트를 고정한다. 바로 바깥 이웃 키(auto 탄젠트는 이웃이 바뀌면 다시 계산된다)도 고정해
        구간 밖 커브가 잘라낸 뒤에도 그대로이게 한다.
        """
        try:
            times = cmds.keyframe(curve, q=True, timeChange=True) or []
        except Exception:
            times = []
        before = [t for t in times if t < start]
        after = [t for t in times if t > end]
        has_before, has_after = bool(before), bool(after)
        try:
            if has_before:
                p = max(before)
                cmds.keyTangent(curve, e=True, time=(p, p), itt="fixed", ott="fixed")
                LayerKeyManager._insert_fixed(curve, start - 1)
                LayerKeyManager._insert_fixed(curve, start)
            if has_after:
                n = min(after)
                cmds.keyTangent(curve, e=True, time=(n, n), itt="fixed", ott="fixed")
                LayerKeyManager._insert_fixed(curve, end)
                LayerKeyManager._insert_fixed(curve, end + 1)
        except Exception:
            pass
        return (has_before, has_after)

    @staticmethod
    def _move_info(plug, attr, src, dst, root, src_curve, start, end, edges,
                   dst_member, note):
        """붙여넣기 **전에** 읽어야 하는 것들을 모은다. 보존이 불가능한 채널이면 None(이유는 note 로).

        dst_member : 이 plug 가 (멤버 추가 전에) 이미 대상 레이어 멤버였나. override 대상이 새 멤버면
                     구간 이동 때 구간 밖까지 덮어 버리므로 경고만 한다.

        돌려주는 사전:
            src_kind / dst_kind : "base" | "additive" | "override"
            src_input           : 잘라낸 뒤 identity 를 써 넣을 소스 blend 입력 plug (override 소스는 None - 멤버에서 뺀다)
            src_identity        : 그 identity 값 (0, multiply 스케일은 1)
            compose             : 붙여넣은 키에 합성할 대상의 정적값 ("add"|"mul", 값) 또는 None
            outside             : 구간 이동일 때 대상 커브의 `s-1` · `e+1` 키 값(대상이 밖에서 내던 정적값) 또는 None
        """
        chain = LayerKeyManager._blend_chain(plug)
        if not chain:
            note("channel is not driven by an anim layer - not kept", attr)
            return None
        for node, _ in chain:
            if not cmds.nodeType(node).startswith("animBlendNodeAdditive"):
                note("non-numeric channel (boolean/enum) - not kept", attr)
                return None

        src_kind = LayerKeyManager._layer_kind(src, root)
        dst_kind = LayerKeyManager._layer_kind(dst, root)

        def find(layer):
            nodes = LayerKeyManager._layer_nodes(layer)
            for node, suffix in chain:
                if node in nodes:
                    return node, suffix
            return None, None

        bottom_node, bottom_suf = chain[-1]
        base_input = bottom_node + ".inputA" + bottom_suf

        src_node = src_suf = None
        if src_kind != "base":
            src_node, src_suf = find(src)
            if not src_node:
                note("no blend node on '{0}' - not kept".format(src), attr)
                return None
        dst_node = dst_suf = None
        if dst_kind != "base":
            dst_node, dst_suf = find(dst)
            if not dst_node:
                note("could not be added to '{0}' - not kept".format(dst), attr)
                return None

        # 채널 성격은 blend 노드 타입으로 (attr 이름은 "sx" 든 "scaleX" 든 상관없이)
        ntype = cmds.nodeType(bottom_node)
        is_scale = (ntype == "animBlendNodeAdditiveScale")
        is_rot = (ntype == "animBlendNodeAdditiveRotation")

        def multiply(layer):
            if not is_scale or layer == root:
                return False
            try:
                return int(cmds.getAttr(layer + ".scaleAccumulationMode")) == LayerKeyManager.SCALE_MULTIPLY
            except Exception:
                return False

        def by_layer(layer):
            if not is_rot or layer == root:
                return False
            try:
                return int(cmds.getAttr(layer + ".rotationAccumulationMode")) == LayerKeyManager.ROT_BY_LAYER
            except Exception:
                return False

        def ident(layer):
            return 1.0 if multiply(layer) else 0.0

        # 대상이 커브 없이 들고 있던 정적값 d (커브가 있으면 None = replace 로 덮인다)
        dst_input = base_input if dst_kind == "base" else dst_node + ".inputB" + dst_suf
        d = None
        if LayerKeyManager.layer_curve(plug, dst, root):
            note("destination already has keys - replaced, not merged "
                 "(use Bake > Merge Layers)", attr)
        else:
            d = LayerKeyManager._static(dst_input)
            if dst_kind == "override" and dst_member:
                # 키 없는 override 멤버는 정적값으로 이미 아래를 전부 덮고 있다 - "이동 전" 이 그 상수였다.
                note("'{0}' already overrides with a static value - the pasted keys "
                     "replace it".format(dst), attr)

        compose = None
        src_input = None
        src_identity = 0.0
        mode_layer = dst if dst_kind != "base" else src   # 합성 규칙을 정하는 레이어

        if src_kind == "base":
            src_input = base_input
            src_identity = ident(dst)
            if dst_kind == "additive" and d is not None:
                compose = ("mul" if multiply(dst) else "add", d)

        elif src_kind == "additive":
            src_input = src_node + ".inputB" + src_suf
            src_identity = ident(src)
            if dst_kind == "additive":
                if is_scale and multiply(src) != multiply(dst):
                    note("scale accumulation mode differs between '{0}' and '{1}' - "
                         "scale not exact".format(src, dst))
                if d is not None:
                    compose = ("mul" if multiply(dst) else "add", d)
            elif dst_kind == "base":
                if d is not None:
                    compose = ("mul" if multiply(src) else "add", d)
            else:   # override 대상 : 소스 아래의 값까지 절대값으로 담아야 한다
                below = LayerKeyManager._static(src_node + ".inputA" + src_suf)
                if below is None:
                    note("layers below '{0}' are animated - override destination "
                         "not exact".format(src), attr)
                else:
                    compose = ("mul" if multiply(src) else "add", below)

        else:   # override 소스 : identity 가 없다 -> 커브를 다 옮긴 뒤 멤버에서 뺀다
            if start is not None and (edges[0] or edges[1]):
                note("'{0}' is an override layer with keys outside the range - "
                     "cannot neutralize the range only".format(src))
                return None
            if dst_kind == "additive":
                below = LayerKeyManager._static(src_node + ".inputA" + src_suf)
                if below is None:
                    note("layers below '{0}' are animated - not exact".format(src), attr)
                elif multiply(dst):
                    if d is not None and abs(below) > 1e-12:
                        compose = ("mul", d / below)
                elif d is not None:
                    compose = ("add", d - below)

        if (is_rot and compose and abs(compose[1]) > 1e-9 and by_layer(mode_layer)):
            note("'{0}' rotates by layer and a non-zero rotation had to be folded in - "
                 "rotation not exact".format(mode_layer))

        outside = None
        if start is not None and d is not None:
            outside = d
            if dst_kind == "override" and not dst_member:
                note("'{0}' is an override layer the channel was not in - it now overrides "
                     "outside the range too".format(dst), attr)

        return {
            "plug": plug, "attr": attr, "src": src, "dst": dst, "root": root,
            "src_curve": src_curve, "start": start, "end": end, "edges": edges,
            "src_kind": src_kind, "dst_kind": dst_kind,
            "src_input": src_input, "src_identity": src_identity,
            "compose": compose, "outside": outside,
        }

    @staticmethod
    def _compose_destination(info):
        """붙여넣은 키에 대상의 정적값을 합성하고, 구간 이동이면 대상 커브 바깥(`s-1` · `e+1`)에 그 정적값 키를 둔다."""
        curve = LayerKeyManager.layer_curve(info["plug"], info["dst"], info["root"])
        if not curve:
            return
        start, end = info["start"], info["end"]
        tk = {} if start is None else {"time": (start, end)}
        compose = info["compose"]
        try:
            if compose:
                op, v = compose
                if op == "add":
                    if abs(v) > 1e-12:
                        cmds.keyframe(curve, e=True, relative=True, valueChange=v, **tk)
                elif abs(v - 1.0) > 1e-12:
                    cmds.scaleKey(curve, valueScale=v, valuePivot=0.0, **tk)
            if info["outside"] is not None:
                has_before, has_after = info["edges"]
                if has_before:
                    cmds.setKeyframe(curve, time=(start - 1, start - 1), value=info["outside"])
                if has_after:
                    cmds.setKeyframe(curve, time=(end + 1, end + 1), value=info["outside"])
        except Exception:
            pass

    @staticmethod
    def _neutralize_source(info):
        """잘라낸 뒤 소스가 더 이상 기여하지 않게 한다. 했으면 True.

        커브가 통째로 사라졌으면 blend 입력에 남은 정적값을 identity 로(override 소스는 멤버에서 뺀다),
        구간만 잘라 커브가 남아 있으면 `s`(step) · `e` 에 identity 키를 둔다.
        """
        plug = info["plug"]
        curve = info["src_curve"]
        alive = False
        try:
            alive = bool(cmds.objExists(curve)
                         and (cmds.keyframe(curve, q=True, keyframeCount=True) or 0))
        except Exception:
            alive = False
        try:
            if info["src_kind"] == "override":
                cmds.animLayer(info["src"], e=True, removeAttribute=plug)
                return True
            v = info["src_identity"]
            if alive:
                s, e = info["start"], info["end"]
                cmds.setKeyframe(curve, time=(s, s), value=v, outTangentType="step")
                cmds.setKeyframe(curve, time=(e, e), value=v)
                return True
            if info["src_input"]:
                cmds.setAttr(info["src_input"], v)
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def _scope_text(attrs):
        """로그에 쓸 "무엇을 옮겼나" 한 조각.

        9축이 전부 켜져 있으면(기본값) 이름 아홉 개를 늘어놓지 않고 `TRS 9 axes` 로 접는다.
        """
        trs = [a for a in attrs if a in LayerKeyManager.TRS_ATTRS]
        other = [a for a in attrs if a not in LayerKeyManager.TRS_ATTRS]

        parts = []
        if len(trs) == len(LayerKeyManager.COPY_ATTRS):
            parts.append("TRS 9 axes")
        elif trs:
            parts.append("+".join(trs))
        if other:
            parts.append("+".join(other))

        return ", ".join(parts) if parts else "none"

    @staticmethod
    def _brief(names, limit=8):
        """이름 목록을 로그 한 줄에 담을 만큼만 줄인다(Copy Key 탭과 같은 규칙)."""
        uniq = sorted(set(names))
        if len(uniq) <= limit:
            return ", ".join(uniq)
        return "{0} (+{1} more)".format(", ".join(uniq[:limit]), len(uniq) - limit)
