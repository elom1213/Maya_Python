# A00140_ConnectClosest 사용법

## 1. 개요

여러 **driver** 오브젝트 각각에 대해 **위치가 가장 가까운 driven** 오브젝트 하나를 자동으로
찾아 **1:1로 매칭**하고, constraint로 연결하는 툴이다. 연결 후에는 **driver가 움직이면
driven이 따라 움직인다**.

- DCC: Autodesk Maya (PySide UI)
- 아키텍처: Standalone/Qt 앱 형식 (core 로직 ↔ ui 화면 분리)
- 연결 방향: `xxxConstraint(driver, driven)` — driver가 부모/컨트롤러, driven이 따라감.

---

## 2. 폴더 구조

```
A00140_ConnectClosest/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(): MainWindow 생성 → 테마 적용 → show()
├── __dragDrop_A00140.py                   # 셸프 버튼 설치 + 드래그&드롭 진입점
├── CHANGELOG.md
├── requirements.txt
└── app/
    ├── config/
    │   └── version.py          # VERSION / LAST_UPDATE
    ├── core/                   # 로직 (UI 비의존)
    │   ├── maya_scene.py       # maya.cmds 래퍼 (거리 계산, constraint 4종)
    │   └── closest_connector.py# 핵심 로직: 최근접 매칭 + 연결 + 입력 검증
    └── ui/
        └── main_window.py      # 2-리스트 + 체크박스 + Connect 버튼 + 로그창
```

- **core**(`maya_scene.py`, `closest_connector.py`)는 화면을 모르고, `MayaScene` 어댑터를 통해서만
  `maya.cmds`를 호출한다.
- **ui**(`main_window.py`)는 위젯 구성과 시그널 연결, 로그 출력만 담당하고 로직은 core에 위임한다.

---

## 3. 설치

`A00140_ConnectClosest/__dragDrop_A00140.py` 파일을 **Maya 뷰포트로 드래그&드롭**한다.
현재 셸프에 **`CnctClose`** 버튼이 설치된다(중복 버튼은 자동 제거 후 재설치).

---

## 4. 실행

- 설치된 셸프 버튼 **`CnctClose`** 클릭, 또는
- Maya Script Editor에서 직접 호출:

```python
import tools.A00140_ConnectClosest as A00140_ConnectClosest
A00140_ConnectClosest.run(True)
```

`run()`을 다시 호출하면 기존 창을 닫고 새로 띄운다(항상 최상위 표시).

---

## 5. UI 구성

```
┌ Help ──────────────────────────────────┐  ← 메뉴 바 (Help > About)
├ Set Up ────────────────────────────────┐
│ [Select Objects]      [Select Objects]  │
│ Driven   Number: N     Driver  Number: N │
│ ┌ QListWidget ┐       ┌ QListWidget ┐   │
│ │   driven    │       │   driver    │   │
│ └─────────────┘       └─────────────┘   │
│ Add|Del|Up|Down        Add|Del|Up|Down  │
│ [   Sort   ]           [   Sort   ]     │
├ Constraint Type ───────────────────────┤
│ ☑ Parent ☐ Point ☐ Orient ☐ Scale      │
│ ☑ Maintain Offset                       │
├────────────────────────────────────────┤
│              [   Connect   ]            │
├ Log ───────────────────────────────────┤
│ ┌ read-only 로그창 (영어 출력) ┐        │
│ └────────────────────────────────┘      │
└────────────────────────────────────────┘
```

- **Help > About**: 상단 메뉴 바. 클릭하면 툴 설명과 사용법이 담긴 팝업(`QMessageBox`)이 뜬다.
- **왼쪽 리스트 = Driven**, **오른쪽 리스트 = Driver**. 두 리스트는 재사용 PySide 위젯
  `Framework/qt/MOD_tsl_qt_v01.py`(`JUN_mod_tsl_qt_v01`)로 만들어진다.
