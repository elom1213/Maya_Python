# A00210_FileManager — Path Structure 라이브러리 독립 계획서 (공용 Saved Structures + 카테고리)

> **작성** 2026-11-27 · 상태: **구현 전** · 대상 버전 **v01.60** · 다음 작업 = 7장 결정 확인 → 4장 단계 1부터
> 요청 (사용자, 2026-11-27):
> 1. Path Structure 탭의 **Saved Structures 를 File Manager 탭의 Profile 과 무관하게 전부** 보이게 한다.
>    지금은 예를 들어 `Dnable_CH` 가 `Local_CH_D` 프로파일(데이터 폴더 `Dnable`)에서만 보이고 `JUN` · `MUE` 프로파일에서는 안 보인다.
> 2. Saved Structures **만** 따로 Push / Pull 해서 공유한다.
> 3. 저장된 구조를 **사용자가 만든 카테고리**로 나눈다. 카테고리는 생성 · 삭제 · 이름 바꾸기가 되고, 역시 Push / Pull 로 관리된다.
> 4. 목적: 저장된 구조들을 **File Manager 탭에서 독립**시킨다.

이 문서만 보고 구현 · 검증 · 이전(마이그레이션)까지 진행할 수 있도록 썼다. 코드 위치는 전부
`JUN_All/tools/A00210_FileManager/` 기준 상대 경로다.

---

## 0. 결론

- 구조 JSON 을 **데이터 저장소 루트의 `path_structures/`** 로 옮긴다 — `profiles/<data_folder>/` 밖.
  저장소(`JUN_FileManager_data`, 비공개, `main`)와 클론은 **지금 것을 그대로** 쓴다. 새 저장소 · 새 브랜치 없음.
- 그 클론 경로와 `Recreate To` 는 **프로파일이 아니라 PC 단위 설정 파일**(`~/.jun_filemanager/structure_library.json`)에 둔다.
  → 프로파일 · Source Mode(git/local) · Data Folder 를 바꿔도 Path Structure 탭은 **아무것도 바뀌지 않는다.**
- Path Structure 탭에 **자기 Pull / Push** 를 둔다. Push 는 `path_structures/` **만** 스테이징한다
  (File Manager 의 Push 가 `profiles/<folder>/` 만 올리는 v01.45 방식과 같은 원리, 범위만 다름).
- 카테고리는 **카테고리 하나 = 파일 하나** (`path_structures/_categories/<id>.json`), 구조 JSON 에는 `category` 에 **id** 를 적는다.
  이름 바꾸기 = 카테고리 파일 하나만 바뀜 → 두 PC 가 동시에 카테고리를 만들어도 git 충돌이 원리상 안 난다.
- 기존 20개 구조는 **일회성 이전 스크립트**로 `git mv` 한다. 옛 데이터 폴더 이름(`Dnable` · `JUN` · `MUE` · `SA`)을 그대로 첫 카테고리로 만든다(이후 사용자가 이름 바꾸기 · 정리).

---

## 1. 현재 상태 (2026-11-27 관찰)

### 1-1. 코드

| 위치 | 지금 동작 |
|------|-----------|
| `app/core/path_structure.py` | 저장 위치 = `structures_dir(store_dir)` = `<store_dir>/path_structures/<name>.json`. `save` · `list_names` · `load` · `exists` · `delete` · `rename` 모두 `store_dir` 하나를 받는다. `list_names` 는 그 폴더의 `*.json` 만 본다(하위 폴더 무시). |
| `app/ui/path_structure_tab.py` | `PathStructureTab(get_store, get_project_root, get_store_dir, log)`. 모든 읽기/쓰기가 `self._get_store_dir()` = MainWindow 의 `_effective_store_dir()`. 목록 = `QListWidget list_structs`(maxHeight 120). 버튼 `[Refresh][Rename][Delete] ... [Recreate]`. 저장 후 로그 *"use Push on the File Manager tab to sync."* |
| `app/ui/main_window.py` | `_effective_store_dir()` → `prefs.data_dir_of()` = **git 모드 `<store_dir>/profiles/<data_folder>`**, local 모드 `<local_dir>`. 그래서 구조 목록이 **프로파일의 Data Folder 를 따라간다** ← 문제의 원인. `_refresh_other_tabs()` 가 프로파일 · Source Mode · Data Folder 를 바꿀 때마다 `path_structure_tab.on_refresh()` 호출. `recreate_to` 는 `_load_prefs_to_ui` / `_collect_prefs` 로 **프로파일에** 저장. |
| `app/core/git_sync.py` | `GitSync(store_dir, remote, branch, data_folder)` → `data_rel = "profiles/<data_folder>"`. `push()` = `add -A -- <data_rel>` → commit → `pull --rebase --autostash` → push(거절 시 1회 재시도). `pull()` = `pull --rebase --autostash`. **rebase 충돌 시 abort 하지 않는다**(저장소가 rebase 중 상태로 남을 수 있다 — 이번에 함께 고친다, 3-3). |
| `app/core/prefs.py` | 프로파일 = `~/.jun_filemanager/profiles/<name>.json`. `PATH_KEYS` 에 `recreate_to` 포함. |
| `app/core/lineage.py`, `app/ui/lineage_tab.py` | 주석에서 "path_structure 와 같은 패턴" 이라고 언급만. 코드 의존 없음 → 손대지 않는다. |
| 다른 툴 | `JUN_All/` 전체에서 `path_structure` 를 import 하는 곳은 A00210 안뿐(A00211 · A00480 은 lineage/ref 쪽만 씀). |

### 1-2. 데이터 (이 PC, 클론 `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_FileManager_data`, 브랜치 `main`)

구조 JSON **20개**, 전부 git 추적 중 · 미커밋 변경 없음. 이름 충돌 없음.

