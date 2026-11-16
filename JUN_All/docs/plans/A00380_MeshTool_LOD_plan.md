# A00380_MeshTool — LOD 탭 계획서 (재생용 저폴리 프록시 메시 빠르게 만들기)

> **작성** 2026-11-16 · 상태: **v01.20 구현 (1~5단계, 7단계 완료)** — 남은 것: 6단계 마야 GUI 실기 · 재바인딩 후 재생 끊김 확인 · Maya 2023 · 대상 Maya 2024
> 실측 스크립트: [`A00380_MeshTool_LOD_probe_bench.py`](A00380_MeshTool_LOD_probe_bench.py) · 시험 [`A00380_MeshTool_LOD_probe_test.py`](A00380_MeshTool_LOD_probe_test.py) (mayapy 로 바로 돌린다)
> 이 문서만 보고 구현할 수 있게 쓴다 — 알고리즘 · 파일 · 함수 · UI · 검증 · 완료 조건까지.

---

## 0. 결론

- **새 탭 `LOD`** 를 A00380 맨 오른쪽(Match 다음)에 둔다. 메시를 고르고 **Build LODs** 한 번이면
  LOD1 ~ LODn(1~5개, 기본 3개) 메시가 그룹으로 생긴다. 바인딩은 하지 않는다.
- 알고리즘은 마야 `polyReduce` 가 아니라 **numpy 로 짠 "그리드 클러스터링 + 셀마다 QEM 대표점"**
  (Lindstrom 2000, out-of-core simplification 방식)을 쓴다. 한 번에 통째로 계산하는 벡터 연산이라
  순차 에지 붕괴(edge collapse)를 하는 `polyReduce` 보다 **5 ~ 18배 빠르다** (2장 실측).
- 대가는 품질 — 손가락 · 옷 겉/안처럼 **얇고 가까운 부분이 붙을 수 있고, 삼각형만 나오고, UV 는 대충** 이다.
  요구사항("UV 일그러져도 됨", "재생 끊김 해결용") 에 맞는 절충이다. 품질이 필요하면 같은 탭에서
  `Method = Quality (polyReduce)` 로 바꿀 수 있게 둔다(느리지만 마야 기본과 같은 결과).
- 스킨된 메시는 **바인드 포즈(orig 셰이프)** 에서 줄인다 → 재바인딩(A00275) 할 때 조인트와 자세가 맞는다.

---

## 1. 배경 · 요구사항

모션캡처 6000 프레임 × 5명 클린업 중, 원본 아바타로 재생하면 **가끔 몇 프레임 멈췄다 재생**된다.
같은 아바타를 저폴리 메시에 바인딩해 재생하면 끊김이 없다 → 재생용 저폴리(LOD) 아바타를 빨리 만드는 툴이 필요하다.

| # | 요구 | 중요도 | 이 계획의 답 |
|---|------|:-----:|--------------|
| R1 | LOD 를 여러 개 (3개면 충분, 5개까지) | 3 | LOD 수 1~5, 기본 3 (5장) |
| R2 | 마야 기본 폴리곤 줄이기보다 빠를 것. 클린업마다 아바타 5개+ | **4** | numpy 클러스터-QEM, 실측 5~18배 (2장) + LOD 간 사전 계산 공유 (4-3) |
| R3 | UV 를 완벽히 재현할 필요 없음 (일그러져도 됨) | — | 버텍스당 대표 UV 하나 (4-5), 끌 수도 있음 |
| R4 | 바인딩 불필요 (A00275 로 다시 리깅) | — | 바인딩 안 함. 대신 재바인딩이 쉽게 바인드 포즈로 만들고 원본을 기록 (6장) |

---

## 2. 실측 (2026-11-16, mayapy 2024, 이 PC)

`polySphere` 를 원본으로, 같은 목표 삼각형 수를 두 방법으로 만들었다.
`polyReduce` 는 속도에 유리하게 `ver=1, kqw=0, uwt=0, cwt=0, ch=False`(사각형 · UV · 색 보존 끔).
클러스터 쪽 시간은 **읽기 + 계산 + 메시 생성** 전부 합친 값이다.

