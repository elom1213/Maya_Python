---
name: wip-a00120-fkik-bake-constraintfree
description: "IMPLEMENTED (Maya test + push pending) — fixed A00120_FKIK Bake IK/FK altering out-of-range poses by removing parentConstraint, switching to per-frame matchTransform bake (+ Get Current buttons)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8546124f-32a8-4de0-8ce6-b4460f257dcf
---

WIP (started 2026-06-29): A00120_FKIK 의 **Bake IK/FK 버그 수정** + Get Current 버튼 추가.

**버그**: 컨트롤러가 base + 다른 애니 레이어 2곳에 키가 있을 때, base 레이어에서 특정 구간을
Bake IK 하면 **구간 밖 포즈가 베이크 전과 달라진다**.

**원인**: 현재 `app/core/fkik_matcher.py::bake()` 는 임시 `parentConstraint`(mo=False) + `bakeResults`
방식. parentConstraint 를 거는 순간 pairBlend 가 끼며 기존 animCurve 가 플러그에서 분리 →
preserveOutsideKeys 가 무력화. 기존엔 `_snapshot_outside_keys`/`_restore_outside_keys` 로 우회했지만
**animation layer 를 인식하지 못해**(cmds.keyframe 은 머지된 커브를 봄) 레이어 상황에서 깨진다.

**원본은 정상**: `_archive/legacy_tools/01_Modules/JUN_PY_FKIK_Tool_V02_01.py::JUN_cmd_bake_IK_FK` 는
constraint 없이 per-frame: `for f in range(str,end): currentTime(f); JUN_MATCH_twoObjects(xform 월드복사);
setKeyframe(flw, t=f)`. 구간 안 키만 찍고 setKeyframe 이 활성 레이어에 써서 다른 구간/레이어 안전.

**해결 (사용자 요구: constraint 전혀 안 씀 + rotateOrder 달라도 정확)**: A00145_RigConnect Match 탭
참고 → `cmds.matchTransform(flw, tgt, position=True, rotation=True)` (rotateOrder-safe, constraint 없음).

**구현 계획**:
- `fkik_matcher.py`:
  - `match_transforms(tgt,flw,...)`: rotateOrder 스왑 xform 방식 → `cmds.matchTransform(flw_i, tgt_i,
    position=translate, rotation=rotate)` 로 교체(시그니처 유지, rot_order/rot_axis 인자는 무시·문서화).
  - `bake(tgt,flw,start,end)`: parentConstraint+bakeResults+snapshot 전부 제거 → per-frame 루프:
    undo_chunk + suspend_refresh, `for f in start..end(inclusive): currentTime(f); 각 쌍 matchTransform;
    setKeyframe translate/rotate(try/except)`. 끝에 currentTime 복원. 반환 end-start+1 유지.
  - `_snapshot_outside_keys`/`_restore_outside_keys` 는 `bake_constraint()` 가 여전히 쓰므로 유지.
    (Bake (Constraint) 버튼은 이름대로 의도적 constraint 방식 → 그대로 둠.)
- `main_window.py`: Start/End QSpinBox 옆에 **Get Current** 버튼 추가(A00110 _make_get_current_btn 패턴,
  단 QSpinBox 라 setValue). 헬퍼 `_make_get_current_btn(spin)` + `_set_current_frame(spin)`.
  clicked lambda 는 `*_a` 로 checked 인자 흡수.
- version.py 01.06→01.07, LAST_UPDATE 2026-06-29, main_window 헤더 날짜.
- docs `JUN_All/docs/A00120_FKIK.md` bake 섹션(57·67·74~79줄 부근: parentConstraint/snapshot 설명) →
  constraint-free per-frame matchTransform 으로 갱신 + Get Current 언급. WORKLOG 2026-06-29 항목.
- 검증 py_compile (Maya 실기 대기).

**진행 상태**: 구현 완료. fkik_matcher(match_transforms→matchTransform, bake()→per-frame matchTransform,
헤더 changelog 추가), main_window(Get Current 버튼+_make_get_current_btn/_set_current_frame, 헤더 날짜),
version 01.07, docs §4·5 + WORKLOG 2026-06-29, py_compile 통과. _snapshot/_restore 는 bake_constraint 전용 잔존.
**남은 일**: Maya 실기 검증 + 푸시([[push-target-dnable-dev]]). 끝나면 이 메모 삭제.
규약 [[ui-text-english-only]], [[maya-2023-compat]](matchTransform 은 2023 OK), [[animlayer-no-global-selected-query]],
[[push-includes-tool-guide-docs]], [[worklog-maintenance]].
