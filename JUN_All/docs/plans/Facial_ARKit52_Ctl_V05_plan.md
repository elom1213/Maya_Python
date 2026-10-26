# Facial ARKit 52 컨트롤러 V05 — 작업 계획서 (Ctl_Only_V04 → V05, Maya + Unreal 공용 보드)

> **작성** 2026-10-26 · 상태: **계획 (코드 · 파일 생성 전, §7 M0 실측 전)** · 대상 Maya 2024 (mayapy 빌드 · 검증) · Unreal 5.x Control Rig (2단계)
> 원본 `C:\Users\USER\Desktop\JP\0035_maya_src_rig\01_Module_01_Facial\Ctl_Only_V04.mb` (Maya 2024 · cm · 레퍼런스 없음 · 플러그인 의존 없음)
> 참고 `07_MH_sample_02\0010_sample_0030.mb` 의 MetaHuman 페이셜 GUI 보드(`GRP_faceGUI`, CTRL 181개)
> 전례 `02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma` — JUN_JALI `examples/build_jali_slider_ctl.py` 로 **스크립트 생성 + 검증**한 슬라이더 리그(메모리 `wip-jali-slider-ctl`)
> §0 · §1 의 수치는 전부 **mayapy 실측**(2026-10-26, 관찰 스크립트 3개) 이다. 추정은 "추정" 이라고 적었다.

---

## 0. 요청과 산출물

| # | 요청 (사용자 2026-10-26) | 산출물 |
|---|------|--------|
| **R1** | 컨트롤러 위치가 **실제 얼굴이 변하는 자리**와 거의 같거나 비슷하게 | 얼굴 지도형 2D 보드 재배치 — 52 attr 전부의 자리 · 컨트롤 종류를 §2 표로 확정 |
| **R2** | `BS_Face_CSV` · `BS_Face_Connect_01` 의 **연결 관계 유지** (CSV 임포트 → 컨트롤러 베이크 / 출력 키 → 다른 노드 연결용 더미) | 두 노드의 **이름 · 타입 · 52 attr 이름 · 순서 그대로**, 컨트롤러만 바뀜. 뒤로(CSV → 컨트롤러) · 앞으로(컨트롤러 → Connect_01) 두 경로 모두 다시 연결 (§3) |
| **R3** | 같은 모양의 컨트롤러를 **언리얼에서도** 생성 · 사용, forward / backward 베이크 (MetaHuman 보드처럼 Maya · UE UI 동일) | **보드 명세 json 하나**가 단일 소스 → Maya 빌더(이번) · UE Control Rig 빌더(2단계)가 같은 json 을 읽는다 (§4) |
| 산출물 | | `01_Module_01_Facial\Ctl_Only_V05.ma` + `.mb` · 명세 `arkit52_board_v05.json` · 빌더 · 검증 스크립트 · V04 → V05 이관표 · 안내 문서. **V04 는 건드리지 않는다** |

---

## 1. 관찰 — 지금 V04 가 어떻게 되어 있나 (실측)

### 1-1. 구조

```
CH_n_faical_xx_zro
├── CH_n_faical_xx_con
│   └── CH_n_faical_xx_ctl          # 루트 컨트롤 (attr `_` · Head · Global · World — 연결 없음)
│       ├── BS_eye_all_gud / BS_nose_all_gud / BS_lip_all_gud / BS_jaw_all_gud
│       │   └── <이름>_gud > <이름>_zro > <이름>_ctl     # 컨트롤 52 (NURBS 원, 지름 0.61)
│       └── BS_text_all_grp         # 라벨 글자 커브(eye · nose · mouth · jaw) + FaicalMesh_geo
└── BS_Face_Connect_01              # transform, user attr 52 (앞으로 출력)
BS_Face_CSV                         # blendShape (FaicalMesh_geo 에 걸림), 타겟 52 — 델타 0 (순수 더미)
```

- 보드 = 평면 패널, x 13.3 ~ 26.6 · y 142 ~ 166.8 · z 0 (가로 13.3 · 세로 25). 행: 눈썹 166.8 / 눈 163.3 / 눈꺼풀·광대·코주름 159.5 / 코 158.9 / 윗입술 153.7 / 입꼬리 152 / 아랫입술 150.3 / 뺨 148.2 / 턱 145.2 / 퍼널·퍼커·슈러그 142 ~ 143.
- `FaicalMesh_geo` 는 얼굴이 아니라 **"Faical" 글자 메시**(404 vtx, y 170 라벨). `BS_Face_CSV` 는 이 메시의 blendShape 이고 **52 타겟 전부 델타 0** — 메시는 CSV 키를 받을 자리일 뿐이다. ("얼굴이 변하는 위치" 는 이 파일에는 없다 → R1 의 기준은 **실제 얼굴 해부 위치**, §2.)
- 노드 쓰레기: `composeMatrix` 532 · `renderLayer`(legacy) 29 · `poseInterpolatorManager` 29 · HIK 노드 · `unknown` 40 — 열 때 "legacy render layers" 에러. 새로 빌드하면 자연히 사라진다.

