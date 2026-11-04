# A00210_FileManager — 데이터 저장소: "프로파일마다 브랜치" → "브랜치 하나 + 프로파일 폴더" 작업 계획서

> **작성** 2026-11-04 · 상태: **계획 (구현 전)** · 대상 A00210 v01.44 → **v01.45**, 함께 바뀌는 곳 A00211_RefLineage
> 이 문서만 보고 작업할 수 있게 쓴다. 순서대로 하고, 각 단계 끝의 **확인** 을 통과해야 다음으로 간다.
> 원격을 바꾸는 단계(§5 · §7)는 **그 턴에 사용자 푸시 요청이 있을 때만** 실행한다(전역 규칙 2장).

---

## 0. 왜 바꾸나 (2026-11-04 관찰)

| 저장 폴더(클론) | 원격 | 브랜치 | 쓰는 프로파일 (`~/.jun_filemanager/profiles/*.json`) |
|----------------|------|--------|-----------------------------------------------------|
| `0030_maya_python_JUN/JUN_FileManager_data` | `elom1213/JUN_FileManager_data` (공개) | `Dnable` | Default · HDN · Local_CH_C · Local_CH_D · Local_PJ_root · NAS_Character · Template |
| `JUN_FileManager_data_all/A0030_Src_Rig` | 같은 저장소 | `src_rig` | Rig_Src |
| `JUN_FileManager_data_all/A0020_SA` | 같은 저장소 | `SA` | soundAliance (**프로파일의 branch 값은 `Dnable` — 어긋남**, §3-4) |
| `JUN_FileManager_data_all/A0010_MEU` | `elom1213/JUN_FileManager_data_Private` (비공개) | `MUE` | MUE |

문제: ① 브랜치마다 클론 폴더가 하나씩 늘어난다 ② `Dnable` 한 브랜치에 7개 프로파일 데이터가 이미 섞여 있다(브랜치가 프로파일을
나누지 못함) ③ GitHub 기본 화면 = `master`(06-19 이후 멈춤)라 전체가 안 보이고, 브랜치들이 master 에서 갈라져 정리 커밋이 섞인다
④ 프로파일 branch 값과 클론의 실제 브랜치가 어긋나도 아무도 모른다.

## 1. 목표 구조

```
JUN_FileManager_data            (공개, 브랜치 main 하나, PC 당 클론 하나)
└─ profiles/
   ├─ Dnable/   lineage/ path_structures/ records/ thumbs/     ← 지금 Dnable 브랜치 전체
   ├─ SA/       path_structures/ records/ thumbs/              ← 지금 SA
   └─ src_rig/  records/ thumbs/                               ← 지금 src_rig
JUN_FileManager_data_Private    (비공개, 브랜치 main 하나)
└─ profiles/
   └─ MUE/      lineage/ path_structures/ records/ thumbs/     ← 지금 MUE
```

- **프로파일 설정에 `data_folder` 를 둔다** = `profiles/` 아래 폴더 이름. 여러 프로파일이 같은 폴더를 써도 된다(지금 7개가 Dnable 공유 — 그대로).
- 실제 데이터 폴더 = `<store_dir>/profiles/<data_folder>` (이하 **data_dir**). records · thumbs · lineage · path_structures 는 전부 data_dir 아래.
- 브랜치는 `main` 하나. 비공개가 필요한 데이터만 **저장소를 나눈다**(GitHub 읽기 권한은 저장소 단위 — 브랜치로는 못 막는다).
- 폴더 이름은 **지금 브랜치 이름 그대로**(Dnable · SA · src_rig · MUE) — 옮기기와 프로파일 변환이 1:1 이 된다. 이름을 바꾸고 싶으면 마지막에 `git mv` 한 번.
- `master` 는 폴더로 옮기지 않는다: master 의 데이터는 Dnable 에 다 있고, 없는 4개(`lineage/LUN_Test.json` · `Test_02` · `Test_03` · `path_structures/Test.json`)는
  Dnable 에서 일부러 지운 시험 파일이다 → `archive/master` 태그로만 보존. 비공개 저장소의 `master` · `private` 는 `MUE` 의 조상이라 역시 태그로만.

