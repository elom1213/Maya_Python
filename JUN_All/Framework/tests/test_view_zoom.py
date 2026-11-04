# -*- coding: utf-8 -*-
# Framework/qt/MOD_viewZoom_qt_v01 시험 (오프스크린). PySide6 = 시스템 python, PySide2 = mayapy 둘 다 돈다.
#   python test_view_zoom.py
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_view_zoom.py
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)

from Framework.qt.qt import *   # noqa: E402,F403
from Framework.qt.MOD_viewZoom_qt_v01 import JUN_mod_viewZoom_qt_v01, SETTINGS_ORG, SETTINGS_APP, font_px_of   # noqa: E402

QTest = __import__(QApplication.__module__.split(".")[0] + ".QtTest", fromlist=["QTest"]).QTest
app = QApplication.instance() or QApplication(sys.argv)
R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def make_tree():
    tw = QTreeWidget()
    tw.setColumnCount(4)
    tw.setHeaderLabels(["Layer", "Mute", "Solo", "Lock"])
    hdr = tw.header()
    hdr.setSectionResizeMode(0, QHeaderView.Stretch)
    for c in (1, 2, 3):
        hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
    for name in ("Top", "Mid", "BaseAnimation"):
        it = QTreeWidgetItem([name, "", "", ""])
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        for c in (1, 2, 3):
            if name == "BaseAnimation" and c != 3:
                continue
            it.setCheckState(c, Qt.Unchecked)
        tw.addTopLevelItem(it)
    bold = tw.topLevelItem(1).font(0)
    bold.setBold(True)
    tw.topLevelItem(1).setFont(0, bold)
    tw.resize(420, 300)
    tw.show()
    app.processEvents()
    return tw


def row_h(tw, i=0):
    return tw.visualItemRect(tw.topLevelItem(i)).height()


KEY = "test/view_zoom"
QSettings(SETTINGS_ORG, SETTINGS_APP).remove(KEY)

# ---- 배율 1.0 / 2.0 : 행 높이 · 글자 · 체크박스 ----
tw = make_tree()
h_plain = row_h(tw)
z = JUN_mod_viewZoom_qt_v01(tw, default=1.0)
app.processEvents()
h1 = row_h(tw)
px1 = font_px_of(tw.font())
z.set_scale(2.0)
app.processEvents()
h2 = row_h(tw)
check("row taller at 2.0", h2 >= h1 * 1.7, (h_plain, h1, h2))
check("font doubled", font_px_of(tw.font()) == px1 * 2 == z.font_px(), (px1, font_px_of(tw.font())))
check("header font follows", font_px_of(tw.header().font()) == px1 * 2, font_px_of(tw.header().font()))
check("indicator doubled", z.delegate.indicator_size() == 26, z.delegate.indicator_size())
check("check column widened to fit indicator", tw.columnWidth(1) >= 26, tw.columnWidth(1))
check("clamped to maximum", (z.set_scale(10) or z.scale()) == 3.0, z.scale())
check("clamped to minimum", (z.set_scale(0.1) or z.scale()) == 0.8, z.scale())
z.set_scale(1.5)

# 굵은 글꼴 칸도 배율 크기 (굵기 유지)
opt = QStyleOptionViewItem()
opt.initFrom(tw)
opt.font = tw.font()
idx_bold = tw.model().index(1, 0)
z.delegate.initStyleOption(opt, idx_bold)
check("item font scaled and still bold", opt.font.pixelSize() == z.font_px() == int(round(px1 * 1.5)) and opt.font.bold(),
      (opt.font.pixelSize(), z.font_px(), opt.font.bold()))

# ---- 칸 어디를 눌러도 체크 토글, 행 선택은 그대로 ----
app.processEvents()
it0 = tw.topLevelItem(0)
tw.clearSelection()
cell = tw.visualItemRect(it0)
x_mute = tw.header().sectionViewportPosition(1) + 2              # Mute 칸의 왼쪽 끝 근처(체크박스 밖)
pt = QPoint(x_mute, cell.center().y())
QTest.mouseClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, pt)
app.processEvents()
check("click cell edge toggles Mute", it0.checkState(1) == Qt.Checked, it0.checkState(1))
check("click on check cell does not select the row", not it0.isSelected())
QTest.mouseClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, pt)
check("second click unchecks", it0.checkState(1) == Qt.Unchecked)
# 이름 칸 클릭은 평소처럼 행 선택
QTest.mouseClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(10, cell.center().y()))
check("click name cell selects the row", it0.isSelected())
# 체크 없는 칸(BaseAnimation 의 Mute) 클릭은 아무 일 없음
it2 = tw.topLevelItem(2)
cell2 = tw.visualItemRect(it2)
QTest.mouseClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(x_mute + 4, cell2.center().y()))
check("cell without check state stays without", it2.data(1, Qt.CheckStateRole) is None)
# itemChanged 가 난다 (툴은 이 시그널로 마야에 반영)
seen = []
tw.itemChanged.connect(lambda item, col: seen.append((item.text(0), col)))
QTest.mouseClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(tw.header().sectionViewportPosition(3) + 3,
                                                                      cell.center().y()))
