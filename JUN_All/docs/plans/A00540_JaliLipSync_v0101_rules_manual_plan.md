# A00540_JaliLipSync v01.01 — 규칙(json) 역할표 · Auto / Manual 타겟 · 스케일 json 기본값 + A0020 리그 JaLi 기본값 이동

> **작성** 2026-10-22 · 상태: **S1~S7 완료 (2026-10-22) — S8 사용자 마야 GUI 확인 대기** · 대상 Maya 2024 · 이 문서만 보고 작업할 수 있게 쓴다.
> 결과: `tests/run_all.py` 매핑 21 · 코어 22 · UI 18 · 실제 파일 18 전부 통과. 출력 세기 규칙(`output_max` 10 등)은 **만들지 않는다** — 사용자가 리그에서 직접(2026-10-22 결정, C8 보강).
> 배경: JUN_JALI `docs/0090`(A0020 슬라이더 리그) 의 후속 S6. 새 리그의 입력 허브 `DUMMY_IN_*` 에 VisemeNet 키를 걸려면 툴이 `CNT_PHONEMES` 이름과 angela 단위(scale 10 · Jaw/Lip 0~15) 에 묶여 있는 것을 풀어야 한다.
> 관련: `docs/A00540_JaliLipSync.md`(사용 안내) · JUN_JALI `docs/0090_jali_slider_ctl_plan.md` · `docs/0120_jali_dummy_out_attrs_guide.md` · 메모리 `wip-a00540-jalilipsync` · `wip-jali-slider-ctl`

---

## 0. 확정 사항 (2026-10-22 사용자 제안 + 평가에서 합의)

| # | 항목 | 확정 |
|---|------|------|
| C1 | 새 규칙 json `jali_slider_dummy_in.json` — `DUMMY_IN_PHONEMES` · `DUMMY_IN_COARTIC` · `DUMMY_IN_JALI` 를 Auto 로 찾아 키. **viseme scale 1 · JaLi scale 1** (txt 의 1.0 = 슬라이더 끝) | 사용자 |
| C2 | 툴에 **JaLi scale** 수치 추가. 규칙마다 기본값이 다르고(angela 10 · 새 규칙 1) 사용자가 바꿀 수 있다 | 사용자 |
| C3 | Target 을 **Auto / Manual** 로 나눈다. Auto = 지금처럼 자동 탐색. Manual = 역할 3개(Phonemes · Coartic · JaLi) 노드를 사용자가 직접 지정, **하나라도 채우면 그것만 키**, 빈 역할은 건너뜀 | 사용자 |
| C4 | 자동 탐색 표식 · 노드 이름은 코드가 아니라 **json 의 역할표 `nodes`** 가 든다. Auto 와 Manual 이 같은 json 을 쓴다 (Manual = 역할표의 노드 이름을 사용자가 고른 노드로 치환) | 평가 §1 |
| C5 | Viseme scale · JaLi scale · Fixed Jaw/Lip 의 **기본값 · 범위는 json 이 공급**하고, Mapping 콤보를 바꾸면 스핀박스가 그 값으로 리셋된다. 그 뒤 사용자가 바꾸는 것은 허용 | 평가 §2 · §3 |
| C6 | Apply 전 **단위 검사**: 어트리뷰트에 max 가 있고 적용 scale 이 max 보다 크면 `[WARN]` 한 줄(막지는 않음) | 평가 §5 |
| C7 | 리그(A0020): 2D 박스 컨트롤러 `CNT_JaLi` 의 기본 위치를 **0, 0** 으로, `DUMMY_IN_JALI.Jaw/Lip` 의 기본값을 **0.6** 으로 옮긴다 (출력 기본 9 유지). 이름은 그대로 `CNT_JaLi` | 평가 끝 |
| C8 | 매핑 json 의 `targets[].scale` 은 **하위 호환으로 남기되** 새 json 에서는 쓰지 않는다 (최상위 `viseme_scale` · `jali.scale` 이 기본) | 이 계획 |
| C9 | A00550 PoseMapper 의 Solo / Capture 가 `DUMMY_OUT_*` 을 Source 로 못 쓰는 문제는 **이번 범위 밖** (§9) | 이 계획 |
| C10 | 출력 세기(`DUMMY_OUT_*` 최종값 — `output_max` · `global_scale`)는 **규칙에 두지 않고** 사용자가 마야에서 직접 조절. Viseme scale 1 = txt 1.0 이 슬라이더 끝 | 사용자 (2026-10-22) |

