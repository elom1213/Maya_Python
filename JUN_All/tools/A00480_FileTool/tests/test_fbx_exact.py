# -*- coding: utf-8 -*-
# A00480_FileTool v01.13 - Mocap FBX Import (Exact Rotation) 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_fbx_exact.py
# 합성 씬(XZY 조인트 + ±180 을 넘는 회전 키)을 마야로 FBX 로 내보내 다시 임포트한다 - 실파일 없이 돈다.
# 환경 변수 JUN_FBX_TEST_DIR 이 있으면 실파일도 본다 (BCM_01_004.fbx 임포트 · 0010_motion_0010.mb 고치기, 1분쯤).
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.mel as mel   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import maya_fbx, maya_fbx_exact as fx, euler_math as em   # noqa: E402
from tools.A00480_FileTool.app import core   # noqa: E402
from tools.A00480_FileTool.app.ui.import_fbx_exact import FbxExactImportSection   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def has(logs, text):
    return any(text in line for line in logs)


TMP = tempfile.mkdtemp(prefix="jun_a00480_fbx_exact_")

# ---------------------------------------------------------------- 합성 FBX
cmds.file(new=True, force=True)
cmds.currentUnit(time="ntsc")
rig = cmds.group(empty=True, name="Rig")
cmds.select(clear=True)
hips = cmds.joint(name="Hips", position=(0, 10, 0))
spine = cmds.joint(name="Spine", position=(0, 15, 0))
end = cmds.joint(name="Spine_end", position=(0, 18, 0))
cmds.parent(hips, rig)
hips, spine = "|Rig|Hips", "|Rig|Hips|Spine"
cmds.setAttr(hips + ".rotateOrder", 3)            # xzy
cmds.setAttr(hips + ".jointOrient", 10, 0, 0)
cmds.setAttr(spine + ".rotateOrder", 2)           # zxy
loc = cmds.spaceLocator(name="Marker1")[0]
cmds.parent(loc, rig)
for frame in range(1, 41):
    rx = -175.0 + frame * 9.0                    # -166 ... 185 : +-180 을 넘는다
    cmds.setKeyframe(hips, attribute="rotateX", time=frame, value=rx)
    cmds.setKeyframe(hips, attribute="rotateY", time=frame, value=70.0 + frame)   # 가운데 축이 90 을 넘나든다
    cmds.setKeyframe(hips, attribute="rotateZ", time=frame, value=-170.0 + frame * 0.5)
    cmds.setKeyframe(hips, attribute="translateY", time=frame, value=10.0 + 0.1 * frame)
    cmds.setKeyframe(spine, attribute="rotateY", time=frame, value=frame * 2.0)
cmds.playbackOptions(minTime=1, maxTime=40)
fbx_path = os.path.join(TMP, "synthetic.fbx").replace("\\", "/")
maya_fbx.ensure_fbx_plugin()
cmds.select(rig, hierarchy=True)
cmds.file(fbx_path, force=True, options="v=0;", typ="FBX export", pr=True, es=True)
check("synthetic FBX written", os.path.isfile(fbx_path))

# ---------------------------------------------------------------- scan
info, logs = core.scan_fbx_exact(fbx_path)
check("scan : one skeleton", info and [n for n, _c in info["skeletons"]] == ["Rig"], info and info["skeletons"])
check("scan : 30 fps, frames 1-40", info and info["settings"]["fps"] == 30.0
      and (info["settings"]["start"], info["settings"]["stop"]) == (1.0, 40.0), info and info["settings"])
bad_info, bad_logs = core.scan_fbx_exact(os.path.join(TMP, "missing.fbx"))
check("scan : missing file -> FAIL log", bad_info is None and bad_logs[0].startswith("[FAIL]"), bad_logs)

# ---------------------------------------------------------------- import (Normalize ON = 기본)
cmds.file(new=True, force=True)
quat_before = mel.eval("FBXImportQuaternion -q")
mode_before = mel.eval("FBXImportMode -q")
ok, logs = core.import_fbx_exact(fbx_path)
print("\n".join("    " + line for line in logs))
check("import : ok", ok)
check("import : verify passed", has(logs, "[OK] Verify"))
check("import : FBX options restored", (mel.eval("FBXImportQuaternion -q"), mel.eval("FBXImportMode -q")) ==
      (quat_before, mode_before))
