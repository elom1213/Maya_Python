---
title: Framework.core.fbx_binary · euler_math · maya_fbx_exact — FBX 리더 · 오일러 수학 · 모캡 정확 임포트
aliases: [fbx_binary, euler_math, maya_fbx_exact, FBX reader, rotate order unwrap]
tags: [maya-python, framework, fbx, import, mocap, animation]
updated: 2026-10-27
---

# `Framework.core.fbx_binary` · `euler_math` · `maya_fbx_exact`

2026-10-27 [A00480_FileTool](A00480_FileTool.md) v01.13 `Mocap FBX Import (Exact Rotation)` 을 위해 만들었다.
마야 FBX 임포터가 비 XYZ 회전 순서 조인트의 회전 키를 XYZ 동치 공식으로 뒤집는 문제를, **파일 원본 키로 커브를 다시 써서** 고친다.
배경 · 실측은 [계획서](plans/A00480_FileTool_fbx_exact_import_plan.md). Framework 에 둔 이유는 나중에 A00210 일괄 처리(요청 시)가 같은 코드를 쓰게 하려는 것.

| 모듈 | 마야 필요 | 하는 일 |
|------|-----------|---------|
| `fbx_binary` | ❌ (순수 파이썬, numpy 없음) | 바이너리 FBX(7.x, 32/64비트 노드 헤더, zlib 배열) 리더. 모델 · 계층 · 애니 커브 |
| `euler_math` | ❌ | 오일러 동치 · 언랩 · 3x3 행렬 · (jo · 회전 순서 · ra) → XYZ 정규화 |
| `maya_fbx_exact` | ✅ (maya.cmds lazy) | `scan` · `import_exact` · `fix_scene_from_fbx` |
| `maya_fbx.import_options` | ✅ | `with` 블록 안에서만 `FBXImportQuaternion` · `FBXImportMode` · `FBXImportFillTimeline` 을 바꾸고 되돌린다 |

## `fbx_binary`

```python
from Framework.core import fbx_binary as fb

doc = fb.read(path)                      # FbxDocument (ASCII FBX 는 FbxError)
doc.version                              # 7700
doc.settings                             # {"up_axis": "Z", "unit_cm": 1.0, "fps": 60.0, "start": 1.0, "stop": 6285.0}
doc.counts                               # {"LimbNode": 365, "Marker": 390, ...}
doc.skeleton_roots()                     # [(id, "CHOEUN", 73), ...]  자손에 LimbNode 가 있는 최상위 모델
doc.models[id].name / .short / .kind     # "CHOEUN:Hips" / "Hips" / "LimbNode"
doc.children[id] · doc.parent[id] · doc.descendants(id) · doc.path_from(root, id)
doc.rotation_order(id)                   # "XZY" (앞 글자가 먼저 적용 = 마야 rotateOrder 와 같은 뜻)
doc.pre_rotation(id) / post_rotation(id) / static(id, "Lcl Translation")
doc.build_channel_index()                # 큰 파일에서 channel() 을 많이 부르기 전에 한 번
doc.channel(id, "Lcl Rotation")          # {"X": Track, "Y": Track, ...}  커브 있는 축만
Track.frames · .values · .interp_kind() · .value_at(frame)   # 파일 fps 프레임, Linear/Constant 보간
doc.value_at(id, prop, frame)            # (x, y, z) - 커브 없는 축은 정적 값
fb.maya_node_name("Spine-1")             # "SpineFBXASC0451" - 마야 임포터가 만드는 이름
```

- 108MB(키 1300만 개) 파일을 약 0.2초에 읽는다. 배열은 `values()` 를 부를 때 푼다(`array` 모듈).
- **numpy 를 쓰지 않는다** — 이 PC 의 numpy 는 Maya 번들이 아니라 사용자 site-packages 에 있었다(2026-10-27). Maya 2023 에서도 돌아야 한다.
- 애니 스택 · 레이어가 여럿이면 첫 스택의 첫 레이어만.

## `euler_math`

```python
em.alternate(v, order)                   # 같은 자세의 다른 해: first+180, 180-middle, last+180
em.unwrap_triples(xs, ys, zs, order)     # 세 축 키가 같은 시간일 때 - 두 해 x 2π 중 이전 키에 가장 가까운 것
em.unwrap_single(values)                 # 한 축만 - 2π 만
em.normalize_xyz(xs, ys, zs, order, jo, ra)   # JO · R(order) · RA (열 벡터) -> XYZ 오일러 + 연속 해
em.matrix(v, order) · mat_mul · transpose · decompose_xyz · angle_between · same_angles · count_jumps
```

