# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-15
# A00110_animTool - Base -> Target 애니메이션 키 복사 + 축별 값 반전(Reverse) 핵심 로직 (maya.cmds, UI 비의존)
# 레거시 01_Modules/JUN_PY_CopyPasteKey_V03_01.py 의 JUN_cmd_copyKey_V02 알고리즘을 이식

import maya.cmds as cmds


class CopyKeyManager:
    """
    Base 리스트의 각 오브젝트 애니메이션 키를 같은 인덱스의 Target 오브젝트로 복사한다.
    시간 범위(start, end)로 copyKey 한 뒤 paste_option 모드로 pasteKey 하고,
    체크된 축은 timePivot=start 기준으로 값을 반전(valueScale=-1)한다.

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

    # cmds.pasteKey 의 option 인자로 쓸 수 있는 유효값(UI 콤보와 단일 소스). 기본은 "insert".
    PASTE_OPTIONS = [
        "insert", "replace", "replaceCompletely", "merge",
        "scaleInsert", "scaleReplace", "scaleMerge",
        "fitInsert", "fitReplace", "fitMerge",
    ]

    @staticmethod
    def copy_keys(base_list, tgt_list, start, end, reverse_flags, paste_option="insert"):
        """
        base_list[i] -> tgt_list[i] 로 time=(start, end) 키를 복사한다.

        base_list, tgt_list : 오브젝트 이름 리스트. 같은 인덱스끼리 매칭.
        start, end          : copyKey 시간 범위.
        reverse_flags       : {"tx": bool, "ty": bool, ...}. 체크된 축은 valueScale=-1 로 반전.
        paste_option        : cmds.pasteKey option (PASTE_OPTIONS 중 하나, 기본 "insert").
        반환                : (처리한 쌍 수, 메시지)
        """
        if not base_list:
            return (0, "[Warning] Base list is empty.")
        if not tgt_list:
            return (0, "[Warning] Target list is empty.")

        # 목록 밖 값이면 기본값으로 폴백(방어).
        if paste_option not in CopyKeyManager.PASTE_OPTIONS:
            paste_option = "insert"

        # 매칭 가능한 쌍 수(짧은 쪽 기준). 불일치는 메시지에 집계.
        pair_count = min(len(base_list), len(tgt_list))

        done = 0
        skipped = 0

        cmds.undoInfo(openChunk=True)
        try:
            for i in range(pair_count):
                base = base_list[i]
                tgt = tgt_list[i]

                try:
                    cmds.copyKey(base, time=(start, end))
                    cmds.pasteKey(tgt, option=paste_option)

                    for attr, key in CopyKeyManager.AXES:
                        scale = -1 if reverse_flags.get(key) else 1
                        if scale == 1:
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
        finally:
            cmds.undoInfo(closeChunk=True)

        msg = "{0} pairs copied (option: {1}).".format(done, paste_option)
        if skipped:
            msg += " {0} skipped (no keys / paste failed).".format(skipped)
        if len(base_list) != len(tgt_list):
            msg += " [Warning] Base({0}) / Target({1}) count mismatch.".format(
                len(base_list), len(tgt_list))

        return (done, msg)
