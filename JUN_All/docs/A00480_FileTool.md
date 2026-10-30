---
title: A00480_FileTool 사용법
aliases: [File Tool, FileTool, A00480]
tags: [maya-python, tool-guide, file, fbx, export, import, path, reference, mocap, pyside]
updated: 2026-10-30
---

# A00480_FileTool 사용법

Maya 안에서 도는 **파일 입출력 · 경로** PySide 툴이다(arch B, in-Maya).
흩어져 있던 두 툴의 기능을 한 창의 탭으로 모았다.

| 탭 | 내용 | 출처 |
|----|------|------|
| **Export** | objectSet 마다 FBX 한 파일로 일괄 익스포트 (Export Path · Set Up · Naming · Type Filter · Joints only) | [`A00040_file_exporter_V02`](A00040_file_exporter_V02.md) 화면 전체 |
| **Import > CSV** (v01.10) | ARKit 페이셜 CSV(Live Link Face) → 노드 키프레임 + 오디오. **블렌드셰이프뿐 아니라 ARKit 어트리뷰트를 가진 아무 노드** | `A00200_CSV_tool` (ARKit Facial Import) 이식, 원본 보존 |
| **Import > FBX** | `Import FBX normal` — FBX 임포트가 파일의 노멀을 그대로 쓰게 · **`Mocap FBX Import (Exact Rotation)`**(v01.13) — 마야 임포터가 뒤집는 회전 키를 FBX 원본 키로 다시 써서 모캡을 정확하게 | [`A00030_quickTool_V02`](A00030_quickTool_V02.md) `Import option` · 신규 (§3-2) |
| **Path** | `Copy Scene Folder` · `Open Scene Folder` | [`A00030_quickTool_V02`](A00030_quickTool_V02.md) `File` |
| **Reference > Default** (v01.12) | 현재 씬의 레퍼런스를 **중첩(이중 · 삼중)까지 트리**로 → 고른 파일을 탐색기에서 열기 · 경로 복사 | 신규 (§5) |

