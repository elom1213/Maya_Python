# A00060_jointTool_V02 — Joint Tool (사용 안내)

MEL `JointTool V05.03`(탭: Curve / Divide / Aim)와 기존 `A00060_jointTool`(헤어 커브용 조인트 유틸)을
하나로 합친 툴이다. **UI 는 PySide(Qt)**, 로직은 `maya.cmds` 로 작성되었다.

- 버전: `v01.00` (`app/config/version.py`)
- 위치: `JUN_All/tools/A00060_jointTool_V02`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴(`QTabWidget` 4탭)
- 원본 `A00060_jointTool` / MEL 파일은 그대로 보존(미수정)

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00060_V02.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`JointTool2`** 버튼 설치.
이후 셸프 버튼 클릭으로 실행된다.

### 코드로 실행
```python
import tools.A00060_jointTool_V02 as A00060_jointTool_V02
A00060_jointTool_V02.run(True)   # True 면 DEV_MODE 에서 reload 후 실행
```

> `config.py` 의 `DEV_MODE = True` 일 때 `run(True)` 는 자기 패키지 + Framework 만 reload 한다.
> 창은 `objectName` 으로 식별되어 재실행 시 기존 창을 닫고 새로 띄운다(창 누적 없음).

---

## 2. 공통 UI

- 상단 **Help > About** 메뉴: 버전/작성자/업데이트 일자.
- 하단 **로그창**: 모든 작업 결과가 `[OK]` / `[ERR]` 로 표시된다.
- 모든 작업은 **undo chunk** 로 감싸져 한 번의 Ctrl+Z 로 되돌릴 수 있다.
- 각 리스트는 재사용 위젯 `JUN_mod_tsl_qt_v01`:
  - **Select** : 현재 씬 선택으로 리스트 교체
  - **Add / Del** : 현재 선택 추가(중복 무시) / 선택 항목 제거
  - **Up / Down** : 선택 항목 순서 이동
  - 리스트 항목 클릭 시 해당 노드를 씬에서 선택
  - 우측 상단 `Number:` 에 항목 수 표시
- 접이식 프레임(▼/▶ 헤더)을 눌러 각 도구 그룹을 펼치거나 접을 수 있다(MEL `frameLayout -collapsable` 대응).

---

## 3. 탭별 사용법

### 3.1 Curve 탭 (MEL Tab 1)
리스트(`Selections`)에 **NURBS 커브** 또는 **조인트**를 담아 사용한다.

- **Tool : joint to Crv** — 리스트의 커브를 따라 조인트 생성
  - 포인트 종류 라디오:
    - `Control Vertex (Omit [1], [-2])` : CV 사용하되 두 번째·끝에서 두 번째 CV 생략
    - `Control Vertex` : 모든 CV
    - `Edit Point` : 에디트 포인트
  - `Joints to Crv` : 위 옵션으로 조인트 생성
  - `Clusters` : 커브 CV마다 클러스터 생성
- **Tool : joint to obj** — 리스트의 오브젝트 위치마다 조인트 생성
  - `Connect` : 조인트들을 체인으로 연결 / `Separate` : 각각 분리(루트)
  - `Foward axis` / `Secondary axis` / `Secondary axis orient` : orient 축 옵션
  - `Match to Obj` : 실행
- **Tool : joint orient and rotate** — 리스트 조인트에 대해
  - `joint orient to rotate` : jointOrient 값을 0으로, rotate 에 합산
  - `rotate to joint orient` : 반대로 합산
- **Tool : Set Orient** (기본 접힘) — 선택 축의 `jointOrient` 를 입력 각도로 설정
  - `Orient axis` / `Orient degree` → `Set joints orientation`
  - 내부적으로 체인을 역순 unparent → 설정 → 정순 reparent 한다(리스트는 root→end 순서여야 함).

### 3.2 Divide 탭 (MEL Tab 2)
시작/끝 오브젝트 쌍 사이를 직선 커브로 잇고, 그 길이를 균등 분할해 조인트를 만든다.

- `Start` / `End` 리스트(좌우)
- `Select Start End` : 현재 선택 순서로 (sel[0]~sel[n-2]) = Start, (sel[1]~sel[n-1]) = End 자동 구성
- `Add Start End` : **정확히 2개** 선택 → 첫째를 Start, 둘째를 End 리스트에 추가
- `Joints Number` : 쌍마다 생성할 조인트 수 → `Make Joint Divided`
- Start/End 리스트의 항목 수는 같아야 한다.

