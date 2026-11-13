---
title: A00590_SwingTwistNative 사용법
aliases: [Swing Twist Native, SwingTwistNative, A00590]
tags: [maya-python, tool-guide, metahuman, swing-twist, quaternion, quatNodes]
updated: 2026-11-13
---

# A00590_SwingTwistNative 사용법

MetaHuman for Maya 의 **`SwingTwistEvaluatorNode`(Epic 플러그인)** 를 **마야에 동봉된 `quatNodes` 노드망**으로 대신 만드는
in-Maya PySide 툴(arch B). 원본과 **오일러 값까지 같은 결과**(골든 시험 최대 2e-13°)를 내므로, 에픽 플러그인 없이 같은 swing/twist 리그를 세운다.

- **버전**: `app/config/version.py` (v01.01)
- **설치**: `__dragDrop_A00590.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **SwTw** → `tools.A00590_SwingTwistNative.run(True)`
- **코어**: `Framework/core/maya_swing_twist.py` (UI 없음 — 스크립트에서 바로 쓸 수 있다)
- **계획서**: [`plans/A00590_SwingTwistNative_plan.md`](plans/A00590_SwingTwistNative_plan.md) (원본 사양 · 수식 · 노드망 · 다음 단계)

탭은 셋 — **Build**(새로 만들기) · **Convert**(씬의 원본 노드를 망으로 바꾸기) · **Rigs**(만든 망 관리 · container · 원본으로 되돌리기).

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
`Wrap in Container`(기본 켬)면 만든 망을 container 하나로 묶는다(§3).

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

## 2. Convert 탭

씬에 이미 있는 원본 `SwingTwistEvaluatorNode` 를 같은 결과의 노드망으로 바꾼다. 원본 플러그인이 로드돼 있어야 목록에 나온다
(위쪽 상태 줄 · `Load Plugin` — MetaHumanForMaya 모듈 경로 → 기본 설치 위치 순으로 찾는다).

목록 `Node · Start · Swing · Twists · From End · Note`. `Note` 에 변환할 수 없는 이유(레퍼런스 노드 등)가 나온다.

| 버튼 · 옵션 | 하는 일 |
|------|---------|
| `Convert Selected` / `Convert All` | 노드마다: 설정 읽기 → 망 생성 → **원본과 수치 대조** → 원본 삭제 → 같은 조인트 `.rotate` 에 망 출력 연결. 노드마다 **Ctrl+Z 한 번** |
| `Verify (20 random poses)` | 켜면 지금 포즈 + 무작위 20 포즈로 대조(입력 조인트를 잠깐 돌렸다 되돌린다). 끄면 지금 포즈만. 1e-6° 를 넘으면 **그 노드는 그대로 두고** `[ERROR]` |
| `Wrap in Container` | 변환한 망을 container 로 묶는다(기본 켬) |
| `Unload Plugin` | 원본 노드가 0 개일 때만 켜진다. 저장한 씬에서 `requires SwingTwistEvaluatorPlugin` 이 빠진다 |

옮기는 것 · 지키는 것
- 블렌드 값 + **블렌드에 걸린 키 · 연결**(animCurve, 컨트롤 어트리뷰트)을 홀더로 옮긴다 — 원본을 지우기 **전에** 옮긴다(원본에만 연결된 animCurve 는 원본과 함께 지워진다).
- `twists[]` 의 빈 인덱스는 자리를 지킨다(`twists[0]`, `twists[2]` 만 있으면 망도 0 · 2).
- 원본의 출력 unitConversion 은 원본과 함께 사라진다(남는 노드 없음).
- 홀더에 `sourceType` · `sourceName` 을 남긴다 → Rigs 탭 `Source` 칸, Restore 의 이름.

거절하는 경우: **레퍼런스 노드**(원본 파일에서 변환할 것), start 연결 없음, 출력이 rotate 가 아닌 곳 · 두 곳 이상을 구동, 출력 조인트 rotate 잠김.
`fromEnd` 가 연결돼 있으면 지금 값으로 고정하고 `[WARN]`(망은 구조로 정해진다 — §4).

★ **Unload Plugin 은 undo 큐를 비운다** — 변환으로 지운 원본 노드가 undo 큐에 남아 있으면 마야가 플러그인을 못 내린다(확인 창이 먼저 알린다).

## 3. Rigs 탭

씬에 만든 노드망(홀더) 목록 — `Holder · Start · Swing · Twists · From End · Nodes · Container · Source`.
행을 고르면 홀더(container 로 묶였으면 container)가 선택된다. `Source` = 변환한 원본 노드 이름, 새로 만든 망이면 `Built`.

| 버튼 | 하는 일 |
|------|---------|
| `Refresh` | 씬에서 다시 읽는다(탭을 열 때도 자동) |
| `Select Holder` | 홀더(또는 container) 선택 → **Channel Box 에서 `swingBlend` · `twistBlend[i]` 를 바로 고친다**(키도 된다) |
| `Select Nodes` | 노드망 전체 선택 |
| `Select Joints` | 입력 · 출력 조인트 선택 |
| `Load to Build` | 설정을 Build 탭으로 복사(고쳐서 다시 만들 때 — 옛 망을 먼저 Delete) |
| `Delete` | 노드망 + 홀더(+ container) 삭제(확인 창, Ctrl+Z 한 번). 출력 조인트는 마지막 회전값에 남는다 |
| `Wrap` / `Unwrap` | 망 + 홀더를 container `<홀더>_CTN` 하나로 묶기 / 풀기(망은 그대로, container 만 지움) |
| `Black Box` | container 의 blackBox 토글 — 켜면 Outliner · Node Editor 에서 한 노드로 보인다 |
| `Restore Original` | 망을 원본 `SwingTwistEvaluatorNode` 로 되돌린다(원본 플러그인 필요, 블렌드 키 · 연결도 원본으로). **MetaHuman DNA export 전에** |

### Container

망 하나 = container 하나. 조인트는 **넣지 않는다**. 원본 노드와 같은 이름으로 공개한다:

| 공개 이름 | 바인드 |
|-----------|--------|
| `swingBlend` · `twistBlend<i>` | 홀더 블렌드 — container 를 고르고 Channel Box 에서 고친다(키 가능) |
| `startJoint` · `endJoint` | 입력 eulerToQuat `.inputRotate` (endJoint 는 From End 일 때만) |
| `swing` · `twists<i>` | 출력 quatToEuler `.outputRotate` |

container 를 지우면 안의 망 · 홀더도 함께 지워진다. 저장 · 다시 열기 뒤에도 container · 공개 이름 · 결과가 그대로다(시험).

## 4. 원본과 같은 점 · 다른 점

**같은 점** — 트위스트 축 X 고정, 오일러는 항상 XYZ(rotateOrder 무시), jointOrient 무시(`.rotate` 만), 블렌드 의미 · 외삽,
특이 입력(Y/Z 180° 등) 처리까지 같다.

**다른 점**
- 노드 하나가 아니라 망이다: 평가기 하나당 **8 + 트위스트당 2**(From End + End 조인트면 +2, 스윙 없으면 스윙 가지 5개 생략).
  블렌드는 홀더 `<Name>_SwingTwist`(network 노드) 하나에서 고친다.
- `fromEnd` 는 **빌드 때 구조로 정해진다** — 홀더의 `fromEnd` 는 정보용. 바꾸려면 Load to Build → Delete → Build.
- `twistBlend` 는 container 공개 이름이 `twistBlend0`, `twistBlend1` …(원본은 `twistBlend[i].values`).
- 씬 파일에 `requires "quatNodes"` 가 생긴다(마야 동봉 플러그인, 별도 설치 없음). `SwingTwistEvaluatorPlugin` 은 필요 없다.
- ★ **MetaHuman Pose Editor 의 DNA 내보내기는 `SwingTwistEvaluatorNode` 를 찾는다** — 이 툴로 만든 망은 내보내기에 들어가지 않는다.
  DNA 로 내보내기 전에 Rigs 탭 **`Restore Original`** 로 원본 노드를 되살린다(원본 플러그인 필요).

## 5. 스크립트에서

```python
from Framework.core import maya_swing_twist as ST