| 데이터 폴더 | 구조 (파일명 = 표시 이름, 다르면 괄호) | 보이는 프로파일 (지금) |
|-------------|------------------------------|------------------------|
| `profiles/Dnable/path_structures/` | `Dnable_CH` `Dnable_CH_Local` `Dnable_CH_Local_01` `Dnable_CH_Local_02` `Dnable_CH_UE` `Dnable_CH_file` `JALI_cleanup` `NAS_Rig_01` `Set_template_Local_02` `UE_Set_01` `UE_Set_02` `UE_Set_03` `tmp_Bebul` (13) | Default · HDN · Local_CH_C · Local_CH_D · Local_PJ_root · NAS_Character · Template |
| `profiles/JUN/path_structures/` | `JUN_0010` (1) | JUN |
| `profiles/MUE/path_structures/` | `MEU_root` `MUE_root_002` `MUE_root_003` `MUE_root_004` `Test`(표시 이름 `test`) (5) | MUE |
| `profiles/SA/path_structures/` | `SoundAliiance_Root` (1) | soundAliance |
| `profiles/src_rig/` | (없음) | Rig_Src |

> 주의: 클론에는 `profiles/Dnable/records/` 쪽 **미커밋 변경이 있다**(다른 작업의 records). 이전 스크립트와 새 Push 는
> 이것을 **절대 스테이징하지 않는다** — 경로를 `path_structures/` 와 `profiles/*/path_structures/` 로만 한정한다.

---

## 2. 목표 상태

### 2-1. 저장소 배치

```
JUN_FileManager_data/              (클론 = "Library Repo")
├── path_structures/               ★ 새 위치 — 프로파일 무관, 모든 PC · 모든 프로파일이 같은 목록
│   ├── _categories/
│   │   ├── c3f9a1b2.json          {"id": "c3f9a1b2", "name": "Dnable", "created_by": "...", "created_at": "..."}
│   │   └── 7d0e44aa.json
│   ├── Dnable_CH.json             {..., "category": "c3f9a1b2"}
│   ├── JUN_0010.json
│   └── ...
└── profiles/<data_folder>/        records · thumbs · lineage · manifests (File Manager · Lineage · Sync 탭, 그대로)
    └── (path_structures/ 없음 — 이전 후 사라진다)
```

- 구조 파일은 **카테고리와 무관하게 평평하게** 둔다. 카테고리를 옮겨도 파일 경로가 안 바뀐다(이동 = JSON 한 줄 수정).
- 구조 이름은 **라이브러리 전체에서 유일**(지금처럼 `_sanitize_name(name).json`). 다른 카테고리여도 같은 이름 불가 —
  파일이 평평해서 그렇고, Recreate · 로그에서 이름만으로 구분되게 하려는 것이기도 하다.
- `_categories` 는 `.json` 이 아닌 **폴더**라 기존 `list_names()`(폴더 안 `*.json` 만)에 섞여 들지 않는다. 그래도 새 코드는
  `_` 로 시작하는 항목을 명시적으로 건너뛴다.

### 2-2. 왜 카테고리를 "파일 하나씩 + id" 로 하는가

| 방식 | 이름 바꾸기 | 두 PC 가 동시에 카테고리 추가 | 판정 |
|------|-------------|------------------------------|------|
| A. 카테고리 = 하위 폴더 (`path_structures/<카테고리>/x.json`) | 폴더째 `git mv` — 그 안 모든 파일이 바뀜. 다른 PC 가 같은 때 그 폴더에 구조를 저장하면 rebase 충돌 | 충돌 없음 | ✗ |
| B. 목록 파일 하나 (`_categories.json` 배열) | 한 줄 | **같은 파일 두 곳 수정 → rebase 충돌** | ✗ |
| **C. 카테고리 하나 = 파일 하나 + 구조는 id 참조** | **그 카테고리 파일 하나만** | **새 파일 두 개 — 충돌 없음** | **✓ 채택** |

C 에서 충돌이 나는 경우는 "두 PC 가 **같은** 카테고리 이름을 동시에 바꿈" · "같은 구조를 동시에 고침" 뿐이다 — 드물고, 나면 3-3 의 abort 로 안전하게 멈춘다.

### 2-3. 카테고리 규칙

- **id**: `uuid.uuid4().hex[:8]`. 이름이 아니라 id 로 참조하므로 이름을 바꿔도 구조 JSON 은 그대로.
- **이름**: 앞뒤 공백 제거, 빈 이름 불가, **대소문자 무시 중복 불가**. 파일명이 아니므로 `\/:*?` 등 제한 없음(id 가 파일명).
- **Uncategorized**: `category` 가 `""` 이거나 **없는 id**(다른 PC 가 카테고리를 지움)인 구조는 가상 노드 `Uncategorized` 아래에 보인다.
  이 노드는 파일이 없고 이름 바꾸기 · 삭제 불가. 해당하는 구조가 하나도 없으면 트리에 안 보인다.
- **정렬**: 카테고리 이름 순(대소문자 무시), `Uncategorized` 는 맨 아래. 카테고리 안 구조도 이름 순.
- **카테고리 삭제**: 비어 있으면 확인 후 삭제. 구조가 있으면 3지선다 —
  `Move to Uncategorized`(기본) / `Delete Structures Too` / `Cancel`. "같이 삭제" 는 되돌릴 수 없다는 경고를 문구에 넣는다
  (git 기록에는 남는다).
- 빈 카테고리도 유지된다(파일이 있으니까) — 미리 카테고리를 만들어 두고 나중에 구조를 넣을 수 있다.

### 2-4. PC 단위 설정 — `~/.jun_filemanager/structure_library.json`

