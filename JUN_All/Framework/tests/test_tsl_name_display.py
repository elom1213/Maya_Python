# -*- coding: utf-8 -*-
# Framework/qt/MOD_tsl_qt_v01 - 이름 표시 모드(name_display) 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_tsl_name_display.py
# 계획서 docs/plans/Framework_MOD_tsl_qt_name_display_plan.md §4-1.
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다. 사용자 QSettings 값은 끝에서 되돌린다.
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)

from Framework.qt.qt import *   # noqa: E402,F403
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from Framework.qt import MOD_tsl_qt_v01 as T   # noqa: E402
from Framework.qt.MOD_filter_qt_v01 import JUN_mod_filter_qt_v01   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


settings = QSettings(T.NAME_SETTINGS_ORG, T.NAME_SETTINGS_APP)
saved = settings.value(T.NAME_SETTINGS_KEY)

# 1. display_name 규칙
cases = [("A|dup", "dup"), ("|A|dup", "dup"), ("keep", "keep"), ("grp|ns:dup", "ns:dup"),
         ("A|pCube1|pCube1Shape.vtx[3]", "pCube1Shape.vtx[3]"), ("A|pCube1.vtx[0:5]", "pCube1.vtx[0:5]"),
         ("nodeA.translateX", "nodeA.translateX"), ("(Null)", "(Null)"), ("", ""), ("a file.ma", "a file.ma")]
bad = [(i, T.display_name(i), o) for i, o in cases if T.display_name(i) != o]
check("display_name rules", not bad, bad)

# 2. 저장값이 없으면 기본 Outliner Name
settings.remove(T.NAME_SETTINGS_KEY)
T._NAME_STATE["mode"] = None
check("default mode is Outliner Name", T.get_name_display() == T.NAME_OUTLINER, T.get_name_display())

# ---- 씬 : A|dup, B|dup, keep, A|pCube1
cmds.file(new=True, force=True)
for grp, x in (("A", -2), ("B", 2)):
    cmds.group(empty=True, name=grp)
    cmds.select(clear=True)
    j = cmds.joint(name="dup", position=(x, 0, 0))
    cmds.parent(j, grp)
cmds.select(clear=True)
cmds.joint(name="keep")
cube = cmds.polyCube(name="pCube1")[0]
cmds.parent(cube, "A")

tsl = T.JUN_mod_tsl_qt_v01(title="Opt-in", name_display=True)
plain = T.JUN_mod_tsl_qt_v01(title="Plain")
cmds.select(["A|dup", "B|dup", "keep"])
listed = cmds.ls(sl=True)
tsl.set_items(listed)
plain.set_items(listed)
check("listed names are the clash-free paths", listed == ["A|dup", "B|dup", "keep"], listed)

# 3 ~ 6
check("get_all_items keeps the stored text", tsl.get_all_items() == listed, tsl.get_all_items())
dlg = tsl.list_widget.itemDelegate()
shown = [dlg.displayText(tsl.list_widget.item(i).text(), QLocale()) for i in range(3)]
check("delegate draws Outliner names", shown == ["dup", "dup", "keep"], shown)
check("shown_text matches", [tsl.shown_text(i) for i in range(3)] == ["dup", "dup", "keep"])
check("tooltips tell the same names apart",
      tsl.full_path_tooltip(0) == "|A|dup" and tsl.full_path_tooltip(1) == "|B|dup"
      and tsl.full_path_tooltip(2) == "|keep", [tsl.full_path_tooltip(i) for i in range(3)])

# 6b. 실제 툴팁 이벤트 (helpEvent) - 툴팁을 띄우고 True
view = tsl.list_widget
idx = view.model().index(1, 0)
rect = view.visualRect(idx)
ev = QHelpEvent(QEvent.ToolTip, rect.center(), view.viewport().mapToGlobal(rect.center()))
handled = dlg.helpEvent(ev, view, QStyleOptionViewItem(), idx)
check("helpEvent shows the full path tooltip", handled and QToolTip.text() == "|B|dup", (handled, QToolTip.text()))
QToolTip.hideText()

# 7. 리네임해도 툴팁은 지금 경로
cmds.rename("A", "A2")
check("tooltip follows a rename (UUID)", tsl.full_path_tooltip(0) == "|A2|dup", tsl.full_path_tooltip(0))
cmds.rename("A2", "A")

# 8. 지운 노드
tmp = T.JUN_mod_tsl_qt_v01(title="Tmp", name_display=True)
cmds.select(clear=True)
gone = cmds.joint(name="gone")
tmp.set_items([gone])
cmds.delete(gone)
check("deleted node tooltip says not in the scene",
      tmp.full_path_tooltip(0) == "gone  (not in the scene)", tmp.full_path_tooltip(0))

# 9. (Null) 은 글자 그대로 + 기존 안내 툴팁 유지
tmp.set_items(["(Null)"])
item = tmp.list_widget.item(0)
check("(Null) unchanged and keeps its own tooltip",
      tmp.shown_text(0) == "(Null)" and bool(item.toolTip()) and tmp.full_path_tooltip(0) is None,
      (tmp.shown_text(0), item.toolTip()))

# 10. 컴포넌트
cmds.select("A|pCube1.vtx[0]")
comp_text = cmds.ls(sl=True)[0]
tmp.set_items([comp_text])
check("component : short shown, full path tooltip",
      tmp.shown_text(0) == "pCube1.vtx[0]" and tmp.full_path_tooltip(0) == "|A|pCube1.vtx[0]",
      (comp_text, tmp.shown_text(0), tmp.full_path_tooltip(0)))

