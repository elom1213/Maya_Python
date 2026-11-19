# -*- coding: utf-8 -*-
# Framework/qt/MOD_sliderStyle_qt_v01 시험 (오프스크린). PySide6 = 시스템 python, PySide2 = mayapy 둘 다 돈다.
#   python test_slider_style.py
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_slider_style.py
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)

from Framework.qt.qt import *   # noqa: E402,F403
from Framework.qt import MOD_sliderStyle_qt_v01 as S   # noqa: E402
from Framework.themes.theme_manager import ThemeManager   # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)
R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# 1. 테마 색 읽기
c = S.theme_colors("green_dark")
check("green_dark colors", c == {"accent": "#6f9e80", "field": "#353835", "window": "#2b2b2b"}, c)
styles = sorted(f[:-4] for f in os.listdir(S._styles_dir()) if f.endswith(".qss"))
fallback = []
for name in styles:
    S._COLOR_CACHE.pop(name, None)
    got = S.theme_colors(name)
    with open(os.path.join(S._styles_dir(), name + ".qss"), encoding="utf-8") as fh:
        text = fh.read().lower()
    # 강조색은 그 테마 qss 에 있는 색이거나(버튼 테두리), 테두리가 없는 무채색 테마(dark)면 버튼 배경을 밝힌 회색이어야 한다
    accent_ok = got["accent"] in text or (name == "dark" and len(set(got["accent"][1:][i:i + 2] for i in (0, 2, 4))) == 1)
    if not (accent_ok and got["window"] in text):
        fallback.append((name, got))
check("every theme's colors come from its own qss ({0})".format(len(styles)), not fallback, fallback)

# 2. 스타일시트
qss = S.slider_style("green_dark")
check("style covers horizontal + vertical + disabled",
      all(k in qss for k in ("QSlider::groove:horizontal", "QSlider::groove:vertical",
                             "QSlider::handle:horizontal:disabled", "#6f9e80")))
check("fill=False does not paint the filled side with the accent",
      "QSlider::sub-page:horizontal { background: #6f9e80" not in S.slider_style("green_dark", fill=False)
      and "QSlider::sub-page:horizontal { background: #6f9e80" in qss)
light = S.slider_style("coral_light")
check("light theme : accent handle", "background: " + S.theme_colors("coral_light")["accent"] + ";" in light)


# 3. 위젯 : 보일 때 칠한다, 남이 칠한 것은 그대로
def make_root():
    root = QWidget()
    lay = QVBoxLayout(root)
    a = QSlider(Qt.Horizontal)
    a.setRange(0, 100)
    a.setValue(70)
    b = QSlider(Qt.Vertical)
    own = QSlider(Qt.Horizontal)
    own.setStyleSheet("QSlider::groove:horizontal { background: red; }")
    for w in (a, b, own):
        lay.addWidget(w)
    root.resize(300, 200)
    return root, a, b, own


root, a, b, own = make_root()
ThemeManager.load_theme_to_widget(root, "green_dark")
helper = S.JUN_mod_sliderStyle_qt_v01(root)
check("not painted before it is shown", a.styleSheet() == "")
root.show()
app.processEvents()
check("painted on show (both orientations)", "#6f9e80" in a.styleSheet() and "#6f9e80" in b.styleSheet())
check("a slider with its own style is left alone", own.styleSheet() == "QSlider::groove:horizontal { background: red; }")

# 4. 실제 픽셀 : 가운데 줄에서 배경과 다른 픽셀이 대부분이어야 홈이 보인다
app.processEvents()
img = a.grab().toImage()
y = img.height() // 2
bg = QColor("#2b2b2b")


def far(col):
    return abs(col.red() - bg.red()) + abs(col.green() - bg.green()) + abs(col.blue() - bg.blue()) > 30


seen = sum(1 for x in range(img.width()) if far(img.pixelColor(x, y)))
check("groove is visible against the background (middle row)", seen > img.width() * 0.8, (seen, img.width()))
left = img.pixelColor(int(img.width() * 0.25), y)
check("filled side shows the accent", left.name() == "#6f9e80", left.name())

# 5. 테마가 바뀌면 다음에 보일 때 다시 칠한다
root.hide()
ThemeManager.load_theme_to_widget(root, "coral_light")
root.show()
app.processEvents()
accent_light = S.theme_colors("coral_light")["accent"]
check("repainted with the new theme on the next show", accent_light in a.styleSheet(), accent_light)

# 6. 비활성
a.setEnabled(False)
app.processEvents()
img = a.grab().toImage()
check("disabled slider still draws a groove", any(img.pixelColor(x, img.height() // 2).name() != "#fdf1ee"
                                                   for x in range(img.width())))

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
