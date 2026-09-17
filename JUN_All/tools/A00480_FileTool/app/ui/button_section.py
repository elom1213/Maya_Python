# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - 버튼 섹션 빌더 (Import · Path 탭 공용)
#
# A00030_quickTool_V02 의 `SECTIONS` 표 방식을 그대로 쓴다.
#   (섹션 제목, [(라벨, 핸들러 이름, 툴팁), ...])
# 버튼을 더하는 일은 탭의 표에 한 줄이다. 버튼은 **두 칸 그리드**, 하나뿐이면 가로를 다 쓴다.

from Framework.qt.qt import (
    QGroupBox,
    QGridLayout,
    QPushButton,
)


def build_button_section(owner, title, specs, buttons=None):
    """QGroupBox 하나를 만들어 돌려준다.

    owner   : 핸들러 이름을 `getattr(owner, name)` 으로 찾을 객체(탭).
    buttons : dict 를 주면 라벨 -> QPushButton 을 기록한다(테스트 · 외부 접근용).
    """
    box = QGroupBox(title)
    grid = QGridLayout(box)

    for index, (label, handler, tip) in enumerate(specs):
        button = QPushButton(label)
        button.setToolTip(tip)
        button.clicked.connect(getattr(owner, handler))
        if buttons is not None:
            buttons[label] = button

        row, column = divmod(index, 2)
        if len(specs) == 1:
            grid.addWidget(button, row, 0, 1, 2)
        else:
            grid.addWidget(button, row, column)

    return box
