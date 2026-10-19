# -*- coding: utf-8 -*-
# A00550_PoseMapper - capture / PhonemeDriver 시험 (mayapy 2024)
#   mayapy test_capture.py <테스트 씬 .mb>   (씬은 열기만, 저장하지 않는다)
import os
import sys

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00550_PoseMapper.app.core import attrs, capture, library, network   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


try:
    cmds.file(sys.argv[1], o=True, force=True, executeScriptNodes=False, ignoreVersion=True)
except RuntimeError:
    pass
src, bs = "JALI1:JALI_IN", "CHN_n_Face_xx_bs"
phon = ["AHH", "AAA", "Eh", "IEE", "OHH", "UUU", "WWW", "RRR", "SSS", "SSH", "FFF", "TTH", "MBP", "Schwa", "LNTD", "GK"]
print("  JaLi now:", cmds.getAttr("JALI1:CNT_JaLi.tx"), cmds.getAttr("JALI1:CNT_JaLi.ty"),
      "keyed phonemes:", len(cmds.listConnections("JALI1:CNT_PHONEMES", type="animCurve") or []))
check("settable plug follows JALI_IN.AAA -> CNT_PHONEMES.AAA", capture.settable_plug(src + ".AAA") == "JALI1:CNT_PHONEMES.AAA")

before = {p: cmds.getAttr("JALI1:CNT_PHONEMES." + p) for p in phon}
lib, info = capture.capture(src, phon, bs, attrs.target_attrs(bs), 10.0, name="cap")
after = {p: cmds.getAttr("JALI1:CNT_PHONEMES." + p) for p in phon}
check("P6 values restored after capture", before == after)
check("no problems", not info["problems"])
jaw = cmds.getAttr("JALI1:CNT_JaLi.tx") / 9.0
lip = cmds.getAttr("JALI1:CNT_JaLi.ty") / 9.0
print("  AHH pose:", lib.pose("AHH"))
print("  MBP pose:", lib.pose("MBP"))
default = library.load("jali_arkit_0040_default")
# 기본 라이브러리 값 x 지금 JaLi 배율 (jaw 계열은 Jaw, 나머지 Lip) 과 같아야 한다 (bw 를 손으로 바꾼 곳 제외)
exp = default.get("AHH", "jawOpen") * jaw
check("P1 AHH jawOpen {0:.3f} = default x Jaw/9 {1:.3f}".format(lib.get("AHH", "jawOpen"), exp), abs(lib.get("AHH", "jawOpen") - min(exp, 1.0)) < 2e-3)
exp2 = default.get("MBP", "mouthClose") * lip
check("P1 MBP mouthClose {0:.3f} = default x Lip/9 {1:.3f}".format(lib.get("MBP", "mouthClose"), exp2), abs(lib.get("MBP", "mouthClose") - min(exp2, 1.0)) < 2e-3)
check("baseline reported (non-speech targets)", isinstance(info["baseline"], dict))
print("  baseline:", info["baseline"])

# Solo preview
drv = capture.PhonemeDriver(src, phon)
drv.solo("OHH", 10.0)
check("solo OHH=10, AHH=0", cmds.getAttr(src + ".OHH") == 10.0 and cmds.getAttr(src + ".AHH") == 0.0)
drv.solo("AHH", 7.5)
check("switch to AHH 7.5", cmds.getAttr(src + ".AHH") == 7.5 and cmds.getAttr(src + ".OHH") == 0.0)
try:
    drv.solo("AHH", 15.0)
    check("ref above max -> error", False)
except capture.CaptureError as e:
    check("ref above max -> error ({0})".format(str(e)[:50]), "above the max" in str(e))
drv.restore()
check("P6 restore", {p: cmds.getAttr("JALI1:CNT_PHONEMES." + p) for p in phon} == before)

# 캡처한 포즈로 BS 에 replace 로 연결 -> 결과가 같아야 한다
lib.clamp = True
net, rep = network.build(lib, src, bs, prefix="cap_", on_existing="replace")
drv = capture.PhonemeDriver(src, phon)
drv.solo("AHH", 10.0)
v_new = cmds.getAttr(bs + ".jawOpen")
drv.restore()
check("rebuilt network gives the captured value ({0:.3f})".format(v_new), abs(v_new - lib.get("AHH", "jawOpen")) < 2e-3)
check("skip is default: building again on driven targets skips", network.build(lib, "JALI1:JALI_IN", "JALI1:ARKIT_OUT")[1]["skipped_existing"] != [])
print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
