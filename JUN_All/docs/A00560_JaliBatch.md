# A00560_JaliBatch

VisemeNet Converter(`JUN_JALI`) 가 만든 **변환 결과 폴더**(대사마다 22열 txt + `.visemenet.json` + wav)를 받아
**대사마다 마야 클립 `.mb` 하나**를 만드는 standalone PySide 툴. 마야 밖에서 돌고, 마야 일은 **mayapy 워커 한 프로세스**가
클립 N 개를 순서대로 처리한다. 만든 클립은 짝 툴 **`A00570_JaliReview`** 가 마야 안에서 레퍼런스로 검수한다.

- **버전**: v01.01 (2026-10-26) — 더블클릭 실행 파일 `Run_JaliBatch.bat`, Python 3.14 · Windows 10 지원. v01.00 첫 버전
- **아키텍처**: (B) standalone PySide6 (`python launch.py` / `build_exe.bat`), 마야 일은 `app/maya/worker.py` (mayapy)
- **짝**: `A00570_JaliReview`(검수) · `A00540_JaliLipSync`(마야 안에서 클립 하나를 바로 키) · `JUN_JALI`(변환기 · STT)
- **공용 코어**: `Framework/jali` ([Framework_jali](Framework_jali.md)) · mayapy 러너 `Framework/core/mayapy_runner.py` + `Framework/qt/MOD_mayapyProcess_qt_v01.py`
- **계획 · 평가**: [plans/A00560_JaliBatch_plan.md](plans/A00560_JaliBatch_plan.md) · [plans/A00560_JaliBatch_pipeline_review.md](plans/A00560_JaliBatch_pipeline_review.md)

---

## 1. 클립이란

```
<name>.mb  =  빈 씬(fps 30)  +  JALI 컨트롤러 레퍼런스 (ns JALI)  +  컨트롤러 채널에 베이크된 키  +  <name>.wav 사운드 노드  +  fileInfo 도장
```

- 컨트롤러(`A0030_jali_slider_ctl_direct_arkit.ma`)는 **레퍼런스**다. 원본을 고치면 클립 N 개가 한 번에 따라온다(이름 · 결선이 같을 때).
- 키는 `DUMMY_IN_*`(A00540 과 같은 매핑 json)에 걸고 **컨트롤러(`CTL_PH_*` `.ty` · `CNT_JaLi` `.tx/.ty`)로 복사**(키 수 · 탄젠트 그대로)한 뒤
  DUMMY_IN 의 커브는 지운다. 커브 이름은 `JALI_<ctl>_<attr>`. 클립 안에 남는 것은 animCurve 와 레퍼런스 편집(연결 끊기 · 잇기)뿐이다.
- `ARKIT_OUT`(ARKit 52) 은 컨트롤러가 계산하므로 클립을 레퍼런스한 검수 씬에서 `CLIP:JALI:ARKIT_OUT.*` 을 블렌드셰이프에 이으면 된다.
- 출력 폴더에 `jali_clips.manifest.json` — 설정 + 클립마다 `start · end · frames · status(generated / edited / failed) · 시각`.
  A00570 의 클립 목록 · 재생 범위가 여기서 나온다(레퍼런스된 클립의 fileInfo 는 검수 씬에서 보이지 않는다).

## 2. 실행 — `Run_JaliBatch.bat` 더블클릭

```
tools/A00560_JaliBatch/
├── Run_JaliBatch.bat   ← 이것을 더블클릭. 처음 한 번은 환경을 만들고(콘솔 창, 1 ~ 2 분) 그 다음부터는 바로 창이 뜬다(콘솔 없음)
├── setup_env.bat       환경만 다시 만들 때 (옵션 --force = 환경 다시, --yes = 묻지 않고 전용 파이썬 다운로드)
└── setup_env.log       설치 기록 (문제가 생기면 이 파일)

%USERPROFILE%\.jun_jalibatch\      ← 만들어지는 것은 전부 여기 (툴 폴더 밖)
├── venv\                 PySide6 Essentials 가 든 파이썬 환경 (약 90 MB)
├── python\               쓸 수 있는 파이썬이 없을 때만 — 전용 Python 3.11.9
└── prefs.json            툴 설정 (mayapy 경로 등)
```

