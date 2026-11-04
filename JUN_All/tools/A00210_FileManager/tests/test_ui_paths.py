# -*- coding: utf-8 -*-
# A00210_FileManager v01.46 - 화면 경로 표기 통일(슬래시) 시험. 표준 python, 오프스크린.
#   python test_ui_paths.py
import os
import sys
import shutil
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

from tools.A00210_FileManager.app.core.paths import ui_path, ui_text   # noqa: E402
from tools.A00210_FileManager.app.core import prefs as P   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ---------------------------------------------------------------- ui_path
A = r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_FileManager_data"
B = "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/JUN_FileManager_data"
check("backslash and slash -> same text", ui_path(A) == ui_path(B) == B, (ui_path(A), ui_path(B)))
check("mixed separators", ui_path(r"C:/Users/USER\Desktop/JP") == "C:/Users/USER/Desktop/JP")
check("trailing separator removed", ui_path("C:/work/") == "C:/work" and ui_path("C:\\work\\") == "C:/work")
check("drive root kept", ui_path("D:\\") == "D:/" and ui_path("D:/") == "D:/", (ui_path("D:\\"), ui_path("D:/")))
check("UNC backslash -> //server", ui_path(r"\\172.30.1.93\MANUTeam\02.Art\Asset") == "//172.30.1.93/MANUTeam/02.Art/Asset",
      ui_path(r"\\172.30.1.93\MANUTeam\02.Art\Asset"))
check("UNC slash kept", ui_path("//172.30.1.93/MANUTeam/02.Art/Asset") == "//172.30.1.93/MANUTeam/02.Art/Asset")
check("dots collapsed", ui_path("C:/a/./b/../c") == "C:/a/c")
check("empty", ui_path("") == "" and ui_path(None) == "" and ui_path("   ") == "")
check("case kept", ui_path(r"C:\Users\USER\Desktop") == "C:/Users/USER/Desktop")
check("spaces kept", ui_path(r"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe")
      == "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe")

# ---------------------------------------------------------------- ui_text (로그)
check("log path converted", ui_text("Data folder: " + A + "\\profiles\\Dnable")
      == "Data folder: " + B + "/profiles/Dnable")
check("log path with spaces", ui_text(r"mayapy : C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe  (+1 more)")
      == "mayapy : C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe  (+1 more)")
check("log UNC converted", ui_text(r"Scanned 3 file(s) in \\172.30.1.93\MANUTeam\x") == "Scanned 3 file(s) in //172.30.1.93/MANUTeam/x")
check("log quoted path stops at quote", ui_text("Settings saved to profile 'Default': C:\\a\\b.json")
      == "Settings saved to profile 'Default': C:/a/b.json")
check("log without path untouched", ui_text("[OK] 3 file(s)\nnext line") == "[OK] 3 file(s)\nnext line")
check("multi-line log, each path", ui_text("a C:\\x\\y\nb D:\\z") == "a C:/x/y\nb D:/z")
check("non-path backslash left alone", ui_text("regex \\d+ found") == "regex \\d+ found")

# ---------------------------------------------------------------- 프로파일 읽기 = 같은 표기
raw_a = {"store_dir": A, "project_root": r"D:\D__02.Art\D__Asset\D__Character", "scan_dir": r"D:\D__02.Art",
         "local_dir": r"\\172.30.1.93\MANUTeam", "recreate_to": "E:\\out\\", "mayapy_path": r"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe",
         "export_rules_dir": "C:\\rules", "export_fbx_dir": "C:\\fbx", "branch": "main", "data_folder": "Dnable"}
raw_b = {"store_dir": B, "project_root": "D:/D__02.Art/D__Asset/D__Character", "scan_dir": "D:/D__02.Art",
         "local_dir": "//172.30.1.93/MANUTeam", "recreate_to": "E:/out", "mayapy_path": "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe",
         "export_rules_dir": "C:/rules", "export_fbx_dir": "C:/fbx", "branch": "main", "data_folder": "Dnable"}
