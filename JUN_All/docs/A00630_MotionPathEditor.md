---
title: A00630_MotionPathEditor 사용법
aliases: [A00630, Motion Path Editor, MotionPathEditor, 모션 경로 편집, editable motion path, motion trail 대체]
tags: [maya-python, tool-guide, animation, motion-path, motion-trail, viewport-draw]
updated: 2026-11-20
---

# A00630_MotionPathEditor 사용법

오브젝트 · 조인트가 **프레임마다 어디에 있는지를 뷰포트에 경로로 그리고**, 경로 위의 **키 점을 끌어 애니메이션을 고치는** in-Maya PySide 툴(arch B).
그래프 에디터를 열지 않고 궤적 모양을 보면서 위치 애니메이션을 고친다.

- **버전**: `app/config/version.py` (v01.15 — **Edit 묶음을 Speed 탭 맨 아래로**(Path 탭 = Range · Layer · Display) · v01.14 — 매니퓰레이터 호버(마우스를 올린 부분이 굵어짐) · v01.13 — Path 탭 `Drag in` 줄 숨김(매니퓰레이터가 대신) · v01.12 — **Speed 탭 Edit Path · 그래프 폴오프 [a, b] 띠 · Frames > Falloff · 폴오프 범위 위치 Smooth** · 기즈모 1.5배 굵게 · v01.11 — **이동 · 회전 매니퓰레이터**(w / e) · 놓기 4배 빠름 · v01.10 — **프레임 점 · 폴오프 끌기** · 선이 메시에 안 가리게 화면 2D 로 · v01.09 — **프레임 점 고르기 + 폴오프**(b 톡 = 켜기/끄기, b + 끌기 = 반경, 가중치 색) · v01.08 — **Acceleration 그래프 스무딩**(브러시 Smooth Acceleration) · v01.07 — 마야에 남은 옛 플러그인 때문에 키 끌기가 `junMotionPathDirty` 에러로 실패하던 것 수정 · v01.06 — Speed 탭 Frames 에 **Custom**(Start / End / Get Sel Range 로 그 구간만 그래프) · v01.05 — 그래프 스크럽이 undo 큐에 쌓여 Ctrl+Z 가 획을 못 되돌리던 것 수정 · 그래프 키 선 끌기(키 시간 이동) 없앰 · v01.04 — **Speed 탭: 속도 그래프 + Smooth 브러시 · 속도 끌기**(§2-2) · v01.03 — **애니메이션 레이어**: 고른 레이어의 키만 끌어 고친다(경로는 합친 움직임) · v01.02 — Edit Path 를 켜도 버튼이 연한 빨강이 안 되던 것 수정 · v01.01 — 키 드래그 에러 수정 · Custom 범위에 Get Current / Get Sel Range · Edit Path 켜짐 = 연한 빨강 · v01.00 — 첫 버전: 위치 경로 표시 + 키 드래그)
- **설치**: `__dragDrop_A00630.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **MPath** → `tools.A00630_MotionPathEditor.run(True)`.
  툴 런처(A00370) ANIM 프로파일에도 **MotionPath** 버튼이 있다.
- **계획서**: [plans/A00630_MotionPathEditor_plan.md](plans/A00630_MotionPathEditor_plan.md) — 단계별 계획 · 0단계 실측 결과 · 다음 단계
  · 속도 그래프: [plans/A00630_MotionPathEditor_speed_graph_plan.md](plans/A00630_MotionPathEditor_speed_graph_plan.md) — 진단 · G0 실측 · 설계
  · 매니퓰레이터 · 폴오프 (계획, 구현 전): [plans/A00630_MotionPathEditor_manipulator_falloff_plan.md](plans/A00630_MotionPathEditor_manipulator_falloff_plan.md)
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
[ Path ] [ Speed ]                         ← v01.04 탭 (Speed = §2-2)
┌ Range ─ ( ) Playback ( ) Scene (o) Custom                          ┐
│  Start [ 1 ] [Get Current]  End [ 120 ] [Get Current] [Get Sel Range] │
┌ Display ─ [x] Frame dots [x] Keys [ ] Frame numbers     │
│   Line width [==|-----] 2   Dot size [===|---] 4   Key size [====|--] 9
┌ Edit ─ [   Edit Path   ] [Refresh]   (켜지면 Edit Path 가 연한 빨강) │
│   Manipulator (o) Move ( ) Rotate   Axes (o) World ( ) Path │   ← v01.11
│   [x] Falloff  Radius [ 8.0 fr] [Curve...]              │   ← v01.09
│   3 point(s) selected - falloff [36, 54]                │
[Log]
```

