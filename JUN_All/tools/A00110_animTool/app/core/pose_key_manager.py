# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-12
# A00110_animTool - 선택 오브젝트의 현재 프레임에 pose 키를 설정하는 핵심 로직 (maya.cmds, UI 비의존)
# A00030_quickTool 의 JUN_cmd_anim_rot_x_z_to_zero 기능을 6축 + 축별 토글로 일반화한 것

import maya.cmds as cmds


class PoseKeyManager:
    """
    선택한 오브젝트(들)의 현재 타임라인 프레임에 회전/이동 값을 키프레임으로 설정한다.

    원본(A00030)은 rotate X / rotate Z / translate Y 3축을 첫 번째 선택 오브젝트에만
    적용했지만, 여기서는 6축으로 확장하고 KeyframeManager 와 동일하게 선택 전체를 대상으로 한다.
    어떤 축을 적용할지는 호출부(UI)가 axis_values dict 로 결정한다(체크된 축만 포함).
    """

    # 축 정의: (attr, 표시 라벨). 표시 순서/라벨 고정.
    AXES = [
        ("rx", "rotate X"),
        ("ry", "rotate Y"),
        ("rz", "rotate Z"),
        ("tx", "translate X"),
        ("ty", "translate Y"),
        ("tz", "translate Z"),
    ]

    @staticmethod
    def set_pose_keys(axis_values, objects=None):
        """
        선택 오브젝트(들)의 현재 프레임에 각 축 값으로 setKeyframe.

        axis_values: {"rx": float, "rz": float, "ty": float, ...}
                     (체크된 축만 포함된 dict)
        objects    : 명시하지 않으면 현재 선택을 사용.
        반환       : (처리한 오브젝트 수, 메시지)
        """
        sel = objects if objects else (cmds.ls(sl=True) or [])

        if not sel:
            return (0, "No objects selected.")

        if not axis_values:
            return (0, "No axis checked.")

        cmds.undoInfo(openChunk=True)
        try:
            for obj in sel:
                for attr, val in axis_values.items():
                    cmds.setKeyframe(obj, at=attr, v=val)
        finally:
            cmds.undoInfo(closeChunk=True)

        axes = ", ".join(axis_values.keys())
        return (
            len(sel),
            f"{len(sel)} objects : pose key set on current frame  ({axes})"
        )