## 2. 사전 상태 (2026-11-04 11:30 기준 — 옮기기 직전 다시 확인)

| ref | 커밋 | 파일 수 |
|-----|------|--------|
| 공개 `origin/master` | `670743b` | 27 |
| 공개 `origin/Dnable` | `4690a34` | **265** |
| 공개 `origin/SA` | `47bda85` | **11** |
| 공개 `origin/src_rig` | `e8d7bba` | **7** |
| 비공개 `origin/master` · `origin/private` | `fe5aabd` · `49a50bf` | 23 · — (둘 다 MUE 의 조상) |
| 비공개 `origin/MUE` | `51f4b2a` | **128** |

모든 클론이 깨끗하고 원격과 같다(2026-11-04 Dnable 미반영 82건을 `4690a34` 로 푸시함). 옮기기 전에 **다른 PC 에서도 Push 를 끝내 둔다**.

---

## 3. 코드 변경 (A00210 v01.45) — 원격 변경 없이 먼저 끝낸다

### 3-1. `app/config/data_repo.py`

```python
DATA_REPO_BRANCH = "main"          # was "master"
DATA_PROFILES_DIR = "profiles"     # 새 상수: 저장소 안 프로파일 폴더들의 부모
DEFAULT_DATA_FOLDER = "Dnable"     # 새 상수: data_folder 가 비었을 때
```

### 3-2. `app/core/prefs.py` — `data_folder` 키 + 옛 프로파일 변환 + data_dir 계산(공용 함수)

1. `DEFAULTS` 에 `"data_folder": ""` 추가.
2. `_apply_defaults(data)` 끝에 변환 규칙(파일은 저장할 때 새 값으로 바뀐다):
   ```python
   if not prefs.get("data_folder"):
       old = (data or {}).get("branch", "")
       prefs["data_folder"] = _LEGACY_FOLDER_BY_STORE.get(_norm(prefs.get("store_dir"))) \
           or {"master": "Dnable", "main": "Dnable", "": "Dnable"}.get(old, old) or data_repo.DEFAULT_DATA_FOLDER
   if prefs.get("branch") in ("master", "Dnable", "SA", "src_rig", "MUE", "private", ""):
       prefs["branch"] = data_repo.DATA_REPO_BRANCH          # 이제 브랜치는 main 하나
   ```
   - `_LEGACY_FOLDER_BY_STORE` = **저장 폴더 이름 → 데이터 폴더** 표. 프로파일의 branch 값이 틀린 경우(soundAliance)를 바로잡는 근거:
     `{"A0020_SA": "SA", "A0030_Src_Rig": "src_rig", "A0010_MEU": "MUE"}` (키 = `os.path.basename(store_dir)`). 나머지는 branch 값 → 폴더.
3. 새 공용 함수(A00211 도 쓴다):
   ```python
   def data_dir_of(prefs):
       """프로파일 세팅 → 실제 데이터 폴더. local 모드는 Shared Folder 그대로(폴더 규칙 없음)."""
       if prefs.get("source_mode") == "local":
           return prefs.get("local_dir", "")
       store = prefs.get("store_dir", "")
       folder = prefs.get("data_folder") or data_repo.DEFAULT_DATA_FOLDER
       return os.path.join(store, data_repo.DATA_PROFILES_DIR, folder) if store else ""
   ```
4. 이 PC 프로파일 10개의 변환 결과(시험 기대값):

   | 프로파일 | data_folder | branch |
   |---------|-------------|--------|
   | Default · HDN · Local_CH_C · Local_CH_D · Local_PJ_root · NAS_Character · Template | Dnable | main |
   | Rig_Src | src_rig | main |
   | soundAliance | **SA** (저장 폴더 표로 교정) | main |
   | MUE | MUE | main |

### 3-3. `app/core/git_sync.py` — 받기 · 올리기 순서

