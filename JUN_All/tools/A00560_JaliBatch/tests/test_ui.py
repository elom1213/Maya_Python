# -*- coding: utf-8 -*-
# A00560_JaliBatch - UI 시험 (T8, 오프스크린 PySide6, 가짜 워커) + 실제 mayapy 1회 (예시 자료 · 컨트롤러가 있을 때만)
#   python test_ui.py            (시스템 python + PySide6 - standalone 과 같은 환경)
import json
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, Qt, QMessageBox   # noqa: E402
app = QApplication.instance() or QApplication([])
from Framework.themes.theme_manager import ThemeManager   # noqa: E402
ThemeManager.load_theme_dev(app, "teal_dark")
from Framework.qt.MOD_mayapyProcess_qt_v01 import JobOutcome   # noqa: E402
from tools.A00560_JaliBatch.app.core import prefs, manifest, jobs   # noqa: E402
from tools.A00560_JaliBatch.app.ui import main_window as mw   # noqa: E402
from tools.A00560_JaliBatch.app.ui import batch_tab as bt   # noqa: E402
from tools.A00560_JaliBatch.app.ui import validate_tab as vt   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump():
    app.processEvents()
    app.processEvents()


SRC = r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI_Voice\0060_Vivian_voice\out_en_002"
CTL_SRC = r"C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma"
work = tempfile.mkdtemp(prefix="a00560_ui_")
prefs.PREFS_DIR = os.path.join(work, "prefs")
prefs.PREFS_PATH = os.path.join(prefs.PREFS_DIR, "prefs.json")
CTL = os.path.join(work, "ctl.ma")
with open(CTL, "w") as f:
    f.write("//Maya ASCII 2024 scene (fake controller for UI test)\n")
OUT = os.path.join(work, "maya")

# 가짜 워커: job 을 기록하고 generate 면 클립 .mb 를 빈 파일로 만들어 주며 매니페스트도 워커처럼 갱신한다
calls = []


def fake_run_job(parent, mayapy, job, worker, title="", message="", log=None, job_prefix=""):
    calls.append(job)
    out = JobOutcome()
    if job["job"] == "generate":
        os.makedirs(job["out_dir"], exist_ok=True)
        res = {"generated": 0, "skipped": 0, "failed": 0, "cancelled": False, "clips": []}
        data = manifest.load(job["out_dir"])
        for c in job["clips"]:
            if os.path.isfile(c["out_mb"]) and job["overwrite"] == "skip":
                res["skipped"] += 1
                res["clips"].append({"name": c["name"], "status": "skipped"})
                continue
            if c["name"].endswith("_03_f0490_0600"):
                res["failed"] += 1
                res["clips"].append({"name": c["name"], "status": "failed", "error": "fake failure"})
                manifest.update_clip(data, c["name"], status="failed", error="fake failure", start=c["start"])
                continue
            with open(c["out_mb"], "w") as f:
                f.write("fake")
            res["generated"] += 1
            res["clips"].append({"name": c["name"], "status": "generated", "start": c["start"]})
            manifest.update_clip(data, c["name"], status="generated", start=c["start"], mb=c["out_mb"], end=c["start"] + 10)
        manifest.save(job["out_dir"], data)
        out.result = res
    else:
        rows = []
        for p in job["clips"]:
            rows.append({"mb": p, "name": os.path.splitext(os.path.basename(p))[0], "controller": job.get("repath") or CTL,
                         "loaded": True, "failed_edits": 2 if p.endswith("_02_f0445_0490.mb") else 0, "baked_channels": 24,
                         "keys": 100, "dummy_in_curves": 0, "sound": True, "stamp": {"start": 1, "end": 10, "fps": 30.0},
                         "controller_changed": False, "problems": ["2 failed reference edit(s)"] if p.endswith("_02_f0445_0490.mb") else [],
                         "status": "warn" if p.endswith("_02_f0445_0490.mb") else "ok", "repathed": bool(job.get("repath"))})
        out.result = {"rows": rows, "ok": sum(1 for r in rows if r["status"] == "ok"), "warn": sum(1 for r in rows if r["status"] == "warn"),
                      "failed": 0, "cancelled": False}
    if log:
        log("fake worker: {0}".format(job["job"]))
    return out


w = mw.MainWindow(run_job_func=fake_run_job)
w.show()
pump()
check("U1 window opens with 2 tabs + log + mayapy row", w.tabs.count() == 2 and w.log_widget.toPlainText() and w.le_mayapy is not None)
check("U1 theme applied (stylesheet present)", bool(app.styleSheet()))
check("U1 mayapy auto-detected", bool(w.mayapy_path()), w.mayapy_path())

