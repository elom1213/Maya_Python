---
title: A00480_FileTool — Mocap FBX 정확 임포트 (Exact Rotation) 계획서
aliases: [FBX Exact Import, fbx_exact, Mocap FBX Import, rotate order flip]
tags: [plan, maya-python, fbx, import, mocap, animation, A00480]
updated: 2026-10-27
---

# A00480_FileTool — Mocap FBX 정확 임포트 (Exact Rotation) 계획서

> 작성 2026-10-27 · 상태: **설계 완료 · 구현 전** · 아키텍처 (B) Maya 내 PySide 툴(기존 툴에 기능 추가)
>
> 이 문서의 수치는 전부 이 PC 의 `Maya2024/bin/mayapy.exe` 헤드리스 실측이다(FBX 플러그인 2020.3.4).
> 시제품 스크립트는 저장소에 넣지 않았다. 핵심 알고리즘은 §8 에 코드로 옮겨 두었다.

---

## 0. 요약 (1분 버전)

- **현상**: `BCM_01_004.fbx`(Vicon 계열 모캡, 5인 스켈레톤)를 마야로 바로 임포트하면 **일부 조인트가 엉뚱한 방향을 본다.**
  블렌더로 임포트 → FBX 로 다시 뽑기 → 마야 임포트를 거치면 멀쩡하다.
- **누가 맞나**: FBX 를 직접 파싱해 변환 수식으로 계산한 **정답**과 비교했다. **블렌더가 맞고 마야 직접 임포트가 틀렸다.**
  CHOEUN 의 머리는 1001프레임에서 37cm, 전체 조인트 기준으로는 최대 200cm 어긋난다.
- **원인 (실측)**: 마야 FBX 임포터가 회전 키를 "이전 키에 가까운 동치 오일러"로 바꿀 때 **회전 순서와 상관없이 XYZ 용 동치 공식
  `(x+180, 180−y, z+180)`** 을 쓴다. 이 파일의 조인트는 대부분 회전 순서가 XZY 같은 **비 XYZ** 라서 그 공식으로 바꾸면
  **다른 방향**이 된다. 뒤집힌 키 전부가 이 공식과 정확히 맞았다. 값이 ±180° 근처를 오가는 `Hips` 와 `RightArm` 에서 터진다.
- **마야 기본 기능으로는 안 된다.** 임포트 옵션 `Quaternion Interpolation` 세 가지 모드가 전부 틀린다. 이 필터를 끄는 옵션은
  FBX 임포트 속성 목록에 없다. Euler Filter 같은 후처리로도 못 고친다. 틀린 값이 **연속**이라 필터가 이상을 알아차릴 수 없다.
- **블렌더 경유도 손실이 있다.** 키를 6285 → 약 4600개로 줄이고, 월드 위치가 최대 **1.27cm** 어긋나며, 타임라인을 1프레임 당긴다.
- **해법 (시제품 검증 완료)**: 마야로 임포트한 뒤 **FBX 파일의 원본 회전 키를 직접 읽어 회전 커브를 다시 쓴다.**
  5명 · 365조인트 · 6285프레임 전체에서 **불일치 0**, 월드 오차 **0.00000cm**(47,450 샘플)가 나왔다. 걸린 시간은 약 7초다.
  원본 데이터 자체에 있는 ±360° 래핑(1603곳)은 **회전 순서를 고려한 언랩**으로 없앴고, 행렬은 그대로 유지된다(차 2e-15).
- **어디에**: 기존 **`A00480_FileTool` 의 Import > FBX 하위 탭**에 섹션을 하나 더한다(v01.13).
  로직은 **`Framework/core`** 에 둔다. 나중에 `A00210_FileManager` 의 mayapy 일괄 처리에서도 같은 코드를 쓸 수 있다(Phase 2).
  새 툴은 만들지 않는다(§5).
- 사용자가 바라는 **"0020 처럼"** 은 옵션 `Normalize joints`(jointOrient 0 · rotateOrder xyz)로 맞춘다.
  위치와 방향은 정답과 같고, 조인트 표현은 블렌더 경유 결과와 같아진다(§6-3, Q1).

---

## 1. 요청과 재료

> BCM_01_004.fbx 가 블렌더와 마야에서 각각 다르게 임포트된다. 이 현상 때문에 마야에서 온전한 FBX 애니 데이터를 불러올 수 없다.
> 지금까지는 블렌더로 임포트 → FBX 추출 → 마야 임포트를 거쳐 왔다. 마야에서 바로 0020 처럼 불러오고 싶다.

| 파일 (`C:\Users\USER\Desktop\JP\0001_tmp_01\fbx_test`) | 내용 |
|------|------|
| `0010_origin/BCM_01_004.fbx` | 원본. 108,680,960 B |
| `0010_motion_0010.mb` | 원본을 **마야로 바로 임포트**한 결과 (틀린 쪽) |
| `0010_motion_0010.blend` | 원본을 **블렌더 4.3.2**로 임포트한 결과 |
| `0020_CHOEUN_0010.fbx` | 위 블렌더 씬에서 아바타 `CHOEUN` 하나를 FBX 로 뽑은 것 (Blender FBX IO 5.12.5) |
| `0020_CHOEUN_0010.mb` | 그 FBX 를 마야로 임포트한 결과 (사용자가 원하는 모양) |

---

## 2. 원인 분석 (실측)

### 2-1. 원본 FBX 구조

순수 파이썬 바이너리 FBX 파서(§8-1)로 덤프했다. 108MB 를 0.24초에 읽는다.

