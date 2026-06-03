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


# from Framework.qt.qt import QApplication 
from Framework.qt.qt import * 

from .app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


window_instance = None


def run():

    global window_instance


    try:
        window_instance.close()
        window_instance.deleteLater()
    except:
        pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget( window_instance, "red")

    window_instance.show()

    return window_instance