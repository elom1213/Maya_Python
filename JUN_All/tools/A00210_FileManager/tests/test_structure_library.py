# -*- coding: utf-8 -*-
# A00210_FileManager v01.60 - Path Structure 라이브러리 독립 (프로파일 무관 · 카테고리 · 탭 전용 Pull/Push · 이전 스크립트)
#   python test_structure_library.py   (표준 python, 오프스크린, 임시 폴더 + 로컬 bare git 원격)
#   계획 docs/plans/A00210_FileManager_structure_library_plan.md 5장
import os
import sys
import json
import shutil
import tempfile
import subprocess

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

from Framework.qt.qt import QApplication, Qt   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)

from tools.A00210_FileManager.app.core import path_structure as ps        # noqa: E402
from tools.A00210_FileManager.app.core import structure_library as L      # noqa: E402
from tools.A00210_FileManager.app.core import library_settings as LS      # noqa: E402
from tools.A00210_FileManager.app.core import prefs as P                  # noqa: E402
from tools.A00210_FileManager.app.core.git_sync import GitSync            # noqa: E402
from tools.A00210_FileManager.app.config import data_repo                 # noqa: E402
from tools.A00210_FileManager.dev import migrate_structure_library as MIG  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


TMP = tempfile.mkdtemp(prefix="jun_a00210_lib_").replace("\\", "/")


def git(cwd, *args):
    p = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode == 0, ((p.stdout or "") + (p.stderr or "")).strip()


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def struct(name, cat="", folders=("a", "a/b")):
    return ps.PathStructure(name=name, folders=list(folders), files=["a/x.ma"], category=cat,
                            created_at="2026-11-27 00:00:00")


# ================================================================ L : library core
REPO = TMP + "/lib_repo"
os.makedirs(REPO)
lib = L.StructureLibrary(REPO)
check("L1 empty library", lib.list_categories() == [] and lib.grouped() == [])

c1 = lib.create_category("Character", author="me")
check("L2 category file + 8 hex id", os.path.isfile(os.path.join(REPO, "path_structures", "_categories", c1.id + ".json"))
      and len(c1.id) == 8 and all(ch in "0123456789abcdef" for ch in c1.id), c1)
try:
    lib.create_category("character")
    dup = False
except ValueError:
    dup = True
check("L3 duplicate name (case-insensitive) refused", dup)
try:
    lib.create_category("Uncategorized")
    res = False
except ValueError:
    res = True
check("L3b reserved name refused", res)

lib.save(struct("S1", c1.id))
lib.save(struct("S2", c1.id))
s1_before = read(ps.struct_path(REPO, "S1"))
lib.rename_category(c1.id, "Chars")
check("L4 rename category touches only the category file",
      read(ps.struct_path(REPO, "S1")) == s1_before and lib.get_category(c1.id).name == "Chars")
check("L5 list_structures gives (name, id)", lib.list_structures() == [("S1", c1.id), ("S2", c1.id)], lib.list_structures())

lib.save(struct("Lost", "deadbeef"))
g = lib.grouped()
check("L6 unknown id -> Uncategorized, last", g[-1][0] is None and g[-1][1] == ["Lost"], g)

c2 = lib.create_category("Env")
lib.save(struct("E1", c2.id))
moved = lib.delete_category(c2.id, mode="move")
check("L7 delete category (move) keeps structure as Uncategorized",
      moved == ["E1"] and lib.exists("E1") and lib.category_of("E1") == L.UNCATEGORIZED
      and lib.get_category(c2.id) is None)

c3 = lib.create_category("Tmp")
lib.save(struct("T1", c3.id))
lib.save(struct("T2", c3.id))
gone = lib.delete_category(c3.id, mode="delete")
check("L8 delete category (delete) removes its structures", sorted(gone) == ["T1", "T2"]
      and not lib.exists("T1") and not lib.exists("T2"))

before = json.loads(read(ps.struct_path(REPO, "E1")))
lib.set_category(["E1", "Lost"], c1.id)
after = json.loads(read(ps.struct_path(REPO, "E1")))
check("L9 set_category moves several, keeps other fields",
      lib.category_of("E1") == c1.id and lib.category_of("Lost") == c1.id
      and {k: v for k, v in after.items() if k != "category"} == {k: v for k, v in before.items() if k != "category"})

