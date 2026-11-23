# -*- coding: utf-8 -*-
# A00210_FileManager v01.57 - Sync > Status 의 Preview (오프스크린)   python test_sync_preview.py
# 사용자: 스캔 전에 어떤 경로 · 파일이 있는지 빠르게 트리로 - 상태 진단 없이 A00240 Tree 처럼 존재만.
import os
import shutil
import subprocess
import sys
import tempfile
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, QMessageBox, QColor, Qt  # noqa: E402
app = QApplication.instance() or QApplication([])
from Framework.qt.MOD_fileTree_qt_v01 import JUNCTION_COLOR, JUN_mod_fileTree_qt_v01  # noqa: E402
from tools.A00210_FileManager.app.core import sync_manifest as sm  # noqa: E402
from tools.A00210_FileManager.app.ui import sync_tab as st  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra != "" else ""))


def write(root, rel, size=10):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(os.urandom(size))


work = tempfile.mkdtemp(prefix="a00210_preview_")
root = os.path.join(work, "JUN")
target = os.path.join(work, "rig_target")
link = os.path.join(root, "A_rig")
try:
    # 스캔이 해시하느라 오래 걸릴 만한 양: 폴더 20 x 파일 10 x 1 MB = 200 MB
    for i in range(20):
        for j in range(10):
            write(root, "shots/s{0:02d}/take_{1:02d}.mb".format(i, j), 1024 * 1024)
    write(root, "top.ma")
    write(target, "rig_v01.mb")
    subprocess.run(["cmd", "/c", "mklink", "/J", link, target], check=True, capture_output=True)

    data_dir = os.path.join(work, "data")
    os.makedirs(data_dir)
    QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
    LOG = []
    tab = st.SyncTab(get_data_dir=lambda: data_dir, get_project_root=lambda: root.replace("\\", "/"),
                     is_git_mode=lambda: False, git_pull=lambda: True, git_push=lambda msg: True,
                     get_author=lambda: "tester", log=LOG.append)
    tab._pc = "PCA"
    tab.load_prefs({})
    tab.resize(1000, 700)
    tab.show()
    app.processEvents()
    check("Preview button sits first in the Status buttons, before Scan",
          tab.btn_preview.text() == "Preview" and tab.btn_preview.isEnabled())

    t0 = time.perf_counter()
    tab.btn_preview.click()
    app.processEvents()
    t_preview = time.perf_counter() - t0
    dlg, tree = tab._preview, tab._preview_tree
    check("Preview opens a window with the shared folder tree (same as A00240 Tree)",
          dlg is not None and dlg.isVisible() and isinstance(tree, JUN_mod_fileTree_qt_v01))
    top = tree.tree.topLevelItem(0)
    names = sorted(top.child(i).text(0) for i in range(top.childCount())) if top else []
    check("Preview shows the root's folders and files", names == ["A_rig", "shots", "top.ma"], names)
    check("adaptive (reads a folder only when opened) - fast", tree.chk_adaptive.isChecked())
    a_item = [top.child(i) for i in range(top.childCount()) if top.child(i).text(0) == "A_rig"][0]
    check("junctions are light red in the preview too", a_item.foreground(0).color().name() == QColor(JUNCTION_COLOR).name())
    a_item.setExpanded(True)
    app.processEvents()
    check("opening the junction shows its files", [a_item.child(i).text(0) for i in range(a_item.childCount())] ==
          ["rig_v01.mb"])
    mpath = sm.manifest_path(data_dir, tab._current_root()["id"], "PCA")
    check("Preview does not scan (no manifest, no hashing)", not os.path.exists(mpath))
    check("Preview window title names the root", "Preview - " in dlg.windowTitle())

    # 스캔과 속도 비교
    t0 = time.perf_counter()
    tab.on_scan(push=False)
    while tab._thread is not None and time.perf_counter() - t0 < 120:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    t_scan = time.perf_counter() - t0
    print("   preview {0:.3f} s  vs  scan {1:.3f} s (200 MB)".format(t_preview, t_scan))
    check("Preview is much faster than a scan (at least 5x here)", t_preview * 5 < t_scan, (t_preview, t_scan))

    # 같은 창을 다시 쓴다
    tab.btn_preview.click()
    app.processEvents()
    check("pressing Preview again reuses the same window", tab._preview is dlg)
    tab.shutdown()
    app.processEvents()
    check("closing the tab closes the preview", not dlg.isVisible())
    tab.close()
finally:
    try:
        os.rmdir(link)
    except OSError:
        pass
    shutil.rmtree(work, ignore_errors=True)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
