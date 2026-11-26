# 메타휴먼 JALI 혀 조절 더미 (`JALI_TONGUE_TUNE`) — 관찰 · 원인 · 작업 계획서

> **작성** 2026-11-26 · 상태: **계획 (구현 전)** · 위치: 처음 `JUN_JALI/docs/0150_mh_jali_tongue_tune_plan.md` 로 썼다가 같은 날 이 자리로 옮김(사용자 지시 — 작업은 Maya_Python `JUN_All` 세션에서) · 대상 Maya 2024 (mayapy 로 생성 · 검증, 마지막 눈 확인만 GUI)
> 원본 리그: `C:\JUN\JUN_Src_Rig\07_MH_sample_02\0010_sample_0050_JaLiMap.mb` — 0110 계획 (`JUN_JALI/docs/0110_jali_mh_dummy_plan.md`)으로 만든 JALI 더미 리그
> 관찰 씬: `D:\D__1010_PortFolio\00010_JALI_Brant\0010_Metahuman_01.mb` — 위 리그를 네임스페이스 `MH` 로 레퍼런스(`oldRN`),
> `JUN_JALI_Voice\0070_Brant\00010_brant_kr\out_0010\brant_kr.txt` 를 A00540_JaliLipSync(Default 탭, 매핑 `jali_slider_dummy_in`)로 키를 넣은 결과
> 참고: 0110 (`JUN_JALI/docs/0110_jali_mh_dummy_plan.md`) §3 · §5.3 (혀 직접 경로 가중치) · 0120 (`JUN_JALI/docs/0120_jali_dummy_out_attrs_guide.md`) (angela 혀 실측) · `JUN_JALI/examples/build_mh_jali_dummy.py`

이 문서만 보고 작업을 끝까지 진행할 수 있게 썼다. 순서는 §8 단계표, 검증은 §9, 사용자가 정할 것은 §11 (답이 없으면 **권장값으로 진행**).

---

## 0. 요청 정리

| # | 요청 (원문 요지) | 이 계획 |
|---|------------------|---------|
| R1 | 입술은 무난, **혀 움직임 개선** | §2 원인 3개 → §5 노드망 |
| R2 | 아래 구간은 혀가 너무 올라가 **혀 뒷부분(밑면)이 보인다** → 안 보이게 | §1.3 구간 실측, §6 권장 초기값의 효과 계산 |
| R3 | 방법 1: `0050_JaLiMap` 의 노드를 고친 업데이트 파일 / 방법 2: `rig` 그룹에 **실시간으로 혀 움직임 정도를 조절하는 어트리뷰트를 가진 더미** / 그 밖의 좋은 방법 제안 | §3 방안 비교 — **방법 2 로 진행** (사용자 선호, 2026-11-26 "2번으로 하면 적응하기 좋을 것 같다"). 방법 1 은 방법 2 의 기본값으로 흡수된다 |
| R4 | 작업 계획서만 보고 진행 가능할 것 | 이 문서 |

문제 구간 (사용자 지정, 씬 30 fps · 시작 프레임 1):

| 구간 | 대사 | MFA 정렬(`brant_kr.phones.json`)에서 그 구간의 혀끝 자음 |
|------|------|------------------------------------------------------|
| 50 – 65 | 무대 | `t̚`(ㄷ)@58 → `ɛː`@60 |
| 100 – 160 | 캐릭터에 몰입하기만 하면 돼 | `ʎ`(ㄹ)@104 · `tʰ`(ㅌ)@108 · `ɾʲ`(ㄹ)@117 · `n`@129 · `n`@135 · `tʷ`(ㄷ)@137 |
| 180 – 260 | 그 순간 무대는 오직 나만의 세상이거든 | `n`@182 · `t̚`@188 · `n`@191 · `n`@193 · `n`@216 · `n`@224 · `d`@241 · `n`@243 |

세 구간 모두 **ㄴ · ㄷ · ㄹ · ㅌ (혀끝 자음) 바로 뒤에 입이 벌어지는 모음**(ㅐ · ㅓ · ㅏ)이 온다 — 혀끝이 올라간 채 입이 열리면 혀 밑면이 보인다.

---

## 1. 관찰 결과 (mayapy 2024, 2026-11-26)

### 1.1 씬 구조

- 시간 단위 `ntsc`(30 fps), 재생 1 – 781, 사운드 `jali_lipsync_audio` = `brant_kr.wav` offset 1.
- 레퍼런스 1개: `oldRN` → `C:/JUN/JUN_Src_Rig/07_MH_sample_02/0010_sample_0050_JaLiMap.mb`, 네임스페이스 `:MH`.
- 키는 **`MH:DUMMY_IN_*` 23개 어트리뷰트에만** (각 771 키, 프레임 1 – 771): `DUMMY_IN_PHONEMES` 16 · `DUMMY_IN_COARTIC` 5 (`FFF GK LNTD MMM WA_PEDAL`) · `DUMMY_IN_JALI.Jaw/Lip`.
  나머지 273 커브는 리그 안 SDK 커브.
