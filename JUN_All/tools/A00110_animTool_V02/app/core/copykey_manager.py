# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-24
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

    복사 대상 채널은 두 갈래로 고른다.
      - 9축 체크박스(`attr_flags`) : Translate / Rotate / Scale x X/Y/Z
      - 커스텀 채널 목록(`custom_attrs`) : ikBlend, 페이셜 슬라이더처럼 사용자가 만든
        채널박스 어트리뷰트. `list_custom_attrs()` 로 Base 에서 뽑아 UI 가 넘겨 준다.
    커스텀을 하나도 안 고르고 9축이 전부 켜져 있으면 예전처럼 필터 없이 통째로 복사한다.

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

    # 9축이 이미 담당하는 이름(짧은 이름과 부모 compound 포함).
    # 커스텀 채널 목록을 만들 때 걸러 낸다.
    TRS_ATTRS = frozenset(
        [attr for _key, attr in COPY_ATTRS] +
        ["translate", "rotate", "scale", "t", "r", "s",
         "tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
    )

    # cmds.pasteKey 의 option 인자로 쓸 수 있는 유효값(UI 콤보와 단일 소스). 기본은 "insert".
    PASTE_OPTIONS = [
        "insert", "replace", "replaceCompletely", "merge",
        "scaleInsert", "scaleReplace", "scaleMerge",
        "fitInsert", "fitReplace", "fitMerge",
    ]

    # ==================================================
    # 조회 (UI 목록 채우기)
    # ==================================================

    @staticmethod
    def list_custom_attrs(objects, skip_trs=True):
        """오브젝트들의 **키 가능 + 채널박스 노출 + 잠기지 않은** 채널 합집합.

        첫 등장 순서를 지킨다(리스트에 담은 순서대로 채널이 나오도록).

        `listAttr(keyable=True, visible=True)` 가 곧 "채널박스에 뜨는 키 가능 채널"이다.
        채널박스에만 보이고 키는 못 찍는 채널(`setAttr -k false -cb true`)은 `-channelBox`
        쪽에 잡히므로 여기서는 빠진다 — 요청이 "채널박스에 노출된, 키프레임을 찍을 수 있는"
        어트리뷰트라서 그렇다. 잠긴 채널도 키를 못 찍으므로 `unlocked=True` 로 거른다.
        (같은 규칙을 fill_key_manager.FillKeyManager.list_keyable_attrs 도 쓴다.)

        skip_trs=True(기본)면 9축 체크박스가 이미 담당하는 translate/rotate/scale 을 빼고
        visibility 와 사용자 정의 채널만 남긴다.
        """
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
                if skip_trs and attr in CopyKeyManager.TRS_ATTRS:
                    continue
                seen.add(attr)
                found.append(attr)

        return found

    # ==================================================
    # 복사
    # ==================================================

    @staticmethod
    def resolve_attrs(attr_flags, custom_attrs=None):
        """
        attr_flags({"tx": bool, ...}) + custom_attrs(["ikBlend", ...]) 를
        copyKey 에 넘길 어트리뷰트 이름 리스트로 바꾼다.

        None 을 반환하면 **필터 없음**(= copyKey 가 애니메이션된 어트리뷰트를 전부 복사)이다.
        커스텀 채널을 하나도 지정하지 않은 상태에서 9축이 모두 켜져 있거나 flags 가 비어
        있으면 None 을 준다 — 커스텀 목록을 건드리지 않은 사용자는 예전과 완전히 같은
        동작(커스텀 어트리뷰트까지 통째로 복사)을 그대로 받는다.

        커스텀 채널을 하나라도 골랐으면 **명시 목록**으로 간다(체크된 9축 + 고른 커스텀).
        9축을 전부 켜 두면 "TRS 전부 + 고른 커스텀 채널"이 된다.
        """
        custom = []
        seen = set()
        for attr in (custom_attrs or []):
            attr = (attr or "").strip()
            if attr and attr not in seen:
                seen.add(attr)
                custom.append(attr)

        if not attr_flags:
            # 9축 정보가 없는 예전 호출부는 그대로 "필터 없음".
            # 커스텀만 넘어온 경우는 그 채널만 복사한다.
            return custom or None

        trs = [attr for key, attr in CopyKeyManager.COPY_ATTRS if attr_flags.get(key)]

        if not custom and len(trs) == len(CopyKeyManager.COPY_ATTRS):
            return None

        # 커스텀이 9축과 겹쳐 들어와도 한 번만 남긴다(같은 plug 를 두 번 붙여넣지 않도록).
        merged = list(trs)
        for attr in custom:
            if attr not in merged:
                merged.append(attr)
        return merged

    @staticmethod
    def copy_keys(base_list, tgt_list, start, end, reverse_flags, paste_option="insert",
                  one_to_many=True, attr_flags=None, custom_attrs=None):
        """
        Base -> Target 으로 time=(start, end) 키를 복사한다.

        base_list, tgt_list : 오브젝트 이름 리스트.
        start, end          : copyKey 시간 범위.
        reverse_flags       : {"tx": bool, "ty": bool, ...}. 체크된 축은 valueScale=-1 로 반전.
        paste_option        : cmds.pasteKey option (PASTE_OPTIONS 중 하나, 기본 "insert").
        one_to_many         : True(기본)이고 **Base 가 정확히 1개**면 그 하나를 모든 Target 에
                              복사한다(1->n). Base 가 2개 이상이면 이 값과 무관하게 n->n.
        attr_flags          : {"tx": bool, ... "sz": bool} 9축 선택.
        custom_attrs        : 채널박스 커스텀 채널 이름 목록(예: ["ikBlend", "visibility"]).
                              하나라도 있으면 명시 필터 경로로 간다.
        반환                : (처리한 쌍 수, 메시지)

        **명시 필터 경로는 채널(plug) 하나씩 copyKey/pasteKey 한다.** 노드 단위로
        `pasteKey(attribute=[...])` 를 쓰면 마야가 클립보드 커브를 **이름이 아니라 순서로**
        맞춰 버린다 — 클립보드에 myFloat 커브 하나만 있는데 attribute 로
        ["translateY", "myFloat"] 을 주면 그 커브가 **translateY 에 들어간다**(mayapy 2024
        확인). 채널 단위로 돌면 그 뒤섞임이 없고, 일부 채널에 키가 없어도 나머지는 붙는다.
        """
        if not base_list:
            return (0, "[Warning] Base list is empty.")
        if not tgt_list:
            return (0, "[Warning] Target list is empty.")

        # 목록 밖 값이면 기본값으로 폴백(방어).
        if paste_option not in CopyKeyManager.PASTE_OPTIONS:
            paste_option = "insert"

        # 어트리뷰트 선택 해석. None = 필터 없음, [] = 하나도 안 골랐다(할 일 없음).
        attrs = CopyKeyManager.resolve_attrs(attr_flags, custom_attrs)
        if attrs is not None and not attrs:
            return (0, "[Warning] No attribute checked (Translate / Rotate / Scale / Custom).")

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
        missing = []      # Base 나 Target 한쪽에 없는(또는 붙여넣기 실패한) 채널
        no_key = []       # 채널은 있는데 구간에 Base 키가 없는 것

        with undo_chunk():
            for base, tgt in pairs:
                if attrs is None:
                    copied = CopyKeyManager._copy_pair_all(
                        base, tgt, start, end, paste_option)
                else:
                    copied = CopyKeyManager._copy_pair_attrs(
                        base, tgt, start, end, paste_option, attrs, missing, no_key)

                if not copied:
                    skipped += 1
                    continue

                CopyKeyManager._apply_reverse(tgt, start, reverse_flags, copied)
                done += 1

        mode = "1->n" if fan_out else "n->n"
        scope = "all attrs" if attrs is None else "+".join(attrs)
        msg = "{0} pairs copied ({1}, option: {2}, attrs: {3}).".format(
            done, mode, paste_option, scope)
        if skipped:
            msg += " {0} skipped (no keys / paste failed).".format(skipped)
        if no_key:
            msg += " No key in range: {0}.".format(CopyKeyManager._brief(no_key))
        if missing:
            msg += " Channel missing or locked: {0}.".format(
                CopyKeyManager._brief(missing))
        # 개수 불일치 경고는 n->n 에서만 뜻이 있다(1->n 은 개수가 달라도 정상).
        if not fan_out and len(base_list) != len(tgt_list):
            msg += " [Warning] Base({0}) / Target({1}) count mismatch.".format(
                len(base_list), len(tgt_list))
            if one_to_many:
                msg += " (1->n needs exactly 1 Base, got {0}.)".format(len(base_list))

        return (done, msg)

    # ==================================================
    # 내부 헬퍼
    # ==================================================

    @staticmethod
    def _brief(names, limit=8):
        """채널 이름 목록을 로그 한 줄에 담을 만큼만 줄인다.

        9축을 전부 켜 둔 채 커스텀 채널을 고르면, 키가 없는 TRS 채널 이름이 아홉 개까지
        따라 붙어 로그가 읽히지 않는다. 나머지는 개수로만 적는다.
        """
        uniq = sorted(set(names))
        if len(uniq) <= limit:
            return ", ".join(uniq)
        return "{0} (+{1} more)".format(", ".join(uniq[:limit]), len(uniq) - limit)

    @staticmethod
    def _copy_pair_all(base, tgt, start, end, paste_option):
        """필터 없는 경로: 노드 단위로 통째 copy/paste.

        반환은 붙여넣은 채널 목록 대신 ["*"](= 전부)이다. 노드 단위 pasteKey 는 어떤
        채널이 들어갔는지 알려 주지 않으므로 Reverse 는 6축 전부를 대상으로 본다.
        """
        try:
            curves = cmds.copyKey(base, time=(start, end))
        except Exception:
            return []
        # 클립보드가 비면 pasteKey 가 실패한다. 예외로 흘리지 말고 건너뛴다.
        if not curves:
            return []
        try:
            cmds.pasteKey(tgt, option=paste_option)
        except Exception:
            return []
        return ["*"]

    @staticmethod
    def _copy_pair_attrs(base, tgt, start, end, paste_option, attrs, missing, no_key):
        """명시 필터 경로: 채널 하나씩 copy/paste. 반환은 실제로 붙여넣은 채널 목록."""
        copied = []
        for attr in attrs:
            src = "{0}.{1}".format(base, attr)
            dst = "{0}.{1}".format(tgt, attr)
            if not cmds.objExists(src) or not cmds.objExists(dst):
                missing.append(attr)
                continue
            try:
                if not cmds.copyKey(src, time=(start, end)):
                    no_key.append(attr)
                    continue
                cmds.pasteKey(dst, option=paste_option)
            except Exception:
                # 잠긴 채널 등 붙여넣기 불가("Nothing to paste to"). 나머지는 계속 간다.
                missing.append(attr)
                continue
            copied.append(attr)
        return copied

    @staticmethod
    def _apply_reverse(tgt, start, reverse_flags, copied_attrs):
        """체크된 축을 timePivot=start 기준으로 반전한다.

        **실제로 복사한 채널만** 뒤집는다 — 복사하지 않은 축까지 뒤집으면 타깃에 원래
        있던 키가 망가진다. copied_attrs 가 ["*"] 면 필터 없는 경로(전부 복사)라 6축 모두
        가 대상이다.
        """
        if not reverse_flags:
            return
        all_copied = "*" in copied_attrs
        for attr, key in CopyKeyManager.AXES:
            if not reverse_flags.get(key):
                continue
            if not all_copied and attr not in copied_attrs:
                continue
            try:
                cmds.scaleKey(
                    tgt + "." + attr,
                    timeScale=0, timePivot=start,
                    valueScale=-1, valuePivot=0,
                )
            except Exception:
                pass
