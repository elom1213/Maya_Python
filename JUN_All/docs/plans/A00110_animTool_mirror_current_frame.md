# A00110_animTool — Mirror Key "현재 프레임만 미러(오토키)" 기능 계획서

## Context (배경 / 목적)

Mirror Key 탭은 지금 `[Start, End]` **구간**을 대상으로만 동작한다
(`Source keys` 시점 union 또는 `Bake` 정수 프레임 전수). 두 모드 모두
`MirrorKeyManager.mirror_keys` → `_mirror_one` 에서 **대상 채널에 무조건 `setKeyframe`** 한다.

요구: **"지금 프레임의 자세만" 미러하는 버튼**을 추가한다.

1. 버튼을 누르면 **현재 타임라인 프레임 1곳**의 포즈만 반대쪽으로 미러한다.
2. 키는 **알파벳 `s`(setKeyframe 전체 키) 방식이 아니라**, **auto keyframe 토글처럼**
   동작해야 한다 — 즉 **이미 키(애니메이션 커브)가 있는 채널에만** 현재 프레임에 키가 갱신되고,
   **키가 없던 채널/오브젝트는 키를 만들지 않고 포즈만** 미러된다.

> 왜 기존 구간 기능으로 안 되나: `Start=End=현재프레임 + Bake` 로 해도 `mirror_keys` 는
> **키가 없던 오브젝트에도 키를 새로 찍는다.** 요구의 핵심("키 없던 건 그대로 키 없이 미러")을
> 만족하지 못하므로 **별도 경로**가 필요하다.

---

## 1. 현재 동작 분석 (`mirror_key_manager.py`)

- `mirror_keys(pairs, start, end, axis, do_t, do_r, time_mode)` — 구간 진입점.
- `_mirror_one(...)` — 시점 목록 `times` 마다
  `local = (refl · srcWorld · refl) · tgtParentInverse` 를 구해 `values` dict 생성 후,
  대상 attr 마다 **`cmds.setKeyframe(...)`** 로 기록(무조건 키 생성).
- `_collect_times` — `bake` = 정수 프레임 전수, `source_keys` = 소스 키 시점.
- `_reflection_matrix`, `_is_settable`(잠금 제외), `RO_ENUM`(타겟 rotateOrder 재분해) 등 헬퍼 존재.

**재사용 포인트**: 미러 수학(반사 행렬 → 타겟 로컬 분해)과 페어링(`resolve_pairs`)은 그대로 쓴다.
**바꿀 점**: "시점 = 현재 프레임 1개", "키잉 = autoKeyframe 규칙(채널별 조건부)".

---

## 2. 핵심 설계 — autoKeyframe 동작의 명시적 재현

Maya 의 Auto Keyframe 규칙: **이미 time 애니메이션 커브가 있는 채널에 한해**, 값이 바뀌면
현재 프레임에 키를 갱신한다(없던 채널엔 안 찍음). 이를 전역 `autoKeyframe` 상태에 의존하지 않고
**채널 단위로 명시 구현**한다(결정적·안전).

채널 `attr` 마다:
1. **time 애니메이션 커브 존재 여부 판정**
   ```python
   curves = cmds.keyframe(tgt, attribute=attr, query=True, name=True) or []
   time_curves = [c for c in curves if cmds.nodeType(c).startswith("animCurveT")]
   has_anim = bool(time_curves)
   ```
   - `animCurveT*`(TL/TA/TU/TT) = **시간 기반** 커브만 인정. set-driven-key 의 `animCurveU*` 는 제외
     (autoKeyframe 도 time 커브만 대상).
2. **값 변경 여부**(autoKeyframe 의 "값이 바뀌면" 재현)
   ```python
   old = cmds.getAttr(tgt + "." + attr)
   changed = abs(old - value) > TOL          # TOL = 1e-6 정도
   ```
3. **적용**
   - `has_anim` 이고 `changed` → `cmds.setKeyframe(tgt, attribute=attr, time=cur, value=value)`
     (현재 프레임에 키 갱신/삽입. 값도 함께 설정됨).
   - `has_anim` 인데 `changed` 아님 → no-op(이미 같은 값).
   - `has_anim` 아님(키 없던 채널) → `cmds.setAttr(tgt + "." + attr, value)`
     (**포즈만 미러, 키 생성 안 함**).
   - 잠금/연결 등으로 실패하면 해당 채널 skip(try/except), 전체는 계속.

