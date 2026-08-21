---
name: new-tool-needs-icon
description: 새 툴을 만들면 아이콘(icon/TOOL.svg + .png)도 반드시 함께 만든다
metadata:
  node_type: memory
  type: feedback
---

**새 툴을 만들 때 아이콘이 없으면 만들어 준다.** 요청을 따로 받지 않아도 툴 생성 작업의
일부로 포함한다. 아이콘이 없으면 셸프 버튼이 기본 `pythonFamily.png` 로 떠서 셸프에서
구분이 안 된다.

## 규격 (in-Maya 툴 · arch B)

- 위치: `tools/A00XXX_Name/icon/A00XXX_Name.svg` + 같은 이름 `.png`
- **32 x 32**, SVG 로 그리고 PNG 로 래스터라이즈해 **둘 다** 저장
- 공통 배경 틀 — 기존 툴과 같아야 셸프에서 한 세트로 보인다:
  ```xml
  <rect x="1" y="1" width="30" height="30" rx="6"
        fill="#2d2d30" stroke="#4a4a4f" stroke-width="1.5"/>
  ```
- `__dragDrop_A00XXX.py` 는 이미 `icon/<툴이름>.png` 를 찾고 없으면 `pythonFamily.png` 로
  폴백하므로, 파일만 규칙대로 두면 자동으로 붙는다.

## SVG → PNG 래스터라이즈

`mayapy` + PySide2 `QSvgRenderer` 로 한다(별도 설치 불필요).

```python
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QImage, QPainter, QColor
from PySide2.QtSvg import QSvgRenderer
app = QApplication.instance() or QApplication([])
r = QSvgRenderer(src)                      # r.isValid() 확인
img = QImage(size, size, QImage.Format_ARGB32)
img.fill(QColor(0, 0, 0, 0))               # 투명 배경
p = QPainter(img); p.setRenderHint(QPainter.Antialiasing, True)
r.render(p); p.end(); img.save(dst, "PNG")
```

**standalone(arch B 터미널 실행) 툴은 요구사항이 더 있다** — 다중 크기 `.ico` +
AppUserModelID. → [[standalone-taskbar-icon-method]]

## 그릴 때 (실제로 겪은 것)

- **256px 로 렌더해서 눈으로 확인한 뒤 32px 도 확인한다.** 256 에서 멀쩡해도 32 에서
  뭉개진다. 특히 얇은 타원(`ry` 2 이하)은 32px 에서 선으로 뭉개진다.
- **요소는 적고 굵게.** 기존 아이콘들이 요소 2~3개다. 비슷한 크기 도형을 3개 이상
  늘어놓으면 산만해지고 32px 에서 못 알아본다.
- **둥근 모서리(rx=6)에 잘리지 않게** 안쪽으로 당긴다. 회전한 타원은 바운딩 박스가
  `sqrt((rx·cos θ)² + (ry·sin θ)²)` 라 눈대중보다 크다 — 실제로 좌하단이 잘렸었다.
- 크기 대비를 주면 체인/계층 같은 의미가 읽힌다(예: FK 링을 앞은 크게 뒤는 작게).

**Why:** 2026-08-21 A00460_ControllerTool 을 만들 때 아이콘을 빠뜨렸고, 사용자가
"앞으로 새 툴에 아이콘이 없으면 만들어야 한다"고 규칙으로 정했다.

**How to apply:** 툴 생성 커밋에 `icon/*.svg` + `*.png` 를 함께 넣는다. 가이드 문서
`docs/A00XXX_*.md` 의 구조 절에도 `icon/` 을 적는다. 관련: [[study-doc-request-recipe]] 와
같은 "요청에 딸려오는 기본 작업" 규칙이다.
