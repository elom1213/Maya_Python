# A00110_animTool_V02 — Shift+A 추가 기능: Layer Blend Key 계획서

- 작성: 2026-11-04 (현재 V02 = v02.38) → 구현 버전 **v02.39**
- 상태: **v02.39 구현 완료 (2026-11-04)** — 시험 29/29 · UI 11/11, 마야 GUI 확인 아직.
  - 구현 중 바뀐 것: additive 레이어에서 `setKeyframe -animLayer -value` 는 값을 **최종(합성) 값**으로 받아 레이어 값을 역산한다(mayapy 실측).
    그래서 −N 키는 레이어 커브 노드에 직접 쓰고(`_key_raw`), 현재 프레임 Pose 키는 Pose Key 와 같은 호출 → **최종 값 = Pose 값**.
    5장 3번의 "레이어 tx 커브 f100 = 5.0" 은 additive 에선 "f100 최종 tx = 5.0" 으로 확인한다(override 는 둘이 같다).
  - 멤버 판정은 이름 비교 대신 plug 앞단 blend 사슬에 그 레이어 blend 노드가 있는지로(`LayerKeyManager._blend_chain`).
  - `getAttr -time` 은 레이어 blend 를 거치면 옛 값이 나올 때가 있어, 시험은 시간을 실제로 옮겨 잰다.
- 이 문서만 보고 구현할 수 있도록 결정 사항 · 파일 위치 · 로직 · 검증을 모두 적는다.

---

## 1. 요구사항 (사용자 확정)

Shift+A 를 누르면:

1. **기존 기능** — Graph Editor 에서 선택한 키 구간에 Hold Selected Range (`KeyframeManager.hold_selected_keys()`) 를 그대로 수행한다.
2. **추가 기능 (옵션, 사용자가 켜고 끈다)** — 사용자가 고른 애니메이션 레이어(예: `Layer_01`)에:
   - **현재 프레임 − N** 에, 선택 오브젝트에서 **키를 찍을 수 있는 모든 어트리뷰트**에 키를 찍는다.
   - **현재 프레임** 에, `Key / Pose Key` 탭에서 정한 대로(체크된 축 · 값) 키를 찍는다.
   - 결과: 레이어에서 N 프레임 동안 원래 값에서 Pose Key 값으로 부드럽게 바뀐다.

### 결정 사항 (2026-11-04 사용자 답)

| # | 질문 | 결정 |
|---|------|------|
| 1 | −N 프레임 키 값 | **그 시점의 레이어 값을 그대로 유지**해서 키를 찍는다 (레이어 커브를 그 프레임에서 평가한 값. 커브가 없으면 레이어 기본값: Additive 는 0, scale 은 1(Multiply)/0(Additive), Override 는 그 시점의 합성값 — 아래 4.3) |
| 2 | 레이어가 없거나 오브젝트가 멤버가 아닐 때 | **경고하고 건너뛴다** (레이어를 만들거나 멤버로 넣지 않는다). 어떤 레이어를 쓸지는 **사용자가 UI 에서 고른다** |
| 3 | −N 위치에 이미 키가 있을 때 | **덮어쓴다** |

---

## 2. 현재 코드 위치 (2026-11-04 기준)

경로 기준: `JUN_All/tools/A00110_animTool_V02/app/`

| 무엇 | 위치 |
|------|------|
| Shift+A 바인딩 클래스 | `core/hotkey_manager.py` `HotkeyManager` (`NAME_CMD = "JUN_animTool_holdSelectedKeys"`, `runner="run_hold"`) |
| Shift+A 실행 함수 | `core/hotkey_manager.py:163` `HotkeyManager.run_hold()` — **정적 함수, nameCommand(MEL `python("...")`) 로 불린다. UI 인스턴스에 접근하지 않는다** |
| Hold 로직 | `core/keyframe_manager.py:225` `KeyframeManager.hold_selected_keys()` → `(count, msg)` |
| Pose Key 로직 | `core/pose_key_manager.py` `PoseKeyManager.set_pose_keys(axis_values, objects=None)` — `cmds.setKeyframe(obj, at=attr, v=val)`, `AXES` = rx ry rz tx ty tz |
| Pose Key UI 값 수집 | `ui/main_window.py:3692` `on_set_pose()` — `self.pose_rows[attr] = (QCheckBox, QLineEdit)` |
| Hot Key / Main 페이지 | `ui/main_window.py:624` `_build_hotkey_main_page()` — `self.cb_hotkey` ("Shift+A hotkey") 행 |
| 핫키 설치 | `ui/main_window.py:154` `self.hotkey_mgr = HotkeyManager.hold()` |
| 버전 | `config/version.py` `VERSION = "02.38"` |
| undo 묶기 | `Framework.core.maya_undo.undo_chunk` |

