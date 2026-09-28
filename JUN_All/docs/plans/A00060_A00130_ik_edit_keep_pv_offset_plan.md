---
title: IK Edit — 폴 벡터 offset 을 지키고 중간 조인트를 폴 평면에 맞추기 — 수정 계획서
aliases: [IK Edit Keep Offset, Keep PV Offset, A00060 IK Edit, A00130 IK session]
tags: [plan, A00060, A00130, jointTool, controlRig, ik, poleVector, reference]
updated: 2026-09-28
---

# IK Edit — 폴 벡터 offset 을 지키고 중간 조인트를 폴 평면에 맞추기

> **대상**: `A00060_jointTool_V03`(v03.12) `Chain > IK Edit` · `A00130_ControlRig_V02`(v02.27) `Match` 의 IK 세션
> **공유 코드**: `tools/A00060_jointTool_V03/app/core/ik_edit_manager.py` — A00130 의 `app/core/ik_session.py` 가 이것을 부른다

---

## 1. 요약 — 결론부터

| 물음 | 답 |
|---|---|
| **할 수 있나?** | **된다.** offset 을 한 글자도 안 바꾸고 IK 를 되켠 뒤 위치·회전 편차 **0.000000** (mayapy 2024 실측, 3장) |
| **레퍼런스에서도 되나?** | **된다.** 레퍼런스로 불러온 체인에서 같은 절차 → 편차 0, 저장 후 다시 열어도 그대로 (reference edit 로 남는다) |
| **`Rest Translate` 를 맞추면 IK 가 고쳐지나?** | **아니다.** `Rest Translate` 는 타깃 weight 가 1 이면 **출력에 영향이 없다**. IK 를 실제로 맞추는 것은 **joint2 를 폴 평면에 올려놓는 것**이다. `Rest Translate = Constraint Translate` 는 정리용으로 함께 한다(3-1) |
| **무엇이 바뀌나?** | 지금은 "체인이 먼저, 폴 벡터가 따라간다"(offset 을 역산). 새 방식은 **"폴 타깃이 먼저, 체인이 따라간다"** — 폴 평면은 poleTgt + 기존 offset 이 정하고 joint2 가 그 평면으로 간다 |
| **조심할 것** | ① v 가 폴 **반대편**이면 솔버가 체인을 뒤집는다(편차 6.39) ② joint2 를 옮기면 뼈 축(X)이 다음 조인트를 안 본다(18.6°) ③ A00130 의 폴 타깃이 **체인에 살아 있게 물린 것**이면 전제가 달라진다(5장) |

---

## 2. 지금 어떻게 동작하나

`ik_edit_manager.end_edit()` → `_update_one()` 의 순서:

```
1. 편집된 체인을 기억한다(각 조인트의 월드 위치·회전)
2. 핸들을 이펙터로 스냅
3. _apply_pole_vector() : 편집된 체인에서 "원하는 폴 벡터" 를 계산해
      new_offset = desired_pv − (current_pv − current_offset)
   으로 poleVectorConstraint.offset 을 **바꾼다**
4. preferred angle 저장 → IK 켜기 → 편차 측정
```

즉 **joint2 가 정답이고 폴 벡터가 맞춰 간다.** 그래서 offset 이 바뀌고, 그 결과로
`constraintTranslate`(= 핸들의 `poleVector`)도 바뀐다 — 요청에서 말씀하신 현상이 이것이다.

A00130 은 `ik_session.end()` 에서 이 `end_edit()` 을 **그대로** 부른다(`pv_mode` 기본값 = offset 갱신).
`D01_IK_handle` 세트의 핸들 + 세트에 없지만 매칭 대상을 건드리는 핸들(`related_handles`)이 전부 이 길을 탄다.

---

## 3. 검토 — mayapy 2024 실측

테스트 체인: `joint1 (0,10,0) → joint2 (0,5,1) → joint3 (0,0,0)`, `ikRPsolver`, `poleTgt (0,5,8)` 에 poleVectorConstraint.
옮긴 자리: `joint1 → (1,12,0.5)`, `joint3 · 핸들 → (1.5,1,2)`, `poleTgt → (4,7,6)`, `v = (2,7,3)`.

### 3-1. `Rest Translate` 의 역할

| 상태 | `constraintTranslate`(IK 에 들어가는 값) |
|---|---|
| weight 1, `restTranslate` 를 (50,50,50) 으로 | **변화 없음** (0,−5,8) — joint2 도 그대로 |
| weight 0.5 | 변화 없음 (타깃 하나면 정규화된다) |
| weight 0 | (50,50,50) — **이때만** rest 가 쓰인다 |

