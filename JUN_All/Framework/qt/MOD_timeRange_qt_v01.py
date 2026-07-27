# -*- coding: utf-8 -*-
"""
JUN_mod_timeRange_qt_v01 - 재사용 PySide 시간 구간(Start/End) 입력 위젯.

A00110_animTool 의 여러 탭(Move Keys / Stagger / Copy / Mirror / Bake / Follow)에서
반복되던 `Start [값][Get Current]  End [값][Get Current]  [Get Sel Range]` UI 를 하나의
위젯으로 승격한 것. MOD_tsl_qt_v01(JUN_mod_tsl_qt) 처럼 여러 툴에서 공용으로 쓴다.

구성 (한 줄):
    Start [QLineEdit] [Get Current]   End [QLineEdit] [Get Current]   [Get Sel Range]

  - **Get Current**  : 현재 Maya 프레임(`currentTime`)으로 그 칸 하나를 채운다(칸마다 하나).
  - **Get Sel Range**: 지금 **선택한 키프레임들 중 제일 앞/뒤 프레임**을 찾아 Start·End
    **두 칸을 함께** 채운다(예: 어떤 커브의 6~15f 키 선택 후 누르면 Start=6, End=15).

두 버튼 모두 `show_get_current` / `show_sel_range` 로 개별 표시 제어한다.

Maya 밖에서도 import / 위젯 생성이 되도록 maya.cmds 는 메서드 안에서 lazy import 하고,
Maya 가 없거나 호출이 실패하면 조용히 무시한다(로그 콜백이 있으면 안내).

값 접근
------
`start()` / `end()` 는 정수(파싱 실패 시 None), `values()` 는 (start, end) 또는 None.
`set_start` / `set_end` / `set_range` 로 값을 넣는다. 내부 QLineEdit 은 `start_edit` /
`end_edit` 로 노출하므로, 기존 코드가 하던 `.text()` / `.setText()` / `.setValidator()` /
`.setPlaceholderText()` 도 그대로 쓸 수 있다(마이그레이션 편의).

값이 사용자 입력이나 버튼으로 바뀌면 `changed` 시그널을 방출한다.
"""

from Framework.qt.qt import *


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


