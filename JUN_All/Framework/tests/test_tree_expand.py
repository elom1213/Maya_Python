# -*- coding: utf-8 -*-
# Framework.qt.MOD_treeExpand_qt_v01 시험 (오프스크린). 화살표 클릭 = 한 단계, Shift = 전부.
#   python test_tree_expand.py
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import (  # noqa: E402
    QApplication, QTreeWidget, QTreeWidgetItem, QTreeView, QStandardItemModel, QStandardItem, Qt, QPoint)
try:
    from PySide6.QtTest import QTest  # noqa: E402
except ImportError:
    from PySide2.QtTest import QTest  # noqa: E402
app = QApplication.instance() or QApplication([])
from Framework.qt.MOD_treeExpand_qt_v01 import JUN_mod_treeExpand_qt_v01, attach  # noqa: E402
from Framework.qt import JUN_mod_treeExpand_qt  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build_widget_tree():
    tw = QTreeWidget()
    tw.setHeaderLabels(["Name"])
    root = QTreeWidgetItem(["root"])
    tw.addTopLevelItem(root)
    a = QTreeWidgetItem(["a"])
    root.addChild(a)
    a1 = QTreeWidgetItem(["a1"])
    a.addChild(a1)
    a1.addChild(QTreeWidgetItem(["a1x"]))
    b = QTreeWidgetItem(["b"])
    root.addChild(b)
    b.addChild(QTreeWidgetItem(["b1"]))
    return tw, root, a, a1, b


def arrow_click(view, item_or_index, shift=False):
    idx = view.indexFromItem(item_or_index) if hasattr(view, "indexFromItem") else item_or_index
    rect = view.visualRect(idx)
    pos = QPoint(rect.x() - view.indentation() // 2, rect.center().y())
    mods = Qt.ShiftModifier if shift else Qt.NoModifier
    QTest.mouseClick(view.viewport(), Qt.LeftButton, mods, pos)
    app.processEvents()


def all_expanded(items):
    return all(i.isExpanded() for i in items)


tw, root, a, a1, b = build_widget_tree()
ext = JUN_mod_treeExpand_qt_v01(tw)
tw.resize(400, 300)
tw.show()
app.processEvents()

# 코드의 expandAll 은 그대로 (사용자 입력이 아니다)
tw.expandAll()
app.processEvents()
check("code expandAll untouched", all_expanded([root, a, a1, b]))

# 접고 다시 펼치면 한 단계만 (Qt 기본은 a / a1 / b 가 다시 열린 채)
arrow_click(tw, root)
check("arrow click collapses root", not root.isExpanded())
arrow_click(tw, root)
check("arrow expand shows one level", root.isExpanded() and not a.isExpanded() and not b.isExpanded(),
      (root.isExpanded(), a.isExpanded(), b.isExpanded()))
check("deeper state remembered below collapsed child", a1.isExpanded())   # a 를 펼치면 다시 한 단계로 정리된다
arrow_click(tw, a)
check("expand child: one level again", a.isExpanded() and not a1.isExpanded())

# Shift + 펼치기 = 전부
arrow_click(tw, root)          # 접기
arrow_click(tw, root, shift=True)
check("shift expand = all below", all_expanded([root, a, a1, b]))

# Shift + 접기 = 전부 접기
arrow_click(tw, root, shift=True)
check("shift collapse = root + all below collapsed", not any(i.isExpanded() for i in (root, a, a1, b)))
arrow_click(tw, root)
check("after shift collapse, expand = one level", root.isExpanded() and not a.isExpanded())

# 더블클릭(행)도 사용자 입력 - 한 단계
tw.collapseAll()
tw.expandAll()
arrow_click(tw, root)
rect = tw.visualItemRect(root)
QTest.mouseClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center())    # 실제 더블클릭처럼 누름이 먼저
QTest.mouseDClick(tw.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center())
app.processEvents()
check("double click expand = one level", root.isExpanded() and not a.isExpanded())

# 키보드: 오른쪽 화살표 = 한 단계, '*' = 전부
tw.collapseAll()
tw.expandAll()
tw.collapseItem(root)
tw.setCurrentItem(root)
tw.setFocus()
QTest.keyClick(tw, Qt.Key_Right)
app.processEvents()
check("Right key expand = one level", root.isExpanded() and not a.isExpanded())
tw.collapseItem(root)
QTest.keyClick(tw, Qt.Key_Asterisk)
app.processEvents()
check("'*' key = all below", all_expanded([root, a, a1, b]))

# 코드 setExpanded / expand 는 손대지 않는다
tw.collapseAll()
a1.setExpanded(True)
root.setExpanded(True)
check("code setExpanded untouched", root.isExpanded() and a1.isExpanded())

# 두 번 붙여도 하나
again = JUN_mod_treeExpand_qt_v01(tw)
check("attach twice returns same", again is ext and attach(tw) is ext)
arrow_click(tw, root)
arrow_click(tw, root)
check("still works after re-attach", root.isExpanded() and not a.isExpanded())
check("alias in Framework.qt", JUN_mod_treeExpand_qt.JUN_mod_treeExpand_qt_v01 is JUN_mod_treeExpand_qt_v01)

# QTreeView + 모델
view = QTreeView()
model = QStandardItemModel()
r = QStandardItem("r")
c = QStandardItem("c")
g = QStandardItem("g")
c.appendRow(g)
g.appendRow(QStandardItem("leaf"))
r.appendRow(c)
model.appendRow(r)
view.setModel(model)
JUN_mod_treeExpand_qt_v01(view)
view.resize(300, 200)
view.show()
view.expandAll()
app.processEvents()
ri, ci, gi = model.indexFromItem(r), model.indexFromItem(c), model.indexFromItem(g)
arrow_click(view, ri)
arrow_click(view, ri)
check("QTreeView: one level", view.isExpanded(ri) and not view.isExpanded(ci))
arrow_click(view, ri)
arrow_click(view, ri, shift=True)
check("QTreeView: shift = all", view.isExpanded(ri) and view.isExpanded(ci) and view.isExpanded(gi))

# 게으른 트리: 펼칠 때 자식을 채운다 - Shift 전부 펼치기가 따라가되 max_nodes 에서 멈춘다
lazy = QTreeWidget()
made = [0]


def make_lazy(parent, depth):
    it = QTreeWidgetItem(["d{0}".format(depth)])
    it.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
    it.setData(0, Qt.UserRole, depth)
    (parent.addChild(it) if isinstance(parent, QTreeWidgetItem) else parent.addTopLevelItem(it))
    made[0] += 1
    return it


def on_lazy_expand(item):
    if item.childCount() == 0:
        for _ in range(2):
            make_lazy(item, item.data(0, Qt.UserRole) + 1)


lazy.itemExpanded.connect(on_lazy_expand)
top = make_lazy(lazy, 0)
JUN_mod_treeExpand_qt_v01(lazy, max_nodes=50)
lazy.resize(300, 300)
lazy.show()
app.processEvents()
arrow_click(lazy, top, shift=True)
check("lazy tree: shift expand follows new children, stops at max_nodes",
      top.isExpanded() and top.child(0).isExpanded() and top.child(1).isExpanded() and 50 <= made[0] <= 160, made[0])
check("lazy tree: breadth first (shallow levels filled first)",
      all(top.child(i).child(j).isExpanded() for i in range(2) for j in range(2)))

print("\n{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
