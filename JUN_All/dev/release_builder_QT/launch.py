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

# 툴마다 고유한 패키지 경로(dev.release_builder_QT.app...)로 import 한다.
# 모든 standalone Qt 툴이 똑같이 최상위 `app` 으로 import 하면 한 인터프리터
# (예: Maya·공용 런처)에서 두 툴을 동시에 띄울 때 sys.modules['app'] 가 충돌한다.
from Framework.qt.qt import QApplication
from dev.release_builder_QT.app.ui.main_window import MainWindow
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