뷰포트에 그려지는 것 (경로마다 다른 색, 메시에 가려지지 않는다):

| 그림 | 뜻 |
|------|----|
| 선 | 프레임마다 이은 궤적 (회전 피벗의 월드 위치 = 마야 Move 툴이 보여 주는 점) |
| 작은 점 | 프레임마다 하나 — **간격이 속도**다(촘촘하면 느림) |
| 흰 큰 점 | 키 |
| 주황 큰 점 | 선택된 키 (작은 주황 = 선택된 프레임 점, v01.09) |
| 노랑 → 주황 → 빨강 점 · 굵은 선 | 폴오프 범위 — 고른 점(노랑)에서 멀어질수록 빨강 (v01.09) |
| 빨간 점 | 현재 프레임 |
| (옵션) 숫자 | 키의 프레임 번호 |
| 회색 경로 | 편집할 수 없는 경로 (이유는 로그 — §4) |

---

## 2. 사용법

1. 씬에서 애니메이션된 **오브젝트 · 조인트**를 고르고 `Paths` 의 **Set Selected**(또는 Add). 경로가 바로 그려진다.
2. **Edit Path**(v01.15 부터 **Speed 탭 맨 아래** Edit 묶음 - Manipulator · Falloff 도 함께) 를 누르면 편집 툴이 되고 버튼이 **연한 빨강**이 된다. 다시 누르거나 `Q` · 다른 마야 툴로 나가면 버튼도 꺼진다.

   **두 단계로 한다 — 먼저 고르고, 그다음 고른 점을 잡고 끈다.**
   - 고르기: 키 점 · **프레임 점**(v01.09)을 클릭하거나, 빈 곳에서 눌러 사각형을 그려(박스 선택) 여러 점을 고른다 → 고른 점이 주황색.
     같은 자리면 키가 먼저 골라진다. `Frame dots` 를 끄면 프레임 점은 고르지 않는다.
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
   | **매니퓰레이터** (v01.11) | 고른 점들의 가운데에 나온다. 화살표 / 평면 / 가운데 = 이동, 고리 = 회전. 점보다 먼저 잡힌다 |
   | **`w` / `e`** (v01.11) | 매니퓰레이터 Move / Rotate (편집 툴일 때만 - 마야 툴로 안 나간다) |
   | **`b` 톡** (v01.09) | 폴오프 켜기 / 끄기 |
   | **`b` 누른 채 좌우 끌기** (v01.09) | 폴오프 반경 (1 px = 0.1 프레임, 커서 옆에 숫자). `Ctrl+Shift` + 끌기도 같다 |
   | Alt + 드래그 | 마야 카메라 (편집과 무관) |

3. **Falloff** (v01.09): 고른 점 둘레의 점들이 가중치만큼 함께 움직이게 할 범위. **Radius 는 프레임**(경로를 따라 잰 거리 —
   경로가 고리 · 왕복이어도 시간이 먼 점은 안 들어온다), **Curve...** 는 가중치 모양(공용 falloff 커브, 기본 Smooth). 범위의 점 · 선이 가중치 색이 된다.
   `b` 는 편집 툴이 켜져 있을 때만 툴이 받는다 — 마야 소프트 셀렉션 설정은 그대로다.
   **끌기 (v01.10)**: 프레임 점을 골랐거나 폴오프가 켜져 있으면 고른 점 = 1, 둘레는 가중치만큼 함께 움직인다. 끄는 동안은 미리보기(원래 경로 회색 점선 + 새 경로),
   **놓을 때 키에 쓴다**(Speed 탭과 같은 refit — 키 프레임 유지, 허용 오차를 넘는 곳만 키 추가, 범위 밖 그대로). 경로 여럿도 Ctrl+Z 한 번.
   키만 고르고 폴오프를 끄면 예전처럼 끄는 동안 오브젝트가 바로 따라온다. 성긴 키 커브에서 크게 움직이면 키가 늘 수 있다(로그에 수).