- **버전**: `app/config/version.py` (v01.13 — Import > FBX 에 **`Mocap FBX Import (Exact Rotation)`**: 마야 FBX 임포터가 비 XYZ 회전 순서 조인트의 회전 키를 뒤집는 문제를 FBX 원본 키로 고침 · `Fix Scene From FBX`(§3-2) · v01.12 — **`Reference` 탭**(하위 탭 `Default`): 씬 레퍼런스를 중첩까지 트리로, `Open in Explorer` · `Copy Path`(§5) · v01.11 — Import > CSV 에 **`Value Scale`**: CSV 값 x 배율로 키(AdvancedSkeleton 페이셜 컨트롤 = `x10`, §3-1) · v01.10 — Import 탭이 하위 탭 **CSV / FBX**, CSV = `A00200_CSV_tool` 이식(영어 UI, 아무 노드에 키, §3-1) · v01.09 — Naming 토큰 규칙에 **`Enum`**(정해진 값 중 고르기, A00330 과 같은 공용 규칙, §2-4) · v01.08 — Naming 칸을 고쳐도 저장 안 함, **`Save` 버튼**으로만 프로파일 기본이 된다(§2-4) · v01.07 — 창이 화면보다 커서 **로그창이 두 개처럼** 보이던 문제 수정(탭 스크롤 + 화면 높이에 맞춤) · v01.06 — **Naming 을 A00330 Token 과 같은 토큰 칸 + Profile** 로(§2-4) · v01.05 — 걸린 메시를 **마야에서 선택** · v01.04 — `Check Hide Mesh` 는 **메시 자신만** 본다 · v01.03 — Export **규칙**: 내보내기 전 검사, 첫 규칙 `Check Hide Mesh` · v01.02 — Pin 글자 잘림 수정)
- **설치**: `__dragDrop_A00480.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **FileTool** → `tools.A00480_FileTool.run(True)`
- **테마**: `slate_dark`
- **원본 두 툴은 그대로 남아 있다.** quickTool 의 File · Import option 버튼도 지워지지 않았다.
  창 이름(objectName)이 달라 **셋을 동시에 띄워도 서로 닫지 않는다.**

> 이름이 비슷한 [`A00210_FileManager`](A00210_FileManager.md) 는 **마야 밖**에서 도는 씬 파일 버전·작업 기록 추적 앱이고,
> [`A00240_PathTool`](A00240_PathTool.md) 은 자주 쓰는 폴더를 버튼으로 여는 standalone 런처다. 이 툴은 **마야 안의 입출력**이다.

---

## 1. 화면

```
┌ File Tool v01.02 ───────────────────────────── [ Pin ] ┐
│ Help                                                    │
│ ┌ Export ┬ Import ┬ Path ┬ Reference ┐                  │
│ │ Export Path [.................] [Browse][Paste][Scene]│
│ │ Set Up      [Set's Name]   [File name]                │
│ │ Naming      Profile [Default▾][Save][New][Rename][Delete] [Add Token][Delete Token]
│ │             [Token 1][Token 2]...  (칸마다 규칙 콤보)  │
│ │             Preview : SK_MANU_CH_Name_Basic_Version [Set Name]
│ │ Export      □ Move to scene root □ Joints only ...    │
│ │             Type Filter : [Include Types ▾] [Export]  │
│ └───────────────────────────────────────────────────────┘
│ Log ─────────────────────────────── [Expand][Clear][Copy]
│   Copyright (c) Park Ji Hun. All rights reserved.        │
└──────────────────────────────────────────────────────────┘
```

- **로그창은 네 탭이 함께 쓴다.** 어느 탭에서 누른 결과든 같은 곳에 쌓인다.
- **표식은 색으로 보인다** (2026-09-22~) — `[WARN]` 노랑 · `[OK]` 초록 · `[FAIL]` 빨강 · `[SKIP]` 회색 · `[Info]` 파랑. 이 툴만의 장식이 아니라 **저장소 공용 규칙**이다 — [Framework_log_levels](Framework_log_levels.md).
- **창 크기** — v01.01~01.05 는 원본 `A00040_file_exporter_V02` 와 같았다(slate_dark 기준 960 x 853, 폭은 Naming 6칸 줄이 정했다).
  **v01.06 부터 868 x 970**(오프스크린 측정) — Naming 이 토큰 칸이 되면서 Numbering 칸(4줄)만큼 높아지고, 고정 6칸이 없어져 좁아졌다.
  Profile 과 Add/Delete Token 을 한 줄에, Set Name 을 미리보기 줄 오른쪽에 둬서 높이를 줄였다(988 → 970).
  - 테마 qss 는 `show()` 뒤에야 자식 위젯에 입혀지므로, 그 전에 재면 글자가 큰 상태의 최소 크기(약 1290 폭)로 창이 커진다.
    `launch.py` 가 show 다음 이벤트 루프에서 `fit_to_content()` 로 레이아웃 최소 크기에 맞춘다.
  - **v01.07 — 화면보다 크면 화면에 맞춘다.** 내용 높이가 약 1070px(+ 타이틀 바)이라 1080 모니터나 배율 125/150% 에서는
    창이 작업 영역을 넘었다. 윈도우가 잘라낸 아래쪽을 Qt 가 그리지 못해 **로그창 잔상(Win10 · Maya 2023) / 흰 영역(Win11 · Maya 2024)**
    이 남아 로그창이 두 개처럼 보였다. 이제 탭은 `QScrollArea` 안에 있고, 창 높이는 `min(내용 높이, 모니터 작업 영역)` 이다.
    - 탭 높이는 `sizeHint` 로 잰다 — 스크롤 칸이 없던 때 레이아웃이 탭에 준 높이와 같다(`minimumSizeHint` 면 리스트가 92px 줄어든다).
    - 줄일 때는 리스트가 먼저 줄고, 탭 최소 높이보다 작을 때만 세로 스크롤바가 생긴다(그때만 스크롤바 폭만큼 넓힌다).
    - 창 아래가 화면 밖이면 위로 올린다. 로그창과 푸터는 늘 화면 안에 있다.
  - 탭 테두리만큼 늘어나는 것은 Export 페이지 여백 0 · 창 좌우 여백 -2 · Pin 높이 22 로 상쇄했다.
  - Pin 버튼은 22px 높이라 테마의 `padding: 8px` 이면 글자 자리가 4px 뿐이다 → 이 버튼만 위아래 padding 0(v01.02).

---

## 2. Export 탭

**원본 `A00040_file_exporter_V02` v02.09 와 동작이 같다** — 같은 씬 · 같은 옵션이면 같은 FBX 가 나온다
(§7 검증). 사용법 전체는 원본 문서를 그대로 따른다:

- 흐름 → [A00040 §5](A00040_file_exporter_V02.md#5-사용-흐름). **Naming 만은 v01.06 부터 원본과 다르다** → §2-4
- Type Filter · Joints only under joints → [A00040 §6](A00040_file_exporter_V02.md#6-내보낼-대상-고르기-type-filter--joints-only)
- Move to scene root → [A00040 §7](A00040_file_exporter_V02.md#7-내보내기-동작-move-to-scene-root--keep-hierarchy)
- Paste 가 받아 주는 경로 모양 → [A00040 §4-1](A00040_file_exporter_V02.md#4-1-paste--클립보드의-경로-꽂기-v0208)

### 2-1. `Scene` 버튼 (신규)

**현재 씬이 저장된 폴더를 Export Path 에 바로 채운다.**

따로일 때는 quickTool 의 `Copy Scene Folder` 로 복사하고, 창을 바꿔 A00040 의 `Paste` 로 붙여야 했다.
씬 옆에 FBX 를 뽑는 일이 잦아 한 번에 되게 했다.

| 상황 | 결과 |
|------|------|
| 저장된 씬 | 폴더를 `/` 모양으로 채우고 `Export path : ...` 로그 |
| 저장 안 한 씬 | **기존 경로를 건드리지 않고** `[WARN] Current scene has not been saved yet (no scene folder).` |

### 2-2. Export 규칙 — 내보내기 전에 검사 (v01.03)

`Type Filter` 옆 **`Rules (n/m)`** 드롭다운에서 켤 규칙을 고른다(항목에 마우스를 올리면 설명). `Check` 는 **내보내지 않고** 규칙만 돌린다.

```
Type Filter : [Include Types v]  Rules : [Rules (1/1) v] [Check]        [      Export      ]
```

- 켜 둔 규칙을 **Set's Name 의 모든 세트에 먼저 전부** 돌린다. 하나라도 걸리면 **파일을 단 한 개도 쓰지 않는다** —
  세트별로 내보내다 도중에 멈추는 것이 아니다. 통과한 세트도 내보내지 않는다.
- 첫 실패에서 멈추지 않고 **켠 규칙을 모두** 돌려 문제를 한 번에 보여 준다.
- 켠 규칙이 없으면 예전과 똑같이 바로 내보낸다.

**`Check Hide Mesh`** (기본 꺼짐) — 세트 안의 **모든 메시**(멤버와 그 아래 전부 · 하위 세트 · 컴포넌트 멤버의 오브젝트) 중
**메시 자신이 숨겨진 것**이 있으면 막는다. **메시만 본다**(v01.04) — 그룹 · 조인트 · 로케이터처럼 메시가 아닌 오브젝트는
숨겨져 있어도 괜찮고, 그래서 **켜진 메시가 숨겨진 그룹 안에 있는 경우는 걸리지 않는다**(v01.03 은 모든 조상을 봤다). 숨김 원인:

| 원인 | 로그 |
|------|------|
| 메시 트랜스폼 또는 쉐입의 `visibility` 꺼짐 | `eye.visibility is off` · `bodyShape.visibility is off` |
| `lodVisibility` 꺼짐 | `lodOff.lodVisibility is off` |
| 메시에 걸린 디스플레이 레이어가 숨김 | `display layer 'HIDE_LAYER' is hidden` |
| Drawing Override 로 숨김 | `xxx is hidden by its drawing override` |

원본 쉐입(`intermediateObject`, 디포머가 만든 Orig)은 원래 숨겨진 것이라 보지 않는다.

**걸린 메시는 마야에서 선택된다 (v01.05)** — `Check` 뒤에도, 규칙에 막힌 `Export` 뒤에도 숨긴 메시의 **트랜스폼**이
선택되고(숨겨져 있어도 선택은 된다 — 아웃라이너 · 채널박스에서 바로 고친다) 로그에 `[Info] Selected N object(s) in the scene: ...`.
모든 규칙이 통과하면 선택은 **건드리지 않는다**.

```
--- Rules (Check Hide Mesh) ---
[WARN] Check Hide Mesh : 2 hidden mesh(es) in 2 set(s).
[WARN]   SET_A : 1 hidden mesh(es)
[WARN]     - eye  (eye.visibility is off)
[WARN]   SET_D : 1 hidden mesh(es)
[WARN]     - compHidden  (compHidden.visibility is off)
[Info] Selected 2 object(s) in the scene: eye, compHidden
[WARN] Export not started - fix the problems above, or uncheck the rule in 'Rules' if it is intended. No file was written.
```

**규칙 늘리기** — `app/core/export_rules.py` 에 검사 함수 `check_xxx(ctx) -> RuleResult(passed, logs, nodes)` 를 쓰고
`EXPORT_RULES` 에 `ExportRule(key, label, tooltip, check, default)` 한 줄. 드롭다운 · Export · Check 가 그대로 읽는다.
`nodes` 에 문제 노드(전체 경로)를 담으면 툴이 검사 뒤 선택해 준다 — 없으면 비워 둔다.
`ctx`(`RuleContext`)에는 세트 목록 · 경로 · 타입 필터 · 계층 옵션이 들어 있다 — 규칙에 필요한 값이 더 생기면 여기에 더한다.

### 2-4. Naming — 토큰 칸 + Profile (v01.06)

**A00330_NamingTool Rename > Token 과 같은 화면**이다(공용 위젯 [Framework_MOD_tokenName_qt](Framework_MOD_tokenName_qt.md)).
세트마다 토큰을 `_` 로 이어 파일명을 만들고, `Set Name` 이 File name 리스트를 채운다.

| 규칙 | 값 |
|------|-----|
| `Custom` | 적은 글자 그대로 (비면 건너뜀) |
| `Enum` (v01.09) | **정해진 값 중 고른 하나** — 콤보로 고르므로 오타가 없다. 칸 위에 칸 이름(예 `character`), `Values...` 로 칸 이름 · 값 목록(쉼표로 구분)을 고친다. A00330 Token 의 Enum 과 **같은 공용 규칙**(`Framework/core/token_naming.py` 의 `COMMON_RULES`) |
| `Numbering` | Set's Name 리스트의 **세트 순번** — Start 부터, Pad 0 자리수. **한 이름에 하나만** |
| `Set's Name` | 그 세트의 이름 (네임스페이스 · 경로 없이 — `ns:SET_body` → `SET_body`) |

- 칸 머리 `Token N` 을 눌러 고른 뒤 `Add Token`(오른쪽에 새 칸) / `Delete Token`(마지막 한 칸은 남는다). 넘치면 가로 스크롤.
- **Profile** — `Save` / `New`(지금 칸 복사) / `Rename` / `Delete`.
  - **칸을 고쳐도 저장하지 않는다**(v01.08~). **`Save` 를 눌러야** 지금 칸이 그 프로파일의 기본이 된다.
    v01.06 ~ 01.07 은 고칠 때마다 바로 저장돼서, 툴을 다시 열면 마지막으로 고친 칸이 알림 없이 기본으로 나왔다.
  - `Save` 는 저장 안 한 변경이 있을 때만 켜진다(고쳤다가 원래대로 되돌리면 다시 꺼진다).
  - 저장 안 한 칸은 **프로파일을 바꾸면**(`[WARN] ... unsaved edits ... were dropped.`) 또는 **툴을 닫으면** 버려진다.
  - `New` 는 지금 칸을 새 프로파일에 저장하고 그쪽으로 바꾼다 — 떠나온 프로파일은 건드리지 않는다.
  파일은 툴 폴더 `data/token_profiles/<이름>.json`(PC 별, git 추적 안 함).
- **기본 프로파일 `Default` = 옛 6칸 글자 그대로** `SK_MANU_CH_Name_Basic_Version`(전부 Custom).
  옛 화면의 `Name` 칸을 `Set's Name` 으로 쓰던 방식은 그 칸의 규칙만 `Set's Name` 으로 바꾸면 된다.
- 막는 것(로그 `[WARN] Set Name : ...`, 파일명 리스트는 그대로): 파일명에 못 쓰는 글자 `\ / : * ? " < > |`,
  Numbering 2 개 이상, 모든 칸이 빈 경우.

예) 세트 `SET_body`, `SET_head` · 칸 `SK | MANU | CH | Set's Name | Basic | Version | Numbering(Start 1, Pad 2)`
→ `SK_MANU_CH_SET_body_Basic_Version_01`, `SK_MANU_CH_SET_head_Basic_Version_02`