- `MH:rig` 아래 `body_grp · head_grp · joints_grp · DMY_grp`. `DMY_grp` 아래 `dmy_in · dmy_out · DUMMY_IN_JALI · DUMMY_IN_PHONEMES · DUMMY_IN_COARTIC · dmy_in_jali_arkit · dmy_in_jali_mh`.
- mayapy 에서 열 때 `Cannot find procedure "internalTimeUnitStringToDisplayFPSString"` 오류 2줄 — GUI 전용 MEL 이 없어서 나는 것, 씬 내용과 무관.

### 1.2 혀 신호 경로 (리그에서 읽은 그대로)

```
DUMMY_IN_PHONEMES.* / DUMMY_IN_COARTIC.*
  → jali_bw_mh_<attr>   (blendWeighted, 아래 가중치)
  → jali_md_mh_<attr>   (× jali_md_weightJaw.output = Jaw/0.6 × weight)
  → jali_cl_mh_<attr>   (clamp 0~1)
  → dmy_in_jali_mh.<attr>
  → bw_dmy_CTRL_C_tongue_<ctrl>_y (blendWeighted, 부호)  → pma_dmy_* → GRP_dmy_CTRL_C_tongue_<ctrl>.ty → CTRL_C_tongue_<ctrl> (컨트롤러 자신의 ty 는 0, 부모 그룹이 움직인다)
  → CTRL_expressions.tongue*  → RigLogic → FACIAL_C_Tongue1~4 · TongueUpper/Lower · L/R_TongueSide
```

| `jali_bw_mh_*` | input 순서 · 가중치 (index: 소스 = 값) | 가는 곳 (`bw_dmy_*` 의 input · 부호) |
|-----------------|------------------------------------------|--------------------------------------|
| `tongueTipUp` | 0 `PH.LNTD` 0.61 · 1 `PH.RRR` 0.63 · 2 `PH.UUU` 0.20 · 3 `PH.SSH` 0.20 · **4 `CO.LNTD` 1.00** | `bw_dmy_CTRL_C_tongue_tipMove_y` input[0] **+1** |
| `tongueTipDown` | 0 `PH.GK` 0.44 · 1 `PH.SSS` 0.20 · 2 `PH.AAA` 0.20 · 3 `PH.Eh` 0.14 · 4 `PH.IEE` 0.20 · **5 `CO.GK` 1.00** | `bw_dmy_CTRL_C_tongue_tipMove_y` input[1] **−1** |
| `tongueBendUp` | 0 `PH.GK` 0.40 · 1 `PH.UUU` 0.20 · 2 `PH.OHH` 0.30 · 3 `PH.WWW` 0.20 · **4 `CO.GK` 0.46** | `bw_dmy_CTRL_C_tongue_bendTwist_y` input[0] +1 |
| `tongueUp` | 0 `PH.LNTD` 0.30 · **1 `CO.LNTD` 0.35** | `bw_dmy_CTRL_C_tongue_move_y` input[2] +1 (input 0 · 1 = `dmy_in.tongueOut` · `dmy_in_jali_arkit.tongueOut` × −0.826) |
| `tongueOutExtra` | 0 `PH.RRR` 0.15 | `bw_dmy_CTRL_C_tongue_inOut_y` input[2] −1 |

`PH` = `DUMMY_IN_PHONEMES`, `CO` = `DUMMY_IN_COARTIC`. 경유(ARKit) 경로의 혀 성분은 `tongueOut` 하나뿐(이 씬에서 최대 0.027) — 문제와 무관.

### 1.3 프레임별 실측 (1 – 781 전부 샘플, 문제 구간 158 프레임 vs 나머지 623)

| 값 | 문제 구간 최대 / 평균 | 나머지 최대 / 평균 |
|----|----------------------|--------------------|
| `CTRL_expressions.tongueTipUp` | 0.561 / **0.126** | 0.555 / 0.080 |
| `CTRL_expressions.tongueUp` | 0.192 / 0.050 | 0.193 / 0.030 |
| `CTRL_expressions.jawOpen` | 0.518 / 0.196 | 0.462 / 0.142 |
| `DUMMY_IN_PHONEMES.LNTD` | 0.599 / 0.157 | 0.600 / 0.093 |
| `DUMMY_IN_PHONEMES.RRR` | 0.382 / 0.099 | 0.360 / 0.055 |
| `DUMMY_IN_JALI.Jaw` | 0.318 / 0.295 | 0.314 / 0.292 (데이터 Jaw 는 거의 상수 ≈ 0.3 → 배율 Jaw/0.6 ≈ 0.5) |
| `tongueTipUp > 0.3` 인 프레임 | 35 / 158 (22 %) | 86 / 623 (14 %) |

대표 프레임 — `tipUp` 에 들어온 몫 (= 가중치 × 입력 × Jaw/0.6):

| 프레임 | 소리 | tipUp | jawOpen | PH.LNTD | PH.RRR | **CO.LNTD** |
|-------:|------|------:|--------:|--------:|-------:|------------:|
| 58 | 무**대** | 0.32 | 0.31 | 0.11 | 0.02 | **0.18** |
| 110 | 캐릭**터** | 0.44 | 0.28 | 0.14 | 0.10 | **0.23** |
| 130 | 하**면** | 0.38 | 0.40 | 0.14 | 0.00 | **0.24** |
| 195 | 무대**는** | 0.47 | 0.14 | 0.18 | 0.00 | **0.30** |

