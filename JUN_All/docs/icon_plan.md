---
title: Maya 툴 셸프 아이콘 생성 계획서
aliases: [icon-plan, shelf-icon, 아이콘계획]
tags: [plan, maya, shelf, icon]
updated: 2026-06-23
---

# Maya 툴 셸프 아이콘 생성 계획서

## 1. 목적 / 배경

`JUN_All/tools/` 의 **Maya 내부에서 동작하는 모든 툴**은 `__dragDrop_*.py` 를 Maya 뷰포트에
드래그&드롭하면 셸프 버튼이 설치된다. 그러나 현재 **모든 버튼이 동일한 기본 아이콘
`pythonFamily.png`** 를 쓴다(모든 drag-drop 파일에 `ICON_NAME = "pythonFamily.png"` 하드코딩).
→ 셸프에서 툴을 **시각적으로 구분할 수 없다**.

이 작업의 목표:

> Maya 사용자 아이콘 폴더(`C:\Users\USER\Documents\maya\2024\prefs\icons`)의 **`Ari*` 아이콘
> 스타일을 학습**해, 그와 유사한 톤의 **툴별 고유 32×32 셸프 아이콘**을 만들고, 각 툴의
> drag-drop 이 그 아이콘을 가리키게 한다.

### 확정된 결정 사항
- **생성 방식**: SVG 작성 후 래스터화(손그림 비트맵 대신 벡터 작성 → PNG).
- **저장 경로**: 각 툴 폴더 안 `icon/` 폴더(툴 자기완결성 유지).
- **적용 범위**: 실사용 Maya 툴만(베이스 템플릿 제외, 버전 중복은 현행 우선).
- **drag-drop 처리**: 전체 처리 — 기존 파일 `image1` 갱신 + 없는 툴은 신규 생성.

---

## 2. Ari 아이콘 스타일 분석 (학습 결과)

`prefs/icons` 의 `Ari*` 9개(`AriSortOutliner`, `AriUVAdsorption`, `AriUVAdsorptionMove`,
`AriSamePositionSelector`, `AriUVFit`, `AriUVGridding`, `AriSceneOpener`, `AriMaterialList`,
`AriSelectLoopRing`)를 직접 판독한 결과:

- **규격**: 전부 **32×32, 32bit ARGB(`Format32bppArgb`)**, PNG. (셸프 아이콘 표준 크기)
- **배경**: 어두운 차콜(≈`#2d2d2d`) 단색 + **얇은 외곽 프레임/테두리**가 흔함(패널/창 느낌).
- **모티프**: 채도 높고 단순·도식적인 그래픽, 텍스트 거의 없음.
  - `AriSortOutliner` — 리스트 행 + 녹색 정렬 화살표
  - `AriUVFit` / `AriUVGridding` — 프레임 안 컬러 체커/그리드
  - `AriMaterialList` — 패널 + 색 스와치/버튼들
  - `AriSelectLoopRing` — 가로 컬러 스트라이프
  - `AriSamePositionSelector` — 녹색 큐브들
  - `AriUVAdsorption(Move)` — 화살표/자석식 이동 기호
- **공통 톤**: 다크 배경 위 **고대비·고채도 단색 도형**(시안/그린/오렌지/옐로우/마젠타/블루),
  약한 안티에일리어싱(약간 픽셀 느낌), 작은 크기에서도 식별되는 굵은 형태.

### 우리 아이콘 공통 스타일 가이드
- 캔버스 **32×32**, 다크 라운드 배경(`#2d2d30`) + 얇은 프레임(`#4a4a4f`).
- 중앙에 **툴 도메인을 상징하는 단순 채색 글리프** 하나. **텍스트 미사용**(래스터라이저 폰트
  의존 제거 + 32px 가독성).
- 팔레트(고채도): 시안 `#3fc1c9`, 그린 `#5fd35f`, 오렌지 `#ff9f43`, 레드 `#ee5253`,
  옐로우 `#feca57`, 마젠타 `#ff6bd6`, 블루 `#54a0ff`, 퍼플 `#a55eea`, 틸 `#1dd1a1`.
- 도형 스트로크는 굵게(1.5~3px) — 축소 시 뭉개지지 않도록.

---

## 3. 적용 범위 & 툴별 아이콘 디자인표