```json
{
  "repo_dir":   "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/JUN_FileManager_data",
  "remote":     "origin",
  "branch":     "main",
  "remote_url": "https://github.com/elom1213/JUN_FileManager_data.git",
  "recreate_to": "E:/out",
  "expanded":   ["c3f9a1b2"]
}
```

- **프로파일 밖**이라 프로파일 전환 · 삭제 · 이름 바꾸기와 무관하다. git 밖(`.jun_filemanager` 는 데이터 저장소가 아님)이라 Push 되지 않는다.
- **첫 실행 시드**(파일이 없을 때 한 번): `repo_dir` ← 활성 프로파일이 git 모드면 그 `store_dir`, 아니면 `data_repo.DEFAULT_STORE_DIR`.
  `recreate_to` ← 활성 프로파일의 `recreate_to`. `remote` · `branch` · `remote_url` ← `app/config/data_repo.py` 상수.
- `expanded` = 펼쳐 둔 카테고리 id(편의 기능, 없으면 전부 펼침).
- 이 PC 는 모든 프로파일의 `store_dir` 이 같은 클론이라 시드 결과가 곧 정답이다. 다른 PC 도 대개 같다.

### 2-5. Push / Pull 범위

| 버튼 | 스테이징 | 받기 |
|------|---------|------|
| Path Structure 탭 **Push** | `git add -A -- path_structures` **만** | `pull --rebase --autostash` 뒤 push |
| Path Structure 탭 **Pull** | — | `pull --rebase --autostash` |
| File Manager 탭 Push (그대로) | `profiles/<folder>` 만 | 〃 |

- **Pull 은 git 특성상 브랜치 전체를 받는다**(한 클론에서 경로만 골라 pull 하는 방법은 없다 — `checkout origin/main -- path_structures`
  같은 우회는 HEAD 와 작업 트리를 어긋나게 해서 쓰지 않는다). 다른 PC 가 올린 records 도 같이 들어오지만 File Manager 탭의 Pull 과
  똑같은 결과이고, 이 PC 의 미커밋 records 는 `--autostash` 가 보존한다. **올리는 쪽(Push)은 엄격히 `path_structures/` 만**이다.
- Push 는 브랜치의 **로컬 커밋 전부**를 보낸다(git push 특성). 이전 스크립트가 만든 이전 커밋도 첫 Push 에 함께 나간다 — 의도된 동작.
- Pull 후에는 Path Structure 목록만이 아니라 File Manager 파일 목록도 바뀌었을 수 있으므로 MainWindow 에 알린다(3-5).

---

## 3. 설계 상세

### 3-1. 새 코어 — `app/core/structure_library.py` (UI/DCC 비의존)

```python
# 상수
LIB_DIR = "path_structures"          # 저장소 루트 기준
CAT_DIR = "_categories"              # LIB_DIR 아래
UNCATEGORIZED = ""                   # category id 가 비었거나 모르는 id

@dataclass
class Category:
    id: str
    name: str
    created_by: str = ""
    created_at: str = ""
    def to_dict(self): ...
    @staticmethod
    def from_dict(d): ...

class StructureLibrary:
    """저장소 루트(repo_dir) 하나를 받아 path_structures/ 를 다룬다."""
    def __init__(self, repo_dir): ...
    # 경로
    def lib_dir(self)            -> <repo>/path_structures
    def cat_dir(self)            -> <repo>/path_structures/_categories
    # 카테고리
    def list_categories(self)    -> [Category] 이름 순. 깨진 json 은 건너뛰고 경고 목록에 넣는다.
    def create_category(self, name, author="") -> Category   # 중복 이름이면 ValueError
    def rename_category(self, cat_id, new_name)               # 없는 id / 중복 이름이면 ValueError
    def delete_category(self, cat_id, mode="move")            # mode: "move"(구조 -> Uncategorized) | "delete"(구조도 삭제)
                                                              # 반환: 영향받은 구조 이름 목록
    def category_name(self, cat_id) -> str                    # 모르는 id -> "Uncategorized"
    # 구조 (기존 path_structure 함수에 위임 - store_dir 자리에 repo_dir 을 넘기면 경로가 그대로 맞는다)
    def list_structures(self)    -> [(name, category_id)]     # 모르는 id 는 UNCATEGORIZED 로 정규화
    def grouped(self)            -> [(Category|None, [name...])]  # 트리 채우기용. None = Uncategorized(있을 때만, 맨 뒤)
    def load(self, name) / save(self, structure) / exists(name) / delete(name) / rename(old, new)
    def set_category(self, names, cat_id)                     # 여러 구조를 한 번에 이동. JSON 의 category 만 바꿔 다시 쓴다
    # 이전
    def legacy_files(self)       -> [(data_folder, abs_path)] # <repo>/profiles/*/path_structures/*.json
```

- **경로 재사용**: `path_structure.structures_dir(store_dir)` = `<store_dir>/path_structures` 이므로 `repo_dir` 을 그대로 넘기면
  새 위치와 정확히 같다. `save/load/exists/delete/rename/list_names` 는 **수정 없이** 재사용한다.
- `path_structure.PathStructure` 에 필드 추가: `category: str = ""`. `from_dict` 는 `data.get("category", "") or ""`
  (구버전 JSON → Uncategorized). `to_dict` 는 `asdict` 라 자동 포함.
- `path_structure.list_names()` 는 이름만 준다 → `list_structures()` 는 같은 루프에서 `category` 도 읽는 **새 헬퍼**
  `path_structure.list_entries(store_dir) -> [(name, category)]` 를 추가해 쓴다(파일 한 번만 연다).
- `rename()` 은 JSON 전체를 읽어 다시 쓰므로 `category` 가 보존된다(확인만).
- 카테고리 파일 쓰기는 `json.dump(..., ensure_ascii=False, indent=2)` + `MetaStore._ensure_parent` (기존 관례).
- 시각 문자열은 기존 `"%Y-%m-%d %H:%M:%S"`.

