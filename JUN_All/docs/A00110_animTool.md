# A00110_animTool 사용법

## 1. 개요

애니메이션 키 작업을 돕는 PySide(Qt) 툴이다. **여섯 개의 탭**과 **공유 로그창**으로 구성된다.

1. **Key Edit** — (v01.14~) **접이식 섹션 3개**로 구성된다. **Move Keys**: 키를 시간 범위로
   **이동(앞/뒤 offset)·삭제**. **Graph Editor**: 선택한 키 구간을 **평평하게 유지(Hold)**
   (`Shift+A` 핫키 호출 가능). **Offset & Hold**(기본 접힘): **리스트업한 컨트롤러**의 키를
   **포즈 유지(hold) + 보간(offset)** 구조로 재배치. 섹션을 접고 펼치면 **창 크기가 자동 조정**된다.
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
6. **Follow** (v01.11~) — 좌(**Target**)/우(**Follower**) 리스트로, 각 follower 가 같은 인덱스의
   target 의 **월드 위치·회전(·스케일)과 동일**해지도록 구간 키를 굽는다(컨스트레인트 없이
   `parentConstraint(maintainOffset=False)` 와 동등). **rotateOrder 가 달라도 정확**하고,
   **blend(0~1)** 로 원본 follower 애니메이션과 매치 결과를 섞으며(0=원본 유지, 1=덮어쓰기,
   0.5=반반), 선택된 **애니메이션 레이어**(override/additive)에 키가 들어간다.

> **v01.14 — Key Edit 탭을 접이식 섹션 3개로 분리**: Key Edit 탭을 **Move Keys / Graph Editor /
> Offset & Hold** 세 개의 접이식(collapsible) 섹션으로 나눴다(레거시 `JUN_PY_SelectionTool` 의
> `frameLayout(collapsable=True)` 패턴을 Qt 로 이식). 각 섹션 헤더를 클릭하면 접고/펼치며,
> **Offset & Hold 는 기본 접힘**이다. 접고 펼칠 때(및 탭 전환 시) **창 크기가 현재 탭 콘텐츠에 맞춰
> 자동으로 줄고 늘어난다**. 접이식 위젯은 재사용 모듈 `Framework/qt/MOD_collapsible_qt_v01.py`
> (`JUN_mod_collapsible_qt_v01` 헤더형 섹션 + `JUN_mod_fit_tab_page_v01` 숨김 시 sizeHint 0 인 탭
> 페이지)로 분리했고, 창 크기 조정은 `main_window` 의 `_fit_window`(섹션 `toggled` /
> `QTabWidget.currentChanged` → 한 틱 뒤 `resize`)가 담당한다.

> **v01.13 — Offset & Hold 를 Key Edit 탭으로 통합**: 별도 탭이던 Offset & Hold 를 없애고 **Key Edit
> 탭의 "Offset && Hold" 그룹**으로 옮겼다(기능·로직 동일, UI 위치만 변경). 리스트의 각 오브젝트에서
> **대상 커브들의 키 시점 합집합**을 '포즈 프레임'으로 삼아, 포즈마다 `[start+i·P, start+i·P+hold]`
> (P=hold+offset) plateau 를 만들고 그 사이를 offset 길이로 보간한다. 포즈 프레임 값은 어트리뷰트를
> 시점별로 평가(`getAttr time=`)해 샘플링하므로 그 시점에 키가 없던 커브도 보간값으로 잡힌다. plateau
> 양 끝 안쪽 탄젠트는 **flat**, 보간 구간 바깥은 **spline** 이라 유지→가속→감속→유지가 된다. 로직은
> `app/core/offset_hold_manager.py`, 리스트 UI 는 재사용 위젯 `JUN_mod_tsl_qt_v01`.

> **v01.11 — Follow 탭 신설**: follower 들을 인덱스로 매칭된 target 의 월드 transform 에 맞춰 구간
> 키 베이크한다. target `worldMatrix` 를 follower `parentInverseMatrix` 로 로컬화한 뒤 **follower
> 자신의 rotateOrder 로 재분해**(Mirror Key 의 검증된 경로 재사용)하므로 rotateOrder 무관이다.
> **blend(0~1)** 는 위치/스케일 선형 lerp + 회전 쿼터니언 slerp 로 **키 값에 직접 베이크**(레이어
> weight 는 1 유지)하고, 현재 선택된 애니 레이어가 override 면 `V=F`, additive 면 `V=F−base` 로
> 기록한다. 로직은 `app/core/follow_match_manager.py`, 리스트 UI 는 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개.

> **v01.09 — Mirror Key 동작 기준/Behavior 수식 정리**: ① Mirror 실행(Mirror Selected·Mirror
> Current Frame)이 **씬 선택과 무관하게 Source/Target 리스트의 오브젝트만** 대상으로 한다(선택 →
> `Resolve Pairs`/`Select Source` 로 리스트 채우기 → 실행으로 단계 분리). ② Behavior 모드 수식에서
> **반사를 제거**해 소스의 **로컬 채널 값이 타겟에 그대로 복사**되도록 했다(예: zxy `(-10,-3,-50)` →
> 타겟도 `(-10,-3,-50)`). Behavior 는 반사축에 무관하므로 ON 이면 **Mirror Axis 라디오가 비활성**.