- 마야 임포터의 버그 = `alternate(v, "XYZ")` 를 XZY 조인트에 쓴 것. 테스트에 실측값(RightArm f3707)으로 재현돼 있다.
- `decompose_xyz` · `normalize_xyz` 의 y 는 `asin` 이 아니라 `atan2(-m20, cy)` — 어깨처럼 PreRotation Y 90° 인 조인트는 정규화하면 y ≈ 90° 가 되는데,
  asin + 근사 분기는 그 근처에서 0.05° 틀렸다(2026-10-27 실측). 지금은 짐벌 근처도 1e-9° 안.
- `angle_between` 은 `||A−B||_F = 2√2·sin(θ/2)` 로 구한다 — acos(trace) 는 작은 각에서 1e-6° 쯤 뭉개져서 허용치 비교가 틀린다.

## `maya_fbx_exact`

```python
from Framework.core import maya_fbx_exact as fx

info, logs = fx.scan(path)                                   # 씬을 안 건드림
ok, logs, report = fx.import_exact(path, skeletons=None, skeletons_only=True,
                                   unwrap=True, normalize=True, verify=True, progress=None)
ok, logs, report = fx.fix_scene_from_fbx(path, roots=None, unwrap=True, normalize=True, verify=True, progress=None)
```

순서: (import 만) 이름 충돌 검사 → `import_options(quaternion="euler", mode="add")` 로 `FBXImport` → 새 루트 · 빈 네임스페이스 정리
→ 조인트 매핑(계층 경로, 네임스페이스 무시) → 진단 → 회전(+이동) 커브 재생성(`MFnAnimCurve.addKeys` 한 번) → 정규화 / 언랩 → 검증.

| 판단 | 기준 |
|------|------|
| 덮을 조인트 | LimbNode · 마야 joint · rotateOrder = 파일 · jointOrient = PreRotation · rotateAxis 0 · PostRotation 0 · rotate/translate 입력이 animCurve 뿐. 아니면 `[SKIP]` |
| "wrong rotations" | 마야 값 = 파일 값의 XYZ 동치(허용 0.001°, 버그 지문) **또는** 자세 차이 > 1° |
| 미세 차이 | 그 밖에 0.001° 넘는 것(임포터의 키 감소 · 탄젠트) - `[Info]` 한 줄 |
| 이동 | 파일에 이동 커브가 있는 축만, 파일 · 씬 단위가 둘 다 cm 일 때 |
| Fix 의 키 시간 | 씬 키 시간이 파일 키 시간의 **부분집합**이면 OK(임포터가 키를 줄인다), 아니면 `[FAIL]` |
| 검증 | 커브 수준: 조인트당 약 200 샘플, `Rpre·R·Rpost⁻¹` vs `JO·R·RA` / DG 수준: 시작 · 중간 · 끝 3프레임, 루트 기준 조인트 위치. 허용 0.001° · 0.001cm |

실측(mayapy 2024, `BCM_01_004.fbx` 5명): 임포트 6.7초 + 재생성 22.5초 + 검증 3.5초 = 34초, 검증 0.0000° · 0.0000cm,
별도 검사(47,815 샘플 월드 위치) 최대 0.000004cm. CHOEUN 하나만 12초. 사용자 씬 고치기(5명) 32초.

## 실측으로 정한 것

- **마야 FBX 임포터는 씬 fps 를 파일 fps 로 바꾼다**(ntsc 씬 → ntscf). 그래서 미리 맞추지 않고 바뀌면 로그만 남긴다.
- `FBXImportQuaternion euler` 모드는 재샘플을 안 해서 이동 커브가 파일 키 그대로 들어온다. 기본 `resample` 은 모든 조인트를 0.1° 안팎 바꾼다.
- 마야 임포터는 `CHOEUN:Hips` 의 접두사를 떼고 `|CHOEUN|Hips` 를 만들면서 **빈 네임스페이스를 수백 개** 남긴다(이 파일 827개, "No namespace matches name: 'System'" 오류가 줄줄이 찍힌다).
- 마커는 캐릭터 루트 Null 의 자식이다 → `Skeletons only` 는 루트 아래 조인트 없는 가지도 지운다.

쓰는 곳: [A00480_FileTool](A00480_FileTool.md) §3-2. 시험: `tools/A00480_FileTool/tests/test_fbx_core.py`(순수 파이썬 45) · `test_fbx_exact.py`(mayapy 29).
