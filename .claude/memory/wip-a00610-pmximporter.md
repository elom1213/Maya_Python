---
name: wip-a00610-pmximporter
description: "A00610_PmxImporter - PMX(MMD) direct import into Maya; user decisions (FBXASC names, lambert, IK bones), golden-test basis, next steps"
metadata:
  node_type: memory
  type: project
  originSessionId: a9d7bd20-6410-453e-9d1a-03779fdc3ff3
  modified: 2026-11-09T01:04:46.456Z
---

`tools/A00610_PmxImporter` v01.00 (2026-11-09). 계획서 `docs/plans/A00610_PmxImporter_plan.md`(§13 결정 기록 · §14 PMX 의 나머지 데이터), 안내 `docs/A00610_PmxImporter.md`.

- **사용자 결정(2026-11-09)**: 이름 = **PMX 고유(일본어) 이름, 못 쓰는 글자는 FBXASC###**(FBX 규칙, CATS 영어 이름 · 이름 맵 JSON 은 폐기) · 머티리얼 **lambert** 고정 · **IK 본 기본 생성**.
- 변환(기준 mb `021_Miyabi/00_01_03_RIG_01_PJ/scenes/0010_Miyabi_base_02.mb` 와 숫자 대조로 확정): 위치 `(x,y,-z)×8` cm · UV `(u,1-v)` · 삼각형 `(c,b,a)` · 정점 순서 = PMX.
- 텍스처는 cp949 밖 글자 경로만 PMX 옆 `maya_textures/` 에 복사, 문자열 어트리뷰트는 ASCII — [[maya-codepage-nonascii-traps]].
- 시험: `tests/test_pmx_core.py`(시스템 파이썬) · `tests/test_import_maya.py`(mayapy, 골든 G1~G12). 모델 파일은 저장소에 넣지 않는다(readme 재배포 금지), `A00610_SAMPLE_DIR`.
- **번호 충돌 이력**: 다른 세션이 같은 A00610 으로 NameDecoder 계획을 3분 먼저 커밋 → 그쪽이 A00620 으로 옮김. 새 번호를 정하면 **커밋 직전에 다시 확인**할 것.
- 남은 것: GUI 실기 확인(뷰포트 텍스처 · 투명 · Shape Editor · FBX → UE), 2차 = 부여(付与) 본 quatNodes 망(애니에 필수, 계획서 §14-1) · IK → ikHandle · 물리.

**Why:** CATS(블렌더) → FBX → 마야 손질 과정을 없애려는 툴. **How to apply:** 이 툴을 고칠 때 골든 시험을 함께 돌린다.
