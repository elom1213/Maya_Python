# A00110_animTool — Bake 탭 신설 계획서 (FKIK 네이티브 베이크 이식)

## Context (배경 / 목적)

`A00120_FKIK` 의 `bake()` 를 **Python 프레임 루프 → 네이티브 `cmds.bakeResults`** 로
교체해(`docs/plans/A00120_FKIK_bake_speed.md`) 6000+프레임 × 50~100 컨트롤러 환경에서
큰 속도 이득을 얻었다. 이 **검증된 베이크 코어**를 `A00110_animTool` 에 **독립 Bake 탭**으로 이식한다.

요구 사항:
1. animTool UI 에 **Bake 탭 + Bake 버튼** 추가 — 버튼을 누르면 베이크 실행.
2. **라디오 버튼**으로 구간 소스 선택(**기본 = (1)번 체크**):
   - (1) **지금 Maya 타임라인(플레이백) 구간**만 베이크. ← 기본값
   - (2) **Custom 구간** — 첫/끝 프레임을 `QLineEdit` 로 직접 입력.
3. **베이크 대상**: 현재 씬 선택이 아니라 **`MOD_tsl_qt_v01`(재사용 위젯 `JUN_mod_tsl_qt_v01`)
   textScrollList 에 리스트업된 컨트롤러/오브젝트만** 베이크한다.
4. **Keep constraints 체크박스**: 기본 **체크** → `disableImplicitControl=False`
   (컨스트레인트를 유지한 채 `pairBlend` 로 키 공존). 해제하면 `True`(bake down).
5. 사용 환경은 FKIK 와 동일: **6000+프레임 × 50~100 컨트롤러**.

> animTool 의 Mirror Key 탭에 이미 "Bake" *time mode* 가 있으나(미러 전용 시점 모드),
> 본 작업은 **선택 컨트롤러의 애니메이션을 정수 프레임으로 굽는 범용 Bake 탭**으로 별개다.

---

## 1. FKIK bake 와 무엇이 같고 무엇이 다른가

| 구분 | A00120_FKIK `bake()` | A00110 신규 Bake 탭 |
|------|----------------------|---------------------|
| 목적 | 타깃→팔로워 **매칭** 결과를 굽기 | **선택 컨트롤러 자체**의 애니메이션을 dense 키로 굽기 |
| 컨스트레인트 | `parentConstraint(mo=False)` 필요(매칭) | **불필요** — 리스트 노드를 바로 bake |
| 대상 노드 | `flw_list`(쌍의 한쪽) | `JUN_mod_tsl_qt_v01` 리스트 항목(리스트업된 것만) |
| 채널 | translate/rotate | translate/rotate (+선택적 scale) |
| 컨스트레인트 처리 | 임시 생성분 베이크 후 `delete` | **유지 기본**(`dic=False`), 체크 해제 시 bake down |
| 코어 | `bakeResults` + refresh suspend + undo + currentTime 복원 | **동일 코어 재사용** |

→ **재사용 핵심 = 네이티브 `bakeResults` 호출 패턴.** FKIK 의 컨스트레인트 단계만 빼면
그대로 범용 bake 가 된다. 더 단순하고, 같은 속도 이점을 그대로 가진다.

### 코드 재사용 방식 — **자립 복제(권장)**
`CLAUDE.md` 규칙상 툴은 자기완결적이어야 하고 `build_release.py` 는 단일 툴+Framework 만
복사한다. 따라서 `tools.A00120_FKIK...` 를 **직접 import 하지 않고**, animTool 의 core 에
`bake_manager.py` 로 코어를 복제한다. (장기적으로 여러 툴이 공유하게 되면 `Framework` 로
승격하는 별도 작업을 고려 — 본 계획 범위 밖.)

---

## 2. 추가/수정 파일

```
A00110_animTool/
├── app/
│   ├── config/version.py                 # [수정] 01.04 -> 01.05
│   ├── core/
│   │   ├── __init__.py                    # [수정] BakeManager export 추가
│   │   └── bake_manager.py                # [신규] 네이티브 bake 코어 (UI 비의존)
│   └── ui/main_window.py                  # [수정] _build_bake_tab() 추가 + 탭 등록 + 핸들러
```
문서:
```
docs/A00110_animTool.md                    # [수정] Bake 탭 사용법/규칙/로그 추가, 탭 수 갱신
docs/plans/A00110_animTool_bake_tab.md     # [본 문서]
```

