---
title: A00420_Wrapper 사용법
aliases: [Wrapper, A00420, curve wrap, 커브 래핑]
tags: [maya-python, tool-guide, wrap, retopology, tps, rbf, facial]
updated: 2026-08-10
---

# A00420_Wrapper 사용법

Maya 안에서 도는 **래핑** PySide 툴이다(arch B, in-Maya).

**토폴로지가 다른 두 메시** A(소스) / B(타깃) 에 대해, **A 의 토폴로지는 그대로 두고 형태만 B 와
똑같아지도록** A 의 정점을 옮긴다. 그 대응의 근거가 되는 가이드가 **커브 쌍**이다.

Wrap3D 로 치면 `SelectPointPairs`(가이드) + `Wrapping`(래핑) 을 한 창에 넣은 것이고, 다른 점은
가이드가 낱개 포인트가 아니라 **커브**라는 것이다. 얼굴이면 입술·눈두덩·코·턱선처럼 특징이 "선"으로
잡히므로, 점을 수십 개 찍는 대신 커브 몇 개만 그려도 대응이 잡힌다.

- **버전**: `app/config/version.py` (v01.01)
- **설치**: `__dragDrop_A00420.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **Wrapper** →
  `tools.A00420_Wrapper.run(True)`
- **필요**: `numpy` (Maya 2022+ 내장. 없으면 창은 뜨되 Wrap 버튼이 비활성화되고 이유를 로그에 적는다)
- **관련 툴**: 가이드 커브 만들기는 `A00400_CurveTool` 을 그대로 재사용(**Curve from Edges** 버튼).
  정점 쓰기 방식(`shape.pnts` 구간 setAttr)은 `A00380_MeshTool` 과 같다.

---

## 1. 화면 구성

```
┌ Wrapper ────────────────────────────────────────────┐
│ Help                                                │
│ ┌ Meshes ─────────────────────────────────────────┐ │
│ │ Source [ head_lowRes        ] [<<] [Sel]        │ │  ← 변형될 메시
│ │ Target [ head_scan          ] [<<] [Sel]        │ │  ← 맞출 메시
│ └─────────────────────────────────────────────────┘ │
│ ┌ Guide Pairs (source curve -> target curve) ─────┐ │
│ │ On │ Source     │ Target     │ Flip │ Info      │ │
│ │ [x]│ lip_src    │ lip_tgt    │ [ ]  │ 24 samples│ │
│ │ [x]│ eyeL_src   │ eyeL_tgt   │ [ ]  │ closed,   │ │
│ │ [x]│ nose_src   │ nose_tgt   │ [ ]  │  offset 7 │ │
│ │ [ Add Curve Pair ] [ Add Point Pair ]           │ │
│ │ [ Curve from Edges ][ Swap ][ Remove ][ Clear ] │ │
│ │ [ Show Guide Links ] [ Clear Links ]            │ │
│ └─────────────────────────────────────────────────┘ │
│ ▼ Guide Settings                                    │
│     Samples per curve [ 24 ]                        │
│     [x] Auto align direction / start point          │
│     [x] Snap guide samples to the mesh surface      │
│ ▼ Wrap Settings                                     │
│     Smoothness         [ 0.000 ]                    │
│     Projection steps   [ 5 ]                        │
│     Projection strength[ 1.00 ]                     │
│     Relax              [ 0.30 ]  Relax steps [ 2 ]  │
│     Max distance       [ 0.000 ]                    │
│     Normal angle limit [ 90.0 ]                     │
│ ┌ Output ─────────────────────────────────────────┐ │
│ │ (o) New mesh (duplicate)  ( ) In place          │ │
│ │ Suffix [ _wrap ]   Amount [ 1.00 ]              │ │
│ └─────────────────────────────────────────────────┘ │
│ [                    Wrap                         ] │
│ [ log ... ]                                         │
└─────────────────────────────────────────────────────┘
```

---

## 2. 동작 원리 (왜 2 단계인가)

### 2-1. 커브 쌍 → 대응 포인트

짝지은 두 커브를 **같은 개수로 호 길이 등간격 샘플링**해서, 소스 커브의 i 번째 점과 타깃 커브의
i 번째 점을 대응시킨다. 커브 1개 = 대응 포인트 24개(기본)다.

> **Snap guide samples to the mesh surface** 를 켜 두면 샘플을 각자의 메시 표면 최근접점으로 당긴다.
> 커브를 눈대중으로 그려 표면에서 살짝 떠 있어도 대응이 "표면 → 표면"이 된다.

### 2-2. Warp — Thin Plate Spline

대응 포인트 쌍으로 **TPS**(3D 커널 `phi(r) = r`)를 푼다. 컨트롤 포인트를 **정확히 통과**하면서,
그 사이 공간은 "휘는 에너지가 최소"가 되도록 부드럽게 채우는 변형이다.

```
f(x) = Σ w_i · |x − p_i| + a0 + A·x
```

여기서 입술·눈·코 같은 **특징 대응**이 맞고, 두 얼굴의 큰 비율 차이(길이·폭·각도)가 거의 사라진다.
다만 TPS 는 컨트롤 포인트 사이를 보간할 뿐이라, **가이드가 없는 영역(볼·이마·뒤통수)은 타깃 표면에
정확히 붙지 않는다.**

### 2-3. Project — 표면 투영 (비강체 ICP)

워프된 정점을 타깃 표면의 최근접점으로 당긴다. 반복마다 **변위(displacement)** 를 라플라시안으로
스무딩해서, 표면에 붙이면서도 삼각형이 뒤집히거나 스파이크가 생기지 않게 한다.

> **투영만으로는 왜 안 되나**: 최근접점만 보면 "윗입술 위 정점"이 아랫입술로 끌려갈 수 있다.
> 워프로 특징을 먼저 맞춰 둬야 최근접점이 **올바른 대응**이 된다. 그래서 두 단계가 한 짝이다.

---

## 3. 사용법

### 3-1. 준비 — 가이드 커브 그리기

소스 메시와 타깃 메시에 **같은 부위를 가리키는 커브**를 각각 그린다.

- 메시 엣지 루프를 따라 만들 거라면 엣지를 고르고 **Curve from Edges** (내부적으로 `A00400_CurveTool`).
- 손으로 그려도 된다. 커브가 표면에서 조금 떠 있어도 **Snap** 옵션이 잡아 준다.
- 커브의 **cv 개수·degree 는 서로 달라도 된다.** 샘플링으로 개수를 맞추기 때문이다.

권장 가이드(얼굴):

| 부위 | 형태 | 비고 |
|------|------|------|
| 입술 바깥 라인 | 닫힌 커브 | 시작점이 달라도 자동 정렬 |
| 눈 라인 (좌/우) | 닫힌 커브 | 좌우를 각각 다른 쌍으로 |
| 코 라인(콧대 + 콧볼) | 열린 커브 | |
| 턱선 · 얼굴 외곽 | 열린 커브 | **바깥 경계를 하나 넣어 주면** 가장자리 왜곡이 준다 |
| 귀 · 헤어라인 | 열린 커브 | 필요할 때 |

> **가이드가 얼굴 한가운데만 몰려 있으면** 바깥 영역은 TPS 가 외삽하느라 크게 벌어진다.
> 커버하려는 범위를 **감싸는** 커브를 최소 하나 넣는 것이 결과에 제일 크게 기여한다.

### 3-2. 메시 지정

1. 변형될 메시를 선택 → **Source** 의 `<<`.
2. 맞출 메시를 선택 → **Target** 의 `<<`.

### 3-3. 가이드 쌍 등록

1. **소스 커브를 먼저, 타깃 커브를 다음에** 선택하고 **Add Curve Pair**.
   - 4·6·8… 개를 한 번에 고르면 `(1↔2), (3↔4), …` 연속 쌍으로 한꺼번에 들어간다.
2. 점 하나로 못 박고 싶은 곳(입꼬리·눈꼬리 등)은 버텍스나 로케이터를 2개 골라 **Add Point Pair**.
3. **거꾸로 넣었으면(타깃 커브를 먼저 골랐으면) 그 행을 선택하고 Swap** — 소스/타깃이 맞바뀐다.
   지우고 다시 넣을 필요가 없고, **선택한 행만** 바뀐다. 행의 **On / Flip 체크는 그대로**,
   **Info** 칸의 이전 방향·시작점 정보만 지워진다(다시 샘플링해야 유효하므로).
   선택한 행이 없으면 아무것도 하지 않는다 — 전체를 조용히 뒤집는 쪽이 더 위험하기 때문이다.
4. 잘못 넣은 행은 골라서 **Remove**, 잠깐 빼고 싶으면 **On** 체크를 끈다.

### 3-4. 대응 확인 (권장)

**Show Guide Links** 를 누르면 소스 샘플 i 와 타깃 샘플 i 를 잇는 선이 그려진다.

- 선이 **나란하면** 대응이 맞은 것.
- 선이 **X 자로 꼬여 있으면** 커브 방향이 반대인 것 → **Auto align** 을 켜거나, 끈 상태라면 **Flip** 체크.
- 닫힌 커브가 **한 바퀴 비틀려 있으면** 시작점(seam)이 다른 것 → **Auto align** 이 잡는다.
- 빨간 선이 **첫 샘플(시작점)** 이다. 두 커브의 빨간 선이 같은 부위에 있는지 보면 된다.

확인이 끝나면 **Clear Links** 로 지운다.

### 3-5. 설정

**Guide Settings**

| 항목 | 뜻 | 기본 |
|------|-----|------|
| **Samples per curve** | 커브 1개를 몇 점으로 샘플링할지 | 24 |
| **Auto align direction / start point** | 정/역 + (닫힌 커브면) 시작점 N 가지를 모두 시도해 제일 잘 맞는 조합 선택 | on |
| **Snap guide samples to the mesh surface** | 샘플을 각 메시 표면으로 당김 | on |

**Wrap Settings**

| 항목 | 뜻 | 기본 |
|------|-----|------|
| **Smoothness** | TPS 정규화. 0 = 가이드를 정확히 통과. 두 커브 모양이 많이 다르거나 결과가 울렁이면 올린다 | 0.0 |
| **Projection steps** | 표면 투영 반복 횟수. **0 이면 워프만** 한다 | 5 |
| **Projection strength** | 반복 1회당 최근접점 쪽으로 가는 비율 | 1.0 |
| **Relax** | 투영 변위에 걸리는 라플라시안 스무딩 세기. 높이면 고르지만 덜 붙는다 | 0.3 |
| **Relax steps** | 스무딩 반복 | 2 |
| **Max distance** | 타깃 표면이 이보다 멀면 그 정점은 **안 옮긴다**. 0 = 제한 없음 | 0.0 |
| **Normal angle limit** | 타깃 면의 노멀이 이 각도 이상 어긋나면 건너뛴다. 바깥 피부가 안쪽(구강 등)에 붙는 것을 막는다. 0 = 검사 안 함 | 90 |

**Output**

| 항목 | 뜻 |
|------|-----|
| **New mesh (duplicate)** | 소스를 복제하고 히스토리를 지운 뒤 결과를 쓴다(원본 보존, 기본) |
| **In place** | 소스 메시의 정점을 직접 옮긴다 |
| **Suffix** | 복제 결과 이름 접미사 (기본 `_wrap`) |
| **Amount** | 원본(0) ↔ 결과(1) 블렌드 |

### 3-6. Wrap

**Wrap** 을 누르면 로그에 다음이 찍힌다.

```
Warp done. 4 guide(s) -> 124 control point(s), fit error avg 0.00000 / max 0.00000.
  projection 1/5  mean gap 0.01746
  ...
