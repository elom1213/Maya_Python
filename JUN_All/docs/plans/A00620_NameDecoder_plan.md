---
title: A00620_NameDecoder 계획서
tags: [maya-python, plan, fbx, fbxasc, unicode, blendshape, naming]
updated: 2026-11-09
---

# A00620_NameDecoder 계획서

마야 FBX 임포터가 `FBXASC227FBXASC129FBXASC130` 처럼 바꿔 놓은 이름(일본어 · 중국어 · 띄어쓰기 · 맨 앞 숫자 등)을
**원래 글자로 풀어서 보여 주는** in-Maya PySide 툴(arch B).
1차 목표는 **"읽을 수 있게"** 이고, 씬의 이름을 바꾸는 기능은 끄고 시작하는 옵션으로만 둔다(이유는 §2-3).

## 1. 요구 (2026-11-09 사용자)

| # | 요구 | 결정 |
|---|------|------|
| 1 | 마야가 표현 못 하는 글자(일본어 · 중국어 · 띄어쓰기)가 `FBXASC###` 로 바뀐 이름을 원래 글자로 읽고 싶다 | 디코드해서 표로 보여 준다(§3) |
| 2 | 대상 = 임의 노드 이름 + 블렌드셰이프 타겟 이름 | 노드 이름(DAG · DG 전부) + **블렌드셰이프 웨이트 alias** 를 함께 다룬다 |
| 3 | 새 툴 / 기존 툴 이식 판단 | **새 툴 A00620 + 디코더는 Framework 공용**(§4) |

## 2. 실측 (mayapy 2024, 2026-11-09, 예시 `0010_Miyabi_base_02.mb`)

### 2-1. 인코딩 규칙

- `FBXASC` + **UTF-8 바이트 하나의 10진수 3자리**. `[A-Za-z0-9_]` 밖의 바이트가 전부 이렇게 바뀐다.
  - `あ` = UTF-8 `E3 81 82` → `FBXASC227FBXASC129FBXASC130`
  - 띄어쓰기 `0x20` → `FBXASC032` (`Left ankle` 등 28개)
  - **맨 앞 숫자** `1` → `FBXASC049` (마야 이름은 숫자로 시작할 수 없어서. `FBXASC049_001` … 45개 조인트)
- 이미 인코더가 있다: `Framework/core/fbx_binary.maya_node_name()` (A00480 fbx_exact 가 쓰는 중).
  **디코더는 이것의 정확한 역함수**로 같은 모듈 옆에 둔다(§5-1).

### 2-2. 예시 씬 결과

| 대상 | 개수 | 예 (원래 → 디코드) |
|------|------|------|
| joint | 45 | `ArmFBXASC233FBXASC165FBXASC176` → `Arm饰`, `FBXASC049_003` → `1_003` |
| transform (메시) | 52 | `FBXASC229FBXASC143FBXASC163FBXASC229FBXASC183FBXASC166` → `口左` |
| mesh 셰이프 | 52 | `…Shape` → `口左Shape` (접미사는 ASCII 그대로) |
| blendShape 타겟 alias | **52 / 52** (`Miyabi_ncl1_3`) | `まばたき` · `キリッ` · `怒り目` · `あ` · `い２` … |
| 사용자 어트리뷰트 | 0 | — |

- 디코드 실패(깨진 UTF-8) 0개, 디코드 후 이름 중복 0개, 레퍼런스 노드 0개.
- 이 씬은 MMD(PMX) 계열 원본으로 보인다 — 모프 이름이 `あいうえお` · `まばたき` 라 **페이셜 작업에서 타겟을 못 읽는 것**이 실제 고통점.

### 2-3. 마야가 할 수 있는 것 / 없는 것

