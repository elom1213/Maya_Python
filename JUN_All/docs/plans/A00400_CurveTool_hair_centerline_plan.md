---
title: A00400_CurveTool — Create > From Hair (헤어 가닥 중심선 커브) 계획서
tags: [maya-python, plan, curve-tool, hair, centerline, houdini-port]
updated: 2026-11-09
---

# A00400_CurveTool — `Create > From Hair` 계획서

헤어 메시 가닥마다 **가닥을 관통하는 중심선 커브**를 마야 안에서 바로 만든다.
지금은 Houdini(`0010_hairShrink_LUN_01.hip`)에서 커브를 뽑아 abc 로 넘긴 뒤 마야에서 조인트 · 리깅을 했다.
이 계획은 그 Houdini 단계를 **A00400_CurveTool 의 새 하위 탭**으로 대체한다.

목표 버전: **A00400 v01.32**. 이 문서만 보고 구현 · 검증까지 끝낼 수 있게 쓴다.

> **상태 (2026-11-09)**: v01.32 로 **구현 완료** · mayapy 시험 66/66 · **마야 GUI 확인 아직.**
> 구현하며 계획에서 바뀐 점은 맨 아래 §12.

---

## 0. 한눈에

| 항목 | Houdini (현재) | 마야 툴 (이 계획) |
|------|----------------|-------------------|
| 방식 | 가닥마다 VDB 로 메시를 수축 → 3D 스켈레톤(Labs `straight_skeleton_3d`) | 가닥의 **열린 끝(경계 루프)에서 링 단위 BFS → 링 중심점** |
| 149 가닥 시간 | **71.5 초**(foreach 루프만) | 시제작 **0.47 초**(순수 파이썬, 같은 데이터) |
| 결과 커브 | 150개(가닥 146개에서 커브 · 3개 실패 · 2개는 쪼개짐 + 2점짜리 조각 4개) | 가닥당 정확히 1개(필터로 뺀 것 제외) |
| 방향 | 정해지지 않음 | **cv[0] = 뿌리(열린 끝)** 로 고정 |
| 편차 | — | Houdini 커브와 평균 편차 중앙값 **0.15 cm**, p95 0.23 cm |
| 추가 | — | 크기 · 길이 필터, Analyze(미리 보기), CV 개수 지정, Joints 탭 연동 |

---

## 1. 요구 (2026-11-09 사용자)

| # | 요구 | 결정 |
|---|------|------|
| 1 | hip 의 `foreach_begin1 ~ foreach_end1` 루프(메시마다 커브 생성)를 마야에서 그대로 | 결과(가닥당 중심선 커브)를 재현한다. **알고리즘은 바꾼다**(§4 — VDB 수축 대신 링 중심점) |
| 2 | 각각 분리된 헤어 메시 가닥 → 가닥을 관통하는 커브 → 커브 CV 에 맞는 조인트 → 리깅 | 커브 생성까지가 이 기능. 조인트 · 바인드 · 컨트롤러는 **기존 `Edit > Joints`** 가 한다(§5.6 연동) |
| 3 | `A00400_CurveTool` 에 추가 | `Create` 카테고리에 새 하위 탭 **`From Hair`** |
| 4 | 일정 길이 이하 커브 / 일정 크기 이하 메시는 만들지 않기 | `Skip meshes smaller than` (바운딩 박스 대각선) + `Skip curves shorter than` (중심선 길이), 둘 다 체크 + 값 |
| 5 | Houdini 보다 빠르게 | 목표: 149 가닥(71,599 정점) **3 초 이내**(시제작 0.47 초 + 마야 읽기 · 커브 생성) |

---

## 2. Houdini 파일 분석

대상: `JP__LUN/JP__Rig/JP__Revision_01020_HDN/JP_0030_hairshrink/0010_hairShrink_LUN_01.hip` (Houdini 21.0.700)
입력 `0010_src/hair_01.fbx`, 출력 `0020_out/hair_02.abc|fbx`(커브), `hair_01.abc|fbx`(델타머시 메시).

### 2.1 노드 그래프 (`/obj/geo1`)

```
file1 (hair_01.fbx)
 └ transform1        scale 0.01            cm → m
   └ deltamush1      iter 53, step 0.5351, pin border   ← display. rop_fbx1 이 여기서 hair_01.fbx 출력
     └ polyreduce1   24.5 %                71,478 → 17,511 프림 (스켈레톤 속도용)
       └ connectivity1  prim, attr "class"   가닥 = 연결 성분 149개
         └ foreach_begin1  (piece)  ─────────────── 루프 시작: 가닥 하나
             null1
             color1            흰색(의미 없음)
             straight_skeleton_3d1   Labs. voxel 0.01, accuracy 0.5, iter 10, fuse 0.01  ← 핵심
             convert1          → NURBS curve, order 4
             remesh1           (커브에는 효과 없음 — 폴리곤용 노드)
             smooth1           uniform, strength 10, 끝점 고정(groupboundary)
             resample1         최대 세그먼트 1.97 m → 사실상 NURBS → 폴리라인 변환만
           foreach_end1  (pieces, merge, attrib = class) ── 루프 끝
 └ null2
   ├ separatepieces1 (class 로 조각 띄우기) ─┐
   └ blendshapes1 (blend1 = 1 → null2 모양) ─┘  결과적으로 항등 — 위치 변화 없음
     └ attribdelete1   점 · 프림 어트리뷰트 삭제(class 만 남김)
       └ transform2    scale 100   m → cm
         ├ rop_fbx2      hair_02.fbx  (path = class → 커브마다 오브젝트)
         └ rop_alembic1  hair_02.abc
```