### 2-3. 원본과 달라진 것 (동작 아님)

| | A00040_V02 | FileTool |
|---|---|---|
| FBX 플러그인이 없을 때 | `cmds.file(typ="FBX export")` 가 트레이스백 | **익스포트 전에** 플러그인을 올려 보고, 안 되면 `[FAIL] Cannot export FBX without the plugin.` |
| undo | 파일 안의 자체 `undo_chunk` 복제 | 공용 `Framework.core.maya_undo.undo_chunk` |
| Paste 경로 정규화 | UI 핸들러 안 | `core.normalize_pasted_path` (마야 없이 검증 가능, 결과 동일) |

---

## 3. Import 탭

v01.10 부터 **하위 탭 둘** — `CSV` / `FBX`. FBX 는 예전 Import 탭 그대로다.

### 3-1. CSV — ARKit 페이셜 CSV 임포트 (v01.10, `A00200_CSV_tool` 이식)

Live Link Face 앱이 내보낸 **ARKit 페이셜 CSV** 를 노드의 **키프레임**으로 임포트하고, CSV 와 같은 이름의
WAV(또는 같은 이름의 동영상에서 ffmpeg 로 추출한 WAV)를 **씬 사운드**로 함께 넣는다.
`A00200_CSV_tool`(ARKit Facial Import 창)을 하위 탭으로 옮긴 것이고 **원본 툴은 그대로 남아 있다.**

```
┌ ARKit Facial CSV ──────────────────────────────────────────────┐
│ CSV File    [D:/mocap/take01_Face_raw.csv        ] [Browse]     │
│ Node        [faceCtrl   (52 ARKit, transform) ▾] [Detect][Selected]
│ Start Frame [ 1 ]   FPS  Recorded [60]  Output [30 ▾]           │
│ Value Scale [ 10.000 ] [x1] [x10]                               │
│ Audio       [✓] Import audio   [ ] Overwrite WAV                │
└────────────────────────────────────────────────────────────────┘
[ Import Animation ]
```

1. `CSV File` — `Browse` 로 CSV 를 고른다. 헤더 줄이 어트리뷰트 이름이다(`Timecode` · `BlendShapeCount` 같은 메타 열은
   건너뛴다).