### 1-2. 연결 — 두 경로가 **동시에 살아 있다**

| 경로 | 모양 | 수 |
|------|------|----|
| **뒤로** (CSV → 컨트롤러) | `BS_Face_CSV.<attr>` → (`multiplyDivide` · `plusMinusAverage`) → **`<ctl>.translateX/Y`** | 컨트롤 **38개의 translate 가 입력 연결 상태** |
| **앞으로** (컨트롤러 → 출력) | `<ctl>.translateX/Y` → (`clamp` 0~1 · `multiplyDivide` ×−1) → `BS_Face_Connect_01.<attr>` | 52 attr 전부 |

- 양방향 축은 `clamp` 로 ± 를 둘로 가른다: `c_jaw_rot_ctl.tx` → jawLeft / jawRight, `.ty` → jawOpen · `l_eyeball_ctl.tx/ty` → eyeLookIn/Out/Up/Down · `BS_lipLeft_ctl.ty` → mouthSmile/Frown · `BS_lipLow_ctl.tx` → mouthLeft/Right.
- **저장된 상태에서 컨트롤러는 CSV 가 끌고 다닌다** → 손 애니는 베이크(연결 끊기) 뒤에만 가능. 지금 흐름 = CSV 임포트 → `BS_Face_CSV` 가중치에 키 → 컨트롤러가 따라옴 → 컨트롤러로 베이크 (JALI direct 리그와 같은 모양, 사용자가 그쪽에서 "컨트롤러에 키가 그대로 남게" 로 고른 방식).
- 리밋 **없음**(transformLimits 전부 꺼짐) — 범위는 뒤의 `clamp` 가 자르고 컨트롤러는 무한히 움직인다. rotate · scale 도 키어블(쓸모 없음).

### 1-3. R1 의 근거 — 자리 · 이름이 얼굴과 안 맞는 곳

| 종류 | 실측 |
|------|------|
| **연결 없는 컨트롤 7** | `BS_cheekLeft/Right_innOut` · `BS_eyebrowLeft/Right_mid` · `BS_lipTop_frontBack` · `BS_noseLeft/Right` — 어디에도 안 간다 (죽은 컨트롤) |
| **자리 ≠ 부위** | `BS_checkPuff`(cheekPuff) 가 **중앙** x 19.95 — 볼은 양옆 · `BS_mouthFunnel/Pucker` 가 **턱 아래** y 142 ~ 143 — 입술 모양 · `c_jaw_mouthShrugUpper/Lower` 가 턱 행 x 17.77 에 세로로 — 입술 · `l_eyelid_Up`(eyeBlink) x 24.21 · `l_eyeWide_Up` x 25.17 — 눈(21.85) 보다 **바깥쪽** · `l_cheekSquint`(광대 올림) 가 코주름 옆 |
| **이름 ≠ 기능** | `l_eyelid_Up_ctl` → eyeBlink(눈 감기) · `BS_lipLow_ctl.tx` → mouthLeft/Right(입 전체 좌우) · `BS_lipLow_leOut` → mouthStretch · `BS_lipTop_leOut` → mouthPress · `BS_lipTop_ctl` → mouthRollUpper · `BS_eyebrowLeft_inn` → browDownLeft(눈썹 전체 내림) |
| **이름 체계 혼재** | 접두어 `BS_` · `c_` · `l_/r_` 셋, 좌우 `Left/Right` · `le/ri` · `l_/r_` 혼용, `faical` · `checkPuff` 오타, `BS_eyebrowRight_inn_1_ctl` 의 `_1` |

### 1-4. MetaHuman 보드 (0010_sample_0030) 에서 가져올 것

```
GRP_faceGUI (머리에 parentConstraint) > CTRL_faceGUI > FRM_faceGUI
  > GRP_<region>GUI (brow · eye · nose · mouth · jaw · tongue · teeth · neck · switches)
    > FRM_<ctl> (테두리 · 라벨) > CTRL_<L|R|C>_<region>_<motion>   # 181개, 셰이프는 폴리 메시
CTRL_expressions (user attr 252)  ←  animCurveUU `CTRL_expressions_<attr>`  ←  CTRL_*.ty
```

