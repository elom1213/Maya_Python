# Framework — `MOD_tokenName_qt_v01` (토큰 이름 위젯) + `core/token_naming` (규칙 · 프로파일)

이름을 `_` 로 이은 **토큰 칸**으로 짓는 화면 한 벌. 칸마다 규칙을 고르고, 칸은 원하는 자리에 더하고 빼고,
규칙 한 벌을 **프로파일(json)** 로 저장한다. 이름을 실제로 적용하는 일(rename · 파일명)은 툴이 한다.

- 위젯: `JUN_All/Framework/qt/MOD_tokenName_qt_v01.py` — 별칭 `from Framework.qt import JUN_mod_tokenName_qt`
  - `JUN_mod_tokenName_qt_v01(store, log=None, log_prefix="Token", framed=True)`
- 규칙 · 저장: `JUN_All/Framework/core/token_naming.py` (UI · 마야 비의존)
  - `TokenRuleSet` — 툴이 쓸 규칙 묶음 · 검사 · 이름 만들기 · 미리보기
  - `TokenProfileStore(data_dir, default_tokens, ruleset)` — 프로파일 json
- 출처: `A00330_NamingTool` Rename > Token 탭(v01.07~01.08)을 공용으로 올렸다 (2026-09-28).
- 사용처: **A00330_NamingTool** Rename > Token (v01.10) · **A00480_FileTool** Export > Naming (v01.06)

## 화면

```
framed=True (A00330)                          framed=False (A00480, 그룹 박스 안)
┌ Profile ───────────────────────────────┐    Profile [Default ▾][Save][New][Rename][Delete]  [Add Token][Delete Token]
│ [Default  ▾] [Save][New][Rename][Delete]│    ┌Token 1┐┌Token 2┐┌Token 3┐ ...  <- 가로 스크롤 ->
└─────────────────────────────────────────┘    │Custom▾││Custom▾││Set's▾ │
┌ Tokens ────────────────────────────────┐    │ SK    ││ MANU  ││<Set>  │
│ [Add Token] [Delete Token]              │    └───────┘└───────┘└───────┘
│ ┌Token 1┐┌Token 2┐┌Token 3┐ ...         │    Preview : SK_MANU_<Set> ...           [Set Name]
│ Preview : dyn_asset_side_00_00 -> ...   │                                         ↑ preview_row 에 툴 버튼
└─────────────────────────────────────────┘
```

- 칸 머리(`Token N`)를 누르면 그 칸이 골라진다(노랗게). **Add Token** = 고른 칸 **오른쪽**에 빈 Custom 칸,
  **Delete Token** = 고른 칸 삭제(마지막 한 칸은 남는다). 칸 폭 80px, 넘치면 가로 스크롤.
- **칸을 고쳐도 저장하지 않는다**(2026-10-01~). Profile 줄의 **`Save`**(`save_profile()`)를 눌러야 지금 칸이 그 프로파일의
  기본이 된다. `Save` 는 저장 안 한 변경이 있을 때만 켜지고(`is_dirty()`), 저장 안 한 칸은 프로파일 전환(`[WARN]` 로그)
  · 창 닫기 때 버려진다. 예전엔 고칠 때마다 바로 저장돼서 다시 열면 고친 칸이 알림 없이 기본이 됐다.
- `New` 는 지금 칸을 복사한 새 프로파일(떠나온 프로파일은 그대로).
- `framed=False` 는 Profile 과 Add/Delete Token 을 **한 줄**에 둬서 세로를 아낀다.
- `preview_row`(QHBoxLayout) 오른쪽에 툴 실행 버튼을 붙일 수 있다.

## 규칙