> **v01.08 — Mirror Key 에 "Behavior" 모드 추가**: 반대쪽 컨트롤러의 **고유 forward/up 축 방향을
> 보존**하며 미러한다(Maya `mirror joints` 의 **Behavior** 세팅처럼 좌우 축이 반전된 리그용). 각
> 컨트롤의 **레스트(기준) 포즈**(채널 기본값 상태의 월드 행렬)를 기준으로 상대 미러하므로, 소스가
> 레스트면 타겟도 자기 레스트가 된다. **Behavior 체크박스(기본 ON)** 로 켜고, 끄면 기존 **순수 월드
> 반사(orientation)** 가 된다. 구간 미러(Mirror Selected)·현재 프레임(Mirror Current Frame) 모두 적용.

> **v01.06 — Mirror Key 에 "Mirror Current Frame" 추가**: 구간이 아니라 **현재 프레임 1곳만** 미러한다.
> 키잉은 autoKeyframe 를 재현해 **키가 있던 채널만** 현재 프레임에 키를 갱신하고, **키가 없던 채널은
> 포즈만(`setAttr`)** 미러한다(전역 autoKeyframe 상태는 건드리지 않음). Keying 옵션으로 **Per-channel**
> (기본) / **Per-object**(애니 있는 오브젝트는 선택 채널 전부 키) 중 선택.

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
  Mirror Key / Follow 만 행렬·회전 연산에 `maya.api.OpenMaya`(2.0) 의 `MMatrix`/
  `MTransformationMatrix`/`MEulerRotation`/`MQuaternion` 사용.
- 복사 알고리즘 원본: 레거시 `JUN_cmd_copyKey_V02`. Pose Key 는 `A00030_quickTool` 의
  `JUN_cmd_anim_rot_x_z_to_zero`(3축)를 6축으로 일반화한 것.

---

## 2. 폴더 구조

```
A00110_animTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마 적용 → show()
├── __dragDrop_A00110.py              # 셸프 버튼 설치 + 드래그&드롭 진입점
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
    │   ├── bake_manager.py       # 리스트 노드 구간 bake (Bake 탭, native bakeResults)
    │   ├── follow_match_manager.py # follower→target 월드 매치 베이크 (Follow 탭, OpenMaya + blend)
    │   └── offset_hold_manager.py # 키를 hold+offset 구조로 재배치 (Key Edit 탭 > Offset & Hold)
    └── ui/main_window.py  # 전체 UI (6개 탭 + 공유 로그창 + 메뉴 바)
```

- 각 manager 는 **UI 비의존 정적 메서드**(`@staticmethod`)로 작성되고 `(count, msg)` 를 반환한다.
  작업 전체를 `cmds.undoInfo(openChunk/closeChunk)` 로 묶어 **Ctrl+Z 한 번**에 취소된다.
- UI(`main_window.py`)는 manager 를 호출하고 결과 메시지를 **모든 탭 공유 로그창**에 출력한다.

---

## 3. 설치

`A00110_animTool/__dragDrop_A00110.py` 를 Maya 뷰포트로 **드래그&드롭** → 셸프에 버튼 생성.

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
│ [Key Edit][Pose Key][Copy Key][Mirror Key][Bake][Follow]      │  ← 탭 (6개)
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

**접이식 섹션 3개**(v01.14~)로 구성된다. 각 섹션 **헤더(▼/▶ + 제목)를 클릭하면 접고/펼칠 수 있고**
(레거시 `frameLayout` 패턴), 토글하면 **창 전체 크기가 콘텐츠에 맞춰 자동으로 줄고 늘어난다**.
**Offset & Hold 섹션은 기본 접힘**이다.

```
┌───────────────────────────────────────────────────┐
│ ▼ Move Keys                                       │  ← 클릭하면 접힘/펼침
│    Start [ 4 ]  End [ 10 ]  Offset [ 5 ]          │
│    [ ◀ Earlier (-) ]      [ Later (+) ▶ ]         │
│    [ Delete Keys in Range ]                       │
│ ▼ Graph Editor                                    │
│    [ Hold Selected Range ]                        │
│    [v] Shift+A hotkey      Shift+A : ON           │
│ ▶ Offset & Hold              (기본 접힘)          │  ← 펼치면 아래 내용 표시
│    [Offset/Hold List]  (Select/Add/Del/Up/Down)   │
│    Hold [ 10 ] Offset [ 30 ] Start [(first key)]  │
│    [ Apply Offset & Hold ]                        │
└───────────────────────────────────────────────────┘
```

- **섹션 접기/펼치기**: 헤더 클릭으로 토글. 토글·탭 전환 시 창 높이가 **현재 탭 콘텐츠**에 맞춰
  자동 조정된다(다른 탭은 숨김 페이지의 sizeHint 를 0 으로 보고하므로 창이 현재 탭에만 맞춰진다).

#### Move Keys 섹션 (키 위치 이동 / 삭제)