lib.rename("E1", "E1_renamed")
check("L10 structure rename keeps category", lib.category_of("E1_renamed") == c1.id)

write_json(os.path.join(REPO, "path_structures", "_junk.json"), {"name": "junk"})
check("L11 _categories folder and _*.json are not structures",
      all(not n.startswith("_") for n, _ in lib.list_structures()) and "junk" not in [n for n, _ in lib.list_structures()])

write_json(os.path.join(REPO, "profiles", "Dnable", "path_structures", "Old.json"), struct("Old").to_dict())
lg = lib.legacy_files()
check("L12 legacy_files finds profiles/*/path_structures", len(lg) == 1 and lg[0][0] == "Dnable", lg)

check("L13 old JSON without category -> Uncategorized",
      ps.PathStructure.from_dict({"name": "x", "folders": []}).category == "")
check("L14 empty categories still listed", any(c.id == c1.id for c, _ in lib.grouped()))

# ================================================================ S : PC settings
SP = TMP + "/settings/structure_library.json"
s = LS.load({"source_mode": "git", "store_dir": "D:\\data\\repo", "recreate_to": "E:\\out\\"}, path=SP)
check("S1 seed from git profile", s["repo_dir"] == "D:/data/repo" and s["recreate_to"] == "E:/out" and os.path.isfile(SP), s)
SP2 = TMP + "/settings2/structure_library.json"
s2 = LS.load({"source_mode": "local", "store_dir": "D:/x", "local_dir": "//nas/x"}, path=SP2)
check("S2 seed from local profile -> bundled default clone",
      s2["repo_dir"] == P.ui_path(data_repo.DEFAULT_STORE_DIR), s2["repo_dir"])
s["recreate_to"] = "F:\\new"
LS.save(s, path=SP)
s3 = LS.load({"store_dir": "IGNORED"}, path=SP)
check("S3 round trip, seed ignored once the file exists", s3["recreate_to"] == "F:/new" and s3["repo_dir"] == "D:/data/repo", s3)

# ================================================================ G : git (bare remote + PC A / PC B)
REMOTE = TMP + "/remote.git"
git(TMP, "init", "--bare", "-b", "main", REMOTE)
SEED = TMP + "/seed"
git(TMP, "clone", REMOTE, SEED)
for cwd in (SEED,):
    git(cwd, "config", "user.name", "t"); git(cwd, "config", "user.email", "t@t")
git(SEED, "checkout", "-B", "main")
write_json(SEED + "/profiles/Dnable/records/r.json", {"v": 1})
write_json(SEED + "/profiles/Dnable/path_structures/Dnable_CH.json", struct("Dnable_CH").to_dict())
write_json(SEED + "/profiles/Dnable/path_structures/UE_Set.json", struct("UE_Set").to_dict())
write_json(SEED + "/profiles/MUE/path_structures/Test.json", dict(struct("test").to_dict(), name="test"))
write_json(SEED + "/profiles/JUN/path_structures/Dnable_CH.json", struct("Dnable_CH").to_dict())   # 이름 충돌 (M5)
git(SEED, "add", "-A"); git(SEED, "commit", "-m", "seed"); git(SEED, "push", "-u", "origin", "main")

A = TMP + "/pcA"
B = TMP + "/pcB"
for d in (A, B):
    git(TMP, "clone", REMOTE, d)
    git(d, "config", "user.name", "t"); git(d, "config", "user.email", "t@t")

# ---------------- M : migration (on PC A)
write_json(A + "/profiles/Dnable/records/r.json", {"v": 2})            # 다른 작업의 미커밋 records (M6)
rc = MIG.main([A, "--no-pull"])
ok_st, st = git(A, "status", "--porcelain", "--", "path_structures", "profiles/*/path_structures")
ok_log, n_commits = git(A, "rev-list", "--count", "HEAD")
check("M1 dry-run changes nothing", rc == 0 and st == "" and n_commits.strip() == "1", (rc, st, n_commits))

rc = MIG.main([A, "--apply", "--no-pull", "--author", "tester"])
libA = L.StructureLibrary(A)
names = {c.name for c in libA.list_categories()}
ents = dict(libA.list_structures())
check("M2 apply: moved, categories = folder names, one commit",
      rc == 0 and not libA.legacy_files() and names == {"Dnable", "JUN", "MUE"}
      and git(A, "rev-list", "--count", "HEAD")[1].strip() == "2", (rc, names, ents))