전수 분석 결과 **Maya 내부에서 동작하는 툴 = 셸프 아이콘 대상**. 베이스 템플릿
(`A00000_base`, `A00004_base_QT`, `A00008_base_QT_maya`) 제외. **`A00240_PathTool` 은 maya
미의존 standalone 으로 확인되어 제외**. 버전 중복은 현행(_V02) 우선이되 레거시 폴더에도 drag-drop
이 있으면 같은 아이콘 재사용.

| 툴 | 도메인 | 아이콘 모티프 | 주색 |
|----|--------|--------------|------|
| A00010_humanIKTool_V02 | 리깅 | 휴머노이드 스켈레톤 스틱 | 시안 |
| A00020_move_skineWeightTool | 리깅 | 메시 그리드 + 그라데이션 + 이동 화살표 | 오렌지→블루 |
| A00030_quickTool | 유틸 | 번개/렌치 | 옐로우 |
| A00040_file_exporter | 파일 | 박스 + 밖으로 화살표 | 그린 |
| A00050_uvTool | 모델링 | 프레임 안 컬러 체커 그리드(Ari풍) | 멀티 |
| A00060_jointTool(_V02) | 리깅 | 본 체인(연결된 조인트 3개) | 시안/화이트 |
| A00090_ConnectionBuilder | 페이셜 | 노드 + 연결 화살표(RBF) | 마젠타/그린 |
| A00110_animTool | 애님 | 타임라인 트랙 위 키프레임 다이아몬드 | 레드/그린 |
| A00120_FKIK | 애님/리깅 | 팔 체인 + FK/IK 스위치 토글 | 블루/오렌지 |
| A00130_ControlRig | 리깅 | NURBS 원형 컨트롤러 | 옐로우 |
| A00140_ConnectClosest | 리깅 | 두 점 + 최근접 링크선 | 그린 |
| A00145_RigConnect | 리깅 | 체인 링크/커넥터 | 틸 |
| A00150_remapVal | 리깅 | 리맵 램프 곡선 그래프 | 그라데이션 |
| A00160_sphericalEye | 리깅 | 눈 구체 + 홍채 + 축 | 블루 |
| A00170_driverTool | 리깅 | 다이얼/드라이버 + 곡선 | 퍼플 |
| A00180_abSymMesh | 모델링 | 중심축 기준 좌우 미러 메시 | 블루/그린 |
| A00190_FKIK_General_Tool | 리깅 | 제네릭 체인 + 기어 | 스틸 |
| A00200_CSV_tool | 페이셜 | 얼굴 외곽 + 데이터 점 + 그리드 | 핑크/시안 |
| A00211_RefLineage | 파이프라인 | 그래프 노드/브랜치(DAG 레인) | 그린 |
| A00250_SceneMemo | 파이프라인 | 메모지 + 연필 | 옐로우 |

→ **고유 아이콘 20종**. A00060 아이콘은 V01·V02 두 폴더에 공유.

### drag-drop 신규 생성 대상 (현재 설치 파일 없음)
- `A00020_move_skineWeightTool` — Type A, `__init__.py` 가 `run` 노출 → `tools.A00020....run(True)`
- `A00030_quickTool` — Type A, 동일
- `A00090_ConnectionBuilder` — Type B(namespace pkg), `launch.run()` → `tools.A00090....launch.run(True)`

레거시 `A00010_humanIKTool`(V01)은 V02 로 대체되어 drag-drop 신규 생성하지 않음.

---

## 4. 저장 구조 & 도구 체인

### 경로 레이아웃
```
tools/A000XX_name/
└── icon/
    ├── A000XX_name.svg   # 벡터 소스(재생성 근거)
    └── A000XX_name.png   # 래스터 결과 32×32 ARGB (셸프가 참조)
```
SVG 소스와 PNG 결과를 한 폴더에 함께 둬 툴 자기완결(드롭 설치 시 함께 이동) + 재생성 가능.

### 래스터라이저 — mayapy + PySide2 `QSvgRenderer` (추가 설치 0)
환경 점검 결과 `cairosvg / Pillow / pycairo / Inkscape / ImageMagick / rsvg` **전부 부재**,
Python 3.11 만 존재. 반면 **Maya 2024 설치됨** → `mayapy` 의 PySide2 에 `QtSvg` 포함.