---

## 3. 설계

### 3.1 핵심 문제: 핫키는 UI 값을 모른다

`run_hold()` 는 nameCommand 에서 정적으로 불려서 UI 위젯을 읽을 수 없다.
→ **UI 가 바뀔 때마다 설정을 코어 모듈의 저장소에 밀어 넣고**, `run_hold()` 는 그 저장소를 읽는다.

- 저장소: 새 파일 `core/hold_layer_manager.py` 의 클래스 변수 `HoldLayerManager.settings` (dict).
  - 리로드 시 클래스 변수가 초기화될 수 있다 → UI `__init__` 끝과 각 위젯 변경 시그널에서 매번 다시 push.
- 창을 닫으면 핫키도 원래대로 돌아가므로(기존 동작) 창이 열려 있는 동안만 유효하면 충분하다.
- 창을 다시 열 때 값을 기억하도록 **`cmds.optionVar`** 에 저장한다 (키 접두사 `JUN_A00110_holdLayer_`).

```python
HoldLayerManager.settings = {
    "enabled": False,      # 추가 기능 On/Off
    "layer": "",           # 대상 animLayer 이름
    "offset": 10,          # N (프레임, int >= 1)
    "axis_values": {},     # Pose Key 탭에서 체크된 축 {"rx": 0.0, ...}
}
```

### 3.2 새 코어: `core/hold_layer_manager.py` (maya.cmds, UI 비의존)

```python
class HoldLayerManager:
    settings = {...}

    @classmethod
    def update(cls, **kw): cls.settings.update(kw)

    @classmethod
    def apply(cls, objects=None, frame=None):
        """현재 프레임-N 에 '그 시점 레이어 값' 키, 현재 프레임에 Pose 값 키.
        반환 (count, msg). 실패/건너뜀도 msg 로 (영어)."""
```

`apply()` 순서:

1. `enabled` 가 False → `(0, "")` 즉시 반환 (메시지 없음).
2. 대상 오브젝트 = `cmds.ls(sl=True)` (Graph Editor 키 선택과 무관하게 **오브젝트 선택** 기준. Pose Key 와 같다).
   비었으면 `"[Warning] Layer Blend: no objects selected."`.
3. 레이어 검사: `cmds.objExists(layer) and cmds.nodeType(layer) == "animLayer"` 아니면
   `"[Warning] Layer Blend: layer '<name>' not found. Skipped."` 반환. BaseAnimation 은 UI 에서 고를 수 없게 한다.
4. `axis_values` 가 비면 `"[Warning] Layer Blend: no Pose Key axis checked. Skipped."`.
5. 오브젝트마다 멤버 검사:
   - `members = cmds.animLayer(layer, q=True, attribute=True) or []` (형식 `obj.attr`).
   - 멤버 어트리뷰트가 하나도 없는 오브젝트 → 건너뛰고 skipped 목록에 추가.
6. 키 대상 어트리뷰트 = **오브젝트의 keyable 어트리뷰트 중 그 레이어 멤버인 것** (
   `cmds.listAttr(obj, keyable=True, unlocked=True)` ∩ 멤버). 레이어 멤버가 아닌 어트리뷰트에는 레이어 키를 찍을 수 없으므로 무시 (결정 2 와 일관).
   - Pose 축 중 멤버가 아닌 축이 있으면 그 축만 경고 목록에 넣는다.
7. `t0 = frame - N`, `t1 = frame` (frame 기본 = `cmds.currentTime(q=True)`).
8. **−N 키 (결정 1 · 3)**: 각 어트리뷰트에 대해 레이어 커브의 t0 값을 구해 그 값으로 키 (덮어쓰기).
   - 레이어 커브: `cmds.animLayer(layer, q=True, findCurveForPlug=f"{obj}.{attr}")` → 있으면
     `cmds.keyframe(curve, q=True, eval=True, time=(t0,))[0]` 로 평가.
   - 커브가 없으면(멤버지만 아직 키 없음): 레이어 블렌드 노드 입력의 현재 정적값을 쓴다 — 4.3 참고.
   - 키: `cmds.setKeyframe(obj, at=attr, t=t0, v=val, animLayer=layer)`.
     같은 시간에 키가 있으면 setKeyframe 이 값만 바꾼다(덮어쓰기). 탄젠트는 기존 설정 유지.
