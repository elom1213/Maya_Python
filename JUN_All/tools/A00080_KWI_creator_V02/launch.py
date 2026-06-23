import sys, os

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if ROOT not in sys.path:
    sys.path.append(ROOT)


from Framework.qt.qt import QApplication

# 툴 고유 패키지 경로로 import (내부 모듈도 동일). 최상위 `app` 으로 import 하면
# 한 인터프리터에서 다른 standalone 툴과 sys.modules['app'] 가 충돌한다.
from tools.A00080_KWI_creator_V02.app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


def main():

    app = QApplication(sys.argv)

    ThemeManager.load_theme_dev(app, "purple_dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()