cat_by_name = {c.name: c.id for c in libA.list_categories()}
check("M2b each structure's category matches its old folder",
      ents.get("UE_Set") == cat_by_name["Dnable"] and ents.get("test") == cat_by_name["MUE"], ents)
ok, follow = git(A, "log", "--follow", "--format=%s", "--", "path_structures/UE_Set.json")
check("M3 history follows the move", "seed" in follow, follow)
check("M5 name clash -> <stem>_<folder>", "Dnable_CH" in ents and "Dnable_CH_JUN" in ents
      and os.path.isfile(A + "/path_structures/Dnable_CH_JUN.json"), sorted(ents))
ok, show = git(A, "show", "--stat", "--format=", "HEAD")
check("M6 records change not in the migration commit, still uncommitted",
      "records" not in show and "profiles/Dnable/records/r.json" in git(A, "status", "--porcelain", "--", "profiles/Dnable/records")[1], show)
rc = MIG.main([A, "--apply", "--no-pull"])
check("M4 re-run = nothing to migrate", rc == 0 and git(A, "rev-list", "--count", "HEAD")[1].strip() == "2")
write_json(A + "/profiles/MUE/path_structures/Late.json", struct("Late").to_dict())
git(A, "add", "--", "profiles/MUE/path_structures"); git(A, "commit", "-m", "late old-version save")
rc = MIG.main([A, "--apply", "--no-pull"])
check("M4b late legacy file migrated, category reused",
      rc == 0 and libA.category_of("Late") == cat_by_name["MUE"] and len(libA.list_categories()) == 3)

# ---------------- G : scoped push / pull
cA = libA.create_category("FromA")
gitA = GitSync(A, "origin", "main", scope_rel="path_structures")
gitB = GitSync(B, "origin", "main", scope_rel="path_structures")
ok, out = gitA.push("lib push A")
ok_r, remote_files = git(SEED, "pull"); remote_ls = git(SEED, "ls-files")[1]
check("G1 push sends path_structures (and the migration commit), not the uncommitted records",
      ok and "path_structures/_categories/" + cA.id + ".json" in remote_ls
      and "profiles/Dnable/records/r.json" in git(A, "status", "--porcelain", "--", "profiles/Dnable/records")[1]
      and json.loads(read(SEED + "/profiles/Dnable/records/r.json"))["v"] == 1, out)
ok, out = gitB.pull()
libB = L.StructureLibrary(B)
check("G2 PC B pull sees structures + categories", ok and libB.exists("UE_Set") and libB.get_category(cA.id) is not None, out)

cA2 = libA.create_category("A_side")
cB2 = libB.create_category("B_side")
okA, outA = gitA.push("A cat")
okB, outB = gitB.push("B cat")       # 거절 -> 다시 받고 재시도
git(SEED, "pull")
ls = git(SEED, "ls-files")[1]
check("G3 two PCs add categories at once -> both land, no conflict",
      okA and okB and cA2.id in ls and cB2.id in ls, outB)

sA = libA.load("UE_Set"); sA.folders = ["A_only"]; libA.save(sA)
okA, outA = gitA.push("A edits UE_Set")
sB = libB.load("UE_Set"); sB.folders = ["B_only"]; libB.save(sB)
okB, outB = gitB.push("B edits UE_Set")
check("G4 same structure edited on both -> push fails, rebase aborted, local edit kept",
      okA and not okB and "aborted" in outB and not gitB._rebase_in_progress()
      and libB.load("UE_Set").folders == ["B_only"], outB)

g_old = GitSync(A, "origin", "main", data_folder="Dnable")
check("G5 data_folder GitSync unchanged", g_old.data_rel == "profiles/Dnable" and gitA.data_rel == "path_structures")
gs = GitSync(TMP + "/fresh_scope", "origin", "main", scope_rel="path_structures")
os.makedirs(gs.store_dir)
gs.ensure_repo("")
check("G6 scoped skeleton does not make records/thumbs",
      os.path.isdir(gs.store_dir + "/path_structures") and not os.path.isdir(gs.store_dir + "/profiles")
      and not os.path.isdir(gs.store_dir + "/path_structures/records"))