| 함수 | 지금 | 바꾼 뒤 |
|------|------|--------|
| `__init__(store_dir, remote, branch)` | — | 인자 `data_folder=""` 추가 → `self.data_rel = f"profiles/{data_folder}"` |
| `pull()` | `pull <remote> <branch>` | `pull --rebase --autostash <remote> <branch>` |
| `push(message)` | `add -A` → commit → push | ① `add -A -- <data_rel>` (**내 폴더만**) ② `diff --cached --quiet` 로 바뀐 게 없으면 commit 생략 ③ `pull --rebase --autostash` ④ push ⑤ 거절(`rejected`/`non-fast-forward`)이면 ③④ 한 번 더 |
| (새) `current_branch()` | — | `rev-parse --abbrev-ref HEAD` |
| (새) `check_branch()` | — | 현재 브랜치 ≠ `self.branch` 면 `(False, "This clone is on '<x>', profile expects '<y>'. Run Switch to main.")` — pull/push 앞에서 호출, 어긋나면 **아무것도 안 한다** |
| `_write_skeleton()` | `records/` `thumbs/` + `.gitignore` | `<data_rel>/records`, `<data_rel>/thumbs` + 루트 `.gitignore`(새로 만드는 저장소만 — 지금 원격 브랜치들엔 `.gitignore` 가 없다) |
| `list_branches()` | 유지 | 유지(고급 칸) |
| (새) `list_data_folders()` | — | `profiles/` 아래 폴더 이름(정렬). 원격 것까지 보려면 pull 뒤 |

> 다른 프로파일 폴더의 미커밋 변경은 이 프로파일 Push 에 섞이지 않는다(①). `--autostash` 가 그 변경을 지켜 준다.

### 3-4. `app/ui/main_window.py`

1. **Settings 에 `Data Folder` 줄** (Store Repo 줄 아래): 편집 가능한 `QComboBox` `self.cmb_data_folder`, 목록 = `GitSync.list_data_folders()`(콤보를 펼칠 때 갱신 — `_BranchComboBox` 와 같은 방식), 새 이름 입력 = 새 폴더.
   툴팁: `"Folder under <Store Repo>/profiles/ that holds this profile's records. Profiles may share a folder."`
2. 프로파일 읽기(현 774행 근처)에 `self.cmb_data_folder.setCurrentText(self._prefs.get("data_folder", ...))`, 저장(현 810행 근처 dict)에 `"data_folder": ...`.
3. `_effective_store_dir()`(현 932행) — **data_dir 을 돌려주게** 바꾼다: `return prefs.data_dir_of({...지금 UI 값...})`.
   `get_store_dir()` · `_make_store()` · Lineage / Path Structure 탭의 `get_store_dir` 콜러블이 모두 이걸 쓰므로 **records · thumbs · lineage · path_structures 가 한 번에 data_dir 로 옮겨간다.**
   git 쪽은 저장소 루트가 필요하므로 `_make_git()`(현 1001행)은 `self.ipf_store_dir.text()`(루트)를 그대로 쓰고 `data_folder=` 를 넘긴다.
4. `on_pull` / `on_push`(현 1430 · 1454행) 맨 앞에 `ok, msg = git.check_branch()` → 실패면 로그 + `lbl_git_status = "Wrong branch"` + 끝.
5. **`Switch to main` 버튼**(Git Sync 그룹, check_branch 실패 때만 보이게): `git fetch` → 미커밋 변경 있으면 거부(먼저 Push 하라고) → `git checkout main`(없으면 `checkout -b main --track origin/main`).
6. Remote / Branch 칸은 그대로 두되 Branch 기본값 `main`.
7. 상태 표시: Git 그룹 제목 옆에 `profiles/<folder>` 를 보여 준다(어느 폴더를 올리는지 눈으로 확인).

### 3-5. `tools/A00211_RefLineage/app/core/ref_scanner.py`

38행 근처 `prefs.json 에서 store_dir 을 읽어 MetaStore` → **`fm_prefs.data_dir_of(prefs)`** 로 MetaStore · lineage 경로를 만든다.
(A00480 Reference > Lineage 는 A00211 을 그대로 쓰므로 함께 따라온다 — 따로 고칠 것 없음, 확인만.)

### 3-6. 버전 · 문서