### 3-2. 새 코어 — `app/core/library_settings.py` (PC 단위 설정)

```python
SETTINGS_PATH = os.path.join(prefs.PREFS_DIR, "structure_library.json")
DEFAULTS = {"repo_dir": "", "remote": data_repo.DATA_REPO_REMOTE, "branch": data_repo.DATA_REPO_BRANCH,
            "remote_url": data_repo.DATA_REPO_URL, "recreate_to": "", "expanded": None}

def load(seed_prefs=None) -> dict
    # 파일이 없으면 seed_prefs(활성 프로파일 dict)로 2-4 의 시드 규칙 적용 후 저장하고 반환.
    # 경로 키(repo_dir, recreate_to)는 paths.ui_path 로 정리(v01.46 관례).
def save(data) -> path
```

### 3-3. `app/core/git_sync.py` 수정

1. **범위 인자**: `GitSync.__init__(..., data_folder="", scope_rel="")` — `scope_rel` 이 있으면 `self.data_rel = scope_rel`
   (`profiles/<folder>` 규칙 대신). 라이브러리용은 `GitSync(repo_dir, remote, branch, scope_rel="path_structures")`.
   기존 호출부(`main_window._make_git`)는 그대로 동작.
2. **rebase 충돌 시 abort** (기존 버그 겸): `pull()` 과 `push()` 안의 `pull --rebase` 가 실패하면
   `.git/rebase-merge` 또는 `.git/rebase-apply` 가 있는지 보고 있으면 `git rebase --abort` 실행, 로그에
   `"Pull hit a conflict - the rebase was aborted, nothing was changed. Resolve it in git, then try again."` 를 덧붙여 실패 반환.
   → 저장소가 "rebase 중" 상태로 남아 다음 File Manager Push 까지 막히는 일을 없앤다. (autostash 는 abort 시 복원된다.)
3. **커밋할 게 없을 때**: 지금은 *"No changes to commit ... Pushing anyway."* 후 push 한다. 그대로 둔다
   (이전 커밋처럼 이미 있는 로컬 커밋을 보내려면 필요).
4. `_write_skeleton()` 은 `data_rel` 아래에 records/thumbs 를 만든다 → **`scope_rel` 이 있으면 skeleton 을 만들지 않는다**
   (`path_structures/records` 같은 엉뚱한 폴더 방지). 새 클론(`ensure_repo` clone 경로)은 skeleton 을 안 쓰므로 영향 없음.

### 3-4. UI — `app/ui/path_structure_tab.py`

**생성자**: `PathStructureTab(get_store, get_project_root, get_seed_prefs, log, on_pulled=None)`
- `get_store_dir` 삭제. 대신 탭이 `library_settings.load(get_seed_prefs())` 로 자기 설정을 갖고 `self._lib = StructureLibrary(repo_dir)`.
- `get_store` · `get_project_root` 는 **유지** — Capture 가 `base_rel`(정보용)을 채우고 Preview 가 디스크 파일을 찾는 데만 쓴다.
  목록 · 저장 위치에는 관여하지 않는다(프로파일이 바뀌어도 목록 불변).
- `on_pulled` = Pull 성공 후 호출할 콜백(MainWindow 가 File Manager 목록 재스캔).

**화면** (UI 문자열 영어, 전역 규칙 6장):

```
┌ Save Structure ─────────────────────────────────────────────┐
│ Base Folder [..................................] [Browse...] │
│ Folders to record                              [x] All [Scan]│
│ ┌──────────────────────────────────────────────────────────┐ │
│ └──────────────────────────────────────────────────────────┘ │
│ Name [....................]  Category [Dnable        ▾]      │  ← 새 콤보 (Uncategorized 포함)
│ Capture Depth [1] [x] Include files        [Capture] [Save]  │
└──────────────────────────────────────────────────────────────┘
┌ Saved Structures ───────────────────────────────────────────┐
│ Library  C:/.../JUN_FileManager_data/path_structures         │  ← 라벨(읽기 전용, 툴팁 = 전체 경로)
│          [Browse...]                 [Pull] [Push]  Pull OK  │  ← 이 탭 전용 git
│ ┌ tree ────────────────────────────────────────────────────┐ │
│ │ ▾ Dnable                                            (13) │ │  ← 카테고리 = 굵게 + 폴더 아이콘 + 개수
│ │     Dnable_CH                                            │ │
│ │     ...                                                  │ │
│ │ ▾ MUE                                                (5) │ │
│ │ ▸ Uncategorized                                      (0) │ │  ← 해당 구조가 있을 때만
│ └──────────────────────────────────────────────────────────┘ │
│ [Refresh] [New Category] [Rename] [Delete] [Move To...]  [Recreate] │
│ Recreate To [..............................] [Browse...]     │
│ Preview                         Depth [All] [x] Create files [Expand] │
│ ┌ preview tree (그대로) ────────────────────────────────────┐ │
└──────────────────────────────────────────────────────────────┘
```

- `list_structs`(QListWidget) → **`tree_structs`(QTreeWidget, 헤더 숨김)**. 최상위 = 카테고리, 자식 = 구조.
  - `UserRole` = `("cat", id)` 또는 `("struct", name)`. 높이 `setMaximumHeight(120)` → **약 200** (탭 높이 자동 맞춤 `MOD_tabFit` 이 처리).
  - `JUN_mod_treeExpand_qt_v01(tree_structs)` 한 줄(모든 트리 관례). 펼침 상태는 `expanded` 에 저장.
  - 선택: `ExtendedSelection` — 구조 여러 개를 골라 `Move To...` 할 수 있게. **Preview · Recreate 는 "현재 항목"이 구조일 때만**.
  - 카테고리 노드를 고르면 Preview 를 비운다(`_clear_preview`).
