# -*- coding: utf-8 -*-
# CollapsibleBox - MEL frameLayout -collapsable 의 PySide 대응 위젯.
# 헤더(QToolButton)를 누르면 내용(content) 영역이 접히고 펴진다.
# PySide2/PySide6 양립을 위해 Framework.qt.qt 의 와일드카드 import 만 사용한다.

from Framework.qt.qt import *


class CollapsibleBox(QWidget):

    def __init__(self, title="", collapsed=False, parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self._toggle = QToolButton()
        self._toggle.setText(title)
        self._toggle.setCheckable(True)
        self._toggle.setChecked(not collapsed)
        self._toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._toggle.setArrowType(Qt.DownArrow if not collapsed else Qt.RightArrow)
        self._toggle.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; text-align: left; }"
        )
        self._toggle.toggled.connect(self._on_toggled)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 4, 4, 6)
        self._content_layout.setSpacing(5)
        self._content.setVisible(not collapsed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)
        outer.addWidget(self._toggle)
        outer.addWidget(self._content)

    # ----------------------------------------------------------
    # public API
    # ----------------------------------------------------------

    def addWidget(self, widget):
        self._content_layout.addWidget(widget)

    def addLayout(self, layout):
        self._content_layout.addLayout(layout)

    def content_layout(self):
        return self._content_layout

    # ----------------------------------------------------------
    # slot
    # ----------------------------------------------------------

    def _on_toggled(self, checked):
        self._content.setVisible(checked)
        self._toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
