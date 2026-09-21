---
title: A00400_CurveTool 사용법
aliases: [Curve Tool, CurveTool, A00400]
tags: [maya-python, tool-guide, curve, mesh-edge, polyToCurve, lineWidth, wrap, blendShape, editPoint, laplacian, smoothCurve, softSelect, joint, skinCluster, controller, shape-transform]
updated: 2026-09-21
---

# A00400_CurveTool 사용법

Maya 안에서 도는 **커브** PySide 툴이다(arch B, in-Maya).
**v01.06 부터 탭이 두 단계**다 — **상위 탭 = 카테고리, 하위 탭 = 기능**
(`A00110_animTool_V02` 과 같은 규칙).

| 상위 탭 | 하위 탭 | 내용 |
|---------|---------|------|
| **Create**<br>씬에 **새 커브를 만든다** | **From Edges** | ① 선택한 메시 엣지에 부착된 커브 생성(엣지 덩어리마다 커브 하나) ② Reverse Direction(방향 통일) |
| | **Controls** (v01.15~) | 컨트롤러 커브 **34종**을 만들고(Parent / Child / World / Origin) **색**을 입힌다(인덱스 32색 + **팔레트 팝업의 임의 색**, v01.17~). `bs_controls` 이식 |
| | **From Points** (v01.04~) | 리스트에 담은 오브젝트·조인트·컴포넌트의 **월드 위치**를 **순서대로** 잇는 커브 하나. 정확히 통과 / 완화 선택 |
| **Edit**<br>기존 커브의 **형상(CV)** 을 바꾼다 | **Smooth** (v01.05~) | 씬에서 고른 **CV** 를 슬라이더로 실시간 Smooth / Rough. **소프트 셀렉션 폴오프**를 그대로 쓴다. **닫힌 커브도 이음매를 넘어** 고른다 (v01.08~) |
| | **Wrap** (v01.03~) | **CV 개수가 달라도** 한 커브가 다른 커브의 모양을 따르게 한다. 0~1 envelope 어트리뷰트로 라이브 블렌드 |
| | **Joints** (v01.07~) | 커브 위에 조인트를 **균일 배치** → 그 조인트로 **커브를 바인드** → 조인트마다 `zro/con/ctl/tgt` 컨트롤러. 컨트롤러가 조인트를, 조인트가 커브를 움직인다. **v01.14~ NURBS 서피스도** — U 또는 V 방향 한 줄로 |
| | **Combine** (v01.11~) | 좌측 **Source** 커브의 쉐입을 우측 **Target** 커브에 합친다. 인스턴스가 아닌 **복사본**이라 Source 를 지우거나 고쳐도 영향 없음 |
| **Display**<br>**어떻게 보이는지**를 바꾼다 | **Line Width** (v01.01~) | 리스트업한 커브의 **뷰포트 표시 굵기**를 슬라이더로 조절 — 씬에서 **잘 보이고 잘 집히게**. 형상은 불변 |
| | **Replace** (v01.16~) | 컨트롤의 **셰이프를 다른 커브 모양으로 교체**한다(이름·트랜스폼·연결은 그대로). 대상과 교체본을 **TSL 두 칸**에 담아 순서대로 짝짓는다 |
| | **Transform** (v01.18~) | 리스트업한 커브의 **셰이프 자체**를 **각 커브의 피벗 기준**으로 **스케일 · 이동 · 회전**한다. CV 를 전부 골라 툴을 쓴 것과 같은 결과이고 **트랜스폼 채널은 건드리지 않는다**. X/Y/Z 축마다 켜고 끈다. 기본은 **Scale 만** |

### 분류 기준 (v01.06)

기준은 **"씬에 무엇을 하는가"** 하나다.

- **Line Width 는 Edit 이 아니라 Display** — `nurbsCurve.lineWidth` 는 **뷰포트 표시 굵기**일 뿐
  커브 데이터를 건드리지 않는다. 커브를 바꾸는 기능과 보이는 방식만 바꾸는 기능이 한 상자에 섞이면 분류가 흐려진다.
- **Reverse Direction 은 성격상 Edit 이지만 `Create > From Edges` 에 남겼다** —
  생성 버튼과 **같은 커브 리스트(`self.tsl`)** 를 공유하기 때문이다. 떼어내면 커브를 두 번 리스트업해야 한다.
- **`Display > Replace` 는 셰이프 노드를 갈아 끼우므로 성격은 Edit 에 가깝다** — 그런데도 Display 에 둔 것은
  쓰는 사람이 "이 컨트롤을 **어떤 모양으로 보이게 할까**" 로 찾기 때문이다(v01.16, 사용자 지정).
  그래서 Display 의 설명도 "형상 불변" 이 아니라 **"어떻게 보이는지"** 로 바꿨다.
- **`Display > Transform` 도 CV 를 옮기니 성격은 Edit** — 그런데도 Display 에 둔 것은 같은 이유다(v01.18,
  사용자 지정). 쓰는 사람은 "이 컨트롤을 **얼마나 크게 · 어느 방향으로 보이게 할까**" 로 찾고,
  바로 옆 `Replace` 와 한 묶음으로 쓴다(모양을 갈아 끼우고 → 크기를 맞춘다).
- ~~하위 페이지가 하나뿐인 Display 도 하위 탭 바를 그대로 둔다~~ — v01.16 에 `Replace`, v01.18 에 `Transform` 이 붙었다.
  탭 하나짜리였을 때도 탭 바를 둔 이유(기능 이름이 화면에 남고, 늘어나도 구조가 그대로)가 그대로 맞았다.

- **Joints 는 조인트·컨트롤러를 새로 만들지만 Create 가 아니라 Edit** — Create 의 기준은
  "새 **커브**를 만든다" 이고, Joints 는 **이미 있는 커브**를 대상으로 그 커브의 CV 를 무엇이
  움직일지 바꾼다(바인드). 만들어지는 조인트·컨트롤러는 그 목적을 위한 수단이라, 분류는
  커브 기준으로 유지했다.

> 분류표는 코드에서 `MainWindow.CATEGORIES` 한 곳이 정한다. 탭을 추가·이동하려면 그 표만 고치면 된다.

