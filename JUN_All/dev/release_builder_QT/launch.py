# -*- coding: utf-8 -*-
# launch.py - Release Builder 진입점

import sys
import os

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)  # -> JUN_All

if ROOT not in sys.path:
    sys.path.append(ROOT)

# launch.py 가 있는 디렉터리 ( release_builder_QT ) 를 path 에 추가 -> "app" import 용
TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
if TOOL_ROOT not in sys.path:
    sys.path.append(TOOL_ROOT)

from Framework.qt.qt import QApplication
from app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


# Maya 등에서 윈도우가 GC 되지 않도록 모듈 레벨 참조 유지
_window = None


def run():

    global _window

    # run() 호출 전에 이미 인스턴스가 있으면 = 외부 이벤트 루프(Maya 등)
    existing = QApplication.instance()
    app = existing or QApplication(sys.argv)

    ThemeManager.load_theme_dev(app, "dark")

    win = MainWindow()
    win.show()
    _window = win

    # 외부 이벤트 루프가 이미 도는 환경에서는 윈도우 참조만 반환
    if existing is not None:
        return win

    # standalone 실행: 자체 이벤트 루프 진입
    app.exec()
    return win


if __name__ == "__main__":
    run()