- 위 식(`clamp((Σ w·x)·Jaw/0.6, 0, 1) − tipDown`)으로 781 프레임 전부를 다시 계산하면 리그 값과 **오차 0.0000** — 아래 §6 의 효과 계산은 이 식으로 한 것이다.
- 혀 조인트 범위는 문제 구간과 나머지가 비슷하다 (`FACIAL_C_Tongue4.rx` 문제 −14.5 ~ 5.2°, 나머지 −16.3 ~ 4.6°). 즉 **문제 구간에만 있는 극단값이 아니라, 혀끝 올림이 잦고 입이 같이 열리는 것**이 차이다.
  `tipUp × jawOpen`(밑면이 보이는 정도의 대용값) 상위 40 프레임 중 7개만 문제 구간 → **같은 현상이 286 · 361 · 531 · 575 · 666 – 685 근처에도 있다** (§11 Q4).

---

## 2. 원인

| # | 원인 | 근거 |
|---|------|------|
| C1 | **`CO.LNTD` 가 `PH.LNTD` 와 같은 데이터** — 혀끝 올림이 1.61배로 들어간다 | A00540 매핑 `jali_slider_dummy_in.json` 이 `DUMMY_IN_COARTIC.LNTD ← LNTD` · `.GK ← GK` · `.MMM ← MBP` · `.FFF ← FV` 로, **음소와 같은 txt 열**을 동시조음에도 넣는다 (관찰 씬에서 두 값이 모든 프레임에서 같다). VisemeNet 에는 동시조음 열이 따로 없다. 그런데 0110 은 angela 의 COARTIC 을 "음소와 별개 신호" 로 보고 `CO.LNTD` 에 **1.00**(음소 0.61 의 1.6배)을 줬다 → 대표 프레임에서 tipUp 의 **50 – 64 %** 가 이 중복 몫. `tongueUp`(0.30 + 0.35) · `tongueTipDown` / `tongueBendUp` 의 `CO.GK` 도 같은 중복 |
| C2 | **`RRR` → 혀끝 올림 0.63** 은 영어 권설음(혀끝을 뒤로 말아 올림, 밑면이 보이는 동작) 값 | 한국어 ㄹ 은 혀끝이 잇몸을 한 번 치는 탄설음 `ɾ` / 설측음 `ʎ` — 말아 올리지 않는다. 모델은 ㄹ · ㅌ 근처에서 `R` 열을 낸다 (110 프레임 `RRR` 몫 0.10) |
| C3 | **입이 벌어질 때도 혀끝 올림을 줄이지 않는다** | 사람은 ㄴ · ㄷ 다음 모음으로 넘어가며 입을 열 때 혀끝을 이미 내린다. VisemeNet 커브는 모음 쪽으로 꼬리를 길게 끈다 (A00540 Smooth 를 켜면 더 길어질 수 있다). 결과적으로 `tipUp` 0.3 – 0.47 과 `jawOpen` 0.28 – 0.40 이 같은 프레임에 겹친다 |

0110 §11 에 적어 둔 위험("§3 은 전부 제안값 · 메타휴먼 혀가 더 크게 움직이면 전체를 줄인다")이 실제로 드러난 것이다. 0110 은 혀 값을 **GUI 로 확인하지 않은 채** 끝났다 (§12 "미확인").

---

## 3. 방안 비교

| 방안 | 내용 | 장점 | 단점 | 판단 |
|------|------|------|------|------|
| **1. 리그 가중치 수정본** | `jali_bw_mh_*` 가중치를 고정값으로 낮춰 다시 저장 | 단순, 노드 추가 없음 | 값을 바꿀 때마다 파일을 다시 만든다. 구간별 조절 불가 | 방법 2 의 **기본값**으로 흡수 |
| **2. 실시간 조절 더미** (채택) | `rig|DMY_grp` 에 `JALI_TONGUE_TUNE` — 혀 세기 · 동시조음 중복 · RRR · 입 벌림 억제 · 상한을 **키 가능한 어트리뷰트**로 | 씬을 연 채 슬라이더로 바로 보며 맞춘다. **구간마다 키를 줄 수도 있다**(예: 100 – 160 만 더 줄이기). 리그 하나로 여러 대사에 재사용. 기본값 "중립" 이면 기존 결과와 완전히 같다 | 노드 25개 추가 | **채택** (사용자 선호) |
| 3. 매핑 json 쪽 (A00540) | 한국어용 매핑 `jali_slider_dummy_in_kr.json` — `COARTIC.LNTD/GK` 를 빼거나(또는 배율), `RRR` 을 약하게 | 데이터 단계에서 고침, 리그 무수정 | 지금 A00540 매핑은 타겟별 배율이 없다(전체 `viseme_scale` 하나) → A00540 수정 필요, 바꿀 때마다 Apply 다시 | 보류 — 방법 2 로 맞춘 값을 나중에 json 기본값으로 옮길 수 있다 (§10 후속) |
| 4. 애니메이션 레이어 수작업 | 문제 구간에서 `DUMMY_IN_PHONEMES.LNTD` 등을 애님 레이어로 깎기 (A00110 툴) | 리그 무수정 | 대사마다 손작업, 입술(`LNTD` → `jawOpen`) 까지 같이 바뀐다 | 방법 2 의 구간 키로 대체 |
| 5. 정렬(phones.json) 기반 규칙 | MFA 정렬로 ㄴ ㄷ ㄹ 의 실제 길이만큼만 혀끝을 올리는 별도 커브 생성 | 가장 정확 | 새 툴 규모 | 장기 과제 (§10) |