| 항목 | 값 |
|------|----|
| 포맷 | Binary FBX **7700**(64비트 오프셋), `FBX SDK/FBX Plugins version 2020.0.1` |
| 축 · 단위 | **Z-up**(UpAxis=2, FrontAxis=−Y), cm(UnitScaleFactor 1.0) |
| 시간 | **60fps**(TimeMode 3), 스택 `BCM_01_004_mcp`, **1 ~ 6285 프레임** |
| 노드 | 스켈레톤 루트 Null 5개(`CHOEUN` `SUA` `ZHAN` `IVI` `KANA`)와 각 **LimbNode 73개**(총 365개), Marker 390, Camera 67, `System` Null 1 |
| 이름 | `CHOEUN:Hips` 처럼 캐릭터 접두사가 붙는다(마야 임포터는 접두사를 떼고 `\|CHOEUN\|Hips` 로 만든다) |
| 애니 | AnimationCurve 2085개 · 키 13,104,225개. **전부 정수 프레임**, 전부 **Linear**(KeyAttrFlags 0x2104) |
| LimbNode 속성 | `PreRotation` 100개(캐릭터당 20개) · **`RotationOrder` 비 XYZ 190개**(XZY 130 · ZXY 40 · YZX 10 · ZYX 10) · 모든 모델 `QuaternionInterpolate = 1` · PostRotation · 피벗 · 오프셋 없음 |
| 뼈 방향 | 자식이 로컬 **+Z** 로 놓인다(`Lcl Translation = (0, 0, 9.93)` 등) |

마야 임포터는 `PreRotation → jointOrient`, `RotationOrder → rotateOrder` 로 **바르게** 옮긴다.
어긋나지 않은 조인트는 로컬 행렬 차가 0 이었다. 문제는 **회전 커브의 값**에만 있다.

### 2-2. 정답과 비교

"정답"은 FBX 변환 수식 `Local = T · Rpre · R(order) · Rpost⁻¹ · S` 를 파일 값으로 직접 계산한 것이다(§8-6).
마야 씬의 루트에는 Z-up → Y-up 을 위한 −90°X 가 걸려 있어서 `(x, y, z)_fbx → (x, z, −y)_maya` 로 맞춰 비교했다.

| CHOEUN `Head` 월드 위치 (cm) | 프레임 101 | 프레임 1001 |
|------|------|------|
| 정답 (FBX 직접 계산) | (−54.74, 141.95, −169.50) | (−43.37, 138.02, −129.44) |
| 블렌더 경유 (`0020_CHOEUN_0010.mb`) | (−54.77, 141.95, −169.47) | (−43.37, 138.02, −129.25) |
| **마야 직접** (`0010_motion_0010.mb`) | **(−61.79, 142.02, −169.50)** | **(−80.41, 138.43, −132.21)** |

### 2-3. 어디서 틀리나 — 조인트 · 프레임 단위 전수 조사

조인트마다, 6285프레임 전부에서 **FBX 회전 행렬 `Rpre · R(order)`** 과 **마야 `jointOrient · R(rotateOrder)`** 를 비교했다(허용 1e-3).

`0010_motion_0010.mb` 의 CHOEUN (73조인트):

| 조인트 | 회전 순서 | 틀린 프레임 | 예 |
|------|------|------|------|
| `Hips` | XZY | **1 ~ 5493** (5493) | f1 · 파일 `(−173.366, −179.834, 3.349)` → 마야 `(6.634, −0.166, −176.651)` |
| `RightArm` | XZY | **3707 ~ 6285** (2579) | f3707 · 파일 `(3.472, 34.422, 88.554)` → 마야 `(543.472, −574.422, −91.446)` |
| 나머지 71개 | — | 0 | |

**규칙**: 뒤집힌 키가 하나도 빠짐없이 `x' = x+180(+360k)`, `y' = 180−y(+360k)`, `z' = z+180(+360k)` 을 따른다.
이 공식은 **XYZ 순서에서만** 같은 방향을 준다. XZY 처럼 가운데 축이 Z 인 순서의 동치는 `(x+180, y+180, 180−z)` 다.
즉 임포터가 키 사이 연속성을 맞추려고 동치 오일러로 바꾸면서 **rotateOrder 를 무시하고 XYZ 공식을 쓴다.**
값이 ±180° 근처를 넘나드는 조인트에서만 이 변환이 발동한다. Vicon 의 Hips 는 Z-up 에서 rx ≈ ±180 으로 시작한다.

> 이 판단은 관측된 사실(전 키 일치)에서 끌어낸 추정이다. 마야 소스로 확인한 것은 아니다.
> 다만 이 추정은 해법에 영향을 주지 않는다. 해법은 원인과 상관없이 파일 값으로 덮는다.

### 2-4. 마야 임포트 옵션 세 가지 전부 재현 (`FBXImportQuaternion`)

빈 씬에 `FBXResetImport` 를 한 뒤 모드만 바꿔 임포트하고, 같은 전수 조사를 했다(CHOEUN).

| 모드 (UI 이름) | 결과 |
|------|------|
| `euler` (Set As Euler Interpolation) | Hips 1~5493 · RightArm 3707~6285 = **8072 조인트·프레임**. **사용자 씬과 숫자까지 똑같다** → 사용자는 이 모드로 임포트했다 |
| `resample` (Resample As Euler, **기본값**) | Hips 6088프레임이 뒤집힌다. 여기에 **나머지 거의 모든 조인트**가 재샘플 때문에 0.1° 안팎 틀린다(조인트당 3000~5000프레임) |
| `quaternion` (Retain Quaternion) | Hips 5672 · RightArm 414 · LeftArm 137프레임, 여기에 손 · 손가락 7개 조인트(LeftHand 와 좌우 Middle1 · Ring1 · Pinky1)가 군데군데(가운데 축 ±90° 근처) 뒤집힌다. 합계 6799 |

5명 전체로 보면 euler 모드 기준 월드 오차가 최대 **200.0cm** 다(`|CHOEUN|…|RightHandPinky4`, 프레임 1901, 47,450 샘플 중 37,631 샘플이 0.01cm 를 넘는다).

