# A00180_abSymMesh 사용법

## 1. 개요

폴리곤 메시의 **대칭/비대칭 블렌드셰이프 제작**을 돕는 **PySide(Qt) 툴**이다. 메시의 대칭을
검사하고, 선택한 정점을 **미러 / 플립 / 리버트**하며, 두 블렌드셰이프를 **복사 / 더하기 / 빼기**할
수 있다. Brendan Ross 의 고전 MEL 스크립트 `abSymMesh`(2008, `origin.mel`)를 동작은 유지하면서
**속도를 크게 높여** Python / OpenMaya 2.0 으로 재구현했고, UI 는 PySide 로 작성했다.

- **벌크 정점 입출력**: 정점마다 `xform` 을 호출하던 원본과 달리 `MFnMesh.getPoints/setPoints`
  로 전체 좌표를 한 번에 읽고 쓴다.
- **대칭 테이블**: O(N²) 매칭 + 선형 탐색을 **공간 해시 O(N) + dict O(1) 조회**로 대체.
- **Undo**: 모든 정점 편집은 Undo 가능 커맨드(`abSymSetPoints`)를 경유 → **Ctrl+Z** 정상.
- **UI**: PySide(`Framework.qt.qt` 가 PySide6→PySide2 폴백). 테마는 `ThemeManager` 의 `yellow_dark` qss.
- **Maya 2023 호환** (Python 3.9 / PySide2 / OpenMaya 2.0). UI 문자열/로그는 모두 영어.

> **전제**: 미러/플립/리버트는 **base 메시와 동일한 정점 순서(토폴로지)**를 가진 메시에서 동작한다.
> 대칭 메시로 base 를 잡은 뒤, 그 복제본(블렌드셰이프 타겟)에 기능을 적용하는 방식이다.

---

## 2. 폴더 구조

```
A00180_abSymMesh/
├── origin.mel            # 원본 MEL (참고용 보존, 미사용)
├── __init__.py           # from .launch import run
├── launch.py             # run(): DEV reload + undo 플러그인 로드 → MainWindow show
├── config.py             # DEV_MODE + 셸프 버튼 설치 / 드래그&드롭 진입점
└── app/
    ├── config/version.py # VERSION / LAST_UPDATE
    ├── core/             # 로직 (씬 비의존 + 씬 I/O 분리) — UI 와 무관, 재사용
    │   ├── mesh_io.py        # OpenMaya 벌크 getPoints/setPoints, 선택/좌표 유틸, 플러그인 로드
    │   ├── sym_core.py       # 공간 해시 대칭 + 미러/플립/리버트/카피 수학 (순수 계산)
    │   ├── undo_bridge.py    # 플러그인 ↔ 툴 staging (PENDING 페이로드 단일 객체 공유)
    │   └── undo_cmd.py       # MPxCommand 플러그인 (abSymSetPoints, Undo 가능 setPoints)
    └── ui/main_window.py # 전체 UI (PySide) + 핸들러 (MainWindow)
```

- **로직(app/core)과 UI(app/ui/main_window.py)를 분리**한다. 씬 접근(getPoints/setPoints,
  선택 조회)은 `mesh_io` 한 곳에 모으고, 대칭/미러 수학은 `sym_core` 가 좌표 배열만으로 처리한다.
  UI 를 maya.cmds → PySide 로 재작업할 때 `app/core` 는 그대로 재사용했다.

---

## 3. 설치

