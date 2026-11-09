# Changelog — A00610_PmxImporter

All notable changes to this tool are documented here.

## [01.01] - 2026-11-09

- **2차 1단계** — 결정: IK 근사 생성(기본 켬) · 로컬축 반영(기본 켬) · 외곽선 / 툰 / 스피어 보류.
- **부여(付与) 본이 움직인다.** Miyabi 의 다리 웨이트는 전부 `足D` · `ひざD` · `足首D` 에 있어 v01.00 에서는 다리를 돌려도 메시가 안 움직였다.
  - quatNodes 망: 부여 부모의 MMD 로컬 회전을 `slerp(I, q, 비율)`(음수 비율은 역회전) → 조인트 **`rotateAxis`** 로.
    마야 조인트 행렬에서 rotateAxis 가 rotate 보다 먼저라 **부여 먼저, 자기 회전 나중**(three.js MMD GrantSolver 와 같은 순서) — `rotate` 는 비어 있어 직접 조작 가능.
  - 사슬(`足補助 ← 足D ← 足`)은 부모의 총 회전, IK 가 돌린 본은 IK 결과까지 따라간다. 이동 부여 · 로컬 부여는 아직(경고).
- **IK** — IK 본마다 ikHandle(링크 2개 이상 RP, 1개 SC), 핸들은 IK 본 아래(숨김). MMD 의 CCD 반복 · 각도 제한은 적용하지 않는 근사.
- **로컬축** — 로컬축(팔 · 손가락) · 고정축(비틀기 본)이 있는 본 42개를 그 축으로 jointOrient, 나머지는 월드 정렬. 월드 위치 · 스킨은 그대로.
- **표시 프레임** — 본 프레임 → 조인트 셋(`<모델>_frames` 아래), 모프 패널 → Shape Editor 그룹(eyebrow / eye / mouth / other).
- **엣지 배율** → 컬러 셋 `mmdEdgeScale`(1 이 아닌 정점이 있을 때만).
- UI 체크 4개 추가(`Local axes` · `Append bones` · `IK` · `Display frames`, 전부 기본 켬).
- 시험 core 61/61 · mayapy 80/80(+20): MMD 규칙 직접 검사(비틀기 = 같은 축 ×0.25/0.5/0.75 · 허리 캔슬) ·
  **Blender + mmd_tools 와 포즈 메시 대조**(다리 D 체인 · 허리 / 어깨 캔슬 < 1e-3 cm, IK 평균 0.03 cm). **GUI 확인 아직.**

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
