# A00120_FKIK — Bake 속도 개선(Tier 2) 계획서 + Maya 2023 호환성 진단

## Context (배경 / 목적)

`A00120_FKIK`(FKIK Tool, Qt UI)는 FK↔IK 컨트롤러 매칭 결과를 프레임 구간에 걸쳐
키프레임으로 **베이크**한다. 실제 작업은 `app/core/fkik_matcher.py` 의
`FKIKMatcher.bake()` 가 담당한다 (UI 버튼: **Bake IK / Bake FK**).

현장 조건이 **6000프레임 이상 × 컨트롤러 50~100개**로 흔하다. 현재 구현은
**Python 프레임 루프 + 프레임마다 `currentTime` + 쌍별 `xform` 반복**이라
이 규모에서 수 분이 걸린다.

목표: **동작(베이크 결과 = 월드 트랜스폼)과 UI/시그니처는 그대로 두고**,
내부를 Maya 네이티브 베이커(`cmds.bakeResults`, C++)로 교체해 체감 속도를 크게 높인다.
본 문서는 그 **Tier 2 안의 설계·개선점·Maya 2023 호환성·검증 절차**를 정리한다.

> 관련: 전체 진단은 대화 진단(병목 ①②③)에서 출발했고, 본 문서는 그중 **권장안 Tier 2**를
> 구체화한 개발 문서다. 사용법 문서가 아니라 `docs/plans/` 규칙을 따른다.

---

## 1. 현재 병목 분석 (`fkik_matcher.py`)

문제의 루프 (`bake()`, L128–147):

```python
for frame in range(start, end + 1):
    cmds.currentTime(frame, edit=True)               # 병목 ①
    match_transforms(tgt_list, flw_list, 1, 1, 1, 1) # 병목 ②
    cmds.setKeyframe(flw_list, t=frame)              # 병목 ③
```

`match_transforms()` 는 **한 쌍당 `cmds.xform` 약 10회**(query 4 + set 6, L39–58).

6000프레임 × 50쌍 기준 부하:

| # | 근본 원인 | 위치 | 영향 |
|---|-----------|------|------|
| **①** | `currentTime(edit=True)` 가 프레임마다 **전체 DG 평가 + 뷰포트 리프레시** | L141 | 6,000회 리프레시 = 단일 최대 병목 |
| **②** | 쌍별 `xform` 반복 = Python↔C++ 명령 디스패치 | `match_transforms` | 6,000 × 50 × 10 ≈ **300만 회** 호출 오버헤드 |
| **③** | `setKeyframe(flw_list)` 프레임마다 followers 전체 평가 | L143 | 6,000회 |
| **④** | 전 과정이 **직렬 DG 평가** — Evaluation Manager(병렬) 미활용 | 루프 전체 | 누적 |

> 빠른 경로의 부품은 이미 코드에 있다: `bake_constraint()`(L149–190)가
> `parentConstraint` + `bakeSimulation`(네이티브 베이커)을 사용한다. 정작 주력 버튼
> (Bake IK/FK)이 느린 Python 루프를 쓰는 상태이므로, 같은 네이티브 베이커 방식을
> `bake()` 에 적용하는 것이 본 계획의 핵심이다.

---

## 2. Tier 2 핵심 개선 기법

1. **프레임 루프 제거 → `cmds.bakeResults` 위임 (①②③④ 동시 해결)**
   타깃→팔로워 임시 `parentConstraint` 를 건 뒤, **단일 `bakeResults` 호출**로 구간 전체를
   샘플링한다. 베이크는 C++ 내부 루프 + 내부 리프레시 억제 + Evaluation Manager 활용으로
   동작하므로, 300만 회 `xform` 디스패치와 6000회 뷰포트 리프레시가 사라진다.
2. **scale 제외** — `match_transforms` 는 translate/rotate 만 다룬다. 따라서
   베이크 대상 어트리뷰트는 `["tx","ty","tz","rx","ry","rz"]` 로 한정(불필요한 sx/sy/sz 베이크 제거).
3. **베이크 후 임시 컨스트레인트 정리** — 베이크가 키를 구운 뒤 컨스트레인트를 삭제,
   팔로워에는 순수 애니메이션 커브만 남긴다.
4. **상태 복원 보장** — `currentTime` 원위치, `refresh(suspend)` 해제, `undoInfo` 청크 닫기를
   `finally` 에서 무조건 수행(예외 시 뷰포트 멈춤/플레이헤드 이동 방지).
5. **단일 Undo 스텝** — 전체 베이크를 하나의 `undoInfo` 청크로 묶어 Ctrl+Z 한 번에 되돌림.

기대 효과: **Python 루프 대비 약 20~50배**(수 분 → 수~수십 초). `currentTime`/`xform`
디스패치 제거가 지배적 이득.

---

## 3. 제안 구현 (`bake()` 교체안)

시그니처·반환값(`end - start + 1`)을 유지하므로 호출부(`main_window.on_bake`) **무수정**.