---

## 1. 지금 코드 (2026-10-22 읽음) — 바꿀 자리

| 파일 | 지금 | 바꿀 것 |
|------|------|---------|
| `app/core/scene.py` | `RIG_MARKER = "CNT_PHONEMES"` 고정, `find_rigs()` 가 그 이름의 트랜스폼이 있는 네임스페이스 목록 | `find_rigs(marker)` — 표식을 인자로 |
| `app/core/mapping.py` | `load_mapping()` 이 `model_columns` · `targets[attr, from, combine, scale, role]` · `clamp` 검사 | `nodes` · `viseme_scale` · `jali{scale, range, fixed_default}` 읽기 · 검사, 타겟의 역할을 노드로 판정 |
| `app/core/keyer.py` | `target_attrs/controls/check_targets/apply/remove` 가 `namespace + t["attr"]`. `sample()` 은 `viseme_scale` 이 있으면 `role != "jali"` 타겟의 scale 을 덮어쓰고 jali 타겟은 json scale | 타겟 해석을 한 곳(`resolve_targets`)으로 모으고 `node_map`(Manual) · `jali_scale` 추가 |
| `app/ui/main_window.py` | Target: `cmb_rig` + Refresh + `cmb_mapping`. Options: `ds_scale`(0~12, 10) · JaLi `rb_jali_data/fixed` + `ds_jaw/ds_lip`(0~15, 9) | Target 에 Auto/Manual 라디오 + Manual 3칸, Options 에 JaLi scale, 매핑 변경 시 리셋 |
| `app/mappings/angela_jali_visemenet.json` | `targets[].scale 10`, `role: "jali"` | `nodes` · `viseme_scale` · `jali` 블록 추가 (값은 그대로) |
| `app/config/version.py` | 01.00 | 01.01 |
| `docs/A00540_JaliLipSync.md` | §2 사용 · §4 json 형식 | §2 Target Auto/Manual · Options JaLi scale, §4 형식 v2 |
| JUN_JALI `examples/build_jali_slider_ctl.py` | `CNT_JaLi` 기본 (0.6, 0.6), `DUMMY_IN_JALI` dv 0 | C7 |

`tests/` 폴더는 없다(v01.00 검증은 임시 스크립트였다). 이번에 `tests/` 를 만든다(§7).

---

## 2. 매핑 json 형식 v2