---

## 3. Core 설계 — `app/core/bake_manager.py`

다른 manager 와 동일 스타일: `@staticmethod` + `undoInfo` 청크 + `(count, msg)` 반환.

```python
# -*- coding: utf-8 -*-
# A00110_animTool - 선택 컨트롤러를 구간 dense 키로 굽는 코어 (maya.cmds, UI 비의존)
#   A00120_FKIK 의 native bakeResults 베이크를 범용(컨스트레인트 없는 선택 bake)으로 이식.

import maya.cmds as cmds


class BakeManager:

    # match/FKIK 와 동일: scale 제외가 기본. 필요 시 호출부에서 channels 로 확장.
    DEFAULT_CHANNELS = ["tx", "ty", "tz", "rx", "ry", "rz"]

    @staticmethod
    def bake(objects, start, end, channels=None, simulation=True,
             disable_implicit=False):
        """
        objects 의 [start, end] 구간을 native bakeResults 로 굽는다.

        objects          : 베이크할 노드 리스트(리스트 위젯에 리스트업된 항목).
        start, end       : 정수 프레임 구간(포함).
        channels         : 베이크 attr 리스트(기본 translate/rotate). scale 포함 시 호출부 지정.
        simulation       : True = 프레임 순차 평가(컨스트레인트/익스프레션 의존 리그 안전).
        disable_implicit : bakeResults 의 disableImplicitControl 로 그대로 전달.
                           False(기본) = 컨스트레인트 유지(pairBlend 로 키 공존),
                           True        = 구동 컨스트레인트 정리(bake down).
        반환             : (baked_count, msg)

        currentTime/xform 프레임 루프 없이 단일 C++ 베이커로 처리 -> 6000+프레임 × 50~100
        컨트롤러에서 수십 배 빠름. Maya 2023(Python 3.9) 동작 확인.
        """
        if not objects:
            return (0, "[Warning] No objects to bake. Add controllers to the list first.")

        if start > end:
            return (0, "[Warning] Start ({0}) is greater than End ({1}).".format(start, end))

        attrs = list(channels) if channels else list(BakeManager.DEFAULT_CHANNELS)

        cur = cmds.currentTime(q=True)

        cmds.undoInfo(openChunk=True)
        cmds.refresh(suspend=True)
        try:
            cmds.bakeResults(
                objects,
                simulation=simulation,
                time=(start, end),
                sampleBy=1,
                attribute=attrs,
                disableImplicitControl=disable_implicit,
                preserveOutsideKeys=True,
                sparseAnimCurveBake=False,
            )
        finally:
            cmds.refresh(suspend=False)
            cmds.currentTime(cur, edit=True)
            cmds.undoInfo(closeChunk=True)

        n = len(objects)
        frames = end - start + 1
        kept = "kept" if not disable_implicit else "baked down"
        return (n, "{0} object(s) baked over [{1}-{2}] ({3} frames, constraints {4}).".format(
            n, start, end, frames, kept))
```

### 플래그 의미
- `simulation=True` : 순차 평가(리그 의존 안전). 순수 FK 라면 호출부에서 `False` 로 가속 가능.
- `sampleBy=1` : 매 정수 프레임 키.
- `disableImplicitControl=disable_implicit` : **기본 False = 컨스트레인트 유지**(Maya 가 `pairBlend`
  를 삽입, `blendParent` 로 컨스트레인트↔키 블렌드). True 면 구동을 끊어 키만 남김(bake down).
- `preserveOutsideKeys=True` : 구간 밖 기존 키 보존.
- `sparseAnimCurveBake=False` : dense 키(프레임마다).

---

## 4. UI 설계 — `_build_bake_tab()` (main_window.py)

다른 탭과 동일 패턴(QWidget 반환, 시그널 연결, 공유 `self.log` 사용).