b = w.batch_tab
b.le_controller.setText(CTL)
b.le_output.setText(OUT)
if os.path.isdir(SRC):
    b.set_source(SRC)
    b.scan()
    pump()
    check("U2 scan lists 5 clips, all checked", b.table.rowCount() == 5 and len(b.checked_rows()) == 5)
    check("U2 Start column = 1, Frames at 30 fps = wav length", b.start_of_row(0) == 1 and b.table.item(0, bt.COL_FRAMES).text() == "324")
    b.cmb_fps.setCurrentText("24")
    pump()
    check("U2 fps 24 -> frames shrink (259)", b.table.item(0, bt.COL_FRAMES).text() == "259", b.table.item(0, bt.COL_FRAMES).text())
    b.cmb_fps.setCurrentText("30")
    b.set_start_of_row(1, 101)
    b.table.item(2, bt.COL_START).setText("abc")
    pump()
    check("U2 non-integer Start reverts", b.start_of_row(2) == 1)
    b.sb_start.setValue(5)
    b.apply_start_to_all()
    check("U2 Apply to all fills every Start", all(b.start_of_row(i) == 5 for i in range(5)))
    b.set_start_of_row(1, 101)
    job = b.build_job()
    check("U3 job carries per-row start (row 2 = 101, others 5) and the file name is not parsed",
          [c["start"] for c in job["clips"]] == [5, 101, 5, 5, 5] and job["fps"] == 30.0 and job["controller"] == CTL, [c["start"] for c in job["clips"]])
    check("U3 job defaults: skip, copy_wav, jali data, mapping", job["overwrite"] == "skip" and job["copy_wav"] and job["jali"]["mode"] == "data"
          and job["mapping"] == "jali_slider_dummy_in")
    b.rb_jali_fixed.setChecked(True)
    b.ds_jaw.setValue(0.4)
    job = b.build_job()
    check("U3 JaLi fixed -> job", job["jali"] == {"mode": "fixed", "fixed": [0.4, 0.6], "scale": None})
    b.rb_jali_data.setChecked(True)

    outcome = b.run()
    pump()
    check("U4 run: fake worker called with generate job", calls and calls[-1]["job"] == "generate" and len(calls[-1]["clips"]) == 5)
    check("U4 run: 4 generated 1 failed -> statuses in table", outcome.result["generated"] == 4 and
          b.table.item(2, bt.COL_STATUS).text() == "failed" and b.table.item(0, bt.COL_STATUS).text() == "exists",
          [b.table.item(i, bt.COL_STATUS).text() for i in range(5)])
    mf = manifest.load(OUT)
    check("U4 manifest has settings + starts (row 2 = 101)", mf["settings"]["fps"] == 30.0 and mf["clips"][job["clips"][1]["name"]]["start"] == 101)
    check("U4 Validate tab folder set by the generated signal", w.validate_tab.folder() == os.path.normpath(OUT) and w.validate_tab.table.rowCount() == 4,
          (w.validate_tab.folder(), w.validate_tab.table.rowCount()))
    # Keep edited: 클립 1 을 edited 로 표시하고 overwrite 로 다시 Run -> 빠진다
    mf = manifest.load(OUT)
    manifest.update_clip(mf, job["clips"][0]["name"], status="edited")
    manifest.save(OUT, mf)
    b._load_manifest()
    b.set_overwrite_policy("overwrite")
    job2 = b.build_job()
    check("U5 Keep edited excludes the edited clip", len(job2["clips"]) == 4 and job["clips"][0]["name"] not in [c["name"] for c in job2["clips"]])
    b.cb_skip_edited.setChecked(False)
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.No)
    n_calls = len(calls)
    check("U5 overwrite with edited and Keep off -> asks, No cancels run", b.run() is None and len(calls) == n_calls)
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
    b.run()
    check("U5 Yes -> runs with the edited clip included", len(calls) == n_calls + 1 and len(calls[-1]["clips"]) == 5)
    b.set_overwrite_policy("skip")
    b.cb_skip_edited.setChecked(True)

    # Validate 탭 (U5 의 Yes 가 클립 1 을 다시 만들어 edited 가 generated 로 돌아갔다 - 워커와 같은 동작. 다시 edited 로 표시)
    mf = manifest.load(OUT)
    manifest.update_clip(mf, job["clips"][0]["name"], status="edited")
    manifest.save(OUT, mf)
    v = w.validate_tab
    v.scan()
    check("U6 validate scan lists 4 .mb with manifest status", v.table.rowCount() == 4 and v.table.item(0, vt.COL_MANIFEST).text() == "edited",
          [v.table.item(i, vt.COL_MANIFEST).text() for i in range(v.table.rowCount())])
    v.validate(repath=False)
    pump()
    check("U6 validate fills rows, failed edits red on clip 2", calls[-1]["job"] == "validate" and v.table.item(1, vt.COL_FAILED).text() == "2"
          and v.table.item(0, vt.COL_RESULT).text() == "ok" and "failed" in v.table.item(1, vt.COL_RESULT).text())
    v.le_repath.setText("")
    check("U6 repath without a file -> error, no worker call", v.validate(repath=True) is None)
    v.le_repath.setText(CTL)
    v.table.selectRow(0)
    v.validate(repath=True)
    check("U6 repath: only selected clip, repath path in job", calls[-1]["job"] == "validate" and len(calls[-1]["clips"]) == 1 and calls[-1]["repath"] == CTL)
