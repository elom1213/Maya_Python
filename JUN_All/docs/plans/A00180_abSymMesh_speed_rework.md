# A00180_abSymMesh — 속도 개선 재작업 계획서

## Context (배경 / 목적)

`origin.mel` 은 2008년에 작성된 Brendan Ross 의 `abSymMesh` (대칭/비대칭 블렌드셰이프
제작 툴, MEL 1229줄)이다. 기능은 유용하지만 **정점(vertex) 단위로 `xform` 명령을
하나씩 호출**하고 **대칭 매칭이 O(N²)** 이라, 정점이 많은 메시(수천~수만)에서는
"Select Base Geometry", "Mirror Selected", "Flip Selected" 등이 수 초~수십 초씩 걸린다.

목표: 동작/UI 는 그대로 유지하되, **`maya.api.OpenMaya` (OpenMaya 2.0) 의 벌크 정점
입출력**과 **더 나은 자료구조(공간 해시 / dict)** 로 다시 구현해 체감 속도를 크게
높인다. 코드는 레거시 단일 MEL 대신 `JUN_All` 의 **maya.cmds in-DCC 툴 패턴
(A00000_base)** 에 맞춰 Python 으로 포팅한다. (UI 문자열·로그는 영어, 주석은 한국어 가능.)

---

## 1. 현재 병목 분석 (origin.mel)

성능을 죽이는 3대 근본 원인:

| # | 근본 원인 | 위치 | 영향 |
|---|-----------|------|------|
| **R1** | **정점마다 `xform` 명령 1회 호출** (쿼리/세트 모두). MEL 명령 1건마다 파싱+DG 평가 비용. | 거의 모든 proc | 정점 수 N 에 비례하는 명령 디스패치 = 가장 큰 비용 |
| **R2** | **대칭 매칭이 O(N²)** — pos 정점마다 neg 정점 전체를 선형 탐색. 내부에서 `xform` 재쿼리까지. | `abCheckSym` 2번째 루프 (L154–197) | N=2만이면 ~2×10⁸ 비교 |
| **R3** | **`abGetSymVtx` 가 O(N) 선형 탐색** — 선택 정점마다 sym 테이블 전체를 훑음 → Mirror/Flip/SelMirror 가 O(M×N) | `abGetSymVtx` (L219–238) | Mirror Selected 의 실질적 킬러 |

부가 원인: 정점 인덱스를 매번 정규식 `match()` 로 파싱(R4), 이미 구한 좌표를 재쿼리(R5).

### 버튼별 매핑

| 버튼 (UI) | 핸들러 proc | 현재 복잡도 | 지배 비용 |
|-----------|-------------|-------------|-----------|
| **Select Base Geometry** `sbgBn` | `abCheckSym(...,bTable=1)` | **O(N²)** + N×xform | R2 + R1 |
| Check Symmetry `favBn` | `abCheckSym(...,bTable=0)` | **O(N²)** + N×xform | R2 + R1 |
| **Mirror Selected** `msBn` | `abMirrorSel(flip=0)` | **O(M×N)** + ~2M×xform | R3 + R1 |
| **Flip Selected** `fsBn` | `abMirrorSel(flip=1)` | **O(M×N)** + ~4M×xform | R3 + R1 |
| Selection Mirror `smBn` | `abSelMirror` | O(M×N) (xform 없음) | R3 |
| Select Moved Verts `smvBn` | `abSelMovedVerts` | O(N) + 2N×xform | R1 |
| Revert Selected `rsBn` / 슬라이더 | `abRevertSel` / `abSymInteractiveRevertToBase` | O(M) + ~3M×xform | R1 |
| Copy/Add/Subtract (메뉴) | `abSMAddSubtractCopyMesh` | O(N) + 4N×xform | R1 |
| `abSelSideVerts` (오브젝트 선택 시 보조) | — | O(N) + N×xform | R1 |

---

## 2. 핵심 개선 기법

