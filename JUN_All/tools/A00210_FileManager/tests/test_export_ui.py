# -*- coding: utf-8 -*-
# A00210_FileManager - Maya > Export UI 시험 (오프스크린 PySide6, 가짜 워커). Reference 탭이 picker · mayapy bar 로 바뀐 뒤에도 서는지 함께 본다.
#   python test_export_ui.py
import os
import sys
import json
import tempfile
import shutil

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, Qt, QMessageBox  # noqa: E402
app = QApplication.instance() or QApplication([])
from Framework.themes.theme_manager import ThemeManager  # noqa: E402
from Framework.qt.MOD_mayapyProcess_qt_v01 import JobOutcome  # noqa: E402
from tools.A00210_FileManager.app.maya.ui import maya_tab as mt  # noqa: E402
from tools.A00210_FileManager.app.maya.ui import export_tab as et  # noqa: E402
from tools.A00210_FileManager.app.maya.ui import export_table as xt  # noqa: E402
from tools.A00210_FileManager.app.maya.core import set_rules, export_jobs  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


work = tempfile.mkdtemp(prefix="a00210_ui_")
rules_dir = os.path.join(work, "rules")
out_dir = os.path.join(work, "out")
os.makedirs(out_dir)
files = []
for n in ("anim_01.mb", "anim_02.ma", "anim_03.mb"):
    p = os.path.join(work, n)
    open(p, "wb").write(b"x")
    files.append(p)

PREFS = {"mayapy_path": "", "export_rules_dir": rules_dir, "export_fbx_dir": out_dir}


def load():
    return dict(PREFS)


def save(d):
    PREFS.clear(); PREFS.update(d)


logs = []
tab = mt.MayaTab(log=logs.append, prefs={"load": load, "save": save})
ThemeManager.load_theme_to_widget(tab, "red")
tab.show(); app.processEvents()
ex = tab.export_tab

check("two sub tabs + mayapy bar once", [tab.tabs.tabText(i) for i in range(2)] == ["Reference", "Export"] and tab.mayapy_bar is not None
      and not hasattr(tab.reference_tab, "ipf_mayapy"))
check("default rule Bake created in prefs rules dir", ex.cmb_rule.currentText() == "Bake" and os.path.isfile(os.path.join(rules_dir, "Bake.json")))
check("rule summary line", ex.lbl_rule.text().startswith('set "Bake"'))
check("naming default token 0 bake", ex.cmb_mode.currentData() == "token" and ex.sb_position.value() == 0 and ex.le_text.text() == "bake")

# files -> table rows + output preview
ex.picker.add_files(files)
app.processEvents()
check("table rows follow picker", ex.table.rowCount() == 3 and ex.table.paths() == [os.path.normpath(f) for f in files])
check("output preview immediate", ex.table.item(0, xt.COL_OUT).text() == "bake_anim_01.fbx" and ex.lbl_preview.text().startswith("Preview: anim_01.mb  ->  bake_anim_01.fbx"))
check("status '-' before check sets", ex.table.item(0, xt.COL_STATUS).text() == "-")

# naming change -> output
ex.sb_position.setValue(1); app.processEvents()
check("naming change updates output", ex.table.item(0, xt.COL_OUT).text() == "anim_bake_01.fbx" and PREFS["export_naming"]["position"] == 1)
ex.le_find.setText("_0"); ex.le_replace.setText("_"); app.processEvents()
check("find/replace in output", ex.table.item(0, xt.COL_OUT).text() == "anim_bake_1.fbx")
ex.le_find.setText(""); ex.le_replace.setText(""); ex.sb_position.setValue(0); app.processEvents()

# collision
ex.le_find.setText("_01"); ex.le_replace.setText("_03"); app.processEvents()
check("collision marks two rows", ex.table.item(0, xt.COL_STATUS).text() == export_jobs.STATUS_COLLISION
      and ex.table.item(2, xt.COL_STATUS).text() == export_jobs.STATUS_COLLISION and ex.table.item(1, xt.COL_STATUS).text() == "-")
ex.le_find.setText(""); ex.le_replace.setText(""); app.processEvents()

