try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *

    QT_VERSION = 6

except ImportError:

    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *

    QT_VERSION = 2