방법 2 안에 **입 벌림 억제(C3 대응)** 를 넣은 것이 이 계획의 핵심 제안이다 — 구간을 일일이 고르지 않아도 "입이 열릴수록 혀끝을 내린다" 가 모든 대사에 자동으로 적용된다.

---

## 4. 결정 사항 (권장 = 이대로 진행)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D1 | 결과 파일 | 원본을 열어 **`0010_sample_0060_JaLiTongue.mb`** 로 저장 (같은 폴더). `0050_JaLiMap` 은 그대로 | 0040 → 0050 과 같은 "복사본에 더하기" 규칙. 관찰 씬은 레퍼런스만 바꾸면 된다(§8 S6) |
| D2 | 노드 이름 · 위치 | `|rig|DMY_grp|JALI_TONGUE_TUNE` (transform, 이동 · 회전 · 스케일 잠금, `DUMMY_IN_*` 옆) | 애니메이터가 이미 키를 보는 자리. "rig 그룹 안의 더미" 요청과 같다. 대안: `|rig|JALI_TONGUE_TUNE` (rig 바로 아래) |
| D3 | 새 노드 접두사 | `jtt_` (JALI tongue tune) | 기존 `jali_` · `bw_dmy_` 와 겹치지 않게, 지우기 쉽게 |
| D4 | 어트리뷰트 기본값 | **권장 초기값**(§6 의 D 열)을 기본값으로. 스크립트에 `--neutral` 옵션 = 기존과 같은 값 | 열자마자 개선된 상태. 중립값은 검증 T2 (기존과 동일) 에 쓴다 |
| D5 | 입 벌림 신호 | `CTRL_expressions.jawOpen` (0110 의 `× jawOpen` 노드와 같은 소스) | 실제 턱이 연 정도. `DUMMY_IN_JALI.Jaw` 는 데이터에서 거의 상수(≈ 0.3)라 쓸모없다 |
| D6 | 어디에 끼우나 | `jali_cl_mh_<attr>.outputR` → **새 체인** → `dmy_in_jali_mh.<attr>` (기존 연결을 끊고 사이에 넣는다) + 중복 입력 4개의 `weight[i]` 에 배율 노드 | `dmy_in_jali_mh` 이후(컨트롤러 쪽)는 0040 · 0110 구조 그대로 |

---

## 5. 설계

### 5.1 `JALI_TONGUE_TUNE` 어트리뷰트 (전부 double · keyable · 채널박스 표시)

| 어트리뷰트 | 범위 | 권장 기본 | 중립(기존과 같음) | 뜻 |
|-----------|------|----------:|------------------:|-----|
| `tongueWeight` | 0 – 2 | 1.0 | 1.0 | 혀 직접 경로 5개 전체 배율 (마스터) |
| `tipUpWeight` | 0 – 2 | 1.0 | 1.0 | 혀끝 올림만 배율 |
| `tipDownWeight` | 0 – 2 | 1.0 | 1.0 | 혀끝 내림 배율 |
| `bendUpWeight` | 0 – 2 | 1.0 | 1.0 | 혀 몸통(뒤쪽) 올림 배율 |
| `tongueUpWeight` | 0 – 2 | 1.0 | 1.0 | 혀 전체 올림 배율 |
| `coarticWeight` | 0 – 1 | **0.3** | 1.0 | 동시조음 `CO.LNTD` · `CO.GK` 몫 배율 (C1 — 음소와 같은 데이터라 중복) |
| `rrrTipWeight` | 0 – 1 | **0.4** | 1.0 | `RRR` → 혀끝 올림 몫 배율 (C2 — 한국어 ㄹ 은 말아 올리지 않음) |
| `jawOpenSuppress` | 0 – 1 | **0.6** | 0.0 | 입이 열릴수록 혀끝 올림을 줄이는 세기 (C3). 0 = 끔 |
| `jawOpenRef` | 0.05 – 1 | 0.4 | 0.4 | 이 `jawOpen` 에서 억제가 최대가 된다 |
| `tipUpMax` | 0 – 1 | 0.5 | 1.0 | 혀끝 올림 최종 상한 (안전망) |

나머지 어트리뷰트(이동 · 회전 · 스케일 · visibility)는 잠그고 숨긴다 (`build_mh_jali_dummy._lock_transform` 재사용).

### 5.2 식

