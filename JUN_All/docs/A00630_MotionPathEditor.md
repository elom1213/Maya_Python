---
title: A00630_MotionPathEditor 사용법
aliases: [A00630, Motion Path Editor, MotionPathEditor, 모션 경로 편집, editable motion path, motion trail 대체]
tags: [maya-python, tool-guide, animation, motion-path, motion-trail, viewport-draw]
updated: 2026-11-19
---

# A00630_MotionPathEditor 사용법

오브젝트 · 조인트가 **프레임마다 어디에 있는지를 뷰포트에 경로로 그리고**, 경로 위의 **키 점을 끌어 애니메이션을 고치는** in-Maya PySide 툴(arch B).
그래프 에디터를 열지 않고 궤적 모양을 보면서 위치 애니메이션을 고친다.

- **버전**: `app/config/version.py` (v01.03 — **애니메이션 레이어**: 고른 레이어의 키만 끌어 고친다(경로는 합친 움직임) · v01.02 — Edit Path 를 켜도 버튼이 연한 빨강이 안 되던 것 수정 · v01.01 — 키 드래그 에러 수정 · Custom 범위에 Get Current / Get Sel Range · Edit Path 켜짐 = 연한 빨강 · v01.00 — 첫 버전: 위치 경로 표시 + 키 드래그)
- **설치**: `__dragDrop_A00630.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **MPath** → `tools.A00630_MotionPathEditor.run(True)`.
  툴 런처(A00370) ANIM 프로파일에도 **MotionPath** 버튼이 있다.
- **계획서**: [plans/A00630_MotionPathEditor_plan.md](plans/A00630_MotionPathEditor_plan.md) — 단계별 계획 · 0단계 실측 결과 · 다음 단계
- **원본 아이디어**: 블렌더 애드온 *Editable Motion Paths* (GPL-3.0-or-later). **코드는 쓰지 않은 독자 구현**이다(계획서 §1).

---

## 1. 화면

```
[Help]
  Draw the motion of objects / joints as a path, then drag the keys ...
