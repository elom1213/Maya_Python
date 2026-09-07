---
name: wip-a00460-fk-ik
description: A00460_ControllerTool FK & IK 탭 — 자식 스택은 _tgt 가 아니라 _ctl 밑에(_tgt 는 잎), Hierarchy(FK/IK)는 Mode(Bone Root/Chain)와 별개 축. 중복 판정은 풀패스로 (v01.04)
metadata:
  node_type: memory
  type: project
---

`A00460_ControllerTool` **Create > FK & IK** 탭 (v01.03 → **01.04**, 2026-09-07).
탭 이름을 `FK` → `FK & IK` 로 바꾸고 두 가지를 넣었다. 코어는 `app/core/fk_manager.py`
(`build_fk_controls` → **`build_controls`** 로 개명, 외부 importer 없음).

**① 자식 스택이 붙는 자리를 `_tgt` → `_ctl` 로**

예전에는 `_tgt` 가 "조인트를 끄는 드라이버" 와 "다음 뼈의 부모" **두 역할을 겸했다.**
월드 결과는 같지만(`_tgt` 도 `_ctl` 에 로컬 0 으로 붙어 있다) `_tgt` 에 자식이 달려 있으면
그것만 따로 옮기거나 지울 수 없다. 이제 `_ctl` 밑에 `_tgt`(잎)와 자식 `_zro` 가 **나란히** 선다.

구현은 **역할을 나누는 것**이 전부다 — `_build_one` 이 `last`(=`_tgt`)로 컨스트레인트를 걸고
**`ctl` 을 돌려준다.** `tgt` 옵션을 꺼도 자식이 붙는 자리는 `_ctl` 로 같다.

**② Hierarchy(FK / IK) — Mode 와 별개 축**

- `HIER_FK` : 스택끼리 잇는다(기존 동작).
- `HIER_IK` : 잇지 않는다. **모든 `_zro` 가 씬 최상위(월드)** 에 선다.

**★ Mode(Bone Root / Bone Chain)와 섞지 말 것.** Mode 는 *누구에게 만들까*, Hierarchy 는
*만든 것끼리 어떻게 이을까* 다. 네 조합이 모두 성립한다. UI 도 그룹박스를 따로 두고
제목에 그 차이를 적었다(`Mode - which nodes get a control` / `Hierarchy - how the stacks are linked`).

**★ 자손을 "따라가는 것" 과 스택을 "잇는 것" 은 별개다.** Bone Root + IK 는 자손까지 그대로
돌며 컨트롤러를 만들되 부모를 넘기지 않는다. `_build_root_recursive` 가 재귀는 그대로 하고
`child_parent` 만 `None` 으로 넘긴다 — 여기를 한 덩이로 보면 "IK 면 자손을 안 판다" 로
잘못 만들게 된다.

IK 도 **스택 최상단은 조인트 자리에 matchTransform** 한다(부모가 없을 뿐). 조인트는 여전히
자기 `_tgt` 를 따라가므로 컨트롤러 하나를 옮기면 **그 조인트만** 움직인다(실측).

**③ fix — 루트와 자손을 함께 리스트에 담으면 자손 스택이 두 번 생기던 것**

ROOT 모드의 중복 판정 `seen` 이 **입력 문자열 그대로**를 담고 있었다. 재귀는 `_children_of`
가 준 **풀패스**(`|a|b`)를, 바깥 루프는 사용자가 넣은 **짧은 이름**(`b`)을 넣으므로 같은
조인트를 다른 것으로 봤다. **에러가 나지 않고** `b_zro1` 스택이 조용히 하나 더 생겼다.
`cmds.ls(node, long=True)` 로 정규화해 비교한다. (테스트를 쓰다 걸린 기존 버그다.)

검증 45항목([[mayapy-headless-verify]]) — `_tgt` 잎 · 자식 부모 = `_ctl` · `tgt` 끈 경우 ·
IK 가 분기 포함 전부 월드 · IK 는 컨트롤러가 서로를 안 끄는 것과 FK 는 끄는 것 대조 ·
네 조합 · 기본값/알 수 없는 값 폴백 · 중복 회귀 · 스택이 조인트 자리에 서는지.

관련: 스택 관례는 [[wip-a00400-curve-joints]] 가 같은 모양으로 맞춰 쓴다(그쪽은 이 모듈을
**import 하지 않고 복사**했다 — `dev/build_release.py` 가 툴 하나 + Framework 만 복사하므로).