- **필요한 것**: Windows 10 / 11 + **64-bit Python 3.10 이상** (Python **3.14** 만 있는 PC 도 된다 — PySide6 는 abi3 휠이라 3.14 에 그대로 설치된다).
  `setup_env.bat` 이 `py -3.14 … -3.10` → PATH 의 `python` → `.jun_jalibatch\python\` 순으로 **실제로 실행해 버전을 읽어** 고른다(새 Python 설치 관리자의
  `py -3.11` 은 없는 버전이어도 오류만 찍고 종료 코드 0 이라 종료 코드를 믿지 않는다 — Windows 10 보고). 쓸 수 있는 파이썬이 없으면
  **전용 Python 3.11.9** 를 `.jun_jalibatch\python\` 에 받아 쓴다(python.org NuGet, 17 MB, SHA-256 확인, 시스템에 설치하지 않음 — JUN_JALI 와 같은 루틴).
- **환경은 툴 폴더 밖** `%USERPROFILE%\.jun_jalibatch\venv\` 에 만든다(환경 변수 `JUN_JALIBATCH_HOME` 으로 바꿀 수 있다). 이유는 **Windows 260자 경로 한도**:
  PySide6 휠(Essentials 도) 안에 151자짜리 경로(`PySide6\qml\Qt\labs\assetdownloader\…\…init.cpp.obj`)가 있어 환경 루트가 약 85자를 넘으면 롱패스를 켜지 않은 PC 에서
  pip 가 `No such file or directory` 로 실패한다(실측 — 이 저장소의 툴 폴더는 86자). 패키지는 PySide6 **Essentials**(QtWidgets · QtGui · QtCore · QtSvg, 약 90 MB) —
  전체 PySide6(WebEngine · QML 포함 250 MB)는 쓰지 않는다. PC 의 다른 파이썬 · conda 환경 변수(`PYTHONPATH` 등)는 bat 이 비우고 시작한다.
- 자가 검사(`app/selftest.py`): PySide6 import → Framework · 툴 import → 창을 오프스크린으로 생성 → mayapy 탐색(없으면 경고만).
- **마야는 mayapy 만 쓴다** — `Program Files\Autodesk\Maya*\bin\mayapy.exe` 중 최신을 자동으로 잡고 칸에서 바꿀 수 있다
  (설정은 `%USERPROFILE%\.jun_jalibatch\prefs.json`). 마야가 없는 PC 에서는 창은 뜨지만 Run · Validate 가 mayapy 를 요구한다.
- 창 안 `File > Add to Start Menu` 로 시작 메뉴 바로가기(venv 의 pythonw 를 가리킨다). 환경을 만든 파이썬을 지우면 `Run_JaliBatch.bat` 이
  깨진 환경을 알아서 다시 만든다. 개발 실행은 `python launch.py`(PySide6 가 있는 파이썬), exe 는 `build_exe.bat`(pyinstaller 별도 설치).

**확인 (2026-10-26)**: 이 PC(Python 3.11 + 3.14 NuGet 사본)에서 **가짜 `py` 런처(오류 출력 · 종료 코드 0) + PATH 에 Python 3.14.9 만 + `PYTHONPATH` 오염**
환경을 꾸며 `Run_JaliBatch.bat --no-launch` → 3.14 발견 · `.jun_jalibatch\venv` 생성 · PySide6 Essentials 6.12 설치 · 자가 검사 통과, 그 3.14 환경으로 test_core 33 · test_ui 30 통과.
(첫 시도는 툴 폴더 안 `.venv` 였고 전체 PySide6 도, Essentials 도 260자 한도에 걸려 실패 → 환경을 사용자 폴더로 옮겨 통과.)
실제 Windows 10 PC 와 전용 파이썬 다운로드 경로(이 PC 에는 3.14 가 있어 다운로드가 일어나지 않는다)는 미확인 — JUN_JALI 의 같은 루틴은 모사 검증됨.

## 3. Batch 탭

```
┌ JUN JALI Batch v01.00 ───────────────────────────────────────────  [Shrink] [Pin] ┐
│ File  Help                                                                         │
│ mayapy [C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe        ][...][Detect]   │
│ ┌ Batch ┐┌ Validate ┐                                                              │
│ Paths   Source     […\out_en_002                    ][...][Scan]                   │
│         Controller […\A0030_jali_slider_ctl_direct_arkit.ma ][...]                 │
│         Output     [<source>/maya                   ][...]                         │
│ Clips   ☑ │ Clip                          │ Start │ Frames │ WAV          │ Status │
│         ☑ │ 0030_vivian_en_01_f0105_0429  │   1   │  324   │ …_01.wav     │ -      │
│         ☑ │ 0030_vivian_en_02_f0445_0490  │   1   │   45   │ …_02.wav     │ exists │
│         [All] [None]  5 clip(s) - 5 checked, 869 frames total at 30 fps            │
│ Settings Start [1] [Apply to all]  fps [30 ▾]  Mapping [jali_slider_dummy_in ▾]    │
│          JaLi (•) From data ( ) Fixed Jaw [0.60] Lip [0.60]                         │
│          Existing [Skip existing ▾] [x] Copy WAV next to clip [x] Keep edited clips │
│ [            Run            ] [ Open Output Folder ]                               │
│ Log                                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Source** — 변환기 출력 폴더. `Scan` 은 **22열 txt 가 읽히는 이름만** 클립 후보로 올린다(대본 txt 는 "not a VisemeNet output" 으로
   건너뛴다). json 이 없으면 WARN(길이는 wav 로), **wav 가 없으면 제외**(클립엔 소리가 있어야 한다). 22열 txt 가 하나도 없으면
   "Run VisemeNet Converter first (JUN_JALI)" 안내.