| 시도 | 결과 |
|------|------|
| `cmds.rename(node, "まばたき")` | **실패** `New name has invalid characters` |
| `cmds.aliasAttr("あ_test", bs.w[0])` | **실패** |
| 블렌드셰이프 웨이트에 nice name | **불가** — `weight` 는 동적 어트리뷰트가 아니다 |
| 문자열 어트리뷰트에 `まばたき` 저장 · 읽기 | **성공** (왕복 동일) |
| **FBX 내보내기** (`FBXASC…` 이름 노드 + alias) | **원래 글자로 복원돼 나간다** — `Model::あ`, BS 채널 `い` |
| 그 FBX 를 다시 임포트 | 다시 `FBXASC…` 로 들어온다 |

결론:
- **마야 안에서 원래 글자로 "이름을 바꾸는" 방법은 없다.** 아웃라이너 · 채널 박스 · Shape Editor 의 글자도 바꿀 수 없다
  → **툴 창(Qt)에서 풀어 보여 주는 것**이 유일한 해법. Qt 위젯은 유니코드를 그대로 그린다.
- **`FBXASC` 이름은 손실 없는 왕복 형식이다.** 그대로 두면 FBX → UE 로 원래 일본어 이름이 살아서 나간다.
  ASCII 로 이름을 바꾸면(예: `まばたき` → `blink`) **원래 이름이 영영 사라진다** → 이름 바꾸기는 기본 기능이 아니라
  경고와 함께 쓰는 선택 기능(§3-3, 2 단계).

## 3. 기능

### 3-1. Scan (1 단계 · 핵심)

- 범위: `Scene` / `Selected` / `Selected + Hierarchy` (콤보).
- 찾는 것:
  1. 노드 이름에 `FBXASC` 가 들어간 모든 노드(DAG + DG) — 짧은 이름 기준, 네임스페이스는 떼서 디코드하고 붙여 보여 준다.
  2. **blendShape 웨이트 alias** (`aliasAttr -q`) — 타겟 인덱스와 함께.
  3. (옵션 체크) 사용자 어트리뷰트 이름 · enum 필드 문자열.
- 표(QTreeWidget, 공용 `JUN_mod_treeExpand_qt_v01` · `JUN_mod_viewZoom_qt_v01`):

  | Type | Decoded | Raw | Owner |
  |------|---------|-----|-------|
  | joint | `Arm饰` | `ArmFBXASC233…` | — |
  | blendShape target [6] | `あ` | `FBXASC227FBXASC129FBXASC130` | `Miyabi_ncl1_3` |

  - 블렌드셰이프는 노드 아래 타겟을 자식 행으로(트리), 타입별로 묶기 / 펼친 목록 토글.
  - `Show encoded only` 체크(기본 ON) — 끄면 범위 안 모든 이름을 보여 주고 바뀐 것만 색으로.
- 위에 공용 필터 위젯(`JUN_mod_filter_qt_v01`) — **디코드된 글자로 검색**(`まば` 를 쳐서 `まばたき` 찾기). Raw 로도 맞으면 함께.

### 3-2. 읽기 동작 (1 단계)

- 행 클릭 = 마야에서 그 노드 선택(블렌드셰이프 타겟 행은 블렌드셰이프 노드 선택).
- `Sync with Selection` 체크 — 마야 선택이 바뀌면 그 노드 행을 표에서 강조(selectionChanged scriptJob, 창 닫힐 때 해제).
- 우클릭 메뉴: `Copy Decoded` / `Copy Raw` / `Copy Both (tab)` — 여러 행 복사 가능.
- `Export List...` — `Raw<TAB>Decoded<TAB>Type<TAB>Owner` 를 UTF-8 csv / json 으로(번역표를 만들 때 출발점).

### 3-3. 블렌드셰이프 타겟 패널 (2 단계)

Shape Editor 가 `FBXASC…` 로만 보여 주는 문제를 직접 해결한다.

- 블렌드셰이프 노드를 고르면 타겟마다 **디코드된 이름 + 웨이트 슬라이더(0~1) + 숫자 칸**. 슬라이더는 `setAttr` 직결(키는 안 찍음).
- `Reset All` (전부 0).
- 웨이트에 연결이 들어와 있으면 슬라이더 잠금 + 툴팁에 연결 소스.

### 3-4. Rename to ASCII (2 단계 · 선택 기능, 기본 숨김)