```json
{
  "name": "jali_slider_dummy_in",
  "description": "VisemeNet 22 columns -> A0020_jali_slider_ctl.ma input hubs (0-1). txt 1.0 = slider top.",
  "model_columns": ["Jaw", "Lip", "Ah", "Aa", "Eh", "Ee", "Ih", "Oh", "Uh", "U", "Eu", "Schwa", "R", "S",
                    "ShChZh", "Th", "JY", "LNTD", "GK", "MBP", "FV", "W"],
  "clamp": [0.0, 1.0],
  "nodes": {"phonemes": "DUMMY_IN_PHONEMES", "coartic": "DUMMY_IN_COARTIC", "jali": "DUMMY_IN_JALI"},
  "viseme_scale": 1.0,
  "jali": {"scale": 1.0, "range": [0.0, 1.0], "fixed_default": [0.6, 0.6]},
  "targets": [
    {"attr": "DUMMY_IN_JALI.Jaw",          "from": ["Jaw"]},
    {"attr": "DUMMY_IN_JALI.Lip",          "from": ["Lip"]},
    {"attr": "DUMMY_IN_PHONEMES.AAA",      "from": ["Aa"]},
    {"attr": "DUMMY_IN_PHONEMES.Eh",       "from": ["Eh"]},
    {"attr": "DUMMY_IN_PHONEMES.AHH",      "from": ["Ah"]},
    {"attr": "DUMMY_IN_PHONEMES.OHH",      "from": ["Oh", "Uh"], "combine": "max"},
    {"attr": "DUMMY_IN_PHONEMES.UUU",      "from": ["U"]},
    {"attr": "DUMMY_IN_PHONEMES.IEE",      "from": ["Ee", "Ih"], "combine": "max"},
    {"attr": "DUMMY_IN_PHONEMES.RRR",      "from": ["R"]},
    {"attr": "DUMMY_IN_PHONEMES.WWW",      "from": ["U"]},
    {"attr": "DUMMY_IN_PHONEMES.SSS",      "from": ["S"]},
    {"attr": "DUMMY_IN_PHONEMES.FFF",      "from": ["FV"]},
    {"attr": "DUMMY_IN_PHONEMES.TTH",      "from": ["Th"]},
    {"attr": "DUMMY_IN_PHONEMES.MBP",      "from": ["MBP"]},
    {"attr": "DUMMY_IN_PHONEMES.SSH",      "from": ["ShChZh"]},
    {"attr": "DUMMY_IN_PHONEMES.Schwa",    "from": ["Schwa"]},
    {"attr": "DUMMY_IN_PHONEMES.GK",       "from": ["GK"]},
    {"attr": "DUMMY_IN_PHONEMES.LNTD",     "from": ["LNTD"]},
    {"attr": "DUMMY_IN_COARTIC.LNTD",      "from": ["LNTD"]},
    {"attr": "DUMMY_IN_COARTIC.GK",        "from": ["GK"]},
    {"attr": "DUMMY_IN_COARTIC.MMM",       "from": ["MBP"]},
    {"attr": "DUMMY_IN_COARTIC.FFF",       "from": ["FV"]},
    {"attr": "DUMMY_IN_COARTIC.WA_PEDAL",  "from": ["W"]}
  ]
}
```

- 타겟 열 대응은 `angela_jali_visemenet.json` 과 **동일**(원본 VisemeNet 매핑: `WWW` ← `U`, `YA_PEDAL` · `Eu` · `JY` 안 씀).
- **역할 판정**: 타겟의 노드 이름이 `nodes` 의 어느 역할 값과 같은지로 정한다. `role: "jali"` 가 타겟에 명시돼 있으면 그것이 우선(하위 호환).
- `angela_jali_visemenet.json` 에는 다음 세 줄을 더한다. 타겟은 그대로 둔다.
  ```json
  "nodes": {"phonemes": "CNT_PHONEMES", "coartic": "CNT_COARTIC", "jali": "CNT_JaLi"},
  "viseme_scale": 10.0,
  "jali": {"scale": 10.0, "range": [0.0, 15.0], "fixed_default": [9.0, 9.0]},
  ```
- `load_mapping()` 검사 추가 (틀리면 `ValueError`, 영어):
  - `nodes` 는 dict 이고 키는 `phonemes` `coartic` `jali` 중 하나 이상 (빈 dict 금지). 값은 노드 이름(점 없음).
  - 모든 타겟의 노드 이름이 `nodes` 값 중 하나여야 한다 → 아니면 `"{attr} uses node {node} not listed in nodes"`.
  - `viseme_scale` 없으면 **타겟들의 `scale` 중 jali 가 아닌 첫 값**, 그것도 없으면 1.0. `jali.scale` 없으면 jali 타겟의 `scale`, 없으면 1.0. `jali.range` 기본 `[0, 15]`, `fixed_default` 기본 `[9, 9]` (angela 호환).
  - 읽은 뒤 `data["nodes"]` · `data["viseme_scale"]` · `data["jali"]` 가 항상 채워져 있게 한다(이후 코드는 `.get` 안 씀).