- **Start / End**: 작업할 시간 범위(프레임). **Offset**: 이동량(양수 입력, 부호는 버튼이 결정).
- **◀ Earlier (-)** / **Later (+) ▶**: `[Start, End]` 구간의 키를 Offset 만큼 **앞/뒤로 상대 이동**.
- **Delete Keys in Range**: `[Start, End]` 구간의 키를 **삭제**(클립보드 미사용).
- **채널 스코프**: 채널박스(`mainChannelBox`)에서 **어트리뷰트를 선택해 두면 그 채널만**,
  선택이 없으면 **오브젝트의 모든 애니메이션 커브**가 대상이 된다(이동/삭제 공통).

#### Graph Editor 섹션 (Hold)

- **Hold Selected Range**: 그래프 에디터에서 **선택한 키들**을 커브별로, 선택 구간의 시작 값으로
  **평평하게(flat) 유지**한다(아래 7장 규칙 참고).
- **Shift+A hotkey** 체크박스: 켜면 Shift+A 를 Hold 에 바인딩, 끄면 원래 바인딩으로 복원.
  옆 라벨에 `Shift+A : ON / OFF / unavailable` 상태를 표시한다.

#### Offset & Hold 섹션 (v01.13~, v01.14~ 접이식·기본 접힘)

리스트업한 컨트롤러의 키를 **포즈 유지(hold) + 보간(offset)** 구조로 재배치한다(위의 이동용 Offset 과는
무관한 별도 기능). 대상은 씬 선택이 아니라 **그룹 안 리스트의 항목**이다.

- **Offset/Hold List** (재사용 위젯 `JUN_mod_tsl_qt_v01`): `Select Objects` 로 현재 씬 선택을 리스트에
  채운다(Add/Del/Up/Down/Sort, "Number: N", 항목 클릭 시 씬 자동 선택 내장). 리스트가 비면 아무것도 안 한다.
- **Hold**: 각 포즈를 평평하게 유지할 구간 길이(프레임, ≥0).
- **Offset**: 인접 포즈 사이 보간 구간 길이(프레임, ≥0). Hold + Offset 은 0보다 커야 한다.
- **Start**: 첫 plateau 시작 프레임. **비우면 오브젝트별 첫 키 프레임**을 앵커로 쓴다(`0` 을 넣으면 0부터).
- **채널 스코프**: 채널박스 선택 어트리뷰트가 있으면 그 채널만, 없으면 모든 (시간 기반) 커브.
- **Apply Offset & Hold**: 재배치 실행. 결과(오브젝트 수 / hold·offset / 스코프 / skip)가 로그에 출력.

**배치 공식** (P = Hold + Offset, start = 앵커, i = 0…n−1, n = 포즈 개수):

```
plateau_start_i = start + i·P          (유지 시작)
plateau_end_i   = start + i·P + Hold    (유지 끝)
사이 구간 [plateau_end_i, plateau_start_{i+1}] = 길이 Offset 보간
```