- 컨트롤은 **tx/ty 만 keyable**, `transformLimits` 로 **0~1 또는 −1~1 고정**(나머지 축 0 고정). 크기 0.1 ~ 0.5, 보드 x 9.5 ~ 41 · y 140.8 ~ 172.9 · z 2.8 (머리 옆 평면).
- 행: 눈썹 164 ~ 165 / 눈 161 / 코·광대 159 / 윗입술 156 / 입 155 / 아랫입술 154 / 턱 148.7 / 목 143 ~ 144 — **얼굴 지도** 배치. `L` 이 +x (보는 사람 기준 오른쪽, 캐릭터 왼쪽). V04 도 Left 가 +x 라 같다.
- 종류 셋: 슬라이더 0~1 · 슬라이더 ±1(두 표현을 한 축에) · 2D 패드(tx/ty ±1 → 4 표현). 컨트롤 → **출력 attr 노드**(`CTRL_expressions`) 한 곳으로 모으는 구조는 우리 `BS_Face_Connect_01` 과 같다.
- UE 쪽 MetaHuman 은 같은 이름의 컨트롤을 Control Rig 가 갖고 Backwards Solve 로 애니 → 컨트롤 베이크를 한다. **이름 · 위치 · 리밋이 같으면 UI 가 같아진다** — R3 의 방법.

---

## 2. 설계 결정 (권장안 — §9 질문에서 확인)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| **D1** | 파일 · 버전 | `Ctl_Only_V05.ma` + `.mb`, V04 보존 | 관례(버전은 파일명에). `.ma` 는 UE 빌더 · diff 용, `.mb` 는 작업용 |
| **D2** | 더미 노드 | `BS_Face_CSV`(blendShape, 타겟 52 별칭 · 순서) · `BS_Face_Connect_01`(transform, attr 52 · 순서) · 둘이 걸린 `FaicalMesh_geo` 를 **이름 그대로** | R2. CSV 임포트 · RigConnect 규칙 `Apple ARKit 52 Facial Target` · 기존 키 베이크 흐름이 이 이름을 본다. 메시는 글자 메시 대신 **작은 평면**으로 바꾸되 이름 유지 (오타도 유지 — 바꾸면 임포트가 깨질 수 있다, Q2) |
| **D3** | 컨트롤 이름 | **`CTRL_<L|R|C>_<region>_<motion>`** (MetaHuman 관례), 그룹 `GRP_<region>GUI`, 틀 `FRM_<ctl>`, 루트 `GRP_faceBoard` | UE Control Rig 에서 같은 이름으로 만든다. L/R 은 **캐릭터 기준**(ARKit 과 같음), 보드에서 L 은 +x |
| **D4** | 배치 | **얼굴 지도형 2D 보드**, 좌우 대칭, 부위 자리에 컨트롤 (§2-1 표 · §2-2 그림). 보드 로컬 좌표(가로 −7 ~ 7 · 세로 0 ~ 26), 루트가 세상 자리 결정 | R1. UE 에서는 로컬 좌표가 그대로 쓰인다 |
| **D5** | 컨트롤 종류 셋 | **슬라이더 0~1**(ty) · **슬라이더 ±1**(ty, 반대 표현 둘) · **2D 패드**(tx/ty ±1, 표현 넷). `transformLimits` 로 고정, 나머지 채널 lock + hide | MetaHuman 과 같다. 클램프 노드 대신 **리밋이 범위를 보장**하므로 손 애니가 범위 밖으로 못 간다 |
| **D6** | 앞으로 경로 (컨트롤 → Connect_01) | 0~1 슬라이더는 **직결**, ± 축은 `clamp(0,1)` 와 `×−1 → clamp` 둘로 가름. 이름 `<CTRL>__<attr>_clamp` 식 | 선형 · 노드 3종이면 UE 그래프에서 1:1 재현이 쉽다(animCurveUU 는 UE 로 못 간다). 현행과 같은 수식 |
| **D7** | 뒤로 경로 (CSV → 컨트롤) | **direct 유지** — `BS_Face_CSV.a` → `CTRL.ty` (0~1), ± 축은 `plusMinusAverage(a₊ − a₋)` → `CTRL.ty`. 베이크 스크립트(JALI `bake_ctl_keys` copy 모드 이식) 제공 → 베이크하면 연결이 끊기고 키가 컨트롤러에 남는다 | 현행 흐름이고 사용자가 JALI 에서 같은 선택을 했다. 대안 `_drv` 합산(컨트롤러는 늘 자유, 베이크 = drv → ctl 복사)은 Q1 |
| **D8** | 생성 방법 | **손으로 만들지 않고 빌더 스크립트**(mayapy) 가 json 명세에서 생성 + 검증 스크립트 | JALI 슬라이더 리그 전례(305 ~ 495 항목 검증). 자리 수정 = json 수정 → 재생성. UE 빌더가 **같은 json** 을 읽는다(R3) |
| **D9** | 빌더 위치 | Maya_Python `JUN_All/tools/A00580_FacialBoardBuilder/`(헤드리스 `build.py` + `verify.py` + `spec/arkit52_board_v05.json` + `migrate_v04.json`), UI 없이 시작 | 라우팅 규칙(마야 파이썬 → Maya_Python). A00560/A00570 다음 번호. 나중에 in-Maya UI 를 얹을 수 있게 (B) 폴더 모양 |
| **D10** | 색 | L **빨강** · R **파랑** · C **노랑**, 슬라이더 트랙 · 틀은 Reference 표시(선택 안 됨), 라벨 = `textCurves` | 좌우가 한눈에. textCurves 는 mayapy 에서 된다(JALI 실측) |
| **D11** | 루트 attr `Head / Global / World` | **유지하되 연결하지 않음**(지금도 연결 없음) + 보드 전체 `visibility` · `boardScale` | 무엇에 쓰는지 확인 뒤(Q5) 연결 |
| **D12** | V04 호환 | `migrate_v04.json`(V04 `ctl.attr` → V05 `CTRL.attr` + 부호) 제공 → 옛 키 애니는 A00110 Copy Key / A00145 Connect by Rule 로 이관 | 이름이 전부 바뀌므로 옛 `.ma` 애니가 바로 안 붙는다 — 표로 건너가게 |

