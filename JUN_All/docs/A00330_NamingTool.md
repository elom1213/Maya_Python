# A00330_NamingTool 사용법

## 1. 개요

씬 오브젝트의 **이름을 일괄 변경**하는 PySide(Qt) 툴이다. 레거시 maya.cmds 단일 파일 툴
`JUN_PY_NamingTool_V03_04` 를 `A00310_SearchTool` 과 같은 **하나의 창 + 탭** 구조로 이식했고,
원본 2개 탭에 더해 `ref/ref_01.mel`(현장용 빠른 리네임)을 **3번째 탭**으로 통합했다.

1. **Rename** (v01.07 상위 탭) — 이름을 **짓고 바꾸는** 두 하위 탭을 묶었다.
   - **Token** (구 Naming Dyn) — 오브젝트와 그 transform 자손을 **토큰 규칙**으로 일괄 리네임.
     토큰 칸마다 `Custom`(글자) / `Numbering`(Start + Pad 0)을 고르고, 칸 수는 `Add Token` / `Delete Token` 으로 자유.
     규칙 한 벌은 **Profile**(json)로 저장·불러오기(§6.1).
   - **Set Rename** — 아래 4번.
2. **Copy Name** — Base 리스트의 leaf 이름(+Prefix)을 Targets 리스트에 순서대로 적용. (구 Copy name 탭)
   **Search / Replace** 로 Base 이름 속 단어를 바꿔서 복사할 수도 있다(v01.05).
3. **Quick Rename** — 하위 탭 두 개(v01.09).
   - **Selection** — **현재 선택** 기준으로 앞/뒤 글자 추가·제거, 새 이름+인덱스 부여. (`ref/ref_01.mel` 이식)
   - **Insert** — 리스트에 담은 오브젝트 이름의 **n 번째 자리**에 글자를 넣는다. 음수는 끝에서부터 센다.
     미리보기 표로 결과를 먼저 보고 **Apply** 를 눌러야 바뀐다(§6.3.1).
4. **Set Rename** (Rename 의 하위 탭) — **세트 이름**의 부분 문자열 찾아 바꾸기. 마야 기본 `Search and Replace Names` 는
   세트를 고를 수 없다(§6.4). (v01.02 신규)

- 모든 UI 문자열/로그는 영어. 리스트(TSL)는 공용 위젯 `JUN_mod_tsl_qt_v01`(**Select / Add / Del / Up / Down / Sort**)을 쓴다.
- 로직(리네임)은 `app/core`(maya.cmds), 화면은 `app/ui`(PySide)로 분리한다. 모든 작업은 **단일 Undo** 로 묶인다.

---

## 2. 폴더 구조

```
A00330_NamingTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마(green_dark) → show()
├── __dragDrop_A00330.py   # 셸프 버튼 설치 + 드래그&드롭 진입점 (TOOL_LABEL = "NamingTool")
├── icon/                  # 셸프 아이콘 (svg + png 64/32)
├── ref/ref_01.mel         # Quick Rename 원본 (참고)
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존, maya.cmds)
    │   ├── naming_ops.py      # rename_tokens(v01.07) / rename_dynamics / copy_name / insert_front /
    │   │                      #   add_rear / change_new / trim_front / trim_rear / all_apply
    │   ├── token_ops.py       # 이 툴의 규칙 묶음(MAYA_NODE_RULES) + 레거시 기본값 - 본체는 Framework/core/token_naming (v01.10)
    │   ├── token_profile_prefs.py  # Token 프로파일 저장소(STORE) - v01.10 부터 공용 TokenProfileStore
    │   ├── set_rename_ops.py  # Set Rename
    │   ├── insert_ops.py      # Quick Rename > Insert - 위치 규칙 · 미리보기 · 적용 (v01.09)
    │   └── __init__.py        # core 재노출
    ├── ui/main_window.py  # 창 · 상위 탭(Rename / Copy Name / Quick Rename) · Set Rename · 공유 로그창 · 메뉴 바
    └── ui/token_tab.py    # Rename > Token 탭 = Objects + 공용 토큰 위젯 + Rename (v01.10)
data/                      # (git 추적 안 함) Token 프로파일 - token_profiles/<이름>.json + token_profiles_active.json
```

- 위젯/핸들러는 탭별로 나눈다: **Token = `ui/token_tab.py`**, **Copy Name = `copy_*`**, **Quick Rename = `qr_*`(Selection) / `ins_*`(Insert)**, **Set Rename = `sr_*`**.
  공유하는 것은 `self._log()`(공용 로그창)뿐이다.