`A00180_abSymMesh/config.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
"abSymMesh" 버튼이 설치된다(중복 버튼은 자동 제거).

---

## 4. 실행

- 셸프 버튼 클릭, 또는 스크립트 에디터에서:
  ```python
  import tools.A00180_abSymMesh as A00180_abSymMesh
  A00180_abSymMesh.run(True)   # True 면 DEV_MODE 에서 자기 자신 + Framework reload 후 실행
  ```
- 창은 `objectName`(`JUN_A00180_abSymMesh_window`)으로 관리되어 재실행 시 중복 없이 교체된다.
- 실행 시 Undo 커맨드 플러그인(`app/core/undo_cmd.py`)이 자동 로드된다. 미로드 상태에서
  편집을 시도해도 `mesh_io.ensure_undo_plugin()` 이 사용 직전에 자가 로드한다.

---

## 5. UI 구성

| 요소 | 의미 |
|------|------|
| **YZ / XZ / XY** (라디오) | 대칭(미러) 평면. YZ→X축, XZ→Y축, XY→Z축 기준. 바꾸면 base 가 해제된다. |
| **Global Tolerance** | 대칭/이동 판정 허용 오차(기본 `0.001`). |
| **Select Base Geometry** | 선택 메시로 대칭 테이블을 만든다. 아래 다른 기능들의 기준. |
| (base 표시 필드) | 현재 base 메시 이름(읽기 전용). |
| **Check Symmetry** | 선택 메시의 **비대칭 정점**을 선택해 보여준다(base 불필요). |
| **Selection Mirror** | 선택 정점의 **대칭 정점**으로 선택을 바꾼다(편집 아님). |
| **Select Moved Verts** | base 대비 위치가 바뀐 정점을 선택. |
| **Mirror Selected** | 선택 정점(또는 한쪽 면)을 반대쪽으로 **미러**한다. |
| **Flip Selected** | 선택 정점을 좌우 **플립**(스왑)한다. |
| **Revert Selected to Base** | 선택 정점을 base 위치로 되돌린다. 우클릭 시 % 단위 리버트. |
| (Revert 슬라이더) | 드래그로 선택 정점을 base 로 **실시간** 보간(0=base, 1=현위치). |
| **Operate -X to +X** | 미러/플립 시 음(−)축 → 양(+)축 방향으로 소스 면을 잡는다. 라벨은 축에 따라 변함. |
| **Use Pivot as Origin** | 체크(기본)면 오브젝트 pivot 을 대칭축 원점으로, 해제면 월드 원점/bbox 중앙을 쓴다. |
| **Close** | 창 닫기. |
| **Operations 메뉴** | Copy A→B / Add A→B / Subtract A from B (두 메시 선택). |
| (Revert 슬라이더 우클릭) | Use Selected as Base / Use Original Base / Select Moved from Revert Base. |

---

## 6. 사용 순서

1. **대칭인 메시**를 선택하고 **Select Base Geometry** 클릭 → 대칭 테이블 생성.
   대칭이 아니면 경고가 뜬다(그래도 매칭된 정점에 한해 동작).
2. 같은 정점 순서를 가진 **복제(타겟) 메시**를 선택한다.
   - **오브젝트 전체** 선택: 미러/플립/리버트가 자동으로 한쪽 면(또는 전체) 정점에 적용된다.
   - **정점(컴포넌트)** 선택: 선택한 정점에만 적용된다.
3. 원하는 기능 클릭: **Mirror Selected** / **Flip Selected** / **Revert Selected to Base**.
4. (선택) 블렌드셰이프 합성: base 를 잡은 상태에서 source·target 두 메시를 선택하고
   **Operations 메뉴**의 Copy / Add / Subtract 사용.

각 편집은 `cmds.undoInfo(openChunk/closeChunk)` 로 묶여 **Ctrl+Z 한 번**에 취소된다.

---

## 7. 블렌드셰이프 합성 — Copy / Add / Subtract

**Operations 메뉴**의 세 항목은 base 와 같은 정점 순서를 가진 두 메시 사이에서 **블렌드셰이프 델타**
(= 한 메시가 base 로부터 변형된 양)를 복사·합성·제거한다. 모두 정점별로, **오브젝트 공간**에서 계산한다.
(`app/core/sym_core.py: add_sub_copy_points`)

**전제 / 선택 규칙**
- 먼저 **Select Base Geometry** 로 base(중립 메시)를 잡아야 한다.
- 이어서 **메시 두 개**를 선택한다: **먼저 선택한 메시 = A(source)**, **두 번째 = B(target)**.
- 둘 다 base 와 정점 수(토폴로지)가 같아야 하고, base 자체는 A/B 로 쓸 수 없다.
- 결과는 **B(두 번째 메시)에만 기록**된다(A·base 는 변하지 않으며 Undo 가능).
- 델타 정의: `offset = A − base`(정점별 좌표 차). 이는 A 블렌드셰이프의 "형상 변화"에 해당한다.

| 메뉴 | 수식(정점별) | 의미 |
|------|--------------|------|
| **Copy A to B** | `B = A` | B 정점을 A 좌표로 그대로 덮어쓴다(base 는 선택/토폴로지 검증에만 쓰이고 계산엔 들어가지 않음). A 형상을 B 로 복제. |
| **Add A to B** | `B = B + (A − base)` | A 가 base 로부터 변형된 양을 B 에 **더한다**. A 의 형상 변화를 B 에 누적/합성. |
| **Subtract A from B** | `B = B − (A − base)` | A 의 base 대비 변형을 B 에서 **뺀다**. B 에 섞여 있던 A 의 형상 기여를 제거. |

> 예: 중립 얼굴(base)과 "미소"(A), 그리고 "미소+찡그림"이 섞인 메시(B)가 있을 때,
> **Subtract A from B** 하면 B 에서 미소 성분이 빠져 "찡그림"만 남는다. 반대로 **Add** 는 형상을 합친다.
> **Copy** 는 델타가 아니라 A 의 절대 좌표를 그대로 옮긴다.

---

## 8. 동작 규칙

- **대칭 매칭**: 각 정점 좌표를 tolerance 격자로 양자화해 공간 해시를 만들고, 양(+)쪽 정점의
  거울 위치를 음(−)쪽 해시에서 조회해 짝을 찾는다(O(N)). 짝은 양방향 dict 로 보관해
  미러/플립에서 O(1) 로 조회한다.
- **대칭 평면(mid)**: **Use Pivot** 체크면 오브젝트 pivot, 해제면 — Select Base 는 bounding box
  중앙, Check Symmetry 는 월드 원점(0), 미러/플립의 대상 메시는 월드 원점을 기준으로 한다
  (원본 MEL 규칙 그대로).
- **공간**: 미러/플립/대칭검사/면선택은 **월드 공간**, 리버트/이동검사/Copy·Add·Subtract 는
  **오브젝트 공간**으로 계산한다.
- **중앙(zero) 정점**: 대칭 평면 위 정점은 미러 시 평면으로 스냅, 플립 시 평면 반사된다.
- **NaN/inf 정점**: 좌표가 비정상인 정점은 매칭에서 제외(비대칭으로 남김)하고 경고한다.
  메시 정리(`Mesh > Cleanup`) 후 다시 base 를 잡으면 된다.

---

## 9. 로그 · 문제 해결

- **"Base geometry is symmetrical"** — Select Base 성공, 전 정점이 대칭.
- **"Base geometry is not symmetrical, not all vertices can be mirrored"** — 일부 정점만 매칭됨.
  tolerance 를 키우거나(미세 비대칭) 메시 대칭을 확인한다.
- **"N vertex(es) ... have invalid (NaN/inf) coordinates ..."** — 깨진 정점 존재.
  **Check Symmetry** 로 해당 정점 위치를 확인하고 메시를 정리한다.
- **"No Base Geometry Selected"** — 미러/플립/Selection Mirror 전에 Select Base 가 필요하다.
- **"Failed to load the undo command plugin: ...app/core/undo_cmd.py"** — 플러그인 로드 실패.
  새 씬에서 재실행하거나 메시지 전문을 확인한다. (참고: loadPlugin 으로 로드되는 `.py` 에는
  `__file__` 이 없으므로 플러그인은 경로를 `__file__` 로 계산하지 않는다.)
- **속도** — 정점이 많은 메시(수천~수만)에서 원본 MEL 대비 Select Base / Mirror / Flip 이
  크게 빨라진다(벌크 I/O + O(N) 해시).
