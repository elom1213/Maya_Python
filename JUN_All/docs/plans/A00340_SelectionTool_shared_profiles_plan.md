---
title: A00340_SelectionTool — 공유 프로파일 · 규칙 (shared/) 계획서
aliases: [A00340 shared profiles, profiles_share, shared folder]
tags: [plan, maya-python, A00340, profile, git, share]
updated: 2026-10-28
---

# A00340_SelectionTool — 공유 프로파일 · 규칙 (shared/) 계획서

> 작성 2026-10-28 · 대상 버전 **v01.17** · 상태: **구현 완료(2026-10-28, mayapy 오프스크린 46 항목) · 마야 GUI 확인 전** (진행은 §9 체크리스트)
>
> **이 PC 는 작업 중에 저절로 꺼질 수 있다.** 그래서 이 문서만 보고 이어서 작업할 수 있게 썼고, 단계마다 로컬 커밋한다.
> 이어서 할 때는 §9 의 체크 상태와 `git log --oneline -10`(커밋 제목에 `[T번호]`)을 먼저 본다.

---

## 0. 요약

- **문제**: `.gitignore` 의 `**/A00340_SelectionTool/data/` 때문에 `data/profiles/*.json` · `data/rules/*.json` 이 GitHub 에 안 올라간다.
  공유하고 싶은 프로파일만 골라 올릴 방법이 없다.
- **결정 (사용자 2026-10-28 "모두 추천대로")**
  1. 공유 폴더 = **`A00340_SelectionTool/shared/`** (`profiles/` · `rules/`). `data/` **밖**이라 git 이 추적한다.
     (git 은 무시된 폴더 안을 `!` 로 다시 포함시킬 수 없다 - `data/profiles_share/` 는 안 된다.)
  2. 툴은 **로컬(`data/`) + 공유(`shared/`)** 두 곳을 함께 보여 준다. 프로파일 정체 = **(scope, 이름)** - 같은 이름이 양쪽에 있어도 따로 보인다.
  3. 공유 프로파일도 **편집 가능**. 이름 바꾸기 · 지우기만 한 번 더 확인.
  4. 오가기 명령: **`Share`**(로컬 → 공유 이동) · **`Copy to Local`**(공유 → 로컬 복사).
  5. **Rules 탭도 같은 규칙**(`shared/rules/`).
  6. **공유 폴더 경로는 PC 별로 바꿀 수 있다**(`data/active.json` 의 `shared_dir`, 기본은 툴 안 `shared/`). NAS · 별도 데이터 저장소도 가리킬 수 있다.

---

## 1. 지금 구조 (2026-10-28, v01.16)

| 파일 | 하는 일 |
|------|---------|
| `app/core/prefs.py` | `PREFS_DIR = <tool>/data`, `PROFILES_DIR = data/profiles`, `ACTIVE_PATH = data/active.json`. `list_profiles()` · `load_profile(name)` · `save_profile(name, data)` · `delete_profile(name)` · `rename_profile(old, new)` · `get_active()` · `set_active(name)` · `get_setting(key)` · `set_setting(key, value)` · `profile_path(name)` · `sanitize_name(name)`. 프로파일이 하나도 없으면 `Default` 를 만든다(`_ensure_setup`) |
| `app/core/select_rules.py` | `RULES_DIR = data/rules`. 함수마다 `rules_dir=None` 인자가 있다(`load_rules` · `find_rule` · `save_rule` · `rename_rule` · `delete_rules` · `rule_path`). `update_rule` 은 `rule.path` 에 쓴다 |
| `app/ui/selection_tab.py` | `self._profile`(이름) · `self._data`. 콤보 `cmb_profile`(`addItems(list_profiles())`, `currentTextChanged` → `on_profile_changed(name)`), `on_new_profile` · `on_rename_profile` · `on_delete_profile`(하나는 남겨야 함), `_save_and_render` → `prefs_mod.save_profile(self._profile, self._data)` |
| `app/ui/rules_tab.py` | `RulesTab(rules_dir=None)` 한 폴더만. 표 열 Name / Objects / File. 상태 줄 `lbl_folder`(v01.12 짧은 경로 + 툴팁) |
| `app/ui/main_window.py` | View 메뉴 `Show Controls` · `Show Profile`(`prefs_mod.profile_path(get_active())`) · `Show Rules Folder` |
| `.gitignore` (저장소 루트) | `**/A00340_SelectionTool/data/` - 손대지 않는다 |

---

## 2. 데이터 배치

```
A00340_SelectionTool/
├── data/                      # git 제외 (그대로)
│   ├── active.json            # {"active": "MUE_BCM", "active_scope": "shared", "shared_dir": "", ...}
│   ├── profiles/*.json        # 로컬 프로파일
│   └── rules/*.json           # 로컬 규칙
└── shared/                    # git 추적 (신규)
    ├── profiles/*.json        # 공유 프로파일 (형식은 로컬과 같다)
    │   └── .gitkeep
    └── rules/*.json           # 공유 규칙
        └── .gitkeep
```

