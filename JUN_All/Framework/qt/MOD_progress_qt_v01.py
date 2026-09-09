# -*- coding: utf-8 -*-
"""
JUN_mod_progress_qt_v01 - 재사용 PySide 진행률 팝업(모달 게이지 창).

오래 걸리는 작업(Apply / Bake / 씬 샘플링)이 도는 동안 **아무 안내 없이 창이 멎어 있는 것**을
막는다. 0~100% 게이지 + 현재 단계 이름 + 세부 메시지 + 경과 시간을 모달 팝업으로 띄운다.

왜 위젯을 따로 두는가
--------------------
DemBone(A00430)은 메인 창에 붙은 QProgressBar, Wrapper(A00420)는 로그 줄로 진행을 알렸다.
"작업 도는 동안 뜨는 팝업" 은 모든 무거운 툴에 똑같이 필요하므로 `MOD_tsl_qt_v01` /
`MOD_timeRange_qt_v01` 처럼 공용 위젯으로 승격했다.

단계(phase) 가중치
-----------------
한 작업은 보통 비용이 다른 여러 단계로 나뉜다(샘플링 45% / 솔브 15% / 기록 40% 처럼).
단계 목록을 넘겨 두면 각 단계 안에서는 **0~1 상대 진행만** 보고하면 되고, 전체 퍼센트
환산은 위젯이 한다. 실제로 돌지 않는 단계(캐시 재사용 등)는 목록에서 빼면 나머지 가중치가
**자동으로 재정규화**되므로 게이지가 중간에서 멈추거나 건너뛰지 않는다.

콜백 규약 (core 쪽이 부르는 것)
------------------------------
    progress(done, total, message=None)

**현재 단계 안에서의** 상대 진행이다. core 는 이 위젯을 몰라도 되고(그냥 콜백),
콜백이 `None` 이면 아무 일도 하지 않는다 — 즉 진행 표시 없이도 같은 코드가 돈다.

쓰는 법
------
    dlg = JUN_mod_progress_qt_v01(
        self, title="Apply",
        phases=[("Sampling scene", 45), ("Solving chains", 15), ("Writing keys", 40)])
    dlg.start()
    try:
        dlg.begin_phase()                      # 1단계
        core.sample(..., progress=dlg.callback())
        dlg.begin_phase()                      # 2단계
        core.solve(..., progress=dlg.callback())
        dlg.begin_phase()                      # 3단계
        core.write(..., progress=dlg.callback())
    finally:
        dlg.finish()

갱신 비용
--------
`setKeyframe` 을 수천 번 도는 루프에서 매번 `processEvents()` 를 부르면 **그리는 쪽이 더
비싸다**. 그래서 게이지 값은 늘 반영하되(`setValue` 는 다시 그리기를 예약만 한다),
실제로 화면을 갱신하는 `processEvents()` 만 `_MIN_INTERVAL` 간격으로 묶는다.
값까지 건너뛰면 갱신이 뚝 끊긴 순간의 퍼센트가 화면에 안 올라간 채 남는다.

취소
----
`cancellable=True` 면 Cancel 버튼이 생기고 `was_cancelled()` 가 True 가 된다. **중단
지점이 안전한 작업에만** 켤 것 — 씬을 반쯤 고쳐 놓고 멈추면 안 되는 작업은 기본값(False)
그대로 두고 창을 닫지도 못하게 둔다(닫기 버튼 없음, Esc 무시).
"""

import time

from Framework.qt.qt import *


# 다시 그리는 최소 간격(초). 이보다 자주 오는 갱신은 값만 반영하고 그리지 않는다.
_MIN_INTERVAL = 0.03

# 게이지 색은 툴 테마(qss)를 타지만, 홈이 배경에 묻히는 coral_dark 대비용으로 직접 그린다.
PROGRESS_STYLE = """
QProgressBar {
    border: 1px solid #1e1e1e; border-radius: 3px; background: #2b2b2b;
    height: 18px; text-align: center; color: #e6e6e6;
}
QProgressBar::chunk {
    background: #d08778; border-radius: 2px;
}
"""


