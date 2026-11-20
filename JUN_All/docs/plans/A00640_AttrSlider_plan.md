---
title: A00640_AttrSlider — 선택한 노드의 어트리뷰트를 슬라이더로 계획서
aliases: [A00640, AttrSlider, 어트리뷰트 슬라이더, 채널박스 슬라이더]
tags: [plan, maya-python, animation, attribute, slider, blendshape, fbxasc, A00640]
updated: 2026-11-20
---

# A00640_AttrSlider — 선택한 노드의 어트리뷰트를 슬라이더로 계획서

> 작성 2026-11-20 · 상태: **1단계 구현 (v01.00)** · 아키텍처 (B) Maya 내 PySide 툴
>
> 요청 (2026-11-20):
> - 마야에서 **선택한 오브젝트의 어트리뷰트를 나열**하고 각각을 **슬라이더로 조절**한다.
>   예: `A00390_WindTool_V03` > Chain Wave Lite 가 만드는 `*_liteDriver` 로케이터의 `Wind Swing Angle` · `Wind Wavelength` 등.
> - 일반 오브젝트는 **채널박스에 보이는 어트리뷰트**를 나열한다.
> - **blendShape 노드를 고르면 타겟 웨이트**를 슬라이더로 조절한다.
> - `A00620_NameDecoder` 처럼 **마야가 표현할 수 없는 글자(일본어 등, FBXASC)를 풀어** 보여 준다.
>
> 결정 (이전 턴 논의): A00620 에 탭으로 넣지 않는다 — A00620 은 "읽기 전용 이름 해독" 툴이라 도메인이 다르다.
> A00145 Attribute 하위 탭도 아니다 — 리깅용 큰 창이라 재생하며 옆에 띄워 두기 무겁다. → **작은 새 툴**.

---

## 0. 요약

- **무엇**: 고른 노드마다 섹션(풀린 노드 이름) 하나, 그 아래 채널박스 어트리뷰트마다 **이름 · 슬라이더 · 숫자 칸** 한 줄.
  bool = 체크박스, enum = 콤보(항목 이름도 풀어서). blendShape = `envelope` + 타겟 웨이트(풀린 타겟 이름).
- **선택을 따라간다**(`SelectionChanged`). `Lock List` 로 목록을 고정할 수 있다.
- **시간 · undo 를 따라간다** — 시간이 바뀌거나 undo/redo 하면 값만 다시 읽는다(위젯은 다시 만들지 않는다).
- **슬라이더 드래그 한 번 = undo 한 번.**
- **씬을 바꾸는 것은 `setAttr` (+ 켜면 `setKeyframe`) 뿐**이다.

## 1. 실측 (2026-11-20, mayapy, 계획을 정한 근거)

| 상황 | `setAttr` | 결과 / 결정 |
|------|-----------|-------------|
| 시간 커브 키(`animCurveT*`) | 됨 | 시간을 옮기면 커브 값으로 돌아감 → **Keyed** 표시(분홍) + `Auto Key` 옵션 |
| 애님 레이어(`animBlendNode*`) | 됨 | 같은 이유로 **Keyed** 로 다룬다 |
| 드리븐 키(`animCurveU*`) | 에러 없이 됨 | 곧 드라이버가 덮어씀 → **Driven**(노랑) · **비활성** |
| 일반 연결 · 잠금 | 에러 | **Driven / Locked** · 비활성, 이유는 툴팁 |
| 하드 최솟값 아래 | 에러 | 넣기 전에 하드 범위로 자른다 |
| blendShape `weight` | 하드 -10~10, **소프트 0~1** | 범위 규칙이 **소프트를 하드보다 먼저** 봐야 0~1 슬라이더(처음 하드를 먼저 봐서 -10~10 이 됐다 - 시험으로 잡음) |
| FBXASC 이름의 어트리뷰트 | niceName 도 FBXASC 그대로 | 긴 이름을 `fbx_name.decode` 로 직접 푼다 |
| `listAttr -k` / `-cb` | 키어블 / 비키어블 표시 | 둘을 합치고 hidden · compound 부모는 뺀다(A00145 `channel_box_attrs` 와 같은 규칙) |

