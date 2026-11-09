---
title: A00610_PmxImporter 계획서
tags: [maya-python, plan, pmx, mmd, importer, skin, blendshape, material]
updated: 2026-11-09
---

# A00610_PmxImporter 계획서

MMD 모델 파일(**PMX 2.0 / 2.1**)을 블렌더 · CATS · FBX 를 거치지 않고 **마야에 바로** 임포트하는 in-Maya PySide 툴(arch B).
결과는 **스킨된 메시 + 조인트 + 블렌드셰이프 + 머티리얼 · 텍스처가 연결된 상태**다.

> 이 문서만 보고 구현할 수 있게 썼다. §2 실측값 · §4 PMX 바이너리 규격 · §5 변환 규칙 · §11 검증 기준이 핵심이다.
> 실측 스크립트: [`A00610_PmxImporter_probe_dump.py`](A00610_PmxImporter_probe_dump.py)(시스템 파이썬, PMX 구조 덤프) ·
> [`A00610_PmxImporter_probe_golden.py`](A00610_PmxImporter_probe_golden.py)(mayapy, 위치 · UV · 감기 · 노멀을 기준 mb 와 대조) ·
> [`A00610_PmxImporter_probe_golden_morph.py`](A00610_PmxImporter_probe_golden_morph.py)(mayapy, 추가 UV · 모프 델타 대조).

> [!success] **v01.00 구현 완료 (2026-11-09)** — `tools/A00610_PmxImporter`
> 시험: 코어 `test_pmx_core.py` **61/61**(합성 PMX · 실제 3 파일) · 마야 `test_import_maya.py` **60/60**(합성 + 기준 mb 골든 G1~G12).
> Miyabi 임포트 1.4초, 기준 mb 대비 위치 2.8e-5 cm · UV 0 · 면 33,528/33,528 · 모프 51개 1.1e-4 · 웨이트 = PMX · 포즈 변형 7.6e-6.
> 계획에서 바뀐 것은 **§13 결정 기록**에 모았다(이름 = FBXASC · lambert 고정 · IK 본 기본 생성 · 텍스처 복사 기본 켬 · undo · ASCII 문자열).
> PMX 안의 나머지 데이터(물리 등)는 **§14**. GUI 실기 확인(§11-3 V3~V7)은 아직.
>
> [!success] **v01.01 2차 1단계 (2026-11-09)** — 부여 본(rotateAxis, 부여 먼저) · IK 근사 · 로컬축 · 표시 프레임 · 엣지 배율.
> Blender + mmd_tools 포즈 메시 대조 포함 mayapy **80/80** → **§15**.

---

## 1. 요구 (2026-11-09 사용자)

| # | 요구 | 결정 |
|---|------|------|
| 1 | 마야에서 PMX 를 **온전하게** 임포트 | 메시 · UV · 노멀 · 본 · 스킨 웨이트 · 버텍스 모프(블렌드셰이프) · 머티리얼 · 텍스처 (§3 범위) |
| 2 | 대상은 대부분 **리깅된 메시 + 본 + 블렌드셰이프** | 스킨 · 블렌드셰이프가 1차 범위의 중심. 물리(강체 · 조인트) · IK · 부여(付与)는 데이터만 보존하고 2차 |
| 3 | PMX 는 `spa/` · `tex/` 의 텍스처를 쓴다 | PMX 안의 상대 경로(`tex\颜.png`)를 PMX 폴더 기준으로 찾아 file 노드에 연결 (§7) |
| 4 | 결과에 **머티리얼 · 텍스처까지 적용** | PMX 재질 1개 = 마야 머티리얼 + SG 1개, 면 범위로 할당 (§7) |
| 5 | 지금은 CATS(블렌더) → FBX → 마야 손질로 하고 있다(`0010_Miyabi_base_02.mb`) | 그 mb 를 **골든 기준**으로 삼아 숫자로 대조한다 (§2, §11) |

---

## 2. 실측 (2026-11-09, 시스템 파이썬 3 + mayapy 2024)

### 2-1. 대상 폴더 `C:\Users\USER\Desktop\JP\0090_Avatar\0010_ZZZ\021_Miyabi`

```
Miyabi.pmx          2.8 MB   본체
武器.pmx             184 KB   무기
幽灵.pmx              37 KB   유령(이펙트, mmd_tools 로 내보낸 것)
skin.bmp hair.bmp toon_defo.bmp   툰 텍스처 (32x32 / 16x16 BMP 24bit)
tex/  体.png 内.png 头饰.png 武器.png 颜.png 髮.png spa_h.png
spa/  stk.png hair_s.bmp
tex_eng/            사용자가 영어 이름으로 바꾼 사본(기준 mb 가 쓰는 것) - PMX 는 참조하지 않는다
readme【一定要看】.txt   배포 금지 · 부품 분해 금지 등 → 모델 · 텍스처를 저장소에 커밋하지 말 것(§11-1)
```

### 2-2. PMX 구조 (probe_dump)

| | Miyabi.pmx | 武器.pmx | 幽灵.pmx |
|---|---|---|---|
| 버전 · 인코딩 | 2.0 · UTF-16LE | 2.0 · UTF-16LE | 2.0 · UTF-16LE |
| 추가 UV | **2** | 0 | 0 |
| 인덱스 크기 v/t/m/b/morph/rb | 2/1/1/2/1/2 | 2/1/1/1/1/1 | 2/1/1/1/1/1 |
| 정점 | 27,086 (BDEF1 8,946 · BDEF2 9,515 · BDEF4 8,625) | 4,008 (BDEF1 3,978 · BDEF2 30) | 759 (BDEF1) |
| 삼각형 | 33,528 | 4,353 | 1,306 |
| 텍스처 | 9 | 2 | 0 |
| 재질 | 23 | 3 | 1 |
| 본 | 436 (IK 4 · 회전부여 30 · 로컬축 38 · 고정축 4 · 비표시 65) | 17 | 1 |
| 모프 | 52 (**전부 vertex**, 패널 눈썹 6 · 눈 15 · 입 31) | 0 | 0 |
| 강체 / 조인트 | 318 / 442 | 12 / 10 | 0 / 0 |