**마야로 옮길 때 필요 없는 것**: `transform1/2`(단위 왕복), `color1`, `remesh1`, `separatepieces1 + blendshapes1`(항등),
`attribdelete1`, ROP 두 개(커브가 이미 씬에 있다).
**전처리였던 것**: `deltamush1` · `polyreduce1` 은 스켈레톤을 안정 · 빠르게 하려는 것 — 링 중심점 방식은 둘 다 필요 없다.
델타머시의 "울퉁불퉁함 제거" 효과는 중심선 스무딩(§5.3)이 대신한다.
**재현할 것**: 루프 본체(가닥 → 중심선) + `smooth1`(끝점 고정 라플라시안) + 출력 점 밀도(`resample`).

### 2.2 Labs `straight_skeleton_3d` 내부 (HDA 잠금 해제 후 확인)

1. 가닥을 단위 박스 크기로 맞춤(`matchsize`) → `remesh`(적응형, `gradation = 1 - accuracy`).
2. **수축 루프**(최대 `iterations` 10회, 점 99 %가 볼륨 밖이면 정지):
   메시 → SDF VDB(`voxel_size` 가 반복마다 커짐) → 평균 곡률 흐름 스무딩 → 그래디언트 정규화 →
   잠기지 않은 점을 **안쪽으로 이류(advect, RK4)** → 엣지 리샘플 → 볼륨 밖으로 나간 점 · 면은 잠금.
   (Au et al. "mesh contraction" 계열 메디얼 축 추출을 VDB 로 한 것)
3. **세선화 루프**(voxel 0.03) — 같은 구조로 한 번 더.
4. 정리: 삼각형 → 선(`divide` · `ends` · `fuse`), 끝점 제외 100회 블러, `polypath` 로 잇기,
   가지점(이웃 > 2)에서 `polycut` → 가지마다 커브. `matchsize` 로 원래 크기 복원.

→ 위상과 무관하게 어떤 덩어리든 스켈레톤을 내지만 **느리고(가닥당 ~0.5 초), 끝이 안쪽으로 줄고(끝 간격 중앙값 0.9 cm),
가끔 쪼개진다**(아래 실측).

### 2.3 실측 (hython 으로 hip 을 실제 쿡, 2026-11-09)

| 측정 | 값 |
|------|----|
| 입력 | 71,599 점 / 71,478 프림 / 가닥 149 |
| `foreach_end1` 쿡 | **71.54 초** |
| 결과 | 폴리라인 150개 · 점 13,176 |
| 가닥 → 커브 수 | 1개 144 가닥 · **3개 2 가닥**(class 146 · 147 — 본 커브 + 길이 0.14 cm 2점 조각 둘) · **0개 3 가닥** |
| 커브 길이 (cm) | 최소 0.06 · 평균 11.8 · 최대 22.4 |
| 커브당 점 | 2 ~ 137 (본 커브는 50 ~ 137, 점 간격 ≈ 0.1 cm — Labs 내부 `resample 0.001 m`) |

마야에서 `hair_02.fbx` 를 임포트하면 **커브가 0개**(폴리라인 커브가 FBX 로 안 넘어옴) — 그래서 지금은 abc 경로를 쓴다.

---

## 3. 입력 데이터 실측 — 알고리즘을 정한 근거

`hair_01.fbx` (Houdini 와 mayapy 2024 양쪽에서 확인)

| 항목 | 값 |
|------|----|
| 마야 임포트 | **메시 오브젝트 149개, 각 1 shell**, 단위 cm, 계층 있음 (`LUN_Hair_grp1|LUN_hair_n_01_01|LUN_hair_n_01_03` — 메시 아래 메시) |
| 면 | 쿼드 위주 + 삼각형(끝 팬). 141 가닥 = 3·4각형만, 7 가닥 5·6각형 섞임, 1 가닥 쿼드만 |
| 경계 루프 | **149 가닥 전부 정확히 1개**(크기 12 ~ 24) — 뿌리 쪽이 열린 튜브 |
| 끝 | 삼각형 팬으로 닫힘(극점 정점 valence = 링 크기) |
| 비다양체 | 0 |
| 정점 / 가닥 | 4 ~ 1,065 (중앙 421) |
| 바운딩 박스 대각선 | **0**(정점 4개짜리 퇴화 조각 1개) · 그 다음 4.18 cm · 중앙 12.2 cm · 최대 20.8 cm |
| 열린 끝의 높이 | 열린 끝(경계 루프 중심) 이 극점보다 **위 146 / 아래 2** — 열린 끝 = 두피 쪽 뿌리 |
| 링 크기 | 일정 122 가닥 · 극점 근처에서 변함 26 가닥 (중심점 계산엔 문제 없음) |
| 링 수 / 가닥 | 1 ~ 53 (중앙 26) |

**결론**: 이 데이터는 "한쪽이 열린 쿼드 튜브" 다. 열린 끝(경계 루프)에서 위상 거리(BFS 단계)로 링을 나누면
링 하나가 곧 튜브의 단면이고, **단면 중심을 이으면 중심선**, 첫 링이 뿌리이므로 **방향도 저절로** 정해진다.
VDB 도, 메시 감소도, 반복 수축도 필요 없다.

---

## 4. 마야 알고리즘

### 4.1 왜 Labs 스켈레톤을 옮기지 않는가