정말 ASCII 이름이 필요할 때만(예: 사내 이름 규칙에 맞춰야 할 때).

- 입력 = **번역표 json** (`{"まばたき": "blink", "あ": "A", ...}`) — 툴이 자동 번역하지 않는다(네트워크 없음, 추측 금지).
  `Export List` 로 뽑은 파일을 채워서 쓰는 흐름.
- 미리보기 표(Raw → Decoded → New) 에서 확인 후 `Apply`. 노드는 `cmds.rename`, 타겟은 `aliasAttr`.
- **실행 전 경고 대화상자**: "FBX 로 내보낼 때 원래 이름이 사라진다". undo 청크 하나.
- 바꾼 노드에 원래 이름을 문자열 어트리뷰트 `fbxOriginalName`(실측: 유니코드 저장 OK)로 남겨 **`Restore Original Names`** 가능.
- 레퍼런스 · 잠긴 노드는 Skipped.
- 번역표에 없는 이름은 그대로 둔다(Skipped 로 표시).

### 3-5. 이번에 하지 않는 것

- 아웃라이너 · 채널 박스 · Shape Editor 의 글자를 직접 바꾸기 — 마야 UI 라 불가(§2-3).
- 자동 번역 · 로마자 변환 — 추측으로 이름을 만들지 않는다. 필요하면 나중에 번역표 생성 보조로만.
- 마야 밖 파일 일괄 스캔(mayapy 워커) — 필요해지면 A00210 쪽 작업.

## 4. 새 툴 vs 기존 툴 — 판단

| 후보 | 맞는 점 | 안 맞는 점 |
|------|---------|-----------|
| **A00330 NamingTool** | 이름 다루는 툴 | 목적이 *이름 바꾸기*. 이 요구의 핵심은 *읽기* 이고, 바꾸면 오히려 FBX 원래 이름이 망가진다(§2-3). 배포판은 `Rename > Token` 만 보이는 Release view 라 새 탭을 넣으면 배포 규칙도 같이 손대야 한다. 탭이 이미 많다(Rename · Copy Name · Quick Rename + 하위 탭) |
| **A00290 BSTool_V02** | 고통점의 52/52 가 블렌드셰이프 타겟 | 조인트 45 · 메시 104 개 이름은 범위 밖. 노드 이름 읽기를 BS 툴에 넣으면 도메인이 섞인다 |
| A00480 FileTool | FBX 임포트를 다룬다 | 파일 입출력 툴. 임포트가 끝난 씬을 읽는 일과 다르다 |
| A00310 SearchTool | 검색 | 규칙 기반 타입/토큰 검색. 디코드 표 · BS 슬라이더와 결이 다르다 |

**결정: 새 툴 `A00620_NameDecoder` + 디코더는 `Framework` 공용.**

- 일이 **노드 타입을 가로지르는 "읽기 전용 뷰어"** 라서 어느 기존 툴 도메인에도 온전히 속하지 않는다.
- 작은 툴이라 애니메이터 · 모델러에게 그대로 배포하기 쉽다(A00330 의 Release view 규칙과 엮이지 않는다).
- 디코더를 `Framework/core/fbx_name.py` 로 두면 **기존 툴은 한 줄로 디코드 표시를 얻을 수 있다** — 3 단계 후보:
  - A00290 V02 타겟 목록에 `Decoded` 표시
  - A00330 Token 미리보기의 Current 열에 디코드 툴팁
  - (기존 툴 수정이라 각각 따로 요청 시)

## 5. 구조