# ================================================================ U : UI (MainWindow, temp prefs)
P.PREFS_DIR = TMP + "/prefs"
P.PROFILES_DIR = P.PREFS_DIR + "/profiles"
P.ACTIVE_PATH = P.PREFS_DIR + "/active.json"
P.PREFS_PATH = P.PREFS_DIR + "/prefs.json"
LS.SETTINGS_PATH = None                            # 호출 시점 PREFS_DIR 아래
os.makedirs(P.PROFILES_DIR)
UI_REPO = TMP + "/pcA"                             # 이전 끝난 클론
P.save_profile("Local_CH_D", {"store_dir": UI_REPO, "data_folder": "Dnable", "recreate_to": TMP + "/out"})
P.save_profile("JUN", {"store_dir": UI_REPO, "data_folder": "JUN"})
P.save_profile("NAS", {"source_mode": "local", "local_dir": TMP + "/nas", "store_dir": UI_REPO})
P.set_active("Local_CH_D")

from tools.A00210_FileManager.app.ui import main_window as mw          # noqa: E402
from tools.A00210_FileManager.app.ui import path_structure_tab as pst  # noqa: E402

ANSWERS = {}
pst.QInputDialog.getText = staticmethod(lambda *a, **k: (ANSWERS.pop("text"), True))
pst.QInputDialog.getItem = staticmethod(lambda *a, **k: (ANSWERS.pop("item"), True))
pst.QMessageBox.question = staticmethod(lambda *a, **k: pst.QMessageBox.Yes)
pst.QMessageBox.information = staticmethod(lambda *a, **k: None)
pst.QMessageBox.warning = staticmethod(lambda *a, **k: None)

win = mw.MainWindow()
tab = win.path_structure_tab
tree = tab.tree_structs


def snapshot():
    out = []
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        out.append((top.text(0), [top.child(j).text(0) for j in range(top.childCount())]))
    return out


def find(kind, key):
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        if tuple(top.data(0, Qt.UserRole)) == (kind, key):
            return top
        for j in range(top.childCount()):
            ch = top.child(j)
            if tuple(ch.data(0, Qt.UserRole)) == (kind, key):
                return ch
    return None


snap0 = snapshot()
cats_shown = [t.split("  (")[0] for t, _ in snap0]
check("U1 tree: categories on top, sorted, children = structures",
      cats_shown == sorted(cats_shown, key=str.lower) and any("UE_Set" in ch for _, ch in snap0), snap0)
check("U1b settings seeded from active profile", tab.library().repo_dir.replace("\\", "/") == UI_REPO
      and tab.recreate_to() == TMP + "/out", (tab.library().repo_dir, tab.recreate_to()))

tree.setCurrentItem(find(pst.KIND_STRUCT, "UE_Set"))
win.cmb_data_folder.setCurrentText("JUN")
win._on_data_folder_committed()
win.on_profile_changed("JUN")
check("U2 profile / data folder change: tree and selection unchanged",
      snapshot() == snap0 and tab._selected_name() == "UE_Set", (snapshot(), tab._selected_name()))
win.on_profile_changed("NAS")
check("U3 local-mode profile: tree unchanged, Recreate To unchanged",
      snapshot() == snap0 and tab.recreate_to() == TMP + "/out")

ANSWERS["text"] = "Character"
tab.on_new_category()
cat = tab.library().find_category("Character")
check("U4 New Category creates + selects it", cat is not None and tab._current_info() == (pst.KIND_CAT, cat.id))
ANSWERS["text"] = "Characters"
tab.on_rename()
check("U5 Rename on a category renames the category", tab.library().get_category(cat.id).name == "Characters")

tree.clearSelection()
it1, it2 = find(pst.KIND_STRUCT, "UE_Set"), find(pst.KIND_STRUCT, "Dnable_CH")
tree.setCurrentItem(it1)
it2.setSelected(True)
ANSWERS["item"] = "Characters"
tab.on_move_to()
check("U7 Move To moves the selected structures", tab.library().category_of("UE_Set") == cat.id
      and tab.library().category_of("Dnable_CH") == cat.id)