| 원본 삼각형 | 비율 | `polyReduce` | 클러스터-QEM | 배수 |
|-----------:|-----:|------------:|------------:|----:|
| 79,600 | 50 % | 0.75 s | 0.20 s | 3.8× |
| 79,600 | 25 % | 1.06 s | 0.16 s | 6.7× |
| 79,600 | 12.5 % | 1.28 s | 0.14 s | 9.4× |
| 79,600 | 6.25 % | 1.38 s | 0.13 s | 10.6× |
| 79,600 | 3 % | 1.44 s | 0.14 s | 10.0× |
| 319,200 | 50 % | 4.05 s | 0.85 s | 4.7× |
| 319,200 | 25 % | 6.98 s | 0.71 s | 9.8× |
| 319,200 | 12.5 % | 8.51 s | 0.62 s | 13.8× |
| 319,200 | 6.25 % | 8.70 s | 0.61 s | 14.4× |
| 319,200 | 3 % | 9.22 s | 0.52 s | **17.9×** |

- `polyReduce` 는 **많이 줄일수록 느려진다**(붕괴 횟수 ∝ 지운 수). 클러스터는 거의 일정(입력 크기에만 비례).
- 32만 삼각형 아바타 하나에 LOD 3개(50/25/12.5 %): `polyReduce` ≈ 19.5 s, 클러스터 ≈ 2.2 s.
  면 쿼드릭 · 메시 읽기를 LOD 끼리 공유하면(4-3) **≈ 1.3 s** 로 더 준다.
- 목표 삼각형 수 오차: 클러스터 −0.3 ~ −6.6 % (항상 목표 이하). 표시용으로 충분하다.
- 구체는 이상적인 입력이다. **실제 아바타(얇은 부위 · 여러 셸 · 수십 개 메시)로 4단계에서 다시 잰다.**

> 측정 대상 스크립트는 `A00380_MeshTool_LOD_probe_bench.py`. 실행:
> `"C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" A00380_MeshTool_LOD_probe_bench.py`

---

## 3. 방법 선택

| 방법 | 속도 | 품질 | 의존성 | 판단 |
|------|------|------|--------|------|
| 마야 `polyReduce` | 느림 (위 표) | 좋음 (QEM 에지 붕괴, UV 보존) | 없음 | **Quality 모드로만** 남긴다 |
| **numpy 클러스터-QEM** | **빠름** | 보통 (얇은 부위 붙음, 삼각형만) | numpy (Maya 2022+ 내장, 2024 = 2.2.6) | **기본(Fast) 모드** |
| 순수 파이썬 QEM 에지 붕괴 | 매우 느림 (힙 + 순차 루프) | 좋음 | 없음 | 버림 — 언리얼이 빠른 건 C++ 이라서다 |
| 외부 C++ 라이브러리 (`meshoptimizer`, `pyfqmr` 등 pip) | 매우 빠름 | 좋음 | **mayapy 에 pip 설치 필요** | 버림 — 릴리스 배포 · 다른 PC 설치 부담. 나중에 필요하면 "있으면 쓰는" 선택지로만 |

numpy 는 이미 A00275 · A00420 · A00430 이 쓰고 있다. 없으면(가능성 낮음) 탭이 Fast 를 막고 Quality 만 허용한다.

---

## 4. 알고리즘 (Fast = 클러스터-QEM)

입력: 한 메시의 점 `P (N,3)`(오브젝트 공간), 삼각형 `T (F,3)`, 목표 삼각형 수 `target`.
출력: 새 점 `V (M,3)`, 삼각형 `Tri (K,3)`, 그리고 각 출력 삼각형의 **원본 폴리곤 번호**(재질용) · 각 출력 점의 **대표 원본 버텍스**(UV 용).

### 4-1. 사전 계산 (메시당 1번, LOD 수와 무관)

```
P, (tri_counts, tri_verts) = MFnMesh.getPoints(kObject), MFnMesh.getTriangles()
T        = tri_verts.reshape(-1,3)
tri_poly = np.repeat(arange(numPolygons), tri_counts)       # 삼각형 -> 원본 폴리곤
n        = cross(P[T1]-P[T0], P[T2]-P[T0]);  area2 = |n|;  nn = n/area2
plane    = [nn, -dot(nn, P[T0])]                            # (F,4)
Kf       = outer(plane, plane) * area2                       # (F,4,4) 면 쿼드릭, 면적 가중
Kv       = Σ_{면 ∋ v} Kf  (np.add.at 3번)                   # (N,4,4) 버텍스 쿼드릭
vnormal  = Σ_{면 ∋ v} n  (면적 가중) -> 버킷 0..5 (지배 축 · 부호)
bbmin, ext = P.min(0), (P.max(0)-P.min(0)).max()
```