- **버전**: `app/config/version.py` (v01.07)
- **설치**: `__dragDrop_A00400.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **CurveTool** → `tools.A00400_CurveTool.run(True)`
- **참고**: 엣지→커브 생성은 `ref/ref_01.mel`(`duplicateCurve`+`attachCurve`)의 아이디어를, 축 비교 방식은 `A00360_SortTool` 을 이식/응용.

---

## 1. 화면 구성

```
┌ Curve Tool ─────────────────────────┐
│ Help                                │
│ [ Create ][ Edit ][ Display ]       │  ← 상위 탭 (카테고리)
│ [ From Edges ][ From Points ]       │  ← 하위 탭 (기능)
│ ┌ Create Curves from Mesh Edges ──┐ │
│ │ Name Prefix [ edgeCurve       ] │ │
│ │ [ ] Smooth curve (degree 3)     │ │
│ │ [ Create Curves from Sel Edges ]│ │
│ └─────────────────────────────────┘ │
│ [ List Selected Curves ]            │  ← 씬에서 커브 골라 담기(선택)
│ Curves               Number: N      │
│ ┌─────────────────────────────────┐ │
│ │ edgeCurve_01                    │ │   TSL: Add / Del / Up / Down
│ │ edgeCurve_02                    │ │
│ │ edgeCurve_03                    │ │
│ └─────────────────────────────────┘ │
│ [Add][Del][Up][Down]                │
│ ┌ Reverse Direction ──────────────┐ │
│ │ Compare Axis ( )X (o)Y ( )Z     │ │
│ │ cv[0] at (o)Max end ( )Min end  │ │
│ │ [       Reverse Direction      ]│ │
│ └─────────────────────────────────┘ │
│ [ log ... ]                         │
└─────────────────────────────────────┘
```

---

## 2. 사용법

### 2-1. 엣지 → 커브 생성

1. Maya에서 메시의 **엣지**를 선택한다. 여러 개의 **떨어진 엣지 구간**을 함께 골라도 된다
   (예: `pSphere1.e[156:158]`, `pSphere1.e[196:199]`, `pSphere1.e[236:239]`).
2. 옵션:
   - **Name Prefix** — 생성 커브 이름 접두사(`<prefix>_01`, `<prefix>_02` …). 기본 `edgeCurve`.
   - **Smooth curve (degree 3)** — 끄면 엣지를 그대로 따르는 **직선(degree 1)**, 켜면 **부드러운 곡선(degree 3)**.
3. **Create Curves from Selected Edges** — 붙어 있는 엣지 덩어리마다 커브 1개씩 생성해 **Curves** 리스트에 담는다.
   위 예시는 **커브 3개**가 나온다. 생성 커브는 `constructionHistory` 로 **메시에 부착**(엣지가 움직이면 따라감)된다.
   전체가 **한 번의 undo** 로 묶인다.

> ref_01.mel 은 선택 전체를 커브 **1개**로만 묶어(떨어진 세 구간을 골라도 커브 1개), 여러 커브를 만들지 못했다.
> 이 툴은 그 한계를 풀어 **엣지 그룹마다 커브 1개**를 만든다.

### 2-2. Reverse Direction (방향 통일)

1. 방향을 맞출 커브들을 **Curves** 리스트에 둔다(생성 직후 자동으로 담겨 있거나, 씬에서 커브를 골라 **List Selected Curves**/Add).
2. **Compare Axis** — 비교할 월드 축(**X / Y / Z**, 기본 **Y**).
3. **cv[0] at** — `cv[0]` 이 와야 할 끝:
   - **Max end** (기본) — 축의 **큰 쪽**(예: Y 위쪽). "위 → 아래" 로 cv 를 정렬하고 싶을 때.
   - **Min end** — 축의 **작은 쪽**(예: Y 아래쪽).
4. **Reverse Direction** — 각 커브의 `cv[0]`/`cv[n]` 축값을 비교해, `cv[0]` 이 지정한 끝에 오도록 방향이 반대면
   `reverseCurve` 로 뒤집는다. 이미 맞는 커브는 그대로 둔다. 전체가 **한 번의 undo**.

> 예) 씬 위에서 아래로 cv 가 정렬되길 원하면 **Axis=Y, cv[0] at Max**. `cv[0]` 이 위에 있으면 방치, 아래에 있으면 뒤집는다.

---

## 3. 동작 원리 / 주의

- **엣지 그룹핑(연결 성분)**: 두 엣지가 정점을 공유하면 같은 그룹(BFS). 서로 다른 메시의 엣지는 정점을 공유할 수
  없어 자연히 다른 그룹으로 갈린다. 그룹마다 그 엣지들을 선택해 `polyToCurve(form=2, degree, ch=1)` 로 커브 1개를 만든다.
- **왜 polyToCurve 인가**: ref 의 `duplicateCurve`+`attachCurve`(각 엣지를 작은 커브로 뜬 뒤 이어붙임)와 결과는
  같은 "엣지를 따라가는 부착 커브"지만, `polyToCurve` 가 **엣지 체인의 cv 순서를 스스로 정렬**해 줘 더 견고하고
  **`cv[0]`/`cv[n]` 끝점이 명확**하다(방향 정렬에 필요). `form=2` 로 열림/닫힘을 자동 판단한다(엣지 루프면 닫힘).
- **방향 비교**: `cv[0]`/`cv[n]` 의 월드 위치(`pointPosition -w`) 축 성분을 비교한다. 두 끝의 축값이 **같으면**
  (예: 위도 링처럼 수평 커브를 Y 로 비교) 판단 불가라 **건너뛰고** 로그에 표시한다. 커브가 아니거나 cv 가 2개 미만인
  항목도 건너뛴다.
- **UUID 안전**: Reverse 대상은 TSL 의 `get_all_nodes()`(UUID 기반)로 현재 경로를 되찾아, 리네임/리페어런트 후에도 정확히 그 커브를 잡는다.

---

## 4. 구조

```
tools/A00400_CurveTool/
├── launch.py / __init__.py / __dragDrop_A00400.py
├── icon/A00400_CurveTool.svg (+ .png)   # 셸프 아이콘(커브 + CV 포인트 + 방향 화살표)
├── ref/ref_01.mel                       # 참고: 단일 커브 attach 방식 MEL
└── app/
    ├── config/version.py
    ├── core/curve_manager.py        # 엣지 그룹핑 + polyToCurve + reverseCurve (maya.cmds, UI 비의존)
    ├── core/points_manager.py       # 월드 위치 목록 -> 커브
    ├── core/smooth_manager.py       # CV 라플라시안 스무딩
    ├── core/wrap_manager.py         # rebuildCurve + blendShape 래핑
    ├── core/joint_curve_manager.py  # 커브 위 균일 조인트 + skinCluster 바인드 + 컨트롤러 스택
    ├── core/combine_manager.py      # Source 쉐입을 Target 에 복사해 합치기
    ├── core/control_manager.py      # 컨트롤러 커브 34종 생성 · 색 · 셰이프 교체
    ├── core/shape_xform_manager.py  # 셰이프(CV) 를 피벗 기준으로 scale / rotate / move
    ├── ui/controls_tab.py           # Create > Controls 화면
    ├── ui/replace_tab.py            # Display > Replace 화면
    ├── ui/shape_xform_tab.py        # Display > Transform 화면
    └── ui/main_window.py            # PySide UI (카테고리 상위 탭 + 기능 하위 탭 + 로그)
```

**탭 구조 (v01.06~)** — `MainWindow` 안의 표가 분류를 정한다.

```python
CREATE_PAGES  = (("From Edges", tip, "_build_create_tab"),
                 ("From Points", tip, "_build_points_tab"))
EDIT_PAGES    = (("Smooth", tip, "_build_smooth_tab"),
                 ("Wrap",   tip, "_build_wrap_tab"),
                 ("Joints", tip, "_build_joints_tab"))
DISPLAY_PAGES = (("Line Width", tip, "_build_width_tab"),
                 ("Replace",    tip, "_build_replace_tab"),
                 ("Transform",  tip, "_build_shape_xform_tab"))

CATEGORIES = (("Create",  tip, CREATE_PAGES,  "create_tabs"),
              ("Edit",    tip, EDIT_PAGES,    "edit_tabs"),
              ("Display", tip, DISPLAY_PAGES, "display_tabs"))
```

- `_build_category_tab(pages, attr)` — 카테고리 상위 탭 하나를 만들고 하위 탭 위젯을
  `self.<attr>` (예: `self.edit_tabs`) 로 붙인다.
- `_build_sub_tabs(pages)` — `(라벨, 툴팁, 빌더 메서드 이름)` 목록을 하위 탭 위젯으로 만든다.
  라벨이 길면 `ElideRight` 로 자른다(스크롤 화살표만 뜨는 것보다 읽기 쉽다).
- **기능 빌더(`_build_*_tab`)는 손대지 않았다.** 탭 재배치는 위 표만 바꾸면 된다.

- 핵심 API:
  - `curve_manager.curves_from_selected_edges(prefix, degree)` → `(created_curves, group_count)`
  - `curve_manager.reverse_curves_by_axis(curves, mode, cv0_at_max)` → `(reversed_names, skipped)`
    - `mode` = `MODE_X/Y/Z`, `cv0_at_max=True` 면 `cv[0]` 을 축 최대 끝에.
  - `curve_manager.group_edges(edges)` → 연결 성분별 엣지 그룹 리스트.

---

## Display > Line Width (v01.01~) — 커브를 잘 보이고 잘 집히게

씬에 커브가 많아지면 얇은 선은 **눈에 잘 안 띄고 클릭으로 집기도 어렵다.** 이 탭은 리스트업한
커브의 `nurbsCurve.lineWidth`(뷰포트에 그려지는 선 굵기)를 한 번에 바꾼다.

> **표시 전용이다.** 커브의 형상·CV·히스토리는 전혀 건드리지 않는다. 렌더에도 영향이 없다.

### 사용법

1. 씬에서 커브를 고르고 **List Selected Curves** 로 리스트에 담는다(이 탭 전용 리스트).
2. **슬라이더를 드래그**하면 리스트의 모든 커브에 **실시간**으로 반영되고,
   **손을 떼는 순간 그 값으로 확정**된다(v01.02~ — 따로 누를 버튼이 없다).
   오른쪽 스핀박스로 정확한 값(0.1 단위)을 넣어도 된다(Enter/포커스 아웃이 곧 확정).
   둘은 항상 같이 움직인다.
3. 필요하면 **Get**(첫 커브의 값 읽어오기) / **Use Maya Default (-1)**.

| 버튼·값 | 뜻 |
|---------|-----|
| 슬라이더 · 스핀박스 | 0.0 ~ 10.0. 숫자가 클수록 굵게 그려진다. **놓는 즉시 적용**(Apply 버튼 없음) |
| **Use Maya Default (-1)** | `lineWidth = -1` — **마야 전역 라인 굵기 설정을 따른다**(커브의 원래 기본값) |
| **Get** | 리스트 첫 커브의 현재 값을 슬라이더로 가져온다. `-1` 이면 로그로 알려 주고 슬라이더는 최솟값에 둔다 |

### 알아둘 것

- **드래그 한 번이 undo 한 스텝**이다(누를 때 청크를 열고, **확정 적용까지 마친 뒤** 닫는다).
  드래그 중 수십 번 값이 바뀌어도 `Ctrl+Z` 한 번이면 원래대로 돌아온다.
  > 확정을 청크 **밖**에서 하면 드래그 하나가 undo 두 스텝으로 갈라진다(v01.02 에서 고침).
- 커브가 아닌 항목, `lineWidth` 어트리뷰트가 없는 **구버전(Maya 2019 미만)**, 잠기거나 연결된
  어트리뷰트는 **사유와 함께 건너뛰고** 나머지는 계속 처리한다.
- 리스트는 UUID 로 현재 경로를 되찾으므로 **리네임·리페어런트 후에도** 같은 커브를 잡는다.
- 커브 하나에 셰이프가 여럿이면 **모든 nurbsCurve 셰이프**에 적용한다.

---

## Edit > Wrap (v01.03~)

**CV 개수가 다른 두 커브**에서, 한쪽(driven)이 다른 쪽(driver)의 모양을 그대로 따르게 한다.

마야 기본 `wrap` 디포머로도 커브끼리 묶을 수는 있지만 변형이 불안정해 실무에 쓰기 어렵다.
이 탭은 디포머를 쓰지 않고, **마야가 이미 정확히 계산해 주는 것**을 노드로 엮는다.

```
driverShape.local ─▶ rebuildCurve ─▶ transformGeometry ─▶ wrapTarget 커브
                     (driven 의 span/degree 로)  (driver world × driven worldInverse)
                                                        │
                         wrapTarget ─▶ blendShape(driven) 타깃,  weight = envelope
