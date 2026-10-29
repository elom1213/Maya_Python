# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
"""
JUN_mod_tabFit_qt_v01 - 탭을 바꿀 때마다 창 높이를 **지금 보이는 탭 내용**에 맞춘다.

문제
----
툴 창의 탭 페이지는 길이가 제각각이다. `QTabWidget` 의 sizeHint / minimumSizeHint 는 **안 보이는
페이지까지 포함한 모든 페이지의 최댓값**이라, 창을 고정 높이로 열고 긴 페이지는 `QScrollArea` 로
스크롤해 보게 된다. 사용자는 스크롤 없이 페이지 전체가 보이도록 **탭마다 창 높이가 저절로 맞춰지길**
원했다 (2026-10-29, A00275 에 먼저 적용).

원리
----
1. 안 보이는 탭 페이지의 **세로 size policy 를 `Ignored`** 로 둔다. `QStackedLayout` 은 `Ignored`
   정책인 위젯의 그 방향 sizeHint 를 0 으로 치므로, 탭 위젯의 sizeHint 가 **현재 페이지만** 따른다.
   현재 페이지는 원래 정책으로 되돌린다. 중첩 탭(카테고리 > 기능)도 같은 규칙을 모든 QTabWidget 에
   적용하면 바깥 → 안쪽 사슬의 현재 페이지만 남는다.
2. 페이지가 `QScrollArea` 면 그 sizeHint 는 믿지 않는다 - **`QScrollArea.sizeHint()` 는 글자 높이의
   24배(12px 글꼴이면 약 350px)로 잘려 있다**(Qt 소스 `boundedTo(36h, 24h)`, sizeAdjustPolicy 와 무관).
   그래서 창 sizeHint 에 **(안 내용 sizeHint + 테두리) - 스크롤 영역 sizeHint** 만큼을 더한다.
   보이는 사슬(바깥 탭의 현재 페이지 안에 든 것)의 스크롤 페이지마다 더한다. minimumSizeHint 는 그대로
   작아서, 창을 손으로 줄이면 예전처럼 스크롤이 생긴다 - 스크롤 영역은 **화면보다 긴 페이지의 안전망**으로 남는다.
3. 탭이 바뀌면(모든 QTabWidget 의 `currentChanged`) 다음 이벤트 루프에서 창을 `sizeHint` 높이로
   `resize` 한다. 폭은 건드리지 않는다. 높이는 창이 있는 모니터의 **작업 영역 - 타이틀 바**를
   넘지 않게 자르고, 창 아래가 화면 밖이면 위로 올린다([[window-taller-than-screen-ghost]]).
4. 처음 보일 때도 한 번 맞춘다 - 테마 qss 는 show() 뒤 polish 때 적용되므로 `showEvent` 다음
   이벤트 루프에서 잰다([[offscreen-size-needs-theme]]).

사용법
------
    from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01

    self.tabs = QTabWidget()
    ...  # 페이지(중첩 탭 · QScrollArea 포함)를 다 넣은 뒤
    main_layout.addWidget(self.tabs)
    self.tab_fit = JUN_mod_tabFit_qt_v01(self, self.tabs)

    # 페이지 내용이 바뀌어 높이가 달라졌을 때(접기 · 숨김 등)
    self.tab_fit.fit_later()

- `tabs` 아래의 QTabWidget 은 전부(중첩 포함) 자동으로 따라간다. 나중에 생긴 탭 위젯도 다음 fit 때 잡는다.
- `enabled=False` 로 만들거나 `set_enabled(False)` 로 끄면 정책만 되돌리고 아무것도 하지 않는다.
- 창 밖 다른 위젯(로그창 등)은 레이아웃의 sizeHint 그대로 더해진다. 로그창처럼 늘어나는 위젯은
  `setMaximumHeight` 가 있어야 창이 그만큼만 커진다.

Maya 밖에서도 import / 생성이 가능하도록 maya 의존이 없다.
"""

from Framework.qt.qt import *


# 페이지의 원래 세로 정책을 기억해 두는 property 이름
_ORIG_VPOLICY = "_jun_tabFit_vpolicy"


