# A00050_uvTool_V02 — UV Tool (사용 안내)

> **V01(`A00050_uvTool`, `maya.cmds` UI)에서 갈라져 나온 PySide 버전이다.** 폴더가 V02 이므로
> 버전도 **02.xx** 로 센다(`A00110_animTool_V02` = 02.00 과 같은 규칙).
> V01 은 손대지 않고 그대로 남아 있다.

메시의 **UV 세트를 규칙에 맞추는** 툴이다. 규칙은 하나다 —

> **메시는 `map1` 이라는 UV 세트 하나만 갖는다.**
>
> (`map1` 은 **기본값**이다 — v02.01 부터 원하는 이름을 화면에서 입력한다, §3)

UV 세트가 둘 이상이거나 이름이 다르면 익스포트·머티리얼 쪽에서 **엉뚱한 세트를 물게 된다.**
이 툴은 그 규칙에 어긋난 메시를 **찾아 주고**(`Catch Objects`), 첫 UV 세트의 **이름을 고친다**
(`Rename UV Set`).

- 버전: `v02.02` (`app/config/version.py`) — **PySide 이식 + 로그**,
  **바꿀 UV 세트 이름을 화면에서 입력**(§3) · 리스트 옆 **UV Sets 표** + 로그의 `[wrong_name]` 빨간색(§2.1, v02.02) · **`Delete UV Sets`**(§4.1, v02.03)
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
│ ┌ Objects ─────────┐┌ UV Sets   1 / 3 OK ─────┐│
│ │ [ Select Objects ]││ Object UV Sets    Rule  ││
│ │ good             ││ good   map1       OK    ││
│ │ wrong            ││ wrong  uvA        wrong_name ││
│ │ multi            ││ multi  map1, uvB  multiple ││
│ │ [Add][Del][Up]...││                         ││
│ └──────────────────┘└─────────────────────────┘│
│ ┌ Tool ──────────────────────────────────┐   │
│ │ UV set name [ map1            ] [ map1 ] │  │
│ │ ☑ Catch : look at every mesh in the scene│  │
│ │ ☑ Catch : select the offending meshes    │  │
│ │ [        Catch Objects        ]          │  │
│ │ [ Delete UV Sets ] [ Rename UV Set ]     │  │
│ └─────────────────────────────────────────┘   │
│ ┌ 로그 (Expand / Clear / Copy) ───────────┐   │
│ └─────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### 2.1 UV Sets 표 (v02.02)

리스트 옆에 **오브젝트마다 UV 세트 이름들과 규칙에 맞는지**를 세 칸으로 보여 준다
(A00330_NamingTool Quick Rename > Insert 의 Preview 와 같은 형식 — 줄 선택 없음 · 줄무늬).

| 칸 | 내용 |
|----|------|
| `Object` | 트랜스폼 이름(툴팁 = 셰이프 롱네임). 셰이프가 여럿이면 셰이프마다 한 행 |
| `UV Sets` | 그 메시의 UV 세트 전부, `polyUVSet(q=allUVSets)` 순서. 없으면 `-` |
| `Rule` | `OK`(초록) 또는 `multiple` / `wrong_name` / `no_uv` / `not_mesh` / `missing`(빨강). 툴팁 = 사유 |

- 제목에 `UV Sets   k / n OK` 로 맞은 수를 적는다.
- **다시 그리는 때**: 리스트가 바뀔 때(Select / Add / Del / Up / Down / Sort / Catch),
  `UV set name` 칸을 고칠 때(규칙이 바뀌므로), `Rename UV Set` 뒤. 씬은 바꾸지 않는다.
- 메시가 아니거나 씬에 없는 항목도 **행으로 남긴다** — 리스트에 올린 것이 표에서 조용히 사라지면 왜 빠졌는지 알 수 없다.
- 로그의 **`[wrong_name]` 줄은 빨간색**이다(공용 로그 색 규칙의 `[ERROR]` 빨강, 밝은 테마는 진한 빨강).
  `[wrong_name]` 은 밑줄이 있어 공용 표식 규칙(글자만)에 걸리지 않으므로 툴이 HTML 로 칠해 넣는다.
- 창 기본 폭을 560 → **720** 으로 넓혔다(표가 보이게). 최소 크기 533 x 772 는 그대로.

> **A00380_MeshTool 로 옮길 예정**이다. 표는 `app/ui/uv_set_table.py`(Framework · Qt 에만 기댐,
> 툴 코드를 import 하지 않음), 행 데이터는 코어 `uv_set_manager.inspect()` 라 두 파일을 그대로 가져가면 된다.

