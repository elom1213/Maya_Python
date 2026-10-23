# A00560_JaliBatch — 툴 제작 계획서 (대량 wav → JALI 클립 .mb 생성 + 레퍼런스 검수)

> **작성** 2026-10-23 · **갱신** 2026-10-23 (D7 — 시작 프레임을 파일 이름에서 읽지 않는다, 사용자 지시) · 상태: **계획 (실측 M0 전)** · 대상 Maya 2024 (mayapy) · PySide6 standalone + in-Maya 검수 툴
> 평가 문서 [A00560_JaliBatch_pipeline_review.md](A00560_JaliBatch_pipeline_review.md) 의 개선안(§2-1 ~ 2-11)을 **그대로 반영**한 계획이다.
> 참고 코드: `A00540_JaliLipSync/app/core`(keyer · mapping · lipsync_data · sequence · scene — **이 코어를 그대로 쓴다**, 사용자 요청) ·
> `A00210_FileManager/app/maya`(mayapy 워커 · QProcess · 진행률 · 취소) · JUN_JALI `examples/build_jali_slider_ctl.py`(`bake_ctl_keys`) ·
> JUN_JALI `tools/VisemeNet_Converter/app/core/converter.py`(`Engine` · `run_batch`, 2단계 CLI 의 재료).
> 용어: **JALI 툴** = `JUN_JALI` · **JALI 컨트롤러** = `02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma` · **클립** = 대사 하나의 `.mb`.

---

## 0. 요청과 산출물

| # | 요청 | 산출물 | 저장소 · 형태 |
|---|------|--------|---------------|
| **P0** | 공용으로 끌어올리기 — A00540 코어와 A00210 mayapy 러너를 다른 툴이 쓸 수 있게 | `Framework/jali/`(keyer · mapping · lipsync_data · sequence · bake + mappings json) · `Framework/core/mayapy_runner.py` · `Framework/qt/MOD_mayapyProcess_qt_v01.py` | Maya_Python (A00540 · A00210 은 재노출 유지) |
| **P1** | 변환 결과 폴더(N 개 txt · json · wav) → **N 개 클립 .mb** (컨트롤러 레퍼런스 + DUMMY_IN 키 → 컨트롤러 베이크 + 소리 + 도장) | **`A00560_JaliBatch`** standalone(Qt, 마야 밖) — `Batch` 탭 | Maya_Python, 아키텍처 (B) |
| **P2** | 클립들을 한꺼번에 점검 · 컨트롤러 경로 갱신 | A00560 `Validate` 탭 | 〃 |
| **P3** | 검수 씬: 클립 + 아바타 레퍼런스, ARKIT_OUT → 블렌드셰이프 연결, **클립 교체**, **편집 저장**(Save Reference Edits), 편집 검사 | **`A00570_JaliReview`** in-Maya(PySide, 드래그&드롭 셸프) | Maya_Python, 아키텍처 (B) in-Maya |
| **P4** (2단계) | wav + 대본 폴더에서 변환까지 한 번에 | JUN_JALI `tools/VisemeNet_Converter/cli.py`(헤드리스) + A00560 `Convert` 단계 | JUN_JALI + Maya_Python |

예시 입력: `JUN_JALI_Voice/0060_Vivian_voice/out_en_002`(5 클립: 22열 txt · `.visemenet.json` · `.phones.json` · wav).
`src_en` 은 wav + 대본만이라 P4 전에는 변환기를 먼저 돌린 폴더를 넣는다.

---

