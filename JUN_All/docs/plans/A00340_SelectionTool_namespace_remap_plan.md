---
title: A00340_SelectionTool — 네임스페이스 교체로 다른 아바타 선택 계획서
aliases: [A00340 namespace remap, namespace map, Namespace combo]
tags: [plan, maya-python, A00340, namespace, selection]
updated: 2026-10-28
---

# A00340_SelectionTool — 네임스페이스 교체로 다른 아바타 선택 계획서

> 작성 2026-10-28 · 대상 버전 **v01.18** · 상태: **구현 중** (진행은 §10 체크리스트)
>
> **이 PC 는 작업 중에 저절로 꺼질 수 있다.** 이 문서만 보고 이어서 작업할 수 있게 썼고, 단계마다 로컬 커밋한다(제목에 `[N번호]`).
> 이어서 할 때는 §10 체크와 `git log --oneline -10` 을 먼저 본다.

---

## 0. 요약

- **요청**: `MUE_BCM` 프로파일은 `test:ZIHAN:Cage:` 컨트롤러를 고른다. 네임스페이스만 `test:IVI:Cage:` 처럼 바꾸면 다른 아바타에도 쓸 수 있다 →
  **UI 에서 쓸 네임스페이스를 골라** 선택할 때 바꿔 끼우는 기능.
- **결정 (사용자 2026-10-28 "권장안대로")**
  1. 프로파일 json 은 **그대로**. 교체는 선택할 때만 쓰는 **화면 설정**(공유 프로파일도 git 변경 없음).
  2. Buttons 탭 `Add` 줄에 **`Namespace` 콤보** — `(as saved)` + 씬에서 이 프로파일 컨트롤러가 있는 네임스페이스(찾은 수/전체, 많이 찾은 순).
  3. 프로파일이 네임스페이스를 **여럿** 쓰면 **`Map...`** 창(원래 ns 마다 대상 고르기).
  4. 고른 값은 **프로파일마다 · PC 마다 기억**(`data/active.json`). 씬에 없으면 `(as saved)` 로 되돌리고 알림.
  5. **캡처(Selection · Update · Add Objects) 는 원래 네임스페이스로 되돌려 저장**.
  6. Rules 탭 · 이름 꼴이 다른 리그(좌우 글자 대소문자 등)는 **이번 범위 밖**.

---

## 1. 현재 데이터 (2026-10-28)

| 프로파일 | scope | 오브젝트 | 네임스페이스 |
|------|------|------|------|
| `MUE_BCM` | shared | 33 | `test:ZIHAN:Cage` |
| `Vivian` | local | 232 | `Vivi:cage` 210 · `Unb:unbrella` 15 · `Unb` 7 |
| `Meflat` | local | 37 | `TBM` |
| `MUE_WU` | local | 1 | `A:ZIHAN:cage` |
| `Test` | local | 6 | 없음 |

ZIHAN 씬(`C:\JUN\JUN_MUE\00_04_02_ANI_00_PJ_010\scenes\5010_cleanup_BCM_ZIHAN\00010_cleanup_ZIHAN_00070.mb`) 의 아바타 네임스페이스:
`test:CHOEUN:cage`(소문자 c) · `test:IVI:Cage` · `test:KANA:Cage` · `test:SUA:Cage` · `test:ZIHAN:Cage`.

관련 코드 (v01.17)
- `app/ui/selection_tab.py` : `_build_buttons_pane()` 가 `Add` 줄(`self.chk_add` + stretch)을 만든다 · `_build_selection_button()` 툴팁 = objects 앞 20개 ·
  `_on_button_clicked(cat, btn)` → `maya_select.select_objects(objects, add)` · `on_create_selection()` / `_update_button_objects(cat, btn, append)` → `maya_select.capture_selection()` ·
  `_switch_profile` · `reload_profiles` · `self._scope` · `self._profile`.
- `app/core/maya_select.py` : `capture_selection()` · `select_objects(objects, add)` → (found, missing). **바꾸지 않는다.**
- `app/core/prefs.py` : `get_setting` / `set_setting`(active.json).

---

## 2. 교체 규칙 — `app/core/namespace_map.py` (신규, 순수 로직 + 씬 조회 분리)