Projection done. 5 iteration(s), 3542 vertex(es) snapped, 0 skipped, mean gap 0.00011.
Wrapped 3542 vertex(es) -> head_lowRes_wrap
```

- **fit error** — 가이드 대응이 목표에 얼마나 정확히 갔는지. Smoothness 0 이면 ~0.
- **mean gap** — 결과 메시가 타깃 표면에서 평균 얼마나 떨어져 있는지. 반복이 돌수록 0 에 수렴해야 정상.
- **skipped** — Max distance / Normal angle limit 때문에 안 옮긴 정점 수.

전체가 **한 번의 undo** 로 묶인다.

---

## 4. 자주 겪는 문제

| 증상 | 원인 | 대처 |
|------|------|------|
| 소스 메시가 엉뚱하게 반대로 끌려간다 | 커브를 **타깃 → 소스** 순으로 골라 등록했다 | 그 행을 선택하고 **Swap** |
| 결과가 통째로 뒤틀린다 | 커브 방향이 반대 | **Show Guide Links** 로 확인 → **Auto align** 켜기 |
| 눈/입 루프가 한 바퀴 돌아간다 | 닫힌 커브의 시작점(seam)이 다름 | **Auto align** 이 잡는다. 꺼져 있으면 켠다 |
| 얼굴 바깥(귀·뒤통수)이 크게 벌어진다 | 그 영역에 가이드가 없어 TPS 가 외삽 | **외곽을 감싸는 가이드**를 하나 추가 |
| 얇은 부위가 안쪽 면에 달라붙는다 | 최근접점이 반대쪽 면 | **Normal angle limit** 를 60~80 으로 낮춘다 |
| 표면이 자글자글하다 | 투영이 세다 | **Relax** 를 올리거나 **Projection strength** 를 낮춘다 |
| 결과가 울렁인다 | 가이드 커브 두 개가 서로 모순되는 대응을 요구 | **Smoothness** 를 0.01~0.1 로 올린다 |
| `Wrap` 이 비활성 | numpy 없음 | Maya 2022+ 를 쓰거나 numpy 를 설치 |

---

## 5. 구조

```
A00420_Wrapper/
├── __init__.py                 # run() 노출
├── launch.py                   # DEV reload -> MainWindow -> ThemeManager
├── __dragDrop_A00420.py        # 셸프 버튼 설치
├── icon/A00420_Wrapper.svg|png
├── CHANGELOG.md
└── app/
    ├── config/version.py
    ├── core/                   # UI 비의존
    │   ├── mesh_utils.py       # 메시 읽기/쓰기, MMeshIntersector 최근접점, 라플라시안
    │   ├── guide_sampler.py    # 커브/포인트 쌍 -> 대응 컨트롤 포인트 (방향·시작점 정렬)
    │   ├── rbf_warp.py         # Thin Plate Spline (numpy 만, maya 비의존)
    │   └── wrap_manager.py     # 파이프라인 (warp -> project -> write) + 가이드 미리보기
    └── ui/main_window.py
