# A00190_FKIK_General_Tool 사용법

## 1. 개요

캐릭터 리그의 **FK/IK 매칭 & 베이크**를 돕는 **PySide(Qt) 툴**이다. 팔·다리(좌/우) 컨트롤을
리스트로 모아, FK↔IK 포즈를 서로 **스냅 매칭**하고 선택한 **프레임 구간을 베이크**한다.
보조로 매칭 기준이 되는 **드라이버(pose object)** 를 자동 생성하고, 리스트 구성을 **JSON 으로 저장/로드**한다.

레거시 단일 파일 maya.cmds 툴(`01_Modules/JUN_PY_FKIK_General_Tool_V01_02.py`)을
현행 (B) Qt 아키텍처로 리팩토링한 버전이다.

- **로직/UI 분리**: 매칭·드라이버·세팅 로직은 `app/core`(씬 접근만 cmds/pymel), 화면은 `app/ui` 가 담당.
- **중복 UI 제거**: 반복되던 textScrollList 블록을 `Framework.qt.JUN_mod_tsl_qt` 위젯으로 통일.
- **UI**: PySide(`Framework.qt.qt` 가 PySide6→PySide2 폴백). 테마는 `ThemeManager` 의 `blue_dark` qss.
- **Maya 2023 호환** (Python 3.9 / PySide2). `pin_to_surface` 는 pymel 을 사용한다. UI 문자열/로그는 모두 영어.

> **전제**: 매칭은 **pose object(타깃)** 와 **control(추종)** 의 쌍으로 동작한다. control 이 pose object 의
> 월드 위치/회전으로 스냅된다. 보통 드라이버 셋업으로 pose object 를 만든 뒤 매칭/베이크한다.

---

## 2. 폴더 구조

```
A00190_FKIK_General_Tool/
├── __init__.py           # from .launch import run
├── launch.py             # run(): DEV reload + MainWindow 생성/교체 → ThemeManager → show
├── __dragDrop_A00190.py             # DEV_MODE + 셸프 버튼 설치 / 드래그&드롭 진입점
└── app/
    ├── config/version.py # VERSION / LAST_UPDATE
    ├── core/             # 로직 (UI 비의존, list[str] 입출력)
    │   ├── matching.py        # match_two_objects, MatchData, OGSFreeze, run_match_bake
    │   ├── driver_setup.py    # pin_to_surface(pymel), Cage, setup_triangle_drivers, create_switch_drivers
    │   ├── selection_utils.py # 계층/토큰 필터, 위치/평균, parent 헬퍼
    │   └── settings_io.py     # save_settings / load_settings (dict[slot, list] ↔ JSON)
    └── ui/
        ├── main_window.py     # MainWindow(QWidget): 탭 + Option + 로그 + 핸들러
        └── limb_list_group.py # TslListGroup: 재사용 tsl 위젯 묶음
```

- **로직(app/core)과 UI(app/ui)를 분리**한다. UI 핸들러가 위젯에서 `list[str]` 를 뽑아 core 함수에 넘기고,
  결과 리스트를 위젯에 되돌린다. core 는 위젯/컨트롤 이름을 모른다.

---

## 3. 설치