4. **Manipulator** (v01.11): `Move` = 축 화살표(그 축으로만) · 평면 사각형(그 평면에서) · 가운데 사각형(아래 Drag in 대로),
   `Rotate` = 축 고리 · 바깥 화면 고리(피벗 = 고른 점들의 가운데, 폴오프 범위는 각도 x 가중치). `Axes` World / Path(고른 점 자리의 경로 방향 · 위 · 옆).
   마우스를 올리면 그 부분이 굵어진다(v01.14, 잡을 곳 표시). 기즈모는 화면 크기 고정이고 메시에 안 가린다. 고른 점 위를 누르면 가운데 사각형이 잡힌다(= 예전처럼 점 끌기).
5. (v01.13 부터 이 줄은 숨김 — 점 · 가운데 사각형 끌기는 View. 축 · 평면 고정은 매니퓰레이터로) **Drag in** 으로 움직이는 평면을 고른다: **View**(화면과 평행, 기본) · **Ground**(수평면) · **X / Y / Z**(그 월드 축으로만).
6. 놓으면 **Ctrl+Z 한 번**에 그 드래그 전체가 되돌아간다.
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

## 2-2. Speed 탭 — 속도 그래프 · Smooth (v01.04~)

```
Path [ bumpy            ▾]                     [ Edit Path ]  [Pop Out]   ← Edit Path v01.12 (Path 탭과 같은 툴)
Show (o) Speed ( ) Position ( ) Acceleration                 [per frame ▾]
Frames (o) Whole Path ( ) Selected Keys ( ) Around Current ( ) Custom ( ) Falloff   ← Falloff v01.12
Start [  1 ][Get Current]  End [ 120 ][Get Current]  [Get Sel Range]     ← Custom 일 때만 (v01.06)
┌ Speed (cm/frame) ─────────────────────────── Radius 8  Strength 0.50 ┐
│      |20        |35   |45          |60   |70         (키 선 + 번호) │
│  ╱‾‾╲__╱‾‾‾╲__        (회색 = 칠하기 전, 색 = 새 곡선)             │
│ ▔▔▔▔▔▔▔▔ (브러시 띠: 반경 · 세기)          초록 세로선 = 현재 프레임 │
└──────────────────────────────────────────────────────────────────────┘
Brush [Smooth Speed ▾]  Radius [ 8.0 fr]  Strength [====|---] 0.50
[ ] Whole Pose   Tolerance [0.10 %]                      [Smooth Range]
```

그래프의 가로는 프레임, 세로는 **Speed** = 프레임마다 경로를 따라 움직인 거리(속도, 기본) · **Position** = 월드 X/Y/Z(빨강 · 초록 · 파랑, 읽기 전용) ·
**Acceleration** = 속도가 얼마나 바뀌나(튀는 곳 · 떨림이 솟는다). **Path** 콤보의 경로가 편집 대상이고 다른 경로는 흐리게 함께 그린다.
Frames: **Whole Path** · **Selected Keys**(선택 키 사이, 하나면 양쪽 구간) · **Around Current**(현재 프레임 앞뒤 키) ·
**Custom**(v01.06) — **[Start, End] 구간만** 그래프로. Start · End 칸, Get Current(현재 프레임), **Get Sel Range**(그래프 에디터 · 타임 슬라이더에서 고른 키의 첫 · 끝 프레임)
은 Path 탭 Range 와 같은 공용 위젯이다. 경로 범위를 넘는 부분은 잘라 보이고, 경로와 전혀 안 겹치면 그래프 자리에 그렇다고 쓴다. 값은 기억된다.
Smooth Range 도 이 구간에 칠한다(브러시 반경만큼 구간 끝 바깥도 조금 함께 고르게 된다 — 다른 Frames 모드와 같다).

| 그래프 위에서 | 동작 |
|---|---|
| **오른쪽 드래그** | **Smooth 브러시** — 지나간 곳을 부드럽게. 휠 = 반경, Shift+휠 = 세기 |
| 왼쪽 · **곡선** 잡고 위 / 아래 | 그곳을 **빠르게 / 느리게** (끄는 중 휠 = Reach, 가장자리가 보상해 범위 밖은 그대로) — Speed 모드 |
| 왼쪽 · 곡선 밖 (키 선 위 포함) | 현재 프레임 스크럽 (undo 큐에 안 쌓인다 - v01.05). 키 시간 이동은 v01.05 에서 없앴다 — 그래프 에디터로 |
| Esc / 끄는 중 반대 버튼 | 그 드래그 취소 |

**Brush** 두 가지:

