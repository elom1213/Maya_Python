# -*- coding: utf-8 -*-
"""
JUN_mod_viewZoom_qt_v01 - 리스트 · 트리 · 표(QAbstractItemView)를 확대 / 축소하는 공용 기능.

A00110_animTool_V02 View > Layers 에서 "행이 낮아 고르기 어렵고 Mute 체크박스가 작다" 는 요청으로 만들었다
(v02.38, 2026-11-04). 툴마다 행 높이를 따로 박는 대신, 뷰 하나에 이 객체를 붙이면 확대 배율 하나로
**글자 · 행 높이 · 체크박스 · 트리 들여쓰기**가 함께 커지고 작아진다.

    zoom = JUN_mod_viewZoom_qt_v01(tree, key="A00110/layers", default=1.5)
    row_layout.addWidget(zoom.controls())          # [-] 150% [+]  (선택)

- **Ctrl + 마우스 휠** (뷰 위에서) 로 확대 / 축소. `controls()` 의 `-` / `+`, 퍼센트 글자 클릭 = 기본 배율로.
- **체크박스를 직접 그린다** — 아이템 뷰의 체크박스는 스타일(마야 안이면 마야 스타일)이 고정 크기(13px)로 그려
  qss 로도 키울 수 없다. 델리게이트가 배율만큼 큰 체크박스를 팔레트 색으로 그린다.
- **칸 어디를 눌러도 체크가 바뀐다**(`whole_cell_toggle`, 기본 켬) — 텍스트 없는 체크 칸(예: Mute 열)은 칸 전체가 누름 영역.
  기본 델리게이트처럼 체크 영역의 누름은 행 선택을 바꾸지 않는다. Space 키도 체크를 바꾼다(현재 칸).
- 배율은 `key` 가 있으면 QSettings(`JUN/viewZoom`)에 기억해 다음 실행 때 되살린다.
- 뷰에 이미 다른 델리게이트가 있으면 덮어쓰므로, 커스텀 델리게이트를 쓰는 뷰에는 붙이지 말 것.

이름이 있는 아이템 글꼴(예: 굵은 글씨 = 활성 레이어)도 같은 배율로 키운다(굵기 · 기울임은 그대로).
"""

from Framework.qt.qt import *


SETTINGS_ORG = "JUN"
SETTINGS_APP = "viewZoom"

BASE_ROW = 20          # 배율 1.0 의 최소 행 높이(px)
BASE_INDICATOR = 13    # 배율 1.0 의 체크박스 한 변(px) - 마야 · Fusion 기본과 같은 크기
INDICATOR_MARGIN = 4


def _enum_value(v):
    """PySide6 enum / PySide2 int 를 int 로."""
    return getattr(v, "value", v)


def font_px_of(font, widget=None):
    """QFont 의 글자 크기(px). 스타일시트 `font-size: Npx` 는 pixelSize, 포인트 글꼴은 DPI 로 환산.
    (QFontInfo 는 오프스크린 등에서 -1 을 줄 수 있어 쓰지 않는다)"""
    if font.pixelSize() > 0:
        return font.pixelSize()
    pt = font.pointSizeF()
    if pt <= 0:
        return 0
    dpi = widget.logicalDpiY() if widget is not None else 96
    return int(round(pt * dpi / 72.0))


def _check_state(index):
    """체크 칸이면 Qt.CheckState int(0/1/2), 아니면 None."""
    data = index.data(Qt.CheckStateRole)
    if data is None:
        return None
    return int(_enum_value(data))


