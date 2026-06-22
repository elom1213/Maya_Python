# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00220_BackupTool - Chrome-Dino style animation widget (Qt, standalone)
#
# 백업 상태 표시 자리에 쓰는 픽셀아트 T-Rex(Chrome Dino).
#   - set_running(True): 제자리 달리기(다리 2프레임 교차) + 바닥 점선 스크롤 +
#     주기적 점프.
#   - set_running(False): 가만히 서 있음(정지).
#   - hop(): 1회 점프 트리거(작은 강조용).
#   - spin(): 공중에서 360° 1회전(파일이 실제로 백업된 순간을 또렷이 알린다).
# 외부 에셋 없이 코드 내장 비트맵을 QPainter 로 그린다(테마 무관, exe 번들 불필요).

import math

from Framework.qt.qt import (
    QWidget,
    QTimer,
    QPainter,
    QColor,
    QSize,
    Qt,
)

# 픽셀아트 비트맵('#' = 채움). 머리는 오른쪽, 꼬리는 왼쪽을 향한다.
# 다리(아래 5줄)만 프레임마다 바뀐다 → BODY + LEGS_* 조합.
_BODY = [
    "            ########",
    "            # ######",   # 눈: 13열 공백
    "            ########",
    "            ###     ",
    "            ########",   # 아래턱
    "            ###     ",
    "#           ###     ",   # 꼬리끝(0열) + 목
    "##          ####    ",
    "###        #####    ",
    "####      ######    ",
    "#####    #######    ",
    "################### ",   # 등
    " #################  ",
    "  ###############   ",
    "   #############    ",
    "    ##########      ",   # 배
]

_LEGS_STAND = [
    "    ###  ###        ",
    "    ##   ###        ",
    "    ##   ###        ",
    "    #     ##        ",
    "   ##     ##        ",
]

# 달리기 A: 앞다리 내림 / 뒷다리 올림
_LEGS_RUN_A = [
    "    ###  ###        ",
    "    ##   ###        ",
    "    ##   ###        ",
    "         ##         ",
    "         ##         ",
]

# 달리기 B: 앞다리 올림 / 뒷다리 내림
_LEGS_RUN_B = [
    "    ###  ###        ",
    "    ##   ###        ",
    "    ##   ###        ",
    "    ##              ",
    "    ##              ",
]

# 점프: 두 다리 모음(짧게)
_LEGS_JUMP = [
    "    ###  ###        ",
    "    ##   ###        ",
    "    ###  ##         ",
    "     #   #          ",
    "                    ",
]

_GRID_W = 20
_GRID_H = len(_BODY) + len(_LEGS_STAND)   # 21

# 스프라이트를 중심 기준으로 360° 회전시키면 대각선만큼의 공간이 필요하다.
# (회전 중 모서리가 위젯 밖으로 잘리지 않도록 세로 여유를 이 값으로 확보한다.)
_DIAG_CELLS = math.hypot(_GRID_W, _GRID_H)        # ≈ 29.0 칸
_RESERVE_CELLS = int(math.ceil(_DIAG_CELLS)) + 4  # 회전 여유 포함 세로 칸수


