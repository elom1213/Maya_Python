---
name: wip-a00170-attachcrv-tab
description: "A00170_driverTool AttachCrv tab IMPLEMENTED (Maya test + push pending) — attach TSL objects to closest point on a curve, ported/changed from ref_01.mel"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8546124f-32a8-4de0-8ce6-b4460f257dcf
  modified: 2026-09-15T00:46:17.638Z
---

WIP (started 2026-06-26): A00170_driverTool 에 새 탭 **AttachCrv** 추가. `ref/ref_01.mel`
(attachDriverOnCurve, by Doosup Jung) 을 PySide/Python 으로 이식하되 **동작을 바꾼다**.

**요구사항 (사용자)**: 기존 ref 는 커브에 *일정 간격*으로 새 로케이터를 어태치했음. 대신,
해당 탭 TSL 에 나열된 **기존 오브젝트들**을 각자 **커브에서 가장 가까운 지점(closest param)** 에
라이브로 붙인다. 커브가 변형되면 오브젝트도 따라감.

**구현 설계 (확정)**:
- 새 core 모듈 `app/core/attach_curve.py` (cmds 기반; 다른 build 모듈은 pymel 이나 이건 cmds 로 자족).
  함수 `build_attach_to_closest(curve, objects, orient=True, aim_axis='+X')`:
  - 오브젝트마다: 임시 `nearestPointOnCurve` 노드로 빌드시점 최근접 `.parameter` 취득(오브젝트
    위치는 `xform -q -ws -rp`), 노드 삭제.
  - `pointOnCurveInfo`(turnOnPercentage=0, parameter=그값), curveShape.worldSpace[0] 연결.
  - `fourByFourMatrix`(in30/31/32 = poci.positionX/Y/Z) → `multMatrix`(matrixIn[0]=fbf.output,
    matrixIn[1]=obj.parentInverseMatrix[0]) → `decomposeMatrix` → obj.translate (orient 시 obj.rotate 도).
  - orient: poci.normalizedTangent = X축. side = T×worldUp(0,1,0), up'=side×T (vectorProduct op=2,
    normalizeOutput=1). +X: in00..=T, in10..=up', in20..=side. -X: T 와 side 를 multiplyDivide(-1) 로
    반전(handedness 유지). 수직 커브(tangent∥up)면 degenerate → orient off 권장(문서화).
  - 각 obj try/except, 실패 로그 후 continue. 반환: (attached_count, failed_list) 정도.
- `app/core/__init__.py` 에 `run_attach_to_closest` 별칭으로 재노출(+__all__).
- `app/ui/main_window.py`: `_build_attach_tab()` 추가, `self.tabs.addTab(..., "AttachCrv")`.
  UI: Attachment Curve(QLineEdit + Get), Objects TSL(JUN_mod_tsl_qt), Orient 체크박스(기본 on)
  + Aim Axis 콤보(+X/-X, orient 일 때만 enable), Build 버튼 "Attach to Closest Point".
  핸들러 `on_atc_get_curve`/`on_atc_build` (undo_chunk 로 감쌈, self._log 사용).
- 버전 `app/config/version.py` 01.03→01.04, LAST_UPDATE 2026-06-26. About 텍스트에 AttachCrv 추가.
- 문서 `JUN_All/docs/A00170_driverTool.md` 갱신 + `JUN_All/docs/WORKLOG.md` 2026-06-26 항목.
- 검증: `py_compile` (Maya 실기 대기, 이 repo 관례).

**진행 상태**: 구현 완료(아래 전부 작성·`py_compile` 통과). attach_curve.py / core __init__ /
main_window(_build_attach_tab, on_atc_*, About) / version 01.04 / docs / WORKLOG 모두 반영됨.
추가됨: 체크박스 "Group pointOnCurveInfo nodes into a set"(기본 ON) → 빌드로 만든 poci 들을
objectSet `<curve>_atcPOCI_SET` 으로 묶음(core `create_set` 파라미터, 반환 (attached,failed,set_node)).

