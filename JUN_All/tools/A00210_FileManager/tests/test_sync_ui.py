# -*- coding: utf-8 -*-
# A00210_FileManager - Sync 탭 UI 시험 (v01.47, 오프스크린, 가짜 PC · 가짜 git).
#   python test_sync_ui.py
import os
import sys
import json
import shutil
import tempfile
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, QMessageBox, QFileDialog, QInputDialog  # noqa: E402
app = QApplication.instance() or QApplication([])
from tools.A00210_FileManager.app.core import sync_settings as ss  # noqa: E402
from tools.A00210_FileManager.app.core import sync_manifest as sm  # noqa: E402
from tools.A00210_FileManager.app.core import sync_compare as sc  # noqa: E402
from tools.A00210_FileManager.app.ui import sync_tab as st  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


work = tempfile.mkdtemp(prefix="a00210_syncui_")
data_dir = os.path.join(work, "data", "profiles", "MUE")
root_a = os.path.join(work, "JUN_MUE_A")
root_b = os.path.join(work, "JUN_MUE_B")
os.makedirs(data_dir)


def write(root, rel, data):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)


for root in (root_a, root_b):
    write(root, "00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA/00010_cleanup_KANA_00070.mb", b"v70")
    write(root, "00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA/backup/x_BU.mb", root.encode())
    write(root, "00_00_02_doc/a.pdf", b"pdf")
write(root_b, "00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA/00010_cleanup_KANA_00080.mb", b"v80")
write(root_a, "only_a/new.mb", b"a")

# 다이얼로그 · 질문은 자동 응답
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
DIALOG = {"dir": "", "name": ""}
QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: DIALOG["dir"])
QInputDialog.getText = staticmethod(lambda *a, **k: (DIALOG["name"], True))

LOG = []
PUSHED = []
PULLED = []
STATE = {"git": True, "project_root": root_a.replace("\\", "/")}


def wait_scan(tab, timeout=20):
    t0 = time.time()
    while tab._thread is not None and time.time() - t0 < timeout:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


def make_tab():
    tab = st.SyncTab(
        get_data_dir=lambda: data_dir,
        get_project_root=lambda: STATE["project_root"],
        is_git_mode=lambda: STATE["git"],
        git_pull=lambda: PULLED.append(1) or True,
        git_push=lambda msg: PUSHED.append(msg) or True,
        get_author=lambda: "tester",
        log=LOG.append,
    )
    tab._pc = "PCA"
    return tab


def tree_rows(tab):
    out = {}

    def walk(it, path):
        rel = it.data(0, st.ROLE_REL)
        kind = it.data(0, st.ROLE_KIND)
        out[rel] = (kind, [it.text(c) for c in range(tab.tree.columnCount())])
        for i in range(it.childCount()):
            walk(it.child(i), path)

    for i in range(tab.tree.topLevelItemCount()):
        walk(tab.tree.topLevelItem(i), "")
    return out