### 2-1. 52 attr → 컨트롤 매핑표 (컨트롤 **33개**)

부호: `+ty` = 위, `−ty` = 아래, `+tx` = 보드 오른쪽(캐릭터 **Left**). R 쪽 패드의 In/Out 은 거울(§3-3).

| 부위 | 컨트롤 | 종류 | 축 → attr | 자리 (로컬 x, y) |
|------|--------|------|-----------|------------------|
| 눈썹 | `CTRL_C_brow_raiseIn` | 0~1 | +ty browInnerUp | 0, 24.0 |
| | `CTRL_L_brow_down` / `_R_` | 0~1 | +ty browDownL/R *(아래로 끌면 내려가게 −ty 로 둘지 Q6)* | ±1.6, 24.0 |
| | `CTRL_L_brow_raiseOut` / `_R_` | 0~1 | +ty browOuterUpL/R | ±3.4, 24.4 |
| 눈 | `CTRL_L_eye` / `_R_` | 2D ±1 | +ty eyeLookUp · −ty eyeLookDown · **바깥쪽** tx eyeLookOut · 안쪽 eyeLookIn | ±2.4, 20.5 |
| | `CTRL_L_eye_blinkWide` / `_R_` | ±1 | −ty eyeBlink · +ty eyeWide | ±2.4, 22.3 (윗꺼풀) |
| | `CTRL_L_eye_squint` / `_R_` | 0~1 | +ty eyeSquint | ±2.4, 18.8 (아랫꺼풀) |
| 광대·볼 | `CTRL_L_cheek_squint` / `_R_` | 0~1 | +ty cheekSquint | ±3.6, 17.6 |
| | `CTRL_C_cheek_puff` | 0~1 | +ty cheekPuff | 0, 14.6 *(한 attr 이라 하나 — 자리 Q3)* |
| 코 | `CTRL_L_nose_sneer` / `_R_` | 0~1 | +ty noseSneer | ±1.1, 16.4 |
| 입 | `CTRL_C_mouth_move` | ±1 (tx) | +tx mouthLeft · −tx mouthRight | 0, 11.6 |
| | `CTRL_L_mouth_corner` / `_R_` | 2D ±1 | +ty mouthSmile · −ty mouthFrown · 바깥 tx mouthStretch · 안쪽 tx mouthDimple | ±3.2, 11.6 |
| | `CTRL_L_mouth_upperLipRaise` / `_R_` | 0~1 | +ty mouthUpperUp | ±1.4, 13.2 |
| | `CTRL_L_mouth_lowerLipDepress` / `_R_` | 0~1 | −ty mouthLowerDown *(아래로 끌면)* | ±1.4, 9.9 |
| | `CTRL_L_mouth_press` / `_R_` | 0~1 | +ty mouthPress | ±2.3, 12.4 |
| | `CTRL_C_mouth_upperLip` | ±1 | +ty mouthShrugUpper · −ty mouthRollUpper | 0, 13.4 |
| | `CTRL_C_mouth_lowerLip` | ±1 | −ty mouthShrugLower · +ty mouthRollLower | 0, 9.7 |
| | `CTRL_C_mouth_funnel` | 0~1 | +ty mouthFunnel | −1.0, 11.6 *(입 중앙 양옆, Q4)* |
| | `CTRL_C_mouth_pucker` | 0~1 | +ty mouthPucker | +1.0, 11.6 |
| | `CTRL_C_mouth_close` | 0~1 | +ty mouthClose | 0, 10.7 (입술 선) |
| 턱 | `CTRL_C_jaw` | 2D | **−ty** jawOpen (아래로 끌면 열림, ty −1~0) · +tx jawLeft · −tx jawRight | 0, 6.0 |
| | `CTRL_C_jaw_fwd` | 0~1 | +ty jawForward | 2.0, 6.0 |
| 혀 | `CTRL_C_tongue_out` | 0~1 | +ty tongueOut | 0, 8.2 (아랫입술 아래) |