- 각 리스트 버튼:
  - **Select Objects** — 현재 Maya 선택으로 리스트를 **교체**.
  - **Add** — 현재 선택을 **중복 없이 추가**(이미 있으면 로그에 안내).
  - **Del** — 리스트에서 선택한 항목 삭제.
  - **Up / Down** — 선택한 항목을 한 칸 위/아래로 이동.
  - **Sort** — 리스트를 이름순 정렬.
- 리스트 항목을 클릭하면 해당 오브젝트가 Maya 씬에서 선택된다.
- **Constraint Type**: `Parent / Point / Orient / Scale` **체크박스(다중 선택)**. 기본값은 **Parent** 체크.
- **Maintain Offset**: 체크하면 현재 오프셋을 유지한 채 연결(기본 체크).
- **Connect**: 매칭 + 연결 실행.
- **Log**: 모든 결과/경고를 **영어**로 출력하는 읽기 전용 창.

---

## 6. 사용 순서

1. driven으로 쓸 오브젝트들을 Maya에서 선택 → **Driven 컬럼의 Add**(또는 Select).
2. driver로 쓸 오브젝트들을 선택 → **Driver 컬럼의 Add**(또는 Select).
3. 적용할 **Constraint Type** 체크박스를 하나 이상 선택.
4. 필요하면 **Maintain Offset** 체크.
5. **Connect** 클릭. 결과가 로그창에 출력된다.

---

## 7. 동작 규칙

- **1:1 매칭**: driver 하나가 가장 가까운 driven을 가져가면, 그 driven은 후보 풀에서 **제외**된다.
  다음 driver는 남은 driven 중에서 가장 가까운 것을 고른다. (같은 driven이 중복 연결되지 않음)
- **거리 기준**: 월드 좌표상의 직선 거리(translation)로 비교한다.
- **연결 방향**: 선택된 constraint마다 `cmds.xxxConstraint(driver, driven, mo=...)`로 생성 →
  driven이 driver를 따라간다.
- **다중 constraint**: 체크된 종류만큼 각각의 constraint 노드가 생성된다(예: Parent + Scale 동시).
- **driver 수 > driven 수**: 짝이 부족하면 일부 driver는 연결되지 않고 `[WARN]` 경고가 출력된다.
- 씬에 존재하지 않는 오브젝트는 자동으로 건너뛰고 경고를 남긴다.

---

## 8. 로그 · 문제 해결

### 정상 로그 예시
```
--- Connect Closest ---
Connected: pCube1 -> pSphere3 (dist 1.420, Parent)
Connected: pCube2 -> pSphere1 (dist 0.875, Parent, Scale)
Done. 2 connection(s) made.
```
형식: `Connected: <driver> -> <driven> (dist <거리>, <적용된 constraint들>)`

### 경고 메시지(`[WARN]`)와 의미
- `No driver objects. ...` — Driver 리스트가 비어 있음.
- `No driven objects. ...` — Driven 리스트가 비어 있음.
- `No constraint type selected. ...` — 체크박스를 하나도 선택하지 않음.
- `Driver/Driven not found in scene, skipped: <이름>` — 씬에 없는 오브젝트(이름 변경·삭제 등).
- `More drivers (N) than drivens (M); K driver(s) will be left unconnected.` — driver가 더 많아 일부 미연결.
- `<Type> constraint failed (<driver> -> <driven>): <error>` — 해당 constraint 생성 중 Maya 오류.

### 자주 겪는 문제
- **아무 일도 일어나지 않음** → 리스트가 비었거나 체크박스 미선택. 로그의 `[WARN]` 확인.
- **원하지 않은 매칭** → 1:1 + 거리 기준이므로, driver/driven의 위치를 확인하거나 리스트 구성을 조정한다.
- **이미 있는 항목 추가** → `<이름> is already in the list.` 로그가 뜨며 중복은 추가되지 않는다.
