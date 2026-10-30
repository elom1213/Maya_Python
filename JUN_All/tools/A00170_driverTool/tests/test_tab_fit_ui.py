# -*- coding: utf-8 -*-
# A00170_driverTool v01.35 - 탭마다 창 높이가 **그 탭 페이지**에 맞는지 + 리스트가 짧게 열리는지 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_tab_fit_ui.py
#
# 배경(2026-10-30): v01.34 가 공용 tabFit 을 달았는데도 Remap Value · Spherical Eye · AttachCrv > Default 가
# 가장 긴 Seal 페이지 높이로 열렸다. Qt 5.15 의 `QTabWidget.sizeHint()` 가 숨은 페이지의 `Ignored` 정책을 보지 않고
# **모든 페이지 sizeHint 의 최댓값**을 내기 때문 - tabFit 의 `tab_correction` 이 이를 보정한다. 리스트(QListWidget 기본
# sizeHint 192px)는 `list_hint_height=LIST_HINT` 로 짧게 연다. 오프스크린 px 은 마야보다 크므로 절대값 대신 상대 조건으로 본다.
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다.
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
from tools.A00170_driverTool.app.ui import main_window as mw   # noqa: E402

R = []
TOL = 16


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump(n=8):
    for _ in range(n):
        app.processEvents()