```
(중복 입력 배율 — jali_bw_mh_* 의 weight[i] 를 상수 × 어트리뷰트로)
  tongueTipUp.weight[1]  (PH.RRR)  = 0.63 × rrrTipWeight
  tongueTipUp.weight[4]  (CO.LNTD) = 1.00 × coarticWeight
  tongueTipDown.weight[5](CO.GK)   = 1.00 × coarticWeight
  tongueBendUp.weight[4] (CO.GK)   = 0.46 × coarticWeight
  tongueUp.weight[1]     (CO.LNTD) = 0.35 × coarticWeight

(뒤 체인 — 각 혀 어트리뷰트, a = tongueTipUp · tongueTipDown · tongueBendUp · tongueUp · tongueOutExtra)
  v  = jali_cl_mh_<a>.outputR                     (기존 0~1 값)
  v ×= tongueWeight × <a 의 배율>                  (tongueOutExtra 는 tongueWeight 만)
  tongueTipUp 만:  v ×= 1 − jawOpenSuppress × clamp(jawOpen / jawOpenRef, 0, 1)
  dmy_in_jali_mh.<a> = clamp(v, 0, 상한)            (상한: tongueTipUp = tipUpMax, 나머지 1)
```

### 5.3 노드 (전부 이름 고정 — 검증 · 재실행이 이름으로 찾는다)

| 노드 | 타입 | 연결 |
|------|------|------|
| `jtt_md_w_tongueTipUp_RRR` | multDoubleLinear | input1 = 0.63 (setAttr), input2 ← `JALI_TONGUE_TUNE.rrrTipWeight` → `jali_bw_mh_tongueTipUp.weight[1]` |
| `jtt_md_w_tongueTipUp_COLNTD` | 〃 | 1.00 × `coarticWeight` → `jali_bw_mh_tongueTipUp.weight[4]` |
| `jtt_md_w_tongueTipDown_COGK` | 〃 | 1.00 × `coarticWeight` → `jali_bw_mh_tongueTipDown.weight[5]` |
| `jtt_md_w_tongueBendUp_COGK` | 〃 | 0.46 × `coarticWeight` → `jali_bw_mh_tongueBendUp.weight[4]` |
| `jtt_md_w_tongueUp_COLNTD` | 〃 | 0.35 × `coarticWeight` → `jali_bw_mh_tongueUp.weight[1]` |
| `jtt_md_gain_<a>` ×4 (`tongueTipUp` `tongueTipDown` `tongueBendUp` `tongueUp`) | multDoubleLinear | `tongueWeight` × `<a 의 배율>` |
| `jtt_md_<a>` ×5 | multDoubleLinear | input1 ← `jali_cl_mh_<a>.outputR`, input2 ← `jtt_md_gain_<a>.output` (`tongueOutExtra` 는 ← `tongueWeight` 직접) |
| `jtt_pma_jawSup` | plusMinusAverage (subtract) | input1D[0] = 1, input1D[1] ← `jawOpenSuppress` → output1D = 1 − s |
| `jtt_rv_jawSup` | remapValue | inputValue ← `MH 쪽 CTRL_expressions.jawOpen`, inputMin 0, inputMax ← `jawOpenRef`, outputMin = 1, outputMax ← `jtt_pma_jawSup.output1D` (remapValue 는 입력을 inputMin~Max 로 **클램프한다** — 실측 메모, 그래서 jawOpen > ref 면 1 − s 에 머문다). value 곡선은 기본 직선 2점 그대로 |
| `jtt_md_jawSup_tongueTipUp` | multDoubleLinear | `jtt_md_tongueTipUp.output` × `jtt_rv_jawSup.outValue` |
| `jtt_cl_<a>` ×5 | clamp | min 0, maxR = 1 (tongueTipUp 은 maxR ← `tipUpMax`) → **`dmy_in_jali_mh.<a>`** (`connectAttr -force`, 기존 `jali_cl_mh_<a>.outputR` 연결은 이 단계에서 끊긴다) |

합계 **5 + 4 + 5 + 1 + 1 + 1 + 5 = 22 노드** + `JALI_TONGUE_TUNE` 1. 입술 · 턱 · ARKit 경로는 건드리지 않는다.

- 순환: `jawOpen` 은 `CTRL_C_jaw` 체인 출력, 이 체인의 끝은 혀 컨트롤러(`GRP_dmy_CTRL_C_tongue_*`) — 0110 의 `jali_mdjaw_*`(입술)와 같은 구조라 순환이 없어야 한다. **T6 에서 `cycleCheck -all` 로 확인** (실패하면 D5 대안: `jawOpen` 대신 `DUMMY_IN_PHONEMES.AAA + AHH + Eh` 합).
- `jawOpen` 플러그 이름: 리그 파일 안에서는 `CTRL_expressions.jawOpen` (0110 스크립트의 `EXPR_JAWOPEN` 상수 그대로).

---

## 6. 권장 초기값의 효과 (관찰 데이터로 계산, §1.3 의 식 · 오차 0)

`tipUp` = 혀끝 최종값(올림 − 내림), `vis` = max(tipUp, 0) × jawOpen 의 최댓값 (밑면이 보이는 정도의 대용값)

