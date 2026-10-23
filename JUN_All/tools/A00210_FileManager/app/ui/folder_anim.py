# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00210_FileManager - Shrink 폴더 · 기록 카드 애니메이션 위젯 (Qt, standalone)
#
# Shrink 로 줄어든 창의 버튼 왼쪽 자리에서, 이 툴 아이콘(icon/A00210_FileManager.svg)의
# 폴더 · 기록 카드 · 동기화 뱃지가 움직이기를 **무한 반복**한다 (v01.38).
#
# 한 바퀴 (start() = 0 초, PERIOD = 3.0 초) - 끝나면 처음부터
#   0.0-0.5   올라온다  - 폴더 앞판 뒤에 숨어 있던 기록 카드가 위로 올라온다 (ease-out)
#   0.5-1.4   채워진다  - 카드에 썸네일 · 제목 · 로그 줄이 0.3 초 간격으로 들어온다 (3 단계)
#   1.4-2.2   동기화    - 폴더 오른쪽 아래 뱃지의 화살표 호 둘이 한 바퀴 돈다
#   2.2-2.7   내려간다  - 카드가 폴더 안으로 돌아간다 (ease-in)
#   2.7-3.0   쉼        - 닫힌 폴더만 - 그리고 0.0 으로
#
# A00220 공룡 · A00240 파일 트리 · A00370 로켓과 같은 방식이다 - 코드 안 비트맵을 QPainter 로
# 칸마다 채운다. 카드 몸체는 테마 글자색(palette windowText), 폴더 · 로그 줄 · 뱃지는 아이콘
# svg 의 파랑 그대로. 외부 에셋이 없어 exe 번들에도 그대로 실린다.

import math

from Framework.qt.qt import (
    QWidget,
    QTimer,
    QElapsedTimer,
    QPainter,
    QColor,
    QSize,
    Qt,
)


#: 그림 칸 수 (가로 x 세로) - 창 높이에 맞춰 칸 크기(scale)가 정해진다.
GRID_W = 30
GRID_H = 32

#: 아이콘 svg 의 색
COLOR_FOLDER_BACK = QColor("#2f6bd6")
COLOR_FOLDER_FRONT = QColor("#4c8dff")
COLOR_THUMB = QColor("#8fb6ff")
COLOR_TITLE = QColor("#3d78e0")
COLOR_LINE = QColor("#9db6d6")
COLOR_LINE_LIGHT = QColor("#c2d2e8")
COLOR_BADGE_BG = QColor("#161f2b")
COLOR_BADGE_RING = QColor("#4c8dff")
COLOR_BADGE_ARROW = QColor("#e6f0ff")   # svg 는 #7fb0ff - 링과 구분되게 더 밝게

#: 폴더 - (x, y, w, h) 칸. 뒷판(탭 포함) 위에 카드, 그 위에 앞판.
FOLDER_TAB = (2, 15, 9, 2)
FOLDER_BACK = (2, 17, 26, 15)
FOLDER_FRONT = (1, 22, 28, 10)

#: 기록 카드 - 크기와 x, 올라온 y / 숨은 y (앞판 뒤).
CARD_W = 16
CARD_H = 14
CARD_X = 7
CARD_Y_UP = 3
CARD_Y_DOWN = 24

#: 카드 안 내용 - 카드 왼쪽 위 기준 (x, y, w, h, 색, 단계). 단계 순서대로 채워진다.
CARD_PARTS = (
    (2, 2, 6, 5, COLOR_THUMB, 0),        # 썸네일
    (9, 2, 5, 1, COLOR_TITLE, 0),        # 제목
    (9, 4, 4, 1, COLOR_LINE, 1),         # 작업자
    (2, 9, 12, 1, COLOR_LINE, 2),        # 로그 1
    (2, 11, 9, 1, COLOR_LINE_LIGHT, 2),  # 로그 2
)
FILL_STEPS = 3

#: 동기화 뱃지 - 9 x 9, 왼쪽 위 칸. 폴더 앞판 오른쪽 아래.
BADGE_X = 19
BADGE_Y = 23
BADGE_N = 9
#: 뱃지 링을 시계 방향으로 한 바퀴 돈 칸들 (24 칸). 화살표 호 둘이 이 위를 돈다.
BADGE_RING = (
    (3, 0), (4, 0), (5, 0), (6, 1), (7, 1), (7, 2), (8, 3), (8, 4), (8, 5), (7, 6), (7, 7), (6, 7),
    (5, 8), (4, 8), (3, 8), (2, 7), (1, 7), (1, 6), (0, 5), (0, 4), (0, 3), (1, 2), (1, 1), (2, 1),
)
ARC_CELLS = 8            # 호 하나의 길이 (칸)
ARC_STEP = 2             # 한 프레임에 호가 움직이는 칸 수
ARC_FRAMES = len(BADGE_RING) // ARC_STEP     # 한 바퀴 = 12 프레임
#: 링 안쪽(배경) 칸 - 중심에서 거리로 구한다.
BADGE_INNER = tuple(
    (x, y) for y in range(BADGE_N) for x in range(BADGE_N)
    if (x, y) not in BADGE_RING and math.hypot(x - 4, y - 4) <= 3.6)


