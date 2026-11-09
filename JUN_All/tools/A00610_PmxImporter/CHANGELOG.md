# Changelog — A00610_PmxImporter

All notable changes to this tool are documented here.

## [01.00] - 2026-11-09

- **첫 버전.** MMD 모델(PMX 2.0 / 2.1)을 마야에 바로 임포트 — 계획서 `docs/plans/A00610_PmxImporter_plan.md`.
  - 메시 하나(정점 순서 = PMX): 위치 `(x, y, -z) × 8` cm · UV `(u, 1-v)` · 삼각형 `(c, b, a)` · 노멀 잠금 · 추가 UV → `UV1` ~ `UV4`.
    기준 mb(CATS → FBX)와 수치로 대조해 정했다.
  - 재질마다 lambert + SG + file(같은 텍스처는 공유), 알파 있는 텍스처는 투명도 연결, 확산 알파 곱.
  - 본마다 조인트(IK 본 포함, 월드 정렬), 스킨(BDEF1/2/4, 같은 본 합치기 · 정규화, SDEF/QDEF → 듀얼 쿼터니언).
  - 버텍스 모프 → 지오메트리 없는 blendShape 타깃(스킨보다 앞).
  - 이름 = PMX 고유 이름, 마야에 못 쓰는 글자는 `FBXASC###`(FBX 와 같은 규칙, 원래 글자로 복원 가능).
  - 시스템 코드페이지(cp949)로 못 읽는 텍스처 경로는 PMX 옆 `maya_textures/` 에 FBXASC 이름으로 복사해 연결.
  - 원본 정보(본 플래그 · 부여 · IK · 재질 값 · 모프 패널 · 리포트)는 ASCII 문자열 어트리뷰트로 보존(`.ma` 코드페이지 손실 방지).
  - 강체 · 물리 조인트 · 표시 프레임 · 버텍스 외 모프는 리포트에 개수만.
  - Ctrl+Z 한 번에 임포트 전체가 되돌아간다. 네임스페이스 옵션.
- 시험 core 61/61 · mayapy 60/60(기준 mb 골든 G1 ~ G12). **GUI 확인 아직.**
