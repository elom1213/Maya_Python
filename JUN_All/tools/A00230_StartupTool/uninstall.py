# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00230_StartupTool - remove the boot launcher from the Windows Startup folder
#
#   python uninstall.py

import os
import sys

LAUNCHER_NAME = "A00230_StartupTool.vbs"


def startup_dir():
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, "Microsoft", "Windows",
                        "Start Menu", "Programs", "Startup")


def main():
    if os.name != "nt":
        print("[A00230] uninstall is Windows-only.", file=sys.stderr)
        return 1

    launcher = os.path.join(startup_dir(), LAUNCHER_NAME)
    if os.path.isfile(launcher):
        os.remove(launcher)
        print("[A00230] removed launcher: %s" % launcher)
    else:
        print("[A00230] launcher not found (nothing to remove): %s" % launcher)
    return 0


if __name__ == "__main__":
    sys.exit(main())