check("itemChanged emitted for Lock", seen == [("Top", 3)], seen)

# whole_cell_toggle=False : 체크박스 밖 클릭은 토글 안 됨
tw2 = make_tree()
z2 = JUN_mod_viewZoom_qt_v01(tw2, default=1.5, whole_cell_toggle=False)
app.processEvents()
c2 = tw2.visualItemRect(tw2.topLevelItem(0))
QTest.mouseClick(tw2.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(tw2.header().sectionViewportPosition(1) + 1,
                                                                       c2.center().y()))
check("whole_cell_toggle off: edge click ignored", tw2.topLevelItem(0).checkState(1) == Qt.Unchecked)

# ---- Ctrl + 휠 ----
s0 = z.scale()
ev = QWheelEvent(QPointF(20, 20), QPointF(tw.viewport().mapToGlobal(QPoint(20, 20))), QPoint(0, 0), QPoint(0, 120),
                 Qt.NoButton, Qt.ControlModifier, Qt.NoScrollPhase, False)
QApplication.sendEvent(tw.viewport(), ev)
check("ctrl + wheel up zooms in", abs(z.scale() - (s0 + 0.1)) < 1e-6, (s0, z.scale()))
ev = QWheelEvent(QPointF(20, 20), QPointF(tw.viewport().mapToGlobal(QPoint(20, 20))), QPoint(0, 0), QPoint(0, -120),
                 Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
QApplication.sendEvent(tw.viewport(), ev)
check("plain wheel does not zoom", abs(z.scale() - (s0 + 0.1)) < 1e-6, z.scale())

# ---- 버튼 줄 ----
ctl = z.controls()
ctl.btn_zoom_in.click()
check("+ button", abs(z.scale() - (s0 + 0.2)) < 1e-6, z.scale())
check("percent label follows", ctl.btn_zoom_reset.text() == "{0:d}%".format(int(round(z.scale() * 100))),
      ctl.btn_zoom_reset.text())
ctl.btn_zoom_reset.click()
check("percent click resets to default", z.scale() == 1.0)
ctl.btn_zoom_out.click()
check("- button", abs(z.scale() - 0.9) < 1e-6, z.scale())

# ---- 기억 (QSettings) ----
tw3 = make_tree()
z3 = JUN_mod_viewZoom_qt_v01(tw3, key=KEY, default=1.5)
check("no saved value -> default", z3.scale() == 1.5)
z3.set_scale(2.2)
tw4 = make_tree()
z4 = JUN_mod_viewZoom_qt_v01(tw4, key=KEY, default=1.5)
check("saved value restored", abs(z4.scale() - 2.2) < 1e-6, z4.scale())
QSettings(SETTINGS_ORG, SETTINGS_APP).remove(KEY)

# ---- 창 qss 가 글자 크기를 박아도 (테마 `QWidget { font-size: 12px }`) 확대된다, 테마를 나중에 입혀도 Show 때 따라간다 ----
host = QWidget()
lay = QVBoxLayout(host)
tw5 = make_tree()
lay.addWidget(tw5)
z5 = JUN_mod_viewZoom_qt_v01(tw5, default=1.5)
host.setStyleSheet("QWidget { font-size: 12px; }")      # 테마는 위젯을 만든 뒤에 (launch.py 와 같은 순서)
host.show()
app.processEvents()
check("theme qss: base 12px", z5.base_font_px() == 12, z5.base_font_px())
check("theme qss: view font 18px at 150%", font_px_of(tw5.font()) == 18, font_px_of(tw5.font()))
check("theme qss: header 18px", font_px_of(tw5.header().font()) == 18, font_px_of(tw5.header().font()))
check("theme qss: sibling widgets keep 12px", font_px_of(host.font()) == 12)
z5.set_scale(2.0)
check("theme qss: 200% -> 24px", font_px_of(tw5.font()) == 24, font_px_of(tw5.font()))
tw6 = QTreeWidget()
tw6.setStyleSheet("QTreeView { background: #202020; }")
z6 = JUN_mod_viewZoom_qt_v01(tw6, default=1.0)
check("own sheet kept", "background: #202020" in tw6.styleSheet() and "font-size" in tw6.styleSheet(), tw6.styleSheet())

# ---- 그리기에서 예외가 없다 (렌더) ----
img = tw.grab()
check("renders", not img.isNull() and img.width() > 0)

# ---- QListWidget 에도 붙는다 ----
lw = QListWidget()
for t in ("a", "b"):
    li = QListWidgetItem(t)
    li.setFlags(li.flags() | Qt.ItemIsUserCheckable)
    li.setCheckState(Qt.Unchecked)
    lw.addItem(li)
lw.show()
zl = JUN_mod_viewZoom_qt_v01(lw, default=2.0)
app.processEvents()
r = lw.visualItemRect(lw.item(0))
QTest.mouseClick(lw.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(r.left() + 4 + 6, r.center().y()))
check("list: click indicator (text cell) toggles", lw.item(0).checkState() == Qt.Checked, lw.item(0).checkState())
check("list: row height scaled", r.height() >= 38, r.height())
lw.grab()

print("RESULT {0}/{1}".format(sum(R), len(R)))
