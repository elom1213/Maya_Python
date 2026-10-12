# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00520_icon_builder - launch entry point (dev tool, in-Maya or mayapy)
#
# tools/*/icon/*.svg 와 dev/*/icon/*.svg 를 32x32 PNG 로 굽는다 (옛 dev/build_icons.py).
# 창이 없다. 셸프 버튼(__dragDrop_A00520.py)은 run() 을 부르고, 터미널은 이 파일을 mayapy 로 실행한다.
#
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" dev/A00520_icon_builder/launch.py [--only A00440] [--ico]
#
# 개발 전용이라 릴리즈본(dev/ 제외)에는 실리지 않는다.

import os
import sys

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))          # .../dev/A00520_icon_builder
ROOT = os.path.abspath(os.path.join(TOOL_ROOT, "..", ".."))      # .../JUN_All

if ROOT not in sys.path:
    sys.path.append(ROOT)


def _in_view(message):
    """마야 뷰포트 메시지. 마야가 아니면(mayapy · 테스트) 조용히 건너뛴다."""
    try:
        import maya.cmds as cmds
        cmds.inViewMessage(amg=message, pos="midCenter", fade=True)
    except Exception:
        pass


def run(only=None, make_ico=False):
    """모든 툴 아이콘을 다시 굽는다. 반환 {"ok": [...], "failed": [(svg, 이유)...], "skipped": [...]}.

    only     : 툴 폴더 이름의 일부 (예: "A00440") - 그 툴만.
    make_ico : True 면 .png 옆에 다중 크기 .ico 도 (Pillow 가 있을 때만, 없으면 건너뛰고 알린다).
    """
    from dev.A00520_icon_builder.app.core import icon_builder

    report = icon_builder.build_all(only=only, make_ico=make_ico)

    print("[IconBuilder] {0} png written, {1} failed, {2} ico{3}".format(
        len(report["ok"]), len(report["failed"]), len(report["ico"]),
        "" if report["ico_available"] or not make_ico else " (Pillow not available - ico skipped)"))
    for svg, why in report["failed"]:
        print("[IconBuilder]   FAILED {0} : {1}".format(svg, why))

    if report["failed"]:
        _in_view("<hl>Icons</hl> {0} written, <hl>{1} failed</hl> - see Script Editor".format(
            len(report["ok"]), len(report["failed"])))
    else:
        _in_view("<hl>Icons</hl> {0} png written".format(len(report["ok"])))
    return report


if __name__ == "__main__":
    only = None
    make_ico = "--ico" in sys.argv
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    result = run(only=only, make_ico=make_ico)
    sys.exit(1 if result["failed"] else 0)