class JUN_mod_tabFit_qt_v01(QObject):
    """창 + 루트 QTabWidget 에 붙여, 탭 전환마다 창 높이를 현재 페이지에 맞춘다."""

    fitted = Signal(int)        # 맞춘 뒤 창 높이

    def __init__(self, window, tabs, enabled=True, parent=None):
        super().__init__(parent or window)
        self._window = window
        self._tabs = tabs
        self._enabled = bool(enabled)
        self._connected = set()         # currentChanged 를 이미 연결한 QTabWidget id
        self._shown_once = False
        self._pending = False

        self._hook_tab_widgets()
        window.installEventFilter(self)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def set_enabled(self, enabled):
        """끄면 페이지 정책을 원래대로 돌리고 더는 창을 건드리지 않는다. 켜면 바로 한 번 맞춘다."""
        enabled = bool(enabled)
        if enabled == self._enabled:
            return
        self._enabled = enabled
        if enabled:
            self.fit_later()
        else:
            for tab_widget in self.tab_widgets():
                for i in range(tab_widget.count()):
                    self._restore_policy(tab_widget.widget(i))

    def is_enabled(self):
        return self._enabled

    def tab_widgets(self):
        """루트 탭 위젯 + 그 아래 모든 QTabWidget."""
        if self._tabs is None:
            return []
        found = [self._tabs]
        try:
            found.extend(self._tabs.findChildren(QTabWidget))
        except Exception:
            pass
        return found

    def fit_later(self, *_args):
        """다음 이벤트 루프에서 맞춘다(탭 전환 직후엔 새 가시성이 레이아웃에 아직 안 들어가 있다)."""
        if not self._enabled or self._pending:
            return
        self._pending = True
        QTimer.singleShot(0, self._fit_now)

    def fit(self):
        """지금 바로 맞춘다. 돌려주는 값은 창 높이(안 맞췄으면 None)."""
        if not self._enabled or self._window is None:
            return None
        self._hook_tab_widgets()
        target_h = self.content_height()
        max_h = self._max_height()
        if max_h is not None:
            target_h = min(target_h, max_h)
        self._window.resize(self._window.width(), target_h)

        # 레이아웃이 남는 높이를 다른 Expanding 위젯(로그창 등, 최대 높이까지)에도 나눠 주면
        # 스크롤 페이지가 몇 px 모자랄 수 있다. 실제 뷰포트를 재서 모자란 만큼 한두 번 더 늘린다
        # (그 위젯들은 이미 최대라 두 번째부터는 전부 탭으로 간다).
        for _ in range(2):
            short = self.shortfall()
            if short <= 0:
                break
            wanted = target_h + short
            if max_h is not None:
                wanted = min(wanted, max_h)
            if wanted <= self._window.height():
                break
            target_h = wanted
            self._window.resize(self._window.width(), target_h)

        self._keep_on_screen()
        height = self._window.height()
        self.fitted.emit(height)
        return height

    def shortfall(self):
        """보이는 스크롤 페이지의 내용이 뷰포트보다 긴 만큼(px). 0 이하면 스크롤 없이 다 보인다."""
        layout = self._window.layout()
        if layout is not None:
            layout.activate()
        short = 0
        for scroll in self.visible_scroll_pages():
            need = scroll.widget().sizeHint().height()
            short = max(short, need - scroll.viewport().height())
        return short

    def content_height(self):
        """맞출 때 창이 가질 높이(화면 제한 전) = 창 sizeHint + 보이는 스크롤 페이지의 잘린 몫."""
        self._apply_policies()
        self._invalidate_layouts()
        height = self._window.sizeHint().height()
        for scroll in self.visible_scroll_pages():
            height += max(0, self._scroll_wanted_height(scroll) - scroll.sizeHint().height())
        return height

    def visible_pages(self):
        """지금 보이는 사슬의 현재 페이지들(바깥 → 안쪽)."""
        pages = []
        for tab_widget in self.tab_widgets():
            page = tab_widget.currentWidget()
            if page is None or not self._on_visible_chain(tab_widget):
                continue
            pages.append(page)
        return pages

    def visible_scroll_pages(self):
        """보이는 현재 페이지 중 내용 위젯을 가진 `QScrollArea`(widgetResizable) 들."""
        return [p for p in self.visible_pages()
                if isinstance(p, QScrollArea) and p.widget() is not None and p.widgetResizable()]

    def _on_visible_chain(self, widget):
        """조상 QTabWidget 마다 이 위젯이 **현재 페이지** 안에 있는가."""
        parent = widget.parentWidget()
        while parent is not None and parent is not self._window:
            if isinstance(parent, QTabWidget):
                current = parent.currentWidget()
                if current is None or not current.isAncestorOf(widget):
                    return False
            parent = parent.parentWidget()
        return True

    @staticmethod
    def _scroll_wanted_height(scroll):
        """스크롤 없이 내용을 다 보이는 데 필요한 스크롤 영역 높이."""
        inner = scroll.widget()
        height = inner.sizeHint().height() + 2 * scroll.frameWidth()
        if scroll.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOn:
            height += scroll.horizontalScrollBar().sizeHint().height()
        return height

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _fit_now(self):
        self._pending = False
        try:
            self.fit()
        except Exception as exc:        # 창 크기 맞추기가 툴을 죽이면 안 된다
            print("[JUN_mod_tabFit_qt_v01] fit skipped : {0}".format(exc))

    def _hook_tab_widgets(self):
        for tab_widget in self.tab_widgets():
            key = id(tab_widget)
            if key in self._connected:
                continue
            tab_widget.currentChanged.connect(self.fit_later)
            tab_widget.destroyed.connect(lambda *_a, k=key: self._connected.discard(k))
            self._connected.add(key)

    def _apply_policies(self):
        """모든 QTabWidget 에서 현재 페이지는 원래 정책, 나머지는 세로 Ignored."""
        for tab_widget in self.tab_widgets():
            current = tab_widget.currentIndex()
            for i in range(tab_widget.count()):
                page = tab_widget.widget(i)
                if page is None:
                    continue
                if i == current:
                    self._restore_policy(page)
                else:
                    self._ignore_vertical(page)

    def _ignore_vertical(self, page):
        policy = page.sizePolicy()
        if policy.verticalPolicy() == QSizePolicy.Ignored:
            return
        if page.property(_ORIG_VPOLICY) is None:
            page.setProperty(_ORIG_VPOLICY, int(policy.verticalPolicy()))
        policy.setVerticalPolicy(QSizePolicy.Ignored)
        page.setSizePolicy(policy)

    def _restore_policy(self, page):
        if page is None:
            return
        orig = page.property(_ORIG_VPOLICY)
        if orig is None:
            return
        policy = page.sizePolicy()
        if policy.verticalPolicy() != QSizePolicy.Ignored:
            return
        policy.setVerticalPolicy(QSizePolicy.Policy(int(orig)))
        page.setSizePolicy(policy)

    def _invalidate_layouts(self):
        """정책을 바꾼 뒤 캐시된 sizeHint 를 버리게 한다 - 페이지 → 탭 위젯 → 창 순."""
        for tab_widget in self.tab_widgets():
            for i in range(tab_widget.count()):
                page = tab_widget.widget(i)
                if page is None:
                    continue
                if isinstance(page, QScrollArea) and page.widget() is not None:
                    inner = page.widget()
                    if inner.layout() is not None:
                        inner.layout().invalidate()
                        inner.layout().activate()
                    inner.updateGeometry()
                page.updateGeometry()
            tab_widget.updateGeometry()
        layout = self._window.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()

    def _available_geometry(self):
        """창이 떠 있는 모니터의 작업 영역(작업 표시줄 제외). 모르면 None."""
        window = self._window
        screen = None
        try:
            handle = window.windowHandle()
            if handle is not None:
                screen = handle.screen()
        except Exception:
            screen = None
        if screen is None:
            try:
                screen = QGuiApplication.screenAt(window.frameGeometry().center())
            except Exception:
                screen = None
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen is not None else None

    def _frame_height(self):
        """타이틀 바 + 테두리. 아직 안 보였으면 0 (frameGeometry 가 geometry 와 같다)."""
        window = self._window
        return max(0, window.frameGeometry().height() - window.geometry().height())

    def _max_height(self):
        avail = self._available_geometry()
        if avail is None:
            return None
        return max(100, avail.height() - self._frame_height())

    def _keep_on_screen(self):
        """창 아래가 화면 밖이면 위로 올린다 (처음 보이기 전엔 건드리지 않는다)."""
        if not self._shown_once:
            return
        avail = self._available_geometry()
        if avail is None:
            return
        frame = self._window.frameGeometry()
        if frame.bottom() > avail.bottom() or frame.top() < avail.top():
            top = max(avail.top(), avail.bottom() - frame.height() + 1)
            self._window.move(frame.left(), top)

    # ------------------------------------------------------------------
    # 창 이벤트
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        if obj is self._window and event.type() == QEvent.Show and not self._shown_once:
            self._shown_once = True
            self.fit_later()
        return False
