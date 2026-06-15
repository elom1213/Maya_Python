# A00110_animTool 사용법

## 1. 개요

애니메이션 키 작업을 돕는 PySide(Qt) 툴이다. **세 개의 탭**과 **공유 로그창**으로 구성된다.

1. **Key Edit** — 선택 오브젝트의 키를 시간 범위로 **이동(앞/뒤 offset)·삭제**하고, 그래프
   에디터에서 선택한 키 구간을 **평평하게 유지(Hold)** 한다. `Shift+A` 핫키로 Hold 를 호출할 수 있다.
2. **Pose Key** — 선택 오브젝트(들)의 **현재 프레임**에 6축(rotate X/Y/Z, translate X/Y/Z)
   값을 키프레임으로 설정한다. 축마다 체크박스가 있어 체크된 축만 적용된다.
3. **Copy Key** (v01.03~) — **Base → Target** 으로 시간 범위 애니메이션 키를 복사하고,
   축별로 값을 **반전(Reverse)** 한다. `cmds.pasteKey` 의 붙여넣기 모드를 콤보박스로 선택한다.

> **v01.03 — Copy Key 탭 신설**: 레거시 단일 파일 툴
> `01_Modules/JUN_PY_CopyPasteKey_V03_01.py`(maya.cmds 기반 "Copy Key Tool V03.01")의
> "키 복사 + 축 Reverse" 기능을 현행 Qt 툴의 세 번째 탭으로 이식했다. 리스트 UI 는 직접
> 만들지 않고 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개로 구성하고, 복사 로직은
> `app/core/copykey_manager.py` 로 분리했다. 레거시의 Match Name(접두/접미 제거)은 생략했다.

- DCC: Autodesk Maya (PySide UI). 키 조작은 `maya.cmds`(`keyframe`/`cutKey`/`copyKey`/
  `pasteKey`/`scaleKey`/`setKeyframe`/`keyTangent`) 표준 명령만 사용 → Maya 2023 호환.
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
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존, maya.cmds)
    │   ├── keyframe_manager.py   # 키 이동 / 삭제 / Hold (Key Edit 탭)
    │   ├── hotkey_manager.py     # Shift+A 핫키 설치 / 복원 → Hold 호출
    │   ├── pose_key_manager.py   # 현재 프레임 6축 pose 키 (Pose Key 탭)
    │   └── copykey_manager.py    # Base→Target 키 복사 + 축 Reverse (Copy Key 탭)
    └── ui/main_window.py  # 전체 UI (3개 탭 + 공유 로그창 + 메뉴 바)
```

- 각 manager 는 **UI 비의존 정적 메서드**(`@staticmethod`)로 작성되고 `(count, msg)` 를 반환한다.
  작업 전체를 `cmds.undoInfo(openChunk/closeChunk)` 로 묶어 **Ctrl+Z 한 번**에 취소된다.
- UI(`main_window.py`)는 manager 를 호출하고 결과 메시지를 **3개 탭 공유 로그창**에 출력한다.

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
┌ Help ────────────────────────────────────────────┐  ← 메뉴 바 (Help > About)
│ [ Key Edit ] [ Pose Key ] [ Copy Key ]            │  ← 탭
├───────────────────────────────────────────────────┤
│  (선택된 탭 내용)                                  │
├ Log (3개 탭 공유) ────────────────────────────────┤
│ ┌ read-only 로그창 (영어 출력) ┐                  │
│ └─────────────────────────────────┘               │
│      Copyright (c) Park Ji Hun. ...               │
└───────────────────────────────────────────────────┘
```

- **Help > About**: 작성자·업데이트 날짜 팝업.
- 하단 **로그창**과 저작권 라벨은 세 탭이 **공유**한다(모든 결과/경고가 여기 출력).

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
