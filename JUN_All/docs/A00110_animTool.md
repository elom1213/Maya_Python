# A00110_animTool 사용법

## 1. 개요

애니메이션 키 작업을 돕는 PySide(Qt) 툴이다. **다섯 개의 탭**과 **공유 로그창**으로 구성된다.

1. **Key Edit** — 선택 오브젝트의 키를 시간 범위로 **이동(앞/뒤 offset)·삭제**하고, 그래프
   에디터에서 선택한 키 구간을 **평평하게 유지(Hold)** 한다. `Shift+A` 핫키로 Hold 를 호출할 수 있다.
2. **Pose Key** — 선택 오브젝트(들)의 **현재 프레임**에 6축(rotate X/Y/Z, translate X/Y/Z)
   값을 키프레임으로 설정한다. 축마다 체크박스가 있어 체크된 축만 적용된다.
3. **Copy Key** (v01.03~) — **Base → Target** 으로 시간 범위 애니메이션 키를 복사하고,
   축별로 값을 **반전(Reverse)** 한다. `cmds.pasteKey` 의 붙여넣기 모드를 콤보박스로 선택한다.
4. **Mirror Key** (v01.04~) — 한쪽 컨트롤러의 키를 **반대쪽 컨트롤러로 좌우 미러**한다(언리얼
   *Mirror Data Table* 과 동일한 결과). 좌/우 토큰(`_l/_r` 등, **JSON 으로 확장 가능**)으로 자동
   페어링하거나 수동 리스트로 짝짓는다. **소스/타겟의 rotateOrder 가 달라도 정확**하다.
5. **Bake** (v01.05~) — **리스트업한 컨트롤러/오브젝트**의 키를 구간 전체에 **정수 프레임 단위로
   굽는다(bake)**. 구간은 **현재 타임라인(플레이백)** 또는 **직접 입력(Custom)** 중 선택한다.
   Maya 네이티브 `bakeResults`(C++)를 써서 **6000+프레임 × 50~100 컨트롤러** 같은 대규모도 빠르다.

> **v01.05 — Bake 탭 신설**: `A00120_FKIK` 의 native `bakeResults` 베이크(Python 프레임 루프 대체)를
> 범용 bake 로 이식했다. 컨스트레인트로 묶지 않고 **리스트의 노드 자체**를 굽는다. 로직은
> `app/core/bake_manager.py`, 대상 리스트는 재사용 위젯 `JUN_mod_tsl_qt_v01`. **Keep constraints**
> 옵션(기본 ON)으로 컨스트레인트를 유지(`pairBlend` 공존)할지 정리(bake down)할지 고른다.

> **v01.04 — Mirror Key 탭 신설**: 컨트롤 키를 좌우 대칭으로 반대쪽에 복사한다. 채널 부호 반전이
> 아니라 **월드 매트릭스 반사 → 타겟 rotateOrder 재분해** 방식이라 rotateOrder/축 정렬에 무관하다.
> 로직은 `app/core/mirror_key_manager.py`, 토큰 JSON 입출력은 `app/core/mirror_token_store.py`
> (`app/config/mirror_tokens.json`)로 분리했다. 리스트 UI 는 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개.

> **v01.03 — Copy Key 탭 신설**: 레거시 단일 파일 툴
> `01_Modules/JUN_PY_CopyPasteKey_V03_01.py`(maya.cmds 기반 "Copy Key Tool V03.01")의
> "키 복사 + 축 Reverse" 기능을 현행 Qt 툴의 세 번째 탭으로 이식했다. 리스트 UI 는 직접
> 만들지 않고 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개로 구성하고, 복사 로직은
> `app/core/copykey_manager.py` 로 분리했다. 레거시의 Match Name(접두/접미 제거)은 생략했다.

- DCC: Autodesk Maya (PySide UI). 키 조작은 `maya.cmds`(`keyframe`/`cutKey`/`copyKey`/
  `pasteKey`/`scaleKey`/`setKeyframe`/`keyTangent`) 표준 명령만 사용 → Maya 2023 호환.
  Mirror Key 만 행렬 연산에 `maya.api.OpenMaya`(2.0) 의 `MMatrix`/`MTransformationMatrix` 사용.
- 복사 알고리즘 원본: 레거시 `JUN_cmd_copyKey_V02`. Pose Key 는 `A00030_quickTool` 의
  `JUN_cmd_anim_rot_x_z_to_zero`(3축)를 6축으로 일반화한 것.

