# A00160_sphericalEye 사용법

## 1. 개요

눈동자(각막/동공) 메시를 **구면(spherical)으로 dilation** 시키는 리깅 셋업을 만드는 툴이다.
rigmarolestudio "Rigging Spherical Eyes" 기법을 재현한다.

- 조인트는 구 표면이 아니라 **눈동자 맨 앞(Z+)에서 중심까지 Z축을 따라 일렬 배치**한다.
- 조인트들은 **translateX, translateY 가 변하지 않는다**(Z축 위 고정).
- 컨트롤러 attr 하나(`dilate`)로 각 조인트의 **scaleX/Y(단면 반경)와 translateZ(깊이)**를
  구면 함수로 구동해 동공이 구면을 유지하며 부풀게 한다.
- DCC: Autodesk Maya (PySide UI). 노드 생성은 **pymel**, UI 보조는 **maya.cmds**.

> remapValue 기반인 `A00150_remapVal` 과는 무관한 기법(순수 곱/덧셈 노드)이라 별도 툴이다.

**두 가지 빌드 모드**:

| 모드 | 버튼 | 동작 | 특징 |
|------|------|------|------|
| **Baked** | `Build (Spherical Eye)` | 구면 dilation (scale + translateZ 를 sin/cos 로 구동) | sin/cos 를 빌드 시 파이썬 `math` 상수로 박음 |
| **Converge** | `Build (Converge to Center)` | dilate −90~90 양방향: **+면 center(마지막), −면 front(첫) 조인트로 수렴** + 커브를 구 표면에 맞춰 scale | **Maya 2023+** 호환(trig 노드 없음). translate=2-타겟 lerp, scale=구 단면 √(R²−ζ²) |

> 두 모드는 목적이 다르다. Baked 는 동공을 **구면으로 부풀리는** dilation, Converge 는 모든 조인트를
> **한 점(center 조인트)으로 모으는** 수렴이다. 같은 컨트롤러·조인트에 둘을 동시에 빌드하지 말 것
> (translate 가 이중 연결되어 충돌).

---

## 2. 폴더 구조

```
A00160_sphericalEye/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow → 테마 적용 → show()
├── __dragDrop_A00160.py              # 셸프 버튼 설치 + 드래그&드롭 진입점
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/
    │   ├── spherical_drive.py  # add_attr / build_spherical_drive(+run_build)      = Baked
    │   │                       #         / build_spherical_drive_nodes(+run_build_nodes) = Converge
    │   └── maya_scene.py       # cmds 보조 래퍼 (selection / exists)
    └── ui/main_window.py       # 전체 UI
```

- 노드 생성 본체(`spherical_drive.py`)는 pymel, UI 보조(선택 가져오기)는 `maya.cmds`
  (`maya_scene.py`). UI 는 pymel 을 직접 다루지 않고 `run_build(...)` 만 호출한다.

---

## 3. 설치 / 실행

- `A00160_sphericalEye/__dragDrop_A00160.py` 를 Maya 뷰포트로 **드래그&드롭** → 셸프에 **`SphericalEye`** 버튼 생성.
- 셸프 버튼 클릭, 또는 Script Editor 에서:

```python
import tools.A00160_sphericalEye as A00160_sphericalEye
A00160_sphericalEye.run(True)
```

---

## 4. UI 구성

```
┌ Help ─────────────────────────────────┐  ← 메뉴 바 (Help > About)
│ Main Controller [ QLineEdit   ] [Get] │
│ Prefix          [ eye         ]       │
│ Driver Attr     [ dilate      ]       │
│ Radius (R)      [ 1.000 ]             │
├ Joints (front -> center order) ───────┤
│ [Joints] Select/Add/Del/Up/Down/Sort  │
│ ┌ QListWidget (앞 -> 중심 순서) ┐     │
│ └──────────────────────────────┘      │
├───────────────────────────────────────────┤
│ [Build (Spherical Eye)] [Converge to Center]│  ← Baked / Converge 2-버튼
├ Log ──────────────────────────────────────┤
│ ┌ read-only 로그창 (영어 출력) ┐      │
│ └──────────────────────────────┘      │
└───────────────────────────────────────┘
```

