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
# v02.20 - **뷰포트의 Tab 은 핫키로 못 잡는다.** Modeling Toolkit(modelingToolkit.mll)이 Maya 툴
#   (선택 · Move · Rotate · Scale)에서 Tab 을 먼저 가로채 자기 옵션 `nexOpt mayaTabPressCmd` /
#   `mayaTabReleaseCmd`(기본 `dR_paintPress` / `dR_paintRelease` = 페인트 선택)를 실행한다.
#   v02.19 의 `hotkey -keyShortcut Tab` 은 그래서 한 번도 불리지 않았다(스크립트 에디터에 dR_paint* 만 찍힘).
#   -> manip_space() 는 TabKeyManager : 그 두 nexOpt 명령을 툴 명령으로 바꿔 끼우고 닫을 때 되돌린다.
#      MTK 가 없으면(플러그인 미로드) 가로채는 쪽도 없으므로 예전처럼 핫키로 건다.
#   nexOpt -e 는 메모리 값만 바꾼다(-save 해야 저장) - 마야가 죽어도 다음 세션은 원래 Tab 이다.
#
# 주의:
#  - keyShortcut 은 소문자 'a' + shiftModifier=True 로 지정한다 (.mhk 의 "s" -sht 관례).
#  - 현재 핫키 세트만(메모리) 수정하며 .mhk 원본 파일은 건드리지 않는다.
#  - 활성 세트가 잠긴 경우(예: Maya Default)에는 경고만 하고 전역 상태를 바꾸지 않는다.

import time

import maya.cmds as cmds
import maya.mel as mel

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
        """Tab -> 매니퓰레이터 공간 Object <-> World (Modeling Toolkit 의 Tab 명령 경유)."""
        return TabKeyManager()

    @classmethod
    def manip_space_hotkey(cls):
        """Tab 핫키판 - MTK 가 없어 Tab 을 아무도 가로채지 않을 때 TabKeyManager 가 쓴다."""
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

    # Tab 을 누르고 있으면 키 자동 반복으로 press 가 계속 들어온다 -> 한 번 누름에 한 번만 토글.
    # release 가 오면 풀리고, release 를 놓쳐도 press 가 이만큼 끊기면 새 누름으로 본다.
    _tab_held = False
    _tab_last = 0.0
    TAB_REPEAT_GAP = 0.6

    @staticmethod
    def run_tab_press():
        """MTK 의 mayaTabPressCmd 가 호출."""
        now = time.time()
        cls = HotkeyManager
        if cls._tab_held and now - cls._tab_last < cls.TAB_REPEAT_GAP:
            cls._tab_last = now
            return None
        cls._tab_held = True
        cls._tab_last = now
        return cls.run_toggle_space()

    @staticmethod
    def run_tab_release():
        """MTK 의 mayaTabReleaseCmd 가 호출."""
        HotkeyManager._tab_held = False


def _mel_quote(text):
    """MEL 문자열 리터럴로 감싼다."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class TabKeyManager:
    """뷰포트 Tab -> 매니퓰레이터 공간 토글. HotkeyManager 와 같은 install / restore 인터페이스.

    Modeling Toolkit 이 Maya 툴의 Tab 을 가로채 실행하는 nexOpt 옵션 넷을 바꿔 끼운다:
        useMayaTabPressCmd   (int)    1 로
        mayaTabPressCmd      (string) run_tab_press 로
        useMayaTabReleaseCmd (int)    1 로
        mayaTabReleaseCmd    (string) run_tab_release 로   (기본 dR_paintRelease 가 페인트 선택을 끄던 자리)
    걸기 전 값을 저장했다가 restore 에서 그대로 되돌린다.
    """

    PRESS_CMD = _PY_CALL.format("run_tab_press")
    RELEASE_CMD = _PY_CALL.format("run_tab_release")
    # 이전 세션이 되돌리지 못하고 남긴 값이면 이걸로 되돌린다 (MTK 기본값)
    DEFAULTS = {
        "useMayaTabPressCmd": 1, "mayaTabPressCmd": "dR_paintPress",
        "useMayaTabReleaseCmd": 1, "mayaTabReleaseCmd": "dR_paintRelease",
    }

    label = "Tab"

    def __init__(self):
        self._prev = None
        # MTK 가 없을 때 쓰는 핫키판
        self._fallback = None

    def is_installed(self):
        return self._prev is not None or (
            self._fallback is not None and self._fallback.is_installed())

    @staticmethod
    def _mtk_available():
        try:
            if not cmds.pluginInfo("modelingToolkit", q=True, loaded=True):
                return False
            return bool(mel.eval('exists "nexOpt"'))
        except RuntimeError:
            return False

    @staticmethod
    def _query(name):
        return mel.eval("nexOpt -q {0}".format(name))

    @staticmethod
    def _edit(name, value):
        if isinstance(value, str):
            value = _mel_quote(value)
        mel.eval("nexOpt -e {0} {1}".format(name, value))

    def install(self):
        if self.is_installed():
            return (False, "Tab hotkey already active.")

        if not self._mtk_available():
            # Tab 을 가로챌 MTK 가 없다 -> 일반 핫키로 충분하다
            self._fallback = HotkeyManager.manip_space_hotkey()
            ok, msg = self._fallback.install()
            if not ok:
                self._fallback = None
            return (ok, msg + "  (Modeling Toolkit not loaded - hotkey binding)")

        try:
            prev = {name: self._query(name) for name in self.DEFAULTS}
        except RuntimeError as exc:
            return (False, "Tab not bound: cannot read the Modeling Toolkit Tab option "
                           "({0}). (Toggle button still works.)".format(exc))

        # 리로드 · 크래시로 우리 명령이 남아 있으면 자기참조 복원 방지
        for name in ("mayaTabPressCmd", "mayaTabReleaseCmd"):
            if "A00110_animTool_V02" in str(prev[name]):
                prev[name] = self.DEFAULTS[name]
                prev["use" + name[0].upper() + name[1:]] = 1

        self._prev = prev
        try:
            self._edit("useMayaTabPressCmd", 1)
            self._edit("mayaTabPressCmd", self.PRESS_CMD)
            self._edit("useMayaTabReleaseCmd", 1)
            self._edit("mayaTabReleaseCmd", self.RELEASE_CMD)
        except RuntimeError as exc:
            self.restore()
            return (False, "Tab not bound: Modeling Toolkit Tab option failed ({0}). "
                           "(Toggle button still works.)".format(exc))

        HotkeyManager._tab_held = False
        return (True, "Tab bound to Toggle Manipulator Space  (Modeling Toolkit Tab "
                      "command; was '{0}').".format(prev["mayaTabPressCmd"]))

    def restore(self):
        if self._fallback is not None:
            self._fallback.restore()
            self._fallback = None
        if self._prev is None:
            return
        prev, self._prev = self._prev, None
        for name, value in prev.items():
            try:
                self._edit(name, value)
            except RuntimeError:
                pass
