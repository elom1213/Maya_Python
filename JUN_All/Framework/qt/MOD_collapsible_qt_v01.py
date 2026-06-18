# -*- coding: utf-8 -*-
"""
JUN_mod_collapsible_qt_v01 - 재사용 PySide 접이식(collapsible) 프레임 위젯.

Maya `cmds.frameLayout(collapsable=True)` (예: 레거시 JUN_PY_SelectionTool 의
"Tool : Selection" / "Tool : Select By Shape")의 PySide 대응물.
헤더(제목 + 화살표)를 클릭하면 본문이 접히고/펼쳐진다.

함께 제공하는 JUN_mod_fit_tab_page_v01 은 QTabWidget 페이지용 QWidget 으로,
'현재 탭이 아닐 때'(숨김) sizeHint 를 0 으로 보고한다. 이렇게 하면 QStackedLayout 이
모든 페이지의 최댓값이 아니라 '현재 탭'에만 맞춰 sizeHint 를 내므로, 섹션을 접고 펼칠 때
창 전체를 콘텐츠에 맞춰 줄이고 늘릴 수 있다(자세한 사용은 메인 윈도우의 _fit_window 참고).

Maya 밖에서도 import / 생성이 가능하도록 maya 의존이 없다.
"""

from Framework.qt.qt import *


class JUN_mod_collapsible_qt_v01(QWidget):
    """제목 헤더를 클릭하면 본문을 접고/펼치는 위젯.

    expanded=False 로 만들면 처음부터 접힌 상태. 본문에는 body 레이아웃에 직접 추가하거나
    add_widget / add_layout 헬퍼로 위젯·레이아웃을 넣는다. 토글 시 toggled(bool) 시그널을
    방출하므로(인자=펼침 여부), 부모가 받아 창 크기를 다시 맞출 수 있다.
    """

    toggled = Signal(bool)

    def __init__(self, title="", expanded=True, parent=None):
        super(JUN_mod_collapsible_qt_v01, self).__init__(parent)
        self._build_ui(title, expanded)

    def _build_ui(self, title, expanded):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 헤더: 화살표 + 제목. 클릭하면 토글. (frameLayout 의 접기 헤더 대응)
        self.header = QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; text-align: left; padding: 4px; }")
        self.header.clicked.connect(self._on_clicked)
        outer.addWidget(self.header)

        # 본문 컨테이너
        self._content = QWidget()
        self.body = QVBoxLayout(self._content)
        self.body.setContentsMargins(10, 2, 4, 6)
        outer.addWidget(self._content)

        self._content.setVisible(expanded)

    # ================================================================
    # 공개 API
    # ================================================================

    def add_widget(self, widget):
        self.body.addWidget(widget)

    def add_layout(self, layout):
        self.body.addLayout(layout)

    def is_expanded(self):
        return self.header.isChecked()

    def set_expanded(self, expanded):
        if self.header.isChecked() != bool(expanded):
            self.header.setChecked(bool(expanded))
            self._on_clicked()

    # ================================================================
    # 내부
    # ================================================================

    def _on_clicked(self):
        expanded = self.header.isChecked()
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self._content.setVisible(expanded)
        self.toggled.emit(expanded)


class JUN_mod_fit_tab_page_v01(QWidget):
    """QTabWidget 페이지용 QWidget.

    숨겨져 있으면(= 현재 탭이 아니면) sizeHint / minimumSizeHint 를 0 으로 보고한다.
    기본 QStackedLayout 은 모든 페이지 sizeHint 의 최댓값을 쓰므로, 이 위젯을 페이지로
    쓰면 '현재 탭'에만 맞춰 창을 줄이고 늘릴 수 있다.
    """

    def sizeHint(self):
        return super(JUN_mod_fit_tab_page_v01, self).sizeHint() if self.isVisible() else QSize(0, 0)

    def minimumSizeHint(self):
        return super(JUN_mod_fit_tab_page_v01, self).minimumSizeHint() if self.isVisible() else QSize(0, 0)
