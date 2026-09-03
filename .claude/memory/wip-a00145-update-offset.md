---
name: wip-a00145-update-offset
description: "A00145 Constrain > Update 탭 — AE 의 constraint Update 버튼(-e -maintainOffset)을 리스트 전체에. 타깃을 전부 넘겨야 하고, 타깃이 아닌 걸 넘기면 edit 인데도 추가된다 (v01.36)"
metadata: 
  node_type: memory
  type: project
  originSessionId: eed8b93d-9d98-420a-85c3-532581f77463
  modified: 2026-09-03T01:13:36.659Z
---

A00145_RigConnect `Constrain` 에 **`Update`** 하위 탭 추가 (v01.35→**01.36**, 2026-09-03).
Attribute Editor 의 constraint **Update** 버튼 —
`parentConstraint -e -maintainOffset curve2  curve1_parentConstraint1;` — 을 **리스트에 담은
constraint 전부**에 돌린다. 리스트 해석·범위 규칙은 [[wip-a00145-target-edit]] 과 같다.

**offset 수식을 다시 구현하지 않았다.** `cmds.<type>Constraint(*targets, cn, e=True, mo=True)` 를
그대로 부른다 — AE 버튼과 결과가 어긋날 이유가 없어야 한다. 어려운 곳은 계산이 아니라 **명령에
넘길 타깃 목록**이었다. Maya 2024 실측([[mayapy-headless-verify]]):

- **타깃을 전부 넘겨야 한다.** 2개 중 하나만 넘기면 **넘긴 슬롯의 offset 만** 다시 구워지고
  나머지는 옛 값으로 남는다 → weight 가 섞이는 순간 driven 이 튄다. 에러는 안 난다.
- **타깃이 아닌 오브젝트를 넘기면 `-e` 인데도 타깃으로 추가된다.** 그래서 이름을 새로 만들지
  않고 지금 연결된 target 슬롯에서 읽어 넘긴다.
- `-q -targetList` 는 **짧은 이름**이라 동명 노드에서 엉뚱한 것을 집는다 → Target Edit 과 같은
  `_target_entries()`(입력 연결 역추적, 롱네임). [[uuid-safe-rename-duplicate-names]] 와 같은 이유.
- **타입이 갈린다**: parent / point / orient / scale / aim / pointOnPoly 는 `-e -mo` 를 받고,
  `geometry` / `normal` / `tangent` / `poleVector` 는 플래그 자체가 없어 **`Invalid flag 'mo'`**.
  → 건너뛰고 경고. (Target Edit 의 "보정할 offset 이 없는 타입" 목록과 같다.)
- 타깃이 여럿이고 weight 가 섞여 있어도 **정확**하다 — driven 월드 행렬 오차 **1e-16**.

**살아 있는 constraint 에 돌리면 no-op** 이다(driven 이 이미 constraint 가 시키는 자리에 있으니
같은 offset 이 다시 나온다). 그래서 로그가 `updated` / `no change` 를 가르고, "일단 다 담고
돌리기" 가 안전하다.

**driven 을 어떻게 옮기나** — 채널이 연결돼 있어 그냥은 못 움직인다. 보통 `blendParent1`
(키가 있는 오브젝트에 constraint 를 걸면 Maya 가 만드는 pairBlend 어트리뷰트)을 0 으로 두고
옮긴 뒤 Update → 1 로 되돌린다. **pairBlend 는 translate/rotate 만** 있어서 `scaleConstraint`
에는 이 경로가 없다(키가 있는 scale 에 scaleConstraint 를 걸면 아예 `Destination attribute must
be writable` 로 실패한다 — 헤드리스 테스트는 출력 연결을 잠깐 끊는 방식으로 대신했다).

파일: `app/core/constraint_update_manager.py`(신규) · `app/ui/main_window.py`.
