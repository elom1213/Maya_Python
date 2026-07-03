# 학습 노트 (study)

이 폴더는 **특정 툴 사용법이 아니라, 작업 방법론·기법에 대한 공부용 문서**를 모은다.
(툴 안내 문서는 상위 `docs/*.md`, 개발 계획은 `docs/plans/` 에 둔다.)

- 본문은 **한글**, UI/코드 식별자·함수명은 영어 그대로 인용.
- 파일명은 주제 기반(예: `skinWeight_transfer_workflow.md`).
- 관련 개발 계획/툴 문서가 있으면 상호 링크한다.

---

## 문서 목록

| 주제 | 도메인 | 문서 |
|------|--------|------|
| 스킨 웨이트 전이 (Shrink Wrap + Blendshape 공간 정렬) | 리깅 / 스킨 | [skinWeight_transfer_workflow](skinWeight_transfer_workflow.md) |
| SmartLayer Bake 알고리즘 분석 (서드파티 툴 `.pyc` 역분석) | 애니메이션 / 베이크 | [SmartLayer_bake_algorithm_analysis](SmartLayer_bake_algorithm_analysis.md) |
| 후디니 의상 주름 강조 (Wrinkle Exaggeration, 언샤프 마스크) | 시뮬레이션 / 후처리 | [houdini_wrinkle_exaggeration](houdini_wrinkle_exaggeration.md) |
| 버텍스 노말 색(노랑/초록 = locked/unlocked)과 FBX 커스텀 노말 보존 | 모델링 / 셰이딩 / FBX | [vertex_normals_locked_vs_unlocked_fbx](vertex_normals_locked_vs_unlocked_fbx.md) |
| 노드 신원: 이름/경로 vs UUID (동일 이름·rename 안전 처리) | 스크립팅 / maya.cmds | [maya_node_identity_name_vs_uuid](maya_node_identity_name_vs_uuid.md) |
