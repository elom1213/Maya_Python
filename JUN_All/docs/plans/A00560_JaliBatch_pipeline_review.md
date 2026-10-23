# JALI 대량 변환 → 마야 클립 파일 → 레퍼런스 검수 — 계획 평가와 개선안

> **작성** 2026-10-23 · **갱신** 2026-10-23 (시작 프레임을 파일 이름에서 읽지 않는다 — §2-5, 사용자 지시) · 사용자가 설명한 파이프라인(아래 §0)을 **그대로 코드로 옮기기 전에** 마야 레퍼런스 동작 기준으로 평가한 문서.
> 결론만 보려면 §1. 툴 제작 계획은 짝 문서 [A00560_JaliBatch_plan.md](A00560_JaliBatch_plan.md).
> 용어(사용자 지정): **JALI 툴** = `JUN_JALI` 저장소(VisemeNet 변환기 · MFA) · **JALI 컨트롤러** = `0035_maya_src_rig\02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma`.
> 관련: `A00540_JaliLipSync`(txt → DUMMY_IN 키, 코어를 그대로 쓴다) · `A00210_FileManager` Maya 탭(standalone 에서 mayapy 워커를 돌리는 선례) ·
> JUN_JALI `docs/0090_jali_slider_ctl_plan.md`(컨트롤러 구조 · `bake_ctl_keys`) · 메모리 `wip-jali-slider-ctl` `maya-reference-import-traps`.

---

## 0. 사용자의 계획 (요약)

```
src_en/  <이름>.wav + <이름>.txt(대본)  × N 개
   │  JALI 툴 (VisemeNet + MFA)  → <이름>.txt(22열 비짐) + .visemenet.json
   ▼
클립 .mb  × N 개   = 빈 씬 + JALI 컨트롤러 **레퍼런스** + DUMMY_IN 에 키 → 컨트롤러로 **베이크** → 저장 (<이름>.mb)
   │        컨트롤러 원본이 바뀌면 레퍼런스만 갈아 끼운다
   ▼
검수 씬          = 빈 씬 + 클립 .mb **레퍼런스** + 아바타 **레퍼런스**, 클립의 ARKIT_OUT(52) → 아바타 블렌드셰이프 연결
                  "Allow edits on referenced animation curves" 를 켜고 어색한 키를 고치면 **그대로 저장**된다(고 기대)
                  다른 클립을 보려면 클립 레퍼런스를 다른 .mb 로 **교체**만 한다
```

예시 자료: `JUN_JALI_Voice/0060_Vivian_voice/src_en`(wav + 대본 5쌍, 이름 `0030_vivian_en_01_f0105_0429` …),
변환 결과 `out_en_002`(22열 txt · `.visemenet.json` · `.phones.json`).

---

## 1. 판정 — 뼈대는 좋다, 저장 · 교체 두 곳이 틀어져 있다