KANA = "00_04_02_ANI_00_PJ_010/scenes/5040_cleanup_BCM_KANA/"
try:
    tab = make_tab()
    tab.load_prefs({})
    tab.resize(1000, 700)
    tab.show()
    app.processEvents()

    # ---------------------------------------------------------- 기본 루트 = Project Root (저장 전)
    check("default root from project root", tab.cmb_root.count() == 1 and tab._settings_dirty
          and tab._root_abs() == STATE["project_root"], tab._settings)
    check("settings not written yet", not os.path.exists(ss.settings_path(data_dir)))
    check("PCs label says not scanned", "not scanned" in tab.lbl_pcs.text())
    rid = tab._root_id

    # ---------------------------------------------------------- PC A 스캔 + 푸시
    tab.on_scan(push=True)
    check("scan thread started + buttons disabled", tab._thread is not None and not tab.btn_scan.isEnabled())
    wait_scan(tab)
    man_a = sm.manifest_path(data_dir, rid, "PCA")
    check("manifest A saved", os.path.isfile(man_a))
    check("settings saved on first scan", os.path.isfile(ss.settings_path(data_dir)) and not tab._settings_dirty)
    check("push called with root id", len(PUSHED) == 1 and "[{0}]".format(rid) in PUSHED[0] and "PCA" in PUSHED[0], PUSHED)
    check("buttons enabled again", tab.btn_scan.isEnabled() and not tab.progress_row.isVisible())
    ma = json.load(open(man_a, encoding="utf-8"))
    check("backup ignored in manifest", not any("backup" in k for k in ma["files"]), list(ma["files"]))

    # ---------------------------------------------------------- PC B 매니페스트(다른 PC 를 흉내)
    mb, _ = sm.scan(root_b, rid, "PCB", "other", [], ss.DEFAULT_IGNORE)
    sm.save_manifest(data_dir, mb)
    tab.on_pull_compare()
    check("pull called", PULLED == [1])
    rows = tree_rows(tab)
    k80 = KANA + "00010_cleanup_KANA_00080.mb"
    check("00080 shown as Missing on this PC", k80 in rows and rows[k80][1][-1].startswith("Missing")
          and "get from PCB" in rows[k80][1][-1], rows.get(k80))
    check("PC columns: this PC first", tab.tree.headerItem().text(1) == "PCA (this PC)" and tab.tree.headerItem().text(2) == "PCB")
    check("missing cell shows dash", rows[k80][1][1] == "—")
    k70 = KANA + "00010_cleanup_KANA_00070.mb"
    check("OK hidden by default", k70 not in rows)
    check("only-here shown as Only here", rows.get("only_a/new.mb", (0, [""]))[1][-1].startswith("Only here"))
    check("folder badge counts", "1 Missing" in rows[KANA][1][-1], rows.get(KANA))
    check("summary label", "Missing 1" in tab.lbl_summary.text() and "Only here 1" in tab.lbl_summary.text(), tab.lbl_summary.text())

    tab.chk_show[sc.OK].setChecked(True)
    check("OK shown when checked", k70 in tree_rows(tab))
    tab.chk_show[sc.OK].setChecked(False)

    tab.le_filter.setText("kana 0080")
    rows = tree_rows(tab)
    check("filter words", k80 in rows and "only_a/new.mb" not in rows)
    tab.le_filter.clear()

    tab.cmb_compare.setCurrentIndex(tab.cmb_compare.findData("all"))
    rows = tree_rows(tab)
    check("All PCs mode: per-PC text", rows["only_a/new.mb"][1][-1] == "Missing: PCB" and rows[k80][1][-1] == "Missing: PCA",
          (rows["only_a/new.mb"][1][-1], rows[k80][1][-1]))
    tab.cmb_compare.setCurrentIndex(tab.cmb_compare.findData("this"))

    # ---------------------------------------------------------- 제외 (공유 / 이 PC)
    tab._exclude([KANA], "shared")
    rows = tree_rows(tab)
    check("shared exclude hides folder", k80 not in rows)
    sset = json.load(open(ss.settings_path(data_dir), encoding="utf-8"))
    check("shared exclude saved", sset["roots"][0]["excluded_paths"] == [KANA], sset["roots"][0])
    check("excluded list shows it", tab.lst_shared.count() == 1)
    tab.chk_show_excluded.setChecked(True)
    rows = tree_rows(tab)
    check("excluded shown grey with flag", rows.get(KANA, ("",))[0] == "excluded", rows.get(KANA))
    tab._include_again([(KANA, "shared")])
    check("include again", k80 in tree_rows(tab) and json.load(open(ss.settings_path(data_dir), encoding="utf-8"))["roots"][0]["excluded_paths"] == [])
    tab.chk_show_excluded.setChecked(False)

    tab._exclude(["only_a/"], "local")
    check("local exclude hides + in prefs", "only_a/new.mb" not in tree_rows(tab)
          and tab.prefs_values()["sync_local_excluded"] == {rid: ["only_a/"]})
    check("local exclude not in shared file",
          json.load(open(ss.settings_path(data_dir), encoding="utf-8"))["roots"][0]["excluded_paths"] == [])
    # 다음 스캔은 제외 폴더를 안 본다
    tab.on_scan(push=False)
    wait_scan(tab)
    ma2 = json.load(open(man_a, encoding="utf-8"))
    check("rescan skips local-excluded folder", not any(k.startswith("only_a/") for k in ma2["files"]), list(ma2["files"]))
    check("scan only = no push", len(PUSHED) == 1)

    # ---------------------------------------------------------- 무시 패턴
    tab.txt_ignore.setPlainText("**/backup/**\n**/*.pdf")
    tab.on_save_patterns()
    check("ignore pattern applies at compare", "00_00_02_doc/a.pdf" not in tree_rows(tab) and
          json.load(open(ss.settings_path(data_dir), encoding="utf-8"))["ignore_patterns"] == ["**/backup/**", "**/*.pdf"])
    tab.on_reset_patterns()

    # ---------------------------------------------------------- 루트 추가 · PC 별 경로
    other = os.path.join(work, "Mocap")
    write(other, "take01.fbx", b"fbx")
    DIALOG.update(dir=other.replace("\\", "/"), name="Mocap")
    tab.on_add_root()
    check("second root added + selected", tab.cmb_root.count() == 2 and tab._current_root()["name"] == "Mocap", tab._settings["roots"])
    check("roots table rows", tab.tbl_roots.rowCount() == 2)
    tab.on_scan(push=False)
    wait_scan(tab)
    check("second root manifest in own folder", os.path.isfile(sm.manifest_path(data_dir, "mocap", "PCA")))
    check("first root manifest untouched", json.load(open(man_a, encoding="utf-8"))["files"] == ma2["files"])

    # 다른 위치(이 PC 만)
    moved = os.path.join(work, "Mocap_E")
    shutil.copytree(other, moved)
    DIALOG.update(dir=moved.replace("\\", "/"))
    tab.on_set_local_path()
    check("local path set", tab._root_abs() == moved.replace("\\", "/") and tab.prefs_values()["sync_root_paths"]["mocap"] == moved.replace("\\", "/"))
    check("shared default unchanged", tab._current_root()["default_path"] == other.replace("\\", "/"))
    tab.on_use_default_path()
    check("use shared default", tab._root_abs() == other.replace("\\", "/"))

    # 겹치는 루트: 바깥 루트 안의 폴더를 루트로 → 바깥 루트에서 제외(질문에 Yes)
    tab.cmb_root.setCurrentIndex(tab.cmb_root.findData(rid))
    inner = os.path.join(root_a, "00_00_02_doc")
    DIALOG.update(dir=inner.replace("\\", "/"), name="Docs")
    tab.on_add_root()
    outer = ss.find_root(tab._settings, rid)
    check("nested root excluded from outer", "00_00_02_doc/" in outer["excluded_paths"], outer["excluded_paths"])
    DIALOG.update(dir=inner.replace("\\", "/"), name="Docs again")
    n_before = len(tab._settings["roots"])
    tab.on_add_root()
    check("same path refused", len(tab._settings["roots"]) == n_before)

    # 이름 바꾸기 · 지우기
    DIALOG.update(name="Docs Renamed")
    tab.on_rename_root()
    check("rename keeps id", tab._current_root()["name"] == "Docs Renamed" and tab._current_root()["id"] == "docs")
    tab.on_remove_root()
    check("remove root", ss.find_root(tab._settings, "docs") is None and tab.cmb_root.count() == 2)

    # ---------------------------------------------------------- PC 가 많으면 요약 열
    tab.cmb_root.setCurrentIndex(tab.cmb_root.findData(rid))
    for n in ("PCC", "PCD", "PCE"):
        m = dict(mb)
        m["pc"] = n
        sm.save_manifest(data_dir, m)
    tab.on_refresh()
    heads = [tab.tree.headerItem().text(c) for c in range(tab.tree.columnCount())]
    check("5 PCs -> summary columns", heads == ["Path", "This PC", "Latest on", "Missing on", "Outdated on", "Status"], heads)
    rows = tree_rows(tab)
    check("summary cells", rows[k80][1][2] == "PCB, PCC, PCD, PCE" and rows[k80][1][3] == "PCA", rows.get(k80))

    # 오래된 매니페스트 경고
    m = json.load(open(sm.manifest_path(data_dir, rid, "PCE"), encoding="utf-8"))
    m["scanned_epoch"] = time.time() - 3 * 86400
    sm.save_manifest(data_dir, m)
    tab.on_refresh()
    check("stale manifest warning", "stale" in tab.lbl_pcs.text() and "3 days ago" in tab.lbl_pcs.text())

    # ---------------------------------------------------------- Local 모드 = 푸시 안 함
    STATE["git"] = False
    n_push = len(PUSHED)
    tab.on_scan(push=True)
    wait_scan(tab)
    check("local mode: no push", len(PUSHED) == n_push and any("Local mode" in l for l in LOG))
    tab.on_pull_compare()
    check("local mode: no pull", PULLED == [1])
    STATE["git"] = True

    # ---------------------------------------------------------- 취소
    big = os.path.join(root_a, "big.bin")
    with open(big, "wb") as f:
        f.write(os.urandom(64 * 1024 * 1024))
    before = open(man_a, "rb").read()
    tab.on_scan(push=False)
    tab.on_cancel_scan()
    wait_scan(tab)
    check("cancel keeps manifest", open(man_a, "rb").read() == before and any("cancelled" in l for l in LOG))
    os.remove(big)

    # ---------------------------------------------------------- 루트 폴더가 없는 PC
    DIALOG.update(dir=os.path.join(work, "nope").replace("\\", "/"))
    tab.cmb_root.setCurrentIndex(tab.cmb_root.findData("mocap"))
    tab._local_paths["mocap"] = os.path.join(work, "nope").replace("\\", "/")
    tab._update_root_label()
    check("missing root label", "not found" in tab.lbl_root_path.text())
    tab.on_scan()
    check("scan refused when root missing", tab._thread is None)

    # ---------------------------------------------------------- prefs 왕복
    vals = tab.prefs_values()
    tab2 = make_tab()
    tab2.load_prefs(vals)
    check("prefs round trip", tab2.prefs_values() == vals, (tab2.prefs_values(), vals))
    tab.shutdown()
    tab2.shutdown()

    # ---------------------------------------------------------- MainWindow 에 탭이 붙는다 (닫지 않음 - 실제 프로파일 저장 안 함)
    from tools.A00210_FileManager.app.ui import main_window as mw
    win = mw.MainWindow()
    titles = [win.tabs.tabText(i) for i in range(win.tabs.count())]
    check("MainWindow has Sync tab", titles[-1] == "Sync", titles)
    check("MainWindow collect prefs has sync keys", "sync_root_paths" in win._collect_prefs())
    win.deleteLater()

finally:
    shutil.rmtree(work, ignore_errors=True)

print("\n{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
