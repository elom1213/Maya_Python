# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# Framework.qt.maya_window - 마야 메인 윈도우를 QWidget 으로 반환하는 공용 헬퍼.
#
# 툴 창을 마야 메인 윈도우에 parent(소유)시키면, 마야 뷰포트 위에는 계속 떠 있으면서도
# 다른 툴 창들과는 정상 Z-order 로 동작한다(밑의 창을 클릭하면 그 창이 위로 올라온다).
# 이는 모든 창을 영구히 최상단에 고정하는 Qt.WindowStaysOnTopHint 의 대체 방식이다.
#
# 주의: maya / shiboken import 는 함수 내부에서 lazy 로 한다(standalone Qt 툴이 모듈
#       import 만으로 깨지지 않도록). PySide2(~2024) / PySide6(2025+) 양쪽 지원.

from Framework.qt.qt import QWidget


def maya_main_window():
    """마야 메인 윈도우를 QWidget 으로 반환. 마야 밖(standalone)이거나 실패 시 None."""
    try:
        import maya.OpenMayaUI as omui
    except ImportError:
        return None

    try:
        from shiboken6 import wrapInstance
    except ImportError:
        try:
            from shiboken2 import wrapInstance
        except ImportError:
            return None

    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QWidget) if ptr else None