| 설정 | 문제 구간 max / 평균 / vis | 나머지 max / 평균 / vis | 110 · 130 · 195 프레임 |
|------|---------------------------|--------------------------|------------------------|
| 중립 (지금) | 0.56 / 0.091 / 0.177 | 0.56 / 0.047 / 0.189 | 0.44 · 0.38 · 0.47 |
| A `coarticWeight` 0.3 | 0.36 / 0.038 / 0.100 | 0.38 / 0.015 / 0.103 | 0.28 · 0.21 · 0.27 |
| B + `rrrTipWeight` 0.4 | 0.30 / 0.019 / 0.100 | 0.33 / 0.004 / 0.103 | 0.22 · 0.21 · 0.27 |
| **C + `jawOpenSuppress` 0.6 (ref 0.4)** | **0.21 / −0.011 / 0.042** | 0.21 / −0.015 / 0.050 | **0.11 · 0.09 · 0.21** |
| D + `tipUpMax` 0.5 | C 와 같음 (안전망, 이 대사에서는 안 걸림) | | |

- 권장값(D)이면 혀끝 올림 최대가 0.56 → 0.21, `vis` 가 약 1/4. `tongueUp` 도 0.19 → 0.12 (`coarticWeight` 0.3).
- 평균이 음수로 간다 = 혀끝이 평균적으로 살짝 아래(아랫니 뒤) — 너무 내려가 ㄴ · ㄷ 에서 **혀가 아예 안 보이면** `coarticWeight` 를 0.5 쪽으로, `jawOpenSuppress` 를 0.4 쪽으로 (§7 조정 가이드).
- 이 수치는 컨트롤러 값까지다. **눈으로 본 결과**(혀 밑면이 실제로 안 보이는지)는 §8 S7 에서 사용자가 판단한다.

---

## 7. 사용 · 조정 가이드 (S7 에서 사용자에게 그대로 전달)

1. 씬에서 `MH:JALI_TONGUE_TUNE` 를 선택 → 채널박스.
2. 문제 구간(예: 100 – 160)을 재생하며 아래 순서로 조절 — **위에서부터 하나씩**:
   - 혀가 전체적으로 크면 `tongueWeight` (0.7 → 0.5).
   - ㄴ · ㄷ 에서 혀끝이 과하면 `coarticWeight` (0.3 → 0).
   - ㄹ 에서 혀가 말리면 `rrrTipWeight` (0.4 → 0).
   - 모음으로 넘어가며 밑면이 보이면 `jawOpenSuppress` ↑ (0.6 → 0.8) 또는 `jawOpenRef` ↓ (0.4 → 0.3, 더 작은 입 벌림에서 억제).
   - 그래도 튀는 프레임이 있으면 `tipUpMax` ↓ (0.5 → 0.3).
3. **구간만 다르게**: 이 어트리뷰트들은 키를 줄 수 있다. 예) 99 프레임에 `tongueWeight` 1 키, 100 에 0.6 키, 160 에 0.6, 161 에 1 → 그 대사만 줄인다. (A00540 Apply 는 `DUMMY_IN_*` 만 지우고 다시 거므로 이 키는 남는다.)
4. 맞춘 값을 다른 대사에도 기본으로 쓰려면 값을 알려 주면 스크립트 기본값(§5.1 "권장 기본")을 바꿔 0060 을 다시 만든다.

---

## 8. 단계

| 단계 | 할 일 | 결과물 · 명령 |
|------|-------|---------------|
| S0 | §11 질문 확인 (답이 없으면 권장값) → 이 문서 §4 갱신 | 문서 |
| S1 | 원본 백업 확인 — `07_MH_sample_02/backup/0010_sample_0050_JaLiMap_BU.mb` 가 있다(2026-11-26 10:22, `backup/log.txt`). 이 계획은 원본을 **덮어쓰지 않는다** | — |
| S2 | 생성 스크립트 `JUN_JALI/examples/build_mh_jali_tongue_tune.py` 작성 (§5 그대로, 아래 구조) | 스크립트 |
| S3 | 검증 스크립트 `JUN_JALI/examples/check_mh_jali_tongue_tune.py` 작성 (§9 T1 – T7) | 스크립트 |
| S4 | 생성: `mayapy JUN_JALI/examples/build_mh_jali_tongue_tune.py "C:/JUN/JUN_Src_Rig/07_MH_sample_02/0010_sample_0050_JaLiMap.mb" "C:/JUN/JUN_Src_Rig/07_MH_sample_02/0010_sample_0060_JaLiTongue.mb"` | `0010_sample_0060_JaLiTongue.mb` |
| S5 | 검증: `mayapy JUN_JALI/examples/check_mh_jali_tongue_tune.py <0060.mb>` → `RESULT OK` | 로그 |
| S6 | 관찰 씬 시험 (T8): 관찰 씬을 **복사본으로** 열어(`JUN_JALI/out/0150/0010_Metahuman_01_tune.mb`, out 은 gitignore) 레퍼런스 `oldRN` 을 0060 으로 교체 → 키 23개가 그대로 붙어 있는지 · §6 D 열 수치가 나오는지 | 복사본 + 로그. **원본 `D:\D__1010_PortFolio\…\0010_Metahuman_01.mb` 는 건드리지 않는다** |
| S7 | 사용자 GUI 확인 — 원본 씬에서 Reference Editor → `oldRN` 우클릭 → Replace Reference → 0060 선택 → 세 구간 재생, §7 로 조절 | 사용자 답 |
| S8 | 사용자가 정한 값을 §5.1 기본값에 반영해 S4 – S5 다시 (필요할 때만) → §12 기록, README 목록 갱신 | 완료 |