합계: 눈썹 5 · 눈 6(14 attr) · 광대 3 · 코 2 · 입 14(23 attr) · 턱 2(4 attr) · 혀 1 = **33 컨트롤 / 52 attr** (V04 는 52 컨트롤 중 7 이 죽어 있었다).

### 2-2. 보드 그림 (로컬 좌표, 보는 사람 기준 — 오른쪽이 캐릭터 Left)

```
 y
26 ┤        [R raiseOut]  [R down] [C raiseIn] [L down]  [L raiseOut]        눈썹
22 ┤              [R blinkWide]                [L blinkWide]                  윗꺼풀
20 ┤              ( R eye  )                   ( L eye  )                     눈 (2D)
19 ┤              [R squint]                   [L squint]                     아랫꺼풀
17 ┤   [R cheekSquint]   [R sneer] [L sneer]   [L cheekSquint]                광대 · 코
15 ┤                          [C cheekPuff]                                   볼
13 ┤        [R upperLipRaise] [R press] [C upperLip] [L press] [L upperLipRaise]  윗입술
12 ┤ ( R corner )  [C funnel] <C mouth_move> [C pucker]  ( L corner )         입
11 ┤                          [C close]                                       입술 선
10 ┤        [R lowerLipDepress]   [C lowerLip]   [L lowerLipDepress]          아랫입술
 8 ┤                          [C tongueOut]                                   혀
 6 ┤                          ( C jaw )   [C jaw_fwd]                         턱
   └──────┬──────────┬──────────┬──────────┬──────────┬──────► x
         −6         −3          0          3          6
   [ ] 슬라이더   ( ) 2D 패드   < > 좌우 슬라이더
```

---

## 3. 노드망 규격 (빌더가 만드는 것)

### 3-1. 컨트롤 하나의 계층

```
GRP_<region>GUI
└── FRM_<ctl>            # 틀 · 트랙 · 눈금 · 라벨 (Reference, 선택 불가)
    └── <CTRL>           # NURBS 원/사각, tx·ty 만 keyable, transformLimits, 색 D10
```

- 0~1 슬라이더: `ty` [0, 1], `tx` [0, 0] · ±1 슬라이더: `ty` [−1, 1] · 2D 패드: `tx` `ty` [−1, 1] · 턱 패드: `ty` [−1, 0]. `tz` · rotate · scale lock + hide.

### 3-2. 앞으로 (컨트롤 → `BS_Face_Connect_01`)

| 종류 | 노드 |
|------|------|
| 0~1 슬라이더 | `CTRL.ty → BS_Face_Connect_01.attr` **직결** (리밋이 범위) |
| ± 축의 + 표현 | `CTRL.ty → clamp(min 0, max 1).inputR → .outputR → attr₊` |
| ± 축의 − 표현 | `CTRL.ty → multiplyDivide(×−1) → clamp(0,1) → attr₋` |
| 턱 open | `CTRL_C_jaw.ty → ×−1 → clamp → jawOpen` |

### 3-3. 뒤로 (`BS_Face_CSV` → 컨트롤, D7 direct)

| 종류 | 노드 |
|------|------|
| 0~1 슬라이더 | `BS_Face_CSV.attr → CTRL.ty` 직결 |
| ± 축 | `plusMinusAverage(attr₊ − attr₋).output1D → CTRL.ty` (턱 open 은 `0 − jawOpen`) |
| R 쪽 패드 tx | L 패드가 `+tx = Out` 이면 R 패드는 `+tx = In` (보드 오른쪽 = 코 쪽) — **거울 부호**를 json `mirror_x` 로 |

- 연결 중에는 컨트롤러가 CSV 를 따른다. **베이크** = `bake_ctl_keys(copy)` 이식: `BS_Face_CSV` 의 animCurve 를 컨트롤 ty/tx 로 복사(± 는 합산 커브 생성), 뒤로 연결 끊기. 베이크 뒤 `BS_Face_Connect_01` 은 컨트롤러를 따라간다.
- 되돌리기: `reconnect_csv()` 가 json 명세로 뒤로 경로를 다시 건다 (다음 CSV 임포트 전).

### 3-4. 명세 json (단일 소스) — 모양

