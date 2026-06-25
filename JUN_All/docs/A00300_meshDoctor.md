# A00300_meshDoctor

문제 있는 폴리곤 메시를 **읽기 전용으로 진단**해 **로그 파일(JSON + TXT)** 로 출력하고,
**안전한 원클릭 수정**(Undo 가능)을 제공하는 PySide 툴. 로그를 Claude 에게 주면 근본 원인 분석을 받을 수 있다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00110_animTool` 클론)
- **버전**: `app/config/version.py` (v01.00)
- **설치**: `__dragDrop_A00300.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 → `tools.A00300_meshDoctor.run(True)`
- **의존**: 외부 pip 없음. `maya.cmds` + `maya.api.OpenMaya` 2.0 만 사용 (Maya 2023+).

---

## 왜 만들었나 — 두 가지 대표 증상

1. **메시가 아닌 빈 공간을 클릭해도 메시가 선택됨.**
   → 거의 항상 **bounding box 팽창**. Maya 클릭 셀렉션은 먼저 bbox 히트 테스트를 쓰는데,
   **NaN/Inf 정점**, 본체에서 멀리 떨어진 **떠돌이(stray) 정점**, 깨진 **intermediate(orig) shape** 가
   bbox 를 비정상적으로 키우면 빈 공간 클릭이 메시로 잡힌다.

2. **웨이트 Transfer(예: kangaroo SkinCluster › Transfer) 시 일부만 이동되거나 일부 페이스가 일그러짐/삭제됨.**
   → **토폴로지 손상**. Transfer 는 내부적으로 **barycentric(무게중심) 좌표**로 웨이트를 매핑한다.
   **zero-area 페이스**(면적 0)는 균등 폴백(0.25)으로, **NaN 정점**은 0 으로 처리되고,
   **non-manifold / lamina** 는 closest-point 면 ID 가 잘못 잡혀 그 부위만 웨이트가 0/오류로 들어간다.
   결과적으로 "일부만 이동·일그러짐"이 된다.

이 두 원인을 한 번에 점검·수정하려고 만든 툴이다.

---

## kangaroo Transfer 는 어떻게 동작하고, 왜 깨지나 (증상 2 원리)

> kangaroo 플러그인(`C:/Users/USER/Desktop/JP/0020_maya_plugin/0010_kangaroo`) 소스를 따라가 확인한 내용.
> 진단 항목이 무엇을 노리는지 이해하려면 Transfer 의 내부 원리를 알아야 한다.

**핵심: Transfer 는 `copySkinWeights` 를 쓰지 않는다.** 대신 **barycentric(무게중심) 보간**으로 타겟 정점마다
웨이트를 새로 계산한 뒤 `MFnSkinCluster.setWeights()`(OpenMayaAnim API)로 직접 써넣는다.
관련 파일: `scripts/kangarooTabTools/weights.py`(전이 로직), `scripts/kangarooTools/barycentric.py`(좌표 계산),
`plug-ins/.../kt_cmdUndo.py`(웨이트 적용).

**흐름 (기본 `closestPoint` 모드)**

1. 타겟 메시의 각 정점에 대해, 플러그인 `kt_findClosestPoints(... returnFaces=True)` 로 **소스 메시 표면의
   최근접점 + 그 면(face) ID** 를 구한다.
2. 그 면의 정점들에 대한 **barycentric 좌표**(면 안에서 각 정점이 차지하는 가중치)를 계산한다.
3. `타겟 웨이트 = Σ(소스 정점 웨이트 × barycentric 좌표)` 로 보간해 적용한다.

전이 모드는 `vertexIndex / closestVertex / closestPoint(기본) / closestUV / closestUVPoint / spikes` 가 있고,
**토폴로지 일치 불요**(정점 수가 달라도 됨)·**UV 불요**(UV 모드 제외)·**히스토리 삭제 안 함**·**메시 미수정**이다.
→ 즉 Transfer 자체는 페이스를 지우지 않는다. "삭제·일그러짐"처럼 보이는 건 **잘못 계산된 웨이트로 정점이
엉뚱하게 변형**된 결과다.

