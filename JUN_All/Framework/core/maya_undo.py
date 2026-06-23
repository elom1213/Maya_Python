# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-23
# Framework - Maya undo 청크(chunk) 공용 헬퍼.
#
# cmds.undoInfo(openChunk=True) / closeChunk 로 여러 cmds 호출을 "한 번의 undo
# 스텝"으로 묶는다. 여러 툴(A00110/A00120/A00145/A00150/A00160/A00170/A00180/
# A00190/A00010_V02/A00060_V02/A00200 등)이 같은 open/try/finally/close 패턴을
# 각자 복붙해 왔다 → 이 컨텍스트 매니저 하나로 통일한다.
#
# 핵심: 블록 안에서 예외가 나도 finally 에서 반드시 closeChunk 를 호출해, chunk 가
# 열린 채 남아(이후 undo 가 비정상적으로 묶이는) 누수를 막는다.

import contextlib

import maya.cmds as cmds


@contextlib.contextmanager
def undo_chunk():
    """블록 안의 Maya 작업을 하나의 undo 스텝으로 묶는다.

    사용 예:
        with undo_chunk():
            cmds.bakeResults(...)
            cmds.delete(...)
        # 한 번의 Ctrl+Z 로 위 작업 전체가 되돌려진다.

    예외가 발생해도 finally 에서 closeChunk 를 보장하므로 chunk 누수가 없다.
    """
    cmds.undoInfo(openChunk=True)
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)