- `active.json` 새 키
  - `active_scope` : `"local"` | `"shared"`. **없으면 `"local"`**(v01.16 이하 파일과 호환).
  - `shared_dir` : 공유 루트 절대 경로. 비었거나 없는 폴더면 기본 `<tool>/shared`. 폴더 안에 `profiles/` · `rules/` 를 쓴다.
- json 형식은 바꾸지 않는다. 로컬 ↔ 공유 이동은 파일 이동 · 복사뿐이다.

---

## 3. `prefs.py` 설계

```python
SCOPE_LOCAL, SCOPE_SHARED = "local", "shared"
SCOPES = (SCOPE_LOCAL, SCOPE_SHARED)
DEFAULT_SHARED_ROOT = os.path.join(_base_dir(), "shared")
SHARED_DIR_KEY = "shared_dir"

def shared_root():                    # get_setting(SHARED_DIR_KEY) 가 있는 폴더면 그것, 아니면 DEFAULT_SHARED_ROOT
def set_shared_root(path):            # "" 이면 기본으로 되돌림
def profiles_dir(scope=SCOPE_LOCAL)   # local -> PROFILES_DIR, shared -> shared_root()/profiles
def rules_dir(scope=SCOPE_LOCAL)      # local -> data/rules,   shared -> shared_root()/rules

def list_profiles(scope=SCOPE_LOCAL)  # 그 폴더의 이름 목록(정렬) - 기존 호출과 호환
def list_all_profiles()               # [(scope, name)] - 로컬 먼저, 그다음 공유
def profile_path(name, scope=SCOPE_LOCAL)
def load_profile(name, scope=SCOPE_LOCAL)
def save_profile(name, data, scope=SCOPE_LOCAL)
def delete_profile(name, scope=SCOPE_LOCAL)
def rename_profile(old, new, scope=SCOPE_LOCAL)   # 활성이면 active 도 갱신 (scope 까지 같을 때)

def get_active()                      # 이름만 (호환)
def get_active_ref()                  # (scope, name) - 없거나 사라졌으면 list_all_profiles()[0] 로 보정 후 저장
def set_active(name, scope=SCOPE_LOCAL)

def share_profile(name)               # 로컬 -> 공유 **이동**. 공유에 같은 이름이 있으면 ValueError. 활성이면 active 를 (shared, name) 로
def copy_profile_to_local(name)       # 공유 -> 로컬 **복사**. 로컬에 같은 이름이 있으면 ValueError
```

- `_ensure_setup()` : 로컬 폴더 보장 + **로컬과 공유를 합쳐** 프로파일이 하나도 없을 때만 로컬 `Default` 를 만든다.
- 공유 폴더가 없으면 목록은 빈 것으로 보고, 쓸 때 만든다(`os.makedirs`).
- `select_rules.py` 는 **함수는 그대로**, `RULES_DIR` 도 그대로(로컬). 공유는 `prefs.rules_dir(SCOPE_SHARED)` 를 `rules_dir=` 로 넘긴다.
  - 추가: `share_rule(rule, shared_dir)`(이동) · `copy_rule_to(rule, target_dir)`(복사) - 대상에 같은 파일/이름이 있으면 ValueError.

---

## 4. Buttons 탭 (`selection_tab.py`)

- 상태 : `self._scope` 추가(`self._profile` 은 이름 그대로).
- 콤보 : 항목 글자 = 로컬 `Name`, 공유 `Name [Shared]`. `itemData` = `(scope, name)`. 시그널은 `currentIndexChanged` → `on_profile_changed(index)` 로 바꾼다
  (같은 이름이 양쪽에 있어도 구별되게).
- `_save_and_render` → `save_profile(self._profile, self._data, self._scope)`.
- Profile 그룹 버튼 : `New` · `Rename` · `Delete` + **`Share`** · **`Copy to Local`**(현재 프로파일 scope 에 따라 하나만 활성: 로컬이면 Share, 공유면 Copy to Local).
  - `New` = 로컬에 만든다(공유는 Share 로 올린다 - 실수로 공유 폴더에 시험용 프로파일이 생기지 않게).
  - `Rename` · `Delete` 는 현재 scope 안에서. 같은 scope 에 같은 이름이 있으면 막는다. **공유면 확인 한 번 더**("This profile is shared (git tracked) ...").
  - `Delete` 는 로컬 + 공유 합쳐 하나는 남아야 한다.
  - `Share` : 공유에 같은 이름이 있으면 막고 알린다. 성공하면 콤보에서 그 항목이 `[Shared]` 로 바뀐다. 로그에 "commit and push shared/profiles/<name>.json to share it" 안내.
  - `Copy to Local` : 로컬에 같은 이름이 있으면 막는다. 성공하면 로컬 복사본으로 전환.
- 프로파일이 공유일 때 Profile 그룹 제목을 `Profile (shared)` 로 바꿔 지금 무엇을 고치는지 보이게 한다.

---

## 5. Rules 탭 (`rules_tab.py`)

