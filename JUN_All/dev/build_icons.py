# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-23
# build_icons.py - 툴별 icon/*.svg 를 32x32 ARGB PNG 로 래스터화하는 개발 편의 스크립트.
#
# 사용 (추가 설치 없이 Maya 의 mayapy 권장):
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" dev/build_icons.py
# 또는 PySide2 가 있는 일반 python, 혹은 svglib/reportlab 폴백:
#   pip install svglib reportlab
#   python dev/build_icons.py
#
# 동작: JUN_All/tools/*/icon/*.svg 를 찾아 같은 폴더의 동명 .png(32x32)로 렌더한다. 멱등.

import os
import sys
import glob

ICON_SIZE = 32

# dev/ 의 부모 = JUN_All
JUN_ALL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(JUN_ALL_ROOT, "tools")


# =========================
# SVG 탐색
# =========================

def find_svgs():
    pattern = os.path.join(TOOLS_DIR, "*", "icon", "*.svg")
    return sorted(glob.glob(pattern))


# =========================
# 백엔드 1: PySide2 QtSvg (mayapy 등)
# =========================

def _qt_app():
    """오프스크린 QApplication 1회 보장 (QPainter 가 paint engine 을 잡으려면 필요)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide2.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


def render_qt(svg_path, png_path, size=ICON_SIZE):
    from PySide2.QtSvg import QSvgRenderer
    from PySide2.QtGui import QImage, QPainter, QColor

    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))  # 투명 배경

    renderer = QSvgRenderer(svg_path)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()

    return img.save(png_path, "PNG")


# =========================
# 백엔드 2: svglib + reportlab (cairo 불필요 폴백)
# =========================

def render_svglib(svg_path, png_path, size=ICON_SIZE):
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM

    drawing = svg2rlg(svg_path)
    if drawing is None:
        return False

    # 원본 뷰박스 → 32x32 로 스케일
    if drawing.width and drawing.height:
        sx = float(size) / float(drawing.width)
        sy = float(size) / float(drawing.height)
        drawing.width = size
        drawing.height = size
        drawing.scale(sx, sy)

    renderPM.drawToFile(drawing, png_path, fmt="PNG", bg=0xFFFFFF, configPIL={"transparent": None})
    return True


# =========================
# 백엔드 선택
# =========================

def pick_backend():
    try:
        _qt_app()
        from PySide2.QtSvg import QSvgRenderer  # noqa: F401
        return "qt"
    except Exception:
        pass
    try:
        import svglib.svglib  # noqa: F401
        import reportlab.graphics  # noqa: F401
        return "svglib"
    except Exception:
        pass
    return None


# =========================
# MAIN
# =========================

def main():
    svgs = find_svgs()
    if not svgs:
        print("[build_icons] No SVG found under tools/*/icon/*.svg")
        return 0

    backend = pick_backend()
    if backend is None:
        print("[build_icons] No rasterizer available.")
        print("  - Run with Maya's mayapy (PySide2 QtSvg), OR")
        print("  - pip install svglib reportlab")
        return 1

    print("[build_icons] backend = %s, %d svg(s)" % (backend, len(svgs)))

    ok = 0
    for svg in svgs:
        png = os.path.splitext(svg)[0] + ".png"
        try:
            if backend == "qt":
                done = render_qt(svg, png)
            else:
                done = render_svglib(svg, png)
            if done:
                ok += 1
                print("  [OK] %s" % os.path.relpath(png, JUN_ALL_ROOT))
            else:
                print("  [FAIL] %s" % os.path.relpath(svg, JUN_ALL_ROOT))
        except Exception as e:
            print("  [ERROR] %s : %s" % (os.path.relpath(svg, JUN_ALL_ROOT), e))

    print("[build_icons] done: %d/%d" % (ok, len(svgs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