`Kv` 를 미리 만들어 두면 LOD 마다 셀 쿼드릭은 `np.add.at(Q, cid, Kv)` 한 번이다(프로토타입은 면에서 매번 다시 더했다 → 이것만으로 계산 시간 약 1/3).

### 4-2. LOD 하나 만들기

```
def cluster(res):                       # res = 가장 긴 축의 셀 개수
    cell = ext / res
    g    = floor((P - bbmin)/cell)  (int64)
    key  = ((g.x*(res+2) + g.y)*(res+2) + g.z)*6 + bucket      # ★ 노멀 버킷 = 얇은 부위 보호 (4-4)
    uniq, cid = np.unique(key, return_inverse=True)
    tc   = cid[T];  keep = 세 꼭짓점 셀이 모두 다름
    return cid, tc[keep], tri_poly[keep]

res 를 이분 탐색: 남는 삼각형 수 <= target 인 가장 큰 res
  - 시작값 추정 res0 ≈ res_full * sqrt(target/F)  (res_full = 원본이 거의 다 남는 해상도)
  - 상한 ~12 회. 반복 1회 = np.unique 한 번 (32만 삼각형에서 ~30 ms)

Q   = Σ_{v in cell} Kv                                          # (C,4,4)
A, b = Q[:3,:3], -Q[:3,3]
mean = 셀 버텍스 평균
λ    = 1e-3 * trace(A)/3                                         # 평평한 셀 안정화
X    = solve(A + λI, b + λ*mean)                                 # 셀 대표점 = QEM 최소점
X    = 셀 AABB 로 clamp                                          # 튀는 점 방지 (프로토타입에 없음, 추가)
중복 삼각형 제거 (정렬 후 np.unique(axis=0))
쓰인 셀만 남기고 번호 다시 매김 -> V, Tri
```

### 4-3. 속도를 위한 규칙

- **메시 읽기 · `Kf/Kv` · 버킷은 메시당 한 번**, LOD 들이 공유한다. LOD 1~5 는 4-2 만 반복.
- LOD 간 이분 탐색 범위는 앞 LOD 의 res 를 상한으로 쓴다(뒤로 갈수록 res 가 작다).
- 마야 쪽 쓰기는 **`MFnMesh.create` 한 번**(+ UV 한 번, 재질은 범위 문자열). 버텍스별 `cmds` 호출 금지.
- `MPointArray` 는 리스트 컴프리헨션보다 `setLength` + 인덱스 대입이 빠르다(A00610 `maya_build.py` 방식).
- 진행률 팝업은 메시 단위로만 갱신(LOD 단위 스로틀 없이, 마지막 값은 반드시 보낸다 — [[framework-progress-widget]] 메모).

### 4-4. 얇은 부위 보호 (노멀 버킷)

그리드 클러스터링은 셀 하나에 든 버텍스를 무조건 합친다 → 셀이 커지면 **손가락끼리, 옷 겉면과 안감, 입술 위아래**가 붙는다.
`key` 에 버텍스 노멀의 지배 축 · 부호(6 버킷)를 넣으면 **반대쪽을 보는 면은 같은 셀이어도 따로 남는다**.
대가: 버킷 경계에서 작은 틈(crack)이 생길 수 있다 → 재생용 프록시엔 문제없다. 옵션 `Keep thin parts` (기본 ON).

추가로 **메시 단위로 따로 처리**하므로 서로 다른 메시(몸 · 옷 · 머리카락)는 절대 붙지 않는다.

### 4-5. UV (대충)

- 원본에서 **버텍스당 UV 하나**: 각 버텍스의 첫 face-vertex UV (`getAssignedUVs` → 첫 등장값).
- LOD 의 각 점(셀)은 **대표점 X 에 가장 가까운 셀 안 원본 버텍스**의 UV 를 받는다(셀 안에서 argmin, 벡터화).
- 결과: UV 셸 경계(seam)에서 텍스처가 늘어나 보인다 — R3 에서 허용.
- 옵션 `Approx UVs` (기본 ON). 끄면 UV 없이 만든다(가장 빠름).

### 4-6. 재질

- 원본 `MFnMesh.getConnectedShaders(instance)` → 폴리곤마다 셰이딩 그룹 번호.
- LOD 삼각형은 `tri_poly` 로 원본 폴리곤 → 셰이딩 그룹을 안다.
- **출력 삼각형을 셰이딩 그룹 순서로 정렬해서 만든다** → 그룹마다 면 번호가 연속 → `sets -forceElement sg mesh.f[a:b]` 를 **그룹당 한 번**.
- 옵션 `Copy materials` (기본 ON). 끄면 `initialShadingGroup`.
- 셰이딩 쿼리 주의: [[shading-per-face-assignment]] (`sets -q` 는 트랜스폼 기준이라 쓰지 말 것).

