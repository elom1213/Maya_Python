# 학습 노트 (study)

이 폴더는 **특정 툴 사용법이 아니라, 작업 방법론·기법에 대한 공부용 문서**를 모은다.
(툴 안내 문서는 상위 `docs/*.md`, 개발 계획은 `docs/plans/` 에 둔다.)

- 본문은 **한글**, UI/코드 식별자·함수명은 영어 그대로 인용.
- 파일명은 **`00100_주제.md`** 형식 — 5자리 번호 접두사 + 영문 주제명(`tools/A000XX_` 와 같은 방식).
- 관련 개발 계획/툴 문서가 있으면 상호 링크한다.

---

## 번호 규칙

파일명 앞의 번호는 **탐색기·GitHub 에서 문서가 늘 같은 순서로 보이게** 하고,
**번호가 가까운 문서 = 서로 관련 있는 문서**라는 뜻을 담는다.

- **간격은 100** (`00100`, `00200`, `00300` …). 새 주제는 마지막 번호 + 100.
- **사이에 끼울 때는 중간값**을 쓴다. `00200` 과 `00300` 사이면 `00250`,
  거기서 더 끼우면 `00225` → `00212` … 로 6단계까지 뒤 문서를 밀지 않고 들어간다.
- **최초 배치만 연대순이었고, 그 뒤로는 주제 근접성이 우선**이다.
  연대순이 필요하면 git 로그를 보고, 파일명 번호는 "무엇과 이웃인가"만 표현한다.
- 번호를 바꾸면 **인바운드 링크가 깨진다**. 리네임은 `git mv` + 링크 일괄 치환 + 이 표 갱신을
  **한 커밋에** 함께 한다. (참조처: `docs/*.md`, `docs/WORKLOG.md`, `tools/*/README.md`)
- `README.md` 는 번호를 붙이지 않는다 (GitHub 이 폴더 인덱스로 자동 렌더하는 이름).

---

## 문서 목록

| # | 주제 | 도메인 | 문서 |
|---|------|--------|------|
| 00100 | 버텍스 노말 색(노랑/초록 = locked/unlocked)과 FBX 커스텀 노말 보존 | 모델링 / 셰이딩 / FBX | [00100_vertex_normals_locked_vs_unlocked_fbx](00100_vertex_normals_locked_vs_unlocked_fbx.md) |
| 00200 | 스킨 웨이트 전이 (Shrink Wrap + Blendshape 공간 정렬) | 리깅 / 스킨 | [00200_skinWeight_transfer_workflow](00200_skinWeight_transfer_workflow.md) |
| 00300 | Kangaroo 스킨 웨이트 전이 알고리즘 분석 (`00200` 워크플로우의 내부 동작) | 리깅 / 스킨 | [00300_kangaroo_skinWeight_transfer_analysis](00300_kangaroo_skinWeight_transfer_analysis.md) |
| 00400 | AdvancedSkeleton `Add ARKit Curves to Skeleton` 분석 | 페이셜 / ARKit | [00400_Add_ARKit_Curves_to_Skeleton_analysis](00400_Add_ARKit_Curves_to_Skeleton_analysis.md) |
| 00500 | 위 분석의 B안 구현 가이드 | 페이셜 / ARKit | [00500_Add_ARKit_Curves_plan_B_implementation_guide](00500_Add_ARKit_Curves_plan_B_implementation_guide.md) |
| 00600 | AdvancedSkeleton MetaHuman Animator — `Connect Face Animation` / `Bake to standard Face Controls` 알고리즘 분석 (베이크가 어긋나는 원인) | 페이셜 / MetaHuman / 베이크 | [00600_AdvancedSkeleton_MetaHumanAnimator_connect_bake_analysis](00600_AdvancedSkeleton_MetaHumanAnimator_connect_bake_analysis.md) |
| 00700 | SmartLayer Bake 알고리즘 분석 (서드파티 툴 `.pyc` 역분석) | 애니메이션 / 베이크 | [00700_SmartLayer_bake_algorithm_analysis](00700_SmartLayer_bake_algorithm_analysis.md) |
| 00800 | 언리얼 본 피직스 3종 원리 (Kawaii vs Physics Asset vs Anim Dynamics, 왜 Physics Asset이 더 리얼한가) | 리깅 / 시뮬레이션 / 언리얼 | [00800_unreal_bone_physics_kawaii_vs_physicsAsset_vs_animDynamics](00800_unreal_bone_physics_kawaii_vs_physicsAsset_vs_animDynamics.md) |
| 00900 | 후디니 의상 주름 강조 (Wrinkle Exaggeration, 언샤프 마스크) | 시뮬레이션 / 후처리 | [00900_houdini_wrinkle_exaggeration](00900_houdini_wrinkle_exaggeration.md) |
| 01000 | 노드 신원: 이름/경로 vs UUID (동일 이름·rename 안전 처리) | 스크립팅 / maya.cmds | [01000_maya_node_identity_name_vs_uuid](01000_maya_node_identity_name_vs_uuid.md) |

주제 흐름: **모델링(001) → 스킨(002~003) → 페이셜(004~006) → 베이크(007) → 시뮬/피직스(008~009) → 스크립팅(010)**