- `app/config/version.py` `01.45` + 이력 주석, `CHANGELOG.md`, `docs/A00210_FileManager.md`(Settings 표에 Data Folder, 1장 데이터 구조 그림, "옛 브랜치 클론 정리" 절), WORKLOG, 메모리(`wip-a00210-...`).

### 3-7. 시험 (`tests/test_data_folders.py`, 표준 python + 임시 폴더, 네트워크 없음)

1. **변환**: §3-2 표의 10개 프로파일 dict(저장 폴더 경로 포함)를 `_apply_defaults` 에 넣어 data_folder · branch 기대값 확인. 이미 data_folder 가 있으면 건드리지 않음.
2. **data_dir_of**: git 모드 = `<store>/profiles/<folder>`, local 모드 = local_dir, store 비면 "".
3. **동시 Push**: 임시 bare 저장소 + 클론 A · B, A 는 `profiles/X/records/a.json`, B 는 `profiles/Y/records/b.json` 을 거의 동시에 Push → 둘 다 성공(B 는 rebase 후 재시도), 최종 main 에 두 파일.
4. **내 폴더만**: 클론 A 에 `profiles/Y/records/stray.json` 미커밋 변경을 두고 X 프로파일로 Push → 커밋에 stray 없음, stray 는 작업 트리에 그대로.
5. **check_branch**: 클론을 `SA` 브랜치로 두고 Push → 거부, 아무 커밋도 안 생김.
6. **UI(오프스크린)**: Data Folder 콤보 목록 = profiles 하위 폴더, 프로파일 전환 시 값 전환, Save Record 가 `profiles/<folder>/records/...` 에 쓰는지.
7. 기존 시험(`test_export_*`) 그대로 통과.

**확인**: 1~7 통과. 이 단계까지는 원격을 건드리지 않는다. Maya_Python 로컬 커밋.

---

## 4. 옮기기 리허설 (원격 변경 없음) — 공개 저장소

작업 폴더는 **새 임시 폴더**(기존 클론은 손대지 않는다). 예: `C:/Users/USER/Desktop/JP/0030_maya_python_JUN/_migrate`.

```bash
cd C:/Users/USER/Desktop/JP/0030_maya_python_JUN/_migrate
git clone --mirror https://github.com/elom1213/JUN_FileManager_data.git backup_public.git   # 통째 백업(지우지 말 것)
git clone https://github.com/elom1213/JUN_FileManager_data.git public && cd public
git remote set-url --push origin DISABLED_NO_PUSH        # 리허설 중 실수 푸시 방지 (§5 에서 되돌림)
git fetch origin

# (1) main = Dnable 의 기록을 이어받고, 최상위 4폴더를 profiles/Dnable 로 이동
git checkout -b main origin/Dnable
mkdir -p profiles/Dnable
git mv lineage path_structures records thumbs profiles/Dnable/
git commit -m "Restructure: move Dnable data into profiles/Dnable"

# (2) SA, src_rig 를 폴더로 합친다 — 각 브랜치 기록을 main 기록에 남기는 방식(merge -s ours + read-tree)
for B in SA src_rig; do
  git merge -s ours --no-commit --allow-unrelated-histories origin/$B
  git read-tree --prefix=profiles/$B/ -u origin/$B
  git commit -m "Restructure: merge branch $B into profiles/$B"
done
```

**확인 (리허설 결과 — 하나라도 틀리면 멈춘다)**
```bash
git ls-tree --name-only main                 # profiles  (최상위에 records/thumbs 가 없어야)
git ls-tree --name-only main:profiles        # Dnable SA src_rig
for B in Dnable SA src_rig; do echo $B $(git ls-tree -r --name-only main:profiles/$B | wc -l) $(git ls-tree -r --name-only origin/$B | wc -l); done
#   두 숫자가 같아야 한다 (265 · 11 · 7)
git log --oneline main | head -5                               # merge 커밋 2개 + restructure 1개
git merge-base --is-ancestor origin/SA main && echo SA-history-kept
git merge-base --is-ancestor origin/src_rig main && echo src_rig-history-kept
```
> 파일 비교는 `git diff <브랜치> main:profiles/<B>` 대신 다음이 확실하다:
> `diff <(git ls-tree -r origin/$B | awk '{print $3, $4}' | sort) <(git ls-tree -r main:profiles/$B | awk '{print $3, $4}' | sort)` — **blob 해시 · 경로가 전부 같아야** 한다(출력 0줄).