else:
    print("SKIP U2-U6 (no example folder)")

# prefs 왕복
w.collect_prefs()
w.save_prefs()
p = prefs.load()
check("U7 prefs saved: controller, output, fps, overwrite", p["controller"] == CTL and p["output_dir"] == OUT and p["fps"] == "30" and p["overwrite"] == "skip")
w2 = mw.MainWindow(run_job_func=fake_run_job)
check("U7 new window reloads prefs", w2.batch_tab.le_controller.text() == CTL and w2.batch_tab.le_output.text() == OUT)
w2.close()

# Shrink / Pin
w.shrink_button.setChecked(True)
pump()
check("U8 shrink 272x155, tabs hidden, Pin under Shrink", (w.width(), w.height()) == (272, 155) and not w.tabs.isVisible()
      and w.button_grid.itemAtPosition(1, 0) is not None)
w.shrink_button.setChecked(False)
pump()
check("U8 restore shows tabs", w.tabs.isVisible() and w.width() > 272)
w.pin_button.setChecked(True)
pump()
check("U8 pin sets stays-on-top + label", bool(w.windowFlags() & Qt.WindowStaysOnTopHint) and w.pin_button.text() == "Pinned")
w.pin_button.setChecked(False)
check("U8 log widget shared by tabs", "fake worker" in w.log_widget.toPlainText() or not os.path.isdir(SRC))
w.close()

# ---------------------------------------------------------------- 실제 mayapy 1회 (UI 경로 그대로, 공용 QProcess 러너)
if os.path.isdir(SRC) and os.path.isfile(CTL_SRC):
    real_ctl = os.path.join(work, "A0030_real.ma")
    shutil.copy2(CTL_SRC, real_ctl)
    OUT2 = os.path.join(work, "maya_real")
    w3 = mw.MainWindow()
    w3.show()
    pump()
    w3.batch_tab.set_source(SRC)
    w3.batch_tab.le_controller.setText(real_ctl)
    w3.batch_tab.le_output.setText(OUT2)
    w3.batch_tab.scan()
    w3.batch_tab.set_all_checked(False)
    w3.batch_tab.table.item(1, bt.COL_CHECK).setCheckState(Qt.Checked)     # 가장 짧은 클립 하나만 (1.5 s)
    outcome = w3.batch_tab.run()
    pump()
    name = w3.batch_tab.scan_result.clips[1].name
    check("R1 real mayapy via QProcess: 1 generated, .mb exists", outcome is not None and outcome.result and outcome.result["generated"] == 1
          and os.path.isfile(os.path.join(OUT2, name + ".mb")), outcome and (outcome.error or outcome.result))
    w3.validate_tab.set_folder(OUT2)
    out_v = w3.validate_tab.validate(repath=False)
    pump()
    check("R2 real validate: ok row", out_v is not None and out_v.result and out_v.result["ok"] == 1 and w3.validate_tab.table.item(0, vt.COL_RESULT).text() == "ok",
          out_v and (out_v.error or out_v.result and out_v.result["rows"][0]["problems"]))
    w3.close()
else:
    print("SKIP R1-R2 (no example data / controller)")

shutil.rmtree(work, ignore_errors=True)
print("RESULT", "OK" if all(R) else "FAIL", "{0}/{1}".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