2. **Controller** — JALI 슬라이더 컨트롤러 `.ma`. 모든 클립에 네임스페이스 `JALI` 로 레퍼런스된다.
3. **Output** — 비우면 `<source>/maya`. 클립 `.mb` · wav 복사본 · `backup/` · 매니페스트가 여기.
4. **표** — `Start` 는 **모든 클립 같은 값**(Settings 의 Start → Apply to all)에서 시작해 **칸을 직접 고칠 수 있다**(매니페스트에 남아 다음
   Run 에도 그대로). **파일 이름에서 프레임을 읽지 않는다** — 예시 자료의 `_f0105_0429` 는 그 자료만의 표기다. `Frames` 는 wav 길이를
   아래 fps 로 환산한 수(모델 출력은 끝 0.32 s 가 짧아 txt 가 아니라 wav 기준). `Status`: `-` / `exists` / `edited`(A00570 에서 손본 클립) / `failed`.
5. **Settings** — `fps` 기본 30(ntsc), 콤보에 직접 숫자를 쳐도 된다. `Mapping` 은 `Framework/jali/mappings/*.json`.
   `JaLi` From data(모델 Jaw/Lip) / Fixed(값 2개). `Existing`: **Skip**(기본) / Overwrite / Overwrite with backup(`backup/<name>_NN.mb`).
   `Keep edited clips`(기본 ON)이면 `edited` 클립은 덮지 않는다 — 끄고 덮으려 하면 한 번 더 묻는다(손으로 고친 키가 날아가는 유일한 경로).
6. **Run** — 진행 팝업(클립 이름 · Cancel). 취소는 **현재 클립이 끝난 뒤**. 실패한 클립은 `failed` 로 적고 **다음 클립을 계속** 한다 —
   결과 표에서 실패만 다시 Run 하면 된다. 끝나면 "N generated, M skipped, K failed" 와 함께 Validate 탭의 폴더가 채워진다.

## 4. Validate 탭

클립 폴더의 `.mb` 를 mayapy 로 **열기만 하고** 점검한다. 컨트롤러를 바꾼 날 N 개를 한 번에 확인하는 용도.

| 열 | 뜻 |
|----|-----|
| Manifest | 매니페스트의 상태 (`edited` 노랑 · `failed` 빨강) |
| Controller / Loaded | 클립 안 `JALI` 레퍼런스의 파일 · 로드 여부 |
| Failed edits | **빨강이면 컨트롤러의 노드 이름이 바뀌어** 클립의 결선 · 커브 연결이 실패한 것 (`referenceQuery -failedEdits`) |
| Baked / Keys | animCurve 가 붙은 컨트롤러 채널 수(24 = 슬라이더 22 + JaLi 2) · 키 합계 |
| DUMMY_IN | DUMMY_IN 에 남은 커브 수 (0 이어야 정상) |
| Stamp | `ok` / `changed`(노랑 — 컨트롤러 파일이 클립을 만든 뒤 수정됐다, 값만 바뀌었다면 문제 없음) / `none`(A00560 이 만든 클립이 아님) |

