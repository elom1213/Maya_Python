---
name: maya-set-rename-traps
description: 세트 이름 바꾸기 함정 — Search and Replace Names 가 막힌 건 명령이 아니라 select(set) 이 멤버를 펼치는 것, 짧은 이름으로 rename 하면 네임스페이스가 벗겨진다, 마야가 잘못된 문자를 조용히 고친다
metadata:
  type: reference
---

세트(`objectSet`) 이름을 바꿀 때 **실측이 아니면 조용히 틀리는 것들** (Maya 2024).

**① 마야 기본 `Search and Replace Names` 가 세트에 안 먹히는 진짜 이유**

명령이 막힌 게 아니다. MEL `searchReplaceNames` 는 **`"all"` 모드로 돌리면 세트도 잘 바꾼다**
(실측: 세트 5개 포함 8개 이름이 한 번에 바뀐다). 막힌 것은 **세트를 선택하는 방법**이다.

```python
cmds.select(mySet)
cmds.ls(sl=True)                    # ['pCube1']  <- 세트가 아니라 멤버가 나온다
cmds.ls(sl=True, type="objectSet")  # []
cmds.select(mySet, noExpand=True)
cmds.ls(sl=True, type="objectSet")  # ['mySet']   <- 이러면 잡힌다
```

**`cmds.select(set)` 은 세트를 멤버로 펼친다**([[wip-a00440-settool]] 과 같은 사실).
그래서 `"selected"` 모드는 세트를 영영 못 보고, `"all"` 모드는 메시·조인트·카메라까지 바꿔
쓸 수가 없다. → **세트를 다루는 UI 는 씬 선택에 기대지 말고 직접 열거해서 고르게 해야 한다.**

**② 짧은 이름으로 rename 하면 네임스페이스가 벗겨진다** ★

```python
cmds.rename("NS:in_ns", "plain")   # -> 'plain' 이 **루트 네임스페이스**에 생긴다. NS 는 빈다.
```

레퍼런스에서 온 세트에 이걸 하면 **전부 네임스페이스를 잃는다.**
→ 네임스페이스를 떼어 두고 **짧은 이름만 치환한 뒤 다시 붙여서** `rename("NS:new", ...)` 한다.

**③ 마야가 잘못된 문자를 조용히 고친다** (경고만 뜨고 넘어간다)

| 준 이름 | 실제로 생기는 이름 |
|---|---|
| `1bad` | `bad` — **맨 앞 숫자가 사라진다**(`_` 로 안 바뀐다) |
| `has space` · `has-dash` · `has.dot` · `a\|b` | `has_space` · `has_dash` · `has_dot` · `a_b` |
| `""` | `RuntimeError: New name has no legal characters.` |

→ 의도와 다른 이름이 조용히 생긴다. **미리 검사해서 거르는 편이 낫다**
(`^[A-Za-z_][A-Za-z0-9_]*$`).

**④ 이름이 겹치면 번호를 붙인다** — `rename(b, "dup_set")` → `dup_set1`. **에러가 아니다.**
→ 사전에 `objExists` 로 알리고, 실행 뒤에는 **`rename` 이 돌려준 실제 이름**을 봐야 한다.

**⑤ 기본 세트 판정에 `ls(readOnly=True)` 를 쓰면 안 된다** — **빈 리스트를 준다.**
그런데 `rename("initialShadingGroup", ...)` 은 `Cannot rename a read only node` 로 죽는다.
→ `cmds.ls(defaultNodes=True)` 로 골라야 한다. 잠긴 노드는 `Cannot rename a locked node`.

**⑥ `partition` 은 `objectSet` 이 아니다** — `ls(type="objectSet")` 에 **안 잡힌다**.
따로 열거해야 한다. 반대로 `shadingEngine` 은 `objectSet` 의 하위 타입이라 **같이 딸려 온다**
(렌더 셋업을 실수로 건드리지 않으려면 기본에서 빼는 편이 낫다).

**⑦ 세트는 이미 쓰이는 이름을 못 쓴다 (DAG 는 쓸 수 있다)**

| | 결과 |
|---|---|
| 트랜스폼 `myName` 이 있는데 세트를 `myName` 으로 | **조용히 `myName1`** |
| 세트 `shared` 가 있는데 트랜스폼을 `shared` 로 | **조용히 `shared2`** |
| DAG 둘이 **부모만 다르면** 같은 이름 | **허용** (`\|g1\|c` 와 `\|g2\|c` 공존) |

→ 세트에 이름을 복사할 때는 **접미사가 필요하다**(`_copy` 등). DAG 대상은 필요 없다.

**⑧ 세트 판정은 `nodeType(inherited=True)` 로**
`shadingEngine` 은 `objectSet` 의 **하위 타입**이라 `nodeType()` 문자열 비교로는 놓친다
(실측: `['containerBase', 'entity', 'objectSet', 'shadingEngine']`).
`partition` 은 별도 타입이다.

**⑨ 짧은 이름으로 rename 하면 네임스페이스가 벗겨지는 것은 트랜스폼도 마찬가지다**
② 는 세트만의 문제가 아니다 — `rename("NS:inCube", "plainCube")` 도 루트로 옮긴다(실측).
**이름을 바꾸는 모든 코드가 네임스페이스를 떼어 두고 다시 붙여야 한다.**

**그 밖에**
- 세트는 DAG 노드가 아니라 `|` 경로가 없다 — `ls(uuid, long=True)` 가 그냥 이름을 준다.
  UUID 핸들은 그대로 쓸 수 있다([[uuid-safe-rename-duplicate-names]]).
- 세트 `rename` 은 **undo 된다**.

적용: `A00330_NamingTool` 의 `Set Rename` 탭
과 `Copy Name` 탭의 세트 지원
(`app/core/set_rename_ops.py` · `naming_ops.copy_name`, v01.02~01.03 — [[wip-a00330-set-rename]]).
검증은 [[mayapy-headless-verify]].
