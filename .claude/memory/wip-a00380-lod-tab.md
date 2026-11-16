---
name: wip-a00380-lod-tab
description: "A00380_MeshTool v01.20 LOD 탭 — numpy 클러스터-QEM 저폴리 프록시, 실제 아바타 polyReduce 대비 12배, 해상도 탐색은 중복 제거 후 개수로. GUI 실기 아직"
metadata:
  node_type: memory
  type: project
  originSessionId: 9964c4f6-a11b-4e08-bc52-f3d62bf6f428
  modified: 2026-11-16T00:56:36.337Z
---

2026-11-16, A00380_MeshTool **v01.20 LOD 탭**(맨 오른쪽). 모캡 클린업 중 고폴리 아바타 재생 끊김 →
재생용 저폴리 프록시(LOD1~5)를 만든다. 바인딩 안 함(사용자가 A00275 로 재바인딩).
계획서 `docs/plans/A00380_MeshTool_LOD_plan.md`(§10-2 결과), 시험 `..._LOD_probe_test.py`(mayapy 19항목).

- Fast = numpy 그리드 클러스터링 + 셀마다 QEM 최소점(Lindstrom), 노멀 6 버킷을 셀 키에 → 옷 겉/안 안 붙음.
  Quality = polyReduce(`trm=2, tct=`). 스킨/블렌드셰이프 메시는 orig 셰이프(intermediate, inMesh 입력 없음, 같은 버텍스 수) 에서.
- ★ 목표 삼각형 수용 해상도 이분 탐색은 **중복 삼각형을 뺀 뒤** 세야 한다 — 양면 헤어 카드가 절반 사라져 목표의 36% 가 됐었다.
- ★ 트랜스폼 `exactWorldBoundingBox` 는 숨은 orig 셰이프까지 포함 → 변형 결과는 셰이프로 잰다.
- ★ 스크래치 mayapy 스크립트를 `inspect.py` 로 이름 지으면 표준 모듈을 가려 initialize 가 트레이스백 없이 죽는다.
- 실측(CHOEUN `geo_grp` 5메시 27.6만 tri, LOD 3개): Fast 1.6 s vs Quality 18.9 s.
- 테스트 씬: `C:\JUN\JUN_MUE\00_03_01_RIG_01_PJ\scenes\0405_CHOEUN\0010_CHOEUN_rig_AGF_0020.mb` (사용자 허락, 열기만 · 저장 금지).

남은 것: 마야 GUI 실기, 재바인딩 후 실제로 재생 끊김이 사라지는지, Maya 2023.
Related: [[wip-a00380-meshtool-peak]], [[mayapy-headless-verify]], [[qapplication-before-maya-standalone]]
