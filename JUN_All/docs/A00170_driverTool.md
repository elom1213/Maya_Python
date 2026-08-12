# A00170_driverTool 사용법

## 1. 개요

리깅 **드라이버 셋업**(메인 컨트롤러 어트리뷰트로 구동되는 노드 네트워크)을 만드는 PySide(Qt)
툴이다. 워크플로가 거의 동일한 두 기존 툴(`A00150_remapVal`, `A00160_sphericalEye`)을
`A00110_animTool` 과 같은 **하나의 창 + 탭** 구조로 통합하고, 커브 어태치(`AttachCrv`)와
스트레치 드라이버(`Stretch`) 기능을 더했다. **네 개의 탭**과 **공유 로그창**으로 구성된다.

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
3. **AttachCrv** — 커브에 오브젝트를 라이브 어태치한다. **하위 탭 2개**로 나뉜다(v01.14).
   - **Default** — 아래 두 모드(기존 기능 그대로).
   - **Edge Loop** — 엣지 루프 → 커브 → 버텍스 자리 널 → 어태치(+조인트)를 **버튼 하나로**. (§4.3.1)

   (`ref/ref_01.mel` 의 `attachDriverOnCurve` 이식)
   - **Attach to Closest Point** (동작 변경): TSL 에 나열된 **기존 오브젝트들**을 각자
     `nearestPointOnCurve` 로 구한 **최근접 파라미터** 지점에 붙인다. 오브젝트당
     `pointOnCurveInfo(parameter=최근접) → fourByFourMatrix → multMatrix(* parentInverseMatrix)
     → decomposeMatrix → translate`(옵션: `rotate`) 네트워크를 만든다. **부모 계층 안전**
     (parentInverse 사용)하고, 빌드 후 **커브가 변형되면 따라간다**.
   - **Distribute Drivers on Curve** (ref 원래 동작): **Count**(양의 정수)만큼 **새 드라이버**
     (Locator/Null)를 만들어 커브의 시작~끝(`minValue`~`maxValue`) 사이에 **균일한 파라미터 간격**으로
     배치·어태치한다. 파라미터는 ref 의 `makeParameterValueList` 그대로 구한다 — **Distribute across
     full range** ON 이면 `division=count-1`(양 끝 정확히 포함, 열린 커브용), OFF 면 `division=count`
     (마지막이 끝 직전에서 멈춤, 주기/닫힌 커브 seam 중복 방지). 어태치 네트워크는 Closest 모드와 동일하다.
4. **Stretch** — Default Distance 어트리뷰트 값(`a`)을 driver 로, Stretch 오브젝트 어트리뷰트를
   driven 으로 구동하는 네트워크를 만든다. **모든 함수 모드는 rest(driver=`a`)에서 driven = 원래 값**
   을 보존한다. (`ref/ref_01_StretchTool.mel` 의 Stretch 기능 이식 + 리팩토링)
   - **선형** `f(x)=x-a+1`(기울기 +1) / `-x+a+1`(기울기 -1): `animCurveUU`(linear 탄젠트, pre/post
     infinity) + `addDoubleLinear` 오프셋으로 additive — `driven = original + (x-a)` / `(a-x)`.
     rest 에서 원래 값, driver 가 `a` 에서 멀어질수록 그 값에서 증감(예: `translateX` 원래 1.5 → 1.5 에서).
   - **시그모이드** `Sigmoid` / `Sigmoid rev`: 해석적 **노드망**(`multiplyDivide` power 등). `(a, original)`
     을 지나는 S 곡선으로 한쪽은 `Threshold Max`, 반대쪽은 `Threshold Min`(≥0 → 0 밑으로 안 감)에 수렴.
     `Sharpness`(지수의 밑 = `1/(1+e^-x)` 의 e, 클수록 급격)·threshold 를 사용자가 지정.
     `Threshold Min < 원래 값 < Threshold Max` 여야 한다. **이 세 값은 Default Distance 오브젝트에
     어트리뷰트(`stretchSharpness`/`stretchThreshMin`/`stretchThreshMax`)로 추가·연결되어 씬에서 실시간 조절**된다.
   - **Stretch 어트리뷰트는 여러 개 선택 가능** — 선택한 모든 어트리뷰트에 동일하게 적용된다.
   - Default 가 1개면 그 하나로 모든 Stretch 를 구동(1:n), 아니면 순서쌍 n:n(min 길이).

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
├── launch.py              # run(): MainWindow 생성 → 테마(coral_dark, 리깅 카테고리) → show()
├── __dragDrop_A00170.py              # 셸프 버튼 설치 + 드래그&드롭 진입점 (TOOL_LABEL = "DriverTool")
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존)
    │   ├── maya_scene.py       # 선택/존재/keyable attr/거리 (maya.cmds 어댑터)
    │   ├── slerp_ramp.py       # Slerp Ramp / Sine Wave 빌드 (pymel) — A00150 복사
    │   ├── spherical_drive.py  # Baked / Converge 빌드 (pymel) — A00160 복사
    │   ├── attach_curve.py     # 커브 어태치 (maya.cmds) — Closest / Distribute 두 모드
    │   └── __init__.py         # run_build_slerp / run_build_wave /
    │                           #   run_build_spherical / run_build_nodes /
    │                           #   run_attach_to_closest / run_attach_uniform 재노출
    └── ui/main_window.py  # 전체 UI (4개 탭 + 공유 로그창 + 메뉴 바)