**그래서 토폴로지가 손상되면 그 부위만 좌표 계산이 깨진다:**

| 메시 결함 | barycentric 단계에서 벌어지는 일 | 결과 |
|-----------|----------------------------------|------|
| **zero-area 페이스** (면적 0) | 쿼드는 좌표가 `[0.25,0.25,0.25,0.25]` 균등 폴백, 트라이앵글은 면적이 `1e-10` 으로 클램프 → 정규화 시 쓰레기 좌표 | 그 페이스의 웨이트가 무의미 → 정점이 바인드 위치로 붕괴/일그러짐 |
| **NaN 정점** | 0 나눗셈 → NaN → `np.nan_to_num()` 이 **조용히 0 으로** 변환 → 좌표 `[0,0,0,0]` | 그 정점에 **influence 가 전혀 전이되지 않음**(웨이트 0) |
| **non-manifold / lamina** | 최근접점이 **엉뚱한 face ID** 를 돌려줌(한 엣지를 3+개 페이스가 공유 / 겹친 페이스) | 다른 면의 웨이트로 보간 → 그 부위만 왜곡 |
| **겹친(미병합) 정점** | 보이지 않는 토폴로지 분할로 closest-face 매핑이 일관되지 않음 | 경계에서 웨이트 불연속 |

타겟 정점은 **하나씩 독립 처리**되므로, 좋은 토폴로지 부위는 정상 전이되고 결함이 있는 부위만 0/오류 웨이트가
들어간다. → **"일부만 이동, 일부만 일그러짐"** 이라는 증상으로 나타난다.

**대응**: 그래서 Transfer **전에** 소스/타겟 메시를 `polyCleanup`(zero-area·non-manifold·lamina·zero-edge),
`Merge Vertices`(겹친 정점), `Snap NaN/Stray Verts`(NaN) 로 정리해야 한다 — 이 툴의 진단·수정이 노리는 지점이다.

> **NaN(Not a Number)이란?**
> 부동소수점(IEEE 754)에서 **수치로 정의되지 않는 값**을 가리키는 특수값이다. `0/0`, `∞-∞`,
> `sqrt(음수)` 같은 **정의되지 않은 연산**의 결과로 생기며, 메시에서는 정점 좌표가 `(NaN, NaN, NaN)`
> 처럼 깨진 상태를 말한다(흔히 잘못된 디포머/스크립트/임포트/시뮬 발산에서 발생). NaN 의 핵심 성질은
> **전염성**이다 — `NaN` 과의 모든 비교는 거짓이고(`NaN == NaN` 도 `False`), `NaN` 이 섞인 모든 산술은
> 다시 `NaN` 이 된다. 그래서 정점 하나만 NaN 이어도 그것을 참조하는 거리·면적·bounding box·웨이트
> 계산이 통째로 오염된다(`Inf`(무한대)도 비슷하게 bbox 를 망가뜨린다). 이 툴은 `math.isfinite()` 로
> NaN/Inf 를 판별한다.

> **manifold / non-manifold 란?**
> **manifold(다양체)** 메시는 "실제로 만들 수 있는 표면"처럼 위상이 깔끔한 상태다. 구체적으로
> **모든 엣지가 정확히 1~2 개의 페이스에만 공유**되고(경계는 1, 내부는 2), **한 정점 주위의 페이스들이
> 하나의 부채꼴로 연속**되게 이어진다. **non-manifold(비다양체)** 는 이 규칙이 깨진 상태로 대표 케이스는:
> ① **한 엣지를 3 개 이상의 페이스가 공유**(T자/책장 모양), ② **나비넥타이(bowtie) 정점** — 두 페이스가
> 정점 하나로만 붙어 주변이 두 갈래로 갈라짐, ③ **반대로 뒤집힌 노멀이 한 점에서 맞붙는** 경우.
> 두께 0 의 벽을 한 면이 공유하거나, 정점/엣지 병합을 잘못했을 때 흔히 생긴다. 표면 위 한 점에서
> "안/밖"이나 "이웃 면"이 모호해지므로, closest-point/표면 기반 연산(스킨 전이·언랩·시뮬)이 그 부위에서
> 어긋난다. 진단: `cmds.polyInfo(nonManifoldEdges=True / nonManifoldVertices=True)`.

