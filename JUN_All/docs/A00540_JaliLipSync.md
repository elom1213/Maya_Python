# A00540_JaliLipSync

**VisemeNet** 이 음성에서 뽑은 비짐 커브(txt)를 **JALI 리그 컨트롤에 키로 거는** in-Maya PySide 툴.
txt 는 짝 저장소 **`JUN_JALI`** 의 스탠드얼론 `VisemeNet Converter` 가 만든다(wav → txt, TensorFlow 필요).
이 툴은 txt · wav 만 읽으므로 마야 안에 TensorFlow 가 없어도 된다.

- **버전**: v01.00 (2026-10-19)
- **아키텍처**: (B) in-Maya PySide (`maya.cmds`), 드래그&드롭 셸프 설치
- **짝**: `JUN_JALI` (https://github.com/elom1213/JUN_JALI) — 설치 · 변환은 `JUN_JALI/docs/0050_converter_guide.md`,
  계획은 `0030_tool_plan.md`, JALI ↔ ARKit 매칭은 `0040_jali_arkit_mapping.md`
- **대상 리그**: `angela_JALI.ma` (JALI 논문 공개 리그, `CNT_JaLi` / `CNT_PHONEMES` / `CNT_COARTIC`)

---

## 1. 설치 · 실행

`__dragDrop_A00540.py` 를 마야 뷰포트로 드래그&드롭 → 현재 셸프에 `JaliLipSync` 버튼(입술 + 키 아이콘).
버튼 = `tools.A00540_JaliLipSync.run(True)`.

## 2. 사용

```
┌ JALI LipSync v01.00 ───────────────────────────────┐
│ Data    Viseme TXT [line01_ko.txt        ] [...]   │
│         Audio WAV  [line01_ko.wav        ] [...]   │
│         364 rows = 3.64 s -> 87 frames at 24 fps | WAV 3.99 s
│ Target  Rig [(root) ▼] [Refresh]                   │
│         Mapping [angela_jali_visemenet ▼]          │
│ Options Start frame [1]  Viseme scale [10.0]       │
│         JaLi (•) From data ( ) Fixed  Jaw [9] Lip [9]
│         [x] Attach audio  [x] Set playback range   │
│ [ Apply ]  [ Remove Keys ]  [ Select Controls ]    │
│ Log                                                 │
└─────────────────────────────────────────────────────┘
```

1. 리그 씬을 연다(`angela_JALI.ma`). 레퍼런스로 불러온 리그도 된다 — `Rig` 콤보에 `angela:` 처럼 네임스페이스가 나온다.
2. `Viseme TXT` 의 `...` → 변환기가 만든 `<이름>.txt`.
   **WAV 는 자동으로 채운다** — `<이름>.visemenet.json` 의 원본 경로 → txt 폴더의 같은 이름 `.wav` → 상위 폴더의 같은 이름 순.
   못 찾으면 `[WARN]` 후 직접 고른다(선택 사항).
3. `Apply`. 로그: `[DONE] 23 attributes keyed on '(root)': frames 1-88 @ 24 fps (2024 keys, JaLi from data)`.
4. 재생. 타임슬라이더에 파형이 붙는다(`jali_lipsync_audio` 노드). 재생 속도는 `Real-time` 으로.

| 옵션 | 뜻 |
|------|-----|
| `Start frame` | 첫 프레임 (대사를 100 프레임부터면 100) |
| `Viseme scale` | 모델 값(0~1) × 이 값 = 비짐 키. 10 = 원본, 리그 최대 12. `CNT_JaLi` 에는 적용 안 됨 |
| `JaLi From data` | 모델의 Jaw / Lip 커브를 `CNT_JaLi.translateX / Y` 에 키 (0~10) |
| `JaLi Fixed` | `CNT_JaLi` 를 구간 처음 · 끝에 고정값으로만 키 — 비짐 타이밍은 데이터, 말투는 사람이 정한다 |
| `Attach audio` | 사운드 노드를 만들어 Start frame 에 놓는다 (다시 Apply 하면 교체) |
| `Set playback range` | 타임라인을 결과 길이로 |

- **다시 Apply 해도 섞이지 않는다** — 그 구간의 기존 키를 지우고 건다. **전체가 Undo 한 번.**
- `Remove Keys` = 매핑 어트리뷰트의 키를 데이터 구간에서 지운다(데이터가 없으면 전부). `Select Controls` = 세 컨트롤 선택.
- 정보 줄의 `(check the pair: +0.80 s)` — WAV 가 txt 보다 0.5초 넘게 길거나 짧다. 다른 음성의 txt 를 고른 것은 아닌지 확인.
  (정상이어도 WAV 가 0.3초쯤 길다 — 아래)

## 3. 알아 둘 것

- **키는 씬 fps 로 샘플한다** — 프레임 f → 시간 f / fps → 모델 줄 `round(시간 × 100)`. 원본 VisemeNet `maya_animation.py` 는
  4줄마다 1프레임(= 25fps 가정)이라 24fps 씬에서 4% 어긋났다.
- **모델 출력은 음성 끝 0.32초가 빠진다**(시작은 맞다) — 마지막 키 값이 유지된다. 이유는 JUN_JALI `docs/0050` §4.2.
- 매핑은 원본 스크립트와 같다: `OHH` = max(Oh, Uh), `IEE` = max(Ee, Ih), `WWW` ← `U` 열, `CNT_COARTIC.WA_PEDAL` ← `W` 열,
  `CNT_COARTIC.YA_PEDAL` · `Eu` · `JY` 는 안 씀.
- 키를 걸 수 없는 어트리뷰트(없음 · 잠김 · 애니커브가 아닌 연결)가 하나라도 있으면 **아무것도 하지 않고** 목록을 로그에 남긴다.

## 4. 새 리그 · ARKit 아바타

`app/mappings/<이름>.json` 하나를 추가하면 `Mapping` 콤보에 나온다(코드 수정 없음).

```json
{"name": "...", "model_columns": ["Jaw", "Lip", "Ah", ...22개],
 "clamp": [0.0, 1.0],
 "targets": [
   {"attr": "CNT_JaLi.translateX", "from": ["Jaw"], "scale": 10, "role": "jali"},
   {"attr": "CNT_PHONEMES.OHH", "from": ["Oh", "Uh"], "combine": "max", "scale": 10}
 ]}
```

`combine` = `max` / `sum` / `avg`. `role: "jali"` = `JaLi Fixed` 일 때 고정값을 넣을 대상.
ARKit 블렌드셰이프 아바타라면 `attr` 을 `blendShape1.jawOpen` 처럼 쓰고 `JUN_JALI/docs/0040` 의 표로 `from` · `scale` 을 채운다.

## 5. 구조 (개발자용)

```
A00540_JaliLipSync/
├── __init__.py · launch.py · __dragDrop_A00540.py
├── app/config/version.py
├── app/core/
│   ├── lipsync_data.py   txt(22열) + json 읽기 · 검증, find_wav(), wav_seconds()   (Maya 비의존)
│   ├── mapping.py        app/mappings/*.json 읽기 · 검증, combine()                  (Maya 비의존)
│   ├── keyer.py          scene_fps · sample · check_targets · apply · remove · controls (undo_chunk)
│   └── scene.py          find_rigs() (CNT_PHONEMES 네임스페이스), attach_sound()
├── app/mappings/angela_jali_visemenet.json
├── app/ui/main_window.py
└── icon/A00540_JaliLipSync.svg / .png
```

**확인 기록 (2026-10-19, mayapy 2024)**: 코어 19항목(적용 · 재적용 · Undo 한 번 · JaLi 고정 · 배율 · 지우기 · 사운드 ·
잠긴 어트리뷰트 거부 · 레퍼런스 + 네임스페이스 · 형식 오류) + 오프스크린 UI 15항목(`run()` · WAV 자동 찾기(json 있음/없음) ·
Apply · Fixed · Select · Remove · 나쁜 txt). **마야 GUI 에서 드롭 설치 · 소리와 함께 재생은 사용자 확인 전.**