- **버튼 동작**
  | 버튼 | 선택이 카테고리 | 선택이 구조 |
  |------|----------------|------------|
  | `New Category` | `QInputDialog.getText("New Category", "Category name:")` → `create_category`. 만든 뒤 그 노드 선택 | 〃 |
  | `Rename` | `rename_category` | 기존 `on_rename` (구조 이름) |
  | `Delete` | 2-3 의 3지선다 (`QMessageBox` 커스텀 버튼 3개) | 기존 `on_delete`. 여러 개 선택이면 "Delete N structures?" |
  | `Move To...` | 비활성 | `QInputDialog.getItem` (카테고리 이름 목록 + `Uncategorized`) → `set_category(선택 이름들, id)` |
  | `Uncategorized` 노드 선택 시 | Rename / Delete 비활성 | — |
- **Category 콤보 (Save 그룹)**: 카테고리 이름 목록 + `Uncategorized`(data `""`). 기본값 = 트리에서 지금 고른 카테고리
  (구조를 골랐으면 그 구조의 카테고리). `on_save` 가 `self._pending.category = 콤보 id`. **덮어쓰기 저장일 때**는
  콤보 값으로 카테고리도 바뀐다(문구에 표시: *"Overwrite? It will be saved in category 'X'."*).
- **Library 줄**:
  - `Browse...` = 클론 폴더(저장소 루트) 선택. `.git` 없는 폴더면 경고 *"Not a git clone. Pull will clone the data repo here if the folder is empty."*
    → 설정 저장 → `self._lib` 재생성 → 새로고침.
  - `Pull`: `GitSync(repo_dir, ..., scope_rel="path_structures")`. 저장소가 없으면 `ensure_repo(remote_url)`(빈 폴더면 clone),
    `check_branch()` 실패면 로그 + 중단(전환은 File Manager 의 `Switch to main` 이 담당 — 여기선 안내만). 성공하면 `on_refresh()` + `on_pulled()`.
  - `Push`: 메시지 `"Update path structures by {user} on {PC} ({time}) [path_structures]"` —
    `user` = `getpass.getuser()`, `PC` = `os.environ.get("COMPUTERNAME", "")` (프로파일의 Author 를 쓰지 않는다 — 독립).
    결과를 상태 라벨(`Push OK` / `Push failed`)과 로그에.
  - Pull/Push 는 File Manager 탭과 같은 **동기 호출**(UI 잠깐 멈춤 허용, 기존 관례). 버튼은 실행 중 `setEnabled(False)`.
- **Recreate To**: 값은 `library_settings` 의 `recreate_to`. 칸의 `editingFinished` · Browse 후 · 창 닫을 때 저장.
  `recreate_to()` / `set_recreate_to()` 공개 메서드는 삭제(MainWindow 가 더 안 쓴다) — 대신 `save_settings()` 를 공개.
- **로그 문구 교체**: `"Saved locally - use Push on the File Manager tab to sync."` →
  `"Saved locally - use Push in the Saved Structures group to share it."` (Rename · Delete · 카테고리 작업도 같은 안내).
- **레거시 경고**: `on_refresh()` 때 `self._lib.legacy_files()` 가 비어 있지 않으면 로그에 한 번
  `"[Warning] N structure(s) still in the old per-profile folders (profiles/*/path_structures). Run the migration (see docs) - they are not listed here."`
  (이전 전 · 옛 버전 툴을 쓰는 PC 가 옛 위치에 저장한 경우를 잡는다.)
- Store Repo 미설정 경고 `"Set Store Repo first (File Manager tab)."` → `"Set the Library folder first (Browse... in Saved Structures)."`

### 3-5. `app/ui/main_window.py` 수정

| 위치 | 변경 |
|------|------|
| `PathStructureTab(...)` 생성 (현재 338행 부근) | `get_store_dir=self.get_store_dir` 삭제 → `get_seed_prefs=lambda: self._prefs`, `on_pulled=self.on_scan` 추가 |
| `_load_prefs_to_ui` (814행 부근) | `self.path_structure_tab.set_recreate_to(...)` **삭제** |
| `_collect_prefs` (851행 부근) | `"recreate_to": self.path_structure_tab.recreate_to(),` **삭제**. 옛 프로파일의 `recreate_to` 값은 남아도 무해(읽기만 하고 안 씀). `prefs.PATH_KEYS` · `DEFAULTS` 의 `recreate_to` 도 남겨 둔다(시드 소스) |
| `_refresh_other_tabs` (947행) | `self.path_structure_tab.on_refresh()` **삭제** — 프로파일 · Source Mode · Data Folder 전환이 목록을 건드리지 않게 |
| `on_pull` (1532행) 성공 분기 | `self.on_scan()` 뒤에 `self.path_structure_tab.on_refresh()` 추가 — File Manager Pull 도 브랜치 전체를 받으므로 새 구조가 들어왔을 수 있다 |
| `closeEvent` | `self.path_structure_tab.save_settings()` 호출 추가(try/except, 기존 패턴) |
| Git 그룹 제목 | 변경 없음(*records / thumbnails only* — 원래도 구조는 이제 안 올린다는 뜻과 맞다) |

### 3-6. 일회성 이전 — `tools/A00210_FileManager/dev/migrate_structure_library.py`

> `dev/` 는 툴 안 개발용(릴리즈 제외 대상인지 4장 단계 7에서 A00510 규칙 확인). 사용자가 직접 한 번 돌린다.

```
python migrate_structure_library.py <repo_dir> [--apply] [--author NAME]
```