## 1. 설계 결정 (권장안 — §9 질문에서 확인)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| **D1** | 툴 배치 | **standalone `A00560_JaliBatch`(생성 · 점검) + in-Maya `A00570_JaliReview`(검수)** 두 툴 | 생성은 마야 밖에서 mayapy 로 N 개를 돌리는 일(A00210 Maya 탭과 같은 성격), 검수는 마야 GUI 안에서 레퍼런스를 다루는 일. 한 패키지에 두 진입점을 넣으면 릴리즈 빌더 · 드롭 파일 · 문서가 둘 다 꼬인다. `A00540` 은 "음성 → 키 한 가지" 를 유지(A00550 계획 D1 과 같은 이유) |
| **D2** | A00540 코어 재사용 방법 | **`Framework/jali/` 로 승격**, A00540 은 `from Framework.jali import keyer …` 재노출 | 릴리즈본은 툴 간 import 금지(메모리 `release-layout-launch-py`) — Framework 는 모든 릴리즈에 동봉되므로 A00560 워커 · A00570 이 같은 코드를 쓴다. 복사본은 두 벌이 갈라진다 |
| **D3** | mayapy 러너 재사용 | **A00210 `mayapy_runner.py` → `Framework/core/`, `mayapy_process.py` → `Framework/qt/`** 로 승격, A00210 재노출 | D2 와 같은 이유. A00210 메모리에 "뗄 수 있게 만들었다" 고 적혀 있다 |
| **D4** | 베이크 코드 | JUN_JALI `bake_ctl_keys` 를 **`Framework/jali/bake.py` 로 이식**(출처 주석) + DUMMY_IN 커브 삭제 추가 | JUN_JALI 는 별도 공개 저장소라 import 할 수 없다. 이식 뒤 JUN_JALI 쪽은 그대로 둔다(검증 스크립트가 쓴다) |
| **D5** | 클립 한 개 = 작업 단위, 워커 **한 프로세스**가 N 개 순서대로 | 기동 1회(4~5초), 클립 경계에서 취소 | A00210 워커 프로토콜(`JUNMSG` log/progress/result/error + cancel 플래그 파일) 그대로 |
| **D6** | 클립 씬 설정 | `currentUnit -time <fps>`(기본 **ntsc 30**) → 컨트롤러 레퍼런스(ns **`JALI`**) → 재생 범위 → 키 → 베이크 → 소리 → fileInfo 도장 → `.mb` 저장 | fps 를 먼저 — A00540 keyer 가 씬 fps 로 샘플한다. 네임스페이스 고정은 평가서 §2-4 |
| **D7** | 시작 프레임 | **모든 클립 같은 값 하나**(스핀박스, 기본 `1`) + 표의 `Start` 열을 클립마다 **손으로 수정** 가능(매니페스트에 저장). **파일 이름은 읽지 않는다** | 사용자 지시(2026-10-23): 예시 자료의 `_f0105_0429` 는 그 자료만의 표기, 이름에 프레임이 없는 파일이 일반적일 수 있다 — 이름 규칙에 의존하면 다른 폴더에서 조용히 틀린다. 이름은 클립 `.mb` 이름에만 쓴다 (평가서 §2-5) |
| **D8** | 베이크 모드 | `copy`(DUMMY_IN 커브를 컨트롤러로 통째 복사) 고정, 뒤에 DUMMY_IN 커브 삭제 · animCurve 이름 `JALI_<ctl>_<attr>` | 키 수 · 탄젠트 그대로. `bake` 샘플은 프레임마다 키가 생겨 손질이 힘들다 |
| **D9** | 덮어쓰기 | **Skip** 기본 / Overwrite / Overwrite with backup(`backup/`). `edited` 클립은 한 번 더 묻기 | 평가서 §2-8 |
| **D10** | 기록 | 출력 폴더 `jali_clips.manifest.json` + 클립 `fileInfo jun_jali_clip` | 평가서 §2-3 · 2-6. A00570 이 목록을 여기서 읽는다 |
| **D11** | 검수 씬 연결 | ARKIT_OUT 52 → 블렌드셰이프 **별칭 이름 일치**만, 이미 연결된 타겟 Skip, 결과 표. 아바타별 규칙 json(선택) | 평가서 §2-11 |
| **D12** | 편집 저장 · 교체 | `Save Clip Edits` = `file -saveReference`; `Swap` 은 편집 0건일 때만, 아니면 Save / Discard / Cancel | 평가서 §2-1 · 2-2 (**M0 실측으로 확정**) |
| **D13** | JaLi(Jaw/Lip) | A00540 과 같은 선택 — **Data**(기본) / Fixed(값 2개) | 사용자가 A00540 에서 이미 쓰는 옵션. 리그 기본 0.6 은 Fixed 기본값 |
| **D14** | wav | 기본 **클립 옆으로 복사**(같은 이름 `.wav`), 소리 노드는 복사본을 가리킴 | 클립 폴더만 옮겨도 소리가 산다 |