```python
@staticmethod
def bake(tgt_list, flw_list, start, end):
    """
    [start, end] 구간을 native bakeResults 로 베이크. (구 Python 프레임 루프 대체)

    각 (tgt, flw) 쌍에 임시 parentConstraint 를 건 뒤 bakeResults 로 일괄 샘플링하고,
    베이크 후 컨스트레인트를 삭제한다. world 결과는 기존 match 베이크와 동치.
    """
    if not tgt_list or not flw_list:
        return 0

    count = min(len(tgt_list), len(flw_list))
    flw = flw_list[:count]
    attrs = ["tx", "ty", "tz", "rx", "ry", "rz"]   # match_transforms 는 scale 미사용

    cur = cmds.currentTime(q=True)

    cmds.undoInfo(openChunk=True)
    cmds.refresh(suspend=True)
    cons = []
    try:
        for i in range(count):
            try:
                cons += cmds.parentConstraint(
                    tgt_list[i], flw[i], maintainOffset=False
                )
            except Exception as e:
                # 락/연결된 attr 등으로 컨스트레인트 실패 → 해당 쌍 skip
                cmds.warning("FKIK bake: skip pair %s -> %s (%s)"
                             % (tgt_list[i], flw[i], e))

        if cons:
            cmds.bakeResults(
                flw,
                simulation=True,
                time=(start, end),
                sampleBy=1,
                attribute=attrs,
                disableImplicitControl=True,
                preserveOutsideKeys=True,
                sparseAnimCurveBake=False,
            )
    finally:
        if cons:
            cmds.delete([c for c in cons if cmds.objExists(c)])
        cmds.refresh(suspend=False)
        cmds.currentTime(cur, edit=True)
        cmds.undoInfo(closeChunk=True)

    return end - start + 1
```

### 플래그 의미
- `simulation=True` : 프레임 순서대로 평가(시뮬레이션 의존 리그 안전). 원본 루프와 동일한 순차 평가 성격.
- `sampleBy=1` : 매 프레임 키(원본은 프레임마다 setKeyframe → 동일).
- `disableImplicitControl=True` : 베이크 중 컨스트레인트 영향을 정리해 깨끗한 커브 생성.
- `preserveOutsideKeys=True` : [start, end] 밖의 기존 키 보존.
- `sparseAnimCurveBake=False` : 매 프레임 dense 키(원본 동작과 일치).

### (선택) 공통 헬퍼로 추출
`bake_constraint()` 와 로직이 겹치므로 `_native_bake(flw, t, attrs, mo)` 같은 내부 헬퍼로
묶고, scale 포함 여부(`attrs`)와 `maintainOffset` 만 파라미터화하면 중복이 준다. 리팩토링 시 함께 정리.

---

## 4. 기존 동작과의 동일성 / 차이 (중요)

`match_transforms` 와 `parentConstraint(mo=False)` 의 **월드 결과는 동치**다. 다만 키로
저장되는 표현과 일부 보조 어트리뷰트 처리에 차이가 있어 명시한다.

| 항목 | 기존 `match_transforms` | Tier 2 (parentConstraint+bake) | 결과 영향 |
|------|------------------------|-------------------------------|-----------|
| 월드 translate/rotate | 타깃과 일치 | 타깃과 일치 | **동일** |
| rotateOrder | 작업 중 타깃값 적용 후 **원복** | 팔로워 자체 order 로 rx/ry/rz 샘플 | 월드 동일, 키 값 표현만 다름 |
| rotateAxis | 타깃값으로 **변경(원복 안 함, L49-50)** | 변경하지 않음(기존 rotateAxis 반영해 회전 계산) | 월드 동일. **rotateAxis≠0 리그면 attr 자체는 미복사** |
| scale | 건드리지 않음 | 베이크 대상에서 제외 | 동일 |
| 키 밀도 | 매 프레임 | 매 프레임(`sampleBy=1`) | 동일 |

핵심: **컨트롤러의 rotateAxis 가 보통 (0,0,0)** 이므로 실사용 결과는 동일하다. 비-0 rotateAxis를
쓰는 특수 리그에서만 "rotateAxis 어트리뷰트 복사"가 빠진다(월드 포즈는 여전히 동일). 검증 5장에서 확인한다.

**오프셋 정책**: `maintainOffset=False` 는 기존 `match()`(타깃에 월드 정렬)와 같은 의미.
만약 리그가 컨트롤러–타깃 사이 의도된 오프셋을 가진다면 `True` 옵션이 필요하다 → 검증 후 결정.

---

## 5. Maya 2023 호환성 — **진단 결과: 정상 동작(폴백 불필요)**

Tier 2가 사용하는 모든 요소가 Maya 2023(Python 3.9)에서 지원된다.