- **Smooth Speed** (원본 애드온의 그래프 Smooth) — **경로 모양은 그대로** 두고 **타이밍만** 고른다. 키는 프레임을 지키고 포즈가 경로를 따라 미끄러진다.
  브러시 밖의 움직임은 그대로, **정지(hold)는 같은 자리에서 정지**로 남는다. 경로 위 프레임 점 간격이 고르게 되는 것이 눈에 보인다.
- **Smooth Shape** — **경로 자체의** 울퉁불퉁함(짧은 파장)을 줄인다. 큰 호는 오그라들지 않게(Taubin 평활). Acceleration 모드로 보면서 칠하면 좋다.
- **Smooth Acceleration** (v01.08) — **가속도**를 고르게: 점들을 시간 축으로 평균 쪽으로 당긴다. 튐 · 떨림 · 꺾인 곳이 둥글어지고 모양과 타이밍이 함께 바뀐다.
  Show 를 **Acceleration** 으로 바꾸면 이 브러시가 저절로 골라진다(나오면 그 전 브러시로). Acceleration 그래프를 볼 때 Smooth Speed 는 쓰지 말 것 —
  꺾인 곳을 더 빨리 지나가게 해 가속도를 키울 수 있다. 키로 다시 맞출 때 허용 오차를 1/5 로 엄격히 해서 키가 조금 더 들어간다.

- **획 하나 = Ctrl+Z 하나.** 칠하는 동안은 미리보기만(뷰포트: 원래 경로 회색 점선 + 새 프레임 점, 그래프: 원래 곡선 회색), 놓을 때 커브에 쓴다.
- 여러 번 칠해도 흘러가지 않는다 — 새 점은 늘 **처음 경로 위**에서 계산한다(세션). 그래프 에디터에서 고치거나 undo 하면 다음 획은 그 상태에서 새로 시작한다.
- **Whole Pose**: 속도 획이 rotate · scale 키도 **같은 시간 변화**로 옮긴다. 끄면(기본, 원본과 같음) 위치만 바뀌어 손은 일찍 도착하는데 손목은 원래 시간에 돈다.
- **Tolerance %**: 키가 획을 얼마나 정확히 따라갈지(경로 크기 대비, 기본 0.1%). 작게 하면 정확하지만 키가 더 생긴다. 로그에 축마다 남은 오차와 넣은 키 수가 나온다.
  매 프레임 키(모캡)는 값만 바꾸므로 늘 정확하고 키도 늘지 않는다.
- **Smooth Range**: 그래프에 보이는 구간 전체를 브러시 설정으로 한 번(undo 하나).
  **(v01.12) Edit Path 에서 점을 골라 두었으면 그 폴오프 범위만, 가중치만큼 위치를 스무딩한다** — 그래프 배경의 색 띠가 그 범위 · 세기다(뷰포트 폴오프 색과 같다).
  브러시 Smooth Shape / Smooth Acceleration 결과를 가중치로 섞는다(범위 밖은 그대로). Smooth Speed 면 위치가 아니라 타이밍 브러시라 Smooth Shape 로 대신한다.
- **Edit Path (v01.12)**: Path 탭의 Edit Path 와 같은 편집 툴. Speed 탭에서 켜고 뷰포트에서 점 · 폴오프 · 매니퓰레이터로 끌면 그래프가 **끄는 동안 따라 바뀐다**.
  고른 점의 폴오프 범위 [a, b] 는 그래프에 가중치 색 띠로, Frames > **Falloff** 는 그 범위만 보여 준다.
- **Pop Out**: 그래프를 따로 띄워 넓게(두 번째 모니터). 다시 누르거나 닫으면 탭으로 돌아온다.