> **lamina face 란?**
> **한 페이스가 다른 페이스와 자신의 모든 엣지(테두리 전체)를 공유**하는 상태 — 같은 자리에 페이스가
> **앞뒤로 두 장 겹쳐** 있는 것이다("lamina" = 얇은 층/겹). 면을 실수로 복제하거나, 열린 구멍을 양쪽에서
> 메우다 겹치거나, 미러/병합 후 가운데가 두 겹이 될 때 생긴다. 겉보기엔 한 장처럼 보여 눈치채기 어렵지만
> 두께 0 으로 포개져 있어 노멀/셰이딩이 깜빡이고, 면적·closest-face 계산이 어느 장을 고를지 모호해진다.
> non-manifold 의 특수한 형태로 분류되며, 진단: `cmds.polyInfo(laminaFaces=True)`. 둘 다 `polyCleanup` 으로 정리.

---

## 메시를 수정하지 않고 Transfer 하는 법

> kangaroo 플러그인을 **수정하지 않고**, UI 옵션만 바꿔 깨진 메시로도 Transfer 를 정상 동작시키는 방법.
> 근거는 모두 kangaroo 소스(`scripts/kangarooTabTools/weights.py`)에서 읽기 전용으로 확인했다.

**핵심: Transfer 모드를 기본 `closestPoint` 에서 `closestVertex` 로 바꾼다.**
SkinCluster 탭 › Transfer 옵션에는 모드 라디오 버튼이 있다(`weights.py:1818`,
`controls.RadioButtonsControl(TransferMode)`). 웨이트 적용부(`weights.py:2073-2077`)가 모드별로 경로가 다르다:

```python
if iMode in [0, 1, 3]:     # vertexIndex / closestVertex / closestUV
    aWeights[...] = xWeights[iMesh][xIdMaps[iMesh]]          # 소스 정점 웨이트를 그대로 직접 대입
elif iMode in [2, 4, 5]:   # closestPoint / closestUVPoint / spikes
    aMultiplied = xWeights[...] * aMapCoords[...]            # ← barycentric 좌표(aMapCoords) 곱셈
    aWeights[...] = np.sum(aMultiplied, axis=1)
```

깨짐의 원흉인 **barycentric 좌표 `aMapCoords` 는 모드 2·4·5 에서만 쓰인다.** `closestVertex`(1)/`closestUV`(3)
는 최근접 **정점**의 웨이트를 그대로 복사하므로 면(face)·면적·면 ID 를 일절 보지 않는다.

| 메시 결함 | `closestVertex` 모드에서 |
|-----------|--------------------------|
| zero-area 페이스 | **무관** (면을 안 봄) |
| non-manifold / lamina | **무관** (면 ID 매핑 안 함) |
| 겹친(미병합) 정점 | 무해 (가까운 정점 하나 선택) |
| **NaN 정점** | ⚠️ **여전히 깨짐** (위 NaN 정의 참고 — 거리 계산이 통째로 오염) |

→ 메시를 전혀 건드리지 않고, 깨지던 부위가 정상 전이된다.

**보완 / 주의**

1. **NaN 만은 예외.** 어떤 모드든 NaN 은 우회 불가(전염성 때문). 단 MeshDoctor 의 `Snap NaN/Stray Verts` 는
   정점을 **삭제하지 않고 좌표만 복구**(정점 수·점 순서·토폴로지 보존)하므로 "토폴로지 수정"이 아니라
   "오염된 좌표값 복구"에 가깝다 → 사실상 무수정에 준한다.