```python
def split_ns(name)                    # 'a:b:obj' -> ('a:b', 'obj'), 'obj' -> ('', 'obj')  (마지막 ':')
def remap_name(name, mapping)          # mapping = {원래 ns: 대상 ns}. '|' 로 나눈 마디마다 split_ns 후 ns 가 mapping 에 **정확히** 있으면 교체
def remap_names(names, mapping)        # 순서 유지
def reverse_mapping(mapping)           # {대상: 원래} (대상이 겹치면 첫 것)
def profile_namespaces(data)           # 프로파일 dict -> Counter{ns: 오브젝트 수} (빈 ns 는 '' )
def profile_objects(data)              # 모든 버튼 objects (순서 · 중복 유지)

# --- 씬 조회 (maya.cmds lazy)
def scene_namespaces()                 # namespaceInfo(':', listOnlyNamespaces, recurse) - 'UI' · 'shared' 제외
def candidates(objects, source_ns)     # [(ns, found, total)] - source_ns 오브젝트들의 짧은 이름이 각 씬 ns 에 몇 개 있나.
                                       #   found > 0 인 것만, found 내림차순 → ns 이름순. source_ns 자신도 포함
```

- 교체는 **네임스페이스가 정확히 같을 때만**(부분 문자열 아님). `''`(네임스페이스 없음)도 원래 ns 로 쓸 수 있다.
- `candidates` 의 `found` = `cmds.objExists(대상ns + ':' + 짧은이름)`(대상 ns 가 '' 이면 짧은 이름) 개수. 짧은 이름은 `|` 마지막 마디.

---

## 3. UI — Buttons 탭

```
[x] Add   Namespace [ (as saved)            ▾] [Map...] [⟳]
                    [ test:IVI:Cage  (33/33)  ]
                    [ test:KANA:Cage (33/33)  ]
                    [ test:CHOEUN:cage (0/33)  ← found 0 은 목록에 안 넣는다 ]
```

- 위치: `_build_buttons_pane()` 의 `add_row` (Controls 를 접어도 보인다).
- **콤보** `cmb_ns`
  - 첫 항목 `(as saved)` (itemData `None`).
  - 프로파일이 쓰는 네임스페이스가 **하나**면: `candidates(objects, 그 ns)` 를 `ns  (found/total)` 로. itemData = 대상 ns.
    고르면 매핑 `{원래: 대상}`. 대상 = 원래 와 같으면 `(as saved)` 와 같은 뜻.
  - **여럿**이면: 콤보는 `(as saved)` / `(mapped: N)` 두 상태만 보이고 비활성 → `Map...` 로 고친다.
  - 네임스페이스를 안 쓰는 프로파일(`Test`)이면 콤보 · Map 둘 다 비활성(툴팁으로 이유).
- **`Map...`** : 작은 대화상자. 원래 ns 마다 한 줄 = `원래 ns (n objects) → [콤보: (keep) + candidates]`. OK 면 매핑 저장.
  하나짜리 프로파일에서도 열 수 있다(콤보와 같은 값).
- **`⟳`** : 후보 다시 읽기(씬이 바뀌었을 때). 프로파일 바뀔 때 · 탭 showEvent · 버튼 누를 때는 자동으로 읽지 않는다(느릴 수 있음) - 프로파일 바뀔 때만 자동.
- **켜짐 표시** : 매핑이 실제로 바꾸는 게 있으면 콤보 배경을 강조색(연한 파랑 `#cfe3ff` / 글자 진하게) + 툴팁에 매핑 전체.
- 버튼 툴팁 : 매핑이 켜져 있으면 **교체한 이름** 앞 20개 + 첫 줄에 `(namespace: 원래 -> 대상)`.

---

## 4. 동작

| 동작 | 매핑 적용 |
|------|-----------|
| 버튼 클릭(선택) | `remap_names(objects, mapping)` 를 `select_objects` 에 넘긴다. 로그 `Selected n object(s) via test:IVI:Cage` + missing |
| `Selection`(새 버튼) · `Update` · `Add Objects` | 캡처한 이름에 `remap_names(captured, reverse_mapping(mapping))` → **원래 ns 로 저장**. 되돌릴 수 없는 이름(대상 ns 밖)은 그대로 + `[WARN] n object(s) are outside the mapped namespace(s) - saved as they are` |
| 프로파일 바꿈 | 그 프로파일의 저장된 매핑 불러옴 → 후보 다시 읽기 → 저장된 대상이 후보에 없으면 그 항목 버리고 `[Info] namespace 'x' is not in this scene - using as saved` |
| 드래그 · 색 · 이름 바꾸기 | 매핑과 무관 |