키를 어떻게 고치나 (refit): 키의 **프레임은 그대로** 두고 값 = 목표, 탄젠트 = 목표에 가장 잘 맞는 기울기(최소제곱)로 바꾸고, 그래도 허용치를 넘는 곳에만 키를 넣는다.
바뀐 키와 그 구간 양 끝 키의 탄젠트는 **fixed** 가 된다(auto · spline 은 값이 바뀌면 마야가 이웃까지 다시 계산한다). 안 바뀐 구간 쪽 탄젠트는 원래 그대로
(그래서 정지 경계의 flat 이 남는다 — 그 키의 탄젠트 묶음이 풀릴 수 있다).

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
- **플러그인 교체 (v01.07)**: 마야는 한 번 읽은 플러그인(`jun_motion_path`)을 툴을 새로 고쳐도 다시 읽지 않는다. 툴 창을 열 때 플러그인 버전을 비교해
  옛것이면 바꿔 읽는다(로그 `Replaced the old Motion Path plugin`). 버전은 읽힌 코드에 명령 `junMotionPathVersion` 으로 묻는다 — `pluginInfo -version` 은 같은 경로에서 다시 읽어도 처음 값을 돌려준다. 이때 마야가 거부하면 **undo 큐를 한 번 비운다** — 그 전 작업은 Ctrl+Z 로 못 되돌린다.
  그래도 실패하면 마야를 다시 켠다. (v01.06 이전 툴로 열린 마야에서 키를 끌면 `no attribute 'junMotionPathDirty'` 에러가 났다.)

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
| `app/core/gizmo.py` | (v01.11) 매니퓰레이터 모양 · 고르기 · 끌기 수학(화면 크기 고정, 축 / 평면 / 고리, 가중 회전, Path 축) - 컨텍스트와 플러그인이 같은 모양을 쓴다 |
| `app/core/falloff.py` | (v01.09) 폴오프 가중치(경로를 따라 잰 프레임 거리 · 공용 falloff 커브) · 구간 · 색표 · 색 선 조각 (마야 비의존) |
| `app/core/draw_nodes.py` · `draw_bridge.py` | 플러그인 로드 · 그리기 노드 (API, undo 밖, doNotWrite) · 툴 ↔ 플러그인 데이터 |
| `app/plugin/jun_motion_path.py` | 노드 `junMotionPath` + VP2 draw override + 명령 `junMotionPathSetKeys`(undo 한 번) |
| `app/ui/main_window.py` · `edit_context.py` | 툴 창 · 편집 컨텍스트(draggerContext) |
| `app/core/arc_length.py` | (v01.04) 호 길이 · 속도 · 가속도 · 위치 (numpy, 마야 비의존) |
| `app/core/retime.py` | (v01.04) 속도 Smooth · 속도 바꾸기(시간 왜곡, 모양 유지 · 보존 · 정지) · 모양 Smooth(Taubin) (마야 비의존) |
| `app/core/refit.py` | (v01.04) 마야 커브 수학(골든) · 목표 → 키 값 · 기울기 최소제곱 · 키 추가 · 쓰기 |
| `app/core/speed_session.py` | (v01.04) 획 세션(원래 경로 · 미리보기 · 차이만 쓰기 · undo 하나) |
| `app/ui/speed_graph.py` | (v01.04) 그래프 위젯(QPainter) · Speed 탭 패널 |

---

## 7. 검증

mayapy 2024 (`tests/`, `-u` 로 실행):