---

## 2. 최종 폴더 구조

```
JUN_All/
├─ Framework/
│  ├─ jali/                               P0 (A00540 코어 승격)
│  │  ├─ __init__.py
│  │  ├─ keyer.py · mapping.py · lipsync_data.py · sequence.py      ← A00540 app/core 에서 이동 (maya.cmds 는 keyer 만)
│  │  ├─ bake.py                          ← JUN_JALI bake_ctl_keys 이식 + cleanup_dummy_in()
│  │  ├─ clip_stamp.py                    fileInfo 도장 읽기 · 쓰기 (순수 파이썬 + cmds 분리)
│  │  └─ mappings/                        angela_jali_visemenet.json · jali_slider_dummy_in.json (A00540 app/mappings 이동)
│  ├─ core/mayapy_runner.py               P0 (A00210 승격) find_mayapy · write_job · command · parse_line
│  └─ qt/MOD_mayapyProcess_qt_v01.py      P0 (A00210 승격) QProcess + 진행률 팝업 + Cancel
│
├─ tools/A00540_JaliLipSync/app/core/*.py 재노출 (from Framework.jali.keyer import *) — tests 132 그대로 통과해야
├─ tools/A00210_FileManager/app/maya/core/mayapy_runner.py · ui/mayapy_process.py 재노출
│
├─ tools/A00560_JaliBatch/                P1 · P2 (standalone, A00210 · A00240 과 같은 모양)
│  ├─ launch.py · __init__.py · launch.spec · build_exe.bat · requirements.txt · icon/
│  ├─ app/config/{version.py, app_meta.py}
│  ├─ app/core/
│  │  ├─ source_scan.py                   폴더 → 클립 후보 (txt 22열 + json + wav 짝, 이름 패턴 → start), 문제 목록
│  │  ├─ manifest.py                      jali_clips.manifest.json 읽기 · 쓰기 · 상태 갱신
│  │  ├─ jobs.py                          generate / validate job json 만들기 (설정 → 워커 입력)
│  │  └─ prefs.py                         mayapy 경로 · 컨트롤러 경로 · 최근 폴더 · 옵션 (A00240 prefs 모양)
│  ├─ app/maya/worker.py                  mayapy 가 실행. job "generate" / "validate" (Framework.jali · bake 사용)
│  └─ app/ui/{main_window.py, batch_tab.py, validate_tab.py, clip_table.py}
│
└─ tools/A00570_JaliReview/               P3 (in-Maya PySide, A00008_base_QT_maya 복제)
   ├─ launcher.py · __init__.py · __dragDrop_A00570.py · icon/
   ├─ app/config/version.py
   ├─ app/core/
   │  ├─ review_scene.py                  클립 · 아바타 레퍼런스 만들기 · 찾기 (CLIP_RN), swap, pending edits, save_reference
   │  ├─ arkit_connect.py                 CLIP:JALI:ARKIT_OUT.* → BS 별칭 매칭 연결 · 보고 · 규칙 json
   │  └─ prefs.py                         마지막 클립 폴더 · 아바타 경로 · 규칙
   └─ app/ui/main_window.py               Clips(목록 · Prev/Next/Swap) · Connect · Edits(목록 · Save/Discard) · Open Clip
```

문서: `docs/A00560_JaliBatch.md` · `docs/A00570_JaliReview.md`(사용 안내) · 이 계획서 · `docs/README.md` 표 두 줄 · `docs/Framework_jali.md`(공용 코어 안내) · WORKLOG · 메모리.

---

## 3. 파이프라인 — 워커 한 클립의 순서 (P1 `generate`)

```
job.json  { "job": "generate", "controller": <A0030 .ma>, "mapping": "jali_slider_dummy_in", "fps": 30,
            "default_start": 1, "jali": {"mode": "data" | "fixed", "fixed": [0.6, 0.6]},
            "viseme_scale": 1.0, "overwrite": "skip" | "overwrite" | "backup", "copy_wav": true,
            "clips": [{"name", "txt", "json", "wav", "out_mb", "start"}],   # start = 표의 값 (기본 default_start, 이름에서 안 읽음)
            "manifest": <경로>,
            "result": <결과 json>, "cancel_flag": <경로> }
```