### 4-7. 노멀

`MFnMesh.create` 직후 엣지가 하드로 나올 수 있다 → 만든 뒤 `cmds.polySoftEdge(mesh, a=180, ch=False)` 한 번
(1단계에서 실제로 하드인지 확인하고, 아니면 생략).

### 4-8. 작은 메시

삼각형이 `Min triangles`(기본 100) 이하면 **줄이지 않고 그대로 복제**(눈알 · 치아 같은 작은 메시가 사라지지 않게).
목표가 이보다 작아지는 LOD 에서도 이 값을 바닥으로 쓴다.

### 4-9. Quality 모드 (polyReduce)

같은 입력(바인드 포즈 점)을 임시 메시로 만든 다음
`polyReduce(ver=1, trm=1, tct=target, kqw=0, uwt=0, cwt=0, ch=False)` — 삼각형 수로 직접 지정.
UV 보존이 필요하면 `uwt` 를 올리는 건 사용자 몫이 아니다 — 이 모드는 "느리지만 깨끗한" 비교용 하나면 된다.
결과 메시를 4-6 · 6장과 같은 방식으로 정리(이름 · 그룹 · 기록)한다.

---

## 5. 입력 처리

| 상황 | 처리 |
|------|------|
| 트랜스폼 선택 | 그 아래 **intermediate 가 아닌** mesh 셰이프 (공용 `Framework/core/maya_shape` — [[extendtoshape-picks-wrong-shape]]) |
| 그룹 · 아바타 루트 선택 | 아래의 모든 mesh 트랜스폼을 모은다 (`listRelatives -ad -type mesh -ni` → 부모). **보이지 않는 메시 제외 옵션**은 v2 |
| **스킨 · 블렌드셰이프가 있는 메시** | `Source pose = Bind` (기본): 디포머 체인 맨 위의 **orig 셰이프**(intermediate, inMesh 입력 없음)를 읽는다. `listHistory(shape)` 에서 `intermediateObject=1` 이고 `inMesh` 연결이 없는 mesh. 못 찾으면 현재 셰이프로 폴백하고 로그에 WARNING |
| `Source pose = Current` | 화면에 보이는 변형 결과(현재 프레임)를 읽는다 — 자세 그대로 정적 프록시가 필요할 때 |
| 인스턴스 · 비매니폴드 · 0 면적 면 | 인스턴스는 첫 경로만. 0 면적 삼각형은 면적 가중이라 쿼드릭 기여 0 — 그냥 통과. 비매니폴드도 알고리즘상 문제 없음 |
| 레퍼런스 메시 | 읽기만 하므로 그대로 된다. 출력은 씬의 새 노드 |
| 잠긴 · 숨은 원본 | 상관없다 (읽기만) |

**점 공간**: 오브젝트 공간으로 읽고, LOD 트랜스폼에 **원본 트랜스폼의 월드 행렬을 복사**한다
(`xform -q -ws -m` → 새 트랜스폼 `xform -ws -m`). 원본에 offsetParentMatrix · 비동일 피벗이 있어도 월드 위치가 같다.
Bind 모드에서 orig 셰이프 점은 원본 트랜스폼 기준이므로 같은 행렬을 쓰면 바인드 포즈 위치에 놓인다.

---

## 6. 출력

```
<root>_LOD_grp                      # root = 첫 소스의 최상위 부모 이름 (없으면 소스 이름)
├── LOD1_grp
│   ├── body_LOD1
│   └── cloth_LOD1
├── LOD2_grp
└── LOD3_grp
```

- 이름 = `<원본 짧은 이름>_LOD<n>`, 네임스페이스는 떼고 씬 루트에 둔다.
- 같은 이름의 그룹이 이미 있으면 `Overwrite` (기본 ON) 일 때 **그 그룹을 지우고 다시** 만든다. OFF 면 마야 기본 이름 증가.
- **기록 어트리뷰트** (재바인딩 · 다시 만들기용, 파일 이름에 의존하지 않는다 — [[no-filename-dependent-data]]):
  - `junLodSource` (string) = 원본 메시 **UUID**
  - `junLodLevel` (long) = n
  - `junLodTarget` (long) = 목표 삼각형 수, `junLodMethod` (string) = `fast` / `quality`
