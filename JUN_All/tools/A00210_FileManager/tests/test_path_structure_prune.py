# -*- coding: utf-8 -*-
# A00210_FileManager v01.59 - Path Structure : 체크 해제한 폴더는 그 하위 전부도 Recreate 하지 않는다.
#   python test_path_structure_prune.py   (표준 python, 오프스크린)
import os
import sys
import shutil
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

from Framework.qt.qt import QApplication, Qt   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)

from tools.A00210_FileManager.app.core import path_structure as ps   # noqa: E402
from tools.A00210_FileManager.app.ui import path_structure_tab as pst   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ---------------------------------------------------------------- core
rels = ["a", "a/b", "a/b/c", "ab", "x", "x/y"]
check("C1 excluded folder drops all its descendants", ps.prune_excluded(rels, {"a"}) == ["ab", "x", "x/y"],
      ps.prune_excluded(rels, {"a"}))
check("C2 'a' does not drop sibling 'ab'", "ab" in ps.prune_excluded(rels, {"a"}))
check("C3 deep exclusion keeps the parent", ps.prune_excluded(rels, {"a/b"}) == ["a", "ab", "x", "x/y"])
check("C4 files under an excluded folder dropped",
      ps.prune_excluded(["a/f.ma", "a/b/g.ma", "x/h.ma"], {"a"}) == ["x/h.ma"])
check("C5 nothing excluded -> unchanged", ps.prune_excluded(rels, set()) == rels)
check("C6 excluded file only drops itself", ps.prune_excluded(["a/f.ma", "a/g.ma"], {"a/f.ma"}) == ["a/g.ma"])

# ---------------------------------------------------------------- UI : 실제 Recreate
TMP = tempfile.mkdtemp(prefix="jun_a00210_prune_").replace("\\", "/")
STORE = TMP + "/store"
OUT = TMP + "/out"
os.makedirs(STORE)
os.makedirs(OUT)
ps.save(STORE, ps.PathStructure(name="S", folders=["a", "a/b", "a/b/c", "ab", "x"],
                                files=["a/b/f.ma", "x/g.ma"], max_depth=0))

pst.QMessageBox.information = staticmethod(lambda *a, **k: None)
LOG = []
# v01.60 : 라이브러리 = PC 단위 설정의 repo_dir (프로파일 store_dir 은 첫 시드로만). 설정 파일은 임시 경로.
from tools.A00210_FileManager.app.core import library_settings as LS   # noqa: E402
LS.SETTINGS_PATH = TMP + "/structure_library.json"
tab = pst.PathStructureTab(lambda: None, lambda: "", lambda: {"store_dir": STORE}, LOG.append)
tab.on_refresh(select="S")
tab.on_select_structure()
tab.ipf_recreate_to.setText(OUT)
tree = tab.tree_preview


def item_of(rel):
    found = []

    def walk(parent):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == rel:
                found.append(child)
            walk(child)

    walk(tree.invisibleRootItem())
    return found[0]


item_of("a").setCheckState(0, Qt.Unchecked)          # 상위만 해제, 아래(a/b, a/b/c, a/b/f.ma)는 체크된 채
check("U1 children keep their own check", item_of("a/b").checkState(0) == Qt.Checked
      and item_of("a/b/c").checkState(0) == Qt.Checked)
check("U2 children under the unchecked folder are greyed with a tooltip",
      item_of("a/b").toolTip(0) == tab._BLOCKED_TIP and item_of("a/b/f.ma").toolTip(0) == tab._BLOCKED_TIP
      and item_of("ab").toolTip(0) != tab._BLOCKED_TIP)
tab.on_recreate()
made = sorted(os.path.relpath(os.path.join(d, n), OUT).replace("\\", "/")
              for d, ds, fs in os.walk(OUT) for n in ds + fs)
check("U3 Recreate skips the unchecked folder and everything under it",
      made == ["ab", "x", "x/g.ma" + ps.RECREATED_SUFFIX], made)

item_of("a").setCheckState(0, Qt.Checked)
check("U4 checking the parent again clears the grey", item_of("a/b").toolTip(0) == "")
item_of("a/b").setCheckState(0, Qt.Unchecked)
shutil.rmtree(OUT)
os.makedirs(OUT)
tab.on_recreate()
made = sorted(os.path.relpath(os.path.join(d, n), OUT).replace("\\", "/")
              for d, ds, fs in os.walk(OUT) for n in ds + fs)
check("U5 unchecking a/b keeps a, drops a/b/c and a/b/f.ma",
      made == ["a", "ab", "x", "x/g.ma" + ps.RECREATED_SUFFIX], made)

tab.close()
shutil.rmtree(TMP, ignore_errors=True)
ok = sum(R)
print("\nRESULT: {0}/{1} passed".format(ok, len(R)))
sys.exit(0 if ok == len(R) else 1)
