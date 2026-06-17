# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - standalone launch entry point
#
# Maya 없이 Windows 에서 독립 실행되는 PySide 앱.
#   python launch.py        (개발 실행)
#   build_exe.bat           (PyInstaller exe 빌드)

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

# 스크립트 디렉터리(이 툴 폴더)도 path 에 추가 → `import app...` 가능.
TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
if TOOL_ROOT not in sys.path:
    sys.path.append(TOOL_ROOT)


from Framework.qt.qt import QApplication

from app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


def main():

    app = QApplication(sys.argv)

    ThemeManager.load_theme_dev(app, "blue_dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
