# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - standalone launch entry point
#
# Maya 없이 Windows 에서 독립 실행되는 PySide 앱. 마야 일(클립 생성 · 점검)은 mayapy 워커(app/maya/worker.py)로.
#   python launch.py        (개발 실행)
#   build_exe.bat           (PyInstaller exe 빌드)

import sys, os

# dev 트리와 릴리즈본은 배치가 다르다 - 경로는 "있는 것"을 보고 정한다 (docs/Release_Layout.md).
#   dev 트리 : Framework 가 JUN_All 에 있고 모든 툴이 공유한다
#   릴리즈본 : Framework 는 툴 폴더 안에 동봉된다
TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))

# tools 패키지를 담은 폴더 (dev: JUN_All, 릴리즈: 저장소 루트)
ROOT = os.path.abspath(
    os.path.join(
        TOOL_ROOT,
        "..",
        ".."
    )
)

# 툴 폴더 안에 Framework 가 동봉돼 있으면 릴리즈본이다.
IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))

# Framework 가 실제로 있는 곳과 tools 패키지 루트를 둘 다 sys.path 에 올린다.
for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)

# 툴마다 고유한 패키지 경로(tools.<tool>.app...)로 import 한다 (메모리 standalone-app-package-collision).
from Framework.qt.qt import QApplication, QIcon

from tools.A00560_JaliBatch.app.ui.main_window import MainWindow
from tools.A00560_JaliBatch.app.config.app_meta import APP_USER_MODEL_ID, icon_path
from Framework.themes.theme_manager import ThemeManager

THEME = "teal_dark"


def _set_windows_app_id():
    """Windows 작업표시줄이 python.exe 아이콘 대신 이 앱의 아이콘을 쓰도록 AppUserModelID 지정 (QApplication 전에)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def main():
    _set_windows_app_id()
    app = QApplication(sys.argv)
    sIcon = icon_path()
    if sIcon:
        app.setWindowIcon(QIcon(sIcon))
    ThemeManager.load_theme_dev(app, THEME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
