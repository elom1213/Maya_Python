# A00050_uvTool_V02 — UV Tool (사용 안내)

> **V01(`A00050_uvTool`, `maya.cmds` UI)에서 갈라져 나온 PySide 버전이다.** 폴더가 V02 이므로
> 버전도 **02.xx** 로 센다(`A00110_animTool_V02` = 02.00 과 같은 규칙).
> V01 은 손대지 않고 그대로 남아 있다.

메시의 **UV 세트를 규칙에 맞추는** 툴이다. 규칙은 하나다 —

> **메시는 `map1` 이라는 UV 세트 하나만 갖는다.**

UV 세트가 둘 이상이거나 이름이 다르면 익스포트·머티리얼 쪽에서 **엉뚱한 세트를 물게 된다.**
이 툴은 그 규칙에 어긋난 메시를 **찾아 주고**(`Catch Objects`), 첫 UV 세트의 **이름을 고친다**
(`Rename UV Set`).

- 버전: `v02.00` (`app/config/version.py`) — **PySide 이식 + 로그**
- 위치: `JUN_All/tools/A00050_uvTool_V02`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴. 검사·이름 정리 로직은 `app/core` 에 분리

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00050_V02.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`uvToolV2`** 버튼 설치.
아이콘은 툴 폴더의 `icon/A00050_uvTool_V02.png`(V01 과 같은 그림)을 쓴다.

### 코드로 실행
```python
import tools.A00050_uvTool_V02 as A00050_uvTool_V02
A00050_uvTool_V02.run(True)     # True 면 DEV_MODE 에서 리로드
```

---

## 2. 화면

```
┌──────────────────────────────────────────────┐
│ [메뉴 바]                            [ Pin ] │
│ One UV set per mesh, named 'map1'.           │
│ ┌ Objects ───────────────────────────────┐   │
│ │ [ Select Objects ]                      │   │
│ │ pCube1                                  │   │
│ │ [Add][Del][Up][Down] [Sort] [Reverse]   │   │
│ └─────────────────────────────────────────┘   │
│ ┌ Tool ──────────────────────────────────┐   │
│ │ ☑ Catch : look at every mesh in the scene│  │
│ │ ☑ Catch : select the offending meshes    │  │
│ │ [        Catch Objects        ]          │  │
│ │ [        Rename UV Set        ]          │  │
│ └─────────────────────────────────────────┘   │
│ ┌ 로그 (Expand / Clear / Copy) ───────────┐   │
│ └─────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

---

## 3. `Catch Objects` — 무엇이 왜 규칙에 어긋나는지

**규칙에 어긋난 메시를 찾아 ① 사유를 로그에 적고 ② 리스트에 담고 ③ 씬에서 선택한다.**
씬은 **아무것도 바뀌지 않는다**(조회 전용).

| 상태 | 뜻 | 로그 예 |
|------|-----|--------|
| `multiple` | UV 세트가 둘 이상 | `has 2 UV sets (map1, uvSet1) - only 'map1' should be there` |
| `wrong_name` | 하나뿐인데 이름이 다름 | `its only UV set is 'uvSet9', not 'map1'` |
| `no_uv` | UV 세트가 없음 | `has no UV set at all` |

```
Catch : checked 4 mesh(es) in the scene.
  [multiple] two_sets : has 2 UV sets (map1, uvSet1) - only 'map1' should be there
  [wrong_name] wrong_name : its only UV set is 'uvSet9', not 'map1'
       2 mesh(es) break the rule, 2 object(s) listed.
       Selected them in the scene.
```

- **`Catch : look at every mesh in the scene`**(기본 ON): 씬의 모든 메시를 본다(V01 과 같다).
  끄면 **리스트에 담긴 것만** 본다(리스트가 비면 씬 선택을 쓰고 그 사실을 로그에 적는다).
- **`Catch : select the offending meshes`**(기본 ON): 걸린 메시를 씬에서 선택한다.
- 규칙에 다 맞으면 `Every mesh follows the rule (one 'map1').` 이라고 말한다 —
  **아무 일도 안 일어난 것처럼 보이지 않게.**

> **V01 과 달라진 점**: V01 은 UV 세트가 **2개 이상인 것만** 찾았고, 리스트에 담기만 했다.
> V02 는 **이름이 다른 하나짜리·UV 세트 없음**까지 규칙 위반으로 보고, **사유**를 적고
> **씬에서 선택**한다.

---

## 4. `Rename UV Set` — 이름이 어떻게 바뀌었나

리스트에 담긴 오브젝트(비어 있으면 씬 선택)의 **첫 UV 세트**를 `map1` 으로 바꾼다.
**메시마다 한 줄씩** 바뀐 내용을 적는다. 전체가 **undo 한 스텝**.

```
  wrong_nameShape : uvSet9  ->  map1
  good_meshShape : map1  (already 'map1', left alone)
  [WARN] blocked_meshShape : uvSet1, map1  (not renamed - 'map1' already exists on this mesh)