- 마야 `cmds` 에는 OpenVDB SDF · 이류 노드가 없다(Bifrost 로 가능은 하나 그래프 · 의존성 · 속도 모두 손해).
- 원본도 가닥당 0.5 초 — 옮겨도 빠를 수 없다. 사용자 요구 5(더 빠르게)와 정면 충돌.
- 원본의 결함(끝 수축, 조각, 실패 3 가닥)까지 따라온다.

### 4.2 기본 엔진 — `Rings` (위상 링 중심점)

가닥(shell) 하나마다:

```
seeds  = 뿌리 정점 집합 (§4.4)
level  = seeds 에서 시작하는 BFS 단계 (엣지 홉 수)        # 링 0, 1, 2, ...
pts[k] = level == k 인 정점들의 평균 위치                  # 단면 중심
pts    = 끝점 고정 라플라시안 스무딩(pts)                   # Houdini smooth1
pts    = 끝 다듬기(trim) → 리샘플(호 길이 균등)             # Houdini resample
```

- 마지막 링은 끝 팬의 극점 하나 → 커브 끝이 가닥의 **실제 끝**에 닿는다(Houdini 는 0.9 cm 안쪽에서 끝남).
- 첫 링은 경계 루프 → 커브 시작이 **가닥의 열린 끝(두피 쪽)**.

시제작 결과(§0): 149 가닥 0.47 초, Houdini 커브와 평균 편차 중앙값 0.15 cm, 길이는 Houdini 가 우리 것의 0.92 배
(Houdini 가 양끝이 줄어든 만큼).

### 4.3 보조 엔진 — `Geodesic` (측지 거리 슬라이스)

위상이 고르지 않은 메시(삼각화 · 리듀스된 메시, 카드형, 링이 비스듬한 경우)용.

```
dist   = seeds 에서의 Dijkstra 거리 (엣지 길이 가중)
bins   = [0, max(dist)] 를 Slices 개로 균등 분할
pts[k] = bin k 에 든 정점들의 평균 위치 (빈 bin 은 건너뜀)
```

나머지(스무딩 · 다듬기 · 리샘플)는 같다. `heapq` 순수 파이썬, 가닥당 수백 정점이라 충분히 빠르다.

### 4.4 뿌리(seeds) 고르기

| 가닥 경계 상태 | seeds | 비고 |
|----------------|-------|------|
| 경계 루프 1개 (**이 데이터 전부**) | 그 루프의 정점 | `Root = Open end` (기본) |
| 경계 루프 2개 (양끝 열린 튜브) | `Root` 규칙으로 고른 루프 | 다른 루프가 자연히 마지막 링 |
| 경계 0개 (닫힌 튜브) | **2단계 BFS**: 임의 정점 → 가장 먼 A → A 에서 가장 먼 B. A · B 중 `Root` 규칙으로 하나 | 그 정점 하나가 seeds |
| 경계 3개 이상 (구멍) | 가장 큰 루프(또는 `Root` 규칙) + **경고** | 결과는 만들되 로그에 이름 |

`Root` 콤보: `Open end`(기본) / `Highest Y` / `Lowest Y` / `Highest X` / `Lowest X` / `Highest Z` / `Lowest Z`.
`Open end` 인데 열린 끝이 2개 이상이거나 0개면 **`Highest Y` 로 대체**하고 로그에 남긴다.
(만든 뒤 방향을 바꾸고 싶으면 기존 `Create > From Edges` 의 Reverse Direction 을 쓰면 된다 — 같은 창)

### 4.5 가지(branch) 감지

한 링(또는 bin)의 정점이 **링 안 엣지로 이어 봤을 때 2개 이상의 덩어리**면 그 가닥은 갈라진 것이다.
v1 은 **가장 큰 덩어리만 이어 본 줄기 커브를 만들고** 경고(`branched`)로 이름을 남긴다. 가지별 커브는 v2(§11).
이 데이터에는 가지가 없다(Houdini 가 쪼갠 class 146 · 147 은 0.14 cm 짜리 잡음 조각).

### 4.6 `Auto` 판정

`Method = Auto`(기본)는 가닥마다:
- 4각형 면 비율 ≥ 0.8 **이고** 경계 루프가 1~2개 → `Rings`
- 그 밖 → `Geodesic`

판정 결과는 Analyze 요약에 집계해 보여준다(`Rings 148 · Geodesic 0`).

---

## 5. 기능 명세

### 5.1 입력

- 리스트(공용 TSL `JUN_mod_tsl_qt_v01`, 라벨 `Hair meshes`)에 메시 트랜스폼 / 그룹을 담는다.
- `Include child meshes`(기본 **켬**): 담은 노드 아래의 메시를 모두 모은다 — 이 데이터는 메시 아래 메시 계층이고
  그룹(`LUN_Hair_grp1`) 하나만 담아도 되게 한다. `listRelatives(ad=True, type="mesh", f=True)` + `noIntermediate`.
- 같은 셰이프가 두 번 모이면(그룹과 그 자식을 함께 담음) 한 번만 처리.
- 메시 하나에 shell 이 여러 개면 **shell 마다 커브 하나**(Houdini connectivity 와 같음).
- 점 위치는 **월드**(`MFnMesh.getPoints(kWorld)`) — 부모가 움직여 있어도 결과는 월드에서 맞다.

### 5.2 필터 (요구 4)