---

## 3. 설치

`A00330_NamingTool/__dragDrop_A00330.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
"NamingTool" 버튼이 설치된다(중복 버튼은 자동 제거).

---

## 4. 실행

- **셸프 버튼** 클릭, 또는 스크립트 에디터에서:
  ```python
  import tools.A00330_NamingTool as A00330_NamingTool
  A00330_NamingTool.run(True)   # True 면 DEV_MODE 에서 Framework + 자기 자신 reload
  ```
- 창은 `objectName`(`JUN_A00330_NamingTool_window`)으로 관리되어 재실행 시 중복 없이 교체된다.
- PySide2(Maya ~2024) / PySide6(2025+) 양쪽 지원(`Framework.qt.qt` 자동 분기).

---

## 5. UI 구성

- **상단 탭**: Rename(하위 탭 **Token** / **Set Rename**) / Copy Name / Quick Rename(하위 탭 **Selection** / **Insert**, v01.09).
- **하단 공유 로그창**: 모든 결과·경고(`[WARN]`)가 누적된다.
- **Help > About**: 세 탭의 기능 요약.
- 리스트(TSL)의 버튼: **Select**(현재 선택으로 교체) · **Add**(현재 선택 추가) · **Del** · **Up** · **Down** · **Sort**.
  리스트 항목을 클릭하면 그 오브젝트가 씬에서 선택된다.

---

## 6. 사용 순서

### 6.1 Rename > Token 탭 (v01.07, 구 Naming Dyn)

> v01.10 : Profile + Tokens 화면은 공용 위젯 [Framework_MOD_tokenName_qt](Framework_MOD_tokenName_qt.md) 이다.
> [A00480_FileTool](A00480_FileTool.md) Export > Naming 도 같은 위젯을 쓴다(그쪽은 규칙 `Set's Name` 이 하나 더 있다). 보이는 것 · 동작 · 프로파일 파일은 v01.09 와 같다.

```
┌ Objects ──────────────┬ Preview (v01.15) ──────────────────────────────┐
│ (Select Base / Add /  │ Current │ New name                    │ Status  │
│  Del / Up / Down /    │ v setGrp│ SIN_n_Set008_..._01_geo     │ OK      │
│  Sort)                │    acc1 │ SIN_n_Set008_..._02_geo     │ OK      │
├ Profile ───────────────────────────────┤
│ [Default        v] [Save] [New] [Rename] [Delete]
├ Tokens ────────────────────────────────┤
│ [Add Token] [Delete Token]
│ ┌Token 1┐┌Token 2┐┌Token 3┐┌Token 4──┐┌Token 5──┐  <- 가로 스크롤 ->
│ │Custom ││Custom ││Custom ││Numbering││Numbering│
│ │ Text  ││ Text  ││ Text  ││ Start   ││ Start   │   <- 이름 줄 (v01.13 - 모든 칸)
│ │[dyn  ]││[asset]││[side ]││ [0]     ││ [0]     │   <- 입력칸 - 같은 줄 · 같은 높이
│ │       ││       ││       ││ Pad 0   ││ Pad 0   │
│ │       ││       ││       ││ [2]     ││ [2]     │
│ Preview : dyn_asset_side_00_00 -> next node dyn_asset_side_00_01 | next object dyn_asset_side_01_00
└────────────────────────────────────────┘
[ Rename ]
```

**쓰는 법**

1. 씬에서 루트 오브젝트들을 선택하고 **Select Base** → Objects 리스트에 채운다(순서가 곧 오브젝트 번호 순서).
2. **Profile** 에서 규칙을 고른다. 처음 열면 레거시 규칙 그대로인 **`Default`** 가 만들어져 있다
   (`dyn_asset_side_{번호}_{번호}`, Pad 0 은 둘 다 2).
3. 필요하면 토큰 칸을 고친다 — **고쳐도 저장되지 않는다**(v01.11~). 기본으로 남기려면 Profile 줄의 **`Save`**. `Preview` 줄에서 결과 이름을 미리 본다.
4. 오른쪽 **Preview 표**(v01.15)에서 결과를 본다 — Rename 으로 바뀔 노드 **전부**(오브젝트 + transform 자손)가 계층 그대로
   `Current` → `New name` 과 `Status` 로 나온다. 리스트나 토큰 칸이 바뀌면 바로 다시 계산한다(씬은 그대로).