class JUN_mod_timeRange_qt_v01(QWidget):

    # 값이 (편집/버튼으로) 바뀌면 방출. 부모가 받아 후속 처리 가능.
    changed = Signal()

    def __init__(self, start_label="Start", end_label="End",
                 start_value=None, end_value=None,
                 start_placeholder="", end_placeholder="",
                 show_get_current=True, show_sel_range=True,
                 min_value=-1000000, max_value=1000000,
                 log_callback=None, parent=None):
        super(JUN_mod_timeRange_qt_v01, self).__init__(parent)

        self.start_label = start_label
        self.end_label = end_label
        self.show_get_current = show_get_current
        self.show_sel_range = show_sel_range
        self.min_value = min_value
        self.max_value = max_value
        # 안내 메시지 콜백. None 이면 print(툴 로그창에 연결 가능).
        self.log_callback = log_callback

        # setEnabled 로 껐다 켜야 하는 입력 위젯들(라벨 제외)을 모아둔다.
        self._input_widgets = []

        self._build_ui(start_value, end_value, start_placeholder, end_placeholder)

    # ================================================================
    # UI 구성
    # ================================================================

    def _build_ui(self, start_value, end_value, start_ph, end_ph):
        # 예전(각 QLineEdit 이 행에서 늘어나던) 모습을 유지하도록 위젯 자체가 가로로
        # 늘어나게 둔다(부모 행에 함께 놓인 다른 위젯과 공간을 나눠 가진다).
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        validator = QIntValidator(self.min_value, self.max_value, self)

        # --- Start ---
        row.addWidget(QLabel(self.start_label))
        self.start_edit = QLineEdit()
        self.start_edit.setValidator(validator)
        if start_ph:
            self.start_edit.setPlaceholderText(str(start_ph))
        if start_value is not None:
            self.start_edit.setText(str(start_value))
        self.start_edit.editingFinished.connect(self.changed.emit)
        row.addWidget(self.start_edit)
        self._input_widgets.append(self.start_edit)
        if self.show_get_current:
            row.addWidget(self._make_get_current_btn(self.start_edit))

        # --- End ---
        row.addWidget(QLabel(self.end_label))
        self.end_edit = QLineEdit()
        self.end_edit.setValidator(validator)
        if end_ph:
            self.end_edit.setPlaceholderText(str(end_ph))
        if end_value is not None:
            self.end_edit.setText(str(end_value))
        self.end_edit.editingFinished.connect(self.changed.emit)
        row.addWidget(self.end_edit)
        self._input_widgets.append(self.end_edit)
        if self.show_get_current:
            row.addWidget(self._make_get_current_btn(self.end_edit))

        # --- Get Sel Range (두 칸 함께 채움) ---
        if self.show_sel_range:
            btn = QPushButton("Get Sel Range")
            btn.setToolTip("Fill Start/End from the first and last selected keyframe")
            # clicked 는 checked(bool) 를 슬롯에 넘기므로 *_a 로 흡수한다(안 그러면
            # 위치 인자를 덮어써 오작동).
            btn.clicked.connect(lambda *_a: self.get_selected_range())
            row.addWidget(btn)
            self._input_widgets.append(btn)

    def _make_get_current_btn(self, line_edit):
        """현재 프레임으로 line_edit 하나를 채우는 'Get Current' 버튼."""
        btn = QPushButton("Get Current")
        # clicked 의 checked(bool) 인자를 *_a 로 흡수(그러지 않으면 le 를 덮어씀).
        btn.clicked.connect(
            lambda *_a, le=line_edit: self._set_current_frame(le))
        self._input_widgets.append(btn)
        return btn

    # ================================================================
    # 공개 API — 값 읽기/쓰기
    # ================================================================

    def start_text(self):
        return self.start_edit.text().strip()

    def end_text(self):
        return self.end_edit.text().strip()

    def start(self):
        """Start 값(int). 비었거나 파싱 실패면 None."""
        return self._as_int(self.start_text())

    def end(self):
        """End 값(int). 비었거나 파싱 실패면 None."""
        return self._as_int(self.end_text())

    def values(self):
        """(start, end) 튜플. 둘 중 하나라도 유효하지 않으면 None."""
        s, e = self.start(), self.end()
        if s is None or e is None:
            return None
        return s, e

    def set_start(self, value):
        self.start_edit.setText("" if value is None else str(value))
        self.changed.emit()

    def set_end(self, value):
        self.end_edit.setText("" if value is None else str(value))
        self.changed.emit()

    def set_range(self, start, end):
        self.start_edit.setText("" if start is None else str(start))
        self.end_edit.setText("" if end is None else str(end))
        self.changed.emit()

    def clear(self):
        self.start_edit.clear()
        self.end_edit.clear()
        self.changed.emit()

    def set_inputs_enabled(self, enabled):
        """입력 칸/버튼을 함께 켜고 끈다(라벨은 그대로). 예: Bake 의 Custom 모드 전용."""
        for w in self._input_widgets:
            w.setEnabled(bool(enabled))

    # ================================================================
    # 공개 API — Maya 연동 동작(프로그램에서도 호출 가능)
    # ================================================================

    def get_current_start(self):
        """Start 를 현재 프레임으로 채운다."""
        self._set_current_frame(self.start_edit)

    def get_current_end(self):
        """End 를 현재 프레임으로 채운다."""
        self._set_current_frame(self.end_edit)

    def selected_key_range(self):
        """선택된 키프레임들의 (최소, 최대) 프레임(int). 선택 키가 없으면 None.

        `cmds.keyframe(q=True, sl=True)` 는 그래프 에디터/타임슬라이더에서 선택된 모든
        키의 시간을 오브젝트·어트리뷰트에 무관하게 전역으로 돌려준다(여러 커브에 걸쳐
        선택해도 전체의 앞/뒤를 잡는다).
        """
        cmds = _cmds()
        if cmds is None:
            return None
        try:
            times = cmds.keyframe(query=True, selected=True) or []
        except Exception:
            return None
        if not times:
            return None
        return int(round(min(times))), int(round(max(times)))

    def get_selected_range(self):
        """선택 키의 앞/뒤 프레임으로 Start·End 두 칸을 함께 채운다. 채웠으면 (s,e), 아니면 None."""
        rng = self.selected_key_range()
        if rng is None:
            self._log("[Warning] No keyframes selected. "
                      "Select keys in the Graph Editor / Time Slider first.")
            return None
        self.set_range(rng[0], rng[1])
        return rng

    # ================================================================
    # 내부 헬퍼
    # ================================================================

    def _set_current_frame(self, line_edit):
        cmds = _cmds()
        if cmds is None:
            return
        try:
            frame = int(round(cmds.currentTime(query=True)))
        except Exception:
            return
        line_edit.setText(str(frame))
        self.changed.emit()

    @staticmethod
    def _as_int(text):
        if not text:
            return None
        try:
            return int(round(float(text)))
        except ValueError:
            return None

    def _log(self, message):
        if callable(self.log_callback):
            self.log_callback(message)
        else:
            print(message)