| 옵션 | 기본 | 판정 시점 | 기준 |
|------|------|-----------|------|
| `Skip meshes smaller than` | 켬, **1.0** | 중심선 계산 **전** | shell 의 월드 바운딩 박스 **대각선** |
| `Skip curves shorter than` | 켬, **1.0** | 스무딩 · 다듬기 **후**, 리샘플 전 | 중심선 꺾은선 **길이** |
| (내부, 옵션 아님) | — | 전 | 정점 < 4 또는 링/bin < 2 → `degenerate` |

- 값은 **씬 길이 단위**(UI 단위). 코어는 내부 단위(cm)로 바꿔 쓴다: `om.MDistance.uiToInternal(v)`.
- 기본 1.0 은 이 데이터에서 퇴화 조각 1개만 거른다(가장 짧은 실제 가닥: 대각선 4.18, 중심선 4.07).
- 걸러진 shell 은 이유와 함께 리포트에 남고, `Select Skipped` 로 선택할 수 있다.

### 5.3 모양

| 옵션 | 기본 | 동작 |
|------|------|------|
| `Method` | `Auto` | `Auto` / `Rings` / `Geodesic` (§4.2 ~ 4.6) |
| `Slices` | 30 | Geodesic 의 bin 수 (Rings 에선 비활성) |
| `Root` | `Open end` | §4.4 |
| `Smooth Iterations` | 10 | 끝점 고정 라플라시안: `p[i] = (1-s)·p[i] + s·(p[i-1]+p[i+1])/2`, 0 = 끄기 |
| `Smooth Strength` | 0.5 | 위 식의 `s` (0 ~ 1) |
| `Trim Root` / `Trim Tip` | 0 / 0 | 뿌리 · 끝에서 호 길이만큼 잘라냄(씬 단위). 남는 길이가 0 이하면 `trimmed_out` 으로 건너뜀 |

### 5.4 출력

| 옵션 | 기본 | 동작 |
|------|------|------|
| `Points` | `Count` | `Count` = 호 길이 균등 N 점 / `Spacing` = 간격 d 로 균등(끝점 포함, 마지막 간격은 맞춰 늘림) / `Per Ring` = 링(bin) 중심점 그대로 |
| `Count` | **10** | 2 이상. 리깅에서 가닥당 조인트 수와 같게 쓰는 값 |
| `Spacing` | 1.0 | 씬 단위 |
| `Degree` | **1 Linear** | 1 = CV 가 곧 계산한 점(조인트를 CV 에 맞추는 흐름에 맞음) / 3 = 그 점들을 **지나는** 큐빅(`cmds.curve(ep=...)`) |
| `Name` | `{mesh}_crv` | `{mesh}` = 메시 트랜스폼 짧은 이름(네임스페이스 제거). shell 이 여러 개면 `_s01`, `_s02` … 를 붙인다 |
| `Group` | 켬, `hairCurves_grp` | 만든 커브를 이 그룹 아래로(없으면 만든다, 있으면 그 아래 추가) |
| `Add source attribute` | 켬 | 커브 트랜스폼에 문자열 어트리뷰트 `hairSourceMesh` = 원본 메시 긴 이름 (나중에 짝 찾기용) |

- **방향**: 언제나 cv[0] = 뿌리(seeds 쪽).
- 커브는 **히스토리 없는 정적 커브**(메시를 따라 움직이지 않음). 리깅 셋업 단계용.
- Degree 1 + `Count N` 이면 CV N 개, 노트 `0, 1, …, N-1`(`cmds.curve(d=1, p=…)` 기본) → `Edit > Joints` 에서 Count N,
  Spacing **`Param`** 으로 만들면 **조인트 i 가 정확히 cv[i] 위**(§8 시험 16). `Length` 로도 거의 같지만 정확하진 않다 —
  CV 는 *스무딩된 꺾은선* 위에서 호 길이 균등으로 찍었고, 새 커브의 구간 길이는 그 사이 **현(chord)** 이라 미세하게 다르다.
  그래서 `Send to Joints` 는 Joints 탭의 Spacing 을 `Param` 으로 맞춰 준다.

### 5.5 버튼

| 버튼 | 동작 |
|------|------|
| `Analyze` | 씬을 바꾸지 않고 전부 계산만 → 요약 로그: 가닥 수 · 만들 커브 수 · 필터로 뺀 수(이유별) · 엔진별 수 · 경고(가지, 루트 대체, 구멍) · 길이 최소/중앙/최대 · 소요 시간 |
| `Create Curves` | 계산 + 커브 생성. **undo 한 스텝**(`Framework.core.maya_undo.undo_chunk`) |
| `Select Skipped` | 마지막 Analyze/Create 에서 걸러진 메시를 선택 (UUID 로 기억 — 이름이 바뀌어도) |
| `Send to Joints` | 마지막 Create 로 만든 커브를 `Edit > Joints` 리스트에 채우고 그 탭으로 이동. Points 가 `Count` 면 Joints 의 Count 칸에 같은 값, Spacing 은 `Param`(아래 메모) |

### 5.6 리포트 / 로그 (UI 문자열 영어)

```
[Hair] 149 shells from 149 meshes - 148 curves, 1 skipped (0.38s)
[Hair]   Skipped (smaller than 1.0): LUN_hair_n_03_12
[Hair]   Method: Rings 148, Geodesic 0
[Hair]   Length: min 4.07 / median 13.11 / max 24.30
[Hair] WARNING  Root fallback (no single open end -> Highest Y): ...
```

경고 · 건너뜀은 공용 로그 레벨 색(`JUN_mod_log_qt_v01`)을 쓴다. 목록이 길면 앞 10개 + `... and N more`.