| 평가 | 내용 |
|------|------|
| **좋은 점 ①** | **클립 = 컨트롤러 레퍼런스 + 자기 animCurve**. 컨트롤러 노드는 클립 파일 안에 복사되지 않고, 클립이 가진 것은 animCurve 노드와 "DUMMY_IN 연결을 끊고 animCurve 를 컨트롤러 채널에 붙였다" 는 **레퍼런스 편집**뿐이다. 컨트롤러 원본을 고치면 N 개 클립이 한 번에 따라온다. 올바른 구조다 |
| **좋은 점 ②** | **검수 씬에서 클립을 레퍼런스로 교체**. 아바타(무겁다)는 그대로 두고 클립(가볍다)만 갈아 끼우니 빠르다. `file -loadReference <refNode> <새 경로>` 한 번이고, 노드 이름이 같으면 ARKIT_OUT → 블렌드셰이프 연결(아바타 쪽 레퍼런스 편집)이 유지된다 |
| **좋은 점 ③** | 변환(TensorFlow · MFA)과 마야 작업이 **다른 프로세스**로 떨어져 있다. 변환기는 이미 있으니(`Run_VisemeNet_Converter.bat`) 새 툴은 변환 결과 폴더에서 시작하면 된다 |
| **틀어진 곳 ①** | **"수정하면 그대로 저장된다" 가 아니다.** 레퍼런스된 animCurve 의 키를 고치면 그 변경은 **검수 씬의 레퍼런스 편집 목록**에 쌓이고, 클립 `.mb` 는 Ctrl+S 로는 **바뀌지 않는다**. 클립 파일에 쓰려면 Reference Editor **File > Save Reference Edits** (`cmds.file(refNode, saveReference=True)`)를 따로 실행해야 한다. 이 한 단계가 빠지면 Unreal 로 나가는 클립은 고친 적 없는 파일이다 → §2-1 |
| **틀어진 곳 ②** | **편집을 남긴 채 교체하면 다음 클립에 묻어 간다.** 레퍼런스 편집은 **노드 이름**으로 기록된다. 모든 클립은 같은 컨트롤러를 같은 네임스페이스로 레퍼런스하고 베이크 animCurve 이름도 같은 규칙(`CTL_PH_AAA_translateY` 류)으로 생기므로, 클립 01 에서 고친 키 편집이 저장되지 않은 채 02 로 교체되면 마야는 그 편집을 **02 의 같은 이름 커브에 적용**한다. 교체 전 "편집 0건" 을 강제해야 한다 → §2-2 |
| **빠진 곳 ③** | 컨트롤러 원본 갱신은 **노드 · 어트리뷰트 이름과 direct 결선이 유지될 때만** 안전하다. 이름이 바뀌면 N 개 클립의 레퍼런스 편집이 조용히 실패한다(`referenceQuery -failedEdits`). 클립을 한꺼번에 점검하는 **Validate** 작업과, 클립마다 어느 컨트롤러 버전으로 만들었는지 **도장**이 필요하다 → §2-3 |

> 정리: 구조(①②③)는 그대로 가져가고, **"저장" 을 명시 단계로**, **"교체" 앞에 편집 검사**를 넣고, **Validate** 를 더하면 된다.

---

## 2. 개선안 (중요한 순서)

### 2-1. 저장은 "Save Clip Edits" 버튼 한 가지 길로

- 검수 툴의 버튼 **`Save Clip Edits`** = `referenceQuery -editStrings` 로 편집을 보여 주고 → `file -saveReference` → 저장 뒤 편집 목록이 비었는지 확인 → 매니페스트(§2-6)에 `edited` 와 시각을 기록.
- 검수 씬 자체는 **저장하지 않아도 된다**(아바타 · 연결만 있는 껍데기). 저장하더라도 편집은 이미 클립으로 빠져 있어 중복되지 않는다.
- **M0 실측** 항목: "Allow edits on referenced animation curves" 환경설정의 정확한 optionVar 이름, 켠 상태에서 키를 옮기면 편집이 `setAttr ".ktv[n]"` 류로 쌓이는지, `saveReference` 뒤 클립 `.mb` 를 mayapy 로 다시 열어 키 값이 바뀌어 있는지 (계획서 §6 M0-1 ~ M0-3).

### 2-2. 교체(Swap) 앞에 편집 검사

- `Swap Clip` 은 **편집이 0건일 때만** 바로 실행. 편집이 있으면 **Save / Discard / Cancel** 세 갈래 — Discard 는 편집 제거(`file -cleanReference` 또는 `referenceEdit -removeEdits`) 뒤 교체.
- **M0 실측**: 편집을 남기고 교체하면 정말 다음 클립에 적용되는지(같은 이름이므로 적용되리라 예상) — 적용된다면 위 검사는 필수, 안 된다면 경고로 낮춘다 (M0-4).

### 2-3. Validate 작업 + 컨트롤러 도장

- 클립 생성 때 `fileInfo` 에 `jun_jali_clip = {source_wav, controller_path, controller_mtime, mapping, fps, start, generated_at, A00560 version}` 을 쓴다(클립은 자기 파일이라 fileInfo 를 쓸 수 있다).
- **Validate** (mayapy 워커, 열기만): 클립마다 열어 ① 컨트롤러 레퍼런스 경로 · 로드 상태 ② `failedEdits` 0건 ③ 베이크된 채널 수 · 키 수 ④ DUMMY_IN 에 남은 연결 0 ⑤ 도장의 controller_mtime 과 현재 파일 비교 → 표로. 컨트롤러를 바꾼 날 N 개를 이걸로 한 번에 확인한다.
- 컨트롤러 교체 자체는 클립을 열지 않아도 된다(경로가 같으면 자동). 경로를 바꾸는 경우만 Validate 에 **Repath** 옵션(`file -loadReference` 새 경로 → 저장).