```

### 검증하며 확인한 마야 API 함정

- `MMeshIntersector.create(node, matrix)` 에 **월드 행렬을 넘겨도** `getClosestPoint()` 가 돌려주는
  point/normal 은 **오브젝트 공간**이다. → intersector 는 항등으로 만들고, 좌표 변환은 numpy 로
  통째 처리한다(행렬 변환을 파이썬 루프 밖으로).
- 최근접점 20,000 회: `MMeshIntersector` **0.6s** vs `MFnMesh.getClosestPoint(kWorld)` **4.9s** (8 배).
  반복 투영에는 반드시 전자.
- `np.array(MFnMesh.getPoints())` 는 **(N, 4) 동차좌표**다. `[:, :3]` 로 자른다.
- 컨트롤 포인트가 겹치면(커브 끝이 만나거나 가이드가 교차) TPS 행렬이 특이해져 결과가 폭발한다 →
  격자 반올림으로 미리 합친다.
- 마야는 **행벡터 규약**(`p' = p * M`)이라 numpy 에서도 `p @ M[:3,:3] + M[3,:3]` 가 맞다.

### 성능 (mayapy 실측)

| 소스 정점 | 타깃 정점 | 가이드 | 투영 | 총 시간 |
|-----------|-----------|--------|------|---------|
| 3,542 | 8,012 | 4 쌍 (32 샘플) | 8 회 | 0.13 s |
| 32,222 | 39,802 | 3 쌍 (32 샘플) | 8 회 | 0.98 s |