---

## 6. 구조

```
tools/A00400_CurveTool/
├── app/core/hair_curve_manager.py     # 신규 — 코어 (아래)
├── app/ui/hair_tab.py                 # 신규 — From Hair 탭 위젯 (controls_tab.py / replace_tab.py 와 같은 분리 방식)
├── app/ui/main_window.py              # CREATE_PAGES 에 한 줄 + _build_hair_tab + Send to Joints 연결
├── app/config/version.py              # 01.32
├── CHANGELOG.md
└── tests/test_hair_curve.py           # 신규 — mayapy 오프스크린 시험
docs/A00400_CurveTool.md               # From Hair 절 추가
```

툴 간 import 금지(릴리즈 빌더 규칙) — 다른 툴 코어를 쓰지 않는다. Framework 만 쓴다.

### 6.1 코어 — `hair_curve_manager.py`

**순수 계산부(maya 비의존)** 와 **마야부**를 한 파일 안에서 나눈다. 순수 계산부는 마야 없이(hython · 일반 파이썬) 시험할 수 있어야 한다.
numpy 는 쓰지 않는다(시제작 순수 파이썬 0.47 초로 충분, Maya 2023 호환 걱정 없음).

```python
# ---- 상수
METHOD_AUTO, METHOD_RINGS, METHOD_GEODESIC = "auto", "rings", "geodesic"
ROOT_OPEN_END = "open_end"; ROOT_AXIS = {"+y": (1, +1), "-y": (1, -1), "+x": (0, +1), ...}
POINTS_COUNT, POINTS_SPACING, POINTS_PER_RING = "count", "spacing", "per_ring"
REASON_SMALL, REASON_SHORT, REASON_DEGENERATE, REASON_TRIMMED = ...
QUAD_RATIO_AUTO = 0.8

class HairOptions:            # 모든 옵션 (UI → 코어). 길이 값은 내부 단위(cm)로 들어온다
class ShellResult:            # node, shell_index, points(list[tuple]) | None, reason, method, warnings(list), length, diag
class HairReport:             # results, curves(생성된 이름), elapsed, summary_lines()

# ---- 순수 계산 (입력: points = [(x,y,z)...], faces = [[v...], ...])
def split_shells(num_points, faces) -> list[list[int]]          # union-find, 면 인덱스 묶음
def shell_topology(faces, face_ids) -> (adj: dict[int,set], boundary_loops: list[list[int]], quad_ratio)
def bbox_diagonal(points, verts) -> float
def pick_seeds(points, adj, loops, root) -> (seeds: list[int], warnings)
def levels_rings(adj, seeds) -> list[list[int]]                 # BFS 단계별 정점
def levels_geodesic(points, adj, seeds, slices) -> list[list[int]]
def split_level_components(adj, verts) -> list[list[int]]        # 가지 감지 (§4.5)
def level_centroids(points, levels) -> list[tuple]
def smooth_polyline(pts, iterations, strength) -> list[tuple]    # 끝점 고정
def polyline_length(pts) -> float
def trim_polyline(pts, root_len, tip_len) -> list[tuple] | None
def resample_polyline(pts, mode, count, spacing) -> list[tuple]  # 호 길이 균등
def compute_shell(points, faces, face_ids, opts) -> ShellResult  # 위 함수들을 엮는 한 가닥 처리 + 필터

# ---- 마야
def collect_meshes(nodes, include_children=True) -> list[str]    # 메시 셰이프 long name, 중복 제거
def read_mesh(shape) -> (points, faces)                         # om2: getPoints(kWorld) + getVertices()
def analyze(nodes, opts, progress=None) -> HairReport            # 씬 무변경
def create_curves(nodes, opts, progress=None) -> HairReport      # analyze + 생성 (undo_chunk 하나)
```

**의사코드 — `compute_shell`**

```python
def compute_shell(points, faces, face_ids, opts):
    adj, loops, quad_ratio = shell_topology(faces, face_ids)
    verts = list(adj)
    if len(verts) < 4: return skip(REASON_DEGENERATE)
    diag = bbox_diagonal(points, verts)
    if opts.min_size_on and diag < opts.min_size: return skip(REASON_SMALL, diag=diag)
    method = opts.method
    if method == METHOD_AUTO:
        method = METHOD_RINGS if (quad_ratio >= QUAD_RATIO_AUTO and 1 <= len(loops) <= 2) else METHOD_GEODESIC
    seeds, warns = pick_seeds(points, adj, loops, opts.root)
    levels = levels_rings(adj, seeds) if method == METHOD_RINGS else levels_geodesic(points, adj, seeds, opts.slices)
    levels, branched = keep_main_trunk(adj, levels)         # split_level_components 사용, 가지면 경고
    pts = level_centroids(points, levels)
    if len(pts) < 2: return skip(REASON_DEGENERATE)
    pts = smooth_polyline(pts, opts.smooth_iter, opts.smooth_strength)
    pts = trim_polyline(pts, opts.trim_root, opts.trim_tip)
    if pts is None: return skip(REASON_TRIMMED)
    length = polyline_length(pts)
    if opts.min_length_on and length < opts.min_length: return skip(REASON_SHORT, length=length)
    if opts.points_mode != POINTS_PER_RING:
        pts = resample_polyline(pts, opts.points_mode, opts.count, opts.spacing)
    return ShellResult(points=pts, method=method, warnings=warns, length=length, diag=diag)
```