---

## 3. 코어 변경

### 3.1 `scene.py`

```python
def find_rigs(marker):
    """marker 이름의 트랜스폼이 있는 네임스페이스 목록 ("" = 루트, "angela:" 처럼 콜론까지)."""
```
- `RIG_MARKER` 상수는 지운다. 호출부(UI)가 `mapping["nodes"]["phonemes"]` 를 넘긴다. `phonemes` 가 없는 json 이면 `nodes` 의 첫 값.

### 3.2 `keyer.py` — 타겟 해석을 한 곳으로

```python
def resolve_targets(mapping, namespace="", node_map=None):
    """키를 걸 타겟 목록 [{attr(최종 plug), role, from, combine, scale}].

    namespace : Auto 모드 — 모든 노드 앞에 붙인다 ("angela:").
    node_map  : Manual 모드 — {"phonemes": "pSphere1", "coartic": None, "jali": "ctl"}.
                역할의 노드가 None 이면 그 역할 타겟은 목록에서 **뺀다**(건너뜀). namespace 는 무시.
    """
```
- 역할 판정: `role = t.get("role") or 노드 이름으로 nodes 역순 조회`. `nodes` 에 없는 노드는 `load_mapping` 이 이미 막는다.
- `target_attrs` · `controls` · `check_targets` · `apply` · `remove` 는 전부 `resolve_targets()` 결과를 쓴다. 시그니처:
  - `check_targets(mapping, namespace="", node_map=None)`
  - `sample(data, mapping, fps, viseme_scale=None, jali_scale=None, targets=None)` — `targets` 가 주어지면 그것을 쓴다. scale 결정: jali 역할이면 `jali_scale`(None 이면 `mapping["jali"]["scale"]`), 아니면 `viseme_scale`(None 이면 `mapping["viseme_scale"]`). **타겟의 `scale` 은 더 이상 안 본다**(C8 — 기본값은 §2 의 `load_mapping` 이 이미 흡수했다).
  - `apply(data, mapping, namespace="", start=1, viseme_scale=None, jali_scale=None, jali_fixed=None, node_map=None, progress=None)` — 반환 dict 에 `skipped`(건너뛴 역할 목록) 추가.
  - `remove(mapping, namespace="", start=None, end=None, node_map=None)` · `controls(mapping, namespace="", node_map=None)`.
- 건너뛴 역할이 있어도 나머지는 건다. 해석된 타겟이 **0개면** `KeyingError("No target node - fill at least one of Phonemes / Coartic / JaLi")`.

### 3.3 단위 검사 (C6)

```python
def scale_warnings(targets, viseme_scale, jali_scale):
    """[(attr, scale, attr_max)] — attributeQuery -maxExists 인 어트리뷰트 중 scale > max 인 것."""
```
- `apply` 가 아니라 **UI 가 Apply 직전에** 불러 `[WARN] {attr}: scale {scale:g} exceeds the attribute maximum {max:g}` 로 찍는다. 막지 않는다.

---

## 4. UI 변경 (`main_window.py`)

### 4.1 Target 그룹

