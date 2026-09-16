# A00310_SearchTool 사용법

## 1. 개요

이 툴이 하는 일은 하나다 — **Objects 리스트에서 조건에 맞는 것만 골라 선택한다.**
다른 것은 **무엇으로 고르는가** 뿐이고, 그 기준이 탭이다.

| 탭 | 고르는 기준 | 출신 |
|----|-------------|------|
| **Type** | 노드 **타입** | 구 `JUN_PY_SelectionTool_V02_01` |
| **Token** | 오브젝트 **이름**(부분 문자열) | 구 `JUN_PY_SearchTool_V01_02` |
| **Rules** | 씬에서의 **상태** — 연결 · 히스토리 · 디포머 (v01.02~) | 신규 |

**대상 목록은 셋이 공유한다** — 창 위쪽의 **Source · Objects · Get · Invert** 는 탭 바깥에 있어,
한 번 `Get` 하면 어느 탭으로 옮겨도 같은 목록을 본다(4장).

**규칙(Rules)은 늘어나는 것을 전제로** 레지스트리에 모아 두었다. 규칙을 더하는 일은
**함수 하나 + 등록 한 줄**이고 **UI 코드는 건드리지 않는다**(7장).

- 모든 UI 문자열/로그는 영어. 리스트는 공용 위젯 `JUN_mod_tsl_qt_v01` 을 쓰며
  **Select 계열 + Add / Del / Up / Down / Sort** 버튼을 갖는다.
- 로직(선택/검색/규칙)은 `app/core`(maya.cmds), 화면은 `app/ui`(PySide)로 분리한다.

> **v01.03 에서 탭 구조가 바뀌었다.** 그전에는 상위 탭이 `Selection` / `Search` 였고 `Search` 만
> 하위 탭(`Token`/`Rules`)을 가졌다. `Selection` 도 결국 같은 일(리스트에서 조건에 맞는 것 고르기)이라
> **셋을 같은 층으로** 올렸고, 그러면 상위 탭이 하나만 남아 중첩이 의미가 없어지므로 중첩을 걷어냈다.
> **기능은 하나도 빠지지 않았다** — `Selection` 탭의 내용이 그대로 `Type` 탭이다.

---

## 2. 폴더 구조

```
A00310_SearchTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마(coral_dark) → show()
├── __dragDrop_A00310.py   # 셸프 버튼 설치 + 드래그&드롭 진입점 (TOOL_LABEL = "SearchTool")
├── icon/                  # 셸프 아이콘 (svg + png)
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존, maya.cmds)
    │   ├── maya_scene.py      # 선택/계층 펼치기/노드 타입/존재 (cmds 어댑터)
    │   ├── search_select.py   # collect_from_selection / collect_types /
    │   │                      #   select_by_types / select_by_token (+ CONSTRAINT_TYPES)
    │   ├── select_rules.py    # ★ 규칙 레지스트리 (Rules 탭, v01.02~)
    │   └── __init__.py        # core 재노출
    └── ui/main_window.py  # 전체 UI (공유 영역 + 탭 3 + 공유 로그창 + 메뉴 바)
```

- `main_window.py` 에서 **공유하는 것**(세 탭이 함께 쓰는 것)은 접두사 없이 둔다 —
  `objs_tsl` · `rb_hierarchy` / `rb_selected` · `cb_invert` · `_log()`.
  탭 전용 위젯만 탭 이름을 붙인다 — `type_types_tsl` · `token_le` · `rules_list`.

---

## 3. 설치 / 실행