### 레이아웃
```
┌ Bake ─────────────────────────────────────────────────┐
│ [Bake List]                                           │  ← 재사용 위젯 JUN_mod_tsl_qt_v01
│ Select Objects                                        │     (Select/Add/Del/Up/Down/Sort 내장)
│ ┌ QListWidget ┐                                       │
│ │  ctrl objs  │                                       │
│ └─────────────┘                                       │
│ Range  (•) Current timeline   ( ) Custom range        │  ← 라디오 2택 (기본 (1))
│ Start [        ]   End [        ]                      │  ← Custom 일 때만 활성
│ Channels  [v] Translate  [v] Rotate  [ ] Scale        │  ← (선택) 기본 T·R
│ [v] Keep constraints (insert blend)                   │  ← 기본 ON → dic=False
│ [v] Simulation                                        │  ← (선택) 기본 on
│ [ Bake List ]                                         │
└───────────────────────────────────────────────────────┘
```

### 위젯
- **`self.bake_tsl`** = `JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Bake List",
  select_label="Select Objects", log_callback=self.log)`.
  Copy Key / Mirror Key 탭과 동일한 재사용 위젯. **베이크 대상은 이 리스트의 항목**
  (`self.bake_tsl.get_all_items()`)이며, 현재 씬 선택이 아니다. Select/Add/Del/Up/Down/Sort,
  "Number: N" 카운트, 항목 클릭 시 씬 선택은 위젯이 내장.
- `self.bake_range_grp` (`QButtonGroup`) + `self.rb_bake_timeline` / `self.rb_bake_custom`.
  - **기본: `rb_bake_timeline.setChecked(True)`** (요구 = 1번 기본 체크).
- `self.le_bake_start` / `self.le_bake_end` (`QLineEdit` + `QIntValidator(-1000000,1000000)`).
  - 빌드 시 현재 playback 범위로 초기값 채움(다른 탭과 동일 관례).
  - 초기 상태는 timeline 모드이므로 **비활성**으로 시작(`_bake_update_range_mode` 가 토글).
- 채널 체크박스 `self.cb_bake_t/r/s` — 기본 T·R on, S off.
- **`self.cb_bake_keep_con`** (`QCheckBox "Keep constraints (insert blend)"`) — **기본 setChecked(True)**.
  체크 = 컨스트레인트 유지(`disable_implicit=False`), 해제 = bake down(`True`).
- `self.cb_bake_sim` (`QCheckBox "Simulation"`) — 기본 on.
- `self.btn_bake` (`QPushButton "Bake List"`).

### 라디오 동작 (요구 1·2)
```python
def _bake_update_range_mode(self, *args):
    custom = self.rb_bake_custom.isChecked()
    self.le_bake_start.setEnabled(custom)
    self.le_bake_end.setEnabled(custom)
```
- **Current timeline**: Start/End 비활성. 베이크 시 `playbackOptions(min/maxTime)` 로 구간 결정.
- **Custom range**: Start/End 활성. 베이크 시 두 `QLineEdit` 값을 사용.

### 구간 해석 헬퍼
```python
def _bake_resolve_range(self):
    """라디오에 따라 (start, end) 결정. 실패 시 None."""
    if self.rb_bake_timeline.isChecked():
        start = int(cmds.playbackOptions(q=True, minTime=True))
        end = int(cmds.playbackOptions(q=True, maxTime=True))
        return (start, end)

    s_txt = self.le_bake_start.text().strip()
    e_txt = self.le_bake_end.text().strip()
    if s_txt == "" or e_txt == "":
        self.log("[Warning] Enter Start / End.")
        return None
    start, end = int(s_txt), int(e_txt)
    if start > end:
        self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
        return None
    return (start, end)
```

### 핸들러
```python
def on_bake(self):
    objs = self.bake_tsl.get_all_items()          # 리스트업된 항목만 (씬 선택 아님)
    if not objs:
        self.log("[Warning] Add controllers to the Bake List first.")
        return

    rng = self._bake_resolve_range()
    if rng is None:
        return
    start, end = rng

    channels = []
    if self.cb_bake_t.isChecked():
        channels += ["tx", "ty", "tz"]
    if self.cb_bake_r.isChecked():
        channels += ["rx", "ry", "rz"]
    if self.cb_bake_s.isChecked():
        channels += ["sx", "sy", "sz"]
    if not channels:
        self.log("[Warning] Enable at least one channel group.")
        return

    count, msg = BakeManager.bake(
        objs, start, end, channels=channels,
        simulation=self.cb_bake_sim.isChecked(),
        disable_implicit=not self.cb_bake_keep_con.isChecked(),  # 체크=유지 -> False
    )
    self.log(msg)
```