## 2. 범위(슬라이더 끝) 규칙 — 핵심 설계

liteDriver 의 어트리뷰트는 대부분 **최솟값만 있거나 범위가 없다**(Envelope 0~1 · Tip Follow 0~0.99 만 양쪽).
그래서 우선순위로 정한다(`app/core/ranges.py`, 마야 비의존):

1. **사용자 범위** — 행 우클릭 `Set Range...` 로 저장한 것. **어트리뷰트 이름** 기준(노드가 달라도, liteDriver 를 다시 만들어도 같은 범위).
   optionVar 에 json 으로 둔다.
2. **양쪽 소프트 범위** (blendShape weight 0~1) — weight 는 하드 -10~10 도 있다(실측). 소프트가 "슬라이더 범위" 라는 뜻이라 먼저 본다
3. **양쪽 하드 범위** (Envelope 0~1)
4. 하드 최소만 있음 → `[min, max(min + 기본폭, 값 × 2)]`
5. 아무 범위 없음 → 각도 = -180~180, 그 밖은 `값 ± max(기본폭, |값|)`
6. int 는 정수로 반올림, bool · enum 은 슬라이더가 아니다.

- 범위는 **행을 만들 때 한 번** 정한다(값이 바뀔 때마다 끝이 움직이면 혼란스럽다).
  숫자 칸으로 범위 밖 값을 넣으면 **그 행만 범위를 넓힌다**(저장 안 함). `Reset Range` 는 저장한 범위를 지운다.
- 숫자 칸은 하드 범위까지 받는다(없으면 ±1e6).

## 3. 나열 규칙

- 고른 노드 순서대로 섹션. 같은 노드는 한 번만, **최대 30 노드**(넘으면 로그 경고).
- 일반 노드: 채널박스 어트리뷰트(키어블 + 비키어블 표시, listAttr 순서). 다루는 타입 = float 계열 · int 계열 · bool · enum.
  문자열 · 행렬 · 메시 성분 같은 것은 뺀다.
- `View > Shapes`(기본 켬): 트랜스폼이면 중간 셰이프가 아닌 셰이프의 채널박스 어트리뷰트도 섹션으로(채널박스 SHAPES 처럼).
- `View > Blend Shapes of Selection`(기본 켬): 고른 메시의 히스토리에 있는 blendShape 도 섹션으로(채널박스 INPUTS 처럼).
- blendShape 노드: `envelope` + 타겟(`weight[i]` 별칭, 공용 `maya_fbx_names.blendshape_targets`).
- 이름 표시: `View > Nice Names / Long Names`. FBXASC 가 든 이름은 **풀어서**, 원래 마야 이름은 툴팁.
  노드 이름 · 어트리뷰트 이름 · 타겟 이름 · enum 항목 이름 모두.
- Filter 칸: 풀린 이름 · 마야 이름 어느 쪽이든 맞으면 보인다. 맞는 행이 없는 섹션은 숨긴다.

## 4. 쓰기 규칙

- 드래그: 누를 때 undo 묶음 열고 놓을 때 닫는다 → 한 번의 Ctrl+Z.
- 숫자 칸: Enter · 포커스 아웃에서 확정(`keyboardTracking` 끔) — 칠 때마다 쓰면 뒷자리를 못 친다.
- 하드 범위로 자른 뒤 `setAttr`. int 는 반올림.
- `Auto Key`(기본 끔): 쓴 뒤 `setKeyframe`. 키가 이미 있는 어트리뷰트만 키를 찍을지 고르는 옵션은 두지 않는다 —
  켜면 바꾼 어트리뷰트에 키를 찍는다(마야 Auto Key 와 같은 기대).
- 행 색: Keyed = 분홍 · Driven = 노랑 · Locked = 회색(마야 채널박스 색을 따름).

