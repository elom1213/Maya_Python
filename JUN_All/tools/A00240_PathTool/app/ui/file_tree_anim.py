# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00240_PathTool - Shrink 파일 트리 애니메이션 위젯 (Qt, standalone)
#
# Shrink 로 줄어든 창의 버튼 왼쪽 자리에서, 파일 트리가 자라나는 짧은 애니메이션을 그린다.
# 계획서: docs/plans/A00240_PathTool_shrink_animation_plan.md
#
#   {파일 0}
#   ├── {파일 1}
#   │   └── {파일 2}
#   └── {파일 1}
#       └── {파일 2}
#
# 타임라인 (start() = 0 초) - 1.5 초마다 처음부터 **무한 반복** (v01.12)
#   0.00-0.50   파일 0 만
#   0.50-0.75   파일 1 둘이 파일 0 에서 펼쳐진다
#   1.00-1.25   파일 2 둘이 각자의 파일 1 에서 펼쳐진다
#   1.25-1.50   완성된 트리 - 그리고 0.00 으로
#   (단계마다 0.5 초씩 보인다 - 완성된 트리도 0.5 초 머문 뒤 되돌아간다)
#
# v01.12 피드백: 무한 반복 · 맨 밑의 파일 1, 2 한 쌍을 뺐다(7행 -> 5행) · 선을 굵게(1 -> 2px).
#
# "펼쳐진다" = 진행값 p(0->1, ease-out) 하나로 세 가지가 함께 움직인다
#   1) 자식 아이콘이 부모 자리에서 출발해 자기 행 · 들여쓰기로 이동 (아래 행일수록 멀리 - 부채꼴)
#   2) 부모에서 내려오는 연결선이 자식을 따라 자란다
#   3) 투명도 0 -> 1 (출발점에서 부모와 겹쳐 보이지 않게)
#
# A00220_BackupTool 의 공룡(dino_widget.py)과 같은 방식이다 - 코드 안 비트맵을 QPainter 로
# 칸마다 채우고, 색은 테마 글자색(palette windowText)을 쓴다. 외부 에셋이 없어 exe 번들도 그대로.

from Framework.qt.qt import (
    QWidget,
    QTimer,
    QElapsedTimer,
    QPainter,
    QColor,
    QSize,
    Qt,
)


#: 파일 아이콘 10 x 12 ('#' = 선). 선 굵기 2칸, 오른쪽 위가 접힌 모서리.
#: (v01.11 은 7 x 9 에 선 1칸 - 굵게 해 달라는 피드백으로 바꿨다. 5행이라 한 행이 약 15px 로 들어간다.)
FILE_ICON = [
    "#######...",
    "#######...",
    "##...####.",
    "##...#####",
    "##......##",
    "##......##",
    "##......##",
    "##......##",
    "##......##",
    "##......##",
    "##########",
    "##########",
]
ICON_W = len(FILE_ICON[0])
ICON_H = len(FILE_ICON)

#: 트리 행 수 (0 한 줄 + (1, 2) 두 쌍)
ROWS = 5

#: 아이콘 1 의 행 / 그 아래(+1) 아이콘 2 의 행
LEVEL1_ROWS = (1, 3)

#: 연결선 굵기 (칸 수) - 아이콘 테두리와 같은 2칸
LINE_CELLS = 2

#: 연결선 투명도 (아이콘보다 옅게)
LINE_ALPHA = 0.6


def ease_out(x):
    """0..1 -> 0..1, 끝에서 느려지는 곡선(cubic)."""
    x = min(1.0, max(0.0, x))
    return 1.0 - (1.0 - x) ** 3