---

## 2. 폴더 구조

```
A00110_animTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마 적용 → show()
├── config.py              # 셸프 버튼 설치 + 드래그&드롭 진입점
├── requirements.txt
└── app/
    ├── config/
    │   ├── version.py            # VERSION / LAST_UPDATE
    │   └── mirror_tokens.json    # 좌/우 토큰 쌍 (Mirror Key, 확장 가능)
    ├── core/              # 로직 (UI 비의존, maya.cmds)
    │   ├── keyframe_manager.py   # 키 이동 / 삭제 / Hold (Key Edit 탭)
    │   ├── hotkey_manager.py     # Shift+A 핫키 설치 / 복원 → Hold 호출
    │   ├── pose_key_manager.py   # 현재 프레임 6축 pose 키 (Pose Key 탭)
    │   ├── copykey_manager.py    # Base→Target 키 복사 + 축 Reverse (Copy Key 탭)
    │   ├── mirror_key_manager.py # 컨트롤 키 좌우 미러 (Mirror Key 탭, OpenMaya)
    │   ├── mirror_token_store.py # mirror_tokens.json 입출력 + 폴백
    │   └── bake_manager.py       # 리스트 노드 구간 bake (Bake 탭, native bakeResults)
    └── ui/main_window.py  # 전체 UI (5개 탭 + 공유 로그창 + 메뉴 바)
```

- 각 manager 는 **UI 비의존 정적 메서드**(`@staticmethod`)로 작성되고 `(count, msg)` 를 반환한다.
  작업 전체를 `cmds.undoInfo(openChunk/closeChunk)` 로 묶어 **Ctrl+Z 한 번**에 취소된다.
- UI(`main_window.py`)는 manager 를 호출하고 결과 메시지를 **모든 탭 공유 로그창**에 출력한다.

---

## 3. 설치

`A00110_animTool/config.py` 를 Maya 뷰포트로 **드래그&드롭** → 셸프에 버튼 생성.

---

## 4. 실행

- 셸프 버튼 클릭, 또는 Script Editor에서:

```python
import tools.A00110_animTool as A00110_animTool
A00110_animTool.run(True)   # True = reload
```

- 창은 항상 위(`WindowStaysOnTopHint`)로 뜨고, 재실행 시 기존 창을 닫고 다시 연다.

---

## 5. UI 구성

```
┌ Help ────────────────────────────────────────────────────────┐  ← 메뉴 바 (Help > About)
│ [Key Edit][Pose Key][Copy Key][Mirror Key][ Bake ]            │  ← 탭 (5개)
├───────────────────────────────────────────────────────────────┤
│  (선택된 탭 내용)                                             │
├ Log (모든 탭 공유) ───────────────────────────────────────────┤
│ ┌ read-only 로그창 (영어 출력) ┐                             │
│ └─────────────────────────────────┘                          │
│      Copyright (c) Park Ji Hun. ...                          │
└───────────────────────────────────────────────────────────────┘
```

- **Help > About**: 작성자·업데이트 날짜 팝업.
- 하단 **로그창**과 저작권 라벨은 **모든 탭이 공유**한다(모든 결과/경고가 여기 출력).

### 5.1 Key Edit 탭