2. **품질.** `closestVertex` 는 면 보간이 없어 소스가 성긴 메시면 웨이트가 계단식으로 거칠 수 있다.
   소스가 조밀하면 차이가 거의 없고, 거칠면 전이 후 weight smooth 를 주거나 UV 가 깨끗하면
   `closestUV`(모드 3, 동일하게 직접 대입 경로)를 쓴다.
3. **컴포넌트 스킵(옵션).** `weights.py:1868-1878` — 소스에서 좋은 컴포넌트만 선택해 전이하면 나머지는
   `aSkip` 으로 자동 제외된다(closestVertex 는 정점 단위, closestPoint 는 페이스 단위). 문제 페이스/정점을
   빼고 전이하는 것도 메시 수정 없이 가능하다.
4. **비파괴 프록시(품질 최우선).** `closestPoint` 의 부드러운 면 보간을 유지하고 싶으면 — **원본은 그대로 두고**
   복제본을 만들어 (동일 토폴로지라 index 로 1:1) 웨이트 복사 → 복제본만 `polyCleanup` →
   **깨끗한 복제본을 소스로** `closestPoint` 전이. 원본 메시는 끝까지 손대지 않는다.

**요약**: 가장 간단한 무수정 해법은 **Transfer 모드를 `closestVertex` 로 변경**(NaN 만 별도 처리).

---

## 진단 항목 (메시를 수정하지 않음)

선택한 폴리곤 메시마다 아래를 검사하고, 각 항목을 `PASS / INFO / WARN / FAIL` 로 분류한다.

**정점 무결성 (증상 1)**
- `nan_inf_vertices` — NaN/Inf 좌표 정점 (FAIL)
- `stray_vertices` — 본체에서 비정상적으로 먼 떠돌이 정점 (FAIL)
- `bbox_inflation` — 실제 bbox 대각 vs 본체 bbox 대각 비교 → 팽창 (FAIL)
- `intermediate_shapes` — 다중 orig shape (WARN)
- `construction_history` — 잔여 non-deformer 히스토리 (WARN)

**토폴로지 (증상 2)**
- `non_manifold` — non-manifold edge/vertex (FAIL)
- `lamina_faces` — 겹친 페이스 (FAIL)
- `zero_area_faces` — 퇴화/슬라이버 페이스 (형상품질 q 기반, FAIL) · `tiny_faces` — 작지만 정상인 면 (INFO, 결함 아님)
- `zero_length_edges` — 길이 0 엣지 (FAIL)
- `coincident_vertices` — merge 거리 안의 미병합 정점쌍 (WARN)
- `holed_faces` / `concave_faces` / `floating_vertices` / `border_edges`

**기타 건강도**
- `negative_scale` — 음수 스케일(노멀 뒤집힘) (WARN)
- `uv_sets` / `missing_uvs` — UV 셋·누락(UV 기반 transfer 모드 대비)
- `skin_cluster` — skinCluster influence/maxInfluences 정보 (INFO)

각 메시 결과 끝에 **suspected_root_causes**(증상 1/2 매핑)를 함께 출력한다.

---

## 사용 순서