1. **벌크 정점 I/O (R1 해결)** — `om.MFnMesh.getPoints(space)` 로 전체 좌표를 **한 번에**
   `MPointArray` 로 읽고, 계산 후 `setPoints(points, space)` 로 **한 번에** 쓴다.
   N×`xform` → 쿼리 1회 / 세트 1회. 월드=`om.MSpace.kWorld`, 오브젝트=`kObject`
   (원본의 `-ws`/`-os` 와 동일하게 매핑).
2. **대칭 테이블을 공간 해시로 빌드 (R2 해결)** — O(N²)→**O(N)**. 각 정점의 좌표를
   tol 격자로 양자화해 `dict[(rounded mirrored pos)] → index` 를 만들고, pos 정점의
   "거울 위치" 키를 조회해 짝을 찾는다. 결과는 **양방향 dict** `pair[i]=j, pair[j]=i`
   와 zero(대칭축 위) 정점 집합으로 저장.
3. **`abGetSymVtx` → dict 조회 (R3 해결)** — O(N) 선형 탐색을 **O(1)** dict lookup 으로.
   Mirror/Flip/SelMirror 가 O(M×N)→O(M).
4. **정점 인덱스 파싱 1회 (R4)** — 선택은 `cmds.filterExpand`/`cmds.ls -fl` 로 평탄화 후
   인덱스만 정수로 한 번에 추출(또는 OpenMaya 컴포넌트 이터레이터). 루프 내 정규식 제거.
5. **진행바 정책** — 벌크화 후 대부분 연산이 ms 단위라 progressWindow 불필요. 무거운
   순수 파이썬 루프(테이블 빌드)만 청크 단위 업데이트, 임계값은 기존 `$abSymProgBarThresh`
   대응 상수로 유지.

---

## 3. 재구현 아키텍처 (A00000_base 패턴)

`origin.mel` 은 보관용으로 남기고, 새 Python 패키지를 같은 폴더에 만든다.

```
A00180_abSymMesh/
├── origin.mel                 # 원본 보존(참고용, 미사용)
├── __init__.py                # from .launcher import run
├── launcher.py                # run(reload_module=False): DEV reload 후 build__()
├── __dragDrop_A00180.py        # 셸프 설치 + onMayaDroppedPythonFile (A00000_base 복제)
├── abSymMesh_v01.py           # UI 본체: class ...UI__ + build() + build__()  ← maya.cmds
├── utility.py
└── core/
    ├── __init__.py
    ├── mesh_io.py             # OpenMaya 2.0 벌크 get/set + 인덱스 유틸 (DCC I/O 전담)
    └── sym_core.py            # 대칭 테이블/미러/플립/리버트 수학 (가능한 한 cmds 비의존)
```

- **UI(`abSymMesh_v01.py`)** 는 maya.cmds 로 원본 레이아웃을 재현(`formLayout` 또는
  `columnLayout`). 버튼은 `JUN_button__.ButtonSpec/Buttons` 패턴, 색은
  `MOD_colorThem.ColorThemeRegistry`. 진입점 `build__()` **함수명 유지**(launcher 호출).
- **core 분리** — `core/` 는 정점 좌표 배열을 받고 새 좌표 배열을 돌려주는 순수 로직 중심.
  실제 씬 접근(getPoints/setPoints, 선택 조회)은 `mesh_io.py` 한 곳에 모은다.
- 상태(global) 정리: 원본의 `$abSymTable`, `$abSbg`, `$abAltSbg`, 리버트 캐시 테이블들을
  UI 클래스의 인스턴스 멤버(또는 모듈 싱글턴)로 옮긴다.

---

## 4. 버튼별 재구현 계획

### 4-1. Select Base Geometry (`abCheckSym` bTable, R2+R1) — 최우선
- `MFnMesh.getPoints(kWorld)` 로 전체 좌표 1회 취득.
- mid 계산: usePiv 면 pivot, 아니면 bbox 중앙(축).
- **공간 해시**: `bucket = round((x,y,z)/tol)`; pos/zero/neg 분류 후, 각 pos 정점의 거울
  버킷 `(2*mid-axis, 그대로)` 를 dict 에서 조회 → 짝 인덱스. 매칭 결과를
  `self.sym_pair`(양방향 dict) + `self.zero_verts` 로 저장.
