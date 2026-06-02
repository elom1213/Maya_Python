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

from app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


def main():

    app = QApplication(sys.argv)

    ThemeManager.load_theme_dev(app, "dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()