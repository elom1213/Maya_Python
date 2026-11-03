# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-03
# A00510_release_builder - 툴 폴더에 아이콘이 보이는 바로가기(.lnk) 만들기 (v01.04)
#
# .bat 파일은 Windows 가 아이콘을 바꿀 수 없다(항상 톱니 문서 아이콘). 그래서
# Run_ReleaseBuilder.bat 이 이 스크립트를 불러 **툴 아이콘이 박힌 바로가기**
# `Release Builder.lnk` 를 툴 폴더에 만든다. 탐색기에서 평소에도 툴 아이콘으로 보이고,
# 더블클릭하면 콘솔 없이(pythonw) 창이 뜬다.
#
# - 바로가기에 launch 와 같은 AppUserModelID 를 넣는다 -> 바로가기로 띄운 창도 작업 표시줄에
#   툴 아이콘으로 묶이고, 작업 표시줄에 고정해도 파이썬 아이콘이 아니다.
# - .lnk 는 절대 경로(파이썬 · 툴 폴더)를 담으므로 git 에 넣지 않는다(.gitignore).
#   지금 내용을 `.shortcut_stamp` 에 적어 두고, 파이썬이나 폴더가 바뀌었을 때만 다시 만든다
#   (만들 때 PowerShell C# 컴파일로 1-2 초 걸리므로 매번 만들지 않는다).
#
# 사용: python make_shortcut.py [--force]
#   종료 코드 0 = 있음/만듦, 1 = 실패 (실패해도 bat 은 툴을 그대로 띄운다)

import os
import sys

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TOOL_ROOT, "..", ".."))      # -> JUN_All

if ROOT not in sys.path:
    sys.path.append(ROOT)

LNK_NAME = "Release Builder.lnk"
STAMP_NAME = ".shortcut_stamp"
DESCRIPTION = "Release Builder - copy chosen tools + Framework to a release folder (dev only)"


def _app_meta():
    # app_meta 는 Qt(QIcon) 를 import 한다. 여기선 경로 · ID 만 필요하지만 같은 값을 쓰려고 그대로 읽는다.
    from dev.A00510_release_builder.app.config import app_meta
    return app_meta


def ensure_shortcut(force=False):
    from Framework.core import shell_integration as shell

    if not shell.is_supported():
        print("[Shortcut] Windows only - skipped")
        return None

    meta = _app_meta()
    icon = meta.icon_path("ico") or ""
    spec = shell.launch_spec(TOOL_ROOT, icon)

    lnk = os.path.join(TOOL_ROOT, LNK_NAME)
    stamp_path = os.path.join(TOOL_ROOT, STAMP_NAME)
    stamp = "|".join([spec.target, spec.arguments, spec.workdir, spec.icon, meta.APP_USER_MODEL_ID])

    if not force and os.path.isfile(lnk) and os.path.isfile(stamp_path):
        try:
            with open(stamp_path, "r", encoding="utf-8") as f:
                if f.read().strip() == stamp:
                    return lnk                              # 그대로 쓸 수 있다
        except OSError:
            pass

    shell.create_shortcut(lnk, spec, meta.APP_USER_MODEL_ID, DESCRIPTION)

    with open(stamp_path, "w", encoding="utf-8") as f:
        f.write(stamp)

    print("[Shortcut] {0}".format(lnk))
    return lnk


if __name__ == "__main__":
    try:
        ensure_shortcut(force="--force" in sys.argv[1:])
    except Exception as e:                                  # noqa: BLE001
        print("[Shortcut] FAILED: {0}".format(e))
        sys.exit(1)