```json
{
  "version": "05", "board": {"width": 14, "height": 26, "ctl_radius": 0.35},
  "dummies": {"csv": "BS_Face_CSV", "out": "BS_Face_Connect_01", "mesh": "FaicalMesh_geo"},
  "controls": [
    {"name": "CTRL_L_eye", "region": "eye", "type": "pad", "pos": [2.4, 20.5], "mirror_of": null,
     "axes": {"ty+": "eyeLookUpLeft", "ty-": "eyeLookDownLeft", "tx+": "eyeLookOutLeft", "tx-": "eyeLookInLeft"},
     "limits": {"tx": [-1, 1], "ty": [-1, 1]}, "color": "L"},
    {"name": "CTRL_C_jaw", "region": "jaw", "type": "pad", "pos": [0, 6.0],
     "axes": {"ty-": "jawOpen", "tx+": "jawLeft", "tx-": "jawRight"}, "limits": {"tx": [-1, 1], "ty": [-1, 0]}, "color": "C"}
  ]
}
```

R 쪽은 `mirror_of: "CTRL_L_eye"` 한 줄로 x 반전 + Left→Right 치환 + tx 부호 거울을 빌더가 만든다 (손으로 두 번 안 적는다).

---

## 4. Unreal 동기화 (2단계 — 이번 산출물에는 **명세만** 맞춘다)

| 항목 | 계획 |
|------|------|
| 컨트롤 | UE Python `RigHierarchyController.add_control` 로 json 의 **같은 이름 · 같은 로컬 위치 · 같은 리밋**(Control Settings limits) 생성, 셰이프는 Control Rig 기본 라이브러리 `Circle_Thin` / `Box_Thin` (NURBS 커브는 UE 로 안 가므로 모양은 "원 / 사각" 둘로만 맞춘다 — D5 가 종류를 셋으로 묶은 이유) |
| forward | Control Rig Forwards Solve: `Get Control Float/Vector2D → Clamp / Multiply(−1) → Set Curve Value(ARKit 52 커브 이름 = attr 이름)` — §3-2 와 같은 수식 |
| backward | Backwards Solve: `Get Curve Value → (a₊ − a₋) → Set Control` — §3-3 과 같은 수식 → **Bake to Control Rig** 로 ARKit 애니 시퀀스를 컨트롤 키로 |
| 좌표 | 보드 로컬 좌표(cm) 그대로, 루트 컨트롤이 머리 옆 배치 |
| 확인 (M0) | UE 5.4/5.5 Python 에서 limits · shape transform · 색 설정 API 이름 실측(`set_control_settings` · `set_control_shape_transform`) |

---

## 5. 폴더 · 파일

```
0035_maya_src_rig/01_Module_01_Facial/
├── Ctl_Only_V04.mb                      # 보존
├── Ctl_Only_V05.ma  /  Ctl_Only_V05.mb  # 빌더 출력
└── Ctl_Only_V05_board.png               # 보드 미리보기 (CV 덤프 → PIL, JALI 전례)

Maya_Python/JUN_All/tools/A00580_FacialBoardBuilder/
├── build.py            # mayapy build.py spec/arkit52_board_v05.json <out.ma> [--mb]
├── verify.py           # mayapy verify.py <out.ma>   (T1 ~ T8)
├── bake.py             # bake_csv_to_ctl(copy) · reconnect_csv()   (3단계에 in-Maya 버튼으로)
├── spec/arkit52_board_v05.json
├── spec/migrate_v04.json                # V04 ctl.attr → V05 CTRL.attr (+부호)
└── docs → JUN_All/docs/A00580_FacialBoardBuilder.md (사용 안내) · 이 계획서
```

---

## 6. 단계

| 단계 | 내용 | 산출 |
|------|------|------|
| **M0** | §7 실측 8항목 (반나절) | 이 문서 §7 에 결과 기록, D5/D7/Q 확정 |
| **M1** | 명세 json 작성 (§2-1 표 그대로) + 미리보기 png | `arkit52_board_v05.json` · png → **사용자 확인(자리 · 이름)** 뒤 M2 |
| **M2** | 빌더: 보드 · 컨트롤 · 리밋 · 색 · 라벨 · 더미 노드 3개 · 앞으로 경로 | `.ma` 생성 |
| **M3** | 뒤로 경로 + `bake.py`(copy · reconnect) | 〃 |
| **M4** | `verify.py` T1~T8, `.mb` 저장, `migrate_v04.json` | 검증 통과 파일 |
| **M5** | 문서 · WORKLOG · 메모리, 로컬 커밋 | |
| **M6** (2단계) | UE Control Rig 빌더 (같은 json) | 별도 계획서 |

---

## 7. M0 — 코드 전에 실측으로 확정할 것