# bake before check sets -> blocked (info box auto-closed)
calls = {"run": [], "info": 0, "question": [], "overwrite": None}
_orig_info = QMessageBox.information
QMessageBox.information = lambda *a, **k: calls.__setitem__("info", calls["info"] + 1)
ex.on_export(bake=True)
check("export before check sets is blocked", calls["info"] == 1 and any("Press Check Sets first" in l for l in logs))

# fake worker
PROBE = {"files": [
    {"file": os.path.normpath(files[0]), "ok": True, "version": "2024", "fps": 30.0, "unit": "ntsc", "playback": [2.0, 6000.0], "anim": [0.0, 6100.0],
     "sets": [{"name": "Bake", "members": 1, "nodes": 78}], "references": {"loaded": 1, "unloaded": 0}, "seconds": 1.0},
    {"file": os.path.normpath(files[1]), "ok": True, "version": "2022", "fps": 24.0, "unit": "film", "playback": [1.0, 48.0], "anim": [1.0, 48.0],
     "sets": [], "references": {"loaded": 0, "unloaded": 0}, "seconds": 1.0},
    {"file": os.path.normpath(files[2]), "ok": False, "error": "open failed : boom", "version": "", "fps": None, "unit": "", "playback": [None, None],
     "anim": [None, None], "sets": [], "references": {}, "seconds": 0.0}],
    "mayapy_version": "2024"}


def fake_run_job(parent, mayapy, job, title="", message="", log=None, cancel_grace_sec=120):
    calls["run"].append((job, cancel_grace_sec))
    o = JobOutcome()
    if job["job"] == "probe":
        o.result = PROBE
    else:
        o.result = {"results": [{"file": i["file"], "status": "exported", "out_fbx": i["out_fbx"], "error": ""} for i in job["items"]],
                    "exported": len(job["items"]), "skipped": 0, "failed": 0, "cancelled": False}
    return o


et.mayapy_process.run_job = fake_run_job
ex._mayapy_path = lambda: sys.executable          # 가짜 mayapy 경로 (존재하는 파일)

ex.on_check_sets(); app.processEvents()
check("probe job shape", calls["run"] and calls["run"][0][0]["job"] == "probe" and calls["run"][0][0]["rule"]["set_name"] == "Bake")
check("row 1 : set, range from playback, fps, ver, ready", ex.table.item(0, xt.COL_SET).text() == "Bake (1 -> 78)" and ex.table.item(0, xt.COL_START).text() == "2"
      and ex.table.item(0, xt.COL_END).text() == "6000" and ex.table.item(0, xt.COL_FPS).text() == "30" and ex.table.item(0, xt.COL_VER).text() == "2024"
      and ex.table.item(0, xt.COL_STATUS).text() == export_jobs.STATUS_READY)
check("row 2 : no set -> unchecked + status no set, ver 2022 warn colour", ex.table.item(1, xt.COL_CHECK).checkState() == Qt.Unchecked
      and ex.table.item(1, xt.COL_STATUS).text() == export_jobs.STATUS_NO_SET and ex.table.item(1, xt.COL_VER).foreground().color().name() != "#000000")
check("row 3 : failed probe -> unchecked + failed", ex.table.item(2, xt.COL_CHECK).checkState() == Qt.Unchecked and ex.table.item(2, xt.COL_STATUS).text().startswith("failed"))
check("log summary", any("[OK] Check Sets : 3 file(s) - 1 with a matching set, 1 without, 1 could not be read" in l for l in logs))

# range combo
ex.cmb_range.setCurrentIndex(1); app.processEvents()
check("anim range fills 0-6100", ex.table.item(0, xt.COL_START).text() == "0" and ex.table.item(0, xt.COL_END).text() == "6100")
ex.cmb_range.setCurrentIndex(2); ex.sb_cstart.setValue(10); ex.sb_cend.setValue(20); app.processEvents()
check("custom range fills all rows incl. unprobed", ex.table.item(0, xt.COL_START).text() == "10" and ex.table.item(2, xt.COL_END).text() == "20")
ex.cmb_range.setCurrentIndex(0); app.processEvents()
check("timeline back to 2-6000 + prefs", ex.table.item(0, xt.COL_START).text() == "2" and PREFS["export_range_mode"] == "timeline")

# edited cell goes into job
ex.table.item(0, xt.COL_START).setText("100")
rows = ex.table.checked_rows()
check("checked_rows only ready rows, edited start", len(rows) == 1 and rows[0]["start"] == "100" and rows[0]["out_fbx"].lower() == os.path.join(out_dir, "bake_anim_01.fbx").lower())