- 비대칭 정점 수로 "symmetrical / not symmetrical" 메시지(영어). 버튼 enable 처리 유지.
- 기대: O(N²)+N×xform → **O(N) + 쿼리 1회**. 가장 큰 체감 개선.
- 견고성 옵션: tol 경계 흔들림 대비, 거울 버킷의 인접 ±1 버킷도 조회(필요 시).

### 4-2. Mirror Selected / Flip Selected (`abMirrorSel`, R3+R1)
- 선택 정점 인덱스 1회 파싱.
- 대상 메시 `getPoints` 1회 → 메모리 배열 `pts`.
- 각 선택 인덱스 `i`: `j = self.sym_pair.get(i)` (**O(1)**).
  - Mirror: `pts[j] = mirror(pts[i], mid, axis)`.
  - Flip: `pts[i], pts[j]` 둘 다 거울 위치로 스왑. zero 정점은 축 위치로/평면 반사.
- `setPoints(pts)` **1회** 적용.
- 기대: O(M×N)+다수 xform → **O(M) + 쿼리/세트 각 1회**.

### 4-3. 기타 버튼
- **Selection Mirror** `abSelMirror`: `sym_pair` dict 조회로 대칭 정점 이름 리스트 생성 후 `select`. (세트 없음)
- **Select Moved Verts** `abSelMovedVerts`: 두 메시 `getPoints` 1회씩, NumPy/순수 벡터 비교로 tol 초과 정점만 수집 → `select`.
- **Revert Selected** `abRevertSel` + **인터랙티브 슬라이더** `abSymInteractiveRevertToBase`:
  base/obj `getPoints` 1회, bias 보간을 벌크 계산 → `setPoints` 1회. 슬라이더 드래그는
  최초 1회만 캐시 구축(기존 로직 유지) 후 매 드래그마다 벌크 setPoints — **드래그 반응성 대폭 향상**.
- **Copy/Add/Subtract** `abSMAddSubtractCopyMesh`: base/source/target 3개 `getPoints`,
  오프셋 벌크 계산 → target `setPoints` 1회.
- **Check Symmetry** `favBn`: 4-1 과 동일 해시로 비대칭 정점만 반환·선택.
- `abSelSideVerts`(오브젝트 선택 시 한쪽 면 선택): `getPoints` 1회 + 벌크 분류.

---

## 5. Undo 전략 — **확정: (A) 인라인 Undo 커맨드 + 풀속도**

`MFnMesh.setPoints()` 는 빠르지만 기본적으로 Undo 에 안 잡히므로(원본 `xform` 은 잡힘),
작은 **API 2.0 플러그인 커맨드**를 툴에 내장해 Undo 를 보장한다.

- `core/undo_cmd.py` 에 `om.MPxCommand` 서브클래스 `abSymSetPoints` 구현:
  - 인자: 대상 메시 + 새 `MPointArray` + space.
  - `doIt()` 에서 기존 좌표를 `getPoints` 로 백업(old) 후 `setPoints`(new).
  - `isUndoable()=True`, `undoIt()` = old 복원, `redoIt()` = new 재적용.
  - 모듈에 `maya_useNewAPI = True` 선언, `initializePlugin/uninitializePlugin` 제공.
- 등록: `launcher.run()` 에서 `cmds.pluginInfo(..., q=True, loaded=True)` 로 확인 후
  미로딩 시 `cmds.loadPlugin(undo_cmd 경로)`. DEV reload 시 충돌 없게 idempotent 처리.
- 모든 벌크 정점 쓰기(Mirror/Flip/Revert/Copy·Add·Sub)는 이 커맨드를 경유 →
  **풀 속도 + Ctrl+Z 정상**. 단일 user 액션 = 단일 undo 스텝(`undoInfo` 청크).
- 슬라이더 드래그(인터랙티브 리버트)는 원본처럼 드래그 중 `undoInfo -swf off`,
  드래그 종료 시 1개 스텝으로 커밋.

---

## 6. Maya 2023 호환성 — **확인됨(이 설계의 모든 요소가 2023 지원)**

