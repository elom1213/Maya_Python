---
name: posewrangler-plugin-fork-patch
description: Epic PoseDriverConnect(PoseWrangler) 포크 위치와 내가 넣은 3단계 패치 요지
metadata: 
  node_type: memory
  type: reference
  originSessionId: 85c8852e-52d8-4514-9afa-b44bf5d7ef96
  modified: 2026-07-30T01:03:43.968Z
---

Epic Games 공식 Maya 플러그인 **PoseDriverConnect**(= PoseWrangler)를 로컬 git 포크로 관리 중.
경로: `C:\Users\USER\Documents\maya\2024\modules\PoseDriverConnect\python` (이 repo 밖, 별도 git)
`699e71e first commit` = 벤더 원본, 이후 3커밋이 내 수정.

패치 대상은 `epic_pose_wrangler/v2/model/serializers/serializer_v1_2_0.py` 의 `deserialize()`.
델타 모드 프리셋 임포트 시 JSON 의 `driven_transforms`(헬퍼/트위스트 코렉티브 조인트)가 씬에
전부 있다고 전제하므로, 하나라도 없으면 임포트 전체가 실패 → MetaHuman 표준 스켈레톤이 아닌
커스텀 아바타에 프리셋 재사용 불가. 수정: ① `cmds.objExists` 로 `driven_transforms` 필터,
② 포즈 델타 복원 루프에서 없는 driven skip (KeyError 방지), ③ driven 이 0개가 된 솔버는
`RBFNode.create_from_data` 단계에서 건너뛰고 로그 (껍데기 솔버 노드 생성 방지).
변수/플래그는 `JUN__` 접두사로 표시해 벤더 코드와 구분.

**Why:** 이 패치가 portfolio 1-5 "MetaHuman RBF 세팅을 비메타휴먼
아바타로 일반화" 를 실제로 가능하게 한 전제 조건. 이력서 MetaHuman 항목 근거로 사용됨.
**How to apply:** 엔진 플러그인 업데이트 시 벤더 원본 위에 위 3군데만 다시 얹으면 됨.
포트폴리오 서술은 `JUN_All/docs/portfolio/portfolio_KR.md` / `_EN.md` 의 1-6 절 참고
([[update-portfolio-on-tool-work]]).