---

## 5. 저장 — `data/active.json`

```json
"namespace_maps": {
  "shared:MUE_BCM": {"test:ZIHAN:Cage": "test:IVI:Cage"},
  "local:Vivian":   {"Vivi:cage": "Vivi1:cage", "Unb": "Unb1"}
}
```

- 키 = `"<scope>:<이름>"`. 값 = 바뀌는 쌍만(원래 == 대상 이면 지운다). 비면 키 삭제.
- prefs 에 헬퍼: `get_namespace_map(scope, name)` · `set_namespace_map(scope, name, mapping)`. 프로파일 이름 바꾸기 · 지우기 · Share 시 키도 따라가게(Rename/Share → 키 이동, Delete → 키 삭제).

---

## 6. 방어

| 사례 | 처리 |
|------|------|
| 대상 ns 가 씬에서 사라짐(버튼 누를 때) | 그대로 바꿔 선택 → 전부 missing 로그(없는 걸 고르지는 않는다) |
| 매핑 대상이 겹침(두 원래 ns → 같은 대상) | 허용(선택은 문제없음). 캡처 되돌리기는 첫 원래 ns 로 + `[WARN]` |
| 이름에 `|` 부분 경로 | 마디마다 교체 |
| 씬 네임스페이스 수백 개 | 후보 계산은 프로파일 오브젝트 짧은 이름 x ns. objExists 만 - 이 씬(약 30 ns x 33) 은 즉시 |

---

## 7. 검증 — `tests/test_namespace_remap.py` (mayapy 오프스크린, prefs 경로는 임시 폴더)

1. 순수 : `split_ns` · `remap_name`(정확 일치만 · 부분 문자열 안 바꿈 · `|` 경로 · 빈 ns) · `reverse_mapping` · `profile_namespaces`
2. 씬 : 같은 큐브 리그를 `A:rig` · `B:rig` · `C:other`(이름 일부만) 로 만들어 `candidates` 수 · 정렬 · found 0 제외
3. UI : 콤보 항목 · 고르면 선택이 B 로 · 로그 · 강조 · 툴팁 · 다시 열면 기억 · 씬에 없으면 (as saved) · 여러 ns 프로파일 → 콤보 비활성 + Map 대화상자로 매핑 · ns 없는 프로파일 비활성
4. 캡처 되돌리기 : 매핑 켠 채 B 선택으로 Update → 저장은 A ns, 밖의 오브젝트는 그대로 + 경고
5. 프로파일 Rename / Share / Delete 시 매핑 키 따라감
6. 회귀 : `tests/test_shared_profiles.py` 46 항목 그대로 통과
7. 실제 씬(읽기만) : ZIHAN 씬에서 `MUE_BCM` 후보 = IVI · KANA · SUA · ZIHAN 33/33, CHOEUN 은 목록에 없거나 0

---

## 8. 범위 밖 (다음에)

- Rules 탭에 같은 콤보.
- 이름 꼴이 다른 리그(예: `_L_` ↔ `_l_`) - 찾기 · 바꾸기 규칙(Studio Library mirror table 같은 것).

---

## 9. 파일

```
app/core/namespace_map.py        # 신규
app/core/prefs.py                # get/set_namespace_map + rename/share/delete 때 키 이동
app/ui/selection_tab.py          # Namespace 줄 · Map 대화상자 · 클릭 · 캡처 · 툴팁
app/config/version.py · CHANGELOG.md · docs/A00340_SelectionTool.md · docs/WORKLOG.md
tests/test_namespace_remap.py    # 신규
```

---

## 10. 진행 체크리스트 (단계마다 로컬 커밋, 제목에 `[N번호]`)

- [x] **N1** 이 계획서 커밋
- [x] **N2** `namespace_map.py` + prefs 매핑 저장 (rename/share/delete 키 이동)
- [x] **N3** Buttons 탭 Namespace 콤보 · ⟳ · 강조 · 툴팁 · 클릭 적용 · 기억
- [x] **N4** `Map...` 대화상자 (여러 ns) + 캡처 되돌리기
- [ ] **N5** 시험 `tests/test_namespace_remap.py` + 회귀 46 + 실제 씬 확인
- [ ] **N6** 버전 01.18 · CHANGELOG · 사용 안내 · WORKLOG · 이 문서 상태 = 구현 완료

커밋은 로컬만. **푸시는 사용자가 그 턴에 말할 때만.**