class _ZoomDelegate(QStyledItemDelegate):
    """배율만큼 행을 높이고, 체크박스를 크게 직접 그리고, 칸 전체를 체크 누름 영역으로 쓰는 델리게이트."""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self._owner = owner

    # ------------------------------------------------------------------ 치수

    def _scale(self):
        return self._owner.scale()

    def indicator_size(self):
        return max(8, int(round(BASE_INDICATOR * self._scale())))

    def _indicator_rect(self, option, index):
        """체크박스 사각형 - 텍스트가 없는 칸은 가운데, 있으면 왼쪽."""
        size = self.indicator_size()
        r = option.rect
        has_text = bool(index.data(Qt.DisplayRole))
        if has_text:
            x = r.left() + INDICATOR_MARGIN
        else:
            x = r.left() + (r.width() - size) // 2
        y = r.top() + (r.height() - size) // 2
        return QRect(x, y, size, size)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # 아이템이 글꼴을 직접 가진 경우(굵게 등)도 배율 크기로 - 뷰 글꼴만 키우면 그런 칸은 그대로 남는다.
        if index.data(Qt.FontRole) is not None:
            f = QFont(option.font)
            f.setPixelSize(self._owner.font_px())
            option.font = f

    def sizeHint(self, option, index):
        hint = super().sizeHint(option, index)
        h = max(hint.height(), int(round(BASE_ROW * self._scale())))
        w = hint.width()
        if _check_state(index) is not None:
            w = max(w, self.indicator_size() + INDICATOR_MARGIN * 2 + (hint.width() if index.data(Qt.DisplayRole) else 0))
        return QSize(w, h)

    # ------------------------------------------------------------------ 그리기

    def paint(self, painter, option, index):
        state = _check_state(index)
        if state is None:
            super().paint(painter, option, index)
            return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        # 스타일의 작은 체크박스는 빼고 배경 · 선택 · 텍스트만 그린다.
        opt.features = opt.features & ~QStyleOptionViewItem.HasCheckIndicator
        ind = self._indicator_rect(option, index)
        if opt.text:
            opt.rect = QRect(opt.rect)
            # 배경은 칸 전체 - 먼저 텍스트 없이 칸 전체를 그리고, 텍스트는 체크박스 오른쪽에.
            bg = QStyleOptionViewItem(opt)
            bg.text = ""
            style = opt.widget.style() if opt.widget else QApplication.style()
            style.drawControl(QStyle.CE_ItemViewItem, bg, painter, opt.widget)
            opt.rect.setLeft(ind.right() + INDICATOR_MARGIN)
            opt.backgroundBrush = QBrush()
            style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
        else:
            style = opt.widget.style() if opt.widget else QApplication.style()
            style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
        enabled = bool(opt.state & QStyle.State_Enabled) and bool(index.flags() & Qt.ItemIsEnabled)
        self._draw_indicator(painter, ind, state, opt.palette, enabled)

    @staticmethod
    def _draw_indicator(painter, rect, state, palette, enabled):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = max(2.0, rect.width() * 0.18)
        border = QColor(palette.color(QPalette.Text))
        border.setAlpha(170 if enabled else 70)
        fill = QColor(palette.color(QPalette.Highlight))
        if not enabled:
            fill.setAlpha(90)
        pen_w = max(1.0, rect.width() / 13.0)
        if state == 2:            # Checked
            painter.setPen(QPen(fill, pen_w))
            painter.setBrush(fill)
            painter.drawRoundedRect(r, radius, radius)
            mark = QColor(palette.color(QPalette.HighlightedText))
            if not enabled:
                mark.setAlpha(120)
            painter.setPen(QPen(mark, max(1.6, rect.width() / 7.0), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            w, h, x, y = r.width(), r.height(), r.left(), r.top()
            path = QPainterPath(QPointF(x + w * 0.22, y + h * 0.52))
            path.lineTo(QPointF(x + w * 0.42, y + h * 0.72))
            path.lineTo(QPointF(x + w * 0.78, y + h * 0.30))
            painter.drawPath(path)
        else:
            painter.setPen(QPen(border, pen_w))
            painter.setBrush(QColor(palette.color(QPalette.Base)))
            painter.drawRoundedRect(r, radius, radius)
            if state == 1:        # PartiallyChecked
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill)
                inset = r.width() * 0.28
                painter.drawRoundedRect(r.adjusted(inset, inset, -inset, -inset), radius / 2, radius / 2)
        painter.restore()

    # ------------------------------------------------------------------ 누름

    def _hit(self, option, index, pos):
        if self._owner.whole_cell_toggle and not index.data(Qt.DisplayRole):
            return option.rect.contains(pos)
        return self._indicator_rect(option, index).adjusted(-3, -3, 3, 3).contains(pos)

    def editorEvent(self, event, model, option, index):
        state = _check_state(index)
        flags = index.flags()
        if state is None or not (flags & Qt.ItemIsUserCheckable) or not (flags & Qt.ItemIsEnabled):
            return super().editorEvent(event, model, option, index)
        etype = event.type()
        if etype in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.MouseButtonRelease):
            if event.button() != Qt.LeftButton:
                return False
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if not self._hit(option, index, pos):
                return False
            if etype != QEvent.MouseButtonRelease:
                return True               # 누름 · 더블클릭은 삼킨다 - 행 선택이 바뀌지 않게(기본 델리게이트와 같음)
        elif etype == QEvent.KeyPress:
            if event.key() not in (Qt.Key_Space, Qt.Key_Select):
                return False
        else:
            return False
        if flags & Qt.ItemIsUserTristate:
            new = (state + 1) % 3
        else:
            new = 0 if state == 2 else 2
        return model.setData(index, Qt.CheckState(new), Qt.CheckStateRole)


