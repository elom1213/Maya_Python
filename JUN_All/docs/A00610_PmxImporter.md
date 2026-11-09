---
title: A00610_PmxImporter 사용법
aliases: [PMX Importer, PmxImporter, A00610, MMD import]
tags: [maya-python, tool-guide, pmx, mmd, importer, skin, blendshape, material]
updated: 2026-11-09
---

# A00610_PmxImporter 사용법

MMD 모델(**PMX 2.0 / 2.1**)을 블렌더 · CATS · FBX 를 거치지 않고 **마야에 바로** 임포트하는 in-Maya PySide 툴(arch B).
결과 = **스킨된 메시 하나 + 조인트 + 블렌드셰이프(모프) + lambert 머티리얼 · 텍스처**. **Ctrl+Z 한 번**에 임포트 전체가 되돌아간다.

- **버전**: `app/config/version.py` (v01.01 — 부여 본 · IK · 로컬축 · 표시 프레임)
- **설치**: `__dragDrop_A00610.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **PMX** → `tools.A00610_PmxImporter.run(True)`
  (ToolLauncher `UTIL` 프로파일 `File` 칸에도 있다)
- **계획서**: [`plans/A00610_PmxImporter_plan.md`](plans/A00610_PmxImporter_plan.md) — 실측 근거 · PMX 규격 · PMX 안의 다른 데이터(§14)

## 1. 쓰는 순서

1. `File` 에 `.pmx` 를 넣거나 `Browse...` → 자동으로 `Read`.
2. `Info` 에서 확인: 모델 이름 · 정점/면/재질/본/모프 수 · 웨이트 종류 · 물리(강체 · 조인트) 수,
   텍스처 표 — `Found`(초록) · `Copy needed (cp949)`(노랑, 임포트 때 복사) · `Found elsewhere`(노랑) · `Missing`(빨강).
3. 옵션을 고르고 `Import` → 진행 팝업 → 로그에 요약. 끝나면 결과 그룹이 선택된다.

## 2. 옵션

| UI | 기본 | 하는 일 |
|----|------|---------|
| `Mesh` | 켬 | 메시 하나(정점 순서 = PMX). 끄면 메시 · 재질 · 모프 · 스킨 모두 없음 |
| `Materials` | 켬 | PMX 재질마다 lambert + SG, 면 범위 할당. 끄면 `initialShadingGroup` |
| `Skeleton` | 켬 | PMX 본마다 조인트(**IK 본 포함**), 월드 정렬(jointOrient 0) |
| `Skin` | 켬 | skinCluster + PMX 웨이트(웨이트가 있는 본만 인플루언스) |
| `Morphs` | 켬 | 버텍스 모프 → blendShape 타깃 |
| `Local axes` | 켬 | 로컬축(팔 · 손가락) · 고정축(비틀기 본)이 있는 본을 그 축으로 jointOrient(Miyabi 42개). 끄면 전부 월드 정렬 |
| `Append bones` | 켬 | 부여(付与) 본이 부여 부모를 따라간다(아래 5-1) |
| `IK` | 켬 | IK 본마다 ikHandle — **근사**(아래 5-2) |
| `Display frames` | 켬 | 본 표시 프레임 → 조인트 셋, 모프 패널 → Shape Editor 그룹 |
| `Import normals` | 켬 | PMX 노멀을 잠가 넣는다 |
| `Hide invisible bones` | 켬 | MMD 에서 숨김인 본은 `drawStyle = None` |
| `SDEF/QDEF as dual quaternion` | 켬 | SDEF · QDEF 정점만 듀얼 쿼터니언(weight blended). 끄면 선형 |
| `Copy unreadable textures` | 켬 | 아래 3장 |
| `Scale` | 8.0 | MMD 1 단위 = 8 cm (CATS 의 0.08 m 와 같은 크기) |
| `UV set` | `map1` | 기본 UV 셋 이름(`UVMap` 도 고를 수 있다). 추가 UV 는 `UV1` ~ `UV4` |
| `Namespace` | 비움 | 넣으면 그 네임스페이스로 임포트 |

옵션 · 마지막 파일은 기억한다(optionVar).

## 3. 이름 — PMX 고유 이름 + FBXASC

노드 이름은 **PMX 의 일본어 이름**이다. 마야 이름에 못 쓰는 글자는 FBX 와 같은 **`FBXASC###`**(UTF-8 바이트 10진수)로 바뀐다.

| PMX | 마야 |
|-----|------|
| `左足` | `FBXASC229FBXASC183FBXASC166FBXASC232FBXASC182FBXASC179` |
| `1` (숫자로 시작) | `FBXASC049` |
| `New MMD Model` | `NewFBXASC032MMDFBXASC032Model` |
| `HairF1_01` | `HairF1_01` (그대로) |

- 원래 글자로 읽으려면 `A00620_NameDecoder`, 또는 `pmx_convert.decode_name(name)`.
- 겹치면 `_1`, `_2`. 같은 모델을 두 번 넣어도 이름이 겹치지 않는다.
- 원본 정보는 어트리뷰트에(전부 **ASCII** — `.ma` 로 저장해도 안 깨진다):
  조인트 · 머티리얼 `mmdName`(FBXASC) · `mmdIndex` · `mmdData`(JSON: 본 = 플래그 · 부여 · 축 · IK, 재질 = 색 · 엣지 · 스피어 · 툰),
  blendShape `mmdMorphs`, 결과 그룹 `mmdModelName` · `mmdComment` · `mmdSourceFile` · `mmdImportReport`(JSON).

## 4. 텍스처 — 코드페이지 복사

