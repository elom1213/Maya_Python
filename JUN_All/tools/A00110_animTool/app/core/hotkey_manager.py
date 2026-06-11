# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-11
# A00110_animTool - Shift+A 핫키 라이프사이클 (maya.cmds, UI 비의존)
#
# 툴이 열려 있는 동안 Shift+A 를 hold_selected_keys 에 바인딩하고,
# 닫힐 때 원래 Shift+A 바인딩을 그대로 복원한다.
#
# 주의:
#  - keyShortcut 은 소문자 'a' + shiftModifier=True 로 지정한다 (.mhk 의 "s" -sht 관례).
#  - 현재 핫키 세트만(메모리) 수정하며 .mhk 원본 파일은 건드리지 않는다.
#  - 활성 세트가 잠긴 경우(예: Maya Default)에는 경고만 하고 전역 상태를 바꾸지 않는다.

import maya.cmds as cmds

from .keyframe_manager import KeyframeManager


class HotkeyManager:

    NAME_CMD = "JUN_animTool_holdSelectedKeys"
    KEY = "a"   # 소문자 + shiftModifier=True

    def __init__(self):
        self._installed = False
        self._prev_press = None
        self._prev_release = None

    # --------------------------------------------------
    # install / restore
    # --------------------------------------------------

    def install(self):
        """
        현재 Shift+A 바인딩(press/release)을 저장하고 hold 명령으로 교체.
        반환: (성공여부, 메시지)
        """
        if self._installed:
            return (False, "Shift+A hotkey already active.")

        try:
            # 기존 바인딩 저장 (press + release)
            self._prev_press = cmds.hotkey(
                self.KEY, q=True, shiftModifier=True, name=True
            )
            self._prev_release = cmds.hotkey(
                self.KEY, q=True, shiftModifier=True, releaseName=True
            )

            # 리로드 등으로 우리 바인딩이 남아 있으면 자기참조 복원 방지
            if self._prev_press == self.NAME_CMD:
                self._prev_press = ""
            if self._prev_release == self.NAME_CMD:
                self._prev_release = ""

            # nameCommand 는 핫키 실행 시 MEL 로 돌기 때문에, python 코드를
            # MEL 의 python("...") 으로 감싼다 (sourceType="python" 직접 지정은
            # 핫키 트리거 시 MEL 로 실행돼 "Cannot find procedure import" 에러가 남).
            cmds.nameCommand(
                self.NAME_CMD,
                annotation="JUN AnimTool: hold selected keys",
                sourceType="mel",
                command=(
                    'python("import tools.A00110_animTool.app.core.hotkey_manager '
                    'as _h; _h.HotkeyManager.run_hold()")'
                ),
            )

            cmds.hotkey(keyShortcut=self.KEY, shiftModifier=True, name=self.NAME_CMD)

            self._installed = True

            cur = cmds.hotkeySet(q=True, current=True)
            return (True, f"Shift+A bound to Hold Selected Range.  (set: {cur})")

        except RuntimeError:
            # 활성 세트가 잠긴 경우 -> 경고만, 전역 상태 변경 없음
            return (
                False,
                "Shift+A not bound: active hotkey set is locked. "
                "Switch to a custom hotkey set to enable it. (Hold button still works.)",
            )

    def restore(self):
        """저장해 둔 Shift+A 바인딩을 그대로 복원 (없었으면 빈 값으로 해제)."""
        if not self._installed:
            return

        try:
            cmds.hotkey(
                keyShortcut=self.KEY,
                shiftModifier=True,
                name=(self._prev_press or ""),
                releaseName=(self._prev_release or ""),
            )
        except RuntimeError:
            pass
        finally:
            self._installed = False
            self._prev_press = None
            self._prev_release = None

    # --------------------------------------------------
    # 핫키가 호출하는 진입점
    # --------------------------------------------------

    @staticmethod
    def run_hold():
        """nameCommand 가 호출. hold 실행 후 결과를 뷰포트 메시지로 표시."""
        count, msg = KeyframeManager.hold_selected_keys()
        cmds.inViewMessage(amg=msg, pos="topCenter", fade=True)
        return count