**2026-11-04 리허설 실측**(scratchpad 임시 클론, push URL 막아 둠 — 원격 변경 없음): 위 명령 그대로 실행 →
최상위 `profiles` 하나, `profiles` = `Dnable SA src_rig`, 파일 수 **265=265 · 11=11 · 7=7, blob 차이 0줄**, 세 브랜치 모두 `main` 의 조상(기록 보존),
`git log --follow profiles/Dnable/records/...` 가 옛 기록까지 3커밋 추적, 가장 긴 경로 **128자**. 커밋 3개(restructure 1 + merge 2).
> 리허설 클론에서는 실수 푸시를 막으려고 `git remote set-url --push origin DISABLED_NO_PUSH` 를 먼저 해 둔다. §5 에서 실제 반영할 때는
> 새로 클론하거나 `git remote set-url --push origin https://github.com/elom1213/JUN_FileManager_data.git` 로 되돌린다.

**리허설 확인 2 — 툴로 읽기**: v01.45 툴의 프로파일 하나(예: Rig_Src)를 복사해 store_dir = `_migrate/public`, data_folder = `src_rig` 로 두고 Scan →
레코드 · 썸네일이 예전과 같이 보이는지(Push 는 누르지 않는다 — 리허설 클론의 원격은 실제 원격이다).

## 5. 공개 저장소 반영 (원격 변경 — 사용자 푸시 요청이 있는 턴에만)

```bash
cd C:/Users/USER/Desktop/JP/0030_maya_python_JUN/_migrate/public
git fetch origin
for B in Dnable SA src_rig; do echo "$B new since rehearsal: $(git rev-list --count main..origin/$B)"; done   # 전부 0 이어야(아니면 §4 다시)
git remote set-url --push origin https://github.com/elom1213/JUN_FileManager_data.git
for B in master Dnable SA src_rig; do git tag archive/$B origin/$B; done
git push origin main
git push origin --tags                                    # archive/* 태그 4개
gh repo edit elom1213/JUN_FileManager_data --default-branch main
```
- **옛 브랜치(master · Dnable · SA · src_rig)는 아직 지우지 않는다.** 다른 PC · 옛 버전 툴이 계속 Push 할 수 있다 → §7 정리 단계에서.
- 반영 뒤 옛 브랜치에 새 커밋이 생기면(옛 툴이 Push) `git log archive/<B>..origin/<B>` 로 찾아 §4 (2) 처럼 그 차이만 다시 합친다
  (`git checkout <commit> -- ` 로 해당 파일을 `profiles/<B>/` 에 가져와 커밋).

## 6. 비공개 저장소 — §4 · §5 와 같은 순서

```bash
cd C:/Users/USER/Desktop/JP/0030_maya_python_JUN/_migrate
git clone --mirror https://github.com/elom1213/JUN_FileManager_data_Private.git backup_private.git
git clone https://github.com/elom1213/JUN_FileManager_data_Private.git private && cd private
git checkout -b main origin/MUE
mkdir -p profiles/MUE && git mv lineage path_structures records thumbs profiles/MUE/
git commit -m "Restructure: move MUE data into profiles/MUE"
# 확인: profiles/MUE 파일 수 == origin/MUE 파일 수(128, .gitignore 제외 차이만), blob 비교 같음
# --- 사용자 푸시 요청 턴에만 ---
for B in master private MUE; do git tag archive/$B origin/$B; done
git push origin main && git push origin --tags
gh repo edit elom1213/JUN_FileManager_data_Private --default-branch main
```

## 7. 이 PC 전환 · 정리

1. v01.45 툴 실행 → 프로파일이 자동 변환(§3-2 표) — 프로파일마다 열어 Data Folder 값 확인.
2. **클론 하나로 합친다**: `JUN_FileManager_data` 에서 툴의 `Switch to main` (또는 `git fetch && git checkout -b main --track origin/main`).
   이 클론에 이제 `profiles/Dnable · SA · src_rig` 가 다 있다.