| 시험 | 항목 | 내용 |
|------|------|------|
| `bench_motion_path.py` | 실측 | 굽기 방법 비교 · 마야 Motion Trail 대비 (§3 표) |
| `test_path_math.py` | 19 | 경로 = 마야 `xform -ws -rp` (피벗 · OPM · 부분 키 · 컨스트레인트 아래 · 조인트 jointOrient/SSC/비균일 부모), solve 정확, 사용자 시간 · 선택 · 포즈 불변, 소수 프레임 키, 회전 · 스케일 편집 뒤 굽기 없이 맞음 |
| `test_anim_channels.py` | 15 | 상태 판정 · 레이어 잠금 · 평가 = 마야 · m 단위 · 키 맞추기가 모양을 지킴 |
| `test_edit_session.py` | 21 | 여러 번 움직여도 오차 없음 · 드래그 중 undo 큐 비어 있음 · **undo 한 번** · redo · 여러 키 · 여러 경로 · 부분 키 · 잠긴 축 · 취소 · 안 움직임 · auto 탄젠트 범위 · 속도(3.4 ms) |
| `test_plugin_reload.py` | 12 | (v01.07) **같은 경로**의 옛 플러그인(1.0, Dirty · 버전 명령 없음)으로 사용자 에러 재현 → 새 내용으로 바꾸고 툴 창 열기 = 교체(그리기 노드 · undo 큐에 옛 명령이 있어도) · pluginInfo 버전 이름표는 낡은 채(그래서 버전 명령) · 로그 한 번 · 다시 열면 그대로 · 끌기 · undo 한 번 · 반쯤 만든 창 닫기 |
| `test_watcher.py` | 20 | 다른 곳의 커브 편집 · undo 뒤 경로 · 소수 키 → 다시 굽기 · 선택 · 저장 파일에 노드/requires 없음 · 그리기 노드가 undo 큐 밖 · 새 씬 정리 |
| `test_layers.py` | 27 | (v01.03) 경로 = 레이어 합친 실제 움직임(Base · additive 가중치 애니 · override 0.5 · 뮤트 · lock · 부모 애니), 키 = 고른 레이어, 레이어 바꿀 때 굽지 않음, 레이어별 끌기 정확 · **그 레이어 커브만** 바뀜 · undo 한 번에 커브와 **실제 움직임** 복원, override 의 커브 없던 축, 잠금 이유 3종, 관리자 레이어 바꾸기 · 지운 레이어 → Base |
| `test_ui.py` | 35 | 오프스크린 창: 경로 추가/빼기 · 표시 옵션 → 그리기 데이터 · optionVar · 범위(Custom · Get Current · Get Sel Range · 같은 범위면 안 굽기) · 슬라이더 색 · Edit Path 빨강 · 툴 바뀌면 버튼 끔 · Refresh · 닫으면 정리 |
| `test_picking.py` | 13 | 투영 · 고르기 · 박스 · 카메라 뒤 · 평면 / 축 드래그 |
| `test_speed_engine.py` | 40 | (v01.04) 속도 · 가속도 · dab 보존 · τ 단조 · 모양 유지 · 정지 유지 · 속도 바꾸기 · Taubin, **마야 커브 골든**(24/30/60 fps · cm/m · 가중/비가중 < 1e-11) · refit(같은 목표 = 안 바꿈, 키 추가, 끝 밖 불변, 쓰기 = 마야, undo, 가중 커브, 매 프레임 키, 첫 키 앞 앵커) |
| `test_speed_session.py` | 49 | (v01.04) 칠하는 동안 커브 · undo 큐 불변 → 놓으면 쓰기 · **원래 경로 위**(< 0.2%) · 브러시 밖 불변 · 키 프레임 유지 · 속도 고르게 · 두 번째 획 / 여러 획 흘러가지 않음 · **획마다 undo 하나** · 바깥 undo 감지 · 취소 · 정지 유지 · 회전하는 부모 · 레이어(Base 불변) · Whole Pose(회전 = 옛 회전(τ)) · 모양 Smooth · 속도 바꾸기 · (v01.08) 가속도 Smooth(최대 · 평균 절반 이하 · 미리보기 = 쓴 결과 · 밖 불변 · undo) · 잠긴 경로 |
| `test_speed_graph_ui.py` | 60 | (v01.04) 오프스크린 Speed 탭: 모드 · 단위 · 범위 3종 · (v01.06) Custom 범위(켜고 끔 · 구간만 · 기억 · 경로 끝 자르기 · 경로 밖 안내 · Get Sel Range) · 휠 반경/세기 · 스크럽 · **오른쪽 드래그 획**(미리보기 → 놓으면 쓰기 → undo 하나) · (v01.05) 획 → 스크럽 → **undo 한 번에 획 · 그래프 복귀**, 스크럽은 큐 밖, redo · Esc 취소 · Smooth Range · 곡선 끌기 = 빠르게 · 키 선 위 드래그 = 스크럽(키 불변) · Shape 브러시 · (v01.08) Acceleration 보기 = 가속도 브러시 저절로 · 칠하면 가속도 절반 이하 · 나오면 브러시 복귀 · Pop Out / Dock · 닫으면 정리 |
| `bench_speed_graph.py` | 실측 | (v01.04) 조밀 경로 보간 vs 서브프레임 굽기(차이 0.03%, 80배 빠름) · dab 0.1~0.5 ms · 놓기(refit + 쓰기) 5~10 ms, 매 프레임 키 1,000 개 146 ms |
| `test_speed_falloff.py` | 19 | (v01.12) 두 Edit Path 버튼 같은 상태 · 그래프 폴오프 띠(가중치 · 끄면 고른 프레임만 · 없으면 없음) · Frames > Falloff · 뷰포트 미리보기 → 그래프 라이브 · 폴오프 Smooth Range(범위 밖 그대로 · 가속도 감소 · 가중치 · undo 한 번 · Speed 브러시 → Shape · 선택 없으면 예전) |
| `test_gizmo.py` | 46 | (v01.11) 원근 카메라: 시선 방향 · 화살표 / 가운데 / 평면 / 빈 곳 고르기 · 화면 크기 고정 · 축 / 평면 이동 · 고리 3개 각도 · 가중 회전 · Path 축, 컨텍스트(화살표 끌기 · 키만 = 예전 끌기 · 폴오프 회전 · 각도 글자 · 미리보기 · 취소 · Shift = 점 · 가운데 = Drag in · 툴 끄면 사라짐), w/e 필터, 플러그인 그리기, 창 라디오 |
| `test_deform_drag.py` | 30 | (v01.10) deform 세션 · 프레임 점 끌기 · 폴오프 끌기(가중치대로 · 범위 밖 불변) · 키+폴오프 = deform · 키만 = 예전 끌기 · 끄는 동안 미리보기만 · 오른쪽 취소 · 안 움직인 클릭 = 안 씀 · 축 고정 · 경로 둘 undo 한 번 · 레이어 · 화면 2D 선 조각(카메라 뒤 끊기) |
| `test_falloff.py` | 58 | (v01.09) 가중치(선형 반값 · 대칭 · 두 점 = 가까운 쪽 · 반경 0 · 소수) · 구간 · 색표 · 색 선 조각 · 커브 저장, 프레임 점 고르기 · 선택 정리 · 그리기 데이터 · 플러그인 1.6, 컨텍스트(프레임 점 클릭 · 키 우선 · 박스 · 끌면 안내 · b 톡 · b 끌기 반경 · Ctrl+Shift 끌기 · 나가면 정리), **진짜 Qt 키 이벤트로 b 필터**(ShortcutOverride 먹음 · 반복 무시 · Ctrl+B · 다른 툴이면 통과), 창(Falloff 줄 · 저장 · 범위 표시 · 커브 팝업) |
| `test_edit_context.py` | 19 | (v01.01) 편집 컨텍스트 전체 흐름 — 누름 → 끌기 → 놓기 · 축 고정 · 박스 선택 후 함께 끌기 · Shift / Ctrl · 빈 곳 클릭 해제 · 오른쪽 버튼 취소. 가짜 뷰의 `viewToWorld` 가 **마야 2024 와 같은 OUT 인자 모양**이라 v01.00 의 호출 실수를 잡는다 |

