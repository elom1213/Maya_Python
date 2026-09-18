# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00480_FileTool - Export 규칙 드롭다운 (v01.03)
#
# core.EXPORT_RULES 를 읽어 규칙마다 체크 항목을 만든다. 규칙이 늘어도 이 파일은 그대로다.
# Type Filter 와 같은 드롭다운 모양이라 규칙이 몇 개가 되든 창 크기가 변하지 않는다.
# 버튼 글자에 켜 둔 수를 보여 준다 - "Rules (1/3)".

from Framework.qt.qt import *


class RulesButton(QToolButton):
    """'Rules (n/m) ▾' 드롭다운. 체크된 규칙의 key 목록을 checked_keys() 로 돌려준다."""

    def __init__(self, rules, parent=None):
        super(RulesButton, self).__init__(parent)

        self.setPopupMode(QToolButton.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setToolTip(
            "Checks that run before exporting. If any checked rule finds a problem,\n"
            "nothing is exported - not even the sets that passed.\n"
            "Hover an item to see what it checks.")

        self._menu = QMenu(self)
        self._menu.setToolTipsVisible(True)
        self._actions = {}  # key -> QAction (checkable)
        self._labels = {}

        for rule in rules:
            action = self._menu.addAction(rule.label)
            action.setCheckable(True)
            action.setChecked(bool(rule.default))
            action.setToolTip(rule.tooltip)
            action.toggled.connect(self._update_text)
            self._actions[rule.key] = action
            self._labels[rule.key] = rule.label

        self.setMenu(self._menu)
        self._update_text()

    def _update_text(self, *_args):
        self.setText("Rules ({0}/{1})".format(len(self.checked_keys()), len(self._actions)))

    def checked_keys(self):
        """체크된 규칙 key (등록 순서)."""
        return [key for key, action in self._actions.items() if action.isChecked()]

    def checked_labels(self):
        return [self._labels[key] for key in self.checked_keys()]

    def set_checked(self, key, checked):
        if key in self._actions:
            self._actions[key].setChecked(bool(checked))