| 단계 | maya.cmds | 비고 |
|------|-----------|------|
| 1 | `file(new=True, force=True)` · `currentUnit(time=<fps 이름>)` | fps 를 먼저 (keyer 는 씬 fps 샘플) |
| 2 | `file(controller, reference=True, namespace="JALI")` | 네임스페이스 고정. 중첩 없음 |
| 3 | `data = lipsync_data.load(txt)` → `seg = sequence.layout([Clip], start, 0, fps)` → `playbackOptions(min=start, max=seg.end, ast, aet)` | 클립 길이는 **wav 길이** 기준(A00540 v01.02 와 같다) |
| 4 | `keyer.apply_sequence(seg, mapping, namespace="JALI:", jali_fixed=…)` | DUMMY_IN_* 23 어트리뷰트에 키. `undo_chunk` 는 standalone 에서도 무해 |
| 5 | `bake.bake_ctl_keys(nodes=ls("JALI:CTL_PH_*","JALI:CTL_CO_*","JALI:CNT_JaLi"), mode="copy")` → `bake.cleanup_dummy_in()` → 커브 rename `JALI_<ctl>_<attr>` | 컨트롤러 채널에 키가 남고 DUMMY_IN → 컨트롤러 연결은 끊김(레퍼런스 편집 2종: disconnectAttr · connectAttr). DUMMY_IN 커브 삭제 |
| 6 | (copy_wav) wav 복사 → `sound(file=…, offset=start, name="jali_lipsync_audio")` | 레퍼런스 씬에서 보이는지는 M0-5 |
| 7 | `fileInfo("jun_jali_clip", json)` · `file(rename=out_mb)` · `file(save=True, type="mayaBinary")` | 도장 뒤 저장. 기존 파일 정책은 D9 (backup 은 저장 전 복사) |
| 8 | `progress(i, N, name)` · 매니페스트 갱신 · `cancel_flag` 확인 | 실패 클립은 `status: failed, error` 로 적고 **다음 클립 계속**(변환기의 "멈춤" 정책과 다르다 — 클립은 서로 독립, 결과 표에서 실패만 다시 돌린다) |

`validate` job: 클립마다 `file(open, loadReferenceDepth="all", prompt=False)` → `referenceQuery(RN, filename, failedEdits)` · 베이크 채널 수(`JALI:CTL_*` 중 animCurve 연결) · 키 수 · DUMMY_IN 연결 0 · fileInfo 도장 ↔ 컨트롤러 mtime → 표. `repath` 옵션이면 `file(new_controller, loadReference=RN)` 후 저장(이때만 쓴다).

---

## 4. A00560 UI (standalone)

