# -*- coding: utf-8 -*-
# A00210_FileManager v01.45 - 데이터 폴더(profiles/<data_folder>) 시험. 표준 python + 임시 폴더 + 로컬 bare 저장소(네트워크 없음).
#   python test_data_folders.py
# 계획서 docs/plans/A00210_FileManager_data_folders_plan.md §3-7 의 1 ~ 6.
import os
import sys
import json
import shutil
import subprocess
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

from tools.A00210_FileManager.app.core import prefs as P   # noqa: E402
from tools.A00210_FileManager.app.core.git_sync import GitSync   # noqa: E402
from tools.A00210_FileManager.app.config import data_repo   # noqa: E402

R = []
TMP = tempfile.mkdtemp(prefix="a00210_df_")


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def git(cwd, *args):
    p = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


# ---------------------------------------------------------------- 1. 옛 프로파일 변환 (이 PC 10개와 같은 값)
BASE = "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/"
PUB = "https://github.com/elom1213/JUN_FileManager_data.git"
PRIV = "https://github.com/elom1213/JUN_FileManager_data_Private.git"
cases = {
    "Default": ({"store_dir": BASE + "JUN_FileManager_data", "branch": "Dnable", "remote_url": PUB}, "Dnable"),
    "HDN": ({"store_dir": BASE + "JUN_FileManager_data", "branch": "Dnable", "remote_url": PUB}, "Dnable"),
    "Local_CH_C": ({"store_dir": BASE.replace("/", "\\") + "JUN_FileManager_data", "branch": "Dnable", "remote_url": PUB}, "Dnable"),
    "NAS_Character": ({"store_dir": BASE + "JUN_FileManager_data", "branch": "Dnable", "remote_url": PUB}, "Dnable"),
    "Rig_Src": ({"store_dir": BASE + "JUN_FileManager_data_all/A0030_Src_Rig", "branch": "src_rig", "remote_url": PUB}, "src_rig"),
    "soundAliance": ({"store_dir": BASE + "JUN_FileManager_data_all/A0020_SA", "branch": "Dnable", "remote_url": PUB}, "SA"),
    "MUE": ({"store_dir": BASE + "JUN_FileManager_data_all/A0010_MEU", "branch": "MUE", "remote_url": PUB}, "MUE"),
    "old_master": ({"store_dir": "", "branch": "master", "remote_url": PUB}, "Dnable"),
}
for name, (raw, want) in cases.items():
    got = P._apply_defaults(raw)
    check("convert {0}: data_folder={1}, branch=main".format(name, want),
          got["data_folder"] == want and got["branch"] == "main", (got["data_folder"], got["branch"]))
got = P._apply_defaults({"store_dir": "x", "branch": "MUE", "remote_url": PRIV})
check("retired private URL -> public URL", got["remote_url"] == data_repo.DATA_REPO_URL, got["remote_url"])
got = P._apply_defaults({"store_dir": BASE + "JUN_FileManager_data_all/A0020_SA", "branch": "Dnable", "data_folder": "Custom"})
check("existing data_folder kept", got["data_folder"] == "Custom", got["data_folder"])
got = P._apply_defaults({"store_dir": "x", "branch": "feature_x", "remote_url": PUB})
check("custom branch kept (not a legacy profile branch)", got["branch"] == "feature_x" and got["data_folder"] == "feature_x",
      (got["branch"], got["data_folder"]))
check("store_dir not changed by conversion",
      P._apply_defaults(cases["MUE"][0])["store_dir"] == cases["MUE"][0]["store_dir"])

# ---------------------------------------------------------------- 2. data_dir_of
check("data_dir_of git", os.path.normpath(P.data_dir_of({"store_dir": "C:/repo", "data_folder": "SA"}))
      == os.path.normpath("C:/repo/profiles/SA"))
check("data_dir_of default folder", P.data_dir_of({"store_dir": "C:/repo"}).replace("\\", "/").endswith("profiles/Dnable"))
check("data_dir_of local = shared folder",
      P.data_dir_of({"source_mode": "local", "local_dir": "//nas/share", "store_dir": "C:/repo"}) == "//nas/share")
check("data_dir_of no store", P.data_dir_of({"store_dir": "", "data_folder": "SA"}) == "")