5. **Rename** → 각 오브젝트와 그 transform 자손이 토큰을 `_` 로 이은 이름으로 바뀐다. **Undo 한 번**으로 되돌아간다.
   Rename 왼쪽 **`Hierarchy`**(v01.18) 를 끄면 **리스트의 오브젝트만** 바뀌고 자손은 그대로다(기본은 켜짐 = 예전 동작).
   Preview 표도 체크를 따라간다.
   바뀐 뒤 Objects 리스트는 새 이름으로 갱신된다(v01.15).

**Preview 표의 Status** (v01.15) — Quick Rename > Insert 와 같은 규칙.

| Status | 뜻 |
|---|---|
| `OK` (초록) | 그대로 바뀐다 |
| `name taken` (노랑) | 같은 부모 아래에 그 이름이 이미 있다 → 마야가 번호를 붙인다. **이름을 차례로 바꾸는 과정을 흉내 내서** 판정한다 — 곧 다른 이름으로 바뀔 형제의 이름을 받는 건 괜찮고, 이 배치에서 이미 쓴 이름이나 배치 밖 노드의 이름과 겹칠 때만 |
| `no change` (회색) | 이미 그 이름이다 |
| `token error` | 토큰 칸 문제(Preview 줄의 `[WARN]` 과 같은 내용) — Rename 이 실행되지 않는다 |
| `invalid name` / `locked` / `referenced` / `default node` / `gone` | 바꿀 수 없는 노드 — Rename 이 **그 노드만 건너뛰고** 로그에 `[Warning]`. v01.14 까지는 잠긴 노드에서 예외로 멈췄다 |

- 계산은 `core.preview_tokens` — Rename(`rename_tokens`)과 **같은 순서 · 같은 이름**이다(Maya 2024 에서 미리보기 = 실제 결과 대조).
- 토큰을 칠 때마다 씬을 조회하지 않도록 갱신을 150ms 모은다.
- **세 칸은 색이 다르다**(v01.16) — Current 파랑 · New name 보라 · Status 회색, 머리글까지. 반투명이라 테마 바탕 위에 얹힌다
  (어두운 테마는 조금 진하게). 머리글은 테마 qss 가 배경을 덮어쓰므로 테마가 그린 위에 덧칠한다(`TintedHeader`).

**토큰 규칙** (칸 밑의 콤보)

| 규칙 | 입력 | 결과 |
|------|------|------|
| `Custom` | 글자 | 적은 글자 그대로. **비워 두면 그 토큰은 건너뛴다**(`a__b` 가 생기지 않는다) |
| `Enum` (v01.12) | 값 콤보 · `Values...` | **정해진 값 중 고른 하나**. 타이핑하지 않으므로 오타가 없다. 칸 위에 칸 이름(role, 예: `character`)이 보인다. `Values...` 로 칸 이름과 값 목록(쉼표로 구분)을 고친다 — **개발자 모드에서만**(v01.14, 아래) |
| `Numbering` | `Start`(시작 정수) · `Pad 0`(자리수) | Start 부터 올라가는 번호, Pad 0 자리까지 0 을 채운다(Pad 2 → `00, 01, …`, 자리수를 넘으면 `123` 그대로) |

**개발자 모드 / 배포본** (v01.14) — 정해진 규칙(Enum 칸)을 공유받은 사람이 바꾸지 못하게 한다.

| | 개발자 모드 (`JUN_All/config.py` 의 `DEV_MODE = True`) | 배포본 (릴리즈 저장소) · `DEV_MODE = False` |
|---|---|---|
| `Values...` (칸 이름 · 값 목록 편집) | 있음 | **없음** |
| Enum 칸의 규칙 콤보 | 바꿀 수 있음 | **잠김**(회색) — Custom 으로 바꿔 아무 글자나 넣는 길을 막는다 |
| `Add Token` / `Delete Token` | 있음 | **없음** (v01.17) — 칸 구성 자체가 정해진 규칙이다 |
| Enum 칸 삭제 | 됨 | **안 됨** (코드에서도 막는다 — `[WARN] Token N is a fixed rule and cannot be deleted.`) |
| 다른 칸의 규칙 콤보 | Custom / Enum / Numbering | Custom / Numbering (값 목록을 만들 수 없으니 Enum 을 뺀다) |
| Enum 값 고르기 · Custom · Numbering · Save | 됨 | 됨 |
| 다른 탭 (Set Rename · Copy Name · Quick Rename) | 됨 | **잠김**(회색 글자, 툴팁에 `Not available in the shared tool`) — Rename > Token 만 (v01.17) |
| `Dev Mode` 토글 (Tokens 줄 오른쪽) | **있음** — 끄면 배포 화면을 그대로 본다, 다시 켜면 개발 화면 | 없음 |