- 출력은 바인딩하지 않는다(R4). 로그 끝에 "Rebind with A00275_skinTool_V01 (Copy Weights from source)" 안내 한 줄.
- 재바인딩 흐름(참고, 이 툴 범위 밖): LOD 메시를 원본과 같은 조인트로 `skinCluster` → A00275 Copy Weights / Transfer 로 원본에서 웨이트 복사.
  `junLodSource` 덕분에 짝이 이름 없이도 정해진다(A00275 에 "LOD 짝 자동" 을 넣는 건 별도 작업).

### `Combine per LOD` (옵션, 기본 OFF)

LOD 마다 모든 소스를 **한 메시로 합친다**(월드 공간으로 변환해 배열을 이어 붙이고 `create` 한 번).
스킨클러스터 수가 1개로 줄어 **재생은 더 가볍다** — 끊김 원인이 메시 개수(디포머 수)일 때 효과가 크다.
대신 재바인딩 때 웨이트를 여러 원본에서 가져와야 한다(A00275 Transfer 가 여러 소스를 받는지 1단계에서 확인).
v01.20 에 넣되 기본 OFF.

---

## 7. UI — `LOD` 탭

```
┌ LOD ─────────────────────────────────────────────┐
│ Sources                                          │
│ ┌──────────────────────────────────────────────┐ │
│ │ body_geo        (84,212 tris)                │ │  ← 공용 TSL (Add / Del / Clear / Sort)
│ │ cloth_geo       (41,006 tris)                │ │
│ └──────────────────────────────────────────────┘ │
│ [Add Selected] [Remove] [Clear]   Total 125,218  │
│                                                  │
│ LOD count [ 3 ▾]   Mode (•) Ratio ( ) Triangles  │
│ LOD1 [ 50.0 ]%  LOD2 [ 25.0 ]%  LOD3 [ 12.5 ]%   │  ← count 만큼만 보임, Triangles 모드면 정수
│ LOD4 [  6.2 ]%  LOD5 [  3.1 ]%                   │
│                                                  │
│ Method      (•) Fast (Cluster)  ( ) Quality      │
│ Source pose (•) Bind            ( ) Current      │
│ [x] Approx UVs   [x] Copy materials              │
│ [x] Keep thin parts   [ ] Combine per LOD        │
│ [x] Overwrite     Min triangles [ 100 ]          │
│                                                  │
│ [          Build LODs          ]                 │
│ [Select LOD1][LOD2][LOD3]...    [Delete LODs]    │
│                                                  │
│ Mesh       Src     LOD1    LOD2    LOD3   Time   │  ← 결과 표 (QTreeWidget, 공용 treeExpand 불필요 - 평면)
│ body_geo   84212   41950   20877   10388  0.41s  │
│ cloth_geo  41006   20311   10119    5002  0.22s  │
└──────────────────────────────────────────────────┘
```

- UI 문자열은 **전부 영어**. 주석 · 독스트링만 한국어.
- 설정은 optionVar 로 기억(`JUN_A00380_lod_*`): LOD count, 비율/수, 체크박스, Method, Source pose.
- 리스트 항목 = UUID 붙인 TSL ([[framework-tsl-attach-uuids]]), 메시가 아니면 Add 때 거른다.
- `Select LODn` = 마지막 Build 결과 n 단계 메시 선택. `Delete LODs` = 마지막 결과 그룹 삭제(undo 가능).
- 버튼 상태: 리스트가 비면 Build 비활성. numpy 가 없으면 Fast 라디오 비활성 + 툴팁.
- 창 높이는 기존 `JUN_mod_tabFit_qt_v01` 가 탭을 따라간다 — 새 탭도 자동 포함(별도 코드 불필요, 확인만).
- 결과 표는 길어질 수 있으니 높이 상한 + 스크롤([[tsl-widget-max-height-squeezes-buttons]] 처럼 리스트에만 상한).

---

## 8. 파일 구성

```
tools/A00380_MeshTool/
├── app/core/lod_manager.py      # 신규 - Qt 비의존. 4·5·6장 전부
├── app/ui/lod_tab.py            # 신규 - LodTab(QWidget). uv_tab.py 와 같은 꼴 (log 콜백 주입)
├── app/ui/main_window.py        # 탭 등록 3줄 + Help > LOD Notes(선택)
└── app/config/version.py        # 01.20 기록
docs/A00380_MeshTool.md          # 3-6 절 "LOD 탭" 추가, 화면 구성 그림에 탭 추가
docs/WORKLOG.md                  # 그날 항목
docs/portfolio/*                 # EN/KR 동기 ([[update-portfolio-on-tool-work]])
```

