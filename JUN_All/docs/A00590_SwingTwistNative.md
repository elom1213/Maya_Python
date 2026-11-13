---
title: A00590_SwingTwistNative 사용법
aliases: [Swing Twist Native, SwingTwistNative, A00590]
tags: [maya-python, tool-guide, metahuman, swing-twist, quaternion, quatNodes]
updated: 2026-11-13
---

# A00590_SwingTwistNative 사용법

MetaHuman for Maya 의 **`SwingTwistEvaluatorNode`(Epic 플러그인)** 를 **마야에 동봉된 `quatNodes` 노드망**으로 대신 만드는
in-Maya PySide 툴(arch B). 원본과 **오일러 값까지 같은 결과**(골든 시험 최대 2e-13°)를 내므로, 에픽 플러그인 없이 같은 swing/twist 리그를 세운다.

- **버전**: `app/config/version.py` (v01.00)
- **설치**: `__dragDrop_A00590.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **SwTw** → `tools.A00590_SwingTwistNative.run(True)`
- **코어**: `Framework/core/maya_swing_twist.py` (UI 없음 — 스크립트에서 바로 쓸 수 있다)
- **계획서**: [`plans/A00590_SwingTwistNative_plan.md`](plans/A00590_SwingTwistNative_plan.md) (원본 사양 · 수식 · 노드망 · 다음 단계)

> v01.00 은 **새로 만들기(Build)** 만 한다. 씬에 이미 있는 `SwingTwistEvaluatorNode` 를 바꾸는 **Convert**,
> 노드망을 한 노드처럼 묶는 **Container** 는 다음 단계(계획서 §9 · §10).

## 1. Build 탭

MetaHuman `create_swing_twist_evaluator()` 와 같은 입력을 받는다.

| 칸 | 내용 |
|----|------|
| `Name` | 만들 노드 이름 앞부분. 비우면 Start 조인트 이름. 홀더는 `<Name>_SwingTwist` |
| `Start` | 입력 조인트(필수). `.rotate` 를 **XYZ 로** 읽는다 |
| `End` | 선택. **From End 가 켜졌을 때만** 쓰인다 |
| `Swing` + `Swing Blend` | 선택. 스윙 출력 조인트와 블렌드 |
| `From End` | 트위스트 출력이 시작 트위스트 상쇄 대신 **End 조인트의 X 트위스트**를 따른다 |
| `Twist Joints` 표 | 트위스트 출력 조인트 + 블렌드(행 순서 = `twists[0]`, `twists[1]` …). `Add Selected` · `Remove` · `Up` · `Down` · `Clear` |

각 줄의 `Set` 은 첫 번째 선택 오브젝트를 넣는다. `Build` 한 번 = **Ctrl+Z 한 번**에 전부 되돌아간다.

### 블렌드 — 직관과 반대

블렌드는 출력을 **완전한 역회전(0) → identity(1)** 로 민다(원본과 같다).

| 출력 | 0 | 1 |
|------|---|---|
| Twist | 시작 트위스트를 **상쇄**(From End 면 End 트위스트 **복사**) | 회전 0 |
| Swing | 시작 회전 **전체 상쇄** | 시작 **트위스트만** 상쇄 (0 이 아니다) |

0~1 밖 값은 외삽된다.

### Build 가 거절하는 경우 (로그 `[ERROR]`)

- Start 가 없음 · 출력(Swing/Twist)이 하나도 없음 · 없는 노드
- 같은 조인트를 출력 두 곳에 · 입력 조인트를 출력으로(순환)
- 출력 조인트 `rotate`(또는 rotateX/Y/Z)가 **이미 구동 중**(키 · 연결) — 먼저 끊는다
- 출력 조인트 rotate 채널이 잠김

경고 `[WARN]`: rotateOrder 가 XYZ 가 아닌 조인트(원본처럼 XYZ 로 읽고 쓴다), From End 없는 End 조인트 등.

## 2. Rigs 탭

씬에 만든 노드망(홀더) 목록 — `Holder · Start · Swing · Twists · From End · Nodes`. 행을 고르면 홀더가 선택된다.

| 버튼 | 하는 일 |
|------|---------|
| `Refresh` | 씬에서 다시 읽는다(탭을 열 때도 자동) |
| `Select Holder` | 홀더 선택 → **Channel Box 에서 `swingBlend` · `twistBlend[i]` 를 바로 고친다**(키도 된다) |
| `Select Nodes` | 노드망 전체 선택 |
| `Select Joints` | 입력 · 출력 조인트 선택 |
| `Load to Build` | 설정을 Build 탭으로 복사(고쳐서 다시 만들 때 — 옛 망을 먼저 Delete) |
| `Delete` | 노드망 + 홀더 삭제(확인 창, Ctrl+Z 한 번). 출력 조인트는 마지막 회전값에 남는다 |

## 3. 원본과 같은 점 · 다른 점

**같은 점** — 트위스트 축 X 고정, 오일러는 항상 XYZ(rotateOrder 무시), jointOrient 무시(`.rotate` 만), 블렌드 의미 · 외삽,
특이 입력(Y/Z 180° 등) 처리까지 같다.

**다른 점**
- 노드 하나가 아니라 망이다: 평가기 하나당 **8 + 트위스트당 2**(From End + End 조인트면 +2, 스윙 없으면 스윙 가지 5개 생략).
  블렌드는 홀더 `<Name>_SwingTwist`(network 노드) 하나에서 고친다.
- `fromEnd` 는 **빌드 때 구조로 정해진다** — 홀더의 `fromEnd` 는 정보용. 바꾸려면 Load to Build → Delete → Build.
- 씬 파일에 `requires "quatNodes"` 가 생긴다(마야 동봉 플러그인, 별도 설치 없음). `SwingTwistEvaluatorPlugin` 은 필요 없다.
- ★ **MetaHuman Pose Editor 의 DNA 내보내기는 `SwingTwistEvaluatorNode` 를 찾는다** — 이 툴로 만든 망은 내보내기에 들어가지 않는다.
  DNA 로 내보내야 하는 리그면 원본 노드를 쓴다(되돌리는 Restore 는 다음 단계 §9).

## 4. 스크립트에서

```python
from Framework.core import maya_swing_twist as ST

holder = ST.build("upperarm_l", "upperarm_l", None, "upperarm_swing_l", 0.0,
                  ["upperarm_twist_01_l", "upperarm_twist_02_l"], [0.33, 0.66], from_end=False)
ST.set_twist_blend(holder, 1, 0.5)
ST.read_holder(holder)     # build() 인자 모양 dict
ST.delete_rig(holder)
```

## 5. 시험 (mayapy)

| 파일 | 내용 |
|------|------|
| `tests/test_swing_twist_golden.py [samples]` | 원본 플러그인과 나란히 — 무작위 1500 × 6 구성 + 특이 입력 22 × 2. 오일러 · 행렬 1e-9 기준, 실측 최대 2.1e-13° · 3.8e-15 (16/16) |
| `tests/test_swing_twist_tool.py` | 입력 검사 · 홀더 · 블렌드 의미 · undo/redo · 저장 후 다시 열기 · 삭제 · UI 오프스크린 (46/46) |

GUI(실제 마야 창) 확인은 아직.
