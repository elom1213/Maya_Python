---
name: wip-a00290-target-order-tab
description: A00290_BSTool Target Order 탭 — blendShape 타겟 순서(weight 인덱스) 재배치. 마야에 없는 명령, 흩어진 데이터를 전부 함께 옮겨야 하고 removeMultiInstance 는 그룹 단위로 쓰면 undo 가 안 된다
metadata:
  type: project
---

`A00290_BSTool` **Target Order 탭**(v01.20, 2026-09-07 신규) — blendShape 노드의 타겟
나열 순서를 TSL 에서 바꾸면 그대로 노드에 적용한다. 코어는
`app/core/target_order_manager.py`, UI 는 `_build_target_order_tab()`.

**Why:** 마야에는 이 명령이 **없다.** `blendShape` 커맨드에 재정렬 플래그가 없고,
Shape Editor 의 드래그는 그룹(디렉터리) 안 **표시 순서**만 옮긴다 — 채널박스 ·
`aliasAttr` · `blendShape -q -target` 이 보여 주는 진짜 순서인 **weight 인덱스**는
한 번 만들어지면 굳는다. Maya 2024 MEL 전체에도 재정렬 프로시저가 없다.

**How to apply:**

- **타겟 하나는 한 군데 있지 않다.** 인덱스 `i` 를 키로 흩어져 있어, 하나라도 빠뜨리면
  이름과 모양이 어긋난다(별칭만 옮기면 `A` 라는 이름이 `B` 의 델타를 가리킨다).
  별칭 · `weight[i]`(값/연결/lock) · `inputTargetGroup[i]`(델타 · 인비트윈 ·
  `targetWeights` · `normalizationId` · `postDeformersMode` · 타겟 행렬) ·
  `parentDirectory[i]` · `targetVisibility[i]` · `targetParentVisibility[i]` ·
  `nextTarget[i]` · `inbetweenInfoGroup[i]` · `targetDirectory[d].childIndices`.
- **`inputTarget` 는 베이스 지오메트리마다 하나다.** 한 blendShape 가 메시 여러 개를
  디폼하면 같은 타겟의 델타가 `inputTarget[0]`, `[1]` … 에 따로 있다. `[0]` 만 옮기면
  **두 번째 메시부터** 어긋난다.
- **★ `removeMultiInstance` 는 `inputTargetGroup[i]` 를 통째로 지우면 undo 로 안 돌아온다.**
  Ctrl+Z 뒤에도 `inputPointsTarget` 이 빈 채 남는다 = 델타가 영영 사라진다(실측).
  **잎 요소**(`inputTargetItem[6000]`, `targetWeights[4]`, `parentDirectory[2]`)는 정상
  복원된다. → 그룹을 비우지 말고 **슬롯 위에 덮어쓰고 남는 잎만** 지운다.
- **덮어쓰기 방식에서는 "값이 없으면 건너뛰기" 가 조용한 버그다.** 새 주인이 안 쓰는
  배열을 건너뛰면 전 주인의 델타가 그 슬롯에 그대로 남아, 이름만 바뀐 채 남의 모양이
  딸려 온다(빈 인비트윈 아이템이 있는 씬에서 실제로 났다). 없으면 **빈 배열로 지운다.**
- **인덱스 슬롯은 새로 만들지 않는다.** 듬성한 인덱스(`0,1,4,7`)를 그대로 두고 그 안에서만
  자리를 바꾼다. `0..n-1` 로 다시 매기면 번호로 `weight[4]` 를 참조하던 바깥
  노드/스크립트가 조용히 다른 타겟을 가리킨다.
- **Edit(sculpt) 중이면 거절**한다 — 확정 안 된 편집이 떠 있어 엉뚱한 타겟에 확정된다.
- **모양은 변하지 않는다** — 평가가 `base + Σ(wᵢ·δᵢ)` 라 더하는 순서와 무관(실측 편차
  `1e-6`, 부동소수 합 순서 차이).
- 리스트는 공용 TSL 이되 **Select/Add/Del 은 감춘다**(타겟은 씬 오브젝트가 아니다).
  이때 [[framework-tsl-attach-uuids]] 처럼 `attach_uuids=False` 를 준다.

관련: [[blendshape-target-name-vs-alias]] · [[blendshape-live-target-inputpointstarget]] ·
[[setattr-int32array-no-count]] · [[wip-a00290-shape-editor-tab]]
