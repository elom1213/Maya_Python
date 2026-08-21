# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00110_animTool_V02 - Base -> Target 애니메이션 키 복사 + 축별 값 반전(Reverse) 핵심 로직 (maya.cmds, UI 비의존)
# 레거시 01_Modules/JUN_PY_CopyPasteKey_V03_01.py 의 JUN_cmd_copyKey_V02 알고리즘을 이식

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


class CopyKeyManager:
    """
    Base 리스트의 각 오브젝트 애니메이션 키를 Target 오브젝트로 복사한다.
    시간 범위(start, end)로 copyKey 한 뒤 paste_option 모드로 pasteKey 하고,
    체크된 축은 timePivot=start 기준으로 값을 반전(valueScale=-1)한다.

    매칭은 두 가지다.
      n->n (기본 동작) : Base[i] -> Target[i], 같은 인덱스끼리. 짧은 쪽 길이만큼만.
      1->n             : Base 가 **정확히 1개**일 때 그 하나를 **모든** Target 에 복사.
    `one_to_many=True`(기본) 여도 Base 가 1개가 아니면 **그냥 n->n 으로 간다** —
    옵션이 켜져 있다고 해서 여러 Base 를 가진 평소 작업이 막히지는 않는다.
    (Follow 탭의 1<-n 은 개수가 안 맞으면 에러를 내지만, 여기는 폴백이 요구 사항이다.)

    레거시 JUN_cmd_copyKey_V02 를 UI 비의존 정적 메서드로 옮긴 것.
    pose_key_manager.PoseKeyManager 와 동일한 스타일(정적 메서드 + undoInfo 청크 + (count, msg)).
    """

    # 축 정의: (attr 전체 이름, reverse_flags 키). UI 체크박스 순서와 일치.
    AXES = [
        ("translateX", "tx"),
        ("translateY", "ty"),
        ("translateZ", "tz"),
        ("rotateX", "rx"),
        ("rotateY", "ry"),
        ("rotateZ", "rz"),
    ]

    # 복사 대상 어트리뷰트 정의: (attr_flags 키, attr 전체 이름). UI 체크박스 순서와 일치.
    # Translate / Rotate / Scale 을 축 단위로 골라 복사할 때 쓴다.
    COPY_ATTRS = [
        ("tx", "translateX"),
        ("ty", "translateY"),
        ("tz", "translateZ"),
        ("rx", "rotateX"),
        ("ry", "rotateY"),
        ("rz", "rotateZ"),
        ("sx", "scaleX"),
        ("sy", "scaleY"),
        ("sz", "scaleZ"),
    ]

    # cmds.pasteKey 의 option 인자로 쓸 수 있는 유효값(UI 콤보와 단일 소스). 기본은 "insert".
    PASTE_OPTIONS = [
        "insert", "replace", "replaceCompletely", "merge",
        "scaleInsert", "scaleReplace", "scaleMerge",
        "fitInsert", "fitReplace", "fitMerge",
    ]

    @staticmethod
    def resolve_attrs(attr_flags):
        """
        attr_flags({"tx": bool, ...}) 를 copyKey 에 넘길 어트리뷰트 이름 리스트로 바꾼다.

        None 을 반환하면 **필터 없음**(= copyKey 가 애니메이션된 어트리뷰트를 전부 복사)이다.
        9축이 모두 켜져 있거나 flags 가 비어 있으면 None 을 준다 — 필터를 걸면 커스텀
        어트리뷰트(예: ikBlend, 페이셜 슬라이더)의 키가 빠져 버리므로, "전부 체크" 는
        **필터를 아예 걸지 않는** 예전 동작 그대로 두는 게 맞다.
        """
        if not attr_flags:
            return None

        attrs = [attr for key, attr in CopyKeyManager.COPY_ATTRS if attr_flags.get(key)]

        if len(attrs) == len(CopyKeyManager.COPY_ATTRS):
            return None
        return attrs

    @staticmethod
    def copy_keys(base_list, tgt_list, start, end, reverse_flags, paste_option="insert",
                  one_to_many=True, attr_flags=None):
        """
        Base -> Target 으로 time=(start, end) 키를 복사한다.

        base_list, tgt_list : 오브젝트 이름 리스트.
        start, end          : copyKey 시간 범위.
        reverse_flags       : {"tx": bool, "ty": bool, ...}. 체크된 축은 valueScale=-1 로 반전.
        paste_option        : cmds.pasteKey option (PASTE_OPTIONS 중 하나, 기본 "insert").
        one_to_many         : True(기본)이고 **Base 가 정확히 1개**면 그 하나를 모든 Target 에
                              복사한다(1->n). Base 가 2개 이상이면 이 값과 무관하게 n->n.
        attr_flags          : {"tx": bool, ... "sz": bool} 9축 선택. None 이거나 9축이 모두
                              True 면 필터를 걸지 않는다(= 애니메이션된 어트리뷰트 전부 복사).
                              일부만 True 면 그 어트리뷰트만 copyKey 한다.
        반환                : (처리한 쌍 수, 메시지)
        """
        if not base_list:
            return (0, "[Warning] Base list is empty.")
        if not tgt_list:
            return (0, "[Warning] Target list is empty.")

        # 목록 밖 값이면 기본값으로 폴백(방어).
        if paste_option not in CopyKeyManager.PASTE_OPTIONS:
            paste_option = "insert"

        # 어트리뷰트 선택 해석. None = 필터 없음, [] = 하나도 안 골랐다(할 일 없음).
        attrs = CopyKeyManager.resolve_attrs(attr_flags)
        if attrs is not None and not attrs:
            return (0, "[Warning] No attribute checked (Translate / Rotate / Scale).")

        # ---- 매칭 구성 ----
        # 1->n 은 Base 가 정확히 1개일 때만 성립한다. 옵션이 켜져 있어도 Base 가 여러 개면
        # 평소대로 n->n(같은 인덱스, 짧은 쪽 기준)으로 간다.
        fan_out = bool(one_to_many) and len(base_list) == 1
        if fan_out:
            pairs = [(base_list[0], tgt) for tgt in tgt_list]
        else:
            pair_count = min(len(base_list), len(tgt_list))
            pairs = list(zip(base_list[:pair_count], tgt_list[:pair_count]))

        done = 0
        skipped = 0

        with undo_chunk():
            for base, tgt in pairs:
                try:
                    if attrs is None:
                        curves = cmds.copyKey(base, time=(start, end))
                    else:
                        curves = cmds.copyKey(base, time=(start, end), attribute=attrs)

                    # 고른 어트리뷰트에 키가 하나도 없으면 클립보드가 비어 pasteKey 가 실패한다.
                    # 예외로 흘리지 말고 여기서 건너뛴다.
                    if not curves:
                        skipped += 1
                        continue

                    cmds.pasteKey(tgt, option=paste_option)

                    for attr, key in CopyKeyManager.AXES:
                        scale = -1 if reverse_flags.get(key) else 1
                        if scale == 1:
                            continue
                        # 복사하지 않은 축은 반전 대상이 아니다(대상의 기존 키가 뒤집힌다).
                        if attrs is not None and attr not in attrs:
                            continue
                        cmds.scaleKey(
                            tgt + "." + attr,
                            timeScale=0, timePivot=start,
                            valueScale=scale, valuePivot=0,
                        )
                    done += 1
                except Exception:
                    # 키가 없거나 붙여넣기 실패한 쌍은 건너뛴다.
                    skipped += 1

        mode = "1->n" if fan_out else "n->n"
        scope = "all attrs" if attrs is None else "+".join(attrs)
        msg = "{0} pairs copied ({1}, option: {2}, attrs: {3}).".format(
            done, mode, paste_option, scope)
        if skipped:
            msg += " {0} skipped (no keys / paste failed).".format(skipped)
        # 개수 불일치 경고는 n->n 에서만 뜻이 있다(1->n 은 개수가 달라도 정상).
        if not fan_out and len(base_list) != len(tgt_list):
            msg += " [Warning] Base({0}) / Target({1}) count mismatch.".format(
                len(base_list), len(tgt_list))
            if one_to_many:
                msg += " (1->n needs exactly 1 Base, got {0}.)".format(len(base_list))

        return (done, msg)