예) Hold=10, Offset=30, 포즈 3개, Start=0 → `0~10 유지 / 10~40 보간 / 40~50 유지 / 50~80 보간 / 80~90 유지`.

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
│ [v] Behavior (keep target local axes)             │  ← 기본 ON (새 방식)
│ Start [ 1 ] End [ 24 ]   Time (•)Source keys ( )Bake│
│ ┌ L / R Tokens (mirror_tokens.json) [접이식] ────┐│
│ │ ┌ Left │ Right ┐                                ││
│ │ │ _l   │ _r    │  ...                           ││
│ │ └──────┴───────┘                                ││
│ │ [Add Row][Remove Row][Save][Reload]             ││
│ └──────────────────────────────────────────────────┘│
│ [ Mirror Selected ]                               │  ← 구간 미러 (Start/End/Time 사용)
│ ┌ Current Frame ─────────────────────────────────┐ │
│ │ Keying (•) Per-channel (auto-key) ( ) Per-object│ │  ← 기본 Per-channel
│ │ [ Mirror Current Frame ]                        │ │  ← 현재 프레임만 미러
│ └─────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘
```

- **실행 대상은 항상 Source/Target 리스트** (v01.09~): Mirror 실행은 **씬 선택을 읽지 않고**
  리스트에 담긴 오브젝트만 처리한다. 먼저 **Select Source** 또는 **Resolve Pairs** 로 리스트를
  채운 뒤 실행한다.
- **Mode**:
  - **Auto pair from selection**(기본): **Source 리스트**의 컨트롤을 토큰으로 자동 페어링한다
    (Source 가 소스, 토큰으로 찾은 반대쪽이 타겟). Target 리스트가 이미 채워져(Resolve 등) 개수가
    맞으면 그 페어를 그대로 쓴다. **Resolve Pairs** 버튼은 현재 씬 선택을 토큰 페어링해 리스트를
    채워주는 보조 기능(선택 → 리스트).
  - **Manual list**: `Source[i] → Target[i]` 로 같은 인덱스끼리 직접 매칭(Copy Key 방식).
- **Source / Target** (재사용 위젯 `JUN_mod_tsl_qt_v01`): 실행 대상 리스트. **Select Source/Targets**
  로 씬 선택을 담거나, **Resolve Pairs** 로 자동 페어 결과를 채워 미리보기/수정할 수 있다.
- **Mirror Axis**: 월드 반사축(기본 **X** = YZ 평면, 좌우 대칭). 보통 캐릭터 좌우축이 월드 X.
  **Behavior 가 ON 이면 비활성**(behavior 모드는 반사축을 쓰지 않음).
- **Channels**: **Translate / Rotate** 그룹 토글(기본 둘 다 on). 회전만 미러하려면 Translate off.
- **Behavior (keep target local axes)** (기본 **ON**, v01.08~): 반대쪽 컨트롤러의 **고유 forward/up
  축 방향을 보존**하며 미러한다(예: 왼쪽 위팔 up=+Y → 오른쪽 위팔이 자기 고유 up=−Y 를 유지).
  소스의 **로컬 채널 값을 타겟에 그대로 전달**하므로(반사축 무관) Maya `mirror joints` 의
  **Behavior** 세팅으로 만든 좌우 축 반전 리그에 맞는 결과다. **OFF** 면 기존 **순수 월드
  반사(orientation)** — 타겟도 월드 기준으로 정렬된다(up=+Y). 구간·현재 프레임 미러 둘 다 적용.
- **Start / End**: (구간 미러 전용) 미러 대상 시간 범위(기본 = 현재 playback 범위).
- **Time**: (구간 미러 전용) **Source keys**(기본, 소스의 실제 키 시점에만 기록 → 곡선·타이밍 보존) /
  **Bake**(범위 내 정수 프레임 전수 기록).
- **L / R Tokens**: `app/config/mirror_tokens.json` 의 좌/우 토큰 쌍 편집 테이블.
  **Add/Remove Row** 로 행 추가·삭제, **Save** 로 JSON 기록, **Reload** 로 다시 읽기.
  기본 4쌍(`_l/_r`, `_L/_R`, `_lf/_rt`, `Left/Right`). 새 네이밍은 행 추가만으로 지원.
- **Mirror Selected**: **구간 미러** 실행(Start/End/Time 사용). 결과(처리한 페어 수 / 반사축 /
  건너뛴 페어)가 로그에 출력.
- **Current Frame (v01.06~)**: **현재 타임라인 프레임 1곳**만 미러하는 별도 동작
  (Start/End/Time **미사용**). Mode·Mirror Axis·Channels 는 위 설정을 공유한다.
  - **Keying**:
    - **Per-channel (auto-key)**(기본): autoKeyframe 처럼 **키(애니메이션 커브)가 있는 채널만**
      현재 프레임에 키를 갱신하고, **키가 없던 채널은 `setAttr` 로 포즈만**(키 생성 안 함).
    - **Per-object**: 타겟의 대상 채널 중 **하나라도 애니가 있으면 선택 채널 전부** 현재 프레임에
      키(없던 채널엔 커브 신규 생성). 애니가 전혀 없으면 전부 포즈만.
  - **Mirror Current Frame**: 실행. 결과(`... at frame N (axis: X; keyed K, posed P).`)가 로그에 출력.

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

### 5.6 Follow 탭

```
┌───────────────────────────────────────────────────┐
│ [Target]                  [Follower]              │  ← 재사용 위젯 2개 (가로 2분할)
│ Select Targets            Select Followers        │
│ ┌ QListWidget ┐           ┌ QListWidget ┐         │
│ │  tgt objs   │           │  flw objs   │         │
│ └─────────────┘           └─────────────┘         │
│ Add|Del|Up|Down|Sort      Add|Del|Up|Down|Sort    │
│ Start [ 1 ]   End [ 24 ]                           │  ← 기본값 = 현재 playback 범위
│ Channels [v] Translate [v] Rotate [ ] Scale       │  ← 기본 T·R (Scale off)
│ Blend (0..1) [ 1.0 ]  [====슬라이더 0..100====]   │  ← LineEdit ↔ Slider 동기화, 기본 1.0
│ [ Match Follow ]                                  │
└───────────────────────────────────────────────────┘
```

- **Target / Follower** (재사용 위젯 `JUN_mod_tsl_qt_v01`): `Select Targets`/`Select Followers` 로
  현재 Maya 선택을 리스트에 채운다. **Target[i] → Follower[i]** 로 같은 인덱스끼리 매칭하므로
  **두 리스트의 개수와 순서를 맞춰야** 한다(개수가 다르면 경고 후 중단). Add/Del/Up/Down/Sort 와
  "Number: N" 카운트, 항목 클릭 시 씬 자동 선택은 위젯이 내장한다.
- **Start / End**: 매치 키를 구울 시간 범위(정수 프레임 전수). 기본값 = 현재 playback 범위.
- **Channels**: 매치/블렌드할 채널 그룹(**Translate / Rotate / Scale**). 기본 **T·R on, Scale off**.
- **Blend (0..1)**: 원본 follower 애니메이션과 매치 결과의 혼합 비율. **0 = 원본 유지(아무것도 안 함)**,
  **1 = 매치로 완전히 덮어쓰기**(기본), **0.5 = 반반**. LineEdit 와 0~100 슬라이더가 동기화된다.
  위치/스케일은 선형 보간, 회전은 쿼터니언 **slerp**(최단호)로 섞는다.
- **애니메이션 레이어**: 현재 **선택된 애니 레이어**가 있으면 그 레이어에 키가 들어간다(override/additive
  자동 판별). 선택된 레이어가 없거나 BaseAnimation 이면 베이스 커브에 키를 굽는다. blend 는 항상 **키
  값에 베이크**되며(레이어 weight 는 1 유지), follower/프레임마다 독립적이다.
- **Match Follow**: 실행. 결과(매치한 follower 수 / 구간 / 프레임 수 / blend / 사용 레이어 / skip)가
  로그에 출력.

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

### Mirror Key — 현재 프레임만 미러
1. 타임라인을 미러할 프레임으로 이동.
2. 소스 컨트롤(들) 선택(Auto) 또는 Source/Target 리스트 구성(Manual). Mirror Axis·Channels 확인.
3. **Current Frame > Keying** 선택: **Per-channel**(기본, 키 있는 채널만 키) / **Per-object**(애니
   있는 오브젝트는 선택 채널 전부 키).
4. **Mirror Current Frame** → 현재 프레임의 포즈가 반대쪽으로 미러된다. 키가 있던 채널만 그 프레임에
   키가 갱신되고, 키가 없던 채널은 포즈만 적용(키 생성 안 함).

### Mirror Key — 토큰 확장
1. **L / R Tokens** 그룹을 펼친다.
2. **Add Row** → 새 좌/우 토큰 입력(예: `:left` / `:right`).
3. **Save** → `mirror_tokens.json` 에 기록(다음 실행에도 유지). 파일을 직접 편집해도 된다.

### Bake
1. 베이크할 컨트롤러(들)를 씬에서 선택 → **Select Objects** 로 **Bake List** 에 채운다(Add 로 추가도 가능).
2. **Range** 선택: **Current timeline**(기본, 현재 재생 구간) 또는 **Custom range**(Start/End 직접 입력).
3. **Channels**(기본 T·R) / **Keep constraints**(기본 ON=유지) / **Simulation**(기본 ON) 확인.
4. **Bake List** → 리스트의 노드만 해당 구간에 정수 프레임 키로 구워진다(단일 Undo).

### Follow
1. 따라갈 대상(**target**)들을 선택 → Target 의 **Select Targets**.
2. 따라가는 컨트롤(**follower**)들을 선택 → Follower 의 **Select Followers**
   (`Target[i] ↔ Follower[i]` 가 맞도록 **개수·순서를 Sort/Up/Down 으로 정렬**).
3. **Start / End**(기본 = 현재 playback 범위) / **Channels**(기본 T·R) / **Blend**(기본 1.0) 확인.
4. (선택) 키를 특정 **애니 레이어**에 굽고 싶으면 Channel Box / Anim Layer 에디터에서 **그 레이어를
   선택**해 둔다.
5. **Match Follow** → 각 follower 가 구간 내 매 프레임에서 target 의 월드 위치/회전(/스케일)에 맞춰
   키가 구워진다(단일 Undo). blend < 1 이면 원본과 섞인다.

### Offset & Hold (Key Edit 탭 > Offset & Hold 그룹)
1. 재배치할 컨트롤러(들)를 씬에서 선택 → **Select Objects** 로 **Offset/Hold List** 에 채운다.
   (특정 채널만 작업하려면 채널박스에서 어트리뷰트 선택)
2. **Hold**(포즈 유지 길이) / **Offset**(보간 길이)를 입력하고, 필요하면 **Start**(시작 프레임, 비우면
   각 오브젝트의 첫 키) 입력.
3. **Apply Offset & Hold** → 각 오브젝트의 포즈가 hold 만큼 유지되고 사이가 offset 으로 보간되도록
   키가 재배치된다(단일 Undo).

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
- **두 가지 미러 모드** (Behavior 체크박스, v01.08~). 둘 다 프레임 `t` 마다 `_mirrored_values` 가
  타겟 로컬 TRS(dict)를 계산하고, `getAttr(..., time=t)` 로 타임라인을 옮기지 않고 평가한다:
  - **Behavior (기본, ON)** (v01.09~): 소스의 **로컬 채널 값**(translate/rotate)을
    `getAttr(src.attr, time=t)` 로 읽어 타겟에 **그대로 복사**한다(행렬·반사 연산 없음). Maya
    `mirror joints` 의 **Behavior** 세팅으로 만든 좌우 축 반전 리그는 컨트롤러 자체가 거울상으로
    정렬돼 있어, 로컬 채널 값 복사만으로 대칭 포즈가 된다. **반사축(Mirror Axis)에 무관**하므로
    Behavior ON 이면 Axis 라디오가 비활성. 예: rotateOrder zxy `(-10,-3,-50)` → 타겟도
    `(-10,-3,-50)`(소스 order 그대로). 값 자체를 복사하므로 rotateOrder 변환도 일어나지 않는다.
  - **Orientation (OFF)**: 순수 월드 반사(반사축 사용). 소스를 `worldMatrix`(오일러 무관)로 읽고
    `world = refl · Ms · refl` 후 `local = world · targetParentInverse` 로 타겟 로컬화,
    `MEulerRotation.reorderIt(타겟 rotateOrder)` 로 **타겟 order 에 맞춰** 기록한다. `refl` 은
    반사축 대각 행렬(예: X → `diag(-1,1,1,1)`)이라 위치를 반사하고 회전을 켤레(conjugate)하므로
    **det +1(정상 회전)** 을 유지한다. 부모가 애니메이션돼도 `parentInverseMatrix` 를 t 시점으로
    읽어 정확하고, 채널 부호 반전을 쓰지 않아 양쪽 order 가 무엇이든 결과 월드 포즈가 동일하다.
- **페어링**(`resolve_pairs`): 이름의 토큰을 양방향 치환해 후보를 만들고 **씬에 존재하는 첫 후보**를
  페어로 삼는다(`objExists` 로 거르므로 `_l` 이 `arm_lower` 에 잘못 걸려도 무시됨).
  토큰이 없으면 **센터 컨트롤**로 보고 self-mirror(같은 컨트롤 제자리 좌우 반전). 토큰은 있는데
  반대쪽 노드가 없으면 **unpaired** 로 분류해 건너뛰고 로그에 표시한다.
- **스왑 방지**: 좌·우를 모두 선택해도 한 방향만 처리한다(먼저 본 쪽이 소스). L→R 기록이 R→L
  읽기를 오염시키는 문제를 피한다.
- **채널 스킵**: 잠긴 채널(`getAttr lock`)은 제외하고, 연결/잠금으로 `setKeyframe` 이 실패하면
  해당 키만 건너뛴다. 키를 하나도 못 넣은 페어는 skip 으로 집계.
- **단일 Undo 청크** — Ctrl+Z 한 번으로 전체 취소.

### Mirror Key — 현재 프레임만 미러(`mirror_current_frame`)
- **대상 시점 = 현재 프레임 1곳**(`currentTime`). Start/End/Time(Source keys/Bake) 컨트롤은 미사용.
  미러 수학·페어링·반사축은 구간 미러와 동일(`_mirrored_values` 공유).
- **autoKeyframe 재현(전역 autoKeyframe 상태 미변경)** — 채널의 time 애니 커브 유무로 분기한다.
  애니 판정은 `cmds.keyframe(... name=True)` 로 연결 커브를 받아 **`animCurveT*`(시간 기반)** 만
  인정한다(set-driven-key 의 `animCurveU*` 는 "키 없음"으로 취급).
  - **Per-channel (auto-key, 기본)**: 채널에 time 커브가 **있고 값이 바뀌면**(`|old-new| > tol`,
    `tol=1e-6`) 현재 프레임에 `setKeyframe`. 커브가 **없던 채널은 `setAttr` 로 포즈만**(키 생성 안 함).
    값이 안 바뀐 키 채널은 no-op.
  - **Per-object**: 타겟의 대상 채널 중 **하나라도** time 커브가 있으면 **대상 채널 전부**
    현재 프레임에 `setKeyframe`(없던 채널엔 커브 신규 생성). 전혀 없으면 전부 `setAttr`(포즈만).
- **채널 스킵**: 잠긴/연결로 실패한 채널은 건너뛰고, 아무것도 못 건드린 페어는 skip 으로 집계.
- **단일 Undo 청크** — 키+`setAttr` 가 Ctrl+Z 한 번으로 복원.

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

### Follow (`follow_match_manager.FollowMatchManager.match_follow`)
- **인덱스 매칭**: `Target[i] → Follower[i]`. 개수가 다르면 **경고 후 중단**(Copy/Mirror 와 달리 짧은
  쪽 처리 없이 막는다 — 추종 대상이 어긋나면 결과가 무의미하므로).
- **매치 수학(rotateOrder 무관)**: 프레임 `t` 마다
  `local = worldMatrix(target) · parentInverseMatrix(follower)` 를 `MTransformationMatrix` 로 분해해
  위치(`translation`)·회전(`rotation` 쿼터니언)·스케일(`scale`)을 얻고, 회전은 **follower 자신의
  rotateOrder** 로 재분해한다(`MEulerRotation.reorderIt`). `getAttr(..., time=t)` 로 타임라인을 옮기지
  않고 평가하므로 부모가 애니메이션돼도 정확하다. **offset 0**(정확히 일치, maintainOffset=False).
- **blend(0~1) 는 키 값에 베이크**(레이어 weight=1 유지): 원본 평가값 `O` 와 매치값 `M` 을 섞어 최종
  `F` 를 만든다 — 위치/스케일 선형 lerp `F = O + (M−O)·b`, 회전 쿼터니언 **slerp**(최단호). `blend==0`
  이면 아무것도 안 쓰고 반환(원본 유지), `blend==1` 이고 override(/베이스)면 `F=M` 단축 경로.
- **2-pass(원본 오염 방지)**: 먼저 구간 전체의 원본 `O`(additive 면 레이어 뮤트로 base `B` 도)를
  **모두 읽은 뒤** 키를 쓴다. 먼저 쓴 키가 이후 `O` 읽기를 오염시키는 문제를 피한다.
- **애니메이션 레이어**: **선택된 레이어**의 첫 레이어에 키를 굽는다(여러 개면 첫 번째, 로그 표시).
  `animLayer` 에는 선택 레이어 목록을 주는 전역 쿼리가 없으므로 `cmds.ls(type="animLayer")` 로 전체를
  나열한 뒤 레이어마다 `animLayer(lyr, q=True, selected=True)` 로 검사한다. 채널을 레이어 멤버로
  등록(`animLayer edit attribute`) 후
  `setKeyframe(..., animLayer=layer)`. 모드별 기록값:
  - **override**(weight 1): 평가값 = 레이어 값 → **`V = F`**(최종값 그대로).
  - **additive**(weight 1): 평가값 = base + 레이어 값 → 위치/스케일 **`V = F − B`**(스케일은 `F / B`),
    회전 **`V = B⁻¹ · F`**(회전 합성). base `B` 는 레이어를 잠시 뮤트해 읽고 끝나면 복원.
  - 선택 레이어 없음 / **BaseAnimation** → 레이어 인자 없이 베이스 커브에 `V = F`.
- **채널 스킵**: 잠긴 채널(`getAttr lock`)은 제외하고, 연결/잠금으로 `setKeyframe` 이 실패하면 해당
  키만 건너뛴다. 키를 하나도 못 넣은 follower 는 skip 으로 집계.
- **성능**: 베이크 동안 `refresh(suspend=True)` 로 뷰포트 갱신을 막고, 끝나면 현재 프레임 복원 +
  뷰포트 해제. **단일 Undo 청크** — Ctrl+Z 한 번으로 전체 취소.

### Offset & Hold (`offset_hold_manager.OffsetHoldManager.apply_offset_hold`)
- **대상 = Offset/Hold List 항목**. 씬 선택이 아니라 리스트업된 노드만 처리한다(리스트가 비면 경고).
- **채널 스코프**: 채널박스 선택 어트리뷰트가 있으면 그 채널만(`attribute`), 없으면 오브젝트의 모든
  애니메이션 플러그(`listAnimatable` 중 키가 1개 이상인 것). 시간 기반 키만 대상.
- **포즈 프레임**: 오브젝트별로 **대상 플러그들의 키 시점 합집합**을 정렬·중복제거해 '포즈'로 삼는다.
  모든 대상 채널이 같은 포즈 인덱스를 공유하므로 동일한 plateau 구조로 동기화된다.
- **값 샘플링**: 각 포즈 프레임에서 `getAttr(plug, time=f)` 로 평가해 값을 확보한다(그 시점에 키가
  없던 커브도 보간값으로 잡힘). **수정 전에 먼저 읽어** 재배치가 이후 읽기를 오염시키지 않는다.
- **재배치**: 플러그별로 `cutKey(clear=True)` 로 기존 키를 지운 뒤, 포즈 i 마다
  `start + i·P`(유지 시작)와 `start + i·P + Hold`(유지 끝, Hold>0 일 때)에 같은 값으로 키를 찍는다
  (P = Hold + Offset). **앵커 start** 는 입력값, 비우면 포즈 프레임의 최솟값(첫 키).
- **탄젠트**: plateau 시작 키 `in=spline, out=flat`, 끝 키 `in=flat, out=spline` → 유지 구간은 평평,
  보간 구간은 spline 가속·감속(첫 키 in / 마지막 키 out 은 무의미하므로 영향 없음). Hold=0 이면
  포즈당 키 1개(spline)로 순수 리타이밍.
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
3 pair(s) mirrored at frame 12 (axis: X; keyed 12, posed 6).

# Bake
60 object(s) baked over [1-6000] (6000 frames, constraints kept).
60 object(s) baked over [1-6000] (6000 frames, constraints baked down).

# Follow
4 follower(s) matched over [1-24] (24 frames, blend 1.0). No anim layer selected; keys on base curves.
4 follower(s) matched over [1-24] (24 frames, blend 0.5). Layer 'AnimLayer1' (override).
3 follower(s) matched over [1-24] (24 frames, blend 1.0). Layer 'AnimLayer2' (additive). 1 skipped (no settable channels / no node).

# Offset & Hold
3 object(s) re-timed (hold 10f / offset 30f)  (all curves)
2 object(s) re-timed (hold 10f / offset 30f)  (channels: translateY)  (1 skipped: no keys)
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
- `[Warning] Enable at least one channel group.` — (Bake/Follow) Translate/Rotate/Scale 모두 off.
- `[Warning] Fill both Target and Follower lists.` — (Follow) Target/Follower 비어 있음.
- `[Warning] Target(n) / Follower(m) count mismatch.` — (Follow) 두 리스트 개수 불일치(중단).
- `[Warning] Invalid Blend value.` — (Follow) Blend 입력이 숫자가 아님.
- `[Info] Blend is 0; follower animation unchanged.` — (Follow) blend=0 이라 아무것도 안 함.
- `[Warning] Add objects to the Offset/Hold List first.` — (Offset & Hold) 리스트가 비어 있음.
- `[Warning] Enter Hold and Offset.` — (Offset & Hold) Hold/Offset 입력 누락.
- `[Warning] Hold + Offset must be greater than 0.` — (Offset & Hold) 둘 다 0(주기 0).
- `No animated objects to process. (n skipped: no keys)` — (Offset & Hold) 리스트 항목에 키가 없음.

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
- **(Mirror Key) 반대쪽 컨트롤러의 축 방향(up/forward)이 뒤집혀 보임** → **Behavior** 체크박스를
  확인한다. **ON**(기본)이면 타겟 고유 축을 보존(예: 오른쪽 up=−Y 유지), **OFF**면 월드 기준으로
  정렬(up=+Y)된다. 좌우 축이 반전된(behavior 미러) 리그는 ON, 양쪽 축이 동일한 리그는 OFF 가 맞다.
- **(Mirror Key) 일부 컨트롤이 skip 됨** → 소스에 해당 범위 키가 없거나 타겟 채널이 잠김/연결됨.
  로그의 `skipped` 수를 확인.
- **(Mirror Key) 센터 컨트롤이 미러 안 됨** → 좌/우 토큰이 이름에 없으면 self-mirror(제자리 반전)로
  처리된다. 의도와 다르면 Manual 모드로 지정한다.
- **(Mirror Current Frame) 키가 안 찍히는데 포즈만 바뀜** → 정상이다. 그 채널에 **기존 키(time 커브)가
  없으면** Per-channel 모드는 포즈만 적용한다(autoKeyframe 동일). 키를 강제로 찍으려면 **Per-object**
  로 바꾸거나, 먼저 해당 채널에 키를 하나 만든다.
- **(Mirror Current Frame) set-driven-key 채널이 "키 없음"으로 처리됨** → time 커브(`animCurveT*`)만
  인정하므로 드리븐키(`animCurveU*`)는 포즈만(`setAttr`) 시도된다(드리븐 입력이 있으면 skip).
- **(Bake) 아무것도 안 구워짐** → 씬에서 선택만 하고 **Bake List 에 안 넣었을** 수 있다. `Select Objects`
  로 리스트에 채운다(대상은 리스트 항목이지 씬 선택이 아니다).
- **(Bake) 굽는 구간이 예상과 다름** → Range 가 **Current timeline**(재생 슬라이더 범위)인지
  **Custom range**(입력값)인지 확인. Current 는 애니메이션 전체 범위가 아니라 현재 재생 구간이다.
- **(Bake) 키를 구웠는데 컨트롤이 안 움직임처럼 보임** → **Keep constraints**(기본 ON)면 `pairBlend`
  가 끼어 컨스트레인트가 우세할 수 있다. 컨트롤의 `blendParent1` 을 키 쪽으로 바꾸거나, 순수 키만
  원하면 **Keep constraints 를 끄고**(bake down) 다시 굽는다.
- **(Follow) follower 가 target 과 정확히 안 겹침** → ① Channels 에 필요한 그룹(보통 T·R)이 켜져
  있는지 확인. ② **Blend 가 1.0** 인지 확인(1 미만이면 원본과 섞여 덜 따라간다). ③ follower 채널이
  잠겨/연결돼 있으면 그 채널은 skip 된다(로그의 `skipped` 확인).
- **(Follow) 키가 엉뚱한 레이어/베이스에 들어감** → 실행 전에 원하는 **애니 레이어를 선택**해 둔다.
  선택된 레이어가 없으면 베이스 커브에 들어간다. 로그 끝의 `Layer '...'` / `keys on base curves` 로
  실제 대상 레이어를 확인할 수 있다.
- **(Follow) additive 레이어인데 결과가 두 배로 더해진 듯 보임** → additive 레이어는 base + 레이어
  값이라 base 를 빼고(`V=F−B`) 기록한다. 정상 동작이며, 레이어 weight 를 0 으로 내리면 base 로
  돌아간다. blend 를 키로 베이크하므로 레이어 weight 는 1 로 두고 쓴다.
- **(Follow) rotateOrder 가 다른데도 회전이 맞는다** → 정상이다. target 의 월드 회전을 follower
  rotateOrder 로 재분해해 기록하므로 채널 값은 서로 달라도 월드 방향은 동일하다.
- **(Follow) Blend=0 인데 아무 일도 안 일어남** → 의도된 동작이다(원본 유지). 효과를 보려면 Blend 를
  0 보다 크게 올린다.
- **(Offset & Hold) 아무것도 안 바뀜** → 씬에서 선택만 하고 **Offset/Hold List 에 안 넣었을** 수 있다.
  `Select Objects` 로 리스트에 채운다(대상은 리스트 항목이지 씬 선택이 아니다).
- **(Offset & Hold) 일부 오브젝트가 skip 됨** → 그 오브젝트(또는 채널박스로 좁힌 채널)에 키가 없다.
  로그의 `skipped` 수를 확인한다.
- **(Offset & Hold) 일부 채널만 재배치됨** → 채널박스에서 어트리뷰트가 선택돼 있으면 그 채널만
  대상이 된다. 전체 커브에 적용하려면 채널박스 선택을 해제한다.
- **(Offset & Hold) 시작 프레임이 예상과 다름** → **Start** 가 비어 있으면 각 오브젝트의 **첫 키
  프레임**을 앵커로 쓴다(오브젝트마다 다를 수 있음). 모두 같은 지점에서 시작하려면 Start 에 값을
  입력한다(예: `0`).
- **(Offset & Hold) 유지 구간이 평평하지 않고 미끄러짐** → Offset 이 0 이면 plateau 끝과 다음 plateau
  시작이 같은 프레임이 되어 유지가 깨질 수 있다. 보간 구간을 주려면 Offset 을 1 이상으로 둔다.