| # | 질문 | 방법 |
|---|------|------|
| 1 | **CSV 임포트 툴이 무엇을 보는가** — `BS_Face_CSV` 노드 이름? 별칭 이름? `FaicalMesh_geo`? (어떤 툴인지 Q2) | 툴 코드 · 지금까지 베이크한 씬 하나 열어 animCurve 가 어디 붙었는지 |
| 2 | V04 `jawOpen` · `mouthLowerDown` 등 **부호** — `multiplyDivide20.Y` 가 ×−1 인지, 컨트롤러를 어느 방향으로 끌면 1 이 되는지 | mayapy: 컨트롤 ty 에 ±1 넣고 `BS_Face_Connect_01` 값 읽기 (52 전부 표) |
| 3 | `transformLimits` 가 걸린 ty 에 `BS_Face_CSV` 연결 시 **입력값이 리밋에 잘리는가** (연결값은 리밋 무시인지) | mayapy 2 노드 |
| 4 | `plusMinusAverage(a₊ − a₋)` → ty, 두 attr 이 동시에 1 이면 0 — **ARKit 데이터에서 양쪽이 동시에 뜨는 프레임**이 실제로 있는지(eyeLookUp + eyeLookDown 등) | 기존 CSV 한 개로 통계 |
| 5 | `textCurves` · `transformLimits` · 색(`overrideColorRGB`) 이 `.ma` → `.mb` 저장 왕복에 보존되는지 | mayapy |
| 6 | `bake_ctl_keys(copy)` 이식 — ± 합산 커브를 **키 단위로 빼기**(두 커브 키 시각 합집합) 가 탄젠트를 어떻게 바꾸는지 | mayapy, 샘플 CSV |
| 7 | 기존 베이크 씬에서 V04 컨트롤 키 → `migrate_v04.json` 으로 V05 로 옮겼을 때 `BS_Face_Connect_01` 52 값이 **프레임마다 같은지** | mayapy, 허용 오차 1e-4 |
| 8 | UE Python `add_control` · limits · shape API 이름 (5.x 버전) | UE 에디터 Python 콘솔 (2단계 전) |

---

## 8. 검증 목록 (`verify.py`)

| T | 확인 |
|---|------|
| T1 | 컨트롤 33 · 이름 규칙 · 그룹 7 · 더미 노드 3 이름 그대로 · `BS_Face_CSV` 별칭 52 순서 = V04 · `BS_Face_Connect_01` attr 52 순서 = V04 |
| T2 | 리밋: 종류별 [0,1] / [−1,1] / 턱 [−1,0], 나머지 채널 lock · hidden, keyable 은 tx/ty 만 |
| T3 | 앞으로: 컨트롤마다 축을 ±1 로 두면 해당 attr 만 1, 나머지 51 은 0 (52 × 경우) |
| T4 | 뒤로: `BS_Face_CSV.attr` 를 1 로 두면 해당 컨트롤 축이 ±1, 다른 컨트롤 0; 되돌리면 0 |
| T5 | 왕복: CSV 1 → 컨트롤 → Connect_01 == 1 (52 attr), ± 쌍은 둘 다 0.5 일 때 양쪽 0 (M0-4 와 함께 판단) |
| T6 | 베이크: 샘플 CSV 키 → `bake(copy)` → 뒤로 연결 0개, 컨트롤 animCurve 수 = 33 컨트롤의 쓰인 축 수, 프레임마다 Connect_01 값 == 베이크 전 (1e-4) → `reconnect_csv()` 로 복구 |
| T7 | 좌우 거울: L/R 컨트롤 x 부호만 반대, R 패드 In/Out 부호 거울, 색 L/R/C |
| T8 | `.ma` ↔ `.mb` 왕복 뒤 T1 ~ T5 재통과 · 열 때 에러 0 · `unknown` 노드 0 · legacy renderLayer 0 |

---

## 9. 질문 (답이 없으면 권장안으로)

| Q | 질문 | 권장 |
|---|------|------|
| **Q1** | 뒤로 경로: **direct**(CSV → ctl 직결, 베이크로 끊음) 유지? 아니면 `_drv` 합산(컨트롤러 늘 자유, 베이크 = 복사)? | direct (현행 · JALI 와 같은 선택) |
| **Q2** | CSV 임포트에 쓰는 툴은 무엇인가 (레거시 스크립트? A00110?) — 그것이 `FaicalMesh_geo` · `BS_Face_CSV` 이름을 참조하는지 | M0-1 에서 확인, 이름은 전부 유지 |
| **Q3** | `cheekPuff` 하나를 어디에 — 중앙(코 아래) 하나 / 양쪽 볼에 두 개(둘 다 같은 attr, 베이크 때 하나만) | 중앙 하나 |
| **Q4** | `mouthFunnel` · `mouthPucker` 를 입 중앙 양옆 두 슬라이더로 / 한 ± 슬라이더(+ funnel · − pucker)로 | 두 슬라이더 (둘이 반대 표현이 아니다) |
| **Q5** | 루트의 `Head / Global / World` attr 용도 (머리 따라가기 스위치?) | 유지 · 미연결, 용도를 알려주면 M2 에서 연결 |
| **Q6** | 끌어내리는 표현(browDown · mouthLowerDown · jawOpen · eyeBlink) 을 **−ty** 로(손이 아래로 가면 내려가게) / 전부 +ty 0~1 로 통일 | 아래 표현은 −ty (MetaHuman 식, 직관) — 표 §2-1 이 그 기준 |
| **Q7** | 컨트롤 색 · 크기 · 보드 가로 14 cm 가 지금 작업 화면에 맞는지 (V04 는 13.3 × 25) | 그대로, M1 png 로 확인 |
| **Q8** | UE 빌더(M6)를 이번 묶음에 넣을지, 명세만 맞추고 다음으로 | 다음 (별도 계획서) |