# ---------------------------------------------------------------- 3 ~ 5. GitSync (로컬 bare 저장소)
bare = os.path.join(TMP, "remote.git")
git(TMP, "init", "--bare", "-b", "main", bare)
seed = os.path.join(TMP, "seed")
git(TMP, "clone", bare, seed)
for who in ("seed",):
    git(seed, "config", "user.name", "t"); git(seed, "config", "user.email", "t@t")
os.makedirs(os.path.join(seed, "profiles", "X", "records"))
open(os.path.join(seed, "profiles", "X", "records", "init.json"), "w").write("{}")
git(seed, "checkout", "-b", "main")
git(seed, "add", "-A"); git(seed, "commit", "-m", "init"); git(seed, "push", "origin", "main")
# 옛 프로파일 브랜치 하나(SA)
git(seed, "checkout", "-b", "SA"); open(os.path.join(seed, "sa.json"), "w").write("{}")
git(seed, "add", "-A"); git(seed, "commit", "-m", "sa"); git(seed, "push", "origin", "SA"); git(seed, "checkout", "main")


def clone(name):
    d = os.path.join(TMP, name)
    git(TMP, "clone", "-b", "main", bare, d)
    git(d, "config", "user.name", name); git(d, "config", "user.email", name + "@t")
    return d


A, B = clone("A"), clone("B")
ga = GitSync(A, "origin", "main", data_folder="X")
gb = GitSync(B, "origin", "main", data_folder="Y")
check("list_data_folders", ga.list_data_folders() == ["X"], ga.list_data_folders())

os.makedirs(os.path.join(A, "profiles", "X", "records"), exist_ok=True)
open(os.path.join(A, "profiles", "X", "records", "a.json"), "w").write('{"a": 1}')
# 4. 다른 폴더(Y) 미커밋 변경은 X 의 Push 에 섞이지 않는다
os.makedirs(os.path.join(A, "profiles", "Y", "records"), exist_ok=True)
open(os.path.join(A, "profiles", "Y", "records", "stray.json"), "w").write("{}")
os.makedirs(os.path.join(B, "profiles", "Y", "records"), exist_ok=True)
open(os.path.join(B, "profiles", "Y", "records", "b.json"), "w").write('{"b": 1}')

ok_a, out_a = ga.push("A push")
ok_b, out_b = gb.push("B push")            # A 가 먼저 올렸으므로 B 는 받아서 이어 붙인 뒤 올린다
check("push A ok", ok_a, out_a[-200:])
check("push B ok after rebase (different folder, no conflict)", ok_b, out_b[-300:])
ok, files = git(bare, "ls-tree", "-r", "--name-only", "main")
check("remote main has both folders' files",
      "profiles/X/records/a.json" in files and "profiles/Y/records/b.json" in files, files)
check("stray change in other folder not committed", "profiles/Y/records/stray.json" not in files)
check("stray change still in A working tree", os.path.isfile(os.path.join(A, "profiles", "Y", "records", "stray.json")))
ok, last = git(bare, "log", "-1", "--name-only", "--format=%s", "main")
check("B's commit touched only profiles/Y", all(l.startswith("profiles/Y/") for l in last.splitlines()[1:] if l), last)

ok_p, out_p = ga.pull()
check("pull (rebase) brings B's file to A", ok_p and os.path.isfile(os.path.join(A, "profiles", "Y", "records", "b.json")), out_p[-200:])

# 거절 후 재시도: B 가 몰래 먼저 올린 상태에서 A 가 다시 Push
open(os.path.join(B, "profiles", "Y", "records", "b2.json"), "w").write("{}")
git(B, "add", "-A", "--", "profiles/Y"); git(B, "commit", "-m", "b2"); git(B, "push", "origin", "main")
open(os.path.join(A, "profiles", "X", "records", "a2.json"), "w").write("{}")
ok_a2, out_a2 = ga.push("A push 2")
check("push after someone else pushed: rebased and pushed", ok_a2, out_a2[-300:])

# 아무 변경 없을 때
ok_n, out_n = gb.push("nothing")
check("push with no changes: ok, no empty commit", ok_n and "No changes to commit" in out_n, out_n[-200:])