**`keep_main_trunk`**: 링마다 덩어리를 나눠, 덩어리가 2개 이상인 링부터는 **직전 링의 중심에 가장 가까운 덩어리**를 따라간다
(그래야 한 가지를 끝까지 탄다). 하나라도 갈라졌으면 `branched` 경고.

**마야부 메모**
- `read_mesh`: `om.MSelectionList().add(shape).getDagPath(0)` → `MFnMesh` → `getPoints(om.MSpace.kWorld)` 를
  `[(p.x, p.y, p.z) ...]` 로 **즉시** 바꾼다(MFn 배열 수명 함정 — 메모 `mfn-cvpositions-lifetime`).
  `getVertices()` → `(counts, connects)` 로 `faces` 를 만든다. **`cmds.xform` · `pointPosition` 을 정점마다 부르지 않는다**(속도).
- 생성: `cmds.curve(d=1, p=pts, n=name)` / 큐빅은 `cmds.curve(d=3, ep=pts, n=name)`. 셰이프 이름은 `{name}Shape` 로 맞춘다.
  가닥 수백 개면 `cmds.curve` 호출 수백 번 — 측정상 문제 없음(아래 §7 목표 안). om2 `MFnNurbsCurve.create` 는 **undo 가 안 돼** 쓰지 않는다.
- 이름 충돌은 마야 자동 번호에 맡기되, 반환 이름을 그대로 리포트에 쓴다(`cmds.curve` 반환값).
- 레퍼런스 메시도 읽기만 하므로 된다.

### 6.2 UI — `hair_tab.py` (`class HairTab(QWidget)`)

`main_window.CREATE_PAGES` 의 `From Points` 다음에 추가:

```python
("From Hair",
 "From Hair - one centerline curve through each hair strand mesh (root -> tip)",
 "_build_hair_tab"),
```

```
┌ Hair meshes ───────────────────────────── [TSL: Add / Remove / Clear / Sort …] ┐
│ [x] Include child meshes                                                      │
├ Centerline ──────────────────────────────────────────────────────────────────┤
│ Method [Auto ▼]   Slices [30]   Root [Open end ▼]                             │
│ Smooth Iterations [10]   Strength [0.50]   Trim Root [0.0]   Trim Tip [0.0]   │
├ Output ──────────────────────────────────────────────────────────────────────┤
│ Points [Count ▼]  Count [10]  Spacing [1.0]   Degree (•) 1 Linear ( ) 3 Cubic │
│ Name [{mesh}_crv]   [x] Group [hairCurves_grp]   [x] Add source attribute     │
├ Filters ─────────────────────────────────────────────────────────────────────┤
│ [x] Skip meshes smaller than [1.0]  (bounding box diagonal)                   │
│ [x] Skip curves shorter than [1.0]  (centerline length)                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ Analyze ] [ Create Curves ]            [ Select Skipped ] [ Send to Joints ] │
└──────────────────────────────────────────────────────────────────────────────┘
```

- 모든 라벨 · 툴팁 · 로그 영어. 주석 · 독스트링 한국어.
- 비활성 규칙: `Slices` 는 Method 가 `Rings` 일 때 끔 / `Count` · `Spacing` 은 Points 모드에 맞는 것만 켬 / 필터 값 칸은 체크 따라.
- 리스트 최소 높이 `list_hint_height=140`(v01.30 과 같은 규칙), 창 높이는 기존 tabFit 이 알아서 맞춘다.
- 옵션 값은 `optionVar`(`A00400_hair_*`)로 기억 — 기존 탭들과 같은 방식인지 `main_window.py` 의 다른 탭 저장 방식을 확인해 맞춘다.
- 가닥이 **20개 이상**이면 공용 진행 팝업 `JUN_mod_progress_qt_v01`(단계: `Reading meshes` 30 / `Computing centerlines` 50 / `Creating curves` 20).
  코어는 `progress(done, total, message)` 콜백만 안다.
- `Send to Joints`: main_window 가 넘겨준 콜백으로 `self.tsl_joints` 를 비우고 커브를 채운 뒤 `Edit > Joints` 탭을 연다
  (HairTab 은 main_window 를 직접 만지지 않는다 — 생성자에서 `on_send_to_joints` 콜백을 받는다).

---

## 7. 성능 목표와 설계

| 단계 | 목표 (149 가닥 · 71,599 정점) | 방법 |
|------|-------------------------------|------|
| 메시 읽기 | < 0.5 초 | 메시당 om2 호출 2번(getPoints, getVertices) |
| 계산 | < 1.0 초 | 순수 파이썬 BFS · 평균 (시제작 0.47 초) |
| 커브 생성 | < 1.0 초 | `cmds.curve` 가닥당 1번 + parent 1번(모아서) |
| **합계** | **< 3 초** (Houdini 71.5 초 대비 20 배 이상) | |

- 그룹 parent 는 커브마다 하지 않고 **마지막에 한 번** `cmds.parent(all_curves, grp)`.
- 진행 팝업 갱신은 공용 위젯이 스로틀한다(마지막 값은 반드시 보낸다 — 메모 `framework-progress-widget`).
- 측정은 시험(§8)에서 `time.perf_counter` 로 단계별 출력.

---

## 8. 검증

### 8.1 `tests/test_hair_curve.py` (mayapy 2024 오프스크린, 기존 `test_ribbon.py` 와 같은 틀)

**합성 메시 (데이터 파일 없이 항상 도는 것)**