1. `__dragDrop_A00300.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프에 **MeshDoctor** 버튼 생성.
2. 문제 메시 선택 → **Diagnose Selected**.
   - 로그뷰에 색상별(FAIL=빨강 …) 요약 출력.
   - `tools/A00300_meshDoctor/0020_out/` 에 두 파일 저장:
     - `meshDoctor_<scene>_<timestamp>.json` — 구조화 데이터(**Claude 분석용**)
     - `..._summary.txt` — 사람이 읽는 요약
3. **Open Log Folder** 로 폴더 열기 → `.json` 내용을 Claude 에게 전달 → 근본 원인·수정 순서 안내 받기.
4. (권장: 복제본에서) **Safe One-Click Fixes** 버튼으로 수정 → 다시 **Diagnose** 로 PASS 확인 → Transfer 재시도.

---

## 안전 원클릭 수정 (전부 Undo 가능 / Ctrl+Z 한 번)

| 버튼 | 동작 | 쓰는 상황 |
|------|------|-----------|
| **Delete History (deformer-safe)** | `bakePartialHistory(prePostDeformers=True)` (skinCluster/blendShape 보존) | 잔여 poly 히스토리 |
| **Merge Vertices** | `polyMergeVertex(distance=1e-4)` | 겹친/미병합 정점 |
| **Conform Normals** | 노멀 잠금 해제 + `polyNormal(conform)` | 뒤집힌/잠긴 노멀 |
| **polyCleanup (fix corruption)** | non-manifold + lamina + zero-area face + zero-length edge 일괄 수정 | 증상 2 핵심. **토폴로지가 바뀔 수 있어 재바인딩 필요할 수 있음** |
| **Snap NaN / Stray Verts** | NaN·떠돌이 정점을 centroid 로 이동(**삭제 없이**) | 증상 1 — bbox 수축, 빈 공간 선택 해결 |

> **주의**: `polyCleanup` / `Merge` 는 정점·엣지를 추가/삭제할 수 있다. 스킨이 걸린 메시는
> **복제본에서 정리하거나 정리 후 재바인딩**을 고려한다. `Snap NaN/Stray Verts` 는 정점 수를
> 보존하므로 스킨 안전.

**Select Problem Components** (셀렉션만 변경, 지오메트리 불변): Non-Manifold / Zero-Area Faces / Stray·NaN Verts 를
선택해 뷰포트에서 직접 확인할 수 있다.

---

## 진단 노트 — `polyCleanup` 후에도 `zero_area_faces` 가 남는 경우

`polyCleanup` 을 돌려도 `zero_area_faces` 가 계속 FAIL 로 잡히고, 그 면을 선택하면 **육안으로 보이는 아주 작은
면**이 나오는 사례가 있다. 원인과 판단 기준, 그리고 **v01.01 에서 적용한 개선**을 정리한다.

### 왜 어긋났나 (v01.00 의 판정 기준)
- **진단(`mesh_scan.py`)**: `it.zeroArea()` **또는** 오브젝트공간 `getArea() < 1e-10` 이면 FAIL.
- **`polyCleanup`(`mesh_fix.py`)**: zeroGeom 허용치 **`1e-05`** 미만 면을 제거.
- polyCleanup(1e-05)이 안 지웠는데 진단이 잡았다는 것은, 트리거가 **Maya 의 `it.zeroArea()`** 라는 뜻이다.
  즉 Maya 는 그 면을 "면적 0" 으로 보지만 polyCleanup 기준으론 정리 대상이 아니어서 **둘이 어긋난** 상태다.
  (오브젝트 공간에서 작게 모델링하고 트랜스폼 스케일로 키운 메시에서도 절대 면적이 작게 나와 잘 발생한다.)

### 케이스 A — 진짜 슬라이버(퇴화) 면
정점들이 거의 **일직선/겹침**이라 면적이 구조적으로 0 에 수렴. 육안엔 "얇은 선" 같아도 실제 면적은 ~0.
- **Transfer 를 진짜로 깨뜨린다**(barycentric 가 면적으로 나눗셈 → ill-conditioned). → **계속 FAIL 로 잡는 게 맞다.**
- 이 면이 필요해 토폴로지를 못 건드리면 → **Transfer 를 `closestVertex` 모드로**(면을 아예 안 봄, 위 섹션 참고).

### 케이스 B — 작지만 멀쩡한 면 (오탐)
정점이 서로 떨어져 있고 일직선이 아닌, **절대 크기만 작은** 정상 면.
- barycentric 좌표는 **면적의 비율**(부분/전체)이라 면이 균일하게 작아도 수치적으로 멀쩡하다. → **FAIL 은 오탐.**
  이건 메시가 아니라 **툴을 고쳐야** 하는 경우다.

### 권고
- **필요한 면은 삭제하지 않는다.** 필요한 면을 지우면 구멍/실루엣 변형으로 작은 면 하나보다 더 큰 문제가 생긴다.
  삭제는 **불필요한 쓰레기 면**(겹친 중복면·붕괴 잔재)에만 적용한다.
- **무조건 "zero_area 로 안 친다" 도 위험**하다 — 케이스 A 슬라이버는 실제로 Transfer 를 깨므로.

### v01.01 적용 — 형상품질(q) 기반 판정
절대 면적/`zeroArea()` 의존을 줄이고 **스케일 무관 형상품질**로 퇴화를 판정한다(`mesh_scan.face_quality`):

```
q = (4 · π · area) / perimeter²      # 등주지수. 원=1, 정사각형≈0.785, 정삼각형≈0.60, 슬라이버→0
```

- **후보 면** = `it.zeroArea()` 또는 `area < AREA_TINY(1e-5)`.
- 후보 중 **`area < AREA_DEGEN(1e-10)` 또는 `q < QUALITY_EPS(1e-2)`** → `zero_area_faces`(**FAIL**, 케이스 A 슬라이버, Transfer 깨짐).
- 그 외(작지만 형상 정상) → 신규 `tiny_faces`(**INFO**, 케이스 B, 결함 아님). FAIL 오탐 제거.
- 임계치 `AREA_TINY` 는 polyCleanup zeroGeom(1e-05)과 정렬. 세 상수 모두 `mesh_scan.py` 상단에서 조정 가능.
- 로그(JSON/TXT)의 `zero_area_faces`/`tiny_faces` 샘플에 면별 **`f<idx> a=<면적> q=<품질>`** 을 기록 → 케이스 A/B 를 눈으로 구분.
- `Select Zero-Area Faces` 헬퍼도 같은 기준(슬라이버만 선택).

> **케이스 A 인 면이 꼭 필요하면** 메시를 고치지 말고 **Transfer 를 `closestVertex` 모드로**(위 "메시를 수정하지 않고 Transfer 하는 법" 참고). 슬라이버 면이 무시되어 그대로 전이된다.

---

## 진단 → 분석 → 수정 워크플로 (Claude 연동)

```
[Diagnose] → 0020_out/*.json  →  사용자가 Claude 에게 전달
            → Claude 가 근본 원인 확정 + 어떤 Fix 버튼을 어떤 순서로 누를지 안내
            → 복제본에서 Fix 적용 → 재 Diagnose 로 PASS 확인 → Transfer 재시도
```

전형적 처방:
- **증상 1만**: `Snap NaN/Stray Verts` → (필요 시) `Delete History` → 재진단.
- **증상 2**: `Delete History` → `Merge Vertices` → `polyCleanup` → `Conform Normals` → 재진단 → 재바인딩 후 Transfer.

---

## 구조

```
tools/A00300_meshDoctor/
├── launch.py / __init__.py / __dragDrop_A00300.py
├── app/
│   ├── config/version.py
│   ├── core/
│   │   ├── mesh_scan.py     # 읽기 전용 진단 (핵심)
│   │   ├── report.py        # JSON + TXT 로그 출력 (PathManager → 0020_out/)
│   │   └── mesh_fix.py      # 안전 원클릭 수정 (Undo 가능)
│   └── ui/main_window.py    # Qt UI
└── 0020_out/                # 로그 출력 (.gitignore 대상)
```

- 진단 로직은 `maya.api.OpenMaya` (`MFnMesh`, `MItMeshPolygon/Edge/Vertex`) + `maya.cmds.polyInfo` 사용.
- 임계값(떠돌이 배수, bbox 팽창비, 면적/엣지 epsilon, merge tol)은 `mesh_scan.py` 상단 상수로 조정 가능.
