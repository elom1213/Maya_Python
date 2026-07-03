# Maya 노드 신원(identity): 이름/경로 vs UUID

> 스크립트에서 노드를 "잡아두는" 방법의 차이와, 씬에 **같은 이름의 오브젝트**가 있어도
> 리네임·편집이 깨지지 않게 하는 기법을 정리한다.
> 실전 적용 사례: [A00330_NamingTool](../A00330_NamingTool.md) v01.01 (2026-07-03).

---

## 1. UUID 란?

**UUID(Universally Unique Identifier)** = 전 세계에서 유일하도록 만든 128비트 식별자.
`4C3B2A1D-6F8E-4A2B-9C1D-...` 같은 16진수 문자열로 표현되며, 랜덤/시간 기반으로 생성해서
사실상 충돌하지 않는다. "이름"과 달리 **중복이 없고 바뀌지 않는 도장** 역할을 한다.

Maya 는 씬의 **모든 노드에 UUID 를 하나씩** 자동 부여한다(Maya 2016+). 파일에 저장되어
재오픈 후에도 유지된다.

---

## 2. 이름/경로 vs UUID

노드를 스크립트로 참조하는 방법은 세 가지고, 성질이 다르다.

| | short name (`joint_02`) | DAG 경로 (`|grp|joint_02`) | UUID |
|---|---|---|---|
| 유일성 | ❌ 같은 이름 여러 개 가능 | △ 그 순간엔 유일 | ✅ 노드마다 유일 |
| rename 하면 | 바뀜 | 바뀜 | **안 바뀜** |
| 부모/구조 바뀌면(reparent) | 그대로지만 여전히 모호 | 경로가 바뀜 → **무효** | **안 바뀜** |
| 저장→재오픈 | 유지 | 유지 | 유지 |

핵심 직관:

- **이름·경로**는 "지금 이 노드가 **어디에 있고 뭐라 불리는가**" → 상황에 따라 변하거나 모호해진다.
- **UUID**는 "이 노드가 **바로 그 노드다**"라는 신원 자체 → 절대 흔들리지 않는다.

> 개념적으로는 C++ API 의 `MObject` / `MObjectHandle`, 또는 다른 DB 의 primary key 와 같은 역할이다.

---

## 3. 왜 문제가 되나 — 동일 이름 & rename 중 경로 변화

공용 리스트 위젯(`JUN_mod_tsl_qt_v01`)과 `cmds.ls(sl=True)` 는 기본적으로 **short name** 을
저장/반환한다. 씬에 같은 이름이 여러 개면 이 short name 은 **모호**해진다.

예) 두 루트 밑에 각각 같은 이름 `joint_02` 자식이 있는 경우:

```
joint_01
└── joint_02      ← (A)
joint_03
└── joint_02      ← (B) : (A) 와 이름이 같다
```

```python
cmds.rename("joint_02", "new")   # (A)? (B)? → RuntimeError: Invalid path 'joint_02'
```

또 하나의 함정: **부모를 rename 하면 자식의 DAG 경로가 바뀐다.** 그래서 루프 시작 전에
자손 경로를 미리 모아두고 순회하면, 앞에서 부모를 바꾸는 순간 뒤쪽 자식 경로는 **무효**가 된다.

```python
paths = cmds.listRelatives(root, allDescendents=True, fullPath=True)  # 미리 수집
cmds.rename(paths[0], ...)   # 부모를 바꾸면...
cmds.rename(paths[1], ...)   # 이 경로는 이미 옛 경로 → 실패 가능
```

---

## 4. 해결 패턴 — UUID 로 신원을 잡고, 경로는 매번 다시 조회

UUID 는 rename·reparent 중에도 안 바뀌는 유일한 안정 핸들이다. 절차:

1. **입력 정규화**: 이름을 `cmds.ls(name, long=True)` 로 고유 경로화, 자손은 `fullPath=True` 로 수집.
2. **신원 확보**: 편집 전에 각 노드를 UUID 로 잡아둔다.
3. **배정 선계산**: `(uuid, 새 이름)` 목록을 **먼저 전부 계산**한다(부모부터 바꿔도 배정은 고정).
4. **경로 재해석 후 편집**: 실제 rename 직전에 `cmds.ls(uuid, long=True)` 로 **그 순간의 현재 경로**를
   다시 물어 rename 한다.

```python
def _to_uuid(node):
    """노드(이름/경로) → UUID. 실패 시 None."""
    uuids = cmds.ls(node, uuid=True) or []
    return uuids[0] if uuids else None


def _rename_by_uuid(uuid, new_name):
    """UUID 로 현재 경로를 다시 찾아 rename. 성공 시 새 이름, 없으면 None."""
    if not uuid:
        return None
    paths = cmds.ls(uuid, long=True) or []   # ← 지금 이 순간의 실제 경로
    if not paths:
        return None
    return cmds.rename(paths[0], new_name)


# 사용: 배정을 먼저 계산 → UUID 로 하나씩 rename
plan = [(_to_uuid(node), make_name(node)) for node in nodes]   # (1)(2)(3)
for uuid, new_name in plan:                                    # (4)
    _rename_by_uuid(uuid, new_name)
```

이렇게 하면 (A)/(B) 처럼 이름이 같아도, 부모를 먼저 바꿔 자식 경로가 변해도
항상 올바른 노드를 가리켜 실패하지 않는다.

---

## 5. 언제 이 패턴을 쓰나 / 유의점

- **적용 대상**: 노드를 **rename** 하거나, 미리 모아둔 경로로 나중에 편집하는 모든 코드
  (리네임 툴, 계층 일괄 편집, 선택 저장 후 재선택 등). 리스트가 short name 을 담는 순간 위험 신호.
- **UUID 조회**: `cmds.ls(node, uuid=True)` 로 얻고, `cmds.ls(uuid, long=True)` 로 되돌린다(Maya 2016+).
- **입력이 여러 노드로 해석될 때**: 이름이 모호하면 `cmds.ls(name, long=True)` 가 **여러 경로**를
  반환한다. 모두 처리할지, 첫 번째만 쓸지, 경고할지는 툴 정책으로 정한다.
- **읽기 전용 조회**엔 과할 수 있다. 씬을 바꾸지 않고 단발 조회만 한다면 fullPath 로 충분하다.
  UUID 는 **"편집 도중 신원이 바뀔 수 있는"** 상황에서 진가를 발휘한다.

---

## 6. 참고

- 실전 수정: [A00330_NamingTool](../A00330_NamingTool.md) §7 — Naming Dyn / Copy Name / Quick Rename
  전부 UUID 기반으로 하드닝(`app/core/naming_ops.py` 의 `_to_uuid` / `_rename_by_uuid`).