```

핵심은 **`rebuildCurve`** 다. "같은 모양을 다른 CV 개수로 다시 표현"하는 노드이므로,
driven 의 span/degree 로 driver 를 재구성하면 **CV 개수가 driven 과 정확히 같아진다.**
그러면 blendShape 의 타깃으로 그대로 쓸 수 있고, 노드로 남으니 **라이브**다.

### 사용법

1. driver 커브를 고르고 **Driver** 옆 `<<`
2. driven 커브를 고르고 **Driven** 옆 `<<`
3. (선택) **Check** — 두 커브의 CV/span/degree/form 을 보고 걸 수 있는지 알려 준다. 씬은 안 건드린다.
4. **Create Wrap**

driven 커브에 **`wrapEnvelope`** 어트리뷰트(0~1, 키 가능)가 붙는다.
**0 = 원래 모양 / 1 = wrap 된 모양**, blendShape 의 envelope 과 같은 감각이다.
탭 아래 슬라이더로 바로 돌려볼 수 있고(드래그 한 번 = undo 한 스텝), 채널박스에서 키를 걸거나
다른 어트리뷰트에 연결해도 된다. 이름은 **Envelope attr** 필드로 바꿀 수 있다.

**Remove Wrap** 을 누르면 셋업(blendShape · rebuildCurve · transformGeometry · multMatrix ·
타깃 그룹 · envelope 어트리뷰트)이 전부 지워지고 driven 은 원래 모양으로 돌아온다.

### 옵션

| 옵션 | 뜻 |
|------|-----|
| **Preserve offset** | 끄면(기본) envelope 1 에서 driven 이 **driver 의 모양 그대로** 된다. 켜면 driven 이 **자기 모양을 유지한 채** driver 의 **변화량만** 따라간다(타깃 2개 — 라이브 `+env`, 바인드 스냅샷 `-env`) |
| **Uniform-rebuild the driven curve** | driven 의 노트가 불균등할 때만 의미가 있다. 켜면 균등하게 먼저 재구성한다 — driven 자체 모양이 조금 바뀌는 대신 정확도가 크게 오른다(실측 0.264 → 0.088) |
| **Envelope attr** | driven 에 붙는 0~1 어트리뷰트 이름 (기본 `wrapEnvelope`). 같은 이름이 이미 있으면 뒤에 번호를 붙인다 |

### 정확도

Create 직후 **얼마나 잘 맞았는지 로그에 찍는다** — 최대 편차, driver 길이 대비 %, 평균 편차.
(두 커브를 호 길이 등간격으로 60점 샘플해 월드 좌표로 잰다.)

| 상황 | 실측 최대 편차 |
|------|----------------|
| driven 12 CV ← driver 4 CV (둘 다 균등) | **0.0013** — 사실상 정확히 일치 |
| driven 이 driver 보다 CV 가 적을 때 | CV 개수만큼만 근사된다. 경고와 함께 편차를 보고한다 |
| driven 의 노트가 불균등 | 0.264 (→ Uniform-rebuild 켜면 0.088) |

### 알아둘 것 (mayapy 로 확인)

- **노트 벡터의 범위(0~1 vs 0~9)가 달라도 결과는 같다.** 균등 간격이기만 하면 무관하다.
  반대로 **간격이 불균등하면** driver 를 아무리 잘 재구성해도 driven 의 노트로 다시 해석될 때
  모양이 어긋난다 → 그래서 Check/Create 가 경고하고 Uniform-rebuild 옵션을 둔다.
- **form(open / periodic)이 다르면 결과가 망가진다**(실측 편차 10.77). CV 개수가 우연히 같으면
  blendShape 이 **에러도 없이** 만들어지므로, 이 툴은 form 이 다르면 **아예 거절한다.**
- **`rebuildCurve` 노드는 소스의 CV 변화만 따라가고 트랜스폼 이동은 무시한다**
  (기본적으로 `worldSpace` 에 연결돼 있는데도 그렇다). 그래서 지오메트리는 driver 의 `local` 을
  먹이고, 공간 변환은 `driver.worldMatrix × driven.worldInverseMatrix` 를 `multMatrix` →
  `transformGeometry` 로 따로 건다. **행렬은 평범한 어트리뷰트라 전파가 확실하다.**
  덕분에 두 커브의 트랜스폼이 각각 움직여도(회전 포함) 어긋나지 않는다.
- blendShape weight 는 **음수를 받는다** — Preserve offset 이 타깃 2개로 되는 이유다.
- 생성 전체가 **undo 한 스텝**이다. envelope 슬라이더 드래그도 한 스텝.
- 중간 타깃 커브는 `<driven>_wrapGrp` 그룹에 담아 숨긴다. 셋업을 지우면 함께 사라진다.

---

## Create > From Points (v01.04~)

리스트에 담은 것들의 **월드 위치**를 **리스트 순서대로** 잇는 **커브 하나**를 만든다.
오브젝트든 조인트든 컴포넌트든 위치 하나로 환원해서 다룬다.

### 사용법

1. 씬에서 원하는 것들을 고르고 **List Selected**
   순서가 곧 결과이므로 이 탭의 리스트는 **Order 체크박스가 기본 ON** 이다 — 고른 순서대로 담긴다.
   담은 뒤에도 `Up` / `Down` / `Reverse` 로 순서를 바꿀 수 있다.
2. **Degree** 를 고른다 (1 이면 점들을 직선으로 잇는 폴리라인, 3 이 보통의 부드러운 커브)
3. 모드를 고른다
4. **Create Curve from List**

### 두 가지 모드

| 모드 | 결과 |
|------|------|
| **Through the points (exact)** | 모든 위치를 **정확히 지난다**. `cmds.curve(ep=...)` 의 **에디트 포인트** 커브 — 실측 최대 거리 `0.0` |
| **Smoothed (relaxed)** | 위치를 꼭 지나지는 않지만 완만하다. 위 커브의 **CV 를 라플라시안으로 이완**한다. **첫/마지막 위치는 항상 유지**된다 |

**Smoothness** 0 은 exact 와 같고, 1 이 가장 완만하다. 입력점에서 멀어지는 정도가
슬라이더 값에 **비례**한다(실측 `0 → 0.77 → 1.60 → 2.43 → 3.27`).

> 처음에는 완화를 `rebuildCurve` 의 span 수로 하려다 접었다. span 을 5→4→3 으로 줄일 때
> 입력점까지의 최대 거리가 `0.30 → 1.73 → 1.44` 로 **단조롭게 늘지 않아** 슬라이더로 쓰기 나쁘다.
> 또 라플라시안도 세기를 슬라이더에 그대로 비례시키면 반복 효과가 지수적으로 쌓여
> **앞쪽 25% 에서 변화가 거의 끝나 버린다**(`0 → 2.57 → 2.68 → 3.03 → 3.27`).
> 그래서 **"완전히 이완한 결과"를 한 번 구한 뒤 원본과 선형 보간**한다.

### 무엇을 "위치"로 보는가

`cmds.xform(q=True, ws=True, translation=True)` 하나로 전부 처리한다(mayapy 로 확인).

| 대상 | 위치 |
|------|------|
| 트랜스폼 · 조인트 | 월드 트랜슬레이트 (부모 그룹이 움직였어도 실제 월드 위치) |
| 버텍스 · NURBS CV · 래티스 포인트 | 그 점의 월드 위치 |
| **엣지 · 페이스** | 구성 정점들이 여러 개 나오므로 **평균(중심)** 을 쓴다 |

> `cmds.pointPosition` 은 엣지/페이스에서 에러가 나므로 쓰지 않는다.

### 알아둘 것

- 위치를 못 얻는 항목(지워졌거나 위치 개념이 없는 노드)은 **사유와 함께 건너뛰고** 나머지로 만든다.
- 위치가 **2개 미만**이면 만들지 않고 이유를 로그에 남긴다.
- 점 개수가 차수보다 적으면 **차수를 자동으로 낮추고** 그 사실을 로그에 적는다.
- 생성 직후 **입력 위치에서 커브까지의 최대/평균 거리**를 로그로 보고한다 —
  exact 면 0, 완화하면 얼마나 벗어났는지 바로 보인다.
- 만든 커브는 씬에서 선택된 상태가 되고, **생성 + 선택이 undo 한 스텝**이다.
  > 선택을 청크 밖에서 하면 `Ctrl+Z` 한 번이 커브가 아니라 선택만 되돌린다(개발 중 실제로 겪음).
- 리스트는 UUID 로 현재 경로를 되찾으므로 **리네임·리페어런트 후에도** 같은 대상을 잡는다.

---

## Edit > Smooth (v01.05~)

씬에서 고른 **커브 CV** 를 슬라이더로 실시간 **Smooth / Rough** 한다.
마야 기본 `Curves > Smooth`(`cmds.smoothCurve`)의 **결과를 그대로 쓰되**, 그 명령이 못 하는
네 가지를 얹은 것이다.

| | 마야 기본 `Curves > Smooth` | 이 탭 |
|---|---|---|
| Rough(반대 방향) | ❌ **음수 smoothness 를 조용히 무시한다** | ✅ 슬라이더 왼쪽 |
| 소프트 셀렉션 | ❌ 고른 CV 를 전부 똑같이 민다 | ✅ **폴오프 가중치대로** |
| 실시간 조절 | ❌ 한 번 실행 | ✅ 드래그하는 동안 계속 |
| **닫힌(주기) 커브** | ❌ `Cannot smooth CVs on periodic curves` | ✅ **이음매를 넘어서** (v01.08~) |

### 사용법

1. 커브를 컴포넌트 모드로 놓고 **CV 를 고른다**. 소프트 셀렉션을 켜 두면 그 폴오프가 그대로 쓰인다.
2. (선택) **Check Selection** — 몇 개가 잡혔는지, 소프트 셀렉션이 켜져 있는지 보고만 한다.
3. **슬라이더를 드래그**한다. 오른쪽이 Smooth, 왼쪽이 Rough. 드래그하는 내내 뷰포트에 반영되고,
   **손을 떼는 순간 확정**된다(별도의 Apply 버튼 없음). 확정 후 슬라이더는 **가운데(0)로 돌아온다** —
   같은 자리에서 한 번 더 밀면 한 번 더 적용된다.

### 닫힌 커브 (v01.08~)

원 · 엣지 루프에서 뜬 커브처럼 **닫힌(주기) 커브**도 열린 커브와 똑같이 다룬다.
따로 켜고 끌 것은 없고, 고르기만 하면 된다.

- **고정되는 CV 가 없다.** 열린 커브는 양 끝이 못 움직이지만 닫힌 커브는 끝이 없으므로
  `cv[0]` 과 마지막 CV 만 골라도 **서로를 이웃으로 보고** 고르게 밀린다.
- **Check Selection** 이 커브마다 `open` / `closed` 를 함께 적는다.
- 열린 커브와 닫힌 커브를 **한꺼번에 골라도** 된다. 각각 제 방식으로 처리된다.
- degree 1(직선) 커브는 열린 쪽 닫힌 쪽 여전히 제외된다 — 마야의 Smooth 자체가 안 된다.

구현은 **마야의 알고리즘을 그대로 다시 쓴다.** 라플라시안 같은 대체 스무딩을 따로 지으면
열린 커브와 닫힌 커브의 감촉이 갈라지기 때문이다.

```
1) 닫힌 커브의 CV                 [ 0 1 2 3 4 5 6 7 ]

