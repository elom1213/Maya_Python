# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-31
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
# 이 기능은 **커브 값을 그대로** 옮긴다 - 레이어 기여분을 다시 계산하지 않는다.
# 그래서 Base(절대값) -> additive 레이어처럼 성격이 다른 레이어로 옮기면 **최종 결과는
# 달라진다**(그 레이어에 그 값의 커브가 생기는 것뿐이다). 마야의 복사/붙여넣기와 같은
# 규칙이며, "이 레이어의 커브를 저 레이어로" 라는 요청에 맞는 동작이다.
# 최종 포즈를 유지한 채 레이어를 바꾸고 싶으면 Bake 탭을 쓴다.

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
                      paste_option=None, cut=False):
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

        moved = 0          # 실제로 붙여넣은 채널 수
        cut_count = 0      # 소스에서 지운 채널 수
        objs_done = set()
        missing_obj = []   # 씬에 없는 오브젝트
        missing = []       # plug 가 없는 채널
        no_key = []        # 소스 레이어에 (구간 안) 키가 없는 채널
        failed = []        # 붙여넣기 실패

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

                    # ---- 4) 잘라내기 : 붙여넣기가 성공한 뒤에만 소스를 지운다
                    if cut and LayerKeyManager._cut_source(plug, src_layer, root,
                                                           start, end):
                        cut_count += 1

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