```
┌───────────────────────────────────────────────────┐
│ Start [ 4 ]  End [ 10 ]  Offset [ 5 ]             │
│ [ ◀ Earlier (-) ]        [ Later (+) ▶ ]          │
│ [ Delete Keys in Range ]                          │
│ ┌ Graph Editor ───────────────────────────────┐  │
│ │ [ Hold Selected Range ]                      │  │
│ │ [v] Shift+A hotkey      Shift+A : ON         │  │
│ └──────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

- **Start / End**: 작업할 시간 범위(프레임). **Offset**: 이동량(양수 입력, 부호는 버튼이 결정).
- **◀ Earlier (-)** / **Later (+) ▶**: `[Start, End]` 구간의 키를 Offset 만큼 **앞/뒤로 상대 이동**.
- **Delete Keys in Range**: `[Start, End]` 구간의 키를 **삭제**(클립보드 미사용).
- **채널 스코프**: 채널박스(`mainChannelBox`)에서 **어트리뷰트를 선택해 두면 그 채널만**,
  선택이 없으면 **오브젝트의 모든 애니메이션 커브**가 대상이 된다(이동/삭제 공통).
- **Graph Editor > Hold Selected Range**: 그래프 에디터에서 **선택한 키들**을 커브별로,
  선택 구간의 시작 값으로 **평평하게(flat) 유지**한다(아래 7장 규칙 참고).
- **Shift+A hotkey** 체크박스: 켜면 Shift+A 를 Hold 에 바인딩, 끄면 원래 바인딩으로 복원.
  옆 라벨에 `Shift+A : ON / OFF / unavailable` 상태를 표시한다.

### 5.2 Pose Key 탭

```
┌ Set Pose Key (current frame) ─────────────────────┐
│ [v] rotate X     [ 0 ]                            │
│ [ ] rotate Y     [ 0 ]                            │
│ [v] rotate Z     [ 0 ]                            │
│ [ ] translate X  [ 0 ]                            │
│ [v] translate Y  [ 0 ]                            │
│ [ ] translate Z  [ 0 ]                            │
└───────────────────────────────────────────────────┘
[ Set Pose Key ]
```

- 6축(rotate X/Y/Z, translate X/Y/Z)마다 **체크박스 + 값 입력**.
- **기본 체크 축**: rotate X / rotate Z / translate Y (원본 A00030 의 3축).
- **Set Pose Key**: 선택 오브젝트(들)의 **현재 타임라인 프레임**에 **체크된 축만** 입력값으로
  `setKeyframe`. 체크됐는데 값이 비어 있으면 경고 후 중단.

### 5.3 Copy Key 탭

```
┌───────────────────────────────────────────────────┐
│ [Base]                    [Target]                │  ← 재사용 위젯 2개 (가로 2분할)
│ Select Base               Select Targets          │
│ ┌ QListWidget ┐           ┌ QListWidget ┐         │
│ │  src objs   │           │  tgt objs   │         │
│ └─────────────┘           └─────────────┘         │
│ Add|Del|Up|Down|Sort      Add|Del|Up|Down|Sort    │
│ Start [ 1 ]   End [ 24 ]                           │  ← 기본값 = 현재 playback 범위
│ Paste Option [ insert ▼ ]                         │  ← 기본 insert
│ ┌ Reverse ─────────────────────────────────────┐ │
│ │ Translate [X][Y][Z]   Rotate [X][Y][Z]       │ │  ← 기본 모두 off
│ └──────────────────────────────────────────────┘ │
│ [ Copy Key ]                                      │
└───────────────────────────────────────────────────┘
```

- **Base / Target** (재사용 위젯 `JUN_mod_tsl_qt_v01`): `Select Base`/`Select Targets` 로 현재
  Maya 선택을 리스트에 채운다. Add/Del/Up/Down/Sort 와 "Number: N" 카운트, 리스트 항목 클릭 시
  씬 자동 선택까지 위젯이 내장한다. **Base[i] → Target[i]** 로 같은 인덱스끼리 복사하므로
  **두 리스트의 순서를 맞춰야** 한다(Up/Down/Sort 로 정렬).
- **Start / End**: 복사할 시간 범위(`cmds.copyKey time=(start,end)`). 빌드 시 현재 playback
  범위(`minTime`/`maxTime`)로 채워진다.
- **Paste Option**: `cmds.pasteKey` 의 `option` 인자. **기본 `insert`**. 선택 가능값(10개):
  `insert`, `replace`, `replaceCompletely`, `merge`, `scaleInsert`, `scaleReplace`,
  `scaleMerge`, `fitInsert`, `fitReplace`, `fitMerge`.
- **Reverse**: 체크한 축은 붙여넣은 뒤 `timePivot=Start` 기준으로 값을 반전(`valueScale=-1`).
  Translate X/Y/Z, Rotate X/Y/Z 6개, 기본 모두 off.
- **Copy Key**: 복사 실행. 결과(처리한 쌍 수 / 사용한 옵션 / 건너뛴 쌍 / 개수 불일치 경고)가 로그에 출력.

### 5.4 Mirror Key 탭

```
┌───────────────────────────────────────────────────┐
│ Mode  (•) Auto pair from selection  ( ) Manual list│
│ [Source]                  [Target]                │  ← 재사용 위젯 2개
│ ┌ QListWidget ┐           ┌ QListWidget ┐         │
│ └─────────────┘           └─────────────┘         │
│ [ Resolve Pairs from Selection ]                  │  ← Auto 모드에서 미리보기
│ Mirror Axis (•)X ( )Y ( )Z   Channels [v]T [v]R   │
│ Start [ 1 ] End [ 24 ]   Time (•)Source keys ( )Bake│
│ ┌ L / R Tokens (mirror_tokens.json) [접이식] ────┐│
│ │ ┌ Left │ Right ┐                                ││
│ │ │ _l   │ _r    │  ...                           ││
│ │ └──────┴───────┘                                ││
│ │ [Add Row][Remove Row][Save][Reload]             ││
│ └──────────────────────────────────────────────────┘│
│ [ Mirror Selected ]                               │
└───────────────────────────────────────────────────┘
```

- **Mode**:
  - **Auto pair from selection**(기본): 씬에서 선택한 컨트롤을 토큰으로 자동 페어링한다.
    선택한 쪽이 **소스**, 토큰으로 찾은 반대쪽이 **타겟**.
  - **Manual list**: `Source[i] → Target[i]` 로 같은 인덱스끼리 직접 매칭(Copy Key 방식).
- **Source / Target** (재사용 위젯 `JUN_mod_tsl_qt_v01`): 수동 매칭용. **Resolve Pairs** 로 자동
  페어 결과를 여기에 채워 미리보기/수정할 수 있다.
- **Mirror Axis**: 월드 반사축(기본 **X** = YZ 평면, 좌우 대칭). 보통 캐릭터 좌우축이 월드 X.
- **Channels**: **Translate / Rotate** 그룹 토글(기본 둘 다 on). 회전만 미러하려면 Translate off.
- **Start / End**: 미러 대상 시간 범위(기본 = 현재 playback 범위).
- **Time**: **Source keys**(기본, 소스의 실제 키 시점에만 기록 → 곡선·타이밍 보존) /
  **Bake**(범위 내 정수 프레임 전수 기록).
- **L / R Tokens**: `app/config/mirror_tokens.json` 의 좌/우 토큰 쌍 편집 테이블.
  **Add/Remove Row** 로 행 추가·삭제, **Save** 로 JSON 기록, **Reload** 로 다시 읽기.
  기본 4쌍(`_l/_r`, `_L/_R`, `_lf/_rt`, `Left/Right`). 새 네이밍은 행 추가만으로 지원.
- **Mirror Selected**: 미러 실행. 결과(처리한 페어 수 / 반사축 / 건너뛴 페어)가 로그에 출력.

### 5.5 Bake 탭

```
┌───────────────────────────────────────────────────┐
│ [Bake List]                                       │  ← 재사용 위젯 JUN_mod_tsl_qt_v01
│ Select Objects                                    │     (Select/Add/Del/Up/Down/Sort 내장)
│ ┌ QListWidget ┐                                   │
│ │  ctrl objs  │                                   │
│ └─────────────┘                                   │
│ Range (•) Current timeline  ( ) Custom range      │  ← 라디오 2택 (기본 = Current timeline)
│ Start [ 1 ]   End [ 24 ]                           │  ← Custom 일 때만 활성 (기본 playback 범위)
│ Channels [v] Translate [v] Rotate [ ] Scale       │  ← 기본 T·R
│ [v] Keep constraints (insert blend)               │  ← 기본 ON → 컨스트레인트 유지
│ [v] Simulation                                    │  ← 기본 ON
│ [ Bake List ]                                     │
└───────────────────────────────────────────────────┘
```

- **Bake List** (재사용 위젯 `JUN_mod_tsl_qt_v01`): `Select Objects` 로 현재 씬 선택을 리스트에
  채운다. **베이크 대상은 이 리스트의 항목**이며 씬 선택이 아니다(리스트가 비면 아무것도 안 굽힌다).
  Add/Del/Up/Down/Sort 와 "Number: N" 카운트, 항목 클릭 시 씬 자동 선택은 위젯이 내장한다.
- **Range**: 베이크 구간 소스.
  - **Current timeline**(기본): 현재 타임라인 플레이백 범위(`playbackOptions` min/maxTime)로 굽는다.
    이때 Start/End 입력칸은 비활성.
  - **Custom range**: Start/End 입력칸이 활성되고, 직접 입력한 구간으로 굽는다(기본값 = 현재 playback 범위).
- **Channels**: 베이크할 채널 그룹(**Translate / Rotate / Scale**). 기본 T·R on, Scale off.
- **Keep constraints (insert blend)** (기본 **ON**): 베이크 대상이 컨스트레인트로 구동 중일 때
  동작을 정한다. **ON = 컨스트레인트 유지**(Maya 가 `pairBlend` 삽입 → `blendParent1` 로 컨스트레인트↔키
  전환). **OFF = bake down**(구동을 끊고 키만 남김). 내부적으로 `bakeResults` 의
  `disableImplicitControl` 에 반대로 매핑된다(ON → `False`).
- **Simulation** (기본 ON): `bakeResults(simulation=True)` — 프레임 순차 평가(컨스트레인트/익스프레션
  의존 리그에 안전). 순수 FK 라면 꺼서 가속할 수 있다.
- **Bake List**: 베이크 실행. 결과(개수 / 구간 / 프레임 수 / 컨스트레인트 kept·baked down)가 로그에 출력.

---

## 6. 사용 순서

### Key Edit — 키 이동 / 삭제
1. 대상 오브젝트(들)를 씬에서 선택. (특정 채널만 작업하려면 채널박스에서 어트리뷰트 선택)
2. **Start / End** 입력(이동이면 **Offset** 도).
3. **◀ Earlier (-)** / **Later (+) ▶** 로 이동, 또는 **Delete Keys in Range** 로 삭제.

### Key Edit — Hold
1. 그래프 에디터에서 평평하게 만들 **키 구간을 선택**(커브마다 2개 이상).
2. **Hold Selected Range** 클릭(또는 Shift+A) → 각 커브가 시작 값으로 평평하게 유지된다.

### Pose Key
1. 대상 오브젝트(들) 선택 → 타임라인을 키를 찍을 프레임으로 이동.
2. 적용할 축 체크 + 값 입력 → **Set Pose Key**.

### Copy Key
1. 복사 **원본** 오브젝트들을 선택 → Base 의 **Select Base**.
2. 복사 **대상** 오브젝트들을 선택 → Target 의 **Select Targets**.
   (Base[i] ↔ Target[i] 가 맞도록 **Sort/Up/Down 으로 순서 정렬**)
3. **Start / End** 확인(기본 = 현재 playback 범위) → **Paste Option** 선택(기본 `insert`).
4. 필요하면 **Reverse** 축 체크(예: 좌/우 대칭 복사 시 Rotate Y/Z 등) → **Copy Key**.

### Mirror Key — 자동(Auto)
1. 미러할 **소스 컨트롤(들)을 선택**(예: 왼팔 FK 컨트롤). 한쪽만 선택하면 된다.
2. **Mirror Axis**(보통 X) / **Channels**(T·R) / **Start·End** / **Time** 확인.
3. (선택) **Resolve Pairs** 로 페어 결과를 Source/Target 리스트에 미리보기.
4. **Mirror Selected** → 토큰으로 찾은 반대쪽 컨트롤에 좌우 대칭 키가 기록된다.

### Mirror Key — 수동(Manual)
1. **Mode = Manual list** 선택.
2. 소스들을 선택 → **Select Source**, 타겟들을 선택 → **Select Targets**
   (`Source[i] ↔ Target[i]` 가 맞도록 Sort/Up/Down 으로 정렬).
3. 옵션 확인 후 **Mirror Selected**.

### Mirror Key — 토큰 확장
1. **L / R Tokens** 그룹을 펼친다.
2. **Add Row** → 새 좌/우 토큰 입력(예: `:left` / `:right`).
3. **Save** → `mirror_tokens.json` 에 기록(다음 실행에도 유지). 파일을 직접 편집해도 된다.

### Bake
1. 베이크할 컨트롤러(들)를 씬에서 선택 → **Select Objects** 로 **Bake List** 에 채운다(Add 로 추가도 가능).
2. **Range** 선택: **Current timeline**(기본, 현재 재생 구간) 또는 **Custom range**(Start/End 직접 입력).
3. **Channels**(기본 T·R) / **Keep constraints**(기본 ON=유지) / **Simulation**(기본 ON) 확인.
4. **Bake List** → 리스트의 노드만 해당 구간에 정수 프레임 키로 구워진다(단일 Undo).

---

## 7. 동작 규칙

### 공통
- 각 작업은 **단일 Undo 청크** — Ctrl+Z 한 번으로 취소된다.
- manager 는 결과를 `(개수, 메시지)` 로 돌려주고 메시지는 로그창에 영어로 출력된다.

### Key Edit
- **이동**(`move_keys`): `cmds.keyframe(..., relative=True, timeChange=offset)`. Offset 은 **절댓값**으로
  입력하고 버튼이 부호를 정한다(Earlier = `-`, Later = `+`). Offset 이 0이면 `Offset is 0.`.
- **삭제**(`delete_keys`): `cmds.cutKey(..., clear=True)` 로 구간 키 제거.
- **채널 스코프**(이동/삭제 공통): 채널박스 선택 어트리뷰트가 있으면 **그 채널만**(`attribute` 플래그),
  없으면 **모든 커브**(`all curves`). 선택 리스트 전체를 한 번에 넘겨 Maya 네이티브로 일괄 처리(100+ 대응).
- **Hold**(`hold_selected_keys`): 오브젝트가 아니라 **그래프 에디터에서 선택된 키** 기준.
  커브마다 `start`(선택 최소 프레임) 값을 읽어 `(start, end]` 구간을 삭제하고 `end` 에 start 값을
  재삽입, start out / end in 탄젠트를 **flat** 으로 만들어 구간을 평평하게 유지한다. 선택 키가
  2개 미만이거나 값이 없는 커브는 건너뛴다.
- **Shift+A 핫키**(`hotkey_manager`): 툴이 열려 있는 동안만 Shift+A 를 Hold 에 바인딩하고, 창을
  닫으면(`closeEvent`) 원래 바인딩으로 복원한다. **현재 핫키 세트(메모리)만** 수정하며 `.mhk`
  원본은 건드리지 않는다. 활성 세트가 잠긴 경우(예: Maya Default)에는 **경고만** 하고 전역 상태를
  바꾸지 않는다(이때도 Hold 버튼은 동작).

### Pose Key
- `cmds.setKeyframe(obj, at=attr, v=value)` 를 선택 오브젝트 전체 × 체크된 축에 적용.
- 선택이 없으면 `No objects selected.`, 체크 축이 없으면 `No axis checked.`.

### Copy Key
- **인덱스 매칭**: `Base[i] → Target[i]`. 개수가 다르면 **짧은 쪽 기준**으로만 복사하고
  로그에 `count mismatch` 경고를 남긴다.
- 각 쌍: `cmds.copyKey(base, time=(start,end))` → `cmds.pasteKey(tgt, option=<선택값>)`.
- **Reverse**: 체크된 축만 `cmds.scaleKey(tgt.attr, timeScale=0, timePivot=start, valueScale=-1, valuePivot=0)`.
  체크 안 한 축은 scaleKey 자체를 건너뛴다(원본값 그대로).
- 키가 없거나 붙여넣기에 실패한 쌍은 **건너뛰고**(skip) 집계해 로그에 표시한다 → 일부 실패해도 중단되지 않는다.
- **Paste Option** 이 유효값 목록 밖이면 `insert` 로 폴백(방어).

### Mirror Key
- **rotateOrder 무관**: 소스는 `worldMatrix`(오일러 무관)로 읽고, 결과는 `MTransformationMatrix`
  로 분해 후 `MEulerRotation.reorderIt(타겟 rotateOrder)` 로 **타겟 order 에 맞춰** 기록한다.
  채널 부호 반전을 쓰지 않으므로 양쪽 order 가 무엇이든 결과 월드 포즈가 동일하다.
- **미러 수학**(`_mirror_one`): 프레임 `t` 마다
  `local = (refl · worldMatrix · refl) · targetParentInverse` 를 계산한다. `refl` 은 반사축
  대각 행렬(예: X → `diag(-1,1,1,1)`). `refl·M·refl` 은 위치를 해당 축으로 반사하고 회전을
  켤레(conjugate)하므로 **det +1(정상 회전)** 을 유지한다. `getAttr(..., time=t)` 로 타임라인을
  옮기지 않고 평가하며, 부모가 애니메이션돼도 `parentInverseMatrix` 를 t 시점으로 읽어 정확하다.
- **월드 경유의 이점**: 타겟의 실제 부모 공간을 기준으로 로컬값을 역산하므로, 리그가 좌우
  **behavior**(축 반전) 든 **orientation**(동일 축) 셋업이든 상관없이 동작한다(대칭 리그 전제).
- **페어링**(`resolve_pairs`): 이름의 토큰을 양방향 치환해 후보를 만들고 **씬에 존재하는 첫 후보**를
  페어로 삼는다(`objExists` 로 거르므로 `_l` 이 `arm_lower` 에 잘못 걸려도 무시됨).
  토큰이 없으면 **센터 컨트롤**로 보고 self-mirror(같은 컨트롤 제자리 좌우 반전). 토큰은 있는데
  반대쪽 노드가 없으면 **unpaired** 로 분류해 건너뛰고 로그에 표시한다.
- **스왑 방지**: 좌·우를 모두 선택해도 한 방향만 처리한다(먼저 본 쪽이 소스). L→R 기록이 R→L
  읽기를 오염시키는 문제를 피한다.
- **채널 스킵**: 잠긴 채널(`getAttr lock`)은 제외하고, 연결/잠금으로 `setKeyframe` 이 실패하면
  해당 키만 건너뛴다. 키를 하나도 못 넣은 페어는 skip 으로 집계.
- **단일 Undo 청크** — Ctrl+Z 한 번으로 전체 취소.

### Bake
- **대상 = Bake List 항목**(`get_all_items()`). **씬 선택이 아니라 리스트업된 노드만** 굽는다.
  선택만 하고 리스트가 비어 있으면 `Add controllers to the Bake List first.` 경고 후 중단.
- **구간**: **Current timeline** = `playbackOptions` 의 min/maxTime(재생 슬라이더 범위, 애니메이션 전체
  범위가 아님). **Custom range** = Start/End 입력값(빈값/`Start>End` 면 경고).
- **엔진**(`bake_manager.BakeManager.bake`): 프레임 루프 없이 `cmds.bakeResults` 단일 호출
  (`sampleBy=1`, `preserveOutsideKeys=True`, `sparseAnimCurveBake=False`). 베이크 동안
  `refresh(suspend=True)` 로 뷰포트 갱신을 막고, 끝나면 **현재 프레임 복원 + 뷰포트 해제**.
  → currentTime/xform 반복이 없어 6000+프레임 × 50~100 컨트롤러에서 수십 배 빠르다.
- **Keep constraints**(기본 ON) → `disableImplicitControl=False`: 컨스트레인트 구동 노드는
  `pairBlend` 가 삽입되어 **컨스트레인트가 남고 키와 공존**한다(`blendParent1` 로 전환). OFF → `True`:
  구동을 끊고 키만 남기는 **bake down**. (이 툴은 컨스트레인트를 만들거나 `delete` 하지 않는다.)
- **Channels**: 체크한 그룹만(T=tx/ty/tz, R=rx/ry/rz, S=sx/sy/sz). 모두 끄면 경고.
- **단일 Undo 청크** — Ctrl+Z 한 번으로 전체 취소.

---

## 8. 로그 · 문제 해결

### 정상 로그 예시
```
# Key Edit
5 objects : keys in [4-10f] moved +5f  (all curves)
3 objects : keys in [4-10f] deleted  (channels: translateX, translateY)
2 curve(s) held flat at start value.
Shift+A bound to Hold Selected Range.  (set: MyHotkeys)

