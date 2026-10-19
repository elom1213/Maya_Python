# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00110_animTool_V02 - Key > Key Attrs 핵심 로직 (maya.cmds, UI 비의존)
#
# A00290_BSTool_V02 의 Key every target(EditBSManager.key_every_target) 을 일반화한 것.
#   - BSTool 은 blendShape 노드의 weight[i] 전부를 대상으로 한다.
#   - 여기서는 **사용자가 고른 오브젝트 x 고른 어트리뷰트** 를 대상으로 한다.
# 키 규칙은 BSTool 과 같다: n 번째 플러그를 프레임 start+n 에서 1, 앞뒤 프레임에서 0.
# 순서는 오브젝트 리스트 순 -> 어트리뷰트 리스트 순 (obj1.a, obj1.b, obj2.a, ...).

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


class AttrKeyManager:

    # 'Channel Box only' 를 끈 경우 나열할 수치형 어트리뷰트 타입 (setKeyframe 대상)
    NUMERIC_TYPES = {
        "double", "float", "long", "short", "byte", "bool", "enum",
        "doubleLinear", "doubleAngle", "floatLinear", "floatAngle", "time",
    }

    # ==================================================
    # 조회
    # ==================================================

    @staticmethod
    def _alias_map(node):
        """{'weight[0]': 'smile', ...} - blendShape 타겟처럼 별칭이 있는 플러그를 이름으로 보이게."""
        pairs = cmds.aliasAttr(node, query=True) or []
        return {pairs[i + 1]: pairs[i] for i in range(0, len(pairs) - 1, 2)}

    @staticmethod
    def _is_keyable_plug(plug):
        """잠기지 않은 수치형 플러그인가."""
        try:
            if cmds.getAttr(plug, lock=True):
                return False
            return cmds.getAttr(plug, type=True) in AttrKeyManager.NUMERIC_TYPES
        except (RuntimeError, ValueError):
            return False

    @staticmethod
    def _is_driven(plug):
        """애니 커브 / 애니 레이어가 아닌 노드(컨스트레인트 · 드리븐 키 · 익스프레션 등)가 구동하는가.

        그런 플러그에 setKeyframe 하면 마야가 pairBlend 를 끼워 리그 연결을 바꾸므로 건너뛴다.
        """
        sources = cmds.listConnections(plug, source=True, destination=False,
                                       skipConversionNodes=True) or []
        for src in sources:
            if cmds.nodeType(src).startswith("animCurveT"):
                continue        # 시간 기반 애니 커브(TL/TA/TU/TT) = 이미 키가 있는 것. 드리븐 키(U*)는 아님
            if "animBlendNodeBase" in (cmds.nodeType(src, inherited=True) or []):
                continue        # 애니 레이어
            return True
        return False

    @staticmethod
    def _expand_multi(obj, names):
        """listAttr 는 multi 어트리뷰트를 부모 이름('weight')으로만 준다 -> 존재하는 원소('weight[0]')로 편다.

        blendShape 타겟이 이 경우다 (채널박스는 원소를 별칭으로 보여 준다).
        중첩 경로('inputTarget.vertex.xVertex')는 그대로 두고 키 가능 검사에서 걸러진다.
        """
        for name in names:
            if "." not in name and "[" not in name:
                try:
                    is_multi = cmds.attributeQuery(name, node=obj, multi=True)
                except RuntimeError:
                    is_multi = False
                if is_multi:
                    plug = "{0}.{1}".format(obj, name)
                    for idx in cmds.getAttr(plug, multiIndices=True) or []:
                        yield "{0}[{1}]".format(name, idx)
                    continue
            yield name

    @staticmethod
    def list_object_attrs(obj, channel_box_only=True):
        """한 오브젝트에서 키를 걸 수 있는 어트리뷰트 이름들 (채널박스 순서)."""
        # 채널박스 = keyable + (non-keyable 이지만 채널박스에 표시)
        names = (cmds.listAttr(obj, keyable=True) or []) + \
                (cmds.listAttr(obj, channelBox=True) or [])
        if not channel_box_only:
            names += cmds.listAttr(obj, scalar=True, settable=True) or []

        aliases = AttrKeyManager._alias_map(obj)
        result = []
        seen = set()
        for name in AttrKeyManager._expand_multi(obj, names):
            name = aliases.get(name, name)
            if name in seen:
                continue
            seen.add(name)
            if AttrKeyManager._is_keyable_plug("{0}.{1}".format(obj, name)):
                result.append(name)
        return result

    @staticmethod
    def list_attrs(objects, channel_box_only=True):
        """오브젝트들의 어트리뷰트 합집합 (처음 나온 순서 유지).

        반환: (이름 리스트, {이름: 그 어트리뷰트를 가진 오브젝트 리스트})
        """
        names = []
        owners = {}
        for obj in objects:
            if not cmds.objExists(obj):
                continue
            for name in AttrKeyManager.list_object_attrs(obj, channel_box_only):
                if name not in owners:
                    owners[name] = []
                    names.append(name)
                owners[name].append(obj)
        return names, owners

    # ==================================================
    # Key every attribute
    # ==================================================

    @staticmethod
    def key_every_attr(objects, attrs, start=0):
        """고른 플러그를 차례대로 0 -> 1 -> 0 으로 키한다 (BSTool Key every target 과 같은 규칙).

        n 번째 플러그: 프레임 start+n 에서 1, start+n-1 / start+n+1 에서 0.
        오브젝트에 없거나 잠긴 / 다른 노드가 구동하는 플러그는 건너뛰고 프레임도 쓰지 않는다.

        반환: (키를 건 플러그 수, 메시지, 건너뛴 플러그 리스트)
        """
        objects = [o for o in (objects or []) if cmds.objExists(o)]
        if not objects:
            return 0, "[Warning] No valid object in the list.", []
        if not attrs:
            return 0, "[Warning] No attribute checked.", []

        keyed = 0
        skipped = []
        frame = start
        with undo_chunk():
            for obj in objects:
                for attr in attrs:
                    plug = "{0}.{1}".format(obj, attr)
                    if not cmds.objExists(plug) or not AttrKeyManager._is_keyable_plug(plug) \
                            or AttrKeyManager._is_driven(plug):
                        skipped.append(plug)
                        continue
                    try:
                        cmds.setKeyframe(plug, t=frame - 1, v=0)
                        cmds.setKeyframe(plug, t=frame, v=1)
                        cmds.setKeyframe(plug, t=frame + 1, v=0)
                    except RuntimeError:
                        skipped.append(plug)
                        continue
                    keyed += 1
                    frame += 1

        if not keyed:
            return 0, "[Warning] No plug could be keyed ({0} skipped).".format(len(skipped)), skipped

        msg = "[Key every attribute] {0} plug(s) keyed on frames {1} - {2}.".format(
            keyed, start, start + keyed - 1)
        if skipped:
            msg += " {0} skipped (missing, locked or driven).".format(len(skipped))
        return keyed, msg, skipped