- **Repath** — `Repath to` 의 컨트롤러로 레퍼런스 경로를 바꾸고 **그때만 저장**한다(선택한 행, 없으면 전부). 경로가 같으면 바꿀 필요가 없다
  (레퍼런스라 원본 수정이 자동으로 따라온다).

## 5. 알아 둘 것

- **클립 길이는 wav 기준**이고 키는 모델 줄 수까지만 — 마지막 키 값이 끝까지 유지된다(A00540 과 같다).
- **fps 를 컨트롤러 레퍼런스보다 먼저** 건다(워커 1단계). keyer 가 씬 fps 로 샘플하기 때문. 클립을 24 fps 로 만들면 키 수가 줄어든다.
- 컨트롤러를 **이름이 바뀌게** 고치면 N 개 클립의 레퍼런스 편집이 조용히 실패한다 → Validate 의 Failed edits 로 잡는다. 값 · 색 · 범위만
  바꾼 것은 안전하다(실측 M0-7).
- mayapy 기동 4 ~ 5 초 + 클립당 0.2 ~ 0.5 초(예시 5 클립 5.5 초). 클립 `.mb` 는 50 ~ 150 KB.
- 변환(TensorFlow · MFA · STT)은 이 툴이 부르지 않는다 — 변환기 출력 폴더가 입력이다. 2단계(P4, `cli.py` 호출)는 계획서 §7 M7.

## 6. 구조 (개발자용)

```
A00560_JaliBatch/
├── launch.py · launch.spec · build_exe.bat · requirements.txt
├── app/config/version.py · app_meta.py (AUMID · 아이콘 · 시작 메뉴 · worker_path · guide_doc)
├── app/core/
│   ├── source_scan.py   scan(folder) -> ScanResult(clips[ClipSource], skipped, hint)  (Maya 비의존)
│   ├── manifest.py      Framework/jali/clip_manifest 재노출 (A00570 도 읽는다)
│   ├── jobs.py          generate_job / validate_job dict, fps 콤보 · 덮어쓰기 상수
│   └── prefs.py         ~/.jun_jalibatch/prefs.json
├── app/maya/worker.py   mayapy 가 실행. generate(클립마다: fps → 레퍼런스 → keyer → bake → wav → 도장 → 저장) · validate(열기 · 점검 · repath)
├── app/ui/main_window.py (메뉴 · Shrink/Pin · mayapy 줄 · 탭 · 로그) · batch_tab.py · validate_tab.py
├── icon/A00560_JaliBatch.svg / .png / .ico
└── tests/test_core.py(33, python) · test_worker.py(32, mayapy 실제 워커) · test_ui.py(30, PySide6 오프스크린 + 실제 mayapy 1회)
```

워커 프로토콜은 `Framework/core/mayapy_runner.py`(`JUNMSG {json}` log / progress / result / error, Cancel = 플래그 파일) —
A00210 Maya 탭과 같다. 얼린 exe 는 `launch.spec` datas 로 `app/maya` 와 `Framework/jali` · `Framework/core` 를 디스크에 싣는다(워커가 .py 를 읽어야 한다).

**확인 기록 (2026-10-26, mayapy 2024 · Windows 11)**: M0 실측 8항목(계획서 §11) → 코어 33 · 워커 32(5 클립 생성 · 재열기 키 수 = 프레임 + 1 ·
failedEdits 0 · DUMMY_IN 0 · Skip/Overwrite/backup · 3번째에서 취소 · 깨진 txt 하나만 failed · Validate 5 ok · 이름 바꾼 컨트롤러 Repath → failedEdits 2 ·
되돌리면 0) · UI 30(가짜 워커 + 실제 mayapy QProcess 1회). **실제 화면에서 창을 열어 본 것은 아직**(오프스크린만) · exe 빌드 미실행.