```

- `main_window.py` 의 위젯/핸들러는 탭별 접두사로 분리한다: **Remap Value = `rmp_*`**,
  **Spherical Eye = `sph_*`**, **AttachCrv = `atc_*`**(Edge Loop 하위 탭은 `lp_*`), **Stretch = `stc_*`**.
  공유하는 것은 `self._log()`(공용 로그창)뿐이다. Stretch 로직은 `app/core/stretch.py`
  (`run_build_stretch`)에 있다.
- `attach_curve.py` 는 노드 생성을 **maya.cmds** 로 한다(pymel 인 다른 두 빌드 모듈과 달리 자족적).

---

## 3. 설치 / 실행

- **설치**: `A00170_driverTool/__dragDrop_A00170.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
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
3. **List Attributes** → 첫 조인트의 어트리뷰트를 Attributes 리스트에 채운다. keyable 뿐 아니라
   `listAttr` 전체를 보여주며 multi/compound 어트리뷰트는 자식까지 펼친다(A00145_RigConnect Connect
   탭과 동일). 목록이 길면 **Filter** 로 좁힌다(§4.5). 빌드는 **보이면서 선택된** 어트리뷰트에만
   적용된다.
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

### 4.3 AttachCrv

**하위 탭 2개** — `Default`(아래) / `Edge Loop`(§4.3.1).

#### Default

1. 커브를 선택하고 **Get** → **Attachment Curve** 설정.
2. **Objects** 리스트에 커브에 붙일 오브젝트들을 추가(`Select`/`Add`).
3. 옵션:
   - **Orient to curve tangent**(기본 ON): 켜면 **Aim Axis**(`+X`/`-X`) 축을 커브 접선에 맞추고
     오브젝트의 `rotate` 까지 구동한다. 끄면 `translate` 만 구동(현재 회전 유지).
   - **Create Normal Curve (norCrv)**(기본 ON, `ref_01.mel` 원본 방식): 켜면 attachCrv 밑에
     직선 **norCrv** 커브 한 개를 만들어 그 자식으로 두고, 각 오브젝트의 **up(Y)/side(Z) 축을
     norCrv 의 tangent/normal 에서** 가져온다(fourByFourMatrix : X=attachCrv 접선, Y=norCrv 접선,
     Z=norCrv 노멀). **norCrv 를 회전/조정하면 어태치된 체인 전체의 up·트위스트가 바뀐다.**
     **norCrv Length** 로 생성 길이를 정한다. 끄면 norCrv 없이 월드 +Y 시드의 자족 직교 프레임을 쓴다.
     (이 옵션은 Orient 가 켜져 있을 때만 의미가 있다.)
   - 자족 프레임(norCrv OFF)은 접선이 월드 업(+Y)과 평행한 **수직 커브**에서 프레임이 무너질 수
     있으니 그런 경우 norCrv 를 쓰거나 Orient 를 끈다.
   - **Group pointOnCurveInfo nodes into a set**(기본 ON): 이번 빌드로 생긴 `pointOnCurveInfo`
     노드들을 모두 담는 objectSet 한 개(`<curve>_atcPOCI_SET`)를 만든다(나중에 한 번에 선택·관리용).