┌ Paths ──────────────────────────────┐   공용 리스트: Set Selected / Add / Del
│ ctrl                                │   담으면 바로 경로가 생긴다
│ j3                                  │
└─────────────────────────────────────┘
┌ Range ─ ( ) Playback ( ) Scene (o) Custom                          ┐
│  Start [ 1 ] [Get Current]  End [ 120 ] [Get Current] [Get Sel Range] │
┌ Display ─ [x] Frame dots [x] Keys [ ] Frame numbers     │
│   Line width [==|-----] 2   Dot size [===|---] 4   Key size [====|--] 9
┌ Edit ─ [   Edit Path   ] [Refresh]   (켜지면 Edit Path 가 연한 빨강) │
│   Drag in (o) View ( ) Ground ( ) X ( ) Y ( ) Z         │
│   2 key(s) selected                                     │
[Log]
```

뷰포트에 그려지는 것 (경로마다 다른 색, 메시에 가려지지 않는다):

| 그림 | 뜻 |
|------|----|
| 선 | 프레임마다 이은 궤적 (회전 피벗의 월드 위치 = 마야 Move 툴이 보여 주는 점) |
| 작은 점 | 프레임마다 하나 — **간격이 속도**다(촘촘하면 느림) |
| 흰 큰 점 | 키 |
| 주황 큰 점 | 선택된 키 |
| 빨간 점 | 현재 프레임 |
| (옵션) 숫자 | 키의 프레임 번호 |
| 회색 경로 | 편집할 수 없는 경로 (이유는 로그 — §4) |

---

## 2. 사용법

1. 씬에서 애니메이션된 **오브젝트 · 조인트**를 고르고 `Paths` 의 **Set Selected**(또는 Add). 경로가 바로 그려진다.
2. **Edit Path** 를 누르면 편집 툴이 되고 버튼이 **연한 빨강**이 된다. 다시 누르거나 `Q` · 다른 마야 툴로 나가면 버튼도 꺼진다.

   **두 단계로 한다 — 먼저 고르고, 그다음 고른 점을 잡고 끈다.**
   - 고르기: 키 점을 클릭하거나, 빈 곳에서 눌러 사각형을 그려(박스 선택) 여러 키를 고른다 → 고른 점이 주황색.
   - 끌기: **주황색 점 중 아무거나 하나 위에서**(반경 약 10 px) 왼쪽 버튼을 누른 채 움직인다 → 고른 키가 모두 함께 움직인다. 놓으면 확정.
     점이 아닌 빈 곳에서 누르고 끌면 이동이 아니라 새 박스 선택이 된다.

   | 입력 | 동작 |
   |------|------|
   | 키 클릭 | 그 키만 선택 (이미 선택된 키를 누르면 선택을 유지한 채 함께 끈다) |
   | Shift + 클릭 | 더하기 / 빼기 |
   | Ctrl + 클릭 | 빼기 |
   | 빈 곳 드래그 | 박스 선택 (Shift = 더하기, Ctrl = 빼기) · 빈 곳 클릭 = 선택 해제 |
   | **선택 키 드래그** | 이동 → 그 프레임의 translate 키 값이 바뀌고 오브젝트와 경로가 바로 따라온다 |
   | 드래그 중 오른쪽 버튼 | 취소 (원래대로) |
   | Alt + 드래그 | 마야 카메라 (편집과 무관) |

3. **Drag in** 으로 움직이는 평면을 고른다: **View**(화면과 평행, 기본) · **Ground**(수평면) · **X / Y / Z**(그 월드 축으로만).
4. 놓으면 **Ctrl+Z 한 번**에 그 드래그 전체가 되돌아간다.
- **Range** : Playback(타임 슬라이더 재생 범위) · Scene(애니메이션 시작/끝) · **Custom**. Custom 은 아래 줄에 시작 · 끝을 넣는다 —
  **Get Current** 는 그 칸을 현재 프레임으로, **Get Sel Range** 는 그래프 에디터 · 타임 슬라이더에서 고른 키의 처음 · 끝으로 두 칸을 함께 채운다
  (A00110 animTool 과 같은 공용 위젯). 범위가 실제로 바뀔 때만 경로를 다시 굽는다.
5. 그래프 에디터에서 키를 고치거나 undo 하면 경로가 따라 바뀐다.
   **부모 · 컨스트레인트 · 드라이버** 애니메이션을 바꿨으면 **Refresh** 를 누른다(§3).

---

## 2-1. 애니메이션 레이어 (v01.03~)

툴 창 **Animation Layer** 목록에 Base 와 씬의 레이어가 레이어 에디터 순서로 나온다. 하나를 고르면:

- 경로 위 **키 점 = 그 레이어의 키**. 끌면 **그 레이어의 커브만** 바뀐다(Base · 다른 레이어는 그대로).
- **경로 자체는 늘 모든 레이어를 합친 실제 움직임**이다(무엇을 고르든 같다). 놓은 키는 합친 결과가 정확히 그 자리에 오도록 그 레이어 값이 정해진다.
- 레이어를 만들거나 지웠으면 **Reload Layers**(또는 Refresh). 지워진 레이어를 고르고 있었으면 Base 로 돌아간다. 고른 레이어는 다음에도 기억한다.

| 로그 (회색 경로) | 이유 |
|---|---|
| `Not in the animation layer <L>` | 그 오브젝트가 그 레이어에 없다 — 레이어 에디터에서 넣거나 다른 레이어를 고른다 |
| `The animation layer <L> is locked` | 레이어 lock |
| `... has no effect here (muted, weight 0, or covered by an override layer above)` | 그 레이어를 바꿔도 결과가 안 바뀐다 |

어떻게 계산하나 (mayapy 실측): 레이어마다 translate 위에 `animBlendNodeAdditiveDL` 이 쌓이고 모두
`output = weightA × 아래 결과 + weightB × 그 레이어 값` 이다(additive: 1 · 가중치, override: 1−가중치 · 가중치, 뮤트: 1 · 0).
그래서 최종 translate 는 고른 레이어 값에 대한 1차식이고, 끈 위치로 정확히 역산된다. 레이어 가중치(뮤트 · 솔로 · 가중치 애니메이션)는
경로를 만들 때 함께 굽는다 — 가중치를 바꿨으면 **Refresh**.

- 그 레이어에 커브가 없던 축(예: override 레이어에 X 만 키가 있을 때의 Y)은 처음 움직일 때 그 레이어의 **원래 상수 값으로** 커브를 만든다 — 다른 프레임은 그대로.
- undo 는 한 번에 커브 · 레이어 커브 생성 · 실제 움직임까지 돌아간다(마야가 레이어 커브 삭제 뒤 다시 계산하지 않는 문제를 툴이 막는다 — §5).

---

## 3. 동작 (왜 빠른가)

경로의 점은

```
P(f) = (c + T(f)) · parentMatrix(f)
```

- `parentMatrix(f)` : 부모 · 컨스트레인트 · 드라이버 · offsetParentMatrix 를 모두 담은 행렬. **경로를 만들 때 한 번만** 프레임마다 구운다
  (그 plug 만 시간 문맥으로 평가 — 스킨 메시 · 다른 캐릭터는 계산하지 않고, 현재 시간 · 선택 · 포즈도 그대로).
- `T(f)` : 그 노드의 translate. **애님 커브를 직접 계산**한다 — 씬을 평가하지 않는다.
- `c` : rotatePivot + rotatePivotTranslate (조인트 · 피벗이 원점이면 0).

그래서 키를 끌 때는 씬을 다시 평가하지 않고 커브 계산 + 행렬 곱만 한다. 놓은 위치로의 역산도 정확하다(`T = W · parentMatrix⁻¹ − c`).

| 실측 (mayapy 2024, 1,000 프레임) | 이 툴 | 마야 Editable Motion Trail |
|---|---|---|
| 처음 만들기 (계층 · 무거운 리그) | 0.14 ~ 0.19초 | 0.15 ~ 0.18초 |
| 키 하나 바꾼 뒤 다시 그리기 | **0.002초** | 0.15 ~ 0.17초 |
| 드래그 중 마우스 한 번 | **3.4 ms** | (매번 위와 같은 재계산) |

처음 만들기는 둘 다 프레임마다 리그를 평가해야 해서 비슷하고, **편집할 때 약 70 ~ 90배** 빠르다.

- 부모 · 컨스트레인트 애니메이션이 바뀌면 구운 행렬이 낡는다 → **Refresh**(v01.00 은 수동, 자동은 계획서 2단계).
- 자기 회전 · 스케일 키를 바꾸는 것은 경로에 영향이 없다(회전 피벗은 회전 · 스케일과 무관) — Refresh 필요 없음.

---

## 4. 편집할 수 없는 경로 (회색)

| 로그 | 이유 |
|------|------|
| `Translate is driven by <node> (<type>) - edit that instead` | 컨스트레인트 · 표현식 · 다른 노드가 translate 를 구동 |
| `Translate goes through <node> - animation layers / blends are not supported yet` | 애니메이션 레이어 · pairBlend (계획서 3단계) |
| `Translate is locked` | 세 축 모두 lock |

한두 축만 lock 이면 그 축은 그대로 두고 나머지만 움직인다.

---

## 5. 알아 둘 것

- **부분 키**: 끈 키의 프레임에 다른 축 키가 없으면, 처음 움직일 때 그 축에 **모양을 지키며** 키를 넣는다(마야 `setKeyframe -insert`).
  키가 아예 없는 축은 기존 키 프레임마다 지금 값으로 커브를 만든다. 이것도 같은 undo 한 번에 포함된다. 끌기만 하고 안 움직이면 아무것도 안 바뀐다.
- **auto 탄젠트**: 마야 `auto` 탄젠트는 키 하나를 바꾸면 이웃 키의 탄젠트도 다시 계산한다(그래프 에디터와 같다). 그래서 앞뒤 키 사이 경로도 조금 바뀐다 — 화면은 늘 실제 결과다.
- **단위**: 내부 단위(cm)로 계산한다. 씬 단위가 m 여도 맞다(시험).
- **그리기 노드** `JUN_motionPath_*`: 아웃라이너에서 숨김, **씬에 저장되지 않고**(저장 직전에 잠깐 지워 플러그인 requires 줄도 남지 않는다) undo 큐에도 들어가지 않는다.
  창을 닫거나 새 씬 · 열기를 하면 지워진다. 툴 없이도 파일이 그대로 열린다.
- **소수 프레임 키**도 경로에 들어간다.
- **undo 뒤 다시 계산 (v01.03)**: 레이어에 새 커브를 만든 편집을 undo 하면 마야가 블렌드 체인 아래를 다시 계산하지 않아 오브젝트가 낡은 위치에 남았다
  (데이터는 맞는데 표시만 낡음, 시간을 옮겨도). 그래서 드래그 묶음 맨 앞에 표시 명령 `junMotionPathDirty` 를 넣어 undo · redo 끝에 대상과 블렌드 노드를 `dgdirty` 한다.
- 범위 밖 키는 그리지 않는다 — Range 를 Scene / Custom 으로.

---

## 6. 구조

| 파일 | 역할 |
|------|------|
| `app/core/anim_channels.py` | translate 세 축 ↔ 애님 커브 (상태 · 잠금 · 평가 · 키 합집합 · 키 맞추기) |
| `app/core/parent_space.py` | `parentMatrix` 굽기 (MDGContext.makeCurrent), 피벗 보정 `c` |
| `app/core/path_cache.py` | 경로 하나 (점 · 키 · solve · refresh / rebake) |
| `app/core/edit_session.py` | 드래그 한 번 (스냅샷 · 키 맞추기 · MAnimCurveChange 누적 · commit / cancel) |
| `app/core/path_manager.py` | 경로들 · 키 선택 · 그리기 데이터 · 설정 |
| `app/core/watcher.py` | 커브 편집 · undo/redo · 시간 · 저장 · 새 씬 콜백 |
| `app/core/picking.py` | 화면 투영 · 키 고르기 · 박스 · 드래그 평면 / 축 |
| `app/core/draw_nodes.py` · `draw_bridge.py` | 플러그인 로드 · 그리기 노드 (API, undo 밖, doNotWrite) · 툴 ↔ 플러그인 데이터 |
| `app/plugin/jun_motion_path.py` | 노드 `junMotionPath` + VP2 draw override + 명령 `junMotionPathSetKeys`(undo 한 번) |
| `app/ui/main_window.py` · `edit_context.py` | 툴 창 · 편집 컨텍스트(draggerContext) |

---

## 7. 검증

mayapy 2024 (`tests/`, `-u` 로 실행):

| 시험 | 항목 | 내용 |
|------|------|------|
| `bench_motion_path.py` | 실측 | 굽기 방법 비교 · 마야 Motion Trail 대비 (§3 표) |
| `test_path_math.py` | 19 | 경로 = 마야 `xform -ws -rp` (피벗 · OPM · 부분 키 · 컨스트레인트 아래 · 조인트 jointOrient/SSC/비균일 부모), solve 정확, 사용자 시간 · 선택 · 포즈 불변, 소수 프레임 키, 회전 · 스케일 편집 뒤 굽기 없이 맞음 |
| `test_anim_channels.py` | 15 | 상태 판정 · 레이어 잠금 · 평가 = 마야 · m 단위 · 키 맞추기가 모양을 지킴 |
| `test_edit_session.py` | 21 | 여러 번 움직여도 오차 없음 · 드래그 중 undo 큐 비어 있음 · **undo 한 번** · redo · 여러 키 · 여러 경로 · 부분 키 · 잠긴 축 · 취소 · 안 움직임 · auto 탄젠트 범위 · 속도(3.4 ms) |
| `test_watcher.py` | 20 | 다른 곳의 커브 편집 · undo 뒤 경로 · 소수 키 → 다시 굽기 · 선택 · 저장 파일에 노드/requires 없음 · 그리기 노드가 undo 큐 밖 · 새 씬 정리 |
| `test_layers.py` | 27 | (v01.03) 경로 = 레이어 합친 실제 움직임(Base · additive 가중치 애니 · override 0.5 · 뮤트 · lock · 부모 애니), 키 = 고른 레이어, 레이어 바꿀 때 굽지 않음, 레이어별 끌기 정확 · **그 레이어 커브만** 바뀜 · undo 한 번에 커브와 **실제 움직임** 복원, override 의 커브 없던 축, 잠금 이유 3종, 관리자 레이어 바꾸기 · 지운 레이어 → Base |
| `test_ui.py` | 35 | 오프스크린 창: 경로 추가/빼기 · 표시 옵션 → 그리기 데이터 · optionVar · 범위(Custom · Get Current · Get Sel Range · 같은 범위면 안 굽기) · 슬라이더 색 · Edit Path 빨강 · 툴 바뀌면 버튼 끔 · Refresh · 닫으면 정리 |
| `test_picking.py` | 13 | 투영 · 고르기 · 박스 · 카메라 뒤 · 평면 / 축 드래그 |
| `test_edit_context.py` | 19 | (v01.01) 편집 컨텍스트 전체 흐름 — 누름 → 끌기 → 놓기 · 축 고정 · 박스 선택 후 함께 끌기 · Shift / Ctrl · 빈 곳 클릭 해제 · 오른쪽 버튼 취소. 가짜 뷰의 `viewToWorld` 가 **마야 2024 와 같은 OUT 인자 모양**이라 v01.00 의 호출 실수를 잡는다 |

**마야 GUI 확인 (아직)** — 헤드리스로는 확인할 수 없는 것:
1. 경로 · 점 · 키가 보이고 메시에 가려지지 않는다 (x-ray 그리기).
2. Edit Path: 클릭 · Shift · Ctrl · 박스 선택, 드래그 → 오브젝트가 따라옴 → Ctrl+Z 한 번. 오른쪽 버튼 취소. Alt 카메라. Q 로 나가기.
3. 그래프 에디터에서 키를 고치면 경로가 따라온다(커브 편집 알림은 마야가 idle 에 보낸다 - 헤드리스에서는 안 온다).
4. 무거운 리그에서 마야 Editable Motion Trail 과 체감 비교.
5. 저장 → 툴 없이 다시 열기: 오류 · 남은 노드 없음.