### S2 스크립트 구조 (`build_mh_jali_tongue_tune.py`)

```python
# build_mh_jali_dummy.py 와 같은 형식 (argparse src dst, maya.standalone, 같은 상수 재사용)
import build_mh_jali_dummy as JD           # NODE_MH = 'dmy_in_jali_mh', EXPR_JAWOPEN, PREFIX='jali_', _lock_transform
TUNE = 'JALI_TONGUE_TUNE'
ATTRS = OrderedDict([  # 이름: (min, max, 권장 기본, 중립)
    ('tongueWeight', (0, 2, 1.0, 1.0)), ('tipUpWeight', (0, 2, 1.0, 1.0)), ('tipDownWeight', (0, 2, 1.0, 1.0)),
    ('bendUpWeight', (0, 2, 1.0, 1.0)), ('tongueUpWeight', (0, 2, 1.0, 1.0)),
    ('coarticWeight', (0, 1, 0.3, 1.0)), ('rrrTipWeight', (0, 1, 0.4, 1.0)),
    ('jawOpenSuppress', (0, 1, 0.6, 0.0)), ('jawOpenRef', (0.05, 1, 0.4, 0.4)), ('tipUpMax', (0, 1, 0.5, 1.0)),
])
WEIGHT_TAPS = [  # (bw 노드 attr, weight index, 원래 상수, 조절 어트리뷰트, 노드 이름 꼬리)
    ('tongueTipUp', 1, 0.63, 'rrrTipWeight', 'RRR'), ('tongueTipUp', 4, 1.00, 'coarticWeight', 'COLNTD'),
    ('tongueTipDown', 5, 1.00, 'coarticWeight', 'COGK'), ('tongueBendUp', 4, 0.46, 'coarticWeight', 'COGK'),
    ('tongueUp', 1, 0.35, 'coarticWeight', 'COLNTD'),
]
GAIN = {'tongueTipUp': 'tipUpWeight', 'tongueTipDown': 'tipDownWeight', 'tongueBendUp': 'bendUpWeight',
        'tongueUp': 'tongueUpWeight', 'tongueOutExtra': None}
```

- 함수: `create_tune_node(neutral)` → `wire_weight_taps()` → `wire_post_chain()` → `build(neutral=False)`.
- **사전 검사** (하나라도 실패하면 아무것도 만들지 않고 `BuildError`): `JALI_TONGUE_TUNE` 가 이미 있음(재실행 금지 — 0050 에 돌릴 것) · `DMY_grp` / `dmy_in_jali_mh` / `jali_bw_mh_*` 5개 / `jali_cl_mh_*` 5개 / `CTRL_expressions.jawOpen` 없음 ·
  `WEIGHT_TAPS` 의 각 `weight[i]` 의 **현재 값이 원래 상수와 다름**(0050 이 다른 버전이라는 뜻) · 그 `input[i]` 의 소스가 기대한 플러그(`DUMMY_IN_PHONEMES.RRR` 등)가 아님 · `weight[i]` 에 이미 연결이 있음.
- `weight[i]` 를 연결하기 전 값 = 상수인지 확인한 뒤 `connectAttr`. 뒤 체인은 `connectAttr -force` 로 `dmy_in_jali_mh.<a>` 를 덮는다.
- `--neutral` 옵션 = 기본값을 중립 열로 (T2 용). 저장은 `cmds.file(rename=dst); cmds.file(save=True, type='mayaBinary')`.
- RigLogic 플러그인(`build_mh_arkit_dummy.RIGLOGIC_PLUGIN`)이 로드돼 있어야 한다 — 0110 `build()` 와 같은 검사.

---

## 9. 검증 (`check_mh_jali_tongue_tune.py`, mayapy)

