---
name: wip-ik-edit-keep-pv-offset
description: "A00060 IK Edit Keep offset(v03.13) · A00130 Match IK 세션(v02.28) — 폴 벡터 offset 불변, 체인을 폴 평면에 맞춤, 둘 다 기본. 2조인트 체인은 솔버의 비틀림을 굳힘, 길이는 IK 켜기 전에 써야 스트레치가 안 흔든다"
metadata:
  node_type: memory
  type: project
  originSessionId: 9708a5ac-8e21-47b2-9c53-e7db58a3356c
  modified: 2026-09-28T01:20:24.426Z
---

2026-09-28 구현 완료 (계획서 `JUN_All/docs/plans/A00060_A00130_ik_edit_keep_pv_offset_plan.md` 6장 답 · 7장 결과).
공유 코어 `A00060 .../ik_edit_manager.py` 의 `PV_MODE_KEEP` 이 기본. 옛 `offset` · `target` 모드는 순서까지 불변.

**사용자 규칙**: X → 다음 조인트, up = Y/Z 중 지금 월드 +Y 를 더 향한 축을 **폴 평면 법선 쪽**으로,
반대편은 거울 반사, 바뀐 체인 길이로 옵션 컨트롤러(`Arm_L` 등 12개)도 갱신.

**실측으로 정한 것 (케이지 `0035_maya_src_rig/02_Cage_v02/Cage_v002_0060.mb`)**
- ★ 2조인트 RP 체인(D01 16개 중 12개)은 **솔버가 폴을 볼 축을 정한다** — up 규칙으로 돌리면 90°. X 만 맞추고
  IK 를 잠깐 켜 솔버 회전을 읽어 굳힌다. **읽기 전에 preferred angle 을 현재 포즈로** (안 하면 또 90°).
- 오른팔 체인은 **−X 규약**(자식 tx 음수) — +X 강제하면 180° 뒤집힘. 지금 부호 유지.
- ★ 길이는 **IK 를 켜기 전에** 쓴다. 매칭 중엔 옛 휴지 길이로 스트레치 1.206 → 켠 뒤 쓰면 체인이 줄어 wrist 6.26 이탈.
  코어가 계산/놓기를 나누고(`fit_to_pole_plane`/`place_fit`) `after_fit` 콜백 뒤 같은 월드 목표로 다시 놓는다.
- 팔·다리 루트 rotate 는 parentConstraint 구동 — 타깃 offset 재고정은 `constraintRotateOrder` 로 풀어야 0.
- `_measure` 회전은 이제 쿼터니언 각도. 오일러 성분 차는 같은 방향을 90/270/356° 로 보고했다.
- up 동률(`UP_AMBIGUOUS_DOT` 0.5): 템플릿 팔이 아래로 내려간 실제 Match 에서 걸려 Y 선택(글자 규칙이면 Z). 사용자에게 보고함.
- 합성 레퍼런스 체인 저장→재오픈 어긋남은 옛 모드도 같다(테스트 장면 고유). 실제 케이지 레퍼런스는 ≤ 0.00004.

**How to apply:** IK 체인을 건드리는 새 기능은 2조인트 체인 · −X 규약 · 스트레치 구동 길이를 먼저 확인한다.
관련 [[wip-a00060-ik-edit]] · [[wip-a00130-ik-session]] · [[wip-a00130-ik-axis]] · [[wip-a00060-pole-target]]