### 2-5. 블렌더 경유는 왜 맞고, 무엇을 잃나

블렌더 임포터는 PreRotation 과 회전 순서를 **행렬로 합쳐서** 본마다 XYZ 오일러로 다시 굽는다.
그래서 마야 임포터의 동치 변환 버그를 타지 않는다. 대신 다음이 바뀐다.

| 항목 | 블렌더 경유 결과 (`0020_CHOEUN_0010.mb`) | 원본 / 정답 |
|------|------|------|
| jointOrient · rotateOrder | **전부 0 · xyz** (PreRotation 은 회전 값에 녹았다) | jointOrient = PreRotation, rotateOrder 는 조인트마다 다르다 |
| 조인트 수 | 86 = 73 + **`_end` 리프 본 13개** (블렌더 `Add Leaf Bones`) | 73 |
| 키 | **줄어 있다**(Hips tx 4596/6285 · ty 4712 · tz 4368, FBX 익스포터의 Simplify). 모든 본에 T·R·S 키 | 매 프레임 |
| 정확도 | Hips 이동 최대 **0.56cm**, 월드 위치 최대 **1.27cm**(손끝, 프레임 2301), 18,396 샘플 중 8,314 샘플이 0.05cm 초과 | — |
| 타임라인 | **0 ~ 6284** (1프레임 당김) | 1 ~ 6285 |
| 루트 | `CHOEUN` 그룹 −90°X (마야 직접 임포트와 같다) | — |
| 들어온 것 | CHOEUN 스켈레톤 하나 | 5명 + 마커 + 카메라 |

→ 지금 쓰는 우회는 **방향은 맞지만 정확하지 않다.** 계획한 기능은 정답과 같은 결과를 낸다.

### 2-6. 원본 데이터 자체의 ±360° 래핑

원본 회전 커브에도 **연속 키 사이에서 180° 이상 튀는 곳이 1603곳** 있다(Hips ×5명, RightArm ×3명 등 10개 조인트).
정수 프레임의 자세는 맞지만, Linear 보간이라 **프레임 사이에서 한 바퀴 돈다.**
모션 블러 · 리타임 · 서브프레임 베이크 · 그래프 에디터 판독이 망가진다.
마야 임포터가 하려던 "연속화"는 **필요한 일**이다. 다만 회전 순서를 고려해서 해야 한다(§8-4).

---

## 3. 마야에 있는 방식으로 해결되나? → 안 된다

| 시도 | 결과 |
|------|------|
| 임포트 옵션 `Quaternion Interpolation` 3종 | 전부 틀린다 (§2-4) |
| 이 변환을 끄는 옵션 | 없다. `FBXProperties` 의 Import 항목을 모두 확인했다. `Animation\|CurveFilter` 는 이미 false 고, Euler 필터 · 언롤 토글은 없다 |
| 임포트 후 Euler Filter (Graph Editor · `filterCurve`) | 못 고친다. 틀린 구간이 **연속 곡선**이라 필터가 불연속을 찾지 못한다. 문제는 튐이 아니라 **방향이 다른 것**이다 |
| HumanIK 리타깃 | 소스 조인트가 이미 틀린 자세라 그대로 옮겨 간다 |
| 다른 마야 버전의 FBX 플러그인 | **확인 안 했다.** 이 PC 에는 Maya 2024(플러그인 2020.3.4)만 있다. 새 플러그인이 고쳤을 수도 있지만 그 경우에도 아래 기능이 해가 되지는 않는다 |

**결론: 기능을 만든다.**

---

## 4. 해법 — "임포트 + 원본 회전 키로 덮기"

1. 마야 FBX 임포터로 **평소처럼 임포트**한다. 계층 · jointOrient · rotateOrder · 이동 커브 · 마커 · 카메라는 맞게 들어온다.
2. **같은 FBX 를 순수 파이썬으로 파싱**해 LimbNode 마다 `Lcl Rotation` 의 X/Y/Z 커브(키 시간 · 값 · 보간)를 읽는다.
3. FBX 노드의 계층 경로(`CHOEUN:Hips` → `|CHOEUN|Hips`)로 마야 조인트를 찾는다.
4. 그 조인트의 `rotateX/Y/Z` 커브를 지우고 **파일 값 그대로** 다시 만든다(`MFnAnimCurve.addKeys`, 한 번에).
5. **회전 순서를 고려한 언랩**으로 ±360° 래핑을 없앤다. 각 키에서 같은 방향인 두 해와 2π 배수 중 이전 키에 가장 가까운 것을 고른다.
6. (옵션) `Normalize joints` — 로컬 회전 `jo · R(ro)` 를 XYZ 오일러로 다시 굽고 jointOrient 0 · rotateOrder xyz 로 바꾼다. 결과가 블렌더 경유와 같은 표현이 된다.
7. **검증** — 샘플 프레임에서 마야 로컬 행렬과 FBX 수식 행렬을 비교해 최대 오차를 로그로 남긴다.

### 시제품 실측

| 항목 | 결과 |
|------|------|
| 4단계 후 회전 불일치 (CHOEUN · KANA, 모드 euler · resample 각각) | **0 조인트·프레임** (6285프레임 전수) |
| 월드 위치 오차 (5명 365조인트 × 130프레임 = 47,450 샘플) | 최대 **0.00000cm** (덮기 전 200.0cm) |
| 덮기 시간 | **6.2 ~ 8.5초** (커브 900개 · 키 5,656,500개, `MFnAnimCurve.addKeys`) |
| 마야 임포트 시간 | 8.5 ~ 9.2초 |
| 5단계 언랩 (300개 회전 트리플) | 튐 1603 → **0**, 행렬 최대 차 **2.3e-15**. numpy 를 키마다 호출한 시제품이라 17.9초 걸렸다 → §8-4 의 순수 파이썬 루프로 줄인다 |