---

## 3. `UV set name` — 어떤 이름으로 맞출지 (v02.01~)

**칸 하나가 두 버튼을 함께 정한다.**

| 쓰는 곳 | 뜻 |
|---------|-----|
| `Rename UV Set` | 첫 UV 세트를 **이 이름으로** 바꾼다 |
| `Catch Objects` | **이 이름 하나만** 가진 메시를 "규칙에 맞다" 고 본다 |

둘을 따로 두면 **잡아서 고쳤는데 여전히 위반**이 되므로 한 칸으로 묶었다.
기본값은 `map1` 이고, 오른쪽 **`map1` 버튼**이 기본값을 되돌린다.
창 위의 규칙 문장도 입력에 따라 바뀐다 — `One UV set per mesh, named 'uvMap'.`

> **마야가 거절하는 것은 빈 이름뿐이다** — `Invalid new uv set name specified`.
> 공백(`UV Map`) · `-` · `.` · `:` · `|` · 숫자 시작까지 **마야는 그대로 받는다**(실측).
> 그래서 막지 않고 **앞뒤 공백만 떼고**(오타일 가능성이 크다) 그 사실을 로그에 적는다.
> 빈 이름이면 **실행하지 않고** 마야의 문구를 그대로 보여 준다.

---

## 4. `Catch Objects` — 무엇이 왜 규칙에 어긋나는지

**규칙에 어긋난 메시를 찾아 ① 사유를 로그에 적고 ② 리스트에 담고 ③ 씬에서 선택한다.**
씬은 **아무것도 바뀌지 않는다**(조회 전용).

| 상태 | 뜻 | 로그 예 |
|------|-----|--------|
| `multiple` | UV 세트가 둘 이상 | `has 2 UV sets (map1, uvSet1) - only 'map1' should be there` |
| `wrong_name` | 하나뿐인데 이름이 다름 | `its only UV set is 'uvSet9', not 'map1'` |
| `no_uv` | UV 세트가 없음 | `has no UV set at all` |

```
Catch : checked 4 mesh(es) in the scene, wanting one 'map1'.
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

## 4.1 `Delete UV Sets` — 규칙 이름이 아닌 세트 지우기 (v02.03)

`Rename UV Set` **왼쪽** 버튼. 리스트의 오브젝트(비면 씬 선택)에서 **`UV set name` 칸의 이름이 아닌
UV 세트를 모두 지운다.** 전체가 **undo 한 스텝**이고, 끝나면 UV Sets 표를 다시 그린다.

★ **마야는 첫 번째(기본) UV 세트를 지우지 못한다** — 이름이 무엇이든 `allUVSets` 의 첫 세트면
`The default uv set cannot be deleted.`(mayapy 2024 실측). 그래서 결과가 넷으로 갈린다.

| 메시의 UV 세트 | 결과 | 로그 |
|---|---|---|
| `map1, uvB, uvC` | 지움 → `map1` | `multiShape : map1, uvB, uvC  ->  map1` |
| `map1` | 할 일 없음 | `(only 'map1', nothing to delete)` |
| `uvA, map1, uvZ` | **지울 수 있는 것만** → `uvA, map1` | `[WARN] ... ('uvA' is the default (first) UV set and Maya cannot delete it)` |
| `uvA` (규칙 이름 없음) | **하나도 안 지움** | `[WARN] ... there is no 'map1' to keep - rename a set to 'map1' first` |

- 규칙 이름이 아예 없는 메시를 건드리지 않는 이유: 지워 봐야 규칙 이름은 생기지 않고 UV 만 잃는다. `Rename` 이 먼저다.
- 현재(current) UV 세트를 지우면 마야가 현재 세트를 기본 세트로 넘긴다.
- 지울 때마다 히스토리에 `deleteUVSet` 노드가 하나씩 생긴다(스킨이 붙은 메시도 지워진다).
- 확인 대화상자는 없다 — `Rename` 과 같이 로그에 before -> after 를 남기고, `Ctrl+Z` 한 번으로 전부 돌아간다.

---

## 5. `Rename UV Set` — 이름이 어떻게 바뀌었나

리스트에 담긴 오브젝트(비어 있으면 씬 선택)의 **첫 UV 세트**를 **`UV set name` 에 적은 이름**(기본 `map1`)으로 바꾼다.
**메시마다 한 줄씩** 바뀐 내용을 적는다. 전체가 **undo 한 스텝**.

```
Rename : first UV set -> 'map1' on 3 object(s).
  wrong_nameShape : uvSet9  ->  map1
  good_meshShape : map1  (already 'map1', left alone)
  [WARN] blocked_meshShape : uvSet1, map1  (not renamed - 'map1' already exists on this mesh)
       1 renamed, 2 left as they were.
       Ctrl+Z undoes the whole run.
