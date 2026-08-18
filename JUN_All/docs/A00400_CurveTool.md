---
title: A00400_CurveTool 사용법
aliases: [Curve Tool, CurveTool, A00400]
tags: [maya-python, tool-guide, curve, mesh-edge, polyToCurve, lineWidth, wrap, blendShape, editPoint, laplacian]
updated: 2026-08-18
---

# A00400_CurveTool 사용법

Maya 안에서 도는 **커브** PySide 툴이다(arch B, in-Maya). **탭 4개**로 나뉜다(v01.04).

| 탭 | 내용 |
|----|------|
| **Create / Direction** | ① 선택한 메시 엣지에 부착된 커브 생성(엣지 덩어리마다 커브 하나) ② Reverse Direction(방향 통일) |
| **Line Width** (v01.01~) | 리스트업한 커브의 **뷰포트 표시 굵기**를 슬라이더로 조절 — 씬에서 **잘 보이고 잘 집히게** |
| **Wrap** (v01.03~) | **CV 개수가 달라도** 한 커브가 다른 커브의 모양을 따르게 한다. 0~1 envelope 어트리뷰트로 라이브 블렌드 |
| **Points to Curve** (v01.04~) | 리스트에 담은 오브젝트·조인트·컴포넌트의 **월드 위치**를 **순서대로** 잇는 커브 하나. 정확히 통과 / 완화 선택 |

- **버전**: `app/config/version.py` (v01.04)
- **설치**: `__dragDrop_A00400.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **CurveTool** → `tools.A00400_CurveTool.run(True)`
- **참고**: 엣지→커브 생성은 `ref/ref_01.mel`(`duplicateCurve`+`attachCurve`)의 아이디어를, 축 비교 방식은 `A00360_SortTool` 을 이식/응용.

---

## 1. 화면 구성

```
┌ Curve Tool ─────────────────────────┐
│ Help                                │
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
    ├── core/curve_manager.py   # 엣지 그룹핑 + polyToCurve + reverseCurve (maya.cmds, UI 비의존)
    └── ui/main_window.py       # PySide UI (생성 박스 + TSL + Reverse 박스 + 로그)
```

- 핵심 API:
  - `curve_manager.curves_from_selected_edges(prefix, degree)` → `(created_curves, group_count)`
  - `curve_manager.reverse_curves_by_axis(curves, mode, cv0_at_max)` → `(reversed_names, skipped)`
    - `mode` = `MODE_X/Y/Z`, `cv0_at_max=True` 면 `cv[0]` 을 축 최대 끝에.
  - `curve_manager.group_edges(edges)` → 연결 성분별 엣지 그룹 리스트.

---

## Line Width 탭 (v01.01~) — 커브를 잘 보이고 잘 집히게

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

## 탭 3 — Wrap (v01.03~)

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

## 탭 4 — Points to Curve (v01.04~)

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