```
┌ JALI Batch ───────────────────────────────────────────────  [Shrink] [Pin] ┐
│ File(Add to Start Menu)  Help                                              │
│ ┌ Batch ─────────────────────┐ ┌ Validate ──────────────────────────────┐ │
│ │ Source   [out_en_002  ][…] │ │ Clip folder [ … ][…]  [Scan]            │ │
│ │ Controller [A0030….ma ][…] │ │ ┌ Clip | Controller | Edits | Keys |   │ │
│ │ Output   [out_en_002/maya][…]│ │ │ … failedEdits 빨강, stamp 불일치 노랑 │ │
│ │ ┌ ☑ Clip | Start | Frames | wav | Status ┐ │ │ └───────────────────────┘ │ │
│ │ │ ☑ 0030_vivian_en_01_f0105_0429 |   1 | 324 | ● | - │ │ │ Repath controller [ … ] ☐ │ │
│ │ │ ☑ 0030_vivian_en_02_f0445_0490 |   1 | 135 | ● | exists │ │ │ [Validate] [Repath]      │ │
│ │ └──────────────────────────────┘ │ └────────────────────────────────────┘ │
│ │ Start [  1 ] (all clips, Start cell editable) fps [30 ▾] Mapping [jali_slider_dummy_in ▾] │
│ │ JaLi [Data ▾] [0.60][0.60]  Existing [Skip ▾]  ☑ Copy WAV                │
│ │ mayapy [C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe][…][Detect]    │
│ │ [Run]  [Cancel]  ▓▓▓▓▓▓░░░░ 3 / 5  0030_vivian_en_03…                     │
│ └──────────────────────────────────────────────────────────────────────────┘
│ Log (공용 JUN_mod_log_qt_v01)                                               │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Source 스캔**(`source_scan`): 22열 txt 가 있는 이름만 클립 후보. json 없음 → WARN(길이는 wav 로), wav 없음 → ERROR(제외). **파일 이름에서 프레임을 읽지 않는다** — `Start` 는 스핀박스 값으로 채우고 표에서 클립마다 고칠 수 있다(매니페스트에 저장돼 다음 Run 에도 남는다). 22열이 하나도 없으면 "Run VisemeNet Converter first (JUN_JALI)" 안내.
- 표는 공용 TSL 이 아니라 `QTableWidget`(체크 · 상태 열) — A00540 클립 표와 같은 모양. 상태: `-` / `exists` / `edited`(매니페스트) / `failed`.
- 공용: 메뉴 바 + `shell_integration`(Add to Start Menu) · `pin_style` · Shrink(272×155, A00240 v01.25 방식) · 로그 · `MOD_mayapyProcess`(진행률 팝업 · Cancel) · 페이지별 `QScrollArea`(A00240 v01.30 방식으로 창 자유 크기).
- 끝나면 결과 표 갱신 + "N generated, M skipped, K failed" + 출력 폴더 열기(`file_opener`).

---

## 5. A00570 UI (in-Maya)

```
┌ JALI Review ───────────────────────────────────────────────────────┐
│ Clips  [out_en_002/maya ][…]  (manifest 읽음)                        │
│ ┌ Clip | Frames | Status ┐  [◀ Prev] [Next ▶] [Swap]                │
│ │ ▶ …en_01 | 105-429 | edited │  Current: CLIP_RN → …en_01.mb         │
│ │   …en_02 | 445-490 | -      │  Edits: 0            [Save Clip Edits]│
│ └────────────────────────┘  [Discard Edits]  [Open Clip…]           │
│ Avatar [ … .mb][…] [Reference]   BlendShape [CHN_n_Face_xx_bs ▾]    │
│ [Connect ARKIT_OUT → BS]   connected 51 · missing 1 (tongueOut)     │
│ ☑ Allow edits on referenced animation curves (pref)                 │
│ Log                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

- **Build review scene**: 빈 씬에서 `Reference` 로 아바타, 클립 목록에서 첫 클립을 ns `CLIP` 으로 레퍼런스. 이미 `CLIP_RN` 이 있으면 그대로 쓴다.
- **Swap**(D12): `referenceQuery(CLIP_RN, editStrings=True)` 가 비었으면 `file(path, loadReference="CLIP_RN")`; 아니면 Save / Discard / Cancel 다이얼로그. 재생 범위 · 소리를 새 클립에 맞춤(도장의 start · frames, `jali_lipsync_audio` 를 타임슬라이더에).
- **Save Clip Edits**: 편집 목록 표시 → `file(saveReference=True, referenceNode="CLIP_RN")` → 편집 0 확인 → 매니페스트 `edited`.
- **Connect**: `CLIP:JALI:ARKIT_OUT.<t>` → `<BS>.<t>` 별칭 일치만, 이미 연결 Skip, 결과 표. 연결은 아바타 레퍼런스 편집으로 남으므로 검수 씬을 저장하면 다음에 그대로.
- **Allow edits** 체크박스 = 해당 optionVar(M0-1 에서 이름 확정) 를 켜고 끈다. 꺼져 있으면 키를 못 고치니 Swap 옆에 상태 표시.
- **Open Clip**(평가서 §2-10, Q6): 현재 클립 `.mb` 를 열고 아바타를 임시 레퍼런스(`REVIEW_AVATAR` ns) + Connect, `Save & Close` 가 임시 레퍼런스를 제거한 뒤 저장.

---

## 6. M0 — 코드 전에 mayapy 로 확정할 사실 (반나절)