| # | 장면 | 기대 |
|---|------|------|
| 1 | `polyCylinder`(높이 10, 축 Y) 위 캡 삭제 + 아래 캡 → 한 점으로 모은 원뿔 끝 | 커브 1개, cv[0] 이 열린 끝 중심(오차 1e-4), 마지막 CV = 극점, 모든 점이 축 위(x,z ≈ 0) |
| 2 | 1 을 S 자로 구부림(`nonLinear bend` 후 히스토리 삭제) | 커브 점이 각 링 중심과 일치(Per Ring, Smooth 0) |
| 3 | 양끝 열린 실린더 | Root `Open end` → 대체 경고 + `Highest Y` 끝이 cv[0] |
| 4 | 양끝 닫힌 실린더 | 경계 0 → 2단계 BFS, 커브 1개 |
| 5 | 한 메시에 실린더 2개 combine | 커브 2개, 이름 `_s01` `_s02` |
| 6 | 크기 0.5 실린더 + 기본 필터 | `small` 로 건너뜀, Select Skipped 가 그 메시를 선택 |
| 7 | 길이 필터: 짧은 가닥 | `short` 로 건너뜀 |
| 8 | `Count 10` | CV 10 개, 이웃 CV 간격 표준편차 / 평균 < 1e-3 |
| 9 | `Spacing 1.0` | 간격 ≈ 1.0 (마지막 간격 포함 ±1e-3 비율) |
| 10 | Degree 3 | 커브가 계산한 점을 지난다(`closestPoint` 거리 < 1e-3) |
| 11 | 그룹 + 자식 메시(`Include child meshes`) | 그룹만 담아도 자식 메시 모두 처리, 중복 없음 |
| 12 | 부모 트랜스폼 이동 · 회전 · 스케일 | 월드 결과 동일 |
| 13 | 삼각화한 실린더 + Auto | Geodesic 로 판정, 커브가 축 근처(평균 편차 < 반지름의 10 %) |
| 14 | Y 갈라진 메시(실린더 3개를 이어 붙임) | `branched` 경고 + 줄기 커브 1개 |
| 15 | undo / redo | Create 한 번 = undo 한 스텝으로 커브 · 그룹 모두 사라짐, redo 복원 |
| 16 | Send to Joints → `build_joints_on_curves(count=10, spacing=SPACING_PARAM)` | 조인트 i 월드 위치 == cv[i] (오차 1e-4). `SPACING_LENGTH` 는 오차만 출력(합격 조건 아님) |
| 17 | UI 오프스크린 | 탭 존재, 버튼 클릭 → 로그 줄, 비활성 규칙 |
| 18 | 이름이 바뀐 뒤 Select Skipped | UUID 로 찾아 선택 |

**실데이터 골든 (파일이 있을 때만, 없으면 SKIP)**

`0010_src/hair_01.fbx` 를 임포트하고 `0020_out/hair_02.abc`(Houdini 결과, `AbcImport`)를 함께 불러 대조:

| 항목 | 합격 기준 (시제작 실측 기준 여유) |
|------|-----------------------------------|
| 커브 수 | **148** (149 가닥 − 퇴화 1) |
| 건너뜀 | 1 개, 이유 `degenerate` 또는 `small` |
| 방향 | 열린 끝 Y > 극점 Y 인 가닥 146 개에서 cv[0].y > cv[-1].y |
| 편차 | 각 커브 → 가장 가까운 Houdini 커브까지 평균 거리: 중앙값 ≤ **0.3 cm**, p95 ≤ **0.5 cm** (시제작 0.15 / 0.23) |
| 시간 | Analyze + Create **< 3 초**, 단계별 시간 출력 |

> 골든 대조는 Houdini 결과가 "정답" 이라는 뜻이 아니다 — Houdini 는 델타머시를 먼저 걸어 메시가 약간 수축됐고 끝이 짧다.
> 같은 자리를 지나는 커브인지 확인하는 용도.

### 8.2 GUI 확인 (사용자)

마야 2024 에서 `__dragDrop_A00400.py` → `Create > From Hair` → `hair_01.fbx` 그룹을 담고 Analyze → Create →
`Send to Joints` → Joints 탭에서 Create. 커브가 가닥 가운데를 지나고 뿌리에서 시작하는지 눈으로 본다.

---

## 9. 작업 순서 (체크리스트)

1. [ ] `hair_curve_manager.py` 순수 계산부 + 합성 메시 시험 1 ~ 10, 13, 14 (먼저 mayapy 로 메시만 만들어 `read_mesh` → `compute_shell`)
2. [ ] 마야부(`collect_meshes` · `read_mesh` · `analyze` · `create_curves`) + 시험 11, 12, 15, 18
3. [ ] 실데이터 골든 시험 → 편차 · 시간 확인. 기준 미달이면 Smooth 기본값부터 조정(§10 위험 1)
4. [ ] `hair_tab.py` UI + `main_window` 등록 + 진행 팝업 + optionVar
5. [ ] `Send to Joints` + 시험 16, 17
6. [ ] 버전 · 문서: `version.py` 01.32 · `CHANGELOG.md` · `docs/A00400_CurveTool.md` 의 Create 절에 From Hair 사용법
   (옵션 표 + "Houdini 단계를 대체" 한 줄 + 조인트 흐름) · `docs/WORKLOG.md` · 포트폴리오 EN/KR(메모 `update-portfolio-on-tool-work`) ·
   메모 `wip-a00400-curvetool` 에 한 단락
7. [ ] 커밋(로컬). 푸시는 사용자가 요청할 때만

