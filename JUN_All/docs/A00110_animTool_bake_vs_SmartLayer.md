# A00110_animTool Bake vs SmartLayer Bake — 비교와 Smart bake 이식

> 관련 문서: [SmartLayer_bake_algorithm_analysis.md](SmartLayer_bake_algorithm_analysis.md)
> 대상 코드: `JUN_All/tools/A00110_animTool/app/core/bake_manager.py`, `app/ui/main_window.py`

---

## 1. 두 베이크 비교

| 항목 | **A00110_animTool** (`BakeManager.bake`) | **SmartLayer** (`Create Smart Layer`) |
|------|------------------------------------------|----------------------------------------|
| 본질 | **네이티브 `bakeResults` 얇은 래퍼** | **속도 기반 키 재구성 + 공간 변환 파이프라인** |
| 키 밀도 | `sampleBy=1` → **매 프레임 dense**(`sparseAnimCurveBake=False`) | **속도 임계값 적응형** — 빠른 구간 촘촘, 느린 구간 freeze |
| 공간 | 현재 공간 그대로 | **world / relative / object 공간 변환** |
| 보간/보정 | 없음 | slerp·spline 경로보간, stretch / lean / flex pivot, pelvis 보정, fix-sliding |
| 동작 방식 | 대상 노드를 직접 bake | 결과를 월드 로케이터에 키잉 → 컨스트레인 → bake → `SmartLayer` 레이어 병합 |
| 옵션 | 채널 T/R/S, Range, Simulation, Keep constraints | space, simulation, interpolation, weight_by_distance, pelvis 등 |
| 코드 | 순수 소스, 명료 | **`.pyc` 컴파일·난독, 라이선스 체크 존재** |
| 목적 | "구동된 모션을 키로 확정"(robust·빠름) | "모션을 다른 공간으로 지능적으로 재가공" |

### 핵심 결론
둘은 **우열이 아니라 목적이 다른 도구**다.
- 단순히 컨스트레인/익스프레션 구동 모션을 키로 굽는 것 → A00110의 native dense bake가 **이미 정답**(빠르고 무손실).
- SmartLayer가 가치 있는 지점은 두 가지뿐: **(1) 스마트 키 감축(decimation)**, **(2) 공간 변환(space switch)**.

---

## 2. 이식 가능성 판단

**SmartLayer 코드를 "이식"하는 것은 불가능/비현실적이다.**
- 전부 컴파일된 `.pyc`(난독)라 소스 복사 불가 — 디스어셈블로 *개념*만 파악 가능.
- 라이선스 체크가 있는 상용 툴이라 코드 복제는 부적절.
- 공간 변환·spline·lean·flex·pelvis 전체는 내부 자료구조/`SmartLayerCore`/`SplineMath`에 깊게 얽혀, 옮기면 사실상 툴 전체 재작성.

**대신 핵심 아이디어(스마트 키 감축)는 독립 구현 가능하다.** 흥미롭게도 SmartLayer도 자체
적응형 샘플링 후 최종 병합에서는 native smart bake 를 꺼버린다(`animLayerMergeSmartBake 0`).
A00110에는 Maya 표준 기능으로 가볍게 추가하는 것이 맞다.

---

## 3. 구현 방식 선택 — (A) 네이티브 smart vs (B) 자체 decimation

| | (A) 네이티브 smart | (B) 자체 decimation |
|---|---|---|
| 구현 | `cmds.bakeResults(..., smart=(1, tol))` 한 줄 | dense bake + 파이썬 후처리(값 읽기→임계 비교→키 삭제) |
| 코드량 | 매우 적음 | 수십~수백 줄, 직접 검증 부담 |
| 처리 위치 | C++ 단일 패스 | C++ 베이크 + **파이썬 후처리** |
| **Maya 2023** | **OK** — `smart` 플래그는 **Maya 2020+** 제공(2023 동작) | OK — 순수 cmds/OpenMaya |
| 결과 | Maya 표준 smart bake 품질 | 완전 제어 가능 |