| 사용 요소 | Maya 2023 지원 | 비고 |
|-----------|----------------|------|
| `cmds.parentConstraint(maintainOffset=...)` | ✅ | 매우 오래된 명령 |
| `cmds.bakeResults(...)` | ✅ | C++ 네이티브 베이커 |
| ├ `simulation` (sm) | ✅ | |
| ├ `time` (t) `=(start, end)` | ✅ | 튜플 구간 |
| ├ `sampleBy` (sb) | ✅ | |
| ├ `attribute` (at) | ✅ | |
| ├ `disableImplicitControl` (dic) | ✅ | |
| ├ `preserveOutsideKeys` (pok) | ✅ | |
| └ `sparseAnimCurveBake` (sac) | ✅ | |
| `cmds.refresh(suspend=True/False)` | ✅ | 뷰포트 억제 |
| `cmds.currentTime(q/edit)` | ✅ | |
| `cmds.undoInfo(openChunk/closeChunk)` | ✅ | |
| `cmds.objExists` / `cmds.delete` / `cmds.warning` | ✅ | |
| **Python 3.9** (Maya 2022~2023 기본) | ✅ | 아래 주의 |

**Python 버전 주의(2023 = Python 3.9)** — 제안 코드는 표준 dict/list, f-string/`%` 포맷만
쓰므로 안전하다. 단 향후 수정 시 **3.10+ 전용 문법 금지**:
- `match`/`case` 문 금지
- `X | Y` 런타임 타입 유니온 지양(typing 사용)

**메모리 참고**: `[[maya-2023-compat]]` 의 "native sin/cos 노드 없음"은 **DG 노드 그래프** 얘기다.
본 작업은 노드를 만들지 않는 순수 명령 호출이므로 무관. `[[maya-loadplugin-no-file]]` 도
플러그인 로딩과 무관(해당 없음).

> **결론: Tier 2 코드는 Maya 2023 에서 별도 분기/폴백 없이 그대로 동작한다.**

### 5-b. 버전 무관하지만 반드시 지킬 것 (견고성)
- `refresh(suspend=True)` 는 **반드시** `finally` 에서 `suspend=False` 로 해제. 예외로 억제가
  남으면 뷰포트가 멈춘 것처럼 보인다.
- `currentTime` 원위치 복원(작업 전 프레임으로).
- 컨스트레인트 생성 실패(락/연결/레퍼런스 attr) 시 해당 쌍 skip + `warning`, 전체 중단 금지.
- `cons` 가 비면 `bakeResults` 호출 생략(불필요/에러 방지).

---

## 6. 검증 (Verification)

Maya 2023(가능하면 최신 버전도)에서 `tools.A00120_FKIK.launch.run()` 으로 UI 실행 후:

1. **정합성(월드 일치)** — 동일 입력에서 (a) 기존 Python 루프 베이크 결과와 (b) Tier 2 결과의
   팔로워 월드 트랜스폼을 여러 프레임에서 비교(예: `xform -q -ws` 로 몇 프레임 샘플 대조). 허용오차 내 일치.
2. **속도** — 6000프레임 × 50/100 컨트롤러 씬에서 소요 시간 측정(간단 타이머 로그). 목표: 수십 배 단축.
3. **Undo** — 베이크 후 Ctrl+Z 한 번으로 키/컨스트레인트가 깨끗이 되돌려지는지.
4. **상태 복원** — 베이크 후 현재 프레임이 작업 전으로 복원, 뷰포트 정상(suspend 해제) 확인.
5. **엣지/회귀**
   - `start == end`(1프레임), `start > end`(UI 차단 동작 유지) 확인.
   - rotateAxis≠0 리그에서 월드 포즈 일치 여부(4장 차이 항목) 확인.
   - 락/연결된 attr 컨트롤러 포함 시 skip + 경고, 나머지 정상 베이크.
   - IK→FK / FK→IK 양방향 모두.
   - `[start, end]` 밖 기존 키 보존(`preserveOutsideKeys`) 확인.

---

## 7. 작업 순서(제안)

1. `fkik_matcher.py` `bake()` 를 3장 구현으로 교체(시그니처/반환값 유지).
2. 컨스트레인트 실패 skip + 경고, `cons` 빈 경우 처리, `finally` 상태 복원 반영.
3. (선택) `_native_bake()` 헬퍼로 추출해 `bake_constraint()` 와 공유(scale·mo 파라미터화).
4. (선택) UI에 `maintainOffset` 토글 추가 — 리그 오프셋 정책이 필요한 경우만.
5. 6장 검증(특히 Maya 2023). 정합성·속도·Undo 확인.
6. `app/config/version.py` 버전 상향 + 파일 헤더 `last Update date` 갱신, 필요 시 CHANGELOG 기록.

---

## 8. 롤백 / 리스크

- 변경 범위가 `bake()` 한 함수에 국한, 시그니처 불변 → 문제 시 함수 단위 롤백 용이.
- 리스크: (a) 특수 rotateAxis 리그의 attr 미복사(월드는 동일), (b) 의도된 오프셋 리그에서
  `mo` 정책 차이 → 둘 다 검증 항목으로 사전 차단. 불확실하면 기존 Python 루프 베이크를
  옵션으로 잠시 병존시킬 수 있다(예: UI 토글 "Legacy bake").