- **Main Controller** = 제어용 어트리뷰트가 추가될 컨트롤러. `Get` = 현재 선택의 첫 오브젝트.
- **Prefix** = 생성 노드/어트리뷰트 이름 접두사(기본 `eye`).
- **Driver Attr** = 컨트롤러에 추가되는 keyable double(기본 `dilate`). Baked=dilation 강도,
  Converge=양방향 수렴(−90~90, +면 center / −면 front).
- **Radius (R)** = 구 반지름. Baked=dilation 강도(`{prefix}_radius` 기본값), Converge=커브가 맞춰질 구의
  반지름. **Joints 리스트가 바뀔 때(Select/Add/Del)마다 first→last(front→center) 조인트 거리로 자동 갱신**
  되며, 빌드 전 수동 override 도 가능하다.
- **Joints** = 대상 조인트들. **반드시 앞(Z+) → 중심 순서**로 리스트에 넣는다.
  Baked 는 순서가 위도 분배 기준, **Converge 는 리스트 마지막 조인트가 수렴 target**.
- **Build (Spherical Eye)** = Baked 모드. **Build (Converge to Center)** = Converge 모드(조인트 ≥ 2개).
  둘 다 전체가 **하나의 Undo 청크**. 입력 위젯(Controller/Prefix/Driver Attr/Radius/Joints)은 공용.
  **Radius(R)** 는 Baked=dilation 강도, **Converge=커브가 맞춰질 구의 반지름**(둘 다 사용).

---

## 5. 동작 규칙 (수학)

공통 정의 — 조인트 i (i=0 앞/극점 … i=N-1 중심/적도), `span = max(N-1, 1)`:

```
offset_i (deg) = 90 * i / span                 # 앞 0° → 중심 90°
```

`Zinit_i` = **빌드 시점**의 조인트 로컬 translateZ(유지되는 기준값).
`driver`(컨트롤러 `dilate`)·`R`(컨트롤러 `{prefix}_radius`) 는 빌드 후 라이브 조절 가능.
두 모드 모두 **translateX / translateY 는 연결하지 않는다**(Z축 위 고정).

### 5.1 Baked 모드 — `Build (Spherical Eye)`

```
scaleX/Y_i   = 1       + driver * R * sin(offset_i)
translateZ_i = Zinit_i + driver * R * cos(offset_i)
```

- offset 이 고정이라 `sin/cos` 를 빌드 시 파이썬 `math` 상수로 박는다(eulerToQuat 불필요).

생성 노드:
- 공통 1개: `{prefix}_dR_MLT` (multiplyDivide, `driver * R`)
- 조인트당 3개:
  - `{prefix}_eye_{i}_MLT` (multiplyDivide): `dR*sin`(outputX), `dR*cos`(outputY)
  - `{prefix}_eye_{i}_sADD` (addDoubleLinear): `1 + dR*sin` → scaleX/Y
  - `{prefix}_eye_{i}_zADD` (addDoubleLinear): `Zinit + dR*cos` → translateZ

### 5.2 Converge 모드 — `Build (Converge to Center)`  *(Maya 2023+)*

`dilate`(−90~90) 하나로 **양방향 수렴**: dilate>0 이면 center(리스트 마지막), dilate<0 이면
front(리스트 첫) 조인트 위치로 모인다. front=`oColl[0]`, center=`oColl[-1]` 의 로컬 translate. 전 조인트 i:

```
t_c         = clamp(dilate,  0, 90)/90          # center 방향 0..1 (dilate≥0)
t_f         = clamp(dilate,-90,  0)/(-90)       # front  방향 0..1 (dilate≤0)
translate_i = init_i + t_c*(center - init_i) + t_f*(front - init_i)
```

- `dilate=0` → 양 항 0 → 원위치(rest). `dilate=+90` → center 로, `dilate=−90` → front 로 전부 수렴.
- 두 항 중 항상 하나만 0 이 아니라 합으로 양방향이 된다(외삽이 아니라 두 타겟 보간이라 끝 조인트를
  **뚫지 않고** 정확히 모인다).
- **전 조인트 구동**한다. 각 끝 조인트는 한 방향의 앵커이자 반대 방향의 이동 대상:
  - front(`oColl[0]`): center 로만 이동, front 방향엔 정지(앵커).
  - center(`oColl[-1]`): front 로만 이동, center 방향엔 정지(앵커).
- `dilate` 는 **min −90 / max 90 클램프** → 양 끝에서 완전 수렴, 초과 overshoot 방지.

