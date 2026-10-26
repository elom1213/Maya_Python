# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00490_KeyboardTool - 환경 자가 검사 (Run_KeyboardTool.bat 의 4단계). 종료 코드 0 = 통과. 메시지는 영어.
#
# 1) Python 버전 · 비트  2) PySide6 import  3) Framework · 툴 import (launch.py 와 같은 sys.path 규칙)
# 4) 창을 오프스크린으로 만들어 본다. A00560_JaliBatch 의 selftest 와 같은 모양(mayapy 검사만 없다).

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))              # .../A00490_KeyboardTool/app
TOOL_ROOT = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(TOOL_ROOT, "..", ".."))
IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))
for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)


def main():
    major, minor = sys.version_info[:2]
    bits = 64 if sys.maxsize > 2 ** 32 else 32
    print("[INFO] Python {0}.{1} ({2}-bit) {3}".format(major, minor, bits, sys.executable))
    if (major, minor) < (3, 10) or bits != 64:
        print("[ERROR] 64-bit Python 3.10 or newer is required")
        return 1
    try:
        import PySide6
        from PySide6 import QtWidgets, QtSvg   # noqa: F401
    except Exception as e:  # noqa: BLE001 - DLL load failed 등
        print("[ERROR] PySide6 import failed: {0}".format(e))
        if "DLL load failed" in str(e):
            print("        Install the Microsoft Visual C++ Redistributable (x64): https://aka.ms/vs/17/release/vc_redist.x64.exe")
        return 1
    print("[OK] PySide6 {0}".format(PySide6.__version__))

    try:
        from Framework.qt.qt import QApplication, QT_VERSION
        from Framework.themes.theme_manager import ThemeManager
        from tools.A00490_KeyboardTool.app.ui.main_window import MainWindow
        from tools.A00490_KeyboardTool.app.config.version import VERSION
        from tools.A00490_KeyboardTool.app.core import keys, win32   # noqa: F401 - ctypes user32 바인딩
    except Exception as e:  # noqa: BLE001
        print("[ERROR] tool import failed: {0}".format(e))
        print("        Framework must be at ..\\..\\Framework (dev tree) or inside this folder (release).")
        return 1
    print("[OK] imports (Qt binding PySide{0}, tool v{1})".format(QT_VERSION, VERSION))

    try:
        app = QApplication.instance() or QApplication([])
        ThemeManager.load_theme_dev(app, "teal_dark")
        win = MainWindow()
        win.show()
        app.processEvents()
        ok = win.isVisible() and win.table.columnCount() == 3
        win.close()
    except Exception as e:  # noqa: BLE001
        print("[ERROR] window could not be built: {0}".format(e))
        return 1
    if not ok:
        print("[ERROR] window built but looks wrong")
        return 1
    print("[OK] window builds (offscreen)")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.exit(code)