class FileTreeAnimWidget(QWidget):
    """Shrink 때 버튼 왼쪽에서 파일 트리가 자라나기를 되풀이한다. start() 로 재생, stop() 으로 정지."""

    STEP_DELAY = 0.5     # 단계 사이 (요청)
    UNFOLD = 0.25        # 한 단계가 펼쳐지는 시간
    LEVEL1_START = STEP_DELAY
    LEVEL2_START = STEP_DELAY * 2
    DONE = LEVEL2_START + UNFOLD
    PERIOD = STEP_DELAY * 3      # 한 바퀴 - 완성된 트리도 한 단계만큼 보인 뒤 처음으로

    FRAME_MS = 16        # 약 60fps (줄어든 동안 돈다 - 머무는 구간엔 다시 그리지 않는다)

    def __init__(self, parent=None):
        super(FileTreeAnimWidget, self).__init__(parent)

        self._clock = QElapsedTimer()
        self._frozen = None          # set_elapsed() 로 고정한 시각 (테스트용)
        self._elapsed = 0.0          # 지금 바퀴 안의 시각 (0 .. PERIOD)
        self._drawn = None           # 마지막으로 그린 진행값 - 같으면 다시 그리지 않는다

        self._timer = QTimer(self)
        self._timer.setInterval(self.FRAME_MS)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ 제어

    def start(self):
        """t = 0 부터 재생한다 (Shrink 를 켤 때마다)."""
        self._frozen = None
        self._elapsed = 0.0
        self._clock.start()
        self._timer.start()
        self.update()

    def stop(self):
        """타이머를 멈추고 처음 모습(파일 0 만)으로 되돌린다."""
        self._timer.stop()
        self._frozen = None
        self._elapsed = 0.0
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

    def progress(self):
        """(아이콘 1 진행값, 아이콘 2 진행값) - 각 0..1."""
        t = self._elapsed
        return (ease_out((t - self.LEVEL1_START) / self.UNFOLD),
                ease_out((t - self.LEVEL2_START) / self.UNFOLD))

    def visible_icons(self):
        """지금 그려지는 아이콘 수 (파일 0 포함). 펼치는 중인 것도 센다."""
        p1, p2 = self.progress()
        n = len(LEVEL1_ROWS)
        return 1 + (n if p1 > 0 else 0) + (n if p2 > 0 else 0)

    def _tick(self):
        # 무한 반복 - 바퀴 안의 시각으로 되감는다.
        self._elapsed = (self._clock.elapsed() / 1000.0) % self.PERIOD
        # 펼치는 동안에만 모습이 바뀐다. 머무는 구간(0.5 초씩)은 다시 그리지 않는다
        # - 줄어든 창은 오래 켜 두므로 쉬는 구간에 그리기를 쉬어 CPU 를 아낀다.
        state = self.progress()
        if state != self._drawn:
            self._drawn = state
            self.update()

    def hideEvent(self, event):
        # 줄어든 상태를 풀면 숨겨진다 - 그때 타이머도 세운다.
        self._timer.stop()
        super(FileTreeAnimWidget, self).hideEvent(event)

    # ------------------------------------------------------------------ 배치

    def sizeHint(self):
        return QSize(ICON_W * 3 + 30, ROWS * (ICON_H + 1))

    def minimumSizeHint(self):
        return QSize(ICON_W * 3 + 20, ROWS * ICON_H)

    def _geometry(self):
        """(칸 크기, 행 높이, 들여쓰기, 왼쪽 여백, 위 여백) - 위젯 크기에서 계산한다.

        행 = 높이 / ROWS. 행이 아이콘보다 넉넉하면 칸 크기(scale)를 키워 또렷하게 그린다.
        """
        row_h = self.height() / float(ROWS)
        scale = max(1, int(row_h // (ICON_H + 1)))
        icon_h = ICON_H * scale
        # 행이 아이콘보다 낮으면(아주 작은 창) 행 높이를 아이콘 높이로 - 아래가 조금 잘린다.
        row_h = max(row_h, float(icon_h))
        indent = ICON_W * scale + 5 * scale
        left = 2
        top = (self.height() - row_h * ROWS) / 2.0
        return scale, row_h, indent, left, top

    def _slot(self, row, level):
        """행 · 들여쓰기 단계 -> 그 자리 아이콘의 왼쪽 위 (x, y)."""
        scale, row_h, indent, left, top = self._geometry()
        icon_h = ICON_H * scale
        x = left + indent * level
        y = top + row_h * row + (row_h - icon_h) / 2.0
        return x, y

    # ------------------------------------------------------------------ 그리기

    def paintEvent(self, event):
        painter = QPainter(self)
        color = self.palette().windowText().color()
        if not color.isValid():
            color = QColor("#535353")

        scale = self._geometry()[0]
        p1, p2 = self.progress()

        root = self._slot(0, 0)
        # 자식 먼저 그리고 부모를 위에 - 출발점에서 겹칠 때 부모가 덮는다.
        for row in LEVEL1_ROWS:
            parent1 = self._slot(row, 1)
            if p2 > 0:
                self._draw_child(painter, color, scale, parent1,
                                 self._slot(row + 1, 2), p2)
        for row in LEVEL1_ROWS:
            if p1 > 0:
                # 아이콘 2 는 아이콘 1 이 다 자란 뒤에 나오므로 부모 자리는 최종 위치다.
                self._draw_child(painter, color, scale, root,
                                 self._slot(row, 1), p1)
        self._draw_icon(painter, color, scale, root[0], root[1], 1.0)
        painter.end()

    def _draw_child(self, painter, color, scale, parent, target, p):
        """부모 자리에서 target 으로 p 만큼 나온 자식 아이콘 + 연결선."""
        px, py = parent
        tx, ty = target
        x = px + (tx - px) * p
        y = py + (ty - py) * p

        icon_w = ICON_W * scale
        icon_h = ICON_H * scale
        # 부모 아래로 내려오는 세로선 - 아이콘 가운데 (굵기의 절반만큼 왼쪽으로)
        trunk_x = int(px + icon_w / 2.0 - LINE_CELLS * scale / 2.0)
        parent_bottom = py + icon_h
        child_mid = y + icon_h / 2.0

        line = QColor(color)
        line.setAlphaF(LINE_ALPHA * p)
        painter.setPen(Qt.NoPen)
        painter.setBrush(line)
        thick = LINE_CELLS * scale
        # 세로선: 부모 밑에서 자식 가운데 높이까지
        if child_mid > parent_bottom:
            painter.drawRect(trunk_x, int(parent_bottom) + 1, thick,
                             int(child_mid - parent_bottom))
        # 가로선: 세로선에서 자식 왼쪽 앞까지 (두 칸 띄운다)
        branch_end = x - 2 * scale
        if branch_end > trunk_x + thick:
            painter.drawRect(trunk_x, int(child_mid - thick / 2.0),
                             int(branch_end - trunk_x), thick)

        self._draw_icon(painter, color, scale, x, y, p)

    @staticmethod
    def _draw_icon(painter, color, scale, x, y, alpha):
        c = QColor(color)
        c.setAlphaF(max(0.0, min(1.0, alpha)))
        painter.setPen(Qt.NoPen)
        painter.setBrush(c)
        x0 = int(round(x))
        y0 = int(round(y))
        for r, line in enumerate(FILE_ICON):
            for col, ch in enumerate(line):
                if ch == "#":
                    painter.drawRect(x0 + col * scale, y0 + r * scale, scale, scale)
