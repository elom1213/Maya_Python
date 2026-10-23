# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00370_ToolLauncher - Shrink 로켓 발사 애니메이션 위젯 (Qt, in-Maya)
#
# Shrink 로 줄어든 창의 버튼 왼쪽 자리에서, 이 툴 아이콘의 로켓이 위로 발사되기를
# **무한 반복**하는 짧은 애니메이션을 그린다 (v01.11).
#
# 한 바퀴 (start() = 0 초, PERIOD = 2.4 초) - 끝나면 처음부터
#   0.00-0.60   발사대 위에서 점화 - 불꽃이 깜빡이고 몸체가 살짝 떤다
#   0.60-1.80   상승 - 바닥에서 창 위로 사라질 때까지 (ease-in, 점점 빨라진다)
#               지나간 자리에 배기 연기 점이 남았다가 옅어진다
#   1.80-2.40   빈 하늘 (연기만 사라진다) - 그리고 0.00 으로
#
# A00220 의 공룡(dino_widget.py) · A00240 의 파일 트리(file_tree_anim.py)와 같은 방식이다 -
# 코드 안 비트맵을 QPainter 로 칸마다 채운다. 로켓 몸체는 테마 글자색(palette windowText),
# 창문 · 꼬리날개 · 불꽃은 툴 아이콘(icon/A00370_ToolLauncher.svg)의 코랄 색 그대로.
# 외부 에셋이 없어 릴리즈본에도 그대로 실린다.

from Framework.qt.qt import (
    QWidget,
    QTimer,
    QElapsedTimer,
    QPainter,
    QColor,
    QSize,
    Qt,
)


#: 로켓 11 x 14 ('B' = 몸체, 'W' = 창문, 'F' = 꼬리날개, '.' = 빈 칸).
#: 아이콘 svg 의 로켓(둥근 머리 · 창문 하나 · 날개 둘)을 픽셀로 옮긴 것.
ROCKET = [
    ".....B.....",
    "....BBB....",
    "....BBB....",
    "...BBBBB...",
    "...BBBBB...",
    "...BBWBB...",
    "...BWWWB...",
    "...BBWBB...",
    "...BBBBB...",
    "..FBBBBBF..",
    ".FFBBBBBFF.",
    "FFFBBBBBFFF",
    "FF.BBBBB.FF",
    "F...BBB...F",
]
ROCKET_W = len(ROCKET[0])
ROCKET_H = len(ROCKET)

#: 불꽃 두 모양 - 번갈아 그려 깜빡인다 ('E' = 불꽃). 로켓 바로 아래에 붙는다.
FLAME_FRAMES = (
    [
        "....EEE....",
        "....EEE....",
        ".....E.....",
    ],
    [
        "....EEE....",
        ".....E.....",
        "...........",
    ],
)
FLAME_H = len(FLAME_FRAMES[0])

#: 아이콘 svg 의 색 - 창문 · 불꽃(코랄), 꼬리날개(연한 주황)
COLOR_WINDOW = QColor("#ff7a59")
COLOR_FLAME = QColor("#ff7a59")
COLOR_FIN = QColor("#ffb27a")

#: 발사대(바닥 선) 굵기 (칸 수) 와 투명도
PAD_CELLS = 1
PAD_ALPHA = 0.6

#: 연기 점 - 상승 중 일정 간격마다 하나씩 남긴다
SMOKE_SPACING = 0.08      # 초 - 점 사이 시간 간격
SMOKE_LIFE = 0.9          # 초 - 점이 사라지기까지
SMOKE_ALPHA = 0.5


def ease_in(x):
    """0..1 -> 0..1, 처음에 느리고 끝에서 빨라지는 곡선(quadratic) - 발사 가속."""
    x = min(1.0, max(0.0, x))
    return x * x


