# -*- coding: utf-8 -*-
# Framework - JUN_mod_tabFit_qt_v01 롤아웃 전수 시험 (mayapy 오프스크린, 2026-10-29)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_tab_fit_rollout.py
#
# tabFit 을 단 모든 툴의 MainWindow 를 실제로 만들어(launch.py 와 같은 테마) 보이고, 루트 탭과 그 안의
# 중첩 탭을 전부 돌며 다음을 본다.
#   - 창 높이 = tabFit.content_height() (+ 보정 16px 이내)  ← 현재 페이지에 맞춰졌다
#   - shortfall() <= 0                                     ← 보이는 스크롤 페이지/칸에 세로 스크롤이 필요 없다
#   - 폭은 탭을 바꿔도 그대로
#   - 보이는 현재 페이지(스크롤 영역이 아닌 것)의 높이 >= 그 sizeHint   ← 페이지가 잘리지 않았다 (2026-10-30 추가)
#   - 현재 페이지들 sizeHint 의 합 기준으로 창이 맞춰졌다 — 가장 긴 숨은 페이지에 끌려가지 않았다 (2026-10-30 추가,
#     Qt 5.15 QTabWidget.sizeHint 는 Ignored 정책을 보지 않는다 → tabFit.tab_correction 이 보정)
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

# 페이지 잘림이 tabFit 탓이 아닌 곳 - 창은 내용 높이에 맞는데 **툴의 창 레이아웃**이 그 공간을 탭 밖 위젯에 준다.
# A00310 : 탭 위의 TSL 과 탭이 둘 다 stretch=1 이라 QBoxLayout 이 여분을 최소 크기 기준으로 나눠 탭 안 TSL 이 최소(198)로 눌린다.
#          10-29 롤아웃 전(고정 창)에도 같은 모양 - 손보려면 그 툴의 stretch 를 고친다. 여기서는 KNOWN 으로 세고 실패로 치지 않는다.
KNOWN_CLIP = {
    "A00310_SearchTool Type": "window layout: TSL above the tabs and the tabs both stretch=1 (pre-existing)",
}
known = []


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
                # 보이는 현재 페이지(스크롤 영역 제외)가 잘리지 않았다 + 가장 긴 숨은 페이지에 끌려가지 않았다
                if not clamped:
                    for page_ in fit.visible_pages():
                        if isinstance(page_, QScrollArea):
                            continue
                        # 글줄 바꿈 라벨이 있는 페이지는 레이아웃이 실제 폭의 heightForWidth 를 쓴다(sizeHint 는 좁은 폭 기준이라 더 크다)
                        if page_.hasHeightForWidth():
                            need_ = page_.heightForWidth(page_.width())
                        else:
                            need_ = page_.sizeHint().height()
                        # 페이지 안에 중첩 탭이 있으면 그 sizeHint 는 "가장 긴 하위 페이지" 기준 - 현재 하위 페이지로 고친다
                        need_ += fit.tab_correction(page_)
                        if page_.height() < need_ - 1:
                            key_ = "%s %s" % (tool, " > ".join(label))
                            msg_ = "%s : page clipped h=%d < need %d" % (key_, page_.height(), need_)
                            if key_ in KNOWN_CLIP:
                                known.append(msg_ + "  (" + KNOWN_CLIP[key_] + ")")
                            else:
                                failed.append(msg_)
                    if fit.tab_correction() == 0:
                        # 현재 페이지가 가장 긴 페이지일 때만 0 이어야 한다 - 더 긴 숨은 페이지가 있으면 보정이 빠진 것
                        for tw_ in fit.tab_widgets():
                            if not fit._on_visible_chain(tw_) or tw_.currentWidget() is None or tw_.hasHeightForWidth():
                                continue
                            cur_ = tw_.currentWidget().sizeHint().height()
                            tallest_ = max(tw_.widget(k).sizeHint().height() for k in range(tw_.count()))
                            if tallest_ > cur_ + 1:
                                failed.append("%s %s : no correction although a hidden page is taller (%d > %d)" % (tool, " > ".join(label), tallest_, cur_))
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
print("\ntools %d, checks %d, failed %d, known %d" % (len(tools), total_checks, len(failed), len(known)))
for k in known:
    print("  KNOWN", k)
for f in failed:
    print("  FAIL", f)
maya.standalone.uninitialize()
sys.exit(1 if failed else 0)