---

## 5. 어디에 넣나

| 후보 | 판단 |
|------|------|
| **`A00480_FileTool` Import > FBX 하위 탭** | ✅ **채택.** 마야 안의 파일 입출력 툴이고, 이미 `Import > FBX`(`Import FBX normal`)가 있다. FBX 헬퍼도 `Framework.core.maya_fbx` 로 이어져 있다. 요청이 "임포트할 때 해결" 이므로 위치가 정확히 맞는다 |
| 새 툴 | ❌ 기능 하나(섹션 하나)다. 파일 선택 · 로그 · 테마 같은 입출력 UI 를 중복으로 만들게 된다 |
| `A00110_animTool_V02` (Curve 탭) | ❌ 이미 있는 커브를 다듬는 툴이다. 이 수정은 **원본 FBX 가 있어야** 가능하다(무엇이 정답인지 커브만 보고는 모른다) |
| `A00210_FileManager` Maya 탭 | ⏸ Phase 2 후보. 마야 밖에서 FBX 폴더를 mayapy 로 **일괄** `.mb` 로 바꿀 때 쓸 수 있다. 같은 코드를 쓰도록 로직을 Framework 에 둔다 |

**로직은 `Framework/core` 에 둔다.** 릴리즈본은 툴 간 import 를 금지한다([Release_Layout](../Release_Layout.md)).
A00480(마야 안)과 A00210(mayapy 워커)가 함께 쓰려면 Framework 에 있어야 한다.
`maya_fbx` 를 A00480 에서 Framework 로 올린 2026-10-26 결정과 같은 이유다.

---

## 6. 기능 명세

### 6-1. 화면 (Import > FBX 하위 탭, 기존 `FBX Import Option` 섹션 아래)

```
┌ FBX Import Option ───────────────────────────────────────────────┐
│ [ Import FBX normal ]                                             │
└───────────────────────────────────────────────────────────────────┘
┌ Mocap FBX Import (Exact Rotation) ───────────────────────────────┐
│ FBX File   [C:/.../BCM_01_004.fbx                     ] [Browse]  │
│ Info       FBX 7700 · Z-up · cm · 60 fps · 1-6285 · 5 skeletons    │
│ Skeletons  [✓] CHOEUN (73)  [✓] SUA (73)  [✓] ZHAN (73)            │
│            [✓] IVI (73)     [✓] KANA (73)        [All] [None]      │
│ Options    [✓] Skeletons only (skip markers / cameras)             │
│            [✓] Unwrap rotations (rotate order aware)               │
│            [✓] Normalize joints (jointOrient 0, rotateOrder xyz)   │
│            [✓] Verify against file                                 │
│ [ Import FBX (Exact) ]                  [ Fix Scene From FBX ]     │
└───────────────────────────────────────────────────────────────────┘
```

- `Browse` 로 파일을 고르면 **곧바로 스캔**한다(파서만 쓰므로 0.3초 안팎, 마야 씬은 건드리지 않는다). `Info` 줄과 `Skeletons` 체크 목록이 채워진다.
  스켈레톤은 "자손에 LimbNode 가 있는 최상위 Model" 이다. 괄호 안 숫자는 LimbNode 개수다.
- `Skeletons` 는 FlowLayout(줄바꿈)으로 놓는다. 스켈레톤이 1개뿐이면 체크 목록 대신 이름만 보여 준다.
- 모든 UI 문자열 · 로그는 영어다(전역 규칙 6장).

### 6-2. `Import FBX (Exact)` 흐름

| # | 단계 | 내용 |
|---|------|------|
| 1 | 사전 검사 | 파일 있음 · 파싱 가능. 체크한 스켈레톤 루트 이름이 **이미 씬에 있으면 `[FAIL]` 로 멈춘다**(임포터가 기존 노드에 키를 합쳐 매핑이 꼬인다) |
| 2 | 씬 fps | 씬 시간 단위가 파일 fps 와 다르면 파일 fps 로 바꾸고 로그를 남긴다(§9 T3 에서 임포터 동작을 실측한 뒤 확정) |
| 3 | 임포트 | `with maya_fbx.import_options(quaternion="euler", ...)` 안에서 `FBXImport -f`. euler 모드는 재샘플을 하지 않아 **이동 커브도 파일 키 그대로**다. 나갈 때 옵션을 되돌린다 |
| 4 | 새 노드 수집 | 임포트 전후의 assemblies · namespaces 차이로 **이번에 생긴 것만** 다룬다 |
| 5 | 정리 | 체크 안 한 스켈레톤을 지운다. `Skeletons only` 면 Marker · Camera · `System` 같은 비 스켈레톤 루트도 지운다. **이번에 생긴 빈 네임스페이스**(이 파일은 827개 — `CHOEUN1~152` 같은 쓰레기)를 지운다 |
| 6 | 진단 | 덮기 전에 임포터 커브와 파일 값을 비교해 **임포터가 뒤집은 조인트 · 구간**을 센다(로그에 남긴다. 같은 파일이 왜 틀렸는지 사용자가 볼 수 있다) |
| 7 | 덮기 | LimbNode 회전 커브를 파일 값으로 다시 만든다(§8-3) |
| 8 | 언랩 | `Unwrap rotations` 면 §8-4 |
| 9 | 정규화 | `Normalize joints` 면 §8-5 |
| 10 | 검증 | `Verify against file` 면 §8-6, 최대 오차(°, cm)를 로그에 남긴다 |
| 11 | 타임라인 | playback · animation 범위 = 파일 스택 범위(1 ~ 6285) |

로그 예:

```
[Info] FBX 7700 · Z-up · cm · 60 fps · frames 1-6285 · 5 skeletons · 365 joints · 390 markers · 67 cameras
[Info] Imported in 9.1s. Removed: 390 markers, 67 cameras, 1 other root, 827 empty namespaces.
[WARN] Maya importer flipped 2 joints on CHOEUN: Hips (frames 1-5493), RightArm (frames 3707-6285).
[OK] Rotation curves rebuilt from file: 900 curves / 5,656,500 keys (7.4s).
[OK] Unwrapped 1603 jumps over 180 deg (10 joints).
[OK] Normalized 365 joints to jointOrient 0 / rotateOrder xyz.
[OK] Verify: max 0.0000 deg rotation / 0.0000 cm position over 365 joints x 630 frames.
```

### 6-3. `Normalize joints` (사용자의 "0020 처럼")

| | Normalize OFF | Normalize ON |
|------|------|------|
| jointOrient | 파일 PreRotation | **0** |
| rotateOrder | 파일 RotationOrder (조인트마다) | **xyz** |
| 회전 커브 | 파일 값(+언랩) | `jo · R(ro)` 를 XYZ 로 분해(+연속 해) |
| 부분 채널(예: 손가락 Y 만) | 파일에 있는 축만 | **세 축 모두** 키 |
| 월드 자세 | 정답 | 정답 (같다) |

`0020_CHOEUN_0010.mb` 와 같지 **않게 남기는** 것: `_end` 리프 본(블렌더가 만든 것이라 만들지 않는다),
키 감소(하지 않는다), 1프레임 당김(하지 않는다), 모든 본의 T·S 키(파일에 있는 것만). → Q1 · Q3

### 6-4. `Fix Scene From FBX` (이미 임포트해 둔 씬 고치기)

`0010_motion_0010.mb` 처럼 **이미 마야로 바로 임포트해서 작업 중인 씬**을 FBX 원본으로 고친다.

- 대상: 씬에서 선택한 루트. 선택이 없으면 FBX 스켈레톤 이름과 같은 최상위 노드를 쓴다.
- 3 · 5단계(임포트 · 정리)를 건너뛰고 6 ~ 10단계만 한다. Normalize 는 이 모드에서도 옵션이다.
- 조인트의 rotateOrder · jointOrient 가 파일과 다르면(이미 정규화했거나 다른 경로로 온 씬) 그 조인트는 `[SKIP]` 하고 이유를 남긴다.
- 커브 키 시간이 파일과 다르면(리타임 · 오프셋한 씬) `[WARN]` 을 남기고 고치지 않는다.

---

## 7. 모듈 설계

```
JUN_All/
├── Framework/core/
│   ├── fbx_binary.py          # 신규 · 순수 파이썬(마야 · numpy 없이) 바이너리 FBX 리더
│   ├── euler_math.py          # 신규 · 순수 파이썬 오일러 동치 · 언랩 · 행렬(검증용)
│   ├── maya_fbx.py            # 기존 + import_options() 컨텍스트 매니저 (fbx_options 와 같은 모양)
│   └── maya_fbx_exact.py      # 신규 · 마야: scan / import_exact / fix_scene_from_fbx
├── tools/A00480_FileTool/
│   ├── app/core/import_ops.py         # + scan_fbx_exact / import_fbx_exact / fix_scene_from_fbx (얇은 래퍼, 로그 리스트 반환)
│   ├── app/ui/import_fbx_exact.py     # 신규 · 섹션 위젯 (QGroupBox)
│   ├── app/ui/import_tab.py           # FbxImportPage 에 섹션 추가
│   ├── app/config/version.py          # 01.13
│   ├── CHANGELOG.md
│   └── tests/test_fbx_exact.py        # mayapy
└── docs/
    ├── A00480_FileTool.md             # §3-2 에 사용법
    ├── Framework_fbx_binary.md        # 신규 (리더 · 언랩 API)
    └── Framework_maya_fbx.md          # import_options · maya_fbx_exact 줄 추가
```

### 7-1. `Framework/core/fbx_binary.py` (마야 비의존)

```python
doc = fbx_binary.read(path)                  # FbxDocument
doc.version                                   # 7700
doc.settings                                  # {"up_axis": "Z", "unit_cm": 1.0, "fps": 60.0, "start": 1, "stop": 6285}
doc.models[id]                                # FbxModel(id, name="CHOEUN:Hips", short="Hips", kind="LimbNode", props={...})
doc.parent[id] -> id | 0
doc.skeleton_roots()                          # [(root_id, "CHOEUN", n_limbs), ...]
doc.dag_path(id)                              # "|CHOEUN|Hips|Spine"  (네임스페이스 접두사 제거, FBXASC 인코딩은 §10)
doc.rotation_order(id)                        # "XZY" (FBX enum 0..5 -> 문자열)
doc.pre_rotation(id) / post_rotation(id)      # (x, y, z) deg
doc.channel(id, "Lcl Rotation")               # {"X": Track, "Z": Track}  (없는 축은 빠진다)
Track.frames / Track.values / Track.interp    # list[float] · list[float] · "linear"|"constant"|"cubic"
doc.static(id, "Lcl Rotation")                # 커브 없는 축의 정적 값
```

- 배열은 `array.array('f'|'d'|'q'|'i').frombytes(zlib.decompress(...))` 로 푼다. numpy 를 쓰지 않는다.
  **이 PC 의 numpy 는 Maya 번들이 아니라 사용자 site-packages(`AppData\Roaming\Python\Python310`)에 있다** —
  `DEPENDENCIES.md` 의 "Maya 2022+ 내장" 서술과 다르다. 그래서 numpy 에 기대지 않는다.