### 2-4. 네임스페이스와 이름 고정

| 대상 | 네임스페이스 | 이유 |
|------|------------|------|
| 클립 안의 컨트롤러 | **`JALI`** (모든 클립 동일) | 검수 씬 연결이 `CLIP:JALI:ARKIT_OUT.jawOpen` 으로 늘 같아야 교체 뒤 연결이 살아 있다 |
| 검수 씬의 클립 | **`CLIP`** (고정, 교체해도 유지) | 같은 이유. 레퍼런스 노드 `CLIP_RN` 하나를 툴이 찾는다 |
| 검수 씬의 아바타 | 아바타 파일 그대로 | 툴이 정하지 않는다. 연결 규칙만 네임스페이스 무관하게 |

- 베이크 animCurve 이름은 `pasteKey` 가 만든 기본 이름을 쓰지 말고 **`JALI_<ctl>_<attr>`** 로 rename 해 두면 편집 문자열을 읽을 때 사람이 알아본다(2-2 의 "같은 이름" 성질은 그대로 — 그래서 검사가 필요하다).

### 2-5. 시작 프레임 · fps · 소리

- **시작 프레임은 파일 이름에서 읽지 않는다** (사용자 지시 2026-10-23). 예시 자료의 `_f0105_0429` 는 이 자료만의 표기이고, 프레임이 이름에 없는 파일이 일반적일 수 있다. 파일 이름에 의존해 데이터를 만들면 이름 규칙이 다른 폴더에서 조용히 틀린다. 시작 프레임은 **모든 클립에 같은 값 하나**(UI 스핀박스, 기본 1)로 두고, 클립마다 다르게 두고 싶으면 표의 Start 열을 **손으로 고치거나 CSV/매니페스트로 넣는다**. 파일 이름은 클립 `.mb` 이름을 정할 때만 쓴다.
- **fps 는 명시**해야 한다. mayapy 의 새 씬은 film 24, 컨트롤러 `.ma` 도 film 이고, A00540 `keyer` 는 **씬 fps 로 샘플**한다. 클립 씬은 컨트롤러를 레퍼런스하기 전에 `currentUnit -time ntsc`(옵션, 기본 30)를 건다. 클립 재생 범위 = `[start, start + 프레임 수]`.
- 소리: `cmds.sound(file=wav, offset=start)` 노드를 클립에 넣는다(A00540 `scene.attach_sound` 와 같은 이름 `jali_lipsync_audio`). 검수 씬에서 레퍼런스된 사운드 노드가 타임슬라이더 소리 메뉴에 뜨는지 **M0-5** 에서 확인. wav 는 절대 경로라 PC 를 옮기면 끊긴다 → 옵션 "Copy WAV next to clip" (기본 ON).

### 2-6. 매니페스트 json 하나로 묶기

출력 폴더에 `jali_clips.manifest.json` — 생성 설정(컨트롤러 경로 · 매핑 · fps · 시작 모드 · 변환기 · A00560 버전) + 클립마다 `{name, wav, txt, mb, start, end, frames, status: generated|edited|failed, generated_at, edited_at}`.
검수 툴의 **클립 목록 · 이전/다음**이 이 파일을 읽고, Validate 가 갱신한다. 폴더만 보고도 "어디까지 됐나" 를 안다.

### 2-7. 베이크 뒤 정리

`bake_ctl_keys(mode='copy')` 는 DUMMY_IN → 컨트롤러 연결을 끊고 키를 복사하지만 **DUMMY_IN 의 animCurve 는 남긴다**(JUN_JALI examples 코드). 클립에는 진실이 한 곳이어야 하므로 복사 뒤 DUMMY_IN 커브를 **지운다**. 그러면 DUMMY_IN 은 기본값(음소 0, Jaw/Lip 0.6)으로 돌아가고 컨트롤러는 더 이상 DUMMY_IN 을 보지 않으니 결과는 같다. (`bake` 모드로 샘플한 채널도 동일.)

### 2-8. 덮어쓰기 · 재생성 정책