- **설치**: `A00310_SearchTool/__dragDrop_A00310.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
  "SearchTool" 버튼이 설치된다(중복 버튼은 자동 제거).
- **실행**: 셸프 버튼 클릭, 또는 스크립트 에디터에서
  ```python
  import tools.A00310_SearchTool as A00310_SearchTool
  A00310_SearchTool.run(True)   # True 면 DEV_MODE 에서 Framework + 자기 자신 reload
  ```
- 창은 `objectName`(`JUN_A00310_SearchTool_window`)으로 관리되어 재실행 시 중복 없이 교체된다.

---

## 4. 공통 영역 — 세 탭이 함께 쓴다 (v01.03~)

창 위쪽의 **Source · Objects 리스트 · Get · Invert** 는 **탭 바깥**에 있고 세 탭이 함께 쓴다.
**한 번 `Get` 하면 Type / Token / Rules 어디로 옮겨도 같은 목록**을 대상으로 삼는다.

- **Source — Hierarchy / Selected**: `Get` 이 무엇을 대상으로 할지 정한다.
  - **Hierarchy**(기본): 선택한 오브젝트 각각의 **자손 transform 까지 펼쳐서** 대상으로 삼는다(shape 제외).
  - **Selected**: 현재 선택만 그대로 대상으로 삼는다.
- **Get**: 위 기준대로 Objects 리스트를 채운다.
- **Invert**: 선택 결과를 **여집합**으로 뒤집는다. 즉 Objects 리스트에서 조건에 **맞지 않는** 것을 선택한다.
  세 탭의 모든 선택 버튼에 함께 걸린다.

> Objects 리스트(TSL)의 버튼: **Get**(채우기) · **Add**(현재 선택 추가) · **Del** · **Up** · **Down** ·
> **Sort**(이름 정렬). 리스트 항목을 클릭하면 그 오브젝트가 씬에서 선택된다.

> **v01.02 까지는 탭마다 Objects 리스트·Get·Source·Invert 를 따로 갖고 있었다.** Token 에서 Get 해 놓고
> Rules 로 넘어가면 리스트가 비어 있어서 다시 모아야 했다. 같은 대상을 다른 기준으로 고르는 것이 이 툴의
> 전부인데 대상을 탭마다 다시 모으는 것은 앞뒤가 맞지 않아 v01.03 에서 하나로 합쳤다.

---

## 5. Type 탭 — 노드 타입으로 (구 Selection 탭)

Objects 리스트에 있는 것들의 **노드 타입**으로 고른다.

1. 위에서 **Get** → Objects 리스트를 채운다.
2. (선택) Types 리스트의 **List Types** → Objects 리스트에 있는 오브젝트들의 **노드 타입**(shape 가
   있으면 shape 타입, 없으면 transform 타입)을 정렬·중복제거해 채운다.
3. 원하는 방식으로 선택:
   - **Select By Shape**: 고정 버튼 — **Mesh / nurbsCurve / Joint / Constraint**. Objects 리스트 중 그
     타입인 것을 선택한다. (Constraint 는 `aim/orient/point/scale/parentConstraint` 5종을 모두 매칭)
   - **Select By Type (use selected types)**: Types 리스트에서 **선택한 타입들**과 일치하는 Objects 를 선택한다.

> **`List Types` 는 v01.03 부터 씬 선택이 아니라 Objects 리스트를 본다.** 다른 버튼들과 같은 대상을
> 보게 해서, 화면에 보이는 목록과 타입 목록이 어긋나지 않도록 한 것이다. 먼저 **Get** 을 눌러야 한다.

---

## 6. Token 탭 — 이름으로

1. **Search Token** 에 찾을 부분 문자열을 입력한다.
2. **Search By Token**(또는 토큰 입력 후 Enter) → Objects 리스트 중 이름에 토큰이 들어간 것을 선택한다.
   **Invert** 면 토큰이 **없는** 것을 선택한다.

---

## 7. Rules 탭 — 씬에서의 상태로 (v01.02~)

연결 · 히스토리 · 디포머처럼 **이름이 아니라 씬에서 어떤 상태인지**로 고른다.

1. 위에서 **Get** → Objects 리스트를 채운다.
2. **Rules** 목록에서 규칙을 고른다. **여러 개 고르면 AND** — 고른 규칙을 **전부** 만족하는 것만 남는다.
   고른 규칙의 설명은 목록 밑에 한 줄로 뜨고, 항목 툴팁에도 같은 글이 나온다.
3. **Select By Rules** → 맞는 것만 씬에서 선택한다(**Invert** 면 여집합).

**빠진 것은 이유가 로그에 남는다.** "12개 중 3개" 보다 "나머지 9개는 각각 이래서 제외" 가
쓸모 있기 때문이다. 리스트가 크면 앞에서 20줄까지만 적고 나머지는 개수로 알린다.

```
Select By Rules [Standalone] : 3 of 6 object(s).
    - dirty_hist : has history - polyCube1 (polyCube)
    - dirty_skin : has a deformer - skinCluster1 (skinCluster)
    - dirty_con  : driven by a constraint - dirty_con_parentConstraint1 (parentConstraint)