- 배열은 **필요할 때 푼다**(lazy). 스캔은 헤더와 Model 속성만 읽는다.
- FBX 버전 < 7500 이면 노드 헤더가 32비트다(블렌더 출력 7400). 둘 다 지원한다.

### 7-2. `Framework/core/euler_math.py` (마야 비의존)

```python
alternate(v, order)                # 같은 방향의 다른 해: first+180, 180-middle, last+180
unwrap_triples(xs, ys, zs, order)  # 세 축 모두 키가 있을 때 (§8-4)
unwrap_single(values)              # 한 축만: 2pi 배수만 (동치 해를 쓸 수 없다)
matrix(v, order) / mat_mul / max_abs_diff   # 3x3 리스트 행렬 (검증용)
```

### 7-3. `Framework/core/maya_fbx_exact.py` (마야)

```python
scan(path) -> (info: dict, logs: list)
import_exact(path, skeletons=None, skeletons_only=True, unwrap=True, normalize=True, verify=True)
    -> (ok: bool, logs: list, report: dict)
fix_scene_from_fbx(path, roots=None, unwrap=True, normalize=False, verify=True) -> (ok, logs, report)
```

- 반환 규약은 기존 `maya_fbx` 와 같다 — `(성공, 로그 리스트)`. 로그 표식은 [Framework_log_levels](../Framework_log_levels.md).
- **undo**: 키 수백만 개를 undo 큐에 올리지 않는다. 덮기 · 언랩 · 정규화 구간은 `cmds.undoInfo(stateWithoutFlush=False)` 로 감싸고 `finally` 에서 되돌린다.
  로그에 `[Info] Undo is not recorded for this import.` 를 남긴다. 사전 검사(이름 충돌 `[FAIL]`)가 기존 씬을 보호한다. → Q4

### 7-4. `maya_fbx.import_options(...)`

기존 `fbx_options()`(export 용)과 같은 모양이다. `with` 블록 안에서만 `FBXImportQuaternion` · `FBXImportFillTimeline` ·
`FBXImportMode`(`add`)를 바꾸고, 나갈 때 `-q` 로 읽어 둔 값으로 되돌린다.
**사용자가 평소 쓰는 임포트 설정을 이 기능이 바꿔 놓지 않는다.**

---

## 8. 알고리즘 상세

### 8-1. 바이너리 FBX 파서 (시제품에서 검증한 핵심)

```python
# header 27 B: "Kaydara FBX Binary  \x00\x1a\x00" + uint32 version
# node record: endOffset, numProps, propListLen (version >= 7500: uint64 x3, else uint32 x3), uint8 nameLen, name
# props: Y i16 · C bool · I i32 · F f32 · D f64 · L i64 · S/R (u32 len + bytes)
#        f/d/l/i/b array: u32 count, u32 encoding(1=zlib), u32 compressedLen, data
# 자식 노드는 endOffset 까지, 끝은 null record (13 B / 25 B)
```

- 필요한 노드: `GlobalSettings`(UpAxis · UnitScaleFactor · TimeMode · CustomFrameRate), `Objects/Model`(Properties70),
  `Objects/AnimationCurveNode` · `AnimationCurve`(KeyTime · KeyValueFloat · KeyAttrFlags · KeyAttrRefCount),
  `Objects/AnimationStack`(LocalStart · LocalStop), `Connections`(`OO` 부모 · `OP` 속성 연결: 커브 → 커브노드 `d|X`, 커브노드 → 모델 `Lcl Rotation`).
- TimeMode → fps 표: 0 기본(CustomFrameRate), 1=120, 2=100, 3=60, 4=50, 5=48, 6=30, 7=30 drop, 8=29.97 NTSC drop, 9=29.97, 10=25, 11=24, 12=1000, 13=23.976, 14=custom, 15=96, 16=72, 17=59.94.
- 키 시간: `frame = ticks * fps / 46186158000` (정수에 1e-6 안이면 반올림). 이 파일은 키 13,104,225개 전부 정수 프레임이다.
- AnimationStack 이 여럿이면 첫 스택을 쓰고 `[WARN]` 을 남긴다(Phase 1).

### 8-2. 노드 매핑

- FBX 계층 경로를 마야 경로로 바꾼다. 이름의 `ns:` 접두사를 떼고 `|` 로 잇는다 → `|CHOEUN|Hips|Spine`.
  임포트 모드는 4단계에서 수집한 **새 루트 아래**에서만 찾는다.
- 찾지 못한 노드는 `[WARN] Not found in scene: <path>` 로 모은다(10개까지 보여 주고 나머지는 개수만).
- 매핑된 조인트의 `rotateOrder` 가 파일 RotationOrder 와 다르면 그 조인트는 덮지 않는다(§6-4).
  FBX → Maya 순서 표: XYZ→0 · XZY→3 · YZX→1 · YXZ→4 · ZXY→2 · ZYX→5.

### 8-3. 회전 커브 다시 만들기 (시제품 그대로)

```python
from maya.api import OpenMaya as om, OpenMayaAnim as oma
TANGENT = {"linear": oma.MFnAnimCurve.kTangentLinear, "constant": oma.MFnAnimCurve.kTangentStep}
for axis, attr in (("X", "rotateX"), ("Y", "rotateY"), ("Z", "rotateZ")):
    track = tracks.get(axis)
    if track is None: continue                       # 파일에 없는 축은 임포터의 정적 값을 둔다
    old = cmds.listConnections(plug_name, s=True, d=False, type="animCurve") or []
    if old: cmds.delete(old)
    fn = oma.MFnAnimCurve(); fn.create(plug, oma.MFnAnimCurve.kAnimCurveTA)
    times = om.MTimeArray([om.MTime(f, om.MTime.uiUnit()) for f in track.frames])
    vals = om.MDoubleArray([math.radians(v) for v in values])      # API 각도 = 라디안
    fn.addKeys(times, vals, TANGENT[track.interp], TANGENT[track.interp])
```