- **텍스처 경로는 `\` 구분 상대 경로**: `tex\颜.png`, `spa\stk.png`, `skin.bmp`(PMX 와 같은 폴더).
- 재질 23개 중 **텍스처는 전부 있음**, 스피어는 `袜` 하나(`spa\stk.png`, 모드 1 = 곱하기), 툰은 개별 BMP(`skin.bmp` · `hair.bmp` · `toon_defo.bmp`).
- `目光2` 는 diffuse 알파 **0.35**, 武器.pmx 의 `刃2` 는 알파 **0.0**(평소 숨김, 재질 모프용으로 보인다).
- 텍스처 알파: `颜.png` · `髮.png` · `内.png` 는 **RGBA**(PNG colortype 6), `体.png` · `头饰.png` · `武器.png` · `stk.png` 는 RGB.
- 모프 영어 이름이 **중복**된다(`Eye_Close_Unagi` ×3, `Mouth_AaTalk_Unagi` ×2 …) → 이름은 반드시 중복을 풀어야 한다(§6).
- 본 · 재질 · 텍스처 이름은 **일본어 · 중국어**(`センター`, `颜`, `髮.png`). 재질 영어 이름은 비어 있다.
- SDEF · QDEF 정점은 이 모델에 없지만 규격상 나올 수 있다(§8-3).

### 2-3. 기준 mb `00_01_03_RIG_01_PJ/scenes/0010_Miyabi_base_02.mb` (probe_golden)

- 씬: cm · Y-up · 메시 **`Body` 하나**(정점 27,086 / 면 33,528 = PMX 와 같은 수, CATS 가 재질별 메시를 하나로 합침).
- `Body` 트랜스폼 = `rotateX -90 · scale 100`(블렌더 FBX 흔적). UV 셋 `UVMap` · `UV1` · `UV2`(= 추가 UV 2개).
- skinCluster: 인플루언스 339(조인트 517 중, CATS 가 안 쓰는 본을 지움 + 사용자가 `apos_*` 등 추가), maxInfluences 5.
- blendShape `Miyabi_ncl1_3`: 타깃 52, 이름이 `FBXASC227FBXASC129…` 로 깨져 있음(UTF-8 바이트를 FBX 가 인코딩), 타깃 메시는 `tgt_grp` 에 남아 있음.
- 머티리얼: phong 23 + file 4(텍스처 이미지별 공유), **색만 연결 — 투명도 연결 없음**, 경로는 다른 PC 의 `E:/109_Avatar/.../tex_eng/*.png`.
- 노멀은 잠겨 있음(locked).

### 2-4. 좌표 · UV · 감기 · 모프 — **PMX ↔ 기준 mb 수치 대조**

| 항목 | 변환 | 기준 mb 와 최대 오차 |
|------|------|------|
| 정점 위치 | **`(x, y, -z) × 8`** (MMD 1 = 8 cm) | **2.8e-5 cm** (27,086 정점 전부, 정점 순서도 같음) |
| UV (`UVMap`) | **`(u, 1 - v)`** | **0** (face-vertex 100,584 개) |
| 추가 UV 1·2 (`UV1` · `UV2`) | **`(x, 1 - y)`** (z · w 는 이 모델에서 전부 0) | **0** |
| 면 감기 | PMX 삼각형 `(a, b, c)` → 마야 **`(c, b, a)`** | 첫 면 PMX `[2,1,0]` → mb `[0,1,2]`. PMX 순서 그대로 쓰면 면 노멀이 마야 노멀과 **0 / 6,706** 일치(전부 반대) |
| 모프 오프셋 | **`(dx, dy, -dz) × 8`** (오브젝트 공간, origin = local) | **6.2e-5 cm** (타깃 10개 대조 — 이후는 CATS 가 이름을 바꿔 자동 매칭 실패) |

- 다른 변환 후보는 확실히 틀림: `(x,y,z)×8` 오차 65.6, `(-x,y,z)×8` 오차 114.
- **PMX `左`(왼쪽) 본이 +X** 에 있다(`左目` x = +0.397 → mb `Eye_L` x = +3.175). 이름의 좌우와 마야 좌표가 일치한다.
- CATS 의 `scale=0.08`(m) 과 같은 값이다(`tools/importer.py`). mmd_tools 는 `Vector(co).xzy * scale` + `flipUV_V` 로 같은 일을 한다.
- 조인트 위치도 같은 변환: PMX `上半身2` y = 13.798 × 8 = 110.38 → mb `Chest` y = 110.388.

---

## 3. 범위

### 1차 (이 계획의 구현 대상)

| 데이터 | 마야 결과 |
|--------|-----------|
| 정점 · 면 · 노멀 | 메시 1개(재질별로 나누지 않음, 정점 순서 = PMX), 노멀은 PMX 값으로 잠금 |
| UV + 추가 UV | `map1` + `UV1` … `UV4` |
| 본 | 조인트(전부, 계층 = PMX 부모), 원본 정보는 어트리뷰트로 보존 |
| 웨이트 BDEF1/2/4 (SDEF · QDEF 는 근사) | skinCluster |
| 버텍스 모프 | blendShape 타깃(지오메트리 없는 델타 직접 입력) |
| 재질 · 텍스처 | 머티리얼 + SG + file 노드(색 · 알파), 툰 · 스피어 · 엣지는 어트리뷰트로 보존 |
| 리포트 | 로그 + 그룹 어트리뷰트 `mmdImportReport`(JSON) |

### 2차 (데이터는 1차에서 보존, 동작은 나중)

IK(`足ＩＫ`) → ikHandle · 회전/이동 부여(`腰キャンセル`, `捩`, `足D`) → 노드 망 · 강체/조인트 물리 ·
재질/UV/본/그룹/플립/임펄스 모프 · 재질별 메시 분리 · 툰/스피어 셰이딩 · A 포즈 변환(기준 폴더의 `0020_Miyabi_base_Apos_01.mb` 작업).

> **주의 — 부여 본에 웨이트가 있다.** `左足D` 등은 MMD 에서 `左足` 의 회전을 따라가는 본이고 웨이트가 실려 있다.
> 1차 결과는 **바인드 포즈에서는 완벽**하지만 `左足` 만 돌리면 `左足D` 에 실린 정점이 따라오지 않는다.
> 애니메이션에 쓰려면 2차의 부여 재현이 필요하다 — UI · 문서에 이 한계를 적는다.

---

## 4. PMX 바이너리 규격 (구현용 요약)

리틀 엔디언. `text` = `int32 바이트 길이` + 바이트(헤더의 인코딩: 0 = UTF-16LE, 1 = UTF-8).
인덱스는 헤더의 크기(1/2/4)대로 읽는다 — **정점 인덱스만 1·2 바이트일 때 unsigned**(`B` · `H`), 4 바이트는 signed.
나머지 인덱스(텍스처 · 재질 · 본 · 모프 · 강체)는 전부 signed(`b` · `h` · `i`), **-1 = 없음**.

```
Header   "PMX " | float version(2.0/2.1) | byte n(=8) | byte[n]:
         encoding, additionalUV(0~4), vIdx, texIdx, matIdx, boneIdx, morphIdx, rigidIdx
         text nameJ, nameE, commentJ, commentE
Vertex   int32 count, each:
         float3 pos | float3 normal | float2 uv | float4 × additionalUV
         byte type: 0 BDEF1 {bone}
                    1 BDEF2 {bone, bone, float w1}           (w2 = 1 - w1)
                    2 BDEF4 {bone×4, float×4}
                    3 SDEF  {bone, bone, float w1, float3 C, float3 R0, float3 R1}
                    4 QDEF  {bone×4, float×4}               (2.1)
         float edgeScale
Face     int32 indexCount, vIdx × indexCount   (3개씩 삼각형)
Texture  int32 count, text path × count
Material int32 count, each:
         text nameJ, nameE | float4 diffuse(RGBA) | float3 specular | float specPower | float3 ambient
         byte flags (0x01 양면 · 0x02 지면 그림자 · 0x04 셀프섀도 맵 · 0x08 셀프섀도 · 0x10 엣지 · 2.1: 0x20 정점색 · 0x40 점 · 0x80 선)
         float4 edgeColor | float edgeSize | texIdx texture | texIdx sphere | byte sphereMode(0 끔 1 곱 2 더하기 3 서브텍스처)
         byte sharedToon → 1 이면 byte toon(0~9 = toon01~10.bmp), 0 이면 texIdx toon
         text memo | int32 faceIndexCount   (재질 순서대로 면 인덱스를 연속으로 차지)
Bone     int32 count, each:
         text nameJ, nameE | float3 pos | boneIdx parent | int32 layer | uint16 flags
         flags&0x0001 ? boneIdx tailBone : float3 tailOffset
         flags&0x0300 (0x100 회전부여 | 0x200 이동부여) ? boneIdx appendParent, float ratio
         flags&0x0400 ? float3 fixedAxis
         flags&0x0800 ? float3 localX, float3 localZ
         flags&0x2000 ? int32 externalParentKey
         flags&0x0020 ? boneIdx ikTarget, int32 loop, float limitRad, int32 linkCount,
                        links: boneIdx, byte hasLimit, [float3 min, float3 max]
         (기타 flags: 0x2 회전가능 0x4 이동가능 0x8 표시 0x10 조작가능 0x80 로컬부여 0x1000 물리후변형)
Morph    int32 count, each: text nameJ, nameE | byte panel(0 시스템 1 눈썹 2 눈 3 입 4 기타) | byte type | int32 n, offsets:
         0 group    {morphIdx, float w}          1 vertex {vIdx, float3 offset}
         2 bone     {boneIdx, float3 move, float4 quat}
         3 uv · 4~7 addUV1~4 {vIdx, float4}     8 material {matIdx, byte op, float × 28}
         9 flip(2.1){morphIdx, float w}          10 impulse(2.1) {rigidIdx, byte local, float3 vel, float3 torque}
DispFrame int32 count, each: text nameJ, nameE, byte special, int32 n, {byte type(0 본 1 모프), idx}
Rigid    int32 count, each: text×2, boneIdx, byte group, uint16 noCollide, byte shape(0 구 1 상자 2 캡슐),
         float3 size, float3 pos, float3 rot, float mass, linDamp, angDamp, restitution, friction, byte mode(0 정적 1 동적 2 동적+본 위치)
Joint    int32 count, each: text×2, byte type, rigidIdx a, b, float3 pos, rot, posMin, posMax, rotMin, rotMax, springPos, springRot
SoftBody (2.1 만) - 1차에서는 읽지 않는다(Joint 뒤에서 멈춰도 된다)
```

- 실측 덤프가 이 규격대로 3 파일 모두 Rigid 끝까지 어긋남 없이 읽었다(Miyabi 는 Joint 개수 442 까지 읽고 남은 61,844 바이트 = Joint 본문).
- **파서는 끝까지 읽지 않아도 된다.** 1차는 Morph · DisplayFrame · Rigid · Joint 의 개수와 이름까지만 쓴다
  (Rigid · Joint 는 개수만 리포트). 단, Rigid/Joint 를 건너뛸 때도 바이트 수를 정확히 세서 2.1 SoftBody 앞에서 멈출 것.

---

## 5. 변환 규칙 (마야 내부 단위 = cm, Y-up)

```python
SCALE = 8.0                                    # UI 옵션, 기본 8 (MMD 1 = 8 cm, CATS 0.08 m 와 같음)
pos_maya    = (x * S, y * S, -z * S)
normal_maya = (nx, ny, -nz)                    # 정규화
uv_maya     = (u, 1.0 - v)                     # map1 / 추가 UV 의 x, y 도 같은 규칙
tri_maya    = (c, b, a)                        # PMX (a, b, c) 를 뒤집는다 - 첫 정점까지 기준 mb 와 같다
morph_delta = (dx * S, dy * S, -dz * S)
bone_pos    = (x * S, y * S, -z * S)           # 월드 위치
```

- `MFnMesh.create` · `setPoints` 등 API 는 **내부 단위(cm)** 로 받으므로 씬 UI 단위가 m 여도 위 값을 그대로 쓴다.
- 씬이 **Z-up** 이면 결과 그룹에 `rotateX = 90` 을 주고 로그에 경고(기본 마야 씬은 Y-up 이라 대부분 해당 없음).
- 회전(강체 · 조인트 등, 2차): 좌표가 z 반전이므로 오일러 각은 `(-rx, -ry, rz)`(mmd_tools 의 `rot.xzy * -1` 과 같은 뜻), 축 벡터는 위치와 같은 규칙.
  MMD 오일러 회전 순서(YXZ 로 알려져 있음)는 2차 구현 때 강체 하나를 놓고 실측으로 확정할 것.
  1차에서는 로컬축(`0x800`) · 고정축(`0x400`)을 **어트리뷰트에 마야 좌표로 변환해 보존**만 한다.

---

## 6. 이름 규칙

> **2026-11-09 사용자 결정으로 바꿨다.** 처음 안(CATS 영어 이름 사전 + 모델별 이름 맵 JSON + `Export Name Map`)은 **폐기**.
> "PMX 가 간직한 고유의 이름이면 좋겠다. 마야로 표현할 수 없는 일어 · 중국어는 FBXASC... 같은 이름이어도 좋다."

마야 노드 이름은 `[A-Za-z_][A-Za-z0-9_]*` 만 된다. PMX 이름은 대부분 일본어/중국어다.

### 6-1. 규칙 (본 · 모프 · 재질 · 텍스처 · 모델 공통, `pmx_convert.encode_name`)

- **PMX 일본어 이름**을 쓴다(비었으면 영어 이름, 그것도 비었으면 `bone_012` · `morph_05` · `mat_07` · `tex_03`).
- FBX 와 같은 규칙: `[A-Za-z0-9_]` 는 그대로, **나머지 글자는 UTF-8 바이트마다 `FBXASC` + 3자리 10진수**.
  첫 글자가 숫자면 그 숫자도 바꾼다(`1` → `FBXASC049`, 기준 mb 의 FBX 결과와 같다). 공백 → `FBXASC032`.
  - `まばたき` → `FBXASC227FBXASC129FBXASC190FBXASC227FBXASC129FBXASC176FBXASC227FBXASC129FBXASC159FBXASC227FBXASC129FBXASC141`
  - `刃2` → `FBXASC229FBXASC136FBXASC1312` (항상 3자리라 뒤의 `2` 와 헷갈리지 않는다)
- **`decode_name` 으로 원래 글자가 정확히 돌아온다**(시험: `左足ＩＫ` · `体(上)` · `Mouth_↙oo_Unagi` · `1.001` 왕복).
  다른 세션의 `A00620_NameDecoder`(FBXASC 이름 읽기 툴)와 같은 표기라 그 툴로도 읽힌다.
- **중복**은 뒤에 `_1`, `_2`. 씬에 이미 있는 이름(만들 네임스페이스 기준)도 피한다 — 같은 모델을 두 번 넣어도 마야가 숫자를 붙이지 않는다.
- 모델 그룹 이름 = PMX 안의 모델 이름(`Unagi` → `Unagi_grp`), 파일 이름이 아니다.

### 6-2. 원본 이름 보존 — **문자열 어트리뷰트는 ASCII 만**

★ 실측(2026-11-09): **`.ma` 는 시스템 코드페이지(cp949)로 저장**되어 그 밖의 글자(`颜` · `体`)가 `?` 로 깨진다. `.mb` 는 괜찮다.
그래서 모든 `mmd*` 문자열은 ASCII 로 쓴다 — 이름은 FBXASC, 글 · JSON 은 유니코드 이스케이프(`json.loads` 로 그대로).

| 어트리뷰트 | 붙는 곳 | 값 (읽는 법) |
|------------|---------|-----|
| `mmdName` · `mmdNameE` | 조인트 · 머티리얼 | PMX 일본어 / 영어 이름 FBXASC (`decode_name`) |
| `mmdIndex` | 조인트 · 머티리얼 | PMX 인덱스(long) |
| `mmdData` | 조인트 · 머티리얼 | JSON(ASCII) — 본: 플래그 · 꼬리 · 부여 · 축 · IK / 재질: 색 · 플래그 · 엣지 · 텍스처 · 스피어 · 툰 · 메모 |
| `mmdMorphs` | blendShape | JSON `{alias: {index, name, nameE, panel}}` |
| `mmdModelName(E)` · `mmdComment` · `mmdSourceFile` · `mmdImporterVersion` · `mmdImportReport` | 결과 그룹 | 이름 = FBXASC, 글 = JSON 문자열 본문(`json.loads('"' + 값 + '"')`), 리포트 = JSON |

---

## 7. 머티리얼 · 텍스처

### 7-1. 텍스처 경로 찾기 (`texture_resolver.py`, 마야 비의존)

1. PMX 경로의 `\` → `/`, PMX 폴더 기준으로 합친다(절대 경로면 그대로).
2. 있으면 끝. 없으면 **대소문자 무시**로 같은 경로를 찾는다(Windows 에서는 보통 1에서 끝난다).
3. 그래도 없으면 PMX 폴더 아래(깊이 3까지)에서 **같은 파일 이름**을 찾는다 — 여럿이면 경로가 가장 짧은 것 + 경고.
4. 못 찾으면 **file 노드는 만들되** 경로는 원래 값을 PMX 폴더 기준 절대 경로로, 로그에 `Missing texture` + 리포트.

### 7-2. 노드 구성

```
PMX 재질 i ─▶ <mat>  (기본 lambert, 옵션 standardSurface)
              └─ <mat>SG ─▶ mesh.f[start:end]   (면 범위 = 앞 재질들 faceIndexCount 누적 / 3)
PMX 텍스처 t ─▶ file "<tex>_file" + place2dTexture 하나   (같은 텍스처를 쓰는 재질끼리 공유 - 기준 mb 와 같음)
```

| PMX | lambert (기본) | standardSurface (옵션) |
|-----|----------------|------------------------|
| 텍스처 있음 | `file.outColor → color` | `file.outColor → baseColor` |
| 텍스처 없음 | `color = diffuse.rgb` | `baseColor = diffuse.rgb` |
| 텍스처 **알파 있음**(§7-3) | `file.outTransparency → transparency` | `file.outAlpha → opacity(r,g,b)` |
| diffuse 알파 < 1 | 알파와 곱한다(아래) | 〃 |
| specular · ambient · edge · toon · sphere | 어트리뷰트로 보존(아래) | 〃 |

- 기본 lambert 인 이유: 뷰포트에서 바로 보이고 FBX · UE 로 넘길 때 가장 무난하다. `diffuse = 1.0` 으로 둔다(텍스처 색 그대로).
- 알파 합성: diffuse 알파 `a` < 1 이고 텍스처 알파도 있으면 `multiplyDivide(file.outAlpha × a)` → `reverse` → transparency.
  텍스처 알파가 없으면 `transparency = (1-a, 1-a, 1-a)`. **`a = 0`(武器 `刃2`)** 도 그대로 투명 0 으로 만들고 로그에 `hidden material` 경고.
- file 노드: `colorSpace = sRGB`, `fileTextureName` = 절대 경로, `alphaIsLuminance = 0`.
- 텍스처 없는 재질(幽灵.pmx): color 만, file 노드 없음.
- 보존 어트리뷰트(머티리얼에): `mmdDiffuse`(float4) · `mmdSpecular` · `mmdSpecularPower` · `mmdAmbient` · `mmdFlags` · `mmdEdgeColor` · `mmdEdgeSize` ·
  `mmdToon`(파일 경로 또는 `toon01.bmp`) · `mmdSphere` · `mmdSphereMode` · `mmdMemo`.
- **양면(flag 0x01)**: 마야 `doubleSided` 는 셰이프 단위라 1차는 셰이프 기본(양면)을 그대로 두고 플래그만 보존.

### 7-3. 텍스처 알파 판정 (헤더만 읽는다, PIL · numpy 금지)

| 형식 | 알파 있음 조건 |
|------|----------------|
| PNG | IHDR colortype 4 · 6, 또는 `tRNS` 청크 |
| TGA | 픽셀 깊이 32 또는 이미지 디스크립터 알파 비트 > 0 |
| BMP | bpp 32 |
| DDS | `DDPF_ALPHAPIXELS` 또는 DXT3/DXT5/BC7 → 있음으로 본다 |
| 기타 | 없음으로 보고 리포트 |

Miyabi 실측으로 `颜` · `髮` · `内` 가 알파 있음 — 눈 · 속눈썹 · 머리카락 끝이 투명해야 맞다(기준 mb 는 이 연결이 빠져 있다).

### 7-4. 비 ASCII 파일 경로 — **실측 결과 (2026-11-09, mayapy 2024, 시스템 코드페이지 cp949)**

- `cmds.setAttr(file.fileTextureName, "…/tex/颜.png")` → 되읽으면 **`…/tex/?.png`**, `outSize = 0`(이미지를 못 읽음). MEL 도 같다.
- API `MPlug.setString` 은 글자는 그대로 남지만 **역시 `outSize = 0`**. `体.png` 도 실패(cp949 에 없는 간체자).
- 8.3 짧은 경로(`59F8~1.PNG`)는 읽히지만 볼륨 설정에 따라 없고 다른 PC 로 못 옮긴다 → 쓰지 않는다.
- **결정**: 경로를 `cmds.about(codeset=True)` 코드페이지로 인코딩할 수 없으면 `<PMX 폴더>/maya_textures/<FBXASC(상대 경로)>.<확장자>` 로 복사
  (`tex/颜.png` → `maya_textures/texFBXASC047FBXASC233FBXASC162FBXASC156.png`, `/` 까지 인코딩해 `decode_name` 으로 원래 경로가 나온다).
  크기 · 수정 시각이 같으면 다시 복사하지 않는다. Miyabi: `颜` · `体` · `头饰` · `内` 4장 복사, `髮`(cp949 에 있음) · `武器` 는 원본 그대로.
  옵션 `Copy unreadable textures`(기본 켬). 아래 원래 계획 문단은 기록으로 남긴다.

(원래 계획) **검증 항목 V3**

텍스처 파일 이름이 `颜.png` · `髮.png` 이다. 마야 2024 file 노드가 비 ASCII 경로를 **뷰포트에서 실제로 그리는지** GUI 에서 확인한다.
안 되면 옵션 `Copy textures to ASCII names`(기본 끔): `<워크스페이스>/sourceimages/<모델>/` 에 §6 텍스처 이름으로 복사해 그 경로를 연결
(원본은 건드리지 않는다). 사용자의 `tex_eng/` 폴더가 바로 이 작업을 손으로 한 결과다.

---

## 8. 메시 · 스켈레톤 · 스킨 · 모프

### 8-1. 메시 (`maya_mesh.py`)

- `om.MFnMesh().create(points, [3]*nTri, connects(c,b,a), uValues, vValues, parent=transform)` 한 번. **정점 순서 = PMX** (모프 · 웨이트 인덱스가 그대로 맞는다).
- UV: uvId = 정점 번호(PMX 는 정점당 UV 하나) → `assignUVs(counts, connects)`. 기본 셋 이름 `map1`(마야 관례, 옵션으로 `UVMap`).
- 추가 UV k: `createUVSet("UV{k}")` → `setUVs` · `assignUVs`. z · w 가 0 이 아닌 정점이 있으면 리포트(버린다).
- 노멀: `setVertexNormals(normals, range(nv))` 로 잠근다(옵션 `Import normals`, 기본 켬). 쓴 뒤 `cmds.dgdirty(shape)`.
  면 · 정점이 같은 노멀이라 face-vertex 로 쓸 필요 없다(쪼개지면 무거워진다 — 메모 skincluster-deforms-user-normals).
- 모든 엣지 soft(노멀을 잠그면 셰이딩은 노멀이 정한다).
- 이름: `<model>_mesh`, 트랜스폼은 항등(기준 mb 의 `rotateX -90 · scale 100` 같은 것 없음).

### 8-2. 스켈레톤 (`maya_skeleton.py`)

1. 모든 본을 **먼저 월드 위치로** 만들고(`cmds.createNode("joint")` + `xform -ws -t`), 그다음 부모를 연결한다
   — PMX 는 부모 인덱스가 자식보다 뒤에 올 수 있다. 부모 연결은 `cmds.parent` 대신 **로컬 translate 를 계산해 직접 넣는다**(월드 정렬이라 `t = pos - parentPos`).
2. `jointOrient = 0`, `rotate = 0` — MMD 본은 레스트 회전이 없다. (조인트 방향 정렬 옵션은 2차: X 를 tail 쪽으로 · 로컬축 0x800 반영)
3. 부모가 -1 인 본 = `<model>_skel_grp` 아래 최상위(`全ての親` · `操作中心` · IK 친 본 등).
4. `radius` = 모델 높이 × 0.004 (Miyabi 약 0.7). 비표시 본(flag 0x08 꺼짐)은 `drawStyle = 2(None)` — 옵션 `Hide invisible bones`(기본 켬).
5. 보존 어트리뷰트: `mmdName` · `mmdNameE` · `mmdIndex` · `mmdFlags` · `mmdLayer` · `mmdTail`(본 인덱스 또는 오프셋, 마야 좌표) ·
   `mmdAppendParent` · `mmdAppendRatio` · `mmdFixedAxis` · `mmdLocalX` · `mmdLocalZ` · `mmdIK`(JSON: target · loop · limit · links[{bone, min, max}]).
   → 2차의 IK · 부여 재현이 이 어트리뷰트만 읽고 만들 수 있게.
6. 옵션 `Skip unweighted IK bones`(기본 끔): IK 본(0x20) · IK 친 본 중 웨이트가 없고 자식도 그런 본은 만들지 않는다.

### 8-3. 스킨 (`maya_skin.py`)

- 인플루언스 = 웨이트가 0 보다 큰 정점이 하나라도 있는 본(Miyabi 예상 300 대).
- `cmds.skinCluster(joints, mesh, toSelectedBones=True, bindMethod=0, maximumInfluences=4, obeyMaxInfluences=False, normalizeWeights=1, name=...)`.
- 웨이트는 **`MFnSkinCluster.setWeights` 한 번**(전체 정점 × 인플루언스 행렬, 인덱스는 **물리** = `range(len(influenceObjects()))` —
  메모 skincluster-weight-index-physical, 공용 `Framework.core.maya_skin.weight_indices()`). 27,086 × 339 ≈ 920만 double(≈ 73 MB) — 괜찮다.
  정점 10만 이상이면 1만 정점씩 나눠 쓴다.
- 타입별:
  - BDEF1 `{b: 1}` · BDEF2 `{b1: w, b2: 1-w}` · BDEF4 `{b_i: w_i}`
  - 같은 본이 두 번 나오면 **더한다**, 본 -1 · 웨이트 0 은 버린다, 합이 1 이 아니면 **정규화**(리포트에 개수).
  - **SDEF** → BDEF2 로(선형). 옵션 `SDEF/QDEF as dual quaternion`(기본 켬): `skinningMethod = 2`(weight blended) + 그 정점만 `blendWeights = 1`.
    C · R0 · R1 은 버린다(리포트에 개수).
  - **QDEF** → BDEF4 + 위와 같은 DQ 블렌드.
- 바인드는 조인트가 레스트일 때 하므로 `bindPreMatrix` = 조인트 월드 역행렬, dagPose 생성(마야 기본).

### 8-4. 모프 → blendShape (`maya_morph.py`)

- **스킨보다 먼저** 만든다(디포머 순서 blendShape → skinCluster). 나중에 만들면 `frontOfChain=True`.
- `cmds.blendShape(mesh, name="<model>_morphs", origin="local")` 로 빈 노드를 만들고, 타깃마다 직접 쓴다:
  ```
  bs.inputTarget[0].inputTargetGroup[i].inputTargetItem[6000].inputPointsTarget     ← MFnPointArrayData (델타, cm)
  bs.inputTarget[0].inputTargetGroup[i].inputTargetItem[6000].inputComponentsTarget ← MFnComponentListData (vtx 인덱스)
  bs.weight[i] = 0,  aliasAttr <이름> bs.weight[i]
  ```
  → **V1 실측 통과(2026-11-09)**: 값 1 에서 델타대로 움직이고, FBXASC 별칭과 함께 `.mb` · `.ma` 저장 왕복에서 산다
  (`blendShape -q -t` 는 빈 목록 — 지오메트리 타깃이 없으니 정상). Shape Editor 표시는 GUI 확인(V5).
  (원래 계획) **검증 항목 V1**: 이 방식으로 만든 타깃이 (1) 값 1 에서 델타대로 움직이는지 (2) Shape Editor 에 이름으로 보이는지
  (3) `.mb` 저장 · 다시 열기 왕복에서 살아남는지 mayapy 로 먼저 확인한다. 안 되면 폴백: 임시 타깃 메시를 만들어
  `blendShape -e -t` 로 넣고 지운다(느리지만 확실, 52 타깃은 문제없다).
- 델타 0 인 정점은 넣지 않는다(PMX 오프셋 목록 그대로가 이미 희소).
- 버텍스 모프가 아닌 모프(그룹 · 본 · UV · 재질 · 플립 · 임펄스)는 리포트에 종류 · 이름만. 그룹 모프는 2차에 "구성 모프 가중치 연결"로.
- 버텍스 모프가 0 개면 blendShape 를 만들지 않는다(武器 · 幽灵).

---

## 9. 결과 씬 구조

```
<model>_grp                       (mmdModelName · mmdModelNameE · mmdComment · mmdSourceFile · mmdImporterVersion · mmdImportReport)
├── <model>_geo_grp
│   └── <model>_mesh              blendShape <model>_morphs → skinCluster <model>_skinCluster
└── <model>_skel_grp
    ├── <全ての親 → 이름>          … PMX 계층 그대로
    └── <操作中心 → 이름>
```

- `<model>` = §6 규칙으로 정한 모델 이름(Miyabi → PMX 이름 `Unagi`. 파일 이름이 아니라 PMX 안의 이름).
- 무기 · 유령처럼 여러 PMX 를 한 씬에 넣으면 그룹이 따로 생긴다(네임스페이스로 충돌 방지).

---

## 10. 툴 구조 · UI

> **v01.00 실제 구성** (아래 원래 계획과 다른 점: 이름 사전 · 이름 맵 없음, 마야 쪽은 한 파일, UI 에서 Material 콤보 · Export Name Map 빠짐)
> ```
> app/core/pmx_reader.py        PMX 2.0/2.1 파서 (마야 비의존) - 강체 · 조인트 본문까지, 2.1 소프트바디는 개수만
> app/core/pmx_convert.py       좌표 · UV · 감기 · 웨이트 정리 · 본 생성 순서 · FBXASC encode/decode · NameBook (마야 비의존)
> app/core/texture_resolver.py  경로 찾기 · 알파 판정 · 코드페이지 판정 · maya_textures 복사 (마야 비의존)
> app/core/maya_build.py        메시 · 재질 · 스켈레톤 · 모프 · 스킨 (+ ASCII 문자열 어트리뷰트)
> app/core/import_runner.py     ImportOptions · run_import(단계 · undo 청크 · 네임스페이스 · 리포트)
> app/ui/main_window.py         File/Browse/Read · Info(요약 + 텍스처 상태 트리) · Import 체크 9개 · Scale · UV set · Namespace · Import · 로그
> tests/pmx_writer.py · test_pmx_core.py · test_import_maya.py
> ```

```
tools/A00610_PmxImporter/           ← A00008_base_QT_maya 복제로 시작
├── __init__.py · launch.py · __dragDrop_A00610.py
├── icon/A00610_PmxImporter.svg (+png, 32x32, 공통 배경 틀)
├── CHANGELOG.md
├── app/
│   ├── config/version.py
│   ├── data/mmd_names_ja_en.json          # 내장 이름 사전 (§6-1)
│   ├── core/                               # ── 아래 4개는 마야 비의존 (시스템 파이썬에서 테스트)
│   │   ├── pmx_reader.py      # PmxModel (header, vertices, faces, textures, materials, bones, morphs, counts)
│   │   ├── pmx_convert.py     # §5 변환 + 웨이트 정리(합치기 · 정규화 · SDEF) - 순수 함수
│   │   ├── name_resolver.py   # §6 이름 결정 + 이름 맵 JSON 읽기/쓰기
│   │   ├── texture_resolver.py# §7-1 경로 + §7-3 알파 판정
│   │   │                                   # ── 아래는 maya
│   │   ├── maya_mesh.py · maya_skeleton.py · maya_skin.py · maya_morph.py · maya_material.py
│   │   └── import_runner.py   # 단계 순서 · progress 콜백 · 리포트 (UI 모름)
│   └── ui/main_window.py
└── tests/
    ├── test_pmx_reader.py     # 합성 PMX(아래) + 실제 파일(있을 때만)
    ├── test_convert_names.py
    └── test_import_maya.py    # mayapy: 골든 대조 G1~G9
```

- 툴 간 import 금지(릴리즈 레이아웃). 공용으로 쓸 것은 `Framework` 에 있는 것만: `maya_undo` · `maya_skin.weight_indices` · 로그 · 진행 팝업 · 메뉴바 · tabFit.
- 파이썬 3.9 문법(마야 2023 호환), numpy · PIL 금지, PySide 는 `Framework.qt.qt` 로(2024 = PySide2, 2025 = PySide6).
- `pmx_reader` 는 나중에 다른 툴(A00210 미리보기 등)도 쓸 수 있으면 `Framework/core/pmx_reader.py` 로 승격한다(1차는 툴 안).

### 10-1. UI (영어 문자열)

```
┌ PMX Importer ───────────────────────────────────────────────┐
│ File  [C:/.../021_Miyabi/Miyabi.pmx              ] [Browse] │
│       [Read]                                                │
│ ┌ Info ─────────────────────────────────────────────────┐   │
│ │ Model: Unagi (Unagi)   PMX 2.0  UTF-16                │   │
│ │ Vertices 27,086  Triangles 33,528  Materials 23       │   │
│ │ Bones 436  Morphs 52 (vertex 52)  Rigid 318  Joints 442│  │
│ │ Textures  ✔ tex/颜.png  ✔ tex/髮.png ... ✖ (missing)  │   │
│ └───────────────────────────────────────────────────────┘   │
│ Import:  ☑ Mesh  ☑ Skeleton  ☑ Skin  ☑ Morphs  ☑ Materials  │
│ Scale [8.0] (MMD unit → cm)   Namespace [Miyabi] ☑          │
│ Material [Lambert ▾]   UV set name [map1 ▾]                 │
│ ☑ Import normals  ☑ Hide invisible bones                    │
│ ☐ Skip unweighted IK bones  ☑ SDEF/QDEF as dual quaternion  │
│ ☐ Copy textures to ASCII names                              │
│ [Export Name Map...]  [Open Name Map]          [Import]     │
│ ── Log ─────────────────────────────────────────────────    │
└─────────────────────────────────────────────────────────────┘
```

- `Read` = 파서만 돌려 Info 를 채운다(씬을 건드리지 않음). 텍스처 줄은 공용 트리/리스트(찾음 ✔ / 없음 ✖ 빨강), viewZoom 붙이기.
- `Import` = 진행 팝업(`JUN_mod_progress_qt_v01`) 단계: Read 10 · Mesh 15 · Materials 10 · Skeleton 10 · Morphs 20 · Skin 30 · Finish 5.
- 옵션은 `optionVar` 로 기억(파일 경로 최근 5개 포함). 메뉴바는 공용 `COMMON_MENUS`.
- 끝나면 결과 그룹을 선택하고 로그에 요약: 만든 노드 수 · 빠진 텍스처 · 정규화한 정점 수 · SDEF 개수 · 건너뛴 모프 종류.

### 10-2. undo

> **실측(V2, 2026-11-09)으로 바뀜**: 트랜스폼을 `cmds.createNode` 로 만들고 그 **아래에** `MFnMesh.create(parent=...)` 로 셰이프를 만들면
> undo 청크 하나로 트랜스폼과 셰이프가 같이 사라진다. 웨이트 · 노멀 · 블렌드셰이프 타깃(API 쓰기)은 노드째 사라지므로 상관없다.
> → **임포트 전체가 `undo_chunk()` 하나, Ctrl+Z 한 번에 통째로 되돌아간다**(시험: 노드 목록이 임포트 전과 같다).
> `Remove Last Import` 버튼은 만들지 않았다. redo 는 보장하지 않는다(API 쓰기는 다시 실행되지 않는다).
> ★ 노멀 확인 함정: `MFnMesh.getVertexNormal` 은 **잠긴 사용자 노멀을 무시**하고 기하 평균을 준다 — `getFaceVertexNormal` · `polyNormalPerVertex -q` 로 읽을 것.

(원래 계획)

`MFnMesh.create` · `MFnSkinCluster.setWeights`(undo 인자 없이) 는 마야 undo 에 남지 않는다 — 그래서 **임포트는 Ctrl+Z 로 되돌리지 않는다**고 정한다.
- 전체를 `undo_chunk()` 로는 감싸되(cmds 부분), 창에 `Undo is not supported - use Remove Last Import` 안내.
- 버튼 `Remove Last Import`: 마지막 결과 그룹 + 그 아래 노드 + 이 임포트가 만든 머티리얼 · SG · file · place2d 노드(그룹 어트리뷰트에 목록 저장)를 지운다.
- **검증 항목 V2**: `MFnMesh.create` 대신 `MDagModifier` 를 쓰면 undo 가 되는지, 되면 그쪽으로 바꾼다.

---

## 11. 검증

### 11-1. 테스트 데이터

- **모델 · 텍스처를 저장소에 넣지 않는다**(readme: 재배포 금지). 실제 파일 시험은 환경 변수 `A00610_SAMPLE_DIR`
  (기본 `C:/Users/USER/Desktop/JP/0090_Avatar/0010_ZZZ/021_Miyabi`) 가 있을 때만 돌고 없으면 SKIP.
- **합성 PMX**: 테스트가 직접 작은 PMX 를 써서 읽는다(쓰기 함수는 tests 안에). 덮을 것:
  UTF-8 / UTF-16 · 인덱스 크기 1/2/4(정점 1·2 바이트 unsigned 경계값 255 · 65535) · BDEF1/2/4 · SDEF · QDEF · 추가 UV 0~4 ·
  공유 툰 / 개별 툰 · 텍스처 -1 · 부모가 뒤에 오는 본 · IK 링크(제한 있음/없음) · 모든 모프 타입 · PMX 2.1 SoftBody 앞에서 멈춤.

### 11-2. 골든 대조 (mayapy, 기준 = `0010_Miyabi_base_02.mb`, probe_golden 이 이미 하는 계산)

| # | 항목 | 통과 기준 | 오늘 실측 |
|---|------|-----------|-----------|
| G1 | 정점 위치: 임포트 메시 vs `BodyShapeOrig` 월드 | 최대 오차 ≤ 1e-4 cm | 2.8e-5 |
| G2 | UV `map1` vs `UVMap`, `UV1` · `UV2` vs mb 같은 이름 | 0 | 0 |
| G3 | 면 정점 목록: 면 i 가 mb 면 i 와 같은 순환 순서 | 33,528 / 33,528 | 첫 면 일치 확인 |
| G4 | 모프 델타 vs `tgt_grp` 타깃 - 베이스(이름은 FBXASC 디코드 = UTF-8 바이트) | ≤ 1e-4 cm, 52개 중 매칭되는 전부 | 6.2e-5 (10개) |
| G5 | 스킨: skinCluster 에서 다시 읽은 정점별 {본: w} vs PMX 정리 결과 | ≤ 1e-6 | - |
| G6 | 조인트 월드 위치 vs PMX `(x,y,-z)×8` | ≤ 1e-4 | - |
| G7 | 재질: SG 23개, SG 별 면 수 = PMX faceCount/3, file 노드 경로 존재, RGBA 텍스처만 투명도 연결 | 정확히 일치 | - |
| G8 | 바인드 포즈 변형: 스킨 출력 = 입력(조인트 안 움직임) | ≤ 1e-4 | - |
| G9 | 포즈 테스트: `左ひじ` 를 90° 돌렸을 때 PMX 웨이트로 직접 계산한 LBS 위치와 스킨 출력 | ≤ 1e-3 (DQ 정점 제외) | - |
| G10 | 武器.pmx · 幽灵.pmx 임포트 오류 없음, 幽灵 은 file 노드 0 · 武器 `刃2` 투명 | - | - |
| G11 | 시간: Miyabi 전체 임포트(mayapy) | < 15 초 | - |
| G12 | `.mb` 저장 → 다시 열기 후 G1 · G4 · G5 · G7 다시 통과(별칭 · 어트리뷰트 유지) | - | - |

> G5 를 기준 mb 와 직접 비교하지 않는 이유: CATS 가 본을 지우고 합치며(436 → 인플루언스 339), 사용자가 조인트를 추가했다.
> 웨이트의 정답은 PMX 자체다. 대신 G9 로 "변형이 MMD 수식과 같다"를 확인한다.

### 11-3. GUI 확인 (사용자, 실기)

| # | 확인 |
|---|------|
| V3 | 비 ASCII 텍스처 경로가 뷰포트(Viewport 2.0, Textured)에 보인다 |
| V4 | 눈 하이라이트(`目光2` 0.35) · 속눈썹 · 머리카락 끝 투명이 자연스럽다(정렬 문제 있으면 `transparencyAlgorithm` 안내) |
| V5 | Shape Editor 에 모프 52개가 이름으로 보이고 슬라이더가 움직인다 |
| V6 | 조인트를 돌리면 메시가 따라온다(부여 본 한계 §3 확인) |
| V7 | FBX 로 내보내 UE 에 넣었을 때 스켈레톤 · 모프 · 머티리얼 슬롯이 들어간다(1차 마무리 후) |

---

## 12. 구현 순서

| 단계 | 내용 | 끝 조건 |
|------|------|---------|
| M0 | `A00008_base_QT_maya` 복제 → `A00610_PmxImporter`, 아이콘 · `__dragDrop_A00610.py` · version 01.00 | 셸프 설치 · 빈 창 열림 |
| M1 | `pmx_reader` + 합성 PMX 시험 + 실제 3 파일 읽기 | 숫자가 §2-2 표와 같다 |
| M2 | `pmx_convert` · `name_resolver`(사전 1차분) · `texture_resolver` | 시스템 파이썬 시험 통과 |
| M3 | V1 · V2 mayapy 확인(blendShape 직접 입력 · undo) → 결과를 이 문서 §8-4 · §10-2 에 적는다 | 방식 확정 |
| M4 | 메시(위치 · 면 · UV · 추가 UV · 노멀) | G1 · G2 · G3 |
| M5 | 머티리얼 · 텍스처 | G7 · G10 일부 |
| M6 | 스켈레톤 + 스킨 | G5 · G6 · G8 · G9 |
| M7 | 모프 | G4 |
| M8 | UI · 리포트 · 이름 맵 내보내기 · Remove Last Import | G10 · G11 · G12 |
| M9 | 문서 · 등록: `docs/A00610_PmxImporter.md`(안내) · CHANGELOG · WORKLOG · 루트 README 툴 표 · A00370 ToolLauncher 버튼 · portfolio EN/KR | GUI 확인(V3~V6) 요청 |

각 단계 끝에 로컬 커밋(푸시는 요청 시에만).

---

## 13. 결정 기록 · 열린 질문

| 항목 | 결정 (v01.00 구현) | 근거 |
|------|------------------|----------|
| 메시 | 하나로(정점 순서 = PMX, 기준 mb 와 같음) | 재질별 분리는 2차 옵션 |
| 단위 | ×8 → cm | UI `Scale` |
| 조인트 방향 | 월드 정렬(jointOrient 0) | MMD 원본과 같고 변환 오차가 없다. 2차 `Orient joints` |
| 이름 | **PMX 고유 이름, 못 쓰는 글자는 FBXASC** (§6) | **사용자 결정 2026-11-09** (CATS 이름 · 이름 맵 JSON 폐기) |
| 머티리얼 타입 | **lambert 고정** | **사용자 결정 2026-11-09** (타입 고르는 UI 는 만들지 않음) |
| IK 본 | **기본으로 만든다**(웨이트 없어도) | **사용자 결정 2026-11-09** (`Skip unweighted IK bones` 옵션은 만들지 않음) |
| 텍스처 경로 | 코드페이지로 못 읽는 경로만 `maya_textures/` 에 FBXASC 이름으로 복사, **기본 켬** | 실측: 마야가 `颜` 경로를 `?` 로 바꿔 못 읽는다(§7-4) |
| undo | **Ctrl+Z 한 번 = 임포트 통째로**, `Remove Last Import` 버튼 없음 | 실측 V2 통과(§10-2) |
| 문자열 어트리뷰트 | ASCII 만 | 실측: `.ma` 코드페이지 손실(§6-2) |
| 모듈 | `maya_mesh` 등 5개 → **`maya_build.py` 하나**, `name_resolver` → `pmx_convert` 에 합침 | 규모가 작아 나눌 이득이 없었다 |
| IK · 부여 · 물리 | 데이터만 보존 | 2차 (§14) |
| 툴 번호 | A00610 | ★ 09:31 다른 세션이 같은 번호로 NameDecoder 계획을 먼저 커밋 → 그쪽이 **A00620** 으로 옮김(2026-11-09). 이 툴이 A00610 |

---

## 14. PMX 안의 데이터 전체 — 본 · 메시 · 블렌드셰이프 말고 무엇이 있나 (사용자 요청 2026-11-09)

PMX 는 아래 10 구획이 순서대로 들어 있다(§4 규격). 개수는 `pmx_reader` 로 Miyabi.pmx 를 읽은 실측. **v01.00** 열 = 지금 임포트가 하는 일.

| 구획 | 들어 있는 것 | Miyabi.pmx | v01.00 | 2차에서 할 수 있는 것 |
|------|-------------|------------|--------|------------------------|
| **헤더 · 모델 정보** | 버전, 글자 인코딩, 추가 UV 수, 인덱스 크기, 모델 이름(일/영), **주석**(배포 조건 등) | 2.0 · UTF-16 · 추가 UV 2 · 이름 `Unagi` · 주석 = readme 와 같은 이용 조건 | 그룹 어트리뷰트(`mmdModelName` · `mmdComment`) | - |
| **정점** | 위치 · 노멀 · UV · **추가 UV 4개까지(float4)** · 웨이트(BDEF1/2/4 · **SDEF** · **QDEF**) · **엣지 배율** | 27,086 · BDEF1 8,946 / BDEF2 9,515 / BDEF4 8,625 · 엣지 배율 전부 1.0 | 메시 · UV1/UV2 · 스킨 · SDEF/QDEF → DQ | 엣지 배율 → 컬러 셋(외곽선 굵기용) · SDEF 의 C/R0/R1 로 정확한 SDEF 디포머 |
| **면** | 삼각형 인덱스 | 33,528 | 메시 | - |
| **텍스처 목록** | 경로 문자열(색 · 스피어 · 개별 툰이 같은 목록을 나눠 씀) | 9 = 색 5(`颜` `髮` `头饰` `体` `内`) · 툰 3(`skin.bmp` `hair.bmp` `toon_defo.bmp`) · 스피어 1(`spa\stk.png`). 폴더의 `tex\spa_h.png` · `spa\hair_s.bmp` 는 PMX 가 안 씀 | 색 텍스처만 file 노드 | 툰 · 스피어 셰이딩 |
| **재질** | 확산색+알파 · 반사색/반사 강도 · 환경색 · **플래그**(양면 · 지면 그림자 · 셀프섀도 · **엣지(외곽선)**) · **엣지 색/굵기** · 텍스처 · **스피어 + 모드(곱/더하기/서브텍스처)** · **툰(공유 toon01~10 / 개별)** · 메모 · 면 수 | 23 · 플래그 0x1f 12 / 0x0f 6 / 0x03 4 / 0x0e 1 · 엣지 굵기 0.5 ×14, 1.0 ×9 · 스피어 `袜` 1 | lambert(색 · 알파) + 나머지는 `mmdData` | 툰 램프 · 스피어(matcap) · 외곽선(인버티드 헐 또는 툰 셰이더) · 양면 플래그 → 재질별 메시 분리 시 `doubleSided` |
| **본** | 위치 · 부모 · **변형 계층(layer)** · 플래그(회전/이동 가능 · 표시 · 조작 가능 · **물리 후 변형**) · 꼬리 · **부여(付与, 회전/이동, 비율)** · **고정축** · **로컬축** · **외부 부모** · **IK**(타깃 · 반복 · 각도 제한 · 링크별 회전 제한) | 436 · IK 4(`左足ＩＫ`: 링크 `左ひざ`(제한 있음) · `左足`) · 부여 30 · 고정축 4(`腕捩` · `手捩`) · 로컬축 38(팔 · 손가락) · 계층 0:416 / 1:12 / 2:8 · 외부 부모 0 | 조인트(전부, IK 본 포함) + 전부 `mmdData` 에 | IK → `ikHandle`(링크 제한은 회전 리밋) · 부여 → 노드 망(아래) · 고정축/로컬축 → 조인트 방향 |
| **모프** | 그룹 · 버텍스 · 본 · UV · 추가 UV1~4 · 재질 · (2.1) 플립 · 임펄스, 패널(눈썹/눈/입/기타) | 52 = 전부 버텍스(눈썹 6 · 눈 15 · 입 31) | 버텍스 → blendShape, 나머지는 리포트에 종류 · 개수 | 그룹 → 구성 타깃에 가중치 연결 · 본 → 포즈 드라이버 · UV → UV 애니 · 재질 → 셰이더 어트리뷰트 |
| **표시 프레임** | MMD 화면의 본 · 모프 묶음(조작 패널 목록) | 14 = Root · 表情(모프 52) · センター · ＩＫ · 体(上) · 髪(68) · 腕 · 指 · 体(下) · 足 · Ear · リボン(69) · その他 · Q(120) | 리포트에 개수 | 셀렉션 셋 · Shape Editor 그룹 |
| **강체(물리)** | 붙은 본 · 충돌 그룹(0~15) · **비충돌 마스크** · 모양(구 · 상자 · 캡슐) · 크기 · 위치 · 회전 · 질량 · 이동/회전 감쇠 · 반발 · 마찰 · **모드**(본 추종 / 물리 / 물리+본 위치) | **318** = 상자 205 · 캡슐 109 · 구 4 · 모드: 본 추종 38 · 물리 201 · 물리+본 79 · 그룹 8 · 질량 0.0008 ~ 28. 머리카락(`Hair*` 24) · 장식(`MaJia*` 15) · 치마(`Q_*` 120) 등 | **개수만 리포트**(원본은 `mmdSourceFile` 로 다시 읽을 수 있다) | ① 마야 Bullet 플러그인(강체 + 제약) — 1:1 대응 ② 기존 툴 A00410 SecondaryMotion · A00390 ChainWave 로 근사 ③ UE Physics Asset 로 내보내기 |
| **조인트(물리)** | 두 강체를 잇는 스프링 6DOF: 위치 · 회전 · 이동/회전 한계 · 이동/회전 스프링 | **442** = 전부 스프링 6DOF · 스프링 값이 있는 것 18(가슴 `左胸上` 회전 스프링 100/80/100 등) | **개수만 리포트** | 위 ① 의 제약(6DOF spring) |
| **소프트바디** (2.1 만) | 천 · 소프트바디 물리 | 없음(2.0) | 개수만 | - |

같은 폴더의 다른 모델: 武器.pmx = 강체 12(캡슐, 본 추종 2 · 물리+본 10) · 조인트 10 · 표시 프레임 3, 幽灵.pmx = 물리 없음.

### 14-1. 부여(付与) 본 — 애니메이션에 쓰려면 제일 먼저 필요한 2차 작업

Miyabi 의 부여 30개(이 값으로 MMD 가 자동으로 돌리는 본, **웨이트가 실려 있다**):

| 종류 | 본 (부여 부모, 비율) | 의미 |
|------|------|------|
| 눈 | `左目` · `右目` ← `両目` 0.9 | 두 눈 함께 돌리기 |
| 허리 캔슬 | `腰キャンセル左/右` ← `腰` **-1.0** | 허리를 돌려도 다리는 그대로 |
| 어깨 캔슬 | `左肩C` · `右肩C` ← `肩P` -1.0 | 어깨 올림 보정 |
| 팔 비틀기 | `腕捩1/2/3` ← `腕捩` 0.25/0.5/0.75 · `手捩1/2/3` ← `手捩` 0.25/0.5/0.75 | 비틀림을 3 단계로 나눔 |
| 다리 D 본 | `足D` · `ひざD` · `足首D` ← `足` · `ひざ` · `足首` 1.0 | 변형용 다리(웨이트는 여기에) |
| 보조 | `ひざ補助` ← `ひざD` 0.5 · `足首補助` ← `足首D` 0.8 · `足補助` ← `足D` -0.5 | 무릎 · 발목 부피 보정 |

v01.00 은 바인드 포즈만 맞다 — `左足` 을 돌려도 웨이트가 실린 `左足D` 가 따라오지 않는다. 2차 방법: 부여 부모의 **로컬 회전 쿼터니언을 비율만큼 slerp**
(`quatSlerp` 로 항등과 섞기, 음수 비율은 `quatInvert` 후) → 자식 조인트 회전에 더함(`quatProd`). 마야 2023 에도 있는 `quatNodes` 만으로 된다.

> **v01.01 에서 구현 완료** — 실제 구현 · 순서 · 검증은 §15.

---

## 15. 2차 1단계 — v01.01 (2026-11-09)

### 15-1. 진단 → 결정

§14 의 "2차에서 할 수 있는 것" 중 물리(강체 · 조인트)를 뺀 13개를 진단했다(사용자 요청). 실측 근거:
**Miyabi 의 다리 웨이트는 전부 D 본**(`左足D` 279 · `左ひざD` 1,059 · `左足首D` 540 정점, `左足` · `左ひざ` · `左足首` 은 0) → v01.00 은 다리를 돌려도 메시가 안 움직인다.

| 판정 | 항목 |
|------|------|
| **1단계로 진행** | 부여 → 노드 망 · 표시 프레임 → 셋 / Shape Editor 그룹 · 엣지 배율 → 컬러 셋 · IK → ikHandle(근사) · 로컬축 → 조인트 방향 |
| 보류(사용자) | 외곽선 · 툰 · 스피어 |
| 보류(이 모델에 데이터 없음) | 그룹 · 본 · 재질 모프 |
| 안 함 | UV 모프(마야에 UV 디포머 없음) · SDEF 정확 디포머(C++ 플러그인 필요, DQ 근사 유지) · 양면 → 재질별 분리(22/23 이 이미 양면) |

사용자 결정(2026-11-09): **IK 근사 생성 · 기본 켬**, **로컬축 반영 · 기본 켬**, 외곽선 / 툰 / 스피어 보류.

### 15-2. 구현

| 기능 | 방법 |
|------|------|
| 로컬축 | 로컬축(0x800): X = localX, Y = localZ × X, Z = X × Y / 고정축(0x400)만: X = 축, Z = X × 월드 위 → 그 방향을 jointOrient 로(`translate` = 부모 방향으로 본 오프셋). Miyabi 42개(팔 · 손가락 38 + 비틀기 4). 월드 위치 · 스킨 불변(G1 ~ G9 그대로 통과) |
| 부여 | MMD 로컬 회전 `Rm = W⁻¹ · R · W`(W = 조인트 레스트 월드 방향) → `Append = slerp(I, Rm_부모, |r|)`(r < 0 이면 `quatInvert` 먼저) → **`rotateAxis = W · Append · W⁻¹`**(`quatToEuler`). 사슬은 부모의 총 회전(`Append · own`) |
| IK | 타깃 본에서 부모를 따라 올라가 링크와 같은 사슬일 때만. 링크 2+ = `ikRPsolver`, 1 = `ikSCsolver`, 핸들을 IK 본 아래에 숨김. 스킨 뒤에 만든다(레스트 불변을 G14 가 확인) |
| 표시 프레임 | 본 항목이 있는 프레임마다 `objectSet`(+ `mmdName`), 전부 `<모델>_frames` 아래. 모프는 **패널**(eyebrow · eye · mouth · other)별 `targetDirectory` + `parentDirectory`(마야 `blendShapeCreateTargetGroup.mel` 과 같은 구조) |
| 엣지 배율 | 1 이 아닌 정점이 있을 때만 컬러 셋 `mmdEdgeScale`(회색 = 배율, `displayColors` 끔) |

**부여 순서(중요)** — MMD 는 `q = own × slerp(I, parent, ratio)`(열벡터) = **부여가 먼저, 자기 회전이 나중**.
three.js `MMDAnimationHelper` GrantSolver 원문(`bone.quaternion.multiply(_q)`)으로 확인했다.
마야 조인트 행렬은 `[rotateAxis][rotate][jointOrient][T]` 라 rotateAxis 가 rotate 보다 먼저다 → 부여를 rotateAxis 에 넣으면 순서가 맞고 **`rotate` 는 비어 있어 애니메이션 키를 그대로 찍을 수 있다**.
처음 구현은 offsetParentMatrix(= 자기 회전 먼저)였는데 순서가 반대라 바꿨다.

### 15-3. 검증 — Blender + mmd_tools 를 정답 기준으로

- 이 PC 의 **Blender 2.93 에서 CATS zip 안의 mmd_tools 가 headless 로 Miyabi 를 임포트**한다(`tests/blender_mmd_reference.py`).
  같은 MMD 포즈(mmd_tools VMD 임포터의 `BoneConverter.convert_rotation` = VMD 키와 같은 뜻)를 양쪽에 주고 정점 27,086 개를 대조.
- 좌표: 마야 `(x, y, z)` cm ↔ 블렌더 `(x, -z, y)` m — 반사가 아니라 고유 회전이라 회전축을 그대로 옮긴다.

| 시나리오 | 최대 차이 | 판정 |
|----------|-----------|------|
| 레스트 · 엉덩이 40° · 무릎 -60° · 다리 체인(D + 보조) · 허리 캔슬 · 어깨 캔슬 | **≤ 6.7e-4 cm** | 일치 (블렌더 float 정밀도) |
| 비틀기 `左腕捩` 60° | 0.34 cm | **mmd_tools 쪽 근사** — 아래 |
| 눈 `両目` + `左目` | 0.05 cm | 〃 |
| IK `左足ＩＫ` (0, 15, 10) cm | 최대 2.0 cm · 평균 0.03 cm | 솔버가 다름(마야 RP ↔ 블렌더 IK, 둘 다 MMD CCD 아님) |

**실측으로 알게 된 것**
1. **mmd_tools 는 부여를 MMD 규칙대로 하지 않는다.** 부모를 축 a 로 60° 돌리면 MMD 규칙은 `左腕捩1` = 같은 축 15° 인데, mmd_tools 는 다른 축 15.79°(오일러 채널을 섞는 `TRANSFORM` 컨스트레인트 근사).
   → 축이 섞이는 경우는 블렌더가 기준이 못 된다. 시험 G13a 가 **MMD 규칙을 직접** 검사한다(같은 축 · 정확히 15° / 30° / 45°, 허리 캔슬 = 다리 회전 0).
2. 블렌더에서 IK 만 끄면 mmd_tools 가 IK 링크에 거는 **`LIMIT_ROTATION`(무릎 X -180 ~ -0.5°)이 남아 레스트에서도 다리 D 체인이 최대 71 cm 어긋난다** → IK 를 끌 땐 회전 제한도 같이 끈다.
3. 블렌더 `pose_bone.matrix` 대입은 컨스트레인트를 빼고 basis 를 역산한다 → 부여가 걸린 본에 월드 회전을 주면 **부여가 두 번** 들어간다. 부여 본은 basis(MMD 로컬 회전)로 포즈해야 한다.

시험: core 61/61 · mayapy **80/80**(G13a · G13b · G14 · G15 추가). GUI 확인(뷰포트에서 다리 · 팔 비틀기 · IK 조작, Shape Editor 그룹)은 아직.

### 15-4. 남은 2차

이동 부여 · 로컬 부여(Miyabi 없음) · IK 각도 제한(무릎) · 그룹 / 본 / 재질 모프 · 외곽선 / 툰 / 스피어(보류) · 물리.
