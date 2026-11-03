# -*- coding: utf-8 -*-
# launch.py - Release Builder 진입점
#
# 두 가지로 뜬다.
#   1) 터미널 / Run_ReleaseBuilder.bat  : 이 프로세스가 QApplication 을 만든다 (standalone)
#   2) 마야 셸프 버튼(__dragDrop_A00510) : 마야의 QApplication 이 이미 있다
#
# ★ v01.04 - 2) 에서 **마야 UI 전체가 이 툴의 테마로 바뀌던 문제**를 고쳤다.
#   예전엔 두 경우 모두 `ThemeManager.load_theme_dev(app, ...)` 로 qss 를 **QApplication** 에
#   입혔는데, 마야 안에서 app 은 마야 자신이라 마야의 모든 위젯이 dark.qss 를 받았다.
#   또 모듈 import 시점에 AppUserModelID 를 지정해 **마야 프로세스의 작업 표시줄 ID** 까지 바꿨다.
#   이제 앱 전역에 손대는 것(qss · 앱 아이콘 · AUMID)은 **이 프로세스가 앱을 만들 때만** 하고,
#   마야 안에서는 qss 를 **이 창에만** 입힌다(load_theme_to_widget).

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

# 툴마다 고유한 패키지 경로(dev.A00510_release_builder.app...)로 import 한다.
# 모든 standalone Qt 툴이 똑같이 최상위 `app` 으로 import 하면 한 인터프리터
# (예: Maya·공용 런처)에서 두 툴을 동시에 띄울 때 sys.modules['app'] 가 충돌한다.
from dev.A00510_release_builder.app.config import app_meta

from Framework.qt.qt import QApplication
from dev.A00510_release_builder.app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


# Maya 등에서 윈도우가 GC 되지 않도록 모듈 레벨 참조 유지
_window = None


def run():

    global _window

    # run() 호출 전에 이미 인스턴스가 있으면 = 외부 이벤트 루프(Maya 등)
    existing = QApplication.instance()

    if existing is None:
        # ★ AppUserModelID 는 QApplication 보다 **먼저** 지정해야 작업 표시줄이 이 툴을
        #   파이썬이 아닌 자기 자신으로 본다(docs/taskbar_icon_guide.md). 내 프로세스일 때만.
        app_meta.set_app_user_model_id()
        app = QApplication(sys.argv)

        # 앱 전역 qss · 앱 아이콘(작업 표시줄) - 이 프로세스의 앱이므로 괜찮다.
        ThemeManager.load_theme_dev(app, "dark")
        icon = app_meta.window_icon()
        if icon is not None:
            app.setWindowIcon(icon)
    else:
        app = existing

        # 마야에서 다시 누르면 이전 창을 닫고 새로 띄운다(창이 겹쳐 쌓이지 않게).
        if _window is not None:
            try:
                _window.close()
                _window.deleteLater()
            except RuntimeError:                            # 이미 지워진 C++ 객체
                pass
            _window = None

    win = MainWindow()

    if existing is not None:
        # 마야 안: qss 를 **이 창에만** 입힌다. 앱(=마야)의 스타일은 건드리지 않는다.
        ThemeManager.load_theme_to_widget(win, "dark")

    win.show()
    _window = win

    # 외부 이벤트 루프가 이미 도는 환경에서는 윈도우 참조만 반환
    if existing is not None:
        return win

    # standalone 실행: 자체 이벤트 루프 진입 (PySide6 = exec, PySide2 = exec_)
    (getattr(app, "exec", None) or app.exec_)()
    return win


if __name__ == "__main__":
    run()