9. **현재 프레임 키**: Pose 축마다 `cmds.setKeyframe(obj, at=attr, t=t1, v=val, animLayer=layer)`.
   - Pose 축이 아닌 다른 어트리뷰트는 t1 에 키를 찍지 않는다 (요구사항: 현재 프레임은 Pose Key 대로).
10. 전부 `undo_chunk()` 하나로 묶는다 — 단 Hold 와 한 번에 undo 되도록 **호출부(run_hold) 에서 묶는다** (3.3).
11. 반환 메시지(영어) 예: `"Layer Blend: 3 objects keyed on 'Layer_01' (f90 -> f100). Skipped: pCube2 (not in layer)."`

### 3.3 `run_hold()` 수정 (`core/hotkey_manager.py:163`)

```python
@staticmethod
def run_hold():
    with undo_chunk():
        count, msg = KeyframeManager.hold_selected_keys()
        lcount, lmsg = HoldLayerManager.apply()
    if lmsg:
        msg = f"{msg}<br>{lmsg}"
    cmds.inViewMessage(amg=msg, pos="topCenter", fade=True)
    return count
```

- **Hold 결과와 무관하게** Layer Blend 는 수행한다 (Hold 가 키 선택이 없어 0 이어도 레이어 키는 찍는다).
  — 애매하면 구현 시 사용자 확인. 기본은 "독립 수행".
- **주의**: `hold_selected_keys` 안에 이미 `undo_chunk` 가 있으면 중첩된다. 중첩해도 되는지 `Framework/core/maya_undo.py` 를 먼저 열어 확인 (openChunk 중첩은 마야가 허용하지만 구현이 플래그로 막는지 확인).
- **활성 레이어 주의**: Hold 는 현재 활성(선택) 레이어에서 동작한다. Layer Blend 는 `animLayer=layer` 플래그로 대상 레이어를 지정하므로 활성 레이어를 바꾸지 않는다. 바꿔야 하는 경우가 생기면 반드시 원래대로 복구.

### 3.4 UI: Hot Key / Main 페이지 (`_build_hotkey_main_page`)

Shift+A 행 아래에 그룹 하나 추가 (문자열 전부 영어):

```
[x] Shift+A hotkey   <status>
  [ ] Layer Blend Key          ← self.cb_hold_layer
      Layer  [Layer_01   v] [Refresh]   ← self.cmb_hold_layer (BaseAnimation 제외 animLayer 목록)
      Frames before  [ 10 ]             ← self.sp_hold_layer_offset (QSpinBox 1~1000)
      Uses Key > Pose Key axes/values.  ← 안내 QLabel
```

- 툴팁: `"Shift+A also keys the chosen layer: all layer attributes at (current - N) with their layer value, and Pose Key axes at the current frame."`
- 레이어 목록: `cmds.ls(type="animLayer")` 에서 `cmds.animLayer(q=True, root=True)` (BaseAnimation) 제외. 기존 Layers 탭에 목록 함수가 있으면 재사용 (`grep -n "ls(type=\"animLayer\"" ui/main_window.py core/*.py`).
- 저장된 레이어 이름이 목록에 없으면 콤보에 그대로 넣고 `(missing)` 표시, 실행 시 경고 후 건너뜀 (결정 2).
- `cb_hold_layer` 가 꺼지면 아래 두 위젯 비활성.
- 시그널 → `_push_hold_layer_settings()`:
  - `cb_hold_layer.toggled`, `cmb_hold_layer.currentTextChanged`, `sp_hold_layer_offset.valueChanged`
  - **Pose Key 행** `self.pose_rows` 의 각 `cb.toggled` / `le.textChanged` 에도 연결 (Pose 값이 바뀌면 바로 반영).
  - Pose 값 수집은 `on_set_pose()` 의 로직을 `_collect_pose_axis_values(warn=False)` 로 뽑아 공유 (빈 칸 · 숫자 아님은 그 축 제외).
- `_push_hold_layer_settings()` 는 `HoldLayerManager.update(...)` + optionVar 저장.
- `__init__` 에서 핫키 설치 직후 optionVar 를 읽어 위젯에 넣고 한 번 push.
- 창 높이: 공용 tabFit 이 이미 걸려 있으므로 추가 작업 없음 (확인만).

---

## 4. 함정 · 확인할 것 (구현 시 mayapy 로 실측)