2. `Node` — 키를 받을 노드. **원본과 다른 점**: 블렌드셰이프 노드만이 아니라 **CSV 열과 같은 이름의 어트리뷰트를 가진
   아무 노드**가 된다(ARKit 52 어트리뷰트를 단 페이셜 컨트롤 등). 블렌드셰이프는 weight 별칭을, 그 밖의 노드는 스칼라
   어트리뷰트를 이름으로 맞춘다(대소문자 무시, 열 순서 무관).
   - `Detect` — 씬의 **모든 블렌드셰이프 + ARKit 이름 어트리뷰트를 가진 노드**(네임스페이스 안도)를 콤보에 담고, ARKit
     이름을 가장 많이 가진 것을 고른다. 항목 글자의 `(n ARKit, 타입)` 이 52개 중 몇 개를 갖는지다.
   - `Selected` — 씬에서 선택한 노드를 콤보에 더하고 고른다(목록에 없는 노드도 된다).
3. `Start Frame` — 첫 행이 놓일 프레임. 오디오도 여기서 시작한다.
4. `FPS` — `Recorded`(녹화, Live Link Face 는 60) / `Output`(30 · 60). 행은 `round(Recorded / Output)` 간격으로
   다운샘플되고(60→30 이면 한 행 걸러), **씬 FPS 가 Output 으로 바뀐다.**
5. `Value Scale` (v01.11) — **키 값 = CSV 값 x 배율.** CSV 는 `0 ~ 1` 실수뿐인데 AdvancedSkeleton 페이셜 컨트롤은
   `0 ~ 10` 을 받으므로 `x10` 을 누르고 임포트한다. `x1` = CSV 값 그대로(블렌드셰이프 weight). 아무 수나 직접 넣어도
   된다(-1000 ~ 1000, 음수 = 방향 반전). 1 이 아니면 로그에 `values scaled x10` 처럼 적힌다.
6. `Audio` — `Import audio` 면 CSV 와 같은 stem 의 WAV 를 찾는다(`..._Face_raw.csv` 는 `..._Face.wav` 도 본다). 없으면
   같은 stem 의 동영상(MOV · MP4 · M4V · MKV · AVI · MXF · WEBM)에서 **PATH 의 ffmpeg** 로 추출한다. `Overwrite WAV` 는 이미
   있어도 다시 추출. ffmpeg 가 없거나 오디오 스트림이 없으면 로그에 적고 건너뛴다.
7. `Import Animation` — 매칭된 어트리뷰트 전부에 키, 타임라인 in/out 을 임포트 구간까지 넓히고(줄이지 않음), 오디오를
   넣는다. **키 · 타임라인 · 사운드 노드가 한 번의 undo** 다(원본은 키만 묶였다). 로그에 프레임 수 · 적용/미매칭 어트리뷰트 수가
   적힌다. 매칭되는 열이 하나도 없으면 아무것도 하지 않고 `[ERR]`.

> **구현 메모** — `app/core/csv_ops.py` (UI 비의존, maya.cmds 는 함수 안에서만). `node_targets(node)` 가 노드 종류에 따라
> `{ 소문자이름: 플러그 }` 를 만들고, `list_candidate_nodes()` 는 `ls(type="blendShape")` + `ls("*.jawOpen", recursive=True)`
> 류의 대표 어트리뷰트 5개로 찔러 ARKit 노드를 찾는다(씬 전체 listAttr 보다 싸다). 로직은 원본 `arkit_facial_import.py` 와
> 같고 로그만 영어다.

### 3-2. FBX

#### `Import FBX normal`

FBX 임포트가 **파일에 저장된 노멀을 그대로** 쓰게 한다(`OverrideNormalsLock` = 1).
**다음 임포트부터 적용되는 전역 FBX 설정**이라 지금 씬은 바뀌지 않는다.

- `FBXProperty` 는 `fbxmaya` 플러그인이 등록하는 프로시저라, **플러그인을 먼저 올려 보고** 안 되면 로그에 이유를 남긴다.
- 로그: `FBX import : OverrideNormalsLock ON (applies to the next import).`

#### `Mocap FBX Import (Exact Rotation)` (v01.13)

**마야 FBX 임포터가 일부 조인트의 회전을 뒤집는 문제**를 고쳐서, 모캡 FBX 를 블렌더를 거치지 않고 정확하게 임포트한다.
배경 · 실측은 [계획서](plans/A00480_FileTool_fbx_exact_import_plan.md).

- **왜** — 마야 임포터는 회전 키를 "이전 키에 가까운 동치 오일러" 로 바꿀 때 회전 순서와 상관없이 XYZ 꼴 `(x+180, 180−y, z+180)` 을 쓴다.
  Vicon 모캡처럼 조인트 회전 순서가 XZY 등이고 값이 ±180° 를 넘나들면 **자세가 틀린다**(`BCM_01_004.fbx` CHOEUN: Hips 1-5493 · RightArm 3707-6285,
  손끝 최대 200cm). 임포트 옵션 `Quaternion Interpolation` 세 모드 다 틀리고 끄는 옵션이 없다.
- **어떻게** — 마야 임포터로 평소처럼 임포트한 뒤(`Set As Euler` 모드, 끝나면 사용자 설정으로 되돌림), **같은 FBX 를 순수 파이썬으로 읽어**
  조인트의 회전 커브(파일에 이동 커브가 있으면 이동도)를 **파일 키 그대로** 다시 쓴다.

```
┌ Mocap FBX Import (Exact Rotation) ─────────────────────────────────┐
│ FBX File   [C:/.../BCM_01_004.fbx                        ] [Browse] │
│ Info       FBX 7700, Z-up, cm, 60 fps, frames 1-6285, 5 skeletons,  │
│            365 joints, 390 markers, 67 cameras                       │
│ Skeletons  [x] CHOEUN (73)  [x] SUA (73)  [x] ZHAN (73)      [All]   │
│            [x] IVI (73)     [x] KANA (73)                    [None]  │
│ Options    [x] Skeletons only        [x] Verify against file         │
│            [x] Normalize joints (jointOrient 0, rotateOrder xyz)     │
│            [ ] Unwrap rotations (rotate order aware)   <- Normalize 끌 때만 │
│ [ Import FBX (Exact) ]               [ Fix Scene From FBX ]          │
└─────────────────────────────────────────────────────────────────────┘
```

1. `Browse` — FBX 를 고르면 **바로 읽는다**(씬은 안 건드림, 108MB 0.2초). `Info` 줄과 스켈레톤마다 체크박스(괄호 = 조인트 수)가 생긴다.
   스켈레톤 = 자손에 조인트(LimbNode)가 있는 최상위 노드. ASCII FBX 는 아직 안 된다(`[FAIL]`).
