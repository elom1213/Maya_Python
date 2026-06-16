# Python Script by Ji Hun Park
# last Update date : 2026-06-16
# JUN_All - dependency doctor
#
# 이 프로젝트의 진짜 실패 모드는 "이 Maya 버전에서 모듈이 import 되는가" 이다.
# 정적 목록 대신, 실제로 import 를 시도해 보고 결과를 표로 보고한다.
#
# 사용법
#   - Maya 스크립트 에디터 / mayapy / 일반 python 어디서든:
#       import dev.check_dependencies as chk; chk.run()
#     또는 이 파일을 그대로 실행.
#
# stdlib 만 사용한다(importlib, sys). 경로를 __file__ 로 계산하지 않는다.

import sys
import importlib


# =========================
# CHECK TARGETS
# =========================
#
# kind:
#   "qt"           PySide6 우선, 실패 시 PySide2 (Framework.qt.qt 와 동일 규칙)
#   "maya"         Maya 가 제공해야 함 (pip 설치 대상 아님)
#   "standalone"   standalone / exe 빌드 venv 에서만 필요 (pip 설치)

QT_CANDIDATES = ["PySide6", "PySide2"]

CHECKS = [
    # (label, module, kind, note)
    ("pymel",       "pymel.core", "maya",       "Maya 제공. 사용 툴: A00150/160/170/190"),
    ("maya.cmds",   "maya.cmds",  "maya",       "Maya 제공. in-DCC 툴 공통"),
    ("pyinstaller", "PyInstaller", "standalone", "standalone .exe 빌드용"),
]


# =========================
# HELPERS
# =========================

def _try_import(module_name):
    """import 시도. (ok: bool, detail: str) 반환."""
    try:
        mod = importlib.import_module(module_name)
        ver = getattr(mod, "__version__", "")
        return True, (str(ver) if ver else "ok")
    except Exception as e:                                   # ImportError 외 환경 오류도 포착
        return False, "{}: {}".format(type(e).__name__, e)


def _resolve_qt():
    """PySide6 → PySide2 순으로 잡히는 첫 바인딩 반환. (name|None, detail)."""
    for name in QT_CANDIDATES:
        ok, detail = _try_import(name)
        if ok:
            return name, detail
    return None, "PySide6 / PySide2 모두 import 실패"


def _maya_version():
    try:
        import maya.cmds as cmds
        return str(cmds.about(version=True))
    except Exception:
        return "(not in Maya)"


# =========================
# MAIN
# =========================

def run(check_standalone=False):
    """의존성 점검 후 결과 표를 출력. 누락이 있으면 False 반환.

    check_standalone=True 이면 standalone(pyinstaller) 항목도 함께 검사한다.
    Maya 안에서 in-DCC 툴만 쓸 거면 기본값(False)으로 둔다.
    """

    lines = []
    missing = []

    lines.append("=" * 56)
    lines.append("JUN_All dependency check")
    lines.append("-" * 56)
    lines.append("Python : {}".format(sys.version.split()[0]))
    lines.append("Maya   : {}".format(_maya_version()))
    lines.append("-" * 56)

    # Qt 바인딩 (PySide6 → PySide2)
    qt_name, qt_detail = _resolve_qt()
    if qt_name:
        lines.append("[ OK     ] Qt binding    -> {} ({})".format(qt_name, qt_detail))
    else:
        lines.append("[ MISSING] Qt binding    -> {}".format(qt_detail))
        missing.append("Qt binding (PySide6/PySide2)")

    # 나머지 항목
    for label, module, kind, note in CHECKS:

        if kind == "standalone" and not check_standalone:
            lines.append("[ SKIP   ] {:<13} -> standalone 전용 (check_standalone=True 로 검사)".format(label))
            continue

        ok, detail = _try_import(module)

        if ok:
            lines.append("[ OK     ] {:<13} -> {}".format(label, detail))
        else:
            lines.append("[ MISSING] {:<13} -> {}".format(label, note))
            missing.append(label)

    lines.append("-" * 56)

    if missing:
        lines.append("RESULT : MISSING {} -> {}".format(len(missing), ", ".join(missing)))
        lines.append("  - 'maya' 항목 누락은 Maya 안에서 실행했는지 / 해당 Maya 가 제공하는지 확인.")
        lines.append("  - 'standalone' 항목 누락은: pip install -r JUN_All/requirements.txt")
    else:
        lines.append("RESULT : ALL OK")

    lines.append("=" * 56)

    print("\n".join(lines))
    return not missing


if __name__ == "__main__":
    run(check_standalone=True)