4. **Attach to Closest Point** 클릭. 각 오브젝트가 자신과 가장 가까운 커브 파라미터 지점에 붙고,
   로그에 오브젝트별 파라미터가 출력된다. norCrv 를 만들었으면 그 이름도 로그에 표시된다(이후
   그 커브를 조정해 방향을 잡는다). 씬에 없는 항목은 skip 후 경고하고, 세트 이름도 로그에 표시된다.

#### Distribute (새 드라이버 균일 배치)

위 옵션(Orient / Aim Axis / norCrv / set)을 그대로 공유하며, **Objects 리스트는 필요 없다**
(드라이버를 새로 만든다). **Distribute new drivers uniformly** 그룹에서:

- **Count**: 만들 드라이버 개수(양의 정수).
- **Driver Type**: `Locator`(spaceLocator) 또는 `Null`(빈 그룹).
- **Distribute across full range (open curve)**(기본 ON): 열린 커브면 켜서 양 끝에 정확히
  드라이버를 둔다. 주기적/닫힌 커브면 꺼서 seam 에서 첫·마지막이 겹치지 않게 한다.

**Distribute Drivers on Curve** 클릭 → `<curve>_1_drv`, `<curve>_2_drv` … (Count 자릿수만큼 0 패딩)
드라이버가 생성되어 커브 시작~끝에 균일 배치된다. 로그에 드라이버별 파라미터가 출력된다.

> 어태치는 오브젝트의 `translate`(옵션 `rotate`)에 노드를 **연결**한다. Closest 모드에서 이미
> 연결/잠금된 채널이 있으면 해당 오브젝트만 실패 처리(로그 경고)하고 나머지는 계속한다.

#### 4.3.1 Edge Loop — 루프에서 드라이버 셋업 한 번에 (v01.14~)

입술·눈꺼풀처럼 **엣지 루프를 커브로 뽑아 몇 개의 드라이버로 제어**하는 셋업을 버튼 하나로 만든다.

```
[Store Edge Loops] --polyToCurve--> 커브(루프마다 1개)
[Store Vertices]   --그 자리에-->  널 --가장 가까운 커브에 어태치--> 커브를 따라 움직임
                                    └(옵션, 기본 ON) 조인트가 널을 따라감
```

1. 엣지 루프를 선택 → **Store Edge Loops from Selection**. 떨어진 루프를 **여러 개 한 번에** 골라도
   된다 — 붙어 있는 엣지 덩어리(연결 성분)마다 커브가 하나씩 나온다.
2. 드라이버를 놓을 **버텍스**를 선택 → **Store Vertices from Selection**(엣지/페이스는 버텍스로 변환).
3. **Name Prefix** / **Degree**(1=폴리라인, 3=부드러운 곡선)와 어태치·조인트 옵션을 정하고
   **Build Curve + Nulls (+ Joints)**.

> 저장한 엣지/버텍스는 **리스트 위젯으로 펼치지 않는다** — 루프 하나가 수십~수백 개라 창이 무거워진다.
> 요약 라벨(`Edge loops: 96 edge(s) in 2 loop(s)`)과 `Select` / `Clear` 로 다룬다.

**만들어지는 것**

