---
name: wip-facial-arkit52-ctl-v05
description: Facial ARKit 52 controller board Ctl_Only_V04 -> V05 plan (2026-10-26, plan only) - what V04 really is, the decisions, and where the plan lives
metadata:
  type: project
---

`0035_maya_src_rig\01_Module_01_Facial\Ctl_Only_V04.mb` = ARKit 52 를 애니메이터가 다루는 **2D 보드**(NURBS 원 52 + 루트, x 13~27 · y 142~167,
리밋 없음). 더미 둘: `BS_Face_CSV`(blendShape, 타겟 52 **델타 0**, `FaicalMesh_geo` = "Faical" 글자 메시에 걸림 — CSV 임포트가 키를 넣는 자리) ·
`BS_Face_Connect_01`(transform, attr 52 — 출력). **두 경로가 동시에 연결돼 있다**: CSV → mult/pma → 컨트롤 translate(38개) · 컨트롤 → clamp(±분리)/×−1
→ Connect_01. 저장 상태에서 컨트롤러는 CSV 가 끌고 다닌다(JALI direct 리그와 같은 꼴, 베이크로 끊는다). 죽은 컨트롤 7, 자리 ≠ 부위(cheekPuff 중앙,
funnel/pucker 턱 아래 …), 이름 체계 3종 혼재.

**계획 (2026-10-26, 코드 전)** `JUN_All/docs/plans/Facial_ARKit52_Ctl_V05_plan.md`: 더미 3 노드 **이름 · attr 순서 그대로**, 컨트롤은 MetaHuman 식
`CTRL_<L|R|C>_<region>_<motion>` 33개(0~1 슬라이더 · ±1 슬라이더 · 2D 패드, `transformLimits` 로 범위), 얼굴 지도형 배치(52 attr 매핑표 + 그림),
앞으로 = 직결/clamp/×−1, 뒤로 = direct + `bake(copy)` · `reconnect_csv()`, **json 명세 하나 → Maya 빌더(`A00580_FacialBoardBuilder`, mayapy) + UE Control Rig
빌더(2단계)**. MetaHuman 0030 보드 실측: `GRP_faceGUI > … > FRM_<ctl> > CTRL_*` 181(폴리 메시), tx/ty 만 keyable + 리밋, → animCurveUU → `CTRL_expressions`.
L 이 +x (보드를 마주보는 사람의 오른쪽, 캐릭터 왼쪽) — V04 도 같다. M0 실측 8항목(특히 **CSV 임포트 툴이 어떤 이름을 보는지 Q2**, V04 부호) 뒤 M1 json → 사용자 확인 → 빌드.

관련: [[wip-jali-slider-ctl]](빌더 · 검증 · bake_ctl_keys 전례), [[wip-a00145-connect-rules]](ARKit 52 규칙), [[metahuman-cloth-corrective-A00280]]