Rename : 1 renamed, 2 left as they were.
       Ctrl+Z undoes the whole run.
```

| 상태 | 뜻 |
|------|-----|
| `renamed` | 첫 세트 이름을 `map1` 으로 바꿨다 — `before -> after` 를 적는다 |
| `already` | 이미 `map1` 하나뿐이라 할 일이 없다 |
| `extra` | 첫 세트는 `map1` 인데 **다른 세트가 더 있다** — 이 툴은 UV 세트를 **지우지 않는다** |
| `blocked` | 이미 `map1` 이 있어 **마야가 rename 을 거절**한다 |
| `failed` | 마야가 거절했다(잠김·레퍼런스 등) — 마야의 메시지를 그대로 적는다 |
| `no_uv` / `not_mesh` / `missing` | UV 세트 없음 / 메시 아님 / 씬에 없음 |

> **★ V01 은 이 실패들을 조용히 삼켰다.** `try: ... except: pass` 였기 때문에,
> `['map1', 'uvSet1']` 같은 메시는 **아무 일도 일어나지 않았는데 성공처럼 보였다.**
> V02 는 미리 판정해서 **사유를 적는다.**

---

## 5. mayapy(2024) 로 확인한 것 ★

- `polyUVSet` 은 **오브젝트를 인자로 받는다**(트랜스폼·셰이프 둘 다). V01 처럼
  `cmds.select` 로 고른 뒤 부를 필요가 없다 → **씬 선택을 건드리지 않는다.**
- **이미 있는 이름으로 rename 하면 에러**다 —
  `RuntimeError: Cannot rename uv set to an existing uv set name.`
  `map1` -> `map1` 도 같은 에러라 **이미 맞는 메시는 시도하지 않는다.**
- **기본 UV 세트는 지울 수 없다** — `The default uv set cannot be deleted.`
  그래서 이 툴은 **지우지 않고 이름만 고친다**(`extra` 상태가 그 한계를 말해 준다).
- `ls(type="mesh")` 는 **중간(Orig) 셰이프까지** 준다(디포머가 붙은 메시).
  같은 트랜스폼이 두 번 걸리므로 `noIntermediate=True` 로 거른다 — **V01 은 걸러지 않았다.**
- UV 세트 rename 은 **undo 된다** → 전체를 `undo_chunk()` 로 묶어 Ctrl+Z 한 번.
- 첫 세트는 `polyUVSet(q=allUVSets)` 의 **순서 그대로**이고 `currentUVSet` 과 다를 수 있다
  (V01 과 같은 기준을 유지했다).

---

## 6. 구조

```
A00050_uvTool_V02/
├─ launch.py                    # run() — 창 재생성 방지 + 테마(coral_dark)
├─ __dragDrop_A00050_V02.py     # 셸프 버튼 설치
├─ icon/A00050_uvTool_V02.png|.svg
└─ app/
   ├─ config/version.py
   ├─ core/uv_set_manager.py    # 검사(find_offenders) + 이름 정리(rename_first_uv_set)
   └─ ui/main_window.py         # 창 · 리스트 · 버튼 2개 · 로그 · Pin · 메뉴
```

V01 의 `utility.py` 두 함수가 `app/core/uv_set_manager.py` 로 옮겨지면서
**UI 비의존**(리스트 위젯을 인자로 받지 않음)이 되어 headless 로 검증할 수 있게 됐다.

---

## 7. 검증

`mayapy` (Maya 2024) 헤드리스 **42항목 통과** (코어 + 오프스크린 Qt UI).

**코어** — 씬 전체 검사 · 정상 메시는 안 걸림 · `multiple` / `wrong_name` 사유 문구 ·
커브는 보지 않음 · 트랜스폼으로 보고 · **Catch 가 씬을 안 바꿈** · **Orig 셰이프 중복 없음** ·
리스트 한정 검사 · rename 성공/`already`/`extra`/`blocked`/`not_mesh`/`missing` ·
세트 둘 다 map1 이 아니면 **첫 것**이 map1 이 됨 · **undo 한 스텝** ·
**rename 이 씬 선택을 안 건드림**(V01 은 `cmds.select` 를 썼다).

**UI** — 버튼·리스트·로그 존재 · Catch 로그(검사 수 · 메시별 사유 · 정상 메시는 안 적음) ·
리스트 채우기 · 씬 선택 · Rename 로그(`before -> after` · 사유 · 요약) ·
빈 리스트 경고 · 리스트 한정 Catch · 빈 리스트면 씬 선택으로 넘어가며 그 사실을 알림 ·
규칙에 다 맞는 씬.

창 최소 크기 **533 x 736**, 기본 **560 x 780**.

---

## 로그창

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다(`Expand` / `Clear` / `Copy`).
자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
