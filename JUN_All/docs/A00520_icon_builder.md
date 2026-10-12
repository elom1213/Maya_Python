# A00520_icon_builder — Icons (사용 안내)

툴별 `icon/*.svg` 를 **32x32 ARGB png** 로 굽는 개발 도구다. 옛 `dev/build_icons.py`(2026-06-23) 를
툴 폴더로 옮긴 것으로, 셸프 버튼과 mayapy 양쪽에서 쓴다.

- 버전: `v01.00` (`app/config/version.py`)
- 위치: `JUN_All/dev/A00520_icon_builder` — 개발 도구라 `dev/` (릴리즈본에는 실리지 않는다)
- 창이 없다. 결과는 스크립트 에디터와 뷰포트 메시지.

## 1. 실행

- 마야 셸프: `__dragDrop_A00520.py` 를 뷰포트로 드롭 → `Icons` 버튼. 누르면 **모든** 툴 아이콘을 다시 굽는다.
- 터미널 (추가 설치 없이 mayapy 권장):

```bash
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" dev/A00520_icon_builder/launch.py
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" dev/A00520_icon_builder/launch.py --only A00440
python dev/A00520_icon_builder/launch.py --only A00510 --ico      # .ico 는 Pillow 가 있는 시스템 python 으로
```

## 2. 동작

- 훑는 곳: `JUN_All/tools/*/icon/*.svg` **와 `JUN_All/dev/*/icon/*.svg`** (옛 스크립트는 tools 만 봤다).
- 각 svg 옆에 동명 `.png` 를 쓴다. 멱등.
- 백엔드: PySide2 `QSvgRenderer`(mayapy) 우선, 없으면 `svglib + reportlab`.
- `--ico` / `run(make_ico=True)`: 16·24·32·48·64·128·256 을 **svg 에서 각각 렌더**해 다중 크기 `.ico` 로
  (standalone 툴의 작업 표시줄용, [standalone_taskbar_icon](taskbar_icon_guide.md)). **Pillow 가 필요**하고 mayapy 에는 없다 — 없으면 건너뛰고 알린다.
- `run(only=...)` 은 툴 폴더 이름에 그 글자가 든 것만.

그리는 규격(32px, 공통 배경 틀)은 [icon_plan](icon_plan.md).

## 3. 구조

```
dev/A00520_icon_builder/
├── __init__.py · launch.py (run(only, make_ico) -> report) · __dragDrop_A00520.py
├── icon/A00520_icon_builder.svg|.png
└── app/
    ├── config/version.py
    └── core/icon_builder.py     # find_svgs / render_qt / render_svglib / make_ico / build_all (UI 비의존)
```