```

| 상태 | 뜻 |
|------|-----|
| `renamed` | 첫 세트 이름을 **적은 이름**으로 바꿨다 — `before -> after` 를 적는다 |
| `already` | 이미 그 이름 하나뿐이라 할 일이 없다 |
| `extra` | 첫 세트는 그 이름인데 **다른 세트가 더 있다** — 이 툴은 UV 세트를 **지우지 않는다** |
| `blocked` | 그 이름의 세트가 이미 있어 **마야가 rename 을 거절**한다 |
| `failed` | 마야가 거절했다(잠김·레퍼런스 등) — 마야의 메시지를 그대로 적는다 |
| `no_uv` / `not_mesh` / `missing` | UV 세트 없음 / 메시 아님 / 씬에 없음 |

> **★ V01 은 이 실패들을 조용히 삼켰다.** `try: ... except: pass` 였기 때문에,
> `['map1', 'uvSet1']` 같은 메시는 **아무 일도 일어나지 않았는데 성공처럼 보였다.**
> V02 는 미리 판정해서 **사유를 적는다.**

---

## 6. mayapy(2024) 로 확인한 것 ★

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

## 7. 구조

```
A00050_uvTool_V02/
├─ launch.py                    # run() — 창 재생성 방지 + 테마(coral_dark)
├─ __dragDrop_A00050_V02.py     # 셸프 버튼 설치
├─ icon/A00050_uvTool_V02.png|.svg
└─ app/
   ├─ config/version.py
   ├─ core/uv_set_manager.py    # 검사(find_offenders · inspect) + 이름 정리(rename_first_uv_set) + 삭제(delete_other_uv_sets)
   ├─ ui/uv_set_table.py        # UV Sets 표 + [wrong_name] 빨간 로그 줄 (v02.02, 이식 단위)
   └─ ui/main_window.py         # 창 · 리스트 | 표 · 이름 칸 · 버튼 2개 · 로그 · Pin · 메뉴
```

V01 의 `utility.py` 두 함수가 `app/core/uv_set_manager.py` 로 옮겨지면서
**UI 비의존**(리스트 위젯을 인자로 받지 않음)이 되어 headless 로 검증할 수 있게 됐다.

---

## 8. 검증

`mayapy` (Maya 2024) 헤드리스 **57항목 통과** (코어 + 오프스크린 Qt UI).

**코어** — 씬 전체 검사 · 정상 메시는 안 걸림 · `multiple` / `wrong_name` 사유 문구 ·
커브는 보지 않음 · 트랜스폼으로 보고 · **Catch 가 씬을 안 바꿈** · **Orig 셰이프 중복 없음** ·
리스트 한정 검사 · rename 성공/`already`/`extra`/`blocked`/`not_mesh`/`missing` ·
세트 둘 다 map1 이 아니면 **첫 것**이 map1 이 됨 · **undo 한 스텝** ·
**rename 이 씬 선택을 안 건드림**(V01 은 `cmds.select` 를 썼다).

**UI** — 버튼·리스트·로그 존재 · Catch 로그(검사 수 · 메시별 사유 · 정상 메시는 안 적음) ·
리스트 채우기 · 씬 선택 · Rename 로그(`before -> after` · 사유 · 요약) ·
빈 리스트 경고 · 리스트 한정 Catch · 빈 리스트면 씬 선택으로 넘어가며 그 사실을 알림 ·
규칙에 다 맞는 씬.

**이름 칸 15항목 (v02.01)** — 기본값 `map1` · 규칙 문장이 입력을 따라 바뀜 ·
Rename 이 **입력한 이름**을 씀 · **Catch 가 같은 이름으로 판정**(이름을 바꾸면 같은 메시가
위반이 되었다가 안 되었다가) · `map1` 버튼 · **빈 이름은 두 버튼 모두 거절**(마야 문구 그대로) ·
거절 뒤 씬 불변 · 앞뒤 공백 제거 + 칸에도 반영 · 공백이 낀 이름(`UV Map`)은 그대로 통과 ·
코어 기본값은 여전히 `map1`.

창 최소 크기 **533 x 772**, 기본 **560 x 820**.

---

## 로그창

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다(`Expand` / `Clear` / `Copy`).
자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