```
Target
  ( ) Auto   Rig [ angela:        ▾ ] [Refresh]
  ( ) Manual Phonemes [ DUMMY_IN_PHONEMES   ] [<< Sel] [x]
             Coartic  [                     ] [<< Sel] [x]
             JaLi     [ DUMMY_IN_JALI       ] [<< Sel] [x]
  Mapping [ jali_slider_dummy_in ▾ ]
```
- 라디오 `rb_auto`(기본) / `rb_manual`. Auto 면 Rig 행만, Manual 이면 3칸만 활성화(다른 쪽은 `setEnabled(False)`).
- `<< Sel` = 선택한 첫 트랜스폼 이름(네임스페이스 포함 전체 이름)을 넣는다. 선택이 없으면 `[WARN] Select a node first.`. `x` = 비우기. 칸은 `QLineEdit` 이라 손으로 쳐도 된다.
- 도움말: Rig 콤보 툴팁 `"Namespaces that contain the mapping's phonemes node."` (지금 "CNT_PHONEMES" 문구 삭제).
- `_node_map()` → Manual 이면 `{"phonemes": text or None, ...}`, Auto 면 `None`. `_namespace()` 는 Auto 일 때만 쓴다.
- Refresh: `scene.find_rigs(mapping["nodes"].get("phonemes") or first)`. 매핑을 못 읽으면 로그만.

### 4.2 Options

```
Start frame [1]      Viseme scale [1.0]
JaLi  ( ) From data  JaLi scale [1.0]   ( ) Fixed  Jaw [0.60] Lip [0.60]
[x] Attach audio  [x] Set playback range
```
- `ds_scale` 범위 **0 ~ 100**(지금 0~12 는 angela 전용 제한) · step 0.5 → 1 미만 규칙에서는 step 0.1 이 편하므로 `setSingleStep(0.1)` · 소수 2자리.
- `ds_jali_scale`(신규, 0~100, 소수 2자리). From data 일 때만 활성화.
- `ds_jaw` · `ds_lip` 범위 · 기본값 = `mapping["jali"]["range"]` · `fixed_default`. 소수 2자리.
- **`on_mapping_changed`**(콤보 `currentTextChanged`): json 을 읽어 `ds_scale` · `ds_jali_scale` · `ds_jaw/ds_lip` 범위와 값을 리셋, Manual 칸이 비어 있으면 `nodes` 의 이름을 **플레이스홀더**로 보여 준다(값은 안 넣음). 로그 `[INFO] Mapping '{name}': viseme scale {v:g}, JaLi scale {j:g}, Jaw/Lip {lo:g}-{hi:g}`. 창을 만들 때 한 번 호출.
- `on_apply`: `jali_fixed` 는 지금처럼 `(ds_jaw, ds_lip)`; `viseme_scale=ds_scale`, `jali_scale=ds_jali_scale`, `node_map=_node_map()`. Apply 직전 `scale_warnings` 로그. Manual 에서 3칸 전부 비면 `[ERROR] Manual target: fill at least one node.` 로 멈춘다.
- `[DONE]` 로그에 건너뛴 역할 표시: `..., skipped: coartic`.
- Remove Keys · Select Controls 도 `node_map` 을 넘긴다 (Manual 에서는 채운 노드만).
- About · 안내 문구에서 `CNT_JaLi / CNT_PHONEMES / CNT_COARTIC` 고정 표현을 `"the mapping's nodes (e.g. CNT_PHONEMES or DUMMY_IN_PHONEMES)"` 로.

### 4.3 창 크기
행이 3줄 늘어난다. `resize(460, 700)`. 오프스크린 테스트에서 레이아웃 최소 높이가 화면을 넘지 않는지 본다(메모리 `window-taller-than-screen-ghost`).

---

## 5. 리그 변경 (JUN_JALI `examples/build_jali_slider_ctl.py`, C7)

