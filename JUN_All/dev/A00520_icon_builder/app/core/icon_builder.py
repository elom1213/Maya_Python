# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00520_icon_builder - 툴별 icon/*.svg 를 32x32 ARGB PNG 로 래스터화 (옛 dev/build_icons.py, 2026-06-23)
#
# 동작: JUN_All/tools/*/icon/*.svg 와 JUN_All/dev/*/icon/*.svg 를 찾아 같은 폴더의 동명 .png(32x32)로
# 렌더한다. 멱등. 백엔드는 PySide2 QtSvg(mayapy) 우선, 없으면 svglib + reportlab.
# make_ico 면 .ico(16~256 다중 크기)도 만든다 - Pillow 가 있을 때만(mayapy 에는 없다, 시스템 python 에 있다).
#
# UI 비의존. 마야 없이도 돈다 (QApplication 은 오프스크린으로 스스로 만든다).

import os
import sys
import glob

ICON_SIZE = 32
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)

# core -> app -> A00520_icon_builder -> dev -> JUN_All
JUN_ALL_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SCAN_DIRS = ("tools", "dev")


# =========================
# SVG 탐색
# =========================

def find_svgs(only=None):
    """tools/*/icon/*.svg + dev/*/icon/*.svg (정렬). only 가 있으면 툴 폴더 이름에 그 글자가 든 것만."""
    svgs = []
    for sub in SCAN_DIRS:
        svgs.extend(glob.glob(os.path.join(JUN_ALL_ROOT, sub, "*", "icon", "*.svg")))
    svgs = sorted(set(svgs))
    if only:
        svgs = [s for s in svgs if only in os.path.basename(os.path.dirname(os.path.dirname(s)))]
    return svgs


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


def render_qt_image(svg_path, size):
    from PySide2.QtSvg import QSvgRenderer
    from PySide2.QtGui import QImage, QPainter, QColor

    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))  # 투명 배경

    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        raise ValueError("invalid svg")
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    return img


def render_qt(svg_path, png_path, size=ICON_SIZE):
    return render_qt_image(svg_path, size).save(png_path, "PNG")


# =========================
# 백엔드 2: svglib + reportlab (cairo 불필요 폴백)
# =========================

def render_svglib(svg_path, png_path, size=ICON_SIZE):
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM

    drawing = svg2rlg(svg_path)
    if drawing is None:
        return False

    # 원본 뷰박스 -> size 로 스케일
    if drawing.width and drawing.height:
        sx = float(size) / float(drawing.width)
        sy = float(size) / float(drawing.height)
        drawing.width = size
        drawing.height = size
        drawing.scale(sx, sy)

    renderPM.drawToFile(drawing, png_path, fmt="PNG", bg=0xFFFFFF, configPIL={"transparent": None})
    return True


# =========================
# .ico (standalone 툴의 작업 표시줄용) - Pillow 가 있을 때만
# =========================

def ico_available():
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def make_ico(svg_path, ico_path, sizes=ICO_SIZES):
    """각 크기를 SVG 에서 직접 렌더(축소 금지)해 다중 크기 .ico 로. Qt 백엔드 + Pillow 가 필요하다."""
    from PIL import Image
    frames = []
    for size in sizes:
        img = render_qt_image(svg_path, size)
        tmp = ico_path + ".{0}.tmp.png".format(size)
        img.save(tmp, "PNG")
        frames.append(Image.open(tmp).convert("RGBA"))
    base = frames[-1]
    base.save(ico_path, format="ICO", sizes=[(f.width, f.height) for f in frames],
              append_images=frames[:-1])
    for size in sizes:
        try:
            os.remove(ico_path + ".{0}.tmp.png".format(size))
        except OSError:
            pass
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

def build_all(only=None, make_ico_files=False, make_ico=None, log=print):
    """svg 전부를 png 로 (옵션 .ico). 반환 dict:
        ok     : 쓴 png 경로들
        failed : (svg 경로, 이유)
        ico    : 쓴 ico 경로들
        ico_available : Pillow 가 있는가
        backend : "qt" / "svglib" / None
    """
    if make_ico is not None:            # launch 가 make_ico= 로 부른다
        make_ico_files = make_ico

    report = {"ok": [], "failed": [], "ico": [], "ico_available": ico_available(), "backend": None}

    svgs = find_svgs(only)
    if not svgs:
        log("[IconBuilder] No SVG found under tools/*/icon or dev/*/icon{0}".format(
            " (only={0})".format(only) if only else ""))
        return report

    backend = pick_backend()
    report["backend"] = backend
    if backend is None:
        log("[IconBuilder] No rasterizer available.")
        log("  - Run with Maya's mayapy (PySide2 QtSvg), OR")
        log("  - pip install svglib reportlab")
        report["failed"] = [(s, "no rasterizer") for s in svgs]
        return report

    log("[IconBuilder] backend = {0}, {1} svg(s)".format(backend, len(svgs)))

    for svg in svgs:
        png = os.path.splitext(svg)[0] + ".png"
        rel = os.path.relpath(svg, JUN_ALL_ROOT)
        try:
            done = render_qt(svg, png) if backend == "qt" else render_svglib(svg, png)
            if done:
                report["ok"].append(png)
                log("  [OK] {0}".format(os.path.relpath(png, JUN_ALL_ROOT)))
            else:
                report["failed"].append((rel, "render returned False"))
                log("  [FAIL] {0}".format(rel))
        except Exception as e:
            report["failed"].append((rel, str(e)))
            log("  [ERROR] {0} : {1}".format(rel, e))
            continue

        if make_ico_files and backend == "qt" and report["ico_available"]:
            ico = os.path.splitext(svg)[0] + ".ico"
            try:
                make_ico(svg, ico)
                report["ico"].append(ico)
                log("  [OK] {0}".format(os.path.relpath(ico, JUN_ALL_ROOT)))
            except Exception as e:
                report["failed"].append((rel, "ico: {0}".format(e)))
                log("  [ERROR] {0} ico : {1}".format(rel, e))

    if make_ico_files and not report["ico_available"]:
        log("[IconBuilder] Pillow not available - .ico skipped (use the system python for ico)")

    log("[IconBuilder] done: {0}/{1}".format(len(report["ok"]), len(svgs)))
    return report
