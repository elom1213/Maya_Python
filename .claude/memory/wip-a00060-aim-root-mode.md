---
name: wip-a00060-aim-root-mode
description: "A00060_V03 Orient > Aim 의 Mode Chain/Root(v03.11) — Root 는 루트 아래 최하위까지, 분기는 첫 자식 조준. X 조준만으로는 자식이 X 축 위일 때만 위치 보존 → 움직인 자식을 원위치"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8fc27b42-f7ec-4155-b340-da985ee075b0
  modified: 2026-09-18T01:49:16.384Z
---

`A00060_jointTool_V03` v03.11 (2026-09-18): `Orient > Aim` 에 Mode 라디오 `Chain` / `Root`
(A00145 Mirror 탭 Mode 모양). Root = `Start`/`End` 자리에 `Root` 리스트 하나, 각 루트부터 **모든 최하위
자식까지**, 줄마다 pole tgt 하나(모자라면 마지막). 분기점은 **첫 번째 자식** 조준(마야 Orient Joint 규칙).
core: `aim_manager.make_joint_aim_roots` / `root_tasks`, 두 모드가 `_apply_tasks` 공유.

**함정(mayapy 실측)**: 부모 X 를 자식의 원본 위치로 조준해도 자식이 제자리에 남는 건 **자식이 이미 부모 X 축
위에 있을 때뿐**이다. 분기점의 다른 가지, X 로 정렬 안 된 체인은 트위스트에 딸려 움직인다(1.49). 가이드는
"완전 보존" 이라 했지만 전제가 숨어 있었다 → 돌린 직후 **움직인 자식만** `xform ws` 로 원위치, 되읽어 확인
([[xform-silent-on-locked-channels]]). 정렬된 체인은 예전과 결과 차이 0.

**Why:** 사용자 요청(Root 모드). 버그는 분기 계층 테스트를 짜다가 드러났다.
**How to apply:** `make_joint_aim` 반환이 None → `(done, warnings)` 로 바뀌었다. 다른 곳에서 부르면 맞출 것.