| # | 확인할 것 | 예상 | 틀리면 |
|---|-----------|------|--------|
| M0-1 | "Allow edits on referenced animation curves" 환경설정의 optionVar 이름과 `cmds` 에서 켜는 법(Preferences > Settings > Animation 계열) | optionVar 하나 | A00570 체크박스를 안내 문구로 대체 |
| M0-2 | 켠 상태에서 레퍼런스된 animCurve 키를 옮기면 `referenceQuery -editStrings` 에 어떤 문장으로 쌓이나(`setAttr .ktv[n]` ?), 키 추가 · 삭제도 되나 | ktv/kix/kiy 류 setAttr | 편집 가능 범위를 안내에 적는다 |
| M0-3 | `file -saveReference` 뒤 클립 `.mb` 를 다시 열어 **키 값이 바뀌어 있고** 편집 목록이 비는가. 클립 안의 컨트롤러 레퍼런스(중첩)는 그대로인가 | 그렇다 | **설계 변경** — Open Clip 을 기본으로 올린다 |
| M0-4 | 편집을 남기고 `loadReference` 로 다른 클립을 넣으면 편집이 새 클립의 같은 이름 커브에 적용되나 | 적용된다 | Swap 검사를 경고로 낮춘다 |
| M0-5 | 레퍼런스된 `sound` 노드가 타임슬라이더 소리 메뉴에 뜨고 재생되나(GUI) | 뜬다 | A00570 Swap 이 검수 씬에 소리 노드를 직접 만든다 |
| M0-6 | 클립 생성 한 개 왕복: 30fps 설정 → 컨트롤러 레퍼런스(`JALI:`) → `keyer.apply_sequence` → `bake_ctl_keys(copy)` → DUMMY_IN 커브 삭제 → 저장 → 다시 열어 `JALI:CTL_PH_AAA.ty` 키 수 = txt 샘플 수, `ARKIT_OUT.jawOpen` 이 프레임마다 기대값, `failedEdits` 0 | 된다 | keyer 의 namespace 인자 · bake 의 `*:` 패턴 손질 |
| M0-7 | 컨트롤러 `.ma` 를 수정(예: 슬라이더 색)해 저장한 뒤 클립을 열면 키 · 연결이 그대로인가; CTL 이름을 바꾸면 `failedEdits` 에 잡히나 | 그대로 / 잡힌다 | Validate 표 열 조정 |
| M0-8 | 5 클립(`out_en_002`) 생성 시간 · 결과 `.mb` 크기 | 클립당 수 초, 수백 KB | 워커 진행률 단위 조정 |

M0 스크립트는 scratchpad 에 두고 결과를 이 문서 §10 에 적는다. **원본 컨트롤러 · 음성 파일은 수정하지 않는다**(복사해서).

---

## 7. 단계

| 단계 | 내용 | 완료 조건 |
|------|------|-----------|
| **M0** | §6 실측 | 표 8줄 모두 채움, D12 확정 |
| **M1** | P0 승격 — `Framework/jali/`(A00540 코어 이동 + 재노출) · `mayapy_runner` · `MOD_mayapyProcess` 승격(A00210 재노출) · `bake.py` 이식 | A00540 `tests/run_all.py` 132 · A00210 워커 17 + UI 14 그대로 통과, A00540 v01.03 · A00210 v01.40 (코드 이동만, 기능 변화 없음) |
| **M2** | A00560 코어 — `source_scan` · `manifest` · `jobs` · `worker.py generate` | mayapy 로 `out_en_002` 5 클립 생성, M0-6 검사 5개 모두 통과, Skip/Overwrite/backup 동작 |
| **M3** | A00560 UI — Batch 탭 + 진행률 · Cancel · 로그 · prefs · Shrink/Pin/Start Menu · 아이콘 · exe spec | 오프스크린 UI 시험(가짜 워커 = python) + 실제 mayapy 1회 |
| **M4** | A00560 Validate 탭 + `worker.py validate` + Repath | 컨트롤러를 복사본으로 바꿔 Repath → failedEdits 0 |
| **M5** | A00570 코어 — `review_scene`(build · swap · pending · save_reference) · `arkit_connect` | mayapy 시험: 교체 뒤 연결 유지, 편집 저장 뒤 클립 재열기 값 확인, 편집 있는 Swap 차단 |
| **M6** | A00570 UI + 드롭 설치 + 안내 문서 둘 + README 표 + WORKLOG + 메모리 | 마야 GUI 눈 확인(사용자) |
| **M7** (2단계) | P4 — JUN_JALI `cli.py`(`run_batch` 헤드리스, 인자 = wav 폴더 · 언어 · 출력) + A00560 `Convert` 단계(`.venv` 경로 prefs) | `src_en` 에서 바로 5 클립 |