### 시그널
- `self.rb_bake_custom.toggled.connect(self._bake_update_range_mode)` (또는 grp.buttonToggled)
- `self.btn_bake.clicked.connect(self.on_bake)`
- 빌드 끝에서 `self._bake_update_range_mode()` 1회 호출(초기 활성 상태 동기화).

### 탭 등록 / import
- `_build_ui()` 의 탭 추가부에:
  `self.tabs.addTab(self._build_bake_tab(), "Bake")`
- 상단 import: `from tools.A00110_animTool.app.core import BakeManager`
  (`JUN_mod_tsl_qt` 는 이미 import 되어 있음)
- `core/__init__.py` 에 `BakeManager` export 추가(import + `__all__`).

---

## 5. Maya 2023 호환성 — **정상 동작(폴백 불필요)**

FKIK 진단과 동일. 신규 코드가 쓰는 모든 요소가 Maya 2023(Python 3.9)에서 지원된다.

| 요소 | 2023 | 비고 |
|------|------|------|
| `cmds.bakeResults(simulation/time/sampleBy/attribute/disableImplicitControl/preserveOutsideKeys/sparseAnimCurveBake)` | ✅ | C++ 베이커, 전 플래그 지원 |
| `cmds.refresh(suspend=...)` | ✅ | 뷰포트 억제 |
| `cmds.playbackOptions(q, minTime/maxTime)` | ✅ | 타임라인 구간 |
| `cmds.currentTime` / `undoInfo` / `ls` | ✅ | |
| Qt: `QButtonGroup`/`QRadioButton`/`QLineEdit`/`QIntValidator`/`QCheckBox` | ✅ | 기존 탭에서 이미 사용 중 |
| 재사용 위젯 `JUN_mod_tsl_qt_v01` (Framework.qt) | ✅ | Copy/Mirror 탭에서 이미 사용 중 |
| Python 3.9 | ✅ | `match/case`·`X|Y` 유니온 미사용 |

`[[maya-2023-compat]]`(native sin/cos 노드 없음)은 DG 노드 그래프 이슈로 본 작업과 무관.

### 견고성(버전 무관, 필수)
- `refresh(suspend=True)` 는 **반드시** `finally` 에서 해제(예외 시 뷰포트 멈춤 방지).
- `currentTime` 원위치 복원, 전체를 단일 undo 청크로.
- 잠금/연결 채널이 있어도 `bakeResults` 는 가능한 채널만 굽고 진행(전체 중단 없음).

---

## 6. 동작 규칙 / 주의

- **대상 = Bake List 위젯 항목**(`self.bake_tsl.get_all_items()`). **씬 선택이 아니라
  리스트업된 노드만** 베이크한다. Copy/Mirror 탭과 동일한 `JUN_mod_tsl_qt_v01` 사용
  (Select Objects 로 현재 선택을 리스트에 채우고, Add/Del/Up/Down/Sort 로 관리).
- **Current timeline**(기본) = `playbackOptions` 의 min/maxTime(타임라인 플레이백 슬라이더 범위).
  "지금 보고 있는 구간"의 정의를 이 값으로 고정(애니메이션 전체 범위가 아니라 재생 범위).
  Custom 모드에서만 Start/End `QLineEdit` 활성.
- **scale 기본 제외**: FKIK 매칭 의미와 동일하게 T·R 이 기본. Scale 은 체크 시에만.
- **Keep constraints(기본 ON) → `disableImplicitControl=False`**: 베이크 대상이 컨스트레인트로
  구동 중이면 Maya 가 `pairBlend` 를 삽입해 **컨스트레인트를 유지한 채 키와 공존**시킨다
  (`blendParent` 로 전환). 체크 해제 시 `True` → 구동을 끊고 키만 남기는 bake down.
  → 같은 채널이 "활성 컨스트레인트 + 베이크 키" 둘 다 갖게 되며 `blendParent1` 로 가중치를 조절한다.

---

## 7. 검증 (Verification)

