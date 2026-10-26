---
name: wip-facial-arkit52-ctl-v05
description: Facial ARKit 52 controller board Ctl_Only_V04 -> V05 (built 2026-10-26 by A00580_FacialBoardBuilder, verify 1582 pass, GUI check pending) - what V04 really is, the decisions, dummies, bake flow
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

**완성 (2026-10-26 같은 날)** — 사용자 답: direct 유지 · CSV 임포트 = **A00480 FileTool `Import > CSV`, `BS_Face_CSV` 별칭만 본다**(메시 불필요) · cheekPuff 중앙 하나 +
좌우 예비 `CTRL_L/R_cheek_puff` 미연결 회색 · funnel/pucker 두 슬라이더 · `Head/Global/World` = 따라가기 가중치(로케이터 3 에 parentConstraint) · 아래 표현 −ty.
`JUN_All/tools/A00580_FacialBoardBuilder/`(헤드리스: board_spec · build · bake · verify · preview · migrate · spec/) → `01_Module_01_Facial\Ctl_Only_V05.ma/.mb/_board.png`,
컨트롤 35 / attr 52, 보드 15 × 24.4, 루트 (20,140,0). **verify 1582 통과, GUI 눈 확인 아직.** 함정: 지오메트리 없는 blendShape 는 연결 노드 delete 로 사라진다 →
숨긴 평면 `BS_Face_CSV_geo` ([[maya-delete-cascades-geoless-blendshape]]). V04 별칭 인덱스 = ARKit 52 순서. 베이크 = `bake.bake_csv_to_ctl()`(0~1 직결은 커브 복사, ± 는 합산 키),
`reconnect_csv()` 는 키 있는 축을 건너뛴다. 이관표 `spec/migrate_v04.json`(`merged_v05_plugs` 는 합). 다음: 사용자 GUI 확인 → UE Control Rig 빌더(M6, 같은 json).

관련: [[wip-jali-slider-ctl]](빌더 · 검증 · bake_ctl_keys 전례), [[wip-a00145-connect-rules]](ARKit 52 규칙), [[metahuman-cloth-corrective-A00280]], [[wip-a00480-filetool]]