| 이름 | 내용 |
|------|------|
| `<prefix>_crv_01`, `_02` … | 엣지 루프마다 커브 1개. `polyToCurve(form=2, ch=True)` 라 **닫힌 루프는 주기적 커브**가 되고, 히스토리가 남아 **메시가 변형되면 커브도 따라간다** |
| `<prefix>_null_grp` / `_null_01` … | 저장한 버텍스 **자리마다** 널(빈 그룹). 만든 뒤 커브에 어태치되므로 커브 위 최근접 지점으로 끌려간다(버텍스가 커브 위면 그 자리 그대로) |
| `<prefix>_null_01_con` / `_ctl` / `_tgt` | (체크 시, 기본 ON) 널 밑 컨트롤러 계층 — 아래 참고 |
| `<prefix>_jnt_grp` / `_jnt_01` … | (체크 시) 널마다 조인트 1개. **`parentConstraint`** 로 `_tgt`(컨트롤러 계층이 없으면 널)를 따라간다 |
| `<curve>_norCrv` / `<curve>_atcPOCI_SET` | Default 탭과 동일(커브마다 하나씩) |

- **커브가 여럿이면 널은 각자 가장 가까운 커브**에 붙는다(`nearestPointOnCurve` 로 거리 비교).
  위/아래 입술 루프를 한 번에 처리해도 섞이지 않는다.
- **Insert a controller under each null**(기본 **ON**, v01.15~) — 널과 조인트 사이에 zero-out +
  컨트롤러 계층을 넣는다. 애니메이터가 `ctl` 을 움직이면 **커브가 준 위치 위에 오프셋**이 얹힌다.

  ```
  <prefix>_null_01            ← 커브에 어태치된 널
  └── <prefix>_null_01_con    ← zero-out 널 그룹
      └── <prefix>_null_01_ctl    ← Sphere 커브 컨트롤러 (A00145 Match 탭과 같은 모양)
          └── <prefix>_null_01_tgt    ← **이 노드가 조인트를 컨스트레인트한다**
  ```

  세 노드 모두 로컬 트랜스폼 0(`parent -relative`)이라 널 자리에 정확히 겹친다.
  컨트롤러 크기는 **Joint Radius × 1.5** — 조인트보다 조금 크게 그려진다.
  끄면 예전처럼 **널이 조인트를 직접** 컨스트레인트한다.
- **Create joints that follow the nulls**(기본 **ON**) — 조인트는 널(또는 `_tgt`) 밑으로 parent 하지
  않고 **`parentConstraint`** 로 묶는다. 스켈레톤 계층(`<prefix>_jnt_grp`)을 따로 두어 그대로
  스킨·익스포트할 수 있게 하기 위해서다.
- **Joint Radius** — 조인트의 **`.radius` 어트리뷰트가 이 값이 되도록** 생성 후 명시적으로 설정한다.
  컨트롤러 크기(×1.5)도 이 값에서 나오므로, 조인트를 끄고 컨트롤러만 만들 때도 활성이다.
  > 뷰포트에 **그려지는** 크기는 여기에 마야의 전역 배율(`Display > Animation > Joint Size`)이
  > 곱해진 값이다. 화면에서 커/작아 보여도 어트리뷰트는 입력한 수치가 맞다.
- 어태치 옵션(Orient / Aim Axis / norCrv / POCI 세트)은 Default 탭과 **같은 의미**이며 이 탭 전용 위젯이다.
- 커브 생성 방식은 [`A00400_CurveTool`](A00400_CurveTool.md) 과 같다(연결 성분별 `polyToCurve`).
  A00400 을 import 하지는 않는다 — 툴 하나를 릴리스할 때 다른 툴이 딸려가지 않게 하기 위해서다.
- 전체가 **한 번의 undo** 로 묶인다.

### 4.4 Stretch

거리(또는 임의의 driver 어트리뷰트)에 따라 다른 오브젝트의 어트리뷰트를 선형으로 구동한다.
전형적으로 **Default Distance = `distanceDimension` 의 `distance`**, **Stretch = 조인트의
`scale`/커스텀 attr** 로 쓴다.

