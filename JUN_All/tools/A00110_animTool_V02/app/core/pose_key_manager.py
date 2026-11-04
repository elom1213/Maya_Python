# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-04
# A00110_animTool_V02 - 선택 오브젝트의 현재 프레임에 pose 키를 설정하는 핵심 로직 (maya.cmds, UI 비의존)
# A00030_quickTool 의 JUN_cmd_anim_rot_x_z_to_zero 기능을 6축 + 축별 토글로 일반화한 것
# v02.41 - use_current=True : 입력 값 대신 **지금 프레임의 현재 값**으로 키 (체크된 축만, UI `Use current values`).
#          키 없이 움직여 둔 값도 그대로 키가 된다. 활성 애니메이션 레이어에서는 최종 값이 그대로 남는다.
# v02.44 - current_axes : **축마다** 현재 값 여부 (UI 행마다 `Current`). use_current=True 는 전부 current.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


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
    def set_pose_keys(axis_values, objects=None, use_current=False, current_axes=None):
        """
        선택 오브젝트(들)의 현재 프레임에 각 축 값으로 setKeyframe.

        axis_values: {"rx": float, "rz": float, "ty": float, ...}
                     (체크된 축만 포함된 dict)
        objects    : 명시하지 않으면 현재 선택을 사용.
        use_current: True 면 axis_values 의 값은 무시하고(축 선택만 쓴다) 각 채널의 현재 값으로 키.
        current_axes: 이 축들만 현재 값으로 (v02.44 축마다). 나머지 축은 axis_values 값.
        반환       : (처리한 오브젝트 수, 메시지)
        """
        sel = objects if objects else (cmds.ls(sl=True) or [])

        if not sel:
            return (0, "No objects selected.")

        if not axis_values:
            return (0, "No axis checked.")

        current = set(axis_values) if use_current else set(current_axes or []) & set(axis_values)

        # 현재 값은 키를 찍기 전에 전부 읽는다 (앞 키가 다른 채널 평가를 바꿀 수 있다)
        plan = []
        for obj in sel:
            for attr, val in axis_values.items():
                if attr in current:
                    try:
                        val = cmds.getAttr(f"{obj}.{attr}")
                    except Exception:                       # noqa: BLE001
                        continue
                plan.append((obj, attr, float(val)))

        with undo_chunk():
            for obj, attr, val in plan:
                cmds.setKeyframe(obj, at=attr, v=val)

        axes = ", ".join(a + ("=current" if a in current else "") for a in axis_values)
        return (
            len(sel),
            f"{len(sel)} objects : pose key set on current frame  ({axes})"
        )
