# -*- coding: utf-8 -*-
# Framework - JUN_mod_tabFit_qt_v01 롤아웃 전수 시험 (mayapy 오프스크린, 2026-10-29)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_tab_fit_rollout.py
#
# tabFit 을 단 모든 툴의 MainWindow 를 실제로 만들어(launch.py 와 같은 테마) 보이고, 루트 탭과 그 안의
# 중첩 탭을 전부 돌며 다음을 본다.
#   - 창 높이 = tabFit.content_height() (+ 보정 16px 이내)  ← 현재 페이지에 맞춰졌다
#   - shortfall() <= 0                                     ← 보이는 스크롤 페이지/칸에 세로 스크롤이 필요 없다
#   - 폭은 탭을 바꿔도 그대로
# 모니터 작업 영역은 2560 x 1392 로 바꿔 끼운다(오프스크린 화면은 800 x 600 이라 전부 잘린다).
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다.
import os
import re
import sys
import glob
import importlib
import traceback

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import *   # noqa: E402,F401
from Framework.themes.theme_manager import ThemeManager   # noqa: E402
from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01   # noqa: E402

BIG = QRect(0, 0, 2560, 1392)
TOL = 16


def pump(n=8):
    for _ in range(n):
        app.processEvents()


def nearest_tab_ancestor(widget):
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QTabWidget):
            return parent
        parent = parent.parentWidget()
    return None


def theme_of(tool):
    p = os.path.join(JUN_ALL, "tools", tool, "launch.py")
    try:
        m = re.search(r'load_theme_to_widget\([^,]+,\s*"([^"]+)"', open(p, encoding="utf-8").read())
        return m.group(1) if m else None
    except Exception:
        return None


tools = sorted(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(f))))
               for f in glob.glob(os.path.join(JUN_ALL, "tools", "*", "app", "ui", "main_window.py"))
               if "JUN_mod_tabFit_qt_v01" in open(f, encoding="utf-8", errors="ignore").read())

total_checks = 0
failed = []
summary = []
for tool in tools:
    try:
        mod = importlib.import_module("tools.%s.app.ui.main_window" % tool)
        win = mod.MainWindow()
        theme = theme_of(tool)
        if theme:
            ThemeManager.load_theme_to_widget(win, theme)
        fit = win.tab_fit
        assert isinstance(fit, JUN_mod_tabFit_qt_v01)
        fit._available_geometry = lambda: BIG
        win.show()
        pump()
        if hasattr(win, "fit_to_content") and not fit.is_enabled():
            # A00480 은 launch.py 가 show 다음 루프에서 부른다 - 같은 흐름
            win.fit_to_content()
            pump()
        assert fit.is_enabled(), "tabFit not enabled after show"
        width0 = win.width()
        state = {"w": width0}

        def visit(tab_widget, path):
            """탭 위젯의 모든 페이지를 돌며 검사, 페이지 안의 중첩 탭도 재귀."""
            global total_checks
            for i in range(tab_widget.count()):
                tab_widget.setCurrentIndex(i)
                pump()
                label = path + [tab_widget.tabText(i)]
                h, c, short = win.height(), fit.content_height(), fit.shortfall()
                total_checks += 1
                clamped = h >= fit._max_height() - 1          # 화면보다 긴 페이지 - 화면 높이에서 멈추고 스크롤
                # 폭은 그대로 - 단, 페이지 최소 폭이 더 넓으면 Qt 가 최소까지 넓히고 그 뒤 줄지 않는다
                # (A00110 V01 의 fit_tab_page 페이지는 숨으면 최소 0 이라 예전부터 이랬다)
                width_ok = win.width() == state["w"] or (win.width() > state["w"] and win.width() == win.minimumWidth())
                state["w"] = win.width()
                ok = ((c <= h <= c + TOL and short <= 0) or clamped) and width_ok
                if not ok:
                    failed.append("%s %s : h=%d content=%d short=%d w=%d (start %d, min %d)" % (tool, " > ".join(label), h, c, short, win.width(), width0, win.minimumWidth()))
                page = tab_widget.widget(i)
                for inner in page.findChildren(QTabWidget):
                    # 바로 위 조상 탭이 이 탭 위젯인 것만(한 단계씩 내려간다)
                    if nearest_tab_ancestor(inner) is tab_widget and inner.count() > 1:
                        visit(inner, label)

        visit(win.tabs, [])
        heights = []
        for i in range(win.tabs.count()):
            win.tabs.setCurrentIndex(i); pump(); heights.append(win.height())
        summary.append("%-26s pages h=%s" % (tool, heights))
        win.close(); win.deleteLater(); pump()
    except Exception as exc:
        traceback.print_exc()
        failed.append("%s : %s %s" % (tool, type(exc).__name__, exc))

for line in summary:
    print(line)
print("\ntools %d, checks %d, failed %d" % (len(tools), total_checks, len(failed)))
for f in failed:
    print("  FAIL", f)
maya.standalone.uninitialize()
sys.exit(1 if failed else 0)