2) 앞뒤로 감아 복사한 열린 임시   [ 5 6 7 : 0 1 2 3 4 5 6 7 : 0 1 2 ]
                                    ^^^^^                     ^^^^^
                                    패딩 - 마야가 고정하는 끝은 전부 여기 들어간다

3) 임시 커브에 마야 smoothCurve

4) 가운데 구간만 읽어 온다        [ 0 1 2 3 4 5 6 7 ]
```

- 패딩 폭은 `2 * degree + 4`. degree 7 까지 이 값이면 패딩을 40 으로 키운 결과와 같다(실측).
- 결과는 마야의 내부 스텐실(degree 3 기준 `[-1/18, 2/9, 2/3, 2/9, -1/18]`)을 **순환으로** 건 것과
  소수점까지 같다(실측 오차 `8.9e-16`).

### Multiplier

**적용값 = 슬라이더 값 × Multiplier** 이고, 이 값이 그대로 `smoothCurve` 의 `smoothness` 로 들어간다.

- Multiplier `1` → 슬라이더 값이 그대로 적용된다(슬라이더 오른쪽 끝 = `smoothness 1`).
- Multiplier `> 1` → 같은 슬라이더 이동으로 훨씬 강한 smooth 에 닿는다(끝 = `smoothness 5` 등).

옆 라벨에 지금 적용될 값이 `+1.50 (smooth)` 처럼 실시간으로 표시된다.

### 계산

```
target[i] = 마야 smoothCurve(smoothness = |적용값|) 를 적용한 위치
result[i] = origin[i] + sign(적용값) * weight[i] * (target[i] - origin[i])
```

- 적용값 `1`, 가중치 `1` 이면 **마야 기본 Smooth 와 정확히 같은 결과**가 된다(검증 항목으로 고정).
- 값을 키울 때 스무딩 결과를 **넘겨 외삽하지 않고** `smoothCurve` 에 더 큰 `smoothness` 를 넘긴다
  (마야가 하는 것과 같은 방식) → 값이 커져도 형태가 튀지 않는다.
- 음수면 **스무딩 결과에서 멀어지는 방향** = Rough.
- `weight[i]` 가 소프트 셀렉션 폴오프다. 소프트가 꺼져 있으면 고른 CV 가 전부 `1.0` 이라
  **같은 코드 경로로 처리된다**.

마야의 결과는 임시 사본에서 뽑는다 — 드래그 시작 때 커브를 하나 복제해 두고, 틱마다 원본
스냅샷을 그 사본에 써 넣은 뒤 `smoothCurve` 를 돌려 결과만 읽어 온다. 사본은 숨겨져 있고
드래그가 끝나면 지워진다.

### 알아둘 것 (mayapy 로 확인)

- **`smoothCurve` 는 음수 smoothness 를 무시한다**(`s=-1` 이면 값이 그대로다). Rough 가 직접 구현인 이유.
- **degree 1(직선) 커브에서는 `smoothCurve` 자체가 실패한다.**
  그런 커브는 **미리 걸러** 이유를 로그에 적고 나머지 커브만 처리한다.
- **주기(periodic) 커브에서도 실패한다**(`Cannot smooth CVs on periodic curves`).
  v01.07 까지는 그 커브를 통째로 건너뛰었고, **v01.08 부터는 감아 넣은 임시 커브로 우회**한다(위 참고).
- **주기 커브는 CV 가 두 가지로 세어진다.** `.cv[i]` 로 고를 수 있는 것은 `spans` 개인데
  `MFnNurbsCurve.cvPositions()` 는 `spans + degree` 개를 돌려준다 — 뒤의 `degree` 개는 앞의 복사본이다.
  쓸 때 **그 복사본까지 같이 갱신**하지 않으면 이음매가 벌어진다.
- **주기 커브에는 `cmds.curve(replace=True)` 가 그냥은 안 통한다** —
  `Must specify knots with the -per option`. 원본의 `periodic` + `knot` 을 그대로 다시 넘겨야
  형태가 열린 커브로 바뀌지 않는다. `setAttr .controlPoints` 로 쓰는 길은 쓰지 않았다 —
  히스토리가 붙은 커브(예: `makeNurbCircle` 이 살아 있는 원)에서는 그 값이
  **절대 위치가 아니라 트윅(델타)** 이 되어 값이 두 번 섞인다.
- **열린 커브의 양 끝 CV 는 절대 움직이지 않는다**(닫힌 커브에는 해당 없다).
  실측(CV 12개): degree 3 이면 앞뒤 2개씩, degree 5 면 3개씩, degree 2 면 앞 2 / 뒤 1.
  → **끝쪽 CV 만 골랐다면 명령은 성공하는데 아무 것도 변하지 않는다.** 그래서 이 탭은
  **실제로 움직인 CV 수**를 세어 `3 of 21 CV(s) moved` 처럼 보고하고, 0 이면 그 이유를 경고로 띄운다.
  `Check Selection` 은 고른 CV 중 **어떤 것이 고정되어 움직일 수 없는지** 미리 알려 준다.
- `smoothCurve` 는 **실수 smoothness** 를 받는다(`0.5` 와 `1` 의 결과가 다르다). 다만 값에 따라
  **CV 하나만 보면 단조롭지 않을 수 있다** — 실측에서 `s=1` → `s=5` 로 키울 때 전체 최대 변위는
  `1.19 → 2.48` 로 커졌지만 특정 CV 는 `0.89 → 0.81` 로 오히려 줄었다. 스무딩이 굽이를 재분배하기
  때문이며 버그가 아니다.
- `smoothCurve` 는 **히스토리 노드를 만들지 않는다**(일회성 편집).
- **씬 선택을 지우는 마야 명령이 세 개다**(v01.09 에서 둘을 더 찾았다). `cmds.smoothCurve` 는
  다른 커브에 걸어도 **활성 선택을 지우고**, `cmds.curve` 는 **만든 커브를 선택하며**,
  `cmds.delete` 는 지운 것이 선택돼 있었으면 **선택을 비운다.** 이 탭은 슬라이더를 놓을 때마다
  선택을 다시 읽으므로, 한 번이라도 풀리면 그 뒤로는
  `Select some curve CVs first ... [RuntimeError: (kFailure): Object does not exist]`
  (빈 선택에서 `getRichSelection()` 이 던지는 예외) 만 나온다. **닫힌 커브의 임시 사본만**
  `cmds.curve` 로 새로 만들기 때문에 닫힌 커브에서만 이 증상이 났다
  (열린 커브는 `cmds.duplicate` — 선택을 안 건드린다). 세 군데 전부 공용
  `keep_selection()` 컨텍스트로 묶여 있다.
- **선택을 읽는 경로가 두 개다.** 폴오프까지 얻으려면 `MGlobal.getRichSelection()` 이 필요한데,
  이 호출은 **빈 선택에서 예외를 던지고**(`Object does not exist`) 마야 버전/상태에 따라 다른
  이유로도 실패할 수 있다. 그 실패를 조용히 삼키면 **"선택한 게 없다"** 로 오해되어 CV 를
  분명히 골랐는데도 툴이 아무 것도 못 하게 된다(실제로 그 증상이 보고됐다).
  그래서 리치가 실패하거나 비면 **평범한 선택 목록(`cmds.ls(selection=True)`)으로 되돌아가고**,
  어느 경로를 썼는지와 실패 사유를 **로그에 남긴다**. 이때 폴오프는 적용되지 않으므로 그 사실도 알린다.
- 커브 CV 인지는 **컴포넌트 타입 enum 이 아니라 노드가 `nurbsCurve` 인지**로 판정한다.
  NURBS **서페이스** CV(`cv[0][0]`), 메시 버텍스, 오브젝트 선택은 전부 걸러진다.
- **Check Selection** 이 지금 무엇이 잡히는지 그대로 찍는다 — 어느 경로로 읽었는지,
  마야가 보고하는 **원본 선택 문자열**, 커브의 degree/CV 수, 고른 CV 인덱스(`5, 7-16, 19-25` 처럼
  범위로 압축), 폴오프 가중치, 그리고 **고정되어 못 움직이는 CV**. 기대대로 동작하지 않을 때 여기부터 본다.
- **드래그 한 번이 undo 한 스텝**이다. 임시 사본을 **만드는 것까지 청크 안**에 있어야 한다 —
  밖에 두면 `Ctrl+Z` 가 CV 가 아니라 "임시 커브 삭제"를 되돌려, 커브는 그대로인데 임시 노드만
  되살아난다(개발 중 실제로 겪음).
- 드래그 중에는 **원본 스냅샷에서 매번 다시 계산**하므로 값이 누적되지 않는다. 슬라이더를
  왔다 갔다 해도 결과는 그 순간 값 하나로만 정해진다.
- **`smoothCurve` 는 활성 선택을 지운다** — 다른(임시) 커브에 걸어도 그렇다(실측 7개 → 0개).
  그대로 두면 슬라이더를 처음 움직이는 순간 골라 둔 CV 가 전부 풀리고, **그 다음 틱부터는 적용할
  대상이 없어 드래그해도 아무 반응이 없다.** 그래서 이 명령 앞뒤로 활성 선택을 보관했다 되돌린다
  (`MGlobal.getActiveSelectionList` / `setActiveSelectionList`). 소프트 셀렉션 폴오프도 그대로 남는다.
- **드래그 중 화면 갱신은 툴이 직접 한다.** Qt 슬라이더를 붙잡고 있는 동안에는 마야가 스스로
  뷰포트를 다시 그릴 틈을 얻지 못해, CV 는 바뀌는데 **화면은 그대로여서 "드래그해도 반응이 없다"**
  로 보인다(놓는 순간에야 한꺼번에 그려진다). 그래서 틱마다 `cmds.refresh()` 를 부른다.
  refresh 는 이벤트를 처리하므로 슬롯이 재진입할 수 있어 플래그로 막는다.
- **CV 읽기/쓰기는 한 번에 한다.** CV 하나씩 `cmds.xform` 을 부르면 틱마다 수십~수백 개의 명령이
  나가 드래그가 무거워진다. 읽기는 API 배열 접근(`cvPositions`), 쓰기는 **`cmds.curve(replace=True)`**.
  > API 의 `setCVPositions` 가 더 빠르지만 **undo 큐에 남지 않아** Ctrl+Z 로 되돌아오지 않는다
  > (개발 중 실제로 이 회귀를 냈고 테스트가 잡았다). `cmds.curve -r` 은 한 번의 호출로 CV 전체를
  > 바꾸면서 **undo 가 되고**(0.16 ms/call), degree·CV 수·히스토리를 보존하며 숨긴 커브에도 통한다.
  > 한 청크 안에서 여러 번 불러도 `Ctrl+Z` 한 번에 전부 되돌아간다.
- 확정 뒤 슬라이더를 0 으로 되돌릴 때는 **신호를 막고** 되돌린다. 막지 않으면 `valueChanged` 가
  0 으로 다시 적용되어 방금 확정한 결과가 그대로 지워진다.

---

## Create > Controls (v01.15~) — 컨트롤러 커브 만들기 · 색 · 셰이프 교체

Brandon Schaal 의 **`bs_controls`**(Control Curves Tool)를 이 툴로 옮긴 탭이다. 원본은 마야 셸프에서

```python
import bs_controlsUI
bsCon = bs_controlsUI.BSControlsUI()
bsCon.bsControlsUI()
```

로 띄우던 `maya.cmds` 창이었고, **세 섹션(만들기 · 색 · 셰이프 교체)을 순서 그대로** 한 탭에 담았다.

> **셰이프 34종은 툴이 아니라 Framework 가 갖는다** — `Framework/rules/control_shapes.json` +
> [`Framework.core.control_shapes`](Framework_control_shapes.md). 컨트롤러 셰이프는 이 툴만의 것이 아니어서,
> `A00460_ControllerTool` 등 다른 툴도 같은 라이브러리를 쓴다.

### 1. Create Controls

| 칸 | 뜻 |
|----|-----|
| **Name** | 비우면 `<오브젝트>_ANIM`. **한 단어**면 오브젝트 이름의 흔한 접미사(`_jnt` `_loc` `_grp` …)를 그 단어로 바꾼다(`spine_jnt` + `ctl` → `spine_ctl`). **`_` 가 들어 있으면** 그 이름을 그대로 쓴다(공백은 `_`) |
| **Thickness** | `1.0` 초과일 때만 셰이프 `lineWidth` 에 넣는다(표시 굵기, 형상 불변) |
| **셰이프 목록** | 34종. **더블클릭하면 원점에** 하나 만든다 |

| 버튼 | 무엇을 하나 |
|------|-------------|
| **Parent** | 선택 오브젝트 자리에 컨트롤을 만들고 **오브젝트의 부모**로 끼운다(원래 부모 밑으로 들어간다) |
| **Child** | 컨트롤을 **오브젝트 밑**에 두고, 오브젝트의 **자식들은 컨트롤 밑으로** 옮긴다 |
| **World** | 자리만 맞추고 **월드에 그대로** 둔다 |
| **Origin** | 선택과 무관하게 **원점에 하나**. 이름을 비우면 셰이프 이름(`circle_pin`) |

전부 **undo 한 스텝**이고, 만든 컨트롤이 선택된 채로 끝난다.

### 2. Control Color

색은 **셰이프에** 건다 — 트랜스폼에 걸면 **자식들이 전부 물려받기** 때문이다(원본과 같은 판단).

- 색칸 31개 = 마야 오버라이드 인덱스. **`T`** = template(회색·선택 불가), **`R`** = reference(그대로 보이되 선택 불가).
- 색을 지정하면 `overrideDisplayType` 을 `0` 으로 되돌린다 — template/reference 로 둔 채 색을 넣으면 색이 안 보인다.
- **`Reset Color`** 는 트랜스폼과 셰이프 **양쪽** 오버라이드를 끈다(레이어·기본색으로 돌아간다).
- **선택을 지우지 않는다** — 원본은 색을 바꿀 때마다 `cmds.select(d=True)` 로 선택을 날려서, 색을 몇 번
  바꿔 보는 흐름이 그때마다 끊겼다.

#### `Color Palette...` — 인덱스에 없는 색 (v01.17~)

버튼을 누르면 **별도 팔레트 창**이 뜨고, 고른 색이 그대로 들어간다. 옆의 작은 칸은 **마지막으로 고른 색**이고
누르면 그 색을 다시 입힌다. 취소하면 아무것도 바뀌지 않는다.

- 참고: `ref/ref_01.mel` 의 `Color Palettes`. **어트리뷰트도 같다** — `overrideRGBColors` 를 켜고
  `overrideColorRGB` 에 0~1 값을 쓴다.
- **인덱스 색과 임의 색은 스위치 하나(`overrideRGBColors`)로 갈린다.** 그래서 색을 넣을 때마다 그 스위치를
  맞춰 준다 — 안 맞추면 값만 들어가고 **화면은 이전 모드의 색 그대로**라 "왜 안 바뀌지" 가 된다.
  `Reset Color` 도 스위치와 RGB 값을 함께 되돌린다.
- 팔레트는 마야 `colorEditor` 가 아니라 **Qt 팔레트**다 — 이 툴이 PySide 창이라 팝업도 같은 계열이어야
  부모·테마·항상 위 설정이 맞물린다. 고르는 값(0~1 RGB)과 결과는 ref 와 같다.

> **셰이프 교체는 v01.16 에서 [`Display > Replace`](#display--replace-v0116--컨트롤의-셰이프-갈아-끼우기) 로 옮겼다.**
> 원본 창에서는 이 자리(세 번째 섹션)에 있었다.

### 원본에서 바꾼 것

| 원본 `bs_controls` | 이 탭 |
|---|---|
| 선택이 비면 `cmds.error` 로 **중단** | **로그 경고**만 남기고 나머지는 계속 |
| 오브젝트마다 undo 가 쪼개짐 | 버튼 한 번 = **undo 한 스텝** |
| 색 변경 후 **선택 해제** | 선택 유지 |
| 자리 맞추기에 `parentConstraint` 를 걸었다 지움 | **`matchTransform`**(피벗 · `rotateOrder` · `jointOrient` 를 마야가 처리) |
| 셰이프 없는 노드를 고르면 `Reset Color` 가 **죽음**(`UnboundLocalError`) | 건너뛰고 알린다 |
| 셰이프 데이터가 툴 파일 안 | **Framework 공용 데이터**로 승격 |

### 검증 (mayapy 2024 + 오프스크린 Qt, 33항목 통과)

**34종 전부 원본과 CV 단위로 일치** · Gear 셰이프 2개 · thickness → lineWidth · 이름 규칙 3가지 ·
Parent / Child / World / Origin 계층과 위치 · 선택 없이 누르면 경고 · undo 한 스텝 ·
색이 셰이프에만 들어가고 트랜스폼은 그대로 · 선택 유지 · T/R · 색 지정이 displayType 을 되돌림 ·
Reset 이 양쪽을 끔 · 메시도 색이 들어감 · 셰이프 없는 노드는 경고 ·
셰이프 교체(이름·트랜스폼 보존, 원본 불변, 잔여 노드 없음, 1→N, N→N, 개수 불일치 거절, 미러가 X 를 뒤집음) ·
UI(탭 존재, 목록 34, 색칸, 버튼 동작, 창 폭).

---

## Display > Replace (v01.16~) — 컨트롤의 셰이프 갈아 끼우기

이미 있는 컨트롤에 **다른 커브의 모양**을 입힌다. 타깃의 **이름 · 트랜스폼 · 연결은 그대로**고
커브 셰이프 노드만 바뀐다(셰이프 이름은 `<타깃>Shape`).

원본 `bs_controls` 에서는 `Create > Controls` 안의 한 섹션이었고 대상·교체본을 **텍스트 칸**에 담았다.
v01.16 에서 **하위 탭으로 떼어 내고 두 칸을 공용 TSL** 로 바꿨다 — 리스트에 담아 두고 순서를 손보며
여러 번 돌리는 것이 실제 작업 방식이기 때문이다.

### 사용법

1. 바꿀 컨트롤을 씬에서 고르고 왼쪽 **`Shapes to replace`** 의 `List Selected`.
2. 모양을 가져올 커브를 고르고 오른쪽 **`Replacement`** 의 `List Selected`.
3. 필요하면 `Mirror Shapes` 를 켜고 **`Replace Shapes`**.

TSL 이라 `Add` · `Del` · `Up` · `Down` 으로 목록과 **순서**를 그대로 손볼 수 있다.

### 짝 짓는 규칙 ★

| 왼쪽(대상) | 오른쪽(교체본) | 결과 |
|---|---|---|
| N개 | **N개** | **순서대로 1:1** |
| N개 | M개 (N ≠ M) | **적은 쪽 개수만큼** 앞에서부터 1:1, 남는 것은 **건드리지 않는다**(로그에 몇 쌍을 했는지 적는다) |
| N개 | **1개** | 그 하나가 **모든 대상**에 들어간다 |

> v01.15 까지는 개수가 다르면 **아예 거절**했다(원본도 그랬다). v01.16 에서 사용자 요청으로
> **적은 개수만큼 돌리도록** 바꿨다 — 리스트에 담아 둔 것 중 짝이 맞는 데까지 처리하는 편이
> 실제 흐름에 맞는다.

### 알아둘 것

- **`Mirror Shapes`** 는 `scaleX = -1` 인 그룹에 넣었다 빼 **좌우를 뒤집어** 넣는다(반대쪽 컨트롤용).
  이때는 타깃 자리에 맞추지 않는다.
- 복제본(`temp_CRV`) · 미러 그룹(`mirror_GRP`)은 남기지 않는다. 전체가 **undo 한 스텝**.
- 리스트가 비어 있으면 어느 쪽이 비었는지 로그로 알린다.

### 검증 (mayapy 2024 + 오프스크린 Qt, 13항목 통과)

같은 개수 → 순서대로 1:1 · 대상이 더 많음 → 앞 2쌍만, 나머지 불변 + 로그 · 교체본이 더 많음 → 앞 2쌍 ·
교체본 1개 → 전부 · Display 하위 탭이 `Line Width` + `Replace` · `Create > Controls` 에서 교체 위젯이 사라짐 ·
TSL 두 개 · 씬 선택으로 리스트업 · UI 실행 · 빈 리스트 경고 · 창 폭.

---

## Display > Transform (v01.18~) — 셰이프를 피벗 기준으로 크게 · 옮기고 · 돌리기

리스트에 담은 커브마다 **그 커브의 피벗**을 기준으로 **셰이프(CV 전체)** 를
**스케일 / 이동 / 회전**한다. 뷰포트에서 그 커브의 CV 를 **전부 골라** Scale · Move · Rotate 툴을
쓴 것과 **같은 결과**이고, 트랜스폼의 `scale` / `rotate` / `translate` 채널은 **전혀 건드리지 않는다**
— 컨트롤러의 채널은 기본값(0 / 1)으로 남아 있어야 하기 때문이다.

### 사용법

1. 커브(컨트롤)를 씬에서 고르고 **`List Selected Curves`**.
2. 쓸 줄만 켠다 — **`Scale` / `Move` / `Rotate`** 체크박스. **기본은 `Scale` 만 켜져 있다.**
3. 각 줄에서 **X / Y / Z 축 체크박스**로 적용할 축을 고르고 값을 친다.
4. **`Apply to Shapes`**. 다시 누르면 한 번 더 걸린다(스케일은 곱해지고, 이동·회전은 더해진다).

| 위젯 | 내용 |
|------|------|
| `Scale` | 배율. `1` = 그대로, `2` = 두 배, `0.5` = 절반. **음수면 그 축으로 뒤집힌다**(미러) |
| `Move` | 씬 단위 이동량. **그 커브 자신의 축** 방향 |
| `Rotate` | 도(degree). **XYZ 순**, 그 커브 자신의 축 |
| 축 체크박스 | **끄면 그 축은 중립값**(스케일 1 / 이동·회전 0) — 아무 것도 안 한 것과 같다 |
| `Uniform` | **Scale 전용**. 한 칸에 친 값을 **켜 둔 다른 축**에도 그대로 넣는다(세 축을 같은 배율로 키우는 것이 대부분이라 기본 켬) |
| `Reset Values` | 칸만 기본값으로(스케일 1 / 이동 0 / 회전 0). **씬은 건드리지 않는다** |

### 기준점과 축 ★

```
new_cv = pivot + T + R * (S * (cv - pivot))          # 스케일 → 회전 → 이동
```

- **기준점은 그 커브 트랜스폼의 rotate pivot** 이다. 피벗을 옮겨 둔 컨트롤은 **옮긴 그 자리**가 기준이 된다.
- 계산은 **오브젝트 공간** — 축은 그 커브 **자신의 로컬 축**이다. 그래서 회전이 들어간 좌우 컨트롤에
  **같은 값**을 넣으면 각자 자기 축으로 같은 만큼 변한다(월드 축으로 갈리지 않는다).
- 셋 다 켜면 **스케일 → 회전 → 이동** 순으로 한 번에 걸린다.
- 트랜스폼 아래 **셰이프가 여러 개**면(합쳐진 컨트롤) **전부 같은 피벗 기준**으로 함께 변환한다 —
  모양 하나만 움직여 어긋나지 않게.

### 알아둘 것

- CV 쓰기는 `cmds.curve(shape, replace=True, point=...)` **한 번**이다. **undo 가 되고**
  (API 의 `setCVPositions` 는 undo 큐에 안 남는다) 히스토리가 살아 있는 커브(예: `makeNurbCircle` 이
  붙은 원)에서도 통하며 degree · CV 수를 보존한다. `setAttr .controlPoints` 는 히스토리가 있으면
  **절대 위치가 아니라 트윅**이 되므로 쓰지 않는다(같은 판단이 `Edit > Smooth` 에도 있다).
- **닫힌(주기) 커브**는 `replace=True` 만으로는 거절된다("Must specify knots with the -per option") →
  `periodic` + `degree` + `knot` 까지 같이 넘긴다. 모든 CV 에 **같은 변환**을 걸어 이음매도 어긋나지 않는다.
- 커브가 아닌 항목 · 없는 노드는 건너뛰고 **사유를 로그에 적는다**. 전체가 **undo 한 스텝**.
- 값이 전부 중립(스케일 1 / 이동 0 / 회전 0)이면 아무 것도 하지 않고 경고만 낸다.

### 검증 (mayapy 2024, 코어 23항목 + 오프스크린 Qt UI 20항목 통과)

**코어** — CV 를 전부 골라 `cmds.scale` / `move` / `rotate`(축 = `objectSpace`, 피벗 = 커브의 월드 rotate pivot)
를 건 결과와 **소수점까지 같음**: 균일 스케일 · 축 하나만 스케일(이동+회전된 트랜스폼) · 옮긴 피벗 기준 스케일 ·
음수 스케일(미러) · 축 하나만 이동 · degree 1 열린 커브 이동 · 옮긴 피벗 기준 회전 · XYZ 회전(회전된 트랜스폼) ·
degree 1 커브 회전. 그 밖에 트랜스폼 채널 불변 · 닫힌 커브의 form/CV 수 보존 · 히스토리 커브 · undo 한 스텝 ·
셰이프 여러 개 · 메시/없는 노드 걸러내기 · 셰이프 노드 직접 입력.

> `cmds.scale` / `rotate` 의 `-pivot` 은 `-objectSpace` 를 줘도 **월드 좌표**다(mayapy 로 확인).
> 비교할 때 이걸 오브젝트 공간 값으로 넘기면 엉뚱한 결과가 나온다.

**UI** — Display 하위 탭이 `Line Width` / `Replace` / `Transform` · 기본은 Scale 만 켜짐(나머지 칸은 비활성) ·
축을 끄면 중립값 · `Uniform` 켬/끔 · `Reset Values` · 빈 리스트 · 아무것도 안 켬 · 중립값 경고 ·
실제 적용(스케일 배율 + Y 만 이동) · 트랜스폼 채널 불변 · 커브 아닌 항목 로그.

---

## Edit > Joints (v01.07~) — 커브(와 NURBS 서피스)를 조인트로 움직이게

> **v01.14~ NURBS 서피스도 받는다.** 리스트에 커브와 서피스를 섞어 담아도 된다.
> 서피스는 **U 또는 V 방향의 아이소파름 한 줄**을 커브처럼 보고 같은 흐름(배치 → 바인드 → 스택)을 탄다.
> 자세한 내용은 아래 [NURBS 서피스 (v01.14~)](#nurbs-서피스-v0114) 절.

커브를 애니메이션·리깅에서 쓰려면 **커브를 직접 잡는 대신 무언가가 커브를 끌어 주어야** 한다.
이 탭은 그 셋업을 한 번에 만든다.

```
리스트업한 커브
   ↓ ① 균일 배치