1. **`setKeyframe -animLayer` 와 멤버 아닌 어트리뷰트**: 멤버가 아니면 키가 BaseAnimation 으로 가거나 에러. 그래서 6단계에서 멤버만 걸러낸다.
2. **회전 · 블렌드 모드**: 레이어 `rotationAccumulationMode` / `scaleAccumulationMode` 에 따라 커브 값 의미가 다르다. 결정 1 은 "레이어 커브 값 유지"이므로 **커브 값을 그대로 다시 넣으면** 모드와 무관하게 맞다. 커브가 없을 때만 4.3 처리.
3. **커브 없는 멤버의 기본값**: 레이어 블렌드 노드(`animBlendNodeAdditive*` 등)의 해당 레이어 입력(inputB) 정적값을 `getAttr` 로 읽는다. 찾기 어려우면 Additive=0 · scale(Multiply 모드)=1 · Override=그 시점 `getAttr(obj.attr, t=t0)` 로 폴백. 관련 메모: `wip-a00110-layer-range-merge.md`(정적 멤버는 blend 노드 inputB), `animlayer-copy-cut-traps.md`.
4. **`findCurveForPlug`** 는 리스트를 돌려준다 → `[0]`. rotate 는 컴파운드라 `obj.rotateX` 처럼 잎 단위로 질의.
5. **레이어 Lock** (`cmds.animLayer(layer, q=True, lock=True)`) 이면 키가 안 찍힌다 → 경고하고 건너뜀.
6. **레이어 Mute** 는 키는 찍히지만 결과가 안 보인다 → 메시지에 `(layer muted)` 덧붙이기.
7. **N 이 현재 프레임보다 앞 범위 밖**이어도 setKeyframe 은 된다. 제한하지 않는다.
8. **Pose Key 축이 0개** → Layer Blend 만 건너뛰고 Hold 는 수행.
9. 단위: `setKeyframe v=` 의 rotate 값은 UI 단위(도). Pose Key 와 같은 방식이라 일치.

---

## 5. 검증 (mayapy headless, `tests/` 에 스크립트)

`tests/test_hold_layer_blend.py` — `maya.standalone` 으로:

1. 큐브에 rx/tx 키 (BaseAnimation), `Layer_01` (Additive) 생성 후 큐브 tx/rx/ry 를 멤버로, 레이어 tx 에 f90=2.0 키.
2. `settings = {enabled:True, layer:"Layer_01", offset:10, axis_values:{"rx":0.0,"tx":5.0}}`, currentTime 100 → `apply()`.
3. 확인:
   - 레이어 tx 커브: f90 = 2.0 (기존 값 유지 · 덮어쓰기), f100 = 5.0.
   - 레이어 rx 커브: f90 = 0 (커브 없던 Additive 기본), f100 = 0.0.
   - 레이어 ry: f90 키 있음, f100 키 없음 (Pose 축 아님).
   - BaseAnimation 커브는 변화 없음.
4. 멤버 아닌 오브젝트 선택 → 키 없음 + 메시지에 Skipped.
5. 없는 레이어 이름 → 아무 키도 안 생김 + 경고 메시지.
6. 잠긴 레이어 → 경고.
7. Override 레이어에서도 1~3 반복.
8. `cmds.undo()` 한 번에 Hold + Layer Blend 둘 다 되돌아가는지 (run_hold 경유).

GUI 확인(사용자): 실제 Shift+A 로 뷰포트 메시지 두 줄, 콤보 · 스핀 · 체크 저장/복원.

---

## 6. 마무리 체크리스트

- [ ] `config/version.py` → `02.39`, `LAST_UPDATE`, 버전 이력에 한 줄
- [ ] 새 파일 헤더 관례 (`# Python Script by Ji Hun Park` / `# last Update date :`)
- [ ] `CHANGELOG.md` 항목
- [ ] 툴 가이드 docs (`JUN_All/docs/` 의 A00110 V02 가이드 — Hot Key > Main 섹션에 Layer Blend Key 추가)
- [ ] `JUN_All/docs/WORKLOG.md` (최신이 위, 날짜 헤딩 중복 금지)
- [ ] 메모리: `wip-a00110-hold-layer-blend.md` 새로 + `MEMORY.md` A00110 줄에 링크
- [ ] portfolio EN/KR (해당 시)
- [ ] 로컬 커밋 (경로 명시 스테이징). **푸시는 그 턴에 요청이 있을 때만.**
