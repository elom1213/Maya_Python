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


from PySide2.QtWidgets import QApplication

from .app.ui.main_window import MainWindow


window_instance = None


def run():

    global window_instance

    try:
        window_instance.close()
        window_instance.deleteLater()

    except:
        pass

    window_instance = MainWindow()

    window_instance.show()

    return window_instance