| 자리 | 지금 | 바꿈 |
|------|------|------|
| `build_jali_box()` | `cmds.setAttr(ctl + '.t', JALI_DEFAULT, JALI_DEFAULT, 0)` | `0, 0, 0` (컨트롤러 휴식 위치 0) |
| `_dummy()` 호출 `din_jali` | `addAttr … min 0 max 1` (dv 0) | `DUMMY_IN_JALI.Jaw/Lip` 만 `dv=JALI_DEFAULT`(0.6). `_dummy(name, attrs, parent, limited, defaults=None)` 로 |
| `verify()` | `JaLi default 9, 9` · `Lip 0.6+0.4 -> 15` · T6 Jaw unaffected | 기본 9 는 그대로 통과해야 한다(0.6 이 dummy 에서 옴). `DUMMY_IN_JALI.Lip` 을 **1.0** 으로 두면 15, `CNT_JaLi.ty` 0.4 + dummy 0.6 → 15. 추가: `DUMMY_IN_JALI.Jaw = 0` 이면 출력 0 |
| 헤더 주석 · 0090 §2 표 | "기본 위치 (0.6, 0.6) = 9, 9" | "DUMMY_IN_JALI 기본 0.6 = 9, 컨트롤러 휴식 0" |

- 결과: `A0020_jali_slider_ctl.ma` 를 **다시 생성 · 검증** 후 덮어쓴다 (`mayapy build_jali_slider_ctl.py <경로>` → `--verify`). 박스의 십자는 전과 같은 자리(0.6)에 보인다.
- 0090 계획서 §0-A 에 C7 한 줄, §9 S6 상태 갱신. 0120 안내 §0 의 "`DUMMY_OUT_JALI` 기본 9" 는 그대로 맞다.

---

## 6. 작업 순서

| 단계 | 할 일 | 끝났다는 기준 |
|------|-------|---------------|
| S1 ✅ | 리그 C7 (§5) → A0020 재생성 · `--verify` 통과 | 305 항목 0 실패, `DUMMY_IN_JALI` 기본 0.6 |
| S2 ✅ | `mapping.py` v2 읽기 · 검사, 두 json (angela 보강 · 새 규칙 추가) | T-M 21 통과 |
| S3 ✅ | `keyer.py` `resolve_targets`(→ `(targets, skipped)` 튜플) · `node_map` · `jali_scale` · `scale_warnings`, `scene.marker_of` · `find_rigs(marker)` | T-K 22 통과 |
| S4 ✅ | UI (§4) | T-U 18 통과 |
| S5 ✅ | 실제 파일로 끝까지 (T-E 18 통과, JUN_JALI `out/visemenet_intro.txt` 로): `A0020_jali_slider_ctl.ma` 를 열고 Auto + 새 규칙으로 Apply → `DUMMY_IN_*` 키 확인, Manual 로 Phonemes 만 → 나머지 건너뜀 확인, angela 파일 + angela 규칙으로 Apply → v01.00 과 같은 키값 | §7 T-E 통과 |
| S6 ✅ | 문서: `docs/A00540_JaliLipSync.md` §2 · §3 · §4 · §5 확인 기록, `version.py` 01.01, `docs/WORKLOG.md` 오늘 항목(최신이 위, 날짜 헤딩 중복 금지), JUN_JALI 0090 §0-A · §9, 메모리 `wip-a00540-jalilipsync` · `wip-jali-slider-ctl` | — |
| S7 ✅ | 커밋 (§8). **푸시 없음** | — |
| S8 | 사용자 GUI 확인: 드롭 설치, Auto/Manual 전환, 스핀박스 리셋, 실제 재생 | 사용자 |

---

## 7. 검증 (mayapy 2024, `tests/` 신설)

`tools/A00540_JaliLipSync/tests/` 에 두고 `mayapy -m pytest` 없이도 돌게 **각 파일이 `__main__` 으로 실행되는 단순 assert 스크립트** 로 쓴다(A00550 `tests/` 와 같은 방식). 실행: `"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" tests\run_all.py` (전부 돌리고 실패 수를 exit code 로).