1. **Default Distance** 그룹 — driver.
   - **Objects** 리스트에 driver 오브젝트를 추가.
   - **List Attributes** 로 첫 오브젝트의 어트리뷰트를 채우고(길면 **Filter** 로 좁힌다, §4.5),
     driver 로 쓸 어트리뷰트 **하나를 선택**. 그 어트리뷰트의 **현재 값이 `a`**(빌드 시점 스냅샷)다.
2. **Stretch Object** 그룹 — driven. 같은 방식으로 오브젝트와 **어트리뷰트를 하나 이상** 선택한다
   (여러 개 선택하면 선택한 모든 어트리뷰트에 같은 함수가 적용된다).
3. **Function / Infinity**:
   - **Function**: 네 가지.
     - `f(x)=x-a+1` / `-x+a+1` — 선형(멀수록 증가/감소).
     - `Sigmoid (x-:max, x+:min)` — driver 가 `-`쪽이면 `Threshold Max` 로 증가·수렴,
       `+`쪽이면 `Threshold Min` 으로 감소·수렴.
     - `Sigmoid rev (x-:min, x+:max)` — 위와 방향 반대.
   - **Pre Infinity / Post Infinity**(선형 전용, 각각 기본 **Cycle with Offset**): driven 커브의 키
     범위 밖 동작. 양쪽 모두 **Cycle with Offset** 이면 전 구간 직선. `Constant`/`Linear`/`Cycle`/
     `Oscillate` 도 가능. *(시그모이드 선택 시 비활성)*
   - **Sharpness / Thresh Min / Thresh Max**(시그모이드 전용): `Sharpness` 는 지수의 밑
     (`1/(1+e^-x)` 의 e, 기본 `e≈2.7183`, 클수록 급격, `>1`). `Thresh Min`(≥0) / `Thresh Max` 는
     수렴 plateau. **원래 값이 두 threshold 사이(strict)** 여야 한다. *(선형 선택 시 비활성)*
     이 세 값은 **Default Distance 오브젝트에 어트리뷰트로 추가**되어(기본값=UI 값) 네트워크에 연결되므로
     빌드 후 **씬(채널박스)에서 실시간으로 조절**할 수 있다(driver 오브젝트당 한 벌, 그 driver 의 모든
     시그모이드가 공유).
4. **Apply Stretch** 클릭 → 짝마다 driver 로 driven 을 구동하는 네트워크를 만든다.
   - 선형: `driver.attr → animCurveUU → addDoubleLinear(+original-1) → driven.attr`.
   - 시그모이드: `driver.attr → 노드망 → driven.attr` 로
     `driven = tmin + (tmax-tmin)/(1 + ratio·base^(±(x-a)))`, `ratio = (tmax-original)/(original-tmin)`.
     `base^L = ratio` 라 로그 없이 `ratio` 를 곱해 `(a, original)` 통과를 보장하므로, `base`·`tmax`·`tmin`
     을 상수로 굳히지 않고 **위 제어 어트리뷰트에 연결**해도 항상 `driven(a)=original` 이 유지된다.
   - 어느 모드든 **rest 에서 driven = 원래 값**. Default 1개면 1:n, 아니면 n:n(선택한 어트리뷰트 수만큼
     짝마다 반복). 로그에 `driver (a=..) -> driven (rest=.., 노드)` 와 skip 사유가 출력된다.

> driven 어트리뷰트의 **원래 값은 네트워크를 연결하기 전에 스냅샷**한다(연결 후에는 구동값이라 못 읽음).
> 컴파운드(예: `translate`)는 스칼라가 아니라 skip 하고 `[WARN]` — 리프 어트리뷰트(`translateX` 등)를 고른다.
> 시그모이드에서 원래 값이 threshold 범위 밖이면 그 짝만 skip 하고 `[WARN]`(범위를 넓히거나 값을 조정).
> 씬에서 제어 어트리뷰트를 원래 값이 범위를 벗어나도록 바꾸면 `(a, original)` 통과가 깨질 수 있으니 주의.