3. 프로파일 store_dir 바꾸기: **Rig_Src · soundAliance → `JUN_FileManager_data`** (data_folder 는 각각 src_rig · SA 그대로).
   MUE 는 비공개 클론 `A0010_MEU` 에서 `Switch to main`, store_dir 그대로.
4. 각 프로파일로 Pull → Scan → 레코드 · 썸네일 · Lineage · Path Structure 가 예전과 같은지. 한 프로파일에서 메모 하나 수정 → Push → GitHub 에서
   `profiles/<folder>/records/...` 한 파일만 바뀐 커밋인지.
5. A00211 RefLineage(+ A00480 Reference > Lineage)에서 저장 · 읽기 확인.
6. 옛 클론 `JUN_FileManager_data_all/A0020_SA` · `A0030_Src_Rig` 는 **1~2주 사용해 본 뒤** 사용자 확인을 받아 지운다(그전엔 이름만 `_old_` 접두).
7. 원격 옛 브랜치 삭제(`git push origin --delete Dnable SA src_rig master` / 비공개 `MUE private master`) — **다른 PC 도 v01.45 로 바꾼 뒤, 사용자가 정할 때만.**
   태그 `archive/*` 와 `_migrate/backup_*.git` 미러는 남긴다.

## 8. 되돌리기

| 시점 | 방법 |
|------|------|
| §3 (코드만) | Maya_Python 커밋 되돌리기(revert). 데이터 무관 |
| §5 · §6 직후 | 옛 브랜치를 안 지웠으므로 옛 툴(v01.44)로 그대로 계속 쓸 수 있다. GitHub 기본 브랜치를 원래대로(`gh repo edit --default-branch master`), `main` 은 그대로 두거나 사용자 확인 뒤 삭제 |
| §7-7 이후 | `archive/<B>` 태그에서 브랜치 복구: `git push origin archive/<B>:refs/heads/<B>` (미러 백업도 있음) |

## 9. 위험 · 주의

- **다른 PC 의 옛 툴**: 옛 툴은 옛 브랜치에 Push 한다 → §5 의 "반영 뒤 옛 브랜치 새 커밋" 처리. 모든 PC 를 v01.45 로 바꾸기 전엔 옛 브랜치를 지우지 않는다.
- **배포 사용자**: 번들 기본 브랜치가 `master` → `main` 으로 바뀐다. 첫 Pull 에서 `check_branch` 가 어긋남을 알리고 `Switch to main` 을 안내 — 자동 변환이 아니라 버튼으로(미커밋 데이터 보호).
- **경로 길이**: `profiles/<folder>/` 가 붙어 경로가 약 16자 길어진다. 리허설 실측 최장 **128자** + 클론 위치(`C:/Users/USER/Desktop/JP/0030_maya_python_JUN/JUN_FileManager_data/` 69자) = 197자 < 260 — OK. 새 PC 에서 클론 위치가 깊으면 다시 확인.
- `git mv` 는 기록상 이름 변경이라 `git log --follow profiles/Dnable/records/...` 로 옛 기록을 따라갈 수 있다. SA · src_rig 는 merge 부모로 기록이 남는다(`git log archive/SA`).
- **히스토리 재작성 금지** — 이 계획은 커밋 추가 · 태그 · 기본 브랜치 변경만 한다. force push 없음.

## 10. 체크리스트 (요약)

- [ ] §3 코드 + 시험 1~7 통과, 로컬 커밋
- [ ] §4 리허설: 폴더 3개, 파일 수 · blob 일치, 기록 보존, 툴로 읽기
- [ ] (푸시 요청 턴) §5 공개 저장소 main · archive 태그 · 기본 브랜치
- [ ] §6 비공개 저장소 리허설 → (푸시 요청 턴) 반영
- [ ] §7-1 ~ 5 이 PC 전환 확인
- [ ] (나중, 사용자 결정) 옛 클론 · 옛 원격 브랜치 정리
