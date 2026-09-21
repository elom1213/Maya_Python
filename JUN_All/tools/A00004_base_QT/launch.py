import sys, os

# dev 트리와 릴리즈본은 배치가 다르다 - 경로는 "있는 것"을 보고 정한다.
#   dev 트리 : Framework 가 JUN_All 에 있고 모든 툴이 공유한다
#   릴리즈본 : Framework 는 툴 폴더 안에 동봉된다
# 자세한 것은 docs/Release_Layout.md
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


from Framework.qt.qt import QApplication

from tools.A00004_base_QT.app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


def main():

    app = QApplication(sys.argv)

    ThemeManager.load_theme(app, "dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()