check("import : undo state restored", cmds.undoInfo(query=True, state=True))
check("import : marker removed (Skeletons only)", not cmds.objExists("|Rig|Marker1"))
check("import : normalized jo 0 / ro xyz", cmds.getAttr(hips + ".rotateOrder") == 0
      and all(abs(v) < 1e-9 for v in cmds.getAttr(hips + ".jointOrient")[0]))
values = cmds.keyframe(cmds.listConnections(hips + ".rx", s=True, d=False)[0], q=True, vc=True)
check("import : no jumps over 180", em.count_jumps(values) == 0)
check("import : timeline = file", (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True))
      == (1.0, 40.0))

# 이름 충돌 -> FAIL, 씬은 그대로
n_before = len(cmds.ls(type="joint"))
ok2, logs2 = core.import_fbx_exact(fbx_path)
check("import again : name clash -> FAIL", not ok2 and has(logs2, "already has 'Rig'"), logs2[-1])
check("import again : scene unchanged", len(cmds.ls(type="joint")) == n_before)

# ---------------------------------------------------------------- import (Normalize OFF) + Fix
cmds.file(new=True, force=True)
ok, logs = core.import_fbx_exact(fbx_path, normalize=False, skeletons_only=False)
check("import raw : ok + verify", ok and has(logs, "[OK] Verify"))
check("import raw : keeps file layout (xzy, jo 10)", cmds.getAttr(hips + ".rotateOrder") == 3
      and abs(cmds.getAttr(hips + ".jointOrientX") - 10.0) < 1e-6)
check("import raw : marker kept (Skeletons only off)", cmds.objExists("|Rig|Marker1"))

# 회전 키를 망가뜨린 뒤 Fix Scene From FBX
curve = cmds.listConnections(hips + ".rx", s=True, d=False)[0]
cmds.keyframe(curve, edit=True, time=(10, 20), relative=True, valueChange=37.0)
ok, logs = core.fix_scene_from_fbx(fbx_path, normalize=False)
print("\n".join("    " + line for line in logs))
check("fix : ok + verify", ok and has(logs, "[OK] Verify"))
check("fix : reports the broken joint", has(logs, "Hips (10-20)"), [l for l in logs if "Hips" in l])
cmds.setAttr(spine + ".rotateOrder", 0)
ok, logs = core.fix_scene_from_fbx(fbx_path, normalize=False)
check("fix : joint with other rotateOrder skipped", has(logs, "[SKIP] Spine"), [l for l in logs if "SKIP" in l])

# ---------------------------------------------------------------- UI
section = FbxExactImportSection(log=lambda m: None)
section.le_path.setText(fbx_path)
section.on_scan()
check("ui : skeleton checkbox", [n for n, _c in section.skeleton_checks] == ["Rig"])
check("ui : buttons enabled", section.btn_import.isEnabled() and section.btn_fix.isEnabled())
check("ui : unwrap disabled while normalize on", not section.chk_unwrap.isEnabled())
section._check_all(False)
check("ui : import disabled with no skeleton", not section.btn_import.isEnabled())
section.chk_normalize.setChecked(False)
check("ui : unwrap enabled when normalize off", section.chk_unwrap.isEnabled())

# ---------------------------------------------------------------- 실파일 (있으면)
real = os.environ.get("JUN_FBX_TEST_DIR")
bcm = os.path.join(real or "", "0010_origin", "BCM_01_004.fbx")
if real and os.path.isfile(bcm):
    cmds.file(new=True, force=True)
    ok, logs = core.import_fbx_exact(bcm, skeletons=["CHOEUN"])
    print("\n".join("    " + line for line in logs))
    check("[BCM] import CHOEUN : ok + verify", ok and has(logs, "[OK] Verify"))
    check("[BCM] Maya flips found : Hips 1-5493, RightArm 3707-6285",
          has(logs, "Hips (1-5493), RightArm (3707-6285)"))
    check("[BCM] only CHOEUN left", cmds.ls(assemblies=True) == ["persp", "top", "front", "side", "CHOEUN"],
          cmds.ls(assemblies=True))
    motion = os.path.join(real, "0010_motion_0010.mb")
    if os.path.isfile(motion):
        cmds.file(motion, open=True, force=True)
        ok, logs = core.fix_scene_from_fbx(bcm, roots=["|CHOEUN"])
        print("\n".join("    " + line for line in logs))
        check("[BCM] fix user scene CHOEUN : ok + verify", ok and has(logs, "[OK] Verify"))
else:
    print("SKIP real files (set JUN_FBX_TEST_DIR)")

shutil.rmtree(TMP, ignore_errors=True)
print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
