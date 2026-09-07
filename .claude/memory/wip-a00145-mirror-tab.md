---
name: wip-a00145-mirror-tab
description: "A00145 Mirror 탭 신규 — 계층을 통째로 미러(스킨/컨스트레인트/클러스터 재구성). Behavior 행렬은 '법선 성분만 남기고 뒤집기', Behavior 는 이동을 미러하지 않는다, 메시는 정점을 한 번 더 반사해야 한다, 토큰 없으면 이름을 찍고 세트로 묶는다 (v01.38)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8a1f639d-1fbe-4096-98f7-2265e5589a17
  modified: 2026-09-07T01:05:42.741Z
---

A00145_RigConnect **`Mirror` 탭 신규** (v01.37→**01.38**, 2026-09-07). TSL 에 담은
오브젝트와 **그 아래 자식 전부**를 복제해 반대쪽 리그를 만들고, **스킨 웨이트 ·
컨스트레인트 · 클러스터**를 반대쪽에 다시 세운다. 평면 YZ/XY/XZ(기본 YZ),
조인트/커브 각각 Behavior·Orientation(기본 Behavior), `Disable token check`.

**스코프는 리스트가 정한다.** 리스트에 없으면 복사하지 않는다 — 스코프 밖 메시가 미러
대상 조인트에 바인드되어 있어도 그 메시는 그대로 두고, 스코프 밖 드라이버/인플루언스는
**그 노드를 그대로 참조**한다(센터 조인트·센터 컨트롤이 자연히 처리된다).

- **토큰이 없어 멈출 때는 이름을 찍고 세트로 묶는다.** 걸린 오브젝트 이름을 로그에
  (한 줄에 4개씩) 찍고 `mirror_noToken_set` 하나로 묶어 **선택**까지 한다. 세트 이름은
  고정이고 **비워서 재사용**한다 — 같은 이름으로 `cmds.sets` 를 또 부르면 `..._set1`,
  `...2` 로 쌓여 어느 것이 방금 것인지 알 수 없어진다.
  **★ 예외로 던지면 반환값(warnings)이 통째로 사라져 이름이 로그에 안 남는다** →
  `MissingTokenError` 에 이름 목록·세트 이름·로그 줄을 실어 보내고 UI 가 먼저 찍은 뒤
  다시 던진다. (`Disable token check` 면 세트는 안 만들고 `_mir` 접미사로 진행)
- **★ Behavior 행렬 = 각 축에서 법선 성분만 남기고 나머지 둘 뒤집기.** 평면의 법선 축
  (YZ→X, XZ→Y, XY→Z)만 알면 된다. Orientation 은 축 그대로 + 위치만 반사.
  Behavior 는 "반사 후 세 축 전부 뒤집기" 와 같다(세 축을 다 뒤집어야 행렬식이 양수로
  돌아와 오른손계 유지). mayapy 2024 에서 `mirrorJoint -mirrorYZ -mirrorBehavior` 와
  **행렬 성분 단위로 일치** 확인, `-mb off` 는 회전이 원본과 완전히 동일.
- **★ Behavior 는 회전을 미러하지, 이동을 미러하지 않는다.** 같은 `rotateZ +40` 은 좌우
  대칭이지만 같은 `translateY +2` 는 **반대로** 간다(로컬 Y 축이 뒤집혀 있으니 당연).
  클러스터 핸들처럼 **이동으로 구동하는 것은 Orientation** 으로 둬야 한다. mirrorJoint 의
  Behavior 도 같은 성질 — "Behavior 인데 왜 반대로 가냐" 는 버그가 아니다.
- **★ 메시는 트랜스폼만으로 안 뒤집힌다.** 두 방식 다 강체 회전이라 왼쪽 신발이 오른쪽에서도
  왼쪽 신발이다. 트랜스폼을 규칙대로 놓은 뒤 오브젝트 공간에서 보정 행렬
  `C = (M·S)·M_new⁻¹` 로 정점을 한 번 더 반사하고 `polyNormal -nm 0`. 정점 순서가 보존돼
  스킨/클러스터 웨이트는 인덱스 그대로. 자세한 함정은 [[xform-silent-on-locked-channels]].
- **★ 마야는 트랜스폼을 리네임하면 셰이프를 알아서 따라 바꾼다.** 그걸 모르고 셰이프
  이름까지 미러하면 이미 맞는 `mesh_r_01Shape1` 을 `mesh_l_01Shape1` 로 **되돌린다.**
  마야가 손대지 않은 셰이프만 바꿀 것.
- 컨스트레인트는 **어떤 채널을 실제로 구동하는지 연결로 판정해** skip 을 재현한다(키가 있으면
  `pairBlend`, 레이어면 `animBlendNode*` 를 거치므로 **2홉까지** 본다 — 한 홉만 보면 "구동
  안 함" 으로 잘못 읽는다). 미러된 오브젝트가 이미 제자리라 `maintainOffset=True` 면 원본이
  오프셋을 갖든 안 갖든 그대로 재현된다.
- 클러스터는 `cluster -wn <미러된 핸들> -bindState` — bindState 가 핸들의 현재 트랜스폼을
  상쇄해 생성 직후 형상이 안 튄다. 웨이트는 범위 지정 `weightList[i].weights[0:n-1]`.
- 좌/우 토큰 규칙은 **공용**으로 옮겼다 → [[framework-mirror-tokens]].

파일: `app/core/mirror_manager.py`(신규) · `app/ui/main_window.py`(Mirror 탭 · `on_mirror`) ·
`docs/A00145_RigConnect.md`.
