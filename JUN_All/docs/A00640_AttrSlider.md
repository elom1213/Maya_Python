---
title: A00640_AttrSlider 사용법
aliases: [Attr Slider, AttrSlider, A00640, 어트리뷰트 슬라이더]
tags: [maya-python, tool-guide, animation, attribute, slider, blendshape, fbxasc]
updated: 2026-11-20
---

# A00640_AttrSlider 사용법

마야에서 **고른 노드의 채널박스 어트리뷰트를 슬라이더로** 조절하는 in-Maya PySide 툴(arch B).
blendShape 노드는 **타겟 웨이트**를, FBX 에서 온 일본어 · 중국어 이름(`FBXASC…`)은 **풀어서** 보여 준다.

대표 용도: `A00390_WindTool_V03` > Chain Wave Lite 가 만드는 `*_liteDriver` 로케이터의 `Wind Swing Angle` ·
`Wind Wavelength` · `Wind Envelope` 등을 재생하면서 끌어 맞추기. 채널박스의 가운데 버튼 드래그보다 범위가 보이고 정확하다.

- **버전**: `app/config/version.py` (v01.00)
- **설치**: `__dragDrop_A00640.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **Slider** → `tools.A00640_AttrSlider.run(True)`
  (ToolLauncher `ANIM` 프로파일 `Motion` 칸에도 있다)
- **계획서**: [`plans/A00640_AttrSlider_plan.md`](plans/A00640_AttrSlider_plan.md) (실측 근거 §1)

## 1. 화면

```
[ View  Help ]                                [Pin]
[Lock List] [Refresh]                   [ ] Auto Key
[ Filter attributes / nodes ...                    ]
▼ a0_liteDriver1   (transform)
  Translate X      |=====o--------|  [  0.000 ]
  ...
  Wind Swing Angle |=======o------|  [ 15.000 ]
  Wind Envelope    |=============o|  [  1.000 ]
  Wind Phase Time  (회색 - 연결되어 바꿀 수 없음)
▼ faceBS   (blendShape)
  Envelope         |=============o|  [  1.000 ]
  まばたき          |o-------------|  [  0.000 ]