| 규칙 | 토큰 dict | 값 |
|------|-----------|-----|
| `Custom` | `{"rule": "custom", "text": "SK"}` | 적은 글자 그대로. 비면 건너뛴다(`__` 없음) |
| `Numbering` | `{"rule": "numbering", "start": 0, "pad": 2}` | Start 부터 올라가는 번호, Pad 0 자리수 |
| `Set's Name` | `{"rule": "setname"}` | 대상마다 주어진 이름(세트 이름 - 네임스페이스 · 경로 없이) |
| `Enum` (2026-10-02) | `{"rule": "enum", "role": "part", "values": ["Top", "Pants"], "value": "Top"}` | 정해진 값 중 고른 하나(콤보). 칸에 칸 이름(role) · 값 콤보 · `Values...`(칸 이름 · 값 목록 편집). 목록에 없는 value 는 첫 값으로, 값이 없으면 검사에서 막는다. 키는 A00470 이름 규칙 json 과 같다 |

툴은 **규칙 묶음**을 고른다.

| 묶음 | 규칙 | Numbering | 글자 검사 |
|------|------|-----------|-----------|
| `MAYA_NODE_RULES` | Custom · Enum · Numbering | 1 개 = 전체 순번, 2 개 = 오브젝트 / 오브젝트 안 노드 | `[A-Za-z0-9_]`, 숫자로 시작 금지 (마야가 조용히 지운다) |
| `FILE_NAME_RULES` | Custom · Numbering · Set's Name | 1 개 = 세트 순번 | Windows 파일명 금지 문자 `\ / : * ? " < > \|` |

새 묶음은 `TokenRuleSet(rules=..., max_numbering=..., name_kind=NAME_MAYA|NAME_FILE, ...)` 한 줄.
묶음에 없는 규칙이 json 에 있으면 `Custom`(빈 글자)으로 읽는다.

## 사용

```python
from Framework.core import token_naming
from Framework.qt.MOD_tokenName_qt_v01 import JUN_mod_tokenName_qt_v01

STORE = token_naming.TokenProfileStore(
    os.path.join(<tool>, "data"),                      # PC 별 - .gitignore 에 추가할 것
    [{"rule": "custom", "text": "SK"}, ...],           # 프로파일이 없을 때 만드는 Default
    token_naming.FILE_NAME_RULES)

self.token_widget = JUN_mod_tokenName_qt_v01(STORE, log=self._log, log_prefix="Naming", framed=False)

tokens = self.token_widget.tokens()
errors = STORE.ruleset.validate(tokens)                # [] 면 실행 가능
names  = STORE.ruleset.names_for(set_names, tokens)    # 대상마다 이름 하나
groups = STORE.ruleset.plan_names([2, 3], tokens)      # 오브젝트마다 노드 수 -> [[..], [..]]
```

- 프로파일 파일: `<data_dir>/token_profiles/<이름>.json` (`{"tokens": [...]}`) + `token_profiles_active.json`.
- 신호 `tokensChanged(list)` — 칸이 바뀔 때마다(프로파일 전환 포함).

## 알아 둘 것

- 테마 qss 에 `QPushButton:checked` 가 없으면 고른 칸이 안 보인다 → 칸 머리 버튼에만 강조 stylesheet.
- 가로 전용 `QScrollArea` 는 레이아웃이 테마 전 높이를 캐시해 칸 아래가 잘린다 → `TokenScrollArea` 가
  LayoutRequest / Polish 때 높이를 직접 고정한다.
- Numbering 칸은 `Start` / `Pad 0` 라벨을 스핀박스 위에 둔 4줄이라, 칸 줄 높이는 이 칸이 정한다.
- **규칙 페이지는 모두 [이름 줄] -> [입력칸] -> ... -> stretch** (2026-10-02). 이름 줄이 없는 페이지가 있으면 입력칸이 한 줄 위로
  붙고, stretch 가 없는 페이지는 남는 높이가 이름 줄로 나뉘어 입력칸이 내려간다(실측 6px). 입력칸 높이는
  `TokenColumn._match_input_heights` 가 테마를 입힌 QLineEdit / QSpinBox 중 큰 값으로 고정한다(Polish · StyleChange · Show 때).
