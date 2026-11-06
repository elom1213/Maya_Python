# Python Script by Ji Hun Park
# last Update date : 2026-11-06
# A00210_FileManager - 체크 항목을 눌러도 닫히지 않는 메뉴 (File Types 확장자 필터)
#
# v01.52 : main_window 의 _CheckableMenu 를 옮겨 왔다 - File Manager 와 Sync > Status 의 `File Types` 버튼이 같이 쓴다
#          (sync_tab 은 main_window 를 import 할 수 없다 - 순환).

from Framework.qt.qt import QMenu


class CheckableMenu(QMenu):
    """체크 가능한 항목을 토글해도 닫히지 않는 메뉴.

    기본 QMenu 는 항목 클릭 시 닫히므로 여러 확장자를 연속으로 체크/해제하기 불편하다.
    체크 가능한 항목 위에서 마우스를 떼면 닫지 않고 그 항목만 토글(trigger)한다.
    """

    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action is not None and action.isEnabled() and action.isCheckable():
            action.trigger()   # 체크 토글 + triggered(bool) 방출, 메뉴는 유지
            return
        super().mouseReleaseEvent(event)