# Pose Key
4 objects : pose key set on current frame  (rx, rz, ty)

# Copy Key
5 pairs copied (option: insert).
3 pairs copied (option: replace). 2 skipped (no keys / paste failed). [Warning] Base(5) / Target(3) count mismatch.

# Mirror Key
4 token pair(s) loaded.
3 pair(s) resolved. 1 center (self-mirror). 1 unpaired: arm_l_ctrl
4 pair(s) mirrored (axis: X).
2 pair(s) mirrored (axis: X). 1 skipped (no keys / not settable).
4 token pair(s) saved.

# Bake
60 object(s) baked over [1-6000] (6000 frames, constraints kept).
60 object(s) baked over [1-6000] (6000 frames, constraints baked down).
```

### 경고 메시지
- `No objects selected.` — (Key Edit/Pose Key) 선택된 오브젝트 없음.
- `Offset is 0.` — (Key Edit 이동) Offset 이 0.
- `No keys selected in Graph Editor.` — (Hold) 그래프 에디터에 선택된 키 없음.
- `Shift+A not bound: active hotkey set is locked. ...` — 핫키 세트가 잠김(커스텀 세트로 전환 필요).
- `No axis checked.` / `[Warning] <attr> is checked but empty.` — (Pose Key) 축 미체크 / 값 비어 있음.
- `[Warning] Fill both Base and Target lists.` — (Copy Key) Base/Target 비어 있음.
- `[Warning] Enter Start / End.` / `[Warning] Start (n) is greater than End (m).` — (Copy Key) 시간 범위 오류.
- `[Warning] Base(n) / Target(m) count mismatch.` — (Copy Key) 두 리스트 개수 불일치(짧은 쪽만 복사).
- `[Warning] Select source controllers first.` — (Mirror Key Auto) 선택된 컨트롤 없음.
- `[Warning] No pairs resolved.` — (Mirror Key Auto) 토큰으로 페어를 못 찾음(unpaired 만 있음).
- `[Warning] Enable Translate and/or Rotate.` — (Mirror Key) 채널 토글이 모두 off.
- `[Warning] Source(n) / Target(m) count mismatch.` — (Mirror Key Manual) 두 리스트 개수 불일치.
- `[Info] mirror_tokens.json not found. Using built-in defaults.` — JSON 없음(기본 토큰 사용).
- `[Warning] Add controllers to the Bake List first.` — (Bake) Bake List 가 비어 있음(씬 선택만으론 안 됨).
- `[Warning] Enter Start / End.` / `[Warning] Start (n) is greater than End (m).` — (Bake Custom) 시간 범위 오류.
- `[Warning] Enable at least one channel group.` — (Bake) Translate/Rotate/Scale 모두 off.

### 자주 겪는 문제
- **이동/삭제가 일부 채널에만 적용됨** → 채널박스에서 어트리뷰트가 선택돼 있으면 그 채널만 대상이 된다.
  전체 커브에 적용하려면 채널박스 선택을 해제한다.
- **Shift+A 가 안 먹힘** → 활성 핫키 세트가 잠겨 있을 수 있다. 커스텀 핫키 세트로 전환하면 된다(Hold 버튼은 항상 동작).
- **Hold 가 커브를 건너뜀** → 해당 커브에 선택된 키가 2개 미만이다(구간을 만들려면 2개 이상 선택).
- **Pose Key 가 안 찍힘** → 오브젝트 선택 여부와 축 체크/값 입력을 확인.
- **(Copy Key) 타겟에 키가 안 붙음** → 로그의 `skipped` 확인. 원본에 해당 범위 키가 없거나 타겟 이름이 씬에 없을 수 있음.
- **(Copy Key) 엉뚱한 오브젝트끼리 복사됨** → Base/Target **순서**가 어긋남. Sort 또는 Up/Down 으로 인덱스를 맞춘다.
- **(Copy Key) 붙여넣기 모드가 예상과 다름** → Paste Option 콤보 확인(기본 `insert`). `replace`/`replaceCompletely`
  는 타겟 기존 키를 덮어쓰고, `merge` 는 병합한다.
- **(Mirror Key) 반대쪽을 못 찾음(unpaired)** → 컨트롤 네이밍이 토큰 테이블에 없을 수 있다.
  L/R Tokens 에 해당 토큰 쌍을 추가(Save)하거나, Manual 모드로 직접 매칭한다.
- **(Mirror Key) 미러 결과가 안 맞음** → ① Mirror Axis 가 캐릭터 좌우축인지(보통 X) 확인.
  ② 리그가 좌우 대칭(타겟 부모가 소스 부모의 거울상)인지 확인. ③ 비대칭/오프셋 리그면 결과가
  어긋날 수 있다.
- **(Mirror Key) 일부 컨트롤이 skip 됨** → 소스에 해당 범위 키가 없거나 타겟 채널이 잠김/연결됨.
  로그의 `skipped` 수를 확인.
- **(Mirror Key) 센터 컨트롤이 미러 안 됨** → 좌/우 토큰이 이름에 없으면 self-mirror(제자리 반전)로
  처리된다. 의도와 다르면 Manual 모드로 지정한다.
- **(Bake) 아무것도 안 구워짐** → 씬에서 선택만 하고 **Bake List 에 안 넣었을** 수 있다. `Select Objects`
  로 리스트에 채운다(대상은 리스트 항목이지 씬 선택이 아니다).
- **(Bake) 굽는 구간이 예상과 다름** → Range 가 **Current timeline**(재생 슬라이더 범위)인지
  **Custom range**(입력값)인지 확인. Current 는 애니메이션 전체 범위가 아니라 현재 재생 구간이다.
- **(Bake) 키를 구웠는데 컨트롤이 안 움직임처럼 보임** → **Keep constraints**(기본 ON)면 `pairBlend`
  가 끼어 컨스트레인트가 우세할 수 있다. 컨트롤의 `blendParent1` 을 키 쪽으로 바꾸거나, 순수 키만
  원하면 **Keep constraints 를 끄고**(bake down) 다시 굽는다.