---

## 10. 위험 · 열린 질문

| # | 위험 | 대응 |
|---|------|------|
| 1 | 링 중심점이 **끝 팬 근처에서 한쪽으로 쏠림**(극점 근처 링 크기가 변하는 26 가닥) | 스무딩(10회)으로 흡수 — 골든 p95 로 확인. 부족하면 링 평균을 **엣지 길이 가중 평균**(링 둘레 위 균등)으로 바꾼다 |
| 2 | 다른 캐릭터의 헤어가 **카드형(납작한 띠)** 이면 경계가 띠 둘레 전체 하나 → Rings 가 폭 방향으로 링을 만든다 | Auto 판정에 "경계 루프 길이 / 전체 정점" 비율이 크면 Geodesic + 2단계 BFS 끝점 사용을 추가. **이 데이터엔 없음** — v1 은 Method 를 직접 고르게 두고 Analyze 경고만 |
| 3 | 뿌리가 아래인 가닥(이 데이터 2개 — 위로 뻗은 가닥 추정) | `Open end` 가 맞는 동작(열린 끝 = 두피). 축 규칙으로 바꾸면 오히려 틀린다 — 툴팁에 명시 |
| 4 | 커브 CV 수를 가닥 길이에 비례시키고 싶을 수 있음 | `Spacing` 모드가 그 용도. 조인트 개수가 가닥마다 달라지는 점은 Joints 탭이 커브마다 같은 Count 를 쓰므로 v1 에선 **Count 모드 권장**으로 안내 |
| 5 | 사용자가 계속 Houdini 처럼 "메시를 먼저 델타머시" 한 결과를 원할 수 있음 | 필요하면 v2 에 `Pre-smooth mesh`(마야 `deltaMush` 를 임시로 걸고 읽은 뒤 삭제) |

---

## 11. 범위 밖 (v2 후보)

- 가지마다 커브(갈라진 가닥) — `polycut` 처럼 가지점에서 나눠 커브 여러 개.
- 메시를 따라 움직이는 커브(히스토리/디포머 연결).
- 카드형 헤어 전용 판정(§10-2).
- 가닥 길이에 비례한 조인트 수(Joints 탭 쪽 기능).

---

## 12. 구현 결과 · 계획과 달라진 점 (2026-11-09)

| 항목 | 계획 | 구현 | 이유 |
|------|------|------|------|
| 실데이터 시간 | < 3 초 | Analyze 0.49 + Create 0.60 = **1.1 초** | — |
| 골든 편차 | 중앙값 ≤ 0.3 · p95 ≤ 0.5 cm | **0.11 / 0.15 cm** | — |
| 가지 판정 | 링이 둘 이상 덩어리면 가지 | **두 번째로 긴 덩어리가 `max(3, 단계 10 %)` 이상**일 때만 | LUN `n_05_05` 는 끝 단계에 이웃 아닌 정점 2개가 남아 거짓 가지 경고가 났다. 판정은 "레벨 k 이상 정점 집합" 을 바깥부터 union-find 로 합치며 덩어리 길이를 센다 — O(V) |
| 닫힌 메시 끝 찾기 | 2단계 **BFS(홉)** | 2단계 **측지 스윕, 이웃 = 같은 면의 정점(면 대각선 포함)** | 홉 · 엣지 길이 가중 모두 쿼드 격자에서 둘레를 도는 경로를 과대평가 → 극점 대신 맞은편 링 정점이 "가장 먼 끝". Geodesic 구간도 같은 거리 사용 |
| Spacing | 간격 d, 마지막 간격을 맞춰 늘림 | **구간 수 = round(L / d)** 인 균등 간격(가장 가까운 균등) | 모든 간격이 같아야 조인트 연동이 단순 |
| 옵션 기억 | optionVar | **저장 안 함** | 이 툴의 다른 탭이 저장하지 않는다(§6.2 "기존 방식에 맞춘다") |
| `Send to Joints` | Count 복사 | Count 복사 + **By parameter**, Count 모드 + Degree 1 일 때만 Count 를 넘김 | §5.4 |
| numpy | 안 씀 | 안 씀 | Maya 2023 mayapy 엔 numpy 가 없다(포트폴리오 Ribbon 항목과 같은 제약) |

파일: `app/core/hair_curve_manager.py`(순수 계산부 + 마야부), `app/ui/hair_tab.py`, `main_window.py`(등록 · `_hair_to_joints`),
`tests/test_hair_curve.py`.

---

## 부록 A. 분석 재현 방법

hip 은 **ASCII cpio** 다. cpio 명령이 없어도 파이썬으로 풀린다(헤더 76 바이트, 8진수 `namesize`(59:65) · `filesize`(65:76)).
노드별 `*.init`(타입) · `*.def`(입력 · 플래그) · `*.parm`(값) 이 나온다.

hython(`C:/Program Files/Side Effects Software/Houdini 21.0.700/bin/hython.exe`)으로 실측:

```python
hou.hipFile.load(hip, suppress_save_prompt=True, ignore_load_warnings=True)
sk = hou.node('/obj/geo1/straight_skeleton_3d1'); sk.allowEditingOfContents()   # 잠긴 HDA 내부 보기
geo = hou.node('/obj/geo1/foreach_end1').geometry()                               # 루프 쿡(71.5 초)
```

시제작(링 중심점) 핵심 — 위 §4.2 의사코드 그대로, `hou.node('/obj/geo1/file1').geometry()` 의 점 · 면으로 돌렸다.