class JUN_mod_viewZoom_qt_v01(QObject):
    """아이템 뷰 하나의 확대 배율. 글자 · 행 높이 · 체크박스 · 들여쓰기를 함께 바꾼다."""

    scale_changed = Signal(float)

    def __init__(self, view, key=None, default=1.0, minimum=0.8, maximum=3.0, step=0.1,
                 whole_cell_toggle=True, parent=None):
        super().__init__(parent or view)
        self.view = view
        self.key = key
        self.default = float(default)
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.step = float(step)
        self.whole_cell_toggle = whole_cell_toggle
        self._init_px = font_px_of(view.font(), view) or 12   # 부모가 없을 때의 기준(뷰 글꼴은 이후 이 객체가 바꾼다)
        self._own_sheet = view.styleSheet()      # 뷰가 원래 가진 스타일시트 - 글자 크기 규칙을 그 뒤에 붙인다
        self._base_indent = view.indentation() if hasattr(view, "indentation") else None
        self._labels = []
        self._scale = self.default
        self._font_px = 12
        self.delegate = _ZoomDelegate(self, view)
        view.setItemDelegate(self.delegate)
        view.viewport().installEventFilter(self)
        view.installEventFilter(self)            # Show 때 다시 적용(테마가 창을 만든 뒤에 입혀져도 기준 글자 크기를 따라간다)
        self.set_scale(self._load(), save=False)

    # ------------------------------------------------------------------ 배율

    def scale(self):
        return self._scale

    def base_font_px(self):
        """배율 1.0 의 글자 크기(px) = 부모 위젯의 글자 크기.

        뷰 자신의 글꼴은 이 객체가 스타일시트로 바꾸므로 기준이 될 수 없다. 테마 qss(`QWidget { font-size: 12px }`)가
        정한 크기는 부모도 같이 받으므로 부모 글꼴을 기준으로 삼는다."""
        ref = self.view.parentWidget()
        if ref is None:
            return self._init_px
        px = font_px_of(ref.font(), ref)
        return px if px > 0 else self._init_px

    def font_px(self):
        """지금 배율의 글자 크기(px)."""
        return self._font_px

    def set_scale(self, value, save=True):
        value = max(self.minimum, min(self.maximum, round(float(value), 2)))
        changed = abs(value - self._scale) > 1e-6
        self._scale = value
        self._apply()
        if save:
            self._save()
        for lbl in self._labels:
            lbl.setText("{0:d}%".format(int(round(value * 100))))
        if changed:
            self.scale_changed.emit(value)

    def zoom_in(self):
        self.set_scale(self._scale + self.step)

    def zoom_out(self):
        self.set_scale(self._scale - self.step)

    def reset(self):
        self.set_scale(self.default)

    def _apply(self):
        v = self.view
        # 글자 크기는 뷰 자신의 스타일시트로 - 테마 qss 의 `QWidget { font-size }` 가 setFont 를 덮기 때문.
        # 뷰 자신의 시트가 조상(창)의 시트보다 우선한다. 헤더는 뷰의 자식이라 같은 규칙을 받는다.
        self._font_px = max(6, int(round(self.base_font_px() * self._scale)))
        rule = "QAbstractItemView, QHeaderView {{ font-size: {0}px; }}".format(self._font_px)
        sheet = (self._own_sheet + "\n" + rule) if self._own_sheet else rule
        if v.styleSheet() != sheet:
            v.setStyleSheet(sheet)
        if self._base_indent is not None:
            v.setIndentation(max(8, int(round(self._base_indent * self._scale))))
        # 행 높이(sizeHint) 다시 계산
        v.scheduleDelayedItemsLayout()
        v.doItemsLayout()
        if hasattr(v, "header"):
            hdr = v.header()
            for col in range(hdr.count()):
                if _enum_value(hdr.sectionResizeMode(col)) == _enum_value(QHeaderView.ResizeToContents):
                    v.resizeColumnToContents(col)
        v.viewport().update()

    # ------------------------------------------------------------------ 저장

    def _settings(self):
        return QSettings(SETTINGS_ORG, SETTINGS_APP)

    def _load(self):
        if not self.key:
            return self.default
        try:
            value = self._settings().value(self.key)
            return float(value) if value is not None else self.default
        except (TypeError, ValueError):
            return self.default

    def _save(self):
        if self.key:
            try:
                self._settings().setValue(self.key, self._scale)
            except Exception:  # noqa: BLE001 - 기억 못 해도 동작에는 지장 없다
                pass

    # ------------------------------------------------------------------ Ctrl + 휠

    def eventFilter(self, obj, event):
        if obj is self.view:
            if event.type() == QEvent.Show:
                self._apply()                     # 테마 · 부모(Expand 창으로 옮김)가 바뀌었을 수 있다
            return False
        if event.type() == QEvent.Wheel and (event.modifiers() & Qt.ControlModifier):
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ 버튼 줄

    def controls(self, parent=None, label="Zoom"):
        """`Zoom [-] 150% [+]` 한 줄 위젯. 퍼센트 글자를 누르면 기본 배율로."""
        w = QWidget(parent)
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        if label:
            row.addWidget(QLabel(label))
        btn_out = QToolButton(w)
        btn_out.setText("-")
        btn_out.setToolTip("Zoom out the list (Ctrl + Mouse Wheel).")
        btn_out.clicked.connect(lambda *_: self.zoom_out())
        pct = QToolButton(w)
        pct.setAutoRaise(True)
        pct.setToolTip("Click to reset to {0:d}%.".format(int(round(self.default * 100))))
        pct.clicked.connect(lambda *_: self.reset())
        pct.setMinimumWidth(44)
        btn_in = QToolButton(w)
        btn_in.setText("+")
        btn_in.setToolTip("Zoom in the list (Ctrl + Mouse Wheel).")
        btn_in.clicked.connect(lambda *_: self.zoom_in())
        for b in (btn_out, pct, btn_in):
            row.addWidget(b)
        self._labels.append(pct)
        pct.setText("{0:d}%".format(int(round(self._scale * 100))))
        w.btn_zoom_out, w.btn_zoom_reset, w.btn_zoom_in = btn_out, pct, btn_in
        return w
