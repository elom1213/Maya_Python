# -*- coding: utf-8 -*-
# A00210_FileManager v01.55 - Sync 가 정션을 따라 들어가는지 · 정션 표시 (실제 정션, 오프스크린)
#   python test_sync_junctions.py
# 사용자: C:\JUN 을 스캔하면 평범한 폴더는 되는데 정션 폴더 · 그 안 파일이 안 나온다 → 정션도 스캔 + A00240 Tree 처럼 연한 빨강.
#
# 구조 (mklink /J - 관리자 권한 불필요):
#   root/plain/a.txt                 평범한 폴더
#   root/A_proj          -> T1       정션 (깊이 1)        T1/x.ma, T1/deep/y.mb
#   root/sub/B_again     -> T1       같은 대상 정션 (깊이 2) - 한 번만 센다 (얕은 A_proj 가 이긴다)
#   root/loop            -> root     위를 가리키는 순환 정션 - 들어가지 않는다
#   root/C_empty         -> T2       빈 대상
import os
import shutil
import subprocess
import sys
import tempfile
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, QMessageBox, QColor  # noqa: E402
app = QApplication.instance() or QApplication([])
from Framework.core import tree_scanner  # noqa: E402
from Framework.qt.MOD_fileTree_qt_v01 import JUNCTION_COLOR  # noqa: E402
from tools.A00210_FileManager.app.core import sync_settings as ss  # noqa: E402
from tools.A00210_FileManager.app.core import sync_manifest as sm  # noqa: E402
from tools.A00210_FileManager.app.ui import sync_tab as st  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra != "" else ""))