조인트 n 개
   ↓ ② 바인드(skinCluster)
커브가 조인트를 따라간다
   ↑ ③ 컨스트레인트
<joint>_zro > _con > _ctl > _tgt      ← 애니메이터는 _ctl 만 잡는다
```

컨트롤러 스택의 모양·옵션·툴팁은 **`A00460_ControllerTool` 의 FK 탭과 같게** 맞췄다.
두 툴을 오가며 써도 같은 자리에서 같은 이름을 찾을 수 있어야 하기 때문이다.

### 사용법

1. 씬에서 커브 또는 NURBS 서피스를 고르고 **List Selected**.
2. **Count per Object** 를 정한다. 서피스라면 **Surface Direction**(U / V)과 **Across** 도.
3. 필요하면 아래 옵션을 손보고 **Create Joints**.

만들어진 컨트롤러가 선택된 채로 끝난다. **전체가 undo 한 스텝**이다.

### Count per Object — 몇 개를, 어디에

커브의 **처음~끝을 `[0, 1]`** 로 보고 그만큼 균일하게 놓는다.

| 입력 | 놓이는 자리 |
|------|-------------|
| `1` | `0.5` (구간 중앙 하나) |
| `2` | `0`, `1` (양 끝) |
| `3` | `0`, `0.5`, `1` |
| `5` | `0`, `0.25`, `0.5`, `0.75`, `1` |

**닫힌 커브는 마지막 자리를 뺀다.** 닫힌/주기 커브에서 `u=1` 은 `u=0` 과 **같은 점**이라
그대로 두면 마지막 조인트가 첫 조인트 위에 겹친다. 그래서 `count` 등분으로 바꿔
`4` → `0, 0.25, 0.5, 0.75` 를 쓴다. (엣지 루프에서 뜬 커브가 대부분 여기 해당한다)

### Spacing — 호 길이 균등 vs 파라미터 균등

| 옵션 | 뜻 |
|------|-----|
| **By length** (기본) | 눈에 보이는 **커브를 따라** 균등. `MFnNurbsCurve.findParamFromLength` |
| **By parameter** | 커브 **자기 파라미터** 범위에서 균등 |

둘은 스팬 길이가 고르면 같지만, **제각각이면 눈에 띄게 달라진다.** 예를 들어 CV 가
`(0,0,0) (1,0,0) (11,0,0)` 인 직선 커브(스팬 1 : 10)에 3개를 놓으면

- **By length** → `x = 0, 5.5, 11` (정확히 절반 지점)
- **By parameter** → `x = 0, 1, 11` (짧은 스팬 쪽에 몰린다)

메시 엣지에서 뜬 커브는 스팬 길이가 고르지 않은 게 보통이라 **기본은 By length** 다.

### 나머지 옵션

| 옵션 | 기본 | 설명 |
|------|------|------|
| **Surface Direction** (v01.14~) | `U` | 서피스에서 조인트를 **U 를 따라**(V 고정) 놓을지 **V 를 따라**(U 고정) 놓을지. 커브는 무시 |
| **Across** (v01.14~) | `0.5` | 서피스에서 그 줄이 **반대 방향 어디에** 있는지, 파라미터 범위의 비율 `0~1`. `0.5` = 가운데 줄. 커브는 무시 |
| **Aim joints along the curve / row** | 켬 | 조인트 **X 축을 접선**으로 돌린다. 커브는 up 힌트가 월드 Y(접선이 Y 와 나란하면 월드 Z), **서피스는 Y 가 서피스 노멀 쪽**. 컨트롤러는 조인트에 맞춰지므로 같이 돈다. 끄면 조인트가 월드 방향 그대로 |
| **Bind the curve / surface to the new joints** | 켬 | 방금 만든 조인트로 그 커브/서피스를 `skinCluster`. **이미 skinCluster 가 걸린 것은 건너뛰고** 로그에 남긴다(덮어쓰지 않는다) |
| **Group the new nodes per object** | 켬 | `<name>_crvJnt_grp`(서피스는 **`<name>_srfJnt_grp`**) 밑에 `<name>_jnt_grp` · `<name>_ctl_grp` 로 나눠 담는다 |
| **zro / con / tgt** | 셋 다 켬 | 컨트롤러 스택에 넣을 널. **`ctl`(큐브 커브)은 항상** 만든다 |
| **Control Size** | `1.0` | 큐브의 **반변 길이**(반지름 감각) |
| **Constraint** | Parent | 조인트가 스택 **마지막 노드**(보통 `_tgt`)를 따르는 방식. Parent / Point / Orient / Scale |

### 만들어지는 이름

커브 이름이 `spine_crv`, 조인트 3개라면

```
spine_crv_crvJnt_grp
├── spine_crv_jnt_grp
│   ├── spine_crv_1_jnt        (0.0 지점)
│   ├── spine_crv_2_jnt        (0.5)
│   └── spine_crv_3_jnt        (1.0)
└── spine_crv_ctl_grp
    ├── spine_crv_1_jnt_zro > _con > _ctl > _tgt
    ├── spine_crv_2_jnt_zro > ...
    └── spine_crv_3_jnt_zro > ...