- `QSvgRenderer(svg).render(QPainter(QImage(32,32, Format_ARGB32)))` → `QImage.save(png)`.
- **장점**: 신규 의존성 0, **출력이 32×32 ARGB32 = Ari 포맷과 정확히 일치**, 헤드리스 동작.
- mayapy 경로(예): `C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe`.
- **대안(폴백)**: `pip install svglib reportlab`(Windows 휠 존재, cairo 네이티브 DLL 불필요).
  cairosvg 는 Windows 에서 cairo DLL 의존이라 비권장.

### 빌드 스크립트 `JUN_All/dev/build_icons.py`
- `tools/` 순회 → 각 `icon/*.svg` 를 같은 폴더 `*.png`(32×32)로 래스터화.
- 래스터러 자동 검출: mayapy/QtSvg → svglib/reportlab → 둘 다 없으면 안내 후 종료.
- 멱등(재실행 안전). 개발 편의 스크립트라 릴리스 제외 관례 따름.

---

## 5. drag-drop 셸프 와이어링

각 `__dragDrop_A000XX.py` 의 아이콘 지정을 **툴 폴더 내 절대경로**로 바꾼다. `TOOL_ROOT` 가
이미 계산돼 있어 그대로 활용:

```python
# 기존
ICON_NAME = "pythonFamily.png"

# 변경: 로컬 아이콘 절대경로(없으면 기본 아이콘으로 폴백)
_ICON_PATH = os.path.join(TOOL_ROOT, "icon", "A000XX_name.png")
ICON_NAME = _ICON_PATH if os.path.exists(_ICON_PATH) else "pythonFamily.png"
```
- `cmds.shelfButton(..., image1=ICON_NAME, ...)` 호출부는 그대로(이미 `image1=ICON_NAME`).
- **Icon Label**: 같은 호출에 `imageOverlayLabel=TOOL_LABEL` 을 추가해 아이콘 위 라벨을
  Tooltip(`annotation=TOOL_LABEL`)과 동일 값으로 맞춘다(아이콘만으로 구분이 어려울 때 식별 보강).
- **기존 drag-drop 보유 툴**: 위 3줄 교체만.
- **신규 생성 툴**(A00020/A00030/A00090): `A00110_animTool/__dragDrop_A00110.py` 를 템플릿으로
  **고유 번호 파일** 신규 생성 — 파일명 충돌 방지 규칙(`sys.modules.pop(__name__)`, 고유
  베이스네임) 준수, `run` 진입점만 툴에 맞춤.

---

## 6. 작업 순서

1. **확정 점검**(완료): A00240 standalone 확인·제외, 신규 drag-drop 대상/진입점 픽스.
2. **이 계획서 작성**(완료).
3. **시범 SVG 1개**(`A00110_animTool`) → 래스터화 → Ari 셋 옆 톤 확인 → 공통 스타일 픽스.
4. **`dev/build_icons.py`** 작성 및 시범 SVG 로 동작 검증.
5. **툴별 SVG 일괄 제작**(디자인표대로) → `build_icons.py` 로 전체 PNG 생성.
6. **drag-drop 일괄 갱신 + 신규 생성**.
7. **WORKLOG/문서 동기화**, 변경 파일 `py_compile` 통과 확인.

---

## 7. 검증

- **래스터 산출**: `build_icons.py` 실행 후 각 `icon/*.png` 가 **32×32 / ARGB** 인지 확인
  (PowerShell `System.Drawing` 로 폭·높이·PixelFormat 점검 — Ari 점검과 동일 방법).
- **시각 확인**: 생성 PNG 들을 이미지로 열어 Ari 셋과 톤·식별성 육안 비교.
- **drag-drop 정합성**: 변경된 `__dragDrop_*.py` 전부 `py_compile` 통과, `_ICON_PATH` 존재 시
  그 경로/부재 시 `pythonFamily.png` 폴백 로직 점검.
- **Maya 실동작(사용자 측)**: 대표 툴 drag-drop → 셸프에 **고유 아이콘** 버튼 설치 + 클릭 시
  `run()` 정상 동작 확인(셸프 동작은 Maya 실행 환경에서만 최종 검증).
- 미보유 아이콘 툴은 `os.path.exists` 폴백으로 **회귀 없음**(기존처럼 기본 아이콘 표시).