> 결과: 키 있던 채널은 현재 프레임 1곳에 오토키처럼 갱신, 키 없던 채널은 값만 미러 → 요구 그대로.
> **판정 단위는 채널(attr)** 이다. 예: 타겟이 tx 만 키가 있으면 tx 에만 키가 찍히고 rx 는 포즈만.
> (autoKeyframe 와 동일. "오브젝트 단위"가 아님 — 확인 필요시 옵션화 가능.)

---

## 3. Core 변경 — `mirror_key_manager.py`

### 3-1. (리팩토링) 미러 값 계산 공통화
`_mirror_one` 의 값 계산부를 추출해 구간/현재프레임이 공유한다.

```python
@staticmethod
def _mirrored_values(src, tgt, t, refl, do_t, do_r):
    """시점 t 에서 src 를 미러해 타겟 로컬 TRS(dict: attr->value) 반환."""
    ms = om.MMatrix(cmds.getAttr(src + ".worldMatrix[0]", time=t))
    mpi = om.MMatrix(cmds.getAttr(tgt + ".parentInverseMatrix[0]", time=t))
    tm = om.MTransformationMatrix((refl * ms * refl) * mpi)

    values = {}
    if do_t:
        tr = tm.translation(om.MSpace.kTransform)
        values["translateX"] = tr.x
        values["translateY"] = tr.y
        values["translateZ"] = tr.z
    if do_r:
        ro = cmds.getAttr(tgt + ".rotateOrder")
        eul = tm.rotation(asQuaternion=True).asEulerRotation()
        eul.reorderIt(MirrorKeyManager.RO_ENUM[ro])
        values["rotateX"] = math.degrees(eul.x)
        values["rotateY"] = math.degrees(eul.y)
        values["rotateZ"] = math.degrees(eul.z)
    return values
```
(기존 `_mirror_one` 도 이 헬퍼를 쓰도록 정리 → 중복 제거. 동작 동일.)

### 3-2. (신규) 현재 프레임 미러 (오토키)
> 구현은 `per_object` 파라미터를 포함한다(아래 시그니처는 초안이며, 실제로는
> `..., tol=1e-6, per_object=False` 로 per-channel/per-object 분기를 받는다).
```python
@staticmethod
def mirror_current_frame(pairs, mirror_axis="x",
                         do_translate=True, do_rotate=True, tol=1e-6,
                         per_object=False):
    """
    현재 프레임의 포즈만 각 (src, tgt) 로 미러한다.

    키잉은 autoKeyframe 규칙을 재현:
      - 대상 채널에 time 애니메이션 커브가 있고 값이 바뀌면 -> 현재 프레임에 setKeyframe.
      - 커브가 없던 채널 -> setAttr 로 포즈만(키 생성 안 함).
    반환: (처리한 페어 수, 메시지)
    """
    if not pairs:
        return (0, "[Warning] No pairs to mirror.")
    if not do_translate and not do_rotate:
        return (0, "[Warning] Enable Translate and/or Rotate.")

    refl = MirrorKeyManager._reflection_matrix(mirror_axis)
    cur = cmds.currentTime(q=True)

    attrs = []
    if do_translate:
        attrs += [a for _, a in MirrorKeyManager.T_AXES]
    if do_rotate:
        attrs += [a for _, a in MirrorKeyManager.R_AXES]

    done = skipped = keyed = posed = 0

    cmds.undoInfo(openChunk=True)
    try:
        for src, tgt in pairs:
            settable = [a for a in attrs if MirrorKeyManager._is_settable(tgt, a)]
            if not settable:
                skipped += 1
                continue

            values = MirrorKeyManager._mirrored_values(
                src, tgt, cur, refl, do_translate, do_rotate)

            touched = False
            for a in settable:
                v = values[a]
                full = tgt + "." + a
                try:
                    curves = cmds.keyframe(tgt, attribute=a, query=True, name=True) or []
                    has_anim = any(cmds.nodeType(c).startswith("animCurveT") for c in curves)
                    if has_anim:
                        if abs(cmds.getAttr(full) - v) > tol:
                            cmds.setKeyframe(tgt, attribute=a, time=cur, value=v)
                            keyed += 1
                            touched = True
                    else:
                        cmds.setAttr(full, v)
                        posed += 1
                        touched = True
                except Exception:
                    pass

            if touched:
                done += 1
            else:
                skipped += 1
    finally:
        cmds.undoInfo(closeChunk=True)

    msg = "{0} pair(s) mirrored at frame {1} (axis: {2}; keyed {3}, posed {4}).".format(
        done, int(cur), mirror_axis.upper(), keyed, posed)
    if skipped:
        msg += " {0} skipped.".format(skipped)
    return (done, msg)
```

