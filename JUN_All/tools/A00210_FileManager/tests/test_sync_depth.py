# -*- coding: utf-8 -*-
# A00210_FileManager v01.56 - Sync 스캔 깊이 (오프스크린)   python test_sync_depth.py
# 사용자: Sync > Status 에서 깊이를 정해 스캔하고 싶다(지금은 모든 깊이).
#   root/top.txt                  깊이 0 (루트의 파일)
#   root/a/a1.txt                 폴더 깊이 1
#   root/a/b/b1.txt               폴더 깊이 2
#   root/a/b/c/c1.txt             폴더 깊이 3
#   root/only_sub/x/deep.txt      깊이 1 폴더에는 파일이 없고 하위 폴더만 - 깊이 1 로 보면 빈 폴더가 아니다
#   root/empty/                   진짜 빈 폴더 (깊이 1)
import json
import os
import shutil
import sys
import tempfile
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, QMessageBox  # noqa: E402
app = QApplication.instance() or QApplication([])
from tools.A00210_FileManager.app.core import sync_settings as ss  # noqa: E402
from tools.A00210_FileManager.app.core import sync_manifest as sm  # noqa: E402
from tools.A00210_FileManager.app.core import sync_compare as sc  # noqa: E402
from tools.A00210_FileManager.app.ui import sync_tab as st  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra != "" else ""))


def write(root, rel, data=b"x"):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)


work = tempfile.mkdtemp(prefix="a00210_depth_")
root = os.path.join(work, "JUN")
try:
    for rel in ("top.txt", "a/a1.txt", "a/b/b1.txt", "a/b/c/c1.txt", "only_sub/x/deep.txt"):
        write(root, rel)
    os.makedirs(os.path.join(root, "empty"))

    # ---- 코어
    def rels(depth):
        files, _ = sm.list_files(root, max_depth=depth)
        return [f[0] for f in files]
    check("depth All (0) = every file", rels(0) == ["a/a1.txt", "a/b/b1.txt", "a/b/c/c1.txt", "only_sub/x/deep.txt", "top.txt"],
          rels(0))
    check("depth 1 = the root files and the files of its folders", rels(1) == ["a/a1.txt", "top.txt"], rels(1))
    check("depth 2 = one level deeper", rels(2) == ["a/a1.txt", "a/b/b1.txt", "only_sub/x/deep.txt", "top.txt"], rels(2))
    m1, rep1 = sm.scan(root, "jun", "PCA", max_depth=1)
    check("depth 1 manifest: records the depth", m1["depth"] == 1 and set(m1["files"]) == {"a/a1.txt", "top.txt"})
    check("depth 1: a folder with only unscanned subfolders is not called empty, a real empty folder is",
          "only_sub" not in m1["empty_dirs"] and "a" not in m1["empty_dirs"] and "empty" in m1["empty_dirs"],
          m1["empty_dirs"])
    m0, _ = sm.scan(root, "jun", "PCB")
    check("depth All manifest: depth 0", m0["depth"] == 0 and "a/b/c/c1.txt" in m0["files"])
    check("within_depth rules", ss.within_depth("a/b/c.mb", 2) and not ss.within_depth("a/b/c/d.mb", 2) and
          ss.within_depth("a/b", 2, is_dir=True) and not ss.within_depth("a/b/c", 2, is_dir=True) and
          ss.within_depth("anything/deep/x", 0))
    check("clean_depth", ss.clean_depth("3") == 3 and ss.clean_depth(-1) == 0 and ss.clean_depth(500) == 99 and
          ss.clean_depth(None) == 0)

    # ---- 비교: 다른 PC(B)는 전부 스캔, 이 PC(A)는 깊이 1 - 깊이 1 로 비교하면 거짓 Missing 이 없다
    rows_all = sc.compare({"PCA": m1, "PCB": m0}, "PCA")
    check("without depth in the compare, B's deeper files look Missing on A (the problem)",
          any(r.rel == "a/b/c/c1.txt" and r.status == sc.MISSING for r in rows_all))
    rows1 = sc.compare({"PCA": m1, "PCB": m0}, "PCA", depth=1)
    check("compare with the shared depth: only files within it, all OK (no false Missing)",
          sorted(r.rel for r in rows1) == ["a/a1.txt", "top.txt"] and all(r.status == sc.OK for r in rows1),
          [(r.rel, r.status) for r in rows1])
    dirs1 = sc.empty_dirs({"PCA": m1, "PCB": m0}, "PCA", rows=rows1, depth=1)
    check("empty folders compare within the depth", [d.rel for d in dirs1] == ["empty"], [d.rel for d in dirs1])

    # ---- 설정
    check("new root: scan depth All (0)", ss.new_root("JUN", root)["scan_depth"] == 0)

    # ---- UI
    data_dir = os.path.join(work, "data")
    os.makedirs(data_dir)
    QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
    LOG = []
    tab = st.SyncTab(get_data_dir=lambda: data_dir, get_project_root=lambda: root.replace("\\", "/"),
                     is_git_mode=lambda: False, git_pull=lambda: True, git_push=lambda msg: True,
                     get_author=lambda: "tester", log=LOG.append)
    tab._pc = "PCA"
    tab.load_prefs({})
    tab.resize(1000, 700)
    tab.show()
    app.processEvents()
    check("UI: 'Scan depth' box shows All by default", tab.spn_depth.value() == 0 and tab.spn_depth.text() == "All")
    tab.spn_depth.setValue(2)
    check("UI: changing the depth saves it in the shared settings", tab._current_root()["scan_depth"] == 2 and
          any("scan depth = 2" in m for m in LOG))
    tab.on_scan(push=False)
    t0 = time.time()
    while tab._thread is not None and time.time() - t0 < 30:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    man = sm.load_manifest(sm.manifest_path(data_dir, tab._current_root()["id"], "PCA"))
    check("UI: the scan uses the depth (manifest depth 2, no deeper file)", man and man["depth"] == 2 and
          "a/b/b1.txt" in man["files"] and "a/b/c/c1.txt" not in man["files"], sorted((man or {}).get("files", {})))
    saved = json.load(open(ss.settings_path(data_dir), encoding="utf-8"))
    check("UI: the shared settings file has the depth", saved["roots"][0]["scan_depth"] == 2)
    for cb in tab.chk_show.values():
        cb.setChecked(True)
    tab._populate_tree()
    seen = set()
    stack = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())]
    while stack:
        it = stack.pop()
        seen.add(it.data(0, st.ROLE_REL))
        stack += [it.child(i) for i in range(it.childCount())]
    check("UI Status: no row deeper than the depth", "a/b/b1.txt" in seen and not any(
        r and r.count("/") > 2 and not r.endswith("/") for r in seen), sorted(r for r in seen if r))
    tab.spn_depth.setValue(1)
    app.processEvents()
    seen1 = set()
    stack = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())]
    while stack:
        it = stack.pop()
        seen1.add(it.data(0, st.ROLE_REL))
        stack += [it.child(i) for i in range(it.childCount())]
    check("UI: lowering the depth narrows the Status at once (before scanning again)", "a/b/b1.txt" not in seen1 and
          "a/a1.txt" in seen1, sorted(r for r in seen1 if r))
    tab.spn_depth.setValue(0)
    check("UI: back to All", tab._current_root()["scan_depth"] == 0)
    tab.shutdown()
    tab.close()
    app.processEvents()
finally:
    shutil.rmtree(work, ignore_errors=True)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
