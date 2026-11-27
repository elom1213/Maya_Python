# -*- coding: utf-8 -*-
# A00210_FileManager - Maya > File Date 시험 (v01.54, 오프스크린 PySide6)
#   python test_file_date.py
# 체크한 .ma / .mb / .fbx 의 수정한 날짜만 바뀌고 내용 · 크기는 그대로인지, 기본 오늘 · 시각 유지 / 지정 · 건너뛰기 · Undo Last.
import datetime
import hashlib
import os
import shutil
import stat
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.qt.qt import QApplication, QDate, QTime  # noqa: E402
app = QApplication.instance() or QApplication([])

from tools.A00210_FileManager.app.maya.core import file_dates as fd  # noqa: E402
from tools.A00210_FileManager.app.maya.ui.file_date_tab import FileDateTab  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if str(extra) else ""))


OLD = datetime.datetime(2020, 1, 2, 3, 4, 5).timestamp()


def make_files(root):
    paths = {}
    for rel, body in (("a.ma", b"//Maya ASCII 2024 scene\nrequires maya \"2024\";\n" * 50),
                      ("b.mb", os.urandom(4096)),
                      ("c.fbx", os.urandom(2048)),
                      ("notes.txt", b"hello"),
                      (os.path.join("sub", "E.FBX"), os.urandom(512))):
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(body)
        os.utime(full, (OLD, OLD))
        paths[rel] = full
    return paths


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


