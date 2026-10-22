# A00540_JaliLipSync

**VisemeNet** 이 음성에서 뽑은 비짐 커브(txt)를 **JALI 리그 컨트롤에 키로 거는** in-Maya PySide 툴.
txt 는 짝 저장소 **`JUN_JALI`** 의 스탠드얼론 `VisemeNet Converter` 가 만든다(wav → txt, TensorFlow 필요).
이 툴은 txt · wav 만 읽으므로 마야 안에 TensorFlow 가 없어도 된다.

- **버전**: v01.01 (2026-10-22)
- **아키텍처**: (B) in-Maya PySide (`maya.cmds`), 드래그&드롭 셸프 설치
- **짝**: `JUN_JALI` (https://github.com/elom1213/JUN_JALI) — 설치 · 변환은 `JUN_JALI/docs/0050_converter_guide.md`,
  계획은 `0030_tool_plan.md`, JALI ↔ ARKit 매칭은 `0040_jali_arkit_mapping.md`
- **대상 리그**: 매핑 json 하나 = 리그 하나 — `angela_JALI.ma` (JALI 논문 공개 리그, `CNT_JaLi` / `CNT_PHONEMES` / `CNT_COARTIC`) ·
  `A0020_jali_slider_ctl.ma` (슬라이더 리그, `DUMMY_IN_JALI` / `DUMMY_IN_PHONEMES` / `DUMMY_IN_COARTIC`, JUN_JALI `docs/0090` · `0120`)

---

## 1. 설치 · 실행

`__dragDrop_A00540.py` 를 마야 뷰포트로 드래그&드롭 → 현재 셸프에 `JaliLipSync` 버튼(입술 + 키 아이콘).
버튼 = `tools.A00540_JaliLipSync.run(True)`.

## 2. 사용

```
┌ JALI LipSync v01.01 ──────────────────────────────────────────┐
│ Data    Viseme TXT [line01_ko.txt        ] [...]              │
│         Audio WAV  [line01_ko.wav        ] [...]              │
│         364 rows = 3.64 s -> 87 frames at 24 fps | WAV 3.99 s │
│ Target  (•) Auto    Rig [(root) ▼] [Refresh]                   │
│         ( ) Manual  Phonemes [                 ] [<< Sel] [x] │
│                     Coartic  [                 ] [<< Sel] [x] │
│                     JaLi     [                 ] [<< Sel] [x] │
│                     Mapping  [jali_slider_dummy_in ▼]         │
│ Options Start frame [1]  Viseme scale [1.00]                  │
│         JaLi (•) From data  JaLi scale [1.00]                 │
│              ( ) Fixed  Jaw [0.60] Lip [0.60]                 │
│         [x] Attach audio  [x] Set playback range              │
│ [ Apply ]  [ Remove Keys ]  [ Select Controls ]               │
│ Log                                                            │
└────────────────────────────────────────────────────────────────┘
```

1. 리그 씬을 열고 **`Mapping` 에서 리그에 맞는 규칙**을 고른다 — `angela_jali_visemenet`(angela) 또는 `jali_slider_dummy_in`(A0020 슬라이더 리그).
   규칙을 고르면 `Viseme scale` · `JaLi scale` · `Fixed` 의 범위 · 기본값이 그 규칙 값으로 **리셋**된다(그 뒤 손으로 바꿔도 된다).
   `Target` 은 둘 중 하나:
   - **Auto** — 규칙의 phonemes 노드 이름(`CNT_PHONEMES` / `DUMMY_IN_PHONEMES`)으로 리그를 찾는다. 레퍼런스면 `Rig` 콤보에 `angela:` 처럼 네임스페이스가 나온다.
   - **Manual** — Phonemes · Coartic · JaLi 노드를 씬에서 골라 `<< Sel` 로 넣는다(이름은 아무거나, 어트리뷰트 이름만 규칙과 같으면 된다).
     **비워 둔 역할은 건너뛴다** — Phonemes 만 넣으면 음소만 키. 로그에 `skipped: coartic, jali`.
2. `Viseme TXT` 의 `...` → 변환기가 만든 `<이름>.txt`.
   **WAV 는 자동으로 채운다** — `<이름>.visemenet.json` 의 원본 경로 → txt 폴더의 같은 이름 `.wav` → 상위 폴더의 같은 이름 순.
   못 찾으면 `[WARN]` 후 직접 고른다(선택 사항).
3. `Apply`. 로그: `[DONE] 23 attributes keyed on '(root)': frames 1-88 @ 24 fps (2024 keys, JaLi from data x 1)`.
   적용 배율이 어트리뷰트 최댓값보다 크면(예: angela 규칙 scale 10 을 0~1 노드에) `[WARN] … exceeds the attribute maximum` 을 먼저 찍는다 — 규칙을 잘못 고른 신호.
4. 재생. 타임슬라이더에 파형이 붙는다(`jali_lipsync_audio` 노드). 재생 속도는 `Real-time` 으로.

| 옵션 | 뜻 |
|------|-----|
| `Start frame` | 첫 프레임 (대사를 100 프레임부터면 100) |
| `Viseme scale` | 모델 값(0~1) × 이 값 = 비짐 키. 기본값은 규칙이 정한다 — angela 10(리그 최대 12), 슬라이더 리그 1(txt 1.0 = 슬라이더 끝). JaLi 에는 적용 안 됨 |
| `JaLi From data` + `JaLi scale` | 모델의 Jaw / Lip 커브 × JaLi scale 을 JaLi 노드에 키. 기본값 angela 10(`CNT_JaLi.translateX/Y` 0~10), 슬라이더 리그 1(`DUMMY_IN_JALI.Jaw/Lip` 0~1) |
| `JaLi Fixed` | JaLi 노드를 구간 처음 · 끝에 고정값으로만 키(리그 단위 — 범위 · 기본값은 규칙: angela 0~15 · 9, 슬라이더 0~1 · 0.6) — 비짐 타이밍은 데이터, 말투는 사람이 정한다 |
| `Attach audio` | 사운드 노드를 만들어 Start frame 에 놓는다 (다시 Apply 하면 교체) |
| `Set playback range` | 타임라인을 결과 길이로 |

- **다시 Apply 해도 섞이지 않는다** — 그 구간의 기존 키를 지우고 건다. **전체가 Undo 한 번.**
- `Remove Keys` = 매핑 어트리뷰트의 키를 데이터 구간에서 지운다(데이터가 없으면 전부). `Select Controls` = 규칙의 컨트롤 선택. Manual 이면 채운 노드만.
  **키를 지워도 어트리뷰트 값은 마지막 키 값에 머문다**(마야 동작). 슬라이더 리그의 JaLi 를 기본 9 로 되돌리려면 `DUMMY_IN_JALI.Jaw / Lip` 을 0.6 으로.
- 정보 줄의 `(check the pair: +0.80 s)` — WAV 가 txt 보다 0.5초 넘게 길거나 짧다. 다른 음성의 txt 를 고른 것은 아닌지 확인.
  (정상이어도 WAV 가 0.3초쯤 길다 — 아래)

## 3. 알아 둘 것

- **키는 씬 fps 로 샘플한다** — 프레임 f → 시간 f / fps → 모델 줄 `round(시간 × 100)`. 원본 VisemeNet `maya_animation.py` 는
  4줄마다 1프레임(= 25fps 가정)이라 24fps 씬에서 4% 어긋났다.
- **모델 출력은 음성 끝 0.32초가 빠진다**(시작은 맞다) — 마지막 키 값이 유지된다. 이유는 JUN_JALI `docs/0050` §4.2.
- 매핑은 원본 스크립트와 같다: `OHH` = max(Oh, Uh), `IEE` = max(Ee, Ih), `WWW` ← `U` 열, `CNT_COARTIC.WA_PEDAL` ← `W` 열,
  `CNT_COARTIC.YA_PEDAL` · `Eu` · `JY` 는 안 씀.
- 키를 걸 수 없는 어트리뷰트(없음 · 잠김 · 애니커브가 아닌 연결)가 하나라도 있으면 **아무것도 하지 않고** 목록을 로그에 남긴다.

## 4. 새 리그 · ARKit 아바타 — 매핑 json (v01.01 형식)

`app/mappings/<이름>.json` 하나를 추가하면 `Mapping` 콤보에 나온다(코드 수정 없음). 들어 있는 것: `angela_jali_visemenet`(angela 리그) · `jali_slider_dummy_in`(A0020 슬라이더 리그).

```json
{"name": "...", "model_columns": ["Jaw", "Lip", "Ah", ...22개],
 "clamp": [0.0, 1.0],
 "nodes": {"phonemes": "DUMMY_IN_PHONEMES", "coartic": "DUMMY_IN_COARTIC", "jali": "DUMMY_IN_JALI"},
 "viseme_scale": 1.0,
 "jali": {"scale": 1.0, "range": [0.0, 1.0], "fixed_default": [0.6, 0.6]},
 "targets": [
   {"attr": "DUMMY_IN_JALI.Jaw", "from": ["Jaw"]},
   {"attr": "DUMMY_IN_PHONEMES.OHH", "from": ["Oh", "Uh"], "combine": "max"}
 ]}
```

| 키 | 뜻 |
|----|-----|
| `nodes` | **역할 → 노드 이름**. `phonemes` `coartic` `jali` 중 하나 이상. Auto 는 `phonemes` 노드 이름으로 리그를 찾고, Manual 은 이 이름을 사용자가 고른 노드로 바꿔 끼운다. 모든 `targets` 의 노드가 여기 있어야 한다(없으면 읽기 거부) |
| `viseme_scale` | 비짐 배율 기본값(스핀박스 리셋값) |
| `jali` | `scale` JaLi 배율 기본값 · `range` Fixed 스핀박스 범위 · `fixed_default` Fixed 기본 `[jaw, lip]` (전부 리그 단위) |
| `targets[]` | `attr`(노드.어트리뷰트) · `from`(모델 열) · `combine` = `max` / `sum` / `avg`. 역할은 노드로 판정한다(`role: "jali"` 를 명시해도 된다). `scale` 은 옛 형식 호환용 — `viseme_scale` · `jali.scale` 이 없을 때만 읽는다 |

ARKit 블렌드셰이프 아바타라면 `nodes` 를 `{"phonemes": "blendShape1"}` 처럼 두고 `attr` 을 `blendShape1.jawOpen` 으로, `JUN_JALI/docs/0040` 의 표로 `from` 을 채운다.
출력 세기(슬라이더 리그의 `output_max` · `global_scale`)는 규칙이 아니라 **리그에서** 조절한다.

## 5. 구조 (개발자용)

```
A00540_JaliLipSync/
├── __init__.py · launch.py · __dragDrop_A00540.py
├── app/config/version.py
├── app/core/
│   ├── lipsync_data.py   txt(22열) + json 읽기 · 검증, find_wav(), wav_seconds()   (Maya 비의존)
│   ├── mapping.py        app/mappings/*.json 읽기 · 검증(nodes 역할표 · 배율 기본값 채움), combine()   (Maya 비의존)
│   ├── keyer.py          resolve_targets(Auto 네임스페이스 / Manual node_map) · sample · check_targets · scale_warnings
│   │                     · apply · remove · controls (undo_chunk)
│   └── scene.py          marker_of(mapping) · find_rigs(marker), attach_sound()
├── app/mappings/angela_jali_visemenet.json · jali_slider_dummy_in.json
├── app/ui/main_window.py
├── tests/run_all.py      test_mapping · test_keyer · test_ui · test_end_to_end (mayapy, 실제 파일은 열기만)
└── icon/A00540_JaliLipSync.svg / .png
```

**확인 기록 (2026-10-19, mayapy 2024)**: 코어 19항목(적용 · 재적용 · Undo 한 번 · JaLi 고정 · 배율 · 지우기 · 사운드 ·
잠긴 어트리뷰트 거부 · 레퍼런스 + 네임스페이스 · 형식 오류) + 오프스크린 UI 15항목(`run()` · WAV 자동 찾기(json 있음/없음) ·
Apply · Fixed · Select · Remove · 나쁜 txt). **마야 GUI 에서 드롭 설치 · 소리와 함께 재생은 사용자 확인 전.**

**확인 기록 (2026-10-22, v01.01, `tests/run_all.py`)**: 매핑 21(두 json · 오류 5종 · 옛 형식 호환) · 코어 22(Auto/Manual 해석 · 건너뜀 · 배율 · Fixed · 잠김 거부 · 단위 경고) ·
오프스크린 UI 18(규칙 바꾸면 스핀박스 리셋 · Manual 전환 · `<< Sel` · 빈 Manual 거부 · 건너뜀 로그 · 단위 경고 · 창 높이) · 실제 파일 18(`A0020_jali_slider_ctl.ma` Auto/Manual — 출력 = 키 × 12, Jaw = 키 × 15 · `angela_JALI.ma` 키값이 v01.00 식과 동일). **마야 GUI 미확인.**