holder = ST.build("upperarm_l", "upperarm_l", None, "upperarm_swing_l", 0.0,
                  ["upperarm_twist_01_l", "upperarm_twist_02_l"], [0.33, 0.66], from_end=False)
ST.set_twist_blend(holder, 1, 0.5)
ST.read_holder(holder)     # build() 인자 모양 dict
ST.delete_rig(holder)

# 원본 노드 변환 · 되돌리기 · container
ST.load_original_plugin()
for node in ST.list_original_nodes():
    holder = ST.convert(node, verify_samples=20, wrap=True)
ST.restore(holder)                  # 원본 SwingTwistEvaluatorNode 로(망 삭제)
ST.wrap_container(holder); ST.unwrap_container(holder); ST.set_black_box(holder, False)
ST.unload_original_plugin(flush_undo=True)
```

## 6. 시험 (mayapy)

| 파일 | 내용 |
|------|------|
| `tests/test_swing_twist_golden.py [samples]` | 원본 플러그인과 나란히 — 무작위 1500 × 6 구성 + 특이 입력 22 × 2. 오일러 · 행렬 1e-9 기준, 실측 최대 2.1e-13° · 3.8e-15 (16/16) |
| `tests/test_swing_twist_convert.py` | 원본 MetaHuman 식 셋업 → Convert(41 포즈 대조 2e-13°, 블렌드 키 · 연결 이동, 빈 twist 인덱스) · undo/redo · Restore 왕복 · container(공개 이름 · blackBox · unwrap · undo) · 플러그인 내리고 저장 · 다시 열기(`requires` 에 SwingTwist 없음) · 거절 경우(레퍼런스 등) (50/50) |
| `tests/test_swing_twist_tool.py` | 입력 검사 · 홀더 · 블렌드 의미 · undo/redo · 저장 후 다시 열기 · 삭제 · UI 오프스크린(Convert 탭 · Wrap/Unwrap · Restore · Unload 포함) (59/59) |

GUI(실제 마야 창) 확인 · 실제 MetaHuman 씬 변환 · 성능(fps) · Maya 2023 은 아직.
