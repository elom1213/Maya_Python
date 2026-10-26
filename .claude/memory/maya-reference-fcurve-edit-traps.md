---
name: maya-reference-fcurve-edit-traps
description: "레퍼런스된 animCurve 키 편집(refAnimCurvesEditable)의 함정 — 편집은 relationship fcurve 로 레퍼런스 노드에 쌓이고 saveReference 로만 파일에 써진다, 미저장 편집은 재로드 때 24fps 기준으로 시각이 환산되는 마야 버그(30fps 에서 10 → 12.5), 편집 수는 -onReferenceNode 로, Discard 는 unload 뒤 removeEdits. mayapy 2024 실측 2026-10-26"
metadata:
  type: project
---

mayapy 2024 실측 (2026-10-26, A00570_JaliReview 만들며 — 계획서 `docs/plans/A00560_JaliBatch_plan.md` §11 M0).

- **켜는 법**: `cmds.animDisplay(e=True, refAnimCurvesEditable=True)` (= 환경설정 "Allow edits on referenced animation curves", optionVar `refAnimCurvesEditable`).
  **꺼져 있으면 `keyframe -e` 가 에러 없이 조용히 무시된다** — 툴은 상태를 보여 줘야 한다.
- 키 편집은 레퍼런스 노드에 `relationship "fcurve" "<curve>" -relationshipData "add <t> <v> ..." -relationshipData "cut <t>"` 편집으로 쌓인다.
  **씬 저장(Ctrl+S)으로는 레퍼런스 파일이 안 바뀐다.** 파일에 쓰는 길은 `cmds.file(<레퍼런스 파일 경로>, saveReference=True)` 뿐
  (`saveReference=True, referenceNode=...` 는 "No file name given", 노드 이름을 주면 "not a loaded reference"). 저장 뒤 편집 목록이 빈다.
- **★ 미저장 편집을 들고 `loadReference`(교체 · 재로드)하면 편집 시각이 24fps 기준으로 환산된다** — 30fps 씬에서 `add 10` 이 `add 12.5`, `5000` 이 `6250`,
  `cut 20` 이 `cut 25` 로 다시 적용된다(마야 버그, 같은 파일로 재로드해도 같다). 그 상태로 saveReference 하면 엉뚱한 프레임에 키가 써진다.
  **편집 직후 바로 saveReference 하면 정확하다**(재열기로 확인). → 교체 전에 반드시 저장 또는 폐기, 편집을 남긴 검수 씬을 저장했다가 다시 열지 말 것.
- `referenceQuery <RN> -editStrings` 는 **그 레퍼런스 안의 중첩 레퍼런스에 저장된 편집**(클립 파일이 컨트롤러 레퍼런스에 한 23건)까지 보여 준다.
  "이 씬에서 한 편집" 만 세려면 **`-onReferenceNode <RN>`**. `-editNodes` 는 `['커브', 'add 10 0', 'cut 20']` 식으로 토큰이 섞여 나와 쓸모없다.
- **Discard**: `referenceEdit -removeEdits` 는 **로드 상태에서는 지워지지 않는다** → `file -unloadReference` → `referenceEdit(rn, removeEdits=True, successfulEdits=True, failedEdits=True, onReferenceNode=rn)` → `file -loadReference`. 중첩 편집 · 다른 레퍼런스의 편집은 그대로다.
- 두 레퍼런스 사이의 `connectAttr`(클립 안 노드 → 아바타 블렌드셰이프) 편집은 **아바타(목적지) 레퍼런스 노드**에 저장된다(레퍼런스 순서 무관).
  클립을 교체해도 연결이 살고, 클립 saveReference 에 섞여 들어가지 않는다. 블렌드셰이프 weight 에 `setAttr .w[0:2]` 편집이 하나 더 생기는데 무해.
- 레퍼런스된 클립의 `fileInfo` 는 레퍼런스한 씬에서 **보이지 않는다**(자기 파일의 fileInfo 만). 메타데이터는 옆 json(매니페스트)에.
  레퍼런스된 `sound` 노드는 `CLIP:jali_lipsync_audio` 로 보인다(타임슬라이더 재생은 GUI 미확인).
- 컨트롤러 `.ma` 를 다른 경로의 같은 내용으로 `loadReference` 하면 키 · 연결 그대로, failedEdits 0. 노드 이름을 바꾼 파일이면 그 노드의
  disconnectAttr · connectAttr 편집 2건이 failedEdits 로 잡히고 나머지 채널은 멀쩡하다.
- mayapy standalone 의 `file new` · `currentUnit` 때 `Cannot find procedure "internalTimeUnitStringToDisplayFPSString"` 에러 줄이 찍히지만 무해(GUI 전용 MEL).

관련: [[maya-reference-import-traps]], [[wip-a00560-jalibatch]], [[mayapy-headless-verify]]