→ `Rest Translate` 는 **"타깃 weight 가 모두 0 일 때 돌아갈 자리"** 다. 평상시 IK 에는 관여하지 않는다.
그래서 요청의 2단계(`Rest = Constraint Translate`)는 **IK 를 고치는 단계가 아니라 기록을 맞추는 단계**다 —
해 두면 나중에 누가 weight 를 0 으로 내려도 체인이 엉뚱한 옛 평면으로 튀지 않는다. 계획에 그대로 넣는다.

### 3-2. 제안 방식이 성립하는가

폴 평면 = **체인 축(joint1→joint3)** + **폴 벡터**(핸들 부모 공간의 `poleVector` 를 월드로) 가 이루는 평면.
`twist ≠ 0` 이면 솔버가 그 평면을 축 둘레로 twist 만큼 **더** 돌리므로 같은 각만큼 돌린 평면을 쓴다.
joint2 = v 를 그 평면에 **수직 투영**한 점. joint3 · 핸들은 월드 자리를 지킨다.

| 경우 | v 가 옮겨진 거리 | offset | IK 켠 뒤 위치 편차 | 회전 편차 |
|---|---|---|---|---|
| 기본 | 0.237 | **그대로** | **0.000000** | **0.0000°** |
| `twist 30` | 0.765 | 그대로 | 0.000000 | 0.0000° |
| offset `(1,0,2)` 가 원래 있던 체인 | 0.204 | 그대로 | 0.000000 | — |
| **레퍼런스(`CAGE:`)** | 0.237 | 그대로 | 0.000000 | — |
| 레퍼런스 → 저장 → 다시 열기 | | | joint2 **그대로** | |
| **v 가 폴 반대편** | 2.754 | 그대로 | **6.392913** ✗ | |

- 레퍼런스 노드에 `restTranslate` · 조인트 `translate` · `ikBlend` · `snapEnable` `setAttr` 전부 된다(reference edit 10개로 저장).
- joint1–joint2, joint2–joint3 길이는 **바뀐다** — 요청대로 허용한다. joint3 은 월드 자리를 지킨다.

### 3-3. v 가 폴 반대편일 때

평면에 투영한 점이 폴 벡터의 **반대쪽 반평면**에 떨어지면, RP 솔버는 팔꿈치를 **늘 폴 쪽**에 놓으므로
체인이 뒤집힌다(편차 6.39). 막을 방법은 셋이다 — **정책을 정해 주셔야 한다(6장 Q3).**

| 안 | 동작 | 비고 |
|---|---|---|
| A. 거울 반사 | 투영점을 체인 축에 대해 **폴 쪽으로 뒤집어** 놓는다 | 폴 방향이 우선. v 와 가장 가까운 "가능한" 자리는 아니다 |
| B. 건너뛰고 경고 | 그 체인은 **손대지 않고** `[WARN]` | 리그 데이터가 틀린 것일 수 있으니 사람이 본다 |
| C. 축 위로 | 투영점을 **축 위(일직선)** 로 | 가능한 자리 중 v 에 가장 가깝지만 팔이 펴진다 — 비추천 |

### 3-4. 뼈 축(X)이 다음 조인트를 안 본다

joint2 의 `translate` 만 바꾸면 joint1 의 방향(`jointOrient`)은 그대로라, **X 축이 joint2 를 보지 않게 된다**.

| | joint1 X ↔ 뼈 | joint2 X ↔ 뼈 | IK 편차 |
|---|---|---|---|
| 방향 그대로 | **18.63°** | 7.26° | 0 |
| joint1 · joint2 방향 다시 맞춤(X→다음 조인트) | **0.000°** | **0.000°** | 0 |

방향을 다시 맞춰도 IK 편차는 0 이다. **어느 쪽을 원하시는지 정해 주셔야 한다(6장 Q2)** — 지금의 IK Edit 도
사용자가 옮긴 그대로 두지 방향을 고치지 않는다. 맞추기로 하면 up 축(Z 를 평면 법선 쪽 / 폴 쪽 등)도 정해야 한다.

---

## 4. 설계

### 4-1. 새 모드 — `PV_MODE_KEEP` (공유 코어 `ik_edit_manager.py`)

기존 두 모드(`offset` 갱신 · `target` 이동)는 그대로 두고 **셋째 모드**를 더한다.

```
end_edit(handles, pv_mode=PV_MODE_KEEP, mid_policy=..., reorient=...)

  편집 모드에 들어온 뒤 사용자(또는 A00130 Match)가 joint1 · joint3 · 핸들 · poleTgt · joint2 를 옮겨 둔 상태
  ├─ 1. (확인) offset 을 읽어 둔다 — 끝나고 **같은 값인지 검사**해 로그에 [OK] offset kept
  ├─ 2. restTranslate ← constraintTranslate           (3-1)
  ├─ 3. 폴 평면 계산 : 체인 축 + poleVector(월드) (+ twist 회전)
  ├─ 4. v = 지금 joint2 의 월드 위치 → 평면에 투영     (반대편이면 mid_policy, 3-3)
  ├─ 5. joint2 를 그 자리에, joint3 · 그 자식들은 월드 자리 유지
  ├─ 6. (선택) joint1 · joint2 방향 다시 맞춤            (3-4)
  ├─ 7. 핸들을 이펙터로 스냅 (지금과 같다)
  └─ 8. preferred angle 저장 → IK 켜기 → 편차 측정 (지금과 같다)
```

