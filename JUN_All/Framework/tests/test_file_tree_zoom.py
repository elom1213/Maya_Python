# -*- coding: utf-8 -*-
# Framework/qt/MOD_fileTree_qt_v01 의 글자 확대 / 축소 (zoom_key, 2026-11-23 · A00240 v01.34) 시험 - 오프스크린.
#   python test_file_tree_zoom.py                                              (PySide6)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_file_tree_zoom.py  (PySide2)
import os
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)

from Framework.qt.qt import *   # noqa: E402,F403
from Framework.qt.MOD_fileTree_qt_v01 import JUN_mod_fileTree_qt_v01   # noqa: E402
from Framework.qt.MOD_viewZoom_qt_v01 import SETTINGS_ORG, SETTINGS_APP, JUN_mod_viewZoom_qt_v01   # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)
R = []
KEY = "Framework_test/fileTreeZoom"


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra != "" else ""))


def forget():
    QSettings(SETTINGS_ORG, SETTINGS_APP).remove(KEY)


tmp = tempfile.mkdtemp(prefix="jun_tree_zoom_")
try:
    for d in ("A/B", "A/C", "D"):
        os.makedirs(os.path.join(tmp, d))
    for f in ("top.ma", "A/one.ma", "A/B/two.mb", "D/three.txt"):
        open(os.path.join(tmp, f), "w").close()
    forget()

    # ---- 끈 상태(기본) = 예전 그대로 (A00480 · A00210 은 이렇게 쓴다)
    plain = JUN_mod_fileTree_qt_v01()
    check("default: no zoom, no zoom buttons, the tree keeps Qt's own delegate",
          plain.zoom is None and plain.zoom_controls is None and not plain._zooms and type(plain.tree.itemDelegate()).__name__ == "QStyledItemDelegate")

    # ---- 켠 상태
    w = JUN_mod_fileTree_qt_v01(zoom_key=KEY)
    w.resize(500, 600)
    w.show()
    w.ipf_path.setText(tmp)
    w.on_build()
    app.processEvents()
    check("zoom on: the tree gets a viewZoom (Ctrl + wheel)", isinstance(w.zoom, JUN_mod_viewZoom_qt_v01))
    check("zoom buttons [-] 100% [+] sit in the Filter row of the tree widget",
          w.zoom_controls is not None and w.isAncestorOf(w.zoom_controls) and w.zoom_controls.isVisible())
    check("starts at 100% (looks the same as before until the user zooms)", abs(w.zoom.scale() - 1.0) < 1e-9)
    check("tooltip tells Ctrl + Mouse Wheel", "Ctrl + Mouse Wheel" in w.tree.toolTip())
    root_item = w.tree.topLevelItem(0)
    check("the tree was built", root_item is not None and root_item.childCount() >= 2)
    row0 = w.tree.sizeHintForRow(0)
    px0 = w.zoom.font_px()
    w.zoom.set_scale(1.5)
    app.processEvents()
    row1 = w.tree.sizeHintForRow(0)
    px1 = w.zoom.font_px()
    check("150%: text and rows get bigger", px1 > px0 and row1 > row0, (px0, px1, row0, row1))
    check("the text size is on the tree's own stylesheet (the theme's font-size cannot win)",
          "font-size" in w.tree.styleSheet())
    big = w._make_tree_widget()
    w._fill_tree(big)
    check("the Expand window tree opens at the same zoom", abs(w._zooms[-1].scale() - 1.5) < 1e-9 and big.topLevelItem(0) is not None)
    w._trees.remove(big)
    big.deleteLater()

    # ---- 기억
    again = JUN_mod_fileTree_qt_v01(zoom_key=KEY)
    check("the zoom is remembered for next time (same key)", abs(again.zoom.scale() - 1.5) < 1e-9)

    # ---- 체크박스 트리와 함께 (A00480 처럼 checkable_files 를 켠 경우도 깨지지 않는다)
    cw = JUN_mod_fileTree_qt_v01(checkable_files=True, zoom_key=KEY)
    cw.show()
    cw.ipf_path.setText(tmp)
    cw.on_build()
    app.processEvents()
    # 체크는 사용자 클릭으로만 기록된다(setCheckState 는 확대와 무관하게 기록 안 됨) → 실제 클릭으로 시험
    QTest = __import__(QApplication.__module__.split(".")[0] + ".QtTest", fromlist=["QTest"]).QTest
    cw.zoom.set_scale(2.0)                      # 체크박스가 커진 상태에서도
    app.processEvents()
    root_c = cw.tree.topLevelItem(0)
    target = [root_c.child(i) for i in range(root_c.childCount())
              if os.path.isfile(root_c.child(i).data(0, Qt.UserRole) or "")]
    target = target[0] if target else None
    if target is not None:
        rect = cw.tree.visualItemRect(target)
        QTest.mouseClick(cw.tree.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(rect.left() + 10, rect.center().y()))
        app.processEvents()
    check("zoom 200% + checkable files: clicking the (bigger) check box still checks the file",
          target is not None and target.data(0, Qt.UserRole) in cw.checked_paths(),
          (target.text(0) if target else None, cw.checked_paths()))
finally:
    forget()
    shutil.rmtree(tmp, ignore_errors=True)

# ---- A00240 이 실제로 켜 두는지 (소스)
src = open(os.path.join(JUN_ALL, "tools", "A00240_PathTool", "app", "ui", "main_window.py"), encoding="utf-8").read()
check("A00240 Tree tab turns it on (zoom_key)", 'TreeTab(zoom_key="A00240_PathTool/tree")' in src)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