2. `Skeletons` — 임포트할 캐릭터. 체크 안 한 스켈레톤은 임포트 뒤 지운다.
3. `Options`
   - `Skeletons only`(기본 ON) — 스켈레톤 루트 아래의 마커 · 조인트 없는 가지와 카메라 · `System` 같은 다른 최상위 노드를 지운다.
   - `Normalize joints`(기본 ON) — jointOrient(FBX PreRotation)와 회전 순서를 회전 값에 녹여 **모든 조인트를 jointOrient 0 · rotateOrder xyz** 로.
     블렌더 경유(`0020_CHOEUN_0010.mb`)와 같은 표현이다. 자세는 켜든 끄든 같다. 끄면 파일 그대로(jointOrient = PreRotation, 조인트별 회전 순서).
   - `Unwrap rotations` — 키 사이 360° 튐(원본 데이터에도 1603곳)을 **그 조인트 회전 순서의 동치 해**로 없앤다. Normalize 는 늘 이렇게 하므로 Normalize 를 끌 때만 켜진다.
   - `Verify against file` — 샘플 프레임에서 파일 수식과 비교해 최대 오차를 로그에 남긴다(허용 0.001° · 0.001cm, 넘으면 `[FAIL]`).
4. `Import FBX (Exact)` — 체크한 스켈레톤 루트와 **같은 이름이 씬 최상위에 있으면 `[FAIL]` 로 멈춘다**(새 씬에서 쓰거나 이름을 바꾼다).
   임포트 → 정리 → 진단(마야가 틀린 조인트 · 구간을 로그) → 커브 재생성 → 정규화/언랩 → 검증. 타임라인은 **파일 범위 그대로**(1 ~ 6285),
   씬 fps 는 임포터가 파일 fps 로 바꾼다. **undo 는 기록하지 않는다**(키 수백만 개). 임포터가 만드는 빈 네임스페이스(이 파일은 827개)는 지운다.
5. `Fix Scene From FBX` — **이미 FBX 를 마야로 바로 임포트해 둔 씬**(`0010_motion_0010.mb` 같은)을 같은 방법으로 고친다. 씬에서 루트(또는 그 아래 아무
   노드)를 선택하면 그 루트만, 선택이 없으면 FBX 스켈레톤과 이름이 같은 최상위 노드 전부. 회전 순서 · jointOrient 가 파일과 다른 조인트(이미 정규화한 씬 등)는
   `[SKIP]`, 키 시간이 파일 키 시간의 부분집합이 아니면(리타임 · 오프셋) `[FAIL]` 로 멈춘다. 마야 임포터가 줄여 둔 키 · 탄젠트 때문에 생긴 미세 차이(최대 0.5° · 0.016cm)도 함께 고친다.

로그 예 (`BCM_01_004.fbx`, 5명 전부, 이 PC 34초):

```
[Info] FBX 7700, Z-up, cm, 60 fps, frames 1-6285, 5 skeletons, 365 joints, 390 markers, 67 cameras
[Info] Undo is not recorded for this import.
[Info] Imported in 6.7s. Scene time unit film -> ntscf (from the file).
[Info] Removed : 395 marker / non-joint branches, 1 other top nodes (cameras ...), 827 empty namespaces.
[WARN] CHOEUN : Maya had wrong rotations on 2 joints - Hips (1-5493), RightArm (3707-6285). Rebuilt from the file.
...
[OK] Curves rebuilt from the file : 365 joints, 900 rotation + 15 translation curves, 5,750,775 keys (22.5s).
[OK] Normalized joints : jointOrient 0, rotateOrder xyz.
[OK] Verify : max 0.0000 deg rotation, 0.0000 cm position (3.5s).
```

- **알아 둘 것**
  - 회전 · 이동 커브를 다시 쓰는 것은 **조인트(LimbNode)** 만이다. 이동은 파일 · 씬 단위가 둘 다 cm 일 때만 다시 쓴다(아니면 임포터 결과 그대로 + `[Info]`).
  - Cubic 키(마야가 내보낸 FBX 등)는 auto 탄젠트로 쓰고 `[WARN]` — 키 위치 값은 정확하고 키 사이 모양이 근사다. 모캡(Linear)은 해당 없다.
  - PostRotation 이 있는 조인트는 `[SKIP]`(아직 지원 안 함). 애니 스택 · 레이어가 여럿이면 첫 것만 쓴다(`[WARN]`).
  - **Maya 2023 · Windows 10 에서도 써야 한다**(사용자 요구 2026-10-27). 코드는 Python 3.7 문법 · Maya 2023 에도 있는 API 만 쓰고 numpy 를 쓰지 않는다.
    다만 이 PC 에는 Maya 2024 만 있어 **2023 실기 확인은 아직**이다.
  - 로직은 `Framework.core.maya_fbx_exact`(+ `fbx_binary` · `euler_math`) — [Framework_fbx_binary](Framework_fbx_binary.md).

---

## 4. Path 탭

### `Copy Scene Folder`