- **v 는 "편집이 끝났을 때 joint2 가 있는 자리"** 로 정한다. A00060 에서는 사용자가 옮겨 둔 자리,
  A00130 에서는 Match 가 템플릿 조인트에 맞춰 둔 자리다 — 별도 입력이 필요 없다.
- `poleVectorConstraint` 가 없고 `poleVector` 를 직접 쓰는 핸들 → 그 값을 "고정된 폴" 로 똑같이 쓴다.
  `ikSCsolver` → 폴 평면이 없으므로 지금처럼 핸들 스냅만. `ikSplineSolver` → 지금처럼 거부.
- **3 조인트보다 긴 RP 체인**(joint1→a→b→end): 중간 조인트 **전부**를 같은 평면에 투영하는 것이 자연스럽다 — 6장 Q5.
- 판정 · 스냅 · IK 끄고 켜기 · 스냅샷 · 취소 · 레퍼런스 솔버 이름 문제(v03.02) 등 **나머지는 지금 코드를 그대로** 쓴다.
- `update_now()`(세션 없이 한 번 맞추기)에도 같은 모드를 연다.

### 4-2. A00060 UI

`Chain > IK Edit` 의 `Pole vector` 콤보에 한 줄 추가:

```
Pole vector : [ Keep offset - fit the mid joint to the pole plane   v ]   ← 새 모드
              [ Constraint offset (keep the target where it is)       ]   ← 지금 기본
              [ Move the pole vector target                            ]
Opposite side : [ Mirror to the pole side  v ]      ← 새 모드일 때만 켜짐 (Q3 에 따라)
☐ Re-orient joints to the new bones                ← Q2 에 따라
```

로그(영어): 투영으로 joint2 가 얼마나 옮겨졌는지(`moved 0.237`), 반대편 처리 여부, `offset kept`, 편차.

### 4-3. A00130

`ik_session.end()` 가 `ike.end_edit(handles, pv_mode=PV_MODE_KEEP, ...)` 로 부르게 바꾼다 —
`D01_IK_handle` 의 핸들 + `related_handles` 로 찾은 핸들 모두. 매칭 순서(부모부터, 밀려난 것 재매칭)는 그대로.

**함께 봐야 할 두 단계** (둘 다 새 방식과 부딪칠 수 있다):

| 단계 | 문제 | 대응 |
|---|---|---|
| **IK 축 맞추기**(`ik_axis_manager`, 세션 **뒤**에 `twist` 를 바꾼다) | twist 를 바꾸면 **폴 평면이 돌아서** 방금 평면에 올린 joint2 가 평면에서 벗어난 채 솔버가 다시 푼다 | 새 방식에서는 (a) 축 맞추기를 **세션 전에** 하거나 (b) twist 가 바뀐 뒤 평면을 다시 계산해 한 번 더 맞춘다 — 실측으로 고른다(Phase 0) |
| **Orient & Place 의 폴 타깃**(`_do_pole_targets` → A00060 `pole_target_manager.ensure()`) | 폴 타깃이 `A' = (1−n)/2·p1 + n·p2 + (1−n)/2·p3` 로 **체인에 살아 있게 물려 있으면**, joint2 를 옮기는 순간 poleTgt 도 따라 움직인다 → "고정된 폴 평면" 이 없다 | 이 경우 A' 는 늘 체인 평면 위라 **투영이 할 일이 없고**(v 가 이미 평면에 있다) offset 만 지키면 된다. 어느 구조인지 **확인이 필요하다 — Q4** |

- Match 체크박스 `IK session` 툴팁 · 로그 · 문서에 "offset kept, mid joint fitted" 를 적는다.
- 가능하면 A00130 에도 **모드 선택**(새 방식 기본 / 옛 방식)을 둔다 — 되돌릴 길을 남기기 위해. Q1 에 따라.

---

## 5. 단계