spine_crv_skinCluster          (커브를 세 조인트에 바인드)
```

번호는 개수 자릿수만큼 0 을 채운다 — 3개면 `1`~`3`, 12개면 `01`~`12`.
이름이 이미 쓰이고 있으면 마야가 뒤에 번호를 붙이고, **그 사실을 로그에 남긴다**.

### NURBS 서피스 (v01.14~)

서피스에서는 **한 줄**을 고른다 — 방향(U/V)과 그 줄이 반대 방향 어디에 있는지(Across).

```
Direction U, Across 0.5            Direction V, Across 0.25
 V                                  V
 ↑ ┌───────────────────┐            ↑ ┌───────────────────┐
 │ │                   │            │ │    ●              │
 │ │ ●────●────●────●  │  ← 가운데  │ │    ●              │
 │ │                   │            │ │    ●              │
 │ └───────────────────┘            │ └───────────────────┘
 └──────────────────────→ U         └──────────────────────→ U
```

- **Count · Spacing · 닫힘 처리 · 바인드 · 컨트롤러 스택은 커브와 똑같다.**
  - **By length** 는 그 줄의 **호 길이** 균등이다. 아이소파름용 길이 함수가 MFn 에 없어서, 줄을 **스팬당 32점**으로
    촘촘히 찍은 꺾은선 길이로 재고 역보간한다(스팬 1 : 3 인 평면에서 가운데 조인트가 정확히 가운데).
  - **원통처럼 그 방향으로 닫힌(`formU/formV ≠ 0`) 서피스**는 커브처럼 마지막 자리를 뺀다 — 둘레에 4개면 90° 간격.
- **Across 는 파라미터 비율**이다. 반대 방향으로 호 길이를 맞추지는 않는다(스팬이 고르지 않으면 `0.5` 가 눈으로 본 정가운데와 조금 다를 수 있다).
- **조준(Aim)** — X = 그 방향 접선, **Y = 서피스 노멀 쪽**. 노멀은 `tangentU × tangentV` 라 `[tanU, N, tanV]` 를 그대로 행렬에 넣으면
  왼손계가 되어 회전이 뒤집힌다. 그래서 `Z = X × N`, `Y = Z × X` 로 직교화한다(A00170 AttachCrv 와 같은 판단).
- **극점(구의 끝처럼 한 점으로 모이는 줄)** 은 접선이 0 이라 방향을 정할 수 없다. 그 조인트는 월드 방향으로 두고
  **로그에 경고**한다. 줄 전체가 한 점이면 조인트들도 한 점에 겹친다 — Direction 이나 Across 를 바꾸면 된다.
- 결과 이름은 커브와 같은 규칙이고 최상위 그룹만 `<name>_srfJnt_grp` 다.

### 알아둘 것 (mayapy 로 확인)

- **NURBS 서피스에도 `skinCluster` 가 걸린다** (v01.14~) — 컨트롤러를 움직이면 서피스 CV 가 따라온다.
- **커브에도 `skinCluster` 가 걸린다.** 메시 전용이 아니다. `polyToCurve` 로 만든
  **히스토리가 살아 있는 커브**에도 걸리고(디포머가 히스토리 뒤에 끼어든다) 조인트가
  CV 를 정상으로 끈다.
- **바인드는 조인트를 그룹에 넣은 뒤에 한다.** `bindPreMatrix` 는 **바인드 시점의 행렬**을
  잡아 두므로, 바인드하고 나서 조인트를 옮기면 옮긴 것만으로 커브가 튄다.
- **리페어런트는 롱네임을 죽인다.** 조인트를 `_jnt_grp` 에 넣는 순간 `|spine_crv_1_jnt` 는
  없는 경로가 된다(`cmds.xform` 이 곧바로 `No object matches name`). 결과 dict 에는
  **옮긴 뒤의 경로**를 담고, 컨트롤러 스택은 옮기기 전에 **UUID** 를 잡아 두었다가 다시
  해석한다. 개발 중 실제로 이 회귀를 냈고 헤드리스 테스트가 잡았다.
- **조인트는 하나씩 선택을 비우고 만든다.** `cmds.joint` 는 **현재 선택의 자식**으로 붙으므로
  그냥 반복하면 조인트끼리 부모-자식 체인이 된다. 커브를 구동하는 조인트들은 각자 독립으로
  움직여야 CV 가 제 몫만큼만 따라온다.
- **조인트 방향은 `rotate` 가 아니라 `jointOrient` 에 쓴다.** 조인트의 로컬 행렬은
  `R * JO` 라, 부모가 항등이고 `rotate` 가 0 인 갓 만든 조인트에서는 `jointOrient` 에 넣은
  값이 곧 월드 방향이 된다. `rotate` 에 넣으면 애니메이터가 채널을 0 으로 돌리는 순간
  방향이 풀린다.
- **`A00460_ControllerTool` 의 `fk_manager` 를 import 하지 않는다.** 노드 구성은 같지만
  `dev/build_release.py` 가 **툴 하나 + Framework** 만 릴리스로 복사하므로, 다른 툴의 core 를
  참조하면 릴리스에서 곧바로 깨진다. 정말 공유해야 해지면 `Framework` 로 올릴 자리다.
- 커브·서피스가 아닌 항목(메시 등), 씬에 없는 이름, 이미 바인드된 것은 **사유와 함께 건너뛴다** — 나머지
  처리는 계속된다.

**v01.14 검증** (mayapy 2024 + 오프스크린 Qt, **22항목 전부 통과**): 이동·회전한 평면에서 U 5개가 **서피스 위**에 **같은 간격** ·
`_srfJnt_grp` + 서피스 skinCluster · V 줄은 U 줄과 **직교**하고 가운데에서 만난다 · Aim 의 X = 줄 방향, Y = 노멀(내적 1.0) ·
컨트롤러를 움직이면 서피스가 변형 · Across 0 과 1 이 반대 가장자리 · 스팬 1 : 3 에서 By length 는 가운데 0, By parameter 는 -1 ·
원통 둘레(닫힌 방향) 4개가 겹치지 않고 균등 · 구의 극점 줄에서 크래시 없이 경고 · **커브 기존 동작(0, 5.5, 11) 그대로** ·
커브+서피스+메시 혼합(메시는 사유와 함께 건너뜀) · 잘못된 방향 거절 · UI 기본값 U / 0.5 · UI 에서 V · 4개 · Across 0.25 로 생성 → **undo 한 번에 전부 제거** ·
Joints 탭 최소 폭(906)이 창 폭(1176) 안.

- 핵심 API:
  - `joint_curve_manager.build_joints_on_curves(curves, count, spacing, aim, bind, group, use_zro, use_con, use_tgt, constraints, size, joint_radius, direction, across)` → 결과 dict
    (`curves` / `surfaces` / `joints` / `controls` / `roots` / `groups` / `skins` / `constraints` / `missing` / `skipped` / `renamed` / `warnings`)
  - `joint_curve_manager.uniform_us(count, closed)` → `[0, 1]` 위의 균일 위치 목록
  - `joint_curve_manager.sample_curve(shape, count, spacing)` → `[(월드 위치, 월드 접선, None), ...]`
  - `joint_curve_manager.sample_surface(shape, count, spacing, direction, across)` → `[(월드 위치, 월드 접선, 월드 노멀), ...]` (v01.14~)
  - `joint_curve_manager.resolve_target(node)` → `(shape, "curve" | "surface")`, 둘 다 아니면 `(None, None)` (v01.14~)

---

## Edit > Combine (v01.11~) — 커브 쉐입 합치기

좌측 **Source** 리스트의 커브 쉐입을 우측 **Target** 리스트의 커브 트랜스폼 밑에 붙인다.
컨트롤러 모양을 여러 커브로 그린 뒤 하나로 묶을 때 쓴다.

### 사용법

1. 좌측 **Select Source** 로 합칠 커브들을, 우측 **Select Target** 으로 받을 커브를 담는다.
   - Target **1 개** → 모든 Source 가 그 Target 으로 간다.
   - Target **여러 개** → Source 와 **행 순서대로 1:1**. 개수가 다르면 실행하지 않는다.
2. 옵션
   - **Placement** (v01.13~)
     - **Move to Target position**(기본) — Source 를 **Target 의 월드 위치로 옮겼을 때의 모양**으로 붙는다.
       Maya *Match Transformation > Position* 처럼 **rotate pivot 끼리** 맞추고, Source 의 회전·스케일은 그대로 둔다.
     - **Keep Source world position** — 붙은 쉐입이 **원래 보이던 자리 그대로** 남는다(v01.11~01.12 기본).
     - **Keep local CV values** — CV 로컬 값을 그대로 가져가서 Target 트랜스폼을 따라 움직인다(MEL `parent -s -add` 와 같다).
   - **Delete Source curves after combining** — 복사가 끝난 Source 를 지운다.
     Source 가 다른 짝의 Target 이거나 **밑에 Target 이 있으면** 지우지 않는다(같이 사라지므로).
3. **Combine Shapes** — 한 번의 Undo 로 되돌릴 수 있다. 새 쉐입 이름은 `<Target>Shape#`.