**T-M `test_mapping.py`** (Maya 비의존)
1. angela json: `nodes` 3개, `viseme_scale` 10, `jali` {10, [0,15], [9,9]}, 타겟 23개 그대로.
2. 새 json: `nodes` 가 `DUMMY_IN_*`, `viseme_scale` 1, `jali` {1, [0,1], [0.6,0.6]}, 타겟 23개, 열 대응이 angela json 과 **같다**(attr 의 노드 이름만 다르고 `from` · `combine` 동일 — 두 파일을 짝지어 비교).
3. 오류: `nodes` 없음 · 타겟 노드가 `nodes` 에 없음 · `nodes` 값에 점 → 전부 `ValueError`, 메시지에 attr 이름.
4. 하위 호환: `viseme_scale` 없이 `targets[].scale 10` 만 있는 json → `viseme_scale` 10 으로 채워짐.

**T-K `test_keyer.py`** (작은 가짜 리그를 코드로 만든다: 트랜스폼 3개 + 어트리뷰트 min 0 max 1)
1. `resolve_targets(auto, "ns:")` → 23개, 전부 `ns:` 접두.
2. `resolve_targets(manual, node_map={"phonemes": "A", "coartic": None, "jali": "C"})` → coartic 5개 빠진 18개, 노드 이름 치환.
3. `node_map` 전부 None → `KeyingError`.
4. `sample`: 새 규칙 + `viseme_scale` None → 값 ≤ 1.0 (txt 최댓값 그대로); `jali_scale` 1 → Jaw 값 그대로; angela 규칙 → 10배.
5. `apply` Manual(`node_map={"phonemes": "A", "coartic": None, "jali": "C"}`) → A · C 노드에 키, 반환 `skipped == ["coartic"]`. `jali` 까지 None 이면 `skipped == ["coartic", "jali"]` 이고 C 노드 키 0개.
6. `remove` · `controls` 가 같은 `node_map` 을 따른다.
7. `scale_warnings`: max 1 어트리뷰트에 scale 10 → 경고 목록에 들어감, scale 1 → 빈 목록.
8. Fixed: `jali_fixed=(0.6, 0.6)` 이 새 규칙 타겟 `DUMMY_IN_JALI.Jaw/Lip` 에 구간 양끝 키로 들어간다.

**T-U `test_ui.py`** (오프스크린 — `QApplication` 을 `maya.standalone.initialize()` **앞에** 만든다, 메모리 `qapplication-before-maya-standalone`)
1. `run()` 으로 창 생성. 기본 Auto, Manual 칸 비활성.
2. 매핑 콤보를 새 규칙으로 → `ds_scale` 1.0 · `ds_jali_scale` 1.0 · `ds_jaw/ds_lip` 범위 0~1 값 0.6. angela 로 되돌리면 10 · 10 · 0~15 · 9.
3. Manual 선택 → Rig 콤보 비활성, 칸 활성. 씬에서 노드를 선택하고 `<< Sel` → 칸에 이름. `x` → 비움.
4. Manual 전부 빈 채 Apply → 로그 `[ERROR] Manual target` 로 멈춤(키 0).
5. 가짜 리그 + 새 규칙 + Auto Apply → 로그 `[DONE]`, 키 수 > 0. 단위 어긋남(angela 규칙 + max 1 노드 Manual) → `[WARN] … exceeds`.
6. 창 `sizeHint().height()` 가 1000 미만.

**T-E `test_end_to_end.py`** (실제 파일, 읽기만 · 저장 금지)
1. `02_Cage_JALI/A0020_jali_slider_ctl.ma` 열기 → `find_rigs("DUMMY_IN_PHONEMES")` == `[""]`. JUN_JALI 저장소의 참조 txt(`data/output_viseme/visemenet_intro/mayaparam_viseme.txt`, 0010 §3.3) 로 Auto Apply → `DUMMY_IN_PHONEMES.AAA` 키 존재, 모든 키 값 0~1, `DUMMY_OUT_PHONEMES.AAA` 의 최댓값 = 그 프레임 `DUMMY_IN` 값 × 12, `DUMMY_OUT_JALI.Jaw` = 데이터 Jaw × 15 (컨트롤러 휴식 위치가 0 이고 `DUMMY_IN_JALI` 의 기본값 0.6 은 키가 덮으므로 **더해지는 값이 없다**).
2. 같은 씬 Manual: Phonemes = `DUMMY_IN_PHONEMES` 만 → COARTIC · JALI 에 키 없음, `skipped == ["coartic", "jali"]`.
3. `angela_JALI.ma` + angela 규칙 Auto Apply → v01.00 과 같은 키값(이전 버전 결과를 미리 json 으로 떠 두거나, 같은 식으로 계산한 기대값과 비교).

