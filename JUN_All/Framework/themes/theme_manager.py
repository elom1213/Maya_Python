import os
import sys

from Framework.qt.qt import QApplication


def resource_path(relative_path):

    if hasattr(sys, "_MEIPASS"):

        base_path = sys._MEIPASS

    else:

        base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

    return os.path.join(
        base_path,
        relative_path
    )


def _read_qss(qss_path):
    """qss 파일을 읽고, `@STYLES@` 토큰을 그 qss 가 있는 폴더의 절대경로로 치환한다.

    qss 의 `url(...)`(예: 스핀박스 화살표 아이콘)은 기본적으로 실행 작업 디렉터리
    기준으로 해석돼 깨지기 쉽다. `url(@STYLES@/sb_up_light.png)` 처럼 적어 두면 로드
    시점에 절대경로(슬래시)로 바뀌어 어디서 실행하든 아이콘을 찾는다."""
    with open(qss_path, "r", encoding="utf-8") as f:
        text = f.read()
    styles_dir = os.path.dirname(os.path.abspath(qss_path)).replace("\\", "/")
    return text.replace("@STYLES@", styles_dir)


class ThemeManager:

    @staticmethod
    def get_root():

        # PyInstaller exe 환경
        if getattr(sys, 'frozen', False):

            return sys._MEIPASS

        # 일반 python 실행
        return os.path.dirname(
            os.path.dirname(__file__)
        )

    @classmethod
    def load_theme_dev(cls, app, theme_name="dark"):

        root = cls.get_root()

        qss_path = os.path.join(
            root,
            "styles",
            f"{theme_name}.qss"
        )

        app.setStyleSheet(_read_qss(qss_path))

    @staticmethod
    def load_theme_to_widget(widget, theme_name="dark"):

        root = ThemeManager.get_root()

        qss_path = os.path.join(
            root,
            "styles",
            f"{theme_name}.qss"
        )

        widget.setStyleSheet(_read_qss(qss_path))

    @staticmethod
    def load_theme(app, theme_name):

        theme_path = resource_path(
            f"Framework/styles/{theme_name}.qss"
        )

        app.setStyleSheet(_read_qss(theme_path))