pa, pb = P._apply_defaults(raw_a), P._apply_defaults(raw_b)
diff = [k for k in P.PATH_KEYS if pa[k] != pb[k]]
check("profile load: every path key same text for \\ and / profiles", not diff, diff)
check("profile load: no backslash left", not any("\\" in pa[k] for k in P.PATH_KEYS), [pa[k] for k in P.PATH_KEYS])
check("data_dir_of slash only", P.data_dir_of(pa) == B + "/profiles/Dnable", P.data_dir_of(pa))
check("data_dir_of UNC local", P.data_dir_of(dict(pa, source_mode="local")) == "//172.30.1.93/MANUTeam")

# ---------------------------------------------------------------- UI (오프스크린, 임시 prefs)
TMP = tempfile.mkdtemp(prefix="a00210_paths_")
from Framework.qt.qt import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
P.PREFS_DIR = os.path.join(TMP, "prefs")
P.PROFILES_DIR = os.path.join(P.PREFS_DIR, "profiles")
P.ACTIVE_PATH = os.path.join(P.PREFS_DIR, "active.json")
P.PREFS_PATH = os.path.join(P.PREFS_DIR, "prefs.json")
os.makedirs(P.PROFILES_DIR)
store_bs = os.path.join(TMP, "repo").replace("/", "\\")
os.makedirs(os.path.join(store_bs, "profiles", "Dnable"))
P.save_profile("Back", dict(raw_a, store_dir=store_bs, project_root=TMP.replace("/", "\\"), scan_dir=""))
P.save_profile("Fwd", dict(raw_b, store_dir=store_bs.replace("\\", "/"), project_root=TMP.replace("\\", "/"), scan_dir=""))
P.set_active("Back")

from tools.A00210_FileManager.app.ui import main_window as mw   # noqa: E402
win = mw.MainWindow()
fields_back = (win.ipf_store_dir.text(), win.ipf_project_root.text(), win.path_structure_tab.ipf_recreate_to.text())
win.on_profile_changed("Fwd")
fields_fwd = (win.ipf_store_dir.text(), win.ipf_project_root.text(), win.path_structure_tab.ipf_recreate_to.text())
check("UI: \\ profile and / profile show identical text", fields_back == fields_fwd, (fields_back, fields_fwd))
check("UI: no backslash in fields", not any("\\" in f for f in fields_back), fields_back)
win.ipf_project_root.setText("C:\\typed\\path\\")
win.ipf_project_root.editingFinished.emit()
check("UI: typed path tidied on editing finished", win.ipf_project_root.text() == "C:/typed/path", win.ipf_project_root.text())
win.log_widget.clear()
win.log("Data folder: " + store_bs + "\\profiles\\Dnable")
check("UI: log shows slash path", "\\" not in win.log_widget.toPlainText(), win.log_widget.toPlainText())
win._save_current_to_active()
saved = P._read_json(os.path.join(P.PROFILES_DIR, "Fwd.json"), {})
check("UI: saved profile uses slash", "\\" not in saved.get("store_dir", "") and "\\" not in saved.get("project_root", ""),
      (saved.get("store_dir"), saved.get("project_root")))
check("UI: get_store_dir slash", "\\" not in win.get_store_dir(), win.get_store_dir())
mt = win.maya_tab
bar = getattr(mt, "mayapy_bar", None) or getattr(mt, "bar", None)
if bar is not None and hasattr(bar, "ipf_mayapy"):
    mw_paths = __import__("tools.A00210_FileManager.app.maya.ui.mayapy_bar", fromlist=["x"])
    orig = mw_paths.QFileDialog.getOpenFileName
    mw_paths.QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe", ""))
    try:
        bar.on_browse()
    finally:
        mw_paths.QFileDialog.getOpenFileName = orig
    check("UI: mayapy browse keeps slash (was normpath \\)", bar.ipf_mayapy.text() == "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe",
          bar.ipf_mayapy.text())
else:
    check("UI: mayapy bar found", False, [a for a in dir(mt) if "bar" in a.lower() or "mayapy" in a.lower()])
win.close()

print("RESULT {0}/{1}".format(sum(R), len(R)))
shutil.rmtree(TMP, ignore_errors=True)