1. 검사: `<repo_dir>/.git` 존재 · 현재 브랜치 `main` · `git status --porcelain -- path_structures "profiles/*/path_structures"` 가 **비어 있음**
   (records 쪽 미커밋 변경은 무관 — 검사 대상 아님). `rebase-merge` 없음. 하나라도 어긋나면 이유 출력 후 종료 코드 1.
2. `git pull --rebase --autostash origin main` (최신에서 시작).
3. 계획 수립 (`--apply` 없으면 여기까지 출력만 = dry-run):
   - `profiles/*/path_structures/*.json` 을 모은다.
   - 데이터 폴더 이름마다 카테고리 하나(이미 같은 이름 카테고리가 있으면 재사용 — **재실행해도 안전**).
   - 목적지 `path_structures/<같은 파일명>`. **이미 있으면**(이름 충돌) `<stem>_<data_folder>.json` 으로, 표시 이름도 같은 접미사.
     지금 데이터엔 충돌 없음(1-2) — 규칙은 다른 PC 대비.
4. `--apply`:
   - 카테고리 파일 생성.
   - 파일마다 `git mv <src> <dst>` → dst JSON 을 읽어 `category` = 해당 id (이름 바꿨으면 `name` 도) → 다시 쓰기.
   - `git add -- path_structures` (카테고리 파일 + 수정분), `profiles/*/path_structures` 의 삭제는 `git mv` 가 이미 스테이징.
   - `git commit -m "Move path structures to shared library (A00210 v01.60) [path_structures]"`  ← **푸시하지 않는다.**
   - 출력: 옮긴 수 · 카테고리 · 커밋 해시 · *"Push it with the Path Structure tab's Push (or git push) when ready."*
5. 원격 반영은 사용자가 툴의 Path Structure **Push** 를 누를 때(또는 그 턴에 요청받아 git push) — 이 Push 는 로컬 커밋 전부를 보내므로 이전 커밋도 같이 나간다.

**다른 PC**: 새 버전 툴 설치 → Path Structure 탭 `Pull` 한 번. 이전 커밋이 들어오면서 옛 폴더는 사라지고 새 목록이 보인다.
옛 버전 툴을 쓰는 PC 가 그 뒤 옛 위치에 저장하면 → 새 버전의 레거시 경고(3-4)가 잡고, 스크립트를 다시 돌리면 이어서 옮긴다(멱등).

---

## 4. 구현 단계 (순서대로, 단계마다 검증)

| # | 작업 | 파일 | 완료 기준 |
|---|------|------|-----------|
| 1 | `PathStructure.category` 필드 + `list_entries()` | `app/core/path_structure.py` | 구버전 JSON → `""`, 저장 · 로드 · rename 왕복에 category 보존 |
| 2 | `StructureLibrary` + `Category` | `app/core/structure_library.py` (새) | 5장 L1~L12 통과 |
| 3 | PC 단위 설정 | `app/core/library_settings.py` (새) | 시드 규칙 · 경로 정리 · 왕복 (S1~S3) |
| 4 | `GitSync` `scope_rel` + rebase abort + skeleton 건너뛰기 | `app/core/git_sync.py` | 5장 G1~G5 (로컬 bare 원격) |
| 5 | 이전 스크립트 | `dev/migrate_structure_library.py` (새) | 5장 M1~M5 (임시 클론) · **실제 클론에서 dry-run 출력 확인** |
| 6 | 탭 UI 개편 | `app/ui/path_structure_tab.py` | 5장 U1~U12 (오프스크린) |
| 7 | MainWindow 연결 정리 | `app/ui/main_window.py` | U13~U15, 기존 `tests/test_ui_paths.py` 수정 후 통과(아래) |
| 8 | 기존 시험 전부 | `tests/*.py` | 전부 PASS (`PYTHONIOENCODING=utf-8` — cp949 콘솔 함정) |
| 9 | 실제 이전 | 이 PC 클론 | `--apply` → 커밋 1개, `git show --stat` 에 `path_structures/` 와 `profiles/*/path_structures/` 만. **푸시는 하지 않는다** |
| 10 | GUI 실기 | standalone 실행 | 6장 체크리스트 |
| 11 | 버전 · 문서 | `app/config/version.py`(01.60), `CHANGELOG.md`, `JUN_All/docs/A00210_FileManager.md` §4-C, `docs/WORKLOG.md`, 메모리, (포트폴리오 규칙 해당 시) | 8장 |
| 12 | 원격 반영 | — | **사용자가 그 턴에 "푸시해" 할 때만**: Maya_Python → `Dnable_repo` `dev`, 데이터 저장소 → 툴 Path Structure Push(이전 커밋 포함) |

`tests/test_ui_paths.py` 수정 메모: 83 · 85행이 `win.path_structure_tab.ipf_recreate_to.text()` 를 프로파일 왕복 값으로 비교한다.
Recreate To 가 프로파일에서 빠지므로 이 비교에서 `recreate_to` 를 빼고, 54 · 57행 프로파일 dict 의 `recreate_to` 는 그대로 둬도 된다
(무시되는지 확인하는 셈). 시험이 `~/.jun_filemanager` 를 실제로 건드리지 않게 `library_settings.SETTINGS_PATH` 를 임시 경로로 바꿔 끼운다
(시험 안에서 모듈 속성 덮어쓰기 — `prefs.PREFS_DIR` 를 다루는 기존 방식이 있으면 그대로 따른다).

---

## 5. 시험 — `tests/test_structure_library.py` (새, 오프스크린 · 임시 폴더 · 표준 python)

형식은 `tests/test_path_structure_prune.py` 와 같게(`check(name, cond, extra)` · 마지막에 PASS 수 / 전체).
git 시험은 `tempfile` 안에 `git init --bare remote.git` + 클론 두 개(PC A / PC B)로 실제 push/pull.