class RocketAnimWidget(QWidget):
    """Shrink 때 버튼 왼쪽에서 로켓 발사를 되풀이한다. start() 로 재생, stop() 으로 정지."""

    IGNITION = 0.6       # 발사대에서 점화하는 시간
    ASCEND = 1.2         # 바닥에서 창 밖까지 오르는 시간
    REST = 0.6           # 빈 하늘
    LIFTOFF = IGNITION
    GONE = IGNITION + ASCEND
    PERIOD = IGNITION + ASCEND + REST

    FLICKER = 0.08       # 불꽃 모양이 바뀌는 간격 (초)
    SHAKE_CELLS = 1      # 점화 중 몸체가 좌우로 떠는 폭 (칸)

    FRAME_MS = 16        # 약 60fps (모습이 바뀔 때만 다시 그린다)

    def __init__(self, parent=None):
        super(RocketAnimWidget, self).__init__(parent)

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
        """타이머를 멈추고 처음 모습(발사대 위)으로 되돌린다."""
        self._timer.stop()
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
        """'ignition' | 'ascend' | 'rest' - 지금 바퀴 안의 단계."""
        t = self._elapsed
        if t < self.LIFTOFF:
            return "ignition"
        if t < self.GONE:
            return "ascend"
        return "rest"

    def ascent(self):
        """상승 진행값 0..1 (ease-in). 점화 중 0, 사라진 뒤 1."""
        return ease_in((self._elapsed - self.LIFTOFF) / self.ASCEND)

    def rocket_visible(self):
        """로켓이 화면 안에 그려지는가 (사라진 뒤 빈 하늘이면 False)."""
        return self._elapsed < self.GONE

    def _flame_index(self):
        return int(self._elapsed / self.FLICKER) % len(FLAME_FRAMES)

    def _state(self):
        """그리기에 영향을 주는 값들 - 바뀔 때만 다시 그린다."""
        phase = self.phase()
        if phase == "rest":
            # 연기만 옅어진다 - 연기가 다 꺼지면 그릴 것이 없다
            smoke = tuple(self._smoke_points())
            return (phase, smoke)
        return (phase, self._flame_index(), round(self.ascent(), 4),
                tuple(self._smoke_points()))

    def _tick(self):
        # 무한 반복 - 바퀴 안의 시각으로 되감는다.
        self._elapsed = (self._clock.elapsed() / 1000.0) % self.PERIOD
        state = self._state()
        if state != self._drawn:
            self._drawn = state
            self.update()

    def hideEvent(self, event):
        # 줄어든 상태를 풀면 숨겨진다 - 그때 타이머도 세운다.
        self._timer.stop()
        super(RocketAnimWidget, self).hideEvent(event)

    # ------------------------------------------------------------------ 배치

    def sizeHint(self):
        return QSize(ROCKET_W * 4 + 20, (ROCKET_H + FLAME_H) * 4 + 20)

    def minimumSizeHint(self):
        return QSize(ROCKET_W * 2, (ROCKET_H + FLAME_H) * 2)

    def _scale(self):
        """칸 크기 - 창 높이에 로켓 둘(여정) 정도가 들어가게, 가로도 넘치지 않게."""
        by_h = self.height() // ((ROCKET_H + FLAME_H) * 2)
        by_w = self.width() // (ROCKET_W + 6)
        return max(1, min(by_h, by_w))

    def _travel(self, scale):
        """(출발 y, 도착 y) - 로켓 왼쪽 위 기준. 출발은 발사대 위, 도착은 창 위 바깥."""
        pad_y = self.height() - PAD_CELLS * scale
        start_y = pad_y - (ROCKET_H + FLAME_H) * scale
        end_y = -(ROCKET_H + FLAME_H) * scale
        return start_y, end_y

    def rocket_pos(self):
        """지금 로켓의 왼쪽 위 (x, y) - 픽셀. 점화 중엔 좌우로 떤다."""
        scale = self._scale()
        start_y, end_y = self._travel(scale)
        x = (self.width() - ROCKET_W * scale) / 2.0
        if self.phase() == "ignition":
            # 불꽃 깜빡임과 같은 박자로 1칸 좌우
            shake = (self._flame_index() * 2 - 1) * self.SHAKE_CELLS * scale * 0.5
            return x + shake, start_y
        y = start_y + (end_y - start_y) * self.ascent()
        return x, y

    def _smoke_points(self):
        """(y 비율, 남은 수명 0..1) - 상승 중 남긴 연기 점들. 비율은 출발 0 .. 도착 1."""
        t = self._elapsed
        if t < self.LIFTOFF:
            return []
        points = []
        born = self.LIFTOFF
        while born <= min(t, self.GONE):
            age = t - born
            if age < SMOKE_LIFE:
                frac = ease_in((born - self.LIFTOFF) / self.ASCEND)
                points.append((round(frac, 3), round(1.0 - age / SMOKE_LIFE, 2)))
            born += SMOKE_SPACING
        return points

    # ------------------------------------------------------------------ 그리기

    def paintEvent(self, event):
        painter = QPainter(self)
        body = self.palette().windowText().color()
        if not body.isValid():
            body = QColor("#535353")

        scale = self._scale()
        start_y, end_y = self._travel(scale)
        painter.setPen(Qt.NoPen)

        # 발사대 - 바닥에 가로선
        pad = QColor(body)
        pad.setAlphaF(PAD_ALPHA)
        painter.setBrush(pad)
        pad_w = (ROCKET_W + 4) * scale
        pad_x = int((self.width() - pad_w) / 2.0)
        painter.drawRect(pad_x, self.height() - PAD_CELLS * scale, pad_w, PAD_CELLS * scale)

        # 연기 - 로켓이 지나간 자리 (가운데 열, 옅어진다)
        cx = int((self.width() - scale) / 2.0)
        flame_bottom_offset = (ROCKET_H + FLAME_H) * scale
        for frac, life in self._smoke_points():
            y = start_y + (end_y - start_y) * frac + flame_bottom_offset - scale
            smoke = QColor(body)
            smoke.setAlphaF(SMOKE_ALPHA * life)
            painter.setBrush(smoke)
            size = max(1, int(scale * (0.5 + life * 0.5)))
            painter.drawRect(cx, int(y), size, size)

        if self.rocket_visible():
            x, y = self.rocket_pos()
            self._draw_rocket(painter, body, scale, x, y)
            self._draw_flame(painter, scale, x, y + ROCKET_H * scale, self._flame_index())
        painter.end()

    @staticmethod
    def _draw_rocket(painter, body, scale, x, y):
        x0 = int(round(x))
        y0 = int(round(y))
        colors = {"B": body, "W": COLOR_WINDOW, "F": COLOR_FIN}
        for r, line in enumerate(ROCKET):
            for col, ch in enumerate(line):
                color = colors.get(ch)
                if color is not None:
                    painter.setBrush(color)
                    painter.drawRect(x0 + col * scale, y0 + r * scale, scale, scale)

    @staticmethod
    def _draw_flame(painter, scale, x, y, index):
        x0 = int(round(x))
        y0 = int(round(y))
        painter.setBrush(COLOR_FLAME)
        for r, line in enumerate(FLAME_FRAMES[index]):
            for col, ch in enumerate(line):
                if ch == "E":
                    painter.drawRect(x0 + col * scale, y0 + r * scale, scale, scale)
