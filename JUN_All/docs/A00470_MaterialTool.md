---
title: A00470_MaterialTool 사용법
aliases: [Material Tool, MaterialTool, A00470, Material Name Check]
tags: [maya-python, tool-guide, material, naming, convention, qc, json-profile]
updated: 2026-09-16
---

# A00470_MaterialTool 사용법

Maya 안에서 도는 **머티리얼 이름 진단** PySide 툴이다(arch B, in-Maya).
메시를 리스트업하면 거기 붙은 머티리얼을 모으고, 그 이름들이 **명명 규칙**을 지키는지 검사해
**어디가 틀렸는지 + 어떻게 고치면 되는지**를 로그로 낸다. **씬은 읽기만 하고 아무것도 바꾸지 않는다.**

| 상위 탭 | 내용 |
|---------|------|
| **Name Check** (v01.00) | 메시 → 머티리얼 수집 → 프로파일(JSON) 규칙으로 진단 → 리포트(클립보드 복사) |

- **버전**: `app/config/version.py` (v01.03 — 표의 칸 폭 조절 · 더블클릭 선택)
- **설치**: `__dragDrop_A00470.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **MatTool** → `tools.A00470_MaterialTool.run(True)`
- **규칙은 코드가 아니라 데이터다** — `data/profiles/*.json` 한 파일이 규칙 한 벌. 새 규칙은 툴 수정이 아니라 파일 추가다.

---

## 1. 쓰는 법

1. 씬에서 메시를 고르고 **`Select Meshes`** (또는 `Add`) 로 리스트에 담는다.
2. **`List Materials`** — 리스트의 메시에 붙은 머티리얼을 모아 표에 띄운다.
   - **더블클릭하면** 그 **머티리얼 노드**가 씬에서 선택된다. 여러 행을 골라 둔 상태면 **고른 것
     전부**가 선택된다. **한 번 클릭으로는 씬 선택이 바뀌지 않는다** — 목록을 훑어보는 동안
     선택이 딸려 바뀌지 않도록 한 것이다(v01.03 에서 바뀐 동작).
   - 칸 경계(`Material` / `Status` / `Meshes` 헤더의 세로선)를 **드래그해 폭을 조절**할 수 있고,
     목록을 다시 채워도 그 폭은 유지된다.
3. **`Profile`** 콤보에서 규칙을 고른다(기본 제공 `Set_v001`). 아래에 그 규칙의 패턴이 보인다.
4. **`Check Names`** — 진단해서 로그창에 리포트를 찍고, 기본값으로 **클립보드에 복사**한다.

> `List Materials` 를 누르지 않고 바로 `Check Names` 를 눌러도 된다 — 리스트가 비어 있으면
> 먼저 모으고 나서 검사한다(버튼을 두 번 누르게 하지 않는다).

### 옵션

| 체크박스 | 기본 | 뜻 |
|----------|------|-----|
| `Detailed report (why each token is wrong)` | 끔 | 틀린 토큰마다 **기대한 규칙 + 고칠 값**을 한 줄씩 편다 |
| `Include the names that pass` | 끔 | 통과한 이름도 리포트에 넣는다(기본은 고칠 것만) |
| `Copy the report to the clipboard` | **켬** | 리포트를 클립보드로. 남에게 그대로 건네는 글이라 기본이 켜져 있다 |

---

## 2. 리포트

### 짧은 쪽 (기본)

```
=== Material name check : profile 'Set_v001' ===
pattern : MT_MANU_CH_{character}_{set}_{part}_{extra...}
checked : 3 material(s)   ok : 1   failed : 2

MT_SYN_Sett002_Pantss
  invalid tokens : SYN, Sett002, Pantss
  missing tokens : MANU, CH
  suggested name : MT_MANU_CH_SIN_Set002_Pants
```

### 자세한 쪽 (`Detailed`)

```
MT_SYN_Sett002_Pantss
  invalid tokens : SYN, Sett002, Pantss
  [-] MANU     missing 'vendor' - expected exactly 'MANU'   (suggest : MANU)
  [-] CH       missing 'category' - expected exactly 'CH'   (suggest : CH)
  [2] SYN      invalid 'character' - expected one of : CHN, DHA, LUN, SIN, TBM   (suggest : SIN)
  [3] Sett002  invalid 'set' - expected 'Set' followed by 3 digit(s) : Set000 - Set999   (suggest : Set002)
  [4] Pantss   invalid 'part' - expected one of : Body, Hair, Top, Pants, Shoes, Accessory   (suggest : Pants)
  missing tokens : MANU, CH
  suggested name : MT_MANU_CH_SIN_Set002_Pants
```

- `[n]` 은 **이름 안에서 몇 번째 토큰**인지다. `[-]` 는 아예 없는(생략된) 토큰.
- **`suggested name` 이 이 리포트의 핵심이다.** "틀렸다" 로 끝나면 받은 사람이 다시 물어야 한다.
- 생략된 토큰은 고정값이면 그 값(`MANU`), 아니면 자리표시(`{character}`)로 적힌다 —
  "`MANU` 라는 단어가 빠졌다" 와 "캐릭터 토큰이 빠졌다" 는 다른 말이기 때문이다.
- 고칠 값을 알 수 없으면 제안에 `{character}` 가 그대로 남는다(억지로 고르지 않는다).

### 로그창 (v01.02)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 (`Check Names` 의 리포트 복사와는 별개로, 로그에 쌓인 것 전부) |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).

---

## 3. 기본 프로파일 `Set_v001`

```
MT_MANU_CH_{character}_{set}_{part}_{extra...}
```

| 자리 | 규칙 | 예 |
|------|------|-----|
| 1 `prefix` | 고정 `MT` (대소문자까지 동일) | `MT` |
| 2 `vendor` | 고정 `MANU` | `MANU` |
| 3 `category` | 고정 `CH` (`MT` 와 마찬가지로 한 글자도 달라선 안 된다) | `CH` |
| 4 `character` | `CHN` `DHA` `LUN` `SIN` `TBM` 중 하나 | `CHN` |
| 5 `set` | `Set` + **숫자 3자리** | `Set002` |
| 6 `part` | `Body` `Hair` `Top` `Pants` `Shoes` `Accessory` 중 하나 | `Top` |
| 7~ `extra` | 아무 글자나, **몇 개든**(없어도 된다) | `lace_trim` |

> **`CH` 와 `CHN` 은 한 글자 차이다.** 그래서 `MT_MANU_CHN_Set002_Top`(= `CH` 를 빼먹은 이름)은
> 자칫 "`CHN` 이 `CH` 의 오타" 로 읽힐 수 있는데, 정렬(§6.1)이 **`CH` 생략 + `CHN` 은 캐릭터**
> 쪽을 더 높은 점수로 고른다. 반대로 `MT_MANU_CH_Set002_Top` 은 **`CH` 는 제자리, 캐릭터가 생략**
> 으로 읽힌다. 두 경우 모두 테스트로 못 박아 두었다.

### 꼬리 숫자 규칙

이름 **맨 끝의 숫자**가 마지막 토큰에 **붙어** 있으면 경고한다.

| 이름 | 판정 |
|------|------|
| `MT_MANU_CH_CHN_Set002_Top_extra_002` | OK — `_` 로 갈라진 숫자 토큰 |
| `MT_MANU_CH_CHN_Set002_Top_extra3` | **경고** — 마지막 토큰에 붙었다 → `extra_3` 제안 |
| `MT_MANU_CH_CHN_Set002` | OK — `Set002` 의 숫자는 규칙이 요구한 것이다 |

> `Set` 뒤 자릿수는 요청의 `SetXXX` 를 **3자리**로 읽은 것이다. 자릿수를 바꾸려면 JSON 의
> `"digits": 3` 한 줄만 고치면 된다.

---

## 4. 프로파일 JSON

`tools/A00470_MaterialTool/data/profiles/<이름>.json` 한 파일 = 규칙 한 벌.
파일 이름이 곧 콤보에 뜨는 이름이다. 고친 뒤 **`Reload`** 를 누르면 다시 읽는다.

```json
{
  "name": "Set_v001",
  "separator": "_",
  "pattern": "MT_MANU_CH_{character}_{set}_{part}_{extra...}",
  "tokens": [
    {"role": "prefix",    "type": "literal", "value": "MT"},
    {"role": "category",  "type": "literal", "value": "CH"},
    {"role": "character", "type": "enum",    "values": ["CHN", "DHA", "LUN", "SIN", "TBM"]},
    {"role": "set",       "type": "pattern", "prefix": "Set", "digits": 3},
    {"role": "extra",     "type": "any",     "repeat": true, "optional": true}
  ],
  "checks": {"trailing_digit": true}
}
```

| `type` | 뜻 | 필드 | 고칠 값 제안 |
|--------|-----|------|--------------|
| `literal` | 한 글자도 다르면 안 된다 | `value` | 오타면 그 값으로 |
| `enum` | 목록 중 하나 | `values` | 편집 거리로 가장 가까운 값 |
| `pattern` | 접두사 + 고정 자릿수 숫자 | `prefix`, `digits` | 알파벳/숫자를 갈라 다시 조립 |
| `regex` | 직접 쓴 정규식 | `regex` | (없음 — 무엇이 맞는지 알 수 없다) |
| `any` | 아무 글자나 | — | (없음) |

공통 필드 — `optional`(없어도 됨) · `repeat`(개수 제한 없이, 남은 토큰을 받는 **꼬리 슬롯**) ·
`case_sensitive`(기본 `true`) · `hint`(리포트에 찍히는 기대값 설명을 직접 쓴다).
모르는 `type` 은 `any` 로 떨어진다 — 오래된 프로파일이 툴을 깨뜨리지 않게.

---

## 5. 구조

```
A00470_MaterialTool/
├─ launch.py                 # run() — 창 재생성 방지 + 테마(teal_dark)
├─ __dragDrop_A00470.py
├─ icon/A00470_MaterialTool.svg (+ .png)   # 셸프 아이콘(머티리얼 볼 + 네임 태그)
├─ data/profiles/Set_v001.json             # 규칙 = 데이터
└─ app/
   ├─ config/version.py
   ├─ core/
   │  ├─ profiles.py        # 프로파일 JSON 입출력          (Maya 무의존)
   │  ├─ name_rules.py      # 규칙 · 정렬 · 진단 · 제안      (Maya 무의존)
   │  ├─ reporter.py        # 진단 결과 -> 사람이 읽는 글    (Maya 무의존)
   │  └─ maya_materials.py  # 메시 -> 셰이딩 엔진 -> 머티리얼 (씬 읽기 전용)
   └─ ui/
      ├─ main_window.py     # 창 · 탭 · 메뉴(Help > Profile Format) · Pin
      │                     #  + 공용 로그 위젯 JUN_mod_log_qt_v01 (Expand/Clear/Copy)
      └─ name_check_tab.py  # Name Check 탭 본문
```

코어 3개가 `maya.cmds` 를 쓰지 않으므로 **규칙 엔진은 마야 없이 그대로 테스트된다**(§7).

---

## 6. 구현에서 중요한 것

### 6.1 ★ 토큰을 슬롯에 "앞에서부터" 붙이면 안 된다

이 툴에서 유일하게 어려운 지점이다. 토큰 1 = 슬롯 1 로 붙이면 **토큰 하나가 생략된 순간
그 뒤가 전부 밀린다.**

```
MT_SYN_Sett002_Pantss        <- MANU 와 CH 가 빠진 이름

순서대로 붙이면              정렬로 풀면
  MT      = MT       OK        MT      = MT        OK
  SYN     = MANU     X         (없음)  = MANU      생략
  Sett002 = CH       X         (없음)  = CH        생략
  Pantss  = character X        SYN     = character X
  (없음)  = set      X         Sett002 = set       X
  (없음)  = part     X         Pantss  = part      X
```

왼쪽은 "전부 틀림" 이라 **사람에게 쓸모가 없다.** 그래서 **정렬(alignment)** 로 푼다 —
`match` / `슬롯 비우기(생략)` / `토큰 버리기(잉여)` 세 가지 수를 두는 DP
(Needleman–Wunsch 와 같은 꼴, `name_rules.NameProfile._align`).

점수는 이렇게 둔다. **고칠 수 있는 오타는 "그 자리에 오려던 토큰"** 이라는 뜻이므로 가산점을 준다.

| 수 | 점수 |
|----|------|
| 규칙을 만족하는 토큰 | **+4** |
| 오타지만 고칠 수 있는 토큰 | **+2** |
| 그 자리에 왔지만 전혀 아닌 토큰 | −1 |
| 슬롯을 비운다(생략된 토큰) | −2 |
| 토큰을 버린다(규칙에 없는 자리) | −3 |

`extra` 같은 **반복 슬롯은 정렬에서 빼고 꼬리로 받는다**(개수가 정해지지 않으므로).
남은 토큰은 꼬리 슬롯이 공짜로 받고, 꼬리 슬롯이 없는 프로파일이면 전부 "잉여" 로 보고된다.

### 6.2 고칠 값은 규칙이 스스로 안다

규칙 타입마다 `repair()` 가 있고, **돌려주기 전에 자기 `is_valid()` 로 다시 검사한다** —
통과하지 못하는 수정 제안은 없느니만 못하다. (§7 에서 이 성질을 테스트로 못 박았다)

- `enum` : 대소문자만 다르면 그 값, 아니면 **편집 거리**로 가장 가까운 값 (`SYN`→`SIN`, `Pantss`→`Pants`)
- `pattern` : 앞 글자와 뒤 숫자를 갈라 다시 조립 (`Sett002`→`Set002`, `Set2`→`Set002`, `Set0002`→`Set002`)
- 거리 한계는 단어 길이에 따른다 — 4글자 이하는 1, 그 위는 2.
  **짧은 단어는 한 글자만 달라도 다른 단어다**(`CHN` 과 `SIN` 은 서로 고쳐 주지 않는다).

### 6.3 ★ 한 트랜스폼 아래 셰이프가 여럿일 수 있다

`maya_materials.geometry_shapes()` 는 **non-intermediate 셰이프를 전부** 본다.
"첫 셰이프" 만 고르면(익숙한 `extendToShape` 류의 함정) blendShape 타겟 셰이프를 같은
트랜스폼에 정리해 둔 리그나 임포트 잔재에서 **머티리얼을 통째로 놓친다.**
페이스별 할당도 셰이딩 엔진이 결국 셰이프에 연결되므로 같은 경로로 잡힌다(둘 다 실측).

### 6.4 그 밖에

- 이름 검사 전에 **경로와 네임스페이스를 뗀다** — `|grp|rig:MT_...` 는 `MT_...` 로 본다.
- 메시 리스트는 공용 TSL 이 **UUID 로 보관**하므로 담아 둔 뒤 리네임돼도 올바른 노드를 잡는다.
- 표에서 행을 **더블클릭**하면 `noExpand` 로 **머티리얼 노드 자체**를 선택한다.
- ★ 칸을 드래그해 넓힐 수 있게 하려면 헤더가 `Interactive` 여야 한다. `Stretch` 나
  `ResizeToContents` 는 스타일이 폭을 계산해 버려서 **드래그 자체가 막힌다.** 마지막 칸은
  `setStretchLastSection(False)` 로 풀어 줘야 사용자가 정한 폭을 지킨다.
- 같은 머티리얼을 여러 메시가 쓰면 **한 번만** 나열하고, `Meshes` 열에 쓰는 메시 수를 적는다.

---

## 7. 검증

`mayapy` (Maya 2024) 헤드리스 — **규칙 엔진 102항목 + 마야 통합 27항목 통과**.

**규칙 엔진(마야 없이, 102항목)** — 프로파일 로딩 · 통과해야 하는 이름 6종 ·
요청의 예시 `MT_SYN_Sett002_Pantss` 가 **정확히 `SYN, Sett002, Pantss` + 생략 `MANU, CH`** 로 나오는지 ·
짧은/자세한 리포트 문구 · **`CH` 슬롯 10종**(틀린 값 · 소문자 · 긴 단어 · **`CH`/`CHN` 이 서로 빨려들지
않는지** 양방향) · **생략된 토큰이 뒤를 밀지 않는지(정렬) 6종** · 꼬리 숫자 5종 ·
토큰 교정 7종 · **모든 제안이 그 자신 규칙을 통과하는지 13종** · 네임스페이스/경로/빈 이름/
`lambert1` 같은 가장자리 · 배치 리포트(개수 · 통과 이름 숨김 · 클립보드에 들어가는 문자열) ·
**다른 모양의 프로파일**(구분자 `-`, `regex` 규칙, 꼬리 슬롯 없음, 모르는 타입 폴백).

**마야 통합(27항목)** — 메시→머티리얼 수집 · 여러 메시가 공유하는 머티리얼을 한 번만 ·
**페이스별 할당** · **한 트랜스폼에 셰이프 2개일 때 둘 다** · 빈 리스트/그룹/없는 노드 가드 ·
셰이프와 컴포넌트를 직접 넘긴 경우 · **머티리얼 선택이 다른 것으로 펼쳐지지 않는지** ·
씬에서 모은 이름을 그대로 진단하는 끝-끝 흐름.

**로그 위젯(오프스크린 Qt, 56 + 55항목)** — 공용 위젯 `JUN_mod_log_qt_v01` 의 버튼 3개(8개 테마에서
글자가 들어갈 여백이 있는지 포함) · 드롭인 호환 ·
Expand 의 이동/복귀/미아 방지, 그리고 **이 툴이 실제로 그 위젯을 쓰는지**(탭의 `log()` 경로 ·
진단 리포트 · Expand 동작). 자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).

**머티리얼 표(오프스크린 Qt + 씬, 21항목)** — 세 칸이 모두 `Interactive` 인지 · 마지막 칸이
자동으로 늘어나지 않는지 · 초기 폭 · **드래그한 폭이 남고 목록을 다시 채워도 유지되는지** ·
**한 번 클릭은 씬 선택을 건드리지 않는지** · 더블클릭이 머티리얼 노드를(멤버로 펼치지 않고)
선택하는지 · 여러 행을 골라 두고 더블클릭하면 전부 선택되는지 · 지워진 머티리얼을 더블클릭하면
죽지 않고 이유를 로그에 적는지.

> 실제 Maya GUI 에서의 사용 확인은 아직이다(헤드리스 검증만 마쳤다).