### 왜 MEL `parent -s -add` 를 쓰지 않나 (mayapy 로 확인)

`parent -s -add` 는 쉐입을 **옮기거나 복사하지 않고 인스턴스로 하나 더 매단다** — 노드는 하나인데
부모가 둘이다(`listRelatives(shape, allParents=True)` → `['A', 'B']`).

| A 를 지우는 방법 | B 에 붙은 쉐입 |
|------------------|----------------|
| 아웃라이너에서 계층째 (`select -hi A; delete`) | **함께 삭제** |
| 쉐입 경로 (`delete \|A\|AShape`) | **함께 삭제** |
| 트랜스폼만 (`delete A` / `doDelete`) | 남는다 |

지우지 않아도 **A 의 CV 를 움직이면 B 도 같이 움직인다** — 같은 노드이기 때문이다.

이 탭은 대신 ① Source 를 `duplicate`(upstream 없이 → 히스토리 없는 현재 모양의 **새 쉐입 노드**)
② 새 쉐입을 `parent -r -s` 로 Target 에 **옮기고** ③ 임시 트랜스폼을 지운다.
결과 쉐입은 Source 와 연결이 전혀 없다.

### 알아둘 것

- **히스토리가 있는 Source**(예: `makeNurbCircle`) — 복사본은 입력이 없는 **정적 모양**이다.
  이후 Source 의 히스토리를 바꿔도 따라가지 않는다.
- **스킨된 Source** — intermediate(`Orig`) 쉐입은 제외하고, **지금 디폼된 모양**을 복사한다.
- Target 에 디포머가 있어도 새 쉐입은 그 디포머에 들어가지 않는다(별도 쉐입이다).
- 한 Source 에 쉐입이 여러 개면 전부 복사한다. 커브가 아닌 항목은 건너뛰고 로그에 남긴다.

---

## 로그창 (v01.10)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위에 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