| 사용 요소 | Maya 2023 지원 | 비고 |
|-----------|----------------|------|
| `maya.api.OpenMaya` (API 2.0) | ✅ (2013+ 제공) | 본 설계의 기반 |
| `MFnMesh.getPoints() / setPoints(MPointArray, MSpace)` | ✅ | 벌크 정점 I/O |
| `MSpace.kWorld / kObject` | ✅ | `-ws`/`-os` 대응 |
| `MSelectionList`, `MItMeshVertex`, `MFnSingleIndexedComponent` | ✅ | 선택/컴포넌트 처리 |
| `om.MPxCommand` (+ `maya_useNewAPI=True`, `MFnPlugin`) | ✅ | (A) Undo 커맨드 |
| maya.cmds UI (`window`/`formLayout`/`button`/`floatSlider`/`popupMenu`/`menuItem`) | ✅ | 원본 MEL UI 와 동일 명령군 |
| **Python 3.9** (Maya 2022~2023.x 기본) | ✅ | 아래 주의 |

**Python 버전 주의**: Maya 2023 은 **Python 3.9** 다. 따라서 3.10+ 전용 문법은 금지:
- `match`/`case` 문 금지(원본의 switch 는 if/elif 로), `X | Y` 타입 유니온(런타임 평가
  맥락) 지양, 표준 typing 사용. f-string·dataclass 는 3.9 OK(기존 `A00000_base` 와 동일).
- (참고) Maya 2025+ 는 Python 3.11 이지만 위 제약만 지키면 2023↔최신 모두 동작.

> 결론: **계획대로 만들면 Maya 2023 에서 정상 동작**한다. 별도 폴백 코드 불필요.
> 메모리의 "no native sin/cos 노드" 이슈는 DG 노드 그래프 얘기로, 본 툴(파이썬 계산)과 무관.

## 6-b. 동작 동일성 / 기타 주의
- `-ws`(mirror/flip/check/side) vs `-os`(revert/moved/add-sub-copy) 공간 구분을 원본과 정확히 일치.
- tol 의미(.001 기본), usePiv / negToPos(Operate −X→+X) / 축(YZ·XZ·XY) 옵션을 1:1 보존.
- 기존 `origin.mel` 은 삭제하지 않고 참고용으로 보존.

---

## 7. 검증 (Verification)

Maya 에서(`tools.A00180_abSymMesh.run(True)` 또는 셸프 버튼):
1. **정합성** — 대칭 메시 + 비대칭 변형 메시로, 원본 MEL 과 새 Python 의 결과(미러/플립/리버트
   후 정점 위치, 비대칭 정점 선택)가 동일한지 같은 입력에서 비교.
2. **속도** — 저·중·고밀도 메시(예 1k / 1만 / 5만 정점)에서 Select Base / Mirror / Flip 의
   소요 시간을 원본 대비 측정(`timeit` 또는 간단 타이머 로그). 목표: 고밀도에서 수십 배 단축.
3. **Undo** — 채택한 전략(A/B)에 따라 Mirror/Flip/Revert 후 Ctrl+Z 동작 확인.
4. **엣지** — 비대칭 base 경고, zero(중앙) 정점 처리, 오브젝트 선택 vs 컴포넌트 선택 분기,
   usePiv on/off, 3축 각각, Operate −→+ 토글, alternate base, 슬라이더 드래그 반응성.
5. **회귀** — Copy/Add/Subtract, Select Moved(원본/alt base) 결과 일치.

---

## 8. 작업 순서(제안)

1. 폴더 스캐폴딩(A00000_base 복제) + `core/mesh_io.py` 벌크 get/set 유틸.
2. `core/sym_core.py` 대칭 테이블(공간 해시) + 미러/플립/리버트 수학.
3. UI 포팅(`abSymMesh_v01.py`) — 버튼/옵션/슬라이더/메뉴 재현, core 호출로 연결.
4. Undo 전략(A or B) 반영.
5. config 드래그&드롭 설치 + launcher reload.
6. 검증(7장) 후 버전/헤더 기록.
