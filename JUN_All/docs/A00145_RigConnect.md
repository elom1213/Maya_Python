# A00145_RigConnect — RigConnect (사용 안내)

MEL `ConnectionTool V04.02`(탭: Constrain / Connect / List Connected)와 기존
`A00140_ConnectClosest`(최근접 1:1 constraint)를 하나로 합친 툴이다.
**UI 는 PySide(Qt)**, 로직은 `maya.cmds` 로 작성되었다.

- 버전: `v01.00` (`app/config/version.py`)
- 위치: `JUN_All/tools/A00145_RigConnect`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴(`QTabWidget` 4탭)
- 원본 `A00140_ConnectClosest` / MEL 파일은 그대로 보존(미수정)

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00145.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`RigConnect`** 버튼 설치.
이후 셸프 버튼 클릭으로 실행된다.

### 코드로 실행
```python
import tools.A00145_RigConnect as A00145_RigConnect
A00145_RigConnect.run(True)   # True = DEV_MODE 면 reload 후 실행
```

---

## 2. 탭 구성

### Constrain
타겟(드라이버) → 팔로워로 constraint 를 건다.

- `Targets` / `Followers` 리스트에 오브젝트 추가(Select/Add/Del/Up/Down).
- Options: `Maintain Offset` 체크 + constraint 종류 라디오
  (`Parent` / `Scale` / `Point` / `Orient` / `Point On Poly`).
- `Constrain` 클릭.
- **브로드캐스트**: target 이 1개면 모든 follower 에 동일 target 적용, 아니면 인덱스 1:1.

### Connect
어트리뷰트를 source → destination 으로 연결한다.

- Source/Destination 각 섹션:
  - `Objects` 리스트에 오브젝트 추가 → `List Attributes` 로 첫 오브젝트의 어트리뷰트를 우측 목록에 채움.
  - `search` 입력 + `Search`: 현재 목록에서 일치 항목을 **선택**하고, 없으면 검색어로 어트리뷰트를 다시 질의.
  - 우측 어트리뷰트 목록에서 연결할 항목을 **선택(다중 가능)**.
- `Connect Source to Destination`: 선택된 src/dst 어트리뷰트 수에 따라 3가지 패턴으로 연결.
  1. src obj 1개 & src/dst attr 수 동일 → 한 src 를 각 dst obj 의 attr 별로
  2. src/dst attr 각각 1개 → obj 쌍 1:1
  3. src/dst attr 수 동일 → obj 쌍 × attr 모두
- `Connect 52 Facial Target`: 52 ARKit 페이셜 어트리뷰트를 같은 이름끼리 obj 쌍 1:1 로 일괄 연결(없는 attr 은 스킵).

### List Connected
노드 그래프(up/down stream)를 타입별로 탐색한다.

- `Objects` 리스트에 오브젝트 추가.
- `List UpStream` / `List DownStream`: 연결된 노드의 **타입 목록**을 `Types` 에 표시.
- `Types` 에서 타입 선택 후 `Search`: 해당 타입의 **노드들**을 `Nodes` 에 표시.
- `Nodes` 목록에서 항목을 선택하면 씬에서도 선택된다.

### Connect Closest
각 driver 에 대해 가장 가까운 driven 을 1:1 매칭해 constraint 로 연결한다(A00140 이식).

- `Driven` / `Driver` 리스트 구성.
- constraint 종류 체크박스(`Parent` / `Point` / `Orient` / `Scale`, 다중) + `Maintain Offset`.
- `Connect`: 월드 좌표 유클리드 거리 기준 최근접 매칭. 각 driven 은 한 번만 사용.

---

## 3. 구조 (개발자용)

```
A00145_RigConnect/
├── launch.py                       # run(): MainWindow + coral_dark 테마
├── __dragDrop_A00145.py            # 셸프 설치 (RigConnect)
└── app/
    ├── config/version.py
    ├── core/                       # UI 비의존 maya.cmds 로직
    │   ├── constrain_manager.py    # Constrain  (MEL 포팅)
    │   ├── connect_manager.py      # Connect    (MEL 포팅: attr 나열/검색/연결, 52 facial)
    │   ├── stream_manager.py       # List Connected (MEL 포팅: hyperShade up/down)
    │   ├── maya_scene.py           # Connect Closest (A00140 복사)
    │   └── closest_connector.py    # Connect Closest (A00140 복사)
    └── ui/
        ├── collapsible.py          # CollapsibleBox
        └── main_window.py          # QTabWidget 4탭 + 공유 로그 + Help>About
```

- 모든 textScrollList 는 `Framework.qt.JUN_mod_tsl_qt_v01` 위젯으로 대체.
- `app/core`(로직) ↔ `app/ui`(화면) 분리. 위젯은 값만 읽어 매니저에 전달.
- UI 문자열은 영어, 한국어는 주석/독스트링만.