# 5. 브랜치가 다르면 아무것도 안 한다
C = clone("C")
git(C, "checkout", "-b", "SA", "origin/SA")
gc = GitSync(C, "origin", "main", data_folder="X")
open(os.path.join(C, "new.json"), "w").write("{}")
head_before = git(bare, "rev-parse", "main")[1]
ok_c, out_c = gc.push("should not push")
check("wrong branch: push refused", not ok_c and "expects 'main'" in out_c, out_c)
check("wrong branch: remote untouched", git(bare, "rev-parse", "main")[1] == head_before)
ok_c, out_c = gc.pull()
check("wrong branch: pull refused", not ok_c)
ok_s, out_s = gc.switch_branch()
check("switch refused with uncommitted changes", not ok_s and "Uncommitted" in out_s, out_s)
os.remove(os.path.join(C, "new.json"))
ok_s, out_s = gc.switch_branch()
check("switch to main", ok_s and gc.current_branch() == "main", out_s)
check("after switch: check_branch ok", gc.check_branch()[0])

# 새 저장소 뼈대 = profiles/<folder>/records · thumbs
D = os.path.join(TMP, "fresh")
gd = GitSync(D, "origin", "main", data_folder="Z")
gd.ensure_repo("")
check("fresh repo skeleton under profiles/Z",
      os.path.isdir(os.path.join(D, "profiles", "Z", "records")) and os.path.isdir(os.path.join(D, "profiles", "Z", "thumbs"))
      and os.path.isfile(os.path.join(D, ".gitignore")))

# ---------------------------------------------------------------- 6. UI (오프스크린) - 실제 프로파일은 건드리지 않게 prefs 경로를 임시로
from Framework.qt.qt import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
P.PREFS_DIR = os.path.join(TMP, "prefs")
P.PROFILES_DIR = os.path.join(P.PREFS_DIR, "profiles")
P.ACTIVE_PATH = os.path.join(P.PREFS_DIR, "active.json")
P.PREFS_PATH = os.path.join(P.PREFS_DIR, "prefs.json")
os.makedirs(P.PROFILES_DIR)
proj = os.path.join(TMP, "project")
os.makedirs(proj)
open(os.path.join(proj, "scene.mb"), "w").write("x")
for name, folder in (("One", "X"), ("Two", "Y")):
    P.save_profile(name, {"source_mode": "git", "store_dir": A, "branch": "main", "remote_url": PUB,
                          "project_root": proj, "scan_dir": proj, "data_folder": folder, "author": "tester"})
P.set_active("One")

from tools.A00210_FileManager.app.ui import main_window as mw   # noqa: E402
win = mw.MainWindow()
check("UI: data folder from profile", win.cmb_data_folder.currentText() == "X", win.cmb_data_folder.currentText())
check("UI: store dir for tabs = profiles/X",
      os.path.normpath(win.get_store_dir()) == os.path.normpath(os.path.join(A, "profiles", "X")), win.get_store_dir())
check("UI: git uses repo root", os.path.normpath(win._make_git().store_dir) == os.path.normpath(A))
check("UI: git group title shows folder", "profiles/X" in win.git_group.title(), win.git_group.title())
check("UI: folder list", win._data_folder_names() == ["X", "Y"], win._data_folder_names())
win.cmb_profile.setCurrentText("Two")
win.on_profile_changed("Two")
check("UI: profile switch -> Y", win.cmb_data_folder.currentText() == "Y"
      and win.get_store_dir().replace("\\", "/").endswith("profiles/Y"))
# Save Record 가 profiles/Y/records 에 쓰는지 - MetaStore 로 직접
store = win._make_store()
key = store.make_key(os.path.join(proj, "scene.mb"))
rec_path = store.record_path(key)
check("UI: record path under profiles/Y/records",
      os.path.normpath(rec_path).startswith(os.path.normpath(os.path.join(A, "profiles", "Y", "records"))), rec_path)
win.cmb_data_folder.setCurrentText("NewFolder")
win._on_data_folder_committed()
check("UI: typed new folder", win.get_store_dir().replace("\\", "/").endswith("profiles/NewFolder"))
win._save_current_to_active()
check("UI: saved to profile json", P.load_profile("Two")["data_folder"] == "NewFolder")
# 잘못된 브랜치면 Switch 버튼
gc_win = mw.GitSync(C, "origin", "main", data_folder="X")
git(C, "checkout", "SA")
check("UI: wrong branch -> switch button visible", win._branch_ok(gc_win) is False and win.btn_switch_branch.isVisibleTo(win)
      and win.btn_switch_branch.text() == "Switch to main")
win.close()

print("RESULT {0}/{1}".format(sum(R), len(R)))
shutil.rmtree(TMP, ignore_errors=True)
