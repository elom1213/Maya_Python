# SmartLayer — Bake 알고리즘 분석

> 대상 툴: `C:\Users\USER\Documents\maya\scripts\_SmartLayer` (서드파티 Maya 애니메이션 툴)
> 분석 범위: Main 탭의 **"Create Smart Layer"** 베이크 파이프라인
> 분석 기준 버전: `smart_layer311.pyc` (Python 3.11 바이트코드)

---

## 0. 분석 방법과 주의사항

이 툴은 **모든 핵심 로직이 컴파일된 바이트코드(`.pyc`)로 배포**된다. 각 `.py` 파일은
버전별 `.pyc`를 import 하는 얇은 래퍼일 뿐이다.

```python
# 예: core/smart_layer.py
import sys
current_version = int("{0}{1}".format(sys.version_info[0], sys.version_info[1]))
if current_version == 311:
    from .__hybrid__.smart_layer311 import *   # 실제 코드는 여기
```

`__hybrid__/` 안에 `27 / 37 / 39 / 310 / 311` 버전이 함께 들어 있어 Maya의 Python 버전에
맞춰 로드된다. 따라서 **클린 소스는 읽을 수 없고**, 본 문서의 모든 내용은 Python 3.11로
`.pyc`를 `marshal` + `dis`로 **직접 디스어셈블**해 얻은 것이다(바이트코드에 남아 있는
문자열 상수·docstring·호출 이름이 근거이며 추측이 아니다).