| # | 검사 | 기대 |
|---|------|------|
| T1 | 구조 | `|rig|DMY_grp|JALI_TONGUE_TUNE` 존재, §5.1 어트리뷰트 10개 · 범위 · 기본값(권장), 변환 채널 잠김. `jtt_*` 노드 22개, §5.3 연결 전부. `dmy_in_jali_mh.<a>` 5개의 소스가 `jtt_cl_<a>.outputR` |
| T2 | **중립 = 기존과 동일** | 0060 에서 어트리뷰트를 중립 열로 놓고, 25 케이스(0110 T2 의 단일 입력 케이스: 음소 16 · 동시조음 5 각 1.0, Jaw/Lip 0.6 + `LNTD`+`RRR` 혼합 등) 마다 `dmy_in_jali_mh.*` 와 `CTRL_expressions.tongue*` 가 **0050 에서 같은 입력을 준 값과 1e-6 이내**. 0050 값은 같은 스크립트가 0050 을 열어 미리 잰다 |
| T3 | 각 어트리뷰트 단독 효과 | 입력 `PH.LNTD` 1 · `CO.LNTD` 1 · Jaw 0.6: 중립 tipUp = clamp(0.61 + 1.0) = 1.0 → `coarticWeight` 0.3 이면 clamp(0.61 + 0.3) = 0.91; `PH.RRR` 1 단독: 0.63 → `rrrTipWeight` 0.4 이면 0.252; `tongueWeight` 0.5 → 절반; `tipUpMax` 0.3 → 0.3 에서 잘림 |
| T4 | 입 벌림 억제 | `PH.LNTD` 0.5 단독(억제 전 tipUp 0.305), `coarticWeight` 1 · `jawOpenSuppress` 0.6 · ref 0.4. **`LNTD` 자체가 ARKit 경로로 `jawOpen` 을 만든다**(LNTD 1 → 0.30, 0110 §12) — 그래서 기대값은 그 프레임에서 읽은 `j = CTRL_expressions.jawOpen` 으로 계산: `0.305 × (1 − 0.6 × min(j / 0.4, 1))`. 세 점: 추가 없음(j ≈ 0.15) · `dmy_in.jawOpen` 0.1 추가 · 0.5 추가(j ≥ 0.4 → 0.305 × 0.4 = 0.122). `jawOpenSuppress` 0 이면 세 점 모두 0.305 |
| T5 | 입술 · 턱 · ARKit 무변 | 0110 T2 의 252 채널 중 혀 5채널 하류(`tongue*`) 를 뺀 나머지가 권장값에서도 0050 과 1e-6 이내 (`jawOpen` · `lipsTogether*` · `funnel` · `dmy_out.*` 등) |
| T6 | 순환 · 손 조작 | `cycleCheck -all` 결과 없음. 혀 컨트롤러 8개의 tx · ty 연결 없음(손 조작 자유, 0110 T7 과 같음). `JALI_TONGUE_TUNE` 어트리뷰트에 키를 걸고 시간을 바꾸면 값이 따라 변함 |
| T7 | A00540 호환 | `DUMMY_IN_*` 이름 · 어트리뷰트 · 범위가 0050 과 같음 → `Framework.jali.keyer.check_targets(load_mapping('jali_slider_dummy_in'))` 가 빈 목록 |
| T8 | 관찰 씬 (S6, 복사본) | 레퍼런스 교체 뒤 `MH:DUMMY_IN_*` 의 animCurve 연결 23개 그대로 · 프레임 110 · 130 · 195 의 `CTRL_expressions.tongueTipUp − tongueTipDown` 이 §6 D 열(0.11 · 0.09 · 0.21) ± 0.01 · 문제 구간 max ≤ 0.22 |
| T9 | 사용자 GUI (S7) | 세 구간에서 혀 밑면이 안 보임 · ㄴ ㄷ 에서 혀끝이 여전히 잇몸 쪽으로 움직임(너무 죽지 않음) |

`check` 스크립트 마지막 줄 `RESULT OK` / `RESULT n FAILED`, 종료 코드 = 실패 수 (0110 검증과 같은 형식).

---

## 10. 후속 (이번 범위 밖)

- **같은 현상이 다른 프레임에도 있다** (§1.3 — 286 · 361 · 531 · 575 · 666 – 685). 권장값은 전 구간에 적용되므로 같이 좋아질 것으로 보이지만, S7 에서 함께 봐 달라고 안내한다.
- 방법 3: 사용자 값이 정해지면 A00540 매핑 json 에 타겟별 배율(`scale`)을 넣는 안 — 그때 `COARTIC.LNTD/GK` 의 중복을 데이터 단계에서 줄일 수 있다 (A00540 · Framework/jali 수정 필요).
- 방법 5: MFA 정렬(`*.phones.json`)로 ㄴ ㄷ ㄹ 길이만큼만 혀끝 커브를 만드는 규칙.
- 0110 의 다른 미확인(입술 깨물기 · `COARTIC.MMM`)도 같은 중복(C1) 구조 — `CO.MMM ← MBP`, `CO.FFF ← FV`. 입술은 사용자가 "무난" 이라 했으므로 이번에는 손대지 않는다.

---

## 11. 확인 질문 (답이 없으면 권장으로 진행)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | 결과 파일 이름 `0010_sample_0060_JaLiTongue.mb` (D1) | 그대로 |
| Q2 | 더미 위치 `|rig|DMY_grp|JALI_TONGUE_TUNE` vs `|rig|JALI_TONGUE_TUNE` (D2) | `DMY_grp` 아래 |
| Q3 | 기본값 = 권장값(열자마자 개선) vs 중립(기존과 같게 열고 직접 조절) (D4) | 권장값 |
| Q4 | 지정 구간 밖(286 · 361 · 531 · 575 · 666 – 685 등)도 같이 좋아지는 게 맞는지 — 전 구간 적용이 기본 | 전 구간 적용 + 구간 키는 필요할 때 |
| Q5 | 생성 · 검증 스크립트 위치 — 계획서는 Maya_Python 으로 옮겼지만 스크립트는 `JUN_JALI/examples/` (의존하는 `build_mh_jali_dummy.py` · `build_mh_arkit_dummy.py` 가 거기 있다) vs `JUN_All` 쪽 | `JUN_JALI/examples/` — 0100 · 0110 스크립트와 한 자리, import 그대로 |

---

## 12. 구현 · 검증 결과

(S4 – S8 후 기록)