tree.setCurrentItem(find(pst.KIND_STRUCT, "Dnable_CH"))
ANSWERS["text"] = "Dnable_CH2"
tab.on_rename()
check("U5b Rename on a structure renames the structure, keeps category",
      tab.library().exists("Dnable_CH2") and tab.library().category_of("Dnable_CH2") == cat.id)

check("U8 Category combo follows the selected structure's category", tab.cmb_category.currentData() == cat.id)
SRC = TMP + "/src_base"
os.makedirs(SRC + "/top/sub")
tab.ipf_base.setText(SRC)
tab._scan_folders()
tab.on_capture()
tab.ipf_name.setText("NewOne")
tab.cmb_category.setCurrentIndex(tab.cmb_category.findData(cat.id))
tab.on_save()
check("U8b saved in the chosen category and selected", tab.library().category_of("NewOne") == cat.id
      and tab._selected_name() == "NewOne")

tree.setCurrentItem(find(pst.KIND_CAT, cat.id))
check("U9 category selected -> preview empty", tab._cur_structure is None and tab.tree_preview.topLevelItemCount() == 0)

# U6 : 카테고리 삭제 3지선다 (QMessageBox 인스턴스 - exec_/clickedButton 대체)
WANT = {"text": ""}
orig_exec, orig_clicked = pst.QMessageBox.exec_, pst.QMessageBox.clickedButton
pst.QMessageBox.exec_ = lambda self: 0
pst.QMessageBox.clickedButton = lambda self: next((b for b in self.buttons() if b.text() == WANT["text"]), None)
WANT["text"] = "Cancel"
tab.on_delete()
check("U6a Cancel keeps the category", tab.library().get_category(cat.id) is not None)
WANT["text"] = "Move to Uncategorized"
tab.on_delete()
check("U6b Move to Uncategorized", tab.library().get_category(cat.id) is None and tab.library().exists("NewOne")
      and tab.library().category_of("NewOne") == L.UNCATEGORIZED)
check("U10 Uncategorized selected -> Rename / Delete disabled",
      tab._current_info() == (pst.KIND_CAT, pst.UNCAT_KEY) and not tab.btn_rename.isEnabled() and not tab.btn_delete.isEnabled())
ANSWERS["text"] = "Doomed"
tab.on_new_category()
doomed = tab.library().find_category("Doomed")
tab.library().set_category(["NewOne"], doomed.id)
tab.on_refresh(select_cat=doomed.id)
WANT["text"] = "Delete Structures Too"
tab.on_delete()
check("U6c Delete Structures Too", tab.library().get_category(doomed.id) is None and not tab.library().exists("NewOne"))
pst.QMessageBox.exec_, pst.QMessageBox.clickedButton = orig_exec, orig_clicked

tab.ipf_recreate_to.setText(TMP + "/out2")
tab.ipf_recreate_to.editingFinished.emit()
prof = win._collect_prefs()
check("U11 Recreate To saved per PC, not in the profile",
      json.loads(read(LS.settings_path()))["recreate_to"] == TMP + "/out2" and "recreate_to" not in prof)
check("U13 _collect_prefs has no recreate_to", "recreate_to" not in prof)

write_json(UI_REPO + "/profiles/SA/path_structures/Legacy.json", struct("Legacy").to_dict())
tab._legacy_warned = False
n_before = len(win.log_widget.toPlainText())
tab.on_refresh()
tab.on_refresh()
logtxt = win.log_widget.toPlainText()[n_before:]
check("U12 legacy warning once", logtxt.count("old per-profile folders") == 1, logtxt[-300:])
os.remove(UI_REPO + "/profiles/SA/path_structures/Legacy.json")

called = []
tab.on_refresh = lambda *a, **k: called.append(1)


class _FakeGit:
    store_dir = UI_REPO
    branch = "main"
    data_rel = "profiles/Dnable"

    def is_repo(self):
        return True

    def check_branch(self):
        return True, ""

    def pull(self):
        return True, "ok"


win.on_profile_changed("Local_CH_D")
win._make_git = lambda: _FakeGit()
win.on_pull()
check("U14 File Manager Pull refreshes the Path Structure list", called == [1], called)
del tab.on_refresh
win.close()

ok = sum(R)
print("\nRESULT: {0}/{1} passed".format(ok, len(R)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if ok == len(R) else 1)