- 전역 `autoKeyframe` 상태를 건드리지 않으므로(켜고 끄지 않음) 안전·결정적.
- `om`/`math` 는 이미 모듈 상단 import. 단일 `undoInfo` 청크.

---

## 4. UI 변경 — `main_window.py` (Mirror Key 탭)

### 4-1. 버튼 추가
기존 `Mirror Selected`(`btn_mirror`) 아래에 한 줄 추가.
```python
self.btn_mirror_current = QPushButton("Mirror Current Frame")
tab_layout.addWidget(self.btn_mirror_current)
...
self.btn_mirror_current.clicked.connect(self.on_mirror_current_frame)
```
- Start/End/Time 컨트롤은 이 버튼에 **사용되지 않음**(현재 프레임 고정). 라벨/툴팁로 명시.

### 4-2. 페어링 공통화(리팩토링)
`on_mirror_key` 의 Auto/Manual 페어 해석부를 헬퍼로 추출해 두 핸들러가 공유.
```python
def _mir_resolve_pairs(self):
    """현재 모드(Auto/Manual)로 (src,tgt) 페어 리스트 반환. 실패 시 None(경고 로그)."""
    if self.rb_mir_manual.isChecked():
        base = self.mir_base_tsl.get_all_items()
        tgt = self.mir_tgt_tsl.get_all_items()
        if not base or not tgt:
            self.log("[Warning] Fill both Source and Target lists.")
            return None
        if len(base) != len(tgt):
            self.log(f"[Warning] Source({len(base)}) / Target({len(tgt)}) count mismatch.")
            return None
        return list(zip(base, tgt))

    sel = cmds.ls(sl=True) or []
    if not sel:
        self.log("[Warning] Select source controllers first.")
        return None
    token_pairs = self._mir_token_pairs() or list(MirrorKeyManager.DEFAULT_TOKEN_PAIRS)
    pairs, unpaired, center = MirrorKeyManager.resolve_pairs(sel, token_pairs)
    if unpaired:
        self.log(f"[Warning] {len(unpaired)} unpaired (skipped): {', '.join(unpaired)}")
    if not pairs:
        self.log("[Warning] No pairs resolved.")
        return None
    return pairs
```
- 기존 `on_mirror_key` 도 이 헬퍼를 쓰도록 정리(동작 동일).

### 4-3. 신규 핸들러
```python
def on_mirror_current_frame(self):
    do_t = self.cb_mir_translate.isChecked()
    do_r = self.cb_mir_rotate.isChecked()
    if not do_t and not do_r:
        self.log("[Warning] Enable Translate and/or Rotate.")
        return

    pairs = self._mir_resolve_pairs()
    if pairs is None:
        return

    count, msg = MirrorKeyManager.mirror_current_frame(
        pairs, mirror_axis=self._mir_axis(),
        do_translate=do_t, do_rotate=do_r)
    self.log(msg)
```
- Mirror Axis / Channels 토글은 기존 것을 공유. Start/End/Time 은 미사용.

---

## 5. Maya 2023 호환성 — **정상 동작(폴백 불필요)**

| 사용 요소 | 2023 | 비고 |
|-----------|------|------|
| `cmds.keyframe(query, name=True)` / `nodeType` | ✅ | time 커브(animCurveT*) 판정 |
| `cmds.getAttr` / `setAttr` / `setKeyframe` / `currentTime` | ✅ | |
| `maya.api.OpenMaya` `MMatrix`/`MTransformationMatrix`/`MEulerRotation` | ✅ | 기존 미러와 동일 |
| `cmds.undoInfo(open/closeChunk)` | ✅ | 단일 Undo |
| Qt `QPushButton` | ✅ | 기존 사용 중 |
| Python 3.9 | ✅ | `match/case`·`X|Y` 유니온 미사용 |