> **원본(`ref_01_StretchTool.mel`) 대비 개선**: ① pre/post infinity 를 **둘 다 사용자 지정**(원본은
> post=Cycle w/ Offset, pre=Constant 고정이라 rest 이하가 직선이 아니었다). ② 탄젠트를 **auto→linear**.
> ③ 두 번째 키를 `2a`→`a+1` 로 바꿔 **실제로 `f(x)=x-a+1`** 이 되게 하고(원본은 기울기 `1/a`), `a=0`
> 에서 두 키 입력이 겹쳐 커브가 깨지거나 `a<0` 에서 기울기 부호가 뒤집히던 문제를 없앴다.
> ④ `setDrivenKeyframe` 2회로 커브를 직접 만들어 `connectionInfo` 재조회를 제거. ⑤ 존재/self-drive/
> 스칼라 여부 **입력 검증** 추가(headless mayapy 로 함수 일치·infinity·탄젠트 검증 완료).
>
> 참고: 원본 MEL 의 **Distance 탭**(`distanceDimension` 생성)은 이식하지 않았다. 필요하면 Maya 의
> 기본 Distance Tool 또는 별도 유틸을 쓴다.

### 4.5 Filter — 어트리뷰트 찾기 (v01.13, 기존 `Attr Search` 대체)

Remap Value 탭과 Stretch 탭의 두 그룹, **세 곳의 Attributes 리스트**가 같은 검색 UI 를 쓴다.
공용 위젯 [`Framework_MOD_filter_qt`](Framework_MOD_filter_qt.md) 이며 `A00145_RigConnect` ·
`A00290_BSTool` 과 동작이 같다.

```
Attributes
┌───────────────────────────────────┐
│ rotateX                            │   ← 일치하는 것만 남고
│ rotateY                            │      나머지는 숨는다
│ rotateZ                            │
└───────────────────────────────────┘
Filter [ rotate             ] [Clear] [Reveal]
```

- **입력하는 즉시** 일치하는 항목만 남고 나머지는 **숨는다**(지우는 게 아니라 가리는 것).
- **부분 일치**, **대소문자 무시**, 공백으로 나눈 **여러 단어는 AND**.
- `List Attributes` 로 목록을 다시 채워도 **필터가 유지**된다.

> **필터가 걸린 동안에는 "보이는 것이 작업 대상"이다.** Qt 는 항목을 숨겨도 선택 상태를 유지하므로,
> 그대로 두면 **가려서 안 보이는 어트리뷰트까지 빌드에 들어간다.** 그래서 Build / Apply 는
> **보이면서 선택된** 어트리뷰트만 쓰고, 가려진 선택이 있으면
> `[INFO] ... hidden by the filter were skipped.` 로 알린다.

#### `Reveal` — 목록에 없던 어트리뷰트 드러내기

Filter 는 **이미 채워진 목록만** 거른다. 그래서 애초에 리스트업되지 않은 어트리뷰트
(예: `worldMatrix`)는 Filter 로 찾을 수 없다. 그때만 쓰는 보조 버튼이 **`Reveal`** 이다 —
Filter 에 적은 문구로 **첫 오브젝트를 다시 질의**(`listAttr(obj.<token>)`)해 그 결과로 목록을
교체한다. 드러낸 항목이 곧바로 가려지지 않도록 **필터는 자동으로 비워진다.**

> 예전 `Attr Search` 버튼은 ① 일치 항목 **선택** ② 일치가 없으면 **재질의** 를 한 버튼이 겸했다.
> ①은 Filter 가 대신하고, ②는 별개의 동작이라 **`Reveal` 버튼으로 분리**했다 — 언제 재질의가
> 일어나는지가 눈에 보인다.

---

## 5. 로그 / About

- 네 탭의 모든 결과·경고(`[WARN]`)·오류(`[ERROR]`)는 창 하단의 **공유 로그창**에 누적된다.
- **Help > About** 에 네 탭의 빌드 모드 설명이 함께 표기된다.