- 클립 `.mb` 가 이미 있으면 **Skip(기본) / Overwrite / Overwrite with backup**(`backup/<이름>_NN.mb`, A00210 · A00220 과 같은 자리).
- 매니페스트 `status == edited` 인 클립을 Overwrite 하려 하면 **한 번 더 묻는다** — 손으로 고친 키가 날아가는 유일한 경로다.
- 변환기 품질이 좋아져 재생성할 때: "edited 는 건너뛰고 나머지만" 이 기본 체크.

### 2-9. 변환 단계는 입력으로만 — 처음에는 변환기 출력 폴더에서 시작

변환기(TensorFlow `.venv` · MFA)는 Python 3.11 전용 환경이고 마야 툴과 섞으면 설치 · 릴리즈가 모두 무거워진다. 새 툴의 **입력은 변환기 출력 폴더**(22열 txt + `.visemenet.json` + wav)로 잡고, 변환기 호출(`.venv\Scripts\python.exe` 로 헤드리스 CLI)은 **2단계**에 둔다. `src_en` 처럼 wav · 대본만 있는 폴더면 변환기를 먼저 돌리라고 안내(폴더 검사에서 22열 txt 가 없으면 메시지).

### 2-10. 깊은 수정은 "클립을 직접 연다" 를 대안으로

레퍼런스 편집 층을 거치는 수정은 키 몇 개를 다듬는 데는 좋지만, 커브를 크게 갈아엎을 때는 편집 문자열이 길어지고 느려진다. 검수 툴에 **`Open Clip`**(클립 `.mb` 를 직접 열고, 아바타를 **임시** 레퍼런스로 붙여 보고, 저장 전에 아바타 레퍼런스를 떼는 보조)을 둔다. 기본은 사용자의 레퍼런스 검수, 무거운 손질은 Open Clip.

### 2-11. ARKIT_OUT → 아바타 연결은 이름 매칭 + 규칙 파일

ARKIT_OUT 52 중 아바타에 없는 타겟(예: `tongueOut`, A00550 테스트 씬은 51개)이 흔하다. 연결은 **별칭 이름이 같은 타겟만** 붙이고 나머지를 표로 보고한다. 이미 연결된 타겟은 Skip 기본(A00550 과 같은 정책). 아바타별 예외는 `A00145_RigConnect` 규칙 json 과 같은 모양의 json 으로 저장해 재사용.

---

## 3. 바꾸지 않을 것 (사용자 계획 유지)

- 클립 파일 이름 = wav 이름 (`0030_vivian_en_01_f0105_0429.mb`), 포맷 `.mb`.
- 클립은 컨트롤러를 **레퍼런스**(임포트 아님). 컨트롤러 원본 갱신 = 레퍼런스 경로 그대로.
- 검수 = 빈 씬 + 클립 레퍼런스 + 아바타 레퍼런스 + 레퍼런스 교체. "Allow edits on referenced animation curves" 를 켜고 키를 고치는 흐름.
- 키는 `DUMMY_IN` 에 걸고 **컨트롤러로 베이크**해 애니메이터가 뷰포트 슬라이더의 키를 본다(JUN_JALI 0090 C8 의 결정 그대로).

---

## 4. 예상 비용 (실측 전 추정)

| 항목 | 추정 | 근거 |
|------|------|------|
| mayapy 기동 | 4 ~ 5 초, 1회 | A00210 워커 실측(2024) |
| 클립 1개 | 수 초 | 컨트롤러 `.ma` 레퍼런스 + 23 어트리뷰트 × ~324 프레임 ≈ 7.5k `setKeyframe` + copyKey 23 + 저장 |
| 100 클립 | 몇 분 | 위 × 100, 한 프로세스에서 순서대로 (취소는 클립 경계) |
| 검수 교체 | 1 ~ 2 초 | 클립 파일은 animCurve 수십 개 + 레퍼런스 한 줄 |

---

## 5. 열린 질문 (계획서 §9 로 넘김)

Q1 툴을 어디에(새 standalone `A00560` + in-Maya 검수 `A00570` 권장) · Q2 시작 프레임 기본(모든 클립 1, 표에서 개별 수정) · Q3 fps 기본(30 권장) · Q4 JaLi(Jaw/Lip) 키를 데이터대로 / 고정 · Q5 wav 복사 여부 · Q6 Open Clip 보조 포함 여부.