- 회전 플러그에 animCurve 가 아닌 입력(컨스트레인트 · pairBlend · animLayer)이 걸려 있으면 `[SKIP]` 한다. 이 파일은 없다.
- Cubic 키(이 파일은 없다)는 Phase 1 에서 `kTangentAuto` 로 근사하고 `[WARN] Cubic keys approximated` 를 남긴다. 정확한 탄젠트(KeyAttrDataFloat)는 Phase 2.

### 8-4. 회전 순서를 고려한 언랩

```python
def alternate(v, order):          # order "XZY" = X 가 먼저 적용
    i = {"X": 0, "Y": 1, "Z": 2}
    f, m, l = i[order[0]], i[order[1]], i[order[2]]
    a = list(v); a[f] += 180.0; a[m] = 180.0 - a[m]; a[l] += 180.0
    return a

def unwrap_triples(xs, ys, zs, order):
    prev = [xs[0], ys[0], zs[0]]; out = [prev]
    for k in range(1, len(xs)):
        best = None
        for c in ([xs[k], ys[k], zs[k]], alternate([xs[k], ys[k], zs[k]], order)):
            c = [c[j] + 360.0 * round((prev[j] - c[j]) / 360.0) for j in range(3)]
            d = abs(c[0] - prev[0]) + abs(c[1] - prev[1]) + abs(c[2] - prev[2])
            if best is None or d < best[0]: best = (d, c)
        prev = best[1]; out.append(prev)
    return out
```

- 시제품(이 로직을 numpy 로 키마다 호출) 결과: 300 트리플 · 튐 1603 → 0 · 행렬 최대 차 2.3e-15 · 17.9초.
  위 순수 파이썬 리스트 연산은 키마다 numpy 를 호출하는 오버헤드가 없다. **목표 5초 이하**이고 T4 에서 잰다.
  넘치면 프레임 루프 안에서 조인트를 묶어 처리한다.
- 세 축이 모두 키가 아니면 `unwrap_single` 로 축마다 2π 만 맞춘다. 동치 해는 세 축을 함께 바꾸기 때문이다.
- 마야의 `MEulerRotation.closestSolution` 도 순서를 고려하지만 키마다 API 객체를 만드는 비용이 커서 정규화 단계에서만 쓴다.

### 8-5. Normalize joints

키마다 (row-vector, 마야 joint 규약 `[S][RA][R][JO]…`):

```python
m = om.MEulerRotation(rad(r), ro).asMatrix() * om.MEulerRotation(rad(jo), XYZ).asMatrix()
e = om.MEulerRotation.decompose(m, om.MEulerRotation.kXYZ).closestSolution(prev)
```

- 키가 없는 축은 정적 값으로 채워서 계산한다. 결과는 세 축 모두 키다.
- 키 시간은 그 조인트의 회전 커브 키 시간의 합집합이다(이 파일은 세 축이 같다).
- `rotateAxis ≠ 0` 인 조인트는 `m = RA · R · JO` 로 넣고 RA 도 0 으로 만든다(이 파일은 전부 0).
- 끝나면 `jointOrient = 0`, `rotateOrder = xyz`. 키가 하나도 없는 조인트도 jo 를 회전 값으로 옮긴다.

### 8-6. 검증

- **커브 수준(빠르다)** — 샘플 프레임마다 마야 쪽은 `MFnAnimCurve.evaluate` 와 jo · ro 로, 파일 쪽은
  `Rpre · R(order) · Rpost⁻¹` 로 회전 행렬을 만들어 최대 원소 차를 각도로 바꾼다. 샘플은 10프레임마다 + 원본 튐이 있던 프레임 + 마지막 프레임이다.
- **DG 수준(스모크)** — 5프레임만 `currentTime` + `xform -ws` 로 루트별 손끝 월드 위치를 FBX 월드 계산값(Z-up → Y-up 변환 포함)과 비교한다.
- 실패 기준: 회전 1e-3° 또는 위치 1e-3cm 초과 → `[FAIL] Verify` 와 가장 나쁜 조인트 · 프레임 5개를 남긴다.

---

## 9. 작업 순서

| # | 작업 | 산출물 · 완료 조건 |
|---|------|------|
| T1 | `fbx_binary.py` + 순수 파이썬 테스트 | BCM(7700, 64비트) · CHOEUN(7400, 32비트)에서 §2-1 표의 숫자가 그대로 나온다. 테스트 안에 작은 FBX 를 직접 쓰는 헬퍼를 둬서 실파일 없이도 32 · 64비트 · zlib 배열 · 연결을 검증한다. 실파일 테스트는 환경 변수 `JUN_FBX_TEST_DIR` 이 없으면 skip |
| T2 | `euler_math.py` + 테스트 | 6개 순서 모두 `matrix(alternate(v)) == matrix(v)`(1e-12), 무작위 래핑 시퀀스 언랩 뒤 튐 0 · 행렬 불변 |
| T3 | `maya_fbx.import_options` + 임포터 동작 실측 | 옵션 복원 확인. **씬 fps ≠ 파일 fps 일 때 임포터가 시간 단위를 바꾸는지** 실측해 §6-2 의 2단계를 확정한다 |
| T4 | `maya_fbx_exact.import_exact` (1 ~ 8, 11단계) | mayapy: BCM 5명 전수 조사 0 · 월드 0 · 튐 0 · 진단 로그가 CHOEUN Hips 1-5493 / RightArm 3707-6285 를 짚는다. 시간 측정 |
| T5 | 정규화 · 검증 (9, 10단계) | Normalize ON: jo 0 · ro xyz · 월드 오차 < 1e-3cm. `0020_CHOEUN_0010.mb` 와 조인트 이름 · 계층이 같다(`_end` 제외) |
| T6 | `fix_scene_from_fbx` | `0010_motion_0010.mb` 를 열고 고친 뒤 전수 조사 0 |
| T7 | A00480 UI · 래퍼 · v01.13 · CHANGELOG | 오프스크린 UI 테스트(스캔 → 체크 목록 · 버튼 활성 · 로그) |
| T8 | 문서 · WORKLOG · 메모리 | `A00480_FileTool.md` §3-2, `Framework_fbx_binary.md`, `Framework_maya_fbx.md`, README 툴 표 |
| T9 | **마야 GUI 확인 (사용자)** | 실제 마야 2024 창에서 BCM 임포트 → 뷰포트로 Hips · RightArm 확인 |

