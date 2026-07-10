---
name: wip-a00145-match-dootool-options
description: A00145_RigConnect v01.10 IMPLEMENTED (Maya test + push pending) — Match tab ported DOOTOOL_PY_TOOL_Match.py checkboxes (Translation/Rotation/Scale/Parent)
metadata: 
  node_type: memory
  type: project
  originSessionId: f512cf79-ecd4-4c35-bd99-27839d408de1
---

WIP (2026-07-01): A00145_RigConnect Match 탭에 레거시 `DOOTOOL_PY_TOOL_Match.py`
(C:\Users\USER\Documents\maya\2024\prefs\scripts\, Doosup Jung 2018) 의 옵션 체크박스 이식. v01.09→01.10.

**요청**: DOOTOOL 의 Translation/Rotation/Scale/Parent Followers to Targets 체크박스를 이식,
동작·기본 체크 상태 원본과 동일. **Rotate Order / Rotate Axis 는 제외**(A00145 는 월드 행렬 매칭이라 무의미).

**기본값(원본 준수)**: Translation ON / Rotation ON / Scale(world) OFF / Parent OFF.

**구현**:
- core `app/core/match_manager.py`: `match(targets, followers, normal_axis="y", translate=True,
  rotate=True, scale=False, parent=False)`. transform 타겟은 `_match_one` 이 matchTransform 의
  position/rotation/scale 플래그로 켜진 채널만 월드 매칭. 원본 Scale(null+scaleConstraint 로 월드
  스케일 읽어 로컬 attr set)은 `matchTransform scale`(월드 스케일 일치)로 대체. Parent 는 매칭 후
  별도 패스 `_parent_one(flw, tgt)` — 컴포넌트면 `tgt.split(".")[0]` 소유 transform 아래로, 자기자신/
  이미 자식이면 스킵, cmds.parent 가 월드 위치 보존. vertex/mesh/cluster/component 특수 처리는
  translate/rotate 로 게이팅(둘 다 off 면 vertex 샘플링도 스킵). `_match_via_matrix` 에 translate/
  rotate 플래그 추가. create_and_match 는 기본값으로 기존 동작 유지.
- ui `app/ui/main_window.py`: Match 탭 "Match Options" QGroupBox(cb_mt_translate/rotate/scale/parent,
  툴팁). on_match 가 값 읽어 전달, 채널 전무 시 경고 no-op, 로그에 적용 채널 [TRSP] 표기. About/버전 갱신.

**검증**: 전 파일 ast.parse + 페이크 maya.cmds 로 core 단위검증 10/10 PASS(플래그별 matchTransform
kwargs / parent→owner / already-child 스킵 / count·skip). Maya 실기 대기.

**남은 일**: Maya 실기 검증 + 푸시([[push-target-dnable-dev]], 가이드 doc 포함=[[push-includes-tool-guide-docs]],
[[worklog-maintenance]]). 끝나면 이 메모 삭제. 규약: [[ui-text-english-only]], [[maya-2023-compat]].