| Phase | 내용 | 검증 |
|---|---|---|
| **0. 실측 확정** | 사용자 답(6장)을 받은 뒤, 실제 케이지(레퍼런스)로 ① 폴 타깃 구조 ② twist 축 맞추기와의 순서 ③ 4조인트 이상 RP 체인 ④ 반대편 정책을 mayapy 로 확인 | 케이지 파일에서 IK 켠 뒤 편차 · offset 불변 · reference edit 수 |
| **1. 코어** | `ik_edit_manager` 에 `PV_MODE_KEEP` · 평면 투영 · rest 동기화 · 반대편 정책 · (선택) 재정렬. 기존 두 모드 불변 | 3장 표를 회귀로 — 기본/twist/offset/레퍼런스/재오픈/반대편/재정렬 + **옛 모드 기존 테스트 전부** |
| **2. A00060 UI** | 콤보 항목 · 옵션 · 로그 · 가이드 문서 | 오프스크린 UI (편집 ON → 옮기기 → OFF → 편차 0, 취소 복원, undo 한 번) |
| **3. A00130** | `ik_session.end` 가 새 모드 · twist 축 맞추기 순서 조정 · 모드 선택(Q1) | 기존 Match / Length / Orient / IK 회귀 568항목 + 새 모드 항목 |
| **4. 문서** | 두 툴 가이드 · WORKLOG · 메모 | |

버전: A00060 **v03.13**, A00130 **v02.28**. A00130 은 A00060 코어를 import 하므로 **A00060 먼저**.

---

## 6. 알려 주셔야 할 것

| # | 질문 | 왜 필요한가 |
|---|---|---|
| **Q1** | 새 방식을 **기본값**으로 할까요, **옵션**으로 둘까요? A00060 은 콤보에 추가(기본을 바꿀지), A00130 은 새 방식만 쓸지 / 선택하게 할지 | 지금까지 만든 리그를 옛 방식으로 다시 맞출 일이 있는지 |
| **Q2** | joint2 를 옮긴 뒤 **joint1 · joint2 의 뼈 축(X)을 다음 조인트로 다시 맞출까요?** 맞춘다면 up 축은? (예: Z 를 폴 쪽 / 평면 법선 쪽) | 안 맞추면 X 가 뼈에서 최대 18.6° 벗어난다(3-4). IK 편차는 어느 쪽이든 0 |
| **Q3** | v 가 폴 **반대편**일 때 A(폴 쪽으로 거울 반사) / B(건너뛰고 경고) / C(축 위로) 중 어느 것? | 그대로 두면 솔버가 체인을 뒤집는다(편차 6.39) |
| **Q4** | 실제 케이지의 **poleTgt 는 어떤 물체**인가요? ① 자유로운 로케이터/컨트롤러 ② A00060 `Pole Target`(A00130 Orient & Place 가 만드는, 체인에 살아 있게 물린 것) ③ 컨트롤러 아래 그룹 등. 그리고 A00130 Match 에서 **poleTgt 의 새 위치는 어디서 오나요?** (템플릿 조인트에 매칭되는 세트가 있는지, 아니면 사람이 먼저 옮겨 두는지) | ②면 joint2 를 옮기는 순간 폴도 따라 움직여 "고정된 평면" 이 없다(4-3). 새 위치의 출처가 없으면 A00130 은 poleTgt 를 옛 자리에 둔 채 평면을 계산한다 |
| **Q5** | `D01_IK_handle` 에 **3 조인트보다 긴 RP 체인**이 있나요? 있다면 중간 조인트 전부를 평면에 투영하면 될까요? | 요청 예시는 3 조인트다 |
| **Q6** | A00130 의 **IK 축 맞추기**(`D02_IK_handle_axiesUpadate : +Z`, twist 를 바꾼다)는 계속 쓰시나요? | twist 를 바꾸면 폴 평면이 돈다 — 순서를 바꾸거나 한 번 더 맞춰야 한다(4-3) |
| **Q7** | 가능하면 **실제 케이지 파일 경로**(레퍼런스로 쓰는 것)와, 옮겨야 하는 체인 하나의 예(조인트 · 핸들 · poleTgt 이름) | Phase 0 을 실제 리그로 확인하기 위해. 테스트 체인에서는 되지만, 폴 타깃 배선 · 중첩 IK · twist 가 섞인 실제 리그에서 한 번 봐야 한다 |

---

## 7. 참고

- 실측 스크립트: 세션 스크래치(`probe_pv.py`, `probe_orient.py`) — Phase 1 회귀 테스트로 옮긴다.
- 관련 메모: `wip-a00060-ik-edit`(poleVectorConstraint 식, twist 보정, 레퍼런스 솔버 이름) ·
  `wip-a00130-ik-session`(snapEnable 과 undo, 중첩 IK) · `wip-a00130-ik-axis`(twist 로만 축이 돈다) ·
  `wip-a00060-pole-target`(A' 배선).
- 관련 계획서: [`A00060_poleTarget_plan.md`](A00060_poleTarget_plan.md) · [`A00130_ControlRig_V02_plan.md`](A00130_ControlRig_V02_plan.md)(Phase 4 · 7-4).