- `RulesTab(rules_dir=None, shared_dir=None)` - 둘 다 None 이면 `prefs.rules_dir(local)` · `prefs.rules_dir(shared)`.
  기존 테스트 호환: `rules_dir` 만 주면 공유는 `shared_dir` 인자(없으면 공유 안 봄 - 테스트가 실제 공유 폴더를 건드리지 않게).
- 표 열 : **Name / Scope / Objects / File** (Scope = `Local` / `Shared`). 같은 이름이 양쪽에 있어도 두 줄.
- 고른 규칙의 폴더 = `os.path.dirname(rule.path)` → Rename · Delete · Update · Description 은 그 폴더 안에서(`rules_dir=` 에 넘김).
- `New Rule from Selection` = 로컬에.
- 우클릭 메뉴(있으면 거기에, 없으면 새로) + 버튼 행에 **`Share`** · **`Copy to Local`**.
  여러 규칙을 골랐으면 해당하는 것만(로컬 → Share, 공유 → Copy to Local).
- 공유 규칙 Rename · Delete 는 확인 한 번 더.
- 상태 줄 : `N local + M shared rule(s)`, 툴팁에 두 폴더 경로.

---

## 6. 메뉴 (`main_window.py`)

- View > `Show Profile` : 현재 프로파일의 scope 경로(`profile_path(name, scope)`).
- View > **`Show Shared Folder`** : `shared_root()` 를 탐색기로(없으면 만든다).
- View > **`Shared Folder...`** : 폴더 고르기(QFileDialog) → `set_shared_root(path)`, 두 탭 다시 읽기. 같은 메뉴에 **`Use Default Shared Folder`**.
  지금 경로를 로그에 남긴다. 툴팁: "Per PC setting (data/active.json). Default = the tool's shared folder, tracked by git."
- About 에 공유 설명 몇 줄.

---

## 7. 경계 · 방어

| 사례 | 처리 |
|------|------|
| `active.json` 에 `active_scope` 없음 (옛 파일) | `local` 로 본다 |
| 활성 프로파일 파일이 사라짐 (git pull 로 공유 쪽이 지워짐 등) | `get_active_ref()` 가 첫 프로파일로 보정 |
| `shared_dir` 가 없는 폴더 (다른 PC 경로) | 기본 `shared/` 로 쓰고 `[WARN]` 한 번 |
| 공유와 로컬에 같은 이름 | 둘 다 보인다. Share / Copy 는 대상에 같은 이름이 있으면 막는다 |
| 깨진 공유 json | 기존과 같이 빈 구조로 읽는다(프로파일) / errors 로 알린다(규칙) |
| 파일명 금지 문자 | 기존 `sanitize_name` 그대로 |

---

## 8. 검증

`tests/test_shared_profiles.py`(신규, mayapy 오프스크린). **`prefs` 의 경로 상수를 임시 폴더로 바꿔** 실제 `data/` · `shared/` 를 건드리지 않는다.

1. prefs : `list_all_profiles` 순서 · 같은 이름 양쪽 · `share_profile` 이동 · 충돌 막기 · `copy_profile_to_local` · `active_scope` 없는 옛 active.json · 사라진 활성 보정 · `shared_dir` 지정 / 없는 경로 → 기본
2. Buttons 탭 : 콤보 글자 `[Shared]` · 같은 이름 둘 중 고른 쪽이 열림 · 버튼 추가가 그 scope 파일에 저장 · Share / Copy to Local 버튼 활성 규칙 · 공유 Delete 확인 두 번 · 하나는 남김
3. Rules 탭 : Scope 열 · 두 폴더 합쳐 보임 · 공유 규칙 Rename 이 공유 폴더 안에서 · Share / Copy to Local
4. 회귀 : 드래그 시험(scratch `drag_test.py` 를 tests 로 옮김) · Add 체크 · 창 최소 폭

받아들임: 위 전부 통과 + 실제 저장소에서 `git status` 에 `shared/profiles/.gitkeep` · `shared/rules/.gitkeep` 만 새로 보임(`data/` 는 여전히 안 보임).

---

## 9. 진행 체크리스트 (단계마다 로컬 커밋, 제목에 `[T번호]`)

- [x] **T1** 이 계획서 커밋
- [x] **T2** `prefs.py` scope · 공유 루트 · share/copy + `select_rules.py` share/copy + `shared/*/.gitkeep`
- [x] **T3** Buttons 탭 (콤보 (scope, name) · Share / Copy to Local · 공유 확인)
- [x] **T4** Rules 탭 (Scope 열 · 두 폴더 · Share / Copy to Local)
- [x] **T5** main_window 메뉴 (Show Profile scope · Show Shared Folder · Shared Folder... · Use Default)
- [x] **T6** 시험 `tests/test_shared_profiles.py` + 회귀(드래그 · Add) 통과
- [x] **T7** 버전 01.17 · CHANGELOG · `docs/A00340_SelectionTool.md` 공유 절 · WORKLOG · 이 문서 상태 = 구현 완료

커밋은 로컬만. **푸시는 사용자가 그 턴에 말할 때만**(전역 규칙 2장).