버전: A00560 v01.00(M2~M4), A00570 v01.00(M5~M6). 커밋은 단계마다(M1 은 "refactor(Framework): jali · mayapy 승격" 따로).

---

## 8. 검증 목록

| ID | 무엇을 | 어떻게 |
|----|--------|--------|
| T1 | `Framework/jali` 승격 뒤 A00540 동작 불변 | A00540 tests 132 + 매핑 json 경로 변경 확인 |
| T2 | `source_scan` | out_en_002(정상 5) · src_en(22열 없음 → 안내) · json 없는 txt · `_fNNNN` 이 없는 이름도 **같은 결과**(이름을 안 읽는다) · 표에서 고친 Start 가 job 에 그대로 |
| T3 | generate 5 클립 | 키 수 · ARKIT_OUT 기대값(A0030 verify T8 의 공식) · DUMMY_IN 연결 0 · fileInfo 도장 · 소리 노드 offset = start · fps ntsc · 재생 범위 |
| T4 | 덮어쓰기 정책 | Skip 은 mtime 불변, Overwrite 는 바뀜, backup 은 `backup/<이름>_01.mb` |
| T5 | 취소 · 실패 | 3번째에서 cancel_flag → 2개 생성 후 멈춤, 종료 코드 0; 깨진 txt 하나 → 그 클립만 failed |
| T6 | Validate | 정상 5 → 전부 OK; CTL 이름 바꾼 컨트롤러 복사본 → failedEdits 표시; Repath 뒤 OK |
| T7 | Review 코어(mayapy) | build → connect 51/52 보고 → 키 편집 → Swap 차단 → Save → 클립 재열기 값 변경 → Swap 성공 → 연결 유지 |
| T8 | UI 오프스크린 | A00560 Batch · Validate(가짜 워커) · A00570(가짜 cmds 없이 UI 만) |
| T9 | 실기 | 사용자 눈 확인: 변환기 → Batch → Review 교체 · 편집 · 저장 한 바퀴 |

---

## 9. 질문 (답이 없으면 권장안으로)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | 툴 배치 — standalone `A00560` + in-Maya `A00570` 두 개로 가나, 하나로 묶나 | **두 개** (D1) |
| Q2 | 시작 프레임 기본 | **모든 클립 1**, 표의 Start 열에서 개별 수정 (D7, 파일 이름은 읽지 않음 — 사용자 확정) |
| Q3 | fps 기본 | **30 (ntsc)** — 예시 자료의 원본 영상이 30fps 였다. 다른 자료는 UI 에서 고른다 (D6) |
| Q4 | JaLi(Jaw/Lip) 키 | **Data**(VisemeNet 값) 기본, Fixed 0.6/0.6 선택 (D13) |
| Q5 | wav 를 클립 옆에 복사 | **ON** (D14) |
| Q6 | `Open Clip` 보조(클립 직접 열어 깊은 수정) | **포함** — M0-3 이 틀리면 이것이 기본이 된다 |
| Q7 | 실패 클립 정책 — 멈춤(변환기 방식) vs 계속(권장) | **계속**, 결과 표에서 실패만 다시 Run |
| Q8 | A00560 입력에 변환까지(P4) 를 1단계부터 넣나 | **2단계** — 먼저 변환기 출력 폴더로 시작 (평가서 §2-9) |

---

## 10. 진행표

| 날짜 | 단계 | 내용 |
|------|------|------|
| 2026-10-23 | 계획 | 평가서 + 이 계획서 작성. M0 전 |
| 2026-10-23 | 계획 수정 | 사용자 지시 — 시작 프레임을 파일 이름(`_f0105_0429`)에서 읽지 않는다. D7 · job json · UI · T2 · Q2 · Q3 갱신 |