### 3.3 Aim 탭 (MEL Tab 3)
조인트 체인의 시작/끝과 폴 타깃으로 ikHandle + poleVector 구속을 만든다.

- `Start` / `End` / `pole tgt` 리스트(3분할)
- `Select Start End` / `Add Start End` : Start·End 채우기(Divide 탭과 동일 규칙)
- `Make Joint Aim` : 쌍마다 `ikHandle(sj=Start, ee=End)` 생성 후 폴 타깃으로 `poleVectorConstraint`

### 3.4 Hair 탭 (기존 A00060_jointTool)
헤어 커브 정리 및 조인트 편집 유틸.

- 리스트(`Joint Tool`)에 커브/조인트를 담는다.
- **Sub Tool : Curve**
  - `Separate Curve` : 각 커브 shape 를 개별 transform(`hairCrv`)으로 분리
  - `Max Length` + `Remove Curve` : 길이가 값 이하인 커브 삭제
  - `Interval` + `Max joints` + `Rebuild Curve` : 길이/간격 기반 span 산정해 rebuild(최대 span = Max joints − 1)
- **Tool : Edit**
  - `Remove origin` 체크 : 켜면 원본 체인 삭제 + `_rev` 접미사 제거
  - `Reverse joint chain` : 리스트의 root 조인트 체인을 위치/radius 유지하며 역순 재생성
  - `Select Unused Joints` : 리스트 조인트 중 skinCluster 에 쓰이지 않는 것을 선택

---

## 4. 구조 (개발자용)

```
A00060_jointTool_V02/
├── __init__.py                     # run 노출
├── launch.py                       # run(): reload → MainWindow → coral_dark 테마 → show
├── __dragDrop_A00060_V02.py        # 셸프 버튼 설치 (고유 파일명)
├── requirements.txt
└── app/
    ├── config/version.py           # VERSION / LAST_UPDATE
    ├── core/                       # UI 비의존 maya.cmds 로직
    │   ├── curve_joint_manager.py  # Curve 탭 (joint to Crv / Clusters)
    │   ├── obj_joint_manager.py    # Curve 탭 (joint to obj / orient / swap)
    │   ├── divide_manager.py       # Divide 탭
    │   ├── aim_manager.py          # Aim 탭
    │   └── hair_manager.py         # Hair 탭 (A00060 이식)
    └── ui/
        ├── collapsible.py          # CollapsibleBox (frameLayout -collapsable 대응)
        └── main_window.py          # QTabWidget 4탭 + 공유 로그 + Help>About
```

- `core`(로직)와 `ui`(화면)를 분리: UI 가 위젯에서 값을 읽어 매니저에 넘기고, 결과로 리스트/로그를 갱신한다.
- 리스트 위젯은 `Framework.qt.JUN_mod_tsl_qt` 재사용. 색상은 `coral_dark` qss 테마.
- PySide2/PySide6 양립을 위해 UI 는 `from Framework.qt.qt import *` 만 사용한다.

### MEL → Python 포팅 매핑(요약)

| MEL proc | 이식 위치 |
|----------|-----------|
| `JUN_cmd_create_joints_toCrv` / `JUN_cmd_create_clusters_toCrv` | `curve_joint_manager` |
| `JUN_cmd_create_joints_toObj` / `JUN_cmd_joint_swap_rotate` / `JUN_cmd_set_jntOri` | `obj_joint_manager` |
| `JUN_cmd_makeJnt_divide` / `JUN_cmd_selStrEnd` / `JUN_cmd_addStrEnd` | `divide_manager` |
| `JUN_cmd_make_jntAim` | `aim_manager` |
| 리스트 Select/Add/Del/Up/Down (`JUN_cmd_*` TSL 군) | `JUN_mod_tsl_qt_v01` 내장 |

> 동작은 MEL V05.03 과 동일하게 유지했다(좌표 보정·축 인덱스 계산 등 원본 로직 그대로 이식).

---

## 5. 참고 / 주의

- 작업 대상은 **씬 선택이 아니라 각 탭의 리스트에 담긴 항목**이다(먼저 Select/Add 로 리스트에 올릴 것).
- Set Orient / Reverse 는 리스트 순서가 체인 순서(root→end)와 일치해야 한다.
- 원본 `A00060_jointTool` 의 카피 흔적(`config.py`/dragDrop 의 `A00040_file_exporter` 식별자)은
  V02 에 가져오지 않았다 — 모든 식별자는 `A00060_jointTool_V02` 로 일관.
