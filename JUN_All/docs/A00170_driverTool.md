# A00170_driverTool 사용법

## 1. 개요

리깅 **드라이버 셋업**(메인 컨트롤러 어트리뷰트로 구동되는 노드 네트워크)을 만드는 PySide(Qt)
툴이다. 워크플로가 거의 동일한 두 기존 툴(`A00150_remapVal`, `A00160_sphericalEye`)을
`A00110_animTool` 과 같은 **하나의 창 + 탭** 구조로 통합했다. **두 개의 탭**과 **공유 로그창**으로 구성된다.

1. **Remap Value** — 컨트롤러 어트리뷰트로 여러 오브젝트의 어트리뷰트를 `remapValue` 곡선을 따라
   보간/전파한다. (구 `A00150_remapVal`)
   - **Build (Slerp Ramp)**: master `remapValue` 가 자식 `remapValue` 들을 driven 해 멀티아웃
     곡선처럼 어트리뷰트를 보간한다(Chris Lesage `build_slerp_ramp` 기반).
   - **Build (Sine Wave)**: 오브젝트마다 `plusMinusAverage → animCurve → remapValue` 체인으로
     위상이 어긋난 사인 웨이브를 전파한다. 컨트롤러에 추가되는 Driver Attr 가 전체 위상을 민다.
2. **Spherical Eye** — Z축 일렬(앞 → 중심) 조인트들을 컨트롤러 driver 하나로 구면 dilation
   구동한다. (구 `A00160_sphericalEye`)
   - **Build (Spherical Eye)**: baked 구면 dilation. `scaleX/Y = 1 + driver*R*sin`,
     `translateZ = Zinit + driver*R*cos` (sin/cos 는 빌드 시 상수).
   - **Build (Converge to Center)**: Maya 2023+ 호환 노드 네트워크. `dilate(-90..90)` 가 모든
     조인트를 center(+) 또는 front(-) 조인트로 수렴시키고, 바인드된 곡선이 반지름 R 구 표면에
     놓이도록 `scaleX/Y` 를 구동한다.

> **통합 방침**: 핵심 로직은 두 원본의 `app/core`(`slerp_ramp.py`, `spherical_drive.py`)를
> **수정 없이 복사**해 재사용한다. 두 모듈이 모두 `run_build` 를 정의하므로 `app/core/__init__.py`
> 에서 `run_build_slerp` / `run_build_spherical` 별칭으로 구분해 노출한다. 리스트 UI 는 재사용
> 위젯 `JUN_mod_tsl_qt_v01`, 로직 노드 생성은 pymel, UI 보조(선택/존재/거리)는 `MayaScene`(maya.cmds)이 담당한다.

> **기존 툴과의 관계**: 원본 `A00150_remapVal` / `A00160_sphericalEye` 는 **그대로 유지**되며
> 각자의 셸프 버튼/`run()` 으로 단독 실행도 가능하다. A00170 은 둘을 묶은 별도 툴이다.

- 모든 UI 문자열/로그는 영어. 각 Build 는 `cmds.undoInfo(openChunk/closeChunk)` 로 묶여
  **Ctrl+Z 한 번**에 취소된다.

---

## 2. 폴더 구조

```
A00170_driverTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마(yellow_dark) → show()
├── config.py              # 셸프 버튼 설치 + 드래그&드롭 진입점 (TOOL_LABEL = "DriverTool")
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존)
    │   ├── maya_scene.py       # 선택/존재/keyable attr/거리 (maya.cmds 어댑터)
    │   ├── slerp_ramp.py       # Slerp Ramp / Sine Wave 빌드 (pymel) — A00150 복사
    │   ├── spherical_drive.py  # Baked / Converge 빌드 (pymel) — A00160 복사
    │   └── __init__.py         # run_build_slerp / run_build_wave /
    │                           #   run_build_spherical / run_build_nodes 재노출
    └── ui/main_window.py  # 전체 UI (2개 탭 + 공유 로그창 + 메뉴 바)
```

- `main_window.py` 의 위젯/핸들러는 탭별 접두사로 분리한다: **Remap Value = `rmp_*`**,
  **Spherical Eye = `sph_*`**. 공유하는 것은 `self._log()`(공용 로그창)뿐이다.

---

## 3. 설치 / 실행

- **설치**: `A00170_driverTool/config.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
  "DriverTool" 버튼이 설치된다(중복 버튼은 자동 제거).
- **실행**: 셸프 버튼 클릭, 또는 스크립트 에디터에서
  ```python
  import tools.A00170_driverTool as A00170_driverTool
  A00170_driverTool.run(True)   # True 면 DEV_MODE 에서 Framework + 자기 자신 reload
  ```
- 창은 `objectName`(`JUN_A00170_driverTool_window`)으로 관리되어 재실행 시 중복 없이 교체된다.

---

## 4. 탭별 사용법

### 4.1 Remap Value

1. 오브젝트를 선택하고 **Get** → Main Controller 설정.
2. **Joints** 리스트에 대상 오브젝트를 추가(`Select`/`Add`). Joints 수가 바뀌면 **In Max** 가
   자동으로 (개수 − 1)로 갱신된다(읽기 전용, Sine Wave 의 master input 범위).
3. **List Attributes** → 첫 조인트의 keyable 어트리뷰트를 Attributes 리스트에 채운다.
   **Attr Search** 토큰(예: `rotate`)으로 일치 항목을 일괄 선택할 수 있다. 빌드는 **선택된**
   어트리뷰트에만 적용된다.
4. **Prefix**(기본 `twist`) 설정. Sine Wave 는 **Driver Attr**(기본 `wave`)도 설정.
   **Range** 의 Out Min/Max 는 두 모드 공용, In Min 은 Sine Wave 전용 기본값이다.
5. **Build (Slerp Ramp)** 또는 **Build (Sine Wave)** 클릭.

### 4.2 Spherical Eye

1. 오브젝트를 선택하고 **Get** → Main Controller 설정.
2. **Joints** 리스트에 조인트를 **앞(Z+) → 중심 순서**로 추가한다. Joints 가 바뀌면 **Radius (R)**
   가 first→last(front→center) 거리로 자동 갱신되며, 빌드 전 수동 override 가능하다.
3. **Prefix**(기본 `eye`), **Driver Attr**(기본 `dilate`), **Radius (R)** 설정.
4. **Build (Spherical Eye)**(Baked) 또는 **Build (Converge to Center)** 클릭.
   - Converge 는 조인트가 **2개 이상** 필요(첫=front 타겟, 마지막=center 타겟)하고,
     center 까지 rest 거리가 R 이상인 조인트는 **scale 만 skip**(translate 는 유지)되며 로그에 경고한다.

---

## 5. 로그 / About

- 두 탭의 모든 결과·경고(`[WARN]`)·오류(`[ERROR]`)는 창 하단의 **공유 로그창**에 누적된다.
- **Help > About** 에 두 탭의 빌드 모드 설명이 함께 표기된다.