**마야 GUI 확인 (아직)** — 헤드리스로는 확인할 수 없는 것:
1. 경로 · 점 · 키가 보이고 메시에 가려지지 않는다 (x-ray 그리기).
2. Edit Path: 클릭 · Shift · Ctrl · 박스 선택, 드래그 → 오브젝트가 따라옴 → Ctrl+Z 한 번. 오른쪽 버튼 취소. Alt 카메라. Q 로 나가기.
3. 그래프 에디터에서 키를 고치면 경로가 따라온다(커브 편집 알림은 마야가 idle 에 보낸다 - 헤드리스에서는 안 온다).
4. 무거운 리그에서 마야 Editable Motion Trail 과 체감 비교.
5. 저장 → 툴 없이 다시 열기: 오류 · 남은 노드 없음.
6. (v01.04) Speed 탭: 그래프 위 오른쪽 드래그 중 뷰포트에 회색 점선(원래 경로) + 새 프레임 점이 보이고, 놓으면 오브젝트가 따라온다 · Ctrl+Z 한 번.
   그래프에 키보드 포커스가 있을 때 Esc 취소, 휠 · Shift+휠, Pop Out 창.
7. (v01.09~10) 프레임 점 클릭 · 박스, 폴오프 색(점 · 굵은 선)과 **경로 선이 메시에 안 가린다**(v01.10 2D 선), 폴오프 끌기 미리보기 → 놓으면 오브젝트가 따라옴 · Ctrl+Z 한 번, `b` 톡 · `b` + 끌기 반경 · 커서 옆 숫자, 그동안 마야 소프트 셀렉션 그대로.
8. (v01.11) 매니퓰레이터가 화면 크기로 보이고 메시에 안 가린다, 화살표 · 평면 · 가운데 · 고리 끌기, w / e 로 바뀌고 마야 툴로 안 나간다.
9. (v01.12) Speed 탭 Edit Path 로 켜고 뷰포트에서 끌 때 그래프가 따라오는지, 그래프 폴오프 색 띠 · Frames Falloff · 폴오프 Smooth Range 결과, 기즈모 굵기.