**코어 — 라이브러리**
- L1 빈 저장소 → `list_categories() == []`, `grouped() == []`
- L2 `create_category("Character")` → `_categories/<id>.json` 생성, id 8자 hex
- L3 같은 이름(대소문자만 다름) 생성 → ValueError
- L4 `rename_category` → 카테고리 파일만 바뀌고 구조 JSON 은 바이트 그대로
- L5 구조 저장 시 category 기록 · `list_structures()` 가 (이름, id) 반환
- L6 모르는 id 를 가진 구조 → Uncategorized 로 묶임, `grouped()` 맨 뒤
- L7 `delete_category(mode="move")` → 구조 남고 category `""`
- L8 `delete_category(mode="delete")` → 구조 파일도 삭제, 반환 목록 일치
- L9 `set_category([a, b], id)` → 두 파일만 바뀜, 다른 필드(folders · files · created_at) 보존
- L10 구조 `rename` 후 category 보존
- L11 `_categories` 폴더 · `_` 로 시작하는 json 이 구조 목록에 안 섞임
- L12 `legacy_files()` 가 `profiles/X/path_structures/*.json` 를 찾음

**코어 — 설정**
- S1 파일 없음 + seed(git 모드, store_dir=D, recreate_to=R) → repo_dir=D, recreate_to=R, 파일 생성
- S2 파일 없음 + seed(local 모드) → repo_dir = `DEFAULT_STORE_DIR`
- S3 저장 → 다시 load 왕복, 경로 `\` → `/` 정리

**git**
- G1 PC A 에서 구조 저장 + `profiles/Dnable/records/x.json` 도 수정 → 라이브러리 Push → 원격 커밋에 `path_structures/` 만, records 는 A 에 **미커밋으로 남음**
- G2 PC B Pull → 구조 보임
- G3 A · B 가 **서로 다른 카테고리**를 동시에 만들고 각각 Push → 두 번째가 거절 → 자동 재시도로 성공, 양쪽 카테고리 다 원격에
- G4 A · B 가 **같은 구조**를 다르게 고쳐 Push → 두 번째 실패 · `rebase --abort` 됨(`.git/rebase-merge` 없음) · 로컬 커밋 · 파일 보존 · 메시지에 "aborted"
- G5 기존 `GitSync(data_folder="Dnable")` 동작 불변(기존 `tests/test_data_folders.py` 통과로 확인)

**이전 스크립트** (임시 클론에 1-2 와 같은 모양의 옛 폴더를 만들어서)
- M1 dry-run → 파일 변경 · 커밋 없음, 계획 출력에 20개 같은 수
- M2 `--apply` → 커밋 1개, 옛 위치 비고 새 위치에 전부, 카테고리 = 데이터 폴더 이름들, 각 JSON category 일치
- M3 `git log --follow path_structures/Dnable_CH.json` 이 옛 기록까지 이어짐(이력 보존)
- M4 다시 `--apply` → "nothing to migrate", 커밋 없음(멱등). 옛 위치에 새 파일을 하나 더 만들고 다시 → 그것만 옮기고 기존 카테고리 재사용
- M5 이름 충돌(두 데이터 폴더에 같은 파일명) → 두 번째가 `<stem>_<folder>.json`, 표시 이름도 접미사
- M6 records 쪽 미커밋 변경이 있어도 진행되고, 그 변경은 커밋에 안 들어감

**UI (오프스크린, MainWindow 째)**
- U1 트리: 카테고리 최상위 · 구조 자식 · 개수 표시 · 이름 순 · Uncategorized 맨 아래 / 없으면 숨김
- U2 **프로파일 전환(Data Folder Dnable → JUN) 후 트리 항목 · 선택 불변** ← 요청 1 의 핵심
- U3 **Source Mode git → local 전환 후에도 불변**
- U4 New Category → 노드 생김 · 선택됨 (`QInputDialog` 는 몽키패치)
- U5 카테고리 Rename / 구조 Rename 이 선택 종류에 따라 갈림
- U6 카테고리 Delete 3지선다 각각(Move / Delete Structures Too / Cancel)
- U7 Move To... 로 구조 2개 이동 → 트리 반영
- U8 Save 그룹 Category 콤보 = 트리에서 고른 카테고리 기본, 저장 후 그 카테고리 아래에 나타나고 선택됨
- U9 카테고리 노드 선택 → Preview 비움, Recreate 경고 *"Select a structure first."*
- U10 Uncategorized 선택 → Rename · Delete 비활성
- U11 Recreate To 가 `structure_library.json` 에 저장 · 복원(프로파일 dict 에는 안 들어감)
- U12 레거시 파일이 있으면 경고 로그 한 번
- U13 `_collect_prefs()` 결과에 `recreate_to` 없음
- U14 File Manager Pull 성공 경로에서 `path_structure_tab.on_refresh` 호출됨(스텁 git 으로)
- U15 기존 v01.59 Recreate 시험(`test_path_structure_prune.py` UI 부분)이 새 생성자 · 트리로 통과하도록 같이 고침

---

## 6. GUI 실기 체크리스트 (사용자 확인용)

1. 툴 실행 → Path Structure 탭 → 카테고리 `Dnable` · `JUN` · `MUE` · `SA` 아래 20개 전부 보인다.
2. 상단 Profile 을 `Local_CH_D` → `JUN` → `MUE` 로 바꿔도 목록 · 선택 · Recreate To 가 그대로다.
3. `New Category` 로 `Character` 생성 → `Dnable_CH` · `Dnable_CH_UE` 를 Ctrl 로 골라 `Move To...` → `Character`.
4. `Dnable` 카테고리 이름을 `Dnable_Old` 로 바꾸기, 빈 카테고리 만들고 지우기.
5. Path Structure `Push` → 로그에 `[path_structures]` 커밋, File Manager 쪽 미커밋 records 는 그대로(File Manager Push 로 따로).
6. 다른 PC: 새 버전 설치 → Path Structure `Pull` → 같은 카테고리 · 목록.
7. Recreate 는 예전과 똑같이 동작(Depth · 체크 해제 · Create files · Recreate To).
8. 창 높이: 트리가 커졌어도 탭 높이 자동 맞춤으로 잘리지 않는다.

---

## 7. 결정 사항 (기본값으로 설계함 — 다르게 원하면 구현 전에 말할 것)

| # | 질문 | 이 계획의 기본값 | 대안 |
|---|------|-----------------|------|
| D1 | 라이브러리를 어디에 두나 | **지금 데이터 저장소 루트 `path_structures/`** (클론 · 자격증명 · 원격 그대로) | 새 저장소 `JUN_PathStructures` — 완전 분리지만 GitHub 저장소 생성 · 모든 PC 클론 추가 필요 |
| D2 | 첫 카테고리 | **옛 데이터 폴더 이름(Dnable · JUN · MUE · SA)** 으로 자동 생성 | 전부 Uncategorized 로 두고 사용자가 직접 분류 |
| D3 | 구조 이름 유일 범위 | **라이브러리 전체** | 카테고리 안에서만(같은 이름 다른 카테고리 허용 — 파일을 카테고리 폴더로 나눠야 해서 2-2 A 의 단점이 따라온다) |
| D4 | 카테고리 삭제 시 안의 구조 | **3지선다(기본 Move to Uncategorized)** | 비어 있을 때만 삭제 허용 |
| D5 | Recreate To | **프로파일 → PC 단위 설정으로 이동** (독립) | 프로파일에 그대로 |
| D6 | Pull 범위 | **브랜치 전체를 받음(git 한계), 올리기만 `path_structures/` 한정** | 완전 한정 받기는 D1 의 새 저장소안이어야 가능 |
| D7 | Local (Shared/NAS) 모드 프로파일 | **라이브러리는 모드와 무관하게 git 클론**을 쓴다 | local 모드면 `<Shared Folder>/path_structures` — 이 경우 "프로파일 무관" 이 깨진다 |
| D8 | 카테고리 중첩(하위 카테고리) | **없음(한 단계)** | 2단계 이상 — 필요해지면 `parent` 필드 추가로 확장 가능하게 id 방식을 택해 둠 |

---

## 8. 문서 · 기록 (단계 11)

- `app/config/version.py`: 주석 `# 01.60  Path Structure - Saved Structures 를 프로파일에서 독립 ...` + `VERSION = "01.60"`, `LAST_UPDATE`.
- `CHANGELOG.md` `[01.60]`: 위치 이동 · 카테고리 · 탭 전용 Pull/Push · Recreate To PC 단위 · 이전 스크립트 · rebase abort.
- `JUN_All/docs/A00210_FileManager.md`:
  - §4-C 제목에 `라이브러리 독립 · 카테고리 v01.60` 추가, 화면 목업 교체, "저장 위치" · "카테고리" · "Pull / Push" · "이전(한 번만)" 소절 추가.
  - §1 핵심 개념 / §5 구조(개발자용)의 데이터 배치 그림에 `path_structures/` 를 저장소 루트로 고친다(프로파일 폴더 아래에서 뺀다).
