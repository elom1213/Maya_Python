# -*- coding: utf-8 -*-
# A00275_skinTool_V01 v01.38 - 탭마다 창 높이 자동 맞춤(JUN_mod_tabFit_qt_v01) 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_tab_fit_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
# 오프스크린 화면은 작으므로(800 x 600) 모니터 작업 영역은 함수를 바꿔 끼워 두 경로(넉넉한 화면 / 작은 화면)를 다 본다.
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import *   # noqa: E402,F401
from Framework.themes.theme_manager import ThemeManager   # noqa: E402
from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01   # noqa: E402
from tools.A00275_skinTool_V01.app.ui.main_window import MainWindow   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump(n=6):
    for _ in range(n):
        app.processEvents()


BIG = QRect(0, 0, 2560, 1392)
SMALL = QRect(0, 0, 1200, 600)

win = MainWindow()
ThemeManager.load_theme_to_widget(win, "green_dark")   # launch.py 와 같은 테마(글자 크기가 측정에 영향)
fit = win.tab_fit
check("tab_fit is the shared widget", isinstance(fit, JUN_mod_tabFit_qt_v01))
fit._available_geometry = lambda: BIG
win.show()
pump()

# ----------------------------------------------------------------------
# 1. 처음 보일 때 현재 페이지(Weights > Classic)에 맞춰진다
# ----------------------------------------------------------------------
h0 = win.height()


def near_content(h):
    """창 높이 = 내용 높이 + 보정(0 ~ 16px, 로그창이 최대 높이까지 받아 간 몫)."""
    c = fit.content_height()
    return c <= h <= c + 16, (h, c)


check("first show : height == content height (+ small correction)", *near_content(h0))
check("first show : height != old fixed 710", h0 != 710, h0)
check("width kept 620", win.width() == 620, win.width())


def current_scroll():
    """지금 보이는 하위 페이지의 QScrollArea."""
    sub = win.tabs.currentWidget()
    return sub.currentWidget()


def page_fits():
    scroll = current_scroll()
    inner = scroll.widget()
    vp = scroll.viewport().height()
    need = inner.sizeHint().height()
    return vp >= need and not scroll.verticalScrollBar().isVisible(), (vp, need)


ok, info = page_fits()
check("first show : no vertical scrollbar, viewport >= content", ok, info)

# ----------------------------------------------------------------------
# 2. 모든 하위 탭을 돌며 창 높이 = 내용 높이, 스크롤바 없음
# ----------------------------------------------------------------------
heights = {}
for ci in range(win.tabs.count()):
    win.tabs.setCurrentIndex(ci)
    pump()
    sub = win.tabs.currentWidget()
    for si in range(sub.count()):
        sub.setCurrentIndex(si)
        pump()
        label = "%s > %s" % (win.tabs.tabText(ci), sub.tabText(si))
        near, (h, want) = near_content(win.height())
        ok, info = page_fits()
        heights[label] = win.height()
        check("fit %-28s h=%4d ~ content %4d, no scrollbar %s" % (label, h, want, info), near and ok)

tallest = max(heights, key=heights.get)
shortest = min(heights, key=heights.get)
check("pages differ in height (tallest %s %d / shortest %s %d)" % (tallest, heights[tallest], shortest, heights[shortest]),
      heights[tallest] - heights[shortest] >= 100)

# ----------------------------------------------------------------------
# 3. 긴 탭 → 짧은 탭이면 창이 줄어든다 (grow only 가 아니다)
# ----------------------------------------------------------------------
def goto(label):
    cat, sub_label = [x.strip() for x in label.split(">")]
    for ci in range(win.tabs.count()):
        if win.tabs.tabText(ci) == cat:
            win.tabs.setCurrentIndex(ci)
            pump()
            sub = win.tabs.currentWidget()
            for si in range(sub.count()):
                if sub.tabText(si) == sub_label:
                    sub.setCurrentIndex(si)
                    pump()
                    return
    raise KeyError(label)


goto(tallest); pump()
h_tall = win.height()
goto(shortest); pump()
h_short = win.height()
check("tall -> short shrinks the window", h_short < h_tall, (h_tall, h_short))
goto(tallest); pump()
check("short -> tall grows it back", win.height() == h_tall, (win.height(), h_tall))

# ----------------------------------------------------------------------
# 4. 사용자가 손으로 줄이면 그대로 두고 스크롤이 생긴다 (최소 높이는 작다)
# ----------------------------------------------------------------------
check("window minimumSizeHint stays small (< 450)", win.minimumSizeHint().height() < 450, win.minimumSizeHint().height())
win.resize(620, 400); pump()
check("manual resize to 400 sticks", win.height() == 400, win.height())
ok, info = page_fits()
check("manual small window -> page scrolls (scrollbar visible)", not ok and current_scroll().verticalScrollBar().isVisible(), info)
goto(shortest); pump()
check("next tab change re-fits", *near_content(win.height()))

# ----------------------------------------------------------------------
# 5. 화면이 작으면 화면 높이에서 멈추고 스크롤
# ----------------------------------------------------------------------
fit._available_geometry = lambda: SMALL
goto(tallest); pump()
max_h = SMALL.height() - fit._frame_height()
check("small screen : height clamped to work area (%d)" % max_h, win.height() == max_h, win.height())
check("small screen : page scrolls", current_scroll().verticalScrollBar().isVisible())
check("small screen : window bottom inside work area", win.frameGeometry().bottom() <= SMALL.bottom(), win.frameGeometry())
fit._available_geometry = lambda: BIG
goto(shortest); pump()
goto(tallest); pump()
check("big screen again : full height", win.height() == h_tall, (win.height(), h_tall))

# ----------------------------------------------------------------------
# 6. 끄면 정책이 돌아와 탭 위젯 sizeHint 가 다시 '모든 페이지 최댓값' 이 된다
# ----------------------------------------------------------------------
goto(shortest); pump()
def ignored_pages():
    return [tw.widget(i) for tw in fit.tab_widgets() for i in range(tw.count())
            if tw.widget(i).sizePolicy().verticalPolicy() == QSizePolicy.Ignored]


# 상위 4 중 3 숨김 + 하위 12 중 (카테고리마다 현재 1 씩) 8 숨김 = 11
check("enabled : hidden pages have vertical Ignored policy (11)", len(ignored_pages()) == 11, len(ignored_pages()))
fit.set_enabled(False)
pump()
check("disabled : every page policy restored (no Ignored)", not ignored_pages(), len(ignored_pages()))
fit.set_enabled(True); pump()
check("re-enabled : fits again", *near_content(win.height()))

# ----------------------------------------------------------------------
# 7. 기존 동작 회귀 - 하위 페이지는 전부 QScrollArea, 상위는 아님, 편집 탭 재조회 슬롯 그대로
# ----------------------------------------------------------------------
all_scroll = all(isinstance(win.tabs.widget(ci).widget(si), QScrollArea)
                 for ci in range(win.tabs.count()) for si in range(win.tabs.widget(ci).count()))
check("sub pages are still QScrollArea", all_scroll)
check("category pages are QTabWidget (no double scroll)", all(isinstance(win.tabs.widget(ci), QTabWidget) for ci in range(win.tabs.count())))
check("visible_scroll_pages = exactly the current sub page", fit.visible_scroll_pages() == [current_scroll()])

win.close()
print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