- 판정은 `app/config/dev_mode.py` — `launch.py` 와 같은 규칙: 툴 폴더 안에 `Framework` 가 동봉돼 있으면 배포본(항상 잠금),
  아니면 `JUN_All/config.py` 의 `DEV_MODE`(경로로 읽는다 - `import config` 는 다른 툴의 config.py 를 집을 수 있다).
- 프로파일 json 을 직접 고치는 것까지 막지는 않는다 — 화면에서 규칙을 바꾸는 길만 닫았다.
- `Dev Mode` 를 바꿔도 지금 칸 · 저장 안 한 변경(Save 상태)은 그대로다. 잠글 때는 Rename > Token 탭으로 옮긴다.

> **팀 이름 규칙(SetXXX)** 은 프로파일 **`Dnable_Set_v001`** 로 짓는다 — 캐릭터 · 좌우 · 파츠 · 오브젝트종류가 Enum 칸이다.
> 규칙과 쓰는 법은 [A00330_NamingRule_Set.md](A00330_NamingRule_Set.md) (팀 공유용).

**Numbering 토큰 개수 = 무엇을 세는지** — 레거시 Index 1 / Index 2 와 같은 규칙이다.

| 개수 | 세는 것 | 예 (오브젝트 2개, 각각 노드 2개) |
|------|---------|------|
| 1 개 | 이름을 바꾸는 **노드 전부를 순서대로** (오브젝트가 바뀌어도 이어진다) | `jnt_001, jnt_002, jnt_003, jnt_004` |
| 2 개 | 앞 = **오브젝트마다** +1, 뒤 = **오브젝트 안의 노드마다** +1(오브젝트가 바뀌면 Start 로) | `a_00_00, a_00_01, a_01_00, a_01_01` |
| 0 개 | 번호 없음 — 모든 노드가 같은 이름을 원하게 된다. 마야가 번호를 붙이면 로그에 `[Warning]` | |
| 3 개 이상 | 셀 대상이 없어 **실행하지 않는다** (`Preview` 와 로그에 `[WARN]`) | |

**토큰 칸 늘리고 줄이기**

- 칸 머리(`Token N`)를 누르면 그 칸이 **골라진다**(노랗게 표시). 처음엔 마지막 칸이 골라져 있다.
- **`Add Token`** — 고른 칸 **오른쪽**에 빈 `Custom` 칸을 넣고 그 칸을 고른다.
- **`Delete Token`** — 고른 칸을 지우고 그 자리의 이웃 칸을 고른다. **마지막 한 칸은 지울 수 없다.**
- 칸이 창 폭보다 많아지면 **가로 스크롤**이 생긴다. 칸 수가 늘어도 창의 최소 폭은 늘지 않는다.
- **입력칸은 모든 칸에서 같은 줄 · 같은 높이**(v01.13) — 칸마다 입력칸 위에 이름 줄(`Text` / Enum 칸 이름 / `Start` / `Set`)이 있고,
  높이는 테마를 입힌 글자 칸 · 스핀박스 중 큰 쪽으로 맞춘다. 전에는 Enum 값 콤보가 낮고 Custom 입력칸이 한 줄 위에 붙어 있었다(`ref/ref_02.png`).
- 칸 폭은 **80px**(v01.08, 처음 120px 의 2/3). 이 폭에 맞추려고 규칙 콤보의 여백을 줄이고 `Start` / `Pad 0` 라벨을 스핀박스 위에 둔다.

**Profile** (A00145 `Attribute > Create` 의 Profile 과 같은 구성)

| 버튼 | 동작 |
|------|------|
| 콤보 | 프로파일을 바꾸면 그 규칙으로 칸을 다시 만든다. 마지막으로 쓴 프로파일은 다음에 열 때도 그대로 |
| `Save` | **지금 칸을 지금 프로파일의 기본으로 저장**(v01.11~). 저장 안 한 변경이 있을 때만 켜진다. 누르지 않으면 프로파일을 바꾸거나 툴을 닫을 때 버려진다 |
| `New` | **지금 칸을 복사해** 새 프로파일을 만들고 그쪽으로 바꾼다(같은 이름은 거절) |
| `Rename` | 지금 프로파일 이름 바꾸기 |
| `Delete` | 지금 프로파일 삭제(확인 창). **마지막 하나는 남긴다** |