#### scale — 커브를 구 표면에 맞춤
각 조인트에 바인드된 커브(단면 링, ref_02~04 의 빨간 링)가 반지름 `R`(= Radius 필드) 구의 표면에
항상 놓이도록 scaleX/Y 를 구동한다. center 와의 현재 거리 ζ 에 대해 구 단면 반경 `ρ(ζ)=√(R²−ζ²)` 이므로:

```
scaleX/Y_i = √(R² − ζ_i(t)²) / √(R² − ζ_i,rest²)     # rest 단면 대비 비율(rest=1)
ζ_i(t) = center 로부터 조인트 i 의 현재 거리(translate 출력에서 distanceBetween 으로 읽음)
```

- `distanceBetween`(center 기준)이 방향과 무관하게 현재 거리를 읽으므로 **center/front 양방향 모두**
  구 표면을 따른다: center 로 갈수록 ρ→R(적도, ref_04), front 로 갈수록 ζ→R 이라 ρ→0(front 극점).
- 항상 `ρ(t)² + ζ(t)² = R²` 이라 dilate 전 구간에서 커브가 구 표면에 정확히 놓인다.
- **center 조인트도 이제 scale 구동**(front 로 갈 때 0 으로 수축). rest ζ=0 → scale 1 유지(center 방향).
- **R 은 모든 조인트의 center 까지 거리 이상**이어야 한다(아니면 √음수). 작으면 그 조인트의 **scale 만
  skip**(translate 는 유지)하고 빌드 로그에 경고. front 가 pole(ρ_rest≈0, ÷0)이어도 skip.

노드 (공통 4개 + 조인트당 translate 3개 + scale 5개):

| 노드명 | 타입 | 연결 / 값 |
|--------|------|-----------|
| `{prefix}_tc_CLP` (공통) | clamp | inputR=`dilate`, min/max=0/90 → outputR |
| `{prefix}_tc_MLT` (공통) | multiplyDivide | input1X=tc_CLP.outputR, **×1/90** → t_c |
| `{prefix}_tf_CLP` (공통) | clamp | inputR=`dilate`, min/max=−90/0 → outputR |
| `{prefix}_tf_MLT` (공통) | multiplyDivide | input1X=tf_CLP.outputR, **×−1/90** → t_f |
| `{prefix}_conv_{i}_cMLT` | multiplyDivide | input1X/Y/Z=t_c, **input2=(center−init)** → t_c·Δc |
| `{prefix}_conv_{i}_fMLT` | multiplyDivide | input1X/Y/Z=t_f, **input2=(front−init)** → t_f·Δf |
| `{prefix}_conv_{i}_PMA` | plusMinusAverage(sum) | input3D[0]=cMLT.out, [1]=fMLT.out, **[2]=init** → joint.translate |
| `{prefix}_sc_{i}_DST` | distanceBetween | point1 ← conv_PMA.output3D, **point2=center** → distance = ζ(t) |
| `{prefix}_sc_{i}_dsq_MLT` | multiplyDivide(power) | input1X=distance, **input2X=2** → ζ(t)² |
| `{prefix}_sc_{i}_sub_PMA` | plusMinusAverage(subtract) | input1D[0]=**R²**, input1D[1]=ζ(t)² → R²−ζ(t)² |
| `{prefix}_sc_{i}_sqrt_MLT` | multiplyDivide(power) | input1X=above, **input2X=0.5** → ρ(t) |
| `{prefix}_sc_{i}_scl_MLT` | multiplyDivide(divide) | input1X=ρ(t), **input2X=ρ_rest** → scaleX, scaleY |

> translate 는 두 타겟 선형 lerp + clamp, scale 은 구 단면(sqrt)이라 둘 다 trig 불필요
> (clamp + distanceBetween + multiplyDivide power). 모두 Maya 2023 에 존재.

### 공통 거동
**rest(driver=0)**: 모든 조인트가 원위치·rest scale 유지. **driver↑**:
- Baked → 중심 조인트가 가장 부풀며 구가 팽창(dilation).
- Converge → dilate>0 이면 전 조인트가 center 로(커브 → 적도 반경 R), dilate<0 이면 front 로
  (커브 → front 극점 scale 0) 모이며 구 표면을 따른다.

---

## 6. 사용 순서