### 8-1. `lod_manager.py` 골격

```python
# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-xx
"""LOD 메시 생성 (재생용 저폴리 프록시). numpy 클러스터-QEM(Fast) / polyReduce(Quality)."""

from dataclasses import dataclass, field

@dataclass
class LodOptions:
    count: int = 3
    mode: str = "ratio"                    # "ratio" | "triangles"
    values: tuple = (50.0, 25.0, 12.5, 6.25, 3.125)
    method: str = "fast"                   # "fast" | "quality"
    source_pose: str = "bind"              # "bind" | "current"
    approx_uvs: bool = True
    copy_materials: bool = True
    keep_thin: bool = True
    combine: bool = False
    overwrite: bool = True
    min_tris: int = 100

@dataclass
class MeshData:                            # 4-1 의 사전 계산 결과 (LOD 간 공유)
    source: str          # 원본 트랜스폼 (긴 이름)
    uuid: str
    world_matrix: list
    P: "np.ndarray"; T: "np.ndarray"; tri_poly: "np.ndarray"
    Kv: "np.ndarray"; bucket: "np.ndarray"
    vert_uv: "np.ndarray | None"           # (N,2)
    poly_sg: "np.ndarray | None"; sg_names: list
    bbmin: "np.ndarray"; ext: float

@dataclass
class LodResult:
    source: str
    src_tris: int
    lod_meshes: list = field(default_factory=list)   # [(level, mesh, tris)]
    seconds: float = 0.0
    warnings: list = field(default_factory=list)

def has_numpy() -> bool
def collect_meshes(nodes) -> list[str]                       # 5장: 그룹 펼치기, 메시 트랜스폼만
def find_orig_shape(transform) -> str | None                 # 5장: 디포머 체인 맨 위
def read_mesh(transform, source_pose, want_uv, want_sg) -> MeshData        # 4-1
def target_tris(src_tris, opts, level) -> int                # 비율/수 → 목표 (min_tris 바닥)
def simplify_cluster(md, target, keep_thin, res_hi=None) -> (V, Tri, tri_poly, rep_vert, res)   # 4-2
def simplify_quality(md, target) -> (V, Tri, tri_poly)       # 4-9
def create_mesh(name, parent, V, Tri, uv=None) -> str        # cmds.createNode transform + MFnMesh.create(parent=)
def assign_materials(mesh, tri_sg, sg_names)                 # 4-6, 정렬된 연속 범위
def tag(mesh, md, level, target, method)                     # 6장 기록 어트리뷰트
def build_lods(nodes, opts, progress=None, log=None) -> list[LodResult]   # 전체, undo_chunk 안
def delete_lods(group)
```

규칙:
- **`build_lods` 전체를 `Framework.core.maya_undo.undo_chunk()` 로 감싼다** → Ctrl+Z 한 번에 LOD 전부 사라짐.
  트랜스폼을 `cmds.createNode` 로 만들고 그 아래 `MFnMesh.create(parent=...)` 로 셰이프를 만들면 같은 청크로 사라진다
  (A00610 `maya_build.py` 8행 주석에서 확인된 방식). 1단계에서 undo/redo 를 다시 확인한다.
- 계산(numpy)과 씬 쓰기(cmds/API)를 함수로 나눈다 → 계산부는 마야 없이도 단위 시험 가능.
- 실패한 메시 하나가 전체를 멈추지 않는다: 메시별 try → `LodResult.warnings` + 로그 WARNING, 나머지는 계속.

### 8-2. `main_window.py` 변경

```python
from .lod_tab import LodTab
...
self.lod_tab = LodTab(log=lambda text: self.log(text))
self.tabs.addTab(self.lod_tab, "LOD")      # Match 다음 (맨 오른쪽)
```
`on_tab_changed` 에서 LOD 탭은 Peak/Match 세션을 건드리지 않는다(다른 탭으로 갈 때 미리보기 restore 하는 기존 흐름 유지).

---

## 9. 작업 순서 · 완료 조건