def ease_out(x):
    """0..1 -> 0..1, 끝에서 느려지는 곡선(cubic)."""
    x = min(1.0, max(0.0, x))
    return 1.0 - (1.0 - x) ** 3


def ease_in(x):
    """0..1 -> 0..1, 처음에 느리고 끝에서 빨라지는 곡선(quadratic)."""
    x = min(1.0, max(0.0, x))
    return x * x


class FolderAnimWidget(QWidget):
    """Shrink 때 버튼 왼쪽에서 폴더 · 기록 카드 · 동기화 뱃지를 되풀이한다. start() 로 재생, stop() 으로 정지."""

    RISE = 0.5                       # 카드가 올라오는 시간
    FILL_START = RISE + 0.1          # 첫 내용이 들어오는 시각
    FILL_GAP = 0.3                   # 내용 단계 사이
    SYNC_START = 1.4                 # 뱃지가 돌기 시작
    SYNC_END = 2.2
    LOWER = 0.5                      # 카드가 내려가는 시간
    LOWER_END = SYNC_END + LOWER     # 2.7
    PERIOD = 3.0

    SYNC_FRAME = (SYNC_END - SYNC_START) / ARC_FRAMES   # 한 프레임 시간 - 동기화 동안 꼭 한 바퀴

    FRAME_MS = 16        # 약 60fps (모습이 바뀔 때만 다시 그린다)

    def __init__(self, parent=None):
        super(FolderAnimWidget, self).__init__(parent)

        self._clock = QElapsedTimer()
        self._frozen = None          # set_elapsed() 로 고정한 시각 (테스트용)
        self._elapsed = 0.0          # 지금 바퀴 안의 시각 (0 .. PERIOD)
        self._drawn = None           # 마지막으로 그린 상태 - 같으면 다시 그리지 않는다

        self._timer = QTimer(self)
        self._timer.setInterval(self.FRAME_MS)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ 제어

    def start(self):
        """t = 0 부터 재생한다 (Shrink 를 켤 때마다)."""
        self._frozen = None
        self._elapsed = 0.0
        self._drawn = None
        self._clock.start()
        self._timer.start()
        self.update()

    def stop(self):
        """타이머를 멈추고 처음 모습(닫힌 폴더)으로 되돌린다."""
        self._timer.stop()
        self._resume = False
        self._frozen = None
        self._elapsed = 0.0
        self._drawn = None
        self.update()

    def set_elapsed(self, seconds):
        """그 시각의 모습으로 고정한다 (테스트 · 캡처용). 타이머는 멈춘다. 바퀴를 넘으면 되감긴다."""
        self._timer.stop()
        self._frozen = float(seconds)
        self._elapsed = self._frozen % self.PERIOD
        self.update()

    def is_running(self):
        return self._timer.isActive()

    def elapsed(self):
        return self._elapsed

    def phase(self):
        """'rise' | 'fill' | 'sync' | 'lower' | 'rest' - 지금 바퀴 안의 단계."""
        t = self._elapsed
        if t < self.RISE:
            return "rise"
        if t < self.SYNC_START:
            return "fill"
        if t < self.SYNC_END:
            return "sync"
        if t < self.LOWER_END:
            return "lower"
        return "rest"

    def card_lift(self):
        """카드가 올라온 정도 0..1 (0 = 폴더 안, 1 = 다 올라옴)."""
        t = self._elapsed
        if t < self.RISE:
            return ease_out(t / self.RISE)
        if t < self.SYNC_END:
            return 1.0
        if t < self.LOWER_END:
            return 1.0 - ease_in((t - self.SYNC_END) / self.LOWER)
        return 0.0

    def fill_count(self):
        """카드에 들어온 내용 단계 수 0..FILL_STEPS. 내려가는 동안엔 그대로, 쉴 때 0."""
        t = self._elapsed
        if t < self.FILL_START or t >= self.LOWER_END:
            return 0
        return min(FILL_STEPS, int((t - self.FILL_START) / self.FILL_GAP) + 1)

    def badge_frame(self):
        """뱃지 화살표 호의 프레임 0..ARC_FRAMES-1. 동기화 구간에서만 돈다."""
        t = self._elapsed
        if t < self.SYNC_START or t >= self.SYNC_END:
            return 0
        return int((t - self.SYNC_START) / self.SYNC_FRAME) % ARC_FRAMES

    def _state(self):
        return (round(self.card_lift(), 3), self.fill_count(), self.badge_frame())

    def _tick(self):
        # 무한 반복 - 바퀴 안의 시각으로 되감는다.
        self._elapsed = (self._clock.elapsed() / 1000.0) % self.PERIOD
        state = self._state()
        if state != self._drawn:
            self._drawn = state
            self.update()

    def hideEvent(self, event):
        # 줄어든 상태를 풀면 숨겨진다 - 그때 타이머도 세운다. 단, Pin 토글처럼 창 플래그가 바뀌어
        # 잠깐 숨었다 다시 보이는 경우가 있으므로, 돌던 중이었으면 기억해 두고 showEvent 에서 잇는다.
        self._resume = self._timer.isActive()
        self._timer.stop()
        super(FolderAnimWidget, self).hideEvent(event)

    def showEvent(self, event):
        super(FolderAnimWidget, self).showEvent(event)
        if getattr(self, "_resume", False):
            self._resume = False
            self._timer.start()

    # ------------------------------------------------------------------ 배치

    def sizeHint(self):
        return QSize(GRID_W * 4 + 10, GRID_H * 4 + 10)

    def minimumSizeHint(self):
        return QSize(GRID_W * 2, GRID_H * 2)

    def _scale(self):
        """칸 크기 - 그림 전체가 창에 들어가게."""
        return max(1, min(self.height() // GRID_H, self.width() // GRID_W))

    def _origin(self, scale):
        """그림 왼쪽 위 픽셀 - 가로 가운데, 세로 아래 맞춤."""
        x = (self.width() - GRID_W * scale) / 2.0
        y = self.height() - GRID_H * scale
        return x, y

    def card_y_cells(self):
        """지금 카드의 위쪽 y (칸, 소수). 테스트용."""
        return CARD_Y_DOWN + (CARD_Y_UP - CARD_Y_DOWN) * self.card_lift()

    # ------------------------------------------------------------------ 그리기

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        card_color = self.palette().windowText().color()
        if not card_color.isValid():
            card_color = QColor("#eef4ff")

        scale = self._scale()
        ox, oy = self._origin(scale)

        def cell_rect(x, y, w, h):
            return (int(round(ox + x * scale)), int(round(oy + y * scale)),
                    int(round(w * scale)), int(round(h * scale)))

        # 폴더 뒷판 + 탭
        painter.setBrush(COLOR_FOLDER_BACK)
        painter.drawRect(*cell_rect(*FOLDER_TAB))
        painter.drawRect(*cell_rect(*FOLDER_BACK))

        # 기록 카드 - 앞판이 덮는 부분은 앞판이 가린다.
        card_y = self.card_y_cells()
        painter.setBrush(card_color)
        painter.drawRect(*cell_rect(CARD_X, card_y, CARD_W, CARD_H))
        filled = self.fill_count()
        for px, py, pw, ph, color, step in CARD_PARTS:
            if step < filled:
                painter.setBrush(color)
                painter.drawRect(*cell_rect(CARD_X + px, card_y + py, pw, ph))

        # 폴더 앞판
        painter.setBrush(COLOR_FOLDER_FRONT)
        painter.drawRect(*cell_rect(*FOLDER_FRONT))

        # 동기화 뱃지 - 배경 · 링 · 화살표 호 둘(프레임만큼 링을 따라 돈다)
        painter.setBrush(COLOR_BADGE_BG)
        for x, y in BADGE_INNER:
            painter.drawRect(*cell_rect(BADGE_X + x, BADGE_Y + y, 1, 1))
        frame = self.badge_frame()
        n = len(BADGE_RING)
        arc = set()
        for start in (0, n // 2):
            for i in range(ARC_CELLS):
                arc.add((start + i + frame * ARC_STEP) % n)
        for idx, (x, y) in enumerate(BADGE_RING):
            painter.setBrush(COLOR_BADGE_ARROW if idx in arc else COLOR_BADGE_RING)
            painter.drawRect(*cell_rect(BADGE_X + x, BADGE_Y + y, 1, 1))
        painter.end()
