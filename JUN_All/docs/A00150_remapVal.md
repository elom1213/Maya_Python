# A00150_remapVal 사용법

## 1. 개요

여러 오브젝트(주로 조인트)의 어트리뷰트를 **마스터 remapValue 커브 하나로 보간(slerp ramp)** 하는
셋업을 만드는 툴이다. 하나의 마스터 remapValue 가 여러 개의 remapValue 를 구동해서
"multi-out 커브" 효과를 흉내낸다. 원래 트위스트 리본 IK용으로 작성됐지만, 임의의 어트리뷰트에
적용할 수 있다.

- 원본 로직: `sample_01.py` 의 `build_slerp_ramp` (Chris Lesage, 2019).
- DCC: Autodesk Maya (PySide UI). 노드 생성은 **pymel** 사용.
- UI는 `A00090_ConnectionBuilder`(QLineEdit+Get)와 `01_Modules/JUN_PY_numberTool`(소스+어트리뷰트 2-리스트)
  구성을 참고했다.

---

## 2. 폴더 구조

```
A00150_remapVal/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마 적용 → show()
├── config.py              # 셸프 버튼 설치 + 드래그&드롭 진입점
├── CHANGELOG.md
├── requirements.txt
├── sample_01.py           # 원본 참고 코드(보존)
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직
    │   ├── slerp_ramp.py  # add_attr / build_slerp_ramp(원본 이식) + run_build(이름→PyNode 래퍼)
    │   └── maya_scene.py  # cmds 보조 래퍼 (selection / list_keyable_attrs / exists)
    └── ui/main_window.py  # 전체 UI
```

- **노드 생성 본체**(`slerp_ramp.py`)는 pymel을 쓰고, **UI 보조**(선택·어트리뷰트 나열)는 `maya.cmds`
  (`maya_scene.py`)를 쓴다. UI는 pymel을 직접 다루지 않고 `run_build(...)`만 호출한다.

---

## 3. 설치

`A00150_remapVal/config.py` 를 Maya 뷰포트로 **드래그&드롭** → 셸프에 **`RemapVal`** 버튼 생성.

---

## 4. 실행

- 셸프 버튼 **`RemapVal`** 클릭, 또는 Script Editor에서:

```python
import tools.A00150_remapVal as A00150_remapVal
A00150_remapVal.run(True)
```

---

## 5. UI 구성

```
┌ Help ───────────────────────────────────┐  ← 메뉴 바 (Help > About)
│ Main Controller [ QLineEdit        ] [Get]│
│ Prefix          [ twist            ]      │
├ Set Up ──────────────────────────────────┤
│ [Joints]                [Attributes]      │
│ Select Objects          List Attributes   │
│ ┌ QListWidget ┐         ┌ QListWidget ┐   │
│ │  joints     │         │ rotateX...  │   │
│ └─────────────┘         └─────────────┘   │
│ Add|Del|Up|Down|Sort    Del|Up|Down|Sort  │
│ Attr Search [ token        ] [Search]     │
├──────────────────────────────────────────┤
│                [   Build   ]              │
├ Log ─────────────────────────────────────┤
│ ┌ read-only 로그창 (영어 출력) ┐          │
│ └────────────────────────────────┘        │
└──────────────────────────────────────────┘
```

- **Help > About**: 툴 설명·사용법 팝업.
- **Main Controller** = `build_slerp_ramp`의 `controlObj`. `Get`을 누르면 현재 Maya 선택의 첫 오브젝트가 채워진다. 보간을 제어하는 어트리뷰트들이 이 컨트롤러에 추가된다.
- **Prefix** = 함수 첫 인자(기본 `twist`). 생성되는 노드/어트리뷰트 이름의 접두사로 쓰여 이름 충돌을 막는다.
- **Joints** (좌측, 재사용 위젯 `JUN_mod_tsl_qt_v01`) = `oColl`. 보간 대상 오브젝트들. Select/Add/Del/Up/Down/Sort.
- **Attributes** (우측, 재사용 위젯) = `twistAttrs`. **List Attributes** 버튼이 Joints 리스트 **첫 오브젝트**의 keyable 어트리뷰트(rotateX/Y/Z, scaleX/Y/Z 등)를 채운다. 여기서 **하나 또는 여러 개**를 선택한다.
- **Attr Search**: 토큰(예: `rotate`)을 포함하는 어트리뷰트를 리스트에서 선택해 준다(어트리뷰트가 많을 때 편리).
- **Build**: 셋업 생성 실행. 전체가 **하나의 Undo 청크**로 묶여 Ctrl+Z 한 번에 취소된다.
- **Log**: 결과/경고를 영어로 출력하는 읽기 전용 창.

---

## 6. 사용 순서

1. 컨트롤러로 쓸 오브젝트를 선택 → **Get** (Main Controller 채움).
2. 보간할 조인트들을 선택 → Joints 리스트의 **Add**.
3. **List Attributes** 클릭 → 채워진 어트리뷰트에서 적용할 것(예: `rotateY`)을 하나 이상 선택.
   (필요하면 Attr Search로 빠르게 선택)
4. **Prefix** 입력(기본 `twist`).
5. **Build** 클릭. 로그에 생성된 마스터 노드와 적용 결과가 출력된다.

---

## 7. 동작 규칙

- 생성되는 마스터 노드: `{prefix}_master_ribbon_lerp_MAP` (remapValue). 조인트 개수만큼
  `{prefix}_lerp_profile_{i}_MAP` 등이 생성되어 마스터 커브에 연결된다.
- 컨트롤러에 추가되는 제어 어트리뷰트: `{prefix}_start`, `{prefix}_end`,
  `{prefix}_start_position`, `{prefix}_end_position`, `{prefix}_interpolation`.
- Attributes는 **선택된 항목**만 적용된다(리스트에 있어도 선택 안 하면 미적용).
- Build 전체가 **단일 Undo 청크** — Ctrl+Z 한 번으로 생성 노드 전부 취소.

---

## 8. 로그 · 문제 해결

### 정상 로그 예시
```
--- Build Slerp Ramp ---
Listed 18 keyable attribute(s) from joint1.
Built: twist_master_ribbon_lerp_MAP | 5 joint(s) | attrs: rotateY
```

### 경고/오류 메시지
- `[WARN] Nothing selected. ...` — Get 시 선택이 없음.
- `[WARN] Joints list is empty. ...` — List Attributes/Build 전에 조인트를 추가해야 함.
- `[WARN] Main Controller is empty. ...` — 컨트롤러 미설정.
- `[WARN] Controller not found in scene: <name>` — 입력한 컨트롤러가 씬에 없음.
- `[WARN] No attribute selected. ...` — 어트리뷰트를 선택하지 않음.
- `[ERROR] Build failed: <error>` — pymel 노드 생성 중 오류(이름 오타, 존재하지 않는 어트리뷰트 등).

### 자주 겪는 문제
- **List Attributes에 아무것도 안 뜸** → Joints 리스트가 비었거나 첫 오브젝트가 씬에 없음.
- **Build해도 아무 변화 없음** → 로그의 `[WARN]` 확인(컨트롤러/조인트/어트리뷰트/Prefix 중 빠진 것).
- **어트리뷰트 연결 실패** → 선택한 어트리뷰트가 조인트들에 모두 존재하는지 확인.
