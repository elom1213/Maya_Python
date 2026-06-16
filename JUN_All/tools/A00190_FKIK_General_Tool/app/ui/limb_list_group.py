# -*- coding: utf-8 -*-
"""
limb_list_group - 제목 박스 안에 여러 개의 재사용 tsl 위젯을 가로로 배치하는 컴포지트.

레거시의 수작업 반복 tsl 블록(+CMD_ToolSel_b_add/del/up/down 콜백)을
Framework.qt.JUN_mod_tsl_qt 위젯으로 대체한다.
각 tsl 은 (slot_id, label) 스펙으로 만들어지고, slot_id 로 조회/세팅한다.
"""

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt


class TslListGroup(QGroupBox):
    """title 박스 안에 specs=[(slot_id, label), ...] 만큼 tsl 을 가로 배치."""

    def __init__(self, title, specs, log_callback=None, list_min_height=110, parent=None):
        super(TslListGroup, self).__init__(title, parent)

        self.widgets = {}   # slot_id -> JUN_mod_tsl_qt_v01

        row = QHBoxLayout(self)
        row.setContentsMargins(4, 4, 4, 4)

        for slot_id, label in specs:
            tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
                title=label,
                show_sort=False,
                list_min_height=list_min_height,
                log_callback=log_callback,
            )
            self.widgets[slot_id] = tsl
            row.addWidget(tsl)

    # ------------------------------------------------------------------

    def get(self, slot_id):
        return self.widgets[slot_id].get_all_items()

    def set(self, slot_id, items):
        self.widgets[slot_id].set_items(items)

    def all_widgets(self):
        """slot_id -> 위젯 dict (MainWindow 가 전체 집계용으로 사용)."""
        return self.widgets
