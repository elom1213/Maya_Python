---
name: wip-a00145-match-keep-children
description: "A00145 Match > Keep Children in Place (기본 OFF) — 팔로워만 옮기고 자식은 월드 자리에. Mirror 와 공용 app/core/keep_children.py (v01.53)"
metadata:
  node_type: memory
  type: project
---

`A00145_RigConnect` **Match > Keep Children in Place** (v01.52 -> 01.53, 2026-09-21, 사용자 요청).
Followers 를 Targets 에 맞춰 옮기되, 그 **아래 오브젝트는 있던 월드 자리에** 둔다. **기본은 해제** —
평소에는 자식이 부모를 따라가는 것이 맞다. Mirror 탭의 같은 이름 체크박스(v01.41, 기본 ON)와
**같은 코어**를 쓴다: `app/core/keep_children.py` (v01.53 에 `mirror_manager` 에서 떼어 냈고,
mirror 쪽은 `_children_to_keep = keep.capture` 식 위임만 남겼다 — 동작 불변).

**Why:** 같은 이름의 체크박스가 두 탭에 있는데 구현이 갈라지면 쓰는 사람이 둘을 다른 기능으로
믿게 된다. 기본값만 다르다(Mirror ON / Match OFF).

**How to apply:**
- 순서는 언제나 `capture(parent, skip_paths)` -> 부모 이동 -> `restore(kept, flipped, ...)`.
  **읽기는 아무것도 옮기기 전에 전부** — 앞 줄이 움직이면 그 아래 자식도 이미 밀려 있다.
- **직계 자식만** 잡는다. 손자는 로컬이 그대로라 저절로 제자리다(계층이 커도 비용이 안 는다).
- **켜지면 팔로워를 부모 -> 자식 순서로 매칭한다** (`_depth` = 롱네임의 `|` 개수). 안 그러면
  자식 팔로워를 먼저 맞춰 놓고 부모 팔로워가 다시 끌고 간다. 잡아 둘 자식이 하나도 없어도
  정렬은 한다 — 처음에 `captured` 가 비면 정렬을 건너뛰게 짰다가 이 케이스로 테스트가 깨졌다.
- 보존 대상에서 빼는 것: **그 자신이 팔로워인 자식**(제 타겟으로 간다) · 컨스트레인트 노드 · 셰이프.
- 잠기거나 연결된 채널이 있는 자식은 **부모를 따라간 채로** 두고 사유를 notes 로 알린다
  (`xform` 은 잠긴 채널을 조용히 건너뛰고 나머지만 써서 반쪽 결과를 만든다 →
  [[xform-silent-on-locked-channels]]).
- 부모의 좌우손계가 바뀌면(음수 스케일 타겟 + Scale) 자식 로컬 스케일 부호가 바뀌어야 해서
  그때만 scale 채널까지 검사한다(`keep.determinant3` 부호 비교).
- 요약 줄은 `_note` 가 아니라 **`_info`** 로 넣는다 — `_note` 는 5줄 제한이 있어 앞에 경고가
  쌓이면 "몇 개 지켰다" 가 사라진다. 로그 플래그에 `K` 가 붙는다(`[TRK]`).
- 검증: mayapy 2024 코어 27항목 + 오프스크린 Qt UI 10항목. **Mirror 회귀 테스트를 같이 돌린다**
  (공용 모듈로 뺐으므로). [[wip-a00145-mirror-tab.md]] 참고.