- 저장 위치: `A00330_NamingTool/data/token_profiles/<이름>.json`, 활성 프로파일은 `data/token_profiles_active.json`.
  **git 으로 추적하지 않는다**(A00145 · A00340 프로파일과 같다 — PC 마다 따로). 없으면 `Default` 를 코드가 다시 만든다.
- json 모양:
  ```json
  {"tokens": [
    {"rule": "custom", "text": "dyn"},
    {"rule": "custom", "text": "asset"},
    {"rule": "custom", "text": "side"},
    {"rule": "numbering", "start": 0, "pad": 2},
    {"rule": "numbering", "start": 0, "pad": 2}
  ]}
  ```
  깨진 파일이나 빈 목록은 `Default` 규칙으로 읽는다.
  Enum 칸은 `{"rule": "enum", "role": "character", "values": ["CHN", "DHA", "LUN", "SIN", "TBM"], "value": "SIN"}`
  — `values` · `role` 키는 A00470_MaterialTool 의 이름 규칙 json 과 같다. 목록에 없는 `value` 는 첫 값으로 읽는다.

**실행 전에 막는 것** — 마야는 잘못된 이름을 **에러 없이 다른 이름으로 바꿔 버린다**(Maya 2024 실측):

| 넣은 이름 | 마야가 만든 이름 |
|-----------|------------------|
| `01_a` | **`_a`** (앞 숫자를 지운다) |
| `a-b` | `a_b` |

그래서 `Custom` 글자는 **영문 · 숫자 · `_`** 만, 이름이 **숫자로 시작하면**(첫 토큰이 Numbering) 실행하지 않고 이유를 알린다.

- **네임스페이스는 보존한다** — `ns:grp` 는 `ns:<새 이름>` 이 된다(레거시 Naming Dyn 은 루트 네임스페이스로 옮겼다).
- `Default` 규칙의 결과는 레거시 `rename_dynamics` 와 **같다**(같은 이름이 있는 계층에서 대조 확인).

### 6.2 Copy Name 탭

1. 좌측 **Select Base**, 우측 **Select Targets** 로 두 리스트를 채운다. (필요하면 각 **Sort**)
   - **세트를 담으려면 `Add Sets`** 를 쓴다(v01.03). `cmds.select(set)` 이 멤버를 펼쳐 버려서
     평범한 Select/Add 로는 세트가 안 담긴다. 이 버튼은 **선택에 든 세트**와
     **선택한 오브젝트가 속한 세트**를 함께 모은다.
2. **Prefix** 에 접두어를 입력한다(선택).
3. **Set suffix** — **대상이 세트일 때만** 뒤에 붙는다. 기본 `_copy` (v01.03).
4. **Search / Replace** (v01.05, 선택) — Base 이름 안의 `Search` 를 **전부** `Replace` 로 바꾼 결과를 복사한다.
   예: Base `L_arm_jnt`, Search `jnt`, Replace `ctrl` → Target `L_arm_ctrl`.
   - 규칙은 Set Rename 탭과 같다 — 글자 그대로(정규식 아님), `Case sensitive`(기본 켬).
   - 치환은 **Base 이름에만** 걸린다. `Prefix` 와 `Set suffix` 는 그 **뒤에** 붙는다
     (Prefix 안의 단어는 바뀌지 않는다).
   - `Search` 가 비어 있으면 예전과 똑같이 그대로 복사한다.
   - 치환 결과가 빈 이름이면(Base 이름 전체를 지움) 그 대상은 **건너뛰고** `[Warning]` 을 남긴다.
5. **Copy Name** 클릭 → Targets[i] 가 `Prefix + (치환한) Base[i] 의 leaf 이름` 으로 리네임된다(리스트 순서 기준).

> **세트에 접미사가 필요한 이유** — 세트는 DG 노드라 **이미 쓰이는 이름을 그대로 못 쓴다.**
> 트랜스폼 `myName` 이 있는 씬에서 세트를 `myName` 으로 바꾸면 **마야가 조용히 `myName1` 로
> 만든다**(실측). DAG 노드는 부모가 다르면 같은 이름을 가질 수 있어(`|g1|c` 와 `|g2|c` 공존)
> 이 문제가 없다 — 그래서 접미사는 **세트 대상에만** 붙는다.
>
> `Set suffix` 를 비우면 접미사 없이 시도하고, 마야가 이름을 바꾸면 **실제로 붙은 이름**을
> 로그에 `[Warning]` 으로 알린다(조용히 넘어가지 않는다).

> **네임스페이스는 보존된다**(v01.03). 짧은 이름만 넘기면 노드가 **루트 네임스페이스로
> 옮겨간다** — 세트도 트랜스폼도 마찬가지다(실측). 이 탭은 대상의 네임스페이스를 그대로 다시 붙인다.