# 11 ~ 14. Full Path 로 바꾸기
other = T.JUN_mod_tsl_qt_v01(title="Other", name_display=True)
other.set_items(listed)
T.set_name_display(T.NAME_FULL)
shown = [dlg.displayText(tsl.list_widget.item(i).text(), QLocale()) for i in range(3)]
check("Full Path draws the stored text", shown == listed, shown)
check("every opt-in list follows the mode", other.name_display_mode() == T.NAME_FULL
      and other.shown_text(0) == "A|dup")
check("mode is saved in QSettings",
      QSettings(T.NAME_SETTINGS_ORG, T.NAME_SETTINGS_APP).value(T.NAME_SETTINGS_KEY) == T.NAME_FULL)
T._NAME_STATE["mode"] = None
check("saved mode is read back", T.get_name_display() == T.NAME_FULL)
try:
    T.set_name_display("bad")
    raised = False
except ValueError:
    raised = True
check("unknown mode raises ValueError", raised)

# 15 ~ 16. Sort
cmds.file(new=True, force=True)
for grp, name in (("B", "alpha"), ("A", "zeta")):
    cmds.group(empty=True, name=grp)
    cmds.select(clear=True)
    j = cmds.joint(name=name)
    cmds.parent(j, grp)
cmds.select(clear=True)
cmds.joint(name="keep")
sort_items = ["A|zeta", "keep", "B|alpha"]
T.set_name_display(T.NAME_OUTLINER)
tsl.set_items(sort_items)
tsl._on_sort()
check("Outliner Name sort = shown name order", tsl.get_all_items() == ["B|alpha", "keep", "A|zeta"],
      tsl.get_all_items())
T.set_name_display(T.NAME_FULL)
tsl.set_items(sort_items)
tsl._on_sort()
check("Full Path sort = stored text order (as before)", tsl.get_all_items() == ["A|zeta", "B|alpha", "keep"],
      tsl.get_all_items())
plain.set_items(sort_items)
T.set_name_display(T.NAME_OUTLINER)
plain._on_sort()
check("not opted in : sort unchanged even in Outliner mode",
      plain.get_all_items() == ["A|zeta", "B|alpha", "keep"], plain.get_all_items())

# 17. 옵트인 아님 = 예전 그대로
check("not opted in : no name delegate, no context menu",
      not isinstance(plain.list_widget.itemDelegate(), T._NameDelegate)
      and plain.list_widget.contextMenuPolicy() != Qt.CustomContextMenu
      and plain.name_display_mode() == T.NAME_FULL and plain.shown_text(0) == plain.get_all_items()[0])

# 18. 우클릭 메뉴 액션
menu = tsl._build_name_menu()
actions = {a.text(): a for a in menu.actions() if a.isCheckable()}
check("menu has the two modes, current one checked",
      set(actions) == {"Outliner Name", "Full Path"} and actions["Outliner Name"].isChecked())
actions["Full Path"].trigger()
check("menu action switches the mode", T.get_name_display() == T.NAME_FULL)
menu2 = tsl._build_name_menu()
actions2 = {a.text(): a for a in menu2.actions() if a.isCheckable()}
actions2["Outliner Name"].trigger()
check("menu action switches back", T.get_name_display() == T.NAME_OUTLINER)

# 19. 행 클릭 = 씬 선택 (그대로)
cmds.file(new=True, force=True)
for grp in ("A", "B"):
    cmds.group(empty=True, name=grp)
    cmds.select(clear=True)
    j = cmds.joint(name="dup")
    cmds.parent(j, grp)
cmds.select(["A|dup", "B|dup"])
tsl.set_items(cmds.ls(sl=True))
cmds.select(clear=True)
tsl.list_widget.item(1).setSelected(True)
check("row click still selects the right node", cmds.ls(sl=True, long=True) == ["|B|dup"], cmds.ls(sl=True, long=True))

# 20 ~ 21. 필터
cmds.select(clear=True)
cmds.joint(name="keep")
tsl.set_items(["A|dup", "B|dup", "keep"])
flt = JUN_mod_filter_qt_v01(tsl.list_widget)
flt.le_filter.setText("A")
flt.refresh()
hidden = [tsl.list_widget.item(i).isHidden() for i in range(3)]
check("filter on an opt-in list uses the shown name ('A' hides A|dup)", hidden == [True, True, True], hidden)
flt.le_filter.setText("dup")
flt.refresh()
hidden = [tsl.list_widget.item(i).isHidden() for i in range(3)]
check("filter 'dup' shows both dup rows", hidden == [False, False, True], hidden)
plain.set_items(["A|dup", "B|dup", "keep"])
flt2 = JUN_mod_filter_qt_v01(plain.list_widget)
flt2.le_filter.setText("A")
flt2.refresh()
hidden = [plain.list_widget.item(i).isHidden() for i in range(3)]
check("filter on a plain list is unchanged ('A' keeps A|dup)", hidden == [False, True, True], hidden)

# 사용자 설정 되돌리기
if saved is None:
    settings.remove(T.NAME_SETTINGS_KEY)
else:
    settings.setValue(T.NAME_SETTINGS_KEY, saved)
T._NAME_STATE["mode"] = None

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