1. 컨트롤러로 쓸 오브젝트 선택 → **Get**.
2. 눈동자 메시에 스킨된 조인트들을 **앞 → 중심 순서**로 Joints 리스트에 **Add**.
3. **Prefix / Driver Attr** 설정. **Radius(R)** 는 Joints 변경 시 first→last 거리로 자동 채워진다
   (필요하면 빌드 전 수동 조정). 참고: 자동값은 front 조인트 거리와 같아 front 조인트가 pole(ρ_rest≈0)이
   되어 그 조인트 scale 은 skip 된다. front 도 scale 시키려면 R 을 그보다 크게 키운다.
4. **Build (Spherical Eye)**(Baked, 구면 dilation) 또는 **Build (Converge to Center)**
   (Maya 2023+, ±dilate 로 center/front 수렴 + 커브를 구 표면에 맞춤 / 조인트 ≥ 2개) 클릭.
5. 컨트롤러의 `dilate` 를 조절:
   - Baked → `dilate`·`{prefix}_radius` 로 동공이 구면을 유지하며 부풂.
   - Converge → `dilate` 0→+90 이면 전 조인트가 center 로(커브 적도 반경 R), 0→−90 이면 front 로
     (커브 front 극점 0) 모이며 구 표면을 따른다.

> 어떤 모드를 쓸까? 동공을 **구면으로 부풀리는** 셋업이면 **Baked**, 모든 조인트를 **한 점(center
> 조인트)으로 모으는** 셋업이면 **Converge**. 두 모드는 같은 컨트롤러·조인트에 동시에 빌드하지 말 것
> (translate 가 이중 연결되어 충돌한다).

---

## 7. 로그 · 문제 해결

### 정상 로그 예시
```
--- Build Spherical Eye (Baked) ---
Built (baked): driver eye_ctl.dilate | 5 joint(s) | radius 1.0

--- Build Converge to Center ---
Built (converge): driver eye_ctl.dilate | 6 joint(s) | +center 'eye_center_jnt' / -front 'eye_front_jnt' | sphere radius 2.0
```

> Radius(R)가 어떤 조인트의 center 까지 rest 거리보다 작으면 그 조인트의 **scale 만 skip**하고 경고:
> `[WARN] scale NOT driven for 1 joint(s) (radius 2.0 <= rest distance from center): eye_front_jnt`

### 경고/오류
- `[WARN] Nothing selected. ...` — Get 시 선택 없음.
- `[WARN] Main Controller is empty. ...` / `Controller not found ...` — 컨트롤러 미설정/씬에 없음.
- `[WARN] Joints list is empty.` — 조인트 미추가.
- `[WARN] Driver Attr name is empty.` — Driver Attr 이름 비어 있음.
- `[WARN] Need at least 2 joints (front .. center) to converge.` — Converge 모드인데 조인트가 1개뿐
  (마지막 조인트가 수렴 target 이라 최소 2개 필요).
- `[ERROR] Build failed: <error>` — pymel 노드 생성 중 오류.

### 자주 겪는 문제
- **(Baked) dilation 방향/형태가 이상** → Joints 순서가 **앞 → 중심**인지 확인(순서가 위도 분배 기준).
- **(Converge) 엉뚱한 곳으로 모임** → 수렴 target 은 **리스트 마지막 조인트**다. center 가 맨 끝에
  오도록 **앞 → 중심 순서**로 넣었는지 확인.
- **(Converge) dilate 를 ±90 밖으로 못 올림** → 의도된 클램프(−90..90). +90=center, −90=front 완전 수렴.
- **(Converge) front(−) 방향이 안 되거나 조인트가 앞을 뚫고 나감** → 구버전(단일 center 타겟) 빌드.
  최신 빌드(v01.05+)는 front 를 두 번째 타겟으로 잡아 정확히 모인다. 다시 빌드할 것.
- **(Converge) 커브 크기가 안 변함 / scale 경고** → **Radius(R)** 가 너무 작다. R 은 **구의 반지름**이라
  모든 조인트의 center 까지 거리 이상이어야 한다. front 조인트 거리 이상으로 키울 것.
- **(Converge) 커브가 구 표면에서 뜸** → R 이 실제 구(커브 바인드 시 형상)의 반지름과 맞는지, 조인트의
  center 까지 rest 거리가 구 위 위치와 일치하는지 확인.
- **rest 에서 위치가 틀어짐** → 위치 기준은 빌드 시 **로컬 translate** 다. 조인트의 부모/월드 구조에
  따라 기준값이 달라질 수 있으니 빌드 시 조인트 배치를 확정해 둔다.