`[[maya-2023-compat]]`(native sin/cos 노드 없음)은 DG 노드 그래프 이슈로 본 작업과 무관.

---

## 6. 검증 (Verification)

Maya 2023 에서 `tools.A00110_animTool.run(True)` → Mirror Key 탭:
1. **키 있는 채널** — 타겟에 기존 키가 있는 컨트롤을 미러 → **현재 프레임에만** 키가 갱신되고
   다른 프레임 키는 보존. 값이 반대쪽 포즈와 일치.
2. **키 없는 채널/오브젝트** — 키가 전혀 없던 컨트롤을 미러 → **키 생성 0**, 포즈만 반대쪽으로 적용.
3. **혼합** — tx 만 키가 있는 타겟: tx 는 키 갱신, rx 는 포즈만(키 없음) 확인.
4. **값 미변경** — 이미 미러 결과와 같은 값이면 키를 새로 안 찍는지(autoKeyframe 와 동일).
5. **Auto/Manual 모드, Mirror Axis(X/Y/Z), Channels(T/R)** 조합 동작.
6. **센터(self-mirror)** 컨트롤: 현재 프레임 제자리 좌우 반전. 키 유무 규칙 동일 적용.
7. **Undo** 한 번으로 (키+setAttr) 전체 복원. 잠금/연결 채널 skip + 로그.
8. **회귀** — 기존 `Mirror Selected`(구간) 동작 불변(공통 헬퍼 리팩토링 후).

---

## 7. 작업 순서(제안)

1. `mirror_key_manager.py`: `_mirrored_values` 추출(+`_mirror_one` 정리) → `mirror_current_frame` 추가.
2. `main_window.py`: `_mir_resolve_pairs` 추출(+`on_mirror_key` 정리) → `btn_mirror_current` +
   `on_mirror_current_frame` 추가.
3. `version.py` 01.05 → 01.06, 헤더 `last Update date` 갱신.
4. 6장 검증(특히 키 유무별 동작, 값 미변경, 센터).
5. `docs/A00110_animTool.md` 갱신:
   - 5.4 Mirror Key UI 에 **Mirror Current Frame** 버튼 설명(현재 프레임/오토키 규칙, Start·End·Time 미사용).
   - 6장 사용 순서에 "현재 프레임만 미러" 절 추가.
   - 7장 동작 규칙에 autoKeyframe 재현(채널별 time 커브 판정, 값 변경 시 키, 없으면 setAttr) 규칙 추가.
   - 8장 로그 예시(`... at frame N (axis: X; keyed K, posed P).`) + 관련 경고 추가.

---

## 8. 결정 사항 (확정)

- **판정 단위 옵션화 확정**: `mirror_current_frame(..., per_object=False)` 파라미터 + UI 라디오
  **Keying (•) Per-channel (auto-key) / ( ) Per-object** (Current Frame 그룹, 기본 Per-channel).
  - Per-channel = autoKeyframe 동일(채널별). Per-object = 대상 채널 중 하나라도 애니가 있으면 선택 채널 전부 키.
- **값 변경 임계값 `tol=1e-6` 확정**(per-channel 모드 기본값).
- **time 커브 판정**: `animCurveT*` 만 인정. set-driven-key(`animCurveU*`)만 걸린 채널은 "키 없음" 취급.
- 변경은 **메서드/버튼 추가 + 내부 리팩토링**에 국한 → 기존 구간 미러/타 탭 무영향(롤백 용이).
- **time 커브 판정**: `animCurveT*` 만 인정하므로 set-driven-key 만 걸린 채널은 "키 없음"으로 보고
  `setAttr`(드리븐 입력이 있으면 setAttr 실패 → skip). 의도와 맞는지 확인.
- 변경은 **메서드/버튼 추가 + 내부 리팩토링**에 국한 → 기존 구간 미러/타 탭 무영향(롤백 용이).