---

## 8. 커밋 범위 (푸시는 그 턴에 요청이 있을 때만)

| 저장소 | 경로 | 메시지 머리 |
|--------|------|-------------|
| `Maya_Python` (dev) | `JUN_All/tools/A00540_JaliLipSync/**`(mappings 2개 · tests/ 포함) · `JUN_All/docs/A00540_JaliLipSync.md` · `JUN_All/docs/plans/A00540_JaliLipSync_v0101_rules_manual_plan.md` · `JUN_All/docs/WORKLOG.md` · `.claude/memory/wip-a00540-jalilipsync.md` · `.claude/memory/wip-jali-slider-ctl.md` · `MEMORY.md` | `feat(A00540_JaliLipSync): v01.01 …` |
| `JUN_JALI` (main) | `examples/build_jali_slider_ctl.py` · `docs/0090_jali_slider_ctl_plan.md` | `feat(examples): A0020 JaLi 기본값을 DUMMY_IN_JALI 로 …` |

- 스테이징은 **경로 명시** (`git add <경로>`). 작업 트리에 다른 세션 변경(`A00550 … libraries/*.json`, JUN_JALI `docs/.obsidian/`)이 있으면 그대로 둔다.
- `WORKLOG.md` · `MEMORY.md` 는 공용 파일 — 커밋 전 다른 세션 항목이 섞였는지 `git diff` 로 보고, 섞였으면 보고하고 묻는다.
- 포트폴리오 문서: 기능이 소폭이라 **갱신하지 않는다**(규칙 json 역할표는 포트폴리오 항목이 아님). 사용자가 원하면 그때.

---

## 9. 범위 밖 · 알려진 것

- **A00550 PoseMapper**: `capture.settable_plug()` 는 직결 소스를 최대 4단계 따라가는데, `DUMMY_OUT_PHONEMES.AAA ← gs_PH_AAA.output` 에서 `gs_*.output` 은 소스가 없어 "settable" 로 반환되고 거기에 `setAttr` 하면 실패한다(유틸리티 출력). 즉 **새 리그의 `DUMMY_OUT_*` 을 Source 로 두면 Solo / Capture 가 안 된다.** 해법 후보: Pose Map 에 "Solo 입력 노드 + 배율" 칸(`DUMMY_IN_PHONEMES`, ref 10 → 10/12)을 두거나, `settable_plug` 가 `multDoubleLinear/remapValue/plusMinusAverage` 를 만나면 첫 입력(`input1`/`inputValue`/`input1D[0]`)으로 들어가게 하는 것. 별도 계획으로.
- `YA_PEDAL` 은 원본 VisemeNet 매핑에 없어 새 규칙에도 없다(0010 §3.4 의 버그를 그대로 둔다 — 열이 없다).
- Manual 모드는 네임스페이스가 다른 노드를 섞어도 막지 않는다(의도: 어떤 리그든). 같은 역할에 노드 두 개는 지원하지 않는다.
- v01.00 형식 json 은 `nodes` 가 없으면 `load_mapping` 이 **거부**한다(의도 — 역할 없는 규칙은 Auto 표식을 정할 수 없다). 그래서 **`angela_jali_visemenet.json` 보강은 S2 에서 새 json 과 같은 커밋으로** 한다. `targets[].scale` 만 있는 json 은 §2 의 기본값 흡수로 읽힌다.
