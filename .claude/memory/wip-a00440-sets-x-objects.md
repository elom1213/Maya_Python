---
name: wip-a00440-sets-x-objects
description: "A00440 v01.05 - Create 의 One set for all 모드 + Edit 탭의 Objects 리스트/Add Objects to Sets(세트 하나면 전부, 여럿이면 행 순서 1:1)"
metadata:
  node_type: memory
  type: project
---

`A00440_SetTool` v01.04 -> **01.05** (2026-09-22 사용자 요청 두 가지).

1. **Create 탭 `Mode`** — `One set per object`(기본, 원래 동작) / `One set for all`
   (리스트 전부를 담은 세트 하나, 이름은 `Set Name` 칸 · 비우면 `objects_Set`).
   코어 `set_manager.run_create_one_set()`.
2. **Edit 탭 `Objects` 리스트**(Sets 우측) + `Set Operations` 안의 **`Sets x Objects`**
   묶음에 `Add Objects to Sets`. 코어 `run_add_objects_to_sets()` ·
   `pair_objects_with_sets()`.

**Why:** 컨트롤러마다 세트를 두는 리그 외에, 여러 개를 한 세트로 묶거나 **이미 있는 세트에
오브젝트를 넣는** 일이 필요했다. 요청 전 확인 결과 Edit 탭에는 그 기능이 없었다
(∪ ∩ ∖ · Split 은 전부 **새 세트를 만드는** 연산이다).

**How to apply:**
- 짝 규칙은 core 한 곳(`pair_objects_with_sets`)에 있다 — **세트가 하나면 오브젝트 전부를
  그 하나에**, 여럿이면 **행 순서 1:1**, 개수가 다르면 적은 쪽만큼(로그에 적는다).
  [[wip-a00275-transfer-pairs]] 의 1:1 규칙과 같은 모양으로 맞췄다.
- 세트 이름은 한 세트 모드에서도 `maya_sets.set_name_for` 로 다듬는다 — 네임스페이스를 남기면
  마야가 **그 네임스페이스 안에** 세트를 만든다(이 툴 v01.01 의 함정).
- 이미 멤버인 것은 마야가 무시하므로 **몇 개가 이미 있었는지 세어 로그에 적는다** —
  안 그러면 눌렀는데 아무 일도 없는 것처럼 보인다.
- `Set Operations` 안에 `Sets x Objects` 소제목을 두었다. 세트끼리의 연산과 **입력이 다른**
  연산이라 섞이면 안 되고, 앞으로 이 자리에 연산이 더 붙는다.
- 검증 51항목(mayapy 2024 + 오프스크린 Qt).