| 단계 | 내용 | 완료 조건 |
|------|------|-----------|
| **1. 코어 프로토타입 → `lod_manager.py`** | 4-1 ~ 4-3, 4-7, 4-8, `create_mesh`, `undo_chunk`. UV · 재질 · 버킷 없이 먼저 | mayapy 시험 A · B · F 통과 |
| **2. 얇은 부위 · UV · 재질** | 4-4 버킷, 4-5 UV, 4-6 재질 | 시험 C · D · E 통과 |
| **3. 입력 처리 · 출력 정리** | 5장 (orig 셰이프, 그룹 펼치기, 월드 행렬), 6장 (그룹 · 이름 · 기록 · Overwrite · Combine), 4-9 Quality | 시험 G · H · I 통과 |
| **4. 실제 아바타 실측** | 사용자 아바타 씬 1개로 Fast vs Quality 시간 · 삼각형 수 · 겉보기 비교, 2023 에서도 1회 | 아바타 1개 LOD3 개 Fast 가 Quality 의 1/5 시간 이하, 표를 이 문서 10장에 기록 |
| **5. UI `lod_tab.py`** | 7장 화면, optionVar, 진행률 팝업, 결과 표, 테마 입힌 오프스크린 렌더로 레이아웃 확인 | 오프스크린 렌더 png 확인 ([[offscreen-size-needs-theme]]) |
| **6. 마야 GUI 확인** | 사용자가 실제 마야에서 Build → 재생 끊김이 사라지는지 | 사용자 확인 (헤드리스로 Qt 를 못 돌린다 — [[mayapy-headless-verify]]) |
| **7. 문서** | 버전 01.20, `docs/A00380_MeshTool.md` 3-6 절, WORKLOG, portfolio, 메모리 | 커밋 (푸시는 그 턴 요청 시만) |

### 9-1. mayapy 시험 목록 (`docs/plans/A00380_MeshTool_LOD_probe_test.py` 로 만든다)

| ID | 시험 | 기대 |
|----|------|------|
| A | 구 8만 / 32만 삼각형, 비율 50·25·12.5·6.25·3.125 | 각 LOD 삼각형 ≤ 목표, 목표의 85 % 이상 |
| B | 같은 입력에서 Fast 전체 시간 vs `polyReduce` | 모든 비율에서 Fast 가 더 빠름 (2장 표 재현) |
| C | 서로 0.2 떨어진 평행 판 두 장(앞뒤 노멀 반대)을 한 메시로, 12.5 % | `keep_thin=True` 면 두 판이 서로 붙지 않음(각 판의 점들이 자기 판 평면에서 0.05 이내) |
| D | UV 있는 메시 | LOD 에 UV 세트 존재, UV 수 = 버텍스 수, 값이 0~1 원본 범위 안 |
| E | 반은 lambert1, 반은 새 블린인 메시 | LOD 면의 셰이딩 그룹이 원본 공간 위치와 일치 (각 LOD 면 중심 → 가장 가까운 원본 면의 SG 와 95 % 이상 일치) |
| F | `undo` 한 번 / `redo` | 그룹 · 메시 전부 사라짐 / 다시 생김, 씬 노드 수 원상 |
| G | 조인트 2개에 스킨하고 조인트를 90° 돌린 상태 | Bind 모드 LOD 의 bbox ≈ 원본 바인드 포즈 bbox, Current 모드 LOD bbox ≈ 변형된 bbox |
| H | 원본 트랜스폼에 이동 · 회전 · 스케일 · offsetParentMatrix | LOD 와 원본의 월드 bbox 중심 차 < 1e-3 × 크기 |
| I | 같은 설정으로 두 번 Build (Overwrite ON / OFF) | ON: 그룹 하나 유지, OFF: `_LOD_grp1` 이 생김. `junLodSource` = 원본 UUID |

---

## 10. 위험 · 한계

| 위험 | 대응 |
|------|------|
| 얇은 부위(손가락 · 옷) 가 낮은 LOD 에서 붙음 | 노멀 버킷(4-4), 메시 단위 처리. 그래도 심하면 그 LOD 만 Quality 로 (v2: LOD 마다 Method) |
| 버킷 경계 · 셀 경계에 작은 틈 | 재생 프록시 용도로 허용. 문서에 명시 |
| 목표 삼각형 수를 정확히 못 맞춤 (−7 % 내외) | 표시만 정확히. 정확한 수가 필요하면 Quality |
| 실제 아바타에서 속도 이득이 구보다 작을 수 있음 (메시가 많고 작으면 고정 비용 비중↑) | 4단계 실측. 메시당 고정 비용(읽기 · 노드 생성)을 줄이는 쪽으로 최적화 |
| `MFnMesh.create` 결과가 undo 청크에 안 묶이는 경우 | 1단계 시험 F. 안 되면 트랜스폼 delete 로 정리하는 `Delete LODs` 를 확실히 + 로그 안내 |
| numpy 없는 마야 | Fast 비활성, Quality 만 |