### 속도 차이
| | (A) 네이티브 smart | (B) 자체 decimation |
|---|---|---|
| 6000프레임 × 100컨트롤러 | 현재 dense bake와 **거의 동일**(감축 오버헤드 미미) | dense bake 시간 **+ 후처리 패스** |
| 후처리 비용 | 없음(내장) | `cmds` 기반이면 베이크 시간과 맞먹거나 그 이상, OpenMaya로도 추가 비용 |
| 체감 | 가장 빠름 | A보다 느림(대략 1.5~수 배) |

### 선택: **(A) 네이티브 smart bake**
2023에서 동작하고, 더 빠르고, 코드가 최소이며, Maya 표준 동작이라 유지보수가 쉽다.
(B)는 문서상 대안으로만 남긴다 — 향후 "속도/곡률 기반 커스텀 감축"이 필요할 때 별도 검토.

---

## 4. A00110에 적용한 내용 (v01.07)

### `app/core/bake_manager.py` — `BakeManager.bake()`
- 파라미터 추가: `smart=False`, `smart_tolerance=0.5`(`DEFAULT_SMART_TOLERANCE`).
- `smart=True` 면:
  - `sparseAnimCurveBake=True`(키를 솎아내기 위함),
  - `cmds.bakeResults(..., smart=(1, float(tolerance)))`.
- **폴백**: `smart` 플래그를 모르는 구버전(<2020)에서 `TypeError` 발생 시, dense
  (`sparseAnimCurveBake=False`, smart 제거)로 다시 굽고 로그에 표시.
- 반환 메시지에 모드(`smart bake (tol …)` / `dense` / `dense (smart unsupported, fell back)`) 표기.

```python
bake_kwargs = dict(
    simulation=simulation, time=(start, end), sampleBy=1, attribute=attrs,
    disableImplicitControl=disable_implicit, preserveOutsideKeys=True,
    sparseAnimCurveBake=bool(smart),
)
if smart:
    bake_kwargs["smart"] = (1, float(smart_tolerance))   # [on, tolerance(deg)]
try:
    cmds.bakeResults(objects, **bake_kwargs)
except TypeError:                 # smart 플래그 미지원 버전 -> dense 폴백
    bake_kwargs.pop("smart", None)
    bake_kwargs["sparseAnimCurveBake"] = False
    cmds.bakeResults(objects, **bake_kwargs)
```

### `app/ui/main_window.py` — Bake 탭
- `Simulation` 아래에 **"Smart bake (reduce keys)"** 체크박스 + **"Tolerance"** 입력
  (`QDoubleValidator`, 기본 `0.5`) 추가.
- 체크 상태에 따라 Tolerance 입력 활성/비활성(`_bake_update_smart_mode`).
- `on_bake()`에서 체크/허용오차를 읽어 `BakeManager.bake(smart=…, smart_tolerance=…)` 전달.
  허용오차 파싱 실패 시 기본값으로 폴백하고 경고 로그.

### 사용법
- 기본(체크 해제) = 기존과 동일한 매 프레임 dense bake.
- 체크 시 = native smart bake. **Tolerance ↑ → 키 더 많이 제거(거침)**, **↓ → 더 촘촘(정밀)**.

---

## 5. 검증 방법 (Maya 2023)

1. A00110 실행 → **Bake** 탭. Bake List에 컨트롤러 추가.
2. 긴 구간(예: 1–6000)을 dense / smart 각각 베이크해 비교:
   - **키 수**: smart 가 dense 보다 적은지(특히 정지 구간).
   - **속도**: smart 가 dense와 비슷하거나 더 빠른지(후처리 없음).
   - **품질**: Tolerance를 0.1 / 0.5 / 2.0 으로 바꿔 모션 유지 정도 확인.
3. (호환성) 구버전 Maya가 있으면 smart 체크 시 dense 폴백 로그가 뜨는지 확인.

> 참고: `bakeResults`의 `smart` 인자 형식이 환경에 따라 `(1, tol)` 튜플/단일 bool 로 다르게
> 받아들여질 수 있다. 2023에서 동작을 1차 확인하고, 이상 시 `smart=1` 단일 인자도 시도.