### 받아들임 기준 (BCM_01_004.fbx)

| # | 기준 |
|---|------|
| A1 | 5명 전부, 6285프레임 전부 회전 불일치 **0** (§2-3 방식) |
| A2 | 월드 위치 오차 **< 0.001cm** (365조인트 × 130프레임 이상) |
| A3 | 언랩 뒤 연속 키 180° 초과 튐 **0**, 행렬 불변(≤ 1e-9) |
| A4 | Normalize ON 도 A1 · A2 를 만족하고 모든 조인트가 jo 0 · ro xyz |
| A5 | 전체 시간 **40초 이하**(이 PC, 임포트 9초 포함) |
| A6 | 문제없는 FBX(`0020_CHOEUN_0010.fbx`)도 돌아가고 `No flips found` · 오차 0 |
| A7 | 사용자 FBX 임포트 옵션이 실행 전과 같다 |

---

## 10. 경계 사례 · Phase 1 에서 안 하는 것

| 사례 | 처리 |
|------|------|
| ASCII FBX | 지원하지 않는다 → `[FAIL] ASCII FBX is not supported yet.` (Phase 2) |
| 이름에 특수문자 | 마야 임포터는 `[A-Za-z0-9_]` 밖의 바이트를 `FBXASC%03d` 로 바꾼다 → 매핑도 같은 규칙으로 인코딩한다(T4 테스트에 포함) |
| 스택 여러 개 · 애니 레이어 여러 개 | 첫 스택 · 첫 레이어만, `[WARN]` |
| Cubic 키 | §8-3 근사 + `[WARN]` |
| LimbNode 가 아닌 노드(Null · Marker)의 회전 | 덮지 않는다(같은 버그가 있을 수 있지만 이번 요청 밖이다. Marker 는 이동만 있다) |
| 이동 · 스케일 커브 | 덮지 않는다. euler 모드에서는 파일 키 그대로 들어오는 것을 확인했다(A2) |
| Maya 2023 | 이 PC 에 없어서 확인 못 한다. API 는 2023 에도 있는 것만 쓴다(`MFnAnimCurve.addKeys` · `MEulerRotation`) |
| 다른 FBX 플러그인 버전 | §3 — 확인 안 했다 |

---

## 11. 결정이 필요한 것

| # | 질문 | 추천 |
|---|------|------|
| Q1 | `Normalize joints` 기본값 | **ON** — 요청이 "0020 처럼" 이고, 지금까지 쓰던 블렌더 경유 결과와 표현이 같아야 뒤 공정(리타깃 등)이 그대로 돈다. 원본 표현(jo · 회전 순서)이 필요하면 끄면 된다 |
| Q2 | `Skeletons only` 기본값 | **ON** — 블렌더 경유도 스켈레톤만 남겼고, 마커 390개와 카메라 67개는 보통 필요 없다 |
| Q3 | 타임라인 | **파일 그대로(1 ~ 6285)**. 블렌더 경유는 0 ~ 6284 로 1프레임 당겨진다. 기존 작업과 프레임을 맞춰야 하면 `Start Frame` 칸을 Phase 2 로 더한다 |
| Q4 | undo | **기록하지 않는다**(키 560만 개). 대신 이름 충돌이면 `[FAIL]` 로 막아 기존 씬을 보호한다 |
| Q5 | Phase 2 — `A00210_FileManager` 에서 FBX 폴더를 일괄 `.mb` 로 | 요청이 있을 때. 코어가 Framework 에 있으니 mayapy 워커 잡 하나다 |

---

## 부록 A. 실측 방법 (재현용)

| 검사 | 방법 |
|------|------|
| FBX 덤프 | 순수 파이썬 파서(§8-1)로 GlobalSettings · Model 속성 통계 · 스택 · 커브 플래그 |
| 정답 계산 | `Local = T · Rpre(XYZ) · R(RotationOrder) · Rpost⁻¹ · S` 를 부모로 곱해 월드. 커브는 Linear 보간 |
| 전수 조사 | 조인트마다 6285프레임 `Rpre · R(order)` vs `jo · R(ro)` 회전 행렬 최대 원소 차 > 1e-3 이면 불일치. 마야 값은 `keyframe -q -tc -vc` 를 보간 |
| 모드 재현 | 새 mayapy 세션 · `FBXResetImport` · `FBXImportQuaternion -v <mode>` · `FBXImport -f` |
| 블렌더 정확도 | `0020_CHOEUN_0010.mb` 프레임 f ↔ FBX 프레임 f+1, Hips 이동 커브 전 프레임 · 월드 위치 25프레임마다 |
| 덮기 시제품 | §8-3 코드 → 전수 조사 + 월드 검사 |

> 시제품을 돌리다 겪은 함정: 스크립트 폴더에 `imp.py` 를 두면 표준 라이브러리 `imp` 를 가려서 mayapy 가
> `Python is unable to find Maya's Python modules` 를 내며 망가진다. 테스트 · 도구 파일 이름이 표준 모듈과 겹치지 않게 한다.