---

## 10. 진행표

| 날짜 | 단계 | 내용 |
|------|------|------|
| 2026-10-26 | 계획 | V04 · MetaHuman 0030 실측(관찰 스크립트 3개) → 이 문서. 코드 · 파일 생성 전 |

---

## 부록 A. V04 컨트롤 → attr 실측표 (이관표 `migrate_v04.json` 의 재료, 부호는 M0-2 에서)

| V04 컨트롤 . 축 | attr | 비고 |
|------|------|------|
| `BS_eyebrowInnerUp_inn_ctl.ty` | browInnerUp | 직결 |
| `BS_eyebrowLeft_inn_ctl.ty` / `BS_eyebrowRight_inn_1_ctl.ty` | browDownLeft / Right | `multiplyDivide68` |
| `BS_eyebrowLeft_out_ctl.ty` / `BS_eyebrowRight_out_ctl.ty` | browOuterUpLeft / Right | 직결 |
| `l_eyeball_ctl.tx` / `.ty` | eyeLookIn/OutLeft · eyeLookUp/DownLeft | `clamp3,4,5,6` · `multiplyDivide14` |
| `r_eyeball_ctl.tx` / `.ty` | eyeLookIn/OutRight · eyeLookUp/DownRight | `clamp7,10` · `multiplyDivide16` |
| `l_eyelid_Up_ctl.ty` / `r_eyelid_Up_ctl.ty` | eyeBlinkLeft / Right | `multiplyDivide18` |
| `l_eyeWide_Up_ctl.ty` / `r_eyeWide_Up_ctl.ty` | eyeWideLeft / Right | 직결 |
| `l_eyelid_Dw_ctl.ty` / `r_eyelid_Dw_ctl.ty` | eyeSquintLeft / Right | 직결 |
| `l_cheekSquint_Dw_ctl.ty` / `r_cheekSquintRight_Dw_ctl.ty` | cheekSquintLeft / Right | 직결 |
| `l_noseSneerLeft_Dw_ctl.ty` / `r_noseSneer_Dw_ctl.ty` | noseSneerLeft / Right | 직결 |
| `BS_checkPuff_ctl.tx` | cheekPuff | 직결 |
| `BS_lipLeft_ctl.tx` / `.ty` | mouthDimpleLeft · mouthSmileLeft / mouthFrownLeft | `clamp15` · `multiplyDivide70` |
| `BS_lipRight_ctl.tx` / `.ty` | mouthDimpleRight · mouthSmileRight / mouthFrownRight | `multiplyDivide59` · `clamp18` · `multiplyDivide26` |
| `BS_lipLow_ctl.tx` / `.ty` | mouthLeft / mouthRight · mouthRollLower | `clamp13` · `multiplyDivide54` |
| `BS_lipTop_ctl.ty` | mouthRollUpper | 직결 |
| `BS_lipTop_leSide_ctl.ty` / `_riSide_` | mouthUpperUpLeft / Right | 직결 |
| `BS_lipLow_leSide_ctl.ty` / `_riSide_` | mouthLowerDownLeft / Right | `multiplyDivide61` |
| `BS_lipTop_leOut_ctl.ty` / `_riOut_` | mouthPressLeft / Right | 직결 |
| `BS_lipLow_leOut_ctl.ty` / `_riOut_` | mouthStretchLeft / Right | `multiplyDivide74` |
| `BS_mouthFunnel_ctl.tx` / `BS_mouthPucker_ctl.tx` | mouthFunnel / mouthPucker | 직결 |
| `c_jaw_rot_ctl.tx` / `.ty` | jawLeft / jawRight · jawOpen | `clamp11` · `multiplyDivide20` |
| `c_jaw_forward_ctl.ty` · `c_mouthClose_ctl.ty` · `c_tongueOut_ctl.ty` | jawForward · mouthClose · tongueOut | 직결 · 직결 · `multiplyDivide76` |
| `c_jaw_mouthShrugUpper_ctl.ty` / `_Lower_` | mouthShrugUpper / Lower | 직결 |
| `BS_cheekLeft/Right_innOut` · `BS_eyebrowLeft/Right_mid` · `BS_lipTop_frontBack` · `BS_noseLeft/Right` | — | **연결 없음** (V05 에서 제거) |