[ Log ]
```

- 고른 노드마다 **섹션**(풀린 노드 이름 + 타입). 머리를 누르면 접고 편다. 머리 우클릭 = Select Node · Copy Name · Copy Maya Name.
- **행**: float · int = 슬라이더 + 숫자 칸, bool = 체크박스, enum = 콤보(항목 이름도 풀어서).
- **선택을 따라간다.** `Lock List` 를 켜면 지금 목록을 고정한다(버튼이 연한 빨강 `List Locked`).
- `Refresh` = 목록을 다시 만든다(어트리뷰트를 추가 · 삭제했을 때).
- 시간을 옮기거나 undo/redo 하면 **값만** 다시 읽는다.
- Filter: 풀린 이름 · nice 이름 · 마야 이름 어느 쪽으로든 찾는다. 노드 이름이 맞으면 그 섹션 전체가 보인다.

### 무엇이 나열되나

| 고른 것 | 섹션 |
|---------|------|
| 일반 노드 | 채널박스에 보이는 어트리뷰트(키어블 + 비키어블 표시, hidden 제외) |
| 트랜스폼 | + 셰이프 섹션 (`View > Shapes`, 기본 켬 — 채널박스 SHAPES 처럼) |
| 메시 | + 히스토리의 blendShape 섹션 (`View > Blend Shapes of Selection`, 기본 켬 — INPUTS 처럼) |
| blendShape 노드 | `envelope` + 타겟 웨이트(별칭을 풀어서) |

- 다루는 타입: float 계열(각도 · 거리 · 시간 포함) · int 계열 · bool · enum. 문자열 · 행렬 · 멀티 · compound 부모(`translate` 자체)는 빠진다.
- 한 번에 **최대 30 노드**(넘으면 앞에서 자르고 로그에 경고).
- `View > Nice Names / Long Names` — 채널박스와 같은 두 표시. FBXASC 이름은 둘 다 **풀린 글자**로 보인다(마야 niceName 은 FBXASC 그대로라 직접 푼다).
  행 이름에 마우스를 올리면 마야 이름 · plug · 범위 · 상태가 나온다.

## 2. 슬라이더 범위

| 순서 | 범위 | 예 |
|------|------|----|
| 1 | **사용자 범위** — 행 우클릭 `Set Range...` | 어디서나 `windSwingAngle` = 0~90 |
| 2 | 양쪽 **소프트** 범위 | blendShape weight 0~1 (하드 -10~10 보다 먼저) |
| 3 | 양쪽 **하드** 범위 | `windEnvelope` 0~1, `windTipFollow` 0~0.99 |
| 4 | 하드 최소만 | `windWavelength`(최소 0.001) = 최소 ~ max(최소+10, 값×2) |
| 5 | 범위 없음 | 회전 = -180~180, 그 밖 = 값 ± max(10, \|값\|) — `windSwingAngle` 15 → 0~30 |

- 사용자 범위는 **어트리뷰트 이름 기준**으로 저장된다(optionVar). liteDriver 를 새로 만들어도, 다른 노드여도 같은 범위가 쓰인다.
  `Reset Range` 로 지운다.
- 범위는 행을 만들 때 정한다. 숫자 칸에 범위 밖 값을 넣으면 **그 행만** 넓어진다(저장 안 함).
- 숫자 칸은 하드 범위까지만 받는다. 하드 범위 밖 값은 마야가 거부하므로 넣기 전에 자른다.

## 3. 값 쓰기 · 키

- **슬라이더 드래그 한 번 = Ctrl+Z 한 번.** 숫자 칸은 Enter · 포커스 아웃에서 확정.
- 행 이름 색은 마야 채널박스와 같다:

| 색 | 상태 | 바꿀 수 있나 |
|----|------|--------------|
| 기본 | 그냥 값 | 예 |
| **분홍** | Keyed — 시간 커브 키 또는 애님 레이어 | 예. 하지만 **시간을 옮기면 커브 값으로 돌아간다** |
| **노랑** | Driven — 연결 · 드리븐 키 · 표현식 | 아니오(회색). 드리븐 키는 넣어도 곧 드라이버가 덮어쓴다 |
| 회색 파랑 | Locked | 아니오 |

- `Auto Key` 를 켜면 바꾼 어트리뷰트에 **키를 찍는다**(드래그는 놓을 때 한 번). 키가 있는 어트리뷰트를 고정하려면 켜 두거나 행 우클릭 `Set Key`.
- liteDriver 의 `windPhaseTime` 은 시계 노드가 연결되어 있어 노랑 · 회색이 정상이다.

## 4. 구조

```
tools/A00640_AttrSlider/
├── __init__.py · launch.py · __dragDrop_A00640.py
├── app/config/version.py
├── app/core/ranges.py       # 범위 규칙 + 사용자 범위 저장(마야 비의존)
├── app/core/attr_rows.py    # 선택 → 섹션 · 행, 상태 판정, 값 읽기 · 쓰기
├── app/ui/main_window.py    # 섹션 · 행 위젯, scriptJob(SelectionChanged · timeChanged · Undo · Redo · SceneOpened)
├── icon/A00640_AttrSlider.svg · .png
└── tests/test_attr_slider.py
```

- 공용: `Framework/core/fbx_name`(디코드) · `maya_fbx_names.blendshape_targets` · `maya_undo` · `MOD_sliderStyle_qt_v01` ·
  `MOD_log_qt_v01` · `MOD_menuBar_qt_v01` · `pin_style`.
- 채널박스 판정 · 종류 표 · enum 파싱은 A00145 와 같은 규칙을 따로 둔다(툴 간 import 금지). Framework 로 합치는 것은 계획서 §6.

## 5. 시험

`"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" tools/A00640_AttrSlider/tests/test_attr_slider.py` — **75항목**(mayapy 오프스크린).
범위 규칙 17 · 나열 8 · 디코드 4 · blendShape 7 · 상태 6 · 쓰기 5 · UI 28.
liteDriver 와 같은 모양의 로케이터(A00390 V03 `_make_lite_driver` 의 어트리뷰트 · 범위 그대로)로 시험한다.
**마야 GUI 확인 아직.**

## 6. 알려진 제약

- 여러 노드를 골라도 노드마다 따로 보인다 — 같은 어트리뷰트를 한 슬라이더로 묶는 `Common` 모드는 다음 단계.
- 재생 중에도 매 프레임 값을 다시 읽는다(행이 많으면 무거울 수 있다 — 최대 30 노드).
- 행 이름 칸 폭은 고정(150px)이라 긴 이름은 잘린다 — 전체 이름은 툴팁.