# existing output -> overwrite popup (Cancel then Overwrite)
open(os.path.join(out_dir, "bake_anim_01.fbx"), "wb").write(b"old")
QMessageBox.question = lambda *a, **k: QMessageBox.Yes
ex._confirm_overwrite = lambda existing, label: calls.__setitem__("overwrite", list(existing)) or False
ex.on_export(bake=True)
check("existing fbx -> popup, Cancel stops run", calls["overwrite"] and os.path.basename(calls["overwrite"][0]) == "bake_anim_01.fbx"
      and len(calls["run"]) == 1 and any("cancelled - existing FBX" in l for l in logs))
ex._confirm_overwrite = lambda existing, label: True
ex.chk_euler.setChecked(True)
ex.chk_channels["scale"].setChecked(False)
ex.on_export(bake=True); app.processEvents()
job, grace = calls["run"][-1]
check("export job from UI", job["job"] == "export" and job["bake"] is True and job["channels"] == ["translate", "rotate"] and job["euler_filter"] is True
      and job["joints_only"] is True and job["import_references"] is True and job["items"][0]["start"] == 100 and job["items"][0]["end"] == 6000
      and os.path.dirname(job["report"]).lower() == out_dir.lower(), job)
check("export cancel grace 1800", grace == et.EXPORT_CANCEL_GRACE_SEC)
check("result -> status exported", ex.table.item(0, xt.COL_STATUS).text() == "exported" and any("Bake & Export done - 1 exported" in l for l in logs))
ex.on_export(bake=False); app.processEvents()
check("export only job", calls["run"][-1][0]["bake"] is False)

# rule CRUD via core + reload; rule change resets probe
r2 = set_rules.SetRule("Face", "FaceCtl", "contains", True, "d")
set_rules.save_rule(r2, rules_dir)
ex._reload_rules(select="Face"); app.processEvents()
check("rule combo reload + select + prefs", [ex.cmb_rule.itemText(i) for i in range(ex.cmb_rule.count())] == ["Bake", "Face"] and ex.cmb_rule.currentText() == "Face"
      and PREFS["export_rule"] == "Face")
check("rule change resets Set column", ex.table.item(0, xt.COL_SET).text() == "-" and ex.table.item(0, xt.COL_STATUS).text() == "-")
check("rule summary for Face", 'set "FaceCtl"' in ex.lbl_rule.text() and "contains" in ex.lbl_rule.text())

# prefs round trip into a new tab
tab2 = mt.MayaTab(log=logs.append, prefs={"load": load, "save": save})
ex2 = tab2.export_tab
check("prefs reload : rule, folder, euler, channels", ex2.cmb_rule.currentText() == "Face" and ex2.le_folder.text() == out_dir and ex2.chk_euler.isChecked()
      and not ex2.chk_channels["scale"].isChecked())

# reference tab still works with picker
ref = tab.reference_tab
ref.add_files(files)
check("reference tab picker delegation", len(ref.file_paths()) == 3 and ref.mayapy_path() == tab.mayapy_bar.path())

# sizes
tab.resize(900, 700); app.processEvents()
ms = tab.minimumSizeHint()
print("  MayaTab minimumSizeHint = %d x %d ; export tab = %d x %d ; reference tab = %d x %d" % (
    ms.width(), ms.height(), ex.minimumSizeHint().width(), ex.minimumSizeHint().height(),
    ref.minimumSizeHint().width(), ref.minimumSizeHint().height()))
check("export tab not wider than 1000 px minimum", ex.minimumSizeHint().width() <= 1000, ex.minimumSizeHint().width())

# hw label eventually filled (QProcess) - wait up to 8 s
import time
t0 = time.time()
while time.time() - t0 < 8 and ex.lbl_resources.text() == "Resources: ...":
    app.processEvents(); time.sleep(0.05)
check("resources line filled", ex.lbl_resources.text().startswith("Resources: CPU") or "unavailable" in ex.lbl_resources.text(), ex.lbl_resources.text())

QMessageBox.information = _orig_info
shutil.rmtree(work, ignore_errors=True)
print("\nRESULT %d/%d" % (sum(R), len(R)))
sys.exit(0 if all(R) else 1)