### 재생 끊김 원인에 대한 메모 (작업 범위 밖, 참고)

LOD 로 끊김이 사라진 건 **스킨 평가 비용**(버텍스 수 × 영향 수)이 원인일 가능성이 크다. LOD 와 함께 해 볼 만한 것:
Preferences > Animation > **Evaluation = Parallel + GPU Override**(스킨을 GPU 로), **Cached Playback**, 재생 중 보이지 않는 고폴리 원본 숨기기.
"가끔 몇 프레임" 이 메모리 · 캐시 채우는 순간일 수도 있으니, 4단계 실측 때 원본 아바타를 숨긴 채 LOD 아바타만 재생해 끊김 유무를 같이 적는다.

---

## 10-2. 구현 결과 (2026-11-16)

**실제 아바타** CHOEUN 리그 씬(`geo_grp` 메시 5개 · 27.6만 삼각형, 스킨 + 블렌드셰이프), LOD 3개(50 / 25 / 12.5 %):

| 메시 | 원본 | Fast LOD1 / 2 / 3 | Quality LOD1 / 2 / 3 |
|------|-----:|------|------|
| Body | 15,564 | 7,713 / 3,770 / 1,910 | 7,782 / 3,890 / 1,946 |
| Face | 9,082 | 4,474 / 2,257 / 1,096 | 4,541 / 2,270 / 1,134 |
| Magical_Costume | 195,270 | 97,496 / 48,526 / 24,206 | 97,635 / 48,817 / 24,408 |
| panties | 1,658 | 804 / 381 / 195 | 828 / 414 / 206 |
| SG_Hair | 54,728 | 26,512 / 13,410 / 6,380 | 27,363 / 13,682 / 6,840 |
| **합계 시간** | | **1.59 s** | 18.89 s (**11.9배**) |

- 바인드 포즈 확인: orig 셰이프와 LOD1 bbox 차이 최대 0.73 (panties, 크기 32.6 의 2%), 나머지 0.13 이하.
- 재질: Face 8개 · Costume 3개 셰이딩 그룹이 LOD3 까지 그대로 붙는다.
- Combine per LOD: 1.54 s, LOD 메시 3개(137k / 68k / 34k).
- 4단계 완료 조건(Fast ≤ Quality 의 1/5) 통과.

**계획에서 바뀐 것**

- ★ 해상도 이분 탐색의 개수는 **중복 삼각형을 뺀 뒤** 센다(§4-2). 빼기 전으로 세면 양면 헤어 카드가 절반씩 사라져
  SG_Hair LOD3 이 목표 6,840 의 **36%(2,456)** 까지 떨어졌다 → 수정 후 93%. 중복 판정은 정렬한 세 셀 번호를
  정수 키 하나로 만들어 1차원 `np.unique`(axis=0 보다 빠르다).
- Quality 모드도 메시 읽기(numpy)를 쓰므로 **numpy 가 없으면 탭 전체(Build)를 끈다**(§3 의 "Quality 만 허용" 대신).
- 시험 G(현재 포즈) 기대값: 트랜스폼 `exactWorldBoundingBox` 는 숨은 orig 셰이프까지 포함한다 → 보이는 셰이프로 잰다.
- mayapy 시험 스크립트 이름을 `inspect.py` 로 두면 표준 모듈을 가려 `maya.standalone.initialize()` 가 그대로 죽는다(스크래치 파일 이름 주의).

**검증**: mayapy 시험 19/19, 오프스크린 UI(빌드 · LOD 선택 · 모드 전환 · 삭제 · 탭 최소 폭 379 < UV Sets 439 → 창 폭 748 그대로).

---

## 11. 다음 버전 후보 (v2)

- LOD 마다 Method 지정, 보이지 않는 메시 제외, 이름 규칙 프로파일(공용 토큰 위젯)
- A00275 에서 `junLodSource` 로 LOD ↔ 원본 짝 자동 → "Rebind LODs" 한 버튼
- 같은 아바타를 다시 만들 때 사전 계산 캐시(원본 점이 안 바뀌었으면 재사용)