`A00190_FKIK_General_Tool/__dragDrop_A00190.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
"FKIK_Gen" 버튼이 설치된다(중복 버튼은 자동 제거).

---

## 4. 실행

- 셸프 버튼 클릭, 또는 스크립트 에디터에서:
  ```python
  import tools.A00190_FKIK_General_Tool as A00190_FKIK_General_Tool
  A00190_FKIK_General_Tool.run(True)   # True 면 DEV_MODE 에서 자기 자신 + Framework reload 후 실행
  ```
- 창은 `objectName`(`JUN_A00190_FKIK_General_window`)으로 관리되어 재실행 시 중복 없이 교체된다.

---

## 5. UI 구성

### 탭

| 탭 | 의미 |
|----|------|
| **Source** | 드라이버 셋업의 입력. `Set Source : FK`(팔·다리 좌/우 FK 컨트롤), `Set Source : IK`(IK 소스) 리스트. |
| **Match FK** | FK 매칭/베이크용. limb 별 **pose**(타깃 드라이버) / **ctl**(추종 컨트롤) 리스트 쌍. |
| **Match IK** | IK 매칭/베이크용. limb 별 **pose** / **ctl** 리스트 쌍. |

각 리스트(tsl)는 공통 버튼을 제공한다(`Framework.qt.JUN_mod_tsl_qt`):

| 버튼 | 동작 |
|------|------|
| **Select Objects** | 현재 씬 선택으로 리스트를 **교체**. |
| **Add** | 현재 선택을 **중복 없이 추가**. |
| **Del** | 선택 항목 제거. |
| **Up / Down** | 선택 항목 순서 이동. |
| (항목 클릭) | 해당 항목을 씬에서 선택. |

### Option 패널 (모든 탭 공용, 하단)

| 요소 | 의미 |
|------|------|
| **Arm/Leg Left/Right** (체크박스) | 매칭/베이크 대상 limb 선택(기본 모두 ON). |
| **Start / End Frame** | 베이크 구간(기본값은 플레이백 범위). |
| **Set up triangle drivers** | Source FK 로 NURBS 삼각형 + 표면 핀 locator(=pole 드라이버) 생성. |
| **Drivers for FK IK switch** | FK↔IK 전환용 드라이버 locator 생성, 결과를 Match 탭 **pose** 리스트에 자동 기입. |
| **Load setting / Save setting** | 모든 리스트 구성을 JSON 으로 로드/저장. |
| **Match IK / Match FK** | 현재 프레임에서 IK/FK 컨트롤을 pose 에 매칭(+키). |
| **Bake IK / Bake FK** | Start~End 구간을 매칭하며 베이크. |

---

## 6. 사용 순서

1. **Source 탭** — 팔·다리(좌/우)의 FK 컨트롤을 `Set Source : FK` 각 리스트에, IK 소스를 `Set Source : IK` 에 Add.
2. **Set up triangle drivers** — Source FK 로 삼각형 surface 드라이버(pole 위치)를 만든다.
3. **Drivers for FK IK switch** — 전환 드라이버를 생성한다. Match FK/IK 탭의 **pose** 리스트가 자동으로 채워진다.
   (필요하면 Match 탭에서 pose/ctl 리스트를 직접 보정한다.)
4. **Option** — 대상 limb 체크, 베이크할 Start/End Frame 설정.
5. 실행:
   - **Match IK / Match FK** — 현재 프레임에서 한 번 스냅 매칭(+키프레임).
   - **Bake IK / Bake FK** — 구간 전체를 프레임별로 매칭하며 키를 굽는다(뷰포트 정지로 가속).
6. (선택) **Save setting** 으로 리스트 구성을 JSON 에 저장, 다음 세션에서 **Load setting** 으로 복원.

각 셋업/매칭/베이크는 `cmds.undoInfo(openChunk/closeChunk)` 로 묶여 **Ctrl+Z 한 번**에 취소된다.

---

## 7. 동작 규칙 / 개념

- **매칭 원자 연산**(`match_two_objects`): 각 쌍에서 타깃의 `rotateOrder`/`rotateAxis`/월드 `translation`/월드
  `rotation` 을 추종 오브젝트에 복사한다. 타깃의 rotateOrder 를 잠시 적용해 회전을 정확히 세팅한 뒤,
  추종 오브젝트의 원래 rotateOrder 로 복원한다.
- **pose object = 타깃, control = 추종**: `run_match_bake` 는 선택된 limb 의 `(pose, ctl)` 쌍을 모아
  ctl 을 pose 로 스냅한다. `Match IK`/`Bake IK` 는 IK 쪽 쌍(Match IK 탭), `Match FK`/`Bake FK` 는 FK 쪽 쌍을 쓴다.
- **Match vs Bake**: Match 는 **현재 프레임 1회**(키 1개), Bake 는 **Start~End 구간**을 프레임마다 매칭+키.
  베이크 동안 `OGSFreeze` 로 뷰포트를 일시정지해 속도를 높인다.
- **프레임 종속 보정**: 한 프레임당 매칭을 2회 반복해, 부모-자식 종속 컨트롤이 한 번에 안 맞는 경우를 보정한다.
- **드라이버 셋업**:
  - *Triangle drivers* — limb 의 FK 소스 컨트롤 3개로 degree-1 NURBS 삼각형을 만들고, 무게중심에 둔
    locator 를 표면에 핀(`pin_to_surface`)해 pole 위치 드라이버로 쓴다.
  - *FK/IK switch drivers* — IK 소스 위치에 locator 를 만들어 FK 컨트롤 회전에 맞추고 IK 소스에
    `parentConstraint` 한다(IK→FK). wrist/ankle/toe 에 대한 FK→IK 드라이버도 생성한다.
- **공간/순서**: 드라이버 그룹은 `JUN_posObjs_grp` 아래에 모인다. 같은 이름의 기존 드라이버는 재생성 시 삭제된다.

---

## 8. 세팅 저장 / 로드

- **Save setting** — 24개 리스트(Source FK/IK, Match FK/IK 의 pose·ctl)를 **슬롯 id**(예: `mfk_arm_l_ctl`)를
  키로 하는 JSON(`*.json`)으로 저장한다.
- **Load setting** — JSON 의 슬롯 id 가 현재 UI 에 있으면 해당 리스트를 복원한다(없는 키는 무시).
- 저장 포맷은 슬롯 id 기반이라 UI 위젯 이름 변경과 무관하게 안정적이다(레거시의 tsl 이름 키와 비호환).

---

## 9. 로그 · 문제 해결

- 하단 **로그창**에 각 동작 결과/경고가 출력된다(`[WARN]` 접두 + Maya `cmds.warning`).
- **"End frame is before start frame."** — Bake 시 End < Start. 프레임 범위를 확인한다.
- **Match/Bake 가 0 control matched** — 대상 limb 체크 해제 또는 Match 탭의 pose/ctl 리스트가 비어 있음.
  Source 입력 → 드라이버 셋업 → pose 리스트 채움 순서를 확인한다.
- **pose 리스트에 `"Empty"` 가 보임** — 드라이버 셋업이 부분적으로만 수행됨(예: 팔에는 toe 드라이버 없음).
  필요한 Source/컨트롤을 채운 뒤 셋업을 다시 실행한다.
- **드라이버 셋업 실패** — Source 리스트의 컨트롤 개수/순서가 기대(삼각형은 3개, switch 는 wrist=idx2 등)와
  맞는지 확인한다. 로그의 예외 메시지를 참고한다.
```
