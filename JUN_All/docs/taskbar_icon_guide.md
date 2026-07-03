---
title: Standalone Qt 툴 작업표시줄 아이콘 만들기 (재사용 가이드)
aliases: [taskbar-icon, appusermodelid, standalone-icon, 작업표시줄아이콘]
tags: [guide, qt, pyside, standalone, icon, windows]
updated: 2026-07-03
---

# Standalone Qt 툴 작업표시줄 아이콘 만들기 (재사용 가이드)

> **대상**: 터미널에서 `python launch.py` 로 실행하는 **standalone PySide 툴**(아키텍처 B)의
> **Windows 작업표시줄 아이콘**을 바꾸는 방법. `A00210_FileManager` v01.27 에서 확립한 방식.
>
> Maya **셸프** 아이콘(32×32, `__dragDrop_*.py`)은 이 문서가 아니라 [icon_plan.md](icon_plan.md) 참고.
> (셸프=Maya 내부 drag-drop, 이 문서=OS 작업표시줄. 맥락이 다르다.)

---

## 0. 핵심 3줄 요약

1. **아이콘 제작**: SVG 로 디자인 → **QtSvg 로 사이즈별 렌더** → 멀티 사이즈 `.ico`(16~256px) + `.png`.
2. **아이콘 적용**: `app.setWindowIcon(QIcon(ico))` + 창에도 `setWindowIcon`.
3. **작업표시줄 반영(가장 중요)**: `QApplication` 생성 **전에** Windows **AppUserModelID** 를 지정.
   → 안 하면 터미널 실행 프로세스가 `python.exe` 라 **python 아이콘**이 뜬다.

---

## 1. 왜 AppUserModelID 가 필요한가

터미널에서 `python launch.py` 로 띄우면 실제 프로세스는 `python.exe` 다. Windows 작업표시줄은
프로세스의 **AppUserModelID(AUMID)** 로 창을 그룹핑하고 아이콘을 고르는데, 지정하지 않으면
`python.exe` 의 것을 쓴다. 그래서 `setWindowIcon` 만으로는 **창 좌상단 아이콘은 바뀌어도
작업표시줄은 python 아이콘**으로 남는다. AUMID 를 명시하면 이 프로세스를 별도 앱으로 인식해
우리 아이콘을 쓴다. (exe 빌드본에서도 그룹핑이 안정적이 된다.)

```python
import ctypes, sys
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Vendor.App.SubApp.Name")
```
- **반드시 `QApplication()` 생성 전에** 호출.
- ID 는 역-DNS 형태 문자열(예: `Dnable.JUN.A00210.FileManager`). 툴마다 고유하게.

---

## 2. 아이콘 제작 — SVG → QtSvg → 멀티 사이즈 .ico

**손그림 비트맵이 아니라 SVG 벡터로 그린 뒤 사이즈별로 렌더**한다. 핵심 함정 2개:

- ⚠️ **각 사이즈를 SVG 에서 직접 렌더**할 것. 하나의 큰 래스터(예: 256px)를 축소해 여러 프레임을
  만들면 작은 크기가 뭉갠다. (반대로 16px 한 장에서 확대하면 전부 저해상 — 실제로 겪은 버그)
- ⚠️ `.ico` 저장 시 **가장 큰 프레임을 base 로** `save(sizes=[...])`. base 가 16px 이면 Qt 가
  `availableSizes()` 에서 16 만 인식한다.

렌더 스크립트(오프스크린, 추가 네이티브 의존 없음 — `PySide6.QtSvg` + `Pillow`):

```python
# QT_QPA_PLATFORM=offscreen python make_icon.py
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QGuiApplication
from PySide6.QtSvg import QSvgRenderer
from PIL import Image

app = QGuiApplication(sys.argv)
renderer = QSvgRenderer("TOOL.svg")

def render(size, path):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(p)
    p.end()
    img.save(path)

render(256, "TOOL.png")                       # 고해상 마스터 PNG
sizes = [16, 24, 32, 48, 64, 128, 256]
frames = []
for s in sizes:                               # 각 사이즈를 SVG 에서 직접 렌더
    fp = "f_%d.png" % s
    render(s, fp)
    frames.append(Image.open(fp).convert("RGBA"))
frames[-1].save("TOOL.ico", format="ICO", sizes=[(s, s) for s in sizes])  # base=최대
```