### 6.3 Quick Rename > Selection 탭 (현재 선택 기준)

1. 씬에서 대상 오브젝트를 선택한다(리스트가 아니라 **실제 선택**을 사용).
2. 원하는 동작:
   - **Front Insert** + **Insert Apply** — 이름 앞에 텍스트 삽입.
   - **Change New** (+ **Start (Index)**) + **New Apply** — 새 이름 + 증가 인덱스로 변경.
   - **Last Add** + **Add Apply** — 이름 뒤에 텍스트 추가.
   - **-1 Front / -1 Rear** — 이름의 앞/뒤 한 글자 제거.
   - **All Apply** — Change New → Front Insert → Last Add 순으로 한 번에 적용.

#### 6.3.1 Quick Rename > Insert 탭 (v01.09)

리스트에 담은 오브젝트마다 **이름의 n 번째 자리에 글자를 끼워 넣는다.**
Selection 탭의 Front Insert / Last Add 가 앞·끝만 되는 것을 **임의의 자리**로 넓힌 것이다.

1. 씬에서 오브젝트를 고르고 **Select Objects**(또는 Add)로 왼쪽 `Objects` 리스트에 담는다.
2. **Text** 에 넣을 글자, **Position** 에 자리를 적는다.
3. 오른쪽 **Preview** 표에 `Current` → `New name` 과 `Status` 가 **바로** 보인다
   (Text · Position · 리스트가 바뀔 때마다 다시 계산한다). 이때 씬은 그대로다.
   `New name` 에서 **새로 넣은 글자만 초록색**이다(`arm_`**`Up`**`jnt`) — 자리가 맞는지 한눈에 보인다.
   한 칸에 한 색만 되는 표 대신 리치 텍스트 라벨을 칸 위에 얹어 그린다.
4. **Apply** 를 눌러야 이름이 바뀐다. 전부 **Undo 한 번**으로 돌아간다. 바뀐 뒤 리스트는 새 이름으로 갱신된다.

**Position 규칙** — 짧은 이름의 글자 수로 센다. `0` 과 `-1` 이 짝(맨 앞 / 맨 끝)이다.

| Position | 뜻 | `arm_jnt` + `X` |
|---:|---|---|
| `0` | 맨 앞 | `Xarm_jnt` |
| `3` | 앞 3 글자 뒤 | `armX_jnt` |
| `-1` | 맨 끝 | `arm_jntX` |
| `-4` | 뒤 3 글자 앞 | `arm_Xjnt` |
| `99` / `-99` | 이름 밖 → 끝 / 앞에 붙임 (Status 에 적힘) | `arm_jntX` / `Xarm_jnt` |

- Position 칸 옆에 뜻(`front` / `after the first 3 character(s)` …)이 한 줄로 나온다.
- 이름 밖을 가리켜도 막지 않는다 — 길이가 다른 여러 이름에 한 번에 쓰기 때문이다. 대신 그 행의 Status 에
  `position is outside the name - put at the end` 로 적는다.
- **DAG 경로와 네임스페이스는 세지 않고 그대로 둔다** — `NS:hand` 에 `-1`,`_L` → `NS:hand_L`.

**Status 열** — 규칙은 Set Rename 탭과 같다. `OK`·`name taken` 만 Apply 대상이다.

| Status | 뜻 |
|---|---|
| `OK` (초록) | 그대로 바뀐다 |
| `name taken` (노랑) | 같은 부모 아래(DG 노드는 씬 전체)에 이미 있는 이름 → 마야가 번호를 붙인다. 실제 이름은 로그 `[WARN]` 에 |
| `no change` (회색) | Text 가 비었다 |
| `invalid name` | 숫자로 시작하거나 공백·`-`·`|` 같은 글자가 생긴다 → 건너뜀 (마야는 조용히 고쳐 버린다) |
| `locked` / `referenced` / `default node` | 바꿀 수 없는 노드 → 건너뜀 |
| `not a node` / `gone` | 컴포넌트(`.vtx[0]`)이거나 씬에서 사라졌다 |

- 부모와 자식을 함께 담아도 된다 — **깊은 노드부터** 바꾸므로 경로가 틀어지지 않는다.
- 트랜스폼을 바꾸면 마야가 **셰이프 이름도 따라 바꾼다**(`arm_jntShape` → `arm_jnt_LShape`, 마야 `rename` 기본 동작 · 다른 탭과 같다).

---