class JUN_mod_progress_qt_v01(QDialog):
    """0~100% 게이지를 띄우는 모달 진행률 팝업."""

    def __init__(self, parent=None, title="Progress", message="",
                 phases=None, width=400, cancellable=False):
        super(JUN_mod_progress_qt_v01, self).__init__(parent)

        self._cancellable = bool(cancellable)
        self._cancelled = False

        self._phases = []      # [(label, weight), ...]
        self._bounds = []      # [(base, span), ...] 0~1 로 정규화된 단계 구간
        self._index = -1       # 현재 단계 인덱스(-1 = 시작 전)

        self._fraction = 0.0
        self._percent = -1
        self._last_draw = 0.0
        self._t0 = time.time()

        self._build_ui(title, message, width)
        self.set_phases(phases or [])

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self, title, message, width):
        self.setWindowTitle(title)
        # 닫기 버튼을 없앤다 — 작업 도중 창을 닫아도 작업은 멈추지 않기 때문에,
        # 멈춘 것처럼 보이는 상태를 아예 만들지 않는다.
        flags = Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        self.setWindowFlags(flags)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(int(width))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        self.lbl_phase = QLabel(message or title)
        f = self.lbl_phase.font()
        f.setBold(True)
        self.lbl_phase.setFont(f)
        lay.addWidget(self.lbl_phase)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        self.bar.setStyleSheet(PROGRESS_STYLE)
        lay.addWidget(self.bar)

        info = QHBoxLayout()
        self.lbl_detail = QLabel("")
        self.lbl_detail.setWordWrap(False)
        info.addWidget(self.lbl_detail, 1)
        self.lbl_time = QLabel("0.0s")
        info.addWidget(self.lbl_time, 0, Qt.AlignRight)
        lay.addLayout(info)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_cancel.setVisible(self._cancellable)
        lay.addWidget(self.btn_cancel, 0, Qt.AlignRight)

    # ==================================================================
    # 단계
    # ==================================================================

    def set_phases(self, phases):
        """단계 목록 지정. `[(label, weight), ...]` 또는 `[label, ...]`(균등 가중치).

        가중치는 합이 얼마든 상관없이 **비율로만** 쓰인다(45/15/40 처럼 써도 되고
        0.45/0.15/0.4 여도 같다). 돌지 않는 단계는 애초에 목록에서 빼면 된다.
        """
        norm = []
        for p in phases or []:
            if isinstance(p, (tuple, list)):
                label = p[0]
                weight = float(p[1]) if len(p) > 1 else 1.0
            else:
                label, weight = p, 1.0
            norm.append((str(label), max(0.0, weight)))

        total = sum(w for _, w in norm)
        if total <= 0.0:
            norm = [(lbl, 1.0) for lbl, _ in norm]
            total = float(len(norm)) or 1.0

        self._phases = norm
        self._bounds = []
        base = 0.0
        for _, w in norm:
            span = w / total
            self._bounds.append((base, span))
            base += span
        self._index = -1

    def begin_phase(self, label=None, index=None):
        """다음 단계로 넘어간다(`index` 를 주면 그 단계로). 게이지는 단계 시작점으로."""
        if index is None:
            self._index += 1
        else:
            self._index = int(index)

        if label is not None and 0 <= self._index < len(self._phases):
            weight = self._phases[self._index][1]
            self._phases[self._index] = (str(label), weight)

        text = label
        if text is None and 0 <= self._index < len(self._phases):
            text = self._phases[self._index][0]
        if text:
            self.lbl_phase.setText(text)
        self.lbl_detail.setText("")

        base, _ = self._window()
        self.set_fraction(base, force=True)

    def skip_phase(self):
        """현재 단계를 돌지 않고 건너뛴다(게이지는 그 단계 끝까지 채운다)."""
        self._index += 1
        base, span = self._window()
        self.set_fraction(base + span, force=True)

    def _window(self):
        """현재 단계의 (시작, 폭). 단계 목록이 없으면 전체 구간."""
        if 0 <= self._index < len(self._bounds):
            return self._bounds[self._index]
        return (0.0, 1.0)

    # ==================================================================
    # 진행 보고
    # ==================================================================

    def step(self, done, total, message=None):
        """현재 단계 안에서의 진행. `total` 이 0 이면 단계 끝으로 본다."""
        total = float(total or 0.0)
        local = 1.0 if total <= 0.0 else max(0.0, min(1.0, float(done) / total))
        base, span = self._window()
        self.set_fraction(base + span * local, message)

    def set_fraction(self, fraction, message=None, force=False):
        """전체 진행(0.0~1.0)을 직접 지정한다."""
        self._fraction = max(0.0, min(1.0, float(fraction)))
        if message is not None:
            self.lbl_detail.setText(str(message))
        self._draw(force=force)

    def set_message(self, text):
        self.lbl_detail.setText(str(text))
        self._draw(force=True)

    def callback(self):
        """core 에 넘길 `progress(done, total, message=None)` 콜백."""
        def _progress(done, total, message=None):
            self.step(done, total, message)
        return _progress

    def _draw(self, force=False):
        """게이지 값은 **항상** 반영하고, 실제로 다시 그리는 것만 제한한다.

        `setValue` 자체는 다시 그리기를 예약만 하므로 싸다. 비싼 것은
        `processEvents()` 라서 그쪽만 간격으로 묶는다. 값까지 건너뛰면 갱신이 뚝
        끊긴 순간의 퍼센트가 화면에 영영 안 올라가는 경우가 생긴다.
        """
        percent = int(round(self._fraction * 100.0))
        now = time.time()

        if percent != self._percent:
            self._percent = percent
            self.bar.setValue(percent)

        if not force and (now - self._last_draw) < _MIN_INTERVAL:
            return

        self._last_draw = now
        self.lbl_time.setText("{0:.1f}s".format(now - self._t0))
        QApplication.processEvents()

    # ==================================================================
    # 수명
    # ==================================================================

    def start(self):
        """팝업을 띄운다(모달, 블로킹하지 않음 — 호출자가 계속 일한다)."""
        self._t0 = time.time()
        self._cancelled = False
        self.show()
        self.raise_()
        QApplication.processEvents()
        return self

    def finish(self):
        """작업이 끝났다(성공/실패 무관). 팝업을 닫는다."""
        self._fraction = 1.0
        try:
            self.bar.setValue(100)
            QApplication.processEvents()
        except Exception:
            pass
        self.close()
        self.deleteLater()

    def elapsed(self):
        """시작 후 경과 시간(초)."""
        return time.time() - self._t0

    # ==================================================================
    # 취소
    # ==================================================================

    def was_cancelled(self):
        return self._cancelled

    def _on_cancel(self):
        self._cancelled = True
        self.btn_cancel.setEnabled(False)
        self.lbl_detail.setText("Cancelling...")
        QApplication.processEvents()

    def keyPressEvent(self, event):
        # Esc 로 조용히 닫히면 작업은 계속 도는데 창만 사라진다 — 막는다.
        if event.key() == Qt.Key_Escape:
            if self._cancellable:
                self._on_cancel()
            event.accept()
            return
        super(JUN_mod_progress_qt_v01, self).keyPressEvent(event)

    def closeEvent(self, event):
        super(JUN_mod_progress_qt_v01, self).closeEvent(event)