마야(2024)는 **시스템 코드페이지(한국어 Windows = cp949)에 없는 글자**가 든 경로의 이미지를 읽지 못한다(`颜.png` → `?.png`).
그런 텍스처만 `<PMX 폴더>/maya_textures/` 에 FBXASC 이름으로 **복사**해 연결한다(원본은 그대로, 같은 파일이면 다시 복사하지 않음).

```
tex\颜.png  ->  maya_textures/texFBXASC047FBXASC233FBXASC162FBXASC156.png
tex\髮.png  ->  (cp949 에 있는 글자라 원본 그대로)
```

- 알파가 있는 텍스처(PNG RGBA 등)는 `outTransparency → transparency` 로 연결 — 눈 · 속눈썹 · 머리카락 끝이 투명.
- 재질 확산 알파가 1 보다 작으면 함께 곱한다. **알파 0 재질**(예: 武器 `刃2`)은 완전 투명 + 로그 경고(MMD 에서도 평소 숨김).
- 툰 · 스피어 텍스처는 연결하지 않고 `mmdData` 에 경로만 남긴다.

## 5. 결과 씬

```
<모델>_grp
├── <모델>_geo_grp
│   └── <모델>_mesh        blendShape <모델>_morphs -> skinCluster <모델>_skinCluster
└── <모델>_skel_grp
    └── PMX 본 계층 그대로(全ての親 · 操作中心 · IK 친 본 …)
```

`<모델>` = PMX 안의 모델 이름(Miyabi.pmx → `Unagi`). 그 밖에 `<모델>_frames`(표시 프레임 셋), IK 본 아래 숨긴 `*_ikHandle`,
부여 노드 `mmd_<본>_*`(eulerToQuat · quatProd · quatSlerp · quatToEuler).

### 5-1. 부여(付与) 본

MMD 가 자동으로 돌리는 본. Miyabi 는 30개이고 **다리 웨이트가 전부 여기**(`足D` · `ひざD` · `足首D`)에 있다 — 이게 없으면 다리를 돌려도 메시가 안 움직인다.

| 종류 | 예 | 동작 |
|------|----|------|
| 다리 D 본 | `左足D` ← `左足` ×1 | 다리를 그대로 따라감 |
| 보조 | `左ひざ補助` ← `左ひざD` ×0.5 | 사슬 - 부모의 부여까지 포함 |
| 비틀기 | `左腕捩1/2/3` ← `左腕捩` ×0.25/0.5/0.75 | 같은 축으로 비율만큼 |
| 캔슬 | `腰キャンセル左` ← `腰` ×-1 | 허리를 돌려도 다리는 그대로 |
| 눈 | `左目` ← `両目` ×0.9 | 두 눈 함께 + 각자 회전 |

- 부여 회전은 조인트의 **`rotateAxis`** 에 들어간다 → **`rotate` 는 비어 있어 키를 그대로 찍을 수 있다**(부여 먼저, 자기 회전 나중 — MMD 와 같은 순서).
- IK 가 돌린 본(`足`)의 결과도 따라간다. 이동 부여 · 로컬 부여 플래그는 아직(경고 로그).

### 5-2. IK (근사)

- IK 본(`左足ＩＫ` · `左つま先ＩＫ` …)을 움직이면 다리가 따라온다. 링크 2개 이상 = RP 솔버, 1개 = SC 솔버. 핸들은 IK 본 아래에 숨겨져 있다.
- MMD 의 IK 는 반복형(CCD) + 무릎 각도 제한이라 **완전히 같지는 않다** — Blender mmd_tools 대비 평균 0.03 cm, 최대 2 cm(발을 15 cm 들고 10 cm 앞으로).
- IK 를 켠 상태에서는 `足` · `ひざ` 를 손으로 돌려도 IK 가 덮어쓴다(마야 IK 와 같음). FK 로 쓰려면 핸들의 `ikBlend` 를 0 으로.

## 6. 한계 (v01.01)

- **물리(강체 · 조인트)**, **버텍스 외 모프**(그룹 · 본 · UV · 재질)는 만들지 않고 리포트에 개수만.
- IK 는 근사(위 5-2), 이동 부여 · 로컬 부여는 아직.
- 툰 · 스피어 · 외곽선 셰이딩 없음(보류 - lambert 색 + 알파만).
- redo(Ctrl+Y)는 보장하지 않는다.

## 7. 검증

- `tests/test_pmx_core.py` — 파서 · 변환 · 이름 · 텍스처(마야 없이) 61/61.
- `tests/test_import_maya.py` — mayapy: 합성 PMX + 실제 모델을 CATS → FBX 로 만든 기준 mb 와 숫자 대조 80/80
  (위치 2.8e-5 cm · UV 0 · 면 33,528 전부 같음 · 모프 51개 1.1e-4 · 웨이트 = PMX · 팔꿈치 포즈 변형 7.6e-6 · 저장 왕복).
  v01.01: **Blender + mmd_tools 로 같은 MMD 포즈를 준 메시와 대조**(`tests/blender_mmd_reference.py`, 블렌더 · CATS zip 이 있을 때만) —
  다리 D 체인 · 허리 / 어깨 캔슬 1e-3 cm 이하, IK 평균 0.03 cm. 비틀기 · 눈은 mmd_tools 가 오일러로 근사해 0.3 cm 차이가 나므로
  MMD 규칙(같은 축 × 비율)을 직접 검사한다.
  모델 파일은 저장소에 없다(재배포 금지) — `A00610_SAMPLE_DIR` 이 있을 때만 실제 모델 시험을 한다.
- GUI 실기 확인(뷰포트 텍스처 · 투명 · Shape Editor · FBX → UE)은 아직.