### 6.4 Set Rename 탭 (v01.02, 신규)

**세트 이름 안의 부분 문자열을 찾아 바꾼다.**

#### 마야 기본 기능은 왜 안 되나 (Maya 2024 실측)

`Modify > Search and Replace Names` 의 실체는 MEL `searchReplaceNames` 다.
**이 명령 자체는 세트도 잘 바꾼다** — `"all"` 모드로 돌리면 세트 이름이 같이 바뀐다
(실측: 세트 5개를 포함해 8개 이름이 한 번에 바뀌었다).

막힌 것은 명령이 아니라 **세트를 선택하는 방법**이다.

```python
cmds.select(mySet)
cmds.ls(sl=True)                    # ['pCube1']  <- 세트가 아니라 멤버가 나온다
cmds.ls(sl=True, type="objectSet")  # []
```

**`cmds.select(set)` 은 세트가 아니라 그 멤버를 펼쳐 선택한다.** 그래서 `"selected"` 모드는
세트를 영영 못 본다. `noExpand=True` 로 넘기면 세트 자신이 선택되고 그때는 마야 기본 기능도
세트를 바꾸지만, 뷰포트·아웃라이너 조작으로 그 상태를 만들기가 어렵다.
`"all"` 모드는 대안이 못 된다 — 씬의 메시·조인트·카메라까지 전부 바꾼다.

→ **이 탭은 세트를 직접 열거해 고르게 하고, 바꾸기 전에 미리보기를 준다.**

#### 쓰는 법

1. **`Refresh`** — 씬의 모든 세트를 나열한다(목록을 **교체**).
   **`From Selection`** — 지금 선택한 오브젝트가 **속한** 세트를 나열한다(목록을 **교체**).
   메시 하나를 고르고 그것이 든 세트를 찾는 흐름이다. 세트 자신을 `noExpand` 로 골라 둔
   경우도 함께 잡는다.
   **`Add`** / **`Del`** (v01.03) — 다른 탭의 TSL 과 같은 조작이다.
   `Add` 는 선택과 관련된 세트를 **기존 목록에 더한다**(이미 있으면 건너뛴다).
   `Del` 은 하이라이트한 행을 **목록에서만** 뺀다 — **씬의 세트는 지워지지 않는다.**
2. **Filter** 로 목록을 좁힌다(부분 일치 · 대소문자 무시 · 공백은 AND).
3. 바꿀 세트를 **하이라이트**한다(다중 선택).
4. **Search / Replace** 를 친다 — **목록의 `New name` · `Status` 열이 즉시 갱신된다.**
5. **`Rename Selected Sets`** — 전체가 **undo 한 스텝**.

> **필터에 가려진 선택은 대상이 아니다.** 가려진 채 선택된 행이 있으면 로그로 알려 준다
> ("보이는 것이 작업 대상" — 공용 Filter 위젯의 규칙).

| 옵션 | 뜻 |
|---|---|
| `Shading Engines` | `shadingEngine` 노드도 목록에. **기본 꺼짐** — 렌더 셋업을 건드리게 된다 |
| `Partitions` | `partition` 노드도 목록에. **`partition` 은 `objectSet` 이 아니라서** 기본 목록에 안 잡힌다 |
| `Case sensitive` | 마야 기본 기능과 같은 동작 (기본 켜짐) |
| `Select Sets in Scene` | 하이라이트한 **세트 자신**을 씬에서 선택한다 (`noExpand=True`) |

#### Status 열

| 상태 | 뜻 | 실행되나 |
|---|---|---|
| `OK` | 문제 없음 | O |
| `name taken` | 같은 이름이 이미 있다 — **마야가 번호를 붙인다**(`dst_set` → `dst_set1`) | O (실제 붙은 이름을 로그로 보고) |
| `no change` | 검색어가 이름에 없다 | X |
| `invalid name` | 마야가 허용하지 않는 문자 (이유를 함께 표시) | X |
| `locked` | 잠긴 노드 | X |
| `referenced` | 레퍼런스에서 온 노드 | X |
| `default set` | `initialShadingGroup` 등 기본 세트 | X |

#### 실측으로 알아낸 함정 (이 탭이 대신 막아 주는 것)

- **네임스페이스가 벗겨진다.** `rename("NS:in_ns", "plain")` 하면 세트가 **루트 네임스페이스로
  옮겨간다**(`NS` 는 비게 된다). 짧은 이름만 바꿔 넘기면 레퍼런스에서 온 세트가 전부
  네임스페이스를 잃는다. → 이 탭은 **네임스페이스를 떼어 두고 짧은 이름만 치환한 뒤 다시
  붙여서** rename 한다.