현재 씬 폴더를 클립보드에 넣는다. 경로는 **OS 네이티브 모양**(윈도우는 `\`)이라 탐색기 주소창 ·
파일 다이얼로그에 그대로 붙여넣을 수 있다. 저장 안 한 씬이면 경고만 남기고 클립보드를 건드리지 않는다.

### `Open Scene Folder`

현재 씬 폴더를 **탐색기로 연다.** 씬 파일이 디스크에 있으면 **그 파일을 선택한 채로** 연다.

| 상황 | 결과 |
|------|------|
| 저장된 씬 · 파일 있음 | 폴더를 열고 씬 파일 선택 |
| 파일이 지워졌거나 이름이 바뀜 | 폴더만 연다 |
| 폴더가 없음(드라이브 분리 등) | 탐색기를 안 띄우고 `[WARN] Scene folder does not exist on disk` |
| 저장 안 한 씬 | 경고만 |
| 탐색기 호출 실패 | 트레이스백 없이 `[WARN] Could not open the folder` |

---

## 5. Reference 탭 (v01.12)

하위 탭 **`Default`**(트리) 와 **`Lineage`**(노드 그래프, v01.17 — §5-1) 둘이다.

```
┌ Reference ─────────────────────────────────────────────────┐
│ ┌ Default ┐                                                 │
│ │ References : 6 (nested 2, missing 1)  Show [Full Path ▾] [Refresh] │
│ │ Reference        File                          Status     │
│ │ ▾ MID_A          D:\...\mid.ma                  Loaded     │
│ │     MID_A:LEAF   D:\...\leaf.ma                 Loaded     │
│ │ ▾ MID_B{1}       D:\...\mid.ma                  Loaded     │
│ │     MID_B:LEAF   D:\...\leaf.ma                 Loaded     │
│ │   LEAF_TOP{2}    D:\...\leaf.ma                 Unloaded   │  (회색 — 안의 중첩은 로드돼야 보인다)
│ │   GONE{3}        D:\...\gone.ma                 Missing    │  (빨강 — 파일이 디스크에 없다)
│ │ [ Open in Explorer ]            [ Copy Path ]             │
└─┴───────────────────────────────────────────────────────────┘
```

- **목록** — 현재 씬의 레퍼런스 **전부**. 레퍼런스 안의 레퍼런스(중첩, 깊이 제한 없음)는 부모 행 아래 자식 행으로 들어간다(기본 전부 펼침).
  `Reference` 열은 네임스페이스(같은 파일을 여러 번 레퍼런스하면 마야가 붙이는 `{1}` `{2}` 복사 번호를 뒤에), `File` 은 실제 경로
  (복사 번호 뺀 것, 윈도우 모양), `Status` 는 `Loaded` / `Unloaded`(회색) / `Missing`(빨강). 툴팁에 레퍼런스 노드 이름 · 씬에 적힌 원래 경로(환경 변수 · 상대 경로면 다를 수 있다).
  최상위 순서는 Reference Editor 와 같다.
- **`Show` 콤보 (v01.16)** — File 열을 **`Full Path`**(기본, 전체 경로) / **`File Name`**(파일 이름만) 으로 바꿔 본다. 모든 레퍼런스가
  같은 긴 폴더에 있을 때 이름만 보는 쪽이 읽기 쉽다. **글자만 바뀐다** — 열기 · 더블클릭 · 복사는 그대로 전체 경로, 툴팁에도 전체 경로.
  `File Name` 이면 헤더도 `File Name`. 고른 모드는 마야 optionVar 에 기억돼 다음에 툴을 열 때도 같다. 바꿀 때 씬은 다시 읽지 않는다.
- **탭을 열 때마다 씬을 다시 읽는다.** 다른 씬을 열고 와도 `Refresh` 를 안 눌러도 된다(눌러도 된다). 레퍼런스가 없으면 `[Info] No references in the current scene.`
- **`Open in Explorer`** — 고른 행들의 파일을 탐색기에서 연다. **파일마다 창 하나**, 그 파일이 선택된 채로. 더블클릭은 그 행 하나, 우클릭 메뉴 `Reveal in File Explorer (n files)` 는 고른 것 전부.
  같은 파일을 여러 행이 가리키면(복사 번호 · 중첩) **한 번만** 연다. 파일이 없으면(`Missing`) **그 폴더**를 열고 `[WARN] File is missing - opening its folder instead`, 폴더도 없으면 경고만.
- **`Copy Path`** — 고른 행들의 경로를 클립보드에, **한 줄에 하나**(윈도우 모양 `\`, 같은 파일은 한 번). 우클릭 `Copy file path (n files)` 도 같다. 로그 `Copied to clipboard : 2 paths`.
- 여러 행은 Shift / Ctrl 로 고른다. 아무것도 안 고르고 누르면 `[WARN] No reference selected.`

| 상황 | 결과 |
|------|------|
| 부모 레퍼런스가 **언로드** | 그 안의 중첩 레퍼런스는 **목록에 없다** — 마야가 로드돼야 노드를 만든다. 툴팁에 안내, 로드하고 Refresh |
| 같은 파일을 두 번 레퍼런스 | 행 둘(`MID_A`, `MID_B{1}`), 열기 · 복사는 한 번 |
| 파일이 디스크에 없음 | `Missing` 빨강, 열기는 폴더로 |
| 마야 밖(maya.cmds 없음) | `[WARN] maya.cmds is not available` |

> 마야 밖에서 **디스크의 파일들**이 부르는 레퍼런스를 모으고 임포트하는 것은 [`A00210_FileManager`](A00210_FileManager.md) Maya > Reference 다. 이 탭은 **열려 있는 씬**이다.

### 5-1. Lineage 하위 탭 — 레퍼런스 관계를 노드 그래프로 (v01.17)

Default 와 같은 레퍼런스를 **노드 그래프**로 본다. 데이터는 [`A00211_RefLineage`](A00211_RefLineage.md) 의 스캐너가 만들고,
노드 · 화살표는 [`A00210_FileManager`](A00210_FileManager.md) **Lineage 탭의 그림 그대로**다 — 그래서 Export 한 그래프를 A00210 에서
열어도 똑같이 보인다.

```
┌ Reference ──────────────────────────────────────────────────┐
│ ┌ Default ┐┌ Lineage ┐                                       │
│ │ Reference graph : 4 file(s), 4 reference link(s)  [Refresh] [Fit View] │
│ │                 ┌────────────┐                               │
│ │                 │ top.ma     │  ← 씬 자신(루트, 'current scene')        │
│ │                 │current scene│                               │
│ │                 └─────▲──────┘                               │
│ │        ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  회색 점선 = 참조 대상 → 참조하는 파일 │
│ │  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│ │  │ gone.ma  │  │ leaf.ma  │  │ mid.ma   │  ← 깊이 1 (같은 파일을 두 번 레퍼런스해도 노드 하나) │
│ │  │ unloaded │  │          │  │          │                     │
│ │  └──────────┘  └────▲─────┘  └──────────┘                     │
│ │                     └┄┄┄┄┄┄┄┄┄┄┄┘  mid.ma 안의 중첩 레퍼런스     │
│ │ Graph name [ top            ]            [ Export to Lineage ] │
│ │ Export : D:\store\lineage\top.json  /  Project root : D:\proj   │
└─┴───────────────────────────────────────────────────────────────┘
```

- **노드** = 파일 1개. 씬 자신이 루트(라벨 `current scene`), 로드 안 된 레퍼런스는 `unloaded`, project root 밖이면 `(out of project root)`.
  색은 A00210 레인 팔레트 자동색. **같은 파일을 여러 번 레퍼런스해도 노드는 하나**(Default 탭은 행 둘).
- **화살표** = `참조 대상 → 참조하는 파일` 회색 점선(채운 삼각 화살촉). 중첩 레퍼런스는 깊이별 행으로 자동 배치된다.
- **조작** — 휠 줌(커서 기준) · 중간 버튼 드래그 팬 · 노드 드래그 이동 · 빈 곳 드래그로 러버밴드 선택. `Refresh` 는 씬을 다시 읽고
  (탭을 열 때마다 자동), `Fit View` 는 전체가 보이게 맞춘다(노드가 하나뿐이면 1:1).
- **노드 우클릭** — `Reveal in File Explorer`(없는 파일은 그 폴더) / `Copy Path`. Default 탭과 같은 동작이고, 이 페이지는 절대 경로를
  알고 있어 **project root 없이도** 된다.
- **`Export to Lineage`** — 지금 그래프(끌어 놓은 위치 포함)를 **A00211 과 같은 lineage JSON** 으로 A00210 **Store Repo**
  (`<store_dir>/lineage/<name>.json`)에 쓴다. `Graph name` 이 비면 씬 파일 이름. 같은 이름이 있으면 덮어쓸지 묻는다.
  아래 줄에 저장될 경로와 project root 가 보인다. 그 뒤 A00210 Lineage 탭에서 **Refresh**(동기화는 Push).

| 상황 | 결과 |
|------|------|
| A00210 Store Repo 미설정 | 그래프는 보인다. Export 는 `[WARN] Store Repo is not set - set it in A00210_FileManager ...` |
| Project root 미설정 / 루트 밖 | 노드 key 가 비어 `(out of project root)` — record · 썸네일 링크만 없다 |
| 저장 전(untitled) 씬 | 루트 노드 `(untitled scene)`, Export 는 이름을 쳐야 한다 |
| A00211 · A00210 이 tools 폴더에 없음(릴리즈본) | 이 페이지는 안내문만, 버튼 비활성. Default 탭과 다른 탭은 그대로 |

> **툴 간 import 예외.** 이 저장소는 릴리즈본(툴 하나 + Framework 동봉)을 위해 툴 간 import 를 피하지만([`Release_Layout.md`](Release_Layout.md)),
> 이 탭은 사용자 지시(2026-10-30)로 `A00211_RefLineage` 와 `A00210_FileManager` 를 import 한다(A00211 자체도 A00210 을 쓴다).
> 릴리즈본에 셋을 함께 담거나, 이 페이지 없이 쓴다.

---

## 6. 구조

```
A00480_FileTool/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(reload): MainWindow → 테마(slate_dark) → show → (다음 루프) fit_to_content()
├── __dragDrop_A00480.py        # 셸프 설치 (TOOL_LABEL = "FileTool")
├── icon/                       # A00480_FileTool.svg / .png (폴더 + 들어오고 나가는 화살표)
├── CHANGELOG.md
├── tests/test_reference.py     # Reference > Default 시험 (mayapy 오프스크린, v01.12 · v01.16 Show 콤보)
├── tests/test_reference_lineage.py  # Reference > Lineage 시험 (mayapy 오프스크린, v01.17)
├── tests/test_fbx_core.py      # FBX 리더 · 오일러 수학 시험 (순수 파이썬, 작은 FBX 를 직접 씀, v01.13)
├── tests/test_fbx_exact.py     # Mocap FBX Import (Exact Rotation) 시험 (mayapy 오프스크린, v01.13)
└── app/
    ├── config/version.py       # VERSION = "01.13"
    ├── core/                   # UI 비의존 (결과는 로그 문자열 리스트)
    │   ├── fbx_plugin.py       # ensure_fbx_plugin() — Export · Import 공용
    │   ├── export_ops.py       # A00040_V02 export_ops 이식 (타입 필터 · 파일명 · FBX export)
    │   ├── export_rules.py     # Export 규칙 레지스트리 + Check Hide Mesh (v01.03)
    │   ├── naming_ops.py       # Naming 규칙 묶음(FILE_NAME_RULES) · 기본 토큰 · TOKEN_STORE · build_file_names (v01.06)
    │   ├── import_ops.py       # import_fbx_normal · scan_fbx_exact · import_fbx_exact · fix_scene_from_fbx (v01.13, 본체는 Framework.core.maya_fbx_exact)
    │   ├── csv_ops.py          # Import > CSV : ARKit CSV -> 키프레임(아무 노드) · 후보 노드 탐색 · 오디오(ffmpeg) (v01.10, A00200 이식)
    │   ├── path_ops.py         # scene_folder · open_scene_folder · normalize_pasted_path
    │   └── reference_ops.py    # Reference : scene_references(중첩 트리 순 행) · open_reference_files · clipboard_text (v01.12)
    └── ui/
        ├── main_window.py      # 메뉴 · Pin · QTabWidget · 공용 로그 · 푸터
        ├── export_tab.py       # A00040_V02 화면 + Scene 버튼 · Naming = 공용 토큰 위젯 (v01.06)
        ├── import_tab.py       # 하위 탭 CSV / FBX (FBX = SECTIONS 표, v01.10)
        ├── import_csv_page.py  # Import > CSV 화면 (v01.10)
        ├── import_fbx_exact.py # Import > FBX 의 Mocap FBX Import (Exact Rotation) 섹션 (v01.13)
        ├── path_tab.py         # SECTIONS 표
        ├── reference_tab.py    # Reference 탭 = 하위 탭 Default (트리 · Open in Explorer · Copy Path · 우클릭 · Show 콤보) + Lineage (v01.12 · 16 · 17)
        ├── reference_lineage_page.py  # Reference > Lineage : A00211 ref_scanner 데이터 + A00210 NodeItem/EdgeItem/LineageView 그림 + Export (v01.17)
        ├── button_section.py   # SECTIONS 표 → 두 칸 버튼 그리드 (quickTool 방식)
        ├── type_filter_button.py
        └── rules_button.py     # Rules (n/m) 드롭다운 - EXPORT_RULES 에서 항목을 만든다 (v01.03)
```

### 기능 더하기

- **Import > FBX · Path 탭에 버튼** — 페이지 클래스(`FbxImportPage` · `PathTab`)의 `SECTIONS` 에 `(라벨, 핸들러 이름, 툴팁)`
  한 줄 + 핸들러 메서드. 로직은 `app/core/*_ops.py` 에 두고 **로그 문자열 리스트**를 돌려준다.
- **Import 에 새 파일 형식** — `ui/import_<형식>_page.py` 에 `QWidget(log=...)` 페이지를 만들고 `ImportTab.build_ui` 에
  `addTab` 한 줄 (CSV 가 본보기).
- **섹션이 3~4개를 넘으면** 접이식으로 쌓지 말고 하위 탭으로 나눈다.
- **새 탭** — `app/ui/<name>_tab.py` 에 `QWidget(log=...)` 를 만들고 `main_window.build_ui` 에서 `addTab`.
- **Reference 에 새 하위 탭** — `ui/<name>_page.py` 에 페이지 `QWidget(log=...)` 를 만들고 `ReferenceTab.build_ui` 에 `addTab` 한 줄
  (Lineage 가 본보기). 씬을 읽는 것은 `core/reference_ops.scene_references()`(행 dict 목록)를 같이 쓴다.
- **Export 의 타입 필터 타입** — `export_ops.FILTER_TYPES` + `_TYPE_MATCHERS` 두 곳(원본과 같다).
- **Export 규칙** — `export_rules.EXPORT_RULES` 에 한 줄 + 검사 함수(§2-2).

---

## 7. 검증 (mayapy 2024 + 오프스크린 Qt)

**v01.17 Reference > Lineage** — `tests/test_reference_lineage.py` **31항목 통과**. 같은 합성 씬, A00210 설정은 임시 폴더로 바꿔 끼움:
노드 4(같은 파일 두 번 → 하나) · A00210 `NodeItem` 그대로 · 엣지 4 방향(참조 대상 → 참조하는 파일) · 점선 회색 · 라벨 `current scene` / `unloaded` ·
project-relative key · 깊이별 행 · 레인 팔레트 색 · 드래그 → 모델 위치 + 엣지 재배선 · Reveal(없는 파일은 폴더) · Copy Path · Fit View ·
Export → `<store>/lineage/top.json` 을 A00210 `lineage.load` 로 다시 읽어 노드 · references · 끌어 놓은 위치 유지 · 덮어쓰기 확인(거절 시 유지) ·
이름 지정 · Store 미설정 경고 · root 없으면 key 빈 채 그림 · 저장 전 씬(`(untitled scene)`, Export 경고) · 하위 탭 `Default` + `Lineage` ·
백엔드 없을 때 안내문 + 버튼 비활성.

**v01.12 Reference (v01.16 에 `Show` 콤보 11항목 추가 → 46항목)** — `tests/test_reference.py` 통과 (`mayapy tests/test_reference.py`). 합성 씬 `leaf.ma ← mid.ma ← top`
(mid 를 두 번 = 복사 번호, leaf 를 최상위에도, 없는 파일로 바꾼 레퍼런스 하나):
- core — 6행(중첩 2) · 최상위 순서 = Reference Editor · 자식은 부모 바로 아래 depth 1 · 경로에 복사 번호 없음(`{1}` 따로) · 네임스페이스 앞 `:` 없음 ·
  Loaded / Missing · 요약 로그 · **부모 언로드 → 중첩 행 사라짐 + `nested_hidden`** · 열기(중복 한 번 · 없는 파일은 폴더 · 폴더도 없으면 경고 · 탐색기 실패는 경고) · 복사 문자열(한 줄 하나 · 중복 제거)
- UI — 탭을 보이면 채움(4 최상위 + 중첩 2, 펼침) · 글자(`MID_B{1}` · 윈도우 경로 · 상태) · Missing 빨강 / Unloaded 회색 · 툴팁에 노드 · 선택 순서 · Copy Path → 클립보드 두 줄 ·
  Open in Explorer → 파일마다 한 번 · 더블클릭 한 파일 · 빈 선택 경고 · Refresh 뒤 언로드 반영 · 우클릭 메뉴 항목 · 빈 씬 안내 · 메인 창 탭 4개 + Default · About
- `Show` 콤보(v01.16) — 기본 Full Path · File Name 이면 중첩 · Missing 포함 전 행이 이름만 + 헤더 `File Name` · 저장된 경로와 `selected_paths` 는 전체 경로 그대로 ·
  이름 모드에서 Copy Path 도 전체 경로 · Refresh 뒤 모드 유지 · optionVar 에 기억(새 페이지가 이름 모드로 열림) · 되돌리기 · 모르는 값은 무시

**54항목 통과.** 창 크기는 원본과 나란히 띄워 **둘 다 960 x 853** 인 것을 확인(v01.01).

- **창** — `run()` 을 두 번 불러도 보이는 창은 하나 · 제목 · 탭 `Export / Import / Path` 순서, Export 가 기본 ·
  원본 두 툴과 objectName 이 다름 · 버튼 라벨과 툴팁 · Pin 켜기/끄기
- **Paste 정규화** — 역슬래시 → `/` · 따옴표 벗기기 · 파일이면 폴더 · 여러 줄이면 첫 줄 · 비었으면 경고 ·
  없는 경로는 넣되 경고 · **빈 클립보드면 기존 값 유지**
- **Scene 버튼** — 미저장이면 경로 유지 + 경고 · 저장된 씬이면 `/` 모양 폴더
- **Path 탭** — Copy 미저장 시 클립보드 그대로 · 저장된 씬이면 네이티브 경로 · Open 은 (탐색기 호출을 가로채서)
  파일 선택 / 파일 없으면 폴더 / 폴더 없으면 경고 / 호출 실패 시 경고 · 미저장이면 탐색기 안 띄움
- **Import 탭** — `OverrideNormalsLock` 이 실제로 1 · 플러그인이 없으면 `[WARN]` 만
- **Export = 원본** — 조인트 체인 밑에 메시·로케이터, 그룹 안 메시·커브, **같은 이름 노드**가 있는 씬에서
  옵션 4조합(Move to root / Keep hierarchy × Type Filter × Joints only)마다 원본 `A00040_V02` core 와 FileTool
  **탭 핸들러**로 각각 익스포트해서
  - 파일 이름 목록이 같다
  - **FBX 를 다시 임포트한 계층이 같다**
  - 결과 로그(`[OK]` · exported · excluded)가 같다
  - 익스포트 후 씬 계층이 전과 같고, **Ctrl+Z 한 번** 뒤에도 씬이 깨지지 않는다
- **플러그인 없는 Export** — `[FAIL]` 로그, 파일 안 생김, 트레이스백 없음

**v01.06 Naming** (mayapy 2024): 기본 6칸 · 규칙 콤보 3개 · 미리보기 · 기본 `SK_MANU_CH_Name_Basic_Version` ·
Set's Name 칸 · Numbering(세트 순번, pad) · 프로파일은 `Save` 로만 저장(v01.08, 편집 → 재오픈 시 원래 칸) · Numbering 2 개 차단 · 파일명 금지 글자 차단 · 숫자로 시작 허용.

> 실제 Maya GUI 육안 확인은 아직이다.

## 창 높이 자동 맞춤 (v01.15~)

탭(중첩 포함)을 바꾸면 창 높이가 **지금 보이는 페이지**에 맞게 늘거나 줄어 스크롤 없이 다 보인다. 페이지가 모니터 작업 영역보다
길면 화면 높이에서 멈추고(스크롤 영역이 있는 페이지는 그 페이지만 스크롤), 창 아래가 화면 밖이면 위로 올린다. 폭은 건드리지 않는다(처음 여는 크기는 예전 `fit_to_content` 그대로, 그 뒤 높이만 따라간다).
공용 [`JUN_mod_tabFit_qt_v01`](Framework_MOD_tabFit_qt.md) — A00275 v01.38 과 같은 방식. **마야 GUI 확인 아직.**