```

### 규칙 목록

| 규칙 | 통과 조건 |
|------|-----------|
| **Standalone** (v01.02~) | 연결도 히스토리도 없다 — 아무것도 이 노드를 구동하지 않고, 이 노드도 아무것도 구동하지 않는다 |

> **이름에 대해** — 요청은 `Get Pure` 였다. 바꾸어 달다 하셔서 **`Standalone`** 으로 놓았다.
> 이유는 두 가지다 — 이 툴에서 `Get` 은 **리스트를 채우는 버튼 이름**이라 규칙 이름에 들어가면
> 같은 단어가 두 가지 뜻으로 쓰이고, `Pure` 만으로는 **무엇으로부터 순수한지**가 안 드러난다.
> `Standalone` 은 "혼자 서 있다" 를 그대로 말한다. 그대로 `Get Pure` 를 쓰고 싶으시면
> `select_rules.py` 맨 아래 `register(...)` 의 두 번째 인자(라벨)만 바꾸면 된다.

### Standalone 이 무엇을 보는가

통과하려면 **네 가지가 전부 없어야** 한다 — 오른쪽은 로그에 찍히는 사유 이름이다.

| 검사 | 탈락 사유 | 예 |
|------|-----------|----|
| 컨스트레인트 | `driven by a constraint` | parent/point/orient/scale/aim… (걸린 쪽도, **드라이버 쪽도**) |
| 디포머 | `has a deformer` | skinCluster · blendShape 등 `geometryFilter` 상속 전부 |
| 히스토리 | `has history` | polyCube 같은 생성 노드, 애니메이션 커브 … |
| 어트리뷰트 연결 | `connected to …` | 들어오는 것도, **나가는 것도** |

**통과하는 것**(헷갈리기 쉬운 자리 — 전부 실측으로 고정했다):

- **머티리얼만 배정된 메시** — 히스토리 없이 만든 폴리큐브에도 `initialShadingGroup` 은 붙어 있다.
  이걸 연결로 치면 **어떤 메시도 통과하지 못한다.** 면 단위로 머티리얼이 여러 벌 붙은 것도 같다.
- **디스플레이 레이어 멤버 · 평범한 오브젝트 셋 멤버** — 리깅으로 엮인 것이 아니다.
- **그룹 밑에 부모만 있는 것** — 부모-자식은 DAG 관계지 DG 연결이 아니다. 그룹 밑에 넣었다고
  그 노드가 무언가에 구동되는 것은 아니다.

무시하는 타입 목록은 `select_rules.IGNORED_TYPES` 에 한데 모여 있다.

### ★ 규칙을 늘리는 법 — UI 는 안 고친다

규칙은 `app/core/select_rules.py` 의 **레지스트리**에 모인다. UI 는 `all_rules()` 를 그대로
그리므로, **함수 하나 + `register()` 한 줄**이면 목록에 저절로 나타난다.

```python
def _rule_my_thing(obj):
    if 조건에 맞지 않으면:
        return False, "왜 안 맞는지"      # 이 문장이 로그에 그대로 찍힌다
    return True, ""

register(SelectRule("my_thing", "My Thing", "한 줄 설명.", _rule_my_thing))
```

판정 함수는 `(맞는가, 안 맞는 이유)` 를 돌려준다. 이유를 함께 돌려주는 것이 이 구조의 핵심이다.

---

## 8. 로그 / About

- 두 탭의 모든 결과·경고(`[WARN]`)는 창 하단의 **공유 로그창**에 누적된다.
- **Help > About** 에 두 탭의 기능 설명이 표기된다.

---

## 로그창 (v01.01)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위에 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