Maya 2023(가능하면 최신도)에서 `tools.A00110_animTool.run(True)` 후 Bake 탭:
1. **대상 = 리스트** — Select Objects 로 리스트에 채운 노드만 베이크되고, 씬 선택만 하고 리스트가
   비어 있으면 경고(`Add controllers to the Bake List first.`). 리스트 ≠ 씬 선택임을 확인.
2. **라디오 동작** — **기본 Current timeline 체크**, Start/End 비활성·타임라인 범위로 베이크.
   Custom 선택 시 입력칸 활성·입력값으로 베이크. 잘못된 범위(빈값/Start>End) 경고.
3. **Keep constraints** — **기본 체크(유지)**: 컨스트레인트 구동 노드 베이크 후 컨스트레인트가
   남고 `blendParent1` 가 생기는지, `blendParent1` 토글로 키↔컨스트레인트 전환되는지 확인.
   체크 해제 시 구동이 끊기고(bake down) 키만 남는지 확인.
4. **정합성** — 베이크 전후 컨트롤러 월드 포즈가 프레임별로 동일(구동→키 변환 정확).
5. **속도** — 6000+프레임 × 50~100 컨트롤러에서 1회 호출로 완료, 체감 수 초~수십 초.
6. **구간 밖 키 보존**(`preserveOutsideKeys`), **Undo 1회 복원**, **현재 프레임 복원**, **뷰포트 정상**.
7. **채널 토글** — T만 / R만 / +Scale 조합이 의도대로 키 생성.
8. **엣지** — 리스트 빈 경우 경고, 1프레임 구간(start==end), 잠긴 채널 포함 시 진행.

---

## 8. 작업 순서(제안)

1. `app/core/bake_manager.py` 신규(3장, `disable_implicit` 파라미터 포함) + `core/__init__.py` export 추가.
2. `main_window.py` `_build_bake_tab()` — **Bake List 위젯 + 라디오(기본 timeline) + Custom 구간 +
   채널 + Keep constraints(기본 ON) + Simulation + Bake 버튼** + 핸들러/시그널(4장), 탭 등록·import.
3. `version.py` 01.04 → 01.05, 파일 헤더 `last Update date` 갱신.
4. 7장 검증(특히 Maya 2023, 라디오 두 모드, 리스트 대상, Keep constraints on/off).
5. **`docs/A00110_animTool.md` 갱신**:
   - 1장 개요: 탭 **5개**(Key Edit / Pose Key / Copy Key / Mirror Key / **Bake**)로 수정,
     "v01.05 — Bake 탭 신설" 노트 추가(FKIK 네이티브 베이커 이식).
   - 2장 폴더 구조: `core/bake_manager.py` 한 줄 추가.
   - 5장 UI: "5.5 Bake 탭" 신설(리스트/라디오/Custom/채널/Keep constraints/Simulation 설명).
   - 6장 사용 순서: "Bake" 절 추가(① 리스트 채우기 ② 구간 모드 ③ 옵션 ④ Bake).
   - 7장 동작 규칙: 대상=리스트, 구간=playback vs custom, Keep constraints(dic) 규칙, 단일 undo.
   - 8장 로그/문제 해결: 정상 로그 예시 + 경고(`Add controllers to the Bake List first.` 등) 추가.
   - 공유 로그창 설명의 "3개 탭/네 개의 탭" 표기를 **5개 탭**으로 일관 정리.

---

## 9. 리스크 / 롤백

- 변경이 **신규 파일 1 + 추가 메서드/탭**에 국한 → 기존 4개 탭 로직 무영향. 탭 등록 한 줄만
  빼면 비활성화 가능(롤백 용이).
- 리스크: (a) Keep constraints(기본 ON, `dic=False`)는 `pairBlend` 를 삽입하므로, 사용자가
  베이크 후 컨트롤러에 `blendParent1` 어트리뷰트가 생긴 것을 인지하지 못하면 "키가 안 먹는 것처럼"
  보일 수 있음(컨스트레인트 가중치가 우세할 때) → 문서·로그(`constraints kept`)로 명시.
  순수히 키만 남기려면 체크 해제(bake down). (b) "현재 구간" 정의(playback vs animation range)
  혼동 → playback(min/maxTime)으로 고정하고 문서에 명기. (c) 대상이 씬 선택이 아니라 **리스트**
  이므로, 선택만 하고 리스트가 비면 아무것도 안 굽힘 → 경고 메시지로 안내.