class DinoWidget(QWidget):

    def __init__(self, px=3, parent=None):
        super().__init__(parent)

        self._px = px                 # 픽셀 1칸 크기
        self._running = False
        self._leg = 0                 # 0/1 달리기 다리 프레임
        self._ground_scroll = 0       # 바닥 점선 위치

        # 점프 상태: None=땅, 아니면 0..(_JUMP_TICKS) 진행 틱
        self._jump_t = None
        self._ticks_since_jump = 0

        # 360° 회전 상태: None=안 함, 아니면 0..(_SPIN_TICKS) 진행 틱.
        # 백업이 실제로 일어난 순간 spin() 으로 트리거한다.
        self._spin_t = None

        # 애니메이션 타이머(~33fps)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)

        self._frame_count = 0

        h = _RESERVE_CELLS * self._px  # 점프/회전 여유 포함 높이
        self.setMinimumHeight(h)
        self.setMinimumWidth(_GRID_W * self._px + 40)

    # 점프 1회 길이(틱)와 자동 점프 주기(틱). 33ms 기준.
    _JUMP_TICKS = 18          # ~0.6s
    _JUMP_PEAK_CELLS = 7      # 점프 높이(픽셀 칸)
    _AUTO_JUMP_PERIOD = 78    # ~2.6s 마다 자동 점프
    _LEG_SWAP_EVERY = 4       # 다리 교체 간격(틱) → ~7.5fps

    # 360° 회전(백업 성공 강조)
    _SPIN_TICKS = 24          # ~0.8s 동안 한 바퀴
    _SPIN_LIFT_CELLS = 4      # 회전하며 살짝 떠오르는 높이(픽셀 칸)

    # --------------------------------------------------------------- control

    def set_running(self, on):
        on = bool(on)
        if on == self._running:
            return
        self._running = on
        if on:
            self._ticks_since_jump = 0
            self._timer.start()
        else:
            self._timer.stop()
            self._jump_t = None
            self._spin_t = None
            self._leg = 0
        self.update()

    def hop(self):
        """점프 1회 트리거(이미 점프/회전 중이면 무시). 달리는 중에만 의미 있음."""
        if self._running and self._jump_t is None and self._spin_t is None:
            self._jump_t = 0
            self._ticks_since_jump = 0

    def spin(self):
        """공중에서 360° 1회전(백업 성공 강조). 정지 상태면 먼저 달리기로 깨운다.
        이미 회전 중이어도 처음부터 다시 돌려, 연속 백업마다 또렷이 표시한다."""
        if not self._running:
            self.set_running(True)
        self._spin_t = 0
        self._jump_t = None
        self._ticks_since_jump = 0

    # ------------------------------------------------------------- animation

    def _tick(self):
        self._frame_count += 1

        # 바닥 점선 스크롤
        self._ground_scroll = (self._ground_scroll + 2) % (self._px * 6)

        # 다리 교체(점프 중엔 다리 모음이라 무관)
        if self._frame_count % self._LEG_SWAP_EVERY == 0:
            self._leg ^= 1

        # 회전 진행(회전 중엔 일반 점프/자동 점프를 멈춘다)
        if self._spin_t is not None:
            self._spin_t += 1
            if self._spin_t >= self._SPIN_TICKS:
                self._spin_t = None
                self._ticks_since_jump = 0
        # 점프 진행 / 자동 점프 스케줄
        elif self._jump_t is not None:
            self._jump_t += 1
            if self._jump_t >= self._JUMP_TICKS:
                self._jump_t = None
        else:
            self._ticks_since_jump += 1
            if self._ticks_since_jump >= self._AUTO_JUMP_PERIOD:
                self._jump_t = 0
                self._ticks_since_jump = 0

        self.update()

    def _jump_offset_px(self):
        """현재 점프의 세로 오프셋(px, 위로 +). 포물선."""
        if self._jump_t is None:
            return 0
        x = self._jump_t / float(self._JUMP_TICKS)   # 0..1
        arc = 4.0 * x * (1.0 - x)                     # 0..1..0 (x=0.5 정점)
        return int(self._JUMP_PEAK_CELLS * self._px * arc)

    # ----------------------------------------------------------------- paint

    def sizeHint(self):
        return QSize(_GRID_W * self._px + 60, _RESERVE_CELLS * self._px)

    def _current_legs(self):
        if self._jump_t is not None:
            return _LEGS_JUMP
        if self._running:
            return _LEGS_RUN_A if self._leg == 0 else _LEGS_RUN_B
        return _LEGS_STAND

    def paintEvent(self, event):
        painter = QPainter(self)
        px = self._px

        color = self.palette().windowText().color()
        if not color.isValid():
            color = QColor("#535353")

        w = self.width()
        h = self.height()

        sprite_w = _GRID_W * px
        sprite_h = _GRID_H * px

        # 바닥선 y(스프라이트 발이 닿는 위치). 위젯 하단에서 약간 띄움.
        ground_y = h - 6 * px

        # 스프라이트 좌측 x(살짝 왼쪽에 배치)
        sprite_x = max(8, (w - sprite_w) // 4)
        # 발이 ground_y 에 닿도록 top 계산 + 점프 오프셋
        sprite_top = ground_y - sprite_h - self._jump_offset_px()

        # --- 바닥선 + 점선(흐름) ---
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(0, ground_y, w, max(1, px // 2))
        dash_w = px * 3
        gap = px * 6
        start = -self._ground_scroll
        x = start
        dash_y = ground_y + 2 * px
        while x < w:
            painter.drawRect(int(x), dash_y, dash_w, max(1, px // 2))
            x += gap

        # --- 공룡 ---
        if self._spin_t is not None:
            # 공중에서 360° 회전(백업 성공 강조). 중심 기준으로 회전하며 살짝 떠오른다.
            p = self._spin_t / float(self._SPIN_TICKS)   # 0..1
            arc = 4.0 * p * (1.0 - p)                     # 0..1..0 (p=0.5 정점)
            lift = self._SPIN_LIFT_CELLS * px * arc
            angle = 360.0 * p

            cx = sprite_x + sprite_w / 2.0
            cy = sprite_top + sprite_h / 2.0 - lift
            # 회전 시 모서리가 잘리지 않게 중심을 위젯 안(대각선 반지름만큼 여유)으로 클램프.
            half_diag = 0.5 * math.hypot(sprite_w, sprite_h)
            cx = min(max(cx, half_diag + 1), w - half_diag - 1)
            cy = min(max(cy, half_diag + 1), h - half_diag - 1)

            painter.save()
            painter.translate(cx, cy)
            painter.rotate(angle)
            rows = _BODY + _LEGS_JUMP   # 회전 중엔 다리를 모은 점프 포즈
            for r, line in enumerate(rows):
                for c, ch in enumerate(line):
                    if ch == "#":
                        painter.fillRect(
                            int(round(c * px - sprite_w / 2.0)),
                            int(round(r * px - sprite_h / 2.0)),
                            px, px,
                            color,
                        )
            painter.restore()
        else:
            rows = _BODY + self._current_legs()
            for r, line in enumerate(rows):
                for c, ch in enumerate(line):
                    if ch == "#":
                        painter.fillRect(
                            sprite_x + c * px,
                            sprite_top + r * px,
                            px, px,
                            color,
                        )

        painter.end()