# ----------------------------------------------------------------------
# 0. 전제 - Qt 5.15 QTabWidget.sizeHint 는 숨은 페이지의 Ignored 정책을 보지 않는다 (minimumSizeHint 만 따른다)
# ----------------------------------------------------------------------
class _Tall(QFrame):
    def __init__(self, h):
        super().__init__()
        self._h = h
        self.setMinimumHeight(h // 2)

    def sizeHint(self):
        return QSize(200, self._h)


def _page(h):
    w = QWidget()
    QVBoxLayout(w).addWidget(_Tall(h))
    return w


probe_tabs = QTabWidget()
p_short, p_tall = _page(300), _page(900)
probe_tabs.addTab(p_short, "a")
probe_tabs.addTab(p_tall, "b")
probe_win = QWidget()
QVBoxLayout(probe_win).addWidget(probe_tabs)
probe_win.show()
pump()
hint_before, min_before = probe_tabs.sizeHint().height(), probe_tabs.minimumSizeHint().height()
pol = p_tall.sizePolicy()
pol.setVerticalPolicy(QSizePolicy.Ignored)
p_tall.setSizePolicy(pol)
p_tall.updateGeometry()
pump()
hint_after, min_after = probe_tabs.sizeHint().height(), probe_tabs.minimumSizeHint().height()
check("premise : QTabWidget.sizeHint ignores the Ignored policy of a hidden page",
      hint_after == hint_before and hint_after >= 900, (hint_before, hint_after))
check("premise : QTabWidget.minimumSizeHint does follow it", min_after < min_before, (min_before, min_after))
probe_win.close()

# ----------------------------------------------------------------------
# 1. 툴 창 - 모든 탭(중첩 포함)에서 창 높이 = content_height, 스크롤 모자람 없음
# ----------------------------------------------------------------------
BIG = QRect(0, 0, 2560, 4000)        # 화면 제한에 걸리지 않게 아주 큰 작업 영역
win = mw.MainWindow()
ThemeManager.load_theme_to_widget(win, "teal_dark")   # launch.py 와 같은 테마
fit = win.tab_fit
check("tab_fit is the shared widget", isinstance(fit, JUN_mod_tabFit_qt_v01))
fit._available_geometry = lambda: BIG
win.show()
pump()
width0 = win.width()

heights = {}


def goto(root_index, sub_index=None):
    win.tabs.setCurrentIndex(root_index)
    if sub_index is not None:
        win.atc_tabs.setCurrentIndex(sub_index)
    pump()
    fit.fit()
    pump()


for name, idx, sub in (("Remap Value", 0, None), ("Spherical Eye", 1, None), ("AttachCrv > Default", 2, 0),
                       ("AttachCrv > Edge Loop", 2, 1), ("Stretch", 3, None), ("Seal", 4, None)):
    goto(idx, sub)
    h, c, short = win.height(), fit.content_height(), fit.shortfall()
    heights[name] = h
    check("%s : window height == content height (+%d)" % (name, TOL), c <= h <= c + TOL, (h, c))
    check("%s : nothing left to scroll" % name, short <= 0, short)
    check("%s : width kept" % name, win.width() == width0, (win.width(), width0))

# ----------------------------------------------------------------------
# 2. 창 높이가 **그 페이지**를 따른다 - 가장 긴 Seal 보다 짧은 탭은 짧게 열린다
# ----------------------------------------------------------------------
seal = heights["Seal"]
for name in ("Remap Value", "Spherical Eye", "AttachCrv > Default"):
    check("%s : opens well below the tallest page (Seal)" % name, heights[name] <= seal * 0.62, (heights[name], seal))
check("Stretch : between the short tabs and Seal", heights["AttachCrv > Default"] < heights["Stretch"] < seal,
      (heights["Stretch"], seal))
check("Edge Loop (word-wrap label -> height-for-width path) : its own height, not Seal's",
      heights["AttachCrv > Edge Loop"] < seal, (heights["AttachCrv > Edge Loop"], seal))

goto(4)
check("tab_correction is 0 on the tallest page", fit.tab_correction() == 0, fit.tab_correction())
goto(0)
check("tab_correction is negative on a shorter page", fit.tab_correction() < 0, fit.tab_correction())

# 창 높이 - 페이지 sizeHint = 탭 밖 부분(메뉴 · 탭 바 · 로그 · 푸터)이라 탭마다 같아야 한다
chrome = {}
for name, idx in (("Remap Value", 0), ("Spherical Eye", 1), ("Stretch", 3), ("Seal", 4)):
    goto(idx)
    chrome[name] = win.height() - win.tabs.widget(idx).sizeHint().height()
spread = max(chrome.values()) - min(chrome.values())
check("window height - page sizeHint is the same on every root tab (<= %d px spread)" % TOL, spread <= TOL, chrome)

# ----------------------------------------------------------------------
# 3. 리스트는 LIST_HINT 로 짧게 열리고, 창을 늘리면 따라 늘어난다
# ----------------------------------------------------------------------
check("LIST_HINT is 100 (half-height lists, user request 2026-10-30)", mw.LIST_HINT == 100, mw.LIST_HINT)
for name, idx, sub, tsls in (("Remap Value", 0, None, ("rmp_joints_tsl", "rmp_attr_tsl")),
                             ("Spherical Eye", 1, None, ("sph_joints_tsl",)),
                             ("AttachCrv > Default", 2, 0, ("atc_objs_tsl",))):
    goto(idx, sub)
    for attr in tsls:
        lw = getattr(win, attr).list_widget
        check("%s %s : list sizeHint == LIST_HINT" % (name, attr), lw.sizeHint().height() == mw.LIST_HINT,
              lw.sizeHint().height())
        check("%s %s : list opens near LIST_HINT (not the 192px Qt default)" % (name, attr),
              mw.LIST_HINT <= lw.height() <= mw.LIST_HINT + 60, lw.height())

goto(1)
before = win.sph_joints_tsl.list_widget.height()
win.resize(win.width(), win.height() + 300)
pump()
after = win.sph_joints_tsl.list_widget.height()
check("Spherical Eye : list grows when the window is made taller", after >= before + 250, (before, after))
goto(1)
check("Spherical Eye : fit() brings the window back", win.height() == heights["Spherical Eye"],
      (win.height(), heights["Spherical Eye"]))

# 다른 탭의 리스트는 그대로 Qt 기본 sizeHint (바꾸지 않았다)
goto(4)
check("Seal lists keep the default list sizeHint", win.seal_up_tsl.list_widget.sizeHint().height() != mw.LIST_HINT,
      win.seal_up_tsl.list_widget.sizeHint().height())

# ----------------------------------------------------------------------
# 4. AttachCrv > Default 의 모드별(Objects 숨김/보임) 도 맞춰진다
# ----------------------------------------------------------------------
goto(2, 0)
mode_h = {}
for i in range(win.atc_cb_mode.count()):
    win.atc_cb_mode.setCurrentIndex(i)
    pump()
    fit.fit()
    pump()
    h, c = win.height(), fit.content_height()
    mode_h[win.atc_cb_mode.currentText()] = h
    check("AttachCrv mode %s : window height == content height" % win.atc_cb_mode.currentText(),
          c <= h <= c + TOL, (h, c))
win.atc_cb_mode.setCurrentIndex(0)
check("Distribute mode (no Objects list) is the shortest", min(mode_h, key=mode_h.get) == mw.MODE_DISTRIBUTE, mode_h)

win.close()
win.deleteLater()
pump()
n_fail = R.count(False)
print("\n%d checks, %d failed" % (len(R), n_fail))
maya.standalone.uninitialize()
sys.exit(1 if n_fail else 0)