검증: `QIcon("TOOL.ico").availableSizes()` 가 `[16,24,32,48,64,128,256]` 을 다 보이면 OK.

### 저장 위치 / 디자인
- 툴 폴더 안 `icon/` 에 `TOOL.svg`(소스) + `TOOL.png`(256) + `TOOL.ico`(멀티) 를 함께 둔다(자기완결).
- 앱 테마(예: `blue_dark`)와 톤을 맞추고, 라운드-스퀘어 배경 + 도메인 글리프 하나로 작은 크기에서도
  식별되게. 텍스트는 피한다(작은 사이즈 가독성).

---

## 3. 코드 배선 (A00210 실제 구조)

### `app/config/app_meta.py` — AUMID + 아이콘 경로 해석기 (UI/DCC 비의존)
```python
APP_USER_MODEL_ID = "Dnable.JUN.A00210.FileManager"

def icon_path(prefer_ico=True):
    """dev(소스) · PyInstaller(_MEIPASS) 양쪽에서 아이콘 절대경로 반환(없으면 '')."""
    # tool_root/icon/ 및 (frozen 이면) sys._MEIPASS/icon 에서 .ico → .png 순 탐색
```
- **왜 별도 모듈?**: `launch.py` 와 `main_window.py` 가 같은 값을 공유하고, exe(`sys.frozen`/`_MEIPASS`)
  경로까지 한 곳에서 처리하기 위함.

### `launch.py`
```python
def _set_windows_app_id():
    if sys.platform != "win32": return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass

def main():
    _set_windows_app_id()                 # QApplication 생성 전!
    app = QApplication(sys.argv)
    p = icon_path()
    if p: app.setWindowIcon(QIcon(p))     # 앱 전역 아이콘
    ...
```

### `main_window.py`
```python
_sIcon = icon_path()
if _sIcon:
    self.setWindowIcon(QIcon(_sIcon))     # 다른 진입점으로 창만 띄우는 경우까지 대비
```

### `build_exe.bat` (PyInstaller)
```
--icon "icon/TOOL.ico" ^          (exe 파일 자체 아이콘)
--add-data "icon;icon" ^          (런타임에 QIcon 이 찾도록 번들)
```

---

## 4. 체크리스트 (새 툴에 적용할 때)

- [ ] `icon/TOOL.svg` 디자인(테마 톤 + 도메인 글리프).
- [ ] 위 스크립트로 `TOOL.png`(256) + `TOOL.ico`(16~256, base=최대) 생성. 임시 `f_*.png` 삭제.
- [ ] `app/config/app_meta.py` 에 고유 `APP_USER_MODEL_ID` + `icon_path()`.
- [ ] `launch.py`: `_set_windows_app_id()` **QApplication 전** + `app.setWindowIcon`.
- [ ] `main_window.py`: `self.setWindowIcon`.
- [ ] `build_exe.bat`: `--icon` + `--add-data "icon;icon"`.
- [ ] 검증: `py_compile`, 오프스크린 스모크(`icon_path()` 존재 · `QIcon.availableSizes()` 다중 · 창 아이콘 non-null).
- [ ] 실기: 터미널 `python launch.py` → 작업표시줄에 앱 아이콘. (python 아이콘이 고정 캐시로 남으면
      작업표시줄 고정 해제 후 재실행.)

---

## 5. 참고
- 이 방식 첫 적용: `A00210_FileManager` v01.27 (docs [A00210_FileManager](A00210_FileManager.md) §2).
- Maya 셸프 아이콘(다른 맥락): [icon_plan.md](icon_plan.md).