def write(path, data=b"x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def junction(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    subprocess.run(["cmd", "/c", "mklink", "/J", link, target], check=True, capture_output=True)


work = tempfile.mkdtemp(prefix="a00210_junc_")
root = os.path.join(work, "JUN")
t1 = os.path.join(work, "target1")
t2 = os.path.join(work, "target2")
try:
    write(os.path.join(root, "plain", "a.txt"))
    write(os.path.join(t1, "x.ma"), b"scene")
    write(os.path.join(t1, "deep", "y.mb"), b"rig")
    os.makedirs(t2)
    junction(os.path.join(root, "A_proj"), t1)
    junction(os.path.join(root, "sub", "B_again"), t1)
    junction(os.path.join(root, "loop"), root)
    junction(os.path.join(root, "C_empty"), t2)

    # ---- 판별 (Framework tree_scanner - A00240 Tree 와 같은 것)
    is_j, target = tree_scanner.junction_info(os.path.join(root, "A_proj"))
    check("junction_info: a junction and where it points", is_j and os.path.normcase(target) == os.path.normcase(t1),
          target)
    check("junction_info: a plain folder is not", tree_scanner.junction_info(os.path.join(root, "plain")) == (False, ""))

    # ---- 스캔 (기본 = 정션을 따라 들어간다)
    dups = []
    dirs = []
    files, errors = sm.list_files(root, dirs_out=dirs, duplicates_out=dups)
    rels = [f[0] for f in files]
    check("plain folder files are found", "plain/a.txt" in rels)
    check("files inside a junction are found (the bug)", "A_proj/x.ma" in rels and "A_proj/deep/y.mb" in rels, rels)
    check("the same real folder reached twice is counted once (shallower path wins)",
          not any(r.startswith("sub/B_again/") for r in rels) and ("sub/B_again", "A_proj") in dups, dups)
    check("a junction pointing back up (loop) is not entered", not any(r.startswith("loop/") for r in rels) and
          ("loop", "") in dups, dups)
    check("an empty junction target is still a folder (empty dir record)", "C_empty" in dirs)
    check("no errors", errors == [], errors)
    files2, _ = sm.list_files(root, duplicates_out=[])
    check("same order every time (breadth first, by name - same on every PC)", [f[0] for f in files2] == rels)
    manifest, report = sm.scan(root, "jun", "PCA")
    check("scan(): junction files in the manifest, duplicates in the report",
          "A_proj/deep/y.mb" in manifest["files"] and len(report["duplicates"]) == 2 and "C_empty" in manifest["empty_dirs"],
          report["duplicates"])
    files3, _ = sm.list_files(root, follow_junctions=False)
    check("Skip junctions = the old behaviour (junction folders skipped)",
          [f[0] for f in files3] == ["plain/a.txt"], [f[0] for f in files3])

    # ---- 설정
    check("new root: skip_junctions off (junctions followed)", ss.new_root("JUN", root)["skip_junctions"] is False and
          "follow_junctions" not in ss.new_root("JUN", root))

    # ---- UI: Sync 탭이 실제로 스캔하고 정션을 연한 빨강으로
    data_dir = os.path.join(work, "data")
    os.makedirs(data_dir)
    QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
    LOG = []
    tab = st.SyncTab(get_data_dir=lambda: data_dir, get_project_root=lambda: root.replace("\\", "/"),
                     is_git_mode=lambda: False, git_pull=lambda: True, git_push=lambda msg: True,
                     get_author=lambda: "tester", log=LOG.append)
    tab._pc = "PCA"
    tab.load_prefs({})                               # 설정 읽기 - 기본 루트 = Project Root (test_sync_ui 와 같다)
    tab.resize(1000, 700)
    tab.show()
    app.processEvents()
    check("UI: option reads 'Skip junctions inside this root', off", tab.chk_follow.text() == "Skip junctions inside this root"
          and not tab.chk_follow.isChecked())
    tab.on_scan(push=False)
    t0 = time.time()
    while tab._thread is not None and time.time() - t0 < 30:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    for cb in tab.chk_show.values():
        cb.setChecked(True)
    tab._populate_tree()
    items = {}
    stack = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())]
    while stack:
        it = stack.pop()
        items[it.data(0, st.ROLE_REL)] = it
        stack += [it.child(i) for i in range(it.childCount())]
    check("UI Status: the junction folder and its files show up", "A_proj/" in items and "A_proj/deep/y.mb" in items,
          sorted(k for k in items if k)[:12])
    jc = QColor(JUNCTION_COLOR).name()
    a_item = items.get("A_proj/")
    check("UI Status: the junction folder is light red with 'Junction ->' tooltip (like A00240 Tree)",
          a_item is not None and a_item.foreground(0).color().name() == jc and "Junction -> " in a_item.toolTip(0) and
          a_item.data(0, st.ROLE_JUNCTION))
    p_item = items.get("plain/")
    check("UI Status: a plain folder keeps its normal color", p_item is not None and not p_item.data(0, st.ROLE_JUNCTION)
          and p_item.foreground(0).color().name() != jc)
    check("UI log: tells that a folder was counted once", any("counted once" in m for m in LOG), LOG[-3:])
    tab._reload_excl_tree()
    ex = {tab.excl_tree.topLevelItem(i).text(0): tab.excl_tree.topLevelItem(i)
          for i in range(tab.excl_tree.topLevelItemCount())}
    check("UI Excluded tree: junctions light red too, plain folder not",
          ex["A_proj"].foreground(0).color().name() == jc and ex["loop"].foreground(0).color().name() == jc and
          ex["plain"].foreground(0).color().name() != jc and "Junction ->" in ex["A_proj"].toolTip(0))
    tab.chk_follow.setChecked(True)
    check("UI: ticking Skip saves skip_junctions", tab._current_root()["skip_junctions"] is True)
    tab.shutdown()
    tab.close()
    app.processEvents()
finally:
    for link in (os.path.join(root, "A_proj"), os.path.join(root, "sub", "B_again"), os.path.join(root, "loop"),
                 os.path.join(root, "C_empty")):
        try:
            os.rmdir(link)                       # 정션만 지운다 (대상은 그대로) - rmtree 가 정션 안을 지우지 않게
        except OSError:
            pass
    shutil.rmtree(work, ignore_errors=True)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