- **마야가 이름을 조용히 고친다.** `1bad` → `bad`(**맨 앞 숫자가 사라진다**),
  `has space` → `has_space`, `has-dash` → `has_dash`, `a|b` → `a_b`.
  경고만 뜨고 넘어가므로 의도와 다른 이름이 조용히 생긴다. → **미리 걸러 내고 건너뛴다**
  (마야의 조용한 변환을 흉내 내지 않는다).
- **이름이 겹치면 번호를 붙인다**(에러가 아니다). → 미리보기에서 `name taken` 으로 표시하고,
  실행 후 **실제로 붙은 이름**을 `[Warning]` 으로 알린다.
- **기본 세트는 못 바꾼다** — `Cannot rename a read only node`. 다만 **`ls(readOnly=True)` 는
  빈 리스트를 준다**(판정에 쓰면 안 된다) — `ls(defaultNodes=True)` 로 골라야 한다.
- `rename` 은 **undo 된다.**

---

## 7. 동작 규칙

- **Token 번호**: Numbering 이 2 개면 앞 번호는 **루트 그룹마다** 1 증가, 뒤 번호는 **그룹 내 항목마다** 증가하고 그룹이 바뀌면
  시작값으로 리셋된다(레거시 Index1 / Index2). 1 개면 전체 순번. 각 번호는 **Pad 0** 자리수로 0 패딩된다(§6.1).
- **자손 수집**: 루트가 transform 이면 자손 중 **transform 만** 남긴다(shape 노드 제외). `[root, 얕은→깊은 자손]` 순서.
- **Change New 패딩**: 10 미만은 `0` 패딩(`01…09`), 이후는 그대로(`10, 11…`).
  Start 가 비어 있고 **단일 선택**이면 번호 없이 이름만, **다중 선택**이면 `01` 부터 자동 부여.
- **이름 정리**: 모든 처리에서 DAG 경로(`|`)와 네임스페이스(`:`)를 제거한 leaf 이름을 기준으로 한다.
- **Undo**: 각 버튼 동작은 `core.undo_chunk` 로 묶여 **한 번의 Undo** 로 되돌릴 수 있다.
- **동일 이름 안전(v01.01+)**: 모든 rename 은 노드를 **UUID** 로 잡아 처리한다(`_to_uuid` → `_rename_by_uuid`).
  씬에 같은 이름의 오브젝트가 여러 개 있어도(예: `joint_01`·`joint_03` 밑에 각각 `joint_02`),
  또 부모를 rename 해 자식 경로가 바뀌어도 UUID 로 현재 경로를 다시 찾아가므로 실패하지 않는다.
  (Naming Dyn 은 자손을 `fullPath` 로 수집하고, 입력 이름도 `ls(long=True)` 로 정규화한다.)

---

## 8. 로그 · 문제 해결

- 정상: `Token : 12 node(s) renamed (profile 'Default').` / `Copy Name : 8 target(s) renamed.` / `Front Insert : 3 renamed.`
- 경고:
  - `[WARN] Objects list is empty. Use Select Base first.` — Naming Dyn 리스트가 비어 있음.
  - `[WARN] 3 Numbering tokens - use at most 2 ...` — Numbering 토큰이 3 개 이상.
  - `[WARN] The name would start with a digit ...` — 첫 토큰이 Numbering. 앞에 Custom 토큰을 둔다.
  - `[WARN] Token N '...' has characters Maya does not allow ...` — Custom 에 영문·숫자·`_` 외 글자.
  - `[WARN] Token : one token must remain.` — 마지막 칸은 못 지운다.
  - `[Warning] ... (asked for '...' - Maya changed it, the name is already used).` — 번호가 없어 이름이 겹쳤다.
  - `[WARN] Both Base and Targets lists must be filled.` — Copy Name 양쪽 리스트 필요.
  - `[WARN] Base(n) and Targets(m) counts differ; renaming first k item(s).` — 개수 불일치 시 앞쪽만 처리.
  - `[WARN] Enter a new name. (Change New is empty)` — Change New 비어 있음.
- **이름이 안 바뀜**: Quick Rename > Selection 은 리스트가 아니라 **현재 씬 선택**을 대상으로 한다. 선택 여부를 먼저 확인.
  Quick Rename > Insert 는 반대로 **리스트**가 대상이고, Preview 의 Status 가 `OK`/`name taken` 인 행만 바뀐다.

---

## 로그창 (v01.04)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위에 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
