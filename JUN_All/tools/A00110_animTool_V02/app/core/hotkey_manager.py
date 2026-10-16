# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-16
# A00110_animTool_V02 - 툴 전용 핫키 라이프사이클 (maya.cmds, UI 비의존)
#
# 툴이 열려 있는 동안 키 하나를 툴 명령에 바인딩하고,
# 닫힐 때 원래 바인딩을 그대로 복원한다.
#
# v02.19 - 키 하나(Shift+A)만 다루던 클래스를 **키마다 인스턴스 하나**로 일반화했다.
#   HotkeyManager.hold()        : Shift+A -> Hold Selected Range (예전 HotkeyManager())
#   HotkeyManager.manip_space() : Tab     -> 매니퓰레이터 공간 Object <-> World
#
# 주의:
#  - keyShortcut 은 소문자 'a' + shiftModifier=True 로 지정한다 (.mhk 의 "s" -sht 관례).
#  - 현재 핫키 세트만(메모리) 수정하며 .mhk 원본 파일은 건드리지 않는다.
#  - 활성 세트가 잠긴 경우(예: Maya Default)에는 경고만 하고 전역 상태를 바꾸지 않는다.

import maya.cmds as cmds

from .keyframe_manager import KeyframeManager
from .manip_space_manager import ManipSpaceManager


# nameCommand 는 핫키 실행 시 MEL 로 돌기 때문에, python 코드를 MEL 의 python("...") 으로
# 감싼다 (sourceType="python" 직접 지정은 핫키 트리거 시 MEL 로 실행돼
# "Cannot find procedure import" 에러가 남).
_PY_CALL = ('python("import tools.A00110_animTool_V02.app.core.hotkey_manager '
            'as _h; _h.HotkeyManager.{0}()")')


class HotkeyManager:

    # 예전 이름 유지 (Shift+A Hold)
    NAME_CMD = "JUN_animTool_holdSelectedKeys"
    KEY = "a"   # 소문자 + shiftModifier=True

    def __init__(self, key=KEY, shift=True, name_cmd=NAME_CMD, runner="run_hold",
                 annotation="JUN AnimTool: hold selected keys", label="Shift+A",
                 action="Hold Selected Range", fallback="Hold button"):
        self.key = key
        self.shift = shift
        self.name_cmd = name_cmd
        self.runner = runner
        self.annotation = annotation
        # 로그 · 상태 라벨에 쓰는 키 이름
        self.label = label
        self.action = action
        # 핫키를 못 걸었을 때 대신 쓸 버튼 (메시지용)
        self.fallback = fallback

        self._installed = False
        self._prev_press = None
        self._prev_release = None

    @classmethod
    def hold(cls):
        """Shift+A -> Hold Selected Range."""
        return cls()

    @classmethod
    def manip_space(cls):
        """Tab -> 매니퓰레이터 공간 Object <-> World."""
        return cls(key="Tab", shift=False, name_cmd="JUN_animTool_toggleManipSpace",
                   runner="run_toggle_space",
                   annotation="JUN AnimTool: toggle manipulator space Object / World",
                   label="Tab", action="Toggle Manipulator Space",
                   fallback="Toggle button")

    def is_installed(self):
        return self._installed

    # --------------------------------------------------
    # install / restore
    # --------------------------------------------------

    def install(self):
        """
        현재 키 바인딩(press/release)을 저장하고 툴 명령으로 교체.
        반환: (성공여부, 메시지)
        """
        if self._installed:
            return (False, f"{self.label} hotkey already active.")

        try:
            # 기존 바인딩 저장 (press + release)
            self._prev_press = cmds.hotkey(
                self.key, q=True, shiftModifier=self.shift, name=True
            )
            self._prev_release = cmds.hotkey(
                self.key, q=True, shiftModifier=self.shift, releaseName=True
            )

            # 리로드 등으로 우리 바인딩이 남아 있으면 자기참조 복원 방지
            if self._prev_press == self.name_cmd:
                self._prev_press = ""
            if self._prev_release == self.name_cmd:
                self._prev_release = ""

            cmds.nameCommand(
                self.name_cmd,
                annotation=self.annotation,
                sourceType="mel",
                command=_PY_CALL.format(self.runner),
            )

            cmds.hotkey(keyShortcut=self.key, shiftModifier=self.shift,
                        name=self.name_cmd)

            self._installed = True

            cur = cmds.hotkeySet(q=True, current=True)
            return (True, f"{self.label} bound to {self.action}.  (set: {cur})")

        except RuntimeError:
            # 활성 세트가 잠긴 경우 -> 경고만, 전역 상태 변경 없음
            return (
                False,
                f"{self.label} not bound: active hotkey set is locked. "
                f"Switch to a custom hotkey set to enable it. "
                f"({self.fallback} still works.)",
            )

    def restore(self):
        """저장해 둔 바인딩을 그대로 복원 (없었으면 빈 값으로 해제)."""
        if not self._installed:
            return

        try:
            cmds.hotkey(
                keyShortcut=self.key,
                shiftModifier=self.shift,
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

    @staticmethod
    def run_toggle_space():
        """nameCommand 가 호출. 공간을 토글하고 결과를 뷰포트 메시지로 표시."""
        space, msg = ManipSpaceManager.toggle()
        cmds.inViewMessage(amg=msg, pos="topCenter", fade=True)
        return space