```
Framework/core/fbx_name.py              # 공용 - DCC 비의존(순수 파이썬)
    encode(text) -> str                 # = fbx_binary.maya_node_name 로직을 옮김, fbx_binary 는 이걸 호출(재노출)
    decode(name) -> str                 # 역함수
    decode_parts(name) -> [(raw, text, is_encoded)]   # 하이라이트용 조각
    is_encoded(name) -> bool

Framework/core/maya_fbx_names.py        # 공용 - maya.cmds
    scan(scope, include_attrs=False) -> [NameEntry]   # node / bs_target / attr
    select_entry(entry)

tools/A00620_NameDecoder/
├─ __init__.py · launch.py · __dragDrop_A00620.py · icon/A00620_NameDecoder.svg(+png)
├─ app/config/version.py
├─ app/core/name_table.py      # NameEntry 묶기 · 필터 · export(csv/json)
├─ app/core/ascii_rename.py    # 2 단계: 번역표 → 미리보기 → apply / restore
├─ app/ui/main_window.py       # Scan 탭 (+ 2 단계 BlendShape · Rename 탭)
└─ tests/test_name_decoder.py
```

### 5-1. 디코더 규칙 (정확성)

- `FBXASC(\d{3})` 연속 구간을 **바이트로 모아 한 번에** UTF-8 디코드(글자 하나가 2~4 바이트에 걸친다).
- `FBXASC` 뒤가 3 자리 숫자가 아니거나 값 > 255 → 글자 그대로 둔다.
- 모은 바이트가 깨진 UTF-8 → 그 구간은 **Raw 그대로 두고 행을 노랑**(추측 디코드 금지, `errors="replace"` 로 `�` 를 만들지 않는다).
- 마야가 붙인 접미사(`_001`, `Shape`, `SG`, `Orig`)는 ASCII 라 그대로 남는다.
- 네임스페이스 `ns:` · DAG 경로 `|` 는 조각마다 따로 디코드.
- **`decode(encode(s)) == s`** 를 모든 시험 문자열에 대해 보장(왕복 시험).

## 6. 시험

- `test_name_decoder.py` (순수 파이썬, 마야 불필요)
  - 예시 씬에서 뽑은 실제 이름 표(`まばたき` · `い２` · `Arm饰` · `Left ankle` · `1_003` · `口横狭め左Shape`) 디코드 일치
  - 왕복: 한·중·일 · 이모지(4 바이트) · 띄어쓰기 · `-` `.` · 맨 앞 숫자
  - 깨진 바이트 · `FBXASC12` · `FBXASC999` 는 그대로
  - `fbx_binary.maya_node_name` 이 그대로 같은 결과(A00480 `test_fbx_core.py` 도 다시 돌린다)
- mayapy 헤드리스
  - `FBXASC` 큐브 + 블렌드셰이프 alias 씬 → `scan` 이 노드 · 타겟을 다 찾음 · 범위(Selected) 동작
  - **예시 `0010_Miyabi_base_02.mb`** → 노드 149 · BS 타겟 52 (원본 파일은 열기만, 저장 안 함)
  - 2 단계 Rename: 번역표 적용 → undo 한 번 원상 → Restore 로 원상 · FBX 내보내기 시 원래 이름 사라짐 경고 조건
- UI(오프스크린) — 표 행 수 · 디코드 글자 필터 · Copy Decoded 클립보드 내용.
- **GUI 확인(실기)**: 일본어 글꼴이 마야 Qt 창에서 □ 로 깨지지 않는지 (Windows 기본 글꼴 폴백 확인 — 깨지면 `Yu Gothic` / `Microsoft YaHei` 폴백 지정).

## 7. 단계

| 단계 | 내용 |
|------|------|
| 1 | `Framework/core/fbx_name.py` + `maya_fbx_names.py` + A00620 Scan 탭(표 · 검색 · 선택 · Sync · Copy · Export) |
| 2 | BlendShape 타겟 패널(디코드 이름 + 슬라이더) · Rename to ASCII / Restore |
| 3 | 기존 툴에 디코드 표시 한 줄씩(A00290 V02 · A00330) — 따로 요청 시 |

## 8. 문서 · 기록

- `docs/A00620_NameDecoder.md` 사용 안내(인코딩 규칙 · 마야 한계 · **FBX 왕복은 FBXASC 그대로가 안전** · 번역표 형식)
- `docs/WORKLOG.md`, 메모리 `wip-a00610-namedecoder.md`, 아이콘 32x32 svg + png, A00370 런처 버튼
