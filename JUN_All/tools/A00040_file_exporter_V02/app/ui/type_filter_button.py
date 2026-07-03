# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-03
# A00040_file_exporter_V02 - 타입 필터 드롭다운 위젯
#
# 체크 가능한 항목을 담은 드롭다운(QToolButton + QMenu). 등록된 타입만 체크박스로 노출되고,
# 체크 해제된 타입의 key 목록(excluded_keys)을 반환한다. 항목은 core.FILTER_TYPES 에서 온다.

from Framework.qt.qt import *


class TypeFilterButton(QToolButton):
    """'Include Types ▾' 드롭다운. 체크된 타입은 포함, 해제된 타입은 제외한다.

    filter_types: [{"key": "mesh", "label": "Mesh"}, ...] (core.FILTER_TYPES)
    등록되지 않은 타입은 항상 포함되므로 이 목록에 없다.
    """

    def __init__(self, filter_types, parent=None):
        super(TypeFilterButton, self).__init__(parent)

        self.setText("Include Types")
        self.setPopupMode(QToolButton.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setToolTip(
            "Choose which node types to include in the export.\n"
            "Unchecked types are excluded; types not listed here are always included.")

        self._menu = QMenu(self)
        self._actions = {}  # key -> QAction (checkable)

        for spec in filter_types:
            action = self._menu.addAction(spec["label"])
            action.setCheckable(True)
            action.setChecked(True)  # 기본: 모두 포함
            self._actions[spec["key"]] = action

        self.setMenu(self._menu)

    def excluded_keys(self):
        """체크 해제된(=제외할) 타입 key 목록."""
        return [key for key, action in self._actions.items()
                if not action.isChecked()]

    def included_keys(self):
        """체크된(=포함할) 타입 key 목록."""
        return [key for key, action in self._actions.items()
                if action.isChecked()]
