# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - screen region capture overlay (Qt)
#
# 프레임리스 풀스크린 반투명 오버레이에서 드래그로 화면 영역을 선택해 PNG 로 저장한다.
# Maya 뷰포트든 무엇이든 "화면에 보이는 것" 을 그대로 캡쳐한다 (playblast 미사용).

import os
import tempfile

from Framework.qt.qt import (
    QWidget,
    QApplication,
    QGuiApplication,
    QRect,
    QPoint,
    Qt,
    QPainter,
    QColor,
    QPen,
    QTimer,
    Signal,
)


class RegionCapture(QWidget):
    """드래그로 화면 영역을 선택해 임시 PNG 경로를 captured 시그널로 보낸다."""

    captured = Signal(str)    # 저장된 임시 PNG 경로
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)

        # 전체 가상 데스크탑(모든 모니터) 영역을 덮는다.
        self._virtual_rect = self._compute_virtual_rect()
        self.setGeometry(self._virtual_rect)

        self._origin = None      # 시작점 (global)
        self._current = None     # 현재점 (global)
        self._selected = None    # 확정 QRect (global)

    @staticmethod
    def _compute_virtual_rect():
        rect = QRect()
        for screen in QGuiApplication.screens():
            rect = rect.united(screen.geometry())
        return rect

    # ----------------------------------------------------------- painting

    def paintEvent(self, event):
        painter = QPainter(self)

        # 전체를 어둡게 덮는다.
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        if self._origin and self._current:
            sel = self._selection_rect_local()

            # 선택 영역은 다시 비운다(밝게).
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(sel, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            pen = QPen(QColor(80, 170, 255), 2)
            painter.setPen(pen)
            painter.drawRect(sel)

    def _selection_rect_local(self):
        """위젯 로컬 좌표 기준 선택 사각형."""
        origin = self.mapFromGlobal(self._origin)
        current = self.mapFromGlobal(self._current)
        return QRect(origin, current).normalized()

    # ------------------------------------------------------------- events

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._origin = self.mapToGlobal(event.pos())
            self._current = self._origin
            self.update()

    def mouseMoveEvent(self, event):
        if self._origin is not None:
            self._current = self.mapToGlobal(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._origin is None:
            return

        self._current = self.mapToGlobal(event.pos())
        self._selected = QRect(self._origin, self._current).normalized()

        if self._selected.width() < 5 or self._selected.height() < 5:
            # 너무 작으면 취소로 본다.
            self._finish_cancel()
            return

        # 오버레이가 화면에서 사라진 뒤 캡쳐해야 자기 자신이 안 찍힌다.
        self.hide()
        QTimer.singleShot(120, self._grab)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._finish_cancel()

    # ------------------------------------------------------------ capture

    def _grab(self):
        rect = self._selected
        screen = QGuiApplication.screenAt(rect.center()) or QGuiApplication.primaryScreen()
        geo = screen.geometry()

        pixmap = screen.grabWindow(
            0,
            rect.x() - geo.x(),
            rect.y() - geo.y(),
            rect.width(),
            rect.height(),
        )

        fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="jun_fm_thumb_")
        os.close(fd)

        if pixmap.save(tmp_path, "PNG"):
            self.captured.emit(tmp_path)
        else:
            self.cancelled.emit()

        self.close()

    def _finish_cancel(self):
        self.cancelled.emit()
        self.close()