tmp = tempfile.mkdtemp(prefix="a210_filedate_")
try:
    P = make_files(tmp)

    # ---- 대상 거르기
    keep, skipped = fd.split_targets([P["a.ma"], P["notes.txt"], P["a.ma"], P[os.path.join("sub", "E.FBX")],
                                      os.path.join(tmp, "missing.mb")])
    check("split_targets: ma + upper-case .FBX kept, duplicate dropped", keep == [P["a.ma"], P[os.path.join("sub", "E.FBX")]],
          keep)
    check("split_targets: .txt and missing file are skipped with a reason",
          [os.path.basename(p) for p, _w in skipped] == ["notes.txt", "missing.mb"], skipped)

    # ---- 오늘 날짜, 각 파일의 시각 유지 - 내용 · 크기 그대로
    targets = [P["a.ma"], P["b.mb"], P["c.fbx"]]
    before = {p: (digest(p), os.path.getsize(p)) for p in targets}
    today = datetime.date.today()
    res = fd.set_dates(targets, today)
    check("set_dates reports every file ok", all(c.ok for c in res) and len(res) == 3, [c.error for c in res])
    stamps = [datetime.datetime.fromtimestamp(os.stat(p).st_mtime) for p in targets]
    check("modified date is today, time of day kept (03:04:05)",
          all(s.date() == today and (s.hour, s.minute, s.second) == (3, 4, 5) for s in stamps), stamps)
    check("contents and sizes are unchanged", all((digest(p), os.path.getsize(p)) == before[p] for p in targets))
    check("old modified time is recorded", all(abs(c.old - OLD) < 1.0 for c in res))

    # ---- 시각 지정
    res2 = fd.set_dates([P["c.fbx"]], datetime.date(2025, 6, 7), datetime.time(18, 30, 0))
    s = datetime.datetime.fromtimestamp(os.stat(P["c.fbx"]).st_mtime)
    check("Set time puts the given time of day", res2[0].ok and (s.year, s.month, s.day, s.hour, s.minute) ==
          (2025, 6, 7, 18, 30), s)

    # ---- 읽기 전용 파일도
    ro = P["b.mb"]
    os.chmod(ro, stat.S_IREAD)
    res3 = fd.set_dates([ro], datetime.date(2024, 2, 29))
    check("a read-only file gets the new date too", res3[0].ok and
          datetime.datetime.fromtimestamp(os.stat(ro).st_mtime).date() == datetime.date(2024, 2, 29),
          res3[0].error)
    os.chmod(ro, stat.S_IREAD | stat.S_IWRITE)

    # ---- restore
    n = fd.restore(res3)
    check("restore puts the previous modified time back",
          n == 1 and abs(os.stat(ro).st_mtime - res3[0].old) < 1.0)

    # ---- UI
    for p in P.values():
        os.utime(p, (OLD, OLD))
    logs = []
    tab = FileDateTab(log=logs.append)
    tab.confirm = False
    tab.resize(800, 700)
    tab.show()
    app.processEvents()
    check("default date is today, time mode keeps each file's time",
          tab.date_edit.date() == QDate.currentDate() and tab.rb_keep_time.isChecked() and not tab.time_edit.isEnabled())
    check("nothing checked: Set Date is off", not tab.btn_set.isEnabled() and tab.table.rowCount() == 0)
    tab.file_tree.ipf_path.setText(tmp)
    tab.file_tree.on_build()
    app.processEvents()
    tab.file_tree.set_checked_paths([P["a.ma"], P["b.mb"], P["notes.txt"]])
    app.processEvents()
    check("checked .ma / .mb listed, the .txt left out and noted",
          tab.table.rowCount() == 2 and "not .ma / .mb / .fbx" in tab.lbl_count.text() and
          tab.btn_set.text() == "Set Date (2 file(s))", (tab.table.rowCount(), tab.lbl_count.text(), tab.btn_set.text()))
    check("table shows the current and the new modified date",
          tab.table.item(0, 2).text() == "2020-01-02 03:04:05" and
          tab.table.item(0, 3).text() == today.isoformat() + " 03:04:05",
          (tab.table.item(0, 2).text(), tab.table.item(0, 3).text()))
    tab.rb_set_time.setChecked(True)
    tab.time_edit.setTime(QTime(9, 15, 0))
    check("Set time updates the preview", tab.table.item(0, 3).text() == today.isoformat() + " 09:15:00"
          and tab.time_edit.isEnabled())
    tab.rb_keep_time.setChecked(True)
    tab.date_edit.setDate(QDate(2023, 3, 4))
    tab.btn_today.click()
    check("Today button brings the date back to today", tab.date_edit.date() == QDate.currentDate())
    before_ui = {p: digest(p) for p in (P["a.ma"], P["b.mb"])}
    tab.btn_set.click()
    app.processEvents()
    dates = [datetime.datetime.fromtimestamp(os.stat(p).st_mtime).date() for p in (P["a.ma"], P["b.mb"])]
    check("Set Date changes the checked files to today", dates == [today, today], dates)
    check("the .txt that was checked is not touched", abs(os.stat(P["notes.txt"]).st_mtime - OLD) < 1.0)
    check("contents unchanged after Set Date in the UI", all(digest(p) == h for p, h in before_ui.items()))
    check("Set Date is logged (and the .txt skip)", any(m.startswith("[OK] Set the modified date of 2 of 2") for m in logs)
          and any(m.startswith("[SKIP] notes.txt") for m in logs), logs)
    check("table refreshes to the new date", tab.table.item(0, 2).text().startswith(today.isoformat()))
    check("Undo Last is on", tab.btn_undo.isEnabled())
    tab.btn_undo.click()
    check("Undo Last puts the old dates back", all(abs(os.stat(p).st_mtime - OLD) < 1.0 for p in (P["a.ma"], P["b.mb"]))
          and not tab.btn_undo.isEnabled())
    tab.btn_uncheck.click()
    app.processEvents()
    check("Uncheck All empties the list", tab.table.rowCount() == 0 and not tab.btn_set.isEnabled())

    # ---- 메인 창에 탭이 있다
    from tools.A00210_FileManager.app.ui.main_window import MainWindow  # noqa: E402
    from tools.A00210_FileManager.app.core import library_settings as LS  # noqa: E402
    import tempfile as _tf  # noqa: E402
    LS.SETTINGS_PATH = os.path.join(_tf.mkdtemp(prefix="a00210_lib_"), "structure_library.json")  # 실제 PC 설정 보호 (v01.60)
    win = MainWindow()
    names = [win.maya_tab.tabs.tabText(i) for i in range(win.maya_tab.tabs.count())]
    check("Maya tab has Reference / Export / File Date", names == ["Reference", "Export", "File Date"], names)
    win.close()
finally:
    for root, _dirs, files in os.walk(tmp):
        for f in files:
            try:
                os.chmod(os.path.join(root, f), stat.S_IREAD | stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(tmp, ignore_errors=True)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
