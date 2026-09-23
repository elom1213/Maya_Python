# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
# A00050_uvTool_V02 - UV Sets 표 (v02.02)
#
# 오브젝트마다 **UV 세트 이름들**과 **규칙에 맞는지**를 세 칸으로 보여 준다.
# 형식은 A00330_NamingTool 의 Quick Rename > Insert Preview 와 같다 -
# 줄 선택 없음 · 줄무늬 · 판정 칸만 색(초록 = 맞음, 빨강 = 어긋남) · 사유는 툴팁.
#
# ★ A00380_MeshTool 로 옮길 예정이다. 그래서 이 파일은 **Framework 와 Qt 에만** 기대고
#   툴 코드(창 · 코어)를 import 하지 않는다. 행 데이터는 코어 `uv_set_manager.inspect()`
#   가 만든 dict 목록을 그대로 받는다 - 두 파일을 함께 옮기면 된다.

from Framework.qt.qt import (
    QAbstractItemView,
    QBrush,
    QColor,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from Framework.core import log_levels


#: 판정 칸에 쓰는 글. 상태 코드는 코어(uv_set_manager)의 것과 같은 문자열이다.
STATUS_OK = "ok"
STATUS_TEXT = {STATUS_OK: "OK"}

#: 로그에서 빨간색으로 칠할 상태(요청: `[wrong_name]`).
RED_LOG_STATUSES = ("wrong_name",)


def _is_dark():
    """지금 테마가 어두운가. 테마 모듈을 못 읽으면 저장소 기본(어두움)."""
    try:
        from Framework.themes.theme_manager import ThemeManager
        return bool(ThemeManager.is_dark_theme())
    except Exception:                                       # noqa: BLE001
        return True


def colored_log_line(line, status):
    """RED_LOG_STATUSES 의 상태면 **빨간 HTML 한 줄**, 아니면 None.

    공용 로그창은 `<` 가 든 줄을 툴이 쓴 HTML 로 보고 **그대로** 받는다
    (`JUN_mod_log_qt_v01.append`). 색은 공용 규칙의 `[ERROR]` 빨강 - 밝은 테마에서도 읽힌다.
    `[wrong_name]` 은 밑줄이 있어 공용 표식 규칙(글자만)에는 걸리지 않으므로 여기서 칠한다.
    """
    if status not in RED_LOG_STATUSES:
        return None
    return '<span style="color:{0}; white-space: pre-wrap;">{1}</span>'.format(
        log_levels.color("ERROR", _is_dark()), log_levels.escape(line))


class UvSetTable(QWidget):
    """제목 + 세 칸 표 (Object / UV Sets / Rule).

    `set_rows(rows, wanted)` 로 채운다. rows 는 `uv_set_manager.inspect()` 의 결과.
    """

    COL_OBJECT, COL_SETS, COL_RULE = range(3)

    def __init__(self, title="UV Sets", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.lbl_title = QLabel(title)
        font = self.lbl_title.font()
        font.setBold(True)
        self.lbl_title.setFont(font)
        layout.addWidget(self.lbl_title)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Object", "UV Sets", "Rule"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.tree.setToolTip(
            "UV sets of every listed mesh, and whether it follows the rule.\n"
            "Hover the Rule cell for the reason. Nothing here changes the scene.")
        layout.addWidget(self.tree, 1)

    def set_rows(self, rows, wanted=""):
        """표를 rows 로 다시 채운다. 제목에 맞은 수 / 전체 수를 적는다."""
        dark = _is_dark()
        ok_color = log_levels.color("OK", dark)
        bad_color = log_levels.color("ERROR", dark)

        self.tree.clear()
        passed = 0
        for row in rows or []:
            status = row["status"]
            if status == STATUS_OK:
                passed += 1
            node = row.get("transform") or row.get("node") or ""
            item = QTreeWidgetItem([
                node.split("|")[-1],
                ", ".join(row["sets"]) if row["sets"] else "-",
                STATUS_TEXT.get(status, status)])
            item.setToolTip(self.COL_OBJECT, row.get("shape") or node)
            item.setToolTip(self.COL_RULE, row.get("reason") or
                            "one UV set named '{0}'".format(wanted))
            item.setForeground(self.COL_RULE, QBrush(QColor(
                ok_color if status == STATUS_OK else bad_color)))
            self.tree.addTopLevelItem(item)

        for col in range(3):
            self.tree.resizeColumnToContents(col)

        total = len(rows or [])
        self.lbl_title.setText(
            "UV Sets   {0} / {1} OK".format(passed, total) if total else "UV Sets")

    def row_texts(self):
        """(오브젝트, UV 세트, 판정) 글 목록 - 테스트·로그용."""
        return [tuple(self.tree.topLevelItem(i).text(c) for c in range(3))
                for i in range(self.tree.topLevelItemCount())]