## 5. 구조

```
tools/A00640_AttrSlider/
├── __init__.py · launch.py · __dragDrop_A00640.py
├── app/config/version.py
├── app/core/ranges.py      # 범위 규칙 + 사용자 범위 저장소(마야 비의존 계산 / optionVar 저장은 주입)
├── app/core/attr_rows.py   # 씬 → 섹션 · 행(종류 · 범위 재료 · 상태) / 값 읽기 · 쓰기
├── app/ui/main_window.py   # 섹션 · 행 위젯, scriptJob, Filter
├── icon/A00640_AttrSlider.svg · .png
└── tests/test_attr_slider.py   # mayapy 오프스크린 (core + UI)
```

- 공용 재사용: `Framework/core/fbx_name`(디코드) · `maya_fbx_names.blendshape_targets` · `maya_undo.undo_chunk` ·
  `MOD_sliderStyle_qt_v01` · `MOD_log_qt_v01` · `MOD_menuBar_qt_v01` · `pin_style`.
- **A00145 의 어트리뷰트 질의 코드는 import 하지 않는다**(툴 간 import 금지). 같은 규칙(채널박스 판정 · 종류 표 · enum 파싱)을
  `attr_rows.py` 에 둔다. 공용 `Framework/core` 로 합치는 것은 A00145 를 함께 시험해야 해서 **이번 범위 밖**(아래 3단계).

## 6. 단계

1. **v01.00** — 위 전부(나열 · 슬라이더 · 범위 · 디코드 · 상태 색 · Auto Key · Filter · Lock List · 시간/undo 동기화).
2. 다음 — 여러 노드의 같은 어트리뷰트를 한 슬라이더로(`Common` 모드, 상대/절대), 어트리뷰트 즐겨찾기(순서 고정).
3. 다음 — A00145 `attr_value_manager` 와 질의 코드를 `Framework/core/maya_attr_values.py` 로 합친다.

## 7. 시험 (mayapy 오프스크린)

- 범위 규칙: 사용자 > 하드 양쪽 > 소프트 양쪽 > 최소만 > 없음(각도/그 밖), int 반올림.
- 나열: 채널박스 어트리뷰트 = 키어블 + `cb`, hidden · compound 부모 제외, Shapes · Blend Shapes 옵션, 30 노드 한계.
- 디코드: FBXASC 노드 · 어트리뷰트 · 타겟 · enum 항목 이름.
- 상태: Keyed(시간 커브 · 레이어) · Driven(연결 · 드리븐 키) · Locked.
- 쓰기: 하드 범위 자르기, 드래그 = undo 한 번, Auto Key 가 키를 찍음.
- UI: 선택 → 섹션/행 수, 슬라이더 → 씬 값, 숫자 칸 범위 밖 → 범위 넓힘, 시간 변경 → 위젯 값, Filter, Lock List.
- liteDriver 모양(Wind Swing Angle 최소 0 · Envelope 0~1 · Tip Follow 0~0.99)의 로케이터.

## 8. 결과

- **v01.00 (2026-11-20)** — 1단계 전부 구현. 시험 `tests/test_attr_slider.py` **75항목** 통과(mayapy 오프스크린,
  범위 17 · 나열 8 · 디코드 4 · blendShape 7 · 상태 6 · 쓰기 5 · UI 28). 가이드 `docs/A00640_AttrSlider.md`.
- 구현 중 실측으로 바뀐 것: 범위 규칙에서 **소프트를 하드보다 먼저** 본다 — blendShape weight 가 하드 -10~10 과 소프트 0~1 을
  둘 다 가져서, 처음 계획 순서(하드 먼저)로는 -10~10 슬라이더가 됐다(시험이 잡음).
- 트랜스폼을 고르면 셰이프 섹션도 나온다(로케이터는 localPosition · localScale) — 채널박스 SHAPES 와 같은 동작이라 그대로 둔다(`View > Shapes` 로 끈다).
- **마야 GUI 확인 아직.**
