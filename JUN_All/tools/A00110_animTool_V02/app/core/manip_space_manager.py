# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-16
# A00110_animTool_V02 - 매니퓰레이터 공간 Object <-> World 토글 (maya.cmds, UI 비의존)
#
# Hot Key > Main 의 `Toggle Manipulator Space` 버튼과 Tab 핫키가 부른다.
#
# 마야 툴 컨텍스트 이름과 mode 값 (마야 커맨드 문서 기준):
#   Move   (manipMoveContext)   : 0 = Object, 2 = World (기본)
#   Rotate (manipRotateContext) : 0 = Object (기본), 1 = World, 2 = Gimbal
#   Scale  (manipScaleContext)  : 0 = Object, 2 = World (기본)
# 이동·스케일과 회전의 World 번호가 다르다(2 / 1) - 번호를 하나로 쓰면 회전이 Gimbal 이 된다.
#
# ★ standalone mayapy 에는 툴 컨텍스트가 없어 실측할 수 없다(query 가 False).
#   값은 문서 기준이고, 실제 동작은 마야 GUI 에서 확인한다.

import maya.cmds as cmds


OBJECT = "Object"
WORLD = "World"

# (컨텍스트 이름, 커맨드 이름, {공간: mode})
_TOOLS = (
    ("Move", "manipMoveContext", {OBJECT: 0, WORLD: 2}),
    ("Rotate", "manipRotateContext", {OBJECT: 0, WORLD: 1}),
    ("Scale", "manipScaleContext", {OBJECT: 0, WORLD: 2}),
)

# currentCtx() 가 돌려주는 툴 이름 -> 위 컨텍스트 이름
_SUPER_CONTEXTS = {
    "moveSuperContext": "Move",
    "RotateSuperContext": "Rotate",
    "scaleSuperContext": "Scale",
}


class ManipSpaceManager:
    """Move / Rotate / Scale 매니퓰레이터의 공간을 Object 와 World 사이에서 오간다.

    기준은 **지금 쓰는 툴**의 공간이다 - World 면 Object 로, 그 밖(Object · Gimbal · Parent ·
    Normal ...)이면 World 로. 결과 공간은 **세 툴 모두에** 맞춘다(툴을 바꿔도 같은 공간).
    """

    @staticmethod
    def _cmd(name):
        return getattr(cmds, name)

    @staticmethod
    def active_tool():
        """지금 툴이 Move / Rotate / Scale 이면 그 이름, 아니면 "Move"."""
        try:
            ctx = cmds.currentCtx() or ""
        except RuntimeError:
            ctx = ""
        return _SUPER_CONTEXTS.get(ctx, "Move")

    @staticmethod
    def current_space(tool=None):
        """tool 의 공간. Object / World 가 아니면 None (Gimbal, Parent 등)."""
        tool = tool or ManipSpaceManager.active_tool()
        for name, cmd, modes in _TOOLS:
            if name != tool:
                continue
            try:
                mode = ManipSpaceManager._cmd(cmd)(name, q=True, mode=True)
            except RuntimeError:
                return None
            for space, value in modes.items():
                if mode == value:
                    return space
        return None

    @staticmethod
    def set_space(space):
        """세 툴의 공간을 space 로. 반환: 바꾼 툴 이름 목록."""
        done = []
        for name, cmd, modes in _TOOLS:
            try:
                ManipSpaceManager._cmd(cmd)(name, e=True, mode=modes[space])
                done.append(name)
            except RuntimeError:
                # 컨텍스트가 아직 없으면(툴을 한 번도 안 열었거나 standalone) 건너뛴다
                pass
        return done

    @staticmethod
    def toggle():
        """Object <-> World 토글. 반환: (새 공간 또는 None, 메시지)."""
        tool = ManipSpaceManager.active_tool()
        current = ManipSpaceManager.current_space(tool)
        target = OBJECT if current == WORLD else WORLD

        done = ManipSpaceManager.set_space(target)
        if not done:
            return (None, "Manipulator space not changed: no Move / Rotate / Scale "
                          "tool context found.")
        return (target, "Manipulator space: {0}  ({1})".format(target, " / ".join(done)))
