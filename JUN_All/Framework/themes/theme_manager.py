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

        with open(qss_path, "r", encoding="utf-8") as f:

            app.setStyleSheet(f.read())

    @staticmethod
    def load_theme_to_widget(widget, theme_name="dark"):

        root = ThemeManager.get_root()

        qss_path = os.path.join(
            root,
            "styles",
            f"{theme_name}.qss"
        )

        with open(qss_path,"r",encoding="utf-8") as f:
            widget.setStyleSheet(f.read())

    @staticmethod
    def load_theme(app, theme_name):

        theme_path = resource_path(
            f"Framework/styles/{theme_name}.qss"
        )

        with open(theme_path, "r", encoding="utf-8") as f:

            app.setStyleSheet(f.read())