재현 방법은 [부록](#부록-재현-방법)을 참고.

---

## 1. 결론 요약

SmartLayer의 베이크는 단순한 `bakeResults`가 아니라 다음을 수행하는 파이프라인이다.

1. 대상 애님 레이어의 애니메이션을 프레임별로 샘플링한다.
2. 오브젝트의 **이동/회전 속도(speed)**를 계산한다.
3. 속도에 **임계값(threshold)**을 적용해 **키가 필요한 프레임만 적응적으로 선택**한다
   (느린 구간 = 키 줄임/freeze, 빠른 구간 = 키 촘촘히).
4. 레이어드 애니메이션을 **목표 공간(world / relative / object space)**으로 변환한다
   (델타 보간 + slerp + spline + stretch/lean/flex pivot + pelvis 보정 + fix-sliding).
5. 월드 공간 **로케이터를 만들어 결과 트랜스폼을 키잉**하고 원본을 컨스트레인한다.
6. 컨스트레인된 원본을 네이티브 `bakeResults`로 굽고, 결과를 **`SmartLayer`라는 새 애님
   레이어로 병합**한다.
7. 로케이터/임시 데이터를 정리한다.

즉, **"속도 기반 적응형 키 샘플링 + 공간 변환 + reparent 베이크"**가 이 툴의 정체성이다.

---

## 2. 두 개의 "Bake" UI 구분 (중요)

이름이 비슷해 혼동하기 쉬운 두 버튼이 있다.

| UI | 위치 | 버튼 | 실제 동작 |
|----|------|------|-----------|
| **Bake Anim Curves** | Curve Filters 탭 | bake 버튼 (Sample by 슬라이더) | ❌ **미구현 스텁** |
| **Create Smart Layer** | Main 탭 (Bake Options 섹션) | Create Smart Layer | ✅ 실제 베이크 |

Curve 탭의 bake 버튼 콜백 `on_apply_bake_btn_clicked`를 디스어셈블하면 다음이 전부다.

```python
def on_apply_bake_btn_clicked(self):
    print("Baking anim curves by sample: {}".format(str(self.sample)))
```

콘솔에 메시지만 출력할 뿐 실제 키 베이크가 없다. `core/curve_filters/curve_filter.py`
(`SmartLayerAnimCurveFilter`)에도 smooth / interpolate / retime / intensity 함수만 있고
**bake/resample 함수 자체가 없다**. 따라서 실제로 키프레임을 굽는 기능은 아래 Main 탭 경로뿐이다.

---

## 3. 호출 체인

```
[Main 탭] "Create Smart Layer" 버튼 (UI/tab_main/button_proceed.py → MainTab 콜백)
   └─> SmartLayer.main()                         (core/smart_layer.py :: class SmartLayer)
         └─> ... 23단계 파이프라인 ...
               └─> SmartLayer.__reparent_objects()   # 결과를 로케이터에 키잉 + 컨스트레인
               └─> SmartLayer.__bake_hik()           # 네이티브 bakeResults + 레이어 병합
```

`SmartLayer.__init__`은 인자 28개(`args=29`, self 포함)를 받는다 — anim_layer, objects,
anim_curves, space, simulation, interpolation, weight_by_distance, override_layer,
pelvis 관련 설정 등 UI 옵션 전체가 여기로 전달된다.

---

## 4. `main()` 파이프라인 단계별

`main()`을 디스어셈블해 추출한 self-메서드 호출 순서다.

| # | 메서드 | 역할 |
|---|--------|------|
| 1 | `__initial_check` | 라이선스/입력 유효성 검사 |
| 2 | `__build_attrs` | 대상 어트리뷰트 목록 구성 |
| 3 | `__get_initial_data` | 선택/anim curve/대상 레이어의 초기 데이터 읽기 |
| 4 | `__build_m_time_arr` | `om.MTime` 배열 구성 |
| 5 | `__pelvis_correction_master_check` | pelvis 보정 사용 여부/설정 점검 |
| 6 | `__build_specific_object_data` ×2 | rotation-up object, center object 데이터 |
| 7 | `__get_key_times` / `__prepare_anim_data_structures` | 키타임·자료구조 준비 |
| 8 | `__scrap_animation_data` | **프레임별 트랜스폼 샘플링** |
| 9 | `__calculate_speed` | **이동/회전 속도 계산** (5.1) |
| 10 | `__define_steps_by_threshold` | **속도 임계값 기반 적응형 키타임** (5.2) |
| 11 | `__scrap_layer_data_by_threshold` / `__scrap_layer_data` | 레이어 데이터 추출 |
| 12 | `__get_center_data` | 센터(피벗/평균) 데이터 |
| 13 | `__calculate_keytimes_relative_movement` | 상대 이동 키타임 계산 |
| 14 | `__calculate_deltas_and_final_transforms` | **목표 공간으로 최종 트랜스폼 산출** (5.3) |
| 15 | `__reparent_objects` | **월드 로케이터 키잉 + 컨스트레인** (5.4) |
| 16 | `__bake_hik` | **네이티브 bake + SmartLayer 레이어 병합** (5.5) |
| 17 | `__scrap_transforms_after_reparent` | reparent 후 트랜스폼 재추출 |
| 18 | `__reparent_final_and_keyframes` | 최종 reparent 키프레임 |
| 19 | `__final_scrap_and_keyframes` | 최종 키프레임 설정 |
| 20 | `__pelvis_correction_main` | pelvis 보정 적용 |

중간중간 `__update_progress_bar`로 진행률(예: bake 직후 85%)을 갱신한다. heavy rig가
감지되면 *"enabling simulation to bake objects in world space; Parallel evaluation works
faster."* 메시지와 함께 **simulation 옵션을 자동 활성화**한다(HIK 관련 경고 문자열도 존재).

---

## 5. 핵심 알고리즘 심층 분석

### 5.1 속도 계산 — `__calculate_speed`

바이트코드 내장 docstring:

> *"going through all animation data and calculating delta between keyframes. as the keyframe
> time is always '1', it can be considered as 'animation speed'"*

- 키프레임 간격이 항상 1프레임이므로, **연속 키 사이의 변화량(델타)을 그대로 속도로 간주**한다.
- `pos_speed`: 위치 델타 벡터의 길이(`om.MVector.length`). x/y/z 축별 사용 플래그
  (`use_pos_x/y/z_speed`)로 특정 축만 속도에 반영 가능.
- `rot_speed`: 회전을 쿼터니언으로 다뤄 `conjugate` → `normalizeIt` → `asAxisAngle`로
  **회전 각도(라디안, `math.pi` 사용)**를 추출.
- `pos_rot_combined_speed`: 위치·회전 속도를 합성한 값.

### 5.2 속도 기반 적응형 키 샘플링 — `__define_steps_by_threshold` (핵심 차별점)

docstring:

> *"returns new keytimes, 'middle step' points, and reevaluates speed arrays"*

- `SmartLayerCore.build_relative_speed_arr`로 **상대 속도 배열**을 만들고
  `sliding_smooth`로 스무딩한다(`relative_speed_arr`, `relative_speed_arr_smoothed`).
- `sliding_threshold`(슬라이딩 임계값 배열)와 비교해, 어느 프레임에 키를 둘지 결정한다.
- 산출물:
  - `keyframe_times_from_threshold` — 임계값 통과로 선택된 키타임
  - `kt_threshold_dict` — 키타임별 임계 정보
  - `intervals_to_freeze_starts` — **변화가 거의 없어 "동결(freeze)"할 구간**의 시작점
- 결과적으로 **빠르게 움직이는 구간엔 키를 촘촘히, 정지/저속 구간엔 키를 줄이거나 freeze**
  한다. 단순 매 프레임 bake보다 키 수가 적고 편집이 쉬운 커브를 만드는 것이 목적.

> 보조: `__get_property_percents_smart` docstring — *"priority position over rotation. if both
> are static then simple linear interp is chosen"*. 위치·회전·스케일의 보간 비율(percent)을
> 계산하되, 둘 다 정지 상태면 단순 선형 보간을 택한다.

### 5.3 공간 변환·델타 보간 — `__calculate_deltas_and_final_transforms`

docstring:

> *"getting delta between layer and no_layer data, then interpolating to get delta for every
> frame. then adding initial world transform, to get result world transform"*

이 메서드가 **레이어 적용 전/후의 델타를 구해 매 프레임으로 보간한 뒤, 초기 월드 트랜스폼에
더해 목표 공간의 최종 트랜스폼**을 만든다. 호출하는 보조 로직(이름 기준):

- 공간/방향: `space` (world/relative/object), `rotation_up_type`/`rotation_up_vector`,
  `build_rotation_delta`
- 보간: `MQuaternion.slerp`(회전), `SplineMath.build_spline` / `spline_interp` /
  `transform_by_spline`(경로 기반 보간), `transform_interp` 계열
- 변형 보정:
  - **stretch**: `get_transform_stretch_factor`, `use_stretch`
  - **lean(기울기)**: `calculate_leans`, `get_lean_universal`, `get_lean_from_spline`,
    `leans_intensity`, `leans_smooth_interval`
  - **flexible pivot(유연 피벗)**: `flexible_pivot`, `flex_transformation`,
    `calculate_flex_weight_master`
  - **거리 가중**: `weight_by_distance`, `define_weight_based_on_projected_distance`,
    `find_target_segment_index_and_weight_based_on_distance`
  - **pelvis 보정**: `enable_pelvis_cor`, `pelvis_objects`
  - **fix-sliding**: `get_fix_sliding_final_transforms`
- 경로 길이 0일 때 *"path length is 0, evaluation might produce incorrect results"* 경고.

산출물: `result_positions`, `result_rotations`, `result_scale`(+ 기타 커브 `result_other`).

### 5.4 reparent + 컨스트레인 — `__reparent_objects`

docstring:

> *"creates locators in world space, adds keys to these locators, and then point/orient/scale
> constraint objects to these locators"*

1. 각 오브젝트마다 월드 공간 로케이터(`{}_{}_LOC`)와 `{}_orient_grp`를 생성한다.
2. 5.3에서 구한 `result_positions/rotations/scale`을 **`om.MFnAnimCurve.create` + `addKeys`로
   로케이터의 translate/rotate/scale 커브에 직접 키잉**한다(`kTangentGlobal`).
3. 원본 오브젝트를 로케이터에 `pointConstraint` / `orientConstraint` / `scaleConstraint`로
   묶는다. 이때 회전축 오프셋(`rotate_axis_euler_inversed`)을 보정하고, 스케일 기존 연결은
   `MDGModifier`로 끊는다(*"ERROR: can not disconnect scale attrs {}"* 예외 처리 존재).

즉, **최종 모션을 로케이터에 먼저 키잉**해 두고 원본을 따라가게 만든 뒤, 다음 단계에서 그
원본을 구워 깔끔한 애니메이션을 얻는 구조다.

### 5.5 네이티브 bake + 레이어 병합 — `__bake_hik`

`__bake_hik`은 전체 바이트코드를 확보했고, 동작은 다음과 같다.

```python
def __bake_hik(self):
    prev_anim_layers = set(cmds.ls(type='animLayer'))           # 베이크 전 레이어 스냅샷

    cmds.bakeResults(self.objects_list,
                     time=(self.min_t, self.max_t),
                     <kw>=1, <kw>=1)                             # 네이티브 bake (sim/oversample=1)
    self.__update_progress_bar(85)

    if self.override_layer == 0:
        # PATH 1: 임시 레이어 생성 후 머지
        tmp_layer = cmds.animLayer('tmp')
        current = set(cmds.ls(type='animLayer'))
        new_layers = list(current - prev_anim_layers)

        # 머지 대상 지정
        mel.eval('$gSelectedAnimLayers = {"%s", "%s"};' % (new_layers[0], new_layers[1]))

        # 머지 옵션 (optionVar)
        mel.eval('optionVar -intValue   animLayerMergeUp 1;')
        mel.eval('optionVar -intValue   animLayerMergeChilds 0;')
        mel.eval('optionVar -intValue   animLayerMergeResultType 1;')
        mel.eval('optionVar -intValue   animLayerMergeDeleteLayers 0;')
        mel.eval('optionVar -intValue   animLayerMergeBakeAll 0;')
        mel.eval('optionVar -floatValue animLayerMergeByTime 1.0;')
        mel.eval('optionVar -intValue   animLayerMergeOversamplingRate 1;')
        mel.eval('optionVar -intValue   animLayerMergeSmartBake 0;')
        mel.eval('optionVar -intValue   animLayerMergeSmartFidelity 0.0;')
        mel.eval('optionVar -floatValue animLayerMergeSmartFidelityDelta 5;')
        mel.eval('performAnimLayerMerge 0;')                    # 실제 병합

        after = set(cmds.ls(type='animLayer'))
        self.smart_layer = cmds.rename(after - current, 'SmartLayer')   # 결과 레이어 이름 부여
        cmds.delete(new_layers)                                 # 임시 레이어 정리
    else:
        # PATH 2: override_layer ≠ 0 → 새 레이어를 그대로 SmartLayer로 rename
        current = set(cmds.ls(type='animLayer'))
        new_layers = list(current - prev_anim_layers)
        self.smart_layer = cmds.rename(new_layers[0], 'SmartLayer')
```

> 참고: 위 코드는 디스어셈블한 바이트코드를 가독성 있게 재구성한 것이다. `bakeResults`의
> 두 키워드 인자는 KW_NAMES 상수로 전달되며 값은 모두 `1`이다(simulation / oversampling 계열).
> `animLayer`/`ls`/`rename`/`delete`/`mel.eval` 호출 자체와 모든 문자열 상수는 바이트코드에서
> 그대로 확인된다.

핵심:
- `bakeResults`로 컨스트레인된 원본의 모션을 키로 굽는다.
- `performAnimLayerMerge`로 베이크 결과 레이어들을 **하나로 병합**한다(SmartBake 끄고
  `ByTime=1.0`, `OversamplingRate=1`로 매 프레임 병합).
- 최종 레이어 이름을 **`SmartLayer`**로 통일한다.

---

## 6. Maya 네이티브 bake와의 차이 (왜 이렇게까지 하나)

| 항목 | 네이티브 `bakeResults` | SmartLayer |
|------|------------------------|------------|
| 키 배치 | 매 프레임(또는 sampleBy 고정) | **속도 기반 적응형**(느린 구간 freeze) |
| 공간 | 현재 공간 그대로 | **world / relative / object** 변환 |
| 경로 보간 | 없음 | spline / slerp / stretch / lean / flex pivot |
| 추가 보정 | 없음 | pelvis 보정, fix-sliding, 거리 가중 |
| 출력 | 기존 채널 위 | **별도 `SmartLayer` 애님 레이어** |

따라서 SmartLayer의 bake는 "키를 굽는 것"보다 **"의미 있는 키만 남기면서 다른 공간으로
모션을 재구성하는 것"**에 가깝다. 마지막의 `bakeResults` + `performAnimLayerMerge`는 이
재구성 결과를 실제 키로 확정하는 단계일 뿐이다.

---

## 부록: 재현 방법

`strings` 없이 Python 3.11로 `.pyc`를 직접 디스어셈블한다(읽기 전용).

```python
import marshal, dis

def load(fn):
    with open(fn, 'rb') as f:
        f.read(16)               # Python 3.7+ pyc 헤더(16바이트) 건너뜀
        return marshal.load(f)

def find(code, name):            # co_consts를 재귀로 뒤져 함수 코드 객체 찾기
    for k in code.co_consts:
        if hasattr(k, 'co_name'):
            if k.co_name == name:
                return k
            r = find(k, name)
            if r:
                return r

m  = load(r"C:\Users\USER\Documents\maya\scripts\_SmartLayer\core\__hybrid__\smart_layer311.pyc")
fn = find(m, "__bake_hik")
print(fn.co_consts)              # 문자열/숫자 상수 (mel 명령 등)
print(fn.co_names)               # 참조 이름 (cmds, bakeResults, animLayer ...)
dis.dis(fn)                      # 실제 바이트코드
```

- `co_consts`의 문자열에는 docstring과 mel 명령이 그대로 남아 있다.
- `co_names`로 어떤 Maya/OpenMaya API를 호출하는지 알 수 있다.
- 메서드 목록은 `co_consts`를 재귀로 돌며 `co_name`을 출력하면 된다.