**UPDATE 2026-06-30 (v01.07)**: AttachCrv 탭에 **Distribute 모드** 추가(ref 원래 동작 복원).
사용자 요청: 양의 정수 Count 만큼 **새 오브젝트를 커브에 균일하게** 어태치. core
`build_attach_uniform(curve, count, driver_type, full_range, ...)` (= `run_attach_uniform`):
ref `makeParameterValueList` 그대로 — count==1→중앙, full_range ON→division=count-1(양끝포함),
OFF→division=count(주기커브 seam). Locator/Null 드라이버 생성 후 rename `<curve>_<NN>_drv`
(0패딩) → 기존 `_attach_one(..., param=)` 재사용(param=None 이면 closest, 값주면 그 지점).
UI: "Distribute new drivers uniformly" 그룹(Count spin, Driver Type 콤보, full-range 체크,
Distribute 버튼) — orient/aim/norCrv/set 옵션은 Closest 모드와 공유. 핸들러 `on_atc_distribute`.
**UPDATE 2026-09-15 (v01.22)**: Default 에 **`Maintain offset`**(기본 ON, Closest 전용).
core `build_attach_to_closest(..., maintain_offset=False)` — 기본 False 라 Edge Loop(`loop_rig`)는 그대로.
켜면 translate/rotate 대신 `offsetParentMatrix = 상수 × fbf.output × 부모.worldInverseMatrix`
(상수 = `OPM0 × 부모월드0 × inv(프레임0)`) → 채널 값·피벗·JO·RA 무보정으로 제자리 유지.
함정 2개: `obj.parentMatrix` 는 자기 OPM 포함([[parentmatrix-includes-offsetparentmatrix]]),
**직선 norCrv 의 normal 은 커브 평행 이동만으로 부호가 뒤집힌다** → maintain 경로는 X=접선 +
업시드=norCrv 접선의 직교 정규 프레임을 새로 짠다. **OFF 경로의 ref 프레임(Z=norCrv normal)은 같은
뒤집힘으로 rotate 가 튈 수 있는데 손대지 않았다** — 사용자에게 보고함. headless 148항목.

**UPDATE 2026-09-15 (v01.23)**: Attachment 칸이 **NURBS surface** 도 받는다(`JUN_PY_matrixPinning_V01_01` 이식).
core `resolve_target()` → (shape, 'curve'|'surface'), `attach_target_kind()` 재노출. `_attach_one(kind=)` 가
서피스면 `closestPointOnSurface`(임시) → `pointOnSurfaceInfo`(`<obj>_atc_POSI`, 세트 `_atcPOSI_SET`),
attached 의 param 은 `(u, v)`. norCrv 는 커브 전용(서피스면 UI 체크박스 비활성). Distribute 는
`surface_axis`(U/V) 방향 균일 + 반대 방향은 **범위 가운데**(ref 는 0.5 고정). **ref 프레임은 왼손계**
([[surface-normal-handedness]]) → Z = tangentU×normal 오른손 프레임. Maintain offset 그대로 적용.
관찰(미수정): 모든 오브젝트가 skip 돼도 norCrv 는 먼저 만들어져 남는다(기존 동작).
headless 서피스 139항목 + 커브 회귀 148항목.

**UPDATE 2026-09-23 (v01.26)**: 사용자 요청 — `Maintain offset` 도 **translate/rotate 를 구동**해야
채널박스만 보고 어태치를 알 수 있다. **OPM 구동을 버렸다**: 상수 오프셋을 `multMatrix.matrixIn[0]` 에
끼우고 나머지는 OFF 경로와 **같은 네트워크**(`프레임 × obj.parentInverseMatrix → decomposeMatrix →
translate/rotate`). 상수 = `local0 × obj.parentMatrix0 × inv(frame0)` — `local0` 는 현재
translate/rotate 만으로 만든 행렬(스케일 1)이라 빌드 순간 decompose 출력이 **지금 채널 값과 일치**한다.
네트워크가 `parentInverseMatrix` 를 쓰므로 상수도 **`parentMatrix`(자기 OPM 포함)로 짝을 맞춘다**
— OPM 을 구동하지 않으니 [[parentmatrix-includes-offsetparentmatrix]] 의 되먹임은 이제 없다.
`decomposeMatrix.inputRotateOrder` ← `obj.rotateOrder` 연결(기본 XYZ 고정이라 `xzy` 등이 어긋났다,
**두 모드 모두 고쳐짐**). 사전 검사도 OPM 연결 → **translate(/rotate) 연결·잠금** 확인으로 교체
(노드 만들기 전). `scale` 은 구동하지 않는다. norCrv maintain 경로의 직교 정규 프레임은 그대로
(shear·부호 뒤집힘 때문). 검증 headless 코어 24 + 오프스크린 UI 13.

**남은 일**: Maya 실기 검증 + 푸시(기본 푸시처: [[push-target-dnable-dev]]). 검증/푸시 끝나면 이 메모 삭제.
규약: [[ui-text-english-only]], [[prefer-pyside-for-new-tools]], [[push-includes-tool-guide-docs]],
[[worklog-maintenance]], [[maya-2023-compat]].