- 파일 헤더 `last Update date` + 버전 이력 주석: `path_structure.py`, `path_structure_tab.py`, `git_sync.py`, `main_window.py`.
- `JUN_All/docs/WORKLOG.md`(현재 월, 최신이 위 · 날짜 헤딩 중복 금지).
- 메모리: `wip-a00210-structure-library.md` 새로 + `index-tools.md` A00210 줄에 링크, 이 계획서 경로 명시.
- 포트폴리오(EN/KR) — 메모리 규칙 `update-portfolio-on-tool-work` 에 해당하면 함께.

---

## 9. 위험 · 주의

- **미커밋 records 섞임** — 클론에 다른 작업의 records 변경이 있다(1-2). 이전 스크립트 · 탭 Push 모두 경로 한정 `add` 만 쓴다.
  `git add -A`(경로 없이) 를 절대 쓰지 않는다. G1 · M6 시험이 이것을 지킨다.
- **옛 버전 툴을 쓰는 다른 PC** — 이전 후에도 옛 위치에 저장할 수 있다. 레거시 경고 + 스크립트 재실행(멱등)으로 흡수.
  모든 PC 를 v01.60 으로 올리는 것이 근본 해결 — 반영 공지에 적는다.
- **같은 클론을 두 탭이 공유** — File Manager Push 와 Path Structure Push 가 동시에 돌 일은 없다(둘 다 동기 호출, UI 스레드).
- **rebase 충돌** — 지금 코드는 abort 하지 않아 클론이 rebase 중으로 남는다. 3-3 에서 고친다. 고친 뒤에도 사용자가 직접 git 으로
  풀어야 하는 경우의 안내문을 문서 §4-C 에 둔다.
- **파일 이름 의존 금지**(메모리 `no-filename-dependent-data`) — 카테고리는 JSON 의 `category` id 로만 정한다. 파일명 · 폴더명에서
  카테고리를 읽지 않는다. (이전 스크립트가 옛 **폴더 이름**으로 카테고리 이름을 만드는 것은 일회성 출력 이름이라 해당 없음.)
- **PySide 버전** — A00210 은 `Framework.qt.qt` 래퍼로 import 한다. 새 위젯도 그 래퍼에서만 가져온다(`QInputDialog.getItem` 포함 확인).
- **원격 작업은 그 턴 요청 때만** — 이전 커밋 · 코드 커밋 모두 로컬까지. 데이터 저장소 Push 와 Maya_Python Push 는 각각 사용자 지시가 있을 때.
